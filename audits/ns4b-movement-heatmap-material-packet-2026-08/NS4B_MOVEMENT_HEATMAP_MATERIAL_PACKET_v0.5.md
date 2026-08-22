# NS-4B — Market Movement Heatmap (12/12, observe-only fetch) — MATERIAL PACKET (v0.5, PROVISIONAL, REPLACEMENT)

**Status: REVIEW-CLEAN — NO IMPLEMENTATION AUTHORITY — HELD FOR DUSTIN'S
DESIGN-DIRECTION RULING.**
v0.5 is the single consolidated author correction (GOV-2 §2 step 4) of the v0.4
fresh Event-1 findings F1-F7 + G1, resolved against Dustin's 2026-08-22 ruling
("12/12, keep it simple; Option A as the smallest observation-only fetch seam").
Codex Event-2 (`NS4B_V05_EVENT2_CODEX_CONFIRMATION_2026-08-22.md`, reviewed SHA
`2789dda`) confirmed **F1-F7 + G1 all RESOLVED, NEW BLOCKING: NONE — VERDICT
CLEAN**. The GOV-2 packet cycle is COMPLETE and the packet is REVIEW-CLEAN.
No implementation authority (GOV-2 §4); all FILES/LOC are `ESTIMATED SURFACE —
NOT YET APPROVED` (GOV-2 §5). Next governed steps (GOV-2 §2/§4): Dustin's
design-direction ruling -> Stage-0 PRD -> independent PRD review -> Gate A.

**Code baseline `main` @ `80ac6eb`.** Correction facts verified (§16, CORRECTION
CYCLE). Live yfinance confirmed UCO/GOOG fetch via the existing path (§4.4).

---

## 0. GOV-2 order

```
MATERIAL boundary reset to 12/12 (owner) .............. DONE
bounded fetch-impact trace ............................ DONE (v0.4 §4; §16)
fresh Event-1 on 12/12 (v0.4 @ 5d51f94) ............... DONE (FINDINGS F1-F7; G1 confirmed fixed)
owner design ruling (Option A, smallest seam) ......... DONE (2026-08-22)
consolidated correction (F1-F7 + G1) .................. DONE (this v0.5 doc)   <-- HERE
exact-corrected-head confirmation (Event-2) ........... PENDING (on v0.5 head)
Dustin design-direction ruling ....................... PENDING
Stage-0 PRD -> independent PRD review -> Gate A ....... PENDING
```

MICRO-ineligible (MATERIAL); rides **HIGH-RISK** (`dashboard_renderer.py`).

---

## 0.1 Owner rulings governing v0.5 (Dustin, 2026-08-22)

- **F1 -> Option A, SMALLEST observe-only fetch seam.** UCO/GOOG go through the
  existing yfinance fetch + normalization and are merged only into the mapping the
  watchlist sidecar consumes. They MUST NOT enter structure, regime, qualification,
  candidate generation, trade counts, ranking, or permission. No provider
  abstraction, universe engine, scheduler, ingestion subsystem, or broad refactor.
- **F2 -> no validation-carrier redesign.** Preserve existing watchlist-sidecar
  admission semantics. Honest contract: fetch/normalization failure -> `n/a`;
  honest zero -> `0.0%`; validation-invalid behavior remains whatever the existing
  `normalized_quotes` sidecar does. The false "every validation failure -> n/a"
  claim is removed. Validation-aware admission is recorded as separate future debt
  only (§15).
- **F7 -> NS-4A registry `trade_eligible=True` unchanged** (not runtime authority;
  this slice does not redefine it).
- **G1 -> keep the future-`generated_at` suppression removed** (no reference clock
  exists in the design); malformed/naive handling stays clock-free.
- **12/12 contract:** all 12 registry symbols appear; UCO/GOOG normally fetched via
  the existing free yfinance path; transient missing -> `n/a`; honest zero ->
  `0.0%`; never omit a registry symbol; never fabricate zero. No new provider,
  credential, or paid data.
- Carried R2-R5 (group order; hourly last-writer; captured freshness; absent/invalid
  suppression); open R6 (helper) / R7 (versioning, resolved recommendation).

---

## 1. Product question and outcome

A read-only **MARKET MOVEMENT** block: all 12 registry symbols grouped by primary
group, each with its move off the prior session close; 12/12 normally live.
UCO/GOOG are fetched observation-only (§4). Transient missing (fetch/normalization
failure) -> `SYM n/a`; honest zero -> `0.0%`; null never fabricated as `0.0`;
never omitted. Movement basis: `pct_change_decimal` x100 (PRD-199; Event-1 T-3).
Fixed group order (R2); `captured HH:MM ET` footer (R4).

---

## 2. Intake classification (GOV-2 §1)

**MATERIAL: YES.** Carrier trigger (`watchlist_snapshot.json` first machine
reader) + a small runtime observe-only fetch/merge. The seam is NARROWER than
v0.4: it does NOT modify `ALL_SYMBOLS`, `COMMODITIES`, `HIGH_BETA`, or
`NON_TRADABLE_SYMBOLS`, so no decision-universe constant changes (F1 resolved
structurally, §4.2). Crosses ingestion (a tiny separate fetch), delivery, and
dashboard. Lane HIGH-RISK forced by `dashboard_renderer.py` (§13).

---

## 3. Verified current state
(As v0.4 §3, unchanged: `pct_change_decimal` `normalization.py:29`; fail-loud
`ingestion.py:369`; `fetched_at_utc` fetch-clock `:112/295`; carrier
`watchlist_sidecar.py:61`, `current_price=quote.price` `:71`; writer
`sort_keys=True` `runtime/__init__.py:2517`; hourly write `:784`, daily none;
gitignored `.gitignore:49`; zero machine readers; 12 enabled registry symbols.)

### 3.5 Admission seam (F2, honest)
The main 10 symbols reach the sidecar via `normalized_quotes` (`:784`), which is
`normalize_all(fetch_all())` BEFORE `validate_quotes` — so the sidecar renders
NORMALIZED values without re-validation, exactly as the existing watchlist price
display already does. A symbol that fails validation is removed from
`valid_quotes` but REMAINS in `normalized_quotes`, so it still renders movement,
NOT `n/a` (v0.4's "validation failure -> n/a" was false; removed). Only a
fetch/normalization failure (absent from the mapping) yields `n/a`. Making the
sidecar validation-aware (feeding `valid_quotes`, or a validity flag) is a
runtime scope change recorded as future debt (§15), NOT solved here (owner F2).

---

## 4. The smallest observe-only fetch seam (owner Option A)

### 4.1 Design

```python
# config.py — a separate observation-only set; NOT in ALL_SYMBOLS / NON_TRADABLE
OBSERVE_ONLY_SYMBOLS: tuple[str, ...] = ("UCO", "GOOG")
```

```python
# ingestion.py — tiny helper, reuses the existing per-symbol fetch + normalize
def fetch_observe_only_quotes() -> dict[str, NormalizedQuote]:
    out = {}
    for sym in config.OBSERVE_ONLY_SYMBOLS:
        try:
            nq = normalize_quote(fetch_quote(sym))   # existing fetch_quote:87 + normalize_quote:61
            if nq is not None:
                out[sym] = nq
        except Exception:
            continue   # best-effort: a failure -> symbol absent -> n/a (never halts)
    return out
```

```python
# runtime/__init__.py — merge ONLY at the hourly watchlist write site (:784)
_write_watchlist_snapshot(
    normalized_quotes={**normalized_quotes, **fetch_observe_only_quotes()},
    generated_at=run_at_utc,
)
```

- `OBSERVE_ONLY_SYMBOLS` is a wholly separate constant, **disjoint from
  `ALL_SYMBOLS`**. It is never iterated by the ingestion universe loop
  (`ingestion.py:78`), never enters `normalize_all(fetch_all())` ->
  `normalized_quotes` -> `validate_quotes` -> `valid_quotes`.
- The observe-only quotes are merged into a NEW local mapping passed ONLY to
  `_write_watchlist_snapshot`; the `normalized_quotes` variable that feeds the
  decision pipeline is unchanged.
- Best-effort fetch: a UCO/GOOG failure omits the symbol -> `n/a` (R1'); never
  halts (they are not HALT/REQUIRED symbols and are outside validate_quotes).
- No provider abstraction / universe engine / scheduler (owner F1). `fetch_quote`
  routes via `SYMBOL_SOURCE_PRIORITY.get(sym, default=["yfinance"])`
  (`ingestion.py:93`) — no entry needed.

### 4.2 Structural isolation proof (F1 / R8)

The decision pipeline is keyed EXCLUSIVELY on `ALL_SYMBOLS` (the ingestion loop,
`ingestion.py:78`) and `valid_quotes` (a subset of
`normalize_all(fetch_all())`). Because `OBSERVE_ONLY_SYMBOLS ∩ ALL_SYMBOLS = ∅`
and the observe-only quotes are merged only into the sidecar's local mapping —
DOWNSTREAM of, and disjoint from, `normalized_quotes` — UCO/GOOG can never reach:

| Surface | Keyed on | Reaches UCO/GOOG? |
|---|---|---|
| ingestion universe loop | `ALL_SYMBOLS` | NO (disjoint) |
| `validate_quotes` / `valid_quotes` | `normalize_all(fetch_all())` | NO |
| `compute_all_derived` / `classify_all_structure` | `valid_quotes` | NO |
| `generate_candidates` / `qualify_all` (`qualification.py:191`) | structure/candidates from `valid_quotes` | NO |
| regime breadth / leadership (`regime.py:112-120`) | `ALL_SYMBOLS` / `valid_quotes` / hardcoded lists | NO |
| notifications / counts (`symbols_qualified`) | qualification over `valid_quotes` | NO |
| `is_tradable_symbol` / `is_actionable_trade` | never called on observe-only (they reach no candidate/notification path) | N/A |

This is a membership-by-construction proof, not an empirical one. Guard test:
`assert set(OBSERVE_ONLY_SYMBOLS).isdisjoint(config.ALL_SYMBOLS)` (M17) plus a
runtime test that the `validate_quotes` input excludes OBSERVE_ONLY symbols while
the watchlist mapping includes them (M18). No trade eligibility, regime,
leadership, qualification, count, ranking, or permission change (owner R8).

### 4.3 Universe-taxonomy + bounds/source (F4)

`OBSERVE_ONLY_SYMBOLS` is NOT in `ALL_SYMBOLS`, so the `docs/universe_taxonomy.md`
`ALL_SYMBOLS` mutation rule (update source priority + validation bounds) does not
apply. The slice ADDS a new taxonomy entry documenting the OBSERVE_ONLY universe
(purpose: observation-only movement display; ownership: `config.OBSERVE_ONLY_SYMBOLS`;
consumers: the watchlist sidecar via the runtime merge ONLY; mutation boundary:
never add to `ALL_SYMBOLS`/`NON_TRADABLE_SYMBOLS`/decision paths). `PRICE_BOUNDS`
is not applicable (observe-only quotes bypass `validate_quotes`, where the bound
is checked); `SYMBOL_SOURCE_PRIORITY` uses the default entry — no per-symbol edit.
(Pre-existing drift noted, not fixed here: the taxonomy doc lists 4 macro drivers
vs 7 in code.)

### 4.4 Live fetch verification (2026-08-22)
UCO 44.97/45.55 (+1.29%), GOOG 338.18/341.75 (+1.05%), SPY control 762.86/765.72,
via `ticker.fast_info.previous_close/.last_price` (`ingestion.py:352-361`) — the
exact path `fetch_quote` uses. Both resolve; unchanged formula.

---

## 5. Design (sidecar + renderer; carried, F2/F4/F5/F6 resolved)

### 5.1 Sidecar contract (`watchlist_sidecar.py`)
Add per row (additive): `daily_change_pct` = `round(pct_change_decimal*100,1)` or
`null` (n/a hook); `primary_group` passthrough; `registry_index` int
(recovers R2 order despite `sort_keys=True`). Bump `schema_version` 1 -> 2.

**Reader acceptance contract (F4/F6 tightened).** The renderer accepts iff
`source == "watchlist"` AND `schema_version == 2` AND the `symbols` object
contains EXACTLY the 12 enabled registry symbols (full-12 identity, F6) with
every row well-formed: `symbol` (str, matching its key), `primary_group` in the 5
known groups, `registry_index` a unique int in range, `daily_change_pct`
float-or-null. Missing/extra/mismatched symbol, duplicate/out-of-range
`registry_index`, wrong version/source, or malformed row -> artifact UNUSABLE ->
suppress (R5). Producer guarantees the full-12 population; the acceptance check
enforces R1' (never silently omit).

### 5.2 Renderer block
Read + acceptance-validate; suppress on any failure (R5). Render all 12 rows
grouped by fixed order INDEX, METALS, ENERGY, TECH, HIGH_BETA, sorted within group
by `registry_index`. Chips `SYM +X.X%` (honest zero `0.0%`) / `SYM n/a`. Footer
`captured HH:MM ET` from `generated_at`. Renderer never imports the registry.
Helper `movement_card.py` proposed (R6, design choice).

---

## 6. Seam trace

```
--- observe-only fetch (owner Option A; disjoint from the decision pipeline) ---
config.OBSERVE_ONLY_SYMBOLS = (UCO, GOOG)   (NOT in ALL_SYMBOLS)
  -> fetch_observe_only_quotes() [ingestion: fetch_quote:87 + normalize_quote:61, best-effort]
       -> {UCO,GOOG: NormalizedQuote}   (never enters normalized_quotes/validate_quotes)
--- main universe (unchanged) ---
config.ALL_SYMBOLS -> fetch_all -> normalize_all -> normalized_quotes -> validate_quotes -> decision pipeline
--- merge only at the watchlist write ---
runtime:784 _write_watchlist_snapshot(normalized_quotes={**normalized_quotes, **observe_only})
  -> build_watchlist_snapshot (ADD daily_change_pct + primary_group + registry_index; schema_version 2) [watchlist_sidecar.py:61]
  -> logs/watchlist_snapshot.json (atomic, sort_keys, gitignored)
  -> dashboard_renderer validate + read -> MARKET MOVEMENT block (12/12, grouped)
  --- publish (hourly workflow only, ex-F1) ---
  -> --output ui/dashboard.html -> ui/index.html -> readiness -> publish branch -> Pages
     [dashboard_renderer.py:58 default; hourly_alert.yml:152-216; pages.yml:30-38]
```

---

## 7. Schema / persistence
Additive row keys + artifact `schema_version` 2; no `PAYLOAD_SCHEMA_VERSION`
change, no persisted/published file, no decision contract. Hygiene guard pins
not-restored/not-staged/gitignored. Publish/last-writer per R3.

---

## 8. FILES cone (ESTIMATED SURFACE — NOT YET APPROVED; smallest Option A)

| Op | File | Purpose |
|---|---|---|
| M | `cuttingboard/config.py` | add `OBSERVE_ONLY_SYMBOLS` (separate; NOT in ALL_SYMBOLS/NON_TRADABLE) |
| M | `cuttingboard/ingestion.py` | `fetch_observe_only_quotes()` best-effort helper (reuses `fetch_quote`+`normalize_quote`) |
| M | `cuttingboard/runtime/__init__.py` | fetch observe-only + merge ONLY into the watchlist write mapping (`:784`) |
| M | `cuttingboard/watchlist_sidecar.py` | `daily_change_pct` + `primary_group` + `registry_index`; `schema_version`->2 |
| M | `cuttingboard/delivery/dashboard_renderer.py` | MARKET MOVEMENT block: acceptance-validate + 12/12 grouped render + R5 suppression |
| A (design choice, R6) | `cuttingboard/delivery/movement_card.py` | small pure validator/block-builder |
| M | `tests/test_ingestion.py` | observe-only fetch: UCO/GOOG fetched, best-effort failure -> absent; disjoint from ALL_SYMBOLS |
| A | `tests/test_observe_only_isolation.py` | isolation guard: OBSERVE_ONLY absent from `validate_quotes` input; present in the watchlist mapping (M17/M18) |
| M | `tests/test_watchlist_sidecar.py` | fields, scale, null, group, registry_index, schema_version 2, full-12 |
| M | `tests/test_dashboard_renderer.py` | 12/12 presence, n/a vs honest-zero, order vs sort_keys, acceptance/identity, R5 suppression, captured-clock |
| M | `tests/test_ci_artifact_hygiene.py` | artifact stays not-restored/not-staged/gitignored |
| M | `docs/SCHEMA_MAP.md` | watchlist row schema (new fields, version 2) |
| M | `docs/artifact_flow_map.md` | renderer as reader; `11-tuple`->`12-tuple` (O-1) |
| M | `docs/universe_taxonomy.md` | add the OBSERVE_ONLY universe entry (F4) |
| M | `docs/PRD_REGISTRY.md`, `docs/prd_index.json`, `docs/PROJECT_STATE.md` | Stage-0 bookkeeping |
| M | `docs/plans/decision-support-workplan-v0.1.md` | ledger row |
| A | `docs/prd_history/PRD-NNN.md` | Stage-0 PRD scaffold |

**Verified-UNAFFECTED, NOT edited (F5 disposition — the seam changes NO decision
universe):** `config.ALL_SYMBOLS`/`COMMODITIES`/`HIGH_BETA`/`NON_TRADABLE_SYMBOLS`
(untouched); `regime.py`, `universe.py`, `trade_decision.py`, `qualification.py`,
`validation.py` (observe-only never reaches them). The six Codex-flagged F5 files
and the count test assert those unchanged constants and stay green with NO edit:
`tests/test_phase1.py:80` (`len(ALL_SYMBOLS)==23`, unchanged),
`tests/test_config.py`, `tests/test_contract_macro_drivers.py:94-96`,
`tests/test_prd161_sizing_gate_fixture.py:244-248`,
`tests/test_prd162_reconciliation.py:124-141`,
`tests/test_runtime_decision.py:246-252`, `tests/test_trade_decision.py:242-259`,
`tests/test_trend_structure.py:429-438`, `tests/test_expansion_regime.py`.

---

## 9. Estimated production LOC (ESTIMATED SURFACE — NOT YET APPROVED)

- **AMENDED CEILING (GOV-2 §5, Dustin amended Gate A 2026-08-22): <=240 net
  production LOC.** The Stage-0 estimate below understated the already-authorized
  `movement_card.py` full-12 acceptance validator + grouping + deterministic
  ordering + fragment (~160 LOC, sibling to gex_card's 200); actual implementation
  is ~223 net across the same five authorized files — an estimate correction, NOT
  scope expansion. Seam/FILES/observe-only isolation unchanged; `ingestion.py`
  untouched (the observe-only fetch is inline in runtime, so no ingestion.py
  helper was added). Consequence: exceeding ≤240, or any authorized-seam
  expansion, is a further stop-and-renew.
- Original Stage-0 estimate (superseded): **~145-185 net production LOC; ceiling
  <=220.** config ~2; ingestion helper ~15; runtime merge ~6; sidecar ~15;
  renderer + acceptance + grouping/ordering + 12/12/n-a ~105-145. Test LOC ~200.
- **Tripwire:** any change to `ALL_SYMBOLS`/`NON_TRADABLE`/a decision universe;
  any observe-only symbol reaching `validate_quotes`/qualification; any daily
  write; any `PAYLOAD_SCHEMA_VERSION`/required-key change -> §12.

---

## 10. Discriminating test / mutation matrix (F3/F5/F6 tightened; G1 fixed)

| # | Case | Asserted (exact) | Mut? |
|---|---|---|---|
| M1 | Scale | `daily_change_pct == round(pct_change_decimal*100,1)` | **YES** |
| M2 | Null preserved | missing quote -> `None`, never `0.0` | **YES** |
| M3 | Honest zero vs n/a | live `0.0` -> `0.0%`; null -> `n/a`; never collapse | **YES** |
| M4 | Group passthrough | fine registry `primary_group`, not `sector_theme` | **YES** |
| M5 | registry_index | == registry position | **YES** |
| M6 | Full-12 identity (acceptance) | artifact accepted iff exactly the 12 registry symbols present, unique in-range registry_index; missing/extra/duplicate -> UNUSABLE -> suppress | **YES** — omitting UCO/GOOG or a duplicate index reddens |
| M7 | Order vs sort_keys artifact | rendered order `(GROUP_ORDER, registry_index)`; TSLA under HIGH_BETA | **YES** |
| M8 | Suppress: absent | no artifact -> whole output byte-equal baseline | **YES** |
| M9 | Suppress: each invalid class | {malformed JSON, missing symbols, wrong types, schema_version!=2, source!=watchlist, full-12 violation} -> byte-equal baseline | **YES** |
| M10 | Captured clock | footer `captured HH:MM ET` from `generated_at` | **YES** |
| M11 | Malformed/naive generated_at | -> artifact unusable -> suppressed (single outcome). No "future" case; the block holds no clock (§12 #7) — G1 fixed | **YES** |
| M12 | Unknown primary_group | row group outside the 5 -> unusable -> suppressed | **YES** |
| M13 | Cadence / call-site | `_write_watchlist_snapshot` invoked from the hourly site only, not daily | **YES** |
| M14 | UCO/GOOG fetched + live | observe-only fetch success -> both carry real `daily_change_pct`, render live | **YES** — not fetching them reddens |
| M15 | Transient observe-only failure -> n/a | UCO fetch/normalization failure -> row `n/a`, others unaffected, no halt | **YES** — halting or fabricating `0.0` reddens |
| M16 | Observe-only does not halt | a UCO/GOOG fetch exception is swallowed best-effort; run completes | **YES** |
| M17 | Isolation: disjoint | `set(OBSERVE_ONLY_SYMBOLS).isdisjoint(ALL_SYMBOLS)` | **YES** — adding them to ALL_SYMBOLS reddens |
| M18 | Isolation: pipeline-blind | in a runtime test, `validate_quotes` input / `valid_quotes` excludes OBSERVE_ONLY while the watchlist mapping includes them | **YES** — routing observe-only into normalized_quotes reddens |
| M19 | Fail-loud upstream | invalid `previous_close` still raises (PRD-262) (documents guarantee) | |

Whole-output baselines for absent/invalid; no golden byte-diff for presence.
Guard-with-green-mutation does not merge (PRD-198 inv. 4).

---

## 11. Unavailable / failure semantics
Artifact absent OR invalid -> whole block suppressed (R5). Individual symbol null
(fetch/normalization failure, incl. a bad UCO/GOOG observe-only fetch) -> `n/a`,
row retained (R1'), never `0.0`. Honest zero -> `0.0%`. Validation-invalid main
symbols render their normalized movement (existing sidecar semantics, §3.5) —
NOT n/a; a validation-aware carrier is future debt (§15). UCO/GOOG never halt.

---

## 12. Stop-and-amend conditions
1. Adding `OBSERVE_ONLY_SYMBOLS` to `ALL_SYMBOLS`, `NON_TRADABLE_SYMBOLS`, or any
   decision/universe path; any observe-only symbol reaching `validate_quotes`/
   structure/regime/qualification/candidates/counts/ranking/permission (violates
   owner F1/R8).
2. Any change to `MACRO_DRIVERS`/`REQUIRED_SYMBOLS`/`HALT_SYMBOLS`.
3. Any `PAYLOAD_SCHEMA_VERSION` bump / required-key add.
4. Any NEW durable/published persistence surface; any `git add -f` of the artifact.
5. Renderer-side recomputation of any movement value.
6. Any daily watchlist write (slice 2).
7. Any `datetime.now()` in the block (freshness keyed on `generated_at`).
8. Any null/missing -> `0.0` coercion (R1').
9. Any validation-aware / valid_quotes admission change for the sidecar (future
   debt, owner F2).
10. Any change to the publish workflows.
11. Exceeding §8 files / §9 ceiling without a fresh GOV-2 §1 pass.
12. Any scoring/ranking/permission/bullish-bearish/relative-strength logic.

---

## 13. Materiality / lane
**MATERIAL** (carrier + tiny observe-only fetch/merge); structurally isolated from
decisions (§4.2). **HIGH-RISK** (dashboard_renderer.py; PRD-121 R11).
MICRO-ineligible. After review-clean + design-direction ruling: Stage-0 PRD ->
independent PRD review -> Gate A. Governance hold: DRAFT + self-named (GOV-0 /
PRD-186), held for Dustin.

---

## 14. What gets CUT
- Any decision-pipeline entry for UCO/GOOG (owner F1/R8; proven §4.2).
- Provider abstraction / universe engine / scheduler / ingestion subsystem /
  broad refactor (owner F1).
- Validation-carrier redesign / valid_quotes admission (owner F2; future debt §15).
- Registry `trade_eligible` change (owner F7).
- PRICE_BOUNDS/source-priority edits (N/A — observe-only bypasses validate_quotes;
  default source routing).
- Adding UCO/GOOG to ALL_SYMBOLS/COMMODITIES/HIGH_BETA/NON_TRADABLE.
- Scoring/ranking/prediction/second board/new cadence/relative-strength.
- Daily watchlist write (slice 2).

---

## 15. Open design/review questions
- **D-5 Helper extraction (R6):** `movement_card.py` vs inline.
- **D-7 Versioning (R7) — resolved recommendation:** `schema_version`->2, reader
  accepts source==watchlist AND version==2 AND full-12 identity, else suppress.
- **Future debt (owner F2, recorded not solved):** validation-aware sidecars /
  `valid_quotes` admission — whether the watchlist/trend-structure sidecars should
  render only validation-passed quotes, and whether to bound per-symbol quote age.
  A runtime scope change for a future slice.

---

## 16. Author self-verification (GOV-2 §3)
All against `main` @ `80ac6eb`; correction facts [C]:
- [C] `fetch_quote(symbol)` (`ingestion.py:87`), `normalize_quote`
  (`normalization.py:61`), `fetch_all`/`normalize_all`/`validate_quotes` assembly
  (`runtime/__init__.py:549-552`); watchlist write `:784`. The merge point is
  downstream of `normalized_quotes`. CONFIRMED.
- [C] `OBSERVE_ONLY_SYMBOLS` disjoint from `ALL_SYMBOLS` by construction; the
  ingestion loop iterates `ALL_SYMBOLS` (`:78`); decision pipeline keyed on
  `ALL_SYMBOLS`/`valid_quotes`. CONFIRMED (isolation §4.2).
- [C] `qualification.py:191` fans out over `structure_results` from `valid_quotes`
  — observe-only never enters it. CONFIRMED.
- [C] `docs/universe_taxonomy.md` governs `ALL_SYMBOLS`; observe-only is a separate
  universe -> new taxonomy entry (F4). CONFIRMED.
- [C] The six F5 files + `test_phase1.py:80` (`==23`) assert unchanged constants ->
  green, no edit. CONFIRMED.
- [C] Live UCO/GOOG fetch via `fast_info` path (§4.4). CONFIRMED.
- Carrier/movement/freshness/version facts as v0.4 §16. CONFIRMED.

Author self-verification is NOT independent review. Event-2 confirmation of
F1-F7+G1 at the v0.5 head is PENDING.

---

## 17. Packet review records (GOV-2 §2, §7)

### CONSOLIDATED CORRECTION of the 12/12 Event-1 (this v0.5) — CORRECTION CYCLE
Reviewed head `5d51f94` (v0.4). One consolidated correction per GOV-1 / GOV-2 §2
step 4, against Dustin's Option-A ruling.

- **F1 (BOUNDARY) — ACTIONED.** Replaced the config-membership seam with a separate
  `OBSERVE_ONLY_SYMBOLS` fetched via the existing `fetch_quote`+`normalize_quote`
  and merged only at the watchlist write (§4.1). Structural isolation proof (§4.2)
  + guards M17/M18. UCO/GOOG never enter `ALL_SYMBOLS`/`valid_quotes`/
  qualification/regime.
- **F2 (BOUNDARY) — ACTIONED (owner-scoped).** Removed the false "validation
  failure -> n/a"; honest contract = fetch/normalization failure -> n/a; existing
  normalized-sidecar semantics preserved (§3.5); validation-aware admission
  recorded as future debt (§15). No carrier redesign.
- **F3 (P1) — ACTIONED.** Explicit disjointness + pipeline-blind guards (M17/M18);
  removed the false "existing EXPANSION tests redden the unsafe mutation" claim.
- **F4 (BOUNDARY) — ACTIONED.** Observe-only is not in `ALL_SYMBOLS`, so the
  taxonomy's ALL_SYMBOLS mutation rule does not apply; ADD an OBSERVE_ONLY
  taxonomy entry (§4.3, §8). PRICE_BOUNDS N/A (bypasses validate_quotes);
  source-priority default. Pre-existing taxonomy drift (4 vs 7 macro drivers)
  noted, not fixed here.
- **F5 (P2) — ACTIONED.** The seam changes no decision universe; the six flagged
  files + `test_phase1.py:80` are enumerated verified-UNAFFECTED (§8).
- **F6 (P1) — ACTIONED.** Acceptance now enforces exact full-12 identity + unique
  in-range registry_index (§5.1); M6/M9 mutations.
- **F7 (P2) — ACTIONED (owner).** Registry `trade_eligible=True` unchanged; stated
  as an observational attribute, not runtime authority (§0.1, §14).
- **G1 — ACTIONED.** M11 has no future-`generated_at` case; no clock introduced;
  §12 clock tripwire is #7 and M11 references #7 (cross-ref fixed).

### EXACT-CORRECTED-HEAD CONFIRMATION (Event-2) — COMPLETE, CLEAN (2026-08-22)
Record: `NS4B_V05_EVENT2_CODEX_CONFIRMATION_2026-08-22.md`. Reviewer: independent
Codex, fresh context, read-only, high. Reviewed SHA `2789dda` (v0.5). **Verdict:
CLEAN — F1-F7 + G1 all RESOLVED; NEW BLOCKING: NONE.** The GOV-2 packet cycle is
COMPLETE; the packet is REVIEW-CLEAN. Downstream authority still requires Dustin's
design-direction ruling -> Stage-0 PRD -> independent PRD review -> Gate A.

### Historical records (evidence)
- 10/12: `NS4B_EVENT1_CODEX_REVIEW_2026-08-22.md` (v0.2), `NS4B_EVENT2_CODEX_CONFIRMATION_2026-08-22.md` (v0.3, G1).
- 12/12 v0.4: `NS4B_V04_EVENT1_CODEX_REVIEW_2026-08-22.md` (F1-F7).

### Out-of-scope
- O-1 `artifact_flow_map.md:122` "11-tuple" -> 12; slice corrects.
- O-2 `universe_taxonomy.md` lists 4 macro drivers vs 7 in code (pre-existing
  drift); not fixed here.

---

## 18. Revision log
- **v0.5 (2026-08-22):** consolidated correction of the 12/12 Event-1 (F1-F7 + G1)
  against Dustin's Option-A ruling — smallest observe-only fetch seam (separate
  `OBSERVE_ONLY_SYMBOLS`, merged only at the watchlist write; structural isolation
  proof; honest F2 admission contract; taxonomy entry; full-12 acceptance;
  verified-unaffected F5 set; registry unchanged; G1 fixed). Supersedes v0.4.
- **v0.4:** 12/12 config-membership boundary reset (Event-1 FINDINGS F1-F7).
- **v0.3:** 10/12 consolidated correction (Event-2 NOT CLEAN on G1).
- **v0.2:** owner alignment (Event-1). **v0.1:** initial.

---

END OF PACKET v0.5 — PROVISIONAL / NOT REVIEW-CLEAN — NO IMPLEMENTATION
AUTHORITY. Codex Event-2 (EXACT-CORRECTED-HEAD CONFIRMATION of F1-F7 + G1) runs
on this revision's committed head. Gate A is neither requested nor granted.
