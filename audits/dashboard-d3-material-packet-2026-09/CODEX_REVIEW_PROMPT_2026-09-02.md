# Codex Event-1 review prompt — Dashboard D3 MATERIAL packet

```
GOV-2 sec2 step 3 dispatch prompt. Invocation: codex exec -s read-only --skip-git-repo-check -c model_reasoning_effort=high, prompt on stdin, artifact written from captured stdout by the authoring session, 2026-09-02. Reviewed head named inside: 4372b9e.
```

---

You are Sol, a commissioned fresh-context independent design reviewer (Adversary seat) for the Cuttingboard repository at /home/dustin/Projects/cuttingboard. Read-only. Do not edit files. Do not implement anything.

REVIEW TARGET
- PRD: docs/prd_history/PRD-328.md
- Frozen design head: 4372b9e4fdd2a8aa88f9f5c6627b03b94b204e23 (branch claude/prd-328-d3-design). Verify with `git rev-parse HEAD` and `git diff ebf01dd..4372b9e --stat`; the diff must contain only the PRD, the registry row and the prd_index entry. If HEAD differs, say so and stop.
- Merge base / main: ebf01dd888b68a8414704ad774f1245973673ce8.
- Effort: HIGH. This is a design review of a MATERIAL, HIGH-RISK, CONSUMER PRD before any implementation. No implementation exists; do not ask for one.

CONTEXT YOU MUST READ FIRST
- CLAUDE.md (standing contract), docs/contract/MODE_REVIEW.md, docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md sections 1, 2, 10.
- Prior ruled authorities the PRD narrowly supersedes: docs/prd_history/PRD-318.md (R4, R5), docs/prd_history/PRD-321.md (ruling Q2, R3, R4), docs/prd_history/PRD-326.md (D1-Q1, R1-R3, OUT OF SCOPE), docs/prd_history/PRD-327.md (D2, seam tests), docs/DECISIONS.md entries dated 2026-09-01.
- A1 contract: docs/prd_history/PRD-323.md and PRD-324.md; cuttingboard/delivery/intraday_bars.py.
- Renderer: cuttingboard/delivery/dashboard_renderer.py (verify every line number the PRD cites), cuttingboard/delivery/setup_chart.py, cuttingboard/spy_observation.py, cuttingboard/delivery/payload.py, cuttingboard/market_map.py (_watch_zones, _fib_levels).
- Tests: tests/test_dash_candidates.py, tests/test_dashboard_renderer.py, tests/test_dashboard_d2_seam.py, tests/preview_fixtures.py.

ATTACK SURFACE (address each explicitly, with file:line evidence)
1. Disclosure semantics: does native nested `<details open>` inside a closed `<details class="tier-group">` guarantee nothing is visible on initial load, in every browser the project targets (phone Safari/Chrome)? Is there any renderer path where a card ends up inside a closed tier with `open` wrappers but the tier itself is visible (e.g. CSS, summary styling, `list-style`)?
2. Page-load vs explicit-user-intent: does S1 ever render a secondary chart visually open before an operator click? Check the D1-Q1 open-tier branch, TRADE PERMITTED (no level-detail), operator lock, HALT, and the primary-in-C sibling case.
3. Secondary-chart regression: does S1 break PRD-321 R3 / ruling Q2 / PRD-326 R1-R3 or their tests beyond the single narrowed assertion the PRD names? Verify the PRD's claim that no tests/test_dashboard_d2_seam.py golden hash moves (inspect which fixtures contain a C tier and whether that tier is open).
4. SPY data provenance: verify each row of the PRD's S2 recon table against the code. Is `_price_bars["SPY"]` really available at render time with the caption the PRD names? Is `market_map["symbols"]["SPY"]` guaranteed present, and what happens when it is not? Is the observation truly DAILY-only and absent on hourly renders and in every committed fixture?
5. Pre-open / stale / unavailable honesty: for each observation state (PRE_OPEN, OBSERVED, STALE, UNAVAILABLE with each reason) and for missing bars / missing SPY map entry / invalid current_price, is the proposed output honest? Does the NOW price on the chart (market_map current_price, hourly) sitting next to the observation PRICE row (session observation) create a two-clocks ambiguity the PRD fails to label? Does using daily bars with the `bars through <as_of>` caption avoid claiming intraday?
6. Observational vs permission boundary (O3): can `#spy-session` ever read or vary with decision/permission state under the design? Is R7's byte-identity test sufficient? Does placing the block between WATCHING and DETAILS visually rank it against the decision hierarchy in a way that reads as permission?
7. Ladder semantic leakage: with `contract_entry=None, contract_stop=None`, verify `_render_level_ladder` emits no ENTRY/STOP/riskband/lvl-neutral/lvl-locked and no action colouring; check the CSS for `.lvl-*` classes that might still colour rows by action. Does the ladder's `lvl-vwap` or tier classes carry candidate meaning?
8. Duplication: TODAY keeps its one-line SPY SESSION zone-item; DETAILS loses the observation block; the S2-Q1 default keeps MARKET CONTROL in DETAILS. Is any SPY fact rendered twice in a way PRD-318 R5 forbids, or removed in a way its FAIL line forbids? If SPY is also a candidate card (fixture primary_chart_c_grade), two SPY charts exist (candidate `setup-chart` with entry/stop and observational `spy-chart`); is that acceptable, and does the PRD rule it?
9. Ruling Q2 narrowing (S2-Q2): is the proposed narrowing (candidate charts only; the `spy-chart` is the one permitted non-candidate full chart outside disclosure) the smallest honest change, and is the fallback (chart behind a default-closed details inside `#spy-session`) correctly described?
10. Implementation cone: is 70 net production lines in one file credible for S1 + S2 (relocated emitter, chart call, ladder call, unavailable lines, one CSS rule for `.spy-chart`)? Are the FILES complete (any test file that pins bytes of the DETAILS body, the section order, or the SPY block that the PRD did not list)? Is `tests/test_dashboard_renderer.py:4067` (`four_full_weight_zones_before_details`) really unaffected given the new section uses `class="block"` without `operator-zone`?
11. Test vacuity: for each FAIL line and each listed red test T1-T16, would it actually go red on the pre-PRD-328 renderer and green only under the design? Name any FAIL line that is not binary/observable.
12. Accidental A1 expansion: confirm the design touches neither PRD-323 nor PRD-324 surfaces, and that deferring the SPY intraday chart (with the named prerequisite) is the correct disposition under the owner's O4 rule rather than a small adapter this slice should carry.
13. Materiality and authority: is MATERIAL correct, and are the three SUPERSEDED IN PART propagations (PRD-318 R5, PRD-321 Q2/R3, PRD-326 sentence) the exact and complete set? Is any current ruling left in conflict (GOV-2 keeps one current ruling)?

OUTPUT FORMAT (markdown, plain ASCII only; no em-dashes, smart quotes, arrows, or emoji)
# PRD-328 Review - Sol / Codex (commissioned fresh-context independent design review)
**Reviewed head:** <sha>  **Merge base:** ebf01dd
**Verdict:** APPROVE | APPROVE WITH REQUIRED EDITS | REJECT - N REQUIRED, M RECOMMENDED
## Strengths
## REQUIRED findings  (each: ### REQ-n - [category] title; Claim; Evidence with file:line; Smallest fix)
## RECOMMENDED findings (same shape, REC-n)
## Attack-surface checklist (items 1-13, each PASS / FAIL / NOTE with one line of evidence)
## Blockers for Helm (rulings the owner must make; say "none" if none beyond S2-Q1, S2-Q2, S1-Q1)
