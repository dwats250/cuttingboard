"""PRD-136 R10: universe/bounds invariants for the spot-metals macro drivers.

Asserts that GC=F (gold front-month) and SI=F (silver front-month) are wired
into the cuttingboard config exactly as macro-driver-style non-tradable
symbols, mirroring the CL=F precedent from PRD-122. The spot-metals
display labels XAU/XAG are deliberately NOT asserted here — those live in
the renderer per PRD-136 R7.

PRD-304: operator-availability lock resolution (R1) is asserted at the bottom.
"""

import logging

from cuttingboard import config


_SPOT_METAL_SYMBOLS = ("GC=F", "SI=F")


def test_spot_metals_in_macro_drivers() -> None:
    for sym in _SPOT_METAL_SYMBOLS:
        assert sym in config.MACRO_DRIVERS, f"{sym} missing from MACRO_DRIVERS"


def test_spot_metals_in_all_symbols() -> None:
    for sym in _SPOT_METAL_SYMBOLS:
        assert sym in config.ALL_SYMBOLS, f"{sym} missing from ALL_SYMBOLS"


def test_spot_metals_in_non_tradable_symbols() -> None:
    for sym in _SPOT_METAL_SYMBOLS:
        assert sym in config.NON_TRADABLE_SYMBOLS, (
            f"{sym} missing from NON_TRADABLE_SYMBOLS — must be fenced from "
            "qualification iteration via MACRO_DRIVERS membership"
        )


def test_spot_metals_absent_from_tradable_lists() -> None:
    for sym in _SPOT_METAL_SYMBOLS:
        assert sym not in config.COMMODITIES, f"{sym} must not be in COMMODITIES"
        assert sym not in config.INDICES, f"{sym} must not be in INDICES"
        assert sym not in config.HIGH_BETA, f"{sym} must not be in HIGH_BETA"


def test_spot_metals_have_price_bounds() -> None:
    for sym in _SPOT_METAL_SYMBOLS:
        assert sym in config.PRICE_BOUNDS, f"{sym} missing from PRICE_BOUNDS"
        low, high = config.PRICE_BOUNDS[sym]
        assert low > 0, f"{sym} PRICE_BOUNDS low must be > 0, got {low}"
        assert high > low, (
            f"{sym} PRICE_BOUNDS high must exceed low, got ({low}, {high})"
        )


def test_spot_metals_not_in_halt_symbols() -> None:
    for sym in _SPOT_METAL_SYMBOLS:
        assert sym not in config.HALT_SYMBOLS, (
            f"{sym} must NOT be in HALT_SYMBOLS — observational only"
        )


def test_spot_metals_not_in_required_symbols() -> None:
    for sym in _SPOT_METAL_SYMBOLS:
        assert sym not in config.REQUIRED_SYMBOLS, (
            f"{sym} must NOT be in REQUIRED_SYMBOLS — graceful degradation"
        )


def test_spot_metals_not_in_symbol_units() -> None:
    """Default 'usd_price' units apply for spot-metal futures."""
    for sym in _SPOT_METAL_SYMBOLS:
        assert sym not in config.SYMBOL_UNITS, (
            f"{sym} must not override SYMBOL_UNITS — default 'usd_price' applies"
        )


def test_spot_metals_source_priority_yfinance_only() -> None:
    """Match the CL=F precedent: yfinance-only fetch routing."""
    for sym in _SPOT_METAL_SYMBOLS:
        if sym in config.SYMBOL_SOURCE_PRIORITY:
            assert config.SYMBOL_SOURCE_PRIORITY[sym] == ["yfinance"], (
                f"{sym} SYMBOL_SOURCE_PRIORITY override must be ['yfinance'], "
                f"got {config.SYMBOL_SOURCE_PRIORITY[sym]!r}"
            )


# ---------------------------------------------------------------------------
# PRD-304 R1 — operator-availability input and fail-closed resolution
# ---------------------------------------------------------------------------

_AVAILABLE = config.OPERATOR_AVAILABLE
_LOCKED = config.OPERATOR_CANNOT_MONITOR


def test_operator_availability_explicit_available_opens() -> None:
    assert config.resolve_operator_availability("AVAILABLE") == _AVAILABLE


def test_operator_availability_explicit_locked() -> None:
    assert config.resolve_operator_availability("CANNOT_MONITOR") == _LOCKED


def test_operator_availability_trimmed_and_case_insensitive() -> None:
    # Trimmed, case-insensitive input; canonical uppercase resolved value.
    assert config.resolve_operator_availability("  available ") == _AVAILABLE
    assert config.resolve_operator_availability("Available") == _AVAILABLE
    assert config.resolve_operator_availability("\tcannot_monitor\n") == _LOCKED


def test_operator_availability_missing_fails_closed() -> None:
    assert config.resolve_operator_availability(None) == _LOCKED


def test_operator_availability_empty_fails_closed() -> None:
    assert config.resolve_operator_availability("") == _LOCKED


def test_operator_availability_whitespace_fails_closed() -> None:
    assert config.resolve_operator_availability("   ") == _LOCKED


def test_operator_availability_unrecognized_fails_closed() -> None:
    # Any value other than the two canonical states is fail-closed.
    assert config.resolve_operator_availability("YES") == _LOCKED
    assert config.resolve_operator_availability("true") == _LOCKED
    assert config.resolve_operator_availability("ENABLED") == _LOCKED


def test_operator_availability_env_read_when_unset_arg(monkeypatch) -> None:
    # With no raw arg, the resolver reads the environment exactly once.
    monkeypatch.setenv(config.OPERATOR_AVAILABILITY_ENV, "available")
    assert config.resolve_operator_availability() == _AVAILABLE
    monkeypatch.setenv(config.OPERATOR_AVAILABILITY_ENV, "CANNOT_MONITOR")
    assert config.resolve_operator_availability() == _LOCKED
    monkeypatch.delenv(config.OPERATOR_AVAILABILITY_ENV, raising=False)
    assert config.resolve_operator_availability() == _LOCKED


def test_operator_availability_invalid_value_not_disclosed(caplog) -> None:
    # Non-disclosure: the raw invalid value never appears in any log record; a
    # warning naming ONLY the variable is emitted.
    secret = "SUPERSECRETRAWVALUE"
    with caplog.at_level(logging.WARNING):
        assert config.resolve_operator_availability(secret) == _LOCKED
    joined = " ".join(rec.getMessage() for rec in caplog.records)
    assert secret not in joined, "raw invalid value must never be logged"
    assert config.OPERATOR_AVAILABILITY_ENV in joined, "warning must name the variable"


def test_operator_availability_valid_values_emit_no_warning(caplog) -> None:
    # Missing/empty/valid resolutions must not warn (only present-but-unrecognized does).
    with caplog.at_level(logging.WARNING):
        config.resolve_operator_availability("AVAILABLE")
        config.resolve_operator_availability("CANNOT_MONITOR")
        config.resolve_operator_availability(None)
        config.resolve_operator_availability("")
    assert not caplog.records, "valid/absent resolutions must not warn"


def test_is_operator_locked_helper() -> None:
    assert config.is_operator_locked(_LOCKED) is True
    assert config.is_operator_locked(_AVAILABLE) is False


def test_operator_lock_permission_string_canonical() -> None:
    # R5/R9: canonical locked permission carrier with the em dash.
    assert config.OPERATOR_LOCK_PERMISSION == "No new trades permitted — operator cannot monitor."
    assert config.OPERATOR_LOCK_TITLE == "OBSERVE ONLY — OPERATOR LOCK"
