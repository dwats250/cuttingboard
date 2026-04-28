#!/usr/bin/env bash
# PreToolUse/Write + PreToolUse/Edit
# Blocks writes to protected paths unless explicitly listed in the active PRD FILES section.

set -euo pipefail

INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', ''))
")

[[ -n "$FILE_PATH" ]] || exit 0

# --- Protected pattern check ---
is_protected() {
  local p="$1"
  local base
  base=$(basename "$p")
  [[ "$base" == ".env" ]]             && return 0
  [[ "$base" == .env.* ]]             && return 0
  [[ "$p" == .git/* ]]                && return 0
  [[ "$p" == */.git/* ]]              && return 0
  [[ "$base" == *.lock ]]             && return 0
  [[ "$p" == .github/workflows/* ]]   && return 0
  [[ "$base" == secrets* ]]           && return 0
  return 1
}

is_protected "$FILE_PATH" || exit 0

# --- Protected: check active PRD ---
STATE_FILE=".claude/state/active_prd.txt"

if [[ ! -f "$STATE_FILE" || ! -s "$STATE_FILE" ]]; then
  echo "[protect_files] BLOCKED: '$FILE_PATH' is protected. active_prd.txt is missing or empty — failing closed." >&2
  exit 1
fi

ACTIVE_PRD=$(tr -d '[:space:]' < "$STATE_FILE")
PRD_FILE="docs/prd_history/${ACTIVE_PRD}.md"

if [[ ! -f "$PRD_FILE" ]]; then
  echo "[protect_files] BLOCKED: '$FILE_PATH' is protected. PRD file not found: $PRD_FILE" >&2
  exit 1
fi

# Extract FILES section and check for this path
LISTED=$(python3 << PYEOF
import re, sys

prd_path = "$PRD_FILE"
target = "$FILE_PATH"

with open(prd_path) as f:
    content = f.read()

files_section = re.search(r'\nFILES\n(.*?)\n(?:[A-Z])', content, re.DOTALL)
if not files_section:
    print("0")
    sys.exit()

for line in files_section.group(1).splitlines():
    line = line.strip()
    if not line or line[0] not in ('A', 'M', 'D') or len(line) < 3:
        continue
    listed_path = line[1:].strip()
    if target == listed_path or target.endswith(listed_path) or listed_path.endswith(target):
        print("1")
        sys.exit()

print("0")
PYEOF
)

if [[ "$LISTED" == "1" ]]; then
  echo "[protect_files] ALLOWED: '$FILE_PATH' is listed in $ACTIVE_PRD FILES section." >&2
  exit 0
fi

echo "[protect_files] BLOCKED: '$FILE_PATH' is protected and not listed in $ACTIVE_PRD FILES." >&2
exit 1
