from dataclasses import FrozenInstanceError

import pytest

from cuttingboard.output import SystemReport, format_system_report, generate_report
from cuttingboard.policy.models import OptionsExpression, TradeCandidate, TradeDecision


def _candidate(
    ticker: str,
    *,
    direction: str = "long",
    structure: str = "breakout",
    entry: float = 100.0,
    stop: float = 98.0,
    target: float = 106.0,
    atr14: float = 2.0,
) -> TradeCandidate:
    return TradeCandidate(
        ticker=ticker,
        direction=direction,
        entry_price=entry,
        stop_price=stop,
        target_price=target,
        ema9=99.0,
        ema21=97.0,
        ema50=95.0,
        atr14=atr14,
        structure=structure,
    )


def _approved(
    ticker: str,
    *,
    structure: str = "breakout",
    entry: float = 100.0,
    stop: float = 98.0,
    target: float = 106.0,
    spread_type: str = "call_debit",
) -> TradeDecision:
    candidate = _candidate(
        ticker,
        structure=structure,
        entry=entry,
        stop=stop,
        target=target,
    )
    return TradeDecision(
        candidate=candidate,
        posture="LONG_BIAS",
        decision="APPROVED",
        reason=None,
        options_plan=OptionsExpression(
            spread_type=spread_type,
            duration="weekly",
            notes=None,
        ),
    )


def _rejected(
    ticker: str,
    *,
    reason: str = "RR_INVALID",
    structure: str = "pullback",
) -> TradeDecision:
    return TradeDecision(
        candidate=_candidate(ticker, structure=structure),
        posture="LONG_BIAS",
        decision="REJECTED",
        reason=reason,
        options_plan=None,
    )


def test_all_trades_appear_with_no_silent_drop():
    report = generate_report(
        [
            _approved("MSFT", target=107.0),
            _approved("AAPL", target=106.0),
            _rejected("TSLA", reason="MACRO_CONFLICT"),
            _rejected("NVDA", reason="RR_INVALID"),
        ],
        posture="LONG_BIAS",
        market_quality="CLEAN",
    )

    seen = len(report.top_trades) + len(report.watchlist) + len(report.rejected)
    assert seen == 4
    assert report.summary.total_candidates == 4
    assert report.summary.approved_count == 2
    assert report.summary.rejected_count == 2


def test_approved_trades_are_ranked_deterministically():
    report = generate_report(
        [
            _approved("MSFT", structure="pullback", target=106.0),   # rr 3.0
            _approved("AAPL", structure="breakout", target=105.0),   # rr 2.5
            _approved("AMZN", structure="reversal", target=107.0),   # rr 3.5
            _approved("GOOG", structure="breakout", target=106.0),   # rr 3.0
        ],
        posture="LONG_BIAS",
        market_quality="CLEAN",
    )

    assert [trade.ticker for trade in report.top_trades] == ["AMZN", "GOOG", "MSFT"]
    assert [trade.ticker for trade in report.watchlist] == ["AAPL"]


def test_top_trades_are_capped_at_three():
    report = generate_report(
        [
            _approved("AAPL", target=108.0),
            _approved("MSFT", target=108.0),
            _approved("NVDA", target=108.0),
            _approved("GOOG", target=108.0),
        ],
        posture="LONG_BIAS",
        market_quality="CLEAN",
    )

    assert len(report.top_trades) == 3
    assert len(report.watchlist) == 1


def test_watchlist_contains_remaining_approved_sorted_by_rr_then_ticker():
    report = generate_report(
        [
            _approved("AAPL", target=108.0),
            _approved("MSFT", target=108.0),
            _approved("NVDA", target=108.0),
            _approved("GOOG", target=105.0),  # rr 2.5 -> watchlist after top 3
            _approved("AMD", target=104.0),   # rr 2.0 -> watchlist
        ],
        posture="LONG_BIAS",
        market_quality="MIXED",
    )

    assert [trade.ticker for trade in report.watchlist] == ["GOOG", "AMD"]


def test_rejected_trades_are_logged_with_reason():
    report = generate_report(
        [
            _approved("AAPL"),
            _rejected("TSLA", reason="MACRO_CONFLICT"),
            _rejected("NVDA", reason="NO_STRUCTURE"),
        ],
        posture="LONG_BIAS",
        market_quality="CLEAN",
    )

    assert [(trade.ticker, trade.reason) for trade in report.rejected] == [
        ("TSLA", "MACRO_CONFLICT"),
        ("NVDA", "NO_STRUCTURE"),
    ]


def test_summary_counts_and_breakdown_are_accurate():
    report = generate_report(
        [
            _approved("AAPL"),
            _rejected("TSLA", reason="RR_INVALID"),
            _rejected("NVDA", reason="RR_INVALID"),
            _rejected("META", reason="MACRO_CONFLICT"),
        ],
        posture="LONG_BIAS",
        market_quality="CLEAN",
    )

    assert report.summary.total_candidates == 4
    assert report.summary.approved_count == 1
    assert report.summary.rejected_count == 3
    assert report.summary.rejection_breakdown == {
        "MACRO_CONFLICT": 1,
        "RR_INVALID": 2,
    }


def test_halt_condition_returns_empty_trade_lists_and_full_rejected_log():
    report = generate_report(
        [
            _approved("AAPL"),
            _rejected("TSLA", reason="NO_STRUCTURE"),
        ],
        posture="NEUTRAL",
        market_quality="CHAOTIC",
    )

    assert report.top_trades == []
    assert report.watchlist == []
    assert [trade.ticker for trade in report.rejected] == ["AAPL", "TSLA"]
    assert report.summary.approved_count == 0
    assert report.summary.rejected_count == 2
    assert report.summary.rejection_breakdown == {
        "MARKET_CHAOTIC": 1,
        "NO_STRUCTURE": 1,
    }


def test_all_rejected_returns_valid_report():
    report = generate_report(
        [
            _rejected("AAPL", reason="MACRO_CONFLICT"),
            _rejected("TSLA", reason="RR_INVALID"),
        ],
        posture="LONG_BIAS",
        market_quality="MIXED",
    )

    assert report.top_trades == []
    assert report.watchlist == []
    assert len(report.rejected) == 2


def test_deterministic_sorting_uses_ticker_as_final_tiebreak():
    report = generate_report(
        [
            _approved("MSFT", target=106.0),
            _approved("AAPL", target=106.0),
        ],
        posture="LONG_BIAS",
        market_quality="CLEAN",
    )

    assert [trade.ticker for trade in report.top_trades] == ["AAPL", "MSFT"]


def test_empty_input_raises_value_error():
    with pytest.raises(ValueError):
        generate_report([], posture="LONG_BIAS", market_quality="CLEAN")


def test_approved_trade_missing_options_plan_raises():
    trade = TradeDecision(
        candidate=_candidate("AAPL"),
        posture="LONG_BIAS",
        decision="APPROVED",
        reason=None,
        options_plan=None,
    )

    with pytest.raises(ValueError):
        generate_report([trade], posture="LONG_BIAS", market_quality="CLEAN")


def test_invalid_reason_code_raises():
    with pytest.raises(ValueError):
        generate_report(
            [_rejected("AAPL", reason="NOT_A_REASON")],
            posture="LONG_BIAS",
            market_quality="CLEAN",
        )


def test_cli_formatter_matches_expected_sections():
    report = generate_report(
        [
            _approved("AAPL", target=106.0),
            _rejected("TSLA", reason="RR_INVALID"),
        ],
        posture="LONG_BIAS",
        market_quality="CLEAN",
    )

    rendered = format_system_report(report)
    assert rendered.startswith("=== CUTTINGBOARD REPORT ===")
    assert "TOP TRADES" in rendered
    assert "1. AAPL | breakout | RR 3.00 | call_debit (weekly)" in rendered
    assert "WATCHLIST" in rendered
    assert "REJECTED (SUMMARY)" in rendered
    assert "RR_INVALID: 1" in rendered


def test_system_report_is_frozen():
    report = generate_report([_approved("AAPL")], posture="LONG_BIAS", market_quality="CLEAN")
    assert isinstance(report, SystemReport)
    with pytest.raises(FrozenInstanceError):
        report.posture = "SHORT_BIAS"
