"""System report builder for the Output Standard Layer."""

from datetime import datetime, timezone

from cuttingboard.output.models import RejectedTrade, SummaryStats, SystemReport, TradeOutput
from cuttingboard.output.ranking import rank_approved_trades, sort_watchlist
from cuttingboard.policy.models import OptionsExpression, TradeCandidate, TradeDecision
from cuttingboard.policy.rules import (
    VALID_MARKET_QUALITIES,
    VALID_TRADE_STRUCTURES,
    compute_rr,
)

VALID_REASON_CODES = {
    "INVALID_INPUT",
    "MACRO_CONFLICT",
    "MARKET_CHAOTIC",
    "NEUTRAL_POSTURE",
    "NO_STRUCTURE",
    "RR_INVALID",
    "VOL_MISMATCH",
}

VALID_POSTURES = {"LONG_BIAS", "SHORT_BIAS", "NEUTRAL"}
VALID_DECISIONS = {"APPROVED", "REJECTED"}


def generate_report(
    trades: list[TradeDecision],
    posture: str,
    market_quality: str,
) -> SystemReport:
    if not trades:
        raise ValueError("trades must not be empty")

    _validate_context(posture, market_quality)
    validated_trades = [_validate_trade_decision(trade) for trade in trades]
    timestamp = _timestamp_utc()

    if posture == "NEUTRAL" and market_quality == "CHAOTIC":
        rejected = [_to_halt_rejection(trade) for trade in validated_trades]
        return SystemReport(
            timestamp=timestamp,
            posture=posture,
            market_quality=market_quality,
            top_trades=[],
            watchlist=[],
            rejected=sorted(rejected, key=lambda trade: trade.ticker),
            summary=_build_summary(
                total_candidates=len(validated_trades),
                approved_count=0,
                rejected=rejected,
            ),
        )

    approved = [_to_trade_output(trade) for trade in validated_trades if trade.decision == "APPROVED"]
    rejected = [_to_rejected_trade(trade) for trade in validated_trades if trade.decision == "REJECTED"]

    ranked = rank_approved_trades(approved, market_quality)
    top_trades = [trade for trade in ranked if trade.rr >= 2.5][:3]
    top_symbols = {trade.ticker for trade in top_trades}
    watchlist = sort_watchlist([trade for trade in ranked if trade.ticker not in top_symbols])

    return SystemReport(
        timestamp=timestamp,
        posture=posture,
        market_quality=market_quality,
        top_trades=top_trades,
        watchlist=watchlist,
        rejected=sorted(rejected, key=lambda trade: (trade.reason, trade.ticker)),
        summary=_build_summary(
            total_candidates=len(validated_trades),
            approved_count=len(approved),
            rejected=rejected,
        ),
    )


def _validate_context(posture: str, market_quality: str) -> None:
    if posture not in VALID_POSTURES:
        raise ValueError(f"invalid posture: {posture}")
    if market_quality not in VALID_MARKET_QUALITIES:
        raise ValueError(f"invalid market_quality: {market_quality}")


def _validate_trade_decision(trade: TradeDecision) -> TradeDecision:
    if not isinstance(trade, TradeDecision):
        raise ValueError("each trade must be a TradeDecision")
    _validate_candidate(trade.candidate)
    if trade.posture not in VALID_POSTURES:
        raise ValueError(f"invalid trade posture: {trade.posture}")
    if trade.decision not in VALID_DECISIONS:
        raise ValueError(f"invalid trade decision: {trade.decision}")

    if trade.decision == "APPROVED":
        if trade.options_plan is None:
            raise ValueError("approved trade missing options_plan")
        _validate_options_plan(trade.options_plan)
        if trade.reason is not None:
            raise ValueError("approved trade cannot have rejection reason")
        return trade

    if trade.reason is None:
        raise ValueError("rejected trade missing reason")
    if trade.reason not in VALID_REASON_CODES:
        raise ValueError(f"invalid reason code: {trade.reason}")
    return trade


def _validate_candidate(candidate: TradeCandidate) -> None:
    if not isinstance(candidate, TradeCandidate):
        raise ValueError("trade candidate is required")
    if candidate.structure not in VALID_TRADE_STRUCTURES:
        raise ValueError(f"invalid structure: {candidate.structure}")
    if not candidate.ticker:
        raise ValueError("candidate ticker is required")
    if candidate.direction not in {"long", "short"}:
        raise ValueError(f"invalid direction: {candidate.direction}")
    for field_name in ("entry_price", "stop_price", "target_price", "atr14"):
        if getattr(candidate, field_name) is None:
            raise ValueError(f"candidate.{field_name} is required")


def _validate_options_plan(options_plan: OptionsExpression) -> None:
    if not isinstance(options_plan, OptionsExpression):
        raise ValueError("options_plan must be an OptionsExpression")
    if not options_plan.spread_type:
        raise ValueError("options_plan.spread_type is required")
    if not options_plan.duration:
        raise ValueError("options_plan.duration is required")


def _to_trade_output(trade: TradeDecision) -> TradeOutput:
    options_plan = trade.options_plan
    if options_plan is None:
        raise ValueError("approved trade missing options_plan")
    candidate = trade.candidate
    return TradeOutput(
        ticker=candidate.ticker,
        direction=candidate.direction,
        structure=candidate.structure,
        entry=candidate.entry_price,
        stop=candidate.stop_price,
        target=candidate.target_price,
        rr=compute_rr(candidate),
        spread_type=options_plan.spread_type,
        duration=options_plan.duration,
    )


def _to_rejected_trade(trade: TradeDecision) -> RejectedTrade:
    candidate = trade.candidate
    reason = trade.reason
    if reason is None:
        raise ValueError("rejected trade missing reason")
    return RejectedTrade(
        ticker=candidate.ticker,
        reason=reason,
        direction=candidate.direction,
        structure=candidate.structure,
    )


def _to_halt_rejection(trade: TradeDecision) -> RejectedTrade:
    candidate = trade.candidate
    reason = trade.reason if trade.reason in VALID_REASON_CODES else "MARKET_CHAOTIC"
    if trade.decision == "APPROVED":
        reason = "MARKET_CHAOTIC"
    return RejectedTrade(
        ticker=candidate.ticker,
        reason=reason,
        direction=candidate.direction,
        structure=candidate.structure,
    )


def _build_summary(
    *,
    total_candidates: int,
    approved_count: int,
    rejected: list[RejectedTrade],
) -> SummaryStats:
    breakdown: dict[str, int] = {}
    for reason in sorted(trade.reason for trade in rejected):
        breakdown[reason] = breakdown.get(reason, 0) + 1
    return SummaryStats(
        total_candidates=total_candidates,
        approved_count=approved_count,
        rejected_count=len(rejected),
        rejection_breakdown=breakdown,
    )


def _timestamp_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
