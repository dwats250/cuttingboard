"""
Layer 1 — Raw Ingestion.

Fetches quotes and OHLCV history. No math, no transforms — raw values only.
Each symbol is fetched independently; one failure never contaminates another.
"""

import logging
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from urllib.request import Request, urlopen

import pandas as pd
import yfinance as yf

from cuttingboard import config
from cuttingboard.time_utils import most_recent_completed_session_date

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RawQuote:
    symbol: str
    price: float
    pct_change_raw: float       # decimal: 5.2% is stored as 0.052
    volume: Optional[float]
    fetched_at_utc: datetime    # UTC with tzinfo — never naive
    source: str                 # "yfinance" | "fred"
    fetch_succeeded: bool
    failure_reason: Optional[str]
    # PRD-335 (R2/D-1): producer-written observation date for daily-cadence
    # drivers (currently the FRED DGS2 2Y yield). None for intraday yfinance
    # quotes — fetched_at_utc stays the acquisition clock, never the observation
    # time. Carried honestly to the tape so a daily value is never shown as live.
    as_of: Optional[date] = None


# ---------------------------------------------------------------------------
# Live-data guard
# ---------------------------------------------------------------------------

_live_data_blocked = threading.local()


@contextmanager
def block_live_data():
    """Block live data fetches within the context.

    Raises RuntimeError("LIVE_DATA_FORBIDDEN_IN_SUNDAY_MODE") if
    fetch_all_quotes or fetch_intraday_bars is called while active.
    """
    _live_data_blocked.blocked = True
    try:
        yield
    finally:
        _live_data_blocked.blocked = False


def _is_live_data_blocked() -> bool:
    return bool(getattr(_live_data_blocked, "blocked", False))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def fetch_all_quotes() -> dict[str, "RawQuote"]:
    """Fetch quotes for all symbols in the instrument universe.

    Returns a dict keyed by symbol. Every symbol appears in the result —
    failures are represented as RawQuote(fetch_succeeded=False, ...).
    """
    if _is_live_data_blocked():
        raise RuntimeError("LIVE_DATA_FORBIDDEN_IN_SUNDAY_MODE")
    results: dict[str, RawQuote] = {}
    for symbol in config.ALL_SYMBOLS:
        results[symbol] = fetch_quote(symbol)
    return results


# Short alias for interactive / pipeline use
fetch_all = fetch_all_quotes


def fetch_quote(symbol: str) -> "RawQuote":
    """Fetch a single quote, trying sources in priority order.

    Falls through to the next source only on failure. Always returns a
    RawQuote — never raises.
    """
    sources = config.SYMBOL_SOURCE_PRIORITY.get(symbol, config.SYMBOL_SOURCE_PRIORITY["default"])

    last_failure: Optional[str] = None
    for source in sources:
        if source == "yfinance":
            result = _try_yfinance_quote(symbol)
        elif source == "fred":
            # PRD-335 D-1: the actual 2Y yield carrier. Never reaches yf.Ticker;
            # inherits the never-raises / per-symbol-isolation contract.
            result = _try_fred_quote(symbol)
        else:
            logger.warning(f"{symbol}: unknown source '{source}' in priority list — skipping")
            continue

        if result.fetch_succeeded:
            return result
        last_failure = result.failure_reason

    return RawQuote(
        symbol=symbol,
        price=0.0,
        pct_change_raw=0.0,
        volume=None,
        fetched_at_utc=datetime.now(timezone.utc),
        source="none",
        fetch_succeeded=False,
        failure_reason=last_failure or "all sources failed",
    )


def fetch_ohlcv(symbol: str) -> Optional[pd.DataFrame]:
    """Fetch 6-month daily OHLCV, using a local parquet cache when fresh.

    Returns a DataFrame with columns [Open, High, Low, Close, Volume] indexed
    by date, or None when data is unavailable and the cache is stale/absent.
    The caller (derived metrics layer) treats None as INVALID for that symbol.
    """
    cache_path = _ohlcv_cache_path(symbol)

    if cache_path.exists():
        try:
            df = pd.read_parquet(cache_path)
            if _is_fresh_ohlcv_cache(df):
                logger.debug(f"{symbol}: OHLCV from fresh cache ({len(df)} bars)")
                return df
            logger.info(f"{symbol}: OHLCV cache stale — live refresh required")
        except Exception as exc:
            logger.warning(f"{symbol}: cache read failed: {exc}")

    df = _fetch_ohlcv_from_yfinance(symbol)
    if df is not None:
        _write_ohlcv_cache(symbol, cache_path, df)
        return df

    logger.error(f"{symbol}: OHLCV unavailable — symbol INVALID for derived metrics")
    return None


def _is_fresh_ohlcv_cache(df: pd.DataFrame) -> bool:
    """Fresh iff the cache already holds the most recent completed trading session.

    PRD-193: keyed on the trading day, not a fixed-hours TTL. Daily bars are
    always >= 1 day old (the fetch uses end=<today UTC>, exclusive), so an
    age-vs-TTL test rejected every cache -- the pre-market live run re-fetched
    even a just-warmed cache. A cache whose last bar is the most recent completed
    session holds exactly what a same-slot re-fetch would return, so it is reused;
    an older last bar (a new session has since completed) falls through to a
    fetch. Self-heals every weekday; never serves stale data.
    """
    if df is None or df.empty or df.index.empty:
        return False

    last_bar = pd.Timestamp(df.index.max())
    if last_bar.tzinfo is None:
        last_bar = last_bar.tz_localize(timezone.utc)
    else:
        last_bar = last_bar.tz_convert(timezone.utc)

    return last_bar.date() >= most_recent_completed_session_date(datetime.now(timezone.utc))


# PRD-271 / CB-07: the rolling window the watch layer consumes for recent
# metrics. The opening-range formation bars (09:30-09:35 ET) are retained IN
# ADDITION so the session-scoped ORB producer can select them by timestamp even
# after the tail would evict them — a bounded opening-range retention only.
MAX_INTRADAY_RETURN_BARS = 120
ORB_RETENTION_START = "09:30"
ORB_RETENTION_END = "09:35"


def _retain_session_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Retain the current session's opening-range bars plus the recent window.

    ``frame`` is a single-session, Eastern-time-indexed regular-session frame.
    Returns a UTC-indexed frame containing the 09:30-09:35 ET formation bars
    unioned with the most recent ``MAX_INTRADAY_RETURN_BARS`` bars, so the ORB
    formation window survives the ordinary rolling truncation (PRD-271).
    """
    opening = frame.between_time(ORB_RETENTION_START, ORB_RETENTION_END)
    recent = frame.tail(MAX_INTRADAY_RETURN_BARS)
    retained = pd.concat([opening, recent])
    retained = retained[~retained.index.duplicated(keep="first")].sort_index()
    retained.index = retained.index.tz_convert("UTC")
    return retained


def fetch_intraday_bars(
    symbol: str,
    *,
    retain_opening_range: bool = False,
    retain_full_session: bool = False,
    timeout_seconds: Optional[float] = None,
    retries: Optional[int] = None,
) -> Optional[pd.DataFrame]:
    """Fetch the current regular session's 1-minute bars from yfinance.

    By default returns the last 120 regular-session bars as a CONTIGUOUS
    trailing window — the original shape every contiguous-window consumer (short
    gate, post-trade evaluation) relies on. When ``retain_opening_range`` is True
    the 09:30-09:35 ET formation bars are additionally retained (PRD-271) so the
    WATCH ORB producer can select the opening range by timestamp; that opt-in
    shape is NON-contiguous. When ``retain_full_session`` is True the COMPLETE
    09:30-16:00 ET regular session is returned with NO ``tail`` truncation
    (PRD-288 session VWAP) — this path sets its own 16:00 bound and must not
    inherit the default 15:30 bound. Failure is per-symbol and returns None.

    ``timeout_seconds`` and ``retries`` are append-only overrides (PRD-323 R11,
    A1-P best-effort acquisition budget). Both default to ``None`` = current
    behavior: ``retries`` falls back to ``config.FETCH_RETRIES`` and no explicit
    ``timeout`` is passed to ``yf.download`` (yfinance keeps its own default). A
    caller passing ``timeout_seconds`` supplies a best-effort per-socket-operation
    timeout to ``yf.download`` (NOT an OS-level hard kill); ``retries=1`` yields a
    single attempt with no backoff. Existing callers pass neither, so their
    fetch behavior is byte-for-byte unchanged.
    """
    if _is_live_data_blocked():
        raise RuntimeError("LIVE_DATA_FORBIDDEN_IN_SUNDAY_MODE")
    def _do_download() -> pd.DataFrame:
        df = yf.download(
            symbol,
            period="7d",
            interval="1m",
            auto_adjust=False,
            progress=False,
            prepost=False,
            multi_level_index=False,
            # PRD-323 R11: pass timeout ONLY when overridden, so existing
            # callers' yf.download call is byte-for-byte unchanged.
            **({"timeout": timeout_seconds} if timeout_seconds is not None else {}),
        )
        if df.empty:
            raise ValueError("yfinance returned empty intraday DataFrame")
        df.columns = [
            c.capitalize() if c.lower() in ("open", "high", "low", "close", "volume") else c
            for c in df.columns
        ]
        frame = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        idx = pd.to_datetime(frame.index)
        if idx.tz is None:
            idx = idx.tz_localize("UTC")
        frame.index = idx.tz_convert("America/New_York")
        session_end = "16:00" if retain_full_session else "15:30"
        frame = frame.between_time("09:30", session_end)
        if frame.empty:
            raise ValueError("no regular-session intraday bars")
        latest_date = frame.index[-1].date()
        frame = frame.loc[frame.index.date == latest_date]
        if frame.empty:
            raise ValueError("no bars for latest session date")
        if retain_full_session:
            frame.index = frame.index.tz_convert("UTC")
            return frame
        if retain_opening_range:
            return _retain_session_frame(frame)
        frame.index = frame.index.tz_convert("UTC")
        return frame.tail(MAX_INTRADAY_RETURN_BARS)

    # PRD-323 R11: `retries` defaults to config.FETCH_RETRIES (existing
    # behavior). A1-P passes retries=1 => a single attempt with no backoff.
    effective_retries = config.FETCH_RETRIES if retries is None else retries
    last_error: Optional[str] = None
    for attempt in range(effective_retries):
        try:
            df = _run_with_timeout(_do_download, config.FETCH_TIMEOUT_SECONDS * 3)
            logger.info("%s: intraday fetched %d bars from yfinance", symbol, len(df))
            return df
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "%s: intraday attempt %d/%d failed: %s",
                symbol,
                attempt + 1,
                effective_retries,
                exc,
            )
            if attempt < effective_retries - 1:
                time.sleep(config.FETCH_BACKOFF_SECONDS)

    logger.info("%s: intraday unavailable for WATCH — %s", symbol, last_error)
    return None


def fetch_intraday_orb_bars(symbol: str) -> Optional[pd.DataFrame]:
    """WATCH ORB producer's intraday fetch: contiguous window PLUS the retained
    09:30-09:35 ET opening-range formation bars (PRD-271). Scoping the retention
    to this entry point keeps it off every contiguous-window consumer."""
    return fetch_intraday_bars(symbol, retain_opening_range=True)


def fetch_intraday_session_bars(
    symbol: str,
    *,
    timeout_seconds: Optional[float] = None,
    retries: Optional[int] = None,
) -> Optional[pd.DataFrame]:
    """SPY session-VWAP producer's intraday fetch (PRD-288): the COMPLETE
    09:30-16:00 ET regular session, UTC-indexed, with no ``tail`` truncation.
    Scoping the full-session shape to this entry point keeps it off every
    contiguous-window consumer and the WATCH ORB producer.

    ``timeout_seconds``/``retries`` are append-only pass-throughs (PRD-323 R11);
    both default to None = existing behavior. Existing callers pass neither."""
    return fetch_intraday_bars(
        symbol,
        retain_full_session=True,
        timeout_seconds=timeout_seconds,
        retries=retries,
    )


# ---------------------------------------------------------------------------
# yfinance
# ---------------------------------------------------------------------------

def _try_yfinance_quote(symbol: str) -> RawQuote:
    """Attempt yfinance fetch with retries and per-attempt timeout."""
    fetched_at = datetime.now(timezone.utc)
    start = time.monotonic()
    last_error: Optional[str] = None

    for attempt in range(config.FETCH_RETRIES):
        try:
            price, pct_change, volume = _run_with_timeout(
                lambda: _yfinance_quote_raw(symbol),
                config.FETCH_TIMEOUT_SECONDS,
            )
            duration = time.monotonic() - start
            logger.info(
                f"yfinance {symbol}: price={price:.4f} "
                f"pct={pct_change:+.4f} vol={volume} "
                f"attempt={attempt + 1} duration={duration:.2f}s"
            )
            return RawQuote(
                symbol=symbol,
                price=price,
                pct_change_raw=pct_change,
                volume=volume,
                fetched_at_utc=fetched_at,
                source="yfinance",
                fetch_succeeded=True,
                failure_reason=None,
            )
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                f"yfinance {symbol} attempt {attempt + 1}/{config.FETCH_RETRIES} failed: {exc}"
            )
            if attempt < config.FETCH_RETRIES - 1:
                time.sleep(config.FETCH_BACKOFF_SECONDS)

    duration = time.monotonic() - start
    logger.error(
        f"yfinance {symbol}: all {config.FETCH_RETRIES} attempts failed "
        f"(duration={duration:.2f}s) — last error: {last_error}"
    )
    return RawQuote(
        symbol=symbol,
        price=0.0,
        pct_change_raw=0.0,
        volume=None,
        fetched_at_utc=fetched_at,
        source="yfinance",
        fetch_succeeded=False,
        failure_reason=last_error,
    )


def _yfinance_quote_raw(symbol: str) -> tuple[float, float, Optional[float]]:
    """Inner yfinance fetch — returns (price, pct_change_decimal, volume).

    Raises on any failure so the retry wrapper can catch and log it.
    """
    ticker = yf.Ticker(symbol)
    info = ticker.fast_info

    price = info.last_price
    if price is None:
        raise ValueError("fast_info.last_price is None")
    price = float(price)
    if math.isnan(price) or price <= 0:
        raise ValueError(f"fast_info.last_price invalid: {price}")

    prev_close = info.previous_close
    if (
        prev_close is None
        or not math.isfinite(float(prev_close))
        or float(prev_close) <= 0
    ):
        # PRD-262: a fabricated pct_change=0.0 reads as market-unchanged and
        # silently disarms the pct-based stress guards; fail loud instead.
        raise ValueError(f"fast_info.previous_close invalid: {prev_close!r}")
    pct_change = (price - float(prev_close)) / float(prev_close)

    volume: Optional[float] = None
    try:
        v = info.last_volume
        if v is not None and not math.isnan(float(v)):
            volume = float(v)
    except Exception:
        pass

    return price, pct_change, volume


# ---------------------------------------------------------------------------
# FRED (public CSV) — the actual US 2Y Treasury yield carrier (PRD-335 D-1)
# ---------------------------------------------------------------------------
#
# The repo's FIRST non-yfinance carrier. It is deliberately bounded to a single
# FRED series (DGS2) fetched from the public CSV endpoint (no API key, no paid
# tier). It never touches yf.Ticker and inherits the never-raises / per-symbol
# isolation contract of fetch_quote. Any growth beyond "one CSV branch + the
# as_of field" is a STOP-and-report boundary (PRD-335 R3), not a silent
# expansion into a rates-platform abstraction.

# PRD-336 R2: DGS5 (actual US 5Y yield) joins DGS2 on the same bounded FRED
# carrier. Each is a separate small per-symbol request (never a combined
# id=DGS2,DGS5 fetch) so per-symbol never-raises isolation holds.
_FRED_SERIES_BY_SYMBOL = {"DGS2": "DGS2", "DGS5": "DGS5"}
# Bounded staleness window for a DAILY observation, weekend/holiday tolerant
# (PRD-335 R2): a row DATE older than this many CALENDAR days fails the fetch
# closed, so the optional driver renders "--" — never a stale number with a date.
_FRED_MAX_ASOF_AGE_DAYS = 5
# PRD-336 R3: bound the request to a recent window (cosd) so a single hourly fetch
# returns ~a dozen rows, not the full multi-decade series (~1000x smaller). This
# is a reliability MITIGATION for the observed intermittent full-series timeouts,
# not a proven root-cause fix; the fail-closed "--" path remains the safety net.
# The window must comfortably exceed the 5-day staleness gate so >= 2 usable rows
# are returned across long weekends/holidays.
_FRED_WINDOW_DAYS = 14


def _fred_csv_url(series_id: str, start: date) -> str:
    # PRD-336 R3: `cosd` (change-observation-start-date) bounds the window to the
    # recent past; the end defaults to the latest available observation.
    return (
        "https://fred.stlouisfed.org/graph/fredgraph.csv"
        f"?id={series_id}&cosd={start.isoformat()}"
    )


def _fetch_fred_csv(url: str, timeout_seconds: float) -> str:
    """Fetch a FRED CSV over HTTP; raises on any network/HTTP failure so the
    caller can catch it. Isolated from parsing so tests inject canned CSV."""
    req = Request(url, headers={"User-Agent": "cuttingboard/1.0"})
    with urlopen(req, timeout=timeout_seconds) as resp:  # noqa: S310 (fixed https host)
        return resp.read().decode("utf-8")


def _parse_fred_csv(text: str, today: date, series_id: str) -> tuple[float, float, date]:
    """Parse a single-series FRED CSV into (yield, pct_change_decimal, as_of).

    PRD-336 R3: generalized from the DGS2-only parser to serve any single-series
    ``observation_date,<series_id>`` CSV (DGS2 and DGS5). The value column is
    verified against ``series_id`` (assert the resolved series, not the requested;
    PRD-198 #2) so a wrong-series response fails closed. A missing observation is
    the literal ``"."``. The last two non-``"."`` rows are used: the latest is the
    observed yield, the prior is the change base. Raises ``ValueError`` on any
    malformed, wrong-series, future-dated, or stale (older than the
    5-calendar-day window) input so the fetch fails CLOSED — a daily value is
    never presented as a stale or fabricated number. ``today`` is the caller's
    reference date.
    """
    rows: list[tuple[date, float]] = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        raise ValueError(f"{series_id} CSV empty")
    header = [c.strip() for c in lines[0].split(",")]
    if len(header) < 2 or header[1] != series_id:
        raise ValueError(f"{series_id} CSV header mismatch: {lines[0]!r}")
    for line in lines[1:]:  # skip the header row
        parts = line.split(",")
        if len(parts) < 2:
            continue
        raw_date, raw_value = parts[0].strip(), parts[1].strip()
        if raw_value == "." or not raw_value:
            continue  # FRED's missing-observation marker
        obs_date = date.fromisoformat(raw_date)  # raises on a malformed date
        obs_value = float(raw_value)             # raises on a malformed number
        rows.append((obs_date, obs_value))
    if len(rows) < 2:
        raise ValueError(f"{series_id} CSV lacks two usable observations")
    _, prev_yield = rows[-2]
    as_of, latest_yield = rows[-1]
    if not (prev_yield > 0 and latest_yield > 0):
        raise ValueError(f"{series_id} yields must be positive")
    if as_of > today:
        raise ValueError(f"{series_id} as-of {as_of.isoformat()} is in the future")
    if (today - as_of).days > _FRED_MAX_ASOF_AGE_DAYS:
        raise ValueError(
            f"{series_id} as-of {as_of.isoformat()} stale "
            f"(> {_FRED_MAX_ASOF_AGE_DAYS} calendar days)"
        )
    pct_change = (latest_yield - prev_yield) / prev_yield
    return latest_yield, pct_change, as_of


def _try_fred_quote(symbol: str) -> RawQuote:
    """Fetch a FRED-series quote (currently DGS2 = the US 2Y yield). Never raises;
    a network or data failure returns fetch_succeeded=False so the optional driver
    is dropped in normalization and renders "--" (fail-loud, no stale fallback)."""
    fetched_at = datetime.now(timezone.utc)
    series_id = _FRED_SERIES_BY_SYMBOL.get(symbol)
    if series_id is None:
        return RawQuote(symbol, 0.0, 0.0, None, fetched_at, "fred", False,
                        f"no FRED series mapped for {symbol}")

    url = _fred_csv_url(series_id, fetched_at.date() - timedelta(days=_FRED_WINDOW_DAYS))
    last_error: Optional[str] = None
    text: Optional[str] = None
    for attempt in range(config.FETCH_RETRIES):
        try:
            text = _run_with_timeout(
                lambda: _fetch_fred_csv(url, config.FETCH_TIMEOUT_SECONDS),
                config.FETCH_TIMEOUT_SECONDS * 3,
            )
            break
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                f"fred {symbol} attempt {attempt + 1}/{config.FETCH_RETRIES} failed: {exc}"
            )
            if attempt < config.FETCH_RETRIES - 1:
                time.sleep(config.FETCH_BACKOFF_SECONDS)

    if text is None:
        logger.error(f"fred {symbol}: fetch unavailable — last error: {last_error}")
        return RawQuote(symbol, 0.0, 0.0, None, fetched_at, "fred", False, last_error)

    # Parse ONCE (deterministic; a stale/malformed CSV must not spin the retry
    # loop). fetched_at.date() is the staleness reference — fetched_at_utc itself
    # stays the acquisition clock so validation freshness is unchanged.
    try:
        price, pct_change, as_of = _parse_fred_csv(text, fetched_at.date(), series_id)
    except Exception as exc:
        logger.info(f"fred {symbol}: unusable CSV — {exc}")
        return RawQuote(symbol, 0.0, 0.0, None, fetched_at, "fred", False, str(exc))

    logger.info(
        f"fred {symbol}: yield={price:.4f} pct={pct_change:+.4f} as_of={as_of.isoformat()}"
    )
    return RawQuote(
        symbol=symbol,
        price=price,
        pct_change_raw=pct_change,
        volume=None,
        fetched_at_utc=fetched_at,
        source="fred",
        fetch_succeeded=True,
        failure_reason=None,
        as_of=as_of,
    )


def _fetch_ohlcv_from_yfinance(symbol: str) -> Optional[pd.DataFrame]:
    """Download 6 months of daily OHLCV from yfinance with retries."""
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=config.OHLCV_FETCH_MONTHS * 31)

    def _do_download() -> pd.DataFrame:
        df = yf.download(
            symbol,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
            multi_level_index=False,
        )
        if df.empty:
            raise ValueError("yfinance returned empty OHLCV DataFrame")
        # Normalise column names — yfinance sometimes returns title-cased
        df.columns = [c.capitalize() if c.lower() in ("open", "high", "low", "close", "volume") else c
                      for c in df.columns]
        return df[["Open", "High", "Low", "Close", "Volume"]].copy()

    last_error: Optional[str] = None
    for attempt in range(config.FETCH_RETRIES):
        try:
            df = _run_with_timeout(_do_download, config.FETCH_TIMEOUT_SECONDS * 3)
            logger.info(f"{symbol}: OHLCV fetched {len(df)} bars from yfinance")
            return df
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                f"{symbol}: OHLCV attempt {attempt + 1}/{config.FETCH_RETRIES} failed: {exc}"
            )
            if attempt < config.FETCH_RETRIES - 1:
                time.sleep(config.FETCH_BACKOFF_SECONDS)

    logger.error(f"{symbol}: OHLCV all attempts failed — last error: {last_error}")
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_with_timeout(fn, timeout_seconds: float):
    """Run fn() in a thread, raising TimeoutError if it exceeds the limit."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(fn)
        try:
            return future.result(timeout=timeout_seconds)
        except FuturesTimeoutError:
            raise TimeoutError(f"fetch timed out after {timeout_seconds}s")


def _ohlcv_cache_path(symbol: str) -> Path:
    """Return the parquet cache path for a symbol's OHLCV data."""
    safe = symbol.replace("^", "").replace("-", "_").replace(".", "_").upper()
    return Path(config.OHLCV_CACHE_DIR) / f"{safe}_ohlcv.parquet"


def _write_ohlcv_cache(symbol: str, cache_path: Path, df: pd.DataFrame) -> None:
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path)
        logger.debug(f"{symbol}: OHLCV cached to {cache_path}")
    except Exception as exc:
        logger.warning(f"{symbol}: OHLCV cache write failed: {exc}")
