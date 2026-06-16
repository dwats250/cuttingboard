#!/usr/bin/env bash
# PRD-194 — publish this run's artifacts onto the dedicated UNPROTECTED publish
# branch (NOT main). main keeps full branch protection and never takes a bot push.
#
# Mechanism (review-amended 2026-06-16; supersedes the rebase-onto-main spec):
# rebasing the main-based artifact commit onto origin/publish would 3-way-merge the
# divergent histories and CONFLICT on append-only logs/audit.jsonl (publish and the
# run both add lines at EOF). Instead we build the publish commit in a WORKTREE on
# the publish tip and overlay artifacts there:
#   - logs/audit.jsonl: DELTA-APPEND only THIS run's new rows onto the publish tip's
#     CURRENT file (never wholesale-copy/clobber — preserves any rows another writer
#     landed since this run's restore). Base = the publish tip we restored from
#     (CB_PUBLISH_BASE_SHA); append-only => the base is a prefix of POST_SHA's file.
#   - everything else (ui/, logs/regime_history.jsonl, logs/latest_*.json, macro
#     snapshots): full-regen OVERWRITE from the run's committed blob.
# Parent = publish tip => clean fast-forward; the cb-publish concurrency group
# serializes all writers so the tip does not move under us. A rejected push (the
# accepted cancel-residual edge) fails the job; the next run's restore recovers.
set -euo pipefail

PUBLISH_BRANCH="${PUBLISH_BRANCH:-publish}"
AUDIT_PATH="logs/audit.jsonl"

pre_sha="${PRE_SHA:-}"
post_sha="${POST_SHA:-}"
base_sha="${CB_PUBLISH_BASE_SHA:-}"   # publish tip at restore time (audit delta base)

if [ -z "$pre_sha" ] || [ -z "$post_sha" ]; then
  echo "artifact publish: missing SHA state - skipping push"
  exit 0
fi
if [ "$pre_sha" = "$post_sha" ]; then
  echo "artifact publish: no changes - skipping push"
  exit 0
fi

# PRD-100-PATCH parity: never publish from a dirty tree. We publish COMMITTED
# blobs (POST_SHA), so a mutated-but-unstaged artifact would be silently dropped.
dirty_files="$(git status --short)"
if [ -n "$dirty_files" ]; then
  echo "artifact publish: dirty tree - aborting"
  echo "$dirty_files"
  exit 1
fi

git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"

msg="$(git show -s --format=%s "$post_sha")"
mapfile -t changed < <(git diff --name-only "$pre_sha" "$post_sha")
echo "artifact publish: ${#changed[@]} file(s) -> $PUBLISH_BRANCH"

# Bootstrap: publish branch absent -> seed it from the artifact commit itself.
if ! git ls-remote --exit-code --heads origin "$PUBLISH_BRANCH" >/dev/null 2>&1; then
  echo "artifact publish: '$PUBLISH_BRANCH' absent - bootstrapping from $post_sha"
  git push origin "$post_sha:refs/heads/$PUBLISH_BRANCH"
  echo "artifact publish: created '$PUBLISH_BRANCH'"
  exit 0
fi

git fetch origin "$PUBLISH_BRANCH"

wt="$(mktemp -d)"
cleanup() { git worktree remove --force "$wt" 2>/dev/null || true; }
trap cleanup EXIT
git worktree add --force "$wt" "origin/$PUBLISH_BRANCH"

for path in "${changed[@]}"; do
  [ -z "$path" ] && continue
  dest="$wt/$path"
  mkdir -p "$(dirname "$dest")"
  if [ "$path" = "$AUDIT_PATH" ]; then
    # HARD REQUIREMENT: delta-append THIS run's new rows onto the publish tip's
    # current audit.jsonl — never clobber. New rows = POST_SHA file beyond the
    # restore-time base (append-only => base is a prefix).
    if [ -n "$base_sha" ] && git cat-file -e "$base_sha:$AUDIT_PATH" 2>/dev/null; then
      base_count="$(git show "$base_sha:$AUDIT_PATH" | wc -l)"
    else
      base_count=0
    fi
    if [ -f "$dest" ] && [ -s "$dest" ] && [ -n "$(tail -c1 "$dest")" ]; then
      printf '\n' >> "$dest"   # ensure newline-terminated before appending
    fi
    git show "$post_sha:$AUDIT_PATH" | tail -n +"$((base_count + 1))" >> "$dest"
    echo "artifact publish: delta-appended $AUDIT_PATH (base rows=$base_count)"
  elif git cat-file -e "$post_sha:$path" 2>/dev/null; then
    git show "$post_sha:$path" > "$dest"   # full-regen overwrite
  else
    rm -f "$dest"   # path deleted in the artifact commit
  fi
done

git -C "$wt" add -A
if git -C "$wt" diff --staged --quiet; then
  echo "artifact publish: no net change vs $PUBLISH_BRANCH - skipping"
  exit 0
fi
git -C "$wt" -c user.name="github-actions[bot]" \
             -c user.email="github-actions[bot]@users.noreply.github.com" \
             commit -m "$msg"

if git -C "$wt" push origin "HEAD:refs/heads/$PUBLISH_BRANCH"; then
  echo "artifact publish: pushed -> $PUBLISH_BRANCH"
  exit 0
fi
echo "artifact publish: push rejected ($PUBLISH_BRANCH tip moved) - failing; next run recovers via restore"
exit 1
