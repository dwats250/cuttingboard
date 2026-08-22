# GEX-3 -- Best-effort free hourly GEX refresh: MATERIAL design packet

Date: 2026-08-22 (revision 2 -- post-Event-1 consolidated correction)
Author: Claude Code (authoring session; GOV-2 packet author)
Base inspected: `main` @ `ed53df372ab355b0fd3f36ce7c8d604c9310a276`
Status: CORRECTED -- awaiting GOV-2 Event-2 exact-corrected-head confirmation.
Event-1 (INITIAL PACKET REVIEW, Codex): DESIGN INCOMPLETE @ `a718cf2`, 5
findings, durable record `GEX_3_EVENT_1_CODEX_REVIEW_2026-08-22.md` in this
directory. All five findings are absorbed below; see CORRECTION CYCLE.

## sec0 -- Intake classification (GOV-2 sec1)

MATERIAL -- ruled by Dustin 2026-08-22, sustaining Codex F1 of
`docs/prd_history/PRD-310.review.codex.md` (frozen PR #269). Decisive
triggers, per the owner adjudication (NOT the pathological any-ceiling
reading, which the owner explicitly rejected):

1. The slice selects a NEW cadence carrier/seam in
   `.github/workflows/hourly_alert.yml` joining the existing GEX producer to
   the existing dashboard/publish path.
2. The resulting seam crosses multiple GOV-2 layers: at minimum
   delivery + dashboard + persistence.
3. GEX-2's prior MATERIAL authority
   (`audits/gex-2-free-board-card-2026-08/`, PR #266) expressly excluded
   workflow/cadence changes, so no existing packet authorizes this carrier.

Consequences: ineligible for LANE MICRO; the downstream PRD rides
HIGH-RISK / INFRA (workflow payload forces the lane mechanically). This
packet is the required upstream authority; the GOV-2 order (packet review ->
correction -> exact-head confirmation -> design-direction ruling -> PRD
redraft -> independent PRD review -> Gate A) governs everything downstream.

## sec1 -- Authority

- Owner GEX-3 product charge (2026-08-21): target shape
  `hourly_alert.yml -> best-effort refresh of logs/gex_snapshot.json ->
  existing dashboard_renderer -> existing hourly publish`; GEX MUST NOT
  become a dependency of the normal hourly board.
- Owner adjudication (2026-08-22): MATERIAL sustained; Gate A WITHHELD;
  PR #269 / PRD-310 FROZEN (no merge, no implementation, no polish); this
  packet proceeds from current `main`, reusing Stage-0 evidence without
  broad re-recon.
- This packet grants NO implementation authority; PRD-310 is NOT redrafted
  until the design-direction ruling.

## sec2 -- Objective (the bounded design question, verbatim scope)

Can the existing `hourly_alert.yml` carry a best-effort, run-local GEX
refresh such that: successful Cboe refresh -> fresh artifact available to
the existing renderer for that hourly board; ordinary provider/producer
failure after a successful initial scrub -> artifact absent, refresh step
successful, normal hourly publish continues without GEX; inability to
establish GEX absence -> fail closed as a local infrastructure failure; no
stale GEX artifact leaks forward; `gex_snapshot.json` is neither restored
nor staged/persisted; rendered HTML remains the durable output; no new
secret, dependency, workflow, cadence carrier, producer behavior, schema,
readiness dependency, or decision authority is introduced.

ANSWER (design conclusion): YES, with the sec4 step design (hard wall-clock
bound included), the sec5 producer-to-final-consumer inventory, and the
board-persistence semantics stated for owner acceptance in sec9 Q3. No
blocker; the two second-order dependencies (gitignore reliance, sec5 item
7h; last-writer/Pages persistence, sec5 part B) are named and guarded or
surfaced, not silent.

## sec3 -- Work type and preflight

Work type: MATERIAL design packet (docs-only; this branch mutates only
`audits/gex-3-hourly-refresh-2026-08/`).

Preflight evidence: Stage-0 recon (2026-08-22, base `ed53df3`) plus the
PRD-310 Codex review findings, RE-VERIFIED against `main` @ `ed53df3`:

- E1 `git ls-files logs/gex_snapshot.json` -> 0 (untracked on main).
- E2 `git cat-file -e origin/publish:logs/gex_snapshot.json` -> ABSENT.
- E3 Restore step (`hourly_alert.yml:90`) restores exactly: audit.jsonl,
  last_hourly_slot.json, latest_hourly_market_map.json, latest_run.json,
  macro_drivers_snapshot.json, regime_history.jsonl, 'logs/run_*.json'.
  gex_snapshot.json is NOT restored.
- E4 The "Commit hourly artifacts" explicit `git add` set contains no gex
  token.
- E5 `git check-ignore -v logs/gex_snapshot.json` -> `.gitignore:49:logs/`
  (`logs/gex_snapshot.json.tmp` is covered by the same directory rule).
- E6 `tools/ci_push_artifacts.sh:54` derives the publish delta from
  `git diff --name-only PRE_SHA POST_SHA` (committed paths only) and aborts
  on a dirty tree (`:41-47`); overlay + force-add happen inside an isolated
  publish worktree the runner workspace never enters; the bootstrap path
  pushes `POST_SHA` (a commit, which cannot carry the unstaged artifact).
- E7 Renderer suppression is already tested:
  `tests/test_dashboard_renderer.py:4497 test_gex_absent_baseline_identical`
  (byte-identical baseline on absent/stale/invalid; PRD-309 golden).
- E8 Producer contract (`tools/gex_snapshot.py`): the CLI path returns 0
  ONLY after a successful atomic write (`os.replace`), and returns 1 on
  operational/provider/validation/ordinary-Exception failures. (A naive
  injected `now` raises ValueError as a programming-error precondition
  before the catch block -- unreachable from the CLI, which never passes
  `now`.) An interrupted or failed temp write can leave
  `logs/gex_snapshot.json.tmp`, which no consumer reads; the sec4 design
  scrubs it explicitly anyway.
- E9 The producer's internal `urlopen(timeout=15)` bounds each BLOCKING
  socket operation, not end-to-end wall clock; a drip-feeding or repeatedly
  stalling connection can extend a run arbitrarily. The refresh step
  therefore needs its own hard wall-clock bound (sec4; Event-1 F2).
- GEX-2 live smoke test (owner-run, 2026-08-21): free keyless producer
  succeeded on the real runner; rendered card matched the artifact;
  artifact-absent render differed by exactly the card block. Owner-attested
  product evidence, not repository evidence.

## sec4 -- Design: the refresh step

Exact insertion: one new step in `.github/workflows/hourly_alert.yml`,
after "Aggregate regime history", before "Render and stage hourly
artifacts", gated identically to the render step:

```yaml
      # GEX-3: best-effort, run-local GEX refresh. Provider failure or
      # wall-clock expiry degrades to GEX absence (renderer suppresses the
      # card); it must never fail the hourly publish. rm failures fail
      # CLOSED: absence we cannot establish is a local infrastructure
      # failure, not a degrade.
      - name: Refresh GEX snapshot (best-effort)
        if: ${{ success() && steps.freshcheck.outputs.fresh == 'true' }}
        run: |
          rm -f logs/gex_snapshot.json logs/gex_snapshot.json.tmp
          timeout 120 python3 tools/gex_snapshot.py \
            || rm -f logs/gex_snapshot.json logs/gex_snapshot.json.tmp
```

The hard wall-clock bound is coreutils `timeout` (present on ubuntu-latest;
no new dependency): expiry kills the producer (exit 124, SIGKILL escalation
137 -- both nonzero), which routes through the SAME `||` cleanup as any
producer failure, so a hang degrades to absence with the step green. The
120-second value is the packet recommendation; the duration is
owner-selectable at the design ruling (sec9 Q2). A GitHub `timeout-minutes`
alone was rejected: runner cancellation bypasses the shell cleanup and
fails the step (Event-1 F2).

Outcome table (exhaustive under the Actions default `bash -e {0}` shell;
`||` exempts the producer line from errexit):

| Case | Behavior | Board result |
|---|---|---|
| Producer exit 0 within bound | fresh atomic artifact present | card renders from THIS run's observation |
| Producer nonzero OR wall-clock expiry; cleanup rm works | final + .tmp absent, step exit 0 | baseline board publishes without GEX |
| Initial scrub rm fails | step fails CLOSED before invoking producer | hourly run fails loudly (local infra fault) |
| Cleanup rm fails after producer failure | step fails CLOSED | hourly run fails loudly (PRD-198 invariant 1: never certify an absence you cannot establish; no `\|\| true` anywhere) |

Why each owner DO-NOT holds by construction: no cuttingboard.yml or new
workflow touch (single-step insertion in the existing hourly carrier); no
readiness coupling (`scripts/check_readiness.py` has zero GEX references);
no secrets or dependencies (keyless GET, stdlib producer, coreutils
timeout); no producer BEHAVIOR/schema/card change (the step invokes the
existing tool with defaults; the docstring truth edit in sec7 is
non-behavioral); no decision coupling (the card is PRD-309's reviewed
display-only surface, activated by data presence alone); Aggregate-before-
Render ordering is preserved across the insertion.

## sec5 -- Seam trace (complete producer-to-final-consumer inventory)

PART A -- the hourly job (the only writer of the artifact), in step order:

1. Checkout (`ref: main`): artifact untracked on main (E1) -> starts absent.
2. Restore step: not in the restore argument list (E3) -> stays absent.
3. Aggregate: writes `logs/regime_history.jsonl` only; disjoint.
4. NEW refresh step (sec4): sole writer; scrub-first guarantees no
   inherited final or .tmp copy survives without a fresh successful write
   in THIS run.
5. Render: `dashboard_renderer` performs the EXISTING optional read
   (`gex_card.load_gex_snapshot`); a present, fresh, valid, in-domain
   artifact -> card block; absent, malformed, stale, or out-of-domain ->
   suppressed to the byte-identical baseline (E7; `gex_card.py` validation
   + staleness gates).
6. Readiness / commit: readiness reads no GEX; commit stages the explicit
   list only (E4) -> the artifact is never committed; the rendered
   `ui/dashboard.html` in the commit is the durable output.
7. Push (`ci_push_artifacts.sh`): publish delta = committed
   `PRE_SHA..POST_SHA` paths in an isolated worktree; worktree `add -f
   logs` cannot see the runner workspace; bootstrap pushes `POST_SHA` (E6).
   (7h) The dirty-tree abort (`:41-47`) never sees the artifact ONLY
   BECAUSE `logs/` is gitignored (E5) -- a REAL PUBLISH-SAFETY DEPENDENCY,
   guarded by discriminating test DR4(h) for BOTH the final and .tmp paths.
8. Failure-artifact upload (`failure()` step): does not list the artifact.
9. Next hourly run repeats 1-8 from scratch: no restore, no commit, no
   publish copy -> no reuse channel for the artifact itself.

PART B -- every OTHER workflow and the final consumer (Event-1 F1):

10. `cuttingboard.yml` (pipeline): invokes the SAME renderer with no GEX
    refresh -> its `ui/dashboard.html` is a GEX-ABSENT render; its Commit
    artifacts step broad-stages `git add -f logs/` (`:526-527`), which is
    inert for GEX only because NOTHING on the pipeline runner produces the
    artifact -- guarded by DR6 (no workflow other than hourly_alert.yml may
    invoke `tools/gex_snapshot.py`); a violation would force-commit the
    artifact past gitignore.
11. `macro_awareness.yml`: publishes through the same helper; generated
    pages outside its committed delta are PRESERVED on publish
    (`ci_push_artifacts.sh` overlay excludes dashboard/index/contract not
    in the delta) -> a macro publish neither adds nor removes GEX HTML.
12. `dashboard_preview.yml`: sanctioned ephemeral render/upload; never
    committed or deployed; no GEX refresh there -> previews render
    GEX-absent; acceptable and out of scope.
13. `pages.yml`: deploys the publish branch `ui/` tree via `workflow_run`
    on COMPLETED runs of all three writers -- including FAILED runs -> a
    failed hourly run redeploys the PRIOR publish tree unchanged.
14. LAST-WRITER SEMANTICS (the persistence consequence, for owner
    acceptance in sec9 Q3): GEX appears on the live board only in HTML
    rendered by an hourly run whose refresh succeeded; ANY later pipeline
    publish REPLACES it with a GEX-absent render; a previously published
    GEX-bearing HTML PERSISTS on the live site (through macro publishes and
    failed/suppressed runs) until the next successful render replaces it.
    The embedded "as of HH:MM ET" label keeps the displayed observation
    honestly timestamped; `gex_card` staleness gating bounds how old a
    RENDER-TIME artifact can be, not how long rendered HTML persists --
    identical to every other card on the board.

Layer crossing acknowledged (the MATERIAL trigger): the step joins the
producer (sidecar tool) to delivery (workflow orchestration), dashboard
(existing optional read), and persistence (rendered HTML in the publish
commit; Pages deploy) -- every crossing except the new step itself is an
EXISTING reviewed surface consumed without modification.

## sec6 -- Requirements and discriminating tests (design-stage; binds the
future PRD, not the tree)

DR1 Insertion/gating: the step exists, named "Refresh GEX snapshot
(best-effort)", after Aggregate, before Render, gated
`success() && steps.freshcheck.outputs.fresh == 'true'`.
DR2 Bounded best-effort semantics: exactly the sec4 body (hard wall-clock
`timeout`, both-path scrubs, no `|| true`); outcomes per the sec4 table.
DR3 Run-local artifact: never restored, never staged, never persisted;
`logs/` gitignore reliance stated as an invariant covering final AND .tmp.
DR4 Structural guard tests in `tests/test_ci_artifact_hygiene.py`, scoped
to the named step block, the exact restore line, and the "Commit hourly
artifacts" add block; mutation-red set (each proven red one at a time):
(a) delete the step; (b) move it after render; (c) remove the fresh gate;
(d) remove the pre-invocation scrub; (e) remove the failure-side `|| rm`;
(f) add the artifact to the restore arguments; (g) add it to the commit add
block; (h) drop `logs/` gitignore coverage (`git check-ignore` stops
succeeding for EITHER `logs/gex_snapshot.json` or
`logs/gex_snapshot.json.tmp`); (i) remove or lengthen-past-ceiling the
`timeout` bound; (j) drop the .tmp path from either scrub.
DR5 Shell-behavior harness (executable, not structural): extract the step
body verbatim from the workflow YAML and run it in bash with a stubbed
producer and controlled PATH/permissions, asserting each terminal outcome
of the sec4 table: (1) success -> artifact present, exit 0; (2) producer
nonzero -> artifact+tmp absent, exit 0; (3) producer hang past the bound ->
killed, artifact+tmp absent, exit 0; (4) initial scrub failure -> nonzero
before producer invocation; (5) cleanup failure after producer failure ->
nonzero. Each asserted against the extracted body so workflow drift cannot
decouple the harness from the shipped step.
DR6 Cross-workflow scan guards: no workflow other than
`hourly_alert.yml` invokes `tools/gex_snapshot.py`; no workflow restores or
stages any `gex_snapshot` path; the existing all-writers Pages guard
(`test_ci_artifact_hygiene.py:648-660` style) remains intact.

## sec7 -- FILES cone (provisional -- ESTIMATED SURFACE, NOT YET APPROVED)

- M `.github/workflows/hourly_alert.yml` (the single inserted step)
- M `tests/test_ci_artifact_hygiene.py` (append-only guard tests + harness)
- M `tools/gex_snapshot.py` (docstring/CLI-description TRUTH-ONLY edit:
  "No cadence, no workflow" and "manual local inspection" become false
  under sec4; zero behavioral change -- Event-1 F4)
- M `docs/artifact_flow_map.md` (writer/carrier truth update: hourly
  best-effort CI cadence joins the manual path -- Event-1 F4)
- MATERIAL packet/review records under `audits/gex-3-hourly-refresh-2026-08/`
- Lifecycle docs only as actually required (PRD doc, workplan GEX-3 ledger
  row, PROJECT_STATE pointer; registry/index implicit per Scope Lock)

## sec8 -- Change-surface ceiling (provisional, GOV-2 sec5)

Approximately <= 14 added workflow lines (zero modified/removed elsewhere
in `hourly_alert.yml`); approximately <= 120 test lines (structural guards
+ shell harness); <= 10 comment/docstring/doc truth lines across
`tools/gex_snapshot.py` + `docs/artifact_flow_map.md` (non-behavioral);
zero new dependencies / secrets / workflows; zero behavioral Python
changes. The first BINDING ceiling is set at Gate A on the reviewed PRD.

## sec9 -- Open design questions for the design-direction ruling

Q1 Fate of frozen PR #269 / PRD-310: redraft PRD-310 in place on its
existing branch/PR (preserving the recorded dispute + review lineage), or
close #269 and open a fresh PRD from the review-clean packet? Packet
recommendation: redraft in place.
Q2 Hard wall-clock bound for the refresh step (Event-1 F2): the design
requires an owner-selected duration for the coreutils `timeout` wrapper,
with expiry routed through the ordinary cleanup path. Packet
recommendation: 120 seconds (8x the per-operation socket timeout; well
under the hourly slot spacing).
Q3 Board persistence semantics (Event-1 answer 7): explicitly accept the
last-writer behavior in sec5 item 14 -- GEX visibility is hourly-render
transient; pipeline publishes replace it with GEX-absent HTML; previously
published GEX-bearing HTML persists through failed/suppressed runs until
the next successful render replaces it. Packet recommendation: accept --
this is the existing board-wide persistence model, and the "as of" label
keeps it honest.

## sec10 -- Review (GOV-2 packet cycle)

- Event-1 INITIAL PACKET REVIEW: COMPLETE -- Codex, fresh context,
  read-only, DESIGN INCOMPLETE @ `a718cf2`, 5 findings. Durable record:
  `GEX_3_EVENT_1_CODEX_REVIEW_2026-08-22.md`.
- ONE consolidated author correction: THIS revision (see CORRECTION CYCLE).
- Event-2 EXACT-CORRECTED-HEAD CONFIRMATION: Codex confirms F1-F5 are
  resolved at the exact corrected head SHA (confirmation, not fresh-scope
  review). Durable record: `GEX_3_EVENT_2_CONFIRMATION_2026-08-22.md`.
- The prior Codex PRD review of PRD-310 (REJECT @ ab56d11) does NOT
  substitute for either event; its F2/F3 substance is absorbed here.

## sec11 -- Validation, landing, stop conditions

- Landing: this packet + event records ride branch
  `claude/gex-3-material-packet` -> a DRAFT PR held for Dustin (GOV-0
  visible hold). Packet merge, design ruling, PRD redraft, PRD review, and
  Gate A are all Dustin-held.
- Stop conditions: an Event-2 finding naming a NEW material boundary
  returns the packet to DESIGN INCOMPLETE; evidence contradicting
  sec3/sec5 stops the cycle for owner review; no implementation, no PRD
  redraft, no PR #269 modification.

## sec12 -- Reusable truths carried / assumptions discarded

Carried (re-verified E1-E8): artifact untracked/ignored; ignore status is a
publish-safety dependency (dirty-tree abort); not restored; not in the
hourly staging set; publish delta is committed-paths-only; producer writes
atomically and exits 0 only on success; renderer suppresses cleanly on
absence/staleness/invalidity; GEX-2 live smoke demonstrated baseline
neutrality; insertion only on the fresh hourly-payload publish path, before
rendering.
Discarded: "ANY failure leaves the step green" (scrub failure fails
closed); the first-draft NOT-MATERIAL classification (owner-overruled,
sec0); "the producer's internal 15s timeout bounds the step" (per-blocking-
operation only -- superseded by the sec4 hard wall-clock bound, Event-1 F2);
"the hourly job is the complete lifecycle" (superseded by the sec5 Part B
cross-workflow/final-consumer inventory, Event-1 F1).

## CORRECTION CYCLE (GOV-2 Event-1 -- single consolidated author
correction, 2026-08-22)

Event-1 verdict DESIGN INCOMPLETE @ `a718cf2`; all five findings ACCEPTED:

- F1 (HIGH, omitted cross-workflow/final-consumer boundary): sec5 rebuilt
  as a complete producer-to-final-consumer inventory (Part B items 10-14:
  cuttingboard.yml render-replacement + broad `git add -f logs/` carrier,
  macro preserve-behavior, dashboard_preview, pages.yml
  deploy-on-any-completion, last-writer persistence semantics); DR6 adds
  the cross-workflow scan guards; sec9 Q3 puts the persistence semantics to
  the owner explicitly.
- F2 (HIGH, no hard wall-clock bound): sec4 step now wraps the producer in
  coreutils `timeout` (owner-selectable duration, recommended 120s), expiry
  routed through the ordinary `||` cleanup so a hang degrades green; the
  four-outcome table replaces the three-outcome table; E9 records the
  urlopen-timeout limitation; step-level `timeout-minutes` alone rejected
  per the finding.
- F3 (MEDIUM, insufficient discriminating tests): DR5 adds the executable
  shell-behavior harness over the extracted step body (five terminal
  outcomes incl. hang); DR4 extends to mutations (i)/(j) and dual-path
  check-ignore in (h); DR6 adds global workflow scans; test ceiling raised
  to <= 120 lines in sec8.
- F4 (MEDIUM, FILES cone omits forced truth corrections): sec7 adds
  truth-only edits to `tools/gex_snapshot.py` (docstring/CLI description)
  and `docs/artifact_flow_map.md`; sec8 adds the <= 10 non-behavioral doc
  lines; explicitly NOT a producer behavior/schema/card change.
- F5 (LOW, precision): E8 narrowed (naive-clock ValueError is a
  pre-catch programming-error precondition, unreachable from the CLI);
  sec5 Part A ordering fixed (Aggregate item 3, Refresh item 4); sec5 item
  5 now says "present, fresh, valid, in-domain artifact" renders the card.

No new material boundary was introduced by this correction; the corrected
head SHA is recorded in the commit that carries this revision and is the
Event-2 confirmation target.
