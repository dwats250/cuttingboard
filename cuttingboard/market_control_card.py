"""NS-2E Market Control Card composer (PRD-289).

The SOLE producer of every final card value: seven fields — LOCATION, STATE,
PERMISSION, EVENT, TRANSITION, INVALIDATION, CANDIDATE-IMPLICATION — each a
truthful value or a typed UNAVAILABLE carrying a reason token from a closed
per-field vocabulary (packet §7, verbatim; per-field namespaces, never one
global enum). Composed once per eligible daily run (``MODE_LIVE`` /
``MODE_FIXTURE``, halted runs included; never ``MODE_SUNDAY``); all time logic
is keyed on ``run_at_utc``, never wall-clock. An unenumerated branch fails
construction rather than rendering silence; no raw upstream free-form string
(invalidation reasons, red-folder ``error``) may enter any card cell.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from cuttingboard.confirmation import STATE_FAILURE_CONFIRMED
from cuttingboard.output import OUTCOME_HALT, OUTCOME_NO_TRADE, OUTCOME_TRADE
from cuttingboard.red_folder import load_schedule
from cuttingboard.spy_observation import OBSERVED, SpyObservation
from cuttingboard.spy_state import VALID_SPY_STATE_UNAVAILABLE_REASONS, SpyStateOutcome

logger = logging.getLogger(__name__)

VALID_LOCATION_STATES = frozenset({"OBSERVED", "PRE_OPEN", "STALE", "UNAVAILABLE"})
VALID_LOCATION_PRICE_VS_VWAP = frozenset({"ABOVE", "BELOW", "AT_LEVEL"})
VALID_LOCATION_REASONS = frozenset({
    "system_halted", "intraday_fetch_failed", "insufficient_bars",
    "pre_open_prior_session", "session_mismatch", "pre_open",
    "observation_lag", "vwap_unavailable",
})
VALID_LOCATION_ORB_STATES = frozenset({"PRE_OPEN", "FORMING", "FORMED", "UNAVAILABLE", "INVALID"})
VALID_LOCATION_ORB_REASONS = frozenset({
    "no_bars", "unordered_bars", "pre_open_prior_session", "session_mismatch",
    "mixed_session", "formation_bars_absent", "formation_incomplete", "impossible_bounds",
})
VALID_SPY_STATE_VALUES = frozenset({"EXPANSION_CONFIRMED", "FAILED_EXPANSION", "RANGE"})
VALID_PERMISSION_VALUES = frozenset({
    "Long bias — trend continuation allowed.",
    "Long bias — defined risk preferred.",
    "Short bias — breakdown trades allowed.",
    "Selective only — defined risk, R:R >= 3:1.",
    "No new trades permitted.",
    "EXPANSION — momentum allowed. Continuation entries. R:R >= 1.5.",
    "No trades permitted. System halted.",
    # PRD-304: the operator-availability lock permission carrier (R9). The gate
    # shape is unchanged; this admits exactly one additional value and continues
    # to reject anything not in this frozenset.
    "No new trades permitted — operator cannot monitor.",
})
VALID_PERMISSION_UNAVAILABLE_REASONS = frozenset()  # EMPTY — total producer
VALID_EVENT_UNAVAILABLE_REASONS = frozenset({"event_schedule_unavailable"})
VALID_TRANSITION_VALUES = frozenset({
    "NO_BREAK", "ORB_BREAK_HOLDING_LONG", "ORB_BREAK_HOLDING_SHORT",
    "ORB_RECLAIMED", "FAILED_RECLAIM", "FAILED_EXPANSION",
})
VALID_TRANSITION_UNAVAILABLE_REASONS = frozenset({"transition_state_unavailable", "transition_deferred"})
VALID_INVALIDATION_VALUES = frozenset({"NOT_TRIGGERED", "WARNING", "TRIGGERED", "NO_ACTIVE_CANDIDATES"})
VALID_INVALIDATION_UNAVAILABLE_REASONS = frozenset({
    "invalidation_deferred_d2", "invalidation_inputs_absent", "invalidation_indeterminate",
})
VALID_CANDIDATE_IMPLICATION_VALUES = frozenset({
    "ACTIONABLE_CANDIDATES", "CANDIDATES_PRESENT_NONE_ACTIONABLE", "NO_CANDIDATES",
})
VALID_CANDIDATE_IMPLICATION_UNAVAILABLE_REASONS = frozenset({
    "candidate_implication_deferred_d3", "candidate_inputs_absent",
})

# F4 mixed-status aggregate precedence — strict total order, zero discretion.
_INVALIDATION_SEVERITY = ("TRIGGERED", "WARNING", "UNKNOWN", "NOT_TRIGGERED")
_ORB_REASON_NONE_LEGAL = frozenset({"PRE_OPEN", "FORMING", "FORMED"})


def _validate_xor_cell(field: str, cell: dict, values: frozenset, reasons: frozenset) -> None:
    value, reason = cell.get("value"), cell.get("unavailable_reason")
    if (value is None) == (reason is None):
        raise ValueError(f"{field}: exactly one of value/unavailable_reason required; got {cell!r}")
    if value is not None and value not in values:
        raise ValueError(f"{field}: unknown value {value!r}")
    if reason is not None and reason not in reasons:
        raise ValueError(f"{field}: unknown unavailable reason {reason!r}")


@dataclass(frozen=True)
class MarketControlCard:
    """Frozen, transient seven-field card; each field a plain-dict cell.
    Every token/value is validated against its field's frozenset here, at
    construction — the renderer projects and never derives."""

    location: dict
    state: dict
    permission: dict
    event: dict
    transition: dict
    invalidation: dict
    candidate_implication: dict

    def __post_init__(self) -> None:
        loc = self.location
        if loc["state"] not in VALID_LOCATION_STATES:
            raise ValueError(f"LOCATION: unknown state {loc['state']!r}")
        if loc["reason"] is None:
            if loc["state"] != OBSERVED:
                raise ValueError(f"LOCATION: reason=None is legal only for OBSERVED; state={loc['state']!r}")
        elif loc["reason"] not in VALID_LOCATION_REASONS:
            raise ValueError(f"LOCATION: unknown reason {loc['reason']!r}")
        if loc["price_vs_vwap"] is not None and loc["price_vs_vwap"] not in VALID_LOCATION_PRICE_VS_VWAP:
            raise ValueError(f"LOCATION: unknown price_vs_vwap {loc['price_vs_vwap']!r}")
        orb = loc["orb"]
        if orb is not None:
            if orb["state"] not in VALID_LOCATION_ORB_STATES:
                raise ValueError(f"LOCATION.orb: unknown state {orb['state']!r}")
            if orb["reason"] is None:
                if orb["state"] not in _ORB_REASON_NONE_LEGAL:
                    raise ValueError(f"LOCATION.orb: reason required for state {orb['state']!r}")
            elif orb["reason"] not in VALID_LOCATION_ORB_REASONS:
                raise ValueError(f"LOCATION.orb: unknown reason {orb['reason']!r}")

        _validate_xor_cell("STATE", self.state, VALID_SPY_STATE_VALUES, VALID_SPY_STATE_UNAVAILABLE_REASONS)

        # PERMISSION is a total projection: value-only, NO unavailable branch.
        if set(self.permission) != {"value"}:
            raise ValueError(f"PERMISSION: value-only cell required; got keys {sorted(self.permission)!r}")
        if self.permission["value"] not in VALID_PERMISSION_VALUES:
            raise ValueError(f"PERMISSION: unknown value {self.permission['value']!r}")

        ev = self.event
        populated = [k for k in ("events", "value", "unavailable_reason") if ev.get(k) is not None]
        if len(populated) != 1:
            raise ValueError(f"EVENT: exactly one of events/value/unavailable_reason required; got {ev!r}")
        if ev.get("value") is not None and ev["value"] != "no_scheduled_events":
            raise ValueError(f"EVENT: unknown value {ev['value']!r}")
        if ev.get("unavailable_reason") is not None and ev["unavailable_reason"] not in VALID_EVENT_UNAVAILABLE_REASONS:
            raise ValueError(f"EVENT: unknown unavailable reason {ev['unavailable_reason']!r}")
        if ev.get("events") is not None:
            for entry in ev["events"]:
                if set(entry) != {"date", "time_et", "type", "name"}:
                    raise ValueError(f"EVENT: entry keys must be date/time_et/type/name; got {sorted(entry)!r}")
        if ev.get("unavailable_reason") is None and not isinstance(ev.get("expiring"), bool):
            raise ValueError("EVENT: expiring must be a bool on valued/empty cells")

        _validate_xor_cell("TRANSITION", self.transition, VALID_TRANSITION_VALUES, VALID_TRANSITION_UNAVAILABLE_REASONS)
        _validate_xor_cell("INVALIDATION", self.invalidation, VALID_INVALIDATION_VALUES, VALID_INVALIDATION_UNAVAILABLE_REASONS)
        _validate_xor_cell(
            "CANDIDATE-IMPLICATION", self.candidate_implication,
            VALID_CANDIDATE_IMPLICATION_VALUES, VALID_CANDIDATE_IMPLICATION_UNAVAILABLE_REASONS,
        )


def _location_cell(observation: SpyObservation) -> dict:
    reason, price_vs_vwap = observation.reason, observation.price_vs_vwap
    if observation.state == OBSERVED and price_vs_vwap not in VALID_LOCATION_PRICE_VS_VWAP:
        # Zero-volume VWAP: the raw upstream literal price_vs_vwap="UNAVAILABLE"
        # never renders as a value — it normalizes to the reason token.
        reason, price_vs_vwap = "vwap_unavailable", None
    orb = observation.orb
    orb_cell = None
    if orb is not None:
        orb_cell = {"state": orb.state, "reason": orb.reason,
                    "orb_high": orb.orb_high, "orb_low": orb.orb_low}
    return {"state": observation.state, "reason": reason,
            "price_vs_vwap": price_vs_vwap, "orb": orb_cell}


def _state_cell(outcome: SpyStateOutcome) -> dict:
    if outcome.unavailable_reason is not None:
        return {"value": None, "unavailable_reason": outcome.unavailable_reason}
    return {"value": outcome.state.state, "unavailable_reason": None}


def _event_cell(run_at_utc: datetime, schedule_path: Optional[str]) -> dict:
    schedule = load_schedule(schedule_path)
    if not schedule.ok:
        # The loader's free-form error string is log-only — never a card cell.
        logger.info("red-folder schedule unavailable for EVENT: %s", schedule.error)
        return {"events": None, "value": None,
                "unavailable_reason": "event_schedule_unavailable", "expiring": None}
    events = schedule.events_in_window(run_at_utc, 48)
    expiring = schedule.is_expiring(run_at_utc)
    if not events:
        return {"events": None, "value": "no_scheduled_events",
                "unavailable_reason": None, "expiring": expiring}
    return {"events": [{"date": e.date, "time_et": e.time_et, "type": e.type, "name": e.name}
                       for e in events],
            "value": None, "unavailable_reason": None, "expiring": expiring}


def _transition_cell(outcome: SpyStateOutcome) -> dict:
    if outcome.unavailable_reason is not None:
        return {"value": None, "unavailable_reason": "transition_state_unavailable"}
    intra = outcome.state
    if intra.permission_state == STATE_FAILURE_CONFIRMED:
        value = "FAILED_EXPANSION"
    elif intra.failed_reclaim:
        value = "FAILED_RECLAIM"
    elif intra.reclaimed_orb:
        value = "ORB_RECLAIMED"
    elif intra.orb_break_direction == "LONG":
        value = "ORB_BREAK_HOLDING_LONG"
    elif intra.orb_break_direction == "SHORT":
        value = "ORB_BREAK_HOLDING_SHORT"
    elif intra.orb_break_direction is None:
        value = "NO_BREAK"
    else:
        raise ValueError(f"TRANSITION: unenumerated orb_break_direction {intra.orb_break_direction!r}")
    return {"value": value, "unavailable_reason": None}


def _invalidation_cell(guidance_map: dict, outcome: str) -> dict:
    if not guidance_map:
        if outcome == OUTCOME_HALT:
            return {"value": None, "unavailable_reason": "invalidation_inputs_absent"}
        return {"value": "NO_ACTIVE_CANDIDATES", "unavailable_reason": None}
    statuses = {entry.get("status") for entry in guidance_map.values()}
    unenumerated = statuses.difference(_INVALIDATION_SEVERITY)
    if unenumerated:
        raise ValueError(f"INVALIDATION: unenumerated status(es) {sorted(map(repr, unenumerated))}")
    for status in _INVALIDATION_SEVERITY:
        if status in statuses:
            if status == "UNKNOWN":
                # Normalizes; the raw upstream reason string is never projected.
                return {"value": None, "unavailable_reason": "invalidation_indeterminate"}
            return {"value": status, "unavailable_reason": None}
    raise ValueError("INVALIDATION: unreachable — empty status set from non-empty map")


def _visibility_counts(visibility_map: dict) -> dict:
    counts = {"ACTIVE": 0, "NEAR_MISS": 0, "BLOCKED": 0}
    for entry in visibility_map.values():
        status = entry.get("visibility_status")
        if status not in counts:
            raise ValueError(f"CANDIDATE-IMPLICATION: unenumerated visibility status {status!r}")
        counts[status] += 1
    return counts


def _candidate_implication_cell(visibility_map: dict, outcome: str) -> dict:
    if outcome == OUTCOME_HALT:
        return {"value": None, "unavailable_reason": "candidate_inputs_absent"}
    if outcome == OUTCOME_TRADE:
        return {"value": "ACTIONABLE_CANDIDATES", "unavailable_reason": None,
                "counts": _visibility_counts(visibility_map)}
    if outcome == OUTCOME_NO_TRADE:
        if not visibility_map:
            return {"value": "NO_CANDIDATES", "unavailable_reason": None}
        return {"value": "CANDIDATES_PRESENT_NONE_ACTIONABLE", "unavailable_reason": None,
                "counts": _visibility_counts(visibility_map)}
    raise ValueError(f"CANDIDATE-IMPLICATION: unenumerated outcome {outcome!r}")


def build_market_control_card(
    *,
    observation: SpyObservation,
    spy_state_outcome: SpyStateOutcome,
    permission: str,
    run_at_utc: datetime,
    invalidation_guidance_map: dict,
    visibility_map: dict,
    outcome: str,
    schedule_path: Optional[str] = None,
) -> MarketControlCard:
    """Compose the card for one eligible daily run. ``schedule_path`` is a
    test seam forwarded to ``red_folder.load_schedule`` (default: the
    production schedule)."""
    return MarketControlCard(
        location=_location_cell(observation),
        state=_state_cell(spy_state_outcome),
        permission={"value": permission},
        event=_event_cell(run_at_utc, schedule_path),
        transition=_transition_cell(spy_state_outcome),
        invalidation=_invalidation_cell(invalidation_guidance_map, outcome),
        candidate_implication=_candidate_implication_cell(visibility_map, outcome),
    )
