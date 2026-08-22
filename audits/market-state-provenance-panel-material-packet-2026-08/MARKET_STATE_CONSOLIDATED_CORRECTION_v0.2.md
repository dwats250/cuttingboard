# Market State Panel — CONSOLIDATED CORRECTION (v0.2) + DESIGN-INCOMPLETE ESCALATION

**Status: REVIEW-CLEAN = NO — DESIGN INCOMPLETE — HELD FOR DUSTIN'S
DESIGN-DIRECTION RULING.**
This is the single consolidated author correction (GOV-2 §2 step 4) of the Codex
Event-1 findings F1-F7 (`MARKET_STATE_EVENT1_CODEX_REVIEW_2026-08-22.md`, reviewed
SHA `66d9731`). All seven findings were independently re-verified against source
before dispositioning. The mechanical findings (F2, F3, F5, F6) are ACTIONED
below and fold into the packet boundary. The owner-blocking findings (F1;
F4-placement; F7-D-1/D-2) are ESCALATED — they require Dustin's design-direction
decision and cannot be author-resolved. Per GOV-2 §1 a new material boundary
omission (F1) returns the packet to DESIGN INCOMPLETE.

The GOV-2 EXACT-CORRECTED-HEAD CONFIRMATION (Event-2) is RESERVED for the
corrected head produced AFTER Dustin rules on INTRADAY, because that ruling can
change the axis set, the runtime boundary, the FILES cone, and the
classification. Confirming the present head would certify nothing durable.

Baseline `main` @ `731b5ee`; correction verified against source (§ Verification).

---

## 1. F1 (BLOCKING) — INTRADAY has no truthful hourly carrier — ESCALATED

**Confirmed.** `fetch_ohlcv` returns 6-month DAILY OHLCV (`ingestion.py:119-124`);
trend-structure rejects non-intraday frames for VWAP and classifies them
`NOT_COMPUTED` (`trend_structure.py:39-56, 120-136`); the committed snapshot shows
SPY `price_vs_vwap="NOT_COMPUTED"` (`logs/trend_structure_snapshot.json`). The only
intraday-session fetch feeding a VWAP (`fetch_intraday_session_bars("SPY")`,
`runtime:1238`) runs solely inside `_run_pipeline` (daily/full path); it is NOT on
the hourly notify path (`_execute_notify_run`, 526-800). Therefore **carrier A
(trend-structure hourly) yields a permanently-unavailable hourly INTRADAY row**,
and no existing hourly carrier supplies SPY vs-VWAP.

The packet v0.1 claim "carrier A truthfully available" (§4.3) and the unqualified
"delivery-only" conclusion (§4.1/§7) are RETRACTED for the INTRADAY axis. The
"honesty nuance" in v0.1 §4.3 was understated: `NOT_COMPUTED` is the hourly steady
state, not an edge case.

**OWNER DESIGN-DIRECTION DECISION REQUIRED (D-INTRADAY).** Three bounded options:

- **(a) Accept an always-unavailable hourly INTRADAY row.** Honest (owner Ruling
  3/5 permit an honest unavailable state), but the axis is effectively dead on the
  primary board; it would only populate on daily/full runs. Zero runtime change;
  stays delivery-only.
- **(b) Drop INTRADAY from the hourly panel (5 hourly axes).** Present INTRADAY as
  an explicitly daily-only axis (or omit it). Zero runtime change; delivery-only;
  the panel is honestly five axes on the hourly board.
- **(c) Authorize the smallest truthful intraday carrier.** An hourly intraday SPY
  VWAP source (e.g. an intraday-session fetch on the notify path). This is a NEW
  runtime seam / producer -> a GOV-2 §5 STOP-AND-RENEW: it re-opens the runtime
  boundary, the FILES cone, the LOC ceiling, and the classification, and conflicts
  with owner Ruling 5 ("build no new producer") and owner Ruling 10 unless
  explicitly renewed. Not adoptable without a fresh owner ruling and boundary
  renewal.

Author recommendation: **(b)** — it preserves the hourly-first intent honestly
with zero runtime change and no new producer, and INTRADAY vs-VWAP already renders
on the daily/full board via the existing `SpyObservation` path. But this is
Dustin's call.

---

## 2. F2 (P1) — PERMISSION carrier corrected — ACTIONED

**Confirmed.** `_build_system_state` returns no permission field
(`contract.py:251-259`); the hourly contract injects permission only for
operator-lock (`runtime:2278-2284`); the hourly *run* summary always supplies it
(`runtime:2363-2369`); the renderer reads the run first, falling back to the
payload (`dashboard_renderer.py:2172-2175`). Live artifacts confirm: run
permission set, payload permission null.

**Correction to the packet:** the PERMISSION carrier is
`latest_hourly_run.json.permission` (renderer run-first, payload-fallback), NOT the
contract/payload `system_state.permission`. Packet §3, §16 [C1], and the §6 seam
trace are corrected accordingly. Additional semantic note surfaced by F4: the
existing system-state block deliberately does NOT render the raw permission line
— PRD-219 replaced it with a distilled `sys-verdict`. The PERMISSION axis must
therefore re-present the existing permission value WITHOUT reintroducing the raw
line PRD-219 removed inside the system-state region (see F4). Tests to add: normal,
halt, operator-lock, and missing-permission PERMISSION-row cases (folds into M3 +
the new M-permission-unavailable, F6).

---

## 3. F3 (BLOCKING, mechanical) — PRD-220 arrow test enumerated — ACTIONED

**Confirmed.** `test_prd220_tradables_arrow_before_price`
(`tests/test_dashboard_renderer.py:4007-4013`) asserts a `tradable-arrow` span
before the price. The v0.1 cut surface (§4.2 step 5) named only PRD-199 tests.
**Correction:** the arrow cut must also remove/replace this PRD-220 assertion.
`tests/test_dashboard_renderer.py` is already in the cone (§8), so this is an
enumeration completeness fix, NOT a file-count expansion. The v0.1 §4.2/§8/§10
arrow-test references now read "PRD-199 arrow tests AND
`test_prd220_tradables_arrow_before_price`."

---

## 4. F4 (BOUNDARY) — placement is a code boundary — ACTIONED (cone) + ESCALATED (decision)

**Confirmed.** `tests/test_dash_system_state.py` extracts the region
`id="system-state"`..`id="candidate-board"` and asserts the raw permission line is
absent from it (`:82-93, :109-127`, PRD-219). An above-cards MARKET STATE block
that re-renders permission inside that region would fail these tests.

**Correction:** D-3 (placement) is RE-CLASSED from "no code-boundary impact" to a
code-boundary decision. Two coherent resolutions, the choice being Dustin's
(D-PLACEMENT):
- **Place the panel OUTSIDE the `system-state`..`candidate-board` region** (e.g.
  above `system-state` or below `candidate-board`), proving `test_dash_system_state.py`
  stays green with no edit. Preferred: smallest blast radius.
- **Place it inside that region** and add `tests/test_dash_system_state.py` to the
  cone, narrowing its block extraction. Larger blast radius; re-opens a PRD-219
  assertion.
Either way, to avoid reintroducing what PRD-219 removed, the PERMISSION row should
mirror the distilled-verdict semantics, not the raw permission string, when inside
or adjacent to the system-state region. `tests/test_dash_system_state.py` is added
to the FILES cone as CONDITIONAL (edited only under the inside-region option).

---

## 5. F5 (BOUNDARY) — docs cone + tripwire — ACTIONED

**Confirmed.** `CALL_SITE_MAP.md` records the analogous `gex_card` load/build/render
seam (`docs/CALL_SITE_MAP.md:63-69`) and must be updated for new high-value
boundaries (`:3-7`); the new `market_state_panel.py` seam belongs there
(file+function granularity, no line numbers — the map's convention).
`PROJECT_STATE.md:224` (PRD-199) states the tradables arrow "now show[s]" — the cut
makes this stale.

**Correction to the FILES cone (§8):**
- ADD `docs/CALL_SITE_MAP.md` (M) — record the `market_state_panel.py` seam
  (`load`/`build`/`render_fragment`, mirroring the GEX entry).
- The Stage-0 PRD MUST update `docs/PROJECT_STATE.md:224` to retire/supersede the
  PRD-199 arrow claim. Packet §12 tripwire #10 ("any file beyond §8") is amended to
  CARVE OUT this governed PRD-stage bookkeeping update (it is authorized
  retirement bookkeeping, not silent scope expansion).

---

## 6. F6 (P1) — mutation matrix strengthened — ACTIONED

**Confirmed.** v0.1 M3 covered only PERMISSION-present; M12/M13 were lexical.
**Correction to §10:**
- ADD **M3b (PERMISSION unavailable):** delete/null both permitted permission
  inputs (run + payload) -> only the PERMISSION row renders `unavailable`; other
  rows unaffected. Mutation-red.
- STRENGTHEN **M12/M13** to a STRUCTURAL assertion: the panel emits EXACTLY the
  approved axis rows and NO aggregate/summary/footer row, so an unlabeled numeric
  composite or a global "as of" cannot evade a lexical score check. Mutation-red on
  adding any aggregate row or global as-of line.

---

## 7. F7 (P1) — PARTICIPATION partial-absence + POSITIONING qualifier — ACTIONED + ESCALATED

**Confirmed.** The watchlist producer emits all 12 rows even when
`daily_change_pct` is null (`watchlist_sidecar.py:76-92`); the Movement card
preserves per-symbol `n/a` (`movement_card.py:86-93, 126-129`). So "12/12
captured" overstates usable observations. The existing GEX Net display carries a
mandatory configured-assumption / not-measured qualifier (`gex_card.py:175-191`).

**Correction / escalation:**
- PARTICIPATION MUST NOT render a bare "12/12 captured" that implies 12 usable
  values. If a count is shown it must reflect usable (non-`n/a`) observations, or
  the row shows availability + provenance only. Add **M8b (partial absence):** some
  movement rows `n/a` -> PARTICIPATION does not claim full capture. Mutation-red.
- If POSITIONING re-presents signed net GEX (D-1), it MUST carry the existing
  configured-assumption/not-measured qualifier. Add **M6b (qualifier preserved):**
  removing the qualifier reddens. Mutation-red.
- **D-1 (POSITIONING value) and D-2 (PARTICIPATION value) are ESCALATED** to
  Dustin's design-direction ruling. Author recommendation: minimal availability +
  honest provenance per row (no re-presented GEX net, no bare 12/12), which avoids
  both the qualifier obligation and the partial-absence overstatement and avoids
  duplicating the existing cards. Dustin decides.

---

## 8. Net effect on the packet boundary (post-correction)

- **FILES cone (§8) delta:** ADD `docs/CALL_SITE_MAP.md`; ADD
  `tests/test_dash_system_state.py` (CONDITIONAL on the inside-region placement
  option); enumerate `test_prd220_tradables_arrow_before_price` within the already-
  listed `tests/test_dashboard_renderer.py`; the Stage-0 PRD carries the
  `docs/PROJECT_STATE.md:224` retirement (tripwire carve-out).
- **Mutation matrix (§10) delta:** ADD M3b (permission-unavailable), M6b
  (GEX-qualifier), M8b (movement partial-absence); STRENGTHEN M12/M13 to structural
  exact-axis / no-aggregate assertions.
- **Carrier correction:** PERMISSION carrier = `latest_hourly_run.json.permission`
  (run-first), presented without reintroducing the PRD-219-removed raw line.
- **INTRADAY (F1):** axis carrier is UNRESOLVED pending D-INTRADAY; §4.1/§4.3/§7
  "delivery-only / carrier A available" retracted for INTRADAY.
- **LOC/ceilings:** unchanged under options (a)/(b) (still delivery-only, no runtime
  change); option (c) would require a full GOV-2 §5 renewal.

## 9. Open OWNER design-direction decisions (block review-clean)

- **D-INTRADAY** (from F1): accept-always-unavailable (a) / drop-to-5-axes (b) /
  authorize-intraday-carrier-with-renewal (c). Author rec: (b).
- **D-PLACEMENT** (from F4): outside the system-state..candidate-board region
  (preferred) vs inside (adds `test_dash_system_state.py`). Author rec: outside.
- **D-1 / D-2** (from F7): POSITIONING and PARTICIPATION row value semantics.
  Author rec: minimal availability + provenance.

## 10. Verification (GOV-2 §3, correction facts)

All at `main` @ `731b5ee` / packet head `66d9731`:
- F1: `ingestion.py:119-124` (daily OHLCV); `trend_structure.py:39-56,120-136`;
  `logs/trend_structure_snapshot.json` SPY `NOT_COMPUTED`;
  `fetch_intraday_session_bars` only at `runtime:1238` in `_run_pipeline`. CONFIRMED.
- F2: `contract.py:251-259`; `runtime:2278-2284,2363-2369`;
  `dashboard_renderer.py:2172-2175`; `latest_hourly_run.json` perm set,
  `latest_hourly_payload.json` perm null. CONFIRMED.
- F3: `tests/test_dashboard_renderer.py:4007-4013`. CONFIRMED.
- F4: `tests/test_dash_system_state.py:82-93,109-127`. CONFIRMED.
- F5: `docs/CALL_SITE_MAP.md:3-7,63-69`; `docs/PROJECT_STATE.md:224`. CONFIRMED.
- F6/F7: `watchlist_sidecar.py:76-92`; `movement_card.py:86-93,126-129`;
  `gex_card.py:175-191`. CONFIRMED.

Author self-verification is NOT independent review. The Event-2
EXACT-CORRECTED-HEAD CONFIRMATION is reserved for the post-ruling corrected head.

---

END OF CONSOLIDATED CORRECTION v0.2 — REVIEW-CLEAN = NO — DESIGN INCOMPLETE — NO
IMPLEMENTATION AUTHORITY. Held for Dustin's design-direction ruling on D-INTRADAY,
D-PLACEMENT, and D-1/D-2. Gate A neither requested nor granted.
