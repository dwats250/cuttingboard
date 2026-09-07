"""NS-4A v2 (PRD-337 precursor) observe-only isolation guards.

Proves the market-structure observation fetch (`_OBSERVE_ONLY_FETCH`, 12 derived
symbols) is fetched for the MARKET MOVEMENT card yet remains structurally disjoint
from the decision pipeline: derived-not-listed membership, disjointness from every
decision list, the per-symbol `nq.symbol == sym` filter that protects decision
quotes, best-effort transient failure, and the monotonic elapsed budget. The
frozen config-literal guards anchor the decision universe at this head so any edit
that widens it reddens here.

The decision-invariance paired run (A/B/C, section 3.10) lives at the bottom.
"""

from __future__ import annotations

from datetime import datetime, timezone

from cuttingboard import config
import cuttingboard.runtime as runtime
from cuttingboard.normalization import NormalizedQuote


def _quote(symbol: str, price: float = 50.0, pct: float = 0.01) -> NormalizedQuote:
    return NormalizedQuote(
        symbol=symbol, price=price, pct_change_decimal=pct, volume=None,
        fetched_at_utc=datetime(2026, 8, 22, 14, 30, tzinfo=timezone.utc),
        source="test", units="usd_price", age_seconds=0.0,
    )


# --- Frozen decision-universe literals (static guards, section 3.10) ---------
# Captured at head 8c403bb4 / f87bda75; byte-identical here so any decision-list
# widening (e.g. appending _OBSERVE_ONLY_FETCH to ALL_SYMBOLS) reddens. (M1)
def test_config_all_symbols_frozen_literal() -> None:
    assert config.ALL_SYMBOLS == [
        "^VIX", "DX-Y.NYB", "^TNX", "BTC-USD", "CL=F", "GC=F", "SI=F",
        "^TYX", "JPY=X", "DGS2", "DGS5", "EURUSD=X", "USDCAD=X", "NG=F", "ETH-USD",
        "SPY", "QQQ", "IWM",
        "GLD", "SLV", "GDX", "PAAS", "USO", "XLE",
        "NVDA", "TSLA", "AAPL", "META", "AMZN", "COIN", "MSTR",
    ]
    assert len(config.ALL_SYMBOLS) == 31


def test_config_required_symbols_frozen_literal() -> None:
    assert config.REQUIRED_SYMBOLS == ["^VIX", "DX-Y.NYB", "^TNX", "BTC-USD", "SPY", "QQQ"]


def test_config_halt_symbols_frozen_literal() -> None:
    assert config.HALT_SYMBOLS == ["^VIX", "DX-Y.NYB", "^TNX", "SPY", "QQQ"]


def test_config_non_tradable_symbols_frozen_literal() -> None:
    assert config.NON_TRADABLE_SYMBOLS == frozenset({
        "^VIX", "DX-Y.NYB", "^TNX", "BTC-USD", "CL=F", "GC=F", "SI=F",
        "^TYX", "JPY=X", "DGS2", "DGS5", "EURUSD=X", "USDCAD=X", "NG=F", "ETH-USD",
    })


def test_config_trend_structure_symbols_frozen_literal() -> None:
    assert config.TREND_STRUCTURE_SYMBOLS == ("SPY", "QQQ", "GDX", "GLD", "SLV", "XLE")


def test_legacy_observe_only_constant_removed() -> None:
    # The hand-listed OBSERVE_ONLY_SYMBOLS is deleted; membership is derived.
    assert not hasattr(config, "OBSERVE_ONLY_SYMBOLS")


# --- Derived observe-only fetch set (literal 12-tuple, disjoint) -------------
def test_observe_only_fetch_is_exact_12_tuple() -> None:  # M1
    assert runtime._OBSERVE_ONLY_FETCH == (
        "XLK", "XLF", "XLI", "XLY", "XLP", "XLV", "XLU", "XLB", "XLRE", "XLC", "MSFT", "GOOG",
    )


def test_observe_only_fetch_disjoint_from_every_decision_list() -> None:  # M1
    obs = set(runtime._OBSERVE_ONLY_FETCH)
    assert obs.isdisjoint(config.ALL_SYMBOLS)
    assert obs.isdisjoint(config.REQUIRED_SYMBOLS)
    assert obs.isdisjoint(config.HALT_SYMBOLS)
    assert obs.isdisjoint(config.NON_TRADABLE_SYMBOLS)
    assert obs.isdisjoint(config.TREND_STRUCTURE_SYMBOLS)


def test_observe_only_excludes_uco_and_tsla() -> None:
    assert "UCO" not in runtime._OBSERVE_ONLY_FETCH   # personal-only, not measurement
    assert "TSLA" not in runtime._OBSERVE_ONLY_FETCH  # disabled tombstone


def test_observe_only_excludes_already_fetched_measurement_symbols() -> None:
    # SPY/QQQ/XLE/GLD/SLV/GDX/AAPL/NVDA/META/AMZN are measurement symbols already
    # in ALL_SYMBOLS; the derived set must not re-fetch them.
    from cuttingboard.watchlist_sidecar import MARKET_STRUCTURE_SYMBOLS
    already = set(MARKET_STRUCTURE_SYMBOLS) & set(config.ALL_SYMBOLS)
    assert already  # guard against a vacuous assertion
    assert set(runtime._OBSERVE_ONLY_FETCH).isdisjoint(already)


# --- Per-symbol fetch behaviour ---------------------------------------------
def test_fetch_observe_only_returns_all_when_fetch_succeeds(monkeypatch):
    monkeypatch.setattr(runtime, "fetch_quote", lambda sym: sym)
    monkeypatch.setattr(runtime, "normalize_quote", lambda raw: _quote(raw))
    out = runtime._fetch_observe_only_quotes()
    assert set(out) == set(runtime._OBSERVE_ONLY_FETCH)
    assert all(out[s].symbol == s for s in out)


def test_fetch_observe_only_best_effort_on_failure(monkeypatch):
    def flaky(sym):
        if sym == "XLK":
            raise RuntimeError("network down")
        return sym
    monkeypatch.setattr(runtime, "fetch_quote", flaky)
    monkeypatch.setattr(runtime, "normalize_quote", lambda raw: _quote(raw))
    out = runtime._fetch_observe_only_quotes()  # must NOT raise
    assert "XLK" not in out
    assert set(out) == set(runtime._OBSERVE_ONLY_FETCH) - {"XLK"}


def test_fetch_observe_only_drops_none_normalization(monkeypatch):
    monkeypatch.setattr(runtime, "fetch_quote", lambda sym: sym)
    monkeypatch.setattr(runtime, "normalize_quote", lambda raw: None if raw == "GOOG" else _quote(raw))
    out = runtime._fetch_observe_only_quotes()
    assert "GOOG" not in out


def test_fetch_observe_only_swallows_normalize_exception(monkeypatch):
    def boom(_raw):
        raise ValueError("bad normalize")
    monkeypatch.setattr(runtime, "fetch_quote", lambda sym: sym)
    monkeypatch.setattr(runtime, "normalize_quote", boom)
    assert runtime._fetch_observe_only_quotes() == {}  # all dropped, no halt


def test_fetch_observe_only_drops_symbol_mismatch(monkeypatch):  # M11
    # A provider that ECHOES a decision symbol (e.g. SPY) for an observe-only
    # request must be dropped by the nq.symbol == sym filter, so a decision quote
    # can never be overwritten via the observation seam.
    def echo_spy(raw):
        return _quote("SPY") if raw == "XLK" else _quote(raw)
    monkeypatch.setattr(runtime, "fetch_quote", lambda sym: sym)
    monkeypatch.setattr(runtime, "normalize_quote", echo_spy)
    out = runtime._fetch_observe_only_quotes()
    assert "SPY" not in out                    # echoed SPY dropped
    assert "XLK" not in out                    # its slot dropped (symbol mismatch)
    assert set(out) == set(runtime._OBSERVE_ONLY_FETCH) - {"XLK"}


def test_disjointness_breach_returns_empty(monkeypatch):
    # If a bad edit made the derived set overlap a decision list, the seam fails
    # WITHIN the observation boundary (empty), never contaminating decisions.
    monkeypatch.setattr(runtime, "_OBSERVE_ONLY_FETCH", ("SPY", "XLK"))
    called = []
    monkeypatch.setattr(runtime, "fetch_quote", lambda sym: called.append(sym) or sym)
    monkeypatch.setattr(runtime, "normalize_quote", lambda raw: _quote(raw))
    assert runtime._fetch_observe_only_quotes() == {}
    assert called == []  # no fetch issued once overlap detected


# --- Monotonic elapsed budget (test D; Astra R2 exact-deadline) -------------
def test_observe_only_budget_is_exhausted_at_equality(monkeypatch):  # test D / M10
    # Deterministic fake monotonic clock, no real sleeping. Each fetch advances
    # elapsed by 30 s, so the pre-fetch elapsed sequence is 0, 30, 60, 90, ...
    # With the corrected exhausted-budget predicate (elapsed >= 60) a fetch STARTS
    # only while elapsed is strictly < 60:
    #   elapsed 0   (< 60)  -> starts
    #   elapsed 30  (< 60)  -> starts
    #   elapsed 60  (== 60) -> budget exhausted; does NOT start (exact deadline)
    #   elapsed 90  (> 60)  -> does NOT start
    # so exactly two fetches begin and both completed observations are retained.
    # (Pre-fix `elapsed > 60` blessed a third start at exactly 60 -- this reddens
    # on that behaviour.)
    clock = {"t": 0.0}

    class _FakeTime:
        def monotonic(self):
            return clock["t"]

    started_at: list[float] = []

    def fake_fetch(sym):
        started_at.append(clock["t"])  # elapsed at the moment this fetch began
        clock["t"] += 30.0
        return sym

    monkeypatch.setattr(runtime, "time", _FakeTime())
    monkeypatch.setattr(runtime, "fetch_quote", fake_fetch)
    monkeypatch.setattr(runtime, "normalize_quote", lambda raw: _quote(raw))

    out = runtime._fetch_observe_only_quotes()  # must NOT raise on budget expiry
    # < 60 begins; == 60 and > 60 refused.
    assert started_at == [0.0, 30.0]
    assert len(out) == 2                        # both completed observations retained
    assert set(out) <= set(runtime._OBSERVE_ONLY_FETCH)


# --- Cadence: exactly one call site -----------------------------------------
def test_watchlist_writer_called_only_at_hourly_seam():
    import inspect
    src = inspect.getsource(runtime)
    calls = [
        ln for ln in src.splitlines()
        if "_write_watchlist_snapshot(" in ln and "def _write_watchlist_snapshot" not in ln
    ]
    assert len(calls) == 1


def test_fetch_observe_only_called_once_outside_definition():
    import inspect
    src = inspect.getsource(runtime)
    calls = [
        ln for ln in src.splitlines()
        if "_fetch_observe_only_quotes(" in ln and "def _fetch_observe_only_quotes" not in ln
    ]
    assert len(calls) == 1  # the single watchlist-merge call site


# --- Merge-seam blindness (fast, patched) -----------------------------------
def test_runtime_observe_only_reaches_watchlist_not_decisions(monkeypatch, tmp_path):
    from datetime import date
    from cuttingboard.notifications import NOTIFY_HOURLY
    from cuttingboard.runtime import MODE_LIVE, SUMMARY_STATUS_SUCCESS, _execute_notify_run
    from tests.test_hourly_alert import (
        _regime, _router_state, _setup_tmp_artifacts, _validation,
    )

    _setup_tmp_artifacts(monkeypatch, tmp_path)
    cap: dict = {}
    monkeypatch.setattr(runtime, "fetch_all", lambda: {})
    monkeypatch.setattr(runtime, "normalize_all", lambda raw: {})
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
                        lambda: {s: _quote(s) for s in runtime._OBSERVE_ONLY_FETCH})

    result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    assert result["status"] == SUMMARY_STATUS_SUCCESS
    # decision-blind: no observe-only symbol entered the validate_quotes input
    assert set(runtime._OBSERVE_ONLY_FETCH).isdisjoint(cap["validate_in"])
    # but they DID reach the watchlist sidecar mapping
    assert set(runtime._OBSERVE_ONLY_FETCH) <= cap["watchlist_in"]


# --- Decision-invariance paired run with REAL decision stages (section 3.10) --
# Volatile keys scrubbed before byte comparison. Every entry is a timestamp or a
# run id -- NEVER a decision field -- so scrubbing them does not weaken the proof.
_VOLATILE_KEYS = frozenset({
    "generation_id", "run_id",              # per-run ids (wall-clock derived)
    "generated_at", "computed_at_utc", "run_at_utc",  # timestamps
    "asof_utc", "as_of_utc", "timestamp",
})


def _real_stage_fixture():
    """Six fresh NormalizedQuotes: all five HALT_SYMBOLS + BTC-USD (the mandatory
    macro drivers) so the REAL validate_quotes does not halt and the real
    compute_regime / compute_all_derived / resolve_sector_router stages run."""
    from cuttingboard.normalization import NormalizedQuote

    def q(sym, price, pct=0.001):
        return NormalizedQuote(
            symbol=sym, price=price, pct_change_decimal=pct, volume=1_000_000.0,
            fetched_at_utc=datetime.now(timezone.utc), source="test",
            units="usd_price", age_seconds=1.0,
        )

    return {
        "SPY": q("SPY", 400.0), "QQQ": q("QQQ", 350.0),
        "^VIX": q("^VIX", 18.0, 0.0), "DX-Y.NYB": q("DX-Y.NYB", 104.0, 0.0),
        "^TNX": q("^TNX", 4.3, 0.0), "BTC-USD": q("BTC-USD", 60000.0, 0.0),
    }


def _scrub(text: str, tmp) -> str:
    import re
    text = text.replace(str(tmp), "<TMP>")
    pattern = r'"(' + "|".join(sorted(_VOLATILE_KEYS)) + r')"\s*:\s*("[^"]*"|null|[0-9.]+)'
    return re.sub(pattern, lambda m: f'"{m.group(1)}":"<V>"', text)


def _run_real_notify(observe_ret, tmp, monkeypatch, validate_calls):
    import json as _json
    from datetime import date
    from cuttingboard.notifications import NOTIFY_HOURLY
    from cuttingboard.runtime import MODE_LIVE, _execute_notify_run

    for attr, fn in [
        ("LATEST_HOURLY_RUN_PATH", "latest_hourly_run.json"),
        ("LATEST_HOURLY_CONTRACT_PATH", "latest_hourly_contract.json"),
        ("LATEST_HOURLY_PAYLOAD_PATH", "latest_hourly_payload.json"),
        ("LATEST_HOURLY_MARKET_MAP_PATH", "latest_hourly_market_map.json"),
        ("MARKET_MAP_PATH", "market_map.json"),
    ]:
        monkeypatch.setattr(runtime, attr, tmp / "logs" / fn)
    monkeypatch.setattr(runtime, "LOGS_DIR", tmp / "logs")
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp / "reports")
    monkeypatch.setattr(runtime, "HOURLY_REPORT_PATH", tmp / "reports" / "output" / "hourly_report.html")
    monkeypatch.setattr(runtime, "WATCHLIST_PATH", tmp / "logs" / "watchlist_snapshot.json")
    monkeypatch.setattr(runtime, "fetch_all", lambda: {})
    monkeypatch.setattr(runtime, "normalize_all", lambda raw: _real_stage_fixture())
    monkeypatch.setattr(runtime, "extract_fetch_failures", lambda raw: {})

    # Recording spy that FORWARDS to the real validate_quotes and records the key
    # set of its quote argument -- proves the decision entry never sees an observe
    # symbol, while the real regime/derived/router stages run unpatched.
    _real_validate = runtime.validate_quotes

    def _spy_validate(nq, *a, **k):
        validate_calls.append(set(nq))
        return _real_validate(nq, *a, **k)

    monkeypatch.setattr(runtime, "validate_quotes", _spy_validate)

    notif: list = []
    monkeypatch.setattr(runtime, "send_notification",
                        lambda title=None, body=None, *a, **k: notif.append((title, body)) or True)
    monkeypatch.setattr(runtime, "_fetch_observe_only_quotes", observe_ret)

    result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    files = {}
    for fn in ("latest_hourly_contract.json", "latest_hourly_run.json",
               "latest_hourly_payload.json", "latest_hourly_market_map.json"):
        p = tmp / "logs" / fn
        files[fn] = _scrub(p.read_text(encoding="utf-8"), tmp) if p.exists() else "<MISSING>"
    wl_path = tmp / "logs" / "watchlist_snapshot.json"
    watchlist = _json.loads(wl_path.read_text(encoding="utf-8")) if wl_path.exists() else None
    return result, files, notif, watchlist


def test_volatile_allowlist_is_only_timestamps_and_ids():
    # Honesty guard for the paired-run scrub: the allowlist may contain ONLY
    # timestamp / run-id keys, never a decision field.
    for key in _VOLATILE_KEYS:
        assert key.endswith(("_at", "_at_utc", "_id", "timestamp")) or key in {
            "computed_at_utc", "run_at_utc", "generated_at", "asof_utc", "as_of_utc",
        }, key


def test_decision_invariance_real_stages_paired_run(tmp_path):  # M6 / section 3.10 / Astra R1
    """Paired runs of _execute_notify_run with REAL validate_quotes /
    compute_regime / compute_all_derived / resolve_sector_router. Three cases,
    each in its OWN monkeypatch scope so the captured spies stay independently
    attributable (Astra section 7 -- no nested scope over an earlier run's spy):
      A: _fetch_observe_only_quotes -> {}          (observation data unavailable)
      B: -> all 12 extras, extreme values          (price 1e6, pct +0.95)
      C: -> raises RuntimeError                     (WHOLE-helper failure, Fable C)

    Every durable decision output must be byte-identical across A/B/C (volatile
    keys scrubbed) AND the full return dicts must be equal, proving the observation
    seam -- empty, extreme, or RAISING -- cannot influence decisions.

    C is the run-level boundary case Astra required (R1): a helper that raises must
    behave exactly like the observation-unavailable run A -- same status, same
    decision artifacts, same single notification, no HALT replacement, no extra
    failure notification. Pre-fix, C escaped to the outer handler and returned FAIL
    with a second notification and HALT artifacts, so this reddens on that
    behaviour. B proves the extreme observations DO reach the carrier without
    overwriting the decision SPY."""
    import re
    from cuttingboard.runtime import SUMMARY_STATUS_SUCCESS

    extreme = {s: _quote(s, price=1e6, pct=0.95) for s in runtime._OBSERVE_ONLY_FETCH}

    def _raise_helper():
        raise RuntimeError("review C sentinel")

    def _isolated_run(observe_ret, tag):
        """Run one case under a fresh, fully-undone MonkeyPatch scope."""
        mp = __import__("pytest").MonkeyPatch()
        validate_calls: list = []
        try:
            res, files, notif, wl = _run_real_notify(
                observe_ret, tmp_path / tag, mp, validate_calls)
        finally:
            mp.undo()
        return res, files, notif, wl, validate_calls

    resA, filesA, notifA, _wlA, va_a = _isolated_run(lambda: {}, "a")
    resB, filesB, notifB, wlB, va_b = _isolated_run(lambda: dict(extreme), "b")
    resC, filesC, notifC, _wlC, va_c = _isolated_run(_raise_helper, "c")

    # (0) All three runs SUCCEED -- the raising helper C must NOT flip to FAIL.
    assert resA["status"] == SUMMARY_STATUS_SUCCESS
    assert resB["status"] == SUMMARY_STATUS_SUCCESS
    assert resC["status"] == SUMMARY_STATUS_SUCCESS

    # (1) Full return dictionaries identical across all three cases.
    assert resA == resB == resC

    # (2) Decision invariance: every durable decision file byte-identical A/B/C.
    #     C identical to A proves NO HALT replacement of the successful artifacts.
    for fn in filesA:
        assert filesA[fn] != "<MISSING>"
        assert filesA[fn] == filesB[fn], f"decision output {fn} differs A vs B"
        assert filesA[fn] == filesC[fn], f"decision output {fn} differs A vs C"

    # (3) One notification per run, identical across runs (clock tokens scrubbed).
    #     Equal counts prove C sent NO extra (failure) notification.
    def _clk(pairs):
        return [(t, re.sub(r"\d{1,2}:\d{2}", "<T>", b or "")) for t, b in pairs]
    assert len(notifA) == len(notifB) == len(notifC)
    assert notifA  # the primary decision notification was sent
    assert _clk(notifA) == _clk(notifB) == _clk(notifC)

    # (4) The real validate_quotes never saw an observe-only symbol in any run.
    assert va_a and va_b and va_c
    for keyset in va_a + va_b + va_c:
        assert set(runtime._OBSERVE_ONLY_FETCH).isdisjoint(keyset)

    # (5) The extreme observations reached the carrier (B), without corrupting SPY.
    assert wlB is not None
    assert set(wlB["symbols"]) == set(runtime.MARKET_STRUCTURE_SYMBOLS)  # exactly 22
    assert wlB["symbols"]["SPY"]["current_price"] == 400.0        # decision value preserved
    assert wlB["symbols"]["XLK"]["current_price"] == 1e6          # extreme extra present
    assert "UCO" not in wlB["symbols"] and "TSLA" not in wlB["symbols"]
