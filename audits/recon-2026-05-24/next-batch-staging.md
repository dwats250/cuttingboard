# Next Batch Staging — Cuttingboard

## Context

Cutting Board's notification surface drifted into a shape that doesn't match how Dustin actually uses it. Five PRDs in the 141/144/148/149 arc built a PT-anchored hourly Telegram window (9 slots, 06:00–13:00 PT) plus daily/Sunday/intraday-mode triggers — but the working anchor going forward is "will I actually use this." The hourly cadence produces more pulses than Dustin reads, and the intraday-mode alerts (post-ORB, mid-morning, power-hour) layer on top.

The replacement is narrower and **prescriptive**: three PT-anchored Telegram reports per day, each scoped to a specific trading job rather than to a generic "status update" framing.
- **06:00 PT pre-market** — one fully-specified trade ready to type into Moomoo, or explicit `NO TRADE`.
- **09:30 PT mid-session** — binary kill / hold against open positions. Not a status update.
- **13:30 PT post-session** — tomorrow's seed. What fired, what didn't and why, carry-over qualified setups, flags for tomorrow.

Every other notification cadence retires. Daily + Sunday + intraday-mode + hourly all go.

The prescriptive shift exposes real pipeline gaps. The contract today emits symbol/direction/entry/stop/target but drops absolute strikes, calendar expiry, dollar risk, and account-equity-driven position size. Each gap is a prereq PRD (B1–B11) that lands before its consuming report unit. These prereq PRDs are the real cost of the shift and are listed under each report unit below.

This document stages the work as placeholder-grade units. No PRDs are drafted yet; each unit becomes its own PRD when picked up, with `prd-authoring-verified` running at that point.

**Constraints (binding for every unit below):**
- Anchor: "will I actually use this when trading." Each report unit must answer a specific trader question (what do I buy at 6 AM / do I close anything at 9:30 / what carries to tomorrow). Anything that doesn't answer one of those is on the kill list.
- No new analytical features this batch. No Phase 2 work. No Polygon revival.
- Telegram is the only notification transport. ntfy is gone.
- Cuts before additions — W1 + W2 land before W3–W5.
- Each PRD respects `CLAUDE.md § operational rules` (strict scope locking, read-only sidecars by default).

**Out of scope for the entire batch:**
- `runtime.py` refactor (acknowledged debt, re-eval 2026-08-15).
- New sidecars or new decision-feeding logic.
- Dashboard semantic changes (W6 is visual-only review, not redesign).
- Phase 2 trade evaluation features.

---

## Work Units

### W1 — Retire current notification cadences (the cut)

**Scope.** Audit every notification path active today (hourly via `cuttingboard/notifications/hourly_slot.py`; daily + Sunday via `cuttingboard/runtime.py` notify modes; intraday modes `NOTIFY_PREMARKET / NOTIFY_ORB_TRAJECTORY / NOTIFY_POST_ORB / NOTIFY_MIDMORNING / NOTIFY_POWER_HOUR / NOTIFY_MARKET_CLOSE` exported from `cuttingboard/notifications/__init__.py`). For each path: identify the originating PRD, the workflow cron entry, the call site in `runtime.py`, and the artifact it writes. Delete the call site, retire the formatter, remove the cron entry. Cap PRDs 141/144/148/149 — and any earlier PRD whose behavior is being deleted (PRD-018 daily/Sunday suppression gate, PRD-101 hourly truth contract, PRD-124 hourly header/body, PRD-127/128 hourly readiness, PRD-141 slot canonicalization, PRD-149 PT-window, etc.) — with **DEPRECATED** status in `docs/PRD_REGISTRY.md` and a pointer to the replacement PRD that lands in W4.

**Dependencies.** Must complete before W4 wires anything new. W3 (Telegram output layer review) can run in parallel with the *audit* portion of W1, but the *deletion* portion blocks W3 finalization.

**Success criteria.**
- `cuttingboard/notifications/hourly_slot.py` deleted.
- `.github/workflows/hourly_alert.yml` deleted.
- `.github/workflows/cuttingboard.yml` cron block trimmed to whatever W5 decides (placeholder: 1–3 entries only).
- Every retired PRD row in `docs/PRD_REGISTRY.md` reads `DEPRECATED` with a `→ PRD-NNN` pointer.
- `grep -rn "hourly\|intraday_mode\|NOTIFY_PREMARKET\|NOTIFY_ORB" cuttingboard/ tests/` returns only test-guard hits (the BANNED-style assertions that pin the surface as removed).
- Test baseline post-cut documented in `docs/PROJECT_STATE.md` (expected: net decrease).

**Explicit non-goals.**
- Don't preserve any legacy formatters "in case." Pure deletion.
- Don't rewrite `runtime.py` notify wiring beyond removing the deleted entrypoints.
- Don't touch `logs/audit.jsonl`'s historical entries; PRD-154/155 doctrine is binding.

---

### W2 — Doc residue sweep (ntfy + Polygon)

**Scope.** Full residue sweep per recon findings. Three known-stale files:
- `docs/runbook.md` — multiple `ntfy` + `send_ntfy` references.
- `docs/system_logic_map.md` — formatter description line still says "ntfy."
- `cuttingboard/notifications/__init__.py` — docstring mentions at lines 112, 184, 293.

Plus regenerate `.claude/skills/generated/notifications/SKILL.md` (autogenerated, carries the stale name) via `scripts/gitnexus-analyze.sh --skip-agents-md`.

Plus a final `grep -ri "ntfy\|polygon" --include="*.md" --include="*.py"` across the repo, with each hit triaged into one of: (a) delete, (b) historical and keep (audit/PRD history, DECISIONS.md, banned-import test guards), (c) update in place.

**Dependencies.** None. Can run in parallel with W1 audit. Should not run after W3/W4 (would generate churn against new docstrings).

**Success criteria.**
- Triaged grep output saved to `audits/recon-2026-05-24/ntfy-polygon-sweep.md`.
- All (c)-class hits resolved.
- Skill regen artifact landed.
- `grep -ri ntfy --include="*.md"` returns only `docs/prd_history/` + `docs/DECISIONS.md` + audit files.

**Explicit non-goals.**
- Don't touch banned-import test guards (`tests/test_market_map.py:458`, `tests/test_scenario_engine.py`, `tests/test_levels.py`, `tests/test_prd006_notification_transport.py`). Those are intentional fences.
- Don't expand the sweep to other deprecated symbols — just ntfy + polygon.

---

### W3 — Telegram output layer review

**Scope.** Document the post-cut Telegram surface. After W1 lands, list what remains in `cuttingboard/notifications/`: which formatters survive, what data they consume from `logs/latest_payload.json` / `logs/latest_run.json`, where the transport call lives (currently `cuttingboard/notifications/formatter.py:format_telegram_alert`). Identify the minimum interface the three new reports in W4 will call. Decide whether `notifications/__init__.py` needs a re-export trim and whether `cuttingboard/notifications/state.py` (notification state tracking) survives the cut or retires with W1.

**Dependencies.** Reads the post-W1 tree. Blocks W4 (W4 needs a stable transport contract to target).

**Success criteria.**
- Written design note (not a PRD yet) listing: surviving modules, surviving public exports, transport call site, expected input contract for the three new reports.
- One question answered: does the W4 PRD need to refactor `format_telegram_alert` or can it call it as-is?
- Reuses existing utilities — `format_telegram_alert`, `cuttingboard/delivery/payload.py:build_report_payload` — not new ones, unless the design note justifies the addition.

**Explicit non-goals.**
- No transport rewrite. Telegram bot ID + chat ID handling stays as-is.
- No new state-tracking mechanism. If `state.py` is retained, it's retained as-is.

---

### W4 — Pre-market report: prescriptive output (06:00 PT)

**Anchor.** "Will I actually use this when trading." One fully-specified trade ready to type into Moomoo — or an explicit no-trade. No interpretation required at the kitchen table.

**Required report shape (top to bottom).**
1. **Header verdict.** `TRADE` / `NO TRADE` / `HALT` — one word.
2. If `TRADE`: symbol + structure + long leg strike + short leg strike + calendar expiry date + debit-or-credit + max risk in dollars + position size (number of contracts) + invalidation level + skip conditions.
3. Supporting context below the verdict (regime / qualification reasoning), short.

**Existing pipeline coverage (what's already emitted).** Per the 2026-05-24 contract-emission recon:
- Symbol, direction, entry, stop, target — emitted at `cuttingboard/contract.py:315-341`.
- `strategy_tag` (e.g. BULL_CALL_SPREAD) emitted — implies "spread, not single-leg" but doesn't label it.
- `timeframe` (integer DTE) emitted — not a calendar date.
- `invalidation_guidance` dict (status / action / reason / triggered_by / thesis_status) emitted — covers most of "skip conditions."
- `policy_reason` + `policy_allowed` + `size_multiplier` (regime-confidence-only float 0.0–1.0) emitted.

**Hard blockers (pipeline gaps that must close before W4 ships).** Each is its own prerequisite PRD. They are the real cost of the prescriptive shift:

| Blocker | Where the value exists today | Where it's dropped | Prereq PRD scope |
|---|---|---|---|
| **B1. Absolute strikes.** `long_strike` and `short_strike` in `OptionSetup` (`cuttingboard/options.py:84-106`) carry only relative labels like `"1_ITM"` / `"ATM"`. Absolute dollar strikes are never picked. | `OptionSetup` (relative labels only) | Never computed | Pick absolute strikes in `options.py` from current_price + strike_distance + chain step. Emit through to contract. |
| **B2. Calendar expiry date.** Only DTE integer ("14") flows through. No "2026-05-31" anywhere. | DTE only | DTE only | Resolve DTE → next valid weekly/monthly expiry calendar date in `options.py`. Emit through to contract. |
| **B3. Per-candidate dollar risk.** `QualificationResult.dollar_risk` computed at `qualification.py:662` as `max_contracts × spread_width × 100`. | `QualificationResult` | Dropped at contract assembly | Pass `dollar_risk` through `contract._build_trade_candidates` into the per-candidate dict. |
| **B4. Account-equity-driven sizing.** No `ACCOUNT_EQUITY` config exists. `max_contracts = floor(150 / (spread_width × 100))` at `qualification.py:643` is hardcoded to a $150 base, untied to equity. | Hardcoded $150 base | n/a | Add `ACCOUNT_EQUITY` (and `MAX_RISK_PCT_PER_TRADE`) to `config.py`. Rewrite the `max_contracts` formula to compute from those. Emit `position_size` (contract count) through to contract. |
| **B5. Debit/credit per contract.** `_estimated_debit(strike_distance)` at `options.py:387-389` (30% of strike_distance × 100) exists in `OptionSetup` but doesn't reach the contract. | `OptionSetup` | Dropped at contract assembly | Carry `estimated_debit` (and direction-of-flow: debit vs credit per `strategy_tag`) through into the candidate dict. |

**Scope of W4 itself (after B1–B5 land).** Build the pre-market 06:00 PT report module. Read the contract's per-candidate dict (now populated), pick the single top-ranked qualified candidate (or emit `NO TRADE` if none survive policy + invalidation gates), format the verdict block, and send via the Telegram transport (per W3). Single-trade output by design — multi-trade pre-market is on the kill list below.

**Dependencies.**
- Blocked by W1 (deletion of conflicting cadences).
- Blocked by W3 (transport contract review).
- Blocked by B1–B5 prereq PRDs. None of them are W4 itself — each is its own scope-locked PRD against the pipeline layer named in the table. Each follows `prd-authoring-verified` and lands its own test deltas.
- DST-correct PT anchoring reuses the `America/Vancouver` resolver from `cuttingboard/notifications/hourly_slot.py` (keep the tz helper, drop the slot canonicalization).

**Testable success criteria.**
- 06:00 PT fixture run produces a Telegram message whose body contains: symbol, structure label, both absolute strikes, calendar expiry (YYYY-MM-DD), debit-or-credit dollar amount, max risk dollars, position size (integer contracts), invalidation price, ≥1 skip condition (or "none").
- 06:00 PT fixture run with no surviving candidate produces a Telegram message with header `NO TRADE` and a one-line reason from the highest-ranked rejected candidate's `decision_trace.reason`.
- `logs/latest_payload.json` post-run carries every B1–B5 field per candidate. A new schema test in `tests/test_payload_*.py` pins the field set.
- Idempotency: same-slot rerun produces zero additional Telegram sends; `logs/last_report_slot.json` carries the persisted slot. Failed Telegram send does NOT persist.

**Explicit non-goals.**
- No multiple trades in one report. One pick or `NO TRADE`. Picking logic = highest-confidence surviving candidate; tie-break by symbol alphabetical.
- No probability-of-profit, expected-value, or scenario-tree output. VISION.md non-prediction rule binds.
- No interactive reply / "execute trade" handling. One-way push only.
- No single-leg options. Existing pipeline only generates spreads; that constraint stands.
- No real-time strike-by-strike chain pricing. B5 uses the existing estimated-debit heuristic; live chain quotes are out of scope.

---

### W5 — Mid-session report: binary kill/hold (09:30 PT)

**Anchor.** Not a status update. Hold = silent (or one line). Kill = loud and specific. The trader's question this answers: "Do I close anything right now?"

**Required report shape.** Two modes only:
- **HOLD mode.** Silent send suppressed, or single line: `HOLD — no action`. Nothing more.
- **KILL mode.** Specific: `Close GDX 112/114 call spread now — invalidation hit at 109.40`. Symbol + structure + strikes + trigger reason. One sentence.

**Existing pipeline coverage.** Most of the kill signal already exists:
- `invalidation_guidance.action == "REDUCE_OR_EXIT"` at `cuttingboard/invalidation.py:156-169` already downgrades ALLOW_TRADE to BLOCK_TRADE when `invalidation_guidance.status == "TRIGGERED"`.
- Gap-down permission revocation lives in `cuttingboard/intraday_state_engine.py` (PRD-151), reachable at `runtime.py:1205` `_apply_intraday_short_permission`. **Not currently emitted to contract** — that's a small fix (carry `trades_allowed` + reason into the candidate record).
- Post-trade evaluation (`cuttingboard/evaluation.py:140-227`) records STOP_HIT / TARGET_HIT — but it runs post-session, not mid-session.

**Hard blockers (smaller than W4).**
| Blocker | Resolution |
|---|---|
| **B6. Open-position state.** No concept of "I'm currently in this trade" exists. The mid-session report needs to know which of yesterday/today's `TRADE` verdicts was actually taken to answer "close what?". | Tiny manual journal — `logs/open_positions.jsonl` written manually by Dustin after entering. The report reads it; no auto-entry-detection. Out of scope: any auto-fill from broker. |
| **B7. Mid-session invalidation re-eval.** `apply_invalidation_gate()` runs in the main pipeline; it doesn't currently run on a 09:30 PT timer against open positions specifically. | Re-run the invalidation gate against `open_positions.jsonl` at 09:30 PT; emit kill signal when status transitions to TRIGGERED. |
| **B8. Gap-down permission → contract emission.** Same gap noted in W4 prereqs but smaller scope here — just need `trades_allowed`/`reason` on the candidate. | Carry the field through. If overlapping with W4 prereqs, fold into the same PRD. |

**Scope of W5 itself.** Build the 09:30 PT report. Read `logs/open_positions.jsonl` + latest contract/invalidation state. Emit HOLD or KILL per open position. Multiple KILLs concatenate (one line each). Empty journal = silent (no send) or one-line "HOLD — no open positions."

**Dependencies.**
- Blocked by W1, W3 (same as W4).
- Blocked by B6/B7/B8 prereq PRDs.
- Independent of W4's B1–B5 — different output path, different report.

**Testable success criteria.**
- Fixture: 1 open position + invalidation TRIGGERED → exactly one KILL line in Telegram body naming symbol, strikes, and trigger reason.
- Fixture: 1 open position + invalidation NOT_TRIGGERED → silent send (or single-line HOLD per config).
- Fixture: empty `logs/open_positions.jsonl` → silent (no Telegram send).
- Fixture: 2 open positions, 1 TRIGGERED + 1 OK → one KILL line, no mention of the OK position.

**Explicit non-goals.**
- No "consider scaling out" / "consider trimming" — binary kill/hold only.
- No P&L reporting in the body. Position context (current price vs entry) is allowed if trivially available; not a blocker.
- No real-time monitoring loop. Single 09:30 PT fire only. Between-slot invalidation is out of scope for this batch.
- No auto-detection of open positions from broker / from `audit.jsonl`. Manual journal only.

---

### W6 — Post-session report: tomorrow's seed (13:30 PT)

**Anchor.** Feeds W4. The 06:00 PT prescriptive verdict depends on what this report's outputs say. Three states per setup: **fired** (entry triggered, outcome known), **didn't fire** (with reason), **carry-over** (qualified but still valid for tomorrow).

**Required report shape.**
1. **What fired.** Per filled trade: symbol, structure, outcome (TARGET_HIT / STOP_HIT / NO_HIT), R-multiple.
2. **What didn't and why.** Per unfilled qualified candidate: symbol, structure, reason from {GATE_FAILED, INVALIDATION_HIT, NEVER_TRIGGERED}.
3. **Carry-over qualified setups.** Per still-valid setup that didn't fire today and has invalidation level intact: symbol, structure, levels.
4. **Flags for tomorrow.** Macro events (FOMC etc.), regime transitions in progress, any explicit do-not-trade conditions.

**Existing pipeline coverage.**
- `run_post_trade_evaluation()` at `cuttingboard/evaluation.py:37` emits TARGET_HIT / STOP_HIT / NO_HIT + R_multiple per ALLOW_TRADE decision. **Covers "what fired."**
- Audit summary at `cuttingboard/contract.py:394` counts gate failures by gate — covers aggregate "GATE_FAILED" but not per-candidate.
- Macro tape and regime artifacts feed "flags for tomorrow" — already on payload.

**Hard blockers.**
| Blocker | Resolution |
|---|---|
| **B9. Per-candidate rejection trace.** Today's audit summary at `contract.py:394` only counts rejections by gate type. Per-candidate rejection reasons are dropped before reaching the contract. The post-session report needs the symbol-level "why" — not just "12 candidates failed STOP gate." | Emit per-rejected-candidate trace (symbol, gate that failed, value vs threshold) into a new payload field. Trim to a sensible ceiling (top 20 by gate-distance, say) to keep payload size sane. |
| **B10. NEVER_TRIGGERED vs INVALIDATION_HIT distinction.** Evaluation today says NO_HIT for both "entry trigger never armed" and "trigger armed but invalidation intervened." | Split NO_HIT into NEVER_TRIGGERED + INVALIDATION_INTERVENED in `evaluation.py:27-30` based on whether the entry trigger condition was met during the evaluation window. |
| **B11. Carry-over qualification state.** Grep returned zero hits for "carry / persistent / qualified_yesterday" — no state survives between runs. Today every qualification re-evaluates from scratch. | Add a small carry-over file — `logs/carry_over_setups.jsonl` — written at post-session, read at next pre-market run. Each entry: symbol + structure + invalidation_level + expiry_window. Pre-market run validates each entry against today's data; expired or invalidated entries are dropped. Not a sidecar in the architectural sense — read-only, single producer, single consumer, scoped to W4 + W6. |

**Scope of W6 itself.** Build the 13:30 PT report module. Read evaluation artifacts + the new per-candidate rejection trace + write `logs/carry_over_setups.jsonl`. Format the four-section report and send via Telegram transport.

**Dependencies.**
- Blocked by W1, W3.
- Blocked by B9/B10/B11 prereq PRDs.
- Feeds W4: B11 carry-over file is read by W4. So strictly: W6 carry-over output must exist before W4 can consume it. But the W4 PRD can ship without carry-over (treat empty file as no carry-over) and the carry-over wiring lands incrementally.

**Testable success criteria.**
- Fixture: 1 fired trade (TARGET_HIT, R=+2.0) + 3 unfired candidates (1 GATE_FAILED, 1 INVALIDATION_HIT, 1 NEVER_TRIGGERED) → Telegram body lists all 4 with correct labels.
- Fixture: 2 qualified setups that didn't fire and remain valid → `logs/carry_over_setups.jsonl` post-run has exactly 2 entries.
- Fixture: 2 qualified setups that didn't fire but invalidation level breached intra-session → `logs/carry_over_setups.jsonl` has 0 entries.
- Pre-market fixture (W4 territory) with non-empty `carry_over_setups.jsonl` ingests entries and lists them under candidates evaluated.

**Explicit non-goals.**
- No P&L aggregation across sessions. Single-session evaluation only (existing PRD-075 contract).
- No backtesting against historical bars (VISION.md non-goal).
- No prediction/forecast for tomorrow's regime. "Flags" are observational only — list known scheduled events, not "we expect risk-on."
- No carry-over of failed trades for "let's retry tomorrow" — invalidation closes a setup permanently for the cycle.

---

### Kill list (considered and rejected)

These were on the table at some point during this batch's scoping and are explicitly NOT part of the plan:

- **Old W4 unified "three reports with macro/regime context" framing.** Superseded by the prescriptive shift. The "context-heavy" version of the reports asked the trader to interpret regime + qualification themselves; the new framing does the interpretation upstream.
- **Multi-trade pre-market output.** Considered listing top-3 candidates ranked. Rejected: defeats the "type into Moomoo" anchor. One pick or NO TRADE.
- **Mid-session status update / "here's how the market looks now."** Rejected by anchor: not a trading signal, not used.
- **Probability-of-profit, expected-value, scenario-tree pre-market output.** Rejected by VISION.md non-prediction rule.
- **Auto-detection of open positions from broker statements / from `logs/audit.jsonl` ALLOW_TRADE rows.** Considered for W5. Rejected: PRD-153/156 just established that statement-based detection produces no joinable signal; audit-row inference assumes Dustin took every ALLOW_TRADE, which is false. Manual `open_positions.jsonl` is the right boundary.
- **Real-time chain pricing for B5 debit/credit.** Considered. Rejected for this batch: existing 30% heuristic stays. Live chain pricing would be its own dependency-class PRD (Polygon revival territory), explicitly out per VISION.md.
- **Interactive Telegram reply handling.** Rejected: out of scope, no consumer.
- **Real-time intra-session invalidation monitoring (continuous loop between 09:30 and 13:30 PT).** Considered for W5. Rejected: complicates scheduling, fights GitHub Actions cron model. Single-slot KILL is the cut.
- **Auto-trim / auto-exit signaling (scale out, trim, hedge).** Rejected: binary kill/hold only.
- **Backtesting the new reports against historical data.** Rejected by VISION.md "no backtesting" non-goal.
- **Generic "carry-over sidecar" with multi-consumer ambitions.** Considered. Rejected: scope-limited to W4 ↔ W6 only. If a third consumer appears later, promote it to a sidecar then.

---

### W7 — Scheduling decision + instrumentation

**Scope.** Two workflows exist today: `.github/workflows/cuttingboard.yml` (engine + daily/Sunday/intraday) and `.github/workflows/hourly_alert.yml` (hourly Telegram). Decide post-cut topology:
- **Option A:** Collapse to one workflow with three cron entries — one per PT slot.
- **Option B:** Keep the engine workflow on its own cadence (prefetch + daily premarket pipeline run) and a separate notify workflow that consumes the latest artifacts at the three PT slots.

Instrumentation: each cron fire writes a row to a new (or repurposed) `logs/scheduler.jsonl` so missed/late fires surface in audit. Reuse the PRD-144 redundancy pattern (±5 min cron entries) since GitHub Actions has demonstrably dropped fires (see PROJECT_STATE 2026-05-19 entry).

**Dependencies.** Reads W4/W5/W6 scheduling needs. Blocks final closeout — without W7 the new cron entries aren't live.

**Success criteria.**
- One design choice (A or B) locked before code.
- `.github/workflows/*.yml` post-cut topology landed.
- `logs/scheduler.jsonl` (or named alternative) writes one row per fire with `slot_pt`, `fire_utc`, `lag_seconds`, `status`.
- Each PT slot has at least one ±5 min backup cron entry (per PRD-144 lesson).

**Explicit non-goals.**
- No new scheduler infrastructure outside GitHub Actions. No cron daemons, no external scheduler.
- No alerting on scheduler drift in this batch — `logs/scheduler.jsonl` is observation-only.

---

### W8 — Dashboard visual layer review

**Scope.** Read-only review of `cuttingboard/delivery/dashboard_renderer.py` and the macro-tape layout (`cuttingboard/delivery/macro_tape_layout.py`). Three deliverables:
1. Visual inventory: a screenshot or rendered-HTML capture of the current dashboard at every state (TRADES / NO TRADE / HALT / inactive).
2. Drift log: what's on the dashboard that the new three-reports cadence makes redundant? What's missing that the new cadence assumes?
3. Decisions list: per-section keep/cut/defer, written to `audits/recon-2026-05-24/dashboard-visual-review.md`.

No code changes. Decisions feed into a follow-up PRD outside this batch.

**Dependencies.** Best done after W4/W5/W6 land so the "what's redundant" question has a concrete answer. Can be sequenced as the last unit.

**Success criteria.**
- Visual capture artifacts saved under `audits/recon-2026-05-24/dashboard-screenshots/`.
- Drift log written.
- Per-section keep/cut/defer table complete.

**Explicit non-goals.**
- No renderer changes.
- No new sections.
- No re-skinning. This is a review, not a redesign.

---

## Sequencing

```
W1 audit ──┬──> W1 deletions ──┬─────────────────────────────────────┐
W2 sweep ──┘                   │                                      │
                   W3 review ──┤                                      │
                               │                                      │
                               ├──> B1..B5 prereqs ──> W4 (pre-mkt) ──┤
                               ├──> B6..B8 prereqs ──> W5 (mid)      ─┼──> W7 (sched) ──> W8 (dash)
                               └──> B9..B11 prereqs ─> W6 (post)    ──┘
```

- W1 audit + W2 sweep + W3 review run in parallel (read-only / independent).
- W1 deletions block W3 finalization, B-series prereqs, and the three report units.
- B1–B11 prereq PRDs each scope-locked to their pipeline layer. Land before their consuming report unit. Several may fold together where they touch the same module (e.g. B1+B2+B5 all in `options.py` + contract pass-through could be one PRD; B6+B7+B8 could be one PRD).
- W4 / W5 / W6 are independent of each other in code (different report modules, different blockers). Order by trader value: W4 first (the daily anchor), W5 second (kill switch), W6 third (feeds tomorrow's W4).
- W7 lands once at least one report module exists.
- W8 last.
- Total batch size: roughly **6 report-and-cut PRDs + 8–11 prereq PRDs**, depending on bundling. Larger than the original 6-unit framing — that's the cost of the prescriptive shift made visible.

## Verification

End-to-end of the whole batch (placeholder — each PRD will tighten its own FAIL conditions):

```bash
# W1: no surviving hourly/intraday call sites
grep -rn "hourly\|NOTIFY_PREMARKET\|NOTIFY_ORB" cuttingboard/ tests/

# W2: no ntfy outside history
grep -ri "ntfy" --include="*.md" --include="*.py" | grep -v "prd_history\|DECISIONS\|test_prd006"

# B1–B5: contract per-candidate dict carries new fields
python3 -m cuttingboard --fixture
python3 -c "import json; c=json.load(open('logs/latest_contract.json'))['trade_candidates'][0]; \
  assert all(k in c for k in ['long_strike','short_strike','expiry_date','dollar_risk','position_size','estimated_debit'])"

# W4 / W5 / W6: each report fires
python3 -m cuttingboard.notify_report --slot 06:00 --force  # pre-market: TRADE or NO TRADE verdict block
python3 -m cuttingboard.notify_report --slot 09:30 --force  # mid-session: HOLD or KILL line(s)
python3 -m cuttingboard.notify_report --slot 13:30 --force  # post-session: four sections + carry-over write

# W6 → W4 handoff
test -s logs/carry_over_setups.jsonl

# W7: scheduler log exists
test -f logs/scheduler.jsonl

# Suite
python3 -m pytest tests -q
python3 -m ruff check cuttingboard tests
python3 -m cuttingboard  # status=SUCCESS

# Registry consistency
python3 tools/validate_prd_registry.py
```

## Critical files (referenced, not modified by this plan)

- `docs/PRD_REGISTRY.md` — DEPRECATED flips land here in W1.
- `docs/PROJECT_STATE.md` — Current State + Last completed PRD update at each PRD closeout.
- `docs/DECISIONS.md` — the "retire hourly cadence + prescriptive shift" decision belongs here with the W1 PRD link.
- `cuttingboard/contract.py` — per-candidate field passthrough (B3/B5/B8 land here).
- `cuttingboard/options.py` — absolute strike selection + calendar expiry resolution (B1/B2).
- `cuttingboard/qualification.py` — equity-driven sizing rewrite (B4).
- `cuttingboard/config.py` — `ACCOUNT_EQUITY` + `MAX_RISK_PCT_PER_TRADE` (B4).
- `cuttingboard/evaluation.py` — NEVER_TRIGGERED / INVALIDATION_INTERVENED split (B10).
- `cuttingboard/intraday_state_engine.py` + `cuttingboard/runtime.py:1205` — gap-down permission passthrough (B8).
- `cuttingboard/invalidation.py` — mid-session re-eval against open positions (B7).
- `cuttingboard/notifications/__init__.py` + `formatter.py` + `hourly_slot.py` + `state.py` — W1/W3.
- `cuttingboard/runtime.py` — call-site removals only, no refactor.
- `.github/workflows/cuttingboard.yml` + `hourly_alert.yml` — W1/W7.
- `logs/open_positions.jsonl` (new, manual) — W5/B6.
- `logs/carry_over_setups.jsonl` (new) — W6/B11 → W4.
- `audits/recon-2026-05-24/` (new directory) — design notes for W2, W4, W5, W6, W8.
