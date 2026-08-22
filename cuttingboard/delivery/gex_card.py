"""GEX-2 free board card (PRD-309): baseline-neutral, display-only GEX context card.

Pure, stdlib-only consumer of ``logs/gex_snapshot.json`` (the GEX-1 sidecar) with
NO decision authority. Renders only a fresh, in-domain artifact; on any absence,
staleness, or domain violation it suppresses to nothing so the dashboard stays
byte-identical to the pre-GEX baseline (R1/R6/D6). All GEX validation and math
live here; the renderer only loads and emits. Imports no ``cuttingboard`` module;
imported only by the renderer (isolation R17).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Identity guards -- must match tools/gex_snapshot.py exactly (D5a / Event-2 F4).
_SOURCE = "cboe_delayed_quotes"
_DATA_DELAY = "~15 min delayed (REPORTED; Cboe delayed_quotes posture)"
_SCHEMA_VERSION = 1
_STALE_MAX = timedelta(hours=24)  # Q4 single freshness knob
_FUTURE_SKEW = timedelta(minutes=5)
_ET = ZoneInfo("America/New_York")

# The producer's exact recognized "unavailable" reason tokens (D5a coherence).
_REASONS = {
    "dominant_net_gamma": {"all_net_gamma_zero"},
    "call_wall": {"no_eligible_calls", "no_nonzero_call_gex"},
    "put_wall": {"no_eligible_puts", "no_nonzero_put_gex"},
}
_ZERO_DTE_REASON = "zero_abs_gex_denominator"
_INVALID = object()  # sentinel: reason/value incoherence -> suppress the whole card


def load_gex_snapshot(path: Path) -> dict | None:
    """Soft loader for the GEX sidecar: never raises; returns a dict on success,
    None on missing / malformed / non-dict, so a bad artifact never breaks publish."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _real(x) -> float | None:
    """Finite, non-boolean int/float -> float; else None (G6: invalid, not coerced)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        return None
    return float(x)


def _wall_strike(obj, reasons):
    """Coherence for call/put/dominant (D5a/R15): a valid strike float; None (typed-
    unavailable via a recognized reason); or _INVALID (contradictory -> suppress)."""
    if not isinstance(obj, dict):
        return _INVALID
    strike, reason = obj.get("strike"), obj.get("reason")
    if strike is None:
        return None if reason in reasons else _INVALID
    s = _real(strike)
    if s is None or s <= 0 or reason is not None:
        return _INVALID
    return s


def _zero_dte_share(obj):
    """0DTE coherence + honest zero (D5a/R11/R15): a share float in [0,1] (incl. 0.0);
    None (typed-unavailable); or _INVALID (contradictory -> suppress)."""
    if not isinstance(obj, dict):
        return _INVALID
    share, reason = obj.get("share"), obj.get("reason")
    if share is None:
        return None if reason == _ZERO_DTE_REASON else _INVALID
    v = _real(share)
    if v is None or not (0.0 <= v <= 1.0) or reason is not None:
        return _INVALID
    return v


def _parse_aware(value) -> datetime | None:
    """ISO-8601 -> tz-aware datetime; None if not a string / naive / malformed."""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else None


@dataclass(frozen=True)
class GexCard:
    """Immutable, display-ready presentation model (no raw producer internals)."""

    net_usd: float
    dominant: tuple[float, float]           # (strike, distance_pct)
    call_wall: tuple[float, float] | None
    put_wall: tuple[float, float] | None
    zero_dte_share: float | None
    as_of_et: str


def build_gex_card(snapshot, *, now: datetime) -> GexCard | None:
    """Validate against the frozen admissibility domain (D5a) and build the model,
    or return None to suppress. ``now`` is injected so staleness is deterministic."""
    if not isinstance(snapshot, dict):
        return None
    sv = snapshot.get("schema_version")
    if not (isinstance(sv, int) and not isinstance(sv, bool) and sv == _SCHEMA_VERSION):
        return None
    if snapshot.get("source") != _SOURCE or snapshot.get("data_delay") != _DATA_DELAY:
        return None
    spot = snapshot.get("spot")
    spot_val = _real(spot.get("value")) if isinstance(spot, dict) else None
    if spot_val is None or spot_val <= 0:
        return None
    net = _real(snapshot.get("gex_total_1pct_usd"))
    if net is None:
        return None
    fetched = _parse_aware(snapshot.get("fetched_at_utc"))
    if fetched is None or (fetched - now) > _FUTURE_SKEW or (now - fetched) > _STALE_MAX:
        return None
    # Dominant anchor is required (Q6): unavailable OR invalid -> suppress the card.
    dom = _wall_strike(snapshot.get("dominant_net_gamma"), _REASONS["dominant_net_gamma"])
    if dom is _INVALID or dom is None:
        return None
    # Optional rows: invalid suppresses the card; typed-unavailable omits the row.
    call = _wall_strike(snapshot.get("call_wall"), _REASONS["call_wall"])
    put = _wall_strike(snapshot.get("put_wall"), _REASONS["put_wall"])
    zero = _zero_dte_share(snapshot.get("zero_dte"))
    if call is _INVALID or put is _INVALID or zero is _INVALID:
        return None

    def dist(strike: float) -> float:
        return (strike / spot_val - 1.0) * 100.0

    return GexCard(
        net_usd=net,
        dominant=(dom, dist(dom)),
        call_wall=(call, dist(call)) if call is not None else None,
        put_wall=(put, dist(put)) if put is not None else None,
        zero_dte_share=zero,
        as_of_et=fetched.astimezone(_ET).strftime("%H:%M"),
    )


def _fmt_strike(strike: float) -> str:
    return f"{int(strike)}" if float(strike).is_integer() else f"{strike:g}"


def _fmt_net(net_usd: float) -> str:
    b = net_usd / 1e9
    return f"{'-' if b < 0 else '+'}${abs(b):.1f}B"


def _kv(label: str, value: str) -> str:
    return f'    <div class="label">{label}</div><div class="value">{value}</div>'


def _row(label: str, pair: tuple[float, float]) -> str:
    strike, dist_pct = pair
    return _kv(label, f"{_fmt_strike(strike)} &nbsp; {dist_pct:+.2f}%")


def render_gex_card_html(card: GexCard | None) -> str:
    """Format the model to a compact HTML fragment; empty string when suppressed.
    Reuses existing dashboard CSS classes and adds no styles (D7/R1)."""
    if card is None:
        return ""
    rows = [_kv("Net", f"{_fmt_net(card.net_usd)} *"), _row("Dominant", card.dominant)]
    if card.call_wall is not None:
        rows.append(_row("Call wall", card.call_wall))
    if card.put_wall is not None:
        rows.append(_row("Put wall", card.put_wall))
    if card.zero_dte_share is not None:
        rows.append(_kv("0DTE", f"{card.zero_dte_share * 100:.1f}%"))
    return "\n".join(
        [
            '<div class="block" id="gex-context">',
            '  <h2>GEX <span class="label">(context only)</span></h2>',
            '  <div class="kv-grid">',
            *rows,
            "  </div>",
            f'  <div class="label">as of {card.as_of_et} ET &middot; Cboe ~15m delayed source</div>',
            '  <div class="label">* net is signed under a configured positioning '
            "assumption; positioning is not measured.</div>",
            "</div>",
        ]
    )


def render_fragment(snapshot, *, now: datetime) -> str:
    """Compose loader-validated model -> HTML. Empty string suppresses the card."""
    return render_gex_card_html(build_gex_card(snapshot, now=now))
