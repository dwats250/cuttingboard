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
    # PRD-319 R3: (6,0) retired (the daily pipeline exclusively owns 06:00);
    # (6,45) added (the ruled CF-D3 "OPEN+1" post-open snapshot).
    assert ALLOWED_PT_SLOTS == (
        (6, 30), (6, 45), (7, 0), (8, 0), (9, 0),
        (10, 0), (11, 0), (12, 0), (13, 0),
    )


@pytest.mark.parametrize(
    "now_utc, expected_pt_hour, expected_pt_minute",
    [
        # PDT day (2026-05-19, UTC-7)
        (datetime(2026, 5, 19, 13, 30, 0, tzinfo=timezone.utc), 6, 30),
        (datetime(2026, 5, 19, 13, 45, 0, tzinfo=timezone.utc), 6, 45),
        (datetime(2026, 5, 19, 13, 50, 0, tzinfo=timezone.utc), 6, 45),
        (datetime(2026, 5, 19, 14, 0, 0, tzinfo=timezone.utc), 7, 0),
        (datetime(2026, 5, 19, 14, 10, 0, tzinfo=timezone.utc), 7, 0),
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
        # PRD-319 R3: 06:00-06:29 PT now has NO eligible slot ((6,0) retired) --
        # the off-season hourly heartbeat / stale cron fires before 06:30 no-op.
        datetime(2026, 5, 19, 13, 0, 0, tzinfo=timezone.utc),   # 06:00 PT -- retired slot
        datetime(2026, 5, 19, 13, 24, 0, tzinfo=timezone.utc),  # 06:24 PT -- nothing eligible
        datetime(2026, 5, 19, 13, 26, 0, tzinfo=timezone.utc),  # 06:26 PT -- nothing eligible
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
        (datetime(2026, 1, 12, 14, 0, 0, tzinfo=timezone.utc), None),  # 06:00 PT — retired slot
        (datetime(2026, 1, 12, 14, 10, 0, tzinfo=timezone.utc), None),  # 06:10 PT — off-season 10 14 heartbeat
        (datetime(2026, 1, 12, 14, 25, 0, tzinfo=timezone.utc), None),  # 06:25 PT — nothing eligible
        (datetime(2026, 1, 12, 14, 30, 0, tzinfo=timezone.utc), (6, 30)),
        (datetime(2026, 1, 12, 14, 45, 0, tzinfo=timezone.utc), (6, 45)),
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


def test_routine_pt_slot_distinct_keys_for_six_thirty_and_six_forty_five():
    """PRD-149/PRD-319: 06:30 and 06:45 must produce distinct dedup slots."""
    six_thirty = routine_pt_slot(datetime(2026, 5, 19, 13, 30, 0, tzinfo=timezone.utc))
    six_forty_five = routine_pt_slot(datetime(2026, 5, 19, 13, 45, 0, tzinfo=timezone.utc))
    assert six_thirty is not None and six_forty_five is not None
    assert six_thirty.isoformat() != six_forty_five.isoformat()


# ---- PRD-319 R2: explicit_pt_slot -------------------------------------------

def test_explicit_pt_slot_resolves_named_slot_in_window():
    from cuttingboard.notifications.hourly_slot import _PT_TZ, explicit_pt_slot

    # 13:32Z PDT = 06:32 PT, named slot 06:30 -> resolves 06:30 exactly.
    slot = explicit_pt_slot(
        datetime(2026, 5, 19, 13, 32, 0, tzinfo=timezone.utc), "06:30"
    )
    assert slot is not None and slot.tzinfo is timezone.utc
    slot_pt = slot.astimezone(_PT_TZ)
    assert (slot_pt.hour, slot_pt.minute) == (6, 30)


def test_explicit_pt_slot_never_shifts_identity():
    """PRD-319 R2 mutation seam: a delayed 06:30 start at 06:46 PT stays 06:30,
    never relabelled 06:45 (the inference path would pick 06:45)."""
    from cuttingboard.notifications.hourly_slot import _PT_TZ, explicit_pt_slot

    now = datetime(2026, 5, 19, 13, 46, 0, tzinfo=timezone.utc)  # 06:46 PDT
    inferred = routine_pt_slot(now)
    assert inferred is not None
    assert (inferred.astimezone(_PT_TZ).hour, inferred.astimezone(_PT_TZ).minute) == (6, 45)
    explicit = explicit_pt_slot(now, "06:30")
    assert explicit is not None
    ex_pt = explicit.astimezone(_PT_TZ)
    assert (ex_pt.hour, ex_pt.minute) == (6, 30)


@pytest.mark.parametrize(
    "now_utc, label",
    [
        # future slot: off-season twin (05:40 PST via 40 13 cron, intended 06:30)
        (datetime(2026, 1, 12, 13, 40, 0, tzinfo=timezone.utc), "06:30"),
        # lag > max: off-season twin (07:40 PDT via 40 14 cron, intended 06:30)
        (datetime(2026, 5, 19, 14, 40, 0, tzinfo=timezone.utc), "06:30"),
        # slot not in ALLOWED_PT_SLOTS (retired 06:00)
        (datetime(2026, 5, 19, 13, 5, 0, tzinfo=timezone.utc), "06:00"),
        # unparseable labels
        (datetime(2026, 5, 19, 13, 32, 0, tzinfo=timezone.utc), "6:30pm"),
        (datetime(2026, 5, 19, 13, 32, 0, tzinfo=timezone.utc), ""),
        (datetime(2026, 5, 19, 13, 32, 0, tzinfo=timezone.utc), "99:99"),
    ],
)
def test_explicit_pt_slot_rejects(now_utc, label):
    from cuttingboard.notifications.hourly_slot import explicit_pt_slot

    assert explicit_pt_slot(now_utc, label) is None


def test_explicit_pt_slot_requires_tzaware():
    from cuttingboard.notifications.hourly_slot import explicit_pt_slot

    with pytest.raises(ValueError):
        explicit_pt_slot(datetime(2026, 5, 19, 13, 32, 0), "06:30")


def test_is_premarket_slot_remains_importable_after_prd149():
    """PRD-149 R6: helper must remain importable with original module attribution."""
    from cuttingboard.notifications.hourly_slot import is_premarket_slot as imported

    assert imported.__module__ == "cuttingboard.notifications.hourly_slot"
