"""PRD-319 R1: Node-executed table test of the PRODUCTION Worker gate.

Follows the PRD-250 precedent (Node-executed client verdict): the table below
drives the ACTUAL exported ``resolveSlot`` from
``workers/cuttingboard-clock/src/index.js`` under Node — never a Python
mirror. Every weekday cron fire is asserted in BOTH DST seasons, so a
zero-dispatch or two-dispatch instant, a slot-identity error, or a silently
retired seasonal PRE cannot pass.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

WORKER = Path(__file__).resolve().parent.parent / "workers" / "cuttingboard-clock" / "src" / "index.js"

pytestmark = pytest.mark.skipif(
    shutil.which("node") is None, reason="node is required to execute the production worker gate"
)


def _utc_ms(y: int, mo: int, d: int, h: int, mi: int) -> int:
    return int(datetime(y, mo, d, h, mi, tzinfo=timezone.utc).timestamp() * 1000)


PIPE = "cuttingboard.yml"
HOURLY = "hourly_alert.yml"

# (utc instant, expected) — expected is None, ("pipeline", slot/mode) or ("hourly", "HH:MM").
# PDT weekday: Tue 2026-05-19 (UTC-7). PST weekday: Mon 2026-01-12 (UTC-8).
CASES = [
    # --- PRE: UTC-anchored, BOTH seasons (PRD-319 R1 required edit) ---
    ((2026, 5, 19, 12, 50), ("pipeline", "PRE", "prefetch")),
    ((2026, 1, 12, 12, 50), ("pipeline", "PRE", "prefetch")),
    # PRE weekend guard (Sat 2026-05-16 / Sun 2026-01-11)
    ((2026, 5, 16, 12, 50), None),
    ((2026, 1, 11, 12, 50), None),
    # --- 0 13-21 * * 1-5 fires, PDT ---
    ((2026, 5, 19, 13, 0), ("pipeline", "OPEN", "live")),   # 06:00 PT
    ((2026, 5, 19, 14, 0), ("hourly", "07:00")),
    ((2026, 5, 19, 15, 0), ("hourly", "08:00")),
    ((2026, 5, 19, 16, 0), ("hourly", "09:00")),
    ((2026, 5, 19, 17, 0), ("hourly", "10:00")),
    ((2026, 5, 19, 18, 0), ("hourly", "11:00")),
    ((2026, 5, 19, 19, 0), ("hourly", "12:00")),
    ((2026, 5, 19, 20, 0), ("hourly", "13:00")),
    ((2026, 5, 19, 21, 0), None),                            # 14:00 PT — off cadence
    # --- 0 13-21 fires, PST ---
    ((2026, 1, 12, 13, 0), None),                            # 05:00 PT — off-season twin
    ((2026, 1, 12, 14, 0), ("pipeline", "OPEN", "live")),   # 06:00 PT
    ((2026, 1, 12, 15, 0), ("hourly", "07:00")),
    ((2026, 1, 12, 16, 0), ("hourly", "08:00")),
    ((2026, 1, 12, 17, 0), ("hourly", "09:00")),
    ((2026, 1, 12, 18, 0), ("hourly", "10:00")),
    ((2026, 1, 12, 19, 0), ("hourly", "11:00")),
    ((2026, 1, 12, 20, 0), ("hourly", "12:00")),
    ((2026, 1, 12, 21, 0), ("hourly", "13:00")),
    # --- 30 13,14 fires ---
    ((2026, 5, 19, 13, 30), ("hourly", "06:30")),            # PDT primary
    ((2026, 5, 19, 14, 30), None),                           # 07:30 PDT — off-season twin
    ((2026, 1, 12, 13, 30), None),                           # 05:30 PST — off-season twin
    ((2026, 1, 12, 14, 30), ("hourly", "06:30")),            # PST primary
    # --- 45 13,14 fires ---
    ((2026, 5, 19, 13, 45), ("hourly", "06:45")),
    ((2026, 5, 19, 14, 45), None),
    ((2026, 1, 12, 13, 45), None),
    ((2026, 1, 12, 14, 45), ("hourly", "06:45")),
    # --- weekend cadence guard (Sat 2026-05-16) ---
    ((2026, 5, 16, 13, 30), None),
]


def _run_gate(instants_ms: list[int]) -> list:
    script = (
        f"import {{ resolveSlot }} from '{WORKER.as_uri()}';\n"
        "const instants = JSON.parse(process.argv[1]);\n"
        "console.log(JSON.stringify(instants.map((ms) => resolveSlot(ms))));\n"
    )
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script, json.dumps(instants_ms)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"node failed: {proc.stderr}"
    return json.loads(proc.stdout.strip())


def test_production_gate_full_both_season_table():
    instants = [_utc_ms(*case[0]) for case in CASES]
    results = _run_gate(instants)
    for (when, expected), got in zip(CASES, results):
        label = datetime(*when, tzinfo=timezone.utc).isoformat()
        if expected is None:
            assert got is None, f"{label}: expected no dispatch, got {got}"
            continue
        assert got is not None, f"{label}: expected a dispatch, got none"
        if expected[0] == "pipeline":
            assert got["workflow"] == PIPE, f"{label}: {got}"
            assert got["inputs"]["slot"] == expected[1], f"{label}: {got}"
            assert got["inputs"]["mode"] == expected[2], f"{label}: {got}"
        else:
            assert got["workflow"] == HOURLY, f"{label}: {got}"
            assert got["inputs"] == {"kind": "routine", "slot": expected[1], "source": "cloudflare-worker"}, (
                f"{label}: {got}"
            )


def test_gate_uses_scheduled_time_not_handler_clock():
    """The resolver is pure over its argument: the same scheduledTime resolves
    identically no matter when it is evaluated (mutation seam: a handler-clock
    read would make these differ across runs — nothing here varies but the
    process invocation)."""
    ms = _utc_ms(2026, 5, 19, 13, 45)
    first = _run_gate([ms])
    second = _run_gate([ms])
    assert first == second == [
        {"workflow": HOURLY, "inputs": {"kind": "routine", "slot": "06:45", "source": "cloudflare-worker"}}
    ]


def test_gate_at_most_one_dispatch_per_instant():
    """PRD-319 R1: for every instant any cron can fire, at most ONE dispatch
    resolves — the dual-offset twins can never both dispatch for one slot."""
    results = _run_gate([_utc_ms(*case[0]) for case in CASES])
    # Group by (utc-date, resolved slot identity): no slot may be dispatched
    # twice from the same day's table rows.
    seen: dict[tuple, int] = {}
    for (when, _), got in zip(CASES, results):
        if got is None:
            continue
        key = (when[0], when[1], when[2], got["workflow"], got["inputs"].get("slot"))
        seen[key] = seen.get(key, 0) + 1
    assert all(v == 1 for v in seen.values()), f"duplicate dispatch rows: {seen}"
