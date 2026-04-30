"""
Tests for the canonical pipeline output contract (PRD-011).

Acceptance criteria covered:
1. Successful run fixture → valid contract shape
2. STAY_FLAT fixture → status="STAY_FLAT", valid shape
3. Degraded/error fixture → status="ERROR", minimal valid shape
4. json.dumps succeeds with no custom encoder
5. Renderer smoke test using only contract fields
6. Regression: schema_version == "v2"
7. Required non-nullable fields are not null
8. trade_candidates is always a list
9. rejections is always a list
10. system_state, market_context, audit_summary, artifacts are always dicts
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

import pytest

from cuttingboard.contract import (
    SCHEMA_VERSION,
    STATUS_ERROR,
    STATUS_OK,
    STATUS_STAY_FLAT,
    assert_valid_contract,
    build_error_contract,
    build_pipeline_output_contract,
    derive_run_status,
)
from cuttingboard.chain_validation import ChainValidationResult, VALIDATED
from cuttingboard.options import OptionSetup
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.output import OUTCOME_HALT, OUTCOME_NO_TRADE, render_report
from cuttingboard.qualification import (
    ENTRY_MODE_DIRECT,
    QualificationResult,
    QualificationSummary,
)
from cuttingboard.regime import (
    AGGRESSIVE_LONG,
    EXPANSION,
    EXPANSION_LONG,
    NEUTRAL,
    RISK_ON,
    STAY_FLAT,
    RegimeState,
)
from cuttingboard.validation import ValidationSummary
from cuttingboard.trade_decision import TradeDecision, ALLOW_TRADE, BLOCK_TRADE


# ---------------------------------------------------------------------------
# Minimal fake objects
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 4, 23, 14, 0, 0, tzinfo=timezone.utc)


def _quote(symbol: str, price: float, pct_change_decimal: float) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=pct_change_decimal,
        volume=1_000_000.0,
        fetched_at_utc=_NOW,
        source="fixture",
        units=(
            "yield_pct"
            if symbol == "^TNX"
            else "usd_price" if symbol == "BTC-USD" else "index_level"
        ),
        age_seconds=0.0,
    )


def _macro_quotes() -> dict[str, NormalizedQuote]:
    return {
        "^VIX": _quote("^VIX", 18.5, -0.02),
        "DX-Y.NYB": _quote("DX-Y.NYB", 104.0, 0.001),
        "^TNX": _quote("^TNX", 4.3, -0.003),
        "BTC-USD": _quote("BTC-USD", 65000.0, 0.015),
    }


def _regime(
    regime: str = RISK_ON,
    posture: str = AGGRESSIVE_LONG,
    confidence: float = 0.75,
    vix_level: float = 16.0,
    vix_pct_change: float = -0.02,
) -> RegimeState:
    return RegimeState(
        regime=regime,
        posture=posture,
        confidence=confidence,
        net_score=4,
        risk_on_votes=5,
        risk_off_votes=1,
        neutral_votes=2,
        total_votes=8,
        vote_breakdown={},
        vix_level=vix_level,
        vix_pct_change=vix_pct_change,
        computed_at_utc=_NOW,
    )


def _val_summary(halted: bool = False) -> ValidationSummary:
    return ValidationSummary(
        symbols_validated=5,
        symbols_attempted=5,
        symbols_failed=0,
        valid_quotes={},
        invalid_symbols={},
        results={},
        failed_halt_symbols=["^VIX"] if halted else [],
        system_halted=halted,
        halt_reason="TEST_HALT" if halted else None,
    )


def _qual_summary(
    qualified: int = 0,
    excluded: Optional[dict] = None,
    regime_short_circuited: bool = False,
    regime_failure_reason: Optional[str] = None,
) -> QualificationSummary:
    qualified_trades = []
    if qualified > 0:
        qualified_trades = [
            QualificationResult(
                symbol="SPY",
                qualified=True,
                watchlist=False,
                direction="LONG",
                gates_passed=["REGIME", "CONFIDENCE", "DIRECTION", "STRUCTURE"],
                gates_failed=[],
                hard_failure=None,
                watchlist_reason=None,
                max_contracts=2,
                dollar_risk=150.0,
                entry_mode=ENTRY_MODE_DIRECT,
            )
        ]
    return QualificationSummary(
        regime_passed=not regime_short_circuited,
        regime_short_circuited=regime_short_circuited,
        regime_failure_reason=regime_failure_reason,
        qualified_trades=qualified_trades,
        watchlist=[],
        excluded=excluded or {},
        symbols_evaluated=3,
        symbols_qualified=len(qualified_trades),
        symbols_watchlist=0,
        symbols_excluded=len(excluded or {}),
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


def _chain_result(symbol: str = "SPY", classification: str = VALIDATED, reason: str | None = None) -> ChainValidationResult:
    return ChainValidationResult(
        symbol=symbol,
        classification=classification,
        reason=reason,
        spread_pct=None,
        open_interest=None,
        volume=None,
        expiry_used=None,
        data_source=None,
    )


def _trade_decision(symbol: str = "SPY", status: str = ALLOW_TRADE, block_reason: str | None = None) -> TradeDecision:
    reason = "TOP_TRADE_VALIDATED" if status == ALLOW_TRADE else block_reason
    return TradeDecision(
        ticker=symbol,
        direction="LONG",
        status=status,
        entry=100.0,
        stop=97.0,
        target=106.0,
        r_r=2.0,
        contracts=2,
        dollar_risk=150.0,
        block_reason=block_reason,
        decision_trace={
            "stage": "CHAIN_VALIDATION",
            "source": "chain_validation",
            "reason": reason,
        },
    )


class _FakePipelineResult:
    """Duck-typed stand-in for PipelineResult."""

    def __init__(
        self,
        *,
        mode: str = "fixture",
        run_at_utc: datetime = _NOW,
        date_str: str = "2026-04-23",
        regime: Optional[RegimeState] = None,
        router_mode: str = "MIXED",
        qualification_summary: Optional[QualificationSummary] = None,
        watch_summary: Any = None,
        option_setups: list = (),
        chain_results: dict = (),
        validation_summary: Optional[ValidationSummary] = None,
        normalized_quotes: dict | None = None,
        raw_quotes: dict = (),
        alert_sent: bool = False,
        report_path: str = "reports/2026-04-23.md",
        errors: list = (),
        trade_decisions: list = (),
    ):
        self.mode = mode
        self.run_at_utc = run_at_utc
        self.date_str = date_str
        self.regime = regime
        self.router_mode = router_mode
        self.qualification_summary = qualification_summary
        self.watch_summary = watch_summary
        self.option_setups = list(option_setups)
        self.chain_results = dict(chain_results)
        self.trade_decisions = list(trade_decisions)
        self.validation_summary = validation_summary or _val_summary()
        self.normalized_quotes = dict(_macro_quotes() if normalized_quotes is None else normalized_quotes)
        self.raw_quotes = dict(raw_quotes)
        self.alert_sent = alert_sent
        self.report_path = report_path
        self.errors = list(errors)


def _build(pr, status=STATUS_OK, **kwargs) -> dict:
    return build_pipeline_output_contract(
        pr,
        generated_at=_NOW,
        status=status,
        artifacts={"log_path": "logs/latest_run.json"},
        **kwargs,
    )


# ---------------------------------------------------------------------------
# 1. Successful run → valid shape
# ---------------------------------------------------------------------------

class TestSuccessfulRun:
    def setup_method(self):
        self.pr = _FakePipelineResult(
            regime=_regime(),
            qualification_summary=_qual_summary(qualified=1),
            option_setups=[_option_setup()],
            chain_results={"SPY": _chain_result()},
            trade_decisions=[_trade_decision()],
        )
        self.contract = _build(self.pr)

    def test_required_top_level_keys(self):
        required = {
            "schema_version", "generated_at", "session_date", "mode", "status",
            "timezone", "system_state", "market_context", "trade_candidates",
            "rejections", "audit_summary", "artifacts", "correlation", "regime",
            "macro_drivers",
        }
        assert required == set(self.contract), (
            f"Missing: {required - set(self.contract)}, "
            f"Extra: {set(self.contract) - required}"
        )

    def test_schema_version_is_v2(self):
        assert self.contract["schema_version"] == "v2"

    def test_status_ok(self):
        assert self.contract["status"] == STATUS_OK

    def test_trade_candidates_is_list(self):
        assert isinstance(self.contract["trade_candidates"], list)

    def test_rejections_is_list(self):
        assert isinstance(self.contract["rejections"], list)

    def test_system_state_is_dict(self):
        assert isinstance(self.contract["system_state"], dict)

    def test_market_context_is_dict(self):
        assert isinstance(self.contract["market_context"], dict)

    def test_audit_summary_is_dict(self):
        assert isinstance(self.contract["audit_summary"], dict)

    def test_artifacts_is_dict(self):
        assert isinstance(self.contract["artifacts"], dict)

    def test_tradable_is_bool(self):
        assert isinstance(self.contract["system_state"]["tradable"], bool)

    def test_json_serializable(self):
        json.dumps(self.contract)  # must not raise

    def test_assert_valid_contract_passes(self):
        assert_valid_contract(self.contract)  # must not raise

    def test_trade_candidate_materialized_from_trade_decision(self):
        candidate = self.contract["trade_candidates"][0]
        assert candidate["entry"] == 100.0
        assert candidate["stop"] == 97.0
        assert candidate["target"] == 106.0
        assert candidate["risk_reward"] == 2.0
        assert candidate["decision_status"] == ALLOW_TRADE
        assert candidate["block_reason"] is None
        assert candidate["policy_allowed"] is True
        assert candidate["policy_reason"] == "policy_not_evaluated"
        assert candidate["size_multiplier"] == 1.0
        assert candidate["decision_trace"] == {
            "stage": "CHAIN_VALIDATION",
            "source": "chain_validation",
            "reason": "TOP_TRADE_VALIDATED",
        }
        assert "overnight_policy" not in candidate

    def test_optional_overnight_policy_is_validated(self):
        candidate = self.contract["trade_candidates"][0]
        candidate["overnight_policy"] = {
            "decision": "ALLOW_HOLD",
            "reason": "PASS_ALL",
        }

        assert_valid_contract(self.contract)

    def test_invalid_overnight_policy_fails_validation(self):
        candidate = self.contract["trade_candidates"][0]
        candidate["overnight_policy"] = {
            "decision": "ALLOW_HOLD",
            "reason": "BROKEN",
        }

        with pytest.raises(AssertionError, match="overnight_policy.reason"):
            assert_valid_contract(self.contract)


# ---------------------------------------------------------------------------
# 2. STAY_FLAT → status="STAY_FLAT", valid shape
# ---------------------------------------------------------------------------

class TestStayFlatRun:
    def setup_method(self):
        flat_regime = _regime(regime=NEUTRAL, posture=STAY_FLAT, confidence=0.4)
        self.pr = _FakePipelineResult(
            regime=flat_regime,
            qualification_summary=_qual_summary(
                regime_short_circuited=True,
                regime_failure_reason="STAY_FLAT_LOW_CONF",
            ),
        )
        self.contract = _build(self.pr, status=STATUS_STAY_FLAT)

    def test_status_is_stay_flat(self):
        assert self.contract["status"] == STATUS_STAY_FLAT

    def test_required_keys_present(self):
        assert_valid_contract(self.contract)

    def test_tradable_false(self):
        assert self.contract["system_state"]["tradable"] is False

    def test_trade_candidates_empty(self):
        assert self.contract["trade_candidates"] == []

    def test_json_serializable(self):
        json.dumps(self.contract)


# ---------------------------------------------------------------------------
# 3. Degraded/error path
# ---------------------------------------------------------------------------

class TestErrorContract:
    def setup_method(self):
        self.contract = build_error_contract(
            generated_at=_NOW,
            artifacts={"log_path": "logs/latest_run.json"},
            error_detail="connection timeout",
        )

    def test_status_is_error(self):
        assert self.contract["status"] == STATUS_ERROR

    def test_required_keys_present(self):
        assert_valid_contract(self.contract)

    def test_schema_version_v2(self):
        assert self.contract["schema_version"] == "v2"

    def test_trade_candidates_empty(self):
        assert self.contract["trade_candidates"] == []

    def test_rejections_empty(self):
        assert self.contract["rejections"] == []

    def test_json_serializable(self):
        json.dumps(self.contract)

    def test_error_count_nonzero(self):
        assert self.contract["audit_summary"]["error_count"] == 1


# ---------------------------------------------------------------------------
# 4. JSON serialization – no custom encoder
# ---------------------------------------------------------------------------

def test_no_custom_encoder_needed():
    pr = _FakePipelineResult(regime=_regime(), qualification_summary=_qual_summary())
    contract = _build(pr)
    # Must succeed with stdlib json and no default= argument
    serialized = json.dumps(contract)
    assert isinstance(serialized, str)
    roundtripped = json.loads(serialized)
    assert roundtripped["schema_version"] == SCHEMA_VERSION


def test_no_datetime_in_contract():
    pr = _FakePipelineResult(regime=_regime())
    contract = _build(pr)

    def _check_no_datetime(obj, path=""):
        if isinstance(obj, datetime):
            raise AssertionError(f"datetime leaked at {path!r}: {obj!r}")
        if isinstance(obj, dict):
            for k, v in obj.items():
                _check_no_datetime(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _check_no_datetime(v, f"{path}[{i}]")

    _check_no_datetime(contract)


def test_no_non_json_types():
    pr = _FakePipelineResult(regime=_regime())
    contract = _build(pr)

    def _check(obj, path=""):
        allowed = (str, int, float, bool, list, dict, type(None))
        if not isinstance(obj, allowed):
            raise AssertionError(f"Non-JSON type {type(obj).__name__} at {path!r}")
        if isinstance(obj, dict):
            for k, v in obj.items():
                _check(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _check(v, f"{path}[{i}]")

    _check(contract)


# ---------------------------------------------------------------------------
# 5. Renderer smoke test – render_report uses contract fields
# ---------------------------------------------------------------------------

def test_render_report_no_crash():
    from cuttingboard.output import OUTCOME_NO_TRADE
    report = render_report(
        date_str="2026-04-23",
        run_at_utc=_NOW,
        regime=_regime(),
        validation_summary=_val_summary(),
        qualification_summary=_qual_summary(),
        option_setups=[],
        outcome=OUTCOME_NO_TRADE,
    )
    assert isinstance(report, str)
    assert len(report) > 0


def test_render_report_stay_flat_no_crash():
    from cuttingboard.output import OUTCOME_NO_TRADE
    flat_regime = _regime(regime=NEUTRAL, posture=STAY_FLAT, confidence=0.4)
    qual = _qual_summary(
        regime_short_circuited=True, regime_failure_reason="STAY_FLAT_LOW_CONF"
    )
    report = render_report(
        date_str="2026-04-23",
        run_at_utc=_NOW,
        regime=flat_regime,
        validation_summary=_val_summary(),
        qualification_summary=qual,
        option_setups=[],
        outcome=OUTCOME_NO_TRADE,
    )
    assert isinstance(report, str)


# ---------------------------------------------------------------------------
# 6. Schema version invariant
# ---------------------------------------------------------------------------

def test_schema_version_always_v2():
    for status in (STATUS_OK, STATUS_STAY_FLAT):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr, status=status)
        assert contract["schema_version"] == "v2", f"Failed for status={status}"


def test_error_contract_schema_version_v2():
    contract = build_error_contract(generated_at=_NOW, artifacts={})
    assert contract["schema_version"] == "v2"


# ---------------------------------------------------------------------------
# 7. Required non-nullable fields are never null
# ---------------------------------------------------------------------------

def test_required_non_nullable_fields():
    pr = _FakePipelineResult(regime=_regime())
    contract = _build(pr)

    # Fields that must never be null per PRD
    assert contract["schema_version"] is not None
    assert contract["generated_at"] is not None
    assert contract["status"] is not None
    assert contract["timezone"] is not None
    assert contract["system_state"] is not None
    assert contract["market_context"] is not None
    assert contract["trade_candidates"] is not None
    assert contract["rejections"] is not None
    assert contract["audit_summary"] is not None
    assert contract["artifacts"] is not None
    assert contract["system_state"]["tradable"] is not None


# ---------------------------------------------------------------------------
# 8 & 9. trade_candidates and rejections always lists
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("qualified,excluded", [
    (0, {}),
    (1, {}),
    (0, {"NVDA": "CHOP"}),
])
def test_trade_candidates_and_rejections_always_lists(qualified, excluded):
    pr = _FakePipelineResult(
        regime=_regime(),
        qualification_summary=_qual_summary(qualified=qualified, excluded=excluded),
        option_setups=[_option_setup()] if qualified else [],
        chain_results={"SPY": _chain_result()} if qualified else {},
        trade_decisions=[_trade_decision()] if qualified else [],
    )
    contract = _build(pr)
    assert isinstance(contract["trade_candidates"], list)
    assert isinstance(contract["rejections"], list)


def test_trade_candidates_empty_when_no_qual():
    pr = _FakePipelineResult()
    contract = _build(pr)
    assert contract["trade_candidates"] == []


# ---------------------------------------------------------------------------
# 10. system_state / market_context / audit_summary / artifacts always dicts
# ---------------------------------------------------------------------------

def test_required_sections_always_dicts():
    for halted in (False, True):
        pr = _FakePipelineResult(
            regime=None if halted else _regime(),
            validation_summary=_val_summary(halted=halted),
        )
        status = STATUS_STAY_FLAT if halted else STATUS_OK
        contract = _build(pr, status=status)
        assert isinstance(contract["system_state"], dict)
        assert isinstance(contract["market_context"], dict)
        assert isinstance(contract["audit_summary"], dict)
        assert isinstance(contract["artifacts"], dict)


# ---------------------------------------------------------------------------
# derive_run_status
# ---------------------------------------------------------------------------

def test_derive_run_status_halted():
    assert derive_run_status(OUTCOME_NO_TRADE, None, system_halted=True) == STATUS_STAY_FLAT


def test_derive_run_status_stay_flat_posture():
    flat_regime = _regime(regime=NEUTRAL, posture=STAY_FLAT)
    assert derive_run_status(OUTCOME_NO_TRADE, flat_regime, system_halted=False) == STATUS_STAY_FLAT


def test_derive_run_status_ok():
    ok_regime = _regime()
    assert derive_run_status(OUTCOME_NO_TRADE, ok_regime, system_halted=False) == STATUS_OK


def test_derive_run_status_halt_outcome():
    assert derive_run_status(OUTCOME_HALT, None, system_halted=False) == STATUS_STAY_FLAT


# ---------------------------------------------------------------------------
# Rejection taxonomy
# ---------------------------------------------------------------------------

def test_rejections_use_canonical_reason():
    qual = _qual_summary(excluded={"TSLA": "CHOP", "NVDA": "direction_mismatch"})
    pr = _FakePipelineResult(regime=_regime(), qualification_summary=qual)
    contract = _build(pr)
    rejection_reasons = {r["reason"] for r in contract["rejections"]}
    assert "CHOP" in rejection_reasons
    assert "direction_mismatch" in rejection_reasons


def test_regime_rejection_included_when_short_circuited():
    qual = _qual_summary(
        regime_short_circuited=True, regime_failure_reason="STAY_FLAT_LOW_CONF"
    )
    pr = _FakePipelineResult(regime=_regime(), qualification_summary=qual)
    contract = _build(pr)
    regime_rejections = [r for r in contract["rejections"] if r["stage"] == "REGIME"]
    assert len(regime_rejections) == 1
    assert regime_rejections[0]["reason"] == "STAY_FLAT_LOW_CONF"


# ---------------------------------------------------------------------------
# Audit summary counts
# ---------------------------------------------------------------------------

def test_audit_summary_counts_nonnegative():
    qual = _qual_summary(qualified=1, excluded={"TSLA": "CHOP"})
    pr = _FakePipelineResult(regime=_regime(), qualification_summary=qual)
    contract = _build(pr)
    audit = contract["audit_summary"]
    assert audit["qualified_count"] >= 0
    assert audit["rejected_count"] >= 0
    assert isinstance(audit["continuation_audit_present"], bool)
    assert audit["error_count"] >= 0


# ---------------------------------------------------------------------------
# assert_valid_contract detects violations
# ---------------------------------------------------------------------------

def test_assert_fails_missing_key():
    pr = _FakePipelineResult(regime=_regime())
    contract = _build(pr)
    del contract["schema_version"]
    with pytest.raises(AssertionError, match="schema_version"):
        assert_valid_contract(contract)


def test_assert_fails_wrong_schema_version():
    pr = _FakePipelineResult(regime=_regime())
    contract = _build(pr)
    contract["schema_version"] = "v1"
    with pytest.raises(AssertionError, match="v2"):
        assert_valid_contract(contract)


def test_assert_fails_invalid_status():
    pr = _FakePipelineResult(regime=_regime())
    contract = _build(pr)
    contract["status"] = "INVALID"
    with pytest.raises(AssertionError, match="status"):
        assert_valid_contract(contract)


def test_assert_fails_missing_trade_candidate_decision_status():
    pr = _FakePipelineResult(
        regime=_regime(),
        qualification_summary=_qual_summary(qualified=1),
        option_setups=[_option_setup()],
        chain_results={"SPY": _chain_result()},
        trade_decisions=[_trade_decision()],
    )
    contract = _build(pr)
    del contract["trade_candidates"][0]["decision_status"]
    with pytest.raises(AssertionError, match="decision_status"):
        assert_valid_contract(contract)


def test_assert_fails_allow_trade_with_nonfinite_numeric_field():
    pr = _FakePipelineResult(
        regime=_regime(),
        qualification_summary=_qual_summary(qualified=1),
        option_setups=[_option_setup()],
        chain_results={"SPY": _chain_result()},
        trade_decisions=[_trade_decision()],
    )
    contract = _build(pr)
    contract["trade_candidates"][0]["entry"] = float("inf")
    with pytest.raises(AssertionError, match="entry"):
        assert_valid_contract(contract)


def test_assert_fails_block_trade_without_block_reason():
    pr = _FakePipelineResult(
        regime=_regime(),
        qualification_summary=_qual_summary(qualified=1),
        option_setups=[_option_setup()],
        chain_results={"SPY": _chain_result(classification="NEEDS_MANUAL_CHECK", reason="needs broker review")},
        trade_decisions=[_trade_decision(status=BLOCK_TRADE, block_reason="needs broker review")],
    )
    contract = _build(pr)
    contract["trade_candidates"][0]["block_reason"] = None
    with pytest.raises(AssertionError, match="block_reason"):
        assert_valid_contract(contract)


def test_assert_fails_missing_decision_trace():
    pr = _FakePipelineResult(
        regime=_regime(),
        qualification_summary=_qual_summary(qualified=1),
        option_setups=[_option_setup()],
        chain_results={"SPY": _chain_result()},
        trade_decisions=[_trade_decision()],
    )
    contract = _build(pr)
    del contract["trade_candidates"][0]["decision_trace"]
    with pytest.raises(AssertionError, match="decision_trace"):
        assert_valid_contract(contract)


def test_assert_fails_block_reason_trace_mismatch():
    pr = _FakePipelineResult(
        regime=_regime(),
        qualification_summary=_qual_summary(qualified=1),
        option_setups=[_option_setup()],
        chain_results={"SPY": _chain_result(classification="NEEDS_MANUAL_CHECK", reason="needs broker review")},
        trade_decisions=[_trade_decision(status=BLOCK_TRADE, block_reason="needs broker review")],
    )
    contract = _build(pr)
    contract["trade_candidates"][0]["decision_trace"]["reason"] = "different reason"
    with pytest.raises(AssertionError, match="block_reason"):
        assert_valid_contract(contract)


def test_assert_fails_missing_trade_candidate_policy_fields():
    contract = build_pipeline_output_contract(
        _FakePipelineResult(
            qualification_summary=_qual_summary(qualified=1),
            option_setups=[_option_setup()],
            chain_results={"SPY": _chain_result()},
            trade_decisions=[_trade_decision()],
        ),
        generated_at=_NOW,
        status=STATUS_OK,
        artifacts={},
    )
    del contract["trade_candidates"][0]["policy_allowed"]
    with pytest.raises(AssertionError, match="policy_allowed"):
        assert_valid_contract(contract)


def test_assert_fails_policy_block_with_allow_trade():
    contract = build_pipeline_output_contract(
        _FakePipelineResult(
            qualification_summary=_qual_summary(qualified=1),
            option_setups=[_option_setup()],
            chain_results={"SPY": _chain_result()},
            trade_decisions=[_trade_decision()],
        ),
        generated_at=_NOW,
        status=STATUS_OK,
        artifacts={},
    )
    contract["trade_candidates"][0]["policy_allowed"] = False
    with pytest.raises(AssertionError, match="policy_allowed"):
        assert_valid_contract(contract)


def test_assert_fails_allow_trade_trace_reason_mismatch():
    pr = _FakePipelineResult(
        regime=_regime(),
        qualification_summary=_qual_summary(qualified=1),
        option_setups=[_option_setup()],
        chain_results={"SPY": _chain_result()},
        trade_decisions=[_trade_decision()],
    )
    contract = _build(pr)
    contract["trade_candidates"][0]["decision_trace"]["reason"] = "wrong"
    with pytest.raises(AssertionError, match="TOP_TRADE_VALIDATED"):
        assert_valid_contract(contract)


# ---------------------------------------------------------------------------
# PRD-023 — Correlation block
# ---------------------------------------------------------------------------

def _make_correlation(state: str = "ALIGNED") -> Any:
    from cuttingboard.correlation import CorrelationResult
    from cuttingboard import config
    score = {"ALIGNED": 1, "NEUTRAL": 0, "CONFLICT": -1}[state]
    modifier = {
        "ALIGNED":  config.CORRELATION_RISK_MODIFIER_ALIGNED,
        "NEUTRAL":  config.CORRELATION_RISK_MODIFIER_NEUTRAL,
        "CONFLICT": config.CORRELATION_RISK_MODIFIER_CONFLICT,
    }[state]
    return CorrelationResult(
        gold_symbol="GLD",
        dollar_symbol="DX-Y.NYB",
        state=state,
        score=score,
        risk_modifier=modifier,
    )


class TestCorrelationBlock:
    def test_correlation_key_present_when_none(self):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr)
        assert "correlation" in contract

    def test_correlation_none_when_not_set(self):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr)
        assert contract["correlation"] is None

    def test_correlation_block_with_aligned(self):
        class _PRWithCorr(_FakePipelineResult):
            correlation = _make_correlation("ALIGNED")

        pr = _PRWithCorr(regime=_regime())
        contract = _build(pr)
        corr = contract["correlation"]
        assert corr["state"] == "ALIGNED"
        assert corr["score"] == 1
        assert corr["gold_symbol"] == "GLD"
        assert corr["dollar_symbol"] == "DX-Y.NYB"
        assert isinstance(corr["risk_modifier"], float)

    def test_correlation_block_with_neutral(self):
        class _PRWithCorr(_FakePipelineResult):
            correlation = _make_correlation("NEUTRAL")

        pr = _PRWithCorr(regime=_regime())
        contract = _build(pr)
        corr = contract["correlation"]
        assert corr["state"] == "NEUTRAL"
        assert corr["score"] == 0

    def test_correlation_block_with_conflict(self):
        class _PRWithCorr(_FakePipelineResult):
            correlation = _make_correlation("CONFLICT")

        pr = _PRWithCorr(regime=_regime())
        contract = _build(pr)
        corr = contract["correlation"]
        assert corr["state"] == "CONFLICT"
        assert corr["score"] == -1

    def test_assert_valid_contract_passes_with_correlation(self):
        class _PRWithCorr(_FakePipelineResult):
            correlation = _make_correlation("ALIGNED")

        pr = _PRWithCorr(regime=_regime())
        contract = _build(pr)
        assert_valid_contract(contract)

    def test_assert_fails_invalid_correlation_state(self):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr)
        contract["correlation"] = {
            "gold_symbol": "GLD",
            "dollar_symbol": "DX-Y.NYB",
            "state": "UNKNOWN",
            "score": 0,
            "risk_modifier": 1.0,
        }
        with pytest.raises(AssertionError, match="state"):
            assert_valid_contract(contract)

    def test_assert_fails_missing_correlation_key(self):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr)
        del contract["correlation"]
        with pytest.raises(AssertionError, match="correlation"):
            assert_valid_contract(contract)

    def test_correlation_json_serializable(self):
        class _PRWithCorr(_FakePipelineResult):
            correlation = _make_correlation("CONFLICT")

        pr = _PRWithCorr(regime=_regime())
        contract = _build(pr)
        json.dumps(contract)  # must not raise

    def test_error_contract_correlation_is_none(self):
        contract = build_error_contract(generated_at=_NOW, artifacts={})
        assert "correlation" in contract
        assert contract["correlation"] is None
        assert_valid_contract(contract)


# ---------------------------------------------------------------------------
# PRD-035 — Regime block
# ---------------------------------------------------------------------------

_REGIME_KEYS = {
    "classification", "posture", "confidence", "net_score",
    "risk_on_votes", "risk_off_votes", "neutral_votes", "total_votes",
    "vote_breakdown", "vix_level", "vix_pct_change",
}

_CANONICAL_VOTE_KEYS = [
    "SPY pct_change",
    "QQQ pct_change",
    "IWM pct_change",
    "VIX level",
    "VIX pct_change",
    "DXY pct_change",
    "TNX pct_change",
    "BTC pct_change",
]


def _regime_with_votes() -> RegimeState:
    breakdown = {k: "RISK_ON" for k in _CANONICAL_VOTE_KEYS}
    return RegimeState(
        regime=RISK_ON,
        posture=AGGRESSIVE_LONG,
        confidence=0.875,
        net_score=7,
        risk_on_votes=7,
        risk_off_votes=0,
        neutral_votes=1,
        total_votes=8,
        vote_breakdown=breakdown,
        vix_level=16.5,
        vix_pct_change=-0.042,
        computed_at_utc=_NOW,
    )


class TestRegimeBlock:
    def test_regime_key_present(self):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr)
        assert "regime" in contract

    def test_regime_has_exact_keys(self):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr)
        assert set(contract["regime"]) == _REGIME_KEYS

    def test_regime_values_correct_types(self):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr)
        r = contract["regime"]
        assert isinstance(r["classification"], str)
        assert isinstance(r["posture"], str)
        assert isinstance(r["confidence"], float)
        assert isinstance(r["net_score"], int)
        assert isinstance(r["risk_on_votes"], int)
        assert isinstance(r["risk_off_votes"], int)
        assert isinstance(r["neutral_votes"], int)
        assert isinstance(r["total_votes"], int)
        assert isinstance(r["vote_breakdown"], dict)

    def test_regime_null_when_no_regime(self):
        pr = _FakePipelineResult(regime=None)
        contract = _build(pr)
        assert contract["regime"] is None

    def test_error_contract_regime_is_null(self):
        contract = build_error_contract(generated_at=_NOW, artifacts={})
        assert "regime" in contract
        assert contract["regime"] is None

    def test_regime_classification_matches_regime_state(self):
        pr = _FakePipelineResult(regime=_regime(regime=RISK_ON))
        contract = _build(pr)
        assert contract["regime"]["classification"] == RISK_ON

    def test_regime_posture_matches_regime_state(self):
        pr = _FakePipelineResult(regime=_regime(posture=AGGRESSIVE_LONG))
        contract = _build(pr)
        assert contract["regime"]["posture"] == AGGRESSIVE_LONG

    def test_regime_confidence_matches(self):
        pr = _FakePipelineResult(regime=_regime(confidence=0.75))
        contract = _build(pr)
        assert contract["regime"]["confidence"] == 0.75

    def test_vix_fields_populated(self):
        pr = _FakePipelineResult(regime=_regime(vix_level=19.4, vix_pct_change=-0.042))
        contract = _build(pr)
        assert contract["regime"]["vix_level"] == 19.4
        assert contract["regime"]["vix_pct_change"] == pytest.approx(-0.042)

    def test_vix_fields_null_when_none(self):
        pr = _FakePipelineResult(regime=_regime(vix_level=None, vix_pct_change=None))
        contract = _build(pr)
        assert contract["regime"]["vix_level"] is None
        assert contract["regime"]["vix_pct_change"] is None

    def test_vote_breakdown_preserves_keys(self):
        pr = _FakePipelineResult(regime=_regime_with_votes())
        contract = _build(pr)
        assert list(contract["regime"]["vote_breakdown"]) == _CANONICAL_VOTE_KEYS

    def test_total_votes_matches_vote_breakdown_count(self):
        pr = _FakePipelineResult(regime=_regime_with_votes())
        contract = _build(pr)
        r = contract["regime"]
        assert r["total_votes"] == len(r["vote_breakdown"])

    def test_regime_json_serializable(self):
        pr = _FakePipelineResult(regime=_regime_with_votes())
        contract = _build(pr)
        json.dumps(contract)

    def test_assert_valid_contract_passes_with_regime(self):
        pr = _FakePipelineResult(regime=_regime_with_votes())
        contract = _build(pr)
        assert_valid_contract(contract)

    def test_assert_valid_contract_passes_with_null_regime(self):
        pr = _FakePipelineResult(regime=None)
        contract = _build(pr)
        assert_valid_contract(contract)

    def test_assert_fails_missing_regime_key(self):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr)
        del contract["regime"]
        with pytest.raises(AssertionError, match="regime"):
            assert_valid_contract(contract)

    def test_assert_fails_regime_missing_subkey(self):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr)
        del contract["regime"]["confidence"]
        with pytest.raises(AssertionError):
            assert_valid_contract(contract)

    def test_assert_fails_regime_extra_subkey(self):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr)
        contract["regime"]["extra_field"] = "bad"
        with pytest.raises(AssertionError):
            assert_valid_contract(contract)

    def test_expansion_regime_valid(self):
        exp_regime = RegimeState(
            regime=EXPANSION,
            posture=EXPANSION_LONG,
            confidence=1.0,
            net_score=0,
            risk_on_votes=0,
            risk_off_votes=0,
            neutral_votes=0,
            total_votes=0,
            vote_breakdown={},
            vix_level=14.2,
            vix_pct_change=-0.05,
            computed_at_utc=_NOW,
        )
        pr = _FakePipelineResult(regime=exp_regime)
        contract = _build(pr)
        r = contract["regime"]
        assert r["classification"] == EXPANSION
        assert r["posture"] == EXPANSION_LONG
        assert r["total_votes"] == 0
        assert r["vote_breakdown"] == {}
        assert_valid_contract(contract)
