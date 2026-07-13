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

## 2026-07-13 — PRD-256 R2 ruling: FIX, not PERMANENT

Ruled by Dustin, reading R1's corrected characterization (below and
`docs/prd_history/PRD-251.continuation-path.proposal.md`'s "PRD-256 R1"
section) after both fresh-context review passes and the bot-review
disposition landed. Recorded per PRD-256's own R2 FAIL condition
("R3 or R4 work begins before R1's analysis is implemented AND a dated
DECISIONS.md entry records which branch was ruled").

**Grounds.** The continuation path is not sizing off an inaccurate
estimate — `options.py::build_option_setups` DISCARDS the qualification
layer's proxy figure and re-sizes off a fixed, ATR-independent value,
deliberately bypassing the strategy-aware sizing PRD-251 applied
everywhere else. This is a code path that opted out of the sizing model,
understating CREDIT-strategy max loss by a flat 2.333x, always, every
trade. There is no honest PERMANENT branch: ruling PERMANENT would
require writing into this file that the continuation path ignores
strategy-aware sizing and understates credit max loss by 2.333x BY
DESIGN — that is not a design. The `CONTINUATION_MAX_RISK_PCT_PER_TRADE
= 0.01` decouple has been a fence around a bypass, not a conservative
estimate. That the factor is flat rather than regime-dependent makes the
fix cleaner, not less urgent — not because any real trade has already
been mis-sized (R1's own evidence: zero continuation candidates have
ever been accepted, captured-run and replay data agree — see the
proposal doc and the HOLD-confirmation-gate ticket), but because the
first credit continuation candidate that ever clears HOLD would be sized
wrong by this exact factor, with no additional discovery needed.

**What this does NOT authorize.** R2 rules the direction; it does not
authorize Phase 2 (R3) to begin. R3 gets its own dispatch, informed by
this ruling, once the FIX-branch scope (which of the proposal doc's
candidate approaches, or a narrower one now that layer 2 already has a
working width concept via `strike_distance` — see the corrected R1
characterization) is decided separately.

`docs/prd_history/PRD-256.md` amended (FILES + R1 text + this ruling
pointer) same-PR per its own falsified-contract justification below.

## 2026-07-13 — Diff-scoped review is structurally blind to consumer-side re-derivation (third instance)

Pattern note, not a new finding: three separate PRDs now had their
highest-value catch come from a sweep that went OUTSIDE the diff under
review, never from the diff-scoped leg examining the changed lines in
isolation. PRD-252: Sol's commissioned Codex disposition, sweeping past
PRD-252's own diff, found the `contract.py`/`audit.py` correlation-modifier
sourcing gap (tracked as PRD-253). PRD-253: the same class recurred one
layer down. PRD-256: `chatgpt-codex-connector[bot]`'s review, running
exhaustive/out-of-diff mode, found that `options.py::build_option_setups`
— a file PRD-256's PR never touched — silently discards and re-derives
the qualification layer's sizing figure, which both a same-context
implementer pass and an adversarial fresh-context orchestrator/retriever
review (itself designed to recompute every number independently) missed,
because neither was charged with tracing a value to its actual
downstream consumer — only with verifying the value's own internal
arithmetic. The fix is a mandatory consumer sweep as a named step in any
characterization or sizing-logic charge ("trace this value to whatever
actually renders/audits/executes it, not just to the function that
computes a plausible-looking number"), not a better or more skeptical
reviewer — the reviewers involved across all three instances were
already adversarial by design and still missed it until something swept
outside the diff.

## 2026-07-13 — PRD-256 Phase 1/R1 corrected: the qualification-layer characterization measured the wrong layer

`chatgpt-codex-connector[bot]`'s review of PR #145 found that the
2026-07-12 R1 characterization below (and the fresh-context review that
ACCEPTed it, `docs/prd_history/PRD-256.review.claude.md` @ `0ca2523`)
measured `_qualify_continuation_candidate`'s ATR-based proxy in isolation
and treated its `dollar_risk` as the number the system acts on. It is
not: `cuttingboard/options.py::build_option_setups` re-sizes every
continuation result from a completely different, ATR-independent figure
(`_estimated_debit(strike_distance) = 0.30 * strike_distance`, fixed at
$0.75/share stock or $1.50/share ETF) and, per an explicit in-code guard
(`result.entry_mode != ENTRY_MODE_CONTINUATION`), NEVER applies PRD-251's
already-correct `_max_loss_for_strategy` value to continuation results —
discarding the qualification layer's ATR-scaled dollar figure entirely
(`options.py:210,253-261`; `tests/test_phase5.py:533-559`).

Re-characterized by direct execution of the real, unmodified
`build_option_setups` (not a re-derivation) against real ATR14 for all 16
tradable symbols, three `risk_modifier` values, and both the current and
hypothetical uncoupled budget: for CREDIT-resolving continuation results,
real max loss is **exactly 2.333x (0.70/0.30)** what's actually charged
and audited — constant, not ATR-dependent, not a 4x-9x range. This is not
merely "the same class" as PRD-251's bug; it is the literal identical
unfixed arithmetic, reached through a path that deliberately excludes
continuation results from the fix applied everywhere else. DEBIT
strategies remain a confirmed 1.000x (no gap) at this layer too. Full
corrected analysis: `docs/prd_history/PRD-251.continuation-path.proposal.md`
§ PRD-256 R1 (2026-07-12, corrected 2026-07-13).

The qualification layer's ATR-based proxy is not irrelevant — it still
sets `result.max_contracts`, one operand of a `min()` against layer 2's
fixed per-bucket contract cap, so ATR14 can still shift which contract
count gets sized (narrow-banded; see the corrected doc's section 5) — but
it never determines the dollar-per-contract understatement, which is
flat regardless of ATR.

The 2026-07-12 fresh-context review's ACCEPT WITH CHANGES does not carry
forward to this corrected version; a fresh review pass is required before
R2 rules on these numbers.

**Process note.** Both the implementer and the fresh-context reviewer
(orchestrator/retriever split, adversarial by design) independently
recomputed every number in the original characterization from real data
and still missed this — the arithmetic was internally consistent and
numerically correct at the layer both examined, so the review's
recomputation-heavy method verified precision within a layer without
questioning which layer was the right one to examine. Neither the PRD nor
the review charge asked "does this qualification-layer dollar_risk
actually reach the trader," so nothing prompted tracing the value past
`_qualify_continuation_candidate`'s return into its caller. Repo-level
"Exhaustive code review" (enabled 2026-07-13) surfaced it via an
out-of-diff trace into `options.py`, a file this PR never touched.
Worth carrying into future characterization charges: for any PRD whose
deliverable is "what does the system actually charge/size/render," the
charge should name tracing the value to its final consumer as an
explicit requirement, not assume the first function that computes a
plausible-looking number is the end of the path.

**Second bot-review round (2026-07-13, same day, on the correction
commit).** With Exhaustive code review now active, three more findings
landed on PR #145: (1) the v2 review artifact this section's correction
needed didn't exist yet at push time — ACTIONED once written (`af419da`);
(2) `logs/audit.jsonl` was mischaracterized as notification-transport-only
when it actually holds two record families (`docs/audit_doctrine.md`) —
635 notification + 5 genuine pipeline records, none showing continuation
data — ACTIONED (`e2765d6`); (3) **`docs/prd_history/PRD-256.md`'s own R1
requirement text still describes the superseded qualification-layer
formula and its DATA FLOW still omits `options.py`** — a real,
unresolved gap, correctly NOT patched here: `PRD-256.md` is not in
PRD-256's own FILES section, so rewriting its R1 contract is outside this
branch's scope-lock (CLAUDE.md: amend the PRD before editing a file it
doesn't authorize). Flagged for Dustin: either authorize a small FILES
amendment updating PRD-256.md's R1/DATA FLOW prose to name `options.py`,
or treat the proposal doc's CORRECTION NOTICE as the sufficient
source-of-truth update. Not ruled here — this is exactly the
rule-vs-practice class the 2026-07-11 entry ("rule-vs-practice gaps
discovered mid-PR are legislated at a gate, not patched in the PR that
found them") describes: surfaced at a gate, not resolved by the agent
that found it.

## 2026-07-12 — PRD-256 Phase 1/R1: continuation-path ATR proxy characterized against real market data

Quantified the max-loss understatement `docs/prd_history/
PRD-251.continuation-path.proposal.md` flagged and PRD-252 decoupled
around. Real ATR14 (Wilder RMA, via `cuttingboard.derived._wilder_atr`)
computed against the system's own cached OHLCV for all 16 real tradable
symbols, run through the real `_qualify_continuation_candidate` sizing
formula. Result, in full in the proposal doc's new R1 section: DEBIT
strategies carry no structural gap (real max loss = debit paid, by
construction); CREDIT strategies understate real max loss 4x-9x in the
common (ATR-floor) case (11 of 16 real tradable symbols exactly at the
floor, 13 of 16 including two more just past it), using the direct
path's strike-distance
convention as a benchmark "width" (not an endorsed fix) — same
risk-through direction as PRD-251's original bug, confirming (not just
plausibly matching) the class DECISIONS 2026-07-10 ruled warrants the
decouple by default. The gap narrows to near-zero at high ATR14 (crossover
at `atr14 = 10 x width`) and, past `atr14 = 20 x width`, the borrowed
width convention goes mathematically undefined (negative implied max
loss) — not reachable by any of today's 16 tradable symbols, but not
guarded against either; noted for whichever FIX approach R2 might choose.

Two out-of-scope findings surfaced and are explicitly NOT actioned here:

1. **`docs/PROJECT_STATE.md`'s "Active PRD" line was stale.** It read
   "none in progress" while `docs/PRD_REGISTRY.md` showed PRD-256 IN
   PROGRESS. PRD-253's closeout (PR #143) flagged this and declined to
   fix it on the premise that `docs/PROJECT_STATE.md` sits outside
   PRD-256's FILES — incorrect; PRD-256's own FILES section lists it.
   Corrected in this PR.
2. **The continuation path's HOLD-confirmation gate appears to never
   pass.** A full historical replay of the real, unmodified qualification
   function against ~4,000 real symbol-days (16 symbols x ~250 trading
   days, VIX-timing gate held favorable to isolate the question) produced
   zero accepted candidates, tracing to `NO_HOLD_CONFIRMATION`:
   `detect_continuation_breakout`'s lookback window already includes the
   candle the HOLD check re-examines, making the check nearly
   unsatisfiable — apparently inconsistent with
   `docs/trade_qualification.md:323`'s documented intent. This is
   consistent with the 95 captured production runs (2026-04-12..2026-07-10)
   — only 1 of which carries a non-null `continuation_audit` block, and
   that one itself shows 0 accepted — also carrying zero accepted
   continuation candidates ever. Unrelated to
   the ATR max-loss proxy this PRD characterizes; not fixed here; flagged
   for separate ticketing, not folded into PRD-256's scope.

R2 (Dustin's FIX-vs-PERMANENT ruling) has not fired. Full analysis:
`docs/prd_history/PRD-251.continuation-path.proposal.md`. Design record:
`docs/prd_history/PRD-256.md`.

---

## 2026-07-11 — rule-vs-practice gaps discovered mid-PR are legislated at a gate, not patched in the PR that found them

PR #141 (PRD-255's post-merge closeout) discovered, mid-PR, that
`PRD_REVIEW_TEMPLATE.md`'s newly-written absolute Review Independence
placement rule contradicted an existing, already-merged precedent
(`PRD-252.review.codex.md`). The implementer resolved the contradiction
unilaterally — loosening the rule rather than rewriting the artifact —
and, on this occasion, got the substantive call right (rewriting an
already-merged artifact to satisfy a later rule would fabricate
compliance, the same logic as the phantom-SHA disposition and the V9
historical-citation rule). Ruling: **the loosened rule stands** — but
the process was wrong independent of the outcome. A rule-vs-practice
conflict discovered mid-PR is a Gate-A-shaped decision, not a
patch-in-place: it gets surfaced and ruled on before the fix lands, not
resolved by the same agent that found the silence, even when the
agent's judgment turns out to be correct. Had the call gone the other
way, the same missing gate would have hidden it.

## 2026-07-11 — .claude/skills/ is NOT INFRA HIGH-RISK by default

A skill is governance-tier iff it gates a merge; today only
`prd-review-claude` qualifies (the Second-Model Disposition and DRIFT
CHECK it authors are load-bearing on HIGH-RISK closes). `prd-authoring-verified`,
`prd-closeout-verified`, and other skills advise an agent but do not
themselves block a merge — CI (`tools/validate_prd_registry.py`) and
the human Gate B merge do that. Rationale: hooks execute and can
permit or block a write or commit; skills advise an agent while a
human still merges — the INFRA CLASS Matrix row's HIGH-RISK FILES list
(CI workflows, `.claude/**` hooks/settings) does not extend to
`.claude/skills/` by default absent this gating property. This
resolves the ambiguity the Fable audit's `audits/FINDINGS.md` finding 6
(F-04/F-05) raised — `.claude/skills/` is absent from
`protect_files.sh`'s protected set — by recording that the absence is
correct for non-gating skills, not a gap; only a skill that gates a
merge needs the protection.

## 2026-07-11 — PRD-252 review calibration: mutation-style review and exhaustive out-of-diff sweeps catch different things

PRD-252's HIGH-RISK close used two independent review legs: the
fresh-context Claude review (`docs/prd_history/PRD-252.review.claude.md`),
which found the missing `options.py` branch test by mutation-style
reasoning (ask which test would fail if a branch were removed or
bypassed) scoped to PRD-252's own diff; and the commissioned Codex
second-model disposition (`docs/prd_history/PRD-252.review.codex.md`),
whose Sol/Luna orchestrator/retriever split ran an exhaustive
out-of-diff consumer sweep and surfaced a pre-existing
correlation-modifier passthrough gap in `contract.py`/`audit.py` — real,
but outside PRD-252's diff and predating it, so neither Gate A nor the
diff-scoped Claude review could have found it.

Both were needed: the mutation-style review is precise inside the diff
but stops at its boundary; the exhaustive sweep ranges wider but needs
an orchestrator forming hypotheses to avoid drowning in raw findings.
Neither framing alone would have found what the other did. See
`docs/prd_history/PRD-252.review.codex.md`'s CLASS OF REVIEW section
for Sol's own characterization of the two review styles.

**First live instance of the commissioned pattern on PRD-255 itself
(2026-07-11):** PRD-255 modifies `prd-review-claude`, the skill that
would normally structure its own Leg-1 review — so Leg 1 ran through
the pre-fix skill, whose V9 check forbade asserting implementation
pass/fail. Leg 1 found a PRD-document self-consistency error (the
CHANGE SURFACE section contradicting its own SCOPE/R7/R8) and graded
the REVIEWED-STATE/checkbox template collision RECOMMENDED. Leg 2
(commissioned, `gpt-5.6-sol` orchestrating `gpt-5.6-luna`'s retrieval,
run read-only against a git-free snapshot, blind to Leg 1's findings)
found three implementation bugs Leg 1 was structurally forbidden to
assert (a check-ID renumbering collision with 15 historical review
artifacts; a SHA-verification check that passes for non-commit
objects; a merge-base computation that could silently bind to the
wrong history) and graded the same template collision BLOCKER. Each
leg found exactly what the other's framing could not see — the same
lesson PRD-252 taught, now confirmed on a second, structurally
different case (a skill modifying itself, rather than a sizing-budget
change).

## 2026-07-10 — PRD-252: continuation path decoupled from the raised budget at both sizing sites

PRD-252 raises `config.MAX_RISK_PCT_PER_TRADE` (not `ACCOUNT_EQUITY` — a
factual account-size input, not the risk-tolerance dial) from 0.01 to
0.026667, raising the effective per-trade budget from $150 to ~$400.005
(BUILD_PLAN.md decision 4; a deliberate loosening, not a pure offset of
PRD-251's corrected arithmetic, which would land near $345).

Gate A asked whether the EXPANSION-regime continuation path should
inherit the raised budget or stay decoupled at $150. Its ATR-based debit
proxy (`qualification.py::_qualify_continuation_candidate`) was confirmed
— from `docs/prd_history/PRD-251.continuation-path.proposal.md`'s own
Stage-0-sweep language, not re-derived here — to carry the identical
max-loss-understatement PRD-251 fixed on the direct path. Ruling:
**DECOUPLE.** A new `config.CONTINUATION_MAX_RISK_PCT_PER_TRADE = 0.01`
constant holds the continuation path at $150 until its fast-follow
corrects the proxy.

Verification during Gate A caught that decoupling only at
`qualification.py:725` would have been incomplete: every
`QualificationResult` (continuation or direct) also passes through
`options.py::build_option_setups`'s correlation-modifier recompute
(`effective_risk`, line ~224), which read the raised main constant
unconditionally. The `min(result.max_contracts, raw_adjusted)` clamp
there masks the leak when the correlation `risk_modifier` stays near 1.0,
but at a low enough modifier `raw_adjusted` (computed off the wrong,
raised budget) can undercut the correctly-decoupled qualification-layer
value while still exceeding what a fully-consistent $150-based figure
would allow — a partial, silent re-couple. Fixed by branching
`effective_risk`'s constant on `result.entry_mode ==
ENTRY_MODE_CONTINUATION`, mirroring the existing PRD-251
`effective_max_loss` branch a few lines below it.

The continuation-path proposal doc now carries a tracked requirement:
its eventual fast-follow must VALIDATE continuation sizing at the raised
~$400 budget when retiring `CONTINUATION_MAX_RISK_PCT_PER_TRADE`, not
silently inherit the main constant as a side effect of deleting the
interim knob.

**Lesson:** a shared budget constant read at more than one call site
means "decouple it" is a claim about every read site, not just the one
that motivated the question. A single-site fix that "obviously" works
because of a downstream `min()` clamp can still leak under a parameter
combination (here: a low correlation modifier) that the common-case
review never exercises — worth an explicit multi-site grep before
declaring a decouple complete, the same discipline PRD-158's grep sweep
already applies to FILES declarations.

Full design record: `docs/prd_history/PRD-252.md`.

## 2026-07-10 — PRD-251 (A1a): Codex caught a real gap the fresh-context Claude review missed

The fresh-context Claude review (`docs/prd_history/PRD-251.review.claude.md`)
required narrowing `build_option_setups`'s `candidate is None` fallback so
continuation-path results never use a direct candidate's strategy-aware
`max_loss` — fixed in commit `c1553cb`. The `chatgpt-codex-connector` bot
review on PR #132 (submitted against the commit right after that fix
landed) found the fix was necessary but incomplete: EXPANSION regime runs
`generate_candidates()` alongside the continuation qualifier
(`direction_for_regime(EXPANSION) == "LONG"`, so it doesn't early-return),
meaning a direct `TradeCandidate` can exist in the `candidates` dict for a
symbol whose `QualificationResult` actually came from the continuation
path — `candidate is None` is false in that case, so `c1553cb`'s guard
didn't fire. Actioned in commit `83a193c`: gated on
`result.entry_mode != ENTRY_MODE_CONTINUATION` in addition to candidate
presence. Reproduced and mutation-verified (reverting the guard reproduces
the bot's reported $350-vs-$150 divergence exactly). Thread resolved
in-thread citing the fixing commit, per PRD-228.

**Lesson:** a single review pass — even a careful, independently-verified
fresh-context one — is not guaranteed to find every instance of a bug
class. The bot's review ran against a slightly later commit and looked at
the same code with a different lens (tracing what populates `candidates`
in EXPANSION regime specifically) and found the more common real-world
shape of the exact defect the Claude review had already partially fixed.
This is why PRD-228 treats bot threads as mandatory-to-triage input rather
than optional noise, even after a HIGH-RISK slice's primary review gate has
already passed.

## 2026-07-10 — PRD-251 (A1a): continuation path folded in at Gate A, then descoped after Stage 0 code evidence

Dustin's initial Gate A ruling for PRD-251 (credit-spread max-loss
arithmetic) folded the EXPANSION-regime continuation path
(`cuttingboard/qualification.py::_qualify_continuation_candidate`) into
the same slice, reasoning it was "the same conceptual defect, reached
through two doors." The Stage 0 sweep then read the actual code: the
continuation path's sizing proxy (`spread_width = max(0.50,
dm.atr14 * 0.05)`, added independently in PRD-008/commit `30b583a`) has
no strike-distance "width" term to subtract a credit from, unlike the
standard Gate 8 path's 30%-of-width convention. Applying PRD-251's
width-minus-credit correction there would require inventing a width
convention for an ATR-based continuation trade — a design decision, not
an arithmetic drop-in. Per `audits/EXECUTION_DOCTRINE.md`'s hard
constraint for this slice, the driver HALTed rather than build a snap
call; Dustin's revised ruling: descope the continuation path from
PRD-251, track it as a fast-follow
(`docs/prd_history/PRD-251.continuation-path.proposal.md`) needing its
own Gate A before build.

**Lesson:** a plan-level scope ruling ("same defect, two doors") can be
right about the symptom and wrong about the mechanism. Reading the
actual implementation — not the build-plan summary — surfaced that the
two code paths estimate the disputed quantity through structurally
unrelated formulas, which is exactly the kind of thing Stage 0's sweep
exists to catch before a HIGH-RISK slice locks in a snap design call.
The doctrine's HALT-on-materially-different-logic clause worked as
intended.

## 2026-07-10 — Execution doctrine adopted; audit deliverables landed (PR #130)

`audits/EXECUTION_DOCTRINE.md` is CANONICAL: the standing per-slice execution
process for ALL future work — one driver end-to-end with per-slice (not
per-stage) model tiering, lanes that skip stages outright (MICRO = CARD ->
BUILD -> VERIFY -> LAND, one operator touch), an inherited-by-reference
failure contract and commit discipline (thin per-slice charges), at most two
operator touches (Gate A direction / Gate B merge), and ten named redundancy
cuts. Reviewed by Dustin through three revision rounds (r1-r3), merged on his
explicit authorization. Subordinate to CLAUDE.md and `docs/PRD_PROCESS.md` by
its own terms; future changes to it ride MANUAL-MERGE-ONLY. Landed with it
(same PR): `audits/BUILD_PLAN.md` (the approved, decision-complete PRD
sequence for the reconciled findings — first application of the doctrine) and
the findings evidence trail (`audits/RECONCILED_FINDINGS.md`,
`CODEX_REVIEW.md`, `FABLE_REVIEW.md`, `FINDINGS.md`,
`CUTTINGBOARD_AUDIT_PLAN.md`). Noted-not-queued inside the doctrine: a
PRD_PROCESS "knob carve-out" (operator-decided config changes ride MICRO) —
deferred until recurring knob-friction justifies weakening R11/R12; revisit
with real instances. Superseded and pruned the same day: the
architecture-audit branch/worktree (deliverables identical on main) and PRs
#126/#128's missed same-PR closeouts (reconciled via #129).

## 2026-07-07 — A test may shell out to Node to exercise client-side JS (PRD-250)

`tests/test_staleness_banner.py` runs the exact emitted `_STALENESS_BANNER_JS`
in Node (a `subprocess` call against a stubbed `document`/`Date`) to assert the
fresh/old/closed boundary. This is the first JS-in-test in the tree, recorded so
it is not later deleted as an anomaly. Rationale: PRD-250's freshness verdict is
load-bearingly **client-side** (viewer-clock-relative, so a frozen board can't
freeze its own "fresh" label) — a Python-only suite can assert the server
contract (timestamp/threshold/session-flag emitted, verdict NOT baked) but
cannot exercise the actual age→verdict decision, which lives in the browser. Node
is the authoritative way to run it; CI's ubuntu image ships `node`, and the test
FAILS LOUDLY (never skips) if it is absent, per the hardening invariants. The
boundary is mutation-verified: inverted threshold, inactive-says-OLD, an injected
action-verb, and a server-baked verdict each flip the corresponding test red. Not
a general license for JS test infra — scoped to verifying client-side verdict
logic that has no server-side authoritative form.

## 2026-07-07 — Hourly-alert board froze ~23h with all workflows green; no code regression (MICRO incident)

**Symptom.** The published board (`dwats250.github.io/cuttingboard/`) read
`UPDATED 2026-07-06 09:14:23 PT` for ~23h while every workflow reported success.
Initial hypothesis (a `check_readiness.py` regression re-adding the retired
`RUN SNAPSHOT` marker) was **wrong**: PR #121 (`1376854`, merged `331f950`) is
present and effective on `main` — `origin/main:scripts/check_readiness.py`
requires only `id="system-state" / id="macro-tape" / id="candidate-board"`, the
guard test `tests/test_check_readiness.py` exists and is green, and the
`17:28Z` `--force-slot` run on the fixed commit passed `Check hourly readiness`
and published. The `RUN SNAPSHOT` seen was a **stale local working tree**, not
`origin/main`. No code regression existed; no code changed this pass.

**Actual cause — two stacked, both benign-looking.** The publish tail
(Aggregate → Render → Check-readiness → Commit → Push in `hourly_alert.yml`) is
gated on `steps.freshcheck.outputs.fresh == 'true'`; a skipped step still lets
the run report **success**. (1) The 07-06 10:00 PT slots (`17:08`/`17:19Z`, on
pre-#121 `ad662a3`) failed at the readiness gate — the one place the marker bug
was ever live; resolved by #121. (2) Every later scheduled run **suppressed**:
GitHub delivered the crons 8–46 min late (`15:43`, `17:34`, `19:42`, `21:21Z`…)
against `routine_pt_slot`'s `max_lag_minutes=25`, so each mapped to no slot →
`outside_routine_window` → `fresh=false` → publish skipped. The `--force-slot`
dispatch published but re-rendered from *restored* data, so its `UPDATED` stayed
at 09:14 PT. Net: no fresh-data hourly landed for ~23h, and because suppression
is green, nothing flagged it. **The board self-recovered 07-07 08:41 PT when the
Pipeline (`cuttingboard.yml`, not the hourly alert) refreshed data and pushed
`4e76a40`; Pages deployed it at `15:47Z`.**

**The durable danger.** On a quiet-Pipeline day the hourly alert can suppress
every slot and the board coasts on stale data with all workflows green — a
frozen read presenting as fresh, the worst failure class for a discretionary
sizing tool (a stale board can feed a real trade). Follow-up proposed:
`docs/prd_history/PRD-250.proposal.md` — a **client-side** staleness banner
(freshness judged at view time, not baked at render), explicitly *not* a wider
`max_lag_minutes`. Propose-only; no code this pass.

## 2026-07-07 — Definitions for the merge/review decisions below

Terms used in the merge/review decisions that follow:
- **auto-merge (mechanism):** GitHub's `gh pr merge --auto` / branch-protection
  auto-merge, which merges a PR automatically once required checks pass. A
  GitHub feature, not an actor.
- **agent-initiated merge:** an agent (Claude / Codex / Claude Code) taking the
  merge action itself, or queuing auto-merge on a PR, without a human performing
  or explicitly authorizing that merge.
- **human-held merge:** the merge action is performed or explicitly authorized
  by the human for that specific PR.
- **manual-merge-only lane:** a change class where auto-merge is disallowed and
  the merge must be human-held (per CLAUDE.md — currently HIGH-RISK and
  governance changes).
- **fresh-context Claude review:** a Claude review of a change derived from a
  clean context that has not read the implementation summary / PR body / prior
  disposition. Its durable form is `docs/prd_history/PRD-###.review.claude.md`.
- **second-model disposition:** the second-model leg required at every
  PRD-242-onward HIGH-RISK close, discharged by EITHER a committed non-Claude
  `PRD-###.review.<model>.md` artifact OR the written waiver sentence — never by
  the Claude review. A SEPARATE leg from the fresh-context Claude review; the
  `.review.claude.md` artifact does not satisfy it (PRD-242 R3).

## 2026-07-07 — Agents may open PRs on per-PR confirmation; agents do not initiate merges

Agents may open a pull request when the human gives explicit confirmation for
that specific PR (per-PR, not standing pre-authorization). Agents do not perform
agent-initiated merges: an agent never takes the merge action itself and never
queues auto-merge on a human's behalf. This does not disable GitHub's auto-merge
mechanism for ordinary work — auto-merge remains the normal landing path for
non-manual-merge-only lanes per CLAUDE.md ("How work lands": push the feature
branch, open the PR, queue `gh pr merge --auto`). What is prohibited is the
AGENT initiating or queuing the merge, not the mechanism existing. For
manual-merge-only lanes (HIGH-RISK, governance), the merge is human-held
regardless of mechanism. A PR opens with its review artifact and disposition
already present, so a PR is never openable-and-mergeable without its second leg
visible. **Rationale:** removes a mechanical step (PR-open) from the human
without moving the seam that protects `main` (the merge decision). The guarded
invariant is who INITIATES the merge, not whether the auto-merge feature is used
on ordinary work. An earlier draft of this entry over-broadly banned "auto-merge
under any circumstances," which contradicted CLAUDE.md's standing landing
policy; this wording scopes the ban to agent-initiated merge, its actual intent.

## 2026-07-07 — HIGH-RISK review artifacts land in-tree

The fresh-context Claude review for a HIGH-RISK change is committed to the repo
at `docs/prd_history/PRD-###.review.claude.md`. This artifact is the Claude
review leg; it is NOT the second-model disposition. Per PRD-242 the fresh-context
Claude review and the second-model disposition are separate legs, and the
`.review.claude.md` artifact does not satisfy the second-model requirement
(PRD-242 R3: "The Claude review never double-counts as the second model") — the
second-model leg is discharged by EITHER a committed non-Claude review artifact
OR the written waiver sentence, never by the Claude review. The artifact carries:
the reviewed SHA (the commit its evidence was actually gathered at — never
backdated to a later head), the merge base, a fresh-context attestation, the full
findings with real command output, the disposition, and any advisory closure. If
later commits supersede the reviewed SHA, the artifact re-verifies the delta in a
marked follow-up rather than restating the header to a commit it did not review.
**Rationale:** the repo is canonical over any external surface; a HIGH-RISK
gate's Claude leg must be durable in the source of truth with honest per-commit
provenance. Naming it the "second-model review" (an earlier draft's error)
conflates two separate legs — the Claude review and the second-model disposition
are distinct, and neither substitutes for the other.

## 2026-07-07 — Concurrent-session authority on a shared PR

When more than one agent session acts on the same PR, the session that performed
the merge is authoritative on merge state. A session woken by a webhook/GitHub
event without the context of the merge must verify against the tree (`git log` /
file presence on `main`) before asserting the PR's state — it must not report
"not merged" or "artifact missing" from its own blind context. **Rationale:**
adopted after a single observed incident (PRD-249 / PR #126) where a
webhook-woken session, lacking its sibling's context, confidently reported the
review artifact as never-committed while it was in fact on `main` at `a448536`.
Recorded as a standing rule because the failure mode (a contextless session
narrating a gap it can't see, in a confident voice) generalizes to any
multi-session PR, and repo-canonical-over-recollection already applies to
Claude's recollection — this extends it to an agent session's recollection.
Flagged as prompted by one incident; revisit if multi-session PR work proves
rare enough that the rule is dead weight.

## 2026-07-06 — PRD-248: `.proposal.md` allowlisted in the registry-gap hook

Closed the INFRA item PRD-247's DECISIONS entry named. `prd_eval.sh`'s
registry-gap allowlist gained a `.proposal.md` clause (alongside
review/adjudication/codex-prompt/impl-notes), so `PRD-NNN.proposal.md` — the
artifact class the #119 governance refactor introduced — is treated as the
non-PRD sidecar it is and no longer trips the UserPromptSubmit warning
(`PRD-244.proposal.md` was the live offender). Guard fails-closed: a genuine
unregistered `PRD-NNN.md` is still flagged, mutation-verified (reverting the
clause reddens the R1 proposal test; the real-PRD-gap test stays green) — run
by the implementer and independently re-run by the fresh-context reviewer.
HIGH-RISK/INFRA (protected hook), not governance-manual-merge-only (the
registry-gap hook is not an enumerated governance guardrail): fresh-context
Claude review ACCEPT (`PRD-248.review.claude.md` @ `518e858`) + second-model
waiver (no codex host) + Dustin's manual merge (PR #125). **Process root
cause:** the number-reservation/registry discipline had no place for a
proposal artifact class; the hook allowlist is the durable fix so the class
doesn't regenerate the warning.

## 2026-07-06 — PRD-247: qualification doc-truth pass (broad 11-gate spec-vs-code audit)

Closed the last thread of the qualification investigation with a broad
spec-vs-code pass over `qualification.py` (all 11 DIRECT gates, the
continuation path, the FVG/PULLBACK path), verified twice — the Fable
diagnosis plus an independent Explore cross-check that recomputed the worked
examples A/B/C. **The code is correct everywhere.** Five doc-truth
divergences reconciled (PRD-247, docs-only): Gate 8 failure message +
pseudocode still showed the retired `$200 maximum` / hardcoded-150 budget
(pre-PRD-157 equity-driven sizing); `system_logic_map.md` regime list omitted
EXPANSION; the continuation EMA21-None fail-open was undocumented; the
"NEUTRAL=0.6 halves it" verb was wrong (0.6 = 40% cut); and PRD-007 R1's
`FVGZone` field list (`high/low/midpoint/direction`) was superseded at
implementation by the live `upper_bound/lower_bound` shape (midpoint derived,
direction a `detect_fvg` param). PRD-007 is COMPLETE, so that last one is
historical spec drift recorded here, not an open requirement.

**Two deferred, on record:**
- **Cosmetic:** `qualification.py:13` (module docstring) and `:325` (Gate 1
  comment) say "CHAOTIC posture" — a category error (CHAOTIC is a regime;
  `regime.py:310` forces its STAY_FLAT posture, so behavior is correct). A
  comment-only tightening → next cosmetic batch (PRD-229), not a canonical-doc
  change.
- **Observability (candidate EXECUTION PRD):** the continuation extension
  fail-open emits no `gates_skipped` marker, unlike the DIRECT path's PRD-235
  markers — invisible at runtime, not just in the doc. Closing it is an
  additive code change (continuation-path skip-marker parity); needs its own
  PRD, not folded into doc-truth.

**Inherited registry-gap (separate owner):** `docs/prd_history/PRD-244.proposal.md`
(the governance refactor's artifact, merged via #119) trips the registry-gap
hook because `.proposal.md` isn't in `prd_eval.sh`'s allowlist (which covers
`.review.`/`.adjudication.`/`.codex_prompt.`). The correct fix is adding the
`.proposal.md` suffix to the hook allowlist — a protected-hook (INFRA) edit,
its own small PRD, not this docs pass.

## 2026-07-06 — PRD-244 number collision: FVG floor PRD renumbered to PRD-245 (reconciliation)

Two sessions raced the number: this branch filed the FVG floor decision-PRD
as PRD-244 (Stage 0 at `04a09df`), while a parallel session's CLAUDE.md
governance refactor claimed PRD-244 at its own branch-side Stage 0 and
reached main first (PR #119, `1e38b18`, merged by Dustin). The filing-time
number-availability check ran against main (registry, `prd_history/`,
`next_prd`) — an open PR's branch-side claim was invisible to it.
Resolution (Dustin ruled): the governance PRD keeps 244 (merged history is
immutable); the FVG PRD is renumbered **245** everywhere on this branch
(doc + review-artifact filenames, registry/index rows, code/test/doc
references); the queued denominator-test fast-follow becomes **PRD-246**.
Branch commit messages saying "PRD-244" (`04a09df`/`8f7ecce`/`6017ce9`/
`b30e137`/`102ea24`) are immutable and denote the FVG PRD-245. The review
artifact body is preserved verbatim under a renumber note — its "PRD-244"
citations were true at its pinned SHA (`b30e137`).
**Process rule surfaced: number reservation must check open PRs, not just
main** — `next_prd` and the registry are both blind to a branch-side
Stage 0 in flight.

## 2026-07-06 — PRD-245 (filed as PRD-244) RULED Branch A and closed: Gate 6 floors re-fire on the FVG swapped stop, fallback-to-DIRECT

R1 ruled by Dustin (hole, not deliberate): the sub-floor swapped stop is
silent, thesis-violating, and trust-eroding; a missed tight setup is
visible and independently recoverable. Semantics: **fallback, not reject,
not clamp** — a post-swap stop violating either Gate 6 leg returns the
already-qualified DIRECT result (Step-2 sub-ruling: no zone retained —
bare return, bit-identical to native DIRECT — a retained zone would be a
reader-less channel). Floor check precedes the R:R re-check because R:R
is a ratio a tighter stop improves. Percent leg divides by the zone
midpoint (the post-swap entry), closing the wrong-denominator trap in the
same stroke. Implementation `8f7ecce`, tests `6017ce9` (PRD-240 R4's red
test re-tuned to floor-clearing geometry with its tier discrimination
preserved at RR 1.80 exact; both mutation checks re-verified red), docs +
closeout in the closing commit. Second-model leg: waiver sentence per the
PRD-240 precedent (no codex host in the container), written on Dustin's
Step-5 directive. Branch held for Dustin's manual merge; no PR opened.

## 2026-07-06 — Fable qualification investigation: two audit candidates resolved without PRDs, one new finding promoted to PRD-245 (PROPOSED; filed as PRD-244 pre-collision)

Verification pass over `qualification.py` at `331f950`, citation-integrity
protocol (every claim from a same-session read). Three outcomes:

1. **"FVG pullback missing its EXPANSION R:R branch" — refuted as stale.**
   The prior recon described pre-PRD-240 code; PRD-240 R4 added the branch
   via the shared `_min_rr_for_regime()` and R1 removed the 1.5 discount it
   would have reached. No PRD.
2. **"Continuation stop lacks Gate 6's ATR floor" — confirmed as behavior,
   deliberate by record.** PRD-240 R6 documents the asymmetry in three
   places; the in-code comment's arithmetic verifies against current config.
   No PRD.
3. **New finding, promoted to PRD-245 (PROPOSED, decision-PRD):** the FVG
   PULLBACK_IMBALANCE upgrade swaps the traded stop to the zone bound and
   re-checks only R:R — a ratio a tighter stop *improves* — so Gate 6's two
   stop-distance floors are never revalidated on the stop that trades
   (post-swap risk floors at 0.15×ATR14 vs the 1.0×ATR14 the DIRECT pass
   enforced; path verified live via `runtime/__init__.py:415-423`). The
   escape is specified nowhere (trade_qualification.md, PRD-007/240/241,
   the audit, in-code — all silent). Hole-vs-deliberate held for Dustin's
   R1 ruling; artifact: `docs/prd_history/PRD-245.md`.

**Supersede stamp:** the 2026-07-05 qualification-tuning audit's
`_resolve_entry_mode` finding (findings.md:280-297) is superseded — its R:R
half by PRD-240 R4, its stop half by PRD-245. Do not resurface it from the
audit artifact.

## 2026-07-06 — PRD-244: CLAUDE.md governance refactor closed (compress-in-place)

CLAUDE.md rebuilt as a lean steering document (2,968 → 2,112 words):
compress-in-place with reference-out — every candidate relocation was
verified already canonical at its destination, so every cut is
de-duplication or narration, never a move (full move-list:
`docs/prd_history/PRD-244.proposal.md`). Fresh-context governance review
(`docs/prd_history/PRD-244.review.claude.md`, SHA-pinned `724991e`)
independently re-derived the load-bearing rule set: 67/67 rules survive,
zero weakened or lost; ACCEPT WITH CHANGES. Its two required fixes landed
in the PRD: Stage-0 filing (this PRD-244), and repair of the four live
inbound citations the section renames had dangled (CODEX.md,
PRD_PROCESS.md, architecture.md, prd-review-claude skill) — CLAUDE.md
itself frozen byte-identical to the reviewed commit. Second-model
instrument not commissioned (waiver sentence in the PRD doc).
Manual-merge-only per the governance carve-out (PR #119, held for
Dustin's merge). Generalizable rule:
**inbound cross-references to CLAUDE.md should cite by rule/topic, not
section header — anchors break on restructure (surfaced by PRD-244).**

## 2026-07-06 — PRD-228 Codex-review branches superseded, not contradicting (branch-cleanup, cont'd)

Two never-merged branches held sole copies of Codex cross-reviews from
PRD-228's own development: `codex-review/PRD-228-00bd1bfbce7b` (review @
`00bd1bf`, REQUEST CHANGES — flagged that the draft clause read as if every
HIGH-RISK PRD requires durable Codex review, broadening the gate) and
`codex-review/PRD-228-225e93bbc7cf` (review @ `225e93b`, later commit,
APPROVE WITH EDITS — confirmed the reworded "any durable Codex cross-review
that PRD's lane/CLASS actually requires" wording fixed the broadening risk).
Checked whether these contradict the current in-tree `CLAUDE.md` bot-thread-
disposition sub-point 3: they don't. Per PR #96's own commit history,
`00bd1bf`'s blocking finding was actioned mid-development, producing exactly
the wording `225e93b` approved; that wording landed at merge (`a11481b`,
2026-07-03). **PRD-242** (`197815e`, 2026-07-05) then deliberately rewrote
that same sub-point again — "any durable Codex cross-review that PRD's
lane/CLASS actually requires" → "the second-model disposition
(artifact-or-sentence, PRD-242)" — as part of retiring the mandatory-Codex
framing repo-wide, already recorded at "2026-07-05 — PRD-242: second-model
review becomes a commissioned instrument" ("The PRD-228 bot-thread
disposition net is untouched" — the triage mechanics were untouched; only
this cross-reference's terminology was updated). **Superseded because:** the
reviews assessed intermediate wording that no longer exists verbatim, having
already been superseded twice (PRD-228's own merge, then PRD-242) — not an
unresolved conflict. Both branches are deletable.

## 2026-07-06 — PRD-228 CODEX-LEG WAIVER backfilled into DECISIONS (closeout gap)

`docs/prd_history/PRD-228.md` (status COMPLETE) carries a `CODEX-LEG WAIVER
(Dustin, 2026-07-03)` note stating the CLAUDE.md Codex cross-review PRD-228
would trigger was waived — Codex API token budget exhausted, so no genuine
`PRD-228.review.codex.md` could be produced — and that the waiver is an
explicit, recorded exception (not a gate-satisfying substitute; Lane
Independence was separately met by a fresh-context, different-model Fable
review). The PRD doc states a `docs/DECISIONS.md` entry recording this waiver
is due at closeout; none was ever written. Backfilling it now, found during
the same branch-cleanup sweep as the two entries above/below: the Codex leg
for PRD-228 is WAIVED (2026-07-03, Dustin, token-budget exhaustion),
Lane Independence satisfied instead by the Fable review, per
`docs/prd_history/PRD-228.md` CODEX-LEG WAIVER note.

## 2026-07-06 — PRD-212 Codex-review artifact backfilled in-tree (branch-cleanup, cont'd)

Second sole-copy artifact found stranded on a never-merged branch during the
same remote-branch cleanup sweep as the entry below.
`docs/prd_history/PRD-212.review.codex.md` (the gpt-5.5 gate-validation Codex
cross-review, reviewed commit `dd843fe`) existed only on
`codex-review/PRD-212-dd843fe90bc3` @ `b55ec1b`; `docs/PROJECT_STATE.md`
cited it BY BRANCH NAME ("artifact landed on
`codex-review/PRD-212-dd843fe90bc3`") rather than by an in-tree path. Pulled
the artifact in-tree verbatim from the branch; repointed the PROJECT_STATE
citation to the committed path. `rg --hidden` confirms zero remaining
references to the branch name anywhere in-tree — the branch is deletable.

**P6 courtesy note (2026-07-06):** this entry's own prose above contains the
literal string `codex-review/PRD-212-dd843fe90bc3` twice — a later `rg
--hidden` sweep for that branch name will hit these two lines. That's
intentional: this is historical narration of a completed backfill, not a
live citation the branch needs to exist for. A future drift/alignment check
that finds this string here should NOT repoint or reword it — leave it
verbatim.

## 2026-07-06 — Branch-cleanup backfills: qualification-tuning audit artifact in-tree + alignment check #6 record

Post-#115 remote-branch cleanup surfaced two sole-copy artifacts stranded on
never-merged branches. (1) `audits/qualification-tuning-2026-07-05/findings.md`
— the ten-finding audit that drove PRD-240/241, already cited at that exact
path by this log and both PRD docs — is now committed in-tree from
`claude/qualification-system-audit-sp0wat` @ `d507130`, so the citations
resolve; the branch is deletable. (2) Alignment check #6 (2026-07-01, `main` @
`c38edf7`, post PR #74/#75) ran as a read-only audit-and-scope pass but its
DECISIONS line was never written (the record was left to a bookkeeping seam
that never executed — this is that line, backfilled). Result: **PASS on all
three cadence questions** (no new prediction logic, no undocumented sidecar,
no off-VISION module; window = PRD-212 + bookkeeping). 13 findings scoped,
none executed: mostly doc-truth staleness and process misses since absorbed or
mooted by the 2026-07-03 codebase review and the Fable window (PRD-230 retired
the codex-review workflow F-2/F-3 described and the cadence itself; PRD-231/232
fixed the doc-truth class; PRD-243 closed the F-13 hash-debt thread). The
artifact (`alignment-check-6.md`, branch `claude/audit-alignment-check-6-6rhltr`)
is working scratch per the PRD-230 sediment rule — superseded, deletable with
its branch; this entry is the durable record.

## 2026-07-05 — PRD-243: subtraction block — prd_eval detectors retired, GitNexus surface deleted, phantom-SHA debt WONTFIX

Lifecycle-audit Step 4 (prescriptions P3/P4/P7), all cuts grep-proven clear
before removal and the two execution-path targets behavior-proven after.
(1) `prd_eval.sh` keyword detectors retired: no channel discrimination, six
misfires on subagent notifications in one audited session; the 108→143→145
exclusion-repair chain was this false-positive class regenerating; the
registry-gap check is the hook's one remaining job, and sequencing truth
lives at the CI validator (PRD-200) + same-PR closeout (PRD-229).
(2) GitNexus deleted wholesale — 12 single-commit never-regenerated skills
with measurably stale indexes pointing at a tool installed nowhere, four of
them trigger-matching ordinary requests; `knowledge_systems.md` now carries
the retirement record. (3) Phantom-SHA debt closed WONTFIX-HISTORICAL at
its true size (29 PRDs / 35 tokens, validator-pinned; the recorded "19" had
silently grown): the #NNN convention killed the class, and rewriting
pre-convention rows would fabricate history against a rule not in force —
the same floor logic as PRD-242's >=242 cutoff. Nothing added anywhere in
this pass (audit P7 do-nothing list honored).

---

## 2026-07-05 — PRD-242: second-model review becomes a commissioned instrument (closes the 197→230 Codex arc)

The lifecycle audit (`audits/prd-lifecycle-audit-2026-07-05/`, PR #114) found
the mandatory Codex cross-review gate had been fiction since PRD-230: the CI
leg was deleted, no codex-capable host exists in the operating loop, all 8
HIGH-RISK closes since ran on waiver-by-merge, and PRD-240 merged while its
own review artifact said the second leg was still owed — a silent gate-skip.
Dustin confirmed Option A after the connector-bot post-merge net was verified
empirically live (substantive ACTIONED P2 threads on #99/#102, an open P2 on
#108; the earlier "out of credits" note was wrong — corrected in the Step 5
sync batch). Decision: the HIGH-RISK second leg is the fresh-context Claude
review + Dustin's manual merge; second-model review is an instrument Dustin
may commission, never a requirement owed; every HIGH-RISK close ≥ 242 records
its disposition explicitly (artifact or the verbatim SECOND-MODEL sentence),
enforced by the registry validator at CI. The waiver is a positive act, never
a silence. The PRD-228 bot-thread disposition net is untouched. This closes
the PRD-197→207→212→230 arc: five PRDs, ~8 PRs, 699 peak LOC, one real catch,
ending as one sentence the merger has to write.

---

## 2026-07-05 — Two testing rules from the PRD-240 implementation arc

Both surfaced during PRD-240 (merged PR #111); recorded as standing rules,
not dated observations:

1. **Threshold-tightening PRDs run the full suite at FILES-scoping time.**
   The token grep sweep (CLAUDE.md pre-implementation sweep) catches name
   references only; PRD-240's sweep covered every constant token and still
   missed `tests/test_account_equity_sizing.py`, whose fixture *geometry*
   (stop=99 vs. the new 1.0×ATR floor) failed the tightened gate before
   reaching its assertions — forcing a mid-implementation FILES amendment.
   When a PRD tightens a numeric gate, run the full suite against a
   prototype of the new value while declaring FILES, and add every failing
   test file up front.

2. **Clear `__pycache__` before trusting a post-mutation-check run.** An
   in-place sed revert+restore that lands same-size/same-second can leave
   stale bytecode, producing a phantom pass/fail against the OLD constant.
   The PRD-240 fresh-context reviewer hit exactly this (one spurious
   full-suite failure; disclosed in `PRD-240.review.claude.md`). After any
   source-mutation verification, invalidate caches (`find . -name __pycache__
   -exec rm -rf {} +` or `PYTHONDONTWRITEBYTECODE=1`) before reading the
   next result as truth.

---

## 2026-07-05 — Qualification tuning audit dispositioned: PRD-240/241 drafted PROPOSED, six findings left as-is

The read-only trade-qualification tuning audit
(`audits/qualification-tuning-2026-07-05/findings.md`, branch
`claude/qualification-system-audit-sp0wat` @ d507130) is dispositioned:

- **Acted on → PRD-240 (PROPOSED, HIGH-RISK/EXECUTION, held for Dustin):**
  EXPANSION R:R discount removal (1.5→2.0; the audit's one
  literature-confluent directional finding), Gate-6 ATR stop floor 0.5→1.0×
  (below every convention found), plus wiring honesty — shared `MIN_STOP_PCT`,
  named continuation reward constant (the formula is a constant 3.0×ATR14 in
  disguise), regime-tiered R:R in `_resolve_entry_mode` (missing EXPANSION
  branch), continuation momentum close-location conviction.
- **Explicit calls on the audit's three "human decision" flags:** FVG R:R
  branch → fix via shared tier helper (behavior-neutral at 2.0); synthetic
  reward → rename honestly, redesign declined; continuation stop-floor
  asymmetry → retained and documented, because a 1.0×ATR floor there would
  meet the post-R1 R:R ceiling (risk ≤ 1.5×ATR14) in a 0.5×ATR-wide
  qualifying band — a de facto continuation shutdown nobody has decided on
  (interaction the audit did not surface; found while drafting).
- **Not adopted:** the audit's NEUTRAL-vs-EXPANSION R:R "reversal" framing —
  NEUTRAL trades here are directional setups in a low-information regime, not
  a mean-reversion strategy; NEUTRAL 3.0 and default 2.0 stand.
- **Left as-is (audit-concurring):** `MIN_REGIME_CONFIDENCE` (only NEUTRAL
  binds on it in production; splitting would duplicate `regime.py` posture
  tiers), extension multipliers, continuation K-values, NEUTRAL ±1 tiebreak.
  Flagged-not-actioned: min-votes confidence guard (degraded-data edge),
  WATCHLIST `gates_skipped` render gap (PRD-235 RECOMMENDED-1, stays deferred).
- **Doc drift → PRD-241 (PROPOSED, MICRO, sequenced after the 240 decision):**
  `system_logic_map.md` "9–11 gates" + `trade_qualification.md` missing two of
  three entry modes and the regime R:R tiers.

SSRN citations are search-snippet confidence only (SSRN full text
bot-blocked) — verify before leaning further on them.

---

## 2026-07-05 — Fable window closed: Blocks 3–4 complete; post-window queue fixed

The 2026-07-04→07-07 Fable window closed early with all four blocks done.
Landed since the Block-3 gate: item I (PRD-236 @ #104), J1 (PRD-237 @ #105,
Dustin's line-by-line schema read), J2 + M-map design (PRD-238 @ #106,
`docs/renderer_decomposition_map.md`), ledger tick reconciliation (#107),
and item G (PRD-239 @ #108, `docs/architecture.md` rewritten against the
real `_run_pipeline`). Every HIGH-RISK PRD carried a fresh-context Claude
review artifact; the Codex leg ran on the window's artifact-or-waiver
pattern (Dustin's merges record the waivers — no `codex` CLI in the
remote container, connector bot out of credits).

`FABLE_WINDOW_PLAN.md` deleted per its own instruction; the
`docs/session_resume/2026-07-04-fable-window.md` scratch note deleted per
the PRD-230 sediment rule after confirming durable homes for its contents.

**Post-window queue (Opus, after July 7)** — the master plan's open boxes
plus review-surfaced follow-ups, consolidated here so nothing lives only
in scratch: master-plan D (single-source constants), E (lockfile +
SHA-pinning), F (confirmation/ingestion test blind spots), K (injected
fetch provider), L (notification dedup state injection), M execution per
`docs/renderer_decomposition_map.md` (re-verify its line numbers first);
hourly-path finalize-validation + retire the `_validated_chain_result`
sibling fail-open (enumerated in PRD-234 OUT OF SCOPE); qualification
missing-candidate fall-through (PRD-235 doc); output.py always-None dead
reads (PRD-237 OUT OF SCOPE); `reports/levels.py::derive_key_levels`
typing MICRO (PRD-238 review); optional mypy gate (PRD-237 follow-up).

**Operational note worth keeping:** the byte-identical fixture harness
must warm TWICE after restoring committed `logs/` (first run trips the
staleness guard against the committed fallback); artifacts are
deterministic only at steady state. Always `git checkout -- logs/
reports/` before commits.

## 2026-07-05 — Alignment check #5 (phase boundary: Fable-window close) — PASS, no drift

Phase-boundary diff-read per CLAUDE.md (the PRD-230 model — first run
under it). Covered `main` merges since check #4 (2026-06-20): PRDs
191–193, 204, 207–208, 210–212, 223–225, and the window's 228–239
(PRs #96–#108). Q1 new prediction logic: none (validation, typing,
docs, process, presentation only). Q2 new sidecar without a documented
consumer: none (`renderer_decomposition_map.md` is a design doc;
PRD-223/224's risk band consumes existing contract fields). Q3 new
module serving none of VISION's four questions: none
(`contract_types.py` types the existing contract). Q4 post-merge drift:
none found — every window review artifact carries its DRIFT CHECK;
PROJECT_STATE refreshed at each same-PR closeout. Findings: none.
Next check: next phase boundary (likely the post-window Opus wave
closing D/E or K/L/M).

## 2026-07-04 — Fable-window Blocks 1+2 merged; Block-3 gate opened (Deviation 2 signed)

Dustin hand-merged PR #99 (Block-1 governance batch, = Deviation-1 sign-off)
and PR #102, which carried the whole Block-2 stack — PRD-233 (validator live
in _run_pipeline, pre-notification), PRD-234 (CHAIN UNVERIFIED fail-open
kill), PRD-235 (qualification loudness) — to `main` in one squash
(`c31bff6`); the authoring PRs #100/#101 were closed as contained and the
registry provenance trued up to #102 (PR #103). He then signed Deviation 2
in-session ("Signed — open Block 3"), so the Wave-3/Block-3 gate is PASSED:
the module-reads clause moves whole to the post-window learning stint,
replaced in-window by byte-identical fixture checks + his line-by-line J1
schema-diff read. First structural cut (PRD-236, master-plan item I)
follows. The connector bot's six in-window catches are dispositioned
in-thread on their PRs.

## 2026-07-04 — Fable-window Block 1: ceremony tiering + process drop-list (PRD-229..232, batch PR #99, manual-merge)

**What changed (mentor-review "What I Should Drop" + leverage item #1,
executed per `audits/codebase-review-2026-07-03/FABLE_WINDOW_PLAN.md`):**
PRD-229 — Cosmetic Carve-Out (cosmetic-only diffs exempt from the R11 lane
floor, ≤10-line MICRO note, ≤1 weekly polish PRD; R12 unchanged) + Same-PR
Closeout (COMPLETE cells record the PR number `#NNN`; validator accepts it;
separate closeout commits retired). PRD-230 — Codex-authenticity apparatus
deleted (codex-review.yml + its 19 tests; plain read-only `codex exec`
review and artifact conventions kept); alignment cadence → phase-boundary
15-min diff-read with the PRD-186 post-merge audit folded in; CALL_SITE_MAP
de-line-numbered; process docs deduped to one owner per domain. PRD-231 —
first carve-out MICRO (gate-count 9→11 ×3 sites, dead runtime.py ref).
PRD-232 — skills/scaffold aligned to the new rules (closeout skill same-PR
mode; authoring skill carve-out; prd_open.sh emits the canonical template).

**Why.** Process output was ~3× product output; 12 cosmetic PRDs paid full
HIGH-RISK freight in two days while a dead validator and a duplicated risk
constant sat unnoticed. The authenticity apparatus (5 PRDs / 344-line
workflow / 16 artifacts) had negative marginal return for a solo repo where
Dustin performs every merge.

**Deviations recorded.** The drop-list's audits-purge premise was falsified
by recon (inbound refs everywhere except one file — only that file deleted;
Dustin dispositions the rest at the batch review). Fable-window Deviation 1
(H drafted by Fable, hand-merged by Dustin) is recorded in the MASTER_PLAN
Parking Lot; Deviation 2 stays unsigned until the Block-3 gate.

**Artifacts.** Reviews: `docs/prd_history/PRD-229.review.claude.md`,
`PRD-230.review.claude.md`, `PRD-232.review.claude.md` (all fresh-context,
ACCEPT WITH CHANGES, all REQUIRED edits remediated in-batch). Registry
reconciliation that unblocked the numbering: PR #98 (`c4927d5`).

---

## 2026-07-02 — PRD-223 SHIPPED: the risk band landed renderer-only; the deferral's premise was already met

**What landed.** PRD-223 (merged via PR #89, `e654ca0`): the level ladder shades
the contract entry→stop span as a soft risk zone (`#e05252`, `opacity 0.08`)
with a dashed `STOP <price> <±%>` edge. Descriptive only — no targets, no R:R
(`target`/`risk_reward` documented in SCHEMA_MAP as deliberately not rendered).

**The scope pivot (supersedes the deferral below).** Dustin commissioned the
band as an engine-contract change (emit numeric entry/stop next to the setup
card's prose). Recon falsified that prescription on two facts:
1. `trade_candidates[].stop` ALREADY existed — `TradeDecision.stop`,
   sizing-grade, finite-asserted for ALLOW_TRADE (`contract.py`), in the same
   artifact whose `entry` the diagram's anchor already read. The deferral's
   reopen condition ("engine needs a numeric stop for an independent reason")
   was met all along; the deferral's author reasoned from the market_map card
   and missed the contract overlay.
2. The prescribed market_map numeric emission is degenerate: `_trade_framing`
   entry prose and `_invalidation` prose both reference `watch_zones[0]`, so
   numeric companions are equal on every directional card — a zero-height band
   (the PRD-222 "always-empty band" channel again). Excluded on realizability;
   reopen only if the engine ever distinguishes the two referent zones.
So the band shipped as the "near-free renderer addition" the deferral
predicted: renderer-only, CLASS CONSUMER, LANE HIGH-RISK, no contract change,
no prose parsing.

**Gate.** Claude fresh-context review ACCEPT + genuine Codex cross-review
(gpt-5.5 honored, read-only, SHA-pinned @ `5b5dd70`) REQUEST CHANGES — both
REQUIRED edits were PROJECT_STATE currency drift, remediated pre-merge
(docs-only; production code stayed byte-identical to the pinned SHA). Reviewer
disagreement on whether stale canonical docs block merge was dispositioned in
Codex's favor. Artifacts: `docs/prd_history/PRD-223.review.claude.md`,
`docs/prd_history/PRD-223.review.codex.md`.

**Recorded follow-ups (PRD-224 fast-follow + noted debt).** (a) macro-tape
glyph alignment: pad GC/SI to 3 chars with `&nbsp;` at the two dashboard tape
emission sites (HTML collapses plain spaces; the notification path already pads
via `:<3`) — Dustin-requested; (b) entry-path guard symmetry in
`_load_contract_entry_context` (bool/non-finite entry bare-coerces; unreachable
from real contracts but asymmetric with the stop path); (c) misleading
staleness comment in `tests/test_dashboard_renderer.py` ("nulls the stop map"
— the mechanism is the pair gate). Sub-$2 y-scale degenerate-span edge: noted
only, out of the traded universe.

## 2026-07-02 — Deferred: numeric entry/stop risk band on the level ladder (future PRD-223+)

> **SUPERSEDED same day — see the PRD-223 SHIPPED entry above.** The reopen
> condition was discovered to have been already met (`trade_candidates[].stop`);
> the band landed renderer-only with no contract change and no prose parsing.
> The banned-shortcut and zone-not-hairline guidance below was honored.

**The idea (approved in principle by Dustin).** Add a shaded *risk band* to the
level diagram (`_render_level_diagram`, `cuttingboard/delivery/dashboard_renderer.py`)
between the entry price and the stop/invalidation price, so a trader reads
*how much room there is before the thesis is wrong* as a to-scale shape rather
than decoding prose. Descriptive, not predictive — band = entry→stop only; no
profit targets or R:R ratios (those cross VISION's description-not-prediction line).

**Why it is NOT a UI change, and is deferred.** The card's `entry` and
`invalidation` fields are **prose**, not numbers (e.g. `"reclaims ORB_LOW with
follow-through"`). There is no numeric stop to draw to. The band is gated on the
setup engine **emitting a numeric stop/invalidation price** (ideally a numeric
entry too) into the payload alongside the existing prose — a payload *contract*
change, i.e. a real HIGH-RISK-lane PRD (decision-surface contract + CONSUMER
renderer), not a micro.

**Banned shortcut (recorded so a future session doesn't take it).** Do NOT
regex-parse the prose to recover a level name and look it up in `watch_zones`.
That is the "authoritative source, not proxy" / "assert the resolved, not the
requested" failure class (CLAUDE.md Semantic-failure hardening §2–3): it works
until the phrasing shifts one word, then silently draws the band to the wrong
level. The correct source is a numeric field the engine emits, not narrative
parsed downstream.

**Second-order caution.** Prose invalidation is deliberately soft ("with
follow-through"); a crisp numeric line invites over-trusting a level the engine
meant as a zone. Prefer rendering the stop as a band/zone, not a hairline.

**Recommendation.** Hold until the engine needs a numeric stop for an
independent reason (position sizing, backtest scoring); then the band is a
near-free renderer addition. Building it now means either the banned prose-parse
or opening the engine contract for a purely visual payoff — hard to justify
against "cuts before additions." The SVG geometry in `_render_level_diagram`
(SVG_H=110, LINE_W=160, the yellow anchor line + its y) is a pinned test
contract; extend, don't disturb.

## 2026-07-02 — PRD-208 COMPLETE: presentation revive lands once the Codex gate is genuinely working

**What landed.** PRD-208 (trend-structure SMA alignment presentation) revived onto
current main and closed. The SMA composite cell now renders a compressed 3-state
arrow vocabulary (↑/↓/= vs SMA50 and SMA200) under the pinned "SMA 50/200" header;
the redundant granular "vs SMA50"/"vs SMA200" columns are cut (trend table 10→8
columns); unavailable states keep "Structure unavailable"/"SMA history insufficient"
and are guarded against ever rendering "NULL"/"None"/prose. Pure presentation change
in `dashboard_renderer.py` (CLASS CONSUMER; no data/schema/gate/count/regime touched).
Impl `0f72e32`; +2 net tests.

**Why it was parked, and what unblocked it.** PRD-208's only blocker was its
HIGH-RISK Codex cross-review leg. The stage-0 artifact (branch
`claude/prd-208-stage-0` @ `ceceedb`) was INVALID: its provenance claimed
`resolved-model=gpt-5-codex` while the body self-reported `Model: gpt-4.1` — the exact
hollow-gate substitution PRD-207 was built to fail-close on, and (per 2026-07-01) the
consequence of `gpt-5-codex` being retired 2026-04-01. The gate only became usable once
PR #76 retargeted it to `gpt-5.5`. PRD-208 was held for exactly this greenlight.

**The gate, run for real.** `codex-review.yml` dispatched against `0f72e32` (run
28563373849) produced a genuine artifact: resolved-model=`gpt-5.5` (requested honored,
no fallback event, allowlist-verified), codex-cli 0.142.1, openai/codex-action
read-only, fresh context, SHA-pinned. This is the first PRD-208 Codex leg that
actually satisfies the CLAUDE.md gate properties (in-tree + durable, SHA-pinned,
verified-real Codex, read-only, fresh-context). Verdict: **APPROVE WITH EDITS** — no
required edits on the implementation; one non-blocking recommended edit (the PRD-190
PROJECT_STATE row still said "SMA Composite", stale after this rename), applied at
closeout.

**Human at the seam.** The implementation, the Codex dispatch, and the dashboard-
publish scope call were Dustin's decisions this session (dispatch: yes; live publish:
out of scope — the published snapshot refreshes on the next scheduled `cuttingboard.yml`
run, never a hand-overwrite). The PR is opened for a human merge and NOT auto-merged;
the merge stays Dustin's.

---

## 2026-07-01 — PRD-212 SUPERSEDED: the Codex-gate outage was a deprecated model, not a CLI-alias problem

**What we believed (PRD-212's premise):** the gate's persistent model-metadata
fallback was a CLI/alias-resolution instability, freezable by pinning codex-cli to
0.142.1. Acceptance was written as "keep model=gpt-5-codex, it is proven served
under the pin."

**What was actually true:** `gpt-5-codex` was deprecated by OpenAI on 2026-04-01
(the entire GPT-5.0/5.1 Codex family retired in one sweep) — before PRD-212 was
authored. A retired model cannot be served; the "metadata not found → fallback"
error is the documented consequence of requesting it. No CLI version pin can
resurrect a retired model. PRD-212 targeted the wrong layer of a misdiagnosed cause.

**How the premise was falsified:** the Phase-4 live dispatches (2026-07-01, on main
under the 0.142.1 pin) returned FAIL-CLOSED(4) model-metadata fallback every run.
Note: the prior DECISIONS crediting "Phase-4 live validation" as a review stand-in
was authored 2026-06-30 22:11 (commit daedf108) — before any Phase-4 run existed —
and the runs, once they occurred, refuted rather than supported the premise. There
is also no PRD-212 Claude-review artifact; the review claim was self-asserted in the
implementation commit, and the implementation was a direct manual merge (39811bf)
with no review PR. Both waiver legs are void.

**What actually fixed it (PR #76):** the model *target*, not the pin. Set the
`model` input to `gpt-5.5` and `ALLOWED_CODEX_MODELS` to `gpt-5.5 gpt-5.5-*`.
Validated end-to-end by run 28560459040 (dd843fe): review/resolve/land all green,
resolved-model=gpt-5.5, exit 0, artifact landed. This account is served gpt-5.5
under its existing API key (auth is API-key, not ChatGPT sign-in). gpt-5.5 is the
accepted target; gpt-5-codex is retired and must not be restored.

**Amended acceptance (supersedes PRD-212:45,65):** the gate's certified model is
`gpt-5.5` (family glob `gpt-5.5-*`), evidenced by run 28560459040. Acceptance is
"requested model is served without fallback and matches the allowlist glob," not a
fixed `gpt-5-codex` string.

**What worked and is NOT superseded:** PRD-207. The gate it built to fail-closed on
silent fallback detected this real, permanent fallback with perfect accuracy — it is
what surfaced the problem. The detection infrastructure held; only PRD-212's
diagnosis failed.

**Residual seam (tracked, not fixed here):** the honor-gate infers "served == 
requested" negatively — this toolchain exposes no served-model id, so honor is
inferred from absence-of-fallback plus turn.completed. The guarantee therefore rests
on the fallback *detector*; if OpenAI changes the fallback wording, that detector
must still catch it. Durability follow-up owns this.

**Lesson:** "model not served" is not always a repo or CLI fact. Sometimes the model
no longer exists — and that fact lives in the vendor's changelog, not this repo. The
doctrine "artifacts overrule recollection" has a dual: for facts that live *outside*
the repo, the artifacts are the thing that goes stale. First check on any future
"model not served" is "does this model still exist."

**Registry note.** PRD-212's row stays `COMPLETE` (its code merged at `daedf10` and
PR #76 *retains* the `0.142.1` pin — the change was not reverted, only its diagnosis
corrected); `SUPERSEDED` is not an allowed registry status and demoting the highest
PRD would regress `next_prd`. The supersession is carried as a title/PROJECT_STATE
annotation plus this entry, not a status flip.

---

## 2026-07-01 — Staged queued-item decisions (PR #51 / PRD-188 / PRD-209)

Recon-and-stage pass over three parked/queued items; durable findings at
`audits/recon-2026-07-01/staged-queued-items.md`. Dustin's decisions, executed this
session as doc mutations behind the human merge seam (PR #51 close is the only direct
action).

**1. PR #51 (PRD-205 codex-review-router) — CLOSED; router idea dropped.** The
`PRD-205` number was void-filled at the PRD-207 closeout (see 2026-06-29
"Numbering-gap convention"; `PRD_REGISTRY.md:225` and `prd_index.json` both record
`DEPRECATED`), orphaning the PR's identity; its pre-void base is now
`mergeable_state: dirty`. The router *capability* was never built — Codex-review runs
via `codex-review.yml` (PRD-197/-207/-212) with host-vs-CI routing chosen by CLAUDE.md
doctrine, not a tool. Closed as orphaned; the auto-routing wrapper is dropped for now
(refile under a live number if the in-container `host_not_allowed` hazard resurfaces).

**2. PRD-188 SHOCK-banner go/no-go (2026-07-15) — ADVISORY; PRD-188 stays parked.**
The date was only a PROJECT_STATE note (origin: 2026-06-19 cadence #3 remediation) with
nothing behind it: `macro_awareness.yml` is `workflow_dispatch`-only by design, and the
PRD-188 gate is unstarted (corpus = 2 cases / 0 labeled; threshold T = TBD; no
eval-result artifact under `audits/`; no explicit go). Decision: treat 2026-07-15 as
**soft/advisory, not a scheduled gate** — PRD-188 remains parked, no eval work
commissioned this session. Making it a live go/no-go later is separately-approved work:
label/expand the corpus, set T, run `tools/macro_awareness_eval.py` to an `audits/`
artifact, then decide.

**3. PRD-209 OHLCV bar-count floor — SHELVED (reopen-on-incident).** The count-blind
ingestion gates (`_is_fresh_ohlcv_cache` date-only; `_fetch_ohlcv_from_yfinance`
empty-only accept) are a *verified latent* fail-silent hole (PRD-198 #1), but the
incident that motivated urgency (F08) was root-caused to a path divergence and fixed by
PRD-210 — not a truncation. No real short-frame-served-as-fresh event has been observed.
Per VISION "cuts before additions," the guard is **documented, not built**: PRD-209 is
retained as a reopen-on-incident spec. **Reopen trigger:** an observed
short-frame-served-as-fresh occurrence, or a deliberate election to enforce PRD-198 #1
proactively. Registry row left PROPOSED (no `SHELVED` status enum exists; the shelve
lives here and in the PRD's own STATUS marker, not as a registry flip).

**Open diagnostic question (resolved; does NOT flip the shelve).** PRD-209 flagged an
unresolved question — was QQQ's 2026-06-24 15:30 failing-slot frame *short*
(INSUFFICIENT_HISTORY, floor-relevant) or *closes-None* (DATA_UNAVAILABLE, not
floor-covered)? The render token was **DATA_UNAVAILABLE** (per
`trend_structure._classify_sma_unavailable`, `_close_series` returned None); derived
computed QQQ EMAs the same run (≥21 bars, no "OHLCV failed" log); diag2-2026-06-24
root-caused it to path-divergence (fixed by PRD-210). Evidence → closes-None, not a
short frame served as fresh → no observed floor-incident → shelve stands. The definitive
confirm-check (row-count of the restored `QQQ_ohlcv.parquet` vs `SPY` at a failing slot)
needs live/publish cache state unavailable in-sandbox; it is belt-and-suspenders and does
not change the math. If a future live confirm ever shows QQQ *was* short at a failing
slot, that IS the reopen trigger.

---

## 2026-06-30 — PRD-212: Codex gate alias-drift incident + CLI-identity pin

**Incident.** `codex-review.yml` left `codex-version` unpinned, so each dispatch
installed a floating "current" Codex CLI. The current CLI dropped local metadata for
the `gpt-5-codex` model id — it emitted `Model metadata for ``gpt-5-codex`` not found.
Defaulting to fallback metadata` and ran a fallback model. The PRD-207 honor gate
correctly fail-closed (exit 4, no artifact). This blocked **every** Codex cross-review,
not just PRD-208 — the HIGH-RISK review lane had no working gate. Reproduced live:
run `28467193644`. Diagnostic confirmed the OpenAI key is present/valid/scoped (a
1.55M-token review completed); the cause is CLI/alias drift, not key or access — the
movable-identity failure class (CLAUDE.md #6; same family as PRD-207/198).

**Pinned identity = the CLI version, not a model snapshot.** This toolchain surfaces
**no** dated `gpt-5-codex-YYYY-MM-DD` snapshot id (PRD-207: no structured served-model
field); the only model identity it records is the alias `gpt-5-codex`. The fix pins
**`codex-version: 0.142.1`** — the last CLI with landed proof of honoring the alias:
two certified artifacts (`codex-review/PRD-210-7e836b9765cd`,
`codex-review/PRD-208-b42ec9aa7ebe`) record `resolved-model=gpt-5-codex … codex-cli=codex-cli 0.142.1`.
`0.142.1` is >0.2.x, so `sandbox: read-only` stays enforceable. **The alias is stable
ONLY downstream of the CLI pin** — under the pinned 0.142.1 it resolves to real
metadata; unpinned, it drifts. `model` stays `gpt-5-codex` (deterministic under the
pin). `ALLOWED_CODEX_MODELS` (the `vars` repo variable, Dustin-set) = **`gpt-5-codex`**
exactly — the one proven-served id, no widening.

**Test honesty — tripwire, not behavioral proof.** The new
`test_prd212_codex_version_pinned_tripwire` is a PRESENCE/STRUCTURE check (pin == 0.142.1):
it proved RED against the unpinned workflow and GREEN after the pin, and any change away
from 0.142.1 goes red. It **cannot** prove 0.142.1 actually honors `gpt-5-codex` — that
is a live-only fact (Phase-4 acceptance: a real dispatch certifying `resolved-model=gpt-5-codex`
HONORED, artifact lands). The BEHAVIORAL honor guard already exists and is unchanged:
the PRD-207 R3 resolver tests run the workflow's own resolver against the real captured
fallback/honored streams (fallback → fail-closed; honored → certify). The tripwire is
labelled as such in-test and here so it never stands in as the behavioral guard
(anti-hollow-gate, PRD-198 #4).

**Bootstrap waiver (second this arc — FLAG for next alignment audit).** PRD-212 repairs
the Codex gate itself, so the gate that would supply its Codex cross-review is the subject
under repair; the Codex leg is waived under the PRD-207 bootstrap precedent (Claude review
+ the recorded Phase-4 live validation stand in). This is the **second** bootstrap
Codex-waiver this arc (PRD-207 first). Gate repairs are necessarily un-cross-reviewed —
**flagged for the next alignment-cadence audit** to confirm the pattern is not masking
drift. HIGH-RISK/INFRA, manual-merge (Dustin holds the seam). Live confirmation is Phase 4,
a separate greenlight; PRD-208 stays parked until then.

---

## 2026-06-30 — Alignment cadence check #5 — PASS (no drift)

Fifth cadence check (since #4 on 2026-06-20), run at Dustin's request after the
PRD-211 merge (main @ `3317456`, PR #71). Scope: PRDs merged since check #4's
boundary — PRDs 203, 204, 207, 210 (impl), 211 — plus the PRD-186 post-merge
drift audit. The window is display / governance / path-coverage tooling only; no
trading-pipeline module added.

- **Q1 (new prediction logic?):** No. The window is display correctness
  (PRD-211 macro-tape metals label, PRD-208-class presentation), governance/harness
  tooling (PRD-203 `prd_close.sh` baseline rebuild, PRD-207 codex-review gate
  repair), and path coverage (PRD-210 premarket trend-structure history fallback —
  the F08 closes-None fix). No ML/forecast/backtest surface.
- **Q2 (new sidecar without consumer or observational purpose?):** No new sidecar
  added. The proposed AI Pathways "Options Monitor" sidecar was correctly *never*
  scaffolded — no orphan observational surface entered the tree.
- **Q3 (new module not serving the four questions?):** No. No new module outside
  VISION's four questions; the window is presentation fixes plus process/governance
  tooling, observational/descriptive character intact.

**Verdict: PASS.** No prediction logic, no orphan sidecar, no non-serving module.

**Post-merge drift audit (PRD-186) — PRDs 203/204/207/210/211:** all carry a Claude
review artifact with a DRIFT CHECK; PRD-210 also carries an in-tree Codex
cross-review; PRD-207's Codex cross-review was waived under the recorded bootstrap
exception (the gate under repair); PRD-211 is MICRO (no review artifact owed, drift
self-checked). No substantive drift found, no stale PROJECT_STATE claim, no
DRIFT-CHECK omission. No corrective PRD required.

**Gating cleanup, scheduled next, NOT bundled here:** the 205–210 registry reconcile
(void-vs-real rows, parked stage-0 branches, the PRD-210/211 closeouts) is a separate
recon + bookkeeping pass held for Dustin's merge seam — explicitly out of scope for
this cadence entry.

---

## 2026-06-29 — Numbering-gap convention: void-fill skipped numbers at closeout

PRD-205/206 were never authored; 207 and 210 were filed out-of-order into the
gap. On closing 207 the registry contiguity check (`validate_prd_registry.py`
line 125) required 205/206 to exist. Recorded as DEPRECATED void placeholders
(File column present, no history doc owed per validator line 225) rather than
backfilled as phantom work. Future out-of-order filings into a gap should
void-fill the skipped numbers at closeout.

---

## 2026-06-29 — PRD-207 closeout: Codex cross-review waived (bootstrap)

PRD-207 repaired the codex-review gate itself; the gate that would supply the
required Codex cross-review artifact was the subject under repair. The
cross-review is therefore waived under the bootstrap exception — no
`PRD-207.review.codex.md` is owed. Provenance rests on the Claude review
(`PRD-207.review.claude.md`) plus the recorded live validation (`13c5d4a`),
which confirmed the repaired gate fail-closes on a substituted model on its
first live run. Registry row flipped IN PROGRESS → COMPLETE this commit.

---

## 2026-06-26 — Repaired Codex gate fail-closed on its first live run (PRD-207 bootstrap validation)

The repaired `codex-review.yml` fail-closed on its FIRST live run — run 28277644046,
reviewing PRD-208 @ `ceceedb`. Requested `gpt-5-codex` was again served the fallback
model; the fixed gate detected codex's structured `item.error`, exited
FAIL-CLOSED(4), emitted no artifact, skipped `land`. The pre-fix hollow gate would
have laundered the same substitution into `resolved-model=gpt-5-codex` and certified
it. This is the PRD-207 bootstrap-note validation: the gate's first act was to refuse
a substituted model. PRD-208's HIGH-RISK Codex leg remains UNSATISFIED — held pending
a genuine allowlisted Codex review, not because the diff is bad.

---

## 2026-06-26 — PRD-210 registry row left IN PROGRESS by design (deferred out-of-order closeout)

PRD-210 merged out-of-order at `b1619f6`; registry row intentionally left IN PROGRESS, closes in-order when 205-209 land — not drift. See `recon/board-state-20260626.md` (commit `c25f9e5`).

---

## 2026-06-26 — Trend-structure "VWAP not applicable" is correct-by-design, not a bug

The dashboard's Intraday Context cell shows a uniform "VWAP not applicable"
across all rows. Recon (`recon/board-state-20260626.md`, commit `c25f9e5`)
classified this as a *population gap that is correct by construction*, not a
defect: the trend-structure VWAP frame (`history_by_symbol`) is built from
`_collect_trend_structure_history(ohlcv)` (`runtime/__init__.py:549`), where
`ohlcv` is the **daily** `fetch_ohlcv()` (`ingestion.py:119`). The intraday
source `fetch_intraday_bars()` (1-minute, `ingestion.py:170`) feeds only
entry-trigger evaluation (`evaluation.py:160`) and `runtime/__init__.py:1177`,
**never** the trend-structure VWAP path. So `_is_intraday(df)` is structurally
always false there and `_vwap()` returns `None` → `NOT_COMPUTED`
(`trend_structure.py:55,134-135`), matching PRD-107's documented boundary
("daily bars → vwap=null"). Confirmed by `logs/trend_structure_snapshot.json`
(every row `"vwap": null`). PRD-210 does not change this — it wires the PRD-174
history fallback for missing *daily* trend-structure history, not an intraday
source.

**Decision:** no fix. The string is honest under the current daily-only design.
Routing intraday bars into the trend-structure frame would be a deliberate
feature (description-of-reality, scope a PRD) — not a bug patch.

## 2026-06-23 — Codex invocation is environment-dependent (host `codex exec` vs CI workflow)

The two Codex surfaces are not interchangeable, and which one is reachable
depends on where the agent runs:

- **Host `codex exec` (Dustin's machine):** the only surface that can carry a
  custom, adversarial LOGIC review prompt. Requires `~/.codex` credentials and
  network egress. Read-only reviews run `codex exec -s read-only - < prompt`.
- **CI Codex (the PRD-197 GitHub Actions workflow):** a FIXED consistency pass.
  It cannot carry a custom review focus — it runs its own prompt. Containers
  (including this remote-execution environment) reach Codex only through this
  workflow; there is no local `codex exec` because the egress wall is by design.

**Rule:** do NOT prompt for or assume local `codex exec` from inside a container —
it will fail at the egress wall. A genuinely adversarial cross-review (vs a
consistency pass) must be run host-side with a real prompt; from a container, the
only Codex channel is the PRD-197 CI workflow. This keeps the review-gate
expectations stable as the available Codex surfaces change (CLI egress, GitHub
connector, future channels) — see the Codex cross-review gate's "properties, not
mechanism" framing in `CLAUDE.md`.

---

## 2026-06-20 — Alignment cadence check #4 — PASS (no drift; 1 stale annotation remediated in place)

Fourth cadence check (since #3 on 2026-06-19), run at Dustin's request after the
PRD-200/201/202 batch. Scope: PRDs merged since check #3 — PRDs 200, 201, 202 —
plus the PRD-186 post-merge drift audit.

Net new production modules since #3: none. The batch is governance/process/harness
tooling: PRD-200 wired the pre-existing `tools/validate_prd_registry.py` into the CI
`test` job (+ a `--skip-commit-resolvability` flag) and reconciled registry/index
data; PRD-201 added a Claude Code harness hook
(`.claude/hooks/canonical_read_guard.sh`); PRD-202 added CLAUDE.md Workflow-pattern
guidance. No trading-pipeline module added.

- **Q1 (new prediction logic?):** No. A CI consistency gate, a non-blocking Read
  reminder hook, and docs guidance — no ML/forecast/backtest surface.
- **Q2 (new sidecar without consumer or observational purpose?):** No sidecars added.
- **Q3 (new module not serving the four questions?):** No. The only new file,
  `canonical_read_guard.sh`, is agent-context-discipline harness tooling (same class
  as `protect_files.sh` / `prd_eval.sh`), not a pipeline module touching the four
  questions; `validate_prd_registry.py` pre-existed.

**Verdict: PASS.** No prediction logic, no orphan sidecar, no non-serving module; the
batch is process/governance tooling, observational/descriptive character intact.

**Post-merge drift audit (PRD-186) — PRDs 200/201/202:**
- PRD-200 (HIGH-RISK): Claude + Codex review artifacts both carried a DRIFT CHECK
  (no VISION conflict; PROJECT_STATE updated). No finding.
- PRD-201 (STANDARD): Claude review artifact carried a DRIFT CHECK (no VISION
  conflict). No finding.
- PRD-202 (MICRO): no review artifact required; drift self-checked inline (no VISION
  conflict). Confirmed here. No finding.

**One finding, remediated in place:** the PROJECT_STATE test-baseline line had drifted —
`prd_close.sh` advanced the count to 2819 but left the prior provenance anchor ("after
the PRD-195 merge — run 27732171939 for 470aa2b") and an obsolete sandbox-2796 /
5-signing-tests note (this sandbox now matches CI at 2819). Corrected in this update to
the PRD-201 merge run (27865518359 / `b1f2598`). Per the refined CLAUDE.md:242-244 rule,
a doc-accuracy staleness fixed in place does not require a corrective PRD.

**Tooling follow-up (noted, not opened):** `prd_close.sh` rewrites only the baseline
*count*, not the surrounding provenance text, so the line goes stale every closeout. A
future tweak should rebuild the whole baseline line from `--ci-summary` (run id +
commit), not just the number.

Next cadence check by 2026-07-31 (or the next phase boundary, whichever comes first).

---

## 2026-06-19 — Drift-remediation scaled to severity (CLAUDE.md:242-244 refined)

The post-merge drift-audit remediation rule mandated a corrective PRD for ANY drift,
including a review-artifact DRIFT-CHECK omission. Alignment cadence #3 (below) hit that
case on PRD-190's review, and a Codex-connector review comment on PR #41 correctly noted
the in-place fix did not satisfy the rule as written. Rather than silently deviate
(VISION: resolve a code/doc divergence by changing one or the other, never leave it to
drift), the rule was refined to scale remediation to severity:

- Substantive drift (a VISION non-goal/principle conflict, or a stale PROJECT_STATE
  claim) → corrective PRD, number recorded. Teeth unchanged.
- Review-artifact process miss (a merged review that skipped the DRIFT CHECK) →
  remediated in place (append the section, confirm no substantive drift); no PRD.

Rationale: forcing a full corrective PRD for a one-line retroactive doc append conflicts
with CLAUDE.md's own "bug fixes within established patterns don't need PRDs" and "cuts
before additions". The refinement is principled independent of the triggering instance,
and fully retains the corrective-PRD requirement for real drift. Carried by governance
PR #42 (CLAUDE.md, manual-merge); recommend merging #42 before this cadence record.

---

## 2026-06-19 — Alignment cadence check #3 — PASS (no drift; 2 process findings remediated)

Third cadence check (since #2 on 2026-05-29), run at Dustin's request. Scope: all
PRDs merged since check #2's boundary commit 24ce294 (2026-05-29, PRD-159 closeout)
through main — PRDs 161–199 — plus the PRD-186 post-merge drift audit.

Net new production modules since the boundary (the check-#2 method): regime_history.py
(PRD-175), red_folder.py (PRD-176), the runtime/ skeleton (PRD-173), and the
macro_awareness producer/eval in tools/ (PRD-187). Everything else was tests,
CI/preview tooling, governance (PRD-182–186, 196, 198), or bookkeeping.

- **Q1 (new prediction logic?):** No. No ML/forecast/backtest surface in the diff; the
  only "prediction" token is a comment in regime_history.py affirming "Description, not
  prediction." Kill switch (PRD-180) is Q4 invalidation; short-gate (PRD-181) is a
  discipline gate; macro votes (PRD-177) are descriptive cyclicality labels.
- **Q2 (new sidecar without consumer or observational purpose?):** No. regime_history and
  red_folder are both consumed by dashboard_renderer.py; macro_awareness (PRD-187) is
  observational (a materiality eval) with a documented, gated, render-only consumer
  (PRD-188, decision-decoupled).
- **Q3 (new module not serving the four questions?):** No. regime_history → Q1,
  red_folder → Q2, macro_awareness → Q2; runtime/ is a refactor of the existing pipeline
  (acknowledged debt, re-eval 2026-08-15).

**Verdict: PASS.** No prediction logic, no orphan sidecar, no non-serving module; the
period remains observational/descriptive in character.

**Post-merge drift audit (PRD-186) — 2 process findings, both remediated here:**
1. PRD-190's HIGH-RISK review artifact omitted the PRD-186-mandated DRIFT CHECK section
   (merged 2026-06-19, after PRD-186). Substance verified non-drift in this audit
   (config-only OHLCV_FETCH_MONTHS bump, zero contract change). Remediated in place per
   the refined CLAUDE.md:242-244 rule (governance entry above; PR #42): the missing DRIFT
   CHECK was appended to docs/prd_history/PRD-190.review.claude.md. A review-artifact
   process miss of this class no longer requires a corrective PRD.
2. The macro_awareness materiality eval (PRD-187) had no re-evaluation date for the
   PRD-188 banner go/no-go — borderline against VISION's "acknowledged debt carries a
   re-evaluation date." Remediated: go/no-go date 2026-07-15 recorded in PROJECT_STATE.

Cleared (not findings): PRD-187 has no Claude review artifact but is STANDARD-lane SIDECAR
class (HIGH-RISK independent review not required); the one stale PROJECT_STATE claim
(PRD-190 "closeout pending") was already reconciled via PR #39 earlier the same day.

Next cadence check by 2026-07-31 (or the next phase boundary, whichever comes first).

---

## 2026-06-17 - PRD-194 verified end-to-end; PRD-194 + PRD-189 closed out

Rollout executed: seeded the unprotected `publish` branch from `main` (`git push
origin main:publish`), then dispatched the live pipeline (`workflow_dispatch`,
mode=live, ref=main; run 27665400742). Verified end-to-end:
- Pipeline run: completed / **success**.
- `publish` advanced `365f0fe -> 1c2a0ff` ("CB report: 2026-06-17 | NEUTRAL | 0 trades
  | SUCCESS"). `main` **byte-unchanged** (still `365f0fe`) — no bot push to main, no
  GH006.
- Artifacts: `audit.jsonl` **+2** (delta-append — this run's rows, not clobbered); a
  brand-new gitignored `logs/run_2026-06-17_041722.json` reached publish (validates the
  force-add fix); `ui/dashboard.html`+`index.html` regenerated; `market_map` /
  `regime_history` / `latest_*` updated.
- Pages deploy 27665453156 (`workflow_run` on the pipeline): **success** — dashboard
  displayed from `publish`.

This is the live validation the R7 content guards could not provide (they pin content,
not runtime). Every PRD-194 mechanism exercised: worktree delta-append, force-add of
ignored artifacts, lifecycle/dedup read-back restore, ui render, main-protection
intact, Pages-from-publish via workflow_run.

Closeout: **PRD-194 COMPLETE** (PR #16 / `365f0fe`). **PRD-189 COMPLETE** — its closeout
was held pending PRD-194 + a fresh published scoreboard row; both now satisfied. The
parked PRD-189-review hourly render-before-aggregate nit was fixed inside PRD-194.
Still open: PRD-190 (R4 live-diff gate), PRD-191 (not started), PRD-192/193 (PROPOSED).
Tracked follow-up (not yet opened): `run_*.json` storage cap/prune on publish.

## 2026-06-16 - PRD-194: production publish decoupling onto an unprotected `publish` branch (option b / state-home b1)

Staleness audit (2026-06-16) found the published dashboard frozen by two
compounding causes. The first (scheduled runs resolving to noop on a wall-clock
match) was fixed by PRD-189; fixing it un-masked the second: the artifact-publish
path direct-pushes to `main`, and `main` branch protection (PRD-182/184, 2026-06-14)
now rejects every such push (GH006, "Required status check 'test' is expected").
Verified live: run 27637384167 (2026-06-16 17:56 UTC) ran the full pipeline,
committed the 2026-06-16 scoreboard row in the runner, and failed only at the push.
`tools/ci_push_artifacts.sh` (`git push origin HEAD:main`) is invoked by three
workflows — cuttingboard.yml, hourly_alert.yml, macro_awareness.yml — so the
dashboard, scoreboard, and macro sidecar are all frozen behind the same wall.

Decision: option (b) — publish to a dedicated UNPROTECTED branch (`publish`) that
Pages deploys from. Rejected: (a) bot bypass of main protection (erodes the
PRD-182/184/186 guardrail); (c) PR + auto-merge per artifact (a full test run + PR
per hourly publish; minutes of latency on a "fresh" surface). State-log home: b1 —
the publish branch carries both `ui/` and the read-back `logs/audit.jsonl`; the
pipeline checks out `main` for code and restores state from `publish` at run start,
so the scoreboard accumulates without `main` ever taking a bot push.

Final mechanism (implemented PR #16, 2026-06-17 — supersedes the originally-sketched
"rebase onto publish + shared cb-publish lock"):
- WORKTREE publish on the publish tip. logs/audit.jsonl is DELTA-APPENDED (this run's
  rows beyond the restore base); other artifacts overwrite from the committed blob.
  No rebase (it would 3-way-conflict on the append-only audit log).
- NO shared concurrency lock. The shared `cb-publish` group over-serialized the
  time-sensitive hourly alert (Codex P2), so each writer keeps its OWN per-workflow
  group and cross-workflow publish races are absorbed by a bounded
  retry-on-non-fast-forward in ci_push_artifacts.sh (re-fetch tip, re-apply this run's
  delta, re-push). Delta-append makes the retry idempotent.
- PER-FILE OWNERSHIP: every published artifact has exactly one owner-publisher;
  consumers restore read-only and revert before commit (never republish a non-owned
  file). Read-back set per writer is enumerated in PRD-194.md (R3), swept from every
  logs/ read + write-site.
- TWO-TREE SYNC INVARIANT: logs/ accumulators flow publish→run (publish authority);
  ui/ static assets flow main→publish via full-sync from CURRENT origin/main (NOT the
  run's POST_SHA — a run based on an older main must not roll publish back to stale
  JS/CSS; Codex P2) (main authority); generated ui pages are published only by a run
  that regenerated them.
- Read-back sweep correction + closure: the literal-path + *_PATH sweep missed glob
  reads; a glob sweep found logs/run_*.json (renderer globs it for "Changes Since Last
  Run") — pipeline-owned, accumulating, immutable per file, now restored by both writers
  (idempotent). The exhaustive closure sweep (named + *_PATH + .glob() + write-sites)
  then found one more symmetric cross-read: the renderer's _load_contract_entry_context
  reads HOURLY-owned latest_hourly_contract.json for entry prices on the PIPELINE render
  too — now restored read-only + reverted before commit. Cross-workflow render reads are
  now all covered (hourly→{latest_run,macro_drivers,run_*}; pipeline→{latest_hourly_contract});
  ZERO remaining read-back gaps. Glob-gate bug (Codex): `git ls-tree -- '<glob>'` does
  NOT expand the wildcard, so the gate uses a shell `case` match; fixed + behaviorally
  tested. DEFERRED to a tracked follow-up PRD (not folded here): run_*.json unbounded
  accumulation on publish needs a storage cap/prune (delete-propagation).
- Publish-write hardening (Codex): (a) the worktree overlay force-adds the gitignored
  artifact dirs (`git add -f -- logs`/reports) after `add -A`, else NEW untracked
  ignored artifacts (a fresh run_<ts>.json each run; macro_*.json on a bootstrapped
  publish) are silently skipped and never published. (b) verify mode must NOT publish:
  it validates only and does not regenerate latest_run/payload/contract, so it would
  publish a dashboard rendered from main's frozen snapshots; PUBLISH_READY stays false
  for a verify-only dispatch (live/sunday set it in their own Run steps). (c) bootstrap
  race: if two writers race to CREATE an absent publish branch, the loser's push is a
  non-fast-forward — it now falls through to the delta-append/retry path (not a set -e
  exit), with the audit delta anchored on PRE_SHA (= main) so it appends only its own
  rows rather than re-appending main's frozen base the winner already published. (Mostly
  defensive — the rollout seeds publish, so the bootstrap path is rarely hit.)
- Dispatch publishers pinned to `ref: main`, AND the publish/push step of all three
  writers is ref-guarded `if: github.ref == 'refs/heads/main'` (Codex P1): a non-main
  workflow_dispatch runs the pipeline (test/lint/render) but never pushes to the
  unprotected branch. Residual: an attacker who EDITS a workflow on their own branch and
  dispatches it can drop the guard (the dispatched ref supplies the YAML); that is closed
  only by OUT-OF-TREE governance — branch protection / CODEOWNERS on `.github/workflows/**`
  plus restricted workflow_dispatch — PRD-186-adjacent and largely moot in a solo-write
  repo (the threat actor needs write access). Pages deploys via workflow_run on all three
  writers (a GITHUB_TOKEN push can't fire on:push).

Lineage: this finishes the decoupling PRD-178 began. PRD-178 decoupled PREVIEW (an
on-demand, never-deploy render loop) and explicitly held production publish out of
scope (its R3 forbade touching pages.yml/hourly_alert.yml/cuttingboard.yml).
Production publish was never decoupled — PRD-194 does that half. After PRD-194 lands,
CLAUDE.md:52-54 ("no direct-push path") becomes true; this PRD's scope corrects that
wording. PRD-186 governance-adjacent (branch-protection config + guardrail prose) →
the implementing PR is MANUAL-MERGE-ONLY (PR #16). Validated by CI green + behavioral
temp-git tests; the live multi-branch flow is proven at the manual rollout (seed
publish unprotected; live dispatch). See docs/prd_history/PRD-194.{md,review.claude.md}.

---

## 2026-06-14 - PRD-186: governance carve-out enforcement - (a) landed, (c) deferred (corrected: label-gated check, not CODEOWNERS)

Refines the (c) enforcement recommendation in the PRD-186 entry below; the
CODEOWNERS approach is withdrawn for the reason stated here (CLAUDE.md R4 and
PRD-186 R4 still name CODEOWNERS - superseded by this entry, fix on a follow-up).

PRD-186: governance carve-out landed as (a) policy-only (agent-honored CLAUDE.md
rule; this PR dogfoods it). (c) mechanical enforcement deferred. Known soft-edge:
the carve-out boundary is prose-defined, so until (c) lands it depends on correct
section classification by the agent. When pursued, build (c) as a required-check
guardrail workflow gated on a human approval label - NOT CODEOWNERS: CODEOWNERS +
single owner forces admin-override merge, which bypasses the `test` gate on
guardrail merges. Trigger: a real guardrail PR appears, or a decision to move from
judgment-based to structural enforcement.

## 2026-06-14 - PRD-186: drift-review gate (closes the PRD-184 audit gaps)

The PRD-184 audit confirmed auto-merge removed the pre-merge human checkpoint
while the per-PRD review checked only correctness. PRD-186 closes four gaps:
(1) the `prd-review-claude` skill + the CLAUDE.md HIGH-RISK review gate now
record a per-PRD DRIFT CHECK (VISION non-goal/principle conflict + PROJECT_STATE
staleness), not just correctness; (2) CLAUDE.md frames drift-review as a
post-merge audit under auto-merge (no pre-merge human read); (3) the Alignment
cadence gains teeth - each run audits PRDs merged since the last audit against
VISION/PROJECT_STATE, defines drift, and remediates by opening a corrective PRD;
(4) a governance carve-out makes PRs that change the review skill or the
governance/auto-merge policy manual-merge-only (excluded from auto-merge).

Enforcement of (4): landed as policy (agent-honored - this PRD itself is
manual-merge). Recommended mechanical hardening is option (c): relocate the
governance/auto-merge policy into a dedicated CODEOWNERS-protected file +
branch-protection "require Code Owner review", which auto-merge cannot satisfy
(forcing a human merge) WITHOUT taxing routine CLAUDE.md/PROJECT_STATE edits.
Rejected: (a) policy-only has no mechanical backstop; (b) CODEOWNERS on all of
CLAUDE.md would gate every routine edit. (c) needs repo-admin; tracked as a
follow-up, not landed here. PRD-186 is MANUAL-MERGE and dogfoods the carve-out.

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

Update (PRD-184 closeout, same day): the residual risk is moot in practice - the
harness auto-mode classifier blocks Claude from ANY direct-to-main push (it
denied `git push origin main` for the closeout itself), independent of
branch protection. So the binding gate is the harness, and the
"bookkeeping may push to main directly" carve-out was retracted: ALL work,
including closeout bookkeeping, lands via PR + CI + auto-merge. CLAUDE.md was
corrected to match. `enforce_admins=true` would add belt-and-suspenders for
non-agent pushes but is not required to gate Claude.

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

**Skill retirement (2026-07-10):** `.claude/skills/real-data-validation/SKILL.md`
and `scripts/validate_consumer_prd.py` — the mechanized form of this pattern
added the same day under "Post-VISION workflow tightening" — were deleted.
Retention price was too high: the skill drifted while dormant, citing a PRD
CLASS outside `docs/PRD_PROCESS.md`'s closed base set and a directory
convention `CLAUDE.md` no longer states. A checklist that misdirects on
first use is worse than no checklist. The discipline itself is unaffected —
it lives in this entry, not in the retired skill.

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
