# Cuttingboard Accessibility-Pressure Root-Cause Atlas

## Verdict

The baseline's 159 FAIL cases are not 159 product bugs.

- 1 is the expected historical PRD-314 calibration failure.
- 1 is the current synthetic PRD-314 pressure profile and is excluded from production root-cause sizing.
- 30 were false-positive FAIL classifications caused by treating visible own-element overflow as clipping.
- 127 are real production/stress page-overflow cases explained by five distinct, overlapping layout mechanisms.
- 0 real cases fail at 100%.
- 0 real cases remain unexplained.

The machine-readable ledger is `reports/accessibility-root-cause-atlas.json`. It records every originally unexpected case, both original and corrected check IDs, geometry, overflow amount, critical leaf, clipping ancestors, first failing scale, persistence, signature multiplicity, root-cause memberships, and classification.

## Evidence boundary

This atlas uses the immutable raw observations already stored in `reports/validation.json` and `measurements/geometry.json`. The classifier correction changes policy, not browser geometry. It was verified by the lab's browser-backed self-tests and the stored observations were deterministically reclassified.

The corrected production/stress distribution is:

| Scale | Original unexpected | Corrected real failures | False-positive FAILs removed |
|---:|---:|---:|---:|
| 100% | 0 | 0 | 0 |
| 125% | 25 | 15 | 10 |
| 150% | 60 | 40 | 20 |
| 200% | 72 | 72 | 0 |
| Total | 157 | 127 | 30 |

All 127 corrected real failures have horizontal page overflow. None has a clipping ancestor, a hidden or zero-size critical element, or vertical clipping. Page overflow is therefore a downstream symptom, not a sixth root cause.

## Primary page-overflow partition

Each real failure is assigned once to its largest causal surface for case-level accounting:

| Primary mechanism | Cases | First scale | Role |
|---|---:|---:|---|
| Opportunity grid/min-content pressure | 116 | 125% | Root cause |
| Market/System State value-column pressure | 8 | 200% | Root cause |
| Trend lineage long-token pressure | 2 | 150% | Root cause |
| Candidate wrapper/card pressure | 1 | 200% | Root cause |
| **Total** | **127** | — | — |

The partition prevents double-counting. It does not erase distinct secondary mechanisms that coexist in the same case and could become the next constraint after an upstream surface is corrected.

## Root-cause clusters

Cluster counts overlap by design.

| Root cause | Cases explained | First failure | Surfaces | Confidence |
|---|---:|---|---|---|
| Opportunity narrow-phone four-column grid retains max-content label pressure | 116 | 360x800 at 125% | Opportunity | High |
| Shared key/value grid retains intrinsic key/value minimums | 72 | 360x800 at 200% | Market State, GEX | High |
| Fixed-width, overflow-visible Candidate SVG exceeds the card content box | 43 | 360x800 at 150% | Candidate diagram/wrapper | High |
| Candidate level and invalidation phrases retain min-content width | 18 | 360x800 at 200% | Candidate level, invalidation | High |
| Unbreakable `artifact_lineage_state=MISSING` diagnostic token | 2 | 390x844 at 150% | Trend Structure | High |

### 1. Opportunity intrinsic grid pressure

The narrow-phone selector uses four tracks:

```css
#opportunity-survival .kv-grid {
  grid-template-columns: max-content minmax(2.5ch, 1fr)
                         max-content minmax(2.5ch, 1fr);
}
```

The label tracks retain their max-content width while root text grows. At 125%, this is the primary cause in all 15 real failures: 14 overflow the page by 19px and the longer operator-lock profile overflows by 24px. All are green at 100%.

The same mechanism participates in 39 cases at 150% and 62 at 200%. A single selector-scoped correction could therefore remove repeated observations without changing information or authority.

Counterexamples: Opportunity suppression and unavailable carrier states do not render this grid. The 30 corrected visible-bleed cases had no page overflow or clipping ancestor and are not product failures. Candidate and Trend mechanisms are independent even when they coexist with Opportunity pressure.

### 2. Shared key/value min-content pressure

The shared grid uses `grid-template-columns: max-content 1fr`. At 200%, Market State has meaningful intrinsic overflow in 72 cases and GEX in 19 of those cases. Only eight cases are primarily attributed to Market/System State; the rest overlap a larger upstream surface.

A correction could plausibly eliminate many observations, but changing the shared `.kv-grid` rule is a broader cone than an Opportunity-only change and may alter otherwise-green surfaces.

Counterexamples: the entire 125% failure set begins before this mechanism. GEX has no independent primary case. A 1px Market State scroll-width delta at 360x800/150% is below the lab threshold and is host/rounding-sensitive, not a failure.

### 3. Candidate SVG intrinsic width

The Candidate level diagram emits a fixed 280px SVG with `overflow:visible`. Under a narrowed card content box, diagram labels extend the Candidate wrapper's intrinsic width. This appears in 43 corrected failure cases, first at 150%.

This is structurally distinct from Candidate prose pressure. Any future correction must preserve every diagram label; hiding or clipping the SVG would turn overflow into information loss.

Counterexamples: no-candidate/source-missing wrappers without a diagram do not prove this mechanism. Candidate level/invalidation leaf failures first appear at 200% and need separate treatment.

### 4. Candidate action-text min-content pressure

Candidate level and invalidation both clip in the same 18 cases at 200%. The phrases lack a usable break opportunity inside the narrowed card. This is an independent leaf-text mechanism, even though all 18 cases overlap a larger page-width cause.

Counterexamples: long reason/watch text that wraps and remains readable is an intentional warning, not this failure. Candidate wrapper overflow at 150% is attributable to the SVG, not these action phrases.

### 5. Trend lineage token

`artifact_lineage_state=MISSING` is one unbreakable diagnostic token in Trend Structure. It creates two failures in the Candidate-carrier-unavailable fixture, at 390x844/150% and 390x844/200%.

Counterexamples: the Candidate wrapper's separate `SOURCE_MISSING` text is not the overflowing token. Ordinary unavailable explanations wrap normally and do not form another cluster.

## Cascades, false positives, warnings, and host sensitivity

### Cascade

`page-horizontal-overflow` occurs in all 127 real cases. It is the document-level consequence of one or more mechanisms above. It must not be counted as a separate root cause, and repeated surface checks in one case must not be counted as separate bugs.

### False-positive FAILs

Thirty original FAIL cases had all of the following:

- `scrollWidth > clientWidth` on a non-scroll surface;
- `overflow-x: visible`;
- no critical text loss established by an authoritative leaf;
- no clipping ancestor; and
- zero page overflow.

The old classifier called the surface clipped solely from its scroll extent. The correction requires an own-element clipping policy (`hidden` or `clip`), authoritative leaf text exiting its box, or an actual clipping ancestor. Twenty-seven cases now pass and three retain independent readable-wrap warnings.

### Intentional warnings

The corrected report has 30 WARNING verdicts. These record readable wrapping or intentionally deep conditional content and do not represent disappeared critical information.

### Host/font-sensitive evidence

Thirteen corrected failure cases also have a 1px Market State `scrollWidth` delta at 360x800/150%; five additional reclassified cases have the same raw observation. The delta is below the failure threshold and does not explain either verdict. Fourteen 431x932/150% false-positive cases are also boundary/font-sensitive visible-bleed observations. None is promoted to a production root cause.

The PRD-314 calibration profile remains explicitly host-font-sensitive and is kept outside production cluster counts.

## Smallest future product slice

### Recommended

**Make Opportunity's narrow-phone four-column tracks shrinkable under 125% root-text pressure while preserving the 100% content, DOM order, and authority contract.**

Observed problem: 15 real 125% cases produce page overflow—14 by 19px and operator lock by 24px—and Opportunity is the primary overflowing surface in every one. The slice should allow the existing labels/value tracks to shrink or wrap without hiding, shortening, reordering, or horizontally scrolling critical counts.

- Root-cause cluster addressed: Opportunity intrinsic grid pressure.
- Expected 125% payoff: potentially all 15 real 125% failures.
- Production file cone: the responsive CSS emitted by `render_dashboard_html` in `cuttingboard/delivery/dashboard_renderer.py`, limited to the Opportunity narrow-phone selector near the shared `.kv-grid` and `#opportunity-survival .kv-grid` rules.
- Test cone: renderer responsive-CSS assertions in `tests/test_dashboard_renderer.py`, plus focused lab coverage for the 15 125% cases, real counts, operator lock, 360/390, and the 430/431 boundary.
- Cosmetic/layout-only plausibility: high, provided the change is selector-scoped and leaves carrier data, emitted text, DOM order, IDs, and conditions byte-equivalent.
- Governance expectation: likely STANDARD for a narrowly scoped CSS-only correction with exact fixture evidence. Treat it as HIGH-RISK if it expands to shared `.kv-grid` behavior, changes authority/source order, or touches renderer state/carrier semantics.

Explicit exclusions:

- no information shortening, hiding, truncation, or horizontal scrolling for critical values;
- no DOM/source-order or decision-authority change;
- no carrier, schema, provider, or runtime change;
- no generic responsive framework;
- no broad shared `.kv-grid` rewrite;
- no promise of 150%/200% perfection; and
- no per-fixture or per-state CSS exceptions.

What remains afterward: 40 current failures at 150% and 72 at 200% remain outside this slice's acceptance target. Some Opportunity-overlap cases may improve as a side effect, but that is not counted as committed payoff. Shared key/value, Candidate SVG, Candidate action-text, and Trend token mechanisms remain independently measurable.

### Second-best slice

Constrain the fixed Candidate SVG to the available card content width at 150% while preserving all diagram labels. It has a narrower selector cone than a shared grid change and participates in 43 real failures, but it yields no 125% payoff and needs stronger proof against label loss. It should follow, not displace, the Opportunity slice.

### Do not build

- a generic responsive-layout framework for one renderer;
- fuzzy pixel-diff gating as primary truth;
- a broad 150%/200% board redesign;
- content removal or abbreviation to make geometry pass;
- critical-surface horizontal scrolling;
- carrier/schema/provider changes for layout symptoms;
- per-state CSS patches for repeated manifestations of one mechanism;
- a global `.kv-grid` rewrite before a selector-scoped Opportunity correction is exhausted; or
- any reversal or extension of PRD-315's authority order, which passed external validation.

## Lab-quality finding

Severity: material false-positive control defect, experiment-only.

The central classifier promoted visible own-element scroll extent to critical clipping. The smallest correction is in `runner/checks.mjs`; `tests/self-test.mjs` now proves that visible surface bleed without text loss, page overflow, or a clipping ancestor is not a clipping FAIL. Existing browser tests still prove hidden cell clipping, readable wrapping, page overflow, hidden critical content, wrong order, missing content, 430/431 separation, and the PRD-314 specimen.

The GitNexus blast radius is HIGH inside the lab because the classifier feeds validation, comparison, and self-test flows: three direct callers, eight impacted lab symbols, four lab processes, and one affected Runner module. No production module or production execution flow is affected.

## PRD-315 cross-reference

`reports/prd315-external-comparison.json` contains the 240-pair structural/geometry evidence and all 18 acceptance results. Verdict: `PRD315_EXTERNAL_PASS`.
