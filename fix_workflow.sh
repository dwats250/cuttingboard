#!/usr/bin/env bash
set -euo pipefail

FILE=".github/workflows/cuttingboard.yml"

echo "=== BACKUP ==="
cp "$FILE" /tmp/cuttingboard.yml.bak

echo "=== REPLACING STALE git add ==="
python3 - <<'PY'
from pathlib import Path
p = Path(".github/workflows/cuttingboard.yml")
s = p.read_text()
old = "git add reports/ logs/"
new = "git add reports/ || true\ngit add -f logs/ || true"
count = s.count(old)
s = s.replace(old, new)
p.write_text(s)
print(f"replaced git add occurrences: {count}")
PY

echo "=== REPLACING STALE PUSH BLOCK ==="
python3 - <<'PY'
from pathlib import Path
p = Path(".github/workflows/cuttingboard.yml")
s = p.read_text()

old1 = '''if [ "$PRE_SHA" = "$POST_SHA" ]; then
  echo "No new commit — skipping push"
  exit 0
fi

git push'''

old2 = '''if [ "$PRE_SHA" = "$POST_SHA" ]; then
  echo "No new commit - skipping push"
  exit 0
fi

git push'''

new = '''if [ -z "${PRE_SHA:-}" ] || [ -z "${POST_SHA:-}" ]; then
  echo "Missing SHA state - skipping push"
  exit 0
fi

if [ "$PRE_SHA" = "$POST_SHA" ]; then
  echo "No new commit - skipping push"
  exit 0
fi

git push'''

count = 0
if old1 in s:
    s = s.replace(old1, new)
    count += 1
if old2 in s:
    s = s.replace(old2, new)
    count += 1

p.write_text(s)
print(f"replaced push block occurrences: {count}")
PY

echo "=== VERIFY ==="
grep -n "git add" "$FILE" || true
grep -n "Missing SHA state - skipping push" "$FILE" || true
grep -n "No new commit - skipping push" "$FILE" || true

echo "=== DIFF ==="
git --no-pager diff -- "$FILE" || true

echo "=== COMMIT ==="
git add "$FILE"
git commit -m "force replace all stale workflow paths"

echo "=== PUSH ==="
git push origin main

echo "=== TRIGGER WORKFLOW ==="
gh workflow run cuttingboard.yml --ref main

echo "=== DONE ==="
