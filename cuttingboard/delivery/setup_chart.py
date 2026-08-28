"""PRD-321: deterministic operator setup chart — daily candles + tiered levels.

Pure presentation. One public function, no I/O, no clock, no randomness, and no
import from decision code (`cuttingboard.runtime`, `cuttingboard.market_map`) or
any network/clock module. Every rendered price traces to an input: the module
computes nothing but geometry and the existing PRD-221/222 signed % distance
from the NOW anchor.

Tier map is FIXED and CLOSED (owner ruling Q4 — no text-mining, no inference):
Tier 1 = NOW (boxed right-edge tag) + contract ENTRY/STOP, whose span shades as
the PRD-223 risk zone and which carry bold in-plot word labels (PRD-304 lock
neutralizes those to LEVEL / INVALIDATION in the neutral grey); Tier 2 = VWAP,
ORB_HIGH/ORB_LOW (band when both), PRIOR_HIGH/PRIOR_LOW, EMA9, EMA21; Tier 3 =
EMA50 and fib retracements, drawn only when already inside the price domain.
The y-domain comes from the bars, the NOW anchor, the contract pair and Tier 2
ONLY — Tier 3 is context and never widens the scale.
"""
from __future__ import annotations

import html as _html
import math
from collections.abc import Mapping, Sequence

__all__ = ["render_setup_chart_svg", "TIER2_TYPES", "TIER3_TYPES",
           "CHART_WIDTH", "CHART_HEIGHT"]

# --- palette (dashboard-consistent; mirrors the ladder/prototype colours) ---
_UP = "#4caf50"
_DOWN = "#f44336"
_NOW_C = "#f5c518"
_ENTRY_C = "#e0a552"
_STOP_C = "#e05252"
_T2_C = "#3a7a8a"
_VWAP_C = "#29b6f6"
_T3_C = "#4a4a4a"
_T3_TEXT = "#555"
_LOCK_C = "#6b7280"
_BG = "#0a0a0a"

TIER2_TYPES: tuple[str, ...] = (
    "VWAP", "ORB_HIGH", "ORB_LOW", "PRIOR_HIGH", "PRIOR_LOW", "EMA9", "EMA21",
)
TIER3_TYPES: tuple[str, ...] = ("EMA50",)

_ABBR: dict[str, str] = {
    "VWAP": "VWAP", "ORB_HIGH": "ORB H", "ORB_LOW": "ORB L",
    "PRIOR_HIGH": "PDH", "PRIOR_LOW": "PDL",
    "EMA9": "EMA9", "EMA21": "EMA21", "EMA50": "EMA50",
}

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun",
           "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

CHART_WIDTH = 358
CHART_HEIGHT = 232
_GUTTER = 78
_PAD_T = 8
_PAD_B = 14
MAX_BARS = 40


def _fin(value: object) -> float | None:
    """Finite positive float or None. Bools are never prices."""
    if value is None or isinstance(value, bool):
        return None
    try:
        num = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return num if math.isfinite(num) and num > 0 else None


def _day_label(raw: object) -> str:
    """`2026-08-27` -> `Aug 27`. Pure string work — no clock, no parsing lib."""
    text = str(raw)
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        try:
            month = int(text[5:7])
        except ValueError:
            return _html.escape(text[:10], quote=True)
        if 1 <= month <= 12:
            return f"{_MONTHS[month - 1]} {text[8:10]}"
    return _html.escape(text[:10], quote=True)


def _normalize_bars(bars: object) -> list[tuple[str, float, float, float, float]]:
    """Keep only complete, finite OHLC rows. Never synthesize or pad a candle."""
    rows: list[tuple[str, float, float, float, float]] = []
    if not isinstance(bars, Sequence) or isinstance(bars, (str, bytes)):
        return rows
    for bar in bars:
        if isinstance(bar, (str, bytes)) or not isinstance(bar, Sequence) or len(bar) < 5:
            continue
        o, h, low, c = (_fin(bar[1]), _fin(bar[2]), _fin(bar[3]), _fin(bar[4]))
        if None in (o, h, low, c):
            continue
        rows.append((_day_label(bar[0]), o, h, low, c))  # type: ignore[arg-type]
    return rows[-MAX_BARS:]


def _tiered_zones(watch_zones: object) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """Split watch zones into the FIXED Tier-2 / Tier-3 sets, input order kept."""
    tier2: list[tuple[str, float]] = []
    tier3: list[tuple[str, float]] = []
    if not isinstance(watch_zones, Sequence) or isinstance(watch_zones, (str, bytes)):
        return tier2, tier3
    for zone in watch_zones:
        if not isinstance(zone, Mapping):
            continue
        ztype = str(zone.get("type") or "")
        level = _fin(zone.get("level"))
        if level is None:
            continue
        if ztype in TIER2_TYPES:
            tier2.append((ztype, level))
        elif ztype in TIER3_TYPES:
            tier3.append((ztype, level))
    return tier2, tier3


def _fib_items(fib_levels: object) -> list[tuple[str, float]]:
    """Retracements only, sorted high->low for deterministic emission order."""
    items: list[tuple[str, float]] = []
    if not isinstance(fib_levels, Mapping):
        return items
    retracements = fib_levels.get("retracements")
    if not isinstance(retracements, Mapping):
        return items
    for label, value in retracements.items():
        level = _fin(value)
        if level is None:
            continue
        items.append((str(label)[:5], level))
    items.sort(key=lambda item: (-item[1], item[0]))
    return items


def render_setup_chart_svg(
    bars: object,
    now_price: object,
    *,
    contract_entry: object = None,
    contract_stop: object = None,
    watch_zones: object = None,
    fib_levels: object = None,
    operator_locked: bool = False,
    width: int = CHART_WIDTH,
    height: int = CHART_HEIGHT,
) -> str:
    """Return a deterministic inline SVG for one candidate, or `""`.

    `""` means "nothing honest to draw" — no usable completed bars or no valid
    NOW anchor (PRD-226). The caller degrades to the compact ladder; it never
    gets a padded or synthesized chart.
    """
    rows = _normalize_bars(bars)
    anchor = _fin(now_price)
    if not rows or anchor is None:
        return ""

    entry = _fin(contract_entry)
    stop = _fin(contract_stop) if entry is not None else None
    if stop is not None and entry is not None and stop == entry:
        stop = None
    tier2, tier3 = _tiered_zones(watch_zones)
    fibs = _fib_items(fib_levels)

    # --- y-domain: bars + NOW + contract pair + Tier 2. Tier 3 NEVER widens it.
    domain: list[float] = [anchor]
    for _d, _o, high, low, _c in rows:
        domain += [high, low]
    domain += [v for v in (entry, stop) if v is not None]
    for _t, level in tier2:
        domain.append(level)
    lo, hi = min(domain), max(domain)
    pad = max((hi - lo) * 0.06, anchor * 0.001)
    lo, hi = lo - pad, hi + pad
    span = hi - lo

    plot_w = width - _GUTTER
    plot_h = height - _PAD_T - _PAD_B

    def y_of(price: float) -> float:
        return round(_PAD_T + plot_h * (1.0 - (price - lo) / span), 1)

    def pct(price: float) -> str:
        # PRD-221/PRD-222: signed % distance from the NOW anchor.
        return f"{(price - anchor) / anchor * 100.0:+.1f}%"

    # PRD-304: under operator lock the action palette and the action vocabulary
    # collapse to neutral observation.
    entry_c = _LOCK_C if operator_locked else _ENTRY_C
    stop_c = _LOCK_C if operator_locked else _STOP_C
    entry_word = "LEVEL" if operator_locked else "ENTRY"
    stop_word = "INVALIDATION" if operator_locked else "STOP"

    out: list[str] = []
    out.append(
        f'<svg viewBox="0 0 {width} {height}" width="100%" '
        f'preserveAspectRatio="xMidYMid meet" role="img" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="monospace">'
    )
    out.append(f'<rect width="{plot_w}" height="{height}" fill="{_BG}"/>')

    # --- zone shading (behind everything) ---
    if entry is not None and stop is not None:
        # PRD-223: the invalidation is a zone, not a tick.
        y0, y1 = sorted((y_of(entry), y_of(stop)))
        out.append(
            f'<rect class="risk-zone" x="0" y="{y0}" width="{plot_w}" '
            f'height="{max(y1 - y0, 1.0):.1f}" fill="{stop_c}" opacity="0.09"/>'
        )
    zmap = dict(tier2)
    if "ORB_HIGH" in zmap and "ORB_LOW" in zmap:
        y0, y1 = sorted((y_of(zmap["ORB_HIGH"]), y_of(zmap["ORB_LOW"])))
        out.append(
            f'<rect class="orb-band" x="0" y="{y0}" width="{plot_w}" '
            f'height="{max(y1 - y0, 1.0):.1f}" fill="{_T2_C}" opacity="0.10"/>'
        )

    # Right-gutter items: [true_y, text, colour, font-size, bold, boxed]
    items: list[list] = []

    # --- Tier 3: faint context, clipped to the domain, never widening it ---
    for label, level in fibs:
        if not lo < level < hi:
            continue
        y = y_of(level)
        out.append(
            f'<line class="lvl-t3" x1="0" y1="{y}" x2="{plot_w}" y2="{y}" '
            f'stroke="{_T3_C}" stroke-width="0.75" stroke-dasharray="2,4"/>'
        )
        items.append([y, f"fib {_html.escape(label)} {level:,.1f}", _T3_TEXT, 7.5, False, False])
    for ztype, level in tier3:
        if not lo < level < hi:
            continue
        y = y_of(level)
        out.append(
            f'<line class="lvl-t3" x1="0" y1="{y}" x2="{plot_w}" y2="{y}" '
            f'stroke="{_T3_C}" stroke-width="0.75" stroke-dasharray="2,4"/>'
        )
        items.append([y, f"{_ABBR[ztype]} {level:,.1f}", _T3_TEXT, 7.5, False, False])

    # --- Tier 2: clear structural references ---
    for ztype, level in tier2:
        y = y_of(level)
        if ztype == "VWAP":
            out.append(
                f'<line class="lvl-t2" x1="0" y1="{y}" x2="{plot_w}" y2="{y}" '
                f'stroke="{_VWAP_C}" stroke-width="1" stroke-dasharray="4,2" opacity="0.75"/>'
            )
            items.append([y, f"VWAP {level:,.1f}", _VWAP_C, 8.5, False, False])
        else:
            out.append(
                f'<line class="lvl-t2" x1="0" y1="{y}" x2="{plot_w}" y2="{y}" '
                f'stroke="{_T2_C}" stroke-width="1" opacity="0.8"/>'
            )
            items.append([y, f"{_ABBR[ztype]} {level:,.1f}", _T2_C, 8.5, False, False])

    # --- candles (the primary spatial representation) ---
    slot = plot_w / len(rows)
    body_w = max(min(slot * 0.62, 9.0), 1.5)
    for index, (_day, o, high, low, c) in enumerate(rows):
        cx = round(slot * (index + 0.5), 1)
        colour = _UP if c >= o else _DOWN
        out.append(
            f'<line class="candle-wick" x1="{cx}" y1="{y_of(high)}" x2="{cx}" '
            f'y2="{y_of(low)}" stroke="{colour}" stroke-width="1"/>'
        )
        top, bottom = y_of(max(o, c)), y_of(min(o, c))
        out.append(
            f'<rect class="candle-body" x="{cx - body_w / 2:.1f}" y="{top}" '
            f'width="{body_w:.1f}" height="{max(bottom - top, 1.0):.1f}" fill="{colour}"/>'
        )

    # --- Tier 1: STOP, ENTRY, NOW ---
    if stop is not None:
        y = y_of(stop)
        out.append(
            f'<line class="lvl-t1 lvl-stop" x1="0" y1="{y}" x2="{plot_w}" y2="{y}" '
            f'stroke="{stop_c}" stroke-width="1.5" stroke-dasharray="5,3"/>'
        )
        out.append(
            f'<text x="4" y="{y - 3}" font-size="8" font-weight="bold" '
            f'fill="{stop_c}">{stop_word} {pct(stop)}</text>'
        )
        items.append([y, f"{stop:,.2f}", stop_c, 9, True, True])
    if entry is not None and abs(entry - anchor) >= 0.005:
        y = y_of(entry)
        out.append(
            f'<line class="lvl-t1 lvl-entry" x1="0" y1="{y}" x2="{plot_w}" y2="{y}" '
            f'stroke="{entry_c}" stroke-width="1.5"/>'
        )
        out.append(
            f'<text x="4" y="{y - 3}" font-size="8" font-weight="bold" '
            f'fill="{entry_c}">{entry_word} {pct(entry)}</text>'
        )
        items.append([y, f"{entry:,.2f}", entry_c, 9, True, True])
    now_y = y_of(anchor)
    out.append(
        f'<line class="lvl-t1 lvl-now" x1="0" y1="{now_y}" x2="{plot_w}" y2="{now_y}" '
        f'stroke="{_NOW_C}" stroke-width="1.75"/>'
    )

    # --- right-edge tags: NOW is pinned, everything else is pushed clear of it,
    # order preserved. Height-aware — a boxed tag needs more room than a line.
    def item_h(item: list) -> float:
        return 15.0 if item[5] else float(item[3]) + 3.0

    now_h = 15.0
    above = sorted([it for it in items if it[0] <= now_y], key=lambda it: -it[0])
    below = sorted([it for it in items if it[0] > now_y], key=lambda it: it[0])
    placed: list[tuple[float, list]] = []
    edge = now_y - now_h / 2
    for item in above:
        yy = max(min(item[0], edge - item_h(item) / 2), _PAD_T + 2)
        placed.append((yy, item))
        edge = yy - item_h(item) / 2
    edge = now_y + now_h / 2
    for item in below:
        yy = min(max(item[0], edge + item_h(item) / 2), height - 4)
        placed.append((yy, item))
        edge = yy + item_h(item) / 2

    out.append(
        f'<rect class="now-tag" x="{plot_w - 1}" y="{now_y - 7}" width="{_GUTTER - 1}" '
        f'height="14" fill="{_NOW_C}"/>'
    )
    out.append(
        f'<text x="{plot_w + 3}" y="{now_y + 3.5}" font-size="9.5" font-weight="bold" '
        f'fill="{_BG}">NOW {anchor:,.2f}</text>'
    )
    for yy, (true_y, text, colour, size, bold, boxed) in placed:
        if abs(yy - true_y) > 4:
            out.append(
                f'<line x1="{plot_w}" y1="{true_y}" x2="{plot_w + 2}" y2="{yy:.1f}" '
                f'stroke="#333" stroke-width="0.75"/>'
            )
        if boxed:
            out.append(
                f'<rect x="{plot_w + 1}" y="{yy - 6.5:.1f}" width="{_GUTTER - 4}" '
                f'height="13" fill="{_BG}" stroke="{colour}" stroke-width="0.75" rx="1.5"/>'
            )
        weight = ' font-weight="bold"' if bold else ""
        out.append(
            f'<text x="{plot_w + 4}" y="{yy + size * 0.38:.1f}" font-size="{size}"'
            f'{weight} fill="{colour}">{text}</text>'
        )

    out.append(f'<text x="2" y="{height - 3}" font-size="7.5" fill="#666">{rows[0][0]}</text>')
    out.append(
        f'<text x="{plot_w - 4}" y="{height - 3}" font-size="7.5" fill="#666" '
        f'text-anchor="end">{rows[-1][0]}</text>'
    )
    out.append("</svg>")
    return "".join(out)
