# CUTTINGBOARD OPPORTUNITY CONTINUITY MATERIAL DESIGN PACKET

| Field | Value |
|---|---|
| Status | **PROVISIONAL MATERIAL DESIGN PACKET — CURRENT-MAIN RECONCILED** |
| Prepared | 2026-08-23 |
| Current-main baseline | `044602770f745e322dc47a88e9bd342dc0955ce7` |
| PRD-314 merge | PR #275, merge commit `044602770f745e322dc47a88e9bd342dc0955ce7` |
| Deep-recon input | `4c85b01db2fefe7188015744afd847095fad596d` |
| Visual-research input | `85579e6b81fc40882bb137f5bdc8c0fe3c3d4816` |
| Packet branch | `docs/opportunity-continuity-material-design-packet` |

This packet reconciles the Opportunity-continuity deep recon to current main,
independently challenges its design, and defines the smallest truthful future
production boundary. It is not PRD-315, Gate A, implementation authority, or
merge authority. No prototype code is production authority.

The product-design result is clean within the strict move-only boundary below.
The packet is not yet GOV-2 review-clean: after this corrected packet is
committed, a fresh-context reviewer independent of this authoring session must
confirm the exact corrected head SHA. Only then may Dustin issue a binding
design-direction ruling. This distinction is deliberate; branch existence and
this document's conclusion authorize no downstream work.

## 1. CURRENT-MAIN RECONCILIATION

### 1.1 Live repository and isolation proof

The reconciliation used an isolated worktree based directly on the fetched
`origin/main` head. The following facts were verified before authoring:

- `origin/main` is exactly
  `044602770f745e322dc47a88e9bd342dc0955ce7`.
- That commit is the merge of baseline `8bf3b58a98120c43860a689756d84950a0b3aadb`
  and the PRD-314 implementation head, and GitHub reports PR #275 `MERGED`.
- `docs/PRD_REGISTRY.md:334` records PRD-314 `COMPLETE`.
- `docs/prd_index.json:3-4` records `latest_complete = 314` and
  `next_prd = 315`.
- `docs/PROJECT_STATE.md` has no active PRD. A stale historical paragraph later
  in that file still names an older next/latest pair; it is not registry
  authority and is a non-blocking bookkeeping observation, not part of this
  product cone.
- The original worktree and the prior PRD-314 worktree were not modified.
  All packet work occurred on the docs-only branch named above.

The current renderer-focused baseline passed before this packet was written:

```text
pytest -q \
  tests/test_dash_core.py \
  tests/test_dash_candidates.py \
  tests/test_dash_system_state.py \
  tests/test_dashboard_renderer.py \
  tests/test_gex_card.py \
  tests/test_movement_card.py \
  tests/test_market_state_panel.py \
  tests/test_dash_level_diagram.py \
  tests/test_preview_fixtures.py

627 passed
```

The registry validator also passed with commit-resolvability skipped for the
local verification run. These results establish a green documentation
baseline only. Per GOV-2, they do not validate a future implementation or the
completeness of this design boundary.

### 1.2 Exact PRD-314 drift

The diff from the deep recon's `8bf3b58a...` baseline to current main changes
ten files. The only production files are:

- `cuttingboard/delivery/dashboard_renderer.py`: an ID-scoped phone rule for
  Market State, System State, and Opportunity Survival at
  `dashboard_renderer.py:921-931`;
- `cuttingboard/delivery/market_state_panel.py`: presentation spans
  `.market-state-main`, `.market-state-provenance`, and
  `.market-state-qualifier` around already-existing text.

The overlapping current tests/artifact are:

- `tests/test_dash_system_state.py`: PRD-314 Opportunity child-order guards;
- `tests/test_dashboard_renderer.py`: exact phone-CSS and generic-selector
  guards;
- `tests/test_market_state_panel.py`: visible-text and span guards;
- `tests/data/dashboard_pre_gex_golden.html`: the new CSS and Market State span
  markup.

PRD-314 did not move, gate, rewrite, wrap, or restyle Candidate. It did not
change Opportunity counts or validity. Its CSS contains no adjacent-sibling
selector, `order`, or visual DOM reordering. The Market State spans change
markup structure only inside that panel and do not depend on Candidate
position.

Two source-slice hashes prove the overlapping functional surfaces are
unchanged between the recon baseline and current main:

| Slice | `8bf3b58a...` SHA-256 | current-main SHA-256 | Result |
|---|---|---|---|
| Candidate comment through the seam before Run Delta | `56270daf5d74b3e0bd33cc531ef1ce0f014fc0f2fed0dd2ebc91b20d0d62edc3` | same | byte-identical |
| Opportunity comment through the seam before Alert | `95943f206aa279aafe944e0fde88eb07dc4f63177ec9fb495f9abfc51489e920` | same | byte-identical |

### 1.3 Reconciliation verdict

**RECON UPDATE REQUIRED**

Only these assumptions require update; the deep recon does not need to be
restarted:

1. Re-pin all current-source navigation and acceptance to
   `044602770f745e322dc47a88e9bd342dc0955ce7`.
2. Preserve PRD-314's phone CSS and Market State span markup exactly; treat the
   associated tests as explicit regressions.
3. Reconcile the order tests and no-GEX golden against the post-314 baseline.
   In particular, the current `_survival_block()` helper ends Opportunity at
   Alert and would incorrectly absorb Candidate after the move.
4. Use the current registry state and the 627-test baseline above.

Every design assumption material to the proposed move remains valid:
Candidate and Opportunity carriers are independent; Candidate's wrapper is
independent of Opportunity presence; Candidate's internal branches are
unchanged; no CSS, JavaScript, report, notification, readiness, workflow, or
carrier consumer depends on the current sibling order.

### 1.4 Exact current emission graph

`render_dashboard_html()` is defined at
`cuttingboard/delivery/dashboard_renderer.py:2055` and emits top-level surfaces
by sequential `w(...)` calls. No caller supplies an order plan.

| # | Current surface | Current-main source | Presence |
|---:|---|---|---|
| 0 | integrity/Sunday notices | before staleness | conditional |
| 1 | `#staleness-banner` | 2338-2349 | inert scaffold always; client visibility age-driven |
| 2 | `#market-state` | 2351-2372 | always |
| 3 | `#system-state` | 2374-2531 | always |
| 4 | `#opportunity-survival` | 2533-2622 | current validity gate only |
| 5 | `#alert-watchlist` | 2624-2636 | non-empty `alert_candidates` |
| 6 | `#gex-context` | 2638-2647 | fresh valid fragment only |
| 7 | `#market-movement` | 2648-2656 | valid schema-v2 fragment only |
| 8 | `#spy-observation` | 2657-2689 | daily session data present |
| 9 | `#market-control-card` | 2690-2716 | daily control data present |
| 10 | `#sunday-macro-context` | 2717-2747 | coherent Sunday state |
| 11 | `#macro-tape` | 2748-2858 | always, with current availability behavior |
| 12 | `#red-folder` | 2859-2899 | current event/default/failure rules |
| 13 | `#trend-structure` | 2900-3022 | always, with current degraded rows |
| 14 | `#candidate-board` | 3023-3160 | wrapper always |
| 15 | `#run-delta` | 3161-3208 | always |
| 16 | `#scoreboard` | 3209-3243 | always |

Therefore Alert, GEX, Movement, session cards, Sunday context, Macro, Red
Folder, and Trend can all intervene between Opportunity and Candidate. The
amount of travel varies with unrelated context availability.

### 1.5 Candidate data and visibility proof

The carriers are separate and already loaded before emission:

```text
finalized payload
  meta.symbols_scanned
  sections.rejected[]
  sections.watchlist[]
       -> Opportunity validity/count rendering

market_map.v1
  symbols{}
  removed_symbols[]
       -> Candidate wrapper/tiering
       -> _render_candidate_card() at line 1876
            -> _render_level_diagram() at line 1609

latest_hourly_contract (optional, independent)
       -> contract entry/stop overlay for the level diagram
       -> Alert Watchlist candidates gated by execution policy
```

There is no Opportunity-to-Candidate join. Opportunity does not select,
filter, authorize, or count market-map cards. A truthful `QUALIFIED 0` can
coexist with a `B — DEVELOPING` Candidate.

Opportunity renders only when the existing gate at lines 2546-2560 has:

- healthy lineage;
- a positive integer `symbols_scanned`, explicitly excluding `bool`;
- list-shaped `sections.rejected` and `sections.watchlist`;
- dictionary-shaped rejected records.

Malformed, zero-scan, missing-map, mixed, or stale lineage suppresses the
whole Opportunity block. Continuation-promotion handling, the derived
qualified count, rejection mode, sanitization, and the operator-lock
`SETUPS FOUND` relabel remain inside the unchanged block.

The Candidate wrapper at lines 3023-3160 is emitted regardless of whether
Opportunity rendered. Its mutually exclusive visibility paths remain:

- unhealthy lineage: `STALE MARKET MAP`, `SOURCE_MISSING`, `PARSE_ERROR`, or
  generic lineage unavailability, with the current independent run/map clocks;
- coherent source error: `SOURCE_MISSING` or `PARSE_ERROR`;
- inactive session: current inactive label;
- healthy stale marker: `STALE`;
- absent map: `N/A`;
- empty symbols: `NO_CANDIDATES`;
- populated map: current skip lines, idle summary, tier order, cards, and
  removed-symbol history.

The complete wrapper includes its current heading and always-open scope line:

```text
OBSERVATION ONLY — setup quality never overrides Decision State or Permission.
```

For current high-grade cards, `_render_candidate_card()` keeps identity,
grade, setup state when supplied, bias/structure, current entry or neutral
`LEVEL`, and first invalidation or neutral `INVALIDATION` outside the existing
`DETAIL` disclosure. Reason for grade, PLAY/preferred structure, and WATCH are
already inside native `<details class="card-detail">`; the level diagram is
outside disclosure. Operator lock retains observations, suppresses action
language, and neutralizes labels through existing logic. None of this changes.

Relevant hooks to preserve include:

- top-level IDs: `#market-state`, `#system-state`,
  `#opportunity-survival`, `#candidate-board`, `#alert-watchlist`,
  `#run-delta`, and `#scoreboard`;
- Candidate structure: `.candidate-scope`, `.tier-group`, `.tier-header`,
  `#tier-aplus`, `#tier-a`, `#tier-b`, `#tier-c`, `.candidate-card`,
  `#card-{symbol}`, `.card-header`, `.card-detail`, `.lvl-diagram`,
  `.lvl-unavail`, `.lifecycle-badge`, `.lifecycle-detail`,
  `.failed-card-fields`, `.removed-symbols`, and `.removed-row`;
- wrapper/status hooks: `.block`, the current disabled modifier,
  `.idle-summary`, and `.unavailable`.

Repository-wide selector and consumer searches found no adjacent-sibling
dependency. `scripts/check_readiness.py` checks that `id="candidate-board"`
exists but does not inspect position. Generated `ui/dashboard.html` and
`ui/index.html` are publish outputs; they are not source and were not updated
by PRD-314.

### 1.6 Current ordering and golden pins

The load-bearing current test locations are:

- `tests/test_dash_core.py:144-182`: System-before-Candidate and PRD-177
  full-board order;
- `tests/test_dash_candidates.py:641-679`: Alert presence/content and the
  historical Alert-before-Candidate assertion;
- `tests/test_dash_system_state.py:37-135,297-318,492-495`: multiple
  System-to-Candidate and Opportunity-to-Alert substring sentinels;
- `tests/test_dashboard_renderer.py:300-315,1442-1446,1717-1762,
  1888-1901,3917-3965`: Macro/Trend/Candidate boundaries, PRD-116/312
  order, protected interval, and PRD-314 CSS;
- `tests/test_dashboard_renderer.py:4496-4534` and
  `tests/data/dashboard_pre_gex_golden.html`: exact no-GEX output.

The golden is a deterministic whole-document historical pin. It now includes
PRD-314 CSS and Market State spans. It must change only because the exact same
Candidate fragment occupies a new document index.

## 2. INDEPENDENT REVIEW VERDICT

### 2.1 Review event

```text
EVENT TYPE: INITIAL PACKET REVIEW
REVIEWED INPUT: 4c85b01db2fefe7188015744afd847095fad596d
REPOSITORY BASELINE: 044602770f745e322dc47a88e9bd342dc0955ce7
REVIEW DATE: 2026-08-23
REVIEWER: Codex, fresh-context independent material-packet reviewer capability
CONTEXT: independent of the prior recon authoring session; direct current-main evidence
MEMORY PROVENANCE: no prior rollout memory used for findings
VERDICT: ACCEPT WITH CORRECTIONS
```

Low-cost subagents performed branch/SHA checks, source and test enumeration,
historical lookup, and repetitive state tracing. Their evidence was reproduced
or reconciled by the primary reviewer. They do not satisfy GOV-2 independence
and did not make the architecture or governance decisions.

### 2.2 Findings and dispositions

| ID | Finding | Disposition in this packet |
|---|---|---|
| F1 | The recon's baseline and line references predate merged PRD-314. | **ACTIONED** — pinned to current main with exact drift and current lines. |
| F2 | The recon did not protect PRD-314's new phone CSS, Market State spans, current Opportunity child-order tests, and updated golden. | **ACTIONED** — added explicit acceptance, regression, and golden invariants. |
| F3 | The prior MATERIAL rationale named exhaustive enumeration but not the independent production FILES/LOC-ceiling trigger. | **ACTIONED** — both exact GOV-2 triggers are recorded in sections 9-10. |
| F4 | `dashboard_renderer.py` is a CONSUMER high-risk file, so STANDARD required an independent R11/R12 challenge. | **ACTIONED** — classification independently challenged and upheld: the literal PRD-229 layout/markup carve-out applies only to the verbatim move; GOV-2 removes MICRO, leaving STANDARD. Any non-layout hunk forces HIGH-RISK. |
| F5 | The proposed test cone needed current-main load-bearing proof and separation from regression-only PRD-314 tests. | **ACTIONED** — five exact test/golden payload files retained; `test_market_state_panel.py` is regression-only. |
| F6 | Seven existing review artifacts are absent from the registry Audit Reports table. | **DISMISSED FOR CURRENT PACKET SCOPE** — no PRD is being saved; the valid gap is recorded as a mandatory prerequisite before any future PRD save, and no registry edit is authorized now. |

The corrected design is internally complete. It still requires a separate
`EXACT-CORRECTED-HEAD CONFIRMATION` against the commit produced from this
packet. This authoring session cannot certify its own corrected head.

### 2.3 Independent challenge results

| Challenge | Finding |
|---|---|
| Is the move semantics-preserving? | Yes, if and only if it is a source-order relocation of the complete 138-line block with extracted-fragment parity. No value, gate, carrier, visibility, label, or helper changes are needed. |
| Does adjacency imply a survivor relationship? | It can to a human reader. That is the principal design risk. Separate wrappers, the observation-only scope line, and an explicit `QUALIFIED 0` plus B Candidate fixture are mandatory controls. No copy may claim lineage between them. |
| Must any detailed Context precede Candidate? | No. Critical Positioning, Participation, and Event Risk summaries already remain in Market State above System/Candidate. Detailed GEX, Movement, session, Macro, Red Folder, and Trend inform but do not authorize. |
| Is Candidate independent of Opportunity presence? | Yes. Candidate wrapper emission is unconditional; Opportunity has its own payload-validity `if`. The proposed paste seam is after that `if`, not inside it. |
| Do HALT and lock remain dominant? | Yes. System remains above both surfaces. Existing lock translations and Candidate scope remain unchanged. Explicit fixtures are still required because proximity increases interpretation risk. |
| Is moved stale/unavailable Candidate misleading? | It becomes more prominent but no less truthful: its current disabled/source wording and independent clocks remain. It must never inherit Opportunity freshness or a global clock. |
| Alert before or after Candidate? | After Candidate. Candidate is the broad market-map observation; Alert is a narrower, separate latest-hourly execution-policy-gated list. PRD-102 protects Alert semantics, not its current Candidate-relative order. |
| CSS/JS adjacency dependency? | None found. PRD-314 CSS is ID-rooted; no `+`, `~`, flex/grid `order`, or DOM-neighbor script targets these surfaces. |
| Reports/notifications/workflows order dependency? | None found. They do not parse dashboard order. Publish workflows regenerate/copy outputs; readiness checks marker presence only. |
| Are PRD-112/177/312 deliberately superseded? | Yes, but narrowly: only Candidate's cross-family position and the interval-as-sentinel are superseded. System authority, Market-before-System, and Context-internal order remain. |
| Is the file cone sufficient? | Yes for the move-only design: one production renderer, four test modules, one deterministic golden. Any additional payload file is a stop/reclassification signal. |
| Is STANDARD correct? | Yes under the process-defined cosmetic/layout carve-out plus GOV-2's MICRO prohibition. This is not a claim that the product decision is trivial. |
| What makes it MATERIAL? | Exhaustive consumer/output/file-cone claims and establishment of production FILES/LOC ceilings. |
| Does the renderer plus order seam automatically force HIGH-RISK? | No. R11's file trigger is explicitly inapplicable to pure layout/markup structure. A single non-cosmetic hunk invalidates that exception and then forces HIGH-RISK. |
| Is Change Surface mandatory? | Yes. The carve-out does not erase the separate Change Surface trigger for a named CONSUMER high-risk file. |

## 3. REQUIRED CORRECTIONS TO DEEP RECON

The deep recon's product conclusion survives. Its corrected authoring input is:

1. Baseline current behavior and line citations at `044602770...`, not
   `8bf3b58a...`.
2. Define the production move as lines 3023-3160 at current main: 138 source
   lines relocated, zero intended net production LOC.
3. Preserve the exact PRD-314 CSS block at lines 921-931 and all
   `market_state_panel.py` span markup/visible text.
4. Replace Opportunity extraction that runs from Opportunity to Alert; after
   the move that interval contains Candidate and is no longer a valid block
   boundary.
5. Treat the post-314 no-GEX golden as the regeneration base and prove an
   order-only difference.
6. State both exact GOV-2 MATERIAL triggers and the conditional Standard-lane
   reasoning.
7. Require Change Surface in the future PRD even though the executable
   mechanism is structural.
8. Complete the seven missing registry Audit Reports rows before saving a new
   PRD. This is governance bookkeeping, not a reason to expand the future
   product/test cone.

No correction is required to the carrier, state, disclosure, reversibility,
or doctrine conclusions.

## 4. FINAL DESIGN BOUNDARY

The visual lab's durable input is the architectural finding—not its prototype
code—that Opportunity continuity was the highest-value tested change for
phone and desktop scanning. This packet adopts that question while rejecting
prototype wrappers, CSS, components, disclosures, and layout as production
authority.

### 4.1 Goal and exact mechanism

Move the existing complete `MARKET MAP / DEVELOPING SETUPS`
`#candidate-board` emission block verbatim from immediately before
`#run-delta` to immediately after the Opportunity conditional and immediately
before `#alert-watchlist`.

Mechanically:

1. Cut `dashboard_renderer.py:3023-3160`, beginning with
   `# --- candidate-board ---` and ending with its final wrapper
   `w("</div>")`.
2. Paste it after the Opportunity conditional closes at line 2622 and before
   the Alert comment currently at line 2624.
3. Change no byte inside the moved block except indentation only if a tool
   proves unavoidable; at the selected seam, no indentation change is needed.
4. Do not extract a helper. Do not introduce a wrapper, flag, shared carrier,
   CSS rule, or new disclosure.

The resulting top-level source/DOM sequence is:

```text
MARKET STATE
SYSTEM STATE
OPPORTUNITY SURVIVAL          when currently valid
MARKET MAP / DEVELOPING SETUPS
ALERT WATCHLIST               when currently present
GEX                           when currently present
MOVEMENT                      when currently present
SESSION OBSERVATION           when currently present
MARKET CONTROL                when currently present
SUNDAY MACRO CONTEXT          when currently present
MACRO
RED FOLDER                    under current rules
TREND
CHANGES
SCOREBOARD
```

When Opportunity is suppressed, Candidate follows System. It is outside the
Opportunity branch and no empty Opportunity placeholder is introduced.

### 4.2 Non-negotiable invariants

- Market State and System State remain separate authorities in that order.
- Opportunity and Candidate remain separate siblings and separate carriers.
- Candidate wrapper/presence, internal tiering, grade/state, sort, content,
  health branches, lock/HALT behavior, level, invalidation, reason/play/watch,
  diagram, provenance, and clocks remain unchanged.
- Opportunity gate, counts, label, wording, carrier, and HTML remain unchanged.
- Alert remains separate and contract-gated.
- Detailed Context retains its current mutual order and every current gate.
- Changes and Scoreboard remain below the unchanged Context/Structure chain.
- No CSS/JS visual reorder diverges from accessible source order.
- No global `as of`, carrier join, predictive score, synthetic direction, or
  new semantic-color meaning is added.

### 4.3 Estimated Change Surface — not yet approved

```text
PRODUCTION SYMBOL: render_dashboard_html
PRODUCTION FILES: 1
TEST/GOLDEN PAYLOAD FILES: 5
PRODUCTION MOVE: 138 relocated physical lines (+138 / -138)
NET PRODUCTION LOC: 0 intended
NEW SYMBOLS OR SIGNATURES: 0
```

GitNexus was refreshed at current main. It indexed 17,833 nodes, 28,281 edges,
and 202 flows, but extraction failed on the large renderer and related tests.
Its upstream result for `render_dashboard_html` was LOW with zero callers and
flows; that result is known incomplete and is not safety evidence. Manual
call-site, consumer, workflow, test, and output tracing defines this surface.

These are provisional estimates under GOV-2, not a binding Gate A ceiling.
Any internal production edit, net production LOC, helper extraction, second
production file, or newly discovered consumer stops the move-only path for
reconciliation and classification.

## 5. ORDERING CONTRACT DISPOSITION

The labels below are deliberately limited to the four requested dispositions.
Where a surface has both a preserved internal contract and a superseded
Candidate-relative contract, they are listed separately.

| Existing assertion or relationship | Disposition | Future contract |
|---|---|---|
| Market State before and separate from System State | **SEMANTIC CONTRACT TO PRESERVE** | `market-state < system-state`; neither wraps or synthesizes the other. |
| System State before Opportunity, Candidate, and every normal downstream block | **SEMANTIC CONTRACT TO PRESERVE** | System remains the execution authority above Candidate under normal, lock, HALT, mixed, and missing states. |
| Opportunity immediately after System when its current gate passes | **SEMANTIC CONTRACT TO PRESERVE** | No top-level block may be inserted between System and Opportunity. |
| Opportunity before Alert | **SEMANTIC CONTRACT TO PRESERVE** | Candidate may intervene, but Opportunity remains above Alert. |
| Opportunity-to-Alert substring used as the Opportunity block boundary | **HISTORICAL TEST PIN TO UPDATE** | Use depth-aware exact top-level block extraction. |
| Candidate internal wrapper, tiers, cards, states, and order | **SEMANTIC CONTRACT TO PRESERVE** | Extracted Candidate fragment remains identical. |
| Candidate after Macro/Red Folder/Trend (PRD-112/177) | **SEMANTIC CONTRACT INTENTIONALLY SUPERSEDED** | Candidate moves ahead of detailed Context; Context-internal sequence remains. |
| Candidate as the lower endpoint of the governed `system-state..candidate-board` interval (PRD-312) | **SEMANTIC CONTRACT INTENTIONALLY SUPERSEDED** | Protect the exact System block and Market-before-System relation, not the old interval. |
| System-to-Candidate substring boundaries in tests | **HISTORICAL TEST PIN TO UPDATE** | Exact block helpers prevent Candidate relocation from weakening System assertions. |
| Alert Watchlist presence, wording, population, and execution-policy meaning | **SEMANTIC CONTRACT TO PRESERVE** | Alert remains a separate optional block. |
| Alert before Candidate | **HISTORICAL TEST PIN TO UPDATE** | Candidate immediately precedes Alert when Alert is present. |
| GEX before Candidate | **INCIDENTAL / NOT A CONTRACT** | GEX moves below Candidate by consequence; its fragment, gate, delayed-source qualifier, positioning assumption, and clock remain. |
| Movement before Candidate | **INCIDENTAL / NOT A CONTRACT** | Movement moves below Candidate by consequence; its 12/12 fragment, gate, provenance, and clock remain. |
| Session Observation before Candidate | **INCIDENTAL / NOT A CONTRACT** | Daily-only conditional Session Observation follows Candidate. |
| Session Observation before/with Market Control when both are present | **SEMANTIC CONTRACT TO PRESERVE** | Their existing pair and conditions remain unchanged. |
| Market Control before Candidate | **INCIDENTAL / NOT A CONTRACT** | Market Control follows Candidate without content or carrier changes. |
| Sunday Macro Context before Macro | **SEMANTIC CONTRACT TO PRESERVE** | It remains conditional and immediately upstream of the unchanged Macro family. |
| Macro before Red Folder before Trend | **SEMANTIC CONTRACT TO PRESERVE** | Preserve exact Context-internal order, including resolved-empty Red Folder omission. |
| Macro before Candidate | **SEMANTIC CONTRACT INTENTIONALLY SUPERSEDED** | Macro follows Candidate; its pressure line and provenance remain internal and unchanged. |
| Macro-pressure line using Candidate as a trailing sentinel | **HISTORICAL TEST PIN TO UPDATE** | Assert the line is inside Macro, independent of Candidate position. |
| Red Folder before Candidate | **SEMANTIC CONTRACT INTENTIONALLY SUPERSEDED** | Detailed Red Folder follows Candidate; critical Event Risk remains in Market State above it. |
| Trend before Candidate | **SEMANTIC CONTRACT INTENTIONALLY SUPERSEDED** | Trend follows Candidate while retaining Macro/Red Folder/Trend ordering and content. |
| Trend extraction ending at Candidate | **HISTORICAL TEST PIN TO UPDATE** | Extract the exact Trend top-level fragment. |
| Changes after Candidate and after existing Context/Structure | **SEMANTIC CONTRACT TO PRESERVE** | `context < run-delta`; Candidate also remains before Changes. |
| Scoreboard after Changes and final in the board | **SEMANTIC CONTRACT TO PRESERVE** | Scoreboard stays below Changes. |
| Whole-document no-GEX golden | **HISTORICAL TEST PIN TO UPDATE** | Regenerate deterministically and prove Candidate-position-only delta. |

The current Candidate location is therefore neither merely accidental nor
carrier-required. PRD-112 and PRD-177 deliberately established a context-first
vertical read; later GEX, Movement, session, Market State, and Opportunity
surfaces accumulated around it. The future PRD must explicitly supersede only
the cross-family Candidate placement and old interval sentinels. Historical
PRDs and audit artifacts remain immutable.

## 6. STATE MATRIX

The matrix describes the future top-level order without changing any current
presence rule. “Next” means the next emitted decision-zone block; an omitted
conditional block does not create a placeholder.

| State | Opportunity result | What appears immediately after Opportunity/System | Downstream consequence | Required truth invariant |
|---|---|---|---|---|
| Normal, one developing Candidate | Current funnel renders | `#candidate-board` with current B tier/card | Alert if present, then detailed Context | Candidate is observation, not a declared survivor or authorization. |
| Multiple developing Candidates | Current funnel renders | One Candidate wrapper; current grade-then-symbol ordering and all cards | Unchanged Context follows | Population and ordering remain market-map-owned. |
| No Candidate | Funnel may independently render | Candidate wrapper with current `NO_CANDIDATES` | Context follows | Do not suppress the wrapper or infer Candidate population from funnel counts. |
| Opportunity suppressed | No Opportunity wrapper because current gate fails | Candidate is the next decision-zone block after System | Alert/Context follows | Candidate wrapper remains independent and truthful. |
| Rejected/no-survivor funnel | Funnel renders current zero-qualified/rejection counts when valid | Candidate wrapper follows, including `NO_CANDIDATES` or independent map content | Context follows | A zero survivor count does not gate Candidate. |
| `QUALIFIED 0` plus independent B `DEVELOPING` Candidate | Funnel renders `QUALIFIED 0` (or `SETUPS FOUND 0` under lock) | B Candidate renders immediately next | Context follows | Explicit regression proves adjacency is not a carrier join or survivor claim. |
| Operator lock | System says `OBSERVE ONLY`; Opportunity label is current `SETUPS FOUND` when valid | Candidate retains observations, neutral `LEVEL`/`INVALIDATION`, no current action directives | Alert/Context unchanged | Lock remains authoritative above Candidate; no action vocabulary reintroduced. |
| HALT | System renders current HALT authority; Opportunity behaves exactly as current inputs dictate | Candidate wrapper follows Opportunity or System with current scope/content | Context follows | HALT remains above and visually dominant; Candidate never overrides it. |
| Stale Candidate carrier | Opportunity may suppress independently on lineage | Disabled Candidate branch with `STALE MARKET MAP` or current stale wording and separate run/map clocks | Other independently valid Context follows | No Opportunity clock or board clock is attributed to Candidate. |
| Candidate unavailable | Opportunity may render or suppress independently | Candidate wrapper shows current `SOURCE_MISSING`, `PARSE_ERROR`, generic unavailable, or `N/A` branch | Context follows | Do not hide, soften, or synthesize unavailable state. |
| GEX unavailable | Opportunity/Candidate unchanged | Candidate follows Opportunity/System | `#gex-context` is truly omitted under current rules; Movement or next Context follows | Market State Positioning retains its current honest unavailable projection; no fake card. |
| Movement unavailable | Opportunity/Candidate unchanged | Candidate follows Opportunity/System | `#market-movement` is truly omitted; next Context follows | Market State Participation remains honest and independent. |
| Red-folder event present | Market State Event Risk remains above System/Candidate | Candidate follows Opportunity/System | Detailed Red Folder remains in Macro -> Red Folder -> Trend chain | Critical event risk is not deferred below Candidate. |
| No Red Folder events | Market State retains current no-event state | Candidate follows Opportunity/System | Healthy resolved-empty detailed Red Folder remains omitted; Macro -> Trend | No empty detail card is reintroduced. |
| Daily session cards present | Opportunity/Candidate unchanged | Candidate follows Opportunity/System | Alert/GEX/Movement, then Session Observation -> Market Control, then Macro family | Daily surfaces retain their own data and order. |
| Hourly-only state | Opportunity/Candidate use current hourly-selected inputs | Candidate follows Opportunity/System | Daily-only Session Observation/Market Control remain absent | No daily/hourly carrier unification is introduced. |
| Inactive session / Sunday | Opportunity follows current gate | Candidate shows current inactive label | Sunday Macro Context remains conditional before Macro | Inactivity is presentation truth, not a new Candidate gate. |
| Stale board | Client staleness banner remains above Market State | Candidate follows Opportunity/System using its own health branch | Context retains independent clocks | No synchronized global `as of`; board age and carrier lineage stay distinct. |

The matrix's cross-case invariant is stronger than simple order:

> Opportunity counts and Candidate population remain independent. Adjacency
> communicates operator reading sequence, not data lineage.

## 7. EXACT CHANGE SURFACE

### 7.1 Production symbol and branch cone

The only production symbol proposed for future modification is
`render_dashboard_html()` in
`cuttingboard/delivery/dashboard_renderer.py`. The affected executable branch
is the sequential emission position of the complete Candidate wrapper. The
following symbols are called by that block but must not be edited:

- `_render_candidate_card()`;
- `_render_level_diagram()`;
- `_GRADE_ORDER`, `_TIER_DEFS`, `_HIGH_GRADES`, and related display constants;
- all market-map, lifecycle, contract-entry, lock, lineage, and availability
  producers/helpers.

Direct production call paths remain:

```text
dashboard_renderer.main()
  -> write_dashboard()
       -> render_dashboard_html()
            -> _render_candidate_card()
                 -> _render_level_diagram()

scripts/preview_fixtures.py and tests
  -> render_dashboard_html() or write_dashboard()
```

No caller passes or consumes a top-level ordering structure. No notification,
report, runtime, schema, persistence, or producer path parses the sibling
order.

### 7.2 Change Surface declaration for future authoring

```text
INPUTS READ:
  unchanged payload, run, market_map, alert_candidates, GEX, Movement,
  session, Macro, Red Folder, Trend, previous-run, and history inputs

VALUES DERIVED:
  unchanged; no new value, label, threshold, health, or lineage derivation

OUTPUT MUTATED:
  top-level HTML/source order only

PERSISTED/TRANSPORTED CONTRACTS:
  none

AUTHORITY RELATION:
  Market State and System State remain above Candidate;
  Candidate remains observation-only; Context remains non-authorizing

ROLLBACK:
  move the same contiguous block back and restore order tests/golden
```

This section is mandatory in the future PRD because the exact FILES list names
a CONSUMER high-risk file, even though R11 is inapplicable to the narrowly
proved layout-only hunk.

## 8. EXACT FILE CONE

### 8.1 Production cone

Exactly one production file:

| File | Load-bearing future edit |
|---|---|
| `cuttingboard/delivery/dashboard_renderer.py` | Relocate the complete current Candidate emission block, with no internal edit. |

### 8.2 Test/golden cone

Exactly five load-bearing test payload files:

| File | Why an edit is required |
|---|---|
| `tests/test_dash_core.py` | Replace PRD-177's Candidate-relative full order with the explicitly superseding continuity order while preserving System-first, Context-internal order, Changes, and Scoreboard. |
| `tests/test_dash_candidates.py` | Reverse the historical Alert-before-Candidate assertion and add direct Candidate/Alert continuity without weakening Alert content/presence or Candidate content tests. |
| `tests/test_dash_system_state.py` | Replace System-to-Candidate and Opportunity-to-Alert substring sentinels where they cease to bound one block; retain every System and Opportunity value/gate assertion and PRD-314 child order. |
| `tests/test_dashboard_renderer.py` | Update protected-interval and Macro/Trend/Candidate positional assertions; add full top-level order and fragment parity; keep PRD-314 CSS and all carrier/content tests intact. |
| `tests/data/dashboard_pre_gex_golden.html` | Deterministically regenerate the exact no-GEX renderer oracle and prove its delta is Candidate relocation only. |

No new shared test helper file is justified. Depth-aware extraction may be a
small test-local helper in an already affected module. If implementation
demonstrates that a shared helper is genuinely required, that is a FILES-ceiling
change and must stop for reconciliation rather than being added opportunistically.

### 8.3 Regression-only files: run, do not edit absent evidence

- `tests/test_market_state_panel.py` — specifically protects PRD-314 spans and
  visible Market State text;
- `tests/test_gex_card.py`;
- `tests/test_movement_card.py`;
- `tests/test_dash_level_diagram.py`;
- `tests/test_preview_fixtures.py`;
- relevant Macro, Red Folder, Trend, session, staleness, readiness,
  operator-lock, notification, and publish tests selected from the final diff.

`tests/test_market_state_panel.py` is deliberately removed from the edit cone:
it has no Candidate-order assertion. It remains a required regression test.

### 8.4 Explicit exclusions

Do not hand-edit or include:

- `cuttingboard/delivery/market_state_panel.py`;
- `ui/dashboard.html`, `ui/index.html`, or other published/generated UI;
- payload, market-map, run, contract, GEX, Movement, Macro, Red Folder, Trend,
  session, or history fixtures merely to make the order test pass;
- runtime, schemas, producers, ingestion, persistence, reports,
  notifications, workflows, publication gates, or readiness logic;
- PRD history, decision canon, registry, or project state as product payload.

Registry pre-authoring bookkeeping is a separate governance prerequisite; it
does not expand this production/test cone.

## 9. CLASS / LANE / MATERIALITY

### 9.1 Final classification

```text
CLASS: CONSUMER
DEFAULT STABILITY TIER: T2
LANE: STANDARD
MATERIAL: YES
CHANGE SURFACE: MANDATORY
```

This classification is provisional design guidance until the packet is
exact-head confirmed and Dustin rules. It is nevertheless the correct current
process result for the strict boundary.

### 9.2 CLASS

`docs/PRD_PROCESS.md:412-421` defines `CONSUMER` as read-only consumers of
finalized artifacts, including the dashboard. The class matrix at lines
456-463 assigns T2 and names
`cuttingboard/delivery/dashboard_renderer.py` as a CONSUMER high-risk file.
No execution, contract, sidecar, infrastructure, or producer behavior changes.

### 9.3 Why MATERIAL is YES

GOV-2 section 1 is disjunctive. This packet triggers it twice:

1. It claims exhaustive enumeration of callers, consumers, renderers, outputs,
   order dependencies, and the exact file cone.
2. It establishes an estimated production FILES ceiling and production LOC
   ceiling for a future slice.

Either trigger is sufficient. The design does not claim the inapplicable
shared-cross-layer-seam, schema/contract, governance-guardrail,
Critical/High-resolution, or two-layer-crossing triggers.

### 9.4 Why STANDARD, not HIGH-RISK

The proposed executable hunk changes only layout/markup emission order in
presentation code and changes none of PRD_PROCESS R12's behavior surfaces:

- no trading-decision behavior;
- no artifact or carrier schema;
- no publication gate or runtime write order;
- no renderer-derived decision-bearing value;
- no threshold-to-label synthesis;
- no source-health or lineage classification;
- no notification truth semantic.

That satisfies the literal PRD-229 Cosmetic Carve-Out at
`docs/PRD_PROCESS.md:601-629`. “Cosmetic” here is a process term for a pure
layout/markup hunk, not a claim that the operator-ordering decision is trivial.
Under the carve-out, R11's high-risk-file trigger does not apply. GOV-2 then
bars MICRO and says a MATERIAL slice is STANDARD at minimum, HIGH-RISK only if
an independent R11 trigger fires. No such trigger remains; therefore STANDARD
is the correct lane.

Touching a deliberate ordering seam and a branch-heavy renderer raises review
risk, test depth, and Change Surface obligations, but it does not by itself
alter an R12 truth semantic. The future PRD must explicitly supersede the
historical ordering contract rather than hiding behind the word “cosmetic.”

### 9.5 Lane invalidation rule

If one production hunk changes Candidate or Opportunity content, visibility,
gate, health, lineage, permission, lock/HALT translation, carrier, CSS, helper
structure, or any other non-layout behavior, the entire slice stops qualifying
for the carve-out. Because the renderer is then a high-risk payload file, R11
forces `LANE: HIGH-RISK`. A carrier/schema discovery additionally stops this
implementation path rather than expanding it.

## 10. GOV-2 TRIGGERS

### 10.1 Exact applicable triggers

From `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:18-29`:

- lines 20-21: the work “claims to enumerate all consumers, callers,
  renderers, outputs, or schema readers”;
- line 23: the work “establishes or changes a production FILES ceiling or LOC
  ceiling.”

These make the slice MATERIAL before PRD authoring. Materiality disqualifies
MICRO but does not independently force HIGH-RISK (`GOV-2:51-63`).

### 10.2 Required order of authority

The remaining lawful sequence is:

```text
commit this corrected MATERIAL packet
-> independent exact-corrected-head SHA confirmation
-> Dustin/HELM design-direction ruling
-> repair required registry Audit Reports rows
-> save a future PRD draft from the ruling
-> fresh-context independent PRD review
-> Dustin Gate A
-> implementation in a separate authorized lane
```

The registry-row repair must occur before saving the PRD; it may occur before
or after the design ruling so long as it does not masquerade as product scope.
No step in this packet supplies a ruling, Gate A, or implementation authority.

### 10.3 Independent-review status

This packet records an initial fresh review of the prior recon and performs the
consolidated current-main correction. GOV-2 explicitly forbids the authoring
agent, its subagents, or a same-session second pass from satisfying the exact
corrected-head confirmation. The future confirmer must record:

- event type `EXACT-CORRECTED-HEAD CONFIRMATION`;
- this packet's exact commit SHA;
- reviewer identity/capability and fresh-context isolation evidence;
- F1-F6 and their dispositions;
- a verdict on whether those corrections are present at that exact SHA.

Until that record is committed, the packet is design-complete but not
review-clean and Dustin's binding GOV-2 ruling is not yet available.

## 11. ACCEPTANCE CONTRACT

### 11.1 All-width source/DOM order

Use a depth-aware HTML parser or deterministic top-level block extractor. For
every relevant fixture, assert:

1. `#market-state` precedes `#system-state`.
2. `#system-state` precedes `#candidate-board`.
3. When Opportunity exists:
   `#system-state < #opportunity-survival < #candidate-board`, with no other
   top-level `.block` between Opportunity and Candidate.
4. When Opportunity is absent, Candidate is the next emitted decision-zone
   block after System; no Opportunity placeholder exists.
5. When Alert exists, Candidate immediately precedes Alert.
6. When Alert is absent, Candidate precedes the first emitted detailed Context
   surface.
7. Candidate precedes GEX, Movement, daily/session Context, Sunday Context,
   Macro, Red Folder, and Trend whenever those surfaces exist.
8. The unchanged Context chain retains its current mutual order.
9. Changes follows Candidate and existing Context/Structure; Scoreboard follows
   Changes.
10. CSS visual order equals source/DOM/accessibility order.

Do not use the old `System..Candidate`, `Opportunity..Alert`, or
`Trend..Candidate` substring intervals as block parsers. Those are the
historical seams being changed.

### 11.2 Fragment and semantic parity

For the same inputs before and after the move:

- the complete extracted `#candidate-board` fragment is byte-identical;
- the Opportunity fragment and its presence/absence decision are
  byte-identical;
- Alert and every detailed Context/History fragment are byte-identical;
- Candidate branch selection, tier/card count, grade/state, level,
  invalidation, reason, PLAY, WATCH, diagram, removal rows, and lock wording
  are unchanged;
- Opportunity counts, primary rejection, sanitization, and lock label are
  unchanged;
- every carrier's provenance and clock remain attached to that carrier;
- no global timestamp, data join, score, or direction verdict is introduced;
- Market State and System State remain distinct blocks and authorities.

The explicit contradiction fixture is mandatory:

```text
Opportunity: QUALIFIED 0
Candidate:   SPY · B · DEVELOPING, with current level and invalidation
Expected:    both render truthfully as separate adjacent surfaces
Forbidden:   any copy, wrapper, filter, or assertion claiming SPY survived
```

### 11.3 Operator and degraded semantics

- HALT remains in System above Candidate and retains current class/text.
- Operator lock retains `OBSERVE ONLY`, `SETUPS FOUND` when Opportunity exists,
  neutral Candidate `LEVEL`/`INVALIDATION`, and current suppression of action
  directives.
- Candidate stale/unavailable wording and independent run/map clocks are exact.
- GEX and Movement unavailable paths remain true omission for their detailed
  cards and honest unavailable projections in Market State.
- Red-folder critical event state remains visible in Market State before
  Candidate; detailed events remain below in the unchanged chain.
- No-candidate and Opportunity-suppressed states remain truthful and
  independent.

### 11.4 390x844 deterministic visual acceptance

Using the same pinned long-content production fixture in baseline and changed
builds:

- Opportunity's top-level closing edge and Candidate's top-level opening edge
  are consecutive in DOM and separated visually only by the existing `.block`
  bottom margin; no Alert or Context heading appears between them.
- Candidate heading/scope/first identity top is strictly earlier than current
  main by the exact aggregate outer height of the emitted surfaces relocated
  below it. The measured delta must be positive and reconcile to those blocks,
  not to CSS or content changes.
- Candidate identity is the next operator read after Opportunity.
- Existing level and invalidation text, when supplied under current rules,
  remains outside closed `<details>` and requires no disclosure action.
- Existing `DETAIL` remains keyboard-focusable and screen-reader reachable;
  no new disclosure is added.
- `document.documentElement.scrollWidth <=
  document.documentElement.clientWidth` and every top-level bounding box stays
  within the viewport; no card, SVG, label, or table clips.
- A computed-style and rendered-text comparison proves no CSS or Candidate
  content change.

The baseline-relative geometry check is the deterministic meaning of
“materially earlier”: the entire current intervening rendered stack, not a
token pixel adjustment, is removed from before Candidate.

### 11.5 1280x800 deterministic visual acceptance

- Market State, System State, Opportunity, and Candidate remain separate
  top-level blocks with no shared wrapper or fake combined authority.
- Candidate minimum read is earlier than current main by the same
  block-height reconciliation rule.
- Detailed Context may begin after Candidate using existing desktop CSS; no
  columns, side rail, family wrapper, or breakpoint is introduced.
- Level and invalidation remain available under existing conditional rules.
- No horizontal overflow, clipping, source/visual-order mismatch, or lost
  provenance occurs.

### 11.6 Required responsive sweep

Also render at 360x800, 430x932, 768x1024, and 1440x900. At all six widths:

- source/DOM/focus/visual order agree;
- staleness, Market State, System HALT/lock, critical unavailable/event state,
  Candidate identity, supplied level, and supplied invalidation are not hidden;
- no information becomes color-only;
- PRD-314's `<=430px` CSS block and generic CSS remain byte-identical;
- no horizontal page overflow occurs.

## 12. TEST PLAN

### 12.1 Structural tests that must fail before the move

Add or rewrite deterministic assertions so current main fails the new
continuity contract and the move passes:

- valid Opportunity: exact top-level order is
  Market -> System -> Opportunity -> Candidate -> optional Alert -> Context;
- suppressed Opportunity: System -> Candidate -> optional Alert/Context;
- Alert present: Candidate immediately before Alert;
- Candidate before each independently conditional Context surface;
- Context-internal order and Changes/Scoreboard tail remain unchanged.

At least one mutation that moves Candidate back to its old seam must fail the
new continuity assertion while Candidate content tests remain green.

### 12.2 State and carrier tests

Cover every row in section 6, with dedicated assertions for:

- one and multiple Candidates, current sorting, and no Candidate;
- valid Opportunity, malformed/zero-scan suppression, and `QUALIFIED 0` plus
  independent B Candidate;
- operator lock and HALT;
- Candidate stale, source-missing, parse-error, `N/A`, and inactive states;
- GEX and Movement present/omitted independently;
- red-folder event present and healthy resolved-empty;
- daily cards, hourly-only state, Sunday/inactive state, and stale board.

Do not alter input carriers to make the desired visual sequence easier to
assert.

### 12.3 Content-parity tests

Use exact top-level fragment extraction. Where a permanent test cannot execute
both code revisions, retain a fixed pre-move Candidate fragment oracle or run a
review-time two-worktree comparator. Prove:

- pre/post Candidate fragment hash equality;
- pre/post Opportunity fragment hash and presence equality;
- pre/post Context fragment hash equality;
- all current Candidate internal branch tests still pass unchanged;
- PRD-314 `_PRD314_PHONE_BLOCK`, Market State visible text/spans, and generic
  selector tests pass unchanged.

The test rewrite must strengthen boundaries, not merely replace `<` with `>`.
A Candidate move that changes System, Opportunity, or Candidate text must be
caught.

### 12.4 Execution set for a future implementation

Minimum focused run:

```text
pytest -q \
  tests/test_dash_core.py \
  tests/test_dash_candidates.py \
  tests/test_dash_system_state.py \
  tests/test_dashboard_renderer.py \
  tests/test_gex_card.py \
  tests/test_movement_card.py \
  tests/test_market_state_panel.py \
  tests/test_dash_level_diagram.py \
  tests/test_preview_fixtures.py
```

Then run the repository's required Consumer/Standard checks and the full suite
if the reviewed PRD or current process requires it. Browser evidence at all six
widths is required because structural tests alone do not prove visual
continuity or overflow safety.

## 13. GOLDEN PLAN

`tests/data/dashboard_pre_gex_golden.html` is the only generated artifact in
the payload cone.

1. Render with the exact frozen fixture used by
   `test_gex_absent_baseline_identical`: `_payload()`, `_run()`, no GEX, and
   `_GEX_FROZEN`.
2. Regenerate mechanically; never hand-move golden text.
3. Extract the full Candidate top-level span from old and new goldens and
   require byte equality and the same SHA-256.
4. Parse both documents into ordered top-level fragments. Remove Candidate
   from each sequence and require all remaining fragments and non-block shell
   bytes to be identical.
5. Require the raw unified diff to consist of one deletion and one insertion
   of the same Candidate lines, aside from deterministic separator placement.
6. Explicitly verify the PRD-314 phone CSS and Market State span/text slices
   are unchanged.
7. Keep `test_gex_absent_baseline_identical` green for absent, stale, and
   invalid GEX.

Any Candidate-content, Opportunity-content, CSS, provenance, timestamp,
Context, or shell delta hidden in regeneration is a failure, not a golden
update to accept.

## 14. REVERSIBILITY

This is one independently reversible production slice:

1. move the existing contiguous Candidate block to the new seam;
2. update only the directly coupled order/extraction tests;
3. regenerate the one deterministic golden.

A clean revert moves the same block back immediately before Run Delta,
restores the former positional expectations, and regenerates the former
golden. There is no migration, schema version, backfill, feature flag, dual
render, carrier compatibility window, producer rollback, or persisted state.

Reversibility acceptance:

- zero intended net production LOC;
- no helper/signature/constant changes;
- extracted Candidate and Context fragments match across the move;
- returning the block to the old seam makes only the new order contract fail;
- a scoped diff/change detector reports no runtime, carrier, schema,
  notification, report, workflow, or generated-UI mutation.

Family wrappers, responsive grid work, typography changes, and any additional
disclosure must remain separate future decisions so reversing this order slice
does not unwind unrelated architecture.

## 15. RISKS

| Risk | Severity | Control / stop condition |
|---|---|---|
| Adjacency implies Candidate survived Opportunity | **High operator-interpretation risk** | Separate wrappers and carriers; preserve scope line; permanent `QUALIFIED 0` plus B Candidate regression; no linking copy. |
| Candidate proximity appears to override HALT or lock | **High operator risk** | Market/System remain above; exact HALT/lock fragment parity and browser review. |
| Moving 138 branch-heavy lines edits internal logic | **High implementation risk** | Same-block deletion/insertion diff, fragment hash parity, zero net LOC, no helper. |
| Brittle substring tests are weakened while being updated | **High regression risk** | Depth-aware top-level extraction; retain every content/gate assertion. |
| Stale/unavailable Candidate gains prominence | **Medium interpretation risk** | Preserve disabled state, wording, and independent clocks; do not inherit Opportunity freshness. |
| Critical Context moves below Candidate | **Medium** | Verify Market State continues to expose critical Positioning, Participation, and Event Risk summaries/qualifiers above Candidate. |
| Alert population is mistaken for Candidate population | **Medium** | Keep separate heading/wrapper/carrier; Candidate -> Alert order; no merge or count relationship. |
| PRD-112/177/312 contracts are silently discarded | **High governance risk** | Future PRD explicitly supersedes only Candidate-relative position and old interval sentinels. |
| PRD-314 compaction/span work is lost in golden/test churn | **High regression risk** | Exact CSS/span/text parity and regression-only `test_market_state_panel.py`. |
| Golden regeneration hides content changes | **High regression risk** | Candidate hash, top-level sequence comparison, same-lines delete/insert proof. |
| Standard lane masks a non-cosmetic hunk | **High governance risk** | Any behavior/CSS/helper hunk stops and forces R11/R12 reclassification; renderer then means HIGH-RISK. |
| GitNexus reports a false-low impact | **Medium recon risk** | Manual cone is authoritative; final change detection plus consumer/test/workflow searches are mandatory. |
| Missing registry review rows contaminate PRD authoring | **High process risk** | Repair all seven rows before saving a new PRD; keep that bookkeeping outside product cone. |
| Packet is treated as review-clean before exact-head confirmation | **High authority risk** | State provisional status everywhere; require separate SHA-pinned confirmation before Dustin's binding ruling. |

## 16. CUT LIST

The future bounded slice excludes all of the following:

- any Candidate redesign, family wrapper, shared Opportunity/Candidate zone,
  heading/copy change, or component extraction;
- CSS, color, typography, whitespace, border, touch-target, breakpoint,
  desktop grid, phone compaction, or side-rail changes;
- any new disclosure or change to current Candidate reason, PLAY, WATCH,
  `DETAIL`, or level diagram visibility;
- Candidate grade/state logic, tiering, sort, filtering, visibility, identity,
  level, invalidation, failure/unavailable state, or scope line changes;
- Opportunity count, gate, carrier, primary rejection, wording, lock label, or
  empty/suppressed behavior changes;
- permission, authorization, HALT, operator lock, action-language, Market
  State, or System State changes;
- Alert content, population, carrier, gate, or merge into Candidate;
- GEX, Movement, session, Market Control, Macro, Red Folder, Trend, Changes, or
  Scoreboard content, gate, provenance, clock, internal order, or styling;
- market-map, payload, run, contract, sidecar, schema, producer, ingestion,
  runtime, persistence, publication, notification, report, or workflow changes;
- renderer decomposition, new helper extraction, feature flag, dual render,
  compatibility layer, or carrier join;
- hand edits to `ui/*.html`, logs, reports, published output, or arbitrary
  fixtures;
- a global `as of`, predictive composite, bullish/bearish synthesis, fake
  certainty, new semantic-color contract, or any implication that Context or
  Candidate authorizes a trade;
- family-wrapper or desktop-layout work from the visual prototypes;
- registry/history cleanup inside the product implementation commit.

If any cut item appears necessary, stop. Do not stretch the move-only PRD;
return to MATERIAL reconciliation and reclassify.

## 17. PRD-315 AUTHORING HANDOFF

### 17.1 Preconditions before a PRD may be saved

1. Commit this packet on its docs-only branch.
2. Obtain independent `EXACT-CORRECTED-HEAD CONFIRMATION` against that commit.
3. Obtain Dustin/HELM's explicit design-direction ruling.
4. Add registry Audit Reports rows for each existing unregistered artifact:
   - `PRD-301.amendment.confirmation.claude.md`
   - `PRD-301.gate-fix.confirmation.codex.md`
   - `PRD-301.ratified.confirmation.claude.md`
   - `PRD-309.impl-review.claude.md`
   - `PRD-311.impl-review.codex.md`
   - `PRD-312.impl-review.claude.md`
   - `PRD-313.impl-review.claude.md`
5. Reverify `origin/main`, registry `next_prd`, current process, and exact line
   seam. If another PRD takes 315, use the then-current number; do not force it.

This packet does not perform step 4 because no new PRD is being saved and the
user prohibited allocation. The registry repair is governance bookkeeping and
must not be bundled into the production/test FILES ceiling.

### 17.2 Future PRD core

Suggested single-sentence goal:

> Make Opportunity Survival and the existing Candidate Board one continuous
> operator read by relocating the complete Candidate emission block after the
> Opportunity conditional and before Alert, with no internal or semantic
> change.

Suggested header facts, subject to the reviewed current process:

```text
CLASS: CONSUMER
LANE: STANDARD
MATERIAL: YES
MAX EXPECTED DELTA: 138 production lines relocated, zero net production LOC
CHANGE SURFACE: mandatory
```

Exact product/test FILES payload:

```text
cuttingboard/delivery/dashboard_renderer.py
tests/test_dash_core.py
tests/test_dash_candidates.py
tests/test_dash_system_state.py
tests/test_dashboard_renderer.py
tests/data/dashboard_pre_gex_golden.html
```

The PRD must cite the exact review-clean packet SHA and Dustin's ruling, name
the PRD-112/177/312 contract supersession, and reproduce the cut list rather
than saying “reorder Candidate” without bounds.

### 17.3 Mandatory future fail conditions

Stop before or during implementation if:

1. Candidate cannot move as one unchanged contiguous block.
2. Candidate or Opportunity extracted HTML changes for the same input.
3. Candidate becomes gated by Opportunity, permission, HALT, or a new carrier.
4. Opportunity counts/population are joined to Candidate cards.
5. Any content, CSS, disclosure, level/invalidation, grade/state, health,
   lineage, lock, HALT, permission, or provenance semantic changes.
6. Any second production file or sixth test/golden payload file is required.
7. Net production LOC is nonzero or the 138-line relocation ceiling is
   exceeded.
8. A schema, producer, runtime, notification, report, workflow, publication,
   persistence, or generated-UI edit is proposed.
9. The no-GEX golden delta is not same-fragment relocation only.
10. PRD-314 CSS, Market State markup/text, or Opportunity child order changes.
11. `QUALIFIED 0` plus independent B Candidate cannot be rendered truthfully.
12. HALT/lock no longer dominates or Candidate stale/unavailable state loses
    its independent wording/clocks.
13. Browser evidence shows overflow, clipping, hidden minimum Candidate data,
    visual/DOM reordering, or lost accessibility at a required width.
14. The cosmetic/layout proof fails; reclassify HIGH-RISK rather than
    continuing under STANDARD.
15. The packet lacks exact-head confirmation, Dustin ruling, reviewed PRD, or
    explicit Gate A.

### 17.4 Review and implementation mechanism

The primary implementation mechanism is exactly one in-place source-order
relocation inside `render_dashboard_html()`. Review should be optimized around
proof that nothing else happened:

- one same-lines deletion/insertion in production;
- depth-aware order assertions;
- pre/post Candidate and Opportunity fragment hashes;
- explicit independent-carrier contradiction fixture;
- exact PRD-314 and context regressions;
- deterministic golden audit;
- six-width browser order/overflow evidence;
- final impact/change-scope detection and manual changed-file check.

Do not combine disclosure, visual-family wrappers, or desktop-layout work with
this slice. Those remain non-blocking research observations from the lab, not
part of the safest first production migration.

### 17.5 Final product-design verdict

**DESIGN CLEAN — READY FOR DUSTIN/HELM RULING**

The design is clean because the desired continuity is achievable through one
bounded, reversible emission-order move without changing any truth, carrier,
gate, permission, candidate, context, or provenance semantic. The independent
review found no detailed Context surface that must precede Candidate. Alert is
better placed after the broad Candidate observation while remaining a separate
narrow policy-gated population.

This verdict is a product-design conclusion, not a claim that the packet is
already GOV-2 review-clean. The exact corrected commit still needs independent
SHA-pinned confirmation before Dustin can make a binding design-direction
ruling. No PRD is allocated, no implementation is authorized, and no PR is to
be opened from this packet.

STOP FOR HELM DESIGN RULING.
