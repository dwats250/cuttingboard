"""Tests for PRD-073-PATCH — Renderer boundary isolation."""

from __future__ import annotations

import builtins as _builtins
import cuttingboard.delivery.dashboard_renderer as _renderer_module

import pytest

from cuttingboard.delivery.dashboard_renderer import render_dashboard_html

from tests.dash_helpers import _payload, _run


# ---------------------------------------------------------------------------
# PRD-073-PATCH — R4-PATCH: Renderer boundary isolation
# ---------------------------------------------------------------------------

def test_contract_module_not_in_renderer_namespace() -> None:
    assert 'contract' not in vars(_renderer_module)


def test_contract_import_absent_from_renderer_source() -> None:
    import inspect
    import re
    source = inspect.getsource(_renderer_module)
    import_lines = [
        line for line in source.splitlines()
        if re.match(r'\s*(import|from)\s+.*\bcontract\b', line)
    ]
    assert not import_lines, f"dashboard_renderer imports contract: {import_lines}"


def test_render_does_not_open_contract_file(monkeypatch: pytest.MonkeyPatch) -> None:
    opened_paths: list[str] = []
    real_open = _builtins.open

    def tracking_open(file, *args, **kwargs):
        opened_paths.append(str(file))
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(_builtins, 'open', tracking_open)
    render_dashboard_html(_payload(), _run())

    contract_paths = [p for p in opened_paths if 'contract' in p.lower()]
    assert not contract_paths, f"render accessed contract paths: {contract_paths}"
