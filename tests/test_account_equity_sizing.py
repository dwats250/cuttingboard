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
