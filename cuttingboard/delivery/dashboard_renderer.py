"""
Signal Forge dashboard renderer (PRD-055).

Reads logs/latest_payload.json, logs/latest_run.json, and
(optionally) logs/market_map.json.
Writes reports/output/dashboard.html.

No computation, inference, or engine logic permitted.
"""

from __future__ import annotations

import html as _html
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from cuttingboard.macro_pressure import build_macro_pressure

_PAYLOAD_PATH = Path("logs/latest_payload.json")
_RUN_PATH = Path("logs/latest_run.json")
_OUTPUT_PATH = Path("reports/output/dashboard.html")
_UI_INDEX_PATH = Path("ui/index.html")
_MACRO_SNAPSHOT_PATH = Path("logs/macro_drivers_snapshot.json")
_HOURLY_CONTRACT_PATH = Path("logs/latest_hourly_contract.json")
HISTORY_LIMIT = 5
_DASHBOARD_REFRESH_SECONDS = 30
DASHBOARD_STALE_AFTER_SECONDS = 300

_GRADE_ORDER: dict[str, int] = {"A+": 0, "A": 1, "B": 2, "C": 3, "D": 4, "F": 5}

_GRADE_CSS: dict[str, str] = {
    "A+": "aplus",
    "A": "a",
    "B": "b",
    "C": "c",
    "D": "d",
    "F": "f",
}

_HIGH_GRADES = frozenset({"A+", "A", "B"})
_UNAVAILABLE_WATCH = "Market data unavailable for this run; review during live market session."

_LIFECYCLE_BADGE_CSS: dict[str, str] = {
    "NEW":        "lifecycle-new",
    "UPGRADED":   "lifecycle-upgraded",
    "DOWNGRADED": "lifecycle-downgraded",
    "UNKNOWN":    "lifecycle-unknown",
}

_PT = ZoneInfo("America/Los_Angeles")


def format_dashboard_timestamp(value: str) -> tuple[str, str]:
    """Return (pacific_line, original_line) for display only. Input is never mutated.

    pacific_line: "YYYY-MM-DD HH:MM:SS PT" or "" on parse failure.
    original_line: readable original, e.g. "YYYY-MM-DD HH:MM:SS UTC".
    """
    raw = str(value) if value else ""
    cleaned = raw.replace("T", " ").rstrip("Z").strip()
    if raw.endswith("Z"):
        cleaned = cleaned + " UTC"
    try:
        if raw.endswith("Z"):
            dt_utc = datetime.fromisoformat(raw[:-1] + "+00:00")
        else:
            dt_utc = datetime.fromisoformat(raw)
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        dt_pt = dt_utc.astimezone(_PT)
        pacific_line = dt_pt.strftime("%Y-%m-%d %H:%M:%S") + " PT"
        return pacific_line, cleaned
    except Exception:
        return "", cleaned


def _compute_timestamp_freshness(value: str) -> str:
    """Return FRESH, STALE, or PARSE_ERROR based on age of a timestamp string."""
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        age = (datetime.now(tz=timezone.utc) - dt).total_seconds()
        return "STALE" if age > DASHBOARD_STALE_AFTER_SECONDS else "FRESH"
    except (ValueError, TypeError):
        return "PARSE_ERROR"


def _parse_utc_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _first_timestamp(obj: dict | None, paths: tuple[tuple[str, ...], ...]) -> tuple[object, datetime | None]:
    if not isinstance(obj, dict):
        return None, None
    for path in paths:
        current: object = obj
        for key in path:
            if not isinstance(current, dict) or key not in current:
                current = None
                break
            current = current[key]
        parsed = _parse_utc_timestamp(current)
        if parsed is not None:
            return current, parsed
    return None, None


def _timestamp_label(value: object, parsed: datetime | None) -> str:
    if parsed is None:
        return "unavailable"
    return str(value)


def _timestamp_delta_exceeds(left: datetime | None, right: datetime | None) -> bool:
    if left is None or right is None:
        return False
    return abs((left - right).total_seconds()) > DASHBOARD_STALE_AFTER_SECONDS


def _timestamp_older_than_baseline(value: datetime | None, baseline: datetime | None) -> bool:
    if value is None or baseline is None:
        return False
    return (baseline - value).total_seconds() > DASHBOARD_STALE_AFTER_SECONDS


def _resolve_market_map(path: Path) -> tuple[str, dict | None]:
    """Load market_map from path and return (status, data).

    status: SOURCE_MISSING | PARSE_ERROR | STALE | FRESH
    data: loaded dict, or None on error/missing
    """
    if not path.exists():
        return "SOURCE_MISSING", None
    try:
        mtime_age = time.time() - os.path.getmtime(path)
    except OSError:
        return "SOURCE_MISSING", None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "PARSE_ERROR", None
    if mtime_age > DASHBOARD_STALE_AFTER_SECONDS:
        return "STALE", data
    return "FRESH", data


def _is_sunday_pt(value: str) -> bool:
    """Return True only if value parses to a Sunday in America/Los_Angeles. Fails closed."""
    try:
        raw = str(value) if value else ""
        if raw.endswith("Z"):
            dt_utc = datetime.fromisoformat(raw[:-1] + "+00:00")
        else:
            dt_utc = datetime.fromisoformat(raw)
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        return dt_utc.astimezone(_PT).weekday() == 6  # 6 = Sunday
    except Exception:
        return False


_TIER_DEFS = [
    ("aplus", "A+ — ACTIONABLE", frozenset({"A+"})),
    ("a",     "A — HIGH QUALITY", frozenset({"A"})),
    ("b",     "B — DEVELOPING",   frozenset({"B"})),
    ("c",     "C — EARLY",        frozenset({"C"})),
    ("df",    "D/F — FAILING",    frozenset({"D", "F"})),
]

_CSS = (
    "*{box-sizing:border-box;margin:0;padding:0}"
    "body{background:#0d0d0d;color:#e0e0e0;font-family:monospace;padding:1rem}"
    ".wrap{max-width:640px;margin:0 auto}"
    ".block{border:1px solid #2a2a2a;border-radius:4px;margin-bottom:1rem;padding:1rem}"
    ".label{color:#888;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.05em}"
    ".value{margin-top:0.25rem}"
    ".row{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:0.5rem}"
    ".field{flex:1;min-width:120px}"
    ".badge{display:inline-block;padding:0.2rem 0.5rem;border-radius:3px;font-size:0.8rem}"
    ".RISK_ON{background:#1a3a1a;color:#4caf50}"
    ".RISK_OFF{background:#3a1a1a;color:#f44336}"
    ".NEUTRAL{background:#2a2a1a;color:#ff9800}"
    ".CHAOTIC{background:#3a1a3a;color:#e040fb}"
    ".STAY_FLAT{background:#1a1a2a;color:#90caf9}"
    ".AGGRESSIVE_LONG,.CONTROLLED_LONG{background:#1a3a1a;color:#4caf50}"
    ".DEFENSIVE_SHORT{background:#3a1a1a;color:#f44336}"
    ".NEUTRAL_PREMIUM{background:#2a2a1a;color:#ff9800}"
    ".halted{color:#f44336;font-weight:bold}"
    ".warn{color:#ff9800}"
    "h2{font-size:0.8rem;color:#888;text-transform:uppercase;"
    "letter-spacing:0.08em;margin-bottom:0.75rem}"
    ".sep{border-top:1px solid #1a1a1a;margin:0.5rem 0}"
    ".tape-slot{white-space:nowrap}"
    ".macro-tape-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(90px,1fr));"
    "gap:6px 12px;margin-top:6px;overflow-x:hidden}"
    ".macro-drivers-row{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:6px;overflow-x:hidden}"
    ".macro-tradables-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px 12px;"
    "margin-top:6px;overflow-x:hidden}"
    ".tradable-cell{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}"
    ".macro-tape-slot{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:100%}"
    ".macro-tape-label{margin-right:0.25rem}"
    ".macro-tape-value{opacity:0.85}"
    ".candidate-card{border-left:3px solid #2a2a2a;padding:0.75rem;margin-bottom:0.5rem}"
    ".grade-aplus{border-left-color:#4caf50}"
    ".grade-a{border-left-color:#8bc34a}"
    ".grade-b{border-left-color:#ff9800}"
    ".grade-c{border-left-color:#607d8b;opacity:0.8}"
    ".grade-d{border-left-color:#f44336;opacity:0.7}"
    ".grade-f{border-left-color:#424242;opacity:0.5}"
    ".unavailable{color:#888}"
    ".macro-bias{margin-top:6px;font-weight:bold}"
    ".action-line{font-weight:bold;margin-bottom:8px;padding:8px 10px;"
    "border-left:3px solid #4a6fa5;background:#111827;font-size:0.9rem;"
    "letter-spacing:0.03em}"
    ".tier-group{margin-bottom:16px}"
    ".tier-header{font-weight:bold;margin-bottom:6px;opacity:0.9}"
    ".candidate-state{font-weight:bold;margin-bottom:4px}"
    ".candidate-risk{color:#ff9800}"
    ".tape-slot.up{color:#4caf50}"
    ".tape-slot.down{color:#f44336}"
    ".tape-slot.flat{color:#888}"
    ".tape-slot.na{color:#444;opacity:0.7}"
    ".macro-bias.long{color:#4caf50}"
    ".macro-bias.short{color:#f44336}"
    ".macro-bias.mixed{color:#ff9800}"
    ".tape-no-data{color:#888;font-style:italic;margin-top:4px;font-size:0.8rem}"
    ".idle-summary{color:#888;margin-bottom:12px;padding:8px;"
    "border-left:3px solid #2a2a2a}"
    ".lifecycle-badge{display:inline-block;padding:0.15rem 0.4rem;"
    "border-radius:3px;font-size:0.75rem;margin-left:0.5rem}"
    ".lifecycle-new{background:#0d2a3a;color:#29b6f6}"
    ".lifecycle-upgraded{background:#1a3a1a;color:#4caf50}"
    ".lifecycle-downgraded{background:#3a1a1a;color:#f44336}"
    ".lifecycle-unknown{background:#222;color:#555}"
    ".lifecycle-detail{color:#888;font-size:0.8rem;margin-bottom:4px}"
    ".removed-symbols{margin-top:12px}"
    ".removed-row{color:#888;font-size:0.8rem;padding:2px 0}"
    ".MIXED{background:#2a1a3a;color:#ba68c8}"
    ".UNKNOWN{background:#1a1a1a;color:#555}"
    ".pressure-grid{display:grid;grid-template-columns:max-content max-content max-content max-content;"
    "gap:4px 8px;margin-top:4px;align-items:baseline}"
    ".pressure-overall{margin-top:10px;display:flex;align-items:baseline;gap:0.4rem}"
    ".pressure-no-data{color:#888;font-style:italic;font-size:0.8rem}"
    ".kv-grid{display:grid;grid-template-columns:max-content 1fr;gap:2px 0.75rem;margin-top:0.25rem}"
    ".history-table{display:grid;grid-template-columns:5ch max-content max-content max-content;"
    "column-gap:0.75rem;row-gap:2px;margin-top:4px;align-items:baseline}"
    ".history-cell{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:0.8rem}"
    ".lvl-diagram{margin-top:8px;padding-top:6px;border-top:1px solid #1a1a1a}"
    ".lvl-unavail{color:#555;font-size:0.75rem;font-style:italic;margin-top:6px}"
    ".artifact-warning{border-color:#ff9800;color:#ff9800}"
    ".artifact-diagnostics{color:#888;font-size:0.72rem;line-height:1.45}"
    ".artifact-diagnostics span{display:block}"
    "#artifact-diagnostics summary,#run-history summary,details.tier-group summary,#macro-pressure summary{cursor:pointer;list-style:none}"
    "#artifact-diagnostics summary::-webkit-details-marker,#run-history summary::-webkit-details-marker,#macro-pressure summary::-webkit-details-marker{display:none}"
    "#artifact-diagnostics summary{color:#555;font-size:0.72rem}"
    "#run-history summary{color:#aaa;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em}"
    "#macro-pressure summary{color:#aaa;font-size:0.7rem;text-transform:uppercase;letter-spacing:.05em}"
    "#macro-pressure{margin-top:8px}"
    ".failed-card-fields{display:grid;grid-template-columns:1fr 1fr;gap:6px 8px;margin-top:4px}"
    ".failed-card-fields .label{font-size:0.7rem}"
    ".failed-card-fields .value{margin-top:1px}"
)

_UP   = "↑"
_DOWN = "↓"
_FLAT = "→"
_DASH = "—"

_ARROW_CSS: dict[str, str] = {_UP: "up", _DOWN: "down", _FLAT: "flat", _DASH: "na"}

_TAPE_DRIVER_DEFS = [
    ("VIX", "volatility"),
    ("DXY", "dollar"),
    ("10Y", "rates"),
    ("BTC", "bitcoin"),
]
_TAPE_MM_SYMBOLS = ["SPY", "QQQ", "GLD", "SLV", "XLE", "GDX"]


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"Required file missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {path}: {exc}") from exc


def _load_json_optional(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {path}: {exc}") from exc


def _req(obj: dict, *keys: str) -> object:
    current = obj
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            raise RuntimeError(f"Required field missing: {'.'.join(keys)}")
        current = current[key]
    return current


def _load_macro_snapshot(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        drivers = data.get("macro_drivers")
        return drivers if isinstance(drivers, dict) else {}
    except Exception:
        return {}


def _esc(value: object) -> str:
    if value is None:
        return ""
    return _html.escape(str(value))


def _bool_str(value: object) -> str:
    if value is True:
        return "YES"
    if value is False:
        return "NO"
    return ""


def _pct_arrow(change_pct: float) -> str:
    if change_pct > 0:
        return _UP
    if change_pct < 0:
        return _DOWN
    return _FLAT


def _direction_arrow(direction: str) -> str:
    if direction == "LONG":
        return _UP
    if direction == "SHORT":
        return _DOWN
    return _FLAT


def _is_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _build_tape_slots(
    macro_drivers: dict,
    market_map: dict | None,
) -> list[tuple[str, str]]:
    slots: list[tuple[str, str]] = []

    for label, key in _TAPE_DRIVER_DEFS:
        block = macro_drivers.get(key) if macro_drivers else None
        if block and isinstance(block.get("change_pct"), float):
            slots.append((label, _pct_arrow(block["change_pct"])))
        else:
            slots.append((label, _DASH))

    symbols: dict = (market_map or {}).get("symbols") or {}
    for sym in _TAPE_MM_SYMBOLS:
        entry = symbols.get(sym)
        if entry:
            tf = entry.get("trade_framing") or {}
            direction = tf.get("direction")
            if direction is not None:
                slots.append((sym, _direction_arrow(direction)))
            else:
                slots.append((sym, _DASH))
        else:
            slots.append((sym, _DASH))

    return slots


def _format_tape_value(symbol: str, value: object) -> str:
    if not _is_finite_number(value):
        return "--"

    numeric = float(value)
    if symbol == "VIX":
        return f"{numeric:.1f}"
    if symbol == "DXY":
        return f"{numeric:.1f}"
    if symbol == "10Y":
        return f"{numeric:.2f}"
    if symbol == "BTC":
        if abs(numeric) >= 10000:
            return f"{numeric / 1000:.1f}K"
        return f"{numeric:.0f}"
    return f"{numeric:.2f}"


def _build_tape_value_slots(
    macro_drivers: dict,
    market_map: dict | None,
) -> list[tuple[str, str]]:
    slots: list[tuple[str, str]] = []

    for label, key in _TAPE_DRIVER_DEFS:
        block = macro_drivers.get(key) if macro_drivers else None
        value = block.get("level") if isinstance(block, dict) else None
        slots.append((label, _format_tape_value(label, value)))

    symbols: dict = (market_map or {}).get("symbols") or {}
    for sym in _TAPE_MM_SYMBOLS:
        entry = symbols.get(sym)
        value = entry.get("current_price") if isinstance(entry, dict) else None
        if _is_finite_number(value):
            slots.append((sym, _format_tape_value(sym, value)))
        else:
            slots.append((sym, "N/A"))

    return slots


_PRESSURE_COMPONENT_LABELS = [
    ("volatility_pressure", "Volatility"),
    ("dollar_pressure",     "Dollar"),
    ("rates_pressure",      "Rates"),
    ("bitcoin_pressure",    "Bitcoin"),
]

_POSTURE_LABELS: dict[str, str] = {
    "AGGRESSIVE_LONG": "Aggressive Long",
    "CONTROLLED_LONG": "Controlled Long",
    "EXPANSION_LONG":  "Expansion Long",
    "NEUTRAL_PREMIUM": "Neutral Premium",
    "DEFENSIVE_SHORT": "Defensive Short",
    "STAY_FLAT":       "Stay Flat",
    "CHAOTIC":         "Chaotic",
}


def _decision_title(outcome: object, system_halted: bool, status: object) -> str:
    if str(status) in {"FAIL", "ERROR"} or system_halted:
        return "SYSTEM HALT"
    if outcome == "TRADE":
        return "TRADE SETUP ACTIVE"
    if outcome == "NO_TRADE":
        return "NO TRADE"
    return "MONITOR"


def _build_pressure_snapshot(macro_drivers: dict, market_map: dict | None) -> dict | None:
    if (not macro_drivers) or all(str(v) == "MARKET MAP UNAVAILABLE" for v in macro_drivers.values()):
        return None
    try:
        return build_macro_pressure(macro_drivers, market_map)
    except Exception:
        return None


def _pct_label(change_pct: float | None, high_label: str, low_label: str) -> str:
    if change_pct is None:
        return "unavailable"
    if change_pct > 0.3:
        return high_label
    if change_pct < -0.3:
        return low_label
    return "flat"


def _metal_label(sym: str, entry: dict | None) -> str:
    if entry is None:
        return f"{sym}: unavailable"
    grade = entry.get("grade") or ""
    change_pct = entry.get("change_pct")
    direction = "up" if (change_pct or 0) > 0 else "down" if (change_pct or 0) < 0 else "flat"
    return f"{sym}: {grade} ({direction})" if grade else f"{sym}: {direction}"


def _build_sunday_context(
    macro_drivers: dict,
    market_regime: str | None,
    market_map: dict | None,
) -> dict:
    drivers = macro_drivers or {}
    dollar_pct = (drivers.get("dollar") or {}).get("change_pct")
    rates_pct = (drivers.get("rates") or {}).get("change_pct")
    vix_level = (drivers.get("volatility") or {}).get("level")
    vix_pct = (drivers.get("volatility") or {}).get("change_pct")
    btc_pct = (drivers.get("bitcoin") or {}).get("change_pct")

    dollar_context = _pct_label(dollar_pct, "dollar strengthening", "dollar weakening")
    rates_context = _pct_label(rates_pct, "rates rising", "rates falling")

    if vix_level is None:
        volatility_context = "volatility unavailable"
    elif vix_level > 25:
        volatility_context = f"elevated volatility (VIX {vix_level:.1f})"
    elif vix_level < 18:
        volatility_context = f"low volatility (VIX {vix_level:.1f})"
    else:
        volatility_context = f"moderate volatility (VIX {vix_level:.1f})"
    if vix_pct is not None and vix_pct > 15:
        volatility_context += " — chaotic spike"

    symbols: dict = (market_map or {}).get("symbols") or {}
    metals_parts = [_metal_label(sym, symbols.get(sym)) for sym in ("GLD", "SLV", "GDX")]
    metals_context = " | ".join(metals_parts)

    risk_context = _pct_label(btc_pct, "risk appetite present", "risk-off signal")

    posture = market_regime or "UNKNOWN"
    if posture in ("RISK_ON", "AGGRESSIVE_LONG", "CONTROLLED_LONG"):
        monday_watch = "Watch for confirmation of risk-on bias before Monday open"
    elif posture in ("RISK_OFF", "DEFENSIVE_SHORT"):
        monday_watch = "Monitor risk pressure — watch for rejection at resistance"
    elif posture == "CHAOTIC":
        monday_watch = "No trade decision before cash session — chaotic conditions"
    else:
        monday_watch = "Watch for confirmation before Monday cash session"

    return {
        "session_type": "SUNDAY_PREMARKET",
        "headline": "Sunday Macro Context — No Cash Session",
        "macro_posture": posture,
        "dollar_context": dollar_context,
        "rates_context": rates_context,
        "volatility_context": volatility_context,
        "metals_context": metals_context,
        "risk_context": risk_context,
        "monday_watch": monday_watch,
    }


def _resolve_previous_run(logs_dir: Path) -> dict | None:
    run_files = sorted(logs_dir.glob("run_*.json"))
    if len(run_files) < 2:
        return None
    runs = [_load_json(path) for path in run_files]
    runs.sort(key=lambda run: str(_req(run, "timestamp")), reverse=True)
    return runs[1]


def _render_level_diagram(
    w: object,
    contract_entry: float | None,
    fib_levels: dict | None,
    watch_zones: list | None,
) -> None:
    """Render a deterministic SVG level diagram for a candidate card (PRD-074)."""
    if contract_entry is None or contract_entry <= 0:
        w('  <div class="lvl-unavail">Chart unavailable — no price data</div>')
        return

    vwap_level: float | None = None
    zone_lines: list[tuple[float, str]] = []
    for zone in (watch_zones or []):
        lv = zone.get("level")
        zt = zone.get("type", "")
        if lv is None:
            continue
        try:
            lv_f = float(lv)
        except (TypeError, ValueError):
            continue
        if zt == "VWAP":
            if lv_f > 0:
                vwap_level = lv_f
        else:
            zone_lines.append((lv_f, zt))

    fib_items: list[tuple[float, str]] = []
    if fib_levels and isinstance(fib_levels, dict):
        retracements = fib_levels.get("retracements") or {}
        for label, val in retracements.items():
            if val is None:
                continue
            try:
                fib_items.append((float(val), str(label)))
            except (TypeError, ValueError):
                pass

    all_prices = [contract_entry]
    if vwap_level is not None:
        all_prices.append(vwap_level)
    for lv_f, _ in zone_lines:
        all_prices.append(lv_f)
    for lv_f, _ in fib_items:
        all_prices.append(lv_f)

    p_min = min(all_prices)
    p_max = max(all_prices)
    p_span = p_max - p_min

    if p_span < 0.01:
        p_min = contract_entry * 0.995
        p_max = contract_entry * 1.005
        p_span = p_max - p_min
    else:
        pad = p_span * 0.12
        p_min -= pad
        p_max += pad
        p_span = p_max - p_min

    SVG_H = 110
    LINE_W = 160
    LABEL_X = LINE_W + 4
    SVG_W = 280

    def _to_y(price: float) -> int:
        return round(SVG_H * (1.0 - (price - p_min) / p_span))

    w('  <div class="lvl-diagram">')
    w(
        f'    <svg width="{SVG_W}" height="{SVG_H}" '
        f'xmlns="http://www.w3.org/2000/svg" style="display:block;overflow:visible">'
    )
    w(f'    <rect width="{LINE_W}" height="{SVG_H}" fill="#0a0a0a"/>')

    for lv_f, label in sorted(fib_items, key=lambda x: x[0], reverse=True):
        y = _to_y(lv_f)
        safe = _esc(label[:8])
        w(
            f'    <line x1="0" y1="{y}" x2="{LINE_W}" y2="{y}" '
            f'stroke="#3a3a3a" stroke-width="1" stroke-dasharray="3,3"/>'
        )
        w(
            f'    <text x="{LABEL_X}" y="{y + 4}" font-size="9" '
            f'fill="#555" font-family="monospace">{safe}</text>'
        )

    for lv_f, zt in sorted(zone_lines, key=lambda x: x[0], reverse=True):
        y = _to_y(lv_f)
        safe = _esc(zt[:10])
        w(
            f'    <line x1="0" y1="{y}" x2="{LINE_W}" y2="{y}" '
            f'stroke="#1a4a5a" stroke-width="1"/>'
        )
        w(
            f'    <text x="{LABEL_X}" y="{y + 4}" font-size="9" '
            f'fill="#3a7a8a" font-family="monospace">{safe}</text>'
        )

    if vwap_level is not None:
        y = _to_y(vwap_level)
        w(
            f'    <line x1="0" y1="{y}" x2="{LINE_W}" y2="{y}" '
            f'stroke="#29b6f6" stroke-width="1.5" stroke-dasharray="4,2"/>'
        )
        w(
            f'    <text x="{LABEL_X}" y="{y + 4}" font-size="9" '
            f'fill="#29b6f6" font-family="monospace">VWAP</text>'
        )

    y = _to_y(contract_entry)
    w(
        f'    <line x1="0" y1="{y}" x2="{LINE_W}" y2="{y}" '
        f'stroke="#f5c518" stroke-width="2"/>'
    )
    w(f'    <circle cx="3" cy="{y}" r="3" fill="#f5c518"/>')
    w(
        f'    <text x="{LABEL_X}" y="{y + 4}" font-size="9" '
        f'fill="#f5c518" font-family="monospace">ENTRY</text>'
    )

    w('    </svg>')
    w('  </div>')


def _render_candidate_card(
    w: object, sym: str, entry: dict, contract_entry: float | None = None
) -> None:
    grade = entry.get("grade") or ""
    css_class = _GRADE_CSS.get(grade, "unknown")
    is_high = grade in _HIGH_GRADES

    lifecycle: dict | None = entry.get("lifecycle")
    lc_tr = lifecycle.get("grade_transition") if lifecycle else None
    badge_css = _LIFECYCLE_BADGE_CSS.get(lc_tr) if lc_tr else None
    badge_html = f'<span class="lifecycle-badge {badge_css}">{_esc(lc_tr)}</span>' if badge_css else ""

    w(f'<div class="candidate-card grade-{css_class}" id="card-{_esc(sym)}">')

    if not is_high:
        w('  <div class="failed-card-fields">')
        w(f'    <div><div class="label">SYMBOL</div><div class="value">{_esc(entry.get("symbol"))}</div></div>')
        w(f'    <div><div class="label">GRADE</div><div class="value">{_esc(grade)}{badge_html}</div></div>')
        w(f'    <div><div class="label">BIAS</div><div class="value">{_esc(entry.get("bias"))}</div></div>')
        w(f'    <div><div class="label">STRUCTURE</div><div class="value">{_esc(entry.get("structure"))}</div></div>')
        w('  </div>')
    else:
        w(f'  <div class="label">SYMBOL</div><div class="value">{_esc(entry.get("symbol"))}</div>')
        w(f'  <div class="label">GRADE</div><div class="value">{_esc(grade)}{badge_html}</div>')
        w(f'  <div class="label">BIAS</div><div class="value">{_esc(entry.get("bias"))}</div>')
        w(f'  <div class="label">STRUCTURE</div><div class="value">{_esc(entry.get("structure"))}</div>')

    if is_high:
        if lifecycle:
            pg = _esc(lifecycle.get("previous_grade")) or _DASH
            cg = _esc(lifecycle.get("current_grade")) or _DASH
            ps = _esc(lifecycle.get("previous_setup_state")) or _DASH
            cs = _esc(lifecycle.get("current_setup_state")) or _DASH
            w(f'  <div class="lifecycle-detail">LIFECYCLE: {pg} → {cg} | {ps} → {cs}</div>')

        setup_state = entry.get("setup_state")
        if setup_state and setup_state != "DATA_UNAVAILABLE":
            w(f'  <div class="candidate-state">STATE: {_esc(setup_state)}</div>')

        tf: dict = entry.get("trade_framing") or {}

        if_now = tf.get("if_now")
        if if_now is not None:
            w(f'  <div class="label">IF NOW</div><div class="value">{_esc(if_now)}</div>')

        entry_val = tf.get("entry")
        if entry_val is not None:
            w(f'  <div class="label">ENTRY</div><div class="value">{_esc(entry_val)}</div>')

        invalidation = entry.get("invalidation")
        if invalidation and len(invalidation) > 0 and invalidation[0] is not None:
            w(f'  <div class="label">INVALIDATION</div><div class="value">{_esc(invalidation[0])}</div>')

        downgrade = tf.get("downgrade")
        if downgrade is not None:
            w(f'  <div class="candidate-risk">RISK: {_esc(downgrade)}</div>')

        reason = entry.get("reason_for_grade")
        if reason is not None:
            w(f'  <div class="label">REASON</div><div class="value">{_esc(reason)}</div>')

        pts = entry.get("preferred_trade_structure")
        if pts is not None:
            w(f'  <div class="label">PLAY</div><div class="value">{_esc(pts)}</div>')
        for item in (entry.get("what_to_look_for") or []):
            if item and item != _UNAVAILABLE_WATCH:
                w(f'  <div class="label">WATCH</div><div class="value">{_esc(item)}</div>')

    level_anchor = contract_entry if contract_entry is not None else entry.get("current_price")
    fib_levels = entry.get("fib_levels")
    watch_zones = entry.get("watch_zones")
    has_level_context = bool(fib_levels) or bool(watch_zones)
    if level_anchor is not None and level_anchor > 0 and not has_level_context:
        w('  <div class="lvl-unavail">Level context unavailable</div>')
    else:
        _render_level_diagram(
            w,
            level_anchor,
            fib_levels,
            watch_zones,
        )

    w("</div>")


def render_dashboard_html(
    payload: dict,
    run: dict,
    *,
    previous_run: dict | None = None,
    history_runs: list[dict] | None = None,
    market_map: dict | None = None,
    market_map_path: Path | None = None,
    macro_snapshot_path: Path | None = None,
    contract_entry_map: dict | None = None,
    contract_generated_at: object | None = None,
    payload_source: str | Path = _PAYLOAD_PATH,
    run_source: str | Path = _RUN_PATH,
    market_map_source: str | Path | None = None,
    contract_source: str | Path = _HOURLY_CONTRACT_PATH,
    fixture_mode: bool = False,
) -> str:
    """Return deterministic Signal Forge dashboard HTML.

    No payload or run mutation. No engine calls.
    """
    # Resolve market_map from path if not provided directly; compute status for candidate board.
    if market_map is not None:
        _mm_status = "FRESH"
    elif market_map_path is not None:
        _mm_status, market_map = _resolve_market_map(market_map_path)
    else:
        _mm_status = "SOURCE_MISSING"

    resolved_market_map_source = market_map_source
    if resolved_market_map_source is None:
        if market_map_path is not None:
            resolved_market_map_source = market_map_path
        elif market_map is not None:
            resolved_market_map_source = "provided"
        else:
            resolved_market_map_source = "none"

    timestamp     = _req(payload, "meta", "timestamp")
    status        = _req(run, "status")
    market_regime = _req(payload, "summary", "market_regime")
    confidence    = _req(run, "confidence")

    payload_timestamp_value, payload_timestamp = _first_timestamp(
        payload,
        (("meta", "timestamp"), ("timestamp",), ("generated_at",)),
    )
    run_timestamp_value, run_timestamp = _first_timestamp(
        run,
        (("run_at_utc",), ("timestamp",), ("generated_at",)),
    )
    market_map_timestamp_value, market_map_timestamp = _first_timestamp(
        market_map,
        (("generated_at",),),
    )
    contract_timestamp = _parse_utc_timestamp(contract_generated_at)

    payload_run_mixed = _timestamp_delta_exceeds(payload_timestamp, run_timestamp)
    baseline_timestamp: datetime | None = None
    if not payload_run_mixed:
        present_timestamps = [ts for ts in (payload_timestamp, run_timestamp) if ts is not None]
        if present_timestamps:
            baseline_timestamp = max(present_timestamps)
    market_map_stale_for_run = (
        not payload_run_mixed
        and _timestamp_older_than_baseline(market_map_timestamp, baseline_timestamp)
    )
    contract_stale_for_run = (
        not payload_run_mixed
        and _timestamp_older_than_baseline(contract_timestamp, baseline_timestamp)
    )
    if contract_stale_for_run:
        contract_entry_map = None

    validation_halt_detail = _req(payload, "sections", "validation_halt_detail")
    stay_flat_reason = (
        validation_halt_detail["reason"]
        if isinstance(validation_halt_detail, dict)
        else None
    )

    macro_drivers: dict = payload.get("macro_drivers") or {}
    if (not macro_drivers) or all(str(v) == "MARKET MAP UNAVAILABLE" for v in macro_drivers.values()):
        _snap = macro_snapshot_path if macro_snapshot_path is not None else _MACRO_SNAPSHOT_PATH
        macro_drivers = _load_macro_snapshot(_snap)

    system_halted = _req(run, "system_halted")
    kill_switch   = _req(run, "kill_switch")
    errors        = _req(run, "errors")
    first_error   = errors[0] if errors else None

    # R2.1 — action line
    outcome    = run.get("outcome")
    permission = run.get("permission")
    title = "MIXED_ARTIFACTS" if payload_run_mixed else _decision_title(outcome, bool(system_halted), status)
    if payload_run_mixed:
        action_text = "ACTION: HOLD — MIXED_ARTIFACTS"
    elif outcome == "STAY_FLAT":
        action_text = "ACTION: WAIT — NO VALID SETUPS"
    elif permission is False:
        action_text = "ACTION: WATCH — SETUPS PRESENT BUT BLOCKED"
    elif permission is True:
        action_text = "ACTION: ACTIVE — TRADE CONDITIONS MET"
    else:
        action_text = "ACTION: MONITOR — SYSTEM ACTIVE"

    # R1 — tape slots
    tape_slots = _build_tape_slots(macro_drivers, market_map)
    tape_value_slots = _build_tape_value_slots(macro_drivers, market_map)
    pressure = _build_pressure_snapshot(macro_drivers, market_map)

    # R1.1 — macro bias from driver arrow counts only (first 4 slots)
    _driver_slots = tape_slots[:4]
    up_count   = sum(1 for _, arrow in _driver_slots if arrow == _UP)
    down_count = sum(1 for _, arrow in _driver_slots if arrow == _DOWN)
    if up_count > down_count:
        macro_bias = f"MACRO BIAS: LONG {_UP}"
        macro_bias_css = "macro-bias long"
    elif down_count > up_count:
        macro_bias = f"MACRO BIAS: SHORT {_DOWN}"
        macro_bias_css = "macro-bias short"
    else:
        macro_bias = "MACRO BIAS: MIXED"
        macro_bias_css = "macro-bias mixed"

    lines: list[str] = []

    def w(line: str) -> None:
        lines.append(line)

    session_type = (payload.get("meta") or {}).get("session_type")

    w("<!doctype html>")
    w('<html lang="en">')
    w("<head>")
    w('  <meta charset="UTF-8">')
    w('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    w(f'  <meta http-equiv="refresh" content="{_DASHBOARD_REFRESH_SECONDS}">')
    w("  <title>Signal Forge</title>")
    w(f"  <style>{_CSS}</style>")
    w("</head>")
    w("<body>")
    w('<div class="wrap">')

    if payload_run_mixed:
        w('<div class="block artifact-warning" id="artifact-coherence">')
        w("  <h2>MIXED_ARTIFACTS</h2>")
        w("  <div class=\"value\">Dashboard inputs are from different artifact timestamps.</div>")
        w("</div>")

    if session_type == "SUNDAY_PREMARKET" and _is_sunday_pt(str(timestamp)):
        w('<div class="block" id="premarket-banner" style="border-color:#29b6f6;color:#29b6f6;text-align:center">')
        w('  <h2>SUNDAY PRE-MARKET CONTEXT &#8212; NO CASH SESSION</h2>')
        w("</div>")

    if fixture_mode:
        from cuttingboard.delivery.fixtures import FIXTURE_SYMBOLS
        market_map = dict(market_map) if market_map is not None else {}
        market_map = {**market_map, "symbols": FIXTURE_SYMBOLS}
        _mm_status = "FRESH"

    # --- system-state ---
    _ts_pacific, _ts_original = format_dashboard_timestamp(str(timestamp))
    _ts_freshness = _compute_timestamp_freshness(str(timestamp))
    _freshness_label = "STALE" if _ts_freshness == "STALE" else "CURRENT"
    regime_cls = _esc(market_regime)
    outcome_val = run.get("outcome") if "outcome" in run else run.get("status")
    halted_cls = " halted" if system_halted else ""
    ks_cls     = " halted" if kill_switch else ""
    w('<div class="block" id="system-state">')
    w(f'  <h2>SYSTEM STATE - {_esc(title)}</h2>')
    w(f'  <div class="action-line">{_esc(action_text)}</div>')
    w('  <div class="row">')
    w(f'    <div class="field"><div class="label">Regime</div>'
      f'<div class="value"><span class="badge {regime_cls}">{_esc(market_regime)}</span></div></div>')
    w(f'    <div class="field"><div class="label">Confidence</div>'
      f'<div class="value">{_esc(confidence)}</div></div>')
    w(f'    <div class="field"><div class="label">Outcome</div>'
      f'<div class="value">{_esc(outcome_val)}</div></div>')
    w("  </div>")
    w('  <div class="row">')
    if bool(system_halted):
        w('    <div class="field"><div class="label">Permission</div>'
          '<div class="value halted">HALTED</div></div>')
    elif stay_flat_reason is not None:
        w(f'    <div class="field warn"><div class="label">Permission</div>'
          f'<div class="value">{_esc(stay_flat_reason)}</div></div>')
    elif run.get("permission") is not None:
        w(f'    <div class="field"><div class="label">Permission</div>'
          f'<div class="value">{_esc(run["permission"])}</div></div>')
    else:
        w('    <div class="field"><div class="label">Permission</div>'
          '<div class="value">NONE</div></div>')
    if bool(system_halted):
        w(f'    <div class="field"><div class="label">Halted</div>'
          f'<div class="value{halted_cls}">{_bool_str(system_halted)}</div></div>')
    if bool(kill_switch):
        w(f'    <div class="field"><div class="label">Kill Switch</div>'
          f'<div class="value{ks_cls}">{_bool_str(kill_switch)}</div></div>')
    if first_error:
        w(f'    <div class="field"><div class="label">Error</div>'
          f'<div class="value halted">{_esc(first_error)}</div></div>')
    w("  </div>")
    if bool(system_halted) and stay_flat_reason is not None:
        w(f'  <div class="field warn"><div class="label">Reason</div>'
          f'<div class="value">{_esc(stay_flat_reason)}</div></div>')
    w('  <div class="sep"></div>')
    w(f'  <div class="label">RUN SNAPSHOT - {_freshness_label}</div>')
    if _ts_pacific:
        w(f'  <div class="value">{_esc(_ts_pacific)}</div>')
    w("</div>")

    # --- sunday-macro-context (SUNDAY_PREMARKET only) ---
    if session_type == "SUNDAY_PREMARKET" and _is_sunday_pt(str(timestamp)):
        ctx = _build_sunday_context(macro_drivers, market_regime, market_map)
        w('<div class="block" id="sunday-macro-context" style="border-color:#29b6f6">')
        w(f'  <h2>{_esc(ctx["headline"])}</h2>')
        w('  <div class="row">')
        w(f'    <div class="field"><div class="label">Posture</div>'
          f'<div class="value">{_esc(ctx["macro_posture"])}</div></div>')
        w(f'    <div class="field"><div class="label">Dollar</div>'
          f'<div class="value">{_esc(ctx["dollar_context"])}</div></div>')
        w(f'    <div class="field"><div class="label">Rates</div>'
          f'<div class="value">{_esc(ctx["rates_context"])}</div></div>')
        w('  </div>')
        w('  <div class="row">')
        w(f'    <div class="field"><div class="label">Volatility</div>'
          f'<div class="value">{_esc(ctx["volatility_context"])}</div></div>')
        w(f'    <div class="field"><div class="label">Risk Sentiment</div>'
          f'<div class="value">{_esc(ctx["risk_context"])}</div></div>')
        w('  </div>')
        w(f'  <div class="field"><div class="label">Metals</div>'
          f'<div class="value">{_esc(ctx["metals_context"])}</div></div>')
        w(f'  <div class="field" style="margin-top:8px"><div class="label">Monday Watch</div>'
          f'<div class="value">{_esc(ctx["monday_watch"])}</div></div>')
        w("</div>")

    # --- macro-tape ---
    w('<div class="block" id="macro-tape">')
    w("  <h2>Macro Tape</h2>")
    if (not macro_drivers) or all(str(v) == "MARKET MAP UNAVAILABLE" for v in macro_drivers.values()):
        w('  <div class="tape-no-data">NO LIVE MACRO DATA</div>')
    tape_value_map = dict(tape_value_slots)

    # Macro bias first
    w(f'  <div class="{_esc(macro_bias_css)}">{_esc(macro_bias)}</div>')

    # Macro drivers row (VIX, DXY, 10Y, BTC) with directional arrows
    driver_html = [
        f'<span class="macro-tape-slot tape-slot {_ARROW_CSS.get(arrow, "na")}">'
        f'<span class="macro-tape-label">{_esc(label)} {_esc(arrow)}</span>'
        f'<span class="macro-tape-value" data-symbol="{_esc(label)}">'
        f'{_esc(tape_value_map.get(label, ""))}</span>'
        f'</span>'
        for label, arrow in tape_slots[:4]
    ]
    w('  <div class="macro-drivers-row">' + "".join(driver_html) + "</div>")

    # Divider
    w('  <div class="sep"></div>')

    # Tradables grid (no arrows, 2 per row)
    w('  <div class="macro-tradables-grid">')
    for sym in _TAPE_MM_SYMBOLS:
        val = tape_value_map.get(sym, "N/A")
        w(
            f'    <span class="tradable-cell">'
            f'<span class="macro-tape-label">{_esc(sym)}</span>'
            f'&nbsp;<span class="macro-tape-value" data-symbol="{_esc(sym)}">{_esc(val)}</span>'
            f'</span>'
        )
    w('  </div>')

    # --- macro-pressure ---
    w('  <details id="macro-pressure">')
    w("    <summary>Macro Pressure</summary>")
    if (not macro_drivers) or all(str(v) == "MARKET MAP UNAVAILABLE" for v in macro_drivers.values()):
        w('    <div class="pressure-no-data">NO PRESSURE DATA</div>')
    elif not isinstance(pressure, dict):
        w('    <div class="pressure-no-data">FIELD_MISSING</div>')
    else:
        w('    <div class="pressure-grid">')
        for key, label in _PRESSURE_COMPONENT_LABELS:
            val = _esc(pressure.get(key, "FIELD_MISSING"))
            w(f'    <span class="label">{_esc(label)}</span>')
            w(f'    <span class="badge {val}">{val}</span>')
        overall = pressure.get("overall_pressure", "FIELD_MISSING")
        w('    <span class="label">Overall</span>')
        w(f'    <span class="badge {_esc(overall)}">{_esc(overall)}</span>')
        w('    </div>')
    w("  </details>")
    w("</div>")

    # --- candidate-board ---
    w('<div class="block" id="candidate-board">')
    if fixture_mode:
        w('  <h2>Candidate Board &#8212; <span style="color:#ff9800">DEMO MODE &#8212; FIXTURE DATA</span></h2>')
    else:
        w("  <h2>Candidate Board</h2>")
    if market_map_stale_for_run:
        w('  <div class="unavailable">STALE MARKET MAP</div>')
        w('  <div class="idle-summary">'
          '<div>Candidate Board paused</div>'
          '<div>market map is older than the selected run</div>'
          '</div>')
    elif _mm_status in ("SOURCE_MISSING", "PARSE_ERROR"):
        w(f'  <div class="unavailable">{_esc(_mm_status)}</div>')
    else:
        if _mm_status == "STALE":
            w('  <div class="unavailable">STALE</div>')
        if market_map is None:
            w('  <div class="unavailable">N/A</div>')
        else:
            symbols: dict = market_map.get("symbols") or {}
            if not symbols:
                w('  <div class="unavailable">NO_CANDIDATES</div>')
            else:
                sorted_syms = sorted(
                    symbols.keys(),
                    key=lambda sym: (_GRADE_ORDER.get(symbols[sym].get("grade", ""), 6), sym),
                )
                has_actionable = any(symbols[s].get("grade", "") in _HIGH_GRADES for s in sorted_syms)
                if not has_actionable:
                    w('  <div class="idle-summary">'
                      '<div>NO ACTIONABLE SETUPS</div>'
                      '<div>Market is not offering structure</div>'
                      '</div>')
                for tier_id, tier_label, tier_grades in _TIER_DEFS:
                    tier_syms = [s for s in sorted_syms if symbols[s].get("grade", "") in tier_grades]
                    if not tier_syms:
                        continue
                    is_low_tier = tier_grades.isdisjoint(_HIGH_GRADES)
                    if is_low_tier:
                        w(f'  <details class="tier-group" id="tier-{tier_id}">')
                        w(f'    <summary class="tier-header">{_esc(tier_label)} ({len(tier_syms)})</summary>')
                    else:
                        w(f'  <div class="tier-group" id="tier-{tier_id}">')
                        w(f'    <div class="tier-header">{_esc(tier_label)} ({len(tier_syms)})</div>')
                    for sym in tier_syms:
                        _render_candidate_card(
                            w, sym, symbols[sym],
                            contract_entry=(contract_entry_map or {}).get(sym),
                        )
                    if is_low_tier:
                        w("  </details>")
                    else:
                        w("  </div>")
            removed_syms: list = market_map.get("removed_symbols") or []
            if removed_syms:
                w('  <div class="removed-symbols">')
                w('    <div class="tier-header">REMOVED</div>')
                for removed_entry in removed_syms:
                    rsym  = _esc(removed_entry.get("symbol"))
                    rprev = _esc(removed_entry.get("previous_grade")) or _DASH
                    w(f'    <div class="removed-row">{rsym} — removed (prev: {rprev})</div>')
                w("  </div>")
    w("</div>")

    # --- run-delta ---
    w('<div class="block" id="run-delta">')
    w("  <h2>Changes Since Last Run</h2>")
    if previous_run is None:
        w('  <div class="value">SOURCE_MISSING</div>')
    else:
        delta_fields = (
            ("Regime",        _req(run, "regime"),        _req(previous_run, "regime")),
            ("Posture",
             _POSTURE_LABELS.get(str(_req(run, "posture")),        str(_req(run, "posture"))),
             _POSTURE_LABELS.get(str(_req(previous_run, "posture")), str(_req(previous_run, "posture")))),
            ("Confidence",    _req(run, "confidence"),    _req(previous_run, "confidence")),
            ("System Halted", _bool_str(_req(run, "system_halted")),
                              _bool_str(_req(previous_run, "system_halted"))),
        )
        changed_fields = [
            (label, previous_value, current_value)
            for label, current_value, previous_value in delta_fields
            if current_value != previous_value
        ]
        if changed_fields:
            for label, previous_value, current_value in changed_fields:
                w(
                    f'  <div class="value">{_esc(label)}: '
                    f'{_esc(previous_value)} -&gt; {_esc(current_value)}</div>'
                )
        else:
            w('  <div class="value">No changes since last run</div>')
    w("</div>")

    # --- run-history ---
    w('<details class="block" id="run-history">')
    w("  <summary>History</summary>")
    if not history_runs:
        w('  <div class="value">NO_HISTORY</div>')
    else:
        w('  <div class="history-table">')
        w('    <span class="label">Time</span>')
        w('    <span class="label">Regime</span>')
        w('    <span class="label">Posture</span>')
        w('    <span class="label">Conf</span>')
        for history_run in history_runs:
            ht         = str(_req(history_run, "timestamp"))[11:16]
            hreg       = _req(history_run, "regime")
            hpos       = _req(history_run, "posture")
            hpos_label = _POSTURE_LABELS.get(str(hpos), str(hpos))
            hcon       = _req(history_run, "confidence")
            w(f'    <span class="history-cell">{_esc(ht)}</span>')
            w(f'    <span class="history-cell">{_esc(hreg)}</span>')
            w(f'    <span class="history-cell">{_esc(hpos_label)}</span>')
            w(f'    <span class="history-cell">{_esc(hcon)}</span>')
        w('  </div>')
    w("</details>")

    w('<details class="block" id="artifact-diagnostics">')
    w("  <summary>Artifact diagnostics</summary>")
    w('  <div class="artifact-diagnostics">')
    w(
        f'    <span>payload={_esc(payload_source)} @ '
        f'{_esc(_timestamp_label(payload_timestamp_value, payload_timestamp))}</span>'
    )
    w(
        f'    <span>run={_esc(run_source)} @ '
        f'{_esc(_timestamp_label(run_timestamp_value, run_timestamp))}</span>'
    )
    w(
        f'    <span>market_map={_esc(resolved_market_map_source)} @ '
        f'{_esc(_timestamp_label(market_map_timestamp_value, market_map_timestamp))}</span>'
    )
    w(
        f'    <span>contract={_esc(contract_source)} @ '
        f'{_esc(_timestamp_label(contract_generated_at, contract_timestamp))}</span>'
    )
    w("  </div>")
    w("</details>")

    w("</div>")  # .wrap
    w("</div>")
    w("</body>")
    w("</html>")

    return "\n".join(lines)


def write_dashboard(
    payload: dict,
    run: dict,
    previous_run: dict | None = None,
    history_runs: list[dict] | None = None,
    market_map: dict | None = None,
    output_path: Path = _OUTPUT_PATH,
    macro_snapshot_path: Path | None = None,
    market_map_path: Path | None = None,
    contract_entry_map: dict | None = None,
    contract_generated_at: object | None = None,
    payload_source: str | Path = _PAYLOAD_PATH,
    run_source: str | Path = _RUN_PATH,
    market_map_source: str | Path | None = None,
    contract_source: str | Path = _HOURLY_CONTRACT_PATH,
    fixture_mode: bool = False,
) -> None:
    html = render_dashboard_html(
        payload,
        run,
        previous_run=previous_run,
        history_runs=history_runs,
        market_map=market_map,
        market_map_path=market_map_path,
        macro_snapshot_path=macro_snapshot_path,
        contract_entry_map=contract_entry_map,
        contract_generated_at=contract_generated_at,
        payload_source=payload_source,
        run_source=run_source,
        market_map_source=market_map_source,
        contract_source=contract_source,
        fixture_mode=fixture_mode,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    _UI_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    _UI_INDEX_PATH.write_text(html, encoding="utf-8")


def _build_contract_entry_map(logs_dir: Path) -> dict[str, float]:
    """Load contract entry prices from latest_hourly_contract.json (best-effort)."""
    path = logs_dir / _HOURLY_CONTRACT_PATH.name
    contract = _load_json_optional(path)
    if not contract:
        return {}
    result: dict[str, float] = {}
    for cand in (contract.get("trade_candidates") or []):
        sym = cand.get("symbol")
        val = cand.get("entry")
        if sym and val is not None:
            try:
                result[sym] = float(val)
            except (TypeError, ValueError):
                pass
    return result


def _load_contract_entry_context(logs_dir: Path) -> tuple[dict[str, float], object | None, Path]:
    """Load latest_hourly_contract entry prices and generated_at timestamp."""
    path = logs_dir / _HOURLY_CONTRACT_PATH.name
    contract = _load_json_optional(path)
    if not contract:
        return {}, None, path
    result: dict[str, float] = {}
    for cand in (contract.get("trade_candidates") or []):
        sym = cand.get("symbol")
        val = cand.get("entry")
        if sym and val is not None:
            try:
                result[sym] = float(val)
            except (TypeError, ValueError):
                pass
    return result, contract.get("generated_at"), path


def main(
    payload_path: Path = _PAYLOAD_PATH,
    run_path: Path = _RUN_PATH,
    output_path: Path = _OUTPUT_PATH,
    logs_dir: Path = Path("logs"),
    macro_snapshot_path: Path | None = None,
    fixture_mode: bool = False,
) -> None:
    import os
    _fixture_mode = fixture_mode or os.environ.get("FIXTURE_MODE", "0") == "1"

    payload    = _load_json(payload_path)
    run        = _load_json(run_path)

    previous_run = _resolve_previous_run(logs_dir)
    history_run_files = sorted(logs_dir.glob("run_*.json"))
    history_runs = [_load_json(path) for path in history_run_files]
    history_runs.sort(
        key=lambda history_run: str(_req(history_run, "timestamp")),
        reverse=True,
    )
    history_runs = history_runs[:HISTORY_LIMIT]

    contract_entry_map_raw, contract_generated_at, contract_source = _load_contract_entry_context(logs_dir)
    contract_entry_map = contract_entry_map_raw or None
    market_map_path = logs_dir / "market_map.json"

    write_dashboard(
        payload, run, previous_run, history_runs, output_path=output_path,
        market_map_path=market_map_path,
        macro_snapshot_path=macro_snapshot_path,
        contract_entry_map=contract_entry_map,
        contract_generated_at=contract_generated_at,
        payload_source=payload_path,
        run_source=run_path,
        market_map_source=market_map_path,
        contract_source=contract_source,
        fixture_mode=_fixture_mode,
    )
    print(f"Dashboard written: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Render Signal Forge dashboard")
    parser.add_argument("--output",         type=Path, default=_OUTPUT_PATH)
    parser.add_argument("--payload",         type=Path, default=_PAYLOAD_PATH)
    parser.add_argument("--run",             type=Path, default=_RUN_PATH)
    parser.add_argument("--logs-dir",        type=Path, default=Path("logs"))
    parser.add_argument("--macro-snapshot",  type=Path, default=None)
    args = parser.parse_args()
    main(
        payload_path=args.payload,
        run_path=args.run,
        output_path=args.output,
        logs_dir=args.logs_dir,
        macro_snapshot_path=args.macro_snapshot,
    )
