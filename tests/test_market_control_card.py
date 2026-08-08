"""PRD-289 — Market Control Card composer (NS-2E).

Composer surface of the discriminating matrix: M10 (cell vocabulary
enforcement), M13 (PERMISSION total under every observation state), M15–M22,
M24, plus the R5 named zero-volume LOCATION case. Pipeline/payload/renderer
halves (M1/M2/M11/M12/M14/M23) live in the runtime, payload, and renderer
test modules.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import date, datetime, timezone

import pytest

from cuttingboard.intraday_state_engine import IntraState
from cuttingboard.market_control_card import (
    VALID_CANDIDATE_IMPLICATION_UNAVAILABLE_REASONS,
    VALID_CANDIDATE_IMPLICATION_VALUES,
    VALID_EVENT_UNAVAILABLE_REASONS,
    VALID_INVALIDATION_UNAVAILABLE_REASONS,
    VALID_INVALIDATION_VALUES,
    VALID_PERMISSION_UNAVAILABLE_REASONS,
    VALID_PERMISSION_VALUES,
    VALID_TRANSITION_UNAVAILABLE_REASONS,
    VALID_TRANSITION_VALUES,
    MarketControlCard,
    build_market_control_card,
)
from cuttingboard.spy_observation import OBSERVED, SpyObservation
from cuttingboard.spy_state import SpyStateOutcome

RUN_AT = datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc)  # 10:00 ET
HALT_LINE = "No trades permitted. System halted."
POSTURE_LINE = "Selective only — defined risk, R:R >= 3:1."


def _intra(**overrides) -> IntraState:
    base = dict(
        symbol="SPY", timestamp="2026-04-28T14:00:00+00:00", orb_high=455.0,
        orb_low=450.0, current_price=456.0, orb_break_direction=None,
        holding_bars=0, reclaimed_orb=False, permission_state="NONE",
        trades_allowed=False, gap_type="FLAT", phase="POST_OPEN",
        failed_reclaim=False, acceptance_below_level=False,
        consecutive_closes_below_level=0, vwap=452.0, vwap_position="ABOVE",
        volume_trend="FLAT", state="RANGE", confidence=0.5, time_window="PRIMARY",
    )
    base.update(overrides)
    return IntraState(**base)


def _obs(state: str = OBSERVED, reason=None, price_vs_vwap="ABOVE", vwap=452.0) -> SpyObservation:
    return SpyObservation(
        observed_symbol="SPY", intended_session_date=date(2026, 4, 28),
        timezone="America/New_York", observed_at_utc=None, state=state,
        reason=reason, session_vwap=vwap, current_price=456.0,
        price_vs_vwap=price_vs_vwap, orb=None,
    )


def _guidance(status: str, reason=None) -> dict:
    return {"status": status, "action": "HOLD_OK", "reason": reason,
            "triggered_by": None, "thesis_status": "OK"}


def _visible(status: str = "ACTIVE") -> dict:
    return {"visibility_status": status, "visibility_reason": None, "enable_conditions": []}


@pytest.fixture
def empty_schedule(tmp_path) -> str:
    path = tmp_path / "red_folder.json"
    path.write_text(json.dumps({"events": []}), encoding="utf-8")
    return str(path)


def _card(empty_schedule: str, **overrides) -> MarketControlCard:
    kwargs = dict(
        observation=_obs(),
        spy_state_outcome=SpyStateOutcome(state=_intra()),
        permission=POSTURE_LINE,
        run_at_utc=RUN_AT,
        invalidation_guidance_map={},
        visibility_map={},
        outcome="NO_TRADE",
        schedule_path=empty_schedule,
    )
    kwargs.update(overrides)
    return build_market_control_card(**kwargs)


def _card_strings(card: MarketControlCard) -> list[str]:
    found: list[str] = []

    def walk(node) -> None:
        if isinstance(node, str):
            found.append(node)
        elif isinstance(node, dict):
            for key, value in node.items():
                walk(key), walk(value)
        elif isinstance(node, (list, tuple)):
            for value in node:
                walk(value)

    for cell in (card.location, card.state, card.permission, card.event,
                 card.transition, card.invalidation, card.candidate_implication):
        walk(cell)
    return found


# --- R5 named case: OBSERVED + zero volume -> vwap_unavailable, never the raw literal ---
def test_location_zero_volume_normalizes_to_vwap_unavailable(empty_schedule):
    zero_volume_obs = _obs(price_vs_vwap="UNAVAILABLE", vwap=None)
    card = _card(empty_schedule, observation=zero_volume_obs)
    assert card.location["state"] == "OBSERVED"
    assert card.location["reason"] == "vwap_unavailable"
    assert card.location["price_vs_vwap"] is None
    assert "UNAVAILABLE" not in _card_strings(card)  # the raw upstream literal never enters the card


def test_location_projects_observation_axes(empty_schedule):
    card = _card(empty_schedule)
    assert card.location == {"state": "OBSERVED", "reason": None, "price_vs_vwap": "ABOVE", "orb": None}


# --- M10 (composer cells): unknown token in any field's cell fails construction ---
@pytest.mark.parametrize("field,bad_cell", [
    ("location", {"state": "OBSERVED", "reason": "no_truthful_producer", "price_vs_vwap": None, "orb": None}),
    ("location", {"state": "GONE", "reason": "pre_open", "price_vs_vwap": None, "orb": None}),
    ("location", {"state": "PRE_OPEN", "reason": None, "price_vs_vwap": None, "orb": None}),
    ("location", {"state": "OBSERVED", "reason": None, "price_vs_vwap": "UNAVAILABLE", "orb": None}),
    ("location", {"state": "OBSERVED", "reason": None, "price_vs_vwap": None,
                  "orb": {"state": "UNAVAILABLE", "reason": None, "orb_high": None, "orb_low": None}}),
    ("state", {"value": "TRENDING", "unavailable_reason": None}),
    ("state", {"value": None, "unavailable_reason": "no_truthful_producer"}),
    ("permission", {"value": "Anything goes."}),
    ("permission", {"value": None, "unavailable_reason": "permission_uncomputable"}),
    ("event", {"events": None, "value": "nothing_scheduled", "unavailable_reason": None, "expiring": False}),
    ("event", {"events": None, "value": None, "unavailable_reason": "schedule_missing", "expiring": None}),
    ("transition", {"value": "SIDEWAYS", "unavailable_reason": None}),
    ("transition", {"value": None, "unavailable_reason": "no_truthful_producer"}),
    ("invalidation", {"value": "UNKNOWN", "unavailable_reason": None}),
    ("invalidation", {"value": None, "unavailable_reason": "INSUFFICIENT_DETERMINISTIC_INPUTS"}),
    ("candidate_implication", {"value": "CANDIDATES_BLOCKED_OR_NEAR_MISS", "unavailable_reason": None}),
    ("candidate_implication", {"value": None, "unavailable_reason": "candidate_implication_uncomposable"}),
])
def test_m10_unknown_tokens_fail_construction(empty_schedule, field, bad_cell):
    card = _card(empty_schedule)
    with pytest.raises(ValueError):
        dataclasses.replace(card, **{field: bad_cell})


def test_m10_xor_cells_reject_both_and_neither(empty_schedule):
    card = _card(empty_schedule)
    with pytest.raises(ValueError):
        dataclasses.replace(card, state={"value": "RANGE", "unavailable_reason": "insufficient_bars"})
    with pytest.raises(ValueError):
        dataclasses.replace(card, transition={"value": None, "unavailable_reason": None})


# --- M13 (composer half): PERMISSION stays VALUED in every observation state ---
@pytest.mark.parametrize("obs_state,obs_reason,seam_reason", [
    ("PRE_OPEN", "pre_open", "non_current_observation"),
    ("STALE", "session_mismatch", "non_current_observation"),
    ("STALE", "observation_lag", "non_current_observation"),
])
def test_m13_state_cascades_while_permission_stays_valued(empty_schedule, obs_state, obs_reason, seam_reason):
    card = _card(
        empty_schedule,
        observation=_obs(state=obs_state, reason=obs_reason, price_vs_vwap=None, vwap=None),
        spy_state_outcome=SpyStateOutcome(unavailable_reason=seam_reason),
    )
    assert card.state == {"value": None, "unavailable_reason": seam_reason}
    assert card.permission == {"value": POSTURE_LINE}


def test_m13_halt_observation_keeps_permission_valued(empty_schedule):
    card = _card(
        empty_schedule,
        observation=_obs(state="UNAVAILABLE", reason="system_halted", price_vs_vwap=None, vwap=None),
        spy_state_outcome=SpyStateOutcome(unavailable_reason="observation_unavailable"),
        permission=HALT_LINE,
        invalidation_guidance_map={},
        visibility_map={},
        outcome="HALT",
    )
    assert card.state == {"value": None, "unavailable_reason": "observation_unavailable"}
    assert card.permission == {"value": HALT_LINE}


# --- M15: EVENT valued from run_at_utc, never wall-clock ---
def test_m15_event_window_keyed_on_run_at_not_wall_clock(tmp_path):
    # In-window for RUN_AT (2026-04-28 + 48 h) but far outside any 2026-08+
    # wall-clock window: a now()-keyed implementation returns empty here.
    schedule = tmp_path / "red_folder.json"
    schedule.write_text(json.dumps({"events": [
        {"date": "2026-04-29", "time_et": "08:30", "type": "CPI", "name": "CPI (April)"},
        {"date": "2026-12-31", "time_et": "10:00", "type": "FOMC", "name": "FOMC (far future)"},
    ]}), encoding="utf-8")
    card = _card(str(schedule), schedule_path=str(schedule))
    assert card.event["events"] == [
        {"date": "2026-04-29", "time_et": "08:30", "type": "CPI", "name": "CPI (April)"},
    ]
    assert card.event["value"] is None
    assert card.event["unavailable_reason"] is None
    assert card.event["expiring"] is False


# --- M16: truthful empty is a VALUE, not an unavailable token ---
def test_m16_zero_events_is_truthful_no_scheduled_events(empty_schedule):
    card = _card(empty_schedule)
    assert card.event["value"] == "no_scheduled_events"
    assert card.event["unavailable_reason"] is None
    assert card.event["events"] is None


# --- M17: missing/malformed schedule -> unavailable; error string never projected ---
def test_m17_missing_schedule_is_unavailable_and_error_string_absent(tmp_path):
    missing = tmp_path / "absent" / "red_folder.json"
    card = _card(str(missing), schedule_path=str(missing))
    assert card.event["unavailable_reason"] == "event_schedule_unavailable"
    assert card.event["value"] is None and card.event["events"] is None
    for text in _card_strings(card):
        assert str(missing) not in text
        assert "not found" not in text


def test_m17_malformed_schedule_is_unavailable(tmp_path):
    malformed = tmp_path / "red_folder.json"
    malformed.write_text("{not json", encoding="utf-8")
    card = _card(str(malformed), schedule_path=str(malformed))
    assert card.event["unavailable_reason"] == "event_schedule_unavailable"


# --- M18: PERMISSION total projection; no unavailable branch exists ---
def test_m18_permission_is_verbatim_and_total(empty_schedule):
    halted = _card(
        empty_schedule, permission=HALT_LINE, outcome="HALT",
        observation=_obs(state="UNAVAILABLE", reason="system_halted", price_vs_vwap=None, vwap=None),
        spy_state_outcome=SpyStateOutcome(unavailable_reason="observation_unavailable"),
    )
    assert halted.permission == {"value": HALT_LINE}
    assert _card(empty_schedule).permission == {"value": POSTURE_LINE}
    assert VALID_PERMISSION_UNAVAILABLE_REASONS == frozenset()
    with pytest.raises(ValueError):  # an unavailable-shaped PERMISSION cell cannot be constructed
        dataclasses.replace(_card(empty_schedule),
                            permission={"value": None, "unavailable_reason": "observation_unavailable"})


# --- M19: INVALIDATION empty-map split by outcome ---
def test_m19_empty_map_split(empty_schedule):
    non_halt = _card(empty_schedule, invalidation_guidance_map={}, outcome="NO_TRADE")
    assert non_halt.invalidation == {"value": "NO_ACTIVE_CANDIDATES", "unavailable_reason": None}
    halt = _card(empty_schedule, invalidation_guidance_map={}, outcome="HALT", permission=HALT_LINE)
    assert halt.invalidation == {"value": None, "unavailable_reason": "invalidation_inputs_absent"}


# --- M20: CANDIDATE-IMPLICATION split, incl. the F3 ACTIVE-only fixture ---
def test_m20_candidate_implication_split(empty_schedule):
    assert _card(empty_schedule, outcome="NO_TRADE", visibility_map={}).candidate_implication == {
        "value": "NO_CANDIDATES", "unavailable_reason": None,
    }
    halt = _card(empty_schedule, outcome="HALT", permission=HALT_LINE)
    assert halt.candidate_implication == {"value": None, "unavailable_reason": "candidate_inputs_absent"}
    trade = _card(empty_schedule, outcome="TRADE",
                  visibility_map={"NVDA": _visible("ACTIVE"), "AMD": _visible("BLOCKED")})
    assert trade.candidate_implication == {
        "value": "ACTIONABLE_CANDIDATES", "unavailable_reason": None,
        "counts": {"ACTIVE": 1, "NEAR_MISS": 0, "BLOCKED": 1},
    }


def test_m20_f3_active_only_map_is_none_actionable(empty_schedule):
    # Policy-allowed NON_TRADABLE symbol: visibility ACTIVE yet outcome NO_TRADE —
    # the truthful cover-all with nothing blocked or near-miss.
    card = _card(empty_schedule, outcome="NO_TRADE", visibility_map={"NVDA": _visible("ACTIVE")})
    assert card.candidate_implication == {
        "value": "CANDIDATES_PRESENT_NONE_ACTIONABLE", "unavailable_reason": None,
        "counts": {"ACTIVE": 1, "NEAR_MISS": 0, "BLOCKED": 0},
    }


# --- M21: UNKNOWN normalizes; the raw upstream reason string appears nowhere ---
def test_m21_unknown_normalizes_to_invalidation_indeterminate(empty_schedule):
    card = _card(empty_schedule, invalidation_guidance_map={
        "NVDA": _guidance("UNKNOWN", reason="INSUFFICIENT_DETERMINISTIC_INPUTS"),
    })
    assert card.invalidation == {"value": None, "unavailable_reason": "invalidation_indeterminate"}
    assert "INSUFFICIENT_DETERMINISTIC_INPUTS" not in _card_strings(card)


# --- M22: TRANSITION six-row precedence + cascade ---
@pytest.mark.parametrize("intra_overrides,expected", [
    # Overlapping flags per row make any precedence reorder red.
    (dict(permission_state="FAILURE_CONFIRMED", failed_reclaim=True, reclaimed_orb=True,
          orb_break_direction="LONG"), "FAILED_EXPANSION"),
    (dict(failed_reclaim=True, reclaimed_orb=True, orb_break_direction="SHORT"), "FAILED_RECLAIM"),
    (dict(reclaimed_orb=True, orb_break_direction="LONG"), "ORB_RECLAIMED"),
    (dict(orb_break_direction="LONG"), "ORB_BREAK_HOLDING_LONG"),
    (dict(orb_break_direction="SHORT"), "ORB_BREAK_HOLDING_SHORT"),
    (dict(orb_break_direction=None), "NO_BREAK"),
])
def test_m22_transition_precedence(empty_schedule, intra_overrides, expected):
    card = _card(empty_schedule, spy_state_outcome=SpyStateOutcome(state=_intra(**intra_overrides)))
    assert card.transition == {"value": expected, "unavailable_reason": None}


def test_m22_state_unavailable_cascades_to_transition(empty_schedule):
    card = _card(empty_schedule, spy_state_outcome=SpyStateOutcome(unavailable_reason="pre_computation_window"))
    assert card.transition == {"value": None, "unavailable_reason": "transition_state_unavailable"}


# --- M24: INVALIDATION mixed-status precedence — the complete stated total order ---
@pytest.mark.parametrize("statuses,expected_cell", [
    (["TRIGGERED", "WARNING"], {"value": "TRIGGERED", "unavailable_reason": None}),
    (["TRIGGERED", "UNKNOWN"], {"value": "TRIGGERED", "unavailable_reason": None}),
    (["WARNING", "UNKNOWN"], {"value": "WARNING", "unavailable_reason": None}),
    (["WARNING", "NOT_TRIGGERED"], {"value": "WARNING", "unavailable_reason": None}),
    (["UNKNOWN", "NOT_TRIGGERED"], {"value": None, "unavailable_reason": "invalidation_indeterminate"}),
    (["NOT_TRIGGERED", "NOT_TRIGGERED"], {"value": "NOT_TRIGGERED", "unavailable_reason": None}),
])
def test_m24_mixed_status_precedence(empty_schedule, statuses, expected_cell):
    guidance_map = {f"SYM{i}": _guidance(status) for i, status in enumerate(statuses)}
    card = _card(empty_schedule, invalidation_guidance_map=guidance_map)
    assert card.invalidation == expected_cell


# --- Closed vocabularies pinned exactly (removed v0.3 tokens cannot reappear) ---
def test_vocabularies_are_exactly_the_packet_sets():
    assert VALID_TRANSITION_VALUES == {"NO_BREAK", "ORB_BREAK_HOLDING_LONG", "ORB_BREAK_HOLDING_SHORT",
                                       "ORB_RECLAIMED", "FAILED_RECLAIM", "FAILED_EXPANSION"}
    assert VALID_TRANSITION_UNAVAILABLE_REASONS == {"transition_state_unavailable", "transition_deferred"}
    assert VALID_INVALIDATION_VALUES == {"NOT_TRIGGERED", "WARNING", "TRIGGERED", "NO_ACTIVE_CANDIDATES"}
    assert VALID_INVALIDATION_UNAVAILABLE_REASONS == {
        "invalidation_deferred_d2", "invalidation_inputs_absent", "invalidation_indeterminate"}
    assert VALID_CANDIDATE_IMPLICATION_VALUES == {
        "ACTIONABLE_CANDIDATES", "CANDIDATES_PRESENT_NONE_ACTIONABLE", "NO_CANDIDATES"}
    assert VALID_CANDIDATE_IMPLICATION_UNAVAILABLE_REASONS == {
        "candidate_implication_deferred_d3", "candidate_inputs_absent"}
    assert VALID_EVENT_UNAVAILABLE_REASONS == {"event_schedule_unavailable"}
    assert len(VALID_PERMISSION_VALUES) == 7
