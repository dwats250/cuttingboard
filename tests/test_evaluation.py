from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from cuttingboard import audit, evaluation, runtime
from cuttingboard.chain_validation import ChainValidationResult, MANUAL_CHECK
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationResult, QualificationSummary, TradeCandidate
from cuttingboard.regime import AGGRESSIVE_LONG, RISK_ON, RegimeState
from cuttingboard.structure import StructureResult
from cuttingboard.trade_decision import ALLOW_TRADE
from cuttingboard.validation import ValidationSummary
from cuttingboard.watch import WatchSummary


ANCHOR = datetime(2026, 4, 28, 13, 0, tzinfo=timezone.utc)


def _bars(*rows: tuple[str, float, float, float, float]) -> pd.DataFrame:
    index = pd.to_datetime([row[0] for row in rows], utc=True)
    return pd.DataFrame(
        {
            "Open": [row[1] for row in rows],
            "High": [row[2] for row in rows],
            "Low": [row[3] for row in rows],
            "Close": [row[4] for row in rows],
            "Volume": [1000 for _ in rows],
        },
        index=index,
    )


def _candidate(direction: str = "LONG", **overrides) -> dict:
    candidate = {
        "symbol": "SPY",
        "direction": direction,
        "entry": 100.0,
        "stop": 98.0,
        "target": 104.0 if direction == "LONG" else 96.0,
    }
    candidate.update(overrides)
    return candidate


def _prior_record(*candidates: dict, run_at_utc: datetime = ANCHOR) -> dict:
    return {
        "run_at_utc": run_at_utc.isoformat(),
        "trade_decisions": [
            {
                "symbol": candidate["symbol"],
                "direction": candidate["direction"],
                "entry": candidate["entry"],
                "stop": candidate["stop"],
                "target": candidate["target"],
                "decision_status": ALLOW_TRADE,
            }
            for candidate in candidates
        ],
    }


def test_long_target_hit() -> None:
    result = evaluation.evaluate_trade_candidate(
        candidate=_candidate("LONG"),
        bars=_bars(
            ("2026-04-28T13:01:00Z", 100.0, 101.0, 99.0, 100.5),
            ("2026-04-28T13:02:00Z", 100.5, 104.2, 100.1, 104.0),
        ),
        anchor=ANCHOR,
        window_bars=78,
    )
    assert result == {"result": "TARGET_HIT", "R_multiple": 2.0, "time_to_resolution": 2}


def test_long_stop_hit() -> None:
    result = evaluation.evaluate_trade_candidate(
        candidate=_candidate("LONG"),
        bars=_bars(("2026-04-28T13:01:00Z", 100.0, 100.2, 97.5, 98.5)),
        anchor=ANCHOR,
        window_bars=78,
    )
    assert result == {"result": "STOP_HIT", "R_multiple": -1.0, "time_to_resolution": 1}


def test_short_target_hit() -> None:
    result = evaluation.evaluate_trade_candidate(
        candidate=_candidate("SHORT", stop=102.0, target=96.0),
        bars=_bars(("2026-04-28T13:01:00Z", 100.0, 100.5, 95.8, 96.2)),
        anchor=ANCHOR,
        window_bars=78,
    )
    assert result == {"result": "TARGET_HIT", "R_multiple": 2.0, "time_to_resolution": 1}


def test_short_stop_hit() -> None:
    result = evaluation.evaluate_trade_candidate(
        candidate=_candidate("SHORT", stop=102.0, target=96.0),
        bars=_bars(("2026-04-28T13:01:00Z", 100.0, 102.1, 99.5, 101.8)),
        anchor=ANCHOR,
        window_bars=78,
    )
    assert result == {"result": "STOP_HIT", "R_multiple": -1.0, "time_to_resolution": 1}


def test_same_bar_conflict_stop_wins() -> None:
    result = evaluation.evaluate_trade_candidate(
        candidate=_candidate("LONG"),
        bars=_bars(("2026-04-28T13:01:00Z", 100.0, 104.5, 97.9, 103.5)),
        anchor=ANCHOR,
        window_bars=78,
    )
    assert result == {"result": "STOP_HIT", "R_multiple": -1.0, "time_to_resolution": 1}


def test_no_hit_in_window_uses_final_close() -> None:
    result = evaluation.evaluate_trade_candidate(
        candidate=_candidate("LONG"),
        bars=_bars(
            ("2026-04-28T13:01:00Z", 100.0, 101.0, 99.4, 100.5),
            ("2026-04-28T13:02:00Z", 100.5, 103.9, 99.5, 103.0),
        ),
        anchor=ANCHOR,
        window_bars=78,
    )
    assert result == {"result": "NO_HIT", "R_multiple": 1.5, "time_to_resolution": 78}


def test_no_forward_bars() -> None:
    result = evaluation.evaluate_trade_candidate(
        candidate=_candidate("LONG"),
        bars=_bars(("2026-04-28T13:00:00Z", 100.0, 101.0, 99.0, 100.5)),
        anchor=ANCHOR,
        window_bars=78,
    )
    assert result == {"result": "NO_HIT", "R_multiple": 0.0, "time_to_resolution": 0}


def test_invalid_trade_entry_equals_stop() -> None:
    with pytest.raises(ValueError, match="positive risk"):
        evaluation.evaluate_trade_candidate(
            candidate=_candidate("LONG", stop=100.0),
            bars=_bars(("2026-04-28T13:01:00Z", 100.0, 101.0, 99.0, 100.5)),
            anchor=ANCHOR,
            window_bars=78,
        )


def test_determinism() -> None:
    candidate = _candidate("LONG")
    bars = _bars(
        ("2026-04-28T13:01:00Z", 100.0, 101.0, 99.4, 100.5),
        ("2026-04-28T13:02:00Z", 100.5, 104.2, 100.1, 104.0),
    )
    first = evaluation.evaluate_trade_candidate(
        candidate=candidate,
        bars=bars,
        anchor=ANCHOR,
        window_bars=78,
    )
    second = evaluation.evaluate_trade_candidate(
        candidate=candidate,
        bars=bars,
        anchor=ANCHOR,
        window_bars=78,
    )
    assert first == second


def test_no_prior_audit_record_skips_cleanly(tmp_path: Path) -> None:
    records = evaluation.run_post_trade_evaluation(
        current_run_at_utc=ANCHOR,
        audit_log_path=str(tmp_path / "logs" / "audit.jsonl"),
        evaluation_log_path=str(tmp_path / "logs" / "evaluation.jsonl"),
    )
    assert records == []
    assert not (tmp_path / "logs" / "evaluation.jsonl").exists()


def test_run_post_trade_evaluation_appends_one_record_per_allow_trade(tmp_path: Path) -> None:
    audit_path = tmp_path / "logs" / "audit.jsonl"
    audit_path.parent.mkdir(parents=True)
    prior = _prior_record(_candidate("LONG"), _candidate("SHORT", symbol="QQQ", stop=102.0, target=96.0))
    audit_path.write_text(json.dumps(prior) + "\n", encoding="utf-8")

    bars_by_symbol = {
        "SPY": _bars(("2026-04-28T13:01:00Z", 100.0, 104.1, 99.5, 104.0)),
        "QQQ": _bars(("2026-04-28T13:01:00Z", 100.0, 100.8, 95.9, 96.1)),
    }
    records = evaluation.run_post_trade_evaluation(
        current_run_at_utc=datetime(2026, 4, 28, 13, 30, tzinfo=timezone.utc),
        fetch_intraday_bars_fn=lambda symbol: bars_by_symbol[symbol],
        audit_log_path=str(audit_path),
        evaluation_log_path=str(tmp_path / "logs" / "evaluation.jsonl"),
    )

    assert len(records) == 2
    written = [
        json.loads(line)
        for line in (tmp_path / "logs" / "evaluation.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert len(written) == 2
    assert {record["symbol"] for record in written} == {"SPY", "QQQ"}


def test_runtime_runs_evaluation_after_audit_write(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    events: list[str] = []
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
    original_write_audit_record = runtime.write_audit_record

    def _tracked_write_audit_record(*args, **kwargs):
        events.append("audit")
        return original_write_audit_record(*args, **kwargs)

    def _tracked_evaluation(*, current_run_at_utc):
        assert current_run_at_utc == ANCHOR
        events.append("evaluation")
        return []

    monkeypatch.setattr(runtime, "write_audit_record", _tracked_write_audit_record)
    monkeypatch.setattr(runtime, "run_post_trade_evaluation", _tracked_evaluation)

    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )

    assert result.contract["trade_candidates"][0]["decision_status"] == ALLOW_TRADE
    assert events == ["audit", "evaluation"]


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
        computed_at_utc=ANCHOR,
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


def _runtime_candidate() -> TradeCandidate:
    return TradeCandidate(
        symbol="SPY",
        direction="LONG",
        entry_price=100.0,
        stop_price=97.0,
        target_price=106.0,
        spread_width=0.75,
    )


def _setup_runtime_mocks(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(runtime, "LATEST_RUN_PATH", tmp_path / "logs" / "latest_run.json")
    monkeypatch.setattr(runtime, "LATEST_CONTRACT_PATH", str(tmp_path / "logs" / "latest_contract.json"))
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", str(tmp_path / "logs" / "audit.jsonl"))
    monkeypatch.setattr(runtime, "_deterministic_run_at", lambda mode, fixture_file: ANCHOR)
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
        computed_at_utc=ANCHOR,
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
    monkeypatch.setattr(runtime, "generate_candidates", lambda *args, **kwargs: {"SPY": _runtime_candidate()})
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


def _null_context():
    class _Ctx:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    return lambda *args, **kwargs: _Ctx()
