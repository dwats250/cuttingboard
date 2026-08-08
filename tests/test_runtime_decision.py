from __future__ import annotations

import json
from dataclasses import replace as _dc_replace
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from cuttingboard import audit, output, runtime
from cuttingboard import validation as validation_mod
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.chain_validation import ChainValidationResult, MANUAL_CHECK
from cuttingboard.options import (
    OPTIONS_SIZING,
    SMALLEST_CONTRACT_EXCEEDS_BUDGET,
    OptionRefusal,
    OptionSetup,
)
from cuttingboard.delivery.payload import build_report_payload
from cuttingboard.delivery.transport import deliver_cli
from cuttingboard.delivery.dashboard_renderer import render_dashboard_html
from cuttingboard.output import build_notification_message, render_report_from_payload
from cuttingboard.reports.postmarket import build_postmarket_report as _real_postmarket
from cuttingboard.reports.premarket import build_premarket_report as _real_premarket
from cuttingboard.qualification import QualificationResult, QualificationSummary, TradeCandidate
from cuttingboard.regime import AGGRESSIVE_LONG, RISK_ON, RegimeState
from cuttingboard.structure import StructureResult
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE
from cuttingboard.validation import HaltCause, ValidationSummary
from cuttingboard.watch import WatchSummary


RUN_AT = datetime(2026, 4, 28, 13, 0, tzinfo=timezone.utc)
EOD_RUN_AT = datetime(2026, 4, 28, 19, 45, tzinfo=timezone.utc)


def _regime() -> RegimeState:
    return RegimeState(
        regime=RISK_ON,
        posture=AGGRESSIVE_LONG,
        confidence=0.8,
        net_score=5,
        risk_on_votes=5,
        risk_off_votes=0,
        neutral_votes=3,
        total_votes=8,
        vote_breakdown={},
        vix_level=16.0,
        vix_pct_change=-0.03,
        computed_at_utc=RUN_AT,
    )


def _validation_summary() -> ValidationSummary:
    return ValidationSummary(
        system_halted=False,
        halt_reason=None,
        failed_halt_symbols=[],
        results={},
        valid_quotes={},
        invalid_symbols={},
        symbols_attempted=0,
        symbols_validated=0,
        symbols_failed=0,
    )


def _qualification_summary(symbol: str = "SPY") -> QualificationSummary:
    return QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[
            QualificationResult(
                symbol=symbol,
                qualified=True,
                watchlist=False,
                direction="LONG",
                gates_passed=["REGIME"],
                gates_failed=[],
                hard_failure=None,
                watchlist_reason=None,
                max_contracts=2,
                dollar_risk=150.0,
            )
        ],
        watchlist=[],
        excluded={},
        symbols_evaluated=1,
        symbols_qualified=1,
        symbols_watchlist=0,
        symbols_excluded=0,
    )


def _option_setup(symbol: str = "SPY") -> OptionSetup:
    return OptionSetup(
        symbol=symbol,
        strategy="BULL_CALL_SPREAD",
        direction="LONG",
        structure="TREND",
        iv_environment="NORMAL_IV",
        long_strike="1_ITM",
        short_strike="ATM",
        strike_distance=5.0,
        spread_width=0.75,
        dte=21,
        max_contracts=2,
        dollar_risk=150.0,
        exit_profit_pct=0.5,
        exit_loss="full_debit",
    )


def _candidate(symbol: str = "SPY") -> TradeCandidate:
    return TradeCandidate(
        symbol=symbol,
        direction="LONG",
        entry_price=100.0,
        stop_price=97.0,
        target_price=106.0,
        spread_width=0.75,
    )


def _setup_runtime_mocks(monkeypatch, tmp_path, symbol: str = "SPY"):
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(runtime, "LATEST_RUN_PATH", tmp_path / "logs" / "latest_run.json")
    monkeypatch.setattr(runtime, "LATEST_CONTRACT_PATH", str(tmp_path / "logs" / "latest_contract.json"))
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", str(tmp_path / "logs" / "audit.jsonl"))
    monkeypatch.setattr(runtime, "_deterministic_run_at", lambda mode, fixture_file: RUN_AT)
    monkeypatch.setattr(runtime, "_load_inputs", lambda mode, fixture_file: ({}, {}))
    monkeypatch.setattr(runtime, "_fixture_validation_clock", _null_context())
    monkeypatch.setattr(runtime, "validate_quotes", lambda *args, **kwargs: _validation_summary())
    monkeypatch.setattr(runtime, "compute_regime", lambda quotes: _regime())
    monkeypatch.setattr(runtime, "compute_correlation", lambda quotes: type("Corr", (), {
        "gold_symbol": "GLD",
        "dollar_symbol": "DX-Y.NYB",
        "state": "ALIGNED",
        "score": 1,
        "risk_modifier": 1.0,
    })())
    monkeypatch.setattr(runtime, "evaluate_policy", lambda corr: type("Policy", (), {"risk_modifier": 1.0})())
    monkeypatch.setattr(runtime, "_fixture_cache_only_ohlcv", _null_context())
    monkeypatch.setattr(runtime, "compute_all_derived", lambda quotes: {symbol: object()})
    monkeypatch.setattr(runtime, "resolve_sector_router", lambda *args, **kwargs: runtime.SectorRouterState(
        mode="MIXED",
        energy_score=0.0,
        index_score=0.0,
        computed_at_utc=RUN_AT,
        session_date="2026-04-28",
    ))
    monkeypatch.setattr(runtime, "classify_all_structure", lambda *args, **kwargs: {
        symbol: StructureResult(
            symbol=symbol,
            structure="TREND",
            iv_environment="NORMAL_IV",
            is_tradeable=True,
            disqualification_reason=None,
        )
    })
    monkeypatch.setattr(runtime, "classify_watchlist", lambda *args, **kwargs: WatchSummary(
        session="PREMARKET",
        threshold=0.0,
        watchlist=[],
        ignored_symbols=[],
        execution_posture="ACTIVE",
    ))
    monkeypatch.setattr(runtime, "generate_candidates", lambda *args, **kwargs: {symbol: _candidate(symbol)})
    monkeypatch.setattr(runtime, "fetch_ohlcv", lambda symbol: None)
    monkeypatch.setattr(runtime, "qualify_all", lambda *args, **kwargs: _qualification_summary(symbol))
    monkeypatch.setattr(runtime, "_log_continuation_audit", lambda regime, summary: None)
    monkeypatch.setattr(runtime, "build_option_setups", lambda *args, **kwargs: [_option_setup(symbol)])
    monkeypatch.setattr(runtime, "render_report", lambda **kwargs: "report")
    monkeypatch.setattr(runtime, "_write_markdown_report", lambda report, date_str, sha: None)
    monkeypatch.setattr(runtime, "_load_run_history", lambda path: [])
    monkeypatch.setattr(runtime, "build_premarket_report", lambda contract: {})
    monkeypatch.setattr(runtime, "build_postmarket_report", lambda contract, history: {})
    monkeypatch.setattr(runtime, "run_post_trade_evaluation", lambda **kwargs: None)
    monkeypatch.setattr(runtime, "build_market_map", lambda **kwargs: {
        "symbols": {
            symbol: {
                "watch_zones": [
                    {"type": "VWAP", "level": 120.0, "context": "session vwap"},
                ]
            }
        }
    })


def _null_context():
    class _Ctx:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    return lambda *args, **kwargs: _Ctx()


def test_runtime_outcome_uses_trade_decision_status(monkeypatch, tmp_path):
    _setup_runtime_mocks(monkeypatch, tmp_path)
    # PRD-286: this fixture has no macro drivers, so real macro computation now
    # fails CLOSED (UNAVAILABLE -> block). This test is about outcome-status
    # derivation, not macro; supply a valid computed pressure to isolate it.
    monkeypatch.setattr(runtime, "_compute_overall_pressure", lambda quotes: "NEUTRAL")
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {
        "SPY": ChainValidationResult(
            symbol="SPY",
            classification=MANUAL_CHECK,
            reason="fixture mode skips live chain validation",
            spread_pct=None,
            open_interest=None,
            volume=None,
            expiry_used=None,
            data_source=None,
        )
    })
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *args, **kwargs: runtime.TradeDecision(
        ticker="SPY",
        direction="LONG",
        status=ALLOW_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=None,
    ))

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    assert result.outcome == runtime.OUTCOME_TRADE
    assert result.contract["trade_candidates"][0]["decision_status"] == ALLOW_TRADE


def test_runtime_outcome_excludes_non_tradable_allow(monkeypatch, tmp_path):
    # PRD-162 AC1: a NON_TRADABLE symbol (^VIX) that reaches an ALLOW_TRADE
    # decision is NOT actionable, so the runtime outcome is NO_TRADE — agreeing
    # with the gated (empty) payload top_trades. The candidate is still retained
    # on contract.trade_candidates.
    symbol = "^VIX"
    assert symbol in runtime.config.NON_TRADABLE_SYMBOLS
    _setup_runtime_mocks(monkeypatch, tmp_path, symbol=symbol)
    # PRD-286: isolate from the now-fail-closed macro seam (fixture has no macro
    # drivers); this test is about NON_TRADABLE exclusion, not macro pressure.
    monkeypatch.setattr(runtime, "_compute_overall_pressure", lambda quotes: "NEUTRAL")
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {
        symbol: ChainValidationResult(
            symbol=symbol,
            classification=MANUAL_CHECK,
            reason="fixture mode skips live chain validation",
            spread_pct=None,
            open_interest=None,
            volume=None,
            expiry_used=None,
            data_source=None,
        )
    })
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *args, **kwargs: runtime.TradeDecision(
        ticker=symbol,
        direction="LONG",
        status=ALLOW_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=None,
    ))

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    assert result.outcome == runtime.OUTCOME_NO_TRADE
    candidate = result.contract["trade_candidates"][0]
    assert candidate["symbol"] == symbol
    assert candidate["decision_status"] == ALLOW_TRADE


def test_runtime_materializes_blocked_decision(monkeypatch, tmp_path):
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {
        "SPY": ChainValidationResult(
            symbol="SPY",
            classification=MANUAL_CHECK,
            reason="fixture mode skips live chain validation",
            spread_pct=None,
            open_interest=None,
            volume=None,
            expiry_used=None,
            data_source=None,
        )
    })

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    candidate = result.contract["trade_candidates"][0]
    assert result.outcome == runtime.OUTCOME_NO_TRADE
    assert candidate["decision_status"] == BLOCK_TRADE
    assert candidate["block_reason"] == "fixture mode skips live chain validation"


def test_runtime_eod_attaches_overnight_policy(monkeypatch, tmp_path):
    _setup_runtime_mocks(monkeypatch, tmp_path)
    # PRD-286: isolate from the now-fail-closed macro seam (fixture has no macro
    # drivers); this test is about overnight-policy attachment, not macro pressure.
    monkeypatch.setattr(runtime, "_compute_overall_pressure", lambda quotes: "NEUTRAL")
    monkeypatch.setattr(runtime, "_deterministic_run_at", lambda mode, fixture_file: EOD_RUN_AT)
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {
        "SPY": ChainValidationResult(
            symbol="SPY",
            classification=MANUAL_CHECK,
            reason="fixture mode skips live chain validation",
            spread_pct=None,
            open_interest=None,
            volume=None,
            expiry_used=None,
            data_source=None,
        )
    })
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *args, **kwargs: runtime.TradeDecision(
        ticker="SPY",
        direction="LONG",
        status=ALLOW_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=None,
    ))

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    candidate = result.contract["trade_candidates"][0]
    assert candidate["overnight_policy"] == {"decision": "FORCE_EXIT", "reason": "SPREAD_FRAGILITY"}
    assert candidate["decision_status"] == ALLOW_TRADE
    assert candidate["policy_allowed"] is True


def test_runtime_non_eod_does_not_attach_overnight_policy(monkeypatch, tmp_path):
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {
        "SPY": ChainValidationResult(
            symbol="SPY",
            classification=MANUAL_CHECK,
            reason="fixture mode skips live chain validation",
            spread_pct=None,
            open_interest=None,
            volume=None,
            expiry_used=None,
            data_source=None,
        )
    })
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *args, **kwargs: runtime.TradeDecision(
        ticker="SPY",
        direction="LONG",
        status=ALLOW_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=None,
    ))

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    assert "overnight_policy" not in result.contract["trade_candidates"][0]


# ---------------------------------------------------------------------------
# PRD-180: kill switch forces a real terminal HALT
# ---------------------------------------------------------------------------


def _nq(symbol: str, pct_change_decimal: float, price: float = 100.0) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=pct_change_decimal,
        volume=1_000_000.0,
        fetched_at_utc=datetime.now(timezone.utc),
        source="test",
        units="usd_price",
        age_seconds=0.0,
    )


def _market_quotes(spy_pct_change: float) -> dict[str, NormalizedQuote]:
    # SPY drives the kill switch; the four required macro-driver symbols keep the
    # contract's macro section buildable for a non-empty quote set.
    quotes = {
        "SPY": _nq("SPY", spy_pct_change),
        "^VIX": _nq("^VIX", 0.0, price=16.0),
        "DX-Y.NYB": _nq("DX-Y.NYB", 0.0),
        "^TNX": _nq("^TNX", 0.0, price=4.2),
        "BTC-USD": _nq("BTC-USD", 0.0, price=60000.0),
    }
    return quotes


def _setup_full_trade_mocks(monkeypatch, tmp_path, symbol: str = "SPY"):
    """Runtime mocks plus a full fixture trade path (chain + ALLOW_TRADE)."""
    _setup_runtime_mocks(monkeypatch, tmp_path, symbol=symbol)
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {
        symbol: ChainValidationResult(
            symbol=symbol,
            classification=MANUAL_CHECK,
            reason="fixture mode skips live chain validation",
            spread_pct=None,
            open_interest=None,
            volume=None,
            expiry_used=None,
            data_source=None,
        )
    })
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *args, **kwargs: runtime.TradeDecision(
        ticker=symbol,
        direction="LONG",
        status=ALLOW_TRADE,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=None,
    ))


def _run_kill_switch_case(
    monkeypatch,
    tmp_path,
    *,
    vix_level: float = 16.0,
    vix_pct_change: float = -0.03,
    spy_pct_change: float = 0.0,
):
    _setup_full_trade_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(
        runtime,
        "compute_regime",
        lambda quotes: _dc_replace(_regime(), vix_level=vix_level, vix_pct_change=vix_pct_change),
    )
    monkeypatch.setattr(
        runtime,
        "_load_inputs",
        lambda mode, fixture_file: ({}, _market_quotes(spy_pct_change)),
    )
    return runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )


# Boundary coverage: comparisons are strict ">", so the exact threshold must NOT
# halt, and anything just above must halt. One parametrization per threshold.
@pytest.mark.parametrize(
    ("kwargs", "expect_halt"),
    [
        ({"vix_level": 35.0}, False),
        ({"vix_level": 35.01}, True),
        ({"vix_pct_change": 0.15}, False),
        ({"vix_pct_change": 0.16}, True),
        ({"spy_pct_change": 0.03}, False),
        ({"spy_pct_change": 0.0301}, True),
        ({"spy_pct_change": -0.03}, False),
        ({"spy_pct_change": -0.0301}, True),
    ],
)
def test_kill_switch_threshold_boundaries(monkeypatch, tmp_path, kwargs, expect_halt):
    result = _run_kill_switch_case(monkeypatch, tmp_path, **kwargs)
    assert (result.outcome == runtime.OUTCOME_HALT) is expect_halt
    assert result.summary["system_halted"] is expect_halt
    assert result.summary["kill_switch"] is expect_halt
    if not expect_halt:
        # exact-threshold run is a normal trade run, not a halt
        assert result.outcome == runtime.OUTCOME_TRADE


def test_kill_switch_trip_forces_full_halt_escalation(monkeypatch, tmp_path):
    # VIX well above the level threshold -> kill switch trips.
    result = _run_kill_switch_case(monkeypatch, tmp_path, vix_level=42.0)
    summary = result.summary

    # R1: recorded outcome is a terminal HALT, not a zeroed NO_TRADE.
    assert result.outcome == runtime.OUTCOME_HALT
    assert summary["outcome"] == runtime.OUTCOME_HALT
    assert summary["system_halted"] is True
    assert summary["status"] == "FAIL"
    assert summary["kill_switch"] is True
    assert summary["candidates_qualified"] == 0

    # halt_reason reads as a market-stress halt, not a data/validation failure.
    assert summary["halt_reason"] == runtime.KILL_SWITCH_HALT_REASON
    assert "kill switch" in summary["halt_reason"].lower()
    assert "valid" not in summary["halt_reason"].lower()

    # R5: trade content suppressed; the alert is a STAY FLAT, not a trade alert.
    assert result.contract["outcome"] == runtime.OUTCOME_HALT
    assert result.contract["trade_candidates"] == []
    title, body = runtime.build_notification_message(result.contract)
    assert "STAY FLAT" in title
    assert "No trade." in body

    # The produced summary satisfies verify_run_summary's HALT invariants.
    summary_path = tmp_path / "kill_switch_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert runtime.verify_run_summary(str(summary_path))["pass"] is True


def test_validation_halt_unchanged_when_kill_switch_not_tripped(monkeypatch, tmp_path):
    # R2: a validation-driven HALT with the kill switch NOT tripped is unchanged.
    _setup_full_trade_mocks(monkeypatch, tmp_path)
    halted = _dc_replace(
        _validation_summary(),
        system_halted=True,
        halt_reason="HALT_SYMBOL ^VIX failed validation",
        halt_cause=HaltCause.VALIDATION,
    )
    monkeypatch.setattr(runtime, "validate_quotes", lambda *args, **kwargs: halted)
    # benign inputs so the kill switch cannot trip independently
    monkeypatch.setattr(runtime, "_load_inputs", lambda mode, fixture_file: ({}, {}))

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )
    summary = result.summary

    assert result.outcome == runtime.OUTCOME_HALT
    assert summary["system_halted"] is True
    assert summary["kill_switch"] is False
    # the validation halt_reason is preserved, NOT overwritten by the kill switch.
    assert summary["halt_reason"] == "HALT_SYMBOL ^VIX failed validation"
    assert summary["halt_reason"] != runtime.KILL_SWITCH_HALT_REASON
    # cause stays VALIDATION; the market-stress arm is not engaged.
    assert result.validation_summary.halt_cause == HaltCause.VALIDATION

    summary_path = tmp_path / "validation_halt_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert runtime.verify_run_summary(str(summary_path))["pass"] is True

    # Notification regression: a validation HALT still produces a STAY FLAT alert
    # with no trade content (unchanged by PRD-180).
    title, body = runtime.build_notification_message(result.contract)
    assert "STAY FLAT" in title
    assert "No trade." in body


@pytest.mark.parametrize(
    ("kwargs", "expect_trip"),
    [
        ({"vix_level": 35.0}, False),
        ({"vix_level": 35.01}, True),
        ({"vix_pct_change": 0.15}, False),
        ({"vix_pct_change": 0.16}, True),
        ({"spy_pct_change": 0.03}, False),
        ({"spy_pct_change": -0.0301}, True),
    ],
)
def test_kill_switch_predicate_strict_greater_than(kwargs, expect_trip):
    # Unit-level boundary on the pure predicate (independent of the pipeline).
    regime = _dc_replace(
        _regime(),
        vix_level=kwargs.get("vix_level", 16.0),
        vix_pct_change=kwargs.get("vix_pct_change", -0.03),
    )
    quotes = {"SPY": _nq("SPY", kwargs.get("spy_pct_change", 0.0))}
    assert runtime._kill_switch(regime, quotes) is expect_trip


# ---------------------------------------------------------------------------
# PRD-180 (round 2): explicit halt cause + cause-labeled report banner
# ---------------------------------------------------------------------------


def _render_halt_report(halt_cause, halt_reason):
    vs = _dc_replace(
        _validation_summary(),
        system_halted=True,
        halt_reason=halt_reason,
        halt_cause=halt_cause,
    )
    return output.render_report(
        date_str="2026-04-28",
        run_at_utc=RUN_AT,
        regime=None,
        validation_summary=vs,
        qualification_summary=None,
        option_setups=[],
        outcome=runtime.OUTCOME_HALT,
        halt_reason=halt_reason,
        chain_results={},
    )


def test_render_report_market_stress_banner():
    # The defect this PRD round fixes: a market-stress HALT must NOT render as a
    # data/validation failure.
    report = _render_halt_report(HaltCause.MARKET_STRESS, runtime.KILL_SWITCH_HALT_REASON)
    assert "MARKET STRESS" in report
    assert "MACRO DATA INVALID" not in report
    assert runtime.KILL_SWITCH_HALT_REASON in report


def test_render_report_validation_halt_banner_unchanged():
    # Regression on the untouched path: a validation HALT still reads as before.
    report = _render_halt_report(HaltCause.VALIDATION, "Failed: ^VIX (stale)")
    assert "MACRO DATA INVALID" in report
    assert "MARKET STRESS" not in report


def test_kill_switch_trip_sets_market_stress_cause(monkeypatch, tmp_path):
    # Positive-ID: the real kill-switch trip stamps the structured cause.
    result = _run_kill_switch_case(monkeypatch, tmp_path, vix_level=42.0)
    assert result.validation_summary.halt_cause == HaltCause.MARKET_STRESS


def test_validation_path_sets_validation_cause():
    # Positive-ID: the real validation halt path stamps VALIDATION (empty quote
    # set fails every HALT_SYMBOL).
    vs = validation_mod.validate_quotes({}, None)
    assert vs.system_halted is True
    assert vs.halt_cause == HaltCause.VALIDATION


def test_kill_switch_trip_skips_pipeline(monkeypatch, tmp_path):
    # Mechanism (b): a trip must SKIP qualification/options/decision, not just
    # suppress their output.
    _setup_full_trade_mocks(monkeypatch, tmp_path)
    calls: list[str] = []
    monkeypatch.setattr(runtime, "generate_candidates", lambda *a, **k: (calls.append("generate"), {})[1])
    monkeypatch.setattr(runtime, "qualify_all", lambda *a, **k: calls.append("qualify"))
    monkeypatch.setattr(runtime, "build_option_setups", lambda *a, **k: (calls.append("options"), [])[1])
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *a, **k: calls.append("decision"))
    monkeypatch.setattr(
        runtime, "compute_regime", lambda quotes: _dc_replace(_regime(), vix_level=42.0)
    )
    monkeypatch.setattr(runtime, "_load_inputs", lambda mode, ff: ({}, _market_quotes(0.0)))

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    assert result.outcome == runtime.OUTCOME_HALT
    assert calls == []


def test_kill_switch_audit_record_carries_halt(monkeypatch, tmp_path):
    # The audit record reflects the HALT outcome and the market-stress reason.
    result = _run_kill_switch_case(monkeypatch, tmp_path, vix_level=42.0)
    assert result.audit_record["outcome"] == runtime.OUTCOME_HALT
    assert result.audit_record["halt_reason"] == runtime.KILL_SWITCH_HALT_REASON


# ---------------------------------------------------------------------------
# PRD-260: continuation decision geometry
# ---------------------------------------------------------------------------

def _manual_check_chain(symbol: str) -> ChainValidationResult:
    return ChainValidationResult(
        symbol=symbol,
        classification=MANUAL_CHECK,
        reason="fixture mode skips live chain validation",
        spread_pct=None,
        open_interest=None,
        volume=None,
        expiry_used=None,
        data_source=None,
    )


def _continuation_summary(symbol: str, promoted: TradeCandidate) -> QualificationSummary:
    return QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[
            QualificationResult(
                symbol=symbol,
                qualified=True,
                watchlist=False,
                direction="LONG",
                gates_passed=["VIX"],
                gates_failed=[],
                hard_failure=None,
                watchlist_reason=None,
                max_contracts=2,
                dollar_risk=150.0,
                entry_mode="CONTINUATION",
            )
        ],
        watchlist=[],
        excluded={},
        symbols_evaluated=1,
        symbols_qualified=1,
        symbols_watchlist=0,
        symbols_excluded=0,
        continuation_candidates={symbol: promoted},
    )


def test_continuation_decision_uses_promoted_geometry_prd260(monkeypatch, tmp_path):
    # PRD-260 R1 decision layer (red pre-change): the runtime merges the
    # promoted candidate over the direct one before decision assembly, so
    # the REAL create_trade_decision renders the gate's geometry — not the
    # rejected direct candidate's ATR stop (97.0 in this fixture).
    symbol = "SPY"
    _setup_runtime_mocks(monkeypatch, tmp_path, symbol=symbol)
    monkeypatch.setattr(
        runtime, "_fixture_chain_results",
        lambda setups: {symbol: _manual_check_chain(symbol)},
    )
    promoted = TradeCandidate(
        symbol=symbol, direction="LONG", entry_price=104.0,
        stop_price=101.0, target_price=110.0, spread_width=0.5,
    )
    monkeypatch.setattr(
        runtime, "qualify_all",
        lambda *args, **kwargs: _continuation_summary(symbol, promoted),
    )

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    cand = result.contract["trade_candidates"][0]
    assert cand["entry"] == pytest.approx(104.0)
    assert cand["stop"] == pytest.approx(101.0)
    assert cand["target"] == pytest.approx(110.0)
    assert cand["risk_reward"] == pytest.approx(2.0)


def test_missing_candidate_fails_loud_prd260(monkeypatch, tmp_path):
    # PRD-260 R5 (red pre-change: bare KeyError): a qualified setup whose
    # symbol has no candidate raises a NAMED error at decision assembly.
    symbol = "SPY"
    _setup_runtime_mocks(monkeypatch, tmp_path, symbol=symbol)
    monkeypatch.setattr(
        runtime, "_fixture_chain_results",
        lambda setups: {symbol: _manual_check_chain(symbol)},
    )
    monkeypatch.setattr(runtime, "generate_candidates", lambda *args, **kwargs: {})
    monkeypatch.setattr(
        runtime, "qualify_all",
        lambda *args, **kwargs: _qualification_summary(symbol),
    )

    with pytest.raises(RuntimeError, match="no TradeCandidate"):
        runtime._run_pipeline(
            mode=runtime.MODE_FIXTURE,
            run_date=date.fromisoformat("2026-04-28"),
            fixture_file=Path("tests/fixtures/2026-04-12.json"),
        )


def test_prd283_sizing_refusal_reaches_every_consumer(monkeypatch, tmp_path, capsys):
    """PRD-283 (CB-02) end-to-end: a real refusal generated in the pipeline
    carries the exact token through contract, audit, postmarket, premarket,
    HTML delivery, notification, and CLI. Omitting the out-parameter or any
    forwarding leg turns this red.
    """
    symbol = "SPY"
    _setup_runtime_mocks(monkeypatch, tmp_path, symbol=symbol)

    # build_option_setups refuses the sole candidate via the out-parameter
    # (the exact contract the real function honors); no OptionSetup is emitted.
    def _refusing_build(*args, refusals=None, **kwargs):
        if refusals is not None:
            refusals.append(OptionRefusal(
                symbol=symbol, strategy="BULL_PUT_SPREAD",
                risk_per_contract=350.0, adjusted_budget=160.0, risk_modifier=0.4,
            ))
        return []
    monkeypatch.setattr(runtime, "build_option_setups", _refusing_build)
    # Use the REAL premarket/postmarket builders so their consumption is proven.
    monkeypatch.setattr(runtime, "build_premarket_report", _real_premarket)
    monkeypatch.setattr(runtime, "build_postmarket_report", _real_postmarket)

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    # No setup was expressed -> NO_TRADE.
    assert result.outcome == runtime.OUTCOME_NO_TRADE

    # 1. Contract rejections carry the OPTIONS_SIZING stage + token.
    sizing = [r for r in result.contract["rejections"] if r["stage"] == OPTIONS_SIZING]
    assert len(sizing) == 1
    assert sizing[0]["symbol"] == symbol
    assert sizing[0]["reason"] == SMALLEST_CONTRACT_EXCEEDS_BUDGET

    # 2. Audit record carries the dedicated refusal carrier, no silent-None row.
    audit_lines = (tmp_path / "logs" / "audit.jsonl").read_text().strip().splitlines()
    record = json.loads(audit_lines[-1])
    assert [c["reason"] for c in record["options_refusals"]] == [SMALLEST_CONTRACT_EXCEEDS_BUDGET]
    assert [q for q in record["qualified_trades"] if q["symbol"] == symbol] == []

    # 3. Postmarket counts the refusal in the breakdown and rejected_count.
    postmarket = _real_postmarket(result.contract, [])
    assert postmarket["rejection_breakdown"]["options_sizing"] == 1
    assert postmarket["trade_summary"]["rejected_count"] >= 1

    # 4. Premarket does not surface the refused symbol as a tradable focus.
    premarket = _real_premarket(result.contract)
    assert all(item.get("symbol") != symbol for item in premarket.get("focus_list", []))

    # 5. HTML delivery renders the refusal (not "no qualifying setups").
    payload = build_report_payload(result.contract)
    html_text = render_report_from_payload(payload)
    assert "REFUSED" in html_text
    assert "no qualifying setups" not in html_text

    # 6. Notification names the refusal, not a generic "no setups".
    _title, body = build_notification_message(result.contract)
    assert "Reason: no setups" not in body
    assert "refused" in body.lower()

    # 7. CLI names the refusal reason.
    deliver_cli(payload)
    cli_out = capsys.readouterr().out
    assert "REFUSED SPY" in cli_out
    assert SMALLEST_CONTRACT_EXCEEDS_BUDGET in cli_out


# ---------------------------------------------------------------------------
# PRD-284 — full A2 materialization end-to-end (execution_policy -> contract).
# render_report is stubbed in this harness; render behavior is covered by
# test_contract.py::test_prd284_render_report_materialized_sizing_and_excludes_blocked.
# ---------------------------------------------------------------------------


def _regime_confidence(confidence: float) -> RegimeState:
    return RegimeState(
        regime=RISK_ON,
        posture=AGGRESSIVE_LONG,
        confidence=confidence,
        net_score=5,
        risk_on_votes=5,
        risk_off_votes=0,
        neutral_votes=3,
        total_votes=8,
        vote_breakdown={},
        vix_level=16.0,
        vix_pct_change=-0.03,
        computed_at_utc=RUN_AT,
    )


def _chain_manual(symbol: str = "SPY") -> ChainValidationResult:
    return ChainValidationResult(
        symbol=symbol,
        classification=MANUAL_CHECK,
        reason="fixture mode skips live chain validation",
        spread_pct=None,
        open_interest=None,
        volume=None,
        expiry_used=None,
        data_source=None,
    )


def test_prd284_e2e_positive_materialization_reaches_contract(monkeypatch, tmp_path):
    # confidence 0.65 -> multiplier 0.5 (NEUTRAL pressure isolates it).
    # Mocked decision: 2 contracts / $400 -> materialized 1 contract / $200.
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "compute_regime", lambda quotes: _regime_confidence(0.65))
    monkeypatch.setattr(runtime, "_compute_overall_pressure", lambda quotes: "NEUTRAL")
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {"SPY": _chain_manual()})
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *a, **k: runtime.TradeDecision(
        ticker="SPY", direction="LONG", status=ALLOW_TRADE, entry=100.0, stop=97.0,
        target=106.0, r_r=2.0, contracts=2, dollar_risk=400.0, block_reason=None,
    ))

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    assert result.outcome == runtime.OUTCOME_TRADE
    candidate = result.contract["trade_candidates"][0]
    assert candidate["decision_status"] == ALLOW_TRADE
    assert candidate["size_multiplier"] == 0.5
    assert candidate["position_size"] == 1        # materialized (setup carries 2)
    assert candidate["dollar_risk"] == 200.0      # 400/2*1, materialized


def test_prd284_e2e_size_rounds_to_zero_blocks_through_contract(monkeypatch, tmp_path):
    # confidence 0.65 -> multiplier 0.5; 1 contract x 0.5 -> floor 0 -> block.
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "compute_regime", lambda quotes: _regime_confidence(0.65))
    monkeypatch.setattr(runtime, "_compute_overall_pressure", lambda quotes: "NEUTRAL")
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {"SPY": _chain_manual()})
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *a, **k: runtime.TradeDecision(
        ticker="SPY", direction="LONG", status=ALLOW_TRADE, entry=100.0, stop=97.0,
        target=106.0, r_r=2.0, contracts=1, dollar_risk=150.0, block_reason=None,
    ))

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    assert result.outcome == runtime.OUTCOME_NO_TRADE
    candidate = result.contract["trade_candidates"][0]
    assert candidate["decision_status"] == BLOCK_TRADE
    assert candidate["block_reason"] == "size_rounds_to_zero"
    assert candidate["policy_reason"] == "size_rounds_to_zero"
    assert candidate["size_multiplier"] == 0.0
    assert candidate["position_size"] == 1  # contracts >= 1 invariant preserved
    assert candidate["decision_trace"]["stage"] == "EXECUTION_POLICY"


def test_prd284_runtime_passes_size_blocked_to_report(monkeypatch, tmp_path):
    # PRD-284 R5: the pipeline builds the size_rounds_to_zero block map from the
    # decisions and passes it to render_report (render is otherwise stubbed).
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "compute_regime", lambda quotes: _regime_confidence(0.65))
    monkeypatch.setattr(runtime, "_compute_overall_pressure", lambda quotes: "NEUTRAL")
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {"SPY": _chain_manual()})
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *a, **k: runtime.TradeDecision(
        ticker="SPY", direction="LONG", status=ALLOW_TRADE, entry=100.0, stop=97.0,
        target=106.0, r_r=2.0, contracts=1, dollar_risk=150.0, block_reason=None,
    ))
    captured: dict = {}
    monkeypatch.setattr(runtime, "render_report", lambda **kwargs: captured.update(kwargs) or "report")

    runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    # 1 contract x 0.5 -> floor 0 -> size_rounds_to_zero, carried into the report.
    assert captured["size_blocked"] == {"SPY": "size_rounds_to_zero"}
    assert captured["materialized_sizing"] == {}  # nothing actionable


# ---------------------------------------------------------------------------
# PRD-286 / CB-05 — macro-pressure COMPUTATION FAILURE fails closed.
# ---------------------------------------------------------------------------

def _raise_value_error(*args, **kwargs):
    raise ValueError("macro computation boom")


def test_prd286_compute_pressure_unavailable_when_build_drivers_raises(monkeypatch):
    # req 1: _build_macro_drivers raising -> the UNAVAILABLE sentinel, not "UNKNOWN".
    monkeypatch.setattr(runtime, "_build_macro_drivers", _raise_value_error)
    assert runtime._compute_overall_pressure({}) == "UNAVAILABLE"


def test_prd286_compute_pressure_unavailable_when_build_macro_pressure_raises(monkeypatch):
    # req 2: build_macro_pressure raising -> the UNAVAILABLE sentinel.
    monkeypatch.setattr(runtime, "_build_macro_drivers", lambda quotes: {})
    monkeypatch.setattr(runtime, "build_macro_pressure", _raise_value_error)
    assert runtime._compute_overall_pressure({}) == "UNAVAILABLE"


def test_prd286_e2e_macro_unavailable_blocks_run(monkeypatch, tmp_path):
    # req 3 (end-to-end): a computation failure blocks the run's decisions with
    # macro_pressure_unavailable at EXECUTION_POLICY (not a full-size allow).
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "compute_regime", lambda quotes: _regime_confidence(0.80))
    monkeypatch.setattr(runtime, "_compute_overall_pressure", lambda quotes: "UNAVAILABLE")
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {"SPY": _chain_manual()})
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *a, **k: runtime.TradeDecision(
        ticker="SPY", direction="LONG", status=ALLOW_TRADE, entry=100.0, stop=97.0,
        target=106.0, r_r=2.0, contracts=2, dollar_risk=400.0, block_reason=None,
    ))

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    assert result.outcome == runtime.OUTCOME_NO_TRADE
    candidate = result.contract["trade_candidates"][0]
    assert candidate["decision_status"] == BLOCK_TRADE
    assert candidate["block_reason"] == "macro_pressure_unavailable"
    assert candidate["policy_reason"] == "macro_pressure_unavailable"
    assert candidate["size_multiplier"] == 0.0
    assert candidate["decision_trace"]["stage"] == "EXECUTION_POLICY"


def test_prd286_e2e_computed_unknown_not_blocked(monkeypatch, tmp_path):
    # req 5 (end-to-end distinction): a genuinely computed "UNKNOWN" (drivers
    # absent, no failure) is NOT a failure — it stays allowed at full size.
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "compute_regime", lambda quotes: _regime_confidence(0.80))
    monkeypatch.setattr(runtime, "_compute_overall_pressure", lambda quotes: "UNKNOWN")
    monkeypatch.setattr(runtime, "_fixture_chain_results", lambda setups: {"SPY": _chain_manual()})
    monkeypatch.setattr(runtime, "create_trade_decision", lambda *a, **k: runtime.TradeDecision(
        ticker="SPY", direction="LONG", status=ALLOW_TRADE, entry=100.0, stop=97.0,
        target=106.0, r_r=2.0, contracts=2, dollar_risk=400.0, block_reason=None,
    ))

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    assert result.outcome == runtime.OUTCOME_TRADE
    candidate = result.contract["trade_candidates"][0]
    assert candidate["decision_status"] == ALLOW_TRADE
    assert candidate["block_reason"] is None


# ---------------------------------------------------------------------------
# PRD-288: SPY observation threaded through the daily pipeline
# ---------------------------------------------------------------------------

def _empty_qualification_summary() -> QualificationSummary:
    return QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[],
        watchlist=[],
        excluded={},
        symbols_evaluated=0,
        symbols_qualified=0,
        symbols_watchlist=0,
        symbols_excluded=0,
    )


def test_t5_spy_observation_present_on_no_candidate_run(monkeypatch, tmp_path):
    # Independent of candidate availability: a zero-candidate run still threads
    # the observation onto the PipelineResult and into the daily payload.
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_compute_overall_pressure", lambda quotes: "NEUTRAL")
    monkeypatch.setattr(runtime, "generate_candidates", lambda *a, **k: {})
    monkeypatch.setattr(runtime, "qualify_all", lambda *a, **k: _empty_qualification_summary())
    monkeypatch.setattr(runtime, "build_option_setups", lambda *a, **k: [])

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    assert result.outcome == runtime.OUTCOME_NO_TRADE
    assert result.spy_observation is not None  # present even with zero candidates
    payload = build_report_payload(result.contract, spy_observation=result.spy_observation)
    assert "spy_observation" in payload["sections"]


def test_t6_t11_halt_threads_unavailable_observation_and_preserves_halt(monkeypatch, tmp_path):
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(
        runtime, "validate_quotes",
        lambda *a, **k: _dc_replace(
            _validation_summary(), system_halted=True, halt_reason="data integrity halt"
        ),
    )

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    # T11: halt semantics unchanged (the pure observation build alters nothing).
    assert result.outcome == runtime.OUTCOME_HALT
    assert result.validation_summary.system_halted is True
    assert result.validation_summary.halt_reason == "data integrity halt"
    # T6: card present as UNAVAILABLE / system_halted, no fabricated value.
    assert result.spy_observation is not None
    assert result.spy_observation.state == "UNAVAILABLE"
    assert result.spy_observation.reason == "system_halted"
    assert result.spy_observation.session_vwap is None
    assert result.spy_observation.current_price is None
    assert result.spy_observation.orb is None


# ---------------------------------------------------------------------------
# PRD-289: Market Control Card threaded through the daily pipeline
# ---------------------------------------------------------------------------

def _spy_session_frame(n_bars: int = 20, start_utc: str = "2026-04-28 13:30") -> pd.DataFrame:
    idx = pd.date_range(start_utc, periods=n_bars, freq="1min", tz="UTC")
    closes = [100.0 + i for i in range(n_bars)]
    return pd.DataFrame(
        {"Open": closes, "High": [c + 1 for c in closes], "Low": [c - 1 for c in closes],
         "Close": closes, "Volume": [1000] * n_bars},
        index=idx,
    )


def _setup_live_card_mocks(monkeypatch, tmp_path):
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "compute_all_intraday_metrics", lambda symbols, asof: ({}, []))
    monkeypatch.setattr(runtime, "_refresh_trend_structure_sidecar", lambda **kwargs: None)


def test_m1_m2_single_fetch_feeds_observation_and_state_same_object(monkeypatch, tmp_path):
    _setup_live_card_mocks(monkeypatch, tmp_path)
    run_at = datetime(2026, 4, 28, 13, 49, 30, tzinfo=timezone.utc)  # 09:49:30 ET

    class _FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return run_at if tz is not None else run_at.replace(tzinfo=None)

    # MODE_LIVE keys run_at_utc on datetime.now (runtime/__init__.py) — freeze it.
    monkeypatch.setattr(runtime, "datetime", _FrozenDatetime)
    frame = _spy_session_frame()
    fetch_calls: list[str] = []

    def _fake_session_fetch(symbol):
        fetch_calls.append(symbol)
        return frame

    monkeypatch.setattr(runtime, "fetch_intraday_session_bars", _fake_session_fetch)
    observation_frames: list = []
    real_build_observation = runtime.build_spy_observation

    def _tap_observation(**kwargs):
        observation_frames.append(kwargs["session_frame"])
        return real_build_observation(**kwargs)

    monkeypatch.setattr(runtime, "build_spy_observation", _tap_observation)
    seam_frames: list = []
    real_seam = runtime.build_spy_state_outcome

    def _tap_seam(**kwargs):
        seam_frames.append(kwargs["session_frame"])
        return real_seam(**kwargs)

    monkeypatch.setattr(runtime, "build_spy_state_outcome", _tap_seam)

    result = runtime._run_pipeline(mode=runtime.MODE_LIVE, run_date=date(2026, 4, 28), fixture_file=None)

    # M2: exactly one SPY session fetch feeds both observation and STATE.
    assert fetch_calls == ["SPY"]
    # M1: both consumers received the EXACT frame object — identity, not equality.
    assert observation_frames and seam_frames
    assert observation_frames[0] is frame
    assert seam_frames[0] is frame
    assert result.spy_observation.state == "OBSERVED"
    card = result.market_control_card
    assert card is not None
    assert card.state["value"] in {"EXPANSION_CONFIRMED", "FAILED_EXPANSION", "RANGE"}
    assert card.state["unavailable_reason"] is None


def test_m14_halt_run_composes_card_without_fetch_or_engine(monkeypatch, tmp_path):
    _setup_live_card_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(
        runtime, "validate_quotes",
        lambda *a, **k: _dc_replace(
            _validation_summary(), system_halted=True, halt_reason="data integrity halt"
        ),
    )

    def _no_fetch(symbol):
        raise AssertionError("halt run must not fetch SPY session bars")

    monkeypatch.setattr(runtime, "fetch_intraday_session_bars", _no_fetch)
    import cuttingboard.spy_state as spy_state_module

    def _no_engine(*a, **k):
        raise AssertionError("halt run must not call the intraday state engine")

    monkeypatch.setattr(spy_state_module, "compute_intraday_state", _no_engine)

    result = runtime._run_pipeline(mode=runtime.MODE_LIVE, run_date=date(2026, 4, 28), fixture_file=None)

    assert result.outcome == runtime.OUTCOME_HALT
    card = result.market_control_card
    assert card is not None  # halted ELIGIBLE runs still carry the card
    assert card.state == {"value": None, "unavailable_reason": "observation_unavailable"}
    assert card.permission == {"value": "No trades permitted. System halted."}
    assert card.transition == {"value": None, "unavailable_reason": "transition_state_unavailable"}
    assert card.invalidation == {"value": None, "unavailable_reason": "invalidation_inputs_absent"}
    assert card.candidate_implication == {"value": None, "unavailable_reason": "candidate_inputs_absent"}
    assert card.location["state"] == "UNAVAILABLE"
    assert card.location["reason"] == "system_halted"


def test_m12_fixture_run_card_is_additive_only(monkeypatch, tmp_path):
    _setup_runtime_mocks(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "_compute_overall_pressure", lambda quotes: "NEUTRAL")
    monkeypatch.setattr(runtime, "generate_candidates", lambda *a, **k: {})
    monkeypatch.setattr(runtime, "qualify_all", lambda *a, **k: _empty_qualification_summary())
    monkeypatch.setattr(runtime, "build_option_setups", lambda *a, **k: [])

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    # Pinned decision fields unchanged while the card exists (additive-only).
    assert result.outcome == runtime.OUTCOME_NO_TRADE
    assert result.contract["outcome"] == runtime.OUTCOME_NO_TRADE
    assert result.validation_summary.system_halted is False
    card = result.market_control_card
    assert card is not None
    base = build_report_payload(result.contract, spy_observation=result.spy_observation)
    with_card = build_report_payload(
        result.contract, spy_observation=result.spy_observation, market_control_card=card
    )
    carded = with_card["sections"].pop("market_control_card")
    assert carded["permission"]["value"] == result.contract["system_state"]["permission"]
    assert with_card == base  # the section is the ONLY delta


def test_m23_sunday_run_produces_no_card_and_no_section(monkeypatch, tmp_path):
    _setup_runtime_mocks(monkeypatch, tmp_path)

    result = runtime._run_pipeline(
        mode=runtime.MODE_SUNDAY, run_date=date.fromisoformat("2026-04-26"), fixture_file=None
    )

    assert result.market_control_card is None
    payload = build_report_payload(
        result.contract,
        spy_observation=result.spy_observation,
        market_control_card=result.market_control_card,
    )
    assert "market_control_card" not in payload["sections"]


def test_m11_card_persists_additively_contract_and_audit_byte_unchanged(monkeypatch, tmp_path):
    # M11 persistence truth against the ACTUAL PERSISTED ARTIFACTS (not in-memory
    # _run_pipeline return values). Drive the real write path through the
    # production entry point execute_run — which runs the pipeline (appending the
    # audit record), writes latest_contract.json, and forwards the card to the
    # payload write (runtime/__init__.py:290-294) — with and without the card, and
    # prove the PRD-289 M11 claims against the bytes on disk:
    #   (a) the card section is additive in the persisted latest_payload.json;
    #   (b) the card block renders in the dashboard produced from the persisted payload;
    #   (c) the persisted latest_contract.json and audit.jsonl are byte-identical with
    #       and without the card, and the card literal appears in neither.
    # This reddens if execute_run / _write_payload_artifacts / payload delivery /
    # dashboard delivery regress so the real artifacts drift or omit the card while
    # the card still exists on PipelineResult (the in-memory-only comparison could not
    # catch that — Codex P1-A on PR #231).
    repo_root = Path.cwd()
    fixture_file = repo_root / "tests" / "fixtures" / "2026-04-12.json"
    _setup_runtime_mocks(monkeypatch, tmp_path)
    # The autouse `_isolate_real_log_paths` fixture + `_setup_runtime_mocks`
    # redirect every default-path artifact write into tmp_path/logs, so the real
    # write path lands its artifacts here:
    logs = tmp_path / "logs"
    payload_path = logs / "latest_payload.json"
    contract_path = logs / "latest_contract.json"
    audit_path = logs / "audit.jsonl"
    # execute_run also writes the market map + macro snapshot via default paths
    # the redirect fixtures do not cover; neutralize them so this test stays
    # hermetic (both are irrelevant to the card's persistence).
    monkeypatch.setattr(runtime, "_load_previous_market_map", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_write_market_map_file", lambda *a, **k: None)
    monkeypatch.setattr(runtime, "_write_macro_snapshot", lambda *a, **k: None)

    def _run_and_persist():
        # Route through execute_run (the production entry point), NOT the write
        # helpers directly, so a regression in execute_run's own forwarding of
        # the card to the write path — runtime/__init__.py:290-294 — is covered
        # (Codex P1-A re-raise on PR #231). execute_run runs the pipeline (which
        # appends the audit record), then writes latest_contract.json and the
        # payload artifacts; the autouse redirect lands them under tmp_path/logs.
        summary = runtime.execute_run(
            mode=runtime.MODE_FIXTURE,
            run_date=date.fromisoformat("2026-04-28"),
            fixture_file=fixture_file,
        )
        return summary, {
            "payload": payload_path.read_text(encoding="utf-8"),
            "contract": contract_path.read_text(encoding="utf-8"),
            "audit": audit_path.read_text(encoding="utf-8").splitlines()[-1],
        }

    # WITH card — capture the persisted bytes before the WITHOUT run overwrites them.
    with_summary, with_art = _run_and_persist()
    payload_with_obj = json.loads(with_art["payload"])
    # execute_run succeeded AND forwarded the card all the way to the persisted
    # payload: if execute_run stopped forwarding market_control_card, dropped the
    # payload write, or fell into its error path, the section would be absent here.
    assert "market_control_card" in payload_with_obj["sections"]

    # Reset the overwrite-mode artifacts so the WITHOUT run writes them fresh
    # (audit.jsonl is append-only; its latest record is compared below).
    payload_path.unlink()
    contract_path.unlink()

    # WITHOUT card
    monkeypatch.setattr(runtime, "build_market_control_card", lambda **kwargs: None)
    without_summary, without_art = _run_and_persist()
    payload_without_obj = json.loads(without_art["payload"])

    # (a) card section additive in the PERSISTED payload
    assert "market_control_card" not in payload_without_obj["sections"]

    # (b) dashboard delivery renders the card block FROM the persisted payload; absent without
    html_with = render_dashboard_html(payload_with_obj, with_summary, market_map=None)
    html_without = render_dashboard_html(payload_without_obj, without_summary, market_map=None)
    assert 'id="market-control-card"' in html_with
    assert 'id="market-control-card"' not in html_without

    # (c) persisted contract + audit byte-identical with/without the card; card leaks into neither
    assert with_art["contract"] == without_art["contract"]
    assert with_art["audit"] == without_art["audit"]
    assert "market_control_card" not in with_art["contract"]
    assert "market_control_card" not in with_art["audit"]
