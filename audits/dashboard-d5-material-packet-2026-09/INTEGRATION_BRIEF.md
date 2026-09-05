# Cuttingboard visual integration brief (frozen design) - D5: A-upper + C-watching

Authored by Fable 5.1 in DESIGN mode, 2026-09-04. Basis: owner visual decision
(hybrid: Direction A upper surface + Direction C WATCHING), audition at
/tmp/cuttingboard-visual-audition/ (AUDITION.md, gallery.html, evidence/),
origin/main 45910ffda55ecab940b07504a0283c317801af23. PR #319 (head 4926388)
salvaged for engineering only. No implementation, no PR, no merge.

Evidence consulted directly: comparison-top.png, comparison-watching.png,
evidence/A-populated-1280-top.png, evidence/C-populated-1280-watching.png,
evidence/C-populated-390-candidate-secondary.png; origin/main
cuttingboard/delivery/dashboard_renderer.py (_CSS 937-1217, WATCHING emission
3163-3436, _render_candidate_card 2248+, _render_spy_session 2512+,
_render_setup_chart_block 2232+); prototypes/C/populated.html (selector markup);
PR #319 diff via gh; test oracle inventory (below).

## 1. FINAL DESIGN THESIS

Cuttingboard stays one terminal-ancestry mono tool. Above the WATCHING seam the
page is an interpretation surface that already works and already carries most
of Direction A (PRD-318 answer-first zones, PRD-322 aligned TAPE grids, PRD-330
SPY SESSION with a native LEVELS toggle); it receives only restrained,
CSS-appended refinement: state-keyed accent rails, a wider desktop column,
chart-beside-readout at desktop, tabular numerals, 44px disclosure targets. At
and below the seam WATCHING becomes Direction C's operator workspace: the
ALERT WATCHLIST (MANUAL CHECK) band moves above the setups, and the high-grade
setups become a selectable workspace driven by a native radio-group tab strip
(the same hidden-input + `:checked ~` mechanism PRD-330 already ships), default
selection = the canonical primary symbol, fail-open to the stacked list if the
selector CSS is ever absent. Selection is presentation only: grades, ordering,
tiers, MANUAL_CHECK, verdict, primary-symbol and chart-slot semantics are
untouched and stay upstream. The two regions read as one product because they
share the single font stack, the single palette, the 3px rail grammar, the
hairline separators, and the h2/h3 caps that already exist in _CSS.

## 2. UPPER SURFACE - A (preserve / adopt)

Boundary: everything emitted BEFORE `<div class="block operator-zone"
id="watching-zone">` (that exact string is `_SEAM` in
tests/test_dashboard_d2_seam.py, so the design boundary and the test boundary
coincide): #verdict-zone/#system-state, #tape-zone, #spy-session, #today-zone.

Preserve byte-identically (markup): every element and its order in
#system-state, #tape-zone, #spy-session, #today-zone (d2_seam R1/R2/R5/R8 pin
these). All changes here are CSS appended to the TAIL of `_CSS` in new rule
blocks; no existing rule string is edited (keeps the pinned CSS substrings in
test_dashboard_d2_seam.py::test_css_edits_confined_to_the_non_phone_region and
test_dash_manual_check_flag.py::test_manual_check_css_outside_protected_phone_block
intact). Phone (<=430px) bytes for existing rules stay identical; new phone
rules go in a NEW `@media(max-width:430px)` block appended after PRD-330's.

Adopt (CSS only):
- A1 Verdict accent rail. `#verdict-zone{border-left:3px solid #3a3a3a}` plus
  state-keyed color via `:has()` (already in baseline):
  `#verdict-zone:has(.decision-state.sys-up){border-left-color:#4caf50}`,
  `.sys-down`/`.sys-halt` -> #f44336, `.sys-flat` -> #ff9800. Reuses the
  existing decision-state classes; no new state. STAY FLAT already renders
  amber via `.decision-state.sys-flat` - the audition's amber note needs no
  change and no color semantics move.
- A2 NEXT EVENT rail. `#today-zone{border-left:3px solid #ff9800}`;
  `#today-zone h2{color:#ff9800}`. Label amber, body text unchanged.
- A3 Desktop column. `@media(min-width:961px){.wrap{max-width:760px}}` (A
  renders at ~760px at 1280; current 640). Nothing else reflows.
- A4 TAPE desktop density. `@media(min-width:641px){.tape-drivers{grid-template-columns:repeat(auto-fit,minmax(9ch,1fr))}}`
  so seven drivers sit on one line at desktop (A-1280 render); phone keeps the
  PRD-322 4-column grid untouched.
- A5 SPY SESSION desktop composition. `@media(min-width:641px)`: the nearest
  common parent of `.spy-chart` and `.lvl-ladder` inside #spy-session becomes
  `display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);column-gap:16px;row-gap:0`;
  h3/.spy-read/.spy-clock `grid-column:1/-1`; `.chart-controls{grid-column:2;grid-row:1;justify-self:end}`;
  `.spy-chart{grid-column:1}`; `.lvl-ladder{grid-column:2;align-self:center}`.
  The `#spy-levels:checked~.spy-chart` sibling selector is unaffected (DOM
  order unchanged). Phone stacks exactly as today.
- A6 Numerals. Append `.lvl-ladder,.tape-drivers,.tape-trend,.history-table{font-variant-numeric:tabular-nums}`.
- A7 Metadata weight. `#system-state #cb-updated` and `.spy-clock` stay muted
  (#666/#777) - already so; no change. Section caps h2/h3 unchanged.

Explicitly NOT adopted from A/B/C or #319 above the seam: tonal section
merging (B), any font change, any new hex value, fluid `clamp()` headline size,
the #319 960px two-column page grid, rounded panels, shadows, driver tiles.

## 3. WATCHING - C (workspace interaction and visual behavior)

Region: #watching-zone through its closing tag; #details-history untouched.

Emission order inside #watching-zone (markup change #1):
1. `<h2>WATCHING</h2>` (unchanged)
2. `.screen-line` survival funnel (unchanged)
3. `#alert-watchlist` (MOVED here from after #candidate-board; its inner markup
   byte-identical: h3, label, `.candidate-state[.manual-check]` rows with
   `.manual-check-flag`). Conditional on alert_candidates exactly as today.
4. `#candidate-board` (h3 SETUPS, idle-summary / unavailable / skip lines
   unchanged in position and text), then:
   - If >= 2 cards fall in high-grade tiers (`_HIGH_GRADES`): the setup
     workspace (markup change #2, below).
   - If exactly 1 high-grade card, or 0: today's markup, unchanged (no tab
     strip for a single setup; the idle summaries already cover 0).
   - Low tiers: today's `<details class="tier-group" id="tier-{id}">`
     blocks, unchanged, emitted after the workspace.
   - `.removed-symbols` unchanged.

Setup workspace markup (all ids HTML-escaped symbols; order = existing
`sorted_syms` order = `_GRADE_ORDER` then symbol; tiers iterate `_TIER_DEFS`
exactly as today):

```
<div class="setup-workspace" id="setup-workspace">
  <style>/* n rule-pairs, one per workspace symbol, see below */</style>
  <input type="radio" name="setup-select" id="setup-SPY" class="setup-select" checked>
  <input type="radio" name="setup-select" id="setup-QQQ" class="setup-select">
  <div class="setup-tabs" role="group" aria-label="Setups">
    <label for="setup-SPY" class="setup-tab grade-aplus"><span class="setup-tab-sym">SPY</span><span class="setup-tab-grade">A+</span></label>
    <label for="setup-QQQ" class="setup-tab grade-a"><span class="setup-tab-sym">QQQ</span><span class="setup-tab-grade">A</span></label>
  </div>
  <div class="setup-panels">
    <div class="tier-group" id="tier-aplus"><div class="tier-header">A+ - ACTIONABLE (1)</div>
      <div class="setup-panel" data-setup="SPY"> ...existing _render_candidate_card output... </div>
    </div>
    <div class="tier-group" id="tier-a"><div class="tier-header">A - HIGH QUALITY (1)</div>
      <div class="setup-panel" data-setup="QQQ"> ...existing card... </div>
    </div>
  </div>
</div>
```

Rules:
- Default `checked` = `_primary_card_symbol` when it is a workspace symbol;
  otherwise the first workspace symbol. Exactly one radio is checked. The
  primary-card chart slot is unchanged (`chart_slot_available=(sym ==
  _primary_card_symbol)`), so the default tab shows the inline chart and every
  other tab keeps its `CHART >` disclosure - which is what C's own prototype
  rendered (C-390-candidate-secondary shows `CHART >` for QQQ).
- Tier wrappers `tier-group`/`tier-header` and their labels (including the
  PRD-304 locked "A+ - OBSERVATION ONLY" substitution) are kept verbatim so the
  tier tests keep passing; the per-symbol rules hide tier-groups that do not
  contain the selected symbol.
- Per-symbol rules emitted in the inline `<style>` (deterministic, no ceiling,
  no JavaScript), for each symbol S:
  `#setup-S:checked~.setup-panels .tier-group:not(:has(.setup-panel[data-setup="S"])){display:none}`
  `#setup-S:checked~.setup-panels .setup-panel:not([data-setup="S"]){display:none}`
  `#setup-S:checked~.setup-tabs label[for="setup-S"]{...active}`
  `#setup-S:focus-visible~.setup-tabs label[for="setup-S"]{outline:1px solid #29b6f6;outline-offset:2px}`
- Fail-open: static `_CSS` never hides a panel. With no checked radio, or with
  the inline rules missing, every card renders stacked as today. A selector
  failure can only show more, never hide a candidate.
- Radios use the existing `.chart-toggle` visually-hidden technique (not
  `display:none`), so they stay focusable; native radio arrow-key behavior
  moves selection between tabs. No `<script>`, no `onclick`, no ARIA tablist
  (that is the JS pattern); a labeled radio group is the native equivalent.
- Tab label = symbol + grade letter, plus the lifecycle badge text when
  `_LIFECYCLE_BADGE_CSS` yields one (`.setup-tab-lc {badge_css}`), plus a
  `CHECK` token (`.setup-tab-check`, amber, currentColor border, plain text)
  when the same symbol appears in alert_candidates with
  `setup_quality == MANUAL_CHECK`. The token text is `CHECK`, not `MANUAL
  CHECK`, so PRD-331's "flag only inside #alert-watchlist" tests stay valid;
  the band above remains the primary carrier.
- Visual, desktop (>=641px): `.setup-workspace{display:grid;grid-template-columns:minmax(9ch,13ch) minmax(0,1fr);column-gap:14px;min-width:0}`;
  `.setup-tabs` is a vertical rail (`display:flex;flex-direction:column;align-self:start;border-right:1px solid #222`);
  each `.setup-tab` is `min-height:44px;display:grid;grid-template-columns:1fr auto;align-items:center;padding:0 10px;border-left:3px solid transparent;color:#888;cursor:pointer`;
  active tab: `color:#e0e0e0;background:#0d0d0d;border-left-color:` the grade
  color (reuse `.grade-aplus` #4caf50 / `.grade-a` #8bc34a / `.grade-b` #ff9800
  via the label's grade class). Inside the panel the card becomes a two-column
  grid: `.setup-workspace .candidate-card{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.25fr);column-gap:16px;row-gap:0;min-width:0}`,
  `.candidate-card>*{grid-column:1}`, `.candidate-card>.setup-chart{grid-column:2;grid-row:1/span 20;margin-top:0;border-top:0;padding-top:0}`
  (empty implicit rows collapse; the span is a placement device, not a layout
  count), `.candidate-card>.chart-detail,.candidate-card>.lvl-ladder{grid-column:1/-1}`.
  Result = C-1280 render: brief left, chart right, ladder full width beneath.
- Visual, phone (<=640px): `.setup-workspace{display:block}`; `.setup-tabs{display:flex;overflow-x:auto;gap:0;border-bottom:1px solid #2a2a2a;margin-bottom:8px}`;
  `.setup-tab{flex:0 0 auto;min-height:44px;padding:0 12px;border-left:0;border-bottom:2px solid transparent}`;
  active: `border-bottom-color:` grade color, `background:#0d0d0d`. Panels stack
  below; card internals stack exactly as today.

## 4. A <-> C COHESION

- One font stack (body rule), one size base (13px), no new typeface anywhere.
- One palette: zero new hex values. Tab active/rails reuse grade colors
  (#4caf50/#8bc34a/#ff9800), text #e0e0e0/#888, surfaces #0d0d0d/#101010,
  hairlines #2a2a2a/#222, focus and actionable cyan #29b6f6, warning amber
  #ff9800.
- One rail grammar: 3px left rails carry state everywhere - verdict (A1), NEXT
  EVENT (A2), candidate cards (existing), manual-check rows (existing), active
  desktop tab (new). Phone tabs use a 2px bottom rail because the strip is
  horizontal; same color rule.
- One caps system: h2 (zone) and h3 (subsection) rules unchanged; the tab grade
  letter uses `.tier-header` sizing (.72rem uppercase #888) so tabs read as
  tier metadata, not as new chrome.
- Same separator rhythm: workspace borders are the existing #222/#2a2a2a
  hairlines; no new box, radius, shadow or tile.
- Same disclosure language: `DETAIL >`, `CHART >`, `DETAILS / HISTORY >`
  remain native `<details>`; #319's 44px summary target and `:focus-visible`
  outline apply page-wide so upper and lower disclosures behave identically.

## 5. MOBILE - exact 390px behavior

- body padding 8px (existing 430px block); column = 374px content width.
- Upper surface: identical to today except the verdict/NEXT EVENT rails and
  tabular numerals. No reflow changes below 641px for TAPE or SPY SESSION.
- WATCHING: h2, screen-line, then ALERT WATCHLIST band (full width, amber
  rail, `MANUAL CHECK` flag first token) BEFORE SETUPS; then h3 SETUPS; then
  the horizontal tab strip (each tab >= 44px tall, symbol + grade [+ lifecycle
  token] [+ CHECK]), scrolls horizontally inside itself (`overflow-x:auto`),
  never the page; then the selected panel: tier-header, card-header, IF NOW /
  LIFECYCLE / IN / OUT kv-grid, `DETAIL >`, chart (inline for the primary,
  width 100% of the card; `CHART >` for others), ladder. Low-tier `<details>`
  groups and REMOVED follow.
- Overflow contract: `document.documentElement.scrollWidth <= window.innerWidth`
  at 390x844 and 360x780, default AND with every disclosure open AND with each
  tab selected in turn. Measured with DevTools device metrics (assert
  `innerWidth==390`; `--window-size` is not trustworthy - see
  reference_headless_chrome_viewport_trap).
- Touch targets: every `summary`, `.setup-tab`, `.chart-toggle-label` >= 44px.

## 6. CRITICAL-STATE VISIBILITY (mapping to existing state only)

Without selecting anything the operator can read:
- How many exist: `.screen-line` (screened / on watch / qualified / rejected)
  plus the visible tab count; low tiers show `(n)` in their summary as today.
- Which is active: the single active tab (rail color + #e0e0e0 text); the
  panel's tier-header and card-header repeat symbol and grade.
- Identity / grade / lifecycle of every other setup: every tab shows symbol,
  grade letter and lifecycle transition token; direction/structure of a
  non-selected setup is one tap/arrow away and never hidden by anything else.
- MANUAL CHECK anywhere: the `#alert-watchlist` band sits above the workspace,
  outside every panel, unaffected by selection, with the PRD-331 flag as the
  first visible token; a workspace symbol that is also a MANUAL_CHECK alert
  candidate additionally shows the `CHECK` token on its tab.
- Other existing warnings: integrator skip lines and `.idle-summary` verdicts
  stay above the workspace in #candidate-board (unchanged position);
  `.verdict-warning` and `#staleness-banner` are above the seam (unchanged);
  low-grade SCREENING NOTE rows stay in their tier `<details>` as today.
- Fail-open: if the inline selector rules are absent or no radio is checked,
  every card is visible (today's stacked layout). Nothing new is aggregated;
  no new warning semantics are invented.

## 7. PR #319 SALVAGE

Reuse (engineering):
- `min-width:0` on grid/flex children: `.wrap>*`, `.candidate-card`,
  `.setup-workspace`, `.setup-panel`.
- `minmax(0,1fr)` in every new grid track (workspace, card, SPY SESSION,
  TAPE desktop drivers).
- 44px targets: `#watching-zone summary,#details-history>summary,.setup-tab{min-height:44px;align-content:center;touch-action:manipulation}`.
- Keyboard: `summary:focus-visible,a:focus-visible,.setup-select:focus-visible~.setup-tabs label[for]{outline:1px solid #29b6f6;outline-offset:2px}` (cyan, not #319's #90caf9, for palette continuity).
- Test discipline: `html.count("<script")==1` and `"onclick" not in html`;
  layer visibility independent of `[open]`; deterministic fixture renders at
  390/360/1280; expanded-state overflow measurement; real toggle/selection
  verification in a browser.
- Chart containment: keep the existing `.setup-chart svg{width:100%;height:auto}`;
  do not drop the 520px cap on phone (moot inside the column anyway).

Reject (skin): system-ui sans body font; navy/slate surfaces (#0b1016,
#121a23, #18232f); boxed driver tiles; border-radius panels; `box-shadow` on
the verdict; 20px padding / 14px base / larger gaps; the generic 960px
two-column page grid; `clamp()` headline; phone negative-margin chart bleed.

## 8. IMPLEMENTATION BOUNDARY

FILES (expected):
- `cuttingboard/delivery/dashboard_renderer.py`
  - `_CSS`: append one tail block (~110-140 LOC of rule strings): A1-A6,
    workspace static rules, desktop `@media(min-width:641px)` and
    `@media(min-width:961px)` blocks, one new `@media(max-width:430px)` block.
    No existing rule string edited.
  - WATCHING emission (3163-3436): move the `#alert-watchlist` block above
    `#candidate-board`; add the >=2 high-grade branch that emits the workspace
    (radios, inline per-symbol `<style>`, tab labels, panels wrapping the
    unchanged `_render_candidate_card` calls). ~50-70 LOC. `_render_candidate_card`,
    `_render_setup_chart_block`, `_render_level_ladder`, `_render_spy_session`
    unchanged.
- Tests: new `tests/test_dash_setup_workspace.py` (red guards, section 9);
  deliberate re-baselines in `tests/test_dashboard_d2_seam.py` (below-seam
  hashes; R1/R2/R5/R8 must still PASS unchanged since upper markup is
  untouched), `tests/test_dashboard_renderer.py` (full-document golden equality,
  PRD-330 region pins), `tests/test_dash_manual_check_flag.py` and
  `tests/test_dash_candidates.py` (the "alert-watchlist immediately after
  candidate-board" adjacency inverts to "immediately before"); regenerated
  `tests/data/dashboard_pre_gex_golden.html` and
  `tests/data/dashboard_pre_a1c_chart_golden.html` from the renderer (never
  hand-edited; committed as their own reviewed commit).
- `docs/CALL_SITE_MAP.md` only if it records WATCHING section order (recon
  cache fix); `docs/PRD_REGISTRY.md`, `docs/prd_index.json`,
  `docs/prd_history/PRD-NNN.md` per the PRD process.
- NOT touched: `ui/dashboard.html` / `ui/index.html` (regenerate via the
  `cuttingboard.yml` pipeline, never hand-overwrite), `cuttingboard/market_map.py`,
  `chain_validation.py`, `trade_decision.py`, `execution_policy.py`,
  `contract.py`, `delivery/primary_selection.py`, `delivery/payload.py`,
  `delivery/setup_chart.py`, `ui/styles.css`/`ui/app.js` (unrelated static UI).

Likely scope: ~200-250 LOC production (renderer), ~200-300 LOC tests, two
regenerated goldens. No new dependency, schema, contract field, ceiling or
runtime path.

Materiality (GOV-2 s1 self-check, surfaced, not ruled): presentation-only, no
schema/contract/ceiling/seam change in the pipeline; BUT it recomposes the
operator surface, relocates the MANUAL CHECK band, and re-baselines three
byte-oracle suites and two goldens. Precedent: the D3 composition change went
through a GOV-2 packet (PRD-328 deprecated, PRD-329 granted). Recommendation:
intake as MATERIAL-candidate via Stage-0 PRD so the fresh-context independent
reviewer is required. Helm rules classification; this brief does not.

## 9. ACCEPTANCE TESTS

Semantic (pytest, must be RED before / GREEN after where new):
- S1 workspace emitted iff >= 2 high-grade cards; single/zero cases produce
  today's markup byte-for-byte below the moved alert band.
- S2 exactly N radios, N labels, N `.setup-panel`, N per-symbol rule sets for
  N workspace symbols; exactly one `checked`; ids escape symbols.
- S3 default checked == `select_primary_card_symbol(...)` when in the
  workspace, else first `sorted_syms` high-grade symbol (fixture where the
  primary sits in a low tier).
- S4 tab order == `sorted_syms` order; tier-group ids/labels/counts unchanged
  (existing test_dash_candidates tier tests pass unmodified).
- S5 `#alert-watchlist` index < `#candidate-board` index and both inside
  `#watching-zone`; PRD-331 flag tests pass unmodified except the adjacency
  direction; `MANUAL CHECK` literal count unchanged; `CHECK` tab token present
  iff a workspace symbol is a MANUAL_CHECK alert candidate.
- S6 no JavaScript added: `html.count("<script")==1`, `onclick`/`onchange`
  absent, `role="tab"` absent.
- S7 fail-open: static `_CSS` contains no `display:none` targeting
  `.setup-panel`/`.tier-group` outside the inline per-symbol block; the inline
  block's rules all begin with `#setup-`.
- S8 chart slot: `class="setup-chart"` count unchanged versus today for the
  same fixtures (primary only; 2 when SPY intraday + disclosed daily).
- S9 upper markup untouched: d2_seam R1/R2/R5/R8 pass unmodified.
- S10 CSS discipline: every pre-existing `_CSS` rule string still present
  verbatim; new rules only after the PRD-330 phone block; new phone rules in a
  separate `@media(max-width:430px)` block.
- S11 goldens regenerated, not edited: a test that re-renders the golden
  fixture and compares equals the committed file (existing pattern).
- Full suite green (`pytest`), ruff clean, CI parity (invariant 5).

Visual (fixture renders, attached as evidence, reviewed against the audition):
- V1 populated / stay_flat / halt x 390 / 360 / 1280: top, tape-spy, watching,
  manual-check, expanded, full, and candidate-secondary captures.
- V2 upper surface reads as current product + rails/column/readout (compare
  A-populated-1280-top.png); WATCHING reads as C (compare
  C-populated-1280-watching.png, C-populated-390-candidate-secondary.png).
- V3 MANUAL CHECK band visible above the tab strip in every capture where an
  alert candidate exists, in every selection state.

Browser (headless Chrome, DevTools device metrics; local evidence since CI has
no browser):
- B1 `innerWidth` asserted 390/360/1280; `scrollWidth <= innerWidth` default,
  all disclosures open, each tab selected.
- B2 clicking each label switches the visible panel; arrow keys on a focused
  radio switch tabs; only one panel visible per state; all tabs visible in all
  states.
- B3 `#alert-watchlist` bounding box unchanged across selections and above
  `#setup-workspace`.
- B4 every `summary`, `.setup-tab`, `.chart-toggle-label` >= 44x44.
- B5 `document.scripts.length==1`; no console errors; no external requests.
- B6 LEVELS toggle still switches the SPY layer with the desktop grid applied.

## 10. OPUS CHARGE (to be issued by Helm after the Stage-0 PRD and Gate A)

```
CHARGE D5-IMPL <date>
Standing contract: UNCHANGED
Standing stops + common escalation block apply (CLAUDE.md).
AUTHORITY: IMPLEMENT
MODEL: Opus 4.8 (claude-opus-4-8[1m])

Objective: Implement the frozen D5 design (Direction A upper surface +
Direction C WATCHING workspace) in the dashboard renderer, presentation-only,
with red guards and deliberately re-baselined byte oracles.

Basis: PRD-NNN (D5) at Gate A GRANTED; frozen design =
/tmp/cuttingboard-visual-audition/INTEGRATION_BRIEF.md (copy into
docs/prd_history/PRD-NNN.md or its packet before implementation; the PRD copy
is authoritative once ratified). Audition evidence:
/tmp/cuttingboard-visual-audition/ (AUDITION.md, evidence/). PR #319: reuse
only the techniques listed in brief section 7; its skin is rejected.

Baseline: main @ 45910ff (re-confirm at session start; report HEAD and
origin/main SHAs); branch claude/prd-NNN-d5-a-upper-c-watching-impl (Dustin
creates/checks out; worktree ops are deny-listed for the agent).

Scope (FILES, as the PRD writes them):
  cuttingboard/delivery/dashboard_renderer.py     (_CSS tail append; WATCHING
                                                   emission 3163-3436 only)
  tests/test_dash_setup_workspace.py               (new)
  tests/test_dashboard_d2_seam.py                  (below-seam hash re-baseline only)
  tests/test_dashboard_renderer.py                 (golden equality + PRD-330 region pins re-baseline only)
  tests/test_dash_manual_check_flag.py             (adjacency direction only)
  tests/test_dash_candidates.py                    (adjacency direction only)
  tests/data/dashboard_pre_gex_golden.html         (regenerated, own commit)
  tests/data/dashboard_pre_a1c_chart_golden.html   (regenerated, own commit)
  docs/CALL_SITE_MAP.md                            (only if it records WATCHING order)
  + PRD bookkeeping files per docs/PRD_PROCESS.md
Any other file = STOP (scope boundary), including every upstream compute
module, ui/dashboard.html, ui/index.html, ui/styles.css, ui/app.js.

Acceptance (brief sections 5, 6, 9 are the contract; summarized):
1. Markup: #alert-watchlist emitted before #candidate-board inside
   #watching-zone; setup workspace emitted iff >= 2 high-grade cards; radios /
   labels / panels / inline per-symbol rules 1:1 with workspace symbols;
   default checked = primary when present else first; tier-group markup,
   labels, counts and the PRD-304 lock substitution unchanged;
   _render_candidate_card and chart-slot logic unchanged (setup-chart counts
   identical per fixture).
2. CSS: no existing _CSS rule string edited; all new rules appended after the
   PRD-330 phone block; new phone rules in a separate @media(max-width:430px)
   block; no new hex values; no font change; static CSS never hides a panel
   (fail-open); desktop rules only under min-width media queries.
3. No JavaScript: html.count("<script")==1, no onclick/onchange, no
   role="tab"/tablist; selection is the native radio group.
4. Tests: S1-S11 red guards written first (TDD), then implementation; d2_seam
   R1/R2/R5/R8 pass UNMODIFIED; PRD-331 flag tests pass with only the
   adjacency direction changed; goldens regenerated by the renderer and
   committed in their own commit with the diff reviewed; full pytest green;
   ruff clean; CI green (local green is unverified).
5. Browser evidence B1-B6 at 390x844, 360x780, 1280x960 for populated,
   stay_flat, halt fixtures, produced with DevTools device metrics (assert
   innerWidth), attached to the draft PR as PNG + metrics JSON; no page
   horizontal overflow default, expanded, or per selected tab; MANUAL CHECK
   band position invariant across selections; 44px targets.
6. Commit per validation step (ruff + pytest at each), no attribution
   trailers, no generated logs/*, reports/* committed.

Delta: NONE.

Novel stop:
- Any acceptance item requires touching a file outside Scope, editing an
  existing _CSS rule string, or changing any upstream compute module -> STOP,
  report, Held for your decision.
- The primary symbol cannot be resolved into a workspace default without
  changing select_primary_card_symbol -> STOP.
- A PRD-331 test other than the adjacency direction would need to change ->
  STOP (the MANUAL CHECK literal count and "only in #alert-watchlist" rule
  are load-bearing).
- Browser evidence shows horizontal overflow or a hidden MANUAL CHECK band in
  any state -> STOP; do not paper over with overflow:hidden.
- Materiality expands (new element type, schema read, ceiling) -> STOP,
  GOV-2 upstream order.

Report: draft PR (held, no auto-merge), impl head SHA, test counts (resolved,
not requested), browser evidence paths, goldens commit SHA, then
"Held for your merge"; fresh-context independent review dispatched per
docs/PRD_PROCESS.md before the merge request. Never both author and review.
```

STOP. Design frozen; no implementation authorized by this document.
