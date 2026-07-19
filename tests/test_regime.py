"""
Phase 3 tests — macro regime engine.

All tests are offline: NormalizedQuote fixtures are injected directly.
No network calls, no file I/O.
"""

import itertools
from datetime import datetime, timezone

import pytest

from cuttingboard.normalization import NormalizedQuote
from cuttingboard.regime import (
    RISK_ON, RISK_OFF, NEUTRAL, CHAOTIC,
    AGGRESSIVE_LONG, CONTROLLED_LONG, NEUTRAL_PREMIUM, DEFENSIVE_SHORT, STAY_FLAT,
    EXPANSION_LONG,
    compute_regime, from_validation_results,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _q(symbol: str, price: float, pct_change: float, units: str = "usd_price") -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol,
        price=price,
        pct_change_decimal=pct_change,
        volume=1_000_000.0,
        fetched_at_utc=datetime.now(timezone.utc),
        source="yfinance",
        units=units,
        age_seconds=5.0,
    )


def _risk_on_quotes() -> dict[str, NormalizedQuote]:
    """All 8 inputs decisively risk-on."""
    return {
        "SPY":      _q("SPY",      540.0,   +0.010),  # > +0.003 ✓
        "QQQ":      _q("QQQ",      450.0,   +0.010),  # > +0.003 ✓
        "IWM":      _q("IWM",      200.0,   +0.008),  # > +0.004 ✓
        "^VIX":     _q("^VIX",      14.0,   -0.050, "index_level"),  # level <18 ✓, pct <-0.03 ✓
        "DX-Y.NYB": _q("DX-Y.NYB", 100.0,   -0.005),  # < -0.002 ✓
        "^TNX":     _q("^TNX",       4.0,   -0.010, "yield_pct"),  # < -0.005 ✓
        "BTC-USD":  _q("BTC-USD", 80000.0,  +0.030),  # > +0.015 ✓
    }


def _risk_off_quotes() -> dict[str, NormalizedQuote]:
    """All 8 inputs decisively risk-off."""
    return {
        "SPY":      _q("SPY",      540.0,   -0.015),  # < -0.003 ✓
        "QQQ":      _q("QQQ",      450.0,   -0.015),  # < -0.003 ✓
        "IWM":      _q("IWM",      200.0,   -0.010),  # < -0.004 ✓
        "^VIX":     _q("^VIX",      30.0,   +0.080, "index_level"),  # level >25 ✓, pct >+0.05 ✓
        "DX-Y.NYB": _q("DX-Y.NYB", 100.0,   +0.008),  # > +0.003 ✓
        "^TNX":     _q("^TNX",       4.5,   +0.015, "yield_pct"),  # > +0.008 ✓
        "BTC-USD":  _q("BTC-USD", 80000.0,  -0.030),  # < -0.020 ✓
    }


def _transition_quotes() -> dict[str, NormalizedQuote]:
    """All inputs near neutral — mixed signals."""
    return {
        "SPY":      _q("SPY",      540.0,   +0.001),  # NEUTRAL (not > 0.003)
        "QQQ":      _q("QQQ",      450.0,   -0.001),  # NEUTRAL
        "IWM":      _q("IWM",      200.0,   +0.002),  # NEUTRAL
        "^VIX":     _q("^VIX",      20.0,   +0.010, "index_level"),  # level NEUTRAL(18-25), pct NEUTRAL
        "DX-Y.NYB": _q("DX-Y.NYB", 100.0,   +0.001),  # NEUTRAL
        "^TNX":     _q("^TNX",       4.2,   +0.003, "yield_pct"),  # NEUTRAL
        "BTC-USD":  _q("BTC-USD", 80000.0,  +0.005),  # NEUTRAL (not > 0.015)
    }


# ---------------------------------------------------------------------------
# Regime classification tests
# ---------------------------------------------------------------------------

class TestRegimeClassification:
    def test_risk_on_decisive(self):
        state = compute_regime(_risk_on_quotes())
        assert state.regime == RISK_ON

    def test_risk_off_decisive(self):
        state = compute_regime(_risk_off_quotes())
        assert state.regime == RISK_OFF

    def test_neutral_mixed(self):
        state = compute_regime(_transition_quotes())
        assert state.regime == NEUTRAL

    def test_chaotic_override_on_vix_spike(self):
        quotes = _risk_on_quotes()
        # Override VIX with a spike > 15%
        quotes = dict(quotes)
        quotes["^VIX"] = _q("^VIX", 25.0, +0.20, "index_level")  # +20% > +15%
        state = compute_regime(quotes)
        assert state.regime == CHAOTIC

    def test_chaotic_overrides_even_risk_on_votes(self):
        # Strong risk-on everywhere but VIX spikes > 15%
        quotes = _risk_on_quotes()
        quotes = dict(quotes)
        quotes["^VIX"] = _q("^VIX", 20.0, +0.16, "index_level")  # spike > 0.15
        state = compute_regime(quotes)
        assert state.regime == CHAOTIC

    def test_vix_spike_exactly_at_threshold_not_chaotic(self):
        # Exactly 0.15 is NOT > 0.15 — should not trigger CHAOTIC
        quotes = dict(_risk_on_quotes())
        quotes["^VIX"] = _q("^VIX", 18.0, +0.15, "index_level")
        state = compute_regime(quotes)
        assert state.regime != CHAOTIC

    def test_net_score_plus2_is_risk_on(self):
        # net_score = +2 → RISK_ON (moderate rule)
        quotes = {
            "SPY":      _q("SPY",       540.0, +0.010),  # RISK_ON
            "QQQ":      _q("QQQ",       450.0, +0.010),  # RISK_ON
            "IWM":      _q("IWM",       200.0, +0.001),  # NEUTRAL
            "^VIX":     _q("^VIX",       20.0, +0.010, "index_level"),  # both NEUTRAL
            "DX-Y.NYB": _q("DX-Y.NYB", 100.0, +0.001),  # NEUTRAL
            "^TNX":     _q("^TNX",        4.2, +0.003, "yield_pct"),  # NEUTRAL
            "BTC-USD":  _q("BTC-USD",  80000.0, +0.005),  # NEUTRAL
        }
        state = compute_regime(quotes)
        assert state.net_score == 2
        assert state.regime == RISK_ON

    def test_net_score_minus2_is_risk_off(self):
        quotes = {
            "SPY":      _q("SPY",       540.0, -0.010),  # RISK_OFF
            "QQQ":      _q("QQQ",       450.0, -0.010),  # RISK_OFF
            "IWM":      _q("IWM",       200.0, +0.001),  # NEUTRAL
            "^VIX":     _q("^VIX",       20.0, +0.010, "index_level"),  # both NEUTRAL
            "DX-Y.NYB": _q("DX-Y.NYB", 100.0, +0.001),  # NEUTRAL
            "^TNX":     _q("^TNX",        4.2, +0.003, "yield_pct"),  # NEUTRAL
            "BTC-USD":  _q("BTC-USD",  80000.0, +0.005),  # NEUTRAL
        }
        state = compute_regime(quotes)
        assert state.net_score == -2
        assert state.regime == RISK_OFF


# ---------------------------------------------------------------------------
# Vote breakdown tests
# ---------------------------------------------------------------------------

class TestVoteBreakdown:
    def test_all_8_keys_present_when_all_symbols_available(self):
        state = compute_regime(_risk_on_quotes())
        expected_keys = {
            "SPY pct_change", "QQQ pct_change", "IWM pct_change",
            "VIX level", "VIX pct_change",
            "DXY pct_change", "TNX pct_change", "BTC pct_change",
        }
        assert set(state.vote_breakdown.keys()) == expected_keys

    def test_risk_on_votes_are_correct(self):
        state = compute_regime(_risk_on_quotes())
        for key, vote in state.vote_breakdown.items():
            assert vote == "RISK_ON", f"{key} should be RISK_ON, got {vote}"

    def test_risk_off_votes_are_correct(self):
        state = compute_regime(_risk_off_quotes())
        for key, vote in state.vote_breakdown.items():
            assert vote == "RISK_OFF", f"{key} should be RISK_OFF, got {vote}"

    def test_skipped_symbol_reduces_total_votes(self):
        # IWM absent — 7 votes cast instead of 8
        quotes = {k: v for k, v in _risk_on_quotes().items() if k != "IWM"}
        state = compute_regime(quotes)
        assert state.total_votes == 7
        assert "IWM pct_change" not in state.vote_breakdown

    def test_vix_contributes_two_votes(self):
        state = compute_regime(_risk_on_quotes())
        assert "VIX level" in state.vote_breakdown
        assert "VIX pct_change" in state.vote_breakdown

    def test_vote_values_are_valid_strings(self):
        state = compute_regime(_transition_quotes())
        valid = {"RISK_ON", "RISK_OFF", "NEUTRAL"}
        for key, vote in state.vote_breakdown.items():
            assert vote in valid, f"{key}: unexpected vote value '{vote}'"


# ---------------------------------------------------------------------------
# Confidence tests
# ---------------------------------------------------------------------------

class TestConfidence:
    def test_confidence_formula(self):
        state = compute_regime(_risk_on_quotes())
        expected = abs(state.net_score) / state.total_votes
        assert state.confidence == pytest.approx(expected, rel=1e-9)

    def test_perfect_risk_on_confidence_is_one(self):
        # All 8 votes risk-on → net_score=8, confidence=1.0
        state = compute_regime(_risk_on_quotes())
        assert state.confidence == pytest.approx(1.0)
        assert state.risk_on_votes == 8
        assert state.risk_off_votes == 0

    def test_perfect_risk_off_confidence_is_one(self):
        state = compute_regime(_risk_off_quotes())
        assert state.confidence == pytest.approx(1.0)
        assert state.risk_off_votes == 8

    def test_all_neutral_confidence_is_zero(self):
        state = compute_regime(_transition_quotes())
        assert state.net_score == 0
        assert state.confidence == pytest.approx(0.0)

    def test_confidence_range(self):
        for quotes in [_risk_on_quotes(), _risk_off_quotes(), _transition_quotes()]:
            state = compute_regime(quotes)
            assert 0.0 <= state.confidence <= 1.0


# ---------------------------------------------------------------------------
# Posture tests
# ---------------------------------------------------------------------------

class TestPosture:
    def test_aggressive_long_high_confidence_risk_on(self):
        # confidence ≥ 0.75 → AGGRESSIVE_LONG
        state = compute_regime(_risk_on_quotes())
        assert state.confidence >= 0.75
        assert state.posture == AGGRESSIVE_LONG

    def test_controlled_long_medium_confidence(self):
        # Need RISK_ON + confidence in [0.55, 0.75) at FULL coverage (PRD-263):
        # 5 risk-on, 0 risk-off, 3 neutral → net=5, total=8, confidence=5/8=0.625
        # → RISK_ON; 0.55 ≤ 0.625 < 0.75 → CONTROLLED_LONG
        quotes = {
            "SPY":      _q("SPY",       540.0, +0.010),   # RISK_ON
            "QQQ":      _q("QQQ",       450.0, +0.010),   # RISK_ON
            "IWM":      _q("IWM",       200.0, +0.008),   # RISK_ON
            "^VIX":     _q("^VIX",       14.0, -0.010, "index_level"),  # level RISK_ON, pct NEUTRAL
            "DX-Y.NYB": _q("DX-Y.NYB", 100.0, -0.005),   # RISK_ON
            "^TNX":     _q("^TNX",        4.2, +0.003, "yield_pct"),    # NEUTRAL
            "BTC-USD":  _q("BTC-USD",  80000.0, +0.005),  # NEUTRAL
        }
        state = compute_regime(quotes)
        assert state.regime == RISK_ON
        assert state.net_score == 5
        assert state.total_votes == 8
        assert state.confidence == pytest.approx(5 / 8)
        assert 0.55 <= state.confidence < 0.75
        assert state.posture == CONTROLLED_LONG

    def test_defensive_short_risk_off_high_confidence(self):
        state = compute_regime(_risk_off_quotes())
        assert state.regime == RISK_OFF
        assert state.confidence >= 0.55
        assert state.posture == DEFENSIVE_SHORT

    def test_stay_flat_chaotic(self):
        quotes = dict(_risk_on_quotes())
        quotes["^VIX"] = _q("^VIX", 25.0, +0.20, "index_level")
        state = compute_regime(quotes)
        assert state.regime == CHAOTIC
        assert state.posture == STAY_FLAT

    def test_stay_flat_low_confidence(self):
        # net_score=1, total_votes=8 → confidence=0.125 < 0.50 → STAY_FLAT
        quotes = {
            "SPY":      _q("SPY",       540.0, +0.010),  # RISK_ON
            "QQQ":      _q("QQQ",       450.0, +0.001),  # NEUTRAL
            "IWM":      _q("IWM",       200.0, +0.001),  # NEUTRAL
            "^VIX":     _q("^VIX",       20.0, +0.010, "index_level"),  # both NEUTRAL
            "DX-Y.NYB": _q("DX-Y.NYB", 100.0, +0.001),  # NEUTRAL
            "^TNX":     _q("^TNX",        4.2, +0.003, "yield_pct"),  # NEUTRAL
            "BTC-USD":  _q("BTC-USD",  80000.0, +0.005),  # NEUTRAL
        }
        state = compute_regime(quotes)
        assert state.net_score == 1
        assert state.confidence < 0.50
        assert state.posture == STAY_FLAT

    def test_vix_only_synthetic_is_bounded_to_stay_flat(self):
        # PRD-263: this fixture (VIX alone, 2 cast votes) was the last path to
        # NEUTRAL_PREMIUM through compute_regime. Worst-case bounding scores
        # the 6 missing votes against the leader: net_cast=1, k=6 →
        # bounded_net=0, confidence=0.0 → NEUTRAL / STAY_FLAT. NEUTRAL_PREMIUM
        # is unreachable via compute_regime at any coverage (NEUTRAL implies
        # |bounded_net| ≤ 1 → confidence ≤ 0.125 < 0.50 floor); the posture
        # branch is retained untouched (parking list, PRD-263 OUT OF SCOPE).
        quotes = {
            "^VIX": _q("^VIX", 22.0, -0.04, "index_level"),
        }
        state = compute_regime(quotes)
        assert state.regime == NEUTRAL
        assert state.net_score == 1          # cast net stays truthful
        assert state.total_votes == 2        # cast count stays truthful
        assert state.confidence == pytest.approx(0.0)
        assert state.vix_level == pytest.approx(22.0)
        assert state.posture == STAY_FLAT

    def test_stay_flat_neutral_vix_above_25(self):
        quotes = dict(_transition_quotes())
        quotes["^VIX"] = _q("^VIX", 26.0, +0.010, "index_level")  # VIX > 25
        state = compute_regime(quotes)
        assert state.regime == NEUTRAL
        assert state.posture == STAY_FLAT


# ---------------------------------------------------------------------------
# VIX state tests
# ---------------------------------------------------------------------------

class TestVIXState:
    def test_vix_level_stored_on_state(self):
        quotes = _risk_on_quotes()
        state = compute_regime(quotes)
        assert state.vix_level == pytest.approx(14.0)

    def test_vix_pct_stored_on_state(self):
        state = compute_regime(_risk_on_quotes())
        assert state.vix_pct_change == pytest.approx(-0.050)

    def test_vix_absent_level_is_none(self):
        quotes = {k: v for k, v in _risk_on_quotes().items() if k != "^VIX"}
        state = compute_regime(quotes)
        assert state.vix_level is None
        assert state.vix_pct_change is None


# ---------------------------------------------------------------------------
# Bridge / dataclass tests
# ---------------------------------------------------------------------------

class TestBridgeAndDataclass:
    def test_from_validation_results_bridge(self):

        # Build a fake flat results list
        class _FakeResult:
            def __init__(self, symbol, quote):
                self.symbol = symbol
                self.passed = True
                self.quote = quote
                self.failure_reason = None

        results = [_FakeResult(sym, q) for sym, q in _risk_on_quotes().items()]
        state = from_validation_results(results)
        assert state.regime == RISK_ON

    def test_from_validation_results_skips_failed(self):
        class _FakeResult:
            def __init__(self, symbol, quote, passed):
                self.symbol = symbol
                self.passed = passed
                self.quote = quote
                self.failure_reason = None if passed else "timeout"

        results = [
            _FakeResult("SPY", _q("SPY", 540.0, +0.010), passed=True),
            _FakeResult("QQQ", _q("QQQ", 450.0, +0.010), passed=False),  # excluded
        ]
        state = from_validation_results(results)
        assert "QQQ pct_change" not in state.vote_breakdown

    def test_regime_state_is_frozen(self):
        state = compute_regime(_risk_on_quotes())
        with pytest.raises((AttributeError, TypeError)):
            state.regime = "SOMETHING_ELSE"  # type: ignore

    def test_computed_at_utc_is_aware(self):
        state = compute_regime(_risk_on_quotes())
        assert state.computed_at_utc.tzinfo is not None

    def test_total_votes_equals_breakdown_count(self):
        state = compute_regime(_risk_on_quotes())
        assert state.total_votes == len(state.vote_breakdown)

    def test_vote_counts_sum_to_total(self):
        state = compute_regime(_risk_on_quotes())
        assert state.risk_on_votes + state.risk_off_votes + state.neutral_votes == state.total_votes


# ---------------------------------------------------------------------------
# Coverage bounding — PRD-263 (Tier-4 quorum floor)
#
# Worst-case bounding: each missing vote (only IWM / BTC-USD can silently
# drop in production; the other 6 votes come from HALT_SYMBOLS) is scored as
# if it voted against the survivors' leader. bounded_net =
# sign(net) * max(0, |net| - k), confidence = |bounded_net| / 8. A skipped
# vote can then never make the verdict more permissive.
# ---------------------------------------------------------------------------

# Explicit permissiveness lattice. CHAOTIC and STAY_FLAT are pinned
# least-permissive so the monotonicity test cannot pass vacuously.
_POSTURE_RANK = {
    STAY_FLAT:       0,   # includes CHAOTIC regime (posture STAY_FLAT)
    NEUTRAL_PREMIUM: 1,
    CONTROLLED_LONG: 2,
    DEFENSIVE_SHORT: 2,
    AGGRESSIVE_LONG: 3,
    EXPANSION_LONG:  3,
}

# Per-slot quote parameters realizing each vote value. VIX level and VIX pct
# are two independent votes carried by one ^VIX quote. The RISK_OFF VIX pct
# (+0.06) stays below the CHAOTIC spike threshold (0.15) so the exhaustive
# sweeps exercise the vote model, not the override.
_SLOT_ON_OFF_NEUTRAL = {
    "SPY":       ("SPY",      540.0,    {"on": +0.010, "off": -0.010, "neutral": 0.0}),
    "QQQ":       ("QQQ",      450.0,    {"on": +0.010, "off": -0.010, "neutral": 0.0}),
    "IWM":       ("IWM",      200.0,    {"on": +0.008, "off": -0.010, "neutral": 0.0}),
    "DX-Y.NYB":  ("DX-Y.NYB", 100.0,    {"on": -0.005, "off": +0.008, "neutral": 0.0}),
    "^TNX":      ("^TNX",       4.2,    {"on": -0.010, "off": +0.015, "neutral": 0.0}),
    "BTC-USD":   ("BTC-USD", 80000.0,   {"on": +0.030, "off": -0.030, "neutral": 0.0}),
}
_VIX_LEVEL = {"on": 14.0, "off": 30.0, "neutral": 20.0}
_VIX_PCT   = {"on": -0.05, "off": +0.06, "neutral": 0.0}


def _quotes_for_votes(
    spy, qqq, iwm, vix_level, vix_pct, dxy, tnx, btc,
) -> dict[str, NormalizedQuote]:
    """Build a quote dict casting exactly the given 8 votes."""
    votes = {"SPY": spy, "QQQ": qqq, "IWM": iwm, "DX-Y.NYB": dxy,
             "^TNX": tnx, "BTC-USD": btc}
    quotes = {}
    for slot, vote in votes.items():
        sym, price, pcts = _SLOT_ON_OFF_NEUTRAL[slot]
        units = "yield_pct" if sym == "^TNX" else "usd_price"
        quotes[sym] = _q(sym, price, pcts[vote], units)
    quotes["^VIX"] = _q("^VIX", _VIX_LEVEL[vix_level], _VIX_PCT[vix_pct], "index_level")
    return quotes


def _drop(quotes: dict, *symbols: str) -> dict:
    return {k: v for k, v in quotes.items() if k not in symbols}


class TestCoverageBounding:
    def test_sol_f1_iwm_dropout_stays_flat(self):
        # sol F1 (PRD-262 SECOND-MODEL, evidence exhibit 2): 4 risk-on among
        # the survivors, 3 neutral, IWM absent. Survivor denominator gave
        # 4/7 ≈ 0.571 → CONTROLLED_LONG. Bounded: net 4 - k 1 = 3 → 0.375
        # → RISK_ON / STAY_FLAT.
        quotes = {
            "SPY":      _q("SPY",       540.0, +0.010),  # RISK_ON
            "QQQ":      _q("QQQ",       450.0, +0.010),  # RISK_ON
            "DX-Y.NYB": _q("DX-Y.NYB", 100.0, -0.005),   # RISK_ON
            "^TNX":     _q("^TNX",        4.2, -0.010, "yield_pct"),  # RISK_ON
            "^VIX":     _q("^VIX",       20.0, +0.010, "index_level"),  # both NEUTRAL
            "BTC-USD":  _q("BTC-USD",  80000.0, +0.005),  # NEUTRAL
        }
        state = compute_regime(quotes)
        assert state.total_votes == 7
        assert state.net_score == 4          # cast net stays truthful
        assert state.confidence == pytest.approx(0.375)
        assert state.regime == RISK_ON
        assert state.posture == STAY_FLAT

    def test_fable_six_votes_do_not_out_permit_eight(self):
        # FABLE addendum arithmetic: 4 RISK_ON + 2 NEUTRAL. At 8 votes the
        # same evidence (plus two neutral votes) is 0.50 → STAY_FLAT; the
        # 6-vote version must not out-permit it. Survivor denominator gave
        # 4/6 ≈ 0.667 → CONTROLLED_LONG. Bounded: net 4 - k 2 = 2 → 0.25.
        six = {
            "SPY":      _q("SPY",       540.0, +0.010),   # RISK_ON
            "QQQ":      _q("QQQ",       450.0, +0.010),   # RISK_ON
            "^VIX":     _q("^VIX",       14.0, -0.050, "index_level"),  # both RISK_ON
            "DX-Y.NYB": _q("DX-Y.NYB", 100.0, +0.001),   # NEUTRAL
            "^TNX":     _q("^TNX",        4.2, +0.003, "yield_pct"),    # NEUTRAL
        }
        eight = dict(six)
        eight["IWM"]     = _q("IWM",      200.0, +0.001)   # NEUTRAL
        eight["BTC-USD"] = _q("BTC-USD", 80000.0, +0.005)  # NEUTRAL

        full    = compute_regime(eight)
        dropped = compute_regime(six)
        assert full.posture == STAY_FLAT       # 4/8 = 0.50 < 0.55
        assert dropped.posture == STAY_FLAT
        assert dropped.confidence == pytest.approx(0.25)
        assert _POSTURE_RANK[dropped.posture] <= _POSTURE_RANK[full.posture]

    def test_unanimous_seven_survivors_still_aggressive(self):
        # Availability at 7 cast votes: unanimous survivors reach bounded
        # net 6 → confidence 0.75 → AGGRESSIVE_LONG (the pre-existing exact
        # >= 0.75 boundary that full-coverage net 6 already sits on).
        state = compute_regime(_drop(_risk_on_quotes(), "IWM"))
        assert state.total_votes == 7
        assert state.net_score == 7
        assert state.confidence == pytest.approx(0.75)
        assert state.posture == AGGRESSIVE_LONG

    def test_seven_votes_net_six_is_controlled_long(self):
        # 6 risk-on + 1 neutral at 7 cast → bounded net 5 → 0.625 →
        # CONTROLLED_LONG (was 6/7 ≈ 0.857 → AGGRESSIVE_LONG pre-PRD-263).
        quotes = _drop(_risk_on_quotes(), "IWM")
        quotes["BTC-USD"] = _q("BTC-USD", 80000.0, +0.005)  # NEUTRAL
        state = compute_regime(quotes)
        assert state.total_votes == 7
        assert state.net_score == 6
        assert state.confidence == pytest.approx(0.625)
        assert state.posture == CONTROLLED_LONG

    def test_dropout_never_more_permissive_exhaustive(self):
        # R2: for every realizable full-coverage vote assignment (3^8),
        # dropping IWM, BTC-USD, or both never raises the posture rank and
        # never raises confidence.
        choices = ("on", "off", "neutral")
        for combo in itertools.product(choices, repeat=8):
            quotes = _quotes_for_votes(*combo)
            full = compute_regime(quotes)
            for drops in (("IWM",), ("BTC-USD",), ("IWM", "BTC-USD")):
                state = compute_regime(_drop(quotes, *drops))
                assert _POSTURE_RANK[state.posture] <= _POSTURE_RANK[full.posture], (
                    f"votes={combo} drops={drops}: "
                    f"{full.regime}/{full.posture} -> {state.regime}/{state.posture}"
                )
                assert state.confidence <= full.confidence + 1e-9, (
                    f"votes={combo} drops={drops}: "
                    f"confidence {full.confidence} -> {state.confidence}"
                )

    def test_six_votes_never_reach_tradable_posture(self):
        # R3 structural floor: with IWM and BTC-USD both absent (the only
        # silently droppable inputs), bounded confidence caps at 4/8 = 0.50
        # < 0.55 — no assignment of the 6 halt-symbol votes can trade.
        choices = ("on", "off", "neutral")
        for combo in itertools.product(choices, repeat=6):
            spy, qqq, vix_level, vix_pct, dxy, tnx = combo
            quotes = _drop(
                _quotes_for_votes(spy, qqq, "neutral", vix_level, vix_pct,
                                  dxy, tnx, "neutral"),
                "IWM", "BTC-USD",
            )
            state = compute_regime(quotes)
            assert state.total_votes == 6
            assert state.posture == STAY_FLAT, (
                f"votes={combo}: {state.regime}/{state.posture} "
                f"confidence={state.confidence}"
            )

    def test_zero_clamp_never_crosses_sign(self):
        # net_cast = +1 at 6 cast votes (k=2): bounding clamps at zero —
        # NEUTRAL with confidence 0.0, never a sign-flip toward RISK_OFF.
        quotes = _drop(
            _quotes_for_votes("on", "neutral", "neutral", "neutral",
                              "neutral", "neutral", "neutral", "neutral"),
            "IWM", "BTC-USD",
        )
        state = compute_regime(quotes)
        assert state.total_votes == 6
        assert state.net_score == 1          # cast net stays truthful
        assert state.regime == NEUTRAL
        assert state.regime != RISK_OFF
        assert state.confidence == pytest.approx(0.0)
        assert state.posture == STAY_FLAT

    def test_vix_fields_populated_under_bounding(self):
        # R4: bounding must never null the kill switch's VIX feed.
        quotes = _drop(
            _quotes_for_votes("on", "on", "neutral", "neutral", "neutral",
                              "on", "on", "neutral"),
            "IWM", "BTC-USD",
        )
        state = compute_regime(quotes)
        assert state.total_votes == 6
        assert state.vix_level == pytest.approx(_VIX_LEVEL["neutral"])
        assert state.vix_pct_change == pytest.approx(_VIX_PCT["neutral"])
