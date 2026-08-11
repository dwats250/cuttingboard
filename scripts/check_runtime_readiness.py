#!/usr/bin/env python3
"""PRD-297: narrow deterministic runtime-readiness pre-gate for the morning executor.

Verifies the minimum prerequisites for `python -m cuttingboard --mode live` to
START -- the startup import chain, the parquet backend the OHLCV cache needs,
the CLI entrypoint's arg contract, and writable output directories. Every check
is deterministic, seconds-fast, network-free, and fails closed independently.

Explicitly NOT here: market-data plausibility, network/quote quality, the full
test suite, ruff, engine_doctor (its own opt-in gate), or any repair/mutation.
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRITABLE_DIRS = ("logs", "reports", "data/cache")


def check_import_chain(failures: list[str]) -> None:
    """(a) The live startup import graph resolves and cli_main is callable.

    Importing cuttingboard.runtime eagerly pulls pandas/yfinance/requests/dotenv
    and runs config-time sizing validation, so this exercises the whole startup
    surface in one import.
    """
    try:
        runtime = importlib.import_module("cuttingboard.runtime")
    except Exception as exc:  # noqa: BLE001 - any import-time failure is a readiness failure
        failures.append(f"import cuttingboard.runtime failed: {type(exc).__name__}: {exc}")
        return
    if not callable(getattr(runtime, "cli_main", None)):
        failures.append("cuttingboard.runtime.cli_main is not callable")


def check_parquet_backend(failures: list[str]) -> None:
    """(b) pyarrow is importable and pandas resolves it as the parquet engine.

    pyarrow is never imported directly by the package (used implicitly by
    pd.read_parquet/to_parquet for the OHLCV cache), so the import-chain check
    above cannot catch a broken/missing pyarrow.
    """
    try:
        import pyarrow  # noqa: F401
        from pandas.io.parquet import get_engine

        get_engine("pyarrow")
    except Exception as exc:  # noqa: BLE001
        failures.append(f"parquet backend (pyarrow) unavailable: {type(exc).__name__}: {exc}")


def check_entrypoint(failures: list[str]) -> None:
    """(c) `python -m cuttingboard --help` runs and the live arg contract is present."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "cuttingboard", "--help"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=ROOT,
        )
    except Exception as exc:  # noqa: BLE001
        failures.append(f"`python -m cuttingboard --help` did not run: {type(exc).__name__}: {exc}")
        return
    if result.returncode != 0:
        failures.append(f"`python -m cuttingboard --help` exited {result.returncode}")
        return
    if "--notify-mode" not in (result.stdout + result.stderr):
        failures.append("`python -m cuttingboard --help` output missing --notify-mode")


def check_writable_dirs(failures: list[str]) -> None:
    """(d) The directories the live path writes are creatable and writable."""
    for rel in WRITABLE_DIRS:
        directory = ROOT / rel
        probe = directory / ".readiness_write_probe"
        try:
            directory.mkdir(parents=True, exist_ok=True)
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{rel}: not writable: {type(exc).__name__}: {exc}")


def check_readiness() -> list[str]:
    failures: list[str] = []
    check_import_chain(failures)
    check_parquet_backend(failures)
    check_entrypoint(failures)
    check_writable_dirs(failures)
    return failures


def main(argv: list[str] | None = None) -> int:
    failures = check_readiness()
    if failures:
        print("Runtime readiness check failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Runtime readiness check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
