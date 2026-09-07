"""Tests for the MARKET MOVEMENT card (NS-4A v2; cuttingboard/delivery/movement_card.py).

Strict full-22 measurement acceptance: exact projection, key-set identity,
per-row type checks, four-group order, honest zero vs n/a, whole-card suppression
on any deviation, and the &nbsp;-inside / plain-space-between chip contract (F5).
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone

from cuttingboard.delivery import movement_card
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.watchlist_sidecar import MARKET_STRUCTURE_SYMBOLS, build_watchlist_snapshot

_GROUP_ORDER = ("MARKET", "SECTORS", "METALS", "MEGACAPS")


def _quote(symbol: str, pct: float) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol, price=100.0, pct_change_decimal=pct, volume=None,
        fetched_at_utc=datetime(2026, 8, 22, 14, 30, tzinfo=timezone.utc),
        source="test", units="usd_price", age_seconds=0.0,
    )


def _generated_at() -> datetime:
    return datetime(2026, 8, 22, 14, 30, tzinfo=timezone.utc)


def _valid_snapshot(overrides=None) -> dict:
    quotes = {sym: _quote(sym, 0.0123) for sym in MARKET_STRUCTURE_SYMBOLS}
    if overrides:
        quotes.update(overrides)
    return build_watchlist_snapshot(quotes, _generated_at())


def test_valid_artifact_renders_all_22_in_four_groups_in_order():  # M2/M3
    frag = movement_card.render_fragment(_valid_snapshot())
    assert frag
    for sym in MARKET_STRUCTURE_SYMBOLS:
        assert sym in frag
    order = [frag.index(g) for g in _GROUP_ORDER]
    assert order == sorted(order)
    # within-group registry order
    assert frag.index("SPY") < frag.index("QQQ")
    assert frag.index("XLK") < frag.index("XLC")
    assert frag.index("GLD") < frag.index("SLV") < frag.index("GDX")
    assert frag.index("AAPL") < frag.index("MSFT")
    assert "captured 10:30 ET" in frag


def test_no_uco_or_tsla_in_valid_render():  # M7/M8
    frag = movement_card.render_fragment(_valid_snapshot())
    assert "UCO" not in frag
    assert "TSLA" not in frag


def test_all_eleven_sectors_present():  # M3
    frag = movement_card.render_fragment(_valid_snapshot())
    for sector in ("XLK", "XLF", "XLE", "XLI", "XLY", "XLP", "XLV", "XLU", "XLB", "XLRE", "XLC"):
        assert sector in frag, sector


def test_scale_is_percent_one_decimal():
    frag = movement_card.render_fragment(_valid_snapshot({"SPY": _quote("SPY", 0.052)}))
    assert "SPY&nbsp;+5.2%" in frag


def test_honest_zero_distinct_from_na():  # M5
    quotes = {sym: _quote(sym, 0.011) for sym in MARKET_STRUCTURE_SYMBOLS if sym != "GOOG"}
    quotes["SPY"] = _quote("SPY", 0.0)
    frag = movement_card.render_fragment(build_watchlist_snapshot(quotes, _generated_at()))
    assert "SPY&nbsp;0.0%" in frag
    assert "GOOG&nbsp;n/a" in frag
    assert "GOOG&nbsp;0.0%" not in frag  # a null is NEVER fabricated as zero


def test_all_null_accepted_with_22_na():
    snap = build_watchlist_snapshot({}, _generated_at())  # full population, all n/a
    frag = movement_card.render_fragment(snap)
    assert frag
    assert frag.count("&nbsp;n/a") == 22


def test_absent_artifact_suppresses():
    assert movement_card.render_fragment(None) == ""


def test_schema_version_2_rejected():  # M12
    base = _valid_snapshot()
    base["schema_version"] = 2
    assert movement_card.render_fragment(base) == ""


def test_invalid_classes_suppress_whole_card():  # M4
    base = _valid_snapshot()

    def sup(mutate):
        s = copy.deepcopy(base)
        mutate(s)
        assert movement_card.render_fragment(s) == ""

    sup(lambda s: s.__setitem__("schema_version", 1))                   # wrong version
    sup(lambda s: s.__setitem__("source", "not_watchlist"))            # wrong source
    sup(lambda s: s["symbols"].pop("GOOG"))                            # missing (21/22)
    sup(lambda s: s["symbols"].__setitem__("ZZZ", s["symbols"]["SPY"]))  # extra unknown
    sup(lambda s: s["symbols"].__setitem__("UCO", dict(s["symbols"]["SPY"], symbol="UCO")))  # injected UCO
    sup(lambda s: s["symbols"].__setitem__("TSLA", dict(s["symbols"]["SPY"], symbol="TSLA")))  # injected TSLA
    sup(lambda s: s["symbols"]["SPY"].__setitem__("registry_index", 99))   # wrong index
    sup(lambda s: s["symbols"]["SPY"].__setitem__("registry_index", s["symbols"]["QQQ"]["registry_index"]))  # dup index
    sup(lambda s: s["symbols"]["SPY"].__setitem__("primary_group", "SECTORS"))  # wrong group
    sup(lambda s: s["symbols"]["SPY"].pop("daily_change_pct"))         # missing pct key
    sup(lambda s: s["symbols"]["SPY"].pop("current_price"))            # missing price key
    sup(lambda s: s["symbols"]["SPY"].__setitem__("daily_change_pct", "x"))     # str
    sup(lambda s: s["symbols"]["SPY"].__setitem__("daily_change_pct", 1))       # int, not float
    sup(lambda s: s["symbols"]["SPY"].__setitem__("daily_change_pct", True))    # bool
    sup(lambda s: s["symbols"]["SPY"].__setitem__("daily_change_pct", float("nan")))  # NaN
    sup(lambda s: s["symbols"]["SPY"].__setitem__("daily_change_pct", float("inf")))  # Inf
    sup(lambda s: s["symbols"]["SPY"].__setitem__("current_price", "x"))        # bad price type
    sup(lambda s: s.__setitem__("symbols", "not a dict"))             # symbols wrong type


def test_explicit_null_pct_accepted():
    base = _valid_snapshot()
    base["symbols"]["SPY"]["daily_change_pct"] = None  # explicit null is valid
    frag = movement_card.render_fragment(base)
    assert frag
    assert "SPY&nbsp;n/a" in frag


def test_malformed_or_naive_generated_at_suppresses():
    base = _valid_snapshot()
    for bad_ts in ("2026-08-22T14:30:00", "not-a-date", None, 12345):
        s = copy.deepcopy(base)
        s["generated_at"] = bad_ts
        assert movement_card.render_fragment(s) == ""


def test_card_holds_no_clock():
    with open(movement_card.__file__, "r", encoding="utf-8") as fh:
        text = fh.read()
    assert "datetime.now(" not in text


# --- F5: chip rendering (nbsp inside, plain space between) -------------------
def test_model_chips_carry_plain_space():
    """The MovementCard model keeps plain-space chips so market_state_panel's
    endswith(' n/a') contract is untouched; nbsp is HTML-render-only."""
    card = movement_card.build_movement_card(_valid_snapshot({"SPY": _quote("SPY", 0.0)}))
    all_chips = [c for _g, chips in card.groups for c in chips]
    assert "SPY 0.0%" in all_chips              # plain space, not &nbsp;, in the model
    assert all("&nbsp;" not in c for c in all_chips)


def test_html_chip_has_nbsp_inside_and_plain_space_between():
    frag = movement_card.render_fragment(_valid_snapshot())
    assert "SPY&nbsp;+1.2%" in frag          # nbsp inside a chip
    assert "SPY +1.2%" not in frag           # no intra-chip breakable space
    assert "+1.2% QQQ&nbsp;" in frag         # plain space BETWEEN chips


def test_survives_sort_keys_roundtrip_order():
    disk = json.dumps(_valid_snapshot(), sort_keys=True)
    reloaded = json.loads(disk)
    frag = movement_card.render_fragment(reloaded)
    assert frag.index("SPY") < frag.index("QQQ")
    assert frag.index("GLD") < frag.index("SLV") < frag.index("GDX")


def test_load_rejects_malformed_and_nondict_json(tmp_path):
    p = tmp_path / "watchlist_snapshot.json"
    p.write_text("{not valid json", encoding="utf-8")
    assert movement_card.load_watchlist_snapshot(p) is None
    p.write_text("[1, 2, 3]", encoding="utf-8")
    assert movement_card.load_watchlist_snapshot(p) is None
    assert movement_card.load_watchlist_snapshot(tmp_path / "missing.json") is None
