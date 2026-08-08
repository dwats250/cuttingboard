# CuttingBoard — Fable Outsider Memo (2026-08-08)

STATUS: Temporary synthesis input for the cross-session reconciliation, NOT
canonical project authority. Commissioned by the 2026-08-08 Reconciliation
Working Notes (§9 outsider-pass assignment). No PRD is allocated by this
document; it edits nothing, authorizes nothing, and is scratch under the
PRD-230 session-note rule — durable findings graduate to `docs/DECISIONS.md`
or a PRD, and this file is deletable once the reconciliation absorbs it.

Grounded in repo state at `main` = `7d0805ee` (PRD-289 merge). Evidence:
direct reads plus a 7-agent read-only survey; every load-bearing claim below
was verified against a file, not chat memory.

## 1. The project story, organized

**Shipped foundations.** Three layers, in dependency order. (a) *Truthful
authority*: TRUTH-SYNC's nine rulings, GOV-2, the Product-Delivery Operating
Rule, and the Owner-Merge Convention turned "what is true, complete, parked,
and authorized" into a repo-answerable question — the registry validator
exits 0, L0 is closed, and no allocated-but-unlanded gap remains.
(b) *Trustworthy execution substrate*: the CB-01..CB-07 wave (trade-brake
dormancy, macro-pressure fail-closed, hourly operational truth, ORB session
provenance) removed silent-fallback holes so a green run means what it says.
(c) *The observation seam*: PRD-288's single-fetch SPY FRAME A and PRD-289's
Market Control Card — a 499-LOC, six-file, projection-only consumer with
seven per-field closed vocabularies, an XOR state carrier, typed unavailable
reasons, and no schema change. The wiring pattern (optional PipelineResult
field → keyword-only payload param → additive `sections[...]` key →
presence-gated renderer block) is now a twice-proven template.

**Active product thesis.** A small pre-trade cockpit that compresses market
state into one disciplined, descriptive read — VISION's four questions —
with explicit permission, invalidation, and honest absence. The named trap
is the real risk: better explanations without fewer trading mistakes.

**Candidate next arcs** (ranked in §3): real-use observation of the shipped
card; context registry; Market Map narrowing; GEX evidence→producer→display;
evaluation/cohort work; heatmap; relationship-aware news.

**Longer-horizon enablers.** Freshness-as-product-property (but see the cut
recommendation), renderer decomposition (PRD-238 design doc exists, never
executed), the runtime/ split (re-evaluation date **2026-08-15 — one week
away**).

**Deliberate non-goals / parked.** Macro (KEEP DORMANT by explicit ruling),
PRD-268 (reopen-on-incident), PRD-209 (reopen-on-incident), PRD-275 (blocked
on its own six undismissed constraints), PRD-283-F1 `qualified_count`
semantics (awaiting a Dustin ruling), the 2026-06-10 parked dashboard items.

## 2. Duplication, hidden dependencies, disproportionate overhead

**Duplication found:**

- **The registry already exists three times, badly.** `config.py`'s flat
  lists, `market_map.py:21`'s `PRIMARY_SYMBOLS` (identical to
  `TREND_STRUCTURE_SYMBOLS`), and `watchlist_sidecar.py`'s dormant
  `(symbol, sector_theme, watch_reason)` tuples — which have **zero
  consumers** per `artifact_flow_map.md:123`. The "context registry" lane is
  not new scope; it is consolidation of existing duplication, and TRUTH-SYNC
  ruling 6 already prescribes exactly this (agent drafts from those seeds,
  Dustin ratifies).
- **The registry lane and NEWS-0 are the same deliverable.** Doctrine §5.4
  already specifies NEWS-0 as a static universe/source/theme registry with a
  schema proposal. Drafting two competing registries would be the failure;
  one PRD should satisfy both.
- **Market Map vs. Market Control Card**: market_map's
  GRADE/BIAS/STRUCTURE/SETUP-STATE taxonomy conceptually overlaps the card's
  seven fields. Unreconciled by design (D-4 SPLIT).
- **GEX-0's status is told three ways** — and PROJECT_STATE's "stopped
  without a verdict… waits on an egress grant" contradicts the packet's
  explicit §1 `VERDICT: EVIDENCE INCOMPLETE`. Small, but it's exactly the
  docs-match-code drift class the project polices. Related staleness: the
  Alignment-check "next check" pointer still references the July-era "Opus
  wave / K/L/M" phrasing, and `system_logic_map.md:21` still claims a
  Polygon fallback (tracked CB-27).

**Hidden dependencies:**

- Market Map is **decision-feeding, not decorative**: `trade_visibility.py`,
  `overnight_policy.py`, `notifications`, `runtime` (including cross-run
  read-back), and 5+ renderer sites. Retirement is a real refactor with an
  EXECUTION blast radius, not a display cleanup.
- The card is strictly `run_at_utc`-keyed (FAIL CONDITION 11); any scheduler
  work inherits that determinism contract.
- A GEX producer must live outside the banned-import-guarded modules and
  must use header auth (the 2026-05 `POLYGON_API_KEY` leak is in DECISIONS).
- `macro_awareness.yml` is the one workflow that force-pushes artifacts to
  **main** — a standing exception to "main receives only CI-gated PR merges"
  worth an eventual explicit ruling, though it's documented in the artifact
  flow map.

**Where governance overhead is disproportionate — and where it isn't.** The
MATERIAL machinery is earning its keep on content: the packet cycle and
Codex passes on PRD-289 found real defects (F1–F4, P1-A/P1-B). What is *not*
earning its keep is **the LOC-ceiling estimation loop**: GOV-2 §5
stop-and-renew has now fired on both PRD-288 (195→308→325) and PRD-289
(300→499→525) for the *same root cause* — closed-vocabulary declarations and
fail-loud validation code are ratified requirements but never counted at
estimation time. That's a biased estimator, not scope creep; each firing
costs a full amended-review cycle. The compression is upstream: count
validation surfaces as first-class LOC at packet time (or apply a stated
validation multiplier), so the ceremony stops firing on its own arithmetic.
The owner-authored-mandate path (both 2026-08-06 docs ratified without GOV-2
packet cycles) and TRUTH-SYNC's nine-rulings-one-PR bundling are good
existing precedents for overhead compression; note that PRD-289 generated
five durable artifacts and ran two Codex passes on one PR — at the edge of
the bounded cycle, defensible this once, not a pattern to normalize.

## 3. Ranked future arcs

Composite of three scored lenses (trader usefulness / architectural
leverage / complexity-and-contamination), which converged strongly:

| Rank | Arc | Usefulness | Leverage | Cheap+safe | Verdict |
|---|---|---|---|---|---|
| 1 | Real-use observation of the shipped card | 9 | 8.5 | 9.5 | Do now; zero cost; tests VISION's trap directly |
| 2 | Context registry (= NEWS-0, seeded from watchlist_sidecar) | 4 | 9.5 | 7.5 | Highest *buildable* leverage; unblocks heatmap + news; consolidates 3 duplicate vocabularies |
| 3 | Market Map **narrowing** (not retirement) | 6.5 | 6.5 | 6 | Subtractive, but decision-feeding consumers make it a real refactor; decide after an observation window |
| 4 | GEX-0 fresh pass (→ GEX-1) | 2.5 | 8 | 5 | Lane #2 by owner directive, but engineering-inert: blocked on owner/infra action only |
| 5 | Evaluation / cohort work | 3 | 6 | 8.5 | Cheap and contamination-free; needs an explicit descriptive-only scoping ruling first |
| 6 | Movement heatmap | 5 | 5 | 4.5 | Real value, hard-blocked on registry; a leaf, unblocks nothing |
| 7 | Relationship-aware news | 4.5 | 4.5 | 1.5 | Highest narrative-contamination risk; double-blocked (registry + NEWS evidence chain) |
| 8 | GEX-2 display card | 3.5 | 3.5 | 2.5 | Two gates downstream; conditional on provider viability |
| 9 | Scheduler/freshness ("Cloudflare is the clock") | 2 | 2.5 | 3 | Probably cut as framed — see §4 |
| 10 | Macro-awareness | 0 | 1 | 0.5 | Owner-ruled dormant |

**The one sequencing tension worth surfacing:** the Operating Rule orders
GEX (#2) ahead of the registry (#3), but GEX's next step is not engineering
— it is Dustin's: an egress grant, a fresh GEX-0 commission, and a
resolution of the packet's §13e ambiguity (does the egress-blocked
INCOMPLETE end the track or pause the pass?). Those are decisions, issuable
in an afternoon, after which the pass itself is small. So the lane order and
the registry-first instinct are compatible: **present Dustin the bounded GEX
decision immediately, and let registry drafting proceed in parallel as lane
#3** — no lane-order violation, no idle time. One packet finding deserves
weight in that decision: OPRA licensing/redistribution terms could alone
flip the verdict to PROVIDER NOT VIABLE, so the evidence pass is genuinely a
go/no-go, not a formality.

## 4. Must-before / nice-to-have / dormant / cut

**Must happen before X:**

- Dustin's egress grant + fresh commission + §13e ruling → before any GEX
  work at all; GEX-0 `PROVIDER VIABLE` → before GEX-1; GEX-1 proven
  artifacts + Dustin inspection → before GEX-2 (doctrine G3/G8 —
  non-collapsible).
- Registry drafted **and Dustin-ratified** (an explicit owner hold) → before
  heatmap and before news; reconcile registry-vs-NEWS-0 into one deliverable
  → before either PRD is drafted.
- Full dead-branch enumeration of all five consumer files → before any
  Market Map narrowing lands; an observation window on the card → before
  deciding *what* to narrow.
- A Dustin ruling that evaluation work is descriptive/historical only →
  before any cohort build (it sits near the no-backtesting non-goal).
- GOV-2 §1 MATERIAL classification at intake, individually → before
  registry, GEX-1/2, heatmap, news, or Market Map PRDs (each plausibly
  qualifies; MATERIAL forces STANDARD-at-minimum).
- Fixing the estimation bias (count validation surfaces) → before the next
  MATERIAL packet's ceiling is set, or §5 will fire a third time.

**Nice to have:** heatmap; evaluation/cohort; PRD-274 micro debt;
generalizing the dashboard wiring pattern **at its third instance, not
before**; the PRD-283-F1 `qualified_count` ruling; refreshing the stale
Alignment-check pointer. Note an Alignment check is actually *due* now by
PRD-230's own trigger — a phase boundary just closed.

**Can safely stay dormant:** macro (by ruling); PRD-268, PRD-209
(reopen-on-incident); PRD-275 (blocked on its own constraints); NEWS-1..3
(evidence-blocked); GEX-1/2 (pending the owner decision).

**Probably cut:** the standalone scheduler/freshness arc. All three lenses
converged: no mechanism exists in code ("Cloudflare is the clock" would be
new external infrastructure), no open incident motivates it, and PRD-250's
client-side staleness banner already solved the one real staleness incident
the repo has had. The honest reframe is doctrine G6 applied per-sidecar:
each new external sidecar (GEX, news) ships its own freshness/provenance
contract as part of its producer PRD. Revisit a shared clock only when ≥2
external sidecars exist and their contracts visibly duplicate. Also worth an
explicit cut ruling: the 2026-06-10 parked dashboard items, which predate
two generations of dashboard rethinking.

## 5. The PRD-289 operating-model lesson

**Why execution got fast:** the MATERIAL packet compiled every semantic
degree of freedom out of the work before implementation began — seven
verbatim vocabularies, an XOR carrier spec, twelve FAIL CONDITIONS, a 24-row
mutation matrix, exact FILES. Implementation became transcription with proof
obligations. This is workplan §11's own rule ("a lighter model… when the
approved PRD leaves no semantic choice") validated empirically.

**Where implementation-class execution (Ultracode) is right:** bounded
implementation against a review-clean packet; test and mutation-evidence
construction; mechanical reconciliation and closeout; recon fan-outs (with
*light* models — this session's second survey run, on lighter agents at low
effort, produced better-grounded evidence than the first attempt at a
fraction of the cost).

**Where exploratory/product reasoning stays mandatory:** packet and
vocabulary design; MATERIAL classification; registry *semantics* (what a
relationship means is a product question — the ratification hold is
correctly Dustin's); the Market Map narrowing adjudication;
evaluation-design (the descriptive/predictive boundary); and — pointedly —
**estimation**. Both ceiling breaches were design-stage failures (the
composer modeled as "thin plumbing" when the ratified design was a
validation surface), not implementation failures. The expensive-reasoning
budget should cover cost modeling of what the design mandates, not just the
design itself.

One operational honesty note from this pass: the first survey fan-out failed
wholesale on a harness fault (all 9 agents' tool calls rejected; ~500k
tokens burned) and was only diagnosable from transcripts. Multi-agent
orchestration adds real fragility — cheap environment probes before
fan-out, and lighter models for mechanical stages, are the fix, and both
were applied in the successful second run.

## 6. Recommended next 1–3 moves (for the follow-on synthesis to weigh)

1. **Ship Dustin the bounded GEX decision** (egress grant? fresh commission?
   §13e interpretation?) — it is the only thing standing between lane #2 and
   motion, and it's a decision, not a build.
2. **Open the registry lane as one reconciled deliverable** (registry =
   NEWS-0; seed from `watchlist_sidecar` + `config` + `market_map` lists;
   Dustin ratifies content) — the highest buildable leverage in the set.
3. **Use the card in anger, and let the observation window drive the Market
   Map narrowing decision** — plus the now-due Alignment check, folding in
   the three small drift fixes (GEX-0 wording in PROJECT_STATE, the stale
   next-check pointer, CB-27).

**Explicit uncertainties:** whether Polygon survives its licensing row;
whether NEWS-1 needs its own evidence pass beyond the registry (the workplan
implies yes, unconfirmed); whether the card actually changes in-session
behavior (the trap question — only observation answers it); the §13e
track-ended-vs-paused interpretation; and the imminent 2026-08-15
runtime/-debt re-evaluation, which nothing in the current lane order
accounts for.
