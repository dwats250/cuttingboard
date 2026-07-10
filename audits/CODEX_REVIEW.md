# Independent review report

*Source: GPT-5.6 / Codex, independent second reviewer (read-only), reviewed against main@7f1ff20. Reproduced verbatim as the evidence trail for the reconciled findings. Contains two parts: the full independent review, and the 2A/2B/2D arithmetic verify follow-up.*

## Scope confirmation

I kept the repository read-only. The local worktree remained on `main` with pre-existing edits; I did not check out or fetch the audit branch.

Read-only GitHub inspection confirmed:

- `claude/cuttingboard-architecture-audit-it5mo6` → `051f3372b53bc4361aa1466ad573426c7de09f77`
- Ledger loaded from `audits/FINDINGS.md` at that ref.
- Audited source is `main@7f1ff20cf60ab36519f394ea3a39657738461da6`.
- GitHub comparison shows the audit branch differs from `7f1ff20` only by `audits/FINDINGS.md`.
- All F-01 through F-23 claims were reviewed.
- No tests were run because tests would create cache/temp artifacts, violating the no-write requirement.

## Finding-by-finding verdicts

### F-01 — SOUND

- Severity: Critical is inflated. Proposed: **High**.
- Evidence: `runtime/__init__.py:356-452` fetches, computes regime, qualifies, and builds hourly candidate lines without `_kill_switch`; daily enforcement is at `runtime/__init__.py:913-931`. The hourly summary hardcodes `False` at `runtime/__init__.py:1946`.
- Operational consequence is confirmed: `notifications/formatter.py:81-117` can emit `Tradable: Yes` and a `<symbol> <direction> READY` title.
- Not a documented exception to the kill-switch doctrine.

### F-02 — SOUND

- Severity: **High is justified**.
- Evidence: `ingestion.py:303-312` substitutes `0.0` when `previous_close` is unavailable. `validation.py:161-219` accepts zero. `_kill_switch` consumes SPY/VIX changes at `runtime/__init__.py:2165-2174`; `regime.py:163-173` consumes the same values.
- There is an additional zero fabrication at `normalization.py:96-115` for NaN percent changes.

### F-03 — SOUND

- Severity: High is inflated. Proposed: **Medium**.
- Evidence: `audit.py:90-180` records derived decisions, not raw quotes/frames; `contract.py:306-375` likewise materializes derived candidates. OHLCV is fetched against the current clock and cached by symbol at `ingestion.py:325-390`.
- Fixture input at `runtime/__init__.py:1626-1717` contains quotes only and monkeypatches current cache access. `--date` merely resolves a label at `runtime/__init__.py:2220-2261`; it does not select historical inputs.
- This is an auditability gap, not an immediate execution failure.

### F-04 — SOUND

- Severity: High is inflated. Proposed: **Medium**.
- Evidence: `tools/validate_prd_registry.py:26` is case-sensitive; `:343-379` trusts the PRD's lane text and checks only the existence/name of a review artifact. Artifact contents are never opened.
- `:224-243` exempts missing history docs when the registry File cell is blank or `—`; `:358-360` then skips the second-model check if that doc is absent.
- The "declare STANDARD" case is a semantic-process bypass, not a regex bug, but the empty-artifact and docless-row bypasses are concrete.

### F-05 — SOUND

- Severity: High is somewhat inflated. Proposed: **Medium**.
- Evidence: `CLAUDE.md:43-59` makes ordinary merges automatic and governance changes manual by convention. `.claude/hooks/protect_files.sh:17-32` does not protect `CLAUDE.md` or `.claude/skills`; `:50-75` uses suffix matching.
- No `CODEOWNERS` exists in the audited tree. `.github/workflows/ci.yml:11-22` provides only the `test` job.
- Unlike the original audit, I inspected live GitHub settings: main requires only `test`; there are no required approvals, conversation resolution, or enabled rulesets, and admin enforcement is disabled. Therefore the conclusion is currently supportable.

### F-06 — OVERSTATED

- Severity: High is inflated. Proposed: **Medium**.
- Real portion: `runtime/__init__.py:1728-1778`, `:2010-2016`, and `delivery/transport.py:80-83` perform in-place writes. A torn market map is rejected at `runtime/__init__.py:1996-2007`, creating the described wedge.
- Incorrect/overstated portion: the cited `hourly_alert.yml:386-388` does not exist; the file is only 216 lines. GitHub Actions jobs use separate runner filesystems, so they do not concurrently append to one open local `audit.jsonl`.
- Cross-workflow publication is explicitly reconciled through delta append and retry at `tools/ci_push_artifacts.sh:5-19,71-115`. Unlocked local-process appends remain possible, but that is not the scheduled-workflow topology described.

### F-07 — SOUND

- Severity: **Medium is justified**.
- Evidence: `runtime/__init__.py:1355-1362` converts every exception to `UNKNOWN`; `execution_policy.py:239-251` treats `UNKNOWN` as fully allowed at the ordinary confidence-derived size.
- This can remove directional blocking or macro size reductions. A warning log is not equivalent to decision-surface visibility.

### F-08 — SOUND — DELIBERATE DESIGN

- Severity: **Medium is justified**.
- Evidence: `alert_runner.py:42-122` deliberately returns zero for every exception. `hourly_alert.yml:106-125` treats absent/stale payloads as successful suppression, and readiness is skipped at `:159-161`.
- More seriously, ordinary runtime exceptions are caught at `runtime/__init__.py:561-609` and converted into fresh ERROR/HALT artifacts. `scripts/check_readiness.py:14-17,46-53` checks only field presence, not whether status is ERROR/HALT, so even a fresh failure artifact can publish green.
- The exit-zero behavior is explicitly documented in the runner docstring; it is deliberate, though operationally unsafe.

### F-09 — SOUND — DELIBERATE DESIGN

- Severity: Medium is inflated. Proposed: **Low**.
- Evidence: production candidate construction always sets `has_earnings_soon=None` at `options.py:382-390`; `qualification.py:448-456` passes and records the gate as skipped.
- This is explicitly documented as fail-open in `qualification.py:1-12` and in the gate comment. The gate is unrealizable in production, but this is a known design choice, not a newly discovered defect.

### F-10 — SOUND

- Severity: Medium is inflated. Proposed: **Low**.
- Evidence: `chain_validation.py:143-158` uses host-local `date.today()`; `:201-213` uses it for expiry selection and DTE.
- It can shift DTE during ET evenings on UTC hosts, but scheduled trading-window runs largely avoid the boundary. Manual/off-hours runs remain exposed.

### F-11 — SOUND

- Severity: **Medium is justified**.
- Evidence: two near-identical hourly branches exist at `runtime/__init__.py:391-452`; the full daily sequence is independently maintained at `:910-1023`.
- F-01 is concrete evidence of behavioral divergence, not merely hypothetical refactoring risk.

### F-12 — SOUND

- Severity: Medium is inflated. Proposed: **Low**.
- Evidence: CI disables resolution globally at `.github/workflows/ci.yml:19`; the validator skip is unconditional at `validate_prd_registry.py:393-399`. `prd_close.sh:157-178,299-304` copies the caller-provided token without proving it resolves.
- `PROJECT_STATE.md:109-122` documents the waiver as historical, so the implementation is broader than the stated decision.
- Current `#PR` closeout tokens reduce practical incidence, making this governance hygiene rather than live-system risk.

### F-13 — SOUND, with bundled-risk inflation

- Severity: **Medium is justified overall**.
- Evidence: workflows use mutable major tags, e.g. `ci.yml:15-16`, `cuttingboard.yml:63-70`, `hourly_alert.yml:49-57`, and `macro_awareness.yml:32-40`. `pyproject.toml:6-20` has lower bounds and no lockfile exists. `macro_awareness_collector.py:46` uses an undated model identifier.
- The model leg is operationally weak because that producer is manual-only and has no consumer. Dependency and action drift are the material parts.

### F-14 — SOUND

- Severity: Medium is inflated. Proposed: **Low**.
- Evidence: summary truth is independently rebuilt at `runtime/__init__.py:1204-1279`, while contract truth is constructed at `:704-837`. `verify_run_summary` at `:1470-1597` checks only summary-internal relationships.
- No present mismatch was demonstrated. This is architectural duplication and drift risk, not a current terminal-state defect.

### F-15 — SOUND

- Severity: Medium is inflated. Proposed: **Low**.
- Evidence: `sidecar_doctrine.md:17-23` explicitly defines decision-feeding sidecars. `:43-63` says anything affecting a decision or sizing is not a sidecar and may not inject contract fields. `:83-97` again forbids reads into execution policy.
- Runtime nevertheless applies market-map-derived overnight fields at `runtime/__init__.py:779-783`.
- This is a genuine documentation/governance contradiction, not evidence that current decision arithmetic is wrong.

### F-16 — OVERSTATED — DELIBERATE DESIGN

- Severity: Medium is inflated. Proposed: **Low**.
- Evidence: `runtime/__init__.py:1662-1678` patches exactly two current OHLCV import paths; `:1697-1717` patches validation's clock.
- A future direct import could escape the patch, but no current escape was identified. This is a consciously implemented fixture mechanism with maintenance risk, not a present production defect.

### F-17 — OVERSTATED

- Severity: Medium is inflated. Proposed: **Low**.
- Evidence matching the claim: `dashboard_renderer.py:1088-1094`, `regime_history.py:81-92`, and `runtime/__init__.py:1781-1810` fail soft.
- The assertion that all JSONL readers silently discard damage is false. `execution_policy.py:315-326` raises on malformed JSON or non-object records; `evaluation.py:93-104` also fails loudly.
- Most cited readers are optional presentation/evaluation surfaces where fail-soft behavior appears intentional.

### F-18 — CANNOT DETERMINE

- Severity: assigned Medium is unsupported. Proposed: **Low pending proof**.
- Evidence: `ingestion.py:325-338` uses adjusted history; `ingestion.py:288-322` uses the live `fast_info` quote; `qualification.py:458-472,642-700` combines them.
- Code inspection alone does not establish the alleged ex-dividend basis offset. Back-adjusted history is normally expressed on the contemporary price scale, which may make this comparison appropriate.
- Needed: an exact-version yfinance capture across a split/ex-dividend event, comparing live price, adjusted final close, EMA/ATR, and a demonstrated threshold flip.

### F-19 — SOUND

- Severity: **Low is justified**.
- Evidence: `runtime/__init__.py:847` freezes `run_at_utc` only for `MODE_FIXTURE`; `:2296-2297` treats Sunday-with-fixture as fixture-backed, and `:1697-1717` still freezes validation.
- The ledger correctly calls it harmless today.

### F-20 — OVERSTATED — DELIBERATE DESIGN

- Severity: Proposed: **Informational/Low**.
- Evidence: the snapshot has no consumer; `artifact_flow_map.md:134-147` explicitly records that fact.
- But `.github/workflows/macro_awareness.yml:1-6` is `workflow_dispatch`-only and explicitly says not to schedule it until PRD-188 supplies the consumer. Calling this a "running producer" is misleading.
- This is a documented staged design with an anti-orphan activation gate, not an active resource drain.

### F-21 — UNSOUND

- Severity: **None for the stated defect**.
- Evidence directly contradicts the claim: `sector_router.py:25-38` discards `quotes`, `derived`, and `state_path`, then always returns `MIXED`, `0.0`, `0.0`. It neither computes scores nor reads/writes a state file.
- `runtime/__init__.py:2300-2303` merely returns a pathname; it is not persistence.
- A separate real issue exists: `architecture.md:76-77` and `artifact_flow_map.md:180-184,248-252` falsely describe a functioning, persisted router. The actual problem is documentation drift around a stub.

### F-22 — SOUND

- Severity: **Low is justified**.
- Evidence: `.github/workflows/cuttingboard.yml:46-48` and `hourly_alert.yml:37-42` inject the secret. An exact source-archive search found no Python reader.
- This unnecessarily enlarges the environment exposed to workflow steps.

### F-23 — OVERSTATED

- Severity: **Low for the valid hygiene items**.
- Evidence:
  - (a) `output.py:93-107` uses `PYTEST_CURRENT_TEST`, but this is deliberate per-test process-state isolation, not a production defect.
  - (b) `runtime/__init__.py:561-565` writes root-level `traceback.txt`; true.
  - (c) `run_daily.sh:5` disagrees with `runtime/__init__.py:2224-2228`; true. But the claim that Sunday's stale Friday quote then halts on freshness is false: `ingestion.py:235-258` stamps the retrieval clock, which `normalization.py:70-85` and `validation.py:177-200` treat as quote freshness.
  - (d) `runtime/__init__.py:566-571` sends failure notifications without checking mode; true.
  - (e) `architecture.md:97-100` says fixture chains are VALIDATED, while `runtime/__init__.py:1681-1694` emits MANUAL_CHECK; true.
- The incorrect freshness consequence conceals a more serious missed defect described below.

## 1. False positives and dressed-up non-issues

- **F-21 is the clearest false positive.** There is no router computation or persistence.
- **F-18 is unsupported.** The audit identifies two data sources but does not prove a basis mismatch or threshold flip.
- **F-20 mischaracterizes intentionally dormant, manual-only scaffolding as a running orphan.**
- **F-09 treats an explicit fail-open product decision as if it were an undisclosed defect.**
- **F-16 promotes a hypothetical future monkeypatch escape to Medium despite finding no current escape.**
- **F-14 is ordinary duplication debt without an observed inconsistency.**
- **F-06's GitHub concurrency story is wrong:** scheduled jobs do not share an open filesystem log, and the publish path has explicit delta reconciliation.
- **F-17's "all JSONL readers" language is false.**
- **F-23(a) is test isolation, not production leakage.**

## 2. Important misses

### A. Credit-spread maximum risk is arithmetically wrong — High

`options.py:263-279` chooses bull-put and bear-call **credit** spreads in elevated/high IV. Yet `options.py:11-17,64-69` assigns every strategy an estimated "debit" equal to 30% of strike width, and `qualification.py:417-442` treats that amount as maximum risk.

For a $5-wide credit spread collecting an estimated $1.50, maximum loss is approximately `$5.00 - $1.50 = $3.50/share`, not `$1.50/share`. The system can therefore call roughly $350 of exposure "max risk $150."

The chain gate does not repair this. `chain_validation.py:222-244` selects one highest-OI near-ATM contract and validates that single option; it never selects both proposed legs or computes the spread's live net credit/debit and max loss. `output.py:345-350` then prints the estimated contract count and "max risk" to the trader.

### B. Policy size multipliers do not resize the trade — High

`execution_policy.py:59-68,179-185` computes and attaches a `0.50/0.75/1.00` multiplier. It does not change `contracts` or `dollar_risk`.

`output.py:345-350` prints the unmodified `OptionSetup.max_contracts` and `dollar_risk`. `contract.py:336-365` is worse: it exports `QualificationResult.max_contracts/dollar_risk`, predating both the correlation adjustment and execution-policy multiplier, while carrying `size_multiplier` separately.

Thus a policy intended to cut risk by 25–50% can still present the full contract count/max-risk line.

### C. "Freshness" measures retrieval time, not market-data time — High

`ingestion.py:235-258` assigns `fetched_at_utc=datetime.now()` before fetching and stores that local retrieval time on the quote. No exchange/provider event timestamp is collected.

`normalization.py:70-85` and `validation.py:177-200` then prove only that the program fetched recently—not that the quoted market observation is recent. Weekend, holiday, delayed-feed, or after-hours stale values can pass the five-minute freshness gate.

This invalidates F-23's assertion that a Sunday-morning live run safely halts on Friday staleness and weakens every "fresh-data" guarantee in the audit.

### D. Execution-policy session state treats recommendations as actual trades — High

`execution_policy.py:71-114` increments `prior_trade_count` for every prior `ALLOW_TRADE` audit decision and treats the pipeline run timestamp as `last_trade_at_utc`. There is no fill or user-entry evidence.

`evaluation.py:37-71,114-137` evaluates every prior recommendation as a hypothetical trade. `execution_policy.py:283-312` then turns those hypothetical results into loss lockouts.

The real manual journal is explicitly isolated from runtime at `manual_journal.py:1-6`. Therefore "max trades," cooldown, and consecutive-loss lockout describe recommendations, not the trader's actual positions. This can block valid later setups or manufacture a loss lockout after trades the user never took.

### E. Expansion confidence inflates under missing optional data — Medium/High

`regime.py:107-122` computes breadth only over symbols that survived validation, with no minimum coverage count. If missing symbols are disproportionately decliners, the denominator shrinks and breadth rises.

When the reduced set passes, `regime.py:139-154` returns `EXPANSION` with `confidence=1.0`, `total_votes=0`, and an empty vote breakdown. There is no evidence-completeness penalty. This is especially dangerous alongside F-02's fabricated zero changes.

### F. Fresh ERROR artifacts still produce a green hourly workflow — Medium/High

The audit focused on absent payloads. It missed the more direct case:

- `runtime/__init__.py:561-609` catches an exception and writes fresh ERROR/HALT artifacts.
- `delivery/payload.py:147-153` accepts `ERROR` as valid.
- `scripts/check_readiness.py:14-17,46-53` checks only that `status` and `outcome` keys exist.
- `hourly_alert.yml:134-185` can therefore render, pass readiness, commit, and publish a failed run while the workflow remains green.

### G. Daily scheduling is not DST-correct — Medium

`.github/workflows/cuttingboard.yml:5-10` equates fixed `13:00 UTC` with `06:00 PT / 09:00 ET`. That is true during daylight time, but during standard time it runs at `05:00 PT / 08:00 ET`.

The hourly workflow explicitly carries dual UTC schedules for DST at `hourly_alert.yml:5-18`; the daily pipeline does not. In summer, both daily and hourly jobs also launch at `13:00 UTC`.

### H. Notification coordination is only process-local — Medium

`output.py:57-65,93-120` keeps rate limits and message hashes in module globals. Daily and hourly workflows have different concurrency groups and share the same Telegram credentials, with overlapping summer schedules.

There is no cross-process Telegram rate limiter or shared logical-alert deduplication. The two paths also use different persisted state mechanisms (`notifications/state.py` versus `notifications/hourly_slot.py`).

### I. The "sector router" is actually a stub, and canonical docs are false — Low/Medium

The audit accused it of excessive state machinery. The opposite is true: `sector_router.py:25-38` does nothing. Canonical architecture and artifact documentation nevertheless describe computed modes and persisted continuity. This is precisely the docs-versus-code drift the audit claimed to check.

### J. ORB window semantics require targeted verification — CANNOT DETERMINE

`intraday_state_engine.py:32-35,124-142` defines the five-minute ORB as 09:30 through 09:35 inclusive. With start-stamped one-minute bars, that is six bars, not five. Determination requires one captured yfinance frame proving whether its timestamps label interval starts or ends.

## 3. Independent top five by live operational risk

1. **Credit-spread risk and chain validation:** the tool can understate maximum loss and validate a different single contract than the proposed two-leg spread.
2. **Retrieval-time "freshness":** stale weekend/holiday/delayed market observations can be certified fresh throughout the system.
3. **Policy sizing is not materialized:** intended 25–50% risk cuts do not change the displayed contract count or max-risk amount.
4. **F-01 hourly kill-switch bypass:** the phone can receive a `READY` alert during conditions the canonical pipeline defines as a terminal HALT.
5. **Recommendations treated as actual trades/losses:** cooldown, daily limits, and loss lockouts are driven by hypothetical decisions rather than user fills.

---

# Verify-only follow-up (2A / 2B / 2D)

Confirmed present at `main@7f1ff20`:

- `cuttingboard/options.py`
- `cuttingboard/execution_policy.py`
- `cuttingboard/qualification.py`
- `cuttingboard/chain_validation.py`
- `cuttingboard/evaluation.py`
- `cuttingboard/contract.py`
- `cuttingboard/output.py`
- `cuttingboard/manual_journal.py`

## MISS 2A — Credit-spread max risk is understated

**Verdict: CONFIRMED**

### 1. High IV selects credit spreads

`options.py:263-279` explicitly says and implements:

```text
266 Debit spreads are preferred in low/normal IV
267 Credit spreads are preferred in elevated/high IV
269 LONG + LOW_IV / NORMAL_IV       -> BULL_CALL_SPREAD (debit)
270 LONG + ELEVATED_IV / HIGH_IV    -> BULL_PUT_SPREAD (credit)
271 SHORT + LOW_IV / NORMAL_IV      -> BEAR_PUT_SPREAD (debit)
272 SHORT + ELEVATED_IV / HIGH_IV   -> BEAR_CALL_SPREAD (credit)
274 high_iv = iv_environment in (ELEVATED_IV, HIGH_IV)
276 if direction == "LONG":
277     return BULL_PUT_SPREAD if high_iv else BULL_CALL_SPREAD
279 return BEAR_CALL_SPREAD if high_iv else BEAR_PUT_SPREAD
```

So both requested credit strategies are confirmed.

### 2. Thirty percent of width is treated as risk regardless of strategy

`options.py:11-17,64-69` defines one generic debit proxy:

```text
13 TradeCandidate.spread_width = estimated net DEBIT per share
16 Max strike distances: $5.00 for index ETFs ...
17 Estimated debit = 30% of strike distance
65 _MAX_STRIKE_DIST_ETF = 5.0
67 _DEBIT_PCT_OF_WIDTH = 0.30
69 _EXIT_LOSS = "full_debit"
```

After selecting the strategy, `options.py:206-209` reuses the same candidate value:

```text
206 strike_distance = ...
209 spread_width = candidate.spread_width ...
```

There is no credit-strategy-specific maximum-loss calculation.

`qualification.py:417-442` treats this value as total risk:

```text
425 spread_cost = candidate.spread_width * 100
430 max_c = math.floor(effective_target / spread_cost)
439 dr = max_c * spread_cost
440 max_contracts = max_c
441 dollar_risk = dr
```

Confirmed: the same 30%-of-width proxy becomes `dollar_risk` for debit and credit strategies.

### 3. Chain validation evaluates one contract, not both spread legs

`chain_validation.py:222-244`:

```text
223 opt_type = _OPTION_TYPE.get(setup.strategy, "calls")
225 chain_df = _get_chain_df(...)
233 near_atm = _filter_near_atm(...)
237 best_row = _find_best_contract(near_atm)
241 # Structural pricing sanity (per-contract)
242 ev = _eval_contract(best_row)
```

It selects one option type, finds one highest-OI near-ATM row, and evaluates that single contract. It does not:

- resolve both proposed strikes;
- price the long and short legs;
- compute net credit/debit;
- calculate spread maximum loss.

Later consistency checks inspect surrounding rows, but they still do not construct or price the proposed two-leg spread.

### 4. Worked example

Assume a $5-wide bull-put spread and a $1.50 credit:

- System proxy: `5.00 x 0.30 = $1.50/share`
- System risk per contract: `$1.50 x 100 = $150`
- True credit-spread maximum loss:
  `($5.00 width - $1.50 credit) x 100 = $350`
- Understatement: `$350 - $150 = $200 per contract`
- Actual maximum loss is about `2.33x` the reported amount.

With the default $150 risk budget, Gate 8 allows one contract and records `$150` risk.

`output.py:345-350` prints:

```text
345 contracts = setup.max_contracts
346 risk = setup.dollar_risk
348 "{contracts} contract..."
349 "max risk ${risk:.0f}"
```

The surface therefore reports:

```text
1 contract - max risk $150
```

For the stated $1.50 credit, actual maximum loss is `$350`.

One nuance makes this worse, not better: the system never establishes that the live credit is actually $1.50. That value is an estimated debit proxy reused for a credit strategy.

---

## MISS 2B — Policy size multiplier does not resize the trade

**Verdict: CONFIRMED**

### 1. Multiplier is computed but contracts/risk are untouched

`execution_policy.py:59-68`:

```text
59 def size_multiplier_for_confidence(confidence):
60     """Return deterministic R-size multiplier for regime confidence."""
61     confidence = float(confidence)
62     if confidence < 0.60:
63         return 0.0
64     if confidence >= 0.80:
65         return 1.0
66     if confidence >= 0.70:
67         return 0.75
68     return 0.50
```

For an allowed decision, `execution_policy.py:179-185` performs:

```text
179 if result.allowed:
180     return replace(
181         decision,
182         policy_allowed=True,
183         policy_reason=result.reason,
184         size_multiplier=result.size_multiplier,
185     )
```

The replacement changes only:

- `policy_allowed`
- `policy_reason`
- `size_multiplier`

It does not mutate `contracts` or `dollar_risk`.

Macro pressure can further reduce the multiplier. For example, `execution_policy.py:239-247` allows a SHORT under `RISK_OFF` with `size * 0.5`, but that result still only reaches `TradeDecision.size_multiplier`.

### 2. Output and contract retain pre-policy sizing

`output.py:345-350` renders the `OptionSetup` values:

```text
345 contracts = setup.max_contracts
346 risk = setup.dollar_risk
348 "{contracts} contract..."
349 "max risk ${risk:.0f}"
```

`OptionSetup` is built before `_run_decision_gates` applies execution policy.

`contract.py:336-365` is even further upstream:

```text
336 position_size aliases result.max_contracts
337 dollar_risk forwards result.dollar_risk
356 policy_allowed = decision.policy_allowed
358 size_multiplier = float(decision.size_multiplier)
359 position_size = int(result.max_contracts)
362 dollar_risk = float(result.dollar_risk)
```

Thus the contract can contain, simultaneously:

```json
{
  "size_multiplier": 0.5,
  "position_size": 2,
  "dollar_risk": 150.0
}
```

It does not materialize `1 contract / $75`.

Also, `result.max_contracts` predates the correlation adjustment applied while building `OptionSetup`, so the contract sizing can predate both correlation and execution-policy reductions. The markdown report at least uses the correlation-adjusted setup, but still ignores execution policy.

### 3. Worked example

Assume:

- Setup: `N = 2 contracts`
- Setup risk: `X = $150`
- Policy returns `size_multiplier = 0.50`
- No other adjustment changes the setup

The intended arithmetic would be:

- Contracts: `2 x 0.50 = 1`
- Risk: `$150 x 0.50 = $75`

Actual code behavior:

- `TradeDecision.contracts` remains `2`
- `TradeDecision.dollar_risk` remains `$150`
- `size_multiplier` becomes `0.50`
- Markdown output prints `2 contracts - max risk $150`
- Contract exports `position_size: 2`, `dollar_risk: 150.0`, and `size_multiplier: 0.5`

Therefore the trader-facing report does not show the policy-adjusted `1 contract / $75`. The multiplier is descriptive metadata, not materialized sizing.

---

## MISS 2D — Recommendations are treated as actual trades

**Verdict: CONFIRMED**

### 1. ALLOW decisions become trade count and trade time without fill evidence

`execution_policy.py:71-114` accepts only audit and evaluation logs—no fills or manual journal:

```text
71 def load_execution_session_state(
75     audit_log_path,
76     evaluation_log_path,
...
91 trade_decisions = record.get("trade_decisions") or []
94 allow_count = sum(
98     decision.get("decision_status") == ALLOW_TRADE
99 )
100 if allow_count:
101     prior_trade_count += allow_count
102     if ...:
103         last_trade_at_utc = record_run_at
```

Confirmed:

- Every prior `ALLOW_TRADE` recommendation increments `prior_trade_count`.
- `last_trade_at_utc` is the pipeline run timestamp.
- No execution, fill, broker, or journal record is checked.

The resulting policy checks are:

```text
execution_policy.py:224-229
224 if prior_trade_count >= MAX_TRADES_PER_DAY: block
226 if consecutive_losses >= 2: block
228 if cooldown_active(timestamp, last_trade_at_utc): block
```

### 2. Hypothetical recommendations feed loss lockout

`evaluation.py:37-71` loads the most recent prior audit run and evaluates its ALLOW candidates:

```text
45 Evaluate the most recent same-day prior run
53 candidates = extract_allow_trade_candidates(prior_record)
57 records = build_evaluation_records(...)
67 append_evaluation_records(records, ...)
```

`evaluation.py:114-137` selects candidates solely from recommendation status:

```text
114 def extract_allow_trade_candidates(...)
115 Return persisted ALLOW_TRADE candidates
128 if raw.get("decision_status") == "ALLOW_TRADE":
129     candidate = {
130         "symbol": ...
132         "entry": ...
133         "stop": ...
134         "target": ...
136     candidates.append(candidate)
```

`evaluation.py:183-223` then evaluates market bars, not an executed position. A bar touching the proposed stop becomes `STOP_HIT`.

`execution_policy.py:283-312` consumes those hypothetical evaluations:

```text
293 for record in evaluation_log:
304 losing = result == "STOP_HIT" or R_multiple < 0
307 records.append(... losing)
309 consecutive = 0
310 for ... losing in sorted(records):
311     consecutive = consecutive + 1 if losing else 0
```

Two hypothetical losing recommendations therefore produce `consecutive_losses == 2`, which triggers the lockout.

### 3. Manual journal isolation and concrete path

`manual_journal.py:1-6` states:

```text
2 Append-only manual trade journal writer.
4 Writes validated records to logs/manual_trades.jsonl.
5 This module must NOT be imported by any runtime, contract, or delivery module.
```

More importantly, the actual session-state function accepts and reads only `audit.jsonl` and `evaluation.jsonl`. It has no journal/fill input, so manual `ENTERED`, `SKIPPED`, or `CANCELLED` records cannot affect this policy path.

#### Cooldown example

- 09:00: pipeline emits one `ALLOW_TRADE` recommendation for AAPL.
- User does **not** enter it.
- 09:05: another full pipeline run loads the 09:00 audit record.
- `allow_count = 1`
- `prior_trade_count = 1`
- `last_trade_at_utc = 09:00`
- Five minutes is inside the configured 15-minute cooldown.
- The 09:05 candidate is blocked for cooldown despite no trade occurring.

#### Daily-limit example

- 09:00 audit contains two `ALLOW_TRADE` recommendations.
- User takes neither.
- Next full run computes `prior_trade_count = 2`.
- `prior_trade_count >= MAX_TRADES_PER_DAY` blocks further decisions.
- The system has treated two recommendations as two completed trades.

#### Consecutive-loss example

- Prior run recommends AAPL and NVDA; user takes neither.
- A later run evaluates forward bars for both recommendations.
- Both proposed stops are touched, producing two `STOP_HIT` evaluation records.
- `_load_consecutive_losses` returns `2`.
- The next full run triggers `POLICY_LOSS_LOCKOUT`.

So yes: cooldown, trade-limit, and loss lockout can all trigger from trades the user never took.
