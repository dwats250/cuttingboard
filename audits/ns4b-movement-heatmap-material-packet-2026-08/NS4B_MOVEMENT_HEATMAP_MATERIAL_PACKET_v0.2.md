# NS-4B — Market Movement Heatmap — MATERIAL PACKET (v0.2, PROVISIONAL, REPLACEMENT)

**Status: PROVISIONAL — NOT REVIEW-CLEAN — NO IMPLEMENTATION AUTHORITY.**
This is the GOV-2 §2 step-2 provisional material packet, revised by a pre-review
OWNER ALIGNMENT pass (Dustin, 2026-08-22) that encodes product rulings lost when
the prior session ended. It carries no implementation authority (GOV-2 §4). All
FILES and LOC figures are `ESTIMATED SURFACE — NOT YET APPROVED` (GOV-2 §5).
v0.2 supersedes the never-reviewed v0.1 (no Codex event ran on v0.1; no review
trail is lost). The next governed step is the independent Codex packet review
(GOV-2 §2 step 3), which Dustin has explicitly commissioned on this revision.

**Authored against `main` @ `80ac6eb2618eb419afff6764292dec5c838204ce`**
(HEAD == origin/main, tree clean). Every line citation is current at that SHA
(author self-verification, §16).

---

## 0. Where this packet sits in the GOV-2 order

```
materiality check at intake ............................. DONE (MATERIAL; §2, §13)
producer / carrier reconciliation ...................... DONE (Stage-0 + §16 re-verify)
provisional material packet authored ................... DONE (v0.1)
pre-review OWNER ALIGNMENT pass ........................ DONE (this v0.2 doc)      <-- HERE
independent packet review (GOV-2 §2 step 3) ............ COMMISSIONED (Dustin, on v0.2)
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

## 0.1 Encoded owner product rulings (pre-review inputs, Dustin 2026-08-22)

Accepted inputs that shape the design. They are **not** the GOV-2 §2 step-6
design-direction ruling, which still comes only after the packet is
review-clean. Numbering matches the owner alignment pass.

- **R1 FULL 12-SYMBOL VISIBILITY (rules D-2, now closed).** The block shows the
  full enabled 12-symbol registry population. 10 have a live movement number;
  UCO and GOOG are unavailable-by-truth. Display contract:
  - UCO -> `n/a`; GOOG -> `n/a`.
  - any normally-fetched registry symbol missing on a particular run -> `n/a`.
  - honest zero movement -> `0.0%`.
  - NEVER convert missing/null movement to `0.0%`.
  - NEVER silently omit a missing registry member; NEVER replace it with only a
    footer count.
  - Reason: the board must not visually imply full group coverage when part of a
    group is unobserved. `n/a` is a first-class, always-present cell.
- **R2 GROUP ORDER (rules D-1, now closed).** Binding display order: INDEX,
  METALS, ENERGY, TECH, HIGH_BETA. Within each group, registry insertion order,
  presentation-only. The order implies no rank, conviction, priority, or trade
  preference.
- **R3 HOURLY-ONLY / LAST-WRITER (rules D-4, now closed).** Hourly-only stands:
  - eligible hourly render with a valid watchlist artifact -> block present.
  - later daily render without a watchlist artifact -> block absent.
  - failed/suppressed render preserves whatever board was previously published,
    per the existing publish model.
  - Do NOT add: a daily watchlist write, any runtime change, any
    `cuttingboard.yml` change, or any artifact-persistence machinery.
- **R4 FRESHNESS WORDING.** `generated_at` is the SNAPSHOT/CAPTURE clock.
  Display wording is **`captured HH:MM ET`**, never `as of HH:MM ET`. Do not
  imply `generated_at` is an exchange observation timestamp or an exact
  quote/last-trade timestamp. No speculative per-symbol freshness UI. (The
  divergent-quote-age question is a real Event-1 falsification target, §17 T-6.)
- **R5 ABSENCE / INVALID ARTIFACT.** Whole artifact absent OR invalid/unusable
  -> suppress the entire block, baseline-neutral dashboard. Valid artifact with
  an individual unavailable movement -> retain that symbol as `n/a`. No empty
  fake card; no fake zero.

Non-rulings (deliberately left as design/review questions):

- **R6 HELPER EXTRACTION (D-5 open, design choice).** Not owner-mandated. Prefer
  a thin `dashboard_renderer.py` with validation/grouping/fragment logic in a
  small pure helper IF that yields the smallest, clearer, more testable surface.
  Codex may challenge whether extraction is actually smaller. Packet design
  choice, not an owner decision.
- **R7 ARTIFACT VERSIONING (D-7 open, design/review question).** Do NOT
  pre-decide `schema_version` 1 vs 2 as an owner ruling. Justify the answer from
  actual readers, existing schema conventions, additive-field compatibility, and
  the fact that this slice creates the artifact's first machine reader. Neither
  bump mechanically nor avoid a bump mechanically (§5.1, §17 T-4).

---

## 1. Product question and user-visible outcome

A compact, read-only **MARKET MOVEMENT** block on the dashboard answering, at a
glance, the VISION question *"is today's move broad or isolated?"* — grouped by
the registry's five primary groups, every enabled registry symbol shown, each
with its move off the prior session close. No prediction, no scoring, no
ranking; it renders only numbers the pipeline already computes.

- **One block, five group lines** (INDEX, METALS, ENERGY, TECH, HIGH_BETA in
  that fixed order, R2), each a row of chips. Every one of the 12 enabled
  registry symbols appears: a live symbol as `SYM +X.X%`, an unobserved symbol
  (UCO, GOOG, or any fetch gap) as `SYM n/a` (R1). One `captured HH:MM ET`
  footer (R4). Mobile-friendly: one column, ~7 rendered lines.
- **Movement basis:** last price vs **previous session close**, decimal at
  source (`NormalizedQuote.pct_change_decimal`), x100 for display — identical to
  the trend-structure and macro-driver `change_pct` convention already on the
  board (PRD-199). No arithmetic invented.
- **Truthful cells only.** A live quote renders its signed percent (honest zero
  is `0.0%`). A null/missing movement renders `n/a` (R1) — never a fabricated
  `0.0`; PRD-262 guarantees a bad `previous_close` fails loud upstream (§11).

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
  `fetched_at_utc` (`:31`) and `age_seconds` (`:34`).
- **`fetched_at_utc = datetime.now(timezone.utc)` at fetch time**
  (`ingestion.py:112`, `:295`) — the FETCH wall-clock, NOT the exchange
  last-trade time. `age_seconds` (`normalization.py:74`) is
  `now - fetched_at_utc` at normalization; there is **no per-quote last-trade-age
  admission gate** on movement quotes (the only staleness logic is the OHLCV
  cache TTL, `ingestion.py:123-156`, a different surface). This is the basis for
  R4's wording and the §17 T-6 falsification target.
- Computed from yfinance `fast_info`: `prev_close = info.previous_close`
  (`ingestion.py:361`); an invalid `previous_close` raises `ValueError`
  (`:369`) — fail-loud, never a fabricated 0.0 (PRD-262).

### 3.2 The carrier already in hand (the sleeper)

- `build_watchlist_snapshot(normalized_quotes, generated_at)`
  (`watchlist_sidecar.py:61`) receives the **full** `NormalizedQuote` mapping,
  iterates `WATCHLIST_SYMBOLS`, and projects each row as
  `{symbol, sector_theme, watch_reason, current_price}` (`:72-77`).
  **`current_price = quote.price` (`:71`) is the ONLY quote field kept — the
  movement number is already in its hands and is dropped on the floor.**
  A missing quote already yields `current_price: None` (`:71`), the exact hook
  the `n/a` contract (R1) extends to `daily_change_pct`.
- Top level: `schema_version: 1`, `source: "watchlist"`, `generated_at`
  (tz-aware ISO, `:79-83`). The writer passes `generated_at=run_at_utc`
  (`runtime/__init__.py:784`) and writes atomically (`.tmp` -> `.replace`,
  `:2517-2519`) so a reader never sees a partial file.
- `WATCHLIST_SYMBOLS` is DERIVED from `UNIVERSE_REGISTRY`
  (`watchlist_sidecar.py:56`, `build_watchlist_symbols` `:43`), filtered on
  `inst.enabled` (`:52`). Live length is **12** (verified §16) — one row per
  enabled registry instrument, so the full-12 display contract (R1) needs no new
  symbol source.
- Rows carry the COARSE legacy `sector_theme` via `_PRIMARY_GROUP_TO_THEME`
  (`watchlist_sidecar.py:34-40`), **not** the fine `primary_group`. Grouping by
  the 5 registry groups (R2) therefore requires a `primary_group` passthrough
  (§5). The sidecar already imports `UNIVERSE_REGISTRY` / `UniverseInstrument`
  (`:26`), so this is a pure projection with no new import.

### 3.3 Write cadence

- **Hourly:** `_write_watchlist_snapshot(...)` at `runtime/__init__.py:784`,
  inside the hourly notify path, gated on `not validation_summary.system_halted`,
  after `_write_trend_structure_snapshot` (`:778`). Writer `:2507`.
- **Daily:** the `MODE_LIVE` daily block (~`:1490`) writes `trend_structure`
  (`:1495` region) and builds `spy_observation`, but **never calls
  `_write_watchlist_snapshot`.** On a fresh daily runner the artifact is absent
  -> the block suppresses honestly (R3, R5).

### 3.4 Publish safety

- `.gitignore:49` ignores `logs/`; `logs/watchlist_snapshot.json` is untracked
  (`git ls-files` returns nothing). Written run-locally, never staged, never on
  `main`, never published today. The renderer reading it from disk (slice 1)
  adds no persisted surface, no `git add -f`, no publish path (R3, §7, §12).

---

## 4. Coverage truth table (10 live + 2 n/a; full-12 display)

Authoritative source: `UNIVERSE_REGISTRY` (`universe_registry.py:52-65`, 12
enabled instruments) intersected with the fetched universe `config.ALL_SYMBOLS`
(`config.py:264` = MACRO_DRIVERS + INDICES + COMMODITIES + HIGH_BETA,
`:258-262`). A symbol has a live movement number iff it is fetched.

| Symbol | primary_group | Fetched (in ALL_SYMBOLS)? | Cell today |
|---|---|---|---|
| SPY  | INDEX     | YES (INDICES)     | live |
| QQQ  | INDEX     | YES (INDICES)     | live |
| GDX  | METALS    | YES (COMMODITIES) | live |
| GLD  | METALS    | YES (COMMODITIES) | live |
| SLV  | METALS    | YES (COMMODITIES) | live |
| XLE  | ENERGY    | YES (COMMODITIES) | live |
| UCO  | ENERGY    | **NO** (config has `USO`, not `UCO`) | **n/a** |
| NVDA | TECH      | YES (HIGH_BETA)   | live |
| META | TECH      | YES (HIGH_BETA)   | live |
| AMZN | TECH      | YES (HIGH_BETA)   | live |
| GOOG | TECH      | **NO** (absent from config HIGH_BETA) | **n/a** |
| TSLA | HIGH_BETA | YES (HIGH_BETA)   | live |

**All 12 shown (R1); 10 live, 2 `n/a`.** By group: INDEX 2/2, METALS 3/3,
ENERGY 1/2 (UCO n/a), TECH 3/4 (GOOG n/a), HIGH_BETA 1/1 — and because the two
`n/a` cells are visible, the board never implies full ENERGY/TECH coverage while
part of the group is unobserved (R1 reason).

> Precision note (conclusion unchanged from Stage-0): `config.ALL_SYMBOLS`
> fetches far more than these 10 (VIX, TNX, IWM, PAAS, USO, AAPL, COIN, MSTR,
> and the macro drivers). The exact claim is: **10 of the 12 registry symbols
> are in the fetched universe; UCO and GOOG are the two registry symbols absent
> from it.**

---

## 5. Design (the slice)

### 5.1 Sidecar contract change (`watchlist_sidecar.py`)

Add two fields to each snapshot row, additive only:

- `daily_change_pct`: `round(quote.pct_change_decimal * 100, 1)` when a quote is
  present, else `null`. Same basis and x100 convention as trend-structure
  `daily_change_pct` (PRD-199). The `null` case is the `n/a` hook (R1); it is
  never coerced to `0.0`.
- `primary_group`: `inst.primary_group` passthrough from the registry (INDEX /
  METALS / ENERGY / TECH / HIGH_BETA). Requires threading `primary_group`
  through `WATCHLIST_SYMBOLS` (currently `(symbol, theme, reason)`) or reading it
  alongside. Pure projection; registry already imported.

Row shape after the change (existing keys byte-unchanged, new keys appended):
`{symbol, sector_theme, watch_reason, current_price, daily_change_pct,
primary_group}`.

**`schema_version` (R7 / D-7, genuine design/review question — no owner lean).**
The artifact is `schema_version: 1` today with **zero machine readers**; this
slice adds the first reader and two additive keys. Arguments to weigh in the
PRD, not to pre-decide here: (a) additive-only keys are backward-compatible, so
existing shape consumers (none machine today) are unaffected either way;
(b) house convention on when a `schema_version` bumps for additive keys (to be
read from `SCHEMA_MAP.md` / sibling artifacts); (c) honesty of signalling a
contract that now has a reader. The PRD must justify bump-to-2 vs
stay-at-1-additive from these, not mechanically. Codex Event-1 target T-4.

### 5.2 Renderer block (`dashboard_renderer.py`, optional `movement_card.py`)

- **Read** `logs/watchlist_snapshot.json` from disk (same artifact-driven
  pattern as `trend_structure_snapshot.json` and `gex_card.py`). The renderer
  never imports the registry; it consumes only the artifact.
- **Validate then render (R5).** Artifact absent, unreadable, malformed JSON, or
  structurally unusable (missing `symbols`, wrong types) -> suppress the entire
  block, baseline-neutral. Only a structurally valid artifact renders a block.
- **Full-12 grouped render (R1, R2).** One `MARKET MOVEMENT` block; groups in
  the fixed order INDEX, METALS, ENERGY, TECH, HIGH_BETA (a new explicit ordered
  constant; `PRIMARY_GROUPS` is an unordered `frozenset` and registry insertion
  order interleaves TSLA among TECH, so neither is relied on). Within a group,
  registry insertion order. Every enabled registry symbol appears; a symbol with
  `daily_change_pct == null` renders `n/a`, never omitted, never `0.0` (R1).
- **Chips:** `SYM +X.X%` for live (sign, one decimal; existing +/- tape
  convention; honest zero `0.0%`), `SYM n/a` for null.
- **Footer:** one `captured HH:MM ET` derived from the snapshot `generated_at`
  (R4). Null/malformed `generated_at` -> footer omitted (block still coherent) or
  the whole block suppressed under R5 if the artifact is thereby unusable.
- **Helper (R6 / D-5, design choice).** A small
  `cuttingboard/delivery/movement_card.py` mirroring `gex_card.py` is proposed to
  keep validation/grouping/fragment logic pure and testable and the renderer
  thin — subject to Codex challenge that inline is smaller (T-9).

---

## 6. Seam trace (complete artifact lifecycle)

```
ingestion.fetch (yfinance fast_info; fetched_at_utc = now, :112/:295)
  -> NormalizedQuote.pct_change_decimal            [normalization.py:29; fail-loud ingestion.py:369]
  -> runtime hourly notify path (non-halt)         [runtime/__init__.py:784, generated_at=run_at_utc]
       -> _write_watchlist_snapshot (atomic)       [runtime/__init__.py:2507; .tmp->.replace :2517-2519]
            -> build_watchlist_snapshot            [watchlist_sidecar.py:61]
                 (ADD daily_change_pct + primary_group per row; null -> n/a hook)   <-- slice change
            -> logs/watchlist_snapshot.json        [WATCHLIST_PATH, _constants.py:57; gitignored :49]
  -> dashboard_renderer validates + reads artifact <-- slice change (FIRST machine reader ever)
       -> MARKET MOVEMENT block (full-12, grouped)  <-- slice change (optional movement_card.py)
       -> reports/output/dashboard.html
  -> (publish path) rendered dashboard on the publish branch (hourly runs only; daily absent, R3)
```

**Reader inventory of `logs/watchlist_snapshot.json` today (zero-reader claim,
falsification attempted):** the only occurrences in `cuttingboard/`, `tools/`,
`tests/` are the writer (`runtime/__init__.py:2507/2513/2521`), the path constant
(`_constants.py:57`), and writer unit tests (`tests/test_watchlist_sidecar.py:287-305`).
The renderer's only `watchlist` reference is `_os_sections.get("watchlist")`
(`dashboard_renderer.py:2522`) — the **overnight-scan** section, a different
object, NOT this artifact. **Confirmed: zero machine readers today.**

---

## 7. Schema / persistence classification

- The two new row keys are **additive** to a transient, run-local, gitignored
  artifact. No `PAYLOAD_SCHEMA_VERSION` bump, no `assert_valid_payload`
  required-key change, no cat-2/cat-3/cat-4 artifact touched, no decision
  contract, no audit surface. (The artifact's own `schema_version` decision is
  D-7 / T-4, §5.1.)
- **No new persisted surface.** The artifact stays untracked and unpublished;
  the renderer reads it from disk within the same run, as it reads
  `trend_structure_snapshot.json` today.
- **Publish behavior / last-writer (R3).** Only the hourly path writes the
  artifact, so the block is present on the published dashboard after hourly
  publishes and absent after the daily publish until the next hourly. A
  failed/suppressed render leaves the previously published board in place per the
  existing publish model. Truthful (no stale data shown); making it
  always-present is slice 2 (daily write), explicitly deferred with its
  `git add -f logs/` publish side effect (§14).

---

## 8. FILES cone (ESTIMATED SURFACE — NOT YET APPROVED)

| Op | File | Purpose |
|---|---|---|
| M | `cuttingboard/watchlist_sidecar.py` | add `daily_change_pct` + `primary_group` per row; thread `primary_group` through rows |
| M | `cuttingboard/delivery/dashboard_renderer.py` | MARKET MOVEMENT block: validate + read artifact, full-12 grouped render, R5 suppression |
| A (design choice, R6) | `cuttingboard/delivery/movement_card.py` | small pure block-builder/validator mirroring `gex_card.py` |
| M | `tests/test_watchlist_sidecar.py` | new-field presence, scale, null-preserved, group passthrough |
| M | `tests/test_dashboard_renderer.py` | full-12 presence, n/a cells, honest-zero vs n/a, group order, R5 suppression (absent + malformed), captured-clock |
| M | `docs/SCHEMA_MAP.md` | `watchlist_snapshot.json` row schema truth (new fields, version decision) |
| M | `docs/artifact_flow_map.md` | `watchlist_snapshot.json` entry: add the renderer as a reader; correct the stale `11-tuple` to `12-tuple` (§17 O-1) |
| M | `docs/PRD_REGISTRY.md`, `docs/prd_index.json`, `docs/PROJECT_STATE.md` | Stage-0 bookkeeping |
| M | `docs/plans/decision-support-workplan-v0.1.md` | ledger row |
| A | `docs/prd_history/PRD-NNN.md` | the Stage-0 PRD scaffold (post-ruling) |

**Deliberately NOT in FILES:** `cuttingboard/runtime/__init__.py` (no runtime
change in slice 1), `normalization.py`, `ingestion.py`, `universe_registry.py`,
`config.py` (adding UCO/GOOG is out of this slice). Touching any is a §12
stop-and-amend event. PRD-158 sweep: this change deletes/renames no rendered
token; a sweep over `watchlist_snapshot`, `daily_change_pct`, `primary_group`
adds no further asserting test files beyond the two listed.

Slice 2 (deferred, §14) would add `cuttingboard/runtime/__init__.py` (one daily
write call) and accept the publish side effect.

---

## 9. Estimated production LOC ceiling (ESTIMATED SURFACE — NOT YET APPROVED)

Governing metric: net production LOC via `git diff --numstat` across authorized
production files; test LOC uncounted.

- **~95-120 net production LOC; provisional ceiling <=150.** Sidecar passthrough
  ~10; renderer block + R5 validation + grouping + full-12/n-a ~80-100 (helper
  split neutral to the total). Test LOC ~130 (absent + malformed baselines,
  presence, n/a, honest-zero, group order, captured-clock).
- **Stop-and-amend tripwire:** any production file beyond §8, any runtime write
  change, any schema/persistence/decision-contract touch, any config universe
  edit -> §12.

Non-binding; the first binding ceiling is Gate A on the reviewed PRD.

---

## 10. Discriminating test / mutation matrix (M-suffix = reddening mutation required)

| # | Case | Asserted | Mut? |
|---|---|---|---|
| M1 | Scale correctness | row `daily_change_pct == round(pct_change_decimal * 100, 1)`; fixture where decimal vs percent differ | **YES** — emitting the raw decimal reddens |
| M2 | Null preserved, never fabricated | missing `NormalizedQuote` -> row `daily_change_pct is None` and `current_price is None`; never `0.0` | **YES** — coercing null to `0.0` reddens |
| M3 | Honest zero distinct from n/a | a live quote with `pct_change_decimal == 0.0` -> cell `0.0%`, NOT `n/a`; a null -> `n/a`, NOT `0.0%` | **YES** — collapsing the two reddens |
| M4 | Group passthrough | row `primary_group` is the fine registry group, not coarse `sector_theme`; fixture where they differ (TECH vs "High beta") | **YES** — projecting `sector_theme` reddens |
| M5 | Additive-only rows | `symbol`/`sector_theme`/`watch_reason`/`current_price` byte-unchanged per row; new keys additive | **YES** — altering an existing key reddens |
| M6 | Full-12 visibility | valid artifact -> all 12 enabled registry symbols rendered, including UCO/GOOG as `n/a`; none omitted | **YES** — omitting a null-movement symbol reddens |
| M7 | Group order + placement | five groups in fixed order INDEX, METALS, ENERGY, TECH, HIGH_BETA; TSLA under HIGH_BETA (not interleaved into TECH) | **YES** — relying on `frozenset` iteration or registry insertion order reddens |
| M8 | Suppression: artifact absent | no `watchlist_snapshot.json` -> NO block; dashboard byte-identical to baseline | **YES** — rendering an empty block reddens |
| M9 | Suppression: artifact invalid | malformed JSON / missing `symbols` / wrong types -> NO block, baseline-neutral (R5) | **YES** — rendering from a malformed artifact reddens |
| M10 | Captured clock | footer `captured HH:MM ET` derived from `generated_at`; wording is "captured", not "as of" | **YES** — reading wall-clock, or emitting "as of", reddens |
| M11 | Malformed/naive/future generated_at | naive or non-parseable `generated_at` -> footer omitted or block suppressed per R5; never a crash, never a fabricated time | **YES** — crashing or defaulting to `now()` reddens |
| M12 | Unknown primary_group | a row whose `primary_group` is outside the five known groups -> fail-loud drop into "unusable" (block suppressed) or explicit skip, per the chosen contract; never silently mis-grouped | **YES** — silently bucketing an unknown group reddens |
| M13 | Daily suppression e2e | render with no watchlist artifact (daily-runner condition) -> no block, baseline-neutral | **YES** — a daily write sneaking in reddens (slice-2 boundary guard) |
| M14 | Fail-loud upstream preserved | invalid `previous_close` still raises upstream (PRD-262) so no fabricated `0.0` reaches a row (documents the guarantee) | |

Reuse existing `NormalizedQuote` fixtures (`tests/test_watchlist_sidecar.py`) and
the dashboard substring-presence/absence style (`tests/test_dashboard_renderer.py`)
— targeted substring baseline for the absent/malformed cases, NOT a golden
byte-diff. A guard whose mutation leaves all tests green is not a guard and does
not merge (PRD-198 invariant 4).

---

## 11. Unavailable / failure semantics

- **Artifact absent OR invalid/unusable** (daily runner; hourly halt where the
  write is skipped at `:784`; malformed JSON; missing `symbols`) -> whole block
  suppressed, baseline-neutral (R5). No empty fake card.
- **Individual symbol null** (UCO, GOOG, any fetch gap) -> cell `n/a`, row
  retained (R1). Never `0.0`.
- **Honest zero** (live quote, `pct_change_decimal == 0.0`) -> `0.0%`, distinct
  from `n/a`.
- **Bad `previous_close`** -> `ValueError` upstream (`ingestion.py:369`, PRD-262)
  -> symbol has no valid quote -> falls into the null path. Fabrication is
  impossible by construction (PRD-198 invariant 1).

---

## 12. Stop-and-amend conditions (hard stops — return to Dustin, re-run GOV-2 §1)

1. Any change to `runtime/__init__.py` (any write-cadence change is slice 2).
2. Any config universe edit (adding UCO/GOOG to `config.ALL_SYMBOLS`).
3. Any `PAYLOAD_SCHEMA_VERSION` bump or `assert_valid_payload` required-key add.
4. Any NEW durable/published persistence surface, or any `git add -f` of the
   artifact.
5. Renderer-side derivation/recomputation of any movement value (the renderer
   projects; it never recomputes `pct_change`).
6. Any wall-clock (`datetime.now()`) dependence in the block (freshness is keyed
   on the snapshot `generated_at`, R4).
7. Any conversion of a null/missing movement to `0.0` (violates R1).
8. Any change to `normalization.py`, `ingestion.py`, or `universe_registry.py`
   beyond read-only.
9. Exceeding the §8 file surface or the §9 ceiling without a fresh GOV-2 §1
   classification.
10. Any scoring, ranking, permission, bullish/bearish labeling, or relative-
    strength computation entering the block (VISION non-goal; §14).

---

## 13. Materiality / lane classification

**MATERIAL** under GOV-2 §1 (new cross-layer artifact->renderer carrier;
delivery+dashboard span; §2). **Lane: HIGH-RISK**, forced independently by
`dashboard_renderer.py` being CONSUMER HIGH-RISK FILES payload (PRD-121 R11) —
not by MATERIAL, which never converts the lane. MICRO-ineligible. After this
packet is review-clean and Dustin issues a design-direction ruling, a fresh
Stage-0 PRD -> independent PRD review -> Gate A sequence is required before
implementation (GOV-2 §4).

**Governance hold:** NS-4B rides the personalized-news / decision-support
expansion track; the landing PR carries the GOV-0 / PRD-186 visible hold (opened
DRAFT, self-named), held for Dustin.

---

## 14. What gets CUT (out of scope)

- Scoring, ranking, permission, bullish/bearish labels, prediction (VISION
  non-goal).
- New provider / ingestion. UCO and GOOG stay unavailable (shown `n/a`); adding
  them is a future 2-symbol `config.ALL_SYMBOLS` edit, Dustin's call, not this
  slice.
- The trend-structure-only variant (0 TECH / 0 HIGH_BETA; cannot answer the
  question).
- Registry schema changes; a second board; a new cadence (rides the existing
  hourly render); benchmark / relative-strength; any generalized universe engine.
- **Daily write (slice 2, deferred, R3):** one mirrored ~6-line
  `_write_watchlist_snapshot` call in the daily `MODE_LIVE` block, which would
  make the block always-present but persist the artifact into the
  `cuttingboard.yml` `git add -f logs/` publish set. A separate decision with
  its own §12 tripwire (#1, #4).

---

## 15. Open design/review questions (owner rulings closed D-1/D-2/D-4, §0.1)

- **D-5 Helper extraction (R6).** `movement_card.py` mirroring `gex_card.py`
  (proposed) vs inline — smallest clearer testable surface wins; Codex may
  challenge (T-9). Design choice, not owner decision.
- **D-7 Artifact versioning (R7).** `schema_version` 1->2 additive vs
  stay-at-1-additive, justified from readers/conventions/compat/first-reader
  (§5.1; T-4). Genuine design/review question.
- **Q-Freshness admissibility (R4/T-6).** Whether existing quote-admission rules
  permit materially divergent quote ages within one valid snapshot such that a
  single `captured HH:MM ET` clock could understate real per-symbol staleness.
  Evidence at `80ac6eb`: `fetched_at_utc` is fetch wall-clock (not last-trade
  time); no per-quote last-trade-age gate found (§3.1). Intended contract: one
  compact capture clock. **The reviewer must falsify** whether last-trade
  staleness can diverge materially and, if so, whether it must be surfaced. The
  packet invents no gate; it names the question.

---

## 16. Author self-verification record (GOV-2 §3)

All against `main` @ `80ac6eb`, tree clean, re-run by the authoring agent (not a
delegated sweep; CLAUDE.md Author-discipline 4). v0.2 additions marked [v0.2]:

- Passthrough drop: `watchlist_sidecar.py:61-83`; `current_price = quote.price`
  (`:71`) is the sole quote field; missing -> `None` (the n/a hook). CONFIRMED.
- Movement source + fail-loud: `normalization.py:26/29/31/34`;
  `ingestion.py:361/369`. CONFIRMED.
- [v0.2] `fetched_at_utc = datetime.now(timezone.utc)` at fetch (`ingestion.py:112/295`),
  fetch-clock not last-trade-time; no per-quote last-trade-age admission gate
  (`rg age_seconds|max_age|stale|admit|reject` -> only OHLCV cache TTL and the
  normalization computation). CONFIRMED -> R4 wording + T-6.
- [v0.2] Atomic write + `generated_at=run_at_utc`: `runtime/__init__.py:784`,
  writer `:2507`, `.tmp`->`.replace` `:2517-2519`. CONFIRMED.
- Write cadence: hourly `:784` (non-halt gate); daily `MODE_LIVE` block
  ~`:1490-1516` writes trend_structure + spy_observation, no watchlist write.
  CONFIRMED.
- Zero machine readers: `rg watchlist_snapshot` -> writer + path constant +
  writer-tests only; renderer's `watchlist` is the overnight-scan section
  (`dashboard_renderer.py:2522`). CONFIRMED (§6).
- Coverage 10 live + 2 n/a: `universe_registry.py:52-65` (12 enabled) vs
  `config.py:258-264`; UCO absent (config has USO), GOOG absent. CONFIRMED (§4).
- Row grouping today is coarse `sector_theme` via `_PRIMARY_GROUP_TO_THEME`
  (`watchlist_sidecar.py:34-40`); registry already imported (`:26`). CONFIRMED.
- Publish safety: `.gitignore:49`; `git ls-files logs/watchlist_snapshot.json`
  empty. CONFIRMED.
- Live `len(WATCHLIST_SYMBOLS) == 12` (Python import). CONFIRMED.
- FILES-cone paths all exist; `gex_card.py` precedent present. CONFIRMED.

Author self-verification is NOT independent review (GOV-2 §3). The independent
Codex packet review (§17) is commissioned on this v0.2 head.

---

## 17. Packet review records (GOV-2 §2, §7)

### Falsification targets for Codex Event-1 (owner-directed, 2026-08-22)

Event-1 must review the packet AND the underlying repo surface in fresh context
and attempt to falsify each:

- **T-1** the complete producer -> artifact -> renderer -> final publish seam (§6).
- **T-2** the full-12 visual contract / 10-live + 2-n/a truth (R1, §4).
- **T-3** movement units and prior-close semantics (§3.1, §5.1).
- **T-4** additive row-contract consequences AND the `schema_version` decision
  (D-7, §5.1) — justified, not mechanical.
- **T-5** capture/freshness wording and the "captured" vs "as of" contract (R4).
- **T-6** whether admission rules permit materially divergent quote ages inside
  one valid snapshot (Q-Freshness, §15) — surface as a real finding if yes.
- **T-7** baseline-neutral suppression on absent AND invalid artifact (R5, M8/M9).
- **T-8** hourly-only / daily-absent last-writer behavior; no persistence (R3).
- **T-9** renderer/helper FILES completeness and whether extraction is smaller (R6).
- **T-10** asserting test / mutation completeness (§10); every named mutation
  killable by construction (PRD-198 inv. 4).
- **T-11** estimated FILES and LOC (§8, §9); no decision coupling.

### INITIAL PACKET REVIEW — PENDING (commissioned on v0.2)

| Field | Value |
|---|---|
| Event type | `INITIAL PACKET REVIEW` (GOV-2 §2; owner-commissioned 2026-08-22) |
| Reviewer identity / capability role | independent Codex packet review, fresh context, read-only (`codex exec -s read-only`) |
| Reviewed commit SHA / packet revision | (v0.2 committed head — pinned at commission) |
| Verdict | PENDING |
| Findings and dispositions | PENDING |
| Fresh-context / independence / run-isolation evidence | PENDING |

### EXACT-CORRECTED-HEAD CONFIRMATION — PENDING

| Field | Value |
|---|---|
| Event type | `EXACT-CORRECTED-HEAD CONFIRMATION` (GOV-2 §2 step 5) |
| Scope | confirmation of the Event-1 findings at the corrected head, not a fresh-scope review |
| Reviewed commit SHA | PENDING (after the one consolidated correction) |
| Verdict | PENDING |

**Terminal rule (GOV-2 §2, §6):** a NEW material boundary omission at a
confirmation head returns the packet to DESIGN INCOMPLETE rather than opening a
further review loop.

### Out-of-scope observations (existing-code, NOT NS-4B fixes)

- **O-1** `docs/artifact_flow_map.md:122` calls `WATCHLIST_SYMBOLS` a "frozen
  11-tuple"; the live value is a 12-tuple (GOOG added in NS-4A / PRD-308). Stale
  doc-drift; the slice corrects it while editing that entry (§8). Recorded so the
  packet review does not rediscover it as an NS-4B defect.

---

## 18. Pre-review revision log

- **v0.2 (2026-08-22):** pre-review OWNER ALIGNMENT pass. Encoded R1-R5 owner
  product rulings (full-12 visibility with `n/a`; group order; hourly last-writer;
  "captured" freshness wording; absent/invalid suppression); kept R6 helper and
  R7 versioning as open design/review questions; added the freshness-admissibility
  question (Q-Freshness) and the Codex Event-1 falsification target list (T-1..T-11);
  added mutations M3 (honest-zero vs n/a), M6 (full-12), M9 (invalid artifact),
  M11 (malformed generated_at), M12 (unknown primary_group). Re-verified the new
  claims against `main` @ `80ac6eb` (§16 [v0.2] lines). Supersedes v0.1.
- **v0.1 (2026-08-22):** initial provisional packet (superseded; never reviewed).

---

END OF PACKET v0.2 — PROVISIONAL / NOT REVIEW-CLEAN — NO IMPLEMENTATION
AUTHORITY. Codex Event-1 (INITIAL PACKET REVIEW) is owner-commissioned on this
revision's committed head. Gate A is neither requested nor granted.
