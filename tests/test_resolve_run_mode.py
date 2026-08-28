"""PRD-189: tests for scripts/resolve_run_mode.py.

Scope is the dedicated premarket crons that write fresh, publish-safe artifacts:
live, sunday, and (PRD-193) the publish-safe cache-warm prefetch slot.
Resolution is a pure cron-string lookup keyed on github.event.schedule, so a
queue-delayed run still resolves to its slot. The intraday/orb slots are
intentionally NOT resolved here (deferred to PRD-192); the tests assert they
resolve to noop. CLI-mapping guards ensure every
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
        # PRD-319: dual-seasonal delayed OPEN fallbacks (was the single 5 13);
        # the off-season twin is no-oped by check_open_fallback_window.py,
        # never by mode resolution.
        ("20 13 * * 1-5", "live"),
        ("20 14 * * 1-5", "live"),
        ("30 23 * * 0", "sunday"),
        ("50 12 * * 1-5", "prefetch"),  # PRD-193: re-enabled cache-warm slot
    ],
)
def test_dedicated_cron_resolves(schedule, expected) -> None:
    assert _resolve(schedule) == expected


def test_old_live_cron_no_longer_resolves() -> None:
    # PRD-299 R7: the 0 13 live cron was replaced by the delayed 5 13 fallback,
    # so 0 13 must no longer map to live (a stale 0 13 firing resolves to noop).
    assert _resolve("0 13 * * 1-5") == "noop"


def test_resolution_is_time_independent() -> None:
    # The resolver takes no clock input, so a queue-delayed run resolves
    # identically to an on-time one -- the freeze bug (exact-minute match) is
    # gone by construction.
    assert _resolve("20 13 * * 1-5") == "live"


def test_retired_open_fallback_cron_resolves_to_noop() -> None:
    # PRD-319 R5 FAIL leg: the retired single fallback must never resolve live.
    assert _resolve("5 13 * * 1-5") == "noop"


# --- Deferred crons resolve to noop -----------------------------------------
# 50 13 / */30 = intraday/orb (deferred to PRD-192). The 50 12 prefetch cron is
# no longer here: PRD-193 re-enabled it as a publish-safe cache-warm slot (see
# test_dedicated_cron_resolves).
@pytest.mark.parametrize(
    "schedule", ["50 13 * * 1-5", "*/30 14-21 * * 1-5"]
)
def test_dropped_crons_resolve_to_noop(schedule) -> None:
    assert _resolve(schedule) == "noop"


def test_unknown_or_empty_schedule_is_noop() -> None:
    assert _resolve("0 0 * * *") == "noop"
    assert _resolve("") == "noop"


def test_non_schedule_event_is_noop() -> None:
    assert _resolve("20 13 * * 1-5", event="push") == "noop"


# --- PRD-299 R2: slot/mode consistency, fail-closed --------------------------
def test_validate_slot_mode_valid_pairs() -> None:
    rrm.validate_slot_mode("OPEN", "live")  # no raise
    rrm.validate_slot_mode("PRE", "prefetch")  # no raise
    rrm.validate_slot_mode(" OPEN ", "live")  # surrounding whitespace tolerated
    rrm.validate_slot_mode("", "live")  # empty slot -> no constraint (legacy)
    rrm.validate_slot_mode("", "prefetch")


@pytest.mark.parametrize(
    "slot,mode",
    [
        ("OPEN", "prefetch"),
        ("OPEN", "sunday"),
        ("OPEN", ""),
        ("PRE", "live"),
        ("PRE", ""),
        ("BOGUS", "live"),
        # Exact-case contract (Sol connector P2): lowercase/mixed-case must fail
        # closed -- the workflow predicates compare 'OPEN' case-sensitively.
        ("open", "live"),
        ("pre", "prefetch"),
        ("Open", "live"),
    ],
)
def test_validate_slot_mode_mismatch_fails_closed(slot, mode) -> None:
    with pytest.raises(rrm.SlotModeError):
        rrm.validate_slot_mode(slot, mode)


def test_main_fails_closed_on_bad_slot(monkeypatch) -> None:
    # R1/R2 (Sol I2): a non-{OPEN,PRE,empty} slot on a workflow_dispatch exits
    # non-zero from main() so the workflow step fails closed BEFORE first-success.
    monkeypatch.setenv("CB_EVENT_NAME", "workflow_dispatch")
    monkeypatch.setenv("CB_DISPATCH_MODE", "live")
    monkeypatch.setenv("CB_SCHEDULE", "")
    monkeypatch.setenv("CB_SLOT", "BOGUS")
    assert rrm.main() == 2


def test_main_ok_on_valid_open_and_on_empty_legacy_slot(monkeypatch, capsys) -> None:
    for slot, mode in (("OPEN", "live"), ("", "live"), ("PRE", "prefetch")):
        monkeypatch.setenv("CB_EVENT_NAME", "workflow_dispatch")
        monkeypatch.setenv("CB_DISPATCH_MODE", mode)
        monkeypatch.setenv("CB_SCHEDULE", "")
        monkeypatch.setenv("CB_SLOT", slot)
        assert rrm.main() == 0
        assert capsys.readouterr().out.strip() == mode


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
