"""PRD-340 Slice 2 -- T1 (R1+R4) and T4 (R3 cross-process + fail-closed).

T1: every REGISTERED in-process channel function REQUIRES an EffectivePermission
    parameter (render-before-resolve is an argument error), every registered
    emitter CONSUMES the projection API, and the in-process emitters read no
    decision-bearing proxy for authoritative output.
T4: the read boundary fail-closes to UNAVAILABLE on absent/malformed/prior-session/
    stale/alternate-field carriers; the projection is derived only from the resolved
    verdict; and ROUTING -- the canonical projection field is read ONLY inside the
    approved validator (any direct raw read by a registered reader -> RED; M6).
"""

from __future__ import annotations

import ast
import pathlib
from datetime import datetime, timezone

import pytest

from cuttingboard import authority_projection as ap
from cuttingboard import effective_permission as ep_authority
from cuttingboard.effective_permission import (
    VERDICT_HALT, VERDICT_NO_TRADE, VERDICT_OBSERVE_ONLY, VERDICT_PERMITTED,
    VERDICT_UNAVAILABLE,
)

REPO = pathlib.Path(__file__).resolve().parents[1]
PKG = REPO / "cuttingboard"

# The Python channel modules whose registered readers must route through the
# approved validator (T4 iii). The projection module + Slice-1 core are the only
# sanctioned readers/writers of the canonical field.
_CHANNEL_READER_MODULES = [
    PKG / "output.py",
    PKG / "delivery" / "transport.py",
    PKG / "delivery" / "dashboard_renderer.py",
    PKG / "delivery" / "html_renderer.py",
    PKG / "delivery" / "payload.py",
    PKG / "market_map.py",
    PKG / "market_control_card.py",
]

# Proxy-authority markers R4 removed from the in-process emitters; a re-introduction
# (M1/M4) is an authoritative proxy read -> RED. (tradable/top_trades evidence reads
# are covered by the fidelity goldens, not this lexical guard.)
_FORBIDDEN_PROXY = frozenset({
    "_regime_to_permission_verb", "_regime_to_permission_key",
    "IF_NOW_TAKE", "OPERATOR_LOCK_PERMISSION",
})

_MODULE_PATHS = {
    "cuttingboard.output": PKG / "output.py",
    "cuttingboard.delivery.transport": PKG / "delivery" / "transport.py",
    "cuttingboard.delivery.dashboard_renderer": PKG / "delivery" / "dashboard_renderer.py",
}


def _load_fn(module: str, name: str) -> ast.FunctionDef:
    tree = ast.parse(_MODULE_PATHS[module].read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{module}.{name} not found")


def _has_required_ep_param(fn: ast.FunctionDef) -> bool:
    # positional (no default) OR keyword-only (no default) named effective_permission.
    pos = fn.args.posonlyargs + fn.args.args
    ndef = len(fn.args.defaults)
    required_pos = pos[: len(pos) - ndef] if ndef else pos
    if any(a.arg == "effective_permission" for a in required_pos):
        return True
    for arg, default in zip(fn.args.kwonlyargs, fn.args.kw_defaults):
        if arg.arg == "effective_permission" and default is None:
            return True
    return False


def _references_api(fn: ast.FunctionDef) -> bool:
    return any(
        isinstance(n, ast.Attribute) and n.attr in
        {"project", "admit_projection", "admit_ep", "assert_in_process_ep"}
        and isinstance(n.value, ast.Name) and n.value.id == "authority_projection"
        for n in ast.walk(fn))


# --------------------------------------------------------------------------- T1

def test_in_process_emitters_require_effective_permission_param() -> None:
    for module, name in sorted(ap.IN_PROCESS_EMITTERS):
        fn = _load_fn(module, name)
        assert _has_required_ep_param(fn), (
            f"PRD-340 R1: {module}.{name} must REQUIRE an effective_permission "
            f"parameter (no default) so render-before-resolve is an argument error")


def test_every_registered_emitter_consumes_the_projection_api() -> None:
    for module, name in sorted(ap.PYTHON_EMITTERS):
        # only the three modules we parse here host emitters; all 7 live in them.
        assert module in _MODULE_PATHS, f"unexpected emitter module {module}"
        fn = _load_fn(module, name)
        assert _references_api(fn), (
            f"PRD-340 R1/R4: {module}.{name} must derive authority from the "
            f"authority_projection API, not a proxy")


def test_in_process_emitters_read_no_proxy_authority() -> None:
    for module, name in sorted(ap.IN_PROCESS_EMITTERS):
        fn = _load_fn(module, name)
        offenders = []
        for node in ast.walk(fn):
            if isinstance(node, ast.Name) and node.id in _FORBIDDEN_PROXY:
                offenders.append(node.id)
            if isinstance(node, ast.Attribute) and node.attr in _FORBIDDEN_PROXY:
                offenders.append(node.attr)
        assert not offenders, (
            f"PRD-340 R4: {module}.{name} reads a decision-bearing proxy for "
            f"authoritative output: {sorted(set(offenders))}")


# --------------------------------------------------------------------------- T4

def _ep(*, mode="live", trade=False, halted=False, locked=False, session="2026-06-12"):
    return ep_authority.resolve_effective_permission(
        mode=mode, outcome_is_trade=trade, system_halted=halted, operator_locked=locked,
        session_date=session, run_uid="a" * 32,
        posture_permission_line="Longs allowed." if trade else "No new trades permitted.",
        operator_lock_line="No new trades permitted — operator cannot monitor.")


@pytest.mark.parametrize("verdict,available,decision,posture,report,locked", [
    (VERDICT_PERMITTED, True, ap.DECISION_TRADE_PERMITTED, ap.POSTURE_TRADE_READY, ap.REPORT_TRADE, False),
    (VERDICT_NO_TRADE, False, ap.DECISION_STAY_FLAT, ap.POSTURE_STAY_FLAT, ap.REPORT_NO_TRADE, False),
    (VERDICT_OBSERVE_ONLY, False, ap.DECISION_OBSERVE_ONLY, ap.POSTURE_OBSERVE_ONLY, ap.REPORT_NO_TRADE, True),
    (VERDICT_HALT, False, ap.DECISION_HALT, ap.POSTURE_HALT, ap.REPORT_HALT, False),
    (VERDICT_UNAVAILABLE, False, ap.DECISION_UNAVAILABLE, ap.POSTURE_UNAVAILABLE, ap.REPORT_UNAVAILABLE, False),
])
def test_project_maps_each_verdict(verdict, available, decision, posture, report, locked) -> None:
    ep = {
        VERDICT_PERMITTED: _ep(trade=True),
        VERDICT_NO_TRADE: _ep(trade=False),
        VERDICT_OBSERVE_ONLY: _ep(locked=True),
        VERDICT_HALT: _ep(halted=True),
        VERDICT_UNAVAILABLE: ep_authority.unavailable("2026-06-12"),
    }[verdict]
    proj = ap.project(ep)
    assert (proj.verdict, proj.available, proj.decision_state, proj.posture,
            proj.report_outcome, proj.operator_locked) == (
        verdict, available, decision, posture, report, locked)


def test_project_rejects_non_ep_lookalike() -> None:
    # R3 in-process defence: a dict/dataclass look-alike is not trusted.
    proj = ap.project({"verdict": VERDICT_PERMITTED, "permission_line": "Longs allowed."})
    assert proj.verdict == VERDICT_UNAVAILABLE and proj.available is False


def _carrier(ep) -> dict:
    return {"effective_permission": ep.to_envelope(), "system_state": {"tradable": True}}


def test_admit_projection_admits_a_valid_carrier() -> None:
    proj = ap.admit_projection(_carrier(_ep(trade=True)), current_session_date="2026-06-12")
    assert proj.verdict == VERDICT_PERMITTED and proj.available is True


@pytest.mark.parametrize("carrier,session,now", [
    ({}, "2026-06-12", None),                                              # absent field
    ({"effective_permission": {"verdict": "PERMITTED"}}, "2026-06-12", None),  # malformed
    ({"system_state": {"tradable": True}}, "2026-06-12", None),            # alternate/proxy field only
])
def test_admit_projection_fail_closed_absent_or_malformed(carrier, session, now) -> None:
    proj = ap.admit_projection(carrier, current_session_date=session, now=now)
    assert proj.verdict == VERDICT_UNAVAILABLE and proj.available is False


def test_admit_projection_fail_closed_prior_session() -> None:
    proj = ap.admit_projection(_carrier(_ep(trade=True, session="2026-06-12")),
                               current_session_date="2026-06-13")
    assert proj.verdict == VERDICT_UNAVAILABLE


def test_admit_projection_fail_closed_stale() -> None:
    carrier = _carrier(_ep(trade=True, session="2026-06-12"))  # valid_until 2026-06-13T08:00Z
    stale_now = datetime(2026, 6, 14, 12, 0, tzinfo=timezone.utc)
    proj = ap.admit_projection(carrier, current_session_date="2026-06-12", now=stale_now)
    assert proj.verdict == VERDICT_UNAVAILABLE


def test_admit_ep_fail_closed_returns_unavailable_sentinel() -> None:
    ep = ap.admit_ep({}, current_session_date="2026-06-12")
    assert ep.verdict == VERDICT_UNAVAILABLE
    assert ap.project(ep).decision_state == ap.DECISION_UNAVAILABLE


# ---------------------------------------------------- T4 (iii) ROUTING (M6)

def _reads_canonical_field(tree: ast.AST) -> list[int]:
    """Direct reads of the canonical projection field key: a subscript/.get()/
    attribute keyed on 'effective_permission' or the CANONICAL_FIELD name."""
    field = ep_authority.CANONICAL_FIELD
    hits: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                and node.slice.value == field:
            hits.append(node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "get" and node.args \
                and isinstance(node.args[0], ast.Constant) and node.args[0].value == field:
            hits.append(node.lineno)
        if isinstance(node, ast.Attribute) and node.attr == "CANONICAL_FIELD":
            hits.append(node.lineno)
        if isinstance(node, ast.Name) and node.id == "CANONICAL_FIELD":
            hits.append(node.lineno)
    return hits


def test_routing_canonical_field_read_only_inside_the_validator() -> None:
    offenders: list[str] = []
    for path in _CHANNEL_READER_MODULES:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for ln in _reads_canonical_field(tree):
            offenders.append(f"{path.relative_to(REPO)}:{ln}")
    assert not offenders, (
        "PRD-340 T4(iii): a registered channel reader accesses the canonical "
        f"projection field RAW, bypassing authority_projection (M6): {offenders}")


def test_routing_projection_module_is_the_reader() -> None:
    # Positive control: the validator DOES read the field (else the routing test is vacuous).
    tree = ast.parse((PKG / "authority_projection.py").read_text(encoding="utf-8"))
    assert _reads_canonical_field(tree), "authority_projection must read the canonical field"


def test_js_routing_derivePosture_reads_only_the_validated_accessor() -> None:
    src = (REPO / "ui" / "app.js").read_text(encoding="utf-8")
    # The raw served field is read ONLY inside admitAuthority; derivePosture and the
    # signal-bar renderer must route through admitAuthority, never the raw field.
    assert src.count("'effective_permission'") == 1, (
        "the served authority field must be read exactly once (inside admitAuthority)")
    admit_fn = src.split("function admitAuthority(", 1)[1].split("\nfunction ", 1)[0]
    assert "'effective_permission'" in admit_fn, "the sole read must be inside admitAuthority"
    derive_fn = src.split("function derivePosture(", 1)[1].split("\nfunction ", 1)[0]
    assert "'effective_permission'" not in derive_fn and "admitAuthority(" in derive_fn
