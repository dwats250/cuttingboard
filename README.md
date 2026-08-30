# Cuttingboard

A pre-market decision-support engine for one discretionary options trader. Each
session it compresses top-down market structure into one disciplined read that
answers four ordered questions: *what environment are we in, what matters today,
is this actually tradable, and what would invalidate the thesis.*

Cuttingboard is **state first, trades second**: it describes and qualifies the
market, and the trade decision is a consequence of that read, never the goal. It
is **descriptive, not predictive** - it does not generate alpha, forecast price,
or execute orders. See [`VISION.md`](VISION.md) for what the system is, is not,
and is becoming.

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

## What the operator sees

The engine renders a single published board (`cuttingboard/delivery/`). Reading
top to bottom it leads with market state and ends with the trade read:

- **Market State** - a five-axis provenance panel of where the market stands.
- **System State** - the run outcome, permission, and the reason behind it.
- **Regime and scoreboard** - the current regime read plus its recent history.
- **Market Map** - symbol-level graded market context.
- **GEX card** - a display-only gamma-exposure read (Cboe, ~15 min delayed).
- **Market Movement** - an observe-only movement heatmap.
- **Operator context tape** - macro pressure and trend-projection bands.
- **Setup chart** - a deterministic daily-candle chart with tiered levels.
- **Staleness banner** - an in-browser page-age notice so a frozen board can
  never read as fresh; shows "MARKET CLOSED" when the session is inactive.

Every board is honest about degradation: missing or untrustworthy inputs
fail closed (they block rather than guess), a market-stress HALT publishes a
halt board, and optional cards (GEX, movement) degrade to their own absence
rather than blocking the rest of the board.

---

## Install and run

Python >= 3.11.

```bash
pip install -e .[dev]
```

Environment variables (set in `.env`, gitignored):

```
POLYGON_API_KEY=<market-data key>          # OHLCV / options pipeline
TELEGRAM_BOT_TOKEN=<bot token>             # HALT / alert notifications
TELEGRAM_CHAT_ID=<chat id>
CB_OPERATOR_AVAILABILITY=<optional>        # operator-availability signal
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

## Architecture

A deterministic, staged pipeline (canonical stage order in
`cuttingboard/runtime/`): ingest -> normalize -> validate -> regime and halt
gates -> analysis (correlation, structure, options, qualification) -> decision
gates (execution / thesis / invalidation / entry-quality) -> a typed output
contract (`cuttingboard/contract_types.py`). Delivery is a strictly read-only
consumer of that contract.

The `.github/workflows/cuttingboard.yml` pipeline runs on scheduled pre-market
and open slots (a Cloudflare Worker sets the logical slot; a GitHub executor
coordinates first-success). It renders the board and publishes to the
unprotected `publish` branch that GitHub Pages serves - the committed snapshot
on `main` is never hand-overwritten from a local render. Full pipeline detail:
[`docs/architecture.md`](docs/architecture.md).

Every run produces exactly one outcome: `TRADES | NO TRADE | HALT`.

Canonical artifacts:

| File | Description |
|---|---|
| `logs/latest_run.json` | Machine-readable canonical run summary |
| `logs/latest_contract.json` | Pipeline output contract |
| `logs/latest_payload.json` | Delivery payload (renderer / notifier input) |
| `logs/audit.jsonl` | Append-only audit log, one record per run |
| `reports/YYYY-MM-DD.md` | Human-readable daily report |
| `ui/dashboard.html`, `ui/index.html` | Rendered board (published via `publish`) |

`logs/` is gitignored at runtime; the pipeline force-adds a small allowlist of
`latest_*.json` artifacts so the published board stays in sync with the run.

---

## Engineering and validation

- **Tests:** ~136 test files covering the pipeline, contract, gates, and
  renderer; run in CI on every PR and push.
- **CI gate:** the `test` job (`.github/workflows/ci.yml`) runs the registry
  validator, `ruff`, then the full `pytest` suite - isolated, no secrets. The
  live pipeline additionally gates on an exact-SHA CI proof plus the engine
  doctor, not the full suite (`docs/engine_doctor.md`).
- **Review discipline:** every change lands through a PR that Dustin merges by
  hand (no auto-merge, no direct push to `main`); each PR gets one
  fresh-context review. Agents operate under a layered standing contract with
  explicit authority modes ([`CLAUDE.md`](CLAUDE.md),
  [`AGENTS.md`](AGENTS.md), `docs/contract/`) - an engineering guardrail, not a
  product feature. Guards assert the resolved effect rather than the requested
  action, preferring an honest non-result over a silent success.

---

## Project structure

```
cuttingboard/          staged pipeline package (runtime, delivery, contract)
tests/                 pytest suite
docs/                  PRDs, architecture, decisions, process, contract
scripts/               operator helpers (pre-commit, pre-push, prd_close)
tools/                 engine_doctor, registry validator, snapshot helpers
ui/                    rendered board
pinescripts/           legacy TradingView helpers (rebuild intent noted inside)
.github/workflows/     CI and the Cuttingboard pipeline
```

---

## Now / next

Recent product work (2026-08) added the Market State panel, the GEX and Market
Movement cards, the operator context tape, and the setup chart. Current
direction centers on three balanced lanes - gamma exposure (GEX), the news /
context-registry / movement-heatmap track, and market-control context - plus a
reconciliation wave closing the Cloudflare-clock, registry, and GEX seams.
Live status and the active lane always live in
[`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md).

---

## Authorship

Author: Dustin Watson.
