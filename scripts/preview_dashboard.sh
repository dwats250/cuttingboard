#!/usr/bin/env bash
# preview_dashboard.sh — PRD-178 Tier 1: local fresh-data dashboard preview.
#
# Fetches fresh hourly artifacts with notification credentials stripped from
# the environment (sends degrade to audited skipped/not_configured rows;
# zero outbound messages), then renders to a NON-ui output path so the
# PRD-118/119 publish gates are never in play (PRD-119 R12 exemption by
# design). This script never writes under the ui directory.
#
# Caveat: the fetch mutates tracked logs/* locally (routine local dirt; the
# hourly CI force-add overwrites these on its next commit). Do not commit
# logs/* afterwards.
#
# Usage:
#   scripts/preview_dashboard.sh              # fetch fresh data + render
#   SKIP_FETCH=1 scripts/preview_dashboard.sh # render only (layout iteration)

set -euo pipefail
cd "$(dirname "$0")/.."

OUT=reports/output/preview_dashboard.html

if [ "${SKIP_FETCH:-0}" != "1" ]; then
    env -u TELEGRAM_BOT_TOKEN -u TELEGRAM_CHAT_ID \
        python3 -m cuttingboard.alert_runner --force-slot
fi

python3 -m cuttingboard.delivery.dashboard_renderer \
    --payload logs/latest_hourly_payload.json \
    --run logs/latest_hourly_run.json \
    --market-map-path logs/latest_hourly_market_map.json \
    --output "$OUT"

echo "preview written: $OUT"
