# Strategy Candidate-Fidelity Delta - 2026-07-31

```
STATUS: READ-ONLY RECONCILIATION DELTA
AUTHORIZES NO IMPLEMENTATION
```

Append-only delta to the 2026-07-30 current-state reconciliation (PR #175).
The four baseline artifacts in this directory are historical evidence and are
not modified by this delta. This file is the only addition.

---

## 1. Reviewed-state header

| Field | Value |
|---|---|
| Cuttingboard pin | `main` @ `68de7d02326d39ad92578a926d056db1e439ab55` (= `origin/main` after `git pull --ff-only`; working tree clean; zero open PRs at review time) |
| Baseline pin (PR #175) | `main` @ `9e6b772` - eight commits behind today's pin (`git rev-list 9e6b772..68de7d0`): `2751527` (#175, the baseline artifacts themselves), `ff8baca` (#177, PRD-272/273 closeout), `871ce90` (#174, PRD-273 limitation + PRD-274/275 scaffolds), `590dc75` (#178, PRD-276), `4b0f3ba` (#179, PRD-277), `28891d4` (#180, PRD-277 closeout), `ec8ee64` (#181, deny-list), `68de7d0` (#182, DECISIONS entry). No `cuttingboard/` production module changes in the range; it is audits/docs/settings plus the PRD-276/277 registry-validator change and its tests |
| Strategy pin | `origin/main` @ `1aefaaab53d907b5452939f4a26c5eb69aa45961` (merge of strategy PR #18, 2026-07-30). All strategy evidence was read via `git show <pin>:<path>`, never from the working tree (the local checkout sits on an unmerged docs branch, `934ae8b` = pin + one Section-j amendment) |
| Evidence paths (strategy) | `exploratory/cuttingboard-candidate-fidelity-v0_5/` (EXPLORATORY_CANDIDATE_FIDELITY_v0.5.md, CBF05_CHECKPOINT_POSTURE_PATCH_COMPARISON.md, README.md, scripts/, exports/, handoff/), `studies/cuttingboard-asis-proxy/` (README.md, LEDGER.csv, manifests/, analysis/, exports/, scripts/) |
| Hashes verified by this delta | v0.5 pine `3136a812c285878d416490f25dfbb62110fb39a863e47b34ef23b495d1b75726`; pre-patch export `e28aa87468d1922500b119bf02ded470c5528d327edf0bf09d2f124b1448ab8b`; post-patch export `2d375b4c1b60671012e834bd093057cdd0c964fee7a09c031e635c1eec5065e9`; AS-IS script `048f5c66eefa3fdb8df9cec882006b1d8cf5fc9772d8694614559ba0a1bce3b5` (recomputed; matches the frozen manifest's stated value exactly); AS-IS export `d1b537506ed1cec9559ad9dd66a35d4a9798d751ee1896e07e6e1739dfe0b970`. All recomputed with `sha256sum` over `git show` blobs at the strategy pin |
| Cuttingboard source pin named by the frozen manifest | `59f8279d796335149afdec4aa507b6f927233518` - verified: resolves in this repo (the Finding D ruling commit, PR #167) and is an ancestor of `main` |
| Tool / network provenance | Local `git` (read-only plumbing: `show`, `ls-tree`, `rev-parse`, `merge-base`, `cat-file`), `gh` (PR state reads against `dwats250/cuttingboard`), `sha256sum`, `awk` recomputation of every headline count. Network access: `git fetch` / `gh` against github.com only. No TradingView access; no chart was re-captured |
| Working-tree status | Authored in a dedicated worktree branched from `68de7d0`; only this file is added |
| Every funnel number below | Independently recomputed by this delta's lead from the pinned CSVs (column-level `awk` over the exported gate series), not transcribed from prose |

## 2. Executive conclusion

The Strategy repository's 2026-07-30 candidate-fidelity work changes nothing
in Cuttingboard and everything in how the Strategy proxy baseline may be
read. The posture-threshold "patch" (0.50 -> 0.55) corrects a Strategy-side
transcription defect: Cuttingboard code (`regime.py:331,336`) and docs
(`regime_model.md:99-102`) both require confidence >= 0.55 for any actionable
posture, and Gate 1 hard-rejects STAY_FLAT (`qualification.py:368-375`).
There is no Cuttingboard production defect and no documentation drift here.
The frozen AS-IS proxy baseline HAS been executed (registered 2026-07-30,
identity chain verified), but it implements only the 0.50 floor - the same
defect - so its registered counts (602 hard-pass / 170 QUALIFIED / 239
WATCHLIST) overcount what Cuttingboard semantics produce; the corrected
analog is 284 / 79 / 112 (recomputed here from the pinned post-patch export).
No PR #175 finding row changes status, severity, evidence, or ordering.
PRD-271 is untouched. The one genuinely new decision is Strategy-side: how
to disposition the defective frozen baseline.

## 3. Baseline relationship

The PR #175 baseline (CHARTER, EVIDENCE_INDEX, FINDING_STATUS_MATRIX,
RECONCILIATION_REPORT) used the strategy repository only as evidence for
CB-29 (the missing cross-repository pointer). Its four artifacts contain
zero references to `cuttingboard-candidate-fidelity-v0_5` or
`cuttingboard-asis-proxy` (verified by sweep; the single grep hit for
"asis" is the word "basis"). The entire candidate-fidelity evidence body is
therefore OUTSIDE the baseline's reconciled scope - not a correction to it -
even though the material existed at the baseline's strategy pin (`934ae8b`).

Effect on baseline rows:

- **No row changes status, severity, evidence, or ordering.** Specifically:
  CB-01, CB-02, CB-03, CB-04, CB-05, CB-06, CB-07, CB-08, CB-10, CB-11,
  CB-12, CB-12b, and every Medium/Low/UNKNOWN row are untouched by the
  Strategy evidence. The proxy explicitly does not represent Gate 8, Gate
  11, chain validation, or the decision chain, so it cannot bear on the
  rows that live there.
- **CB-30 (UNKNOWN, "Gate 9 cannot fail")** gains consistent context only:
  the proxy models g9 as fail-open "by construction", matching
  `qualification.py:501-504` and `docs/trade_qualification.md:209`. CB-30
  stays UNKNOWN; this delta did not run it to ground.
- Two baseline citations are stale for lifecycle reasons unrelated to the
  Strategy evidence, recorded here for the reader, statuses unchanged:
  CB-12's "PR #174 (OPEN, not production)" - PR #174 MERGED 2026-07-31T05:50Z
  (`871ce90`), landing only the PRD-275 Stage-0 scaffold, which DECISIONS
  2026-07-26 blocks behind six named constraints; and CB-28's specifics -
  `docs/PROJECT_STATE.md` was rewritten 2026-07-31 (baseline described the
  2026-07-26 version). CB-28's shape (an "Active PRD: none" line against
  four registry IN PROGRESS rows: 268, 271, 274, 275) persists.
- All other untouched rows remain exactly as the baseline states them.

## 4. Claim matrix

One material claim per row. Evidence column cites what this delta's lead
verified personally; every number was recomputed from the pinned artifacts.

| # | Claim | Evidence | Authority | Disposition | Decision impact |
|---|---|---|---|---|---|
| 1 | The v0.5 proxy's original posture gate (`posturePass = confidence >= 0.50`) was too permissive relative to Cuttingboard; the patch to `>= 0.55` aligns it with Cuttingboard | Committed v0.5 pine line 113 reads `>= 0.50` (hash-verified); Cuttingboard `regime.py:325-338` (actionable posture requires `>= 0.55`; 0.50-0.55 band is STAY_FLAT), `qualification.py:368-375` (Gate 1 hard-rejects STAY_FLAT) | Cuttingboard code at `68de7d0` | PROXY DEFECT ONLY | None for Cuttingboard code. Strategy-side records affected (rows 5-6) |
| 2 | Cuttingboard's 0.55 actionable-posture boundary is documented, implemented policy, not drift | `docs/regime_model.md:99-102`, `docs/runbook.md:40-41` state 0.55; `regime.py:331,336` implements it; `config.py:62` `MIN_REGIME_CONFIDENCE = 0.50` is a separate global floor, also correctly documented | Cuttingboard code + docs at `68de7d0` | INTENTIONAL CUTTINGBOARD POLICY | None. No doc fix owed on this threshold |
| 3 | The pre/post-patch funnel contrast (V2 602->284, V4 170->79, selected 118->62) isolates exactly the confidence == 0.50 bars | Recomputed from both pinned exports: all values reproduce; all 318 dropped V2 rows carry exported confidence exactly 0.50 (join on bar time). On the 8-vote lattice, [0.50, 0.55) contains only 0.50 (= abs(bounded_net) 4) | Pinned exports `e28aa874` / `2d375b4c`; `regime.py:206` (confidence = abs(bounded_net)/8) | CONFIRMED SUPPORTING EVIDENCE | Quantifies row 1's defect; establishes no Cuttingboard behavior |
| 4 | The frozen AS-IS proxy baseline has been executed under its pinned manifest | Manifest FROZEN, captured 2026-07-30 05:42 UTC; script SHA re-verified (recomputed = manifest value); export SHA `d1b53750` recomputed; LEDGER row 1; capture screenshot; declared-window counts recomputed from the export: 2,909 bars, 170 QUALIFIED, 239 WATCHLIST, 204 kill-switch | Strategy pin `1aefaaa`; manifest `RUN_SPY_1D_2015-01-01.md` + 2026-07-30 amendment | CONFIRMED NEW FINDING | Q6 answered: executed. See row 5 for what its output may not be read as |
| 5 | The frozen AS-IS proxy carries the same posture transcription defect: floor-only (0.50), no 0.55 tier; its in-script comment ("the finer posture tiers do not change any gate the proxy evaluates") is false against production | AS-IS pine lines 32, 96-99 (floor only); v0.5 zero-disagreement row-level comparison (2,908 common bars) against the PRE-patch export proves both encode 0.50; production trace (rows 1-2) proves the tier binds; corrected analog recomputed: V2 284, QUALIFIED-analog 79, one-miss band 112 | Strategy pin; Cuttingboard code at `68de7d0` | PROXY DEFECT ONLY | The registered 602/170/239 counts may NOT be read as an AS-IS description of Cuttingboard behavior. Dustin decision D2 (section 9) |
| 6 | The faithful (tier-complete) AS-IS proxy QUALIFIED / WATCHLIST / REJECT counts are not established by any registered run | The only registered run embeds the floor-only defect (row 5); the post-patch v0.5 export gives corrected analogs (284/79/112) but represents just two soft gates, and its generating script is not in the repository (row 9) | Strategy pin | UNRESOLVED PENDING FROZEN RUN | A corrected frozen re-run is the only path to faithful counts, if Dustin wants them (decision D2) |
| 7 | v0.5's strict requirement that both represented soft gates pass conflicts with neither Cuttingboard documented nor implemented semantics; it describes the qualified-setup layer | `docs/trade_qualification.md:5-11` and `qualification.py:536-581`: zero soft misses = qualified, exactly one = WATCHLIST, two+ = REJECT. "Both represented gates pass" = zero misses within the represented subset. The v0.5 doc itself concedes it "under-surfaces the broader CuttingBoard attention stream" | Cuttingboard code + docs at `68de7d0` | INTENTIONAL CUTTINGBOARD POLICY | None. The frozen AS-IS proxy already implements the count-based rule correctly (pine line 168-171) |
| 8 | The 239 non-kill bars missing exactly one represented soft gate are WATCHLIST-layer analogs, not suppressed entries - and the count is pre-patch | Recomputed: 239 on the pre-patch export; 112 on the post-patch export (a number stated in no Strategy document - computed by this delta); both subject to the unrepresented gates (g8, g11) and to gates the proxy approximates | Pinned exports; `qualification.py:551-565` | CONFIRMED SUPPORTING EVIDENCE | Sizes the attention-stream layer only. No Cuttingboard consequence |
| 9 | The post-patch evidence has an identity gap: no committed script produces the `2d375b4c` export | The only committed v0.5 pine is pre-patch (`>= 0.50`, hash matches the packet's pinned SHA); the checkpoint doc says the corrected script is operator-held with SHA "still belong[ing] in a future run record" | Strategy pin | CONFIRMED NEW FINDING | Post-patch numbers rest on a hashed CSV plus prose about its generator. Cure rides decision D2's dated correction |
| 10 | Strategy-side record hygiene is inconsistent at the pin | `studies/cuttingboard-asis-proxy/exports/README.md` still reads "Empty: no run has been executed" beside the registered export; the run-count amendment (3,619 -> 3,620, a `wc -l` trailing-newline defect) is recorded only in the dated amendment; classification counts verified unaffected | Strategy pin | CONFIRMED SUPPORTING EVIDENCE | Folded into decision D2's dated correction; nothing for Cuttingboard |
| 11 | Gate-structure results (g7-fail == NEUTRAL regime on all rows; direction gate binds, falsifying the strategy matrix's Q-03 "CURRENTLY_INERT"; g5 tautological) | `ANALYSIS_GATE_STRUCTURE_2026-07-30.md`; the g7 identity is proxy-construction-specific (R:R fixed at 2.0 by construction; production R:R varies with real geometry) | Strategy pin | OUT OF SCOPE | Strategy-internal translation-matrix corrections (Q-03 already amended at `617978d`). No Cuttingboard row exists for these and none is created |
| 12 | The 52 bars "blocked only by an open simulated position" and all Strategy Tester execution artifacts are TradingView simulation mechanics | v0.5 doc: "Strategy Tester execution artifacts do not equal candidate counts" | Strategy pin | OUT OF SCOPE | Not a Cuttingboard layer; carries no evidence weight here |

## 5. Funnel comparison (before/after, layers kept separate)

All counts recomputed from the pinned exports, evaluation window 2015-01-01+.

| Layer (proxy vocabulary) | Pre-patch (0.50) | Post-patch (0.55) | What the layer is - and is not |
|---|---:|---:|---|
| V2 structure-qualified bars | 602 | 284 | Candidate OCCURRENCE in the proxy after regime/posture/structure. Not a Cuttingboard candidate record |
| V4 (both represented soft gates pass, kill-switch excluded) | 170 | 79 | The proxy analog of a qualified setup within the two-gate represented subset. Not WATCHLIST eligibility, not a TRADE decision |
| Selected simulated entry attempts | 118 | 62 | TradingView strategy-engine entries (blocked-position mechanics included). Not Cuttingboard selected entries, not executed trades, not options executions |
| One-miss non-kill band (WATCHLIST analog) | 239 | 112 | Attention-stream sizing only; the 112 is computed by this delta, stated in no Strategy document |
| Both-miss non-kill band | 170 | 82 | REJECT analog. The pre-patch equality with V4 (170) is coincidence, not identity |

The entire before/after delta at every layer consists of bars whose exported
confidence is exactly 0.50 (verified row-level: 318 of 318 dropped V2 bars).
The contrast therefore establishes one thing: the 0.55 actionable-posture
tier binds massively on SPY daily history, so a posture translation that
omits it inflates every downstream layer roughly 2x. It establishes nothing
about Cuttingboard profitability, expectancy, WATCHLIST behavior on live
runs, or any executed trade.

## 6. Soft-gate semantics trace

- **Documented intent (Cuttingboard):** `docs/trade_qualification.md:5-11` -
  gates 1-4 hard (immediate reject, no watchlist); gates 5-11 soft; exactly
  one soft miss -> WATCHLIST; two or more -> REJECT. Posture tiers:
  `docs/regime_model.md:99-102` (0.55 boundary; below it STAY_FLAT).
- **Implemented behavior (Cuttingboard, verified at `68de7d0`):**
  `qualification.py:536-581` implements exactly the 0 / 1 / 2+ rule;
  `regime.py:319-347` implements the 0.50 global floor plus the 0.55
  actionable tier; `qualification.py:368-375` makes STAY_FLAT a Gate 1 hard
  reject. Docs and code agree.
- **Exploratory v0.5 proxy behavior:** strict AND over its two represented
  soft gates (`directRiskPass = stopDistancePass and notExtended`) - a
  deliberate strict funnel, self-documented as under-surfacing the
  WATCHLIST band; posture floor-only at 0.50 pre-patch, 0.55 post-patch.
- **Frozen AS-IS proxy behavior:** count-based 0 / 1 / 2+ over the five
  representable soft gates (pine lines 168-171) - correct against
  Cuttingboard semantics; posture floor-only at 0.50 - incorrect against
  Cuttingboard semantics, with an in-script comment asserting the tiers do
  not matter.
- **Exact confirmed mismatch:** one, in the posture dimension, in both
  proxy scripts as committed: the 0.55 actionable tier is missing. The
  soft-gate combination rule itself mismatches only in v0.5 (strict AND vs
  count), and that divergence is declared inside the v0.5 record, not
  discovered by this delta.

## 7. Frozen AS-IS proxy status

**EXECUTED.** Evidence: frozen manifest `RUN_SPY_1D_2015-01-01.md`
(captured 2026-07-30, operator dwats250, TradingView Premium, AMEX:SPY 1D
RTH, adjustment convention recorded), dated amendment (row-count correction
3,619 -> 3,620), LEDGER.csv row 1, export
`CBASIS_v0_1_AMEX_SPY_1D_RTH_20150101-20260729_048f5c66.csv` (SHA
recomputed, counts recomputed: 2,909 declared-window bars, 602 hard-gate
pass, 170 QUALIFIED (125L/45S), 239 WATCHLIST, 204 kill-switch), capture
screenshot, published findings, and a published gate-structure analysis
with pre-registered hypotheses.

**Remaining gate:** the registered run is not a faithful AS-IS baseline in
the posture dimension (claim rows 5-6). What remains blocked is not the
run - it is any use of its QUALIFIED / WATCHLIST / REJECT counts as
Cuttingboard-semantics description, pending either a Strategy-side dated
correction that re-scopes the run, or a corrected frozen re-run. Standing
representation limits declared by the manifest remain in force: g8 and g11
NOT REPRESENTABLE; EXPANSION / CONTINUATION / PULLBACK_IMBALANCE not
represented; chain validation and the decision chain absent (the accepted
path is unobservable, as in the closed audit).

## 8. Current Cuttingboard queue (verified 2026-07-31)

- Zero open PRs. `main` = `origin/main` = `68de7d0`. PR #175 (baseline),
  #174 (PRD-273 limitation + PRD-274/275 scaffolds), #180 (PRD-277
  closeout), #181/#182 (deny-list arc) all MERGED.
- Registry IN PROGRESS rows: PRD-268 (hourly coverage-reason scaffold,
  design fork unruled, HIGH-RISK), PRD-271 (ORB, Gate A pending), PRD-274
  (ruff-baseline coverage, queued), PRD-275 (review-artifact enforcement,
  blocked by the six DECISIONS 2026-07-26 constraints).
- `prd_index.json`: `next_prd` 278, `latest_complete` 277.
- PR #175's recommended commission ordering (CB-02 first) stands unchanged
  by this delta.

## 9. Dustin decisions

Only genuinely new decisions are listed. Standing held decisions (PRD-271
Gate A, CB-02 implementation authorization, PRD-268 design fork, PRD-275
constraints) are unchanged and not re-argued here.

- **D1 - Accept this delta.** Merge the draft PR carrying this artifact.
  Recommended ruling: merge. Consequence: the reconciliation directory
  gains its strategy-evidence delta; nothing else changes; no
  implementation is authorized.
- **D2 - Disposition of the defective frozen AS-IS baseline
  (Strategy-side).** The registered run's counts embed the floor-only
  posture defect. Recommended ruling: commission a dated Strategy-side
  correction record that (a) re-scopes RUN_SPY_1D_2015-01-01 as
  floor-only-posture evidence, (b) fixes the stale `exports/README.md`,
  and (c) pins the post-patch v0.5 script hash or declares it
  unrecoverable; decide separately - and without time pressure - whether a
  tier-complete frozen re-run is worth a TradingView session. Consequence
  if unruled: the 170/239 counts sit in the strategy repo labeled as an
  executed AS-IS baseline while overstating the Cuttingboard-semantics
  funnel roughly 2x, available to be cited incorrectly by any future
  packet.

## 10. Single next packet

**Strategy-side dated correction of the AS-IS baseline records** (decision
D2's recommended ruling, executed in `dwats250/strategy`).

- Purpose: one dated amendment re-scoping the registered run as floor-only
  posture evidence, citing the posture-tier trace and the recomputed
  corrected analogs (284 / 79 / 112), correcting the stale exports README,
  and closing the post-patch script identity gap.
- Mutation permission: strategy repo documentation only, via that repo's
  dated-amendment convention; no script edit, no export edit, no re-run.
- Entry condition: Dustin approves D2.
- Exit condition: the amendment is committed in the strategy repo and
  referenced from the study README.
- Does NOT authorize: any Cuttingboard change, any threshold change, any
  tuning, any re-run, any parity or profitability claim.

## 11. What was not checked

- No TradingView capture was reproduced; chart-side settings are taken
  from the frozen manifest's own declarations.
- The post-patch export's generating script is not in the repository; the
  0.55 attribution rests on the checkpoint document plus this delta's
  row-level recomputation showing the delta population is exactly the
  confidence-0.50 bars.
- BATS vs NYSE Arca feed differences beyond the registered row-level join
  were not examined.
- The strategy repo's unmerged branch commit (`934ae8b`, Section-j
  amendment) and its connector state were not evaluated.
- The closed engine audit (`EA-*`) artifacts were consulted only where the
  fidelity packet cites them for identity; the audit itself was not
  re-opened.
- CB-30 through CB-47 were not run to ground; CB-30 gains context only.
- No Cuttingboard test was executed; this delta changes no code and relies
  on reading, tracing, and recomputation.
