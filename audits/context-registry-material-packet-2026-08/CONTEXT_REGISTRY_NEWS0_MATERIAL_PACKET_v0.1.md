# CUTTINGBOARD -- Context Registry + NEWS-0: MATERIAL Packet v0.1

MATERIAL PACKET. Planning/governance docs artifact only. No implementation,
no production code, no PRD number, no Gate A, no consumer migration, no PR
beyond the packet commit. Owner Dustin authorized this draft on 2026-08-08
and ruled REG-D2 (theme axis) on the same date; that ruling is recorded here
as SETTLED. All other owner decisions (REG-D1, REG-D3..REG-D7) are presented
as bounded choices and are NOT pre-decided.

- Recon basis: `main` at `7d0805ee66f7687f5360acfecfed9848a84d1f3c`
  (verified HEAD).
- Design authority: the planning packet
  `audits/reconciliation-2026-08/CONTEXT_REGISTRY_NEWS0_PLANNING_PACKET_2026-08-08.md`
  (reconciliation branch), `docs/plans/decision-support-expansion-doctrine-v0.1.md`
  section 5.4 (NEWS-0 construction gates),
  `docs/plans/decision-support-workplan-v0.1.md`, and TRUTH-SYNC ruling 6
  (`docs/DECISIONS.md:233-237`).
- Charge basis: read-only recon of the four cited source files at
  `main 7d0805e`; the only mutating act is authoring this packet on its own
  non-`main` branch. No source, contract, or `main` edit.
- Workplan state pointer (doctrine section 7): `HELD FOR DUSTIN DECISION`.
  This packet establishes no new queue; NEWS-0 remains the workplan/doctrine
  section 5.4 item and the Context Registry (NS-4A) fusion named by ruling 6.
- Landing hold (GOV-0 / GOV-1): any PR that later carries this work is opened
  as a DRAFT and manual-merged by Dustin. This packet is not that PR.

**READINESS: MATERIAL-PACKET DRAFT COMPLETE -- HELD FOR CODEX PACKET REVIEW
+ EXACT-HEAD CONFIRMATION, THEN OWNER RULINGS.** Not PRD-ready and not
implementation-ready: the schema is a PROPOSAL pending REG-D1/REG-D3..REG-D7,
and all content authority is unratified. Every input is in-tree; no evidence
phase is required.

**Core direction (not re-decided here):** the "context registry" and NEWS-0's
registry half are ONE deliverable. Standing owner direction: TRUTH-SYNC
ruling 6 names the fused Registry (NS-4A universe + NEWS-0 relationship) with
seeds (`config.TREND_STRUCTURE_SYMBOLS`, `market_map.PRIMARY_SYMBOLS`, the
Ledger's suggested groups), agent-drafted and Dustin-ratified, "No symbol or
source is inferred." This packet shapes that direction into a contract; it
does not re-decide it.

---

## 1. PURPOSE / USER VALUE

The registry is CuttingBoard's single, interpretable, hand-auditable
statement of *what Dustin watches and how those things relate*: canonical
identity, classification, sector/subject themes, watch reasons, and (per
owner rulings) benchmark assignments and later typed relationships. It is
static, versioned, owner-ratified data -- the shared substrate the North Star
names for watchlists, news, heatmap, leadership/decoupling, and external
mirroring.

Hard properties: descriptive and deterministic; hand-editable and
diff-reviewable; every element beyond the ruling-6 seeds explicitly ratified;
no scoring engine, no prediction, no automated ontology generation, no
fuzzy/AI relationship inference at runtime. Consumers read it; nothing
computes it. **It is descriptive context authority, never decision
authority.** Role/status metadata in particular is descriptive-only and must
never become decision configuration (REG-D2, section 5).

R1 delivers only the authority artifact plus its guardrails: the hand-authored
registry, a read-only loader, a CI-gate validator, and a NEWS-0 news-schema
proposal doc. R1 changes no existing behavior. The user value it unlocks is
downstream: heatmap (NS-4B) and news (NEWS-1+) can each read one canonical,
owner-ratified universe/theme/source substrate instead of re-deriving five
divergent ones.

## 2. CURRENT TRUTH (duplication map, verified at `main 7d0805e`)

At least five separately-maintained universe concepts exist; consumers greped
and line references re-confirmed at `7d0805e` (see the drift note at the end
of this section):

| Vocabulary | Members | Metadata | Production consumers |
|---|---|---|---|
| `config.MACRO_DRIVERS` (:198) = `NON_TRADABLE_SYMBOLS` (:199, same set, second name) | 7 | none | contract.py, regime.py (breadth), universe.py, trade_decision.py, runtime |
| `config.INDICES` / `COMMODITIES` / `HIGH_BETA` (:200-202) | 3 / 6 / 7 | none | ZERO -- test-only negative assertions; live only via `ALL_SYMBOLS` concat |
| `config.ALL_SYMBOLS` (:204) | 23 | none | ingestion fetch loop, regime breadth, runtime filter |
| `config.REQUIRED_SYMBOLS` (:205) | 6 | none | ZERO production consumers (test-only) |
| `config.TREND_STRUCTURE_SYMBOLS` (:209, PRD-110) | 6 | none | trend_structure writer, dashboard renderer |
| `market_map.PRIMARY_SYMBOLS` (:20) | identical 6, identical order | none | market_map builder |
| `watchlist_sidecar.WATCHLIST_SYMBOLS` (:27-39, PRD-114) | 11 | (symbol, sector_theme, watch_reason) | ZERO modules -- human-reader-only sidecar (DECISIONS 2026-05-22) |
| `config.EXPANSION_LEADERSHIP_SYMBOLS` (:142) | 5 (incl. SMCI) | none | regime.py (EXPANSION detection -- decision logic) |

Supporting facts (re-verified at `7d0805e`):

- The twin 6-tuples are byte-identical (`("SPY","QQQ","GDX","GLD","SLV","XLE")`
  at `config.py:209` and `market_map.py:20`), independently declared, no
  import relationship -- the flagship consolidation target and exactly the
  pair ruling 6 names as seeds.
- `contract.py` and `payload.py` each declare their own
  `_OPTIONAL_MACRO_DRIVERS` with a keep-aligned comment -- an unenforced
  duplicate. **NAMED DEBT -- graduated out of this lane (section 14).**
- SMCI appears in NO universe/bounds/units table while `EXPANSION_LEADERSHIP_SYMBOLS`
  (`config.py:142`) uses it in regime scoring. **NAMED DEBT, graduated out of
  this lane** -- surfaced to REG-D1 as a membership question only; the
  coverage-gap fix is separate corrective work.
- Watchlist taxonomy (Index / Commodities / High beta) parallels config's axis
  lists but membership diverges: COIN, MSTR, PAAS, USO, IWM are absent from the
  11-row watchlist.
- The only relationship structure in code is the hardcoded GLD/DXY correlation
  pair (`config.py:271-276`) -- decision logic, not context.
- No alias, benchmark, or grouping structure exists anywhere (verified).

**Pre-authorized seeds (ruling 6, `DECISIONS.md:233-237`):** the identical
6-tuple `("SPY","QQQ","GDX","GLD","SLV","XLE")` and the Ledger's six suggested
groups (Context, Energy, AI/Semis, Tradeable, Spec/Learning, Holdings).
**Candidate seeds (drafting input only; ratification required):**
`ALL_SYMBOLS` membership; the watchlist's 11 metadata rows; `MACRO_DRIVERS`
as classification input.

**Must NOT become authority automatically:** decision/pipeline configuration
-- `HALT_SYMBOLS`, `PRICE_BOUNDS`, `SYMBOL_UNITS`, `SYMBOL_SOURCE_PRIORITY`,
`NON_TRADABLE_SYMBOLS`' tradability gate, `EXPANSION_LEADERSHIP_SYMBOLS`, the
correlation pair. These encode pipeline behavior, not context; absorbing them
would make the registry a decision surface (section 8). The Ledger's six
groups conflate at least three axes (sector-subject / role-status / personal
intent); they are NOT adopted verbatim -- axis semantics are REG-D2's ruling,
now made (section 5).

**Line-reference drift note:** all eight universe line references above, plus
`EXPANSION_LEADERSHIP_SYMBOLS` (:142), the correlation block (:271-276), and
ruling 6 (`DECISIONS.md:233-237`), were re-read at `main 7d0805e` and hold
byte-for-byte. No drift found; no corrected references required.

## 3. UNRESOLVED LOOP

What keeps this lane open right now:

- **Owner rulings REG-D1 and REG-D3..REG-D7** (section 5): universe
  membership, benchmark v1 inclusion + semantics, NEWS-0 satisfaction and
  source ratification, schema minimality, watchlist direction, canonical
  file/schema shape. None are pre-decided here; the schema below is a PROPOSAL
  throughout. REG-D2 (theme axis) is already ruled and is recorded as SETTLED.
- **GOV-2 packet cycle:** this packet awaits Codex packet review plus
  independent SHA-pinned confirmation of the exact corrected head before a
  design-direction ruling and Stage-0 PRD drafting (section 11).
- No evidence gap exists -- all inputs are in-tree.

## 4. SMALLEST NEXT SLICE (R1)

**R1 -- registry creation only:** canonical static registry (content drafted
from seeds, every non-seed element marked unratified) + read-only loader +
CI-gate validator + the NEWS-0 news-schema proposal doc. **ZERO consumer
migration.** Old vocabularies remain authoritative for all existing behavior.

- **R2 (bounded per-consumer adoption)** and **R3 (delete duplicates only once
  actually unreferenced)** are later, separate work -- OUT OF SCOPE for this
  packet (section 8, section 13).

### 4.1 Proposed minimal contract (all of it pending REG-D rulings)

One versioned, hand-authored JSON file (proposed path
`data/context_registry.json` -- the `data/red_folder_2026.json`
hand-authored-input precedent; **final canonical file/schema shape is REG-D7,
not settled here**), strict keys, canonically sorted:

- **`meta`**: `schema_version` (exact-match string), `content_version`,
  ratification record (date + `DECISIONS.md` pointer). Ratification is
  file-version-level -- ONE owner act per content version, and that act is
  Dustin's merge of the content-carrying PR (GOV-1).

- **`themes`**: the ratified sector/subject theme vocabulary (names + one-line
  meaning). **AXIS-SEPARATED per REG-D2 (SETTLED, section 5):** this array
  carries ONLY sector/subject themes (Energy, AI/Semis, ...). Role/status tags
  never appear here. The specific vocabulary is UNRATIFIED and presented for
  content ratification (section 5, REG-D2 note).

- **`symbols[]`**, each:
  - `symbol` -- canonical in-repo provider ticker.
  - `classification` -- closed enum `tradeable | context_only`. Descriptive
    mirror only; the tradability GATE stays in `config.NON_TRADABLE_SYMBOLS`
    and is NOT absorbed (section 8).
  - `themes[]` -- subset of the ratified sector/subject vocabulary
    (`themes`). Sector/subject axis only.
  - `watch_reason` -- short free text, seeded from the watchlist.
  - `state` -- closed enum `active | dormant`.
  - `aliases[]` -- optional, sparse (news-matching motivation; include-in-v1
    is REG-D5).
  - `provenance` -- closed enum `seed | candidate_seed | ratified_addition`
    (see the note below).
  - `benchmark` -- **CONDITIONAL on REG-D3a; NOT pre-included.** Present only
    if REG-D3a rules it into v1; if present, must reference an existing,
    non-self registry symbol (REG-D3b sets semantics + assignments).

- **`sources[]`** (NEWS-0's approved-source allowlist): `name`, `domain`,
  `enabled` (boolean), `reason` (non-empty). Section present from v1; content
  ratified per REG-D4 -- an empty ratified-sources list truthfully means the
  news track remains content-gated.

**Provenance closed set (proposed extension, REG-D5-adjacent).** The planning
packet proposed `seed | ratified_addition`. To honestly carry ruling 6's
seed-vs-candidate distinction, this packet proposes a three-value closed set:
- `seed` -- ruling-6 pre-authorized content: the 6-tuple symbols and the six
  Ledger group names. No owner act required. The ruling-6 GROUP-NAME seed
  authority is carried by this packet and the `DECISIONS.md` ratification
  record, NOT by the schema (a group name is not a schema field). Seed-coverage
  map: `Context`/`Tradeable` -> classification values; `Energy`/`AI/Semis` ->
  theme ids; `Holdings`/`Spec/Learning` -> reserved role vocabulary.
- `candidate_seed` -- drafting input requiring ratification: `ALL_SYMBOLS`
  membership, the watchlist's 11 rows, `MACRO_DRIVERS` as classification
  input. Becomes `ratified_addition` only upon owner ratification.
- `ratified_addition` -- anything added and ratified beyond the seeds.
The validator enforces that a `ratified_addition` cannot appear in a content
version whose `meta` ratification record is absent/incomplete (section 10).

**REG-D2 role/status axis is RESERVED, not populated in v1.** Per the ruling
(section 5), IF personal/status roles (Holdings, Spec/Learning) ever enter the
registry, they occupy a DISTINCT role/status dimension -- one reserved section
name, `roles` (proposed, UNRATIFIED), recorded in the schema doc -- never
flattened into `themes[]`, and never read as decision configuration. A single
reserved name (not an either/or) is deliberate: it forecloses a competing role
structure appearing later. Whether role content
actually populates v1 is deferred (REG-D5). The reserved-section note exists so
no competing role structure appears later.

**Deliberately deferred (cuts until a consumer demands them), each recorded as
a reserved section name so no competing structure appears later:** pairwise
typed relationships / "related companies"; the role/status dimension above
(roles-as-content); `horizons` and `questions` (NS-4A fields with no near-term
consumer); any numeric fields (bounds, weights, scores -- config-owned or
forbidden, section 8).

This is the smallest shape that unlocks both dependents: the heatmap needs
universe + themes + deterministic order (benchmark only for the later
leadership mode -- the timing trade is exactly REG-D3a); news needs universe +
aliases + themes + sources.

## 5. OWNER DECISIONS REQUIRED

**REG-D2 -- Theme axis semantics: RULED 2026-08-08.** The owner ruling is
recorded verbatim below so the GOV-2 packet review can verify this packet's
encoding against the ruling text in-tree. The schema encoding that follows the
ruling is THE PACKET'S PROPOSAL, consistent with the ruling but not itself
ruled.

> **Owner ruling REG-D2, 2026-08-08.**
> REG-D2 -- THEME AXIS. RULING: Option (a) -- KEEP SECTOR/SUBJECT THEMES
> DISTINCT FROM ROLE/STATUS TAGS. Personal/status roles such as Holdings and
> Spec/Learning MAY belong in canonical context, but they must remain a
> distinct role/status dimension rather than being flattened into the same
> semantic axis as sector/subject themes. The MATERIAL packet should present
> the exact v1 vocabulary for later owner ratification. Do not let role/status
> metadata become decision configuration. REG-D1 and REG-D3..D7 remain
> deferred to the drafted MATERIAL packet.

**What the ruling SETTLES -- exactly three propositions (SETTLED 2026-08-08):**

- (i) Sector/subject themes stay DISTINCT from role/status tags (the two are
  never flattened onto one semantic axis).
- (ii) Roles such as Holdings and Spec/Learning MAY belong in canonical
  context, but only as a distinct role/status dimension.
- (iii) Role/status metadata NEVER becomes decision configuration.

The ruling does NOT settle a "three-axis model" and does NOT rule the
classification enum. Everything below is THE PACKET'S PROPOSED encoding,
consistent with (i)-(iii) and pending the bounded REG-D choices.

**Packet-proposed encoding (PROPOSAL, not settled).** The registry expresses
(i)-(iii) as a descriptive model with these dimensions:

1. **Classification** (proposed closed enum `tradeable | context_only`) --
   PROPOSAL pending REG-D5/REG-D7; the ruling does not require it. Descriptive
   mirror only; the tradability gate stays in config.
2. **Sector/subject theme axis** (`themes[]`) -- carries only descriptive
   subject matter (Energy, AI/Semis, ...); what the heatmap groups by and news
   matches on. Kept DISTINCT from role/status tags per settled (i).
3. **Role/status axis** -- a DEFERRED reserved section: the section NAME is
   recorded now, content is unpopulated, and whether roles actually enter the
   registry in v1 is REG-D5's open choice. If populated, roles occupy this
   distinct dimension per settled (ii), never flattened into `themes[]`, and
   per settled (iii) are never read as decision configuration (permanent scope
   wall, section 8).

Mapping the Ledger's six suggested groups onto this proposed encoding:
`Context` and `Tradeable` -> proposed classification values; `Energy` and
`AI/Semis` -> proposed theme ids; `Holdings` and `Spec/Learning` -> proposed
reserved role vocabulary. The group-name seed authority is carried by this
packet and the `DECISIONS.md` record, not the schema (section 4.1). What
remains for owner content ratification is the vocabulary LIST on each
dimension, presented next as an UNRATIFIED proposal.

**PROPOSED v1 sector/subject theme vocabulary (UNRATIFIED -- content
ratification rides the merge; per-symbol assignment is coupled to REG-D1).**
Marked UNRATIFIED in full:

| Theme (proposed id) | One-line meaning | Seed/candidate members (UNRATIFIED) |
|---|---|---|
| `broad_market` | Index-level market reference | SPY, QQQ; IWM conditional on REG-D1 |
| `precious_metals` | Gold/silver spot and miners | GLD, SLV, GDX; PAAS, GC=F, SI=F conditional on REG-D1 |
| `energy` | Energy sector and crude complex | XLE; USO, CL=F conditional on REG-D1 |
| `ai_semis` | AI and semiconductor bellwethers | NVDA; SMCI conditional on REG-D1 (membership only) |
| `mega_cap_tech` | Large-cap technology | AAPL, META, AMZN |
| `crypto_proxy` | Crypto and crypto-linked equities | BTC-USD; COIN, MSTR conditional on REG-D1 |
| `rates_fx_vol` | Macro rates, FX, and volatility drivers | ^VIX, DX-Y.NYB, ^TNX |

Open per-symbol assignment example (UNRATIFIED): TSLA (`watch_reason`
"retail-flow signal") is a candidate for `mega_cap_tech` or a distinct
autos/EV subject; REG-D2 content ratification resolves it. Nothing above is a
role/status tag.

MACRO_DRIVERS candidate-seed coverage (so REG-D1 rules from a complete
picture): all seven `config.MACRO_DRIVERS` (`config.py:198`) map to a theme
row -- `^VIX`, `DX-Y.NYB`, `^TNX` -> `rates_fx_vol`; `BTC-USD` ->
`crypto_proxy`; `CL=F` -> `energy`; `GC=F`, `SI=F` -> `precious_metals`. As
MACRO_DRIVERS members their proposed `classification` is `context_only`; all
seven remain REG-D1-conditional universe members (theme assignment does not
pre-decide membership).

**PROPOSED role/status axis vocabulary (RESERVED; content deferred per REG-D5;
UNRATIFIED):** `holding` (a personal portfolio position), `spec_learning` (a
speculative or learning-only watch). Descriptive-only; never decision config;
never in `themes[]`. Populated only if owner later ratifies role content.

The remaining owner decisions are BOUNDED CHOICES and are NOT pre-decided:

1. **REG-D1 -- Universe membership.** Which symbols enter the ratified context
   universe beyond the 6-tuple seeds: the rest of `ALL_SYMBOLS`? the
   watchlist's 11? COIN / MSTR / PAAS / USO / IWM? SMCI (used in regime
   scoring, absent from every universe table -- membership question only; the
   coverage-gap fix is named debt outside this lane, section 14)?
2. **REG-D3a -- Whether `benchmark` belongs in v1 at all** (defer like
   relationships/roles, or include now to spare a schema amendment before
   NS-4C/NS-7). **REG-D3b -- if included:** benchmark semantics (NS-4C
   leadership comparison target) and the actual assignments.
3. **REG-D4 -- NEWS-0 satisfaction semantics.** Confirm NEWS-0 is formally
   satisfied by this registry + the news-schema proposal doc; decide whether
   sources are ratified now (name them) or deferred (news track stays gated).
4. **REG-D5 -- Schema minimality confirmations.** Defer pairwise relationships,
   the role/status content axis, horizons, questions (recommended); include
   sparse `aliases` in v1 (recommended)? Confirm the three-value provenance
   closed set (section 4.1) or reduce it.
5. **REG-D6 -- Watchlist direction.** Confirm the watchlist tuple's content is
   absorbed as seed material now, with sidecar retirement deferred to R2/R3 (no
   execution in this slice).
6. **REG-D7 -- Final canonical file/schema shape.** Location (proposed
   `data/context_registry.json`), format (proposed JSON), and section layout --
   proposal only until ruled.

## 6. DEPENDENCIES

- The packet is best drafted with REG-D2 first (now ruled), so content drafting
  does not risk a wasted ratification round; REG-D1 and REG-D3..REG-D7 are
  presented as bounded choices the owner rules after the packet cycle.
- Ratification mechanism: Dustin's merge of the content-carrying PR is the
  ratifying act (GOV-1), recorded with a dated `DECISIONS.md` entry naming the
  ratified `content_version`.
- Heatmap (NS-4B) depends on: ratified universe with `active`/`dormant` state;
  sector/subject theme membership; deterministic canonical ordering (no rank
  implication -- the watchlist's no-rank rule carries over); `classification`.
  NS-4C/NS-7 additionally depend on `benchmark` (REG-D3a decides when that
  arrives). The heatmap needs NO pairwise relationships.
- News (NEWS-1+) depends on: ratified universe, aliases, sector/subject themes,
  and a ratified non-empty `sources` list (REG-D4).
- No dependency on the Morning Brief arc, GEX, or Market Map work.

## 7. PARALLEL-SAFE WORK

Fully parallel, no file collisions: Morning Brief work and packet (runtime/,
delivery/, workflows, cloudflare/ -- disjoint from this lane's data/, tools/,
tests/); the bounded GEX owner decision (no files); real-use Market Control
Card observation (no files). The single shared file is
`.github/workflows/ci.yml` (this lane adds one validator line; the Morning
Brief arc does not touch ci.yml) -- trivial, resolved by Dustin's serialized
merges. Must serialize: R2 consumer-adoption PRDs against anything touching the
same consumer files -- out of scope here.

## 8. SCOPE WALLS (this lane does NOT include)

- **No decision-config absorption.** `HALT_SYMBOLS`, `PRICE_BOUNDS`,
  `SYMBOL_UNITS`, `SYMBOL_SOURCE_PRIORITY`, `NON_TRADABLE_SYMBOLS`' tradability
  gate, `EXPANSION_LEADERSHIP_SYMBOLS`, and the GLD/DXY correlation pair stay
  in config -- they encode pipeline behavior, not context. Absorbing any of
  them would make the registry a decision surface.
- **No role/status metadata as decision config.** The role/status axis
  (REG-D2) is descriptive-only, permanently. It is never read by any decision
  or sizing path.
- **No cross-validation of `classification` against
  `config.NON_TRADABLE_SYMBOLS`.** R1's validator does NOT assert that registry
  `classification` matches the config tradability gate. Divergence between the
  two is tolerable while R1 has zero consumers; authority reconciliation
  between the registry and config is the R2 decision the planning packet
  already names, not an R1 check. A validator that enforced parity now would
  silently couple the registry to decision configuration -- exactly the
  boundary this lane holds.
- **No renderer / payload / runtime files.** No dashboard surface, no payload
  section, no runtime/ change.
- **No numeric or scoring fields.** No bounds, weights, scores, or any computed
  value in the schema.
- **No network / news producer.** No ingestion, no headline ranking, no AI
  summarization, no sentiment or LLM-derived label, no automated relationship
  discovery or AI ontology inference.
- **No consumer migration (R2) or deletion (R3).** Old vocabularies keep their
  authority; nothing is repointed or removed in this slice.
- **No GEX, heatmap implementation, Market Map retirement, scheduler,
  decision-contract change, or automatic trading implication.**
- **No fixing SMCI coverage or the `_OPTIONAL_MACRO_DRIVERS` duplicate** --
  named debt, separate corrective work (section 14).

## 9. FILE / SURFACE ESTIMATE

Honest ranges. Validators and closed vocabularies are counted as FIRST-CLASS
LOC, per the estimate-miss lesson (PRD-288: 195 -> amended 325; PRD-289:
300 -> amended 525): the validator and its closed-set checks are the bulk of
the work, not an afterthought.

| Surface | Path (proposed, REG-D7) | Est. |
|---|---|---|
| Canonical registry (hand-authored, versioned JSON) | `data/context_registry.json` (new) | content, not LOC |
| Read-only loader (frozen dataclasses, fail-loud -- `red_folder.py` pattern) | `cuttingboard/context_registry.py` (new) | 80-160 |
| CI-gate validator (standalone, bare CI step before pytest -- `validate_prd_registry.py` precedent) | `tools/validate_context_registry.py` (new) + one `.github/workflows/ci.yml` line | 120-220 |
| Tests | `tests/test_context_registry.py` (new; loader + validator + determinism + mutation-verified red tests) | 250-450 |
| NEWS-0 news-schema proposal doc | `docs/plans/news-0-schema-proposal-v0.1.md` (new; proposed path, REG-D7-adjacent -- final location confirmed with the schema shape) | content, not LOC |
| Bookkeeping (allowlist -- NOT counted against the LOC/FILES ceiling) | `DECISIONS.md` ratification entry; `PROJECT_STATE.md` row at PRD time. artifact_flow_map registration NOT required (static input, red_folder precedent) -- stated in the PRD so the omission is a decision | n/a |

**Untouched:** `config.py` lists, `market_map.py`, `watchlist_sidecar.py`,
`trend_structure`, renderer, payload, runtime, regime -- every current consumer
keeps its vocabulary until R2.

**FILES ceiling for the eventual Stage-0 PRD:** the FIVE new paths --
`data/context_registry.json`, `cuttingboard/context_registry.py`,
`tools/validate_context_registry.py`, `tests/test_context_registry.py`, and
`docs/plans/news-0-schema-proposal-v0.1.md` -- plus the one
`.github/workflows/ci.yml` validator line. `DECISIONS.md` and
`PROJECT_STATE.md` are bookkeeping-allowlist touches, NOT counted against that
ceiling. Any growth past the ceiling triggers a stop condition (section 12) and
the GOV-2 amended-PRD path.

## 10. TEST / FALSIFICATION PLAN

Validator (CI gate) + loader tests. Every guard ships a mutation-verified red
test (PRD-198 #4); the mutation that must turn the test red is annotated
`(M: ... -> red)`.

- Duplicate canonical symbols rejected. `(M: drop the canonical-dedup check ->
  seeded duplicate-symbol fixture -> red)`
- Duplicate aliases rejected. `(M: drop the alias-dedup check -> seeded
  duplicate-alias fixture -> red)`
- Alias colliding with a canonical symbol rejected. `(M: drop the
  alias-vs-canonical collision check -> collision fixture -> red)`
- Benchmark referent check, ONLY if REG-D3a includes `benchmark`: every
  `benchmark` references an existing, non-self registry symbol. `(M: remove the
  referent check -> unknown-target / self-reference fixture -> red)`. No deeper
  cycle rule is added -- no v1 computation follows benchmark chains, so a cycle
  invariant would be complexity without an invariant.
- Every `themes[]` entry is a member of the ratified sector/subject vocabulary.
  `(M: widen the membership check to allow an unknown theme -> off-vocabulary
  fixture -> red)`
- Every enum value in its closed set -- `classification` in
  `{tradeable, context_only}`, `state` in `{active, dormant}`, `provenance` in
  `{seed, candidate_seed, ratified_addition}`. `(M: widen any one enum -> out-
  of-set fixture -> red)`
- Strict-key schema: unknown keys rejected at every object level. `(M: accept
  unknown keys -> drift fixture with a stray key -> red)`
- `schema_version` exact-match against the loader's expected value. `(M: relax
  to prefix/substring match -> wrong-version fixture -> red)`
- Canonical ordering enforced: file sorted by symbol, sections sorted --
  deterministic diffs, no rank implication. `(M: remove the sort check ->
  shuffled fixture -> red)`
- Sources: duplicate domains rejected; `enabled` is boolean; `reason` is
  non-empty. `(M per check: drop dedup -> duplicate-domain fixture red; accept
  non-boolean enabled -> string-enabled fixture red; accept empty reason ->
  empty-reason fixture red)`
- Consumer-independent green: the validator and loader run green with ZERO
  consumers -- this is the slice's definition of done. `(M: none -- this is the
  positive acceptance test; it must pass with no consumer present)`
- Ratification / provenance representation: `content_version` + the provenance
  vocabulary are validated; a `ratified_addition` row in a content version
  whose `meta` ratification record is absent/incomplete is a validator error.
  `(M: drop the ratified-in-unratified-version check -> silent-authority
  fixture -> red)`
- Loader fail-loud on missing or malformed file -- no substitute-and-continue
  (PRD-198 #1). `(M: add a silent default / empty-registry fallback ->
  missing-file and malformed-JSON fixtures -> red)`
- Explicitly NOT tested in R1: parity between registry `classification` and
  `config.NON_TRADABLE_SYMBOLS`. R1 has zero consumers, divergence is
  tolerable, and reconciling the two authorities is the R2 decision
  (section 8). Coupling the validator to config now would silently bind the
  registry to decision configuration, so this check is deliberately absent (no
  mutation test -- there is no guard to falsify).

## 11. MATERIALITY / GOVERNANCE PATH

**MATERIAL recommended -- no evidence packet needed.** The slice mints
canonical, owner-ratified product authority (universe and theme semantics ARE
product semantics) and a schema that three future lanes (news, heatmap, NS-7
decoupling) depend on -- a shared seam whose misdesign propagates. The
mechanical GOV-2 section 1 classification at intake makes the final call; if it
returns non-MATERIAL, the owner-ratification act still stands as the
substantive gate. No provider, no network, no licensing -- every input is
in-tree.

**Lane: STANDARD.** No HIGH-RISK file is touched -- renderer and runtime stay
out (section 8). A MATERIAL slice is ineligible for `LANE: MICRO` (GOV-2
section 1): the required order includes a PRD, its independent review, and an
explicit Gate A, none of which MICRO contains. HIGH-RISK would apply only if
R11's own triggers fired, which they do not here.

**Expected shape (GOV-2):** this MATERIAL packet -> Codex packet review +
independent SHA-pinned confirmation of the exact corrected head -> Dustin
design-direction ruling + owner rulings REG-D1/REG-D3..REG-D7 -> Stage-0 PRD ->
fresh-context independent review -> Gate A -> implementation. Gate A remains the
later implementation authorization on the independently reviewed PRD; this
packet implies no Gate A.

## 12. STOP CONDITIONS

**Boundary reset (stop, re-run GOV-2 classification / amend upstream):** any
consumer migration creeping into R1; any renderer/payload/runtime file entering
FILES; any decision-config list proposed for absorption; any role/status field
proposed as decision input; any numeric/scoring field proposed for the schema;
pairwise relationship content arriving before its evidence-driven trigger; LOC
growth past the eventual Gate-A ceiling (GOV-2 section 5, requiring the
amended-PRD review).

**Lane stops entirely if:** Dustin declines to ratify any universe/theme
content (a registry with only unratified content has no consumers-to-be and no
purpose -- park, don't build); or GOV-2 intake + owner ruling redirect the
deliverable's shape so materially (e.g. the registry must carry decision config
after all) that the doctrine boundary (context-only) breaks -- that
contradiction goes back to Dustin, not into the packet.

## 13. IMPLEMENTATION READINESS

**MATERIAL-PACKET DRAFT COMPLETE.** Not PRD-READY, not IMPLEMENTATION-READY:
every schema element is a proposal pending REG-D1/REG-D3..REG-D7, and content
authority is entirely unratified. The implementation itself (loader + validator
+ CI line + tests) is mechanical once the packet freezes the schema, but
readiness is not promoted on ease.

Sequential (hard order): REG-D2 ruled -> this MATERIAL packet -> Codex packet
review + exact-head confirmation -> Dustin rulings REG-D1/REG-D3..REG-D7 +
design direction -> Stage-0 PRD -> independent review -> Gate A ->
implementation -> (later, separately) R2 adoption -> R3 deletion. Intentionally
deferred: pairwise relationships; the role/status content axis;
horizons/questions; all consumer migration; all deletions.

## 14. RECOMMENDED NEXT COMMISSION

**Commission the Codex packet review + exact-head confirmation now** (GOV-2
section 2, section 7): a read-only review of this MATERIAL packet against the
repository surfaces it cites, then independent SHA-pinned confirmation of the
exact corrected head after at most one bounded correction cycle. Then: Dustin
design-direction ruling + REG-D1/REG-D3..REG-D7 -> Stage-0 PRD -> independent
review -> Gate A.

**NAMED DEBT -- graduated OUT of this lane, never fixed in-lane (separate
corrective work):**
- `contract.py` / `payload.py` duplicated `_OPTIONAL_MACRO_DRIVERS` (unenforced
  keep-aligned duplicate).
- SMCI's universe-coverage gap: `EXPANSION_LEADERSHIP_SYMBOLS` (`config.py:142`)
  scores SMCI while it is absent from every universe/bounds/units table. In this
  lane it is reduced to a REG-D1 membership question only; the coverage fix
  itself is separate corrective work.
- Negative-assertion tests pinning zero-consumer config lists (R3 must retire
  them deliberately).

**Likely cuts (eventual, not this lane):** `INDICES`/`COMMODITIES`/`HIGH_BETA`
and `REQUIRED_SYMBOLS` (zero-production-consumer vocabulary); horizons/questions
fields; the watchlist tuple (after R2); one twin 6-tuple (after R2).

**Held:** PRD number, Gate A, all implementation, registry content authority
(nothing here is ratified), consumer migration, deletions.
