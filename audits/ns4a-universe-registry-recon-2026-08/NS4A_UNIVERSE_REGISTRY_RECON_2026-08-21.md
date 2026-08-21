# NS-4A Universe Registry - Stage-0 Product Recon

**Date:** 2026-08-21
**Author:** Claude Code (recon session; read-only charge)
**Starting main SHA:** `e89eebb64997e8857827a9f294d228538b30bdce`
**Worktree branch:** `worktree-ns4a-universe-recon` (fresh from main @ `e89eebb`)
**Class:** reconnaissance / owner-input preparation. Evidence only.

## 0. What this is, and is not

This artifact reconstructs the symbol/context universe Cuttingboard *already*
knows about, so Dustin can ratify the smallest useful NS-4A Universe Registry.

It is governed by, and does not exceed, three standing authorities:

- **`docs/DECISIONS.md` 2026-08-05 TRUTH-SYNC ruling 6** (the direct mandate):
  "Registry (NS-4A universe + NEWS-0 relationship): agent drafts from
  repository seeds, Dustin ratifies. Seeds are `config.TREND_STRUCTURE_SYMBOLS`
  and `market_map.PRIMARY_SYMBOLS` plus the Ledger's suggested groups; every
  element beyond the seeds is flagged for ratification. No symbol or source is
  inferred."
- **North Star ledger** `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`
  NS-4A: `LATER`. Registry contents are human-authored.
- **Expansion doctrine / workplan** NEWS-0 registry categories
  (`docs/plans/decision-support-workplan-v0.1.md:325-334`).

**This artifact does NOT:** create the registry, write any registry file,
select an implementation seam, set a FILES/LOC ceiling, claim an exhaustive
all-consumer guarantee, infer any symbol or source, open a PRD, request Gate A,
or propose a merge. It carries evidence and creates no implementation
authority.

**Excluded by charter (not opened):** `tools/gex_snapshot.py`,
`logs/gex_snapshot.json`, `dashboard_renderer.py` /
`cuttingboard/delivery/dashboard_renderer.py`, any `*gex*` file, GEX docs,
PRs #261/#262/#263, NS-2E PRs #222/#225/#226. Where such a file appears below,
it appears only as an unopened downstream reference from grep output.

---

## 1. What the governing authorities already fix

Reading the authorities before inventory (charter section 1) settles four
things, so the recon does not re-derive them:

1. **NS-4A contents are Dustin's to author.** The doctrine is explicit: "The
   exact universe content is supplied or ratified by Dustin. An agent may not
   infer additional symbols or sources"
   (`decision-support-workplan-v0.1.md:333-334`). This is why section 4 below
   is a blank-disposition sheet, not a proposed registry.

2. **The seed is already named.** The implementation program
   (`NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:106`) records the NS-4A seed as
   "Universe substrate (`config.TREND_STRUCTURE_SYMBOLS`,
   `market_map.PRIMARY_SYMBOLS`) - Two agreeing fixed six-symbol tuples -
   RETAINED as the registry seed; NS-4A stays LATER."

3. **The registry is shared substrate, not a feature.** NS-4A feeds NS-4B
   heatmap, NS-4C/D leadership/participation, NS-6 news (NEWS-0), and NS-7
   decoupling (`...IMPLEMENTATION_PROGRAM...:131-134`). NEWS-0's required
   categories (tradeable symbols, context-only symbols, themes, approved
   sources, enabled/disabled + reason) are a subset of the NS-4A shape.

4. **A canonical universe doc already exists** - `docs/universe_taxonomy.md` -
   and it already asserts the exact rule a registry would enforce: "One source
   of truth per universe. No module redefines a universe list locally"
   (`universe_taxonomy.md:100-101`). Section 3 shows that rule is already
   violated, and that the doc itself is stale.

North Star "Suggested groups" (verbatim, `MASTER_LEDGER...:163`):
> Context, Energy, AI / Semis, Tradeable, Spec / Learning, Holdings.

NS-4A field list (verbatim, `MASTER_LEDGER...:157`):
> Human-authored symbols, aliases, themes, roles, horizons, benchmarks,
> questions.

Motto: **Observe wide. Trade narrow.**

---

## 2. Inventory of current universe-definition surfaces

Every current, product-relevant surface that names or groups symbols. Sources
classified per charter: RUNTIME INPUT / HUMAN CONFIG / GENERATED OUTPUT /
TEST FIXTURE / HISTORICAL DOC / PROPOSAL ONLY / STALE-DEAD.

Test fixtures and historical/proposal docs are listed separately (2.4) and are
NOT counted as current product universe.

### 2.1 Human-config symbol universes (the live source of truth)

| # | Construct | Location | Members (as written) | Role | Consumed today? |
|---|---|---|---|---|---|
| 1 | `MACRO_DRIVERS` | `config.py:258` | `^VIX, DX-Y.NYB, ^TNX, BTC-USD, CL=F, GC=F, SI=F` | context drivers (non-tradable) | YES - regime, macro snapshot, payload |
| 2 | `NON_TRADABLE_SYMBOLS` | `config.py:259` | `frozenset(MACRO_DRIVERS)` (derived) | tradability exclusion | YES - `universe.is_tradable_symbol` |
| 3 | `INDICES` | `config.py:260` | `SPY, QQQ, IWM` | index/benchmark | ONLY to build `ALL_SYMBOLS` (label discarded) |
| 4 | `COMMODITIES` | `config.py:261` | `GLD, SLV, GDX, PAAS, USO, XLE` | commodity/metals/energy proxy | ONLY to build `ALL_SYMBOLS` (label discarded) |
| 5 | `HIGH_BETA` | `config.py:262` | `NVDA, TSLA, AAPL, META, AMZN, COIN, MSTR` | high-beta single names | ONLY to build `ALL_SYMBOLS` (label discarded) |
| 6 | `ALL_SYMBOLS` | `config.py:264` | concat of 1,3,4,5 (derived) | full fetch/scan universe | YES - ingestion, validation, regime fan-out |
| 7 | `REQUIRED_SYMBOLS` | `config.py:265` | `^VIX, DX-Y.NYB, ^TNX, BTC-USD, SPY, QQQ` | must-resolve set | YES - validation |
| 8 | `HALT_SYMBOLS` | `config.py:166` | `^VIX, DX-Y.NYB, ^TNX, SPY, QQQ` | kill-switch data-integrity set | YES - `validation.py:106` |
| 9 | `EXPANSION_LEADERSHIP_SYMBOLS` | `config.py:202` | `NVDA, COIN, MSTR, SMCI, TSLA` | regime leadership breadth | YES - `regime.py:120` |
| 10 | `TREND_STRUCTURE_SYMBOLS` | `config.py:269` | `SPY, QQQ, GDX, GLD, SLV, XLE` | trend-structure sidecar universe | YES - `runtime:2449`, trend_structure sidecar |
| 11 | `SYMBOL_SOURCE_PRIORITY` | `config.py:275` | per-symbol -> `["yfinance"]` (+`default`) | source routing | YES - `ingestion.py:93` |
| 12 | `PRICE_BOUNDS` | `config.py:290` | 22-symbol sanity map | validation bounds | YES - validation |
| 13 | `SYMBOL_UNITS` | `config.py:320` | `^VIX, DX-Y.NYB, ^TNX` -> unit label | display/units | YES - normalization |
| 14 | `CORRELATION_GOLD_SYMBOL` / `CORRELATION_DOLLAR_SYMBOL` | `config.py:332-333` | `GLD` / `DX-Y.NYB` | correlation-pair relationship | YES - `correlation.py:43-44` |
| 15 | `_MACRO_DRIVER_SYMBOLS` (alias map) | `contract.py:50-58` | `volatility->^VIX, dollar->DX-Y.NYB, rates->^TNX, bitcoin->BTC-USD, oil->CL=F, gold->GC=F, silver->SI=F` | semantic-name -> ticker ALIAS map | YES - `_build_macro_drivers`; synced to #1 at `contract.py:538` |
| 16 | `_OPTIONAL_MACRO_DRIVERS` | `contract_types.py:45` | `oil, gold, silver` | driver optionality class | YES - contract + payload validators |
| 17 | `_COMPONENT_KEYS` / `_COMPONENT_FIELDS` | `macro_pressure.py:18-30` | `volatility, dollar, rates, bitcoin` (oil/gold/silver excluded) | pressure-synthesis inputs | YES - macro pressure |
| 18 | `_INDEX_ETFS` | `options.py:76` | `SPY, QQQ, IWM` | strike-distance tier (ETF vs single-name) | YES - `options.py:244,448` |
| 19 | `PRIMARY_SYMBOLS` | `market_map.py:20` | `SPY, QQQ, GDX, GLD, SLV, XLE` | market-map graded universe | YES - `market_map.py:141,152` |
| 20 | `ASSET_GROUPS` | `market_map.py:101-108` | `SPY/QQQ->INDEX, GDX/GLD/SLV->METALS, XLE->ENERGY` | symbol -> sector/theme map | YES - market-map labels |
| 21 | `ENERGY_CONTEXT_SYMBOL` | `market_map.py:110` | `USO` | energy context proxy | YES - `market_map.py:568-586` |
| 22 | `primary_symbols` (bare literal) | `runtime/__init__.py:1580-1581` | `{SPY, QQQ, GDX, GLD, SLV, XLE}` | market-map bar-window filter | YES - but DUPLICATES #10/#19 (see 3.1) |
| 23 | regime vote inputs (hardcoded) | `regime.py:49-54, 93-95, 159-173` | `SPY, QQQ, IWM, ^VIX, DXY` literals | regime vote sources | YES - regime engine |
| 24 | `_OBSERVED_SYMBOL` / `compute_intraday_state("SPY")` | `spy_observation.py:42`, `spy_state.py:101` | `SPY` | the single observed symbol (PRD-288/289) | YES - daily SPY card |
| 25 | `WATCHLIST_SYMBOLS` | `watchlist_sidecar.py:28-38` | 11 `(symbol, theme, reason)` triples (see 2.3) | observe-only watchlist w/ themes | YES - live producer (see 2.2) |
| 26 | macro-tape `TapeSlot` rows + alias maps | `delivery/macro_tape_layout.py:34-93` | label<->payload-key<->quote-symbol; display aliases `XAU->GC=F`, `XAG->SI=F` | macro-tape display + aliases + cyclicality groups | YES - delivery layer |
| 27 | `_require_macro_drivers` expected keys | `delivery/payload.py:318-351` | 7 driver keys | payload schema validator | YES - payload build |

**Count: 27 distinct current symbol-universe surfaces in code, across ~11
modules.** (`config.py`, `contract.py`, `contract_types.py`, `macro_pressure.py`,
`options.py`, `market_map.py`, `runtime/__init__.py`, `regime.py`,
`spy_observation.py`, `spy_state.py`, `watchlist_sidecar.py`, plus the two
`delivery/` layout/validator surfaces.)

### 2.2 Generated-output snapshots carrying a universe (GENERATED OUTPUT)

Written by the pipeline; they mirror the config universes, they do not define
them. Listed so a reader does not mistake an output for a source of truth.

| Snapshot | Universe carried | Writer |
|---|---|---|
| `logs/trend_structure_snapshot.json` | `SPY,QQQ,GDX,GLD,SLV,XLE` | `runtime._write_trend_structure_snapshot` |
| `logs/market_map.json` / `logs/latest_hourly_market_map.json` | `primary_symbols`, `symbols.*`, `context.energy.symbol=USO` | market-map writer |
| `logs/macro_drivers_snapshot.json` | 7 macro drivers | `runtime._write_macro_snapshot` (`runtime:2524`) |
| `logs/latest_payload.json` | `macro_drivers.*` (7) | payload build |
| `logs/latest_contract.json` | `correlation.gold_symbol/dollar_symbol` | `contract.py:515-516` |
| `logs/watchlist_snapshot.json` | 11 watchlist rows | `runtime._write_watchlist_snapshot` (`runtime:784, 2507`) |

### 2.3 The one existing NS-4A-shaped artifact: the watchlist sidecar

`cuttingboard/watchlist_sidecar.py` (PRD-114) is already a small
symbol+theme+description registry, live and observe-only. Its shape is the
closest thing in the repo to an NS-4A row:

```
WATCHLIST_SYMBOLS: tuple[tuple[str, str, str], ...] = (
    ("SPY",  "Index",       "broad market reference"),
    ("QQQ",  "Index",       "tech-heavy reference"),
    ("GDX",  "Commodities", "gold miners exposure"),
    ("GLD",  "Commodities", "spot gold ETF"),
    ("SLV",  "Commodities", "spot silver ETF"),
    ("XLE",  "Commodities", "energy sector"),
    ("NVDA", "High beta",   "AI/semis bellwether"),
    ("TSLA", "High beta",   "retail-flow signal"),
    ("META", "High beta",   "large-cap tech"),
    ("AMZN", "High beta",   "large-cap tech"),
    ("AAPL", "High beta",   "large-cap tech"),
)
```

Its own docstring already states the NS-4A discipline: observe-only, "Outputs
do not feed qualification, regime, or any decision surface," and insertion
order "MUST NOT imply rank, priority, conviction..." (R14). This is the
row-shape precedent for the registry, and a candidate to be *sourced from* the
registry later rather than hand-maintained in parallel.

### 2.4 Non-current surfaces (excluded from the product universe)

| Surface | Location | Classification |
|---|---|---|
| 20-symbol cached quote fixture (mirrors `ALL_SYMBOLS`) | `tests/fixtures/2026-04-12.json` | TEST FIXTURE (faithful mirror, not an independent definition) |
| Generic SPY/QQQ/GLD/NVDA/XLE/META stand-ins | many `tests/*.py` | TEST FIXTURE |
| Backtest corpus "16 real tradable symbols" + per-symbol ATR tables | `PRD-251.continuation-path.proposal.md`, `PRD-256...proposal.md` | PROPOSAL ONLY / historical |
| NS-7 decoupling example pairs (AVGO/SOXX, OXY/energy, NVDA/QQQ) | `...IMPLEMENTATION_PROGRAM...:543-544` | PROPOSAL ONLY (LATER, unbuilt) |
| Suggested groups; NEWS-0 categories | ledger:163; workplan:325-334 | PROPOSAL ONLY (aspiration) |
| `## instrument universe` CLAUDE.md anchor | asserted in `PRD-143.md:89,93` | STALE-DEAD (no such header exists in CLAUDE.md today) |
| `lns` / `_build_lns` / `logs/lns_snapshot.json` naming | `PRD_PROCESS.md`, `system_logic_map.md`, milestone docs | STALE-DEAD (code uses `macro_drivers` naming now) |

---

## 3. Duplication and divergence (reconnaissance - NOT an exhaustive guarantee)

This section shows where the same concept is repeated. It does NOT claim to
enumerate every consumer, does NOT select an implementation seam, and does NOT
set any ceiling. Those steps may be MATERIAL and belong to a later governed
packet (section 6E).

### 3.1 The six-symbol context basket is defined THREE times

The implementation program recorded "two agreeing fixed six-symbol tuples."
Recon found a third copy, an undocumented bare literal:

- `config.TREND_STRUCTURE_SYMBOLS` (`config.py:269`) - tuple
- `market_map.PRIMARY_SYMBOLS` (`market_map.py:20`) - tuple, identical members
- `runtime/__init__.py:1580-1581` - bare `set` literal
  `{"SPY","QQQ","GDX","GLD","SLV","XLE"}`, not imported from either constant

All three currently agree by hand. This directly violates
`universe_taxonomy.md:100-101` ("No module redefines a universe list locally;
consumers import from `config.py`"). The bare literal in `runtime` is the
clearest single candidate to disappear behind one registry lookup.

### 3.2 The same symbols carry three DIVERGENT theme taxonomies

The metals/energy names are grouped three different ways:

| Symbol | `config` group (`260-262`) | `market_map.ASSET_GROUPS` (`101`) | `watchlist_sidecar` (`28`) |
|---|---|---|---|
| GLD | COMMODITIES | METALS | Commodities |
| SLV | COMMODITIES | METALS | Commodities |
| GDX | COMMODITIES | METALS | Commodities |
| XLE | COMMODITIES | **ENERGY** | Commodities |
| PAAS | COMMODITIES | (absent) | (absent) |
| USO | COMMODITIES | (absent; `USO` is the ENERGY_CONTEXT proxy) | (absent) |
| SPY/QQQ | INDICES | INDEX | Index |

Three overlapping-but-unequal membership sets and three label vocabularies
(`COMMODITIES` vs `METALS`+`ENERGY` vs `Commodities`). Note also
`EXPANSION_LEADERSHIP_SYMBOLS` includes `SMCI`, which is absent from
`HIGH_BETA` - a fourth divergence on the high-beta theme.

Root cause: the `config` group lists (`INDICES`/`COMMODITIES`/`HIGH_BETA`) are
consumed **only** to concatenate `ALL_SYMBOLS` (`config.py:264`; verified: no
other reader). Their theme meaning is discarded at runtime, so `market_map` and
`watchlist_sidecar` each re-invent a theme mapping independently.

### 3.3 Aliases / source translation live in several places

- The yfinance ticker strings themselves are source-format aliases of a plain
  concept: `^VIX` (VIX), `DX-Y.NYB` (US Dollar Index), `^TNX` (10Y yield),
  `CL=F`/`GC=F`/`SI=F` (WTI/gold/silver futures), `BTC-USD` (bitcoin).
- The semantic-name -> ticker map is `_MACRO_DRIVER_SYMBOLS` (`contract.py:50`),
  kept in sync with `config.MACRO_DRIVERS` by an explicit assertion
  (`contract.py:538`) - i.e. two lists that must be manually reconciled.
- Display aliases (`XAU->GC=F`, `XAG->SI=F`) live separately in
  `macro_tape_layout.py`.

### 3.4 Benchmarks are almost entirely implicit

There is no per-symbol benchmark field anywhere. The only explicit
symbol-to-symbol relationship is the GLD<->DXY correlation pair
(`config.py:332-333`). `ASSET_GROUPS` assigns a group but no benchmark. NS-4C
leadership and NS-7 decoupling both need an assigned benchmark that the repo
does not currently carry - so benchmarks are almost entirely a
Dustin-authored input, not a repository fact.

### 3.5 The canonical taxonomy doc is itself stale

`universe_taxonomy.md:47` lists `MACRO_DRIVERS` as 4 symbols
(`^VIX, DX-Y.NYB, ^TNX, BTC-USD`); `config.py:258` has 7 (adds
`CL=F, GC=F, SI=F`). The doc that claims to be the single canonical universe
reference is out of date with the code it documents (a `docs-match-code`
divergence). Flagged as evidence; not fixed here (recon only, no changes).

---

## 4. Owner-ratification sheet

One row per symbol the repository already names. This is a sheet for Dustin,
not a registry. **No symbol below is inferred** - each is present in a current
code surface (section 2). The OWNER DISPOSITION column is blank for Dustin:
**KEEP / CHANGE / DROP / QUESTION**.

"Consumed today" = whether the symbol participates in a live pipeline effect
beyond simply being fetched.

| Symbol | Source-format alias / note | Observed role | Group(s) as coded (divergences) | Benchmark present? | Defining surfaces | Consumed today (beyond fetch)? | Ambiguity / conflict | OWNER DISPOSITION |
|---|---|---|---|---|---|---|---|:--|
| SPY | - | index / the traded + observed symbol | INDICES / INDEX / Index | none (is itself the reference) | #3,6,7,8,10,18,19,20,22,23,24,25 | YES (regime, ORB, SPY card, market map, trend) | none | |
| QQQ | - | index / tech reference | INDICES / INDEX / Index | none | #3,6,7,8,10,18,19,20,22,23,25 | YES (regime, market map, trend) | none | |
| IWM | - | small-cap index | INDICES / (not in map or watchlist) | none | #3,6,18,23 | YES (regime vote, index-ETF tier) | in `INDICES`+regime but absent from market map, trend basket, watchlist | |
| GDX | - | gold miners | COMMODITIES / METALS / Commodities | none | #4,10,19,20,22,25 | YES (market map, trend) | theme label differs 3 ways (3.2) | |
| GLD | gold ETF | metals / gold leg | COMMODITIES / METALS / Commodities | vs DXY (corr pair) | #4,10,14,19,20,22,25 | YES (correlation, market map, trend) | theme label differs 3 ways | |
| SLV | silver ETF | metals | COMMODITIES / METALS / Commodities | none | #4,10,19,20,22,25 | YES (market map, trend) | theme label differs 3 ways | |
| XLE | energy sector ETF | energy | COMMODITIES / **ENERGY** / Commodities | none | #4,10,19,20,22,25 | YES (market map, trend) | classified ENERGY in map but COMMODITIES elsewhere | |
| PAAS | - | silver miner | COMMODITIES only | none | #4 (via ALL_SYMBOLS), #12 | fetched only; no sidecar/theme consumer | in COMMODITIES + PRICE_BOUNDS but no downstream role | |
| USO | oil ETF | energy context proxy | COMMODITIES / ENERGY_CONTEXT | none | #4,#21 | YES (market-map energy context) | doubles as `ENERGY_CONTEXT_SYMBOL`; also in COMMODITIES list | |
| NVDA | - | high-beta / AI-semis | HIGH_BETA / High beta / leadership | none | #5,9,25 | YES (leadership breadth, watchlist) | in HIGH_BETA + leadership + watchlist | |
| TSLA | - | high-beta | HIGH_BETA / High beta / leadership | none | #5,9,25 | YES (leadership, watchlist) | none material | |
| AAPL | - | large-cap tech | HIGH_BETA / High beta | none | #5,25 | watchlist only (fetched) | in HIGH_BETA + watchlist; not in leadership | |
| META | - | large-cap tech | HIGH_BETA / High beta | none | #5,25 | watchlist only | same | |
| AMZN | - | large-cap tech | HIGH_BETA / High beta | none | #5,25 | watchlist only | same | |
| COIN | - | crypto-beta | HIGH_BETA / leadership | none | #5,9 | YES (leadership) | in HIGH_BETA + leadership; NOT in watchlist | |
| MSTR | - | crypto-beta | HIGH_BETA / leadership | none | #5,9 | YES (leadership) | same as COIN | |
| SMCI | - | AI-semis | leadership only | none | #9 | YES (leadership breadth) | in `EXPANSION_LEADERSHIP_SYMBOLS` but ABSENT from `HIGH_BETA` (3.2) | |
| ^VIX | VIX index | volatility driver (non-tradable) | MACRO_DRIVERS | n/a | #1,7,8,13,15,17,23,26 | YES (regime, halt, pressure, tape) | canonical name vs `volatility` payload key | |
| DX-Y.NYB | US Dollar Index (`dollar`) | dollar driver (non-tradable) | MACRO_DRIVERS | dollar leg of GLD corr | #1,7,8,13,14,15,17,23,26 | YES (regime, halt, correlation, pressure) | alias sync between #1 and #15 | |
| ^TNX | 10Y Treasury yield (`rates`) | rates driver (non-tradable) | MACRO_DRIVERS | n/a | #1,7,8,13,15,17,26 | YES (regime, halt, pressure) | none | |
| BTC-USD | bitcoin (`bitcoin`) | crypto driver (non-tradable) | MACRO_DRIVERS | n/a | #1,7,15,17,26 | YES (regime, pressure) | in REQUIRED but NOT in HALT set | |
| CL=F | WTI crude (`oil`) | oil driver (non-tradable) | MACRO_DRIVERS | n/a | #1,15,16,26 | display/context only (excluded from pressure #17) | "optional" driver; excluded from macro-pressure | |
| GC=F | gold futures (`gold`; tape `XAU`) | gold driver (non-tradable) | MACRO_DRIVERS | n/a | #1,15,16,26 | display/context only | optional; distinct from GLD (the tradable) | |
| SI=F | silver futures (`silver`; tape `XAG`) | silver driver (non-tradable) | MACRO_DRIVERS | n/a | #1,15,16,26 | display/context only | optional; distinct from SLV (the tradable) | |

Additional whole-set dispositions for Dustin (not per-symbol):

| Question for Dustin | Evidence | OWNER DISPOSITION |
|---|---|:--|
| Is the canonical THEME taxonomy the map's (INDEX/METALS/ENERGY), the config's (INDICES/COMMODITIES/HIGH_BETA), or the watchlist's (Index/Commodities/High beta)? | 3.2 | |
| Should the six-symbol context basket, the market-map universe, and the trend basket be one named group or stay separate? | 3.1 | |
| Are PAAS and USO still wanted as fetched members, or is one of them dead weight? | PAAS has no downstream consumer | |
| Which names get an assigned benchmark (needed for NS-4C leadership / NS-7 decoupling)? | 3.4 | |
| Do you want `horizon` and `question` fields at all (no current repo consumer)? | ledger:157 | |

---

## 5. Proposed registry SHAPE only (no contents)

Per charter section 5 and doctrine, this proposes the *smallest useful shape*,
not the registry itself. Boring, deterministic, human-authored data. Fields are
drawn from the North Star NS-4A list (`symbols, aliases, themes, roles,
horizons, benchmarks, questions`), the NEWS-0 category list, and the shapes the
repo already uses (`watchlist_sidecar` row = symbol/theme/reason).

| Field | Req? | Human-authored or derived | Why it exists | Product question it enables |
|---|---|---|---|---|
| `symbol` (canonical) | required | human | the primary key; one canonical id per instrument | all |
| `source_ticker` (e.g. yfinance `^VIX`, `DX-Y.NYB`) | required where it differs from `symbol` | human | collapses the alias/translation spread (3.3) into one place | Q1/Q2 (fetch + display) |
| `aliases` (display, e.g. `XAU`, plain-language name) | optional | human | absorbs `macro_tape` display aliases and human labels | Q2 (readable context) |
| `role` (`tradable` / `context-only` / `driver`) | required | human | replaces the implicit `NON_TRADABLE_SYMBOLS` split with an explicit field | Q3 (is it a trade candidate?) |
| `group` / `theme` (single taxonomy) | optional | human | ends the 3-way theme divergence (3.2); one label per symbol | Q1/Q2; NS-4B heatmap grouping; NS-6 theme match |
| `benchmark` (assigned reference symbol) | optional | human | the repo has almost none (3.4); needed downstream | NS-4C leadership, NS-7 decoupling |
| `enabled` + `reason` | required | human | NEWS-0 mandates human-editable enable/disable + reason | operational control |
| `horizon` | optional | human | North Star names it; NO current consumer - mark aspirational | (future) |
| `question` | optional | human | North Star names it; NO current consumer - mark aspirational | (future) |

Explicitly OUT of the proposed shape (charter section 5 prohibitions, restated
so a later author cannot drift into them): no actual registry contents; no
relationship graph; no bullish/bearish or sentiment field; no score or
confidence; no LLM-derived field; no provider/source abstraction (the sole
source is `yfinance` today); no news-ingestion design; no heatmap
implementation. `horizon` and `question` are carried as optional-and-currently-
unconsumed so the shape stays honest about what has a live consumer.

---

## 6. Product questions (charter section 6)

**A. Minimum registry to let one watchlist feed both the movement heatmap and
relationship-aware news later.**
The minimum is five fields: `symbol`, `source_ticker` (alias), `role`, `group`,
and `enabled+reason`. That set is exactly the `watchlist_sidecar` row shape
(symbol/theme/reason) plus an explicit `role` and the fetch alias. The heatmap
(NS-4B) needs symbol + group + freshness (freshness already exists in the
snapshot layer); news (NEWS-0) needs symbol + role + theme + enabled. Benchmark
is NOT required for that minimum - it is only needed once leadership (NS-4C) or
decoupling (NS-7) is built. So the smallest useful registry is the watchlist
shape with `role` added.

**B. Which current duplicated definitions could eventually disappear once such a
registry exists.**
Candidates (eventual, not now): the bare six-symbol `set` literal in
`runtime/__init__.py:1580`; the duplicate `market_map.PRIMARY_SYMBOLS` (could
read the registry's "context basket" group); the divergent theme maps in
`config` (INDICES/COMMODITIES/HIGH_BETA), `market_map.ASSET_GROUPS`, and
`watchlist_sidecar` (collapse to one `group` field); and the hand-synced alias
pair `config.MACRO_DRIVERS` <-> `_MACRO_DRIVER_SYMBOLS` (one `source_ticker`
field). This is an OPPORTUNITY map, not a removal plan - each collapse is a
separate later decision, and several are MATERIAL (6E).

**C. What Dustin must personally ratify because repository truth cannot
determine intent.**
- The canonical symbol set itself (KEEP/DROP each row in section 4).
- Which of the three theme taxonomies is correct (3.2) and its label vocabulary.
- Each symbol's `role` where the repo is ambiguous (e.g. is USO context-only or
  a commodity member; is GC=F/SI=F kept as drivers).
- Benchmark assignments (the repo carries essentially none, 3.4).
- Whether `horizon` and `question` exist at all (no current consumer).
- The news `source` allowlist - it does not exist yet; the only data source in
  the repo is `yfinance`, and there is no RSS/headline feed anywhere.
- Fate of no-consumer members (PAAS) and cross-set inconsistencies (SMCI in
  leadership but not HIGH_BETA).

**D. Can NS-4A be implemented without touching decision/qualification/execution
logic?**
YES - for the first slice. A new human-authored registry file plus a read-only
loader, with a single observe-only reader (or zero readers) and the existing
`config` universes left byte-for-byte unchanged, is purely additive and
baseline-neutral (satisfies doctrine G2 "human-readable observation is not
pipeline permission" and G5 "additive artifacts only"). The `watchlist_sidecar`
already proves this pattern (observe-only, no decision effect).
NO - the moment a slice *reconciles* the existing universes (makes
`market_map`, `regime`, or qualification read the registry instead of their
own constants), it edits decision-path code and its blast radius. That
reconciliation is a later, separate, and MATERIAL step - not the first NS-4A
slice.

**E. What would make the future implementation MATERIAL under GOV-2.**
Mapping to `GOV-2 section 1` triggers:
- Consolidating the triple basket (3.1) into one shared carrier read by both
  `runtime` and `market_map` = "selects an implementation seam or carrier
  shared across pipeline layers" and "crosses two or more of runtime / ...
  dashboard / persistence" (bullets 2, 7). MATERIAL.
- A persisted registry schema with more than one reader (heatmap AND news AND
  leadership) = "adds ... a persisted schema surface that has more than one
  reader or presentation path" (bullet 4). MATERIAL.
- Any claim to enumerate all consumers of the symbol set (bullet 1), or setting
  a production FILES/LOC ceiling (bullet 3). MATERIAL.
Conversely, a strictly additive, single-reader (or zero-reader) registry file
that leaves every existing universe untouched can plausibly stay
non-MATERIAL and ride STANDARD. **Practical read:** NS-4A as *shared substrate
for multiple consumers* is MATERIAL and must enter through a GOV-2 upstream
packet (Codex packet review, exact-corrected-head confirmation, Dustin
design-direction ruling) before a Stage-0 PRD. NS-4A as a *first additive
registry file with one observe-only reader* can be scoped to avoid the MATERIAL
triggers - and that is the natural smallest first slice. The classification is
Dustin's to set at intake; this recon only maps which shapes cross the line.

---

## 7. Boundary statement

This artifact is evidence only. It creates no implementation authority.

- **NO IMPLEMENTATION** - no production or test code changed.
- **NO PRD** - none opened; no PRD number allocated.
- **NO REGISTRY FILE** - no registry written.
- **NO GATE A** - none requested.
- **NO DECISION ENTRY / NO WORKPLAN MUTATION** - none written.
- **NO MERGE** - the evidence branch/PR is held for Dustin like any other.

The two out-of-scope drift findings surfaced in passing (the stale
`MACRO_DRIVERS` count in `universe_taxonomy.md`, 3.5; the stale `lns` naming in
docs, 2.4) are recorded as evidence for a future owner-directed cleanup, NOT
fixed here.
