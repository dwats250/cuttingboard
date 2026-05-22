# Recon Brief — Gap-Down Permission Gating ↔ PRD-150 Coupling

**For:** Codex, invoked by Claude Code
**Question:** Does the Gap-Down Permission Gating PRD have logical dependencies on PRD-150 (Five-Tier Symbol Classification System)?
**Output:** Single markdown file at `audits/recon-2026-05-XX/gap-down-prd150-coupling.md`
**Scope:** Read-only. Structured analysis. No code changes, no PRD modifications.

---

## Context

VISION.md Phase 1 step 3 calls for implementing Gap-Down Permission Gating. VISION.md also notes that the intraday state classification PRD "needs review against this vision before building," and PRD-150 (Five-Tier Symbol Classification System) appears to be that PRD.

Before committing to Gap-Down implementation order, we need to know whether Gap-Down's logic depends on symbol classification tiers as defined or implied by PRD-150. Two outcomes drive different sequences:

- **Independent** → Gap-Down can be implemented first; PRD-150 vision review proceeds in parallel or after
- **Dependent** → PRD-150 needs vision review and stabilization before Gap-Down can be implemented against its definitions

This recon answers that question and nothing else. Do not propose implementation paths, do not redesign either PRD, do not assess PRD quality. The question is narrow on purpose.

---

## Input documents

Read these in scoped fashion — don't load full content into context unless required:

1. **Gap-Down Permission Gating PRD** — locate via `docs/PRD_REGISTRY.md`. Likely numbered in the PRD-100s or PRD-140s range. If multiple PRD files reference "gap-down" or "permission gating," identify all and treat together.
2. **PRD-150** — `docs/prd_history/PRD-150.md` (Five-Tier Symbol Classification System)
3. **PRD-150 Codex review file** — `docs/prd_history/PRD-150.review.codex.md` (existence noted in audit)
4. **VISION.md** — for the principles either PRD must adhere to
5. **`cuttingboard/universe.py`** — current symbol universe definition; reference point for what symbol classification looks like today

---

## Deliverable structure

Produce `audits/recon-2026-05-XX/gap-down-prd150-coupling.md` with the following sections:

### 1. Document identification

Confirm the file paths for each PRD examined. If Gap-Down Permission Gating spans multiple PRDs or patches, list them. If you can't locate the Gap-Down PRD, state so plainly and stop — surface for human direction rather than guessing.

### 2. Gap-Down summary (3-5 sentences)

In your own words: what does Gap-Down Permission Gating do? What inputs does it consume? What outputs or gate decisions does it produce? Where in the pipeline does it sit?

### 3. PRD-150 summary (3-5 sentences)

In your own words: what does the Five-Tier Symbol Classification System define? What tiers? What governs tier assignment? What downstream consumers does it specify or imply?

### 4. Coupling analysis

The core question. For each of the following potential coupling points, classify as `DEPENDENT`, `INDEPENDENT`, or `AMBIGUOUS`:

- **Symbol tier references**: Does Gap-Down's gating logic reference symbol classification tiers (CORE, CONDITIONAL, SIGNAL, MACRO, EXCLUDED or any subset)?
- **Threshold tiering**: Does Gap-Down apply different gap thresholds, lookback windows, or gating rules to different symbol categories that PRD-150 would define?
- **Universe scope**: Does Gap-Down depend on the symbol universe definition in ways PRD-150 might change?
- **Shared modules**: Do both PRDs propose changes to the same module(s) — e.g., `universe.py`, `qualification.py`, `regime.py`, or `runtime.py`?
- **Sidecar coupling**: Does either PRD propose a sidecar that the other consumes?
- **State/data structure overlap**: Does either PRD introduce data structures, fields, or contracts the other relies on?

For each `DEPENDENT` or `AMBIGUOUS` finding, cite the specific lines or sections in the PRDs that show the coupling.

### 5. Verdict

A single classification:

- **INDEPENDENT** — Gap-Down can be implemented before PRD-150 vision review with no foreseeable rework risk
- **WEAKLY DEPENDENT** — Some coupling exists but Gap-Down can be implemented against current symbol universe assumptions; PRD-150 may later refactor but won't invalidate Gap-Down logic
- **STRONGLY DEPENDENT** — Gap-Down's logic substantively depends on symbol tier definitions; implementing before PRD-150 stabilizes creates real rework risk
- **CANNOT DETERMINE** — PRD content is ambiguous on the coupling question; human review needed

If the verdict is `WEAKLY DEPENDENT` or stronger, identify which specific elements of PRD-150 would need to stabilize before Gap-Down implementation is safe.

### 6. Recommended sequence

Based on the verdict, recommend one of:

- **A — Implement Gap-Down first, vision-review PRD-150 in parallel or after**
- **B — Implement Gap-Down first but defer the coupling-point logic until PRD-150 stabilizes** (specify which elements to defer)
- **C — Vision-review PRD-150 first, then implement Gap-Down against stabilized definitions**

This recommendation is informational. Dustin and Claude (project lead) make the final call.

### 7. Honest limits

Document what you could not determine, what required interpretation, and where the analysis has uncertainty. If a PRD is ambiguous about its scope or consumers, state so plainly.

---

## Constraints

- **Read-only.** No code changes, no PRD modifications, no commits beyond the recon output file.
- **No interpretation beyond what's asked.** This is a coupling analysis, not a PRD redesign or quality review.
- **Cite specifics.** Coupling findings should reference PRD line ranges or section headings.
- **Honesty about limits.** If you can't determine coupling for a specific point, say `AMBIGUOUS` and explain why rather than guessing.
- **Plain prose.** No marketing language, no hedging beyond what's warranted.

## When complete

Commit the recon file to the audits directory. Notify Claude Code (or Dustin directly) that the recon is ready for review. Do not proceed to Gap-Down implementation or PRD-150 vision review based on this output — the recon informs the decision, it does not make it.
