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
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pandas as pd
import requests
import yfinance as yf

from cuttingboard import config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RawQuote:
    symbol: str
    price: float
    pct_change_raw: float       # decimal: 5.2% is stored as 0.052
    volume: Optional[float]
    fetched_at_utc: datetime    # UTC with tzinfo — never naive
    source: str                 # "yfinance" | "polygon"
    fetch_succeeded: bool
    failure_reason: Optional[str]


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
        elif source == "polygon":
            result = _try_polygon_quote(symbol)
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
    if df is None or df.empty or df.index.empty:
        return False

    last_bar = pd.Timestamp(df.index.max())
    if last_bar.tzinfo is None:
        last_bar = last_bar.tz_localize(timezone.utc)
    else:
        last_bar = last_bar.tz_convert(timezone.utc)

    age_seconds = (datetime.now(timezone.utc) - last_bar.to_pydatetime()).total_seconds()
    max_age_seconds = config.OHLCV_STALE_HOURS * 60 * 60
    return 0 <= age_seconds < max_age_seconds


def fetch_intraday_bars(symbol: str) -> Optional[pd.DataFrame]:
    """Fetch the current regular session's 1-minute bars from yfinance.

    Returns up to the last 120 regular-session bars for the latest session date.
    Failure is per-symbol and returns None without raising.
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
        frame = frame.between_time("09:30", "15:30")
        if frame.empty:
            raise ValueError("no regular-session intraday bars")
        latest_date = frame.index[-1].date()
        frame = frame.loc[frame.index.date == latest_date]
        if frame.empty:
            raise ValueError("no bars for latest session date")
        frame.index = frame.index.tz_convert("UTC")
        return frame.tail(120)

    last_error: Optional[str] = None
    for attempt in range(config.FETCH_RETRIES):
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
                config.FETCH_RETRIES,
                exc,
            )
            if attempt < config.FETCH_RETRIES - 1:
                time.sleep(config.FETCH_BACKOFF_SECONDS)

    logger.info("%s: intraday unavailable for WATCH — %s", symbol, last_error)
    return None


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
        prev_close is not None
        and not math.isnan(float(prev_close))
        and float(prev_close) > 0
    ):
        pct_change = (price - float(prev_close)) / float(prev_close)
    else:
        pct_change = 0.0
        logger.debug(f"{symbol}: previous_close unavailable, pct_change defaulted to 0.0")

    volume: Optional[float] = None
    try:
        v = info.last_volume
        if v is not None and not math.isnan(float(v)):
            volume = float(v)
    except Exception:
        pass

    return price, pct_change, volume


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
# Polygon fallback
# ---------------------------------------------------------------------------

def _try_polygon_quote(symbol: str) -> RawQuote:
    """Attempt Polygon.io previous-day aggregate as quote fallback."""
    fetched_at = datetime.now(timezone.utc)

    if not config.POLYGON_API_KEY:
        return RawQuote(
            symbol=symbol,
            price=0.0,
            pct_change_raw=0.0,
            volume=None,
            fetched_at_utc=fetched_at,
            source="polygon",
            fetch_succeeded=False,
            failure_reason="POLYGON_API_KEY not set in .env",
        )

    url = config.POLYGON_PREV_URL.format(symbol=symbol)
    last_error: Optional[str] = None

    for attempt in range(config.FETCH_RETRIES):
        try:
            price, pct_change, volume = _run_with_timeout(
                lambda: _polygon_quote_raw(url),
                config.FETCH_TIMEOUT_SECONDS,
            )
            logger.warning(
                f"polygon fallback used for {symbol}: "
                f"price={price:.4f} pct={pct_change:+.4f} (prev-day close, 15-min delayed)"
            )
            return RawQuote(
                symbol=symbol,
                price=price,
                pct_change_raw=pct_change,
                volume=volume,
                fetched_at_utc=fetched_at,
                source="polygon",
                fetch_succeeded=True,
                failure_reason=None,
            )
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                f"polygon {symbol} attempt {attempt + 1}/{config.FETCH_RETRIES} failed: {exc}"
            )
            if attempt < config.FETCH_RETRIES - 1:
                time.sleep(config.FETCH_BACKOFF_SECONDS)

    return RawQuote(
        symbol=symbol,
        price=0.0,
        pct_change_raw=0.0,
        volume=None,
        fetched_at_utc=fetched_at,
        source="polygon",
        fetch_succeeded=False,
        failure_reason=last_error,
    )


def _polygon_quote_raw(url: str) -> tuple[float, float, Optional[float]]:
    """Inner Polygon fetch — returns (price, pct_change_decimal, volume).

    Uses the /v2/aggs/ticker/{symbol}/prev endpoint (previous trading day).
    price   = previous day close
    pct_change = (close - open) / open for that session
    """
    resp = requests.get(
        url,
        params={"apiKey": config.POLYGON_API_KEY},
        timeout=config.FETCH_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results") or []
    if not results:
        raise ValueError(f"polygon response has no results: {data}")

    r = results[0]
    close = float(r["c"])
    open_ = float(r["o"])
    raw_vol = r.get("v")

    if close <= 0:
        raise ValueError(f"polygon close price invalid: {close}")
    if open_ <= 0:
        raise ValueError(f"polygon open price invalid: {open_}")

    pct_change = (close - open_) / open_
    volume: Optional[float] = float(raw_vol) if raw_vol is not None else None

    return close, pct_change, volume


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
