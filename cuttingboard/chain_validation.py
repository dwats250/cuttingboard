"""
Layer 10 — Options Chain Validation Gate.

Late-stage gate: runs only after all upstream layers pass. Fetches real
options chain data and checks whether a qualified OptionSetup can be
executed against a liquid, efficient market.

Data source priority:
  1. yfinance   — primary (always attempted)
  2. yahooquery — fallback (skipped if not installed)

Single-retry model — no loops. Any fetch failure yields NEEDS_MANUAL_CHECK.
Manual broker confirmation (Moomoo) occurs outside this system.

Classification outputs
----------------------
  TOP_TRADE_VALIDATED          — all gates pass
  WATCHLIST_OPTIONS_WEAK       — spread 8–15% or marginal execution quality
  TOP_TRADE_CHAIN_FAILED       — structure good, chain bad (expiry out of range)
  DISQUALIFIED_OPTIONS_INVALID — hard liquidity or spread failure; broken chain
  NEEDS_MANUAL_CHECK           — data unavailable, ambiguous, or broken quotes

Hard gates (immediate DISQUALIFIED_OPTIONS_INVALID)
  Liquidity : OI ≥ 200, volume ≥ 20, bid > 0, ask > 0
  Spread    : > 15% of mid
  Consistency: isolated OI spike (best > 10× median neighbors)

Soft issue (WATCHLIST_OPTIONS_WEAK)
  Spread    : 8–15% of mid
  Execution : bid < $0.10, OR (OI < 400 AND volume < 40)

Structure gate (TOP_TRADE_CHAIN_FAILED)
  Expiry    : DTE outside [50%, 250%] of target

Ambiguous issues (NEEDS_MANUAL_CHECK)
  Sanity    : inverted quote (ask < bid), zero strike
  Consistency: irregular strike gaps, excessive spread variance across strikes
"""

import logging
import math
from dataclasses import dataclass
from datetime import date
from typing import Optional

import pandas as pd
import yfinance as yf

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

_MIN_OI        = 200     # ≥ 200 open interest required
_MIN_VOLUME    = 20      # ≥ 20 volume required
_SPREAD_PASS   = 0.08    # ≤ 8%  → PASS
_SPREAD_WEAK   = 0.15    # 8–15% → WEAK; > 15% → FAIL
_MIN_DTE_MULT  = 0.50    # expiry must be ≥ 50% of target DTE
_MAX_DTE_MULT  = 2.50    # expiry must be ≤ 250% of target DTE
_STRIKE_BAND   = 10      # evaluate ≤ N strikes nearest to ATM

# Internal consistency thresholds
_MAX_GAP_MULT       = 3.0   # any gap > N × median gap → irregular spacing
_OI_SPIKE_MULT      = 10.0  # best OI > N × median OI → isolated spike
_MAX_SPREAD_RATIO   = 5.0   # max/min spread_pct across strikes > N → unstable

# Execution reality filter thresholds
_MIN_BID_EXECUTION  = 0.10  # bid < $0.10 → near-zero bid, unpredictable fills
_MIN_OI_EXECUTION   = 400   # OI below this (but ≥ _MIN_OI) is thin for execution
_MIN_VOL_EXECUTION  = 40    # volume below this (but ≥ _MIN_VOLUME) is thin

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
    """8-step chain validation pipeline for one OptionSetup.

    Steps:
      1  Fetch chain (yfinance → yahooquery)
      2  Select nearest expiry to target DTE
      3  Expiry fit gate
      4  Contract selection — filter near ATM, pick best by OI
      5  Structural pricing sanity (per-contract)
      6  Liquidity gate + spread gate (per-contract, hard fails)
      7  Internal consistency validation (across near-ATM strikes)
      8  Execution reality filter (soft downgrade)
    """
    # Step 1 — Fetch chain
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

    # Step 3 — Expiry fit gate
    if not _expiry_fit_ok(expiry_dte, setup.dte):
        return _result(
            setup.symbol, CHAIN_FAILED,
            f"expiry DTE {expiry_dte} outside window for target {setup.dte}",
            expiry=expiry, source=source,
        )

    if not current_price or current_price <= 0:
        return _result(
            setup.symbol, MANUAL_CHECK,
            "underlying price unavailable", expiry=expiry, source=source,
        )

    # Step 4 — Contract selection
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

    # Step 5 — Structural pricing sanity (per-contract)
    ev = _eval_contract(best_row)
    if ev is None:
        return _result(setup.symbol, MANUAL_CHECK, "contract evaluation error", expiry=expiry, source=source)

    if not ev.sanity_ok:
        return _result(
            setup.symbol, MANUAL_CHECK, "structural pricing sanity failed",
            spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
            expiry=expiry, source=source,
        )

    # Step 6 — Liquidity gate (hard fail)
    if not ev.liquidity_ok:
        return _result(
            setup.symbol, OPTIONS_INVALID,
            f"liquidity fail: OI={ev.open_interest} vol={ev.volume} "
            f"bid={ev.bid:.2f} ask={ev.ask:.2f}",
            spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
            expiry=expiry, source=source,
        )

    # Step 6 — Spread gate (hard fail)
    if ev.spread_grade == "FAIL":
        return _result(
            setup.symbol, OPTIONS_INVALID,
            f"spread too wide: {ev.spread_pct:.1%}",
            spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
            expiry=expiry, source=source,
        )

    # Step 7 — Internal consistency validation (across near-ATM strikes)
    consistency_reason = _internal_consistency_check(near_atm)
    if consistency_reason is not None:
        # Isolated OI spike is a hard chain integrity failure
        if "isolated" in consistency_reason:
            return _result(
                setup.symbol, OPTIONS_INVALID, consistency_reason,
                spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
                expiry=expiry, source=source,
            )
        # Other consistency issues are ambiguous — flag for manual review
        return _result(
            setup.symbol, MANUAL_CHECK, consistency_reason,
            spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
            expiry=expiry, source=source,
        )

    # Step 8 — Execution reality filter (soft downgrade)
    execution_reason = _execution_reality_check(ev)
    if execution_reason is not None:
        return _result(
            setup.symbol, OPTIONS_WEAK, execution_reason,
            spread_pct=ev.spread_pct, oi=ev.open_interest, vol=ev.volume,
            expiry=expiry, source=source,
        )

    # Final classification
    if ev.spread_grade == "WEAK":
        return _result(
            setup.symbol, OPTIONS_WEAK,
            f"spread {ev.spread_pct:.1%} (8–15% range)",
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
# Strike selection and per-contract evaluation
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

    Returns None only if numeric parsing fails entirely.
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
# Step 7 — Internal consistency validation (across near-ATM strikes)
# ---------------------------------------------------------------------------

def _internal_consistency_check(near_atm: pd.DataFrame) -> Optional[str]:
    """Check chain integrity across multiple strikes.

    Requires ≥ 3 strikes to be meaningful. Returns None if chain is
    internally consistent, or a reason string if a problem is detected.

    Checks:
      1. Strike continuity — no large irregular gaps between adjacent strikes
      2. Liquidity clustering — reject isolated OI spikes with thin neighbors
      3. Spread stability — reject if spread varies excessively across strikes
    """
    if len(near_atm) < 3:
        return None

    strikes = sorted(near_atm["strike"].dropna().tolist())

    # 1. Strike continuity
    if len(strikes) >= 2:
        gaps = [strikes[i + 1] - strikes[i] for i in range(len(strikes) - 1)]
        sorted_gaps = sorted(gaps)
        # Use lower median so one large gap doesn't inflate the reference value.
        median_gap = sorted_gaps[(len(sorted_gaps) - 1) // 2]
        if median_gap > 0 and any(g > _MAX_GAP_MULT * median_gap for g in gaps):
            return "irregular strike spacing detected"

    # 2. Liquidity clustering — isolated OI spike
    if "openInterest" in near_atm.columns:
        oi_vals = [_safe_float(v) for v in near_atm["openInterest"].tolist()]
        positive_oi = [v for v in oi_vals if v > 0]
        if len(positive_oi) >= 3:
            sorted_oi = sorted(positive_oi)
            median_oi = sorted_oi[len(sorted_oi) // 2]
            max_oi = sorted_oi[-1]
            if median_oi > 0 and max_oi > _OI_SPIKE_MULT * median_oi:
                return "isolated OI spike — thin liquidity cluster"

    # 3. Spread stability
    if "bid" in near_atm.columns and "ask" in near_atm.columns:
        sp_vals: list[float] = []
        for _, row in near_atm.iterrows():
            b = _safe_float(row.get("bid", 0))
            a = _safe_float(row.get("ask", 0))
            mid = (b + a) / 2.0
            if mid > 0 and a >= b:
                sp_vals.append((a - b) / mid)

        if len(sp_vals) >= 3:
            sorted_sp = sorted(sp_vals)
            min_sp = sorted_sp[0]
            max_sp = sorted_sp[-1]
            if min_sp > 0.001 and max_sp > _MAX_SPREAD_RATIO * min_sp:
                return "spread varies excessively across strikes"

    return None


# ---------------------------------------------------------------------------
# Step 8 — Execution reality filter (soft downgrade)
# ---------------------------------------------------------------------------

def _execution_reality_check(ev: _ContractEval) -> Optional[str]:
    """Soft downgrade: check whether this trade would realistically fill well.

    Called after all hard gates pass. Returns a downgrade reason if execution
    quality is marginal, or None if the trade looks fillable.

    Near-zero bid: market-maker interest is nearly absent — fills unpredictable.
    Thin OI + volume: the contract technically passes thresholds but is borderline
    in both dimensions simultaneously, making real execution unreliable.
    """
    if ev.bid < _MIN_BID_EXECUTION:
        return f"near-zero bid ${ev.bid:.2f} — fill risk too high"

    if ev.open_interest < _MIN_OI_EXECUTION and ev.volume < _MIN_VOL_EXECUTION:
        return (
            f"thin execution quality: OI={ev.open_interest} vol={ev.volume} "
            f"(both below reliable fill threshold)"
        )

    return None


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
