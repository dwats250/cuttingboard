"""Tests for PRD-036 — slim dashboard renderer (read-only)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    main,
    render_dashboard_html,
    write_dashboard,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _trade(
    symbol: str = "SPY",
    direction: str = "LONG",
    strategy_tag: str = "BULL_CALL_SPREAD",
    entry_mode: str = "LIMIT",
) -> dict:
    return {
        "symbol": symbol,
        "direction": direction,
        "strategy_tag": strategy_tag,
        "entry_mode": entry_mode,
    }


def _payload(
    *,
    top_trades: list | None = None,
    validation_halt_detail: dict | None = None,
    tradable: bool | None = True,
    market_regime: str = "RISK_ON",
    timestamp: str = "2026-04-28T12:00:00Z",
) -> dict:
    return {
        "schema_version": "1.0",
        "run_status": "OK",
        "meta": {"timestamp": timestamp, "symbols_scanned": 5},
        "summary": {
            "market_regime": market_regime,
            "tradable": tradable,
            "router_mode": "MIXED",
        },
        "sections": {
            "top_trades": top_trades if top_trades is not None else [],
            "watchlist": [],
            "rejected": [],
            "option_setups_detail": [],
            "chain_results_detail": [],
            "continuation_audit": None,
            "watch_summary_detail": None,
            "validation_halt_detail": validation_halt_detail,
        },
    }


def _run(
    *,
    status: str = "SUCCESS",
    posture: str = "CONTROLLED_LONG",
    confidence: float = 0.75,
    system_halted: bool = False,
    kill_switch: bool = False,
    errors: list | None = None,
    data_status: str = "ok",
) -> dict:
    return {
        "run_id": "live-20260428T120000Z",
        "status": status,
        "posture": posture,
        "confidence": confidence,
        "system_halted": system_halted,
        "kill_switch": kill_switch,
        "errors": errors if errors is not None else [],
        "data_status": data_status,
        "outcome": "NO_TRADE",
        "mode": "LIVE",
        "timestamp": "2026-04-28T12:00:00Z",
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# test_reads_required_files
# ---------------------------------------------------------------------------

def test_reads_required_files(tmp_path: Path) -> None:
    payload_file = tmp_path / "latest_payload.json"
    run_file = tmp_path / "latest_run.json"
    out_file = tmp_path / "dashboard.html"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")
    main(payload_path=payload_file, run_path=run_file, output_path=out_file)
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "<html" in content
    assert "dashboard-header" in content


# ---------------------------------------------------------------------------
# test_missing_payload_fails
# ---------------------------------------------------------------------------

def test_missing_payload_fails(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="missing"):
        main(
            payload_path=tmp_path / "no_payload.json",
            run_path=tmp_path / "run.json",
            output_path=tmp_path / "out.html",
        )


# ---------------------------------------------------------------------------
# test_missing_run_fails
# ---------------------------------------------------------------------------

def test_missing_run_fails(tmp_path: Path) -> None:
    payload_file = tmp_path / "latest_payload.json"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    with pytest.raises(RuntimeError, match="missing"):
        main(
            payload_path=payload_file,
            run_path=tmp_path / "no_run.json",
            output_path=tmp_path / "out.html",
        )


# ---------------------------------------------------------------------------
# test_invalid_json_fails
# ---------------------------------------------------------------------------

def test_invalid_json_fails(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    run_file = tmp_path / "run.json"
    run_file.write_text(json.dumps(_run()), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid JSON"):
        main(payload_path=bad, run_path=run_file, output_path=tmp_path / "out.html")


# ---------------------------------------------------------------------------
# test_field_mapping_exact
# ---------------------------------------------------------------------------

def test_field_mapping_exact() -> None:
    p = _payload(
        market_regime="CHAOTIC",
        tradable=False,
        timestamp="2026-01-15T09:30:00Z",
        validation_halt_detail={"reason": "VIX_SPIKE_HALT"},
    )
    r = _run(
        status="HALT",
        posture="STAY_FLAT",
        confidence=0.625,
        system_halted=True,
        kill_switch=False,
        errors=["quota_exceeded_unique"],
        data_status="stale",
    )
    html = render_dashboard_html(p, r)

    # HEADER — each value sourced from its exact R3 path
    assert "2026-01-15T09:30:00Z" in html       # payload["meta"]["timestamp"]
    assert "HALT" in html                         # run["status"]
    assert "CHAOTIC" in html                      # payload["summary"]["market_regime"]
    assert "STAY_FLAT" in html                    # run["posture"]
    assert "0.625" in html                        # run["confidence"]

    # SYSTEM STATE
    assert "NO" in html                           # tradable=False → NO
    assert "VIX_SPIKE_HALT" in html               # validation_halt_detail["reason"]

    # RUN HEALTH
    assert "YES" in html                           # system_halted=True → YES
    assert "quota_exceeded_unique" in html         # errors[0]
    # stale_data: data_status != "ok" → True → YES appears (among other YESes)


# ---------------------------------------------------------------------------
# test_primary_visibility
# ---------------------------------------------------------------------------

def test_primary_visibility() -> None:
    # No trades → primary-setup and secondary-setups both absent
    html_empty = render_dashboard_html(_payload(top_trades=[]), _run())
    assert 'id="primary-setup"' not in html_empty
    assert 'id="secondary-setups"' not in html_empty

    # 1 trade → primary present, secondary absent
    html_one = render_dashboard_html(_payload(top_trades=[_trade()]), _run())
    assert 'id="primary-setup"' in html_one
    assert 'id="secondary-setups"' not in html_one

    # 2+ trades → both present
    html_two = render_dashboard_html(_payload(top_trades=[_trade("SPY"), _trade("QQQ")]), _run())
    assert 'id="primary-setup"' in html_two
    assert 'id="secondary-setups"' in html_two


# ---------------------------------------------------------------------------
# test_secondary_limit
# ---------------------------------------------------------------------------

def test_secondary_limit() -> None:
    trades = [_trade(symbol=f"SYM{i}") for i in range(10)]
    html = render_dashboard_html(_payload(top_trades=trades), _run())

    # SYM0 is primary; SYM1–SYM4 are secondary (max 4)
    assert "SYM0" in html
    assert "SYM1" in html
    assert "SYM4" in html
    # SYM5–SYM9 must not appear
    for i in range(5, 10):
        assert f"SYM{i}" not in html


# ---------------------------------------------------------------------------
# test_hidden_sections
# ---------------------------------------------------------------------------

def test_hidden_sections() -> None:
    # null validation_halt_detail → Stay Flat Reason label absent
    html_no_reason = render_dashboard_html(
        _payload(validation_halt_detail=None), _run()
    )
    assert "Stay Flat Reason" not in html_no_reason

    # non-null reason → label present
    html_with_reason = render_dashboard_html(
        _payload(validation_halt_detail={"reason": "STAY_FLAT posture"}), _run()
    )
    assert "Stay Flat Reason" in html_with_reason

    # no errors → Error label absent
    html_no_err = render_dashboard_html(_payload(), _run(errors=[]))
    assert ">Error<" not in html_no_err

    # with error → error text present
    html_with_err = render_dashboard_html(_payload(), _run(errors=["disk_full_unique"]))
    assert "disk_full_unique" in html_with_err


# ---------------------------------------------------------------------------
# test_no_unapproved_fields
# ---------------------------------------------------------------------------

def test_no_unapproved_fields() -> None:
    html = render_dashboard_html(_payload(), _run()).lower()
    for field in (
        "net_score",
        "router_mode",
        "run_id",
        "candidates_generated",
        "energy_score",
        "index_score",
        "schema_version",
        "symbols_scanned",
        "watchlist",
        "rejected",
    ):
        assert field not in html, f"Unapproved field rendered: {field}"


# ---------------------------------------------------------------------------
# test_ascii_only
# ---------------------------------------------------------------------------

def test_ascii_only() -> None:
    html = render_dashboard_html(_payload(), _run())
    non_ascii = [c for c in html if ord(c) >= 128]
    assert not non_ascii, f"Non-ASCII chars found: {non_ascii[:5]}"


# ---------------------------------------------------------------------------
# test_deterministic_output
# ---------------------------------------------------------------------------

def test_deterministic_output() -> None:
    p = _payload(top_trades=[_trade("SPY"), _trade("QQQ")])
    r = _run()
    assert render_dashboard_html(p, r) == render_dashboard_html(p, r)


# ---------------------------------------------------------------------------
# test_macro_tape_present
# ---------------------------------------------------------------------------

def test_macro_tape_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'id="macro-tape"' in html


# ---------------------------------------------------------------------------
# test_macro_tape_section_order
# ---------------------------------------------------------------------------

def test_macro_tape_section_order() -> None:
    html = render_dashboard_html(_payload(), _run())
    header_pos = html.index('id="dashboard-header"')
    macro_pos = html.index('id="macro-tape"')
    system_pos = html.index('id="system-state"')
    assert header_pos < macro_pos < system_pos


# ---------------------------------------------------------------------------
# test_macro_tape_exact_fields
# ---------------------------------------------------------------------------

def test_macro_tape_exact_fields() -> None:
    p = _payload(market_regime="RISK_OFF", tradable=False)
    r = _run(
        posture="STAY_FLAT",
        confidence=0.25,
        system_halted=True,
        kill_switch=False,
        data_status="stale",
    )
    html = render_dashboard_html(p, r)
    macro = html.split('<div class="block" id="macro-tape">', 1)[1]
    macro = macro.split('<div class="block" id="system-state">', 1)[0]

    for label, value in (
        ("market_regime", "RISK_OFF"),
        ("posture", "STAY_FLAT"),
        ("confidence", "0.25"),
        ("tradable", "NO"),
        ("system_halted", "YES"),
        ("kill_switch", "NO"),
        ("data_status", "stale"),
    ):
        assert label in macro
        assert value in macro


# ---------------------------------------------------------------------------
# test_macro_tape_includes_confidence
# ---------------------------------------------------------------------------

def test_macro_tape_includes_confidence() -> None:
    html = render_dashboard_html(_payload(), _run(confidence=0.875))
    macro = html.split('<div class="block" id="macro-tape">', 1)[1]
    assert "confidence" in macro
    assert "0.875" in macro


# ---------------------------------------------------------------------------
# test_macro_tape_rejects_phantom_fields
# ---------------------------------------------------------------------------

def test_macro_tape_rejects_phantom_fields() -> None:
    html = render_dashboard_html(_payload(), _run())
    macro = html.split('<div class="block" id="macro-tape">', 1)[1]
    macro = macro.split('<div class="block" id="system-state">', 1)[0].lower()
    for field in (
        '<div class="label">timestamp</div>',
        '<div class="label">status</div>',
        '<div class="label">stay flat reason</div>',
        '<div class="label">error</div>',
        '<div class="label">stale data</div>',
        '<div class="label">router_mode</div>',
        '<div class="label">run_id</div>',
        '<div class="label">net_score</div>',
    ):
        assert field not in macro, f"Phantom macro field rendered: {field}"


# ---------------------------------------------------------------------------
# test_macro_tape_no_derivation
# ---------------------------------------------------------------------------

def test_macro_tape_no_derivation() -> None:
    html = render_dashboard_html(_payload(tradable=True), _run(data_status="delayed"))
    macro = html.split('<div class="block" id="macro-tape">', 1)[1]
    macro = macro.split('<div class="block" id="system-state">', 1)[0]
    assert "data_status" in macro
    assert "delayed" in macro
    assert "Stale Data" not in macro
    assert ">YES<" in macro  # tradable only
    assert ">NO<" in macro   # system_halted and kill_switch only


# ---------------------------------------------------------------------------
# test_no_mutation
# ---------------------------------------------------------------------------

def test_no_mutation() -> None:
    p = _payload(top_trades=[_trade("NVDA")])
    r = _run(errors=["some_error"])
    p_before = copy.deepcopy(p)
    r_before = copy.deepcopy(r)
    render_dashboard_html(p, r)
    assert p == p_before
    assert r == r_before
