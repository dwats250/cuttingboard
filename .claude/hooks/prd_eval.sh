#!/usr/bin/env bash
# Fires on UserPromptSubmit.
# 1. Detects PRD documents and injects evaluation instructions (+ sequencing note).
# 2. Detects implementation requests for non-sequential PRDs and injects a sequencing gate.
set -euo pipefail

INPUT=$(cat)

PROMPT=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.argv[1])
    print(d.get('prompt') or d.get('message') or '')
except Exception:
    print('')
" "$INPUT" 2>/dev/null || true)

if [ -z "$PROMPT" ]; then
    exit 0
fi

REGISTRY="docs/PRD_REGISTRY.md"

# ---------------------------------------------------------------------------
# Detect PRD document body: PRD-NNN identifier + at least 4 section keywords
# ---------------------------------------------------------------------------
HAS_PRD_NUM=$(echo "$PROMPT" | grep -cE 'PRD-[0-9]+' 2>/dev/null; true)
HAS_SECTIONS=$(echo "$PROMPT" | grep -cE '(^|\s)(STATUS|GOAL|SCOPE|REQUIREMENTS|FILES|DATA FLOW|FAIL CONDITIONS|VALIDATION|ACCEPTANCE CRITERIA|COMMIT PLAN)(\s|$)' 2>/dev/null; true)

HAS_PRD_NUM=${HAS_PRD_NUM:-0}
HAS_SECTIONS=${HAS_SECTIONS:-0}

IS_PRD_BODY=0
if [ "${HAS_PRD_NUM}" -gt 0 ] 2>/dev/null && [ "${HAS_SECTIONS}" -ge 4 ] 2>/dev/null; then
    IS_PRD_BODY=1
fi

# ---------------------------------------------------------------------------
# Detect implementation request: verb + PRD-NNN without a PRD body
# ---------------------------------------------------------------------------
IS_IMPL_REQUEST=0
if [ "${IS_PRD_BODY}" -eq 0 ] && [ "${HAS_PRD_NUM}" -gt 0 ]; then
    HAS_IMPL_VERB=$(echo "$PROMPT" | grep -ciE '(implement|build|code|start|begin|write)\s.{0,30}PRD-[0-9]+|PRD-[0-9]+.{0,30}\s(implement|build|code|start|begin)' 2>/dev/null || true)
    HAS_IMPL_VERB=${HAS_IMPL_VERB:-0}
    if [ "${HAS_IMPL_VERB}" -gt 0 ] 2>/dev/null; then
        IS_IMPL_REQUEST=1
    fi
fi

# ---------------------------------------------------------------------------
# Sequencing check
#
# For PRD body review: always report if non-sequential (skip phrases NOT applied —
# the PRD text itself contains words like "DRAFT" and "SCOPE" that would false-positive).
# For implementation requests: skip phrases suppress the gate so the user can
# declare intent inline ("batch workflow", "deferred", etc.).
# ---------------------------------------------------------------------------
SEQUENCE_WARNING=""
REGISTRY_GAP=""

# ---------------------------------------------------------------------------
# Registry completeness check: flag prd_history/*.md files with no registry row
# ---------------------------------------------------------------------------
if [ -f "$REGISTRY" ] && [ "${HAS_PRD_NUM}" -gt 0 ]; then
    REGISTRY_GAP=$(python3 - "$REGISTRY" <<'PYEOF'
import sys, re, os, glob

registry_path = sys.argv[1]
prd_dir = os.path.join(os.path.dirname(registry_path), "prd_history")

file_stems = set()
for f in glob.glob(os.path.join(prd_dir, "PRD-*.md")):
    name = os.path.basename(f)
    # Review and adjudication artifacts are not PRDs and must not have
    # registry rows (CLAUDE.md § Review artifact discipline).
    if ".review." in name or name.endswith(".adjudication.md"):
        continue
    file_stems.add(name.replace(".md", ""))

try:
    text = open(registry_path, encoding="utf-8").read()
except OSError:
    sys.exit(0)

# A file is registered if its stem appears anywhere in any registry table row
# (catches variant ID formats like "PRD-012 (cleanup)" and "PRD-053 PATCH")
missing = []
for stem in sorted(file_stems):
    if not any(stem in line for line in text.splitlines() if line.startswith("|")):
        missing.append(stem)

if not missing:
    sys.exit(0)

lines = ["REGISTRY GAP — prd_history files with no registry row:"]
for m in missing:
    lines.append(f"  {m}.md")
lines.append("Add a registry row for each before saving new PRDs.")
print("\n".join(lines))
PYEOF
    )
fi

if [ -f "$REGISTRY" ] && [ "${HAS_PRD_NUM}" -gt 0 ]; then
    SEQUENCE_WARNING=$(python3 - "$PROMPT" "$REGISTRY" "$IS_PRD_BODY" <<'PYEOF'
import sys, re

prompt       = sys.argv[1]
registry_path = sys.argv[2]
is_prd_body  = sys.argv[3] == "1"

submitted = sorted(set(int(n) for n in re.findall(r'PRD-(\d+)', prompt)))
if not submitted:
    sys.exit(0)

try:
    text = open(registry_path, encoding="utf-8").read()
except OSError:
    sys.exit(0)

in_progress = []
for line in text.splitlines():
    if "IN PROGRESS" in line:
        nums = re.findall(r'PRD-(\d+)', line)
        in_progress.extend(int(n) for n in nums)
in_progress = sorted(set(in_progress))

if not in_progress:
    sys.exit(0)

blocking = []
for sub in submitted:
    blockers = [ip for ip in in_progress if ip < sub]
    if blockers:
        blocking.append((sub, blockers))

if not blocking:
    sys.exit(0)

# For implementation requests only: check for an explicit skip reason in the prompt.
# PRD body review always shows the note (the PRD text contains too many false-positive words).
if not is_prd_body:
    skip_phrases = re.compile(
        r'(intentional|batch|deferred|defer|skipping|jumping ahead|not yet implement'
        r'|before.*complet|after.*complet|codex|token.*reset|reset.*token|implement.*later'
        r'|reason.*for|because)',
        re.IGNORECASE,
    )
    if skip_phrases.search(prompt):
        sys.exit(0)

lines = ["SEQUENCING GATE — NON-SEQUENTIAL PRD DETECTED"]
for sub, blockers in blocking:
    blocker_str = ", ".join(f"PRD-{b}" for b in blockers)
    verb = "is" if len(blockers) == 1 else "are"
    lines.append(
        f"PRD-{sub} is referenced but {blocker_str} {verb} still "
        f"IN PROGRESS with no commit."
    )
lines.append("")
if is_prd_body:
    lines.append(
        "Include a sequencing note in the Critical Problems section. "
        "If the user has already stated a reason (e.g. batch workflow, deferred implementation), "
        "downgrade to an informational note rather than a blocking problem."
    )
else:
    lines.append(
        "Before proceeding: confirm with the user that skipping ahead is intentional "
        "and ask them to state the reason. Do not begin implementation until the user "
        "provides a reason or clears the lower-numbered PRDs."
    )
print("\n".join(lines))
PYEOF
    )
fi

# ---------------------------------------------------------------------------
# Emit context
# ---------------------------------------------------------------------------
python3 - "$IS_PRD_BODY" "$IS_IMPL_REQUEST" "$SEQUENCE_WARNING" "$REGISTRY_GAP" <<'PYEOF'
import json, sys

is_prd_body     = sys.argv[1] == "1"
is_impl_request = sys.argv[2] == "1"
seq_warning     = sys.argv[3].strip()
registry_gap    = sys.argv[4].strip()

parts = []

if registry_gap:
    parts.append(registry_gap)

if seq_warning:
    parts.append(seq_warning)

if is_prd_body:
    parts.append("""SYSTEM INSTRUCTION — PRD REVIEW MODE ACTIVE

The user has submitted a PRD. Perform a complete evaluation before doing anything else. Read the relevant codebase files to verify all field names, module contracts, constants, and file paths claimed in the PRD actually exist as described.

Structure your response exactly as follows:

## Strengths
Bullet list of what the PRD gets right: scope control, requirement clarity, binary FAIL conditions, data flow coherence, accurate field/module references.

## Cohesiveness
Assess whether GOAL → SCOPE → REQUIREMENTS → FAIL CONDITIONS form a tight, non-contradictory chain. Call out any internal gaps, ambiguities, or contradictions.

## Critical Problems
For each problem found, use this format:
- **Problem:** [one-sentence statement]
- **Root cause:** [specific cause — wrong field name, missing file, undefined behavior, scope violation, etc.]
- **Fix:** [exact change to make]

Cross-check every field name, constant, file path, and module reference against the actual codebase before listing as correct.

## Revised PRD
A complete, corrected PRD. Same section order as the original. All issues from Critical Problems resolved. Do not add scope beyond what the original intended.

---
Do not begin implementation until the user explicitly approves the revised PRD.""")

elif is_impl_request:
    parts.append("""SYSTEM INSTRUCTION — PRD IMPLEMENTATION REQUEST DETECTED

Before writing any code: read docs/PROJECT_STATE.md and the target PRD file. Confirm the requested PRD is the correct next sequential PRD to implement. If it is not, and no explicit skip reason was provided, stop and ask the user to confirm before proceeding.""")

if not parts:
    sys.exit(0)

ctx = "\n\n---\n\n".join(parts)
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": ctx
    }
}))
PYEOF
