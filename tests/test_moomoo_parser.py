"""Tests for ``cuttingboard.moomoo_parser`` against the committed synthetic fixture."""

from __future__ import annotations

from datetime import date
from pathlib import Path


from cuttingboard.moomoo_parser import (
    ACCOUNT_CAD,
    ACCOUNT_USD,
    CLASS_CASH,
    CLASS_EQUITY,
    CLASS_FX,
    CLASS_OPTION,
    NormalizedTrade,
    OptionLeg,
    SIDE_BUY,
    SIDE_DEPOSIT,
    SIDE_EXPIRED,
    SIDE_FX_BUY,
    SIDE_FX_SELL,
    SIDE_SELL,
    extract_period_from_pdf,
    parse_statement,
)


FIXTURE = Path(__file__).parent / "fixtures" / "moomoo" / "synthetic_statement.pdf"


def test_fixture_exists():
    assert FIXTURE.exists(), f"missing committed fixture: {FIXTURE}"
    assert FIXTURE.stat().st_size > 0


def test_period_ending_extracted():
    assert extract_period_from_pdf(FIXTURE) == date(2026, 2, 28)


def test_parse_synthetic_statement():
    trades = parse_statement(FIXTURE)
    assert len(trades) == 9

    expected: list[NormalizedTrade] = [
        NormalizedTrade(
            date=date(2026, 2, 17), account=ACCOUNT_CAD, side=SIDE_DEPOSIT,
            instrument_class=CLASS_CASH, underlier=None, option=None,
            quantity=0.0, price=None, amount=200.0,
            raw_description="INTERAC DEPOSIT", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 23), account=ACCOUNT_CAD, side=SIDE_FX_SELL,
            instrument_class=CLASS_FX, underlier=None, option=None,
            quantity=0.0, price=None, amount=-300.0,
            raw_description="USD/CAD@1.36799", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 18), account=ACCOUNT_USD, side=SIDE_BUY,
            instrument_class=CLASS_OPTION, underlier="GLD",
            option=OptionLeg(strike=480.0, expiry=date(2026, 2, 25), right="CALL", contracts=1),
            quantity=1.0, price=5.0, amount=-501.0,
            raw_description="CALL 100 GLD 02/25/26 480", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 19), account=ACCOUNT_USD, side=SIDE_SELL,
            instrument_class=CLASS_OPTION, underlier="GLD",
            option=OptionLeg(strike=480.0, expiry=date(2026, 2, 25), right="CALL", contracts=1),
            quantity=-1.0, price=4.9, amount=489.0,
            raw_description="CALL 100 GLD 02/25/26 480", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 20), account=ACCOUNT_USD, side=SIDE_EXPIRED,
            instrument_class=CLASS_OPTION, underlier="SLV",
            option=OptionLeg(strike=67.0, expiry=date(2026, 2, 20), right="PUT", contracts=1),
            quantity=-1.0, price=0.0, amount=0.0,
            raw_description="PUT 100 SLV 02/20/26 67", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 23), account=ACCOUNT_USD, side=SIDE_FX_BUY,
            instrument_class=CLASS_FX, underlier=None, option=None,
            quantity=0.0, price=None, amount=438.59,
            raw_description="USD/CAD@1.36799", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 25), account=ACCOUNT_USD, side=SIDE_BUY,
            instrument_class=CLASS_EQUITY, underlier="SPY", option=None,
            quantity=10.0, price=580.0, amount=-5800.0,
            raw_description="SPY", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 25), account=ACCOUNT_USD, side=SIDE_SELL,
            instrument_class=CLASS_EQUITY, underlier="SPY", option=None,
            quantity=-10.0, price=585.0, amount=5850.0,
            raw_description="SPY", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 27), account=ACCOUNT_USD, side=SIDE_BUY,
            instrument_class=CLASS_EQUITY, underlier="QQQ", option=None,
            quantity=5.0, price=510.0, amount=-2550.0,
            raw_description="QQQ", next_period=True,
        ),
    ]
    assert trades == expected


def test_skip_balance_rows():
    trades = parse_statement(FIXTURE)
    descs = [t.raw_description for t in trades]
    assert "Opening Balance" not in descs
    assert "Closing Balance" not in descs


def test_option_underlier_extraction():
    trades = parse_statement(FIXTURE)
    options = [t for t in trades if t.instrument_class == CLASS_OPTION]
    assert {t.underlier for t in options} == {"GLD", "SLV"}
    for t in options:
        assert t.option is not None
        assert t.option.contracts == 1
        assert t.option.right in ("CALL", "PUT")
