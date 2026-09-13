"""PRD-339 Slice 1 (Authority Core) unit tests: resolver / carry / identity /
monotonic / Q4 recovery / admission + discriminating tests for M1-M7 and D1-D5.
See PRD-339.md R1-R8 + the impl-review findings."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cuttingboard import effective_permission as ep

SD = "2026-04-12"


def _daily(*, mode="live", trade=False, halted=False, locked=False, session=SD,
           run_uid=None, accepted=None) -> ep.EffectivePermission:
    return ep.resolve_effective_permission(
        mode=mode, outcome_is_trade=trade, system_halted=halted, operator_locked=locked,
        session_date=session, run_uid=run_uid or ep.new_run_uid(),
        posture_permission_line="POSTURE", operator_lock_line="LOCKED",
        accepted=accepted)


# --- R1: origination only by an admitted daily decision -----------------------

def test_resolve_permitted_only_for_daily_actionable() -> None:
    assert _daily(trade=True).verdict == ep.VERDICT_PERMITTED
    assert _daily(trade=False).verdict == ep.VERDICT_NO_TRADE


def test_resolve_halt_then_lock_precedence() -> None:
    assert _daily(trade=True, halted=True).verdict == ep.VERDICT_HALT
    assert _daily(trade=True, locked=True).verdict == ep.VERDICT_OBSERVE_ONLY


def test_resolve_permission_line_matches_precedence() -> None:
    assert _daily(trade=True).permission_line == "POSTURE"
    assert _daily(trade=True, locked=True).permission_line == "LOCKED"
    assert _daily(halted=True).permission_line == "No trades permitted. System halted."


# --- finding 7: only LIVE/SUNDAY may originate authority; others fail-closed ---

def test_authorized_modes_originate_but_fixture_is_fail_closed() -> None:
    assert _daily(mode="live", trade=True).verdict == ep.VERDICT_PERMITTED
    assert _daily(mode="sunday", trade=False).verdict == ep.VERDICT_NO_TRADE
    fx = _daily(mode="fixture", trade=True)  # unauthorized -> never originates PERMITTED
    assert fx.verdict == ep.VERDICT_UNAVAILABLE
    assert _daily(mode="prefetch", trade=True).verdict == ep.VERDICT_UNAVAILABLE


# --- R1 (M1): carry_forward carries, never originates permission ---------------

def test_carry_forward_does_not_originate_permitted() -> None:
    accepted = _daily(trade=False)  # NO_TRADE
    carried = ep.carry_forward(accepted=accepted)
    assert carried.verdict != ep.VERDICT_PERMITTED
    assert carried.decision_uid == accepted.decision_uid    # Q1 carry (same identity)
    assert carried.decision_seq == accepted.decision_seq    # observations never increment
    assert carried.restriction_rank >= accepted.restriction_rank


def test_carry_forward_carries_admitted_permitted() -> None:
    accepted = _daily(trade=True)  # PERMITTED daily
    carried = ep.carry_forward(accepted=accepted)
    assert carried.verdict == ep.VERDICT_PERMITTED
    assert carried.decision_uid == accepted.decision_uid


# --- R2 (M2): monotonic restriction; rank = max, never lowered ----------------

def test_hourly_halt_raises_rank() -> None:
    permitted = _daily(trade=True)  # rank 0
    halted = ep.carry_forward(accepted=permitted,
                              observed_halted=True)
    assert halted.restriction_rank == ep._RANK[ep.VERDICT_HALT]


def test_lower_ranked_observation_never_lowers_prior_restriction() -> None:
    accepted_halt = _daily(halted=True)  # rank 2
    carried = ep.carry_forward(accepted=accepted_halt,
                               observed_operator_locked=True, operator_lock_line="LOCKED")
    assert carried.restriction_rank == accepted_halt.restriction_rank  # rank=max
    assert carried.verdict == ep.VERDICT_HALT


# --- nit: a benign carry preserves the accepted permission_line ---------------

def test_benign_carry_preserves_observe_only_permission_line() -> None:
    accepted = _daily(locked=True)  # OBSERVE_ONLY, permission_line "LOCKED"
    # a later benign observation (no operator_lock_line supplied) must NOT blank it.
    carried = ep.carry_forward(accepted=accepted)
    assert carried.verdict == ep.VERDICT_OBSERVE_ONLY
    assert carried.permission_line == "LOCKED"


# --- R6 (M6)/finding 5: identity per invocation, collision-free, retry reuse ---

def test_run_uid_unique_per_invocation() -> None:
    assert ep.new_run_uid() != ep.new_run_uid()  # two in-process invocations distinct


def test_decision_uid_collision_free_same_second_new_decisions() -> None:
    a = _daily(trade=True)  # two distinct new-session decisions
    b = _daily(trade=False)  # same wall-clock second
    assert a.run_uid != b.run_uid
    assert a.decision_uid != b.decision_uid and a.decision_uid and b.decision_uid


def test_idempotent_same_run_reresolve_does_not_increment() -> None:  # D3
    first = _daily(trade=False, run_uid="R1")
    reresolve = _daily(trade=False, run_uid="R1", accepted=first)  # same run_uid -> idempotent
    assert reresolve.decision_uid == first.decision_uid
    assert reresolve.decision_seq == first.decision_seq  # no increment
    assert reresolve.run_uid == first.run_uid
    assert reresolve.to_envelope() == first.to_envelope()
    assert reresolve.recovery_basis is None


# --- D3: production redecision wiring (genuine new admitted daily decision) ----

def test_same_rank_new_daily_decision_increments_seq() -> None:  # D3(b)
    first = _daily(trade=False, run_uid="R1")                       # NO_TRADE, seq 1
    second = _daily(trade=False, run_uid="R2", accepted=first)      # fresh run_uid, same rank
    assert second.decision_seq == 2 and second.decision_uid == "R2"
    assert second.recovery_basis is None                           # same rank -> no recovery


def test_new_daily_decision_lowering_rank_recovers() -> None:  # D3 / Q4
    accepted = _daily(halted=True, run_uid="A1")                    # rank 2, seq 1
    redec = _daily(trade=True, run_uid="A2", accepted=accepted)     # fresh invocation, clears halt
    assert redec.decision_uid == "A2" != accepted.decision_uid
    assert redec.decision_seq == 2 and redec.recovery_basis is not None
    assert redec.recovery_basis["superseding_decision_uid"] == "A2"
    assert redec.verdict == ep.VERDICT_PERMITTED
    assert ep.is_authorized_redecision(incoming=redec, accepted=accepted) is True


def test_redecision_predicate_rejects_mismatched_superseding_uid() -> None:
    accepted = _daily(halted=True, run_uid="A1")
    redec = _daily(trade=True, run_uid="A2", accepted=accepted)
    tampered = ep._mint(**{**redec.to_envelope(),
                           "recovery_basis": {**redec.recovery_basis,
                                              "superseding_decision_uid": "SOMEONE_ELSE"},
                           "authority_version": redec.authority_version})
    assert ep.is_authorized_redecision(incoming=tampered, accepted=accepted) is False


def test_recovery_basis_shape_is_strictly_validated() -> None:  # D4
    accepted = _daily(halted=True, run_uid="A1")
    base = _daily(trade=True, run_uid="A2", accepted=accepted)  # valid recovery
    assert ep.is_authorized_redecision(incoming=base, accepted=accepted) is True

    def _with(rb):
        return ep._mint(**{**base.to_envelope(), "recovery_basis": rb,
                           "authority_version": base.authority_version})
    for bad in (
        {**base.recovery_basis, "superseding_decision_uid": ""},        # blank uid
        {**base.recovery_basis, "superseding_decision_uid": "   "},     # whitespace uid
        {**base.recovery_basis, "superseded_authority_version": []},    # empty
        {**base.recovery_basis, "superseded_authority_version": [SD, 1]},        # wrong len
        {**base.recovery_basis, "superseded_authority_version": [SD, "x", 2]},   # wrong type
    ):
        tampered = _with(bad)
        assert ep.is_authorized_redecision(incoming=tampered, accepted=accepted) is False
        env = tampered.to_envelope()
        assert ep.admit_persisted(env, current_session_date=SD) is None  # R7 fail-closed too


def test_redecision_predicate_rejects_unavailable_incoming() -> None:
    accepted = _daily(halted=True, run_uid="A1")
    unavail = ep.unavailable(SD)  # unauthorized-mode / fail-closed incoming
    assert ep.is_authorized_redecision(incoming=unavail, accepted=accepted) is False


def test_redecision_predicate_rejects_without_higher_seq() -> None:
    accepted = _daily(halted=True, run_uid="A1")
    fresh = _daily(trade=True, run_uid="A2")  # seq 1, no recovery_basis
    assert ep.is_authorized_redecision(incoming=fresh, accepted=accepted) is False


def test_still_locked_redecision_cannot_reach_permitted() -> None:
    accepted = _daily(halted=True, run_uid="A1")
    still_locked = _daily(locked=True, run_uid="A2", accepted=accepted)
    assert still_locked.verdict == ep.VERDICT_OBSERVE_ONLY  # lock not cleared -> not PERMITTED


# --- R6: session identity + seq ----------------------------------------------

def test_new_session_resets_seq_and_mints_uid() -> None:
    prior = _daily(trade=False, session="2026-04-11", run_uid="P1")
    fresh = _daily(trade=True, run_uid="F1", accepted=prior)  # different session
    assert fresh.decision_seq == 1 and fresh.decision_uid == "F1"


# --- R7 (M7)/finding 3: fail-closed admission --------------------------------

def _envelope(**over):
    base = _daily(trade=False, run_uid="RU").to_envelope()
    base.update(over)
    return base


def test_admit_valid_same_session() -> None:
    assert ep.admit_persisted(_envelope(), current_session_date=SD) is not None


def test_admit_absent_and_missing_keys() -> None:
    assert ep.admit_persisted(None, current_session_date=SD) is None
    assert ep.admit_persisted({"verdict": "PERMITTED"}, current_session_date=SD) is None


def test_admit_rejects_unknown_verdict() -> None:
    assert ep.admit_persisted(_envelope(verdict="GO"), current_session_date=SD) is None


def test_admit_rejects_verdict_rank_disagreement() -> None:
    assert ep.admit_persisted(_envelope(restriction_rank=0),  # NO_TRADE rank must be 1
                              current_session_date=SD) is None


def test_admit_rejects_authority_version_mismatch() -> None:
    env = _envelope()
    env["authority_version"] = [SD, 9, env["restriction_rank"]]  # seq disagrees
    assert ep.admit_persisted(env, current_session_date=SD) is None


def test_admit_rejects_empty_identity() -> None:
    assert ep.admit_persisted(_envelope(decision_uid=""), current_session_date=SD) is None
    assert ep.admit_persisted(_envelope(run_uid=""), current_session_date=SD) is None
    assert ep.admit_persisted(_envelope(run_uid=123), current_session_date=SD) is None


def test_admit_rejects_missing_valid_until() -> None:
    assert ep.admit_persisted(_envelope(valid_until=None), current_session_date=SD) is None


def test_admit_rejects_malformed_recovery() -> None:
    assert ep.admit_persisted(_envelope(recovery_basis={"reason": "X"}),
                              current_session_date=SD) is None


def test_admit_prior_session_refused() -> None:
    assert ep.admit_persisted(_envelope(), current_session_date="2026-04-13") is None


def test_admit_stale_refused_and_naive_datetime_does_not_raise() -> None:
    env = _envelope(valid_until="2026-04-13T00:00:00")  # naive (no tz) -> normalized
    aware_now = datetime(2026, 4, 14, tzinfo=timezone.utc)
    assert ep.admit_persisted(env, current_session_date=SD, now=aware_now) is None  # stale, no TypeError
    fresh_now = datetime(2026, 4, 12, 12, tzinfo=timezone.utc)
    assert ep.admit_persisted(env, current_session_date=SD, now=fresh_now) is not None


def test_admit_does_not_readmit_unavailable_sentinel() -> None:
    assert ep.admit_persisted(ep.unavailable(SD).to_envelope(), current_session_date=SD) is None


def test_unavailable_is_deterministic_fail_closed() -> None:
    a, b = ep.unavailable(SD), ep.unavailable(SD)
    assert a.to_envelope() == b.to_envelope()  # byte-stable (R8 paired-run safety)
    assert a.verdict == ep.VERDICT_UNAVAILABLE


def test_run_uid_distinct_across_invocations() -> None:
    import subprocess
    import sys
    code = "from cuttingboard.effective_permission import new_run_uid as n; print(n())"
    a = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
    b = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
    assert a and b and a != b


# --- construction capability (packet s13 R3 in-process) ----------------------

def test_cannot_construct_without_capability() -> None:
    with pytest.raises(ep.EffectivePermissionError):
        ep.EffectivePermission(
            verdict="PERMITTED", restriction_rank=0, decision_uid="x", session_date=SD,
            run_uid="r", authority_version=(SD, 1, 0), valid_until=None,
            recovery_basis=None, permission_line="p", decision_seq=1)
