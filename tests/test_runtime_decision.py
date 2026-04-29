from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from cuttingboard import runtime
from cuttingboard.chain_validation import ChainValidationResult, MANUAL_CHECK
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationResult, QualificationSummary, TradeCandidate
from cuttingboard.regime import AGGRESSIVE_LONG, RISK_ON, RegimeState
from cuttingboard.structure import StructureResult
from cuttingboard.trade_decision import ALLOW_TRADE, BLOCK_TRADE
from cuttingboard.validation import ValidationSummary
from cuttingboard.watch import WatchSummary


RUN_AT = datetime(2026, 4, 28, 13, 0, tzinfo=timezone.utc)


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


def _qualification_summary() -> QualificationSummary:
    return QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[
            QualificationResult(
                symbol="SPY",
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


def _option_setup() -> OptionSetup:
    return OptionSetup(
        symbol="SPY",
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


def _candidate() -> TradeCandidate:
    return TradeCandidate(
        symbol="SPY",
        direction="LONG",
        entry_price=100.0,
        stop_price=97.0,
        target_price=106.0,
        spread_width=0.75,
    )


def _setup_runtime_mocks(monkeypatch, tmp_path):
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(runtime, "LATEST_RUN_PATH", tmp_path / "logs" / "latest_run.json")
    monkeypatch.setattr(runtime, "LATEST_CONTRACT_PATH", str(tmp_path / "logs" / "latest_contract.json"))
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
    monkeypatch.setattr(runtime, "compute_all_derived", lambda quotes: {"SPY": object()})
    monkeypatch.setattr(runtime, "resolve_sector_router", lambda *args, **kwargs: runtime.SectorRouterState(
        mode="MIXED",
        energy_score=0.0,
        index_score=0.0,
        computed_at_utc=RUN_AT,
        session_date="2026-04-28",
    ))
    monkeypatch.setattr(runtime, "classify_all_structure", lambda *args, **kwargs: {
        "SPY": StructureResult(
            symbol="SPY",
            structure="TREND",
            iv_environment="NORMAL_IV",
            is_tradeable=True,
            disqualification_reason=None,
        )
    })
    monkeypatch.setattr(runtime, "log_universe_configuration", lambda logger: None)
    monkeypatch.setattr(runtime, "filter_execution_dict", lambda payload, log=None: payload)
    monkeypatch.setattr(runtime, "filter_execution_items", lambda items, symbol_getter=None, log=None: items)
    monkeypatch.setattr(runtime, "classify_watchlist", lambda *args, **kwargs: WatchSummary(
        session="PREMARKET",
        threshold=0.0,
        watchlist=[],
        ignored_symbols=[],
        execution_posture="ACTIVE",
    ))
    monkeypatch.setattr(runtime, "generate_candidates", lambda *args, **kwargs: {"SPY": _candidate()})
    monkeypatch.setattr(runtime, "fetch_ohlcv", lambda symbol: None)
    monkeypatch.setattr(runtime, "qualify_all", lambda *args, **kwargs: _qualification_summary())
    monkeypatch.setattr(runtime, "apply_sector_router", lambda qual, router_state, run_at_utc: (qual, []))
    monkeypatch.setattr(runtime, "_log_continuation_audit", lambda regime, summary: None)
    monkeypatch.setattr(runtime, "build_option_setups", lambda *args, **kwargs: [_option_setup()])
    monkeypatch.setattr(runtime, "render_report", lambda **kwargs: "report")
    monkeypatch.setattr(runtime, "_write_markdown_report", lambda report, date_str, sha: None)
    monkeypatch.setattr(runtime, "_load_run_history", lambda path: [])
    monkeypatch.setattr(runtime, "build_premarket_report", lambda contract: {})
    monkeypatch.setattr(runtime, "build_postmarket_report", lambda contract, history: {})


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
