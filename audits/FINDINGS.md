# CuttingBoard Architecture Audit — FINDINGS

**Date:** 2026-07-09
**Auditor:** Claude Code (read-only architecture audit, branch `claude/cuttingboard-architecture-audit-it5mo6`)
**Audited tree:** `main` @ `7f1ff20` (PRD-250 merge)
**Feeds:** adversarial GPT-5.6 review. Every finding is self-contained and checkable.

**Method notes.**
- The plan of record, `audits/CUTTINGBOARD_AUDIT_PLAN.md`, does **not exist in this repo** — not in the working tree, git history, or any remote ref. The audit was executed from the plan description in the commissioning charge (10 items, 4 phases: mantra sanity-check → dependency + run-trace heavy passes → state/governance → scope/red-team, with complexity and the six PRD-198 semantic-failure invariants as cross-cutting lenses). The charge also references `DECISIONS_LOG.md`; the repo file is `docs/DECISIONS.md` — treated as the settled-decisions ledger.
- Three read-only recon sweeps (governance, state/artifacts, nondeterminism) were dispatched to subagents; every decisive claim carried into this ledger was re-verified in the code by the main auditor (CLAUDE.md author-discipline 4).
- Settled decisions in `docs/DECISIONS.md` were not re-litigated. Findings against them appear only where the code contradicts the decision's own stated scope.
- Spine vocabulary: evidence → questions → state → attention → terminal decision → explanation → governance.

**Item 1 verdict (mantra sanity-check):** the spine is real and the docs largely match the code. `docs/architecture.md` names `runtime._run_pipeline` as its source of truth and describes it accurately (one drift noted in F-19). The four VISION questions map cleanly onto regime → macro → qualification → invalidation. The audit proceeded on that spine.

---

## Findings (ranked by severity)

### F-01 — The hourly alert path bypasses the market-stress kill switch and hardcodes `kill_switch: False`
- **Severity:** Critical
- **Location:** `cuttingboard/runtime/__init__.py:356-559` (`_execute_notify_run`); hardcoded field at `runtime/__init__.py:1946` (`_build_hourly_run_summary`); kill switch evaluated only at `runtime/__init__.py:916` and `:1227` (daily pipeline only)
- **Spine stage:** terminal decision / attention
- **What's wrong:** `_kill_switch` (VIX > 35, VIX pct_change > 0.15, |SPY pct| > 0.03 — PRD-180) is evaluated in exactly two places, both inside the daily `_run_pipeline` path. The hourly path (`_execute_notify_run`, invoked live by `alert_runner` every slot) runs fetch → validate → regime → structure → candidates → `qualify_all` and emits candidate lines to Telegram with **no kill-switch evaluation anywhere**, then writes an hourly run summary that asserts `"kill_switch": False` as a literal. VISION calls extreme market stress "a hard invalidation"; on a day where VIX spikes 20% intraday but validation passes (all quotes fresh, |pct| < 25%), the 06:00 daily run may be fine, and every subsequent hourly alert can present qualified candidates with R:R lines while the daily pipeline, had it run, would HALT. The published hourly dashboard artifacts (`dashboard_renderer.py:2051` reads `kill_switch` via `_req`) then display a categorical "False" that was never computed. Invariant 2 violation (asserts the requested, not the resolved) on a live user-facing channel.
- **Confidence:** verified in code (absence of call site confirmed by exhaustive grep; hardcoded literal read directly)

### F-02 — Ingestion silently substitutes `pct_change = 0.0` when `previous_close` is unavailable, blinding the kill switch and regime with no operator signal
- **Severity:** High
- **Location:** `cuttingboard/ingestion.py:303-312` (`_yfinance_quote_raw`); passes validation at `cuttingboard/validation.py:153-219`; consumed by `runtime/__init__.py:2165-2174` (`_kill_switch`) and `regime.py`
- **Spine stage:** evidence
- **What's wrong:** when yfinance returns a valid `last_price` but no usable `previous_close`, the quote is emitted with `pct_change = 0.0`, `fetch_succeeded=True`, and a **DEBUG-level** log line. A zero pct_change passes every validation rule (`validation.py` header: "No silent fallbacks" — the fallback is upstream of it). If this happens to SPY or ^VIX on a stress day, the kill switch's `spy_pct_change` / `vix_pct_change` legs read 0.0 and the hard invalidation goes blind; regime votes are likewise fed a fabricated calm. This is a textbook invariant-1 violation (substitute-and-continue) sitting directly under the system's single most safety-critical check, and it compounds F-01: the one path that does evaluate the kill switch can be silently disarmed by a data-source hiccup.
- **Confidence:** verified in code (mechanism); frequency of the degraded yfinance mode inferred

### F-03 — No raw-input snapshot is ever persisted: a past run's decision can be explained but not reproduced, and `--date` relabels rather than replays
- **Severity:** High
- **Location:** `cuttingboard/audit.py` (`_build_record` — derived fields only); `runtime/__init__.py:1204-1279` (`_build_run_summary` — derived only); `ingestion.py:325-338` (OHLCV fetch window is always `end=now`, `auto_adjust=True`); `ingestion.py:378-390` (parquet cache symbol-keyed, overwritten); `runtime/__init__.py:2220-2261` (`_resolve_run_date` / `_effective_run_date`)
- **Spine stage:** evidence / explanation
- **What's wrong:** the analysis layer is genuinely deterministic given its inputs, but the inputs are not archived. Audit records, run summaries, and the contract persist only derived values (regime labels, gate reasons, entry/stop/target); the raw 22-symbol quote set, the OHLCV frames the derived metrics ran on (cache overwritten next weekday), intraday 1-minute bars, live chain OI/spread numbers, the flow snapshot contents, and the validation clock are all discarded. There is no capture-to-fixture tool; the fixture schema carries only 8 quote fields, so even a hand-built replay diverges (OHLCV comes from the *current* cache, chain results are synthesized, ORB/intraday gates are skipped, flow loads the *current* config-pointed file). `--date` on a live run fetches today's data and stamps it with the requested date — a relabel, not a time machine. Consequence: "why did it say TRADE on June 12" is answerable only from the recorded reason strings; the claim can never be re-derived or challenged against the actual inputs.
- **Confidence:** verified in code

### F-04 — The HIGH-RISK second-model disposition gate trusts a self-declared label and a filename; four distinct bypasses
- **Severity:** High
- **Location:** `tools/validate_prd_registry.py:26` (`_LANE_HIGH_RISK_RE`), `:359-371` (existence vacuum, filename-only artifact check, substring waiver); `.github/workflows/ci.yml:19`
- **Spine stage:** governance
- **What's wrong:** the CI enforcement CLAUDE.md advertises ("`tools/validate_prd_registry.py` fails the CI `test` check when a HIGH-RISK close carries neither" artifact nor waiver) keys entirely on the PRD doc's own self-declared `LANE` header via a case-sensitive regex. Bypasses, each verified: (a) declare `LANE: STANDARD` — no cross-check against the actual change surface exists; (b) write `High-Risk` — regex has no `re.IGNORECASE`; (c) any header text between `LANE` and `HIGH-RISK` beyond `[:\s]*\n?\s*` defeats the match; (d) `if not doc.exists(): continue` plus the registry File-cell `—` exemption lets a COMPLETE HIGH-RISK row with no doc pass both checks vacuously. Additionally the "artifact" leg is satisfied by the *existence* of any non-`claude`-named `PRD-NNN.review.<model>.md` — contents never read, empty file passes (invariant 3: proxy, not authoritative source) — and the waiver check matches an inner substring, not the exact line CLAUDE.md specifies. The gate verifies the presence of the right words, not correspondence to reality — precisely what PRD-198 defines as semantic failure, in the guard that enforces PRD-198's sibling policy.
- **Confidence:** verified in code

### F-05 — The most load-bearing artifacts are written non-atomically; a mid-write kill wedges subsequent runs
- **Severity:** High
- **Location:** `runtime/__init__.py:1728-1778` (`safe_write_latest`, `_write_summary_files`, `_rewrite_summary_file` — bare `write_text`), `:2010-2016` (`_write_market_map_file`), `delivery/transport.py:80-83`; contrast atomic `tmp.replace` at `:2056-2058`, `:2092-2094`, `:2104-2114`; wedge at `:2000-2007` (`_load_previous_market_map` raises `RuntimeError` on malformed JSON)
- **Spine stage:** state
- **What's wrong:** `logs/latest_run.json`, `logs/latest_contract.json`, `logs/market_map.json`, and the delivery payload/HTML are written with in-place `write_text`, while the *less* critical sidecar snapshots get temp+rename — the atomicity discipline is applied inversely to criticality. The CI workflows kill the pipeline with `timeout 8m` (`cuttingboard.yml:238`); a kill or crash mid-write leaves a truncated file. A truncated `market_map.json` then makes every subsequent daily run raise `RuntimeError` in `_load_previous_market_map` — a persistent wedge requiring manual cleanup — and a truncated `latest_contract.json` breaks downstream renderers loudly but late. Also note `_rewrite_summary_file` bypasses `safe_write_latest`'s newer-timestamp guard entirely, so the post-verification rewrite can clobber a newer concurrent write. Related: `logs/audit.jsonl` and `logs/evaluation.jsonl` are unlocked appends shared by the daily and hourly processes (separate GitHub concurrency groups — overlap is deliberate per `cuttingboard.yml:32-37`); every JSONL reader silently drops unparseable lines, so a torn append is silent record loss (invariant 1).
- **Confidence:** verified in code

### F-06 — Hourly failures are structurally invisible to automation: `alert_runner` always exits 0 and the freshness check greens an empty run
- **Severity:** Medium
- **Location:** `cuttingboard/alert_runner.py:42-122` (`main` — "convert all runtime failures to exit 0", backstop is itself a Telegram send); `.github/workflows/hourly_alert.yml:108-127` (missing/stale payload → `fresh=false` → `exit 0`); `runtime/__init__.py:561-609` (hourly exception handler)
- **Spine stage:** governance / attention
- **What's wrong:** the hourly path's only failure signals are (a) a Telegram backstop message whose own failure is swallowed (`alert_runner.py:120-121`), and (b) a green workflow that quietly skips publish. A broken-but-non-throwing hourly runner therefore reports success indefinitely — the exact class behind the 2026-07-07 hourly freeze that PRD-250 responded to. PRD-250's client-side staleness banner mitigates the *viewer's* blindness, but the job-level vacuous green remains: no exit code, no red job, no `check_readiness` on the suppressed path (`hourly_alert.yml:160` gates it on `fresh == 'true'`). `dashboard_preview.yml:45-64` proves the team knows the fail-loud inversion — it exits 1 on the same condition. Invariants 1 and 4 (the guard has no red test asserting a green-on-empty run is impossible, because it is possible).
- **Confidence:** verified in code

### F-07 — Gate 9 (earnings) is a gate that cannot fail: no production code ever sets `has_earnings_soon`
- **Severity:** Medium
- **Location:** `cuttingboard/options.py:389` (sole production constructor, hardcodes `has_earnings_soon=None`); `cuttingboard/qualification.py:448-456` (None → pass, marked skipped)
- **Spine stage:** questions (Q3, tradability)
- **What's wrong:** `TradeCandidate.has_earnings_soon` has exactly one production construction site and it is the literal `None`. The earnings gate therefore passes on every real run, forever — it can only fail in tests. PRD-235's `gates_skipped` marker makes the skip *visible*, which is honest, but the gate still counts toward "11 gates" in every doc and report while contributing zero discrimination. This is the author-discipline "realizability check" failed at the standing-architecture level: an output channel (earnings rejection) with no input path that can produce it. Either the gate is wired to a data source or it is ceremony; today it is ceremony that reads as protection.
- **Confidence:** verified in code

### F-08 — `chain_validation` uses host-local `date.today()` for expiry/DTE math — the one genuine timezone leak, in a decision-changing spot
- **Severity:** Medium
- **Location:** `cuttingboard/chain_validation.py:152` (`today = date.today()`), `:200-210` (expiry selection and `expiry_dte` arithmetic)
- **Spine stage:** terminal decision
- **What's wrong:** every other clock read in the system is tz-aware UTC or pinned `America/New_York` (`time_utils.py`). Chain validation — which selects the option expiry and gates on DTE fit — computes "today" from the host's local timezone. Run from a UTC container in the ET evening (or any host east of ET around midnight), `date.today()` is already tomorrow: DTE math shifts by one day, which can flip `_expiry_fit_ok` and reclassify a setup. The scheduled runs (13:00 UTC ≈ 9am ET) are safe by luck of the cron slot, not by construction; a `workflow_dispatch` or local evening run is not.
- **Confidence:** verified in code (mechanism); flip requires a boundary DTE — inferred

### F-09 — The hourly path re-implements the premarket pipeline by copy-paste; F-01 is the observable divergence
- **Severity:** Medium
- **Location:** `runtime/__init__.py:391-452` — two near-identical fetch→regime→structure→candidates→qualify blocks inside `_execute_notify_run` (`_QUALIFY_ONLY_MODES` branch at :403-424 vs `_HOURLY_MODES` branch at :426-452), duplicating `_run_pipeline`'s stages :910-1023
- **Spine stage:** questions / terminal decision
- **What's wrong:** the same stage sequence exists three times in one file with hand-maintained differences (no kill switch, no decision gates, no correlation/policy, different sector-router construction, `datetime.now` re-read per stage instead of one run clock). Every future gate added to the daily path must be remembered twice more or the paths diverge silently — F-01 shows this has already happened with the highest-stakes gate. The runtime monolith is acknowledged debt with a re-eval date (2026-08-15, `docs/PROJECT_STATE.md`), but the debt register frames it as a *file-size/extraction* problem; the triple-maintained pipeline logic is the sharper risk and is not named there.
- **Confidence:** verified in code

### F-10 — Commit-resolvability is skipped on the only blocking gate, beyond the scope the settled decision granted
- **Severity:** Medium
- **Location:** `.github/workflows/ci.yml:19` (`--skip-commit-resolvability`); `tools/validate_prd_registry.py:396-397`; `scripts/prd_close.sh:157,175-178,299-304` (writes `COMPLETE @ <--hash>` unverified); decision scope in `docs/PROJECT_STATE.md` § Known technical debt ("CI keeps `--skip-commit-resolvability` permanently **for historical rows**")
- **Spine stage:** governance
- **What's wrong:** PRD-243 settled that pre-#229 phantom SHAs are WONTFIX-HISTORICAL — not re-litigated here. But the implementation disables resolvability for *all* rows, including every future closeout: `prd_close.sh` records whatever `--hash` the caller supplies with no verification the commit exists, and the only check that would catch a typo'd or rebased-away SHA runs solely in non-blocking local scripts. The code exceeds the decision's own stated scope ("for historical rows"); a validator floor (like the ≥242 floor the same file already uses for second-model checks) would satisfy the decision without the standing hole. Invariants 2 and 5.
- **Confidence:** verified in code

### F-11 — Identity pinning is absent across the toolchain: mutable action tags in write-permission workflows, no dependency lockfile, floating model id
- **Severity:** Medium
- **Location:** all workflows (`actions/checkout@v6`, `setup-python@v6`, `cache@v4`, `deploy-pages@v4`, etc.) — `cuttingboard.yml` and `hourly_alert.yml` run these with `contents: write` + secrets; `pyproject.toml:6-20` (floor pins only, no lockfile anywhere); `tools/macro_awareness_collector.py:46` (`DEFAULT_MODEL = "claude-opus-4-8"`, undated)
- **Spine stage:** governance
- **What's wrong:** PRD-198 invariant 6 ("pin identities that matter: model → dated snapshot, action → commit SHA, dependency → declared AND locked") is the repo's own doctrine, and all three legs are unpinned. A re-pointed action tag executes unreviewed code in a workflow that can push to `publish` and holds Telegram/API secrets; `pip install -e ".[dev]"` resolves latest-compatible at CI time, so the tested dependency set drifts silently from any local run (yfinance in particular changes data-shape behavior between releases and sits under the evidence layer); the macro-awareness classifier's behavior can shift under an aliased model id with zero diff.
- **Confidence:** verified in code

### F-12 — Terminal-state truth is derived twice in parallel (contract vs run summary), reconciled only by a field-level self-check
- **Severity:** Medium
- **Location:** `runtime/__init__.py:1204-1279` (`_build_run_summary` — independently recomputes kill_switch, permission lines, min_rr, candidate counts) vs `_build_and_finalize_contract` :704-837; `verify_run_summary` :1470-1597 checks the summary against *itself*; third min-RR duplicate at :2177-2184 (acknowledged in PROJECT_STATE as deferred)
- **Spine stage:** state / explanation
- **What's wrong:** the contract is validated by `assert_valid_contract` (twice, well-designed), but the run summary — the artifact `verify` mode and `run_daily.sh` treat as the run's verdict — is a second, independent derivation from the same in-memory objects with its own copies of the permission-line, min-RR, and kill-switch logic. `verify_run_summary` then validates the summary's internal consistency (fields the same builder produced) rather than cross-checking summary against contract — invariant 3 (proxy, not authoritative). Nothing enforces that `summary.outcome`/`kill_switch`/`candidates_qualified` agree with the contract that notifications and the dashboard render from; today they agree by parallel construction, which is exactly the kind of agreement that drifts.
- **Confidence:** verified in code

### F-13 — Production runtime depends on `unittest.mock.patch` to implement fixture mode
- **Severity:** Medium
- **Location:** `runtime/__init__.py:25` (import), `:1662-1678` (`_fixture_cache_only_ohlcv` patches `cuttingboard.derived.fetch_ohlcv` + `cuttingboard.runtime.fetch_ohlcv`), `:1697-1717` (`_fixture_validation_clock` replaces `cuttingboard.validation.datetime` with a class)
- **Spine stage:** evidence (fixture path)
- **What's wrong:** fixture mode is implemented by monkeypatching module globals at runtime rather than by injecting a data source / clock through parameters. The patch-target list is maintained by hand: any new module that imports `fetch_ohlcv` directly (as `derived.py` and `runtime` do today) silently escapes the patch and performs live fetches in "deterministic" fixture mode; the same applies to any new `datetime.now` call inside `validation.py`'s import graph. It works today, but the mechanism converts every future refactor of import paths into a potential silent fixture-fidelity hole, and it blurs the test/production boundary the same way `output.py:95`'s `PYTEST_CURRENT_TEST` check does (F-20).
- **Confidence:** verified in code

### F-14 — Adjusted OHLCV history is mixed with unadjusted live quotes in the same gate arithmetic
- **Severity:** Medium
- **Location:** `ingestion.py:335` (`yf.download(..., auto_adjust=True)`) vs `ingestion.py:296` (`fast_info.last_price`, unadjusted); combined in `qualification.py:459-472` (Gate 10: `candidate.entry_price` vs `dm.ema21`/`dm.atr14` from adjusted history) and `qualification.py:642-700` (continuation entry = adjusted close, stop = adjusted breakout level)
- **Spine stage:** questions (Q3)
- **What's wrong:** derived metrics (EMA/ATR/SMA) are computed on dividend/split-adjusted daily bars while the candidate's entry price is the live unadjusted last trade. Around ex-dividend dates the two series are offset (typically fractions of a percent for the ETFs in this universe; more after a large distribution or any split), so extension-from-EMA and ATR-floor comparisons mix two price bases. Descriptive tool, small magnitudes, but the gates being fed are threshold gates — `EXTENSION_ATR_MULTIPLIER`, `STOP_ATR_FLOOR_K` — where a basis offset lands directly on the decision margin. Nothing documents the choice.
- **Confidence:** verified in code (mechanism); materiality inferred — needs a second look

### F-15 — Fail-loud doctrine is contradicted by silent-default readers on decision-adjacent state
- **Severity:** Medium
- **Location:** `delivery/dashboard_renderer.py:1088-1094` (`_load_macro_snapshot`: bare `except` → `{}`); `delivery/regime_history.py:91-92` (SPY parquet bare `except` → `[]`); `runtime/__init__.py:1781-1810` (`_load_run_history`: any parse error → `[]`, feeds postmarket report); every JSONL reader drops malformed lines silently
- **Spine stage:** state / explanation
- **What's wrong:** CLAUDE.md's first hardening invariant is "fail-loud, never silent-fallback," and `flow.py`/`red_folder.py` implement it exemplarily. But a corrupt `macro_drivers_snapshot.json` renders as a blank macro section with no signal; a corrupt SPY cache empties the scoreboard source (re-loudened downstream only by a `logger.warning`); a corrupt `audit.jsonl` quietly shrinks run history. Each individually is presentation-adjacent; collectively they mean the operator's read of "what the system knows" can degrade with no tell, which is the failure mode VISION's docs-match-code principle exists to prevent.
- **Confidence:** verified in code

### F-16 — Fixture-backed Sunday runs get a wall-clock `run_at_utc` while fixture mode gets a frozen one
- **Severity:** Low
- **Location:** `runtime/__init__.py:847` (`_deterministic_run_at(...) if mode == MODE_FIXTURE else datetime.now(...)`) vs `_is_fixture_backed` :2296-2297 (fixture_file + mode in {FIXTURE, **SUNDAY**})
- **Spine stage:** evidence
- **What's wrong:** `_is_fixture_backed` deliberately includes Sunday-with-fixture, and the validation clock *is* frozen for it (`_fixture_validation_clock` keys on `_is_fixture_backed`), but the run clock keys on `mode == MODE_FIXTURE` only. A fixture-backed Sunday run therefore mixes a live `run_at_utc` (generation_id, report timestamps, EOD-window checks) with a frozen validation clock — two clocks in one run. Harmless today; inconsistent by construction.
- **Confidence:** verified in code

### F-17 — `logs/macro_awareness_snapshot.json` has zero consumers; the LLM sidecar publishes into the void
- **Severity:** Low
- **Location:** `tools/macro_awareness_collector.py` (producer, PRD-187); consumers: none — no reference in `cuttingboard/**`, `ui/**`, or any renderer (verified by grep); intended consumer PRD-188 is PROPOSED/parked (`docs/PROJECT_STATE.md`)
- **Spine stage:** attention
- **What's wrong:** the collector is admirably doctrined (observe-only, fail-closed, fixed enum, no cuttingboard imports — the PRD-187 decision itself is settled and not re-litigated). But its output is read by nothing: the SHOCK banner that would consume it (PRD-188) is parked with its eval gate unstarted. Under VISION's "if a feature exists but does not change a decision, it should not exist" and the realizability discipline, this is a running producer (workflow, API key, novelty state) maintained for a consumer that may never be approved. It was *declared* defensive-future, which is the honest form — but the declaration has no expiry, and VISION requires acknowledged deferral to carry a re-evaluation date (PRD-188's 2026-07-15 go/no-go is noted as "advisory/soft and NOT wired").
- **Confidence:** verified in code (absence of consumers); status from PROJECT_STATE

### F-18 — `POLYGON_API_KEY` is injected into both scheduled workflows but read by nothing
- **Severity:** Low
- **Location:** `.github/workflows/cuttingboard.yml:47`, `hourly_alert.yml:40`; zero matches for `POLYGON` in any `.py` under `cuttingboard/`, `tools/`, `scripts/`
- **Spine stage:** governance
- **What's wrong:** a live secret is exported into the environment of every scheduled run for no reader. Combined with unpinned action tags (F-11), this needlessly widens the blast radius of a compromised action: the secret is exfiltratable from jobs that have no use for it. Dead config that looks load-bearing is also drift under docs-match-code.
- **Confidence:** verified in code

### F-19 — Doc drift: `architecture.md` says fixture mode synthesizes VALIDATED chain results; the code synthesizes MANUAL_CHECK
- **Severity:** Low
- **Location:** `docs/architecture.md:98` ("fixture mode synthesizes VALIDATED results") vs `runtime/__init__.py:1681-1694` (`_fixture_chain_results` → `MANUAL_CHECK`, "fixture mode skips live chain validation"); note `_validated_chain_result` :2207-2217 *is* VALIDATED but serves a different purpose (missing chain results in `_run_decision_gates`)
- **Spine stage:** explanation / governance
- **What's wrong:** PRD-239 made `architecture.md` "true" and PRD-234 killed the VALIDATED fail-open, but line 98 still describes the pre-234 behavior. Small, but this file self-describes as the canonical stage map and the repo's core principle is docs-match-code; the parked "present-MANUAL_CHECK render visibility" item in PROJECT_STATE compounds it (fixture TRADE renders show zero A+ trades with all setups invisible).
- **Confidence:** verified in code

### F-20 — Assorted hygiene: pytest awareness in production, repo-root `traceback.txt`, run_daily.sh Sunday comment, mode-ungated failure notification
- **Severity:** Low
- **Location:** (a) `output.py:93-107` — notification dedup scope keyed on `PYTEST_CURRENT_TEST`; (b) `runtime/__init__.py:565` — hourly exception handler writes `traceback.txt` to CWD (repo root); (c) `run_daily.sh` header claims "On Sunday, live mode auto-converts" — code converts only when `now_et` ≥ 15:30 (`runtime/__init__.py:2224-2228`), so a Sunday-morning live run stays live and fetches stale Friday data (then halts on freshness — safe, but not what the comment says); (d) `runtime/__init__.py:566-571` — the `_execute_notify_run` failure handler sends a real Telegram notification with no `mode == MODE_LIVE` gate, unlike the success path at :483 (only live callers exist today via `alert_runner`)
- **Spine stage:** governance / attention
- **What's wrong:** each is small; together they mark the same seam — test/production and repo/artifact boundaries leaking. (a) means production dedup semantics differ under test by design (invariant 5); (b) drops an untracked debris file where a generated-artifact discipline exists; (c) is doc-vs-code drift on the operator's entry script; (d) is a latent mode leak guarded only by current call-site discipline.
- **Confidence:** verified in code

---

## Cross-cutting lens summaries

**Complexity.** Three gravity wells: `runtime/__init__.py` (2,427 lines — acknowledged debt, dated 2026-08-15, but see F-09: the risk is triplicated pipeline logic, not file length), `delivery/dashboard_renderer.py` (3,057 lines; decomposition map exists, unexecuted), and `output.py` (970 lines mixing report rendering, Telegram transport with module-global rate-limit/dedup state, and notification result state — `delivery/html_renderer.py:21` importing from it blurs the delivery/core boundary). The `qualification ↔ flow` import cycle is TYPE_CHECKING-only (benign). Otherwise the module graph is clean: delivery consumes downstream-only, `runtime` is the sole orchestrator, `contract_types` is a proper leaf.

**Six invariants (PRD-198) applied to the system itself.** 1 Fail-loud: violated at F-02, F-05 (torn appends), F-06, F-15. 2 Assert-the-resolved: violated at F-01 (`kill_switch: False` literal), F-10 (unverified closeout hash). 3 Authoritative-source: violated at F-04 (filename as artifact), F-12 (summary self-check). 4 Red tests: the guards' happy paths are well-tested; the bypasses (F-04) and vacuous-greens (F-06) have none. 5 Verify-where-truth-is-determined: F-08 (host-local date), F-11 (unlocked deps → CI ≠ local), F-20a. 6 Pin identities: F-11 across all three legs.

---

## READ ME FIRST

**Top 5 findings, in order:**

1. **F-01 (Critical)** — the hourly alert path never evaluates the market-stress kill switch and hardcodes `kill_switch: False` into its published summary. The system's one hard invalidation exists on only one of the two live channels.
2. **F-02 (High)** — ingestion silently fabricates `pct_change = 0.0` when previous_close is missing (DEBUG log, `fetch_succeeded=True`), which passes all validation and can blind the kill switch and regime on exactly the days they matter.
3. **F-03 (High)** — no raw inputs are ever persisted; no run can be reproduced, only its recorded reasons re-read. `--date` relabels current data, and fixture mode cannot restore OHLCV/chain/intraday/flow fidelity even in principle.
4. **F-04 (High)** — the HIGH-RISK second-model CI gate is defeated by lane relabeling, casing, header formatting, or a missing doc, and its "artifact" check is satisfied by an empty correctly-named file.
5. **F-05 (High)** — the most critical artifacts (`latest_contract.json`, `latest_run.json`, `market_map.json`) are written non-atomically under an 8-minute CI kill timer; a torn `market_map.json` wedges every subsequent daily run.

**Interaction to check first:** F-01 × F-02 — the two together mean market-stress protection can fail closed-loop: the hourly channel never checks it, and the daily channel's check can be disarmed by a data hiccup with no operator signal.

**Not reached / thinner than planned:**
- `intraday_state_engine.py` (536 lines), `market_map.py` grading internals, `regime.py` vote-model internals, and `notifications/formatter.py` were traced for interface behavior only, not line-audited.
- Test-suite quality was sampled via the governance guards' red tests, not systematically (the ~2,900-test baseline claim was not re-executed).
- The `publish`-branch content and Pages deployment state were audited from workflow code only, not by inspecting the live branch.
- F-14 (adjusted/unadjusted price-basis mix) is mechanism-verified but its live materiality deserves a targeted second look.

**Provenance notes for the adversarial reviewer:** the plan file this audit was commissioned against exists only outside the repo (see Method notes); the settled-decisions ledger is `docs/DECISIONS.md` (no `DECISIONS_LOG.md` exists). All file:line references are against `main` @ `7f1ff20`.
