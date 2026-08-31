"""PRD-323 (A1-P) R1: the canonical-primary shared leaf.

Two guards:

* Import boundary (R1 FAIL clause 1): the leaf must not import
  ``dashboard_renderer`` (AST check — turns red the moment the import is added).
* Predicate parity (R1 FAIL clause 2): ``select_primary_card_symbol`` picks the
  EXACT symbol the renderer's inline chart slot would go to. The renderer's
  winner is computed by driving its REAL ``_render_candidate_card`` over the same
  fixture (a no-op HTML writer), so a drift in the renderer turns this red until
  A1-C reconciles them. RUNTIME input-source parity is deferred to A1-C; these
  fixtures prove PREDICATE parity only.
"""

from __future__ import annotations

import ast
from pathlib import Path

import cuttingboard.delivery.primary_selection as primary_selection
from cuttingboard.delivery import dashboard_renderer as dr
from cuttingboard.delivery.primary_selection import select_primary_card_symbol


# --- fixtures ---------------------------------------------------------------

def _bars(anchor: float = 100.0):
    """Three complete OHLC rows (label, o, h, l, c, v) — comfortably above
    setup_chart's minimum for ``render_setup_chart_svg`` to return a non-empty
    SVG (a single row can fall below its range/threshold guards)."""
    return [
        ["2026-08-26", anchor, anchor + 1.0, anchor - 1.0, anchor + 0.5, 1000],
        ["2026-08-27", anchor + 0.5, anchor + 1.5, anchor - 0.5, anchor + 1.0, 1100],
        ["2026-08-28", anchor + 1.0, anchor + 2.0, anchor, anchor + 1.5, 1200],
    ]


def _entry(symbol: str, grade: str, price=100.0, *, fib=True, watch=False):
    entry = {
        "symbol": symbol,
        "grade": grade,
        "current_price": price,
        "bias": "LONG",
        "structure": "UPTREND",
    }
    if fib:
        entry["fib_levels"] = {"retracements": {"0.5": 98.0}}
    if watch:
        entry["watch_zones"] = [{"type": "SUPPORT", "level": 97.0}]
    return entry


def _renderer_winner(market_map, price_bars_by_symbol, integrator_skips):
    """The renderer's inline chart-slot winner, computed by walking its REAL
    ``_TIER_DEFS`` / ``_GRADE_ORDER`` and calling its REAL
    ``_render_candidate_card`` (no-op writer) exactly as the dashboard does."""
    symbols = (market_map or {}).get("symbols") or {}
    skips = integrator_skips or {}
    bars_map = price_bars_by_symbol or {}
    sorted_syms = sorted(
        [s for s in symbols if s not in skips],
        key=lambda sym: (dr._GRADE_ORDER.get(symbols[sym].get("grade", ""), 6), sym),
    )
    _noop = lambda *args, **kwargs: None  # noqa: E731 - discard the rendered HTML
    for _tier_id, _tier_label, tier_grades in dr._TIER_DEFS:
        for sym in [s for s in sorted_syms if symbols[s].get("grade", "") in tier_grades]:
            bars, caption = bars_map.get(sym, (None, ""))
            took = dr._render_candidate_card(
                _noop,
                sym,
                symbols[sym],
                contract_entry=None,
                contract_stop=None,
                operator_locked=False,
                decision_permitted=True,
                bars=bars,
                bars_caption=caption,
                chart_slot_available=True,
            )
            if took:
                return sym
    return None


# Each case: id, market_map symbols, price_bars map, integrator_skips, expected.
_CASES = {
    "grade_order_aplus_wins": (
        {"XX": _entry("XX", "B"), "YY": _entry("YY", "A"), "ZZ": _entry("ZZ", "A+")},
        {s: (_bars(), "") for s in ("XX", "YY", "ZZ")},
        {},
        "ZZ",
    ),
    "alpha_within_grade": (
        {"BBB": _entry("BBB", "A"), "AAA": _entry("AAA", "A")},
        {"AAA": (_bars(), ""), "BBB": (_bars(), "")},
        {},
        "AAA",
    ),
    "integrator_skip_drops_winner": (
        {"ZZ": _entry("ZZ", "A+"), "YY": _entry("YY", "A")},
        {"ZZ": (_bars(), ""), "YY": (_bars(), "")},
        {"ZZ": "skip reason"},
        "YY",
    ),
    "invalid_price_skipped": (
        {"ZZ": _entry("ZZ", "A+", price=float("nan")), "YY": _entry("YY", "A")},
        {"ZZ": (_bars(), ""), "YY": (_bars(), "")},
        {},
        "YY",
    ),
    "bool_price_skipped": (
        {"ZZ": _entry("ZZ", "A+", price=True), "YY": _entry("YY", "A")},
        {"ZZ": (_bars(), ""), "YY": (_bars(), "")},
        {},
        "YY",
    ),
    "no_level_context_skipped": (
        {"ZZ": _entry("ZZ", "A+", fib=False, watch=False), "YY": _entry("YY", "A")},
        {"ZZ": (_bars(), ""), "YY": (_bars(), "")},
        {},
        "YY",
    ),
    "no_bars_skipped": (
        {"ZZ": _entry("ZZ", "A+"), "YY": _entry("YY", "A")},
        {"YY": (_bars(), "")},
        {},
        "YY",
    ),
    "unrenderable_bars_skipped": (
        {"ZZ": _entry("ZZ", "A+"), "YY": _entry("YY", "A")},
        {"ZZ": ([["2026-08-28", None, None, None, None, 0]], ""), "YY": (_bars(), "")},
        {},
        "YY",
    ),
    "watch_zones_only_context": (
        {"ZZ": _entry("ZZ", "A+", fib=False, watch=True)},
        {"ZZ": (_bars(), "")},
        {},
        "ZZ",
    ),
    "low_grade_never_wins": (
        {"DD": _entry("DD", "D"), "FF": _entry("FF", "F")},
        {"DD": (_bars(), ""), "FF": (_bars(), "")},
        {},
        None,
    ),
    "no_symbols_none": ({}, {}, {}, None),
}


import pytest  # noqa: E402 - after the fixture defs above, before the parametrized test


@pytest.mark.parametrize("case_id", list(_CASES))
def test_leaf_matches_renderer_chart_slot_winner(case_id):
    symbols, price_bars, skips, expected = _CASES[case_id]
    market_map = {"symbols": symbols}
    leaf = select_primary_card_symbol(market_map, price_bars, skips)
    renderer = _renderer_winner(market_map, price_bars, skips)
    # The leaf equals the renderer's actual inline winner (R1 parity lock)...
    assert leaf == renderer, f"{case_id}: leaf={leaf!r} renderer={renderer!r}"
    # ...and both equal the expected winner (belt-and-suspenders on the fixture).
    assert leaf == expected, f"{case_id}: leaf={leaf!r} expected={expected!r}"


def test_leaf_handles_none_inputs():
    assert select_primary_card_symbol(None, None, None) is None


def test_leaf_does_not_import_dashboard_renderer():
    """R1 FAIL clause 1: the leaf must import only stdlib + setup_chart, never
    dashboard_renderer. AST check so a substring in a comment/docstring does not
    false-positive and an added import turns this red."""
    source = Path(primary_selection.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any("dashboard_renderer" in name for name in imported), imported
