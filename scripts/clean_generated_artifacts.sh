#!/usr/bin/env bash
set -euo pipefail

# Restore tracked generated log/runtime files to HEAD without deleting untracked files.

GENERATED=(
  logs/audit.jsonl
  logs/latest_contract.json
  logs/latest_hourly_contract.json
  logs/latest_hourly_payload.json
  logs/latest_hourly_run.json
  logs/latest_payload.json
  logs/market_map.json
)

for f in "${GENERATED[@]}"; do
  if git ls-files --error-unmatch "$f" &>/dev/null; then
    git checkout HEAD -- "$f"
    echo "restored: $f"
  fi
done

echo ""
git status --short
