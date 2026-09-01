"""PRD-324 (A1-C): mutation-red tests for the pure consumer leaf
``cuttingboard.delivery.intraday_bars`` (M1-M11, M19-M28). Every rejection returns
``None`` so the renderer keeps its daily chart; the leaf never raises."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone

import pytest

from cuttingboard.delivery import intraday_bars
from cuttingboard.delivery.intraday_bars import derive_intraday_session

_UTC = timezone.utc
# 09:30 ET on 2026-08-27 (EDT, UTC-4) == 13:30 UTC. All source ts are UTC (R4).
_ANCHOR = datetime(2026, 8, 27, 13, 30, tzinfo=_UTC)
_SESSION = "2026-08-27"
_NOW = datetime(2026, 8, 27, 13, 46, tzinfo=_UTC)  # 09:46 ET, mid-session
_GEN = datetime(2026, 8, 27, 13, 45, tzinfo=_UTC).isoformat()  # 1 min before now

# A deterministic bin-0 with distinct OHLCV so aggregation is pinned (M6).
_BIN0 = [
    (100.0, 100.5, 99.5, 100.2, 10),
    (100.2, 101.0, 100.0, 100.8, 20),
    (100.8, 100.9, 100.1, 100.3, 30),
    (100.3, 100.4, 99.0, 99.5, 40),   # low 99.0 is the bin min
    (99.5, 100.2, 99.4, 99.8, 50),    # close 99.8 is the bin close
]


def _ts(offset: int) -> str:
    return (_ANCHOR + timedelta(minutes=offset)).isoformat()


def _bar(offset: int, o=100.0, h=101.0, low=99.0, c=100.0, v=10) -> list:
    return [_ts(offset), o, h, low, c, v]


def _bin0_bars() -> list[list]:
    return [_bar(i, *vals) for i, vals in enumerate(_BIN0)]


def _snapshot(bars: list[list], *, primary="SPY", session_date=_SESSION,
              generated_at=_GEN, through=None, **top_over) -> dict:
    entry_through = through if through is not None else (bars[-1][0] if bars else None)
    snap = {
        "schema_version": 1,
        "generated_at": generated_at,
        "session_date": session_date,
        "primary_symbol": primary,
        "source": {"producer": "hourly", "provider": "yfinance",
                   "interval": "1m", "adjusted": False},
        "columns": ["ts", "Open", "High", "Low", "Close", "Volume"],
        "symbols": {primary: {"through": entry_through,
                              "row_count": len(bars), "bars": bars}},
    }
    snap.update(top_over)
    return snap


def _derive(snap, primary="SPY", now=_NOW):
    return derive_intraday_session(snap, primary, now)


# --- happy path ---------------------------------------------------------------

def test_valid_snapshot_derives_completed_5m_session():
    # offsets 0..9 -> two complete bins [09:30,09:35) and [09:35,09:40).
    bars = _bin0_bars() + [_bar(i) for i in range(5, 10)]
    session = _derive(_snapshot(bars))
    assert session is not None
    assert [c.label for c in session.candles] == ["09:30", "09:35"]  # M1 ET labels, M2 anchor
    c0 = session.candles[0]
    assert (c0.open, c0.high, c0.low, c0.close, c0.volume) == (100.0, 101.0, 99.0, 99.8, 150)  # M6
    assert session.session_date == _SESSION
    assert session.completed_through == "09:40"  # END/right edge of last completed bin (R10)


def test_caption_states_completed_through_not_raw_source_through():
    # Last source bar is 09:34 (offset 4); the completed bin's END is 09:35 -> they differ.
    session = _derive(_snapshot(_bin0_bars()))
    assert session is not None
    assert session.completed_through == "09:35"
    assert "09:35" in session.caption and _SESSION in session.caption
    assert "09:34" not in session.caption  # never captions the raw source `through` (R10)


# --- M3/M4/M5 membership and boundaries ---------------------------------------

def test_half_open_bin_excludes_sixth_minute():  # M3
    # offsets 0..5: bin0 complete (0-4); offset 5 opens bin1 but does not close bin0.
    bars = _bin0_bars() + [_bar(5)]
    session = _derive(_snapshot(bars))
    assert session is not None
    assert len(session.candles) == 1
    assert session.candles[0].close == 99.8  # minute-4 close, not the 6th minute


def test_bins_anchor_at_0930_not_first_bar():  # M2
    # Bars start at 09:32: no bin holds all five 09:30-anchored minutes; a first-bar anchor would.
    bars = [_bar(i) for i in range(2, 7)]
    assert _derive(_snapshot(bars)) is None


def test_missing_interior_minute_drops_the_bin():  # M4
    bars = [_bar(i, *_BIN0[i]) for i in (0, 1, 3, 4)]  # missing offset 2
    assert _derive(_snapshot(bars)) is None


def test_partial_final_bin_is_not_rendered():  # M5
    # bin0 complete (0-4), bin1 partial (5,6 only) -> only bin0 renders.
    bars = _bin0_bars() + [_bar(5), _bar(6)]
    session = _derive(_snapshot(bars))
    assert session is not None
    assert len(session.candles) == 1
    assert session.completed_through == "09:35"


def test_zero_completed_bins_returns_none():  # R9 gate (3) at the leaf
    assert _derive(_snapshot([_bar(0), _bar(1), _bar(2)])) is None


# --- M7/M8/M9/M27/M28 freshness & session bounds ------------------------------

def test_generated_at_exactly_90m_admits_and_91m_omits():  # M7
    now = datetime(2026, 8, 27, 15, 0, tzinfo=_UTC)  # 11:00 ET
    at_90 = (now - timedelta(minutes=90)).isoformat()
    at_91 = (now - timedelta(minutes=91)).isoformat()
    bars = _bin0_bars()
    assert _derive(_snapshot(bars, generated_at=at_90), now=now) is not None
    assert _derive(_snapshot(bars, generated_at=at_91), now=now) is None


def test_future_generated_at_is_rejected():  # M27
    now = datetime(2026, 8, 27, 13, 46, tzinfo=_UTC)
    future = (now + timedelta(minutes=1)).isoformat()
    assert _derive(_snapshot(_bin0_bars(), generated_at=future), now=now) is None


def test_through_future_skew_5m_admits_6m_omits():  # M8
    # `through` (last bar 09:34 ET) sits at now+5m (admitted, inclusive) then now+6m (rejected).
    last_ts = _ANCHOR + timedelta(minutes=4)  # 09:34 ET
    now_ok = last_ts - timedelta(minutes=5)   # through == now + 5m
    now_bad = last_ts - timedelta(minutes=6)  # through == now + 6m
    bars = _bin0_bars()
    assert _derive(_snapshot(bars, generated_at=now_ok.isoformat()), now=now_ok) is not None
    assert _derive(_snapshot(bars, generated_at=now_bad.isoformat()), now=now_bad) is None


def test_prior_session_date_is_rejected():  # M9
    assert _derive(_snapshot(_bin0_bars(), session_date="2026-08-26")) is None


def test_through_outside_regular_session_is_rejected():  # M28
    now = datetime(2026, 8, 27, 20, 10, tzinfo=_UTC)  # 16:10 ET, after close
    # `through` is a real 16:05 ET last bar, outside [09:30,16:00); bin0 complete, so only the endpoint check rejects.
    late = datetime(2026, 8, 27, 20, 5, tzinfo=_UTC).isoformat()
    bars = _bin0_bars() + [[late, 100.0, 101.0, 99.0, 100.0, 10]]
    assert _derive(_snapshot(bars, generated_at=now.isoformat()), now=now) is None


# --- M20-M26 / M10 nested admission -------------------------------------------

@pytest.mark.parametrize("mutate", [
    lambda s: s.__setitem__("schema_version", 2),                       # M20
    lambda s: s["source"].__setitem__("producer", "daily"),            # M21
    lambda s: s["source"].__setitem__("provider", "polygon"),          # M21
    lambda s: s["source"].__setitem__("interval", "5m"),               # M21
    lambda s: s["source"].__setitem__("adjusted", True),               # M21
    lambda s: s.__setitem__("columns", ["ts", "o", "h", "l", "c", "v"]),  # M22
    lambda s: s["symbols"]["SPY"].__setitem__("row_count", 99),        # M10 row_count
    lambda s: s["symbols"]["SPY"].__setitem__(  # M10 through (in-session, != last bar; not skew-masked)
        "through", s["symbols"]["SPY"]["bars"][-2][0]),
])
def test_envelope_and_nested_defects_fall_back(mutate):
    snap = _snapshot(_bin0_bars())
    mutate(snap)
    assert _derive(snap) is None


def test_malformed_row_length_rejected():  # M24
    # Under-length (5) and over-length (7); the 7-cell case isn't IndexError-masked, isolating the shape guard.
    for bad in ([_ts(2), 1, 2, 3, 4], _bar(2) + [999]):
        bars = _bin0_bars()
        bars[2] = bad
        assert _derive(_snapshot(bars)) is None


def test_non_ascending_ts_rejected():  # M25
    bars = _bin0_bars()
    bars[1][0], bars[2][0] = bars[2][0], bars[1][0]  # swap -> not strictly ascending
    assert _derive(_snapshot(bars)) is None


@pytest.mark.parametrize("volume", [10.5, -1, True])
def test_non_integer_or_negative_volume_rejected(volume):  # M26
    bars = _bin0_bars()
    bars[0][5] = volume
    assert _derive(_snapshot(bars)) is None


def test_float_integer_volume_admits():
    bars = _bin0_bars()
    bars[0][5] = 10.0  # integer-valued float is fine
    assert _derive(_snapshot(bars)) is not None


def test_incoherent_ohlcv_rejected():  # M10 coherence
    bars = _bin0_bars()
    bars[0][2] = 99.9  # High < max(Open, Close)
    assert _derive(_snapshot(bars)) is None


def test_per_bar_et_date_must_equal_session_date():  # M23
    bars = _bin0_bars()
    # A prior-ET-date first bar stays ascending and minute-aligned, so only the session-date guard rejects it.
    bars[0][0] = datetime(2026, 8, 26, 13, 30, tzinfo=_UTC).isoformat()
    snap = _snapshot(bars)
    snap["symbols"]["SPY"]["through"] = bars[-1][0]
    assert _derive(snap) is None


def test_schema_version_must_be_int_one_not_bool_or_float():  # R2 exact schema type
    assert _derive(_snapshot(_bin0_bars())) is not None                    # exactly 1 admits
    assert _derive(_snapshot(_bin0_bars(), schema_version=True)) is None   # True == 1 must NOT admit
    assert _derive(_snapshot(_bin0_bars(), schema_version=1.0)) is None    # 1.0 == 1 must NOT admit


def test_sub_minute_and_duplicate_minutes_rejected():  # R5 exact source-minute membership
    off = _bin0_bars()
    off[4][0] = off[4][0].replace(":00+00:00", ":30+00:00")  # 09:34:30 is not minute-aligned
    assert _derive(_snapshot(off)) is None
    dup = _bin0_bars()
    extra = list(dup[0])
    extra[0] = extra[0].replace(":00+00:00", ":30+00:00")
    dup.insert(1, extra)  # a second observation inside the 09:30 minute
    snap = _snapshot(dup)
    snap["symbols"]["SPY"]["row_count"] = len(dup)
    snap["symbols"]["SPY"]["through"] = dup[-1][0]
    assert _derive(snap) is None


def test_through_age_90m_admits_91m_omits():  # M7 (through freshness, distinct from generated_at)
    last = _ANCHOR + timedelta(minutes=4)  # 09:34 ET, the through
    now90, now91 = last + timedelta(minutes=90), last + timedelta(minutes=91)
    bars = _bin0_bars()
    assert _derive(_snapshot(bars, generated_at=now90.isoformat()), now=now90) is not None
    assert _derive(_snapshot(bars, generated_at=now91.isoformat()), now=now91) is None


# --- R7 primary agreement -----------------------------------------------------

def test_primary_disagreement_falls_back():  # M11 (leaf half)
    snap = _snapshot(_bin0_bars(), primary="SPY")
    snap["primary_symbol"] = "QQQ"  # snapshot names a different primary
    assert _derive(snap, primary="SPY") is None


def test_none_primary_falls_back():
    assert _derive(_snapshot(_bin0_bars()), primary=None) is None


# --- R1 never-raises ----------------------------------------------------------

@pytest.mark.parametrize("bad", [None, [], "not-a-dict", 42, {"schema_version": 1}])
def test_never_raises_on_garbage(bad):  # M19 (leaf half)
    assert derive_intraday_session(bad, "SPY", _NOW) is None


def test_naive_now_is_rejected_without_raising():
    naive = datetime(2026, 8, 27, 9, 46)  # tz-naive
    assert derive_intraday_session(_snapshot(_bin0_bars()), "SPY", naive) is None


def test_deeply_corrupt_bars_return_none_not_raise():
    snap = _snapshot(_bin0_bars())
    snap["symbols"]["SPY"]["bars"] = [["not-a-timestamp", "x", None, {}, [], object()]]
    snap["symbols"]["SPY"]["row_count"] = 1
    snap["symbols"]["SPY"]["through"] = "not-a-timestamp"
    assert _derive(snap) is None


def test_module_import_boundary_is_pure():  # R12 (a) import boundary
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(intraday_bars))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            imported.update(f"{base}.{alias.name}".strip(".") for alias in node.names)
    for path in imported:
        for forbidden in ("dashboard_renderer", "runtime", "requests", "urllib",
                          "yfinance", "notification", "telegram", "decision"):
            assert forbidden not in path, f"leaf imports {path}"


def test_derivation_is_deterministic():  # R5 byte-identical output for identical input
    snap = _snapshot(_bin0_bars() + [_bar(i) for i in range(5, 10)])
    a = _derive(copy.deepcopy(snap))
    b = _derive(copy.deepcopy(snap))
    assert a == b
