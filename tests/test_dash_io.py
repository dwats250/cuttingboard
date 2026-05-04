"""Tests for PRD-055 — dashboard renderer: File I/O and loading."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    _load_json_optional,
    _resolve_previous_run,
    main,
    render_dashboard_html,
)

from tests.dash_helpers import _payload, _run


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

def test_reads_required_files(tmp_path: Path) -> None:
    payload_file = tmp_path / "latest_payload.json"
    run_file     = tmp_path / "latest_run.json"
    out_file     = tmp_path / "dashboard.html"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")
    main(payload_path=payload_file, run_path=run_file, output_path=out_file, logs_dir=tmp_path)
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "<html" in content
    assert "dashboard-header" in content


def test_missing_payload_fails(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="missing"):
        main(
            payload_path=tmp_path / "no_payload.json",
            run_path=tmp_path / "run.json",
            output_path=tmp_path / "out.html",
            logs_dir=tmp_path,
        )


def test_missing_run_fails(tmp_path: Path) -> None:
    payload_file = tmp_path / "latest_payload.json"
    payload_file.write_text(json.dumps(_payload()), encoding="utf-8")
    with pytest.raises(RuntimeError, match="missing"):
        main(
            payload_path=payload_file,
            run_path=tmp_path / "no_run.json",
            output_path=tmp_path / "out.html",
            logs_dir=tmp_path,
        )


def test_invalid_json_fails(tmp_path: Path) -> None:
    bad      = tmp_path / "bad.json"
    run_file = tmp_path / "run.json"
    bad.write_text("{not valid json", encoding="utf-8")
    run_file.write_text(json.dumps(_run()), encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid JSON"):
        main(payload_path=bad, run_path=run_file, output_path=tmp_path / "out.html", logs_dir=tmp_path)


def test_load_json_optional_returns_none_when_absent(tmp_path: Path) -> None:
    assert _load_json_optional(tmp_path / "missing.json") is None


def test_load_json_optional_raises_on_invalid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Invalid JSON"):
        _load_json_optional(bad)


def test_load_json_optional_returns_dict_when_valid(tmp_path: Path) -> None:
    f = tmp_path / "ok.json"
    f.write_text('{"key": "val"}', encoding="utf-8")
    result = _load_json_optional(f)
    assert result == {"key": "val"}
