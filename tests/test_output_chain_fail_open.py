"""PRD-234: missing chain evidence must render MANUAL CHECK, never VALIDATED.

Red-first against the fail-open default at output.render_report's TRADE
branch (a setup absent from chain_results was synthesized as VALIDATED;
an empty chain_results validated everything).
"""

from __future__ import annotations

from datetime import datetime, timezone

from cuttingboard.chain_validation import ChainValidationResult, VALIDATED
from cuttingboard.output import OUTCOME_TRADE, render_report

from tests.test_contract import (
    _option_setup,
    _qual_summary,
    _regime,
    _val_summary,
)

_NOW = datetime(2026, 7, 4, 13, 0, 0, tzinfo=timezone.utc)


def _chain(symbol: str, classification: str = VALIDATED) -> ChainValidationResult:
    return ChainValidationResult(
        symbol=symbol,
        classification=classification,
        reason=None,
        spread_pct=0.05,
        open_interest=1200,
        volume=500,
        expiry_used="2026-07-25",
        data_source="test",
    )


def _render(option_setups, chain_results):
    return render_report(
        date_str="2026-07-04",
        run_at_utc=_NOW,
        regime=_regime(),
        validation_summary=_val_summary(),
        qualification_summary=_qual_summary(qualified=1),
        option_setups=option_setups,
        outcome=OUTCOME_TRADE,
        chain_results=chain_results,
    )


def test_missing_symbol_renders_unverified_not_validated():
    # SPY validated, QQQ deliberately absent from chain_results.
    report = _render(
        [_option_setup("SPY"), _option_setup("QQQ")],
        {"SPY": _chain("SPY")},
    )

    assert "A+ TRADES  (1)" in report
    assert "CHAIN UNVERIFIED  (1)" in report
    assert "NOT checked" in report
    # QQQ's detail renders in the unverified block, after the warning.
    assert report.index("CHAIN UNVERIFIED") < report.index("QQQ")


def test_empty_chain_results_renders_all_unverified():
    report = _render([_option_setup("SPY")], {})

    assert "A+ TRADES  (0)" in report
    assert "CHAIN UNVERIFIED  (1)" in report
    assert "SPY" in report


def test_none_chain_results_renders_all_unverified():
    report = _render([_option_setup("SPY")], None)

    assert "A+ TRADES  (0)" in report
    assert "CHAIN UNVERIFIED  (1)" in report


def test_validated_setup_renders_unchanged():
    report = _render([_option_setup("SPY")], {"SPY": _chain("SPY")})

    assert "A+ TRADES  (1)" in report
    assert "CHAIN UNVERIFIED" not in report
    assert f"Chain: {VALIDATED}" in report
    assert "Exit: +50% profit or full debit loss" in report


def test_unverified_block_keeps_setup_detail():
    # The unverified block must carry the same detail lines a trader needs
    # (strategy, strikes, sizing, exit) — flagged, not hidden.
    report = _render([_option_setup("SPY")], {})

    assert "BULL_CALL_SPREAD" in report
    assert "Exit: +50% profit or full debit loss" in report
