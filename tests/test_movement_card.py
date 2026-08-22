"""Tests for PRD-311 MARKET MOVEMENT card (cuttingboard/delivery/movement_card.py).

Carries packet 2789dda mutations at the card layer: M1 scale, M3 honest-zero vs
n/a, M4 group, M5 registry_index, M6 full-12 identity, M7 order-vs-sort_keys,
M8/M9 suppression, M10 captured clock, M11 malformed generated_at, M12 unknown
primary_group. Each suppression/identity mutation flips a well-formed artifact and
asserts the whole card suppresses baseline-neutral.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone

from cuttingboard.delivery import movement_card
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.watchlist_sidecar import WATCHLIST_SYMBOLS, build_watchlist_snapshot


def _quote(symbol: str, pct: float) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol, price=100.0, pct_change_decimal=pct, volume=None,
        fetched_at_utc=datetime(2026, 8, 22, 14, 30, tzinfo=timezone.utc),
        source="test", units="usd_price", age_seconds=0.0,
    )


def _generated_at() -> datetime:
    return datetime(2026, 8, 22, 14, 30, tzinfo=timezone.utc)


def _valid_snapshot(overrides=None) -> dict:
    """A real, fully-populated schema_version-2 artifact via the producer."""
    quotes = {sym: _quote(sym, 0.0123) for sym, *_ in WATCHLIST_SYMBOLS}
    if overrides:
        quotes.update(overrides)
    return build_watchlist_snapshot(quotes, _generated_at())


def test_valid_artifact_renders_all_12_grouped_in_order():  # M6/M7
    frag = movement_card.render_fragment(_valid_snapshot())
    assert frag
    for sym, *_ in WATCHLIST_SYMBOLS:
        assert sym in frag
    # groups appear in the fixed order, TSLA under HIGH_BETA (not interleaved TECH)
    order = [frag.index(g) for g in ("INDEX", "METALS", "ENERGY", "TECH", "HIGH_BETA")]
    assert order == sorted(order)
    # within-group registry order: SPY before QQQ
    assert frag.index("SPY") < frag.index("QQQ")
    assert "captured 10:30 ET" in frag


def test_scale_is_percent_one_decimal():  # M1
    frag = movement_card.render_fragment(_valid_snapshot({"SPY": _quote("SPY", 0.052)}))
    assert "SPY +5.2%" in frag  # decimal 0.052 -> +5.2%, not +0.1%


def test_honest_zero_distinct_from_na():  # M3
    # SPY zero -> "0.0%"; GOOG missing -> null -> "n/a"
    quotes = {sym: _quote(sym, 0.011) for sym, *_ in WATCHLIST_SYMBOLS if sym != "GOOG"}
    quotes["SPY"] = _quote("SPY", 0.0)
    frag = movement_card.render_fragment(build_watchlist_snapshot(quotes, _generated_at()))
    assert "SPY 0.0%" in frag
    assert "GOOG n/a" in frag
    assert "GOOG 0.0%" not in frag  # a null is NEVER fabricated as zero


def test_absent_artifact_suppresses():  # M8
    assert movement_card.render_fragment(None) == ""


def test_invalid_classes_suppress_whole_card():  # M9
    base = _valid_snapshot()
    def sup(mutate):
        s = copy.deepcopy(base)
        mutate(s)
        assert movement_card.render_fragment(s) == ""
    sup(lambda s: s.__setitem__("schema_version", 1))                 # wrong version
    sup(lambda s: s.__setitem__("source", "not_watchlist"))          # wrong source
    sup(lambda s: s["symbols"].pop("GOOG"))                          # missing symbol
    sup(lambda s: s["symbols"].__setitem__("ZZZ", s["symbols"]["SPY"]))  # extra symbol
    sup(lambda s: s["symbols"]["SPY"].__setitem__("registry_index", 99))  # wrong index
    sup(lambda s: s["symbols"]["SPY"].__setitem__("daily_change_pct", "x"))  # non-numeric
    sup(lambda s: s["symbols"]["SPY"].__setitem__("daily_change_pct", float("nan")))  # non-finite
    sup(lambda s: s["symbols"]["SPY"].__setitem__("daily_change_pct", 1))    # int, not float (R4)
    sup(lambda s: s["symbols"]["SPY"].__setitem__("daily_change_pct", True))  # bool, not float (R4)
    sup(lambda s: s["symbols"]["SPY"].__setitem__("registry_index", s["symbols"]["QQQ"]["registry_index"]))  # duplicate index
    sup(lambda s: s.__setitem__("symbols", "not a dict"))            # symbols wrong type


def test_group_passthrough_uses_fine_primary_group():  # M4/M12
    base = _valid_snapshot()
    # a row whose primary_group is outside the 5 known groups -> unusable
    bad = copy.deepcopy(base)
    bad["symbols"]["SPY"]["primary_group"] = "COARSE_THEME"
    assert movement_card.render_fragment(bad) == ""


def test_malformed_or_naive_generated_at_suppresses():  # M11
    base = _valid_snapshot()
    for bad_ts in ("2026-08-22T14:30:00", "not-a-date", None, 12345):
        s = copy.deepcopy(base)
        s["generated_at"] = bad_ts
        assert movement_card.render_fragment(s) == ""


def test_card_holds_no_clock():  # G1 / R5
    src = (movement_card.__file__)
    with open(src, "r", encoding="utf-8") as fh:
        text = fh.read()
    assert "datetime.now(" not in text


def test_registry_index_and_group_identity_enforced():  # M5
    base = _valid_snapshot()
    bad = copy.deepcopy(base)
    bad["symbols"]["SPY"]["primary_group"] = "METALS"  # mismatched vs expected INDEX
    assert movement_card.render_fragment(bad) == ""


def test_survives_sort_keys_roundtrip_order():  # M7 (order recovered despite sort_keys)
    # serialize sort_keys=True (alphabetical on disk), reload, assert registry order
    disk = json.dumps(_valid_snapshot(), sort_keys=True)
    reloaded = json.loads(disk)
    frag = movement_card.render_fragment(reloaded)
    assert frag.index("SPY") < frag.index("QQQ")  # registry order, not alphabetical
    assert frag.index("GDX") < frag.index("GLD") < frag.index("SLV")


def test_load_rejects_malformed_and_nondict_json(tmp_path):  # M9 loader
    p = tmp_path / "watchlist_snapshot.json"
    p.write_text("{not valid json", encoding="utf-8")
    assert movement_card.load_watchlist_snapshot(p) is None  # malformed JSON
    p.write_text("[1, 2, 3]", encoding="utf-8")
    assert movement_card.load_watchlist_snapshot(p) is None  # valid JSON, not a dict
    assert movement_card.load_watchlist_snapshot(tmp_path / "missing.json") is None  # absent
