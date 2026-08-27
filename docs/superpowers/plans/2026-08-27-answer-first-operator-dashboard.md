# Answer-First Operator Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use writing-plans to execute this plan task-by-task.

**Goal:** Recompose the existing dashboard into VERDICT, TAPE, TODAY, WATCHING, and DETAILS / HISTORY so the first mobile screen answers operator questions without changing any trading semantics.

**Architecture:** Keep `render_dashboard_html` as the sole composition seam and preserve every producer/carrier. Build display-only summaries from values the renderer already holds, translate only closed presentation vocabularies, use native `<details>` disclosure for supporting evidence, and let only the existing authoritative decision title control candidate-detail emphasis.

**Tech Stack:** Python renderer, escaped HTML, CSS media queries, pytest golden/contract tests, Playwright/Chromium visual harness, GitNexus impact verification.

---

## Authority and derivation matrix

| Display fact | Producer/carrier | Classification | Permitted presentation transform |
|---|---|---|---|
| Decision, permission, halt/operator lock, WHY | `run` plus `latest_hourly_run.json.permission`, projected by existing decision helpers | AUTHORITATIVE | Concise copy and visual hierarchy only |
| Regime/environment | existing summary `market_regime` | OBSERVATIONAL | Plain-language label beside Verdict, visibly separate from permission |
| Macro bias and risk votes | existing renderer macro-driver tally | CONTEXTUAL | Adjacent label; values and vote math unchanged |
| Trend summary | `trend_structure_snapshot[*].trend_alignment` | DISPLAY-ONLY DERIVATION | Exact bullish-row count over the already-rendered rows |
| GEX headline | existing qualified `gex_card` | CONTEXTUAL | Existing one-line value/qualifiers; context-only label |
| Participation | existing `movement_card` capture/provenance | OBSERVATIONAL | Availability/count only; no breadth verdict |
| Today events | existing red-folder view | CONTEXTUAL | Compact empty/unavailable copy; independent clock retained |
| Session state | existing SPY observation and MCC projection | OBSERVATIONAL | Closed display translation; no joined carrier/state |
| Opportunity survival | existing symbols-scanned/rejected/watchlist fields | DISPLAY-ONLY DERIVATION | Existing survival arithmetic only |
| Candidate grades/setups | existing `market_map.symbols` | OBSERVATIONAL | Explicit screening label and decision-keyed disclosure only |
| Alert watchlist | existing alert-candidate overlay | AUTHORITATIVE to its own alert contract only | Preserve independent label/order; cannot create trade permission |
| Changes/Scoreboard | existing prior-run diff and publish-carried history | DIAGNOSTIC/HISTORY | Move below Details; no feed repair |

## Task 1: Lock Stage-0 and baseline evidence

**Files:**
- Create: `docs/prd_history/PRD-318.md`
- Create: `docs/superpowers/plans/2026-08-27-answer-first-operator-dashboard.md`
- Modify: `docs/PRD_REGISTRY.md`
- Modify: `docs/prd_index.json`

1. Add the complete HIGH-RISK CONSUMER PRD and exact FILES/LOC ceiling before production edits.
2. Register PRD-318 as `IN PROGRESS` without advancing completion counters.
3. Run `tools/validate_prd_registry.py`, the registry tests, and GitNexus change detection.
4. Commit Stage-0 separately as `PRD-318: stage 0`.

## Task 2: Pin the hierarchy and semantic exclusions with red tests

**Files:**
- Modify: `tests/test_dashboard_renderer.py`
- Modify: `tests/test_dash_candidates.py`
- Modify: `tests/test_dash_system_state.py`

1. Add depth-aware assertions for `system-state`, `tape-zone`, `today-zone`, `watching-zone`, and `details-history`.
2. Assert the Market State peer card is absent while its five existing meanings have destinations.
3. Assert Tape's exact trend count and forbid `ALIGNED`, `DIVERGING`, `CONFLUENT`, and agreement scoring.
4. Pin distinct map-empty and qualification-empty phrases.
5. Pin locked-versus-permitted candidate disclosure while asserting byte-identical source facts.
6. Pin closed SPY/MCC translations, duplicate permission/ORB suppression, timestamp data preservation, and 430/431 CSS boundary.
7. Run the selected tests and confirm they fail for the intended missing hierarchy/copy.

## Task 3: Implement display-only helpers

**Files:**
- Modify: `cuttingboard/delivery/dashboard_renderer.py`

1. Add closed translation tables/helpers for touched SPY/MCC states and unavailable reasons.
2. Add a concise operator timestamp formatter while preserving the raw ISO value in `data-*` attributes.
3. Add a pure Tape summary helper that counts exact `BULLISH` alignment rows and reuses existing macro/GEX/movement facts.
4. Keep all helpers presentation-only; do not import or call any new producer.
5. Run the helper-focused tests.

## Task 4: Recompose the renderer into five zones

**Files:**
- Modify: `cuttingboard/delivery/dashboard_renderer.py`

1. Make `id="system-state"` the VERDICT card and place freshness inside it.
2. Stop emitting the peer `id="market-state"`; redistribute environment/permission/positioning/participation/event meaning to the named zones.
3. Emit TAPE and TODAY from already-loaded values.
4. Wrap Opportunity, Candidate, and alert surfaces in WATCHING without changing their internal source order.
5. Emit full supporting blocks within a default-collapsed DETAILS / HISTORY surface.
6. Group SPY observation and MCC visually; suppress only the exact duplicate permission and ORB projections.
7. Apply decision-keyed candidate disclosure using the existing decision title and native `<details>`.
8. Run focused renderer, authority, candidate, market-state, session, and control tests.

## Task 5: Add responsive CSS and regenerate the golden

**Files:**
- Modify: `cuttingboard/delivery/dashboard_renderer.py`
- Modify: `tests/data/dashboard_pre_gex_golden.html`

1. Add zone/subsection/disclosure styles with a `max-width:430px` mobile treatment and a clean 431px boundary.
2. Preserve keyboard accessibility, visible summaries, and desktop legibility.
3. Regenerate the pre-GEX golden mechanically from its existing deterministic fixture.
4. Run all affected golden tests and inspect the golden diff for stylesheet/markup/copy changes only.

## Task 6: Browser state matrix and measurements

**Files:** No production files; write evidence under a temporary directory.

1. Render before/after fixtures for locked+candidates, permitted+candidate, no-candidates, stale, GEX-unavailable, and pre-open/session-unavailable.
2. Capture 360x800, 390x844, 430x932, and 1280x800 screenshots.
3. Record decision/Tape/Watching Y, page height, top-card count, duplicate facts, raw-token count, and horizontal overflow.
4. Assert desktop facts/text parity and no critical details loss.

## Task 7: Full validation, review, and PR

**Files:**
- Modify during same-PR closeout: `docs/prd_history/PRD-318.md`
- Modify during same-PR closeout: `docs/PRD_REGISTRY.md`
- Modify during same-PR closeout: `docs/prd_index.json`
- Modify during same-PR closeout: `docs/PROJECT_STATE.md`

1. Run full pytest, ruff, registry validation, `git diff --check`, and GitNexus change detection.
2. Obtain the required fresh-context HIGH-RISK review against the exact implementation head; address at most the single governed correction cycle.
3. Push the branch and open a PR without merging.
4. Close PRD-318 in the same PR using its PR number, refresh PROJECT_STATE, rerun gates, and push.
5. Watch required CI to green and return the exact branch/head, matrix, IA, exclusions, measurements, screenshots, collision fixes, tests, CI, PR, and owner-merge verdict.
