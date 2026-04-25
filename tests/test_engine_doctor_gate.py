"""
Tests for PRD-020: engine doctor gate system.

Covers:
- config.get_engine_doctor_runtime_gate()
- runtime._run_engine_health_gate() behavior (disabled and enabled paths)
- cli_main() aborts before execute_run when gate triggers
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cuttingboard import config
from cuttingboard.runtime import _run_engine_health_gate


# ── config reader ─────────────────────────────────────────────────────────────

def test_runtime_gate_defaults_false_when_section_absent(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text("[flow]\ndata_path = \"\"\n")
    assert config.get_engine_doctor_runtime_gate(toml) is False


def test_runtime_gate_reads_false_explicitly(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text("[engine_doctor]\nruntime_gate_enabled = false\n")
    assert config.get_engine_doctor_runtime_gate(toml) is False


def test_runtime_gate_reads_true(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text("[engine_doctor]\nruntime_gate_enabled = true\n")
    assert config.get_engine_doctor_runtime_gate(toml) is True


def test_runtime_gate_defaults_false_when_file_missing(tmp_path):
    assert config.get_engine_doctor_runtime_gate(tmp_path / "nonexistent.toml") is False


# ── _run_engine_health_gate ───────────────────────────────────────────────────

def test_gate_noop_when_disabled(tmp_path):
    toml = tmp_path / "config.toml"
    toml.write_text("[engine_doctor]\nruntime_gate_enabled = false\n")

    with patch("cuttingboard.config.get_engine_doctor_runtime_gate", return_value=False):
        # Must not call subprocess and must not raise
        with patch("subprocess.run") as mock_run:
            _run_engine_health_gate()
            mock_run.assert_not_called()


def test_gate_noop_when_section_absent():
    with patch("cuttingboard.config.get_engine_doctor_runtime_gate", return_value=False):
        with patch("subprocess.run") as mock_run:
            _run_engine_health_gate()
            mock_run.assert_not_called()


def test_gate_proceeds_when_doctor_exits_zero():
    ok_report = json.dumps({"status": "OK", "modules": {}, "tests": {}, "runtime_files": {}, "dependencies": {}, "impact": {}})
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ok_report
    mock_result.stderr = ""

    with patch("cuttingboard.config.get_engine_doctor_runtime_gate", return_value=True):
        with patch("subprocess.run", return_value=mock_result):
            _run_engine_health_gate()  # must not raise


def test_gate_aborts_on_import_failure_exit_code():
    fail_report = json.dumps({"status": "FAIL"})
    mock_result = MagicMock()
    mock_result.returncode = 2  # import failure
    mock_result.stdout = fail_report
    mock_result.stderr = ""

    with patch("cuttingboard.config.get_engine_doctor_runtime_gate", return_value=True):
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                _run_engine_health_gate()
            assert exc_info.value.code == 2


def test_gate_aborts_on_circular_dep_exit_code():
    mock_result = MagicMock()
    mock_result.returncode = 3
    mock_result.stdout = json.dumps({"status": "FAIL"})
    mock_result.stderr = ""

    with patch("cuttingboard.config.get_engine_doctor_runtime_gate", return_value=True):
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                _run_engine_health_gate()
            assert exc_info.value.code == 3


def test_gate_aborts_on_baseline_mismatch_exit_code():
    mock_result = MagicMock()
    mock_result.returncode = 5
    mock_result.stdout = json.dumps({"status": "FAIL"})
    mock_result.stderr = ""

    with patch("cuttingboard.config.get_engine_doctor_runtime_gate", return_value=True):
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                _run_engine_health_gate()
            assert exc_info.value.code == 5


def test_gate_aborts_on_malformed_json_output():
    mock_result = MagicMock()
    mock_result.returncode = 2
    mock_result.stdout = "not json"
    mock_result.stderr = ""

    with patch("cuttingboard.config.get_engine_doctor_runtime_gate", return_value=True):
        with patch("subprocess.run", return_value=mock_result):
            with pytest.raises(SystemExit) as exc_info:
                _run_engine_health_gate()
            assert exc_info.value.code == 2


def test_gate_deterministic_same_exit_same_decision():
    """Same exit code always produces the same abort behavior."""
    for exit_code in [1, 2, 3, 4, 5]:
        mock_result = MagicMock()
        mock_result.returncode = exit_code
        mock_result.stdout = json.dumps({"status": "FAIL"})
        mock_result.stderr = ""

        with patch("cuttingboard.config.get_engine_doctor_runtime_gate", return_value=True):
            with patch("subprocess.run", return_value=mock_result):
                with pytest.raises(SystemExit) as exc_info:
                    _run_engine_health_gate()
                assert exc_info.value.code == exit_code


# ── cli_main integration ──────────────────────────────────────────────────────

def test_cli_main_aborts_before_execute_run_when_gate_fails():
    """cli_main must not call execute_run when the health gate triggers."""
    mock_result = MagicMock()
    mock_result.returncode = 2
    mock_result.stdout = json.dumps({"status": "FAIL"})
    mock_result.stderr = ""

    with patch("cuttingboard.config.get_engine_doctor_runtime_gate", return_value=True):
        with patch("subprocess.run", return_value=mock_result):
            with patch("cuttingboard.runtime.execute_run") as mock_execute:
                from cuttingboard.runtime import cli_main
                with pytest.raises(SystemExit):
                    cli_main(["--mode", "live"])
                mock_execute.assert_not_called()


def test_cli_main_calls_execute_run_when_gate_disabled():
    """cli_main proceeds to execute_run when gate is disabled."""
    mock_summary = {
        "status": "SUCCESS",
        "warnings": [],
        "errors": [],
    }

    with patch("cuttingboard.config.get_engine_doctor_runtime_gate", return_value=False):
        with patch("cuttingboard.runtime.execute_run", return_value=mock_summary) as mock_execute:
            from cuttingboard.runtime import cli_main
            cli_main(["--mode", "live"])
            mock_execute.assert_called_once()
