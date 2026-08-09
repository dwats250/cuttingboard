#!/usr/bin/env python3
"""CF-E2 provider-semantics diagnostic capture (PLANNING EVIDENCE -- non-production).

Read-only diagnostic for the Cloudflare / Morning Brief planning packet
(audits/reconciliation-2026-08/CLOUDFLARE_CLOCK_MORNING_BRIEF_PLANNING_PACKET_2026-08-08.md,
section 3 / CF-E2). It captures the two facts the packet says the repo itself
cannot answer:

  --slot premarket  (run ~6:00 PT): does the SPY quote's last price reflect
      premarket trades, or does it echo the prior close?  -> gates CF-D1b
  --slot open       (run ~6:32 PT): is the 09:30 ET (OPEN) and 09:31 ET
      (OPEN+1) 1-minute bar available yet, and at what capture time?
      -> first-bar-latency question for the OPEN / OPEN+1 observations

DISCIPLINE (per the owner charge -- preparation only, no fabricated evidence):
  * NO credentials are used or emitted (yfinance public quote path).
  * NO value is fabricated. Missing/unusable data is recorded as UNAVAILABLE
    with its reason and the process exits non-zero.
  * Touches NO production code or data; writes ONE timestamped JSON evidence
    file into THIS audit folder only.
  * It reads live market data -- it is meaningful ONLY when run inside the
    stated PT window on a real market day. `--slot auto` refuses to run
    outside a window.

Provider: yfinance (the repo's quote provider; `cuttingboard/ingestion.py`
uses `fast_info.previous_close` and pct_change). This harness captures the raw
provider behaviour so the semantics are judged from evidence, not assumption.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
ET = ZoneInfo("America/New_York")
OUT_DIR = Path(__file__).resolve().parent
SYMBOL = "SPY"


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _write(record: dict, slot: str) -> Path:
    stamp = record["captured_utc"].replace(":", "").replace("-", "").replace("+", "")
    path = OUT_DIR / f"cf_e2_{slot}_{stamp}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return path


def _fail(reason: str, slot: str, partial: dict | None = None) -> None:
    """Fail loud: record the unavailability truthfully, exit non-zero, no fabrication."""
    now = _now_utc()
    rec = {
        "status": "UNAVAILABLE",
        "slot": slot,
        "symbol": SYMBOL,
        "reason": reason,
        "captured_utc": now.isoformat(),
        "captured_pt": now.astimezone(PT).isoformat(),
        "provenance": {"provider": "yfinance", "no_credentials": True},
    }
    if partial is not None:
        rec["partial"] = partial
    _write(rec, f"{slot}_UNAVAILABLE")
    print(f"CF-E2 UNAVAILABLE ({slot}): {reason}", file=sys.stderr)
    sys.exit(2)


def _import_yf(slot: str):
    try:
        import yfinance as yf  # noqa: WPS433 (deliberate local import for a standalone diagnostic)
    except Exception as exc:  # pragma: no cover - environment probe
        _fail(f"yfinance import failed: {exc!r}", slot)
    return yf


def capture_premarket() -> None:
    yf = _import_yf("premarket")
    ticker = yf.Ticker(SYMBOL)
    try:
        fi = ticker.fast_info
        last = getattr(fi, "last_price", None)
        prev = getattr(fi, "previous_close", None)
        if last is None:
            last = fi["lastPrice"]
        if prev is None:
            prev = fi["previousClose"]
        last = float(last)
        prev = float(prev)
    except Exception as exc:
        _fail(f"fast_info last_price/previous_close unavailable: {exc!r}", "premarket")

    if prev == 0:
        _fail("previous_close is zero (cannot compute pct_change)", "premarket",
              {"last_price": last, "previous_close": prev})

    pct = (last - prev) / prev
    reflects = abs(last - prev) > 1e-9
    now = _now_utc()
    rec = {
        "status": "OK",
        "slot": "PREMARKET",
        "symbol": SYMBOL,
        "captured_utc": now.isoformat(),
        "captured_pt": now.astimezone(PT).isoformat(),
        "fast_info": {"last_price": last, "previous_close": prev, "pct_change": pct},
        "diagnostic": {
            "reflects_premarket_movement": reflects,
            "interpretation": (
                "last_price != previous_close at ~6:00 PT -> quote reflects premarket "
                "trades -> premarket-displacement observation (CF-D1b) is feasible from "
                "this field. last_price == previous_close -> field echoes the prior "
                "close -> premarket-displacement banner is NOT feasible from fast_info."
            ),
        },
        "provenance": {
            "provider": "yfinance",
            "field_path": "Ticker('SPY').fast_info.{last_price,previous_close}",
            "no_credentials": True,
        },
    }
    _write(rec, "premarket")


def _flatten_columns(df):
    # yfinance may return MultiIndex columns for a single ticker; flatten to level 0.
    try:
        import pandas as pd  # noqa: WPS433
        if isinstance(df.columns, pd.MultiIndex):
            df = df.copy()
            df.columns = df.columns.get_level_values(0)
    except Exception:
        pass
    return df


def capture_open() -> None:
    yf = _import_yf("open")
    now = _now_utc()
    et_today = now.astimezone(ET).date()
    try:
        df = yf.download(SYMBOL, period="1d", interval="1m", prepost=False, progress=False)
    except Exception as exc:
        _fail(f"1m download failed: {exc!r}", "open")
    if df is None or len(df) == 0:
        _fail("no 1m bars returned (bars not yet available at capture time)", "open")
    df = _flatten_columns(df)

    bars: dict[str, dict | None] = {}
    for label, hhmm in (("bar_0930_OPEN", "09:30"), ("bar_0931_OPEN_PLUS_1", "09:31")):
        found = None
        for idx, row in df.iterrows():
            ts = idx.to_pydatetime()
            ts = ts.replace(tzinfo=ET) if ts.tzinfo is None else ts.astimezone(ET)
            if ts.date() == et_today and ts.strftime("%H:%M") == hhmm:
                try:
                    found = {
                        "time_et": ts.isoformat(),
                        "open": float(row["Open"]),
                        "close": float(row["Close"]),
                    }
                except Exception as exc:
                    found = {"time_et": ts.isoformat(), "parse_error": repr(exc)}
                break
        bars[label] = found

    rec = {
        "status": "OK",
        "slot": "OPEN",
        "symbol": SYMBOL,
        "captured_utc": now.isoformat(),
        "captured_pt": now.astimezone(PT).isoformat(),
        "session_date_et": et_today.isoformat(),
        "bars": bars,
        "diagnostic": {
            "bar_0930_present": bars["bar_0930_OPEN"] is not None,
            "bar_0931_present": bars["bar_0931_OPEN_PLUS_1"] is not None,
            "interpretation": (
                "Records whether the 09:30 (OPEN) and 09:31 (OPEN+1) ET 1-minute bars "
                "are available at this capture time -- the first-bar-latency the OPEN / "
                "OPEN+1 observations depend on. Absence here is real evidence (bar not "
                "yet published), not a failure."
            ),
        },
        "provenance": {
            "provider": "yfinance",
            "call": "download(SPY, period=1d, interval=1m, prepost=False)",
            "no_credentials": True,
        },
    }
    _write(rec, "open")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="CF-E2 provider-semantics diagnostic (read-only, non-production).",
    )
    ap.add_argument("--slot", choices=["premarket", "open", "auto"], default="auto")
    args = ap.parse_args()
    slot = args.slot

    if slot == "auto":
        pt_now = _now_utc().astimezone(PT)
        hm = pt_now.hour * 60 + pt_now.minute
        if 345 <= hm <= 375:          # ~5:45-6:15 PT
            slot = "premarket"
        elif 388 <= hm <= 405:        # ~6:28-6:45 PT
            slot = "open"
        else:
            print(
                f"refusing to run: PT time {pt_now.strftime('%H:%M')} is not in a CF-E2 "
                "capture window (premarket ~6:00 PT, open ~6:32 PT). Use --slot to force.",
                file=sys.stderr,
            )
            sys.exit(3)

    if slot == "premarket":
        capture_premarket()
    else:
        capture_open()


if __name__ == "__main__":
    main()
