# Market State Panel — GOV-2 INITIAL PACKET REVIEW (Event-1) — durable record

**Event type:** `INITIAL PACKET REVIEW` (GOV-2 §2 step 3, §7).
**Reviewer identity / capability role:** Codex (`codex-cli 0.147.0`, model reasoning
effort `high`), acting as the independent fresh-context material-packet reviewer.
**Reviewed commit SHA:** `66d9731b8b0e86d320e0e98c1d12e691803feb25` (packet v0.1),
against code baseline `main` @ `731b5ee`.
**Review date:** 2026-08-22.
**Invocation:** `codex exec -s read-only -c model_reasoning_effort=high` (prompt via
stdin; verdict from stdout). No repo write access; final git status clean at the
exact packet HEAD (attested below).
**Independence / run-isolation:** fresh context, not the authoring session;
read-only sandbox; reviewed the packet plus repository surfaces, not another
review's prose (attestation reproduced verbatim below).

**VERDICT: FINDINGS** (2 BLOCKING, 2 BOUNDARY, 3 P1).

Author independently re-verified every finding against source at `66d9731`
before dispositioning (see the consolidated correction record). Summary of
findings and author dispositions:

| # | Sev | Claim | Author verification | Disposition |
|---|---|---|---|---|
| F1 | BLOCKING | Hourly trend-structure gets DAILY OHLCV (`fetch_ohlcv` = 6-month daily), so SPY `price_vs_vwap` is always `NOT_COMPUTED` on the hourly board — INTRADAY carrier A cannot truthfully supply hourly vs-VWAP | CONFIRMED: `ingestion.py:119-124`; committed snapshot SPY `price_vs_vwap="NOT_COMPUTED"` (`logs/trend_structure_snapshot.json`); no intraday-session fetch on the hourly notify path (`fetch_intraday_session_bars` only at `runtime:1238` inside `_run_pipeline`) | ESCALATED — owner design-direction decision (DESIGN INCOMPLETE) |
| F2 | P1 | Hourly PERMISSION carrier is `latest_hourly_run.json.permission`, not the contract/payload (which is null except operator-lock) | CONFIRMED: `contract.py:251-259` (no permission field); `runtime:2278-2284` (operator-lock only); `latest_hourly_run.json` permission set, `latest_hourly_payload.json` permission null; renderer reads run first (`dashboard_renderer.py:2172-2175`) | ACTIONED — carrier attribution corrected |
| F3 | BLOCKING | Arrow-cut proof missed `test_prd220_tradables_arrow_before_price` (asserts a `tradable-arrow` span) | CONFIRMED: `tests/test_dashboard_renderer.py:4007-4013` | ACTIONED — enumerated (file already in cone) |
| F4 | BOUNDARY | Placement affects the test boundary; `test_dash_system_state.py` extracts `system-state`..`candidate-board` and forbids the raw permission line (PRD-219) — an above-cards panel re-rendering permission would fail it | CONFIRMED: `tests/test_dash_system_state.py:82-93,109-127` | ACTIONED (cone + placement constraint) + ESCALATED (D-3 placement is now an owner decision) |
| F5 | BOUNDARY | Docs cone omits `CALL_SITE_MAP.md` (analogous GEX seam recorded there) and leaves `PROJECT_STATE.md:224` PRD-199 retirement inside the "any file beyond §8" tripwire | CONFIRMED: `docs/CALL_SITE_MAP.md:3-7,63-69`; `docs/PROJECT_STATE.md:224` | ACTIONED — cone + tripwire carve-out |
| F6 | P1 | Mutation matrix lacks a PERMISSION-unavailable case; strengthen no-score check to structural (exact six axes / no aggregate row), not lexical | CONFIRMED: packet M3 present-only; M12/M13 lexical | ACTIONED — matrix strengthened |
| F7 | P1 | `12/12 captured` PARTICIPATION default conceals partial absence (movement preserves per-symbol `n/a`); a GEX-net POSITIONING value would drop the mandatory configured-assumption qualifier (`gex_card.py:175-191`) | CONFIRMED: `watchlist_sidecar.py:76-92`, `movement_card.py:86-93`; `gex_card.py:175-191` | ACTIONED (partial-absence semantics + qualifier requirement) + ESCALATED (D-1/D-2 value choice is an owner decision) |

---

## Codex Event-1 output (verbatim)

```
VERDICT: FINDINGS

F1. BLOCKING — The chosen INTRADAY carrier cannot produce hourly SPY-vs-VWAP values: production trend structure receives daily OHLCV and therefore emits `NOT_COMPUTED`.
Evidence: the hourly path and its all-symbol fallback both call `fetch_ohlcv` (`cuttingboard/runtime/__init__.py:628-631`, `cuttingboard/runtime/__init__.py:2441-2465`); that function explicitly returns six-month daily bars (`cuttingboard/ingestion.py:119-124`, `cuttingboard/ingestion.py:383-402`); trend structure rejects non-intraday frames for VWAP (`cuttingboard/trend_structure.py:39-56`) and classifies them `NOT_COMPUTED` (`cuttingboard/trend_structure.py:120-136`). The committed snapshot corroborates this for SPY (`logs/trend_structure_snapshot.json:66`, `logs/trend_structure_snapshot.json:72`).
Recommended disposition: retract the "carrier A truthfully available" and delivery-only conclusions. Either obtain an explicit owner ruling accepting an always-unavailable hourly INTRADAY row, or select the smallest truthful intraday carrier and renew the runtime/FILES/classification boundary before proceeding.

F2. P1 — Hourly PERMISSION is available to the board, but the packet incorrectly says the normal hourly contract and payload carry it.
Evidence: `build_pipeline_output_contract` creates `system_state` through `_build_system_state` (`cuttingboard/contract.py:122-124`), whose returned fields do not include permission (`cuttingboard/contract.py:251-259`); `_build_hourly_contract` injects permission only for operator lock (`cuttingboard/runtime/__init__.py:2278-2284`). The hourly run summary always supplies it (`cuttingboard/runtime/__init__.py:2363-2369`), and the renderer reads the run first (`cuttingboard/delivery/dashboard_renderer.py:2172-2175`). Current artifacts show run permission present but payload permission null (`logs/latest_hourly_run.json:33`, `logs/latest_hourly_payload.json:64`).
Recommended disposition: amend C1/C4/C5 and the seam trace to name `latest_hourly_run.json.permission` as the normal carrier; add normal, halt, operator-lock, and missing-permission tests.

F3. BLOCKING — The arrow-cut proof misses a non-PRD-199 asserting test that will fail when the span is removed.
Evidence: `test_prd220_tradables_arrow_before_price` explicitly requires a `tradable-arrow` span immediately before the price (`tests/test_dashboard_renderer.py:4007-4013`), while the packet's exact cut surface only calls out PRD-199 tests (`audits/market-state-provenance-panel-material-packet-2026-08/MARKET_STATE_PANEL_MATERIAL_PACKET_v0.1.md:223-230`).
Recommended disposition: enumerate and remove or replace this PRD-220 assertion. The file is already in the cone, so no file-count expansion is needed.

F4. BOUNDARY — Panel placement does affect the test boundary; D-3's "no code-boundary impact" claim is not established, and `tests/test_dash_system_state.py` is missing from the cone.
Evidence: several tests define the system-state region as everything from `id="system-state"` to `id="candidate-board"` and require the raw permission line to be absent (`tests/test_dash_system_state.py:82-93`, `tests/test_dash_system_state.py:109-127`). An above-cards MARKET STATE block that re-renders permission before the candidate board will enter that region and fail these tests.
Recommended disposition: decide placement before certifying the cone; either add `tests/test_dash_system_state.py` and narrow its block extraction, or constrain placement outside that region and prove the file remains unaffected.

F5. BOUNDARY — The documentation cone omits a new high-value call boundary and leaves required retirement bookkeeping outside an "any file beyond §8" tripwire.
Evidence: `CALL_SITE_MAP.md` requires updates when new high-value boundaries are identified (`docs/CALL_SITE_MAP.md:3-7`) and already records the analogous GEX builder/render seam (`docs/CALL_SITE_MAP.md:63-69`), but §8 omits it. `PROJECT_STATE.md` currently says tradables "now show" the arrow (`docs/PROJECT_STATE.md:224`); the packet defers that file (`MARKET_STATE_PANEL_MATERIAL_PACKET_v0.1.md:347-350`) while also tripwiring every file outside §8 (`MARKET_STATE_PANEL_MATERIAL_PACKET_v0.1.md:364-366`).
Recommended disposition: add `docs/CALL_SITE_MAP.md`; explicitly guarantee the PRD-stage `PROJECT_STATE.md` retirement/supersession update and carve that governed bookkeeping step out of the implementation tripwire, or include it in the cone.

F6. P1 — The mutation matrix lacks a PERMISSION-unavailable case despite promising independent honest absence for every axis.
Evidence: M3 covers only PERMISSION present (`MARKET_STATE_PANEL_MATERIAL_PACKET_v0.1.md:376`), while the packet's general contract says any absent or typed-unavailable carrier renders its own row unavailable (`MARKET_STATE_PANEL_MATERIAL_PACKET_v0.1.md:399-408`). Every other axis has an explicit unavailable case in M2/M5/M7/M9/M11.
Recommended disposition: add a mutation-red case deleting/nulling both permitted permission inputs and require only the PERMISSION row to render `unavailable`. Strengthen M12/M13 with an exact-six-axis/no-aggregate-row assertion so an unlabeled numeric composite or global footer cannot evade lexical checks.

F7. P1 — The default PARTICIPATION value can conceal partial absence, and a GEX-net POSITIONING value would drop an existing semantic qualifier.
Evidence: the watchlist producer emits all twelve rows even when quotes and `daily_change_pct` are null (`cuttingboard/watchlist_sidecar.py:76-92`); the existing Movement card preserves that truth as `SYM n/a` (`cuttingboard/delivery/movement_card.py:86-93`, `cuttingboard/delivery/movement_card.py:126-129`). Therefore `12/12 captured` does not prove twelve usable movement observations. Separately, the existing GEX Net display carries the mandatory configured-assumption/not-measured qualifier (`cuttingboard/delivery/gex_card.py:175-191`), while the packet's M6 checks only headline plus delayed-source provenance (`MARKET_STATE_PANEL_MATERIAL_PACKET_v0.1.md:379`).
Recommended disposition: adjudicate D-1/D-2 before review-clean status. Preserve partial `n/a` semantics for PARTICIPATION, and require the configured-assumption qualifier whenever signed net GEX is re-presented; add partial/all-null and qualifier-removal mutations.

INDEPENDENCE + SCOPE: I reviewed the complete packet at HEAD `66d9731b8b0e86d320e0e98c1d12e691803feb25` and repository source at its baseline parent `731b5ee357d5be8ea2a0c29292d9694eaf809b0e`, not another review's prose. I independently confirmed the hourly fetch/normalize/validate/regime chain (`cuttingboard/runtime/__init__.py:549-570`); conditional GEX and Movement rendering plus unconditional red-folder rendering (`cuttingboard/delivery/dashboard_renderer.py:2613-2630`, `cuttingboard/delivery/dashboard_renderer.py:2840-2852`); daily-only SpyObservation/MCC (`cuttingboard/runtime/__init__.py:1511-1541`); and the production final-reader claim itself—one trend-field read at `cuttingboard/delivery/dashboard_renderer.py:1254`, with the surviving price and notification readers using `current_price`/`q.price` (`cuttingboard/delivery/dashboard_renderer.py:1303-1310`, `cuttingboard/notifications/__init__.py:117-126`). The six golden arrow spans are present at `tests/data/dashboard_pre_gex_golden.html:80-85`. MATERIAL and current-surface HIGH-RISK/CONSUMER are correctly classified under `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:18-29` and `docs/PRD_PROCESS.md:456-482`; F1's disposition may require reclassification. No prediction, composite score, timestamp schema, or decision coupling is otherwise introduced by the stated display-only design. Review was read-only; final git status remained clean at the exact packet HEAD.
```

---

## Author note on the single correction cycle (GOV-1 / GOV-2 §2)

F1 is a new material boundary omission: the hourly-first panel's INTRADAY axis has
no truthful hourly carrier. Per GOV-2 §1 this returns the packet to DESIGN
INCOMPLETE — an owner design-direction decision, not an author-resolvable
correction. F4 (placement) and F7 (D-1/D-2 value semantics) likewise carry owner
decisions. The mechanical findings (F2, F3, F5, F6, and the non-decision parts of
F4/F7) are ACTIONED in the consolidated correction. The GOV-2 EXACT-CORRECTED-HEAD
CONFIRMATION (Event-2) is deliberately RESERVED for the corrected head after
Dustin rules on INTRADAY, because the INTRADAY ruling can change the axis set,
runtime boundary, FILES cone, and classification — confirming the current head
would certify nothing durable. Packet status after correction: REVIEW-CLEAN = NO,
DESIGN INCOMPLETE, held for Dustin's design-direction ruling.
