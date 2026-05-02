"""
Canonical pipeline output contract builder.

Produces one PipelineOutputContract dict per completed pipeline run.
This is the only place that translates internal runtime objects into the
canonical output shape. Renderers read from this dict; they do not
inspect runtime internals after contract creation.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any, Optional

from cuttingboard import config, time_utils
from cuttingboard.trade_decision import (
    ALLOW_TRADE,
    BLOCK_TRADE,
    TradeDecision,
    VALID_DECISION_STATUSES,
)
from cuttingboard.overnight_policy import (
    VALID_DECISIONS as VALID_OVERNIGHT_DECISIONS,
    VALID_REASONS as VALID_OVERNIGHT_REASONS,
)
from cuttingboard.qualification import (
    ENTRY_MODE_PULLBACK_IMBALANCE,
    QualificationSummary,
)
from cuttingboard.regime import EXPANSION, STAY_FLAT, RegimeState

SCHEMA_VERSION = "v2"

STATUS_OK = "OK"
STATUS_STAY_FLAT = "STAY_FLAT"
STATUS_ERROR = "ERROR"

_VALID_STATUSES = frozenset({STATUS_OK, STATUS_STAY_FLAT, STATUS_ERROR})

LATEST_CONTRACT_PATH = "logs/latest_contract.json"

_MACRO_DRIVER_SYMBOLS = {
    "volatility": "^VIX",
    "dollar": "DX-Y.NYB",
    "rates": "^TNX",
    "bitcoin": "BTC-USD",
}


def build_pipeline_output_contract(
    pipeline_result: Any,
    *,
    generated_at: datetime,
    status: str,
    artifacts: dict[str, Any],
    timezone_name: str = "America/New_York",
    data_quality: Optional[str] = None,
) -> dict[str, Any]:
    """Build a PipelineOutputContract dict from a completed PipelineResult.

    All fields are JSON-native. No datetime objects, enums, or custom
    instances survive into the returned dict.
    """
    if status not in _VALID_STATUSES:
        raise ValueError(f"Invalid status {status!r}; must be one of {sorted(_VALID_STATUSES)}")

    pr = pipeline_result
    regime: Optional[RegimeState] = getattr(pr, "regime", None)
    qual: Optional[QualificationSummary] = getattr(pr, "qualification_summary", None)
    option_setups = getattr(pr, "option_setups", [])
    chain_results = getattr(pr, "chain_results", {})
    trade_decisions = getattr(pr, "trade_decisions", [])
    watch_summary = getattr(pr, "watch_summary", None)
    validation_summary = getattr(pr, "validation_summary", None)
    normalized_quotes = getattr(pr, "normalized_quotes", {})
    raw_quotes = getattr(pr, "raw_quotes", {})
    run_at_utc: Optional[datetime] = getattr(pr, "run_at_utc", None)
    router_mode: Optional[str] = _safe_str(getattr(pr, "router_mode", None))
    errors = list(getattr(pr, "errors", []))
    correlation = getattr(pr, "correlation", None)

    dq = data_quality or _compute_data_quality(normalized_quotes, raw_quotes, generated_at)
    macro_drivers = {} if not normalized_quotes else _build_macro_drivers(normalized_quotes)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _iso_str(generated_at),
        "session_date": getattr(pr, "date_str", None),
        "mode": getattr(pr, "mode", None),
        "status": status,
        "timezone": timezone_name,
        "system_state": _build_system_state(
            regime, qual, watch_summary, validation_summary, run_at_utc, router_mode
        ),
        "market_context": _build_market_context(
            regime, qual, normalized_quotes, raw_quotes, generated_at, dq
        ),
        "trade_candidates": _build_trade_candidates(
            qual, option_setups, chain_results, trade_decisions,
            getattr(pr, "visibility_map", {}),
            getattr(pr, "explanation_map", {}),
            getattr(pr, "thesis_map", None),
        ),
        "rejections": _build_rejections(qual),
        "audit_summary": _build_audit_summary(qual, errors),
        "artifacts": _build_artifacts(artifacts, pr),
        "correlation": _build_correlation(correlation),
        "regime": _build_regime_block(regime),
        "macro_drivers": macro_drivers,
    }


def build_error_contract(
    *,
    generated_at: datetime,
    artifacts: dict[str, Any],
    timezone_name: str = "America/New_York",
    error_detail: Optional[str] = None,
) -> dict[str, Any]:
    """Build a minimal valid contract when the pipeline fails with an exception."""
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _iso_str(generated_at),
        "session_date": None,
        "mode": None,
        "status": STATUS_ERROR,
        "timezone": timezone_name,
        "system_state": {
            "router_mode": None,
            "market_regime": None,
            "intraday_state": None,
            "time_gate_open": None,
            "tradable": False,
            "stay_flat_reason": error_detail,
        },
        "market_context": {
            "expansion_regime": None,
            "continuation_enabled": None,
            "imbalance_enabled": None,
            "stale_data_detected": None,
            "data_quality": None,
        },
        "trade_candidates": [],
        "rejections": [],
        "audit_summary": {
            "qualified_count": 0,
            "rejected_count": 0,
            "continuation_audit_present": False,
            "continuation_accepted_count": None,
            "continuation_rejected_count": None,
            "error_count": 1 if error_detail else 0,
        },
        "artifacts": {
            "report_path": artifacts.get("report_path"),
            "log_path": artifacts.get("log_path"),
            "notification_sent": artifacts.get("notification_sent"),
        },
        "correlation": None,
        "regime": None,
        "macro_drivers": {},
    }


def derive_run_status(outcome: str, regime: Optional[RegimeState], system_halted: bool) -> str:
    """Translate runtime outcome + regime state into a contract status string."""
    if system_halted:
        return STATUS_STAY_FLAT
    if regime is not None and regime.posture == STAY_FLAT:
        return STATUS_STAY_FLAT
    if outcome == "HALT":
        return STATUS_STAY_FLAT
    return STATUS_OK


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _build_system_state(
    regime: Optional[RegimeState],
    qual: Optional[QualificationSummary],
    watch_summary: Any,
    validation_summary: Any,
    run_at_utc: Optional[datetime],
    router_mode: Optional[str],
) -> dict[str, Any]:
    system_halted = getattr(validation_summary, "system_halted", False)
    halt_reason = getattr(validation_summary, "halt_reason", None)
    regime_failure_reason = qual.regime_failure_reason if qual else None

    stay_flat_reason: Optional[str] = None
    if system_halted:
        stay_flat_reason = halt_reason
    elif qual is not None and qual.regime_short_circuited:
        stay_flat_reason = regime_failure_reason
    elif regime is not None and regime.posture == STAY_FLAT:
        stay_flat_reason = "STAY_FLAT posture"

    tradable = (
        not system_halted
        and regime is not None
        and regime.posture != STAY_FLAT
    )

    time_gate_open: Optional[bool] = None
    if run_at_utc is not None:
        try:
            now_et = time_utils.convert_utc_to_et(run_at_utc)
            time_gate_open = not time_utils.is_after_entry_cutoff(now_et, config.ENTRY_CUTOFF_ET)
        except Exception:
            pass

    intraday_state: Optional[str] = None
    if watch_summary is not None:
        intraday_state = _safe_str(getattr(watch_summary, "session", None))

    return {
        "router_mode": router_mode,
        "market_regime": _safe_str(regime.regime) if regime else None,
        "intraday_state": intraday_state,
        "time_gate_open": time_gate_open,
        "tradable": bool(tradable),
        "stay_flat_reason": stay_flat_reason,
    }


def _build_market_context(
    regime: Optional[RegimeState],
    qual: Optional[QualificationSummary],
    normalized_quotes: dict,
    raw_quotes: dict,
    generated_at: datetime,
    data_quality: Optional[str],
) -> dict[str, Any]:
    expansion_regime: Optional[str] = None
    continuation_enabled: Optional[bool] = None
    imbalance_enabled: Optional[bool] = None

    if regime is not None:
        if regime.regime == EXPANSION:
            expansion_regime = EXPANSION
        continuation_enabled = regime.regime == EXPANSION

    if qual is not None:
        imbalance_enabled = any(
            getattr(r, "entry_mode", "") == ENTRY_MODE_PULLBACK_IMBALANCE
            for r in qual.qualified_trades
        )

    stale_data_detected: Optional[bool] = None
    if normalized_quotes:
        stale_data_detected = any(
            (generated_at - q.fetched_at_utc).total_seconds() > config.FRESHNESS_SECONDS
            for q in normalized_quotes.values()
        )

    return {
        "expansion_regime": expansion_regime,
        "continuation_enabled": continuation_enabled,
        "imbalance_enabled": imbalance_enabled,
        "stale_data_detected": stale_data_detected,
        "data_quality": data_quality,
    }


def _build_trade_candidates(
    qual: Optional[QualificationSummary],
    option_setups: list,
    chain_results: dict,
    trade_decisions: list[TradeDecision],
    visibility_map: Optional[dict] = None,
    explanation_map: Optional[dict] = None,
    thesis_map: Optional[dict] = None,
) -> list[dict[str, Any]]:
    if qual is None:
        return []

    setup_by_symbol = {s.symbol: s for s in option_setups}
    result_by_symbol = {result.symbol: result for result in qual.qualified_trades}
    chain_by_symbol = dict(chain_results)
    candidates = []

    for decision in trade_decisions:
        result = result_by_symbol.get(decision.ticker)
        if result is None:
            raise ValueError(f"Missing QualificationResult for decision {decision.ticker}")
        setup = setup_by_symbol.get(result.symbol)
        if setup is None:
            raise ValueError(f"Missing OptionSetup for decision {decision.ticker}")
        chain = chain_by_symbol.get(result.symbol)

        vis = (visibility_map or {}).get(result.symbol, {})
        expl = (explanation_map or {}).get(result.symbol, {})
        candidates.append({
            "symbol": result.symbol,
            "direction": _safe_str(result.direction),
            "entry_mode": _safe_str(getattr(result, "entry_mode", None)),
            "strategy_tag": _safe_str(setup.strategy if setup else None),
            "trigger": None,
            "entry": float(decision.entry),
            "stop": float(decision.stop),
            "target": float(decision.target),
            "risk_reward": float(decision.r_r),
            "timeframe": str(setup.dte) if setup else None,
            "setup_quality": _safe_str(chain.classification if chain else None),
            "notes": _safe_str(chain.reason if chain else None),
            "decision_status": decision.status,
            "block_reason": decision.block_reason,
            "decision_trace": dict(decision.decision_trace),
            "policy_allowed": decision.policy_allowed,
            "policy_reason": decision.policy_reason,
            "size_multiplier": float(decision.size_multiplier),
            "visibility_status": vis.get("visibility_status"),
            "visibility_reason": vis.get("visibility_reason"),
            "enable_conditions": vis.get("enable_conditions", []),
            "explanation": expl,
            "thesis": (thesis_map or {}).get(result.symbol),
        })

    return candidates


def _build_rejections(qual: Optional[QualificationSummary]) -> list[dict[str, Any]]:
    if qual is None:
        return []

    rejections: list[dict[str, Any]] = []

    if qual.regime_short_circuited and qual.regime_failure_reason:
        rejections.append({
            "symbol": "REGIME",
            "stage": "REGIME",
            "reason": qual.regime_failure_reason,
            "detail": None,
        })

    for symbol, reason in sorted(qual.excluded.items()):
        rejections.append({
            "symbol": symbol,
            "stage": "QUALIFICATION",
            "reason": reason,
            "detail": None,
        })

    for result in qual.watchlist:
        rejections.append({
            "symbol": result.symbol,
            "stage": "WATCHLIST",
            "reason": _safe_str(result.watchlist_reason) or "ONE_SOFT_MISS",
            "detail": None,
        })

    return rejections


def _build_audit_summary(
    qual: Optional[QualificationSummary],
    errors: list[str],
) -> dict[str, Any]:
    continuation_audit = qual.continuation_audit if qual else None
    continuation_audit_present = continuation_audit is not None

    continuation_accepted: Optional[int] = None
    continuation_rejected: Optional[int] = None
    if continuation_audit is not None:
        continuation_accepted = int(continuation_audit.get("accepted", 0))
        total = int(continuation_audit.get("total_candidates", 0))
        continuation_rejected = total - continuation_accepted

    return {
        "qualified_count": qual.symbols_qualified if qual else 0,
        "rejected_count": len(qual.excluded) if qual else 0,
        "continuation_audit_present": continuation_audit_present,
        "continuation_accepted_count": continuation_accepted,
        "continuation_rejected_count": continuation_rejected,
        "error_count": len(errors),
    }


def _build_artifacts(artifacts: dict[str, Any], pipeline_result: Any) -> dict[str, Any]:
    report_path = artifacts.get("report_path") or _safe_str(getattr(pipeline_result, "report_path", None))
    log_path = artifacts.get("log_path")
    notification_sent = artifacts.get("notification_sent")
    if notification_sent is None:
        raw = getattr(pipeline_result, "alert_sent", None)
        if raw is not None:
            notification_sent = bool(raw)

    return {
        "report_path": report_path,
        "log_path": log_path,
        "notification_sent": notification_sent,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value)


def _build_regime_block(regime: Optional[RegimeState]) -> Optional[dict]:
    if regime is None:
        return None
    return {
        "classification": str(regime.regime),
        "posture":        str(regime.posture),
        "confidence":     float(regime.confidence),
        "net_score":      int(regime.net_score),
        "risk_on_votes":  int(regime.risk_on_votes),
        "risk_off_votes": int(regime.risk_off_votes),
        "neutral_votes":  int(regime.neutral_votes),
        "total_votes":    int(regime.total_votes),
        "vote_breakdown": dict(regime.vote_breakdown),
        "vix_level":      float(regime.vix_level) if regime.vix_level is not None else None,
        "vix_pct_change": float(regime.vix_pct_change) if regime.vix_pct_change is not None else None,
    }


def _build_correlation(correlation: Any) -> Optional[dict]:
    if correlation is None:
        return None
    return {
        "gold_symbol":   correlation.gold_symbol,
        "dollar_symbol": correlation.dollar_symbol,
        "state":         correlation.state,
        "score":         int(correlation.score),
        "risk_modifier": float(correlation.risk_modifier),
    }


def _compute_data_quality(
    normalized_quotes: dict,
    raw_quotes: dict,
    generated_at: datetime,
) -> Optional[str]:
    if not normalized_quotes:
        return None
    if any(
        (generated_at - q.fetched_at_utc).total_seconds() > config.FRESHNESS_SECONDS
        for q in normalized_quotes.values()
    ):
        return "stale"
    if any(getattr(r, "source", "") == "polygon" for r in raw_quotes.values()):
        return "fallback"
    return "ok"


def _assert_macro_driver_mapping_sync() -> None:
    assert set(_MACRO_DRIVER_SYMBOLS.values()).issubset(set(config.MACRO_DRIVERS))


def _required_finite_float(value: Any, label: str) -> float:
    if value is None:
        raise ValueError(f"Missing required value: {label}")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Non-finite required value: {label}")
    return number


def _build_macro_drivers(normalized_quotes: dict) -> dict[str, dict[str, float | str]]:
    _assert_macro_driver_mapping_sync()

    macro_drivers: dict[str, dict[str, float | str]] = {}
    for driver, symbol in _MACRO_DRIVER_SYMBOLS.items():
        quote = normalized_quotes.get(symbol)
        if quote is None:
            raise ValueError(f"Missing macro driver quote: {symbol}")

        price = _required_finite_float(getattr(quote, "price", None), f"{symbol}.price")
        pct_change_decimal = _required_finite_float(
            getattr(quote, "pct_change_decimal", None),
            f"{symbol}.pct_change_decimal",
        )
        block: dict[str, float | str] = {
            "symbol": symbol,
            "level": price,
            "change_pct": pct_change_decimal * 100.0,
        }
        if driver == "rates":
            block["change_bps"] = pct_change_decimal * price * 100.0
        macro_drivers[driver] = block

    return macro_drivers


def assert_valid_contract(contract: dict) -> None:
    """Raise AssertionError if the contract violates any hard invariants."""
    required_top = {
        "schema_version", "generated_at", "session_date", "mode", "status",
        "timezone", "system_state", "market_context", "trade_candidates",
        "rejections", "audit_summary", "artifacts", "correlation", "regime",
        "macro_drivers",
    }
    missing = required_top - set(contract)
    assert not missing, f"Missing required contract keys: {missing}"

    assert contract["schema_version"] == SCHEMA_VERSION, \
        f"schema_version must be {SCHEMA_VERSION!r}, got {contract['schema_version']!r}"
    assert contract["status"] in _VALID_STATUSES, \
        f"Invalid status: {contract['status']!r}"
    _assert_macro_driver_mapping_sync()

    macro_drivers = contract["macro_drivers"]
    if contract["status"] == STATUS_ERROR:
        assert macro_drivers == {}, "ERROR contracts must set macro_drivers to {}"
        return
    if macro_drivers == {}:
        return

    assert isinstance(contract["trade_candidates"], list), "trade_candidates must be a list"
    assert isinstance(contract["rejections"], list), "rejections must be a list"
    assert isinstance(contract["system_state"], dict), "system_state must be a dict"
    assert isinstance(contract["market_context"], dict), "market_context must be a dict"
    assert isinstance(contract["audit_summary"], dict), "audit_summary must be a dict"
    assert isinstance(contract["artifacts"], dict), "artifacts must be a dict"
    assert isinstance(contract["system_state"]["tradable"], bool), "system_state.tradable must be bool"
    _assert_trade_candidates_valid(contract["trade_candidates"])

    corr = contract.get("correlation")
    if corr is not None:
        assert isinstance(corr, dict), "correlation must be a dict"
        assert corr.get("state") in ("ALIGNED", "NEUTRAL", "CONFLICT"), \
            f"invalid correlation state: {corr.get('state')!r}"
        assert corr.get("score") in (-1, 0, 1), \
            f"invalid correlation score: {corr.get('score')!r}"
        assert isinstance(corr.get("risk_modifier"), float), \
            "correlation.risk_modifier must be float"
        assert corr.get("gold_symbol") is not None, "correlation.gold_symbol required"
        assert corr.get("dollar_symbol") is not None, "correlation.dollar_symbol required"

    regime = contract.get("regime")
    if regime is not None:
        assert isinstance(regime, dict), "regime must be a dict or null"
        _REGIME_REQUIRED = {
            "classification", "posture", "confidence", "net_score",
            "risk_on_votes", "risk_off_votes", "neutral_votes", "total_votes",
            "vote_breakdown", "vix_level", "vix_pct_change",
        }
        missing_r = _REGIME_REQUIRED - set(regime)
        assert not missing_r, f"regime missing keys: {missing_r}"
        extra_r = set(regime) - _REGIME_REQUIRED
        assert not extra_r, f"regime has unexpected keys: {extra_r}"
        assert isinstance(regime["vote_breakdown"], dict), "regime.vote_breakdown must be dict"
        assert isinstance(regime["total_votes"], int), "regime.total_votes must be int"
        assert isinstance(regime["confidence"], float), "regime.confidence must be float"

    expected_macro_keys = set(_MACRO_DRIVER_SYMBOLS)
    assert isinstance(macro_drivers, dict), "macro_drivers must be a dict"
    assert set(macro_drivers) == expected_macro_keys, "macro_drivers must have exact driver keys"

    for driver, symbol in _MACRO_DRIVER_SYMBOLS.items():
        block = macro_drivers[driver]
        assert isinstance(block, dict), f"macro_drivers.{driver} must be a dict"
        required_fields = {"symbol", "level", "change_pct"}
        if driver == "rates":
            required_fields = required_fields | {"change_bps"}
        assert set(block) == required_fields, f"macro_drivers.{driver} has unexpected keys"
        assert block["symbol"] == symbol, f"macro_drivers.{driver}.symbol must be {symbol!r}"
        for field in required_fields - {"symbol"}:
            value = block[field]
            assert isinstance(value, float), f"macro_drivers.{driver}.{field} must be float"
            assert math.isfinite(value), f"macro_drivers.{driver}.{field} must be finite"

    # Must be JSON-serializable with no custom encoder
    json.dumps(contract)


def _assert_trade_candidates_valid(trade_candidates: list[Any]) -> None:
    for index, candidate in enumerate(trade_candidates):
        assert isinstance(candidate, dict), f"trade_candidates[{index}] must be a dict"
        decision_status = candidate.get("decision_status")
        assert decision_status in VALID_DECISION_STATUSES, (
            f"trade_candidates[{index}].decision_status invalid: {decision_status!r}"
        )
        block_reason = candidate.get("block_reason")
        decision_trace = candidate.get("decision_trace")
        policy_allowed = candidate.get("policy_allowed")
        policy_reason = candidate.get("policy_reason")
        size_multiplier = candidate.get("size_multiplier")
        assert isinstance(policy_allowed, bool), (
            f"trade_candidates[{index}].policy_allowed must be bool"
        )
        assert isinstance(policy_reason, str) and policy_reason.strip(), (
            f"trade_candidates[{index}].policy_reason must be non-empty string"
        )
        assert isinstance(size_multiplier, float), (
            f"trade_candidates[{index}].size_multiplier must be float"
        )
        assert math.isfinite(size_multiplier) and size_multiplier >= 0.0, (
            f"trade_candidates[{index}].size_multiplier must be finite and non-negative"
        )
        if policy_allowed is False:
            assert decision_status != ALLOW_TRADE, (
                f"trade_candidates[{index}] cannot be ALLOW_TRADE when policy_allowed is False"
            )
        overnight_policy = candidate.get("overnight_policy")
        if overnight_policy is not None:
            assert isinstance(overnight_policy, dict), (
                f"trade_candidates[{index}].overnight_policy must be a dict"
            )
            assert set(overnight_policy) == {"decision", "reason"}, (
                f"trade_candidates[{index}].overnight_policy must contain exactly decision, reason"
            )
            assert overnight_policy["decision"] in VALID_OVERNIGHT_DECISIONS, (
                f"trade_candidates[{index}].overnight_policy.decision invalid: "
                f"{overnight_policy['decision']!r}"
            )
            assert overnight_policy["reason"] in VALID_OVERNIGHT_REASONS, (
                f"trade_candidates[{index}].overnight_policy.reason invalid: "
                f"{overnight_policy['reason']!r}"
            )
        assert isinstance(decision_trace, dict), (
            f"trade_candidates[{index}].decision_trace must be a dict"
        )
        expected_trace_keys = {"stage", "source", "reason"}
        assert set(decision_trace) == expected_trace_keys, (
            f"trade_candidates[{index}].decision_trace must contain exactly stage, source, reason"
        )
        for key in ("stage", "source", "reason"):
            value = decision_trace.get(key)
            assert isinstance(value, str) and value.strip(), (
                f"trade_candidates[{index}].decision_trace.{key} must be non-empty string"
            )
        if decision_status == ALLOW_TRADE:
            assert block_reason is None, (
                f"trade_candidates[{index}].block_reason must be None for ALLOW_TRADE"
            )
            assert decision_trace["reason"] == "TOP_TRADE_VALIDATED", (
                f"trade_candidates[{index}].decision_trace.reason must be TOP_TRADE_VALIDATED for ALLOW_TRADE"
            )
            for field in ("entry", "stop", "target", "risk_reward"):
                value = candidate.get(field)
                assert isinstance(value, float), (
                    f"trade_candidates[{index}].{field} must be float for ALLOW_TRADE"
                )
                assert math.isfinite(value), (
                    f"trade_candidates[{index}].{field} must be finite for ALLOW_TRADE"
                )
        elif decision_status == BLOCK_TRADE:
            assert isinstance(block_reason, str) and block_reason.strip(), (
                f"trade_candidates[{index}].block_reason must be non-empty for BLOCK_TRADE"
            )
            assert block_reason == decision_trace["reason"], (
                f"trade_candidates[{index}].block_reason must match decision_trace.reason for BLOCK_TRADE"
            )
