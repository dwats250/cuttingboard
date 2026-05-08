#!/usr/bin/env bash
set -euo pipefail

pre_sha="${PRE_SHA:-}"
post_sha="${POST_SHA:-}"

if [ -z "$pre_sha" ] || [ -z "$post_sha" ]; then
  echo "artifact push: missing SHA state - skipping push"
  exit 0
fi

if [ "$pre_sha" = "$post_sha" ]; then
  echo "artifact push: no changes - skipping push"
  exit 0
fi

echo "artifact push: committed changes detected ($pre_sha -> $post_sha)"

dirty_files=$(git status --short)
if [ -n "$dirty_files" ]; then
  echo "artifact push: dirty tree before rebase"
  echo "--- git status --short ---"
  git status --short
  echo "--- unstaged ---"
  git diff --name-only
  echo "--- staged ---"
  git diff --cached --name-only
  exit 1
fi

echo "artifact push: fetching origin main"
git fetch origin main

echo "artifact push: rebasing onto origin/main"
git rebase origin/main

echo "artifact push: first push attempt"
if git push origin HEAD:main; then
  echo "artifact push: final push result: success"
  exit 0
fi

echo "artifact push: first push failed; rebase retry"
dirty_files=$(git status --short)
if [ -n "$dirty_files" ]; then
  echo "artifact push: dirty tree before rebase retry"
  echo "--- git status --short ---"
  git status --short
  echo "--- unstaged ---"
  git diff --name-only
  echo "--- staged ---"
  git diff --cached --name-only
  exit 1
fi
git fetch origin main
git rebase origin/main

echo "artifact push: retry push attempt"
if git push origin HEAD:main; then
  echo "artifact push: final push result: success after retry"
  exit 0
fi

echo "artifact push: final push result: failed"
exit 1
