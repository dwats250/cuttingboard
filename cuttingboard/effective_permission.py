"""PRD-339 SLICE 1 (Authority Core): the canonical EffectivePermission carrier --
carrier + sole resolver + Q1 carry + R5 publication non-regression + R3 redecision
predicate + fail-closed admission (R7) + single approved persistence path (s14, R4).
ADDITIVE (no consumer change); requirements R1-R8 in PRD-339.md."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional

VERDICT_PERMITTED = "PERMITTED"
VERDICT_NO_TRADE = "NO_TRADE"
VERDICT_OBSERVE_ONLY = "OBSERVE_ONLY"
VERDICT_HALT = "HALT"
VERDICT_UNAVAILABLE = "UNAVAILABLE"

_RANK = {VERDICT_PERMITTED: 0, VERDICT_NO_TRADE: 1, VERDICT_OBSERVE_ONLY: 1,
         VERDICT_HALT: 2, VERDICT_UNAVAILABLE: 3}  # higher == more restrictive
CANONICAL_FIELD = "effective_permission"  # the exclusive-writer AST guard keys on this.
RECOVERY_REASON_REDECISION = "REDECISION"
_RECOVERY_REASONS = frozenset({RECOVERY_REASON_REDECISION})
_HALT_LINE = "No trades permitted. System halted."
_DEFAULT_LINE = "No new trades permitted."
_TOKEN = object()  # process-local construction capability (s13 R3 in-process).
_KEYS = frozenset({"verdict", "restriction_rank", "decision_uid", "session_date",
                   "run_uid", "authority_version", "valid_until", "recovery_basis",
                   "permission_line", "decision_seq"})


class EffectivePermissionError(RuntimeError):
    """EffectivePermission constructed without the capability."""


@dataclass(frozen=True)
class EffectivePermission:
    """The ONE resolved effective-permission authority (frozen carrier)."""

    verdict: str
    restriction_rank: int
    decision_uid: str
    session_date: str
    run_uid: str
    authority_version: tuple[str, int, int]  # (session_date, decision_seq, rank)
    valid_until: Optional[str]
    recovery_basis: Optional[dict[str, Any]]
    permission_line: str
    decision_seq: int
    _token: Any = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._token is not _TOKEN:
            raise EffectivePermissionError(
                "EffectivePermission is constructed only by this module's resolver")

    def to_envelope(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict, "restriction_rank": self.restriction_rank,
            "decision_uid": self.decision_uid, "session_date": self.session_date,
            "run_uid": self.run_uid, "authority_version": list(self.authority_version),
            "valid_until": self.valid_until, "recovery_basis": self.recovery_basis,
            "permission_line": self.permission_line, "decision_seq": self.decision_seq}


def _mint(**kw: Any) -> EffectivePermission:
    return EffectivePermission(_token=_TOKEN, **kw)


_RUN_UID = uuid.uuid4().hex  # this process's invocation id (R6)


def new_run_uid() -> str:
    """This process's run_uid (R6): a stable opaque id, distinct across processes,
    never mode+second (which collides same-second); stable within a process."""
    return _RUN_UID


def _valid_until(session_date: str) -> Optional[str]:
    try:  # session_date + 1 day at 08:00Z covers a same-session hourly past midnight.
        d = date.fromisoformat(session_date)
    except (ValueError, TypeError):
        return None
    return datetime.combine(d + timedelta(days=1), time(8, 0), tzinfo=timezone.utc).isoformat()


def resolve_effective_permission(
    *, outcome_is_trade: bool, system_halted: bool, operator_locked: bool,
    session_date: str, decision_uid: str, run_uid: str,
    posture_permission_line: str, operator_lock_line: str,
    accepted: Optional[EffectivePermission] = None,
) -> EffectivePermission:
    """ONLY constructor for an admitted DAILY decision (R1). A same-session run is a
    REDECISION: decision_seq += 1 (R3(a)); a lowered rank attaches recovery_basis (Q4).
    Precedence (halt > operator-lock > outcome) mirrors _build_and_finalize_contract."""
    if system_halted:
        verdict, line = VERDICT_HALT, _HALT_LINE
    elif operator_locked:
        verdict, line = VERDICT_OBSERVE_ONLY, operator_lock_line
    else:
        verdict = VERDICT_PERMITTED if outcome_is_trade else VERDICT_NO_TRADE
        line = posture_permission_line
    rank = _RANK[verdict]
    recovery: Optional[dict[str, Any]] = None
    if accepted is not None and accepted.session_date == session_date:
        if accepted.decision_uid == decision_uid:
            seq = accepted.decision_seq  # rerun of the same decision, not a redecision (R3)
        else:
            seq = accepted.decision_seq + 1  # genuine same-session redecision
            if rank < accepted.restriction_rank:
                recovery = {"superseded_authority_version": list(accepted.authority_version),
                            "superseding_decision_uid": decision_uid,
                            "reason": RECOVERY_REASON_REDECISION}
    else:
        seq = 1
    return _mint(verdict=verdict, restriction_rank=rank, decision_uid=decision_uid,
                 session_date=session_date, run_uid=run_uid,
                 authority_version=(session_date, seq, rank),
                 valid_until=_valid_until(session_date), recovery_basis=recovery,
                 permission_line=line, decision_seq=seq)


def carry_forward(
    *, accepted: EffectivePermission, run_uid: str, observed_halted: bool = False,
    observed_operator_locked: bool = False, operator_lock_line: str = "",
) -> EffectivePermission:
    """Q1 observation carry (hourly): carries the admitted daily decision forward
    (same decision_uid/decision_seq/valid_until); rank = MAX (never lowers/originates/recovers)."""
    if observed_halted:
        obs_v = VERDICT_HALT
    elif observed_operator_locked:
        obs_v = VERDICT_OBSERVE_ONLY
    else:
        obs_v = accepted.verdict  # benign observation asserts nothing new.
    if _RANK[obs_v] >= accepted.restriction_rank:
        verdict, rank = obs_v, _RANK[obs_v]
    else:
        verdict, rank = accepted.verdict, accepted.restriction_rank
    if verdict == VERDICT_HALT:
        line = _HALT_LINE
    elif verdict == VERDICT_OBSERVE_ONLY:
        line = operator_lock_line
    else:
        line = accepted.permission_line
    return _mint(verdict=verdict, restriction_rank=rank, decision_uid=accepted.decision_uid,
                 session_date=accepted.session_date, run_uid=run_uid,
                 authority_version=(accepted.session_date, accepted.decision_seq, rank),
                 valid_until=accepted.valid_until, recovery_basis=None,
                 permission_line=line, decision_seq=accepted.decision_seq)


def unavailable(session_date: str, run_uid: str) -> EffectivePermission:
    """The fail-closed canonical state (R7)."""
    r = _RANK[VERDICT_UNAVAILABLE]
    return _mint(verdict=VERDICT_UNAVAILABLE, restriction_rank=r, decision_uid="",
                 session_date=session_date, run_uid=run_uid,
                 authority_version=(session_date, 0, r), valid_until=None,
                 recovery_basis=None, permission_line=_DEFAULT_LINE, decision_seq=0)


def admit_persisted(
    envelope: Any, *, current_session_date: str, now: Optional[datetime] = None,
) -> Optional[EffectivePermission]:
    """Fail-closed admission at the read boundary (R7): the admitted EP, else None
    (absent/malformed/prior-session/stale). Never raises/fabricates/retains a grant."""
    if not isinstance(envelope, dict) or not _KEYS.issubset(envelope.keys()):
        return None
    try:
        av = envelope["authority_version"]
        ep = _mint(verdict=envelope["verdict"], restriction_rank=int(envelope["restriction_rank"]),
                   decision_uid=envelope["decision_uid"], session_date=envelope["session_date"],
                   run_uid=envelope["run_uid"], authority_version=(str(av[0]), int(av[1]), int(av[2])),
                   valid_until=envelope.get("valid_until"), recovery_basis=envelope.get("recovery_basis"),
                   permission_line=envelope.get("permission_line", _DEFAULT_LINE),
                   decision_seq=int(envelope["decision_seq"]))
    except (KeyError, TypeError, ValueError, IndexError):
        return None
    if ep.session_date != current_session_date:
        return None
    if now is not None and ep.valid_until:
        try:
            if now > datetime.fromisoformat(ep.valid_until):
                return None
        except (ValueError, TypeError):
            return None
    return ep


def is_authorized_redecision(*, incoming: EffectivePermission,
                             accepted: EffectivePermission) -> bool:
    """R3 predicate for a LOWER-rank admission: strictly higher decision_seq AND a
    recovery_basis referencing accepted.authority_version."""
    rb = incoming.recovery_basis
    return (incoming.decision_seq > accepted.decision_seq and isinstance(rb, dict)
            and rb.get("reason") in _RECOVERY_REASONS
            and rb.get("superseded_authority_version") == list(accepted.authority_version))


def _av(env: dict[str, Any]) -> tuple[str, int, int]:
    av = env["authority_version"]
    return (str(av[0]), int(av[1]), int(av[2]))


def publication_admits(accepted_envelope: Optional[dict[str, Any]],
                       incoming_envelope: Optional[dict[str, Any]]) -> bool:
    """R5 non-regression: compare authority_version lexicographically (never a
    timestamp, R6). Admit only when (a) not behind, (b) no equal-seq downgrade,
    (c) a lower rank across a higher decision_seq carries a validated recovery_basis
    (Q4), (d) equal version is a no-op only for the same decision_uid. Missing
    incoming -> refuse; missing accepted (bootstrap) -> admit."""
    if not isinstance(incoming_envelope, dict):
        return False
    if not isinstance(accepted_envelope, dict):
        return True
    try:
        inc, acc = _av(incoming_envelope), _av(accepted_envelope)
    except (KeyError, TypeError, ValueError, IndexError):
        return False
    (inc_d, inc_s, inc_r), (acc_d, acc_s, acc_r) = inc, acc
    if inc_d < acc_d:                              # (a) older session
        return False
    if inc_d == acc_d and inc_s < acc_s:           # (a) older decision
        return False
    if inc == acc:                                 # (d) equal-version: no-op iff same decision
        return incoming_envelope.get("decision_uid") == accepted_envelope.get("decision_uid")
    if inc_d == acc_d and inc_s == acc_s:          # (b) intra-decision downgrade
        return inc_r >= acc_r
    if inc_d == acc_d and inc_s > acc_s and inc_r < acc_r:   # (c) recovery-gated
        rb = incoming_envelope.get("recovery_basis")
        return (isinstance(rb, dict) and rb.get("reason") in _RECOVERY_REASONS
                and rb.get("superseded_authority_version") == list(acc))
    return True


def persist(carrier: dict[str, Any], ep: EffectivePermission) -> dict[str, Any]:
    """SINGLE approved persistence path (packet s14, R4): write the canonical field
    onto a carrier. No other module may author it."""
    carrier[CANONICAL_FIELD] = ep.to_envelope()
    return carrier


def persist_copy(dst: dict[str, Any], src: dict[str, Any]) -> dict[str, Any]:
    """Verbatim copy of the resolved canonical field between carriers (a read, not
    authorship)."""
    if isinstance(src, dict) and CANONICAL_FIELD in src:
        dst[CANONICAL_FIELD] = src[CANONICAL_FIELD]
    return dst


def _read_authority(path: str) -> Optional[dict[str, Any]]:
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data[CANONICAL_FIELD] if isinstance(data, dict) and isinstance(
        data.get(CANONICAL_FIELD), dict) else None


def _cli(argv: list[str]) -> int:
    # R5 publisher gate for ci_push_artifacts.sh: publication-admits A B -> 0/1/2.
    if len(argv) != 3 or argv[0] != "publication-admits":
        print("usage: publication-admits <accepted.json> <incoming.json>")
        return 2
    return 0 if publication_admits(_read_authority(argv[1]), _read_authority(argv[2])) else 1


if __name__ == "__main__":  # pragma: no cover
    import sys
    raise SystemExit(_cli(sys.argv[1:]))
