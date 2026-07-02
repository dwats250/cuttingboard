"""Tests for PRD-055 — dashboard renderer: Macro tape, macro bias, macro pressure, pressure labels."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cuttingboard.delivery import dashboard_renderer as _dr
from cuttingboard.delivery.dashboard_integrator import RULE3_MIXED_VERDICT
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


# PRD-160: freeze the renderer clock close to the fixture timestamp so the
# integrator screen-verdict gate (healthy lineage) renders Rule 2/3 banners.
def _freeze_fresh(monkeypatch: pytest.MonkeyPatch) -> None:
    ts = datetime(2026, 4, 28, 12, 1, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(_dr, "_utcnow", lambda: ts)


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
    for label in ("XAU", "XAG", "BTC", "VIX", "DXY", "10Y", "OIL", "SPY", "QQQ", "GLD", "GDX", "SLV", "XLE"):
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
    # PRD-138: row 1 is spot metals plus BTC, row 2 is macro drivers,
    # then the canonical tradables row.
    html = render_dashboard_html(_payload(), _run())
    slots = _macro_tape_value_slots(html)
    assert [symbol for symbol, _ in slots] == [
        "XAU", "XAG", "BTC",
        "VIX", "DXY", "10Y", "OIL",
        "SPY", "QQQ", "GLD", "GDX", "SLV", "XLE",
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
    for symbol in ("SPY", "QQQ", "GLD", "GDX", "SLV", "XLE"):
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
    # PRD-160: VIX↓ DXY↓ 10Y↓ (risk-on) + BTC↑ → LONG.
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.03))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert "MACRO BIAS: LONG" in html


def test_macro_tape_macro_bias_class_unchanged_with_value_row() -> None:
    # PRD-160: VIX↓ DXY↓ 10Y↓ (risk-on) + BTC↑ → LONG.
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.03))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert 'class="macro-bias long"' in html


# ---------------------------------------------------------------------------
# R1.1 — Macro Bias Summary
# ---------------------------------------------------------------------------

def test_macro_bias_long() -> None:
    # PRD-160 per-driver semantics: VIX↓ DXY↓ 10Y↓ (contra-cyclical falling =
    # risk-on) + BTC↑ (pro-cyclical rising = risk-on) → 4 long votes → LONG.
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.03))
    html = render_dashboard_html(p, _run())
    assert "MACRO BIAS: LONG" in html


def test_macro_bias_short() -> None:
    # PRD-160: VIX↑ DXY↑ 10Y↑ (contra-cyclical rising = risk-off) + BTC↓
    # (pro-cyclical falling = risk-off) → 4 short votes → SHORT.
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=-0.01))
    html = render_dashboard_html(p, _run())
    assert "MACRO BIAS: SHORT" in html


def test_macro_bias_mixed() -> None:
    # PRD-160: DXY↓ + 10Y↓ → 2 long; VIX↑ + BTC↓ → 2 short → tie → MIXED.
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=-0.01, tnx=-0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert "MACRO BIAS: MIXED" in html


def test_macro_bias_element_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'class="macro-bias' in html  # matches macro-bias long/short/mixed


# ---------------------------------------------------------------------------
# PRD-160 — per-driver cyclicality in macro_bias arithmetic
# ---------------------------------------------------------------------------

def test_prd160_contra_cyclical_falling_is_long() -> None:
    # Headline failing case: VIX↓ DXY↓ 10Y↓ are all risk-ON (falling
    # contra-cyclical drivers). The old arrow-count arithmetic read three
    # falling arrows as SHORT while the sub-signals said "VIX permits longs".
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.0))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert "MACRO BIAS: LONG" in html
    assert "MACRO BIAS: SHORT" not in html


def test_prd160_contra_cyclical_rising_is_short() -> None:
    # VIX↑ DXY↑ 10Y↑ are all risk-OFF (rising contra-cyclical drivers).
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=0.0))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert "MACRO BIAS: SHORT" in html
    assert "MACRO BIAS: LONG" not in html


def test_prd160_pro_cyclical_btc_keeps_sign() -> None:
    # BTC is pro-cyclical: rising = risk-on. Contra drivers flat → one long
    # vote → LONG. Confirms the per-driver flip does not invert BTC.
    p = _payload(macro_drivers=_macro_drivers(vix=0.0, dxy=0.0, tnx=0.0, btc=0.05))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert "MACRO BIAS: LONG" in html


# ---------------------------------------------------------------------------
# PRD-160 — unwind of the PRD-158 integrator workaround. With the corrected
# arithmetic the integrator receives the semantic direction, so Rule 3 fires
# only on genuine regime/macro/setup divergence — not on the old false
# positive where risk-on drivers were mislabeled SHORT.
# ---------------------------------------------------------------------------

def test_prd160_unwind_no_false_conflict_when_macro_agrees(monkeypatch) -> None:
    _freeze_fresh(monkeypatch)
    # Risk-on macro (VIX↓ DXY↓ 10Y↓ → LONG), RISK_ON regime (longs), and a
    # qualifying long setup all agree → no directional conflict. Pre-fix the
    # old arithmetic produced "short" here and Rule 3 fired spuriously,
    # suppressing the MACRO BIAS label.
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A", bias="BULL")})
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.0))
    html = render_dashboard_html(p, _run(), market_map=mm)
    assert RULE3_MIXED_VERDICT not in html
    assert "MACRO BIAS: LONG" in html


def test_prd160_rule3_still_fires_on_genuine_divergence(monkeypatch) -> None:
    _freeze_fresh(monkeypatch)
    # Genuinely risk-off macro (VIX↑ DXY↑ 10Y↑ → SHORT) against a RISK_ON
    # regime (longs) and a long setup → real conflict → Rule 3 fires and the
    # raw MACRO BIAS label is suppressed.
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A", bias="BULL")})
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=0.0))
    html = render_dashboard_html(p, _run(), market_map=mm)
    assert RULE3_MIXED_VERDICT in html
    assert "MACRO BIAS: SHORT" not in html


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
    # PRD-160: VIX↓ DXY↓ 10Y↓ (risk-on) + BTC↑ → LONG.
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.03))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert 'class="macro-bias long"' in html


def test_macro_bias_short_class() -> None:
    # PRD-160: VIX↑ DXY↑ 10Y↑ (risk-off) + BTC↓ → SHORT.
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert 'class="macro-bias short"' in html


def test_macro_bias_mixed_class() -> None:
    # PRD-160: DXY↓ + 10Y↓ → 2 long; VIX↑ + BTC↓ → 2 short → MIXED.
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=-0.01, tnx=-0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert 'class="macro-bias mixed"' in html


# ---------------------------------------------------------------------------
# PRD-062 — Macro Pressure block
# ---------------------------------------------------------------------------

def _macro_pressure_block(html: str) -> str:
    parts = html.split('class="macro-pressure-line', 1)
    assert len(parts) == 2, 'macro-pressure-line not found'
    return parts[1].split("</div>", 1)[0]


def test_macro_pressure_block_present() -> None:
    # PRD-217: pressure renders as one inline line (no standalone disclosure).
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    assert 'class="macro-pressure-line' in html
    assert '<details id="macro-pressure">' not in html


def test_macro_pressure_block_no_data_when_empty_drivers() -> None:
    # Empty payload drivers + no snapshot → truly no data → "MACRO PRESSURE UNAVAILABLE"
    html = render_dashboard_html(
        _payload(), _run(), macro_snapshot_path=Path("/nonexistent/no_snap.json")
    )
    block = _macro_pressure_block(html)
    assert "Macro pressure unavailable" in block
    assert "NO PRESSURE DATA" not in block


def test_macro_pressure_block_no_data_does_not_raise() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'class="macro-pressure-line' in html


def test_macro_pressure_block_risk_on_drivers_produce_decision_phrase() -> None:
    # vix falling, dxy falling, btc rising → translated to long-permitting phrases.
    drivers = _macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.01, btc=0.05)
    drivers["rates"]["change_bps"] = -5.0
    html = render_dashboard_html(_payload(macro_drivers=drivers), _run())
    block = _macro_pressure_block(html)
    assert "VIX permits longs" in block
    assert "DXY supports risk-on" in block
    assert "BTC supports risk-on" in block


def test_macro_pressure_block_risk_off_drivers_produce_decision_phrase() -> None:
    # vix rising, dxy rising, btc falling → translated to long-blocking phrases.
    drivers = _macro_drivers(vix=0.05, dxy=0.01, tnx=0.05, btc=-0.05)
    drivers["rates"]["change_bps"] = 5.0
    html = render_dashboard_html(_payload(macro_drivers=drivers), _run())
    block = _macro_pressure_block(html)
    assert "VIX blocks longs" in block
    assert "DXY pressures longs" in block
    assert "BTC pressures risk-on" in block


def test_macro_pressure_block_position_after_macro_tape() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    tape_pos = html.find('id="macro-tape"')
    pressure_pos = html.find('class="macro-pressure-line')
    assert tape_pos < pressure_pos


def test_macro_pressure_block_position_after_system_state() -> None:
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    system_pos = html.find('id="system-state"')
    pressure_pos = html.find('class="macro-pressure-line')
    assert system_pos < pressure_pos


# ---------------------------------------------------------------------------
# PRD-073 — R3: Macro pressure driver labels
# ---------------------------------------------------------------------------

