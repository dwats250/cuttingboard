"""PRD-297: behavior tests for the narrow runtime-readiness pre-gate.

Each of the four checks must fail closed under its red mutation, and the gate
must stay narrow -- no network, market semantics, pytest, ruff, or repair.
"""
from __future__ import annotations

import pandas.io.parquet

from pathlib import Path

from scripts import check_runtime_readiness as crr


# --- (a) import chain -------------------------------------------------------

def test_import_chain_passes_in_real_env():
    failures: list[str] = []
    crr.check_import_chain(failures)
    assert failures == []


def test_import_chain_fails_when_import_raises(monkeypatch):
    def raiser(name):
        raise ImportError("simulated broken startup import")

    monkeypatch.setattr(crr.importlib, "import_module", raiser)
    failures: list[str] = []
    crr.check_import_chain(failures)
    assert failures and "cuttingboard.runtime" in failures[0]


def test_import_chain_fails_when_cli_main_not_callable(monkeypatch):
    class FakeModule:  # no cli_main attribute
        pass

    monkeypatch.setattr(crr.importlib, "import_module", lambda name: FakeModule())
    failures: list[str] = []
    crr.check_import_chain(failures)
    assert failures and "cli_main" in failures[0]


# --- (b) parquet backend ----------------------------------------------------

def test_parquet_backend_passes_in_real_env():
    failures: list[str] = []
    crr.check_parquet_backend(failures)
    assert failures == []


def test_parquet_backend_fails_when_engine_unavailable(monkeypatch):
    def raiser(engine):
        raise ImportError("simulated missing pyarrow")

    monkeypatch.setattr(pandas.io.parquet, "get_engine", raiser)
    failures: list[str] = []
    crr.check_parquet_backend(failures)
    assert failures and "parquet" in failures[0]


# --- (c) entrypoint arg contract --------------------------------------------

class _FakeProc:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_entrypoint_passes_when_help_ok(monkeypatch):
    monkeypatch.setattr(crr.subprocess, "run", lambda *a, **k: _FakeProc(0, "usage: --mode --notify-mode"))
    failures: list[str] = []
    crr.check_entrypoint(failures)
    assert failures == []


def test_entrypoint_fails_on_nonzero_exit(monkeypatch):
    monkeypatch.setattr(crr.subprocess, "run", lambda *a, **k: _FakeProc(2, "", "boom"))
    failures: list[str] = []
    crr.check_entrypoint(failures)
    assert failures and "exited 2" in failures[0]


def test_entrypoint_fails_when_arg_contract_missing(monkeypatch):
    monkeypatch.setattr(crr.subprocess, "run", lambda *a, **k: _FakeProc(0, "usage: --mode only"))
    failures: list[str] = []
    crr.check_entrypoint(failures)
    assert failures and "--notify-mode" in failures[0]


# --- (d) writable dirs ------------------------------------------------------

def test_writable_dirs_pass_on_writable_root(monkeypatch, tmp_path):
    monkeypatch.setattr(crr, "ROOT", tmp_path)
    monkeypatch.setattr(crr, "WRITABLE_DIRS", ("logs", "reports", "data/cache"))
    failures: list[str] = []
    crr.check_writable_dirs(failures)
    assert failures == []


def test_writable_dirs_fail_when_target_is_a_file(monkeypatch, tmp_path):
    (tmp_path / "logs").write_text("i am a file, not a dir", encoding="utf-8")
    monkeypatch.setattr(crr, "ROOT", tmp_path)
    monkeypatch.setattr(crr, "WRITABLE_DIRS", ("logs",))
    failures: list[str] = []
    crr.check_writable_dirs(failures)
    assert failures and "logs" in failures[0]


# --- exit code + narrowness -------------------------------------------------

def test_main_returns_zero_when_all_pass(monkeypatch):
    monkeypatch.setattr(crr, "check_readiness", lambda: [])
    assert crr.main([]) == 0


def test_main_returns_one_on_any_failure(monkeypatch):
    monkeypatch.setattr(crr, "check_readiness", lambda: ["something broke"])
    assert crr.main([]) == 1


def test_gate_excludes_broad_concerns():
    """The readiness gate must not IMPORT network/test/market libraries (narrowness)."""
    import ast

    tree = ast.parse(Path(crr.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    for forbidden in ("requests", "urllib", "yfinance", "pytest", "socket", "http"):
        assert forbidden not in imported, f"runtime-readiness gate must not import {forbidden!r}"
