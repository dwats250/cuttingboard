"""PRD-173 (R2): the cuttingboard.runtime package facade must keep every
name importable that any module relied on before the package split.

After converting runtime.py into the runtime/ package, the __init__ facade
re-exports the constants and dataclasses moved to the L0 leaf modules. This
guard fails loudly if any name reachable via `from cuttingboard.runtime
import X` — or the setattr-style attribute-patch surface — stops resolving.
"""

from __future__ import annotations

import ast
import pathlib

import cuttingboard.runtime as rt

REPO = pathlib.Path(__file__).resolve().parents[1]


def _runtime_from_import_names() -> set[str]:
    names: set[str] = set()
    for base in ("cuttingboard", "tests"):
        for f in (REPO / base).rglob("*.py"):
            try:
                tree = ast.parse(f.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "cuttingboard.runtime":
                    for alias in node.names:
                        if alias.name != "*":
                            names.add(alias.name)
    return names


def test_every_from_import_name_is_present() -> None:
    names = _runtime_from_import_names()
    assert names, "scan found no `from cuttingboard.runtime import` sites — scanner broken"
    missing = sorted(n for n in names if not hasattr(rt, n))
    assert not missing, f"cuttingboard.runtime no longer exports: {missing}"


# Names patched via setattr(cuttingboard.runtime, ...) / monkeypatch.setattr —
# not reached through `from ... import`, but part of the preserved surface
# (PRD-170 R2/R3). All are read by functions that still live in __init__.
ATTR_PATCH_SURFACE = [
    "LOGS_DIR",
    "REPORTS_DIR",
    "MARKET_MAP_PATH",
    "WATCHLIST_PATH",
    "LATEST_RUN_PATH",
    "LATEST_CONTRACT_PATH",
    "TREND_STRUCTURE_PATH",
    "fetch_all",
    "fetch_ohlcv",
    "send_notification",
    "compute_regime",
    "MODE_LIVE",
    "MODE_FIXTURE",
    "MODE_SUNDAY",
    "PipelineResult",
    "_PartialPipelineResult",
    "cli_main",
    "_run_pipeline",
    "_execute_notify_run",
]


def test_attribute_patch_surface_present() -> None:
    missing = [n for n in ATTR_PATCH_SURFACE if not hasattr(rt, n)]
    assert not missing, f"cuttingboard.runtime missing patch-surface names: {missing}"
