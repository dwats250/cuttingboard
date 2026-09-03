# Codex Event-1 review - Dashboard D4 MATERIAL packet (INITIAL PACKET REVIEW)

```
GOV-2 sec2 step 3 artifact. Event type: INITIAL PACKET REVIEW. Reviewer: Sol (Codex CLI 0.150.1, model_reasoning_effort=high, sandbox read-only), Adversary / fresh-context independent reviewer seat; independent of the authoring session (separate process, no shared memory; the fresh-context statement and command list are in the body). Reviewed head: 74c915fc02b083abe112557358274e16d3986614 (packet commit on claude/d4-proto-b-levels-design; merge base 858147f). Date: 2026-09-02. Invocation: codex exec -s read-only --skip-git-repo-check -c model_reasoning_effort=high, prompt (CODEX_REVIEW_PROMPT_2026-09-02.md) on stdin; body below is the captured stdout, verbatim.
VERDICT: REJECT - 8 REQUIRED, 3 RECOMMENDED. Boundary omissions: none (GOV-2 sec6 not triggered). Dispositions: recorded in the packet REVIEW RECORD section (one consolidated correction, GOV-2 sec7 step 2).
```

---

# D4 Packet Review - Sol / Codex (INITIAL PACKET REVIEW, commissioned fresh-context independent design review)

**Reviewed head:** 74c915fc02b083abe112557358274e16d3986614  **Merge base:** 858147f  **Date:** 2026-09-02

**Fresh-context statement:** I operated with no prior authoring-session state. Commands run: `git rev-parse HEAD`; `git diff 858147f..74c915f --stat`; `git diff 858147f..74c915f --name-only`; `git status --short --branch`; `git rev-parse origin/main`; `git merge-base HEAD origin/main`; repeated read-only `wc -l`, `sed -n`, `nl -ba`, `rg -n`, and `rg --files` inspections across the commissioned governance, PRD, renderer, chart, producer, fixture, HTML, and test surfaces; searches for `<input`, `<label`, form-control, element-count, byte/hash, section-order, and SVG-order assertions; a read-only Python SVG paint-order probe; and `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_setup_chart.py tests/test_dashboard_renderer.py tests/test_dashboard_d2_seam.py tests/test_dash_candidates.py tests/test_dash_system_state.py` (the initial sandbox attempt could not create a temporary directory; the approved temporary-directory retry passed 826 tests).

**Verdict:** REJECT - 8 REQUIRED, 3 RECOMMENDED

The frozen-head and scope checks passed. HEAD is the commissioned SHA, the merge base agrees with `origin/main`, and the commit diff contains only the packet. The only worktree addition is the expected untracked review prompt.

## Strengths

- MATERIAL is the correct classification. The proposal changes operator-visible hierarchy, information density, chart interaction, and extension architecture, matching the GOV-2 materiality triggers.
- The packet correctly avoids implementing ASTROLOGY, adding data providers, changing qualification, changing primary selection, or inferring CLOSED.
- The setup-chart inventory is substantively complete. Background, risk band, ORB band, Tier 2 and Tier 3 levels, candles, contract lines, NOW, rail labels, leaders, ticks, and date labels can all be located in [setup_chart.py:205](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:205). Treating VWAP as LEVELS and the ORB band as BASE is a defensible product classification; D-2 is correctly reserved for Helm.
- The native checkbox and explicit label mechanism is compatible with the one-script pin and the no-JavaScript chart rule. The general-sibling selector remains structurally valid when the control precedes `.spy-chart`, even if another sibling is between them.
- No existing test was found that rejects `<input>` or `<label>` merely because those elements appear in the document. The existing script-count assertion remains the direct PRD-329 R3 guard.
- The WATCHING count arithmetic, lock relabel, and top-reason projection are based on existing rendered facts. The closed reason display map is an exact presentation mapping with a fail-closed fallback, not a new market inference.
- NEXT EVENT uses existing red-folder fields and the existing inclusive 48-hour loader window. When `+N more` is nonzero, the DETAILS block cannot be suppressed under the healthy-and-empty rule.
- The focused current-head baseline is green: 826 tests passed.

## REQUIRED findings

### REQ-1 - [design correctness] Two contiguous SVG groups cannot preserve the present paint order

**Claim:** The proposed exact two-group structure, one contiguous `BASE` group and one contiguous `LEVELS` group, is incompatible with the packet's legacy visual-order claim.

**Evidence:** The packet requires exactly two SVG groups at [packet:330-334](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:330). The current renderer emits the background first, then the risk/ORB bands, Tier 3 and Tier 2 levels, candles, contract/NOW lines, and finally the rail at [setup_chart.py:205](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:205), [setup_chart.py:213](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:213), [setup_chart.py:232](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:232), [setup_chart.py:268](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:268), and [setup_chart.py:284](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:284). A read-only SVG probe confirmed that interleaving. If BASE is first, LEVELS moves above candles and NOW. If LEVELS is first, the BASE background covers LEVELS.

**Smallest fix:** Replace the exact two-contiguous-group requirement with an ordering-capable structure, such as `base-background`, `levels`, and `base-price`, while retaining one logical BASE selector contract. Alternatively, explicitly authorize the z-order change and add DOM paint-order plus browser-image evidence. Do not retain both "exactly two contiguous groups" and "preserve existing paint order."

### REQ-2 - [authority propagation] The predecessor ledger omits active byte and mobile-placement clauses that D4 changes

**Claim:** Section 7 does not completely identify the predecessor requirements D4 must narrow or supersede.

**Evidence:** PRD-329 preserves byte identity for no-observation rendering at [PRD-329:228-230](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-329.md:228), with the same obligation in R4 at [PRD-329:270-287](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-329.md:270). Unconditional new `_CSS`, control markup, and regenerated goldens change those bytes even when SPY observation is unavailable. PRD-327 R11 requires specified mobile placement thresholds at [PRD-327:419-430](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-327.md:419), while the packet measures the first candidate at 1264 px, 419 px lower than D3, at [packet:623-626](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:623). Neither conflict is fully propagated in [packet:501-538](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:501).

**Smallest fix:** Add explicit predecessor clauses for PRD-329 R2/R4 no-observation byte identity and PRD-327 R11 mobile placement. State exactly which byte and placement guarantees D4 supersedes and which remain binding.

### REQ-3 - [evidence honesty] The compact SPY header drops required observation evidence

**Claim:** S2 removes facts that remain required by PRD-318 R5 and PRD-329 R8 without requesting or documenting their narrowing.

**Evidence:** The current six-row grid exposes `SESSION` and `OBSERVED AT` at [dashboard_renderer.py:2416-2428](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2416). The producer separately carries `intended_session_date` and `observed_at_utc` at [spy_observation.py:49-61](/home/dustin/Projects/cuttingboard/cuttingboard/spy_observation.py:49), and the payload projects them at [payload.py:165-190](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/payload.py:165). The proposed compact state table at [packet:261-288](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:261) has no session-date presentation and does not clearly preserve a raw observed-time carrier. PRD-329 R8 requires state and observed-time visibility at [PRD-329:408-418](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-329.md:408). PRD-318 R5 treats disappearing evidence as failure at [PRD-318:72-76](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-318.md:72). The proposed ORB wording also does not enumerate every existing `_spy_orb_summary` output shape at [dashboard_renderer.py:229-238](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:229).

The state/reason mapping is otherwise honest: it covers UNAVAILABLE, PRE_OPEN, STALE, and OBSERVED producer paths; uses display mappings instead of raw enums; introduces no CLOSED inference; and the STALE clarifier prevents ladder VWAP from being represented as a current session observation.

**Smallest fix:** Preserve intended session date and observed timestamp in compact visible text or another explicitly approved human-facing evidence carrier. Enumerate every ORB output state, including PRE_OPEN, FORMING, FORMED with bounds, FORMED without bounds, and unavailable forms. If those facts are intentionally removed, add the exact PRD-318 R5 and PRD-329 R8 narrowing for Helm.

### REQ-4 - [interaction and accessibility] Control emission, CSS-off state, and focus behavior are under-specified

**Claim:** The native mechanism is viable, but the packet does not yet specify a state-honest or testable interaction contract.

**Evidence:** R8 requires exactly one checkbox and label in every dashboard at [packet:468-472](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:468), while current SPY failure paths intentionally emit no chart at [dashboard_renderer.py:2429-2450](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:2429). That would create a dead control. With CSS unavailable, the packet says the overlay and unchecked checkbox remain visible at [packet:348-358](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:348); an unchecked control beside a visible LEVELS overlay is fail-open but not state-honest. The packet also does not define how the checkbox is visually hidden or how focus is painted. An explicit `<label for>` is the correct native activation mechanism, but hiding the input with `display:none` or `visibility:hidden` would remove keyboard accessibility; a visually hidden, focusable technique is required. See [MDN label guidance](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/label) and [MDN's visually hidden input technique](https://developer.mozilla.org/en-US/docs/Web/API/File_API/Using_files_from_web_applications).

**Smallest fix:** Emit the control only when a nonempty layered SPY chart exists. Specify initial state and CSS-off semantics so visible overlay and visible control do not disagree. Specify the focusable visually hidden CSS and a tested `:focus-visible` indication on the label. Add healthy, unavailable, no-bars, and invalid-observation control-count tests on phone Safari and Chrome.

### REQ-5 - [placement honesty] The clamp and re-stack algorithm has no complete collision invariant

**Claim:** The ordinary displaced-label case remains price-honest, but the near-edge and one-sided overflow cases are not deterministically resolved.

**Evidence:** True-price horizontal lines, ticks, printed prices, and leaders are required at [packet:371-392](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:371). However, the clamp and inward re-stack language at [packet:383-389](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:383) does not prohibit label-label overlap, label-NOW overlap, or a label crossing NOW after clamping. R10 tests only bounds, ticks, leaders, and scale preservation at [packet:478-482](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:478). Eleven labels at a 10-unit pitch require 110 units before edge and NOW clearance, which can exceed the available space on one side.

**Smallest fix:** Define binary invariants for non-overlapping label boxes, no overlap with the NOW tag, side preservation relative to NOW, deterministic overflow handling, and leader requirements after every displacement. Add a one-sided, near-edge, maximum-capacity stress case that forces clamp and re-stack.

### REQ-6 - [regression proof] R11 lacks a frozen pre-D4 byte oracle

**Claim:** `layers=None` can be implemented byte-identically, but the proposed test cone cannot prove that claim as written.

**Evidence:** The legacy requirement is at [packet:483-485](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:483). Current setup-chart determinism tests render the current function twice and compare the results at [test_setup_chart.py:76-86](/home/dustin/Projects/cuttingboard/tests/test_setup_chart.py:76); the maximum-bar check similarly compares outputs produced by the same implementation at [test_setup_chart.py:203-210](/home/dustin/Projects/cuttingboard/tests/test_setup_chart.py:203). Those tests will not detect a deterministic byte drift introduced by grouped emission. Specific risks are paint order, altered f-string whitespace or attribute order, and changing the current `abs(displacement) > 4` leader threshold at [setup_chart.py:313-356](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:313).

**Smallest fix:** Before implementation, freeze representative pre-D4 SVG bytes or hashes for `layers=None`, including ORB, Tier 2, Tier 3, candles, contract lines, NOW, displaced labels, and the leader threshold boundary. Compare the D4 legacy path directly to those frozen pre-D4 oracles.

### REQ-7 - [boundary and cone] The golden inventory is inaccurate and the authorized FILES set is incomplete

**Claim:** Section 4.5 and the implementation boundary do not enumerate the actual hash and browser-proof surfaces.

**Evidence:** The packet says there are 15 fixture hashes at [packet:199-209](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:199), but `_BASE` contains 16 entries at [test_dashboard_d2_seam.py:45-62](/home/dustin/Projects/cuttingboard/tests/test_dashboard_d2_seam.py:45), and the fixture module explicitly describes sixteen pins at [preview_fixtures.py:322-326](/home/dustin/Projects/cuttingboard/tests/preview_fixtures.py:322). The packet names the primary S2 hash but omits the preserved `_S2_MCC_ONLY_SHA` oracle at [test_dashboard_renderer.py:5469-5471](/home/dustin/Projects/cuttingboard/tests/test_dashboard_renderer.py:5469) and its byte test at [test_dashboard_renderer.py:5645-5660](/home/dustin/Projects/cuttingboard/tests/test_dashboard_renderer.py:5645). It also budgets "one browser acceptance script" without giving that file an authorized path at [packet:540-560](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:540).

The existing four-zone order test at [test_dashboard_renderer.py:4059-4079](/home/dustin/Projects/cuttingboard/tests/test_dashboard_renderer.py:4059) can continue to pass: SPY SESSION is not an operator zone, and placing it second-to-last before WATCHING does not add a fifth operator zone.

**Smallest fix:** Correct 15 to 16; classify both S2 hashes as changed or intentionally preserved; give the browser script an exact FILES path; list every modified golden/HTML fixture explicitly; and recalculate the 120 production-line and 420 test-line ceilings after REQ-1, REQ-4, REQ-5, and REQ-8 are resolved. The current ceilings are provisional but not credible enough to ratify as reviewed.

### REQ-8 - [extension seam] LayerSpec does not define how a layer renders or how its defaults control UI

**Claim:** The registry and structural-probe claims exceed the seam actually specified.

**Evidence:** The proposed `LayerSpec` has `key`, `label`, `default_on`, and `user_control`, and `render_setup_chart(..., layers=None)` accepts selected keys at [packet:315-329](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:315). No mapping connects a registered key to an element renderer. The packet also does not define how `default_on` controls the checkbox state, group visibility, IDs, or selectors. Nevertheless, it claims that a synthetic registry probe will produce an independent group, control, and selector at [packet:486-491](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:486). Without a render callback or equivalent dispatch seam, that probe can prove only metadata generation, or it must emit dead UI.

**Smallest fix:** Either define a bounded key-to-renderer mapping plus deterministic ID, selector, default-state, and purity rules, or reduce the seam to the `layers` keyword and stable group keys and defer the generic registry/control generator. R12 must verify real independent rendering without ASTROLOGY strings or dead operator UI.

## RECOMMENDED findings

### REC-1 - [mobile accessibility] Resolve D-5 to a larger phone target

**Claim:** The measured 25 by 81 px control is not automatically a WCAG 2.2 AA defect, but it is a weak phone target for a new operator control.

**Evidence:** The packet records 25 by 81 px at [packet:604-611](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:604). WCAG 2.2 Target Size Minimum requires a target that contains or is spaced to a 24 by 24 CSS-pixel minimum, so the measured control can conform if the entire measured region is clickable. See [W3C Target Size Minimum](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum). That minimum is a conformance floor, not a strong touch-design target.

**Smallest fix:** Resolve D-5 to at least a 44 px touch height or document why 25 px is accepted, then make the chosen minimum a browser-measured assertion.

### REC-2 - [projection robustness] Specify NEXT EVENT date and time formatting

**Claim:** Deriving a weekday from the validated event date is presentation-only and does not violate the loader's projection boundary, but the formatter and fail-soft behavior are not specified.

**Evidence:** The source view exposes `date`, `time_et`, `name`, and `type` at [red_folder.py:28-33](/home/dustin/Projects/cuttingboard/cuttingboard/red_folder.py:28), validates and sorts those fields at [red_folder.py:73-116](/home/dustin/Projects/cuttingboard/cuttingboard/red_folder.py:73), and applies the inclusive 48-hour window at [red_folder.py:52-57](/home/dustin/Projects/cuttingboard/cuttingboard/red_folder.py:52). The packet example converts `08:30` to `8:30 AM` and adds a weekday at [packet:290-298](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:290), but does not define malformed direct-renderer input behavior.

**Smallest fix:** Specify one deterministic date/time formatter and an exact fallback for malformed view dictionaries. Keep window inclusion entirely loader-owned.

### REC-3 - [test clarity] Separate delta-red tests from preservation guards and retain the legacy font test

**Claim:** T1-T14 are not all expected to fail on the merge base, and that is acceptable if the packet labels them honestly.

**Evidence:** Absence of ASTROLOGY UI, legacy `layers=None` behavior, and architecture freeze checks already pass on 858147f, while new hierarchy, controls, groups, placement, and compact copy should fail. The existing minimum font test requires 7.5 px at [test_setup_chart.py:251-261](/home/dustin/Projects/cuttingboard/tests/test_setup_chart.py:251), while the proposed LEVELS rail floor is 8.5 px at [packet:371-400](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:371).

**Smallest fix:** Mark each T-test as either delta-red on 858147f or base-green carry-forward. Leave the legacy `layers=None` 7.5 px assertion unchanged and add a separate layered-path assertion for the 8.5 px LEVELS floor.

## Attack-surface checklist

1. **FAIL:** Native checkbox/label and `:checked ~` are compatible with the one-script and no-JS rules, and no existing tag assertion breaks, but unconditional control emission and CSS-off state are defective as specified. See REQ-4.
2. **FAIL:** CSS-off fail-open overlay visibility is safe but contradicts an unchecked visible control; the hiding/focus technique is unspecified. A 25 px target can meet the 24 px AA floor but should be increased under REC-1.
3. **PASS:** All drawn chart elements were accounted for. VWAP as LEVELS and ORB band as BASE are defensible classifications, with D-2 correctly left to Helm.
4. **FAIL:** True-price lines, ticks, values, and leaders preserve price meaning in ordinary displacement, but clamp/re-stack lacks non-overlap and NOW-crossing rules. The legacy 7.5 test must remain, with a new layered 8.5 test.
5. **FAIL:** A separate legacy path can return byte-identical SVG, but the two-group paint order and absence of pre-D4 byte oracles leave R11 unproved.
6. **FAIL:** The inventory has 16 fixture hashes, not 15, and omits the MCC-only S2 hash. The four-zone count and order can remain valid with SPY SESSION as a non-operator section before WATCHING.
7. **FAIL:** State/reason presentation is free of raw enums and CLOSED inference, and the STALE clarifier is sound, but intended session date and raw observed-time evidence disappear and the ORB matrix is incomplete.
8. **PASS:** Red-folder fields and inclusive 48-hour semantics are correct; weekday derivation is presentation-only. `+N more in DETAILS` cannot coincide with healthy-and-empty DETAILS suppression.
9. **PASS:** Count, promotion, lock, and reason semantics match the existing WATCHING computation. Replacing the first opportunity `<div>` with `<p>` leaves the candidate board as the first `div.operator-subsection`; the phone `nth-child(10)` rule becomes inert but does not bind the new paragraph.
10. **FAIL:** The layer registry is premature unless it defines renderer dispatch and default-state behavior; without that, R12 cannot prove a second independent layer.
11. **PASS:** The proposed inputs remain observational and do not depend on permission, decision, or ranking state. The fixed seven-parameter `_render_spy_session` signature test remains compatible because `layers=CHART_LAYERS` can be added at the chart call rather than the helper signature; add an AST assertion for that call.
12. **FAIL:** The ceilings are provisional but presently optimistic, the browser script has no path, the hash inventory is incomplete, and T1-T14 mix delta-red and carry-forward tests without classification.
13. **FAIL:** MATERIAL is correct and the packet does not contradict Proto B, the open ladder, no CLOSED inference, no dead ASTROLOGY UI, or no candidate change. However, the predecessor-clause ledger is incomplete, so authority propagation is not ready for Helm ruling.

## Boundary omissions

None at the producer, consumer, carrier, schema, or renderer-class level. The packet found the relevant setup-chart call sites and existing data producers. The narrower omissions are authority states and proof surfaces identified in REQ-2, REQ-3, REQ-6, and REQ-7.

## Blockers for Helm

None beyond D-1 through D-7. The eight REQUIRED findings are packet corrections and propagation work, not new product-direction questions. D-5 should be converted into a binary, testable minimum target decision before PRD ratification.
