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
_VALID_VERDICTS = frozenset(_RANK)
_ADMITTED_VERDICTS = frozenset({VERDICT_PERMITTED, VERDICT_NO_TRADE,
                                VERDICT_OBSERVE_ONLY, VERDICT_HALT})
# Only these pipeline modes may originate authority (R3/finding 7); others fail-closed.
AUTHORIZED_DAILY_MODES = frozenset({"live", "sunday"})
CANONICAL_FIELD = "effective_permission"  # the exclusive-writer AST guard keys on this.
RECOVERY_REASON_REDECISION = "REDECISION"
_RECOVERY_REASONS = frozenset({RECOVERY_REASON_REDECISION})
_RECOVERY_KEYS = frozenset({"superseded_authority_version", "superseding_decision_uid", "reason"})
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


def new_run_uid() -> str:
    """A fresh run_uid, unique per pipeline invocation (R6). The caller mints ONE
    per _run_pipeline / hourly invocation and threads it stably through the run."""
    return uuid.uuid4().hex


def _valid_until(session_date: str) -> Optional[str]:
    try:  # session_date + 1 day at 08:00Z covers a same-session hourly past midnight.
        d = date.fromisoformat(session_date)
    except (ValueError, TypeError):
        return None
    return datetime.combine(d + timedelta(days=1), time(8, 0), tzinfo=timezone.utc).isoformat()


def unavailable(session_date: str, run_uid: str = "") -> EffectivePermission:
    """The fail-closed canonical state (R7): a deterministic sentinel (default empty
    identity) that admit_persisted never re-admits as a valid authority."""
    r = _RANK[VERDICT_UNAVAILABLE]
    return _mint(verdict=VERDICT_UNAVAILABLE, restriction_rank=r, decision_uid="",
                 session_date=str(session_date), run_uid=run_uid,
                 authority_version=(str(session_date), 0, r), valid_until=None,
                 recovery_basis=None, permission_line=_DEFAULT_LINE, decision_seq=0)


def resolve_effective_permission(
    *, mode: str, outcome_is_trade: bool, system_halted: bool, operator_locked: bool,
    session_date: str, run_uid: str, posture_permission_line: str, operator_lock_line: str,
    accepted: Optional[EffectivePermission] = None,
) -> EffectivePermission:
    """ONLY constructor for an admitted DAILY decision (R1). Fail-closed for
    unauthorized modes (finding 7). Every genuine new admitted daily decision is a
    full LIVE/SUNDAY chain resolve carrying a FRESH per-invocation run_uid; it mints a
    new decision_uid, increments decision_seq (D3 -- even at the SAME rank), and
    attaches recovery_basis when it LOWERS restriction (Q4/R3, valid for any genuine
    new decision incl. a changed-input re-dispatch). An idempotent same-run re-resolve
    (run_uid == accepted.run_uid) REUSES the identity -> byte-identical envelope
    (R5(d)/D1); a publish-retry re-pushes the prior artifact and never re-resolves.
    A new session starts seq=1. Redecision is NEVER inferred from rank."""
    if mode not in AUTHORIZED_DAILY_MODES:
        return unavailable(session_date)
    if system_halted:
        verdict, line = VERDICT_HALT, _HALT_LINE
    elif operator_locked:
        verdict, line = VERDICT_OBSERVE_ONLY, operator_lock_line
    else:
        verdict = VERDICT_PERMITTED if outcome_is_trade else VERDICT_NO_TRADE
        line = posture_permission_line
    rank = _RANK[verdict]
    recovery: Optional[dict[str, Any]] = None
    same_session = accepted is not None and accepted.session_date == session_date
    if same_session and run_uid == accepted.run_uid:
        decision_uid, seq = accepted.decision_uid, accepted.decision_seq  # idempotent re-resolve
    elif same_session:
        decision_uid, seq = run_uid, accepted.decision_seq + 1            # genuine new daily decision
        if rank < accepted.restriction_rank:
            recovery = {"superseded_authority_version": list(accepted.authority_version),
                        "superseding_decision_uid": run_uid,
                        "reason": RECOVERY_REASON_REDECISION}
    else:
        decision_uid, seq = run_uid, 1                                    # new session
    return _mint(verdict=verdict, restriction_rank=rank, decision_uid=decision_uid,
                 session_date=session_date, run_uid=run_uid,
                 authority_version=(session_date, seq, rank),
                 valid_until=_valid_until(session_date), recovery_basis=recovery,
                 permission_line=line, decision_seq=seq)


def carry_forward(
    *, accepted: EffectivePermission, observed_halted: bool = False,
    observed_operator_locked: bool = False, operator_lock_line: str = "",
) -> EffectivePermission:
    """Q1 observation carry (hourly): carries the admitted daily decision forward
    (same decision_uid/decision_seq/valid_until AND same run_uid -- the observation
    produces no new authority, so a benign carry is byte-identical to the accepted
    envelope, R5(d)/D1); rank = MAX (never lowers/originates/recovers). A benign
    observation preserves accepted.permission_line (nit)."""
    if observed_halted:
        obs_v = VERDICT_HALT
    elif observed_operator_locked:
        obs_v = VERDICT_OBSERVE_ONLY
    else:
        obs_v = accepted.verdict  # benign observation asserts nothing new.
    if _RANK[obs_v] > accepted.restriction_rank:
        verdict, rank = obs_v, _RANK[obs_v]        # this observation newly raises restriction
        line = _HALT_LINE if verdict == VERDICT_HALT else operator_lock_line
    else:
        verdict, rank = accepted.verdict, accepted.restriction_rank  # carried, never lowered
        line = accepted.permission_line            # preserve, do not blank (nit)
    return _mint(verdict=verdict, restriction_rank=rank, decision_uid=accepted.decision_uid,
                 session_date=accepted.session_date, run_uid=accepted.run_uid,
                 authority_version=(accepted.session_date, accepted.decision_seq, rank),
                 valid_until=accepted.valid_until, recovery_basis=None,
                 permission_line=line, decision_seq=accepted.decision_seq)


def _recovery_basis_wellformed(rb: Any) -> bool:
    """D4: closed recovery schema. reason in the enum; a NON-blank superseding
    decision uid; a superseded_authority_version of exactly [session_date:str,
    decision_seq:int, restriction_rank:int]."""
    if not (isinstance(rb, dict) and set(rb.keys()) == _RECOVERY_KEYS
            and rb.get("reason") in _RECOVERY_REASONS):
        return False
    su = rb.get("superseding_decision_uid")
    if not (isinstance(su, str) and su.strip()):
        return False
    sav = rb.get("superseded_authority_version")
    return (isinstance(sav, (list, tuple)) and len(sav) == 3
            and isinstance(sav[0], str) and sav[0]
            and isinstance(sav[1], int) and not isinstance(sav[1], bool)
            and isinstance(sav[2], int) and not isinstance(sav[2], bool))


def _valid_canonical(env: Any) -> bool:
    """Closed-schema + cross-field validation shared by admit_persisted and the
    publisher (D2, DRY): the EXACT canonical key set (no extra fields), a known
    verdict, non-empty typed identity, string valid_until/permission_line, a
    recovery_basis that is None or well-formed, rank == _RANK[verdict], decision_seq
    >= 1, and authority_version == [session_date, decision_seq, restriction_rank]."""
    if not isinstance(env, dict) or set(env.keys()) != _KEYS:
        return False
    verdict, sd = env["verdict"], env["session_date"]
    du, ru, vu, pl, rb = (env["decision_uid"], env["run_uid"], env["valid_until"],
                          env["permission_line"], env["recovery_basis"])
    if verdict not in _VALID_VERDICTS:
        return False
    if not all(isinstance(x, str) and x for x in (du, ru, sd)):
        return False
    if not (isinstance(vu, str) and isinstance(pl, str)):
        return False
    if rb is not None and not _recovery_basis_wellformed(rb):
        return False
    try:
        rank, seq = int(env["restriction_rank"]), int(env["decision_seq"])
        av = env["authority_version"]
        av_t = (str(av[0]), int(av[1]), int(av[2]))
        datetime.fromisoformat(vu)
    except (KeyError, TypeError, ValueError, IndexError):
        return False
    return rank == _RANK[verdict] and seq >= 1 and av_t == (sd, seq, rank)


def admit_persisted(
    envelope: Any, *, current_session_date: str, now: Optional[datetime] = None,
) -> Optional[EffectivePermission]:
    """Fail-closed admission at the read boundary (R7): the admitted EP, else None
    (malformed per _valid_canonical / prior-session / missing-or-stale freshness).
    Never raises (tz-normalized compare), fabricates, or retains a grant."""
    if not _valid_canonical(envelope) or envelope["session_date"] != current_session_date:
        return None
    vu_dt = datetime.fromisoformat(envelope["valid_until"])
    if vu_dt.tzinfo is None:
        vu_dt = vu_dt.replace(tzinfo=timezone.utc)
    if now is not None:
        now_dt = now if now.tzinfo is not None else now.replace(tzinfo=timezone.utc)
        if now_dt > vu_dt:                          # stale/expired
            return None
    av = envelope["authority_version"]
    return _mint(verdict=envelope["verdict"], restriction_rank=int(envelope["restriction_rank"]),
                 decision_uid=envelope["decision_uid"], session_date=envelope["session_date"],
                 run_uid=envelope["run_uid"], authority_version=(str(av[0]), int(av[1]), int(av[2])),
                 valid_until=envelope["valid_until"], recovery_basis=envelope["recovery_basis"],
                 permission_line=envelope["permission_line"], decision_seq=int(envelope["decision_seq"]))


def _recovery_authorized(*, recovery_basis: Any, incoming_decision_uid: Any,
                         incoming_verdict: Any, incoming_seq: int, accepted_seq: int,
                         accepted_av: tuple[str, int, int]) -> bool:
    """Shared R3 recovery predicate (used by is_authorized_redecision AND the
    publication copy): a strictly higher decision_seq, an ADMITTED incoming daily
    decision (non-empty uid, non-UNAVAILABLE verdict), and a well-formed
    recovery_basis referencing the accepted authority whose superseding_decision_uid
    equals the incoming decision_uid."""
    return (incoming_seq > accepted_seq
            and isinstance(incoming_decision_uid, str) and incoming_decision_uid
            and incoming_verdict in _ADMITTED_VERDICTS
            and _recovery_basis_wellformed(recovery_basis)
            and recovery_basis["superseded_authority_version"] == list(accepted_av)
            and recovery_basis["superseding_decision_uid"] == incoming_decision_uid)


def is_authorized_redecision(*, incoming: EffectivePermission,
                             accepted: EffectivePermission) -> bool:
    """R3 predicate for a LOWER-rank admission (Q4 recovery)."""
    return _recovery_authorized(
        recovery_basis=incoming.recovery_basis, incoming_decision_uid=incoming.decision_uid,
        incoming_verdict=incoming.verdict, incoming_seq=incoming.decision_seq,
        accepted_seq=accepted.decision_seq, accepted_av=accepted.authority_version)


def _av(env: dict[str, Any]) -> tuple[str, int, int]:
    av = env["authority_version"]
    return (str(av[0]), int(av[1]), int(av[2]))


def _is_future_session(session_date: str) -> bool:
    """D2: a session_date later than the current authoritative (UTC) date -- or
    unparseable -- is a future/invalid bundle and is refused (no today+1 grace;
    ET is behind UTC, so a real ET session_date is never past UTC today)."""
    try:
        d = date.fromisoformat(session_date)
    except (ValueError, TypeError):
        return True
    return d > datetime.now(timezone.utc).date()


def publication_admits(accepted_envelope: Optional[dict[str, Any]],
                       incoming_envelope: Optional[dict[str, Any]]) -> bool:
    """R5 non-regression: compare authority_version lexicographically (never a
    timestamp, R6). The incoming must be a canonical envelope and not a future
    session (D2, fail-closed on both routes). Admit only when (a) not behind,
    (b) no equal-seq downgrade, (c) a lower rank across a higher decision_seq carries
    a validated recovery_basis (Q4, shared predicate), (d) equal version is a no-op
    ONLY when the FULL persisted envelope is byte/structurally identical (run_uid and
    every field, D1). Missing/malformed incoming -> refuse; a well-formed non-future
    incoming with no accepted (bootstrap) -> admit."""
    if not _valid_canonical(incoming_envelope):
        return False
    inc = _av(incoming_envelope)
    if _is_future_session(inc[0]):
        return False
    if not _valid_canonical(accepted_envelope):
        return not isinstance(accepted_envelope, dict)  # bootstrap admits; malformed accepted refuses
    acc = _av(accepted_envelope)
    (inc_d, inc_s, inc_r), (acc_d, acc_s, acc_r) = inc, acc
    if inc_d < acc_d:                              # (a) older session
        return False
    if inc_d == acc_d and inc_s < acc_s:           # (a) older decision
        return False
    if inc == acc:                                 # (d) equal-version: FULL identity no-op (D1)
        return incoming_envelope == accepted_envelope
    if inc_d == acc_d and inc_s == acc_s:          # (b) intra-decision downgrade refused
        return inc_r >= acc_r
    if inc_d == acc_d and inc_s > acc_s and inc_r < acc_r:   # (c) recovery-gated downgrade
        return _recovery_authorized(
            recovery_basis=incoming_envelope.get("recovery_basis"),
            incoming_decision_uid=incoming_envelope.get("decision_uid"),
            incoming_verdict=incoming_envelope.get("verdict"),
            incoming_seq=inc_s, accepted_seq=acc_s, accepted_av=acc)
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
