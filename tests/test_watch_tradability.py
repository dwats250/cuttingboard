from __future__ import annotations

from datetime import datetime, timezone

from cuttingboard.notifications import NOTIFY_PREMARKET, format_notification
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.output import run_pipeline
from cuttingboard.qualification import QualificationSummary
from cuttingboard.regime import AGGRESSIVE_LONG, RISK_ON, RegimeState
from cuttingboard.universe import is_tradable_symbol
from cuttingboard.validation import ValidationSummary
from cuttingboard.watch import WatchItem, WatchSummary


def _quote(symbol: str) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=100.0,
        pct_change_decimal=0.01,
        volume=1_000_000.0,
        fetched_at_utc=datetime.now(timezone.utc),
        source="test",
        units="usd_price",
        age_seconds=0.0,
    )


def _validation_summary(symbols: list[str]) -> ValidationSummary:
    valid_quotes = {symbol: _quote(symbol) for symbol in symbols}
    return ValidationSummary(
        system_halted=False,
        halt_reason=None,
        failed_halt_symbols=[],
        results={},
        valid_quotes=valid_quotes,
        invalid_symbols={},
        symbols_attempted=len(symbols),
        symbols_validated=len(symbols),
        symbols_failed=0,
    )


def _regime() -> RegimeState:
    return RegimeState(
        regime=RISK_ON,
        posture=AGGRESSIVE_LONG,
        confidence=0.8,
        net_score=6,
        risk_on_votes=6,
        risk_off_votes=0,
        neutral_votes=2,
        total_votes=8,
        vote_breakdown={},
        vix_level=18.0,
        vix_pct_change=0.01,
        computed_at_utc=datetime(2026, 4, 21, 13, 45, tzinfo=timezone.utc),
    )


def _empty_qualification() -> QualificationSummary:
    return QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[],
        watchlist=[],
        excluded={},
        symbols_evaluated=0,
        symbols_qualified=0,
        symbols_watchlist=0,
        symbols_excluded=0,
    )


def _watch_summary(symbols: list[str]) -> WatchSummary:
    return WatchSummary(
        session="MORNING",
        threshold=3,
        watchlist=[
            WatchItem(
                symbol=symbol,
                score=80.0,
                structure="TREND",
                structure_note="TREND near VWAP with building compression",
                missing_conditions=["tighten range"],
                total_signals=4,
                level="VWAP",
                bias="LONG",
            )
            for symbol in symbols
        ],
        ignored_symbols=[],
        execution_posture="A+ Only",
    )


def _run_pipeline_case(monkeypatch, symbols: list[str]) -> dict[str, object]:
    captured: dict[str, object] = {}
    validation_summary = _validation_summary(symbols)
    regime = _regime()
    qualification_summary = _empty_qualification()

    monkeypatch.setattr("cuttingboard.output.fetch_all", lambda: {})
    monkeypatch.setattr("cuttingboard.output.normalize_all", lambda raw: raw)
    monkeypatch.setattr("cuttingboard.output.validate_quotes", lambda normed: validation_summary)

    def _fake_compute_regime(valid_quotes):
        captured["regime_symbols"] = list(valid_quotes)
        return regime

    monkeypatch.setattr("cuttingboard.output.compute_regime", _fake_compute_regime)
    monkeypatch.setattr(
        "cuttingboard.output.compute_all_derived",
        lambda valid_quotes: {symbol: object() for symbol in valid_quotes},
    )
    monkeypatch.setattr(
        "cuttingboard.output.classify_all_structure",
        lambda valid_quotes, dm, vix_level: {symbol: object() for symbol in valid_quotes},
    )

    def _fake_compute_all_intraday_metrics(filtered_symbols):
        captured["intraday_symbols"] = list(filtered_symbols)
        return ({symbol: object() for symbol in filtered_symbols}, [])

    monkeypatch.setattr("cuttingboard.output.compute_all_intraday_metrics", _fake_compute_all_intraday_metrics)

    def _fake_classify_watchlist(structure, dm, intraday_metrics, regime, **kwargs):
        del structure, dm, regime, kwargs
        watch_summary = _watch_summary(list(intraday_metrics))
        captured["watch_summary"] = watch_summary
        return watch_summary

    monkeypatch.setattr("cuttingboard.output.classify_watchlist", _fake_classify_watchlist)
    monkeypatch.setattr("cuttingboard.output.generate_candidates", lambda *args, **kwargs: {})
    monkeypatch.setattr("cuttingboard.output.qualify_all", lambda *args, **kwargs: qualification_summary)
    monkeypatch.setattr("cuttingboard.output.render_report", lambda **kwargs: "report")
    monkeypatch.setattr("cuttingboard.output.write_terminal", lambda report: None)
    monkeypatch.setattr("cuttingboard.output.write_markdown", lambda report, date_str: "/tmp/report.md")

    def _fake_send_notification(title, body):
        captured["alert_title"] = title
        captured["alert_body"] = body
        return False

    monkeypatch.setattr("cuttingboard.output.send_notification", _fake_send_notification)
    monkeypatch.setattr("cuttingboard.output.write_audit_record", lambda **kwargs: None)

    exit_code = run_pipeline()
    captured["exit_code"] = exit_code
    captured["validation_summary"] = validation_summary
    captured["regime"] = regime
    captured["qualification_summary"] = qualification_summary
    return captured


def test_is_tradable_symbol_rules():
    assert is_tradable_symbol("^VIX") is False
    assert is_tradable_symbol("BTC-USD") is False
    assert is_tradable_symbol("SPY") is True


def test_watch_tradability_mixed_input(monkeypatch):
    captured = _run_pipeline_case(monkeypatch, ["^VIX", "^TNX", "BTC-USD", "SPY", "NVDA"])

    assert captured["exit_code"] == 0
    assert captured["regime_symbols"] == ["^VIX", "^TNX", "BTC-USD", "SPY", "NVDA"]
    assert captured["intraday_symbols"] == ["SPY", "NVDA"]

    watch_summary = captured["watch_summary"]
    assert isinstance(watch_summary, WatchSummary)
    assert [item.symbol for item in watch_summary.watchlist] == ["SPY", "NVDA"]

    title, body = format_notification(
        NOTIFY_PREMARKET,
        "2026-04-21",
        captured["regime"],
        captured["validation_summary"],
        captured["qualification_summary"],
        {},
        watch_summary=watch_summary,
    )

    assert title == "WATCHLIST UPDATE"
    assert "Top Focus" in body
    assert "SPY - " in body
    assert "NVDA - " in body
    assert "^VIX" not in body
    assert "^TNX" not in body
    assert "BTC-USD" not in body


def test_watch_tradability_context_only_emits_no_trade(monkeypatch):
    captured = _run_pipeline_case(monkeypatch, ["^VIX", "^TNX"])

    assert captured["exit_code"] == 0
    assert captured["regime_symbols"] == ["^VIX", "^TNX"]
    assert captured["intraday_symbols"] == []
    assert captured["alert_title"] == "NO TRADE"

    watch_summary = captured["watch_summary"]
    assert isinstance(watch_summary, WatchSummary)
    assert watch_summary.watchlist == []

    title, body = format_notification(
        NOTIFY_PREMARKET,
        "2026-04-21",
        captured["regime"],
        captured["validation_summary"],
        captured["qualification_summary"],
        {},
        watch_summary=watch_summary,
    )

    assert title == "NO TRADE"
    assert "Top Focus" not in body


def test_watch_tradability_tradable_only(monkeypatch):
    captured = _run_pipeline_case(monkeypatch, ["SPY", "QQQ", "NVDA"])

    assert captured["exit_code"] == 0
    assert captured["regime_symbols"] == ["SPY", "QQQ", "NVDA"]
    assert captured["intraday_symbols"] == ["SPY", "QQQ", "NVDA"]

    watch_summary = captured["watch_summary"]
    assert isinstance(watch_summary, WatchSummary)
    assert [item.symbol for item in watch_summary.watchlist] == ["SPY", "QQQ", "NVDA"]

    title, body = format_notification(
        NOTIFY_PREMARKET,
        "2026-04-21",
        captured["regime"],
        captured["validation_summary"],
        captured["qualification_summary"],
        {},
        watch_summary=watch_summary,
    )

    assert title == "WATCHLIST UPDATE"
    assert "SPY - " in body
    assert "QQQ - " in body
    assert "NVDA - " in body
