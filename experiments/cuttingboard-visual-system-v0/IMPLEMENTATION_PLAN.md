# Cuttingboard Visual System Lab V0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use the repository GitNexus exploration and impact-analysis skills before symbol edits. Execute this plan inline because the user authorized a continuous long-form prototype session.

**Goal:** Build three self-contained, responsive static dashboard prototypes that preserve current Cuttingboard information and truth semantics while testing materially different visual architectures.

**Architecture:** One immutable fixture catalog supplies five representative board states. A prototype-only renderer emits the same semantic surfaces for each variant, while each variant owns its composition and responsive CSS. A dependency-free Chrome DevTools runner renders every required viewport and exception state, records DOM measurements, and fails on overflow, missing critical content, or inaccessible disclosure controls.

**Tech Stack:** Plain HTML5, CSS Grid/Flexbox, dependency-free browser JavaScript, native `<details>` disclosure, Google Chrome, and the Chrome DevTools Protocol.

---

## File map

| File | Responsibility |
|---|---|
| `README.md` | Lab intent, authority pins, isolation contract, fixture controls, run instructions, and screenshot inventory |
| `IMPLEMENTATION_PLAN.md` | This bounded execution plan |
| `shared/fixture-data.js` | Immutable content for NORMAL, HALT, DEGRADED, EVENT, and NO CANDIDATE modes |
| `shared/base.css` | Shared tokens, semantic typography, accessibility defaults, and content primitives only |
| `shared/prototype.js` | Prototype-only fixture switching, semantic surface rendering, and query-string support |
| `variant-a/index.html` | Evolutionary composition and variant-owned responsive CSS |
| `variant-b/index.html` | Zoned cockpit composition and variant-owned responsive CSS |
| `variant-c/index.html` | Dense responsive desk composition and variant-owned responsive CSS |
| `tools/visual-test.mjs` | Headless Chrome control, screenshot capture, DOM assertions, and measurement output |
| `measurements.json` | Machine-readable 390x844 and 1280x800 results for each variant |
| `COMPARISON.md` | Measured comparison, exception-state validation, and nine decision-question answers |
| `RECOMMENDATION.md` | Winning direction, stolen features, reversible migration slices, risks, and untouched contracts |
| `screenshots/variant-*/` | Exact-viewport PNG evidence for all required states and widths |

## Task 1: Shared fixture and rendering foundation

**Files:**

- Create: `experiments/cuttingboard-visual-system-v0/shared/fixture-data.js`
- Create: `experiments/cuttingboard-visual-system-v0/shared/base.css`
- Create: `experiments/cuttingboard-visual-system-v0/shared/prototype.js`

- [ ] **Step 1: Define five immutable fixtures with one schema**

The public data contract is:

```js
window.CBLabFixtures = Object.freeze({
  normal: { label, freshness, alerts, marketState, systemState, opportunity,
    candidate, gex, movement, macro, eventDetail, sessionObservation,
    marketControl, trend, changes, scoreboard, diagnostics },
  halt: {},
  degraded: {},
  event: {},
  noCandidate: {}
});
```

NORMAL uses the pinned publication values: EXPANSION; operator cannot monitor; OBSERVE ONLY / NO TRADE; net +$10.0B with Cboe delay and positioning-assumption qualifiers; 12/12 Movement; 23 surfaced / 1 setup / 13 watchlist / 9 rejected / CHOP; SPY B DEVELOPING BULLISH PULLBACK; exact level and invalidation strings; and current Macro, Trend, Changes, and Scoreboard examples. Every fixture keeps environment distinct from permission and retains independent clocks.

- [ ] **Step 2: Add shared visual primitives without imposing composition**

`base.css` defines neutral surfaces, focus-visible outlines, type roles, labels, values, provenance, critical banners, numeric tabulation, tables, 44px disclosure summaries, and safe wrapping. It must not define the A/B/C layout grids.

- [ ] **Step 3: Render semantic surfaces and fixture controls**

`prototype.js` exposes only the fixture switcher:

```js
window.cbLabActivateFixture = cbLabActivateFixture;
```

It reads `?fixture=normal|halt|degraded|event|no-candidate` and `?capture=1`, writes the board inside `[data-board-root]`, and dispatches composition by `body[data-variant]`. Candidate identity, level, invalidation, freshness, permission, halt/lock, event risk, integrity warnings, and required provenance never enter a disclosure.

- [ ] **Step 4: Verify containment and syntax**

Run:

```bash
node --check experiments/cuttingboard-visual-system-v0/shared/fixture-data.js
node --check experiments/cuttingboard-visual-system-v0/shared/prototype.js
```

Expected: both commands exit 0 with no output.

## Task 2: Variant A - Evolutionary

**Files:**

- Create: `experiments/cuttingboard-visual-system-v0/variant-a/index.html`

- [ ] **Step 1: Preserve the familiar vertical read**

Use quieter discrete surfaces in this order: warning lane, MARKET STATE, SYSTEM STATE, Opportunity Survival, Candidate, GEX, Movement, Macro, conditional event detail, conditional session/control, Trend, Changes, Scoreboard, diagnostics. Candidate continuity is restored without literal family-zone wrappers.

- [ ] **Step 2: Make hierarchy typographic and responsive**

At phone widths use one 12px-padded column, a compact 2x2 survival grid, low-chrome rows, and full-width disclosures. At desktop widen to roughly 920px so tables and provenance use available width, while retaining the recognizable stacked architecture.

- [ ] **Step 3: Smoke render**

Run Chrome headless against `variant-a/index.html`. Expected DOM contains `data-variant="a"`, `MARKET STATE`, `OBSERVE ONLY`, and `SPY · B · DEVELOPING`.

## Task 3: Variant B - Zoned Cockpit

**Files:**

- Create: `experiments/cuttingboard-visual-system-v0/variant-b/index.html`

- [ ] **Step 1: Compose a small number of strong zones**

Build five visual zones: State, Opportunity, Context, Structure/Session, and History/Detail. Keep MARKET STATE and SYSTEM STATE as independent sub-surfaces inside State. Use internal hairlines rather than cards around every surface. Event detail bridges State and Context only when present.

- [ ] **Step 2: Keep context visibly subordinate**

Use stronger zone headers and state/opportunity type roles while GEX explicitly reads `CONTEXT ONLY`. Phone stays one continuous board. Desktop uses broad zones and balanced inner columns without product tabs.

- [ ] **Step 3: Smoke render**

Expected DOM includes five `.zone` containers, one candidate minimum-read block, and no horizontal overflow at 390px.

## Task 4: Variant C - Dense Responsive Desk

**Files:**

- Create: `experiments/cuttingboard-visual-system-v0/variant-c/index.html`

- [ ] **Step 1: Create desktop comparison pairs at 960px and wider**

Pair MARKET STATE with SYSTEM STATE; Opportunity Survival with Candidate; GEX with Movement; Changes with Scoreboard. Give Macro and Trend full-width rows. Use at least 1100px of a 1280px viewport without a side rail.

- [ ] **Step 2: Collapse deliberately below desktop**

At 768px and below preserve one column and comfortable text measure. At phone widths transform dense tables into labeled rows with separators, never unlabeled cardlets. Do not apply desktop pairing at tablet width.

- [ ] **Step 3: Smoke render**

Expected DOM includes desktop pair markers, critical state first in source order, and a one-column computed layout at 768px.

## Task 5: Automated visual evidence and measurements

**Files:**

- Create: `experiments/cuttingboard-visual-system-v0/tools/visual-test.mjs`
- Create: `experiments/cuttingboard-visual-system-v0/measurements.json`
- Create: `experiments/cuttingboard-visual-system-v0/screenshots/variant-a/*.png`
- Create: `experiments/cuttingboard-visual-system-v0/screenshots/variant-b/*.png`
- Create: `experiments/cuttingboard-visual-system-v0/screenshots/variant-c/*.png`

- [ ] **Step 1: Capture NORMAL at all six required viewports**

Capture 360x800, 390x844, 430x932, 768x1024, 1280x800, and 1440x900 for A/B/C.

- [ ] **Step 2: Capture four exception fixtures at phone and desktop**

Capture HALT, DEGRADED, EVENT, and NO CANDIDATE at 390x844 and 1280x800 for A/B/C. File names are deterministic: `<fixture>-<width>x<height>.png`.

- [ ] **Step 3: Assert semantic and interaction safety**

For every page, fail if `scrollWidth > clientWidth`, a critical marker is absent, a visible element clips, a disclosure summary is under 44px, or a desktop/tablet grid is active at the wrong breakpoint. Verify non-color text markers for stale, HALT, degraded, and event states.

- [ ] **Step 4: Record required measurements**

At 390x844 record board-top-through-Opportunity height, scroll distance before candidate level, full bordered containers before candidate, first GEX/context position, overflow, and identity/level/invalidation visibility. At 1280x800 record used horizontal width, above-fold surfaces, candidate visibility, and context comparison density.

- [ ] **Step 5: Run the visual suite**

Run:

```bash
node experiments/cuttingboard-visual-system-v0/tools/visual-test.mjs
```

Expected: `42 screenshots captured`, `0 overflow failures`, `0 critical-content failures`, and a written `measurements.json`.

## Task 6: Comparison and recommendation

**Files:**

- Create: `experiments/cuttingboard-visual-system-v0/README.md`
- Create: `experiments/cuttingboard-visual-system-v0/COMPARISON.md`
- Create: `experiments/cuttingboard-visual-system-v0/RECOMMENDATION.md`

- [ ] **Step 1: Document artifact operation and evidence inventory**

README pins main/audit/public SHAs, explains query-string fixture switching, lists every screenshot, and states that all content is static and no production module imports experiment code.

- [ ] **Step 2: Answer all nine decision questions with measurements**

COMPARISON compares ten-second, thirty-second, two-minute, phone, desktop, migration safety, transferable features, patterns to retire, and contracts to preserve. It includes the required 390px and 1280px tables plus exception-state results.

- [ ] **Step 3: Recommend a direction and reversible slices**

RECOMMENDATION names one winner based on decision support rather than prettiness, then sequences small independently reversible production slices. Flag semantic color, dashboard truth, carrier, ordering, high-risk-file, and GOV-2 MATERIAL crossings without solving them or allocating a PRD.

## Task 7: Scope verification, commit, and push

**Files:**

- Modify only paths under `experiments/cuttingboard-visual-system-v0/`

- [ ] **Step 1: Verify no production path changed**

Run:

```bash
git status --short
git diff --name-only -- . ':(exclude)experiments/cuttingboard-visual-system-v0/**'
```

Expected: the second command prints nothing; the first lists only the experiment directory plus the local untracked `.gitnexus/` index.

- [ ] **Step 2: Run GitNexus change detection before committing**

Call `gitnexus_detect_changes({repo:"cuttingboard", scope:"all"})`. Expected: no indexed production symbols or execution flows affected; only unindexed experiment assets are present.

- [ ] **Step 3: Remove the local analysis index side effect**

Delete only `/home/dustin/Projects/cuttingboard-visual-system-v0/.gitnexus/`, which this session created and which is not a lab artifact. Re-run `git status --short` and confirm only the experiment remains.

- [ ] **Step 4: Stage exactly the experiment directory and inspect the index**

Run:

```bash
git add experiments/cuttingboard-visual-system-v0
git diff --cached --name-status
```

Expected: every staged path begins with `experiments/cuttingboard-visual-system-v0/`.

- [ ] **Step 5: Commit and push without opening a PR**

Run:

```bash
git commit -m "experiment: compare Cuttingboard visual systems"
git push -u origin experiment/cuttingboard-visual-system-v0
```

Expected: one commit based on `8bf3b58a98120c43860a689756d84950a0b3aadb`, remote branch created, no PR created, and clean worktree.

## Self-review checklist

- [ ] Exactly three variants exist and differ in architecture, not theme.
- [ ] Five fixture modes work in every variant.
- [ ] All required information remains available; safe disclosures only.
- [ ] Phone is one continuous board with no horizontal overflow.
- [ ] Desktop uses width intentionally; tablet is not forced into desktop density.
- [ ] Critical state and provenance remain visible without interaction.
- [ ] Measurements and all 42 screenshots exist.
- [ ] All nine decision questions and migration flags are answered.
- [ ] No production file, PRD, workflow, branch, PR, or runtime behavior changed.
