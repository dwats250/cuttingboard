# F1 estimation-rule graduation -- GOV-2 Codex packet review + exact-head confirmation

Independent GOV-2 upstream MATERIAL-packet review and exact-corrected-head
confirmation for the F1 estimation-rule graduation (the `docs/PRD_PROCESS.md`
`## Binding MAX EXPECTED DELTA` addition on branch
`governance/f1-estimation-rule-graduation`, change-head
`4452deb4babc9d9bba9607d69dd041bc6eaa2750`; DRAFT governance PR #233).

Reviewer: Codex (codex-cli 0.146.0), invoked
`codex exec -s read-only -c model_reasoning_effort=medium` (sandboxed
read-only, prompt via stdin, verdict from stdout). Fresh context; not the change
author or its Fable wording-reviewer. Artifact written by Claude Code from
captured stdout; Codex wrote nothing into the repo tree.

**Upstream MATERIAL packet:** the accepted Engineering Health Packet
(`audits/reconciliation-2026-08/ENGINEERING_HEALTH_PACKET_2026-08-08.md`),
owner-designated for F1 ONLY per Dustin's 2026-08-08 ruling (recorded on PR
#233). The review's subject is that packet, the proposed change, and the
repository surfaces -- not any other review's prose.

## 1. Packet review -- reviewed change-head `4452deb`

**VERDICT: ACCEPT** -- zero required corrections, zero recommended.

Codex's findings (from captured stdout):
- **Upstream-packet adequacy:** the F-1 packet adequately grounds this narrowly
  bounded governance change -- it records the recurring evidence ("2 of last 2
  MATERIAL PRDs"), classifies it as systemic-process friction, specifies
  graduation into `PRD_PROCESS`, and keeps adoption owner-held
  (ENGINEERING_HEALTH_PACKET_2026-08-08.md:46, :64-66, :104-115, :160-165).
- **Fidelity / no over-reach:** the change is exactly one prose-only addition to
  `docs/PRD_PROCESS.md`; it introduces estimation discipline only, retains
  Dustin's sole Gate-A authority, adds no gate/artifact/reviewer/sequence step,
  and leaves stop-and-renew intact (docs/PRD_PROCESS.md:650-685).
- **Evidence correctness:** PRD-288 amended 195->325 and explicitly excludes
  test LOC; PRD-289 records 300->525, the same net-production metric, and the
  repeated validation-surface undercount (PRD-288.md:43-70, :650-659;
  PRD-289.md:40-63, :102-116). So "test LOC stays outside the net-production-LOC
  metric" is accurate.
- **CI-safety:** no CI-bound literal touched -- the `SECOND-MODEL:` sentence and
  the `PRD-NNN.review.<model>.md` filename rule remain elsewhere, and
  `tools/validate_prd_registry.py` is unchanged and does not parse this prose
  (docs/PRD_PROCESS.md:271-294; validate_prd_registry.py:573-609).
- **Placement:** directly after the existing binding-ceiling / stop-and-renew
  rule -- consistent and non-duplicative.
- Reviewed change-head SHA: `4452deb4babc9d9bba9607d69dd041bc6eaa2750`.

## 2. Correction cycle

None required (ACCEPT with zero corrections). The reviewed head is the final
head; no post-review amendment was made.

## 3. Exact-corrected-head confirmation -- confirmed head `4452deb`

Narrow GOV-2 confirmation (reads the head + the prior findings list; not a fresh
review). Run explicitly to honor the owner's step 4 even though corrections were
zero.

**VERDICT: CONFIRMED** -- head `4452deb` is the accepted exact head; GOV-2
review-clean for the design-direction / Stage-0 step. Codex's justification:
`git diff --name-status main 4452deb` returns exactly `M docs/PRD_PROCESS.md`
(a prose-only addition); the branch ref resolves to this same commit; ACCEPT had
zero required corrections, so no post-review amendment was needed; the addition
governs estimation discipline only and expressly leaves Gate A authority, review
gates, and the GOV-2 sequence unchanged.

## Disposition

GOV-2 upstream sequence complete for F1: owner-designated upstream packet
(Engineering Health Packet, F1-only) -> independent Codex packet review (ACCEPT,
zero corrections) -> exact-head confirmation (CONFIRMED @ `4452deb`). Per the
owner's ruling the change now returns for the **design-direction / Stage-0 PRD
step**. This artifact authorizes nothing downstream: no PRD number is allocated,
no Gate A is granted, PR #233 is not merged. When the Stage-0 PRD number is
allocated, this artifact is the change's Codex packet-review record and may be
referenced from / renamed into the `docs/prd_history/PRD-NNN.review.codex.md`
slot.
