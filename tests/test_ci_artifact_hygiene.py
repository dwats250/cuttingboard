"""PRD-129 — CI artifact hygiene regression tests.

These tests guard the interaction between two prior PRDs:

* PRD-020 — Engine health check step writes ``engine_doctor.json`` and
  ``engine_doctor.txt`` to the repo root for artifact upload.
* PRD-100-PATCH — ``tools/ci_push_artifacts.sh`` aborts the publish step if
  ``git status --short`` is non-empty (it publishes committed blobs, so an
  unstaged artifact would be silently dropped). PRD-194 retargeted that helper
  from a direct push to ``main`` to a worktree publish onto the ``publish``
  branch, but the dirty-tree guard is unchanged.

If either filename is not gitignored, the workflow's Engine health check
step leaves the working tree dirty by the push guard's definition and the
pipeline's final Push step fails. This test enforces both the
pattern-coverage assertion (``git check-ignore``) and the push-guard
predicate (``git status --short`` is empty) so the regression cannot
silently return.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CI_ARTIFACT_FILENAMES = ("engine_doctor.json", "engine_doctor.txt")
HOURLY_REQUIRED_STAGED_ARTIFACTS = (
    "logs/audit.jsonl",
    "logs/market_map.json",
    "logs/latest_hourly_market_map.json",
    "logs/macro_drivers_snapshot.json",
    "logs/trend_structure_snapshot.json",
    "logs/latest_run.json",
    "logs/latest_contract.json",
    "logs/latest_payload.json",
    "logs/latest_hourly_run.json",
    "logs/latest_hourly_contract.json",
    "logs/latest_hourly_payload.json",
    "ui/contract.json",
    "ui/dashboard.html",
    "ui/index.html",
)


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("filename", CI_ARTIFACT_FILENAMES)
def test_engine_doctor_artifact_is_gitignored(filename: str) -> None:
    """R1 / R3(a) — pattern-coverage assertion.

    ``git check-ignore`` MUST exit 0 for each filename CI writes to the
    repo root during the Engine health check step.
    """

    result = _run(["git", "check-ignore", "-q", filename], REPO_ROOT)
    assert result.returncode == 0, (
        f"{filename!r} is not gitignored; the Engine health check step "
        f"(PRD-020) would leave it as an untracked file and trip the "
        f"push-guard dirty-tree check in tools/ci_push_artifacts.sh "
        f"(PRD-100-PATCH). check-ignore exit={result.returncode}, "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}."
    )


def test_engine_doctor_artifacts_leave_porcelain_clean() -> None:
    """R2 / R3(b) — push-guard predicate assertion.

    Creating both engine doctor outputs at the exact repo-root paths CI
    uses MUST NOT add lines to ``git status --short`` for those paths.
    This is the predicate ``tools/ci_push_artifacts.sh`` evaluates before it
    publishes to the ``publish`` branch (PRD-194); any non-empty output
    aborts the publish step.

    The test path-scopes the ``git status`` invocation so unrelated
    in-progress work in the developer's tree cannot mask the assertion.
    It only writes the artifacts when they are absent and removes only
    the files it created.
    """

    created: list[Path] = []
    try:
        for filename in CI_ARTIFACT_FILENAMES:
            path = REPO_ROOT / filename
            if path.exists():
                continue
            path.write_text("PRD-129 test fixture; safe to delete.\n")
            created.append(path)

        result = _run(
            ["git", "status", "--short", "--", *CI_ARTIFACT_FILENAMES],
            REPO_ROOT,
        )
        assert result.returncode == 0, (
            f"git status failed: {result.stderr!r}"
        )
        assert result.stdout == "", (
            "git status --short produced non-empty output for engine "
            "doctor artifacts at the repo root. "
            "tools/ci_push_artifacts.sh treats any non-empty status as "
            "a dirty tree and aborts the push step. Offending output:\n"
            f"{result.stdout}"
        )
    finally:
        for path in created:
            path.unlink(missing_ok=True)


def test_hourly_workflow_stages_all_mutated_artifacts_before_push() -> None:
    """Hourly artifacts written before the push guard must be staged.

    ``tools/ci_push_artifacts.sh`` intentionally fails on any dirty tree
    before rebase. Keep this list aligned with files the hourly run mutates
    and expects to publish before invoking the push helper.
    """

    workflow = REPO_ROOT / ".github" / "workflows" / "hourly_alert.yml"
    text = workflow.read_text(encoding="utf-8")

    commit_step = text[text.index("- name: Commit hourly artifacts"):]
    push_idx = commit_step.index("- name: Push hourly artifacts")
    commit_step = commit_step[:push_idx]

    for artifact in HOURLY_REQUIRED_STAGED_ARTIFACTS:
        assert artifact in commit_step, (
            f"{artifact} is not staged by the hourly Commit hourly artifacts "
            "step before tools/ci_push_artifacts.sh runs. Any mutated but "
            "unstaged artifact leaves the tree dirty and correctly trips "
            "the push guard."
        )


def test_hourly_workflow_renders_with_isolated_market_map_path() -> None:
    """PRD-166 R3: the hourly render step points the renderer at the isolated
    hourly market_map so the shared logs/market_map.json can never be the
    source of an hourly render's PRD-118 R3 lineage mismatch.
    """

    workflow = REPO_ROOT / ".github" / "workflows" / "hourly_alert.yml"
    text = workflow.read_text(encoding="utf-8")

    render_step = text[text.index("- name: Render and stage hourly artifacts"):]
    render_step = render_step[: render_step.index("- name: Check hourly readiness")]

    assert "--market-map-path logs/latest_hourly_market_map.json" in render_step, (
        "the hourly render step does not pass "
        "--market-map-path logs/latest_hourly_market_map.json; without it the "
        "renderer falls back to the shared logs/market_map.json (PRD-166 R3)."
    )


# --- PRD-178 R8 — Dashboard Preview workflow safety anchors ----------------
#
# The preview workflow's entire safety claim is structural: it cannot send,
# commit, or deploy. These tests pin each anchor so a regression FAILS the
# suite rather than smoke-passing.

PREVIEW_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "dashboard_preview.yml"


def _preview_workflow_text() -> str:
    return PREVIEW_WORKFLOW.read_text(encoding="utf-8")


def test_preview_workflow_is_dispatch_only() -> None:
    """PRD-178 R1/R8(a) — the only trigger is workflow_dispatch.

    Any schedule, push, pull_request, or workflow_run trigger would let the
    preview run without an operator asking for it, and a push trigger on the
    wrong ref could race the hourly publish path.
    """

    text = _preview_workflow_text()
    assert "workflow_dispatch:" in text, (
        "dashboard_preview.yml lost its workflow_dispatch trigger; the "
        "preview must remain operator-dispatched."
    )
    for forbidden in ("schedule:", "push:", "pull_request:", "workflow_run:"):
        assert forbidden not in text, (
            f"dashboard_preview.yml contains forbidden trigger key "
            f"{forbidden!r}; PRD-178 R1 requires workflow_dispatch as the "
            "sole trigger."
        )


def test_preview_workflow_has_zero_telegram_capability() -> None:
    """PRD-178 R2/R8(b) — no Telegram credential reaches any step.

    send_telegram degrades to an audited skipped/not_configured no-op when
    the env vars are absent (cuttingboard/output.py). Keeping the literal
    out of the workflow file entirely is what guarantees absence.
    """

    text = _preview_workflow_text()
    assert "TELEGRAM" not in text.upper(), (
        "dashboard_preview.yml references TELEGRAM; the preview workflow "
        "must not have send capability (PRD-178 R2)."
    )


def test_preview_workflow_cannot_commit_push_or_deploy() -> None:
    """PRD-178 R3/R8(c) — no commit, push, or deploy step exists."""

    text = _preview_workflow_text()
    for forbidden in ("git commit", "git push", "deploy-pages", "ci_push_artifacts"):
        assert forbidden not in text, (
            f"dashboard_preview.yml contains {forbidden!r}; the preview "
            "workflow must not be able to publish (PRD-178 R3)."
        )


def test_preview_workflow_permissions_exactly_contents_read() -> None:
    """PRD-178 R3/R8(e) — permissions grant exactly contents: read.

    Parses the single permissions block and requires it to contain exactly
    one grant: ``contents: read``. Any additional key (pages, id-token,
    contents: write) widens the blast radius beyond a read-only preview.
    """

    text = _preview_workflow_text()
    lines = text.splitlines()
    assert lines.count("permissions:") == 1, (
        "dashboard_preview.yml must declare exactly one top-level "
        "permissions block (found "
        f"{lines.count('permissions:')})."
    )
    start = lines.index("permissions:")
    block: list[str] = []
    for line in lines[start + 1:]:
        if not line.startswith(" ") or not line.strip():
            break
        block.append(line.strip())
    assert block == ["contents: read"], (
        "dashboard_preview.yml permissions block must be exactly "
        f"['contents: read']; found {block!r} (PRD-178 R3)."
    )


def test_preview_workflow_renders_through_publish_gates_with_hourly_trio() -> None:
    """PRD-178 R4/R8(d) — render parity with the hourly publish path.

    The render step must consume the exact hourly artifact trio and target
    ui/dashboard.html (runner workspace) so validate_coherent_publish runs
    its PRD-118 coherence and PRD-119 freshness checks against fresh data,
    then mirror the publish copy contract (cp + cmp to ui/index.html).
    """

    text = _preview_workflow_text()
    render_step = text[text.index("- name: Render through the publish gates"):]
    render_step = render_step[: render_step.index("- name: Report size delta")]

    for anchor in (
        "--payload logs/latest_hourly_payload.json",
        "--run logs/latest_hourly_run.json",
        "--market-map-path logs/latest_hourly_market_map.json",
        "--output ui/dashboard.html",
        "cp ui/dashboard.html ui/index.html",
        "cmp ui/dashboard.html ui/index.html",
    ):
        assert anchor in render_step, (
            f"missing anchor in dashboard_preview.yml render step: "
            f"{anchor!r} (PRD-178 R4 render parity with hourly_alert.yml)."
        )


def test_preview_workflow_freshness_check_precedes_render() -> None:
    """PRD-178 R5 — the fail-hard freshness check runs before the render.

    A preview that renders without proving a fresh fetch silently shows
    whatever data is checked in at the ref — the exact failure mode this
    workflow exists to eliminate.
    """

    text = _preview_workflow_text()
    assert text.index("- name: Require fresh payload") < text.index(
        "- name: Render through the publish gates"
    ), (
        "dashboard_preview.yml renders before the Require fresh payload "
        "step; the freshness check must gate the render (PRD-178 R5)."
    )


# --- PRD-194 R7 — production publish decoupling (publish branch) -------------
#
# Pin the invariants that keep `main` protected and the scoreboard accumulating:
# the push helper targets the publish branch (never main), delta-appends the audit
# log, and retries on a non-fast-forward (the cross-workflow publish-race mechanism
# that replaced the shared concurrency lock — Codex P2); the state-writers do NOT
# share one concurrency group; each restores its read-back state before running;
# Pages deploys the publish branch via workflow_run on all three writers (a
# GITHUB_TOKEN push cannot fire on:push).

PUBLISH_STATE_WRITERS = ("cuttingboard.yml", "hourly_alert.yml", "macro_awareness.yml")
PUBLISH_WRITER_WORKFLOW_NAMES = (
    "Cuttingboard Pipeline",
    "Cuttingboard Hourly Alert",
    "Cuttingboard Macro-Awareness Producer",
)


def _workflow_text(name: str) -> str:
    return (REPO_ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")


def test_push_helper_targets_publish_branch_not_main() -> None:
    text = (REPO_ROOT / "tools" / "ci_push_artifacts.sh").read_text(encoding="utf-8")
    assert "PUBLISH_BRANCH" in text
    assert "refs/heads/$PUBLISH_BRANCH" in text
    assert "HEAD:main" not in text, "publish helper still pushes to main (PRD-194 R1)"
    assert "origin main" not in text, "publish helper still references origin main"


def test_push_helper_delta_appends_audit_never_clobbers() -> None:
    text = (REPO_ROOT / "tools" / "ci_push_artifacts.sh").read_text(encoding="utf-8")
    assert 'AUDIT_PATH="logs/audit.jsonl"' in text
    # The audit log is delta-appended from the restore-time base, not overwritten.
    assert "CB_PUBLISH_BASE_SHA" in text
    assert "tail -n +" in text, "audit.jsonl must be delta-appended (PRD-194 hard req)"


def test_push_helper_syncs_static_ui_but_not_generated_pages() -> None:
    # PRD-194 (Codex P2): static ui/ assets (app.js, styles.css, themes/*) change on
    # main via PR and are NOT in the per-run artifact diff, so the helper syncs them
    # from POST_SHA. BUT the generated pages (dashboard/index/contract) must be
    # EXCLUDED from that sync, else a macro-only publish (which renders nothing and
    # checks out main's FROZEN pages) would clobber publish's fresh dashboard.
    text = (REPO_ROOT / "tools" / "ci_push_artifacts.sh").read_text(encoding="utf-8")
    assert 'git ls-tree -r --name-only "$post_sha" -- ui' in text, (
        "push helper must sync static ui/ assets from POST_SHA (Codex P2)."
    )
    assert "ui/dashboard.html|ui/index.html|ui/contract.json" in text, (
        "push helper must EXCLUDE the generated pages from the static ui/ sync so a "
        "macro-only publish can't overwrite publish's fresh dashboard (Codex P2)."
    )


def test_push_helper_retries_on_non_fast_forward() -> None:
    # PRD-194 R5 (Codex P2): cross-workflow publish races are handled by a bounded
    # retry in the push helper, NOT a shared concurrency lock that over-serialized
    # the hourly alert. On a non-fast-forward the helper re-applies this run's delta
    # onto the moved tip and re-pushes.
    text = (REPO_ROOT / "tools" / "ci_push_artifacts.sh").read_text(encoding="utf-8")
    assert "non-fast-forward" in text, "push helper must detect a non-fast-forward"
    assert "MAX_ATTEMPTS" in text, "push helper must bound its retry attempts"


def test_state_writers_do_not_share_one_concurrency_lock() -> None:
    # PRD-194 R5 (Codex P2): a shared cb-publish group serialized the entire hourly
    # alert job behind the pipeline/macro producer and could drop a time-sensitive
    # alert. Each writer keeps its OWN per-workflow group instead.
    expected = {
        "cuttingboard.yml": "group: cuttingboard-pipeline",
        "hourly_alert.yml": "group: hourly-alert",
        "macro_awareness.yml": "group: macro-awareness",
    }
    for wf, group in expected.items():
        text = _workflow_text(wf)
        assert "group: cb-publish" not in text, (
            f"{wf} still shares the cb-publish lock; that over-serializes the hourly "
            "alert (Codex P2). Publish races are handled by the push-helper retry."
        )
        assert group in text, f"{wf} should keep its own per-workflow group ({group})"


def test_hourly_restores_dedup_slot_and_aggregates_before_render() -> None:
    # PRD-194 (Codex P1): the hourly alert reads last_hourly_slot.json (dedup) and
    # renders the scoreboard from regime_history.jsonl. With main frozen post-
    # decoupling, the dedup slot must be restored from publish, and the regime
    # aggregate (a full rebuild from audit) must run BEFORE the render so the
    # scoreboard is current rather than main's frozen copy.
    text = _workflow_text("hourly_alert.yml")
    assert (
        "ci_restore_publish_state.sh logs/audit.jsonl logs/last_hourly_slot.json" in text
    ), (
        "hourly must restore logs/last_hourly_slot.json from publish, or the 06:05 "
        "backup cron re-sends the 06:00 alert (Codex P1)."
    )
    assert text.index("- name: Aggregate regime history") < text.index(
        "- name: Render and stage hourly artifacts"
    ), (
        "hourly must aggregate regime_history BEFORE rendering so the dashboard "
        "scoreboard reflects this run, not main's frozen history (Codex P1)."
    )


def test_pipeline_restores_dedup_and_evaluation_state() -> None:
    # PRD-194: the pipeline's complete accumulated/read-back set on publish, beyond
    # audit.jsonl (verified by sweeping every logs/ read, not just *_PATH names):
    #   - last_notification_state.json: notification dedup (load_last_state ->
    #     should_send); without it the next run re-sends an unchanged LOW/MEDIUM alert.
    #   - evaluation.jsonl: append-only post-trade evaluation log; without restore it
    #     resets to this run's records each pipeline run (data loss).
    text = _workflow_text("cuttingboard.yml")
    for path in ("logs/last_notification_state.json", "logs/evaluation.jsonl"):
        assert path in text, (
            f"the pipeline must restore {path} from publish, or its accumulated "
            "state is lost/stale against main's frozen copy."
        )


def test_state_writers_restore_publish_state_before_running() -> None:
    for wf in PUBLISH_STATE_WRITERS:
        assert "tools/ci_restore_publish_state.sh" in _workflow_text(wf), (
            f"{wf} does not restore state from the publish branch (PRD-194 R3); "
            "it would append onto main's frozen copy and re-freeze the scoreboard."
        )


def test_no_state_writer_pushes_to_main() -> None:
    for wf in PUBLISH_STATE_WRITERS:
        assert "HEAD:main" not in _workflow_text(wf), (
            f"{wf} pushes to main; PRD-194 R1 requires all artifact publishing to "
            "target the unprotected publish branch."
        )


def test_state_writers_pin_checkout_to_main() -> None:
    # PRD-194 (Codex P1): with publishing now targeting the UNPROTECTED publish
    # branch, a workflow_dispatch from a feature branch must NOT be able to run
    # that branch's code and publish it to production. All three state-writers pin
    # the checkout to main (scheduled runs already run on main).
    for wf in PUBLISH_STATE_WRITERS:
        assert "ref: main" in _workflow_text(wf), (
            f"{wf} does not pin its checkout to `ref: main`; an unpinned dispatch "
            "on a feature branch would publish that branch's output to the "
            "unprotected publish branch (PRD-194 P1)."
        )


def test_pages_deploys_publish_branch_via_workflow_run_for_all_writers() -> None:
    text = _workflow_text("pages.yml")
    assert "ref: publish" in text, "pages.yml must deploy the publish branch (PRD-194 R2)"
    for name in PUBLISH_WRITER_WORKFLOW_NAMES:
        assert name in text, (
            f"pages.yml workflow_run is missing {name!r}; a GITHUB_TOKEN push to "
            "publish cannot fire on:push, so all three writers must be listed "
            "(PRD-194 Amendment 2)."
        )
    assert "branches: [main]" not in text, (
        "pages.yml still triggers on push to main; main no longer carries "
        "published artifacts (PRD-194 Amendment 2)."
    )
