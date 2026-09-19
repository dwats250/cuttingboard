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
  # PRD-346: the remaining fixed mutable paths the pipelines commit (run_*.json history stays out)
  logs/last_hourly_slot.json
  logs/latest_hourly_market_map.json
  logs/latest_run.json
  logs/macro_drivers_snapshot.json
  logs/price_bars_snapshot.json
  logs/regime_history.jsonl
  logs/trend_structure_snapshot.json
  ui/contract.json
  ui/dashboard.html
  ui/index.html
)

for f in "${GENERATED[@]}"; do
  if git ls-files --error-unmatch "$f" &>/dev/null; then
    git checkout HEAD -- "$f"
    echo "restored: $f"
  fi
done

echo ""
git status --short
