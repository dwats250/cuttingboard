"""PRD-311 observe-only isolation guards (packet 2789dda §4.2 / R2).

Proves UCO/GOOG are fetched for the MARKET MOVEMENT card yet remain structurally
disjoint from the decision pipeline: M17 disjointness, M18 pipeline-blindness,
M14 fetched, M15/M16 best-effort transient failure -> absent (no halt).
"""

from __future__ import annotations

from datetime import datetime, timezone

from cuttingboard import config
import cuttingboard.runtime as runtime
from cuttingboard.normalization import NormalizedQuote


def _quote(symbol: str) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol, price=50.0, pct_change_decimal=0.01, volume=None,
        fetched_at_utc=datetime(2026, 8, 22, 14, 30, tzinfo=timezone.utc),
        source="test", units="usd_price", age_seconds=0.0,
    )


def test_observe_only_disjoint_from_decision_universe():  # M17
    obs = set(config.OBSERVE_ONLY_SYMBOLS)
    assert obs == {"UCO", "GOOG"}
    # Disjoint from ALL_SYMBOLS (the ingestion loop + regime breadth denominator)
    # and from NON_TRADABLE_SYMBOLS. The whole decision pipeline is keyed on
    # ALL_SYMBOLS / valid_quotes (a subset of normalize_all(fetch_all())), so
    # disjointness here is the structural proof of pipeline-blindness (M18).
    assert obs.isdisjoint(config.ALL_SYMBOLS)
    assert obs.isdisjoint(config.NON_TRADABLE_SYMBOLS)
    assert obs.isdisjoint(config.MACRO_DRIVERS)


def test_observe_only_not_fetched_by_the_universe_loop():  # M18
    # The ingestion universe loop iterates config.ALL_SYMBOLS; observe-only
    # symbols are absent from it, so they never enter normalize_all(fetch_all())
    # -> normalized_quotes -> validate_quotes -> any decision surface.
    for sym in config.OBSERVE_ONLY_SYMBOLS:
        assert sym not in config.ALL_SYMBOLS


def test_fetch_observe_only_returns_all_when_fetch_succeeds(monkeypatch):  # M14
    monkeypatch.setattr(runtime, "fetch_quote", lambda sym: sym)  # raw stand-in
    monkeypatch.setattr(runtime, "normalize_quote", lambda raw: _quote(raw))
    out = runtime._fetch_observe_only_quotes()
    assert set(out) == {"UCO", "GOOG"}
    assert out["UCO"].symbol == "UCO"


def test_fetch_observe_only_best_effort_on_failure(monkeypatch):  # M15/M16
    def flaky_fetch(sym):
        if sym == "UCO":
            raise RuntimeError("network down")
        return sym
    monkeypatch.setattr(runtime, "fetch_quote", flaky_fetch)
    monkeypatch.setattr(runtime, "normalize_quote", lambda raw: _quote(raw))
    out = runtime._fetch_observe_only_quotes()  # must NOT raise (no halt)
    assert set(out) == {"GOOG"}  # failed UCO omitted -> renders n/a downstream


def test_fetch_observe_only_drops_none_normalization(monkeypatch):  # M15
    monkeypatch.setattr(runtime, "fetch_quote", lambda sym: sym)
    monkeypatch.setattr(runtime, "normalize_quote", lambda raw: None if raw == "GOOG" else _quote(raw))
    out = runtime._fetch_observe_only_quotes()
    assert set(out) == {"UCO"}


def test_watchlist_writer_called_only_at_hourly_seam():  # M13 cadence
    import inspect
    src = inspect.getsource(runtime)
    calls = [
        ln for ln in src.splitlines()
        if "_write_watchlist_snapshot(" in ln and "def _write_watchlist_snapshot" not in ln
    ]
    # Exactly one call site (the hourly notify path). A daily-block write would
    # add a second and redden this guard (packet 2789dda M13; slice-1 boundary).
    assert len(calls) == 1


def test_fetch_observe_only_swallows_normalize_exception(monkeypatch):  # M15
    def boom(_raw):
        raise ValueError("bad normalize")
    monkeypatch.setattr(runtime, "fetch_quote", lambda sym: sym)
    monkeypatch.setattr(runtime, "normalize_quote", boom)
    assert runtime._fetch_observe_only_quotes() == {}  # raised normalization -> dropped, no halt


def test_runtime_observe_only_reaches_watchlist_not_decisions(monkeypatch, tmp_path):  # M18/M16 runtime proof
    from datetime import date
    from cuttingboard.notifications import NOTIFY_HOURLY
    from cuttingboard.runtime import MODE_LIVE, SUMMARY_STATUS_SUCCESS, _execute_notify_run
    from tests.test_hourly_alert import (
        _regime, _router_state, _setup_tmp_artifacts, _validation,
    )

    _setup_tmp_artifacts(monkeypatch, tmp_path)
    cap: dict = {}
    monkeypatch.setattr(runtime, "fetch_all", lambda: {})
    monkeypatch.setattr(runtime, "normalize_all", lambda raw: {})  # empty main set (stay-flat harness)
    monkeypatch.setattr(runtime, "extract_fetch_failures", lambda raw: {})
    monkeypatch.setattr(runtime, "validate_quotes",
                        lambda nq, *a, **k: cap.__setitem__("validate_in", set(nq)) or _validation())
    monkeypatch.setattr(runtime, "compute_regime",
                        lambda *a, **k: _regime(posture="STAY_FLAT", regime="NEUTRAL"))
    monkeypatch.setattr(runtime, "compute_all_derived", lambda *a, **k: {})
    monkeypatch.setattr(runtime, "resolve_sector_router", lambda *a, **k: _router_state())
    monkeypatch.setattr(runtime, "send_notification", lambda *a, **k: True)
    monkeypatch.setattr(runtime, "_write_watchlist_snapshot",
                        lambda normalized_quotes, generated_at: cap.__setitem__("watchlist_in", set(normalized_quotes)))
    monkeypatch.setattr(runtime, "_fetch_observe_only_quotes",
                        lambda: {"UCO": _quote("UCO"), "GOOG": _quote("GOOG")})

    result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    assert result["status"] == SUMMARY_STATUS_SUCCESS  # run completes (M16), never halts on the merge
    # decision-blind: observe-only symbols never entered the validate_quotes input (M18)
    assert "UCO" not in cap["validate_in"] and "GOOG" not in cap["validate_in"]
    # but they DID reach the watchlist sidecar mapping
    assert {"UCO", "GOOG"} <= cap["watchlist_in"]


def test_intraday_producer_makes_no_live_card_fetch_at_success_seam(monkeypatch, tmp_path):  # PRD-323 R3/R12
    # The A1-P intraday producer runs on the FULL-SUCCESS hourly seam (not only the
    # HALT path). Under the conftest autouse default (no opt-in) it performs ZERO
    # live card fetches. Record at the deeper fetcher and filter by the card
    # signature (timeout_seconds=25) so the daily :1250 SPY fetch is not
    # miscounted; do NOT override the autouse _fetch_intraday_card_bars default —
    # removing that default must turn this red.
    from datetime import date
    from cuttingboard.notifications import NOTIFY_HOURLY
    from cuttingboard.runtime import MODE_LIVE, SUMMARY_STATUS_SUCCESS, _execute_notify_run
    from tests.test_hourly_alert import _regime, _router_state, _setup_tmp_artifacts, _validation

    _setup_tmp_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(runtime, "INTRADAY_BARS_PATH", tmp_path / "logs" / "intraday_bars_snapshot.json")
    recorded: list = []
    monkeypatch.setattr(runtime, "fetch_all", lambda: {})
    monkeypatch.setattr(runtime, "normalize_all", lambda raw: {})
    monkeypatch.setattr(runtime, "extract_fetch_failures", lambda raw: {})
    monkeypatch.setattr(runtime, "validate_quotes", lambda nq, *a, **k: _validation())
    monkeypatch.setattr(runtime, "compute_regime",
                        lambda *a, **k: _regime(posture="STAY_FLAT", regime="NEUTRAL"))
    monkeypatch.setattr(runtime, "compute_all_derived", lambda *a, **k: {})
    monkeypatch.setattr(runtime, "resolve_sector_router", lambda *a, **k: _router_state())
    monkeypatch.setattr(runtime, "send_notification", lambda *a, **k: True)
    monkeypatch.setattr(runtime, "fetch_intraday_session_bars",
                        lambda symbol, **kwargs: recorded.append(kwargs) or None)

    result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    assert result["status"] == SUMMARY_STATUS_SUCCESS
    assert [kw for kw in recorded if kw.get("timeout_seconds") == 25] == []  # zero live card fetches
