"""
Hardcoded fixture symbol data for dashboard demo/fixture mode (PRD-078).

Schema matches market_map symbol entries read by _render_candidate_card.
"""

FIXTURE_SYMBOLS: dict[str, dict] = {
    "SPY": {
        "symbol": "SPY",
        "grade": "A+",
        "bias": "LONG",
        "structure": "BREAKOUT",
        "setup_state": "TRIGGERED",
        "trade_framing": {
            "entry": "585.00",
            "if_now": "Watch break above 585 with volume confirmation",
            "downgrade": "Close below 582 invalidates setup",
        },
        "invalidation": ["Close below 582"],
        "reason_for_grade": "Demo fixture — not live data",
    },
    "QQQ": {
        "symbol": "QQQ",
        "grade": "A",
        "bias": "LONG",
        "structure": "CONTINUATION",
        "setup_state": "DEVELOPING",
        "trade_framing": {
            "entry": "495.00",
            "if_now": "Wait for consolidation hold above 493",
            "downgrade": "Close below 491 negates continuation",
        },
        "invalidation": ["Close below 491"],
        "reason_for_grade": "Demo fixture — not live data",
    },
    "GDX": {
        "symbol": "GDX",
        "grade": "B",
        "bias": "LONG",
        "structure": "RANGE_SUPPORT",
        "setup_state": "EARLY",
        "trade_framing": {
            "entry": "42.50",
            "if_now": "Watch for hold above 42.00",
            "downgrade": "Close below 41.50 removes setup",
        },
        "invalidation": ["Close below 41.50"],
        "reason_for_grade": "Demo fixture — not live data",
    },
}
