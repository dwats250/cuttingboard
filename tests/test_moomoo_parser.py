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
    assert len(trades) == 11

    expected: list[NormalizedTrade] = [
        # CAD section
        NormalizedTrade(
            date=date(2026, 2, 17), account=ACCOUNT_CAD, side=SIDE_DEPOSIT,
            instrument_class=CLASS_CASH, underlier=None, option=None,
            quantity=0.0, price=None, amount=200.0,
            raw_description="INTERAC DEPOSIT", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 18), account=ACCOUNT_CAD, side=SIDE_DEPOSIT,
            instrument_class=CLASS_CASH, underlier=None, option=None,
            quantity=0.0, price=None, amount=1.37,
            raw_description="REBATE", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 23), account=ACCOUNT_CAD, side=SIDE_FX_SELL,
            instrument_class=CLASS_FX, underlier=None, option=None,
            quantity=0.0, price=None, amount=-300.0,
            raw_description="USD/CAD@1.36799", next_period=False,
        ),
        # USD section
        NormalizedTrade(
            date=date(2026, 2, 18), account=ACCOUNT_USD, side=SIDE_BUY,
            instrument_class=CLASS_OPTION, underlier="GLD",
            option=OptionLeg(strike=480.0, expiry=date(2026, 2, 25), right="CALL", contracts=1),
            quantity=1.0, price=5.0, amount=-501.0,
            raw_description="CALL 100 GLD 02/25/26 480 *", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 19), account=ACCOUNT_USD, side=SIDE_SELL,
            instrument_class=CLASS_OPTION, underlier="GLD",
            option=OptionLeg(strike=480.0, expiry=date(2026, 2, 25), right="CALL", contracts=1),
            quantity=-1.0, price=4.9, amount=489.0,
            raw_description="CALL 100 GLD 02/25/26 480 *", next_period=False,
        ),
        NormalizedTrade(
            date=date(2026, 2, 20), account=ACCOUNT_USD, side=SIDE_EXPIRED,
            instrument_class=CLASS_OPTION, underlier="SLV",
            option=OptionLeg(strike=67.0, expiry=date(2026, 2, 20), right="PUT", contracts=1),
            quantity=-1.0, price=None, amount=0.0,
            raw_description="PUT 100 SLV 02/20/26 67 *", next_period=False,
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
            date=date(2026, 2, 26), account=ACCOUNT_USD, side=SIDE_BUY,
            instrument_class=CLASS_EQUITY, underlier=None, option=None,
            quantity=10.0, price=15.11, amount=-153.09,
            raw_description="ETF OPPORTUNITIES TR T REX 2X", next_period=False,
        ),
        # Transactions to settle after current period
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


# ---------------------------------------------------------------------------
# Defect-specific regression coverage (PRD-153 2026-05-22 validation arc)
# ---------------------------------------------------------------------------

def test_defect_a_expired_option_has_no_price():
    """Expired Option rows extract with 2 trailing numerics, not 3."""
    trades = parse_statement(FIXTURE)
    expired = [t for t in trades if t.side == SIDE_EXPIRED]
    assert len(expired) == 1
    assert expired[0].price is None
    assert expired[0].quantity == -1.0
    assert expired[0].amount == 0.0
    assert expired[0].option is not None
    assert expired[0].option.contracts == 1


def test_defect_b_option_star_suffix_parsed():
    """Bare ``*`` between strike and quantity does not break option parsing."""
    trades = parse_statement(FIXTURE)
    options = [t for t in trades if t.instrument_class == CLASS_OPTION and t.underlier == "GLD"]
    assert len(options) == 2
    for t in options:
        assert t.raw_description.endswith(" *")
        assert t.option is not None and t.option.strike == 480.0


def test_defect_c_wrapped_etransfer_type_cell():
    """Wrapped E-transfer\\nDeposit Type cell parses as a single DEPOSIT row."""
    trades = parse_statement(FIXTURE)
    deposits = [t for t in trades if t.side == SIDE_DEPOSIT and t.raw_description == "INTERAC DEPOSIT"]
    assert len(deposits) == 1
    assert deposits[0].account == ACCOUNT_CAD
    assert deposits[0].amount == 200.0
    # The orphan 'Deposit' continuation line is consumed, not parsed as a stray row.
    raw_descs = [t.raw_description for t in trades]
    assert "Deposit" not in raw_descs


def test_defect_d_cash_rebate_parsed_as_deposit():
    """Cash Rebate rows fold into the existing DEPOSIT/CASH shape."""
    trades = parse_statement(FIXTURE)
    rebates = [t for t in trades if t.raw_description == "REBATE"]
    assert len(rebates) == 1
    assert rebates[0].side == SIDE_DEPOSIT
    assert rebates[0].instrument_class == CLASS_CASH
    assert rebates[0].underlier is None
    assert rebates[0].option is None
    assert rebates[0].amount == 1.37


def test_defect_e_multiword_equity_yields_none_underlier():
    """Multi-word equity descriptions without a ticker yield underlier=None."""
    trades = parse_statement(FIXTURE)
    multiword = [t for t in trades if t.raw_description == "ETF OPPORTUNITIES TR T REX 2X"]
    assert len(multiword) == 1
    assert multiword[0].underlier is None
    assert multiword[0].instrument_class == CLASS_EQUITY
    assert multiword[0].quantity == 10.0
    assert multiword[0].price == 15.11
