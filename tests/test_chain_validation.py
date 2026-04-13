"""
Tests for chain_validation.py — Layer 10 Options Chain Validation Gate.

All tests are offline. Network calls are mocked via unittest.mock.
No yfinance, yahooquery, or external API calls made during testing.
"""

import pytest
import pandas as pd
from datetime import date, datetime, timezone
from unittest.mock import patch, MagicMock

from cuttingboard.chain_validation import (
    validate_option_chains,
    _validate_setup,
    _eval_contract,
    _expiry_fit_ok,
    _filter_near_atm,
    _find_best_contract,
    _select_expiry,
    _fetch_chain_yfinance,
    _internal_consistency_check,
    _execution_reality_check,
    ChainValidationResult,
    _ContractEval,
    VALIDATED, CHAIN_FAILED, OPTIONS_WEAK, OPTIONS_INVALID, MANUAL_CHECK,
    _MIN_OI, _MIN_VOLUME, _SPREAD_PASS, _SPREAD_WEAK,
    _MIN_BID_EXECUTION, _MIN_OI_EXECUTION, _MIN_VOL_EXECUTION,
)
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.options import OptionSetup, BULL_CALL_SPREAD, BEAR_PUT_SPREAD, BULL_PUT_SPREAD


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(timezone.utc)
_TODAY = date(2026, 4, 11)


def _quote(symbol="SPY", price=480.0) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol, price=price, pct_change_decimal=0.005,
        volume=5_000_000, fetched_at_utc=_NOW,
        source="yfinance", units="USD", age_seconds=10.0,
    )


def _setup(
    symbol="SPY",
    strategy=BULL_CALL_SPREAD,
    direction="LONG",
    dte=7,
    strike_distance=5.0,
) -> OptionSetup:
    return OptionSetup(
        symbol=symbol,
        strategy=strategy,
        direction=direction,
        structure="TREND",
        iv_environment="NORMAL_IV",
        long_strike="1_ITM",
        short_strike="ATM",
        strike_distance=strike_distance,
        spread_width=1.50,
        dte=dte,
        max_contracts=1,
        dollar_risk=150.0,
        exit_profit_pct=0.50,
        exit_loss="full_debit",
    )


def _good_row(
    strike=480.0, bid=2.00, ask=2.08, oi=500, vol=200
) -> pd.Series:
    """A contract row that passes all gates with updated thresholds."""
    return pd.Series({
        "strike": strike,
        "bid": bid,
        "ask": ask,
        "openInterest": oi,
        "volume": vol,
    })


def _chain_df(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal options chain DataFrame."""
    return pd.DataFrame(rows)


def _good_chain_df(price=480.0) -> pd.DataFrame:
    """A well-behaved near-ATM chain with consistent OI and spreads."""
    return _chain_df([
        {"strike": 476.0, "bid": 2.50, "ask": 2.57, "openInterest": 600, "volume": 250},
        {"strike": 478.0, "bid": 2.20, "ask": 2.27, "openInterest": 650, "volume": 280},
        {"strike": 480.0, "bid": 2.00, "ask": 2.07, "openInterest": 700, "volume": 300},
        {"strike": 482.0, "bid": 1.80, "ask": 1.87, "openInterest": 620, "volume": 260},
        {"strike": 484.0, "bid": 1.60, "ask": 1.67, "openInterest": 580, "volume": 240},
    ])


def _mock_ticker(
    expirations=("2026-04-18", "2026-04-25"),
    calls_df=None,
    puts_df=None,
):
    """Build a mock yfinance Ticker."""
    ticker = MagicMock()
    ticker.options = expirations

    good = calls_df if calls_df is not None else _good_chain_df()

    chain = MagicMock()
    chain.calls = good
    chain.puts = puts_df if puts_df is not None else good.copy()
    ticker.option_chain.return_value = chain

    return ticker


# ---------------------------------------------------------------------------
# _eval_contract — updated thresholds: OI ≥ 200, vol ≥ 20, spread ≤8%/15%
# ---------------------------------------------------------------------------

class TestEvalContract:
    def test_good_contract_passes_all_gates(self):
        # spread = (2.08-2.00)/2.04 ≈ 3.9% → PASS; OI=500, vol=200 → liquidity ok
        row = _good_row()
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.sanity_ok
        assert ev.liquidity_ok
        assert ev.spread_grade == "PASS"

    def test_spread_grade_weak(self):
        # bid=1.75, ask=1.95 → mid=1.85, spread=0.20/1.85 ≈ 10.8% → WEAK (8–15%)
        row = _good_row(bid=1.75, ask=1.95)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.spread_grade == "WEAK"

    def test_spread_grade_fail(self):
        # bid=1.00, ask=4.00 → mid=2.50, spread=3.00/2.50 = 120% → FAIL
        row = _good_row(bid=1.00, ask=4.00)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.spread_grade == "FAIL"

    def test_spread_below_8pct_is_pass(self):
        # bid=1.91, ask=2.05 → mid≈1.98, spread=0.14/1.98 ≈ 7.1% → PASS
        row = _good_row(bid=1.91, ask=2.05)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.spread_grade == "PASS"

    def test_spread_above_15pct_is_fail(self):
        # bid=1.50, ask=1.90 → mid=1.70, spread=0.40/1.70 ≈ 23.5% → FAIL
        row = _good_row(bid=1.50, ask=1.90)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.spread_grade == "FAIL"

    def test_oi_below_threshold_fails_liquidity(self):
        # OI = _MIN_OI - 1 = 199
        row = _good_row(oi=_MIN_OI - 1, vol=200)
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.liquidity_ok

    def test_oi_at_threshold_passes_liquidity(self):
        row = _good_row(oi=_MIN_OI, vol=_MIN_VOLUME)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.liquidity_ok

    def test_volume_below_threshold_fails_liquidity(self):
        row = _good_row(oi=500, vol=_MIN_VOLUME - 1)
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.liquidity_ok

    def test_zero_bid_fails_liquidity(self):
        row = _good_row(bid=0.0, ask=2.00)
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.liquidity_ok

    def test_zero_bid_zero_ask_fails_liquidity_not_sanity(self):
        # ask=bid=0 → structurally valid but no market → liquidity failure
        row = _good_row(bid=0.0, ask=0.0)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.sanity_ok
        assert not ev.liquidity_ok

    def test_inverted_quote_fails_sanity(self):
        row = _good_row(bid=3.00, ask=2.00)
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.sanity_ok

    def test_zero_strike_fails_sanity(self):
        row = _good_row(strike=0.0)
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.sanity_ok

    def test_nan_values_parsed_as_zero(self):
        row = pd.Series({
            "strike": 480.0,
            "bid": float("nan"),
            "ask": 2.08,
            "openInterest": float("nan"),
            "volume": float("nan"),
        })
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.liquidity_ok  # bid=0 → fails


# ---------------------------------------------------------------------------
# _expiry_fit_ok
# ---------------------------------------------------------------------------

class TestExpiryFitOk:
    def test_exact_target_passes(self):
        assert _expiry_fit_ok(7, 7)

    def test_50pct_of_target_passes(self):
        assert _expiry_fit_ok(7, 14)   # 50% of 14 = 7 → boundary

    def test_below_50pct_fails(self):
        assert not _expiry_fit_ok(6, 14)   # 6 < 7

    def test_250pct_of_target_passes(self):
        assert _expiry_fit_ok(17, 7)   # 250% of 7 = 17 → boundary

    def test_above_250pct_fails(self):
        assert not _expiry_fit_ok(18, 7)

    def test_target_21_range(self):
        assert _expiry_fit_ok(10, 21)   # 50% of 21 = 10
        assert _expiry_fit_ok(52, 21)   # 250% of 21 = 52
        assert not _expiry_fit_ok(9, 21)
        assert not _expiry_fit_ok(53, 21)


# ---------------------------------------------------------------------------
# _select_expiry
# ---------------------------------------------------------------------------

class TestSelectExpiry:
    def test_selects_nearest_to_target(self):
        exps = ["2026-04-18", "2026-04-25", "2026-05-16"]
        result = _select_expiry(exps, 7, _TODAY)
        assert result == "2026-04-18"   # DTE=7, exactly target

    def test_skips_expired_dates(self):
        exps = ["2026-04-10", "2026-04-18"]
        result = _select_expiry(exps, 7, _TODAY)
        assert result == "2026-04-18"

    def test_skips_today(self):
        exps = ["2026-04-11", "2026-04-18"]
        result = _select_expiry(exps, 7, _TODAY)
        assert result == "2026-04-18"

    def test_returns_none_when_all_expired(self):
        assert _select_expiry(["2026-04-10", "2026-04-09"], 7, _TODAY) is None

    def test_returns_none_for_empty_list(self):
        assert _select_expiry([], 7, _TODAY) is None

    def test_ignores_malformed_dates(self):
        result = _select_expiry(["not-a-date", "2026-04-18"], 7, _TODAY)
        assert result == "2026-04-18"


# ---------------------------------------------------------------------------
# _filter_near_atm
# ---------------------------------------------------------------------------

class TestFilterNearAtm:
    def test_returns_n_closest_strikes(self):
        df = _chain_df([
            {"strike": 470.0}, {"strike": 475.0}, {"strike": 480.0},
            {"strike": 485.0}, {"strike": 490.0},
        ])
        result = _filter_near_atm(df, 480.0, 3)
        assert len(result) == 3
        assert set(result["strike"].tolist()) == {475.0, 480.0, 485.0}

    def test_returns_empty_when_no_strike_column(self):
        assert _filter_near_atm(_chain_df([{"bid": 1.0}]), 480.0, 5).empty

    def test_returns_all_when_fewer_than_n(self):
        df = _chain_df([{"strike": 480.0}])
        assert len(_filter_near_atm(df, 480.0, 10)) == 1


# ---------------------------------------------------------------------------
# _find_best_contract
# ---------------------------------------------------------------------------

class TestFindBestContract:
    def test_returns_highest_oi_row(self):
        df = _chain_df([
            {"strike": 478.0, "openInterest": 200},
            {"strike": 480.0, "openInterest": 1000},
            {"strike": 482.0, "openInterest": 500},
        ])
        assert _find_best_contract(df)["strike"] == 480.0

    def test_returns_first_row_when_no_oi_column(self):
        df = _chain_df([{"strike": 478.0}, {"strike": 480.0}])
        assert _find_best_contract(df)["strike"] == 478.0

    def test_returns_none_for_empty_df(self):
        assert _find_best_contract(pd.DataFrame()) is None

    def test_handles_none_oi_values(self):
        df = _chain_df([
            {"strike": 478.0, "openInterest": None},
            {"strike": 480.0, "openInterest": 1000},
        ])
        assert _find_best_contract(df)["strike"] == 480.0


# ---------------------------------------------------------------------------
# _internal_consistency_check — Step 7
# ---------------------------------------------------------------------------

class TestInternalConsistencyCheck:
    def test_consistent_chain_passes(self):
        df = _good_chain_df()
        assert _internal_consistency_check(df) is None

    def test_fewer_than_3_strikes_skips_check(self):
        df = _chain_df([
            {"strike": 480.0, "bid": 2.00, "ask": 2.08, "openInterest": 500},
            {"strike": 482.0, "bid": 1.80, "ask": 1.88, "openInterest": 450},
        ])
        assert _internal_consistency_check(df) is None

    def test_irregular_strike_gap_detected(self):
        # Strikes: 478, 480, 490 — gap of 10 vs median 2 → irregular
        df = _chain_df([
            {"strike": 478.0, "bid": 2.00, "ask": 2.07, "openInterest": 600, "volume": 250},
            {"strike": 480.0, "bid": 1.90, "ask": 1.97, "openInterest": 620, "volume": 260},
            {"strike": 490.0, "bid": 1.50, "ask": 1.57, "openInterest": 580, "volume": 230},
        ])
        reason = _internal_consistency_check(df)
        assert reason is not None
        assert "irregular" in reason.lower()

    def test_isolated_oi_spike_detected(self):
        # One contract with 10000 OI vs neighbors with 300 — isolated spike
        df = _chain_df([
            {"strike": 476.0, "bid": 2.50, "ask": 2.57, "openInterest": 300, "volume": 100},
            {"strike": 478.0, "bid": 2.20, "ask": 2.27, "openInterest": 350, "volume": 120},
            {"strike": 480.0, "bid": 2.00, "ask": 2.07, "openInterest": 10000, "volume": 300},
            {"strike": 482.0, "bid": 1.80, "ask": 1.87, "openInterest": 280, "volume": 110},
        ])
        reason = _internal_consistency_check(df)
        assert reason is not None
        assert "isolated" in reason.lower()

    def test_excessive_spread_variance_detected(self):
        # First contract has tight spread (2%), last has very wide (40%)
        df = _chain_df([
            {"strike": 478.0, "bid": 2.00, "ask": 2.04, "openInterest": 600, "volume": 250},
            {"strike": 480.0, "bid": 1.90, "ask": 1.94, "openInterest": 620, "volume": 260},
            {"strike": 482.0, "bid": 1.00, "ask": 1.80, "openInterest": 580, "volume": 220},
        ])
        reason = _internal_consistency_check(df)
        assert reason is not None
        assert "spread" in reason.lower()

    def test_uniform_low_oi_is_not_a_spike(self):
        # All OI values are low but uniform — not an isolated spike
        df = _chain_df([
            {"strike": 478.0, "bid": 2.00, "ask": 2.07, "openInterest": 200, "volume": 50},
            {"strike": 480.0, "bid": 1.90, "ask": 1.97, "openInterest": 210, "volume": 55},
            {"strike": 482.0, "bid": 1.80, "ask": 1.87, "openInterest": 205, "volume": 52},
        ])
        assert _internal_consistency_check(df) is None

    def test_regular_strike_spacing_passes(self):
        # Clean $2 spacing throughout
        df = _chain_df([
            {"strike": 476.0, "bid": 2.50, "ask": 2.56, "openInterest": 600, "volume": 250},
            {"strike": 478.0, "bid": 2.20, "ask": 2.26, "openInterest": 620, "volume": 260},
            {"strike": 480.0, "bid": 2.00, "ask": 2.06, "openInterest": 640, "volume": 270},
        ])
        assert _internal_consistency_check(df) is None


# ---------------------------------------------------------------------------
# _execution_reality_check — Step 8
# ---------------------------------------------------------------------------

class TestExecutionRealityCheck:
    def _ev(self, bid=2.00, ask=2.08, oi=700, vol=300) -> _ContractEval:
        mid = (bid + ask) / 2
        sp = (ask - bid) / mid if mid > 0 else 1.0
        liq = oi >= _MIN_OI and vol >= _MIN_VOLUME and bid > 0
        grade = "PASS" if sp <= _SPREAD_PASS else ("WEAK" if sp <= _SPREAD_WEAK else "FAIL")
        return _ContractEval(
            strike=480.0, bid=bid, ask=ask, mid=mid, spread_pct=sp,
            open_interest=oi, volume=vol,
            liquidity_ok=liq, spread_grade=grade, sanity_ok=True,
        )

    def test_good_contract_passes(self):
        assert _execution_reality_check(self._ev()) is None

    def test_near_zero_bid_downgrades(self):
        ev = self._ev(bid=0.05, ask=0.15)
        reason = _execution_reality_check(ev)
        assert reason is not None
        assert "bid" in reason.lower()

    def test_bid_at_threshold_passes(self):
        # bid = exactly _MIN_BID_EXECUTION → passes (not strictly below)
        ev = self._ev(bid=_MIN_BID_EXECUTION, ask=0.20)
        assert _execution_reality_check(ev) is None

    def test_bid_just_below_threshold_downgrades(self):
        ev = self._ev(bid=_MIN_BID_EXECUTION - 0.01, ask=0.20)
        reason = _execution_reality_check(ev)
        assert reason is not None

    def test_thin_oi_and_volume_together_downgrades(self):
        # Both OI and volume below execution thresholds but above hard liquidity floor
        ev = self._ev(bid=2.00, oi=_MIN_OI_EXECUTION - 1, vol=_MIN_VOL_EXECUTION - 1)
        reason = _execution_reality_check(ev)
        assert reason is not None
        assert "thin" in reason.lower()

    def test_thin_oi_but_good_volume_passes(self):
        # OI is thin but volume is above execution threshold → not both thin → pass
        ev = self._ev(bid=2.00, oi=_MIN_OI_EXECUTION - 1, vol=_MIN_VOL_EXECUTION + 10)
        assert _execution_reality_check(ev) is None

    def test_thin_volume_but_good_oi_passes(self):
        ev = self._ev(bid=2.00, oi=_MIN_OI_EXECUTION + 100, vol=_MIN_VOL_EXECUTION - 1)
        assert _execution_reality_check(ev) is None

    def test_good_oi_and_volume_passes(self):
        ev = self._ev(bid=2.00, oi=800, vol=300)
        assert _execution_reality_check(ev) is None


# ---------------------------------------------------------------------------
# _validate_setup — integration (mocked yfinance)
# ---------------------------------------------------------------------------

class TestValidateSetup:
    def test_validated_on_clean_chain(self):
        setup = _setup(dte=7)
        ticker = _mock_ticker()

        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18", "2026-04-25"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == VALIDATED
        assert result.data_source == "yfinance"
        assert result.expiry_used == "2026-04-18"

    def test_manual_check_when_chain_unavailable(self):
        setup = _setup()
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(None, [], None)):
            with patch("cuttingboard.chain_validation._fetch_chain_yahooquery",
                       return_value=(None, [], None)):
                result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == MANUAL_CHECK

    def test_manual_check_when_price_unavailable(self):
        setup = _setup()
        ticker = _mock_ticker()
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, None, _TODAY)

        assert result.classification == MANUAL_CHECK

    def test_chain_failed_when_expiry_too_short(self):
        setup = _setup(dte=21)
        # 2026-04-15 is DTE=4; 50% of 21 = 10 → 4 < 10 → CHAIN_FAILED
        ticker = _mock_ticker(expirations=("2026-04-15",))
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-15"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == CHAIN_FAILED
        assert "expiry" in result.reason.lower()

    def test_chain_failed_when_expiry_too_long(self):
        setup = _setup(dte=7)
        # 2026-06-10 is ~60 DTE; 250% of 7 = 17 → 60 > 17 → CHAIN_FAILED
        ticker = _mock_ticker(expirations=("2026-06-10",))
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-06-10"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == CHAIN_FAILED

    def test_invalid_on_zero_liquidity(self):
        setup = _setup()
        bad_df = _chain_df([
            {"strike": 480.0, "bid": 0.0, "ask": 0.0, "openInterest": 0, "volume": 0},
        ])
        ticker = _mock_ticker(calls_df=bad_df)
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == OPTIONS_INVALID

    def test_invalid_on_wide_spread(self):
        setup = _setup()
        # bid=1.00, ask=4.00 → spread ≈ 120% → FAIL
        bad_df = _chain_df([
            {"strike": 480.0, "bid": 1.00, "ask": 4.00, "openInterest": 500, "volume": 200},
        ])
        ticker = _mock_ticker(calls_df=bad_df)
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == OPTIONS_INVALID
        assert "spread" in result.reason.lower()

    def test_options_weak_on_spread_in_weak_range(self):
        setup = _setup()
        # bid=1.60, ask=1.90 → spread ≈ 17.1% → WEAK (8–15% range was NEW: 8–15%, but 17.1% > 15% → FAIL)
        # Use bid=1.75, ask=1.95 → mid=1.85, spread=0.20/1.85 ≈ 10.8% → WEAK
        weak_df = _chain_df([
            {"strike": 480.0, "bid": 1.75, "ask": 1.95, "openInterest": 500, "volume": 200},
        ])
        ticker = _mock_ticker(calls_df=weak_df)
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == OPTIONS_WEAK

    def test_manual_check_on_empty_chain(self):
        setup = _setup()
        chain_mock = MagicMock()
        chain_mock.calls = pd.DataFrame()
        ticker = _mock_ticker()
        ticker.option_chain.return_value = chain_mock

        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == MANUAL_CHECK

    def test_sanity_fail_yields_manual_check(self):
        setup = _setup()
        broken_df = _chain_df([
            # ask < bid → inverted quote
            {"strike": 480.0, "bid": 3.00, "ask": 1.00, "openInterest": 500, "volume": 200},
        ])
        ticker = _mock_ticker(calls_df=broken_df)
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == MANUAL_CHECK

    def test_puts_strategy_queries_put_chain(self):
        setup = _setup(strategy=BEAR_PUT_SPREAD, direction="SHORT")
        ticker = _mock_ticker()

        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        ticker.option_chain.assert_called_once_with("2026-04-18")
        assert result.classification in (VALIDATED, OPTIONS_WEAK)

    def test_isolated_oi_spike_yields_invalid(self):
        setup = _setup()
        # One contract dominates with 10000 OI, neighbors have ~300
        spike_df = _chain_df([
            {"strike": 476.0, "bid": 2.50, "ask": 2.56, "openInterest": 300, "volume": 200},
            {"strike": 478.0, "bid": 2.20, "ask": 2.26, "openInterest": 320, "volume": 210},
            {"strike": 480.0, "bid": 2.00, "ask": 2.06, "openInterest": 10000, "volume": 300},
            {"strike": 482.0, "bid": 1.80, "ask": 1.86, "openInterest": 280, "volume": 190},
            {"strike": 484.0, "bid": 1.60, "ask": 1.66, "openInterest": 260, "volume": 180},
        ])
        ticker = _mock_ticker(calls_df=spike_df)
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == OPTIONS_INVALID

    def test_thin_execution_downgrades_to_weak(self):
        setup = _setup()
        # OI just above hard floor but below execution threshold; bid > _MIN_BID_EXECUTION
        thin_df = _chain_df([
            {"strike": 480.0, "bid": 2.00, "ask": 2.06,
             "openInterest": _MIN_OI_EXECUTION - 1,
             "volume": _MIN_VOL_EXECUTION - 1},
        ])
        ticker = _mock_ticker(calls_df=thin_df)
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == OPTIONS_WEAK
        assert "thin" in result.reason.lower()


# ---------------------------------------------------------------------------
# validate_option_chains (integration)
# ---------------------------------------------------------------------------

class TestValidateOptionChains:
    def test_returns_result_per_setup(self):
        setups = [_setup("SPY"), _setup("QQQ")]
        quotes = {"SPY": _quote("SPY", 480.0), "QQQ": _quote("QQQ", 430.0)}

        ticker = _mock_ticker()
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            results = validate_option_chains(setups, quotes)

        assert "SPY" in results
        assert "QQQ" in results
        assert isinstance(results["SPY"], ChainValidationResult)

    def test_missing_quote_yields_manual_check(self):
        setups = [_setup("NVDA")]
        quotes = {}

        ticker = _mock_ticker()
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            results = validate_option_chains(setups, quotes)

        assert results["NVDA"].classification == MANUAL_CHECK

    def test_empty_setups_returns_empty_dict(self):
        assert validate_option_chains([], {}) == {}


# ---------------------------------------------------------------------------
# _fetch_chain_yfinance
# ---------------------------------------------------------------------------

class TestFetchChainYfinance:
    def test_returns_none_on_exception(self):
        with patch("cuttingboard.chain_validation.yf.Ticker",
                   side_effect=Exception("network error")):
            ticker, exps, source = _fetch_chain_yfinance("SPY")
        assert ticker is None
        assert exps == []
        assert source is None

    def test_returns_none_on_empty_expirations(self):
        mock_t = MagicMock()
        mock_t.options = []
        with patch("cuttingboard.chain_validation.yf.Ticker", return_value=mock_t):
            ticker, exps, source = _fetch_chain_yfinance("SPY")
        assert ticker is None

    def test_returns_ticker_and_expirations_on_success(self):
        mock_t = MagicMock()
        mock_t.options = ("2026-04-18", "2026-04-25")
        with patch("cuttingboard.chain_validation.yf.Ticker", return_value=mock_t):
            ticker, exps, source = _fetch_chain_yfinance("SPY")
        assert ticker is not None
        assert "2026-04-18" in exps
        assert source == "yfinance"


# ---------------------------------------------------------------------------
# ChainValidationResult immutability
# ---------------------------------------------------------------------------

class TestChainValidationResult:
    def test_is_frozen(self):
        r = ChainValidationResult(
            symbol="SPY", classification=VALIDATED, reason=None,
            spread_pct=0.04, open_interest=700, volume=300,
            expiry_used="2026-04-18", data_source="yfinance",
        )
        with pytest.raises((AttributeError, TypeError)):
            r.classification = OPTIONS_INVALID  # type: ignore
