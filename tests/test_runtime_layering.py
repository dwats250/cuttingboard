"""PRD-173 (R1): the runtime package's L0 leaf modules must not import from
the runtime package itself.

The PRD-170 sublayer model requires a one-directional import graph
(_constants / _types are leaves). This guard enforces that the leaf modules
never reach up into cuttingboard.runtime (the package facade) — the import
cycle that would otherwise break the split. It extends to new leaf modules as
later extraction PRDs add them.
"""

from __future__ import annotations

import ast
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
LEAF_MODULES = ["_constants", "_types"]


def test_l0_leaves_do_not_import_the_runtime_package() -> None:
    for mod in LEAF_MODULES:
        path = REPO / "cuttingboard" / "runtime" / f"{mod}.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert not module.startswith("cuttingboard.runtime"), (
                    f"{mod}.py imports from {module!r} — an L0 leaf must not "
                    f"depend on the runtime package"
                )
                assert node.level == 0, (
                    f"{mod}.py uses a relative import (level={node.level}) — an "
                    f"L0 leaf must not import from within the package"
                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("cuttingboard.runtime"), (
                        f"{mod}.py imports {alias.name!r} — L0 leaf must not "
                        f"depend on the runtime package"
                    )
