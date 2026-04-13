#!/usr/bin/env bash
# run_daily.sh — Local daily runner for Cuttingboard.
#
# Runs the live pipeline then verifies the output.
# On Sunday, live mode auto-converts to sunday mode (regime-only, no candidates).
#
# Usage (from project root, venv active):
#   chmod +x run_daily.sh
#   ./run_daily.sh
#
# Cron examples (replace paths):
#   # Weekday premarket — 06:00 PT / 09:00 ET
#   0 13 * * 1-5  cd /home/user/cuttingboard && /home/user/cuttingboard/.venv/bin/python -m cuttingboard --mode live && /home/user/cuttingboard/.venv/bin/python -m cuttingboard --mode verify
#
#   # Or via this script:
#   0 13 * * 1-5  cd /home/user/cuttingboard && .venv/bin/python run_daily.sh >> logs/cron.log 2>&1
#
#   # Sunday regime report — 10:00 UTC
#   0 10 * * 0    cd /home/user/cuttingboard && .venv/bin/python -m cuttingboard --mode sunday && .venv/bin/python -m cuttingboard --mode verify
#
# Exit codes:
#   0 — live run succeeded, verify PASS
#   1 — live run failed, OR verify FAIL
#
# Env vars:
#   PYTHON_BIN    override Python binary (default: python3)
#   CB_MODULE     override module name (default: cuttingboard)

set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
CB_MODULE="${CB_MODULE:-cuttingboard}"

# Always run from project root regardless of invocation directory.
cd "$(dirname "$0")"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*"; }

log "Starting live run"
"$PYTHON_BIN" -m "$CB_MODULE" --mode live
log "Live run complete"

log "Starting verify"
set +e
"$PYTHON_BIN" -m "$CB_MODULE" --mode verify
VERIFY_RC=$?
set -e

if [[ $VERIFY_RC -ne 0 ]]; then
    log "VERIFY FAIL (exit $VERIFY_RC) — inspect logs/latest_run.json"
    exit 1
fi

log "VERIFY PASS"
log "Artifacts: logs/latest_run.json  reports/"
