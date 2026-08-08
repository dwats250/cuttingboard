# CUTTINGBOARD — Context Registry + NEWS-0 Consolidation: Planning Packet

PLANNING ONLY. No implementation, no PRD allocated, no Gate A, no PR beyond
this planning commit. Prepared for Dustin + ChatGPT review. Recon basis:
`main` lineage at `7d0805ee`; 3 narrow read-only recon agents + direct reads;
load-bearing claims cite files.

**PLANNING DISPOSITION (2026-08-08): DRAFT COMPLETE — HELD FOR OWNER
REVIEW. Not implementation-ready until owner rulings (D1–D6) and GOV-2
MATERIAL intake close.**

**Core hypothesis verdict: CONFIRMED.** The "context registry" and NEWS-0
are one deliverable. This is not a new synthesis — it is already standing
owner direction: TRUTH-SYNC ruling 6 (DECISIONS.md:233-237) names the fused
"Registry (NS-4A universe + NEWS-0 relationship)" with seeds
(`config.TREND_STRUCTURE_SYMBOLS`, `market_map.PRIMARY_SYMBOLS`, the
Ledger's suggested groups), agent-drafted, Dustin-ratified, "No symbol or
source is inferred." The Operating Rule's lane 3 is "Context registry →
news and heatmap." This packet shapes that direction into a contract; it
does not re-decide it.

---

## 1. CURRENT TRUTH / DUPLICATION MAP

**At least five separately-maintained universe concepts exist** (all
verified with consumers greped):

| Vocabulary | Members | Metadata | Production consumers |
|---|---|---|---|
| `config.MACRO_DRIVERS` (:198) = `NON_TRADABLE_SYMBOLS` (:199, same set, second name) | 7 (^VIX, DX-Y.NYB, ^TNX, BTC-USD, CL=F, GC=F, SI=F) | none | contract.py, regime.py (breadth), universe.py, trade_decision.py, runtime |
| `config.INDICES` / `COMMODITIES` / `HIGH_BETA` (:200-202) | 3 / 6 / 7 | none | **ZERO** — test-only negative assertions (test_config.py:36-38); live only via `ALL_SYMBOLS` concatenation |
| `config.ALL_SYMBOLS` (:204) | 23 | none | ingestion fetch loop, regime breadth, runtime filter |
| `config.REQUIRED_SYMBOLS` (:205) | 6 | none | **ZERO** production consumers (test-only, test_config.py:60-61) |
| `config.TREND_STRUCTURE_SYMBOLS` (:209, PRD-110) | 6 (SPY,QQQ,GDX,GLD,SLV,XLE) | none | trend_structure writer, dashboard renderer |
| `market_map.PRIMARY_SYMBOLS` (:20) | **identical 6, identical order** | none | market_map builder |
| `watchlist_sidecar.WATCHLIST_SYMBOLS` (:27-39, PRD-114) | 11 | (symbol, sector_theme, watch_reason) | **ZERO** modules — human-reader-only sidecar by explicit ruling (DECISIONS 2026-05-22: "the human reader is the consumer") |
| `config.EXPANSION_LEADERSHIP_SYMBOLS` (:142) | 5 (incl. **SMCI**) | none | regime.py:120 (EXPANSION detection — decision logic) |

Supporting duplication/facts:
- `TREND_STRUCTURE_SYMBOLS` and `PRIMARY_SYMBOLS` are byte-identical tuples
  declared independently in two files with no import relationship — the
  flagship consolidation target, and exactly the pair ruling 6 names as
  seeds.
- `contract.py:64` and `payload.py:318-336` each declare their own
  `_OPTIONAL_MACRO_DRIVERS` = {oil, gold, silver} with a comment asking
  they stay aligned — an unenforced duplicate.
- **SMCI** (in EXPANSION_LEADERSHIP_SYMBOLS) appears in NO other table — no
  `PRICE_BOUNDS`, no `SYMBOL_UNITS`, not in `ALL_SYMBOLS`: a symbol used in
  regime scoring that the universe machinery doesn't know exists.
- Watchlist taxonomy ('Index'/'Commodities'/'High beta') parallels
  config's INDICES/COMMODITIES/HIGH_BETA but membership diverges (COIN,
  MSTR, PAAS, USO, IWM in config lists but absent from the watchlist).
- The only relationship structure in the codebase is the hardcoded GLD/DXY
  correlation pair (`config.py:271-276` → `correlation.py`) — decision
  logic, not context.
- No alias structure, no benchmark structure, no grouping structure exists
  anywhere (verified by grep).

**Should seed the registry** (per ruling 6 + candidates for ratification):
- *Pre-authorized seeds (ruling 6):* the identical 6-tuple
  (TREND_STRUCTURE_SYMBOLS / PRIMARY_SYMBOLS) and the Ledger's suggested
  groups (Context, Energy, AI/Semis, Tradeable, Spec/Learning, Holdings).
- *Candidate seeds (agent may draft FROM them; ratification required):*
  `ALL_SYMBOLS` membership as universe-candidate inventory; the watchlist's
  11 (symbol, sector_theme, watch_reason) rows — the richest existing
  human-authored metadata; MACRO_DRIVERS as context-only classification
  input.

**Must NOT become authority automatically:**
- Decision/pipeline configuration: `HALT_SYMBOLS`, `PRICE_BOUNDS`,
  `SYMBOL_UNITS`, `SYMBOL_SOURCE_PRIORITY`, `NON_TRADABLE_SYMBOLS`'
  tradability gate, `EXPANSION_LEADERSHIP_SYMBOLS`, the correlation pair.
  These encode pipeline behavior, not context semantics; absorbing them
  would silently make the registry a decision surface (forbidden here).
- Zero-consumer config lists (INDICES/COMMODITIES/HIGH_BETA,
  REQUIRED_SYMBOLS) — inputs to drafting at most; likely cuts (§9, §14).
- The Ledger's six groups as a flat enum — they conflate at least three
  axes (sector-theme: Energy, AI/Semis; role/status: Tradeable, Context;
  personal intent: Holdings, Spec/Learning) and need owner-ruled axis
  separation (D2), not verbatim adoption.

## 2. PRODUCT PURPOSE

The registry is CuttingBoard's single, interpretable, hand-auditable
statement of *what Dustin watches and how those things relate*: canonical
identity, classification, themes, benchmark assignment, watch reasons, and
(in later versions) explicit typed relationships. It is static, versioned,
owner-ratified data — the shared substrate the North Star names for
watchlists, news, heatmap, leadership/decoupling, and external mirroring
(NS-4/NS-6/NS-7, Ledger:151-208).

Hard properties: descriptive and deterministic; hand-editable and
diff-reviewable; every element beyond the ruling-6 seeds explicitly
ratified; no scoring engine, no prediction, no automated ontology
generation, no fuzzy/AI relationship inference at runtime. Consumers read
it; nothing computes it.

## 3. SMALLEST VIABLE REGISTRY CONTRACT (proposed)

One versioned, hand-authored JSON file (location per §7), strict keys,
canonically sorted. Proposed v1 sections:

- **`meta`**: `schema_version`, `content_version`, ratification record
  (date + DECISIONS pointer). Ratification is file-version-level — one
  owner act per content version, not per-row ceremony.
- **`themes`**: the ratified theme vocabulary (names + one-line meaning).
  Axis-separated per D2 — sector-subject themes (Energy, AI/Semis, …) kept
  distinct from roles.
- **`symbols[]`**, each: `symbol` (canonical, the in-repo provider ticker),
  `classification` (`tradeable` | `context_only`), `themes[]` (⊆ themes
  vocabulary), `benchmark` (optional, must reference a registry symbol),
  `watch_reason` (short free text, seeded from the watchlist),
  `state` (`active` | `dormant`), `aliases[]` (optional; news matching
  needs "Apple"→AAPL; may start sparse), `provenance` (`seed` |
  `ratified_addition`).
- **`sources[]`** (NEWS-0's approved-source allowlist): `name`, `domain`,
  `enabled`, `reason`. Section present from v1; content may be ratified
  later — an empty ratified-sources list truthfully means the news track
  remains content-gated (§5).

**Deliberately deferred (cuts until a consumer demands them):** pairwise
typed relationships / "related companies" (reserved section name recorded
in the schema doc so no competing structure appears later; populated only
when NEWS-1's relevance rules prove the need); `roles`/personal-status
tags beyond classification (Holdings, Spec/Learning — D2 decides if they
enter v1 or wait); `horizons` and `questions` (NS-4A ledger fields with no
near-term consumer); any numeric fields (bounds, weights, scores —
forbidden or config-owned).

This is the smallest shape that unlocks both dependents: the heatmap needs
universe + themes + deterministic order (+ benchmark for the later
leadership mode), and news needs universe + aliases + themes + sources.

## 4. OWNER-RATIFICATION BOUNDARY

- **Derivable facts (no ratification needed to state):** current list
  memberships and their consumers (§1); the identity of the two 6-tuples;
  watchlist metadata contents; SMCI's coverage gap. These are inputs, not
  authority.
- **Agent-draftable proposals (drafted, marked unratified):** the seeded
  draft registry content — symbol rows built from seeds + candidate seeds,
  proposed theme assignments, proposed benchmark assignments, absorbed
  watch reasons, proposed aliases. Ruling 6 explicitly assigns this
  drafting to the agent.
- **Owner-only (cannot become canonical without explicit decision):**
  final universe membership (every symbol beyond the 6-tuple seeds —
  including the fate of COIN, MSTR, PAAS, USO, IWM, SMCI in the context
  universe); the theme vocabulary and its axis semantics; benchmark
  semantics and assignments; every news source; whether NEWS-0 is formally
  satisfied; any personal-status content (Holdings). Mechanism: Dustin's
  merge of the content-carrying PR is the ratifying act (GOV-1), recorded
  with a dated DECISIONS entry naming the ratified `content_version`.

## 5. NEWS-0 CONSOLIDATION — YES, one deliverable, split cleanly

Doctrine §5.4 defines NEWS-0 as "static universe/source/theme registry
**and schema proposal**, no network producer." The registry file (§3)
satisfies the first half outright — same universe, same themes, same
sources section the Ledger's NEWS-0 row enumerates ("Symbols, aliases,
themes, benchmarks, related companies, approved sources", Ledger:188).

**What remains NEWS-specific (rides the same PRD as a small docs
deliverable, not a second registry):** the news *artifact* schema proposal
— item fields (title, source, publication time, URL, matched
symbols/themes, source-grounded excerpt), the 2-3-normally/5-hard item
cap, and deterministic relevance/dedup/freshness rules (doctrine §5.2).
That is a proposal document, not data; it needs no network work and no
producer.

**NEWS-0 closes** when Dustin ratifies (a) the registry content version
and (b) the news-schema proposal — jointly or separately (sources may be
ratified later; until then NEWS-1 stays gated by honest absence of an
approved-source list, while the heatmap path is unaffected).

**Duplicate-registry prevention:** the PRD/DECISIONS closeout records that
NEWS-0's registry IS `data/context_registry.json` (or final path), and the
workplan's NEWS-0 row is updated at closeout to point at it. Any future
news/heatmap PRD that proposes its own symbol/theme structure contradicts
a canonical source and fails review on that ground.

## 6. HEATMAP DEPENDENCY (heatmap itself out of scope)

Before NS-4B can exist cleanly, the registry must provide: (a) a ratified
universe with `active`/`dormant` state (what appears at all); (b) theme
membership (row grouping); (c) deterministic canonical ordering (stable
rendering without rank implication — the watchlist's R14 rule carries
over); (d) `classification` (context rows vs tradeable rows render
differently or not at all — product choice later). Benchmark assignment is
required not for NS-4B's grouped raw movement but for NS-4C
leadership/relative mode and NS-7 decoupling — including the one field in
v1 avoids a schema amendment one slice later. Nothing else is needed; in
particular the heatmap needs no pairwise relationships.

## 7. FILE / SURFACE PLAN (data/schema-first; no renderer/runtime changes)

| Surface | Path | Est. |
|---|---|---|
| Canonical registry (hand-authored, versioned JSON) | `data/context_registry.json` — follows the `data/red_folder_2026.json` hand-authored-input precedent, NOT the logs/ produced-artifact precedent | content, not LOC |
| Read-only loader (frozen dataclasses, fail-loud, no I/O beyond the file — `red_folder.py` pattern) | `cuttingboard/context_registry.py` (new) | 80–160 |
| CI-gate validator (standalone, wired as a bare step before pytest — `validate_prd_registry.py` precedent) | `tools/validate_context_registry.py` (new) + one line in `.github/workflows/ci.yml` | 120–220 |
| Tests | `tests/test_context_registry.py` (loader + validator + determinism) | 250–450 |
| Docs | NEWS-0 news-schema proposal doc; DECISIONS ratification entry; PROJECT_STATE row at PRD time. G5/artifact_flow_map: registration NOT required (static input, not a produced artifact — red_folder precedent), stated explicitly in the PRD so the omission is a decision, not an oversight | n/a |

**Untouched in this slice:** `config.py` lists, `market_map.py`,
`watchlist_sidecar.py`, `trend_structure`, renderer, payload, runtime,
regime — every current consumer keeps its existing vocabulary until R2
adoption (§9). LOC honesty note (PRD-288/289 lesson): the validator IS the
validation surface — it is counted as the largest code item, not rounded
away.

## 8. VALIDATION / FALSIFICATION (each check = a real invariant)

Validator (CI gate) + loader tests, all falsifiable with red tests:
- duplicate canonical symbols; duplicate aliases; alias colliding with any
  canonical symbol (breaks news matching determinism);
- `benchmark` must reference an existing, non-self registry symbol
  (unknown-target and self-reference both fail; deeper cycle rules are NOT
  added — no v1 computation follows benchmark chains, so a cycle invariant
  would be complexity without an invariant);
- every `themes[]` entry ∈ ratified theme vocabulary; every enum field
  (`classification`, `state`, `provenance`) ∈ its closed set;
- strict-key schema: unknown keys rejected (schema drift fails loud);
  `schema_version` exact-match;
- canonical ordering enforced (file sorted by symbol; sections sorted) —
  deterministic diffs, no rank implication;
- sources: duplicate domains, `enabled` boolean, non-empty `reason`;
- consumer-independent: validator + loader run green with zero consumers
  (that is the slice's definition of done);
- ratification representation: `content_version` + provenance vocabulary
  validated; a row marked `ratified_addition` in an unratified content
  version is a validator error (prevents silent authority).

## 9. MIGRATION / CONSOLIDATION PLAN (three stages, only R1 now)

- **R1 (this lane):** create registry + loader + validator + news-schema
  proposal. Zero consumer changes. Old vocabularies remain authoritative
  for all existing behavior.
- **R2 (later, per-consumer adoption PRDs, each bounded):** candidates in
  rough order of value — unify the twin 6-tuples (trend_structure +
  market_map read the registry group); watchlist sidecar reads registry
  rows (then its frozen tuple retires); news/heatmap consumers are born on
  the registry. Decision-config consumers (regime EXPANSION list, halt
  set, bounds) likely NEVER migrate — they are pipeline behavior, not
  context.
- **R3 (later, subtraction PRD):** delete duplicates once unreferenced —
  `INDICES`/`COMMODITIES`/`HIGH_BETA` and `REQUIRED_SYMBOLS` (already
  zero-production-consumer; their negative-assertion tests move or
  retire), `WATCHLIST_SYMBOLS` tuple, one of the twin 6-tuples.
  Cuts-before-additions is satisfied by *naming* these cuts now and
  executing them after adoption, not by a cross-cutting refactor in R1.

## 10. SCOPE WALLS (this lane does NOT include)

News ingestion or any network producer; headline ranking; AI
summarization; sentiment or any LLM-derived label; GEX; heatmap
implementation; Market Map retirement; scheduler work; decision-contract
changes; automatic trading implications; automated relationship discovery
or AI ontology inference; absorption of decision/pipeline config
(HALT_SYMBOLS, PRICE_BOUNDS, SYMBOL_UNITS, SYMBOL_SOURCE_PRIORITY,
EXPANSION_LEADERSHIP_SYMBOLS, correlation pair); any dashboard surface or
payload section; any consumer migration (R2) or deletion (R3); pairwise
relationship content.

## 11. MATERIALITY / GOVERNANCE RECOMMENDATION

**MATERIAL — with no evidence packet needed.** Rationale: the slice mints
canonical, owner-ratified product authority (the universe and theme
semantics ARE product semantics) and establishes a schema that three
future lanes (news, heatmap, NS-7 decoupling) will depend on — a shared
seam whose misdesign propagates. That matches GOV-2's MATERIAL intent even
though the slice has zero production consumers and no behavior change; the
final call is the mechanical GOV-2 §1 classification at intake, and if
that classification comes back non-MATERIAL, the owner-ratification act
(§4) still stands as the substantive gate. No bounded evidence packet is
required: no provider, no network, no licensing — every input is already
in-tree. Expected shape: MATERIAL packet (small — schema + seeded draft
content marked unratified) → Codex packet review + exact-head confirmation
→ Dustin design-direction + content ratification path → Stage-0 PRD →
review → Gate A. Lane: STANDARD (no HIGH-RISK file is touched — renderer
and runtime stay out), MATERIAL classification notwithstanding.

## 12. PARALLELISM

Safely parallel, no file collisions:
- **Cloudflare/Morning Brief E1/E2 + packet:** touches runtime/, delivery/,
  .github/workflows/cuttingboard.yml, cloudflare/ — disjoint from this
  lane's data/, tools/, tests/, ci.yml. The single shared file is
  `.github/workflows/ci.yml` (this lane adds one validator line; the brief
  arc does not touch ci.yml) — no real collision; Dustin's serialized
  merges resolve any trivial overlap.
- **Bounded GEX decision/evidence:** no files; fully parallel. If GEX-1
  ever wants registry symbols, it consumes a ratified version later.
- **Card real-use observation:** no files; fully parallel.

Serialize only: R2 consumer-adoption PRDs against anything else touching
the same consumer files (renderer/payload single-owner rule) — out of
scope here anyway.

## 13. OWNER DECISIONS REQUIRED (minimum set)

1. **D1 — Universe membership:** which symbols enter the ratified context
   universe beyond the 6-tuple seeds — the rest of ALL_SYMBOLS? the
   watchlist's 11? COIN/MSTR/PAAS/USO/IWM? SMCI (currently used in regime
   scoring but absent from every universe table)?
2. **D2 — Theme vocabulary + axis semantics:** ratify the theme list and
   rule the axis separation of the Ledger's six groups (Energy, AI/Semis →
   themes; Tradeable/Context → classification; Holdings, Spec/Learning →
   include as roles in v1, defer, or drop?).
3. **D3 — Benchmark semantics:** what `benchmark` means (NS-4C leadership
   comparison target), and the actual assignments (e.g. SPY for high-beta
   names? none for SPY itself?).
4. **D4 — NEWS-0 satisfaction:** confirm NEWS-0 is formally satisfied by
   this registry + the news-schema proposal doc; decide whether sources
   are ratified now (name them) or deferred (news track stays gated).
5. **D5 — Schema minimality confirmations:** defer pairwise relationships,
   horizons, questions (recommended); include sparse aliases in v1
   (recommended)?
6. **D6 — Watchlist direction:** confirm the watchlist tuple's content is
   absorbed as seed material now, with sidecar retirement deferred to R2/R3
   (no execution in this slice).

## 14. RECOMMENDED NEXT ACTION

**Commission the MATERIAL packet draft now** (design-class model): schema
spec + the seeded draft registry content (every non-seed element marked
unratified) + the news-schema proposal doc, built to make D1–D6 answerable
as bounded choices rather than open questions. No evidence/recon phase is
needed first — all inputs are in-tree and this packet's recon is current.
Then: Codex packet review → Dustin's design-direction + ratification
rulings → Stage-0 PRD → implementation (mechanical: loader + validator +
CI line + tests — a genuine Ultracode sprint once the packet freezes the
schema).

**Hidden dependencies found:** contract.py/payload.py's duplicated
`_OPTIONAL_MACRO_DRIVERS` (pre-existing, adjacent — a future R2/cleanup
candidate, not this slice); SMCI's universe-coverage gap (regime uses a
symbol the fetch/bounds tables don't know — surfaced for D1, possibly its
own tiny corrective PRD); negative-assertion tests pinning zero-consumer
lists (deletion in R3 must retire them deliberately).

**Likely cuts:** INDICES/COMMODITIES/HIGH_BETA and REQUIRED_SYMBOLS
(zero-production-consumer vocabulary); horizons/questions fields; the
watchlist tuple (after R2); one twin 6-tuple (after R2).

**Duplicate concepts that should disappear (eventually):** twin 6-tuples →
one registry group; watchlist taxonomy vs config axis lists → one ratified
theme vocabulary; NON_TRADABLE_SYMBOLS-vs-MACRO_DRIVERS double name →
registry `classification` (R2 decision).

**Sequencing risks:** (a) schema churn after consumers adopt — mitigated
by ratifying schema+content BEFORE any R2 adoption; (b) heatmap pressure
to widen the schema mid-flight — mitigated by the reserved-section rule
and amendment path; (c) a future news PRD drafting its own registry —
mitigated by the §5 canonical-pointer closeout; (d) drafting content
without D2's axis ruling wastes a ratification round — ask D2 first.

**Lightweight vs product reasoning:** lightweight agents were sufficient
for the entire §1 duplication/consumer inventory and the conventions
survey (all mechanical greps and reads); product reasoning was required
for the axis-conflation finding in the Ledger groups, the
decision-config-vs-context authority boundary (§1/§10), the
NEWS-0 split (§5), and the ratification mechanics (§4) — none of which a
grep can settle.

**Held:** PRD number, Gate A, all implementation, registry content
authority (nothing here is ratified), consumer migration, deletions.
