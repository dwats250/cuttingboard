# Codex Event-2 exact-corrected-head confirmation - ATTEMPT 2

```
GOV-2 sec7 artifact. Event type: EXACT-CORRECTED-HEAD CONFIRMATION, attempt 2. Reviewer: Sol (Codex CLI 0.150.1, model_reasoning_effort=high, sandbox read-only), Adversary / fresh-context independent reviewer seat; independent of the authoring session, the Event-1 run and the attempt-1 run (separate process, no shared memory; fresh-context statement and command list in the body). Confirmed head: d5624442dfc3bfe85cd6f80571df0ac19961f64f (bounded repair after attempt 1 at 955e139). Date: 2026-09-02. Invocation: codex exec -s read-only --skip-git-repo-check -c model_reasoning_effort=high, prompt on stdin (reproduced at the end); body is the captured stdout, verbatim. Two earlier dispatches of this attempt were stopped externally before producing output and are not review events.
VERDICT: NOT CONFIRMED - 4 residuals (REQ-1 stale three-group prose, REQ-5 invariant (f) overclaimed for the prototype, REQ-7 estimate/ceiling arithmetic and an unscripted chart-top number, REQ-8 two-position renderer-result contract unspecified). Helm confirmation items 1-13: all PASS. Boundary omissions: none (not DESIGN INCOMPLETE). Disposition: Helm-authorized ONE consolidated packet-only repair (charge "D4 - EVENT-2C BOUNDED PACKET REPAIR + EXACT-HEAD CONFIRMATION", 2026-09-02) followed by a newly commissioned exact-head confirmation, ATTEMPT 3.
```

---

# D4 Packet Confirmation - Sol / Codex

**Event:** EXACT-CORRECTED-HEAD CONFIRMATION, ATTEMPT 2  
**Role:** Sol, fresh-context independent design reviewer, Adversary seat  
**Confirmed head:** `d5624442dfc3bfe85cd6f80571df0ac19961f64f`  
**Prior attempt-1 head:** `955e139b4146f7bafb5d134fff22b80aba671d1b`  
**Merge base:** `858147f2057ed967d7d17fbc4a8c2f6cc20bfb71`  
**Date:** 2026-09-02  
**Verdict:** **NOT CONFIRMED - 4 residuals**

I operated in fresh context, with no memory of the authoring session or Event-1 run. I used the committed attempt-1 Residuals section only as the permitted prior-findings list. No files were edited, no implementation was performed, and the worktree remained clean. No pytest suite was run because this is a design-only confirmation; the proposed runtime does not exist at this head.

The exact-head and scope checks passed. `955e139..d562444` touches only the packet directory and exactly the three expected files. The supplied main SHA is the merge base. `git diff --check` is clean.

## Prior findings

| Finding | Disposition | Evidence |
|---|---|---|
| REQ-1 | **PARTIALLY RESOLVED** | The operative architecture and R7 now specify five segments in legacy order at [packet:409](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:409) and [packet:602](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:602), matching background, band/levels, candles/NOW, rail, axis at [setup_chart.py:205](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:205). However, the current surface ledger and measurement method still call it a “three-group” structure at [packet:724](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:724) and [packet:799](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:799). |
| REQ-2 | **RESOLVED** | PRD-327 R11 is expressly replaced by R14 at [packet:678](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:678), and PRD-329 R2/R4 no-observation byte identity is expressly superseded in part at [packet:685](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:685), against the original clauses at [PRD-329:228](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-329.md:228) and [PRD-329:270](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-329.md:270). |
| REQ-3 | **RESOLVED** | The corrected matrix keeps observed date and time through `_operator_timestamp`, carries `data-session-date`, keys intended-date visibility on producer state/reason without a renderer date comparison, enumerates every ORB result, and uses an operator-safe unknown-reason fallback at [packet:305](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:305). The cited implementation surfaces are correctly located at [dashboard_renderer.py:186](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:186), [dashboard_renderer.py:229](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:229), and [dashboard_renderer.py:282](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/dashboard_renderer.py:282). |
| REQ-4 | **RESOLVED** | Conditional control emission, presentation-attribute `display="none"`, focusable visual hiding, `:focus-visible`, and the zero/one control matrix are specified at [packet:428](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:428) and [packet:613](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:613). |
| REQ-5 | **PARTIALLY RESOLVED** | Tick retention is fixed: the design emits ticks from the complete list at [packet:482](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:482), and the prototype does so at [gen_levels.py:130](/tmp/claude-1000/-home-dustin-Projects-cuttingboard/39db22ac-980f-483c-bfb8-49a50ecb4b93/scratchpad/gen_levels.py:130) and [gen_levels.py:150](/tmp/claude-1000/-home-dustin/Projects/cuttingboard/39db22ac-980f-483c-bfb8-49a50ecb4b93/scratchpad/gen_levels.py:150). But invariant (f) is defined as equality at [packet:504](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:504), while the prototype permits `<= 0.3` SVG-unit differences at [gen_levels.py:205](/tmp/claude-1000/-home-dustin/Projects/cuttingboard/39db22ac-980f-483c-bfb8-49a50ecb4b93/scratchpad/gen_levels.py:205); the read-only probe found four 0.1-0.2 differences and `exact_y=False`. |
| REQ-6 | **RESOLVED** | R16 requires a pre-production committed oracle covering Tier 2/3, ORB, 40 candles, contract/lock cases, exactly-at and just-beyond the 4-unit leader boundary, and the A1-C golden’s embedded SVG at [packet:655](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:655), sequenced before golden regeneration. |
| REQ-7 | **PARTIALLY RESOLVED** | The 16 fixtures are present at [test_dashboard_d2_seam.py:45](/home/dustin/Projects/cuttingboard/tests/test_dashboard_d2_seam.py:45); `_S2_KV_SHA` retirement and `_S2_MCC_ONLY_SHA` preservation match [test_dashboard_renderer.py:5469](/home/dustin/Projects/cuttingboard/tests/test_dashboard_renderer.py:5469) and the MCC-only path at [test_dashboard_renderer.py:5645](/home/dustin/Projects/cuttingboard/tests/test_dashboard_renderer.py:5645); the phone rule is now kept at [packet:389](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:389). However, section 8 totals about `+140 + +40 = 180` production lines but declares 185 at [packet:722](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:722), while the review record still says 180 at [packet:901](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:901). The claimed 390px chart top of 661 at [packet:843](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:843) is not captured by `shoot_levels.py` and reproduced as 654 in the independent CDP query; the threshold still passes. |
| REQ-8 | **PARTIALLY RESOLVED** | The closed maps, stable keys, default-off selector, and absence of dead UI remain stated at [packet:394](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:394) and [packet:543](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:543). The five-segment repair introduces a regression, however: a renderer is said to return “SVG elements only” at [packet:424](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:424), while one map entry must emit independently positioned `under` and `rail` segments at [packet:455](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:455). The return/part contract and compositor insertion rule are not specified, and the one-rectangle probe at [packet:554](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:554) cannot prove that two-position behavior as written. |
| REC-1 | **RESOLVED** | The 44 CSS px author default is specified at [packet:443](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:443) and measured as 44 at all three viewports in [proto_B_levels_measure.json:1](/tmp/claude-1000/-home/dustin/Projects/cuttingboard/39db22ac-980f-483c-bfb8-49a50ecb4b93/scratchpad/proto_B_levels_measure.json:1). |
| REC-2 | **RESOLVED** | ISO date and `HH:MM` parsing, escaped verbatim fallback, and loader-owned window selection are specified at [packet:357](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:357), consistent with [red_folder.py:52](/home/dustin/Projects/cuttingboard/cuttingboard/red_folder.py:52). |
| REC-3 | **RESOLVED** | Delta-red and carry-forward tests are separated at [packet:757](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:757); the existing legacy 7.5 assertion remains at [test_setup_chart.py:251](/home/dustin/Projects/cuttingboard/tests/test_setup_chart.py:251), with a separate planned layered 8.5 assertion. |
| NF-4 | **RESOLVED** | [CODEX_EVENT_1_REVIEW_2026-09-02.md:149](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/CODEX_EVENT_1_REVIEW_2026-09-02.md:149) is the final line; the byte probe returned `ends_one_newline True`. |

## Residuals

### REQ-1: contradictory group count remains

**Claim:** The actual five-segment design preserves legacy SPY paint order, but the packet still describes the implementation and measurement structure as “three-group.”

**Evidence:** [packet:409](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:409) specifies five groups, while [packet:724](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:724) and [packet:799](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:799) say three-group.

**Smallest fix:** Replace both current “three-group” descriptions with “five-segment,” and mark the Event-1 three-group disposition as later found incomplete by attempt 1 so the chronology does not continue to assert that it preserved paint order.

### REQ-5: invariant (f) is still not proved as defined

**Claim:** Tick completeness and overflow are now proved, but the prototype does not prove exact layered-versus-legacy scale/line equality.

**Evidence:** The actual legacy and prototype LEVELS y lists were:

```text
legacy:  47.6 56.3 65.1 67.2 72.4 73.7 74.1 82.1 85.0 93.4 106.5
layered: 47.7 56.5 65.2 67.2 72.5 73.7 74.1 82.1 85.0 93.4 106.4
```

The prototype assertion explicitly permits those differences at [gen_levels.py:205](/tmp/claude-1000/-home/dustin/Projects/cuttingboard/39db22ac-980f-483c-bfb8-49a50ecb4b93/scratchpad/gen_levels.py:205). In addition, [packet:818](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:818) says invariants (a)-(f) were asserted on every case, contradicting [packet:521](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:521), which limits the approximate scale comparison to the live case.

The forced-overflow repair itself is good: 11 lines, 11 ticks, 7 labels, and one `+4 in ladder` marker. The marker does not violate [test_setup_chart.py:161](/home/dustin/Projects/cuttingboard/tests/test_setup_chart.py:161), whose numeric-token regex requires a decimal, and the packet correctly limits that guard to `layers=None`.

**Smallest fix:** Either generate the prototype LEVELS positions from the same exact legacy y-scale and assert equality, or describe the prototype comparison truthfully as approximate evidence and leave exact invariant (f) to the mandatory implementation test. Correct line 818 accordingly.

### REQ-7: ceiling and measurement record are internally inconsistent

**Claim:** The FILES inventory and phone/hash classifications are repaired, but the claimed production ceiling and one exact placement value do not reconcile.

**Evidence:** [packet:722](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:722) estimates `setup_chart.py` at +140 and `dashboard_renderer.py` at net +40, yet [packet:734](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:734) totals 185 “across the two modules.” The durable disposition says 180. The independent 390x844 CDP query returned `spyTop=494`, `chartTop=654`, `watchingTop=1173`, `firstCard=1283`, while the packet claims chart top 661. All R14 limits still pass.

**Smallest fix:** Choose and propagate one production ceiling, explaining any reserve explicitly. Add `chartTop` and `watchingTop` to the measurement script/output if those values remain load-bearing, then use the reproduced value.

### REQ-8: five-segment repair leaves the renderer-map contract incomplete

**Claim:** After splitting LEVELS into `under` and `rail`, the packet no longer explains how one `_LAYER_RENDERERS` entry supplies two segments that the compositor inserts on opposite sides of the base/price segment.

**Evidence:** [packet:400](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:400) maps a key to one renderer; [packet:424](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:424) says that renderer returns SVG elements only; [packet:455](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:455) requires it to emit separate under/rail segments.

**Smallest fix:** Define a closed renderer result contract, for example `{under: elements, rail: elements}`, and state the compositor’s fixed interleaving order. Make the probe return and assert both parts independently. This does not require a general `LayerSpec`, client state, or Astrology-specific logic.

## New findings introduced by the repair

- **NF-5:** Stale three-group language and inconsistent `180`/`185` ceiling claims remain in current packet sections. These map to REQ-1 and REQ-7.
- **NF-6:** The five-segment correction regressed the previously adequate one-renderer/one-group extension seam. This maps to REQ-8.
- **NF-7:** The packet calls a `<=0.3` coordinate comparison proof of an equality invariant and overstates which cases assert invariant (f). This maps to REQ-5.
- The packet’s `chart top = 661` claim reproduced as 654. The R14 pass/fail result is unchanged.

No newly invented existing production symbol or predecessor path was found. `_LAYER_RENDERERS`, `_LAYER_CONTROLS`, `layers=`, the oracle file, and the PRD evidence path are clearly proposed future surfaces rather than claims that they already exist.

## Helm confirmation items

| # | Result | Evidence |
|---|---|---|
| 1 | **PASS** | Five segments place background, levels-under, candles/NOW, levels-rail, and axis in the same category order as [setup_chart.py:211](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:211) through [setup_chart.py:362](/home/dustin/Projects/cuttingboard/cuttingboard/delivery/setup_chart.py:362). The contradictory prose still requires correction. |
| 2 | **PASS** | Lines remain at true y, every level receives a true-y tick before pruning, displaced labels retain leaders, and dropped labels retain ticks at [packet:482](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:482). |
| 3 | **PASS** | The protected phone block, including `nth-child(10)`, is kept byte-for-byte at [packet:389](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:389), consistent with [PRD-327:410](/home/dustin/Projects/cuttingboard/docs/prd_history/PRD-327.md:410). |
| 4 | **PASS** | The state matrix preserves observed date/time, intended-date truth, safe reason text, and raw tokens only in data attributes at [packet:305](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:305). |
| 5 | **PASS** | Control emission is conditional on a non-empty layered SVG at [packet:433](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:433). |
| 6 | **PASS** | Both LEVELS segments carry the default presentation attribute `display="none"`; CSS-off and unchecked states agree at [packet:428](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:428). |
| 7 | **PASS** | OFF/ON changes computed presentation only; SVG innerHTML, y-domain, prices, permission, grades, and rankings are invariant at [packet:465](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:465). Exact prototype equality evidence still needs the REQ-5 correction. |
| 8 | **PASS** | Candidate calls remain `layers=None` and are governed by byte identity at [packet:561](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:561). |
| 9 | **PASS** | `_render_level_ladder` remains visible, unchanged, and independent of the checkbox at [packet:530](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:530). |
| 10 | **PASS** | No Astrology control, behavior, string, render function, or layer-specific production logic is proposed at [packet:470](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:470). The generic multi-part seam still needs REQ-8 clarification. |
| 11 | **PASS** | R16 is non-vacuous: representative runtime inputs, both sides of the leader threshold, and the existing A1-C embedded SVG are pinned before production modification at [packet:655](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:655). |
| 12 | **PASS** | The PRD-318, 321, 326, 327, 329, 282, 304, 322, and 098 clauses are accurately preserved, narrowed, or superseded at [packet:664](/home/dustin/Projects/cuttingboard/audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md:664). |
| 13 | **PASS** | No previously omitted consumer class, renderer, carrier, schema surface, or end-to-end seam was discovered. The remaining issues are local specification, assertion, and measurement-record defects, not a GOV-2 section 6 boundary reset. |

## Boundary omissions

**None.** The four production chart call sites, transient observation producer and payload projection, red-folder loader boundary, renderer/control path, ladder, fixture/hash/golden surfaces, browser evidence path, and protected phone block remain accounted for.

The incomplete multi-part renderer return contract is a defect within the already identified layer seam. It does not reveal a new consumer class, renderer class, carrier, schema, or end-to-end seam. `DESIGN INCOMPLETE` is therefore not the applicable verdict.

## Helm conflicts and drift

No new conflict with a Helm ruling was found. Proto B remains selected; the ladder remains open; no renderer-side CLOSED inference is introduced; candidate charts stay on their legacy path; no new data, persistence, provider, permission, ranking, or market fact is introduced; and no dead Astrology UI ships.

The packet remains consistent with VISION’s “description, not prediction” principle at [VISION.md:51](/home/dustin/Projects/cuttingboard/VISION.md:51). This design-only packet does not create a new `docs/PROJECT_STATE.md` implementation claim; no new D4 project-state staleness was introduced.

## Packet mutation and blocker

**Yes, findings require packet mutation.** REQ-1, REQ-5, REQ-7, and REQ-8 require local packet corrections. None requires implementation, a new product ruling, scope expansion, or a GOV-2 boundary rebuild.

The packet is not review-clean at `d5624442dfc3bfe85cd6f80571df0ac19961f64f` and must not advance to the design-direction ruling.

The smallest unblocking decision belongs to Dustin/Helm: authorize another bounded packet-only repair for these four local residuals followed by a newly commissioned exact-SHA confirmation, or park/narrow the packet. I do not infer that authority.

## Commands run

```text
git rev-parse HEAD
git diff 955e139..d562444 --stat
git status --short --branch
git merge-base d5624442dfc3bfe85cd6f80571df0ac19961f64f 858147f2057ed967d7d17fbc4a8c2f6cc20bfb71
git diff --check 955e139..d562444
git diff --unified=3 955e139..d562444 -- <packet>
git diff 955e139..d562444 --numstat
git diff 858147f..d562444 --name-status
git log -4 --oneline --decorate
git show d5624442...:<path> | sha256sum
sha256sum <working-tree path>
wc -l <packet/review files>
nl -ba <file> | sed -n '<range>p'
rg -n <targeted patterns> <commissioned files>
rg -n "render_setup_chart_svg\(" cuttingboard tests docs/CALL_SITE_MAP.md
find <scratchpad> <targeted prototype/measurement names>
tail -c 32 <Event-1 record> | od -An -t x1
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c <read-only legacy/layered SVG equality probe>
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c <read-only overflow group/tick/label probe>
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -c <exact-one-EOF-newline probe>
google-chrome --headless=new --no-sandbox --disable-gpu --remote-debugging-port=9333 --user-data-dir=/tmp/codex-d4-sol-review about:blank
node -e <read-only local CDP 390x844 geometry query>
```

The first sandboxed local CDP query failed with `EPERM` on the loopback connection and was rerun with approved local access. One narrow `rg` command had an unmatched quote; it was replaced by narrower searches. The browser process was terminated after the query. Final `git status --short --branch` showed no worktree changes.

---

## Dispatch prompt (verbatim)

```
You are Sol, a commissioned fresh-context independent design reviewer (Adversary seat) for the Cuttingboard repository at /home/dustin/Projects/cuttingboard. Read-only. Do not edit files. Do not implement anything. You have no memory of the authoring session or of the Event-1 run; state that you operated in fresh context and list the commands you ran.

EVENT TYPE: EXACT-CORRECTED-HEAD CONFIRMATION, ATTEMPT 2 (GOV-2 sec2 step 5, sec7 step 3; bounded local repair after attempt 1 per GOV-2 sec6 last paragraph). This is a NARROW confirmation: confirm whether the four attempt-1 residuals (REQ-1, REQ-3, REQ-5, REQ-7) and NF-4 are resolved at the exact repaired head, that the seven items attempt 1 marked RESOLVED remain resolved, and whether the repair introduced any new material boundary omission (GOV-2 sec6) or any new conflict with a Helm ruling.

CONFIRMATION TARGET
- Repaired head: d5624442dfc3bfe85cd6f80571df0ac19961f64f (branch claude/d4-proto-b-levels-design). Prior attempt-1 head: 955e139. Verify with `git rev-parse HEAD`. Verify `git diff 955e139..d562444 --stat` touches only audits/dashboard-d4-material-packet-2026-09/ (the packet, the CODEX_EVENT_1_REVIEW_2026-09-02.md EOF fix, and the new CODEX_EVENT_2_CONFIRMATION_ATTEMPT_1_2026-09-02.md). If HEAD differs, say so and stop.
- Merge base / main: 858147f2057ed967d7d17fbc4a8c2f6cc20bfb71.
- Packet: audits/dashboard-d4-material-packet-2026-09/DASHBOARD_D4_MATERIAL_PACKET_2026-09-02.md (corrected revision; REVIEW RECORD at the end lists dispositions).
- Event-1 record: audits/dashboard-d4-material-packet-2026-09/CODEX_EVENT_1_REVIEW_2026-09-02.md (REJECT at 74c915f). Attempt-1 record: audits/dashboard-d4-material-packet-2026-09/CODEX_EVENT_2_CONFIRMATION_ATTEMPT_1_2026-09-02.md (NOT CONFIRMED - 4 residuals at 955e139; read its Residuals section: those are the items to confirm).
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
# D4 Packet Confirmation - Sol / Codex (EXACT-CORRECTED-HEAD CONFIRMATION, ATTEMPT 2, narrow)
**Confirmed head:** <sha>  **Prior attempt-1 head:** 955e139  **Event-1 head:** 74c915f  **Merge base:** 858147f  **Date:** 2026-09-02
**Fresh-context statement:** <one line: no prior session state; commands run>
**Verdict:** CONFIRMED-CLEAN | NOT CONFIRMED - <n> residual(s) | DESIGN INCOMPLETE
## Item table (REQ-1..REQ-8, REC-1..REC-3: Disposition | Evidence)
## Residuals (each: id, claim, evidence, smallest fix; or "none")
## New findings from the correction (or "none")
## Boundary omissions (or "none")
## Blockers for Helm (or "none beyond D-1..D-8")

ATTEMPT-2 SPECIFIC CHECKS (verify against the repaired packet text and the cited surfaces)
- REQ-1: five paint segments (base/under, levels/under, base/price, levels/rail, base/axis) versus setup_chart.py:211-362 legacy order (bg, bands, Tier-3 lines, Tier-2 lines, candles, NOW line, NOW tag, rail, axis). Is the interleaving now preserved for every legacy category? Are both LEVELS segments covered by one selector and default-hidden?
- REQ-3: no visible raw reason token (data-raw-reason carrier + operator-safe fallback); formatter described as date, middle dot, time; _ORB_STATE_DISPLAY cited at 186-192 and _spy_orb_summary at 229-239 (verify).
- REQ-5: ticks emitted for every level from the complete list (invariant (g)); invariant (f) stated and asserted; the prototype's fitted-scale caveat is stated honestly; section 10's overflow row (11 ticks, 7 labels, 4 dropped, marker) is internally consistent. You may inspect the scratch generator at /tmp/claude-1000/-home-dustin-Projects-cuttingboard/39db22ac-980f-483c-bfb8-49a50ecb4b93/scratchpad/gen_levels.py and its *_stats.json outputs read-only.
- REQ-7: the inert nth-child(10) phone rule at dashboard_renderer.py:1097 is now KEPT; R15 and PRD-327 R10 remain consistent; LOC estimate adjusted.
- NF-4: CODEX_EVENT_1_REVIEW_2026-09-02.md ends with exactly one newline.
- Items REQ-2, REQ-4, REQ-6, REQ-8, REC-1, REC-2, REC-3: confirm still RESOLVED (no regression from the repair).

HELM CONFIRMATION ITEMS (answer each 1-13 explicitly, PASS / FAIL with one line of evidence)
1. SVG paint segmentation preserves legacy candle/level ordering.
2. Rail labels/ticks remain true-price anchored and dropped labels retain ticks.
3. No protected PRD-327 phone-block behavior is altered.
4. STALE/header state table preserves date/time truth and no raw reason token leaks.
5. LEVELS control is emitted only when a layered SVG exists.
6. LEVELS OFF is genuinely equivalent to the intended clean base state.
7. LEVELS ON changes presentation only, never y-scale or market facts.
8. Candidate charts remain on the legacy byte-preserving path.
9. Existing SPY ladder remains visible and independent of LEVELS.
10. Future Astrology seam is structural only: no visible Astrology control, no Astrology behavior, no Astrology-specific production logic beyond a generic extension seam.
11. R11 frozen-byte oracle is real and non-vacuous.
12. All predecessor supersessions/preservations are accurately stated.
13. No boundary omission remains.
Also state explicitly whether any finding requires packet mutation.
```
