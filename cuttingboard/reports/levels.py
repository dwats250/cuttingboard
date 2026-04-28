from __future__ import annotations


def _to_float(val: object) -> float | None:
    if val is None:
        return None
    try:
        return float(val)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def derive_key_levels(contract: dict, run_history: list[dict]) -> dict:
    prior_high: float | None = None
    prior_low: float | None = None
    prior_close: float | None = None
    current_price: float | None = None

    valid_runs = [r for r in run_history if r.get("status") != "ERROR"]
    if valid_runs:
        sorted_runs = sorted(valid_runs, key=lambda r: r.get("run_at_utc") or "")
        most_recent = sorted_runs[-1]
        prior_high = _to_float(most_recent.get("prior_high"))
        prior_low = _to_float(most_recent.get("prior_low"))
        prior_close = _to_float(most_recent.get("prior_close"))

    artifacts = contract.get("artifacts") or {}
    raw_price = artifacts.get("current_price")
    if raw_price is not None:
        current_price = _to_float(raw_price)

    gap_direction: str | None = None
    if current_price is not None and prior_close is not None:
        if current_price > prior_close * 1.001:
            gap_direction = "UP"
        elif current_price < prior_close * 0.999:
            gap_direction = "DOWN"
        else:
            gap_direction = "FLAT"

    range_mid: float | None = None
    if prior_high is not None and prior_low is not None:
        range_mid = (prior_high + prior_low) / 2

    return {
        "prior_high": prior_high,
        "prior_low": prior_low,
        "prior_close": prior_close,
        "current_price": current_price,
        "gap_direction": gap_direction,
        "range_mid": range_mid,
    }
