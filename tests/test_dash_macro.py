"""Tests for PRD-055 — dashboard renderer: Macro tape, macro bias, macro pressure, pressure labels."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

from tests.dash_helpers import (
    _macro_drivers,
    _macro_tape_block,
    _macro_tape_value_slots,
    _market_map,
    _mm_symbol,
    _payload,
    _run,
)


# ---------------------------------------------------------------------------
# R1 — Macro Tape
# ---------------------------------------------------------------------------

def test_macro_tape_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'id="macro-tape"' in html


def test_macro_tape_section_order() -> None:
    html = render_dashboard_html(_payload(), _run())
    system_pos = html.index('id="system-state"')
    macro_pos  = html.index('id="macro-tape"')
    assert system_pos < macro_pos


def test_macro_tape_empty_macro_drivers() -> None:
    # macro_drivers={} → slots render with em dash / N/A, no crash
    html = render_dashboard_html(_payload(), _run())
    tape = _macro_tape_block(html)
    for label in ("VIX", "DXY", "10Y", "BTC", "SPY", "QQQ", "GLD", "SLV", "XLE", "GDX"):
        assert label in tape


def test_macro_tape_arrows() -> None:
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=-0.01, tnx=0.0, btc=0.03))
    html = render_dashboard_html(p, _run())
    tape = _macro_tape_block(html)
    assert "VIX ↑" in tape
    assert "DXY ↓" in tape
    assert "10Y →" in tape
    assert "BTC ↑" in tape


def test_macro_tape_no_crash_when_market_map_none() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=None)
    assert 'id="macro-tape"' in html


def test_macro_tape_value_row_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    block = _macro_tape_block(html)
    assert 'class="macro-drivers-row"' in block
    assert 'class="macro-tradables-grid"' in block


def test_macro_tape_value_row_slot_order() -> None:
    # PRD-136: the new macro-spot-metals-row renders ABOVE the
    # macro-drivers-row (between MACRO BIAS and drivers), so in the
    # rendered HTML the XAU/XAG slots appear FIRST, then the driver row
    # (VIX..OIL), then the tradables tail (SPY..GDX).
    html = render_dashboard_html(_payload(), _run())
    slots = _macro_tape_value_slots(html)
    assert [symbol for symbol, _ in slots] == [
        "XAU", "XAG",
        "VIX", "DXY", "10Y", "BTC", "OIL",
        "SPY", "QQQ", "GLD", "SLV", "XLE", "GDX",
    ]


def test_macro_tape_value_row_has_thirteen_fixed_slots() -> None:
    # PRD-136: slot count grew from 11 → 13 (added XAU, XAG).
    html = render_dashboard_html(_payload(), _run())
    assert len(_macro_tape_value_slots(html)) == 13


def test_macro_tape_value_row_vix_format() -> None:
    p = _payload(macro_drivers=_macro_drivers())
    p["macro_drivers"]["volatility"]["level"] = 18.234
    html = render_dashboard_html(p, _run())
    assert dict(_macro_tape_value_slots(html))["VIX"] == "18.2"


def test_macro_tape_value_row_dxy_format() -> None:
    p = _payload(macro_drivers=_macro_drivers())
    p["macro_drivers"]["dollar"]["level"] = 99.87
    html = render_dashboard_html(p, _run())
    assert dict(_macro_tape_value_slots(html))["DXY"] == "99.9"


def test_macro_tape_value_row_10y_format() -> None:
    p = _payload(macro_drivers=_macro_drivers())
    p["macro_drivers"]["rates"]["level"] = 4.321
    html = render_dashboard_html(p, _run())
    assert dict(_macro_tape_value_slots(html))["10Y"] == "4.32"


def test_macro_tape_value_row_btc_compact_format() -> None:
    p = _payload(macro_drivers=_macro_drivers())
    p["macro_drivers"]["bitcoin"]["level"] = 94200
    html = render_dashboard_html(p, _run())
    assert dict(_macro_tape_value_slots(html))["BTC"] == "94.2K"


def test_macro_tape_value_row_btc_plain_format_below_threshold() -> None:
    p = _payload(macro_drivers=_macro_drivers())
    p["macro_drivers"]["bitcoin"]["level"] = 9800
    html = render_dashboard_html(p, _run())
    assert dict(_macro_tape_value_slots(html))["BTC"] == "9800"


def test_macro_tape_value_row_current_price_format() -> None:
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": 512.345}})
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    assert dict(_macro_tape_value_slots(html))["SPY"] == "512.35"


def test_macro_tape_value_row_etf_fallback_when_market_map_none() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=None)
    slots = dict(_macro_tape_value_slots(html))
    for symbol in ("SPY", "QQQ", "GLD", "SLV", "XLE", "GDX"):
        assert slots[symbol] == "N/A"


def test_macro_tape_value_row_missing_macro_driver_level_uses_fallback() -> None:
    p = _payload(macro_drivers=_macro_drivers())
    del p["macro_drivers"]["volatility"]["level"]
    html = render_dashboard_html(p, _run())
    assert dict(_macro_tape_value_slots(html))["VIX"] == "--"


def test_macro_tape_value_row_non_finite_macro_driver_level_uses_fallback() -> None:
    p = _payload(macro_drivers=_macro_drivers())
    p["macro_drivers"]["volatility"]["level"] = float("inf")
    html = render_dashboard_html(p, _run())
    assert dict(_macro_tape_value_slots(html))["VIX"] == "--"


def test_macro_tape_value_row_boolean_macro_driver_level_uses_fallback() -> None:
    p = _payload(macro_drivers=_macro_drivers())
    p["macro_drivers"]["volatility"]["level"] = True
    html = render_dashboard_html(p, _run())
    assert dict(_macro_tape_value_slots(html))["VIX"] == "--"


def test_macro_tape_value_row_boolean_current_price_uses_fallback() -> None:
    mm = _market_map({"SPY": {**_mm_symbol("SPY"), "current_price": False}})
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=mm)
    assert dict(_macro_tape_value_slots(html))["SPY"] == "N/A"


def test_macro_tape_tradable_no_arrow_with_na_value() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(), market_map=None)
    tape = _macro_tape_block(html)
    assert "SPY" in tape
    assert dict(_macro_tape_value_slots(html))["SPY"] == "N/A"
    assert "SPY ↑" not in tape
    assert "SPY ↓" not in tape
    assert "SPY →" not in tape


def test_macro_tape_macro_bias_text_unchanged_with_value_row() -> None:
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert "MACRO BIAS: LONG" in html


def test_macro_tape_macro_bias_class_unchanged_with_value_row() -> None:
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert 'class="macro-bias long"' in html


# ---------------------------------------------------------------------------
# R1.1 — Macro Bias Summary
# ---------------------------------------------------------------------------

def test_macro_bias_long() -> None:
    # 3 ↑, 1 ↓ → LONG
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=-0.01))
    html = render_dashboard_html(p, _run())
    assert "MACRO BIAS: LONG" in html


def test_macro_bias_short() -> None:
    # 1 ↑, 3 ↓ → SHORT
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.01))
    html = render_dashboard_html(p, _run())
    assert "MACRO BIAS: SHORT" in html


def test_macro_bias_mixed() -> None:
    # 2 ↑, 2 ↓ (market_map absent so slots 5-9 are all —)
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=-0.01, tnx=0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert "MACRO BIAS: MIXED" in html


def test_macro_bias_element_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'class="macro-bias' in html  # matches macro-bias long/short/mixed


# ---------------------------------------------------------------------------
# PRD-055 PATCH — macro no-data banner
# ---------------------------------------------------------------------------

def test_macro_no_data_banner_when_empty() -> None:
    # macro_drivers={} with no snapshot source → truly no data → banner shown
    html = render_dashboard_html(
        _payload(), _run(), macro_snapshot_path=Path("/nonexistent/no_snap.json")
    )
    tape = html.split('id="macro-tape"', 1)[1]
    assert "NO LIVE MACRO DATA" in tape


def test_macro_no_data_banner_absent_when_data_present() -> None:
    p = _payload(macro_drivers=_macro_drivers())
    html = render_dashboard_html(p, _run())
    assert "NO LIVE MACRO DATA" not in html


def test_macro_no_data_banner_absent_when_snapshot_has_data() -> None:
    # Production scenario: payload.macro_drivers={} but snapshot has real values.
    # Banner must NOT appear because resolved macro_drivers has data.
    snapshot = {"macro_drivers": _macro_drivers()}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(snapshot, f)
        snap_path = Path(f.name)
    try:
        html = render_dashboard_html(_payload(), _run(), macro_snapshot_path=snap_path)
        tape = html.split('id="macro-tape"', 1)[1]
        assert "NO LIVE MACRO DATA" not in tape
    finally:
        snap_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# PRD-055 PATCH — tape slot directional CSS classes
# ---------------------------------------------------------------------------

def test_tape_slot_up_class() -> None:
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.0, tnx=0.0, btc=0.0))
    html = render_dashboard_html(p, _run())
    assert 'tape-slot up' in html


def test_tape_slot_down_class() -> None:
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=0.0, tnx=0.0, btc=0.0))
    html = render_dashboard_html(p, _run())
    assert 'tape-slot down' in html


def test_tape_slot_flat_class() -> None:
    p = _payload(macro_drivers=_macro_drivers(vix=0.0, dxy=0.0, tnx=0.0, btc=0.0))
    html = render_dashboard_html(p, _run())
    assert 'tape-slot flat' in html


def test_tape_slot_na_class() -> None:
    # macro_drivers={} with no snapshot → driver slots get em dash → class "na"
    html = render_dashboard_html(
        _payload(), _run(), macro_snapshot_path=Path("/nonexistent/no_snap.json")
    )
    assert 'tape-slot na' in html


# ---------------------------------------------------------------------------
# PRD-055 PATCH — macro bias CSS class
# ---------------------------------------------------------------------------

def test_macro_bias_long_class() -> None:
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=0.03))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert 'class="macro-bias long"' in html


def test_macro_bias_short_class() -> None:
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert 'class="macro-bias short"' in html


def test_macro_bias_mixed_class() -> None:
    # 2 up, 2 down, no market_map
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=-0.01, tnx=0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert 'class="macro-bias mixed"' in html


# ---------------------------------------------------------------------------
# PRD-062 — Macro Pressure block
# ---------------------------------------------------------------------------

def _macro_pressure_block(html: str) -> str:
    parts = html.split('id="macro-pressure"', 1)
    assert len(parts) == 2, 'id="macro-pressure" not found'
    return parts[1].split('<div class="block"', 1)[0]


def test_macro_pressure_block_present() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    assert 'id="macro-pressure"' in html


def test_macro_pressure_block_no_data_when_empty_drivers() -> None:
    # Empty payload drivers + no snapshot → truly no data → "MACRO PRESSURE UNAVAILABLE"
    html = render_dashboard_html(
        _payload(), _run(), macro_snapshot_path=Path("/nonexistent/no_snap.json")
    )
    block = _macro_pressure_block(html)
    assert "MACRO PRESSURE UNAVAILABLE" in block
    assert "NO PRESSURE DATA" not in block


def test_macro_pressure_block_no_data_does_not_raise() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'id="macro-pressure"' in html


def test_macro_pressure_block_component_labels_present() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    block = _macro_pressure_block(html)
    for label in ("Volatility", "Dollar", "Rates", "Bitcoin"):
        assert label in block


def test_macro_pressure_block_overall_present() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    block = _macro_pressure_block(html)
    assert "Overall" in block


def test_macro_pressure_block_overall_uses_pressure_grid() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    block = _macro_pressure_block(html)
    assert 'class="pressure-overall"' not in block
    assert block.index("Overall") < block.index("</div>")


def test_macro_pressure_block_overall_value_is_valid() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    block = _macro_pressure_block(html)
    valid = {"RISK_ON", "RISK_OFF", "NEUTRAL", "MIXED", "UNKNOWN"}
    assert any(v in block for v in valid)


def test_macro_pressure_block_risk_on_drivers_produce_risk_on() -> None:
    # vix falling, dxy falling, rates falling, btc rising → all RISK_ON
    drivers = _macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.01, btc=0.05)
    drivers["rates"]["change_bps"] = -5.0
    html = render_dashboard_html(_payload(macro_drivers=drivers), _run())
    block = _macro_pressure_block(html)
    assert "RISK_ON" in block


def test_macro_pressure_block_risk_off_drivers_produce_risk_off() -> None:
    # vix rising, dxy rising, rates rising, btc falling → all RISK_OFF
    drivers = _macro_drivers(vix=0.05, dxy=0.01, tnx=0.05, btc=-0.05)
    drivers["rates"]["change_bps"] = 5.0
    html = render_dashboard_html(_payload(macro_drivers=drivers), _run())
    block = _macro_pressure_block(html)
    assert "RISK_OFF" in block


def test_macro_pressure_block_position_after_macro_tape() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    tape_pos = html.find('id="macro-tape"')
    pressure_pos = html.find('id="macro-pressure"')
    assert tape_pos < pressure_pos


def test_macro_pressure_block_position_after_system_state() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    system_pos = html.find('id="system-state"')
    pressure_pos = html.find('id="macro-pressure"')
    assert system_pos < pressure_pos


# ---------------------------------------------------------------------------
# PRD-073 — R3: Macro pressure driver labels
# ---------------------------------------------------------------------------

def test_macro_pressure_volatility_label() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    block = _macro_pressure_block(html)
    assert "Volatility" in block
    assert "volatility_pressure" not in block


def test_macro_pressure_dollar_label() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    block = _macro_pressure_block(html)
    assert "Dollar" in block
    assert "dollar_pressure" not in block


def test_macro_pressure_rates_label() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    block = _macro_pressure_block(html)
    assert "Rates" in block
    assert "rates_pressure" not in block


def test_macro_pressure_bitcoin_label() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    block = _macro_pressure_block(html)
    assert "Bitcoin" in block
    assert "bitcoin_pressure" not in block


def test_macro_pressure_overall_label_human_readable() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    block = _macro_pressure_block(html)
    assert "Overall" in block
    assert "OVERALL" not in block
