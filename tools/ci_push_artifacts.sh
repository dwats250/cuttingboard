#!/usr/bin/env bash
# PRD-194 — publish this run's artifacts onto the dedicated UNPROTECTED publish
# branch (NOT main). main keeps full branch protection and never takes a bot push.
#
# Mechanism (review-amended; see PRD-194.md R5): build the publish commit in a
# WORKTREE on the publish tip and overlay artifacts there —
#   - logs/audit.jsonl: DELTA-APPEND only THIS run's new rows (beyond the restore
#     base CB_PUBLISH_BASE_SHA) onto the tip's CURRENT file. Never clobbers a row
#     another writer landed since this run's restore.
#   - everything else (ui/, regime_history, latest_*, macro snapshots): full-regen
#     OVERWRITE from the run's committed blob.
# Concurrency is NOT serialized by a shared lock (that over-serialized the hourly
# alert — Codex P2). Instead, if the publish tip moved under us the push is a
# non-fast-forward and we RETRY (bounded, with jitter): re-fetch the tip, re-apply
# THIS run's delta onto the new tip, re-commit, re-push. Delta-append makes the
# retry idempotent against the moving tip.
# Accepted residual: on a tip-moved retry we overwrite ui/ + regime_history with
# THIS run's versions, so regime_history can be briefly one row stale vs the other
# writer's just-landed audit row — regenerated correctly on the next run.
set -euo pipefail

PUBLISH_BRANCH="${PUBLISH_BRANCH:-publish}"
AUDIT_PATH="logs/audit.jsonl"
MAX_ATTEMPTS="${CB_PUBLISH_MAX_ATTEMPTS:-5}"

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

# THIS run's new audit rows are fixed across retries: the count beyond the restore
# base (append-only => base is a prefix of POST_SHA's file).
if [ -n "$base_sha" ] && git cat-file -e "$base_sha:$AUDIT_PATH" 2>/dev/null; then
  base_count="$(git show "$base_sha:$AUDIT_PATH" | wc -l)"
else
  base_count=0
fi

wt="$(mktemp -d)"
cleanup() { git worktree remove --force "$wt" 2>/dev/null || true; rm -rf "$wt" 2>/dev/null || true; }
trap cleanup EXIT

# Build the publish commit on the CURRENT publish tip and push it. Returns 0 on a
# successful push (or no-op), 2 on a non-fast-forward (retryable), 1 on hard error.
attempt_publish() {
  git worktree remove --force "$wt" 2>/dev/null || true
  rm -rf "$wt"
  git fetch origin "$PUBLISH_BRANCH"
  git worktree add --force "$wt" "origin/$PUBLISH_BRANCH"

  local path dest
  for path in "${changed[@]}"; do
    [ -z "$path" ] && continue
    dest="$wt/$path"
    mkdir -p "$(dirname "$dest")"
    if [ "$path" = "$AUDIT_PATH" ]; then
      if [ -f "$dest" ] && [ -s "$dest" ] && [ -n "$(tail -c1 "$dest")" ]; then
        printf '\n' >> "$dest"
      fi
      git show "$post_sha:$AUDIT_PATH" | tail -n +"$((base_count + 1))" >> "$dest"
    elif git cat-file -e "$post_sha:$path" 2>/dev/null; then
      git show "$post_sha:$path" > "$dest"
    else
      rm -f "$dest"
    fi
  done

  git -C "$wt" add -A
  if git -C "$wt" diff --staged --quiet; then
    echo "artifact publish: no net change vs $PUBLISH_BRANCH - skipping"
    return 0
  fi
  git -C "$wt" -c user.name="github-actions[bot]" \
               -c user.email="github-actions[bot]@users.noreply.github.com" \
               commit -m "$msg"
  if git -C "$wt" push origin "HEAD:refs/heads/$PUBLISH_BRANCH" 2>"$wt/.push_err"; then
    return 0
  fi
  cat "$wt/.push_err" >&2 || true
  if grep -qiE 'non-fast-forward|fetch first|rejected|stale info|cannot lock ref' "$wt/.push_err" 2>/dev/null; then
    return 2
  fi
  return 1
}

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  set +e
  attempt_publish
  rc=$?
  set -e
  if [ "$rc" -eq 0 ]; then
    echo "artifact publish: pushed -> $PUBLISH_BRANCH (attempt $attempt)"
    exit 0
  fi
  if [ "$rc" -eq 1 ]; then
    echo "artifact publish: hard error on attempt $attempt - aborting"
    exit 1
  fi
  echo "artifact publish: $PUBLISH_BRANCH tip moved (attempt $attempt/$MAX_ATTEMPTS) - re-applying delta onto new tip"
  sleep "$(( (RANDOM % 3) + 1 ))"   # 1-3s jitter
done

echo "artifact publish: still non-fast-forward after $MAX_ATTEMPTS attempts - failing; next run recovers via restore"
exit 1
