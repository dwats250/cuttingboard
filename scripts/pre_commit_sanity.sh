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
echo "=== gitnexus detect-changes (staged) ==="
# CLAUDE.md § GitNexus: detect_changes is mandatory before every commit.
# Wired into this script so it does not depend on session-by-session
# discipline. Failures are surfaced but do not block the commit — the
# script reports; the human decides.
if command -v npx >/dev/null 2>&1; then
  if [ -z "$STAGED" ]; then
    echo "no staged files — skipping detect-changes"
  else
    npx --no-install gitnexus detect-changes --scope staged 2>&1 \
      || echo "detect-changes returned non-zero (index may be stale; run scripts/gitnexus-analyze.sh)"
  fi
else
  echo "npx not available — skipping detect-changes"
fi

echo ""
echo "=== recent commits ==="
git log --oneline -5
