#!/usr/bin/env bash
set -euo pipefail

if ! python -m ruff --version > /dev/null 2>&1; then
    echo "Ruff not found. Run: source .venv/bin/activate"
    exit 1
fi

echo "==> ruff"
python -m ruff check cuttingboard tests

echo "==> pytest tests/"
python -m pytest tests/ -q

echo "==> git status"
git status --short
