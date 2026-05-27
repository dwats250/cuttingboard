"""PRD-158 § 4.3 — dashboard decision integrator.

Renderer-bound translation pass that collapses contradictory dashboard
state into trader-facing conclusions. Not a new architecture layer,
subsystem, class hierarchy, or state model.

Four rules with explicit precedence (see PRD-158 § 4.3 and the
docs/DECISIONS.md guardrail entry for the drift constraint):

    Rule 1 (symbol scope): required-data collapse
    Rule 2 (screen scope): regime-vs-setup-availability
    Rule 3 (screen scope): directional conflict collapse
    Rule 4 (screen scope): empty-tier suppression

This module does NOT recompute regime, macro bias, gates, grades, or
setup logic. It consumes existing values and emits a renderable view
in decision language.
"""

from __future__ import annotations

_REQUIRED_SYMBOL_FIELDS: tuple[str, ...] = (
    "current_price",
    "setup_direction",
    "setup_type",
    "trigger",
    "invalidation",
)

_LONG_DIRECTIONS = frozenset({"long", "LONG", "bullish", "BULLISH"})
_SHORT_DIRECTIONS = frozenset({"short", "SHORT", "bearish", "BEARISH"})

RULE2_LONG_VERDICT = "No qualifying long setups currently available."
RULE2_SHORT_VERDICT = "No qualifying short setups currently available."
RULE3_MIXED_VERDICT = (
    "Mixed tape — directional trades require symbol-level confirmation."
)


def dashboard_integrator(payload: dict) -> dict:
    """Collapse contradictory dashboard state into trader-facing output.

    Input dict shape (all keys optional; integrator defends against missing
    or None values):

        regime_permission: "longs" | "shorts" | "stand_down" | None
        macro_bias_direction: "long" | "short" | "mixed" | None
        symbols: {
            symbol: {
                current_price, setup_direction, setup_type, trigger,
                invalidation, grade, ...
            }
        }
        tiers: ordered iterable of (tier_id, tier_label, [symbol, ...])

    Output dict:

        symbol_skips: {symbol: trader-facing skip line}
        screen_verdicts: list of trader-facing verdict lines (Rules 2/3)
        rendered_tiers: list of (tier_id, tier_label, [symbol, ...]) with
            Rule 1 symbol drops and Rule 4 empty-tier suppression applied
        suppress: {permission, outcome, macro_bias} booleans indicating
            which raw labels the renderer must hide
    """
    symbols: dict[str, dict] = payload.get("symbols") or {}
    tiers = payload.get("tiers") or []
    regime_permission = payload.get("regime_permission")
    macro_bias = payload.get("macro_bias_direction")

    # Rule 1 — required-data collapse (symbol scope).
    symbol_skips: dict[str, str] = {}
    for sym, fields in symbols.items():
        if _missing_required_fields(fields):
            symbol_skips[sym] = (
                f"{sym} skipped — required market data unavailable."
            )

    qualifying_directions = _qualifying_setup_directions(symbols, symbol_skips)

    screen_verdicts: list[str] = []
    suppress = {"permission": False, "outcome": False, "macro_bias": False}

    # Rule 2 — regime-vs-setup-availability (screen scope).
    rule2_verdict = _rule2_verdict(regime_permission, qualifying_directions)
    if rule2_verdict is not None:
        screen_verdicts.append(rule2_verdict)
        suppress["permission"] = True
        suppress["outcome"] = True

    # Rule 3 — directional conflict collapse (screen scope).
    if _directional_conflict(regime_permission, macro_bias, qualifying_directions):
        screen_verdicts.append(RULE3_MIXED_VERDICT)
        suppress["macro_bias"] = True
        suppress["permission"] = True
        suppress["outcome"] = True

    # Rule 4 — empty-tier suppression (screen scope). Drops tier rows whose
    # candidate list is empty after Rule 1 symbol drops.
    rendered_tiers: list[tuple[str, str, list[str]]] = []
    for tier_id, tier_label, tier_syms in tiers:
        kept = [s for s in tier_syms if s not in symbol_skips]
        if kept:
            rendered_tiers.append((tier_id, tier_label, kept))

    return {
        "symbol_skips": symbol_skips,
        "screen_verdicts": screen_verdicts,
        "rendered_tiers": rendered_tiers,
        "suppress": suppress,
    }


def _missing_required_fields(fields: object) -> bool:
    if not isinstance(fields, dict):
        return True
    for key in _REQUIRED_SYMBOL_FIELDS:
        value = fields.get(key)
        if value is None or value == "":
            return True
    return False


def _qualifying_setup_directions(
    symbols: dict[str, dict],
    skips: dict[str, str],
) -> frozenset[str]:
    directions: set[str] = set()
    for sym, fields in symbols.items():
        if sym in skips:
            continue
        direction = (fields or {}).get("setup_direction")
        if direction in _LONG_DIRECTIONS:
            directions.add("long")
        elif direction in _SHORT_DIRECTIONS:
            directions.add("short")
    return frozenset(directions)


def _rule2_verdict(
    regime_permission: object,
    qualifying_directions: frozenset[str],
) -> str | None:
    if regime_permission == "longs" and "long" not in qualifying_directions:
        return RULE2_LONG_VERDICT
    if regime_permission == "shorts" and "short" not in qualifying_directions:
        return RULE2_SHORT_VERDICT
    return None


def _directional_conflict(
    regime_permission: object,
    macro_bias: object,
    qualifying_directions: frozenset[str],
) -> bool:
    # Conflict requires all three signals expressed AND at least two distinct
    # directions among them.
    if regime_permission not in ("longs", "shorts"):
        return False
    if macro_bias not in ("long", "short"):
        return False
    if not qualifying_directions:
        return False

    regime_dir = "long" if regime_permission == "longs" else "short"
    distinct = {regime_dir, macro_bias, *qualifying_directions}
    return len(distinct) > 1
