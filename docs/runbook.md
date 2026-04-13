# Cuttingboard — Operations Runbook

## Daily Rhythm

| Time (UTC) | Day | Event |
|------------|-----|-------|
| 13:00 | Mon–Fri | Live run fires (GHA or cron) |
| 13:05 | Mon–Fri | Verify run fires — confirms artifact is valid |
| 13:01–13:06 | Mon–Fri | Report committed to `reports/YYYY-MM-DD.md` (GHA) |
| 13:01–13:06 | Mon–Fri | ntfy alert delivered (if configured) |
| 14:00–21:30 | Mon–Fri | Intraday monitor runs every 30 minutes |
| 10:00 | Sunday | Sunday regime report fires (no trade candidates) |

Confirm the run succeeded by checking `logs/latest_run.json` → `status: SUCCESS`. If status is FAIL or the file is missing, inspect GitHub Actions logs or run verify manually.

---

## Reading the Morning Report

The report has four sections. Here's how to read each one.

### Header

```
══════════════════════════════════════════════════════
  CUTTINGBOARD  ·  2026-04-14
  RISK_ON / AGGRESSIVE_LONG  |  conf=0.75  |  net=+6
══════════════════════════════════════════════════════
```

- **Regime:** The macro state — RISK_ON, RISK_OFF, NEUTRAL, or CHAOTIC.
- **Posture:** The trading posture — what you can do today (see table below).
- **conf=:** Confidence in the regime. `abs(net_score) / total_votes`. Below 0.50 → STAY_FLAT regardless of regime.
- **net=:** Risk-on votes minus risk-off votes. Range: −8 to +8.

### Posture Quick Reference

| Posture | Meaning | Action |
|---------|---------|--------|
| `AGGRESSIVE_LONG` | RISK_ON + conf ≥ 0.75 | Full position size, all qualified longs |
| `CONTROLLED_LONG` | RISK_ON + 0.55 ≤ conf < 0.75 | Reduced size or selective entries |
| `DEFENSIVE_SHORT` | RISK_OFF + conf ≥ 0.55 | Qualified short setups only |
| `NEUTRAL_PREMIUM` | NEUTRAL + VIX 18–25 | Defined-risk only; direction comes from `net_score` |
| `STAY_FLAT` | Anything else | Do not trade. No exceptions. |

**When posture is STAY_FLAT:** The pipeline short-circuits before evaluating any symbol. Zero trades, zero watchlist. The report shows:

```
  NO TRADE
  Reason: STAY_FLAT posture (regime=NEUTRAL, confidence=0.12)
```

This is normal. It happens most days. The system is being conservative by design.

### Trades Section

```
  TRADES  (2)
  ──────────────────────────────────────────────────
  SPY     BULL_CALL_SPREAD    TREND / LOW_IV
             1_ITM / ATM   ·  $5.00 wide  ·  21 DTE
             1 contract  ·  max risk $150
             Exit: +50% profit or full debit loss

  QQQ     BULL_CALL_SPREAD    TREND / LOW_IV
             1_ITM / ATM   ·  $5.00 wide  ·  14 DTE
             1 contract  ·  max risk $150
             Exit: +50% profit or full debit loss
```

Each trade block tells you:
- **Symbol + strategy:** What kind of spread to put on.
- **Structure / IV:** Why this strategy was selected (see options_framework.md).
- **Strike labels:** Relative to current price. 1_ITM = one strike in the money. ATM = at the money.
- **Strike width:** Distance between the two strikes in underlying price points.
- **DTE:** Target days to expiry. Find the nearest weekly expiry at or above this number.
- **Contracts / max risk:** Never risk more than this. The dollar amount is the maximum possible loss if the spread expires worthless.
- **Exit rules:** Non-negotiable. Set the order at entry.

**Strike selection in practice:** 1_ITM / ATM for a BULL_CALL_SPREAD means buy the call one strike below current price (ITM), sell the call at the current price (ATM). Adjust to the nearest $1 strike increment available.

### Watchlist Section

```
  WATCHLIST  (1)
  ──────────────────────────────────────────────────
  NVDA    R:R 1.8 below 2.0 minimum
```

Watchlist symbols passed all hard gates but failed exactly one soft gate. They are **not trades today.** They are worth monitoring. The reason tells you exactly what needs to change:

- **R:R below minimum:** Target is too close. Wait for a better setup or let the stock move.
- **Stop distance below 1%:** The stop is too tight. Wait for a wider ATR day.
- **Earnings within 5 calendar days:** Wait until after earnings to enter.
- **Stop below 0.5× ATR14:** Structure isn't clean enough. Pass.

### Excluded Section

```
  EXCLUDED  (8)
  ──────────────────────────────────────────────────
  AAPL    CHOP
  GLD     direction mismatch: SHORT vs regime LONG
  IWM     CHOP
  ...
```

Excluded symbols failed a hard gate or were filtered before qualification:
- **CHOP:** EMA alignment is broken or price is outside the tradeable zone. No setup is valid.
- **direction mismatch:** The symbol's candidate direction conflicts with the current regime. Normal in a RISK_ON regime when a symbol is in a downtrend.

### Data Status Footer

```
  Validated : 20 / 20    VIX : 19.2
  Run       : 2026-04-14T13:00:42Z
```

- **20 / 20:** All symbols validated. Any number below the total means some symbols failed validation (see `logs/audit.jsonl` for which ones and why).
- **VIX:** Current VIX level. This drives the IV environment classification and NEUTRAL_PREMIUM eligibility.

---

## Understanding Regime States

### Why the regime changes day to day

The regime is computed fresh on every run from current market data. It is not a rolling average — it reflects conditions right now. A single large VIX move can flip the regime from RISK_ON to CHAOTIC in one run.

### CHAOTIC regime

CHAOTIC overrides everything. It fires when VIX pct_change (single interval) exceeds 15%. This detects flash crashes and gap events. During CHAOTIC:
- Posture is always STAY_FLAT
- No trades evaluated
- Intraday monitor sends an immediate ntfy alert

If you see CHAOTIC on a morning report: do not trade. Wait for the next day's premarket run to confirm conditions have stabilized.

### NEUTRAL regime

NEUTRAL means the vote model is mixed but still active.

- `net_score > 0` during NEUTRAL → LONG candidates
- `net_score < 0` during NEUTRAL → SHORT candidates
- `net_score = 0` during NEUTRAL → no directional trade
- NEUTRAL trades must clear the stricter `R:R >= 3.0` gate
- `VIX 18–25` during NEUTRAL → `NEUTRAL_PREMIUM`
- `VIX < 18` or `VIX > 25` during NEUTRAL → `STAY_FLAT`

`TRANSITION` remains as a legacy constant in code, but it is not returned by the engine.

---

## What To Do When the System HALTS

A HALT means a required market data symbol failed validation. The report will look like:

```
══════════════════════════════════════════════════════
  CUTTINGBOARD  ·  2026-04-14
  ⚠  SYSTEM HALT
══════════════════════════════════════════════════════

  HALT — MACRO DATA INVALID
  Failed: ^VIX (price 0.0 is not positive)
```

**Immediate response: Do not trade.** The regime, structure, and qualification layers never ran. Any trade assessment from today is invalid.

**Diagnosis steps:**

1. Check which symbol failed:
   ```bash
   tail -1 logs/audit.jsonl | python3 -m json.tool | grep halt
   ```

2. Check if it's a data source issue:
   ```bash
   python3 -c "
   from cuttingboard.ingestion import fetch_quote
   r = fetch_quote('^VIX')
   print(r.fetch_succeeded, r.failure_reason, r.price)
   "
   ```

3. Common HALT causes and fixes:

   | Symbol | Common Cause | Fix |
   |--------|-------------|-----|
   | `^VIX` | yfinance outage | Wait for yfinance to recover; no fallback |
   | `DX-Y.NYB` | yfinance symbol rename | Check Yahoo Finance for new DXY ticker |
   | `^TNX` | Market holiday / weekend data | Expected if run outside market hours |
   | `SPY`, `QQQ` | Price outside bounds | Update `PRICE_BOUNDS` in `config.py` if price has legitimately moved out of range |

4. If it's a price bounds issue (price moved beyond configured range), update `config.py`:
   ```python
   PRICE_BOUNDS: dict[str, tuple[float, float]] = {
       "SPY": (300, 1000),  # expanded upper bound
       ...
   }
   ```

5. Trigger a manual run after fixing:
   ```
   GitHub → Actions → Cuttingboard Pipeline → Run workflow → mode: premarket
   ```

---

## Local Automation (Cron)

### Quick setup

```bash
chmod +x run_daily.sh
```

`run_daily.sh` runs live then verify in sequence. On Sunday it auto-converts to sunday mode (regime-only, no candidates). Exit code is 0 on PASS, 1 on any failure.

### Cron entries

Add to `crontab -e`. Replace `/home/user/cuttingboard` and `.venv` with your actual paths.

```cron
# Premarket live + verify — 06:00 PT (13:00 UTC), Monday–Friday
0 13 * * 1-5  cd /home/user/cuttingboard && .venv/bin/python -m cuttingboard --mode live && .venv/bin/python -m cuttingboard --mode verify >> logs/cron.log 2>&1

# Or via the helper script:
# 0 13 * * 1-5  cd /home/user/cuttingboard && ./run_daily.sh >> logs/cron.log 2>&1

# Verify-only run 5 minutes later (belt-and-suspenders):
# 5 13 * * 1-5  cd /home/user/cuttingboard && .venv/bin/python -m cuttingboard --mode verify >> logs/cron.log 2>&1

# Sunday regime report — 10:00 UTC
0 10 * * 0    cd /home/user/cuttingboard && .venv/bin/python -m cuttingboard --mode sunday && .venv/bin/python -m cuttingboard --mode verify >> logs/cron.log 2>&1
```

**Rules:**
- Run from project root (`cd` before any command)
- Use the full venv path — cron does not inherit your shell's `PATH`
- Redirect stdout and stderr to `logs/cron.log` so failures leave a trace

### Detecting failures locally

```bash
# Did the last run pass?
python -m cuttingboard --mode verify

# What did the last cron run do?
tail -50 logs/cron.log

# What is the current run state?
python3 -c "import json; s=json.load(open('logs/latest_run.json')); print(s['status'], s['regime'], s['posture'])"
```

A non-zero exit from any cron command is logged by the system. On Linux:

```bash
# Check for cron failures in system mail or syslog:
grep CRON /var/log/syslog | grep -i fail | tail -10
```

---

## Triggering a Manual Run

### From GitHub Actions UI

1. Go to the repository on GitHub
2. Click **Actions** → **Cuttingboard Pipeline**
3. Click **Run workflow** (top right)
4. Select `mode`: `live`, `sunday`, `verify`, or `intraday`
5. Click **Run workflow**

### From the command line (local)

```bash
cd ~/cuttingboard
source .venv/bin/activate

# Default live run
python -m cuttingboard

# Deterministic fixture run
python -m cuttingboard --mode fixture --fixture-file tests/fixtures/2026-04-12.json

# Sunday regime-only run
python -m cuttingboard --mode sunday

# Verification only
python -m cuttingboard --mode verify

# Verification against a specific summary file
python -m cuttingboard --mode verify --file logs/run_2026-04-12_130000.json
```

The CLI supports four modes: `live`, `fixture`, `sunday`, and `verify`.
`--fixture-file PATH` selects the JSON fixture for fixture mode.
`--file PATH` selects which summary verify mode checks. Without `--file`, verify mode reads `logs/latest_run.json`.

`logs/latest_run.json` is the machine-readable source of truth for the most recent run. `reports/YYYY-MM-DD.md` is the human-readable report. HTML output is not generated.

### Inspecting output without writing files

```bash
python3 -c "
import logging; logging.disable(logging.WARNING)
from cuttingboard.ingestion import fetch_all
from cuttingboard.normalization import normalize_all
from cuttingboard.validation import validate_quotes
from cuttingboard.derived import compute_all_derived
from cuttingboard.regime import compute_regime, print_regime_report
from cuttingboard.structure import classify_all_structure
from cuttingboard.qualification import qualify_all, print_qualification_summary

raw    = fetch_all()
normed = normalize_all(raw)
val    = validate_quotes(normed)
regime = compute_regime(val.valid_quotes)
dm     = compute_all_derived(val.valid_quotes)
struct = classify_all_structure(val.valid_quotes, dm, regime.vix_level)
qual   = qualify_all(regime, struct)

print_regime_report(regime)
print_qualification_summary(qual, regime)
"
```

---

## Reading audit.jsonl

Every run appends one JSON record to `logs/audit.jsonl`. It is the ground truth of system history.

### View the most recent run

```bash
tail -1 logs/audit.jsonl | python3 -m json.tool
```

### Most recent 5 runs — outcome and regime

```bash
tail -5 logs/audit.jsonl | while read line; do
  echo "$line" | python3 -c "
import json, sys
r = json.load(sys.stdin)
print(f\"{r['date']}  {r['outcome']:<10}  {r['regime']:<12}  conf={r['confidence']:.2f}  trades={r['symbols_qualified']}\")
"
done
```

### All TRADE days in the last 30 records

```bash
tail -30 logs/audit.jsonl | grep '"outcome": "TRADE"' | python3 -c "
import json, sys
for line in sys.stdin:
    r = json.loads(line)
    tickers = [t['symbol'] for t in r.get('qualified_trades', [])]
    print(f\"{r['date']}  {', '.join(tickers)}\")
"
```

### All HALT events

```bash
grep '"outcome": "HALT"' logs/audit.jsonl | python3 -c "
import json, sys
for line in sys.stdin:
    r = json.loads(line)
    print(f\"{r['date']}  {r['halt_reason']}\")
"
```

### Check for ntfy delivery gaps

```bash
grep '"ntfy_sent": false' logs/audit.jsonl | wc -l
```

### With `jq` (if installed)

```bash
# Most recent run
tail -1 logs/audit.jsonl | jq '{date, outcome, regime, posture, confidence}'

# All TRADE days
jq 'select(.outcome == "TRADE") | {date, qualified_trades: [.qualified_trades[].symbol]}' logs/audit.jsonl

# Regime history
jq -r '[.date, .regime, .posture, (.confidence | tostring)] | join("  ")' logs/audit.jsonl | tail -20

# Watchlist symbols over time
jq -r 'select(.watchlist | length > 0) | .date + ": " + ([.watchlist[].symbol] | join(", "))' logs/audit.jsonl
```

---

## Reading intraday_state.json

```bash
cat logs/intraday_state.json
```

Key fields:

| Field | Meaning |
|-------|---------|
| `last_regime` | Regime at the most recent intraday run |
| `last_posture` | Posture at the most recent intraday run |
| `last_run_at_utc` | Timestamp of the most recent intraday run |
| `last_alert_at_utc` | Timestamp of the most recent ntfy alert |
| `last_alert_type` | What triggered the most recent alert (CHAOTIC / REGIME_SHIFT / VIX_SPIKE) |

If `last_alert_at_utc` is recent and no alert was received, check `ntfy_sent` in the audit log — ntfy may not be configured.

---

## Common Issues

### "No report in reports/ for today"

The premarket run did not commit. Check:
1. GitHub Actions → Cuttingboard Pipeline → today's run → logs
2. If the run failed at the git commit/push step, the report still exists in the workflow artifact. Download it from the Actions run.

### "Audit record missing for a run"

`audit.jsonl` is written before the git commit. If the commit failed but the run succeeded, the record exists locally on the runner but wasn't pushed. Check the workflow logs.

### "ntfy not delivering"

1. Verify ntfy settings in `.env` (local) or GitHub Secrets (CI):
   ```bash
   python3 -c "from cuttingboard import config; print(bool(config.NTFY_TOPIC), bool(config.NTFY_URL))"
   ```
2. Test ntfy delivery manually:
   ```bash
   python3 -c "
   from cuttingboard.output import send_ntfy
   ok = send_ntfy('Test message from Cuttingboard', '2026-01-01', 'NO_TRADE')
   print('Delivered:', ok)
   "
   ```

### "Price bounds validation failure after a large market move"

If SPY reaches a new all-time high outside the configured bounds, validation will fail. Update `PRICE_BOUNDS` in `config.py`, commit, and re-run. The bounds are sanity checks — they should be wide enough to accommodate normal multi-year price ranges.
