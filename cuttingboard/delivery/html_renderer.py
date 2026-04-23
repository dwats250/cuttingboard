"""
HTML renderer for the delivery layer.

Converts a validated ReportPayload into a minimal, deterministic HTML string.
Calls render_report_from_payload() so there is a single canonical report body.
"""

from __future__ import annotations

import html as _html


def render_html(payload: dict) -> str:
    """Return a deterministic HTML page from a validated payload dict.

    Same payload → identical HTML output every time.
    No system clock reads, no external calls, no payload mutation.
    """
    from cuttingboard.output import render_report_from_payload

    text = render_report_from_payload(payload)
    meta = payload.get("meta", {})
    timestamp = meta.get("timestamp", "")

    escaped = _html.escape(text)
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "  <meta charset=\"UTF-8\">\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        "  <title>Cuttingboard Report</title>\n"
        "  <style>\n"
        "    body { background: #0d0d0d; color: #e0e0e0; font-family: monospace; padding: 2rem; }\n"
        "    pre  { white-space: pre-wrap; word-break: break-word; }\n"
        "    footer { margin-top: 2rem; font-size: 0.75rem; color: #555; }\n"
        "  </style>\n"
        "</head>\n"
        "<body>\n"
        f"<pre>{escaped}</pre>\n"
        f"<footer>Generated at {_html.escape(timestamp)}</footer>\n"
        "</body>\n"
        "</html>\n"
    )
