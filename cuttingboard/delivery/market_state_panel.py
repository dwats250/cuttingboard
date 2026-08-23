"""PRD-312 MARKET STATE panel: hourly-first, provenance-first five-axis display.

Pure delivery-layer assembly from carriers the renderer already resolves. Each of
the five axis rows renders an existing value OR an honest ``unavailable``, each
with its OWN provenance clock -- NO global synchronized "as of", NO
score/verdict/confluence, NO prediction, NO INTRADAY row. It reuses the existing
GEX / Movement card semantics (qualifiers preserved) but is a persistent
legibility panel, not a baseline-neutral card: a card's ``None`` becomes a visible
``unavailable`` row. To keep the GEX artifact owned solely by ``gex_card`` (PRD-309
R17), the panel never reads a raw snapshot -- the renderer passes the resolved
``GexCard`` / ``MovementCard`` objects, which the panel formats (duck-typed).
Drives no decision surface. Owner ruling 2026-08-22: rendered before System State;
POSITIONING preserves the configured-assumption + ~15m Cboe qualifiers;
PARTICIPATION is availability/provenance only (never "12/12" while any symbol n/a).
"""

from __future__ import annotations

import html
from datetime import datetime
from zoneinfo import ZoneInfo

_ET = ZoneInfo("America/New_York")
_UNAVAILABLE = "unavailable"
# The exact ordered five axes (owner ruling; M10 pins this -- no INTRADAY row).
_AXES = ("ENVIRONMENT", "PERMISSION", "POSITIONING", "PARTICIPATION", "EVENT RISK")


def _run_provenance(run_clock: datetime | None) -> str:
    """The hourly run/capture clock as ``as of HH:MM ET`` (or unavailable)."""
    if isinstance(run_clock, datetime) and run_clock.tzinfo is not None:
        return f"as of {run_clock.astimezone(_ET).strftime('%H:%M')} ET"
    return "as of unavailable"


def _environment(market_regime, run_clock) -> str:
    if not isinstance(market_regime, str) or not market_regime.strip():
        return _UNAVAILABLE
    return f"{html.escape(market_regime)} &middot; {_run_provenance(run_clock)}"


def _permission(permission, run_clock) -> str:
    if not isinstance(permission, str) or not permission.strip():
        return _UNAVAILABLE
    return f"{html.escape(permission)} &middot; {_run_provenance(run_clock)}"


def _fmt_net(net_usd: float) -> str:
    # Mirrors gex_card._fmt_net EXACTLY (kept in sync): the POSITIONING net must
    # read identically to the GEX card's Net line. Signed $B, one decimal.
    b = net_usd / 1e9
    return f"{'-' if b < 0 else '+'}${abs(b):.1f}B"


def _positioning(gex_card_obj) -> str:
    """Reuse the existing GEX semantics from the resolved card: preserve the
    fetched/as-of time, the ~15m delayed Cboe qualifier, AND the configured-
    positioning-assumption / not-measured qualifier. None (absent/suppressed)
    -> unavailable. No new interpretation."""
    if gex_card_obj is None:
        return _UNAVAILABLE
    return (
        f"net {_fmt_net(gex_card_obj.net_usd)} * &middot; "
        f"as of {gex_card_obj.as_of_et} ET, Cboe ~15m delayed &middot; "
        "* net signed under a configured positioning assumption; "
        "positioning is not measured"
    )


def _participation(movement_card_obj) -> str:
    """Reuse the existing Movement semantics from the resolved card: availability
    + generated_at capture provenance + honest partial state. Never claims 12/12
    while any symbol is n/a; creates no breadth/leadership/direction/score. None
    (absent/suppressed) -> unavailable."""
    if movement_card_obj is None:
        return _UNAVAILABLE
    chips = [chip for _group, chips in movement_card_obj.groups for chip in chips]
    total = len(chips)
    na = sum(1 for chip in chips if chip.endswith(" n/a"))
    usable = total - na
    captured = (
        f"{usable}/{total} captured" if na == 0
        else f"{usable}/{total} captured, {na} n/a"
    )
    return f"{captured} &middot; captured {movement_card_obj.captured_et} ET"


def _event_risk(red_folder) -> str:
    """Existing red-folder 48h calendar semantics; no invented feed timestamp.
    Loader error / absent -> unavailable."""
    if not isinstance(red_folder, dict) or not red_folder.get("ok"):
        return _UNAVAILABLE
    events = red_folder.get("events") or []
    n = len(events)
    label = f"{n} events in 48h" if n else "no events in 48h"
    return f"{label} &middot; red-folder calendar"


def _row(label: str, value: str) -> str:
    return f'    <div class="label">{label}</div><div class="value">{value}</div>'


def render_fragment(
    *,
    market_regime,
    permission,
    run_clock: datetime | None,
    gex_card_obj,
    movement_card_obj,
    red_folder,
) -> str:
    """Build the persistent five-axis MARKET STATE block. Always renders exactly
    the five axis rows (M10); each is a value or an honest ``unavailable`` with its
    own provenance. Reuses the existing ``.kv-grid`` / ``.block`` CSS; adds none."""
    values = {
        "ENVIRONMENT": _environment(market_regime, run_clock),
        "PERMISSION": _permission(permission, run_clock),
        "POSITIONING": _positioning(gex_card_obj),
        "PARTICIPATION": _participation(movement_card_obj),
        "EVENT RISK": _event_risk(red_folder),
    }
    rows = [_row(axis, values[axis]) for axis in _AXES]
    return "\n".join(
        [
            '<div class="block" id="market-state">',
            "  <h2>MARKET STATE</h2>",
            '  <div class="kv-grid">',
            *rows,
            "  </div>",
            "</div>",
        ]
    )
