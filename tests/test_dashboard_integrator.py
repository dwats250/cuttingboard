"""PRD-158 § 4.3 — dashboard_integrator unit tests.

Fixture-driven coverage of the four rules + a Rule 2 / Rule 3 co-render.
"""

from __future__ import annotations

from cuttingboard.delivery.dashboard_integrator import (
    RULE2_LONG_VERDICT,
    RULE2_SHORT_VERDICT,
    RULE3_MIXED_VERDICT,
    dashboard_integrator,
)


def _symbol(
    *,
    setup_direction: str | None = "long",
    current_price: float | None = 510.0,
    setup_type: str | None = "breakout",
    trigger: str | None = "above 512",
    invalidation: str | None = "below 505",
    grade: str | None = "A",
) -> dict:
    return {
        "current_price": current_price,
        "setup_direction": setup_direction,
        "setup_type": setup_type,
        "trigger": trigger,
        "invalidation": invalidation,
        "grade": grade,
    }


# ----------------------------------------------------------------------
# Rule 1 — required-data collapse (symbol scope)
# ----------------------------------------------------------------------


def test_rule1_symbol_with_missing_required_field_is_skipped() -> None:
    payload = {
        "symbols": {"SPY": _symbol(current_price=None)},
        "tiers": [("a", "A — HIGH QUALITY", ["SPY"])],
    }
    result = dashboard_integrator(payload)
    assert result["symbol_skips"] == {
        "SPY": "SPY skipped — required market data unavailable."
    }
    # Rule 4 cascade: empty tier suppressed after Rule 1 drops SPY.
    assert result["rendered_tiers"] == []


def test_rule1_symbol_with_complete_fields_is_not_skipped() -> None:
    payload = {
        "symbols": {"SPY": _symbol()},
        "tiers": [("a", "A — HIGH QUALITY", ["SPY"])],
    }
    result = dashboard_integrator(payload)
    assert result["symbol_skips"] == {}
    assert result["rendered_tiers"] == [("a", "A — HIGH QUALITY", ["SPY"])]


def test_rule1_each_required_field_independently_triggers_skip() -> None:
    for field in ("current_price", "setup_direction", "setup_type", "trigger", "invalidation"):
        payload = {"symbols": {"SPY": _symbol(**{field: None})}}
        result = dashboard_integrator(payload)
        assert "SPY" in result["symbol_skips"], f"missing {field} did not skip"


# ----------------------------------------------------------------------
# Rule 2 — regime-vs-setup-availability (screen scope)
# ----------------------------------------------------------------------


def test_rule2_longs_allowed_no_long_setups_emits_verdict() -> None:
    payload = {
        "regime_permission": "longs",
        "symbols": {"SPY": _symbol(setup_direction="short")},
    }
    result = dashboard_integrator(payload)
    assert RULE2_LONG_VERDICT in result["screen_verdicts"]
    assert result["suppress"]["permission"] is True
    assert result["suppress"]["outcome"] is True


def test_rule2_shorts_allowed_no_short_setups_emits_verdict() -> None:
    payload = {
        "regime_permission": "shorts",
        "symbols": {"SPY": _symbol(setup_direction="long")},
    }
    result = dashboard_integrator(payload)
    assert RULE2_SHORT_VERDICT in result["screen_verdicts"]
    assert result["suppress"]["permission"] is True
    assert result["suppress"]["outcome"] is True


def test_rule2_does_not_fire_when_qualifying_setups_present() -> None:
    payload = {
        "regime_permission": "longs",
        "symbols": {"SPY": _symbol(setup_direction="long")},
    }
    result = dashboard_integrator(payload)
    assert RULE2_LONG_VERDICT not in result["screen_verdicts"]
    assert RULE2_SHORT_VERDICT not in result["screen_verdicts"]


def test_rule2_stand_down_regime_emits_no_verdict() -> None:
    payload = {
        "regime_permission": "stand_down",
        "symbols": {"SPY": _symbol(setup_direction="long")},
    }
    result = dashboard_integrator(payload)
    assert result["screen_verdicts"] == []


# ----------------------------------------------------------------------
# Rule 3 — directional conflict collapse (screen scope)
# ----------------------------------------------------------------------


def test_rule3_regime_macro_setup_conflict_emits_mixed_tape() -> None:
    payload = {
        "regime_permission": "longs",
        "macro_bias_direction": "short",
        "symbols": {"SPY": _symbol(setup_direction="long")},
    }
    result = dashboard_integrator(payload)
    assert RULE3_MIXED_VERDICT in result["screen_verdicts"]
    assert result["suppress"]["macro_bias"] is True
    assert result["suppress"]["permission"] is True
    assert result["suppress"]["outcome"] is True


def test_rule3_does_not_fire_when_all_three_agree() -> None:
    payload = {
        "regime_permission": "longs",
        "macro_bias_direction": "long",
        "symbols": {"SPY": _symbol(setup_direction="long")},
    }
    result = dashboard_integrator(payload)
    assert RULE3_MIXED_VERDICT not in result["screen_verdicts"]
    assert result["suppress"]["macro_bias"] is False


def test_rule3_does_not_fire_when_macro_bias_mixed() -> None:
    payload = {
        "regime_permission": "longs",
        "macro_bias_direction": "mixed",
        "symbols": {"SPY": _symbol(setup_direction="long")},
    }
    result = dashboard_integrator(payload)
    assert RULE3_MIXED_VERDICT not in result["screen_verdicts"]


# ----------------------------------------------------------------------
# Rule 4 — empty-tier suppression (screen scope)
# ----------------------------------------------------------------------


def test_rule4_tier_with_zero_cards_after_rule1_is_suppressed() -> None:
    payload = {
        "symbols": {
            "SPY": _symbol(),  # complete
            "QQQ": _symbol(current_price=None),  # Rule 1 skip
        },
        "tiers": [
            ("a", "A — HIGH QUALITY", ["SPY"]),
            ("b", "B — DEVELOPING", ["QQQ"]),
        ],
    }
    result = dashboard_integrator(payload)
    assert result["rendered_tiers"] == [("a", "A — HIGH QUALITY", ["SPY"])]


def test_rule4_preserves_tier_order() -> None:
    payload = {
        "symbols": {"SPY": _symbol(), "QQQ": _symbol(), "GLD": _symbol()},
        "tiers": [
            ("aplus", "A+ — ACTIONABLE", ["SPY"]),
            ("a", "A — HIGH QUALITY", ["QQQ"]),
            ("b", "B — DEVELOPING", ["GLD"]),
        ],
    }
    result = dashboard_integrator(payload)
    assert [t[0] for t in result["rendered_tiers"]] == ["aplus", "a", "b"]


# ----------------------------------------------------------------------
# Rule 2 + Rule 3 co-render (required by PRD-158 Stage 2 implementation note)
# ----------------------------------------------------------------------


def test_rule2_and_rule3_co_render() -> None:
    # Regime permits longs; only setup is short → Rule 2 fires.
    # Regime longs + macro_bias short + setup short → Rule 3 also fires
    # (long regime conflicts with short bias and short setup).
    payload = {
        "regime_permission": "longs",
        "macro_bias_direction": "short",
        "symbols": {"SPY": _symbol(setup_direction="short")},
    }
    result = dashboard_integrator(payload)
    assert RULE2_LONG_VERDICT in result["screen_verdicts"]
    assert RULE3_MIXED_VERDICT in result["screen_verdicts"]
    # Both rules collapse raw permission + outcome.
    assert result["suppress"]["permission"] is True
    assert result["suppress"]["outcome"] is True
    # Rule 3 additionally collapses raw macro_bias.
    assert result["suppress"]["macro_bias"] is True
    # Rules evaluate 2 → 3, so verdict ordering reflects that.
    rule2_idx = result["screen_verdicts"].index(RULE2_LONG_VERDICT)
    rule3_idx = result["screen_verdicts"].index(RULE3_MIXED_VERDICT)
    assert rule2_idx < rule3_idx


# ----------------------------------------------------------------------
# Defensive behavior on degenerate input
# ----------------------------------------------------------------------


def test_empty_payload_returns_empty_output() -> None:
    result = dashboard_integrator({})
    assert result == {
        "symbol_skips": {},
        "screen_verdicts": [],
        "rendered_tiers": [],
        "suppress": {"permission": False, "outcome": False, "macro_bias": False},
    }


def test_none_symbol_entry_is_treated_as_missing() -> None:
    payload = {"symbols": {"SPY": None}}
    result = dashboard_integrator(payload)
    assert "SPY" in result["symbol_skips"]
