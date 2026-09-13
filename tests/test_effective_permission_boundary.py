"""PRD-339 Slice 1 (R4, packet s14): the EXCLUSIVE-WRITER structural guard. Only
persist/persist_copy in cuttingboard/effective_permission.py may AUTHOR the canonical
field; any other authorship (subscript/dict/update/setdefault/__setitem__, at
function/module/class scope) makes this RED (M4/D5). Seams must route through
persist/persist_copy; ui/contract.json is a verbatim workflow cp."""

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


def _approved_authoring_ids(tree: ast.AST) -> set[int]:
    """Node ids of authoring sites that live INSIDE an approved function body."""
    return {id(sub) for fn in ast.walk(tree)
            if isinstance(fn, ast.FunctionDef) and fn.name in APPROVED_FUNCS
            for sub in ast.walk(fn) if _is_authoring(sub)}


def test_no_module_authors_the_field_outside_the_approved_functions() -> None:
    offenders: list[str] = []
    for path in sorted(PKG.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if path == APPROVED_PATH:
            # authoring allowed ONLY inside persist/persist_copy; node-identity diff
            # catches module-scope and class-scope authorship too (D5).
            approved = _approved_authoring_ids(tree)
            stray = [n.lineno for n in ast.walk(tree)
                     if _is_authoring(n) and id(n) not in approved]
            assert not stray, (
                f"effective_permission.py authors the field outside {APPROVED_FUNCS} "
                f"(module/class/other scope) at lines {stray}")
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


# --------------------------------------------------------------------------- #
# PRD-340 Slice 2 -- T3 (R3 in-process): the guarded CONSTRUCTOR boundary.      #
# EffectivePermission is minted ONLY by the resolver module; no other module    #
# constructs it (or the private _mint capability). A second constructor (M3)    #
# makes this RED. (A dict/dataclass look-alike is rejected by                   #
# authority_projection.project -- see test_authority_projection.py.)            #
# --------------------------------------------------------------------------- #

_CONSTRUCT_ATTRS = {"EffectivePermission", "_mint"}


def _ctor_local_names(tree: ast.AST) -> set[str]:
    """Local names bound (possibly via alias) to the EP class or its private mint,
    so an aliased import (``EffectivePermission as _EP``) cannot evade detection."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and \
                node.module.endswith("effective_permission"):
            for a in node.names:
                if a.name in _CONSTRUCT_ATTRS:
                    names.add(a.asname or a.name)
    return names


def _ep_constructions(tree: ast.AST) -> list[int]:
    local = _ctor_local_names(tree)
    hits: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        if isinstance(f, ast.Name) and f.id in local:
            hits.append(node.lineno)               # aliased/direct name construction
        elif isinstance(f, ast.Attribute) and f.attr in _CONSTRUCT_ATTRS:
            hits.append(node.lineno)               # module-qualified construction
    return hits


def test_effective_permission_constructed_only_in_the_resolver_module() -> None:
    offenders: list[str] = []
    for path in sorted(PKG.rglob("*.py")):
        if path == APPROVED_PATH or "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for ln in _ep_constructions(tree):
            offenders.append(f"{path.relative_to(REPO)}:{ln}")
    assert not offenders, (
        "PRD-340 R3 (guarded constructor): EffectivePermission is minted outside "
        f"effective_permission.py: {offenders}")


def test_resolver_module_does_construct_the_ep() -> None:
    # Positive control: the resolver module DOES mint (else the boundary is vacuous).
    tree = ast.parse(APPROVED_PATH.read_text(encoding="utf-8"))
    # inside its own module _mint / EffectivePermission are local defs, not imports.
    assert any(
        isinstance(n, ast.Call) and (
            (isinstance(n.func, ast.Name) and n.func.id in _CONSTRUCT_ATTRS)
            or (isinstance(n.func, ast.Attribute) and n.func.attr in _CONSTRUCT_ATTRS))
        for n in ast.walk(tree))
