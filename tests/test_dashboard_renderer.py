"""Tests for PRD-055 — Signal Forge dashboard renderer."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    HISTORY_LIMIT,
    _GRADE_ORDER,
    _load_json_optional,
    _resolve_previous_run,
    main,
    render_dashboard_html,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _macro_drivers(
    vix: float = 0.05,
    dxy: float = -0.01,
    tnx: float = 0.02,
    btc: float = 0.03,
) -> dict:
    return {
        "volatility": {"symbol": "^VIX",     "level": 18.0,    "change_pct": vix},
        "dollar":     {"symbol": "DX-Y.NYB", "level": 104.0,   "change_pct": dxy},
        "rates":      {"symbol": "^TNX",     "level": 4.5,     "change_pct": tnx, "change_bps": 2.0},
        "bitcoin":    {"symbol": "BTC-USD",  "level": 65000.0, "change_pct": btc},
    }


def _payload(
    *,
    top_trades: list | None = None,
    trade_decision_detail: list | None = None,
    validation_halt_detail: dict | None = None,
    tradable: bool | None = True,
    market_regime: str = "RISK_ON",
    timestamp: str = "2026-04-28T12:00:00Z",
    macro_drivers: dict | None = None,
) -> dict:
    return {
        "schema_version": "1.0",
        "run_status": "OK",
        "meta": {"timestamp": timestamp, "symbols_scanned": 5},
        "macro_drivers": macro_drivers if macro_drivers is not None else {},
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
            "trade_decision_detail": trade_decision_detail if trade_decision_detail is not None else [],
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
    outcome: str = "NO_TRADE",
    permission: bool | None = None,
) -> dict:
    return {
        "run_id":       "live-20260428T120000Z",
        "status":       status,
        "regime":       regime,
        "posture":      posture,
        "confidence":   confidence,
        "system_halted": system_halted,
        "kill_switch":  kill_switch,
        "errors":       errors if errors is not None else [],
        "data_status":  data_status,
        "outcome":      outcome,
        "permission":   permission,
        "mode":         "LIVE",
        "timestamp":    "2026-04-28T12:00:00Z",
        "warnings":     [],
    }


def _mm_symbol(
    symbol: str = "SPY",
    grade: str = "A",
    bias: str = "BULL",
    structure: str = "UPTREND",
    setup_state: str | None = None,
    trade_framing: dict | None = None,
    invalidation: list | None = None,
    reason_for_grade: str | None = None,
) -> dict:
    return {
        "symbol":               symbol,
        "grade":                grade,
        "bias":                 bias,
        "structure":            structure,
        "setup_state":          setup_state,
        "confidence":           "MEDIUM",
        "watch_zones":          [],
        "fib_levels":           None,
        "what_to_look_for":     [],
        "invalidation":         invalidation if invalidation is not None else [],
        "preferred_trade_structure": None,
        "reason_for_grade":     reason_for_grade,
        "trade_framing":        trade_framing if trade_framing is not None else {},
        "asset_group":          "EQUITY",
    }


def _market_map(symbols: dict | None = None) -> dict:
    s = symbols or {}
    return {
        "schema_version":   "market_map.v1",
        "generated_at":     "2026-04-28T12:00:00Z",
        "primary_symbols":  list(s.keys()),
        "symbols":          s,
    }


def _trade(symbol: str = "SPY", direction: str = "LONG") -> dict:
    return {"symbol": symbol, "direction": direction, "strategy_tag": "BULL_CALL_SPREAD", "entry_mode": "LIMIT"}


def _trade_decision(
    symbol: str = "SPY",
    direction: str = "LONG",
    strategy_tag: str = "BULL_CALL_SPREAD",
    entry_mode: str = "DIRECT",
    decision_status: str = "ALLOW_TRADE",
    block_reason: str | None = None,
    trace_stage: str = "CHAIN_VALIDATION",
    trace_source: str = "chain_validation",
    trace_reason: str = "passed",
) -> dict:
    return {
        "symbol":         symbol,
        "direction":      direction,
        "strategy_tag":   strategy_tag,
        "entry_mode":     entry_mode,
        "decision_status": decision_status,
        "block_reason":   block_reason,
        "decision_trace": {"stage": trace_stage, "source": trace_source, "reason": trace_reason},
    }


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

def test_reads_required_files(tmp_path: Path) -> None:
    payload_file = tmp_path / "latest_payload.json"
    run_file     = tmp_path / "latest_run.json"
    out_file     = tmp_path / "dashboard.html"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")
    main(payload_path=payload_file, run_path=run_file, output_path=out_file, logs_dir=tmp_path)
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "<html" in content
    assert "dashboard-header" in content


def test_missing_payload_fails(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="missing"):
        main(
            payload_path=tmp_path / "no_payload.json",
            run_path=tmp_path / "run.json",
            output_path=tmp_path / "out.html",
            logs_dir=tmp_path,
        )


def test_missing_run_fails(tmp_path: Path) -> None:
    payload_file = tmp_path / "latest_payload.json"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    with pytest.raises(RuntimeError, match="missing"):
        main(
            payload_path=payload_file,
            run_path=tmp_path / "no_run.json",
            output_path=tmp_path / "out.html",
            logs_dir=tmp_path,
        )


def test_invalid_json_fails(tmp_path: Path) -> None:
    bad      = tmp_path / "bad.json"
    run_file = tmp_path / "run.json"
    bad.write_text("{not valid json", encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid JSON"):
        main(payload_path=bad, run_path=run_file, output_path=tmp_path / "out.html", logs_dir=tmp_path)


def test_load_json_optional_returns_none_when_absent(tmp_path: Path) -> None:
    assert _load_json_optional(tmp_path / "missing.json") is None


def test_load_json_optional_raises_on_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid JSON"):
        _load_json_optional(bad)


def test_load_json_optional_returns_dict_when_valid(tmp_path: Path) -> None:
    f = tmp_path / "ok.json"
    f.write_text('{"key": "val"}', encoding="utf-8")
    result = _load_json_optional(f)
    assert result == {"key": "val"}


# ---------------------------------------------------------------------------
# Field mapping
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

    assert "2026-01-15T09:30:00Z" in html
    assert "HALT" in html
    assert "CHAOTIC" in html
    assert "STAY_FLAT" in html
    assert "0.625" in html
    assert "VIX_SPIKE_HALT" in html
    assert "YES" in html                    # system_halted=True
    assert "quota_exceeded_unique" in html  # errors[0]


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


def test_deterministic_output() -> None:
    p = _payload()
    r = _run()
    assert render_dashboard_html(p, r) == render_dashboard_html(p, r)


def test_no_mutation() -> None:
    p = _payload(top_trades=[_trade("NVDA")])
    r = _run(errors=["some_error"])
    p_before = copy.deepcopy(p)
    r_before = copy.deepcopy(r)
    render_dashboard_html(p, r)
    assert p == p_before
    assert r == r_before


# ---------------------------------------------------------------------------
# R9 — removed block IDs absent
# ---------------------------------------------------------------------------

def test_removed_block_ids_absent() -> None:
    html = render_dashboard_html(
        _payload(top_trades=[_trade()], trade_decision_detail=[_trade_decision()]),
        _run(),
    )
    assert 'id="decision-summary"'  not in html
    assert 'id="primary-setup"'     not in html
    assert 'id="secondary-setups"'  not in html
    assert 'id="trade-decisions"'   not in html


def test_preserved_block_ids_present() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run(), history_runs=[_run()])
    assert 'id="dashboard-header"' in html
    assert 'id="run-health"'       in html
    assert 'id="run-delta"'        in html
    assert 'id="run-history"'      in html


# ---------------------------------------------------------------------------
# R1 — Macro Tape
# ---------------------------------------------------------------------------

def test_macro_tape_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'id="macro-tape"' in html


def test_macro_tape_section_order() -> None:
    html = render_dashboard_html(_payload(), _run())
    header_pos = html.index('id="dashboard-header"')
    macro_pos  = html.index('id="macro-tape"')
    system_pos = html.index('id="system-state"')
    assert header_pos < macro_pos < system_pos


def test_macro_tape_empty_macro_drivers() -> None:
    # macro_drivers={} → slots 1-4 render with em dash, no crash
    html = render_dashboard_html(_payload(), _run())
    tape = html.split('id="macro-tape"', 1)[1]
    for label in ("VIX", "DXY", "10Y", "BTC", "SPY", "QQQ", "GLD", "SLV", "XLE"):
        assert label in tape


def test_macro_tape_arrows() -> None:
    p = _payload(macro_drivers=_macro_drivers(vix=0.05, dxy=-0.01, tnx=0.0, btc=0.03))
    html = render_dashboard_html(p, _run())
    tape = html.split('id="macro-tape"', 1)[1]
    assert "VIX ↑" in tape
    assert "DXY ↓" in tape
    assert "10Y →" in tape
    assert "BTC ↑" in tape


def test_macro_tape_no_crash_when_market_map_none() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=None)
    assert 'id="macro-tape"' in html


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
    assert 'class="macro-bias"' in html


# ---------------------------------------------------------------------------
# R2 / R2.1 — System State Block
# ---------------------------------------------------------------------------

def test_system_state_block_fields() -> None:
    html = render_dashboard_html(_payload(market_regime="RISK_ON"), _run(posture="CONTROLLED_LONG", confidence=0.75))
    state = html.split('id="system-state"', 1)[1]
    assert "RISK_ON" in state
    assert "CONTROLLED_LONG" in state
    assert "0.75" in state
    assert 'class="action-line"' in state


def test_system_state_regime_badge_class() -> None:
    html = render_dashboard_html(_payload(market_regime="RISK_OFF"), _run())
    assert 'class="badge RISK_OFF"' in html


def test_system_state_posture_badge_class() -> None:
    html = render_dashboard_html(_payload(), _run(posture="STAY_FLAT"))
    assert 'class="badge STAY_FLAT"' in html


def test_system_state_permission_omitted_when_none() -> None:
    r = _run(permission=None)
    html = render_dashboard_html(_payload(), r)
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Permission" not in state


def test_system_state_stay_flat_omitted_when_none() -> None:
    html = render_dashboard_html(_payload(validation_halt_detail=None), _run())
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Stay Flat" not in state


def test_system_state_stay_flat_present_when_set() -> None:
    html = render_dashboard_html(
        _payload(validation_halt_detail={"reason": "STAY_FLAT posture"}), _run()
    )
    assert "STAY_FLAT posture" in html


def test_action_line_stay_flat() -> None:
    r = _run(outcome="STAY_FLAT")
    html = render_dashboard_html(_payload(), r)
    assert "ACTION: WAIT" in html
    assert "NO VALID SETUPS" in html


def test_action_line_blocked() -> None:
    r = _run(permission=False)
    html = render_dashboard_html(_payload(), r)
    assert "ACTION: WATCH" in html
    assert "SETUPS PRESENT BUT BLOCKED" in html


def test_action_line_active() -> None:
    r = _run(permission=True)
    html = render_dashboard_html(_payload(), r)
    assert "ACTION: ACTIVE" in html
    assert "TRADE CONDITIONS MET" in html


def test_action_line_monitor_default() -> None:
    r = _run(outcome="NO_TRADE", permission=None)
    html = render_dashboard_html(_payload(), r)
    assert "ACTION: MONITOR" in html
    assert "SYSTEM ACTIVE" in html


def test_action_line_is_first_in_system_state() -> None:
    html = render_dashboard_html(_payload(), _run())
    state_start = html.index('id="system-state"')
    action_pos  = html.index('class="action-line"')
    regime_pos  = html.index('class="badge ')
    assert state_start < action_pos < regime_pos


# ---------------------------------------------------------------------------
# R3 — Candidate Visibility Board
# ---------------------------------------------------------------------------

def test_candidate_board_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'id="candidate-board"' in html


def test_candidate_board_market_map_absent() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=None)
    assert 'id="candidate-board"' in html
    assert "MARKET MAP UNAVAILABLE" in html


def test_candidate_board_empty_symbols() -> None:
    mm   = _market_map({})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="candidate-board"' in html
    assert "NO SYMBOL DATA" in html


def test_candidate_board_sort_order() -> None:
    syms = {
        "XLE": _mm_symbol("XLE", grade="C"),
        "GLD": _mm_symbol("GLD", grade="A"),
        "SPY": _mm_symbol("SPY", grade="A+"),
        "SLV": _mm_symbol("SLV", grade="B"),
        "QQQ": _mm_symbol("QQQ", grade="A"),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    # A+(SPY) < A(GLD) < A(QQQ) < B(SLV) < C(XLE) — GLD before QQQ alphabetically
    assert html.index('id="card-SPY"') < html.index('id="card-GLD"')
    assert html.index('id="card-GLD"') < html.index('id="card-QQQ"')
    assert html.index('id="card-QQQ"') < html.index('id="card-SLV"')
    assert html.index('id="card-SLV"') < html.index('id="card-XLE"')


def test_candidate_board_all_symbols_rendered() -> None:
    syms = {s: _mm_symbol(s, grade="B") for s in ("SPY", "QQQ", "GLD")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    for sym in ("SPY", "QQQ", "GLD"):
        assert f'id="card-{sym}"' in html


# ---------------------------------------------------------------------------
# R3.1 — Tier Grouping
# ---------------------------------------------------------------------------

def test_tier_grouping_order() -> None:
    syms = {
        "QQQ": _mm_symbol("QQQ", grade="A+"),
        "SPY": _mm_symbol("SPY", grade="B"),
        "GLD": _mm_symbol("GLD", grade="D"),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert html.index('id="tier-aplus"') < html.index('id="tier-b"') < html.index('id="tier-df"')


def test_tier_empty_group_absent() -> None:
    syms = {"SPY": _mm_symbol("SPY", grade="A+")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="tier-aplus"' in html
    assert 'id="tier-a"'     not in html
    assert 'id="tier-b"'     not in html
    assert 'id="tier-c"'     not in html
    assert 'id="tier-df"'    not in html


def test_tier_df_contains_d_and_f() -> None:
    syms = {
        "GLD": _mm_symbol("GLD", grade="D"),
        "SLV": _mm_symbol("SLV", grade="F"),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="tier-df"' in html
    tier = html.split('id="tier-df"', 1)[1]
    assert 'id="card-GLD"' in tier
    assert 'id="card-SLV"' in tier


def test_tier_header_labels() -> None:
    syms = {
        "SPY": _mm_symbol("SPY", grade="A+"),
        "QQQ": _mm_symbol("QQQ", grade="A"),
        "GLD": _mm_symbol("GLD", grade="B"),
        "SLV": _mm_symbol("SLV", grade="C"),
        "XLE": _mm_symbol("XLE", grade="D"),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "A+ — ACTIONABLE"  in html
    assert "A — HIGH QUALITY" in html
    assert "B — DEVELOPING"   in html
    assert "C — EARLY"        in html
    assert "D/F — FAILING"    in html


# ---------------------------------------------------------------------------
# R4 — Candidate Card Fields
# ---------------------------------------------------------------------------

def test_card_always_rendered_fields() -> None:
    syms = {"SPY": _mm_symbol("SPY", grade="C", bias="BEAR", structure="DOWNTREND")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = html.split('id="card-SPY"', 1)[1]
    assert "SPY"       in card
    assert "C"         in card
    assert "BEAR"      in card
    assert "DOWNTREND" in card


def test_card_grade_css_class() -> None:
    for grade, css in (("A+", "grade-aplus"), ("A", "grade-a"), ("B", "grade-b"),
                       ("C", "grade-c"), ("D", "grade-d"), ("F", "grade-f")):
        syms = {"SPY": _mm_symbol("SPY", grade=grade)}
        mm   = _market_map(syms)
        html = render_dashboard_html(_payload(), _run(), market_map=mm)
        assert css in html, f"CSS class {css} not found for grade {grade}"


def test_card_id_present() -> None:
    syms = {"NVDA": _mm_symbol("NVDA", grade="A")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="card-NVDA"' in html


def test_low_grade_card_fields_excluded() -> None:
    syms = {
        "GLD": _mm_symbol(
            "GLD",
            grade="C",
            setup_state="RANGE_BOUND",
            trade_framing={
                "direction": "NEUTRAL",
                "if_now": "WAIT_UNIQUE",
                "entry": "above 220_UNIQUE",
                "downgrade": "break below 210_UNIQUE",
            },
            invalidation=["below 200_UNIQUE"],
            reason_for_grade="low quality setup_UNIQUE",
        ),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    card = html.split('id="card-GLD"', 1)[1]
    assert "WAIT_UNIQUE"             not in card
    assert "above 220_UNIQUE"        not in card
    assert "below 200_UNIQUE"        not in card
    assert "break below 210_UNIQUE"  not in card
    assert "low quality setup_UNIQUE" not in card


def test_high_grade_card_shows_optional_fields() -> None:
    syms = {
        "SPY": _mm_symbol(
            "SPY",
            grade="A+",
            setup_state="BREAKOUT",
            trade_framing={"direction": "LONG", "if_now": "BUY_UNIQUE", "entry": "above 510_UNIQUE"},
            invalidation=["below 490_UNIQUE"],
            reason_for_grade="strong trend_UNIQUE",
        ),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "BUY_UNIQUE"          in html
    assert "above 510_UNIQUE"    in html
    assert "below 490_UNIQUE"    in html
    assert "strong trend_UNIQUE" in html


# ---------------------------------------------------------------------------
# R4.1 — Candidate State Emphasis
# ---------------------------------------------------------------------------

def test_candidate_state_label() -> None:
    syms = {"SPY": _mm_symbol("SPY", grade="A+", setup_state="BREAKOUT")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'class="candidate-state"' in html
    assert "STATE: BREAKOUT"          in html


def test_candidate_state_not_in_low_grade() -> None:
    syms = {"GLD": _mm_symbol("GLD", grade="C", setup_state="BREAKOUT")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'class="candidate-state"' not in html


def test_candidate_state_excluded_for_data_unavailable() -> None:
    syms = {"GLD": _mm_symbol("GLD", grade="A", setup_state="DATA_UNAVAILABLE")}
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert "STATE: DATA_UNAVAILABLE" not in html


def test_candidate_risk_label() -> None:
    syms = {
        "SPY": _mm_symbol(
            "SPY",
            grade="A",
            trade_framing={"direction": "LONG", "downgrade": "break below 500_UNIQUE"},
        ),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'class="candidate-risk"'       in html
    assert "RISK: break below 500_UNIQUE" in html
    assert "WATCH FOR"                    not in html


def test_candidate_risk_not_in_low_grade() -> None:
    syms = {
        "GLD": _mm_symbol(
            "GLD",
            grade="D",
            trade_framing={"direction": "SHORT", "downgrade": "break above 200"},
        ),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'class="candidate-risk"' not in html


def test_candidate_state_before_risk() -> None:
    syms = {
        "SPY": _mm_symbol(
            "SPY",
            grade="A+",
            setup_state="BREAKOUT",
            trade_framing={"direction": "LONG", "downgrade": "break below 500"},
        ),
    }
    mm   = _market_map(syms)
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    state_pos = html.index('class="candidate-state"')
    risk_pos  = html.index('class="candidate-risk"')
    assert state_pos < risk_pos


# ---------------------------------------------------------------------------
# R6 — _GRADE_ORDER constant
# ---------------------------------------------------------------------------

def test_grade_order_constant_correct() -> None:
    assert _GRADE_ORDER["A+"] == 0
    assert _GRADE_ORDER["A"]  == 1
    assert _GRADE_ORDER["B"]  == 2
    assert _GRADE_ORDER["C"]  == 3
    assert _GRADE_ORDER["D"]  == 4
    assert _GRADE_ORDER["F"]  == 5


def test_sort_deterministic() -> None:
    syms = {s: _mm_symbol(s, grade="B") for s in ("ZZZ", "AAA", "MMM")}
    mm   = _market_map(syms)
    html1 = render_dashboard_html(_payload(), _run(), market_map=mm)
    html2 = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert html1 == html2
    # alphabetical within same grade: AAA < MMM < ZZZ
    assert html1.index('id="card-AAA"') < html1.index('id="card-MMM"') < html1.index('id="card-ZZZ"')


# ---------------------------------------------------------------------------
# R7 — market_map optional
# ---------------------------------------------------------------------------

def test_render_accepts_market_map_none() -> None:
    html = render_dashboard_html(_payload(), _run(), market_map=None)
    assert "MARKET MAP UNAVAILABLE" in html


def test_render_accepts_market_map_dict() -> None:
    mm   = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    html = render_dashboard_html(_payload(), _run(), market_map=mm)
    assert 'id="card-SPY"' in html


# ---------------------------------------------------------------------------
# PRD-041 — run delta (preserved)
# ---------------------------------------------------------------------------

def test_run_delta_present_with_previous_run() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=_run(posture="STAY_FLAT"))
    assert 'id="run-delta"' in html


def test_run_delta_hidden_without_previous_run() -> None:
    html = render_dashboard_html(_payload(), _run(), previous_run=None)
    assert 'id="run-delta"' not in html


def test_run_delta_detects_changes() -> None:
    current  = _run(regime="NEUTRAL",  posture="CONTROLLED_LONG", confidence=0.75, system_halted=False)
    previous = _run(regime="RISK_OFF", posture="STAY_FLAT",        confidence=0.25, system_halted=True)
    html     = render_dashboard_html(_payload(), current, previous_run=previous)
    delta    = html.split('id="run-delta"', 1)[1]
    delta    = delta.split('id="system-state"', 1)[0]

    assert "Regime: RISK_OFF -&gt; NEUTRAL"            in delta
    assert "Posture: STAY_FLAT -&gt; CONTROLLED_LONG"  in delta
    assert "Confidence: 0.25 -&gt; 0.75"               in delta
    assert "System Halted: YES -&gt; NO"               in delta


def test_run_delta_ignores_unchanged_fields() -> None:
    html  = render_dashboard_html(_payload(), _run(), previous_run=_run())
    delta = html.split('id="run-delta"', 1)[1]
    delta = delta.split('id="system-state"', 1)[0]

    assert "No changes since last run" in delta
    assert "Regime:"         not in delta
    assert "Posture:"        not in delta
    assert "Confidence:"     not in delta
    assert "System Halted:"  not in delta


def test_run_delta_correct_previous_selection_by_timestamp(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    oldest          = _run(status="OLD",  confidence=0.1)
    oldest["timestamp"] = "2026-04-28T10:00:00Z"
    newest          = _run(status="NEW",  confidence=0.2)
    newest["timestamp"] = "2026-04-28T12:00:00Z"
    previous        = _run(status="PREV", confidence=0.3)
    previous["timestamp"] = "2026-04-28T11:00:00Z"

    (logs_dir / "run_oldest.json").write_text(json.dumps(oldest),   encoding="utf-8")
    (logs_dir / "run_newest.json").write_text(json.dumps(newest),   encoding="utf-8")
    (logs_dir / "run_previous.json").write_text(json.dumps(previous), encoding="utf-8")

    assert _resolve_previous_run(logs_dir) == previous


def test_run_delta_no_unapproved_fields() -> None:
    previous = _run(status="HALT", kill_switch=True, data_status="stale")
    html     = render_dashboard_html(_payload(), _run(), previous_run=previous)
    delta    = html.split('id="run-delta"', 1)[1]
    delta    = delta.split('id="system-state"', 1)[0]

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
    payload  = _payload()
    current  = _run(regime="NEUTRAL", posture="STAY_FLAT", confidence=0.0)
    previous = _run(regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.75)
    assert render_dashboard_html(payload, current, previous_run=previous) == render_dashboard_html(
        payload, current, previous_run=previous
    )


# ---------------------------------------------------------------------------
# PRD-042 — run history (preserved)
# ---------------------------------------------------------------------------

def test_run_history_present() -> None:
    html = render_dashboard_html(_payload(), _run(), history_runs=[_run()])
    assert 'id="run-history"' in html


def test_run_history_limit_enforced(tmp_path: Path) -> None:
    logs_dir     = tmp_path / "logs"
    logs_dir.mkdir()
    payload_file = tmp_path / "latest_payload.json"
    run_file     = tmp_path / "latest_run.json"
    out_file     = tmp_path / "dashboard.html"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")

    for i in range(HISTORY_LIMIT + 2):
        history_run = _run(regime=f"RISK_{i}", posture=f"POSTURE_{i}", confidence=float(i))
        history_run["timestamp"] = f"2026-04-28T12:{i:02d}:00Z"
        (logs_dir / f"run_{i}.json").write_text(json.dumps(history_run), encoding="utf-8")

    main(payload_path=payload_file, run_path=run_file, output_path=out_file, logs_dir=logs_dir)
    history = out_file.read_text(encoding="utf-8").split('id="run-history"', 1)[1]
    rows = [line for line in history.splitlines() if " | " in line][1:]
    assert len(rows) == HISTORY_LIMIT


def test_run_history_sorted_descending(tmp_path: Path) -> None:
    logs_dir     = tmp_path / "logs"
    logs_dir.mkdir()
    payload_file = tmp_path / "latest_payload.json"
    run_file     = tmp_path / "latest_run.json"
    out_file     = tmp_path / "dashboard.html"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")

    older                  = _run(regime="OLDER");  older["timestamp"]  = "2026-04-28T10:00:00Z"
    newest                 = _run(regime="NEWEST"); newest["timestamp"] = "2026-04-28T12:00:00Z"
    middle                 = _run(regime="MIDDLE"); middle["timestamp"] = "2026-04-28T11:00:00Z"

    (logs_dir / "run_older.json").write_text(json.dumps(older),   encoding="utf-8")
    (logs_dir / "run_newest.json").write_text(json.dumps(newest), encoding="utf-8")
    (logs_dir / "run_middle.json").write_text(json.dumps(middle), encoding="utf-8")

    main(payload_path=payload_file, run_path=run_file, output_path=out_file, logs_dir=logs_dir)
    history = out_file.read_text(encoding="utf-8").split('id="run-history"', 1)[1]
    assert history.index("12:00 | NEWEST") < history.index("11:00 | MIDDLE") < history.index("10:00 | OLDER")


def test_run_history_field_mapping_exact() -> None:
    history_run = _run(regime="RISK_OFF", posture="STAY_FLAT", confidence=0.25)
    history_run["timestamp"] = "2026-04-28T12:50:00Z"
    html    = render_dashboard_html(_payload(), _run(), history_runs=[history_run])
    history = html.split('id="run-history"', 1)[1]
    assert "12:50 | RISK_OFF | STAY_FLAT | 0.25" in history


def test_run_history_timestamp_format() -> None:
    history_run = _run()
    history_run["timestamp"] = "2026-04-28T09:30:45Z"
    html    = render_dashboard_html(_payload(), _run(), history_runs=[history_run])
    history = html.split('id="run-history"', 1)[1]
    assert "09:30 |" in history
    assert "2026-04-28T09:30:45Z" not in history


def test_run_history_no_extra_fields() -> None:
    history_run = _run(status="FAIL", system_halted=True, kill_switch=True, data_status="stale")
    html    = render_dashboard_html(_payload(), _run(), history_runs=[history_run])
    history = html.split('id="run-history"', 1)[1].lower()
    for field in ("status", "system_halted", "kill_switch", "data_status", "outcome", "run_id"):
        assert field not in history


def test_run_history_deterministic_output() -> None:
    payload      = _payload()
    run          = _run()
    history_runs = [
        _run(regime="RISK_OFF", posture="STAY_FLAT",        confidence=0.25),
        _run(regime="NEUTRAL",  posture="CONTROLLED_LONG",  confidence=0.75),
    ]
    history_runs[0]["timestamp"] = "2026-04-28T12:50:00Z"
    history_runs[1]["timestamp"] = "2026-04-28T11:45:00Z"
    assert render_dashboard_html(payload, run, history_runs=history_runs) == render_dashboard_html(
        payload, run, history_runs=history_runs
    )


# ---------------------------------------------------------------------------
# Run health (preserved)
# ---------------------------------------------------------------------------

def test_run_health_present() -> None:
    html = render_dashboard_html(_payload(), _run())
    assert 'id="run-health"' in html


def test_run_health_fields() -> None:
    html = render_dashboard_html(_payload(), _run(system_halted=True, kill_switch=False, errors=["err_unique"]))
    health = html.split('id="run-health"', 1)[1]
    assert "YES"        in health   # system_halted
    assert "err_unique" in health


def test_run_health_no_error_when_empty() -> None:
    html = render_dashboard_html(_payload(), _run(errors=[]))
    health = html.split('id="run-health"', 1)[1]
    assert ">Error<" not in health
