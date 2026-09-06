"""PRD-335 R8 — the decision-authority fence for the new display-only drivers.

rates_2y (FRED DGS2 2Y), rates_30y (^TYX) and usdjpy (JPY=X) are OBSERVATIONAL /
DISPLAY CONTEXT ONLY. They must never acquire macro-pressure voting authority.
These tests prove the fence at the ACTUAL voting path, not merely at a whitelist:

- F-1  static membership (present in the display registries, absent from every
       decision/voting registration).
- F-2a positive control: the harness CAN see a real vote (proves sensitivity).
- F-2b per-driver + combined pressure INVARIANCE, with an exact result key-set
       assertion (classification reach) and identical policy output.
- F-2c aggregation-reach spy: _overall_pressure is called once with exactly the
       four production components.
- F-2d one-time semantic MUTATION DEMO on a disposable IN-MEMORY copy (never the
       production macro_pressure.py, which is on the decision-boundary STOP list):
       wiring a new driver to vote makes F-2b/F-2c/F-3 go RED — proof the fence is
       load-bearing. The four RED results are recorded in the PR body.
- F-3  sizing invariance through execution_policy._apply_macro_pressure.
- F-4  display-tally invariance: #macro-tape data-risk-* / data-macro-bias are
       byte-identical with and without the new drivers.
- F-5  BOTH driver-key guards accept present/absent and reject unknown; an
       end-to-end build_report_payload + assert_valid_payload path succeeds with
       each new driver present AND absent; and a guard-sync test asserts the two
       whitelists' key sets are equal so they cannot drift.

Plus mixed-cadence honesty (R9) and notification present/absent (R2).
"""
from __future__ import annotations

import copy
import re as _re
from datetime import datetime, timezone

import pytest

from cuttingboard import macro_pressure as mp
from cuttingboard.contract import _MACRO_DRIVER_SYMBOLS, _DAILY_MACRO_DRIVERS
from cuttingboard.contract_types import _OPTIONAL_MACRO_DRIVERS
from cuttingboard.delivery import payload as payload_mod
from cuttingboard.delivery.macro_tape_layout import MACRO_BIAS_DRIVERS
from cuttingboard.delivery.dashboard_renderer import render_dashboard_html
from cuttingboard.execution_policy import _apply_macro_pressure
from cuttingboard.macro_pressure import build_macro_pressure
from cuttingboard.normalization import NormalizedQuote

from tests.dash_helpers import _macro_drivers, _payload, _run
from tests.test_contract_macro_drivers import _build_contract, _macro_quotes

_NEW_DRIVERS = (
    "rates_2y", "rates_30y", "usdjpy",
    # PRD-336: five further display-only cockpit drivers on the same fence.
    "rates_5y", "eurusd", "usdcad", "natgas", "ethereum",
)
# PRD-335 F2: a deterministic render reference date so a dated 2Y render never
# depends on the wall clock. as_of "2026-09-02" is 2 days before this — admissible.
_RENDER_NOW = datetime(2026, 9, 4, 13, 0, tzinfo=timezone.utc)
# The FROZEN production pressure-result key set — a fifth component key here is a
# fence breach (classification reach).
_EXACT_PRESSURE_KEYS = {
    "volatility_pressure", "dollar_pressure", "rates_pressure",
    "bitcoin_pressure", "overall_pressure",
}


def _base() -> dict:
    """Four voting drivers, all NEUTRAL -> overall NEUTRAL."""
    return {
        "volatility": {"symbol": "^VIX", "level": 18.0, "change_pct": 0.0},
        "dollar": {"symbol": "DX-Y.NYB", "level": 104.0, "change_pct": 0.0},
        "rates": {"symbol": "^TNX", "level": 4.2, "change_pct": 0.0, "change_bps": 0.0},
        "bitcoin": {"symbol": "BTC-USD", "level": 60000.0, "change_pct": 0.0},
    }


def _new_block(key: str) -> dict:
    """A display-only driver block with an EXTREME move (that must not vote)."""
    symbol = {
        "rates_2y": "DGS2", "rates_30y": "^TYX", "usdjpy": "JPY=X",
        "rates_5y": "DGS5", "eurusd": "EURUSD=X", "usdcad": "USDCAD=X",
        "natgas": "NG=F", "ethereum": "ETH-USD",
    }[key]
    block = {"symbol": symbol, "level": 3.6, "change_pct": -0.05}
    if key in _DAILY_MACRO_DRIVERS:
        block["as_of"] = "2026-09-02"
    return block


# ---------------------------------------------------------------------------
# F-1 — static membership
# ---------------------------------------------------------------------------

def test_f1_new_drivers_are_display_only_membership() -> None:
    component_drivers = set(mp._COMPONENT_KEYS.values())
    for key in _NEW_DRIVERS:
        # NOT in any voting / bias registration ...
        assert key not in mp._COMPONENT_FIELDS, key
        assert key not in component_drivers, key
        assert key not in MACRO_BIAS_DRIVERS, key
        # ... but ARE in the display / optional registries.
        assert key in _OPTIONAL_MACRO_DRIVERS, key
        assert key in _MACRO_DRIVER_SYMBOLS, key


def test_f1_new_symbols_absent_from_regime_votes() -> None:
    # Site 5 (PRD-336): regime.py votes by SYMBOL via hardcoded .get() reads and a
    # raw_votes list. A display-only driver's quote symbol must never appear in the
    # regime module source — the site the PRD-335 fence did not assert. A
    # whitelist-only check is insufficient; this reaches the actual vote site.
    import inspect
    import cuttingboard.regime as regime_mod
    src = inspect.getsource(regime_mod)
    for key in _NEW_DRIVERS:
        symbol = _MACRO_DRIVER_SYMBOLS[key]
        assert symbol not in src, (
            f"display-only {key} symbol {symbol!r} must not be read by regime.py"
        )


# ---------------------------------------------------------------------------
# F-2a — positive control (the harness CAN see a real vote)
# ---------------------------------------------------------------------------

def test_f2a_positive_control_real_vote_is_visible() -> None:
    base = _base()
    control = _base()
    # Flip two REAL voting drivers to extreme RISK_OFF moves.
    control["volatility"]["change_pct"] = 0.05      # rising VIX -> RISK_OFF
    control["dollar"]["change_pct"] = 0.05          # rising DXY -> RISK_OFF

    base_pressure = build_macro_pressure(base)
    control_pressure = build_macro_pressure(control)
    assert base_pressure["overall_pressure"] == mp.NEUTRAL
    assert control_pressure["overall_pressure"] == mp.RISK_OFF
    assert base_pressure != control_pressure

    base_policy = _apply_macro_pressure("LONG", base_pressure["overall_pressure"], 1.0, "ok")
    control_policy = _apply_macro_pressure("LONG", control_pressure["overall_pressure"], 1.0, "ok")
    # A real RISK_OFF vote blocks a LONG at zero size; base allows at full size.
    assert (base_policy.allowed, base_policy.size_multiplier) == (True, 1.0)
    assert (control_policy.allowed, control_policy.size_multiplier) == (False, 0.0)
    assert (base_policy.allowed, base_policy.size_multiplier) != (
        control_policy.allowed, control_policy.size_multiplier
    )


# ---------------------------------------------------------------------------
# F-2b — invariance per new driver (the fence)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("keys", [*[(k,) for k in _NEW_DRIVERS], _NEW_DRIVERS])
def test_f2b_new_drivers_do_not_change_pressure(keys) -> None:
    base = _base()
    variant = _base()
    for key in keys:
        variant[key] = _new_block(key)

    base_pressure = build_macro_pressure(base)
    variant_pressure = build_macro_pressure(variant)

    # key-for-key identical, AND the exact production key set (a new *_pressure
    # key would be a classification-reach breach).
    assert variant_pressure == base_pressure
    assert set(variant_pressure) == _EXACT_PRESSURE_KEYS

    base_policy = _apply_macro_pressure("LONG", base_pressure["overall_pressure"], 1.0, "ok")
    variant_policy = _apply_macro_pressure("LONG", variant_pressure["overall_pressure"], 1.0, "ok")
    assert (variant_policy.allowed, variant_policy.size_multiplier) == (
        base_policy.allowed, base_policy.size_multiplier
    )


# ---------------------------------------------------------------------------
# F-2c — aggregation reach: exactly four components feed _overall_pressure
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("keys", [(), ("rates_30y",), _NEW_DRIVERS])
def test_f2c_overall_pressure_sees_exactly_four_inputs(keys, monkeypatch) -> None:
    calls: list[list[str]] = []
    real = mp._overall_pressure

    def _spy(components):
        calls.append(list(components))
        return real(components)

    # The call at macro_pressure.py:126 resolves the module global at call time.
    monkeypatch.setattr(mp, "_overall_pressure", _spy)

    drivers = _base()
    for key in keys:
        drivers[key] = _new_block(key)
    build_macro_pressure(drivers)

    assert len(calls) == 1
    # exactly the four production components, in the fixed order
    assert len(calls[0]) == 4
    assert calls[0] == [mp.NEUTRAL, mp.NEUTRAL, mp.NEUTRAL, mp.NEUTRAL]


# ---------------------------------------------------------------------------
# F-2d — one-time semantic MUTATION DEMO on a disposable in-memory copy
# (never edits cuttingboard/macro_pressure.py). Proves the fence is load-bearing:
# wiring a new driver to vote makes the F-2b/F-2c/F-3 assertions go RED.
# ---------------------------------------------------------------------------

def _mutated_pressure(drivers: dict, new_key: str) -> dict:
    """A DISPOSABLE in-memory MUTATION of the macro-pressure logic that WIRES
    ``new_key`` as a fifth voting component — exactly the change the fence forbids.
    It classifies the four production drivers via the real (unmodified)
    macro_pressure helpers, then adds a fifth classification branch and appends the
    fifth component to the aggregation list (mirroring macro_pressure.py:57-90 and
    :126-133). The production module is never touched."""
    result = {
        ck: mp._classify_driver(drv, drivers.get(drv))
        for ck, drv in mp._COMPONENT_KEYS.items()
    }
    block = drivers.get(new_key)
    value = block.get("change_pct") if isinstance(block, dict) else None
    if value is None:
        new_pressure = mp.UNKNOWN
    elif value >= 0.01:
        new_pressure = mp.RISK_ON
    elif value <= -0.01:
        new_pressure = mp.RISK_OFF
    else:
        new_pressure = mp.NEUTRAL
    result[f"{new_key}_pressure"] = new_pressure
    result["overall_pressure"] = mp._overall_pressure([
        result["volatility_pressure"], result["dollar_pressure"],
        result["rates_pressure"], result["bitcoin_pressure"],
        result[f"{new_key}_pressure"],          # the forbidden fifth input
    ])
    return result


@pytest.mark.parametrize("new_key", _NEW_DRIVERS)
def test_f2d_mutation_demo_shows_the_fence_is_load_bearing(new_key) -> None:
    variant = _base()
    variant[new_key] = _new_block(new_key)      # extreme RISK_OFF move on the new driver

    fenced = build_macro_pressure(variant)      # production: the new driver is ignored
    mutated = _mutated_pressure(variant, new_key)

    # RED-1 (F-2b key-set): the mutated result carries a fifth *_pressure key.
    assert f"{new_key}_pressure" in mutated
    assert set(mutated) != _EXACT_PRESSURE_KEYS

    # RED-2 (F-2b equality): the overall pressure flips (one RISK_OFF + four
    # NEUTRAL -> MIXED) where the fenced result stays NEUTRAL.
    assert fenced["overall_pressure"] == mp.NEUTRAL
    assert mutated["overall_pressure"] == mp.MIXED
    assert mutated["overall_pressure"] != fenced["overall_pressure"]

    # RED-3 (F-3 policy): LONG sizing changes (full size -> MIXED 0.75x).
    fenced_policy = _apply_macro_pressure("LONG", fenced["overall_pressure"], 1.0, "ok")
    mutated_policy = _apply_macro_pressure("LONG", mutated["overall_pressure"], 1.0, "ok")
    assert fenced_policy.size_multiplier == 1.0
    assert mutated_policy.size_multiplier == 0.75
    assert mutated_policy.size_multiplier != fenced_policy.size_multiplier

    # The production module was not mutated by this demo.
    assert new_key not in mp._COMPONENT_FIELDS
    assert f"{new_key}_pressure" not in mp._COMPONENT_KEYS


# ---------------------------------------------------------------------------
# F-3 — sizing invariance through the policy path
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("keys", [*[(k,) for k in _NEW_DRIVERS], _NEW_DRIVERS])
def test_f3_sizing_invariant_through_policy(keys) -> None:
    base_pressure = build_macro_pressure(_base())
    variant = _base()
    for key in keys:
        variant[key] = _new_block(key)
    variant_pressure = build_macro_pressure(variant)
    for direction in ("LONG", "SHORT"):
        base_policy = _apply_macro_pressure(direction, base_pressure["overall_pressure"], 1.0, "ok")
        variant_policy = _apply_macro_pressure(direction, variant_pressure["overall_pressure"], 1.0, "ok")
        assert (variant_policy.allowed, variant_policy.size_multiplier) == (
            base_policy.allowed, base_policy.size_multiplier
        )


# ---------------------------------------------------------------------------
# F-4 — display-tally invariance (#macro-tape data-* attributes)
# ---------------------------------------------------------------------------

def _tape_attrs(html: str) -> dict[str, str]:
    import re
    m = re.search(r'<div class="block" id="macro-tape"([^>]*)>', html)
    assert m is not None
    return dict(re.findall(r'(data-[a-z-]+)="([^"]*)"', m.group(1)))


def test_f4_display_tally_invariant_with_new_drivers() -> None:
    without = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), _run(),
                                    market_map=None, now=_RENDER_NOW)
    md = _macro_drivers()
    md["rates_2y"] = {"symbol": "DGS2", "level": 3.6, "change_pct": -0.05, "as_of": "2026-09-02"}
    md["rates_30y"] = {"symbol": "^TYX", "level": 4.7, "change_pct": 0.05}
    md["usdjpy"] = {"symbol": "JPY=X", "level": 148.2, "change_pct": 0.05}
    # PRD-336: the five new display-only drivers, all with extreme moves — the
    # visible bias tally must stay byte-identical (the MACRO_BIAS_DRIVERS fence).
    md["rates_5y"] = {"symbol": "DGS5", "level": 4.4, "change_pct": -0.05, "as_of": "2026-09-02"}
    md["eurusd"] = {"symbol": "EURUSD=X", "level": 1.08, "change_pct": 0.05}
    md["usdcad"] = {"symbol": "USDCAD=X", "level": 1.38, "change_pct": 0.05}
    md["natgas"] = {"symbol": "NG=F", "level": 3.5, "change_pct": 0.05}
    md["ethereum"] = {"symbol": "ETH-USD", "level": 3200.0, "change_pct": 0.05}
    with_new = render_dashboard_html(_payload(macro_drivers=md), _run(),
                                     market_map=None, now=_RENDER_NOW)

    a0, a1 = _tape_attrs(without), _tape_attrs(with_new)
    for attr in ("data-macro-bias", "data-risk-on", "data-risk-off", "data-macro-pressure"):
        assert a0[attr] == a1[attr], (attr, a0[attr], a1[attr])


# ---------------------------------------------------------------------------
# F-5 — both driver-key guards + end-to-end payload + guard-sync
# ---------------------------------------------------------------------------

def _full_macro_drivers() -> dict:
    md = {
        "volatility": {"symbol": "^VIX", "level": 18.0, "change_pct": 1.0},
        "dollar": {"symbol": "DX-Y.NYB", "level": 104.0, "change_pct": 0.1},
        "rates": {"symbol": "^TNX", "level": 4.2, "change_pct": 0.2, "change_bps": 0.8},
        "bitcoin": {"symbol": "BTC-USD", "level": 60000.0, "change_pct": 1.0},
        "rates_2y": {"symbol": "DGS2", "level": 3.6, "change_pct": 2.86, "as_of": "2026-09-02"},
        "rates_30y": {"symbol": "^TYX", "level": 4.7, "change_pct": 0.3},
        "usdjpy": {"symbol": "JPY=X", "level": 148.2, "change_pct": 0.4},
        # PRD-336 display-only cockpit drivers (rates_5y is daily -> carries as_of).
        "rates_5y": {"symbol": "DGS5", "level": 4.4, "change_pct": 0.5, "as_of": "2026-09-02"},
        "eurusd": {"symbol": "EURUSD=X", "level": 1.08, "change_pct": 0.2},
        "usdcad": {"symbol": "USDCAD=X", "level": 1.38, "change_pct": 0.1},
        "natgas": {"symbol": "NG=F", "level": 3.5, "change_pct": 0.6},
        "ethereum": {"symbol": "ETH-USD", "level": 3200.0, "change_pct": 1.2},
    }
    return md


def test_f5_payload_guard_accepts_present_absent_rejects_unknown() -> None:
    present = _full_macro_drivers()
    payload_mod._require_macro_drivers(present)                     # accepts present

    absent = {k: v for k, v in present.items() if k not in _NEW_DRIVERS}
    payload_mod._require_macro_drivers(absent)                     # accepts absence (optional)

    unknown = dict(present)
    # rates_1y is genuinely unregistered (rates_5y is now a valid PRD-336 key).
    unknown["rates_1y"] = {"symbol": "DGS1", "level": 3.9, "change_pct": 0.1}
    with pytest.raises(ValueError, match="unexpected driver keys"):
        payload_mod._require_macro_drivers(unknown)

    # a dated block with a non-date as_of is rejected on the SEPARATE date path.
    bad_date = copy.deepcopy(present)
    bad_date["rates_2y"]["as_of"] = "not-a-date"
    with pytest.raises(ValueError, match="as_of"):
        payload_mod._require_macro_drivers(bad_date)


def _quote(symbol: str, price: float, pct: float, units: str, as_of=None) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol, price=price, pct_change_decimal=pct, volume=1_000_000.0,
        fetched_at_utc=datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc),
        source="fixture", units=units, age_seconds=0.0, as_of=as_of,
    )


def _quotes_with_new() -> dict:
    q = _macro_quotes()
    q["DGS2"] = _quote("DGS2", 3.6, 0.0286, "yield_pct", as_of="2026-09-02")
    q["^TYX"] = _quote("^TYX", 4.7, 0.003, "yield_pct")
    q["JPY=X"] = _quote("JPY=X", 148.2, 0.004, "jpy_per_usd")
    # PRD-336 display-only cockpit drivers (DGS5 is daily -> carries as_of).
    q["DGS5"] = _quote("DGS5", 4.4, 0.005, "yield_pct", as_of="2026-09-02")
    q["EURUSD=X"] = _quote("EURUSD=X", 1.08, 0.002, "usd_per_eur")
    q["USDCAD=X"] = _quote("USDCAD=X", 1.38, 0.001, "cad_per_usd")
    q["NG=F"] = _quote("NG=F", 3.5, 0.006, "usd_price")
    q["ETH-USD"] = _quote("ETH-USD", 3200.0, 0.012, "usd_price")
    return q


def test_f5_contract_guard_accepts_new_drivers_present_and_absent() -> None:
    from cuttingboard.contract import assert_valid_contract

    present = _build_contract(_quotes_with_new())
    assert set(present["macro_drivers"]) >= set(_NEW_DRIVERS)
    assert present["macro_drivers"]["rates_2y"]["as_of"] == "2026-09-02"
    assert present["macro_drivers"]["rates_5y"]["as_of"] == "2026-09-02"
    assert_valid_contract(present)                                 # accepts present

    absent = _build_contract(_macro_quotes())                     # only the four required
    for key in _NEW_DRIVERS:
        assert key not in absent["macro_drivers"]
    assert_valid_contract(absent)                                 # accepts absence


def test_f5_end_to_end_payload_present_and_absent() -> None:
    from cuttingboard.delivery.payload import assert_valid_payload, build_report_payload

    for quotes in (_quotes_with_new(), _macro_quotes()):
        contract = _build_contract(quotes)
        payload = build_report_payload(contract)
        assert_valid_payload(payload)                             # the runtime path succeeds


def test_f5_guard_sync_whitelists_are_equal() -> None:
    # The two independent whitelists must never drift: their key sets are equal to
    # each other and to the canonical driver mapping.
    payload_keys = set(payload_mod._MACRO_DRIVER_FIELD_WHITELIST)
    contract_keys = set(_MACRO_DRIVER_SYMBOLS)
    assert payload_keys == contract_keys
    # and the optional sets agree (the new drivers are optional in both)
    assert set(_DAILY_MACRO_DRIVERS) <= _OPTIONAL_MACRO_DRIVERS


# ---------------------------------------------------------------------------
# R9 — mixed-cadence honesty (renderer + notification)
# ---------------------------------------------------------------------------

# R9: never a "live" / "real-time" / "now" freshness claim beside a driver.
_LIVE_RE = _re.compile(r"\b(live|real-?time|now)\b", _re.IGNORECASE)


def _macro_tape_only(html: str) -> str:
    """Exactly the #macro-tape block: from its open div to the NEXT element that
    carries an id= (the macro-tape's own cells use data-symbol, never id), so the
    GEX reference and other later sections are excluded."""
    after = html.split('id="macro-tape"', 1)[1]
    nxt = after.find('id="')
    return after if nxt == -1 else after[:nxt]


def _two_y_cell(html: str) -> str | None:
    m = _re.search(r'data-symbol="2Y">([^<]*)</span>', html)
    return m.group(1) if m else None


def test_r9_daily_marker_present_only_from_producer_as_of() -> None:
    md = _macro_drivers()
    md["rates_2y"] = {"symbol": "DGS2", "level": 3.6, "change_pct": 2.86, "as_of": "2026-09-02"}
    md["rates_30y"] = {"symbol": "^TYX", "level": 4.7, "change_pct": 0.3}
    html = render_dashboard_html(_payload(macro_drivers=md), _run(), market_map=None, now=_RENDER_NOW)
    tape = html.split('id="macro-tape"', 1)[1].split('id="red-folder"', 1)[0]
    markers = _re.findall(r'<span class="macro-tape-asof">([^<]*)</span>', tape)
    # the marker appears on EXACTLY the daily 2Y cell, and only from its producer as_of
    assert markers == ["Sep 2"]


def test_r9_no_marker_when_no_producer_as_of() -> None:
    md = _macro_drivers()
    md["rates_2y"] = {"symbol": "DGS2", "level": 3.6, "change_pct": 2.86}   # no as_of
    html = render_dashboard_html(_payload(macro_drivers=md), _run(), market_map=None, now=_RENDER_NOW)
    assert 'class="macro-tape-asof"' not in html


def test_r9_no_live_wording_beside_drivers() -> None:
    md = _macro_drivers()
    md["rates_2y"] = {"symbol": "DGS2", "level": 3.6, "change_pct": 2.86, "as_of": "2026-09-02"}
    html = render_dashboard_html(_payload(macro_drivers=md), _run(), market_map=None, now=_RENDER_NOW)
    tape = _macro_tape_only(html)
    assert _LIVE_RE.search(tape) is None, _LIVE_RE.search(tape)


# ---------------------------------------------------------------------------
# F2 (Helm 2026-09-05) — daily 2Y consumer-boundary admission. The FRED carrier
# fails a stale/future fetch closed; this guards the PERSISTED macro-snapshot
# fallback path where a once-valid rates_2y block reaches the dashboard after its
# as_of is no longer admissible. Rendered against a deterministic reference date.
# ---------------------------------------------------------------------------

def _md_with_2y(as_of):
    md = _macro_drivers()
    md["rates_2y"] = {"symbol": "DGS2", "level": 3.61, "change_pct": -1.2}
    if as_of is not None:
        md["rates_2y"]["as_of"] = as_of
    return md


@pytest.mark.parametrize("as_of,expect_number", [
    ("2026-09-02", True),    # age 2 -> admissible
    ("2026-09-01", True),    # age 3 -> admissible
    ("2026-08-30", True),    # age 5 (inclusive boundary) -> admissible
    ("2026-08-29", False),   # age 6 -> stale -> "--"
    ("2026-10-01", False),   # future -> "--"
    ("not-a-date", False),   # malformed -> "--"
    (None, False),           # missing as_of on a present daily block -> "--"
])
def test_f2_daily_2y_admission_matrix(as_of, expect_number) -> None:
    # Direct payload path, deterministic reference date (2026-09-04).
    html = render_dashboard_html(_payload(macro_drivers=_md_with_2y(as_of)), _run(),
                                 market_map=None, now=_RENDER_NOW)
    cell = _two_y_cell(html)
    if expect_number:
        assert cell not in (None, "--"), (as_of, cell)
    else:
        assert cell == "--", (as_of, cell)
        assert 'class="macro-tape-asof"' not in html   # no stale date marker either


def test_f2_persisted_snapshot_present_stale_block_renders_dash() -> None:
    # THE core F2 case (not mere absence): a PRESENT but stale rates_2y block that
    # reaches the dashboard through the persisted macro-snapshot fallback must
    # render "--", never its stale number.
    import json
    import tempfile
    from pathlib import Path
    snapshot = {"macro_drivers": _md_with_2y("2026-08-01")}   # ~5 weeks old
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(snapshot, f)
        snap = Path(f.name)
    try:
        # payload macro_drivers empty -> the renderer reads the persisted snapshot.
        html = render_dashboard_html(_payload(), _run(), market_map=None,
                                     now=_RENDER_NOW, macro_snapshot_path=snap)
        assert _two_y_cell(html) == "--"
        assert "3.61" not in html.split('id="macro-tape"', 1)[1].split('id="red-folder"', 1)[0]
        assert 'class="macro-tape-asof"' not in html
    finally:
        snap.unlink(missing_ok=True)


def test_f2_persisted_snapshot_present_fresh_block_renders_number() -> None:
    # Positive control: a PRESENT fresh block via the same persisted fallback path
    # DOES render its number + date marker (so the guard is not just "always --").
    import json
    import tempfile
    from pathlib import Path
    snapshot = {"macro_drivers": _md_with_2y("2026-09-02")}   # age 2 at _RENDER_NOW
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(snapshot, f)
        snap = Path(f.name)
    try:
        html = render_dashboard_html(_payload(), _run(), market_map=None,
                                     now=_RENDER_NOW, macro_snapshot_path=snap)
        assert _two_y_cell(html) == "3.61"
        tape = html.split('id="macro-tape"', 1)[1].split('id="red-folder"', 1)[0]
        assert 'macro-tape-asof">Sep 2</span>' in tape
    finally:
        snap.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Notification present / absent (R2)
# ---------------------------------------------------------------------------

def _nq(symbol: str, price: float, pct: float, as_of=None) -> NormalizedQuote:
    return _quote(symbol, price, pct, "yield_pct", as_of=as_of)


def test_notification_new_driver_rows_present() -> None:
    from cuttingboard.notifications import _macro_tape_block

    quotes = {
        "^VIX": _nq("^VIX", 18.5, 0.01),
        "DX-Y.NYB": _nq("DX-Y.NYB", 104.2, 0.001),
        "JPY=X": _nq("JPY=X", 148.23, 0.004),
        "DGS2": _nq("DGS2", 3.60, 0.0286, as_of="2026-09-02"),
        "^TNX": _nq("^TNX", 4.21, 0.002),
        "^TYX": _nq("^TYX", 4.72, 0.003),
        "CL=F": _nq("CL=F", 78.5, 0.012),
    }
    rows = _macro_tape_block(quotes)
    text = "\n".join(rows)
    assert any(r.startswith("30Y") and "4.72" in r for r in rows)       # .2f
    assert any(r.startswith("USDJPY") and "148.2" in r for r in rows)   # .1f
    assert any(r.startswith("2Y") and "(Sep 2)" in r for r in rows)     # daily marker
    assert _LIVE_RE.search(text) is None


def test_notification_new_driver_rows_absent_when_quote_missing() -> None:
    from cuttingboard.notifications import _macro_tape_block

    quotes = {
        "^VIX": _nq("^VIX", 18.5, 0.01),
        "DX-Y.NYB": _nq("DX-Y.NYB", 104.2, 0.001),
        "^TNX": _nq("^TNX", 4.21, 0.002),
        "CL=F": _nq("CL=F", 78.5, 0.012),
    }
    rows = _macro_tape_block(quotes)
    # a missing quote simply omits its row -- no placeholder, no exception.
    assert not any(r.startswith("30Y") for r in rows)
    assert not any(r.startswith("USDJPY") for r in rows)
    assert not any(r.startswith("2Y") for r in rows)
