# CUTTINGBOARD OPPORTUNITY CONTINUITY DEEP RECON

**Date:** 2026-08-23

**Status:** PROVISIONAL READ-ONLY PRODUCTION-MIGRATION RECON — NOT A PRD, NOT
IMPLEMENTATION AUTHORITY

**Repository baseline:** `dwats250/cuttingboard` `main` at
`8bf3b58a98120c43860a689756d84950a0b3aadb`

**Visual-lab input:** `experiment/cuttingboard-visual-system-v0` at
`85579e6b81fc40882bb137f5bdc8c0fe3c3d4816`

**Proposed future classification:** `CLASS: CONSUMER`, `LANE: STANDARD`,
`MATERIAL: YES`, subject to the narrow move-only boundary in section 10

This artifact answers one question only: can the existing production
`MARKET MAP / DEVELOPING SETUPS` surface be emitted immediately after
`OPPORTUNITY SURVIVAL` without changing what either surface means? The answer
is **yes**, provided the first slice is a verbatim emission-order move. It must
not include disclosure, styling, family wrappers, candidate redesign, carrier
work, or any change to decision-bearing visibility.

The proposed destination is:

```text
MARKET STATE
SYSTEM STATE
OPPORTUNITY SURVIVAL        when its existing validity gate passes
MARKET MAP / DEVELOPING SETUPS
ALERT WATCHLIST             when present
CONTEXT                     existing GEX, Movement, session, Macro,
                            Red Folder, and Trend surfaces in their
                            existing relative order
CHANGES SINCE LAST RUN
SCOREBOARD
```

This is visual continuity, not a data join. Opportunity Survival and Candidate
remain independently carried and independently truthful. Their adjacency may
never claim that a displayed market-map candidate is one of the payload
survivors.

## 1. BASELINE

### 1.1 Authority and isolation

The recon was performed in a separate worktree and docs-only branch created
from the exact live `origin/main` head above. The active PRD-314 worktree was
not modified. The Visual System Lab's `COMPARISON.md` and `RECOMMENDATION.md`
were read at their pinned commit. Their finding that Opportunity continuity is
the lab's highest-value architectural change is treated as the question to
investigate, not as implementation authority. Prototype HTML, CSS, JavaScript,
measurements, and component boundaries are not used as production source.

The prior visual-hierarchy audit at
`c2299f9f7358ccbea2109b79a616717f34a97024` and first-screen recon at
`19178e504ef0a41caf54e544aacbcc61c047d174` were used as research inputs rather
than repeated. In particular, they establish the visual problem, the current
System-to-Candidate interval, and the safe/non-safe disclosure boundary. The
repository at the pinned production baseline is the authority for current
behavior.

Process disclosure: during a broad governance-history lookup, a short
committed PRD-314 stub was inadvertently opened from a remote ref. No
implementation diff, implementation file, or active worktree was inspected or
changed; the stub was excluded from this recon's evidence. No further query of
that ref was made.

### 1.2 Verification baseline

The following renderer-focused suite passed before any report file was added:

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

619 passed
```

GitNexus was refreshed at the pinned head and reported 17,825 symbols, 28,241
relationships, and 201 flows. Its Python extraction reported scope failures
for the large renderer and several related tests. Consequently, its upstream
impact result for `render_dashboard_html` — LOW, zero callers, zero processes —
is known-incomplete and is **not** the basis for the file cone. Manual call-site,
workflow, test, and generated-output tracing supplies the authoritative cone
below.

### 1.3 Terms used in this recon

- **Opportunity** means the top-level `#opportunity-survival` block emitted
  from finalized pipeline payload counts.
- **Candidate** means the complete top-level `#candidate-board` block headed
  `Market Map / Developing Setups`.
- **Continuous** means no other top-level dashboard surface is emitted between
  Opportunity and Candidate when Opportunity is present. It does not mean
  shared styling, a wrapper, or shared data.
- **Minimum candidate read** means identity/symbol, grade, setup state, level or
  entry when present, and invalidation when present, under their current
  conditional semantics.
- **Verbatim move** means the candidate emission block's bytes and internal
  branch order are unchanged; only its location inside `render_dashboard_html`
  changes.

## 2. CURRENT ORDER GRAPH

### 2.1 Renderer entry and call graph

The production HTML is assembled by
`cuttingboard/delivery/dashboard_renderer.py:2044-3238` in
`render_dashboard_html(...)`. All carrier loading and most semantic
normalization precede block emission. The relevant call graph is:

```text
dashboard_renderer.main()                         line 3404
  -> load payload/run/market-map/sidecar inputs
  -> _load_contract_entry_context()               line 3313
  -> write_dashboard()                            line 3242
       -> coherent-publish validation
       -> render_dashboard_html()                 line 2044
            -> gex_card.render_fragment()
            -> movement_card.render_fragment()
            -> _render_candidate_card()           line 1865
                 -> _render_level_diagram()       line 1598
       -> write generated dashboard artifact
```

Preview scripts, selected workflows, and tests also call the renderer or writer
directly. No caller passes an ordering plan and no caller consumes candidate
markup by its neighbor. Ordering is controlled entirely by sequential `w(...)`
calls inside `render_dashboard_html`.

### 2.2 Exact current top-level emission order

Line numbers below refer to the pinned main head and are navigation aids, not
stable API. “Always” means the top-level block is emitted; its content may show
an existing unavailable or disabled state.

| # | Surface / DOM ID | Baseline source | Presence gate | Principal input |
|---:|---|---|---|---|
| 0 | Artifact coherence / Sunday premarket notices | before state blocks | Conditional | Run/payload lineage and schedule |
| 1 | Staleness scaffolding / `#staleness-banner` and updated clock | before Market State | Always | Pipeline/payload timestamp with client age check |
| 2 | MARKET STATE / `#market-state` | around line 2340 | Always | Hourly-first five-axis projections with per-axis provenance |
| 3 | SYSTEM STATE / `#system-state` | lines 2363-2520 | Always | Run decision state, permission, reason, environment, integrity |
| 4 | OPPORTUNITY SURVIVAL / `#opportunity-survival` | lines 2522-2611 | Conditional coherent positive-scan funnel | Payload `meta` and `sections` |
| 5 | Alert Watchlist / `#alert-watchlist` | lines 2613-2625 | `alert_candidates` non-empty | Latest-hourly contract gate results |
| 6 | GEX / `#gex-context` | lines 2627-2635 plus `gex_card.py` | Fresh, valid in-domain fragment only; otherwise true omission | GEX sidecar and its own clock/provenance |
| 7 | Market Movement / `#market-movement` | lines 2637-2644 plus `movement_card.py` | Valid schema-v2 fragment only; otherwise true omission | Movement sidecar and its own provenance |
| 8 | SPY Observation / `#spy-observation` | lines 2646-2677 | Daily payload section present | Daily payload section |
| 9 | Market Control / `#market-control-card` | lines 2679-2704 | Daily section present | Daily payload section |
| 10 | Sunday Macro Context / `#sunday-macro-context` | lines 2706-2735 | Coherent Sunday state | Run/payload schedule context |
| 11 | Macro Tape / `#macro-tape` | lines 2737-2846 | Always | Macro snapshot with current unavailable behavior |
| 12 | Red Folder / `#red-folder` | lines 2848-2887 | Event/default/failure rules; healthy resolved-empty may suppress | Red-folder sidecar and its own state |
| 13 | Trend Structure / `#trend-structure` | lines 2889-3010 | Always | Trend sidecar with degraded-state rows |
| 14 | MARKET MAP / DEVELOPING SETUPS / `#candidate-board` | lines 3012-3148 | Always at wrapper level | Market-map carrier plus lifecycle and optional contract diagram overlay |
| 15 | Changes Since Last Run / `#run-delta` | lines 3150-3196 | Always | Current and previous run |
| 16 | Scoreboard / `#scoreboard` | lines 3198-3232 | Always | Run/history aggregates |

Thus the current Opportunity-to-Candidate interval can contain Alert
Watchlist, GEX, Movement, two daily session cards, Sunday context, Macro Tape,
Red Folder, and Trend Structure. Which surfaces actually intervene varies by
carrier health, schedule, and fixture. Candidate discoverability therefore
changes with unrelated context availability.

### 2.3 Current authority order

The semantic authority order at the top is already correct and must not be
collapsed:

```text
MARKET STATE       broad observed condition; five independent axes
SYSTEM STATE       execution permission / halt / lock authority
OPPORTUNITY        pipeline survival accounting, when coherent
```

Moving Candidate after Opportunity does not place it above either authority.
The candidate's own scope line remains mandatory:

```text
OBSERVATION ONLY — setup quality never overrides Decision State or Permission.
```

That line is the explicit guard against reading candidate quality as
authorization.

## 3. CANDIDATE DATA / VISIBILITY GRAPH

### 3.1 Independent carriers

Opportunity and Candidate are produced from different already-finalized
inputs:

```text
pipeline payload
  meta.symbols_scanned
  sections.rejected[]
  sections.watchlist[]
       |
       +-> render_dashboard_html Opportunity validity gate
             -> surfaced / qualified-or-setups-found / watchlist / rejected
             -> modal terminal rejection reason

market_map.v1
  symbols.{symbol}
  removed_symbols[]
       |
       +-> market_map_lifecycle.inject_lifecycle()
       |
       +-> render_dashboard_html Candidate availability/tiering
             -> _render_candidate_card()
                  -> always-open minimum candidate text when supplied
                  -> existing DETAIL disclosure
                  -> _render_level_diagram()

latest_hourly_contract (independent optional overlay)
       |
       +-> _load_contract_entry_context()
             -> contract entry/stop maps for candidate diagram only
             -> Alert Watchlist candidates when execution policy gates them
```

There is no join from Opportunity counts to candidate symbols and no candidate
filter based on Opportunity's qualified count. The proposed adjacency must
preserve that fact in code, tests, and copy. A `QUALIFIED 0` funnel can
truthfully coexist with a `B — DEVELOPING` market-map card because the two
surfaces answer different questions from different carriers.

### 3.2 Opportunity presence and semantics

At `dashboard_renderer.py:2522-2611`, Opportunity renders only when all of the
following current conditions hold:

- artifact lineage is healthy;
- `meta.symbols_scanned` is a real positive integer, explicitly not `bool`;
- `sections.rejected` and `sections.watchlist` are lists;
- every rejected record is a dictionary.

Continuation promotions are removed from terminal rejections and from the
surface's double-count before counts are derived. The qualified count is the
remaining surfaced population. The primary rejection is a deterministic mode
over sanitized existing reason strings. Under operator lock, the label changes
from `QUALIFIED` to `SETUPS FOUND`; the count does not change. Missing,
malformed, zero-scan, or unhealthy-lineage input suppresses the entire block
rather than emitting a partial or misleading funnel.

### 3.3 Market-map production and card inputs

`cuttingboard/market_map.py:116-244` builds `market_map.v1` and its symbol
records. `_build_symbol_record()` supplies, among other fields:

- `symbol`, `grade`, `setup_state`, `bias`, `structure`, and `confidence`;
- current price and watch zones;
- Fibonacci context;
- `what_to_look_for`;
- `invalidation`;
- preferred trade structure;
- reason for grade;
- `trade_framing`, including entry, upgrade, and downgrade text.

The current grade-to-state logic includes `B -> DEVELOPING` at
`market_map.py:203-204`. `market_map_lifecycle.inject_lifecycle()` at
`cuttingboard/market_map_lifecycle.py:39` augments records with lifecycle
information and removed symbols; it does not determine DOM placement.

Daily production reads the shared market map. Hourly production uses its
isolated hourly market-map path and passes it explicitly. The move changes
neither path. It creates no synchronized global “as of” and does not change
which clock belongs to which carrier.

### 3.4 Candidate wrapper states

The top-level Candidate wrapper is always emitted. Its current branches are:

- unhealthy lineage: no tier header or card; show `STALE MARKET MAP`,
  `SOURCE_MISSING`, `PARSE_ERROR`, or the generic unavailable lineage state;
- stale lineage diagnostic: show both selected-run and market-map timestamp
  labels;
- coherent but source missing or parse error: show that status;
- inactive session: show the existing session-inactive label;
- `market_map is None`: show `N/A`;
- empty `symbols`: show `NO_CANDIDATES`;
- populated map: show integrator skip lines, idle verdicts as applicable,
  ordered grade tiers, cards, and removed symbols.

The displayed tier order is defined by `_TIER_DEFS` at
`dashboard_renderer.py:755-760`: A+, A, B, then collapsible C. Symbols inside a
tier are alphabetic after grade ordering. A+/A/B comprise `_HIGH_GRADES`.
Existing D/F omission behavior is outside this recon and must not be silently
changed while moving the block.

### 3.5 Candidate card visibility

`_render_candidate_card()` at `dashboard_renderer.py:1865-2041` owns the
candidate's internal visibility contract.

Always outside the candidate-detail disclosure when the underlying current
record provides it:

- symbol / identity;
- grade;
- setup state except its existing unavailable exception;
- bias and structure;
- lifecycle status;
- `trade_framing.entry`, rendered as actionable entry or neutral `LEVEL`
  according to current lock behavior;
- the first invalidation item, plus the current non-redundant structural
  downgrade clause.

Already inside a default-collapsed native
`<details class="card-detail">` with `DETAIL` summary:

- reason for grade;
- play / preferred trade structure;
- watch / what-to-look-for.

Currently outside disclosure:

- the SVG level diagram, when sufficient current-price and level context
  exists.

Under operator lock, analytical facts remain. `IF NOW` and `PLAY` action
language is suppressed, entry/stop labels become `LEVEL` and `INVALIDATION`,
and A+ is presented as observation only. This logic lives inside the existing
candidate block and must move unchanged.

### 3.6 Level diagram

`_render_level_diagram()` at `dashboard_renderer.py:1598-1862` builds a
deterministic explanatory SVG from current price, watch/Fibonacci zones, and
optional contract entry/stop overlay. Current price is required. Contract
entry and stop do not replace the card's textual level/invalidation; the
diagram is supplementary. A stale contract clears the entry overlay, and a
stop is not drawn without its entry. Under lock, diagram labels and styling
are neutralized by existing logic.

### 3.7 Relevant DOM and styling hooks

The move must preserve these identifiers/classes unchanged:

- top level: `#opportunity-survival`, `#alert-watchlist`,
  `#candidate-board`, `#run-delta`;
- candidate grouping: `.candidate-scope`, `.tier-group`, `.tier-header`,
  `#tier-aplus`, `#tier-a`, `#tier-b`, `#tier-c`;
- cards: `.candidate-card`, grade modifier classes, `#card-{symbol}`,
  `.card-header`, `.label`, `.value`, and the existing dynamic value class;
- subordinate content: `.card-detail`, `.lvl-diagram`, `.lvl-unavail`;
- lifecycle/failure/removal: `.lifecycle-badge` and its modifier,
  `.lifecycle-detail`, `.failed-card-fields`, `.removed-symbols`, and
  `.removed-row`;
- wrapper/status: `.block` plus the current disabled modifier,
  `.idle-summary`, and `.unavailable`.

No CSS adjacent-sibling selector, client JavaScript, notification formatter,
report parser, or workflow step depends on Candidate's current sibling. The
only runtime marker consumer found outside rendering is
`scripts/check_readiness.py`, which requires `id="candidate-board"` but does
not assert position.

## 4. ORDERING CONTRACT INVENTORY

The current location is a combination of deliberate historical ordering and
later accumulation. It is not carrier-dependent, but neither is it safe to
call accidental.

| Constraint | Evidence | Classification | Consequence for a move |
|---|---|---|---|
| System State precedes Candidate | PRD-116 and renderer tests, including `tests/test_dashboard_renderer.py:1731-1760`; core order tests | **HARD SEMANTIC CONTRACT** | Preserve. Candidate remains below System. |
| Macro -> Red Folder -> Trend -> Candidate -> Changes -> Scoreboard | PRD-177's four-question sequence; `tests/test_dash_core.py:152-182` | **HARD HISTORICAL SEMANTIC CONTRACT** | A future PRD must explicitly supersede Candidate's relative position, not merely update a brittle test. Keep the context surfaces' relative order. |
| Trend before Candidate | PRD-112 plus trend extraction/order tests around `tests/test_dashboard_renderer.py:1443-1450` and `1888-1901` | **HARD HISTORICAL SEMANTIC CONTRACT** | Explicitly supersede only the cross-family relation. Do not alter Trend's content/order. |
| Opportunity immediately follows System | PRD-282; source and tests in `tests/test_dash_system_state.py:491-720` | **HARD SEMANTIC CONTRACT when Opportunity is valid** | Preserve. Candidate is inserted after Opportunity, not between System and Opportunity. |
| Opportunity occurs before Alert Watchlist | PRD-282's explicit source seam | **HARD SEMANTIC CONTRACT** | Preserve. Candidate is inserted between them, but Opportunity remains before Alert and retains its exact gate. |
| Market State immediately precedes System and stays outside the protected interval | PRD-312 and `tests/test_dashboard_renderer.py:3917-3945` | **HARD SEMANTIC CONTRACT** | Preserve separate blocks and Market-before-System order. Rewrite the old interval sentinel so it protects System itself rather than requiring all context before Candidate. |
| The `system-state..candidate-board` interval is a protected placement seam | PRD-312, its MATERIAL packet/confirmations, the source comment around `dashboard_renderer.py:2340`, and test splits | **EXPLICITLY GOVERNED HISTORICAL BOUNDARY** | A future PRD must supersede the interval-as-boundary definition. It must retain PRD-219's actual `#system-state`-block protections and the ban on duplicating raw permission/internals; historical audit artifacts remain immutable. |
| System-to-Candidate interval is used as a test extraction boundary | Numerous splits in `tests/test_dash_system_state.py`; protected-region assertion in renderer tests | **TEST-ONLY HISTORICAL PIN layered over semantic tests** | Replace with exact top-level block extraction. Do not let Candidate's new location cause System tests to consume Opportunity/Candidate markup. |
| Alert Watchlist before Candidate | `tests/test_dash_candidates.py:674-679` | **TEST-ONLY HISTORICAL PIN** | Reverse the positional assertion while preserving Alert's presence/content contract. PRD-102 does not establish Candidate-relative semantic dependence. |
| Macro pressure/evidence is inside Macro Tape and occurs before Candidate | PRD-092's old disclosure contract, superseded internally by PRD-217; residual assertion at `tests/test_dashboard_renderer.py:300-316` | **HARD MACRO-INTERNAL CONTRACT plus TEST-ONLY CANDIDATE BOUNDARY** | Preserve the evidence line inside Macro Tape. Supersede only the use of Candidate as its trailing positional sentinel. |
| GEX before Candidate | PRD-309 placement and current sequential source | **VISUAL EXPECTATION / ACCUMULATED ORDER** | No semantic dependency. Move unchanged into post-Candidate Context. |
| Movement before Candidate | PRD-311 placement and current sequential source | **VISUAL EXPECTATION / ACCUMULATED ORDER** | No semantic dependency. Move unchanged into post-Candidate Context. |
| SPY Observation and Market Control before Candidate | PRD-288/289 and current source | **VISUAL EXPECTATION** | Preserve their relationship to each other; Candidate may precede both. |
| Macro before Red Folder before Trend | PRD-112/177 and PRD-313 suppression tests, including `tests/test_dashboard_renderer.py:3819-3850` | **HARD CONTEXT-INTERNAL CONTRACT** | Preserve exactly. Candidate moves as a whole ahead of this chain. |
| Red Folder healthy resolved-empty may disappear while Macro still precedes Trend | PRD-313 | **HARD SEMANTIC CONTRACT** | Unaffected. Critical event truth already remains above Candidate in Market State. |
| Candidate tiers and cards sorted by grade then symbol | candidate tests and `_TIER_DEFS` | **HARD CANDIDATE-INTERNAL CONTRACT** | Preserve byte-for-byte. |
| Candidate visibility independent of permission; A+/A/B remain visible | PRD-098, PRD-304, candidate/system tests | **HARD SEMANTIC CONTRACT** | Preserve. Never gate the moved block on Opportunity, permission, or HALT. |
| Whole rendered HTML equals pre-GEX golden when optional cards absent | `tests/test_dashboard_renderer.py:4462-4493` and `tests/data/dashboard_pre_gex_golden.html` | **GOLDEN / TEST PIN** | Regenerate deterministically from its fixed fixture after the intended order change. Do not hand-edit. |
| Candidate marker exists in published HTML | `scripts/check_readiness.py` | **HARD PRESENCE CHECK, NO ORDER CONTRACT** | Unaffected. |
| Older Candidate-before-System order | PRD-073 R5 | **STALE / EXPLICITLY SUPERSEDED CONTRACT** | Do not revive it; later PRD-116/177 state-first requirements control. |
| Generated `ui/dashboard.html` / `ui/index.html` reflect current order | tracked publish artifacts and workflow rendering | **GENERATED VISUAL SNAPSHOT, NOT SOURCE AUTHORITY** | Let normal future publication regenerate them; do not name or hand-edit them in the move PRD. |
| Candidate location relied on by CSS/JS/notification/report logic | repo-wide selector and consumer trace | **NO CONTRACT FOUND** | No dependent code change is justified. |

### 4.1 Why Candidate is currently low

The historical sequence is:

1. Macro and Candidate existed before today's state architecture.
2. Candidate visibility and stale protection were made explicit.
3. Alert Watchlist and Trend were inserted with their own requirements.
4. PRD-177 deliberately ordered the board as a four-question vertical read,
   leaving Candidate after Macro/Red Folder/Trend.
5. System State and then Opportunity were added above that chain.
6. Daily session cards, GEX, Movement, and Market State were later inserted at
   their own seams.

Therefore the long interval is partly governed legacy and partly feature-by-
feature accumulation. No discovered producer, carrier, lineage check, or
consumer requires Context to render before Candidate. The old semantic intent
must be consciously replaced by the newer doctrine — State, then Opportunity,
then Context — while retaining all truth guards.

## 5. STATE MATRIX

“Immediately after Opportunity” below means Candidate is the next top-level
surface whenever Opportunity's existing gate passes. When Opportunity is
suppressed, Candidate follows System directly; no empty Opportunity shell is
invented.

| State | Opportunity result | What appears next under the proposed move | Required truth guard |
|---|---|---|---|
| 1. Normal developing candidate | Valid funnel with current counts | Candidate wrapper, B tier, symbol/grade/`DEVELOPING`, level, invalidation, existing Detail, and diagram if valid | Scope line remains; no link asserted between funnel survivor and market-map symbol. |
| 2. Multiple developing candidates | One valid funnel | B tier with current count and all B cards in current alphabetic order | Do not show only the first candidate or create carousel/tab hiding. |
| 3. No candidate | Valid funnel if scan is positive | `NO_CANDIDATES` in Candidate | If scan is zero or malformed, Opportunity is absent and System -> Candidate remains truthful. |
| 4. Rejected / no-survivor funnel | `QUALIFIED 0` (or `SETUPS FOUND 0` under lock), rejection count/reason | Candidate's independent current state: often `NO_CANDIDATES`, but it may truthfully contain low-grade or B observations | Add regression for `QUALIFIED 0` plus B `DEVELOPING`; adjacency must not synthesize “survived.” |
| 5. Operator lock | Valid funnel relabels `QUALIFIED` to `SETUPS FOUND` | Candidate renders current locked presentation: observation-only A+, neutral `LEVEL`/`INVALIDATION`, no `IF NOW`, no `PLAY` | Lock remains controlled by System; moving the card must not change analytical counts or card availability. |
| 6. HALT | Existing System State prominently shows HALT; Opportunity follows only if otherwise valid | Candidate still follows with its existing observation-only scope and current card logic | Do not opportunistically change HALT candidate language in this slice. Current HALT-vs-lock nuance is a separate semantic question. |
| 7. Candidate carrier unavailable | Opportunity is suppressed when the shared artifact lineage is unhealthy; it may otherwise be independently valid for non-lineage map absence | Candidate follows System or Opportunity and shows `SOURCE_MISSING`, `PARSE_ERROR`, `N/A`, stale clocks, or generic unavailable state; no cards/tiers under unhealthy lineage | Preserve run and market-map clock labels independently. Never substitute Opportunity for candidate availability. |
| 8. GEX unavailable | Opportunity unchanged | Candidate appears next; detailed GEX fragment remains truly omitted | Market State's Positioning axis remains the above-Candidate critical summary and keeps delayed-source/positioning-assumption qualifiers. |
| 9. Movement unavailable | Opportunity unchanged | Candidate appears next; detailed Movement fragment remains truly omitted | Market State's Participation axis remains independently unavailable/degraded as today. |
| 10. Red-folder event present | Opportunity unchanged | Candidate appears next; detailed Red Folder event follows later in the unchanged Context chain | Market State's Event Risk axis remains above Candidate, so critical event risk is not deferred below a trade surface. |
| 11. Stale board | Client staleness banner remains above Market State; Opportunity depends on server-side lineage as today | Candidate follows using current market-map health branch; its own stale diagnostic remains distinct | No synchronized fake global clock; board age and carrier lineage remain separate. |
| 12. Daily/hourly mismatch | Opportunity uses the selected coherent payload; may suppress on incoherence | Hourly uses isolated hourly market map; daily uses shared daily map. Daily-only SPY/Market Control cards move below Candidate; hourly omits them | Do not load a different map to make adjacency look coherent. Sunday/inactive labels remain as today. |

Additional conditional surface: when Alert Watchlist is present, it becomes the
first top-level surface after Candidate. It remains contract-gated context and
is not merged into Candidate.

## 6. SMALLEST SAFE MOVE

### 6.1 Mechanism

The smallest production mechanism is one source-order relocation inside
`render_dashboard_html`:

1. Cut the complete block beginning at the `# --- candidate-board ---` comment
   and ending after its matching final `w("</div>")` immediately before
   `# --- run-delta ---` (pinned baseline lines 3012-3148).
2. Paste that block immediately after the Opportunity conditional closes and
   before `# --- alert-watchlist ---` (the seam after baseline line 2611).
3. Make no edits inside the moved block.

This is approximately 137 relocated source lines, zero intended net production
LOC, no new helper, and no changed signature. The resulting source order is:

```text
Market State
System State
Opportunity conditional
Candidate Board (always emitted)
Alert Watchlist conditional
GEX conditional
Movement conditional
daily/session conditional surfaces
Macro Tape
Red Folder conditional
Trend Structure
Changes
Scoreboard
```

When Opportunity is absent, Candidate naturally follows System. Do not wrap
Candidate in the Opportunity `if`; do not manufacture a placeholder; do not
compute a candidate list from Opportunity counts.

### 6.2 Invariants for a verbatim move

- Candidate HTML for the same inputs is byte-identical as an extracted
  top-level fragment before and after the move.
- Opportunity HTML and its presence decision are byte-identical.
- Alert, GEX, Movement, session, Macro, Red Folder, Trend, Changes, and
  Scoreboard fragments are byte-identical and retain their mutual order.
- Market State and System State remain separate siblings in the same order.
- No candidate carrier, schema, source-health gate, lineage classification,
  grade threshold, tier order, permission gate, or lock translation changes.
- No CSS or JavaScript uses `order` to create a visual order different from
  DOM/source order.
- No generated dashboard output is edited by hand.

### 6.3 Why not extract a renderer helper first

`docs/renderer_decomposition_map.md` correctly identifies Candidate as a
branch-heavy decision-bearing renderer region and says any future extraction
should move it verbatim. That is not a prerequisite for this order move.
Combining extraction with relocation adds function-signature, argument,
closure-state, and fragment-parity risk without improving continuity. Perform
the move in place; treat renderer decomposition, if ever authorized, as a
separate future slice.

## 7. DISCLOSURE ANALYSIS

### 7.1 First slice verdict: no disclosure change

Disclosure is not required to achieve Opportunity continuity and must be cut
from the first slice. Candidate reason, play, and watch text are already in a
native collapsed `<details class="card-detail">`. The level diagram is the only
listed safe candidate that is currently always open.

The minimum read must remain open:

- identity/symbol;
- grade and setup state;
- entry or neutral level when the current record supplies it;
- invalidation when the current record supplies it.

“Always visible” means not put behind a disclosure; it does not authorize
inventing values when the current carrier omits them.

### 7.2 Existing reason/play/watch disclosure

The existing native `<details>` is keyboard and screen-reader operable without
custom JavaScript, and its content remains in the DOM. Its current summary is
visually small and does not establish a reliable 44px touch target. Improving
that target, label, focus treatment, or expanded-state cue is useful but is a
separate presentation slice. It should not be coupled to the order move.

### 7.3 Possible later diagram disclosure

The level diagram can be evaluated later as an independently reversible slice
because it is supplementary to open text. Any later implementation must:

- keep textual level and invalidation outside disclosure;
- use a native `<details>/<summary>` or an equivalently complete accessible
  control;
- provide an unambiguous accessible name and visible expanded/collapsed state;
- support Enter and Space with a full-width minimum 44px target at phone width;
- preserve the SVG's descriptive text and all existing lock-neutral labels;
- leave the information in source order directly after the candidate minimum
  read.

Custom click-only JavaScript, manual `aria-expanded` state, or hiding the sole
level/invalidation representation would fail. This recon does not authorize
that later slice.

## 8. CONTEXT CONSEQUENCES

### 8.1 What moves below Candidate

Alert Watchlist, GEX, Market Movement, conditional daily/session context,
Macro Tape, Red Folder detail, and Trend Structure would all begin after the
Candidate block. Changes and Scoreboard already do and remain there.

Their internal and mutual order remains:

```text
Alert Watchlist, if present
GEX, if present
Movement, if present
SPY Observation, if present
Market Control, if present
Sunday Macro Context, if present
Macro Tape
Red Folder, if emitted
Trend Structure
Changes
Scoreboard
```

### 8.2 Semantic consequence by surface

- **GEX:** no candidate filter or authorization dependency. Net/dominant/walls,
  0DTE, delayed-source qualifier, positioning-assumption qualifier, provenance,
  and clock remain unchanged. The critical broad positioning result is already
  summarized above Candidate in Market State.
- **Movement:** no candidate dependency. Detailed 12/12 movement becomes
  post-candidate context; the above-Candidate Market State Participation axis
  remains the critical summary.
- **Macro:** no producer or renderer requirement to precede Candidate. It
  becomes supporting context after the narrow opportunity read.
- **Red Folder:** an event's critical risk remains above Candidate through the
  Market State Event Risk axis. The detailed event record can remain later.
- **Trend:** historically positioned before Candidate, but no data dependency
  exists. It becomes explanatory structure after the candidate read.
- **SPY Observation / Market Control:** daily-only context follows Candidate;
  no cards are synthesized on hourly boards.
- **Changes / Scoreboard:** unchanged after all decision/context content.
- **Alert Watchlist:** remains a distinct contract-gated surface immediately
  after Candidate. It must not be folded into the market-map carrier or read as
  the same candidate population.

### 8.3 Doctrine fit

The resulting board follows:

```text
State authority -> Opportunity read -> Context -> History/detail
```

That is a better match for “State first. Trades second. Context may inform;
Context may never authorize” than requiring every context surface to precede
candidate discovery. It does not weaken “Observe wide. Trade narrow” because
Market State retains the wide critical summaries above Candidate and every
detailed context surface remains present below.

No discovered source must precede Candidate for semantic reasons. The move's
main semantic risk is perceived linkage between the independent Opportunity
and market-map populations. Preserve the candidate scope line and add the
explicit zero-survivor/developing-candidate regression to make that non-linkage
testable.

## 9. EXACT FILE CONE

### 9.1 Smallest plausible production/test cone

The bounded future slice should name exactly these six payload files:

| File | Why it changes |
|---|---|
| `cuttingboard/delivery/dashboard_renderer.py` | Relocate the existing Candidate emission block in place, with no internal edit. |
| `tests/test_dash_core.py` | Replace the PRD-177 full-order expectations with the explicitly superseding continuity order while retaining System-first and context-internal checks. |
| `tests/test_dash_candidates.py` | Reverse the Alert-before-Candidate historical position test; add/adjust direct Candidate-continuity assertions without weakening Alert content tests. |
| `tests/test_dash_system_state.py` | Replace System-to-Candidate and Opportunity-to-Alert substring sentinels with exact top-level block extraction so System and Opportunity tests remain scoped after Candidate moves. |
| `tests/test_dashboard_renderer.py` | Update old Macro/Trend/Candidate order assertions, protected-region extraction, and integration expectations; retain all content/health assertions. |
| `tests/data/dashboard_pre_gex_golden.html` | Deterministically regenerate the fixed rendered baseline whose only intended structural delta is Candidate position. |

No new test helper is required. Local exact-block helpers in the already
affected test modules are sufficient; adding `tests/dash_helpers.py` would pad
the cone unless repeated parsing proves impossible during implementation.

### 9.2 Regression-only tests: run, do not edit absent a real failure

- `tests/test_dash_level_diagram.py`
- `tests/test_gex_card.py`
- `tests/test_movement_card.py`
- `tests/test_market_state_panel.py`
- `tests/test_preview_fixtures.py`
- staleness, carrier-loading, publication, and workflow tests selected by the
  future implementer's exact diff/change-scope report

These protect unchanged semantics. A failure is evidence to investigate, not
permission to bulk-update expected output.

### 9.3 Files and outputs that must not be hand-edited

- `ui/dashboard.html` and `ui/index.html`: tracked generated/published
  dashboard artifacts, not renderer source;
- `logs/*`, `reports/output/*`, and timestamped report output;
- payload, run, market-map, contract, GEX, Movement, Trend, Macro, or Red Folder
  fixtures merely to make the move pass;
- workflows and notification/report code, for which no order consumer was
  found;
- schemas, producers, runtime, ingestion, persistence, or carrier modules.

The golden fixture is the sole generated test artifact in the file cone. It
must be regenerated from its fixed renderer fixture and reviewed as an order-
only delta, never edited to resemble the desired result.

## 10. CLASS / LANE / MATERIALITY

### 10.1 Classification

**Likely narrow-slice classification:**

```text
CLASS: CONSUMER
DEFAULT STABILITY TIER: T2
LANE: STANDARD
MATERIAL: YES
CHANGE SURFACE: mandatory
```

Reasoning:

1. `docs/PRD_PROCESS.md:418` defines the dashboard as a read-only artifact
   consumer; the class matrix at lines 456-463 assigns CONSUMER T2 and names
   `cuttingboard/delivery/dashboard_renderer.py` as a high-risk file.
2. GOV-2 section 1 makes this work MATERIAL because the recon and future seam
   selection claim exhaustive enumeration of callers, consumers, renderers,
   outputs, and the exact file cone. That single trigger is sufficient. The
   bounded move does not need to pretend it crosses schemas or pipeline layers.
3. MATERIAL work cannot use MICRO and is STANDARD at minimum. Materiality alone
   does not force HIGH-RISK.
4. The proposed source hunk touches only layout/markup emission order and
   changes none of the R12 surfaces: decision behavior, artifact/schema
   contracts, publication gates, runtime write ordering, dashboard-derived
   values, threshold/label synthesis, source-health classification, lineage
   classification, or notification truth.
5. Under the PRD-229 Cosmetic Carve-Out at `PRD_PROCESS.md:601-629`, R11's
   high-risk-file trigger does not apply to a pure layout/markup change. Since
   GOV-2 independently removes MICRO, the remaining lane is STANDARD.
6. `CHANGE SURFACE` remains mandatory because the file cone names a CONSUMER
   high-risk file; the carve-out does not erase the need to document the exact
   seam and mutation surface.

This is not a casual “cosmetic” assumption. It is a narrow conclusion that
holds only if the Candidate fragment and every truth/visibility decision remain
unchanged. The existing deliberate semantic sequence must be named and
superseded by the future PRD even though the executable change is structural.

### 10.2 Reclassification stop conditions

Stop authoring/implementation and reclassify rather than stretching this
recon if the future work would change any of the following:

- candidate grade/state/value, tier membership, order, presence, or permission
  behavior;
- Opportunity counts, gating, wording, or its carrier;
- source-health or lineage classification;
- HALT/operator-lock semantics or action-language translation;
- any carrier/schema/producer/runtime/publish-gate/notification/report
  contract;
- GEX/Movement/Macro/Trend/Red Folder truth or provenance;
- candidate disclosure in the same slice;
- a reviewer determines that superseding the PRD-177 visual sequence changes
  dashboard truth semantics under R12 rather than layout structure.

Any non-cosmetic hunk makes the whole proposed PRD non-cosmetic. Because
`dashboard_renderer.py` is then a high-risk payload file, R11 would force
`LANE: HIGH-RISK`. A discovered carrier or schema requirement is an explicit
stop: this recon's proposed implementation path would no longer apply.

### 10.3 Required governance order before a future PRD

Because this is MATERIAL, the next governance step is not implementation and
not immediate PRD allocation. GOV-2 requires the upstream packet/recon to pass
its independent review and correction sequence, exact-corrected-head
confirmation, and Dustin design-direction ruling before a durable downstream
PRD is opened. The future PRD then requires its own fresh-context independent
review and explicit Gate A. This document is provisional evidence; it does not
declare itself review-clean and cannot issue any Gate A.

## 11. ACCEPTANCE CONTRACT

The future acceptance suite should use deterministic production renderer
fixtures, not prototype markup. It must compare the pinned pre-move renderer
with the exact post-move renderer for fragment parity and measure real browser
output for order/overflow.

### 11.1 Source/DOM contract at all widths

- `#market-state < #system-state` in source and DOM order.
- When Opportunity is emitted:
  `#system-state < #opportunity-survival < #candidate-board`, and no other
  top-level `.block` occurs between Opportunity and Candidate.
- When Opportunity is suppressed: Candidate follows System as the next
  decision-zone surface; no empty Opportunity wrapper is introduced.
- Alert Watchlist, when present, follows Candidate.
- GEX, Movement, session context, Macro, Red Folder detail, and Trend occur
  after Candidate while retaining their current relative order and conditions.
- Changes and Scoreboard remain after Candidate and Context.
- Market State, System State, Opportunity, and Candidate remain separate
  semantic elements; no combined authority, composite score, or global “as of”
  is added.
- CSS must not visually reorder blocks away from DOM order.

### 11.2 Fragment-parity contract

Across the state matrix, extract complete top-level fragments with an HTML
parser or depth-aware helper. Assert:

- pre/post Candidate fragment equality;
- pre/post Opportunity fragment equality and presence equality;
- equality of every Context and History fragment;
- only the top-level Candidate position changes in the no-GEX golden;
- independent timestamps, delayed-source text, positioning-assumption text,
  source-health text, and provenance are byte-identical.

The parser must not use the current `System..Candidate`, `Trend..Candidate`, or
`Opportunity..Alert` intervals as block boundaries. Those historical sentinels
are precisely what the move supersedes.

### 11.3 Required semantic cases

At minimum test:

- one B `DEVELOPING` candidate with level and invalidation;
- multiple B candidates and existing sort order;
- valid Opportunity plus `NO_CANDIDATES`;
- valid `QUALIFIED 0` plus an independently present B candidate;
- zero-scan/malformed Opportunity suppression plus truthful Candidate;
- operator lock with `SETUPS FOUND`, neutral level/invalidation, no `IF NOW`,
  no `PLAY`;
- HALT with System dominant and Candidate content unchanged;
- stale/source-missing/parse-error market map with no tier/cards;
- GEX unavailable and Movement unavailable by true omission;
- red-folder event present with Market State event risk above Candidate;
- stale board banner plus independent candidate lineage clocks;
- daily and hourly carrier paths, including daily-only card omission on hourly.

### 11.4 390x844 acceptance

- Opportunity and Candidate identity form one continuous read: Candidate is the
  next top-level surface, separated only by the existing block margin.
- With the same long-content fixture, the Candidate identity's top rectangle is
  strictly earlier than in pinned production.
- Candidate identity is discoverable immediately after Opportunity.
- Existing level and invalidation text, when present, are visible without
  opening `DETAIL` or any new disclosure.
- Candidate scope text appears before tier/action language.
- `document.documentElement.scrollWidth <= document.documentElement.clientWidth`;
  no clipped card, SVG, label, or table creates page overflow.
- Existing native disclosure remains keyboard reachable and its content remains
  in DOM/source order.

### 11.5 1280x800 acceptance

- Market State and System State remain visually and semantically distinct from
  Candidate; no wrapper or grid implies shared authority.
- The minimum Candidate read is visible earlier than pinned production for the
  same long-content fixture.
- Context may begin after Candidate and uses the available width according to
  existing production CSS; this slice adds no new desktop layout.
- No candidate-context side-by-side composition, reordering, or hidden critical
  state is introduced.

### 11.6 Other required widths

Smoke and overflow acceptance must also cover 360x800, 430x932, 768x1024, and
1440x900. At every width:

- source order and visual order agree;
- freshness, HALT/lock, Market State event/unavailability summaries, and
  Candidate minimum text are not hidden;
- information is not communicated by color alone;
- all current provenance and independent clocks survive;
- no horizontal page overflow occurs.

Browser screenshots/measurements may be review evidence rather than committed
production harness code because the bounded move changes no CSS. The semantic
and fragment-parity assertions belong in tests.

## 12. REVERSIBILITY

The move is one independently reversible slice:

1. Relocate one contiguous source block.
2. Update exact ordering/extraction tests.
3. Regenerate one deterministic golden.

A clean revert restores the Candidate block to the seam immediately before
Changes, restores the old explicit order assertions, and regenerates the old
golden. No migration, backfill, schema compatibility window, carrier version,
feature flag, or producer rollback is needed.

Reversibility must be proven in review:

- candidate fragment parity shows the block was moved rather than rewritten;
- diff review shows zero intended net production LOC and no helper extraction;
- a focused mutation that returns Candidate to the old location makes the new
  continuity assertion fail while content tests remain green;
- Context fragments remain identical;
- `gitnexus_detect_changes()` and manual diff scope show no runtime, producer,
  contract, notification, workflow, or generated UI mutation.

Family wrappers, desktop grid work, touch-target polish, and diagram disclosure
must remain separate future decisions so each can be rejected or reverted
without undoing continuity.

## 13. RISKS

| Risk | Severity | Control |
|---|---|---|
| Adjacency implies that the market-map candidate survived the Opportunity funnel | High semantic-reading risk | Preserve the observation-only scope line; do not join carriers; add the `QUALIFIED 0` + B candidate case. |
| A brittle test update weakens System/Opportunity protections | High regression risk | Replace interval splits with exact block extraction; retain every state/content assertion. |
| Moving a large branch-heavy block accidentally edits internal logic | High implementation risk | Byte-identical fragment test, zero net production LOC expectation, line-by-line moved-block review. |
| Candidate proximity appears to override HALT or lock | High operator risk | Keep Market/System above, scope line open, current lock translations unchanged, explicit HALT/lock cases. |
| Critical Context moves below Candidate | Medium | Verify Market State retains critical GEX/Movement/Event Risk summaries and qualifiers above Candidate; keep detailed sources unchanged below. |
| Old PRD-177/112 order is silently ignored | Medium governance risk | Future PRD explicitly supersedes only Candidate's cross-family position while preserving context-internal order. |
| Alert Watchlist population is mistaken for market-map candidates | Medium | Keep separate heading/wrapper/carrier and place Alert after, not inside, Candidate. |
| Whole-output golden is manually normalized | Medium | Regenerate from fixed fixture and verify the only structural delta is block position. |
| Daily/hourly map paths are accidentally unified | High carrier risk | No loader changes; test both isolated hourly and shared daily paths. |
| “Always visible” is misread as authority to synthesize missing level/invalidation | Medium truth risk | Preserve current conditional presence; assert only that supplied text stays outside disclosure. |
| Disclosure polish expands the first slice | Medium scope risk | Cut all disclosure/CSS work; separate later slice. |
| GitNexus under-reports renderer impact due extraction failures | Medium recon risk | Treat manual call-site/test/workflow/output trace as authoritative and rerun change detection before commit/implementation. |
| Cosmetic/Standard classification is invalidated by one semantic hunk | High governance risk | Stop, rerun MATERIAL/R11/R12, and classify HIGH-RISK if any non-cosmetic renderer behavior changes. |

## 14. CUT LIST

The bounded future Opportunity-continuity slice must cut all of the following:

- Candidate redesign or new component architecture;
- shared Opportunity/Candidate wrapper or family zone;
- desktop grid, paired columns, side rails, or breakpoint changes;
- CSS, color, typography, spacing, border, or touch-target work;
- new or changed candidate disclosures;
- level-diagram disclosure;
- reason/play/watch content or summary-label changes;
- candidate grade/state thresholds, filtering, tier membership, or sort changes;
- HALT, operator-lock, permission, or action-language changes;
- Opportunity calculation, wording, gating, or primary-rejection changes;
- Alert Watchlist merge, reorder within Candidate, or carrier change;
- GEX, Movement, Macro, Red Folder, Trend, session, Changes, or Scoreboard
  redesign;
- payload, market-map, contract, sidecar, schema, producer, ingestion, runtime,
  persistence, publication, notification, report, or workflow changes;
- renderer helper extraction/decomposition;
- feature flags or dual rendering;
- hand edits to `ui/dashboard.html`, `ui/index.html`, logs, reports, or generated
  output;
- predictive score, bullish/bearish synthesis, global clock, new semantic
  color contract, or any claim that Context authorizes a trade.

If any cut item appears necessary, stop the move-only path and re-scope before
PRD authoring.

## 15. VERDICT

**PROCEED AS ONE BOUNDED FUTURE PRD**

The current Candidate surface can safely become the immediate continuation of
Opportunity through an emission-order-only relocation. The data is already in
hand before rendering; no carrier, schema, producer, visibility gate,
permission rule, or downstream consumer requires the current interval.

This verdict does **not** authorize a PRD now. Because the work selects an
exhaustively traced production seam and file cone, it is MATERIAL. This
provisional recon must first clear the GOV-2 upstream review/correction,
exact-head confirmation, and Dustin design-direction sequence. The verdict
also expires if the future slice cannot remain a byte-preserving candidate
move or if a carrier/schema change is discovered.

Do not split before PRD: the safe production change is one coherent and
reversible order move with its directly coupled tests/golden. Do split out all
disclosure, family-wrapper, and desktop-layout work before PRD authoring; none
belongs in this slice.

## 16. FUTURE PRD AUTHORING HANDOFF

This is an authoring input, not a PRD. After the upstream MATERIAL sequence is
review-clean and Dustin selects the direction, the future author should be
able to proceed without redoing repository archaeology.

### 16.1 Single-sentence goal

Move the existing `#candidate-board` emission block verbatim to immediately
after the existing Opportunity Survival conditional and before Alert Watchlist,
so State -> Opportunity -> Candidate is one source/DOM read without changing
any content, carrier, visibility, decision, permission, or provenance semantic.

### 16.2 Baseline and class

- Re-pin current `origin/main` at authoring time; do not assume this report's
  2026-08-23 SHA remains current.
- `CLASS: CONSUMER`.
- `LANE: STANDARD` only while every implementation hunk qualifies as pure
  layout/markup under the cosmetic carve-out.
- `MATERIAL: YES` due exhaustive seam/consumer/file-cone claims.
- Mandatory `CHANGE SURFACE` naming the exact renderer seam, six-file cone,
  downstream fragment surfaces, and no schema/carrier mutation.

### 16.3 Exact implementation boundary

- Production: one contiguous Candidate block move within
  `render_dashboard_html`.
- Tests: update only obsolete cross-family ordering/extraction assumptions and
  add direct continuity/fragment-parity/state cases.
- Golden: regenerate the fixed pre-GEX output; review as position-only.
- Net production LOC expectation: zero.
- No internal Candidate edit.

### 16.4 Required fail conditions

The future PRD should fail deterministically if any of these occurs:

- any top-level surface exists between valid Opportunity and Candidate;
- Candidate becomes conditional on Opportunity;
- Candidate or Opportunity fragment differs for identical inputs;
- Market State and System State cease to be separate or change order;
- candidate identity, supplied level, or supplied invalidation moves behind a
  disclosure;
- operator lock/HALT, source-health, lineage, grade, or tier behavior changes;
- a provenance clock or required GEX qualifier disappears or is synchronized;
- source and visual order diverge;
- the `QUALIFIED 0` + independently developing candidate case is rendered as a
  contradiction or joined population;
- any required width overflows horizontally;
- the diff touches a cut-list surface or generated production dashboard.

### 16.5 Review evidence expected

- exact-head repository and governance pins;
- complete staged diff and moved-block parity evidence;
- deterministic tests for all state-matrix cases;
- regenerated-golden provenance and structural diff;
- browser order/overflow evidence at 360, 390, 430, 768, 1280, and 1440 widths;
- focused old-order mutation that turns the new continuity test red;
- GitNexus change-scope result supplemented by manual inspection because the
  large renderer was not fully extracted during this recon;
- explicit confirmation that production-generated UI files, carriers,
  schemas, workflows, and notifications are untouched.

### 16.6 Reassessment triggers

Before authoring and again before implementation, re-run MATERIAL and
R11/R12 classification against the live head. Stop if intervening work changes
the candidate seam, Opportunity gate, order contracts, renderer decomposition,
or any relevant carrier. Do not depend on or alter any concurrently active
implementation branch.

NEXT: Move the existing candidate-board emission block verbatim to immediately after Opportunity Survival and before Alert Watchlist, with no disclosure, CSS, carrier, schema, gate, or candidate-content change.
