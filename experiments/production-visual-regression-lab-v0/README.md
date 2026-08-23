# Cuttingboard Production Visual Regression Torture Lab V0

This is an isolated, dependency-free laboratory for validating production-rendered Cuttingboard dashboards under realistic viewport, state, content, and text-size pressure. It does not change production behavior, and no production file imports from this directory.

The primary truth is browser-observed structure, visibility, and geometry. Screenshots are supporting evidence; fuzzy pixel similarity is not a gate.

## Requirements

- Python 3 with the repository environment at `.venv/bin/python`
- Node.js 22 or newer for built-in `fetch`, `WebSocket`, and `node:test`
- Google Chrome at `/usr/bin/google-chrome`, or `CB_VISUAL_LAB_CHROME=/path/to/chrome`

No package installation or dependency-manifest change is required. The committed baseline was measured with Python 3.13.5, Node.js 22.23.2, and Google Chrome 151.0.7922.108.

## Run it

Run commands from the repository root:

```bash
# Rebuild deterministic renderer fixtures, then run all 438 cases.
experiments/production-visual-regression-lab-v0/run-lab.sh validate

# Run the lab's pure-policy and live-Chrome calibration tests.
experiments/production-visual-regression-lab-v0/run-lab.sh self-test

# Fast runner smoke test: selected NORMAL and PRD-314 cells.
experiments/production-visual-regression-lab-v0/run-lab.sh quick

# Generate the targeted PRD-314 before/after comparison and screenshot pairs.
experiments/production-visual-regression-lab-v0/run-lab.sh calibrate
```

`validate` exits nonzero when an unexpected FAIL is present. That is intentional: the committed baseline is green at 100% but exposes real horizontal-overflow failures under 125–200% text pressure. `calibrate` also exits nonzero because the current 360px/125% artifact introduces page overflow even while resolving the historical `23/13` value-cell clipping. Reports are written before either command exits.

### Inspect an immutable rendered HTML file

```bash
experiments/production-visual-regression-lab-v0/run-lab.sh inspect \
  --html /absolute/path/to/dashboard.html \
  --fixture normal \
  --source-id my-render-2026-08-23 \
  --output experiments/production-visual-regression-lab-v0/reports/inspect-my-render.json
```

The source file is checked, hashed, and opened directly with `file://`; it is never rewritten. `--fixture` selects a truth contract from `fixtures/catalog.json`. Use `--contract PATH` to supply either a catalog or one fixture contract for a different artifact shape.

### Compare two immutable rendered HTML files

```bash
experiments/production-visual-regression-lab-v0/run-lab.sh compare \
  --before /absolute/path/to/before.html \
  --after /absolute/path/to/after.html \
  --fixture normal \
  --viewports 360x800,431x932 \
  --scales 100,125 \
  --before-id before-build \
  --after-id after-build \
  --output experiments/production-visual-regression-lab-v0/reports/comparison.json
```

Omit `--viewports` to use all mandatory viewports. The default comparison scale is 100%; use `--all-scales` or an explicit comma-separated `--scales` list. A comparison records requested critical-text equality, DOM-order changes, geometry deltas, overflow and clipping transitions, Candidate discoverability, Context movement, and screenshot pairs.

## Source and fixture truth

The lab supports two first-class source modes:

1. `fixtures/build_fixtures.py` calls the current `render_dashboard_html` with deterministic in-memory carriers, a fixed clock (`2026-08-23T20:00:00Z`), and production rendering mode. It writes only beneath this experiment.
2. `inspect` and `compare` consume supplied rendered HTML files without changing their bytes.

The generated catalog contains 35 fixtures:

- 15 core states: NORMAL, HALT, OPERATOR LOCK, STATE UNAVAILABLE, CANDIDATE CARRIER UNAVAILABLE, GEX UNAVAILABLE, MOVEMENT UNAVAILABLE, RED-FOLDER EVENT PRESENT, HEALTHY EMPTY RED FOLDER, NO CANDIDATE, MULTIPLE CANDIDATES, OPPORTUNITY SUPPRESSED, QUALIFIED 0 plus an independent B DEVELOPING Candidate, STALE BOARD, and INACTIVE SESSION.
- 18 content-pressure fixtures: Opportunity counts `0, 1, 9, 10, 13, 23, 99, 100, 999`; registry-backed short/long symbol pressure; multiple cards; long but word-wrappable reason/watch/invalidation text; missing optional fields; short/long permissions; and three event-text lengths.
- 2 PRD-314 calibration fixtures: current renderer output and a clearly synthetic specimen with only the two historical phone CSS declarations restored.

Synthetic pressure is labeled in the catalog and report. The fixture builder refuses to make the PRD-314 mutant unless each current CSS declaration occurs exactly once. Source artifacts are never mutated in place.

Truth contracts declare required/forbidden visible text, expected presence or intentional absence, Opportunity label/value pairs, Candidate identity/level/invalidation requirements, minimum or maximum Candidate card counts, authority order, warning-only wrap targets, and expected calibration failures. Impossible carrier combinations are not generated merely to increase case count.

## Matrix

Mandatory viewports are exact CSS-pixel dimensions:

| Width | Height | Purpose |
|---:|---:|---|
| 360 | 800 | narrow production phone and PRD-314 pressure |
| 390 | 844 | representative phone |
| 430 | 932 | last pixel inside the production phone media query |
| 431 | 932 | first pixel outside that media query |
| 768 | 1024 | tablet portrait |
| 960 | 900 | compact desktop |
| 1280 | 800 | representative desktop |
| 1440 | 900 | wide desktop |

Scale modes are `100`, `125`, `150`, and `200`. Chrome browser zoom is unreliable under headless device emulation, so the lab uses an explicit equivalent: root `font-size` scaling while preserving the requested viewport exactly. Every case records the observed viewport and resolved root font size and fails if either drifts.

The bounded matrix totals 438 cases:

- NORMAL: all 8 viewports × 4 scales = 32.
- The other 14 core states: 2 representative viewports × 4 scales = 112.
- The 18 content fixtures: 4 pressure viewports × 4 scales = 288.
- The two calibration fixtures: 360/100, 360/125, and 431/100 = 6.

Add viewports in `runner/matrix.mjs` and `fixtures/build_fixtures.py`, then update the catalog case-count pin and its self-test. Add fixture carriers and contracts in `fixtures/build_fixtures.py`; `validateCatalogCoverage` fails closed if mandatory states, viewports, scales, or content tokens disappear.

## Automated checks and verdict policy

Each applicable case checks:

- exact viewport and root-font scale;
- document `scrollWidth` versus `clientWidth`;
- horizontal and vertical non-scroll-container overflow;
- leaf-text bounds for critical values, including the Opportunity cells;
- clipping by hidden/clip ancestors;
- zero-sized, `display:none`, `visibility:hidden`, ancestor-hidden, or opacity-zero critical content;
- expected element and Candidate card presence/absence;
- Candidate identity, level, and invalidation presence;
- exact Opportunity values;
- Market State, System State, HALT/lock/unavailable text, provenance, qualifier, and fixture-specific authority text;
- required top-level DOM authority order.

The classifier deliberately separates three outcomes:

- `FAIL`: horizontal page overflow over one pixel, critical clipping, hidden authority state, a missing expected Candidate field, wrong authority order, or another explicit contract violation.
- `WARNING`: unusual wrapping from a labeled synthetic string when content remains readable, or an explicitly contracted deep Context displacement.
- `INFORMATIONAL`: geometry, fold participation, conditional height changes, and future Candidate-adjacency evidence.

Wrapping alone is not clipping. A wrapping element fails only when its non-scroll content box or a clipping ancestor actually loses content. Broad block text ranges are not used as clipping evidence because embedded SVG and conditional descendants create false positives; authoritative range bounds are restricted to leaf values such as Opportunity counts, Candidate identity/level/invalidation, provenance, qualifier, and staleness.

## Geometry definitions

The raw probe and stable reports record:

- `firstZoneHeight`: from the production root's top to the Opportunity block's bottom.
- `candidateY`: Candidate wrapper page Y.
- `candidateIdentityY`, `candidateLevelY`, `candidateInvalidationY`: page Y for critical Candidate details when present.
- `contextY`: page Y of the first present Context surface, using the ordered Context key list.
- `gexExposedSpace`: the vertical intersection, in CSS pixels, between GEX and the initial viewport fold.
- `opportunityToCandidateGap`: signed distance from the Opportunity bottom to Candidate top.
- `surfacesBetweenOpportunityAndCandidate` and `opportunityCandidateAdjacent`: structural adjacency evidence.
- `candidateBeforeContext`: DOM-order measurement, not a V0 production requirement.
- `fold.intersecting`: surfaces touching the initial fold.
- `fold.fullyAbove`: surfaces fully visible within the initial fold.

These Candidate measurements make a future PRD-315 assertion expressible without relocating or simulating production authority. V0 records Opportunity-to-Candidate adjacency, Candidate-before-Context, QUALIFIED 0 with an independent B Candidate, and the Candidate wrapper under Opportunity suppression as evidence only.

## Screenshots

Filenames are deterministic:

```text
fixture__360x800__scale-125__fail.png
compare-before-fixture__431x932__scale-100__pass.png
```

The validation run captures:

- NORMAL at all eight mandatory widths at 100%;
- HALT, STATE UNAVAILABLE (the DEGRADED specimen), RED-FOLDER EVENT, and NO CANDIDATE at 390 and 1280 at 100%;
- every FAIL automatically.

Comparison captures both sides of every selected pair. The lab does not create screenshots for every passing matrix cell.

## Output contracts

- `reports/validation.json`: stable validation report with baseline/source identifier, fixture, viewport, scale, geometry, checks, verdict, failures, warnings, screenshot path, and raw evidence.
- `measurements/geometry.json`: deterministic case-keyed raw probe evidence for later reclassification.
- `reports/comparison-prd314.json`: structural before/after pairs and screenshot paths.
- `RESULTS.md`: human-readable baseline summary and validation screenshot inventory.
- `schemas/validation-report.schema.json`: JSON Schema draft 2020-12 validation contract.
- `schemas/comparison-report.schema.json`: JSON Schema draft 2020-12 comparison contract.

JSON normalization recursively sorts object keys, rounds finite numbers to one decimal place, uses stable case/check ordering, omits run timestamps and temporary paths, and ends files with one newline. The self-test proves byte-stable normalization.

## PRD-314 calibration

The calibration pair contains literal `SURFACED 23` and `WATCHLIST 13` values from the current renderer. The mutant changes only:

```css
#market-state,#system-state,#opportunity-survival{padding:12px;margin-bottom:10px}
#opportunity-survival .kv-grid{grid-template-columns:max-content minmax(0,1fr) max-content minmax(0,1fr)}
```

On the committed Chrome 151 host, both historical and current profiles are green for those values at 360×800/100%; the host's font metrics do not reproduce the original clipping at baseline text size. At 360×800/125%, the historical value cells collapse to zero width and the checker fails both `SURFACED 23` and `WATCHLIST 13`. Current CSS preserves the two value cells and does not trigger either targeted leaf-value clipping check.

This targeted calibration is PASS. Independently, the current artifact has 19px of page overflow and parent Opportunity clipping at 360×800/125%, so that complete current case and the structural comparison remain FAIL. The lab reports both facts instead of hiding one behind the other. At 431×932/100%, both profiles pass; a separate browser self-test proves 430 and 431 select different media-query states.

## Committed baseline result

For `cuttingboard@044602770f745e322dc47a88e9bd342dc0955ce7`:

- 438 cases: 252 PASS, 27 WARNING, 159 FAIL.
- 100%: 100 PASS, 12 WARNING, 0 FAIL.
- 125%: 74 PASS, 9 WARNING, 27 FAIL.
- 150%: 45 PASS, 3 WARNING, 60 FAIL.
- 200%: 33 PASS, 3 WARNING, 72 FAIL.
- PRD-314 targeted calibration: PASS.
- Self-tests: 10 passed, 0 failed.

The 158 unexpected failures are retained production evidence, dominated by horizontal overflow and critical parent-surface clipping under enlarged text. They are not waived or converted to warnings.

## Known limitations

- Root-font scaling is a documented text-size proxy, not native browser zoom. It is deterministic and keeps exact viewport boundaries, but it does not model every OS/browser zoom interaction.
- Font metrics and anti-aliasing vary by Chrome and host. Geometry and structural checks are authoritative; PNG bytes are not expected to match across platforms.
- Supplied HTML should be self-contained. Background networking is disabled, so remote fonts/assets may be unavailable and should not be treated as production-equivalent evidence.
- V0 has no fuzzy pixel-diff gate, image similarity threshold, or automatic geometry-tolerance waiver system.
- The committed catalog pins baseline `044602770f745e322dc47a88e9bd342dc0955ce7`. Move that pin deliberately when adopting a new production baseline; per-artifact SHA-256 values still expose byte drift.
- The exact historical PRD-314 defect reproduces at 125% rather than 100% on this Chrome host. The calibration report records that host constraint explicitly.
