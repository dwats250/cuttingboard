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
from pathlib import Path

from cuttingboard.macro_pressure import build_macro_pressure

_PAYLOAD_PATH = Path("logs/latest_payload.json")
_RUN_PATH = Path("logs/latest_run.json")
_OUTPUT_PATH = Path("reports/output/dashboard.html")
HISTORY_LIMIT = 5
_DASHBOARD_REFRESH_SECONDS = 30

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

_LIFECYCLE_BADGE_CSS: dict[str, str] = {
    "NEW":        "lifecycle-new",
    "UPGRADED":   "lifecycle-upgraded",
    "DOWNGRADED": "lifecycle-downgraded",
    "UNKNOWN":    "lifecycle-unknown",
}

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
    ".tape-slot{display:inline;margin-right:0.5rem;white-space:nowrap}"
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
    ".pressure-component{margin-right:0.75rem;display:inline-block}"
    ".pressure-no-data{color:#888;font-style:italic;font-size:0.8rem}"
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
_TAPE_MM_SYMBOLS = ["SPY", "QQQ", "GLD", "SLV", "XLE"]


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
        slots.append((sym, _format_tape_value(sym, value)))

    return slots


_PRESSURE_COMPONENT_LABELS = [
    ("volatility_pressure", "VOL"),
    ("dollar_pressure",     "DXY"),
    ("rates_pressure",      "RATES"),
    ("bitcoin_pressure",    "BTC"),
]


def _build_pressure_snapshot(macro_drivers: dict, market_map: dict | None) -> dict | None:
    if not macro_drivers:
        return None
    try:
        return build_macro_pressure(macro_drivers, market_map)
    except Exception:
        return None


def _resolve_previous_run(logs_dir: Path) -> dict | None:
    run_files = sorted(logs_dir.glob("run_*.json"))
    if len(run_files) < 2:
        return None
    runs = [_load_json(path) for path in run_files]
    runs.sort(key=lambda run: str(_req(run, "timestamp")), reverse=True)
    return runs[1]


def _render_candidate_card(w: object, sym: str, entry: dict) -> None:
    grade = entry.get("grade") or ""
    css_class = _GRADE_CSS.get(grade, "unknown")
    is_high = grade in _HIGH_GRADES

    lifecycle: dict | None = entry.get("lifecycle")
    lc_tr = lifecycle.get("grade_transition") if lifecycle else None
    badge_css = _LIFECYCLE_BADGE_CSS.get(lc_tr) if lc_tr else None
    badge_html = f'<span class="lifecycle-badge {badge_css}">{_esc(lc_tr)}</span>' if badge_css else ""

    w(f'<div class="candidate-card grade-{css_class}" id="card-{_esc(sym)}">')
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

    w("</div>")


def render_dashboard_html(
    payload: dict,
    run: dict,
    *,
    previous_run: dict | None = None,
    history_runs: list[dict] | None = None,
    market_map: dict | None = None,
) -> str:
    """Return deterministic Signal Forge dashboard HTML.

    No payload or run mutation. No engine calls.
    """
    timestamp     = _req(payload, "meta", "timestamp")
    status        = _req(run, "status")
    market_regime = _req(payload, "summary", "market_regime")
    posture       = _req(run, "posture")
    confidence    = _req(run, "confidence")

    validation_halt_detail = _req(payload, "sections", "validation_halt_detail")
    stay_flat_reason = (
        validation_halt_detail["reason"]
        if isinstance(validation_halt_detail, dict)
        else None
    )

    macro_drivers: dict = payload.get("macro_drivers") or {}

    system_halted = _req(run, "system_halted")
    kill_switch   = _req(run, "kill_switch")
    data_status   = _req(run, "data_status")
    errors        = _req(run, "errors")
    first_error   = errors[0] if errors else None
    stale_data    = data_status != "ok"

    # R2.1 — action line
    outcome    = run.get("outcome")
    permission = run.get("permission")
    if outcome == "STAY_FLAT":
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

    # R1.1 — macro bias from arrow counts
    up_count   = sum(1 for _, arrow in tape_slots if arrow == _UP)
    down_count = sum(1 for _, arrow in tape_slots if arrow == _DOWN)
    if up_count > down_count:
        macro_bias = "MACRO BIAS: LONG"
        macro_bias_css = "macro-bias long"
    elif down_count > up_count:
        macro_bias = "MACRO BIAS: SHORT"
        macro_bias_css = "macro-bias short"
    else:
        macro_bias = "MACRO BIAS: MIXED"
        macro_bias_css = "macro-bias mixed"

    lines: list[str] = []

    def w(line: str) -> None:
        lines.append(line)

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

    # --- dashboard-header ---
    w('<div class="block" id="dashboard-header">')
    w("  <h2>Dashboard</h2>")
    w('  <div class="row">')
    w(f'    <div class="field"><div class="label">Timestamp</div>'
      f'<div class="value">{_esc(timestamp)}</div></div>')
    w(f'    <div class="field"><div class="label">Status</div>'
      f'<div class="value">{_esc(status)}</div></div>')
    w("  </div>")
    w("</div>")

    # --- macro-tape ---
    w('<div class="block" id="macro-tape">')
    w("  <h2>Macro Tape</h2>")
    if not macro_drivers:
        w('  <div class="tape-no-data">NO LIVE MACRO DATA</div>')
    tape_parts = [
        f'<span class="tape-slot {_ARROW_CSS.get(arrow, "na")}">{_esc(label)} {_esc(arrow)}</span>'
        for label, arrow in tape_slots
    ]
    w("  <div>" + " | ".join(tape_parts) + "</div>")
    value_parts = [
        f'<span class="macro-tape-value" data-symbol="{_esc(label)}">{_esc(value)}</span>'
        for label, value in tape_value_slots
    ]
    w('  <div class="macro-tape-values">' + " | ".join(value_parts) + "</div>")
    w(f'  <div class="{_esc(macro_bias_css)}">{_esc(macro_bias)}</div>')
    w("</div>")

    # --- macro-pressure ---
    w('<div class="block" id="macro-pressure">')
    w("  <h2>Macro Pressure</h2>")
    if pressure is None:
        w('  <div class="pressure-no-data">NO PRESSURE DATA</div>')
    else:
        component_parts = [
            f'<span class="pressure-component">'
            f'<span class="label">{_esc(label)}</span> '
            f'<span class="badge {_esc(pressure[key])}">{_esc(pressure[key])}</span>'
            f'</span>'
            for key, label in _PRESSURE_COMPONENT_LABELS
        ]
        w("  <div>" + "".join(component_parts) + "</div>")
        overall = pressure.get("overall_pressure", "UNKNOWN")
        w(f'  <div style="margin-top:6px"><span class="label">OVERALL</span> '
          f'<span class="badge {_esc(overall)}">{_esc(overall)}</span></div>')
    w("</div>")

    # --- run-delta ---
    if previous_run is not None:
        delta_fields = (
            ("Regime",        _req(run, "regime"),        _req(previous_run, "regime")),
            ("Posture",       _req(run, "posture"),       _req(previous_run, "posture")),
            ("Confidence",    _req(run, "confidence"),    _req(previous_run, "confidence")),
            ("System Halted", _bool_str(_req(run, "system_halted")),
                              _bool_str(_req(previous_run, "system_halted"))),
        )
        changed_fields = [
            (label, previous_value, current_value)
            for label, current_value, previous_value in delta_fields
            if current_value != previous_value
        ]
        w('<div class="block" id="run-delta">')
        w("  <h2>Delta</h2>")
        if changed_fields:
            for label, previous_value, current_value in changed_fields:
                w(
                    f'  <div class="value">{_esc(label)}: '
                    f'{_esc(previous_value)} -&gt; {_esc(current_value)}</div>'
                )
        else:
            w('  <div class="value">No changes since last run</div>')
        w("</div>")

    # --- system-state ---
    regime_cls = _esc(market_regime)
    posture_cls = _esc(posture)
    outcome_val = run.get("outcome") if "outcome" in run else run.get("status")
    w('<div class="block" id="system-state">')
    w("  <h2>System State</h2>")
    w(f'  <div class="action-line">{_esc(action_text)}</div>')
    w('  <div class="row">')
    w(f'    <div class="field"><div class="label">Regime</div>'
      f'<div class="value"><span class="badge {regime_cls}">{_esc(market_regime)}</span></div></div>')
    w(f'    <div class="field"><div class="label">Posture</div>'
      f'<div class="value"><span class="badge {posture_cls}">{_esc(posture)}</span></div></div>')
    w(f'    <div class="field"><div class="label">Confidence</div>'
      f'<div class="value">{_esc(confidence)}</div></div>')
    w(f'    <div class="field"><div class="label">Outcome</div>'
      f'<div class="value">{_esc(outcome_val)}</div></div>')
    w("  </div>")
    if "permission" in run and run["permission"] is not None:
        w(f'  <div class="field"><div class="label">Permission</div>'
          f'<div class="value">{_esc(run["permission"])}</div></div>')
    if stay_flat_reason is not None:
        w(f'  <div class="field warn"><div class="label">Stay Flat</div>'
          f'<div class="value">{_esc(stay_flat_reason)}</div></div>')
    w("</div>")

    # --- candidate-board ---
    w('<div class="block" id="candidate-board">')
    w("  <h2>Candidate Board</h2>")
    if market_map is None:
        w('  <div class="unavailable">MARKET MAP UNAVAILABLE</div>')
    else:
        symbols: dict = market_map.get("symbols") or {}
        if not symbols:
            w('  <div class="unavailable">NO SYMBOL DATA</div>')
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
                w(f'  <div class="tier-group" id="tier-{tier_id}">')
                w(f'    <div class="tier-header">{_esc(tier_label)} ({len(tier_syms)})</div>')
                for sym in tier_syms:
                    _render_candidate_card(w, sym, symbols[sym])
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

    # --- run-history ---
    if history_runs:
        w('<div class="block" id="run-history">')
        w("  <h2>History</h2>")
        w('  <div class="value">timestamp | regime | posture | confidence</div>')
        for history_run in history_runs:
            ht   = str(_req(history_run, "timestamp"))[11:16]
            hreg = _req(history_run, "regime")
            hpos = _req(history_run, "posture")
            hcon = _req(history_run, "confidence")
            w(
                f'  <div class="value">'
                f'{_esc(ht)} | {_esc(hreg)} | {_esc(hpos)} | {_esc(hcon)}'
                f'</div>'
            )
        w("</div>")

    # --- run-health ---
    halted_cls = " halted" if system_halted else ""
    ks_cls     = " halted" if kill_switch else ""
    stale_cls  = " warn" if stale_data else ""
    w('<div class="block" id="run-health">')
    w("  <h2>Run Health</h2>")
    w('  <div class="row">')
    w(f'    <div class="field"><div class="label">System Halted</div>'
      f'<div class="value{halted_cls}">{_bool_str(system_halted)}</div></div>')
    w(f'    <div class="field"><div class="label">Kill Switch</div>'
      f'<div class="value{ks_cls}">{_bool_str(kill_switch)}</div></div>')
    w(f'    <div class="field"><div class="label">Stale Data</div>'
      f'<div class="value{stale_cls}">{_bool_str(stale_data)}</div></div>')
    if first_error is not None:
        w(f'    <div class="field"><div class="label">Error</div>'
          f'<div class="value halted">{_esc(first_error)}</div></div>')
    w("  </div>")
    w("</div>")

    w("</div>")  # .wrap
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
) -> None:
    html = render_dashboard_html(
        payload,
        run,
        previous_run=previous_run,
        history_runs=history_runs,
        market_map=market_map,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def main(
    payload_path: Path = _PAYLOAD_PATH,
    run_path: Path = _RUN_PATH,
    output_path: Path = _OUTPUT_PATH,
    logs_dir: Path = Path("logs"),
) -> None:
    payload    = _load_json(payload_path)
    run        = _load_json(run_path)
    market_map = _load_json_optional(logs_dir / "market_map.json")

    previous_run = _resolve_previous_run(logs_dir)
    history_run_files = sorted(logs_dir.glob("run_*.json"))
    history_runs = [_load_json(path) for path in history_run_files]
    history_runs.sort(
        key=lambda history_run: str(_req(history_run, "timestamp")),
        reverse=True,
    )
    history_runs = history_runs[:HISTORY_LIMIT]

    write_dashboard(payload, run, previous_run, history_runs, market_map, output_path)
    print(f"Dashboard written: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Render Signal Forge dashboard")
    parser.add_argument("--output",   type=Path, default=_OUTPUT_PATH)
    parser.add_argument("--payload",  type=Path, default=_PAYLOAD_PATH)
    parser.add_argument("--run",      type=Path, default=_RUN_PATH)
    parser.add_argument("--logs-dir", type=Path, default=Path("logs"))
    args = parser.parse_args()
    main(
        payload_path=args.payload,
        run_path=args.run,
        output_path=args.output,
        logs_dir=args.logs_dir,
    )
