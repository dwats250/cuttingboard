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
    # --- MON-FRI boundaries: Mon/Fri in both seasons (PDT Mon 2026-05-18,
    #     Fri 2026-05-22; PST Fri 2026-01-16; PST Mon 2026-01-12 above) ---
    ((2026, 5, 18, 13, 0), ("pipeline", "OPEN", "live")),
    ((2026, 5, 22, 20, 0), ("hourly", "13:00")),
    ((2026, 1, 16, 14, 0), ("pipeline", "OPEN", "live")),
    ((2026, 1, 16, 21, 0), ("hourly", "13:00")),
    # --- Sunday session transfer (owner ruling 2026-09-09): Sunday 23:30 UTC
    #     resolves to the EXISTING pipeline mode=sunday with NO slot; adjacent
    #     minutes, other days at 23:30Z, and Sunday weekday-cadence instants
    #     resolve nothing.
    ((2026, 5, 17, 23, 30), ("pipeline-sunday",)),   # Sun, PDT season
    ((2026, 1, 11, 23, 30), ("pipeline-sunday",)),   # Sun, PST season
    ((2026, 5, 17, 23, 29), None),
    ((2026, 5, 17, 23, 31), None),
    ((2026, 5, 16, 23, 30), None),                   # Saturday 23:30Z
    ((2026, 5, 18, 23, 30), None),                   # Monday 23:30Z (16:30 PT)
    ((2026, 5, 17, 13, 30), None),                   # Sunday at a weekday instant
    ((2026, 5, 17, 14, 0), None),
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
        if expected[0] == "pipeline-sunday":
            assert got == {
                "workflow": PIPE,
                "inputs": {"mode": "sunday", "source": "cloudflare-worker"},
            }, f"{label}: {got}"
            continue
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
        key = (when[0], when[1], when[2], got["workflow"], got["inputs"].get("slot"), got["inputs"].get("mode"))
        seen[key] = seen.get(key, 0) + 1
    assert all(v == 1 for v in seen.values()), f"duplicate dispatch rows: {seen}"


# --- Config pin: the committed example TOML is the deployable clock ------------

TOML = WORKER.parent.parent / "wrangler.example.toml"


def _toml() -> dict:
    import tomllib

    return tomllib.loads(TOML.read_text(encoding="utf-8"))


def test_wrangler_crons_exact_mon_fri_plus_sunday_session() -> None:
    """Completion PR (2026-09-09): the four weekday rows keep their exact times
    and use the explicit MON-FRI weekday field (never numeric 1-5); the Sunday
    session row is the single added cron. A time drift, a numeric weekday
    field, or an extra/missing row fails here."""
    crons = _toml()["triggers"]["crons"]
    assert crons == [
        "50 12 * * MON-FRI",
        "0 13-21 * * MON-FRI",
        "30 13,14 * * MON-FRI",
        "45 13,14 * * MON-FRI",
        "30 23 * * SUN",
    ]
    for cron in crons:
        assert not cron.endswith(("1-5", " 0")), cron


def test_wrangler_persists_workers_logs() -> None:
    """Completion PR: persisted Workers Logs so ACCEPTED/REJECTED lines survive
    the invocation (the smallest supported observability config)."""
    obs = _toml()["observability"]
    assert obs["enabled"] is True
    assert obs["head_sampling_rate"] == 1


# --- Scheduled handler: dispatch status honesty + no secret/body leakage -------

SECRET = "ghp_TEST_SECRET_VALUE_NEVER_LOGGED"
BODY_SENTINEL = "RESPONSE_BODY_SENTINEL_NEVER_LOGGED"


def _run_handler(
    instant_ms: int, *, status: int | None, with_token: bool = True, throw: bool = False
) -> dict:
    """Execute the PRODUCTION default export's scheduled() under Node with a
    stubbed global fetch; return captured console output and fetch calls."""
    script = (
        f"import worker from '{WORKER.as_uri()}';\n"
        "const cfg = JSON.parse(process.argv[1]);\n"
        "const out = []; const calls = [];\n"
        "console.log = (...a) => out.push(['log', a.join(' ')]);\n"
        "console.error = (...a) => out.push(['error', a.join(' ')]);\n"
        "globalThis.fetch = async (url, init) => {\n"
        "  calls.push({url, method: init.method, hasAuth: 'Authorization' in init.headers, body: init.body});\n"
        "  if (cfg.throw) throw new TypeError('fetch failed');\n"
        f"  return {{status: cfg.status, text: async () => '{BODY_SENTINEL}'}};\n"
        "};\n"
        "const env = cfg.with_token ? {GH_DISPATCH_TOKEN: cfg.secret} : {};\n"
        "await worker.scheduled({scheduledTime: cfg.ms, cron: ''}, env, {});\n"
        "process.stdout.write(JSON.stringify({out, calls}));\n"
    )
    cfg = {"ms": instant_ms, "status": status, "with_token": with_token, "throw": throw, "secret": SECRET}
    proc = subprocess.run(
        ["node", "--input-type=module", "-e", script, json.dumps(cfg)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, f"node failed: {proc.stderr}"
    return json.loads(proc.stdout)


def _joined(result: dict) -> str:
    return "\n".join(line for _, line in result["out"])


def _assert_no_leak(result: dict) -> None:
    text = _joined(result)
    assert SECRET not in text
    assert BODY_SENTINEL not in text
    assert "Authorization" not in text
    assert "Bearer" not in text


def test_handler_accepted_204_logs_status_workflow_slot_and_time() -> None:
    ms = _utc_ms(2026, 5, 19, 13, 45)  # 06:45 PDT hourly
    res = _run_handler(ms, status=204)
    text = _joined(res)
    assert "dispatch ACCEPTED" in text
    assert "status=204" in text
    assert "workflow=hourly_alert.yml" in text
    assert "slot=06:45" in text
    assert "scheduledTime=2026-05-19T13:45:00.000Z" in text
    assert len(res["calls"]) == 1
    call = res["calls"][0]
    assert call["url"].endswith("/actions/workflows/hourly_alert.yml/dispatches")
    assert call["method"] == "POST" and call["hasAuth"] is True
    assert json.loads(call["body"]) == {
        "ref": "main",
        "inputs": {"kind": "routine", "slot": "06:45", "source": "cloudflare-worker"},
    }
    _assert_no_leak(res)


@pytest.mark.parametrize("status", [401, 403, 422, 500])
def test_handler_rejected_logs_bounded_metadata_never_body(status: int) -> None:
    ms = _utc_ms(2026, 5, 19, 13, 0)  # 06:00 PDT OPEN
    res = _run_handler(ms, status=status)
    text = _joined(res)
    assert "dispatch REJECTED" in text
    assert f"status={status}" in text
    assert "workflow=cuttingboard.yml" in text
    assert "slot=OPEN" in text
    assert "fallback" not in text.lower()
    assert len(res["calls"]) == 1  # no retry
    _assert_no_leak(res)


def test_handler_missing_secret_rejects_without_request() -> None:
    ms = _utc_ms(2026, 5, 19, 14, 0)  # 07:00 PDT
    res = _run_handler(ms, status=204, with_token=False)
    text = _joined(res)
    assert "dispatch REJECTED" in text
    assert "reason=missing_secret" in text
    assert "slot=07:00" in text
    assert res["calls"] == []
    assert "fallback" not in text.lower()
    _assert_no_leak(res)


def test_handler_network_error_logs_safe_class_only() -> None:
    ms = _utc_ms(2026, 5, 19, 14, 0)
    res = _run_handler(ms, status=None, throw=True)
    text = _joined(res)
    assert "dispatch ERROR" in text
    assert "error=TypeError" in text
    assert "fetch failed" not in text  # message text is not echoed, only the class
    assert len(res["calls"]) == 1
    _assert_no_leak(res)


def test_handler_sunday_session_dispatches_mode_sunday_without_slot() -> None:
    ms = _utc_ms(2026, 5, 17, 23, 30)
    res = _run_handler(ms, status=204)
    text = _joined(res)
    assert "dispatch ACCEPTED" in text and "workflow=cuttingboard.yml" in text
    assert "mode=sunday" in text
    assert json.loads(res["calls"][0]["body"]) == {
        "ref": "main",
        "inputs": {"mode": "sunday", "source": "cloudflare-worker"},
    }
    _assert_no_leak(res)


def test_handler_no_slot_instant_makes_no_request() -> None:
    ms = _utc_ms(2026, 5, 19, 14, 30)  # 07:30 PDT — off-season twin
    res = _run_handler(ms, status=204)
    assert res["calls"] == []
    assert "no dispatch" in _joined(res)
    _assert_no_leak(res)
