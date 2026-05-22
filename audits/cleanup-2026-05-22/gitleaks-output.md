# Gitleaks Output — **🛑 109 leaks found**

Command: `gitleaks detect --no-banner --log-opts="--all" --report-format=json`
Date: 2026-05-22
Tool: `gitleaks v8.21.2`
Commits scanned: 714
Repo visibility: **PUBLIC** (`https://github.com/dwats250/cuttingboard`)

Raw JSON report at [gitleaks-raw.json](gitleaks-raw.json). Same findings also recorded in [verifications.md § T2](verifications.md).

## Summary

| File | Findings | Distinct commits | Rule |
|---|---|---|---|
| `.env` | 3 | 3 | `generic-api-key` |
| `logs/intraday.log` | 96 | 1 (`27b2a35a`) | `generic-api-key` |
| `logs/run_2026-04-21_180050.json` | 4 | 1 | `generic-api-key` |
| `logs/run_2026-04-28_211916.json` | 4 | 1 | `generic-api-key` |
| `reports/2026-04-21.md` | 2 | 1 | `generic-api-key` |
| **Total** | **109** | | |

## Nature of the leak

All 109 findings are the same single secret: the value of `POLYGON_API_KEY`. It appears:

- In `.env` historically (three commits before `.env` was gitignored).
- In log/report URLs of the form `https://api.polygon.io/v2/aggs/ticker/<SYMBOL>/prev?apiKey=<VALUE>`. The Polygon URL was rendered with the apiKey query parameter at [cuttingboard/ingestion.py:430](../../cuttingboard/ingestion.py) and captured by Python's logging chain (`urllib3` debug logging is the most likely emitter).

## Current tracked state

- `logs/` is gitignored as of commit `4e9e34b` (PRD-096). The leak files were untracked at that commit but the historical commits still contain them.
- `.env` is gitignored and not currently tracked.
- The Polygon code path is still live in `cuttingboard/ingestion.py` and will continue to log the URL if invoked.

## Required actions (gating further cleanup)

1. **Rotate `POLYGON_API_KEY`** at polygon.io. Treat current value as compromised.
2. **Decide on history rewrite**:
   - **Option A — rewrite history**: `git filter-repo --replace-text <patterns.txt>` to redact the secret across all 714 commits. Force-push to origin. Required follow-up: collaborators (if any) must re-clone; any forks must be notified. Open clones already in the wild cannot be retroactively cleaned.
   - **Option B — accept exposure**: After rotation, the leaked value becomes worthless. Document in `DECISIONS.md`. No history rewrite. Simplest path; relies entirely on rotation being thorough.
3. **Proceed with planned cleanup Commit 2 (Polygon removal)** which deletes the code path that produced the leak.

## Why this gated the cleanup

Per the cleanup brief (line 68):

> If anything is flagged, surface immediately and pause the cleanup until reviewed — this is the only finding that can interrupt the planned commit sequence.
