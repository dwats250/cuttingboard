"""
PRD-013 — Flow Alignment Soft Gate.

Downgrades an already-qualified PASS candidate to WATCHLIST when dominant
speculative options flow opposes the candidate direction.

Entry points:
  apply_flow_gate(result, flow_snapshot)
  load_flow_snapshot(path) -> FlowSnapshot
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from typing import TYPE_CHECKING

from cuttingboard import config
from cuttingboard.universe import is_tradable_symbol

if TYPE_CHECKING:
    from cuttingboard.qualification import QualificationResult

FlowAlignment = str  # "SUPPORTS" | "OPPOSES" | "NEUTRAL" | "NO_DATA"


@dataclass(frozen=True)
class FlowPrint:
    symbol: str
    strike: float
    option_type: str        # "CALL" | "PUT"
    premium: float
    side: str               # "ASK" | "BID" | "MID"
    is_sweep: bool
    underlying_price: float


@dataclass(frozen=True)
class FlowSnapshot:
    """Authoritative flow data for one pipeline run.

    symbols maps each ticker to the list of qualifying FlowPrints.
    Format mirrors the JSON storage schema; see docs/CONSUMERS.md.

    NOTE: PRD-015 specifies FlowSymbolData with aggregated fields
    (total_premium, speculative_premium, call_premium, put_premium).
    apply_flow_gate() requires per-print detail (strike, side, option_type)
    to classify ITM/OTM and compute speculative vs hedge flow; aggregates
    would destroy that information. symbols stores list[FlowPrint] to
    maintain gate compatibility per "No logic changes to PRD-013 gate."
    """
    timestamp: datetime
    symbols: dict[str, list[FlowPrint]]


def apply_flow_gate(
    result: QualificationResult,
    flow_snapshot: dict[str, list[FlowPrint]],
) -> tuple[QualificationResult, FlowAlignment]:
    """Apply the flow alignment soft gate to a single QualificationResult.

    Only acts on qualified (PASS) results. Returns the (possibly downgraded)
    result and the computed FlowAlignment label.
    """
    if not result.qualified:
        return result, "NO_DATA"

    symbol = result.symbol

    # Step 1 — symbol print set
    if not is_tradable_symbol(symbol):
        return result, "NO_DATA"

    prints = [
        p for p in flow_snapshot.get(symbol, [])
        if p.premium >= config.FLOW_MIN_PREMIUM
    ]
    if not prints:
        return result, "NO_DATA"

    # Step 2 — classify each print's strike location
    # Step 3 — aggregate flow type
    total_premium = sum(p.premium for p in prints)
    itm_premium = 0.0
    otm_ask_premium = 0.0

    for p in prints:
        loc = _classify_strike(p.strike, p.underlying_price, p.option_type)
        if loc == "ITM":
            itm_premium += p.premium
        elif loc == "OTM" and p.side == "ASK":
            otm_ask_premium += p.premium

    if itm_premium / total_premium > 0.50:
        aggregate_flow_type = "HEDGE"
    elif otm_ask_premium / total_premium >= config.FLOW_MIN_SPEC_SHARE:
        aggregate_flow_type = "SPECULATIVE"
    else:
        aggregate_flow_type = "MIXED"

    # Step 4 — non-speculative exit
    if aggregate_flow_type != "SPECULATIVE":
        return result, "NEUTRAL"

    # Step 5 — speculative direction
    bullish_spec = sum(
        p.premium for p in prints
        if p.option_type == "CALL"
        and p.side == "ASK"
        and _classify_strike(p.strike, p.underlying_price, p.option_type) == "OTM"
    )
    bearish_spec = sum(
        p.premium for p in prints
        if p.option_type == "PUT"
        and p.side == "ASK"
        and _classify_strike(p.strike, p.underlying_price, p.option_type) == "OTM"
    )

    threshold = config.FLOW_RATIO_THRESHOLD
    if bullish_spec >= bearish_spec * threshold:
        dominant = "BULLISH"
    elif bearish_spec >= bullish_spec * threshold:
        dominant = "BEARISH"
    else:
        dominant = "NEUTRAL"

    # Step 6 — alignment
    if dominant == "NEUTRAL":
        return result, "NEUTRAL"

    opposes = (
        (result.direction == "LONG" and dominant == "BEARISH")
        or (result.direction == "SHORT" and dominant == "BULLISH")
    )

    if opposes:
        downgraded = replace(
            result,
            qualified=False,
            watchlist=True,
            watchlist_reason="FLOW_ALIGNMENT: opposing speculative flow",
            flow_alignment="OPPOSES",
        )
        return downgraded, "OPPOSES"

    return replace(result, flow_alignment="SUPPORTS"), "SUPPORTS"


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_flow_snapshot(path: str) -> FlowSnapshot:
    """Load and validate a flow snapshot from a JSON file.

    JSON schema:
        {
          "timestamp": "<ISO-8601>",
          "symbols": {
            "<TICKER>": [
              { "symbol": str, "strike": float, "option_type": "CALL"|"PUT",
                "premium": float, "side": "ASK"|"BID"|"MID",
                "is_sweep": bool, "underlying_price": float },
              ...
            ]
          }
        }

    Raises FileNotFoundError if path does not exist.
    Raises ValueError on any schema or validation failure.
    Never returns a partial or default result.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            raw = json.load(fh)
    except json.JSONDecodeError as exc:
        raise ValueError(f"load_flow_snapshot: invalid JSON at {path!r}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(
            f"load_flow_snapshot: root must be a JSON object, got {type(raw).__name__}"
        )

    ts_raw = raw.get("timestamp")
    if not ts_raw:
        raise ValueError("load_flow_snapshot: missing required field 'timestamp'")
    try:
        timestamp = datetime.fromisoformat(str(ts_raw).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"load_flow_snapshot: unparseable timestamp {ts_raw!r}"
        ) from exc

    symbols_raw = raw.get("symbols")
    if not isinstance(symbols_raw, dict):
        raise ValueError("load_flow_snapshot: 'symbols' must be a JSON object")
    if not symbols_raw:
        raise ValueError(
            "load_flow_snapshot: 'symbols' must not be empty when flow_data_path is configured"
        )

    symbols: dict[str, list[FlowPrint]] = {}
    for sym, prints_raw in symbols_raw.items():
        if not isinstance(prints_raw, list):
            raise ValueError(
                f"load_flow_snapshot: symbols[{sym!r}] must be a list of print objects"
            )
        symbols[sym] = [_parse_flow_print(sym, i, p) for i, p in enumerate(prints_raw)]

    return FlowSnapshot(timestamp=timestamp, symbols=symbols)


def _parse_flow_print(symbol: str, index: int, p: object) -> FlowPrint:
    """Parse and validate one FlowPrint from a raw dict. Raises ValueError on any issue."""
    if not isinstance(p, dict):
        raise ValueError(
            f"flow print [{symbol}][{index}]: expected a JSON object, got {type(p).__name__}"
        )
    required = {"symbol", "strike", "option_type", "premium", "side", "is_sweep", "underlying_price"}
    missing = required - set(p)
    if missing:
        raise ValueError(
            f"flow print [{symbol}][{index}]: missing required fields {sorted(missing)}"
        )

    for field in ("strike", "premium", "underlying_price"):
        val = p[field]
        if not isinstance(val, (int, float)):
            raise ValueError(
                f"flow print [{symbol}][{index}]: '{field}' must be numeric, got {type(val).__name__}"
            )
        if val < 0:
            raise ValueError(
                f"flow print [{symbol}][{index}]: '{field}' must be >= 0, got {val}"
            )

    if p["premium"] == 0:
        raise ValueError(f"flow print [{symbol}][{index}]: 'premium' must be > 0")

    if p["option_type"] not in ("CALL", "PUT"):
        raise ValueError(
            f"flow print [{symbol}][{index}]: 'option_type' must be CALL or PUT, "
            f"got {p['option_type']!r}"
        )
    if p["side"] not in ("ASK", "BID", "MID"):
        raise ValueError(
            f"flow print [{symbol}][{index}]: 'side' must be ASK/BID/MID, got {p['side']!r}"
        )
    if not isinstance(p["is_sweep"], bool):
        raise ValueError(
            f"flow print [{symbol}][{index}]: 'is_sweep' must be bool, "
            f"got {type(p['is_sweep']).__name__}"
        )

    return FlowPrint(
        symbol=str(p["symbol"]),
        strike=float(p["strike"]),
        option_type=p["option_type"],
        premium=float(p["premium"]),
        side=p["side"],
        is_sweep=p["is_sweep"],
        underlying_price=float(p["underlying_price"]),
    )


def _classify_strike(strike: float, underlying_price: float, option_type: str) -> str:
    distance = (strike - underlying_price) / underlying_price
    if option_type == "CALL":
        if distance > 0.005:
            return "OTM"
        if distance < -0.005:
            return "ITM"
        return "ATM"
    # PUT
    if distance < -0.005:
        return "OTM"
    if distance > 0.005:
        return "ITM"
    return "ATM"
