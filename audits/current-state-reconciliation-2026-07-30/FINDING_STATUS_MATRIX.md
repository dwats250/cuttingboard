# Finding Status Matrix — 2026-07-30

```
STATUS: READ-ONLY RECONCILIATION
AUTHORIZES NO IMPLEMENTATION
```

**Production pin:** `dwats250/cuttingboard` `main` @ `9e6b772`
**Charter:** `CHARTER.md` · **Evidence:** `EVIDENCE_INDEX.md` · **Report:** `RECONCILIATION_REPORT.md`

One concern per row. Every row carries exactly one status. Severity is reassessed
from present consequences, not inherited. "Existing work" records what touched the
concern; it never implies closure.

---

## OPEN — CRITICAL

### CB-01 · Hourly alert channel never evaluates the kill switch and publishes `kill_switch: False` as a literal

| Field | Value |
|---|---|
| **Original source** | `audits/FINDINGS.md` F-01 (2026-07-09, Critical); `audits/RECONCILED_FINDINGS.md` Tier 2 |
| **Exact claim** | The hourly notification path runs fetch → regime → candidates → qualify and emits candidate lines to Telegram with no market-stress evaluation, then writes `"kill_switch": False` as a hardcoded literal into its published summary. |
| **Current status** | **`OPEN`** |
| **Current evidence** | `_kill_switch` has exactly three occurrences in `cuttingboard/runtime/__init__.py`: its definition at `:2194` and two call sites, `:937` (inside `_run_pipeline`, the DAILY path) and `:1256` (inside `_build_run_summary`, the daily summary). `_build_hourly_run_summary` (defined `:1903`) writes the literal at `:1975`. `_failure_summary` (defined `:2335`) writes the same literal at `:2366`. No hourly call site exists. |
| **Production applicability** | Merged production. Both literal sites are on `main` @ `9e6b772`. The hourly workflow runs on schedule — most recent hourly execution 2026-07-30T16:20Z. |
| **User-visible consequence** | On an intraday volatility spike that passes validation, the hourly Telegram alert keeps presenting qualified candidates with R:R lines while the daily pipeline would HALT. The published summary affirmatively reports the safety indicator as clear. The dashboard renders that literal as a safety state. `VISION.md:30-34` names extreme stress "a hard invalidation"; it is enforced on one of two live channels. |
| **Current severity** | **Critical** — bypasses a live safety/invalidation surface AND misstates it as clear. |
| **Existing work** | Planned as BUILD_PLAN "PRD-253". That number landed unrelated work (contract/audit sizing sourcing). No PRD carries F-01's substance. |
| **Missing proof** | None for the defect. Not established: how often an hourly run has coincided with a kill-switch condition (no durable per-run kill-switch evidence on the hourly path — the field is a literal, so history cannot answer it). |
| **Next authority** | Dustin decision. |
| **Residual limitation** | n/a — original defect intact. |
| **Confidence** | **High** — lead reran the exhaustive `_kill_switch` call-site grep and resolved the enclosing function of both literals by line. |

---

### CB-02 · The one-contract floor emits a position whose max loss exceeds the correlation-adjusted risk budget

| Field | Value |
|---|---|
| **Original source** | `docs/prd_history/PRD-259.first-fire-consumers.proposal.md` "Finding D" (2026-07-14, commissioned second-model disposition). **Never entered `audits/FINDINGS.md` or `RECONCILED_FINDINGS.md`.** |
| **Exact claim** | `options.py`'s `max(1, ...)` sizes one contract even when that contract's strategy max loss exceeds `ACCOUNT_EQUITY × MAX_RISK_PCT_PER_TRADE × risk_modifier`. |
| **Current status** | **`OPEN`** |
| **Current evidence** | `cuttingboard/options.py:228-236`. `raw_adjusted = int(effective_risk // risk_per_contract)`; when `risk_per_contract > effective_risk` this is `0`, and `final_contracts = max(1, min(result.max_contracts, raw_adjusted))` yields `1`. `final_dollar_risk` is then one full `risk_per_contract`. Gate 8 (`qualification.py:464-492`) sizes against the REGIME multiplier only and correctly refuses at `max_c < 1` (`:480-487`) — the correlation modifier is applied later, in `options.py`, where no such refusal exists. |
| **Production applicability** | Merged production. `CORRELATION_ENABLED = True` (`config.py:271`). |
| **User-visible consequence** | Worked example on real constants: an index-ETF credit spread has max loss `0.70 × 5.0 × 100 = $350/contract` (`options.py:414-426`, `:65`). Budget is `15000 × 0.026667 × risk_modifier`. At **NEUTRAL correlation (0.7) — the default state**, budget is $280 and the system emits 1 contract at $350, a **1.25× breach**. At CONFLICT (0.4), budget is $160 and it still emits $350, a **2.19× breach**. NEUTRAL is returned whenever GLD or DXY is flat, missing, or stale (`correlation.py:58-70`), so this is the ordinary case, not an edge. The correlation modifier's entire risk reduction is nullified. The breach is silent: `dollar_risk` truthfully prints $350, but no surface states that $350 exceeds the $280 budget the system just computed. |
| **Current severity** | **Critical** — bypasses a live position-risk limit on the ordinary path. |
| **Existing work** | **RULED by Dustin 2026-07-24** (`docs/DECISIONS.md:106-139`): "refuse the trade… A floor that breaches the risk limit turns the limit into a suggestion." The same entry states **"NOT IMPLEMENTED… Nothing in this entry authorizes a code change."** |
| **Missing proof** | Not established: how many of the 6 historical ALLOW_TRADE decisions were emitted under a sub-1.0 correlation modifier (`risk_modifier` is not persisted per candidate in the audit record). |
| **Next authority** | Dustin decision — the ruling exists and explicitly withholds implementation authority. No further diagnostic is needed to establish the defect. |
| **Residual limitation** | n/a — original defect intact. |
| **Confidence** | **High** — lead traced Gate 8 → correlation → `options.py` floor directly and computed the breach from current constants. |

---

## OPEN — HIGH

### CB-03 · Execution-policy size multiplier is computed and recorded but never resizes the position

| Field | Value |
|---|---|
| **Original source** | `RECONCILED_FINDINGS.md` A2 (Tier 0, High) |
| **Exact claim** | The policy `size_multiplier` lands on the decision object and is exported, but never mutates `contracts` / `dollar_risk`; trader-facing surfaces render the pre-policy `OptionSetup`. |
| **Current status** | **`OPEN`** |
| **Current evidence** | Every `size_multiplier` reference in `cuttingboard/` is a definition, a validation, a pass-through, or a record write — none is a multiplication into size. It is set (`execution_policy.py:184,198,215`), type-checked (`contract.py:689-700`), serialized (`contract.py:362`, `audit.py:146,187`, `trade_decision.py:58`), and read as a boolean gate (`trade_decision.py:115`, `size_multiplier > 0`). `output.py:361-362` renders `setup.max_contracts` / `setup.dollar_risk` directly. The literal `size_rounds_to_zero` — the operator-settled policy-block reason — **does not exist in any production file**. |
| **Production applicability** | Merged production. |
| **User-visible consequence** | A policy decision to cut size by half is displayed and exported as a full-size position. The contract can carry the inconsistent triple `{size_multiplier: 0.5, position_size: 2, dollar_risk: 300}`. Only a multiplier of exactly `0` has any effect, and only as a block. |
| **Current severity** | **High** — misleads sizing on the trader-facing surface; the risk-reduction control is inert. |
| **Existing work** | Planned as BUILD_PLAN "PRD-254"; that number landed hook/settings hardening. **Operator decision 2 (2026-07-10, BUILD_PLAN §Operator decisions) approved the materialization AND the explicit `size_rounds_to_zero` block.** Neither shipped. |
| **Missing proof** | None for the defect. |
| **Next authority** | Dustin decision. |
| **Residual limitation** | n/a. |
| **Confidence** | **High** — lead enumerated every `size_multiplier` reference and the repo-wide `size_rounds_to_zero` search directly. **This row corrects a Lane-1 conclusion** that PRD-073 made the behavior intentional; see `RECONCILIATION_REPORT.md` § Contradictions. |

---

### CB-04 · Trade brakes count recommendations as executed trades — including within a single run

| Field | Value |
|---|---|
| **Original source** | `RECONCILED_FINDINGS.md` A3 (Tier 0, High, tagged `[DOCTRINE?]`) |
| **Exact claim** | `prior_trade_count` increments off `ALLOW_TRADE` audit records with no fill evidence, so cooldown / daily-limit / loss-lockout fire on history that never happened. |
| **Current status** | **`OPEN`** |
| **Current evidence** | `execution_policy.py:94-103` sums `decision_status == ALLOW_TRADE` from prior audit records into `prior_trade_count` and sets `last_trade_at_utc`; `:105-109` derives `consecutive_losses` from the hypothetical `evaluation.jsonl`. `load_execution_session_state` returns those derived values — not the dormant `(0, 0, None)` the operator approved. |
| **Production applicability** | Merged production, **and observed firing in live published history**. |
| **User-visible consequence** | Verified against `origin/publish:logs/audit.jsonl` (56 pipeline records, 2026-05-07→2026-07-30): **`cooldown` blocked 5 qualified candidates**, against only 6 `ALLOW_TRADE` decisions in the entire history. Every cooldown block occurred in the **same run** as an ALLOW — 2026-06-30 allowed SPY and blocked QQQ, IWM and NVDA by cooldown; 2026-06-23 allowed AAPL and blocked META; 2026-07-23 allowed SPY and blocked SLV. The trader was shown one candidate instead of four because the system treated its own first *recommendation* as an executed *fill*. |
| **Current severity** | **High** — suppresses qualified candidates from the trader's view on a fill that never occurred. Conservative in direction (it blocks rather than permits), which is why it is not Critical. |
| **Existing work** | Planned as BUILD_PLAN "PRD-255"; that number landed the review-artifact spec. **Operator decision 3 (2026-07-10) approved "fully dormant, including the same-run in-run counter."** Not shipped. |
| **Missing proof** | None for the defect. Not established: whether Dustin would in fact have taken the suppressed candidates. |
| **Next authority** | Dustin decision — the doctrine (`actual-trades-only`) is already settled; only implementation authority is withheld. |
| **Residual limitation** | n/a. |
| **Confidence** | **High** — lead independently aggregated the publish-branch audit log and traced each cooldown block to a same-run ALLOW. |

---

### CB-05 · Macro-pressure computation failure degrades to `UNKNOWN`, which the policy treats as unconstrained at full size

| Field | Value |
|---|---|
| **Original source** | `audits/FINDINGS.md` F-07 (Medium); promoted to Tier 2 High in `RECONCILED_FINDINGS.md` |
| **Exact claim** | Any exception in `_compute_overall_pressure` becomes `"UNKNOWN"`, and `execution_policy` treats `UNKNOWN` as full allow at full size — so a bug or data change silently removes a blocking gate. |
| **Current status** | **`OPEN`** |
| **Current evidence** | `runtime/__init__.py:1384-1391` — bare `except Exception` → `logger.warning(...)` → `return "UNKNOWN"`. `execution_policy.py:239-241` — `if pressure in ("UNKNOWN", "NEUTRAL"): return PolicyDecision(True, reason, size)`, i.e. allowed, size unchanged. `overall_pressure` also feeds the trade-thesis and invalidation gates. |
| **Production applicability** | Merged production. |
| **User-visible consequence** | The one Q2 input that gates decisions (RISK_OFF blocks LONGs; MIXED cuts size 25%) vanishes on any exception with only a log warning. Computed-`UNKNOWN` and failed-to-compute are indistinguishable at every downstream surface. |
| **Current severity** | **High** — silently removes a blocking gate on the live decision path. |
| **Existing work** | Planned as BUILD_PLAN "PRD-260"; that number landed continuation decision geometry. Not shipped. Sits inside the unresolved F-15 sidecar-doctrine contradiction (CB-16). |
| **Missing proof** | Not established: how often the exception path has actually fired (the warning is not durably counted). |
| **Next authority** | Narrow diagnostic — count `build_macro_pressure failed` occurrences in workflow logs — then Dustin decision. |
| **Residual limitation** | n/a. |
| **Confidence** | **High** — lead read both sites directly. |

---

### CB-06 · The hourly channel cannot fail visibly: the runner always exits 0 and readiness checks key presence, not status

| Field | Value |
|---|---|
| **Original source** | `audits/FINDINGS.md` F-08 (Medium); Tier 2 High in `RECONCILED_FINDINGS.md` |
| **Exact claim** | A broken-but-non-throwing hourly runner reports green indefinitely; the freshness/readiness gate greens an empty or ERROR-status run. |
| **Current status** | **`OPEN`** |
| **Current evidence** | `cuttingboard/alert_runner.py:43` — the function's own docstring reads "Run the hourly alert path and **convert all runtime failures to exit 0**"; returns `0` at `:81`, `:95`, `:122`. `scripts/check_readiness.py:15-16` maps each artifact to a tuple of **key names** (`("meta", "run_status", "schema_version", "sections")`, `("status", "outcome")`) — presence, never value. A fresh ERROR/HALT artifact satisfies it. |
| **Production applicability** | Merged production. Precedent: the 2026-07-07 hourly freeze. |
| **User-visible consequence** | The hourly board can stay silently stale or broken while every workflow reports green. PRD-250 added a client-side staleness banner, which fixes the *viewer's* blindness only; the job-level vacuous green remains, with no red test asserting it impossible. |
| **Current severity** | **High** — a trader-facing channel can degrade with no operator signal. |
| **Existing work** | Planned as BUILD_PLAN "PRD-259"; that number landed the continuation HOLD gate. PRD-250 addressed the viewer surface only. `.github/workflows/dashboard_preview.yml` already implements the fail-loud inversion, so the pattern exists in-repo. |
| **Missing proof** | None for the defect. |
| **Next authority** | Dustin decision. |
| **Residual limitation** | Partially narrowed at the VIEWER layer by PRD-250; the JOB layer is untouched. |
| **Confidence** | **High** — lead read the runner's exit paths and the readiness key tuples directly. |

---

### CB-07 · The opening range is computed from mid-session bars and gates live BLOCK_TRADE decisions

| Field | Value |
|---|---|
| **Original source** | `audits/stage0-recon-2026-07-20/`; carried into `docs/prd_history/PRD-271.md`; External Context Brief §4.3 |
| **Exact claim** | `ingestion.fetch_intraday_bars` returns `frame.tail(120)`; `watch._bars_from_df` tails 120 again; `watch.py` then takes `bars[:5]` — so on a full ~361-bar session the "opening range" is a roughly 13:31–13:35 ET window, not 09:30–09:35. |
| **Current status** | **`OPEN`** |
| **Current evidence** | `ingestion.py:207` (`tail(120)`), `watch.py:30,357` (second truncation), `watch.py:164-166` (`bars[:5]`) — all present at HEAD. `docs/prd_history/PRD-271.md:36-45` records two independent reproductions (expected ORB high 110.0, actual 777.0). ORB feeds `execution_policy`'s `orb_inside_range` BLOCK_TRADE gate. |
| **Production applicability** | Merged production. **PRD-271 merged as PR #173 but is a Stage-0 SCAFFOLD ONLY** — GOAL/SCOPE/FILES are deliberately TODO under `GATE A REQUIRED BEFORE AUTHORING`. The merge contains no fix. |
| **User-visible consequence** | Not display-only. A wrong opening range both blocks trades that should pass and passes trades that should block, on a gate whose output is a terminal BLOCK. |
| **Current severity** | **High** — corrupts a live BLOCK gate's input. Held below Critical because the gate blocks conservatively as often as it mis-permits, and no evidence establishes the realized direction of error. |
| **Existing work** | PRD-271 (registry: IN PROGRESS; merged scaffold @ #173). Gate A pending Dustin. |
| **Missing proof** | Not established: how often `orb_inside_range` has actually changed a decision. The audit record does not persist the ORB window. |
| **Next authority** | Dustin decision (PRD-271 Gate A is already the named seam). |
| **Residual limitation** | n/a — numbering exists; the defect does not. |
| **Confidence** | **High** — lead confirmed all three truncation sites at HEAD and that PRD-271 is scaffold-only. |

---

### CB-08 · Spread economics are a 30 %-of-width estimate; live executable pricing is never established

| Field | Value |
|---|---|
| **Original source** | `RECONCILED_FINDINGS.md` A1 second leg ("A1b") |
| **Exact claim** | Chain validation prices one near-ATM contract by open interest; it never resolves the setup's two strikes, prices both legs, or computes net credit/debit — so the live spread economics behind the printed max risk are never established. |
| **Current status** | **`OPEN`** |
| **Current evidence** | `cuttingboard/chain_validation.py` selects a single `best_row` near-ATM contract (`:233-240`); it reads `setup.symbol`, `setup.dte`, `setup.strategy` but never `long_strike` / `short_strike`. The tokens `net_credit` and `net_debit` do not occur in the file. Max loss remains `_max_loss_for_strategy(strategy, strike_distance)` — a fixed 30 %-of-width proxy (`options.py:414-426`, `_DEBIT_PCT_OF_WIDTH = 0.30` at `:67`). |
| **Production applicability** | Merged production. |
| **User-visible consequence** | The printed "max risk" is a model figure, not a quote. The system never establishes that the credit it assumes is obtainable. Under the charter's distinction: this is **modelled spread economics, not live executable pricing**, and must not be read as the latter. |
| **Current severity** | **High** — the money number on the decision surface is an estimate presented without an estimate marker. |
| **Existing work** | Planned as BUILD_PLAN "PRD-256". **The real PRD-256 delivered a different concern** — continuation-path ATR-proxy max-loss bounding — and is correctly COMPLETE for THAT concern. A1b's seam (the `max_loss` field PRD-251 introduced) exists and is unfilled. |
| **Missing proof** | Not established: the magnitude of divergence between the 30 % proxy and live chain economics. One fixture chain comparison would bound it. |
| **Next authority** | Narrow diagnostic (proxy-vs-live divergence on captured chains), then Dustin decision. |
| **Residual limitation** | **This IS the residual limitation of finding A1.** The original arithmetic defect (2.3× understatement) is fixed — see CB-13. What remains is that the corrected arithmetic runs on estimated rather than live economics. Do not restate CB-08 as an understatement defect. |
| **Confidence** | **High** — lead confirmed the single-contract selection and the absence of both-leg pricing. **This row corrects a Lane-2 `SUPERSEDED` proposal**; see `RECONCILIATION_REPORT.md` § Contradictions. |

---

### CB-09 · Load-bearing artifacts are written non-atomically; a torn `market_map.json` wedges every later daily run

| Field | Value |
|---|---|
| **Original source** | `audits/FINDINGS.md` F-06 (High, held) |
| **Exact claim** | `latest_run.json`, `latest_contract.json`, `market_map.json` and the payload/HTML are written in place under CI's kill timer, while less-critical sidecars get temp+rename; a torn `market_map.json` makes every later daily run raise until manually cleared. |
| **Current status** | **`OPEN`** |
| **Current evidence** | `runtime/__init__.py` `safe_write_latest`, `_write_summary_files`, `_rewrite_summary_file` use bare `write_text`; atomic `tmp.replace` is used for the less-critical snapshots. `_load_previous_market_map` raises on malformed JSON. |
| **Production applicability** | Merged production. |
| **User-visible consequence** | Atomicity is applied inversely to criticality. A mid-write kill wedges the daily pipeline until a human clears the file. |
| **Current severity** | **High** — a single interrupted write halts the product until manual intervention. |
| **Existing work** | BUILD_PLAN Wave 5. Never authored. `RECONCILED_FINDINGS.md` already banked two corrections: the impossible line citation and the cross-workflow-concurrency portion are **wrong and must not be built** (separate runner filesystems). The in-process unlocked appends and the torn-map wedge are the real residue. |
| **Missing proof** | Not established: whether a torn write has ever actually occurred. |
| **Next authority** | Dustin decision. |
| **Residual limitation** | Scope already narrowed at reconcile — see "Existing work". |
| **Confidence** | **Medium** — lead confirmed the non-atomic writes via Lane-2 evidence and the surrounding code, but did not re-read every one of the four write sites individually. |

---

### CB-10 · The canonical qualification document states a risk budget 2.7× smaller than the code's

| Field | Value |
|---|---|
| **Original source** | External Context Brief §4.6 (claimed "8 places") |
| **Exact claim** | `docs/trade_qualification.md` documents `MAX_RISK_PCT_PER_TRADE = 0.01` and a $150 effective budget; `config.py` carries `0.026667` → ~$400.005. |
| **Current status** | **`OPEN`** |
| **Current evidence** | `docs/trade_qualification.md:174` ("`# $150 under RISK_ON`"), `:181` ("`MAX_RISK_PCT_PER_TRADE=0.01` … the budget is $150"), `:249` ("`MAX_RISK_PCT_PER_TRADE=0.01`, giving an effective…"). `cuttingboard/config.py:70-71` — `ACCOUNT_EQUITY = 15000.0`, `MAX_RISK_PCT_PER_TRADE = 0.026667`. |
| **Production applicability** | Merged production documentation. |
| **User-visible consequence** | Anyone sizing a position from the canonical qualification document sizes at **37.5 % of the real budget**. It is the document the trader would consult to check the engine's arithmetic by hand. |
| **Current severity** | **High** — a live sizing hazard on the canonical reference, and a direct breach of the `VISION.md` docs-match-code principle. |
| **Existing work** | PRD-252 made the config change and recorded it in `PROJECT_STATE.md`; `trade_qualification.md` was never updated. PRD-247 ran a doc-truth pass over the same file and did not catch it. |
| **Missing proof** | None. |
| **Next authority** | Dustin decision. |
| **Residual limitation** | **Corrected count: 3 substantive stale sites, not the 8 the brief claimed.** The other `0.01` occurrences in that file are `MIN_STOP_PCT` and `CONTINUATION_VIX_SPIKE_BLOCK` and are correct. |
| **Confidence** | **High** — lead grepped and read each occurrence. |

---

### CB-11 · The intended join key `system_candidate_id` is defined but never emitted

| Field | Value |
|---|---|
| **Original source** | External Context Brief §1.3 |
| **Exact claim** | `system_candidate_id` appears in `manual_journal.py`'s field definition, tests, and docs, but no generator exists; it is absent from `audit._build_record` and from the contract. |
| **Current status** | **`OPEN`** |
| **Current evidence** | Definition at `cuttingboard/manual_journal.py:59`; assertions in `tests/test_manual_journal.py` and `tests/test_review_scorecard.py`. `audit._build_record` (`audit.py:90-243`) never constructs or stores it. No generator anywhere. |
| **Production applicability** | Merged production. |
| **User-visible consequence** | Even a fully populated trade journal could only join to engine output on `(date, symbol)`. Every downstream measurement of "did the engine's read change my decision" inherits that ambiguity. |
| **Current severity** | **High** — it is the keystone dependency for the entire awareness→behavior loop `VISION.md:67-75` names as the project's central risk. Not Critical: nothing currently displays or decides on it. |
| **Existing work** | PRD-070 built the journal writer. `docs/decision_quality_map.md` (PRD-105) inventoried the gap. None of its four proposed downstream PRDs exist. |
| **Missing proof** | None for the defect. |
| **Next authority** | Dustin decision. |
| **Residual limitation** | n/a. |
| **Confidence** | **High** — lead-confirmed via Lane 3's repo-wide classification of every occurrence. |

---

## PARTIAL

### CB-12 · The HIGH-RISK CI gate still trusts a self-declared label and an artifact's filename

| Field | Value |
|---|---|
| **Original source** | `audits/FINDINGS.md` F-04 (High) — four verified bypasses |
| **Exact claim (original)** | The gate keys on the PRD doc's own case-sensitive `LANE` header; bypasses are (a) declare `LANE: STANDARD`, (b) `High-Risk` casing, (c) header text between `LANE` and `HIGH-RISK`, (d) docless COMPLETE row passes vacuously. The artifact leg is satisfied by file *existence*; an empty file passes. |
| **Current status** | **`PARTIAL`** |
| **Current evidence** | `tools/validate_prd_registry.py:26` — `_LANE_HIGH_RISK_RE = re.compile(r"^LANE\b[:\s]*\n?\s*HIGH-RISK", re.MULTILINE)`. **`re.IGNORECASE` is absent**, so bypass (b) survives. `:525-527` — `if not doc.exists(): continue` precedes the lane check, so bypass (d) survives on the second-model leg. The artifact leg (`:528+`) computes `has_artifact` from `history.glob(f"{review_prefix}*.md")` filtered by filename prefix — **existence and naming only; contents are never read**, so an empty file still passes. Bypass (a) is unaddressed — nothing cross-checks the declared lane against the change surface. No test in `tests/test_prd_registry.py` covers the casing bypass. |
| **Production applicability** | Merged production. |
| **User-visible consequence** | The gate `CLAUDE.md` advertises can be satisfied by writing the right words rather than doing the work — PRD-198's own definition of semantic failure, inside the guard enforcing PRD-198's sibling policy. |
| **Current severity** | **High** (held) — it is the control standing between an agent and an unreviewed HIGH-RISK merge. Mitigated in practice by GOV-1: Dustin merges every PR by hand. |
| **Existing work** | **What DID land:** PRD-242 (the disposition requirement and its validator) and **PRD-269**, which closed the doc-STATUS blind spot — a registry-COMPLETE row whose doc status disagrees now errors (`:483-499`). That is a real and separate improvement. **It is not F-04's four bypasses.** BUILD_PLAN's "PRD-257" landed a dashboard comment fix. |
| **Missing proof** | None for the residual. |
| **Next authority** | Dustin decision. Note **PR #174 (OPEN, not production)** scaffolds PRD-275, which would enforce artifact append-only and merged-commit SHA pinning — the artifact-content leg. An open PR is pending evidence, not closure. |
| **Residual limitation** | **The residual is: label casing, declared-lane trust, docless-row skip, and existence-not-content on the artifact leg.** Do not restate this row as "the doc-status blind spot" — that half is closed. |
| **Confidence** | **High** — lead read the regex, all three `not doc.exists()` sites, and the `has_artifact` computation directly. **This row corrects a Lane-2 `FIXED` proposal**; see `RECONCILIATION_REPORT.md` § Contradictions. |

---

### CB-12b · Technical backstops for manual-merge discipline: settings leg done, code legs absent

| Field | Value |
|---|---|
| **Original source** | `audits/FINDINGS.md` F-05 (High, held) |
| **Exact claim** | No CODEOWNERS, no CI changed-path check, `CLAUDE.md` and `.claude/skills/` absent from the protected set; branch protection requires only `test`, no approvals, admin enforcement disabled. |
| **Current status** | **`PARTIAL`** |
| **Current evidence** | `.github/CODEOWNERS` does not exist at HEAD. `.github/workflows/ci.yml` contains no changed-path governance check. `.claude/hooks/protect_files.sh` does not list `CLAUDE.md` or `.claude/skills/`. **Closed leg:** `enforce_admins` was flipped true on `main` 2026-07-19 (`docs/DECISIONS.md`), so protection binds the admin identity. |
| **Production applicability** | Merged production (and live GitHub settings). |
| **User-visible consequence** | Governance-guardrail edits have no technical backstop in-repo. |
| **Current severity** | **Medium** — reassessed DOWN from the ledger's High. The finding's premise was unbabysat agent merging; **GOV-1 (2026-07-25) makes Dustin's manual merge universal on every PR, and `.claude/settings.json` denies `gh pr merge` to the agent outright.** The exposure the finding was written against is now covered by process and by a deny rule, not by the missing code. |
| **Existing work** | BUILD_PLAN Wave 3 explicitly records that this "NEVER RODE" and that remaining legs queue behind other work. |
| **Missing proof** | None. |
| **Next authority** | Dustin decision (low urgency). |
| **Residual limitation** | **Residual is the two code legs only** (CODEOWNERS, CI changed-path). The settings leg and the merge-authority premise are closed. |
| **Confidence** | **High** — lead confirmed file absence and read the deny list directly. |

---

## FIXED

### CB-13 · Credit-spread max risk understated ~2.3× — **FIXED**

| Field | Value |
|---|---|
| **Original source** | `RECONCILED_FINDINGS.md` A1a (Tier 0, **CRITICAL**) |
| **Exact claim** | A 30 %-of-width debit proxy became `dollar_risk` for credit strategies: a $5-wide bull put at $1.50 credit printed "max risk $150" against a true max loss of $350. |
| **Current status** | **`FIXED`** |
| **Current evidence (code)** | `cuttingboard/options.py:414-426` — `_max_loss_for_strategy` returns `strike_distance - debit_proxy` (70 % of width) for `BULL_PUT_SPREAD` / `BEAR_CALL_SPREAD`, and the debit for debit strategies. Consumed by Gate 8 (`qualification.py:472-475`) and by the final resize (`options.py:229`). |
| **Current evidence (discriminating regression)** | `tests/test_phase5.py::test_non_continuation_result_ignores_stale_candidate_max_loss_prd256` constructs a candidate with `max_loss=999.0` **deliberately wrong** and asserts `setup.dollar_risk == _max_loss_for_strategy(BULL_PUT_SPREAD, 5.0) * 100`. It goes red if the code ever reads the passed-in value instead of recomputing. Its own comment records that the preceding test could NOT discriminate, because its fixture's `max_loss` already equalled the recomputed figure — the repo found and closed its own non-discriminating-fixture hole. |
| **Production applicability** | Merged production (PRD-251 @ #132; continuation path completed by PRD-256 @ #146). |
| **User-visible consequence** | n/a — resolved. |
| **Current severity** | n/a. |
| **Existing work** | PRD-251, PRD-256 (R2 ruled FIX; R3 removed the continuation exclusion so every result prices through `_max_loss_for_strategy`). |
| **Missing proof** | None. |
| **Next authority** | **None.** |
| **Residual limitation** | The corrected arithmetic runs on ESTIMATED economics — tracked separately as **CB-08**, not here. |
| **Confidence** | **High** — lead read the function body and the discriminating test source. |

---

### CB-14 · Fabricated `pct_change = 0.0` on missing `previous_close` — **FIXED**

| Field | Value |
|---|---|
| **Original source** | `audits/FINDINGS.md` F-02 (High); Tier 1 root cause |
| **Exact claim** | A quote with a valid `last_price` but missing `previous_close` was emitted with `pct_change=0.0` and `fetch_succeeded=True`, so fabricated calm passed every validation rule and disarmed the pct-based stress guards. |
| **Current status** | **`FIXED`** |
| **Current evidence (code)** | `cuttingboard/ingestion.py:303-311` — a `None`, non-finite, or non-positive `prev_close` now `raise ValueError(...)`, with the PRD-262 rationale in-comment. The retry wrapper converts it to `fetch_succeeded=False` with a `failure_reason`. |
| **Current evidence (discriminating regression)** | `tests/test_phase1.py:340` `test_missing_previous_close_raises` (parametrised over the invalid values) and `:348` `test_wrapper_converts_missing_previous_close_to_fetch_failure`, which asserts `"previous_close" in quote.failure_reason`. Both fail if the fallback returns. |
| **Production applicability** | Merged production (PRD-262 @ #151). |
| **User-visible consequence** | n/a — resolved. |
| **Current severity** | n/a. |
| **Existing work** | PRD-262, which also fixed the `normalization.py` NaN twin and the EXPANSION breadth denominator. |
| **Missing proof** | None. |
| **Next authority** | **None.** |
| **Residual limitation** | `_kill_switch` itself still defaults missing SPY/VIX inputs to `0.0`; PRD-262 recorded this deliberately as shielded (those are halt symbols, call sites halt-guarded). Tracked as an observation, not a defect row. |
| **Confidence** | **High** — lead read the raise site and located both tests. |

---

### CB-15 · Regime confidence inflated on optional-symbol dropout — **FIXED**

| Field | Value |
|---|---|
| **Original source** | `RECONCILED_FINDINGS.md` Tier 4 (corroborated ×3) |
| **Exact claim** | Confidence was `abs(net)/total_votes`, so dropout of an optional voter turned dilution into concentration and inflated confidence, crossing a posture tier on identical evidence. |
| **Current status** | **`FIXED`** |
| **Current evidence (code)** | `cuttingboard/regime.py:201-209` — `missing = len(raw_votes) - total_votes`; `bounded_net` moves each missing vote against the survivors' leader, clamped so bounding never crosses sign; `confidence = abs(bounded_net) / len(raw_votes)` (the structural 8-vote denominator, not the survivor count); `_classify_regime` and `_determine_posture` both consume the bounded values. |
| **Current evidence (discriminating regression)** | `tests/test_regime.py::test_vix_only_synthetic_is_bounded_to_stay_flat` asserts that the fixture which was previously the last path to `NEUTRAL_PREMIUM` now yields `confidence == 0.0` and `NEUTRAL`/`STAY_FLAT`, while `net_score == 1` and `total_votes == 2` stay truthful. PRD-263 additionally carries an exhaustive 3^8 × 3 proof that a skipped vote can never out-permit full coverage. |
| **Production applicability** | Merged production (PRD-263 @ #152; coverage marker PRD-265 @ #154). |
| **User-visible consequence** | n/a — resolved. |
| **Current severity** | n/a. |
| **Existing work** | PRD-263, PRD-265, PRD-267. |
| **Missing proof** | Behavior-neutral on complete data over a 247-day replay; the window contained **zero** partial-vote days, so synthetic tests remain the only dropout evidence. PRD-263 disclosed this. |
| **Next authority** | **None.** |
| **Residual limitation** | See **CB-17** for the un-bounded `net_score` readers, which PRD-263 explicitly left out of scope. |
| **Confidence** | **High** — lead read the bounding arithmetic and the named test. |

---

## MEDIUM AND LOW — OPEN

### CB-16 · The sidecar doctrine forbids and legitimises decision-feeding sidecars simultaneously

`OPEN` · **Medium** · Source: `FINDINGS.md` F-15. `docs/sidecar_doctrine.md` declares `market_map → overnight_policy` and `macro_pressure → execution_policy` as sanctioned decision-feeding sidecars, while its own observe-only sections forbid exactly that. Reviews on either side can cite the document. **Consequence:** the operational risk hiding in the ambiguity is CB-05 — a decision-feeding path built to observation-grade failure discipline. **Next authority:** Dustin decision (a doctrine ruling, not code); the ruling shapes how CB-05 would be worded. **Confidence:** Medium — carried from the ledger, not independently re-read this pass.

### CB-17 · `RegimeState.net_score` is stored raw while classification uses `bounded_net`

`OPEN` · **Low** · Source: External Context Brief §4.6; raised as **High** by Lane 4. **Severity reassessed DOWN to Low, and the reason is the substance of this row.** `regime.py:221` stores the raw net; `:206-208` classify and score confidence from `bounded_net`. The decision-bearing raw readers are `qualification.py:649-653` (`direction_for_regime`'s NEUTRAL tiebreaker), `market_map.py:407-409`, `watch.py:453-455`. **The NEUTRAL branch is not reachable in production:** `_classify_regime` returns `NEUTRAL` only when `|bounded_net| ≤ 1`, hence `confidence ≤ 0.125`, and `_determine_posture`'s global floor (`confidence < MIN_REGIME_CONFIDENCE = 0.50`) then forces `STAY_FLAT`, which `qualification.py:368-373` short-circuits before any per-symbol work. `tests/test_regime.py:285-292` states this unreachability explicitly and records the posture branch as deliberately parked by PRD-263. **Residual limitation:** a latent inconsistency with no current decision path, plus one unreachable output channel (`NEUTRAL_PREMIUM`, `regime.py:344`) that nonetheless carries trader-facing copy in `output.py:203`, `runtime/_constants.py:85` and `notifications/formatter.py:313,471`. **Next authority:** none required; Dustin decision if the dead posture should be retired under cuts-before-additions. **Confidence:** High — lead derived the unreachability, then found the repo had already documented it.

### CB-18 · Freshness measures fetch time, not market time

`OPEN` · **Medium** · Source: `RECONCILED_FINDINGS.md` C1 (High). `fetched_at_utc = datetime.now()`; no exchange timestamp is read. Stale weekend, holiday, or delayed prices certify as fresh. **Severity reassessed DOWN from High:** the scheduled crons run in RTH slots where the exposure is small, and the daily path halts on other freshness legs. **Residual:** `workflow_dispatch` and local off-hours runs remain exposed. Invalidates F-23's Sunday-halt claim. **Next authority:** Dustin decision. **Confidence:** Medium — carried from Lane 2's evidence; lead did not re-read `validation.py` this pass.

### CB-19 · No run is reproducible; `--date` relabels rather than replays

`OPEN` · **Medium** · Source: `FINDINGS.md` F-03 (High, held). `runtime/__init__.py:2249-2250` `_resolve_run_date` parses the argument and stamps it; no raw-input snapshot is written anywhere. Quotes, OHLCV frames, intraday bars, chain OI/spread and the validation clock are all discarded. **Consequence:** "why did it say TRADE on June 12" is answerable only from recorded reason strings, never re-derivable — so a wrong explanation is undetectable after the fact. **Severity reassessed DOWN from High:** forensic, with no live-decision path. **Next authority:** Dustin decision. **Confidence:** High.

### CB-20 · The manual journal has no entry point, so the review scorecard is dead code

`OPEN` · **Medium** · Source: External Context Brief §1.3. Two concerns are deliberately kept in one row **only because the second is strictly downstream of the first**: `cuttingboard/manual_journal.py`'s `append_record` is imported by `tests/test_manual_journal.py` alone; `runtime.build_parser` (`:164-180`) registers only `--mode`, `--notify-mode`, `--fixture-file`, `--file`, `--date`; no script writes an entry; `logs/manual_trades.jsonl` has never existed. `review_scorecard.py` reads that path and has no other input. **Consequence:** the only artifact that would measure TRADER behaviour rather than ENGINE behaviour cannot run. The writer, the 13-value mistake taxonomy, validation, and passing tests all exist — it is wiring, not construction. **Next authority:** Dustin decision. Note `docs/decision_quality_map.md` Gap 5 rules the real journal lives in an Obsidian vault outside the repo, so the doctrine question precedes the wiring question. **Confidence:** High.

### CB-21 · Evaluation and performance artifacts are written by code that never runs

`OPEN` · **Medium** · Source: External Context Brief §1.3. `evaluation.py:31` defines `logs/evaluation.jsonl` and `performance_engine.py:28-36` writes `performance_summary.json`; neither file exists on `main` or on `origin/publish`, and no reader consumes the summary. **Next authority:** narrow diagnostic — determine whether the runtime ever invokes them — then Dustin decision. **Confidence:** Medium — absence of the artifacts is certain; whether the call site exists and silently no-ops was not run to ground.

### CB-22 · `_MIN_SAMPLE = 5` asserts that five observations support a rate, and buckets only by symbol

`OPEN` · **Medium** · Source: External Context Brief §1.2/§3.4. `performance_engine.py:23` suppresses below `n = 5`; the aggregation loop keys on symbol alone — no slicing by regime, posture, gate, block reason, or direction. **Consequence:** at n = 5 a win rate carries a 95 % interval of roughly ±44 points; publishing a point estimate there produces confidence without information — the exact `VISION.md:67-75` failure mode. Symbol is close to the least informative axis available and fragments an already-tiny sample across ~23 symbols. **Held at Medium, not High:** CB-21 establishes the engine produces no output today, so nothing currently displays the number. **Next authority:** Dustin decision (withhold the rate, or band it with its interval). **Confidence:** High on the code; the sample-size arithmetic is the brief's, recomputed by its author, not re-derived here.

### CB-23 · Only `ALLOW_TRADE` candidates are ever evaluated forward

`OPEN` · **Medium** · Source: External Context Brief §3.2; `docs/decision_quality_map.md` Gap 6. `evaluation.py:128` filters to `decision_status == "ALLOW_TRADE"`. **Consequence:** "did the gates block winners?" is structurally unanswerable — and that is the question that would justify or retune every threshold in `qualification.py`. **Next authority:** Dustin decision. **Confidence:** High.

### CB-24 · The evaluation horizon does not match the instrument being evaluated

`OPEN` · **Medium** · Source: External Context Brief §3.1. `config.py:191` `EVALUATION_WINDOW_BARS = 78` on 1-minute bars resolves TARGET_HIT / STOP_HIT **on the underlying**, and reports an `R_multiple`; the setups are 14–21 DTE option spreads (`options.py:19-24`). **The charter's distinction applies directly: an underlying target/stop touch is not an actual options-trade result, and must not be read as one.** **Severity held at Medium rather than High** because its most dangerous consumer is neutralised: the brief argues this R feeds `execution_policy`'s `loss_lockout`, and it does — but per CB-04 that lockout derives from the same hypothetical evaluation records and has never been observed firing in the published history (0 of 48 blocks). The corruption is of the *measurement*, not currently of the *decision*. **Next authority:** Dustin decision. **Confidence:** High on the constants; Medium on the consequence chain.

### CB-25 · Gate vectors, `stay_flat_reason`, and `excluded_symbols` structure are computed and discarded

`OPEN` · **Medium** · Source: External Context Brief §4.4. Three losses of already-computed state, grouped because they share one cause — the audit record is narrower than the pipeline's own state. `QualificationResult` carries `gates_passed` / `gates_failed` / `gates_skipped`; `audit._build_record` (`audit.py:127-152`) persists none of them. `stay_flat_reason` reaches only `logs/latest_hourly_contract.json`, overwritten every run — and STAY_FLAT is the modal outcome. `excluded_symbols` is free prose (observed: `{"AAPL": "2 soft gates failed: R:R 2.00 below 2.0 minimum; …", "COIN": "CHOP"}`), which PRD-240 already rewrote once, silently breaking any parser. **Consequence:** rejection analysis requires regex over prose. **Next authority:** Dustin decision. **Confidence:** High.

### CB-26 · Run identity is a timestamp, not a stable id

`OPEN` · **Low** · Source: External Context Brief §4.1 (adjacent to CB-11). The audit record carries `run_at_utc` and `date`; there is no explicit `run_id`. Unique enough per invocation, but not a semantic identity anything else can reference. **Next authority:** none required; folds into CB-11 if that is ever taken up. **Confidence:** High.

### CB-27 · Remaining documentation drift

`OPEN` · **Low** · Source: External Context Brief §4.6, verified by Lane 4. Four items, none decision-bearing, listed for completeness and explicitly NOT corrected by this reconciliation: `runtime/_constants.py:87` renders EXPANSION "R:R >= 1.5" while `config.py:123` reads `EXPANSION_RR_RATIO = 2.0` (**trader-facing** — the permission line in the report header; the highest-value item here); `docs/runbook.md:94` says "Stop below 0.5× ATR14" vs `STOP_ATR_FLOOR_K = 1.0`; `docs/system_logic_map.md:21` says "yfinance primary, Polygon fallback" with no Polygon code in the tree; `cuttingboard/derived.py:8-9` says "6 months (~126 bars)" vs `OHLCV_FETCH_MONTHS = 12`. Also three coexisting pipeline layer numberings (module docstrings vs `engine_doctor.PIPELINE` vs `system_logic_map.md`). **Note:** the brief listed `docs/regime_model.md`'s confidence formula as drift; Lane 4 found the doc **correct**. That item is dropped. **Next authority:** Dustin decision. **Confidence:** High.

### CB-28 · `docs/PROJECT_STATE.md` carries stale claims at HEAD

`OPEN` · **Low** · It records "Last updated 2026-07-26 (commit 724d84a)" while HEAD is `9e6b772`. Verified stale: (a) it states PRD-271's scaffold "sits UNMERGED on branch `claude/prd-271-orb-gate-a`" — PRD-271 merged as PR #173 and is in the log at HEAD; (b) it states "Active PRD: none in progress" while the registry marks **four** rows IN PROGRESS (268, 271, 272, 273); (c) its test baseline (3044 passed, 1 xfailed, run 30189828258) is pinned to `724d84a`, not HEAD. Verified NOT stale: `prd_index.json` does read `next_prd: 271` / `latest_complete: 270`, as PROJECT_STATE claims. **Next authority:** none required — PRD-272's closeout is already written and parked, blocked on PRD-271's resolution by the validator's contiguity check. **Confidence:** High.

### CB-29 · The repository records no pointer to the external audit relationship

`OPEN` · **Low** · Source: External Context Brief §2.1. CuttingBoard contains zero references to `dwats250/strategy` or `EA-ENGINE-AUDIT-PROGRAM-REV3`. The strategy repo (pinned `934ae8b`) names CuttingBoard extensively — `audits/cuttingboard-engine-strategy-audit/`, `plans/EA-ENGINE-AUDIT-PROGRAM-REV3.md`, `docs/INTERFACE_CHARTER_v0.1.md`, `docs/owner-decisions-2026-07-30.md` — and treats it as a read-only evidence source and forbidden mutation target. Meanwhile CuttingBoard holds one half of that conversation: `docs/audit/gate_recon_2026-06-12.md` ("produced for an externally designed strategic gate-alignment audit"), `audits/stage0-recon-2026-07-20/` (governed by a Charter **not in this repo**, citing its §11, §14, invariants I1–I4 and a Q1–Q28 partition), and `audits/FINDINGS.md` ("the plan file lives outside the repo"). **Cross-repository note, per the charter:** strategy-side owner decisions have NO adoption record in CuttingBoard's `docs/DECISIONS.md`, and none of them authorize a CuttingBoard change. **Next authority:** Dustin decision. **Confidence:** High.

### CB-30 · Held mediums and lows not re-verified this pass

`UNKNOWN` · **Medium (candidate)** · `RECONCILED_FINDINGS.md` Tiers 6–7: F-09 (Gate 9 cannot fail), F-10 (`chain_validation` host-local `date.today()`), F-11 (triplicated pipeline stage sequence), F-12 (commit-resolvability skipped), F-13 (unpinned action tags / no lockfile / floating model id), F-14 (terminal truth derived twice), F-16 (fixture mode via `unittest.mock.patch`), F-17 (silent-default state readers), F-18 (adjusted OHLCV mixed with unadjusted quotes), F-19–F-23, plus the three Codex-miss items (daily-workflow DST, cross-process Telegram dedup, ORB bar-count). **These were explicitly NOT investigated in this pass** — Pass 1 triage placed them below the Critical/High verification budget, and no lane was asked to run them to ground. **`UNKNOWN` is the honest status: their historical text is on record, their current truth is not.** **What would resolve it:** one targeted sweep per item against HEAD, of the kind run for CB-01…CB-15. **Next authority:** Dustin decision on whether that sweep is worth commissioning. **Confidence:** High that they are unverified; no confidence either way on their current truth.

---

## Status counts

| Status | Rows |
|---|---|
| `OPEN` — Critical | 2 (CB-01, CB-02) |
| `OPEN` — High | 9 (CB-03…CB-11) |
| `PARTIAL` — High | 1 (CB-12) |
| `PARTIAL` — Medium | 1 (CB-12b) |
| `FIXED` | 3 (CB-13, CB-14, CB-15) |
| `SUPERSEDED` | 0 |
| `OPEN` — Medium | 9 (CB-16, CB-18, CB-19, CB-20, CB-21, CB-22, CB-23, CB-24, CB-25) |
| `OPEN` — Low | 5 (CB-17, CB-26, CB-27, CB-28, CB-29) |
| `UNKNOWN` | 1 (CB-30, covering ~19 historical mediums/lows) |

No row carries more than one status. Every Critical and High row above cites
current code at `9e6b772` that the lead read directly.
