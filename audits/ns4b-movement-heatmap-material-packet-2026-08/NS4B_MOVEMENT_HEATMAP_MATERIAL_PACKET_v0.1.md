# NS-4B — Market Movement Heatmap — MATERIAL PACKET (v0.1, PROVISIONAL)

**Status: PROVISIONAL — NOT REVIEW-CLEAN — NO IMPLEMENTATION AUTHORITY.**
This is the GOV-2 §2 step-2 provisional material packet. It carries no
implementation authority (GOV-2 §4). All FILES and LOC figures are
`ESTIMATED SURFACE — NOT YET APPROVED` (GOV-2 §5). The next governed step is
the independent Codex packet review (GOV-2 §2 step 3), commissioned by Dustin.

**Authored against `main` @ `80ac6eb2618eb419afff6764292dec5c838204ce`**
(HEAD == origin/main, tree clean, confirmed at session start). Every line
citation below is current at that SHA (author self-verification, §16).

---

## 0. Where this packet sits in the GOV-2 order

```
materiality check at intake ............................. DONE (MATERIAL; §2, §13)
producer / carrier reconciliation ...................... DONE (Stage-0 + §16 re-verify)
provisional material packet authored ................... DONE (this v0.1 doc)      <-- HERE
independent packet review (GOV-2 §2 step 3) ............ PENDING (Dustin commissions)
one consolidated correction (step 4) ................... PENDING
exact-corrected-head confirmation (step 5) ............. PENDING
Dustin design-direction ruling (step 6) ................ PENDING
Stage-0 PRD drafting (step 7) .......................... PENDING
independent PRD review (step 7) ........................ PENDING
Dustin Gate A (step 8) ................................. PENDING
```

MICRO-ineligible (MATERIAL, §13); rides **HIGH-RISK** (forced —
`dashboard_renderer.py` is a CONSUMER HIGH-RISK FILES payload).

---

## 0.1 Accepted product direction into this packet (pre-review)

Dustin ruled the two Stage-0 open product choices and directed authoring of this
packet. Recorded here as accepted inputs that shape the design; they are **not**
the GOV-2 §2 step-6 design-direction ruling, which still comes only after the
packet is review-clean.

- **(a) Subset-first coverage: ACCEPTED 10/12.** Ship the 10 registry symbols
  that already have a live movement number; UCO and GOOG are shown as
  unavailable-by-truth (they are not in `config.ALL_SYMBOLS`, §4). Adding them
  later is a 2-symbol `config.ALL_SYMBOLS` edit, out of this slice.
- **(b) Slice boundary: ACCEPTED hourly-only (slice 1).** Zero runtime changes;
  the block renders from the artifact the hourly path already writes. The daily
  write call + its publish side effect is the explicitly deferred slice 2 (§14).

---

## 1. Product question and user-visible outcome

A compact, read-only **MARKET MOVEMENT** block on the dashboard answering, at a
glance, the VISION question *"is today's move broad or isolated?"* — grouped by
the registry's primary groups, each symbol showing its move off the prior
session close. No prediction, no scoring, no ranking; it renders only numbers
the pipeline already computes.

- **One block, five group lines** (INDEX, METALS, ENERGY, TECH, HIGH_BETA),
  each a row of `SYM +X.X%` chips in a fixed order (§5), a single
  `as of HH:MM ET` footer, absent rows omitted. Mobile-friendly: one column,
  ~7 rendered lines.
- **Movement basis:** last price vs **previous session close**, decimal at
  source (`NormalizedQuote.pct_change_decimal`), x100 for display — identical to
  the trend-structure and macro-driver `change_pct` convention already on the
  board (PRD-199). No arithmetic invented.
- **Every cell is a truthful value or an explicit absence.** A symbol with no
  live quote (UCO, GOOG today) is omitted or shown `n/a` (design question D-2);
  never a fabricated `0.0` (PRD-262 guarantees a bad `previous_close` fails loud
  upstream, §11).

---

## 2. Intake classification (GOV-2 §1)

**MATERIAL: YES.**

Primary trigger — *"selects an implementation seam or carrier shared across
pipeline layers"*: this slice selects `logs/watchlist_snapshot.json` as a NEW
artifact -> renderer -> board carrier. That artifact has **zero machine readers
today** (§6); the slice makes `dashboard_renderer.py` its first-ever machine
reader, joining sidecar output to the dashboard/publish path across the sidecar,
delivery, and dashboard layers.

Secondary trigger — *"crosses two or more of runtime, contract, audit,
reporting, notification, delivery, dashboard, or persistence"*: the slice spans
**delivery** (`watchlist_sidecar.py` row schema) and **dashboard**
(`dashboard_renderer.py` block). It fires literally.

Not MATERIAL merely because the renderer/registry "exist." The
trend-structure-only variant (existing seam, no new carrier, no schema change)
would NOT be MATERIAL — but it covers 0 TECH and 0 HIGH_BETA symbols
(`TREND_STRUCTURE_SYMBOLS` = SPY QQQ GDX GLD SLV XLE) and cannot answer the
broad-or-isolated question, so it is not recommended.

MATERIAL classification does not convert the lane to HIGH-RISK; the lane is
HIGH-RISK independently because `dashboard_renderer.py` is CONSUMER HIGH-RISK
FILES payload (§13). MATERIAL adds no Codex-commissioned events beyond the two
in GOV-2 §7 (upstream packet review; exact-corrected-head confirmation).

---

## 3. Verified current state (producers and carriers, @ `80ac6eb`)

### 3.1 The movement number and its freshness clock

- `NormalizedQuote.pct_change_decimal` (`normalization.py:29`) — decimal
  (`5.2% == 0.052`, comment `:29`); the in-process source of truth. Also carries
  `fetched_at_utc` (tz-aware, `:31`) and `age_seconds` (`:34`).
- Computed in `ingestion.py` from yfinance `fast_info`:
  `prev_close = info.previous_close` (`:361`); an invalid `previous_close`
  raises `ValueError` (`:369`) — **fail-loud, never a fabricated 0.0** (PRD-262).

### 3.2 The carrier already in hand (the sleeper)

- `build_watchlist_snapshot(normalized_quotes, generated_at)`
  (`watchlist_sidecar.py:61`) receives the **full** `NormalizedQuote` mapping,
  iterates `WATCHLIST_SYMBOLS`, and projects each row as
  `{symbol, sector_theme, watch_reason, current_price}` (`:72-77`).
  **`current_price = quote.price` (`:71`) is the ONLY quote field it keeps —
  the movement number is already in its hands and is dropped on the floor.**
- The snapshot top level carries `schema_version: 1`, `source: "watchlist"`,
  and `generated_at` (tz-aware ISO, `:79-83`).
- `WATCHLIST_SYMBOLS` is DERIVED from `UNIVERSE_REGISTRY`
  (`watchlist_sidecar.py:56`, `build_watchlist_symbols` `:43`), filtered on
  `inst.enabled` (`:52`). Live length is **12** (verified §16), one row per
  enabled registry instrument.
- Rows carry the COARSE legacy `sector_theme` (Index / Commodities / High beta)
  via `_PRIMARY_GROUP_TO_THEME` (`watchlist_sidecar.py:34-40`), **not** the fine
  `primary_group`. Grouping the movement block by the 5 registry groups
  therefore requires a `primary_group` passthrough (§5). The sidecar already
  imports `UNIVERSE_REGISTRY` / `UniverseInstrument` (`:26`), so this is a pure
  projection with no new import.

### 3.3 Write cadence

- **Hourly:** `_write_watchlist_snapshot(...)` is called at
  `runtime/__init__.py:784`, inside the hourly notify path, gated on
  `not validation_summary.system_halted`, after `_write_trend_structure_snapshot`
  (`:778`). The writer (`:2507`) calls `build_watchlist_snapshot` (`:2513`) and
  writes atomically to `WATCHLIST_PATH` (`runtime/_constants.py:57` =
  `LOGS_DIR / "watchlist_snapshot.json"`).
- **Daily:** the `MODE_LIVE` daily block (`runtime/__init__.py` ~`:1490`) writes
  `trend_structure` (`:1495` region) and builds `spy_observation`, but
  **never calls `_write_watchlist_snapshot`.** On a fresh daily runner the
  artifact is therefore absent (§7) -> the block suppresses honestly.

### 3.4 Publish safety

- `.gitignore:49` ignores `logs/`; `logs/watchlist_snapshot.json` is untracked
  (verified: `git ls-files` returns nothing for it). It is written run-locally,
  never staged, never on `main`, never published today. The renderer reading it
  from disk (slice 1) changes nothing about that: no new persisted surface, no
  `git add -f`, no publish path (§7, §12).

---

## 4. Coverage truth table (10/12)

Authoritative source: `UNIVERSE_REGISTRY` (`universe_registry.py:52-65`, 12
enabled instruments) intersected with the fetched universe
`config.ALL_SYMBOLS` (`config.py:264` = MACRO_DRIVERS + INDICES + COMMODITIES +
HIGH_BETA, `:258-262`). A symbol has a live movement number iff it is fetched
(has a `NormalizedQuote`).

| Symbol | primary_group | Fetched (in ALL_SYMBOLS)? | Movement today |
|---|---|---|---|
| SPY  | INDEX     | YES (INDICES)     | available |
| QQQ  | INDEX     | YES (INDICES)     | available |
| GDX  | METALS    | YES (COMMODITIES) | available |
| GLD  | METALS    | YES (COMMODITIES) | available |
| SLV  | METALS    | YES (COMMODITIES) | available |
| XLE  | ENERGY    | YES (COMMODITIES) | available |
| UCO  | ENERGY    | **NO** (config has `USO`, not `UCO`) | **unavailable** |
| NVDA | TECH      | YES (HIGH_BETA)   | available |
| META | TECH      | YES (HIGH_BETA)   | available |
| AMZN | TECH      | YES (HIGH_BETA)   | available |
| GOOG | TECH      | **NO** (absent from config HIGH_BETA) | **unavailable** |
| TSLA | HIGH_BETA | YES (HIGH_BETA)   | available |

**Coverage: 10 / 12.** By group: INDEX 2/2, METALS 3/3, ENERGY 1/2, TECH 3/4,
HIGH_BETA 1/1 — the broad-or-isolated question is answerable. UCO and GOOG are
unavailable-by-truth (their watchlist rows already carry `current_price: null`).

> Precision note (refines a loose Stage-0 phrasing; conclusion unchanged):
> `config.ALL_SYMBOLS` fetches far more than these 10 (VIX, TNX, IWM, PAAS, USO,
> AAPL, COIN, MSTR, and the macro drivers). The exact claim is: **10 of the 12
> registry symbols are in the fetched universe; UCO and GOOG are the two
> registry symbols absent from it.**

---

## 5. Design (the slice)

### 5.1 Sidecar contract change (`watchlist_sidecar.py`)

Add two fields to each snapshot row, additive only:

- `daily_change_pct`: `round(quote.pct_change_decimal * 100, 1)` when a quote is
  present, else `null`. Same basis and x100 convention as trend-structure
  `daily_change_pct` (PRD-199).
- `primary_group`: `inst.primary_group` passthrough from the registry (INDEX /
  METALS / ENERGY / TECH / HIGH_BETA). Requires threading `primary_group` into
  `WATCHLIST_SYMBOLS` (currently a `(symbol, theme, reason)` 3-tuple) or reading
  it alongside. Pure projection; the registry is already imported.

Row shape after the change (existing keys byte-unchanged, new keys appended):
`{symbol, sector_theme, watch_reason, current_price, daily_change_pct,
primary_group}`. `schema_version` bumps 1 -> 2 (additive), or stays 1 with
additive keys — design question D-7 (§15); recommend an additive bump for
honest versioning since the artifact gains a machine reader.

### 5.2 Renderer block (`dashboard_renderer.py`, optional `movement_card.py`)

- **Optional read** of `logs/watchlist_snapshot.json` from disk (same
  artifact-driven pattern as `trend_structure_snapshot.json` and `gex_card.py`).
  The renderer never imports the registry; it consumes only the artifact.
- **Grouped render:** one `MARKET MOVEMENT` block; groups in the fixed order
  **INDEX, METALS, ENERGY, TECH, HIGH_BETA** (a new explicit ordered constant —
  `PRIMARY_GROUPS` is a `frozenset`, unordered, and registry insertion order
  interleaves TSLA among TECH, so neither can be relied on; design question
  D-1). Within a group, symbols in registry insertion order.
- **Chips:** `SYM +X.X%` (sign only, one decimal; the existing +/- tape
  convention — no color-coded bullish/bearish semantics).
- **Footer:** one `as of HH:MM ET` derived from the snapshot `generated_at`
  (tz-aware; mirrors the GEX card's single-clock pattern).
- **Suppression:** artifact absent -> whole block omitted, byte-identical
  baseline (GEX-golden style). A row whose `daily_change_pct` is `null`
  (UCO, GOOG) -> row omitted or a compact `n/a` chip (design question D-2).
- A small `cuttingboard/delivery/movement_card.py` helper mirroring
  `gex_card.py` is recommended (design question D-5) to keep the block testable
  in isolation and the renderer thin.

---

## 6. Seam trace (complete artifact lifecycle)

```
ingestion.fetch (yfinance fast_info)
  -> NormalizedQuote.pct_change_decimal            [normalization.py:29; fail-loud :369]
  -> runtime hourly notify path (non-halt)         [runtime/__init__.py:784]
       -> _write_watchlist_snapshot                [runtime/__init__.py:2507]
            -> build_watchlist_snapshot            [watchlist_sidecar.py:61]
                 (ADD daily_change_pct + primary_group to each row)   <-- slice change
            -> logs/watchlist_snapshot.json        [WATCHLIST_PATH, _constants.py:57; gitignored :49]
  -> dashboard_renderer reads the artifact         <-- slice change (FIRST machine reader ever)
       -> MARKET MOVEMENT block                    <-- slice change (optional movement_card.py)
       -> reports/output/dashboard.html
  -> (publish path) rendered dashboard on the publish branch (hourly runs only)
```

**Reader inventory of `logs/watchlist_snapshot.json` today (falsification of the
zero-reader claim attempted):** the only occurrences in `cuttingboard/`,
`tools/`, `tests/` are the writer (`runtime/__init__.py:2521` logging;
`:2507/:2513`), the path constant (`_constants.py:57`), and unit tests of the
writer (`tests/test_watchlist_sidecar.py:287-305`). The renderer's only
`watchlist` reference is `_os_sections.get("watchlist")`
(`dashboard_renderer.py:2522`) — the **overnight-scan** section, an entirely
different object, NOT this artifact. **Confirmed: zero machine readers of
`watchlist_snapshot.json` today.**

---

## 7. Schema / persistence classification

- The two new row keys are **additive** to a transient, run-local, gitignored
  artifact. No `PAYLOAD_SCHEMA_VERSION` bump, no `assert_valid_payload`
  required-key change, no cat-2/cat-3/cat-4 artifact touched, no decision
  contract, no audit surface.
- **No new persisted surface.** `watchlist_snapshot.json` remains untracked and
  unpublished; the renderer reads it from disk within the same run, exactly as
  it reads `trend_structure_snapshot.json` today.
- **Publish behavior (honest intermittency).** Because only the hourly path
  writes the artifact, the MARKET MOVEMENT block is present on the published
  dashboard after hourly publishes and absent after the daily publish until the
  next hourly render. This is truthful (no stale data is ever shown) but is a
  visible intermittency; making it always-present is slice 2 (daily write) and
  carries the `git add -f logs/` publish side effect (§14). Design question D-4.

---

## 8. FILES cone (ESTIMATED SURFACE — NOT YET APPROVED)

| Op | File | Purpose |
|---|---|---|
| M | `cuttingboard/watchlist_sidecar.py` | add `daily_change_pct` + `primary_group` passthrough to snapshot rows; thread `primary_group` into `WATCHLIST_SYMBOLS`/rows |
| M | `cuttingboard/delivery/dashboard_renderer.py` | MARKET MOVEMENT block: optional artifact read, grouped render, suppression |
| A (optional) | `cuttingboard/delivery/movement_card.py` | small block-builder helper mirroring `gex_card.py` (design question D-5) |
| M | `tests/test_watchlist_sidecar.py` | new-field presence, scale, null-on-missing, group passthrough |
| M | `tests/test_dashboard_renderer.py` | presence, suppression-when-absent, group order, missing-row handling, freshness footer |
| M | `docs/SCHEMA_MAP.md` | `watchlist_snapshot.json` row schema truth (new fields) |
| M | `docs/artifact_flow_map.md` | `watchlist_snapshot.json` entry: add the renderer as a reader; **correct the stale `11-tuple` to `12-tuple`** (§17 O-1) |
| M | `docs/PRD_REGISTRY.md`, `docs/prd_index.json`, `docs/PROJECT_STATE.md` | Stage-0 bookkeeping |
| M | `docs/plans/decision-support-workplan-v0.1.md` | ledger row |
| A | `docs/prd_history/PRD-NNN.md` | the Stage-0 PRD scaffold (post-ruling) |

**Deliberately NOT in FILES:** `cuttingboard/runtime/__init__.py` (no runtime
change in slice 1 — hourly write already exists), `cuttingboard/normalization.py`,
`cuttingboard/ingestion.py`, `cuttingboard/universe_registry.py`,
`cuttingboard/config.py` (adding UCO/GOOG is out of this slice). Touching any of
these is a §12 stop-and-amend event. PRD-158 sweep: this change deletes/renames
no rendered token; a sweep over `watchlist_snapshot`, `daily_change_pct`, and
`primary_group` adds no further asserting test files beyond the two listed.

Slice 2 (deferred, §14) would add `cuttingboard/runtime/__init__.py` (one daily
write call) and accept the publish side effect.

---

## 9. Estimated production LOC ceiling (ESTIMATED SURFACE — NOT YET APPROVED)

Governing metric: net production LOC via `git diff --numstat` across authorized
production files; test LOC uncounted.

- **~90-110 net production LOC; provisional ceiling <=140.** Sidecar
  passthrough ~10; renderer block + suppression + grouping ~70-90 (helper split
  is neutral to the total). Test LOC ~120 (absent-baseline golden, presence,
  suppression, group projection, order, missing-row).
- **Stop-and-amend tripwire:** any production file beyond §8, any runtime write
  change, any schema/persistence/decision-contract touch, any config universe
  edit -> §12.

Non-binding; the first binding ceiling is Gate A on the reviewed PRD.

---

## 10. Discriminating test / mutation matrix (M-suffix = reddening mutation required)

| # | Case | Asserted | Mut? |
|---|---|---|---|
| M1 | Scale correctness | row `daily_change_pct == round(pct_change_decimal * 100, 1)`; fixture where decimal vs percent differ | **YES** — emitting the raw decimal (no x100) reddens |
| M2 | Null on missing quote | a registry symbol with no `NormalizedQuote` -> row `daily_change_pct is None` and `current_price is None`; never `0.0` | **YES** — fabricating `0.0` reddens |
| M3 | Group passthrough | row `primary_group` is the fine registry group (INDEX/.../HIGH_BETA), not the coarse `sector_theme`; fixture where they differ (TECH vs "High beta") | **YES** — projecting `sector_theme` into `primary_group` reddens |
| M4 | Additive-only rows | `symbol`/`sector_theme`/`watch_reason`/`current_price` byte-unchanged for every row; new keys additive | **YES** — altering an existing key reddens |
| M5 | Block suppression when artifact absent | renderer given no `watchlist_snapshot.json` -> NO MARKET MOVEMENT block; rest of dashboard byte-identical to baseline | **YES** — rendering an empty block reddens |
| M6 | Presence + grouping | artifact present -> block with five group lines in the fixed order INDEX, METALS, ENERGY, TECH, HIGH_BETA | **YES** — relying on `frozenset` iteration or registry insertion order (which interleaves TSLA) reddens |
| M7 | Missing-row handling | UCO/GOOG (null `daily_change_pct`) -> row omitted or explicit `n/a` per D-2; never a fabricated value | **YES** — showing `+0.0%` for a null reddens |
| M8 | Freshness footer | footer `as of HH:MM ET` derived from snapshot `generated_at`; null `generated_at` -> coherent (footer omitted, not a crash) | **YES** — reading wall-clock instead of `generated_at` reddens |
| M9 | Daily suppression e2e | render with no watchlist artifact (daily-runner condition) -> no block, byte-identical baseline | **YES** — a daily write sneaking in reddens (slice-2 boundary guard) |
| M10 | Fail-loud upstream preserved | invalid `previous_close` still raises upstream (PRD-262) so no fabricated `0.0` reaches a row (documents the guarantee; no new guard) | |

Reuse existing `NormalizedQuote` fixtures from `tests/test_watchlist_sidecar.py`
and the dashboard substring-presence/absence style from
`tests/test_dashboard_renderer.py` — NO golden-file byte-diff for presence; a
targeted substring baseline for the absent case. A guard whose mutation leaves
all tests green is not a guard and does not merge (PRD-198 invariant 4).

---

## 11. Unavailable / failure semantics

- **Artifact absent** (daily runner, or hourly halt where the write is skipped
  at `:784`) -> whole block omitted; byte-identical baseline.
- **Symbol quote missing** (UCO, GOOG; or any fetch gap) -> `daily_change_pct`
  is `null` -> row omitted or `n/a` chip (D-2). Never `0.0`.
- **Bad `previous_close`** -> `ValueError` upstream (`ingestion.py:369`, PRD-262)
  -> the symbol has no valid quote -> falls into the missing-quote path above.
  Fabrication is impossible by construction (PRD-198 invariant 1: fail-loud,
  never silent-fallback).

---

## 12. Stop-and-amend conditions (hard stops — return to Dustin, re-run GOV-2 §1)

1. Any change to `runtime/__init__.py` (any runtime write-cadence change is
   slice 2, not slice 1).
2. Any config universe edit (adding UCO/GOOG to `config.ALL_SYMBOLS`).
3. Any `PAYLOAD_SCHEMA_VERSION` bump or `assert_valid_payload` required-key add.
4. Any NEW durable/published persistence surface for the artifact, or any
   `git add -f` of `watchlist_snapshot.json`.
5. Renderer-side derivation/recomputation of any movement value (the renderer
   projects the artifact; it never recomputes `pct_change`).
6. Any wall-clock (`datetime.now()`) dependence in the block (freshness is keyed
   on the snapshot `generated_at`).
7. Any change to `normalization.py`, `ingestion.py`, or `universe_registry.py`
   beyond read-only.
8. Exceeding the §8 file surface or the §9 ceiling without a fresh GOV-2 §1
   classification.
9. Any scoring, ranking, permission, bullish/bearish labeling, or relative-
   strength computation entering the block (VISION non-goal; §14).

---

## 13. Materiality / lane classification

**MATERIAL** under GOV-2 §1 (new cross-layer artifact->renderer carrier;
cross-layer delivery+dashboard span; §2). **Lane: HIGH-RISK**, forced
independently by `dashboard_renderer.py` being CONSUMER HIGH-RISK FILES payload
(PRD-121 R11) — not by MATERIAL, which never converts the lane. MICRO-ineligible.
After this packet is review-clean and Dustin issues a design-direction ruling, a
fresh Stage-0 PRD -> independent PRD review -> Gate A sequence is required before
implementation (GOV-2 §4).

**Governance hold:** NS-4B rides the personalized-news / decision-support
expansion track; the landing PR carries the GOV-0 / PRD-186 visible hold (opened
DRAFT, self-named as a MATERIAL design packet), held for Dustin.

---

## 14. What gets CUT (out of scope)

- Scoring, ranking, permission, bullish/bearish labels, prediction (VISION
  non-goal).
- New provider / ingestion. UCO and GOOG stay unavailable; adding them is a
  future 2-symbol `config.ALL_SYMBOLS` edit, Dustin's call, not this slice.
- The trend-structure-only variant (covers 0 TECH / 0 HIGH_BETA; cannot answer
  the product question).
- Registry schema changes; a second board; a new cadence (rides the existing
  hourly render); benchmark / relative-strength; any generalized universe engine.
- **Daily write (slice 2, deferred):** one mirrored ~6-line
  `_write_watchlist_snapshot` call in the daily `MODE_LIVE` block, which would
  make the block always-present but persist the artifact into the
  `cuttingboard.yml` `git add -f logs/` publish set. A separate decision with
  its own §12 tripwire (#1, #4).

---

## 15. Open design questions for the design-direction ruling

- **D-1 Group display order.** `PRIMARY_GROUPS` is a `frozenset`; registry
  insertion order interleaves TSLA (HIGH_BETA) among TECH. An explicit ordered
  constant is required. **Recommend INDEX, METALS, ENERGY, TECH, HIGH_BETA;**
  within-group, registry insertion order.
- **D-2 Missing-symbol presentation.** Omit the row entirely vs a compact `n/a`
  chip for UCO/GOOG. **Recommend omit the chip but show a small footer count**
  (`2 unavailable: UCO, GOOG`) so absence is visible, not silent.
- **D-4 Publish intermittency (§7).** Accept the block being present after
  hourly publishes and absent after the daily publish (honest, no stale data),
  or take slice 2. **Recommend accept for slice 1** (matches the accepted
  hourly-only ruling).
- **D-5 Helper extraction.** `movement_card.py` mirroring `gex_card.py`
  (recommended) vs inline in `dashboard_renderer.py`.
- **D-7 Artifact versioning.** Additive `schema_version` 1 -> 2 (recommended,
  honest now that the artifact gains a machine reader) vs same-version additive
  keys.

(D-3 slice boundary and D-6 subset coverage are already ruled — §0.1.)

---

## 16. Author self-verification record (GOV-2 §3)

All against `main` @ `80ac6eb`, tree clean, re-run by the authoring agent (not a
delegated sweep; CLAUDE.md Author-discipline 4):

- Passthrough drop: read `watchlist_sidecar.py:61-83`; `current_price =
  quote.price` (`:71`) is the sole quote field kept. CONFIRMED.
- Movement source + fail-loud: `normalization.py:26/29/31/34`;
  `ingestion.py:361/369`. CONFIRMED.
- Write cadence: hourly call `runtime/__init__.py:784` (non-halt gate); writer
  `:2507/:2513`; daily `MODE_LIVE` block `~:1490-1516` writes trend_structure +
  spy_observation, no watchlist write. CONFIRMED.
- Zero machine readers: `rg watchlist_snapshot` over `cuttingboard/ tools/
  tests/` -> writer + path constant + writer-tests only; renderer's `watchlist`
  is the overnight-scan section (`dashboard_renderer.py:2522`), not this
  artifact. CONFIRMED (§6).
- Coverage 10/12: `universe_registry.py:52-65` (12 enabled) vs `config.py:258-264`;
  UCO absent (config has USO), GOOG absent. CONFIRMED (§4).
- Row grouping today is coarse `sector_theme` via
  `_PRIMARY_GROUP_TO_THEME` (`watchlist_sidecar.py:34-40`); registry already
  imported (`:26`). CONFIRMED.
- Publish safety: `.gitignore:49` (`logs/`); `git ls-files
  logs/watchlist_snapshot.json` empty (untracked). CONFIRMED.
- Live `len(WATCHLIST_SYMBOLS) == 12` (Python import). CONFIRMED.
- FILES-cone paths all exist (`ls` each); `gex_card.py` precedent present. CONFIRMED.

Author self-verification is NOT independent review (GOV-2 §3). The independent
Codex packet review (§17) has not run.

---

## 17. Packet review records (GOV-2 §2, §7)

### INITIAL PACKET REVIEW — PENDING

| Field | Value |
|---|---|
| Event type | `INITIAL PACKET REVIEW` (GOV-2 §2 auto-commissioned) |
| Reviewer identity / capability role | independent Codex packet review, fresh context, read-only (`codex exec -s read-only`) — to be commissioned by Dustin |
| Reviewed commit SHA / packet revision | (this packet's committed head — to be pinned at commission) |
| Verdict | PENDING |
| Findings and dispositions | PENDING |
| Fresh-context / independence / run-isolation evidence | PENDING |

### EXACT-CORRECTED-HEAD CONFIRMATION — PENDING

| Field | Value |
|---|---|
| Event type | `EXACT-CORRECTED-HEAD CONFIRMATION` (GOV-2 §2 step 5) |
| Scope | confirmation of the initial-review findings at the corrected head, not a fresh-scope review |
| Reviewed commit SHA | PENDING (after the one consolidated correction) |
| Verdict | PENDING |

**Terminal rule (GOV-2 §2, §6):** a NEW material boundary omission at a
confirmation head returns the packet to DESIGN INCOMPLETE rather than opening a
further review loop.

### Out-of-scope observations (existing-code, NOT NS-4B fixes)

- **O-1** `docs/artifact_flow_map.md:122` calls `WATCHLIST_SYMBOLS` a "frozen
  11-tuple"; the live value is a 12-tuple (GOOG added in NS-4A / PRD-308). Stale
  doc-drift; the slice corrects it while editing that entry (§8). Recorded here
  so the packet review does not rediscover it as an NS-4B defect.

---

## 18. Pre-review revision log

- **v0.1 (2026-08-22):** initial provisional packet, authored from the accepted
  NS-4B Stage-0 evidence and a targeted re-verification of every load-bearing
  citation against `main` @ `80ac6eb` (§16). No prior revision.

---

END OF PACKET v0.1 — PROVISIONAL / NOT REVIEW-CLEAN — NO IMPLEMENTATION
AUTHORITY. The next governed step is the independent Codex packet review
(GOV-2 §2 step 3), commissioned by Dustin. Gate A is neither requested nor
granted.
