"""
Canonical ReportPayload builder.

Derives a deterministic, JSON-safe payload dict from a PRD-011 contract dict.
No access to PipelineResult, RegimeState, or any runtime internals.
"""

from __future__ import annotations

import json
import math
from typing import Any, Optional

PAYLOAD_SCHEMA_VERSION = "1.0"

_VALID_RUN_STATUSES = frozenset({"OK", "STAY_FLAT", "ERROR"})
_DECISION_DETAIL_KEYS = frozenset({"symbol", "direction", "strategy_tag", "entry_mode", "decision_status", "block_reason", "decision_trace"})
_DECISION_TRACE_KEYS = frozenset({"stage", "source", "reason"})


def build_report_payload(contract: dict, fixture_mode: bool = False) -> dict:
    """Build a ReportPayload dict from a canonical PRD-011 contract dict.

    Deterministic: identical contract produces identical payload.
    """
    ss: dict[str, Any] = contract.get("system_state") or {}
    ac: dict[str, Any] = contract.get("audit_summary") or {}
    trade_candidates: list[dict] = list(contract.get("trade_candidates") or [])
    rejections: list[dict] = list(contract.get("rejections") or [])

    # --- summary ---
    market_regime = ss.get("market_regime") or ""
    tradable = ss.get("tradable")         # bool | None — preserve semantics
    router_mode = ss.get("router_mode")   # str | None

    # --- sections ---
    top_trades = [t for t in trade_candidates]

    watchlist = [r for r in rejections if r.get("stage") == "WATCHLIST"]
    rejected = [r for r in rejections if r.get("stage") != "WATCHLIST"]

    continuation_audit: Optional[dict] = None
    if ac.get("continuation_audit_present"):
        continuation_audit = {
            "accepted_count": ac.get("continuation_accepted_count"),
            "rejected_count": ac.get("continuation_rejected_count"),
        }

    trade_decision_detail = [
        {
            "symbol": t.get("symbol"),
            "direction": t.get("direction"),
            "strategy_tag": t.get("strategy_tag"),
            "entry_mode": t.get("entry_mode"),
            "decision_status": t.get("decision_status"),
            "block_reason": t.get("block_reason"),
            "decision_trace": t.get("decision_trace"),
        }
        for t in trade_candidates
    ]

    option_setups_detail = [
        {
            "symbol": t.get("symbol"),
            "strategy_tag": t.get("strategy_tag"),
            "timeframe": t.get("timeframe"),
            "direction": t.get("direction"),
            "entry_mode": t.get("entry_mode"),
        }
        for t in trade_candidates
    ]

    chain_results_detail = [
        {
            "symbol": t.get("symbol"),
            "classification": t.get("setup_quality"),
            "notes": t.get("notes"),
        }
        for t in trade_candidates
    ]

    intraday_state = ss.get("intraday_state")
    watch_summary_detail: Optional[dict] = (
        {"session": intraday_state} if intraday_state is not None else None
    )

    stay_flat_reason = ss.get("stay_flat_reason")
    validation_halt_detail: Optional[dict] = None
    if stay_flat_reason is not None:
        validation_halt_detail = {"reason": stay_flat_reason}

    # --- meta ---
    timestamp = contract.get("generated_at") or ""
    qualified_count = int(ac.get("qualified_count") or 0)
    rejected_count = int(ac.get("rejected_count") or 0)
    watchlist_count = len(watchlist)
    symbols_scanned = qualified_count + rejected_count + watchlist_count

    meta: dict = {
        "timestamp": timestamp,
        "symbols_scanned": symbols_scanned,
    }
    session_type = ss.get("session_type")
    if session_type is not None:
        meta["session_type"] = session_type
    if fixture_mode:
        meta["fixture_mode"] = True

    return {
        "schema_version": PAYLOAD_SCHEMA_VERSION,
        "run_status": contract.get("status", "ERROR"),
        "macro_drivers": contract["macro_drivers"],
        "summary": {
            "market_regime": market_regime,
            "tradable": tradable,
            "router_mode": router_mode,
        },
        "sections": {
            "top_trades": top_trades,
            "watchlist": watchlist,
            "rejected": rejected,
            "continuation_audit": continuation_audit,
            "option_setups_detail": option_setups_detail,
            "chain_results_detail": chain_results_detail,
            "watch_summary_detail": watch_summary_detail,
            "validation_halt_detail": validation_halt_detail,
            "trade_decision_detail": trade_decision_detail,
        },
        "meta": meta,
    }


def assert_valid_payload(payload: dict) -> None:
    """Raise ValueError if the payload violates any schema invariants."""
    _require_keys(payload, {"schema_version", "run_status", "macro_drivers", "summary", "sections", "meta"}, "payload")

    _require_eq(payload, "schema_version", PAYLOAD_SCHEMA_VERSION)
    _require_in(payload, "run_status", _VALID_RUN_STATUSES)

    macro_drivers = payload["macro_drivers"]
    if macro_drivers != {}:
        _require_macro_drivers(macro_drivers)

    summary = payload["summary"]
    _require_keys(summary, {"market_regime", "tradable", "router_mode"}, "summary")
    _require_type(summary, "market_regime", str)
    _require_type_or_none(summary, "tradable", bool)
    _require_type_or_none(summary, "router_mode", str)

    sections = payload["sections"]
    _require_keys(
        sections,
        {
            "top_trades", "watchlist", "rejected",
            "continuation_audit", "option_setups_detail",
            "chain_results_detail", "watch_summary_detail",
            "validation_halt_detail", "trade_decision_detail",
        },
        "sections",
    )
    for list_field in ("top_trades", "watchlist", "rejected", "option_setups_detail", "chain_results_detail", "trade_decision_detail"):
        _require_type(sections, list_field, list)
    for nullable_dict_field in ("continuation_audit", "watch_summary_detail", "validation_halt_detail"):
        _require_type_or_none(sections, nullable_dict_field, dict)

    for i, item in enumerate(sections["trade_decision_detail"]):
        _path = f"trade_decision_detail[{i}]"
        if not isinstance(item, dict):
            raise ValueError(f"{_path} must be a dict")
        if set(item) != _DECISION_DETAIL_KEYS:
            raise ValueError(f"{_path} has unexpected keys: {sorted(set(item) ^ _DECISION_DETAIL_KEYS)}")
        for _str_field in ("symbol", "direction", "strategy_tag", "entry_mode", "decision_status"):
            if not isinstance(item[_str_field], str):
                raise ValueError(f"{_path}.{_str_field} must be str")
        _block_reason = item["block_reason"]
        if _block_reason is not None and (not isinstance(_block_reason, str) or not _block_reason):
            raise ValueError(f"{_path}.block_reason must be None or non-empty str")
        _trace = item["decision_trace"]
        if not isinstance(_trace, dict):
            raise ValueError(f"{_path}.decision_trace must be dict")
        if set(_trace) != _DECISION_TRACE_KEYS:
            raise ValueError(f"{_path}.decision_trace has unexpected keys: {sorted(set(_trace) ^ _DECISION_TRACE_KEYS)}")
        for _trace_field in ("stage", "source", "reason"):
            if not isinstance(_trace[_trace_field], str) or not _trace[_trace_field]:
                raise ValueError(f"{_path}.decision_trace.{_trace_field} must be non-empty str")

    meta = payload["meta"]
    _require_keys(meta, {"timestamp", "symbols_scanned"}, "meta")
    _require_type(meta, "timestamp", str)
    _require_type(meta, "symbols_scanned", int)

    try:
        json.dumps(payload)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"payload is not JSON-safe: {exc}") from exc


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _require_keys(obj: dict, keys: set, path: str) -> None:
    missing = keys - set(obj)
    if missing:
        raise ValueError(f"Missing required keys in {path}: {sorted(missing)}")


def _require_eq(obj: dict, key: str, expected: Any) -> None:
    if obj[key] != expected:
        raise ValueError(f"Expected {key}=={expected!r}, got {obj[key]!r}")


def _require_in(obj: dict, key: str, allowed: frozenset) -> None:
    if obj[key] not in allowed:
        raise ValueError(f"Invalid {key}={obj[key]!r}; must be one of {sorted(allowed)}")


def _require_type(obj: dict, key: str, expected_type: type) -> None:
    if not isinstance(obj[key], expected_type):
        raise ValueError(
            f"Expected {key} to be {expected_type.__name__}, got {type(obj[key]).__name__}"
        )


def _require_type_or_none(obj: dict, key: str, expected_type: type) -> None:
    if obj[key] is not None and not isinstance(obj[key], expected_type):
        raise ValueError(
            f"Expected {key} to be {expected_type.__name__} or None, "
            f"got {type(obj[key]).__name__}"
        )


def _require_macro_drivers(macro_drivers: dict) -> None:
    if not isinstance(macro_drivers, dict):
        raise ValueError("macro_drivers must be dict")
    expected = {
        "volatility": {"symbol", "level", "change_pct"},
        "dollar": {"symbol", "level", "change_pct"},
        "rates": {"symbol", "level", "change_pct", "change_bps"},
        "bitcoin": {"symbol", "level", "change_pct"},
    }
    if set(macro_drivers) != set(expected):
        raise ValueError("macro_drivers must have exact driver keys")
    for driver, required_fields in expected.items():
        block = macro_drivers[driver]
        if not isinstance(block, dict):
            raise ValueError(f"macro_drivers.{driver} must be dict")
        if set(block) != required_fields:
            raise ValueError(f"macro_drivers.{driver} has unexpected keys")
        if not isinstance(block["symbol"], str):
            raise ValueError(f"macro_drivers.{driver}.symbol must be str")
        for field in required_fields - {"symbol"}:
            value = block[field]
            if not isinstance(value, float) or not math.isfinite(value):
                raise ValueError(f"macro_drivers.{driver}.{field} must be finite float")
