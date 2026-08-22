# GEX-3 -- Best-effort free hourly GEX refresh: MATERIAL design packet

Date: 2026-08-22
Author: Claude Code (authoring session; GOV-2 packet author)
Base inspected: `main` @ `ed53df372ab355b0fd3f36ce7c8d604c9310a276`
Status: PROVISIONAL until Codex Event-1 review, one consolidated correction,
and Codex Event-2 exact-corrected-head confirmation complete (GOV-2 sec2).
Packet directory: `audits/gex-3-hourly-refresh-2026-08/` (event records land
here as separate committed files).

## sec0 -- Intake classification (GOV-2 sec1)

MATERIAL -- ruled by Dustin 2026-08-22, sustaining Codex F1 of
`docs/prd_history/PRD-310.review.codex.md` (on the frozen PRD-310 branch,
PR #269). Decisive triggers, per the owner adjudication (NOT the pathological
any-ceiling reading, which the owner explicitly rejected):

1. The slice selects a NEW cadence carrier/seam in
   `.github/workflows/hourly_alert.yml` joining the existing GEX producer to
   the existing dashboard/publish path.
2. The resulting seam crosses multiple GOV-2 layers: at minimum
   delivery + dashboard + persistence.
3. GEX-2's prior MATERIAL authority
   (`audits/gex-2-free-board-card-2026-08/`, PR #266) expressly excluded
   workflow/cadence changes, so no existing packet authorizes this carrier.

Consequences: ineligible for LANE MICRO; the downstream PRD rides
HIGH-RISK / INFRA (workflow payload forces the lane mechanically -- both
prior reviews concur). This packet is the required upstream authority; the
GOV-2 order (packet review -> correction -> exact-head confirmation ->
design-direction ruling -> PRD redraft -> independent PRD review -> Gate A)
governs everything downstream.

## sec1 -- Authority

- Owner GEX-3 product charge (2026-08-21): target shape
  `hourly_alert.yml -> best-effort refresh of logs/gex_snapshot.json ->
  existing dashboard_renderer -> existing hourly publish`; GEX MUST NOT
  become a dependency of the normal hourly board.
- Owner adjudication (2026-08-22): MATERIAL sustained; Gate A WITHHELD;
  PR #269 / PRD-310 FROZEN (no merge, no implementation, no polish); this
  packet proceeds from current `main`, reusing the Stage-0 evidence without
  broad re-recon.
- This packet grants NO implementation authority. It is design authority
  input only. PRD-310 is NOT redrafted until the design-direction ruling.

## sec2 -- Objective (the bounded design question, verbatim scope)

Can the existing `hourly_alert.yml` carry a best-effort, run-local GEX
refresh such that:

- successful Cboe refresh -> fresh artifact available to the existing
  renderer for that hourly board;
- ordinary provider/producer failure after a successful initial scrub ->
  artifact absent, refresh step successful, normal hourly publish continues
  without GEX;
- inability to establish GEX absence -> fail closed as a local
  infrastructure failure;
- no stale GEX artifact leaks forward;
- `gex_snapshot.json` is neither restored nor staged/persisted;
- rendered HTML remains the durable output;
- no new secret, dependency, workflow, cadence carrier, producer behavior,
  schema, readiness dependency, or decision authority is introduced.

ANSWER (design conclusion of this packet): YES, with the exact step design
in sec4 and the seam trace in sec5. No blocker was found; the one
second-order dependency (gitignore reliance, sec5 item 7) is named and
guarded rather than silent.

## sec3 -- Work type and preflight

Work type: MATERIAL design packet (docs-only; this branch mutates only
`audits/gex-3-hourly-refresh-2026-08/`). Mutation of source, contracts,
workflows, tests, and `main` is out of scope for the packet itself.

Preflight evidence: Stage-0 recon (2026-08-22, base `ed53df3`) plus the
PRD-310 Codex review findings, RE-VERIFIED against `main` @ `ed53df3` at
packet-authoring time:

- E1 `git ls-files logs/gex_snapshot.json` -> 0 (untracked on main).
- E2 `git cat-file -e origin/publish:logs/gex_snapshot.json` -> ABSENT.
- E3 Restore step (`hourly_alert.yml:90`) restores exactly: audit.jsonl,
  last_hourly_slot.json, latest_hourly_market_map.json, latest_run.json,
  macro_drivers_snapshot.json, regime_history.jsonl, 'logs/run_*.json'.
  gex_snapshot.json is NOT restored.
- E4 The "Commit hourly artifacts" explicit `git add` set contains no gex
  token (0 matches in the step block).
- E5 `git check-ignore -v logs/gex_snapshot.json` -> `.gitignore:49:logs/`.
- E6 `tools/ci_push_artifacts.sh:54` derives the publish delta from
  `git diff --name-only PRE_SHA POST_SHA` (committed paths only) and aborts
  on a dirty tree (`:41-47`); overlay + force-add happen inside an isolated
  publish worktree the runner workspace never enters.
- E7 Renderer suppression is already tested:
  `tests/test_dashboard_renderer.py:4497 test_gex_absent_baseline_identical`
  (byte-identical baseline on artifact absence; PRD-309 golden).
- E8 Producer contract (`tools/gex_snapshot.py:409-416`): returns 0 ONLY
  after a successful atomic write (`os.replace`), 1 on every failure class;
  a failed temp write can leave `logs/gex_snapshot.json.tmp`, which no
  consumer reads and no publish path can carry.
- GEX-2 live smoke test (owner-run, 2026-08-21): free keyless producer
  succeeded on the real runner; rendered card matched the artifact;
  artifact-absent render differed by exactly the card block; baseline
  neutrality demonstrated on the real renderer.

## sec4 -- Design: the refresh step

Exact insertion: one new step in `.github/workflows/hourly_alert.yml`,
after "Aggregate regime history", before "Render and stage hourly
artifacts", gated identically to the render step:

```yaml
      # GEX-3: best-effort, run-local GEX refresh. Provider failure degrades
      # to GEX absence (renderer suppresses the card); it must never fail the
      # hourly publish. rm failures fail CLOSED: absence we cannot establish
      # is a local infrastructure failure, not a degrade.
      - name: Refresh GEX snapshot (best-effort)
        if: ${{ success() && steps.freshcheck.outputs.fresh == 'true' }}
        run: |
          rm -f logs/gex_snapshot.json
          python3 tools/gex_snapshot.py || rm -f logs/gex_snapshot.json
```

Semantics (three exhaustive outcomes under the Actions default
`bash -e`-style shell):

| Case | Behavior | Board result |
|---|---|---|
| Producer exit 0 | fresh atomic artifact present | card renders from THIS run's observation |
| Producer nonzero, rm works | artifact absent, step exit 0 | baseline board publishes without GEX |
| Either `rm -f` fails | step fails CLOSED | hourly run fails loudly (local infra fault, PRD-198 invariant 1: never certify an absence you cannot establish; no `\|\| true` anywhere) |

Why each owner DO-NOT holds by construction: no cuttingboard.yml or new
workflow touch (single-step insertion in the existing hourly carrier); no
readiness coupling (`scripts/check_readiness.py` has zero GEX references and
is untouched); no secrets/dependencies (keyless GET, stdlib producer,
`pip install -e .` already present); no producer/schema/card change (the
step only invokes the existing tool with defaults); no decision coupling
(the card is PRD-309's reviewed display-only surface, activated by data
presence alone); ordering does not disturb Aggregate-before-Render (both
existing hygiene ordering asserts remain true across the insertion). The
producer's own 15s HTTP timeout bounds a hung fetch; no step-level timeout
is added (kept minimal; flagged as owner question Q2).

## sec5 -- Seam trace (complete artifact lifecycle across layers)

Every process that can touch `logs/gex_snapshot.json` on the hourly path,
with the evidence that each behaves correctly in both refresh outcomes:

1. Checkout (`ref: main`): artifact untracked on main (E1) -> starts absent.
2. Restore step: not in the restore argument list (E3) -> stays absent.
3. NEW refresh step (sec4): sole writer; scrub-first guarantees no
   inherited copy survives without a fresh successful write in THIS run.
4. Aggregate: writes `logs/regime_history.jsonl` only; disjoint.
5. Render: `dashboard_renderer` performs the EXISTING optional read
   (`gex_card.load_gex_snapshot`); absent/malformed -> None -> card
   suppressed (E7); present -> card block only. Delivery + dashboard layers
   consume without modification.
6. Readiness / commit: readiness reads no GEX; commit stages the explicit
   list only (E4) -> the artifact is never committed; the rendered
   `ui/dashboard.html` in the commit is the durable output (persistence
   layer carries HTML, never the artifact).
7. Push (`ci_push_artifacts.sh`): publish delta = committed
   `PRE_SHA..POST_SHA` paths built in an isolated worktree; the worktree
   `add -f logs` cannot see the runner workspace; the bootstrap path pushes
   `POST_SHA` (a commit, which cannot contain the unstaged artifact). The
   dirty-tree abort (`:41-47`) never sees the artifact ONLY BECAUSE `logs/`
   is gitignored (E5) -- this is a REAL PUBLISH-SAFETY DEPENDENCY of the
   design and is guarded by discriminating test (h) in sec6, not left
   implicit. (Codex F3 of the PRD-310 review, absorbed.)
8. Failure-artifact upload (workflow `failure()` step): does not list the
   artifact; irrelevant to success-path publishes.
9. Next hourly run: repeats 1-8 from scratch -- a fresh observation every
   run; no reuse channel exists (no restore, no commit, no publish copy).

Layer crossing acknowledged (the MATERIAL trigger): the step joins the
producer (sidecar tool) to delivery (workflow orchestration), dashboard
(existing optional read), and persistence (the rendered HTML in the publish
commit) -- but every crossing except the new step itself is an EXISTING
reviewed surface consumed without modification.

## sec6 -- Requirements and discriminating tests (design-stage; binds the
future PRD, not the tree)

DR1 Insertion/gating: the step exists, named "Refresh GEX snapshot
(best-effort)", after Aggregate, before Render, gated
`success() && steps.freshcheck.outputs.fresh == 'true'`.
DR2 Bounded best-effort semantics: exactly the sec4 body; outcomes per the
sec4 table; no `|| true`.
DR3 Run-local artifact: never restored, never staged, never persisted;
`logs/` gitignore reliance stated as an invariant.
DR4 Guard tests in `tests/test_ci_artifact_hygiene.py`, scoped to the named
step block, the exact restore line, and the "Commit hourly artifacts" add
block; mutation-red set (each proven red one at a time during
implementation): (a) delete the step; (b) move it after render; (c) remove
the fresh gate; (d) remove the pre-invocation rm; (e) remove the failure-
side `|| rm -f`; (f) add the artifact to the restore arguments; (g) add it
to the commit add block; (h) drop `logs/` gitignore coverage
(`git check-ignore logs/gex_snapshot.json` stops succeeding).

## sec7 -- FILES cone (provisional -- ESTIMATED SURFACE, NOT YET APPROVED)

- M `.github/workflows/hourly_alert.yml` (the single inserted step)
- M `tests/test_ci_artifact_hygiene.py` (append-only guard tests)
- MATERIAL packet/review records under `audits/gex-3-hourly-refresh-2026-08/`
- Lifecycle docs only as actually required (PRD doc, workplan GEX-3 ledger
  row, PROJECT_STATE pointer; registry/index implicit per Scope Lock)

## sec8 -- Change-surface ceiling (provisional, GOV-2 sec5)

Approximately <= 12 added workflow lines (zero modified/removed elsewhere in
`hourly_alert.yml`); approximately <= 60 test lines; zero new
dependencies / secrets / workflows / Python production changes. The first
BINDING ceiling is set at Gate A on the reviewed PRD (GOV-2 sec5).

## sec9 -- Open design questions for the design-direction ruling

Q1 Fate of frozen PR #269 / PRD-310: after the ruling, redraft PRD-310 in
place on its existing branch/PR (preserving the recorded dispute + review
lineage), or close #269 and open a fresh PRD from the review-clean packet?
Packet recommendation: redraft in place -- the dispute record and Codex
artifact are part of this slice's honest history.
Q2 Step timeout: rely on the producer's internal 15s HTTP timeout only
(packet default), or add `timeout-minutes` to the step? Packet
recommendation: no step timeout -- smallest diff; the producer cannot hang
past its socket timeout.

## sec10 -- Review (GOV-2 packet cycle)

- Event-1 INITIAL PACKET REVIEW: Codex, fresh context, read-only sandbox
  (`codex exec -s read-only`, prompt via stdin), reviewing this packet and
  the underlying repository surfaces at the exact packet SHA. Durable
  record: `GEX_3_EVENT_1_CODEX_REVIEW_2026-08-22.md` in this directory.
- ONE consolidated author correction; revision log appended to this packet.
- Event-2 EXACT-CORRECTED-HEAD CONFIRMATION: Codex confirms the enumerated
  Event-1 findings are resolved at the exact corrected head SHA
  (confirmation, not fresh-scope review). Durable record:
  `GEX_3_EVENT_2_CONFIRMATION_2026-08-22.md`.
- The prior Codex PRD review of PRD-310 (REJECT @ ab56d11) does NOT
  substitute for either event; its F2/F3/F4 substance is absorbed into
  sec4-sec6.

## sec11 -- Validation, landing, stop conditions

- Landing: this packet and its event records ride branch
  `claude/gex-3-material-packet` -> a DRAFT PR held for Dustin (GOV-0
  visible hold). The packet PR merge, the design-direction ruling, the PRD
  redraft, its independent review, and Gate A are all Dustin-held.
- Stop conditions: any Event finding that names a new MATERIAL boundary
  returns the packet to DESIGN INCOMPLETE (GOV-2); any evidence
  contradicting sec3/sec5 stops the cycle for owner review; no
  implementation, no PRD redraft, no PR #269 modification.

## sec12 -- Reusable truths carried / assumptions discarded

Carried (re-verified E1-E8 above): artifact untracked/ignored; ignore
status is a publish-safety dependency (dirty-tree abort); not restored; not
in the hourly staging set; publish delta is committed-paths-only; producer
writes atomically and exits 0 only on success; renderer suppresses cleanly
on absence; GEX-2 live smoke demonstrated baseline neutrality; insertion
only on the fresh hourly-payload publish path, before rendering.
Discarded: the PRD-310 first-draft claim that ANY failure leaves the step
green (overstated -- scrub failure fails closed, per Codex F2 and the owner
adjudication); the first-draft NOT-MATERIAL classification (owner-overruled,
sec0).
