# Decisions log

Meaningful decisions and rationale. Date-ordered, newest first.
Short notes, not ceremony.

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
