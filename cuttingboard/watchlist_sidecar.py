"""Watchlist Snapshot Sidecar (PRD-114; NS-4A v2 measurement projection).

Observe-only producer of the MARKET STRUCTURE measurement universe. Consumer is
the dashboard renderer (via ``delivery.movement_card``) and the human reader, not
a decision module. Outputs do not feed qualification, regime, or any decision
surface.

Pure builder over the market-structure registry (``universe_registry``) plus the
existing ``NormalizedQuote.price`` / ``pct_change_decimal`` pass-through. No I/O,
no wall-clock reads, no derived semantics.

The projections below are DERIVED from ``universe_registry.UNIVERSE_REGISTRY``,
not hand-maintained here. Registry order is serialization-only and MUST NOT imply
rank, priority, conviction, trade preference, alert order, or execution
preference. ``validate_registry`` runs once at import (fail-loud) before any
projection is built.
"""

from __future__ import annotations

from datetime import datetime
from typing import Mapping, Optional

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.universe_registry import (
    KNOWN_FUNCTIONS,
    PRIMARY_GROUPS,
    UNIVERSE_REGISTRY,
    UniverseInstrument,
)

_MAX_BENCHMARK_HOPS = 3


def validate_registry(registry: tuple[UniverseInstrument, ...]) -> None:
    """Assert the ratified registry invariants; raise ``ValueError`` on any
    violation. Pure function of ``registry`` (no I/O). Called at import against
    the canonical registry so a bad edit fails loud before projections build.

    Rules (each has a red test):
    1. symbols unique, non-empty, uppercase.
    2. ``enabled`` implies (``personal`` or ``market_structure``).
    3. ``market_structure`` implies ``enabled`` and ``primary_group in
       PRIMARY_GROUPS``; not ``market_structure`` implies ``primary_group is
       None``.
    4. ``benchmark_symbol`` non-null implies the row is ``market_structure``, the
       target is a ``market_structure`` symbol, the target is not the row itself,
       and following benchmarks reaches a null anchor within 3 hops.
    5. ``functions`` is a subset of ``KNOWN_FUNCTIONS``; every ``enabled`` row has
       a non-empty ``rationale``.
    """
    by_symbol: dict[str, UniverseInstrument] = {}
    market_structure_symbols: set[str] = set()
    for inst in registry:
        # Rule 1
        if not inst.symbol or not isinstance(inst.symbol, str):
            raise ValueError(f"registry symbol must be a non-empty string: {inst.symbol!r}")
        if inst.symbol != inst.symbol.upper():
            raise ValueError(f"registry symbol must be uppercase: {inst.symbol!r}")
        if inst.symbol in by_symbol:
            raise ValueError(f"duplicate registry symbol: {inst.symbol!r}")
        by_symbol[inst.symbol] = inst
        if inst.market_structure:
            market_structure_symbols.add(inst.symbol)

    for inst in registry:
        # Rule 2
        if inst.enabled and not (inst.personal or inst.market_structure):
            raise ValueError(
                f"{inst.symbol}: enabled row must be personal or market_structure"
            )
        # Rule 3
        if inst.market_structure:
            if not inst.enabled:
                raise ValueError(f"{inst.symbol}: market_structure implies enabled")
            if inst.primary_group not in PRIMARY_GROUPS:
                raise ValueError(
                    f"{inst.symbol}: market_structure primary_group "
                    f"{inst.primary_group!r} not in {sorted(PRIMARY_GROUPS)}"
                )
        else:
            if inst.primary_group is not None:
                raise ValueError(
                    f"{inst.symbol}: non-measurement row must have primary_group=None, "
                    f"got {inst.primary_group!r}"
                )
        # Rule 4
        if inst.benchmark_symbol is not None:
            if not inst.market_structure:
                raise ValueError(
                    f"{inst.symbol}: benchmark_symbol requires market_structure"
                )
            if inst.benchmark_symbol == inst.symbol:
                raise ValueError(f"{inst.symbol}: benchmark self-reference")
            if inst.benchmark_symbol not in market_structure_symbols:
                raise ValueError(
                    f"{inst.symbol}: benchmark target {inst.benchmark_symbol!r} "
                    "is not a market_structure symbol"
                )
        # Rule 5
        if not set(inst.functions) <= KNOWN_FUNCTIONS:
            raise ValueError(
                f"{inst.symbol}: functions {inst.functions!r} not subset of "
                f"{sorted(KNOWN_FUNCTIONS)}"
            )
        if inst.enabled and not inst.rationale:
            raise ValueError(f"{inst.symbol}: enabled row requires non-empty rationale")

    # Rule 4 (closure): every benchmark chain reaches a null anchor within 3 hops.
    for inst in registry:
        current = inst.benchmark_symbol
        hops = 0
        while current is not None:
            hops += 1
            if hops > _MAX_BENCHMARK_HOPS:
                raise ValueError(
                    f"{inst.symbol}: benchmark chain exceeds {_MAX_BENCHMARK_HOPS} hops "
                    "(cycle or over-deep)"
                )
            current = by_symbol[current].benchmark_symbol


validate_registry(UNIVERSE_REGISTRY)


# --- Derived projections (registry order; inert relationships) --------------

# The 22 measurement symbols, registry order. market_structure implies enabled
# (validation rule 3), so this is the exact observation universe.
MARKET_STRUCTURE_SYMBOLS: tuple[str, ...] = tuple(
    i.symbol for i in UNIVERSE_REGISTRY if i.market_structure
)

# (symbol, primary_group, registry_index) rows; registry_index is the 0-based
# position within MARKET_STRUCTURE_SYMBOLS (serialization/order only; no rank).
MARKET_STRUCTURE_ROWS: tuple[tuple[str, str, int], ...] = tuple(
    (i.symbol, i.primary_group, idx)
    for idx, i in enumerate(i for i in UNIVERSE_REGISTRY if i.market_structure)
)

# Owner-attention set. NO runtime consumer in this precursor: not serialized, not
# fetched, not rendered. Pinned by literal test only.
PERSONAL_SYMBOLS: tuple[str, ...] = tuple(
    i.symbol for i in UNIVERSE_REGISTRY if i.enabled and i.personal
)

# Authored NS-4C relationship map over the 22 measurement symbols. INERT until
# NS-4C: no production module reads it in this slice.
BENCHMARK_BY_SYMBOL: Mapping[str, Optional[str]] = {
    i.symbol: i.benchmark_symbol for i in UNIVERSE_REGISTRY if i.market_structure
}


def build_watchlist_snapshot(
    normalized_quotes: Mapping[str, NormalizedQuote],
    generated_at: Optional[datetime],
) -> dict:
    """Build the schema_version-3 observation carrier: the 22 measurement rows in
    registry order, each with exactly five keys. A missing quote leaves both
    numeric fields ``None`` (the n/a hook); NEVER coerced to 0.0. Pure function of
    the inputs; unrequested quote symbols are ignored."""
    if generated_at is not None and generated_at.tzinfo is None:
        raise ValueError("generated_at must be timezone-aware or None")

    symbols: dict[str, dict] = {}
    for symbol, primary_group, registry_index in MARKET_STRUCTURE_ROWS:
        quote = normalized_quotes.get(symbol)
        current_price = quote.price if quote is not None else None
        daily_change_pct = (
            round(quote.pct_change_decimal * 100, 1) if quote is not None else None
        )
        symbols[symbol] = {
            "symbol": symbol,
            "primary_group": primary_group,
            "registry_index": registry_index,
            "current_price": current_price,
            "daily_change_pct": daily_change_pct,
        }

    return {
        "schema_version": 3,
        "source": "watchlist",
        "generated_at": generated_at.isoformat() if generated_at is not None else None,
        "symbols": symbols,
    }
