"""Bounded SPY STATE acquisition seam (PRD-289, NS-2E).

Derives the Market Control Card's STATE by calling ``compute_intraday_state``
READ-ONLY on the exact ``spy_session_frame`` object (FRAME A) already fetched
once per run — identity with the frame passed to ``build_spy_observation``,
never a second fetch. The packet-§5 failure boundary lives here and only here:
exactly ``(KeyError, ValueError, TypeError, InsufficientDataError)`` resolve to
typed UNAVAILABLE tokens; the pre-09:45 engine ``None`` resolves in-band to
``pre_computation_window``; every other exception propagates to run level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd

from cuttingboard.intraday_state_engine import (
    Bar,
    InsufficientDataError,
    IntraState,
    compute_intraday_state,
)
from cuttingboard.spy_observation import OBSERVED, PRE_OPEN, STALE, UNAVAILABLE, SpyObservation

VALID_SPY_STATE_UNAVAILABLE_REASONS = frozenset({
    "insufficient_bars", "pre_computation_window", "state_computation_error",
    "non_current_observation", "observation_unavailable",
})

# Shared-observation normalization (STATE only — PERMISSION is outside this
# rule by ratified ruling): non-OBSERVED observations never yield a fresh value.
_OBSERVATION_CASCADE = {
    PRE_OPEN: "non_current_observation",
    STALE: "non_current_observation",
    UNAVAILABLE: "observation_unavailable",
}


@dataclass(frozen=True)
class SpyStateOutcome:
    """Frozen strict-XOR carrier: exactly one of ``state`` (a valued
    ``IntraState``) or ``unavailable_reason`` (a closed-vocabulary token).
    Pure validation, no derived-default backfill."""

    state: Optional[IntraState] = None
    unavailable_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if (self.state is None) == (self.unavailable_reason is None):
            raise ValueError(
                "SpyStateOutcome requires exactly one of state / unavailable_reason; "
                f"got state={self.state!r}, unavailable_reason={self.unavailable_reason!r}"
            )
        if self.state is not None and not isinstance(self.state, IntraState):
            raise ValueError(f"SpyStateOutcome.state must be an IntraState; got {type(self.state).__name__}")
        if (
            self.unavailable_reason is not None
            and self.unavailable_reason not in VALID_SPY_STATE_UNAVAILABLE_REASONS
        ):
            raise ValueError(f"Unknown SPY STATE unavailable reason: {self.unavailable_reason!r}")


def _frame_to_bars(session_frame: pd.DataFrame) -> list[Bar]:
    """Owned FRAME A → ``list[Bar]`` adapter. Read-only over the frame; a
    missing OHLCV column raises ``KeyError`` into the seam boundary."""
    opens = session_frame["Open"]
    highs = session_frame["High"]
    lows = session_frame["Low"]
    closes = session_frame["Close"]
    volumes = session_frame["Volume"]
    return [
        Bar(
            timestamp=ts.to_pydatetime(),
            open=float(opens.iloc[i]),
            high=float(highs.iloc[i]),
            low=float(lows.iloc[i]),
            close=float(closes.iloc[i]),
            volume=int(volumes.iloc[i]),
        )
        for i, ts in enumerate(session_frame.index)
    ]


def build_spy_state_outcome(
    *,
    observation: SpyObservation,
    session_frame: Optional[pd.DataFrame],
    previous_close: Optional[float],
) -> SpyStateOutcome:
    """Build the typed STATE outcome from the exact FRAME A object.

    ``previous_close`` may be ``None`` (weaker gap-typing in the engine) — it
    never makes STATE unavailable and never triggers a fetch.
    """
    if observation.state != OBSERVED:
        return SpyStateOutcome(unavailable_reason=_OBSERVATION_CASCADE[observation.state])
    try:
        bars = _frame_to_bars(session_frame)
        intra_state = compute_intraday_state("SPY", bars, previous_close=previous_close)
    except InsufficientDataError:
        return SpyStateOutcome(unavailable_reason="insufficient_bars")
    except (KeyError, ValueError, TypeError):
        return SpyStateOutcome(unavailable_reason="state_computation_error")
    if intra_state is None:
        return SpyStateOutcome(unavailable_reason="pre_computation_window")
    return SpyStateOutcome(state=intra_state)
