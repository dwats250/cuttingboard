"""NS-4B MARKET MOVEMENT card (PRD-311): read-only, baseline-neutral display card.

Pure consumer of ``logs/watchlist_snapshot.json`` (the watchlist sidecar,
schema_version 2). All validation, grouping, ordering, and fragment generation
live here; ``dashboard_renderer`` only loads and emits (R4). On any absence or
contract violation the card suppresses to the empty string, so the dashboard
stays byte-identical to the pre-card baseline (R4/R5).

Imports only stdlib and the pure producer ``watchlist_sidecar`` (which drives no
decision surface) to enforce EXACT full-12 symbol identity against the exact set
the producer emits (R4/F6) — the registry stays a single-consumer module. It
holds NO wall clock: freshness is the artifact's ``generated_at`` capture time
only (R5/G1).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from cuttingboard.watchlist_sidecar import WATCHLIST_SYMBOLS

_SOURCE = "watchlist"
_SCHEMA_VERSION = 2
_ET = ZoneInfo("America/New_York")
_GROUP_ORDER = ("INDEX", "METALS", "ENERGY", "TECH", "HIGH_BETA")

# Expected full-12 identity, taken directly from the producer's projection so the
# reader's expected set can never drift from what the writer emits. Maps each
# expected symbol -> (primary_group, registry_index).
_EXPECTED: dict[str, tuple[str, int]] = {
    sym: (primary_group, registry_index)
    for sym, _theme, _reason, primary_group, registry_index in WATCHLIST_SYMBOLS
}


def load_watchlist_snapshot(path: Path) -> dict | None:
    """Soft loader: never raises; returns a dict on success, None on missing /
    malformed / non-dict, so a bad artifact never breaks publish."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _pct_or_invalid(x):
    """R4: `daily_change_pct` is float-or-null. Returns the float, None (for a
    null cell), or _INVALID for anything else (int/bool/NaN/Inf/str) so the whole
    artifact is rejected — a non-float number is NOT silently coerced."""
    if x is None:
        return None
    if isinstance(x, bool) or not isinstance(x, float) or not math.isfinite(x):
        return _INVALID
    return x


_INVALID = object()


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
class MovementCard:
    """Immutable, display-ready model: ordered (group, chips) lines + capture clock."""

    groups: tuple[tuple[str, tuple[str, ...]], ...]
    captured_et: str


def _chip(symbol: str, pct: float | None) -> str:
    """Movement chip: null -> `SYM n/a`; honest zero -> `SYM 0.0%`; else signed
    one-decimal `SYM +X.X%` (R1'/R5). A null is never fabricated as 0.0."""
    if pct is None:
        return f"{symbol} n/a"
    if pct == 0.0:
        return f"{symbol} 0.0%"
    return f"{symbol} {pct:+.1f}%"


def build_movement_card(snapshot) -> MovementCard | None:
    """Validate the artifact against the strict full-12 acceptance contract
    (R4) and build the model, or return None to suppress the whole card (R5)."""
    if not isinstance(snapshot, dict):
        return None
    if snapshot.get("source") != _SOURCE:
        return None
    sv = snapshot.get("schema_version")
    if not (isinstance(sv, int) and not isinstance(sv, bool) and sv == _SCHEMA_VERSION):
        return None
    captured = _parse_aware(snapshot.get("generated_at"))
    if captured is None:
        return None
    symbols = snapshot.get("symbols")
    if not isinstance(symbols, dict) or set(symbols) != set(_EXPECTED):
        return None

    # Per-symbol identity + type checks; collect (registry_index, chip) per group.
    by_group: dict[str, list[tuple[int, str]]] = {g: [] for g in _GROUP_ORDER}
    for symbol, (exp_group, exp_index) in _EXPECTED.items():
        row = symbols.get(symbol)
        if not isinstance(row, dict):
            return None
        if row.get("symbol") != symbol:
            return None
        if row.get("primary_group") != exp_group:
            return None
        ri = row.get("registry_index")
        if isinstance(ri, bool) or not isinstance(ri, int) or ri != exp_index:
            return None
        pct = _pct_or_invalid(row.get("daily_change_pct"))
        if pct is _INVALID:
            return None  # R4: daily_change_pct is float-or-null; else unusable
        by_group[exp_group].append((exp_index, _chip(symbol, pct)))

    groups = tuple(
        (g, tuple(chip for _, chip in sorted(by_group[g])))
        for g in _GROUP_ORDER
        if by_group[g]
    )
    return MovementCard(
        groups=groups,
        captured_et=captured.astimezone(_ET).strftime("%H:%M"),
    )


def render_movement_card_html(card: MovementCard | None) -> str:
    """Format the model to a compact HTML fragment; empty string when suppressed.
    Reuses existing dashboard CSS classes and adds no styles (R4)."""
    if card is None:
        return ""
    rows = [
        f'    <div class="label">{group}</div><div class="value">{" &nbsp; ".join(chips)}</div>'
        for group, chips in card.groups
    ]
    return "\n".join(
        [
            '<div class="block" id="market-movement">',
            "  <h2>MARKET MOVEMENT</h2>",
            '  <div class="kv-grid">',
            *rows,
            "  </div>",
            f'  <div class="label">captured {card.captured_et} ET</div>',
            "</div>",
        ]
    )


def render_fragment(snapshot) -> str:
    """Compose loader-validated model -> HTML. Empty string suppresses the card.
    Holds no wall clock: freshness is the artifact's generated_at only (R5/G1)."""
    return render_movement_card_html(build_movement_card(snapshot))
