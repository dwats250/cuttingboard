"""Tests for PRD-055 — dashboard renderer: Macro tape, macro bias, macro pressure, pressure labels."""

from __future__ import annotations

import json
import re as _re
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


# PRD-335 R4: the MACRO BIAS headline / risk-vote tally / per-component pressure
# phrases are removed from the human surface; the computed engine values survive
# verbatim as data-* attributes on the #macro-tape element. These read them.
def _macro_tape_attr(html: str, name: str) -> str | None:
    m = _re.search(r'<div class="block" id="macro-tape"([^>]*)>', html)
    if not m:
        return None
    a = _re.search(name + r'="([^"]*)"', m.group(1))
    return a.group(1) if a else None


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
    for label in ("XAU", "XAG", "BTC", "VIX", "DXY", "USDJPY", "2Y", "10Y", "30Y",
                  "OIL", "SPY", "QQQ", "GLD", "GDX", "SLV", "XLE"):
        assert label in tape


def test_macro_tape_arrows() -> None:
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=-0.01, tnx=0.0, btc=0.03))
    html = render_dashboard_html(p, _run())
    tape = _macro_tape_block(html)
    # PRD-336 R1: STACKED cell — the label is on its own line; the direction arrow
    # sits on the value line inside .macro-tape-quote (outside the pure value span).
    assert '<span class="macro-tape-label">VIX</span><span class="macro-tape-quote">↑&nbsp;' in tape
    assert '<span class="macro-tape-label">DXY</span><span class="macro-tape-quote">↓&nbsp;' in tape
    assert '<span class="macro-tape-label">10Y</span><span class="macro-tape-quote">→&nbsp;' in tape
    assert '<span class="macro-tape-label">BTC</span><span class="macro-tape-quote">↑&nbsp;' in tape


def test_macro_tape_no_crash_when_market_map_none() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=None)
    assert 'id="macro-tape"' in html


def test_macro_tape_value_row_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    block = _macro_tape_block(html)
    assert 'class="macro-drivers-row"' in block
    assert 'class="macro-tradables-grid"' in block


def test_macro_tape_value_row_slot_order() -> None:
    # PRD-336 R1: four families rendered four-across in DOM order — VOL / CRYPTO
    # (VIX/BTC/ETH), RATES (2Y/5Y/10Y/30Y), FX (DXY/EURUSD/USDJPY/USDCAD), FUTURES
    # (OIL/NG/XAU/XAG) — then the canonical tradables row (unchanged). data-symbol
    # is the slot label (OIL stays OIL though the cockpit shows "CL").
    html = render_dashboard_html(_payload(), _run())
    slots = _macro_tape_value_slots(html)
    assert [symbol for symbol, _ in slots] == [
        "VIX", "BTC", "ETH",
        "2Y", "5Y", "10Y", "30Y",
        "DXY", "EURUSD", "USDJPY", "USDCAD",
        "OIL", "NG", "XAU", "XAG",
        "SPY", "QQQ", "GLD", "GDX", "SLV", "XLE",
    ]


def test_macro_tape_value_row_has_twenty_one_fixed_slots() -> None:
    # PRD-336 R1: slot count grew 16 -> 21 (added the five display-only cockpit
    # drivers 5Y/EURUSD/USDCAD/NG/ETH; the six tradables are unchanged).
    html = render_dashboard_html(_payload(), _run())
    assert len(_macro_tape_value_slots(html)) == 21


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
    # PRD-160 arithmetic preserved (PRD-335 R4: read from data-macro-bias, the
    # visible headline was removed): VIX↓ DXY↓ 10Y↓ (risk-on) + BTC↑ → LONG.
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.03))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert _macro_tape_attr(html, "data-macro-bias") == "LONG"


def test_macro_tape_macro_bias_class_unchanged_with_value_row() -> None:
    # PRD-160/PRD-335 R4: the raw bias direction now lives in data-macro-bias.
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.03))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert _macro_tape_attr(html, "data-macro-bias") == "LONG"


# ---------------------------------------------------------------------------
# R1.1 — Macro Bias Summary (engine data preserved as #macro-tape data-* attrs
# after the PRD-335 R4 prose deletion; the arithmetic guard survives).
# ---------------------------------------------------------------------------

def test_macro_bias_long() -> None:
    # PRD-160 per-driver semantics: VIX↓ DXY↓ 10Y↓ (contra-cyclical falling =
    # risk-on) + BTC↑ (pro-cyclical rising = risk-on) → 4 long votes → LONG.
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.03))
    html = render_dashboard_html(p, _run())
    assert _macro_tape_attr(html, "data-macro-bias") == "LONG"
    assert _macro_tape_attr(html, "data-risk-on") == "4"
    assert _macro_tape_attr(html, "data-risk-off") == "0"


def test_macro_bias_short() -> None:
    # PRD-160: VIX↑ DXY↑ 10Y↑ (contra-cyclical rising = risk-off) + BTC↓
    # (pro-cyclical falling = risk-off) → 4 short votes → SHORT.
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=-0.01))
    html = render_dashboard_html(p, _run())
    assert _macro_tape_attr(html, "data-macro-bias") == "SHORT"
    assert _macro_tape_attr(html, "data-risk-off") == "4"
    assert _macro_tape_attr(html, "data-risk-on") == "0"


def test_macro_bias_mixed() -> None:
    # PRD-160: DXY↓ + 10Y↓ → 2 long; VIX↑ + BTC↓ → 2 short → tie → MIXED.
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=-0.01, tnx=-0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert _macro_tape_attr(html, "data-macro-bias") == "MIXED"


def test_macro_bias_element_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert _macro_tape_attr(html, "data-macro-bias") in {"LONG", "SHORT", "MIXED"}


# ---------------------------------------------------------------------------
# PRD-160 — per-driver cyclicality in macro_bias arithmetic
# ---------------------------------------------------------------------------

def test_prd160_contra_cyclical_falling_is_long() -> None:
    # Headline failing case: VIX↓ DXY↓ 10Y↓ are all risk-ON (falling
    # contra-cyclical drivers). The old arrow-count arithmetic read three
    # falling arrows as SHORT. Read from the preserved data-macro-bias attr.
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.0))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert _macro_tape_attr(html, "data-macro-bias") == "LONG"


def test_prd160_contra_cyclical_rising_is_short() -> None:
    # VIX↑ DXY↑ 10Y↑ are all risk-OFF (rising contra-cyclical drivers).
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=0.0))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert _macro_tape_attr(html, "data-macro-bias") == "SHORT"


def test_prd160_pro_cyclical_btc_keeps_sign() -> None:
    # BTC is pro-cyclical: rising = risk-on. Contra drivers flat → one long
    # vote → LONG. Confirms the per-driver flip does not invert BTC.
    p = _payload(macro_drivers=_macro_drivers(vix=0.0, dxy=0.0, tnx=0.0, btc=0.05))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert _macro_tape_attr(html, "data-macro-bias") == "LONG"


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
    assert _macro_tape_attr(html, "data-macro-bias") == "LONG"


def test_prd160_rule3_still_fires_on_genuine_divergence(monkeypatch) -> None:
    _freeze_fresh(monkeypatch)
    # Genuinely risk-off macro (VIX↑ DXY↑ 10Y↑ → SHORT) against a RISK_ON
    # regime (longs) and a long setup → real conflict → Rule 3 fires. PRD-335 R4:
    # the raw SHORT direction is still carried unconditionally in data-macro-bias
    # (the human MACRO BIAS headline that Rule 3 used to suppress is gone), so the
    # engine data does not lie even as the integrator emits its mixed-tape line.
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A", bias="BULL")})
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=0.0))
    html = render_dashboard_html(p, _run(), market_map=mm)
    assert RULE3_MIXED_VERDICT in html
    assert _macro_tape_attr(html, "data-macro-bias") == "SHORT"


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
# PRD-335 R4 — macro bias direction (was a CSS class; now a data-* attr)
# ---------------------------------------------------------------------------

def test_macro_bias_long_class() -> None:
    # PRD-160: VIX↓ DXY↓ 10Y↓ (risk-on) + BTC↑ → LONG.
    p = _payload(macro_drivers=_macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.02, btc=0.03))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert _macro_tape_attr(html, "data-macro-bias") == "LONG"


def test_macro_bias_short_class() -> None:
    # PRD-160: VIX↑ DXY↑ 10Y↑ (risk-off) + BTC↓ → SHORT.
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=0.01, tnx=0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert _macro_tape_attr(html, "data-macro-bias") == "SHORT"


def test_macro_bias_mixed_class() -> None:
    # PRD-160: DXY↓ + 10Y↓ → 2 long; VIX↑ + BTC↓ → 2 short → MIXED.
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=-0.01, tnx=-0.02, btc=-0.01))
    html = render_dashboard_html(p, _run(), market_map=None)
    assert _macro_tape_attr(html, "data-macro-bias") == "MIXED"


# ---------------------------------------------------------------------------
# PRD-335 R4 — Macro pressure (was inline prose; now data-macro-pressure on
# #macro-tape, carrying the unchanged macro_pressure engine value)
# ---------------------------------------------------------------------------

def test_macro_pressure_block_present() -> None:
    # The engine value is exposed as an attribute, not visible prose; the old
    # standalone disclosure and the inline pressure line are both gone.
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    assert _macro_tape_attr(html, "data-macro-pressure") is not None
    assert '<details id="macro-pressure">' not in html
    assert 'class="macro-pressure-line' not in html


def test_macro_pressure_block_no_data_when_empty_drivers() -> None:
    # Empty payload drivers + no snapshot → no votable data → engine value UNKNOWN
    # (exposed as data-macro-pressure; no visible prose line to author).
    html = render_dashboard_html(
        _payload(), _run(), macro_snapshot_path=Path("/nonexistent/no_snap.json")
    )
    assert _macro_tape_attr(html, "data-macro-pressure") == "UNKNOWN"
    assert 'class="macro-pressure-line' not in html


def test_macro_pressure_block_no_data_does_not_raise() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert _macro_tape_attr(html, "data-macro-pressure") is not None


def test_macro_pressure_block_risk_on_drivers_produce_decision_phrase() -> None:
    # vix falling, dxy falling, btc rising → RISK_ON overall pressure (was
    # translated to "VIX permits longs" prose; PRD-335 R4 keeps the engine value).
    drivers = _macro_drivers(vix=-0.05, dxy=-0.01, tnx=-0.01, btc=0.05)
    drivers["rates"]["change_bps"] = -5.0
    html = render_dashboard_html(_payload(macro_drivers=drivers), _run())
    assert _macro_tape_attr(html, "data-macro-pressure") == "RISK_ON"


def test_macro_pressure_block_risk_off_drivers_produce_decision_phrase() -> None:
    # vix rising, dxy rising, btc falling → RISK_OFF overall pressure.
    drivers = _macro_drivers(vix=0.05, dxy=0.01, tnx=0.05, btc=-0.05)
    drivers["rates"]["change_bps"] = 5.0
    html = render_dashboard_html(_payload(macro_drivers=drivers), _run())
    assert _macro_tape_attr(html, "data-macro-pressure") == "RISK_OFF"


def test_macro_pressure_value_lives_on_macro_tape() -> None:
    # PRD-335 R4: the pressure value is an attribute ON #macro-tape (not a
    # separate block below it), and #system-state still precedes #macro-tape.
    html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run())
    assert _macro_tape_attr(html, "data-macro-pressure") is not None
    assert html.find('id="system-state"') < html.find('id="macro-tape"')


# ---------------------------------------------------------------------------
# PRD-073 — R3: Macro pressure driver labels
# ---------------------------------------------------------------------------

