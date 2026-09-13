"""PRD-340 Slice 2 -- T2: the authoritative-channel registry is CLOSED.

The registry (cuttingboard.authority_projection) is proved closed by comparing it
to an INDEPENDENTLY DISCOVERED set of authoritative writers -- never enumerated
against itself (circular; cannot detect an out-of-registry writer). Discovery
covers every output-seam CLASS: Python (AST over cuttingboard/), JS (ui/app.js),
shell (ci_push_artifacts.sh), workflow (.github/workflows). A member of the
independent set absent from the registry -- or vice versa -- FAILS.

M2 is observable here: a synthetic authoritative writer added to a channel module
(referencing the projection API, or emitting the raw TRADE PERMITTED grant) is
DISCOVERED by the scan but not registered -> RED. It is DISCOVERED, not fixtured.
"""

from __future__ import annotations

import ast
import pathlib

from cuttingboard import authority_projection as ap

REPO = pathlib.Path(__file__).resolve().parents[1]
PKG = REPO / "cuttingboard"

_API_NAMES = frozenset({"project", "admit_projection", "admit_ep", "assert_in_process_ep"})
# Orchestration/plumbing + the module itself are NOT output channels: the resolver
# side (runtime threads/persists the EP), Slice-1 core, and the projection module.
_EXCLUDED = {
    PKG / "runtime" / "__init__.py",
    PKG / "effective_permission.py",
    PKG / "authority_projection.py",
}


def _module_dotted(path: pathlib.Path) -> str:
    rel = path.relative_to(REPO).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _references_api(fn: ast.FunctionDef) -> bool:
    for node in ast.walk(fn):
        if (isinstance(node, ast.Attribute) and node.attr in _API_NAMES
                and isinstance(node.value, ast.Name) and node.value.id == "authority_projection"):
            return True
    return False


def _discover_python_emitters() -> set[tuple[str, str]]:
    """INDEPENDENT discovery (a): every function in a channel module that consumes
    the projection API is an authoritative Python emitter."""
    found: set[tuple[str, str]] = set()
    for path in sorted(PKG.rglob("*.py")):
        if path in _EXCLUDED or "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        mod = _module_dotted(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and _references_api(node):
                found.add((mod, node.name))
    return found


def _raw_grant_emitters() -> set[tuple[str, str]]:
    """INDEPENDENT discovery (a, defense-in-depth): any function OUTSIDE
    authority_projection.py that emits the raw authoritative grant literal
    'TRADE PERMITTED' as a string constant is an (illicit) authoritative emitter."""
    grant = ap.DECISION_TRADE_PERMITTED
    found: set[tuple[str, str]] = set()
    for path in sorted(PKG.rglob("*.py")):
        if path == PKG / "authority_projection.py" or "__pycache__" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        mod = _module_dotted(path)
        for fn in ast.walk(tree):
            if not isinstance(fn, ast.FunctionDef):
                continue
            for node in ast.walk(fn):
                if isinstance(node, ast.Constant) and node.value == grant:
                    found.add((mod, fn.name))
    return found


def test_python_channel_registry_equals_independent_discovery() -> None:
    discovered = _discover_python_emitters()
    registered = set(ap.PYTHON_EMITTERS)
    assert discovered == registered, (
        "PRD-340 R2: the Python authoritative-channel registry is not closed.\n"
        f"  discovered but NOT registered (out-of-registry writer): {sorted(discovered - registered)}\n"
        f"  registered but NOT discovered (stale registry): {sorted(registered - discovered)}"
    )


def test_no_raw_authoritative_grant_outside_the_projection_module() -> None:
    # The only sanctioned author of the TRADE PERMITTED grant is the projection
    # module; any other emitter must go through the registered projection API.
    stray = _raw_grant_emitters()
    assert stray == set(), (
        f"PRD-340 R2/R4: raw 'TRADE PERMITTED' grant emitted outside the projection "
        f"module (unregistered authoritative writer): {sorted(stray)}")


def test_js_served_contract_channel_discovered_and_registered() -> None:
    src = (REPO / "ui" / "app.js").read_text(encoding="utf-8")
    # (b) JS discovery: derivePosture is the posture-deriving seam and it routes
    # through the validated accessor admitAuthority (not the raw contract fields).
    assert "function derivePosture(" in src
    assert "admitAuthority(" in src
    fn = src.split("function derivePosture(", 1)[1].split("\nfunction ", 1)[0]
    assert "admitAuthority(" in fn, "derivePosture must route through the validated accessor"
    assert ap.JS_EMITTER == ("ui/app.js", "derivePosture")


def test_shell_publish_channel_discovered_and_registered() -> None:
    src = (REPO / "tools" / "ci_push_artifacts.sh").read_text(encoding="utf-8")
    # (c) shell discovery: the publish authority guard routes through the validator.
    assert "authority_guard()" in src
    assert "authority_projection.py" in src and "admit" in src
    assert ap.SHELL_PUBLISH_SEAM == ("tools/ci_push_artifacts.sh", "authority_guard")


def test_workflow_commit_channel_discovered_and_hourly_correctly_absent() -> None:
    daily = (REPO / ".github" / "workflows" / "cuttingboard.yml").read_text(encoding="utf-8")
    hourly = (REPO / ".github" / "workflows" / "hourly_alert.yml").read_text(encoding="utf-8")
    # (d) workflow discovery: the daily commit-message step derives its authoritative
    # wording from the projection CLI; the hourly commit is the STATIC timestamp form
    # and is correctly NOT an authoritative commit-message channel.
    assert "authority_projection" in daily and "commit-status" in daily
    assert ap.WORKFLOW_COMMIT_SEAM[0] == ".github/workflows/cuttingboard.yml"
    assert "commit-status" not in hourly and "authority_projection" not in hourly
