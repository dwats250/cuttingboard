#!/usr/bin/env bash
set -euo pipefail

if ! python -m ruff --version > /dev/null 2>&1; then
    echo "Ruff not found. Run: source .venv/bin/activate"
    exit 1
fi

echo "==> ruff"
python -m ruff check cuttingboard tests

if [ -f "tests/test_dashboard_renderer.py" ]; then
    echo "==> pytest tests/test_dashboard_renderer.py"
    python -m pytest tests/test_dashboard_renderer.py -q
else
    echo "==> tests/test_dashboard_renderer.py not found — skipping"
fi

echo "==> git status"
git status --short
