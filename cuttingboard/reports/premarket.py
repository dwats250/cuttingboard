from __future__ import annotations

_VOLATILITY_STATE: dict[str, str] = {
    "CHAOTIC": "ELEVATED",
    "RISK_OFF": "CAUTIONARY",
    "NEUTRAL": "NEUTRAL",
    "RISK_ON": "SUBDUED",
    "EXPANSION": "SUBDUED",
}

# ── Per-regime scenario builders ─────────────────────────────────────────────


def _scenarios_risk_on(gap_direction: str | None) -> list[dict]:
    if gap_direction == "UP":
        return [
            {
                "id": "risk_on_up_1",
                "condition": "Indices gap up and hold above prior_high; momentum continuation setup",
                "expected_behavior": "Continuation long above prior_high; size normally",
                "preferred_direction": "LONG",
            },
            {
                "id": "risk_on_up_2",
                "condition": "gap_direction UP fades within 30 minutes; range_mid as re-entry zone",
                "expected_behavior": "Pullback to range_mid; wait for stabilization before sizing",
                "preferred_direction": "LONG",
            },
        ]
    if gap_direction == "DOWN":
        return [
            {
                "id": "risk_on_down_1",
                "condition": "RISK_ON regime persists despite gap_direction DOWN; range_mid as stabilization",
                "expected_behavior": "Wait for range_mid reclaim; high false-signal risk until then",
                "preferred_direction": "LONG",
            },
            {
                "id": "risk_on_down_2",
                "condition": "Price recovers above prior_low; prior_high becomes next upside reference",
                "expected_behavior": "Long on confirmed reclaim of prior_low",
                "preferred_direction": "LONG",
            },
        ]
    if gap_direction == "FLAT":
        return [
            {
                "id": "risk_on_flat_1",
                "condition": "Flat open near prior_high; breakout setup forming on RISK_ON strength",
                "expected_behavior": "Momentum long on breakout above prior_high on volume",
                "preferred_direction": "LONG",
            },
            {
                "id": "risk_on_flat_2",
                "condition": "range_mid holds as intraday base; prior_high as upside reference",
                "expected_behavior": "Size long on range_mid support",
                "preferred_direction": "LONG",
            },
        ]
    return [
        {
            "id": "risk_on_1",
            "condition": "Indices hold above prior_close and trend higher; prior_high as upside reference",
            "expected_behavior": "Momentum continuation; strength concentrated in high-beta names",
            "preferred_direction": "LONG",
        },
        {
            "id": "risk_on_2",
            "condition": "VIX spikes intraday above 22; gap_direction determines re-entry bias",
            "expected_behavior": "Long setups pause; hold existing positions, no new sizing",
            "preferred_direction": "NEUTRAL",
        },
        {
            "id": "risk_on_3",
            "condition": "gap_direction UP fades within 30 minutes; prior_close as stabilization level",
            "expected_behavior": "Pullback available; wait for stabilization before sizing",
            "preferred_direction": "LONG",
        },
    ]


def _scenarios_expansion(gap_direction: str | None) -> list[dict]:
    if gap_direction == "UP":
        return [
            {
                "id": "expansion_up_1",
                "condition": "Breadth-driven advance extends above prior_high; expansion regime confirmed",
                "expected_behavior": "Full-size continuation; prior_high acts as new support on pullback",
                "preferred_direction": "LONG",
            },
            {
                "id": "expansion_up_2",
                "condition": "gap_direction UP sustained with broad leadership; prior_high not expected to fade",
                "expected_behavior": "Hold full size; expansion regimes typically run past initial levels",
                "preferred_direction": "LONG",
            },
        ]
    if gap_direction == "DOWN":
        return [
            {
                "id": "expansion_down_1",
                "condition": "Expansion regime despite gap_direction DOWN; prior_high as reclaim reference",
                "expected_behavior": "Wait for prior_high reclaim before sizing; gap may fill first",
                "preferred_direction": "LONG",
            },
            {
                "id": "expansion_down_2",
                "condition": "Price stabilizes above range_mid; breadth intact; prior_high remains upside reference",
                "expected_behavior": "Long on range_mid confirmation; prior_high as objective",
                "preferred_direction": "LONG",
            },
        ]
    if gap_direction == "FLAT":
        return [
            {
                "id": "expansion_flat_1",
                "condition": "Expansion regime with flat open; prior_high as breakout reference with breadth",
                "expected_behavior": "Long on volume-confirmed breakout above prior_high",
                "preferred_direction": "LONG",
            },
            {
                "id": "expansion_flat_2",
                "condition": "range_mid holds; expansion breadth intact; no breakdown below prior_low",
                "expected_behavior": "Size long above range_mid; hold through normal pullbacks",
                "preferred_direction": "LONG",
            },
        ]
    return [
        {
            "id": "expansion_1",
            "condition": "Breadth confirmed above prior_high; leadership advancing; expansion intact",
            "expected_behavior": "Continuation long; prior_high acts as base; extension expected",
            "preferred_direction": "LONG",
        },
        {
            "id": "expansion_2",
            "condition": "Indices consolidate above range_mid; breadth narrows but prior_high holds",
            "expected_behavior": "Hold longs above range_mid; reduce new sizing until breadth confirms",
            "preferred_direction": "LONG",
        },
        {
            "id": "expansion_3",
            "condition": "gap_direction undefined; confirm prior_high before full sizing",
            "expected_behavior": "Scale in above prior_high; breadth confirmation required",
            "preferred_direction": "LONG",
        },
    ]


def _scenarios_risk_off(gap_direction: str | None) -> list[dict]:
    if gap_direction == "DOWN":
        return [
            {
                "id": "risk_off_down_1",
                "condition": "Indices break and hold below prior_low; downside continuation expected",
                "expected_behavior": "Downside continuation; maintain defensive short positioning",
                "preferred_direction": "SHORT",
            },
            {
                "id": "risk_off_down_2",
                "condition": "Any bounce into range_mid fails; short bias intact below prior_low",
                "expected_behavior": "Fade bounce at range_mid; maintain short exposure",
                "preferred_direction": "SHORT",
            },
        ]
    if gap_direction == "UP":
        return [
            {
                "id": "risk_off_up_1",
                "condition": "Counter-trend gap into range_mid or prior_high; RISK_OFF bias intact",
                "expected_behavior": "Fade bounce at range_mid or prior_high; short bias maintained",
                "preferred_direction": "SHORT",
            },
            {
                "id": "risk_off_up_2",
                "condition": "gap_direction UP fails to hold prior_high; reversal confirms RISK_OFF",
                "expected_behavior": "Short on rejection of prior_high; prior_low as downside reference",
                "preferred_direction": "SHORT",
            },
        ]
    if gap_direction == "FLAT":
        return [
            {
                "id": "risk_off_flat_1",
                "condition": "Indices test prior_low; breakdown below prior_low signals continuation",
                "expected_behavior": "Short on confirmed break below prior_low on volume",
                "preferred_direction": "SHORT",
            },
            {
                "id": "risk_off_flat_2",
                "condition": "Bounce into range_mid provides fade opportunity; prior_low as downside reference",
                "expected_behavior": "Fade at range_mid; hold through prior_low",
                "preferred_direction": "SHORT",
            },
        ]
    return [
        {
            "id": "risk_off_1",
            "condition": "Indices break below prior_low; downside continuation expected",
            "expected_behavior": "Downside continuation; defensive positioning maintained",
            "preferred_direction": "SHORT",
        },
        {
            "id": "risk_off_2",
            "condition": "Brief bounce into range_mid or prior_high; fade bounce",
            "expected_behavior": "Fade bounce; short bias intact",
            "preferred_direction": "SHORT",
        },
        {
            "id": "risk_off_3",
            "condition": "VIX reaches 30+ above prior_high volatility zone and stalls or reverses",
            "expected_behavior": "Reduce short exposure; potential VIX exhaustion",
            "preferred_direction": "NEUTRAL",
        },
    ]


def _scenarios_neutral(gap_direction: str | None) -> list[dict]:
    return [
        {
            "id": "neutral_1",
            "condition": "Indices hold within prior_high to prior_low range; no directional bias",
            "expected_behavior": "Range-bound; premium selling opportunity; no directional bias",
            "preferred_direction": "NEUTRAL",
        },
        {
            "id": "neutral_2",
            "condition": "SPY breaks above prior_high on above-average volume",
            "expected_behavior": "Trend shift signal; initiate LONG on confirmation",
            "preferred_direction": "LONG",
        },
        {
            "id": "neutral_3",
            "condition": "SPY breaks below prior_low on above-average volume",
            "expected_behavior": "Trend shift signal; initiate SHORT on confirmation",
            "preferred_direction": "SHORT",
        },
    ]


def _scenarios_chaotic(gap_direction: str | None) -> list[dict]:
    return [
        {
            "id": "chaotic_1",
            "condition": "VIX spike sustained above 30; gap_direction undefined; all setups invalid",
            "expected_behavior": "All setups invalid; stay flat regardless of direction",
            "preferred_direction": "NEUTRAL",
        },
        {
            "id": "chaotic_2",
            "condition": "VIX reverses from spike; price stabilizes above prior_low; monitor only",
            "expected_behavior": "Monitor only; no new sizing until regime normalizes",
            "preferred_direction": "NEUTRAL",
        },
    ]


def _scenarios_unknown(gap_direction: str | None) -> list[dict]:
    return [
        {
            "id": "unknown_1",
            "condition": "Regime unavailable; gap_direction and prior_close indeterminate; no trade",
            "expected_behavior": "No trade; wait for regime resolution",
            "preferred_direction": "NEUTRAL",
        },
        {
            "id": "unknown_2",
            "condition": "System without confirmed regime; prior_high and prior_low unresolved; stay flat",
            "expected_behavior": "Stay flat; do not size any position",
            "preferred_direction": "NEUTRAL",
        },
    ]


def _generate_scenarios(regime: str | None, gap_direction: str | None, levels: dict) -> list[dict]:
    if regime == "RISK_ON":
        return _scenarios_risk_on(gap_direction)
    if regime == "EXPANSION":
        return _scenarios_expansion(gap_direction)
    if regime == "RISK_OFF":
        return _scenarios_risk_off(gap_direction)
    if regime == "NEUTRAL":
        return _scenarios_neutral(gap_direction)
    if regime == "CHAOTIC":
        return _scenarios_chaotic(gap_direction)
    return _scenarios_unknown(gap_direction)


# ── Invalidation generator ───────────────────────────────────────────────────


def _generate_invalidation(regime: str | None, gap_direction: str | None, scenarios: list[dict]) -> list[str]:
    if regime in ("RISK_ON", "EXPANSION"):
        return [
            "VIX closes above 25 — regime shift to RISK_OFF likely; prior_high at risk",
            "SPY loses prior_low on volume; LONG thesis invalidated",
        ]
    if regime == "RISK_OFF":
        return [
            "VIX drops and holds below 20; prior_close may shift to support; SHORT thesis weakening",
            "SPY reclaims prior_low on volume; downside continuation invalidated",
        ]
    if regime == "NEUTRAL":
        return [
            "VIX spike above 25 without intraday recovery; prior_low at risk",
            "SPY moves more than 1% above prior_high or below prior_low on volume",
        ]
    if regime == "CHAOTIC":
        return [
            "VIX does not normalize; gap_direction remains undefined; no trade permitted",
            "Price fails to reclaim prior_low after spike; chaotic regime persists",
        ]
    return [
        "Regime indeterminate; prior_close and gap_direction unavailable; no trade",
        "System state unresolved; prior_high and prior_low unreliable; stay flat",
    ]


# ── Public builder ───────────────────────────────────────────────────────────


def build_premarket_report(contract: dict, levels: dict | None = None) -> dict:
    ss = contract.get("system_state") or {}
    mc = contract.get("market_context") or {}
    correlation = contract.get("correlation")

    market_regime: str | None = ss.get("market_regime")
    tradable: bool = bool(ss.get("tradable", False))
    stay_flat_reason: str | None = ss.get("stay_flat_reason")
    status: str = contract.get("status") or ""

    volatility_state: str | None = _VOLATILITY_STATE.get(market_regime) if market_regime else None
    correlation_state: str | None = correlation.get("state") if correlation else None
    correlation_risk_modifier: float | None = correlation.get("risk_modifier") if correlation else None
    expansion_enabled: bool | None = mc.get("continuation_enabled")

    _levels = levels or {}
    gap_direction: str | None = _levels.get("gap_direction")

    scenarios = _generate_scenarios(market_regime, gap_direction, _levels)

    candidates = contract.get("trade_candidates") or []
    focus_list = [
        {
            "symbol": c.get("symbol") or "",
            "bias": c.get("direction") or "",
            "condition": c.get("strategy_tag") or c.get("entry_mode") or "",
        }
        for c in candidates[:5]
    ]

    invalidation = _generate_invalidation(market_regime, gap_direction, scenarios)
    if not tradable and stay_flat_reason:
        invalidation.insert(0, f"System stay-flat: {stay_flat_reason}")
    elif not tradable:
        invalidation.insert(0, "Tradable == False: no entries permitted this session")

    return {
        "system_state": {
            "market_regime": market_regime,
            "tradable": tradable,
            "stay_flat_reason": stay_flat_reason,
            "status": status,
        },
        "macro_context": {
            "volatility_state": volatility_state,
            "correlation_state": correlation_state,
            "correlation_risk_modifier": correlation_risk_modifier,
            "expansion_enabled": expansion_enabled,
        },
        "key_levels": {
            "prior_high": _levels.get("prior_high"),
            "prior_low": _levels.get("prior_low"),
            "overnight_high": None,
            "overnight_low": None,
            "gap_direction": gap_direction,
        },
        "scenarios": scenarios,
        "focus_list": focus_list,
        "invalidation": invalidation,
    }
