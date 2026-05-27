"""Shared plain helper functions for dashboard renderer tests."""

from __future__ import annotations

import re


def _macro_drivers(
    vix: float = 0.05,
    dxy: float = -0.01,
    tnx: float = 0.02,
    btc: float = 0.03,
) -> dict:
    return {
        "volatility": {"symbol": "^VIX",     "level": 18.0,    "change_pct": vix},
        "dollar":     {"symbol": "DX-Y.NYB", "level": 104.0,   "change_pct": dxy},
        "rates":      {"symbol": "^TNX",     "level": 4.5,     "change_pct": tnx, "change_bps": 2.0},
        "bitcoin":    {"symbol": "BTC-USD",  "level": 65000.0, "change_pct": btc},
    }


def _payload(
    *,
    top_trades: list | None = None,
    trade_decision_detail: list | None = None,
    validation_halt_detail: dict | None = None,
    tradable: bool | None = True,
    market_regime: str = "RISK_ON",
    timestamp: str = "2026-04-28T12:00:00Z",
    macro_drivers: dict | None = None,
) -> dict:
    return {
        "schema_version": "1.0",
        "run_status": "OK",
        "meta": {"timestamp": timestamp, "symbols_scanned": 5, "generation_id": "test-gen-001"},
        "macro_drivers": macro_drivers if macro_drivers is not None else {},
        "summary": {
            "market_regime": market_regime,
            "tradable": tradable,
            "router_mode": "MIXED",
        },
        "sections": {
            "top_trades": top_trades if top_trades is not None else [],
            "watchlist": [],
            "rejected": [],
            "option_setups_detail": [],
            "chain_results_detail": [],
            "continuation_audit": None,
            "watch_summary_detail": None,
            "validation_halt_detail": validation_halt_detail,
            "trade_decision_detail": trade_decision_detail if trade_decision_detail is not None else [],
        },
    }


def _run(
    *,
    status: str = "SUCCESS",
    regime: str = "RISK_ON",
    posture: str = "CONTROLLED_LONG",
    confidence: float = 0.75,
    system_halted: bool = False,
    kill_switch: bool = False,
    errors: list | None = None,
    data_status: str = "ok",
    outcome: str = "NO_TRADE",
    permission: bool | None = None,
) -> dict:
    return {
        "run_id":       "live-20260428T120000Z",
        "generation_id": "test-gen-001",
        "status":       status,
        "regime":       regime,
        "posture":      posture,
        "confidence":   confidence,
        "system_halted": system_halted,
        "kill_switch":  kill_switch,
        "errors":       errors if errors is not None else [],
        "data_status":  data_status,
        "outcome":      outcome,
        "permission":   permission,
        "mode":         "LIVE",
        "timestamp":    "2026-04-28T12:00:00Z",
        "warnings":     [],
    }


_HIGH_GRADES_DEFAULTS = frozenset({"A+", "A", "B"})


def _mm_symbol(
    symbol: str = "SPY",
    grade: str = "A",
    bias: str = "BULL",
    structure: str = "UPTREND",
    setup_state: str | None = None,
    trade_framing: dict | None = None,
    invalidation: list | None = None,
    reason_for_grade: str | None = None,
) -> dict:
    # PRD-158 § 4.3: defaults mirror the L8 _build_symbol_record contract.
    # In production, high-grade symbols (A+/A/B) always carry current_price,
    # setup_state, trade_framing.entry, and a non-empty invalidation list.
    # Test fixtures inherit that shape so the dashboard integrator's Rule 1
    # (required-data collapse) does not fire on minimal high-grade fixtures.
    is_high_grade = grade in _HIGH_GRADES_DEFAULTS
    if setup_state is None and is_high_grade:
        setup_state = "DEVELOPING"
    if trade_framing is None:
        if is_high_grade:
            direction = "SHORT" if bias in ("BEAR", "BEARISH") else "LONG"
            trade_framing = {
                "direction": direction,
                "entry": "hold above reference with constructive follow-through",
                "if_now": "WAIT",
            }
        else:
            trade_framing = {}
    if invalidation is None:
        invalidation = (
            ["loses reference with weak recovery", "momentum fades below trend"]
            if is_high_grade
            else []
        )
    return {
        "symbol":               symbol,
        "grade":                grade,
        "bias":                 bias,
        "structure":            structure,
        "setup_state":          setup_state,
        "confidence":           "MEDIUM",
        "current_price":        100.0 if is_high_grade else None,
        "watch_zones":          [],
        "fib_levels":           None,
        "what_to_look_for":     [],
        "invalidation":         invalidation,
        "preferred_trade_structure": None,
        "reason_for_grade":     reason_for_grade,
        "trade_framing":        trade_framing,
        "asset_group":          "EQUITY",
    }


def _market_map(symbols: dict | None = None) -> dict:
    s = symbols or {}
    return {
        "schema_version":   "market_map.v1",
        "generation_id":    "test-gen-001",
        "generated_at":     "2026-04-28T12:00:00Z",
        "primary_symbols":  list(s.keys()),
        "symbols":          s,
    }


def _macro_tape_block(html: str) -> str:
    return html.split('id="macro-tape"', 1)[1].split('id="macro-pressure"', 1)[0]


def _macro_tape_value_slots(html: str) -> list[tuple[str, str]]:
    block = _macro_tape_block(html)
    return re.findall(
        r'<span class="macro-tape-value" data-symbol="([^"]+)">([^<]+)</span>',
        block,
    )


def _trade(symbol: str = "SPY", direction: str = "LONG") -> dict:
    return {"symbol": symbol, "direction": direction, "strategy_tag": "BULL_CALL_SPREAD", "entry_mode": "LIMIT"}


def _trade_decision(
    symbol: str = "SPY",
    direction: str = "LONG",
    strategy_tag: str = "BULL_CALL_SPREAD",
    entry_mode: str = "DIRECT",
    decision_status: str = "ALLOW_TRADE",
    block_reason: str | None = None,
    trace_stage: str = "CHAIN_VALIDATION",
    trace_source: str = "chain_validation",
    trace_reason: str = "passed",
) -> dict:
    return {
        "symbol":         symbol,
        "direction":      direction,
        "strategy_tag":   strategy_tag,
        "entry_mode":     entry_mode,
        "decision_status": decision_status,
        "block_reason":   block_reason,
        "decision_trace": {"stage": trace_stage, "source": trace_source, "reason": trace_reason},
    }
