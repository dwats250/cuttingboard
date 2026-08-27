# Cuttingboard Mobile Operator Layout Sweep — Experiment Packet

Status: **PROMOTION READY — HOLD FOR NEXT LEGAL POLISH WINDOW**
Production baseline: `origin/main` `8318979fb5c1a52ec9e35db2698ea948c2c5b01e`
Experiment baseline: deterministic current-main renderer fixtures, fixed browser clock
Production changes: **none**

## Decision

Current authority does not permit another cosmetic landing in this weekly
window. PRD-314 and PRD-316 are closed cosmetic-carve-out slices and
`docs/PRD_PROCESS.md` permits at most one polish PRD per week. This packet is a
runtime-injected CSS experiment only. It does not save a new PRD, alter main, or
change any rendered value, source order, visibility gate, carrier, provider,
schema, permission, or decision.

The registry-gap precondition must be cleared before a future PRD is saved:

- `PRD-301.amendment.confirmation.claude.md`
- `PRD-301.gate-fix.confirmation.codex.md`
- `PRD-301.ratified.confirmation.claude.md`
- `PRD-309.impl-review.claude.md`
- `PRD-311.impl-review.codex.md`
- `PRD-312.impl-review.claude.md`
- `PRD-313.impl-review.claude.md`
- `PRD-315.impl-review.claude.md`

## Top three findings

| Rank | Operator cost | Existing block(s) | Smallest fix | 390x844 improvement | Lane |
|---|---|---|---|---:|---|
| 1 | With a stale board, Candidate identity starts at y=831, effectively below the first screen even though the Candidate wrapper begins at y=681. The first screen shows component chrome and the safety scope before the developing setup identity. | `#staleness-banner`, `#candidate-board`, `.candidate-scope` | CSS-only phone compaction; no text hidden | Decision y −27px; Candidate identity y −61px to 770 | Cosmetic MICRO / CONSUMER; current slot unavailable |
| 2 | A healthy empty Candidate state consumes 149px and carries the same full-card weight as a populated setup, delaying GEX to y=781. | `#candidate-board` with `.candidate-scope` + `.unavailable` / `NO_CANDIDATES` | CSS-only empty-state/card chrome compaction | Empty card 149→108px (−28%); GEX y 781→734 | Cosmetic MICRO / CONSUMER; current slot unavailable |
| 3 | GEX, Movement, Macro, Trend, Changes, and Scoreboard all retain full `.block` padding, border, radius, and gap, so Context/History reads as six peer subsystems and page height is 2,416px in the stale phone specimen. | `#gex-context`, `#market-movement`, `#macro-tape`, `#trend-structure`, `#run-delta`, `#scoreboard` | Phone-only CSS grouping through lighter separators and tighter rhythm | Stale page 2416→2207px (−209px, −8.7%); no-candidate page 2012→1829px (−183px, −9.1%) | Cosmetic MICRO / CONSUMER; current slot unavailable |

## Target hierarchy

The existing authority contract requires MARKET STATE before SYSTEM STATE, so
the smallest legal hierarchy is:

1. compact critical status/freshness;
2. MARKET STATE as the five-axis context summary (unchanged semantics/order);
3. SYSTEM STATE as the authoritative decision/permission carrier;
4. Opportunity Survival then independent Candidate continuity;
5. GEX / Movement / Macro as one visually lighter Context run;
6. Trend/session diagnostics;
7. Changes and Scoreboard.

This preserves PRD-312's Market State → System State contract and PRD-315's
Opportunity → Candidate continuity. Opportunity/Candidate remain observation
only; GEX remains CONTEXT ONLY.

## Experiment diff

The only candidate is
`prototypes/mobile-operator-hierarchy.css`. It is injected after the immutable
fixture stylesheet by `runner/mobile_sweep.mjs`.

```css
@media (max-width: 430px) {
  #staleness-banner { padding:6px 10px; margin-bottom:10px; font-size:.75rem; letter-spacing:.04em; }
  #candidate-board { padding:10px; margin-bottom:10px; }
  #candidate-board h2 { margin-bottom:8px; }
  #candidate-board .candidate-scope { padding:6px 8px; margin-bottom:8px; font-size:.72rem; line-height:1.25; }
  #candidate-board:not(:has(.candidate-card)) .unavailable { font-size:.75rem; }
  #gex-context,#market-movement,#macro-tape,#trend-structure { padding:10px 0; margin-bottom:8px; border-right:0; border-left:0; border-radius:0; }
  #run-delta,#scoreboard { padding:10px; margin-bottom:8px; }
}
```

Promotion cone:

- production: `cuttingboard/delivery/dashboard_renderer.py` — add the seven
  ID-scoped CSS rules inside the existing `@media(max-width:430px)` string;
- focused tests: `tests/test_dashboard_renderer.py` — pin exact phone selectors,
  text/order parity, 430/431 boundary, and no overflow;
- deterministic golden: `tests/data/dashboard_pre_gex_golden.html` — regenerate
  only for the stylesheet delta;
- browser proof: reuse this experiment's four viewports and stale/no-candidate
  states.

Expected production size: seven CSS string lines, zero new symbols, zero markup,
zero executable decision logic, zero net carrier/schema/provider change.

## Measurements

### Stale-board specimen

| Viewport | Decision y | Opportunity y | Candidate identity y | Candidate level y | First detailed context y | Page height | Overflow |
|---|---:|---:|---:|---:|---:|---:|---:|
| 360x800 | 379→352 | 580→553 | 846→785 | 933→857 | 1230→1142 | 2475→2252 | 0→0 |
| 390x844 | 364→337 | 565→538 | 831→770 | 903→842 | 1185→1112 | 2416→2207 | 0→0 |
| 430x932 | 318→291 | 519→492 | 770→723 | 842→795 | 1124→1065 | 2326→2147 | 0→0 |
| 1280x800 | 291→291 | 514→514 | 829→829 | 901→901 | 1153→1153 | 2281→2281 | 0→0 |

The stale warning itself is 49→28px on all three phone widths and 49→49px on
desktop.

### Empty/no-candidate specimen

| Viewport | Empty Candidate height | First detailed context y | Page height | Overflow |
|---|---:|---:|---:|---:|
| 360x800 | 149→108 | 796→749 | 2041→1859 | 0→0 |
| 390x844 | 149→108 | 781→734 | 2012→1829 | 0→0 |
| 430x932 | 134→108 | 720→687 | 1922→1769 | 0→0 |
| 1280x800 | 134→134 | 779→779 | 1907→1907 | 0→0 |

### Parity gates

- 12/12 fixture/viewport pairs: critical text byte-equal in the browser probe.
- 12/12 pairs: top-level surface order unchanged.
- 12/12 pairs: horizontal overflow remains zero.
- 3/3 1280x800 specimens: full measured geometry vector unchanged.
- No information is deleted, hidden, abbreviated, truncated, or moved.

## Screenshots

Representative stale-board evidence at the primary 390x844 viewport:

- `mobile-sweep/screenshots/before-stale-board-390x844.png`
- `mobile-sweep/screenshots/after-stale-board-390x844.png`

The measurement JSON preserves the full 360x800, 390x844, 430x932, and
1280x800 geometry matrix; only the representative screenshot pair is retained
on this evidence branch.

Raw measurements:

- `mobile-sweep/before-measurements.json`
- `mobile-sweep/after-measurements.json`

## Validation

- Focused renderer/authority cone: `628 passed`.
- Full suite at exact current main: `3960 passed, 1 xfailed`.
- Ruff: `All checks passed!`.
- Browser parity gates listed above: PASS.
- Registry validator is not clean at baseline because of historical
  unresolvable-commit rows; no new PRD was created and no registry claim is made.

## Landing disposition

**Queued for the next legal polish slot.** Do not land now, do not merge, and do
not allocate/save a new PRD until the eight registry-gap rows are present. At the
next window, rebase/re-render against then-current main, rerun GitNexus impact and
change detection, focused/full tests, and the browser matrix, then submit the
three-file production cone for owner-held merge.
