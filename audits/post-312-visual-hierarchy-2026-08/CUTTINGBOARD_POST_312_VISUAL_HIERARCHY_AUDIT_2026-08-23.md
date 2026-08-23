# CUTTINGBOARD POST-312 VISUAL HIERARCHY AUDIT

Cuttingboard can become materially calmer and faster to scan without removing the detailed GEX, Movement, Macro, Trend, candidate, history, or provenance information. The central problem is not excess information; it is that state, context, candidates, and history are presented with almost the same visual container, spacing, and heading treatment.

## 1. CURRENT VISUAL DIAGNOSIS

Baseline was reconfirmed during this pass:

- Main: `592e991b89b576fe8bda6af35854c14779e4dd9a`
- Publish: `77e9fc8b0780133994058f5a8fb82daf60ed1a3d`
- Public artifact: [Cuttingboard production board](https://dwats250.github.io/cuttingboard/)
- Public SHA-256: `c5f451cc98f6b0360f41ec661e2af533236b3aa9ce5977bb6fa29ca9f65a289f`
- The public hash matches both `ui/index.html` and `ui/dashboard.html` at the pinned publish SHA.
- Pages deploys `ui/` from `publish`, as shown in [pages.yml](/home/dustin/Projects/cuttingboard/.github/workflows/pages.yml:30).

Current rendered order:

1. Freshness/staleness banner
2. MARKET STATE
3. SYSTEM STATE
4. OPPORTUNITY SURVIVAL
5. GEX
6. MARKET MOVEMENT
7. MACRO TAPE
8. RED FOLDER
9. TREND STRUCTURE
10. MARKET MAP / DEVELOPING SETUPS
11. CHANGES SINCE LAST RUN
12. SCOREBOARD

Currently absent conditional surfaces:

- ALERT WATCHLIST
- SPY SESSION OBSERVATION
- MARKET CONTROL
- Sunday-only context
- Artifact/coherence warning and expanded diagnostics

The renderer confirms that order in [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2327), with candidate and history beginning much later at [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:3001).

### Core diagnosis

- Eleven information surfaces plus the staleness banner use the same `.block` rule: one-pixel border, 16px padding, and 16px bottom gap. The CSS source is [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:762).
- Across 12 blocks, padding and inter-card gaps alone consume approximately 576px of vertical travel before counting any data.
- All section headings use the same small, muted `0.8rem` uppercase treatment.
- Almost all data uses the same body size. Primary axis values, long provenance, qualifiers, contextual prices, and historical rows therefore compete in one visual voice.
- The only unmistakably large text is SYSTEM STATE. Even there, `OBSERVE ONLY` is green because the visual class follows the expansion regime, while the adjacent text says `CANNOT MONITOR · NO TRADE`. That is visually ambiguous: green currently encodes environmental state and can be mistaken for permission.
- The board is capped at 640px at every viewport. A 1280px monitor therefore receives roughly the same vertical presentation as a tablet, surrounded by unused space.
- Mobile behavior is narrowly optimized for Trend Structure only. The rest of the dashboard simply stacks and wraps.
- The conceptual reading order breaks after Opportunity Survival: the count says one setup exists, but its SPY identity, level, and invalidation appear only after GEX, Movement, Macro, Red Folder, and Trend Structure.

The board is functionally coherent but visually flat. It has section order, but not enough section hierarchy.

## 2. VISUAL WEIGHT MAP

| Surface | Current visual weight | Weight it should have | Finding |
|---|---|---|---|
| Freshness/staleness, when old | PRIMARY | PRIMARY | Correctly prominent. It should remain a compact warning strip above everything. |
| Freshness, when healthy | DIAGNOSTIC | DIAGNOSTIC | The persistent UPDATED timestamp is sufficient; a large healthy banner is unnecessary. |
| MARKET STATE | PRIMARY | PRIMARY | Correct position, but its five axes and metadata currently share one typographic weight. |
| SYSTEM STATE | PRIMARY | PRIMARY | Correct importance. Decision, halt, and operator lock must remain unmistakable. |
| OPPORTUNITY SURVIVAL | SECONDARY | SECONDARY | Important bridge between state and candidates, but its five vertical rows are taller than the information requires. |
| GEX | SECONDARY | DETAIL | High-value positioning detail, but explicitly context-only and should not compete with permission. |
| MARKET MOVEMENT | SECONDARY | SECONDARY | Useful daily breadth/leadership context; compact enough to remain visible lower on the page. |
| MACRO TAPE | SECONDARY | SECONDARY | Macro bias and pressure are useful context, but the driver and price grids should not rival current state. |
| RED FOLDER: healthy-empty | SECONDARY | DIAGNOSTIC | The separate PRD-313 lane handles its conditional absence. No expansion is recommended here. |
| RED FOLDER: event present | SECONDARY | SECONDARY | Detailed event names/times should remain visible near the state zone. |
| RED FOLDER: unavailable/error | SECONDARY | PRIMARY | Critical event-data unavailability must pierce the hierarchy as a warning. |
| TREND STRUCTURE | SECONDARY | DETAIL | High-value multi-symbol interpretation, but naturally lower-page structure rather than first-screen state. |
| MARKET MAP / DEVELOPING SETUPS | SECONDARY | PRIMARY | This is the actual answer to “what is tradable?” and should lead the Opportunity family. |
| CHANGES SINCE LAST RUN | SECONDARY | DETAIL | Valuable when changed; visually excessive when it contains one no-change line. |
| SCOREBOARD | SECONDARY | DETAIL | Calibration/history, not current-session decision state. |
| SPY SESSION OBSERVATION | SECONDARY when rendered | SECONDARY | Daily/session context. It should be clearly cadence-labeled and grouped with session structure. |
| MARKET CONTROL | SECONDARY when rendered | SECONDARY | Its transition/invalidation can matter, but its daily permission/event repetitions must remain subordinate to current state authority. |
| Alert Watchlist | SECONDARY when rendered | SECONDARY | Belongs beside candidate opportunity, not between state and context. |
| Sunday-only context | SECONDARY when rendered | SECONDARY | Useful conditional context, but not a new permanent top-level hierarchy. |
| Artifact warning | PRIMARY when rendered | PRIMARY | Integrity failures must override ordinary card hierarchy. |
| Artifact diagnostics | DIAGNOSTIC | DIAGNOSTIC | Existing collapsed disclosure is appropriate. |

## 3. MOBILE / TABLET / DESKTOP FOLD ANALYSIS

The current public artifact was captured in headless Chrome at approximately 390×844, 768×1024, and 1280×800.

| Viewport | Visible today before the fold | What should be visible |
|---|---|---|
| 390px phone | `BOARD 12h OLD`; all MARKET STATE; all SYSTEM STATE; all OPPORTUNITY SURVIVAL; only the start of GEX | Freshness/updated state; complete MARKET STATE and SYSTEM STATE; a compact Opportunity Survival summary; and, when one exists, candidate identity plus level and invalidation. |
| 768px tablet | Staleness; MARKET STATE; SYSTEM STATE; OPPORTUNITY SURVIVAL; all GEX; upper portion of Movement | Complete state and opportunity read; candidate summary; at least the opening context summary. Keep one column at this width unless real content proves a two-column state layout legible. |
| 1280px desktop | Staleness; MARKET STATE; SYSTEM STATE; OPPORTUNITY SURVIVAL; only the upper GEX rows | Two-column state zone, an opportunity row containing both counts and candidate, and the opening GEX/Movement context row. |

If the stale banner is hidden, approximately 65px becomes available. The more important issue remains: 768px and 1280px both render a 640px column, so additional desktop width currently produces no information-density benefit.

### Ideal first visual zone

Using only current information, the first zone should answer:

1. Is this board current?
2. What environment and event state exist?
3. Is the system halted or locked?
4. Is trading permitted?
5. Did anything survive, and what is the leading existing candidate?

GEX walls, the full 12-symbol Movement tape, Macro drivers, and Trend rows can follow. They help interpret the read; they should not be prerequisites for discovering whether a trade is allowed or whether a candidate exists.

## 4. GROUPING FINDINGS

| Proposed family | Actual members | Does the grouping hold? | Reason |
|---|---|---|---|
| STATE | Freshness, MARKET STATE, SYSTEM STATE, integrity warnings | YES | These jointly answer whether the board is trustworthy, what environment exists, and whether action is permitted. They must remain separate semantic carriers inside one visual family. |
| OPPORTUNITY | OPPORTUNITY SURVIVAL, Alert Watchlist, MARKET MAP candidates | YES, strongly | Counts explain survival; candidates supply identity, level, and invalidation. Their current physical separation is the largest conceptual break. |
| CONTEXT | GEX, MARKET MOVEMENT, MACRO TAPE | YES | These explain positioning, participation detail, daily movement, and macro pressure. None grants permission. |
| STRUCTURE / SESSION | TREND STRUCTURE, SPY SESSION OBSERVATION, MARKET CONTROL | YES, with cadence labeling | They describe price location, VWAP/ORB, alignment, transition, and invalidation. Daily-only cards must not masquerade as hourly state. |
| DETAIL / HISTORY | CHANGES SINCE LAST RUN, SCOREBOARD, diagnostics | YES | These answer “what changed?” and “how has this behaved?” rather than “what do I do now?” |
| RED FOLDER detail | Conditional bridge between STATE and CONTEXT | CROSS-CUTTING | The top-axis event summary belongs to STATE. Detailed event rows belong immediately below state when present. An error belongs in the critical warning lane. |

Grouping should reduce the number of perceived objects, not create five new full bordered cards. The useful approach is section spacing and one family heading, with lighter internal separators.

Introducing Amon-style product tabs would conflict with Cuttingboard’s “one board” direction. Grouping should preserve a continuous page.

## 5. CARD + TYPOGRAPHY + SPACING FINDINGS

### Card economy

- The universal `.block` treatment makes MARKET STATE, empty Red Folder, Trend Structure, and Scoreboard look like peers.
- There are borders around every major block, six additional bordered mobile Trend rows, a bordered candidate card, and internal separators. The nesting is most visible on phone.
- Full 16px vertical padding and 16px gaps are reasonable for three or four cards, but expensive across twelve.
- Context and history can use section separators or a shared family container rather than separate complete boxes.

### Typography

- The current hierarchy is essentially:

  - SYSTEM decision: 1.4rem
  - Everything else: approximately 0.7–1rem

- MARKET STATE’s main values and provenance are emitted together inside one `.value`; see [market_state_panel.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/market_state_panel.py:99). This makes `EXPANSION`, `as of 00:49 ET`, the Cboe delay, and the positioning-assumption qualifier equally prominent.
- Per-axis provenance should remain visible but use a smaller, muted metadata role.
- Headings need at least two roles:

  - Family heading: STATE, OPPORTUNITY, CONTEXT, STRUCTURE, HISTORY
  - Surface heading: MARKET STATE, GEX, MARKET MOVEMENT, and so on

- Monospace still serves the product well for levels, percentages, symbols, timestamps, and status. A wholesale font or aesthetic replacement is not justified.

### Color

- Color is generally semantic and restrained.
- Current System coloring is overloaded: `OBSERVE ONLY` and `NO TRADE` appear green because the class comes from `EXPANSION`. That deserves a separate explicit color-contract decision, not an incidental CSS cleanup.
- State changes, halt, unavailability, and actionable level/invalidation accents should receive color. Routine headings and borders should not.

### Mobile-specific density

- At 390px, body padding leaves about 358px for a card; card padding leaves about 326px for content.
- Long MARKET STATE provenance wraps repeatedly and is the main first-zone height driver.
- OPPORTUNITY SURVIVAL uses five vertical label/value rows where four numeric metrics could safely use a compact grid and PRIMARY REJECTION could remain full width.
- Macro’s second driver row contains four values but uses a three-column grid, producing an orphan final item.
- Trend Structure’s mobile reflow is compact, but hides the table header and turns each symbol into another bordered mini-card. The reader must remember the cell order.
- Candidate diagrams are 280×110 and fit the phone, but consume meaningful vertical space after the already-visible level and invalidation.
- Existing disclosure summaries are styled as small `0.72rem` text. Any new mobile disclosure control should be a full-width, approximately 44px tap row rather than a tiny text target.

## 6. PROGRESSIVE DISCLOSURE FINDINGS

| Information | Treatment | Constraint |
|---|---|---|
| Board age, UPDATED timestamp, stale/closed state | ALWAYS VISIBLE | Never require interaction. |
| MARKET STATE: environment, permission, positioning, participation, event risk | ALWAYS VISIBLE | Main values prominent; per-axis provenance muted but still visible. |
| SYSTEM STATE: decision, halt, operator lock, reason | ALWAYS VISIBLE | Must remain independent from context. |
| Critical carrier or event-data unavailability | ALWAYS VISIBLE | Do not bury inside an expanded section. |
| Opportunity counts | COMPACT SUMMARY | Four metrics can share space; primary rejection remains readable. |
| Candidate identity, grade/state, level, invalidation | ALWAYS VISIBLE when candidate exists | These are the minimum tradability read. |
| Candidate reason/play/watch | EXPANDABLE DETAIL | Already correctly collapsed. |
| Candidate level diagram | EXPANDABLE DETAIL | Safe to subordinate after level and invalidation remain visible. |
| GEX net, dominant, walls, 0DTE | COMPACT SUMMARY / LOWER-PAGE DETAIL | The current five values are already compact; preserve qualifier and as-of visibly. |
| MARKET MOVEMENT’s 12 values | LOWER-PAGE DETAIL, normally expanded | It is compact and genuinely changes interpretation; no forced disclosure is necessary. |
| Macro bias, vote tally, pressure availability | COMPACT SUMMARY | Keep visible. |
| Macro driver and tradable-price grids | EXPANDABLE DETAIL | Safe if missing/degraded state and relevant provenance remain outside the disclosure. |
| TREND STRUCTURE rows | LOWER-PAGE DETAIL, normally expanded | High-value comparison surface; moving it lower is safer than requiring a tap every time. |
| SPY Observation / Market Control | COMPACT SESSION SUMMARY | Preserve date/cadence, transition, invalidation, and degraded state. |
| CHANGES SINCE LAST RUN | COMPACT SUMMARY | A real change stays visible; no-change can remain a one-line history item. |
| SCOREBOARD | LOWER-PAGE / EXPANDABLE DETAIL | Calibration history does not belong in the immediate decision read. |
| Artifact diagnostics | EXPANDABLE DETAIL | Existing pattern is correct; integrity warning itself remains visible. |

Trend’s repeated `VWAP N/A` should not be casually collapsed into silence. The renderer explicitly preserves the Intraday column even when other uniformly unavailable columns can collapse. Any future consolidation would need one visible, section-level unavailability statement and an explicit product ruling.

## 7. AMON HEN: FIVE TRANSFERABLE LESSONS MAX

The comparison is limited to the current visual behavior of [Amon Hen’s Atlas view](https://amonhen.helmfi.ai/), not its trading model or features.

### 1

AMON HEN DOES: Maintains a compact status strip with ticker, price, regime, key levels, and market state above the main analysis.

WHY IT WORKS: The reader receives orientation without opening or reading the dominant panel.

CUTTINGBOARD ANALOG: Freshness, environment, permission, event state, and decision lock should form one visually coherent state zone.

DO NOT COPY: Its regime vocabulary, gamma conclusions, price signals, or ticker controls.

### 2

AMON HEN DOES: Gives one panel dominant visual weight, then places explanatory metrics and level detail underneath or beside it.

WHY IT WORKS: Dense content still has an obvious starting point.

CUTTINGBOARD ANALOG: MARKET STATE and SYSTEM STATE should dominate; context cards should be visibly subordinate even when fully present.

DO NOT COPY: A predictive prose hero or a bullish/bearish market verdict.

### 3

AMON HEN DOES: Uses different typography roles for branded heading, narrative read, numeric levels, labels, and notes.

WHY IT WORKS: Primary reading, numbers, and explanation are distinguishable before the words are parsed.

CUTTINGBOARD ANALOG: Retain monospace, but separate decision text, axis values, labels, and provenance through size, weight, and muted color.

DO NOT COPY: Its serif brand language or visual theme.

### 4

AMON HEN DOES: Uses broad desktop grids and intentionally collapses those grids into a single mobile column.

WHY IT WORKS: Desktop width enables comparison; phone width remains readable rather than compressed.

CUTTINGBOARD ANALOG: GEX and Movement can share a desktop row, while phone remains one column. State can become two columns only at a width where long permission and provenance text remain legible.

DO NOT COPY: Dense chart layouts or side rails on phone.

### 5

AMON HEN DOES: Keeps explanations subordinate through notes, tabs, tooltips, and secondary panels while retaining a clear current-state read.

WHY IT WORKS: Supporting education does not visually compete with the live read.

CUTTINGBOARD ANALOG: Keep provenance visible, but visually mute it; keep candidate level/invalidation open while placing diagrams and reasons in deliberate disclosure.

DO NOT COPY: Multi-mode navigation as Cuttingboard’s primary architecture. Cuttingboard should remain one board.

## 8. PHONE TEXT WIREFRAME

```text
[CRITICAL STATUS — ALWAYS UNOBSTRUCTED]
  BOARD AGE / CLOSED / INTEGRITY WARNING, when applicable
  UPDATED timestamp remains visible even when healthy

[STATE — PRIMARY, ALWAYS EXPANDED]
  MARKET STATE
    ENVIRONMENT      main value | muted own as-of
    PERMISSION       emphasized value | muted own as-of
    POSITIONING      main value | muted as-of + visible qualifier
    PARTICIPATION    main value | muted captured time
    EVENT RISK       main value | visible source/unavailability

  SYSTEM STATE
    DECISION STATE
    OPERATOR LOCK / HALT / PERMISSION VERDICT
    reason/context
    UPDATED

[WHAT MATTERS TODAY — CONDITIONAL]
  RED FOLDER event names/times, only when present
  RED FOLDER unavailable warning, if degraded
  no healthy-empty standalone block after the separate PRD-313 work

[OPPORTUNITY — SECOND VISUAL ZONE]
  OPPORTUNITY SURVIVAL
    SURFACED | SETUPS
    WATCHLIST | REJECTED
    PRIMARY REJECTION

  MARKET MAP / DEVELOPING SETUPS
    candidate identity / grade / state / structure
    LEVEL — always visible
    INVALIDATION — always visible
    [DETAIL: reason / watch / play]
    [LEVEL MAP: diagram]

[CONTEXT — LOWER PAGE, LIGHTER CHROME]
  GEX
    all existing values
    as-of and positioning qualifier visible

  MARKET MOVEMENT
    existing five group rows
    captured time visible

  MACRO TAPE
    bias / vote tally / availability
    [DRIVERS + TRADABLE PRICES]

[SESSION / STRUCTURE — LOWER PAGE]
  SPY SESSION OBSERVATION, when present
  MARKET CONTROL, when present
  TREND STRUCTURE compact symbol rows

[DETAIL / HISTORY]
  CHANGES SINCE LAST RUN
  [SCOREBOARD]
  [DIAGNOSTICS]
```

All disclosure rows should be comfortably tappable. Hover-only explanation has no role in critical phone information.

## 9. DESKTOP TEXT WIREFRAME

```text
[CRITICAL STATUS — FULL WIDTH]

[STATE — PRIMARY]
  ┌───────────────────────────────┬──────────────────────────┐
  │ MARKET STATE                  │ SYSTEM STATE             │
  │ five axes + own provenance    │ decision / halt / lock   │
  │                               │ reason + updated         │
  └───────────────────────────────┴──────────────────────────┘

[WHAT MATTERS TODAY — CONDITIONAL FULL WIDTH]
  Red Folder event detail or degraded warning

[OPPORTUNITY]
  ┌──────────────────────┬───────────────────────────────────┐
  │ OPPORTUNITY SURVIVAL │ MARKET MAP / DEVELOPING SETUPS    │
  │ compact metrics      │ identity + level + invalidation   │
  │ rejection            │ detail/diagram subordinate       │
  └──────────────────────┴───────────────────────────────────┘

[CONTEXT — SECONDARY]
  ┌──────────────────────┬───────────────────────────────────┐
  │ GEX                  │ MARKET MOVEMENT                   │
  │ detailed levels      │ existing grouped 12-symbol tape   │
  └──────────────────────┴───────────────────────────────────┘
  ┌──────────────────────────────────────────────────────────┐
  │ MACRO TAPE — summary first, driver/price detail below    │
  └──────────────────────────────────────────────────────────┘

[SESSION / STRUCTURE — DETAIL]
  ┌──────────────────────┬───────────────────────────────────┐
  │ SPY OBSERVATION      │ MARKET CONTROL                    │
  │ conditional          │ conditional                       │
  └──────────────────────┴───────────────────────────────────┘
  ┌──────────────────────────────────────────────────────────┐
  │ TREND STRUCTURE                                           │
  └──────────────────────────────────────────────────────────┘

[DETAIL / HISTORY]
  ┌──────────────────────┬───────────────────────────────────┐
  │ CHANGES              │ SCOREBOARD                        │
  └──────────────────────┴───────────────────────────────────┘
  [DIAGNOSTICS — COLLAPSED UNLESS WARNING]
```

The wider layout should activate only around 900–960px, not at nominal tablet width where long permission and provenance strings would make side-by-side state cards cramped.

## 10. TOP FIVE VISUAL REFINEMENTS

### 1. Compact and differentiate the first-screen state zone

- Exact current problem: MARKET STATE, SYSTEM STATE, and OPPORTUNITY SURVIVAL occupy almost the entire phone fold. MARKET STATE values and their provenance share one visual weight.
- Proposed visual change: Add scoped first-zone roles; distinguish axis value from metadata; tighten phone padding and inter-block spacing; render Opportunity counts as a compact metric grid with rejection full width.
- Information removed: NO
- Semantic change: NO
- Likely production files: [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:762), [market_state_panel.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/market_state_panel.py:99)
- Likely tests: `tests/test_market_state_panel.py`, `tests/test_dashboard_renderer.py`, `tests/test_dash_system_state.py`, `tests/test_staleness_banner.py`; browser captures at 390/768/1280.
- Risk: MEDIUM—five-axis structure, exact wording, source order, and decision-state classes are heavily pinned.
- Expected phone impact: Largest immediate improvement; shorter wraps and a clearer state-versus-metadata read.
- Expected desktop impact: Cleaner hierarchy, although full width utilization remains a later slice.

### 2. Restore Opportunity continuity

- Exact current problem: Opportunity Survival reports one setup, but five context surfaces separate that count from the candidate’s identity and invalidation.
- Proposed visual change: Move MARKET MAP / DEVELOPING SETUPS directly after Opportunity Survival; keep identity, level, and invalidation open; place the SVG level diagram in its own disclosure.
- Information removed: NO
- Semantic change: NO
- Likely production files: [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:1865)
- Likely tests: `tests/test_dash_candidates.py`, `tests/test_dash_level_diagram.py`, `tests/test_dashboard_renderer.py`, `tests/test_dash_system_state.py`.
- Risk: MEDIUM-HIGH—the current `system-state … candidate-board` interval and multiple ordering tests are deliberate contracts.
- Expected phone impact: Very high; “anything tradable?” no longer requires passing through all context.
- Expected desktop impact: High; counts and candidate can be read as one opportunity family.

### 3. Replace repeated card chrome with section hierarchy

- Exact current problem: Twelve top-level blocks receive approximately 576px of padding/gap overhead and almost identical borders.
- Proposed visual change: Introduce STATE, OPPORTUNITY, CONTEXT, STRUCTURE, and HISTORY presentation families; use one family boundary or spacing change, with inner surfaces separated by hairlines rather than full boxes.
- Information removed: NO
- Semantic change: NO
- Likely production files: `dashboard_renderer.py`, `market_state_panel.py`, `gex_card.py`, `movement_card.py`.
- Likely tests: Renderer ordering/fragment tests for every affected block plus responsive browser captures.
- Risk: MEDIUM—broad visual cone despite no data or decision changes.
- Expected phone impact: Large reduction in scroll and nested-border noise.
- Expected desktop impact: Large reduction in the impression that every card is equally important.

### 4. Use desktop width for comparison

- Exact current problem: `.wrap{max-width:640px}` makes 768px and 1280px presentations nearly identical.
- Proposed visual change: At a conservative desktop breakpoint, widen the content region and pair related surfaces—MARKET STATE with SYSTEM STATE, GEX with Movement, and history cards together—while preserving phone as one column.
- Information removed: NO
- Semantic change: NO
- Likely production files: `dashboard_renderer.py`; possibly fragment class hooks in `market_state_panel.py`, `gex_card.py`, and `movement_card.py`.
- Likely tests: CSS mechanism assertions plus 768/900/1280 browser captures and long/degraded content fixtures.
- Risk: MEDIUM—long qualifiers, tables, and conditional card omission can create uneven grids.
- Expected phone impact: None by design.
- Expected desktop impact: Very high; faster side-by-side comparison and far less unused space.

### 5. De-chrome mobile dense rows and history

- Exact current problem: Trend creates six bordered mini-cards, Macro’s four-item row wraps 3+1, and history retains full card treatment.
- Proposed visual change: Use lighter row separators in Trend, a balanced mobile Macro grid, and subordinate History styling/disclosure. Preserve every symbol value and every unavailable state.
- Information removed: NO
- Semantic change: NO
- Likely production files: [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:897)
- Likely tests: `tests/test_dashboard_renderer.py`, `tests/test_dashboard_renderer_macro_tape.py`, `tests/test_dash_run_history.py`, Trend Structure tests, and phone captures at 360/390/430px.
- Risk: LOW-MEDIUM—mostly CSS, but Trend’s exact wrapping has regression tests.
- Expected phone impact: High lower-page readability and less repetitive chrome.
- Expected desktop impact: Low to moderate.

## 11. SMALLEST NEXT VISUAL SLICE AFTER PRD-313

### First-screen state-zone compaction

Make one presentation-only change limited to:

- MARKET STATE
- SYSTEM STATE
- OPPORTUNITY SURVIVAL
- Their phone spacing and type hierarchy

Bounded behavior:

1. Preserve every existing string, axis, qualifier, timestamp, class contract, and rendered order.
2. Inside MARKET STATE’s existing `.value` cells, add presentation hooks that distinguish:

   - Main axis value
   - Per-axis provenance
   - Positioning qualifier

3. Keep all three visible without interaction.
4. At 360–430px:

   - Reduce scoped card padding and gaps.
   - Use smaller, muted provenance text.
   - Keep permission and unavailable states visually stronger.
   - Reflow the four Opportunity counts into a 2×2 grid.
   - Keep PRIMARY REJECTION full width.

5. Do not:

   - Move candidates
   - Add section navigation
   - Change colors
   - Change Red Folder behavior
   - Add disclosure
   - Widen desktop
   - Touch any producer, carrier, schema, runtime, ingestion, or decision logic

Likely production cone:

- [market_state_panel.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/market_state_panel.py:103)
- [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2327)
- Generated publish artifacts: `ui/dashboard.html`, `ui/index.html`
- No workflow logic change; the existing hourly renderer continues generating both files through [hourly_alert.yml](/home/dustin/Projects/cuttingboard/.github/workflows/hourly_alert.yml:152).

Likely test cone:

- `tests/test_market_state_panel.py`
- `tests/test_dashboard_renderer.py`
- `tests/test_dash_system_state.py`
- `tests/test_staleness_banner.py`
- Existing readiness/publish checks
- Before/after browser captures at 360, 390, 430, 768, and 1280px

Visual acceptance should require:

- All five axes and every qualifier remain in the DOM and visible.
- No global synchronized as-of is introduced.
- MARKET STATE remains before SYSTEM STATE.
- Staleness, permission, halt, event risk, and critical unavailability require no tap.
- The 390px view is visibly easier to parse and exposes more of the next surface than the current baseline.
- No tablet or desktop wrapping regression.

This is smaller and safer than reordering candidates or introducing board-wide section wrappers, while proving the role-based hierarchy needed for those later changes.

## 12. DO-NOT-TOUCH LIST

- Do not hide freshness, UPDATED, permission, halt, operator lock, environment, event risk, or critical unavailability behind disclosure.
- Do not visually merge MARKET STATE and SYSTEM STATE into a new composite verdict. Group them, but preserve their distinct authority and provenance.
- Do not replace per-carrier clocks with one global as-of.
- Do not hide or abbreviate the Cboe delay and configured-positioning-assumption qualifier into a tooltip.
- Do not remove detailed GEX levels, Movement values, Macro context, Trend rows, candidate level/invalidation, or provenance.
- Do not collapse candidate level or invalidation. Only reason/watch and the existing diagram are safe disclosure candidates.
- Do not treat repeated `VWAP N/A` as decorative noise and silently delete it; degraded-state honesty must remain visible.
- Do not use color alone to communicate permission or availability.
- Do not casually recolor `OBSERVE ONLY` as part of a CSS cleanup. The existing green/regime relationship is a semantic color contract and needs an explicit ruling.
- Do not introduce Amon-style trading modes, signals, gamma interpretation, or a predictive hero.
- Do not make tabs the gateway to state. Cuttingboard remains one board.
- Do not use hover-only explanations for phone-critical information.
- Do not widen the desktop layout by squeezing the same multi-column grid onto 390–768px screens.
- Do not create small text-only disclosure targets; any new phone disclosure must have a full-width tap area.
- Do not expand PRD-313 beyond its separately authorized healthy-empty Red Folder suppression.

## 13. FINAL VERDICT

The board does not need another information cut to become calmer; it first needs a visible hierarchy that makes state dominant, opportunity contiguous, and context/history deliberately subordinate.

No repository files were modified during this audit. A separate process switched the shared clean checkout to `claude/prd-313-stage0` during the pass; all findings above remain pinned to the supplied main and publish SHAs, and no PRD-313 work was inspected or expanded.

VISUAL NEXT: compact the existing MARKET STATE, SYSTEM STATE, and OPPORTUNITY SURVIVAL first-screen zone at phone widths using scoped spacing and value-versus-provenance typography, with zero information, ordering, color, carrier, or semantic changes.
