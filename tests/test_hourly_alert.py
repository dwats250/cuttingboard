"""PRD-012A acceptance tests: hourly alert filtering, R:R format, and alert contract."""

import inspect
import json
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from cuttingboard.notifications import NOTIFY_HOURLY, format_hourly_notification
from cuttingboard.notifications.formatter import ALERT_CONTEXT_NOTIFY, AlertEvent, format_ntfy_alert
from cuttingboard.qualification import QualificationResult, QualificationSummary, TradeCandidate
from cuttingboard.regime import RegimeState
from cuttingboard.runtime import (
    MODE_LIVE,
    SUMMARY_STATUS_FAIL,
    SUMMARY_STATUS_SUCCESS,
    _build_hourly_candidate_lines,
    _execute_notify_run,
    _hourly_rr,
)
from cuttingboard.sector_router import SectorRouterState
from cuttingboard.validation import ValidationSummary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _regime(**kwargs) -> RegimeState:
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
    defaults.update(kwargs)
    return RegimeState(**defaults)


def _validation(*, halted: bool = False) -> ValidationSummary:
    vs = MagicMock(spec=ValidationSummary)
    vs.system_halted = halted
    vs.halt_reason = "test halt" if halted else None
    vs.valid_quotes = {}
    vs.symbols_validated = 0
    vs.symbols_attempted = 0
    return vs


def _qual(symbols: list[str], direction: str = "SHORT") -> QualificationSummary:
    trades = [
        QualificationResult(
            symbol=s,
            qualified=True,
            watchlist=False,
            direction=direction,
            gates_passed=[],
            gates_failed=[],
            hard_failure=None,
            watchlist_reason=None,
            max_contracts=2,
            dollar_risk=150.0,
        )
        for s in symbols
    ]
    return QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=trades,
        watchlist=[],
        excluded={},
        symbols_evaluated=len(symbols),
        symbols_qualified=len(symbols),
        symbols_watchlist=0,
        symbols_excluded=0,
    )


def _candidate(symbol: str, entry: float = 100.0, stop: float = 97.0, target: float = 106.0) -> TradeCandidate:
    return TradeCandidate(
        symbol=symbol,
        direction="SHORT",
        entry_price=entry,
        stop_price=stop,
        target_price=target,
        spread_width=1.0,
    )


def _structure(structure: str = "PULLBACK") -> MagicMock:
    sr = MagicMock()
    sr.structure = structure
    return sr


def _router_state() -> SectorRouterState:
    return SectorRouterState(
        mode="MIXED",
        energy_score=0.0,
        index_score=0.0,
        computed_at_utc=datetime(2026, 4, 23, 14, 30, tzinfo=timezone.utc),
        session_date="2026-04-23",
    )


def _hourly_event(regime=None, qual=None, candidate_lines=(), halted=False) -> AlertEvent:
    val = _validation(halted=halted)
    return AlertEvent(
        alert_context=ALERT_CONTEXT_NOTIFY,
        notify_mode=NOTIFY_HOURLY,
        outcome="NO_TRADE",
        asof_utc=datetime(2026, 4, 23, 14, 30, tzinfo=timezone.utc),
        regime=regime or _regime(),
        validation_summary=val,
        qualification_summary=qual,
        candidate_lines=candidate_lines,
    )


# ---------------------------------------------------------------------------
# R:R computation
# ---------------------------------------------------------------------------

def test_hourly_rr_basic():
    c = _candidate("NVDA", entry=100.0, stop=97.0, target=106.0)
    assert abs(_hourly_rr(c) - 2.0) < 0.01


def test_hourly_rr_zero_risk_returns_zero():
    c = _candidate("NVDA", entry=100.0, stop=100.0, target=106.0)
    assert _hourly_rr(c) == 0.0


def test_hourly_rr_three_to_one():
    # risk=4, reward=12 => 3.0
    c = _candidate("META", entry=200.0, stop=196.0, target=212.0)
    assert abs(_hourly_rr(c) - 3.0) < 0.01


# ---------------------------------------------------------------------------
# Tradable symbol filtering
# ---------------------------------------------------------------------------

def test_candidate_lines_excludes_vix():
    qual = _qual(["^VIX", "NVDA", "META"])
    structure = {s: _structure() for s in ["^VIX", "NVDA", "META"]}
    candidates = {s: _candidate(s) for s in ["^VIX", "NVDA", "META"]}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates)
    symbols = [line.split(" | ")[0] for line in lines]

    assert "^VIX" not in symbols
    assert "NVDA" in symbols
    assert "META" in symbols


def test_candidate_lines_excludes_all_macro_drivers():
    macro = ["^VIX", "^TNX", "DX-Y.NYB", "BTC-USD"]
    tradable = ["NVDA", "META"]
    all_symbols = macro + tradable
    qual = _qual(all_symbols)
    structure = {s: _structure() for s in all_symbols}
    candidates = {s: _candidate(s) for s in all_symbols}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates, limit=len(all_symbols))
    symbols = [line.split(" | ")[0] for line in lines]

    for m in macro:
        assert m not in symbols, f"{m} must be excluded"
    for t in tradable:
        assert t in symbols, f"{t} must be included"


def test_candidate_lines_excludes_caret_symbols():
    qual = _qual(["^TNX", "SPY"])
    structure = {s: _structure() for s in ["^TNX", "SPY"]}
    candidates = {s: _candidate(s) for s in ["^TNX", "SPY"]}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates)
    symbols = [line.split(" | ")[0] for line in lines]

    assert "^TNX" not in symbols
    assert "SPY" in symbols


# ---------------------------------------------------------------------------
# R:R in candidate line format
# ---------------------------------------------------------------------------

def test_candidate_lines_format_has_four_parts():
    qual = _qual(["NVDA"])
    structure = {"NVDA": _structure("TREND")}
    candidates = {"NVDA": _candidate("NVDA")}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates)
    assert len(lines) == 1
    parts = lines[0].split(" | ")
    assert len(parts) == 4, f"Expected SYMBOL | direction | structure | R:R, got: {lines[0]!r}"


def test_candidate_lines_rr_format():
    qual = _qual(["NVDA"])
    structure = {"NVDA": _structure("TREND")}
    # entry=200, stop=196 (risk=4), target=208 (reward=8) => 2.0:1
    candidates = {"NVDA": _candidate("NVDA", entry=200.0, stop=196.0, target=208.0)}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates)
    assert "2.0:1" in lines[0]


def test_candidate_lines_includes_structure():
    qual = _qual(["META"])
    structure = {"META": _structure("BREAKOUT")}
    candidates = {"META": _candidate("META")}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates)
    assert "BREAKOUT" in lines[0]


def test_candidate_lines_respects_limit():
    symbols = ["NVDA", "META", "AAPL", "AMZN", "SPY", "TSLA"]
    qual = _qual(symbols)
    structure = {s: _structure() for s in symbols}
    candidates = {s: _candidate(s) for s in symbols}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates, limit=3)
    assert len(lines) == 3


# ---------------------------------------------------------------------------
# Formatter output
# ---------------------------------------------------------------------------

def test_format_hourly_stay_flat_title_and_body():
    event = _hourly_event(regime=_regime(posture="STAY_FLAT", regime="NEUTRAL"))
    title, body = format_ntfy_alert(event)
    assert title == "STAY FLAT"
    assert "STAY_FLAT — no entries" in body


def test_format_hourly_no_setup_title_and_body():
    event = _hourly_event(qual=_qual([]))
    title, body = format_ntfy_alert(event)
    assert title == "NO SETUP"
    assert "No A+ setups" in body


def test_format_hourly_setup_ready_title():
    event = _hourly_event(
        qual=_qual(["META"]),
        candidate_lines=("META | SHORT | PULLBACK | 2.5:1",),
    )
    title, body = format_ntfy_alert(event)
    assert title == "META SHORT READY"
    assert "META | SHORT | PULLBACK | 2.5:1" in body


def test_format_hourly_required_fields_present():
    event = _hourly_event()
    _, body = format_ntfy_alert(event)
    assert "ET" in body
    assert "Regime:" in body
    assert "Posture:" in body
    assert "Confidence:" in body
    assert "Tradable:" in body
    assert "Setups:" in body


def test_format_hourly_system_halt_routes_to_halt_format():
    event = AlertEvent(
        alert_context=ALERT_CONTEXT_NOTIFY,
        notify_mode=NOTIFY_HOURLY,
        outcome="NO_TRADE",
        asof_utc=datetime(2026, 4, 23, 14, 30, tzinfo=timezone.utc),
        regime=None,
        validation_summary=_validation(halted=True),
        halt_reason="^VIX fetch failed",
    )
    title, body = format_ntfy_alert(event)
    assert title == "SYSTEM HALT"


def test_format_hourly_notification_wrapper_uses_watch_optimized_shape():
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 4, 23, 14, 0, tzinfo=timezone.utc),
        regime=_regime(regime="EXPANSION", posture="RISK_ON", confidence=0.72),
        validation_summary=_validation(),
        qualification_summary=_qual([]),
    )

    assert title == "ACTIVE - NO SETUP 10:00"
    assert body == (
        "EXPANSION | RISK ON | 0.72\n"
        "No trade.\n"
        "Reason: no setups\n\n"
        "TRIGGERS:\n"
        "- breakout above resistance\n"
        "- continuation hold above trigger"
    )


def test_format_hourly_notification_wrapper_filters_macro_candidates():
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 4, 23, 14, 0, tzinfo=timezone.utc),
        regime=_regime(regime="EXPANSION", posture="RISK_ON", confidence=0.81),
        validation_summary=_validation(),
        qualification_summary=_qual(["^VIX", "NVDA"], direction="LONG"),
        candidate_lines=("^VIX | LONG | TREND | 9.0:1", "NVDA | LONG | TREND | 2.4:1"),
    )

    assert title == "LONG NVDA 10:00"
    assert "^VIX" not in body
    assert "- NVDA LONG RR 2.4" in body


def test_format_hourly_notification_wrapper_explicit_watchlist_title_and_reason():
    qual = QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[],
        watchlist=[
            QualificationResult(
                symbol="AAPL",
                qualified=False,
                watchlist=True,
                direction="LONG",
                gates_passed=[],
                gates_failed=[],
                hard_failure=None,
                watchlist_reason="developing above trigger",
                max_contracts=None,
                dollar_risk=None,
            )
        ],
        excluded={},
        symbols_evaluated=1,
        symbols_qualified=0,
        symbols_watchlist=1,
        symbols_excluded=0,
    )
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 4, 23, 14, 0, tzinfo=timezone.utc),
        regime=_regime(regime="EXPANSION", posture="RISK_ON", confidence=0.81),
        validation_summary=_validation(),
        qualification_summary=qual,
    )

    assert title == "WATCHLIST 10:00"
    assert "WATCHLIST" in body
    assert "- AAPL LONG: developing above trigger" in body


# ---------------------------------------------------------------------------
# Alert contract: no file writes on normal execution
# ---------------------------------------------------------------------------

def test_execute_notify_run_does_not_write_markdown():
    src = inspect.getsource(_execute_notify_run)
    assert "_write_markdown_report" not in src


def test_execute_notify_run_does_not_write_latest_run():
    src = inspect.getsource(_execute_notify_run)
    assert "_write_summary_files" not in src
    assert "LATEST_RUN_PATH" not in src


def test_hourly_run_writes_hourly_specific_artifacts(tmp_path, monkeypatch):
    import cuttingboard.runtime as runtime

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_RUN_PATH", tmp_path / "logs" / "latest_hourly_run.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_CONTRACT_PATH", tmp_path / "logs" / "latest_hourly_contract.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_PAYLOAD_PATH", tmp_path / "logs" / "latest_hourly_payload.json")
    monkeypatch.setattr(runtime, "HOURLY_REPORT_PATH", tmp_path / "reports" / "output" / "hourly_report.html")

    patches = _patch_pipeline_stay_flat()
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
        result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    assert result["status"] == SUMMARY_STATUS_SUCCESS
    assert (tmp_path / "logs" / "latest_hourly_run.json").exists()
    assert (tmp_path / "logs" / "latest_hourly_contract.json").exists()
    assert (tmp_path / "logs" / "latest_hourly_payload.json").exists()
    assert (tmp_path / "reports" / "output" / "hourly_report.html").exists()
    assert not (tmp_path / "logs" / "latest_run.json").exists()

    hourly_run = json.loads((tmp_path / "logs" / "latest_hourly_run.json").read_text(encoding="utf-8"))
    hourly_contract = json.loads((tmp_path / "logs" / "latest_hourly_contract.json").read_text(encoding="utf-8"))
    hourly_payload = json.loads((tmp_path / "logs" / "latest_hourly_payload.json").read_text(encoding="utf-8"))

    assert hourly_run["notify_mode"] == NOTIFY_HOURLY
    assert hourly_run["status"] == SUMMARY_STATUS_SUCCESS
    assert hourly_run["notification_sent"] is True
    assert hourly_contract["artifacts"]["log_path"].endswith("latest_hourly_run.json")
    assert hourly_contract["outcome"] == "NO_TRADE"
    assert hourly_payload["meta"]["timestamp"] == hourly_contract["generated_at"]


def test_hourly_run_failure_writes_hourly_failure_artifacts(tmp_path, monkeypatch):
    import cuttingboard.runtime as runtime

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_RUN_PATH", tmp_path / "logs" / "latest_hourly_run.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_CONTRACT_PATH", tmp_path / "logs" / "latest_hourly_contract.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_PAYLOAD_PATH", tmp_path / "logs" / "latest_hourly_payload.json")
    monkeypatch.setattr(runtime, "HOURLY_REPORT_PATH", tmp_path / "reports" / "output" / "hourly_report.html")

    with (
        patch("cuttingboard.runtime.fetch_all", side_effect=RuntimeError("data fetch failed")),
        patch("cuttingboard.runtime.send_notification", return_value=True),
    ):
        result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    assert result["status"] == SUMMARY_STATUS_FAIL
    assert (tmp_path / "logs" / "latest_hourly_run.json").exists()
    assert (tmp_path / "logs" / "latest_hourly_contract.json").exists()
    assert (tmp_path / "logs" / "latest_hourly_payload.json").exists()

    hourly_run = json.loads((tmp_path / "logs" / "latest_hourly_run.json").read_text(encoding="utf-8"))
    hourly_contract = json.loads((tmp_path / "logs" / "latest_hourly_contract.json").read_text(encoding="utf-8"))

    assert hourly_run["status"] == SUMMARY_STATUS_FAIL
    assert hourly_run["notification_sent"] is True
    assert hourly_run["errors"] == ["data fetch failed"]
    assert hourly_contract["status"] == "ERROR"
    assert hourly_contract["outcome"] == "HALT"


# ---------------------------------------------------------------------------
# Alert contract: exactly one send_notification per trigger
# ---------------------------------------------------------------------------

def _patch_pipeline_stay_flat():
    return [
        patch("cuttingboard.runtime.fetch_all", return_value={}),
        patch("cuttingboard.runtime.normalize_all", return_value={}),
        patch("cuttingboard.runtime.extract_fetch_failures", return_value={}),
        patch("cuttingboard.runtime.validate_quotes", return_value=_validation()),
        patch("cuttingboard.runtime.compute_regime", return_value=_regime(posture="STAY_FLAT", regime="NEUTRAL")),
        patch("cuttingboard.runtime.compute_all_derived", return_value={}),
        patch("cuttingboard.runtime.resolve_sector_router", return_value=_router_state()),
        patch("cuttingboard.runtime.send_notification", return_value=True),
    ]


def test_hourly_sends_exactly_once_stay_flat():
    patches = _patch_pipeline_stay_flat()
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7] as mock_send:
        result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)
    mock_send.assert_called_once()
    assert result["status"] == SUMMARY_STATUS_SUCCESS


def test_hourly_sends_exactly_once_system_halted():
    with (
        patch("cuttingboard.runtime.fetch_all", return_value={}),
        patch("cuttingboard.runtime.normalize_all", return_value={}),
        patch("cuttingboard.runtime.extract_fetch_failures", return_value={}),
        patch("cuttingboard.runtime.validate_quotes", return_value=_validation(halted=True)),
        patch("cuttingboard.runtime.send_notification", return_value=True) as mock_send,
    ):
        result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    mock_send.assert_called_once()
    assert result["status"] == SUMMARY_STATUS_SUCCESS


def test_hourly_sends_exactly_once_on_exception(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with (
        patch("cuttingboard.runtime.fetch_all", side_effect=RuntimeError("data fetch failed")),
        patch("cuttingboard.runtime.send_notification", return_value=True) as mock_send,
    ):
        result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    mock_send.assert_called_once()
    assert result["status"] == SUMMARY_STATUS_FAIL


def test_hourly_writes_traceback_on_exception(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with (
        patch("cuttingboard.runtime.fetch_all", side_effect=RuntimeError("data fetch failed")),
        patch("cuttingboard.runtime.send_notification", return_value=True),
    ):
        _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    assert (tmp_path / "traceback.txt").exists()
    content = (tmp_path / "traceback.txt").read_text()
    assert "RuntimeError" in content
    assert "data fetch failed" in content
