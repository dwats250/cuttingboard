# Recommendation

## Winning direction

**Advance the architectural direction of Variant C — Dense Responsive Desk. Do not advance its code.**

C is the best trading decision-support interface because it shortens the operator's path to trustworthy state and candidate facts without creating a composite verdict:

- phone keeps one source-ordered column
- candidate identity is fully visible at `390x844`
- candidate level begins after `49px` of scroll
- desktop shows separate Market/System authority, complete candidate minimum read, and a two-column GEX/Movement opening at `1280x800`
- exception states retain the same hierarchy and fail closed in text
- no information was removed to obtain the density

The mature direction should combine C's responsive comparison geometry with B's family-level calm and A's conservative production seams.

This is a recommendation from throwaway prototypes, not implementation approval. None of the HTML/CSS/JS is merge-ready.

## Five most important findings

1. **Opportunity continuity is the highest-value architectural change.** Counts and candidate identity belong in one read. Moving candidate next to Survival produced more operational value than any color, typeface, or card polish.

2. **Card count and vertical height are different problems.** B reduced the phone path to one border before candidate, yet its family padding made the complete Opportunity path taller than A. A family wrapper must earn its space.

3. **Desktop width should buy comparison, not decoration.** At `1280x800`, only C exposed GEX and Movement while keeping state and candidate minimums visible. A wider single column is an improvement, but not a mature desktop architecture.

4. **Provenance can stay complete and become quiet.** Separating current value, per-carrier clock, delay, and qualifier by type role made long GEX truth easier to read without hiding it or inventing a global `as of`.

5. **Exception states need a dedicated warning lane plus unchanged board structure.** HALT, carrier loss, and event-present modes remained legible because the warning pierced the hierarchy while the same State/Opportunity/Context model stayed in place. No alternate product mode was needed.

## What to steal

### From B — Zoned Cockpit

- one outer family boundary with internal hairlines
- numbered family labels for the lower board
- conditional Red Folder detail placed inside/under State
- the five-zone mental model for a two-minute read
- visibly subordinate Context/Structure/History surfaces

### From A — Evolutionary

- conservative surface names and familiar reading order
- value/provenance type roles that can land without a board rewrite
- 2x2 phone Opportunity metrics as an accessibility fallback
- limited, independently reversible CSS changes
- a migration path that can stop after any slice

## Recommended small-slice migration sequence

These are planning shapes only. They are not PRDs, and this lab does not authorize implementation.

### Slice 1 — Add presentation roles without moving anything

- Add value / provenance / qualifier hooks to MARKET STATE.
- Preserve exact text, punctuation, axis count, source order, colors, and visibility.
- Apply the same typographic roles to existing GEX and Movement provenance where a safe hook already exists.
- Validate exact visible text and independent clocks.

**Reversibility:** remove the hooks and scoped CSS.

**Governance flags:** `market_state_panel.py` and `dashboard_renderer.py` are high-risk production files even when the intended hunk is cosmetic. The existing cosmetic carve-out may apply only while no value, class, visibility, derivation, or global selector changes. Any semantic color change is explicitly outside this slice.

### Slice 2 — Reduce first-board card chrome

- Tighten scoped spacing for MARKET STATE, SYSTEM STATE, and Opportunity Survival.
- Keep their current order and every critical string.
- Use lighter borders and smaller gaps only on those surfaces.
- Prove 360/390/430 behavior with exact text and overflow measurements.

**Reversibility:** one scoped CSS block.

**Governance flags:** high-risk dashboard renderer file; no truth-semantic, carrier, or ordering change is intended. Stop if implementation requires a global `.block` rewrite.

### Slice 3 — Restore Opportunity continuity

- Move MARKET MAP / DEVELOPING SETUPS immediately after Opportunity Survival.
- Keep candidate identity, grade/state, level, and invalidation open.
- Put reason/watch and the existing level diagram behind full-width, 44px disclosures.
- Preserve System-to-candidate authority and all no-candidate behavior.

**Reversibility:** restore the prior emission order and disclosure wrappers.

**Governance flags:** this crosses an existing ordering contract and a protected renderer interval. It touches a high-risk file and requires explicit ordering-test review. Reassess lane/materiality; do not assume the cosmetic carve-out. If any candidate gate or visibility rule changes, dashboard truth semantics are crossed.

### Slice 4 — Introduce lower-board family wrappers

- Add presentation-only families for Context, Structure/Session, and History/Detail.
- Replace per-surface full boxes with one family edge plus internal separators.
- Keep one continuous DOM/source order.
- Keep healthy-empty Red Folder suppressed; put populated/unavailable detail in the State bridge.

**Reversibility:** remove family wrappers/classes and restore current surface chrome.

**Governance flags:** broad renderer CSS/markup cone in a high-risk file. A visibility gate, empty-state change, or source movement would cross dashboard truth semantics. Event-detail placement also touches ordering contracts.

### Slice 5 — Activate desktop comparison at 960px+

- Pair MARKET STATE / SYSTEM STATE.
- Pair Opportunity Survival / Candidate.
- Pair GEX / Market Movement.
- Pair Changes / Scoreboard.
- Keep Macro and Trend full width.
- Keep `768px` and below one column.

**Reversibility:** remove the desktop media query; source order remains valid.

**Governance flags:** high-risk renderer file and conditional-grid testing. No carrier combination is allowed: adjacent surfaces retain their own clocks and authority. A shared/global timestamp would cross a carrier boundary and dashboard truth semantics.

### Slice 6 — Finish safe disclosure and lower-zone density

- Keep Macro bias/tally/availability visible; disclose driver and tradable-price detail.
- Preserve every Trend row and explicit unavailable value.
- Make Scoreboard and diagnostics deliberate full-width disclosures.
- Give conditional Session Observation and Market Control cadence labels within Structure/Session.

**Reversibility:** restore expanded presentation without changing values.

**Governance flags:** session/control are independent conditional carriers. Moving, merging, or changing their presence gates crosses carrier and ordering boundaries. Any change to persisted payload, source health, schema, or multi-reader truth may trigger GOV-2 MATERIAL review; this recommendation does not adjudicate it.

## Explicit RED seams for future work

Stop and govern separately if any slice requires:

- recoloring `OBSERVE ONLY`, EXPANSION, permission, HALT, or availability
- merging MARKET STATE and SYSTEM STATE into one verdict
- introducing a synthetic score or bullish/bearish conclusion
- changing a value, label, derivation, source-health classification, gate, or precedence rule
- replacing independent clocks with one timestamp
- changing carrier/schema/payload contracts
- changing Red Folder availability or empty-state semantics
- changing candidate qualification, authorization, or trade-decision logic
- expanding beyond a consumer/presentation layer
- touching a GOV-2 MATERIAL trigger

Those are not visual cleanups. This lab deliberately leaves them unresolved.

## Major risks

1. **Static fixtures cannot prove production-state completeness.** They prove visual resilience for five representative modes, not every carrier combination.

2. **C's phone metric row is intentionally dense.** It passed 360px without overflow, but production fonts, localization, zoom, and larger accessibility text may require A/B's 2x2 fallback.

3. **Candidate reordering is contract work.** Even with unchanged values, moving the candidate crosses deliberate renderer ordering and test seams.

4. **Semantic color remains unresolved.** Neutral prototype treatment avoids reinforcing the current EXPANSION / OBSERVE ONLY ambiguity, but it is not a new production contract.

5. **Conditional State detail can push Opportunity down.** In event-present mode that is correct priority, but multiple simultaneous warnings need explicit production fixtures.

6. **Desktop pairing can tempt fake synthesis.** Adjacency must never collapse Market/System authority or carrier clocks into one visual verdict.

7. **Progressive disclosure needs non-visual validation.** Keyboard behavior, screen-reader naming, print/export behavior, and persisted open state were not production-tested.

8. **High-risk renderer concentration remains.** Most future slices likely touch `dashboard_renderer.py`; small commits and exact-scope tests are essential.

9. **Active implementation work was not inspected.** This lab is pinned to the supplied main and audit SHAs and must be reconciled with later main before any future planning.

## Patterns to retire

- universal equal-weight cards
- the 640px desktop ceiling
- Context between Survival and Candidate
- equal typography for value and provenance
- repeated card-within-card phone chrome
- history presented like live state
- tiny disclosure links
- phone layout reused unchanged on desktop
- color doing semantic work without text

## Contracts to preserve

- State first; trades second.
- Observe wide; trade narrow.
- Context may inform; context may never authorize.
- MARKET STATE and SYSTEM STATE remain distinct.
- Critical state and unavailability remain open.
- Candidate identity, level, and invalidation remain open.
- GEX delay and positioning-assumption qualifiers remain visible.
- Provenance clocks remain independent.
- No predictive hero, global score, fake certainty, or Amon Hen trading semantics.
- Phone remains one continuous board.

## Isolation confirmation

The implementation surface for this lab is only `experiments/cuttingboard-visual-system-v0/`. No production dashboard source, runtime, schema, carrier, producer, ingestion, notification, workflow, or decision file is part of the experiment.
