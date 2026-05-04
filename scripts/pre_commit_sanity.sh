#!/usr/bin/env bash
set -euo pipefail

echo "=== branch ==="
git branch --show-current

echo ""
echo "=== staged files ==="
git diff --cached --name-only

echo ""
echo "=== artifact warning ==="
STAGED=$(git diff --cached --name-only)
if echo "$STAGED" | grep -qE '^(logs|reports)/'; then
  echo "WARNING: logs/ or reports/ files are staged — confirm this is intentional."
else
  echo "OK — no logs/ or reports/ files staged."
fi

echo ""
echo "=== unresolved conflicts ==="
CONFLICTS=$(git diff --name-only --diff-filter=U)
if [ -n "$CONFLICTS" ]; then
  echo "CONFLICTS DETECTED:"
  echo "$CONFLICTS"
else
  echo "none"
fi

echo ""
echo "=== recent commits ==="
git log --oneline -5
