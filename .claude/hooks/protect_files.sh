#!/usr/bin/env bash
# PreToolUse/Write + PreToolUse/Edit
# Blocks writes to protected paths unconditionally (PRD-254). Catches
# accidents, not intent: a genuine protected-file edit under an active PRD
# goes through Bash (sed -i, heredoc), which this hook never intercepted
# anyway (Write/Edit only) -- see docs/CLAUDE_HOOKS.md for the decision not
# to extend the matcher to Bash.

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

echo "[protect_files] BLOCKED: '$FILE_PATH' is protected. Protected-path writes are never allowed through Write/Edit; use Bash if a PRD genuinely needs to touch it." >&2
exit 1
