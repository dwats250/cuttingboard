"""PRD-339 Slice 1 (R4, packet s14): the EXCLUSIVE-WRITER structural guard. Only
cuttingboard/effective_permission.py may AUTHOR the canonical ``effective_permission``
field (subscript assign or dict-literal key); a synthetic second writer in any other
cuttingboard module makes this RED (M4). Modeled on test_runtime_layering /
test_dash_boundary. The ui/contract.json workflow step must be a verbatim copy."""

from __future__ import annotations

import ast
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
PKG = REPO / "cuttingboard"
FIELD = "effective_permission"
APPROVED = "effective_permission.py"  # the sole authoring module (basename)


def _is_field_ref(node: ast.AST) -> bool:
    """True for an expression that names the canonical field: the literal
    "effective_permission", the CANONICAL_FIELD name, or ``<mod>.CANONICAL_FIELD``."""
    return (
        (isinstance(node, ast.Constant) and node.value == FIELD)
        or (isinstance(node, ast.Name) and node.id == "CANONICAL_FIELD")
        or (isinstance(node, ast.Attribute) and node.attr == "CANONICAL_FIELD")
    )


def _authoring_sites(tree: ast.AST) -> list[int]:
    """Line numbers where the FIELD is AUTHORED: a subscript-assignment target
    ``x[FIELD] = ...`` (plain/aug/annotated) or a dict literal key ``{FIELD: ...}``.
    Catches both the string literal and the CANONICAL_FIELD constant so a second
    writer cannot evade the guard by importing the constant."""
    hits: list[int] = []
    for node in ast.walk(tree):
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
        elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            targets = [node.target]
        for tgt in targets:
            if isinstance(tgt, ast.Subscript) and _is_field_ref(tgt.slice):
                hits.append(node.lineno)
        if isinstance(node, ast.Dict):
            if any(k is not None and _is_field_ref(k) for k in node.keys):
                hits.append(node.lineno)
    return hits


def test_only_the_approved_module_authors_the_canonical_field() -> None:
    offenders: list[str] = []
    for path in sorted(PKG.rglob("*.py")):
        if path.name == APPROVED:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for lineno in _authoring_sites(tree):
            offenders.append(f"{path.relative_to(REPO)}:{lineno}")
    assert not offenders, (
        "PRD-339 R4: the canonical effective_permission field must be authored ONLY "
        f"by cuttingboard/effective_permission.py; a second writer was found: {offenders}"
    )


def test_approved_module_does_author_the_field() -> None:
    # Sanity: the guard is meaningful only because the approved module DOES author it.
    tree = ast.parse((PKG / APPROVED).read_text(encoding="utf-8"))
    assert _authoring_sites(tree), "the approved persistence module must author the field"


def test_ui_contract_json_is_a_verbatim_copy_not_a_rewrite() -> None:
    # The ui/contract.json carrier is produced by a byte `cp` of latest_contract.json;
    # the workflow must not synthesize/rewrite the canonical field (packet s14).
    for wf in ("cuttingboard.yml", "hourly_alert.yml"):
        text = (REPO / ".github" / "workflows" / wf).read_text(encoding="utf-8")
        assert "ui/contract.json" in text
        assert FIELD not in text, (
            f"{wf} must not author/rewrite the canonical {FIELD} field; ui/contract.json "
            "is a verbatim cp of the resolver-written contract"
        )
