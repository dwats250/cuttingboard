# Independent Review — Fable Audit Findings Ledger (`audits/FINDINGS.md` @ `051f337`)

**Reviewer:** Claude Code / blank Fable (independent second reviewer, fresh context — did not author the audit)
**Reviewed tree:** `main` @ `7f1ff20` (identical to the ledger's audited SHA; verified `HEAD == main == 7f1ff20`)
**Charge:** adversarial read-only critique of the findings ledger against the actual code. Every file:line citation in the ledger was checked directly.
*Reproduced verbatim as the evidence trail for the reconciled findings. Includes the post-review regime-inflation addendum.*

## What was reviewed

- **Findings ledger**: loaded from `origin/claude/cuttingboard-architecture-audit-it5mo6`, commit `051f337` (which supersedes the reverted `ef7aa60`). 23 findings, Part A verdicts, Part C triage.
- **Audit plan**: **CANNOT DETERMINE plan fidelity** — the plan file is not in the repo (the ledger's provenance note says it was supplied in-session and lives outside the repo; I confirmed no in-repo copy exists). I can only check the ledger against its own restatement of the plan (10 items, 4 phases, complexity + PRD-198 lenses). Everything below is therefore a code-vs-ledger review, not a plan-vs-execution review. If plan-vs-execution matters, the plan text needs to be committed or re-supplied.

Bottom line up front: **this is an unusually accurate ledger.** Of 23 findings, I rate 21 SOUND, 2 SOUND-with-overstatement, 0 UNSOUND, 0 fabricated references. Every symbol I checked exists; nearly every line number is exact (two citation errors noted below, neither invalidating its finding). My main disagreements are three severity calibrations and one materially incomplete claim in F-01.

## Per-finding verdicts

| # | Verdict | Ledger sev | My sev | Evidence checked |
|---|---------|-----------|--------|-----------------|
| F-01 | **SOUND, one overstatement** | Critical | Critical | `runtime/__init__.py:356-559`, `:1946`, `:916`, `:1227`, `:2156-2174`; `dashboard_renderer.py:2051` — all match |
| F-02 | **SOUND** | High | High | `ingestion.py:303-312`; `validation.py:153-219` (zero passes all 7 rules); `runtime:2165-2174`; `regime.py` |
| F-03 | **SOUND** | High | High | `ingestion.py:327-335`, `:378-390`; `runtime:2220-2261`; fixture has exactly 8 quote fields (verified) |
| F-04 | **SOUND** | High | High | `validate_prd_registry.py:26,359-371` + `_validate_history_docs:239`; `ci.yml:19` — all four bypasses reproduce |
| F-05 | **SOUND** | High | High | No CODEOWNERS (verified); `protect_files.sh` protected set + suffix match; `install_hooks.sh:20` "Informational only" |
| F-06 | **SOUND, two nuances** | High | High | `runtime:1728-1778,1777-1778,2010-2016`; atomic contrast `:2056-2114`; wedge `:2000-2007`; `transport.py:80-83`; appends verified; `timeout 8m` at `cuttingboard.yml:198,237,249,264` |
| F-07 | **SOUND** | Medium | **High** | `runtime:1355-1362`; `execution_policy.py` `_apply_macro_pressure` UNKNOWN -> full allow, full size |
| F-08 | **SOUND** | Medium | **High** | `alert_runner.py:42-122` (returns 0 on all paths, backstop swallow); `hourly_alert.yml:106-125,160`; `dashboard_preview.yml:47-64` inversion |
| F-09 | **SOUND** | Medium | Medium | `options.py:382-390` sole constructor, `has_earnings_soon=None`; `qualification.py:448-456` |
| F-10 | **SOUND** | Medium | Medium | `chain_validation.py:152` — the only naive `date.today()` in `cuttingboard/` (grep-verified) |
| F-11 | **SOUND** | Medium | Medium | Two near-identical blocks `:403-424` / `:426-452` vs `_run_pipeline`; per-stage `datetime.now` at `:369,381,397,421,444` |
| F-12 | **SOUND** | Medium | Medium | `ci.yml:19` unconditional; `prd_close.sh` has no hash verification (grep-verified); `PROJECT_STATE.md:118` says "for historical rows" |
| F-13 | **SOUND** | Medium | Medium | `@v6`/`@v7`/`@v4` tags everywhere; no lockfile anywhere (find-verified); `macro_awareness_collector.py:46` undated model id |
| F-14 | **SOUND** | Medium | Medium | `_build_run_summary:1204-1279` recomputes; `verify_run_summary:1470+` never reads the contract (grep-verified); the min-RR duplicate is acknowledged in `PROJECT_STATE.md` (PRD-240 deferral) — ledger says so |
| F-15 | **SOUND** | Medium | Medium | `sidecar_doctrine.md:17-23` vs `:47-49`, `:58-63`, `:89-92`; injection at `runtime:779-783` — contradiction is textual and real |
| F-16 | **SOUND** | Medium | Medium | `runtime:25` (`from unittest.mock import patch`), `:1663-1679`, `:1699-1718` |
| F-17 | **SOUND** | Medium | Medium | `dashboard_renderer.py:1088-1094`; `regime_history.py:~87-92`; `runtime:1781-1810` — all match |
| F-18 | **OVERSTATED (one leg)** | Medium [2L] | Low-Medium [2L] | Gate 10 leg (`qualification.py:459-472`) verified; the `:642-700` continuation leg draws entry from the *same* adjusted frame, so the mixed-basis critique only partially applies there |
| F-19 | **SOUND** | Low | Low | `runtime:847` (`mode == MODE_FIXTURE` only) vs `_is_fixture_backed:2296-2297` |
| F-20 | **SOUND** | Low | Low | Zero snapshot consumers (grep-verified); `tools/macro_awareness_eval.py` exists but reads a labeled corpus, not the snapshot — ledger's claim holds |
| F-21 | **SOUND — documented design** | Low | Low | `sector_router.py`; state path `runtime:2300-2303`; zero references in qualification/execution_policy/options/trade_decision (grep-verified); `architecture.md:77,265` documents it |
| F-22 | **SOUND** | Low | Low | `cuttingboard.yml:47`, `hourly_alert.yml:40` exact; zero `POLYGON` matches in any `.py` |
| F-23 | **SOUND (all 5 legs)** | Low | Low | (a) `output.py:93-107`; (b) `runtime:565`; (c) `run_daily.sh:5` vs `runtime:2224-2228` (caller at `:208` passes `now_et`, so morning Sunday stays live — comment is wrong); (d) `:566-571` ungated vs `:483` gated; (e) `architecture.md:~98` "synthesizes VALIDATED" vs `MANUAL_CHECK` at `runtime:1681-1694` |

### Findings needing elaboration

**F-01 (the Critical).** Everything cited is real: the hourly path runs fetch->regime->qualify with no `_kill_switch` call (exhaustive grep confirms calls only at `:916` and `:1227`), hardcodes `"kill_switch": False` at `:1946`, and the renderer requires and displays that field (`_req(run, "kill_switch")` at `dashboard_renderer.py:2051`). **But the claim "no market-stress evaluation" is overstated.** The hourly candidate branch is gated on `regime.posture != "STAY_FLAT"` (`:426`), and `_classify_regime` has a CHAOTIC override at `regime.py:290` triggered by `vix_pct > VIX_CHAOTIC_SPIKE` where `VIX_CHAOTIC_SPIKE = 0.15` (`config.py:102`) — *numerically identical to the kill switch's VIX-pct leg*. CHAOTIC forces STAY_FLAT, which suppresses hourly candidates. So one of the three kill-switch legs IS effectively mirrored on the hourly path. The two unmirrored legs are real and serious: absolute VIX > 35 (sustained high vol without a >15% one-interval move), and |SPY| > 3% (which on the short side would leave the hourly path presenting SHORT candidates while the daily path would HALT — VISION calls extreme stress a hard invalidation in *both* directions). And F-02 disarms the CHAOTIC mirror the same way it disarms the kill switch. **Critical stands** — the hardcoded `False` is an actively false safety indicator on a trader-facing surface — but the ledger (and any fix PRD) should state the CHAOTIC partial-mitigation, because it changes which scenarios actually slip through.

**F-06 (two nuances).** (1) The citation "`hourly_alert.yml:386-388`" is impossible — the file is 216 lines; the concurrency block is at lines 26-28. The claim itself (separate concurrency groups, deliberately un-serialized per a documented Codex P2 decision at `cuttingboard.yml:30-36`) is correct. (2) "Makes every later daily run raise `RuntimeError`" slightly overstates the mechanics: `_load_previous_market_map` is called at `:276` inside the `try` whose handler at `:281` converts it to a failed run with an error contract — so it's a repeating loud failure until manually cleared, not an unhandled crash. The wedge is real; the failure mode is at least visible.

**F-07 — severity understated, propose High.** This silently deletes a *blocking* decision gate (RISK_OFF -> LONG blocked; MIXED/RISK_OFF -> 25–50% size cuts) and replaces it with full-allow-at-full-size on *any* exception, logged at WARNING. The one mitigation: `"UNKNOWN"` does flow into rendered surfaces, so an attentive operator might notice. That's a weaker tell than the system's own fail-loud invariant demands for a decision-feeding input. Given F-15 shows this path already sits in doctrinal gray space, I'd rank it above several of the Highs in operational terms.

**F-08 — severity understated, propose High.** This exact class already produced a real incident (the 2026-07-07 hourly freeze the ledger cites), the repo's own `dashboard_preview.yml` proves the team knows the correct inversion, and the fix that shipped (PRD-250) only patched the viewer. A monitoring channel that can be broken-but-green indefinitely on a live trading decision-support system is a High.

**Findings that are real but describe documented, deliberate choices (not defects per se):**
- **F-09**: the fail-open is PRD-sanctioned ("fail-open per PRD", with PRD-235's honest `gates_skipped` marker). The *defect* is narrower than the finding reads: an output channel with no realizable input path — which the repo's own realizability discipline bans. Correctly Medium, but a fix here is a product decision (wire earnings data or retire the gate), not a bug fix.
- **F-14**: the third min-RR duplicate is explicitly acknowledged and deferred in `PROJECT_STATE.md` (PRD-240 closeout: "runtime refactors require their own PRD"). The ledger says "acknowledged, deferred" — honest.
- **F-21**: `architecture.md` documents sector_router honestly as "state model only, no routing application surface." This is a flagged cuts-candidate, not a defect. The ledger frames it correctly.
- **F-06 concurrency leg**: the un-serialized workflows are a documented decision (Codex P2 / PRD-194); the unlocked shared JSONL appends are the actual gap.
- **F-12**: correctly scoped — it does *not* re-litigate PRD-243's WONTFIX-HISTORICAL; it flags only that the code exceeds the decision's stated scope ("for historical rows" vs all rows). I verified both halves; that distinction survives review.

## Cross-cutting judgments

### 1. False positives

**None outright.** Every finding I checked references real code behaving as described. The nearest to inflation:
- F-01's "no market-stress evaluation" (the CHAOTIC mirror, above) — the finding survives but a skeptical reader of the fix PRD needs the caveat.
- F-18's continuation leg (`:642-700`) — entry price there comes from the same adjusted OHLCV frame as the ATR, so the mixed-basis mechanism doesn't apply as cited; only Gate 10 cleanly exhibits it. The [2L] hedge was appropriate; the line-range citation was not.
- F-19 and F-21 are ledger-acknowledged near-non-issues included for completeness — fine at Low.

The ledger's own confidence markers ([V]/[I]/[2L]) checked out honest everywhere I probed — e.g., F-05's [2L] on branch-protection settings is exactly right (not inspectable from the repo), and F-03's oddly specific "8 quote fields" claim is exactly correct.

### 2. Misses

What a rigorous architecture audit of this system should also have examined:

1. **Regime vote-model degradation (admitted "interface-only," but it's load-bearing for both live channels).** `regime.py:190-192`: `confidence = abs(net_score) / total_votes` over only the votes cast, with **no minimum-vote floor**. Non-halt symbols (IWM, DXY, TNX, BTC) dropping out of validation *thins the denominator and inflates confidence* — a stressed day with several failed optional fetches can produce a high-confidence, posture-permissive regime from two or three votes. This compounds F-02 (fabricated-calm votes) and gates the very hourly path in F-01. Look at: `regime.py:125-195`, the HALT_SYMBOL set vs the optional-symbol set, and what `posture` a 2-vote RISK_ON produces. *(See Addendum: the mechanism is confirmed but the optional-symbol set stated here is wrong — production exposure is narrower.)*
2. **The financial arithmetic itself.** No finding touches whether the numbers are right: the R:R computation, `_estimated_debit` (a flat 30%-of-strike-distance heuristic, `options.py:394+`), sizing via `PolicyContext.risk_modifier`, ATR/EMA formula correctness. For a decision-support tool, the arithmetic layer *is* the product; the audit verified plumbing exhaustively and math not at all. Look at: `options.py` sizing, `qualification.py` rr computation, `derived.py`.
3. **Notification dedup semantics across process boundaries.** `output.py`'s dedup state is module-global, i.e., per-process — and every CI run is a fresh process, so in-process dedup does nothing across runs; only `last_hourly_slot.json` (committed back via `git add -f`) carries cross-run state. Whether that slot-file round-trip is atomic with the send (send succeeds, commit fails -> duplicate next run?) went unexamined. Look at: `hourly_alert.yml:165+` commit step vs `save_last_slot` ordering at `runtime:524-526`.
4. **The `publish` branch surface (admitted).** What is actually publicly served by Pages — including whether `macro_awareness_snapshot.json`, audit records, or anything sensitive rides along via `ci_push_artifacts.sh` — and whether the delta-append race claims from PRD-194 hold. The ledger took these at declared value.
5. **Test-suite quality systematically (admitted).** 108 test files; PRDs claim mutation-verified red tests; the audit sampled guard red-tests only. A single sweep for vacuous assertions / always-pass patterns was in reach. (I spot-checked the `importorskip` ban: clean.)
6. **Unbounded artifact growth.** `audit.jsonl`/`evaluation.jsonl` are append-forever, and `_load_run_history` reads the whole file into memory each run (`runtime:1790`). Slow-burn operational risk in a system meant to run daily for years.

### 3. Priority — my top 5 by real operational risk to live decision support

Where I differ from the ledger's Part C: F-03 and F-04/F-05 drop out of my top 5. F-03 is a forensic-capability gap, not a live-decision risk; F-04/F-05 are governance risks in a single-operator repo where the human gate is the same person who'd exploit it. F-08 moves up on incident precedent.

1. **F-01** — the trader's phone receives qualified candidates during two classes of market stress the system's own doctrine calls hard invalidations, and the dashboard renders an affirmatively false `kill_switch: False`. Wrong *and* reassuring, on the highest-trust surface.
2. **F-02** — one data hiccup on SPY or ^VIX silently disarms the kill switch, the CHAOTIC override, and the regime votes simultaneously; it is the single upstream failure that defeats every stress protection at once, with a DEBUG-level whisper.
3. **F-08** — the hourly channel can be broken-but-green indefinitely, has already done it once in production (2026-07-07), and the shipped fix only patched the viewer. Silence from a monitoring system reads as "all clear."
4. **F-06** — an 8-minute kill timer over bare `write_text` on the most load-bearing artifacts, plus unlocked concurrent JSONL appends whose readers silently drop torn lines: both wedged mornings and quiet record loss are time bombs, not hypotheticals.
5. **F-07** — a blocking, sizing-relevant decision gate that degrades to "unconstrained, full size" on any exception. The one protection that says *no* can vanish without changing the system's outward demeanor.

## Overall assessment

I would stake my credibility on F-01 through F-17 and F-19 through F-23 as stated, subject to the F-01 CHAOTIC caveat and the two F-06 nuances. F-18 needs its second look before anyone acts on it. The ledger's self-reported limitations (Part C "not reached") are honest and match what I found unexamined — the regime vote-model internals being the one omission I'd call consequential, since it sits directly under the audit's own top two findings.

---

## Addendum — post-review verification of Miss #1 (regime confidence inflation)

A follow-up verify-only recon (same session, same tree) traced Miss #1 in full. The mechanism is **confirmed** but my original statement of it contained an error that this addendum corrects (failure-contract disclosure):

- **Correction:** Miss #1 above says the optional voters are "IWM, DXY, TNX, BTC". That is wrong. `config.py:95`: `HALT_SYMBOLS = ["^VIX", "DX-Y.NYB", "^TNX", "SPY", "QQQ"]` — DXY and TNX are halt symbols. Of the 8 votes, 7 come from halt-guarded symbols; **only the IWM and BTC-USD votes are optional.** Losing any halt symbol sets `system_halted=True` (`validation.py:104-108`), and both production `compute_regime` call sites are halt-guarded (`runtime/__init__.py:391-392`, `:910-911`), so the "two or three votes" scenario in Miss #1 is unreachable in production. The only unguarded entry point, `from_validation_results` (`regime.py:218-225`), has no production caller (test-only, verified).
- **Confirmed:** `total_votes` counts only votes cast (skipped symbols excluded from numerator AND denominator, `regime.py:178-181`, `:190-192`); there is **no quorum/minimum-vote floor** (the `total_votes > 0` ternary is div-by-zero protection only; `MIN_REGIME_CONFIDENCE` is a confidence floor that fewer votes make *easier* to clear).
- **Bounded but real inflation:** worst production case is IWM+BTC dropout (8->6 votes). With identical surviving evidence (4 RISK_ON + 2 NEUTRAL among halt-symbol votes): 8 votes -> confidence 0.50 -> STAY_FLAT; 6 votes -> confidence ~=0.667 -> **CONTROLLED_LONG**. At 5 risk-on: 5/8 = 0.625 -> CONTROLLED_LONG vs 5/6 ~= 0.833 -> **AGGRESSIVE_LONG**. Two optional-symbol dropouts can move posture one full tier more permissive.
- **F-02 interaction sharpened:** a fabricated `pct_change=0.0` quote still casts a vote — NEUTRAL in every pct-based vote band — so in absolute terms it *dilutes* confidence (stays in the denominator; dropout concentrates, fabrication miscolors). Its permissive push is relative to truth: on a stress day it converts would-be RISK_OFF votes to NEUTRAL and disarms the CHAOTIC override (`0.0 > 0.15` false at `regime.py:290`), letting posture land at NEUTRAL_PREMIUM or better where truthful data would have produced RISK_OFF/DEFENSIVE_SHORT or CHAOTIC/STAY_FLAT. The "VIX level" vote (`_vote_lvl_low`, reads `quote.price`) is the one stress input immune to F-02.
