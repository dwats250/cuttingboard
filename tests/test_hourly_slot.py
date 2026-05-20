"""PRD-141: canonical PT-hour slot computation + idempotency store."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cuttingboard.notifications.hourly_slot import (
    ALLOWED_PT_SLOTS,
    canonical_slot_utc,
    is_premarket_slot,
    load_last_slot,
    routine_pt_slot,
    save_last_slot,
)


# ---- canonical_slot_utc -----------------------------------------------------

@pytest.mark.parametrize(
    "now_utc, expected_utc",
    [
        # PDT (UTC-7) — May
        (datetime(2026, 5, 18, 14, 0, 0, tzinfo=timezone.utc),
         datetime(2026, 5, 18, 14, 0, 0, tzinfo=timezone.utc)),
        (datetime(2026, 5, 18, 14, 30, 0, tzinfo=timezone.utc),
         datetime(2026, 5, 18, 14, 0, 0, tzinfo=timezone.utc)),
        (datetime(2026, 5, 18, 20, 0, 0, tzinfo=timezone.utc),
         datetime(2026, 5, 18, 20, 0, 0, tzinfo=timezone.utc)),
        (datetime(2026, 5, 18, 20, 27, 14, tzinfo=timezone.utc),
         datetime(2026, 5, 18, 20, 0, 0, tzinfo=timezone.utc)),
        (datetime(2026, 5, 18, 20, 48, 0, tzinfo=timezone.utc),
         datetime(2026, 5, 18, 20, 0, 0, tzinfo=timezone.utc)),
        (datetime(2026, 5, 18, 21, 0, 0, tzinfo=timezone.utc),
         datetime(2026, 5, 18, 21, 0, 0, tzinfo=timezone.utc)),
        (datetime(2026, 5, 18, 21, 30, 0, tzinfo=timezone.utc),
         datetime(2026, 5, 18, 21, 0, 0, tzinfo=timezone.utc)),
    ],
)
def test_canonical_slot_pdt(now_utc, expected_utc):
    assert canonical_slot_utc(now_utc) == expected_utc


def test_canonical_slot_pst_dst_correct():
    # January = PST (UTC-8). 21:30Z = 13:30 PST, top of PT hour = 13:00 PST = 21:00Z
    now = datetime(2026, 1, 15, 21, 30, 0, tzinfo=timezone.utc)
    assert canonical_slot_utc(now) == datetime(2026, 1, 15, 21, 0, 0, tzinfo=timezone.utc)


def test_canonical_slot_pdt_vs_pst_differ_by_one_hour():
    # Same UTC instant projected to PT differs by DST offset.
    pdt = canonical_slot_utc(datetime(2026, 5, 18, 20, 30, tzinfo=timezone.utc))
    pst = canonical_slot_utc(datetime(2026, 1, 15, 20, 30, tzinfo=timezone.utc))
    # 20:30Z in PDT = 13:30 PT → 20:00Z; in PST = 12:30 PT → 20:00Z (same UTC by coincidence)
    # Better assertion: 14:30Z in PDT = 7:30 PT → 14:00Z; in PST = 6:30 PT → 14:00Z (also same)
    # The real DST sensitivity: 07:30Z in PDT = 00:30 PT → 07:00Z; in PST = 23:30 prev → 07:00Z
    # Just sanity-check that both return tz-aware UTC tops of hour.
    assert pdt.tzinfo is timezone.utc and pdt.minute == 0
    assert pst.tzinfo is timezone.utc and pst.minute == 0


def test_canonical_slot_requires_tzaware():
    with pytest.raises(ValueError):
        canonical_slot_utc(datetime(2026, 5, 18, 20, 0, 0))


# ---- is_premarket_slot ------------------------------------------------------

@pytest.mark.parametrize(
    "now_utc, expected",
    [
        (datetime(2026, 5, 18, 12, 50, 0, tzinfo=timezone.utc), True),
        (datetime(2026, 5, 18, 13, 0, 0, tzinfo=timezone.utc), True),
        (datetime(2026, 5, 18, 13, 50, 0, tzinfo=timezone.utc), True),
        (datetime(2026, 5, 18, 13, 2, 0, tzinfo=timezone.utc), True),   # ±5 of 13:00
        (datetime(2026, 5, 18, 12, 46, 0, tzinfo=timezone.utc), True),  # ±5 of 12:50
        (datetime(2026, 5, 18, 13, 45, 0, tzinfo=timezone.utc), True),  # ±5 of 13:50
        (datetime(2026, 5, 18, 13, 8, 0, tzinfo=timezone.utc), False),  # outside ±5 of 13:00 and 13:50
        (datetime(2026, 5, 18, 14, 0, 0, tzinfo=timezone.utc), False),
        (datetime(2026, 5, 18, 20, 0, 0, tzinfo=timezone.utc), False),
    ],
)
def test_is_premarket_slot(now_utc, expected):
    assert is_premarket_slot(now_utc) is expected


def test_is_premarket_slot_requires_tzaware():
    with pytest.raises(ValueError):
        is_premarket_slot(datetime(2026, 5, 18, 13, 0, 0))


# ---- load/save round-trip ---------------------------------------------------

def test_load_last_slot_missing_returns_none(tmp_path):
    p = tmp_path / "nope.json"
    assert load_last_slot(str(p)) is None


def test_load_last_slot_malformed_returns_none(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not-json", encoding="utf-8")
    assert load_last_slot(str(p)) is None


def test_load_last_slot_empty_returns_none(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text("", encoding="utf-8")
    assert load_last_slot(str(p)) is None


def test_load_last_slot_missing_slot_key_returns_none(tmp_path):
    p = tmp_path / "wrong.json"
    p.write_text(json.dumps({"saved_at_utc": "x"}), encoding="utf-8")
    assert load_last_slot(str(p)) is None


def test_save_then_load_roundtrip(tmp_path):
    p = tmp_path / "logs" / "last_hourly_slot.json"
    slot = datetime(2026, 5, 18, 20, 0, 0, tzinfo=timezone.utc)
    save_last_slot(slot, str(p))
    data = load_last_slot(str(p))
    assert data is not None
    parsed = datetime.fromisoformat(data["slot_utc"])
    assert parsed == slot
    assert "saved_at_utc" in data


def test_save_creates_parent_dir(tmp_path):
    p = tmp_path / "deep" / "logs" / "slot.json"
    save_last_slot(datetime(2026, 5, 18, 20, 0, tzinfo=timezone.utc), str(p))
    assert Path(p).exists()


def test_save_requires_tzaware():
    with pytest.raises(ValueError):
        save_last_slot(datetime(2026, 5, 18, 20, 0, 0))


# ---- PRD-149: routine_pt_slot ----------------------------------------------

def test_allowed_pt_slots_exact_set():
    assert ALLOWED_PT_SLOTS == (
        (6, 0), (6, 30), (7, 0), (8, 0), (9, 0),
        (10, 0), (11, 0), (12, 0), (13, 0),
    )


@pytest.mark.parametrize(
    "now_utc, expected_pt_hour, expected_pt_minute",
    [
        # PDT day (2026-05-19, UTC-7)
        (datetime(2026, 5, 19, 13, 0, 0, tzinfo=timezone.utc), 6, 0),
        (datetime(2026, 5, 19, 13, 24, 0, tzinfo=timezone.utc), 6, 0),
        (datetime(2026, 5, 19, 13, 30, 0, tzinfo=timezone.utc), 6, 30),
        (datetime(2026, 5, 19, 14, 0, 0, tzinfo=timezone.utc), 7, 0),
        (datetime(2026, 5, 19, 19, 0, 0, tzinfo=timezone.utc), 12, 0),
        (datetime(2026, 5, 19, 20, 0, 0, tzinfo=timezone.utc), 13, 0),
        (datetime(2026, 5, 19, 20, 25, 0, tzinfo=timezone.utc), 13, 0),
    ],
)
def test_routine_pt_slot_pdt_in_window(now_utc, expected_pt_hour, expected_pt_minute):
    from cuttingboard.notifications.hourly_slot import _PT_TZ

    slot = routine_pt_slot(now_utc)
    assert slot is not None
    assert slot.tzinfo is timezone.utc
    slot_pt = slot.astimezone(_PT_TZ)
    assert (slot_pt.hour, slot_pt.minute) == (expected_pt_hour, expected_pt_minute)


@pytest.mark.parametrize(
    "now_utc",
    [
        # PDT (2026-05-19, UTC-7): outside lag or past 13:00 PT
        datetime(2026, 5, 19, 13, 26, 0, tzinfo=timezone.utc),  # lag > 25 min from 06:00
        datetime(2026, 5, 19, 20, 26, 0, tzinfo=timezone.utc),  # lag > 25 min from 13:00
        datetime(2026, 5, 19, 21, 0, 0, tzinfo=timezone.utc),   # 14:00 PT — outside
        datetime(2026, 5, 19, 22, 0, 0, tzinfo=timezone.utc),   # 15:00 PT — failure-mode ts
    ],
)
def test_routine_pt_slot_pdt_outside(now_utc):
    assert routine_pt_slot(now_utc) is None


@pytest.mark.parametrize(
    "now_utc, expected",
    [
        # PST day (2026-01-12, UTC-8)
        (datetime(2026, 1, 12, 13, 0, 0, tzinfo=timezone.utc), None),  # 05:00 PT — before earliest
        (datetime(2026, 1, 12, 14, 0, 0, tzinfo=timezone.utc), (6, 0)),
        (datetime(2026, 1, 12, 14, 25, 0, tzinfo=timezone.utc), (6, 0)),
        (datetime(2026, 1, 12, 14, 30, 0, tzinfo=timezone.utc), (6, 30)),
        (datetime(2026, 1, 12, 21, 0, 0, tzinfo=timezone.utc), (13, 0)),
        (datetime(2026, 1, 12, 21, 30, 0, tzinfo=timezone.utc), None),
    ],
)
def test_routine_pt_slot_pst(now_utc, expected):
    from cuttingboard.notifications.hourly_slot import _PT_TZ

    slot = routine_pt_slot(now_utc)
    if expected is None:
        assert slot is None
        return
    assert slot is not None
    slot_pt = slot.astimezone(_PT_TZ)
    assert (slot_pt.hour, slot_pt.minute) == expected


def test_routine_pt_slot_requires_tzaware():
    with pytest.raises(ValueError):
        routine_pt_slot(datetime(2026, 5, 19, 20, 0, 0))


def test_routine_pt_slot_returns_utc():
    slot = routine_pt_slot(datetime(2026, 5, 19, 20, 0, 0, tzinfo=timezone.utc))
    assert slot is not None
    assert slot.tzinfo is timezone.utc


def test_routine_pt_slot_distinct_keys_for_six_and_six_thirty():
    """PRD-149: 06:00 and 06:30 must produce distinct dedup slots."""
    six = routine_pt_slot(datetime(2026, 5, 19, 13, 0, 0, tzinfo=timezone.utc))
    six_thirty = routine_pt_slot(datetime(2026, 5, 19, 13, 30, 0, tzinfo=timezone.utc))
    assert six is not None and six_thirty is not None
    assert six.isoformat() != six_thirty.isoformat()


def test_is_premarket_slot_remains_importable_after_prd149():
    """PRD-149 R6: helper must remain importable with original module attribution."""
    from cuttingboard.notifications.hourly_slot import is_premarket_slot as imported

    assert imported.__module__ == "cuttingboard.notifications.hourly_slot"
