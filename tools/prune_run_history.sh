#!/usr/bin/env bash
# PRD-195 — cap the run_*.json history on the publish branch.
#
# Every pipeline/hourly/Sunday run force-adds a new logs/run_<ts>.json to the
# publish branch and the restore step pulls the whole glob back each run, so the
# branch accumulated run summaries UNBOUNDED — none were ever deleted. The
# dashboard already caps DISPLAY at HISTORY_LIMIT (dashboard_renderer.py); this
# caps STORAGE.
#
# Operating inside the given worktree, keep the newest <retain> logs/run_*.json
# (the filename is run_YYYY-MM-DD_HHMMSS.json, so a lexicographic sort IS the
# chronological order) and `git rm -f` the rest, staging the deletions for the
# caller's publish commit. The current run's file is the newest timestamp, so it
# is always retained; only strictly-older files are removed. Only run_*.json is
# matched — audit.jsonl, latest_*, regime_history and macro snapshots are never
# touched.
#
# Usage: prune_run_history.sh <worktree-dir> [retain-count]
#   retain-count defaults to $CB_RUN_HISTORY_RETAIN or 50. A non-numeric value
#   falls back to 50; the value is floored at 1 so a misconfiguration can never
#   wipe the history below the renderer's display cap. Keep retain >= the
#   renderer's HISTORY_LIMIT.
set -euo pipefail

wt="${1:?usage: prune_run_history.sh <worktree-dir> [retain-count]}"
retain="${2:-${CB_RUN_HISTORY_RETAIN:-50}}"
case "$retain" in
  ''|*[!0-9]*) retain=50 ;;   # non-numeric -> safe default
esac
[ "$retain" -lt 1 ] && retain=1

[ -d "$wt" ] || { echo "prune_run_history: worktree '$wt' not a directory" >&2; exit 1; }

# Collect run files by on-disk glob (fixed-format names: no spaces/newlines).
shopt -s nullglob
runs=()
for f in "$wt"/logs/run_*.json; do
  runs+=("logs/${f##*/}")
done
shopt -u nullglob

total="${#runs[@]}"
if [ "$total" -le "$retain" ]; then
  echo "prune_run_history: $total run file(s) <= retain $retain - nothing to prune"
  exit 0
fi

# Non-empty and over cap: order newest-last (lexicographic == chronological).
IFS=$'\n' runs=($(printf '%s\n' "${runs[@]}" | LC_ALL=C sort)); unset IFS

drop=$(( total - retain ))
for (( i = 0; i < drop; i++ )); do
  # -f forces removal whether the file is committed (historical) or staged-new
  # (this run's file, never in the drop set). Stages the deletion for the commit.
  git -C "$wt" rm -q -f -- "${runs[$i]}"
done
echo "prune_run_history: pruned $drop run_*.json (kept newest $retain of $total)"
