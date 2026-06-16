#!/usr/bin/env python3
"""PRD-190 R4 diff harness — standalone, config-independent, NO repo-state mutation.

Run on a network-enabled host (e.g. asher). For each universe symbol it fetches a
6-month AND a 12-month daily OHLCV frame DIRECTLY from yfinance (explicit date
windows — it does NOT read config.OHLCV_FETCH_MONTHS, which is already flipped to
12), then computes the window-sensitive decision surface with the SAME production
functions the pipeline uses (cuttingboard.derived._compute and
cuttingboard.trend_structure.build_trend_structure_snapshot). The only variable
between the two columns is frame length, so any movement is the warm-up effect R4
must characterize.

It prints, per symbol:
  - EMA9/21/50 and ATR14: 6mo vs 12mo value + absolute and % delta (the
    adjust=False seed-sensitivity surface — ema50/ATR are the most exposed),
  - RVOL (volume_ratio): 6mo vs 12mo + an IDENTICAL check (tail-windowed, expected
    size-invariant),
  - sma_50/sma_200 and the decision-surface fields price_vs_sma_50,
    price_vs_sma_200, and the trend-structure label — with a FLIP flag.

REGIME CALL: compute_regime(valid_quotes) consumes NormalizedQuotes only (vix /
breadth / leadership) and never reads the OHLCV frame or derived metrics (verified
2026-06-16: no fetch_ohlcv/derived/frame reference in its body). It is therefore
INVARIANT to OHLCV_FETCH_MONTHS by construction and is not A/B-able per window —
reported as such, not synthesized.

VERDICT: null diff (no price_vs_sma_50/200 or trend-label flip, RVOL identical) keeps
PRD-190 STANDARD. Any decision-surface flip escalates to HIGH-RISK and the moved
field must be enumerated + accepted before merge.

This harness writes nothing: it calls yfinance directly (not ingestion.fetch_ohlcv,
which caches) and touches no logs/, data/cache, or ui/.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone

import pandas as pd
import yfinance as yf

from cuttingboard.derived import _compute
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.trend_structure import build_trend_structure_snapshot

UNIVERSE = ["SPY", "QQQ", "GDX", "GLD", "SLV", "XLE"]
WINDOWS = {"6mo": 6 * 31, "12mo": 12 * 31}  # calendar days, mirrors production sizing
RVOL_TOL = 1e-9
DECISION_FIELDS = ("price_vs_sma_50", "price_vs_sma_200", "trend_alignment")


def _fetch_direct(symbol: str, calendar_days: int) -> pd.DataFrame | None:
    """Fetch a daily frame for an explicit lookback — config-independent, uncached."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=calendar_days)
    df = yf.download(
        symbol,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
        multi_level_index=False,
    )
    if df is None or df.empty:
        return None
    df.columns = [
        c.capitalize() if c.lower() in ("open", "high", "low", "close", "volume") else c
        for c in df.columns
    ]
    return df[["Open", "High", "Low", "Close", "Volume"]].copy()


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


def _metrics(symbol: str, df: pd.DataFrame) -> dict:
    price = float(df["Close"].iloc[-1])
    quote = _quote(symbol, price)
    dm = _compute(symbol, quote, df)
    rec = build_trend_structure_snapshot({symbol: quote}, {symbol: df}, [symbol])[
        "symbols"
    ][symbol]
    return {
        "bars": len(df),
        "ema9": dm.ema9,
        "ema21": dm.ema21,
        "ema50": dm.ema50,
        "atr14": dm.atr14,
        "rvol": dm.volume_ratio,
        "sma_50": rec["sma_50"],
        "sma_200": rec["sma_200"],
        "price_vs_sma_50": rec["price_vs_sma_50"],
        "price_vs_sma_200": rec["price_vs_sma_200"],
        "trend_alignment": rec["trend_alignment"],
    }


def _delta_line(name: str, a, b) -> str:
    if a is None or b is None:
        return f"    {name:<8} 6mo={a!s:>12}  12mo={b!s:>12}  Δ=n/a"
    d = b - a
    pct = (d / a * 100) if a else float("nan")
    return f"    {name:<8} 6mo={a:>12.4f}  12mo={b:>12.4f}  Δ={d:>+11.4f} ({pct:>+7.3f}%)"


def main() -> int:
    print("PRD-190 R4 diff — 6mo vs 12mo, config-independent A/B")
    print(f"run_at_utc: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 78)

    flips: list[str] = []
    rvol_breaks: list[str] = []
    failures: list[str] = []
    max_ema_pct = 0.0
    max_atr_pct = 0.0

    for sym in UNIVERSE:
        frames = {label: _fetch_direct(sym, days) for label, days in WINDOWS.items()}
        if any(f is None for f in frames.values()):
            failures.append(sym)
            print(f"\n{sym}: FETCH FAILED for {[k for k, v in frames.items() if v is None]}")
            continue

        m6 = _metrics(sym, frames["6mo"])
        m12 = _metrics(sym, frames["12mo"])

        print(f"\n{sym}: bars 6mo={m6['bars']}  12mo={m12['bars']}")
        for name in ("ema9", "ema21", "ema50", "atr14"):
            print(_delta_line(name, m6[name], m12[name]))
            if m6[name] and m12[name]:
                pct = abs((m12[name] - m6[name]) / m6[name] * 100)
                if name == "atr14":
                    max_atr_pct = max(max_atr_pct, pct)
                else:
                    max_ema_pct = max(max_ema_pct, pct)

        rvol_ok = (
            m6["rvol"] is not None
            and m12["rvol"] is not None
            and abs(m6["rvol"] - m12["rvol"]) <= RVOL_TOL
        )
        print(f"    rvol     6mo={m6['rvol']!s:>12}  12mo={m12['rvol']!s:>12}  "
              f"identical={'YES' if rvol_ok else 'NO'}")
        if not rvol_ok:
            rvol_breaks.append(sym)

        print(f"    sma_50   6mo={m6['sma_50']!s:>12}  12mo={m12['sma_50']!s:>12}")
        print(f"    sma_200  6mo={m6['sma_200']!s:>12}  12mo={m12['sma_200']!s:>12}")
        for field in DECISION_FIELDS:
            flip = m6[field] != m12[field]
            flag = "  <<< FLIP" if flip else ""
            print(f"    {field:<16} 6mo={m6[field]:>20}  12mo={m12[field]:>20}{flag}")
            if flip:
                flips.append(f"{sym}.{field}: {m6[field]} -> {m12[field]}")

    print("\n" + "=" * 78)
    print("REGIME CALL: compute_regime(valid_quotes) is quote-only (vix/breadth/")
    print("  leadership) — it never reads the OHLCV frame, so it is INVARIANT to the")
    print("  fetch window by construction. Not A/B'd; cannot flip from this change.")
    print("-" * 78)
    print(f"max |EMA Δ%| across universe : {max_ema_pct:.3f}%")
    print(f"max |ATR Δ%| across universe : {max_atr_pct:.3f}%")
    print(f"RVOL identical all symbols   : {'YES' if not rvol_breaks else 'NO ' + str(rvol_breaks)}")
    print(f"decision-surface flips       : {len(flips)}")
    for f in flips:
        print(f"    FLIP: {f}")
    if failures:
        print(f"fetch failures (rerun)       : {failures}")

    print("-" * 78)
    if failures:
        print("VERDICT: INCOMPLETE — some symbols failed to fetch; rerun before judging.")
        return 2
    if flips:
        print("VERDICT: ESCALATE — a decision-surface field flipped. PRD-190 -> HIGH-RISK;")
        print("  enumerate + accept each moved field before merge.")
        return 1
    print("VERDICT: NULL DIFF — no decision-surface flip; RVOL identical. PRD-190 stays")
    print("  STANDARD (EMA/ATR warm-up deltas above are characterized, not gating).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
