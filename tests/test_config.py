"""PRD-136 R10: universe/bounds invariants for the spot-metals macro drivers.

Asserts that GC=F (gold front-month) and SI=F (silver front-month) are wired
into the cuttingboard config exactly as macro-driver-style non-tradable
symbols, mirroring the CL=F precedent from PRD-122. The spot-metals
display labels XAU/XAG are deliberately NOT asserted here — those live in
the renderer per PRD-136 R7.
"""

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
