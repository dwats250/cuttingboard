"""
Transport layer for the delivery pipeline.

Writes validated payload artifacts to their output destinations.
No payload modification. No content computation. No runtime state access.
"""

from __future__ import annotations

import json
from pathlib import Path

from cuttingboard.delivery.payload import assert_valid_payload

_DEFAULT_HTML_PATH = "reports/output/report.html"
_DEFAULT_JSON_PATH = "logs/latest_payload.json"

_VALID_MODES = frozenset({"html", "json", "cli"})


def deliver_html(
    payload: dict,
    output_path: str = _DEFAULT_HTML_PATH,
) -> None:
    """Render payload to HTML and write to output_path."""
    assert_valid_payload(payload)
    from cuttingboard.delivery.html_renderer import render_html

    content = render_html(payload)
    _write_file(output_path, content)


def deliver_json(
    payload: dict,
    output_path: str = _DEFAULT_JSON_PATH,
) -> None:
    """Serialize payload to JSON and write to output_path."""
    assert_valid_payload(payload)
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    _write_file(output_path, content)


def deliver_cli(payload: dict) -> None:
    """Print structured payload summary to stdout."""
    assert_valid_payload(payload)

    summary = payload.get("summary", {})
    sections = payload.get("sections", {})
    meta = payload.get("meta", {})

    print(f"STATUS:          {payload.get('run_status')}")
    print(f"MARKET_REGIME:   {summary.get('market_regime')}")
    print(f"TRADABLE:        {summary.get('tradable')}")
    print(f"ROUTER_MODE:     {summary.get('router_mode')}")
    print(f"SYMBOLS_SCANNED: {meta.get('symbols_scanned')}")
    print(f"TOP_TRADES:      {len(sections.get('top_trades', []))}")
    print(f"WATCHLIST:       {len(sections.get('watchlist', []))}")
    print(f"REJECTED:        {len(sections.get('rejected', []))}")


def deliver(payload: dict, mode: str) -> None:
    """Dispatch payload to the named transport mode.

    Modes: "html" | "json" | "cli"
    """
    if mode not in _VALID_MODES:
        raise ValueError(f"Unknown delivery mode {mode!r}; must be one of {sorted(_VALID_MODES)}")
    if mode == "html":
        deliver_html(payload, output_path=_DEFAULT_HTML_PATH)
    elif mode == "json":
        deliver_json(payload, output_path=_DEFAULT_JSON_PATH)
    else:
        deliver_cli(payload)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _write_file(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
