# Cuttingboard

A Python-based market observation and decision-support system for one
discretionary options trader. Ingests market data, computes contextual
interpretations across a 10-layer pipeline, and renders artifacts that help
answer four questions: *what environment are we in, what matters today, is
this actually tradable, and what conditions invalidate this.*

Cuttingboard is **descriptive, not predictive**. It does not generate alpha
and is not an automated execution engine. See `VISION.md` for what the system
is, is not, and is becoming.

---

## Canonical documents

This README is an entry point, not a system description. Authoritative state
lives in:

| Topic | File |
|---|---|
| What the system is and is not | [`VISION.md`](VISION.md) |
| Current state, test baseline, known debt, active PRD | [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md) |
| Meaningful decisions and rationale | [`docs/DECISIONS.md`](docs/DECISIONS.md) |
| Work in flight and completed | [`docs/PRD_REGISTRY.md`](docs/PRD_REGISTRY.md) |
| Pipeline architecture and module boundaries | [`docs/architecture.md`](docs/architecture.md) |
| PRD process and templates | [`docs/PRD_PROCESS.md`](docs/PRD_PROCESS.md) |
| Sidecar doctrine and read-only discipline | [`docs/sidecar_doctrine.md`](docs/sidecar_doctrine.md) |
| Engine doctor (pipeline health authority) | [`docs/engine_doctor.md`](docs/engine_doctor.md) |

---

## Install and run

Python ≥ 3.11.

```bash
pip install -e .[dev]
```

Required environment variables (set in `.env`, gitignored):

```
TELEGRAM_BOT_TOKEN=<bot token>
TELEGRAM_CHAT_ID=<chat id>
```

Run modes:

```bash
python -m cuttingboard                              # live
python -m cuttingboard --mode fixture --fixture-file PATH
python -m cuttingboard --mode sunday                # regime-only, no live data
python -m cuttingboard --mode verify --file PATH    # summary verification only
```

Tests:

```bash
python -m pytest tests -q
```

---

## Outputs

Every run produces exactly one of: `TRADES | NO TRADE | HALT`.

Canonical artifacts:

| File | Description |
|---|---|
| `logs/latest_run.json` | Machine-readable canonical run summary |
| `logs/latest_contract.json` | Pipeline output contract |
| `logs/latest_payload.json` | Delivery payload (renderer / notifier input) |
| `logs/audit.jsonl` | Append-only audit log, one record per run |
| `reports/YYYY-MM-DD.md` | Human-readable daily report |
| `ui/dashboard.html`, `ui/index.html` | Published GitHub Pages dashboard |

`logs/` is gitignored at runtime; the hourly alert workflow force-adds a small
allowlist of `latest_*.json` artifacts so the published dashboard stays in
sync with the latest run.

---

## Project structure

```
cuttingboard/          10-layer pipeline package
tests/                 pytest suite
docs/                  PRDs, architecture, decisions, process
scripts/               operator helpers (pre-commit, pre-push, prd_close)
tools/                 engine_doctor, registry validator
ui/                    published dashboard
pinescripts/           TradingView Pine indicators (rebuild intent in
                       pinescripts/README.md)
.github/workflows/     CI (hourly_alert, deploy, etc.)
```

---

## Authorship

Author: Dustin Watson.
