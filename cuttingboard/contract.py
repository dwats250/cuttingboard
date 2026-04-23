"""
Canonical pipeline output contract builder.

Produces one PipelineOutputContract dict per completed pipeline run.
This is the only place that translates internal runtime objects into the
canonical output shape. Renderers read from this dict; they do not
inspect runtime internals after contract creation.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from cuttingboard import config, time_utils
from cuttingboard.qualification import (
    ENTRY_MODE_PULLBACK_IMBALANCE,
    QualificationSummary,
)
from cuttingboard.regime import EXPANSION, STAY_FLAT, RegimeState

SCHEMA_VERSION = "v1"

STATUS_OK = "OK"
STATUS_STAY_FLAT = "STAY_FLAT"
STATUS_ERROR = "ERROR"

_VALID_STATUSES = frozenset({STATUS_OK, STATUS_STAY_FLAT, STATUS_ERROR})

LATEST_CONTRACT_PATH = "logs/latest_contract.json"


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
    watch_summary = getattr(pr, "watch_summary", None)
    validation_summary = getattr(pr, "validation_summary", None)
    normalized_quotes = getattr(pr, "normalized_quotes", {})
    raw_quotes = getattr(pr, "raw_quotes", {})
    run_at_utc: Optional[datetime] = getattr(pr, "run_at_utc", None)
    router_mode: Optional[str] = _safe_str(getattr(pr, "router_mode", None))
    errors = list(getattr(pr, "errors", []))

    dq = data_quality or _compute_data_quality(normalized_quotes, raw_quotes, generated_at)

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
        "trade_candidates": _build_trade_candidates(qual, option_setups, chain_results),
        "rejections": _build_rejections(qual),
        "audit_summary": _build_audit_summary(qual, errors),
        "artifacts": _build_artifacts(artifacts, pr),
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
) -> list[dict[str, Any]]:
    if qual is None:
        return []

    setup_by_symbol = {s.symbol: s for s in option_setups}
    candidates = []

    for result in qual.qualified_trades:
        setup = setup_by_symbol.get(result.symbol)
        chain = chain_results.get(result.symbol)

        candidates.append({
            "symbol": result.symbol,
            "direction": _safe_str(result.direction),
            "entry_mode": _safe_str(getattr(result, "entry_mode", None)),
            "strategy_tag": _safe_str(setup.strategy if setup else None),
            "trigger": None,
            "entry": None,
            "stop": None,
            "target": None,
            "risk_reward": None,
            "timeframe": str(setup.dte) if setup else None,
            "setup_quality": _safe_str(chain.classification if chain else None),
            "notes": _safe_str(chain.reason if chain else None),
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


def assert_valid_contract(contract: dict) -> None:
    """Raise AssertionError if the contract violates any hard invariants."""
    required_top = {
        "schema_version", "generated_at", "session_date", "mode", "status",
        "timezone", "system_state", "market_context", "trade_candidates",
        "rejections", "audit_summary", "artifacts",
    }
    missing = required_top - set(contract)
    assert not missing, f"Missing required contract keys: {missing}"

    assert contract["schema_version"] == SCHEMA_VERSION, \
        f"schema_version must be {SCHEMA_VERSION!r}, got {contract['schema_version']!r}"
    assert contract["status"] in _VALID_STATUSES, \
        f"Invalid status: {contract['status']!r}"
    assert isinstance(contract["trade_candidates"], list), "trade_candidates must be a list"
    assert isinstance(contract["rejections"], list), "rejections must be a list"
    assert isinstance(contract["system_state"], dict), "system_state must be a dict"
    assert isinstance(contract["market_context"], dict), "market_context must be a dict"
    assert isinstance(contract["audit_summary"], dict), "audit_summary must be a dict"
    assert isinstance(contract["artifacts"], dict), "artifacts must be a dict"
    assert isinstance(contract["system_state"]["tradable"], bool), "system_state.tradable must be bool"

    # Must be JSON-serializable with no custom encoder
    json.dumps(contract)
