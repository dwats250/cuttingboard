"""Hourly delivery liveness probe (completion PR, 2026-09-09).

Executes the PRODUCTION ``scripts/check_hourly_liveness.py`` (loaded by path,
stdlib only) over the due/evidence matrix: 07:59 vs 08:00 PT in both DST
offsets, afternoon, weekend, a valid published record, and every RED class
(absent, malformed, naive, future, previous-day, non-canonical slot,
inconsistent timestamps). A real temporary git repository proves the evidence
is the exact fetched ``origin/publish`` blob and that a main-only copy can
never rescue missing publish evidence.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "check_hourly_liveness.py"

_SPEC = importlib.util.spec_from_file_location("check_hourly_liveness", SCRIPT)
liveness = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
sys.modules[_SPEC.name] = liveness  # dataclasses resolve postponed annotations via sys.modules
_SPEC.loader.exec_module(liveness)


def _utc(y: int, mo: int, d: int, h: int, mi: int, s: int = 0) -> datetime:
    return datetime(y, mo, d, h, mi, s, tzinfo=timezone.utc)


def _record(slot_utc: datetime, saved_at_utc: datetime | None = None) -> str:
    saved = saved_at_utc if saved_at_utc is not None else slot_utc + timedelta(minutes=4)
    return json.dumps({"slot_utc": slot_utc.isoformat(), "saved_at_utc": saved.isoformat()})


def _evidence(text: str) -> liveness.Evidence:
    return liveness.Evidence(sha="0123456789abcdef", text=text)


def _never_called() -> liveness.Evidence:
    raise AssertionError("evidence loader must not be called when NOT_DUE")


def _absent() -> liveness.Evidence:
    raise liveness.SourceError("logs/last_hourly_slot.json absent on origin/publish@deadbeef")


# PDT weekday: Tue 2026-05-19 (UTC-7). PST weekday: Mon 2026-01-12 (UTC-8).
PDT_DAY = (2026, 5, 19)
PST_DAY = (2026, 1, 12)


# --- Due threshold -----------------------------------------------------------

@pytest.mark.parametrize(
    "now_utc",
    [
        _utc(*PDT_DAY, 14, 59),  # 07:59 PDT
        _utc(*PST_DAY, 15, 59),  # 07:59 PST
        _utc(*PDT_DAY, 13, 30),  # 06:30 PDT (first slot, not yet due)
    ],
)
def test_before_threshold_is_not_due_and_never_fetches(now_utc: datetime) -> None:
    verdict = liveness.evaluate(now_utc, _never_called)
    assert verdict.state == liveness.NOT_DUE
    assert verdict.exit_code == 0
    assert "08:00" in verdict.reason


@pytest.mark.parametrize(
    "now_utc",
    [
        _utc(*PDT_DAY, 15, 0),   # exactly 08:00 PDT
        _utc(*PST_DAY, 16, 0),   # exactly 08:00 PST
        _utc(*PDT_DAY, 23, 30),  # 16:30 PDT afternoon -- no upper cutoff hides starvation
    ],
)
def test_at_or_after_threshold_is_due_and_absent_evidence_is_red(now_utc: datetime) -> None:
    verdict = liveness.evaluate(now_utc, _absent)
    assert verdict.state == liveness.RED
    assert verdict.exit_code == 1
    assert "no published evidence" in verdict.reason


@pytest.mark.parametrize(
    "now_utc",
    [
        _utc(2026, 5, 16, 18, 0),  # Saturday 11:00 PDT
        _utc(2026, 5, 17, 18, 0),  # Sunday 11:00 PDT
        _utc(2026, 1, 10, 20, 0),  # Saturday 12:00 PST
    ],
)
def test_weekend_is_not_due_even_without_evidence(now_utc: datetime) -> None:
    verdict = liveness.evaluate(now_utc, _never_called)
    assert verdict.state == liveness.NOT_DUE
    assert verdict.reason == "weekend"


# --- Valid evidence ------------------------------------------------------------

def test_valid_same_day_record_is_healthy_with_publish_sha() -> None:
    now = _utc(*PDT_DAY, 15, 10)
    slot = _utc(*PDT_DAY, 14, 0)  # 07:00 PDT
    verdict = liveness.evaluate(now, lambda: _evidence(_record(slot)))
    assert verdict.state == liveness.HEALTHY
    assert verdict.exit_code == 0
    assert verdict.details["publish_sha"] == "0123456789abcdef"
    assert "07:00" in verdict.reason


def test_valid_record_pst_season_is_healthy() -> None:
    now = _utc(*PST_DAY, 16, 5)
    slot = _utc(*PST_DAY, 14, 30)  # 06:30 PST
    verdict = liveness.evaluate(now, lambda: _evidence(_record(slot)))
    assert verdict.state == liveness.HEALTHY


def test_healthy_halt_delivery_is_delivery_not_failure() -> None:
    """The runtime persists last_hourly_slot after ANY successful send,
    including a market-stress safety HALT (SUMMARY_STATUS_SUCCESS). The probe
    reads delivery evidence, so a HALT day is HEALTHY, never RED."""
    now = _utc(*PDT_DAY, 15, 30)
    verdict = liveness.evaluate(now, lambda: _evidence(_record(_utc(*PDT_DAY, 13, 45))))
    assert verdict.state == liveness.HEALTHY


def test_manual_same_day_hourly_success_satisfies() -> None:
    """A valid manual (forced) same-day hourly success writes the same record
    shape; the probe cannot and does not distinguish it. Product liveness."""
    now = _utc(*PDT_DAY, 20, 30)
    verdict = liveness.evaluate(now, lambda: _evidence(_record(_utc(*PDT_DAY, 19, 0))))
    assert verdict.state == liveness.HEALTHY


# --- RED classes -----------------------------------------------------------------

NOW_DUE = _utc(*PDT_DAY, 15, 30)  # 08:30 PDT


@pytest.mark.parametrize(
    "text, fragment",
    [
        ("{not json", "malformed JSON"),
        ("[]", "not a JSON object"),
        ("{}", "slot_utc missing"),
        (json.dumps({"slot_utc": "2026-05-19T14:00:00+00:00"}), "saved_at_utc missing"),
        (json.dumps({"slot_utc": "2026-05-19T14:00:00", "saved_at_utc": "2026-05-19T14:04:00+00:00"}), "naive"),
        (json.dumps({"slot_utc": "2026-05-19T14:00:00+00:00", "saved_at_utc": "2026-05-19T14:04:00"}), "naive"),
        (json.dumps({"slot_utc": "yesterday", "saved_at_utc": "2026-05-19T14:04:00+00:00"}), "not ISO-8601"),
        (json.dumps({"slot_utc": 1, "saved_at_utc": 2}), "not a string"),
    ],
)
def test_malformed_or_naive_record_is_red(text: str, fragment: str) -> None:
    verdict = liveness.evaluate(NOW_DUE, lambda: _evidence(text))
    assert verdict.state == liveness.RED, verdict
    assert fragment in verdict.reason


def test_previous_day_record_is_stale_red() -> None:
    slot = _utc(2026, 5, 18, 14, 0)  # Monday 07:00 PDT, probe runs Tuesday
    verdict = liveness.evaluate(NOW_DUE, lambda: _evidence(_record(slot)))
    assert verdict.state == liveness.RED
    assert "stale" in verdict.reason and "2026-05-18" in verdict.reason


def test_record_from_2026_08_26_style_starvation_is_red_weeks_later() -> None:
    """The observed production state: last delivery 2026-08-26, probe weeks later."""
    slot = _utc(2026, 8, 26, 16, 0)
    now = _utc(2026, 9, 9, 16, 0)  # Wednesday 09:00 PDT
    verdict = liveness.evaluate(now, lambda: _evidence(_record(slot)))
    assert verdict.state == liveness.RED
    assert "stale" in verdict.reason


def test_future_dated_record_is_red() -> None:
    slot = _utc(2026, 5, 20, 14, 0)  # tomorrow
    verdict = liveness.evaluate(NOW_DUE, lambda: _evidence(_record(slot)))
    assert verdict.state == liveness.RED
    assert "future" in verdict.reason


def test_saved_after_now_is_future_red() -> None:
    slot = _utc(*PDT_DAY, 14, 0)
    saved = NOW_DUE + timedelta(minutes=1)
    verdict = liveness.evaluate(NOW_DUE, lambda: _evidence(_record(slot, saved)))
    assert verdict.state == liveness.RED
    assert "future record" in verdict.reason


def test_saved_before_slot_is_inconsistent_red() -> None:
    slot = _utc(*PDT_DAY, 14, 0)
    saved = slot - timedelta(minutes=1)
    verdict = liveness.evaluate(NOW_DUE, lambda: _evidence(_record(slot, saved)))
    assert verdict.state == liveness.RED
    assert "inconsistent" in verdict.reason


@pytest.mark.parametrize(
    "slot",
    [
        _utc(*PDT_DAY, 14, 30),      # 07:30 PDT -- not an ALLOWED_PT_SLOTS member
        _utc(*PDT_DAY, 13, 0),       # 06:00 PDT -- retired hourly slot (pipeline-owned)
        _utc(*PDT_DAY, 14, 0, 7),    # 07:00:07 -- seconds are never canonical
        _utc(*PDT_DAY, 21, 0),       # 14:00 PDT -- after the last slot
    ],
)
def test_non_canonical_slot_is_red(slot: datetime) -> None:
    verdict = liveness.evaluate(NOW_DUE, lambda: _evidence(_record(slot)))
    assert verdict.state == liveness.RED
    assert "non-canonical" in verdict.reason


def test_allowed_slots_come_from_the_production_leaf() -> None:
    """Mutation seam: the probe reuses hourly_slot.py's ALLOWED_PT_SLOTS rather
    than a duplicate table, so the two can never drift apart."""
    from cuttingboard.notifications.hourly_slot import ALLOWED_PT_SLOTS

    assert tuple(liveness.ALLOWED_PT_SLOTS) == tuple(ALLOWED_PT_SLOTS)


def test_probe_never_uses_the_restore_helper_or_working_tree() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    body = text.split('"""', 2)[2]  # strip the module docstring (which names the helper)
    assert "ci_restore_publish_state" not in body
    assert "origin/" in body and "git" in body
    # No provider / runtime / notifications package import: stdlib + leaf only.
    for forbidden in ("from cuttingboard", "import cuttingboard", "polygon", "telegram", "requests"):
        assert forbidden not in body, forbidden


# --- Real git extraction: exact fetched blob, main copy never rescues ----------

def _git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)
    return proc.stdout.strip()


@pytest.fixture()
def repo_with_origin(tmp_path: Path) -> tuple[Path, Path]:
    """A working clone whose origin has main (with a FROZEN record) and publish."""
    origin = tmp_path / "origin.git"
    seed = tmp_path / "seed"
    seed.mkdir()
    _git(["init", "-q", "-b", "main"], seed)
    _git(["config", "user.email", "t@example.invalid"], seed)
    _git(["config", "user.name", "t"], seed)
    (seed / "logs").mkdir()
    # main carries a frozen (valid-looking, same-day) record -- the trap the
    # restore helper's "keeping main's copy" fallback would fall into.
    (seed / "logs" / "last_hourly_slot.json").write_text(_record(_utc(*PDT_DAY, 14, 0)), encoding="utf-8")
    _git(["add", "-A"], seed)
    _git(["commit", "-q", "-m", "main frozen record"], seed)
    _git(["init", "-q", "--bare", str(origin)], tmp_path)
    _git(["remote", "add", "origin", str(origin)], seed)
    _git(["push", "-q", "origin", "main"], seed)
    clone = tmp_path / "clone"
    _git(["clone", "-q", str(origin), str(clone)], tmp_path)
    return clone, seed


def _publish(seed: Path, record_text: str | None) -> str:
    """Create/replace the publish branch on origin; None = branch WITHOUT the path."""
    _git(["checkout", "-q", "-B", "publish"], seed)
    target = seed / "logs" / "last_hourly_slot.json"
    if record_text is None:
        target.unlink()
    else:
        target.write_text(record_text, encoding="utf-8")
    _git(["add", "-A"], seed)
    _git(["commit", "-q", "--allow-empty", "-m", "publish"], seed)
    _git(["push", "-q", "-f", "origin", "publish"], seed)
    return _git(["rev-parse", "HEAD"], seed)


def test_git_extraction_reads_exact_publish_blob(repo_with_origin) -> None:
    clone, seed = repo_with_origin
    sha = _publish(seed, _record(_utc(*PDT_DAY, 14, 30)))  # deliberately NON-canonical on publish
    evidence = liveness.read_published_record("publish", "logs/last_hourly_slot.json", clone)
    assert evidence.sha == sha
    assert json.loads(evidence.text)["slot_utc"] == _utc(*PDT_DAY, 14, 30).isoformat()
    # And the probe judges THAT blob, not main's canonical one.
    verdict = liveness.evaluate(NOW_DUE, lambda: evidence)
    assert verdict.state == liveness.RED and "non-canonical" in verdict.reason


def test_main_only_record_never_rescues_missing_publish_path(repo_with_origin) -> None:
    clone, seed = repo_with_origin
    _publish(seed, None)  # publish exists but lacks the path; main still has a valid record
    with pytest.raises(liveness.SourceError, match="absent on origin/publish"):
        liveness.read_published_record("publish", "logs/last_hourly_slot.json", clone)
    verdict = liveness.evaluate(
        NOW_DUE, lambda: liveness.read_published_record("publish", "logs/last_hourly_slot.json", clone)
    )
    assert verdict.state == liveness.RED
    assert "no published evidence" in verdict.reason


def test_absent_publish_branch_is_red_when_due(repo_with_origin) -> None:
    clone, _seed = repo_with_origin  # no publish branch pushed at all
    verdict = liveness.evaluate(
        NOW_DUE, lambda: liveness.read_published_record("publish", "logs/last_hourly_slot.json", clone)
    )
    assert verdict.state == liveness.RED
    assert "fetch of origin/publish failed" in verdict.reason


def test_cli_end_to_end_exit_codes(repo_with_origin) -> None:
    clone, seed = repo_with_origin
    _publish(seed, _record(_utc(*PDT_DAY, 14, 0)))
    base = ["python3", str(SCRIPT), "--repo-root", str(clone), "--branch", "publish"]
    healthy = subprocess.run([*base, "--now", NOW_DUE.isoformat()], capture_output=True, text=True)
    assert healthy.returncode == 0, healthy.stderr
    assert healthy.stdout.startswith("hourly-liveness: HEALTHY")
    assert "publish_sha=" in healthy.stdout

    not_due = subprocess.run([*base, "--now", _utc(*PDT_DAY, 14, 59).isoformat()], capture_output=True, text=True)
    assert not_due.returncode == 0 and not_due.stdout.startswith("hourly-liveness: NOT_DUE")

    red = subprocess.run([*base, "--now", _utc(2026, 5, 20, 15, 30).isoformat()], capture_output=True, text=True)
    assert red.returncode == 1
    assert red.stdout.startswith("hourly-liveness: RED") and "stale" in red.stdout
    assert "owner attention" in red.stderr

    bad = subprocess.run([*base, "--now", "2026-05-19T15:30:00"], capture_output=True, text=True)
    assert bad.returncode == 2 and "naive" in bad.stderr
