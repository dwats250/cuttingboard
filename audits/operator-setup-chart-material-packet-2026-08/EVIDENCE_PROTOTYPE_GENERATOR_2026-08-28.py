"""PRD-A prototype: static SVG daily-candle setup chart for Cuttingboard.

Design study only — reads real parquet bars from the repo cache, derives demo
levels, and emits standalone HTML pages for phone-width screenshots.
"""
from __future__ import annotations

import math
import pathlib
import sys

import pandas as pd

REPO = pathlib.Path("/home/dustin/Projects/cuttingboard")
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "proto_out")
OUT.mkdir(parents=True, exist_ok=True)

# ---- palette (dashboard-consistent) ----
UP = "#4caf50"
DOWN = "#f44336"
NOW_C = "#f5c518"
ENTRY_C = "#e0a552"
STOP_C = "#e05252"
T2_C = "#3a7a8a"       # structural teal (existing zone-line colour)
VWAP_C = "#29b6f6"
T3_C = "#4a4a4a"       # faint context
LOCK_C = "#6b7280"

TIER2_TYPES = ("VWAP", "ORB_HIGH", "ORB_LOW", "PRIOR_HIGH", "PRIOR_LOW", "EMA9", "EMA21")
TIER3_TYPES = ("EMA50",)


def build_setup_chart_svg(
    bars: list[tuple[str, float, float, float, float]],
    now_price: float,
    *,
    entry: float | None = None,
    stop: float | None = None,
    zones: list[tuple[str, float]] = (),
    fibs: dict[str, float] | None = None,
    operator_locked: bool = False,
    width: int = 358,
    height: int = 232,
) -> str:
    """Deterministic inline SVG: candles + tiered levels, price tags right."""
    GUT = 78
    PAD_T, PAD_B = 8, 14
    plot_w = width - GUT
    plot_h = height - PAD_T - PAD_B
    n = len(bars)

    lows = [b[3] for b in bars]
    highs = [b[2] for b in bars]
    dom = [now_price] + lows + highs
    for v in (entry, stop):
        if v:
            dom.append(v)
    t2 = [(t, lv) for t, lv in zones if t in TIER2_TYPES]
    t3 = [(t, lv) for t, lv in zones if t in TIER3_TYPES]
    for _, lv in t2:
        dom.append(lv)
    lo, hi = min(dom), max(dom)
    pad = max((hi - lo) * 0.06, now_price * 0.001)
    lo, hi = lo - pad, hi + pad
    span = hi - lo

    def Y(p):
        return round(PAD_T + plot_h * (1.0 - (p - lo) / span), 1)

    def pct(p):
        return f"{(p - now_price) / now_price * 100.0:+.1f}%"

    ABBR = {"PRIOR_HIGH": "PDH", "PRIOR_LOW": "PDL", "ORB_HIGH": "ORB H",
            "ORB_LOW": "ORB L", "VWAP": "VWAP", "EMA9": "EMA9",
            "EMA21": "EMA21", "EMA50": "EMA50"}

    s = []
    s.append(
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        f'style="display:block;max-width:{width}px" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="monospace">'
    )
    s.append(f'<rect width="{plot_w}" height="{height}" fill="#0a0a0a"/>')

    zmap = dict(zones)
    risk_fill = LOCK_C if operator_locked else STOP_C
    if entry and stop:
        y0, y1 = sorted((Y(entry), Y(stop)))
        s.append(f'<rect x="0" y="{y0}" width="{plot_w}" height="{max(y1 - y0, 1):.1f}" fill="{risk_fill}" opacity="0.09"/>')
    if "ORB_HIGH" in zmap and "ORB_LOW" in zmap:
        y0, y1 = sorted((Y(zmap["ORB_HIGH"]), Y(zmap["ORB_LOW"])))
        s.append(f'<rect x="0" y="{y0}" width="{plot_w}" height="{max(y1 - y0, 1):.1f}" fill="{T2_C}" opacity="0.10"/>')

    # gutter items: (y, text, colour, size, bold, tag)  tag=True -> boxed
    items = []
    if fibs:
        for lbl, lv in sorted(fibs.items(), key=lambda kv: -kv[1]):
            if lo < lv < hi:
                y = Y(lv)
                s.append(f'<line x1="0" y1="{y}" x2="{plot_w}" y2="{y}" stroke="{T3_C}" stroke-width="0.75" stroke-dasharray="2,4"/>')
                items.append([y, f"fib {lbl.lstrip(chr(48)) if lbl.startswith(chr(48)) else lbl} {lv:,.1f}", "#555", 7.5, False, False])
    for t, lv in t3:
        if lo < lv < hi:
            y = Y(lv)
            s.append(f'<line x1="0" y1="{y}" x2="{plot_w}" y2="{y}" stroke="{T3_C}" stroke-width="0.75" stroke-dasharray="2,4"/>')
            items.append([y, f"{ABBR.get(t, t)} {lv:,.1f}", "#555", 7.5, False, False])
    for t, lv in t2:
        y = Y(lv)
        if t == "VWAP":
            s.append(f'<line x1="0" y1="{y}" x2="{plot_w}" y2="{y}" stroke="{VWAP_C}" stroke-width="1" stroke-dasharray="4,2" opacity="0.75"/>')
            items.append([y, f"VWAP {lv:,.1f}", VWAP_C, 8.5, False, False])
        else:
            s.append(f'<line x1="0" y1="{y}" x2="{plot_w}" y2="{y}" stroke="{T2_C}" stroke-width="1" opacity="0.8"/>')
            items.append([y, f"{ABBR.get(t, t)} {lv:,.1f}", T2_C, 8.5, False, False])

    slot = plot_w / max(n, 1)
    bw = max(min(slot * 0.62, 9.0), 1.5)
    for i, (_, o, h, l, c) in enumerate(bars):
        cx = round(slot * (i + 0.5), 1)
        colour = UP if c >= o else DOWN
        s.append(f'<line x1="{cx}" y1="{Y(h)}" x2="{cx}" y2="{Y(l)}" stroke="{colour}" stroke-width="1"/>')
        top, bot = Y(max(o, c)), Y(min(o, c))
        s.append(f'<rect x="{cx - bw / 2:.1f}" y="{top}" width="{bw:.1f}" height="{max(bot - top, 1):.1f}" fill="{colour}"/>')

    entry_c = LOCK_C if operator_locked else ENTRY_C
    stop_c = LOCK_C if operator_locked else STOP_C
    entry_word = "LEVEL" if operator_locked else "ENTRY"
    stop_word = "INVALIDATION" if operator_locked else "STOP"
    if stop:
        y = Y(stop)
        s.append(f'<line x1="0" y1="{y}" x2="{plot_w}" y2="{y}" stroke="{stop_c}" stroke-width="1.5" stroke-dasharray="5,3"/>')
        s.append(f'<text x="4" y="{y - 3}" font-size="8" font-weight="bold" fill="{stop_c}">{stop_word} {pct(stop)}</text>')
        items.append([y, f"{stop:,.2f}", stop_c, 9, True, True])
    if entry and abs(entry - now_price) >= 0.005:
        y = Y(entry)
        s.append(f'<line x1="0" y1="{y}" x2="{plot_w}" y2="{y}" stroke="{entry_c}" stroke-width="1.5"/>')
        s.append(f'<text x="4" y="{y - 3}" font-size="8" font-weight="bold" fill="{entry_c}">{entry_word} {pct(entry)}</text>')
        items.append([y, f"{entry:,.2f}", entry_c, 9, True, True])
    now_y = Y(now_price)
    s.append(f'<line x1="0" y1="{now_y}" x2="{plot_w}" y2="{now_y}" stroke="{NOW_C}" stroke-width="1.75"/>')

    # --- gutter layout: NOW tag fixed; others pushed away from it, order kept.
    # Height-aware: a boxed tag needs more clearance than a bare text line. ---
    def _h(it):
        return 15.0 if it[5] else it[3] + 3.0
    NOW_H = 15.0
    above = sorted([it for it in items if it[0] <= now_y], key=lambda it: -it[0])
    below = sorted([it for it in items if it[0] > now_y], key=lambda it: it[0])
    placed = []
    prev_edge = now_y - NOW_H / 2          # top edge of the NOW tag
    for it in above:
        yy = min(it[0], prev_edge - _h(it) / 2)
        yy = max(yy, PAD_T + 2)
        placed.append((yy, it))
        prev_edge = yy - _h(it) / 2
    prev_edge = now_y + NOW_H / 2
    for it in below:
        yy = max(it[0], prev_edge + _h(it) / 2)
        yy = min(yy, height - 4)
        placed.append((yy, it))
        prev_edge = yy + _h(it) / 2

    s.append(f'<rect x="{plot_w - 1}" y="{now_y - 7}" width="{GUT - 1}" height="14" fill="{NOW_C}"/>')
    s.append(f'<text x="{plot_w + 3}" y="{now_y + 3.5}" font-size="9.5" font-weight="bold" fill="#0a0a0a">NOW {now_price:,.2f}</text>')

    for yy, (ly, text, colour, size, bold, tag) in placed:
        if abs(yy - ly) > 4:
            s.append(f'<line x1="{plot_w}" y1="{ly}" x2="{plot_w + 2}" y2="{yy}" stroke="#333" stroke-width="0.75"/>')
        by = yy + size * 0.38
        if tag:
            s.append(f'<rect x="{plot_w + 1}" y="{yy - 6.5}" width="{GUT - 4}" height="13" fill="#0a0a0a" stroke="{colour}" stroke-width="0.75" rx="1.5"/>')
        w_attr = ' font-weight="bold"' if bold else ""
        s.append(f'<text x="{plot_w + 4}" y="{by:.1f}" font-size="{size}"{w_attr} fill="{colour}">{text}</text>')

    if bars:
        s.append(f'<text x="2" y="{height - 3}" font-size="7.5" fill="#666">{bars[0][0]}</text>')
        s.append(f'<text x="{plot_w - 4}" y="{height - 3}" font-size="7.5" fill="#666" text-anchor="end">{bars[-1][0]}</text>')
    s.append("</svg>")
    return "".join(s)


# ---------------------------------------------------------------- demo build
def load_bars(sym: str, n: int = 32) -> tuple[list, pd.DataFrame]:
    df = pd.read_parquet(REPO / f"data/cache/{sym}_ohlcv.parquet").tail(n + 1)
    bars = [
        (idx.strftime("%b %d"), round(r.Open, 2), round(r.High, 2), round(r.Low, 2), round(r.Close, 2))
        for idx, r in df.iterrows()
    ]
    return bars, df


def ema(df: pd.DataFrame, n: int) -> float:
    return float(df["Close"].ewm(span=n, adjust=False).mean().iloc[-1])


def page(title: str, charts: list[tuple[str, str, str]]) -> str:
    blocks = "".join(
        f'<div class="card"><div class="hdr">{h}</div><div class="sub">{sub}</div>{svg}</div>'
        for h, sub, svg in charts
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "<style>*{box-sizing:border-box;margin:0;padding:0}"
        "body{background:#0d0d0d;color:#e0e0e0;font-family:monospace;padding:8px}"
        ".card{background:#101010;border:1px solid #2a2a2a;border-radius:4px;padding:10px;margin-bottom:8px}"
        ".hdr{font-weight:bold;margin-bottom:2px}"
        ".sub{color:#888;font-size:.72rem;margin-bottom:8px}"
        "</style></head><body>" + blocks + "</body></html>"
    )


if __name__ == "__main__":
    spy_bars, spy = load_bars("SPY")
    qqq_bars, qqq = load_bars("QQQ")
    now_spy = round(float(spy["Close"].iloc[-1]) + 1.4, 2)   # demo live tick above last close
    now_qqq = round(float(qqq["Close"].iloc[-1]) - 2.1, 2)

    # variant 1: bullish SPY setup — entry above, stop below, EMA structure + fibs
    fibs_spy = {"0.382": 747.95, "0.5": 744.11, "0.618": 740.27}
    v1 = build_setup_chart_svg(
        spy_bars[-32:], now_spy,
        entry=round(now_spy * 1.004, 2), stop=round(now_spy * 0.988, 2),
        zones=[("EMA9", ema(spy, 9)), ("EMA21", ema(spy, 21)), ("EMA50", ema(spy, 50)),
               ("PRIOR_HIGH", round(float(spy["High"].iloc[-2]), 2)),
               ("PRIOR_LOW", round(float(spy["Low"].iloc[-2]), 2))],
        fibs=fibs_spy,
    )
    # variant 2: dense-level case + ORB band + VWAP
    v2 = build_setup_chart_svg(
        qqq_bars[-32:], now_qqq,
        entry=round(now_qqq * 1.006, 2), stop=round(now_qqq * 0.985, 2),
        zones=[("VWAP", round(now_qqq * 0.998, 2)),
               ("ORB_HIGH", round(now_qqq * 1.003, 2)), ("ORB_LOW", round(now_qqq * 0.994, 2)),
               ("EMA9", ema(qqq, 9)), ("EMA21", ema(qqq, 21)), ("EMA50", ema(qqq, 50)),
               ("PRIOR_HIGH", round(float(qqq["High"].iloc[-2]), 2)),
               ("PRIOR_LOW", round(float(qqq["Low"].iloc[-2]), 2))],
        fibs={"0.382": round(now_qqq * 0.991, 2), "0.5": round(now_qqq * 0.987, 2), "0.618": round(now_qqq * 0.983, 2)},
    )
    # variant 3: operator-locked (neutralized) view of variant 1
    v3 = build_setup_chart_svg(
        spy_bars[-32:], now_spy,
        entry=round(now_spy * 1.004, 2), stop=round(now_spy * 0.988, 2),
        zones=[("EMA9", ema(spy, 9)), ("EMA21", ema(spy, 21))],
        fibs=fibs_spy, operator_locked=True,
    )
    # variant 4: sparse — no contract, levels only (observation)
    v4 = build_setup_chart_svg(
        spy_bars[-32:], now_spy,
        zones=[("EMA9", ema(spy, 9)), ("EMA21", ema(spy, 21)), ("EMA50", ema(spy, 50))],
        fibs=fibs_spy,
    )

    html = page("proto", [
        ("SPY — A · LONG · TRENDING UP", "setup chart · 32 completed daily bars · demo levels", v1),
        ("QQQ — A- · LONG · dense levels + ORB band", "setup chart · 32 completed daily bars · demo levels", v2),
        ("SPY — OBSERVATION ONLY (operator locked)", "neutralized palette · same facts", v3),
        ("SPY — no active contract (levels only)", "observation chart", v4),
    ])
    (OUT / "proto.html").write_text(html)
    print("wrote", OUT / "proto.html")
