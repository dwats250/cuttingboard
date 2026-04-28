from __future__ import annotations

_SCENARIOS: dict[str, list[dict]] = {
    "RISK_ON": [
        {
            "id": "risk_on_1",
            "condition": "Indices hold above prior_close and trend higher; prior_high as upside target",
            "expected_behavior": "Momentum continuation; strength concentrated in high-beta names",
            "preferred_direction": "LONG",
        },
        {
            "id": "risk_on_2",
            "condition": "VIX spikes intraday above 22; gap_direction determines re-entry bias",
            "expected_behavior": "Long setups pause; hold existing positions, no new entries",
            "preferred_direction": "NEUTRAL",
        },
        {
            "id": "risk_on_3",
            "condition": "gap_direction UP fades within 30 minutes; prior_close as stabilization level",
            "expected_behavior": "Pullback entry available; wait for stabilization before sizing",
            "preferred_direction": "LONG",
        },
    ],
    "RISK_OFF": [
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
    ],
    "NEUTRAL": [
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
    ],
    "CHAOTIC": [
        {
            "id": "chaotic_1",
            "condition": "VIX spike sustained above 30; gap_direction undefined; all setups invalid",
            "expected_behavior": "All setups invalid; stay flat regardless of direction",
            "preferred_direction": "NEUTRAL",
        },
        {
            "id": "chaotic_2",
            "condition": "VIX reverses from spike; price stabilizes above prior_low; monitor only",
            "expected_behavior": "Monitor only; no new entries until regime normalizes",
            "preferred_direction": "NEUTRAL",
        },
    ],
}

_DEFAULT_SCENARIOS: list[dict] = [
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

_INVALIDATION: dict[str, list[str]] = {
    "RISK_ON": [
        "VIX closes above 25 — regime shift to RISK_OFF likely; prior_high at risk",
        "SPY loses prior_low (prior session support) on volume",
    ],
    "RISK_OFF": [
        "VIX drops and holds below 20; prior_close may shift to support",
        "SPY reclaims prior_high intraday",
    ],
    "NEUTRAL": [
        "VIX spike above 25 without intraday recovery; prior_low at risk",
        "SPY moves more than 1% above prior_high or below prior_low on volume",
    ],
    "CHAOTIC": [
        "VIX does not normalize; gap_direction remains undefined; no trade permitted",
    ],
}

_DEFAULT_INVALIDATION: list[str] = [
    "Regime indeterminate; prior_close and gap_direction unavailable; no trade",
]

_VOLATILITY_STATE: dict[str, str] = {
    "CHAOTIC": "ELEVATED",
    "RISK_OFF": "CAUTIONARY",
    "NEUTRAL": "NEUTRAL",
    "RISK_ON": "SUBDUED",
}


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

    scenarios = list(_SCENARIOS.get(market_regime, _DEFAULT_SCENARIOS))

    candidates = contract.get("trade_candidates") or []
    focus_list = [
        {
            "symbol": c.get("symbol") or "",
            "bias": c.get("direction") or "",
            "condition": c.get("strategy_tag") or c.get("entry_mode") or "",
        }
        for c in candidates[:5]
    ]

    invalidation = list(_INVALIDATION.get(market_regime, _DEFAULT_INVALIDATION))
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
            "prior_high": levels.get("prior_high") if levels else None,
            "prior_low": levels.get("prior_low") if levels else None,
            "overnight_high": None,
            "overnight_low": None,
            "gap_direction": levels.get("gap_direction") if levels else None,
        },
        "scenarios": scenarios,
        "focus_list": focus_list,
        "invalidation": invalidation,
    }
