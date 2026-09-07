"""Market Structure Universe registry (NS-4A v2; PRD-337 precursor).

Additive, human-authored seed registry of the instruments Cuttingboard
observes. This registry is NOT the universal source of truth: it is read by
exactly one production consumer, ``watchlist_sidecar``. It consolidates no
existing universe definition, drives no decision surface, and carries no
persisted schema. Boring, deterministic, hand-authored data.

This v2 registry evolves the legacy 12-symbol mixed-purpose model into a
bounded 22-symbol MARKET-STRUCTURE MEASUREMENT universe while preserving hard
isolation from every decision-authoritative path. Membership and relationships
are owner-authored; no symbol is inferred.

Two explicit booleans carry the product question -- there is no role ontology:

- ``personal``: owner attention. This precursor has NO runtime consumer; the
  personal projection is pinned by a literal test only and is neither serialized
  nor fetched nor rendered.
- ``market_structure``: measurement membership. This is the ONLY flag any
  producer reads; the 22 measurement symbols are the observation universe.

Decision authority is NEVER inferred from ``personal``, ``market_structure`` or
``trade_eligible``. The tradable universe is ``config.ALL_SYMBOLS`` and the
decision lists derived from it; this registry cannot widen them (see
``watchlist_sidecar`` and ``runtime._OBSERVE_ONLY_FETCH``).

``trade_eligible`` is a PRD-308 registry-level flag with NO consumer. It is NOT
synchronized with ``config.ALL_SYMBOLS`` / ``config.HIGH_BETA`` and must NEVER be
read as the tradable universe (e.g. AAPL/MSFT carry ``trade_eligible=False`` here
while ``config.HIGH_BETA`` lists AAPL as a live trade candidate -- the fields are
independent by design). A test asserts no ``cuttingboard`` module reads
``.trade_eligible``. Retiring the field is an optional owner cut, not this slice.

MEGACAPS is a SIZE-descriptive basket label: the six largest non-TSLA US
mega-caps the owner selected. It claims nothing about leadership; the words
LEADER/LEADING are reserved for future NS-4C relative-performance semantics. The
basket is owner-authored, not a "top-N by weight" rule, so the absence of AVGO or
TSLA is not an error. Each MEGACAPS rationale names the actual GICS sector so
META/GOOG (Communication Services) and AMZN (Consumer Discretionary) are not
mislabeled "technology".

``benchmark_symbol`` records an owner-authored relationship for future NS-4C
relative-move measurement. It is INERT in this slice: no relative performance is
computed, and it is not serialized into the observation carrier. ``null`` marks
an anchor (SPY, GLD) or a non-measurement row.

F7 -- product question and self-weight caveat (why the six MEGACAPS benchmark to
``QQQ``). The intended question is: "how is this selected mega-cap / growth-complex
constituent behaving relative to the broader QQQ growth complex?" It is NOT
sector-relative breadth, NOT a claim that all six are Technology-sector names
(META/GOOG are Communication Services, AMZN is Consumer Discretionary), and NOT a
trading recommendation. Caveat: these six are themselves meaningful components of
``QQQ``, so a constituent's move versus ``QQQ`` is NOT an independent factor
comparison -- it partly compares each name with itself. The spread is still useful
for divergence / relative-behaviour context, but future NS-4C must not overstate
its statistical independence. (Canonical taxonomy note: docs/universe_taxonomy.md,
OBSERVE_ONLY benchmark map.)

No I/O, no wall-clock, no derived semantics.
"""

from __future__ import annotations

from dataclasses import dataclass

# Closed display-group vocabulary for MARKET_STRUCTURE rows. Non-measurement
# rows carry ``primary_group=None``.
PRIMARY_GROUPS: frozenset[str] = frozenset({"MARKET", "SECTORS", "METALS", "MEGACAPS"})

# Bounded, immutable function vocabulary. Deliberately minimal: only the one
# non-obvious functional truth the owner ruling flagged (UCO is a crude-oil
# proxy). Grows only when a real consumer requires it.
KNOWN_FUNCTIONS: frozenset[str] = frozenset({"crude_proxy"})


@dataclass(frozen=True)
class UniverseInstrument:
    """One owner-authored instrument. Immutable, human-authored. Every row
    states all nine values explicitly -- no field defaults."""

    symbol: str
    trade_eligible: bool          # PRD-308 inert flag; NO consumer (see module docstring)
    functions: tuple[str, ...]
    primary_group: str | None     # display group iff market_structure, else None
    enabled: bool                 # observation activation only
    rationale: str
    personal: bool                # owner attention; no consumer in this precursor
    market_structure: bool        # measurement membership; the only produced flag
    benchmark_symbol: str | None  # authored NS-4C relationship; null = anchor / none


# Registry order == serialization order and implies NO rank, priority, or
# conviction. The 22 market_structure rows come first in measurement order,
# followed by the non-measurement rows (personal-only UCO, disabled TSLA
# tombstone).
UNIVERSE_REGISTRY: tuple[UniverseInstrument, ...] = (
    # MARKET
    UniverseInstrument("SPY", True, (), "MARKET", True, "broad market reference", True, True, None),
    UniverseInstrument("QQQ", True, (), "MARKET", True, "growth/tech-heavy broad reference", True, True, "SPY"),
    # SECTORS (all 11 Select Sector SPDRs, benchmarked to SPY)
    UniverseInstrument("XLK", False, (), "SECTORS", True, "Information Technology sector", False, True, "SPY"),
    UniverseInstrument("XLF", False, (), "SECTORS", True, "Financials sector", False, True, "SPY"),
    UniverseInstrument("XLE", True, (), "SECTORS", True, "Energy sector", True, True, "SPY"),
    UniverseInstrument("XLI", False, (), "SECTORS", True, "Industrials sector", False, True, "SPY"),
    UniverseInstrument("XLY", False, (), "SECTORS", True, "Consumer Discretionary sector", False, True, "SPY"),
    UniverseInstrument("XLP", False, (), "SECTORS", True, "Consumer Staples sector", False, True, "SPY"),
    UniverseInstrument("XLV", False, (), "SECTORS", True, "Health Care sector", False, True, "SPY"),
    UniverseInstrument("XLU", False, (), "SECTORS", True, "Utilities sector", False, True, "SPY"),
    UniverseInstrument("XLB", False, (), "SECTORS", True, "Materials sector", False, True, "SPY"),
    UniverseInstrument("XLRE", False, (), "SECTORS", True, "Real Estate sector", False, True, "SPY"),
    UniverseInstrument("XLC", False, (), "SECTORS", True, "Communication Services sector", False, True, "SPY"),
    # METALS (gold complex; GLD anchor)
    UniverseInstrument("GLD", True, (), "METALS", True, "spot gold ETF", True, True, None),
    UniverseInstrument("SLV", True, (), "METALS", True, "spot silver ETF", True, True, "GLD"),
    UniverseInstrument("GDX", True, (), "METALS", True, "gold miners exposure", True, True, "GLD"),
    # MEGACAPS (owner-selected six largest non-TSLA US mega-caps; benchmarked to QQQ)
    UniverseInstrument("AAPL", False, (), "MEGACAPS", True, "Information Technology mega-cap", False, True, "QQQ"),
    UniverseInstrument("MSFT", False, (), "MEGACAPS", True, "Information Technology mega-cap", False, True, "QQQ"),
    UniverseInstrument("NVDA", True, (), "MEGACAPS", True, "Information Technology mega-cap", True, True, "QQQ"),
    UniverseInstrument("META", True, (), "MEGACAPS", True, "Communication Services mega-cap", True, True, "QQQ"),
    UniverseInstrument("AMZN", True, (), "MEGACAPS", True, "Consumer Discretionary mega-cap", True, True, "QQQ"),
    UniverseInstrument("GOOG", True, (), "MEGACAPS", True, "Communication Services mega-cap", True, True, "QQQ"),
    # Non-measurement rows (no primary_group; not in the measurement projection)
    UniverseInstrument("UCO", True, ("crude_proxy",), None, True, "crude-oil energy proxy (personal-only)", True, False, None),
    UniverseInstrument("TSLA", True, (), None, False, "disabled tombstone (was retail-flow signal)", False, False, None),
)
