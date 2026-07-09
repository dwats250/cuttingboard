# CuttingBoard — Fable Audit Findings Ledger

**Date:** 2026-07-09
**Auditor:** Claude Code (Fable window), read-only, branch `claude/cuttingboard-architecture-audit-it5mo6`
**Audited tree:** `main` @ `7f1ff20` (PRD-250 merge)
**Plan of record:** *CuttingBoard — Fable Audit Plan* (10 items, 4 phases, cross-cutting lenses, time-box triage; supplied by Dustin in-session — the plan file lives outside the repo). Output per its contract: ranked findings — what, where, severity, spine stage — descriptive not prescriptive, no PRDs, no building. Feeds the GPT-5.6 adversarial review pass.

**Spine:** evidence → questions → state → attention → terminal decision → explanation → governance.

**Method.** Direct read of the full runtime orchestrator, validation/ingestion/qualification/options/execution-policy layers, sidecar doctrine, hooks, and workflows; three read-only recon sweeps (governance guards, state/artifacts, nondeterminism/replayability) whose decisive claims were each re-verified in code by the main auditor (CLAUDE.md author-discipline 4). Settled decisions in `docs/DECISIONS.md` were not re-litigated; findings against them appear only where code exceeds a decision's own stated scope. Time-box triage: the two must-land passes (#2 dependency, #3 run-trace) landed in full; all ten items were executed this window.

---

## Part A — Verdicts per plan item

### Phase 1 — Architecture foundations

**1. Mantra sanity check.** The spine is the right frame — with one big caveat. `_run_pipeline` literally implements *symbols are evidence → questions create state → state governs attention → attention precedes execution*: frozen-dataclass evidence objects, regime/qualification state, a watch/attention layer, terminal TRADE/NO_TRADE/HALT, templated explanation, validated contract. `docs/architecture.md` names `_run_pipeline` as its own source of truth and matches it. **The caveat: the codebase contains a second, truncated spine.** The hourly path (`_execute_notify_run`) jumps evidence → attention, skipping the kill switch, the decision gates, and contract validation, and pushes candidate attention to Telegram (findings F-01, F-11). Auditing only along the documented spine would have missed the path that violates it — the gut-check earned its place. Second, smaller caveat: "questions create state" holds for Q1/Q3/Q4 but Q2 ("what matters today") mostly *decorates outputs* rather than creating state — red-folder is render-only, macro drivers are display fields; `macro_pressure` is the lone Q2 input that gates anything (and its failure mode is F-07).

**2. Dependency audit.** Module graph is clean overall: `runtime/` is the sole orchestrator, `delivery/` consumes downstream-only, `contract_types` is a proper leaf; the one import cycle (`qualification ↔ flow`) is TYPE_CHECKING-only, benign. State flow and mutation sequence are centralized in `_run_pipeline` → `_run_decision_gates` → `_build_and_finalize_contract`, with the PRD-233 validator guarding the injection cluster — good. The structural risks found: the same pipeline stage sequence is maintained **three times** in one file (F-11); terminal-state truth is derived **twice in parallel** (contract vs run summary, F-14); and `output.py` mixes report rendering, Telegram transport, and module-global dedup state, with `delivery/html_renderer.py` importing back into it — the one blurred boundary. Feedback loops: execution policy reads prior-run state from `audit.jsonl`/`evaluation.jsonl` (declared, traceable); notification dedup state feeds the next run's send decision (declared). No hidden cycles found.

**3. Run-trace / replayability audit.** For any past TRADE / NO_TRADE / HALT: the **reason chain is reconstructable** (gate-by-gate `decision_trace`, block reasons, regime fields, chain classifications persist in the audit record, contract, and summary). The **run is not**: no raw input is persisted anywhere — quotes, OHLCV frames (cache overwritten next weekday), intraday bars, chain OI/spread, flow snapshot contents, validation clock all discarded; `--date` relabels current data rather than replaying; fixture mode cannot restore OHLCV/chain/intraday/flow fidelity even in principle (F-03). Silent-degradation catches from the trace: evidence can be fabricated as calm (`pct_change=0.0` fallback, F-02) and a decision-gate input degrades to fail-open on exception (F-07).

### Phase 2 — State and integrity

**4. State formation & integrity.** Formation is disciplined: derived metrics only from validated quotes, frozen intermediate dataclasses, a TypedDict contract validated twice per run with an enforced `system_state` key whitelist. Integrity is where it cracks: the most load-bearing artifacts are written non-atomically while less-critical sidecars get temp+rename (F-06); duplicate truth exists between contract and summary, reconciled only by a self-check (F-14); silent fallbacks sit under the kill switch (F-02), under the macro-pressure gate input (F-07), and in several state readers (F-17); shared JSONL logs take unlocked appends from two concurrent processes (F-06); `verify_run_summary` reads the field written after decision authority closed (`_rewrite_summary_file` bypasses the newer-timestamp guard). Schema versioning exists only on the contract.

### Phase 3 — Governance

**5. Governance invariant enforcement (six bindings vs actual code).** Every binding has at least one live loophole: **fail-loud** — F-02, F-06 (torn appends), F-07, F-08, F-16; **assert resolved state** — F-01 (`kill_switch: False` literal), F-12 (unverified closeout hash); **authoritative source** — F-04 (filename as artifact), F-14 (summary self-check); **red test per guard** — the guards' happy paths are tested, their bypasses (F-04) and vacuous-greens (F-08) are not; **CI parity** — F-10 (host-local date), F-13 (unlocked deps), F-23a; **pinned identities** — F-13 across all three legs (action tags, dependencies, model id).

**6. Governance alignment pass — could Claude Code merge a violation without being stopped?** **Yes, for at least three classes** (F-05): (a) *governance-guardrail edits* — MANUAL-MERGE-ONLY is pure convention: no CODEOWNERS exists, no CI check inspects changed paths, `CLAUDE.md` and `.claude/skills/` are not in `protect_files.sh`'s protected set, and auto-merge is queued by the same agent the rule constrains; (b) *mislabeled HIGH-RISK work* — the validator keys on a self-declared, case-sensitive LANE header (F-04); (c) *FILES-scope violations* — scope-lock lives in a skill (advisory) and a warn-only pre-commit hook; the one enforcing hook matches FILES paths by loose suffix and binds only the agent's own Write/Edit tools. The only hard gate anywhere is the CI `test` check. The skills (`prd-review-claude`, `prd-closeout-verified`, `scope-lock-precommit`) encode the right process but nothing makes them run.

### Phase 4 — Logic, scope, and red-team

**7. Complexity audit.** Three gravity wells: `runtime/__init__.py` (2,427 lines — acknowledged debt dated 2026-08-15, but the register frames it as file-size; the sharper risk is the triplicated stage logic, F-11), `delivery/dashboard_renderer.py` (3,057 lines; decomposition map written, unexecuted), `output.py` (970 lines, three responsibilities). Parasitic candidates: Gate 9 (cannot fail, F-09), macro_awareness producer (no consumer, F-20), sector_router (display-only state model with its own persisted state file, F-21), `POLYGON_API_KEY` (secret with no reader, F-22). Cuts-before-additions is otherwise visibly practiced (PRD-243's subtraction block, retired detectors, killed PRDs).

**8. Four-question anchor audit.** Q1 (environment): regime, structure/IV, correlation→risk-modifier, kill switch — all anchored. Q3 (tradable): qualification, options, chain validation, decision gates, watch, intraday state — anchored. Q4 (invalidates): invalidation gate, kill switch, overnight policy — anchored. Q2 (matters today): macro drivers/pressure anchored; red-folder render-only (parked entry-gate is the declared path to decision relevance); **macro_awareness serves Q2 in theory but nothing consumes it** (F-20). Serving none of the four: Gate 9 as implemented (F-09 — ceremony that reads as protection), sector_router's persisted state (F-21 — weak Q1-display claim). Evaluation/performance/review-scorecard/manual-journal serve the VISION trap-loop (awareness → changed behavior) — a clear traceability reason, not parasitic. Explanation/visibility maps serve the explanation stage — anchored.

**9. Sidecar doctrine enforcement.** The hunt found one orphan (macro_awareness, F-20), no sidecar *covertly* influencing outcomes — but it found the doctrine itself is internally contradictory about the two that *overtly* do (`macro_pressure` → execution policy; `market_map` → overnight policy → contract injection): the doctrine's own observe-only and no-mutation sections forbid what its categories section declares (F-15). The silent macro-pressure fail-open (F-07) is the operational risk hiding in that ambiguity. `market_map_lifecycle`'s cross-run price backfill is documented and decision-inert (checked — renderer-only).

**10. Mantra adversarial red-team.** *Does the pipeline follow the order?* The daily path does; the hourly path does not — attention is created from partially-formed state (no kill switch, no decision gates) and pushed to the trader's phone (F-01). *Is attention ever created before state?* Yes — that is exactly the hourly path's shape, and notification-suppression state from a *prior* run also gates today's attention (declared, but it means attention is governed by yesterday's state). *Do questions create state or decorate outputs?* Q2 mostly decorates (item 1). *If the doctrine is wrong or incomplete, where does the system fail first?* At the attention layer: the trader acts on what reaches the phone and the dashboard, and both of those channels have a path that skips the state discipline the doctrine promises (F-01) and a failure mode that keeps them silently green/frozen (F-08). Second failure point: the explanation layer — recorded reasons can never be re-derived against archived evidence (F-03), so a wrong explanation is undetectable after the fact.

---

## Part B — Ranked findings ledger

Severity: Critical / High / Medium / Low. Confidence: **[V]** verified in code, **[I]** inferred, **[2L]** needs a second look.

---

### F-01 — Hourly alert path bypasses the market-stress kill switch and hardcodes `kill_switch: False` — **Critical**
- **Where:** `cuttingboard/runtime/__init__.py:356-559` (`_execute_notify_run`); hardcoded literal `runtime/__init__.py:1946`; kill switch evaluated only at `:916` and `:1227` (daily path)
- **Spine stage broken:** state governs attention / terminal decision
- **What:** `_kill_switch` (VIX > 35, VIX pct > 0.15, |SPY pct| > 0.03 — PRD-180) exists only in the daily pipeline. The live hourly path runs fetch → regime → candidates → `qualify_all` and emits candidate lines to Telegram with no market-stress evaluation, then writes `"kill_switch": False` as a literal into its published summary (rendered by `dashboard_renderer.py:2051` via `_req`). On an intraday VIX spike that passes validation (fresh quotes, |pct| < 25%), hourly alerts keep presenting qualified candidates with R:R lines while the daily pipeline, had it run, would HALT. VISION names extreme stress "a hard invalidation"; it is enforced on one of two live channels. **[V]** (call-site absence confirmed by exhaustive grep)

### F-02 — Ingestion silently substitutes `pct_change = 0.0` when `previous_close` is unavailable — **High**
- **Where:** `cuttingboard/ingestion.py:303-312` (`_yfinance_quote_raw`); passes all rules in `validation.py:153-219`; consumed by `runtime/__init__.py:2165-2174` (`_kill_switch`) and `regime.py`
- **Spine stage broken:** evidence
- **What:** a quote with a valid `last_price` but missing `previous_close` is emitted with `pct_change=0.0`, `fetch_succeeded=True`, and a DEBUG-level log. Zero passes every validation rule (`validation.py`'s header says "No silent fallbacks" — the fallback is upstream of it). On SPY or ^VIX during stress, the kill switch's pct-change legs read fabricated calm and regime votes are fed the same. Compounds F-01: the one channel that does check the kill switch can be disarmed by a data hiccup with no operator signal. Invariant: fail-loud. **[V]** mechanism; degraded-mode frequency **[I]**

### F-03 — No raw-input snapshot is ever persisted; runs are explainable but not reproducible; `--date` relabels — **High**
- **Where:** `cuttingboard/audit.py` (`_build_record` — derived fields only); `runtime/__init__.py:1204-1279` (summary — derived only); `ingestion.py:325-338` (OHLCV window always `end=now`, `auto_adjust=True`), `:378-390` (cache symbol-keyed, overwritten); `runtime/__init__.py:2220-2261` (`--date` resolution)
- **Spine stage broken:** evidence / explanation
- **What:** the analysis layer is deterministic given inputs, but the inputs are discarded: raw 22-symbol quotes, the OHLCV frames behind the derived metrics, intraday bars, chain OI/spread, flow contents, and the validation clock are never archived. No capture-to-fixture tool exists; the fixture schema carries 8 quote fields, so even a hand-built replay diverges (current cache, synthesized chain results, skipped ORB/intraday, current flow file). `--date` on a live run fetches today's market and stamps it with the requested date. "Why did it say TRADE on June 12" is answerable only from recorded reason strings, never re-derivable. **[V]**

### F-04 — HIGH-RISK second-model CI gate trusts a self-declared label and a filename; four verified bypasses — **High**
- **Where:** `tools/validate_prd_registry.py:26` (`_LANE_HIGH_RISK_RE`), `:359-371`; `.github/workflows/ci.yml:19`
- **Spine stage broken:** governance
- **What:** the gate CLAUDE.md advertises keys on the PRD doc's own case-sensitive `LANE` header. Bypasses: (a) declare `LANE: STANDARD` — nothing cross-checks lane against change surface; (b) `High-Risk` casing — no `re.IGNORECASE`; (c) header text beyond `[:\s]*\n?\s*` between `LANE` and `HIGH-RISK`; (d) `if not doc.exists(): continue` plus the registry File-cell `—` exemption pass a docless COMPLETE row vacuously. The artifact leg is satisfied by the *existence* of any non-claude-named `PRD-NNN.review.<model>.md` — contents never read, empty file passes; the waiver check matches an inner substring, not the exact documented line. The guard checks for the right words, not correspondence to reality — PRD-198's definition of semantic failure, inside the guard enforcing PRD-198's sibling policy. Invariants: assert-resolved, authoritative-source, red-test (no test covers the bypasses). **[V]**

### F-05 — Merge discipline is convention: Claude Code can auto-merge governance-guardrail changes unstopped — **High**
- **Where:** absence of `CODEOWNERS` (verified repo-wide); `.github/workflows/ci.yml` (only gate: validator/ruff/pytest — no changed-path inspection); `.claude/hooks/protect_files.sh` (protected set: `.env*`, `.git/*`, `*.lock`, `.github/workflows/*`, `secrets*` — `CLAUDE.md` and `.claude/skills/` absent; FILES match by loose suffix; binds only the agent's own Write/Edit); `scripts/pre_commit_sanity.sh` / `install_hooks.sh` (warn-only)
- **Spine stage broken:** governance
- **What:** CLAUDE.md's MANUAL-MERGE-ONLY rule for governance changes (PRD-186) has no technical backstop: no CODEOWNERS, no CI check that a PR touching `CLAUDE.md`/`prd-review-claude` is held, and the agent that queues `gh pr merge --auto` is the same agent the rule constrains. Combined with F-04, the answer to the plan's question — could Claude Code merge a violation without being stopped? — is yes for guardrail edits (convention only), mislabeled HIGH-RISK lanes (regex), and FILES-scope violations (advisory skill + suffix-matched agent-side hook). The process documents are strong; nothing makes them run. **[V]** (branch-protection settings themselves live outside the repo and were not inspectable — **[2L]** whether required-check config adds anything beyond the `test` check)

### F-06 — Load-bearing artifacts written non-atomically; a mid-write kill wedges subsequent runs; shared JSONL appends unlocked — **High**
- **Where:** `runtime/__init__.py:1728-1778` (`safe_write_latest` / `_write_summary_files` / `_rewrite_summary_file` — bare `write_text`), `:2010-2016` (`market_map`); `delivery/transport.py:80-83`; contrast atomic `tmp.replace` at `:2056-2058`, `:2092-2094`, `:2104-2114`; wedge at `:2000-2007` (`_load_previous_market_map` raises on malformed JSON); appends: `audit.py:312-319`, `evaluation.py:256-266`; concurrency deliberately un-serialized (`cuttingboard.yml:32-37` vs `hourly_alert.yml:386-388`)
- **Spine stage broken:** state
- **What:** `latest_run.json`, `latest_contract.json`, `market_map.json`, and the payload/HTML are in-place writes under CI's `timeout 8m` kill timer, while less-critical sidecar snapshots get temp+rename — atomicity applied inversely to criticality. A torn `market_map.json` makes every later daily run raise `RuntimeError` until manually cleared. `_rewrite_summary_file` also bypasses `safe_write_latest`'s newer-timestamp guard. The daily and hourly processes can run concurrently and append to shared `audit.jsonl` with no lock; every JSONL reader silently drops torn lines, so the failure mode is silent record loss. Invariant: fail-loud. **[V]**

### F-07 — Macro-pressure computation failure silently becomes "no macro constraint" at the decision gates — **Medium**
- **Where:** `runtime/__init__.py:1355-1362` (`_compute_overall_pressure`: any exception → `logger.warning` → `"UNKNOWN"`); `execution_policy.py:240-241` (`UNKNOWN` → full allow at full size); `overall_pressure` also feeds `trade_thesis` and `invalidation` gates
- **Spine stage broken:** terminal decision
- **What:** the one Q2 input that actually gates decisions (RISK_OFF blocks LONGs, sizes cut 25–50% otherwise) degrades on any exception to a value the policy treats as "unconstrained, full size," with only a log-level warning. A macro-pressure bug or data change therefore removes a blocking gate silently — the doctrine's "decision-feeding sidecar" without the fail-loud discipline the decision path requires. Invariant: fail-loud / assert-resolved. **[V]**

### F-08 — Hourly failures are structurally invisible: `alert_runner` always exits 0 and the freshness check greens an empty run — **Medium**
- **Where:** `cuttingboard/alert_runner.py:42-122` ("convert all runtime failures to exit 0"; backstop is itself a Telegram send whose failure is swallowed at `:120-121`); `.github/workflows/hourly_alert.yml:108-127` (missing/stale payload → `fresh=false`, `exit 0`; `check_readiness` at `:160` gated on `fresh == 'true'` — skipped on exactly the suppressed path)
- **Spine stage broken:** governance / attention
- **What:** a broken-but-non-throwing hourly runner reports green indefinitely — the class behind the 2026-07-07 hourly freeze. PRD-250's client-side staleness banner fixes the *viewer's* blindness; the job-level vacuous green remains, with no red test asserting it impossible. `dashboard_preview.yml:45-64` proves the fail-loud inversion is known — it exits 1 on the same condition. Invariants: fail-loud, red-test. **[V]**

### F-09 — Gate 9 (earnings) is a gate that cannot fail: no production code ever sets `has_earnings_soon` — **Medium**
- **Where:** `cuttingboard/options.py:389` (sole production constructor, literal `None`); `qualification.py:448-456` (None → pass, marked skipped)
- **Spine stage broken:** questions (Q3)
- **What:** the earnings gate passes on every real run, forever; it can fail only in tests. PRD-235's `gates_skipped` marker makes the skip visible — honest — but the gate still counts toward the documented "11 gates" while contributing zero discrimination. Fails the four-question anchor (#8) and the realizability discipline: an output channel (earnings rejection) with no input path that can produce it. Ceremony that reads as protection. **[V]**

### F-10 — `chain_validation` uses host-local `date.today()` for expiry/DTE math — **Medium**
- **Where:** `cuttingboard/chain_validation.py:152`, consumed at `:200-210` (expiry selection, `expiry_dte`, `_expiry_fit_ok`)
- **Spine stage broken:** terminal decision
- **What:** every other clock in the system is tz-aware UTC or pinned `America/New_York`; this one is the host's local date, in a decision-changing spot. From a UTC container in the ET evening, "today" is already tomorrow: DTE shifts a day and can flip expiry fit. The scheduled crons are safe by slot timing, not construction; `workflow_dispatch`/local evening runs are not. Invariant: CI parity. **[V]** mechanism; boundary-DTE flip **[I]**

### F-11 — The hourly path re-implements the pipeline by copy-paste, three stage-sequences in one file — **Medium**
- **Where:** `runtime/__init__.py:391-452` (two near-identical blocks inside `_execute_notify_run`) duplicating `_run_pipeline` stages `:910-1023`
- **Spine stage broken:** questions / terminal decision
- **What:** the same fetch→regime→structure→candidates→qualify sequence exists three times with hand-maintained differences (no kill switch, no decision gates, per-stage `datetime.now` re-reads instead of one run clock). Every future gate must be remembered in three places or the paths diverge silently — F-01 is the proof this already happened, with the highest-stakes gate. The runtime debt register (re-eval 2026-08-15) frames the monolith as a file-size problem; the triplicated decision logic is the sharper risk and is not named there. **[V]**

### F-12 — Commit-resolvability is skipped on the only blocking gate, beyond the settled decision's stated scope — **Medium**
- **Where:** `.github/workflows/ci.yml:19` (`--skip-commit-resolvability`, unconditional); `tools/validate_prd_registry.py:396-397`; `scripts/prd_close.sh:157,175-178,299-304` (writes `COMPLETE @ <--hash>` unverified); decision scope: `docs/PROJECT_STATE.md` § Known technical debt ("permanently **for historical rows**")
- **Spine stage broken:** governance
- **What:** PRD-243's WONTFIX-HISTORICAL for pre-#229 phantom SHAs is settled and not re-litigated. But the flag disables resolvability for *all* rows including every future closeout: `prd_close.sh` records whatever hash the caller supplies, and the only check that would catch a bogus SHA runs solely in non-blocking local scripts. The code exceeds the decision's scope; a validator floor (the same file already uses a ≥242 floor for second-model checks) would honor the decision without the standing hole. Invariants: assert-resolved, CI parity. **[V]**

### F-13 — Identity pinning absent across the toolchain: mutable action tags in write-permission workflows, no lockfile, floating model id — **Medium**
- **Where:** all workflows (`actions/checkout@v6` etc., running with `contents: write` + secrets in `cuttingboard.yml`/`hourly_alert.yml`); `pyproject.toml:6-20` (floor pins, no lockfile anywhere); `tools/macro_awareness_collector.py:46` (`DEFAULT_MODEL = "claude-opus-4-8"`, undated)
- **Spine stage broken:** governance
- **What:** the repo's own invariant 6 ("model → dated snapshot, action → commit SHA, dependency → declared AND locked") is unpinned on all three legs. A re-pointed action tag executes unreviewed code in workflows that push to `publish` and hold Telegram/API secrets; `pip install -e ".[dev]"` resolves latest-compatible at CI time (yfinance sits under the evidence layer and changes data-shape behavior between releases); the LLM classifier's behavior can shift under an aliased model id with no diff. **[V]**

### F-14 — Terminal-state truth derived twice in parallel (contract vs summary); `verify` checks the summary against itself — **Medium**
- **Where:** `runtime/__init__.py:1204-1279` (`_build_run_summary` independently recomputes kill_switch, permission lines, min-RR, counts) vs `_build_and_finalize_contract` `:704-837`; `verify_run_summary` `:1470-1597`; third min-RR duplicate `:2177-2184` (acknowledged, deferred)
- **Spine stage broken:** state / explanation
- **What:** the contract is validated well (twice, key-whitelisted); the run summary — what `--mode verify` and `run_daily.sh` treat as the run's verdict — is a second derivation with its own copies of the same logic, and `verify_run_summary` validates the summary's *internal* consistency rather than cross-checking it against the contract that notifications and the dashboard render from. Agreement today is by parallel construction, the kind that drifts. Invariant: authoritative-source. **[V]**

### F-15 — The sidecar doctrine contradicts itself about decision-feeding sidecars; the code follows the permissive half — **Medium**
- **Where:** `docs/sidecar_doctrine.md:17-23` (declares decision-feeding sidecars: `market_map` → `overnight_policy`, `macro_pressure` → `execution_policy`) vs `:43-49` ("a sidecar that influences whether a trade is taken, blocked, or sized differently **is not a sidecar**") vs `:58-63` + `:89-92` ("may not… change a candidate's qualification, decision, or sizing"; "No sidecar reads back into … `execution_policy.py`"; "No sidecar… inject[s] derived fields into the contract" — yet `apply_overnight_policy` injects per-candidate contract fields from `market_map` data, `runtime/__init__.py:779-783`)
- **Spine stage broken:** governance
- **What:** the binding doctrine simultaneously legitimizes and forbids the two sidecars that influence decisions/sizing/contract content. Reviews enforcing "observe-only" and reviews accepting "decision-feeding, documented consumer" can both cite this document. The operational risk hiding in the ambiguity is F-07: a decision-feeding path built to observation-grade failure discipline. Item-9 sweep otherwise clean: one orphan (F-20), no *covert* decision influence found; `market_map_lifecycle`'s cross-run price backfill is documented and renderer-only. **[V]**

### F-16 — Production runtime implements fixture mode via `unittest.mock.patch` — **Medium**
- **Where:** `runtime/__init__.py:25` (import), `:1662-1678` (patches `cuttingboard.derived.fetch_ohlcv` + `cuttingboard.runtime.fetch_ohlcv`), `:1697-1717` (replaces `cuttingboard.validation.datetime`)
- **Spine stage broken:** evidence (fixture path)
- **What:** fixture determinism rests on a hand-maintained monkeypatch-target list rather than injected data sources/clocks. Any new module that imports `fetch_ohlcv` directly escapes the patch and performs live fetches in "deterministic" mode; same for new `datetime.now` calls under `validation`. Works today; converts every import-path refactor into a potential silent fixture-fidelity hole. **[V]**

### F-17 — Silent-default readers on decision-adjacent state contradict the fail-loud doctrine — **Medium**
- **Where:** `delivery/dashboard_renderer.py:1088-1094` (`_load_macro_snapshot`: bare `except` → `{}`); `delivery/regime_history.py:91-92` (SPY parquet bare `except` → `[]`); `runtime/__init__.py:1781-1810` (`_load_run_history` → `[]` on any parse error); all JSONL readers drop malformed lines silently
- **Spine stage broken:** state / explanation
- **What:** a corrupt macro snapshot renders as a blank section with no signal; a corrupt SPY cache empties the scoreboard source; a corrupt audit log quietly shrinks run history. Individually presentation-adjacent; collectively the operator's read of "what the system knows" can degrade with no tell. Contrast `flow.py` and `red_folder.py`, which implement the doctrine exemplarily. Invariant: fail-loud. **[V]**

### F-18 — Adjusted OHLCV history mixed with unadjusted live quotes in threshold-gate arithmetic — **Medium [2L]**
- **Where:** `ingestion.py:335` (`auto_adjust=True`) vs `:296` (`fast_info.last_price`, unadjusted); combined in `qualification.py:459-472` (Gate 10 extension) and `:642-700` (continuation entry/stop)
- **Spine stage broken:** questions (Q3)
- **What:** EMA/ATR/SMA are computed on dividend/split-adjusted bars while `entry_price` is the live unadjusted trade. Around ex-dividend dates the bases are offset — small for these ETFs, but the consumers are threshold gates (`EXTENSION_ATR_MULTIPLIER`, `STOP_ATR_FLOOR_K`) where a basis offset lands on the decision margin. Undocumented choice. **[V]** mechanism; materiality **[2L]**

### F-19 — Fixture-backed Sunday runs mix a live run clock with a frozen validation clock — **Low**
- **Where:** `runtime/__init__.py:847` (frozen `run_at_utc` keyed on `mode == MODE_FIXTURE` only) vs `_is_fixture_backed` `:2296-2297` (includes Sunday-with-fixture; the validation clock *is* frozen for it)
- **Spine stage broken:** evidence
- **What:** two clocks in one run for fixture-backed Sunday: wall-clock generation ids/EOD windows, frozen validation freshness. Harmless today; inconsistent by construction. **[V]**

### F-20 — `logs/macro_awareness_snapshot.json` has zero consumers; the LLM sidecar publishes into the void — **Low**
- **Where:** producer `tools/macro_awareness_collector.py` (PRD-187); consumers: none in `cuttingboard/**`, `ui/**`, or any renderer (grep-verified); intended consumer PRD-188 PROPOSED/parked, eval gate unstarted (`docs/PROJECT_STATE.md`)
- **Spine stage broken:** attention (Q2)
- **What:** the collector's doctrine is excellent (observe-only, fail-closed, fixed enum — PRD-187 itself is settled and not re-litigated), but a running producer (workflow, API key, novelty state) is maintained for a consumer that may never be approved, and the declared go/no-go (2026-07-15) is noted as advisory and not wired. Under "if a feature does not change a decision it should not exist," this is the item-8/9 sweep's clearest parasitic candidate. **[V]**

### F-21 — `sector_router` computes and persists state that no decision consumes — **Low**
- **Where:** `cuttingboard/sector_router.py` (`resolve_sector_router`, state file `logs/sector_router_state.json` via `runtime/__init__.py:2300-2303`); `router_mode`/scores flow only to summary, contract display fields, and notification text
- **Spine stage broken:** questions (anchor Q1/Q2, weakly)
- **What:** documented honestly as "state model only, no routing application surface" (`docs/architecture.md`), i.e., a persisted, cross-run stateful component whose output is display text. It passes the anchor audit only as observation; it carries pipeline-grade machinery (own state file, shared by daily and hourly paths) for a display field. Four-question anchor: flag as parasitic-leaning unless retained-with-reason. **[V]**

### F-22 — `POLYGON_API_KEY` injected into both scheduled workflows; nothing reads it — **Low**
- **Where:** `.github/workflows/cuttingboard.yml:47`, `hourly_alert.yml:40`; zero `POLYGON` matches in any `.py` under `cuttingboard/`, `tools/`, `scripts/`
- **Spine stage broken:** governance
- **What:** a live secret exported into every scheduled run's environment for no reader — needless blast-radius widening given F-13's mutable action tags, and dead config that reads as load-bearing. **[V]**

### F-23 — Hygiene batch: pytest awareness in production, repo-root `traceback.txt`, stale run_daily.sh Sunday comment, mode-ungated failure notification, fixture-chain doc drift — **Low**
- **Where:** (a) `output.py:93-107` — notification dedup scope keyed on `PYTEST_CURRENT_TEST`; (b) `runtime/__init__.py:565` — hourly exception handler writes `traceback.txt` to repo root; (c) `run_daily.sh` header ("On Sunday, live mode auto-converts") vs `runtime/__init__.py:2224-2228` (converts only when `now_et` ≥ 15:30 — a Sunday-morning live run stays live, fetches stale Friday data, then halts on freshness: safe, but not what the comment says); (d) `runtime/__init__.py:566-571` — `_execute_notify_run`'s failure handler sends a real Telegram message with no `mode == MODE_LIVE` gate, unlike the success path at `:483`; (e) `docs/architecture.md:98` says fixture mode "synthesizes VALIDATED" chain results — code emits `MANUAL_CHECK` (`runtime/__init__.py:1681-1694`)
- **Spine stage broken:** governance / attention / explanation
- **What:** each small; together they mark the same seams — test/production and repo/artifact boundaries leaking, and two docs-match-code drifts on operator-facing surfaces. **[V]**

---

## Part C — Triage summary for the GPT-5.6 pass

**Top 5:** F-01 (hourly bypasses the kill switch, hardcodes `False`), F-02 (fabricated-calm `pct_change=0.0` under it), F-03 (no run reproducible — inputs never archived), F-04/F-05 (the governance gates are label-trusting and convention-backed: the answer to "could Claude Code merge a violation unstopped" is yes), F-06 (non-atomic critical writes + wedge under an 8-minute kill timer).

**Interaction to attack first:** F-01 × F-02 — market-stress protection can fail closed-loop: one live channel never checks it, and the other channel's check can be silently disarmed by the evidence layer.

**Where the mantra fails first (item 10 verdict):** the attention layer — both trader-facing channels have a path that skips the state discipline the doctrine promises (F-01) or stays silently green while frozen (F-08) — and second, the explanation layer, whose recorded reasons can never be re-derived against archived evidence (F-03).

**Not reached / thinner than planned:** `intraday_state_engine.py` internals, `market_map.py` grading, `regime.py` vote-model internals, and `notifications/formatter.py` were traced for interface behavior only; test-suite quality was sampled via the guards' red tests, not systematically; live branch-protection settings and the `publish` branch content were audited from repo code only (F-05 carries the [2L]); F-18's live materiality needs a targeted second look.

**Provenance:** all file:line references are against `main` @ `7f1ff20`. The plan file is not in the repo; this ledger executes the version Dustin supplied in-session. The settled-decisions ledger in this repo is `docs/DECISIONS.md`.
