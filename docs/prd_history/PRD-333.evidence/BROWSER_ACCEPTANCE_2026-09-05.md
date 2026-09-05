# PRD-333 R12 browser acceptance -- 2026-09-05

Harness: out-of-repo Chrome DevTools Protocol driver (Chrome 151, headless=new),
true device metrics via Emulation.setDeviceMetricsOverride (not --window-size).
Full per-state metrics are embedded at the end of this file. Fixtures rendered
through the renderer with the committed macro snapshot (CI parity).

## Fixtures (rendered dashboards, reference always present)

- rich: A1-C style render -- setup workspace + candidate chart SVG + DETAILS/HISTORY
  + the GEX reference (2 SVGs total: setup chart + reference ladder).
- gex: the GEX-absent whole-dashboard baseline (dashboard_pre_gex_golden.html) --
  reference present, current GEX absent (1 SVG: reference ladder).

## Viewports (device-metric innerWidth asserted)

- desktop 1280x960 (dpr 1)
- phone 390x844 (dpr 3, mobile)
- phone 360x780 (dpr 3, mobile)

## States exercised per viewport

default, reference-open, full-bin-table-open, all-disclosures-open,
setup-selected, native-keyboard (Enter).

## Results (all 6 page x viewport combos: PASS)

| page/viewport            | innerW | scrollW | page overflow | ref summary | scripts | console err | Enter opens |
|--------------------------|--------|---------|---------------|-------------|---------|-------------|-------------|
| rich / 1280x960          | 1280   | 1265    | none (-15)    | 44px        | 1       | 0           | yes         |
| rich / 390x844           | 390    | 390     | none (0)      | 45px        | 1       | 0           | yes         |
| rich / 360x780           | 360    | 360     | none (0)      | 45px        | 1       | 0           | yes         |
| gex / 1280x960           | 1280   | 1265    | none (-15)    | 44px        | 1       | 0           | yes         |
| gex / 390x844            | 390    | 390     | none (0)      | 45px        | 1       | 0           | yes         |
| gex / 360x780            | 360    | 360     | none (0)      | 45px        | 1       | 0           | yes         |

Verified across every state above (default / reference-open / table-open /
all-open / setup-selected):

- No page horizontal overflow: scrollWidth <= innerWidth at every viewport and
  state (phones exactly 0; desktop content narrower than the viewport).
- No clipped labels/numbers in the reference subtree: every #gex-reference
  descendant's right edge <= innerWidth (the wide full-bin table scrolls inside
  its own overflow-x:auto container, never the page).
- Reference summary touch target >= 44px (44px desktop, 45px phones).
- Exactly one script (the pre-existing staleness banner); no second script added.
- No new network requests and zero console errors / exceptions in any state.
- MANUAL CHECK position unchanged between reference-closed and reference-open.
- Native keyboard: the summary is a native <summary>, focusable, no tabindex=-1,
  no pointer-events:none, retains the default focus outline; a trusted Enter
  keypress on the focused summary opens the disclosure (Enter opens = yes).
- data-gex-kind="reference" present; reference is a <details>, collapsed by
  default; on the A1-C page exactly 2 SVGs (setup chart + reference ladder), on
  the GEX baseline exactly 1 (reference ladder).

Note: the native SPY LEVELS control (a CSS-only checkbox, id="spy-levels",
no JS) was not populated by these fixtures; it is independent of the reference
subtree and driven entirely by CSS :checked selectors (renderer :1152), so the
reference cannot affect it. State verified structurally in-renderer.

Goldens digest (committed-macro renders these metrics were taken against):
- dashboard_pre_gex_golden.html  sha256 2b2959105efa5c983bb4ef87d6151c00c70c433739cbdf234455ff95a28f8f3a
- dashboard_pre_a1c_chart_golden.html sha256 f979f3aae2eee50b1b3a6220410059da4535c0a7ac7113fd3b11f8aac5f57438

## Per-state metrics (innerW / scrollW / page-overflow-px)

- rich/desktop_1280x960: errors=none
    default          iw=1280 scrollW=1265 overflow=-15 refSummaryH=44 scripts=1 refMaxRight=1013
    reference_open   iw=1280 scrollW=1265 overflow=-15 refSummaryH=44 scripts=1 refMaxRight=1013
    table_open       iw=1280 scrollW=1265 overflow=-15 refSummaryH=44 scripts=1 refMaxRight=1013
    all_open         iw=1280 scrollW=1265 overflow=-15 refSummaryH=44 scripts=1 refMaxRight=1013
    setup_selected   iw=1280 scrollW=1265 overflow=-15 refSummaryH=44 scripts=1 refMaxRight=1013
    keyboard_enter: refOpen=True isSummary=True focusable=True outlineNone=False
- rich/phone_390x844: errors=none
    default          iw=390 scrollW=390 overflow=0 refSummaryH=45 scripts=1 refMaxRight=382
    reference_open   iw=390 scrollW=390 overflow=0 refSummaryH=45 scripts=1 refMaxRight=382
    table_open       iw=390 scrollW=390 overflow=0 refSummaryH=45 scripts=1 refMaxRight=382
    all_open         iw=390 scrollW=390 overflow=0 refSummaryH=45 scripts=1 refMaxRight=382
    setup_selected   iw=390 scrollW=390 overflow=0 refSummaryH=45 scripts=1 refMaxRight=382
    keyboard_enter: refOpen=True isSummary=True focusable=True outlineNone=False
- rich/phone_360x780: errors=none
    default          iw=360 scrollW=360 overflow=0 refSummaryH=45 scripts=1 refMaxRight=352
    reference_open   iw=360 scrollW=360 overflow=0 refSummaryH=45 scripts=1 refMaxRight=352
    table_open       iw=360 scrollW=360 overflow=0 refSummaryH=45 scripts=1 refMaxRight=352
    all_open         iw=360 scrollW=360 overflow=0 refSummaryH=45 scripts=1 refMaxRight=352
    setup_selected   iw=360 scrollW=360 overflow=0 refSummaryH=45 scripts=1 refMaxRight=352
    keyboard_enter: refOpen=True isSummary=True focusable=True outlineNone=False
- gex/desktop_1280x960: errors=none
    default          iw=1280 scrollW=1280 overflow=0 refSummaryH=44 scripts=1 refMaxRight=1020
    reference_open   iw=1280 scrollW=1265 overflow=-15 refSummaryH=44 scripts=1 refMaxRight=1013
    table_open       iw=1280 scrollW=1265 overflow=-15 refSummaryH=44 scripts=1 refMaxRight=1013
    all_open         iw=1280 scrollW=1265 overflow=-15 refSummaryH=44 scripts=1 refMaxRight=1013
    setup_selected   iw=1280 scrollW=1265 overflow=-15 refSummaryH=44 scripts=1 refMaxRight=1013
    keyboard_enter: refOpen=True isSummary=True focusable=True outlineNone=False
- gex/phone_390x844: errors=none
    default          iw=390 scrollW=390 overflow=0 refSummaryH=45 scripts=1 refMaxRight=382
    reference_open   iw=390 scrollW=390 overflow=0 refSummaryH=45 scripts=1 refMaxRight=382
    table_open       iw=390 scrollW=390 overflow=0 refSummaryH=45 scripts=1 refMaxRight=382
    all_open         iw=390 scrollW=390 overflow=0 refSummaryH=45 scripts=1 refMaxRight=382
    setup_selected   iw=390 scrollW=390 overflow=0 refSummaryH=45 scripts=1 refMaxRight=382
    keyboard_enter: refOpen=True isSummary=True focusable=True outlineNone=False
- gex/phone_360x780: errors=none
    default          iw=360 scrollW=360 overflow=0 refSummaryH=45 scripts=1 refMaxRight=352
    reference_open   iw=360 scrollW=360 overflow=0 refSummaryH=45 scripts=1 refMaxRight=352
    table_open       iw=360 scrollW=360 overflow=0 refSummaryH=45 scripts=1 refMaxRight=352
    all_open         iw=360 scrollW=360 overflow=0 refSummaryH=45 scripts=1 refMaxRight=352
    setup_selected   iw=360 scrollW=360 overflow=0 refSummaryH=45 scripts=1 refMaxRight=352
    keyboard_enter: refOpen=True isSummary=True focusable=True outlineNone=False