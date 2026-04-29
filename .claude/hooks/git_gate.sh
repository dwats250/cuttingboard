#!/usr/bin/env bash
# PreToolUse/Bash — blocks git commit/push; requires APPROVE COMMIT in session transcript.
# Also runs dirty repo guard (R5) before reporting approval status.

set -euo pipefail

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_name', ''))
")

COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('command', ''))
")

# Ensure GitNexus DB is writable so MCP server FTS indexes succeed
chmod 666 .gitnexus/lbug 2>/dev/null || true

# Only act on Bash tool
[[ "$TOOL_NAME" == "Bash" ]] || exit 0

# Only act on git commit or git push
if ! echo "$COMMAND" | grep -qE 'git (commit|push)'; then
  exit 0
fi

TRANSCRIPT_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('transcript_path', ''))
")

# --- R5: Dirty Repo Guard ---
ACTIVE_PRD="none"
if [[ -f ".claude/state/active_prd.txt" && -s ".claude/state/active_prd.txt" ]]; then
  ACTIVE_PRD=$(tr -d '[:space:]' < ".claude/state/active_prd.txt")
fi

DIRTY_OUTPUT=$(git status --short 2>/dev/null || true)
if [[ -n "$DIRTY_OUTPUT" && "$ACTIVE_PRD" != "none" ]]; then
  PRD_FILE="docs/prd_history/${ACTIVE_PRD}.md"
  if [[ -f "$PRD_FILE" ]]; then
    UNRELATED=$(python3 << PYEOF
import re, sys

prd_path = "$PRD_FILE"
dirty_output = """$DIRTY_OUTPUT"""

# Extract FILES section from PRD
with open(prd_path) as f:
    content = f.read()

files_section = re.search(r'\nFILES\n(.*?)\n(?:[A-Z])', content, re.DOTALL)
scoped_files = set()
if files_section:
    for line in files_section.group(1).splitlines():
        line = line.strip()
        if line and line[0] in ('A', 'M', 'D') and len(line) > 2:
            scoped_files.add(line[1:].strip())

unrelated = []
for line in dirty_output.splitlines():
    line = line.strip()
    if not line:
        continue
    parts = line.split(None, 1)
    if len(parts) < 2:
        continue
    fpath = parts[1].strip()
    if not any(fpath == s or fpath.endswith(s) or s.endswith(fpath) for s in scoped_files):
        unrelated.append(line)

for u in unrelated:
    print(u)
PYEOF
    )
    if [[ -n "$UNRELATED" ]]; then
      echo "[git_gate] DIRTY REPO: unrelated files must be resolved before requesting commit/push approval:" >&2
      echo "$UNRELATED" >&2
      echo "[git_gate] BLOCKED: resolve unrelated dirty/untracked files first." >&2
      exit 1
    fi
  fi
fi

# --- R1: Approval Check ---
APPROVED=0
if [[ -n "$TRANSCRIPT_PATH" && -f "$TRANSCRIPT_PATH" ]]; then
  APPROVED=$(python3 << PYEOF
import json, sys

transcript_path = "$TRANSCRIPT_PATH"
approved = 0
try:
    with open(transcript_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get('role') != 'user':
                continue
            content = msg.get('content', '')
            if isinstance(content, str):
                if 'APPROVE COMMIT' in content:
                    approved = 1
                    break
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and 'APPROVE COMMIT' in str(part.get('text', '')):
                        approved = 1
                        break
                if approved:
                    break
except Exception:
    pass
print(approved)
PYEOF
  )
fi

if [[ "$APPROVED" == "1" ]]; then
  echo "[git_gate] APPROVED: APPROVE COMMIT found in session transcript." >&2
  exit 0
fi

echo "[git_gate] BLOCKED: git commit/push requires explicit approval." >&2
echo "[git_gate] To approve, type exactly: APPROVE COMMIT" >&2
exit 1
