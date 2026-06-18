"""PRD-190 R4 GATE — live 6mo-vs-12mo EMA/ATR/SMA pre/post diff.

Transient, throwaway. Not part of PRD-190's shipped FILES; added to run the
R4 decision-surface gate on a GitHub runner (which has yahoo egress) and
removed immediately after. Reuses the production compute paths
(trend_structure._build_record, derived._compute) so the diff is faithful.

GATE (per PRD-190 R4 + the closeout instruction):
  - sma_200 must flip null (pre) -> populated (post) for all symbols.
  - sma_50, ema9/21/50, atr14 stable to sub-display-precision (longer warmup,
    same converged current-bar values).
  - price_vs_sma_50 must NOT flip ABOVE<->BELOW.
Exit 0 if clean, 1 if any decision-surface metric moves materially.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pandas as pd
import yfinance as yf

from cuttingboard import config
from cuttingboard.derived import _compute
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.trend_structure import _build_record

# Relative tolerance for "sub-display-precision" stability on EMA/ATR.
EMA_ATR_REL_TOL = 1e-3      # 0.1%
SMA50_REL_TOL = 1e-6        # sma_50 is tail(50) of the same last bars -> identical


def _flatten(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = df.columns.get_level_values(0)
    return df


def _quote(symbol: str, price: float) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=0.0,
        volume=1_000_000.0,
        fetched_at_utc=datetime.now(timezone.utc),
        source="yfinance",
        units="usd_price",
        age_seconds=10.0,
    )


def _window(df: pd.DataFrame, months: int) -> pd.DataFrame:
    """Mirror ingestion.py: start_date = end - months*31 calendar days."""
    end = df.index[-1]
    start = end - timedelta(days=months * 31)
    return df.loc[df.index >= start]


def _rel(pre: float, post: float) -> float:
    if pre == 0:
        return 0.0 if post == 0 else float("inf")
    return abs(post - pre) / abs(pre)


def main() -> int:
    symbols = list(config.TREND_STRUCTURE_SYMBOLS)
    print(f"PRD-190 R4 diff — symbols={symbols}")
    print(f"pre=OHLCV_FETCH_MONTHS-equivalent 6mo, post=12mo; "
          f"current config value={config.OHLCV_FETCH_MONTHS}\n")

    failures: list[str] = []
    hdr = (f"{'symbol':<6} {'bars(6/12)':>11} {'sma50 Δ%':>9} "
           f"{'sma200 pre→post':>18} {'p_vs_sma50':>16} "
           f"{'ema9 Δ%':>8} {'ema21 Δ%':>8} {'ema50 Δ%':>8} {'atr14 Δ%':>8}")
    print(hdr)
    print("-" * len(hdr))

    for sym in symbols:
        raw = yf.download(sym, period="2y", interval="1d",
                          progress=False, auto_adjust=True)
        if raw is None or len(raw) == 0:
            failures.append(f"{sym}: no data returned from yfinance")
            print(f"{sym:<6} NO DATA")
            continue
        df = _flatten(raw)
        price = float(df["Close"].iloc[-1])
        q = _quote(sym, price)

        pre_df, post_df = _window(df, 6), _window(df, 12)
        pre_t, post_t = _build_record(sym, q, pre_df), _build_record(sym, q, post_df)
        pre_d, post_d = _compute(sym, q, pre_df), _compute(sym, q, post_df)

        # --- gate checks ---
        # sma_200 intended flip
        if pre_t["sma_200"] is not None:
            failures.append(f"{sym}: pre sma_200 unexpectedly populated "
                            f"(6mo window already >=200 bars?)")
        if post_t["sma_200"] is None:
            failures.append(f"{sym}: post sma_200 still null (12mo <200 bars)")
        # sma_50 must be identical
        sma50_delta = _rel(pre_t["sma_50"], post_t["sma_50"])
        if sma50_delta > SMA50_REL_TOL:
            failures.append(f"{sym}: sma_50 moved {sma50_delta:.2%} (>{SMA50_REL_TOL})")
        # price_vs_sma_50 must not flip
        if pre_t["price_vs_sma_50"] != post_t["price_vs_sma_50"]:
            failures.append(f"{sym}: price_vs_sma_50 flipped "
                            f"{pre_t['price_vs_sma_50']} -> {post_t['price_vs_sma_50']}")
        # ema/atr stability
        deltas = {
            "ema9": _rel(pre_d.ema9, post_d.ema9),
            "ema21": _rel(pre_d.ema21, post_d.ema21),
            "ema50": _rel(pre_d.ema50, post_d.ema50),
            "atr14": _rel(pre_d.atr14, post_d.atr14),
        }
        for name, d in deltas.items():
            if d > EMA_ATR_REL_TOL:
                failures.append(f"{sym}: {name} moved {d:.3%} (>{EMA_ATR_REL_TOL:.1%})")

        post_sma200 = post_t["sma_200"]
        sma200_cell = f"{pre_t['sma_200']}→" + (
            f"{post_sma200:.2f}" if post_sma200 is not None else "None")
        p50_cell = f"{pre_t['price_vs_sma_50']}/{post_t['price_vs_sma_50']}"
        bars_cell = f"{len(pre_df)}/{len(post_df)}"
        print(f"{sym:<6} {bars_cell:>11} {sma50_delta:>8.4%} "
              f"{sma200_cell:>18} {p50_cell:>16} "
              f"{deltas['ema9']:>7.3%} {deltas['ema21']:>7.3%} "
              f"{deltas['ema50']:>7.3%} {deltas['atr14']:>7.3%}")

    print()
    if failures:
        print("R4 GATE: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("R4 GATE: CLEAN — sma_200 flips null→populated; "
          "sma_50/EMA/ATR stable to sub-display-precision; no price_vs_sma_50 flip.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
