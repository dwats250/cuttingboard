# Decisions log

Meaningful decisions and rationale. Date-ordered, newest first.
Short notes, not ceremony.

**Compression rule.** At each calendar year-end (or when this file
exceeds 1500 lines, whichever comes first), move entries from
completed years into `docs/DECISIONS-YYYY.md`. Replace each archived
entry's body with a one-line summary + a link to the archive
section, keeping the headline visible in the main file. Do not
condense entries within the active year — they're load-bearing for
ongoing work and the cost of search is cheap.

Phase-boundary archives are optional and only worth doing when a
phase produced ≥20 entries and the next phase has clearly begun.

---

## 2026-06-14 - PRD-184: auto-merge-via-PR landing flow (Claude push enablement)

PRD-182 and PRD-183 each stalled at "PR-ready" waiting on a manual human push
because `.claude/settings.json` denied `git push`. Decision (Dustin): adopt
"auto-merge via PR after CI" so Claude lands PRD work autonomously.

The harness safety classifier reserves permission changes for the human, so it
blocked Claude from editing `.claude/settings.json` to self-grant push -
correctly, since that is self-modifying a guardrail. Dustin applied the change
via a setup one-shot: the settings allowlist now permits `git push` + `gh pr`
(force-push still denied), the repo has "Allow auto-merge" enabled, and `main`
branch protection requires the CI `test` check. PRD work now lands branch ->
push -> PR -> `gh pr merge --auto` -> green CI -> auto-merge to main; docs-only
bookkeeping/closeout commits may push to main directly. CLAUDE.md's no-push rule
was replaced accordingly. PRD-184 itself dogfoods the flow as the first
auto-merged PR. See PRD-184.

Residual risk (independent review, recorded not fixed): `main` branch protection
has `enforce_admins=false`, so a direct non-force push to `main` by the admin
identity (the token Claude uses) bypasses the PR+CI gate. The "bookkeeping may
push to main directly" carve-out is therefore policy-gated, not mechanically
enforced; CI is the only automated gate, and only on the PR path. Accepted as a
reasonable solo-builder tradeoff (Claude is the author and the HIGH-RISK review
gate is a process control). Tighten with `enforce_admins=true` if `main` should
be reachable only through CI-gated PRs. Force-push and branch deletion ARE
mechanically blocked at the protected branch (`allow_force_pushes=false`,
`allow_deletions=false`).

## 2026-06-14 - PRD-183: realign closeout tooling to the new PROJECT_STATE format

The PRD-182 closeout surfaced that `scripts/prd_close.sh`,
`scripts/pre_commit_sanity.sh`, and `tests/test_prd_close.py` still targeted the
pre-realignment PROJECT_STATE markers (non-bulleted Active PRD, `Last completed
PRD` / `Last work completed` prose lines, `- **N passing**` bullet, 4-col history
table). The doc was restructured to "Current state / Recent ships" without
updating the tooling, so each closeout silently skipped five edits and the
scope-lock nudge in `pre_commit_sanity.sh` always read "no active PRD."

Decision (Dustin, 2026-06-14): adapt the tooling TO the canonical new format
rather than restore the removed markers. `prd_close.sh` now resets the bulleted
single-line `- **Active PRD:**`, updates the `Test baseline` line in place
(wrap-tolerant), prepends a 3-column Recent ships row, and routes `--summary`
into the bookkeeping commit body (the new format has no prose summary line). The
Active PRD and Test baseline lines were normalized to single lines so they are
machine-resettable; the proposed-next note moved to its own bullet.
`pre_commit_sanity.sh` parses the bulleted Active PRD line; the
`prd-closeout-verified` skill's V6/V7/V8 were realigned. Validated against a copy
of the real PROJECT_STATE.md with zero WARN-skips. See PRD-183.

## 2026-06-13 - Workflow + hooks audit: cut net-negative machinery, slim AGENT_WORKFLOW

Audited the agent-workflow scaffolding for net value (branch `lean-workflow-hooks`,
off `docs-realignment`, no push). Root finding: the machinery was built for a
flatter package and a heavier pre-harness agent setup, and the code has outgrown
it - two pieces assumed `cuttingboard/*.py` was the whole package and silently
ignored the `runtime/`, `delivery/`, and `notifications/` subpackages.

**Cut (net-negative or dead):**
- `test_gate.sh` - ran the full ~70s suite after every top-level `.py` edit, but
  its scope regex ignored every subdirectory, adding latency on flat edits and
  giving false "all passed" on the subdir code it never ran. The agent already
  runs targeted tests during iteration and the full suite before commit.
- `git_gate.sh` - dormant (never wired in `settings.json`) and redundant with the
  harness's native commit/push gating (push is already denied in settings).
- `stop_snapshot.sh` - a redundant breadcrumb; the harness handles context.

**Slimmed:** `AGENT_WORKFLOW.md` from 667 lines to just the `## Auto-Approval
Policy` section the PRD skills parse, and fixed its protected-file list
(`runtime.py` -> `runtime/`) so `scope-lock-precommit` stops missing edits to the
runtime package. The skill contract (the parsed section) is preserved.

**Kept:** `protect_files.sh` (the real backstop - `settings.json` auto-approves
Write/Edit, so this is the only guard on secrets/.env/CI), `prd_eval.sh` (PRD
review + sequencing), and the non-blocking git `pre-commit` sanity.

**Reconciled:** `CLAUDE_HOOKS.md` rewritten to match reality - it had documented
git_gate as wired (it was not) and protect_files as blocking all writes (it only
guards protected paths), and never documented the live prd_eval hook.

## 2026-06-13 - Documentation realignment: tier-1 docs made canonical, sprawl cut

Re-aligned the docs to describe the system as it is now, not as it was during the
exploration phase. Branch `docs-realignment` (no push).

**Tier-1 rewrites.** `VISION.md` rewritten evergreen: a new objective-declaration
opening, the four questions promoted to the spine, hard non-goals, operating
principles, and the trap-to-watch-for. All current-state (test counts, phase
plans, dead-code-to-remove, in-flight lists) removed and left to
`PROJECT_STATE.md`. `CLAUDE.md` tightened to the operating model with roles, the
no-push rule, the HIGH-RISK review gate, and scope-lock discipline explicit;
`runtime.py` reference corrected to the `runtime/` package; the `prd_open.sh`
"once it exists" note resolved (shipped as PRD-159). `PROJECT_STATE.md` cut from
an accreted changelog to a tight current snapshot - it had duplicated the PRD
registry, architecture.md, and VISION, and carried a self-contradictory test
baseline. Baseline re-verified at 2607 passing / 1 xfailed (commit `4f3257b`).

**Market-stress invalidation in VISION (PRD-180 R4 pointer; decision A1).** The
deferred "what invalidates" pointer (see the GO entry below) is placed in VISION
as an evergreen invalidation *principle* - extreme market stress is a hard stop -
with the concrete kill-switch thresholds and terminal HALT left in
`docs/system_logic_map.md`, where PRD-180 made them canonical. VISION carries the
principle, not the mechanism.

**Cuts.** Removed two stale planning artifacts
(`docs/superpowers/plans/2026-05-08-prd-102*`, `-prd-103*`; superseded by the
shipped PRDs) and an orphaned agent-doc pair (`docs/AGENT_SESSION_BOOTSTRAP.md`,
`docs/AGENT_BUILD_REPORT_TEMPLATE.md`; referenced by nothing live).
`docs/AGENT_WORKFLOW.md` was KEPT - the `scope-lock-precommit` skill reads it at
runtime as the single source of truth for the protected-file set and fails closed
without it.

**Drift fixes in kept reference docs.** `trade_qualification.md` cited a
nonexistent `config.LATE_SESSION_CUTOFF` (real key `config.ENTRY_CUTOFF_ET`);
`runbook.md` referenced the removed ntfy notifier (delivery is Telegram-only);
`architecture.md` documented deleted Moomoo modules, called the orchestrator
`runtime.py` (now the `runtime/` package), and claimed no HTML is rendered while
`delivery/dashboard_renderer.py` ships the dashboard. All corrected.

**Flagged, not touched.** `system_logic_map.md`, `docs/audit/gate_recon_2026-06-12.md`,
and the merged PRD-180/181 code surfaces were left alone. Two follow-ups:
`AGENT_WORKFLOW.md`'s protected-file list still names the literal `runtime.py`
(now a package) and the `scope-lock-precommit` skill parses that file; and
`CLAUDE_HOOKS.md` documents `git_gate.sh` as a wired commit gate while
`settings.json` does not wire it.

## 2026-06-13 — PRD-180 implementation GO: mechanism (b)/tight path; VISION R4 pointer deferred

PRD-180 (kill switch forces real HALT) moved from APPROVED to implementation on
branch `PRD-180-killswitch-halt`.

**Mechanism ratified: (b), tight path.** On a `_kill_switch` trip the run
computes regime early, evaluates the kill switch, sets `outcome = OUTCOME_HALT`,
escalates to a system halt (`system_halted = validation OR kill-switch tripped`),
and skips the qualification/options/decision block exactly as the validation
`system_halted` branch does. Implementation reuses the validation HALT carrier
(`validation_summary` rebuilt as halted with a market-stress `halt_reason`) so
every downstream consumer — report banner, contract `derive_run_status` /
`system_state`, notification, audit record, run summary — treats the market-stress
halt identically to a validation halt with no per-consumer wiring. Rejected
mechanism (a) (late trip routed to HALT inside `_build_run_summary`): it leaves
the pipeline already executed and still needs the same `system_halted`/status
escalation to satisfy `verify_run_summary` and light up the dashboard/notification
surfaces, so it does strictly more work for the same end state. R2 preserved: the
validation `system_halted` branch itself is untouched.

**Tradeoff accepted:** the `system_halted` field's meaning broadens from
"validation halt" to "any system halt"; a kill-switch run will show both the
"Halted" and "Kill Switch" indicators. `halt_reason` is load-bearing and must
read as a market-stress HALT, not a data/validation failure.

**FILES amended at GO:** added `cuttingboard/output.py` (R4 docstring fix) and
`tests/test_operationalization.py` (verify-coherence test home); removed
`VISION.md`.

**Deferred: VISION.md "what invalidates" pointer (R4).** The one-line
market-stress-HALT pointer into VISION.md is deferred to the declaration
workstream rather than landed in this PRD. Tracked here so it is not lost.
PRD-180's R4 is satisfied by `system_logic_map.md` (canonical thresholds + C1
conflict resolution) plus the `output.py:204` docstring correction.

## 2026-06-13 — Two gate-recon behavioral decisions ratified and drafted as PRD-180 / PRD-181

Both decisions resolve open questions from the 2026-06-12 gate recon
(`docs/audit/gate_recon_2026-06-12.md`). Ratified by Dustin; drafted to disk
as PROPOSED PRDs this pass. No source code changed — drafting only.

**D-Q2 (recon C1/O1, open question 2) — kill switch forces real HALT.**
Decision: when any `_kill_switch` threshold trips, the run must resolve to the
existing terminal HALT outcome (`OUTCOME_HALT`), not merely zero the qualified
count with a verify-step backstop; the three thresholds (VIX > 35, VIX
pct_change > 0.15, |SPY| pct_change > 0.03) become named, documented constants
with values unchanged. Rationale: align behavior with the long-standing
doc claim (`system_logic_map.md:63`) and make market-stress invalidation a
real, auditable system stop rather than a silent count-zeroing. Drafted as
PRD-180 (LANE HIGH-RISK, CLASS EXECUTION).

**D-Q7 (recon O5, open question 7) — short-gate fail-closed, open-window-bounded.**
Decision: when intraday state is unavailable AND the clock is within the open
window [09:30 ET, 09:45 ET) (before `_NOISE_END` emission), SHORT candidates
fail CLOSED instead of the current fail-open; LONG side, post-09:45 gating, and
the outside-window fail-open default are all unchanged. Rationale: PRD-151's
OPEN-phase SHORT block is currently inert in exactly the window it was written
for, because no intraday state exists before 09:45; this closes that gap on the
filter side only, without touching `intraday_state_engine.py`. Drafted as
PRD-181 (LANE HIGH-RISK, CLASS EXECUTION).

Both PRDs are PROPOSED and behavioral. They remain pending external review and
are NOT implemented: no change to `runtime/__init__.py`,
`intraday_state_engine.py`, kill-switch logic, or short-gate logic this pass.

## 2026-06-12 — PRD-019 killed: notification-decision layer never built, obsolete under three-report cadence

The 2026-06-12 gate recon (`docs/audit/gate_recon_2026-06-12.md`,
flags G1/D8) found PRD-019's deliverable — a deterministic
notification-decision layer (`build_notification_decision`, the
SENT / SUPPRESSED / RATE_LIMITED / ERROR / DISABLED decision enum plus
a strict reason enum, written into the notification audit record) —
does not exist in the codebase. A grep for `build_notification_decision`
and `RATE_LIMITED` across `cuttingboard/` returns nothing; the
notification audit rows that do exist use a different vocabulary
(sent / suppressed_unchanged_state / suppressed_same_slot /
outside_routine_window). The PRD-019 registry row compounded the
confusion by carrying PRD-020's "Engine doctor — canonical pipeline
health authority" title (PRD_REGISTRY.md:33) instead of its own subject.

**Decision (Dustin, 2026-06-12): PRD-019 is KILLED, not resurrected.**
The explain-why-a-notification-fired need it was scoped to serve is now
met by the three-report cadence (premarket / hourly / postmarket context
reports, PRD-027) layered over the existing notification audit rows, so a
separate decision layer is redundant surface area. Retired under
cuts-before-additions.

**Applied this pass (docs-only, zero behavioral risk):** PRD-019 status
flipped to DEPRECATED in the registry with a "Killed 2026-06-12" note and
its real subject restored; a KILLED banner added at the head of
`docs/prd_history/PRD-019.md` with the original spec retained for
historical record. No code changed — there was no PRD-019 code to remove.
`prd_index.json` is unaffected (it tracks PRD-56+).

**Not actioned (behavioral, pending external review):** the same recon
raised two behavioral questions that remain UNDECIDED and were
deliberately left untouched this pass — kill-switch HALT semantics
(recon C1/O1, open question 2) and the 09:45 noise-window / SHORT
gap-down fail-open interaction (recon O5, open question 7). No
runtime/__init__.py or intraday_state_engine.py change was made.

## 2026-06-10 — Codex exec sandbox verified: workspace-write + network off, not read-only

The sub-agent flow audit (report-only, this date) flagged that the
Codex CLI's sandbox is governed by its own config, not this repo's
`.claude/settings.json` deny list. Verified empirically against
`~/.codex/config.toml` and Codex session logs (the 7 most recent
`codex_exec` runs from this repo, 2026-06-04 through 2026-06-09):

- Effective policy on every run: `sandbox_policy` type
  `workspace-write` with `network_access: false`;
  `approval_policy: never`.
- Driver: `~/.codex/config.toml` sets no explicit sandbox mode, but
  marks this repo — and `"/"`, which is overly broad — as
  `trust_level = "trusted"`, promoting `codex exec` from its
  read-only default to workspace-write.
- What holds: **no-push** holds transitively — network access is off
  inside the sandbox, so `git push` cannot reach a remote.
- What does NOT hold: **workspace-read**. Codex runs can write inside
  the workspace and `/tmp` (`exclude_slash_tmp: false`). A review
  invocation could in principle mutate the repo, and this repo's own
  settings do not constrain it (`Bash(codex exec *)` is allowlisted
  in `settings.local.json`).

**Trust level recorded:** Codex output is trusted as an independent
second-model review opinion; Codex *runs* are not trusted as
read-only by default.

**Same-day update — review path flipped to read-only by invocation,
not just no-push-by-no-network.** Verified first that the artifact
flow tolerates it: session logs for the PRD-170 review runs show
Codex executed only read commands (`rg`/`sed`/`nl`/read-only Python
AST analysis) and emitted the verdict on stdout; the
`.review.codex.md` artifact is written by a shell stdout redirect on
the Claude Code side, outside the Codex sandbox, so the sandbox mode
cannot affect it. Smoke-tested `codex exec -s read-only` end-to-end
(2026-06-10 session log records `sandbox_policy: {"type":
"read-only"}`). CLAUDE.md workflow patterns now route all Codex
*review* invocations (PRD cross-review, vision review, pre-merge
review) through `codex exec -s read-only - < prompt`.

**Follow-up — APPLIED (same day):** trust tightening done in
`~/.codex/config.toml` (backup at `~/.codex/config.toml.bak`).
Removed three entries: `[projects."/"]`,
`[projects."/home/dustin/cuttingboard"]` (stale old repo path), and
`[projects."/home/dustin/Projects/cuttingboard"]`. Cuttingboard now
defaults to read-only for `codex exec`.

Evidence: trust matching is exact-path, not ancestor-prefix —
verified across 152 Codex sessions (all 33 distillery exec runs were
read-only with no trust entry, despite sitting under both `"/"` and
`"/home/dustin"`), so removing `"/"` stranded no project. Smoke
tests from this repo, policies read from session logs: default
invocation records `read-only`; `-s workspace-write` records
`workspace-write`; the review path (`-s read-only`) records
`read-only`.

**Gotcha, explicit:** `codex exec -s workspace-write` silently
re-persists `trust_level = "trusted"` for the cwd back into
config.toml, so the read-only default is NON-DURABLE — it reverts
after any write opt-in from this repo (observed live during
verification; the re-added entry was removed again). Decision: drift
ACCEPTED, because review invocations carry explicit `-s read-only`
and are immune regardless of trust state. Durable alternatives
rejected: per-project `sandbox_mode` key is ignored by codex-cli
0.139.0 (tested); global `sandbox_mode = "read-only"` would strip
the write default from the other trusted projects. Optional untested
path noted for the record: immutable config (`chattr +i`).

**Residual:** `[projects."/home/dustin"]` remains trusted (matches
only cwd exactly equal to `/home/dustin`, per the exact-path
evidence above) — flagged for optional future removal, not done now.

Same audit also added the fourth PRD-author discipline to CLAUDE.md
(sub-agent sweep re-verification: the main agent re-runs the single
decisive `rg` before a delegated sweep counts as evidence for a
FILES boundary or a "nothing else reads this" claim).

## 2026-05-29 — Alignment cadence check #2 — PASS (no drift)

Second cadence check (first since #1 established the post-VISION
baseline on 2026-05-22). Run slightly early at Dustin's request,
coinciding with the PRD-158 output-surface realignment and PRD-160
macro_bias correction — a natural surface-level boundary. Scope: all
production code landed since check #1 (PRDs 154–158, 160; PRD-156 was a
net removal).

Net code surface since #1: exactly one new module —
`cuttingboard/delivery/dashboard_integrator.py` (PRD-158). PRD-157 added
config knobs (`ACCOUNT_EQUITY`, `MAX_RISK_PCT_PER_TRADE`), not a module;
PRD-160 added per-driver cyclicality *data* to the existing
`macro_tape_layout.py`; PRD-156 deleted the Moomoo subsystem
(`moomoo_parser/join/review.py`) that check #1 had evaluated — so the
one sidecar #1 reviewed is now gone. Everything else was tests, docs,
audits, or governance.

- **Q1 (new prediction logic?):** No. `dashboard_integrator` is a
  renderer-bound translation pass — it consumes existing regime / macro
  / setup values and re-expresses them in decision language; it
  recomputes nothing (PRD-158 § 4.3, module docstring). PRD-157 sizing
  is deterministic equity × risk-% arithmetic, not a market forecast.
  PRD-160 made the macro_bias *label* more descriptively accurate
  (per-driver cyclicality) — description, not prediction, and if
  anything a reinforcement of the non-goal.
- **Q2 (new sidecar without consumer or observational purpose?):** No.
  No new sidecar landed. `dashboard_integrator` is not a sidecar — it is
  a delivery-layer pass whose immediate in-process consumer is the
  renderer (`render_dashboard_html`), pinned as translation-only (no
  second source of truth) by the PRD-158 guardrail entry in this file.
- **Q3 (new module not serving the four questions?):** No.
  `dashboard_integrator` serves "what matters today / is this actually
  tradable / what invalidates" by collapsing contradictory dashboard
  state into trader-facing conclusions — squarely the
  cognitive-compression core value. It earns its keep.

**Verdict:** PASS. No prediction logic, no orphan sidecar, no module
that fails the four-questions test; the period was net-subtractive on
module count (one added, three removed). Next cadence check due
2026-07-03 (or the next phase boundary — e.g. the W4 pre-market-report
spine crossing into live trade specification — whichever comes first).

---

## 2026-05-24 — Retire hourly Telegram cadence; replace with three prescriptive PT-anchored reports

The PRD-141/144/148/149 hourly cadence + the daily/Sunday/intraday-mode
alert stack will be retired in favor of three PT-anchored Telegram
reports — 06:00 (pre-market: one fully-specified trade or NO TRADE),
09:30 (binary kill/hold against open positions), 13:30 (post-session
seed for tomorrow). Anchor: "will I actually use this when trading."
The hourly cadence produced more pulses than were read, and the
intraday-mode triggers layered on top without changing trading
behavior.

The prescriptive pre-market shape (strikes + calendar expiry + dollar
risk + account-equity-driven position size + debit-or-credit, all
ready to type into Moomoo) exposes real pipeline gaps. The current
contract emits symbol/direction/entry/stop/target but drops absolute
strikes, calendar expiry date, per-candidate dollar risk, and any
sizing tied to account equity (the current `max_contracts` formula in
`qualification.py:643` hardcodes a $150 base). These gaps become B1–B11
prereq PRDs that land before their consuming report unit.

Plan staged but not started — see
`audits/recon-2026-05-24/next-batch-staging.md`. PRDs are not drafted
yet; each work unit becomes its own PRD when picked up. The hourly
cadence stays alive until the pre-market report has earned trust in
production. Entry point on resumption: **B4 (account-equity sizing)**
— foundational pipeline work before user-facing reports, per the
dependency-respecting sequence in the plan.

Per VISION.md non-prediction binding, the kill list explicitly
excludes: probability-of-profit / EV / scenario-tree pre-market output,
multi-trade pre-market ranking, mid-session status interpretation,
auto-detection of open positions from broker statements or audit-log
ALLOW_TRADE rows (the latter assumes Dustin took every ALLOW_TRADE,
which is false; PRD-153/156 just established broker-statement
detection produces no joinable signal).

PRD-PRD link will be added here when W1 is drafted.

---

## 2026-05-23 — PRD-153 follow-up recon: three deferred items

PRD-153's real-data validation against the three local Moomoo
statements (602 trades, Feb/Mar/Apr 2026) produced zero joins. A
follow-up recon traced the cause through three layers:

1. **Audit-log sparsity** — `logs/audit.jsonl` has only 4 dates with
   pipeline records (4/28, 5/7, 5/12, 5/13). Zero overlap with the
   statement window (2/18 → 5/1).
2. **Test contamination** — 72 of 77 "pipeline records" had
   `report_path` pointing to pytest tmpdirs. Historical residue from
   runs predating the test-isolation guards landed by `a46a792`
   (2026-05-09, per-test patch) and `8b4e654` (2026-05-10, autouse
   fixture). Both guards are in place at HEAD; the residue is the
   only remaining defect. **PRD-154** scrubs the residue.
3. **Audit-write coverage gap** — only `_run_pipeline` (used by
   `live`/`sunday`/`fixture` modes) writes pipeline records.
   `_execute_notify_run` (used by `hourly`/`post_orb`/
   `orb_trajectory`/`midmorning`/`power_hour`/`market_close`) writes
   none. Healthy production therefore yields ≤1 pipeline record per
   trading day — a structural cap on `moomoo_review`'s join density.

PRD-154 closes layer 2. Three items from layers 1 + 3 are
**explicitly deferred** here and not folded into PRD-154's scope:

- **Audit-write coverage doctrine.** What is `logs/audit.jsonl`
  supposed to record — one row per pipeline invocation, per
  decision, or per mode? Until this is settled, density-driven
  changes to `moomoo_review` are premature. Needs its own scoping
  PRD before any consumer-side join changes.
- **2026-04-29 / 2026-04-30 anomaly.** Eight successful
  `Cuttingboard Pipeline` scheduled runs each day per `gh run list`,
  zero records retained. Likely the `live` slot was in the failed
  cohort while the notify-only slots (which write nothing
  pipeline-shaped by design) succeeded; confirmation requires
  per-run workflow log inspection. Cheap to investigate; not on the
  critical path.
- **Tag-precedence in `cuttingboard/moomoo_join.py:183-189`.** Empty
  `date_records` causes out-of-universe trades to be tagged
  `no_audit_for_date` rather than `underlier_not_in_audit_universe`.
  Technically correct per PRD-153 but collapses the tag
  distribution when audit coverage is patchy. Wait until the
  coverage doctrine settles — tag distributions are only meaningful
  when audit density is non-degenerate.

Recon trail and analytic outputs live in this session's transcript
(2026-05-22 → 2026-05-23). No `audits/` artifact committed; the
findings worth preserving are captured above and in PRD-154's GOAL
and NOTES sections.

---

## 2026-05-22 — Phase 1 formally exited; Phase 2 ratified

Phase 1 (per VISION.md: inventory, cleanup, Gap-Down Permission
Gating, alignment audit) is **complete**. Step-by-step:

1. Inventory audit — `audits/inventory-2026-05-22/`
2. Consolidated cleanup — 10 commits between `c5355e0` and
   `2d929bf` (Polygon, ntfy, orphan modules, dead functions,
   unused deps, root cruft)
3. Gap-Down Permission Gating — pre-existing, retroactively
   documented as PRD-151 (`5bf9680`)
4. Architectural alignment audit — `audits/alignment-2026-05-22/`,
   headline verdict **ALIGNED**, Part B doctrine updates in
   `d9b430b`

The Phase 1 → Phase 2 gate was therefore satisfied before PRD-153
(Moomoo Statement Consumer, `5ec073e` + `a1993b9`) shipped. PRD-153
is on-vision Phase 2 work, not a gate-jump.

This entry is recorded in DECISIONS.md because the Phase-1
completion status currently lives in `docs/PROJECT_STATE.md § Next
step`, which rotates when the next PRD ships. DECISIONS.md is the
durable record.

---

## 2026-05-22 — Pre-L7 audit recon findings accepted as descriptive-only design (no new debt)

The 2026-05-22 pre-L7 audit visibility recon
(`audits/recon-2026-05-22/l4-l5-audit-visibility.md`) surfaced
three findings that were originally deferred "to Phase 2 scoping."
Phase 2 has now shipped (PRD-153), so the deferral wording is
stale and the findings need an explicit decision per VISION.md
("acknowledged debt requires a re-evaluation date").

**Decision: accept all three as descriptive-only design.** PRD-153
emits a closed-set blind-spot tag system (`gap_down_short_suppressed`,
`notify_mode_only`, `expansion_data_incomplete_ambiguous`,
`no_audit_for_date`, `underlier_not_in_audit_universe`) at the
post-hoc evaluation surface in `logs/moomoo_review.jsonl` and
`reports/moomoo/<YYYY-MM>.md`. The visibility need that motivated
the recon — "can a Moomoo trade be evaluated against an audit
record without false attribution?" — is met at the descriptive
surface, not at the audit-record surface.

Specifically:

- **Gap-down suppression invisibility.** Covered by the
  `gap_down_short_suppressed` tag; PRD-153 join logic correctly
  attributes a suppressed SHORT to the gate rather than to data
  quality.
- **Notify-path context discard.** Covered by the
  `notify_mode_only` tag; trades from notify-mode runs are
  attributable as such without requiring the audit record to
  carry the discarded context dict.
- **Reject-stage misattribution.** Same `gap_down_short_suppressed`
  tag prevents downstream "data quality" misattribution at the
  evaluation layer.

The underlying `logs/audit.jsonl` invisibility remains by design.
This is a "description, not prediction" application: rather than
expanding the audit log to make the gate visible (predictive of
what an analyst might want), the descriptive evaluation surface
names the blind spots where they actually matter.

No re-evaluation date because this is accepted-as-design, not
deferred. Reopen if a real-data usage pattern shows the
descriptive tags are insufficient — that would be a new finding,
not a continuation of this one.

---

## 2026-05-22 — Alignment cadence check #1 (post-VISION baseline) — PASS with Q3 question refinement

First alignment cadence check since VISION.md was introduced (same
day — so this establishes the post-VISION baseline rather than
measuring drift). Scope: all production code added since VISION.md.
Only PRD-153 landed new modules (`cuttingboard/moomoo_parser.py`,
`moomoo_join.py`, `moomoo_review.py`); everything else was cuts,
docs, audits, tests, or governance.

- **Q1 (new prediction logic?):** No. PRD-153 modules declare
  read-only/descriptive in their docstrings; blind-spot tags are
  observational labels on already-executed trades, not forecasts.
- **Q2 (new sidecar without consumer or observational purpose?):**
  No. PRD-153 is the canonical-shape sidecar — read-only against
  `logs/audit.jsonl`, output channels `reports/moomoo/<YYYY-MM>.md`
  and `logs/moomoo_review.jsonl`, consumed by Dustin.
- **Q3 (new module not serving the four questions?):** Surfaced a
  definitional gap, now fixed. The Moomoo consumer is
  backward-looking (post-hoc trade evaluation) while the four
  questions are forward-looking. VISION.md Phase 2 explicitly
  endorses the consumer, but Q3 as originally written didn't
  accommodate phase-named work. Amended Q3 in `CLAUDE.md` to read
  "...AND isn't an explicitly-named VISION.md phase deliverable."
  With that amendment, Q3 answers No.

**Verdict:** PASS. No drift, no surprise additions. Next cadence
check due 2026-06-19 to 2026-07-03 (4-6 weeks).

---

## 2026-05-22 — Post-VISION workflow tightening (Explore-vs-Codex, parallel reviews, real-data validation skill, memory init)

Six small workflow improvements landed in one pass after a
retrospective on the post-VISION.md PRD cycle (PRDs 151-153).
Triggered by the observation that VISION.md itself is enforced
(PRD-150 kill, [[project_vision_is_active]]) but the surrounding
workflow still carried pre-VISION habits.

### Explore subagent supersedes Codex for codebase recon

`CLAUDE.md` "Workflow patterns" rewritten. The built-in `Explore`
subagent (and `general-purpose`) is the default for codebase recon
— cross-file consistency checks, scoped reads, "where is X used"
sweeps — because it runs locally without an external model call.
Codex is reserved for what only Codex offers: a genuinely
independent second model for PRD cross-review and structured code
review. The pre-L7 audit recon at
`audits/recon-2026-05-22/l4-l5-audit-visibility.md` is the
canonical shape of a task that should now be `Explore`, not Codex.

### Parallel PRD review is the default, not the exception

`docs/PRD_PROCESS.md` gained a "Review Dispatch" section. Claude
vision review and Codex cross-review are independent and dispatched
in parallel from a single message, not serially. The PRD-150 arc
ran serially and the second review's findings did not depend on
the first — pure wall-clock waste. The rule is doc-level rather
than skill-enforced because skills are invoked deliberately anyway;
discipline failure would not be fixed by mechanical enforcement
(see [[feedback_cuts_before_additions]] applied to workflow tooling
itself).

### Real-data validation codified as a skill + thin harness

The validate-then-fix pattern from PRD-153 closeout
([[feedback_validate_then_fix]]) is now a reusable skill:
`.claude/skills/real-data-validation/SKILL.md` plus
`scripts/validate_consumer_prd.py`. The harness runs a
single-argument consumer callable against a real-data fixture and
scaffolds `docs/prd_history/PRD-NNN.validation.md` with the captured
output and an amend-vs-spawn defects template. The skill walks
Claude through preconditions, defect classification, resolution,
and re-run. Smoke-tested against PRD-153's real fixture (Feb 2026
Moomoo statement, 41 normalized trades captured cleanly).

The harness is intentionally minimal — single-arg callable,
repr-based capture, no golden-file diffing. Extending it is
deferred until a second CONSUMER PRD with a different signature
forces the question.

### Codex/subagent artifact links in DECISIONS.md

New convention: when a Codex or subagent artifact materially
drives a decision (KILL, REVISE, scope cut), link the artifact
path in the `docs/DECISIONS.md` entry. Recorded in CLAUDE.md
"Workflow patterns". Thickens the audit trail without ceremony —
the artifact is already written, this just makes the link durable.

### Full test suite runs backgrounded

CLAUDE.md updated: the full suite (297 tests, long enough to
justify it) runs via `run_in_background` once before pre-commit,
freeing foreground work in parallel. Habit, not enforcement.

### Memory system seeded

`~/.claude/projects/-home-dustin-Projects-cuttingboard/memory/`
initialized with `MEMORY.md` + five entries: user profile, three
feedback memories (cuts-before-additions, validate-then-fix,
amend-vs-spawn), one project memory (vision-is-active). Future
sessions read condensed lessons rather than re-deriving them from
CLAUDE.md every time.

**Scope of this entry:** these are workflow/governance changes,
not PRD-scoped. No PRD-NNN bookkeeping needed; this DECISIONS
entry is the artifact. n=1 for the parallel-review rule and the
real-data-validation skill — both will need a second data point
(next PRD with two reviews, next CONSUMER PRD) to confirm the
shape is right.

---

## 2026-05-22 — PRD-153 closeout decisions (validate-then-fix pattern, scope-fold call, ticker-less equity tradeoff)

PRD-153 (Moomoo Statement Consumer) shipped via two commits — `5ec073e`
(initial implementation against the synthetic fixture) + `a1993b9`
(parser fidelity fixes after real-statement validation surfaced six
defects). Three decisions from that arc worth recording, beyond what
the PRD doc captures inline.

### Validate-then-fix as the implementation pattern for CONSUMER-class PRDs touching external data formats

The synthetic fixture established structural confidence — every R1
row type rendered, parser tests green, CLI smoke clean. The
real-PDF validation step surfaced six defects the synthetic could
not have caught: Expired-Option layout (no Price column), bare `*`
description-tail token, wrapped `E-transfer\nDeposit` Type cell,
unrecognized Cash Rebate row type, multi-word equity descriptions
without a ticker, plus the column-width text-extraction quirk that
collapsed `Feb 17, 2026E-transfer` into a single token in the
first synthetic regeneration.

Codifying this: for any future CONSUMER-class PRD whose contract
includes "consumes an external data format we don't control," the
implementation cycle is **synthetic fixture → real-data validation
→ defect fix in same cycle**, not **synthetic fixture → ship → wait
for production drift to surface the gap**. The real-data validation
step is not "QA," it's part of the implementation. The PRD itself
should call out which validation samples exist and where.

### Cash Rebate folded into PRD-153 scope rather than spawned as a follow-up PRD

Cash Rebate was discovered as an unrecognized row type during the
real-statement validation pass. Options were:

1. Add to PRD-153 R1 via amendment, implement in same closeout cycle.
2. Defer to a follow-up PRD (PRD-154 or PATCH PRD-153) so the
   PRD-153 scope statement stays "as originally written."

Chose (1) because: same domain (CASH row type), same shape (one
trailing numeric, no underlier/option), trivial implementation
(one entry in `_TYPE_PREFIXES`), and the user would have to
re-context the same code to do (2). The PRD-153 R1 amendment is
explicit about the addition and the provenance is recorded in the
PRD NOTES section. The bar for amend-vs-spawn: amend if the new
scope item is the same domain, fits inside the existing requirement
shape, and adds < ~10 LOC; spawn a follow-up if any of those fail.

### Ticker-less equity fallback: correctness over coverage

Real Moomoo PDFs render some equity rows with multi-word company
descriptions and no ticker symbol (e.g.
`ETF OPPORTUNITIES TR T REX 2X`, `ISHARES SVR TR`,
`HYCROFT MINING HLDG CORP CL A`). PRD-153's join logic uses
`underlier` as the join key against `logs/audit.jsonl`. Two options:

1. Guess `underlier` from the first description token. Cheap.
   Wrong: would mis-attribute `ETF` rows to a nonexistent universe
   symbol and fire `underlier_not_in_audit_universe` for the wrong
   reason.
2. Yield `underlier=None`, `instrument_class="EQUITY"`. Costs
   join coverage on those rows. Correct: a row with no resolvable
   ticker emits no blind-spot attribution and contributes nothing
   to the join, which is the honest behavior given the input.

Chose (2). The principle: false-negative blind-spot attribution
poisons the descriptive surface PRD-153 exists to provide. Coverage
loss on un-tickerable rows is bounded and honest. Generalises: when
a descriptive-only consumer faces ambiguous input, drop the row
from the descriptive surface rather than fabricate a description.

Single-commit-shape note (parser + fixture + tests bundled into
`a1993b9` to keep `git bisect` green) skipped — that's a generic
workflow principle that doesn't need codifying.

---

## 2026-05-22 — Pre-L7 audit visibility recon completed; fixes deferred to Phase 2 scoping

Codex completed the pre-L7 audit visibility recon at
`audits/recon-2026-05-22/l4-l5-audit-visibility.md`. The recon answered
a narrow factual question: across the boundary from
`generate_candidates(...)` to `qualify_all(...)` in current
production code, what is captured by `logs/audit.jsonl` and what is
not.

Verdict: **BOUNDED-TO-GAP-DOWN**. `_apply_intraday_short_permission`
(PRD-151) is the only production operation that removes generated
candidates before `qualify_all(...)`. Its removals are invisible in
`logs/audit.jsonl` — no pre-filter candidate list, post-filter
candidate list, removed-symbol list, or gap-down reason field is
written. The existing `suppressed_candidates` audit field is fed by
`apply_sector_router(...)` post-qualification, not by the gap-down
gate (`cuttingboard/runtime.py:821-825, 1036`;
`cuttingboard/audit.py:227`).

The recon surfaced three observability findings of different stakes:

- **Gap-down suppression invisibility (primary).** Suppressed SHORT
  candidates leave no audit trace and are absent from
  `qualified_trades`, `trade_decisions`, `near_a_plus`,
  `excluded_symbols`, and `suppressed_candidates`. Directly affects
  Phase 2 join completeness: the Moomoo statement consumer joining
  executed trades against `logs/audit.jsonl` cannot count a
  gap-down-suppressed SHORT as a decision surface from the audit
  record alone.
- **Notify-path context discard (secondary).** The helper's returned
  `context` dict is preserved by the daily/live call site at
  `runtime.py:805` (bound to `intraday_state_context`, propagated to
  the audit) but discarded by the notify-mode call sites at
  `runtime.py:489` and `runtime.py:518` (bound to `_`). Surviving
  SHORT candidates in notify mode therefore lack the intraday context
  fields that daily-mode records carry. Asymmetry in audit
  propagation, not in gate behavior; PRD-151's description of the gate
  remains accurate.
- **EXPANSION continuation misattribution (tertiary).** In EXPANSION
  regime, `qualify_all(...)` iterates `structure_results` rather than
  the candidate dict (`cuttingboard/qualification.py:216-228`). A
  gap-down-suppressed symbol can still be considered by continuation
  logic, but because `ohlcv` is built only for the filtered candidate
  dict, the suppressed symbol has no `df` and continuation rejects it
  as `DATA_INCOMPLETE` (`qualification.py:595-605`). The audit's
  reason chain therefore misattributes a suppression-downstream
  rejection to a data-quality cause.

### Decision

All three findings are observability concerns. Per VISION.md
("description, not prediction" and "cuts before additions"), no
visibility PRDs are opened to remediate them in advance of Phase 2.
The findings are named here as known blind spots, made explicit
inputs to Phase 2 scoping, and the Phase 2 PRD will decide which
(if any) require pre-Moomoo-join remediation versus which the
extension can ship descriptively-with-known-blind-spots.

No PATCH PRD for PRD-151. The gate's behavior matches PRD-151's
description; the notify-path asymmetry is a caller-side audit
propagation concern, not a gate-behavior concern. Folding it into
PRD-151 would muddle the PRD's scope.

### Out-of-scope finding to capture separately

The recon's §8 honest limits notes that `continuation_audit` is
populated in run-summary structures in `cuttingboard/runtime.py` but
is not written to `logs/audit.jsonl`. This is a standalone audit
completeness gap independent of gap-down suppression. To be added to
`docs/PROJECT_STATE.md § Known technical debt` with a re-evaluation
date, per VISION.md's acknowledged-debt principle.

### Layer-numbering correction

The recon brief used "L4→L5" to describe the
`generate_candidates → qualify_all` code boundary. `docs/architecture.md`
labels derived metrics as L4, regime as L5, and qualification as L7
(`architecture.md:102-149`). Codex correctly interpreted the brief's
intent as the code boundary and surfaced the mismatch in §8.
Subsequent references to this boundary in DECISIONS.md, PRD drafts,
and recon outputs should use "pre-L7" or "pre-qualification" rather
than "pre-L5".

### Phase 2 scoping inputs

When Phase 2 scoping opens, the scope statement must explicitly name:

1. Gap-down-suppressed SHORT candidates are invisible to the audit
   record and therefore to any Moomoo statement join.
2. Notify-mode audit records lack the intraday context fields present
   in daily-mode records for surviving candidates.
3. EXPANSION-regime `DATA_INCOMPLETE` rejections can be caused by
   upstream gap-down suppression rather than by genuine data quality
   issues; reason attribution in the audit is not a reliable signal
   for that distinction.

Phase 2 then decides, per finding, whether the extension requires
remediation as a precondition or can ship descriptively with the
blind spot named.

---

## 2026-05-22 — Architectural alignment audit Part B doctrine updates

Phase 1 step 4 — the architectural alignment audit at
`audits/alignment-2026-05-22/` — completed with headline verdict
**ALIGNED**: zero violations, four tension points surfaced, sidecar
discipline verified across all five sidecars, prediction-vs-description
scan clean, all seven VISION.md non-goals clean, 8/8 sampled PRDs match
code. Part B addresses the surfaced tensions via doctrine and doc
updates (no code under `cuttingboard/` touched except the
`watchlist_sidecar.py` docstring).

Outcomes:

- **Watchlist sidecar retained with clarified purpose.** Updated
  `cuttingboard/watchlist_sidecar.py` docstring to declare it an
  observation sidecar serving the human reader for tickers researched
  outside the primary trading universe. The "no v1 consumer" tension
  surfaced in the audit was a category error — the human reader is the
  consumer, and that is a valid sidecar role.
- **Sidecar doctrine updated to distinguish categories.** Added a
  two-category section at the top of `docs/sidecar_doctrine.md`:
  decision-feeding sidecars (must have a documented downstream module
  consumer; examples `market_map.py`, `macro_pressure.py`) versus
  observation sidecars (consumed by renderer/notifications for human
  reading; examples `watchlist_sidecar.py`, `trend_structure.py`,
  `market_map_lifecycle.py`). New sidecar PRDs must declare category.
- **Market map current_price backfill documented.** Added a doctrine
  note that `market_map_lifecycle.inject_lifecycle` performs an
  intentional cross-run `current_price` backfill when current data is
  `None`, propagating prior-run pricing into the renderer-facing
  lifecycle annotation. Description-side accommodation, not forecast;
  no decision module reads the lifecycle block.
- **VISION.md Phase 2 re-framed.** Replaced "Trade evaluation sidecar"
  with "Trade evaluation extension" wording that acknowledges
  `evaluation.py` and `performance_engine.py` already implement
  same-session evaluation. Phase 2's remaining work is the Moomoo
  statement consumer joined to L10 audit output.
- **Alignment cadence pattern added to CLAUDE.md.** New
  § Alignment cadence section codifies a 4-6 week or phase-boundary
  scoped check against VISION.md (three questions: new prediction
  logic? new sidecar without category? new module not serving any of
  VISION.md's four questions?). Cadence is now active per
  `docs/PROJECT_STATE.md`; next scheduled check by 2026-07-03.
- **Acknowledged-debt operating principle added to VISION.md.** New
  bullet under § Operating principles: acknowledged debt requires a
  re-evaluation date in `PROJECT_STATE.md`. Open-ended deferral is
  drift dressed as discipline.
- **runtime.py re-evaluation date set: 2026-08-15.** 12 weeks from the
  alignment audit, intended to land before Phase 2 PRD drafting if
  possible, otherwise immediately after Phase 2 ships. Recorded in the
  `docs/PROJECT_STATE.md § Known technical debt` entry alongside the
  existing scoping reference (PRD-135 milestone).

### Deferred follow-ups (not in this commit)

- **Batch B — compatibility shim removal.** `cuttingboard/sector_router.py`
  (three stub pass-throughs) and the no-op helpers in
  `cuttingboard/universe.py` (`filter_execution_dict`,
  `filter_execution_items`, `log_universe_configuration`) are
  kill candidates flagged in `audits/alignment-2026-05-22/`
  Flag 2. Scoped as a separate PRD because removing them requires
  call-site updates in `runtime.py` and import surface review.
- **Batch C — runtime Group 6 refactor.** First natural cut from
  `audits/alignment-2026-05-22/06-runtime-monolith.md`: extract the
  sidecar wiring + write helpers (`_load_previous_market_map`,
  `_write_market_map_file`, `_tradable_symbols`,
  `_write_trend_structure_snapshot`, `_refresh_trend_structure_sidecar`,
  `_write_watchlist_snapshot`, `_write_macro_snapshot`,
  `_write_payload_artifacts`) into `cuttingboard/runtime/sidecars.py`.
  Scoped as a HIGH-RISK lane PRD per PRD-121 R11; bounded by the
  2026-08-15 re-evaluation date.

---

## 2026-05-22 — Gap-Down Permission Gating governance gap closed (PRD-151 retrospective)

The PRD-150 coupling recon at
`audits/recon-2026-05-22/gap-down-prd150-coupling.md` surfaced that
Gap-Down Permission Gating — listed as "in flight, needs
implementation" in VISION.md and PROJECT_STATE.md — was already
implemented in production: `cuttingboard/intraday_state_engine.py`
defines `classify_gap`, `downside_short_permission`, and supporting
state types; `cuttingboard/runtime.py:1205 _apply_intraday_short_permission`
filters SHORT candidates pre-qualification at three call sites
(`runtime.py:489, 518, 805`); test coverage exists at
`tests/test_gap_down_permission_integration.py` (4 integration tests)
and `tests/test_intraday_state.py` (8 gap-down unit tests). The
feature predates VISION.md being written; the governance docs were
never updated to reflect what shipped.

Resolution:

- Wrote PRD-151 at `docs/prd_history/PRD-151.md` documenting the
  as-built behavior with STATUS = COMPLETE on first write, full
  R1–R9 requirements derived from the existing code, an
  invalidation-conditions section describing what would make the
  feature wrong or unneeded, and an explicit NOTES section flagging
  this as the first instance of the retrospective-documentation
  pattern.
- Updated `docs/PRD_REGISTRY.md` and `docs/prd_index.json` to
  include PRD-151 as COMPLETE; `latest_complete` advanced to 151
  and `next_prd` to 152.
- Updated `VISION.md`: Gap-Down Permission Gating moved from
  "in flight" to "built and in use"; Phase 1 step 3 marked as
  already complete with a note that the realignment discovered it
  was implemented prior to VISION.md being written. PRD-150's
  PROPOSED entry in "in flight" was already gone from the cleanup;
  the section is now "none."
- Updated `docs/PROJECT_STATE.md`: `Last completed PRD` advanced to
  PRD-151; `Next step` advanced to Phase 1 step 4 (architectural
  alignment audit). Steps 1–3 of Phase 1 are complete.

### Precedent for future drift

This is the first instance of a feature shipping ahead of (or
without) its PRD in cuttingboard's recorded history. The
resolution pattern is:

1. **Retrospective documentation, not silent acknowledgment.** When
   code and governance docs diverge and the code is correct, the
   resolution is to write the PRD that should have existed — not
   to quietly delete the "in flight" line from VISION.md.
2. **STATUS = COMPLETE on first write.** Retrospective PRDs do not
   pass through PROPOSED / IN PROGRESS. The work is already
   committed across many prior commits; the PRD is documenting it,
   not authorizing it.
3. **Explicit NOTES section flagging the retrospective nature.** So
   future readers don't mistake the file for prospective work and
   try to "implement" it.
4. **No COMMIT PLAN section.** The work is already committed.
5. **Invalidation conditions are mandatory.** Because the
   retrospective PRD is the first written record of the feature's
   intent, it must include the conditions under which the feature
   becomes wrong or unneeded — these would normally be implicit in
   the prospective PRD's GOAL / OUT OF SCOPE language but here
   they're explicit because there's no prospective record.

Future drift of this shape (feature implemented without a PRD,
discovered later) should follow this pattern. Silent acknowledgment
("just delete the in-flight line") is forbidden because it loses
the institutional memory that comes with a PRD record.

If the drift is in the other direction (PRD exists, code doesn't
match it), the PATCH PRD path applies (`CLAUDE.md § PRD documentation
rule`) — that's already a documented pattern.

---

## 2026-05-22 — PRD-150 killed

PRD-150 (Five-Tier Symbol Classification System) flipped from
`PROPOSED` to `DEPRECATED` in `docs/PRD_REGISTRY.md`. The proposal
file at `docs/prd_history/PRD-150.md` is retained intact as historical
record.

Rationale: vision review at
`audits/recon-2026-05-22/prd-150-vision-review.md` found the PRD's
realizable behavior insufficient to justify its surface area. Across
four Codex cross-review passes the realizable output of the main
visibility channel (the new CLASSIFICATION rejections stage) shrank
from "five tiers, every evaluated symbol" to one tier in practice —
post-R5 PRIME→QUALIFIED demotions via concentration cap or
flow-gate. The other four tiers route through pre-existing channels
and are dedupe-guarded out of the new emission. Two new modules,
contract value-space expansion, a new sidecar artifact, a
notification path split, and a postmarket counter refactor —
in service of one new realizable emission case — fails VISION.md's
"cuts before additions" standard and the behavioral test
("does this change what Dustin actually does, or just help him feel
more informed?").

Salvageable elements captured in the same commit:
`docs/architecture.md` records the `block_reason == decision_trace["reason"]`
contract invariant surfaced in Codex Pass 2. `CLAUDE.md` workflow
patterns gain three PRD-author disciplines surfaced across the
review arc: dead-branch enumeration, downstream-consumer audit, and
realizability check.

If a narrower follow-up captures the PRIME-only notification gating
(the one substantive behavior nudge in PRD-150, implementable as
~10 LOC standalone), it should be drafted as a new PRD against
VISION.md from scratch — not a revision of PRD-150.

---

## 2026-05-22 — Phase 1 realignment

Executed VISION.md-anchored cleanup. See `audits/inventory-2026-05-22/`
for the audit that surfaced the cleanup scope and
`audits/cleanup-2026-05-22/` for verification findings.

Key decisions:

- Polygon integration removed (never used in production).
- ntfy references removed from docs (PRD-006 already removed the code).
- Legacy intraday entrypoint `run_intraday.py` deleted (the live engine
  is `intraday_state_engine.py` consumed by `runtime.py`).
- LLM-driven macro sidecar `tools/macro_collector.py` deleted (no
  consumer; latent risk of crossing description/prediction line).
- Backtesting harness deleted (contradicts VISION non-goal).
- ORB Pine script and reference module deleted; rebuild intent
  documented at `pinescripts/README.md`.
- PRD-053 / PRD-053-PATCH reconciled to `COMPLETE` (landed alongside
  PRD-054; registry's `READY` status was stale recordkeeping —
  verified by comparing `cuttingboard/market_map.py` against the
  PRD-053 spec; full enum + schema + read-only-sidecar match).
- PRD-142 deprecated; workflow change never landed and VISION schedules
  it for kill.
- AGENTS.md deleted as redundant with CLAUDE.md. The file is
  auto-generated by GitNexus; the existing
  `scripts/gitnexus-analyze.sh` wrapper passes `--skip-agents-md` so
  re-generation is suppressed when that wrapper is used. AGENTS.md is
  already in `.gitignore` (line 65), so accidental regeneration via
  `npx gitnexus analyze` direct invocation won't re-enter the repo.
- CLAUDE.md and CODEX.md rewritten as lean skeletons that point at
  canonical source-of-truth documents instead of duplicating them.
- PROJECT_STATE.md elevated as canonical current-state source.

### Polygon key exposure — accepted post-rotation

Gitleaks found 109 historical exposures of `POLYGON_API_KEY` across
`.env`, `logs/intraday.log` (commit `27b2a35a`), two
`logs/run_*.json` artifacts, and one daily report. All from the same
single value, captured by Python logging of the Polygon URL's
`?apiKey=` query string before `logs/` was gitignored at PRD-096
(commit `4e9e34b`).

Repo is public (`https://github.com/dwats250/cuttingboard`). Decision:
**rotate the key out-of-band and accept the leak as historical**.
No git history rewrite. Rationale: post-rotation the leaked value is
worthless; rewriting 714 commits would invalidate any existing clone
and force collaborators (current or future) to re-clone, while the
secret already exists in any prior clone, fork, or archive. The
Polygon code path that produced the leak is removed in this same
cleanup, so the leak cannot reoccur.

### Inventory audit corrections

Two specific inventory-audit assumptions were wrong and were
corrected in verifications:

- `numpy` *is* directly imported by `tests/test_derived.py:11` —
  retained in `pyproject.toml`. The inventory audit speculated
  otherwise.
- `AGENTS.md` is auto-generated by GitNexus; the audit treated it
  as a hand-authored file. Approach above accounts for this.

### 2026-05-27 — PRD-158 dashboard_integrator drift guardrail

`dashboard_integrator` (`cuttingboard/delivery/dashboard_integrator.py`)
is a renderer-bound translation pass with 4 rules. Adding a 5th rule
requires a new PRD with audit evidence of a rendered contradiction.
If this function grows scoring, recomputation, upstream reconciliation,
or discretionary decision logic, it has drifted into a decision layer
and must be cut back or removed.

### 2026-05-24 — PRD-156 closeout: a consumer without a named producer is dead code

PRD-153 (Moomoo Statement Consumer Phase 2) shipped a join layer
between `logs/audit.jsonl` and parsed Moomoo PDF statements on the
assumption that intraday audit-write coverage existed. The PRD-155
audit doctrine (`docs/audit_doctrine.md`, 2026-05-23) codified that
`logs/audit.jsonl` is structurally a ~1-record-per-pipeline-invocation
stream — and that future audit-write expansion requires a *named
consumer* per Rule 1. The Moomoo consumer was that named consumer
turned out to be the only one, and the join data it produced was not
actionable. The subsystem was kept alive only by its own existence.

PRD-156 (commit `3c6fcb4`, 2026-05-24) deleted the entire Moomoo
subsystem — 3 production modules, 3 test modules, fixtures, generated
artifacts, `pdfplumber` + `reportlab` dependencies — ~1,376 LOC net
deletion. PRD-153 is flipped to DEPRECATED with a pointer to PRD-156.

**Lesson:** a consumer that was built to produce data which no other
consumer reads is itself dead code. The audit doctrine's "named
consumer or no write" rule applies inductively: if the only justification
for a subsystem is its own output, and that output has no downstream
reader, the subsystem is the wrong thing to keep alive when the
underlying assumption turns out to be wrong.

**Applied as a process discipline:** before shipping any new consumer
of `logs/audit.jsonl` (or any other sidecar), name the downstream
reader explicitly in the PRD. If the named reader is the consumer
itself, that is the signal to stop, not to ship.
