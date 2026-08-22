# NS-4B — Market Movement Heatmap (12/12) — MATERIAL PACKET (v0.4, PROVISIONAL, REPLACEMENT)

**Status: PROVISIONAL — NOT REVIEW-CLEAN — NO IMPLEMENTATION AUTHORITY.**
v0.4 is a MATERIAL BOUNDARY RESET (Dustin, 2026-08-22): NS-4B now targets **12/12
LIVE coverage** by actually fetching UCO and GOOG through the existing free
yfinance path, as fetched-but-non-tradable observation symbols. This EXPANDS the
producer/fetch boundary relative to v0.3 (which was designed around 10/12 and
excluded fetch-universe change). It carries no implementation authority (GOV-2
§4). All FILES/LOC are `ESTIMATED SURFACE — NOT YET APPROVED` (GOV-2 §5).

Because owner direction expands the MATERIAL boundary, the packet is REOPENED: a
FRESH Codex Event-1 runs against the expanded boundary (owner-commissioned). The
prior Event-1 (v0.2 @ `6e5f176`) and Event-2 (v0.3 @ `5d21923`) records are
preserved as historical evidence of the 10/12 boundary; they do NOT certify the
new 12/12 boundary. The G1 defect from the v0.3 Event-2 is fixed in this design
(§10 M11).

**Code baseline `main` @ `80ac6eb2618eb419afff6764292dec5c838204ce`.** Live
yfinance verification and all citations current (§16).

---

## 0. Where this packet sits in the GOV-2 order

```
MATERIAL boundary reset to 12/12 (owner, 2026-08-22) ... DONE
bounded UCO/GOOG fetch-impact trace ................... DONE (§4.1-4.3, §16)
revised provisional packet (expanded boundary) ....... DONE (this v0.4 doc)   <-- HERE
FRESH independent packet review (Event-1) ............ COMMISSIONED (owner, on v0.4)
one consolidated correction ........................... PENDING
exact-corrected-head confirmation (Event-2) .......... PENDING
Dustin design-direction ruling ....................... PENDING
Stage-0 PRD -> independent PRD review -> Gate A ....... PENDING
```

Historical (10/12 boundary, superseded, retained as evidence): Event-1 FINDINGS
@ `6e5f176`; consolidated correction -> v0.3; Event-2 F1-F6 RESOLVED but NOT
CLEAN on G1 @ `5d21923`.

MICRO-ineligible (MATERIAL, §13); rides **HIGH-RISK** (`dashboard_renderer.py`
CONSUMER HIGH-RISK payload).

---

## 0.1 Encoded owner product rulings

- **R1' FULL 12/12 LIVE VISIBILITY (supersedes the 10/12 subset ruling).** All 12
  enabled registry symbols are part of the fetched movement universe and normally
  carry real previous-close movement when their fetch succeeds. A transient
  fetch/validation failure for ANY individual symbol renders that symbol `n/a`.
  Honest zero -> `0.0%`. Never fabricate missing movement as `0.0`. Never silently
  omit a symbol.
- **R2 GROUP ORDER.** INDEX, METALS, ENERGY, TECH, HIGH_BETA; within group,
  registry insertion order (via `registry_index`, §5.1); implies no rank.
- **R3 HOURLY-ONLY / LAST-WRITER.** Hourly render with a valid artifact -> block
  present; daily render without artifact -> absent; failed render preserves the
  prior board. No daily watchlist write, no `cuttingboard.yml` change, no
  persistence machinery.
- **R4 FRESHNESS.** `captured HH:MM ET` from `generated_at` (run capture clock,
  not exchange/last-trade time); no speculative per-symbol freshness UI.
- **R5 ABSENCE / INVALID.** Whole artifact absent OR invalid -> suppress the block
  (baseline-neutral); individual null -> `n/a`.
- **R8 OBSERVE-ONLY BOUNDARY (new, hard).** Adding UCO/GOOG to the fetch universe
  must create NO new strategy eligibility, regime/leadership semantics,
  qualification rule, risk rule, notification priority, ranking, or trade
  permission. If putting either symbol into an existing category list would
  change any such behavior, choose a narrower fetch-only seam. (Proven and
  satisfied by the `OBSERVE_ONLY` seam, §4.)

Open design/review (not owner rulings): **R6 helper** (D-5); **R7 versioning**
(D-7, resolved to a justified recommendation, §5.1); **PRICE_BOUNDS** choice
(§4.3).

---

## 1. Product question and user-visible outcome

A compact, read-only **MARKET MOVEMENT** block answering *"is today's move broad
or isolated?"*, grouped by the registry's five primary groups, showing all 12
enabled registry symbols, each with its move off the prior session close. No
prediction, scoring, or ranking.

- **12/12 normally live.** UCO and GOOG are added to the fetched universe (§4) and
  carry real movement when their fetch succeeds. Any symbol whose fetch/validation
  transiently fails renders `SYM n/a` (R1', R5). Honest zero -> `0.0%`; null ->
  `n/a`, never fabricated `0.0`.
- **Movement basis:** last price vs previous session close, decimal at source
  (`pct_change_decimal`), x100 for display (PRD-199 convention; Event-1 T-3
  CONFIRMED).
- **Groups** in fixed order (R2), one `captured HH:MM ET` footer (R4).

---

## 2. Intake classification (GOV-2 §1) — EXPANDED boundary

**MATERIAL: YES.** Beyond v0.3's carrier trigger (`watchlist_snapshot.json` as a
new artifact->renderer carrier), v0.4 expands the boundary to the **fetch
universe**: `config.ALL_SYMBOLS` gains UCO/GOOG, which is read by an
ingestion loop AND by `regime.py:114` (a breadth denominator). The slice
therefore crosses ingestion, a regime read-surface, config, delivery, and
dashboard. The design PROVES the regime/decision surfaces are invariant (§4.2):
UCO/GOOG are simultaneously placed in `NON_TRADABLE_SYMBOLS`, so the tradable
universe and breadth denominator are unchanged. Materiality stands (bigger
boundary); lane HIGH-RISK is forced independently by `dashboard_renderer.py`
(§13).

---

## 3. Verified current state (carrier / movement / freshness / admission)

### 3.1 Movement number + freshness clock
`NormalizedQuote.pct_change_decimal` (`normalization.py:29`), decimal; from
`fast_info`: `(last_price - previous_close)/previous_close`, invalid
`previous_close` fails loud (`ingestion.py:361/369`, PRD-262). `fetched_at_utc =
datetime.now(timezone.utc)` at fetch, pre-retry (`ingestion.py:112/295`) — a
FETCH clock, not an exchange last-trade time; no per-quote last-trade-age gate
(only OHLCV cache TTL). Basis for R4 wording + the Q-Freshness owner question
(§15).

### 3.2 Carrier already in hand
`build_watchlist_snapshot(normalized_quotes, generated_at)`
(`watchlist_sidecar.py:61`) iterates `WATCHLIST_SYMBOLS` (12 enabled registry
symbols, §16) and keeps only `current_price = quote.price` (`:71`); a missing
quote yields `current_price: None` — the `n/a` hook. Top level `schema_version:1`,
`source:"watchlist"`, `generated_at`; writer passes `run_at_utc`
(`runtime/__init__.py:784`), atomic `json.dumps(..., sort_keys=True)` then
`.tmp`->`.replace` (`:2517-2519`). `sort_keys=True` alphabetizes `symbols` — so
registry order needs an explicit field (§5.1, ex-F2). Rows carry coarse
`sector_theme` via `_PRIMARY_GROUP_TO_THEME` (`:34-40`), not fine `primary_group`.

### 3.3 Write cadence
Hourly `_write_watchlist_snapshot` at `:784` (non-halt gate); daily `MODE_LIVE`
never writes it (Event-1 T-8). Fresh daily runner -> absent -> suppressed (R3,R5).

### 3.4 Publish safety
`.gitignore:49`; artifact untracked, not restored, not staged (Event-1 T-8).
Renderer reads from disk within the run; no persisted/published file.

### 3.5 Admission seam
Sidecar is fed the full `normalized_quotes` (`:784`), not
`validation_summary.valid_quotes` (regime/derived/structure use `valid_quotes`,
`:570/:588/:599`); the shipped `trend_structure` sidecar uses the identical
`normalized_quotes` input (`:770`). NS-4B is display-parity with the existing
artifact; no valid_quotes restriction and no age gate (both runtime scope
expansions). The valid_quotes/age question is the genuine unresolved OWNER
question (§15 Q-Freshness).

---

## 4. The 12/12 fetch seam (bounded UCO/GOOG impact trace)

### 4.1 The smallest safe fetch-universe change

Add a dedicated observe-only list and fence it as non-tradable:

```python
# config.py
OBSERVE_ONLY = ["UCO", "GOOG"]                 # fetched for observation, never tradable
ALL_SYMBOLS = MACRO_DRIVERS + INDICES + COMMODITIES + HIGH_BETA + OBSERVE_ONLY
NON_TRADABLE_SYMBOLS = frozenset(MACRO_DRIVERS + OBSERVE_ONLY)   # was frozenset(MACRO_DRIVERS)
```

- Ingestion iterates `ALL_SYMBOLS` (`ingestion.py:78`) with NO code change -> UCO
  and GOOG are fetched.
- Membership in `NON_TRADABLE_SYMBOLS` is THE mechanism that makes a fetched
  symbol non-tradable and breadth-excluded (§4.2). UCO/GOOG join that tier —
  exactly the macro-driver treatment, minus the macro-specific rendering (which
  keys on `MACRO_DRIVERS`, which they do NOT join).
- **UCO/GOOG are deliberately NOT added to `COMMODITIES`/`HIGH_BETA`**: those
  lists have exactly one production reader each (the `ALL_SYMBOLS` concat) and
  confer no semantic role, but adding a symbol there without `NON_TRADABLE` would
  make it tradable — so `OBSERVE_ONLY` is clearer and self-documenting.
- **NOT added to `MACRO_DRIVERS`** (would grant macro-contract/rendering
  semantics, `contract.py:539`), **NOT to `REQUIRED_SYMBOLS`/`HALT_SYMBOLS`** (so
  a UCO/GOOG fetch failure never halts the run — it renders `n/a`, R1').

### 4.2 Downstream behavioral-impact inventory + no-decision-authority proof (R8)

Every reader of `ALL_SYMBOLS` / `NON_TRADABLE_SYMBOLS` / the category lists, and
the effect of the seam:

| Consumer | Role | Effect of adding UCO/GOOG via OBSERVE_ONLY |
|---|---|---|
| `ingestion.py:78` (`for s in ALL_SYMBOLS`) | INGESTION | fetches UCO/GOOG — the intended effect |
| `regime.py:112` breadth `advancing` numerator | SEMANTIC | excludes `NON_TRADABLE` -> UCO/GOOG excluded -> UNCHANGED |
| `regime.py:114` breadth `total` denominator | SEMANTIC | `sum(ALL_SYMBOLS not in NON_TRADABLE)` -> stays **16** (25-9), UNCHANGED |
| `regime.py:120` `EXPANSION_LEADERSHIP_SYMBOLS` | SEMANTIC | separate hardcoded list; UCO/GOOG absent -> UNCHANGED |
| `universe.py:11` `is_tradable_symbol` | SEMANTIC | `s not in NON_TRADABLE` -> **False** for UCO/GOOG -> not tradable |
| `trade_decision.py:113` `is_actionable_trade` | SEMANTIC | requires `not in NON_TRADABLE` -> **False** -> never actionable |
| `runtime/__init__.py:503` hourly top-trades filter | SEMANTIC | `is_tradable_symbol` -> excludes UCO/GOOG |
| `runtime/__init__.py:2435` `_tradable_symbols` | DEAD | no production caller (verified) |
| `COMMODITIES`/`HIGH_BETA`/`INDICES` | INGESTION-ONLY | not touched by the seam |
| `MACRO_DRIVERS` / `contract.py:539` macro contract | SEMANTIC | not touched (UCO/GOOG not added to MACRO_DRIVERS) |
| `PRICE_BOUNDS` (`validation.py:204`) | VALIDATION | optional; omitted for UCO/GOOG (§4.3) |
| `SYMBOL_SOURCE_PRIORITY` (`ingestion.py:93`) | INGESTION | `.get(..., default=["yfinance"])` -> no entry needed |

**Proof of no new decision authority (R8):** UCO/GOOG are non-tradable
(`is_tradable_symbol`=False, `is_actionable_trade`=False); the EXPANSION breadth
denominator is invariant at 16 (they are excluded); leadership, required/halt,
and macro-contract sets are untouched; the hourly candidate projection filters
them out. They may appear in `structure`/`derived` exactly as the existing
non-tradable macro drivers already do, and are never actionable. **The existing
`tests/test_expansion_regime.py` assertions ("denominator must stay the
configured 16", `:208/:221`) remain GREEN and act as a standing guard: they
redden if UCO/GOOG ever become tradable.**

### 4.3 PRICE_BOUNDS decision

`PRICE_BOUNDS` is OPTIONAL: `validation.py:204` guards with
`if symbol in config.PRICE_BOUNDS`; an absent symbol skips only the per-symbol
range check. The non-tradable macro drivers already fetch and validate honestly
WITHOUT bounds. **Recommend: OMIT `PRICE_BOUNDS` for UCO/GOOG** (macro-driver /
non-tradable precedent) — validation stays honest via the universal checks
(`last_price` finite/>0, `previous_close` finite/>0 fail-loud, NaN/Inf reject,
pct-change bounds `:212`). No arbitrary bounds are invented. Optionally, for peer
parity with the ETF/stock entries, broad sanity ranges could be added (a design
choice for the reviewer), derived from the existing convention's breadth, not
market timing; the minimal seam does not require them.

### 4.4 Live fetch verification (2026-08-22, `fast_info` attribute path)

- **UCO**: previous_close 44.97, last_price 45.55 -> pct +1.29%.
- **GOOG**: previous_close 338.18, last_price 341.75 -> pct +1.05%.
- Control SPY: 762.86 / 765.72 (network confirmed live). Both symbols resolve on
  the exact `ticker.fast_info.previous_close` / `.last_price` path
  (`ingestion.py:352-361`); the unchanged formula applies. (Transient values;
  what is pinned is that BOTH symbols return valid finite prices via the existing
  path — not these specific numbers.)

---

## 5. Design (sidecar + renderer; carried from v0.3, F1-F6-resolved)

### 5.1 Sidecar contract (`watchlist_sidecar.py`)
Add three additive fields per row; bump `schema_version` 1 -> 2:
- `daily_change_pct` = `round(pct_change_decimal*100, 1)` or `null` (n/a hook, R1').
- `primary_group` = registry `primary_group` passthrough (grouping, R2).
- `registry_index` = int registry position (ex-F2: recovers R2 order despite the
  writer's `sort_keys=True`).

**Reader acceptance contract (ex-F4, D-7 resolved as a justified recommendation):**
the renderer requires `primary_group`+`registry_index`+`daily_change_pct` (absent
in v1) -> bump to `schema_version` 2; the renderer accepts iff `source ==
"watchlist"` AND `schema_version == 2` AND every row is well-formed
(`primary_group` in the 5 known groups, `registry_index` int, `daily_change_pct`
float-or-null); else artifact UNUSABLE -> suppress (R5). Same-run write+render
means no stale-v1 window. (PRD recommendation, subject to PRD review.)

### 5.2 Renderer block (`dashboard_renderer.py`, optional `movement_card.py`)
Read + acceptance-validate the artifact; suppress on any failure (R5, ex-F1/F5).
Render all present rows grouped by the fixed constant order INDEX, METALS,
ENERGY, TECH, HIGH_BETA, sorted within group by `registry_index` (never on-disk
alphabetical order). Chips `SYM +X.X%` (honest zero `0.0%`) / `SYM n/a` (null,
never omitted, never `0.0`). Footer `captured HH:MM ET` from `generated_at`. The
renderer never imports the registry; full-12 population is guaranteed by the
producer (asserted by M6). Helper `movement_card.py` proposed (R6/D-5), "clearer/
testable" judged separately from "smaller".

---

## 6. Seam trace (fetch -> artifact -> renderer -> publish; ex-F1 corrected)

```
config.ALL_SYMBOLS (now incl. OBSERVE_ONLY = UCO, GOOG)
  -> ingestion fetch loop (no code change)              [ingestion.py:78; fast_info :352-361]
  -> normalize_all -> normalized_quotes (ALL)           [runtime/__init__.py:550]
       (validate_quotes -> valid_quotes @ :552; sidecar fed normalized_quotes, §3.5)
       (UCO/GOOG in NON_TRADABLE -> non-tradable, breadth-excluded, §4.2)
  -> pct_change_decimal                                 [normalization.py:29; fail-loud ingestion.py:369]
  -> hourly notify, non-halt                            [runtime/__init__.py:784, generated_at=run_at_utc]
       -> _write_watchlist_snapshot (atomic, sort_keys) [:2507; :2517-2519]
            -> build_watchlist_snapshot                 [watchlist_sidecar.py:61]
                 (ADD daily_change_pct + primary_group + registry_index; schema_version->2)
            -> logs/watchlist_snapshot.json             [gitignored :49]
  -> dashboard_renderer validate + read                 <-- FIRST machine reader
       -> MARKET MOVEMENT block (12/12, grouped)         <-- slice (optional movement_card.py)
  --- production publish (hourly workflow ONLY; ex-F1) ---
  -> renderer default reports/output/dashboard.html (dev)   [dashboard_renderer.py:58]
  -> hourly_alert.yml --output ui/dashboard.html -> ui/index.html -> readiness
       -> commit/push ui/ to publish branch (PRD-194)      [hourly_alert.yml:152-216]
  -> pages.yml deploys ui/ from publish                     [pages.yml:30-38]
```

---

## 7. Schema / persistence classification
Additive row keys + the artifact's own `schema_version`->2 (§5.1); NOT
`PAYLOAD_SCHEMA_VERSION`; no required-key change, no persisted/published surface,
no decision contract. Publish/last-writer per R3 (block present after hourly,
absent after daily). An artifact-hygiene guard pins not-restored/not-staged/
gitignored (§8). The `config.py` change adds fetched symbols but is proven
decision-invariant (§4.2).

---

## 8. FILES cone (ESTIMATED SURFACE — NOT YET APPROVED; expanded for 12/12)

| Op | File | Purpose |
|---|---|---|
| M | `cuttingboard/config.py` | add `OBSERVE_ONLY`; extend `ALL_SYMBOLS`; extend `NON_TRADABLE_SYMBOLS` to fence UCO/GOOG |
| M | `cuttingboard/watchlist_sidecar.py` | `daily_change_pct` + `primary_group` + `registry_index`; `schema_version`->2 |
| M | `cuttingboard/delivery/dashboard_renderer.py` | MARKET MOVEMENT block: acceptance-validate + full-12 grouped render + R5 suppression |
| A (design choice, R6) | `cuttingboard/delivery/movement_card.py` | small pure validator/block-builder (mirrors `gex_card.py`) |
| M | `tests/test_phase1.py` | `len(ALL_SYMBOLS)` count 23 -> 25 |
| M | `tests/test_config.py` | UCO/GOOG in `ALL_SYMBOLS` + in `NON_TRADABLE_SYMBOLS`; non-tradable + breadth-invariance guard |
| M | `tests/test_watchlist_sidecar.py` | new fields, scale, null-preserved, group + registry_index, `schema_version`->2, full-12 population incl. UCO/GOOG |
| M | `tests/test_dashboard_renderer.py` | 12/12 presence, n/a vs honest-zero, group order via registry_index against the sort_keys artifact, acceptance/version/source, R5 suppression (absent + each invalid class), captured-clock |
| M | `tests/test_ci_artifact_hygiene.py` | artifact stays not-restored/not-staged/gitignored |
| M | `docs/SCHEMA_MAP.md` | watchlist row schema truth (new fields, schema_version 2) |
| M | `docs/artifact_flow_map.md` | add renderer as reader; correct `11-tuple`->`12-tuple` (O-1) |
| M | `docs/PRD_REGISTRY.md`, `docs/prd_index.json`, `docs/PROJECT_STATE.md` | Stage-0 bookkeeping |
| M | `docs/plans/decision-support-workplan-v0.1.md` | ledger row |
| A | `docs/prd_history/PRD-NNN.md` | Stage-0 PRD scaffold |

**Verified-unaffected, NOT edited (in the blast radius, no code change):**
`ingestion.py` (iterates `ALL_SYMBOLS`, fetches UCO/GOOG with no edit),
`regime.py` / `universe.py` / `trade_decision.py` (read `NON_TRADABLE`; invariant),
`normalization.py` / `validation.py` (UCO/GOOG use existing paths; no PRICE_BOUNDS),
`contract.py` (macro keys on `MACRO_DRIVERS`), `tests/test_expansion_regime.py`
(denominator stays 16 -> green; a standing guard). Touching a decision surface
(making UCO/GOOG tradable, or a valid_quotes/age change) is a §12 stop-and-amend.

---

## 9. Estimated production LOC ceiling (ESTIMATED SURFACE — NOT YET APPROVED)

- **~125-165 net production LOC; provisional ceiling <=200.** `config.py` ~4;
  sidecar ~15; renderer + acceptance + grouping/ordering + 12/12/n-a ~105-145
  (helper split neutral). Test LOC ~200 (adds membership/non-tradable/breadth-
  invariance guards + the fetch/n-a cases).
- **Tripwire:** any production file beyond §8, any runtime write change, any
  decision-surface change (tradable/breadth/leadership/valid_quotes/age), any
  `PAYLOAD_SCHEMA_VERSION`/required-key change -> §12.

---

## 10. Discriminating test / mutation matrix (G1 fixed; 12/12 + observe-only guards)

| # | Case | Asserted (exact) | Mut? |
|---|---|---|---|
| M1 | Scale | `daily_change_pct == round(pct_change_decimal*100, 1)` | **YES** — raw decimal reddens |
| M2 | Null preserved | missing quote -> `daily_change_pct is None`, never `0.0` | **YES** — coercion reddens |
| M3 | Honest zero vs n/a | live `0.0` -> `0.0%`; null -> `n/a`; never collapse | **YES** |
| M4 | Group passthrough | row `primary_group` is the fine registry group | **YES** |
| M5 | registry_index passthrough | == `UNIVERSE_REGISTRY` position | **YES** |
| M6 | Full-12 population (producer) | writer emits all 12 enabled registry rows incl. UCO/GOOG | **YES** |
| M7 | Order vs sort_keys artifact | given alphabetized on-disk artifact, rendered order = `(GROUP_ORDER, registry_index)`; TSLA under HIGH_BETA | **YES** |
| M8 | Suppress: absent | no artifact -> whole output byte-equal to no-block baseline | **YES** |
| M9 | Suppress: each invalid class | {malformed JSON, missing `symbols`, wrong types, `schema_version!=2`, `source!="watchlist"`} -> byte-equal baseline | **YES** |
| M10 | Captured clock | footer `captured HH:MM ET` from `generated_at`; literal "captured" | **YES** |
| M11 | Malformed/naive generated_at | -> artifact unusable -> block suppressed (single outcome). **NO "future" case** — the block holds no clock (§12 #6), so future-detection is out of scope (G1 fix) | **YES** |
| M12 | Unknown primary_group | row group outside the 5 -> artifact unusable -> suppressed | **YES** |
| M13 | Cadence / call-site | `_write_watchlist_snapshot` invoked from the hourly site only, NOT the daily block | **YES** |
| M14 | UCO/GOOG fetched + live | with UCO/GOOG in `ALL_SYMBOLS`, a successful-fetch fixture -> both carry real `daily_change_pct` and render live | **YES** — dropping them from the fetch universe reddens |
| M15 | Transient failure -> n/a | UCO (or any symbol) fetch/validation failure on a run -> that row `n/a`, others unaffected, no halt | **YES** — halting or fabricating `0.0` reddens |
| M16 | Observe-only: non-tradable | `is_tradable_symbol("UCO")` and `("GOOG")` are False; `is_actionable_trade` false | **YES** — removing them from `NON_TRADABLE` reddens |
| M17 | Observe-only: breadth invariant | EXPANSION breadth denominator stays 16 with OBSERVE_ONLY added (`tests/test_expansion_regime.py` stays green) | **YES** — adding them as tradable reddens the existing :221 assertion |
| M18 | Fail-loud upstream | invalid `previous_close` still raises (PRD-262); no fabricated `0.0` (documents the guarantee) | |

Whole-output baselines for absent/invalid; no golden byte-diff for presence. A
guard whose mutation stays green does not merge (PRD-198 inv. 4).

---

## 11. Unavailable / failure semantics
Artifact absent OR invalid -> whole block suppressed (R5). Individual symbol null
(transient fetch/validation failure, incl. a bad UCO/GOOG fetch) -> `n/a`, row
retained (R1'), never `0.0`. Honest zero -> `0.0%`. Bad `previous_close` -> fail
loud upstream (`ingestion.py:369`) -> null path. UCO/GOOG are non-halt-critical
(not in REQUIRED/HALT), so their failure never halts the run.

---

## 12. Stop-and-amend conditions (hard stops — return to Dustin, re-run GOV-2 §1)

1. Making UCO/GOOG (or any OBSERVE_ONLY symbol) TRADABLE — i.e. any change that
   removes them from `NON_TRADABLE_SYMBOLS` or otherwise lets them into the
   tradable universe, breadth, leadership, candidacy, qualification, ranking, or
   notification (violates R8).
2. Adding UCO/GOOG to `MACRO_DRIVERS`, `REQUIRED_SYMBOLS`, or `HALT_SYMBOLS`.
3. Any change to `runtime/__init__.py` (write-cadence change is slice 2).
4. Any `PAYLOAD_SCHEMA_VERSION` bump / `assert_valid_payload` required-key add.
5. Any NEW durable/published persistence surface; any `git add -f` of the artifact.
6. Renderer-side derivation/recomputation of any movement value.
7. Any `datetime.now()` in the block (freshness keyed on `generated_at`).
8. Any conversion of null/missing movement to `0.0` (R1').
9. Any valid_quotes restriction or quote-age gate for the sidecars (the deferred
   §3.5/§15 owner question) — a runtime change.
10. Any change to the publish workflows.
11. Exceeding §8 files or the §9 ceiling without a fresh GOV-2 §1 pass.
12. Any scoring/ranking/permission/bullish-bearish/relative-strength logic.

---

## 13. Materiality / lane classification
**MATERIAL** (expanded: fetch universe + carrier + delivery + dashboard; §2). The
fetch expansion is proven decision-invariant (§4.2). **Lane: HIGH-RISK**, forced
by `dashboard_renderer.py` (CONSUMER HIGH-RISK; PRD-121 R11). MICRO-ineligible.
After review-clean + design-direction ruling: Stage-0 PRD -> independent PRD
review -> Gate A. Governance hold: decision-support/personalized-news track;
landing PR DRAFT + self-named (GOV-0/PRD-186), held for Dustin.

---

## 14. What gets CUT
- Any trade eligibility / regime / leadership / qualification / risk /
  notification / ranking / permission change from adding UCO/GOOG (R8; the seam
  proves none occurs).
- Adding UCO/GOOG to `COMMODITIES`/`HIGH_BETA`/`MACRO_DRIVERS` (would change
  tradability/macro semantics) — `OBSERVE_ONLY` instead.
- Inventing PRICE_BOUNDS numbers (omitted; optional, §4.3).
- valid_quotes restriction / per-symbol age gate (deferred owner question, §15).
- Scoring/ranking/prediction/second board/new cadence/relative-strength.
- Daily watchlist write (slice 2, deferred; `git add -f` publish side effect).

---

## 15. Open design/review questions
- **D-5 Helper extraction (R6):** `movement_card.py` vs inline (Codex may challenge).
- **D-7 Versioning (R7) — resolved recommendation:** `schema_version`->2, reader
  accepts source==watchlist AND version==2, else suppress (§5.1). PRD-level, not
  owner.
- **PRICE_BOUNDS for UCO/GOOG:** recommend OMIT (non-tradable/macro precedent);
  optional broad peer-parity bounds are a reviewer design choice (§4.3).
- **Q-Freshness/Admission (unresolved OWNER question):** should a future slice
  restrict the sidecars to `valid_quotes` and/or bound per-symbol quote age?
  Non-blocking for slice 1 (display-parity + trend_structure precedent, invents
  no gate); a runtime scope expansion for Dustin to rule (§3.1, §3.5).

---

## 16. Author self-verification record (GOV-2 §3)

All against `main` @ `80ac6eb`, re-run by the authoring agent (not delegated;
CLAUDE.md Author-discipline 4). Fetch-seam facts [BR]:

- [BR] `ALL_SYMBOLS` consumers: `ingestion.py:78` (fetch), `regime.py:114`
  (breadth total), `runtime:2435` (DEAD — no prod caller, grep confirmed). No
  other production reader. CONFIRMED.
- [BR] `NON_TRADABLE_SYMBOLS` consumers: `regime.py:112/114`, `trade_decision.py:113`,
  `universe.py:11` — all exclude-role; none treats it as "macro driver". Macro
  code keys on `MACRO_DRIVERS`/`_OPTIONAL_MACRO_DRIVERS` (`contract.py:539`,
  `contract_types.py:45`). CONFIRMED.
- [BR] `COMMODITIES`/`HIGH_BETA`/`INDICES` each have one production reader (the
  `ALL_SYMBOLS` concat); no semantic role. CONFIRMED.
- [BR] Tradability = `not in NON_TRADABLE` (+`^`-reject) (`universe.py:11`,
  `trade_decision.py:113`); OBSERVE_ONLY in NON_TRADABLE -> non-tradable.
  CONFIRMED.
- [BR] Breadth denominator `= sum(ALL_SYMBOLS not in NON_TRADABLE)` = 16 today;
  with OBSERVE_ONLY in both, stays 16; `tests/test_expansion_regime.py:208/221`
  assert "denominator must stay the configured 16". CONFIRMED.
- [BR] `EXPANSION_LEADERSHIP_SYMBOLS` separate (`regime.py:120`); UCO/GOOG absent.
  REQUIRED_SYMBOLS/HALT_SYMBOLS exclude UCO/GOOG. CONFIRMED.
- [BR] `PRICE_BOUNDS` optional (`validation.py:204` guarded); macro drivers fetch
  without bounds. `SYMBOL_SOURCE_PRIORITY.get(..., default)` (`ingestion.py:93`).
  CONFIRMED.
- [BR] `len(config.ALL_SYMBOLS) == 23` (`test_phase1.py:80`) -> 25 after the add
  (only hard count). CONFIRMED.
- [BR] Live yfinance `fast_info`: UCO 44.97/45.55, GOOG 338.18/341.75, SPY control
  762.86/765.72 — both resolve via `ticker.fast_info.previous_close/.last_price`.
  CONFIRMED (2026-08-22).
- Carrier/movement/freshness/admission facts as v0.3 §16 (passthrough drop,
  pct_change source, sort_keys, cadence, publish, zero-reader, 12 enabled
  registry symbols). CONFIRMED.

Author self-verification is NOT independent review. A FRESH Event-1 on the
expanded boundary is commissioned (§17).

---

## 17. Packet review records (GOV-2 §2, §7)

### FRESH INITIAL PACKET REVIEW (Event-1 on the 12/12 boundary) — PENDING
| Field | Value |
|---|---|
| Event type | `INITIAL PACKET REVIEW` (owner-commissioned on the expanded boundary) |
| Reviewer | independent Codex, fresh context, read-only (`codex exec -s read-only`) |
| Reviewed SHA | PENDING (v0.4 committed head) |
| Verdict / findings / dispositions | PENDING |

### EXACT-CORRECTED-HEAD CONFIRMATION (Event-2 on 12/12) — PENDING

### Historical records (10/12 boundary — evidence only, do NOT certify 12/12)
- `NS4B_EVENT1_CODEX_REVIEW_2026-08-22.md`: Event-1 on v0.2 @ `6e5f176`, FINDINGS
  F1-F6; T-2/T-3/T-5/T-8/zero-reader/O-1 CONFIRMED.
- `NS4B_EVENT2_CODEX_CONFIRMATION_2026-08-22.md`: Event-2 on v0.3 @ `5d21923`,
  F1-F6 RESOLVED, NOT CLEAN on G1 (M11 future-timestamp). G1 is FIXED in v0.4
  (§10 M11: no future case; no clock introduced).

### Carried-forward resolutions (from the v0.2->v0.3 consolidated correction)
F1 publish seam (§6), F2 registry_index/order (§5.1), F3 admission seam (§3.5),
F4 acceptance contract (§5.1), F5 killable mutations (§10), F6 FILES/LOC+hygiene
(§8/§9). All remain in v0.4; the FRESH Event-1 re-reviews them within the
expanded boundary.

### Out-of-scope observation
- **O-1** `artifact_flow_map.md:122` "11-tuple" vs live 12-tuple — slice corrects.

---

## 18. Pre-review revision log
- **v0.4 (2026-08-22):** MATERIAL boundary reset to 12/12. Added the `OBSERVE_ONLY`
  fetch seam (§4.1), the downstream impact inventory + no-decision-authority proof
  (§4.2), the PRICE_BOUNDS decision (§4.3), live UCO/GOOG fetch verification
  (§4.4), mutations M14-M17 (fetch/transient-n/a/non-tradable/breadth-invariance);
  fixed G1 (M11 drops the future case, no clock introduced); expanded FILES
  (config.py, test_phase1, test_config) and LOC. Carried F1-F6 forward.
  Supersedes v0.3.
- **v0.3 (2026-08-22):** consolidated correction of Event-1 F1-F6 (10/12); Event-2
  NOT CLEAN on G1.
- **v0.2 (2026-08-22):** owner alignment (R1-R5); reviewed by Event-1 @ `6e5f176`.
- **v0.1 (2026-08-22):** initial provisional packet.

---

END OF PACKET v0.4 — PROVISIONAL / NOT REVIEW-CLEAN — NO IMPLEMENTATION
AUTHORITY. A FRESH Codex Event-1 against the expanded 12/12 boundary is
owner-commissioned on this revision's committed head. Gate A is neither requested
nor granted.
