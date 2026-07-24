"""PRD-267 — the daily alert's Reason line keeps the vote-coverage clause.

output.py::_alert_reason used to end in a bare ``[:80]``. The vote-coverage
clause qualification.py::_check_regime_gates appends to ``stay_flat_reason``
sits at the END of that string, so the slice dropped exactly the part that
explains why the system stood down.

R3 (Dustin, 2026-07-24) governs how R1 is tested: the fixture must be built
by CALLING ``_check_regime_gates``, never from a literal. The regex in
output.py couples the renderer to that function's wording; if the wording
drifts the regex stops matching, ``_fit_reason`` falls back to the plain
slice, and the bug returns silently — R2 specifies that fallback as
byte-identical to today, so nothing else would go red. Anchoring the fixture
to the producer is what turns that silent channel into a failing test.
"""

from datetime import datetime, timezone

import pytest

from cuttingboard import output
from cuttingboard.qualification import _check_regime_gates
from cuttingboard.regime import STAY_FLAT, RegimeState, _VOTE_KEYS


def _regime(*, posture: str = STAY_FLAT, total_votes: int, confidence: float = 0.42):
    """A RegimeState carrying the vote coverage the clause is derived from."""
    return RegimeState(
        regime="CHOP",
        posture=posture,
        confidence=confidence,
        net_score=0,
        risk_on_votes=0,
        risk_off_votes=0,
        neutral_votes=total_votes,
        total_votes=total_votes,
        vote_breakdown={},
        vix_level=None,
        vix_pct_change=None,
        computed_at_utc=datetime(2026, 7, 24, 14, 0, tzinfo=timezone.utc),
    )


def _bounded_reason(cast: int = 5) -> str:
    """R3: the real producer's output, not a literal copied from it."""
    reason = _check_regime_gates(_regime(total_votes=cast))
    assert reason is not None, "STAY_FLAT must produce a regime failure reason"
    return reason


def _contract(reason: str) -> dict:
    return {"system_state": {"stay_flat_reason": reason}}


def _legacy_truncation(reason: str) -> str:
    """Exactly the pre-PRD-267 behavior, as R2 defines it."""
    return str(reason).replace("\n", " ")[:80]


# ---------------------------------------------------------------------------
# R3 — the fixture is anchored to the producer
# ---------------------------------------------------------------------------

def test_r3_fixture_comes_from_the_producer_and_is_actually_bounded():
    reason = _bounded_reason(5)
    # Derived from _check_regime_gates, so a wording change there lands here.
    assert "5/8 votes cast" in reason
    # The premise of the whole PRD: the real string overflows the budget.
    assert len(reason) > 80, f"fixture must exceed the budget, got {len(reason)}"
    # Guard the arithmetic that motivated the fix (97 chars at HEAD).
    assert _legacy_truncation(reason) != reason
    assert "5/8 votes cast" not in _legacy_truncation(reason)


def test_r3_clause_wording_drift_would_break_r1(monkeypatch):
    """If the producer's wording drifts, R1 must fail rather than fall back.

    Simulated by driving _fit_reason with a drifted clause: the coverage
    regex no longer matches, so the result silently reverts to the plain
    slice. That is the failure mode R3 exists to make observable.
    """
    drifted = _bounded_reason(5).replace("votes cast", "votes counted")
    result = output._fit_reason(drifted)
    assert result == drifted[:80]
    assert "5/8 votes counted" not in result


# ---------------------------------------------------------------------------
# R1 — the clause survives truncation
# ---------------------------------------------------------------------------

def test_r1_coverage_clause_survives_truncation():
    reason = _bounded_reason(5)
    result = output._alert_reason(_contract(reason), has_candidates=False)
    assert "5/8 votes cast" in result
    assert len(result) <= 80


@pytest.mark.parametrize("cast", [1, 2, 3, 4, 5, 6, 7])
def test_r1_holds_for_every_bounded_coverage_level(cast):
    reason = _bounded_reason(cast)
    result = output._alert_reason(_contract(reason), has_candidates=False)
    assert f"{cast}/{len(_VOTE_KEYS)} votes cast" in result
    assert len(result) <= 80


def test_r1_reason_line_in_the_rendered_daily_alert():
    """End-to-end: the clause reaches the rendered Reason line, not just the helper."""
    reason = _bounded_reason(5)
    rendered = f"Reason: {output._alert_reason(_contract(reason), has_candidates=False)}"
    assert "5/8 votes cast" in rendered


def test_r1_never_exceeds_budget_when_clause_cannot_fit():
    """A clause too long for the budget must not blow past the limit."""
    absurd = "x" * 200 + " 5/8 votes cast"
    result = output._fit_reason(absurd, limit=10)
    assert len(result) <= 10


def test_r1_head_is_truncated_not_the_clause():
    reason = _bounded_reason(5)
    result = output._alert_reason(_contract(reason), has_candidates=False)
    assert result.endswith("5/8 votes cast")
    assert result.startswith("STAY_FLAT posture")
    assert "... " in result


# ---------------------------------------------------------------------------
# R2 — no regression for anything without a bounded clause
# ---------------------------------------------------------------------------

def test_r2_no_setups_fallback_unchanged():
    result = output._alert_reason({}, has_candidates=False)
    assert result == _legacy_truncation("no setups")
    assert result == "no setups"


def test_r2_full_coverage_reason_unchanged():
    """total_votes == len(_VOTE_KEYS): the producer emits no clause at all."""
    reason = _check_regime_gates(_regime(total_votes=len(_VOTE_KEYS)))
    assert "votes cast" not in reason
    result = output._alert_reason(_contract(reason), has_candidates=False)
    assert result == _legacy_truncation(reason)


def test_r2_zero_votes_takes_the_unchanged_path():
    """0 votes is degenerate — no clause is emitted, so nothing is protected."""
    reason = _check_regime_gates(_regime(total_votes=0))
    assert "votes cast" not in reason
    result = output._alert_reason(_contract(reason), has_candidates=False)
    assert result == _legacy_truncation(reason)


@pytest.mark.parametrize(
    "reason",
    [
        "short reason",
        "no setups",
        "a" * 200,
        "regime unavailable; data incomplete for the session " + "b" * 120,
        "8/8 votes cast but padded out well past the budget " + "c" * 80,
        "0/8 votes cast but padded out well past the budget " + "d" * 80,
    ],
)
def test_r2_non_bounded_reasons_are_byte_identical_to_legacy(reason):
    result = output._alert_reason(_contract(reason), has_candidates=False)
    assert result == _legacy_truncation(reason)


def test_r2_newlines_still_flattened():
    reason = "line one\nline two"
    result = output._alert_reason(_contract(reason), has_candidates=False)
    assert "\n" not in result
    assert result == _legacy_truncation(reason)


def test_r2_has_candidates_short_circuit_unchanged():
    assert output._alert_reason({}, has_candidates=True) == "candidates gated"


def test_r2_short_bounded_reason_passes_through_untouched():
    """Under the budget, even a clause-bearing reason is returned as-is."""
    short = "CHOP; 5/8 votes cast"
    assert len(short) <= 80
    result = output._alert_reason(_contract(short), has_candidates=False)
    assert result == short
