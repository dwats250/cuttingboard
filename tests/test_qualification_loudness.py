"""PRD-235: the three silent qualification paths become observable.

Red-first: NEUTRAL-direction symbols vanish entirely; gates 9/10 pass
silently on missing data. Outcomes must NOT change — only visibility.
"""

from __future__ import annotations

from datetime import datetime, timezone

from cuttingboard.output import OUTCOME_TRADE, render_report
from cuttingboard.qualification import (
    GATE_EARNINGS,
    GATE_EXTENSION,
    QualificationSummary,
    qualify_all,
    qualify_candidate,
)
from cuttingboard.regime import NEUTRAL, NEUTRAL_PREMIUM

from tests.test_contract import _option_setup, _val_summary
from tests.test_contract import _regime as _contract_regime
from tests.test_qualification import _candidate, _dm, _regime, _structure

_NOW = datetime(2026, 7, 4, 15, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# R1 — NEUTRAL symbols are excluded, not vanished
# ---------------------------------------------------------------------------

def test_neutral_no_direction_symbol_lands_in_excluded():
    regime = _regime(regime=NEUTRAL, posture=NEUTRAL_PREMIUM, net_score=0)
    structure_results = {"SPY": _structure("SPY")}
    candidates = {"SPY": _candidate("SPY")}

    summary = qualify_all(regime, structure_results, candidates)

    all_symbols = (
        {r.symbol for r in summary.qualified_trades}
        | {r.symbol for r in summary.watchlist}
        | set(summary.excluded)
    )
    assert "SPY" in all_symbols, "NEUTRAL symbol vanished from all output"
    assert summary.excluded.get("SPY") == "NEUTRAL_NO_DIRECTION"


def test_neutral_exclusion_fires_on_production_call_shape():
    # PR #102 P2: the runtime call sites pass `candidates or None`, and
    # generate_candidates returns {} precisely in the no-direction case —
    # so production reaches qualify_all with candidates=None. The
    # exclusion must fire on that shape, not only on a supplied dict.
    regime = _regime(regime=NEUTRAL, posture=NEUTRAL_PREMIUM, net_score=0)
    structure_results = {"SPY": _structure("SPY")}

    summary = qualify_all(regime, structure_results, None)

    assert summary.excluded.get("SPY") == "NEUTRAL_NO_DIRECTION"


# ---------------------------------------------------------------------------
# R2 — missing-data passes are marked, outcomes unchanged
# ---------------------------------------------------------------------------

def _qualify(candidate_kwargs=None, dm="present"):
    regime = _regime()
    candidate = _candidate("SPY", **(candidate_kwargs or {}))
    sr = _structure("SPY")
    metrics = None if dm is None else _dm("SPY")
    morning_et = datetime(2026, 7, 4, 10, 0, 0)  # well before the 3:30 PM ET cutoff
    return qualify_candidate(candidate, regime, sr, metrics, now_et=morning_et)


def test_unknown_earnings_pass_is_marked():
    result = _qualify(candidate_kwargs={"has_earnings_soon": None})

    assert GATE_EARNINGS in result.gates_passed  # outcome unchanged
    skipped = dict(result.gates_skipped)
    assert GATE_EARNINGS in skipped


def test_missing_metrics_extension_pass_is_marked():
    result = _qualify(dm=None)

    assert GATE_EXTENSION in result.gates_passed  # outcome unchanged
    skipped = dict(result.gates_skipped)
    assert GATE_EXTENSION in skipped


def test_full_data_pass_has_no_markers():
    result = _qualify(candidate_kwargs={"has_earnings_soon": False})

    assert result.gates_skipped == ()


# ---------------------------------------------------------------------------
# R3 — report visibility
# ---------------------------------------------------------------------------

def test_report_renders_gate_skipped_line():
    # metrics present so the setup QUALIFIES; earnings unknown so the
    # EARNINGS fail-open marker rides a rendered A+ setup.
    qual_result = _qualify(candidate_kwargs={"has_earnings_soon": None})
    assert qual_result.qualified, "fixture must qualify for the TRADE render"
    summary = QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[qual_result],
        watchlist=[],
        excluded={},
        symbols_evaluated=1,
        symbols_qualified=1,
        symbols_watchlist=0,
        symbols_excluded=0,
    )
    from cuttingboard.chain_validation import ChainValidationResult, VALIDATED
    report = render_report(
        date_str="2026-07-04",
        run_at_utc=_NOW,
        regime=_contract_regime(),
        validation_summary=_val_summary(),
        qualification_summary=summary,
        option_setups=[_option_setup("SPY")],
        outcome=OUTCOME_TRADE,
        chain_results={"SPY": ChainValidationResult(
            symbol="SPY", classification=VALIDATED, reason=None,
            spread_pct=None, open_interest=None, volume=None,
            expiry_used=None, data_source=None,
        )},
    )

    assert "Gate skipped (missing data): EARNINGS" in report
