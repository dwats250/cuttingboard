# Reconciled Findings — five-signal synthesis

Signals: original ledger (23) · blank-Fable independent review · GPT-5.6/Codex independent review · verify pass (F-01/F-02 + regime) · verify pass (2A/2B/2D arithmetic).
Rulings: severities never downgraded below the original ledger; on reviewer disagreement, higher severity wins; findings where the DOCTRINE (not the code) may be wrong are tagged [DOCTRINE?] so planning does not assume a code fix.

Evidence trail: CODEX_REVIEW.md (independent review + 2A/2B/2D arithmetic verify) and FABLE_REVIEW.md (independent review + regime-inflation addendum) sit alongside this file. FINDINGS.md is the original 23-finding ledger.

## Through-line
Began as "safety signals lie by omission." Arithmetic verification widened it: the numbers on the decision surface don't mean what they say. Max risk understated ~2.3x on credit spreads; displayed size ignores the policy meant to cut it; trade-history governance polices trades never made. Beneath both sits one root: a fabricated zero that silently disarms every percentage-based stress guard.

## TIER 0 — Decision-surface correctness (verified; fix first)
- A1 (2A) — CRITICAL — credit-spread max risk understated ~2.3x. 30%-of-width debit proxy becomes dollar_risk for credit strategies (qualification.py:425-441); chain validation prices one near-ATM contract, not both legs (chain_validation.py:222-244). $5-wide bull-put @ $1.50 credit -> printed "max risk $150", true max loss $350. Fix: compute true spread max-loss (width - net credit); price both legs.
- A2 (2B) — HIGH — policy size multiplier never materializes. Lands on size_multiplier, never mutates contracts/dollar_risk (execution_policy.py:179-185); output renders pre-policy OptionSetup (output.py:345-350). Same "computes-but-doesn't-bind" shape as F-07. Fix: apply multiplier before output/export.
- A3 (2D) — HIGH — [DOCTRINE?] recommendations counted as trades. prior_trade_count increments off ALLOW_TRADE audit records, no fill evidence (execution_policy.py:94-102); real journal walled off (manual_journal.py:5). Cooldown/daily-limit/loss-lockout fire on phantom history. Decide intent first: track recommendations or fills?

## TIER 1 — Root cause (fix early; starves three failures)
- F-02 — HIGH — fabricated pct_change=0.0 on missing previous_close (ingestion.py:311) + NaN->0.0 twin (normalization.py). Make missing data loud. Starves the daily kill-switch blind, the CHAOTIC-override blind, and the regime-vote miscolor at once.

## TIER 2 — Trader-facing safety (silent-degradation cluster)
- F-01 — CRITICAL — hourly channel never checks kill switch; renders false "kill_switch: False". Critical stands (Codex argued High; tie -> Critical). Carry the CHAOTIC-mirror nuance (regime.py:290, threshold 0.15 mirrors one of three legs) into the fix.
- F-08 — HIGH — hourly can publish broken-but-green; fresh ERROR/HALT artifacts pass readiness (check_readiness.py checks key presence, not status). Real 2026-07-07 precedent; PRD-250 patched only the viewer.
- F-07 — HIGH — macro-pressure failure -> "unconstrained, full size" on any exception.

## TIER 3 — Freshness & durability
- C1 (Codex miss C) — HIGH — "freshness" measures fetch time, not market time. fetched_at_utc=datetime.now(); no exchange timestamp. Stale weekend/holiday/delayed prices certify fresh. Invalidates F-23's Sunday-halt claim.
- F-06 — HIGH (held) — non-atomic writes on load-bearing artifacts. Banked corrections: impossible line cite (hourly_alert.yml:386-388 in a 216-line file) and cross-workflow-concurrency portion are wrong (separate runner filesystems); in-process unlocked appends and torn-map wedge are real.
- F-03 — HIGH (held) — no run is replayable. Forensic gap; lets future silent failures hide.

## TIER 4 — Regime integrity (corroborated x3)
- Regime confidence inflates on optional-symbol dropout (no quorum floor); breadth/EXPANSION path returns confidence=1.0, total_votes=0 (Codex miss E). Bounded blast radius: only IWM and BTC-USD are optional voters (the other vote-feeders are HALT_SYMBOLS, so dropout is 8->6 votes max, not 8->2); the extreme case is unreachable in production. Still crosses one posture tier on identical evidence, and compounds F-02. Fix: minimum-coverage floor before emitting confidence/posture.

## TIER 5 — Governance / the fence
- F-04 / F-05 — HIGH (held) — HIGH-RISK gate bypassable; empty artifact satisfies it; CLAUDE.md unprotected; no CODEOWNERS. Codex confirmed live GitHub settings: only "test" required, no approvals, admin enforcement off. Delegation gate — close before any unbabysat agent merging.

## TIER 6 — Mediums (held per no-downgrade rule)
F-09 [DOCTRINE? documented fail-open], F-10, F-11, F-12, F-13, F-14, F-15 [DOCTRINE? sidecar doctrine self-contradicts], F-16, F-17 (Codex corrected "all readers" overstatement — execution_policy.py and evaluation.py do fail loud; finding narrows but holds).

## TIER 7 — Lows / documented-design / docs-drift
F-19, F-20 [documented anti-orphan staging, workflow_dispatch-only until PRD-188], F-21 [RECLASSIFIED — both reviewers: not parasitic state; it's a stub returning MIXED/0.0/0.0; the defect is canonical docs (architecture.md, artifact_flow_map.md) describing a functioning persisted router that does not exist], F-22, F-23 (Codex corrected the freshness leg — see C1).

## Additional Codex misses to log (read-verified, not deep-verified)
- DST: daily workflow fixed at 13:00 UTC, no standard-time schedule (hourly carries dual schedules, daily does not) — Medium.
- Cross-process Telegram rate-limit/dedup is process-local module globals only; two channels share credentials with overlapping summer schedules — Medium.
- ORB window 09:30-09:35 may be 6 bars not 5 — CANNOT DETERMINE, needs a captured yfinance frame proving start- vs end-stamped bars.

## Remaining arithmetic pass (top three promoted to Tier 0)
Still owed a dedicated pass: _estimated_debit heuristic soundness beyond max-loss, ATR/EMA formula correctness, R:R computation, sizing math end-to-end.

## Build-order decision (OPEN — operator sets at /plan)
Surface-first (A1 -> F-02 -> F-01) if babysat: kills biggest live money risk first.
Fence-first (F-04/F-05) only if agents merge unbabysat.
Current lean: surface-first, operator reviewing merges. Fence early, A1 is #1.
