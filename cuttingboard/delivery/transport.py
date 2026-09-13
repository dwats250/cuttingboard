"""
Transport layer for the delivery pipeline.

Writes validated payload artifacts to their output destinations.
No payload modification. No content computation. No runtime state access.
"""

from __future__ import annotations

import json
from pathlib import Path

from cuttingboard import authority_projection
from cuttingboard.delivery.payload import assert_valid_payload
from cuttingboard.effective_permission import EffectivePermission

_DEFAULT_HTML_PATH = "reports/output/report.html"
_DEFAULT_JSON_PATH = "logs/latest_payload.json"

_VALID_MODES = frozenset({"html", "json", "cli"})


def deliver_html(
    payload: dict,
    *,
    effective_permission: EffectivePermission,
    output_path: str = _DEFAULT_HTML_PATH,
) -> None:
    """Render payload to HTML and write to output_path. PRD-340 R1: an
    EffectivePermission is required (render-before-resolve is an argument error);
    the rendered wording derives from the payload's resolver-written EP via the
    read boundary (render_html -> render_report_from_payload)."""
    assert_valid_payload(payload)
    authority_projection.assert_in_process_ep(effective_permission)
    from cuttingboard.delivery.html_renderer import render_html

    content = render_html(payload)
    _write_file(output_path, content)


def deliver_json(
    payload: dict,
    *,
    effective_permission: EffectivePermission,
    output_path: str = _DEFAULT_JSON_PATH,
) -> None:
    """Serialize payload to JSON and write to output_path. PRD-340 R1: an
    EffectivePermission is required; the payload carries the resolver-written
    authority field (Slice-1 exclusive writer / persist_copy)."""
    assert_valid_payload(payload)
    authority_projection.assert_in_process_ep(effective_permission)
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    _write_file(output_path, content)


def deliver_cli(payload: dict, *, effective_permission: EffectivePermission) -> None:
    """Print structured payload summary to stdout. PRD-340 R1/R4: the EXECUTION
    line derives ONLY from the resolved EffectivePermission projection, never from
    summary.tradable/permission. TRADABLE remains an analytical (non-authoritative)
    fact."""
    assert_valid_payload(payload)
    _proj = authority_projection.project(effective_permission)

    summary = payload.get("summary", {})
    sections = payload.get("sections", {})
    meta = payload.get("meta", {})

    print(f"STATUS:          {payload.get('run_status')}")
    print(f"MARKET_REGIME:   {summary.get('market_regime')}")
    print(f"TRADABLE:        {summary.get('tradable')}")
    # PRD-340 R4: EXECUTION is the authoritative posture from the EP projection.
    print(f"EXECUTION:       {_proj.posture}")
    print(f"ROUTER_MODE:     {summary.get('router_mode')}")
    print(f"SYMBOLS_SCANNED: {meta.get('symbols_scanned')}")
    print(f"TOP_TRADES:      {len(sections.get('top_trades', []))}")
    print(f"WATCHLIST:       {len(sections.get('watchlist', []))}")

    rejected = sections.get("rejected", [])
    print(f"REJECTED:        {len(rejected)}")
    # PRD-283 (CB-02): a bare count hides why. Name each options-sizing refusal
    # so a budget-driven no-trade is not indistinguishable from other rejections.
    for entry in rejected:
        if entry.get("stage") == "OPTIONS_SIZING":
            print(
                f"  REFUSED {entry.get('symbol')}: {entry.get('reason')} "
                f"(options sizing)"
            )


def deliver(payload: dict, mode: str, *, effective_permission: EffectivePermission) -> None:
    """Dispatch payload to the named transport mode.

    Modes: "html" | "json" | "cli"
    """
    if mode not in _VALID_MODES:
        raise ValueError(f"Unknown delivery mode {mode!r}; must be one of {sorted(_VALID_MODES)}")
    if mode == "html":
        deliver_html(payload, effective_permission=effective_permission, output_path=_DEFAULT_HTML_PATH)
    elif mode == "json":
        deliver_json(payload, effective_permission=effective_permission, output_path=_DEFAULT_JSON_PATH)
    else:
        deliver_cli(payload, effective_permission=effective_permission)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _write_file(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
