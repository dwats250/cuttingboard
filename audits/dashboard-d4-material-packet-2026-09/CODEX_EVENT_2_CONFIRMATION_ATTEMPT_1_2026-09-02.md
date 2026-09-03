# Codex Event-2 exact-corrected-head confirmation - ATTEMPT 1

```
GOV-2 sec7 artifact. Event type: EXACT-CORRECTED-HEAD CONFIRMATION. Reviewer: Sol (Codex CLI 0.150.1, model_reasoning_effort=high, sandbox read-only), Adversary / fresh-context independent reviewer seat; independent of the authoring session and of the Event-1 run (separate process, no shared memory; fresh-context statement and command list in the body). Confirmed head: 955e139b4146f7bafb5d134fff22b80aba671d1b (one consolidated correction after Event 1 at 74c915f). Date: 2026-09-02. Invocation: codex exec -s read-only --skip-git-repo-check -c model_reasoning_effort=high, prompt on stdin (prompt text reproduced at the end of this record); body is the captured stdout, verbatim.
VERDICT: NOT CONFIRMED - 4 residuals (REQ-1, REQ-3, REQ-5, REQ-7). Boundary omissions: none (GOV-2 sec6 not triggered; not DESIGN INCOMPLETE). Disposition: bounded local repair (GOV-2 sec6 last paragraph; D3 precedent attempts 2-4) followed by a newly commissioned exact-head confirmation, ATTEMPT 2.
```

---

# D4 Packet Confirmation - Sol / Codex (EXACT-CORRECTED-HEAD CONFIRMATION, narrow)

**Confirmed head:** 955e139b4146f7bafb5d134fff22b80aba671d1b  **Prior reviewed head:** 74c915f  **Merge base:** 858147f  **Date:** 2026-09-02

**Fresh-context statement:** I operated with no D4 authoring-session or Event-1 run state; I used only the committed prior-finding record and a generic exact-head evidence preference containing no D4 facts. Commands run: `git rev-parse HEAD`; `git status --short --branch`; `git diff 74c915f..955e139 --stat`; `git diff 74c915f..955e139 --name-status`; `git merge-base 955e139b4146f7bafb5d134fff22b80aba671d1b 858147f2057ed967d7d17fbc4a8c2f6cc20bfb71`; `git diff --unified=0 74c915f..955e139 -- <packet>`; `git diff 858147f..955e139 --name-status`; `git diff --check 74c915f..955e139`; `git log -2 --oneline --decorate`; `wc -l`; repeated `nl -ba`, `sed -n`, `rg -n`, `rg --files`, and `find` inspections across the commissioned governance, packet, Event-1 record, predecessor PRDs, renderer, chart, carrier, fixture, test, prototype, measurement, and map surfaces; `curl -s http://127.0.0.1:9222/json/version` (no running CDP endpoint); and three read-only `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c` SVG/order/count probes. One `rg` command failed because of an unmatched backtick and was rerun with corrected quoting. No tests were run and no files were edited.

**Verdict:** NOT CONFIRMED - 4 residual(s)

The exact-head check passed. The `74c915f..955e139` diff contains only the packet, Event-1 prompt, and Event-1 record under `audits/dashboard-d4-material-packet-2026-09/`. The worktree remained clean. The supplied main SHA is the merge base.

## Item table

| Item | Disposition | Evidence |
|---|---|---|
| REQ-1 | NOT RESOLVED | Legacy order is level lines, candles, NOW tag, rail leaders/labels, then date axis at [setup_chart.py:232](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:232), [setup_chart.py:268](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:268), [setup_chart.py:333](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:333), [setup_chart.py:341](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:341), and [setup_chart.py:358](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:358). The corrected three-group design puts every LEVELS rail element before candles and NOW at [packet:397](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:397), so R7's paint-order equality claim is false. The read-only SVG probe confirmed that ordering change. |
| REQ-2 | RESOLVED | PRD-327 R11 is explicitly superseded with replacement placement thresholds at [packet:641](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:641), and PRD-329 R2/R4 no-observation byte identity is explicitly narrowed at [packet:653](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:653). The 390x844 measurements support SPY top 494 and first card 1283 against R14's 560 and 1320 limits. |
| REQ-3 | PARTIALLY RESOLVED | The corrected design preserves the observed date and time, intended-session carrier and visibility rule, producer-keyed state/reason rule, and complete ORB state matrix at [packet:297](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:297). However, the visible raw unknown-reason token at packet line 320 contradicts R2's no-raw-enum rule at packet line 553. The cited formatter actually emits a middle-dot separator at [dashboard_renderer.py:282](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:282), not the ASCII-dot shape claimed by the packet, and `_ORB_STATE_DISPLAY` is at lines 186-192, not 192-198. |
| REQ-4 | RESOLVED | Conditional control emission, `display="none"` presentation default, focusable visual hiding without `display:none` or `visibility:hidden`, `:focus-visible`, and failure-path control counts are specified at [packet:411](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:411) and [packet:582](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:582). |
| REQ-5 | PARTIALLY RESOLVED | The packet now states binary invariants, a capacity formula, deterministic outermost-label overflow, a marker, and one-sided/forced-overflow cases at [packet:460](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:460). But the cited prototype filters dropped levels out before the tick-emission loop at [gen_levels.py:128](</tmp/claude-1000/-home-dustin-Projects-cuttingboard/39db22ac-980f-483c-bfb8-49a50ecb4b93/scratchpad/gen_levels.py:128>) and [gen_levels.py:146](</tmp/claude-1000/-home-dustin-Projects-cuttingboard/39db22ac-980f-483c-bfb8-49a50ecb4b93/scratchpad/gen_levels.py:146>). The executable probe counted 11 retained level lines but only 7 ticks, disproving the claimed four unlabeled ticks. The marker does not directly violate [test_setup_chart.py:161](/home/dustin/Projects/cuttingboard/tests/test_setup_chart.py:161), because that test matches decimal tokens only; the separate layered marker assertion is still appropriate. |
| REQ-6 | RESOLVED | R16 requires a pre-production committed SHA fixture covering ORB, Tier 2, Tier 3, 40 candles, contract lines, operator lock, the exact 4-unit leader boundary, a just-beyond-boundary case, and the A1-C golden's embedded SVG at [packet:623](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:623). It is correctly sequenced before golden regeneration. |
| REQ-7 | PARTIALLY RESOLVED | The 16 `_BASE` hashes are confirmed at [test_dashboard_d2_seam.py:45](/home/dustin/Projects/cuttingboard/tests/test_dashboard_d2_seam.py:45). `_S2_KV_SHA` is correctly retired and `_S2_MCC_ONLY_SHA` correctly preserved by the MCC-only no-observation path at [test_dashboard_renderer.py:5466](/home/dustin/Projects/cuttingboard/tests/test_dashboard_renderer.py:5466) and [test_dashboard_renderer.py:5645](/home/dustin/Projects/cuttingboard/tests/test_dashboard_renderer.py:5645). The FILES and 180/520 ceilings are otherwise credible, but packet lines 379-380 remove the phone `nth-child(10)` rule while R15 promises phone-block byte identity at packet lines 620-622. The rule is inside the protected phone block at [dashboard_renderer.py:1083](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:1083), and PRD-327 R10 requires that block to remain byte-unchanged at [PRD-327:410](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-327.md:410). |
| REQ-8 | RESOLVED | The seam is reduced to `layers=`, `_LAYER_RENDERERS`, `_LAYER_CONTROLS`, stable keys, grouped emission, `display="none"`, and a selector pattern at [packet:382](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:382). The probe patches both maps, emits a real independent rectangle group and control, and separately asserts the one-key production maps and no shipped probe/ASTROLOGY UI at [packet:516](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:516). |
| REC-1 | RESOLVED | A 44 CSS px minimum author default is specified at packet line 433 and R14 line 614; the measurement record reports `controlH: 44` at all three viewports, including [proto_B_levels_measure.json:13](</tmp/claude-1000/-home-dustin-Projects-cuttingboard/39db22ac-980f-483c-bfb8-49a50ecb4b93/scratchpad/proto_B_levels_measure.json:13>). |
| REC-2 | RESOLVED | Deterministic ISO-date and `HH:MM` parsing, escaped verbatim fallback, and loader-owned window inclusion are specified at [packet:347](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:347), consistent with the loader boundary at [red_folder.py:52](/home/dustin/Projects/cuttingboard/cuttingboard/red_folder.py:52). |
| REC-3 | RESOLVED | Delta-red and carry-forward groups are separated at [packet:724](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:724). The existing legacy 7.5 assertion at [test_setup_chart.py:251](/home/dustin/Projects/cuttingboard/tests/test_setup_chart.py:251) remains, with a distinct planned 8.5 layered-path assertion. |

## Residuals

### REQ-1

**Claim:** The corrected three-group structure still does not reproduce legacy paint order.

**Evidence:** Current rail leaders and labels are appended after the NOW tag at `setup_chart.py:333-356`, while the corrected LEVELS group, including rail leaders and labels, precedes the entire base/over group at packet lines 397-405.

**Smallest fix:** Replace the three-group requirement with ordered paint segments that preserve all interleaving, for example `base/under`, `levels/under`, `base/price`, `levels/rail`, `base/axis`, with both LEVELS groups controlled by the same stable selector. Alternatively, obtain an explicit Helm ruling authorizing the paint-order change and replace the legacy-order assertion.

### REQ-3

**Claim:** The header correction preserves the missing evidence but introduces an internally conflicting raw-reason rule and two inaccurate source claims.

**Evidence:** Packet line 320 visibly renders an unknown raw reason token, while packet line 553 prohibits raw enums outside data attributes. `dashboard_renderer.py:290` uses a middle-dot separator, and `_ORB_STATE_DISPLAY` occupies lines 186-192 rather than the cited 192-198.

**Smallest fix:** Put the unknown raw reason only in a `data-raw-reason` attribute and render a deterministic operator-safe fallback. Correct the formatter example and `_ORB_STATE_DISPLAY` citation.

### REQ-5

**Claim:** The forced-overflow prototype does not retain a true-y tick for every dropped label and does not prove all claimed invariants.

**Evidence:** `gen_levels.py:128` removes dropped items from `LEVELS`; the tick loop at `gen_levels.py:146-155` then visits survivors only. The read-only probe found 11 level lines, 7 ticks, 7 labels, and one `+4 in ladder` marker. The generator asserts collision, side, and frame properties at lines 129-138, then assigns `INVARIANTS_OK = True`; it contains no legacy-scale comparison proving invariant (f).

**Smallest fix:** Emit ticks from the original complete level list before label pruning. Add explicit assertions for total tick count, dropped-label tick retention, and layered-versus-legacy y-scale and candle geometry, then regenerate the overflow evidence.

### REQ-7

**Claim:** The corrected FILES/test ledger conflicts with its own phone-block preservation promise.

**Evidence:** Packet lines 379-380 require deleting `dashboard_renderer.py:1097`, but packet R15 lines 620-622 and PRD-327 R10 lines 410-417 require the entire phone block to remain byte-identical.

**Smallest fix:** Keep the now-inert rule at line 1097. If removal is still desired, explicitly supersede PRD-327 R10, change R15, and identify the affected phone-block assertion instead of calling it preserved.

## New findings from the correction

- NF-1: The corrected forced-overflow evidence silently loses ticks for dropped labels. This is the REQ-5 residual above.
- NF-2: The corrected text creates a new internal and predecessor-authority conflict over the protected phone block. This is the REQ-7 residual above.
- NF-3: The corrected SPY header contains a visible raw unknown-reason fallback and inaccurate formatter/mapping citations. This is the REQ-3 residual above.
- NF-4, non-material hygiene: `git diff --check 74c915f..955e139` reports a new blank line at EOF in `CODEX_EVENT_1_REVIEW_2026-09-02.md:150`. This did not affect the verdict count.

No new conflict was found with the section 1 Helm rulings: Proto B remains selected, the ladder remains open, no CLOSED inference is introduced, no ASTROLOGY UI ships, candidate cards remain untouched, and no new data is introduced.

## Boundary omissions

None. The correction revealed no previously omitted consumer class, renderer, carrier, schema surface, or end-to-end seam under GOV-2 section 6. The four chart call sites, transient observation carrier and payload projection, red-folder view, renderer paths, hash/golden surfaces, and browser-evidence path family were accounted for. `DESIGN INCOMPLETE` is therefore not the applicable verdict.

## Blockers for Helm

The packet is not review-clean at `955e139b4146f7bafb5d134fff22b80aba671d1b` and cannot advance to the design-direction ruling.

Held for your decision: the smallest unblocking decision is whether to authorize one bounded local correction covering REQ-1, REQ-3, REQ-5, and REQ-7, followed by a newly commissioned exact-SHA confirmation. There is no additional product-direction question beyond D-1 through D-8.



---

## Dispatch prompt (verbatim)

```
You are Sol, a commissioned fresh-context independent design reviewer (Adversary seat) for the Cuttingboard repository at /home/dustin/Projects/cuttingboard. Read-only. Do not edit files. Do not implement anything. You have no memory of the authoring session or of the Event-1 run; state that you operated in fresh context and list the commands you ran.

EVENT TYPE: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 sec2 step 5, sec7 step 3). This is a NARROW confirmation, not a new broad review: confirm whether each Event-1 finding is resolved at the exact corrected head, and whether the correction introduced any new material boundary omission (GOV-2 sec6) or any new conflict with a Helm ruling.

CONFIRMATION TARGET
- Corrected head: 955e139b4146f7bafb5d134fff22b80aba671d1b (branch claude/d4-proto-b-levels-design). Verify with `git rev-parse HEAD`. Verify `git diff 74c915f..955e139 --stat` touches only audits/dashboard-d4-material-packet-2026-09/ (the packet, CODEX_REVIEW_PROMPT_2026-09-02.md, CODEX_EVENT_1_REVIEW_2026-09-02.md). If HEAD differs, say so and stop.
- Merge base / main: 858147f2057ed967d7d17fbc4a8c2f6cc20bfb71.
- Packet: audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md (corrected revision; REVIEW RECORD at the end lists dispositions).
- Event-1 record: audits/dashboard-d4-material-packet-2026-09/CODEX_EVENT_1_REVIEW_2026-09-02.md (REJECT - 8 REQUIRED, 3 RECOMMENDED at 74c915f).
- Effort: HIGH for verification depth, narrow in scope.

READ FIRST
- docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md sections 2, 6, 7; CLAUDE.md; docs/contract/MODE_REVIEW.md.
- The predecessor files the corrected packet cites in section 7 (PRD-318, PRD-321, PRD-326, PRD-327, PRD-329, PRD-282, PRD-304, PRD-322, PRD-098) and the renderer/chart/test surfaces it cites in sections 4 and 5 (cuttingboard/delivery/dashboard_renderer.py, cuttingboard/delivery/setup_chart.py, cuttingboard/spy_observation.py, cuttingboard/delivery/payload.py, cuttingboard/red_folder.py, tests/test_setup_chart.py, tests/test_dashboard_renderer.py, tests/test_dashboard_d2_seam.py, tests/test_dash_candidates.py, tests/preview_fixtures.py). Verify every NEW or CHANGED line citation in the corrected packet.

FOR EACH PRIOR FINDING (REQ-1..REQ-8, REC-1..REC-3), state RESOLVED / NOT RESOLVED / PARTIALLY RESOLVED with one line of file:line evidence, checking specifically:
- REQ-1: the three-group structure (base/under, levels, base/over) reproduces the legacy paint order at setup_chart.py:205-364, and R7 no longer demands two contiguous groups.
- REQ-2: PRD-329 R2/R4 no-observation byte identity and PRD-327 R11 placement thresholds are now explicitly superseded/narrowed with exact statements; R14's replacement thresholds are stated and measured.
- REQ-3: observed date+time (via _operator_timestamp), the intended session date rule, data-session-date carrier, the full _spy_orb_summary matrix (dashboard_renderer.py:229-238, 192-198) and the unknown-reason fallback are specified; the rule does not perform a renderer-side date comparison or CLOSED inference.
- REQ-4: control emitted only with a non-empty layered SVG; display="none" presentation default makes the CSS-off state agree with the unchecked control; visually-hidden-but-focusable input CSS is specified (no display:none/visibility:hidden); :focus-visible specified; control-count matrix tests listed.
- REQ-5: binary invariants (a)-(f), capacity formula, deterministic overflow with the "+N in ladder" marker; one-sided and forced-overflow cases measured; does the marker conflict with tests/test_setup_chart.py:161 and is that conflict handled honestly.
- REQ-6: R16 legacy oracle (frozen pre-D4 sha fixture incl. the leader-threshold boundary and the A1-C golden's embedded SVG) is specified and sequenced before production change.
- REQ-7: 16 fixtures; _S2_MCC_ONLY_SHA and _S2_KV_SHA classified correctly (verify against tests/test_dashboard_renderer.py:5466-5471, 5510, 5645-5660 and the MCC-only render path); browser script path named; FILES list complete; ceilings recalculated and credible.
- REQ-8: the seam is reduced to the layers keyword + closed maps + stable keys + display="none" default + selector pattern; the probe test proves independent rendering by patching the renderer map; no dead UI.
- REC-1: 44 px minimum height as author default, measured.
- REC-2: deterministic date/time formatter with verbatim fallback; window loader-owned.
- REC-3: T-tests classified delta-red vs carry-forward; legacy 7.5 test kept; layered 8.5 test added.

ALSO CHECK
- Any newly invented symbol, path, line number or claim in the corrected text (e.g. section 4.5's order-test statements, section 10's numbers being internally consistent, the paint-order claim, the R14 thresholds versus the measured values).
- Any new conflict with the Helm rulings recorded in section 1 (Proto B selected, open ladder, no CLOSED inference, no dead ASTROLOGY UI, candidate cards untouched, no new data).
- GOV-2 sec6: does the correction reveal a previously omitted consumer class, renderer, carrier, schema surface or seam? If yes, the packet must be marked DESIGN INCOMPLETE.

OUTPUT FORMAT (markdown, plain ASCII only; no em-dashes, smart quotes, arrows, or emoji)
# D4 Packet Confirmation - Sol / Codex (EXACT-CORRECTED-HEAD CONFIRMATION, narrow)
**Confirmed head:** <sha>  **Prior reviewed head:** 74c915f  **Merge base:** 858147f  **Date:** 2026-09-02
**Fresh-context statement:** <one line: no prior session state; commands run>
**Verdict:** CONFIRMED-CLEAN | NOT CONFIRMED - <n> residual(s) | DESIGN INCOMPLETE
## Item table (REQ-1..REQ-8, REC-1..REC-3: Disposition | Evidence)
## Residuals (each: id, claim, evidence, smallest fix; or "none")
## New findings from the correction (or "none")
## Boundary omissions (or "none")
## Blockers for Helm (or "none beyond D-1..D-8")
```
