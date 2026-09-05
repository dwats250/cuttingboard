"""PRD-333: GEX synthetic reference carrier — carrier/fragment guards.

Attacks reference/live confusion, SPX/SPY confusion, freshness/semantic leakage,
laundering, and geometry duplication. Whole-dashboard placement/coexistence and
decision-region invariance live in tests/test_dashboard_renderer.py.
"""
from __future__ import annotations

import ast
import copy
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cuttingboard.delivery import gex_card, gex_reference
from tests.test_gex_card import _rich

_MOD = Path(gex_reference.__file__)
_RES = gex_reference._RESOURCE
_NOW = datetime(2026, 8, 20, 20, 43, tzinfo=timezone.utc)

# The frozen synthetic values (derived once from tests/test_gex_card.py::_rich).
_SPOT = 7747.71
_TOTAL = 125513999999.99998
_CALL_WALL = 7850.0
_PUT_WALL = 7650.0


def _envelope() -> dict:
    return json.loads(_RES.read_text(encoding="utf-8"))


# ---- R8: the bundled resource is valid, and build validation is real ----

def test_bundled_resource_builds():
    ref = gex_reference.build_reference(_envelope())
    assert ref is not None
    assert ref.scenario_id == "spx-structure-v1"
    assert ref.instrument == "SPX"
    assert len(ref.profile.window_bins) == 31
    assert ref.profile.spot == pytest.approx(_SPOT)


def test_frozen_values_traceable_to_helper():
    # Guards fixture drift: the bundled numbers must equal the frozen _rich scenario.
    env = _envelope()
    assert env["spot"] == pytest.approx(_SPOT)
    assert env["gex_total_1pct_usd"] == pytest.approx(_TOTAL)
    assert env["call_wall"]["strike"] == _CALL_WALL
    assert env["put_wall"]["strike"] == _PUT_WALL
    assert env["authoring_helper_path"] == "tests/test_gex_card.py::_rich"


# ---- R3: distinct envelope shape; NO production identity fields ----

def test_envelope_shape_is_reference_not_production():
    env = _envelope()
    for k in ("reference_schema_version", "kind", "scenario_id", "instrument",
              "observation_date", "authoring_basis_sha", "authoring_helper_path",
              "synthetic_source", "by_strike"):
        assert k in env, f"missing reference field {k}"
    assert env["kind"] == "synthetic_reference"
    assert env["observation_date"] is None
    for forbidden in ("schema_version", "source", "data_delay", "fetched_at_utc"):
        assert forbidden not in env, f"production identity field present: {forbidden}"


def test_fragment_marks_reference_kind_not_gex_context():
    frag = gex_reference.render_reference_fragment()
    assert 'data-gex-kind="reference"' in frag
    assert 'id="gex-reference"' in frag
    assert 'id="gex-context"' not in frag           # not the current card wrapper


# ---- R2: five identity surfaces + always-visible availability line ----

def test_five_identity_surfaces():
    frag = gex_reference.render_reference_fragment()
    assert "GEX REFERENCE" in frag                                     # collapsed summary
    assert "REFERENCE - SYNTHETIC SPX EXAMPLE" in frag                 # expanded heading
    assert "REFERENCE &middot; SYNTHETIC SPX EXAMPLE" in frag          # ladder visible caption
    assert "Reference synthetic SPX example, not live" in frag         # ladder accessible name
    # provenance block: scenario_id, instrument, null observation date
    assert "spx-structure-v1" in frag
    assert "Instrument: SPX" in frag
    assert "Observation date: none (synthetic)" in frag
    assert "current availability is shown in TAPE" in frag


def test_ladder_caption_and_aria_both_carry_identity():
    # a ladder crop (visible caption) OR screen reader (aria) must not lose identity
    frag = gex_reference.render_reference_fragment()
    svg = frag[frag.index("<svg"):frag.index("</svg>")]
    assert "REFERENCE" in svg and "SYNTHETIC" in svg                   # visible <text>
    aria = re.search(r'aria-label="([^"]*)"', svg).group(1)
    assert "Reference synthetic SPX example" in aria


# ---- R5: no live/current implication, no directional/predictive language ----

def test_no_live_timestamp_or_source_footer():
    frag = gex_reference.render_reference_fragment()
    assert not re.search(r"\d{4}-\d{2}-\d{2}T", frag), "timestamp in reference subtree"
    low = frag.lower()
    for tok in ("cboe", "as of", "delayed", "fetched_at"):
        assert tok not in low, f"live/current footer token: {tok!r}"


def test_no_directional_or_predictive_terms():
    frag = gex_reference.render_reference_fragment().lower()
    for tok in ("dealer", "support", "resistance", "magnet", " pin", "prediction", "predict"):
        assert tok not in frag, f"prohibited term: {tok!r}"


def test_example_spot_is_spx_scenario_not_spy():
    frag = gex_reference.render_reference_fragment()
    assert "7747" in frag                            # frozen SPX example spot
    assert "SPX strikes are not SPY price levels" in frag


# ---- R4: two-way carrier rejection; rename/provenance/laundering rejected ----

def test_current_admission_rejects_reference_envelope():
    assert gex_card.build_gex_card(_envelope(), now=_NOW) is None


def test_reference_admission_rejects_production_snapshot():
    # fresh, stale and mutated production snapshots must all be rejected
    assert gex_reference.build_reference(_rich()) is None
    stale = copy.deepcopy(_rich())
    stale["fetched_at_utc"] = "2000-01-01T00:00:00+00:00"
    assert gex_reference.build_reference(stale) is None


@pytest.mark.parametrize("mutation", [
    {"kind": "gex_snapshot_v1"},
    {"kind": "synthetic_reference_x"},
    {"scenario_id": "other"},
    {"instrument": "SPY"},
    {"observation_date": "2026-01-01"},
    {"reference_schema_version": 2},
    {"authoring_basis_sha": ""},
    {"authoring_helper_path": ""},
    {"synthetic_source": ""},
    {"schema_version": 1},                           # production identity injected (laundering)
    {"source": "cboe_delayed_quotes"},
    {"fetched_at_utc": "2026-01-01T00:00:00+00:00"},
])
def test_mutated_envelope_rejected(mutation):
    env = _envelope()
    env.update(mutation)
    assert gex_reference.build_reference(env) is None


def test_contradictory_aggregate_rejected():
    env = _envelope()
    env["gex_total_1pct_usd"] = env["gex_total_1pct_usd"] + 1.0     # break reconciliation
    assert gex_reference.build_reference(env) is None


@pytest.mark.parametrize("bad_call", [float("nan"), float("inf"), True, "x"])
def test_non_finite_carrier_rejected(bad_call):
    env = _envelope()
    env["by_strike"]["call_modeled_magnitude_1pct_usd"][0] = bad_call
    assert gex_reference.build_reference(env) is None


# ---- R8: invalid/missing -> labeled unavailable, no numbers, no ladder, no fallback ----

def test_missing_resource_yields_unavailable(monkeypatch):
    monkeypatch.setattr(gex_reference, "_RESOURCE", _RES.parent / "nope.json")
    frag = gex_reference.render_reference_fragment()
    assert frag.count('id="gex-reference"') == 1
    assert "Reference example unavailable." in frag
    assert "<svg" not in frag and "MODEL NET*" not in frag


def test_malformed_json_yields_unavailable(tmp_path, monkeypatch):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json", encoding="utf-8")
    monkeypatch.setattr(gex_reference, "_RESOURCE", bad)
    frag = gex_reference.render_reference_fragment()
    assert "Reference example unavailable." in frag
    assert "<svg" not in frag


def test_unavailable_disclosure_still_labeled():
    # even unavailable keeps the reference identity in the summary (never mistaken current)
    frag = gex_reference._unavailable()
    assert "GEX REFERENCE" in frag and 'data-gex-kind="reference"' in frag


# ---- R5/R7: clock and input independence (structural, not just labeled) ----

def test_fragment_is_input_and_clock_independent():
    a = gex_reference.render_reference_fragment()
    b = gex_reference.render_reference_fragment()
    assert a == b
    # render entry takes NO parameters -> cannot depend on clock/snapshot/network
    import inspect
    assert list(inspect.signature(gex_reference.render_reference_fragment).parameters) == []


# ---- R9: geometry reuse, no second implementation ----

def test_no_duplicate_geometry_implementation():
    src = _MOD.read_text(encoding="utf-8")
    tree = ast.parse(src)
    defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    # the reference must NOT redefine profile/ladder/table geometry
    for banned in ("_compute_profile", "_svg_ladder", "_accessible_table", "_ladder_rows",
                   "_build_profile", "_profile_block"):
        assert banned not in defined, f"duplicate geometry defined: {banned}"


# ---- R11: import isolation (only gex_card; never gex_snapshot) ----

def test_import_isolation():
    src = _MOD.read_text(encoding="utf-8")
    assert "gex_snapshot" not in src, "reference must not reference gex_snapshot"
    tree = ast.parse(src)
    cb_deps: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("cuttingboard"):
            for alias in node.names:
                cb_deps.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("cuttingboard"):
                    cb_deps.add(alias.name)
    assert cb_deps == {"gex_card"}, f"unexpected cuttingboard imports: {cb_deps}"
