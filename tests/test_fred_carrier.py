"""PRD-336 R3 — the bounded FRED carrier (DGS2 + DGS5).

Deterministic and network-free: ``_fetch_fred_csv`` is monkeypatched with canned
CSV. Proves the bounded ``cosd`` request URL, DGS2 + DGS5 parsing, the
gap/malformed/future/stale/wrong-series fail-closed paths, and the never-raises
per-symbol isolation on a network failure. This closes the PRD-198 #4 gap — the
FRED acquisition carrier previously had no red test.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from cuttingboard import ingestion


def _csv(series: str, rows: list[tuple[str, str]]) -> str:
    body = "\n".join(f"{d},{v}" for d, v in rows)
    return f"observation_date,{series}\n{body}\n"


# --- the bounded request URL (R3 mitigation) --------------------------------

def test_bounded_url_contains_cosd() -> None:
    url = ingestion._fred_csv_url("DGS5", date(2026, 9, 6) - timedelta(days=14))
    assert url.startswith("https://fred.stlouisfed.org/graph/fredgraph.csv?")
    assert "id=DGS5" in url
    assert "cosd=2026-08-23" in url   # 14 calendar days before 2026-09-06


# --- parsing DGS2 AND DGS5 (R2 generalization) ------------------------------

@pytest.mark.parametrize("series", ["DGS2", "DGS5"])
def test_parse_latest_and_prior(series: str) -> None:
    today = date(2026, 9, 6)
    text = _csv(series, [("2026-09-02", "4.30"), ("2026-09-03", "4.40")])
    latest, pct, as_of = ingestion._parse_fred_csv(text, today, series)
    assert latest == 4.40
    assert as_of == date(2026, 9, 3)
    assert pct == pytest.approx((4.40 - 4.30) / 4.30)


def test_gap_rows_skipped() -> None:
    today = date(2026, 9, 6)
    text = _csv("DGS2", [("2026-09-01", "4.20"), ("2026-09-02", "."), ("2026-09-03", "4.40")])
    latest, _, as_of = ingestion._parse_fred_csv(text, today, "DGS2")
    assert (latest, as_of) == (4.40, date(2026, 9, 3))


# --- fail-closed paths (never a stale / fabricated number) ------------------

def test_stale_fails_closed() -> None:
    today = date(2026, 9, 20)   # latest row is > 5 calendar days old
    text = _csv("DGS5", [("2026-09-02", "4.30"), ("2026-09-03", "4.40")])
    with pytest.raises(ValueError, match="stale"):
        ingestion._parse_fred_csv(text, today, "DGS5")


def test_future_dated_fails_closed() -> None:
    today = date(2026, 9, 3)
    text = _csv("DGS2", [("2026-09-03", "4.30"), ("2026-09-10", "4.40")])
    with pytest.raises(ValueError, match="future"):
        ingestion._parse_fred_csv(text, today, "DGS2")


def test_malformed_value_fails_closed() -> None:
    today = date(2026, 9, 6)
    text = _csv("DGS2", [("2026-09-02", "4.30"), ("2026-09-03", "NaNsense")])
    with pytest.raises(ValueError):
        ingestion._parse_fred_csv(text, today, "DGS2")


def test_too_few_rows_fails_closed() -> None:
    today = date(2026, 9, 6)
    text = _csv("DGS2", [("2026-09-03", "4.40")])   # only one usable row
    with pytest.raises(ValueError, match="two usable"):
        ingestion._parse_fred_csv(text, today, "DGS2")


def test_wrong_series_header_fails_closed() -> None:
    today = date(2026, 9, 6)
    text = _csv("DGS2", [("2026-09-02", "4.30"), ("2026-09-03", "4.40")])
    # requested DGS5 but the CSV is DGS2 — assert-the-resolved guard fails closed.
    with pytest.raises(ValueError, match="header mismatch"):
        ingestion._parse_fred_csv(text, today, "DGS5")


# --- carrier integration: success stamps as_of; failures never raise --------

def test_try_fred_quote_success_stamps_as_of_and_bounds_url(monkeypatch) -> None:
    today = date.today()
    prior = today - timedelta(days=1)
    text = _csv("DGS5", [(prior.isoformat(), "4.30"), (today.isoformat(), "4.40")])
    captured: dict[str, str] = {}

    def _fake_fetch(url: str, timeout: float) -> str:
        captured["url"] = url
        return text

    monkeypatch.setattr(ingestion, "_fetch_fred_csv", _fake_fetch)
    q = ingestion._try_fred_quote("DGS5")

    assert q.fetch_succeeded is True
    assert q.price == 4.40
    assert q.as_of == today          # observation date, distinct from fetch clock
    assert q.source == "fred"
    assert "id=DGS5" in captured["url"] and "cosd=" in captured["url"]


def test_try_fred_quote_network_failure_never_raises(monkeypatch) -> None:
    def _boom(url: str, timeout: float) -> str:
        raise OSError("network down")

    monkeypatch.setattr(ingestion, "_fetch_fred_csv", _boom)
    q = ingestion._try_fred_quote("DGS5")

    assert q.fetch_succeeded is False   # never raises — optional driver renders "--"
    assert q.as_of is None
    assert q.source == "fred"


def test_try_fred_quote_unmapped_series_never_raises() -> None:
    q = ingestion._try_fred_quote("DGS30")   # not in _FRED_SERIES_BY_SYMBOL
    assert q.fetch_succeeded is False


def test_dgs5_is_registered_on_the_fred_carrier() -> None:
    assert ingestion._FRED_SERIES_BY_SYMBOL.get("DGS5") == "DGS5"
    assert ingestion._FRED_SERIES_BY_SYMBOL.get("DGS2") == "DGS2"


# --- PRD-344: fail-fast (one attempt, truthful diagnostic) -------------------

@pytest.mark.parametrize("symbol", ["DGS2", "DGS5"])
def test_fred_timeout_makes_exactly_one_attempt(monkeypatch, caplog, symbol) -> None:
    """R1/R2/R3: a hanging FRED endpoint costs ONE socket timeout, never a retry
    loop, and the recorded reason is the real exception (not the outer '30s')."""
    calls: list[str] = []
    sleeps: list[float] = []

    def _hang(url: str, timeout: float) -> str:
        calls.append(url)
        raise TimeoutError("timed out")          # what urlopen raises on Py3.11

    monkeypatch.setattr(ingestion, "_fetch_fred_csv", _hang)
    monkeypatch.setattr(ingestion.time, "sleep", lambda s: sleeps.append(s))
    caplog.set_level("WARNING", logger="cuttingboard.ingestion")

    q = ingestion._try_fred_quote(symbol)

    assert len(calls) == 1, f"expected exactly one network attempt, got {len(calls)}"
    assert sleeps == [], "no backoff sleep on the optional FRED driver"
    assert q.fetch_succeeded is False and q.source == "fred"
    assert q.price == 0.0 and q.as_of is None     # no fabricated / carried value
    assert q.failure_reason is not None and "timed out" in q.failure_reason
    fred_records = [r for r in caplog.records if symbol in r.getMessage() and "fred" in r.getMessage()]
    assert fred_records and fred_records[0].levelname == "WARNING"
    joined = " ".join(r.getMessage() for r in fred_records)
    assert "TimeoutError" in joined and "timed out" in joined
    assert "after 30s" not in joined            # the false outer-wrapper label is gone


def test_fred_success_makes_exactly_one_attempt(monkeypatch) -> None:
    """R4: the success path is unchanged and also touches the network once."""
    today = date.today()
    prior = today - timedelta(days=1)
    text = _csv("DGS2", [(prior.isoformat(), "4.00"), (today.isoformat(), "4.10")])
    calls: list[str] = []

    def _ok(url: str, timeout: float) -> str:
        calls.append(url)
        return text

    monkeypatch.setattr(ingestion, "_fetch_fred_csv", _ok)
    q = ingestion._try_fred_quote("DGS2")
    assert len(calls) == 1
    assert q.fetch_succeeded is True and q.price == 4.10 and q.as_of == today
