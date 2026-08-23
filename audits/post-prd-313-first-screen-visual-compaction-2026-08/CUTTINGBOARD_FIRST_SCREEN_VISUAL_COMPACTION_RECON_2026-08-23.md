# CUTTINGBOARD FIRST-SCREEN VISUAL COMPACTION RECON

## 1. EXACT BASELINE

- Expected `origin/main`: `8bf3b58a98120c43860a689756d84950a0b3aadb`
- Verified `origin/main`: `8bf3b58a98120c43860a689756d84950a0b3aadb`
- Main drift: **NONE**
- Merge: PR #274, `Merge PR #274: PRD-313 empty red-folder display suppression`
- Current checkout: `74560ee73d395181753476423108a8bfa2308653`, the merge’s implementation parent.
- Checkout tree and `origin/main` tree are byte-identical: `c2e144a5c0f57aaa171006e3df976c140f07fcc2`
- Authoritative audit commit verified: `c2299f9f7358ccbea2109b79a616717f34a97024`
- Authoritative audit: [CUTTINGBOARD_POST_312_VISUAL_HIERARCHY_AUDIT_2026-08-23.md](https://github.com/dwats250/cuttingboard/blob/docs/post-312-visual-hierarchy-audit/audits/post-312-visual-hierarchy-2026-08/CUTTINGBOARD_POST_312_VISUAL_HIERARCHY_AUDIT_2026-08-23.md)

Current publication truth:

- `origin/publish`: `77e9fc8b0780133994058f5a8fb82daf60ed1a3d`
- Public artifact: [Cuttingboard production board](https://dwats250.github.io/cuttingboard/)
- Live/public SHA-256: `c5f451cc98f6b0360f41ec661e2af533236b3aa9ce5977bb6fa29ca9f65a289f`
- That hash still matches `ui/index.html` and `ui/dashboard.html` at `origin/publish`.
- Therefore, main contains PRD-313, but the public artifact has not advanced past the supplied PRD-312 publish SHA. This does not invalidate the first-screen measurements: the PRD-313 renderer diff changes only the later Red Folder emission and leaves `_CSS`, MARKET STATE, SYSTEM STATE, and OPPORTUNITY SURVIVAL unchanged.

Rendered artifact inspected in Chrome at:

- 360×800
- 390×844
- 430×932
- 768×1024
- 1280×800

Current source seams:

- Main renderer: [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2044)
- Embedded CSS: [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:762)
- MARKET STATE module: [market_state_panel.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/market_state_panel.py:99)
- MARKET STATE insertion: [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2340)
- SYSTEM STATE insertion: [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2363)
- OPPORTUNITY SURVIVAL insertion: [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2522)
- Publish writer: [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:3242)
- Hourly generation of `ui/dashboard.html` and copy to `ui/index.html`: [hourly_alert.yml](/home/dustin/Projects/cuttingboard/.github/workflows/hourly_alert.yml:152)
- Pages deploys `ui/` from `publish`: [pages.yml](/home/dustin/Projects/cuttingboard/.github/workflows/pages.yml:30)

The required graph service returned “No indexed repositories” for queries, symbol context, and both requested upstream impact checks. Rebuilding the index would have modified repository-local analysis files during a read-only pass, so the blast-radius findings below use exact-commit source, call-site, workflow, test, and rendered-DOM evidence.

## 2. CURRENT FIRST-SCREEN MECHANICS

| Surface | Current carrier/rendering seam | Current presentation |
|---|---|---|
| Freshness | Empty `#staleness-banner` emitted at lines 2327–2338; client script reads `#cb-updated` | Separate full `.block`; hidden when fresh, 49px high in the inspected stale state |
| MARKET STATE | `market_state_panel.render_fragment()` receives resolved GEX/Movement cards, run clock, regime, permission, and Red Folder view | `.block` → `h2` → two-column `.kv-grid`; every main value, provenance fact, and qualifier shares one `.value` |
| SYSTEM STATE | Emitted inline at lines 2363–2520 | Existing distinct hooks for decision, verdict, reason, context, halt, separator, and updated timestamp |
| OPPORTUNITY SURVIVAL | Emitted inline at lines 2522–2611 | Generic two-column `.kv-grid`; four metrics plus optional PRIMARY REJECTION form five vertical rows |
| Whole page | `_CSS` is injected into every render at line 2262 | Body padding 16px; `.wrap` capped at 640px; each `.block` has 16px padding, 16px bottom gap, border, and radius |

Current selectors affecting the target surfaces:

- Shared: `body`, `.wrap`, `.block`, `h2`, `.kv-grid`, `.label`, `.value`, `.sep`
- SYSTEM STATE: `.decision-state-label`, `.decision-state`, `.decision-state.sys-*`, `.sys-verdict`, `.sys-verdict.sys-*`, `.sys-why`, `.sys-context`, `.sys-context.halted`, `.halted`
- Freshness: inline styles on `#staleness-banner`; script-applied color/border state
- MARKET STATE: no dedicated child selectors
- OPPORTUNITY SURVIVAL: no dedicated selectors

Current responsive behavior:

- The only media breakpoint is `@media(max-width:640px)` at [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:899).
- It affects only Trend Structure.
- MARKET STATE, SYSTEM STATE, and OPPORTUNITY SURVIVAL have no phone-specific layout.
- At 390px, the outer card is 358px wide; after 16px card padding, approximately 326px remains. MARKET STATE’s label column consumes about 102px, leaving about 210px for its values.

Current measured geometry:

| Width | MARKET STATE | SYSTEM STATE | OPPORTUNITY | First zone | Next surface exposed |
|---:|---:|---:|---:|---:|---:|
| 360 | 344px | 205px | 164px | 810px | GEX begins 42px below fold |
| 390 | 314px | 205px | 164px | 780px | 32px of GEX |
| 430 | 284px | 205px | 164px | 750px | 150px of GEX |
| 768 | 209px | 187px | 164px | 657px | 335px of GEX |
| 1280 | 209px | 187px | 164px | 657px | 111px of GEX |

“First zone” is measured from the top of the visible stale banner to the bottom of OPPORTUNITY SURVIVAL.

## 3. PROPOSED PRESENTATION MECHANISM

The hypothesis is realizable as a pure presentation change.

### MARKET STATE

Add source-level inline hooks inside each existing outer `.value`:

- `.market-state-main`
- `.market-state-provenance`
- `.market-state-qualifier`

The safest implementation shape is a small presentation formatter used by the existing axis helpers. It should return the same string content with inline spans around already-separated components. It must not parse completed HTML or derive presentation parts in client-side JavaScript.

Examples of the structural split:

- ENVIRONMENT: main value + own run provenance
- PERMISSION: complete permission sentence as main value + own run provenance
- POSITIONING: net as main value + GEX clock/delay as provenance + configured-assumption statement as qualifier
- PARTICIPATION: capture count as main value + captured time as provenance
- EVENT RISK: event count/state as main value + calendar provenance

For `unavailable`, only the main hook renders. It must not inherit the smaller provenance treatment.

The outer `.label`, `.value`, `.kv-grid`, block ID, axis order, visible punctuation, spaces around the middot, escaping behavior, and exact per-cell text remain unchanged.

### Phone-scoped layout

Add a new, independent `@media(max-width:430px)` block. Do not broaden the existing 640px Trend breakpoint.

The tested candidate uses:

- 12px padding on only `#market-state`, `#system-state`, and `#opportunity-survival`
- 10px bottom margin on only those blocks
- 8px heading bottom margin inside only those blocks
- 8px MARKET STATE column gap
- `font-weight:600` for `.market-state-main`
- `font-size:.72rem; line-height:1.25` for provenance and qualifier
- No new `color` or `opacity` property
- No change to body padding
- No change to the stale banner
- No change to decision/verdict font sizes or semantic classes

This keeps provenance at the existing text color while distinguishing it through type scale and weight only.

### OPPORTUNITY SURVIVAL

At `max-width:430px`, change only `#opportunity-survival .kv-grid` to:

- `max-content minmax(0,1fr) max-content minmax(0,1fr)`

The existing DOM sequence then naturally renders:

- SURFACED | SETUPS FOUND/QUALIFIED
- WATCHLIST | REJECTED
- PRIMARY REJECTION across the full row below

No metric wrapper or metric reordering is required. The ninth and tenth children—the optional PRIMARY REJECTION label/value—can be given grid-column placement through ID-scoped child selectors. When the rejection row is absent, those selectors match nothing.

This preserves DOM and screen-reader order:

1. SURFACED label/value
2. SETUPS FOUND or QUALIFIED label/value
3. WATCHLIST label/value
4. REJECTED label/value
5. PRIMARY REJECTION label/value, when present

### SYSTEM STATE

SYSTEM STATE already has sufficient presentation hooks. It needs no markup split.

Only its phone card padding, inter-card gap, and heading margin change. The following remain untouched:

- `.decision-state`
- `.sys-verdict`
- `.sys-why`
- `.sys-context`
- `.halted`
- `#cb-updated`
- all `sys-*` classes
- all colors
- all text and state derivation

No production JavaScript, new calculation, carrier, schema, or disclosure is required.

## 4. EXACT FILE CONE

### Likely editable production files

| File | Required reason |
|---|---|
| [market_state_panel.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/market_state_panel.py:99) | Add inline main/provenance/qualifier presentation hooks while preserving all five existing values |
| [dashboard_renderer.py](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:762) | Add the ID-scoped `max-width:430px` CSS for the three target surfaces |

### Likely editable test files

| File | Required reason |
|---|---|
| [test_market_state_panel.py](/home/dustin/Projects/cuttingboard/tests/test_market_state_panel.py:41) | Its `_value()` helper and several assertions assume a text-only `.value`; add hook and exact-visible-text coverage |
| [test_dashboard_renderer.py](/home/dustin/Projects/cuttingboard/tests/test_dashboard_renderer.py:3917) | Pin scoped CSS, MARKET STATE-before-SYSTEM STATE, target IDs, and unchanged text/order |
| [test_dash_system_state.py](/home/dustin/Projects/cuttingboard/tests/test_dash_system_state.py:487) | Pin the direct-child metric order on which the CSS-only 2×2 grid relies and retain locked/unlocked labels |
| [dashboard_pre_gex_golden.html](/home/dustin/Projects/cuttingboard/tests/data/dashboard_pre_gex_golden.html:1) | Exact-byte golden includes both `_CSS` and MARKET STATE markup; it must be intentionally refreshed |

### Regression-only; likely no edit

- [test_staleness_banner.py](/home/dustin/Projects/cuttingboard/tests/test_staleness_banner.py:92)
- [test_dash_core.py](/home/dustin/Projects/cuttingboard/tests/test_dash_core.py:138)

`tests/test_staleness_banner.py` remains important to run, but no banner markup or behavior needs to change.

### Explicitly excluded as editable sources

- `ui/dashboard.html`
- `ui/index.html`

They are tracked generated publication outputs. The hourly workflow renders `ui/dashboard.html`, copies it to `ui/index.html`, stages both, and publishes them from the `publish` branch. They are not hand-edited source inputs for this slice.

Also excluded:

- `tests/preview_fixtures.py`
- `tests/test_preview_fixtures.py`
- workflows
- runtime
- ingestion
- payload/schema modules
- notifications/reports

## 5. CLASS / LANE / MATERIALITY

| Axis | Assessment | Basis |
|---|---|---|
| CLASS | `CONSUMER` | A read-only dashboard presentation over finalized artifacts; [PRD_PROCESS class definition](/home/dustin/Projects/cuttingboard/docs/PRD_PROCESS.md:410) |
| Default tier | T2 | CONSUMER matrix row |
| LANE | `MICRO`, if and only if every production hunk remains cosmetic | The [Cosmetic Carve-Out](/home/dustin/Projects/cuttingboard/docs/PRD_PROCESS.md:601) expressly includes CSS and layout/markup structure and disables the dashboard renderer’s normal high-risk-file trigger |
| MATERIAL | `NO` | No GOV-2 §1 trigger fires |

`dashboard_renderer.py` is ordinarily a CONSUMER high-risk file. That normally forces `LANE: HIGH-RISK`, as PRD-313 did. This slice is different because it changes only CSS/markup structure and none of the R12 dashboard-truth surfaces.

The cosmetic classification fails immediately if implementation changes any:

- value or label
- permission/halt derivation
- visibility gate
- state precedence
- source-health or lineage classification
- event or Opportunity count calculation
- semantic color class
- carrier or schema
- generated-output workflow

If any such hunk appears, the carve-out no longer applies and the entire slice must be reclassified. With `dashboard_renderer.py` as payload, that would make the lane HIGH-RISK.

MATERIAL is `NO` because:

- This recon does not certify a global all-consumer inventory.
- Neither proposed seam is shared across pipeline layers.
- No existing governed FILES/LOC ceiling is being expanded.
- No contract, audit, report, payload, persisted schema, or multi-reader data surface changes.
- No governance guardrail changes.
- No Critical/High correctness finding is being resolved.
- Two delivery-layer modules and three DOM blocks remain one dashboard layer, not a GOV-2 cross-layer change.

The embedded `_CSS` is shared by the whole HTML document, but the proposed selectors are constrained by the three existing IDs and `max-width:430px`; no new shared presentation abstraction is introduced.

The cosmetic rule permits at most one polish PRD per week. Current main shows no other cosmetic MICRO PRD since August 17, so this slice can occupy that slot if the authoring session reconfirms the weekly history.

The separately reported registry gaps must be reconciled before a new PRD is saved. That bookkeeping is a prerequisite, not part of this visual slice and must not be bundled into its implementation FILES.

## 6. REALIZABILITY TRACE

| Required information | Current path | Proposed effect | Preservation proof |
|---|---|---|---|
| ENVIRONMENT | `payload.summary.market_regime` + run clock → `_environment()` | Inline main/provenance spans | Same text; same first axis |
| PERMISSION | `run.permission`, falling back to payload permission → `_permission()` | Permission remains main; clock becomes provenance span | Permission is never muted or hidden |
| POSITIONING | Resolved `GexCard` → `_positioning()` | Net / clock-delay / qualifier receive separate hooks | Net, GEX clock, Cboe delay, and assumption qualifier remain visible |
| PARTICIPATION | Resolved `MovementCard` → `_participation()` | Capture count / captured time receive separate hooks | Partial and unavailable states unchanged |
| EVENT RISK | Resolved Red Folder dict → `_event_risk()` | Event state / calendar provenance receive separate hooks | Error/absence still renders `unavailable` as main |
| SYSTEM decision | Existing `title`, halt, outcome, and operator-lock path | No markup or state change | Decision, verdict, why, halt, lock, context, and updated timestamp remain open |
| Opportunity counts | Existing coherent payload calculation | CSS grid only | Four values and rejection semantics unchanged |
| Freshness | Client reads `#cb-updated` | No change | Banner remains above MARKET STATE and visible when stale |
| DOM order | Existing source order | No `order`, absolute positioning, or `display:contents` | Visual row order matches source and screen-reader order |
| Interaction | No target controls exist | No controls added | No tap or hover dependency |

A temporary browser-only DOM/CSS simulation confirmed, at all five widths:

- exact normalized target-block text equality before/after
- all five MARKET STATE values present
- all provenance and positioning qualifier spans visible
- inherited text color unchanged at `rgb(224, 224, 224)`
- no clipping
- no horizontal overflow
- 768px and 1280px geometry unchanged

## 7. PHONE / TABLET / DESKTOP ACCEPTANCE MATRIX

Use a fixed long-content fixture equivalent to the inspected production state:

- visible stale banner
- operator lock
- long permission string
- full positioning provenance and qualifier
- 12/12 participation
- event state
- all four Opportunity counts
- PRIMARY REJECTION present

| Viewport | Current baseline | Tested presentation result | Minimum acceptance |
|---|---|---|---|
| 360×800 | First zone 810px; Opportunity ends 26px below fold; GEX starts 42px below fold | First zone ≈680px; 94px of GEX exposed | First zone ≤720px; Opportunity fully above fold; ≥50px of GEX exposed |
| 390×844 | First zone 780px; 32px of GEX exposed | First zone ≈665px; 153px of GEX exposed | First zone ≤680px; ≥140px of GEX exposed; improvement ≥100px |
| 430×932 | First zone 750px; 150px of GEX exposed | First zone ≈634px; 272px of GEX exposed | First zone ≤660px; ≥240px of GEX exposed |
| 768×1024 | First zone 657px; 335px of GEX exposed | 657px; 335px exposed | Target block top/height values unchanged within 1 CSS px |
| 1280×800 | First zone 657px; 111px of GEX exposed | 657px; 111px exposed | Target block top/height values unchanged within 1 CSS px |

Required checks at every width:

- `documentElement.scrollWidth == documentElement.clientWidth`
- No target value has `scrollWidth > clientWidth` or `scrollHeight > clientHeight`
- Every MARKET STATE `.value` has nonzero visible bounds
- All provenance and qualifier hooks have `display != none`, `visibility != hidden`, and nonzero bounds
- Exact per-axis visible text equals the pre-change value
- MARKET STATE precedes SYSTEM STATE
- SYSTEM STATE precedes OPPORTUNITY SURVIVAL
- Stale, unavailable, halt, operator lock, and permission remain visible without interaction
- No existing semantic class changes
- No color or opacity changes
- Opportunity source order remains label/value pairs in the existing sequence
- PRIMARY REJECTION remains a full row beneath the four metrics

A literal “no wrapping” rule is not realizable at 360px while preserving current strings, font scale, and board width: the current operator-lock verdict and long permission already wrap. The objective criterion should therefore be:

- no clipping
- no word-breaking
- no increase in critical line count
- `OBSERVE ONLY`, `HALT`, and `STATE UNAVAILABLE` remain individually unmistakable
- long lock/permission strings wrap at the same or fewer lines than baseline

Add a 431px boundary probe: the new phone rules must be inactive immediately above the breakpoint.

## 8. TEST + VISUAL VALIDATION CONE

Current baseline evidence:

- Four relevant files: **471 passed**
- Full suite at exact main tree: **3951 passed, 1 xfailed**
- Repository returned clean after validation

The full suite rewrote two tracked log fixtures during execution:

- `logs/latest_hourly_market_map.json`
- `logs/trend_structure_snapshot.json`

They were clean immediately before the suite and were restored exactly to `HEAD`; the repository is clean now. Future full-suite validation should run in a disposable worktree or explicitly snapshot and verify those two paths afterward.

Required implementation tests:

1. MARKET STATE hook test:

   - exactly five `.label` and five outer `.value` cells
   - one main hook per axis
   - correct provenance-hook presence for available axes
   - qualifier hook only where required
   - unavailable remains a main value
   - exact visible cell text, punctuation, and order preserved
   - no INTRADAY, score, verdict, or global as-of

2. MARKET STATE integration:

   - `#market-state` before `#system-state`
   - no hook or CSS change moves it into the protected System-to-candidate region

3. Opportunity structure:

   - direct children remain SURFACED/value, SETUPS FOUND or QUALIFIED/value, WATCHLIST/value, REJECTED/value, then optional PRIMARY REJECTION/value
   - locked and unlocked labels remain correct
   - primary-absent state still has eight children and no empty row
   - long primary rejection text remains visible

4. CSS scope:

   - new breakpoint is exactly `max-width:430px`
   - every new layout selector is rooted in `#market-state`, `#system-state`, or `#opportunity-survival`
   - no global `.block`, `.label`, `.value`, `.kv-grid`, `h2`, body, or `.wrap` change
   - no color, opacity, display suppression, or semantic class rule added

5. Golden fixture:

   - deliberately refresh `tests/data/dashboard_pre_gex_golden.html`
   - inspect its diff; it should contain only the intended CSS and MARKET STATE span markup
   - preserve the exact-GEX-absence golden assertion rather than weakening it

6. Existing regression tests:

   - `tests/test_market_state_panel.py`
   - `tests/test_dashboard_renderer.py`
   - `tests/test_dash_system_state.py`
   - `tests/test_staleness_banner.py`
   - `tests/test_dash_core.py`
   - full suite once before review

Visual validation:

- Capture fixed-fixture screenshots at 360×800, 390×844, 430×932, 768×1024, and 1280×800.
- Collect DOM rectangle measurements, not only screenshots.
- Compare target-block `textContent` before/after.
- Exercise at least operator-lock, HALT, STATE UNAVAILABLE, and carrier-unavailable fixtures.
- Do not treat “looks better” as pass evidence.

## 9. RISKS

1. **Exact-text test breakage:** MARKET STATE tests currently assume text begins immediately inside `.value`. Nested spans will break `.startswith()` and one exact raw-HTML assertion unless tests are updated to inspect visible text and hooks separately.

2. **Golden fixture churn:** `dashboard_pre_gex_golden.html` pins the whole rendered document byte-for-byte. Both new CSS and MARKET STATE spans will intentionally change it.

3. **Escaping or punctuation drift:** Refactoring the axis helpers could accidentally alter HTML escaping, spaces around `&middot;`, the asterisk, or the configured-assumption wording. The presentation helper must operate on the same already-formatted components and exact text must be pinned.

4. **CSS leakage:** Editing generic `.block`, `.label`, `.value`, `.kv-grid`, or `h2` would affect lower-page cards. All new rules must be rooted in the three target IDs.

5. **Breakpoint leakage:** Adding the rules to the existing `max-width:640px` block would change tablet behavior. Use a separate inclusive 430px breakpoint and test 431px.

6. **Provenance becoming too quiet:** Do not change color or opacity. Keep provenance visible, in source order, at no smaller than the tested `.72rem` role, using `rem` so browser zoom remains effective.

7. **Opportunity child-selector fragility:** The CSS-only grid depends on the existing direct-child order. Pin that order and both primary-present and primary-absent cases in the Opportunity-owned tests.

8. **Critical wrapping:** Long permission and lock text already wraps at phone widths. Compaction must not chase height by shrinking critical decision text or allowing clipping.

9. **Generated-artifact assumptions:** `ui/index.html` and `ui/dashboard.html` are tracked but generated. Editing them on the feature branch would duplicate workflow output and widen the file cone incorrectly.

10. **Validation worktree dirt:** The full suite currently rewrites two tracked logs. Run it in an isolated worktree or prove and restore only those exact paths.

11. **Graph-evidence gap:** Automated graph impact was unavailable in this session. The exact static trace shows one production MARKET STATE caller and one dashboard publish writer, but implementation review should rerun the graph checks if the index is restored.

## 10. CUT LIST

Do not include:

- Red Folder changes beyond already-merged PRD-313
- Candidate movement or reordering
- MARKET MAP changes
- GEX, Movement, Macro Tape, or Trend Structure changes
- Global STATE / OPPORTUNITY / CONTEXT wrappers
- Generic card-system or typography refactoring
- Desktop widening or multi-column layout
- Tablet layout changes
- Color or semantic color-contract changes
- `OBSERVE ONLY` recoloring
- New disclosures, tabs, modes, or tap targets
- New calculations, carriers, schemas, or source fields
- Runtime, ingestion, notification, report, or workflow changes
- Manual edits to generated `ui/*.html`
- Registry-gap hook repair in the visual implementation
- NEWS work
- Amon Hen-inspired semantics or navigation

## 11. RECOMMENDATION

**PROCEED AS ONE BOUNDED PRD**

The slice is small enough to remain one coherent visual change:

1. Add inline main/provenance/qualifier hooks to MARKET STATE without altering text.
2. Add an ID-scoped `max-width:430px` rule for the three target cards.
3. Tighten only their phone padding, inter-card gaps, and heading spacing.
4. Use type size/weight—not color—to separate MARKET STATE main values from metadata.
5. Render Opportunity’s existing four metric pairs as a phone-only 2×2 CSS grid with PRIMARY REJECTION beneath.
6. Leave SYSTEM STATE markup, critical typography, color classes, and decision logic unchanged.
7. Preserve tablet and desktop geometry.
8. Refresh only the load-bearing golden fixture and targeted tests.

Stop and reclassify if implementation requires any value derivation, condition, semantic class, global selector, new carrier, or file outside the identified cone.

## 12. PRD AUTHORING HANDOFF

Authority:

- Main: `8bf3b58a98120c43860a689756d84950a0b3aadb`
- Visual audit: `c2299f9f7358ccbea2109b79a616717f34a97024`
- Public measurement artifact: `origin/publish@77e9fc8b0780133994058f5a8fb82daf60ed1a3d`
- Public artifact hash: `c5f451cc98f6b0360f41ec661e2af533236b3aa9ce5977bb6fa29ca9f65a289f`

Classification:

- `CLASS: CONSUMER`
- `LANE: MICRO — Cosmetic Carve-Out`
- `MATERIAL: NO`
- No MATERIAL packet
- Use the cosmetic MICRO note form if all boundaries remain true
- Reconcile the separately reported registry gaps before saving the PRD; do not place that work in the visual FILES cone

Exact production FILES:

- `M cuttingboard/delivery/market_state_panel.py`
- `M cuttingboard/delivery/dashboard_renderer.py`

Exact likely test FILES:

- `M tests/test_market_state_panel.py`
- `M tests/test_dashboard_renderer.py`
- `M tests/test_dash_system_state.py`
- `M tests/data/dashboard_pre_gex_golden.html`

Run but likely do not modify:

- `tests/test_staleness_banner.py`
- `tests/test_dash_core.py`

Do not list:

- `ui/dashboard.html`
- `ui/index.html`
- workflows
- runtime/ingestion/schema/carrier files
- preview fixture catalog files

Binding behavior:

- MARKET STATE retains exactly five axes and existing order.
- Each axis retains exact visible value, punctuation, provenance, and qualifier.
- MARKET STATE remains before SYSTEM STATE.
- SYSTEM STATE retains decision, halt, lock, why, context, timestamp, and all current classes.
- OPPORTUNITY SURVIVAL retains all four counts, locked/unlocked label behavior, optional PRIMARY REJECTION, and DOM order.
- No color, opacity, semantic styling, source, carrier, calculation, gate, or visibility change.
- New responsive rules apply only at `max-width:430px`.
- Tablet and desktop target geometry remains within 1 CSS px of baseline.
- At 390×844, first-zone height is no more than 680px and at least 140px of GEX is exposed.
- No horizontal overflow or clipped target text at any required width.
- Exact target-cell visible text is equal before and after.
- No interaction is required for freshness, permission, halt, lock, event risk, provenance, or unavailability.

Validation baseline:

- Targeted current baseline: `471 passed`
- Full current baseline: `3951 passed, 1 xfailed`
- Visual baseline and simulated acceptance measurements are recorded in Section 7.

NEXT: Compact MARKET STATE, SYSTEM STATE, and OPPORTUNITY SURVIVAL at 360–430px using source-level MARKET STATE main/provenance/qualifier spans, ID-scoped phone spacing/type rules, and a CSS-only 2×2 Opportunity metric grid, with exact text, DOM order, colors, carriers, tablet/desktop behavior, and trading semantics unchanged.
