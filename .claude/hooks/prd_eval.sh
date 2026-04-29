#!/usr/bin/env bash
# Fires on UserPromptSubmit. Detects PRD documents and injects evaluation instructions.
set -euo pipefail

INPUT=$(cat)

PROMPT=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.argv[1])
    # UserPromptSubmit may use 'prompt' or 'message' key
    print(d.get('prompt') or d.get('message') or '')
except Exception:
    print('')
" "$INPUT" 2>/dev/null || true)

if [ -z "$PROMPT" ]; then
    exit 0
fi

# Detect PRD: requires PRD-NNN identifier AND at least 4 structural section keywords
HAS_PRD_NUM=$(echo "$PROMPT" | grep -cE 'PRD-[0-9]+' 2>/dev/null; true)
HAS_SECTIONS=$(echo "$PROMPT" | grep -cE '(^|\s)(STATUS|GOAL|SCOPE|REQUIREMENTS|FILES|DATA FLOW|FAIL CONDITIONS|VALIDATION|ACCEPTANCE CRITERIA|COMMIT PLAN)(\s|$)' 2>/dev/null; true)

HAS_PRD_NUM=${HAS_PRD_NUM:-0}
HAS_SECTIONS=${HAS_SECTIONS:-0}

if [ "${HAS_PRD_NUM}" -gt 0 ] 2>/dev/null && [ "${HAS_SECTIONS}" -ge 4 ] 2>/dev/null; then
    python3 -c "
import json

ctx = '''SYSTEM INSTRUCTION — PRD REVIEW MODE ACTIVE

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
Do not begin implementation until the user explicitly approves the revised PRD.'''

print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'UserPromptSubmit',
        'additionalContext': ctx
    }
}))
"
fi
