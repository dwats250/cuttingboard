# CUTTINGBOARD — Context Registry + NEWS-0 Consolidation: Planning Packet

PLANNING ONLY. No implementation, no PRD allocated, no Gate A, no PR beyond
the planning commits. Prepared for Dustin + ChatGPT review. Recon basis:
`main` lineage at `7d0805ee`; 3 narrow read-only recon agents + direct
reads; load-bearing claims cite files. Normalized 2026-08-08 to the common
14-section packet structure; two over-decided points (benchmark v1
inclusion, theme-axis outcome) demoted back to explicit owner decisions per
the normalization pass.

**PLANNING DISPOSITION (2026-08-08): DRAFT COMPLETE — HELD FOR OWNER
REVIEW. Not implementation-ready until owner rulings (REG-D1–REG-D7) and
GOV-2 MATERIAL intake close.**

**READINESS: MATERIAL-PACKET-READY.** (The MATERIAL packet draft can be
commissioned now — no evidence phase is needed; every input is in-tree.
See §13.)

**Core hypothesis verdict: CONFIRMED.** The "context registry" and NEWS-0's
registry half are ONE deliverable. This is already standing owner
direction: TRUTH-SYNC ruling 6 (DECISIONS.md:233-237) names the fused
"Registry (NS-4A universe + NEWS-0 relationship)" with seeds
(`config.TREND_STRUCTURE_SYMBOLS`, `market_map.PRIMARY_SYMBOLS`, the
Ledger's suggested groups), agent-drafted, Dustin-ratified, "No symbol or
source is inferred." The Product-Delivery Operating Rule's lane 3 is
"Context registry → news and heatmap." This packet shapes that direction
into a contract; it does not re-decide it.

---

## 1. PURPOSE / USER VALUE

The registry is CuttingBoard's single, interpretable, hand-auditable
statement of *what Dustin watches and how those things relate*: canonical
identity, classification, themes, watch reasons, and (per owner rulings)
benchmark assignments and later typed relationships. It is static,
versioned, owner-ratified data — the shared substrate the North Star names
for watchlists, news, heatmap, leadership/decoupling, and external
mirroring (NS-4/NS-6/NS-7, Ledger:151-208).

Hard properties: descriptive and deterministic; hand-editable and
diff-reviewable; every element beyond the ruling-6 seeds explicitly
ratified; no scoring engine, no prediction, no automated ontology
generation, no fuzzy/AI relationship inference at runtime. Consumers read
it; nothing computes it. **It is descriptive context authority, never
decision authority.**

## 2. CURRENT TRUTH (duplication map)

**At least five separately-maintained universe concepts exist** (verified,
consumers greped):

| Vocabulary | Members | Metadata | Production consumers |
|---|---|---|---|
| `config.MACRO_DRIVERS` (:198) = `NON_TRADABLE_SYMBOLS` (:199, same set, second name) | 7 | none | contract.py, regime.py (breadth), universe.py, trade_decision.py, runtime |
| `config.INDICES` / `COMMODITIES` / `HIGH_BETA` (:200-202) | 3 / 6 / 7 | none | **ZERO** — test-only negative assertions; live only via `ALL_SYMBOLS` concatenation |
| `config.ALL_SYMBOLS` (:204) | 23 | none | ingestion fetch loop, regime breadth, runtime filter |
| `config.REQUIRED_SYMBOLS` (:205) | 6 | none | **ZERO** production consumers (test-only) |
| `config.TREND_STRUCTURE_SYMBOLS` (:209, PRD-110) | 6 | none | trend_structure writer, dashboard renderer |
| `market_map.PRIMARY_SYMBOLS` (:20) | **identical 6, identical order** | none | market_map builder |
| `watchlist_sidecar.WATCHLIST_SYMBOLS` (:27-39, PRD-114) | 11 | (symbol, sector_theme, watch_reason) | **ZERO** modules — human-reader-only sidecar by explicit ruling (DECISIONS 2026-05-22) |
| `config.EXPANSION_LEADERSHIP_SYMBOLS` (:142) | 5 (incl. **SMCI**) | none | regime.py:120 (EXPANSION detection — decision logic) |

Supporting facts:
- The twin 6-tuples are byte-identical, independently declared, no import
  relationship — the flagship consolidation target and exactly the pair
  ruling 6 names as seeds.
- `contract.py:64` and `payload.py:318-336` each declare their own
  `_OPTIONAL_MACRO_DRIVERS` with a keep-aligned comment — an unenforced
  duplicate. **NAMED DEBT — not fixed in this lane.**
- **SMCI** appears in NO universe/bounds/units table while regime scoring
  uses it. **NAMED DEBT, graduated out of this lane** — surfaced to
  REG-D1 as a membership question only; any fix is separate corrective
  work.
- Watchlist taxonomy ('Index'/'Commodities'/'High beta') parallels
  config's axis lists but membership diverges (COIN, MSTR, PAAS, USO, IWM
  absent from the watchlist).
- The only relationship structure in code is the hardcoded GLD/DXY
  correlation pair (`config.py:271-276`) — decision logic, not context.
- No alias, benchmark, or grouping structure exists anywhere (verified).

**Pre-authorized seeds (ruling 6):** the identical 6-tuple and the
Ledger's suggested groups (Context, Energy, AI/Semis, Tradeable,
Spec/Learning, Holdings). **Candidate seeds (drafting input only;
ratification required):** ALL_SYMBOLS membership; the watchlist's 11
metadata rows; MACRO_DRIVERS as classification input.

**Must NOT become authority automatically:** decision/pipeline
configuration — `HALT_SYMBOLS`, `PRICE_BOUNDS`, `SYMBOL_UNITS`,
`SYMBOL_SOURCE_PRIORITY`, `NON_TRADABLE_SYMBOLS`' tradability gate,
`EXPANSION_LEADERSHIP_SYMBOLS`, the correlation pair. These encode
pipeline behavior, not context; absorbing them would make the registry a
decision surface. Zero-consumer config lists are drafting inputs at most
(likely cuts, §14). The Ledger's six groups conflate at least three axes
(sector-theme / role-status / personal intent) and are NOT adopted
verbatim — axis semantics are REG-D2's ruling to make.

## 3. UNRESOLVED LOOP

What keeps this lane open right now:
- **Owner rulings REG-D1–REG-D7** (§5): universe membership, theme-axis
  semantics, benchmark v1 inclusion + semantics, NEWS-0 satisfaction and
  source ratification, schema minimality, watchlist direction, canonical
  file/schema shape. None are pre-decided here; the schema below is a
  PROPOSAL throughout.
- **GOV-2 §1 MATERIAL intake classification** (recommendation §11; the
  mechanical classification happens at intake).
- No evidence gap exists — all inputs are in-tree.

## 4. SMALLEST NEXT SLICE (R1)

**R1 — registry creation only:** canonical static registry (content
drafted from seeds, every non-seed element marked unratified) + read-only
loader + CI-gate validator + the NEWS artifact-schema proposal doc. **ZERO
consumer migration.** Old vocabularies remain authoritative for all
existing behavior. R2 (bounded per-consumer adoption) and R3 (delete
duplicates only once actually unreferenced) are later, separate work (§13
sequencing).

### 4.1 Proposed minimal contract (all of it pending REG-D rulings)

One versioned, hand-authored JSON file (proposed path
`data/context_registry.json` — the `data/red_folder_2026.json`
hand-authored-input precedent; **final canonical file/schema shape is
REG-D7, not settled here**), strict keys, canonically sorted:

- **`meta`**: `schema_version`, `content_version`, ratification record
  (date + DECISIONS pointer). Ratification is file-version-level — one
  owner act per content version.
- **`themes`**: the ratified theme vocabulary (names + one-line meaning).
  **PROPOSED to be axis-separated** — sector-subject themes (Energy,
  AI/Semis, …) kept distinct from role/status tags — **pending REG-D2;
  not yet ratified, and REG-D2 may rule otherwise.**
- **`symbols[]`**, each: `symbol` (canonical in-repo provider ticker),
  `classification` (`tradeable` | `context_only`), `themes[]` (⊆ ratified
  vocabulary), `watch_reason` (short free text, seeded from the
  watchlist), `state` (`active` | `dormant`), `aliases[]` (optional,
  sparse; news matching motivation — REG-D5), `provenance` (`seed` |
  `ratified_addition`), and — **only if REG-D3a rules it into v1** — a
  `benchmark` reference (must reference a registry symbol, non-self).
- **`sources[]`** (NEWS-0's approved-source allowlist): `name`, `domain`,
  `enabled`, `reason`. Section present from v1; content ratified per
  REG-D4 — an empty ratified-sources list truthfully means the news track
  remains content-gated.

**Deliberately deferred (cuts until a consumer demands them):** pairwise
typed relationships / "related companies" (reserved section name recorded
in the schema doc so no competing structure appears later); personal-
status roles (Holdings, Spec/Learning) unless REG-D2 rules them into
canonical context; `horizons` and `questions` (NS-4A fields with no
near-term consumer); any numeric fields (bounds, weights, scores —
config-owned or forbidden).

This is the smallest shape that unlocks both dependents: the heatmap needs
universe + themes + deterministic order (benchmark only for the later
leadership mode — the timing trade is exactly REG-D3a); news needs
universe + aliases + themes + sources.

## 5. OWNER DECISIONS REQUIRED

1. **REG-D1 — Universe membership:** which symbols enter the ratified
   context universe beyond the 6-tuple seeds — the rest of ALL_SYMBOLS?
   the watchlist's 11? COIN/MSTR/PAAS/USO/IWM? SMCI (used in regime
   scoring, absent from every universe table — membership question only;
   the coverage gap itself is named debt outside this lane)?
2. **REG-D2 — Theme vocabulary + axis semantics:** ratify the theme list
   and rule the axis question for the Ledger's six groups — adopt the
   proposed axis separation, collapse to one flat grouping, or something
   else; and whether personal/status roles (Holdings, Spec/Learning)
   belong in canonical context at all.
3. **REG-D3a — Whether `benchmark` belongs in v1 at all** (defer like
   relationships/roles, or include now to spare a schema amendment before
   NS-4C/NS-7). **REG-D3b — if included:** benchmark semantics (NS-4C
   leadership comparison target) and the actual assignments.
4. **REG-D4 — NEWS-0 satisfaction semantics:** confirm NEWS-0 is formally
   satisfied by this registry + the news-schema proposal doc; decide
   whether sources are ratified now (name them) or deferred (news track
   stays gated).
5. **REG-D5 — Schema minimality confirmations:** defer pairwise
   relationships, horizons, questions (recommended); include sparse
   aliases in v1 (recommended)?
6. **REG-D6 — Watchlist direction:** confirm the watchlist tuple's content
   is absorbed as seed material now, with sidecar retirement deferred to
   R2/R3 (no execution in this slice).
7. **REG-D7 — Final canonical file/schema shape:** location (proposed
   `data/context_registry.json`), format (proposed JSON), and section
   layout — proposal only until ruled.

## 6. DEPENDENCIES

- The MATERIAL packet draft benefits from REG-D2 first (drafting content
  without the axis ruling risks a wasted ratification round) but can be
  built to present REG-D1–REG-D7 as bounded choices.
- Ratification mechanism: Dustin's merge of the content-carrying PR is the
  ratifying act (GOV-1), recorded with a dated DECISIONS entry naming the
  ratified `content_version`.
- Heatmap (NS-4B) depends on: ratified universe with `active`/`dormant`
  state; theme membership; deterministic canonical ordering (no rank
  implication — the watchlist's R14 rule carries over); `classification`.
  NS-4C/NS-7 additionally depend on benchmark (REG-D3a decides when that
  arrives). The heatmap needs NO pairwise relationships.
- News (NEWS-1+) depends on: ratified universe, aliases, themes, and a
  ratified non-empty sources list (REG-D4).
- No dependency on the Morning Brief arc, GEX, or Market Map work.

## 7. PARALLEL-SAFE WORK

Fully parallel, no file collisions: Morning Brief CF-E1/CF-E2 work and
packet (runtime/, delivery/, workflows, cloudflare/ — disjoint from this
lane's data/, tools/, tests/); the bounded GEX owner decision (no files);
real-use Market Control Card observation (no files). The single shared
file is `.github/workflows/ci.yml` (this lane adds one validator line;
the Morning Brief arc does not touch ci.yml) — trivial, resolved by
Dustin's serialized merges. Must serialize: R2 consumer-adoption PRDs
against anything touching the same consumer files — out of scope here.

## 8. SCOPE WALLS (this lane does NOT include)

News ingestion or any network producer; headline ranking; AI
summarization; sentiment or any LLM-derived label; GEX; heatmap
implementation; Market Map retirement; scheduler work; decision-contract
changes; automatic trading implications; automated relationship discovery
or AI ontology inference; absorption of decision/pipeline config
(HALT_SYMBOLS, PRICE_BOUNDS, SYMBOL_UNITS, SYMBOL_SOURCE_PRIORITY,
EXPANSION_LEADERSHIP_SYMBOLS, correlation pair — outside the registry
unless separately ruled); any dashboard surface or payload section; any
consumer migration (R2) or deletion (R3); pairwise relationship content;
fixing SMCI coverage or the `_OPTIONAL_MACRO_DRIVERS` duplicate (named
debt, separate corrective work if warranted).

## 9. FILE / SURFACE ESTIMATE

Honest ranges — validators and closed vocabularies counted as first-class
(the PRD-288: 195→308→amended 325 and PRD-289: 300→499→amended 525
estimate-miss lesson):

| Surface | Path (proposed, REG-D7) | Est. |
|---|---|---|
| Canonical registry (hand-authored, versioned JSON) | `data/context_registry.json` | content, not LOC |
| Read-only loader (frozen dataclasses, fail-loud — `red_folder.py` pattern) | `cuttingboard/context_registry.py` (new) | 80–160 |
| CI-gate validator (standalone, bare CI step before pytest — `validate_prd_registry.py` precedent) | `tools/validate_context_registry.py` (new) + one `.github/workflows/ci.yml` line | 120–220 |
| Tests | `tests/test_context_registry.py` (loader + validator + determinism + mutation scaffolding) | 250–450 |
| Docs | NEWS-0 news-schema proposal doc; DECISIONS ratification entry; PROJECT_STATE row at PRD time. artifact_flow_map registration NOT required (static input, red_folder precedent) — stated in the PRD so the omission is a decision | n/a |

**Untouched:** `config.py` lists, `market_map.py`, `watchlist_sidecar.py`,
`trend_structure`, renderer, payload, runtime, regime — every current
consumer keeps its vocabulary until R2.

## 10. TEST / FALSIFICATION PLAN

Validator (CI gate) + loader tests; every guard ships a red test (PRD-198
#4); mutation targets marked (M):
- duplicate canonical symbols; duplicate aliases; alias colliding with a
  canonical symbol (M: drop each dedup check → seeded-duplicate fixture
  turns red);
- `benchmark` (if REG-D3a includes it) must reference an existing,
  non-self registry symbol (M: remove referent check → unknown-target
  fixture red; deeper cycle rules NOT added — no v1 computation follows
  benchmark chains, so a cycle invariant would be complexity without an
  invariant);
- every `themes[]` entry ∈ ratified vocabulary; every enum
  (`classification`, `state`, `provenance`) ∈ its closed set (M: widen an
  enum → red);
- strict-key schema: unknown keys rejected (M: accept unknown key →
  drift fixture red); `schema_version` exact-match;
- canonical ordering enforced (file sorted by symbol; sections sorted) —
  deterministic diffs, no rank implication (M: remove sort check →
  shuffled fixture red);
- sources: duplicate domains, `enabled` boolean, non-empty `reason` (M
  per check);
- consumer-independent: validator + loader run green with zero consumers
  — the slice's definition of done;
- ratification representation: `content_version` + provenance vocabulary
  validated; a `ratified_addition` row in an unratified content version is
  a validator error (M: drop the check → silent-authority fixture red);
- loader: fail-loud on missing/malformed file — no substitute-and-continue
  (PRD-198 #1; M: add a silent default → red).

## 11. MATERIALITY / GOVERNANCE PATH

**MATERIAL recommended — no evidence packet needed.** The slice mints
canonical, owner-ratified product authority (universe and theme semantics
ARE product semantics) and a schema that three future lanes (news,
heatmap, NS-7 decoupling) depend on — a shared seam whose misdesign
propagates. The mechanical GOV-2 §1 classification at intake makes the
final call; if it returns non-MATERIAL, the owner-ratification act still
stands as the substantive gate. No provider, no network, no licensing —
every input is in-tree. Expected shape: MATERIAL packet (schema + seeded
draft content marked unratified + news-schema proposal) → Codex packet
review + exact-head confirmation → Dustin design-direction + ratification
rulings → Stage-0 PRD → independent review → Gate A. Lane: STANDARD (no
HIGH-RISK file touched — renderer and runtime stay out), MATERIAL
classification notwithstanding.

## 12. STOP CONDITIONS

**Boundary reset (stop, re-run GOV-2 classification / amend upstream):**
any consumer migration creeping into R1; any renderer/payload/runtime
file entering FILES; any decision-config list proposed for absorption;
any numeric/scoring field proposed for the schema; pairwise relationship
content arriving before its evidence-driven trigger; LOC growth past the
eventual Gate-A ceiling (GOV-2 §5).

**Lane stops entirely if:** Dustin declines to ratify any universe/theme
content (a registry with only unratified content has no consumers-to-be
and no purpose — park, don't build); or GOV-2 intake + owner ruling
redirect the deliverable's shape so materially (e.g. registry must carry
decision config after all) that the doctrine boundary (context-only)
breaks — that contradiction goes back to Dustin, not into the packet.

## 13. IMPLEMENTATION READINESS

**MATERIAL-PACKET-READY.** Not PRD-READY, not IMPLEMENTATION-READY: every
schema element is a proposal pending REG-D1–REG-D7, and content authority
is entirely unratified. The implementation itself (loader + validator +
CI line + tests) is mechanical once the packet freezes the schema — a
genuine Ultracode sprint — but readiness is not promoted on ease.

Sequential (hard order): REG-D2 (ideally first) → MATERIAL packet draft →
Codex cycle → Dustin rulings REG-D1–REG-D7 + design direction → Stage-0
PRD → review → Gate A → implementation → (later, separately) R2 adoption
→ R3 deletion. Intentionally deferred: pairwise relationships; roles;
horizons/questions; all consumer migration; all deletions.

## 14. RECOMMENDED NEXT COMMISSION

**Commission the MATERIAL packet draft now** (design-class model): schema
spec + seeded draft registry content (every non-seed element marked
unratified) + the news-schema proposal doc, built to make REG-D1–REG-D7
answerable as bounded choices. Asking REG-D2 (theme-axis) first avoids a
wasted ratification round. Then: Codex packet review → owner rulings →
Stage-0 PRD → implementation.

**Hidden dependencies (named debt, outside this lane):**
`contract.py`/`payload.py`'s duplicated `_OPTIONAL_MACRO_DRIVERS`; SMCI's
universe-coverage gap; negative-assertion tests pinning zero-consumer
lists (R3 must retire them deliberately).

**Likely cuts:** INDICES/COMMODITIES/HIGH_BETA and REQUIRED_SYMBOLS
(zero-production-consumer vocabulary); horizons/questions fields; the
watchlist tuple (after R2); one twin 6-tuple (after R2).

**Duplicate concepts that should disappear (eventually):** twin 6-tuples
→ one registry group; watchlist taxonomy vs config axis lists → one
ratified theme vocabulary; NON_TRADABLE_SYMBOLS-vs-MACRO_DRIVERS double
name → registry `classification` (an R2 decision).

**Sequencing risks:** schema churn after consumers adopt (mitigate:
ratify schema+content BEFORE any R2 adoption); heatmap pressure to widen
the schema mid-flight (mitigate: reserved-section rule + amendment path);
a future news PRD drafting its own registry (mitigate: canonical-pointer
closeout per §4.1/REG-D4); drafting content before REG-D2 (mitigate: ask
REG-D2 first).

**Lightweight vs product reasoning:** lightweight agents sufficed for the
entire §2 duplication/consumer inventory and conventions survey; product
reasoning was required for the axis-conflation finding, the
decision-config-vs-context authority boundary, the NEWS-0 split, and the
ratification mechanics.

**Held:** PRD number, Gate A, all implementation, registry content
authority (nothing here is ratified), consumer migration, deletions.
