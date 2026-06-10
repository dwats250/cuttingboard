"""PRD-175 — Historical regime scoreboard aggregation sidecar.

Deterministic fixtures only: synthetic audit.jsonl spanning consecutive dates
plus an injected SPY close series. No parquet, no network, no live run.
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

from cuttingboard.delivery import regime_history
from cuttingboard.delivery.regime_history import aggregate


def _pipeline_record(*, date: str, run_at_utc: str, regime: str, posture: str,
                     confidence: float, net_score: int, vix_level: float) -> dict:
    """Minimal pipeline-shaped audit record (has outcome + run_at_utc, no event)."""
    return {
        "run_at_utc": run_at_utc,
        "date": date,
        "outcome": "NO_TRADE",
        "regime": regime,
        "posture": posture,
        "confidence": confidence,
        "net_score": net_score,
        "vix_level": vix_level,
    }


def _notification_record(*, date: str) -> dict:
    return {"event": "notification", "timestamp": f"{date}T15:00:00+00:00",
            "transport": "telegram", "status": "success"}


def _write_audit(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in records),
        encoding="utf-8",
    )


def _read_history(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


# --- R1 + R2 — one record per date, notifications excluded ---------------

def test_prd175_one_record_per_date_excludes_notifications(tmp_path) -> None:
    audit = tmp_path / "audit.jsonl"
    history = tmp_path / "regime_history.jsonl"
    _write_audit(audit, [
        _pipeline_record(date="2026-06-08", run_at_utc="2026-06-08T13:00:00+00:00",
                         regime="NEUTRAL", posture="STAY_FLAT", confidence=0.4,
                         net_score=0, vix_level=17.0),
        _pipeline_record(date="2026-06-08", run_at_utc="2026-06-08T20:00:00+00:00",
                         regime="NEUTRAL", posture="STAY_FLAT", confidence=0.5,
                         net_score=1, vix_level=16.5),
        _notification_record(date="2026-06-08"),
        _pipeline_record(date="2026-06-09", run_at_utc="2026-06-09T13:00:00+00:00",
                         regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.7,
                         net_score=3, vix_level=15.0),
    ])

    aggregate(audit_path=str(audit), history_path=str(history), spy_closes=[])
    records = _read_history(history)

    dates = [r["date"] for r in records]
    assert dates == ["2026-06-08", "2026-06-09"], f"one record per date in order, got {dates}"
    d0608 = next(r for r in records if r["date"] == "2026-06-08")
    assert d0608["run_count"] == 2, "notification record must not be counted"
    for key in ("date", "regime", "posture", "confidence", "net_score",
                "vix_level", "first_run_at_utc", "last_run_at_utc", "run_count"):
        assert key in d0608, f"summary missing required field {key!r}"
    # R1: no audit field that does not exist (vote breakdown)
    for forbidden in ("risk_on_votes", "risk_off_votes", "neutral_votes", "total_votes"):
        assert forbidden not in d0608, f"summary must not invent field {forbidden!r}"


# --- representativeness — last run of the day wins -----------------------

def test_prd175_summary_uses_last_run_of_day(tmp_path) -> None:
    audit = tmp_path / "audit.jsonl"
    history = tmp_path / "regime_history.jsonl"
    _write_audit(audit, [
        _pipeline_record(date="2026-06-09", run_at_utc="2026-06-09T13:00:00+00:00",
                         regime="RISK_OFF", posture="DEFENSIVE_SHORT", confidence=0.6,
                         net_score=-2, vix_level=22.0),
        _pipeline_record(date="2026-06-09", run_at_utc="2026-06-09T20:00:00+00:00",
                         regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.8,
                         net_score=3, vix_level=15.0),
    ])
    aggregate(audit_path=str(audit), history_path=str(history), spy_closes=[])
    rec = _read_history(history)[0]
    assert rec["regime"] == "RISK_ON", "representative call is the latest run of the day"
    assert rec["posture"] == "CONTROLLED_LONG"
    assert rec["first_run_at_utc"] == "2026-06-09T13:00:00+00:00"
    assert rec["last_run_at_utc"] == "2026-06-09T20:00:00+00:00"


# --- R4 — prior-day record gains spy_close_change_pct -------------------

def test_prd175_prior_day_gains_spy_change_after_two_days(tmp_path) -> None:
    audit = tmp_path / "audit.jsonl"
    history = tmp_path / "regime_history.jsonl"
    _write_audit(audit, [
        _pipeline_record(date="2026-06-08", run_at_utc="2026-06-08T20:00:00+00:00",
                         regime="NEUTRAL", posture="STAY_FLAT", confidence=0.4,
                         net_score=0, vix_level=17.0),
        _pipeline_record(date="2026-06-09", run_at_utc="2026-06-09T20:00:00+00:00",
                         regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.7,
                         net_score=3, vix_level=15.0),
    ])
    # SPY closes for both trading days; 2026-06-09 is the next session after 06-08.
    spy = [("2026-06-08", 100.0), ("2026-06-09", 102.0)]
    aggregate(audit_path=str(audit), history_path=str(history), spy_closes=spy)
    records = {r["date"]: r for r in _read_history(history)}

    assert records["2026-06-08"]["spy_close_change_pct"] == 0.02, (
        "prior day's record must carry next-session SPY change (102/100 - 1)"
    )
    assert records["2026-06-09"]["spy_close_change_pct"] is None, (
        "latest date has no next session yet; change is pending (None)"
    )


# --- R3 — idempotent, incl. re-run after outcome attached ---------------

def test_prd175_idempotent_rerun_no_duplicates(tmp_path) -> None:
    audit = tmp_path / "audit.jsonl"
    history = tmp_path / "regime_history.jsonl"
    _write_audit(audit, [
        _pipeline_record(date="2026-06-08", run_at_utc="2026-06-08T20:00:00+00:00",
                         regime="NEUTRAL", posture="STAY_FLAT", confidence=0.4,
                         net_score=0, vix_level=17.0),
        _pipeline_record(date="2026-06-09", run_at_utc="2026-06-09T20:00:00+00:00",
                         regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.7,
                         net_score=3, vix_level=15.0),
    ])

    # First aggregation: only 06-08 close known, so 06-08 is still pending.
    aggregate(audit_path=str(audit), history_path=str(history),
              spy_closes=[("2026-06-08", 100.0)])
    first = _read_history(history)
    assert [r["date"] for r in first] == ["2026-06-08", "2026-06-09"]
    assert first[0]["spy_close_change_pct"] is None, "06-08 pending until next close exists"

    # Next day: 06-09 close arrives. Re-run replaces 06-08 in place with its
    # now-known outcome; no duplicate date appears.
    aggregate(audit_path=str(audit), history_path=str(history),
              spy_closes=[("2026-06-08", 100.0), ("2026-06-09", 102.0)])
    second = _read_history(history)
    assert [r["date"] for r in second] == ["2026-06-08", "2026-06-09"], "no duplicate dates"
    assert second[0]["spy_close_change_pct"] == 0.02, "06-08 outcome attached on re-run"

    # Third run, identical inputs: byte-for-byte stable (true idempotency).
    aggregate(audit_path=str(audit), history_path=str(history),
              spy_closes=[("2026-06-08", 100.0), ("2026-06-09", 102.0)])
    third = _read_history(history)
    assert third == second, "re-running with identical inputs must not change the file"


# --- R5 — sidecar isolation ---------------------------------------------

def test_prd175_does_not_mutate_audit(tmp_path) -> None:
    audit = tmp_path / "audit.jsonl"
    history = tmp_path / "regime_history.jsonl"
    records = [
        _pipeline_record(date="2026-06-09", run_at_utc="2026-06-09T20:00:00+00:00",
                         regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.7,
                         net_score=3, vix_level=15.0),
    ]
    _write_audit(audit, records)
    before = audit.read_bytes()
    aggregate(audit_path=str(audit), history_path=str(history), spy_closes=[])
    assert audit.read_bytes() == before, "aggregator must never write back to audit.jsonl"


def test_prd175_module_imports_no_decision_layers() -> None:
    """R5: the sidecar must not import runtime/contract/payload/output."""
    src = inspect.getsource(regime_history)
    for forbidden in ("runtime", "contract", "payload", "output"):
        assert f"import {forbidden}" not in src and f"from cuttingboard.{forbidden}" not in src, (
            f"regime_history must not couple to cuttingboard.{forbidden}"
        )


def test_prd175_writes_empty_history_when_no_pipeline_records(tmp_path) -> None:
    """The workflow git-adds logs/regime_history.jsonl unconditionally, so the
    aggregator must always create the file even with nothing to aggregate."""
    audit = tmp_path / "audit.jsonl"
    history = tmp_path / "regime_history.jsonl"
    _write_audit(audit, [_notification_record(date="2026-06-09")])
    aggregate(audit_path=str(audit), history_path=str(history), spy_closes=[])
    assert history.exists(), "history file must be created even with zero pipeline records"
    assert _read_history(history) == []
