# Dev Workflow

Standard flow for validating and pushing a source-only fix.

## Standard Recovery Flow

```bash
source .venv/bin/activate
python -m ruff check cuttingboard tests
python -m pytest tests/test_dashboard_renderer.py -q
git status --short
git pull --rebase origin main
git push
```

Or use the pre-push check script (runs ruff + tests + git status):

```bash
bash scripts/pre_push_check.sh
```

## Common Failures

**`No module named ruff`**
The venv is not active or dependencies are missing.
Fix: `source .venv/bin/activate`

**`Ruff F841`**
A local variable is assigned but never used.
Fix: remove the assignment or prefix the variable name with `_`.

**`Cannot pull with rebase: You have unstaged changes`**
The working tree is dirty. Stage or stash changes first.
Fix: `git stash` then `git pull --rebase origin main` then `git stash pop`

**`Push rejected — fetch first`**
Remote main has commits that local main does not have.
Fix: `git pull --rebase origin main` then `git push`

## Confirming Artifact Tracking

After any git hygiene operation, verify no generated runtime files are tracked:

```bash
git ls-files logs reports
```

Expected output: only `reports/.gitkeep`. Generated runtime files must not appear:

- `logs/latest_run.json`
- `logs/latest_contract.json`
- `logs/latest_payload.json`
- `logs/market_map.json`
- `logs/audit.jsonl`
- `logs/cron.log`
- `logs/evaluation.jsonl`
- `logs/last_notification_state.json`
- `logs/macro_drivers_snapshot.json`
- `logs/performance_summary.json`
- `logs/run_YYYY-MM-DD_HHMMSS.json`
- `reports/YYYY-MM-DD.md`

Files under `tests/fixtures/` and `docs/examples/` remain eligible for tracking.
