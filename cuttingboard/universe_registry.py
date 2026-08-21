"""NS-4A universe seed registry (PRD-308).

Additive, human-authored seed registry of the instruments Cuttingboard
observes. This v1 registry is NOT the universal source of truth: it is read by
exactly one existing observe-only consumer, ``watchlist_sidecar``. It
consolidates no existing universe definition, drives no decision surface, and
carries no persisted schema. Boring, deterministic, hand-authored data.

Contents and membership are owner-ratified (Dustin, 2026-08-21 NS-4A
design-direction ruling); no symbol is inferred. ``primary_group`` is a v1
DISPLAY grouping, not the final ontology for every future consumer.

``trade_eligible`` (a bool) is kept independent from ``functions`` (a bounded,
immutable tuple) so an instrument can be a trade candidate and separately carry
observational role(s). The v1 ``functions`` vocabulary is intentionally minimal
-- only ``crude_proxy``, and only where it is true (UCO is a crude-oil proxy,
not crude futures; XLE stays a distinct ENERGY instrument and is not collapsed
into the same role).

No I/O, no wall-clock, no derived semantics.
"""

from __future__ import annotations

from dataclasses import dataclass

# v1 primary DISPLAY groups (owner-approved). Not a final ontology.
PRIMARY_GROUPS: frozenset[str] = frozenset(
    {"INDEX", "METALS", "ENERGY", "TECH", "HIGH_BETA"}
)

# Bounded, immutable v1 function vocabulary. Deliberately minimal: only the one
# non-obvious functional truth the owner ruling flagged. Grows only when a real
# consumer requires it.
KNOWN_FUNCTIONS: frozenset[str] = frozenset({"crude_proxy"})


@dataclass(frozen=True)
class UniverseInstrument:
    """One owner-ratified instrument. Immutable, human-authored."""

    symbol: str
    trade_eligible: bool
    functions: tuple[str, ...]
    primary_group: str
    enabled: bool
    rationale: str


# Owner-ratified 12-instrument population (Dustin, 2026-08-21). Insertion order
# is serialization-only and implies no rank, priority, or conviction.
UNIVERSE_REGISTRY: tuple[UniverseInstrument, ...] = (
    UniverseInstrument("SPY", True, (), "INDEX", True, "broad market reference"),
    UniverseInstrument("QQQ", True, (), "INDEX", True, "tech-heavy reference"),
    UniverseInstrument("GDX", True, (), "METALS", True, "gold miners exposure"),
    UniverseInstrument("GLD", True, (), "METALS", True, "spot gold ETF"),
    UniverseInstrument("SLV", True, (), "METALS", True, "spot silver ETF"),
    UniverseInstrument("XLE", True, (), "ENERGY", True, "energy sector"),
    UniverseInstrument("UCO", True, ("crude_proxy",), "ENERGY", True, "crude-oil energy proxy"),
    UniverseInstrument("NVDA", True, (), "TECH", True, "AI/semis bellwether"),
    UniverseInstrument("TSLA", True, (), "HIGH_BETA", True, "retail-flow signal"),
    UniverseInstrument("META", True, (), "TECH", True, "large-cap tech"),
    UniverseInstrument("AMZN", True, (), "TECH", True, "large-cap tech"),
    UniverseInstrument("GOOG", True, (), "TECH", True, "large-cap tech"),
)
