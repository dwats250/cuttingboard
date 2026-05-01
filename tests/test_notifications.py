from datetime import datetime, timezone

from cuttingboard.notifications import (
    NOTIFY_POST_ORB,
    NOTIFY_POWER_HOUR,
    format_failure_notification,
    format_hourly_notification,
    format_intraday_alert,
    format_notification,
    format_run_alert,
)
from cuttingboard.qualification import QualificationResult, QualificationSummary
from cuttingboard.regime import (
    RegimeState,
    CONTROLLED_LONG,
    RISK_ON,
    STAY_FLAT,
)
from cuttingboard.validation import ValidationSummary


def _regime(
    *,
    regime=RISK_ON,
    posture=CONTROLLED_LONG,
    confidence=0.62,
    net_score=5,
    vix_level=17.8,
    vix_pct_change=-0.006,
) -> RegimeState:
    return RegimeState(
        regime=regime,
        posture=posture,
        confidence=confidence,
        net_score=net_score,
        risk_on_votes=5,
        risk_off_votes=0,
        neutral_votes=3,
        total_votes=8,
        vote_breakdown={},
        vix_level=vix_level,
        vix_pct_change=vix_pct_change,
        computed_at_utc=datetime(2026, 4, 15, 14, 30, tzinfo=timezone.utc),
    )


def _qualification_summary(
    qualified_symbols: list[str],
    watch_symbols: list[str],
) -> QualificationSummary:
    qualified = [
        QualificationResult(
            symbol=symbol,
            qualified=True,
            watchlist=False,
            direction="LONG",
            gates_passed=[],
            gates_failed=[],
            hard_failure=None,
            watchlist_reason=None,
            max_contracts=1,
            dollar_risk=150.0,
        )
        for symbol in qualified_symbols
    ]
    watchlist = [
        QualificationResult(
            symbol=symbol,
            qualified=False,
            watchlist=True,
            direction="LONG",
            gates_passed=[],
            gates_failed=[],
            hard_failure=None,
            watchlist_reason="developing",
            max_contracts=None,
            dollar_risk=None,
        )
        for symbol in watch_symbols
    ]
    return QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=qualified,
        watchlist=watchlist,
        excluded={},
        symbols_evaluated=10,
        symbols_qualified=len(qualified),
        symbols_watchlist=len(watchlist),
        symbols_excluded=0,
    )


def _validation_summary() -> ValidationSummary:
    return ValidationSummary(
        system_halted=False,
        halt_reason=None,
        failed_halt_symbols=[],
        results={},
        valid_quotes={},
        invalid_symbols={},
        symbols_attempted=0,
        symbols_validated=0,
        symbols_failed=0,
    )


def test_notification_matches_structured_prd_shape():
    title, body = format_notification(
        NOTIFY_POST_ORB,
        "2026-04-15",
        _regime(),
        _validation_summary(),
        _qualification_summary(["BTC-USD", "IWM", "AMZN"], ["NVDA", "MU"]),
        {},
    )

    assert title == "BTC-USD LONG READY"
    assert body == (
        "7:30 AM\n"
        "\n"
        "Long setup ready\n"
        "Long bias\n"
        "Defined risk\n"
        "\n"
        "Trigger\n"
        "BTC-USD"
    )
    assert "CUTTINGBOARD" not in body
    assert all(ord(ch) < 128 for ch in body)


def test_notification_uses_watch_only_summary_when_no_focus():
    regime = _regime(confidence=0.55, net_score=3, vix_level=17.2, vix_pct_change=-0.004)
    _, body = format_notification(
        NOTIFY_POWER_HOUR,
        "2026-04-15",
        regime,
        _validation_summary(),
        _qualification_summary([], ["NVDA"]),
        {},
    )

    assert body.startswith("7:30 AM\n\nDeveloping")
    assert "\nWatch\nNVDA" in body
    assert "Long bias" in body
    assert "Trend intact" in body


def test_run_alert_formats_trade_only_from_qualified_trade():
    title, body = format_run_alert(
        outcome="TRADE",
        run_at_utc=datetime(2026, 4, 15, 14, 30, tzinfo=timezone.utc),
        regime=_regime(),
        validation_summary=_validation_summary(),
        qualification_summary=_qualification_summary(["SPY"], ["NVDA"]),
        watch_summary=None,
    )

    assert title == "SPY LONG READY"
    assert body == (
        "7:30 AM\n"
        "\n"
        "Long setup ready\n"
        "Long bias\n"
        "Defined risk\n"
        "\n"
        "Trigger\n"
        "SPY"
    )


def test_run_alert_stay_flat_no_trade_never_enters_trade_only_formatter():
    regime = _regime(posture=STAY_FLAT, confidence=0.12, net_score=1, vix_level=18.2, vix_pct_change=0.003)

    title, body = format_run_alert(
        outcome="NO_TRADE",
        run_at_utc=datetime(2026, 4, 15, 14, 30, tzinfo=timezone.utc),
        regime=regime,
        validation_summary=_validation_summary(),
        qualification_summary=_qualification_summary([], ["NVDA"]),
        watch_summary=None,
    )

    assert title == "NO TRADE"
    assert body == (
        "7:30 AM\n"
        "\n"
        "Risk-on tape - stay flat\n"
        "VIX 18.2 (+0.3%)\n"
        "Leaning long"
    )
    assert "Watch\nNVDA" not in body


def test_failure_notification_body_has_no_repeated_branding():
    title, body = format_failure_notification(NOTIFY_POST_ORB, "2026-04-15", "timeout")

    assert title == "POST-ORB ERROR"
    assert "CUTTINGBOARD" not in body
    assert "timestamp:" in body
    assert body.endswith("\n\nFailure\ntimeout")
    assert (title + body).isascii()


def test_intraday_notification_uses_shared_compact_style():
    title, body = format_intraday_alert(
        alert_type="REGIME_SHIFT",
        asof_utc=datetime(2026, 4, 15, 17, 12, tzinfo=timezone.utc),
        regime=_regime(),
    )

    assert title == "REGIME SHIFT"
    assert body.startswith("10:12 AM\n\n")
    assert "CUTTINGBOARD" not in title
    assert "CUTTINGBOARD" not in body
    assert "REGIME SHIFT ->" not in body
    assert "New regime:" not in body
    assert "Risk improving" in body


def test_run_alert_appends_meaningful_lifecycle_transitions_only():
    market_map = {
        "symbols": {
            "nvda": {
                "grade": "A+",
                "direction": "long",
                "setup_state": "breakout confirmed",
                "reason_for_grade": "ignored because setup_state wins",
                "lifecycle": {
                    "previous_grade": "B",
                    "grade_transition": "UPGRADED",
                },
            },
            "meta": {
                "grade": "A",
                "direction": "LONG",
                "reason_for_grade": "fresh high-grade setup",
                "lifecycle": {
                    "previous_grade": None,
                    "grade_transition": "NEW",
                },
            },
            "gdx": {
                "grade": "C",
                "direction": "LONG",
                "lifecycle": {
                    "previous_grade": None,
                    "grade_transition": "NEW",
                },
            },
            "msft": {
                "grade": "A",
                "direction": "LONG",
                "lifecycle": {
                    "previous_grade": "A",
                    "grade_transition": "UNCHANGED",
                },
            },
        },
        "removed_symbols": [
            {"symbol": "amd", "previous_grade": "B", "grade_transition": "REMOVED"},
            {"symbol": "xle", "previous_grade": "C", "grade_transition": "REMOVED"},
        ],
    }

    title, body = format_run_alert(
        outcome="NO_TRADE",
        run_at_utc=datetime(2026, 4, 15, 14, 42, tzinfo=timezone.utc),
        regime=_regime(),
        validation_summary=_validation_summary(),
        qualification_summary=_qualification_summary([], []),
        watch_summary=None,
        market_map=market_map,
    )

    assert title == "NO TRADE"
    assert "10:42 NVDA LONG - UPGRADED TO A+" in body
    assert "breakout confirmed" in body
    assert "10:42 META LONG - NEW (A)" in body
    assert "fresh high-grade setup" in body
    assert "10:42 AMD - REMOVED (prev: B)" in body
    assert "GDX" not in body
    assert "MSFT" not in body
    assert "XLE" not in body
    assert body.isascii()


def test_lifecycle_notifications_handle_downgrades_reasons_and_malformed_entries():
    market_map = {
        "symbols": {
            "tsla": {
                "grade": "B",
                "direction": "short",
                "trade_framing": {"downgrade": "lost momentum"},
                "setup_state": "ignored because downgrade wins",
                "lifecycle": {
                    "previous_grade": "A+",
                    "grade_transition": "DOWNGRADED",
                },
            },
            "iwm": {
                "grade": "F",
                "direction": "SHORT",
                "lifecycle": {
                    "previous_grade": "D",
                    "grade_transition": "DOWNGRADED",
                },
            },
            "bad": {
                "grade": "A",
                "direction": "LONG",
                "lifecycle": "not-a-dict",
            },
            "unknown": {
                "grade": "A",
                "direction": "LONG",
                "lifecycle": {
                    "previous_grade": "B",
                    "grade_transition": "UNKNOWN",
                },
            },
        },
        "removed_symbols": "not-a-list",
    }

    _, body = format_run_alert(
        outcome="NO_TRADE",
        run_at_utc=datetime(2026, 4, 15, 14, 30, tzinfo=timezone.utc),
        regime=_regime(),
        validation_summary=_validation_summary(),
        qualification_summary=_qualification_summary([], []),
        watch_summary=None,
        market_map=market_map,
    )

    assert "10:30 TSLA SHORT - DOWNGRADED TO B" in body
    assert "lost momentum" in body
    assert "ignored because downgrade wins" not in body
    assert "IWM" not in body
    assert "BAD" not in body
    assert "UNKNOWN" not in body


def test_lifecycle_notifications_deduplicate_same_transition_in_one_build():
    entry = {
        "grade": "A",
        "direction": "LONG",
        "lifecycle": {
            "previous_grade": "B",
            "grade_transition": "UPGRADED",
        },
    }
    market_map = {
        "symbols": {
            "nvda": entry,
            "NVDA": entry,
        },
        "removed_symbols": [
            {"symbol": "gdx", "previous_grade": "A", "grade_transition": "REMOVED"},
            {"symbol": "GDX", "previous_grade": "A", "grade_transition": "REMOVED"},
        ],
    }

    _, body = format_run_alert(
        outcome="NO_TRADE",
        run_at_utc=datetime(2026, 4, 15, 14, 5, tzinfo=timezone.utc),
        regime=_regime(),
        validation_summary=_validation_summary(),
        qualification_summary=_qualification_summary([], []),
        watch_summary=None,
        market_map=market_map,
    )

    assert body.count("10:05 NVDA LONG - UPGRADED TO A") == 1
    assert body.count("10:05 GDX - REMOVED (prev: A)") == 1


def test_lifecycle_alerts_reuse_hourly_timestamp_convention():
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 4, 15, 15, 20, tzinfo=timezone.utc),
        regime=_regime(posture=STAY_FLAT),
        validation_summary=_validation_summary(),
        qualification_summary=_qualification_summary([], []),
        market_map={
            "symbols": {
                "meta": {
                    "grade": "A",
                    "direction": "LONG",
                    "lifecycle": {
                        "previous_grade": None,
                        "grade_transition": "NEW",
                    },
                }
            }
        },
    )

    assert title == "STAY FLAT 11:20"
    assert "11:20 META LONG - NEW (A)" in body
    assert "15:20" not in body


def test_hourly_watchlist_title_and_reason_are_explicit():
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 4, 15, 14, 30, tzinfo=timezone.utc),
        regime=_regime(),
        validation_summary=_validation_summary(),
        qualification_summary=_qualification_summary([], ["AAPL"]),
    )

    assert title == "WATCHLIST 10:30"
    assert "WATCHLIST" in body
    assert "- AAPL LONG: developing" in body
