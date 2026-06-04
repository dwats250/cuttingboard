"""PRD-161 — Tradable qualified fixture for the PRD-157 sizing gate.

The PRD-157 fixture-verification gate was BLOCKED because the only end-to-end
fixture run produced a single sized candidate that was non-tradable (`^VIX`,
a member of `config.NON_TRADABLE_SYMBOLS`). See
`audits/recon-2026-05-24/prd-157-fixture-gate-report.md`.

This module drives `runtime._run_pipeline` in fixture mode with a qualified
TRADABLE candidate (SPY) injected at the qualification/option stages (the
sanctioned pattern from `tests/test_runtime_decision.py`), and lets the REAL
contract assembly compute `position_size` / `dollar_risk` / `estimated_debit`.
It verifies that a tradable candidate surfaces in the payload `top_trades` with
present, positive, coherent sizing, deterministically.

Realizability note (see PRD-161): fixture mode forces every candidate to
`BLOCK_TRADE` at the chain stage (`_fixture_chain_results` → MANUAL_CHECK →
`trade_decision.py:101`). So `decision_status=ALLOW_TRADE` / `policy_allowed=true`
/ `size_multiplier>0` are unrealizable here by design and are NOT asserted; the
sizing fields are populated regardless of block status. The chain + decision
stages are left REAL so this reproduces the exact gate scenario with a tradable
symbol substituted for `^VIX`.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from cuttingboard import audit, config, runtime
from cuttingboard.delivery.payload import build_report_payload
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import (
    QualificationResult,
    QualificationSummary,
    TradeCandidate,
)
from cuttingboard.regime import AGGRESSIVE_LONG, RISK_ON, RegimeState
from cuttingboard.structure import StructureResult
from cuttingboard.validation import ValidationSummary
from cuttingboard.watch import WatchSummary


GATE_SYMBOL = "SPY"  # tradable: must NOT be in config.NON_TRADABLE_SYMBOLS
RUN_AT = datetime(2026, 4, 28, 13, 0, tzinfo=timezone.utc)

# Deterministic injected sizing inputs -> expected emitted values:
#   position_size   = QualificationResult.max_contracts  = 2
#   dollar_risk     = QualificationResult.dollar_risk     = 150.0
#   estimated_debit = OptionSetup.spread_width * 100       = 0.75 * 100 = 75.0
EXPECTED_POSITION_SIZE = 2
EXPECTED_DOLLAR_RISK = 150.0
EXPECTED_ESTIMATED_DEBIT = 75.0


def _null_context():
    class _Ctx:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    return lambda *args, **kwargs: _Ctx()


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
                symbol=GATE_SYMBOL,
                qualified=True,
                watchlist=False,
                direction="LONG",
                gates_passed=["REGIME"],
                gates_failed=[],
                hard_failure=None,
                watchlist_reason=None,
                max_contracts=EXPECTED_POSITION_SIZE,
                dollar_risk=EXPECTED_DOLLAR_RISK,
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
        symbol=GATE_SYMBOL,
        strategy="BULL_CALL_SPREAD",
        direction="LONG",
        structure="TREND",
        iv_environment="NORMAL_IV",
        long_strike="1_ITM",
        short_strike="ATM",
        strike_distance=5.0,
        spread_width=0.75,
        dte=21,
        max_contracts=EXPECTED_POSITION_SIZE,
        dollar_risk=EXPECTED_DOLLAR_RISK,
        exit_profit_pct=0.5,
        exit_loss="full_debit",
    )


def _candidate() -> TradeCandidate:
    return TradeCandidate(
        symbol=GATE_SYMBOL,
        direction="LONG",
        entry_price=100.0,
        stop_price=97.0,
        target_price=106.0,
        spread_width=0.75,
    )


def _inject_pipeline_stages(monkeypatch, tmp_path):
    """Inject a qualified tradable SPY through the pipeline; leave chain + decision
    + contract assembly REAL so the sizing passthrough is genuinely exercised."""
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(runtime, "LATEST_RUN_PATH", tmp_path / "logs" / "latest_run.json")
    monkeypatch.setattr(runtime, "LATEST_CONTRACT_PATH", str(tmp_path / "logs" / "latest_contract.json"))
    monkeypatch.setattr(audit, "AUDIT_LOG_PATH", str(tmp_path / "logs" / "audit.jsonl"))
    monkeypatch.setattr(runtime, "_deterministic_run_at", lambda mode, fixture_file: RUN_AT)
    monkeypatch.setattr(runtime, "_load_inputs", lambda mode, fixture_file: ({}, {}))
    monkeypatch.setattr(runtime, "_fixture_validation_clock", _null_context())
    monkeypatch.setattr(runtime, "validate_quotes", lambda *a, **k: _validation_summary())
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
    monkeypatch.setattr(runtime, "compute_all_derived", lambda quotes: {GATE_SYMBOL: object()})
    monkeypatch.setattr(runtime, "resolve_sector_router", lambda *a, **k: runtime.SectorRouterState(
        mode="MIXED",
        energy_score=0.0,
        index_score=0.0,
        computed_at_utc=RUN_AT,
        session_date="2026-04-28",
    ))
    monkeypatch.setattr(runtime, "classify_all_structure", lambda *a, **k: {
        GATE_SYMBOL: StructureResult(
            symbol=GATE_SYMBOL,
            structure="TREND",
            iv_environment="NORMAL_IV",
            is_tradeable=True,
            disqualification_reason=None,
        )
    })
    monkeypatch.setattr(runtime, "classify_watchlist", lambda *a, **k: WatchSummary(
        session="PREMARKET",
        threshold=0.0,
        watchlist=[],
        ignored_symbols=[],
        execution_posture="ACTIVE",
    ))
    monkeypatch.setattr(runtime, "generate_candidates", lambda *a, **k: {GATE_SYMBOL: _candidate()})
    monkeypatch.setattr(runtime, "fetch_ohlcv", lambda symbol: None)
    monkeypatch.setattr(runtime, "qualify_all", lambda *a, **k: _qualification_summary())
    monkeypatch.setattr(runtime, "_log_continuation_audit", lambda regime, summary: None)
    monkeypatch.setattr(runtime, "build_option_setups", lambda *a, **k: [_option_setup()])
    monkeypatch.setattr(runtime, "render_report", lambda **k: "report")
    monkeypatch.setattr(runtime, "_write_markdown_report", lambda report, date_str, sha: None)
    monkeypatch.setattr(runtime, "_load_run_history", lambda path: [])
    monkeypatch.setattr(runtime, "build_premarket_report", lambda contract: {})
    monkeypatch.setattr(runtime, "build_postmarket_report", lambda contract, history: {})
    monkeypatch.setattr(runtime, "run_post_trade_evaluation", lambda **k: None)
    monkeypatch.setattr(runtime, "build_market_map", lambda **k: {"symbols": {GATE_SYMBOL: {"watch_zones": []}}})


def _run_gate_top_trades(monkeypatch, tmp_path) -> list[dict]:
    """Drive the fixture pipeline and return payload `sections.top_trades`."""
    _inject_pipeline_stages(monkeypatch, tmp_path)
    result = runtime._run_pipeline(
        mode=runtime.MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-28"),
        fixture_file=Path("tests/fixtures/2026-04-12.json"),
    )
    payload = build_report_payload(result.contract, fixture_mode=True)
    return payload["sections"]["top_trades"]


def _gate_candidate(top_trades: list[dict]) -> dict:
    matches = [t for t in top_trades if t.get("symbol") == GATE_SYMBOL]
    assert matches, f"expected a {GATE_SYMBOL} candidate in top_trades, got {[t.get('symbol') for t in top_trades]}"
    return matches[0]


# --- AC1: a tradable candidate surfaces in top_trades --------------------------

def test_gate_candidate_is_tradable(monkeypatch, tmp_path):
    top_trades = _run_gate_top_trades(monkeypatch, tmp_path)
    candidate = _gate_candidate(top_trades)
    assert candidate["symbol"] == GATE_SYMBOL
    assert GATE_SYMBOL not in config.NON_TRADABLE_SYMBOLS


# --- AC2/AC3/AC4: sizing fields present, numeric, positive ---------------------

def test_sizing_fields_present_positive_numeric(monkeypatch, tmp_path):
    candidate = _gate_candidate(_run_gate_top_trades(monkeypatch, tmp_path))
    for field in ("position_size", "dollar_risk", "estimated_debit"):
        assert field in candidate, f"{field} missing from top_trades candidate"
        value = candidate[field]
        assert isinstance(value, (int, float)) and not isinstance(value, bool), f"{field} not numeric: {value!r}"
        assert value > 0, f"{field} not positive: {value!r}"


# --- AC5: sizing coherence within the dollar-risk cap, pinned values -----------

def test_sizing_coherence_within_risk_cap(monkeypatch, tmp_path):
    candidate = _gate_candidate(_run_gate_top_trades(monkeypatch, tmp_path))
    ps = candidate["position_size"]
    dr = candidate["dollar_risk"]
    ed = candidate["estimated_debit"]
    # Deterministic expected values from the injected qualification/option setup.
    assert ps == EXPECTED_POSITION_SIZE
    assert dr == EXPECTED_DOLLAR_RISK
    assert ed == EXPECTED_ESTIMATED_DEBIT
    # The gate's core coherence relation: total debit risked cannot exceed the cap.
    assert ps * ed <= dr


# --- AC6: deterministic across repeated runs -----------------------------------

def test_fixture_deterministic_across_runs(monkeypatch, tmp_path):
    first = _gate_candidate(_run_gate_top_trades(monkeypatch, tmp_path))
    second = _gate_candidate(_run_gate_top_trades(monkeypatch, tmp_path))
    keys = ("symbol", "position_size", "dollar_risk", "estimated_debit")
    assert {k: first[k] for k in keys} == {k: second[k] for k in keys}
