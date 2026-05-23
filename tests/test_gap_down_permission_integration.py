"""
Integration tests for gap-down short permission gate.

Prevents regression of the A-1 wiring bug: ensures that the intraday
permission gate is correctly wired into _apply_intraday_short_permission
for all observable failure modes.

Coverage-gap tests (PRD-151 §TEST_COVERAGE):
  test_case5_* — R9: fixture-mode skip at runtime.py:805
  test_case6_* — R7 multi-call-site invariant (identical semantics at
                 runtime.py:489, 518, 805)
  test_case7_* — Stricter fixture-mode invariant: gate skipped at ALL three
                 call sites (489, 518, 805), not just 805
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import pytz

from cuttingboard.notifications import NOTIFY_POST_ORB
from cuttingboard.normalization import NormalizedQuote
from cuttingboard.qualification import TradeCandidate
from cuttingboard.regime import RegimeState
from cuttingboard.runtime import (
    _apply_intraday_short_permission,
    _execute_notify_run,
    MODE_FIXTURE,
)

ET = pytz.timezone("US/Eastern")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _et_ts(hour: int, minute: int) -> datetime:
    return ET.localize(datetime(2026, 4, 18, hour, minute, 0))


def _make_bar_df(rows: list[tuple]) -> pd.DataFrame:
    """rows: (hour, minute, open, high, low, close, volume)"""
    index, opens, highs, lows, closes, volumes = [], [], [], [], [], []
    for h, m, o, hi, lo, c, v in rows:
        index.append(_et_ts(h, m))
        opens.append(o)
        highs.append(hi)
        lows.append(lo)
        closes.append(c)
        volumes.append(v)
    return pd.DataFrame(
        {"Open": opens, "High": highs, "Low": lows, "Close": closes, "Volume": volumes},
        index=index,
    )


# ORB_HIGH=455.0, ORB_LOW=453.0
_ORB_ROWS = [
    (9, 30, 455.0, 455.0, 453.0, 454.0, 2_000_000),
    (9, 31, 454.0, 454.5, 453.0, 453.5, 2_000_000),
    (9, 32, 453.5, 454.0, 453.0, 453.5, 2_000_000),
    (9, 33, 453.5, 454.0, 453.0, 453.0, 2_000_000),
    (9, 34, 453.0, 453.5, 453.0, 453.0, 2_000_000),
]

# 09:36–09:44: post-ORB, close=453.5 (inside ORB range, above ORB_LOW)
_NOISE_ROWS = [
    (9, m, 453.2, 453.5, 453.0, 453.5, 1_000_000)
    for m in range(36, 45)
]

# prev_close ≈ 460.0 → gap_pct ≈ -1.1% → gap_type="DOWN"
_GAP_DOWN_QUOTE = NormalizedQuote(
    symbol="TSLA",
    price=453.0,
    pct_change_decimal=-0.01522,
    volume=30_000_000.0,
    fetched_at_utc=datetime(2026, 4, 18, 14, 0, 0, tzinfo=timezone.utc),
    source="yfinance",
    units="USD",
    age_seconds=60.0,
)

_SHORT_CANDIDATE = TradeCandidate(
    symbol="TSLA",
    direction="SHORT",
    entry_price=452.8,
    stop_price=455.5,
    target_price=445.0,
    spread_width=3.0,
)


# ---------------------------------------------------------------------------
# CASE 1 — Gap-down, no permission
# ---------------------------------------------------------------------------

def test_case1_gap_down_no_permission_blocks_short():
    """1 close below ORB_LOW → acceptance=0 → SHORT suppressed."""
    rows = _ORB_ROWS + _NOISE_ROWS + [
        (9, 45, 452.9, 452.9, 452.5, 452.8, 2_500_000),
    ]
    df = _make_bar_df(rows)

    with patch("cuttingboard.runtime.fetch_intraday_bars", return_value=df):
        filtered, context = _apply_intraday_short_permission(
            {"TSLA": _SHORT_CANDIDATE}, {"TSLA": _GAP_DOWN_QUOTE}
        )

    assert "TSLA" not in filtered, (
        "R7: gap-down SHORT with no permission evidence must be popped from"
        " the filtered dict before qualification (not flagged downstream)"
    )
    assert context["TSLA"]["intraday_state_available"] is True
    assert context["TSLA"]["downside_permission"] is False


# ---------------------------------------------------------------------------
# CASE 2 — Gap-down, permission granted
# ---------------------------------------------------------------------------

def test_case2_gap_down_acceptance_allows_short():
    """2 contiguous closes below ORB_LOW → acceptance confirmed → SHORT allowed."""
    rows = _ORB_ROWS + _NOISE_ROWS + [
        (9, 45, 452.9, 452.9, 452.5, 452.8, 2_500_000),
        (9, 46, 452.9, 452.9, 452.5, 452.8, 2_500_000),
    ]
    df = _make_bar_df(rows)

    with patch("cuttingboard.runtime.fetch_intraday_bars", return_value=df):
        filtered, context = _apply_intraday_short_permission(
            {"TSLA": _SHORT_CANDIDATE}, {"TSLA": _GAP_DOWN_QUOTE}
        )

    assert "TSLA" in filtered
    assert context["TSLA"]["intraday_state_available"] is True
    assert context["TSLA"]["downside_permission"] is True


# ---------------------------------------------------------------------------
# CASE 3 — Intraday state unavailable (fail-open)
# ---------------------------------------------------------------------------

def test_case3_state_unavailable_fails_open():
    """When compute_intraday_state raises, SHORT is kept (fail-open)."""
    rows = _ORB_ROWS + _NOISE_ROWS + [
        (9, 45, 452.9, 452.9, 452.5, 452.8, 2_500_000),
    ]
    df = _make_bar_df(rows)

    with patch("cuttingboard.runtime.fetch_intraday_bars", return_value=df), \
         patch("cuttingboard.runtime.compute_intraday_state",
               side_effect=Exception("simulated failure")):
        filtered, context = _apply_intraday_short_permission(
            {"TSLA": _SHORT_CANDIDATE}, {"TSLA": _GAP_DOWN_QUOTE}
        )

    assert "TSLA" in filtered
    assert context["TSLA"]["intraday_state_available"] is False
    assert "downside_permission" not in context["TSLA"]


# ---------------------------------------------------------------------------
# CASE 4 — Sparse bars (non-contiguous)
# ---------------------------------------------------------------------------

def test_case4_sparse_bars_blocks_short():
    """3-minute gap between last 2 bars → contiguity violated → acceptance=0 → SHORT blocked."""
    rows = _ORB_ROWS + _NOISE_ROWS + [
        (9, 45, 452.9, 452.9, 452.5, 452.8, 2_500_000),
        (9, 48, 452.9, 452.9, 452.5, 452.8, 2_500_000),  # 3-min gap > 2-min tolerance
    ]
    df = _make_bar_df(rows)

    with patch("cuttingboard.runtime.fetch_intraday_bars", return_value=df):
        filtered, context = _apply_intraday_short_permission(
            {"TSLA": _SHORT_CANDIDATE}, {"TSLA": _GAP_DOWN_QUOTE}
        )

    assert "TSLA" not in filtered
    assert context["TSLA"]["intraday_state_available"] is True
    assert context["TSLA"]["downside_permission"] is False


# ---------------------------------------------------------------------------
# PRD-151 §TEST_COVERAGE GAP — CASE 5: R9 fixture-mode skip
# ---------------------------------------------------------------------------
# PRD-151 R9: "At the main daily call site (runtime.py:805), the gate is
# invoked only when mode != MODE_FIXTURE. Fixture-mode runs bypass intraday
# filtering entirely."
#
# The gap: this bypass is untested — there is no test asserting that
# _apply_intraday_short_permission is NOT called when mode == MODE_FIXTURE.
# ---------------------------------------------------------------------------

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "2026-04-12.json"


def test_case5_fixture_mode_skips_intraday_short_permission_gate(monkeypatch, tmp_path):
    """R9 — _apply_intraday_short_permission must NOT be called during fixture mode.

    Encodes PRD-151 R9: the gate at runtime.py:804 guards the call with
    `if mode != MODE_FIXTURE`. Fixture-mode runs use canned data that does
    not represent real intraday bars, so the gate must be bypassed entirely.
    The test fails if the implementation calls the gate function during a
    fixture pipeline run.
    """
    import cuttingboard.runtime as _rt

    gate_mock = MagicMock(wraps=_rt._apply_intraday_short_permission)
    monkeypatch.setattr(_rt, "_apply_intraday_short_permission", gate_mock)

    # Redirect all artifact writes so the test is side-effect free
    logs_dir = tmp_path / "logs"
    reports_dir = tmp_path / "reports"
    monkeypatch.setattr(_rt, "LOGS_DIR", logs_dir)
    monkeypatch.setattr(_rt, "REPORTS_DIR", reports_dir)
    monkeypatch.setattr(_rt, "LATEST_RUN_PATH", logs_dir / "latest_run.json")
    monkeypatch.setattr(_rt, "MARKET_MAP_PATH", logs_dir / "market_map.json")
    monkeypatch.setattr(_rt, "LATEST_CONTRACT_PATH", str(logs_dir / "latest_contract.json"))

    import cuttingboard.audit as _audit
    monkeypatch.setattr(_audit, "AUDIT_LOG_PATH", str(logs_dir / "audit.jsonl"))

    from datetime import date
    result = _rt.execute_run(
        mode=MODE_FIXTURE,
        run_date=date.fromisoformat("2026-04-12"),
        fixture_file=_FIXTURE_PATH,
    )

    assert result["status"] == "SUCCESS", (
        "Prerequisite: fixture run must complete successfully for R9 test to be meaningful"
    )
    assert gate_mock.call_count == 0, (
        f"R9 VIOLATION: _apply_intraday_short_permission was called {gate_mock.call_count} "
        f"time(s) during a MODE_FIXTURE run. The gate at runtime.py:804 "
        f"(`if mode != MODE_FIXTURE`) must prevent any call when mode == 'fixture'."
    )


# ---------------------------------------------------------------------------
# PRD-151 §TEST_COVERAGE GAP — CASE 6: R7 multi-call-site invariant
# ---------------------------------------------------------------------------
# PRD-151 R7 + §SCOPE: "_apply_intraday_short_permission pops suppressed
# candidates from the returned dict. [It is called at] runtime.py:489 —
# _QUALIFY_ONLY_MODES branch; runtime.py:518 — _HOURLY_MODES branch;
# runtime.py:805 — main daily/live branch."
#
# The gap: no test asserts that the function produces identical outputs
# (same filter semantics, same context structure) regardless of which of
# the three call sites triggered it. The call sites must treat the function
# identically.
# ---------------------------------------------------------------------------

def test_case6_gate_behavior_is_identical_across_all_three_call_sites():
    """R7 multi-call-site invariant — gate semantics are call-site-independent.

    Encodes PRD-151 R7: _apply_intraday_short_permission must apply the same
    pop-not-flag filtering contract at call sites 489, 518, and 805. Because
    all three call sites invoke the same function with the same signature, the
    invariant is that calling the function three times with identical inputs
    produces three identical (filtered, context) return values.

    This test fails if _apply_intraday_short_permission is not a pure,
    deterministic function with respect to its inputs — i.e., if any
    call-site-specific state leaks into the function or if its return value
    differs across repeated calls with the same arguments.
    """
    rows_blocked = _ORB_ROWS + _NOISE_ROWS + [
        (9, 45, 452.9, 452.9, 452.5, 452.8, 2_500_000),  # 1 close below → no acceptance
    ]
    df = _make_bar_df(rows_blocked)

    results = []
    for _call_site_index in range(3):  # simulates call sites 489, 518, 805
        with patch("cuttingboard.runtime.fetch_intraday_bars", return_value=df):
            filtered, context = _apply_intraday_short_permission(
                {"TSLA": _SHORT_CANDIDATE}, {"TSLA": _GAP_DOWN_QUOTE}
            )
        results.append((filtered, context))

    # All three call sites must produce identical filter outcomes
    filtered_0, context_0 = results[0]
    for i, (filtered_i, context_i) in enumerate(results[1:], start=1):
        assert set(filtered_i.keys()) == set(filtered_0.keys()), (
            f"R7 multi-site VIOLATION: call-site simulation {i} returned different "
            f"filtered keys than call-site 0. "
            f"Expected {set(filtered_0.keys())!r}, got {set(filtered_i.keys())!r}. "
            f"_apply_intraday_short_permission must be stateless across call sites."
        )
        for sym in context_0:
            assert context_i.get(sym, {}).get("downside_permission") == \
                   context_0[sym].get("downside_permission"), (
                f"R7 multi-site VIOLATION: call-site simulation {i} produced a "
                f"different downside_permission decision for {sym!r} than call-site 0. "
                f"The gate must be deterministic regardless of which runtime branch "
                f"(489, 518, or 805) invokes it."
            )


# ---------------------------------------------------------------------------
# AMBIGUITY §1 STRICT FORM — CASE 7: fixture-mode gate skip at ALL call sites
# ---------------------------------------------------------------------------
# Previous analysis of PRD-151 noted this ambiguity:
#   "Call sites 489 and 518 (in _execute_notify_run) have no fixture-mode
#    guard, while site 805 does. PRD-151 does not explain whether 489/518
#    should have one."
#
# This test asserts the STRICTER invariant: the intraday short permission
# gate is skipped in fixture mode regardless of which call site triggers it.
#
# The test INTENTIONALLY FAILS against current code: _execute_notify_run's
# _QUALIFY_ONLY_MODES branch at runtime.py:489 calls
# _apply_intraday_short_permission unconditionally — there is no
# `if mode != MODE_FIXTURE` guard equivalent to the one at line 804.
# ---------------------------------------------------------------------------


def _regime_defensive_short(**overrides) -> RegimeState:
    """Minimal RegimeState with a tradable non-STAY_FLAT posture."""
    from datetime import datetime, timezone
    defaults = dict(
        regime="RISK_OFF",
        posture="DEFENSIVE_SHORT",
        confidence=0.62,
        net_score=-5,
        risk_on_votes=0,
        risk_off_votes=5,
        neutral_votes=3,
        total_votes=8,
        vote_breakdown={},
        vix_level=22.0,
        vix_pct_change=0.02,
        computed_at_utc=datetime(2026, 4, 23, 14, 30, tzinfo=timezone.utc),
    )
    defaults.update(overrides)
    return RegimeState(**defaults)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Stricter invariant not yet implemented: runtime.py:489/518 lack the "
        "`if mode != MODE_FIXTURE` guard present at runtime.py:805. Flip to "
        "passing by adding the guard in a follow-up PRD; strict=True so this "
        "marker fails loudly once the guard lands."
    ),
)
def test_case7_fixture_mode_skips_gate_at_execute_notify_run_call_site(
    monkeypatch, tmp_path
):
    """Stricter invariant — gate must NOT be called from _execute_notify_run when mode is fixture.

    Targets runtime.py:489 (_QUALIFY_ONLY_MODES branch in _execute_notify_run).
    The guard at runtime.py:804 protects call site 805 only. Call site 489 has
    no equivalent guard, so this test fails against current code.

    The rationale from PRD-151 R9 is mode-agnostic: fixture-mode runs use
    canned data that does not represent real intraday bars, making intraday
    filtering semantically undefined regardless of which call site triggers it.
    The test encodes the position that the guard *should* be present at 489/518
    as well as 805.

    EXPECTED FAILURE: gate_mock.call_count will be 1 (not 0) because line 489
    calls _apply_intraday_short_permission without a mode guard.
    """
    import cuttingboard.runtime as _rt
    from cuttingboard.validation import ValidationSummary

    gate_mock = MagicMock(wraps=_rt._apply_intraday_short_permission)
    monkeypatch.setattr(_rt, "_apply_intraday_short_permission", gate_mock)

    _setup_notify_run_artifacts(monkeypatch, tmp_path, _rt)

    validation = MagicMock(spec=ValidationSummary)
    validation.system_halted = False
    validation.halt_reason = None
    validation.valid_quotes = {}
    validation.symbols_validated = 0
    validation.symbols_attempted = 0

    # Patch the full data-fetch pipeline so _execute_notify_run reaches
    # the generate_candidates call site (line 487-489) without real network calls.
    # NOTIFY_POST_ORB is in _QUALIFY_ONLY_MODES, so line 489 is the target.
    with (
        patch("cuttingboard.runtime.fetch_all", return_value={}),
        patch("cuttingboard.runtime.normalize_all", return_value={}),
        patch("cuttingboard.runtime.extract_fetch_failures", return_value={}),
        patch("cuttingboard.runtime.validate_quotes", return_value=validation),
        patch("cuttingboard.runtime.compute_regime",
              return_value=_regime_defensive_short()),
        patch("cuttingboard.runtime.compute_all_derived", return_value={}),
        patch("cuttingboard.runtime.resolve_sector_router",
              return_value=MagicMock()),
        patch("cuttingboard.runtime.classify_all_structure", return_value={}),
        patch("cuttingboard.runtime.generate_candidates", return_value={}),
        patch("cuttingboard.runtime.send_notification", return_value=True),
    ):
        _execute_notify_run(
            mode=MODE_FIXTURE,
            run_date=__import__("datetime").date(2026, 4, 23),
            notify_mode=NOTIFY_POST_ORB,
        )

    assert gate_mock.call_count == 0, (
        f"CASE 7 FAILURE — runtime.py:489 called _apply_intraday_short_permission "
        f"{gate_mock.call_count} time(s) during a MODE_FIXTURE "
        f"_execute_notify_run(notify_mode=NOTIFY_POST_ORB) run. "
        f"Call site 489 has no `if mode != MODE_FIXTURE` guard (unlike site 805). "
        f"The stricter fixture-mode skip invariant requires the guard at all "
        f"three call sites (489, 518, 805), not just 805."
    )


def _setup_notify_run_artifacts(monkeypatch, tmp_path, rt_module) -> None:
    """Redirect _execute_notify_run artifact writes to tmp_path."""
    import cuttingboard.audit as _audit
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(rt_module, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(rt_module, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(
        rt_module, "LATEST_HOURLY_RUN_PATH",
        tmp_path / "logs" / "latest_hourly_run.json"
    )
    monkeypatch.setattr(
        rt_module, "LATEST_HOURLY_CONTRACT_PATH",
        tmp_path / "logs" / "latest_hourly_contract.json"
    )
    monkeypatch.setattr(
        rt_module, "LATEST_HOURLY_PAYLOAD_PATH",
        tmp_path / "logs" / "latest_hourly_payload.json"
    )
    monkeypatch.setattr(
        rt_module, "HOURLY_REPORT_PATH",
        tmp_path / "reports" / "output" / "hourly_report.html"
    )
    monkeypatch.setattr(
        rt_module, "MARKET_MAP_PATH",
        tmp_path / "logs" / "market_map.json"
    )
    monkeypatch.setattr(
        _audit, "AUDIT_LOG_PATH",
        str(tmp_path / "logs" / "audit.jsonl")
    )
