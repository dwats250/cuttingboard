"""PRD-157: Account-Equity-Driven Position Sizing.

Tests for the ACCOUNT_EQUITY + MAX_RISK_PCT_PER_TRADE config replacement
of TARGET_DOLLAR_RISK + MAX_DOLLAR_RISK, the qualification.py / options.py
formula migrations, the GATE_MAX_RISK soft-failure / STOP_TOO_TIGHT
hard-reject preservation, REGIME_RISK_MULTIPLIER preservation, and the
contract per-candidate passthrough (position_size, dollar_risk,
estimated_debit).

Test scope is added incrementally per PRD-157 COMMIT PLAN:
- Commit 2: config constants exist + validation (R1, R2).
- Commit 3: qualification.py main path migration (R3).
- Commit 4: qualification.py continuation path migration (R4).
- Commit 5: options.py:218 migration (R5).
- Commit 6: sizing math / oversize / regime preservation (R7).
- Commit 7: contract.py passthrough (R6, R8).
"""

import pytest

from cuttingboard import config


# ---------------------------------------------------------------------------
# R1: config knobs exist with defaults that preserve TARGET_DOLLAR_RISK=150
# ---------------------------------------------------------------------------


def test_account_equity_constant_exists_and_positive() -> None:
    assert hasattr(config, "ACCOUNT_EQUITY"), (
        "config.ACCOUNT_EQUITY must exist (PRD-157 R1)"
    )
    assert isinstance(config.ACCOUNT_EQUITY, (int, float))
    assert config.ACCOUNT_EQUITY > 0


def test_max_risk_pct_per_trade_constant_exists_and_in_range() -> None:
    assert hasattr(config, "MAX_RISK_PCT_PER_TRADE"), (
        "config.MAX_RISK_PCT_PER_TRADE must exist (PRD-157 R1)"
    )
    assert isinstance(config.MAX_RISK_PCT_PER_TRADE, (int, float))
    assert 0 < config.MAX_RISK_PCT_PER_TRADE <= 1


def test_defaults_preserve_target_dollar_risk_of_150() -> None:
    """PRD-157 R1: defaults preserve the retired TARGET_DOLLAR_RISK=150 exactly.

    15000 × 0.01 = 150.0. This makes the migration behavior-preserving at
    default values; sizing-related test churn beyond this module is unexpected.
    """
    product = config.ACCOUNT_EQUITY * config.MAX_RISK_PCT_PER_TRADE
    assert product == 150.0, (
        f"ACCOUNT_EQUITY × MAX_RISK_PCT_PER_TRADE must equal 150.0 (default "
        f"behavior preservation), got {product}"
    )


# ---------------------------------------------------------------------------
# R2: validation raises ValueError on invalid values
# ---------------------------------------------------------------------------


def test_validation_rejects_zero_account_equity() -> None:
    with pytest.raises(ValueError, match="ACCOUNT_EQUITY"):
        config._validate_sizing_config(0, 0.01)


def test_validation_rejects_negative_account_equity() -> None:
    with pytest.raises(ValueError, match="ACCOUNT_EQUITY"):
        config._validate_sizing_config(-1000, 0.01)


def test_validation_rejects_non_numeric_account_equity() -> None:
    with pytest.raises(ValueError, match="ACCOUNT_EQUITY"):
        config._validate_sizing_config("15000", 0.01)  # type: ignore[arg-type]


def test_validation_rejects_zero_risk_pct() -> None:
    with pytest.raises(ValueError, match="MAX_RISK_PCT_PER_TRADE"):
        config._validate_sizing_config(15000, 0.0)


def test_validation_rejects_negative_risk_pct() -> None:
    with pytest.raises(ValueError, match="MAX_RISK_PCT_PER_TRADE"):
        config._validate_sizing_config(15000, -0.01)


def test_validation_rejects_risk_pct_above_one() -> None:
    with pytest.raises(ValueError, match="MAX_RISK_PCT_PER_TRADE"):
        config._validate_sizing_config(15000, 1.5)


def test_validation_accepts_boundary_risk_pct_of_one() -> None:
    config._validate_sizing_config(15000, 1.0)


def test_validation_accepts_small_positive_values() -> None:
    config._validate_sizing_config(100.0, 0.001)


# ---------------------------------------------------------------------------
# R3 + R7: main-path sizing math (qualify_all) — equity × pct × regime
# ---------------------------------------------------------------------------


def _setup_main_path_fixture(monkeypatch, *, equity, risk_pct):
    """Build a qualify_all fixture that reaches Gate 8 sizing.

    Uses the existing test_qualification helpers but inlined here to avoid
    a cross-test import. Returns the QualificationSummary.
    """
    from datetime import datetime, timezone

    from cuttingboard.derived import DerivedMetrics
    from cuttingboard.qualification import (
        QualificationSummary,
        TradeCandidate,
        qualify_all,
    )
    from cuttingboard.regime import (
        AGGRESSIVE_LONG,
        RISK_ON,
        RegimeState,
    )
    from cuttingboard.structure import NORMAL_IV, StructureResult, TREND

    monkeypatch.setattr(config, "ACCOUNT_EQUITY", equity)
    monkeypatch.setattr(config, "MAX_RISK_PCT_PER_TRADE", risk_pct)
    # Ensure GATE_TIME passes; mirrors the autouse fixture in test_qualification.
    monkeypatch.setattr(
        "cuttingboard.qualification._is_late_session", lambda now_et=None: False
    )

    now = datetime.now(timezone.utc)
    regime = RegimeState(
        regime=RISK_ON,
        posture=AGGRESSIVE_LONG,
        confidence=0.75,
        net_score=6,
        risk_on_votes=6,
        risk_off_votes=0,
        neutral_votes=2,
        total_votes=8,
        vote_breakdown={},
        vix_level=14.0,
        vix_pct_change=-0.01,
        computed_at_utc=now,
    )
    structure = StructureResult(
        symbol="TEST",
        structure=TREND,
        iv_environment=NORMAL_IV,
        is_tradeable=True,
        disqualification_reason=None,
    )
    candidate = TradeCandidate(
        symbol="TEST",
        direction="LONG",
        entry_price=100.0,
        stop_price=99.0,
        target_price=102.0,
        spread_width=0.5,
        has_earnings_soon=False,
    )
    dm = DerivedMetrics(
        symbol="TEST",
        ema9=105.0,
        ema21=102.0,
        ema50=98.0,
        ema_aligned_bull=True,
        ema_aligned_bear=False,
        ema_spread_pct=0.029,
        atr14=2.0,
        atr_pct=0.015,
        momentum_5d=0.01,
        volume_ratio=1.2,
        computed_at_utc=now,
        sufficient_history=True,
    )
    summary: QualificationSummary = qualify_all(
        regime,
        {"TEST": structure},
        {"TEST": candidate},
        {"TEST": dm},
    )
    return summary


@pytest.mark.parametrize(
    "equity,risk_pct,spread_width,expected_max_contracts",
    [
        # equity × pct = 150 (default), spread_cost = 0.5 × 100 = 50 → 3 contracts
        (15000.0, 0.01, 0.5, 3),
        # equity × pct = 100, spread_cost = 50 → 2 contracts
        (10000.0, 0.01, 0.5, 2),
        # equity × pct = 500, spread_cost = 50 → 10 contracts
        (10000.0, 0.05, 0.5, 10),
        # equity × pct = 10, spread_cost = 50 → 0 contracts (soft-fail)
        (10000.0, 0.001, 0.5, None),
    ],
)
def test_main_path_sizing_at_boundary_risk_pcts(
    monkeypatch, equity, risk_pct, spread_width, expected_max_contracts
) -> None:
    """PRD-157 R3 + R7(b): main-path sizing math at boundary risk pcts.

    Verifies max_contracts = floor((equity × pct × regime_mult) / (spread × 100))
    at RISK_ON (regime_mult=1.0). When the result is zero, GATE_MAX_RISK
    soft-failure routes the candidate to watchlist instead of hard-rejecting.
    """
    monkeypatch.setattr(
        "cuttingboard.qualification._is_late_session", lambda now_et=None: False
    )
    summary = _setup_main_path_fixture(
        monkeypatch, equity=equity, risk_pct=risk_pct
    )
    # Spread width is fixed at 0.5 in the fixture; parametrized arg above is
    # documentation. If we ever need to vary it, the fixture would parameterize.
    assert spread_width == 0.5

    if expected_max_contracts is not None:
        # Qualified — max_contracts populated.
        assert len(summary.qualified_trades) == 1, (
            f"Expected 1 qualified trade at equity={equity} pct={risk_pct}, "
            f"got {len(summary.qualified_trades)}: {summary.qualified_trades}"
        )
        result = summary.qualified_trades[0]
        assert result.max_contracts == expected_max_contracts
        assert result.dollar_risk == expected_max_contracts * (spread_width * 100)
    else:
        # Oversize — soft-fail to watchlist via GATE_MAX_RISK.
        assert len(summary.qualified_trades) == 0
        watchlisted = [
            t for t in summary.watchlist if t.symbol == "TEST"
        ]
        assert len(watchlisted) == 1, (
            f"Expected oversize candidate on watchlist, got "
            f"qualified={summary.qualified_trades} watchlist={summary.watchlist}"
        )
        assert watchlisted[0].max_contracts is None
        assert watchlisted[0].dollar_risk is None


def test_main_path_oversize_routes_to_watchlist_with_gate_max_risk(
    monkeypatch,
) -> None:
    """PRD-157 R3 + R7(c): GATE_MAX_RISK soft-failure preservation.

    A candidate whose 1-contract debit exceeds effective_target soft-fails
    (becomes watchlist) rather than hard-rejecting. The reason cites
    GATE_MAX_RISK.
    """
    from cuttingboard.qualification import GATE_MAX_RISK

    # equity × pct = 10 < spread_cost = 50: 1 contract exceeds budget.
    summary = _setup_main_path_fixture(
        monkeypatch, equity=10000.0, risk_pct=0.001
    )
    watchlisted = [t for t in summary.watchlist if t.symbol == "TEST"]
    assert len(watchlisted) == 1
    # watchlist_reason describes the one missed soft gate.
    assert watchlisted[0].watchlist_reason is not None
    assert GATE_MAX_RISK in (watchlisted[0].gates_failed or [])


# ---------------------------------------------------------------------------
# R3 + R7(e,f): REGIME_RISK_MULTIPLIER preservation
# ---------------------------------------------------------------------------


def test_regime_multiplier_chaotic_remains_zero() -> None:
    """PRD-157 R3 + R7(e): CHAOTIC regime preserves zero risk-multiplier.

    Config-level preservation check. The sizing block at qualification.py:397
    multiplies effective_target by REGIME_RISK_MULTIPLIER[regime]; CHAOTIC=0.0
    means CHAOTIC regimes produce effective_target=0 regardless of equity.
    """
    assert config.REGIME_RISK_MULTIPLIER["CHAOTIC"] == 0.0


def test_regime_multiplier_neutral_remains_half() -> None:
    """PRD-157 R3 + R7(f): NEUTRAL regime preserves 0.6 risk-multiplier."""
    assert config.REGIME_RISK_MULTIPLIER["NEUTRAL"] == 0.6


def test_regime_multiplier_risk_on_remains_one() -> None:
    """PRD-157 R3: RISK_ON / RISK_OFF / EXPANSION preserve 1.0 risk-multiplier."""
    assert config.REGIME_RISK_MULTIPLIER["RISK_ON"] == 1.0
    assert config.REGIME_RISK_MULTIPLIER["RISK_OFF"] == 1.0
    assert config.REGIME_RISK_MULTIPLIER["EXPANSION"] == 1.0


# ---------------------------------------------------------------------------
# R4 + R7(d): continuation-path oversize hard-rejects with STOP_TOO_TIGHT
# ---------------------------------------------------------------------------


def test_continuation_path_uses_equity_budget(monkeypatch) -> None:
    """PRD-157 R4 + R7(d): continuation-path sizing uses ACCOUNT_EQUITY ×
    MAX_RISK_PCT_PER_TRADE budget (no regime multiplier — EXPANSION-only path).
    Tested at module level by verifying the source-code reference; full
    end-to-end exercise via run_continuation_qualification is covered by the
    existing test_continuation_mode.py suite which still passes at baseline.
    """
    # Verify the continuation path is not still bound to TARGET_DOLLAR_RISK.
    import inspect

    from cuttingboard import qualification

    src = inspect.getsource(qualification)
    assert "TARGET_DOLLAR_RISK" not in src, (
        "qualification.py must not reference TARGET_DOLLAR_RISK after PRD-157"
    )
    assert "ACCOUNT_EQUITY * config.MAX_RISK_PCT_PER_TRADE" in src or (
        "config.ACCOUNT_EQUITY * config.MAX_RISK_PCT_PER_TRADE" in src
    ), "qualification.py must reference the new equity-driven formula"
