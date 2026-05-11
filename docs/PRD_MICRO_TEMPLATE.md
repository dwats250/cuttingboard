# PRD-NNN — <Title>

> **Use only if the change meets all micro-PRD eligibility criteria in
> CLAUDE.md § Micro-PRD eligibility. When in doubt, use the full
> template at `docs/PRD_TEMPLATE.md`.**

STATUS
PROPOSED

LANE
MICRO
<!-- Micro template is locked to LANE: MICRO. If your change touches
any behavior surface enumerated in docs/PRD_PROCESS.md § MICRO
Eligibility Safety Net, switch to docs/PRD_TEMPLATE.md and declare
the appropriate lane. -->

GOAL
<One paragraph: what this changes and why. State the observed problem
or process gap concretely. No speculative motivation.>

SCOPE
- <Bullet 1: exact change>
- <Bullet 2: exact change>
- <Track this PRD in registry/state per existing convention.>

FILES
Modified:
- <path>
- `docs/PRD_REGISTRY.md` (PRD-NNN row)
- `docs/PROJECT_STATE.md` (active PRD pointer)

New:
- `docs/prd_history/PRD-NNN.md`
- <other new files, if any>

(No files outside this list may be modified by this PRD's commit.)

REQUIREMENTS

R1 — <one-sentence requirement>
FAIL: <observable, binary failure condition>

R2 — <one-sentence requirement>
FAIL: <observable, binary failure condition>

<At least one Rn with a deterministic FAIL line is required. Add as
many as the change warrants — typically 2–5 for a micro-PRD.>

VALIDATION

Diff scope guard (must return no output):
```
git diff --name-only HEAD~1 HEAD | grep -vE '<allowed-paths-regex>'
```

<Other targeted checks: grep for required content, run targeted
tests if executable code changed, etc.>

Test suite (only when executable code changes):
```
python3 -m pytest tests/test_<module>.py -q
```

Run the full suite once before pre-commit review per
CLAUDE.md § Test-suite discipline.

COMMIT PLAN
1. <Step 1: exact action>
2. <Step 2: exact action>
3. Add PRD-NNN IN PROGRESS row to `docs/PRD_REGISTRY.md`.
4. Update `docs/PROJECT_STATE.md` (active PRD → PRD-NNN).
5. Add `docs/prd_history/PRD-NNN.md`.
6. Run validation.
7. Commit: `PRD-NNN: <short imperative summary>`
8. Bookkeeping commit: promote PRD-NNN to COMPLETE with the merge
   commit hash; set PROJECT_STATE active PRD → none.
