PRD-NNN — [Title]

STATUS
IN PROGRESS

CLASS
[GOVERNANCE | SIDECAR | CONSUMER | EXECUTION | CONTRACT | INFRA]
[Append "+ PATCH" overlay if this PRD corrects a defect in a prior PRD;
include a ROOT CAUSE section below FILES.]

WHY NOW
[One sentence. Why this PRD exists at this point in the system's
evolution. Sequencing rationale, not feature description.]

MAX EXPECTED DELTA
[Binding ceiling — production LOC, file count, or other measurable
bound. Exceeding this MUST stop implementation, amend the PRD with a
revised ceiling and reason, and re-trigger review per the CLASS matrix
in `docs/PRD_PROCESS.md`.]

GOAL
[One sentence. What this PRD delivers and why.]

SCOPE
- [Bullet list of what is included]

OUT OF SCOPE
- [Bullet list of what is explicitly excluded]

FILES
A/M/D path/to/file.py
A/M/D path/to/file.py

CHANGE SURFACE
[Optional. Mandatory iff (i) the CLASS default stability tier is T0 or
T1, OR (ii) any FILES entry matches HIGH-RISK FILES for this CLASS in
the matrix in `docs/PRD_PROCESS.md`. For each constrained file, state
HOW deeply it may change, e.g. "append-only section render", "no
signature changes", "constants only".]

REQUIREMENTS

R1 — [Requirement Name]
[Deterministic description of what must be true.]

FAIL: [Observable, binary failure condition.]

R2 — [Requirement Name]
[Deterministic description of what must be true.]

FAIL: [Observable, binary failure condition.]

DATA FLOW
[source] → [transform] → [output]
[source] → [transform] → [output]

FAIL CONDITIONS
- [List all binary failure conditions across all requirements]
- [Each line is pass/fail observable]

VALIDATION
Manual:
- [Step-by-step verification procedure]
- [Each step has a binary expected result]
