# Reconciliation Report — 2026-07-30

```
STATUS: READ-ONLY RECONCILIATION
AUTHORIZES NO IMPLEMENTATION
```

**Production pin:** `dwats250/cuttingboard` `main` @ `9e6b772`
**Companions:** `CHARTER.md`, `FINDING_STATUS_MATRIX.md`, `EVIDENCE_INDEX.md`

Recommendations in this document are proposals. They authorize nothing.

---

## 1. Confirmed open Critical findings

Two. Both were re-verified by the lead directly against current code.

**CB-01 — The hourly channel never evaluates the kill switch, and publishes
`kill_switch: False` as a literal.** `_kill_switch` has exactly two call sites,
both on the daily path. `_build_hourly_run_summary` and `_failure_summary` write
the literal. On an intraday volatility spike the hourly Telegram alert keeps
presenting qualified candidates while the daily pipeline would HALT — and the
published summary affirmatively reports the safety indicator as clear.
`VISION.md` names extreme stress a hard invalidation; it is enforced on one of
two live channels. **Planned as "PRD-253"; that number landed unrelated work.
No PRD carries this.**

**CB-02 — The one-contract floor emits positions that breach the
correlation-adjusted risk budget.** `options.py:228-236` floors at one contract
after applying the correlation modifier, with no refusal branch. On the
**default** NEUTRAL correlation state (0.7), an index-ETF credit spread emits
one contract at $350 against a $280 budget — a **1.25× breach**. At CONFLICT
(0.4) it is **2.19×**. The correlation modifier's entire risk reduction is
nullified, silently: `dollar_risk` prints the true $350, and nothing says it
exceeds the budget the system just computed. **Dustin already ruled this
(2026-07-24): "refuse the trade." The same entry records NOT IMPLEMENTED.**

This finding appears in no version of the audit ledger. It reached an owner
ruling without ever reaching `audits/FINDINGS.md`.

## 2. Confirmed open High findings

Nine, ordered by present user impact.

1. **CB-04 — Trade brakes count recommendations as fills.** Not theoretical:
   in the published history, `cooldown` blocked 5 qualified candidates against
   only 6 ALLOW_TRADE decisions ever, and **every block occurred in the same run
   as its ALLOW**. On 2026-06-30 a single SPY recommendation suppressed QQQ, IWM
   and NVDA from the trader's view.
2. **CB-03 — The policy size multiplier never resizes anything.** A decision to
   halve size is displayed and exported as full size. `size_rounds_to_zero`, the
   operator-settled block reason, does not exist in the codebase.
3. **CB-07 — The opening range is computed from mid-session bars** and gates a
   live BLOCK_TRADE decision. PRD-271 merged as a Stage-0 scaffold containing no
   fix.
4. **CB-05 — Macro-pressure failure fails open** to "unconstrained, full size,"
   with only a log warning. Computed-UNKNOWN and failed-to-compute are
   indistinguishable downstream.
5. **CB-10 — The canonical qualification document states a $150 budget; the code
   uses $400.** Anyone sizing by hand from the document sizes at 37.5 % of the
   real budget.
6. **CB-06 — The hourly channel cannot fail visibly.** The runner's own docstring
   says it converts all failures to exit 0; readiness checks key presence, not
   status.
7. **CB-08 — Spread economics are a 30 %-of-width estimate**, never live chain
   pricing. This is the residual of finding A1, not a restatement of it.
8. **CB-09 — Load-bearing artifacts are written non-atomically**; a torn
   `market_map.json` wedges every later daily run until a human clears it.
9. **CB-11 — `system_candidate_id`, the intended join key, is never emitted.**
   The keystone of the measurement loop `VISION.md` names as the central risk.

## 3. Partial Critical or High findings

**CB-12 — HIGH-RISK gate (High, held).** PRD-269 genuinely closed the doc-status
blind spot. It did **not** close F-04's four bypasses: the lane regex still lacks
`re.IGNORECASE`, docless COMPLETE rows still `continue`, the declared lane is
still unchecked against the change surface, and the artifact leg still tests file
existence and filename rather than content — an empty file passes. No test covers
the casing bypass. Mitigated in practice by GOV-1's universal manual merge.

**CB-12b — Manual-merge backstops (Medium, reassessed down from High).** The
GitHub-settings leg closed (`enforce_admins` true since 2026-07-19). CODEOWNERS
and the CI changed-path check remain absent. Severity drops because the finding's
premise — unbabysat agent merging — is superseded by GOV-1 plus a `gh pr merge`
deny rule.

## 4. Unknown findings with plausible Critical or High consequences

**CB-30** is the one `UNKNOWN` row, and it is deliberately broad: roughly nineteen
historical mediums and lows (F-09 through F-23 plus three Codex-miss items) were
**not investigated this pass**. Pass 1 triage placed them below the Critical/High
verification budget and no lane was asked to run them to ground.

Two of them carry plausible High consequences and are named here so they are not
lost in the aggregate: **F-14** (terminal-state truth derived twice in parallel,
with `verify` checking the summary against itself) and **F-18** (adjusted OHLCV
history mixed with unadjusted live quotes inside threshold-gate arithmetic — the
historical ledger already marked its materiality `[2L]`, needs-a-second-look).

`UNKNOWN` here means their historical text is on record and their current truth is
not. One targeted sweep per item, of the kind run for CB-01…CB-15, would resolve
them.

## 5. Fixed findings

Three, each with current merged code **and** a discriminating regression test the
lead read directly.

- **CB-13 — Credit-spread max risk (was CRITICAL).** `_max_loss_for_strategy`
  returns width-minus-credit. The test sets `candidate.max_loss = 999.0`
  deliberately wrong and asserts the recomputed figure — it goes red on revert.
  Notably, its own comment records that the *neighbouring* test could not
  discriminate because its fixture happened to already equal the right answer.
  The repo found and closed its own non-discriminating-fixture hole; that is the
  standard this reconciliation applied everywhere.
- **CB-14 — Fabricated `pct_change = 0.0` (was HIGH, Tier-1 root cause).** Now
  raises; two discriminating tests, one parametrised over the invalid values.
- **CB-15 — Regime confidence inflation on dropout (was HIGH).** Worst-case
  bounding over a fixed 8-vote denominator, with a named test and an exhaustive
  3^8 × 3 proof. Disclosed limit: the 247-day replay contained zero partial-vote
  days, so synthetic tests remain the only dropout evidence.

## 6. Superseded findings

**None.**

This is a deliberate result, not an oversight. Several findings have had their
*premise* shift — CB-12b's merge-authority premise is superseded by GOV-1, and
`RECONCILED_FINDINGS.md` records that C1 invalidates F-23's Sunday-halt claim and
that F-21 was reclassified from parasitic-state to docs-drift. But in each case
either a material residual remains (so `PARTIAL` is the honest status) or the
supersession is asserted by a historical document rather than verified at HEAD by
this pass (so it belongs in `UNKNOWN`, not `SUPERSEDED`).

Classifying a finding `SUPERSEDED` on the authority of the same historical ledger
this reconciliation exists to re-verify would defeat the exercise.

## 7. Medium and low debt

Nine Medium: CB-16 (sidecar doctrine self-contradiction — a doctrine ruling, not
code), CB-18 (freshness measures fetch time), CB-19 (no run is reproducible),
CB-20 (manual journal has no entry point; review scorecard therefore dead),
CB-21 (evaluation/performance artifacts never written), CB-22 (`_MIN_SAMPLE = 5`,
symbol-only bucketing), CB-23 (only ALLOW_TRADE candidates evaluated forward),
CB-24 (78-bar underlying window evaluating 14–21 DTE spreads), CB-25 (gate
vectors, `stay_flat_reason`, `excluded_symbols` structure discarded).

Five Low: CB-17 (raw `net_score` readers — unreachable), CB-26 (no stable
`run_id`), CB-27 (four remaining doc drifts plus three pipeline numberings),
CB-28 (`PROJECT_STATE.md` stale at HEAD), CB-29 (no reciprocal pointer to the
external audit relationship).

CB-20 through CB-25 form one cluster with one shape: **the system records what it
said and never records what was done or what happened.** They are listed as six
rows because they are six separable decisions, not because they are six problems.

## 8. Contradictions between current code, tests, PRDs, and canonical documentation

**8.1 Lane disagreements resolved by the lead.**

| Question | Lane 1 | Lane 2 | Lead resolution |
|---|---|---|---|
| A2 / size multiplier | `FIXED (BY DESIGN)`, citing PRD-073 | `OPEN` | **`OPEN`.** Lane 1 misread a renderer-boundary rule. PRD-073:56's "UI PATH ONLY" sits inside a `RULE — FIELD AVAILABILITY` block whose FILES are the dashboard renderer and `ui/*`; it constrains which data source the *server renderer* may read. It says nothing about sizing. Operator decision 2 (2026-07-10) settled the opposite. |
| A1b / chain pricing | `OPEN` | `SUPERSEDED` by PRD-256 | **`OPEN` (as CB-08).** PRD-256 delivered continuation-path ATR-proxy bounding — a different concern, correctly COMPLETE for that concern. Chain validation still selects one near-ATM contract; `net_credit` / `net_debit` do not occur in the file. |
| F-04 / HIGH-RISK gate | not assigned | `FIXED` via PRD-242 + PRD-269 | **`PARTIAL` (CB-12).** PRD-269 closed the doc-status leg only. The regex still lacks `IGNORECASE`; the artifact leg still never reads contents. |
| net_score divergence | not assigned | Lane 4: `OPEN`, **High** | **`OPEN`, Low (CB-17).** The only decision-bearing raw reader is `direction_for_regime`'s NEUTRAL branch, and NEUTRAL always forces STAY_FLAT via the confidence floor, which Gate 1 short-circuits. `tests/test_regime.py:285-292` already documents this unreachability. |

**8.2 The PRD-number drift is systemic, not incidental.**
`BUILD_PLAN.md` assigned tentative numbers 251–260. The plan itself already
recorded the drift for Wave 3. Reconciled at HEAD, the drift is wider:

| Planned | Substance | What the number actually landed | Substance status |
|---|---|---|---|
| PRD-251 | A1a credit-spread arithmetic | same | **FIXED** |
| PRD-252 | F-02 pct_change | budget cap raise (F-02 landed as **PRD-262**) | **FIXED** |
| PRD-253 | F-01 hourly kill switch | contract/audit sizing sourcing | **OPEN** — never landed |
| PRD-254 | A2 size multiplier | hook + settings hardening | **OPEN** — never landed |
| PRD-255 | A3 trade brakes | `prd-review-claude` spec | **OPEN** — never landed |
| PRD-256 | A1b both-leg chain pricing | continuation-path ATR proxy | **OPEN** — different concern landed |
| PRD-257 | F-04 gate hardening | `dashboard_preview.yml` comment fix | **PARTIAL** — via 242 + 269 |
| PRD-258 | F-05 backstops | **widened** the Bash allow-list | **PARTIAL** — settings leg only |
| PRD-259 | F-08 hourly fail-loud | continuation HOLD gate | **OPEN** — never landed |
| PRD-260 | F-07 macro-pressure | continuation decision geometry | **OPEN** — never landed |

Five of Wave 1–4's eight planned safety items never landed under any number.
The asymmetry `BUILD_PLAN` flagged for PRD-258 — "the loosening shipped; the
tightening did not" — turns out to describe the whole sequence.

**8.3 Documentation contradicting code.** CB-10 (qualification doc's $150 vs the
code's $400) and CB-27's four remaining items. Each is a live instance of the
`VISION.md` docs-match-code principle failing in the direction the principle was
written to prevent.

**8.4 `PROJECT_STATE.md` contradicting the registry and the git log.** CB-28.

**8.5 A test comment carrying load-bearing knowledge no document holds.**
`tests/test_regime.py:285-292` is the only place in the repository that records
that `NEUTRAL_PREMIUM` is unreachable and deliberately parked. The lead derived
that unreachability independently and then found it already documented — in a
test comment. It is correct, and it is the sole record.

## 9. Recommended next commissions

Proposals only. Ordered by present user impact and dependency. **Nothing here is
an authorization.**

1. **CB-02** — the ruling already exists; only implementation authority is
   withheld. It breaches a risk limit on the default correlation state.
2. **CB-01** — a live safety surface is both bypassed and misreported.
3. **CB-10** — a documentation edit, and the cheapest item that removes a live
   sizing hazard.
4. **CB-04** and **CB-03** together — both are execution-policy materialization,
   both have settled operator doctrine from 2026-07-10, and CB-04's fixtures
   should be written against dormant state so CB-03 does not churn them. This
   pairing is `BUILD_PLAN`'s own interaction flag 5.
5. **CB-07** — PRD-271's Gate A is already the named seam.
6. **CB-05**, then **CB-06** — both fail-open, hourly-adjacent.
7. **CB-11** — cheap, and every day it is absent is a day of unrecoverable data.
   The External Context Brief's strongest argument, and the reconciliation finds
   nothing contradicting it.
8. **CB-30** — a triage sweep to convert the nineteen items behind that single
   `UNKNOWN` row into individual statuses.

## 10. Explicitly deferred

- **CB-30's nineteen items** — not investigated; see § 4.
- **CB-16** — needs a doctrine ruling before any code, and the ruling shapes how
  CB-05's fix would be worded.
- **CB-09's dropped scope** — the cross-workflow-concurrency portion and the
  impossible line citation are **wrong and must not be built**.
- **CB-22's statistical thresholds** — the sample-size arithmetic is the External
  Context Brief's, recomputed by its author. This reconciliation did not
  re-derive it and does not certify it.
- **Live-fire verification of CB-01, CB-05, CB-07** — how often each has actually
  changed an outcome is unestablished, because none of the three persists the
  evidence that would answer it.

## 11. Items that should NOT be commissioned

- **Anything that ports deflated Sharpe, PBO/CSCV, or walk-forward machinery into
  CuttingBoard.** `VISION.md:39-42` lists backtesting as a non-goal; the boundary
  has held since 2026-05-22. The External Context Brief reaches the same
  conclusion and states it as its own headline finding.
- **CB-09's separate-runner concurrency work** — built on a premise already
  refuted at reconcile.
- **Another round of Bash deny-pattern spellings** — `docs/DECISIONS.md`
  (2026-07-18) rules the default disposition DISMISSED, citing that a finite
  string-match list cannot enumerate an open-ended spelling space.
- **Analytics over the existing evaluation output.** CB-21 through CB-24 mean
  there is nothing sound to compute over yet; adding statistics before the inputs
  exist makes the `VISION.md` trap worse, not better.
- **Correcting the documentation drift found in § 8.3 as part of THIS
  initiative.** It is recorded, deliberately unfixed, per the charter.

---

## 12. Lead re-verification record

Independently rerun by the Opus lead, not accepted from any subagent:

- Every `_kill_switch` call site, and the enclosing function of both
  `"kill_switch": False` literals (CB-01).
- The full Gate 8 → correlation-modifier → `max(1, ...)` floor trace, with the
  breach computed from current constants (CB-02).
- Every `size_multiplier` reference in `cuttingboard/`, and the repo-wide
  `size_rounds_to_zero` search (CB-03).
- Aggregation of `origin/publish:logs/audit.jsonl` — record counts, outcome
  distribution, block-reason distribution — and the run-by-run trace tying each
  cooldown block to a same-run ALLOW (CB-04).
- `_compute_overall_pressure`'s exception path and `_apply_macro_pressure`'s
  UNKNOWN branch (CB-05).
- `alert_runner`'s exit paths and `check_readiness`'s key tuples (CB-06).
- `chain_validation.py`'s contract surface and the absence of both-leg pricing
  (CB-08).
- Occurrence-by-occurrence reading of every `0.01` and `$150` in
  `docs/trade_qualification.md`, separating the three stale sites from the three
  correct ones (CB-10).
- The validator's lane regex, all three `not doc.exists()` sites, and the
  `has_artifact` computation (CB-12).
- `_max_loss_for_strategy`'s body and the source of the discriminating test,
  including why the neighbouring test does not count (CB-13).
- The `previous_close` raise site and both discriminating tests (CB-14).
- The bounding arithmetic and the named quorum-floor test (CB-15).
- The full unreachability chain for `direction_for_regime`'s NEUTRAL branch,
  derived before finding the repo had documented it (CB-17).
- PRD-073's "UI PATH ONLY" in its surrounding `RULE — FIELD AVAILABILITY` block
  and its FILES list, to resolve the A2 disagreement.
- Merge state of PR #174 (open), #173 (merged, scaffold-only), #168 (closed
  unmerged).
- Repository topology (`gh repo view`, full `dwats250` repo list) to settle
  whether a separate development fork exists.

`docs/SCHEMA_MAP.md` and `docs/CALL_SITE_MAP.md` were consulted before grepping,
per `CLAUDE.md`. Six spot-checked entries all resolve correctly at HEAD.

## 13. What this reconciliation did not do

It modified no production source, no test, no contract, no schema, and no
canonical document. It allocated no PRD number, opened no issue, changed no
threshold, and created no implementation plan. It did not correct any of the
documentation drift it recorded. It invoked neither Fable 5 nor Codex.

The four files in this directory are its entire output.
