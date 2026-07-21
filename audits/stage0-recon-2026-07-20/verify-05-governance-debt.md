# Verification — Track E: stage0-05-governance-debt-v0.1.md (Q22-28)

Verifier: separate fresh-context Claude Code session (see
`verify-00-disposition-index.md` for capability header). Verified against
this worktree's HEAD, source-tree-identical to the pinned SHA
`771f730839b00b0537327f9696210275f36cd790`, plus one cross-commit claim at
`bc64c99ade80c585086e73fe132442931e724f92` (an unmerged branch tip, checked
via `git show`, not by checking out).

## RUNTIME claim independently re-run

The artifact claims `python3 tools/validate_prd_registry.py --skip-commit-resolvability`
passed at the pin. I ran it myself in this worktree (source-identical to the
pin, confirmed via the diff-stat check in the index file):

```
$ python3 tools/validate_prd_registry.py --skip-commit-resolvability
PRD registry validation passed
```

**Disposition: CONFIRMED / REPRODUCED**, independently re-run, not accepted
from the artifact's say-so.

## Per-question disposition

- **Q22 (PRD-264 status) — CONFIRMED.**
  - `docs/prd_history/PRD-264.md:1-3` — `Status: IN PROGRESS` confirmed
    verbatim.
  - `docs/PRD_REGISTRY.md:284` — row confirmed: `PRD-264 | — | ... | IN
    PROGRESS | ...`.
  - `docs/prd_index.json` PRD-264 entry — confirmed: `"status": "IN
    PROGRESS", "commit": null`.
  - `docs/PROJECT_STATE.md:8,177` — confirmed: "Active PRD: none in
    progress" plus the queue sentence naming PRD-264 as queued behind
    PRD-267, matching the claim that PROJECT_STATE treats it as queued
    rather than active.

- **Q23 (PRD-267 scaffold vs. authorship) — CONFIRMED.**
  - Confirmed via `ls docs/prd_history/`: no `PRD-267.md` exists at HEAD;
    registry/index both stop at PRD-266.
  - Cross-commit check at `bc64c99` (the named unmerged branch tip,
    `prd-267-coverage-reason-surfacing`): `git show bc64c99:docs/prd_history/PRD-267.md`
    confirms the document exists there with `Status: IN PROGRESS`, a populated
    title and WHY NOW section, and every other section (`MAX EXPECTED DELTA`,
    `GOAL`, `SCOPE`, `OUT OF SCOPE`, `FILES`, `R1`, `DATA FLOW`, `FAIL
    CONDITIONS`, `VALIDATION`) literally reading `TODO` — matches the claim
    "only its title and WHY NOW are populated" exactly, checked by reading the
    actual document text at that commit, not inferred.
  - `git show bc64c99:docs/PRD_REGISTRY.md` and the index both confirm a
    PRD-267 row/entry exists at that commit — confirmed.
  - C2 formatter-attachment claim, checked directly:
    - `qualification.py:803-814` (`_check_regime_gates`) builds the long
      `STAY_FLAT posture (...)` reason string with the PRD-263 coverage
      clause appended — confirmed.
    - `output.py:882-893` (`_alert_reason`): confirmed the literal
      `[:80]` truncation on the returned reason string.
    - `output.py:966-974`: confirmed `Reason: {_alert_reason(...)}` is the
      rendered daily line.
    - `runtime/__init__.py:426` (`elif notify_mode in _HOURLY_MODES and
      regime.posture != "STAY_FLAT":`): confirmed qualification is only
      built when posture is NOT `STAY_FLAT` — so on `STAY_FLAT`,
      `qualification_summary` stays `None` going into the hourly formatter.
    - `notifications/__init__.py:245-260` (`_hourly_reason`): confirmed the
      `STAY_FLAT` fallback branch (`return "stay flat posture"`) only fires
      when `qualification_summary` is `None` — exactly the case the
      runtime.py:426 gate produces — confirmed the full causal chain, not
      just the two endpoints.
    - `notifications/__init__.py:543-560` (`format_hourly_notification`):
      confirmed `Reason: {reason}` is the rendered hourly line.

- **Q24 (`prd-second-model-commission` skill, queue clearance) — CONFIRMED.**
  - `find .claude/skills -maxdepth 1 -type d` lists exactly five skills
    (`session-handoff`, `scope-lock-precommit`, `prd-review-claude`,
    `prd-closeout-verified`, `prd-authoring-verified`) — no
    `prd-second-model-commission` — confirmed the skill does not exist in
    the tracked tree.
  - `docs/prd_history/PRD-266.md:64-70` — confirmed: lists the skill as
    "QUEUED BEHIND PRD-265, not built here," with the stated three-rule
    scope (independence conditions, trace-to-surface, memory-provenance).
  - `docs/PRD_PROCESS.md:316-318` — confirmed verbatim: "the commission
    prompt is authored ad-hoc — this doc is its source, there is no separate
    template file."
  - `docs/prd_history/PRD-265.md:214-229` — confirmed `STATUS: COMPLETE
    @ #154`, satisfying the "queue dependency is cleared" half of the claim.
  - `docs/PRD_REGISTRY.md` — confirmed PRD-265 row is `COMPLETE`.

- **Q25 (PRD-266 mechanical closeout unblocked) — CONFIRMED.**
  - `docs/PRD_PROCESS.md:86-103` (PRD-255 rule) — confirmed verbatim: the
    rule requires every allocated number below N to have a *landed doc* on
    main (any status suffices, COMPLETE not required) before N's closeout.
  - `docs/prd_history/PRD-264.md` exists at HEAD with a `Status:` line
    (`IN PROGRESS`, satisfies "any status suffices") — confirmed, satisfying
    the predicate for PRD-266 (266 > 264).
  - `docs/prd_index.json` shows `latest_complete` tracks the actual highest
    COMPLETE number — and I independently re-ran the validator (above),
    which passed, confirming no currently-broken invariant blocks this.
  - `scripts/prd_close.sh` — confirmed present (not individually diffed
    line-by-line against the cited 149-180/200-314 range, but its existence
    and general closeout-mechanics role are not in dispute here).

- **Q26 (stale #153/#154 PROJECT_STATE line) — CONFIRMED.**
  - `docs/PROJECT_STATE.md:177` — confirmed verbatim: "Held PRs for Dustin's
    manual merge: #153 (PRD-266 governance bundle) and #154 (PRD-265)."
  - Confirmed independently via `git log`: commit `bc0a82b` ("PRD-266:
    governance bundle... (#153)") and commit `771f730` ("PRD-265: coverage
    marker... (#154)", = the pin itself) are both already in this worktree's
    ancestry at HEAD — i.e. both PRs the sentence calls "held" are in fact
    already merged. The sentence is stale, exactly as claimed.

- **Q27 (model-role lane trigger) — CONFIRMED.**
  - `docs/PRD_PROCESS.md:176-220` — confirmed the lane's two-condition
    trigger (five full completions, or a first drafting defect) and its
    PROVISIONAL status.
  - `docs/prd_history/PRD-265.md:214-220` — confirmed verbatim: "This is a
    PARTIAL lane run: this seat drafted, so it does NOT count toward the
    five-PRD graduation trigger."
  - `docs/DECISIONS.md:19-32` — confirmed the 2026-07-19 "a model may not be
    the second-model reviewer of a PRD it drafted" ruling, recorded
    independently of the lane's own retirement status.

- **Q28 (no single operator-side reconciliation protocol) — CONFIRMED.**
  - `docs/knowledge_systems.md:35-54` — confirmed: describes Obsidian as
    the pre-PRD human strategic-cognition space ("PRD ideation: drafting and
    refining PRD candidates before they are formalized into
    docs/prd_history/"), supporting the "human strategic decisions precede
    PRDs" characterization.
  - `CLAUDE.md:247-264` — confirmed verbatim as the Alignment-check
    mechanism (phase-boundary diff-read, DECISIONS.md line per run).
  - `docs/PRD_PROCESS.md:119-126` ("Starting a New PRD") — confirmed; this
    section is a single-PRD authoring checklist, not a five-track
    cross-artifact reconciliation protocol, supporting the claim that no
    such protocol currently exists.

## Assessment

Every STATIC citation checked — including one cross-commit citation at an
unmerged branch tip (`bc64c99`), verified via `git show` rather than trusted
from the artifact's paraphrase — matches the described content exactly. The
one RUNTIME claim in this track was independently re-executed with an
identical result. The C2 formatter-attachment sub-claim under Q23 was
traced through its full causal chain (the runtime.py:426 gate producing the
exact `qualification_summary is None` condition that `_hourly_reason`
branches on), not just checked at its two endpoints.

**Disposition: CONFIRMED across Q22-28. Nothing falsified or narrowed.**
