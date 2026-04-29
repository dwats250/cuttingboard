from __future__ import annotations


def _is_run_record(record: dict) -> bool:
    return "outcome" in record and "run_at_utc" in record


def _tradable_from_record(record: dict) -> bool:
    posture = record.get("posture") or ""
    return bool(posture) and posture != "STAY_FLAT"


def _direction_from_posture(posture: str | None) -> str:
    if posture in ("AGGRESSIVE_LONG", "CONTROLLED_LONG"):
        return "LONG"
    if posture in ("DEFENSIVE_SHORT",):
        return "SHORT"
    return "NEUTRAL"


def _level_interaction(preferred_direction: str, levels: dict) -> str:
    current_price = levels.get("current_price")
    prior_high = levels.get("prior_high")
    prior_low = levels.get("prior_low")

    if current_price is None:
        return "PARTIAL"

    if preferred_direction == "LONG":
        if prior_high is not None and current_price > prior_high:
            return "MATCH"
        return "PARTIAL"

    if preferred_direction == "SHORT":
        if prior_low is not None and current_price < prior_low:
            return "MATCH"
        return "PARTIAL"

    return "PARTIAL"


def _classify_evr_with_levels(
    runs: list[dict],
    market_regime: str | None,
    tradable: bool,
    levels: dict,
) -> tuple[str, str]:
    if not runs:
        return "NO_EXPECTATION", "No prior run available in history"

    prior = runs[0]
    prior_posture = prior.get("posture")
    prior_direction = _direction_from_posture(prior_posture)

    realized_direction = _direction_from_posture(
        "AGGRESSIVE_LONG" if (market_regime == "RISK_ON" and tradable) else
        "DEFENSIVE_SHORT" if (market_regime == "RISK_OFF" and tradable) else
        "STAY_FLAT"
    )

    if prior_direction == "NEUTRAL" and realized_direction == "NEUTRAL":
        result = _level_interaction(prior_direction, levels)
        notes = (
            f"Both runs NEUTRAL posture; level interaction: {result.lower()}"
        )
        return result, notes

    if prior_direction != realized_direction:
        return "MISS", (
            f"Expected {prior_direction} (prior posture {prior_posture}); "
            f"realized {realized_direction} (regime {market_regime})"
        )

    result = _level_interaction(prior_direction, levels)
    notes = (
        f"Direction aligned ({prior_direction}); "
        f"level interaction: {result.lower()}"
    )
    return result, notes


def _classify_evr_legacy(
    runs: list[dict],
    market_regime: str | None,
    tradable: bool,
) -> tuple[str, str]:
    if not runs:
        return "NO_EXPECTATION", "No prior run available in history"

    prior = runs[0]
    prior_regime: str | None = prior.get("regime")
    prior_tradable = _tradable_from_record(prior)

    if prior_regime == market_regime and prior_tradable == tradable:
        return "MATCH", f"Regime {market_regime} and tradable={tradable} consistent with prior run"
    if prior_regime == market_regime:
        return "PARTIAL", f"Regime {market_regime} held; tradable changed from {prior_tradable} to {tradable}"
    return "MISS", f"Regime shifted from {prior_regime} to {market_regime}"


def build_postmarket_report(
    contract: dict,
    run_history: list[dict],
    levels: dict | None = None,
) -> dict:
    ss = contract.get("system_state") or {}
    mc = contract.get("market_context") or {}
    audit_summary = contract.get("audit_summary") or {}
    rejections = contract.get("rejections") or []
    correlation = contract.get("correlation")

    market_regime: str | None = ss.get("market_regime")
    tradable: bool = bool(ss.get("tradable", False))
    stay_flat_reason: str | None = ss.get("stay_flat_reason")
    status: str = contract.get("status") or ""

    runs = [r for r in run_history if _is_run_record(r)]

    if levels is not None:
        evr_result, evr_notes = _classify_evr_with_levels(runs, market_regime, tradable, levels)
    else:
        evr_result, evr_notes = _classify_evr_legacy(runs, market_regime, tradable)

    regime_count = sum(1 for r in rejections if r.get("stage") == "REGIME")
    qualification_count = sum(1 for r in rejections if r.get("stage") == "QUALIFICATION")
    watchlist_count = sum(1 for r in rejections if r.get("stage") == "WATCHLIST")

    qualified_count: int = int(audit_summary.get("qualified_count") or 0)

    if not runs:
        persisted = False
        flipped = False
    else:
        prior_regimes = [r.get("regime") for r in runs]
        persisted = all(r == market_regime for r in prior_regimes)
        flipped = any(r != market_regime for r in prior_regimes)

    observations: list[str] = []

    continuation_enabled = mc.get("continuation_enabled")
    if continuation_enabled is True:
        observations.append("Continuation enabled — expansion regime active")
    elif continuation_enabled is False:
        observations.append("Continuation disabled — expansion regime not active")

    cont_rejected = audit_summary.get("continuation_rejected_count")
    if cont_rejected is not None and int(cont_rejected) > 0:
        observations.append(f"{int(cont_rejected)} candidate(s) rejected at continuation audit")

    if qualified_count == 0:
        observations.append("No trade candidates qualified this run")
    else:
        observations.append(f"{qualified_count} candidate(s) qualified for execution")

    if correlation:
        corr_state = correlation.get("state")
        corr_mod = correlation.get("risk_modifier")
        if corr_state and corr_mod is not None:
            observations.append(
                f"Correlation state: {corr_state} — risk modifier applied: {corr_mod}"
            )

    if not tradable and stay_flat_reason:
        observations.append(f"System stay-flat: {stay_flat_reason}")

    return {
        "system_outcome": {
            "market_regime": market_regime,
            "tradable": tradable,
            "stay_flat_reason": stay_flat_reason,
            "status": status,
        },
        "expectation_vs_reality": {
            "result": evr_result,
            "notes": evr_notes,
        },
        "trade_summary": {
            "qualified_count": qualified_count,
            "watchlist_count": watchlist_count,
            "rejected_count": qualification_count,
        },
        "rejection_breakdown": {
            "regime": regime_count,
            "qualification": qualification_count,
            "watchlist": watchlist_count,
        },
        "regime_validation": {
            "persisted": persisted,
            "flipped": flipped,
        },
        "deterministic_observations": observations,
    }
