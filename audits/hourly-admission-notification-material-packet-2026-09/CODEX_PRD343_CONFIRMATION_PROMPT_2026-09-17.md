# Codex exact-corrected-head confirmation prompt -- PRD-343

```
Owner ruling 2026-09-17: exact-head evidence required. Invocation: cbagent launch-codex (read-only, model_reasoning_effort=high). Corrected PRD revision: b7fa8f5a6040e88af422e77cb4eaa8043320b070 (HEAD is exactly one docs-only commit ahead that adds only this prompt file).
```

---

You are Sol, a commissioned fresh-context independent reviewer (Adversary seat) for the Cuttingboard repository at the working directory you were launched in. Read-only. No edits, no implementation. You have no memory of the earlier PRD review; read its committed record.

TARGET
- PRD: docs/prd_history/PRD-343.md at b7fa8f5a6040e88af422e77cb4eaa8043320b070. Verify `git rev-parse HEAD~1` equals it.
- Prior review record: docs/prd_history/PRD-343.review.codex.md (7 REQUIRED, 3 RECOMMENDED against 52c9f513).
- Binding design: audits/hourly-admission-notification-material-packet-2026-09/HOURLY_ADMISSION_NOTIFICATION_MATERIAL_PACKET_2026-09-17.md (sections 0, 5, 6, 9).
- Effort: HIGH. This is the ONE exact-corrected-head confirmation. If you find a new substantive defect, say STOP and classify it; a purely wording/recording residual is reported as such.

TASK
1. For REQ-1..7 and REC-1..3 of the prior review: CONFIRMED / NOT CONFIRMED (smallest residual) with the PRD line and repository file:line you checked. For REQ-2 run `/home/dustin/Projects/cuttingboard/.venv/bin/python tools/validate_prd_registry.py --skip-commit-resolvability` and `git diff --stat 0921fd9d..HEAD~1 -- docs/prd_index.json` (must be a small additive diff, no encoding churn). For REQ-7 report `wc -l docs/prd_history/PRD-343.md`.
2. Confirm the compressed PRD did not weaken: FILES (11 files), the no-hoist boundary, the canonical-only admission (R4), the refusal artifact assertions (R5/R7), the stateful clock harness (R7), the ceilings (45/6/360), and the module-local fixture rule (R9). Cite any weakening.
3. Confirm R1-R9 still each carry exactly one binary FAIL line and that DATA FLOW / FAIL CONDITIONS / VALIDATION do not restate requirements.
4. New findings, or "none".

OUTPUT FORMAT (markdown, plain ASCII only; no em-dashes, smart quotes, arrows, or emoji)
# PRD-343 exact-corrected-head confirmation - Sol / Codex
- CONFIRMED REVISION: <sha of HEAD~1>
- VERDICT: CONFIRMED-CLEAN | NOT CONFIRMED
- DISPOSITIONS: REQ-1..7, REC-1..3, one line each
- WEAKENING CHECK: one line per item in task 2
- NEW FINDINGS: numbered or "none"
- PROPOSED GATE A CEILINGS: production LOC per file, test LOC, FILES (repeat or revise)
- RATIONALE: short
