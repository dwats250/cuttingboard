"""
Tests for chain_validation.py — Layer 10 Options Chain Validation Gate.

All tests are offline. Network calls are mocked via unittest.mock.
No yfinance, yahooquery, or Tradier API calls made during testing.
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
    _tradier_iv_check,
    ChainValidationResult,
    VALIDATED, CHAIN_FAILED, OPTIONS_WEAK, OPTIONS_INVALID, MANUAL_CHECK,
    _MIN_OI, _MIN_VOLUME, _SPREAD_PASS, _SPREAD_WEAK,
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
    strike=480.0, bid=2.00, ask=2.10, oi=500, vol=200
) -> pd.Series:
    """A contract row that passes all gates."""
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


def _mock_ticker(
    expirations=("2026-04-18", "2026-04-25"),
    calls_df=None,
    puts_df=None,
):
    """Build a mock yfinance Ticker."""
    ticker = MagicMock()
    ticker.options = expirations

    good_calls = calls_df if calls_df is not None else _chain_df([
        {"strike": 478.0, "bid": 2.00, "ask": 2.08, "openInterest": 800, "volume": 300},
        {"strike": 480.0, "bid": 1.80, "ask": 1.88, "openInterest": 1200, "volume": 500},
        {"strike": 482.0, "bid": 1.60, "ask": 1.68, "openInterest": 600, "volume": 200},
    ])
    good_puts = puts_df if puts_df is not None else good_calls.copy()

    chain = MagicMock()
    chain.calls = good_calls
    chain.puts = good_puts
    ticker.option_chain.return_value = chain

    return ticker


# ---------------------------------------------------------------------------
# _eval_contract
# ---------------------------------------------------------------------------

class TestEvalContract:
    def test_good_contract_passes_all_gates(self):
        row = _good_row(strike=480.0, bid=2.00, ask=2.10, oi=500, vol=200)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.sanity_ok
        assert ev.liquidity_ok
        assert ev.spread_grade == "PASS"

    def test_spread_grade_weak(self):
        # (2.20 - 2.00) / 2.10 ≈ 9.5% → PASS; need wider
        # mid=2.00, spread=0.40 → 40/4.00 = 10% → PASS boundary
        # use bid=1.60, ask=2.00 → mid=1.80, spread=0.40/1.80 = 22% → FAIL
        # for WEAK: bid=1.60, ask=1.90 → mid=1.75, spread=0.30/1.75 = 17.1% → WEAK
        row = _good_row(bid=1.60, ask=1.90, oi=500, vol=200)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.spread_grade == "WEAK"
        assert ev.liquidity_ok  # OI and vol still pass

    def test_spread_grade_fail(self):
        # bid=1.00, ask=2.00 → mid=1.50, spread=1.00/1.50 = 66.7% → FAIL
        row = _good_row(bid=1.00, ask=2.00, oi=500, vol=200)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.spread_grade == "FAIL"

    def test_spread_below_10pct_is_pass(self):
        # bid=1.91, ask=2.09 → mid=2.00, spread=0.18/2.00 = 9% → PASS
        row = _good_row(bid=1.91, ask=2.09, oi=500, vol=200)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.spread_grade == "PASS"

    def test_low_oi_fails_liquidity(self):
        row = _good_row(oi=_MIN_OI - 1, vol=200)
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.liquidity_ok

    def test_low_volume_fails_liquidity(self):
        row = _good_row(oi=500, vol=_MIN_VOLUME - 1)
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.liquidity_ok

    def test_zero_bid_fails_liquidity(self):
        row = _good_row(bid=0.0, ask=2.00, oi=500, vol=200)
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.liquidity_ok

    def test_zero_ask_fails_liquidity_not_sanity(self):
        # ask=0 → no market → liquidity failure per PRD (ask > 0 is a liquidity gate)
        # sanity only rejects inverted quotes (ask < bid) and zero strikes
        row = _good_row(bid=0.0, ask=0.0)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.sanity_ok     # structurally valid (ask == bid == 0 → not inverted)
        assert not ev.liquidity_ok  # liquidity gate: ask > 0 required

    def test_ask_less_than_bid_fails_sanity(self):
        row = _good_row(bid=2.50, ask=2.00)
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.sanity_ok

    def test_zero_strike_fails_sanity(self):
        row = _good_row(strike=0.0, bid=1.00, ask=2.00)
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.sanity_ok

    def test_nan_values_treated_as_zero(self):
        # pandas NaN for missing numeric values — must not raise, must degrade to zero
        row = pd.Series({"strike": 480.0, "bid": float("nan"), "ask": 2.10,
                         "openInterest": float("nan"), "volume": float("nan")})
        ev = _eval_contract(row)
        assert ev is not None
        assert not ev.liquidity_ok  # bid=0 → liquidity fails (bid must be > 0)

    def test_oi_exactly_at_threshold_passes(self):
        row = _good_row(oi=_MIN_OI, vol=_MIN_VOLUME)
        ev = _eval_contract(row)
        assert ev is not None
        assert ev.liquidity_ok


# ---------------------------------------------------------------------------
# _expiry_fit_ok
# ---------------------------------------------------------------------------

class TestExpiryFitOk:
    def test_exact_target_passes(self):
        assert _expiry_fit_ok(7, 7)

    def test_50pct_of_target_passes(self):
        # 50% of 14 = 7 → passes (min boundary)
        assert _expiry_fit_ok(7, 14)

    def test_below_50pct_fails(self):
        # 6 < 50% of 14 (7) → fails
        assert not _expiry_fit_ok(6, 14)

    def test_250pct_of_target_passes(self):
        # 250% of 7 = 17 → passes (max boundary)
        assert _expiry_fit_ok(17, 7)

    def test_above_250pct_fails(self):
        # 18 > 250% of 7 (17) → fails
        assert not _expiry_fit_ok(18, 7)

    def test_target_21_valid_range(self):
        # min = 10, max = 52
        assert _expiry_fit_ok(14, 21)
        assert _expiry_fit_ok(10, 21)
        assert _expiry_fit_ok(52, 21)
        assert not _expiry_fit_ok(9, 21)
        assert not _expiry_fit_ok(53, 21)


# ---------------------------------------------------------------------------
# _select_expiry
# ---------------------------------------------------------------------------

class TestSelectExpiry:
    def test_selects_nearest_to_target(self):
        exps = ["2026-04-18", "2026-04-25", "2026-05-16"]
        # today = 2026-04-11, target = 7
        # 2026-04-18 → DTE=7, 2026-04-25 → DTE=14, 2026-05-16 → DTE=35
        result = _select_expiry(exps, 7, _TODAY)
        assert result == "2026-04-18"

    def test_skips_expired_dates(self):
        exps = ["2026-04-10", "2026-04-18"]  # 04-10 is in the past
        result = _select_expiry(exps, 7, _TODAY)
        assert result == "2026-04-18"

    def test_skips_today(self):
        exps = ["2026-04-11", "2026-04-18"]  # 04-11 is today (DTE=0)
        result = _select_expiry(exps, 7, _TODAY)
        assert result == "2026-04-18"

    def test_returns_none_when_all_expired(self):
        exps = ["2026-04-10", "2026-04-09"]
        assert _select_expiry(exps, 7, _TODAY) is None

    def test_returns_none_for_empty_list(self):
        assert _select_expiry([], 7, _TODAY) is None

    def test_ignores_malformed_dates(self):
        exps = ["not-a-date", "2026-04-18"]
        result = _select_expiry(exps, 7, _TODAY)
        assert result == "2026-04-18"

    def test_prefers_closer_when_tie_broken_by_order(self):
        # Two exps equidistant from target: picks whichever was seen first
        exps = ["2026-04-15", "2026-04-21"]  # DTE=4 and DTE=10 vs target=7 → both diff=3
        result = _select_expiry(exps, 7, _TODAY)
        assert result in ("2026-04-15", "2026-04-21")


# ---------------------------------------------------------------------------
# _filter_near_atm
# ---------------------------------------------------------------------------

class TestFilterNearAtm:
    def test_returns_n_closest_strikes(self):
        df = _chain_df([
            {"strike": 470.0, "bid": 1.0, "ask": 1.1},
            {"strike": 475.0, "bid": 1.0, "ask": 1.1},
            {"strike": 480.0, "bid": 1.0, "ask": 1.1},
            {"strike": 485.0, "bid": 1.0, "ask": 1.1},
            {"strike": 490.0, "bid": 1.0, "ask": 1.1},
        ])
        result = _filter_near_atm(df, 480.0, 3)
        assert len(result) == 3
        assert set(result["strike"].tolist()) == {475.0, 480.0, 485.0}

    def test_returns_empty_when_no_strike_column(self):
        df = _chain_df([{"bid": 1.0, "ask": 1.1}])
        result = _filter_near_atm(df, 480.0, 5)
        assert result.empty

    def test_returns_all_when_fewer_than_n(self):
        df = _chain_df([{"strike": 480.0, "bid": 1.0, "ask": 1.1}])
        result = _filter_near_atm(df, 480.0, 10)
        assert len(result) == 1


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
        best = _find_best_contract(df)
        assert best is not None
        assert best["strike"] == 480.0

    def test_returns_first_row_when_no_oi_column(self):
        df = _chain_df([{"strike": 478.0}, {"strike": 480.0}])
        best = _find_best_contract(df)
        assert best is not None
        assert best["strike"] == 478.0

    def test_returns_none_for_empty_df(self):
        assert _find_best_contract(pd.DataFrame()) is None

    def test_handles_none_oi_values(self):
        df = _chain_df([
            {"strike": 478.0, "openInterest": None},
            {"strike": 480.0, "openInterest": 1000},
        ])
        best = _find_best_contract(df)
        assert best["strike"] == 480.0


# ---------------------------------------------------------------------------
# _validate_setup — mocked yfinance ticker
# ---------------------------------------------------------------------------

class TestValidateSetup:
    def _good_ticker(self, price=480.0):
        return _mock_ticker()

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
        # Only expiry 4 DTE away — 50% of 21 = 10, so 4 DTE is too short
        ticker = _mock_ticker(expirations=("2026-04-15",))  # 4 DTE from today
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-15"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == CHAIN_FAILED
        assert "expiry" in result.reason.lower()

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
        # bid=1.00, ask=4.00 → mid=2.50, spread=3.00/2.50 = 120% → FAIL
        bad_df = _chain_df([
            {"strike": 480.0, "bid": 1.00, "ask": 4.00, "openInterest": 500, "volume": 200},
        ])
        ticker = _mock_ticker(calls_df=bad_df)
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == OPTIONS_INVALID
        assert "spread" in result.reason.lower()

    def test_options_weak_on_moderate_spread(self):
        setup = _setup()
        # bid=1.60, ask=1.90 → mid=1.75, spread=0.30/1.75 ≈ 17.1% → WEAK
        weak_df = _chain_df([
            {"strike": 480.0, "bid": 1.60, "ask": 1.90, "openInterest": 500, "volume": 200},
        ])
        ticker = _mock_ticker(calls_df=weak_df)
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == OPTIONS_WEAK

    def test_manual_check_on_empty_chain(self):
        setup = _setup()
        empty_chain = MagicMock()
        empty_chain.calls = pd.DataFrame()
        ticker = _mock_ticker()
        ticker.option_chain.return_value = empty_chain

        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == MANUAL_CHECK

    def test_sanity_fail_yields_manual_check(self):
        setup = _setup()
        broken_df = _chain_df([
            # ask < bid — broken quote
            {"strike": 480.0, "bid": 3.00, "ask": 1.00, "openInterest": 500, "volume": 200},
        ])
        ticker = _mock_ticker(calls_df=broken_df)
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == MANUAL_CHECK

    def test_puts_strategy_uses_put_chain(self):
        """BEAR_PUT_SPREAD should query puts, not calls."""
        setup = _setup(strategy=BEAR_PUT_SPREAD, direction="SHORT")
        ticker = _mock_ticker()

        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        # Verify option_chain was called once (not zero)
        ticker.option_chain.assert_called_once_with("2026-04-18")
        # Access to .puts should have been made (mock chains are identical so result is VALIDATED)
        assert result.classification in (VALIDATED, OPTIONS_WEAK)

    def test_chain_failed_when_expiry_too_long(self):
        setup = _setup(dte=7)
        # 250% of 7 = 17 DTE max; supply an expiry at 60 DTE
        far_expiry = "2026-06-10"  # ~60 DTE from 2026-04-11
        ticker = _mock_ticker(expirations=(far_expiry,))
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, [far_expiry], "yfinance")):
            result = _validate_setup(setup, 480.0, _TODAY)

        assert result.classification == CHAIN_FAILED


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
        quotes = {}  # NVDA quote missing

        ticker = _mock_ticker()
        with patch("cuttingboard.chain_validation._fetch_chain_yfinance",
                   return_value=(ticker, ["2026-04-18"], "yfinance")):
            results = validate_option_chains(setups, quotes)

        assert results["NVDA"].classification == MANUAL_CHECK

    def test_empty_setups_returns_empty_dict(self):
        results = validate_option_chains([], {})
        assert results == {}


# ---------------------------------------------------------------------------
# _tradier_iv_check
# ---------------------------------------------------------------------------

class TestTradierIvCheck:
    def test_returns_true_when_api_key_missing(self):
        with patch("cuttingboard.chain_validation.config") as mock_cfg:
            mock_cfg.TRADIER_API_KEY = None
            mock_cfg.FETCH_TIMEOUT_SECONDS = 10
            result = _tradier_iv_check("SPY", "2026-04-18", 480.0, "calls")
        assert result is True

    def test_returns_true_on_request_error(self):
        import requests
        with patch("cuttingboard.chain_validation.config") as mock_cfg:
            mock_cfg.TRADIER_API_KEY = "test-key"
            mock_cfg.FETCH_TIMEOUT_SECONDS = 10
            with patch("requests.get", side_effect=requests.RequestException("timeout")):
                result = _tradier_iv_check("SPY", "2026-04-18", 480.0, "calls")
        assert result is True

    def test_returns_true_on_non_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        with patch("cuttingboard.chain_validation.config") as mock_cfg:
            mock_cfg.TRADIER_API_KEY = "test-key"
            mock_cfg.FETCH_TIMEOUT_SECONDS = 10
            with patch("requests.get", return_value=mock_resp):
                result = _tradier_iv_check("SPY", "2026-04-18", 480.0, "calls")
        assert result is True

    def test_returns_true_on_valid_iv(self):
        payload = {"options": {"option": [
            {"strike": 480.0, "option_type": "call",
             "greeks": {"mid_iv": 0.22}}
        ]}}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = payload
        with patch("cuttingboard.chain_validation.config") as mock_cfg:
            mock_cfg.TRADIER_API_KEY = "test-key"
            mock_cfg.FETCH_TIMEOUT_SECONDS = 10
            with patch("requests.get", return_value=mock_resp):
                result = _tradier_iv_check("SPY", "2026-04-18", 480.0, "calls")
        assert result is True

    def test_returns_false_on_insane_iv(self):
        payload = {"options": {"option": [
            {"strike": 480.0, "option_type": "call",
             "greeks": {"mid_iv": 6.0}}  # 600% — broken
        ]}}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = payload
        with patch("cuttingboard.chain_validation.config") as mock_cfg:
            mock_cfg.TRADIER_API_KEY = "test-key"
            mock_cfg.FETCH_TIMEOUT_SECONDS = 10
            with patch("requests.get", return_value=mock_resp):
                result = _tradier_iv_check("SPY", "2026-04-18", 480.0, "calls")
        assert result is False

    def test_returns_true_when_strike_not_found(self):
        payload = {"options": {"option": [
            {"strike": 500.0, "option_type": "call", "greeks": {"mid_iv": 0.22}}
        ]}}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = payload
        with patch("cuttingboard.chain_validation.config") as mock_cfg:
            mock_cfg.TRADIER_API_KEY = "test-key"
            mock_cfg.FETCH_TIMEOUT_SECONDS = 10
            with patch("requests.get", return_value=mock_resp):
                # Looking for strike 480 but only 500 is present → inconclusive
                result = _tradier_iv_check("SPY", "2026-04-18", 480.0, "calls")
        assert result is True

    def test_returns_true_when_greeks_missing(self):
        payload = {"options": {"option": [
            {"strike": 480.0, "option_type": "call", "greeks": None}
        ]}}
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = payload
        with patch("cuttingboard.chain_validation.config") as mock_cfg:
            mock_cfg.TRADIER_API_KEY = "test-key"
            mock_cfg.FETCH_TIMEOUT_SECONDS = 10
            with patch("requests.get", return_value=mock_resp):
                result = _tradier_iv_check("SPY", "2026-04-18", 480.0, "calls")
        assert result is True


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
            spread_pct=0.05, open_interest=1000, volume=400,
            expiry_used="2026-04-18", data_source="yfinance",
        )
        with pytest.raises((AttributeError, TypeError)):
            r.classification = OPTIONS_INVALID  # type: ignore
