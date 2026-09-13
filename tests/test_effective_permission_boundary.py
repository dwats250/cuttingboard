"""PRD-339 Slice 1 (R4, packet s14): the EXCLUSIVE-WRITER structural guard. The
canonical ``effective_permission`` field may be AUTHORED only by the two approved
functions in cuttingboard/effective_permission.py (persist / persist_copy). Any
other module that authors it -- by subscript-assign, dict literal, ``.update({...})``,
``.setdefault(...)`` or ``.__setitem__(...)`` -- makes this RED (mutation proof M4).
The carrier seams must route through persist/persist_copy, and ui/contract.json is a
verbatim workflow cp. Modeled on test_runtime_layering / test_dash_boundary (AST)."""

from __future__ import annotations

import ast
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
PKG = REPO / "cuttingboard"
FIELD = "effective_permission"
APPROVED_PATH = PKG / "effective_permission.py"          # the ONE exact approved path
APPROVED_FUNCS = {"persist", "persist_copy"}             # the ONLY approved authoring functions


def _field_ref(node: ast.AST | None) -> bool:
    return (
        (isinstance(node, ast.Constant) and node.value == FIELD)
        or (isinstance(node, ast.Name) and node.id == "CANONICAL_FIELD")
        or (isinstance(node, ast.Attribute) and node.attr == "CANONICAL_FIELD")
    )


def _is_authoring(node: ast.AST) -> bool:
    """True if this node AUTHORS the canonical field (any mutation form)."""
    targets: list[ast.expr] = []
    if isinstance(node, ast.Assign):
        targets = list(node.targets)
    elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
        targets = [node.target]
    if any(isinstance(t, ast.Subscript) and _field_ref(t.slice) for t in targets):
        return True
    if isinstance(node, ast.Dict) and any(k is not None and _field_ref(k) for k in node.keys):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        m = node.func.attr
        if m == "update" and any(
                isinstance(a, ast.Dict) and any(k is not None and _field_ref(k) for k in a.keys)
                for a in node.args):
            return True
        if m in {"setdefault", "__setitem__"} and node.args and _field_ref(node.args[0]):
            return True
    return False


def _authoring_lines(tree: ast.AST) -> list[int]:
    return [n.lineno for n in ast.walk(tree) if _is_authoring(n)]


def test_no_module_authors_the_field_outside_the_approved_functions() -> None:
    offenders: list[str] = []
    for path in sorted(PKG.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if path == APPROVED_PATH:
            # Inside the approved module, authoring is allowed ONLY within persist/persist_copy.
            fns = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                   for sub in ast.walk(n) if _is_authoring(sub)}
            stray = fns - APPROVED_FUNCS
            assert not stray, f"effective_permission.py authors the field outside {APPROVED_FUNCS}: {stray}"
            continue
        for lineno in _authoring_lines(tree):
            offenders.append(f"{path.relative_to(REPO)}:{lineno}")
    assert not offenders, (
        f"PRD-339 R4: only effective_permission.py persist/persist_copy may author "
        f"the canonical field; second writer(s): {offenders}"
    )


def test_approved_functions_do_author_the_field() -> None:
    tree = ast.parse(APPROVED_PATH.read_text(encoding="utf-8"))
    authoring_funcs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                       for sub in ast.walk(n) if _is_authoring(sub)}
    assert authoring_funcs == APPROVED_FUNCS, (
        f"persist/persist_copy must be the authoring functions; found {authoring_funcs}")


def test_carrier_seams_route_through_persist() -> None:
    src = (PKG / "runtime" / "__init__.py").read_text(encoding="utf-8")
    for call in (
        "ep_authority.persist(contract, effective_permission)",   # daily contract
        "ep_authority.persist(summary, effective_permission)",    # daily summary
        "ep_authority.persist(contract, _hourly_ep)",             # hourly contract
        "ep_authority.persist(summary, _hourly_ep)",              # hourly summary
        "ep_authority.persist_copy(payload, contract)",           # payload (daily + hourly)
    ):
        assert call in src, f"carrier seam does not route through the approved writer: {call!r}"


def test_ui_contract_json_is_a_verbatim_copy_not_a_rewrite() -> None:
    for wf in ("cuttingboard.yml", "hourly_alert.yml"):
        text = (REPO / ".github" / "workflows" / wf).read_text(encoding="utf-8")
        assert "ui/contract.json" in text
        assert FIELD not in text, f"{wf} must not author/rewrite the canonical field"
