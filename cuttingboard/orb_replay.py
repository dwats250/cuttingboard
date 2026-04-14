"""Fixture-driven ORB 0DTE observational replay harness.

Purpose:
- Load serialized ORB session fixtures.
- Run curated or recorded sessions through the read-only observation path for
  deterministic review.

Inputs:
- `run_orb_observational_replay(sessions)` accepts a mapping of session label
  to ORB `SessionInput`.
- `load_orb_session_fixture(path)` accepts a JSON fixture path containing one
  serialized ORB session.

Outputs:
- Per-session `ORBReplayOutput` objects with the raw observation payload and a
  compact report block for review.

Constraints:
- Fixture-driven review only.
- Expects serialized ORB session fixtures or in-memory `SessionInput` values.
- Does not own scheduling, artifact persistence, or runtime control.

What this module does not do:
- It does not fetch live data.
- It does not write ledgers, status records, or runtime summaries.
- It does not alter the main runtime or ORB rule logic.

Read-only status:
- Read-only. It loads fixtures, builds observation output, and returns replay
  results to callers.
- This module is read-only and does not execute trades.

Feature-flag usage:
- Runtime shadow mode can be invoked with `--observe-orb-0dte` and
  `--orb-session-file <path>`; the runtime loader delegates fixture parsing to
  this module and emits observation output only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime

from cuttingboard.orb_0dte import Candle, OptionSnapshot, SessionInput
from cuttingboard.orb_observation import build_orb_observation, format_orb_observation_lines


@dataclass(frozen=True)
class ORBReplayOutput:
    session_name: str
    observation: dict[str, object]
    report_block: str


def load_orb_session_fixture(path: str) -> SessionInput:
    payload = json.loads(open(path, "r", encoding="utf-8").read())
    return SessionInput(
        session_date=date.fromisoformat(payload["session_date"]),
        candles={
            symbol: [
                Candle(
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    open=float(item["open"]),
                    high=float(item["high"]),
                    low=float(item["low"]),
                    close=float(item["close"]),
                    volume=float(item["volume"]),
                    headline_shock=bool(item.get("headline_shock", False)),
                )
                for item in candles
            ]
            for symbol, candles in payload["candles"].items()
        },
        option_snapshots={
            symbol: [
                OptionSnapshot(
                    contract_id=item["contract_id"],
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    expiry=date.fromisoformat(item["expiry"]),
                    option_type=item["option_type"],
                    strike=float(item["strike"]),
                    delta=float(item["delta"]),
                    premium=float(item["premium"]),
                    session_open_premium=float(item["session_open_premium"]),
                    underlying_symbol=item["underlying_symbol"],
                )
                for item in snapshots
            ]
            for symbol, snapshots in payload["option_snapshots"].items()
        },
        scheduled_high_impact_day=bool(payload.get("scheduled_high_impact_day", False)),
        normal_allocation=float(payload.get("normal_allocation", 1.0)),
    )


def run_orb_observational_replay(sessions: dict[str, SessionInput]) -> dict[str, ORBReplayOutput]:
    outputs: dict[str, ORBReplayOutput] = {}
    for session_name, session in sessions.items():
        observation = build_orb_observation(session)
        outputs[session_name] = ORBReplayOutput(
            session_name=session_name,
            observation=observation,
            report_block="\n".join(format_orb_observation_lines(observation)).rstrip(),
        )
    return outputs
