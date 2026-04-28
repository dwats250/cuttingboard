# Backtesting Sandbox

This directory is for research-only backtests. It is deliberately separate from
the live `cuttingboard` package.

The current reference model is:

- Strategy logic: `algos/orb_reference.py`
- CLI runner: `backtesting/run_orb_backtest.py`
- Tests: `tests/test_orb_reference.py`
- Small fixture data: `tests/fixtures/orb_reference_sample_intraday.csv`
- Large local data: `data/backtests/` ignored by git except `.gitkeep`

## Run The Fixture

```bash
python3 backtesting/run_orb_backtest.py \
  --spy tests/fixtures/orb_reference_sample_intraday.csv \
  --pretty \
  --summary
```

## Run More Data

Put local minute-data CSVs in `data/backtests/`:

```text
data/backtests/SPY_1m.csv
data/backtests/QQQ_1m.csv
```

Then run:

```bash
python3 backtesting/run_orb_backtest.py \
  --spy data/backtests/SPY_1m.csv \
  --qqq data/backtests/QQQ_1m.csv \
  --out data/backtests/orb_trades.json \
  --pretty \
  --summary
```

Required CSV columns:

```text
timestamp,open,high,low,close,volume
```

Timestamps must be timezone-aware New York timestamps:

```text
2024-01-02T09:30:00-05:00
```

Each symbol-day must contain complete 1-minute candles from `09:30` through
`15:55`. Missing candles raise `ValueError`.

## Promotion Rule

Do not import `algos.orb_reference` from `cuttingboard/*`.

If this strategy is promoted later, create a separate PRD that explicitly
defines the production contract, runtime integration point, alert behavior,
reporting behavior, data source, and failure modes.
