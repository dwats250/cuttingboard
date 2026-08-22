# NS-4B — Market Movement Heatmap — MATERIAL PACKET (v0.3, PROVISIONAL, REPLACEMENT)

**Status: DESIGN INCOMPLETE — NOT REVIEW-CLEAN — NO IMPLEMENTATION AUTHORITY —
HELD FOR DUSTIN.**
v0.3 is the single consolidated author correction (GOV-2 §2 step 4) of the
Event-1 findings F1-F6 (record: `NS4B_EVENT1_CODEX_REVIEW_2026-08-22.md`,
reviewed SHA `6e5f176`, v0.2). Event-2 (GOV-2 §2 step 5,
`NS4B_EVENT2_CODEX_CONFIRMATION_2026-08-22.md`, reviewed SHA `5d21923`) confirmed
**F1-F6 all RESOLVED** but returned **NOT CLEAN** on one NEW P1 (G1, §17). Per the
GOV-2 §6 terminal rule the packet is DESIGN INCOMPLETE and the single GOV-1
correction cycle is spent; it is held for Dustin's decision on G1 (§17 / OWNER
HANDOFF). No implementation authority (GOV-2 §4); all FILES/LOC are `ESTIMATED
SURFACE — NOT YET APPROVED` (GOV-2 §5).

**Code baseline `main` @ `80ac6eb2618eb419afff6764292dec5c838204ce`.** Every line
citation is current at that base; correction facts re-verified by the author
(§16, CORRECTION CYCLE).

---

## 0. Where this packet sits in the GOV-2 order

```
materiality check at intake ............................. DONE (MATERIAL; §2, §13)
producer / carrier reconciliation ...................... DONE (Stage-0 + §16)
provisional material packet authored ................... DONE (v0.1)
pre-review OWNER ALIGNMENT pass ........................ DONE (v0.2)
independent packet review (GOV-2 §2 step 3) ............ DONE (Event-1: FINDINGS,
                                                          6 findings @ 6e5f176;
                                                          record file in this dir)
one consolidated correction (step 4) ................... DONE (this v0.3 doc)      <-- HERE
exact-corrected-head confirmation (step 5) ............. PENDING (Event-2 on v0.3 head)
Dustin design-direction ruling (step 6) ................ PENDING
Stage-0 PRD drafting (step 7) .......................... PENDING
independent PRD review (step 7) ........................ PENDING
Dustin Gate A (step 8) ................................. PENDING
```

MICRO-ineligible (MATERIAL, §13); rides **HIGH-RISK** (forced —
`dashboard_renderer.py` is a CONSUMER HIGH-RISK FILES payload).

---

## 0.1 Encoded owner product rulings (pre-review inputs, Dustin 2026-08-22)

Accepted inputs shaping the design; NOT the GOV-2 §2 step-6 design-direction
ruling (which follows review-clean). Numbering matches the owner alignment pass.

- **R1 FULL 12-SYMBOL VISIBILITY (closes D-2).** All 12 enabled registry symbols
  shown. 10 live; UCO and GOOG unavailable-by-truth. UCO/GOOG -> `n/a`; any
  normally-fetched symbol missing on a run -> `n/a`; honest zero -> `0.0%`; NEVER
  coerce missing/null to `0.0%`; NEVER silently omit a registry member or replace
  it with only a footer count. `n/a` is a first-class, always-present cell (the
  board must not imply full group coverage when part of a group is unobserved).
- **R2 GROUP ORDER (closes D-1).** Binding display order INDEX, METALS, ENERGY,
  TECH, HIGH_BETA; within each group, registry insertion order, presentation-only,
  implying no rank.
- **R3 HOURLY-ONLY / LAST-WRITER (closes D-4).** Hourly render with a valid
  artifact -> block present; daily render without the artifact -> block absent;
  failed/suppressed render preserves the previously published board. No daily
  write, runtime change, `cuttingboard.yml` change, or persistence machinery.
- **R4 FRESHNESS WORDING.** `generated_at` is the run CAPTURE clock; display
  `captured HH:MM ET`, never `as of`. Not an exchange or per-symbol last-trade
  timestamp; no speculative per-symbol freshness UI. (Divergent-age exposure is
  real — §3.5, Q-Freshness.)
- **R5 ABSENCE / INVALID ARTIFACT.** Whole artifact absent OR
  invalid/unusable -> suppress the entire block, baseline-neutral. Valid artifact
  with an individual unavailable movement -> `n/a`. No empty fake card; no fake
  zero.

Non-rulings left as design/review questions: **R6 helper extraction** (D-5) and
**R7 artifact versioning** (D-7) — the latter now resolved to a concrete
acceptance contract with justification (§5.1, CORRECTION CYCLE F4), carried as a
PRD recommendation, still subject to PRD review.

---

## 1. Product question and user-visible outcome

A compact, read-only **MARKET MOVEMENT** block answering, at a glance, *"is
today's move broad or isolated?"* — grouped by the registry's five primary
groups, every enabled registry symbol shown, each with its move off the prior
session close. No prediction, scoring, or ranking; only numbers the pipeline
already computes.

- **One block, five group lines** (INDEX, METALS, ENERGY, TECH, HIGH_BETA fixed
  order, R2), each a row of chips. All 12 enabled registry symbols appear: live
  as `SYM +X.X%`, unobserved (UCO, GOOG, or any fetch gap) as `SYM n/a` (R1). One
  `captured HH:MM ET` footer (R4). Mobile-friendly: one column, ~7 lines.
- **Movement basis:** last price vs previous session close, decimal at source
  (`NormalizedQuote.pct_change_decimal`), x100 for display — identical to the
  trend-structure and macro-driver `change_pct` convention (PRD-199; Event-1
  T-3 CONFIRMED). No arithmetic invented.
- **Truthful cells only.** Live quote -> signed percent (honest zero `0.0%`);
  null/missing -> `n/a` (R1), never fabricated `0.0` (PRD-262 fail-loud, §11).

---

## 2. Intake classification (GOV-2 §1)

**MATERIAL: YES.** Primary trigger: selects `logs/watchlist_snapshot.json` as a
NEW artifact -> renderer -> board carrier — zero machine readers today (§6;
Event-1 CONFIRMED), the slice makes `dashboard_renderer.py` its first reader,
joining sidecar output to the dashboard/publish path across sidecar + delivery +
dashboard. Secondary trigger: spans delivery (`watchlist_sidecar.py`) and
dashboard (`dashboard_renderer.py`). The F3 admission reconciliation (§3.5) does
NOT expand the carrier: the slice mirrors the existing artifact's
`normalized_quotes` input (trend-structure precedent), adding no valid/invalid
flag and no new producer field beyond the additive display fields — so MATERIAL
classification is unchanged, no re-classification triggered.

MATERIAL does not convert the lane; HIGH-RISK is forced independently by
`dashboard_renderer.py` being CONSUMER HIGH-RISK payload (§13). No Codex events
beyond the GOV-2 §7 two.

---

## 3. Verified current state (producers and carriers)

### 3.1 The movement number and its freshness clock

- `NormalizedQuote.pct_change_decimal` (`normalization.py:29`) — decimal
  (`5.2% == 0.052`); carries `fetched_at_utc` (`:31`), `age_seconds` (`:34`).
- **`fetched_at_utc = datetime.now(timezone.utc)` at fetch time**
  (`ingestion.py:112`, `:295`) — FETCH wall-clock, assigned **before** provider
  retries, NOT the exchange last-trade time. No per-quote last-trade-age
  admission gate exists (Event-1 T-6/F3 CONFIRMED; the only staleness logic is
  OHLCV cache TTL, `ingestion.py:123-156`). Basis for R4 wording + §3.5.
- From yfinance `fast_info`: `prev_close = info.previous_close`
  (`ingestion.py:361`); invalid `previous_close` raises `ValueError` (`:369`) —
  fail-loud, never fabricated 0.0 (PRD-262).

### 3.2 The carrier already in hand

- `build_watchlist_snapshot(normalized_quotes, generated_at)`
  (`watchlist_sidecar.py:61`) receives the full `NormalizedQuote` mapping, iterates
  `WATCHLIST_SYMBOLS`, projects each row `{symbol, sector_theme, watch_reason,
  current_price}` (`:72-77`). `current_price = quote.price` (`:71`) is the ONLY
  quote field kept; a missing quote already yields `current_price: None` (`:71`)
  — the `n/a` hook the slice extends to `daily_change_pct`.
- Top level `schema_version: 1`, `source: "watchlist"`, `generated_at` (tz-aware
  ISO, `:79-83`). Writer passes `generated_at=run_at_utc` (`runtime/__init__.py:784`)
  and writes atomically, **`json.dumps(..., indent=2, sort_keys=True)`**
  (`:2517`) then `.tmp`->`.replace` (`:2518-2519`). The `sort_keys=True`
  alphabetizes the `symbols` object, so on-disk order is NOT registry order
  (Event-1 F2) — the design carries an explicit order field (§5.1).
- `WATCHLIST_SYMBOLS` DERIVED from `UNIVERSE_REGISTRY` (`watchlist_sidecar.py:56`,
  `:43`), filtered `inst.enabled` (`:52`); live length **12** (§16) — full-12
  needs no new symbol source.
- Rows carry COARSE `sector_theme` via `_PRIMARY_GROUP_TO_THEME`
  (`watchlist_sidecar.py:34-40`), not fine `primary_group`; grouping by the 5
  registry groups (R2) requires a `primary_group` passthrough (§5). Registry
  already imported (`:26`).

### 3.3 Write cadence

- **Hourly:** `_write_watchlist_snapshot(...)` at `runtime/__init__.py:784`,
  hourly notify path, gated `not validation_summary.system_halted`, after
  `_write_trend_structure_snapshot` (`:778`). Writer `:2507`.
- **Daily:** the `MODE_LIVE` block (~`:1490`) writes `trend_structure` + builds
  `spy_observation`, but **never** `_write_watchlist_snapshot` (Event-1 T-8
  CONFIRMED). Fresh daily runner -> artifact absent -> block suppresses (R3, R5).

### 3.4 Publish safety

- `.gitignore:49` ignores `logs/`; `logs/watchlist_snapshot.json` untracked.
  CI starts from `main`, does not restore the artifact, hourly does not stage it
  (Event-1 T-8 CONFIRMED). Run-local, never on `main`, never published as a
  file. The renderer reads it from disk within the run; no persisted surface, no
  `git add -f` (R3; §7).

### 3.5 Admission seam (F3 reconciliation)

- `normalized_quotes = normalize_all(raw_quotes)` (`runtime/__init__.py:550`) is
  ALL normalized quotes; `validate_quotes` (`:552`) splits
  `validation_summary.valid_quotes` from invalid non-HALT quotes. Regime,
  derived, and structure use `valid_quotes` (`:570/:588/:599`), but
  `_write_watchlist_snapshot` (`:784`) and `_write_trend_structure_snapshot`
  (`:770`) are fed the FULL `normalized_quotes`.
- **Consequence:** the existing watchlist artifact already carries
  validation-invalid-non-HALT symbols' prices; NS-4B display-only adds their
  movement. This is not a new NS-4B exposure — it is display-parity with the
  existing artifact, and the already-shipped `trend_structure` sidecar uses the
  identical `normalized_quotes` input (direct precedent, `:770`).
- **In-scope design decision (cuts-before-additions):** NS-4B renders movement
  for exactly the symbols the existing artifact carries (`normalized_quotes`),
  mirroring `trend_structure`. It adds NO valid/invalid flag, NO valid_quotes
  restriction, and NO per-symbol age gate — each of those would require a
  writer/runtime change (§12 tripwire #1), i.e. scope expansion, out of slice 1.
- **Genuine unresolved owner question (Q-Freshness/Admission; §15, handoff):**
  whether a future slice should (a) restrict the watchlist/trend-structure
  sidecars to `valid_quotes`, and/or (b) surface or bound per-symbol quote age /
  last-trade staleness. Non-blocking for slice 1 (the in-scope design is
  precedent-consistent and invents no gate), but it is Dustin's product ruling.

---

## 4. Coverage truth table (10 live + 2 n/a; full-12 display)

`UNIVERSE_REGISTRY` (`universe_registry.py:52-65`, 12 enabled) intersected with
`config.ALL_SYMBOLS` (`config.py:264`, groups `:258-262`). Live iff fetched.
(Event-1 T-2 CONFIRMED.)

| Symbol | primary_group | Fetched? | Cell today |
|---|---|---|---|
| SPY  | INDEX     | YES | live |
| QQQ  | INDEX     | YES | live |
| GDX  | METALS    | YES | live |
| GLD  | METALS    | YES | live |
| SLV  | METALS    | YES | live |
| XLE  | ENERGY    | YES | live |
| UCO  | ENERGY    | **NO** (config has `USO`) | **n/a** |
| NVDA | TECH      | YES | live |
| META | TECH      | YES | live |
| AMZN | TECH      | YES | live |
| GOOG | TECH      | **NO** (absent from config) | **n/a** |
| TSLA | HIGH_BETA | YES | live |

All 12 shown (R1); 10 live, 2 `n/a`. Groups: INDEX 2/2, METALS 3/3, ENERGY 1/2
(UCO n/a), TECH 3/4 (GOOG n/a), HIGH_BETA 1/1 — visible `n/a` prevents any false
implication of full group coverage. (`config.ALL_SYMBOLS` fetches many more
symbols; the exact claim is 10 of the 12 registry symbols are fetched, UCO+GOOG
the two absent.)

---

## 5. Design (the slice)

### 5.1 Sidecar contract change (`watchlist_sidecar.py`)

Add three fields per row, additive; bump `schema_version` 1 -> 2 (justified,
below):

- `daily_change_pct`: `round(quote.pct_change_decimal * 100, 1)` when present,
  else `null` (the `n/a` hook, R1; never coerced to 0.0).
- `primary_group`: `inst.primary_group` passthrough (INDEX/METALS/ENERGY/TECH/
  HIGH_BETA). Pure projection; registry already imported.
- `registry_index`: `int`, the instrument's 0-based position in
  `UNIVERSE_REGISTRY` (F2). Because the writer serializes `sort_keys=True`
  (§3.2), on-disk order is alphabetical; `registry_index` lets the renderer
  reconstruct R2's within-group registry insertion order WITHOUT importing the
  registry.

Row shape after: `{symbol, sector_theme, watch_reason, current_price,
daily_change_pct, primary_group, registry_index}` (existing keys byte-unchanged).

**Reader acceptance contract (F4 / D-7 resolved with justification).** The
renderer is the artifact's first machine reader; it REQUIRES `primary_group` +
`registry_index` + `daily_change_pct`, none present in v1. Therefore:
- bump `schema_version` -> **2** (honest: the schema now has reader-required
  fields beyond v1's shape; this is a reader-driven bump, not a mechanical one);
- the renderer accepts an artifact iff `source == "watchlist"` AND
  `schema_version == 2` AND `symbols` is a non-empty dict whose every row carries
  `symbol` (str), `primary_group` (in the 5 known groups), `registry_index`
  (int), and `daily_change_pct` (float or null);
- a v1 artifact, an unknown version, a wrong `source`, or any structurally
  malformed row -> artifact UNUSABLE -> whole block suppressed (R5). Since the
  same deployed hourly run both writes and renders, there is no stale-v1 window
  in practice; suppression is the safe transitional default.

This is a PRD recommendation (still subject to PRD review), not an owner ruling.

### 5.2 Renderer block (`dashboard_renderer.py`, optional `movement_card.py`)

- **Read + validate** `logs/watchlist_snapshot.json` from disk (artifact-driven,
  like `trend_structure_snapshot.json` / `gex_card.py`). Apply the §5.1
  acceptance contract; any failure -> suppress (R5). The renderer never imports
  the registry.
- **Full-12 grouped render (R1, R2, F2).** Groups in the fixed constant order
  INDEX, METALS, ENERGY, TECH, HIGH_BETA (new explicit ordered constant;
  `PRIMARY_GROUPS` is an unordered `frozenset`). The renderer renders ALL rows
  present in the (usable) artifact, sorted by `(GROUP_ORDER.index(primary_group),
  registry_index)`. Full-12 population is guaranteed by the PRODUCER (the writer
  emits one row per enabled registry instrument; asserted by a writer test, §10
  M6) — the renderer renders what is present and does not hardcode 12. A row with
  `daily_change_pct == null` renders `n/a`, never omitted, never `0.0` (R1).
- **Chips:** `SYM +X.X%` live (sign, one decimal; honest zero `0.0%`),
  `SYM n/a` null.
- **Footer:** one `captured HH:MM ET` from `generated_at` (R4). A malformed/naive
  `generated_at` makes the artifact unusable -> block suppressed (R5) — no
  wall-clock fallback, no fabricated time.
- **Helper (R6 / D-5, design choice).** A small `movement_card.py` mirroring
  `gex_card.py` is proposed for a pure, testable validation+grouping surface;
  "clearer/testable" is judged separately from "smaller" (F6) and is open to
  Codex challenge (T-9).

---

## 6. Seam trace (complete producer -> artifact -> renderer -> publish; F1 corrected)

```
ingestion.fetch (yfinance; fetched_at_utc = now pre-retry, ingestion.py:112/295)
  -> normalize_all -> normalized_quotes (ALL)           [runtime/__init__.py:550]
       (validate_quotes splits valid_quotes @ :552/:570/:588; the WATCHLIST
        writer is fed the full normalized_quotes, §3.5, like trend_structure)
  -> NormalizedQuote.pct_change_decimal                 [normalization.py:29; fail-loud ingestion.py:369]
  -> hourly notify path, non-halt                       [runtime/__init__.py:784, generated_at=run_at_utc]
       -> _write_watchlist_snapshot (atomic, sort_keys) [runtime/__init__.py:2507; :2517-2519]
            -> build_watchlist_snapshot                 [watchlist_sidecar.py:61]
                 (ADD daily_change_pct + primary_group + registry_index; schema_version->2)  <-- slice
            -> logs/watchlist_snapshot.json             [WATCHLIST_PATH, _constants.py:57; gitignored :49]
  -> dashboard_renderer validates + reads artifact      <-- slice (FIRST machine reader ever)
       -> MARKET MOVEMENT block (full-12, grouped by GROUP_ORDER + registry_index)  <-- slice
  --- production publish (hourly workflow ONLY; F1) ---
  -> renderer default output is reports/output/dashboard.html (dev)  [dashboard_renderer.py:58]
  -> hourly_alert.yml renders --output ui/dashboard.html            [hourly_alert.yml:159-163]
       -> cp ui/index.html + ui/contract.json; readiness markers    [hourly_alert.yml:152-198]
       -> commit/push ui/ to the `publish` branch (PRD-194)
  -> pages.yml deploys ui/ from publish                             [pages.yml:30-38]
```

**Publish ownership boundary (F1).** NS-4B changes only the renderer's block; the
render->ui->readiness->publish-branch->Pages chain is owned by the existing
hourly workflow and PRD-194 publish model, unchanged. The block reaches
production ONLY via a successful hourly render+publish; a daily render (no
artifact) publishes a board without the block; a failed/suppressed render leaves
the previously published board (R3).

**Reader inventory today (zero-reader, re-confirmed by Event-1):** only the
writer (`runtime/__init__.py:2507/2513/2521`), the path constant
(`_constants.py:57`), and writer tests (`tests/test_watchlist_sidecar.py`). The
renderer's existing `watchlist` (`dashboard_renderer.py:2522`) is the
overnight-scan section, a different object.

---

## 7. Schema / persistence classification

- New row keys additive; `schema_version` -> 2 is the artifact's OWN version
  (§5.1), NOT `PAYLOAD_SCHEMA_VERSION`; no `assert_valid_payload` change, no
  cat-2/3/4 artifact touched, no decision contract, no audit surface.
- **No new persisted surface.** Artifact stays untracked/unpublished-as-a-file;
  read from disk within the run. An artifact-hygiene guard (§8, F6) pins that it
  stays not-restored / not-staged / gitignored.
- **Publish / last-writer (R3).** Only the hourly path writes it; block present
  after hourly publishes, absent after the daily publish until the next hourly; a
  failed/suppressed render preserves the prior published board. Always-present is
  slice 2 (daily write) with the `git add -f logs/` publish side effect (§14).

---

## 8. FILES cone (ESTIMATED SURFACE — NOT YET APPROVED; F6 re-scoped)

| Op | File | Purpose |
|---|---|---|
| M | `cuttingboard/watchlist_sidecar.py` | add `daily_change_pct` + `primary_group` + `registry_index`; bump `schema_version`->2 |
| M | `cuttingboard/delivery/dashboard_renderer.py` | MARKET MOVEMENT block: acceptance-validate + read, full-12 grouped render (GROUP_ORDER + registry_index), R5 suppression |
| A (design choice, R6) | `cuttingboard/delivery/movement_card.py` | small pure validator/block-builder mirroring `gex_card.py` |
| M | `tests/test_watchlist_sidecar.py` | new fields, scale, null-preserved, group passthrough, registry_index, schema_version->2, full-population |
| M | `tests/test_dashboard_renderer.py` | full-12 presence, n/a vs honest-zero, group order via registry_index against the sort_keys artifact, acceptance/version/source, R5 suppression (absent + each invalid class), captured-clock |
| M | `tests/test_ci_artifact_hygiene.py` | artifact stays not-restored / not-staged / gitignored (F6; GEX pattern precedent) |
| M | `docs/SCHEMA_MAP.md` | `watchlist_snapshot.json` row schema truth (new fields, schema_version 2) |
| M | `docs/artifact_flow_map.md` | add renderer as reader; correct stale `11-tuple`->`12-tuple` (O-1) |
| M | `docs/PRD_REGISTRY.md`, `docs/prd_index.json`, `docs/PROJECT_STATE.md` | Stage-0 bookkeeping |
| M | `docs/plans/decision-support-workplan-v0.1.md` | ledger row |
| A | `docs/prd_history/PRD-NNN.md` | Stage-0 PRD scaffold (post-ruling) |

**Deliberately NOT in FILES:** `runtime/__init__.py` (no runtime change in slice
1), `normalization.py`, `ingestion.py`, `universe_registry.py`, `config.py`,
`validation.py`, the publish workflows (`hourly_alert.yml`, `pages.yml`,
`cuttingboard.yml`). Touching any is a §12 stop-and-amend event. PRD-158 sweep:
deletes/renames no rendered token; a sweep over `watchlist_snapshot`,
`daily_change_pct`, `primary_group`, `registry_index` adds no asserting test file
beyond the three listed.

Slice 2 (deferred, §14) would add `runtime/__init__.py` (one daily write call).

---

## 9. Estimated production LOC ceiling (ESTIMATED SURFACE — NOT YET APPROVED; F6)

Governing metric: net production LOC via `git diff --numstat` across authorized
production files; test LOC uncounted.

- **~120-160 net production LOC; provisional ceiling <=190.** Sidecar (3 fields +
  version bump) ~15; renderer acceptance-validation + grouping/ordering + full-12/
  n-a/honest-zero ~100-135 (helper split neutral). Higher than v0.2 because F2
  (order field + ordering), F4 (acceptance contract), and F5 (exact suppression)
  add real surface. Test LOC ~160.
- **Stop-and-amend tripwire:** any production file beyond §8, any runtime write
  change, any schema/persistence/decision-contract touch, any config/validation
  edit -> §12.

Non-binding; first binding ceiling is Gate A.

---

## 10. Discriminating test / mutation matrix (M-suffix = reddening mutation; F5 tightened)

Absent/invalid cases assert WHOLE rendered-output equality against a baseline
(not substring); each mutation has exactly one falsifiable outcome.

| # | Case | Asserted (exact) | Mut? |
|---|---|---|---|
| M1 | Scale | row `daily_change_pct == round(pct_change_decimal*100, 1)` | **YES** — raw decimal reddens |
| M2 | Null preserved | missing quote -> `daily_change_pct is None`, never `0.0` | **YES** — coercion reddens |
| M3 | Honest zero vs n/a | live `0.0` -> cell `0.0%`; null -> cell `n/a`; the two never collapse | **YES** — collapsing reddens |
| M4 | Group passthrough | row `primary_group` is the fine registry group, not `sector_theme` | **YES** — projecting `sector_theme` reddens |
| M5 | registry_index passthrough | row `registry_index` == the instrument's `UNIVERSE_REGISTRY` position | **YES** — wrong/absent index reddens |
| M6 | Full-12 population (producer) | writer emits exactly the 12 enabled registry rows (incl. UCO/GOOG null) | **YES** — dropping a null-movement symbol reddens |
| M7 | Order against sort_keys artifact | given the alphabetized on-disk artifact, rendered order is `(GROUP_ORDER, registry_index)`; TSLA under HIGH_BETA, not interleaved into TECH | **YES** — using on-disk (alphabetical) order, or frozenset iteration, reddens |
| M8 | Suppress: absent | no artifact -> whole rendered output byte-equal to the no-block baseline | **YES** — any block output reddens |
| M9 | Suppress: invalid class | for EACH of {malformed JSON, missing `symbols`, wrong types, `schema_version != 2`, `source != "watchlist"`} -> whole output byte-equal to baseline | **YES** — rendering from any invalid class reddens |
| M10 | Captured clock | footer `captured HH:MM ET` from `generated_at`; literal "captured", not "as of" | **YES** — wall-clock, or "as of", reddens |
| M11 | Malformed/naive/future generated_at | -> artifact unusable -> block suppressed (single outcome, per R5) | **YES** — rendering, crashing, or defaulting to `now()` reddens |
| M12 | Unknown primary_group | a row with a group outside the 5 known -> artifact unusable -> block suppressed (fail-loud; consistent with full-12) | **YES** — silently bucketing/omitting reddens |
| M13 | Cadence / call-site | `_write_watchlist_snapshot` is invoked from exactly the hourly site and NOT from the daily `MODE_LIVE` block (call-site/AST assertion) | **YES** — adding a daily writer call reddens |
| M14 | Fail-loud upstream | invalid `previous_close` still raises upstream (PRD-262); no fabricated `0.0` reaches a row (documents the guarantee) | |

Reuse `NormalizedQuote` fixtures (`tests/test_watchlist_sidecar.py`) and the
dashboard whole-output baseline style. A guard whose mutation leaves tests green
is not a guard and does not merge (PRD-198 inv. 4).

---

## 11. Unavailable / failure semantics

- **Artifact absent OR invalid/unusable** (daily runner; hourly halt; malformed
  JSON; missing `symbols`; `schema_version != 2`; wrong `source`; malformed row;
  malformed `generated_at`) -> whole block suppressed, baseline-neutral (R5).
- **Individual symbol null** (UCO, GOOG, any fetch gap) -> `n/a`, row retained
  (R1). Never `0.0`.
- **Honest zero** (live, `pct_change_decimal == 0.0`) -> `0.0%`, distinct from
  `n/a`.
- **Bad `previous_close`** -> `ValueError` upstream (`ingestion.py:369`) -> null
  path. Fabrication impossible by construction (PRD-198 inv. 1).

---

## 12. Stop-and-amend conditions (hard stops — return to Dustin, re-run GOV-2 §1)

1. Any change to `runtime/__init__.py` (write-cadence change is slice 2).
2. Any config universe edit (adding UCO/GOOG).
3. Any `PAYLOAD_SCHEMA_VERSION` bump or `assert_valid_payload` required-key add.
4. Any NEW durable/published persistence surface, or any `git add -f` of the
   artifact.
5. Renderer-side derivation/recomputation of any movement value.
6. Any `datetime.now()` dependence in the block (freshness keyed on `generated_at`).
7. Any conversion of null/missing movement to `0.0` (violates R1).
8. Any change to `normalization.py`, `ingestion.py`, `universe_registry.py`, or
   `validation.py` beyond read-only — including any valid_quotes restriction or
   quote-age gate for the sidecars (that is the deferred §3.5/§15 owner question).
9. Any change to the publish workflows (`hourly_alert.yml`, `pages.yml`,
   `cuttingboard.yml`).
10. Exceeding the §8 file surface or §9 ceiling without a fresh GOV-2 §1 pass.
11. Any scoring/ranking/permission/bullish-bearish/relative-strength logic in the
    block (VISION non-goal; §14).

---

## 13. Materiality / lane classification

**MATERIAL** (new cross-layer artifact->renderer carrier; delivery+dashboard
span; §2). The F3 reconciliation does not expand the carrier (§2). **Lane:
HIGH-RISK**, forced independently by `dashboard_renderer.py` (CONSUMER HIGH-RISK
payload; PRD-121 R11). MICRO-ineligible. After review-clean + the
design-direction ruling: Stage-0 PRD -> independent PRD review -> Gate A before
implementation (GOV-2 §4). Governance hold: personalized-news / decision-support
track; landing PR is DRAFT + self-named (GOV-0 / PRD-186), held for Dustin.

---

## 14. What gets CUT (out of scope)

- Scoring, ranking, permission, bullish/bearish labels, prediction (VISION
  non-goal).
- New provider / ingestion; UCO/GOOG stay `n/a` (future 2-symbol config edit).
- The trend-structure-only variant (0 TECH / 0 HIGH_BETA).
- Registry schema changes; a second board; a new cadence; benchmark /
  relative-strength; any generalized universe engine.
- **Any admission change to the sidecars** — a `valid_quotes` restriction or a
  per-symbol age/staleness gate (§3.5) — is a runtime change and the deferred
  owner question, not slice 1.
- **Daily write (slice 2, deferred, R3):** one ~6-line daily
  `_write_watchlist_snapshot` call; makes the block always-present but persists
  the artifact into the `cuttingboard.yml` `git add -f logs/` publish set. §12
  #1/#4.

---

## 15. Open design/review questions

- **D-5 Helper extraction (R6).** `movement_card.py` vs inline — smallest,
  clearer, testable surface wins; Codex may challenge (T-9). Design choice.
- **D-7 Artifact versioning (R7) — RESOLVED as a recommendation (§5.1, F4):**
  bump to `schema_version` 2, reader accepts `source=="watchlist"` AND
  `schema_version==2`, else suppress. Carried as a PRD recommendation, still
  subject to PRD review — not an owner ruling.
- **Q-Freshness/Admission (F3) — GENUINE UNRESOLVED OWNER QUESTION.** Should a
  future slice (a) restrict the watchlist/trend-structure sidecars to
  `valid_quotes`, and/or (b) surface or bound per-symbol quote age / last-trade
  staleness? Evidence: sidecars are fed `normalized_quotes`, not `valid_quotes`
  (§3.5); `fetched_at_utc` is fetch-clock, pre-retry, with no last-trade-age gate
  (§3.1). NS-4B slice 1 mirrors the existing artifact + `trend_structure`
  precedent and invents no gate; the restriction/bound is a runtime scope
  expansion for Dustin to rule. Non-blocking for slice 1.

---

## 16. Author self-verification record (GOV-2 §3)

All against `main`-base code at `6e5f176` (base `80ac6eb`), re-run by the
authoring agent (not delegated; CLAUDE.md Author-discipline 4). v0.3 correction
facts marked [F#]:

- Passthrough drop: `watchlist_sidecar.py:61-83`; `current_price=quote.price`
  (`:71`); missing -> `None`. CONFIRMED.
- Movement source + fail-loud: `normalization.py:26/29/31/34`;
  `ingestion.py:361/369`. CONFIRMED.
- [F3] `fetched_at_utc = datetime.now(timezone.utc)` pre-retry (`ingestion.py:112/295`);
  no last-trade-age gate. CONFIRMED.
- [F2] writer serializes `sort_keys=True` (`runtime/__init__.py:2517`), atomic
  `.tmp`->`.replace` (`:2518-2519`), `generated_at=run_at_utc` (`:784`). CONFIRMED.
- [F3] sidecar fed `normalized_quotes` (`:784`), regime/derived/structure use
  `valid_quotes` (`:570/:588/:599`); `trend_structure` also fed `normalized_quotes`
  (`:770`). CONFIRMED.
- [F1] renderer default `_OUTPUT_PATH = reports/output/dashboard.html`
  (`dashboard_renderer.py:58`); hourly renders `--output ui/dashboard.html`
  (`hourly_alert.yml:159-163`) and publishes `ui/` to the `publish` branch;
  `pages.yml` deploys `ui/`. CONFIRMED.
- [F6] `tests/test_ci_artifact_hygiene.py` carries the not-restored/not-staged/
  gitignored GEX pattern to mirror. CONFIRMED.
- Coverage 10 live + 2 n/a: `universe_registry.py:52-65` vs `config.py:258-264`;
  UCO/GOOG absent. CONFIRMED.
- Zero machine readers; row grouping coarse `sector_theme`
  (`watchlist_sidecar.py:34-40`); registry imported (`:26`); `.gitignore:49`;
  `len(WATCHLIST_SYMBOLS)==12`; FILES paths exist; `gex_card.py` precedent.
  CONFIRMED.

Author self-verification is NOT independent review (GOV-2 §3). Event-1 is
COMPLETE (§17); Event-2 confirmation of F1-F6 at the v0.3 head is PENDING.

---

## 17. Packet review records (GOV-2 §2, §7)

### INITIAL PACKET REVIEW — COMPLETE (Event-1, 2026-08-22)

Full durable record: `NS4B_EVENT1_CODEX_REVIEW_2026-08-22.md` (this directory).
Reviewer: independent Codex (`codex-cli 0.147.0`, `gpt-5.6-sol`), fresh context,
read-only (`codex exec -s read-only`), high effort. Reviewed SHA
`6e5f1767999fcf12169ea939238f4035c044664f` (v0.2). Verdict: FINDINGS — F1/F2/F3
BOUNDARY, F4/F5 P1, F6 P2; T-2/T-3/T-5/T-8/zero-reader/O-1 CONFIRMED. All six
dispositioned in the single consolidated correction (this v0.3; CORRECTION CYCLE
below).

### EXACT-CORRECTED-HEAD CONFIRMATION — COMPLETE, NOT CLEAN (Event-2, 2026-08-22)

Full durable record: `NS4B_EVENT2_CODEX_CONFIRMATION_2026-08-22.md` (this
directory). Reviewer: independent Codex (`codex-cli 0.147.0`, `gpt-5.6-sol`),
fresh context, read-only, high effort. Reviewed SHA
`5d21923b36c475ebe272252897721a9228019e52` (v0.3).

| Field | Value |
|---|---|
| Scope | confirm F1-F6 at the v0.3 head; detect NEW blocking inconsistency |
| F1-F6 | **all RESOLVED** (per-finding cites in the record file) |
| Verdict | **NOT CLEAN** — one NEW P1 (G1) |
| G1 (P1) | M11's "future `generated_at` -> suppress" is undetectable without a clock, which §12 #6 forbids in the block (§5.2 lists only malformed/naive). Introduced by the F5 correction. |

**Terminal rule (GOV-2 §2, §6):** the NEW P1 at the confirmation head returns the
packet to **DESIGN INCOMPLETE**. The single GOV-1 correction cycle is spent; no
further author correction without Dustin's explicit authorization. **HELD FOR
DUSTIN** — authorize a bounded G1-only second correction (drop "future" from M11;
align §5.2/§10/§12 to clock-free malformed/naive detection) + a narrow Event-2
re-confirmation of G1; OR rule G1 non-blocking; OR otherwise direct.

### Out-of-scope observations

- **O-1** `docs/artifact_flow_map.md:122` "frozen 11-tuple" vs live 12-tuple
  (GOOG, NS-4A/PRD-308). Confirmed by Event-1; the slice corrects it (§8).

---

## CORRECTION CYCLE (GOV-2 Event-1 — single consolidated author correction, 2026-08-22)

Reviewed head `6e5f176` (v0.2). One consolidated correction per GOV-1 / GOV-2 §2
step 4. Dispositions:

- **F1 (BOUNDARY, publish seam) — ACTIONED.** §6 rewritten to the real seam:
  renderer default `reports/output/dashboard.html` (dev) vs hourly
  `--output ui/dashboard.html` -> `ui/index.html` -> readiness -> `publish`
  branch -> Pages, with the workflow/publish ownership boundary enumerated (§6).
- **F2 (BOUNDARY, order/population) — ACTIONED.** Added `registry_index` to the
  row (§5.1); the renderer sorts by `(GROUP_ORDER, registry_index)` against the
  `sort_keys=True` artifact, never on-disk order; full-12 population guaranteed by
  the producer, asserted by M6; order pinned by M7 against the alphabetized
  artifact. Renderer does not import the registry.
- **F3 (BOUNDARY, admission seam / divergent ages) — ACTIONED + OWNER QUESTION.**
  §3.5 added reconciling `normalized_quotes` vs `valid_quotes`; in-scope design =
  display-parity with the existing artifact and the `trend_structure` precedent
  (no valid_quotes restriction, no age gate — both scope expansions, §12 #8,
  §14). The valid_quotes/age-bound question recorded as the genuine unresolved
  owner question (§15 Q-Freshness/Admission; handoff). Materiality unchanged (no
  carrier expansion, §2/§13).
- **F4 (P1, D-7 acceptance) — ACTIONED.** §5.1 defines the concrete reader
  acceptance contract (`source=="watchlist"` AND `schema_version==2`; missing/
  wrong -> suppress) and resolves D-7 to a justified bump-to-2 recommendation;
  M9 adds version/source identity, M11 malformed-generated_at.
- **F5 (P1, killable mutations) — ACTIONED.** §10 rewritten: whole-output
  equality for absent (M8) and each invalid class (M9); M11/M12 single exact
  outcomes; M12 unknown-group -> suppress (consistent with full-12); M13 a
  cadence/call-site assertion that reddens on a daily writer; M6 full-population,
  M7 order-against-sort_keys added.
- **F6 (P2, FILES/LOC) — ACTIONED.** `tests/test_ci_artifact_hygiene.py` added to
  FILES (§8); LOC re-estimated up (~120-160, ceiling <=190; §9); helper
  "clearer/testable" separated from "smaller" (§5.2, §15).

No finding was dismissed. F1/F2/F3 are BOUNDARY; under GOV-2 §6 the correction
performed the producer-to-final-consumer inventory refresh (§6 seam + §3.5
admission seam). Event-2 confirms F1-F6 at the v0.3 head.

---

## 18. Pre-review revision log

- **v0.3 (2026-08-22):** single consolidated correction of Event-1 F1-F6
  (CORRECTION CYCLE). Added §3.5 admission seam, `registry_index` + reader
  acceptance contract (schema_version 2), rewrote §6 publish seam, tightened §10
  to whole-output/exact-outcome mutations (M5-M13), added
  `test_ci_artifact_hygiene.py` to FILES, re-estimated LOC, recorded the
  Q-Freshness/Admission owner question. Re-verified all correction facts (§16).
  Supersedes v0.2.
- **v0.2 (2026-08-22):** pre-review OWNER ALIGNMENT pass (R1-R5; reviewed by
  Event-1 @ `6e5f176`).
- **v0.1 (2026-08-22):** initial provisional packet (never reviewed).

---

END OF PACKET v0.3 — PROVISIONAL / NOT REVIEW-CLEAN — NO IMPLEMENTATION
AUTHORITY. Codex Event-2 (EXACT-CORRECTED-HEAD CONFIRMATION of F1-F6) runs on
this revision's committed head. Gate A is neither requested nor granted.
