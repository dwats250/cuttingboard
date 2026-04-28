"""
Slim, read-only HTML dashboard renderer (PRD-036).

Reads logs/latest_payload.json and logs/latest_run.json.
Writes reports/output/dashboard.html.

No computation, inference, or engine logic permitted.
"""

from __future__ import annotations

import html as _html
import json
from pathlib import Path

_PAYLOAD_PATH = Path("logs/latest_payload.json")
_RUN_PATH = Path("logs/latest_run.json")
_OUTPUT_PATH = Path("reports/output/dashboard.html")

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
)


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise RuntimeError(f"Required file missing: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {path}: {exc}") from exc


def _req(obj: dict, *keys: str) -> object:
    """Navigate a nested dict path; raise RuntimeError on missing key."""
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


def _resolve_previous_run(logs_dir: Path) -> dict | None:
    run_files = sorted(logs_dir.glob("run_*.json"))
    if len(run_files) < 2:
        return None
    runs = [_load_json(path) for path in run_files]
    runs.sort(key=lambda run: str(_req(run, "timestamp")), reverse=True)
    return runs[1]


def render_dashboard_html(
    payload: dict,
    run: dict,
    *,
    previous_run: dict | None = None,
) -> str:
    """Return deterministic dashboard HTML from payload and run dicts.

    No payload or run mutation. No engine calls.
    """
    # R3 — HEADER
    timestamp = _req(payload, "meta", "timestamp")
    status = _req(run, "status")
    market_regime = _req(payload, "summary", "market_regime")
    execution_posture = _req(run, "posture")
    confidence = _req(run, "confidence")

    # R3 — SYSTEM STATE
    tradable = _req(payload, "summary", "tradable")
    validation_halt_detail = _req(payload, "sections", "validation_halt_detail")
    stay_flat_reason = (
        validation_halt_detail["reason"]
        if isinstance(validation_halt_detail, dict)
        else None
    )

    # R3 — PRIMARY / SECONDARY
    top_trades = _req(payload, "sections", "top_trades")
    primary = top_trades[0] if len(top_trades) >= 1 else None
    secondary = top_trades[1:5] if len(top_trades) >= 2 else []

    # R3 — RUN HEALTH
    system_halted = _req(run, "system_halted")
    kill_switch = _req(run, "kill_switch")
    data_status = _req(run, "data_status")
    errors = _req(run, "errors")
    first_error = errors[0] if len(errors) > 0 else None
    stale_data = data_status != "ok"  # R4: permitted string equality check

    lines: list[str] = []

    def w(line: str) -> None:
        lines.append(line)

    w("<!doctype html>")
    w('<html lang="en">')
    w("<head>")
    w('  <meta charset="UTF-8">')
    w('  <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    w("  <title>Cuttingboard Dashboard</title>")
    w(f"  <style>{_CSS}</style>")
    w("</head>")
    w("<body>")
    w('<div class="wrap">')

    # --- dashboard-header ---
    regime_cls = _esc(market_regime)
    posture_cls = _esc(execution_posture)
    w('<div class="block" id="dashboard-header">')
    w('  <div class="row">')
    w(f'    <div class="field"><div class="label">Timestamp</div>'
      f'<div class="value">{_esc(timestamp)}</div></div>')
    w(f'    <div class="field"><div class="label">Status</div>'
      f'<div class="value">{_esc(status)}</div></div>')
    w(f'    <div class="field"><div class="label">Regime</div>'
      f'<div class="value"><span class="badge {regime_cls}">{_esc(market_regime)}</span></div></div>')
    w(f'    <div class="field"><div class="label">Posture</div>'
      f'<div class="value"><span class="badge {posture_cls}">{_esc(execution_posture)}</span></div></div>')
    w("  </div>")
    w("</div>")

    # --- macro-tape ---
    w('<div class="block" id="macro-tape">')
    w("  <h2>Macro Tape</h2>")
    w('  <div class="row">')
    w(f'    <div class="field"><div class="label">market_regime</div>'
      f'<div class="value">{_esc(market_regime)}</div></div>')
    w(f'    <div class="field"><div class="label">posture</div>'
      f'<div class="value">{_esc(execution_posture)}</div></div>')
    w(f'    <div class="field"><div class="label">confidence</div>'
      f'<div class="value">{_esc(confidence)}</div></div>')
    w(f'    <div class="field"><div class="label">tradable</div>'
      f'<div class="value">{_bool_str(tradable)}</div></div>')
    w(f'    <div class="field"><div class="label">system_halted</div>'
      f'<div class="value">{_bool_str(system_halted)}</div></div>')
    w(f'    <div class="field"><div class="label">kill_switch</div>'
      f'<div class="value">{_bool_str(kill_switch)}</div></div>')
    w(f'    <div class="field"><div class="label">data_status</div>'
      f'<div class="value">{_esc(data_status)}</div></div>')
    w("  </div>")
    w("</div>")

    # --- run-delta ---
    if previous_run is not None:
        delta_fields = (
            ("Regime", _req(run, "regime"), _req(previous_run, "regime")),
            ("Posture", _req(run, "posture"), _req(previous_run, "posture")),
            ("Confidence", _req(run, "confidence"), _req(previous_run, "confidence")),
            (
                "System Halted",
                _bool_str(_req(run, "system_halted")),
                _bool_str(_req(previous_run, "system_halted")),
            ),
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
            w("  <div class=\"value\">No changes since last run</div>")
        w("</div>")

    # --- system-state ---
    w('<div class="block" id="system-state">')
    w("  <h2>System State</h2>")
    w('  <div class="row">')
    w(f'    <div class="field"><div class="label">Tradable</div>'
      f'<div class="value">{_bool_str(tradable)}</div></div>')
    if stay_flat_reason:
        w(f'    <div class="field"><div class="label">Stay Flat Reason</div>'
          f'<div class="value warn">{_esc(stay_flat_reason)}</div></div>')
    w("  </div>")
    w("</div>")

    # --- primary-setup (hidden if no top_trades) ---
    if primary is not None:
        w('<div class="block" id="primary-setup">')
        w("  <h2>Primary Setup</h2>")
        w('  <div class="row">')
        w(f'    <div class="field"><div class="label">Symbol</div>'
          f'<div class="value">{_esc(primary.get("symbol"))}</div></div>')
        w(f'    <div class="field"><div class="label">Direction</div>'
          f'<div class="value">{_esc(primary.get("direction"))}</div></div>')
        w(f'    <div class="field"><div class="label">Strategy</div>'
          f'<div class="value">{_esc(primary.get("strategy_tag"))}</div></div>')
        w(f'    <div class="field"><div class="label">Entry Mode</div>'
          f'<div class="value">{_esc(primary.get("entry_mode"))}</div></div>')
        w("  </div>")
        w("</div>")

    # --- secondary-setups (hidden if fewer than 2 trades) ---
    if secondary:
        w('<div class="block" id="secondary-setups">')
        w("  <h2>Secondary Setups</h2>")
        for i, setup in enumerate(secondary):
            if i > 0:
                w('  <div class="sep"></div>')
            w('  <div class="row">')
            w(f'    <div class="field"><div class="label">Symbol</div>'
              f'<div class="value">{_esc(setup.get("symbol"))}</div></div>')
            w(f'    <div class="field"><div class="label">Direction</div>'
              f'<div class="value">{_esc(setup.get("direction"))}</div></div>')
            w(f'    <div class="field"><div class="label">Strategy</div>'
              f'<div class="value">{_esc(setup.get("strategy_tag"))}</div></div>')
            w(f'    <div class="field"><div class="label">Entry Mode</div>'
              f'<div class="value">{_esc(setup.get("entry_mode"))}</div></div>')
            w("  </div>")
        w("</div>")

    # --- run-health ---
    halted_cls = " halted" if system_halted else ""
    ks_cls = " halted" if kill_switch else ""
    stale_cls = " warn" if stale_data else ""
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
    output_path: Path = _OUTPUT_PATH,
) -> None:
    html = render_dashboard_html(payload, run, previous_run=previous_run)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def main(
    payload_path: Path = _PAYLOAD_PATH,
    run_path: Path = _RUN_PATH,
    output_path: Path = _OUTPUT_PATH,
    logs_dir: Path = Path("logs"),
) -> None:
    payload = _load_json(payload_path)
    run = _load_json(run_path)
    previous_run = _resolve_previous_run(logs_dir)
    write_dashboard(payload, run, previous_run, output_path)
    print(f"Dashboard written: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Render slim HTML dashboard")
    parser.add_argument("--output", type=Path, default=_OUTPUT_PATH)
    parser.add_argument("--payload", type=Path, default=_PAYLOAD_PATH)
    parser.add_argument("--run", type=Path, default=_RUN_PATH)
    parser.add_argument("--logs-dir", type=Path, default=Path("logs"))
    args = parser.parse_args()
    main(
        payload_path=args.payload,
        run_path=args.run,
        output_path=args.output,
        logs_dir=args.logs_dir,
    )
