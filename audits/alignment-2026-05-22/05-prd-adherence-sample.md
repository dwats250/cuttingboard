# 05 — PRD Adherence Spot-Check

Sample of 8 completed PRDs (mix of recent/older, feature/infrastructure,
sidecar/qualification/delivery, plus PRD-151 retrospective as sanity
check). Verdict per PRD: **MATCHES / MINOR-DRIFT / SIGNIFICANT-DRIFT**.

---

## PRD-114 — Watchlist Snapshot Sidecar (2026-05-10)

- Spec: observe-only producer, frozen curated tuple, pass-through of
  `NormalizedQuote.price`, insertion-order is serialization-only.
- Code at [watchlist_sidecar.py](cuttingboard/watchlist_sidecar.py):
  `WATCHLIST_SYMBOLS` is a `tuple[tuple[str, str, str], ...]` (frozen);
  `build_watchlist_snapshot` reads `quote.price` and emits dict with
  schema_version=1, source="watchlist". No business logic, no fetch.
  Docstring re-asserts R14 (insertion order is not rank).
- **Verdict: MATCHES.**

---

## PRD-107 — Trend Structure Snapshot Sidecar (2026-05-10)

- Spec: pure deterministic builder, no network/file/`datetime.now()`;
  per-symbol record of higher-timeframe and intraday structure context.
- Code at [trend_structure.py](cuttingboard/trend_structure.py): pure
  builder over `NormalizedQuote` + OHLCV DataFrames; explicit
  no-network/no-IO docstring; PRD-130 unknown-state tokens
  (`DATA_UNAVAILABLE`, `INSUFFICIENT_HISTORY`, `NOT_COMPUTED`) propagated
  through `_propagate_unavailable` priority order.
- **Verdict: MATCHES.**

---

## PRD-149 — PT-Anchored Hourly Alert Window (2026-05-19)

- Spec: routine Telegram hourly alerts restricted to fixed PT slot set
  (06:00, 06:30, 07:00, 08:00 .. 13:00 PT); 25-min max lag;
  outside-window writes suppressed audit + grouping key
  `outside:<now_pt>`; force-slot bypass preserved.
- Code at [alert_runner.py](cuttingboard/alert_runner.py):
  `routine_pt_slot(now_utc)` called in the non-force path; `None` returns
  trigger `state_key=f"outside:{now_pt.strftime(...)}"` audit
  ([alert_runner.py:64-80](cuttingboard/alert_runner.py#L64-L80));
  `--force-slot` and `CUTTINGBOARD_FORCE_SLOT=1` env-var honored.
- `ALLOWED_PT_SLOTS` defined at
  [hourly_slot.py:26-30](cuttingboard/notifications/hourly_slot.py#L26-L30).
- **Verdict: MATCHES.**

---

## PRD-151 — Gap-Down Permission Gating (retrospective, 2026-05-22)

- Spec: retrospective documentation of as-built behavior at
  `cuttingboard/intraday_state_engine.py` + `cuttingboard/runtime.py:1205`.
- Code: `classify_gap` at
  [intraday_state_engine.py:182-191](cuttingboard/intraday_state_engine.py#L182-L191);
  `downside_short_permission` at
  [intraday_state_engine.py:242-260](cuttingboard/intraday_state_engine.py#L242-L260);
  `_apply_intraday_short_permission` at runtime.py:1205 wired into three
  call sites (489, 518, 805) per grep — matches DECISIONS.md entry.
  Threshold `_GAP_THRESHOLD = 0.0025` and `_ACCEPTANCE_CLOSES_MIN = 2`
  match the PRD's recorded constants.
- **Verdict: MATCHES.** Sanity check intent (does the retrospective PRD
  accurately reflect code?) — yes.

---

## PRD-136 — Spot Metals Row on Macro Tape (2026-05-12)

- Spec: XAU/XAG added to macro_drivers payload via GC=F/SI=F, fenced from
  qualification via `NON_TRADABLE_SYMBOLS`, optional in contract.
- Code:
  - `MACRO_DRIVERS` includes `GC=F, SI=F` at
    [config.py:149](cuttingboard/config.py#L149).
  - `NON_TRADABLE_SYMBOLS = frozenset(MACRO_DRIVERS)` at
    [config.py:150](cuttingboard/config.py#L150) — auto-fences.
  - `contract._MACRO_DRIVER_SYMBOLS` includes `gold, silver` at
    [contract.py:44-52](cuttingboard/contract.py#L44-L52);
    `_OPTIONAL_MACRO_DRIVERS = frozenset({"oil","gold","silver"})` at
    [contract.py:59](cuttingboard/contract.py#L59).
  - `delivery/macro_tape_layout.py` `MACRO_ROW_1` has XAU/XAG/BTC.
- **Verdict: MATCHES.**

---

## PRD-067 — Trade Thesis Gate (older)

- Spec: deterministic thesis from existing pipeline inputs; INCOMPLETE or
  CONFLICTED → BLOCK_TRADE; never modifies BLOCK_TRADE decisions.
- Code at [trade_thesis.py](cuttingboard/trade_thesis.py): valid
  statuses match ({VALID, INCOMPLETE, CONFLICTED, UNKNOWN}); macro
  alignment tables hard-coded; module operates on ALLOW_TRADE decisions
  only (consistent with docstring).
- **Verdict: MATCHES.**

---

## PRD-138 — Macro Tape Layout Unification (2026-05-13)

- Spec: shared pure-data module exposing `TapeRow`/`TapeSlot` consumed by
  dashboard and notifications; local ordering tuples removed from both.
- Code at
  [delivery/macro_tape_layout.py](cuttingboard/delivery/macro_tape_layout.py):
  frozen dataclasses + three row constants + two `MappingProxyType`
  mappings exactly as spec'd. Consumed by `delivery/dashboard_renderer.py`
  and `notifications/__init__.py` (imports verified).
- **Verdict: MATCHES.**

---

## PRD-141 — Hourly Slot Canonicalization (2026-05-18)

- Spec: floor `now_utc` to top of `America/Vancouver` hour, DST-correct;
  cross-run idempotency store at `logs/last_hourly_slot.json`;
  `--force-slot` bypass; premarket exemption for 12:50/13:00/13:50 UTC.
- Code at
  [notifications/hourly_slot.py](cuttingboard/notifications/hourly_slot.py):
  `canonical_slot_utc`, `is_premarket_slot`, `_PREMARKET_MINUTES_UTC` all
  present and shaped as described.
- **Verdict: MATCHES.**

---

## Headline

8/8 sampled PRDs: **MATCHES**. No drift detected in the sample. The
PRD-151 retrospective passes its sanity check: the retrospective doc
accurately reflects current code, validating the retrospective-
documentation precedent established in `docs/DECISIONS.md` on 2026-05-22.

## Limits of this sample

8 PRDs out of 90+ completed. Sample skewed toward recent (2026-05) and
toward feature/sidecar PRDs. Older infrastructure PRDs (PRD-018 state
notifications, PRD-053 market_map, PRD-100 push contract, PRD-115–120
artifact lineage arc) not re-verified here. None surfaced as suspect in
the inventory/cleanup audits and the registry/index reconciliation is
clean (validator exits 0). Expanding the sample is low marginal value
unless a future audit surfaces a specific suspect.
