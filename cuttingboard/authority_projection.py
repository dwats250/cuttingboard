"""PRD-340 SLICE 2 (Authority Projection): the CLOSED authoritative-channel
registry + the per-channel read/output-boundary validator + the EP-derived
authoritative-action projection.

This module is the ONLY place the canonical projection field
(effective_permission.CANONICAL_FIELD) is read from a served/persisted carrier
for authoritative output (T4 routing), and the ONLY place the authoritative
decision-state vocabulary (TRADE PERMITTED / STAY FLAT / HALT / OBSERVE ONLY /
STATE UNAVAILABLE) is authored. It CONSUMES Slice-1's carrier/resolver/admission:
it never authors the canonical field (Slice-1 exclusive writer, persist) and never
constructs an EffectivePermission (Slice-1 guarded constructor). A channel derives
its authoritative action wording ONLY from an ActionProjection produced here --
either project(ep) for an in-process seam that holds a resolver-provenanced EP
(R1), or admit_projection(carrier, ...) for a cross-process seam reading a
persisted/served carrier through the fail-closed read boundary (R3c/fail-closed)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from cuttingboard import effective_permission as ep_authority
from cuttingboard.effective_permission import (
    CANONICAL_FIELD,
    EffectivePermission,
    VERDICT_HALT,
    VERDICT_NO_TRADE,
    VERDICT_OBSERVE_ONLY,
    VERDICT_PERMITTED,
    VERDICT_UNAVAILABLE,
)

# --- the authoritative decision-state vocabulary (authored ONLY here, R2/T2) ---
DECISION_TRADE_PERMITTED = "TRADE PERMITTED"
DECISION_STAY_FLAT = "STAY FLAT"
DECISION_HALT = "HALT"
DECISION_OBSERVE_ONLY = "OBSERVE ONLY"
DECISION_UNAVAILABLE = "STATE UNAVAILABLE"

# --- the cross-channel posture token (JS / CLI / served contract) ---
POSTURE_TRADE_READY = "TRADE_READY"
POSTURE_STAY_FLAT = "STAY_FLAT"
POSTURE_OBSERVE_ONLY = "OBSERVE_ONLY"
POSTURE_HALT = "HALT"
POSTURE_UNAVAILABLE = "UNAVAILABLE"

# --- the report-body structural outcome (render_report gating; NOT a proxy) ---
REPORT_TRADE = "TRADE"
REPORT_NO_TRADE = "NO_TRADE"
REPORT_HALT = "HALT"
REPORT_UNAVAILABLE = "UNAVAILABLE"

_UNAVAILABLE_LINE = "Authority unavailable. No new trades permitted."

# verdict -> (available, decision_state, posture, report_outcome, operator_locked)
_VERDICT_MAP: dict[str, tuple[bool, str, str, str, bool]] = {
    VERDICT_PERMITTED: (True, DECISION_TRADE_PERMITTED, POSTURE_TRADE_READY, REPORT_TRADE, False),
    VERDICT_NO_TRADE: (False, DECISION_STAY_FLAT, POSTURE_STAY_FLAT, REPORT_NO_TRADE, False),
    VERDICT_OBSERVE_ONLY: (False, DECISION_OBSERVE_ONLY, POSTURE_OBSERVE_ONLY, REPORT_NO_TRADE, True),
    VERDICT_HALT: (False, DECISION_HALT, POSTURE_HALT, REPORT_HALT, False),
    VERDICT_UNAVAILABLE: (False, DECISION_UNAVAILABLE, POSTURE_UNAVAILABLE, REPORT_UNAVAILABLE, False),
}


@dataclass(frozen=True)
class ActionProjection:
    """The ONE authoritative-action projection every channel emits from. Derived
    solely from a resolver-provenanced EffectivePermission (never a proxy)."""

    verdict: str
    available: bool
    permission_line: str
    decision_state: str
    posture: str
    report_outcome: str
    operator_locked: bool

    def to_served(self) -> dict[str, Any]:
        """The served/testable projection mirror (read-boundary output)."""
        return {
            "verdict": self.verdict, "available": self.available,
            "permission_line": self.permission_line, "decision_state": self.decision_state,
            "posture": self.posture, "report_outcome": self.report_outcome,
            "operator_locked": self.operator_locked,
        }


def project(ep: EffectivePermission) -> ActionProjection:
    """Derive the authoritative-action projection from a resolver-provenanced EP
    (R1, in-process seams). Any non-EP argument fails closed to UNAVAILABLE rather
    than trusting a look-alike (R3 in-process defence-in-depth)."""
    if not isinstance(ep, EffectivePermission):
        return _unavailable_projection()
    available, decision_state, posture, report_outcome, operator_locked = _VERDICT_MAP.get(
        ep.verdict, _VERDICT_MAP[VERDICT_UNAVAILABLE])
    line = ep.permission_line if ep.verdict != VERDICT_UNAVAILABLE else _UNAVAILABLE_LINE
    return ActionProjection(
        verdict=ep.verdict, available=available, permission_line=line,
        decision_state=decision_state, posture=posture,
        report_outcome=report_outcome, operator_locked=operator_locked)


def _unavailable_projection() -> ActionProjection:
    available, decision_state, posture, report_outcome, operator_locked = _VERDICT_MAP[VERDICT_UNAVAILABLE]
    return ActionProjection(
        verdict=VERDICT_UNAVAILABLE, available=available, permission_line=_UNAVAILABLE_LINE,
        decision_state=decision_state, posture=posture,
        report_outcome=report_outcome, operator_locked=operator_locked)


def admit_projection(
    carrier: Any, *, current_session_date: str, now: Optional[datetime] = None,
) -> ActionProjection:
    """The per-channel cross-process READ/OUTPUT boundary (R3c, fail-closed). The
    SOLE reader of the canonical projection field on a served/persisted carrier
    (T4 routing). Routes the field through Slice-1's admit_persisted; an absent,
    malformed, prior-session, or stale carrier yields the UNAVAILABLE projection --
    never a proxy claim, never a retained grant, never a raise."""
    envelope = carrier.get(CANONICAL_FIELD) if isinstance(carrier, dict) else None
    ep = ep_authority.admit_persisted(
        envelope, current_session_date=current_session_date, now=now)
    if ep is None:
        return _unavailable_projection()
    return project(ep)


def admit_ep(
    carrier: Any, *, current_session_date: str, now: Optional[datetime] = None,
) -> EffectivePermission:
    """The cross-process read boundary that yields an EffectivePermission for a
    seam which must feed a downstream EP-required interface (e.g.
    render_report_from_payload -> render_report). SOLE reader of the canonical
    field alongside admit_projection (T4 routing). Fail-closed: absent/malformed/
    prior-session/stale -> the resolver's UNAVAILABLE sentinel, never None, never a
    proxy, never a raise."""
    envelope = carrier.get(CANONICAL_FIELD) if isinstance(carrier, dict) else None
    ep = ep_authority.admit_persisted(
        envelope, current_session_date=current_session_date, now=now)
    return ep if ep is not None else ep_authority.unavailable(current_session_date)


def assert_in_process_ep(ep: Any) -> EffectivePermission:
    """R1 gate for an in-process WRITE seam (deliver_json/deliver_html) that emits
    the carried payload rather than re-deriving wording: render-before-resolve is a
    type/argument error because a genuine resolver-provenanced EP is required."""
    if not isinstance(ep, EffectivePermission):
        raise TypeError(
            "authoritative channel requires a resolved EffectivePermission (R1); "
            f"got {type(ep).__name__}")
    return ep


# ---------------------------------------------------------------------------
# R2 -- the CLOSED authoritative-channel registry.
# Each channel names the seam that emits its authoritative wording. The Python
# emitters are exactly the functions that reference this module's projection API
# (project / admit_projection / assert_in_process_ep); T2 discovers that set
# INDEPENDENTLY by AST and asserts equality (never self-enumeration).
# ---------------------------------------------------------------------------

# Python in-process seams that REQUIRE an explicit EP parameter (R1, T1).
IN_PROCESS_EMITTERS: frozenset[tuple[str, str]] = frozenset({
    ("cuttingboard.output", "render_report"),
    ("cuttingboard.output", "build_notification_message"),
    ("cuttingboard.delivery.transport", "deliver_html"),
    ("cuttingboard.delivery.transport", "deliver_json"),
    ("cuttingboard.delivery.transport", "deliver_cli"),
})

# Python cross-process seams that route a served/persisted carrier through
# admit_projection (R3c). They do NOT take a new required EP parameter.
CROSS_PROCESS_EMITTERS: frozenset[tuple[str, str]] = frozenset({
    ("cuttingboard.output", "render_report_from_payload"),
    ("cuttingboard.delivery.dashboard_renderer", "render_dashboard_html"),
})

# The full closed set of Python authoritative emitters (in-process + cross-process).
PYTHON_EMITTERS: frozenset[tuple[str, str]] = IN_PROCESS_EMITTERS | CROSS_PROCESS_EMITTERS

# Non-Python channels (discovered by their own seam scans in T2).
JS_EMITTER = ("ui/app.js", "derivePosture")
SHELL_PUBLISH_SEAM = ("tools/ci_push_artifacts.sh", "authority_guard")
WORKFLOW_COMMIT_SEAM = (".github/workflows/cuttingboard.yml", "Generate commit message")

# The eight authoritative channels (R2), for documentation + closed-set assertions.
CHANNELS: tuple[str, ...] = (
    "publish",                 # (1) tools/ci_push_artifacts.sh
    "telegram",                # (2) output.build_notification_message
    "markdown_report",         # (3) output.render_report -> runtime._write_markdown_report
    "html",                    # (4) transport.deliver_html -> html_renderer.render_html
    "json_payload",            # (5) transport.deliver_json
    "cli",                     # (6) transport.deliver_cli
    "served_contract",         # (7) ui/contract.json -> ui/app.js / render_dashboard_html
    "daily_workflow_commit",   # (8) cuttingboard.yml commit-message step
)


# ---------------------------------------------------------------------------
# CLI: cross-process read-boundary for the shell publish channel + the workflow
# commit-message channel. Reads a persisted carrier file and projects it through
# the fail-closed boundary so those non-Python seams route through this module.
# ---------------------------------------------------------------------------

def _read_carrier(path: str) -> Any:
    import json
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _cli(argv: list[str]) -> int:
    if len(argv) == 2 and argv[0] == "admit":
        # Publish read boundary: exit 0 iff the carrier admits a non-UNAVAILABLE
        # authority for its own session_date; else fail-closed (exit 1).
        carrier = _read_carrier(argv[1])
        env = carrier.get(CANONICAL_FIELD) if isinstance(carrier, dict) else None
        sd = env.get("session_date") if isinstance(env, dict) else None
        proj = admit_projection(carrier, current_session_date=str(sd))
        return 0 if proj.verdict != VERDICT_UNAVAILABLE else 1
    if len(argv) == 2 and argv[0] == "commit-status":
        # Daily workflow commit-message wording, derived ONLY from the projection.
        carrier = _read_carrier(argv[1])
        env = carrier.get(CANONICAL_FIELD) if isinstance(carrier, dict) else None
        sd = env.get("session_date") if isinstance(env, dict) else None
        proj = admit_projection(carrier, current_session_date=str(sd))
        print(proj.decision_state)
        return 0
    print("usage: authority_projection.py (admit|commit-status) <carrier.json>")
    return 2


if __name__ == "__main__":  # pragma: no cover
    import sys
    raise SystemExit(_cli(sys.argv[1:]))
