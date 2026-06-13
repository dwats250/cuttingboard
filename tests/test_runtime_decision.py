from __future__ import annotations

import json
from dataclasses import replace as _dc_replace
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from cuttingboard import audit, runtime
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.chain_validation import ChainValidationResult, MANUAL_CHECK
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationResult, QualificationSummary, TradeCandidate
from cuttingboard.regime import AGGRESSIVE_LONG, RISK_ON, RegimeState
from cuttingboard.structure import StructureResult
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE
from cuttingboard.validation import ValidationSummary
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

    summary_path = tmp_path / "validation_halt_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    assert runtime.verify_run_summary(str(summary_path))["pass"] is True


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
