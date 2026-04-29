#!/usr/bin/env bash
# PostToolUse/Write + PostToolUse/Edit
# Runs pytest -q when a scoped Python file changes; debounces within 10 seconds.

INPUT=$(cat)
PATH=".venv/bin:$PATH"

FILE_PATH=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', ''))
")

[[ -n "$FILE_PATH" ]] || exit 0

# Scope: cuttingboard/*.py or tests/*.py (no subdirectories)
if ! echo "$FILE_PATH" | grep -qE '(^|/)cuttingboard/[^/]+\.py$|(^|/)tests/[^/]+\.py$'; then
  exit 0
fi

# Debounce: skip if pytest ran within the last 10 seconds
DEBOUNCE_FILE=".claude/state/pytest_last_run"
NOW=$(date +%s)

if [[ -f "$DEBOUNCE_FILE" ]]; then
  LAST_RUN=$(cat "$DEBOUNCE_FILE" 2>/dev/null || echo 0)
  ELAPSED=$(( NOW - LAST_RUN ))
  if [[ $ELAPSED -lt 10 ]]; then
    echo "[test_gate] Debounce: skipping pytest (${ELAPSED}s since last run, threshold 10s)" >&2
    exit 0
  fi
fi

echo "[test_gate] $FILE_PATH changed — running pytest..." >&2
echo "$NOW" > "$DEBOUNCE_FILE"

PYTEST_STATUS=0
if .venv/bin/pytest -q tests/; then
  echo "[test_gate] All tests passed." >&2
else
  echo "[test_gate] TESTS FAILED — review failures before proceeding." >&2
  PYTEST_STATUS=1
fi

if ! RUFF_OUTPUT=$(ruff check "$FILE_PATH" 2>&1); then
  echo "[test_gate] Ruff: $RUFF_OUTPUT" >&2
fi

if [[ "$PYTEST_STATUS" -ne 0 ]]; then
  exit 1
fi
