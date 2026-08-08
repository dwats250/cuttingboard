"""PRD-289 — SPY STATE acquisition seam (NS-2E).

Unit surface of the M1–M10 / M13 / M14 matrix rows: the XOR carrier, the
exact packet-§5 failure boundary, the shared-observation cascade, and the
same-frame derivation. The pipeline halves of M1/M2/M14 live in
test_runtime_decision.py.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cuttingboard import spy_state as spy_state_module
from cuttingboard.spy_observation import build_spy_observation
from cuttingboard.spy_state import (
    VALID_SPY_STATE_UNAVAILABLE_REASONS,
    SpyStateOutcome,
    build_spy_state_outcome,
)
from tests.test_spy_observation import _utc_frame


# 2026-04-28 is EDT: 09:30 ET == 13:30 UTC. 18 bars 09:30–09:47 ET covers the
# ORB window (>=5 bars) and reaches past the 09:45 noise end.
def _session_frame(n_bars: int = 18, start_utc: str = "2026-04-28 13:30"):
    return _utc_frame(
        start_utc,
        highs=[101.0 + i for i in range(n_bars)],
        lows=[99.0 + i for i in range(n_bars)],
        closes=[100.0 + i for i in range(n_bars)],
        vols=[1000] * n_bars,
    )


def _observed(frame):
    """OBSERVED observation for ``frame`` (run 30 s after its last bar)."""
    run_at = frame.index[-1].to_pydatetime().replace(second=30)
    obs = build_spy_observation(run_at_utc=run_at, session_frame=frame, orb=None, halted=False)
    assert obs.state == "OBSERVED"
    return obs


# --- M9: strict XOR carrier ---
def test_m9_xor_rejects_both_and_neither():
    frame = _session_frame()
    valued = build_spy_state_outcome(
        observation=_observed(frame), session_frame=frame, previous_close=99.0
    )
    assert valued.state is not None
    with pytest.raises(ValueError):
        SpyStateOutcome(state=valued.state, unavailable_reason="insufficient_bars")
    with pytest.raises(ValueError):
        SpyStateOutcome(state=None, unavailable_reason=None)


# --- M10 (carrier half): closed vocabulary enforced at construction ---
def test_m10_unknown_reason_token_raises():
    with pytest.raises(ValueError):
        SpyStateOutcome(unavailable_reason="no_truthful_producer")
    with pytest.raises(ValueError):
        SpyStateOutcome(state="EXPANSION_CONFIRMED")  # a str is not an IntraState


# --- M1 (unit half): STATE derives from the exact frame handed to the seam ---
def test_m1_state_derived_from_the_frame_passed():
    frame = _session_frame()
    obs = _observed(frame)
    full = build_spy_state_outcome(observation=obs, session_frame=frame, previous_close=99.0)
    assert full.unavailable_reason is None
    assert full.state.state in {"EXPANSION_CONFIRMED", "FAILED_EXPANSION", "RANGE"}
    # A tail slice (the contiguous-window shape) lacks the ORB formation bars:
    # deriving from any frame but the exact full-session object changes STATE.
    tail = build_spy_state_outcome(
        observation=obs, session_frame=frame.tail(10), previous_close=99.0
    )
    assert tail.unavailable_reason == "insufficient_bars"


# --- M3 (unit half): no frame -> observation UNAVAILABLE -> cascade token ---
def test_m3_none_frame_cascades_to_observation_unavailable():
    run_at = datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc)
    obs = build_spy_observation(run_at_utc=run_at, session_frame=None, orb=None, halted=False)
    assert obs.state == "UNAVAILABLE"
    outcome = build_spy_state_outcome(observation=obs, session_frame=None, previous_close=None)
    assert outcome.unavailable_reason == "observation_unavailable"


# --- M4: adapter data-shape failure (missing OHLCV column) at the seam ---
def test_m4_missing_ohlcv_column_is_state_computation_error():
    frame = _session_frame()
    obs = _observed(frame)
    outcome = build_spy_state_outcome(
        observation=obs, session_frame=frame.drop(columns=["Volume"]), previous_close=99.0
    )
    assert outcome.unavailable_reason == "state_computation_error"


# --- M5: engine ValueError (unordered bars) at the seam ---
def test_m5_unordered_bars_value_error_is_typed_unavailable():
    frame = _session_frame()
    obs = _observed(frame)
    shuffled = frame.iloc[::-1]
    outcome = build_spy_state_outcome(observation=obs, session_frame=shuffled, previous_close=99.0)
    assert outcome.unavailable_reason == "state_computation_error"


# --- M6: <5 ORB bars -> InsufficientDataError -> insufficient_bars ---
def test_m6_insufficient_orb_bars():
    # Session starts 09:33 ET: only 2 bars fall in the 09:30-09:35 ORB window.
    frame = _session_frame(n_bars=15, start_utc="2026-04-28 13:33")
    obs = _observed(frame)
    outcome = build_spy_state_outcome(observation=obs, session_frame=frame, previous_close=99.0)
    assert outcome.unavailable_reason == "insufficient_bars"


# --- M7: pre-09:45 engine None -> pre_computation_window, not an error token ---
def test_m7_pre_0945_maps_to_pre_computation_window():
    frame = _session_frame(n_bars=10)  # last bar 09:39 ET
    obs = _observed(frame)
    outcome = build_spy_state_outcome(observation=obs, session_frame=frame, previous_close=99.0)
    assert outcome.unavailable_reason == "pre_computation_window"


# --- M8: programmer errors PROPAGATE — no blanket catch ---
def test_m8_attribute_error_propagates(monkeypatch):
    frame = _session_frame()
    obs = _observed(frame)

    def _boom(symbol, bars, *, previous_close=None):
        raise AttributeError("programmer error must propagate")

    monkeypatch.setattr(spy_state_module, "compute_intraday_state", _boom)
    with pytest.raises(AttributeError):
        build_spy_state_outcome(observation=obs, session_frame=frame, previous_close=99.0)


# --- M13 (seam half): freshness cascade never yields a fresh value ---
def test_m13_non_observed_states_cascade():
    frame = _session_frame()
    run_at = datetime(2026, 4, 29, 14, 0, tzinfo=timezone.utc)  # next day -> STALE
    stale = build_spy_observation(run_at_utc=run_at, session_frame=frame, orb=None, halted=False)
    assert stale.state == "STALE"
    assert (
        build_spy_state_outcome(observation=stale, session_frame=frame, previous_close=99.0)
        .unavailable_reason == "non_current_observation"
    )
    pre = build_spy_observation(
        run_at_utc=datetime(2026, 4, 29, 13, 33, tzinfo=timezone.utc),
        session_frame=frame, orb=None, halted=False,
    )
    assert pre.state == "PRE_OPEN"
    assert (
        build_spy_state_outcome(observation=pre, session_frame=frame, previous_close=99.0)
        .unavailable_reason == "non_current_observation"
    )


# --- M14 (unit half): halt -> observation_unavailable, engine never invoked ---
def test_m14_halt_no_engine_call(monkeypatch):
    run_at = datetime(2026, 4, 28, 14, 0, tzinfo=timezone.utc)
    halted = build_spy_observation(run_at_utc=run_at, session_frame=None, orb=None, halted=True)
    assert halted.reason == "system_halted"

    def _fail(*args, **kwargs):
        raise AssertionError("engine must not be called on halt")

    monkeypatch.setattr(spy_state_module, "compute_intraday_state", _fail)
    outcome = build_spy_state_outcome(observation=halted, session_frame=None, previous_close=None)
    assert outcome.unavailable_reason == "observation_unavailable"


# --- R3 clause: previous_close=None never makes STATE unavailable ---
def test_previous_close_none_still_values_state():
    frame = _session_frame()
    obs = _observed(frame)
    outcome = build_spy_state_outcome(observation=obs, session_frame=frame, previous_close=None)
    assert outcome.unavailable_reason is None
    assert outcome.state is not None


def test_vocabulary_is_exactly_the_packet_set():
    assert VALID_SPY_STATE_UNAVAILABLE_REASONS == {
        "insufficient_bars", "pre_computation_window", "state_computation_error",
        "non_current_observation", "observation_unavailable",
    }
