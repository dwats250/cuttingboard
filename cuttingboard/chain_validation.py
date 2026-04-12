"""
Layer 10 — Options Chain Validation Gate.

Late-stage gate: runs only after all upstream layers pass. Fetches real
options chain data and checks whether a qualified OptionSetup can be
executed against a liquid, efficient market.

Data source priority:
  1. yfinance   — primary (always attempted)
  2. yahooquery — fallback (skipped if not installed)
  3. Tradier    — conditional (API key required; top-tier + spread near threshold)

Single-retry model — no loops. Any fetch failure yields NEEDS_MANUAL_CHECK.

Classification outputs
----------------------
  TOP_TRADE_VALIDATED        — all gates pass
  WATCHLIST_OPTIONS_WEAK     — spread is 10–20% (minor issue)
  TOP_TRADE_CHAIN_FAILED     — structure good, chain bad (expiry, spread > 20%)
  DISQUALIFIED_OPTIONS_INVALID — hard liquidity failure
  NEEDS_MANUAL_CHECK         — data unavailable or broken quotes

Hard gates (immediate DISQUALIFIED_OPTIONS_INVALID)
  Liquidity : OI ≥ 100, volume ≥ 10, bid > 0, ask > 0
  Spread    : > 20% of mid

Soft issue (WATCHLIST_OPTIONS_WEAK)
  Spread    : 10–20% of mid

Structure gates (TOP_TRADE_CHAIN_FAILED)
  Expiry    : DTE outside [50%, 250%] of target
  Tradier   : IV > 500% (broken data sentinel)
"""

import logging
import math
from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf

from cuttingboard import config
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.options import (
    OptionSetup,
    BULL_CALL_SPREAD, BEAR_CALL_SPREAD,
    BULL_PUT_SPREAD, BEAR_PUT_SPREAD,
)

logger = logging.getLogger(__name__)

try:
    from yahooquery import Ticker as _YQTicker  # type: ignore
    _YAHOOQUERY_OK = True
except ImportError:
    _YAHOOQUERY_OK = False
    _YQTicker = None


# ---------------------------------------------------------------------------
# Classification constants
# ---------------------------------------------------------------------------

VALIDATED       = "TOP_TRADE_VALIDATED"
CHAIN_FAILED    = "TOP_TRADE_CHAIN_FAILED"
OPTIONS_WEAK    = "WATCHLIST_OPTIONS_WEAK"
OPTIONS_INVALID = "DISQUALIFIED_OPTIONS_INVALID"
MANUAL_CHECK    = "NEEDS_MANUAL_CHECK"


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

_MIN_OI        = 100
_MIN_VOLUME    = 10
_SPREAD_PASS   = 0.10    # ≤ 10% → PASS
_SPREAD_WEAK   = 0.20    # 10–20% → WEAK; > 20% → FAIL
_MIN_DTE_MULT  = 0.50    # expiry must be ≥ 50% of target DTE
_MAX_DTE_MULT  = 2.50    # expiry must be ≤ 250% of target DTE
_STRIKE_BAND   = 10      # evaluate ≤ N strikes nearest to ATM
_IV_SANITY_MAX = 5.0     # Tradier IV above this (500%) is a broken-data sentinel

_OPTION_TYPE: dict[str, str] = {
    BULL_CALL_SPREAD: "calls",
    BEAR_CALL_SPREAD: "calls",
    BULL_PUT_SPREAD:  "puts",
    BEAR_PUT_SPREAD:  "puts",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class _ContractEval:
    """Single-contract evaluation output."""
    strike:        float
    bid:           float
    ask:           float
    mid:           float
    spread_pct:    float
    open_interest: int
    volume:        int
    liquidity_ok:  bool
    spread_grade:  str    # PASS | WEAK | FAIL
    sanity_ok:     bool


@dataclass(frozen=True)
class ChainValidationResult:
    """Chain validation outcome for one OptionSetup."""
    symbol:         str
    classification: str            # one of the five constants above
    reason:         Optional[str]  # human-readable failure note; None on VALIDATED
    spread_pct:     Optional[float]
    open_interest:  Optional[int]
    volume:         Optional[int]
    expiry_used:    Optional[str]  # YYYY-MM-DD
    data_source:    Optional[str]  # "yfinance" | "yahooquery" | None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_option_chains(
    setups: list[OptionSetup],
    valid_quotes: dict[str, NormalizedQuote],
) -> dict[str, ChainValidationResult]:
    """Run chain validation for every OptionSetup.

    Called after build_option_setups() in run_pipeline(). Returns a dict
    mapping symbol → ChainValidationResult. Does not modify setups.
    """
    today = date.today()
    results: dict[str, ChainValidationResult] = {}

    for setup in setups:
        quote = valid_quotes.get(setup.symbol)
        current_price = quote.price if quote is not None else None
        result = _validate_setup(setup, current_price, today)
        results[setup.symbol] = result
        logger.info(
            "CHAIN %s: %s%s",
            setup.symbol,
            result.classification,
            f" — {result.reason}" if result.reason else "",
        )

    return results


# ---------------------------------------------------------------------------
# Setup-level validation pipeline
# ---------------------------------------------------------------------------

def _validate_setup(
    setup: OptionSetup,
    current_price: Optional[float],
    today: date,
) -> ChainValidationResult:
    """Full 7-step chain validation pipeline for one OptionSetup."""

    # Step 1 — Fetch chain (primary: yfinance; fallback: yahooquery)
    ticker, expirations, source = _fetch_chain_yfinance(setup.symbol)

    if ticker is None:
        logger.warning("%s: yfinance chain unavailable — trying yahooquery", setup.symbol)
        ticker, expirations, source = _fetch_chain_yahooquery(setup.symbol)

    if ticker is None:
        return _result(setup.symbol, MANUAL_CHECK, "chain data unavailable from all sources")

    # Step 2 — Expiry selection
    expiry = _select_expiry(expirations, setup.dte, today)
    if expiry is None:
        return _result(setup.symbol, MANUAL_CHECK, "no suitable expiry found", source=source)

    expiry_dte = (date.fromisoformat(expiry) - today).days

    # Step 5 — Expiry fit gate (checked early to short-circuit chain fetch)
    if not _expiry_fit_ok(expiry_dte, setup.dte):
        return _result(
            setup.symbol, CHAIN_FAILED,
            f"expiry DTE {expiry_dte} outside window for target {setup.dte}",
            expiry=expiry, source=source,
        )

    # Step 3 — Contract selection
    if not current_price or current_price <= 0:
        return _result(
            setup.symbol, MANUAL_CHECK,
            "underlying price unavailable", expiry=expiry, source=source,
        )

    opt_type = _OPTION_TYPE.get(setup.strategy, "calls")
    try:
        chain_df = _get_chain_df(ticker, source, expiry, opt_type)
    except Exception as exc:
        logger.warning("%s: chain retrieval error for %s: %s", setup.symbol, expiry, exc)
        return _result(setup.symbol, MANUAL_CHECK, "chain retrieval error", expiry=expiry, source=source)

    if chain_df is None or chain_df.empty:
        return _result(setup.symbol, MANUAL_CHECK, "empty chain", expiry=expiry, source=source)

    near_atm = _filter_near_atm(chain_df, current_price, _STRIKE_BAND)
    if near_atm.empty:
        return _result(setup.symbol, MANUAL_CHECK, "no strikes near ATM", expiry=expiry, source=source)

    best_row = _find_best_contract(near_atm)
    if best_row is None:
        return _result(setup.symbol, MANUAL_CHECK, "no evaluable contracts", expiry=expiry, source=source)

    # Step 6 — Structural pricing sanity
    ev = _eval_contract(best_row)
    if ev is None:
        return _result(setup.symbol, MANUAL_CHECK, "contract evaluation error", expiry=expiry, source=source)

    if not ev.sanity_ok:
        return _result(
            setup.symbol, MANUAL_CHECK, "structural pricing sanity failed",
            spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
            expiry=expiry, source=source,
        )

    # Step 4 — Liquidity gate (hard fail)
    if not ev.liquidity_ok:
        return _result(
            setup.symbol, OPTIONS_INVALID,
            f"liquidity fail: OI={ev.open_interest} vol={ev.volume} "
            f"bid={ev.bid:.2f} ask={ev.ask:.2f}",
            spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
            expiry=expiry, source=source,
        )

    # Step 4 — Spread gate
    if ev.spread_grade == "FAIL":
        return _result(
            setup.symbol, OPTIONS_INVALID,
            f"spread too wide: {ev.spread_pct:.1%}",
            spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
            expiry=expiry, source=source,
        )

    # Step 7 — Conditional Tradier validation (spread near threshold only)
    near_threshold = _SPREAD_PASS < ev.spread_pct <= _SPREAD_WEAK
    if near_threshold and _tradier_configured():
        tradier_ok = _tradier_iv_check(
            setup.symbol, expiry,
            float(best_row.get("strike", 0) if hasattr(best_row, "get") else getattr(best_row, "strike", 0)),
            opt_type,
        )
        if not tradier_ok:
            return _result(
                setup.symbol, CHAIN_FAILED,
                "Tradier IV validation failed — possible broken chain",
                spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
                expiry=expiry, source=source,
            )

    # Final classification
    if ev.spread_grade == "WEAK":
        return _result(
            setup.symbol, OPTIONS_WEAK,
            f"spread {ev.spread_pct:.1%} (10–20% range)",
            spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
            expiry=expiry, source=source,
        )

    return _result(
        setup.symbol, VALIDATED, None,
        spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
        expiry=expiry, source=source,
    )


# ---------------------------------------------------------------------------
# Chain fetch — yfinance (primary)
# ---------------------------------------------------------------------------

def _fetch_chain_yfinance(symbol: str) -> tuple:
    """Fetch options chain via yfinance. Single attempt, no retry.

    Returns (ticker, expirations, 'yfinance') on success,
            (None, [], None) on failure.
    """
    try:
        ticker = yf.Ticker(symbol)
        expirations = list(ticker.options or [])
        if not expirations:
            logger.warning("%s: yfinance returned no expirations", symbol)
            return None, [], None
        return ticker, expirations, "yfinance"
    except Exception as exc:
        logger.warning("%s: yfinance chain fetch error: %s", symbol, exc)
        return None, [], None


# ---------------------------------------------------------------------------
# Chain fetch — yahooquery (fallback)
# ---------------------------------------------------------------------------

def _fetch_chain_yahooquery(symbol: str) -> tuple:
    """Fetch options chain via yahooquery. Single attempt, no retry.

    Returns (df, expirations, 'yahooquery') on success,
            (None, [], None) on failure or if yahooquery not installed.
    """
    if not _YAHOOQUERY_OK or _YQTicker is None:
        return None, [], None
    try:
        t = _YQTicker(symbol)
        df = t.option_chain
        if df is None or isinstance(df, str):
            logger.warning("%s: yahooquery returned: %s", symbol, df)
            return None, [], None
        if isinstance(df, pd.DataFrame) and df.empty:
            return None, [], None
        expirations = sorted(
            df["expiration"].dt.strftime("%Y-%m-%d").unique().tolist()
        )
        return df, expirations, "yahooquery"
    except Exception as exc:
        logger.warning("%s: yahooquery chain fetch error: %s", symbol, exc)
        return None, [], None


# ---------------------------------------------------------------------------
# Chain DataFrame accessor
# ---------------------------------------------------------------------------

def _get_chain_df(
    ticker_or_df,
    source: str,
    expiry: str,
    opt_type: str,
) -> Optional[pd.DataFrame]:
    """Return the options DataFrame for a specific expiry and type."""
    if source == "yfinance":
        chain = ticker_or_df.option_chain(expiry)
        return chain.calls if opt_type == "calls" else chain.puts

    # yahooquery: full pre-fetched DataFrame
    df: pd.DataFrame = ticker_or_df
    yq_type = "calls" if opt_type == "calls" else "puts"
    mask = (
        (df["expiration"].dt.strftime("%Y-%m-%d") == expiry)
        & (df["optionType"] == yq_type)
    )
    return df[mask].copy().reset_index(drop=True)


# ---------------------------------------------------------------------------
# Expiry selection and fit
# ---------------------------------------------------------------------------

def _select_expiry(
    expirations: list[str], target_dte: int, today: date
) -> Optional[str]:
    """Return the expiry date string nearest to target_dte.

    Skips expirations with DTE < 1 (expired or expiring today).
    """
    best: Optional[str] = None
    best_diff = float("inf")

    for exp_str in expirations:
        try:
            exp_date = date.fromisoformat(exp_str)
        except ValueError:
            continue
        dte = (exp_date - today).days
        if dte < 1:
            continue
        diff = abs(dte - target_dte)
        if diff < best_diff:
            best_diff = diff
            best = exp_str

    return best


def _expiry_fit_ok(expiry_dte: int, target_dte: int) -> bool:
    """True if expiry_dte is within [50%, 250%] of target_dte."""
    min_dte = max(1, int(target_dte * _MIN_DTE_MULT))
    max_dte = int(target_dte * _MAX_DTE_MULT)
    return min_dte <= expiry_dte <= max_dte


# ---------------------------------------------------------------------------
# Strike selection and evaluation
# ---------------------------------------------------------------------------

def _filter_near_atm(
    chain_df: pd.DataFrame, current_price: float, n: int
) -> pd.DataFrame:
    """Return the n strike rows nearest to current_price."""
    if "strike" not in chain_df.columns:
        return pd.DataFrame()
    df = chain_df.copy()
    df["_dist"] = (df["strike"] - current_price).abs()
    return df.nsmallest(n, "_dist").drop(columns="_dist").reset_index(drop=True)


def _find_best_contract(contracts: pd.DataFrame) -> Optional[pd.Series]:
    """Return the contract with highest openInterest, falling back to first row."""
    if contracts.empty:
        return None
    if "openInterest" in contracts.columns:
        oi = contracts["openInterest"].fillna(0)
        return contracts.loc[oi.idxmax()]
    return contracts.iloc[0]


def _safe_float(val, default: float = 0.0) -> float:
    """Parse a value to float, treating None and NaN as default."""
    if val is None:
        return default
    try:
        f = float(val)
        return default if math.isnan(f) else f
    except (TypeError, ValueError):
        return default


def _safe_int(val, default: int = 0) -> int:
    """Parse a value to int, treating None and NaN as default."""
    return int(_safe_float(val, float(default)))


def _eval_contract(row: pd.Series) -> Optional[_ContractEval]:
    """Evaluate a single contract row for liquidity, spread, and sanity.

    Returns None only if numeric parsing fails entirely (should not occur
    with _safe_float/_safe_int, but kept for defensive completeness).
    """
    try:
        bid    = _safe_float(row.get("bid",          0))
        ask    = _safe_float(row.get("ask",          0))
        oi     = _safe_int(  row.get("openInterest", 0))
        vol    = _safe_int(  row.get("volume",       0))
        strike = _safe_float(row.get("strike",       0))
    except Exception as exc:
        logger.warning("contract eval parse error: %s", exc)
        return None

    # Sanity: non-negative bid/ask, no inverted quote, valid strike.
    # bid=0 + ask=0 is a liquidity problem, not a sanity problem.
    sanity_ok = bid >= 0 and ask >= 0 and ask >= bid and strike > 0

    if not sanity_ok:
        return _ContractEval(
            strike=strike, bid=bid, ask=ask, mid=0.0, spread_pct=1.0,
            open_interest=oi, volume=vol,
            liquidity_ok=False, spread_grade="FAIL", sanity_ok=False,
        )

    mid        = (bid + ask) / 2.0
    spread_pct = (ask - bid) / mid if mid > 0 else 1.0

    liquidity_ok = oi >= _MIN_OI and vol >= _MIN_VOLUME and bid > 0

    if spread_pct <= _SPREAD_PASS:
        grade = "PASS"
    elif spread_pct <= _SPREAD_WEAK:
        grade = "WEAK"
    else:
        grade = "FAIL"

    return _ContractEval(
        strike=strike, bid=bid, ask=ask, mid=mid, spread_pct=spread_pct,
        open_interest=oi, volume=vol,
        liquidity_ok=liquidity_ok, spread_grade=grade, sanity_ok=True,
    )


# ---------------------------------------------------------------------------
# Tradier conditional validation
# ---------------------------------------------------------------------------

def _tradier_configured() -> bool:
    """True when TRADIER_API_KEY is set in config."""
    return bool(getattr(config, "TRADIER_API_KEY", None))


def _tradier_iv_check(
    symbol: str,
    expiry: str,
    strike: float,
    opt_type: str,
) -> bool:
    """Spot-check IV sanity via Tradier. Conditional — only called when needed.

    Returns True  if IV looks valid, data is missing, or request fails.
    Returns False only on confirmed IV anomaly (IV > 500%).

    Never raises. All errors are treated as inconclusive (True = pass).
    """
    import requests as _req

    api_key = getattr(config, "TRADIER_API_KEY", None)
    if not api_key:
        return True

    tradier_type = "call" if opt_type == "calls" else "put"

    try:
        resp = _req.get(
            "https://api.tradier.com/v1/markets/options/chains",
            params={"symbol": symbol, "expiration": expiry, "greeks": "true"},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
            },
            timeout=config.FETCH_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        logger.warning("%s: Tradier request error: %s", symbol, exc)
        return True

    if resp.status_code != 200:
        logger.warning("%s: Tradier HTTP %d", symbol, resp.status_code)
        return True

    try:
        options = (resp.json().get("options") or {}).get("option") or []
    except Exception:
        return True

    for opt in options:
        try:
            if (
                abs(float(opt.get("strike", 0)) - strike) < 0.01
                and opt.get("option_type", "") == tradier_type
            ):
                iv_raw = (opt.get("greeks") or {}).get("mid_iv")
                if iv_raw is None:
                    return True  # missing Greeks → don't fail
                iv = float(iv_raw)
                if iv > _IV_SANITY_MAX:
                    logger.warning(
                        "%s: Tradier IV=%.0f%% exceeds sanity bound", symbol, iv * 100
                    )
                    return False
                return True
        except (TypeError, ValueError):
            continue

    return True  # strike not found → inconclusive → pass


# ---------------------------------------------------------------------------
# Result builder
# ---------------------------------------------------------------------------

def _result(
    symbol: str,
    classification: str,
    reason: Optional[str],
    spread_pct: Optional[float] = None,
    oi: Optional[int] = None,
    vol: Optional[int] = None,
    expiry: Optional[str] = None,
    source: Optional[str] = None,
) -> ChainValidationResult:
    return ChainValidationResult(
        symbol=symbol,
        classification=classification,
        reason=reason,
        spread_pct=spread_pct,
        open_interest=oi,
        volume=vol,
        expiry_used=expiry,
        data_source=source,
    )
