"""
Notification suppression layer for PRD-018.

Implements state-key-based deduplication and priority classification so that
only meaningful changes in trading state generate Telegram alerts.

Public API
----------
notification_state_key(contract)   → deterministic string key
classify_notification_priority(contract) → NotificationPriority
load_last_state([path])             → str | None
save_last_state(key[, path])        → None
should_send(current_key, priority, last_key) → bool
"""

from __future__ import annotations

import json
from enum import Enum
from cuttingboard import config
from cuttingboard.contract_types import PipelineContract
from pathlib import Path
from typing import Optional

LAST_STATE_PATH = "logs/last_notification_state.json"

# PRD-304 R8: the operator lock is visible schema-neutrally in the existing
# system_state.permission field (the R5 locked carrier). No new schema key is
# introduced. This posture value gives the lock a DISTINCT dedup state so an
# analytical tradable=true run cannot reuse TRADE_READY's dedup key.
_OPERATOR_LOCKED_POSTURE = "OPERATOR_LOCKED"


def _is_operator_locked(system_state: dict) -> bool:
    return system_state.get("permission") == config.OPERATOR_LOCK_PERMISSION


class NotificationPriority(str, Enum):
    """Priority tier controls whether suppression is bypassed.

    CRITICAL and HIGH always send regardless of state-key match (R5).
    MEDIUM and LOW are subject to suppression when the state key is unchanged.
    """
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


def notification_state_key(contract: PipelineContract) -> str:
    """Return a deterministic string key from decision-relevant contract fields.

    Key structure (pipe-delimited):
        market_regime | execution_posture | tradable | symbols (max 3) | primary_reason

    Fields are sourced exclusively from system_state, trade_candidates, and
    rejections — never from transport-layer or timing metadata.
    """
    ss = contract.get("system_state") or {}
    market_regime = ss.get("market_regime") or ""
    tradable = bool(ss.get("tradable", False))
    # PRD-304 R8: the operator lock takes precedence over the tradable-as-posture
    # mapping, giving locked runs a distinct dedup posture. Analytical `tradable`
    # is preserved in the key so the observation itself still varies the key.
    if _is_operator_locked(ss):
        execution_posture = _OPERATOR_LOCKED_POSTURE
    else:
        execution_posture = "TRADE_READY" if tradable else "STAY_FLAT"

    candidates = (contract.get("trade_candidates") or [])[:3]
    symbols = ",".join(c.get("symbol") or "" for c in candidates)

    # Primary rejection reason: prefer explicit rejections list, fall back to stay_flat_reason
    primary_reason = ""
    rejections = contract.get("rejections") or []
    if rejections:
        primary_reason = rejections[0].get("reason") or ""
    elif ss.get("stay_flat_reason"):
        primary_reason = ss.get("stay_flat_reason") or ""

    return f"{market_regime}|{execution_posture}|{tradable}|{symbols}|{primary_reason}"


def classify_notification_priority(contract: PipelineContract) -> NotificationPriority:
    """Classify notification priority from the current contract.

    CRITICAL — pipeline error or stale/missing data
    HIGH     — tradable == True (execution_posture == TRADE_READY)
    MEDIUM   — trade candidates exist but not yet tradable
    LOW      — flat with no candidates
    """
    status = contract.get("status") or ""
    if status == "ERROR":
        return NotificationPriority.CRITICAL

    mc = contract.get("market_context") or {}
    if mc.get("stale_data_detected"):
        return NotificationPriority.CRITICAL

    ss = contract.get("system_state") or {}
    # PRD-304 R8: OPERATOR_LOCKED classifies ahead of TRADE_READY with NORMAL
    # (suppressible) priority — an analytical tradable=true run under lock must
    # not be classified HIGH (which bypasses suppression as if a trade were
    # ready). MEDIUM keeps it meaningful but suppressible; CRITICAL (error/stale)
    # above still wins.
    if _is_operator_locked(ss):
        return NotificationPriority.MEDIUM

    if ss.get("tradable"):
        return NotificationPriority.HIGH

    if contract.get("trade_candidates"):
        return NotificationPriority.MEDIUM

    return NotificationPriority.LOW


def should_send(
    current_key: str,
    priority: NotificationPriority,
    last_key: Optional[str],
) -> bool:
    """Return True when this run should send a notification.

    Rules (in priority order):
      R6 — No prior state → always send.
      R5 — CRITICAL or HIGH priority → always send (bypass suppression).
      R3 — State unchanged → suppress.
      Default — state changed → send.
    """
    if last_key is None:
        return True
    if priority in (NotificationPriority.CRITICAL, NotificationPriority.HIGH):
        return True
    return current_key != last_key


def load_last_state(path: str = LAST_STATE_PATH) -> Optional[str]:
    """Return the last persisted state key, or None if not found / unreadable."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data.get("state_key") or None
    except (FileNotFoundError, json.JSONDecodeError, KeyError, OSError):
        return None


def save_last_state(key: str, path: str = LAST_STATE_PATH) -> None:
    """Persist the current state key.

    Called only after a confirmed successful send (R7).
    Creates parent directory if needed. Never raises — a write failure
    means the next run re-sends, which is the safe-side failure.
    """
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            json.dumps({"state_key": key}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        import logging
        logging.getLogger(__name__).warning("Failed to persist notification state: %s", exc)
