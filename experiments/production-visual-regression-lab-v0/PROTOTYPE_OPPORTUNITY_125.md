# Opportunity 125% Narrow-Phone Overflow -- Prototype Proof

Experiment-only. No production file is changed. This document plus
`reports/opportunity-125-prototype.json`, `prototypes/opportunity-125.css`, and
`fixtures/currentmain/*` are the deliverable. Final disposition:
**PROMOTION READY - HOLD FOR POLISH WINDOW**.

## Source of truth

- Production main: `2914ec857610e4e952af4895c03617dd8a0848e0` (PRD-315 merged).
- The 15 binding production/state specimens are rendered from EXACT current main
  via `fixtures/build_currentmain_fixtures.py` (loads
  `origin/main:cuttingboard/delivery/dashboard_renderer.py` through git +
  importlib; the working tree is never modified). Only that one renderer file
  differs between the lab's forked base `0446027` and current main, so the loaded
  renderer reproduces exact current-main output.
- Candidate CSS is recorded separately in `prototypes/opportunity-125.css`
  (sha256 `b92984dd28c03bd6ec6c6204d72ebaacc35fbf1f61e722b8b6b78d8d688f3f94`) and
  injected as a runtime `<style>` override. The immutable fixture bytes are never
  rewritten (proved by a self-test that re-hashes the source file after an
  injected run).

## Root cause

The PRD-314 narrow-phone Opportunity rule uses two `max-content` label tracks:

    @media(max-width:430px){
      #opportunity-survival .kv-grid{
        grid-template-columns:max-content minmax(2.5ch,1fr) max-content minmax(2.5ch,1fr)
      }
    }

`max-content` never shrinks, so the widest label pins the grid wider than a
narrow phone as root text grows. The widest label is the two-word
`PRIMARY REJECTION` (rendered whenever there is a primary rejection), and under
operator lock the qualified label becomes the longer `SETUPS FOUND`. That is why
fixtures WITH a `PRIMARY REJECTION` row overflow and fixtures without it
(`qualified-zero-b-candidate`, rejected=0) do not, and why operator lock is the
worst case. All overflow is horizontal page overflow; there is no clipping
ancestor, no hidden critical element, and no vertical clip. Every case is green
at 100%.

## Candidate correction

    @media (max-width: 430px) {
      #opportunity-survival .kv-grid {
        grid-template-columns: auto minmax(2.5ch, 1fr) auto minmax(2.5ch, 1fr);
      }
    }

Exact selector scope: `#opportunity-survival .kv-grid`, inside the existing
`@media(max-width:430px)` block, identical specificity to the production rule so
later source order wins. Nothing outside the Opportunity grid is touched.

### Why it works

`auto` = `minmax(min-content, max-content)`. When there is room (100%, and 430px)
it resolves to `max-content`, so 100% geometry is unchanged. Under narrow-phone
root-text pressure it floors at min-content instead of max-content: the two-word
labels (`PRIMARY REJECTION`, `SETUPS FOUND`) wrap at their space, single-word
labels stay whole, and the value tracks keep PRD-314's `minmax(2.5ch,1fr)` floor
so 2-digit counts never clip. No text is shortened, hidden, truncated, or
horizontally scrolled; DOM order, IDs, and markup are unchanged.

`minmax(0,max-content)` was also measured and also resolves all 12 failing cases,
but `auto` is smaller (a keyword swap), keeps single words unbroken (min-content
floor), and is the smallest truthful correction.

## Binding result: 15 states x 4 phone viewports at 125%

Overflow px BEFORE -> AFTER (candidate CSS). All 15 state fixtures PASS at 125%.

    fixture                          360    390    430    431
    candidate-carrier-unavailable    0->0   0->0   0->0   0->0   (no Opportunity block)
    gex-unavailable                  19->0  0->0   0->0   0->0
    halt                             19->0  0->0   0->0   0->0
    healthy-empty-red-folder         19->0  0->0   0->0   0->0
    inactive-session                 19->0  0->0   0->0   0->0
    movement-unavailable             19->0  0->0   0->0   0->0
    multiple-candidates              19->0  0->0   0->0   0->0
    no-candidate                     19->0  0->0   0->0   0->0
    normal                           19->0  0->0   0->0   0->0
    operator-lock                    49->0  19->0  0->0   0->0   (SETUPS FOUND + PRIMARY REJECTION)
    opportunity-suppressed           0->0   0->0   0->0   0->0   (Opportunity=0, no grid)
    qualified-zero-b-candidate       0->0   0->0   0->0   0->0   (rejected=0, no PRIMARY REJECTION)
    red-folder-event                 19->0  0->0   0->0   0->0
    stale-board                      19->0  0->0   0->0   0->0
    state-unavailable                0->0   0->0   0->0   0->0   (no Opportunity block)

Binding verdicts: before 48 PASS / 12 FAIL, after 60 PASS / 0 FAIL.
Worst case operator-lock 360x800 = 49px overflow, resolved to 0.

Note on the atlas figure: the accessibility atlas prose said "operator lock
overflows by 24px"; that state was only sampled at 390/1280 in the base
validation. This prototype samples all four phone widths and measures operator
lock at 49px (360) and 19px (390). The 49px number supersedes the prose figure.

## 100% regression: 15 states x 8 mandatory viewports

Before: 120 PASS / 0 FAIL. After: 120 PASS / 0 FAIL. New failures: none.
No authority-order change, no candidate discoverability regression, no
visible-text change. Existing 100% geometry preserved (`auto` resolves to
`max-content` when unpressured).

## 430 / 431 boundary

- Override inert at 431 (before == after for every case): PASS. At 431 the phone
  media query is off, so the injected `@media(max-width:430px)` rule never
  applies; a self-test confirms the resolved grid columns are identical with and
  without injection at 431.
- Rule active and clean at 430 (every after-430 overflow <= 1px): PASS.
- A self-test confirms the override changes the resolved Opportunity grid at
  360/125 (pressure) and is inert at 431.

## Mutation proof

1. Current main, no candidate CSS, binding 125%: 12 real failures reproduced.
2. Current main + candidate CSS, binding 125%: 0 failures (60/60 pass).
3. Candidate CSS removed (revert), binding 125%: the same 12 failures return
   (matches step 1 exactly).
4. Current main + candidate CSS, 100% eight-viewport: 0 new failures.

Overall mutation proof: PASS. Two independent runs produce a byte-identical
report (determinism verified).

## PRD-315 is move-only (horizontal geometry unchanged)

Direct base-vs-current-main comparison of operator-lock at 125% (the sharpest
case) shows identical horizontal overflow at every phone viewport
(360:49, 390:19, 430:0, 431:0; delta 0) while DOM order changed. PRD-315
relocates `candidate-board` above `alert-watchlist` -- a vertical move that does
not alter one pixel of horizontal geometry, so the fix proven on current-main
content transfers unchanged.

## Incidental 150% / 200% (informational only; not optimized)

- 150%: before 36 FAIL -> after 3 FAIL. 33 improved incidentally. The 3
  residuals are `state-unavailable` (360) and `candidate-carrier-unavailable`
  (360, 390) -- unhealthy-lineage states that render NO Opportunity grid; their
  overflow is the independent Trend-lineage `artifact_lineage_state=MISSING`
  unbreakable-token cluster, not addressable by an Opportunity change.
- 200%: before 60 FAIL -> after 60 FAIL. 0 improved. At 200% the shared
  `.kv-grid` (Market/System State) min-content pressure and the fixed 280px
  Candidate SVG dominate page width, so Opportunity is no longer the binding
  constraint. No CSS was added to chase these.

Next independent constraints (unchanged from the atlas): shared key/value
min-content grid (Market/System State, GEX) at 200%, and the fixed-width
Candidate level SVG at 150%+.

## Current-main lab calibration disposition

CORRECTION APPLIED (additive; historical evidence preserved).

The reusable `validate` catalog renders the working tree (`0446027`, pre
PRD-315) and truthfully declares that baseline, so it does not treat the
PRD-315 order as a failure -- there is nothing to fix in it, and its pin is left
untouched by design. For the binding prototype, current-main truthfulness is
achieved by a NEW SHA-pinned catalog, `fixtures/currentmain-catalog.json`
(baseline `2914ec8`), whose authority order is the now-canonical PRD-315 order:

    marketState, systemState, opportunity, candidate, gex, movement,
    macro, redFolder, trend, runDelta, scoreboard

A self-test proves this order PASSES on current-main content AND that the
pre-PRD-315 order (candidate after trend) FAILS on current-main content -- the
exact calibration bug, corrected. The historical PRD-315 before/after report
(`reports/prd315-external-comparison.json`, verdict PRD315_EXTERNAL_PASS) and the
0446027 catalog are unchanged.

## Explicit exclusions

- No information shortening, hiding, truncation, ellipsis, or horizontal scroll.
- No DOM/source order or decision-authority change.
- No per-state or operator-lock-specific CSS; one selector-scoped rule.
- No global `.kv-grid` change; no shared Market State / GEX grid change.
- No JavaScript, no markup restructuring, no carrier/schema/provider change.
- No 150%/200% redesign; those are reported as informational only.

## Proof that success is the Opportunity CSS, not an incidental mutation

- The only injected change is the one `#opportunity-survival .kv-grid` rule
  (recorded separately, sha-pinned, static-linted by self-test).
- Removing it reintroduces exactly the 12 failures (mutation step 3).
- The override is inert outside the phone breakpoint (431) and changes only the
  Opportunity grid tracks (self-test).
- Source HTML bytes are unchanged across an injected run (self-test).

The production patch would touch only the existing Opportunity-specific
responsive CSS inside `cuttingboard/delivery/dashboard_renderer.py`. No second
production surface is required.

---

## PROMOTION-READY PATCH SPEC

**PROPOSED GOAL**
Make the narrow-phone Opportunity label tracks shrinkable under 125% root-text
pressure so the board stops overflowing narrow phones, while preserving all
labels/values, DOM order, authority order, and the 100% and 430/431 contracts.

**PROPOSED PRODUCTION FILES**
- `cuttingboard/delivery/dashboard_renderer.py` (one CSS string, line 929 today).

**PROPOSED TEST FILES**
- `tests/test_dashboard_renderer.py` (the asserted Opportunity CSS string,
  ~lines 3938-3939).
- `tests/data/dashboard_pre_gex_golden.html` (regenerate golden; the string
  occurs once).

**PROPOSED CSS BEFORE**

    #opportunity-survival .kv-grid{grid-template-columns:max-content minmax(2.5ch,1fr) max-content minmax(2.5ch,1fr)}

**PROPOSED CSS AFTER**

    #opportunity-survival .kv-grid{grid-template-columns:auto minmax(2.5ch,1fr) auto minmax(2.5ch,1fr)}

**PROPOSED FAIL CONDITION**
A renderer CSS assertion pinning the phone-breakpoint Opportunity grid to
`auto minmax(2.5ch,1fr) auto minmax(2.5ch,1fr)` (RED if it reverts to
`max-content`). Optionally a lab/fixture check that operator-lock at 360x800/125
has <= 1px page overflow (RED at `max-content`, GREEN at `auto`).

**EXPECTED NET PRODUCTION LOC**
0 (one string edit, same line count; two `max-content` tokens -> `auto`).

**EXPECTED 125% PAYOFF**
All 15 binding production/state fixtures pass at 125% across 360/390/430/431;
12 currently-failing phone cases (incl. operator lock 49px) resolve to 0px.

**EXPECTED 100% EFFECT**
None. `auto` resolves to `max-content` when unpressured; 100% eight-viewport
matrix stays 0 FAIL with no visible-text, order, or discoverability change.

**REMAINING OUT OF SCOPE**
150%/200% page overflow driven by the shared `.kv-grid` (Market/System State,
GEX) and the fixed 280px Candidate SVG; the unhealthy-lineage Trend token. These
are independent root causes and are not addressed by this slice.

**GOVERNANCE NOTE (non-binding)**
Cosmetic/layout CSS-only, selector-scoped, byte-equivalent content -- likely
STANDARD, and it rides a cosmetic/polish window. PRD-314 already consumed the
current weekly cosmetic slot, so hold for the next allowed landing window. Do
not allocate PRD-316 from this experiment.
