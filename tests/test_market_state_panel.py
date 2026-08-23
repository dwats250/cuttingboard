"""PRD-312 MARKET STATE panel — unit tests (mutation matrix M1-M12, M17).

Tests the pure ``market_state_panel`` module directly against the resolved
carriers the renderer supplies. Placement (M13) and the arrow cut (M14-M16) are
exercised end-to-end in ``test_dashboard_renderer`` / ``test_trend_structure``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from cuttingboard.delivery import gex_card, market_state_panel, movement_card

_RUN = datetime(2026, 8, 22, 18, 30, tzinfo=timezone.utc)  # 14:30 ET (EDT)


def _gex(net_usd=-5e9, as_of="09:45"):
    return gex_card.GexCard(
        net_usd=net_usd, dominant=(101.0, 1.0), call_wall=None, put_wall=None,
        zero_dte_share=None, as_of_et=as_of,
    )


def _movement(groups, captured="10:00"):
    return movement_card.MovementCard(groups=groups, captured_et=captured)


def _render(**over):
    kw = dict(
        market_regime="EXPANSION",
        permission="No new trades permitted.",
        run_clock=_RUN,
        gex_card_obj=None,
        movement_card_obj=None,
        red_folder={"ok": True, "events": [], "expiring": False},
    )
    kw.update(over)
    return market_state_panel.render_fragment(**kw)


def _value(html: str, axis: str) -> str:
    # The value cell immediately following the axis label.
    return html.split(f'>{axis}</div><div class="value">', 1)[1].split("</div>", 1)[0]


# --- M1 / M2: ENVIRONMENT present / unavailable ---
def test_m1_environment_present():
    assert _value(_render(market_regime="EXPANSION"), "ENVIRONMENT").startswith("EXPANSION")
    assert "as of 14:30 ET" in _value(_render(), "ENVIRONMENT")


def test_m2_environment_unavailable():
    assert _value(_render(market_regime=None), "ENVIRONMENT") == "unavailable"


# --- M3 / M3b: PERMISSION present / unavailable ---
def test_m3_permission_present():
    assert _value(_render(), "PERMISSION").startswith("No new trades permitted.")


def test_m3b_permission_unavailable_isolated():
    html = _render(permission=None)
    assert _value(html, "PERMISSION") == "unavailable"
    # Other rows unaffected.
    assert _value(html, "ENVIRONMENT").startswith("EXPANSION")


# --- M4 / M4b / M5: POSITIONING present / qualifier preserved / unavailable ---
def test_m4_positioning_present():
    v = _value(_render(gex_card_obj=_gex()), "POSITIONING")
    assert "net -$5.0B" in v            # reuses gex net format
    assert "as of 09:45 ET" in v        # GEX fetched/as-of clock


def test_m4b_positioning_qualifiers_preserved():
    v = _value(_render(gex_card_obj=_gex()), "POSITIONING")
    assert "Cboe ~15m delayed" in v
    assert "configured positioning assumption" in v
    assert "positioning is not measured" in v


def test_m5_positioning_unavailable():
    assert _value(_render(gex_card_obj=None), "POSITIONING") == "unavailable"


# --- M6 / M6b / M7: PARTICIPATION present / partial / unavailable ---
def test_m6_participation_all_usable():
    card = _movement(groups=(("INDEX", ("SPY +1.0%", "QQQ 0.0%")),))
    v = _value(_render(movement_card_obj=card), "PARTICIPATION")
    assert v == "2/2 captured &middot; captured 10:00 ET"


def test_m6b_participation_partial_absence_no_full_claim():
    card = _movement(groups=(("INDEX", ("SPY +1.0%", "QQQ n/a")), ("TECH", ("NVDA n/a",))))
    v = _value(_render(movement_card_obj=card), "PARTICIPATION")
    assert "1/3 captured, 2 n/a" in v
    assert "3/3" not in v  # never a full-capture claim while any symbol is n/a


def test_m7_participation_unavailable():
    assert _value(_render(movement_card_obj=None), "PARTICIPATION") == "unavailable"


# --- M8 / M9: EVENT RISK present / none / unavailable ---
def test_m8_event_risk_with_events():
    rf = {"ok": True, "events": [{"name": "CPI"}, {"name": "FOMC"}], "expiring": False}
    assert _value(_render(red_folder=rf), "EVENT RISK").startswith("2 events in 48h")


def test_m8_event_risk_no_events():
    assert _value(_render(), "EVENT RISK").startswith("no events in 48h")


def test_m9_event_risk_unavailable():
    assert _value(_render(red_folder={"ok": False, "error": "x"}), "EVENT RISK") == "unavailable"
    assert _value(_render(red_folder=None), "EVENT RISK") == "unavailable"


# --- M10: structural exact-five, no aggregate/score/global-as-of ---
def test_m10_exactly_five_axes_no_aggregate():
    html = _render()
    assert html.count('class="label"') == 5
    assert html.count('class="value"') == 5
    for axis in ("ENVIRONMENT", "PERMISSION", "POSITIONING", "PARTICIPATION", "EVENT RISK"):
        assert f">{axis}</div>" in html
    # No score / verdict / confluence / global synchronized as-of.
    low = html.lower()
    for banned in ("score", "bullish", "bearish", "confluence", "verdict", "confidence"):
        assert banned not in low


# --- M12: no INTRADAY row ---
def test_m12_no_intraday_row():
    assert "INTRADAY" not in _render()
    assert "vwap" not in _render().lower()


# --- M17: persistent panel — all carriers absent still renders five honest rows ---
def test_m17_all_unavailable_still_renders_five_rows():
    html = market_state_panel.render_fragment(
        market_regime=None, permission=None, run_clock=None,
        gex_card_obj=None, movement_card_obj=None, red_folder=None,
    )
    assert 'id="market-state"' in html
    assert html.count("unavailable") == 5  # every axis honestly unavailable
    assert html.count('class="label"') == 5


# --- cross-check: POSITIONING net matches the GEX card's own net format ---
def test_positioning_net_matches_gex_card_format():
    assert market_state_panel._fmt_net(-5e9) == gex_card._fmt_net(-5e9)
    assert market_state_panel._fmt_net(3.2e9) == gex_card._fmt_net(3.2e9)
