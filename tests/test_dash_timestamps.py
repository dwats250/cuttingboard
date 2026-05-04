"""PRD-081: focused tests for format_dashboard_timestamp and no-mutation guarantee."""
from __future__ import annotations

import copy

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    format_dashboard_timestamp,
    render_dashboard_html,
)
from tests.dash_helpers import _payload, _run


# R1 — Zulu timestamp -> PT + UTC label
def test_zulu_produces_pt_and_utc():
    pacific, original = format_dashboard_timestamp("2026-05-04T18:11:28Z")
    assert "PT" in pacific
    assert pacific.startswith("2026-05-04")
    assert "UTC" in original
    assert "2026-05-04" in original


# R1 — offset timestamp -> PT + readable original
def test_offset_produces_pt():
    pacific, original = format_dashboard_timestamp("2026-05-04T18:11:28+00:00")
    assert "PT" in pacific
    assert pacific.startswith("2026-05-04")
    assert original  # non-empty, readable


# R1 — invalid timestamp -> no exception, pacific_line is empty
def test_invalid_timestamp_no_crash():
    pacific, original = format_dashboard_timestamp("not-a-timestamp")
    assert pacific == ""
    assert original  # cleaned fallback is non-empty


# R4 — input value is never mutated through render
def test_no_mutation_through_render(tmp_path):
    payload = _payload()
    payload["meta"]["timestamp"] = "2026-05-04T18:11:28Z"
    run = _run()
    before = copy.deepcopy(payload["meta"]["timestamp"])
    render_dashboard_html(payload, run)
    assert payload["meta"]["timestamp"] == before
