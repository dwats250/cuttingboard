# Gate Recon - 2026-06-12

Read-only reconnaissance of every decision/gate in the Cuttingboard pipeline,
its documented justification, and the publish-vs-preview gate diff. Produced
for an externally designed strategic gate-alignment audit. This report states
facts and flags; it does not judge whether any gate is strategically right.

METHOD. Seven parallel read-only code sweeps (partitioned by module), one
doc-side claims sweep, one publish-vs-preview topology trace, and one PRD-index
sweep. All decisive cross-cutting claims (publish-vs-preview diffs, "no caller"
claims, doc-vs-code conflicts) were re-verified by the orchestrating agent with
targeted rg/Read before being flagged, per the CLAUDE.md sub-agent sweep
re-verification rule. Every claim carries a file:line citation. Line numbers
are as of commit b4bfc5d (main, 2026-06-12).

SCOPE NOTE. "Gate" here = any conditional that suppresses, permits, transforms,
or reorders rendered output or notifications - permission gates, regime/state
checks, publish gating, preview-path checks, threshold filters, collapse rules,
and upstream status-emitters that downstream renderers key on. Pure computation
branches, raise-only error handling, and logging are excluded. Wording-only
branches (e.g. one posture phrase vs another) are kept but grouped as families.

CONTENTS
1. Canonical docs (verbatim)
2. PRD index
3. Gate inventory
4. Publish-vs-preview diff
5. Traceability map + flags
6. Open questions for the strategist

---

## 1. Canonical docs (verbatim)

The two documents below are spliced into this report directly from the files
on disk (not transcribed by a model), so they are byte-accurate as of the
recon date.

### 1.1 VISION.md

```markdown
# VISION.md

## What Cuttingboard is

Cuttingboard is a Python-based market observation and decision-support system. It ingests market data, computes contextual interpretations across a 10-layer pipeline, and renders artifacts that help answer four questions: *what environment are we in, what matters today, is this actually tradable, and what conditions invalidate this.*

Its core value is **cognitive compression** — reducing noise, organizing context, and forcing explicit reasoning under uncertainty. It is not a prediction engine. It does not generate alpha. It supports a discretionary trader operating in a domain where the cost of being wrong is high and the cost of being unprepared is higher.

## What Cuttingboard is not, and will not become

- Not an automated execution engine
- Not a backtesting framework
- Not a machine learning system
- Not a multi-agent orchestration platform
- Not a generalized financial operating system
- Not a high-frequency signal factory
- Not a regulated infrastructure project requiring aircraft-grade process

The system is built by one person, for one person's trading, on a part-time schedule. Scope decisions reflect that reality.

## Current state, honestly

**Built and in use:** the 10-layer pipeline (Ingestion through Audit), 2499 tests (1 xfailed), CLI entrypoint, GitHub Actions CI committing daily markdown reports, the artifact lineage and coherence enforcement work (PRDs 115-120), the sidecar architectural pattern, Gap-Down Permission Gating (built prior to VISION.md being written; retroactively documented as PRD-151 during the 2026-05-22 realignment).

**In flight:** none. Intraday state classification engine PRD (PRD-150) was killed 2026-05-22 per vision review.

**Dead code to remove:** Polygon integration (never used in production), ntfy alerts (topic `cuttingboard86`, no longer relied on), any references in config, env, requirements, and docs.

**Stalled and to be closed:** PRD 142 is blocked on data that isn't being collected. Either the data collection gap gets explicitly scoped or the PRD gets killed. No middle state.

**Suspected debt, unverified:** duplicated logic across sidecars, stale PRD references, renderer assumptions that no longer match actual use, "temporary" patches that became permanent. To be surfaced during the inventory audit.

## Phases ahead

**Phase 1 — Inventory, cleanup, implement, align.**

1. **Inventory audit.** Codex maps the full repo: modules, dependencies, dead code, orphans, drift from PRDs. Known cleanup targets (Polygon, ntfy, PRD 142) are flagged for deletion in the inventory rather than deeply analyzed.
2. **Consolidated cleanup.** All dead code removed in one informed pass — known targets plus anything inventory surfaced. Single coherent cleanup commit set.
3. **Gap-Down Permission Gating implementation.** Already complete — the 2026-05-22 realignment discovered the feature was implemented in `cuttingboard/intraday_state_engine.py` + `cuttingboard/runtime.py` (with dedicated integration tests) prior to VISION.md being written. Retrospectively documented as PRD-151.
4. **Architectural alignment audit.** Codex (directed by Claude) evaluates whether the resulting system matches this document. Sidecars are still read-only? No prediction logic crept in? Every module earns its keep? Dustin reviews the report and makes explicit decisions on every flagged item.

**Exit criteria:** repo contains only code that's used, every PRD is either active, completed, or formally killed, and the architecture demonstrably reflects what this document declares the system to be. Until alignment audit passes, no Phase 2 work begins.

**Phase 2 — Trade evaluation extension.** Build on the existing same-session evaluation infrastructure (`evaluation.py`, `performance_engine.py`) to consume Moomoo trade statements and produce post-hoc evaluation of actual executed trades against the market state Cuttingboard observed at the time. Read-only consumer of L10 audit output joined to imported trade records. Descriptive, not predictive. Closes the loop between the system's market observations and Dustin's actual trading behavior — the loop whose absence is the project's central weakness. Exit criteria: every trade Dustin takes can be evaluated against the market state at entry, exit, and key intermediate points.

**Phase 3 — Presentation pass.** README, repo hygiene, documentation that reflects the actual system rather than aspirational framing. The goal is a repo that a thoughtful outsider can read and understand in 15 minutes without being misled about what it does. No marketing language. Constraints stated plainly.

The ordering reflects a judgment: cleanup and audit first because debt compounds and silent drift is the failure mode that produced sprawl; sidecar second because it's the keystone for closing the explanation-to-behavior loop; presentation last because it should describe what exists rather than what's planned.

## Operating principles

- **PRD before build for anything non-trivial.** "Non-trivial" means: new module, new external dependency, new architectural pattern, or change that touches more than one layer of the pipeline. Bug fixes, small refactors, and additions within established patterns don't need PRDs. This is graduated formality, not abolition.
- **Read-only sidecars by default.** New observational features extend through sidecars rather than mutating core contracts.
- **Description, not prediction.** Features that explain or contextualize are welcome. Features that forecast are not.
- **Cuts before additions.** Before adding a feature, the system should justify the features it already has. Anything not earning its keep gets removed.
- **The system serves the trader, not the other way around.** If a feature exists but Dustin doesn't actually use it to make decisions, it shouldn't exist.
- **The system must match its documentation.** When code and documented intent diverge, one of them is wrong and the divergence gets resolved explicitly — by changing the code, changing the documentation, or formally acknowledging the gap. Silent drift is the failure mode that allowed sprawl, and the audit gate exists to catch it before it compounds.
- **Acknowledged debt requires a re-evaluation date.** When VISION.md or `docs/PROJECT_STATE.md` acknowledges technical debt with deferred remediation, `PROJECT_STATE.md` must name the date by which the debt is to be re-evaluated. Open-ended deferral is drift dressed as discipline.

## How we work

Dustin makes final decisions. AI handles logic and code. Implementations get reviewed before merge.

Claude (project lead) drafts PRDs, reviews code against architectural principles, flags drift from stated vision, asks the procedural questions the market won't ask. Authorized to push back on scope additions that violate non-goals; Dustin can override.

Codex (implementation) executes against specs. Doesn't make architectural calls. Output gets reviewed against the PRD.

Decisions that meaningfully change direction get recorded with date and rationale — short notes, not ceremony. Next session, we read what we decided last time so neither of us drifts silently.

## The trap to watch for

The strongest pattern-recognition Cuttingboard has built is environmental awareness. The weakest is the loop from awareness to behavioral change. The project's main failure mode going forward is producing better and better explanations of markets without producing fewer behavioral mistakes. Every proposed feature should be evaluated against: *does this change what I'll actually do, or does it just help me feel more informed about what I might do?* The latter is intellectual comfort dressed as progress.
```

### 1.2 CLAUDE.md

```markdown
# CLAUDE.md

## Role

Primary implementation agent for Cuttingboard. Drives PRD construction, code
implementation, test maintenance, and architectural decisions within PRD scope.
Invokes Codex for specialist tasks (cross-referencing, structured analysis,
code review).

## Canonical sources

This repo's state lives in source-of-truth documents. Reference these,
do not duplicate them.

- `VISION.md` — what Cuttingboard is, is not, is becoming
- `docs/PROJECT_STATE.md` — current state: test counts, milestones, known debt
- `docs/PRD_REGISTRY.md` — work in flight and completed
- `docs/DECISIONS.md` — meaningful decisions and rationale
- `README.md` — outsider's entry point
- `docs/architecture.md`, `docs/PRD_PROCESS.md`, `docs/sidecar_doctrine.md` —
  structural references

## Working agreement

Dustin makes final decisions. Claude (project lead, in chat) drafts PRDs and
reviews against VISION principles. Claude Code implements. Codex is invoked by
Claude Code for specialist tasks (cross-referencing, structured analysis,
code review). Architectural direction stays with Claude and Dustin.

Decisions that meaningfully change direction are recorded in `docs/DECISIONS.md`
with date and rationale.

## Operational rules

- **PRD before build for anything non-trivial** (new module, new external
  dependency, new architectural pattern, change touching multiple pipeline
  layers). Bug fixes and additions within established patterns don't need PRDs.
- **Read-only sidecars by default.** New observational features extend through
  sidecars rather than mutating core contracts.
- **Description, not prediction.** Features that explain or contextualize are
  welcome. Features that forecast are not.
- **Cuts before additions.** Before adding a feature, the system should justify
  the features it already has.
- **Strict scope locking.** A PRD's `FILES` section is a hard boundary. If a
  change requires touching a file not listed, stop and amend the PRD (or open
  a new one) before editing.
- **Pre-implementation grep sweep.** Before declaring a PRD's FILES set for any
  change that deletes, renames, or translates a rendered field / contract key /
  enum value, grep all of `tests/` for the affected token. Add every test file
  that asserts on the token to FILES in the initial PRD, not as reactive
  amendments after the test suite breaks. PRD-158 hit this loop three times
  before adopting the rule.
- **PRD file lands at Stage 0.** For any PRD, the first commit is the
  PRD-NNN.md scaffold plus the IN PROGRESS registry row plus the prd_index.json
  entry — *before* any implementation commit. Authoring a PRD in chat and only
  filing it at closeout is what produces sequencing-gate noise and forces
  reconstruction of the spec from chat history. (See `scripts/prd_open.sh` once
  it exists; until then, do the three edits by hand.)

## Workflow patterns

- Start work on a PRD by reading the PRD file, the related modules, and any
  prior decisions in `docs/DECISIONS.md`.
- When drift is discovered mid-task (code doesn't match docs, undocumented
  dependencies surface), pause and surface the drift before proceeding.
- **Reach for `Explore` (or `general-purpose`) reflexively for code-recon
  questions.** If the question is "where is X computed/called/asserted, and
  what depends on it?" — dispatch a subagent before reading files inline.
  Cost is small; the gain is preserved main-context window and parallelism
  while the recon runs. Going inline for this class of question burns context
  on detail the user does not need to see. PRD-158 had at least six missed
  opportunities of this shape.
- **Use `TaskCreate` upfront for any work with ≥3 distinct stages.** Update
  status as each stage starts/completes. Tracks progress visibly and reduces
  the size of per-step reports to a delta-against-tasks rather than a full
  re-statement.
- **Sequencing-gate fires are actionable, not boilerplate.** If the
  `UserPromptSubmit` sequencing-gate hook fires repeatedly for the same
  out-of-order PRD, the right response is to close the underlying registry
  inconsistency (typically a 10-minute bookkeeping commit), not to re-state
  the skip reason on every prompt. Repeating the skip reason is a signal that
  closeout is overdue.
- Invoke Codex when the value is a *genuinely independent second model* —
  PRD cross-review, vision review of a proposed PRD, structured code review
  before merge. Not for tasks `Explore` can do.
- All Codex *review* invocations run sandboxed read-only:
  `codex exec -s read-only - < prompt` (prompt via stdin, verdict
  captured from stdout). The review artifact
  (`docs/prd_history/PRD-NNN.review.codex.md`) is written by Claude
  Code from captured stdout — Codex never writes into the repo tree.
  (Verified 2026-06-10; see `docs/DECISIONS.md`.)
- Do not invoke Codex or subagents for: simple greps, git operations,
  mechanical edits.
- When two reviews are independent (e.g. Claude vision review + Codex
  cross-review on the same PRD draft), dispatch them in parallel rather than
  serially.
- When a Codex (or subagent) artifact materially drives a decision, link the
  artifact path in the `docs/DECISIONS.md` entry so the audit trail survives.
- Run targeted tests during iteration. Run the full suite once before
  pre-commit review — backgrounded (`run_in_background`) when the suite
  takes long enough to be worth doing other work in parallel.
- Read-only inspection commands (git status/diff/log, grep, find, targeted
  reads, pytest) may execute without per-command approval. Mutating commands —
  git pushes, file deletions, dependency changes, edits outside the active
  PRD's FILES allowlist — require explicit approval.

### Alignment cadence

Every 4-6 weeks, or after any phase boundary, run a scoped alignment
check against VISION.md. Three questions:

1. Has any new prediction logic entered the codebase?
2. Has any new sidecar been added without a documented consumer
   (decision-feeding) or without observational purpose (observation)?
3. Has any new module been added that doesn't serve at least one of
   VISION.md's four questions (what environment, what matters today, is
   this tradable, what invalidates) AND isn't an explicitly-named
   VISION.md phase deliverable (e.g. Phase 2 trade evaluation)?

If all three answers are "no," document the check in
`docs/DECISIONS.md` and move on. If any answer is "yes," scope a full
alignment audit. Drift is a function of time, not a bug — these checks
make it visible early.

### PRD-author disciplines

Four checks every PRD author should run before submitting for review.
The first three surfaced from the PRD-150 review arc (2026-05-22); see
`docs/DECISIONS.md` and `audits/recon-2026-05-22/prd-150-vision-review.md`
for context. The fourth surfaced from the sub-agent flow audit
(2026-06-10).

- **Dead-branch enumeration.** When retiring a code path (e.g. a
  short-circuit, a status value, a function), enumerate every
  downstream reader of the retired surface. For each reader, either
  remove it in the same PRD or document it as retained-with-reason
  ("dead branch by design, kept for shape stability"). A retired
  surface with un-enumerated readers is hidden drift.
- **Downstream-consumer audit.** For any new emission, contract field,
  status value, rejection stage, or artifact path: identify every
  module that reads it and verify the change is compatible. Postmarket
  reports, dashboard renderers, audit writers, and notification
  formatters are common consumers. A PRD that adds an emission without
  updating its consumers leaks under-counting or silent drift.
- **Realizability check.** For any new output channel (rejection stage,
  classification tier, sidecar field, status literal), verify there
  exists at least one realistic input path under current routing that
  produces non-trivial output. A channel whose every emission case is
  pre-empted by an upstream channel is dead code with extra steps.
  If a channel is defensive-against-future-routing, declare it as
  such — don't claim it's currently active.
- **Sub-agent sweep re-verification.** Any sub-agent grep/recon sweep
  whose output feeds a PRD FILES boundary or a "nothing else
  reads/calls this" claim must be re-verified before the claim counts:
  the main agent re-runs the single decisive `rg` itself. One command;
  it closes the false-all-clear path where an incomplete delegated
  sweep manufactures a clean result.

## Anti-patterns

- Do not draft PRDs for features that violate VISION.md non-goals without
  explicit override from Dustin.
- Do not refactor `runtime.py` opportunistically; it is acknowledged debt and
  refactors require their own PRD.
- Do not add documentation that duplicates content in canonical sources;
  reference instead.
- Do not silently expand a PRD's FILES set mid-implementation. Amend the PRD
  first.
- Do not commit generated artifacts (`logs/*`, `reports/*`) outside the
  workflow-driven force-add allowlist.
```

---

## 2. PRD index

Source: docs/PRD_REGISTRY.md (status column reproduced exactly), cross-checked
against docs/prd_index.json and docs/prd_history/. Citation = registry row.

| PRD | Status | One-line summary | Cite |
|---|---|---|---|
| Init | COMPLETE | Bootstrap - initial PRD committed | PRD_REGISTRY.md:9 |
| PRD-001 | COMPLETE | 10-layer pipeline bootstrap - full system, 297 tests, GHA workflow | PRD_REGISTRY.md:10 |
| PRD-002 | COMPLETE | Options chain validation + runtime orchestrator | PRD_REGISTRY.md:11 |
| PRD-003 | COMPLETE | Deterministic failure visibility in CI pipeline | PRD_REGISTRY.md:12 |
| PRD-003.2 | PATCH | Fix remaining workflow patch drift | PRD_REGISTRY.md:13 |
| PRD-003.3 | PATCH | Fix CI failure-path guards | PRD_REGISTRY.md:14 |
| PRD-003.4 | PATCH | Replace stale workflow lines exactly | PRD_REGISTRY.md:15 |
| PRD-004 | COMPLETE | Contract alignment - audit contract, stale data validation | PRD_REGISTRY.md:16 |
| PRD-005 | COMPLETE | Alert routing/trade formatting separation; STAY_FLAT crash fix; failure artifacts | PRD_REGISTRY.md:17 |
| PRD-006 | COMPLETE | Remove ntfy transport; enforce Telegram-only notification path | PRD_REGISTRY.md:18 |
| PRD-007 | COMPLETE | Imbalance pullback entry (FVG) - qualification and options layers | PRD_REGISTRY.md:19 |
| PRD-008 | COMPLETE | Expansion regime detection + continuation entry mode | PRD_REGISTRY.md:20 |
| PRD-009 | COMPLETE | Canonical timezone handling + time gate validation | PRD_REGISTRY.md:21 |
| PRD-010 | COMPLETE | Continuation rejection audit + threshold calibration | PRD_REGISTRY.md:22 |
| PRD-011 | COMPLETE | Freeze canonical pipeline output contract | PRD_REGISTRY.md:23 |
| PRD-012 | COMPLETE | Deterministic payload delivery layer - adapter and transport | PRD_REGISTRY.md:24 |
| PRD-012 (cleanup) | PATCH | Post-audit cleanup: dead code, symbols_scanned, determinism | PRD_REGISTRY.md:25 |
| PRD-012A | COMPLETE | Guarantee hourly Telegram alerts via dedicated GitHub workflow | PRD_REGISTRY.md:26 |
| PRD-013 | COMPLETE | Flow alignment soft gate in qualification pipeline | PRD_REGISTRY.md:27 |
| PRD-014 | COMPLETE | Structural hardening, flow wiring, config-driven ingestion | PRD_REGISTRY.md:28 |
| PRD-015 / 015.1 | COMPLETE | Flow wiring and ingestion config consolidation (with PRD-014) | PRD_REGISTRY.md:29 |
| PRD-016 / 016.1 | COMPLETE | Pre-UI audit: legacy cleanup, interface lock, contract verification | PRD_REGISTRY.md:30 |
| PRD-017 | COMPLETE | Notification delivery stabilization: rate limit, retry, aggregation, audit | PRD_REGISTRY.md:31 |
| PRD-018 | COMPLETE | Notification signal hierarchy and suppression: state key, priority, dedup | PRD_REGISTRY.md:32 |
| PRD-019 | COMPLETE | Registry row says "Engine doctor - canonical pipeline health authority"; PRD file is "Notification Decision Audit / Delivery Safety Layer" (see flags, 5.3) | PRD_REGISTRY.md:33 |
| PRD-020 | COMPLETE | Engine doctor gate system (CI + runtime guardrails) | PRD_REGISTRY.md:34 |
| PRD-021 | COMPLETE | Documentation canonicalization (README + docs system) | PRD_REGISTRY.md:35 |
| PRD-022 | COMPLETE | Sunday mode isolation - no live data, forced STAY_FLAT | PRD_REGISTRY.md:36 |
| PRD-023 | COMPLETE | GLD-DXY correlation policy layer - advisory risk_modifier | PRD_REGISTRY.md:37 |
| PRD-024 | COMPLETE | Contract UI consumer - static HTML read-only decision surface | PRD_REGISTRY.md:38 |
| PRD-025 | COMPLETE | Decision compression layer - primary signal and trade promotion | PRD_REGISTRY.md:39 |
| PRD-026 | COMPLETE | Alert visibility upgrade - deterministic ASCII titles, structured body | PRD_REGISTRY.md:40 |
| PRD-027 | COMPLETE | Context report layer - deterministic premarket and postmarket reports | PRD_REGISTRY.md:41 |
| PRD-028 | COMPLETE | PRD system hardening - template, lifecycle states, scope lock | PRD_REGISTRY.md:42 |
| PRD-029 | COMPLETE | Level awareness layer - derived price levels for reports | PRD_REGISTRY.md:43 |
| PRD-030 | COMPLETE | Scenario engine hardening - regime + level driven scenarios | PRD_REGISTRY.md:44 |
| PRD-031 | COMPLETE | Claude Code hooks - commit gate, file guard, test gate, snapshot | PRD_REGISTRY.md:45 |
| PRD-032 | DEPRECATED | Catastrophic output and validation contract repair | PRD_REGISTRY.md:46 |
| PRD-033 | COMPLETE | UI theme layer - sideloadable CSS theme system | PRD_REGISTRY.md:47 |
| PRD-034 | COMPLETE | GitHub Pages deployment - remote read-only access | PRD_REGISTRY.md:48 |
| PRD-035 | COMPLETE | Signal Forge dashboard - contract regime block + UI macro strip | PRD_REGISTRY.md:49 |
| PRD-036 | COMPLETE | Slim dashboard renderer - read-only HTML from payload + run artifacts | PRD_REGISTRY.md:50 |
| PRD-037 | COMPLETE | Dashboard publish artifact - static copy of HTML to docs/ | PRD_REGISTRY.md:51 |
| PRD-038 | COMPLETE | Read-only macro tape consolidation block | PRD_REGISTRY.md:52 |
| PRD-039 | COMPLETE | Dashboard link in all Telegram alerts | PRD_REGISTRY.md:53 |
| PRD-040 | COMPLETE | Protect latest_* artifacts with timestamp guard | PRD_REGISTRY.md:54 |
| PRD-041 | COMPLETE | Run delta change detection block | PRD_REGISTRY.md:55 |
| PRD-042 | COMPLETE | Snapshot history - recent runs view | PRD_REGISTRY.md:56 |
| PRD-043 | COMPLETE | Decision summary block | PRD_REGISTRY.md:57 |
| PRD-044 | COMPLETE | Macro driver payload surface with no-data mode support | PRD_REGISTRY.md:58 |
| PRD-045 | COMPLETE | Trade decision materialization - explicit ALLOW/BLOCK per candidate | PRD_REGISTRY.md:59 |
| PRD-046 | COMPLETE | Decision trace - first-failure explanation per candidate | PRD_REGISTRY.md:60 |
| PRD-047 | (skipped) | Number intentionally not assigned | PRD_REGISTRY.md:61 |
| PRD-048 | COMPLETE | Trade decision visibility in payload and dashboard | PRD_REGISTRY.md:62 |
| PRD-049 | COMPLETE | Development process hardening - CI tests, linting, commit gate | PRD_REGISTRY.md:63 |
| PRD-050 | COMPLETE | Alert runner fail-visible backstop | PRD_REGISTRY.md:64 |
| PRD-051 | COMPLETE | Execution policy materialization | PRD_REGISTRY.md:65 |
| PRD-052 | COMPLETE | Runtime artifact self-healing - legacy timestamp tolerance | PRD_REGISTRY.md:66 |
| PRD-053 | COMPLETE | Graded market map sidecar | PRD_REGISTRY.md:67 |
| PRD-053 PATCH | COMPLETE | Market map input plumbing + usefulness calibration | PRD_REGISTRY.md:68 |
| PRD-054 | COMPLETE | Add trade framing to market map sidecar | PRD_REGISTRY.md:69 |
| PRD-055 | COMPLETE | Dashboard upgrade - macro tape, system state, candidate board | PRD_REGISTRY.md:70 |
| PRD-056 | COMPLETE | Candidate lifecycle tracking - grade/setup_state transitions | PRD_REGISTRY.md:71 |
| PRD-057 | COMPLETE | Lifecycle visibility on dashboard - badge, detail row, removed section | PRD_REGISTRY.md:72 |
| PRD-058 | COMPLETE | Overnight Exit Guidance Layer | PRD_REGISTRY.md:73 |
| PRD-059 | COMPLETE | Macro Tape value row hardening | PRD_REGISTRY.md:74 |
| PRD-060 | COMPLETE | Deterministic macro pressure snapshot | PRD_REGISTRY.md:75 |
| PRD-061 | COMPLETE | PRD Registry Numbering Guard | PRD_REGISTRY.md:76 |
| PRD-062 | COMPLETE | Macro Pressure Block in dashboard | PRD_REGISTRY.md:77 |
| PRD-063 | COMPLETE | Macro Pressure Execution Policy Integration | PRD_REGISTRY.md:78 |
| PRD-064 | COMPLETE | Trade Visibility Layer (Near-Miss Engine) | PRD_REGISTRY.md:79 |
| PRD-065 | COMPLETE | Interactive Dashboard Controls | PRD_REGISTRY.md:80 |
| PRD-066 | COMPLETE | Trade Drilldown Panel (Deterministic Explanation Layer) | PRD_REGISTRY.md:81 |
| PRD-067 | COMPLETE | Trade Thesis Gate | PRD_REGISTRY.md:82 |
| PRD-068 | COMPLETE | Invalidation and Exit Guidance Layer | PRD_REGISTRY.md:83 |
| PRD-069 | COMPLETE | Entry Quality and Chase Filter | PRD_REGISTRY.md:84 |
| PRD-070 | COMPLETE | Manual Trade Journal and Mistake Taxonomy | PRD_REGISTRY.md:85 |
| PRD-071 | COMPLETE | Trading Process Review Scorecard | PRD_REGISTRY.md:86 |
| PRD-072 | COMPLETE | Macro Drivers Snapshot Fallback | PRD_REGISTRY.md:87 |
| PRD-073 | COMPLETE | Human-Readable Dashboard Trader View | PRD_REGISTRY.md:88 |
| PRD-073-PATCH | COMPLETE | Renderer Boundary Test - contract isolation for R4 | PRD_REGISTRY.md:89 |
| PRD-074 | COMPLETE | Chart Context Layer (Level Diagram) | PRD_REGISTRY.md:90 |
| PRD-075 | COMPLETE | Signal Performance Engine | PRD_REGISTRY.md:91 |
| PRD-076 | COMPLETE | Dashboard Live Publishing and Layout Finalization | PRD_REGISTRY.md:92 |
| PRD-077 | COMPLETE | Sunday Futures Pre-Report | PRD_REGISTRY.md:93 |
| PRD-078 | COMPLETE | Dashboard Demo Candidate Fixture Mode | PRD_REGISTRY.md:94 |
| PRD-079 | COMPLETE | PRD Review Token Efficiency Guardrails | PRD_REGISTRY.md:95 |
| PRD-080 | COMPLETE | Sunday Report Expansion Layer | PRD_REGISTRY.md:96 |
| PRD-081 | COMPLETE | Dashboard Timestamp Display Hardening | PRD_REGISTRY.md:97 |
| PRD-082 | COMPLETE | Remove Redundant Dashboard Permission Copy | PRD_REGISTRY.md:98 |
| PRD-083 | COMPLETE | Dashboard Data Freshness and Source Visibility | PRD_REGISTRY.md:99 |
| PRD-084 | COMPLETE | Populate market_map current_price | PRD_REGISTRY.md:100 |
| PRD-085 | COMPLETE | Regression: current_price survives runtime processing chain | PRD_REGISTRY.md:101 |
| PRD-086 | COMPLETE | Carry forward current_price through Sunday market map | PRD_REGISTRY.md:102 |
| PRD-087 | COMPLETE | Pipeline Command Timeout Hardening | PRD_REGISTRY.md:103 |
| PRD-088 | COMPLETE | Candidate Board Level Diagram Price Fallback | PRD_REGISTRY.md:104 |
| PRD-089 | COMPLETE | Dashboard Artifact Coherence Guard | PRD_REGISTRY.md:105 |
| PRD-089-PATCH | COMPLETE | Integrate run snapshot into system state | PRD_REGISTRY.md:106 |
| PRD-090 | COMPLETE | Candidate Board Display Tiers | PRD_REGISTRY.md:107 |
| PRD-091 | COMPLETE | Candidate Validation Context | PRD_REGISTRY.md:108 |
| PRD-092 | COMPLETE | Macro Conditions Consolidation | PRD_REGISTRY.md:109 |
| PRD-093 | COMPLETE | System State Information Economy | PRD_REGISTRY.md:110 |
| PRD-094 | COMPLETE | Public Dashboard Artifact Contamination Guard | PRD_REGISTRY.md:111 |
| PRD-095 | COMPLETE | Scheduled Pipeline Morning Readiness Guard | PRD_REGISTRY.md:112 |
| PRD-096 | COMPLETE | Runtime Artifact Git Hygiene and Pre-Push Safety | PRD_REGISTRY.md:113 |
| PRD-097 | COMPLETE | Dashboard Sidecar Freshness and Permission Clarity | PRD_REGISTRY.md:114 |
| PRD-098 | COMPLETE | Candidate Board Visibility and Validation Diagnostics | PRD_REGISTRY.md:115 |
| PRD-099 | COMPLETE | Dashboard Artifact Generation Contract | PRD_REGISTRY.md:116 |
| PRD-100 | COMPLETE | Standardize Artifact Push Rebase Contract | PRD_REGISTRY.md:117 |
| PRD-100-PATCH | PATCH | Artifact Push Helper Dirty Tree Rebase Safety | PRD_REGISTRY.md:118 |
| PRD-100-PATCH-2 | PATCH | Hourly Artifact Mutation Ordering | PRD_REGISTRY.md:119 |
| PRD-101 | COMPLETE | Hourly Telegram Notification Truth Contract | PRD_REGISTRY.md:120 |
| PRD-102 | COMPLETE | Align Alert and Dashboard Candidate Semantics | PRD_REGISTRY.md:121 |
| PRD-103 | COMPLETE | Dashboard Data Contract Gap Patch | PRD_REGISTRY.md:122 |
| PRD-104 | COMPLETE | Decision Logic and Artifact Flow Audit | PRD_REGISTRY.md:123 |
| PRD-105 | COMPLETE | Decision Quality Evidence Map | PRD_REGISTRY.md:124 |
| PRD-106 | COMPLETE | Cheap Lookup Dispatch Policy | PRD_REGISTRY.md:125 |
| PRD-107 | COMPLETE | Trend Structure Snapshot Sidecar | PRD_REGISTRY.md:126 |
| PRD-108 | COMPLETE | Registry Hook Hygiene | PRD_REGISTRY.md:127 |
| PRD-109 | COMPLETE | Workflow Token Economy | PRD_REGISTRY.md:128 |
| PRD-110 | COMPLETE | Narrow Trend Structure Snapshot Universe | PRD_REGISTRY.md:129 |
| PRD-111 | COMPLETE | Documentation & Knowledge-System Consolidation | PRD_REGISTRY.md:130 |
| PRD-112 | COMPLETE | Trend Structure Dashboard Panel | PRD_REGISTRY.md:131 |
| PRD-113 | COMPLETE | PRD Governance Hardening | PRD_REGISTRY.md:132 |
| PRD-114 | COMPLETE | Watchlist Snapshot Sidecar | PRD_REGISTRY.md:133 |
| PRD-115 | COMPLETE | Dashboard Artifact Lineage Visibility | PRD_REGISTRY.md:134 |
| PRD-116 | COMPLETE | Dashboard Mixed-Artifact Hierarchy Hardening | PRD_REGISTRY.md:135 |
| PRD-117 | COMPLETE | Session-Aware Inactive-State Labeling | PRD_REGISTRY.md:136 |
| PRD-118 | COMPLETE | Coherent Dashboard Publish Artifact Set | PRD_REGISTRY.md:137 |
| PRD-119 | COMPLETE | Dashboard Publish Freshness Gate | PRD_REGISTRY.md:138 |
| PRD-120 | COMPLETE | Dashboard Source-Health Diagnostics + Permission Display Correction | PRD_REGISTRY.md:139 |
| PRD-121 | COMPLETE | PRD Workflow Lane Classification and Review Discipline | PRD_REGISTRY.md:140 |
| PRD-122 | COMPLETE | Add WTI Crude Macro Visibility | PRD_REGISTRY.md:141 |
| PRD-122-PATCH | PATCH | Payload validator permits optional oil driver | PRD_REGISTRY.md:142 |
| PRD-123 | COMPLETE | Trend Structure Refresh Decoupling, Truthful Source Status | PRD_REGISTRY.md:143 |
| PRD-124 | COMPLETE | Hourly Telegram Alert Header and Body Quality | PRD_REGISTRY.md:144 |
| PRD-125 | COMPLETE | OHLCV Cache Freshness Contract | PRD_REGISTRY.md:145 |
| PRD-126 | COMPLETE | Fixture Mode No-Live-OHLCV Boundary | PRD_REGISTRY.md:146 |
| PRD-127 | COMPLETE | Hourly Alert Action Language Alignment | PRD_REGISTRY.md:147 |
| PRD-128 | COMPLETE | Hourly Readiness Ordering | PRD_REGISTRY.md:148 |
| PRD-129 | COMPLETE | CI Artifact Hygiene and Push-Guard Stability | PRD_REGISTRY.md:149 |
| PRD-130 | COMPLETE | Trend Structure Unknown-State Normalization | PRD_REGISTRY.md:150 |
| PRD-131 | COMPLETE | Trend Structure Composite Display Layer | PRD_REGISTRY.md:151 |
| PRD-132 | COMPLETE | Intraday VWAP x RVOL Context Display Layer | PRD_REGISTRY.md:152 |
| PRD-133 | COMPLETE | Telegram Macro Pulse Alert Clarity | PRD_REGISTRY.md:153 |
| PRD-134 | COMPLETE | Daily Pipeline Market Map Coherence Repair | PRD_REGISTRY.md:154 |
| PRD-135 | COMPLETE | Engine Milestone Review and Consolidation Checkpoint | PRD_REGISTRY.md:155 |
| PRD-136 | COMPLETE | Add Spot Metals Row to Macro Tape | PRD_REGISTRY.md:156 |
| PRD-137 | COMPLETE | PATCH PRD-136: payload validator accepts optional spot metals | PRD_REGISTRY.md:157 |
| PRD-138 | COMPLETE | Shared Macro Tape Layout and Spot-Metals Color Parity | PRD_REGISTRY.md:158 |
| PRD-139 | COMPLETE | Upstream Macro Collector Sidecar | PRD_REGISTRY.md:159 |
| PRD-140 | COMPLETE | Document pre_push_check.sh in CLAUDE.md git hygiene | PRD_REGISTRY.md:160 |
| PRD-141 | COMPLETE | Hourly Alert Canonical Slot + Cross-Run Idempotency | PRD_REGISTRY.md:161 |
| PRD-142 | DEPRECATED | PATCH PRD-141: persist hourly slot state across CI runs (killed per VISION 2026-05-22) | PRD_REGISTRY.md:162 |
| PRD-143 | COMPLETE | Process hygiene sweep: hook exclusion, runtime.py debt note | PRD_REGISTRY.md:163 |
| PRD-144 | COMPLETE | Redundant cron entries for 6 AM PT hourly alert resilience | PRD_REGISTRY.md:164 |
| PRD-145 | COMPLETE | Sequencing-gate parser keys on row-owner cell only | PRD_REGISTRY.md:165 |
| PRD-146 | COMPLETE | Reconcile prd_index.json with registry truth for 141/142/143 | PRD_REGISTRY.md:166 |
| PRD-147 | COMPLETE | prd_close.sh must not parse user input as re.sub template | PRD_REGISTRY.md:167 |
| PRD-148 | COMPLETE | Insert PRD-145 entry into prd_index.json | PRD_REGISTRY.md:168 |
| PRD-149 | COMPLETE | PT-Anchored Hourly Alert Window (6:00 AM - 1:00 PM PT) | PRD_REGISTRY.md:169 |
| PRD-150 | DEPRECATED | Five-Tier Symbol Classification System (killed 2026-05-22 per vision review) | PRD_REGISTRY.md:170 |
| PRD-151 | COMPLETE | Gap-Down Permission Gating (retrospective documentation) | PRD_REGISTRY.md:171 |
| PRD-152 | COMPLETE | Batch B: Compatibility Shim Removal | PRD_REGISTRY.md:172 |
| PRD-153 | DEPRECATED | Moomoo Statement Consumer (Phase 2) - superseded by PRD-156 | PRD_REGISTRY.md:173 |
| PRD-154 | COMPLETE | Scrub historical pytest contamination from logs/audit.jsonl | PRD_REGISTRY.md:174 |
| PRD-155 | COMPLETE | Audit-write coverage doctrine | PRD_REGISTRY.md:175 |
| PRD-156 | COMPLETE | Surgical removal of Moomoo Statement Consumer (PRD-153) | PRD_REGISTRY.md:176 |
| PRD-157 | COMPLETE | Account-Equity-Driven Position Sizing | PRD_REGISTRY.md:177 |
| PRD-158 | COMPLETE | Dashboard Output Surface Realignment (Pass 1) | PRD_REGISTRY.md:178 |
| PRD-159 | COMPLETE | scripts/prd_open.sh - Stage 0 PRD scaffolder | PRD_REGISTRY.md:179 |
| PRD-160 | COMPLETE | Fix macro_bias arrow-counting inversion | PRD_REGISTRY.md:180 |
| PRD-161 | COMPLETE | Add tradable qualified fixture for PRD-157 sizing gate | PRD_REGISTRY.md:181 |
| PRD-162 | COMPLETE | outcome / regime / market_map reconciliation | PRD_REGISTRY.md:182 |
| PRD-163 | COMPLETE | Fix regime permission wording for EXPANSION posture | PRD_REGISTRY.md:183 |
| PRD-164 | COMPLETE | Harden PRD lifecycle tooling | PRD_REGISTRY.md:184 |
| PRD-165 | COMPLETE | Candidate-card visual hierarchy + trend-structure dead-column pruning | PRD_REGISTRY.md:185 |
| PRD-166 | COMPLETE | Hourly market_map artifact isolation (PRD-118 R3 coherence) | PRD_REGISTRY.md:186 |
| PRD-167 | COMPLETE | RUN SNAPSHOT relative-freshness token | PRD_REGISTRY.md:187 |
| PRD-168 | COMPLETE | Suppress idle screen-verdict above populated candidate cards | PRD_REGISTRY.md:188 |
| PRD-169 | COMPLETE | Persist continuation_audit to logs/audit.jsonl | PRD_REGISTRY.md:189 |
| PRD-170 | COMPLETE | runtime.py monolith split: cut-line doctrine and roadmap | PRD_REGISTRY.md:190 |
| PRD-171 | COMPLETE | Sync PRD templates' status markers to prd_close.sh convention | PRD_REGISTRY.md:191 |
| PRD-172 | COMPLETE | prd_close.sh baseline-bullet regex tolerates N-xfailed suffix | PRD_REGISTRY.md:192 |
| PRD-173 | COMPLETE | runtime/ package skeleton (Stage A of runtime.py split) | PRD_REGISTRY.md:193 |
| PRD-174 | COMPLETE | Populate trend-structure OHLCV on STAY_FLAT hourly runs | PRD_REGISTRY.md:194 |
| PRD-175 | COMPLETE | Historical regime scoreboard aggregation sidecar | PRD_REGISTRY.md:195 |
| PRD-176 | COMPLETE | Red-folder economic calendar static schedule and loader | PRD_REGISTRY.md:196 |
| PRD-177 | COMPLETE | Dashboard realignment pass 2: cuts, four-questions reorder, macro evidence, scoreboard + red-folder render | PRD_REGISTRY.md:197 |
| PRD-178 | IN PROGRESS | Dashboard fresh-data preview loop (CI preview workflow + local script) | PRD_REGISTRY.md:198 |
| PRD-179 | PROPOSED | Preview fixture/all-section-state coverage (fast-follow to PRD-178) | PRD_REGISTRY.md:199 |

### 2.1 PRD-174..179 detail (flagged set)

- PRD-174 (COMPLETE) - trend structure renders real values for all six
  config.TREND_STRUCTURE_SYMBOLS on every hourly run regardless of
  regime.posture (including STAY_FLAT), preserving graceful degradation.
  FILES: cuttingboard/runtime/__init__.py, tests/test_runtime_trend_structure_refresh.py.
  Lands the data layer for PRD-175/176/177. (PRD-174.md:1, PRD_REGISTRY.md:194)
- PRD-175 (COMPLETE) - daily append-only logs/regime_history.jsonl aggregated
  from logs/audit.jsonl; prior day's record carries SPY next-session pct
  change; produced by a post-run workflow step. FILES:
  cuttingboard/delivery/regime_history.py, .github/workflows/hourly_alert.yml,
  tests/test_regime_history.py. Grading (hit-rate/accuracy) deferred to a
  future PRD; render absorbed by PRD-177. (PRD-175.md:1, PRD_REGISTRY.md:195)
- PRD-176 (COMPLETE) - zero-dependency static red-folder schedule + pure
  loader returning events within a lookahead window, with expiry warning.
  FILES: data/red_folder_2026.json, cuttingboard/red_folder.py,
  tests/test_red_folder.py. Entry/qualification gate keyed on event windows
  explicitly deferred. (PRD-176.md:1, PRD_REGISTRY.md:196)
- PRD-177 (COMPLETE) - every rendered section maps to VISION's four questions
  in order; debugging sections removed; macro rows show cyclicality-aware
  vote; SCOREBOARD and RED FOLDER sections land. FILES: dashboard_renderer.py,
  macro_tape_layout.py, ui/dashboard.html, ui/index.html, 4 test files.
  Invalidation line under System State deferred (needs new engine state).
  (PRD-177.md:1, PRD_REGISTRY.md:197)
- PRD-178 (IN PROGRESS) - on-demand CI preview workflow that can never
  send/commit/deploy + local preview script that can never write under ui/;
  real publish gates exercised against fresh data. FILES:
  .github/workflows/dashboard_preview.yml, scripts/preview_dashboard.sh,
  tests/test_ci_artifact_hygiene.py. Fixture coverage deferred to PRD-179.
  (PRD-178.md:1, PRD_REGISTRY.md:198)
- PRD-179 (PROPOSED) - extend preview loop to synthetic fixture payload sets
  exercising each conditional section state, respecting PRD-118 R5 (fixture
  data never publishes to ui/). (PRD-179.md:1, PRD_REGISTRY.md:199)

### 2.2 Registry consistency

Status values are consistent across PRD_REGISTRY.md, prd_index.json, and the
PRD files for all entries (index sweep, re-checked for 174-179). One
discrepancy found by this recon that the index sweep missed: the PRD-019
registry row TITLE does not match the PRD-019 file (see flag 5.3-G1).

---

## 3. Gate inventory

Grouped by module. Columns: LOC (file:line of the conditional), Trigger
(plain-English condition), Effect when tripped, Path (publish / preview /
both / notification / harness), Breadcrumb (PRD or doc reference found within
~20 lines of the code, "none" = no in-code justification marker). "(B)" after
a gate id = borderline inclusion. "family" rows merge near-identical branches;
all member line numbers are listed. Paths for shared library code are "both"
because the publish and CI-preview paths execute the same Python (see sec. 4).

### 3.1 Runtime orchestration (cuttingboard/runtime/__init__.py) and CI workflows

| Gate | LOC | Trigger | Effect | Path | Breadcrumb |
|---|---|---|---|---|---|
| mode-verify-early-exit | runtime/__init__.py:184 | args.mode == MODE_VERIFY | Pipeline does not run; only verify_run_summary prints PASS/FAIL | standalone verify | none |
| mode-prefetch-early-exit | runtime/__init__.py:193 | args.mode == MODE_PREFETCH | Fetch/normalize/validate/derive only; no report, no notification | warm-up | none |
| prefetch-halted-skip-derive (B) | runtime/__init__.py:224 | system_halted during prefetch | compute_all_derived skipped; no derived cache | warm-up | none |
| verification-pass-status-downgrade | runtime/__init__.py:260 | verify fails or summary status != SUCCESS | summary status -> FAIL; report stamped FAIL; CI exits 1 | publish | none |
| notify-run-validation-halted-skip-regime | runtime/__init__.py:382 | system_halted in _execute_notify_run | regime/candidates/qualification skipped; alert sent with regime=None placeholders | notification | none |
| qualify-only-modes-pipeline-depth | runtime/__init__.py:394 | notify_mode in _QUALIFY_ONLY_MODES (post_orb, power_hour, market_close) | full structure+candidates+qualification runs; alert content includes qualified trades | notification | none |
| regime-only-modes-skip-qualify (B) | runtime/__init__.py:394 (absence of branch) | notify_mode in _REGIME_ONLY_MODES (orb_trajectory, midmorning) | only regime computed; alert has regime data only, no candidates | notification | _constants.py:33 |
| hourly-stay-flat-skip-qualify | runtime/__init__.py:417 | hourly mode AND regime.posture == STAY_FLAT | candidate generation, short-permission filter, qualification all skipped; hourly alert has no candidate lines | notification | none |
| hourly-notify-format-branch | runtime/__init__.py:445 | notify_mode in _HOURLY_MODES | format_hourly_notification used instead of format_notification | notification | none |
| notify-mode-live-only-send | runtime/__init__.py:474 | mode == MODE_LIVE in _execute_notify_run | send_notification only in live mode; fixture/sunday notify runs never send | notification | none |
| hourly-save-slot-on-alert-sent | runtime/__init__.py:515 | alert_sent AND slot_utc set | save_last_slot persists slot; next same-slot run suppressed | notification | PRD-141, PRD-149 |
| hourly-system-halted-skip-watchlist | runtime/__init__.py:544 | system_halted on hourly run | _write_watchlist_snapshot skipped; watchlist snapshot left stale | notification | none |
| system-halt-skip-pipeline | runtime/__init__.py:667 | validation_summary.system_halted | regime, structure, candidates, qualification, setups, decisions, notifications all skipped; outcome=HALT; report renders with no trades | publish | none |
| sunday-skip-derived-and-candidates | runtime/__init__.py:675 | mode == MODE_SUNDAY | derived metrics through trade decisions all skipped; report = regime only | publish | none |
| fixture-skip-intraday-short-permission | runtime/__init__.py:708 | mode == MODE_FIXTURE | gap-down SHORT filter not applied on fixture runs | publish | none (PRD-151.md:106 documents) |
| no-qualified-trades-skip-option-setups | runtime/__init__.py:727 | qualified_trades empty | build_option_setups not called; outcome -> NO_TRADE | publish | PRD-162 (line 793) |
| no-option-setups-skip-chain-validation | runtime/__init__.py:736 | option_setups empty | validate_option_chains not called; no trade decisions | publish | none |
| fixture-chain-validation-bypass | runtime/__init__.py:737 | option_setups AND mode == MODE_FIXTURE | live chain validation replaced with stub MANUAL_CHECK results | publish (fixture) | none |
| no-option-setups-skip-trade-decisions | runtime/__init__.py:744 | option_setups empty | decision/policy/thesis/invalidation/entry-quality gates not called | publish | PRD-162 (line 793) |
| outcome-trade-vs-no-trade | runtime/__init__.py:797 | any decision_is_actionable(decision) | outcome = TRADE vs NO_TRADE; drives report body branch + notification content | publish | PRD-162 (line 793) |
| system-halted-permission-override | runtime/__init__.py:876 | system_halted | contract permission forced to "No trades permitted. System halted." | publish | none |
| sunday-session-type-injection | runtime/__init__.py:887 | mode == MODE_SUNDAY | stay_flat_reason forced PREMARKET_CONTEXT; session_type SUNDAY_PREMARKET | publish | none (PRD-077 documents) |
| premarket-notification-suppression | runtime/__init__.py:894 | mode in {LIVE, SUNDAY} AND not fixture_backed | notification attempted only on live/sunday non-fixture runs | publish | PRD-018 (line 891) |
| prd018-unchanged-state-suppression | runtime/__init__.py:899 | should_send(current_key, priority, last_key) False | notification suppressed; audit row reason=suppressed_unchanged_state; artifacts still publish | publish | PRD-018 (line 891) |
| mode-live-trend-structure-refresh | runtime/__init__.py:979 | mode == MODE_LIVE | trend_structure_snapshot.json refreshed only on live; stale otherwise | publish | PRD-123 (lines 974-978) |
| kill-switch-zeroes-qualified-count | runtime/__init__.py:1055 | _kill_switch true | validated_count forced to 0 in summary; dashboard shows 0 qualified even if decisions exist | publish | none |
| system-halted-permission-in-summary | runtime/__init__.py:1066 | system_halted in _build_run_summary | summary permission = halt message regardless of posture | publish | none |
| summary-status-halted-system | runtime/__init__.py:1076 | system_halted or errors | summary status -> FAIL; CI exit code, verify, dashboard all see failure | publish | none |
| sunday-summary-zeroes-candidates | runtime/__init__.py:1090 | mode == MODE_SUNDAY | candidates_generated/qualified always 0 in summary | publish | none |
| intraday-short-state-unavailable-fail-open | runtime/__init__.py:1136 | intraday state unavailable for SHORT candidate | candidate NOT filtered (fail-open); SHORT proceeds without confirmation | both | none (PRD-151.md:96 documents) |
| intraday-short-permission-filter | runtime/__init__.py:1147 | downside_permission False | SHORT candidate popped pre-qualification; silent in contract (no excluded/watchlist/rejections entry) | both | none (PRD-151.md:117 documents silence) |
| downside-permission-gap-down family | runtime/__init__.py:1255-1266 | gap DOWN + phase OPEN -> deny; gap DOWN + SHORT break unconfirmed -> deny; failed_reclaim or acceptance_below_level -> allow | downside_permission bool consumed by filter above | both | none (PRD-151 documents) |
| verify-stale-timestamp-error | runtime/__init__.py:1343 | live/sunday summary older than 6h | verify fails; report stamped FAIL; CI exits 1 | publish | none |
| verify-kill-switch-no-trades | runtime/__init__.py:1350 | kill_switch AND candidates_qualified != 0 | verify fails | publish | none |
| verify-chaotic-no-trades | runtime/__init__.py:1352 | regime CHAOTIC AND qualified != 0 | verify fails | publish | none |
| verify-stay-flat-no-trades | runtime/__init__.py:1354 | posture STAY_FLAT AND qualified != 0 | verify fails | publish | none |
| verify-neutral-min-rr | runtime/__init__.py:1356 | regime NEUTRAL AND min_rr_applied != 3.0 | verify fails | publish | none |
| safe-write-latest-timestamp-comparison (B) | runtime/__init__.py:1560 | new_ts > old_ts | latest_* artifact only overwritten by newer data | both | none (PRD-040 plausible) |
| hourly-contract-permission-halted | runtime/__init__.py:1746 | system_halted on hourly run | hourly summary permission = halt message | notification | none |
| data-status-fixture-ok | runtime/__init__.py:1940 | fixture-backed run | data_status always "ok" regardless of quote age | publish | none |
| data-status-sunday-stale | runtime/__init__.py:1942 | mode == MODE_SUNDAY non-fixture | data_status always "stale" | publish | none |
| data-status-live-empty-quotes | runtime/__init__.py:1944 | live AND no normalized quotes | data_status "stale" | publish | none |
| data-status-staleness-threshold | runtime/__init__.py:1946 | any quote age > config.FRESHNESS_SECONDS | data_status "stale" | publish | none |
| kill-switch-computation | runtime/__init__.py:1956 | VIX > 35 OR VIX pct_change > 15% OR abs(SPY pct_change) > 3% | returns True; feeds summary kill_switch + qualified-count zeroing | publish | none |
| min-rr-regime-branch | runtime/__init__.py:1963 | regime NEUTRAL -> NEUTRAL_RR_RATIO; EXPANSION -> EXPANSION_RR_RATIO; else MIN_RR_RATIO | min_rr_applied in summary/dashboard; feeds sizing | publish | none (regime_model.md documents) |
| summary-regime-null-fallback | runtime/__init__.py:1974 | regime is None | summary shows NEUTRAL/STAY_FLAT defaults; permission "No new trades permitted." | both | none |
| sunday-mode-auto-conversion | runtime/__init__.py:2011 | requested LIVE AND Sunday AND ET >= 15:30 | effective mode silently becomes MODE_SUNDAY (regime-only run) | publish | none |
| sector-router-state-path-fixture-none (B) | runtime/__init__.py:2087 | mode == MODE_FIXTURE | sector router state file not read/written; result may differ from live | publish (fixture) | none |
| engine-health-gate | runtime/__init__.py:2148 | config engine_doctor runtime gate on AND engine_doctor exits non-zero | SystemExit before any pipeline stage | publish | none (PRD-020 plausible) |
| ci-workflow-dispatch-vs-schedule-mode | .github/workflows/cuttingboard.yml:96 | event == workflow_dispatch | operator-supplied DISPATCH_MODE overrides time-based routing | publish/notification | none |
| ci-sunday-detection | cuttingboard.yml:98 | UTC day-of-week == 7 | job_mode = sunday regardless of time | publish | none |
| ci-time-based-mode-routing | cuttingboard.yml:100-115 | UTC time slot match (1250 prefetch, 1300 live, 1350 orb_trajectory, 1430 post_orb, 1630 midmorning, 1900/2000 power_hour, else noop) | selects which pipeline mode runs; controls what report/notification is produced | both | none |
| ci-noop-no-pipeline | cuttingboard.yml:115 | cron fires at unmatched time | nothing runs; no PUBLISH_READY, no commit/push | both | none |
| ci-verify-step-condition | cuttingboard.yml:159 | job_mode in {live, sunday, verify} | verify_run_summary only after live/sunday; intraday modes never verify | publish | none |
| ci-commit-msg-live-sunday-only | cuttingboard.yml:222 | job_mode live or sunday | structured commit message only for live/sunday | publish | none |
| ci-publish-ready-gate | cuttingboard.yml:253 | success() AND PUBLISH_READY == true | commit step runs only after successful pipeline step | publish | none |
| ci-push-gate | cuttingboard.yml:281 | success() AND PUBLISH_READY == true | push to remote only when publish-ready | publish | none |
| workflow-dispatch-force-slot | hourly_alert.yml:60 | event == workflow_dispatch | alert_runner gets --force-slot: window + same-slot gates bypassed on the FULL publish path (creds + commit + push present) | notification | PRD-141 |
| hourly-payload-missing-fresh-false | hourly_alert.yml:73 | hourly payload file absent | fresh=false; render/commit/push skipped; job green (exit 0) | notification | none |
| hourly-payload-mtime-freshness | hourly_alert.yml:79 | payload mtime < workflow start | fresh=false; publish steps skipped; job green | notification | none |
| hourly-freshcheck-gate | hourly_alert.yml:88 | success() AND fresh == true | render, readiness check, regime-history aggregation, commit, push all conditional on freshness | notification | none |
| preview-payload-missing-fail | dashboard_preview.yml:55 | preview payload absent | hard fail (exit 1) - inverse of hourly skip-green | preview | PRD-178 R5 (lines 1-12) |
| preview-payload-stale-fail | dashboard_preview.yml:60 | payload mtime < workflow start | hard fail (exit 1); no artifact uploaded | preview | PRD-178 R5 (line 48) |
| pages-deploy-on-hourly-completion (B) | pages.yml:6 | hourly workflow completed (any conclusion) OR push to main OR dispatch | GitHub Pages deploy triggered | publish (pages) | none |
| validate-sh invariant family | validate_cuttingboard.sh:178,266-281 | harness asserts: CHAOTIC->0 qualified; STAY_FLAT->0; kill_switch->0; NEUTRAL->min_rr 3.0; fixture file present | local harness FAIL/exit 1; no production effect | harness | none |

### 3.2 Report rendering and Telegram transport (output.py, reports/)

| Gate | LOC | Trigger | Effect | Path | Breadcrumb |
|---|---|---|---|---|---|
| halt-header-swap | output.py:249 | outcome == HALT | header shows SYSTEM HALT banner; session-context lines suppressed | publish | none |
| regime-none-header-suppress | output.py:251 | regime is None (non-halt) | Timestamp/Session/Regime/VIX/Bias header block omitted | publish | none |
| sunday-permission-matrix | output.py:266 | date is Sunday AND regime present AND not halt | weekly permission-matrix block inserted (Sundays only) | publish | none |
| expansion-banner | output.py:271 | regime == EXPANSION, not halt | "EXPANSION MODE - Momentum allowed / Bias: LONG" banner | publish | none |
| halt-body | output.py:277 | outcome == HALT | body = "HALT - MACRO DATA INVALID" + halt_reason; all trade content suppressed | publish | none |
| no-trade-expansion-vs-plain | output.py:282 | NO_TRADE AND regime EXPANSION | wording swap: expansion-specific no-trade message | publish | none |
| no-trade-regime-short-circuit-reason | output.py:286 | NO_TRADE AND qual.regime_short_circuited | reason line = regime_failure_reason instead of posture reason | publish | none |
| no-trade-posture-reason | output.py:288 | NO_TRADE, not short-circuited, regime present | reason = "{posture} posture - no qualifying setups"; suppressed if regime None | publish | none |
| chain-filter-trade-setups | output.py:296-303 | setup chain classification != VALIDATED | failed setups excluded from rendered A+ TRADES list | publish | none |
| entry-mode-tag | output.py:315-316 | mode set and != DIRECT | "[mode]" tag appended to trade line | publish | none |
| chain-detail-line family | output.py:329-339 | chain result exists for symbol; OI/spread/expiry fields present | chain detail line + optional OI/spread/exp fields appended; plural/singular contract label | publish | none |
| continuation-audit-block | output.py:345-350 | EXPANSION AND qual summary AND continuation_audit present | [CONTINUATION_AUDIT] section with rejection-reason counts | publish | none |
| watchlist-section-suppress-halt | output.py:373 | not halt AND watch_summary non-empty | WATCHLIST section rendered; else suppressed | publish | none |
| near-a-plus-section | output.py:386 | not halt AND qual.symbols_watchlist > 0 | NEAR_A_PLUS section rendered | publish | none |
| excluded-section | output.py:393 | qual.symbols_excluded > 0 | EXCLUDED section rendered | publish | none |
| chain-issues-section | output.py:401-406 | any chain result != VALIDATED | CHAIN ISSUES section listing failed symbols | publish | none |
| summary-section-suppress-halt | output.py:415 | not halt AND regime present | SUMMARY block rendered; suppressed on halt / regime None | publish | none |
| execution-posture-source | output.py:421-424 | watch_summary present | posture from watch_summary; else derived "No Trade"/"A+ Only" from STAY_FLAT | publish | none |
| vix-display-na | output.py:432-433 | regime or vix_level None | DATA STATUS shows N/A for VIX | publish | none |
| payload-outcome-from-run-status | output.py:479-484 | render_report_from_payload: ERROR -> HALT; top_trades -> TRADE; else NO_TRADE | report body branch chosen from payload instead of pipeline objects | preview/payload renders | none |
| telegram-no-config-skip | output.py:550-571 | TELEGRAM_BOT_TOKEN or CHAT_ID unset | send suppressed; audit row status=skipped reason=not_configured; returns False | notification | none |
| telegram-dedup-transport | output.py:577-585 | message hash already sent this run | suppressed reason=duplicate at transport level | notification | none (PRD-017 documents) |
| telegram-retry family | output.py:607-612 | HTTP 429 or 5xx on first attempt | one retry after backoff | notification | none (PRD-017 documents) |
| telegram-body-footer-append | output.py:690-691 | body non-empty AND dashboard URL absent | dashboard footer appended | notification | none (PRD-039 plausible) |
| telegram-dedup-logical | output.py:694-702 | logical hash (title, body) already seen in run scope | suppressed reason=duplicate_path before transport | notification | none (PRD-017 documents) |
| notification-alert-reason | output.py:820-831 | has_candidates true | reason "candidates gated"; else stay_flat_reason / regime_failure_reason / error / "no setups" | notification | none |
| notification-watch-lines-cap | output.py:836 | more than 2 candidates | only first 2 shown in WATCH lines | notification | none |
| notification-direction-invalidation-wording | output.py:848-850 | direction SHORT vs LONG | invalidation wording above/below stop | notification | none |
| notification-outcome-inference | output.py:862-868 | outcome field absent/unrecognized | infer HALT from FAIL/ERROR, TRADE from allowed candidates, else NO_TRADE | notification | none |
| notification-primary-candidate-full-alert | output.py:874-902 | ALLOW_TRADE candidates exist with parseable entry + rr | full trade alert (direction/entry/RR/ORB/invalidation); else falls to watchlist path | notification | none |
| notification-orb-line | output.py:882-884 | parseable ORB high+low | ORB line included; omitted if missing | notification | none |
| notification-secondary-candidates | output.py:885-896 | extra candidates with parseable rr | up to 4 secondary lines appended | notification | none |
| notification-invalidation-line | output.py:897-899 | parseable stop price | INVALIDATION block included | notification | none |
| notification-sunday-premarket-title | output.py:900-901,914-915 | session_type SUNDAY_PREMARKET | "[PREMARKET]" title prefix | notification | none (PRD-077 documents) |
| notification-candidates-vs-stayflat-branch | output.py:904-912 | any tradable candidates | ACTIVE-NO-SETUP path with WATCHLIST lines vs STAY FLAT path with flat reason | notification | none |
| notification-regime-trigger-conditions family | output.py:747-754 | regime label RISK OFF / RISK ON / EXPANSION / NEUTRAL / other | different TRIGGERS lines in body | notification | none |
| premarket-tradable-invalidation family | reports/premarket.py:353-356 | not tradable; stay_flat_reason present vs absent | stay-flat reason (or generic line) prepended to invalidation list | publish (report artifact) | none |
| premarket-gap-direction-scenarios | reports/premarket.py:275-286 | market_regime value | selects regime-specific scenario list | publish (report artifact) | none (PRD-030 plausible) |
| premarket-gap-sub-scenarios family | reports/premarket.py:15-238 | gap_direction UP/DOWN/FLAT/None per regime builder | different scenario content | publish (report artifact) | none (PRD-030 plausible) |
| premarket-invalidation-regime-branch | reports/premarket.py:293-315 | regime grouping | different invalidation strings | publish (report artifact) | none |
| premarket-focus-list-cap | reports/premarket.py:343-349 | more than 5 candidates | focus list capped at 5 | publish (report artifact) | none |
| postmarket-levels-vs-legacy-evr | reports/postmarket.py:119-122 | levels parameter present | EVR via level-interaction vs legacy regime matching | publish (report artifact) | none (PRD-029 plausible) |
| postmarket-evr-no-runs | reports/postmarket.py:48-49,87-88 | no valid prior runs | EVR forced NO_EXPECTATION | publish (report artifact) | none |
| postmarket-evr-direction/neutral family | reports/postmarket.py:61-78 | prior vs realized direction match/mismatch; both NEUTRAL | EVR MATCH / PARTIAL / MISS | publish (report artifact) | none |
| postmarket-level-interaction family | reports/postmarket.py:26-36 | LONG above prior high / SHORT below prior low / price missing | MATCH vs PARTIAL | publish (report artifact) | none |
| postmarket-evr-legacy-regime-match | reports/postmarket.py:94-98 | regime+tradable persistence vs flip | MATCH / PARTIAL / MISS | publish (report artifact) | none |
| postmarket-observations family | reports/postmarket.py:130-164 | continuation enabled/rejected, qualified count, correlation present, stay-flat reason | observation lines appended/omited in payload | publish (report artifact) | none |
| levels-no-valid-runs | reports/levels.py:19 | run history empty after ERROR filter | prior high/low/close all None; downstream scenarios degrade | publish (report artifact) | none |
| levels-gap-direction family | reports/levels.py:33-38 | price vs prior close +/-0.1% bands; inputs missing -> None | gap_direction UP/DOWN/FLAT/None feeds scenario selection | publish (report artifact) | none |
| levels-range-mid-none | reports/levels.py:42-43 | prior high or low missing | range_mid None; scenario text degrades | publish (report artifact) | none |

### 3.3 Dashboard renderer (delivery/dashboard_renderer.py, html_renderer.py)

html_renderer.py (47 lines) has no gates of its own; it delegates to
render_report_from_payload. All gates below are in dashboard_renderer.py.
The renderer is shared by publish and CI-preview (same invocation); "both"
below means publish + CI preview. Local preview bypasses the publish gates
via the non-ui output path (sec. 4).

| Gate | LOC | Trigger | Effect | Path | Breadcrumb |
|---|---|---|---|---|---|
| trend-composite-unavailable family | dashboard_renderer.py:113-118 | SMA tokens DATA_UNAVAILABLE / INSUFFICIENT_HISTORY / NOT_COMPUTED | SMA Composite column shows degradation phrase instead of position | both | PRD-131 |
| intraday-rvol-threshold | dashboard_renderer.py:154-156 | relative_volume >= 1.5 | RVOL band phrase ">= 1.5x" vs "< 1.5x" | both | PRD-132 |
| intraday-vwap-unavailable family | dashboard_renderer.py:161-169 | price_vs_vwap NOT_COMPUTED or not in {ABOVE, BELOW, AT_LEVEL} | "VWAP not applicable" / "Intraday context unavailable" | both | PRD-132 |
| inactive-session-freshness-window | dashboard_renderer.py:348-350 | session_type in INACTIVE_SESSION_TYPES (SUNDAY_PREMARKET) | PRD-119 freshness window expands 180 min -> 72 h | publish | PRD-119, PRD-117 |
| output-under-ui-check | dashboard_renderer.py:411 | output path NOT under ui/ | validate_coherent_publish is a NO-OP: PRD-118 coherence + PRD-119 freshness entirely skipped | local preview trips it; publish + CI preview do not | PRD-118, PRD-119 |
| prd118-artifact-missing | dashboard_renderer.py:419-426 | payload/run/market_map not a dict (ui/ publish) | CoherentPublishError; publish blocked, nothing written | publish | PRD-118 |
| prd118-generation-id-missing | dashboard_renderer.py:431-438 | any generation_id absent (ui/ publish) | CoherentPublishError | publish | PRD-118 |
| prd118-fixture-mode-kwarg | dashboard_renderer.py:440-441 | fixture_mode=True (ui/ publish) | CoherentPublishError | publish | PRD-118 |
| prd118-fixture-mode-env | dashboard_renderer.py:442-443 | FIXTURE_MODE=1 env (ui/ publish) | CoherentPublishError | publish | PRD-118 |
| prd118-fixture-substring-in-gid | dashboard_renderer.py:446-453 | "fixture" in any generation_id (ui/ publish) | CoherentPublishError | publish | PRD-118 |
| prd118-generation-id-mismatch | dashboard_renderer.py:455-458 | payload/run/market_map generation_ids differ (ui/ publish) | CoherentPublishError | publish | PRD-118 |
| prd119-stale-payload-timestamp | dashboard_renderer.py:488-493 | payload age > 180 min live / 72 h inactive (ui/ publish) | StalePublishError; publish blocked | publish | PRD-119, PRD-117 |
| artifact-lineage-missing | dashboard_renderer.py:531-537 | payload/run/market_map unavailable or generation_id None | lineage MISSING -> unhealthy; candidate board + trend structure disabled | both | PRD-118 |
| artifact-lineage-mixed | dashboard_renderer.py:538-539 | two or more generation_ids differ | lineage MIXED -> banner + sections disabled | both | PRD-118 |
| artifact-lineage-market-map-stale | dashboard_renderer.py:540-541 | market_map older than baseline by > 300 s | lineage STALE -> sections disabled | both | PRD-116 |
| ts-health-inactive-no-snapshot | dashboard_renderer.py:837-843 | trend snapshot missing AND inactive session | source health INACTIVE_SESSION (not MISSING) for label coherence | both | PRD-123, PRD-117 |
| ts-health-usable-count-zero | dashboard_renderer.py:850-855 | snapshot fresh but no usable symbol rows | MARKET_CLOSED (inactive) / AWAITING_DATA (active) | both | PRD-123 |
| decision-title-halt | dashboard_renderer.py:1250-1251 | status FAIL/ERROR or system_halted | title = SYSTEM HALT regardless of outcome | both | none |
| sunday-vix-context family | dashboard_renderer.py:1304-1311 | VIX > 25 / < 18 / pct > 15 | volatility phrase elevated / low / "chaotic spike" suffix | both | none |
| sunday-monday-watch family | dashboard_renderer.py:1320-1325 | posture risk-on group / risk-off group / CHAOTIC | Monday Watch guidance phrase | both | none |
| history-runs-needs-two-for-previous | dashboard_renderer.py:1344-1348 | fewer than 2 run files | previous_run None; run-delta shows NO_PREVIOUS_RUN | publish | none |
| level-diagram-no-price-data | dashboard_renderer.py:1358-1360 | contract_entry None or <= 0 | "Chart unavailable - no price data"; SVG omitted | both | none |
| level-diagram-vwap-line | dashboard_renderer.py:1451-1460 | VWAP watch zone with level > 0 | VWAP dashed line on diagram | both | none |
| card-lifecycle-badge | dashboard_renderer.py:1485-1487 | grade_transition in badge CSS map | colored lifecycle badge on symbol | both | none (PRD-057 plausible) |
| card-low-grade-layout | dashboard_renderer.py:1492-1506 | grade not in HIGH_GRADES (C/D/F/unknown) | compact failed layout: FAILURE REASON only; all trade-action fields suppressed | both | PRD-158 |
| card-grade-action-label | dashboard_renderer.py:1509-1511 | grade A+/A "Tradeable", B "Developing", else None | GRADE row rendered or omitted | both | PRD-158 |
| card-high-grade field family | dashboard_renderer.py:1516-1557 | per-field presence on high-grade cards: lifecycle, setup_state (!= DATA_UNAVAILABLE), if_now, entry, invalidation, downgrade risk, reason, play, watch items (!= unavailable sentinel) | each field row rendered only when present; silently omitted otherwise | both | PRD-165 (entry/invalidation); none for rest |
| card-level-diagram | dashboard_renderer.py:1570-1571 | valid positive anchor AND fib/watch-zone context | SVG level diagram rendered; else omitted | both | PRD-074, PRD-158 |
| contract-stale-nullification | dashboard_renderer.py:1670-1671 | contract older than payload/run baseline by > 300 s | contract entry prices dropped from cards; diagrams lose ENTRY anchor | both | PRD-116 |
| macro-drivers-fallback-to-snapshot | dashboard_renderer.py:1681-1683 | payload macro_drivers empty or all UNAVAILABLE | macro drivers loaded from sidecar snapshot file instead | both | none (PRD-072 plausible) |
| permission-fallback-from-payload | dashboard_renderer.py:1692-1693 | run.permission None | permission read from payload.summary | both | none |
| system-state-title-mixed-artifacts | dashboard_renderer.py:1694 | artifact_mixed | title = MIXED_ARTIFACTS instead of outcome title | both | PRD-116 |
| integrator-skipped-no-market-map | dashboard_renderer.py:1742-1752 | market_map None or no symbols | dashboard_integrator not called; no verdicts, no suppression | both | PRD-158 |
| artifact-mixed-banner | dashboard_renderer.py:1788-1800 | generation_ids_mixed | prominent MIXED_ARTIFACTS warning block + per-artifact ids | both | PRD-116 |
| sunday-coherent-banner | dashboard_renderer.py:1802-1805 | COHERENT + SUNDAY_PREMARKET + Sunday PT timestamp | "SUNDAY PRE-MARKET CONTEXT - NO CASH SESSION" banner | both | PRD-116 |
| fixture-mode-market-map-override | dashboard_renderer.py:1807-1811 | fixture_mode=True | market_map.symbols replaced with FIXTURE_SYMBOLS; mm status forced FRESH | preview/tests (PRD-118 blocks ui/) | PRD-118, PRD-078 |
| mm-setup-count-health-gate (B) | dashboard_renderer.py:1844-1846 | mm health != OK | rendered setup count forced 0 (feeds PRD-120 diagnostics) | both | PRD-120 |
| system-state-outcome-suppressed | dashboard_renderer.py:1860-1862 | integrator suppress.outcome | Outcome row omitted from System State | both | PRD-158 |
| system-state-permission-ladder | dashboard_renderer.py:1870-1892 | priority ladder: halted -> "HALTED"; integrator-suppressed -> omitted; stay_flat_reason -> warn text; permission value -> shown; unhealthy lineage -> "UNKNOWN" (R3.5); coherent+None+NO_TRADE/STAY_FLAT -> "MONITOR_ONLY" (R3.6); else "UNKNOWN" (R3.7) | permission display value selected by first matching rung | both | PRD-158, PRD-120 |
| system-state-flags family | dashboard_renderer.py:1893-1901 | system_halted / kill_switch / errors present | Halted: YES, Kill Switch: YES, Error rows rendered | both | none |
| system-state-reason-lines | dashboard_renderer.py:1903-1914 | halted+stay_flat_reason; or not-halted+no permission | Reason row: halt reason, first error, "candidates gated", or "no qualified candidates" | both | none |
| alert-watchlist-section | dashboard_renderer.py:1926-1937 | alert_candidates non-empty | Alert Watchlist block listing gated candidates (+ block_reason suffix when present) | both | none |
| sunday-macro-context-section | dashboard_renderer.py:1940-1962 | sunday_coherent | full Sunday Macro Context block; omitted otherwise | both | PRD-116 |
| macro-tape-no-data-label | dashboard_renderer.py:1967-1968 | macro_drivers empty or all UNAVAILABLE | "NO LIVE MACRO DATA" label | both | none |
| macro-bias-suppressed-by-integrator | dashboard_renderer.py:1976-1977 | integrator suppress.macro_bias | raw MACRO BIAS line omitted | both | PRD-158, PRD-160 |
| macro-pressure-data-available | dashboard_renderer.py:2052-2070 | drivers present AND pressure dict | pressure summary block vs "MACRO PRESSURE UNAVAILABLE" | both | none |
| macro-pressure-component-phrase-filter | dashboard_renderer.py:2063-2065 | component phrase resolves None (neutral/unknown) | component row omitted from pressure grid | both | PRD-158 |
| red-folder-error-state | dashboard_renderer.py:2079-2081 | red_folder.ok False | "RED FOLDER UNAVAILABLE: {error}"; event list omitted | both | PRD-176 |
| red-folder-events-present | dashboard_renderer.py:2084-2098 | events in window vs none | event rows vs "No red-folder events in the next 48 hours." | both | PRD-176, PRD-177 |
| red-folder-expiry-warning | dashboard_renderer.py:2099-2100 | schedule expiring | refresh-calendar warning line | both | PRD-176 |
| trend-structure-market-closed-label | dashboard_renderer.py:2109-2112 | ts health MARKET_CLOSED / AWAITING_DATA | closed label + optional last-snapshot timestamp | both | PRD-123 |
| trend-structure-unhealthy-lineage | dashboard_renderer.py:2113-2118 | lineage MIXED/STALE/MISSING | section disabled with diagnostic label; rows omitted | both | PRD-116 |
| trend-structure-inactive-session | dashboard_renderer.py:2119-2121 | inactive session, healthy lineage | "SESSION INACTIVE"; no table | both | PRD-117 |
| trend-structure-records-none | dashboard_renderer.py:2123-2124 | snapshot missing/malformed or any required field absent (all-or-nothing) | "no trend structure data"; dash placeholders | both | PRD-112 |
| trend-structure-column-collapse | dashboard_renderer.py:2172-2187 | every row unavailable for a collapsible column (vs VWAP, vs SMA200, Alignment, Entry Context) | column omitted entirely | both | PRD-165 |
| candidate-board-disabled-class | dashboard_renderer.py:2199 | unhealthy lineage | board gets .disabled CSS | both | PRD-116 |
| fixture-mode-header-label | dashboard_renderer.py:2200-2203 | fixture_mode | "DEMO MODE - FIXTURE DATA" heading | preview/tests | none (PRD-078 plausible) |
| integrator-verdicts-unhealthy-suppressed | dashboard_renderer.py:2223 | unhealthy lineage | ALL integrator verdict lines suppressed; lineage diagnostic shown instead | both | PRD-116, PRD-158 |
| prd168-rule2-verdict-suppression | dashboard_renderer.py:2223-2227 | high-grade card present AND verdict is RULE2 long/short | that verdict line suppressed (card already communicates it) | both | PRD-168 |
| candidate-board-unhealthy-lineage | dashboard_renderer.py:2228-2247 | unhealthy lineage | cards + tier headers suppressed; diagnostic text (STALE detail at 2232-2240, SOURCE_MISSING/PARSE_ERROR at 2241-2242, generic otherwise) | both | PRD-116 |
| candidate-board-source-missing-healthy | dashboard_renderer.py:2248-2249 | mm status SOURCE_MISSING/PARSE_ERROR, healthy lineage | status string only; no cards | both | none |
| candidate-board-inactive-session | dashboard_renderer.py:2250-2252 | inactive session | "SESSION INACTIVE"; no cards | both | PRD-117 |
| candidate-board-stale-mm-warning | dashboard_renderer.py:2254-2255 | mm status STALE | STALE label prepended; cards still render | both | none |
| candidate-board-market-map-none | dashboard_renderer.py:2256-2257 | market_map None | "N/A"; no cards | both | none |
| candidate-board-no-symbols | dashboard_renderer.py:2260-2261 | symbols dict empty | "NO_CANDIDATES" label | both | none |
| integrator-skip-lines | dashboard_renderer.py:2266-2267 | integrator symbol_skips non-empty | one skip line per symbol; symbols excluded from tiers | both | PRD-158 |
| candidate-board-no-actionable-notice | dashboard_renderer.py:2272-2277 | symbols exist but none high-grade | "NO ACTIONABLE SETUPS / Market is not offering structure" | both | none |
| tier-empty-suppression | dashboard_renderer.py:2281-2283 | tier empty after filtering | tier group omitted | both | PRD-158 |
| low-tier-collapsible | dashboard_renderer.py:2284-2299 | tier has only C/D/F grades | tier rendered as collapsible details element | both | none |
| removed-symbols-section | dashboard_renderer.py:2300-2308 | market_map.removed_symbols non-empty | REMOVED tier listing downgraded-out symbols | both | none (PRD-057 plausible) |
| run-delta-no-previous-run | dashboard_renderer.py:2314-2315 | previous_run None | NO_PREVIOUS_RUN; deltas omitted | both | none (PRD-041 plausible) |
| run-delta-regime-flip | dashboard_renderer.py:2324-2326 | regime changed AND current is RISK_ON/RISK_OFF | "Permission flipped to longs/shorts" line; other transitions produce nothing | both | PRD-158 |
| run-delta-field-changed | dashboard_renderer.py:2335-2342 | posture or halted changed; else nothing changed | "previous -> current" rows; or "No changes since last run" | both | none |
| scoreboard-history-present | dashboard_renderer.py:2352-2371 | regime_history non-empty | rows rendered reverse-chronological; else "No regime history yet." | both | PRD-175, PRD-177 |
| scoreboard-10-row-cap | dashboard_renderer.py:2353 | more than 10 rows | only 10 most recent; older silently omitted | both | PRD-177 |
| scoreboard-spy-change-present | dashboard_renderer.py:2361 | spy_close_change_pct not None | signed pct vs "n/a" | both | PRD-175, PRD-177 |
| history-runs-cap (B) | dashboard_renderer.py:2531 | more than 5 run files | only 5 most recent loaded (currently not rendered in body) | publish | none |

### 3.4 Delivery: integrator, payload, transport, regime history

| Gate | LOC | Trigger | Effect | Path | Breadcrumb |
|---|---|---|---|---|---|
| rule1-missing-required-fields | delivery/dashboard_integrator.py:73 | any required symbol field (current_price, setup_direction, setup_type, trigger, invalidation) absent/empty | symbol added to symbol_skips with trader-facing line; excluded from rendered tiers and direction calc | both | PRD-158 4.3 (docstring line 7); DECISIONS.md guardrail (line 8) |
| rule1-non-dict-symbol-fields (B) | delivery/dashboard_integrator.py:114 | symbol fields not a dict | same suppression as rule 1 | both | PRD-158 4.3 |
| rule2-no-long-setups | delivery/dashboard_integrator.py:143 | permission "longs" AND no long setups qualify | RULE2_LONG_VERDICT emitted; permission + outcome rows suppressed in favor of verdict | both | PRD-158 4.3 |
| rule2-no-short-setups | delivery/dashboard_integrator.py:145 | permission "shorts" AND no short setups | RULE2_SHORT_VERDICT; same suppression | both | PRD-158 4.3 |
| rule3-directional-conflict | delivery/dashboard_integrator.py:91 | regime permission, macro bias, and setup directions all expressed AND any two disagree | RULE3_MIXED_VERDICT; macro_bias + permission + outcome all suppressed | both | PRD-158 4.3 |
| rule3-short-circuit family | delivery/dashboard_integrator.py:157-161 | permission not longs/shorts; or macro bias not long/short; or no qualifying directions | Rule 3 conflict never fires (no collapse) | both | PRD-158 4.3 |
| rule4-empty-tier-suppression | delivery/dashboard_integrator.py:101-103 | tier empty after Rule 1 drops | tier omitted from rendered_tiers | both | PRD-158 4.3 |
| top-trades-actionability-filter | delivery/payload.py:47 | candidate fails candidate_is_actionable (NON_TRADABLE symbol, status != ALLOW_TRADE, or size_multiplier <= 0) | excluded from sections.top_trades (remains in detail sections) | publish | PRD-162 (line 42) |
| watchlist-vs-rejected-stage-routing | delivery/payload.py:49-50 | rejection stage == WATCHLIST vs other | record routed to sections.watchlist vs sections.rejected | publish | PRD-011 (docstring) |
| continuation-audit-omission | delivery/payload.py:53-57 | continuation_audit_present falsy | sections.continuation_audit = None; block absent from render | publish | none |
| watch-summary-omission | delivery/payload.py:93-95 | intraday_state None | watch_summary_detail = None; intraday block omitted | publish | none |
| validation-halt-omission | delivery/payload.py:99-100 | stay_flat_reason None | validation_halt_detail = None | publish | none |
| session-type-omission | delivery/payload.py:114-115 | session_type None | meta.session_type key absent | publish | none |
| fixture-mode-meta-flag | delivery/payload.py:116-117 | fixture_mode=True | meta.fixture_mode=True; downstream renderer publish-block keys on it | both | PRD-078 (fixtures.py docstring) |
| transport-mode-dispatch | delivery/transport.py:68-73 | mode html / json / cli | selects which artifact is emitted (report.html, latest_payload.json, or stdout) | publish | none |
| regime-history-event-record-exclusion | delivery/regime_history.py:48-49 | audit record has "event" key (notification rows) | excluded from scoreboard aggregation | sidecar (publish render input) | PRD-175 R2 (docstring line 35) |
| regime-history-required-fields-exclusion | delivery/regime_history.py:50 | record lacks outcome / run_at_utc / date | excluded from aggregation | sidecar | PRD-175 R1 (docstring line 28) |
| regime-history-spy-gap family | delivery/regime_history.py:95-103 | regime date absent from SPY closes; last date in series; zero close | spy_close_change_pct = None for that row | sidecar | PRD-175 |

macro_tape_layout.py and fixtures.py contain no gates (static data
definitions). transport.py's invalid-mode branch raises (excluded by
definition).

### 3.5 Notification layer (notifications/, alert_runner.py)

No code in this layer checks for a preview mode; preview safety is achieved
upstream by credential stripping (sec. 4). All paths below are "notification".

| Gate | LOC | Trigger | Effect | Path | Breadcrumb |
|---|---|---|---|---|---|
| alert-runner-force-slot-bypass | alert_runner.py:45,60-63 | --force-slot flag or CUTTINGBOARD_FORCE_SLOT=1 | window check AND same-slot dedup both bypassed; fetch+notify always attempted | notification | PRD-141, PRD-149 |
| alert-runner-outside-window-suppress | alert_runner.py:64-80 | routine_pt_slot returns None (outside allowed PT slots or > 25 min lag) | entire hourly alert suppressed; audit reason=outside_routine_window; exit 0 | notification | PRD-149 (docstring) |
| alert-runner-same-slot-suppress | alert_runner.py:82-93 | saved slot_utc == current slot | suppressed; audit reason=suppressed_same_slot; exit 0 | notification | PRD-141 (docstring) |
| routine-pt-slot-future-skip | notifications/hourly_slot.py:68 | candidate slot in future | future slots never selected | notification | PRD-149 |
| routine-pt-slot-max-lag | notifications/hourly_slot.py:70 | slot lag > 25 min | stale slots excluded -> outside-window suppression | notification | PRD-149 |
| routine-pt-slot-no-match | notifications/hourly_slot.py:74 | no allowed slot matches | returns None -> suppression at alert_runner:64 | notification | PRD-149 |
| is-premarket-slot-tolerance (DEAD in prod) | notifications/hourly_slot.py:90 | now within +/-5 min of declared premarket UTC minute | returns True; NO production caller - test pins alert_runner must NOT reference it (tests/test_prd050_alert_runner.py:249-252) | none (dead) | PRD-141 (superseded by PRD-149 R6) |
| load-last-slot-missing-or-malformed | notifications/hourly_slot.py:105-108 | state file missing/unparseable | returns None -> dedup gate passes, alert proceeds | notification | PRD-141 |
| state-should-send-no-prior-state | notifications/state.py:105 | last_key None | always send (R6) | notification | PRD-018 |
| state-should-send-critical-high | notifications/state.py:107 | priority CRITICAL or HIGH | always send, bypasses dedup (R5) | notification | PRD-018 |
| state-should-send-unchanged-key | notifications/state.py:109 | current_key == last_key (MEDIUM/LOW) | suppress - state unchanged (R3) | notification | PRD-018 |
| classify-priority family | notifications/state.py:75-86 | status ERROR -> CRITICAL; stale_data_detected -> CRITICAL; tradable -> HIGH; trade_candidates -> MEDIUM | priority feeds should_send breakthrough | notification | PRD-018 |
| should-suppress family (DEAD in prod) | notifications/__init__.py:394-422 | midmorning/power_hour + (regime None; CHAOTIC; or STAY_FLAT + confidence < 0.55 + no watch/qualified) | would suppress IF called - docstring (lines 405-408) states it is NOT called from any live send path; test pins non-wiring (tests/test_notification_audit.py:237-243) | none (dead) | _SUPPRESS_CONFIDENCE=0.55 (line 56) |
| action-label family | notifications/__init__.py:137-148 | halted -> HALT; qualified+TRADE -> TRADE; qualified -> MONITOR SETUP; flat -> STAY FLAT | hourly title prefix selection | notification | none |
| focus-tokens family | notifications/__init__.py:162-179 | non-tradable symbols excluded; malformed lines excluded; cap 3 tokens | focus list content + truncation | notification | none |
| blockers-line-no-gates-failed | notifications/__init__.py:192-203 | no qual summary or no gates_failed | Blockers line suppressed | notification | none |
| pending-lines family | notifications/__init__.py:217-235 | no focus -> block suppressed; non-tradable/non-focus/structureless excluded; cap 3 | Pending-confirmation block content | notification | none |
| hourly-reason family | notifications/__init__.py:249-255 | halted -> halt reason; candidates -> "candidates gated"; regime_failure_reason; STAY_FLAT posture | reason line text selection | notification | none |
| lifecycle-alert-grade-filter | notifications/__init__.py:304-312 | UPGRADED; or NEW at A+/A/B; or DOWNGRADED from A+/A/B | only these transitions produce lifecycle alert lines | notification | _LIFECYCLE_HIGH_GRADES (line 57) |
| lifecycle-removed-high-grade-only | notifications/__init__.py:338-343 | REMOVED transition from A+/A/B | removed-symbol line; lower grades silent | notification | line 57 |
| lifecycle-not-dict / dedup / empty family | notifications/__init__.py:352,364-366,388-390 | market_map not dict; duplicate transition key; no lines | lifecycle lines suppressed / deduped / suffix omitted | notification | none |
| format-hourly-halt-reason-dropped (B) | notifications/__init__.py:515 | always (del halt_reason) | halt_reason param unconditionally discarded; HALT action label used instead | notification | none |
| format-hourly-trade-title-parsed | notifications/__init__.py:526-527 | action TRADE AND candidate lines parse | title "{direction} {symbol} {pt}" vs generic "TRADE {pt}" | notification | none |
| format-hourly optional blocks family | notifications/__init__.py:559-577 | blockers / macro block / tradables / pending present | each block appended only when non-empty | notification | none |
| format-telegram-dispatch ladder | notifications/formatter.py:60-76 | first match of: failure_reason -> FAILED; intraday_alert_type -> intraday; HALT; NOTIFY_HOURLY; ALERT_CONTEXT_RUN; qualified focus -> READY; forming focus -> FORMING; session-check modes; watchlist candidates; else no-trade | selects which alert format fires (order = priority) | notification | none |
| hourly-tradable-posture | notifications/formatter.py:84 | posture STAY_FLAT | candidate count forced 0; STAY FLAT title/body; setup content suppressed | notification | none |
| hourly-candidate-content family | notifications/formatter.py:105-110 | count > 0 with lines -> symbol title; count 0 + tradable -> NO SETUP; else STAY FLAT | hourly title/body selection | notification | none |
| run-summary-outcome-trade | notifications/formatter.py:123 | outcome TRADE | end-of-run alert -> setup-ready format vs no-trade | publish | none |
| intraday-alert-type family | notifications/formatter.py:133-148 | CHAOTIC / REGIME_SHIFT (+RISK_ON direction wording) / else VIX SPIKE | intraday alert content selection | notification | none |
| intraday-halt-reason-present | notifications/formatter.py:195 | halt_reason truthy | reason appended to SYSTEM HALT body | notification | none |
| no-trade-context-vix-line-modes | notifications/formatter.py:276 | mode in {None, PREMARKET, ORB_TRAJECTORY, MIDMORNING, POWER_HOUR} | VIX line included; excluded for POST_ORB, MARKET_CLOSE, HOURLY | notification | none |
| no-trade-context-validation-premarket | notifications/formatter.py:284 | PREMARKET AND symbols_attempted | "N/M validated" line (premarket only) | notification | none |
| no-trade-context-line-cap | notifications/formatter.py:287 | body > 5 lines | truncated to first 5 | notification | none |
| session-context family | notifications/formatter.py:293-300 | regime None / CHAOTIC / STAY_FLAT / RISK_OFF | session-check body phrase selection | notification | none |
| session-posture family | notifications/formatter.py:311-315 | None-CHAOTIC-flat -> "Stay flat"; NEUTRAL_PREMIUM -> "Stay selective"; DEFENSIVE_SHORT -> "Lean short" | posture line wording | notification | none |
| focus-candidates family | notifications/formatter.py:324-329 | qualified trades first; watch_summary fills to 3 | focus candidate selection + cap | notification | none |
| qualified-focus-check | notifications/formatter.py:341 | no qualified trades | returns None - READY alert never fires | notification | none |
| forming-focus family | notifications/formatter.py:348-352 | qual watchlist; else watch_summary; both empty -> None | FORMING alert source / suppression | notification | none |
| display-bias family | notifications/formatter.py:387-395 | regime None -> suppressed; LONG/SHORT/BALANCED/NO TRADE wording | bias line presence + wording | notification | none |
| session-line family | notifications/formatter.py:401-404 | PREMARKET -> "Off session"; watch_summary missing -> suppressed | session line | notification | none |
| vix-line family | notifications/formatter.py:414-416 | regime/level missing -> suppressed; pct change missing -> "+0.0%" | VIX line presence/content | notification | none |
| watch-reason-truncation | notifications/formatter.py:438 | reason > 30 chars | replaced with generic "setup forming" | notification | none |
| invalidation-line family | notifications/formatter.py:486-493 | watch item missing -> suppressed; level VWAP -> lose/reclaim wording; ORB -> "Back inside ORB" | invalidation line in READY/FORMING alerts | notification | none |

### 3.6 Upstream decision modules (qualification, decisions, policy)

These emit the statuses that the payload/renderer/notification gates above
key on. Shared by publish and preview paths ("both").

| Gate | LOC | Trigger | Effect | Path | Breadcrumb |
|---|---|---|---|---|---|
| qual-regime-short-circuit | qualification.py:151-166 | posture STAY_FLAT or confidence < MIN_REGIME_CONFIDENCE, checked before any per-symbol work | summary regime_short_circuited=True, empty qualified/watchlist; no trades anywhere downstream | both | docstring line 13 |
| qual-hard-gate1-stay-flat | qualification.py:302-308 | posture STAY_FLAT (per candidate) | hard reject "REGIME: ..." | both | comment line 301 |
| qual-hard-gate2-confidence | qualification.py:312-318 | confidence < MIN_REGIME_CONFIDENCE (0.50) | hard reject "CONFIDENCE: ..." | both | comment line 311 |
| qual-hard-gate3-direction | qualification.py:183-194,322-330 | candidate direction != direction_for_regime (when set) | hard reject "DIRECTION: ..."; excluded dict | both | comment line 321 |
| qual-hard-gate4-chop | qualification.py:177-179,333-340 | structure == CHOP | hard reject / excluded "CHOP"; never watchlisted | both | comment line 176 |
| qual-soft-gate5-stop-defined | qualification.py:350-353 | stop <= 0 or risk == 0 | soft failure GATE_STOP_DEF | both | comment line 349 |
| qual-soft-gate6-stop-distance | qualification.py:360-373 | stop < 1% of entry; or risk < 0.5 x ATR14 | soft failure GATE_STOP_DIST | both | comment line 355 |
| qual-soft-gate7-rr-ratio | qualification.py:376-393 | rr < regime-specific min (NEUTRAL_RR_RATIO / EXPANSION_RR_RATIO / MIN_RR_RATIO) | soft failure GATE_RR | both | comment line 375; PRD-157 (line 396) |
| qual-soft-gate8-max-risk | qualification.py:407-424 | one contract exceeds regime-scaled risk budget; zero budget; spread undefined | soft failure GATE_MAX_RISK; max_contracts/dollar_risk only set on pass | both | comment lines 395-397; PRD-157 |
| qual-soft-gate9-earnings | qualification.py:427-431 | has_earnings_soon is True (None passes - fail-open) | soft failure GATE_EARNINGS; in production always passes (input always None, PRD-176.md:99) | both | docstring line 10 |
| qual-soft-gate10-extension | qualification.py:434-445 | abs(entry-EMA21)/ATR14 > EXTENSION_ATR_MULTIPLIER; fail-open if metrics missing | soft failure GATE_EXTENSION | both | comment line 433 |
| qual-soft-gate11-time | qualification.py:448-451 | ET >= 15:30 (ENTRY_CUTOFF_ET); fails CLOSED on exception | soft failure GATE_TIME | both | comment line 447; config.py:141 |
| qual-soft-outcome-watchlist | qualification.py:473-486 | exactly 1 soft failure | WATCHLIST with single reason | both | docstring lines 7-8 |
| qual-soft-outcome-reject | qualification.py:488-501 | 2+ soft failures | hard reject "N soft gates failed" | both | docstring lines 7-8 |
| qual-flow-alignment | qualification.py:249-258; flow.py:137-145 | qualified result + dominant speculative flow OPPOSES direction (ratio >= 1.5x, OTM-ask >= 60%, premium >= FLOW_MIN_PREMIUM) | PASS downgraded to WATCHLIST "FLOW_ALIGNMENT: opposing speculative flow" | both | PRD-013 (comment line 248); PRD-015 (flow.py:47) |
| flow-gate-no-data-passthrough (B) | flow.py:66-80 | non-qualified, non-tradable symbol, or no qualifying prints | FlowAlignment NO_DATA - no downgrade | both | PRD-013 |
| continuation-reject family | qualification.py:609-661,676-677 | EXPANSION continuation path: DATA_INCOMPLETE, VIX_BLOCKED (> CONTINUATION_VIX_SPIKE_BLOCK), NO_BREAKOUT, NO_HOLD_CONFIRMATION, INSUFFICIENT_MOMENTUM (< CONTINUATION_MOMENTUM_K x ATR), EXTENDED_FROM_MEAN, STOP_TOO_TIGHT, RR_BELOW_THRESHOLD, TIME_BLOCKED | continuation candidate rejected with named reason; feeds continuation_audit | both | comment line 216; PRD-157 (lines 666-670) |
| trade-decision-chain-validation | trade_decision.py:155 | chain classification != VALIDATED | status BLOCK_TRADE; block_reason = chain reason | both | PRD-162 (line 92) |
| trade-decision-non-tradable-symbol | trade_decision.py:113-116 | symbol in config.NON_TRADABLE_SYMBOLS (macro drivers) | is_actionable False -> excluded from top_trades and OUTCOME_TRADE | both | PRD-162 |
| trade-decision-zero-size-multiplier | trade_decision.py:115 | size_multiplier <= 0.0 | is_actionable False | both | PRD-162 (docstring 102-108) |
| exec-policy-pre-policy-block | execution_policy.py:216-217 | decision already BLOCK_TRADE | policy_allowed False, size 0 | both | PRD-051 (docstring) |
| exec-policy-low-confidence | execution_policy.py:218-219 | confidence < 0.60 | BLOCK_TRADE reason low_confidence | both | PRD-051; trade_visibility.py:27 |
| exec-policy-chaotic-regime | execution_policy.py:220-221 | regime CHAOTIC | BLOCK_TRADE | both | PRD-051 |
| exec-policy-stay-flat | execution_policy.py:222-223 | posture STAY_FLAT | BLOCK_TRADE | both | PRD-051 |
| exec-policy-session-trade-limit | execution_policy.py:224-225 | prior trades >= EXECUTION_POLICY_MAX_TRADES_PER_DAY | BLOCK_TRADE session_trade_limit | both | PRD-051 |
| exec-policy-loss-lockout | execution_policy.py:226-227 | consecutive losses >= 2 | BLOCK_TRADE loss_lockout | both | PRD-051 |
| exec-policy-cooldown | execution_policy.py:228-229,276-280 | trade within EXECUTION_POLICY_COOLDOWN_MINUTES | BLOCK_TRADE cooldown; high grades -> NEAR_MISS | both | PRD-051; trade_visibility.py:25 |
| exec-policy-orb-inside-range | execution_policy.py:231-233,254-273 | price inside ORB range, data complete, not continuation | BLOCK_TRADE orb_inside_range; high grades -> NEAR_MISS | both | PRD-051; trade_visibility.py:24 |
| exec-policy-orb-unavailable (B) | execution_policy.py:234-235,260-266 | ORB data missing | still ALLOW_TRADE; policy_reason=orb_unavailable (visible in artifacts) | both | PRD-051 |
| exec-policy-macro-pressure-conflict | execution_policy.py:244-251 | RISK_OFF + LONG or RISK_ON + SHORT | BLOCK_TRADE macro_pressure_conflict; high grades -> NEAR_MISS | both | PRD-051, PRD-063; trade_visibility.py:23 |
| exec-policy-macro-pressure-size family | execution_policy.py:240-251 | MIXED -> x0.75; RISK_OFF+SHORT -> x0.5; RISK_ON+LONG -> x0.5 | size_multiplier reduced; contract count/dollar risk shrink in rendered artifact | both | PRD-051, PRD-063 |
| exec-policy-confidence-size-tier family | execution_policy.py:59-68 | confidence 0.60-0.70 -> 0.50; 0.70-0.80 -> 0.75; >= 0.80 -> 1.0 | size multiplier tier propagates to rendered sizing | both | PRD-051 |
| visibility-active-near-miss-blocked | trade_visibility.py:47-68 | policy_allowed -> ACTIVE; blocked + grade A+/A/B -> NEAR_MISS; blocked otherwise -> BLOCKED | visibility_status controls how much of the trade slot the dashboard renders | both | PRD-064 (docstring) |
| entry-quality-missing-entry | entry_quality.py:78-85 | no entry mode, structure, confirmation, or invalidation at all | MISSING_ENTRY blocking AVOID; ALLOW -> BLOCK_TRADE ENTRY_QUALITY_BLOCK | both | PRD-069 (docstring) |
| entry-quality-stale | entry_quality.py:88-95 | qualification flagged rejection_reason | STALE blocking WAIT; ALLOW -> BLOCK | both | PRD-069 |
| entry-quality-chase-risk | entry_quality.py:98-105 | thesis CONFLICTED + invalidation present | CHASE_RISK blocking AVOID | both | PRD-069 |
| entry-quality-extended | entry_quality.py:108-115 | entry mode + structure + thesis present but confirmation UNKNOWN | EXTENDED blocking WAIT | both | PRD-069 |
| entry-quality-clean-allow | entry_quality.py:118-125 | entry mode + confirmation present | CLEAN non-blocking ALLOW; decision passes unchanged | both | PRD-069 |
| confirmation-level-state family | confirmation.py:75-90 | BREAK_ONLY (< 3 holds) -> trades_allowed False; HOLD_CONFIRMED (>= 3) -> True; FAILURE_CONFIRMED (reclaim) -> True | LevelConfirmation feeds intraday state engine and the SHORT-permission filter | both | none in file; consumed at intraday_state_engine.py:458-488 |

trade_policy.py contains no gates by design: its own docstring (line 33)
states "policy_note is informational only - never drives gate logic."
(Contrast with docs/system_logic_map.md:56 - see flag 5.3-C2.)

### 3.7 State, regime, and watch modules

| Gate | LOC | Trigger | Effect | Path | Breadcrumb |
|---|---|---|---|---|---|
| noise-window-suppress | intraday_state_engine.py:435 | bar ET time < 09:45 | compute_intraday_state returns None; no IntraState for symbol (feeds fail-open at runtime:1136) | both | none |
| gap-classification-missing-prev-close | intraday_state_engine.py:183-184 | prev_close None or <= 0 | gap_type FLAT -> gap-down gating bypassed entirely, shorts permitted | both | PRD-151 context |
| gap-down-classify-threshold | intraday_state_engine.py:187-191 | (open-prev)/prev <= -0.25% DOWN; >= +0.25% UP; else FLAT | DOWN activates downside permission subsystem; UP/FLAT bypass | both | PRD-151 (_GAP_THRESHOLD 0.0025) |
| gap-down-open-phase-block | intraday_state_engine.py:246-247 | gap DOWN AND phase OPEN (< 5 min) | downside permission False -> trades_allowed False for shorts | both | PRD-151 |
| gap-down-unconfirmed-break-block | intraday_state_engine.py:249-253 | gap DOWN, OR-low broken, neither failed_reclaim nor acceptance | permission False | both | PRD-151 |
| gap-down-unlock family | intraday_state_engine.py:254-258 | failed_reclaim OR acceptance_below_level (>= 2 closes below) | permission True - shorts unblocked | both | PRD-151 |
| short-direction-permission-apply | intraday_state_engine.py:475-476 | break_direction SHORT | trades_allowed AND downside_permission - final combiner | both | PRD-151 |
| no-break-direction-range-state | intraday_state_engine.py:479-480 | no ORB break | state RANGE; confidence capped 0.40 | both | none |
| failure-confirmed-state | intraday_state_engine.py:481-482 | confirmation FAILURE_CONFIRMED | state FAILED_EXPANSION; confidence decays 0.10/bar | both | none |
| expansion-confirmed-state | intraday_state_engine.py:488-489 | HOLD_CONFIRMED + >= 3 holding bars + VWAP aligned | state EXPANSION_CONFIRMED; confidence up to 1.0 | both | none |
| time-window-confidence-penalty family (B) | intraday_state_engine.py:369-372 | MIDDAY -0.15; SECONDARY -0.10 | rendered confidence reduced | both | none |
| expansion-regime-early-return | regime.py:139-154 | SPY>0 AND QQQ>0 AND VIX <= -1.0% AND >= 70% advancing AND >= 2 leadership names up >= 1.5% | regime EXPANSION, posture EXPANSION_LONG, confidence 1.0; vote model bypassed | both | none (PRD-008 plausible) |
| vix-chaotic-spike-override | regime.py:290-291 | vix_pct_change > 0.15 | regime CHAOTIC immediately; posture STAY_FLAT; overnight FORCE_EXIT | both | config.py:102 VIX_CHAOTIC_SPIKE; regime_model.md:59 |
| regime-classify family | regime.py:293-301 | net_score >= 4 + conf >= 0.60 or >= 2 -> RISK_ON; <= -4 + conf or <= -2 -> RISK_OFF; else NEUTRAL | regime value drives posture, direction, rendering | both | regime_model.md:77-83 |
| posture-confidence-floor | regime.py:310 | CHAOTIC or confidence < 0.50 | posture STAY_FLAT - global floor overriding regime logic | both | config.py:62 MIN_REGIME_CONFIDENCE; regime_model.md:96 |
| posture-risk-on family | regime.py:314-318 | conf >= 0.75 AGGRESSIVE_LONG; >= 0.55 CONTROLLED_LONG; else STAY_FLAT | long posture tier | both | regime_model.md:96-104 |
| posture-risk-off family | regime.py:321-323 | conf >= 0.55 DEFENSIVE_SHORT; else STAY_FLAT | short posture tier | both | regime_model.md:96-104 |
| posture-neutral-vix family | regime.py:326-330 | NEUTRAL/TRANSITION: VIX > 25 STAY_FLAT; 18-25 NEUTRAL_PREMIUM; < 18 or None STAY_FLAT (complacency) | neutral posture selection | both | regime_model.md:96-108 |
| watch-execution-posture family | watch.py:464-467 | regime None / CHAOTIC / STAY_FLAT | execution_posture "No Trade"; else "A+ Only" path | both | none |
| watch-outside-session-no-threshold | watch.py:244,247 | time outside 09:30-15:30 ET | watchlist loop skipped entirely; empty watchlist | both | none |
| watch-symbol-exclude family | watch.py:281-288 | CHOP + compression >= 0.7; consecutive expansion >= 4; wide-range dominance | symbol excluded from watchlist | both | none |
| watch-symbol-signal-threshold | watch.py:314-315 | total signals < 3 (MORNING/MIDDAY) or < 2 (POWER_HOUR) | excluded | both | none |
| watch-symbol-score-minimum | watch.py:325-326 | score < 60.0 (WATCH_SCORE_MIN) | excluded even if signals met | both | none |
| watch-output-cap (B) | watch.py:259 | more than 10 pass | truncated to top 10 by score; rest silently dropped | both | none |
| overnight-eod-window-gate | overnight_policy.py:63,85-96 | time NOT in [15:30, 16:00) ET | no overnight_policy block injected at all | publish | none (PRD-058 plausible) |
| overnight-hard-exit-dte | overnight_policy.py:124-126 | dte < 7 | FORCE_EXIT DTE_TOO_LOW | publish | none |
| overnight-chaotic-regime-exit | overnight_policy.py:127-129 | regime CHAOTIC | FORCE_EXIT REGIME_UNSTABLE | publish | none |
| overnight-near-key-level-exit | overnight_policy.py:130-132 | entry within 1.0% of any key level; fail-safe True on malformed input | FORCE_EXIT NEAR_KEY_LEVEL | publish | none |
| overnight-min-hold-dte-exit | overnight_policy.py:133-135 | dte None or < 10 | FORCE_EXIT DTE_TOO_LOW | publish | none |
| overnight-no-continuation-reduce | overnight_policy.py:136-138 | continuation_enabled not True | REDUCE_POSITION NO_EXPANSION_SUPPORT | publish | none |
| overnight-spread-fragility-escalation | overnight_policy.py:143-145 | SPREAD in strategy_tag AND not already FORCE_EXIT | decision escalated one severity step; reason SPREAD_FRAGILITY | publish | none |
| macro-pressure-driver-classify family | macro_pressure.py:58-88 | per-driver thresholds: VIX +/-1%; DXY +/-0.25%; rates +/-3 bps; BTC +/-1%/-1%; missing block/field -> UNKNOWN | component pressures feed overall | both | PRD-122 |
| macro-pressure-overall family | macro_pressure.py:94-107 | >= 2 RISK_ON + 0 RISK_OFF -> RISK_ON; mirror -> RISK_OFF; both >= 1 -> MIXED; all neutral -> NEUTRAL; all unknown -> UNKNOWN | overall_pressure rendered + feeds exec-policy macro gate | both | PRD-122 |
| market-map-lifecycle-new-symbol | market_map_lifecycle.py:53-57 | symbol absent from previous map | transitions NEW, is_new=True | both | none (PRD-056 plausible) |
| market-map-lifecycle-no-previous-map | market_map_lifecycle.py:58-60 | no previous snapshot | transitions UNKNOWN | both | none |
| market-map-lifecycle-grade-transition | market_map_lifecycle.py:19-28 | grade order delta | UPGRADED / DOWNGRADED / UNCHANGED / UNKNOWN | both | none (PRD-056 plausible) |
| market-map-lifecycle-removed-symbol | market_map_lifecycle.py:88-96 | symbol dropped from current map | removed_symbols entry REMOVED | both | none |
| market-map-lifecycle-price-carryforward (B) | market_map_lifecycle.py:82-85 | current price None, previous finite | previous price carried forward into rendered value | both | none |

red_folder.py gates nothing by its own docstring (line 7: "It renders nothing
and gates nothing") - gating delegated to the renderer (PRD-177).
watchlist_sidecar.py outputs feed no decision surface (docstring).

### 3.8 Catch-all sweep (remaining modules)

| Gate | LOC | Trigger | Effect | Path | Breadcrumb |
|---|---|---|---|---|---|
| thesis-gate-block | trade_thesis.py:176-190 | ALLOW_TRADE with thesis INCOMPLETE or CONFLICTED | BLOCK_TRADE THESIS_INCOMPLETE/THESIS_CONFLICTED | both | PRD-067 (docstring) |
| invalidation-gate-block | invalidation.py:156-169 | ALLOW_TRADE with guidance STATUS_TRIGGERED | BLOCK_TRADE INVALIDATION_TRIGGERED | both | PRD-068 (docstring); PRD-067 (line 32) |
| invalidation-warning-direction-pressure (B) | invalidation.py:93-107 | direction conflicts with overall_pressure | guidance STATUS_WARNING (non-blocking, rendered) | both | PRD-068 |
| chain-validation-liquidity-hard-fail | chain_validation.py:253-261 | OI < 200, volume < 20, or bid/ask <= 0 | setup_quality DISQUALIFIED_OPTIONS_INVALID | both | none (thresholds inline 81-97) |
| chain-validation-spread-hard-fail | chain_validation.py:263-270 | spread > 15% of mid | DISQUALIFIED_OPTIONS_INVALID | both | none |
| chain-validation-oi-spike-hard-fail | chain_validation.py:274-281 | best OI > 10x median of neighbors | DISQUALIFIED_OPTIONS_INVALID | both | none |
| chain-validation-execution-soft-downgrade | chain_validation.py:289-296 | bid < $0.10; or OI < 400 AND volume < 40 | WATCHLIST_OPTIONS_WEAK | both | none |
| chain-validation-spread-weak-soft | chain_validation.py:299-305 | spread 8-15% of mid | WATCHLIST_OPTIONS_WEAK | both | none |
| chain-validation-expiry-fit-fail | chain_validation.py:208-214 | nearest expiry outside 50-250% of target DTE | TOP_TRADE_CHAIN_FAILED | both | none |
| chain-validation-needs-manual-check family | chain_validation.py:198-244 | chain/expiry/price unavailable, eval error, inverted quote, consistency issue | NEEDS_MANUAL_CHECK | both | none |
| contract-derive-run-status-stay-flat | contract.py:182-190 | halted, posture STAY_FLAT, or outcome HALT | contract status STAY_FLAT (vs OK); tradable False | both | none |
| contract-system-state-tradable | contract.py:217-221 | halted, regime None, or STAY_FLAT | system_state.tradable False; renderers suppress actionable section | both | none |
| contract-time-gate-open | contract.py:223-229 | ET >= ENTRY_CUTOFF_ET (15:30) | time_gate_open False surfaced in contract | both | config.py:141 |
| contract-optional-macro-driver-omitted | contract.py:507-522 | oil/gold/silver quote missing or non-finite | those macro_driver keys absent from contract | both | PRD-122 / PRD-136 (lines 54-58) |
| correlation-disabled-bypass | correlation.py:46-53 | config.CORRELATION_ENABLED False | always NEUTRAL, modifier 1.0; CONFLICT path unreachable | both | PRD-023 (docstring) |
| correlation-risk-modifier-sizing | correlation.py:56-70 | GLD/DXY same direction CONFLICT 0.4; opposite ALIGNED 1.0; flat/missing NEUTRAL 0.7 | risk modifier scales rendered max_contracts/dollar_risk | both | PRD-023 |
| trade-explanation-near-miss-required-changes | trade_explanation.py:51-58 | visibility NEAR_MISS | required_changes populated in explanation block | both | PRD-066 (docstring) |
| market-map-grade-data-unavailable | market_map.py:187-189 | quote/derived/structure missing | grade F, SETUP_DATA_UNAVAILABLE; framing all WAIT sentinels | both | none |
| market-map-grade-choppy | market_map.py:190-192 | structure CHOPPY | grade F, SETUP_CHOPPY | both | none |
| market-map-grade-extended | market_map.py:193-195 | abs(price-EMA21)/ATR14 > 1.5 | grade D, SETUP_EXTENDED ("pullback reset watch") | both | none |
| market-map-actionable-grade | market_map.py:196-198 | regime-aligned + strong structure + near key level (1%) | grade A+, SETUP_ACTIONABLE; only path with IF_NOW_TAKE | both | none |
| market-map-watch-zone-5pct-filter | market_map.py:350-351 | zone level > 5% from price | zone silently excluded; affects near_key_level + rendered text | both | none |
| market-map-fib-levels-absent (B) | market_map.py:359-384 | bars missing/insufficient/degenerate | fib_levels None; tracked in data_quality | both | none |
| trend-structure-unavailable-propagation | trend_structure.py:99-103,180-195 | price/SMA/VWAP missing or short history | DATA_UNAVAILABLE / INSUFFICIENT_HISTORY / NOT_COMPUTED tokens flow to renderer | both | PRD-107 (docstring); PRD-130 (lines 87-90) |
| normalization-fetch-failure-exclusion | normalization.py:67-68 | fetch_succeeded False | symbol absent from normalized quotes; silently removed downstream (or halt if HALT_SYMBOL) | both | none |
| validation-halt-symbol-failure | validation.py:91-115 | any HALT_SYMBOL (^VIX, DX-Y.NYB, ^TNX, SPY, QQQ) missing/invalid | system_halted True - pipeline-wide halt | both | none (architecture.md:97 documents) |
| validation-freshness-threshold | validation.py:175-179 | quote age >= FRESHNESS_SECONDS (300) | symbol INVALID; halt if HALT_SYMBOL, else silently dropped | both | config.py:93 |
| ingestion-live-data-blocked | ingestion.py:74-75,167-168 | block_live_data context active (Sunday non-fixture) | fetch raises LIVE_DATA_FORBIDDEN_IN_SUNDAY_MODE; Sunday uses empty quotes | both | none (PRD-022 documents) |
| config-engine-doctor-runtime-gate | config.py:37-48 (consumed runtime:2148) | [engine_doctor].runtime_gate_enabled AND failures | SystemExit before output | both | none (PRD-020 plausible) |
| options-chop-symbol-skip | options.py:140-141 | structure CHOP | symbol never becomes a candidate | both | none (structure.py docstring; architecture.md:139) |
| options-dte-momentum-compression | options.py:294-313 | abs(momentum_5d) >= 0.03 AND structure PULLBACK/TREND | DTE compressed one tier (14->7, 21->14); rendered timeframe changes | both | none (docstring line 24) |
| options-stop-zero-skip | options.py:375-377 | computed stop <= 0 | candidate silently dropped | both | none |
| performance-engine-insufficient-sample (B) | performance_engine.py:111-118 | symbol trades < _MIN_SAMPLE (5) | bucket renders insufficient_data only; win_rate/expectancy suppressed | publish (perf artifact) | none (decision_quality_map.md:158 documents) |

NO qualifying gates found in: time_utils.py, sector_router.py, universe.py,
manual_journal.py, derived.py, structure.py (classification feeds gates but
its own branches are pure computation), audit.py, evaluation.py,
market_map_lifecycle covered in 3.7, watchlist_sidecar.py, red_folder.py.

---

## 4. Publish vs PRD-178 preview: gate diff

Three relevant paths exist:

- PUBLISH (hourly): .github/workflows/hourly_alert.yml - scheduled or manual
  dispatch. alert_runner -> _execute_notify_run (fetch, regime, qualify,
  format, send Telegram, write hourly artifacts) -> freshness check ->
  dashboard_renderer --output ui/dashboard.html -> check_readiness.py ->
  regime_history aggregation -> git commit -> push -> pages.yml deploys.
- CI PREVIEW (PRD-178): .github/workflows/dashboard_preview.yml -
  workflow_dispatch only. alert_runner --force-slot (same Python chain) ->
  freshness check (fail-hard) -> SAME renderer invocation targeting
  ui/dashboard.html in the ephemeral workspace (so PRD-118/119 gates
  execute) -> upload ui/ as a 7-day artifact. Nothing sent, committed,
  pushed, or deployed.
- LOCAL PREVIEW (PRD-178): scripts/preview_dashboard.sh - strips Telegram
  env vars (env -u), optional SKIP_FETCH=1, renders to
  reports/output/preview_dashboard.html (non-ui path, so PRD-118/119 are
  no-ops by design - layout iteration mode).

All upstream Python gates (sections 3.5-3.8) are IDENTICAL across publish
and both previews - the divergence is entirely at the workflow/transport/
filesystem layer plus the renderer's ui/-path check. The notification layer
has no preview awareness; preview safety comes from credential absence.

### 4.1 Diff table

Every row below was re-verified directly by the orchestrating agent
(rg/Read), not taken from sub-agent output alone.

| Gate / control | LOC | Publish (hourly) | CI preview | Local preview | Verified |
|---|---|---|---|---|---|
| Trigger surface | hourly_alert.yml:4-18 vs dashboard_preview.yml | schedule + dispatch | dispatch only | manual shell | yes |
| PT window check (routine_pt_slot) | alert_runner.py:63 | active on scheduled runs; BYPASSED on manual dispatch (--force-slot, hourly_alert.yml:60) | bypassed (--force-slot) | bypassed | yes (alert_runner.py:45,60-63) |
| Same-slot idempotency (load_last_slot) | alert_runner.py:81 | active on scheduled runs; bypassed on manual dispatch | bypassed | bypassed | yes |
| Telegram credentials | hourly_alert.yml:30-33 | present (secrets) | ABSENT - rg 'TELEGRAM' in dashboard_preview.yml returns nothing; send degrades to audit row skipped/not_configured (output.py:550-571) | stripped via env -u | yes (empty grep) |
| save_last_slot state mutation | runtime/__init__.py:515-517 | runs when alert actually sent | never (alert_sent False) - preview cannot lock out the next scheduled slot | never | yes |
| Stale-payload handling | hourly_alert.yml:73-83 vs dashboard_preview.yml:55-62 | fresh=false -> skip publish steps, job exits 0 (green) | hard FAIL exit 1 - stale render can never pass as fresh | n/a | yes |
| PRD-118 coherence + PRD-119 freshness (validate_coherent_publish) | dashboard_renderer.py:411 | execute (ui/ output) | execute (ui/ output in ephemeral workspace) - PRD-178 R4 intent | NO-OP (non-ui output path) - intentional per PRD-119.md:131-135 | yes (renderer:353,411) |
| check_readiness.py HTML validation | hourly_alert.yml:101-103 | runs | absent (rg empty) | absent | yes |
| regime_history aggregation | hourly_alert.yml:105-109 | runs (mutates regime_history.jsonl) | absent (rg empty) | absent | yes |
| Repo permissions | hourly_alert.yml:25-26 vs dashboard_preview.yml:17-18 | contents: write | contents: read | n/a (local) | yes |
| git commit / push | hourly_alert.yml:111-147 | yes | absent (rg empty) | no | yes |
| Pages deploy | pages.yml:5-10 | fires on "Cuttingboard Hourly Alert" completion + main push | never (different workflow name; no push) | never | yes |
| Concurrency serialization | hourly_alert.yml:21-23 | hourly-alert group, no cancel | none (parallel dispatches possible; ephemeral, contained) | n/a | per sweep |
| Artifact upload | dashboard_preview.yml:93-98 | failure-only artifacts | always uploads ui/ on green | local file | per sweep |

### 4.2 Notes

- The manual-dispatch hourly run is the maximally privileged path: it
  bypasses the PT window and same-slot gates (--force-slot,
  hourly_alert.yml:60) while retaining Telegram credentials, commit, push,
  and Pages deploy. The CI preview is the same fetch path with every
  outbound capability removed.
- Both publish and preview write hourly artifacts (_write_hourly_artifacts,
  runtime/__init__.py:1776). On CI both are ephemeral or committed
  deliberately; the LOCAL preview mutates tracked logs/* files - protection
  against committing them is doctrinal (PRD-178.md:179-181), not code.
- audit.jsonl IS appended by preview runs via the send_telegram
  not_configured audit row - documented as routine local dirt in
  PRD-178.md:179-181.
- The preview workflow exercises PRD-118/119 on real fresh data; the
  preview-only gates (preview-payload-missing-fail / stale-fail,
  dashboard_preview.yml:55,60) are STRICTER than their publish counterparts
  (fail-hard vs skip-green) - inversion is deliberate (PRD-178 R5).

---

## 5. Traceability map + flags

### 5.1 Gate family -> documented justification

| Gate family (section) | Justification | Strength |
|---|---|---|
| Publish coherence + freshness (3.3: prd118-*, prd119-*, lineage, contract-stale) | PRD-118.md:68-91, PRD-119.md:57-135, PRD-116, PRD-117, PRD-120; VISION "system must match its documentation" (silent-drift clause) | STRONG - in-code breadcrumbs + PRD text verified |
| Integrator collapse rules 1-4 + renderer suppressions (3.4, 3.3) | PRD-158 sec 4.3 (docstring cites); PRD-160, PRD-168 | STRONG |
| Trend-structure rendering ladder (3.3) | PRD-107/110/112/123/130/131/132/165/174 | STRONG |
| Scoreboard (3.3, 3.4 regime-history) | PRD-175 (R1/R2 in docstrings), PRD-177 | STRONG |
| Red folder (3.3) | PRD-176, PRD-177; red_folder.py:7 declares loader gates nothing | STRONG |
| Notification suppression chain: state dedup, priority breakthrough, slot window, same-slot idempotency (3.5, 3.1) | PRD-018.md:37-52, PRD-141.md:54-58, PRD-149.md:19-35; PRD-017 (retry/dedup, parameters unverified); PRD-006 (Telegram-only) | STRONG for structure; parameters unverified |
| Preview path isolation (4) | PRD-178 R1-R7 (verified against workflows) | STRONG |
| Qualification gates 1-11 + outcomes (3.6) | docs/trade_qualification.md:5-275 (thresholds match code, incl. fail-open Gate 9, ENTRY_CUTOFF naming aside - C3); architecture.md:139 | STRONG |
| Flow gate (3.6) | PRD-013.md:29-36; architecture.md:158-163 | STRONG |
| Sizing / RR regime branches (3.1, 3.6) | PRD-157; docs/regime_model.md:108; verify + harness assertions mirror them | STRONG |
| Continuation gates (3.6) | PRD-008, PRD-010 (first-failure semantics, PRD-010.md:37-38); PRD-157 | MEDIUM - ordering claim not re-verified in code |
| Decision chain: materialization, exec policy, macro pressure, visibility, explanation, thesis, invalidation, entry quality (3.6, 3.8) | PRD-045/046/051/063/064/066/067/068/069; PRD-063.md:53-60 table matches execution_policy.py:240-251 | STRONG |
| Regime classification + posture ladder (3.7) | docs/regime_model.md:59-108 (thresholds match code exactly); config.py:62,102 | STRONG |
| Gap-down permission chain (3.7, 3.1) | PRD-151.md:35-120 (incl. documented audit blind spot and fixture skip); VISION.md:23,39 names it explicitly | STRONG (stale line refs aside - D3) |
| Sunday isolation (3.1, 3.8 ingestion) | PRD-022, PRD-077, PRD-080 | MEDIUM - PRD text grepped, not fully read |
| Payload routing / top-trades filter (3.4) | PRD-011 (docstring), PRD-162.md:164-175 | STRONG |
| Validation halt + freshness (3.8) | architecture.md:96-100,263-268 | STRONG |
| Sidecar non-interference (notifications protected from sidecars) | docs/sidecar_doctrine.md:62-63,122-130; system_logic_map.md:144-145 | STRONG - no counterexample found |
| Dashboard section ordering serving VISION four questions | PRD-177 (four-questions reorder); VISION.md:5 | STRONG |

### 5.2 Coverage summary

The section 3 inventory holds 363 rows (family rows fold multiple
near-identical branches, so the raw conditional count is well over 400).
Of the 363: 152 rows (42%) carry an explicit justification - an in-code PRD
breadcrumb or a doc claim matched by this recon; 34 rows (9%) have a
plausible covering PRD noted but not text-verified; 177 rows (49%) have no
justification marker at all. Most of that last group are mechanical
presence-checks (field absent -> row omitted) that arguably need none; the
substantive undocumented gates are flagged in 5.3(a).

### 5.3 Flags

#### (a) ORPHAN gates - no documented justification located

| # | Gate(s) | LOC | What is undocumented |
|---|---|---|---|
| O1 | kill-switch-computation | runtime/__init__.py:1956 | The thresholds VIX > 35, VIX pct_change > 15%, abs(SPY) > 3% appear in no scanned doc. The only doc mention of _kill_switch describes different behavior (see C1). Also note its EFFECT is summary-level only (zeroes candidates_qualified at runtime:1055); it does not block decisions directly. |
| O2 | watch.py family | watch.py:244-326,259 | Session window 09:30-15:30, exclusion rules (compression 0.7, expansion count 4, wide-range dominance), signal thresholds 3/2, WATCH_SCORE_MIN 60, output cap 10 - none located in any PRD or doc. |
| O3 | sunday-mode-auto-conversion | runtime/__init__.py:2011 | Silent LIVE -> SUNDAY conversion when run on Sunday at/after 15:30 ET. Sunday mode itself is PRD-022/077; the auto-conversion trigger and its 15:30 threshold are not. |
| O4 | notification content caps | output.py:836,885-896; formatter.py:287,438; notifications/__init__.py:164-179,235 | Caps of 2 watch lines, 4 secondary candidates, 5 body lines, 3 focus tokens, 3 pending entries, 30-char reason truncation - all hard-coded, none documented. |
| O5 | noise-window-suppress | intraday_state_engine.py:435 | Pre-09:45 ET bar suppression (no IntraState at all). Not in PRD-151. Interacts with the fail-open at runtime:1136: before 09:45 the SHORT gap-down gate is effectively bypassed because state is unavailable. |
| O6 | chain-validation thresholds | chain_validation.py:198-305 | OI 200/400, volume 20/40, spread 8%/15%, OI-spike 10x, expiry 50-250% of target DTE, bid $0.10. architecture.md:173-178 documents the classification taxonomy but no doc names the numbers. |
| O7 | data-status rules | runtime/__init__.py:1940-1942 | Fixture runs always "ok"; Sunday always "stale". |
| O8 | options.py gates | options.py:294-313,375-377 | DTE compression on momentum >= 3% and the silent drop of stop<=0 candidates. |
| O9 | hourly freshcheck mtime gates | hourly_alert.yml:66-87 | Skip-green semantics on stale payload. Possibly PRD-128/129; not verified. |

Unverified-justification (a plausibly-covering PRD exists but its text was
not extracted by this recon - distinguish from true orphans before acting):
market_map grade ladder + 5% zone filter (PRD-053/054), overnight policy
thresholds (PRD-058), EXPANSION early-return thresholds (PRD-008), hourly
alert content shapes (PRD-101/124/127/133), telegram retry/dedup parameters
(PRD-017), safe-write timestamp guard (PRD-040), run-delta and history
blocks (PRD-041/042), lifecycle badges (PRD-056/057).

#### (b) GHOST requirements - documented gating with no code

| # | Documented where | Claim | Code reality |
|---|---|---|---|
| G1 | PRD-019.md:1,21-28 (status COMPLETE in registry) | Notification decision layer: exactly one decision per run from enum SENT / SUPPRESSED / RATE_LIMITED / ERROR / DISABLED via a deterministic reason enum | rg for build_notification_decision and RATE_LIMITED across cuttingboard/ returns nothing. Notification audit rows exist but use a different vocabulary (sent / skipped+not_configured / suppressed_unchanged_state / suppressed_same_slot / outside_routine_window). Compounding: the registry row title for PRD-019 is "Engine doctor - canonical pipeline health authority" (PRD_REGISTRY.md:33), which matches PRD-020's subject, not the PRD-019 file. |
| G2 | docs/runbook.md:10,131-134 | "Intraday monitor runs every 30 minutes (14:00-21:30 UTC)... sends an immediate ntfy alert" during CHAOTIC | No 30-minute monitor exists in any workflow (cuttingboard.yml routes named slots; hourly_alert.yml is hourly). ntfy transport was removed by PRD-006; remaining ntfy references are three stale docstrings (notifications/__init__.py:438,469,491). VISION.md:27 lists ntfy as dead code to remove. |
| G3 | docs/system_logic_map.md:56 | "trade_policy.py - policy context evaluation; can force NO_TRADE for a candidate" | trade_policy.py:33: "policy_note is informational only - never drives gate logic." No gate exists in the module. |
| G4 | PRD-141.md:47-48,117-133 | Premarket cron firings (12:50/13:00/13:50 UTC) are exempt from the same-slot idempotency gate | is_premarket_slot exists (hourly_slot.py:79) but has NO production caller, and tests/test_prd050_alert_runner.py:249-252 asserts alert_runner must NOT reference it (PRD-149 R6). The documented exemption is not in the running system; PRD-149's window gate replaced it. |

#### (c) CONFLICTS - code and docs (or two docs) disagree

| # | Sides | Detail |
|---|---|---|
| C1 | docs/system_logic_map.md:63 vs runtime/__init__.py:1055,1956 | Doc: "_kill_switch which can force HALT". Code: kill switch zeroes candidates_qualified in the run summary and trips a verify assertion (runtime:1350); outcome HALT is produced only by validation system_halted. Behavior described in docs does not match the mechanism in code. |
| C2 | docs/system_logic_map.md:56 vs trade_policy.py:33 | Same evidence as G4/G3 row above: doc asserts a gating capability the module explicitly disclaims. |
| C3 | docs/trade_qualification.md:270 vs config.py:141 | Doc cites config.LATE_SESSION_CUTOFF; no such key exists. Real key: ENTRY_CUTOFF_ET (time(15,30)), used at qualification.py:853. Threshold value matches; symbol name is fictional. |

#### (d) DRIFT candidates - same gate described differently / stale docs

| # | Where | Detail |
|---|---|---|
| D1 | VISION.md:25 vs PRD_REGISTRY.md:198-199 | VISION current-state says "In flight: none"; registry has PRD-178 IN PROGRESS and PRD-179 PROPOSED. VISION's snapshot is stale (it predates the 174-179 arc; also cites 2499 tests at VISION.md:23). |
| D2 | notifications/__init__.py:438,469,491 vs PRD-006 / VISION.md:27 | Three docstrings still describe formatters as producing "ntfy" alerts; transport is Telegram-only. Cosmetic but feeds G2-style confusion. |
| D3 | PRD-151.md:88,100-108 | Cites runtime.py:1205/489/518/805 - line references stale after the PRD-173 runtime/ package split (actual: runtime/__init__.py:1108-1151, 708, etc.). Behavior matches; citations do not. |
| D4 | notifications/__init__.py:394-422 + tests/test_notification_audit.py:237-243 | should_suppress (confidence-based midmorning/power-hour suppression) is dead code, explicitly pinned out by a test. Dead-by-design is documented only in the test file - no canonical doc records the decision to keep-but-not-wire it. |
| D5 | hourly_slot.py:79 + tests/test_prd050_alert_runner.py:249-252 | is_premarket_slot: same keep-but-pinned-out pattern as D4 (see G4). |
| D6 | docs/decision_quality_map.md:222-234 | stay_flat_reason set on the contract but never written to logs/audit.jsonl - documented, acknowledged calibration gap. |
| D7 | docs/decision_quality_map.md:87 | audit.jsonl suppressed_candidates field always empty under sector-router state-only behavior - documented as schema-continuity placeholder. Note: gap-down SHORT suppression (runtime:1147) also does NOT populate it (PRD-151.md:117-120 documents the blind spot). |
| D8 | PRD_REGISTRY.md:33 vs PRD-019.md:1 | Registry row title does not match PRD file subject (see G1). The PRD-index sub-agent reported "no inconsistencies" because it compared statuses only - title mismatch caught on re-verification. |

#### Verified non-findings (checked and cleared)

- PRD-151 fail-open semantics: PRD-151.md:96-98 and runtime/__init__.py:1136
  AGREE (state unavailable -> SHORT preserved). An earlier sub-agent
  paraphrase suggested a conflict; direct read cleared it.
- Regime thresholds, posture ladder, qualification gate thresholds,
  PRD-063 pressure table, PRD-118/119 publish gates, PRD-178 R1-R7: all
  doc-vs-code checks passed.
- PRD registry vs prd_index.json vs PRD files: statuses consistent for all
  entries (subject-line mismatch on PRD-019 noted in D8 is the exception).

---

## 6. Open questions for the strategist

1. PRD-019 identity (G1/D8): is the registry row mislabeled (and the
   notification-decision layer genuinely unbuilt), or was PRD-019 repurposed
   to the engine doctor and the file never updated? Decides whether a
   COMPLETE PRD's deliverable is missing from the codebase.
2. Kill switch semantics (C1/O1): is summary-count-zeroing the intended
   effect (with verify as backstop), or was force-HALT the intent as
   system_logic_map states? The thresholds (VIX 35, 15%, SPY 3%) have no
   recorded rationale anywhere.
3. trade_policy.py (C2/G3): should the doc claim be cut, or should the
   module regain a gating role? Cuts-before-additions suggests the former,
   but that is a strategy call.
4. Dead-but-pinned gates (D4/D5): should_suppress and is_premarket_slot are
   kept, tested, and deliberately unwired. Keep, wire, or delete? VISION's
   "every module earns its keep" bears on this.
5. The manual hourly dispatch path (sec 4.2): --force-slot with full
   credentials, commit, push, and deploy is the least-gated route to
   production output. Acceptable operator override, or should it share the
   preview path's constraints?
6. Ungoverned thresholds (O1, O2, O5, O6): watch scoring, chain-validation
   liquidity numbers, the 09:45 noise window, and kill-switch levels gate
   real output with no documented rationale. Which of these deserve a
   regime_model.md-style reference doc vs being accepted as tuning
   constants?
7. The 09:45 noise window + fail-open interaction (O5): before 09:45 ET the
   gap-down SHORT gate cannot fire (no IntraState -> fail-open at
   runtime:1136). PRD-151 documents OPEN-phase blocking from 09:30; in
   practice the engine produces no state until 09:45. Is the first-15-minute
   behavior what PRD-151 intended?
8. Notification caps (O4): the 2/3/4/5-item truncations decide what the
   trader actually sees on the phone; none are documented. Calibrate or
   codify?
9. Stale docs (G2, D1, D2, D3): runbook.md's monitoring section and
   VISION.md's current-state block both describe a system that no longer
   exists in those respects. Fold into the next alignment-cadence pass?
10. suppressed_candidates blind spot (D7): two suppression mechanisms
    (sector router, gap-down filter) leave no artifact trail. PRD-151
    documents the gap; decision_quality_map preserves the empty field. Is
    silent suppression acceptable for a system whose stated value is
    explicit reasoning under uncertainty (VISION.md:7)?

---

Report generated by read-only recon, 2026-06-12. No source files were
modified. This file is the only write.

