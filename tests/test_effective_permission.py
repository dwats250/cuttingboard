"""PRD-339 Slice 1 (Authority Core): resolver / carrier / identity / monotonic /
Q4 recovery / admission unit tests + the discriminating tests for mutation proofs
M1 (carry originates), M2 (rank max), M3 (recovery predicate), M6 (run_uid), M7
(fail-closed admission). See PRD-339.md R1-R8 and MUTATION PROOFS."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cuttingboard import effective_permission as ep

SD = "2026-04-12"


def _daily(*, trade=False, halted=False, locked=False, session=SD, uid="LIVE-1",
           accepted=None) -> ep.EffectivePermission:
    return ep.resolve_effective_permission(
        outcome_is_trade=trade, system_halted=halted, operator_locked=locked,
        session_date=session, decision_uid=uid, run_uid=ep.new_run_uid(),
        posture_permission_line="POSTURE", operator_lock_line="LOCKED",
        accepted=accepted)


# --- R1: origination only by an admitted daily decision -----------------------

def test_resolve_permitted_only_for_daily_actionable() -> None:
    assert _daily(trade=True).verdict == ep.VERDICT_PERMITTED
    assert _daily(trade=False).verdict == ep.VERDICT_NO_TRADE  # no actionable candidate


def test_resolve_halt_then_lock_precedence() -> None:
    assert _daily(trade=True, halted=True).verdict == ep.VERDICT_HALT
    assert _daily(trade=True, locked=True).verdict == ep.VERDICT_OBSERVE_ONLY


def test_resolve_permission_line_matches_precedence() -> None:
    assert _daily(trade=True).permission_line == "POSTURE"
    assert _daily(trade=True, locked=True).permission_line == "LOCKED"
    assert _daily(halted=True).permission_line == "No trades permitted. System halted."


# --- R1 (M1): carry_forward carries, never originates permission ---------------

def test_carry_forward_does_not_originate_permitted() -> None:
    accepted = _daily(trade=False)  # NO_TRADE
    carried = ep.carry_forward(accepted=accepted, run_uid=ep.new_run_uid())
    assert carried.verdict != ep.VERDICT_PERMITTED          # never originates
    assert carried.decision_uid == accepted.decision_uid    # Q1 carry (same identity)
    assert carried.decision_seq == accepted.decision_seq    # observations never increment
    assert carried.restriction_rank >= accepted.restriction_rank


def test_carry_forward_carries_admitted_permitted() -> None:
    accepted = _daily(trade=True)  # PERMITTED daily
    carried = ep.carry_forward(accepted=accepted, run_uid=ep.new_run_uid())
    assert carried.verdict == ep.VERDICT_PERMITTED          # benign hourly carries it
    assert carried.decision_uid == accepted.decision_uid


# --- R2 (M2): monotonic restriction; rank = max, never lowered ----------------

def test_hourly_halt_raises_rank() -> None:
    permitted = _daily(trade=True)  # rank 0
    halted = ep.carry_forward(accepted=permitted, run_uid=ep.new_run_uid(),
                              observed_halted=True)
    assert halted.restriction_rank == ep._RANK[ep.VERDICT_HALT]  # raised


def test_lower_ranked_observation_never_lowers_prior_restriction() -> None:
    accepted_halt = _daily(halted=True)  # rank 2
    # an hourly operator-lock (rank 1) must NOT lower an accepted HALT (rank 2).
    carried = ep.carry_forward(accepted=accepted_halt, run_uid=ep.new_run_uid(),
                               observed_operator_locked=True, operator_lock_line="LOCKED")
    assert carried.restriction_rank == accepted_halt.restriction_rank  # rank=max, not lowered
    assert carried.verdict == ep.VERDICT_HALT


def test_benign_hourly_carries_prior_restriction() -> None:
    accepted_halt = _daily(halted=True)  # rank 2
    benign = ep.carry_forward(accepted=accepted_halt, run_uid=ep.new_run_uid())
    assert benign.restriction_rank == accepted_halt.restriction_rank
    assert benign.verdict == ep.VERDICT_HALT


# --- R3 (M3): recovery only by an authorized redecision -----------------------

def test_same_session_redecision_lowers_with_recovery_basis() -> None:
    accepted = _daily(halted=True, uid="LIVE-1")            # rank 2, seq 1
    redec = _daily(trade=True, uid="LIVE-2", accepted=accepted)  # rank 0, seq 2
    assert redec.decision_seq == 2
    assert redec.recovery_basis is not None
    assert redec.recovery_basis["superseded_authority_version"] == list(accepted.authority_version)
    assert ep.is_authorized_redecision(incoming=redec, accepted=accepted) is True


def test_rerun_same_decision_uid_is_not_a_redecision() -> None:
    accepted = _daily(halted=True, uid="LIVE-1")
    rerun = _daily(trade=True, uid="LIVE-1", accepted=accepted)  # SAME uid = rerun
    assert rerun.decision_seq == accepted.decision_seq          # no increment
    assert rerun.recovery_basis is None


def test_redecision_predicate_rejects_without_higher_seq() -> None:
    accepted = _daily(halted=True, uid="LIVE-1")               # seq 1
    fresh = _daily(trade=True, uid="LIVE-1")                    # seq 1, no basis
    assert ep.is_authorized_redecision(incoming=fresh, accepted=accepted) is False


def test_redecision_predicate_rejects_without_recovery_basis() -> None:
    accepted = _daily(halted=True, uid="LIVE-1")
    same_rank = _daily(halted=True, uid="LIVE-2", accepted=accepted)  # seq 2, rank 2, no basis
    assert same_rank.recovery_basis is None
    assert ep.is_authorized_redecision(incoming=same_rank, accepted=accepted) is False


# --- R6: identity sufficiency (run_uid uniqueness; version ordering) ----------

def test_run_uid_stable_within_invocation() -> None:
    # Same process = same invocation -> stable run_uid (byte-identical replays).
    assert ep.new_run_uid() == ep.new_run_uid()
    assert _daily(trade=True).run_uid == ep.new_run_uid()


def test_run_uid_distinct_across_invocations() -> None:
    # Two invocations (processes), even in the same wall-clock second, get distinct
    # run_uids (R6). A mode+second run_uid would collide -> M6 catches this.
    import subprocess
    import sys
    code = "from cuttingboard.effective_permission import new_run_uid as n; print(n())"
    a = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
    b = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.strip()
    assert a and b and a != b


def test_first_session_starts_at_seq_one() -> None:
    assert _daily(trade=True, accepted=None).decision_seq == 1
    prior = _daily(trade=False, session="2026-04-11")
    assert _daily(trade=True, accepted=prior).decision_seq == 1  # different session resets


# --- R7 (M7): fail-closed admission ------------------------------------------

def test_admit_valid_same_session() -> None:
    assert ep.admit_persisted(_daily(trade=False).to_envelope(),
                              current_session_date=SD) is not None


def test_admit_absent_and_malformed() -> None:
    assert ep.admit_persisted(None, current_session_date=SD) is None
    assert ep.admit_persisted({"verdict": "PERMITTED"}, current_session_date=SD) is None


def test_admit_prior_session_refused() -> None:
    env = _daily(trade=True).to_envelope()
    assert ep.admit_persisted(env, current_session_date="2026-04-13") is None


def test_admit_stale_refused() -> None:
    env = _daily(trade=True).to_envelope()
    env["valid_until"] = "2020-01-01T00:00:00+00:00"
    now = datetime(2026, 4, 12, 12, tzinfo=timezone.utc)
    assert ep.admit_persisted(env, current_session_date=SD, now=now) is None


def test_unavailable_is_fail_closed_state() -> None:
    u = ep.unavailable(SD, ep.new_run_uid())
    assert u.verdict == ep.VERDICT_UNAVAILABLE
    assert u.restriction_rank == max(ep._RANK.values())


# --- construction capability (packet s13 R3 in-process) ----------------------

def test_cannot_construct_without_capability() -> None:
    with pytest.raises(ep.EffectivePermissionError):
        ep.EffectivePermission(
            verdict="PERMITTED", restriction_rank=0, decision_uid="x", session_date=SD,
            run_uid="r", authority_version=(SD, 1, 0), valid_until=None,
            recovery_basis=None, permission_line="p", decision_seq=1)
