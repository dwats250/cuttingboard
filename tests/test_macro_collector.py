"""Offline tests for tools/macro_collector.py (PRD-139).

Fully mocked. No real network I/O. Asserts model id, FEEDS membership,
credential absence, schema violations, partial-feed failure, atomic write,
and baseline preservation.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "macro_collector_under_test", _ROOT / "tools" / "macro_collector.py"
)
assert _SPEC is not None and _SPEC.loader is not None
mc = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mc)


# ----- helpers -------------------------------------------------------------


class _Resp:
    def __init__(self, body: bytes = b"<rss/>", status: int = 200) -> None:
        self._body = body
        self.status = status
        self.headers: dict[str, str] = {}

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_Resp":
        return self

    def __exit__(self, *a: object) -> bool:
        return False


def _good_payload() -> str:
    return json.dumps(
        {
            "macro_bias": "NEUTRAL",
            "confidence_score": 0.65,
            "fundamental_driver": "FOMC minutes neutral; CPI inline.",
            "timestamp": "2026-05-16T12:00:00+00:00",
        }
    )


def _fake_anthropic_module(captured: dict, payload: str) -> types.ModuleType:
    class _Block:
        type = "text"

        def __init__(self, t: str) -> None:
            self.text = t

    class _Msg:
        def __init__(self, t: str) -> None:
            self.content = [_Block(t)]

    class _Messages:
        def create(self, **kwargs: object) -> "_Msg":
            captured.update(kwargs)
            return _Msg(payload)

    class _Anthropic:
        def __init__(self, api_key: str) -> None:
            captured["api_key"] = api_key
            self.messages = _Messages()

    mod = types.ModuleType("anthropic")
    mod.Anthropic = _Anthropic  # type: ignore[attr-defined]
    return mod


# ----- fixtures ------------------------------------------------------------


@pytest.fixture
def tmp_logs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    snap = tmp_path / "macro_regime_snapshot.json"
    tmp = tmp_path / "macro_regime_snapshot.json.tmp"
    monkeypatch.setattr(mc, "SNAPSHOT_PATH", snap)
    monkeypatch.setattr(mc, "TMP_PATH", tmp)
    monkeypatch.setattr(mc, "BACKOFF_SCHEDULE_S", (0, 0, 0))
    return snap, tmp


@pytest.fixture
def env_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture
def block_network(monkeypatch: pytest.MonkeyPatch) -> None:
    import socket

    def _boom(*a: object, **kw: object) -> None:
        raise AssertionError("real network call attempted")

    monkeypatch.setattr(socket.socket, "connect", _boom)


# ----- contract / isolation ------------------------------------------------


def test_model_id_is_pinned() -> None:
    assert mc.MODEL_ID == "claude-sonnet-4-6"


def test_feeds_membership_exact() -> None:
    assert mc.FEEDS == (
        "https://www.federalreserve.gov/feeds/press_all.xml",
        "https://home.treasury.gov/system/files/126/ofac_press_releases.xml",
        "https://www.bls.gov/feed/bls_latest.rss",
    )
    assert len(mc.FEEDS) == 3


def test_no_cuttingboard_import_in_source() -> None:
    import re

    src = (_ROOT / "tools" / "macro_collector.py").read_text()
    pattern = re.compile(r"^\s*(from|import)\s+cuttingboard(\.|\s|$)", re.MULTILINE)
    assert pattern.search(src) is None


# ----- happy path ----------------------------------------------------------


def test_happy_path_writes_snapshot_and_uses_pinned_model(
    tmp_logs: tuple[Path, Path],
    env_key: None,
    block_network: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snap, tmp = tmp_logs
    captured: dict = {}
    monkeypatch.setitem(
        sys.modules, "anthropic", _fake_anthropic_module(captured, _good_payload())
    )
    monkeypatch.setattr(
        mc.urllib.request, "urlopen", lambda url, timeout=0: _Resp(b"<rss/>")
    )
    assert mc.main() == 0
    written = json.loads(snap.read_text())
    assert written["macro_bias"] == "NEUTRAL"
    assert set(written.keys()) == {
        "macro_bias",
        "confidence_score",
        "fundamental_driver",
        "timestamp",
    }
    assert not tmp.exists()
    assert captured["model"] == "claude-sonnet-4-6"
    assert captured["api_key"] == "test-key"


# ----- credential absence --------------------------------------------------


def test_missing_credentials_exits_1_without_network(
    tmp_logs: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    snap, tmp = tmp_logs
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    call_count = {"n": 0}

    def _track(*a: object, **kw: object) -> _Resp:
        call_count["n"] += 1
        return _Resp()

    monkeypatch.setattr(mc.urllib.request, "urlopen", _track)
    assert mc.main() == 1
    assert call_count["n"] == 0
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err
    assert not tmp.exists()


# ----- partial-allowlist failure aborts immediately ------------------------


def test_single_feed_failure_aborts_run(
    tmp_logs: tuple[Path, Path],
    env_key: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snap, tmp = tmp_logs
    snap.write_bytes(b'{"prior": true}')
    baseline = hashlib.sha256(snap.read_bytes()).hexdigest()
    call_count = {"n": 0}

    def _flaky(url: str, timeout: int = 0) -> _Resp:
        call_count["n"] += 1
        if "treasury" in url:
            raise OSError("simulated failure")
        return _Resp(b"<rss/>")

    monkeypatch.setattr(mc.urllib.request, "urlopen", _flaky)
    assert mc.main() == 1
    assert hashlib.sha256(snap.read_bytes()).hexdigest() == baseline
    assert not tmp.exists()
    # Fed succeeded (1) + Treasury retried 3 times then aborted; BLS never reached.
    assert call_count["n"] == 4


# ----- schema violations preserve baseline ---------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        {
            "macro_bias": "BANANAS",
            "confidence_score": 0.5,
            "fundamental_driver": "x",
            "timestamp": "2026-05-16T00:00:00Z",
        },
        {
            "macro_bias": "NEUTRAL",
            "confidence_score": 1.5,
            "fundamental_driver": "x",
            "timestamp": "2026-05-16T00:00:00Z",
        },
        {
            "macro_bias": "NEUTRAL",
            "confidence_score": -0.1,
            "fundamental_driver": "x",
            "timestamp": "2026-05-16T00:00:00Z",
        },
        {
            "macro_bias": "NEUTRAL",
            "confidence_score": 0.5,
            "fundamental_driver": "",
            "timestamp": "2026-05-16T00:00:00Z",
        },
        {
            "macro_bias": "NEUTRAL",
            "confidence_score": 0.5,
            "fundamental_driver": "x",
            "timestamp": "2026-05-16T00:00:00",
        },
        {
            "macro_bias": "NEUTRAL",
            "confidence_score": 0.5,
            "fundamental_driver": "x",
        },
        {
            "macro_bias": "NEUTRAL",
            "confidence_score": 0.5,
            "fundamental_driver": "x",
            "timestamp": "2026-05-16T00:00:00Z",
            "extra": 1,
        },
    ],
    ids=[
        "bias-out-of-enum",
        "score-above-one",
        "score-below-zero",
        "empty-driver",
        "naive-timestamp",
        "missing-key",
        "extra-key",
    ],
)
def test_schema_violations_exit_1_preserve_baseline(
    bad: dict,
    tmp_logs: tuple[Path, Path],
    env_key: None,
    block_network: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snap, tmp = tmp_logs
    snap.write_bytes(b'{"prior": true}')
    baseline = hashlib.sha256(snap.read_bytes()).hexdigest()
    monkeypatch.setitem(
        sys.modules, "anthropic", _fake_anthropic_module({}, json.dumps(bad))
    )
    monkeypatch.setattr(
        mc.urllib.request, "urlopen", lambda url, timeout=0: _Resp(b"<rss/>")
    )
    assert mc.main() == 1
    assert hashlib.sha256(snap.read_bytes()).hexdigest() == baseline
    assert not tmp.exists()


def test_malformed_json_from_llm_exits_1(
    tmp_logs: tuple[Path, Path],
    env_key: None,
    block_network: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snap, tmp = tmp_logs
    snap.write_bytes(b'{"prior": true}')
    baseline = hashlib.sha256(snap.read_bytes()).hexdigest()
    monkeypatch.setitem(
        sys.modules, "anthropic", _fake_anthropic_module({}, "not json at all")
    )
    monkeypatch.setattr(
        mc.urllib.request, "urlopen", lambda url, timeout=0: _Resp(b"<rss/>")
    )
    assert mc.main() == 1
    assert hashlib.sha256(snap.read_bytes()).hexdigest() == baseline
    assert not tmp.exists()
