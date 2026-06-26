"""PRD-123 — Trend Structure Refresh Decoupling.

Focused regression for `_refresh_trend_structure_sidecar` and its call
wiring inside `_run_pipeline`. Mocks `_write_trend_structure_snapshot`
at its definition site (`cuttingboard.runtime._write_trend_structure_snapshot`)
to avoid filesystem dependency and to assert call/no-call behavior under
each mode.

R7 cases covered:
1. MODE_LIVE refresh invokes the underlying writer.
2. No notification side effect is reachable from the refresh path.
3. MODE_FIXTURE refresh does NOT invoke the underlying writer.
4. MODE_SUNDAY refresh does NOT invoke the underlying writer.
5. Underlying-write exception is swallowed by the writer's own try/except;
   the helper does not propagate.
6. Static regression: `_refresh_trend_structure_sidecar` is wired into
   `_run_pipeline`'s source body so the integration point is not silently
   removed by a future edit.
"""
from __future__ import annotations

import inspect
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd

from cuttingboard import config, runtime
from cuttingboard.runtime import (
    MODE_FIXTURE,
    MODE_LIVE,
    MODE_SUNDAY,
    _collect_trend_structure_history,
    _execute_notify_run,
    _refresh_trend_structure_sidecar,
    _run_pipeline,
)


_NOW = datetime(2026, 5, 11, 8, 11, 0, tzinfo=timezone.utc)


# --- R7.1 — MODE_LIVE invokes the underlying writer ---------------------

def test_prd123_live_mode_invokes_underlying_writer() -> None:
    with patch.object(runtime, "_write_trend_structure_snapshot") as mock_writer:
        _refresh_trend_structure_sidecar(
            mode=MODE_LIVE,
            normalized_quotes={},
            history_by_symbol={},
            generated_at=_NOW,
        )
    assert mock_writer.call_count == 1, (
        f"expected exactly one writer call under MODE_LIVE, got {mock_writer.call_count}"
    )
    call = mock_writer.call_args
    assert call.kwargs["normalized_quotes"] == {}
    assert call.kwargs["history_by_symbol"] == {}
    assert call.kwargs["generated_at"] == _NOW


# --- R7.2 — No notification side effect ---------------------------------

def test_prd123_refresh_path_does_not_send_notification() -> None:
    """The helper must not reach send_notification. We patch at the
    notifications module and assert zero invocations across MODE_LIVE."""
    with patch("cuttingboard.output.send_notification") as mock_notify, \
         patch.object(runtime, "_write_trend_structure_snapshot") as _writer:
        _refresh_trend_structure_sidecar(
            mode=MODE_LIVE,
            normalized_quotes={},
            history_by_symbol={},
            generated_at=_NOW,
        )
    assert mock_notify.call_count == 0, "refresh path must not send notifications"


# --- R7.3 — MODE_FIXTURE skips the underlying writer --------------------

def test_prd123_fixture_mode_skips_underlying_writer() -> None:
    with patch.object(runtime, "_write_trend_structure_snapshot") as mock_writer:
        _refresh_trend_structure_sidecar(
            mode=MODE_FIXTURE,
            normalized_quotes={},
            history_by_symbol={},
            generated_at=_NOW,
        )
    assert mock_writer.call_count == 0, "fixture mode must not write the sidecar"


# --- R7.4 — MODE_SUNDAY skips the underlying writer ---------------------

def test_prd123_sunday_mode_skips_underlying_writer() -> None:
    with patch.object(runtime, "_write_trend_structure_snapshot") as mock_writer:
        _refresh_trend_structure_sidecar(
            mode=MODE_SUNDAY,
            normalized_quotes={},
            history_by_symbol={},
            generated_at=_NOW,
        )
    assert mock_writer.call_count == 0, "sunday mode must not write the sidecar"


# --- R7.5 — Underlying-write failure does not propagate -----------------

def test_prd123_writer_exception_does_not_propagate() -> None:
    """The underlying `_write_trend_structure_snapshot` swallows exceptions
    via its own try/except. If a future regression removed that swallow,
    this test surfaces it — the helper must not propagate either."""
    # Force the underlying writer to raise. The helper relays the call; the
    # writer's own try/except catches the exception. Net behavior: no raise.
    real_writer = runtime._write_trend_structure_snapshot

    def _exploding_build(*_args, **_kwargs):
        raise RuntimeError("simulated snapshot build failure")

    # Patch the deepest layer (the trend_structure builder) so the runtime
    # writer's own try/except is exercised on the way out.
    with patch("cuttingboard.runtime.build_trend_structure_snapshot",
               side_effect=_exploding_build):
        # Should not raise.
        real_writer(
            normalized_quotes={},
            history_by_symbol={},
            generated_at=_NOW,
        )
        _refresh_trend_structure_sidecar(
            mode=MODE_LIVE,
            normalized_quotes={},
            history_by_symbol={},
            generated_at=_NOW,
        )


# --- R7.6 — Static regression: helper is wired into _run_pipeline -------

def test_prd123_run_pipeline_calls_refresh_helper() -> None:
    """Static regression: the body of `_run_pipeline` must contain a call
    to `_refresh_trend_structure_sidecar` so the integration is not
    silently removed by a future runtime edit. Cheaper than running the
    full pipeline with mocks; tighter coupling to intent."""
    src = inspect.getsource(_run_pipeline)
    assert "_refresh_trend_structure_sidecar(" in src, (
        "_run_pipeline must call _refresh_trend_structure_sidecar; "
        "PRD-123 R2 wiring missing"
    )
    # Defense-in-depth: the call must be inside a `mode == MODE_LIVE` gate
    # so fixture/sunday paths never reach the helper even by accident.
    assert "mode == MODE_LIVE" in src, (
        "_run_pipeline must gate the refresh call with mode == MODE_LIVE; "
        "PRD-123 R2 defense-in-depth missing"
    )


# --- Helper signature lock (informational) ------------------------------

def test_prd123_helper_signature_is_keyword_only() -> None:
    """R1: helper signature is keyword-only and rejects positional calls.
    Lock against accidental signature drift."""
    sig = inspect.signature(_refresh_trend_structure_sidecar)
    params = list(sig.parameters.values())
    assert {p.name for p in params} == {
        "mode", "normalized_quotes", "history_by_symbol", "generated_at",
    }
    for p in params:
        assert p.kind == inspect.Parameter.KEYWORD_ONLY, (
            f"parameter {p.name!r} must be keyword-only"
        )


# --- PRD-174 — trend OHLCV populated regardless of posture --------------

def test_prd174_collect_trend_history_covers_all_symbols_on_flat_run() -> None:
    """R1: on a STAY_FLAT hourly run the candidate ohlcv dict is empty, but the
    history handed to the writer must still cover every TREND_STRUCTURE_SYMBOL
    whose fetch returns a frame. Posture is irrelevant to the helper."""
    def _fake_fetch(symbol):
        return pd.DataFrame({"Close": [1.0, 2.0]})

    with patch.object(runtime, "fetch_ohlcv", side_effect=_fake_fetch):
        history = _collect_trend_structure_history({})

    assert set(history.keys()) == set(config.TREND_STRUCTURE_SYMBOLS), (
        "every trend-structure symbol must be present on a flat run, "
        f"got {sorted(history.keys())}"
    )


def test_prd174_collect_trend_history_reuses_candidates_and_omits_none() -> None:
    """R1/R2: an already-fetched candidate frame is reused (not re-fetched), and
    a symbol whose fetch returns None is omitted (so the builder resolves it to
    its existing unavailable sentinel) without raising."""
    spy = config.TREND_STRUCTURE_SYMBOLS[0]
    missing = config.TREND_STRUCTURE_SYMBOLS[1]
    candidate_frame = pd.DataFrame({"Close": [10.0]})

    def _fake_fetch(symbol):
        if symbol == missing:
            return None
        return pd.DataFrame({"Close": [3.0]})

    fetch_mock = MagicMock(side_effect=_fake_fetch)
    with patch.object(runtime, "fetch_ohlcv", fetch_mock):
        history = _collect_trend_structure_history({spy: candidate_frame})

    assert history[spy] is candidate_frame, "pre-fetched candidate frame must be reused"
    assert spy not in [c.args[0] for c in fetch_mock.call_args_list], (
        "a reused candidate frame must not be re-fetched"
    )
    assert missing not in history, "a None-fetch symbol must be omitted"


def test_prd174_execute_notify_run_wires_trend_history_helper() -> None:
    """R1 wiring: _execute_notify_run must feed the writer through the
    posture-agnostic helper, inside the unconditional hourly-artifact block
    (so STAY_FLAT runs are covered). Static-source regression, mirroring the
    PRD-123 R7.6 pattern."""
    src = inspect.getsource(_execute_notify_run)
    assert "history_by_symbol=_collect_trend_structure_history(ohlcv)" in src, (
        "the hourly trend-structure writer call must pass "
        "_collect_trend_structure_history(ohlcv) as history_by_symbol"
    )


# --- PRD-210 R1 — premarket call-site applies the trend-history fallback (F08) ---

def test_prd210_run_pipeline_wraps_premarket_history_with_collector() -> None:
    """PRD-210 R1 (call-site wiring; RED before the fix).

    The F08 fix wraps the premarket sidecar's history argument with
    ``_collect_trend_structure_history`` so a non-candidate TREND_STRUCTURE_SYMBOL
    (e.g. QQQ) resolves on the premarket path, instead of passing the raw
    candidate-scoped ``ohlcv`` (which omits non-candidates -> DATA_UNAVAILABLE).
    Static-source lock, mirroring PRD-123 R7.6 (:143) and PRD-174 (:219). Fails on
    pre-fix code (``history_by_symbol=ohlcv``)."""
    src = inspect.getsource(_run_pipeline)
    assert "history_by_symbol=_collect_trend_structure_history(ohlcv)" in src, (
        "_run_pipeline must wrap the premarket sidecar's history_by_symbol with "
        "_collect_trend_structure_history(ohlcv) so non-candidate trend symbols "
        "resolve on the premarket path (PRD-210 F08 fix); found raw passthrough"
    )


def test_prd210_premarket_collector_reuses_present_candidate_frame() -> None:
    """PRD-210 R3: when a TREND_STRUCTURE_SYMBOL (QQQ) is already present in the
    candidate-scoped ``ohlcv``, the premarket fallback reuses that frame and does
    NOT re-fetch it — no behavior change for symbols already present."""
    qqq = "QQQ"
    assert qqq in config.TREND_STRUCTURE_SYMBOLS, "QQQ must be a trend symbol"
    present_frame = pd.DataFrame({"Close": [100.0]})
    fetch_mock = MagicMock(side_effect=lambda s: pd.DataFrame({"Close": [1.0]}))
    with patch.object(runtime, "fetch_ohlcv", fetch_mock):
        history = _collect_trend_structure_history({qqq: present_frame})
    assert history[qqq] is present_frame, "present QQQ frame must be reused, not refetched"
    assert qqq not in [c.args[0] for c in fetch_mock.call_args_list], (
        "fetch_ohlcv must not be called for a symbol already present in ohlcv"
    )
