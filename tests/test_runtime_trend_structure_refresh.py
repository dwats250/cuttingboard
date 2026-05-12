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
from unittest.mock import patch

from cuttingboard import runtime
from cuttingboard.runtime import (
    MODE_FIXTURE,
    MODE_LIVE,
    MODE_SUNDAY,
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
