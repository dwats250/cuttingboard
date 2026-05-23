"""Tests for ``cuttingboard.moomoo_join.enrich`` blind-spot attachment."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path


from cuttingboard.moomoo_join import (
    BLIND_EXPANSION_DATA_INCOMPLETE_AMBIGUOUS,
    BLIND_GAP_DOWN_SHORT_SUPPRESSED,
    BLIND_NO_AUDIT_FOR_DATE,
    BLIND_NOTIFY_MODE_ONLY,
    BLIND_UNDERLIER_NOT_IN_AUDIT_UNIVERSE,
    enrich,
)
from cuttingboard.moomoo_parser import (
    ACCOUNT_USD,
    CLASS_EQUITY,
    CLASS_OPTION,
    NormalizedTrade,
    OptionLeg,
    SIDE_BUY,
    SIDE_SELL,
)


def _write_audit(tmp_path: Path, records: list[dict]) -> Path:
    p = tmp_path / "audit.jsonl"
    with p.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
    return p


def _equity_trade(symbol: str, side: str = SIDE_BUY, d: date = date(2026, 4, 1)) -> NormalizedTrade:
    return NormalizedTrade(
        date=d, account=ACCOUNT_USD, side=side,
        instrument_class=CLASS_EQUITY, underlier=symbol, option=None,
        quantity=1.0, price=100.0, amount=-100.0,
        raw_description=symbol, next_period=False,
    )


def _put_trade(symbol: str, d: date = date(2026, 4, 1)) -> NormalizedTrade:
    leg = OptionLeg(strike=400.0, expiry=d, right="PUT", contracts=1)
    return NormalizedTrade(
        date=d, account=ACCOUNT_USD, side=SIDE_BUY,
        instrument_class=CLASS_OPTION, underlier=symbol, option=leg,
        quantity=1.0, price=2.0, amount=-200.0,
        raw_description=f"PUT 100 {symbol}", next_period=False,
    )


def _run_record(
    *,
    run_at_utc: str,
    qualified: list[dict] | None = None,
    near_a_plus: list[dict] | None = None,
    watchlist: list[dict] | None = None,
    excluded: dict | None = None,
    regime: str | None = None,
) -> dict:
    return {
        "run_at_utc": run_at_utc,
        "date": run_at_utc.split("T")[0],
        "outcome": "NO_TRADE",
        "regime": regime,
        "qualified_trades": qualified or [],
        "near_a_plus": near_a_plus or [],
        "watchlist": watchlist or [],
        "excluded_symbols": excluded or {},
    }


def test_in_universe_flag(tmp_path):
    audit = _write_audit(tmp_path, [])
    trades = [_equity_trade("SPY"), _equity_trade("ZZZZ")]
    out = enrich(trades, audit_log_path=str(audit))
    assert out[0].in_universe is True
    assert out[1].in_universe is False


def test_no_audit_for_date(tmp_path):
    audit = _write_audit(tmp_path, [])
    out = enrich([_equity_trade("SPY")], audit_log_path=str(audit))
    assert out[0].audit_records == []
    assert BLIND_NO_AUDIT_FOR_DATE in out[0].blind_spots
    assert BLIND_UNDERLIER_NOT_IN_AUDIT_UNIVERSE not in out[0].blind_spots


def test_underlier_not_in_audit_universe(tmp_path):
    """Audit exists for date but does not mention the underlier."""
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            qualified=[{"symbol": "QQQ", "intraday_state_available": True}],
        ),
    ])
    out = enrich([_equity_trade("SPY")], audit_log_path=str(audit))
    assert out[0].audit_records == []
    assert BLIND_UNDERLIER_NOT_IN_AUDIT_UNIVERSE in out[0].blind_spots
    assert BLIND_NO_AUDIT_FOR_DATE not in out[0].blind_spots


def test_gap_down_short_suppressed_put_trade(tmp_path):
    """A PUT trade with no underlier mention but date present → flagged."""
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            qualified=[{"symbol": "QQQ"}],
        ),
    ])
    out = enrich([_put_trade("SPY")], audit_log_path=str(audit))
    assert BLIND_GAP_DOWN_SHORT_SUPPRESSED in out[0].blind_spots
    assert BLIND_UNDERLIER_NOT_IN_AUDIT_UNIVERSE in out[0].blind_spots


def test_gap_down_short_suppressed_equity_sell(tmp_path):
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            qualified=[{"symbol": "QQQ"}],
        ),
    ])
    out = enrich([_equity_trade("SPY", side=SIDE_SELL)], audit_log_path=str(audit))
    assert BLIND_GAP_DOWN_SHORT_SUPPRESSED in out[0].blind_spots


def test_gap_down_not_flagged_for_long_buy(tmp_path):
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            qualified=[{"symbol": "QQQ"}],
        ),
    ])
    out = enrich([_equity_trade("SPY", side=SIDE_BUY)], audit_log_path=str(audit))
    assert BLIND_GAP_DOWN_SHORT_SUPPRESSED not in out[0].blind_spots


def test_notify_mode_only_when_no_intraday_context(tmp_path):
    """Underlier appears, but no entry carries intraday_state_available."""
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            qualified=[{"symbol": "SPY", "direction": "LONG"}],
        ),
    ])
    out = enrich([_equity_trade("SPY")], audit_log_path=str(audit))
    assert len(out[0].audit_records) == 1
    assert BLIND_NOTIFY_MODE_ONLY in out[0].blind_spots


def test_notify_mode_not_flagged_when_intraday_present(tmp_path):
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            qualified=[{"symbol": "SPY", "intraday_state_available": True}],
        ),
    ])
    out = enrich([_equity_trade("SPY")], audit_log_path=str(audit))
    assert BLIND_NOTIFY_MODE_ONLY not in out[0].blind_spots


def test_expansion_data_incomplete_ambiguous(tmp_path):
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            regime="EXPANSION",
            excluded={"SPY": "DATA_INCOMPLETE"},
        ),
    ])
    out = enrich([_equity_trade("SPY")], audit_log_path=str(audit))
    assert BLIND_EXPANSION_DATA_INCOMPLETE_AMBIGUOUS in out[0].blind_spots


def test_expansion_data_incomplete_not_flagged_for_other_reason(tmp_path):
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            regime="EXPANSION",
            excluded={"SPY": "CHOP"},
        ),
    ])
    out = enrich([_equity_trade("SPY")], audit_log_path=str(audit))
    assert BLIND_EXPANSION_DATA_INCOMPLETE_AMBIGUOUS not in out[0].blind_spots


def test_expansion_data_incomplete_not_flagged_outside_expansion(tmp_path):
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            regime="RISK_ON",
            excluded={"SPY": "DATA_INCOMPLETE"},
        ),
    ])
    out = enrich([_equity_trade("SPY")], audit_log_path=str(audit))
    assert BLIND_EXPANSION_DATA_INCOMPLETE_AMBIGUOUS not in out[0].blind_spots


def test_audit_records_chronologically_ordered(tmp_path):
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T19:00:00+00:00",
            qualified=[{"symbol": "SPY"}],
        ),
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            qualified=[{"symbol": "SPY"}],
        ),
        _run_record(
            run_at_utc="2026-04-01T15:00:00+00:00",
            qualified=[{"symbol": "SPY"}],
        ),
    ])
    out = enrich([_equity_trade("SPY")], audit_log_path=str(audit))
    timestamps = [r["run_at_utc"] for r in out[0].audit_records]
    assert timestamps == sorted(timestamps)


def test_combined_blind_spots_expansion_plus_notify(tmp_path):
    """EXPANSION + DATA_INCOMPLETE + no intraday context → both flags."""
    audit = _write_audit(tmp_path, [
        _run_record(
            run_at_utc="2026-04-01T13:00:00+00:00",
            regime="EXPANSION",
            excluded={"SPY": "DATA_INCOMPLETE"},
        ),
    ])
    out = enrich([_equity_trade("SPY")], audit_log_path=str(audit))
    assert BLIND_EXPANSION_DATA_INCOMPLETE_AMBIGUOUS in out[0].blind_spots
    # SPY only appears in excluded_symbols (no qualified/near_a_plus entry)
    # so no intraday context exists → notify_mode_only also flagged.
    assert BLIND_NOTIFY_MODE_ONLY in out[0].blind_spots


def test_notification_records_filtered_out(tmp_path):
    """Notification-event records lack outcome and must be filtered."""
    audit_path = tmp_path / "audit.jsonl"
    with audit_path.open("w", encoding="utf-8") as fh:
        # A notification record (no outcome, no run_at_utc)
        fh.write(json.dumps({"event": "notification", "timestamp": "2026-04-01T13:00:00+00:00"}) + "\n")
        # An empty line
        fh.write("\n")
        # A malformed JSON line
        fh.write("not json\n")
    out = enrich([_equity_trade("SPY")], audit_log_path=str(audit_path))
    assert out[0].audit_records == []
    assert BLIND_NO_AUDIT_FOR_DATE in out[0].blind_spots
