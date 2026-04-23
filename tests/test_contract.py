"""
Tests for the canonical pipeline output contract (PRD-011).

Acceptance criteria covered:
1. Successful run fixture → valid contract shape
2. STAY_FLAT fixture → status="STAY_FLAT", valid shape
3. Degraded/error fixture → status="ERROR", minimal valid shape
4. json.dumps succeeds with no custom encoder
5. Renderer smoke test using only contract fields
6. Regression: schema_version == "v1"
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
from cuttingboard.output import OUTCOME_HALT, OUTCOME_NO_TRADE, OUTCOME_TRADE, render_report
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


# ---------------------------------------------------------------------------
# Minimal fake objects
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 4, 23, 14, 0, 0, tzinfo=timezone.utc)


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
        normalized_quotes: dict = (),
        raw_quotes: dict = (),
        alert_sent: bool = False,
        report_path: str = "reports/2026-04-23.md",
        errors: list = (),
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
        self.validation_summary = validation_summary or _val_summary()
        self.normalized_quotes = dict(normalized_quotes)
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
        )
        self.contract = _build(self.pr)

    def test_required_top_level_keys(self):
        required = {
            "schema_version", "generated_at", "session_date", "mode", "status",
            "timezone", "system_state", "market_context", "trade_candidates",
            "rejections", "audit_summary", "artifacts",
        }
        assert required == set(self.contract), (
            f"Missing: {required - set(self.contract)}, "
            f"Extra: {set(self.contract) - required}"
        )

    def test_schema_version_is_v1(self):
        assert self.contract["schema_version"] == "v1"

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

    def test_schema_version_v1(self):
        assert self.contract["schema_version"] == "v1"

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

def test_render_report_accepts_contract():
    from cuttingboard.output import OUTCOME_NO_TRADE, render_report
    pr = _FakePipelineResult(regime=_regime(), qualification_summary=_qual_summary())
    contract = _build(pr)

    report = render_report(
        date_str="2026-04-23",
        run_at_utc=_NOW,
        regime=_regime(),
        validation_summary=_val_summary(),
        qualification_summary=_qual_summary(),
        option_setups=[],
        outcome=OUTCOME_NO_TRADE,
        contract=contract,
    )
    assert isinstance(report, str)
    assert len(report) > 0


def test_render_report_stay_flat_no_crash():
    from cuttingboard.output import OUTCOME_NO_TRADE, render_report
    flat_regime = _regime(regime=NEUTRAL, posture=STAY_FLAT, confidence=0.4)
    qual = _qual_summary(
        regime_short_circuited=True, regime_failure_reason="STAY_FLAT_LOW_CONF"
    )
    contract = build_error_contract(
        generated_at=_NOW,
        artifacts={},
        error_detail="STAY_FLAT",
    )
    # Must not crash even with empty trade_candidates / rejections
    report = render_report(
        date_str="2026-04-23",
        run_at_utc=_NOW,
        regime=flat_regime,
        validation_summary=_val_summary(),
        qualification_summary=qual,
        option_setups=[],
        outcome=OUTCOME_NO_TRADE,
        contract=contract,
    )
    assert isinstance(report, str)


# ---------------------------------------------------------------------------
# 6. Schema version invariant
# ---------------------------------------------------------------------------

def test_schema_version_always_v1():
    for status in (STATUS_OK, STATUS_STAY_FLAT):
        pr = _FakePipelineResult(regime=_regime())
        contract = _build(pr, status=status)
        assert contract["schema_version"] == "v1", f"Failed for status={status}"


def test_error_contract_schema_version_v1():
    contract = build_error_contract(generated_at=_NOW, artifacts={})
    assert contract["schema_version"] == "v1"


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
    contract["schema_version"] = "v2"
    with pytest.raises(AssertionError, match="v1"):
        assert_valid_contract(contract)


def test_assert_fails_invalid_status():
    pr = _FakePipelineResult(regime=_regime())
    contract = _build(pr)
    contract["status"] = "INVALID"
    with pytest.raises(AssertionError, match="status"):
        assert_valid_contract(contract)
