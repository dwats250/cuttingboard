"""PRD-299: behavioral tests for GitHub-native OPEN first-success coordination.

Two kinds of test:
  * HELPER unit tests over scripts/check_open_slot_satisfied.py with fixture-
    injected Actions-API run records and an injected `now_utc` -- no live network
    (packet audits/cf-clock-executor-coordination-2026-08 v0.4 matrix T1-T24c).
  * STRUCTURAL assertions over .github/workflows/cuttingboard.yml for the
    guarantees whose truth is only determined at GitHub runtime (queue:max
    non-eviction T25-T27, validation-before-no-op ordering) -- PRD-198 #5: the
    runtime behavior is verified where the decision is made (GitHub), and pinned
    structurally here.
"""
from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "check_open_slot_satisfied", _REPO / "scripts" / "check_open_slot_satisfied.py"
)
assert _SPEC and _SPEC.loader
cos = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cos)

_WORKFLOW = _REPO / ".github" / "workflows" / "cuttingboard.yml"

# A summer (EDT) and a winter (EST) trading date. CF fires at 13:00 UTC on both;
# market open is 09:30 ET -> 13:30 UTC (EDT) / 14:30 UTC (EST).
SUMMER = "2026-08-11"  # Tuesday, EDT
WINTER = "2026-01-15"  # Thursday, EST


def _now(date_str: str, hh: int = 13, mm: int = 10) -> datetime:
    y, m, d = (int(x) for x in date_str.split("-"))
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


def _run(
    *,
    event="workflow_dispatch",
    title="CB-SLOT:OPEN",
    created="2026-08-11T13:00:05Z",
    conclusion="success",
    status="completed",
    branch="main",
    path=".github/workflows/cuttingboard.yml",
    rid=99,
    **extra,
):
    r = {
        "path": path,
        "event": event,
        "head_branch": branch,
        "display_title": title,
        "status": status,
        "conclusion": conclusion,
        "created_at": created,
        "id": rid,
    }
    r.update(extra)
    return r


def _eval(runs, now=None, current="1"):
    return cos.evaluate_runs(runs, now or _now(SUMMER), current)


# --- T1/T2/T17: qualifying successes satisfy --------------------------------
def test_t1_cf_dispatch_open_success_satisfies() -> None:
    assert _eval([_run(event="workflow_dispatch", created=f"{SUMMER}T13:00:05Z")]) == cos.SATISFIED


def test_t2_t17_valid_halt_success_satisfies() -> None:
    # A valid MARKET_STRESS HALT concludes execution-success (PRD-298); the proof
    # keys on conclusion==success, so a HALT-origin success satisfies like TRADE.
    assert _eval([_run(created=f"{SUMMER}T13:00:05Z", conclusion="success")]) == cos.SATISFIED


def test_t7_schedule_fallback_success_satisfies() -> None:
    assert _eval([_run(event="schedule", created=f"{SUMMER}T13:05:30Z")]) == cos.SATISFIED


# --- T3/T4/T18: failures / publish-failures do NOT satisfy -------------------
@pytest.mark.parametrize("conclusion", ["failure", "cancelled", "timed_out", None])
def test_t3_t4_t18_non_success_does_not_satisfy(conclusion) -> None:
    assert _eval([_run(created=f"{SUMMER}T13:00:05Z", conclusion=conclusion)]) == cos.UNSATISFIED


# --- T5/T6: empty / duplicate ------------------------------------------------
def test_t5_empty_run_list_unsatisfied() -> None:
    assert _eval([]) == cos.UNSATISFIED


def test_t6_duplicate_successes_deterministic_satisfied() -> None:
    runs = [
        _run(event="workflow_dispatch", created=f"{SUMMER}T13:00:05Z", rid=10),
        _run(event="workflow_dispatch", created=f"{SUMMER}T13:00:07Z", rid=11),
    ]
    assert _eval(runs) == cos.SATISFIED


# --- T10/T24c: date bucket + workflow_dispatch premarket bound ----------------
def test_t10_previous_day_does_not_satisfy() -> None:
    assert _eval([_run(created="2026-08-10T13:00:05Z")]) == cos.UNSATISFIED


def test_t24c_dispatch_after_market_open_does_not_satisfy() -> None:
    # 14:00 UTC = 10:00 EDT, past the 09:30 ET open -> later operator/recovery run.
    assert _eval([_run(event="workflow_dispatch", created=f"{SUMMER}T14:00:00Z")]) == cos.UNSATISFIED


def test_t24c_dispatch_before_lower_bound_does_not_satisfy() -> None:
    # 12:00 UTC (08:00 EDT) is before the 12:55 UTC lower bound (off-hour-early).
    assert _eval([_run(event="workflow_dispatch", created=f"{SUMMER}T12:00:00Z")]) == cos.UNSATISFIED


# --- T11/T12/T13: token / branch exclusions ---------------------------------
def test_t11_pre_token_does_not_satisfy_open() -> None:
    assert _eval([_run(event="schedule", title="CB-SLOT:PRE", created=f"{SUMMER}T12:50:00Z")]) == cos.UNSATISFIED


def test_t12_no_token_manual_run_does_not_satisfy() -> None:
    assert _eval([_run(event="workflow_dispatch", title="Cuttingboard Pipeline 42", created=f"{SUMMER}T13:00:05Z")]) == cos.UNSATISFIED


def test_t13_wrong_ref_does_not_satisfy() -> None:
    assert _eval([_run(branch="feature/x", created=f"{SUMMER}T13:00:05Z")]) == cos.UNSATISFIED


def test_wrong_workflow_path_does_not_satisfy() -> None:
    assert _eval([_run(path=".github/workflows/hourly_alert.yml", created=f"{SUMMER}T13:00:05Z")]) == cos.UNSATISFIED


# --- T16: source is provenance-only (never read by the predicate) -----------
def test_t16_source_field_is_inert() -> None:
    # A spoofed provenance field cannot change satisfaction: a non-qualifying run
    # (post-open manual) stays UNSATISFIED even labelled source=cloudflare-worker.
    spoof = _run(event="workflow_dispatch", created=f"{SUMMER}T14:30:00Z", source="cloudflare-worker")
    assert _eval([spoof]) == cos.UNSATISFIED
    # And a qualifying run satisfies regardless of any source label.
    ok = _run(event="workflow_dispatch", created=f"{SUMMER}T13:00:05Z", source="whatever")
    assert _eval([ok]) == cos.SATISFIED


# --- T19: current run excluded ----------------------------------------------
def test_t19_current_run_excluded() -> None:
    assert cos.evaluate_runs([_run(created=f"{SUMMER}T13:00:05Z", rid=555)], _now(SUMMER), current_run_id="555") == cos.UNSATISFIED


# --- T20: manual in-window slot=OPEN success satisfies (accepted override) ---
def test_t20_manual_in_window_open_satisfies() -> None:
    # 13:20 UTC = 09:20 EDT, still premarket -> a real in-window OPEN publish.
    assert _eval([_run(event="workflow_dispatch", created=f"{SUMMER}T13:20:00Z")]) == cos.SATISFIED


# --- T23: rerun-conclusion-mutation (a re-run that flips success->failure) ----
def test_t23_reran_fallback_now_failing_does_not_satisfy() -> None:
    # The list endpoint returns the latest attempt's conclusion; a schedule
    # fallback re-run that failed drops from the success set. Safety holds
    # elsewhere (the published board persists on the publish branch); here we
    # only assert the proof no longer counts it.
    assert _eval([_run(event="schedule", created=f"{SUMMER}T13:05:00Z", conclusion="failure")]) == cos.UNSATISFIED


# --- T24 / T24b: DST correctness + delayed schedule fallback -----------------
def test_t24_dst_summer_and_winter_cf_dispatch_satisfies() -> None:
    assert _eval([_run(event="workflow_dispatch", created=f"{SUMMER}T13:00:05Z")], _now(SUMMER)) == cos.SATISFIED
    assert _eval([_run(event="workflow_dispatch", created=f"{WINTER}T13:00:05Z")], _now(WINTER, hh=13, mm=10)) == cos.SATISFIED


def test_t24_winter_premarket_vs_postopen_dispatch() -> None:
    # Winter (EST): market open 09:30 EST = 14:30 UTC.
    now_w = _now(WINTER, hh=14, mm=0)
    # 14:00 UTC = 09:00 EST, premarket -> satisfies.
    assert _eval([_run(event="workflow_dispatch", created=f"{WINTER}T14:00:00Z")], now_w) == cos.SATISFIED
    # 14:45 UTC = 09:45 EST, post-open -> does NOT satisfy.
    assert _eval([_run(event="workflow_dispatch", created=f"{WINTER}T14:45:00Z")], now_w) == cos.UNSATISFIED


def test_t24b_delayed_schedule_fallback_still_satisfies() -> None:
    # The S1 fix: a schedule fallback GitHub creates well after the 13:05 nominal
    # (here 14:30 UTC, past any naive 30-min cap) STILL satisfies -- schedule
    # events are automatic by definition, so no intra-day lateness ceiling.
    now = _now(SUMMER, hh=14, mm=40)
    assert _eval([_run(event="schedule", created=f"{SUMMER}T14:30:00Z")], now) == cos.SATISFIED


def test_t24b_mutation_schedule_would_break_under_fixed_cutoff() -> None:
    # Reddens S1: if schedule events were subject to the dispatch upper bound
    # (< market open), the 14:30 UTC (10:30 EDT, post-open) fallback would be
    # wrongly excluded. Prove the current logic does NOT apply that cutoff to
    # schedule (it satisfies), while the SAME instant as a workflow_dispatch does
    # NOT satisfy -- the event split is load-bearing.
    now = _now(SUMMER, hh=14, mm=40)
    created = f"{SUMMER}T14:30:00Z"
    assert _eval([_run(event="schedule", created=created)], now) == cos.SATISFIED
    assert _eval([_run(event="workflow_dispatch", created=created)], now) == cos.UNSATISFIED


# --- T8: malformed record -> PROOF_ERROR (never UNSATISFIED/SATISFIED) --------
def test_t8_malformed_created_at_raises_proof_error() -> None:
    with pytest.raises(cos.ProofError):
        _eval([_run(created=12345)])


def test_t8_malformed_record_not_object_raises_proof_error() -> None:
    with pytest.raises(cos.ProofError):
        _eval(["not-a-dict"])


def test_t8_naive_created_at_raises_proof_error() -> None:
    with pytest.raises(cos.ProofError):
        _eval([_run(created="2026-08-11 13:00:00")])  # no tz


# --- T9/T21: main() maps API/proof errors to PROOF_ERROR, exit 0 (execute) ---
def test_t9_main_proof_error_prints_state_and_exits_zero(monkeypatch, capsys) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "dwats250/cuttingboard")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)

    def boom(*a, **k):
        raise cos.ProofError("simulated API failure")

    monkeypatch.setattr(cos, "_collect_runs", boom)
    rc = cos.main([])
    out = capsys.readouterr().out
    assert rc == 0  # fail toward availability -- never abort the step
    assert "CB_OPEN_SLOT_STATE=PROOF_ERROR" in out


def test_t21_main_missing_env_is_proof_error(monkeypatch, capsys) -> None:
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    rc = cos.main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "CB_OPEN_SLOT_STATE=PROOF_ERROR" in out


def test_main_satisfied_writes_github_output(monkeypatch, capsys, tmp_path) -> None:
    monkeypatch.setenv("GITHUB_REPOSITORY", "dwats250/cuttingboard")
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    gh_out = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(gh_out))
    monkeypatch.setattr(cos, "_collect_runs", lambda *a, **k: [_run(event="schedule", created=f"{datetime.now(timezone.utc).date()}T13:05:00Z")])
    rc = cos.main([])
    assert rc == 0
    assert "state=" in gh_out.read_text()


# --- STRUCTURAL: workflow guarantees only determined at GitHub runtime --------
def _wf() -> str:
    return _WORKFLOW.read_text(encoding="utf-8")


def test_struct_run_name_carrier_present() -> None:
    text = _wf()
    assert "run-name:" in text
    assert "CB-SLOT:" in text
    assert "format('CB-SLOT:{0}', inputs.slot)" in text


def test_struct_cron_swapped() -> None:
    # PRD-319 R5: dual-seasonal delayed fallbacks replace the single 5 13; the
    # exact pair is pinned, both retired live crons are banned, and the season
    # gate + run-name + concurrency + first-success predicates must all
    # recognize BOTH new expressions (counted; a partial literal update fails).
    text = _wf()
    # Quote-delimited: '20 13 * * 1-5' contains the bare "0 13 * * 1-5" substring.
    assert "'0 13 * * 1-5'" not in text   # old live cron removed (PRD-299 R7)
    assert "'5 13 * * 1-5'" not in text   # single fallback retired (PRD-319 R5)
    assert text.count("'20 13 * * 1-5'") >= 4  # cron + run-name + concurrency + gate/openslot ifs
    assert text.count("'20 14 * * 1-5'") >= 4
    assert "check_open_fallback_window.py" in text
    assert "OFF_SEASON_NOOP" in text


def test_struct_slot_and_source_inputs_present() -> None:
    text = _wf()
    assert "slot:" in text and "source:" in text


def test_struct_dedicated_open_group_and_queue_max() -> None:
    # T25/T26/T27 non-eviction is a GitHub runtime property; structurally the
    # workflow MUST route OPEN to a dedicated group AND use native queue: max.
    text = _wf()
    assert "cb-open-coordination" in text
    assert "queue: max" in text


def test_struct_validation_ordered_before_no_op_decision() -> None:
    # Sol C5 ordering bind: slot/mode validation (Determine run mode, which runs
    # resolve_run_mode's validate_slot_mode) MUST precede the first-success
    # pre-check step, so a malformed OPEN dispatch fails closed before it could
    # become a satisfying no-op.
    text = _wf()
    i_mode = text.index("name: Determine run mode")
    i_pre = text.index("name: OPEN first-success pre-check")
    assert i_mode < i_pre
    assert "CB_SLOT:" in text[i_mode:i_pre] or "CB_SLOT:" in text  # slot passed to resolver
    assert "CB_SLOT: ${{ github.event.inputs.slot }}" in text


def test_struct_live_path_gated_on_not_satisfied() -> None:
    # The live-execute path skips on a SATISFIED no-op (so a coordinated no-op
    # concludes success without spurious CI-proof/readiness failures).
    text = _wf()
    assert "steps.openslot.outputs.state != 'SATISFIED'" in text
    # Run live pipeline specifically must carry the guard.
    i_live = text.index("name: Run live pipeline")
    guard_region = text[i_live : i_live + 200]
    assert "steps.openslot.outputs.state != 'SATISFIED'" in guard_region


def test_struct_precheck_uses_ambient_token_no_new_credential() -> None:
    text = _wf()
    i_pre = text.index("name: OPEN first-success pre-check")
    region = text[i_pre : i_pre + 600]
    assert "github.token" in region
    # permissions block still only actions: read (no new credential).
    assert "actions: read" in text


@pytest.mark.parametrize(
    "step_name",
    [
        "Restore OHLCV cache",
        "Restore publish state",
        "Install dev dependencies",
        "Engine health check",
        "Upload engine doctor artifacts",
        "Generate commit message",
    ],
)
def test_struct_satisfied_noop_skips_fallible_tail(step_name) -> None:
    # Sol connector P2: on a SATISFIED coordinated no-op, every fallible live/
    # shared step must be gated on state != 'SATISFIED' so a transient failure
    # cannot fail the no-op run and fire the failure notifier.
    text = _wf()
    i = text.index(f"name: {step_name}")
    # The step's `if:` (and any folded continuation) is within the block before
    # the next step definition.
    nxt = text.find("      - name:", i + 1)
    block = text[i:nxt] if nxt != -1 else text[i:]
    assert "steps.openslot.outputs.state != 'SATISFIED'" in block, (
        f"{step_name!r} must be gated on the OPEN no-op state (P2)"
    )
