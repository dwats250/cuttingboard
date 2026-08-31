"""PRD-323 (A1-P): canonical primary-card symbol selection as a renderer-free
shared leaf.

This leaf owns the SAME selection the dashboard renderer applies inline when it
awards the single full-width setup-chart slot (the "chartable primary"). During
A1-P it is PARITY-LOCKED to that inline selection: it must pick the exact symbol
the renderer's chart slot would go to, proven by the cross-check fixtures in
``tests/test_primary_selection.py`` (which drive the renderer's real
``_render_candidate_card``). The renderer is NOT edited by A1-P and keeps its
inline selection; A1-C later rewires the renderer to this leaf and removes the
then-duplicate inline authority (Helm rulings 2026-08-30).

Import boundary (R1 FAIL): this module imports ONLY stdlib + ``setup_chart``. It
MUST NOT import ``cuttingboard.delivery.dashboard_renderer``. ``_TIER_DEFS`` and
``_GRADE_ORDER`` are temporarily DUPLICATED here from ``dashboard_renderer``;
A1-C removes that duplication when it rewires the renderer to this leaf.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from cuttingboard.delivery import setup_chart

# Duplicated verbatim from cuttingboard.delivery.dashboard_renderer (R1). A1-C
# removes the duplication when the renderer is rewired to this leaf.
_GRADE_ORDER: dict[str, int] = {"A+": 0, "A": 1, "B": 2, "C": 3, "D": 4, "F": 5}
_TIER_DEFS = [
    ("aplus", "A+ — ACTIONABLE", frozenset({"A+"})),
    ("a",     "A — HIGH QUALITY", frozenset({"A"})),
    ("b",     "B — DEVELOPING",   frozenset({"B"})),
    ("c",     "C — EARLY",        frozenset({"C"})),
]
# The chartable grades (those with a rendered tier). A symbol whose grade falls
# outside these tiers is never awarded the renderer's chart slot, so it can
# never be the canonical primary — mirroring the renderer's tier walk, which
# only iterates _TIER_DEFS (A+/A/B/C) and never the D/F grades.
_CHARTABLE_GRADES: frozenset[str] = frozenset().union(*(grades for _, _, grades in _TIER_DEFS))


def _valid_price(value: object) -> bool:
    """Duplicated from dashboard_renderer._render_candidate_card's local closure
    (PRD-226): a drawable NOW anchor must be a finite positive real. ``bool`` is
    excluded (``True``/``1.0`` is not a price); ``inf``/``NaN`` pass a naive
    check but crash the y-scale math, so they are rejected here."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def select_primary_card_symbol(
    market_map: Optional[dict],
    price_bars_by_symbol: Optional[dict[str, tuple[Any, str]]],
    integrator_skips: Optional[dict[str, str]],
) -> Optional[str]:
    """Return the canonical primary-card symbol, or ``None`` when no chartable
    primary exists.

    Mirrors the renderer's inline chart-slot award: walking symbols in
    ``(_GRADE_ORDER[grade], symbol)`` order, restricted to the ``_TIER_DEFS``
    grade tiers and excluding ``integrator_skips`` keys, the first symbol that
    (1) has a valid ``current_price`` (finite positive non-bool), (2) has
    ``fib_levels`` OR ``watch_zones``, (3) has bars supplied in
    ``price_bars_by_symbol``, and (4) yields a non-empty
    ``setup_chart.render_setup_chart_svg``. Pure leaf: no I/O, no fetch.

    ``price_bars_by_symbol`` mirrors the renderer's ``_price_bars`` map,
    ``{symbol: (bars, caption)}`` where ``bars`` is the age-admitted completed-bar
    row list (or ``None``). This leaf proves PREDICATE parity; RUNTIME
    input-source parity (feeding it the byte-identical inputs the renderer
    derives) is deferred to A1-C (R1).
    """
    symbols = (market_map or {}).get("symbols") or {}
    skips = integrator_skips or {}
    bars_map = price_bars_by_symbol or {}
    ordered = sorted(
        (
            sym
            for sym in symbols
            if sym not in skips
            and (symbols[sym] or {}).get("grade", "") in _CHARTABLE_GRADES
        ),
        key=lambda sym: (_GRADE_ORDER.get((symbols[sym] or {}).get("grade", ""), 6), sym),
    )
    for sym in ordered:
        entry = symbols[sym] or {}
        now_price = entry.get("current_price")
        if not _valid_price(now_price):
            continue
        if not (entry.get("fib_levels") or entry.get("watch_zones")):
            continue
        bars, _caption = bars_map.get(sym, (None, ""))
        if not bars:
            continue
        # Non-emptiness of the SVG depends only on `bars` + `now_price`
        # (setup_chart returns "" iff no usable rows or no valid anchor), so the
        # contract-band overlays the renderer also passes cannot change the
        # winner and are intentionally omitted from this leaf's inputs.
        chart_svg = setup_chart.render_setup_chart_svg(
            bars,
            now_price,
            watch_zones=entry.get("watch_zones"),
            fib_levels=entry.get("fib_levels"),
        )
        if chart_svg:
            return sym
    return None
