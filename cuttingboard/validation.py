"""
Layer 3 — Validation Gate.

Every field must pass every check. No exceptions. No silent fallbacks.

A symbol that fails any check is excluded from valid_quotes and logged.
If any HALT_SYMBOL fails, the entire pipeline is halted — no further
layers execute.

This is the most critical layer in the system. Do not weaken it.
"""

import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from cuttingboard import config
from cuttingboard.ingestion import RawQuote
from cuttingboard.normalization import NormalizedQuote

logger = logging.getLogger(__name__)

# Maximum age from validation perspective (15 minutes, as per PRD)
_TIMESTAMP_MAX_AGE_SECONDS = 900


@dataclass(frozen=True)
class SymbolValidation:
    symbol: str
    passed: bool
    failure_reason: Optional[str]


@dataclass(frozen=True)
class ValidationSummary:
    system_halted: bool
    halt_reason: Optional[str]
    failed_halt_symbols: list[str]
    results: dict[str, SymbolValidation]
    valid_quotes: dict[str, NormalizedQuote]
    invalid_symbols: dict[str, str]           # symbol → failure_reason
    symbols_attempted: int
    symbols_validated: int
    symbols_failed: int


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_quotes(
    normalized: dict[str, NormalizedQuote],
    fetch_failures: Optional[dict[str, str]] = None,
) -> ValidationSummary:
    """Validate all normalized quotes and compute system halt status.

    Args:
        normalized:     Output of normalize_quotes() — symbols that succeeded.
        fetch_failures: Optional mapping of symbol → reason for symbols that
                        never produced a NormalizedQuote (fetch_succeeded=False).
                        These are pre-registered as INVALID without running
                        field-level checks.

    Returns:
        ValidationSummary with system_halted=True if any HALT_SYMBOL failed.
    """
    results: dict[str, SymbolValidation] = {}
    valid_quotes: dict[str, NormalizedQuote] = {}
    invalid_symbols: dict[str, str] = {}

    # Pre-register symbols that failed before normalization
    for symbol, reason in (fetch_failures or {}).items():
        results[symbol] = SymbolValidation(symbol=symbol, passed=False, failure_reason=reason)
        invalid_symbols[symbol] = reason
        logger.warning(f"INVALID {symbol}: fetch failure — {reason}")

    # Run field-level checks on each normalized quote
    for symbol, quote in normalized.items():
        result = _validate_symbol(quote)
        results[symbol] = result
        if result.passed:
            valid_quotes[symbol] = quote
            logger.debug(f"VALID   {symbol}: price={quote.price:.4f} age={quote.age_seconds:.0f}s")
        else:
            invalid_symbols[symbol] = result.failure_reason
            logger.warning(f"INVALID {symbol}: {result.failure_reason}")

    # Determine halt: any HALT_SYMBOL missing or invalid triggers full stop
    failed_halt_symbols = [
        s for s in config.HALT_SYMBOLS
        if s not in results or not results[s].passed
    ]

    if failed_halt_symbols:
        halt_lines = []
        for s in failed_halt_symbols:
            reason = invalid_symbols.get(s, "symbol not fetched")
            halt_lines.append(f"{s} ({reason})")
            logger.critical(f"HALT SYMBOL FAILED: {s} — {reason}")

        halt_reason = "Failed: " + "; ".join(halt_lines)

        return ValidationSummary(
            system_halted=True,
            halt_reason=halt_reason,
            failed_halt_symbols=failed_halt_symbols,
            results=results,
            valid_quotes=valid_quotes,
            invalid_symbols=invalid_symbols,
            symbols_attempted=len(results),
            symbols_validated=len(valid_quotes),
            symbols_failed=len(invalid_symbols),
        )

    logger.info(
        f"Validation complete: {len(valid_quotes)}/{len(results)} symbols passed, "
        f"system_halted=False"
    )
    return ValidationSummary(
        system_halted=False,
        halt_reason=None,
        failed_halt_symbols=[],
        results=results,
        valid_quotes=valid_quotes,
        invalid_symbols=invalid_symbols,
        symbols_attempted=len(results),
        symbols_validated=len(valid_quotes),
        symbols_failed=len(invalid_symbols),
    )


# ---------------------------------------------------------------------------
# Per-symbol validation rules
# ---------------------------------------------------------------------------

def _validate_symbol(quote: NormalizedQuote) -> SymbolValidation:
    """Run all hard validation rules on a single NormalizedQuote.

    Rules are applied in order. The first failure short-circuits and returns
    INVALID with an explicit reason. All checks must pass for VALID.
    """
    symbol = quote.symbol

    # 1. Type check — price and pct_change must be float
    if not isinstance(quote.price, float):
        return _fail(symbol, f"price is {type(quote.price).__name__}, expected float")
    if not isinstance(quote.pct_change_decimal, float):
        return _fail(symbol, f"pct_change_decimal is {type(quote.pct_change_decimal).__name__}, expected float")

    # 2. NaN / Inf check on numeric fields
    if math.isnan(quote.price) or math.isinf(quote.price):
        return _fail(symbol, f"price is {quote.price}")
    if math.isnan(quote.pct_change_decimal) or math.isinf(quote.pct_change_decimal):
        return _fail(symbol, f"pct_change_decimal is {quote.pct_change_decimal}")

    # 3. Price must be positive
    if quote.price <= 0:
        return _fail(symbol, f"price {quote.price:.4f} is not positive")

    # 4. Freshness — recompute age at validation time for accuracy
    now_utc = datetime.now(timezone.utc)
    age_seconds = (now_utc - quote.fetched_at_utc).total_seconds()

    if age_seconds < -config.MAX_CLOCK_SKEW_SECONDS:
        return _fail(
            symbol,
            (
                f"fetched_at_utc is {-age_seconds:.0f}s in the future, "
                f"exceeds {config.MAX_CLOCK_SKEW_SECONDS}s clock skew tolerance"
            ),
        )

    if age_seconds >= config.FRESHNESS_SECONDS:
        return _fail(
            symbol,
            f"age {age_seconds:.0f}s exceeds {config.FRESHNESS_SECONDS}s freshness threshold",
        )

    # 5. Timestamp sanity — fetched_at_utc within the last 15 minutes
    if age_seconds > _TIMESTAMP_MAX_AGE_SECONDS:
        return _fail(
            symbol,
            f"fetched_at_utc is {age_seconds:.0f}s old, exceeds 15-minute timestamp threshold",
        )

    # 6. Price sanity bounds (per-symbol)
    if symbol in config.PRICE_BOUNDS:
        lo, hi = config.PRICE_BOUNDS[symbol]
        if not (lo <= quote.price <= hi):
            return _fail(
                symbol,
                f"price {quote.price:.4f} outside expected bounds [{lo}, {hi}]",
            )

    # 7. Pct change bounds — extreme daily moves are suspect
    if not (-0.25 < quote.pct_change_decimal < 0.25):
        return _fail(
            symbol,
            f"pct_change_decimal {quote.pct_change_decimal:.4f} outside [-0.25, 0.25] — suspect data",
        )

    return SymbolValidation(symbol=symbol, passed=True, failure_reason=None)


def _fail(symbol: str, reason: str) -> SymbolValidation:
    return SymbolValidation(symbol=symbol, passed=False, failure_reason=reason)


# ---------------------------------------------------------------------------
# Pipeline helper — build fetch_failures dict from raw quote results
# ---------------------------------------------------------------------------

def extract_fetch_failures(raw_quotes: dict[str, RawQuote]) -> dict[str, str]:
    """Return {symbol: reason} for every RawQuote with fetch_succeeded=False."""
    return {
        symbol: (raw.failure_reason or "fetch failed")
        for symbol, raw in raw_quotes.items()
        if not raw.fetch_succeeded
    }


# ---------------------------------------------------------------------------
# Convenience API — flat list for interactive / pipeline use
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationResult:
    """Per-symbol outcome with the quote attached for easy iteration."""
    symbol: str
    passed: bool
    failure_reason: Optional[str]
    quote: Optional[NormalizedQuote]    # None when validation failed


def validate_all(
    normalized: dict[str, NormalizedQuote],
    fetch_failures: Optional[dict[str, str]] = None,
) -> list[ValidationResult]:
    """Run validate_quotes and return a flat list sorted by symbol.

    System halt is printed to stderr when triggered; the list still contains
    every symbol so the caller can render a full status table.
    """
    import sys
    summary = validate_quotes(normalized, fetch_failures)

    if summary.system_halted:
        print(
            f"\n⚠  SYSTEM HALT — MACRO DATA INVALID\n{summary.halt_reason}\n"
            "DO NOT TRADE — DATA UNTRUSTWORTHY\n",
            file=sys.stderr,
        )

    results: list[ValidationResult] = []
    for symbol in sorted(summary.results):
        sv = summary.results[symbol]
        results.append(ValidationResult(
            symbol=symbol,
            passed=sv.passed,
            failure_reason=sv.failure_reason,
            quote=summary.valid_quotes.get(symbol),
        ))

    return results
