#!/usr/bin/env bash
# PRD-194 R3/R4 — restore read-back state from the publish branch before a run,
# and record the publish tip we restored from so the publish step can delta-append
# this run's new logs/audit.jsonl rows onto the LIVE tip without clobbering history.
#
# Args: the read-back state file path(s) to restore (e.g. logs/audit.jsonl, or
# logs/macro_awareness_state.json for the macro producer).
#
# Amendment 1 (review, 2026-06-16): explicit branch-presence gate, no blanket
# `|| true`. Branch present -> fetch + `git checkout` the state path; a genuine
# checkout error FAILS the job (set -e, no swallow). Branch absent -> bootstrap
# from main's checked-in copy (no restore); the publish push creates the branch.
# A path that is legitimately absent on an existing publish branch (e.g. the macro
# state file before the first macro publish) is logged and skipped — that is not a
# checkout error, so R3's fail-live clause for a PRESENT-but-failing restore stays
# intact.
set -euo pipefail

PUBLISH_BRANCH="${PUBLISH_BRANCH:-publish}"

if [ "$#" -eq 0 ]; then
  echo "publish-state restore: no state paths given" >&2
  exit 2
fi

if git ls-remote --exit-code --heads origin "$PUBLISH_BRANCH" >/dev/null 2>&1; then
  git fetch origin "$PUBLISH_BRANCH"
  base_sha="$(git rev-parse "origin/$PUBLISH_BRANCH")"
  if [ -n "${GITHUB_ENV:-}" ]; then
    echo "CB_PUBLISH_BASE_SHA=$base_sha" >> "$GITHUB_ENV"
  fi
  echo "publish-state restore: '$PUBLISH_BRANCH' present @ $base_sha"
  for path in "$@"; do
    if git cat-file -e "origin/$PUBLISH_BRANCH:$path" 2>/dev/null; then
      echo "publish-state restore: $path"
      git checkout "origin/$PUBLISH_BRANCH" -- "$path"
    else
      echo "publish-state restore: $path absent on '$PUBLISH_BRANCH' — keeping main's copy"
    fi
  done
else
  echo "publish-state restore: '$PUBLISH_BRANCH' absent — bootstrapping from main's checked-in state"
fi
