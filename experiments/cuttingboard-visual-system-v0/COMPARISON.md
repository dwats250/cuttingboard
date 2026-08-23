# Visual System Comparison

## Outcome

**Variant C — Dense Responsive Desk is the winning direction.**

It is the only prototype that satisfies both ends of the operating problem at once:

- At `390x844`, candidate identity is fully present in the initial viewport and the candidate level begins after only `49px` of scroll.
- At `1280x800`, MARKET STATE, SYSTEM STATE, Opportunity Survival, the full candidate minimum read, and the opening GEX/Movement comparison all intersect the initial viewport.
- At `768x1024`, it remains a single column; desktop density does not leak into tablet.
- Across every tested fixture and width, it has zero horizontal overflow and no hidden critical state or provenance.

Variant B is the calmest long-form reading system and contributes important zone behavior to the recommendation. Variant A is the safest production migration bridge. Neither matches C's combined phone/desktop operating speed.

## Measurement method

All measurements come from [measurements.json](measurements.json), generated in headless Google Chrome at device scale 1 with the prototype toolbar hidden.

Definitions:

- **Top through Survival**: board top to the bottom of the Opportunity Survival surface.
- **Top through Opportunity zone**: board top to the end of the complete opportunity family, including candidate minimum read and closed safe disclosures.
- **Level scroll**: scroll needed before the candidate level receives its first visible pixel / becomes fully visible.
- **Bordered before candidate**: fully bordered containers ending before candidate identity.
- **Context top**: initial document Y coordinate of GEX, the first context surface.
- **Initial visibility**: intersection with the viewport at `scrollY=0`; every non-empty fixture still renders identity, level, and invalidation in the DOM.
- **Surface intersects fold**: any part of the surface appears in the initial viewport.

## Phone — 390x844, NORMAL LONG-CONTENT

| Measure | A — Evolutionary | B — Zoned | C — Dense Desk |
|---|---:|---:|---:|
| Top through Opportunity Survival | 876.3px | 915.1px | **806.1px** |
| Top through complete Opportunity zone | 1267.2px | 1298.9px | **1136.0px** |
| Scroll before candidate level starts | 177px | 206px | **49px** |
| Scroll before candidate level is fully visible | 230px | 260px | **99px** |
| Full bordered containers before candidate | 3 | **1** | **1** |
| GEX/context starts at document Y | 1275.2px | 1346.2px | **1165.3px** |
| Scroll before GEX/context starts | 431px | 502px | **321px** |
| Horizontal overflow | 0px | 0px | 0px |
| Candidate identity in initial viewport | No | No | **Yes — fully** |
| Candidate level in initial viewport | No | No | No |
| Invalidation in initial viewport | No | No | No |
| Identity / level / invalidation rendered | Yes / Yes / Yes | Yes / Yes / Yes | Yes / Yes / Yes |

Interpretation:

- A is materially clearer than the current universal-card board, but three complete bordered objects still precede candidate identity.
- B feels calmer because one State zone replaces two cards, yet family padding makes it the tallest phone read.
- C earns its density: the complete candidate identity is in the fold at 390px, and a small deliberate scroll reaches level and invalidation.
- At 430px, C shows candidate identity and level in the initial viewport; the 390px result is the harder constraint.
- At 360px, all three wrap critical strings without clipping or horizontal overflow. C retains a four-metric Opportunity row; A/B use the more relaxed 2x2 grid.

## Desktop — 1280x800, NORMAL LONG-CONTENT

| Measure | A — Evolutionary | B — Zoned | C — Dense Desk |
|---|---:|---:|---:|
| Board box used | 1040px (81.3%) | 1200px (93.8%) | **1280px (100%)** |
| Approx. inner content width | 988px | 1148px | **1232px** |
| Surfaces intersecting fold | 4 | 4 | **6** |
| Surfaces fully above fold | 2 | 2 | **4** |
| Candidate identity visible | Yes | Yes | Yes |
| Candidate level visible | No | **Yes** | **Yes** |
| Candidate invalidation visible | No | **Yes** | **Yes** |
| Context surfaces intersecting fold | 0 | 0 | **2** |
| Context comparison columns | 2 below fold | 2 below fold | **2 in fold** |
| Horizontal overflow | 0px | 0px | 0px |

Surfaces intersecting the fold:

- **A:** Market State, System State, Opportunity Survival, Candidate. Candidate identity only; level is below the fold.
- **B:** Market State, System State, Opportunity Survival, Candidate. Candidate identity, level, and invalidation all fit.
- **C:** Market State, System State, Opportunity Survival, Candidate, GEX, and Market Movement. The complete candidate minimum read fits, and Context begins as a true two-column comparison.

C's `1280px` board box includes `24px` internal padding on each side; it is not edge-to-edge content. At `1440px` the board caps at `1360px`, preventing unbounded ultrawide spread.

## Architectural comparison

| Question | A — Evolutionary | B — Zoned | C — Dense Desk |
|---|---|---|---|
| Visual starting point | Familiar cards with stronger State type | One dominant State zone | Compact State comparison band |
| Opportunity continuity | Survival and Candidate become adjacent | Survival and Candidate share one zone | Survival and Candidate form a comparison pair |
| Card economy | Better, but still card-led | Best family-level reduction | Panels on desktop; low chrome on phone |
| Context subordination | Lighter cards and explicit labels | Strongest semantic zone separation | Explicit context band, visible earlier |
| Phone rhythm | Familiar and forgiving | Calm, but vertically expensive | Fastest; most deliberately compact |
| Desktop use | Moderate | Strong | Strongest |
| Tablet behavior | One column | One column | One column |
| Deep navigation | Familiar scrolling | Clearest five-zone mental map | Efficient bands with native disclosure |
| Production migration risk | Lowest | Medium | Highest of the three |

## Exception-state validation

| Fixture | What remained unmistakable | Result |
|---|---|---|
| HALT | stale board, SYSTEM HALT, HALT decision, SYSTEM HALT · NO TRADE, `disk full` reason, unavailable session state | PASS in A/B/C at 390 and 1280 |
| DEGRADED / CARRIER UNAVAILABLE | primary warning, STATE UNAVAILABLE, NO AUTHORIZATION, last-known environment, independent GEX/Movement/Red Folder clocks | PASS in A/B/C at 390 and 1280 |
| RED-FOLDER EVENT PRESENT | event warning, event count in MARKET STATE, CPI name/time/detail, unchanged permission, conditional Session Observation and Market Control lower on the board | PASS in A/B/C at 390 and 1280 |
| NO CANDIDATE | zero setup count, explicit NO DEVELOPING SETUPS surface, no fabricated identity/level/invalidation, Context remains available | PASS in A/B/C at 390 and 1280 |

Across all `42` captures:

- horizontal overflow failures: `0`
- critical-content failures: `0`
- provenance visibility failures: `0`
- disclosure targets below 44px: `0`
- tablet desktop-grid leakage: `0`

## Decision questions

### 1. Which variant provides the fastest trustworthy 10-second read?

**C.** On phone it is the only variant with complete candidate identity inside the first viewport. On desktop it presents separate Market and System authority, complete candidate minimum read, and the first Context comparison without implying a composite verdict.

### 2. Which gives the best 30-second context read?

**C.** GEX and Movement are already visible as a paired context row at `1280x800`. On phone, Context begins `181px` earlier than B and `110px` earlier than A. The explicit `CONTEXT READ · NEVER AUTHORIZATION` label prevents speed from becoming semantic ambiguity.

### 3. Which gives the best 2-minute deep read?

**B.** Its five-zone mental model is the easiest to retain over a full-board read. Internal hairlines make the large content set calmer, and conditional Session/Control detail has a natural home. The winning C direction should steal this zone grammar below the first two bands.

### 4. Which performs best on phone?

**C.** It has the shortest state-to-candidate path, one full border before candidate, complete candidate identity in the 390px fold, and no overflow at 360px. A is more familiar; B is calmer but slower.

### 5. Which performs best on desktop?

**C.** It uses the available width for comparison while preserving one source order. It is the only variant to expose GEX and Movement above the `1280x800` fold without hiding state or candidate minimums.

### 6. Which requires the least dangerous production migration?

**A.** Typography roles, scoped spacing, lighter borders, and limited desktop pairing can be sliced without immediately introducing family wrappers or broad ordering changes. Its lower risk is valuable even though it is not the final architecture.

### 7. Which features from losing variants should be stolen by the winner?

From B:

- one bordered family rather than a border around every inner surface
- numbered family labels and internal hairlines
- the calm five-zone mental model for the lower board
- event detail treated as a bridge inside State

From A:

- familiar surface names and conservative typography
- forgiving 2x2 Opportunity metrics as a fallback below the narrowest widths if four columns prove too dense with production fonts
- incremental migration seams that do not require the full architecture at once

### 8. What current dashboard patterns should be permanently retired?

- one universal full-border `.block` for every surface
- the permanent `640px` desktop cap
- candidate identity separated from Opportunity Survival by all context
- provenance rendered at the same weight as current values
- repeated full-card padding/gaps across the entire board
- mobile tables converted into unlabeled bordered mini-cards
- full visual-card treatment for no-change history and Scoreboard
- tiny text-only disclosure targets
- a healthy-empty Red Folder surface when Event Risk already carries the fact
- using desktop width only as empty margin

### 9. What must remain untouched?

- MARKET STATE and SYSTEM STATE as separate authorities
- environment distinct from permission
- state first, trades second
- context never authorizing a trade
- freshness, halt, lock, event risk, and critical unavailability always visible
- candidate identity, level, and invalidation always visible when a candidate exists
- Cboe delay and configured positioning-assumption qualifiers
- independent carrier clocks; no fake synchronized global `as of`
- unavailable/degraded truth, including repeated `VWAP N/A` where it is the honest value
- production semantic color contracts until separately governed
- no predictive hero, global score, or synthetic bullish/bearish conclusion
- one continuous board on phone
