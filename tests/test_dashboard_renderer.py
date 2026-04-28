"""Tests for PRD-036 — slim dashboard renderer (read-only)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    HISTORY_LIMIT,
    _resolve_previous_run,
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
    regime: str = "RISK_ON",
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
        "regime": regime,
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


# ---------------------------------------------------------------------------
# PRD-041 — run delta
# ---------------------------------------------------------------------------

def test_run_delta_present_with_previous_run() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run(posture="STAY_FLAT"))
    assert 'id="run-delta"' in html


def test_run_delta_hidden_without_previous_run() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=None)
    assert 'id="run-delta"' not in html


def test_run_delta_detects_changes() -> None:
    current = _run(
        regime="NEUTRAL",
        posture="CONTROLLED_LONG",
        confidence=0.75,
        system_halted=False,
    )
    previous = _run(
        regime="RISK_OFF",
        posture="STAY_FLAT",
        confidence=0.25,
        system_halted=True,
    )
    html = render_dashboard_html(_payload(), current, previous_run=previous)
    delta = html.split('<div class="block" id="run-delta">', 1)[1]
    delta = delta.split('<div class="block" id="system-state">', 1)[0]

    assert "Regime: RISK_OFF -&gt; NEUTRAL" in delta
    assert "Posture: STAY_FLAT -&gt; CONTROLLED_LONG" in delta
    assert "Confidence: 0.25 -&gt; 0.75" in delta
    assert "System Halted: YES -&gt; NO" in delta


def test_run_delta_ignores_unchanged_fields() -> None:
    current = _run()
    previous = _run()
    html = render_dashboard_html(_payload(), current, previous_run=previous)
    delta = html.split('<div class="block" id="run-delta">', 1)[1]
    delta = delta.split('<div class="block" id="system-state">', 1)[0]

    assert "No changes since last run" in delta
    assert "Regime:" not in delta
    assert "Posture:" not in delta
    assert "Confidence:" not in delta
    assert "System Halted:" not in delta


def test_run_delta_correct_previous_selection_by_timestamp(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    oldest = _run(status="OLD", confidence=0.1)
    oldest["timestamp"] = "2026-04-28T10:00:00Z"
    newest = _run(status="NEW", confidence=0.2)
    newest["timestamp"] = "2026-04-28T12:00:00Z"
    previous = _run(status="PREV", confidence=0.3)
    previous["timestamp"] = "2026-04-28T11:00:00Z"

    (logs_dir / "run_oldest.json").write_text(json.dumps(oldest), encoding="utf-8")
    (logs_dir / "run_newest.json").write_text(json.dumps(newest), encoding="utf-8")
    (logs_dir / "run_previous.json").write_text(json.dumps(previous), encoding="utf-8")

    assert _resolve_previous_run(logs_dir) == previous


def test_run_delta_no_unapproved_fields() -> None:
    previous = _run(status="HALT", kill_switch=True, data_status="stale")
    html = render_dashboard_html(_payload(), _run(), previous_run=previous)
    delta = html.split('<div class="block" id="run-delta">', 1)[1]
    delta = delta.split('<div class="block" id="system-state">', 1)[0]

    for field in ("Status:", "Kill Switch:", "Data Status:", "Outcome:", "Run Id:"):
        assert field not in delta


def test_render_function_does_not_discover_files(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "cuttingboard.delivery.dashboard_renderer._resolve_previous_run",
        lambda logs_dir: (_ for _ in ()).throw(AssertionError("unexpected discovery")),
    )
    html = render_dashboard_html(_payload(), _run(), previous_run=_run())
    assert 'id="run-delta"' in html


def test_run_delta_deterministic_output() -> None:
    payload = _payload()
    current = _run(regime="NEUTRAL", posture="STAY_FLAT", confidence=0.0)
    previous = _run(regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.75)
    assert render_dashboard_html(payload, current, previous_run=previous) == render_dashboard_html(
        payload, current, previous_run=previous
    )


# ---------------------------------------------------------------------------
# PRD-042 — run history
# ---------------------------------------------------------------------------

def test_run_history_present() -> None:
    history_runs = [_run()]
    html = render_dashboard_html(_payload(), _run(), history_runs=history_runs)
    assert 'id="run-history"' in html


def test_run_history_limit_enforced(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    payload_file = tmp_path / "latest_payload.json"
    run_file = tmp_path / "latest_run.json"
    out_file = tmp_path / "dashboard.html"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")

    for i in range(HISTORY_LIMIT + 2):
        history_run = _run(
            regime=f"RISK_{i}",
            posture=f"POSTURE_{i}",
            confidence=i,
        )
        history_run["timestamp"] = f"2026-04-28T12:{i:02d}:00Z"
        (logs_dir / f"run_{i}.json").write_text(json.dumps(history_run), encoding="utf-8")

    main(payload_path=payload_file, run_path=run_file, output_path=out_file, logs_dir=logs_dir)
    history = out_file.read_text(encoding="utf-8").split('<div class="block" id="run-history">', 1)[1]
    rows = [line for line in history.splitlines() if " | " in line][1:]
    assert len(rows) == HISTORY_LIMIT


def test_run_history_sorted_descending(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    payload_file = tmp_path / "latest_payload.json"
    run_file = tmp_path / "latest_run.json"
    out_file = tmp_path / "dashboard.html"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")

    older = _run(regime="OLDER")
    older["timestamp"] = "2026-04-28T10:00:00Z"
    newest = _run(regime="NEWEST")
    newest["timestamp"] = "2026-04-28T12:00:00Z"
    middle = _run(regime="MIDDLE")
    middle["timestamp"] = "2026-04-28T11:00:00Z"

    (logs_dir / "run_older.json").write_text(json.dumps(older), encoding="utf-8")
    (logs_dir / "run_newest.json").write_text(json.dumps(newest), encoding="utf-8")
    (logs_dir / "run_middle.json").write_text(json.dumps(middle), encoding="utf-8")

    main(payload_path=payload_file, run_path=run_file, output_path=out_file, logs_dir=logs_dir)
    history = out_file.read_text(encoding="utf-8").split('<div class="block" id="run-history">', 1)[1]
    newest_pos = history.index("12:00 | NEWEST")
    middle_pos = history.index("11:00 | MIDDLE")
    older_pos = history.index("10:00 | OLDER")
    assert newest_pos < middle_pos < older_pos


def test_run_history_field_mapping_exact() -> None:
    history_run = _run(
        regime="RISK_OFF",
        posture="STAY_FLAT",
        confidence=0.25,
    )
    history_run["timestamp"] = "2026-04-28T12:50:00Z"

    html = render_dashboard_html(_payload(), _run(), history_runs=[history_run])
    history = html.split('<div class="block" id="run-history">', 1)[1]

    assert "12:50 | RISK_OFF | STAY_FLAT | 0.25" in history


def test_run_history_timestamp_format() -> None:
    history_run = _run()
    history_run["timestamp"] = "2026-04-28T09:30:45Z"

    html = render_dashboard_html(_payload(), _run(), history_runs=[history_run])
    history = html.split('<div class="block" id="run-history">', 1)[1]

    assert "09:30 |" in history
    assert "2026-04-28T09:30:45Z" not in history


def test_run_history_no_extra_fields() -> None:
    history_run = _run(status="FAIL", system_halted=True, kill_switch=True, data_status="stale")
    html = render_dashboard_html(_payload(), _run(), history_runs=[history_run])
    history = html.split('<div class="block" id="run-history">', 1)[1].lower()

    for field in ("status", "system_halted", "kill_switch", "data_status", "outcome", "run_id"):
        assert field not in history


def test_run_history_deterministic_output() -> None:
    payload = _payload()
    run = _run()
    history_runs = [
        _run(regime="RISK_OFF", posture="STAY_FLAT", confidence=0.25),
        _run(regime="NEUTRAL", posture="CONTROLLED_LONG", confidence=0.75),
    ]
    history_runs[0]["timestamp"] = "2026-04-28T12:50:00Z"
    history_runs[1]["timestamp"] = "2026-04-28T11:45:00Z"

    assert render_dashboard_html(payload, run, history_runs=history_runs) == render_dashboard_html(
        payload,
        run,
        history_runs=history_runs,
    )
