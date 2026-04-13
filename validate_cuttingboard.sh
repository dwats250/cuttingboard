#!/usr/bin/env bash
set -euo pipefail

# Cutting Board validation harness
# Usage:
#   chmod +x validate_cuttingboard.sh
#   ./validate_cuttingboard.sh
#
# Optional env vars:
#   PYTHON_BIN=python3
#   CB_MODULE=cuttingboard
#   FIXTURE_FILE=tests/fixtures/2026-04-12.json

PYTHON_BIN="${PYTHON_BIN:-python3}"
CB_MODULE="${CB_MODULE:-cuttingboard}"
FIXTURE_FILE="${FIXTURE_FILE:-}"

ROOT_DIR="$(pwd)"
LOG_DIR="${ROOT_DIR}/logs"
REPORT_DIR="${ROOT_DIR}/reports"
TMP_DIR="${ROOT_DIR}/.cb_validation_tmp"

mkdir -p "$LOG_DIR" "$REPORT_DIR" "$TMP_DIR"

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; exit 1; }
info() { echo "[INFO] $1"; }
warn() { echo "[WARN] $1"; }

require_file() {
  local path="$1"
  local label="$2"
  [[ -f "$path" ]] || fail "$label missing: $path"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found: $1"
}

json_get() {
  local file="$1"
  local expr="$2"
  "$PYTHON_BIN" - <<PY
import json
from pathlib import Path
p = Path(r"$file")
data = json.loads(p.read_text())
value = data
for part in r"$expr".split("."):
    if not part:
        continue
    value = value[part]
print(value if not isinstance(value, (dict, list)) else json.dumps(value, sort_keys=True))
PY
}

json_has_key() {
  local file="$1"
  local expr="$2"
  "$PYTHON_BIN" - <<PY
import json, sys
from pathlib import Path
data = json.loads(Path(r"$file").read_text())
value = data
try:
    for part in r"$expr".split("."):
        if not part:
            continue
        value = value[part]
except Exception:
    sys.exit(1)
sys.exit(0)
PY
}

json_assert_eq() {
  local file="$1"
  local expr="$2"
  local expected="$3"
  local actual
  actual="$(json_get "$file" "$expr")"
  [[ "$actual" == "$expected" ]] || fail "Expected $expr=$expected but got $actual in $file"
}

json_assert_in() {
  local file="$1"
  local expr="$2"
  shift 2
  local actual
  actual="$(json_get "$file" "$expr")"
  for allowed in "$@"; do
    [[ "$actual" == "$allowed" ]] && return 0
  done
  fail "Expected $expr to be one of [$*] but got $actual in $file"
}

json_assert_int_ge() {
  local file="$1"
  local expr="$2"
  local min="$3"
  local actual
  actual="$(json_get "$file" "$expr")"
  [[ "$actual" =~ ^-?[0-9]+$ ]] || fail "$expr is not integer-like: $actual"
  (( actual >= min )) || fail "Expected $expr >= $min but got $actual"
}

snapshot_paths() {
  find "$LOG_DIR" -maxdepth 1 -type f \( -name 'latest_run.json' -o -name 'run_*.json' -o -name 'audit.jsonl' \) | sort > "$TMP_DIR/$1.logs.txt" || true
  find "$REPORT_DIR" -maxdepth 1 -type f -name '*.md' | sort > "$TMP_DIR/$1.reports.txt" || true
}

newest_report() {
  find "$REPORT_DIR" -maxdepth 1 -type f -name '*.md' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n1 | awk '{print $2}'
}

diff_snapshot() {
  local before="$1"
  local after="$2"
  diff -u "$TMP_DIR/$before.logs.txt" "$TMP_DIR/$after.logs.txt" >/dev/null 2>&1 || true
  diff -u "$TMP_DIR/$before.reports.txt" "$TMP_DIR/$after.reports.txt" >/dev/null 2>&1 || true
}

run_live() {
  info "Running LIVE mode"
  snapshot_paths "before_live"
  "$PYTHON_BIN" -m "$CB_MODULE"
  snapshot_paths "after_live"

  require_file "$LOG_DIR/latest_run.json" "latest run summary"

  local latest_report
  latest_report="$(newest_report)"
  [[ -n "${latest_report:-}" ]] || fail "No markdown report found in $REPORT_DIR"
  require_file "$latest_report" "latest markdown report"

  json_assert_in "$LOG_DIR/latest_run.json" "status" "SUCCESS" "FAIL"
  json_assert_in "$LOG_DIR/latest_run.json" "mode" "LIVE" "SUNDAY" "FIXTURE"
  json_assert_in "$LOG_DIR/latest_run.json" "regime" "RISK_ON" "RISK_OFF" "NEUTRAL" "CHAOTIC"
  json_assert_in "$LOG_DIR/latest_run.json" "posture" "AGGRESSIVE_LONG" "CONTROLLED_LONG" "DEFENSIVE_SHORT" "NEUTRAL_PREMIUM" "STAY_FLAT"
  json_assert_in "$LOG_DIR/latest_run.json" "data_status" "ok" "fallback" "stale"

  grep -q '^Verification: ' "$latest_report" || fail "Verification header missing in report: $latest_report"

  pass "LIVE run produced report and JSON summary"
}

run_verify_expect_pass_or_fail() {
  info "Running VERIFY mode against latest_run.json"
  set +e
  "$PYTHON_BIN" -m "$CB_MODULE" --mode verify
  local rc=$?
  set -e

  if [[ $rc -eq 0 ]]; then
    pass "VERIFY returned PASS"
  elif [[ $rc -eq 1 ]]; then
    warn "VERIFY returned FAIL - inspect latest_run.json and report output"
  else
    fail "VERIFY returned unexpected exit code: $rc"
  fi
}

run_broken_json_test() {
  info "Testing VERIFY failure on intentionally broken JSON"
  local broken="$TMP_DIR/broken.json"
  printf '{"status": "SUCCESS", "mode": "LIVE"' > "$broken"

  set +e
  "$PYTHON_BIN" -m "$CB_MODULE" --mode verify --file "$broken" >/dev/null 2>&1
  local rc=$?
  set -e

  [[ $rc -eq 1 ]] || fail "Broken JSON should fail VERIFY with exit 1, got $rc"
  pass "Broken JSON correctly fails VERIFY"
}

run_fixture_twice_if_available() {
  if [[ -z "$FIXTURE_FILE" ]]; then
    local candidate
    candidate="$(find tests/fixtures -maxdepth 1 -type f -name '*.json' 2>/dev/null | sort | head -n1 || true)"
    FIXTURE_FILE="${candidate:-}"
  fi

  if [[ -z "$FIXTURE_FILE" || ! -f "$FIXTURE_FILE" ]]; then
    warn "No fixture file found. Skipping fixture determinism test."
    return 0
  fi

  info "Running FIXTURE determinism test with $FIXTURE_FILE"

  "$PYTHON_BIN" -m "$CB_MODULE" --mode fixture --fixture-file "$FIXTURE_FILE"
  require_file "$LOG_DIR/latest_run.json" "latest run summary after fixture pass 1"
  cp "$LOG_DIR/latest_run.json" "$TMP_DIR/fixture_run1.json"
  local report1
  report1="$(newest_report)"
  [[ -n "${report1:-}" ]] || fail "No report after fixture run 1"
  cp "$report1" "$TMP_DIR/fixture_run1.md"

  sleep 1

  "$PYTHON_BIN" -m "$CB_MODULE" --mode fixture --fixture-file "$FIXTURE_FILE"
  require_file "$LOG_DIR/latest_run.json" "latest run summary after fixture pass 2"
  cp "$LOG_DIR/latest_run.json" "$TMP_DIR/fixture_run2.json"
  local report2
  report2="$(newest_report)"
  [[ -n "${report2:-}" ]] || fail "No report after fixture run 2"
  cp "$report2" "$TMP_DIR/fixture_run2.md"

  "$PYTHON_BIN" - <<PY
import json, sys
from pathlib import Path

a = json.loads(Path(r"$TMP_DIR/fixture_run1.json").read_text())
b = json.loads(Path(r"$TMP_DIR/fixture_run2.json").read_text())

for transient_key in ("run_id", "timestamp"):
    a.pop(transient_key, None)
    b.pop(transient_key, None)

if a != b:
    print("Fixture JSON mismatch after removing transient fields.")
    sys.exit(1)
PY
  [[ $? -eq 0 ]] || fail "Fixture JSON outputs are not deterministic"

  "$PYTHON_BIN" - <<PY
from pathlib import Path
a = Path(r"$TMP_DIR/fixture_run1.md").read_text().splitlines()
b = Path(r"$TMP_DIR/fixture_run2.md").read_text().splitlines()

def scrub(lines):
    out = []
    for line in lines:
        lower = line.lower()
        if "run id" in lower or "timestamp" in lower or "generated at" in lower:
            continue
        out.append(line)
    return out

if scrub(a) != scrub(b):
    raise SystemExit(1)
PY
  [[ $? -eq 0 ]] || fail "Fixture markdown reports are not deterministic"

  pass "FIXTURE mode is deterministic (excluding transient fields)"
}

run_summary_sanity_checks() {
  require_file "$LOG_DIR/latest_run.json" "latest run summary for sanity checks"

  info "Running summary sanity checks"

  json_has_key "$LOG_DIR/latest_run.json" "kill_switch" || fail "kill_switch missing"
  json_has_key "$LOG_DIR/latest_run.json" "permission" || fail "permission missing"
  json_has_key "$LOG_DIR/latest_run.json" "min_rr_applied" || fail "min_rr_applied missing"
  json_has_key "$LOG_DIR/latest_run.json" "warnings" || fail "warnings missing"
  json_has_key "$LOG_DIR/latest_run.json" "errors" || fail "errors missing"

  local regime posture kill_switch qualified min_rr
  regime="$(json_get "$LOG_DIR/latest_run.json" "regime")"
  posture="$(json_get "$LOG_DIR/latest_run.json" "posture")"
  kill_switch="$(json_get "$LOG_DIR/latest_run.json" "kill_switch")"
  qualified="$(json_get "$LOG_DIR/latest_run.json" "candidates_qualified")"
  min_rr="$(json_get "$LOG_DIR/latest_run.json" "min_rr_applied")"

  if [[ "$regime" == "CHAOTIC" ]]; then
    [[ "$qualified" == "0" ]] || fail "CHAOTIC regime must have zero qualified candidates"
  fi

  if [[ "$posture" == "STAY_FLAT" ]]; then
    [[ "$qualified" == "0" ]] || fail "STAY_FLAT posture must have zero qualified candidates"
  fi

  if [[ "$kill_switch" == "True" || "$kill_switch" == "true" ]]; then
    [[ "$qualified" == "0" ]] || fail "kill_switch=true must force zero qualified candidates"
  fi

  if [[ "$regime" == "NEUTRAL" ]]; then
    [[ "$min_rr" == "3" || "$min_rr" == "3.0" ]] || fail "NEUTRAL regime must set min_rr_applied to 3.0"
  fi

  pass "Summary sanity checks passed"
}

main() {
  require_cmd "$PYTHON_BIN"
  info "Validating Cutting Board from: $ROOT_DIR"
  info "Using Python: $PYTHON_BIN"
  info "Using module: $CB_MODULE"

  run_live
  run_verify_expect_pass_or_fail
  run_broken_json_test
  run_fixture_twice_if_available
  run_summary_sanity_checks

  echo
  echo "Validation harness completed."
  echo "Inspect:"
  echo "  - $LOG_DIR/latest_run.json"
  echo "  - $(newest_report 2>/dev/null || echo "$REPORT_DIR")"
}

main "$@"
