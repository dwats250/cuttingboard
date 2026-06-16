"""PRD-189: tests for scripts/resolve_run_mode.py.

Scope is the dedicated premarket crons that write fresh, publish-safe artifacts:
live and sunday. Resolution is a pure cron-string lookup keyed on
github.event.schedule, so a queue-delayed run still resolves to its slot. The
12:50 prefetch cron and the intraday/orb slots are intentionally NOT resolved
here (prefetch deferred to a cache-persistence rework PRD; intraday to PRD-192);
the tests assert they resolve to noop. CLI-mapping guards ensure every
resolver-emittable slot maps to a `python -m cuttingboard` invocation the parser
accepts (the Codex-found `--mode <slot>` crash must never recur).
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

from cuttingboard.runtime import build_parser

_REPO = Path(__file__).resolve().parents[1]
_WORKFLOW = _REPO / ".github" / "workflows" / "cuttingboard.yml"
_SPEC = importlib.util.spec_from_file_location(
    "resolve_run_mode", _REPO / "scripts" / "resolve_run_mode.py"
)
assert _SPEC and _SPEC.loader
rrm = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(rrm)

_DROPPED_SLOTS = ("orb_trajectory", "post_orb", "midmorning", "power_hour")
_INVOCATION_RE = re.compile(r"python -m cuttingboard --mode (\S+) --notify-mode (\S+)")


def _resolve(schedule: str = "", *, event: str = "schedule", dispatch: str = "") -> str:
    return rrm.resolve(event_name=event, dispatch_mode=dispatch, schedule=schedule)


# --- Dedicated crons resolve by schedule string (delay-immune) --------------
@pytest.mark.parametrize(
    "schedule,expected",
    [
        ("0 13 * * 1-5", "live"),
        ("30 23 * * 0", "sunday"),
    ],
)
def test_dedicated_cron_resolves(schedule, expected) -> None:
    assert _resolve(schedule) == expected


def test_resolution_is_time_independent() -> None:
    # The resolver takes no clock input, so a queue-delayed run resolves
    # identically to an on-time one -- the freeze bug (exact-minute match) is
    # gone by construction.
    assert _resolve("0 13 * * 1-5") == "live"


# --- Deferred crons resolve to noop -----------------------------------------
# 50 12 = prefetch (deferred to the prefetch cache-persistence rework PRD; its
# publish path trips the PRD-119 freshness gate and its cache does not persist).
# 50 13 / */30 = intraday/orb (deferred to PRD-192).
@pytest.mark.parametrize(
    "schedule", ["50 12 * * 1-5", "50 13 * * 1-5", "*/30 14-21 * * 1-5"]
)
def test_dropped_crons_resolve_to_noop(schedule) -> None:
    assert _resolve(schedule) == "noop"


def test_unknown_or_empty_schedule_is_noop() -> None:
    assert _resolve("0 0 * * *") == "noop"
    assert _resolve("") == "noop"


def test_non_schedule_event_is_noop() -> None:
    assert _resolve("0 13 * * 1-5", event="push") == "noop"


# --- workflow_dispatch: explicit operator intent ----------------------------
def test_workflow_dispatch_returns_dispatch_mode() -> None:
    assert _resolve(event="workflow_dispatch", dispatch="verify") == "verify"
    assert _resolve(event="workflow_dispatch", dispatch="sunday") == "sunday"


def test_workflow_dispatch_empty_mode_is_noop() -> None:
    assert _resolve(event="workflow_dispatch", dispatch="") == "noop"


# --- Resolver outputs must map to CLI invocations the parser accepts --------
# Guards the Codex P1: a resolved slot must be invoked with a --mode/--notify-mode
# combo build_parser() accepts (`--mode orb_trajectory` exits argparse code 2).
def _scheduled_modes() -> set[str]:
    return set(rrm._DEDICATED.values())


def test_every_workflow_invocation_is_parser_valid() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    invocations = _INVOCATION_RE.findall(text)
    assert invocations, "no `python -m cuttingboard --mode ... --notify-mode ...` lines found"
    parser = build_parser()
    for mode, notify in invocations:
        # argparse raises SystemExit on an invalid choice; a valid combo parses.
        parser.parse_args(["--mode", mode, "--notify-mode", notify])


def test_every_scheduled_slot_is_wired_to_a_valid_dispatch_step() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    parser = build_parser()
    for mode in _scheduled_modes():
        assert f"--mode {mode} " in text, f"{mode} has no dispatch invocation"
        assert f"job_mode == '{mode}'" in text, f"{mode} has no dispatch `if:` guard"
        parser.parse_args(["--mode", mode, "--notify-mode", "premarket"])


def test_dropped_slots_are_not_resolved_or_dispatched() -> None:
    text = _WORKFLOW.read_text(encoding="utf-8")
    emitted = set(rrm._DEDICATED.values())
    for slot in _DROPPED_SLOTS:
        assert slot not in emitted, f"{slot} should not be resolver-emittable"
        assert f"--notify-mode {slot}" not in text, f"{slot} dispatch invocation still present"
        assert f"job_mode == '{slot}'" not in text, f"{slot} dispatch guard still present"
