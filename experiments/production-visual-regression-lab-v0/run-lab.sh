#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
LAB_ROOT=$SCRIPT_DIR
REPO_ROOT=$(cd -- "$LAB_ROOT/../.." && pwd)
PYTHON=$REPO_ROOT/.venv/bin/python
CLI=$LAB_ROOT/runner/cli.mjs
CATALOG=$LAB_ROOT/fixtures/catalog.json

build_fixtures() {
  "$PYTHON" "$LAB_ROOT/fixtures/build_fixtures.py"
}

build_currentmain_fixtures() {
  "$PYTHON" "$LAB_ROOT/fixtures/build_currentmain_fixtures.py"
}

run_cli() {
  (cd "$LAB_ROOT" && node "$CLI" "$@")
}

command=${1:-validate}
if (($# > 0)); then
  shift
fi

case "$command" in
  validate)
    build_fixtures
    run_cli validate "$@"
    ;;
  quick)
    build_fixtures
    run_cli validate --quick "$@"
    ;;
  self-test)
    build_fixtures
    build_currentmain_fixtures
    (cd "$LAB_ROOT" && node --test tests/self-test.mjs "$@")
    ;;
  prototype)
    build_currentmain_fixtures
    run_cli prototype "$@"
    ;;
  inspect)
    if [[ ! -f "$CATALOG" ]]; then
      build_fixtures
    fi
    run_cli inspect "$@"
    ;;
  compare)
    run_cli compare "$@"
    ;;
  calibrate)
    build_fixtures
    run_cli compare \
      --before "$LAB_ROOT/fixtures/generated/prd314-prefixt-23-13.html" \
      --after "$LAB_ROOT/fixtures/generated/prd314-current-23-13.html" \
      --fixture prd314-current-23-13 \
      --viewports 360x800,431x932 \
      --scales 100,125 \
      --output "$LAB_ROOT/reports/comparison-prd314.json" "$@"
    ;;
  *)
    echo "Usage: $0 [validate|quick|self-test|inspect|compare|calibrate|prototype] [args...]" >&2
    exit 2
    ;;
esac
