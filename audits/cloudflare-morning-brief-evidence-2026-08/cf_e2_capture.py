#!/usr/bin/env python3
"""Bounded CF-E2 provider-semantics capture (evidence only; non-production)."""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
ET = ZoneInfo("America/New_York")
OUT_DIR = Path(__file__).resolve().parent
SYMBOL = "SPY"

# This harness is deliberately single-campaign tooling. A later date requires a
# reviewed source change; there is no ordinary CLI override.
AUTHORIZED_CAPTURE_DATE = date(2026, 8, 10)
CAPTURE_WINDOWS_PT = {
    "premarket": (time(5, 45), time(6, 15)),
    "open": (time(6, 28), time(6, 45)),
}

QUOTE_INFO_FIELDS = (
    "marketState",
    "preMarketPrice",
    "preMarketTime",
    "regularMarketPrice",
    "regularMarketTime",
    "currentPrice",
    "previousClose",
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _write(record: dict[str, Any], slot: str) -> Path:
    stamp = record["captured_utc"].replace(":", "").replace("-", "").replace("+", "")
    path = OUT_DIR / f"cf_e2_{slot}_{stamp}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {path}")
    return path


def _refuse(reason: str) -> None:
    print(f"refusing to run: {reason}; no evidence written", file=sys.stderr)
    raise SystemExit(3)


def _fail(reason: str, slot: str, partial: dict[str, Any] | None = None) -> None:
    """Record a provider/runtime failure; authorization failures never call this."""
    now = _now_utc()
    _require_authorized(slot, now)
    record: dict[str, Any] = {
        "status": "UNAVAILABLE",
        "slot": slot.upper(),
        "symbol": SYMBOL,
        "reason": reason,
        "captured_utc": now.isoformat(),
        "captured_pt": now.astimezone(PT).isoformat(),
        "provenance": {"provider": "yfinance", "no_credentials": True},
    }
    if partial is not None:
        record["partial"] = partial
    _write(record, f"{slot}_UNAVAILABLE")
    print(f"CF-E2 UNAVAILABLE ({slot}): {reason}", file=sys.stderr)
    raise SystemExit(2)


def _import_yf(slot: str):
    try:
        import yfinance as yf  # noqa: WPS433 - standalone evidence dependency
    except Exception as exc:  # pragma: no cover - environment probe
        _fail(f"yfinance import failed: {exc!r}", slot)
    return yf


def _authorized_slot(requested_slot: str, now: datetime) -> tuple[str | None, str | None]:
    """Resolve a slot only when date, weekday, and that slot's PT window are valid."""
    pt_now = now.astimezone(PT)
    if pt_now.date() != AUTHORIZED_CAPTURE_DATE:
        return None, (
            f"PT date {pt_now.date().isoformat()} is not the authorized capture date "
            f"{AUTHORIZED_CAPTURE_DATE.isoformat()}"
        )
    if pt_now.weekday() >= 5:
        return None, f"authorized date {AUTHORIZED_CAPTURE_DATE.isoformat()} is not a weekday"

    candidates = CAPTURE_WINDOWS_PT if requested_slot == "auto" else {
        requested_slot: CAPTURE_WINDOWS_PT[requested_slot]
    }
    for slot, (start, end) in candidates.items():
        if start <= pt_now.time().replace(tzinfo=None) <= end:
            return slot, None

    if requested_slot == "auto":
        expected = "premarket 05:45-06:15 or open 06:28-06:45 PT"
    else:
        start, end = CAPTURE_WINDOWS_PT[requested_slot]
        expected = f"{requested_slot} {start.strftime('%H:%M')}-{end.strftime('%H:%M')} PT"
    return None, f"PT time {pt_now.strftime('%H:%M:%S')} is outside {expected}"


def _require_authorized(slot: str, now: datetime) -> None:
    authorized, refusal = _authorized_slot(slot, now)
    if authorized != slot:
        _refuse(refusal or f"slot {slot} is not authorized")


def _json_scalar(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _finite_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _provider_timestamp(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    numeric = _finite_float(value)
    if numeric is None:
        return None
    try:
        return datetime.fromtimestamp(numeric, timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None


def _build_premarket_record(
    *,
    fast_info: dict[str, Any],
    quote_info: dict[str, Any],
    now: datetime,
    fast_info_error: str | None = None,
    quote_info_error: str | None = None,
) -> dict[str, Any]:
    """Classify only provider-labeled, dated premarket observations."""
    raw_fast = {key: _json_scalar(value) for key, value in fast_info.items()}
    raw_quote = {key: _json_scalar(quote_info.get(key)) for key in QUOTE_INFO_FIELDS}
    raw: dict[str, Any] = {"fast_info": raw_fast, "quote_info": raw_quote}
    if fast_info_error:
        raw["fast_info_error"] = fast_info_error
    if quote_info_error:
        raw["quote_info_error"] = quote_info_error

    market_state = quote_info.get("marketState")
    premarket_price = _finite_float(quote_info.get("preMarketPrice"))
    observed = _provider_timestamp(quote_info.get("preMarketTime"))
    previous_close = _finite_float(fast_info.get("previous_close"))
    if previous_close is None:
        previous_close = _finite_float(quote_info.get("previousClose"))

    reasons: list[str] = []
    if market_state != "PRE":
        reasons.append("provider marketState is not PRE")
    if premarket_price is None or premarket_price <= 0:
        reasons.append("provider preMarketPrice is missing or invalid")
    if observed is None:
        reasons.append("provider preMarketTime is missing or invalid")
    else:
        observed_pt = observed.astimezone(PT)
        if observed_pt.date() != AUTHORIZED_CAPTURE_DATE:
            reasons.append("provider preMarketTime is not on the authorized capture date")
        if not time(1, 0) <= observed_pt.time().replace(tzinfo=None) < time(6, 30):
            reasons.append("provider preMarketTime is outside the US premarket session")
        if observed > now:
            reasons.append("provider preMarketTime is later than capture time")
    if previous_close is None or previous_close <= 0:
        reasons.append("previous close is missing or invalid")

    record: dict[str, Any] = {
        "status": "INCONCLUSIVE" if reasons else "OK",
        "slot": "PREMARKET",
        "symbol": SYMBOL,
        "captured_utc": now.isoformat(),
        "captured_pt": now.astimezone(PT).isoformat(),
        "raw_observations": raw,
        "diagnostic": {
            "classification": "INCONCLUSIVE" if reasons else "PROVIDER_IDENTIFIED_PREMARKET",
            "reason": "; ".join(reasons) if reasons else (
                "Provider supplied marketState=PRE plus a positive preMarketPrice and a "
                "dated preMarketTime within the authorized US premarket session."
            ),
            "last_price_difference_is_classification_evidence": False,
        },
        "provenance": {
            "provider": "yfinance",
            "provider_surfaces": ["Ticker('SPY').fast_info", "Ticker('SPY').info"],
            "no_credentials": True,
        },
    }
    if not reasons:
        assert premarket_price is not None and observed is not None and previous_close is not None
        record["premarket_observation"] = {
            "price": premarket_price,
            "observed_utc": observed.isoformat(),
            "observed_pt": observed.astimezone(PT).isoformat(),
            "previous_close": previous_close,
            "pct_change": (premarket_price - previous_close) / previous_close,
        }
    return record


def _fast_info_observations(info: Any) -> dict[str, Any]:
    observations: dict[str, Any] = {}
    for attr, key in (("last_price", "lastPrice"), ("previous_close", "previousClose")):
        value = getattr(info, attr, None)
        if value is None:
            try:
                value = info[key]
            except Exception:
                value = None
        observations[attr] = value
    return observations


def capture_premarket() -> None:
    yf = _import_yf("premarket")
    ticker = yf.Ticker(SYMBOL)
    fast_info_error = None
    try:
        fast_info = _fast_info_observations(ticker.fast_info)
    except Exception as exc:
        fast_info = {}
        fast_info_error = repr(exc)

    quote_info_error = None
    try:
        provider_info = ticker.info
        quote_info = {key: provider_info.get(key) for key in QUOTE_INFO_FIELDS}
    except Exception as exc:
        quote_info = {}
        quote_info_error = repr(exc)

    if fast_info_error and quote_info_error:
        _fail(
            "both fast_info and quote_info provider surfaces failed",
            "premarket",
            {"fast_info_error": fast_info_error, "quote_info_error": quote_info_error},
        )

    captured_at = _now_utc()
    _require_authorized("premarket", captured_at)
    record = _build_premarket_record(
        fast_info=fast_info,
        quote_info=quote_info,
        now=captured_at,
        fast_info_error=fast_info_error,
        quote_info_error=quote_info_error,
    )
    _write(record, "premarket")


def _flatten_columns(df):
    try:
        import pandas as pd  # noqa: WPS433 - optional runtime type check
        if isinstance(df.columns, pd.MultiIndex):
            df = df.copy()
            df.columns = df.columns.get_level_values(0)
    except Exception:
        pass
    return df


def _open_bar_outcome(row: Any, timestamp: datetime, raw_timestamp: str) -> dict[str, Any]:
    raw = repr(row.to_dict()) if hasattr(row, "to_dict") else repr(row)
    try:
        open_price = float(row["Open"])
        close_price = float(row["Close"])
        if not math.isfinite(open_price) or not math.isfinite(close_price):
            raise ValueError("Open/Close must be finite")
        if open_price <= 0 or close_price <= 0:
            raise ValueError("Open/Close must be positive")
    except Exception as exc:
        return {
            "outcome": "UNPARSEABLE",
            "raw_timestamp": raw_timestamp,
            "time_et": timestamp.isoformat(),
            "error": repr(exc),
            "raw": raw,
        }
    return {
        "outcome": "PRESENT",
        "raw_timestamp": raw_timestamp,
        "time_et": timestamp.isoformat(),
        "open": open_price,
        "close": close_price,
    }


def _merge_open_outcome(
    current: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    if current["outcome"] == "ABSENT":
        return candidate

    raw_timestamps: list[str] = []
    for outcome in (current, candidate):
        raw_timestamps.extend(outcome.get("raw_timestamps", []))
        if "raw_timestamp" in outcome:
            raw_timestamps.append(outcome["raw_timestamp"])
    timezone_unverified = any(
        outcome.get("reason") == "timezone_unverified" for outcome in (current, candidate)
    )
    return {
        "outcome": "UNPARSEABLE",
        "reason": "timezone_unverified" if timezone_unverified else "duplicate_bar_rows",
        "error": "duplicate rows returned for the same expected bar",
        "raw_timestamps": raw_timestamps,
        "raw": repr([current, candidate]),
    }


def _build_open_record(df: Any, now: datetime) -> dict[str, Any]:
    df = _flatten_columns(df)
    et_today = now.astimezone(ET).date()
    expected = (("bar_0930_OPEN", "09:30"), ("bar_0931_OPEN_PLUS_1", "09:31"))
    bars: dict[str, dict[str, Any]] = {
        label: {"outcome": "ABSENT", "expected_time_et": hhmm} for label, hhmm in expected
    }
    timestamp_errors: list[dict[str, str]] = []

    if df is not None:
        for idx, row in df.iterrows():
            raw_timestamp = repr(idx)
            timestamp = idx.to_pydatetime()
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                ambiguous = {
                    "outcome": "UNPARSEABLE",
                    "reason": "timezone_unverified",
                    "raw_timestamp": raw_timestamp,
                }
                matched_expected_wall_time = False
                for label, hhmm in expected:
                    if timestamp.date() == et_today and timestamp.strftime("%H:%M") == hhmm:
                        bars[label] = _merge_open_outcome(bars[label], ambiguous)
                        matched_expected_wall_time = True
                if not matched_expected_wall_time:
                    timestamp_errors.append(ambiguous)
                continue

            timestamp = timestamp.astimezone(ET)
            for label, hhmm in expected:
                if timestamp.date() == et_today and timestamp.strftime("%H:%M") == hhmm:
                    parsed = _open_bar_outcome(row, timestamp, raw_timestamp)
                    bars[label] = _merge_open_outcome(bars[label], parsed)

    invalid = bool(timestamp_errors) or any(
        bar["outcome"] == "UNPARSEABLE" for bar in bars.values()
    )
    record = {
        "status": "INVALID" if invalid else "OK",
        "slot": "OPEN",
        "symbol": SYMBOL,
        "captured_utc": now.isoformat(),
        "captured_pt": now.astimezone(PT).isoformat(),
        "session_date_et": et_today.isoformat(),
        "bars": bars,
        "diagnostic": {
            "bar_0930_present": bars["bar_0930_OPEN"]["outcome"] == "PRESENT",
            "bar_0931_present": bars["bar_0931_OPEN_PLUS_1"]["outcome"] == "PRESENT",
            "interpretation": (
                "PRESENT means a finite positive Open/Close pair parsed for the exact bar; "
                "ABSENT means no matching bar was returned; UNPARSEABLE makes status INVALID."
            ),
        },
        "provenance": {
            "provider": "yfinance",
            "call": "download(SPY, period=1d, interval=1m, prepost=False)",
            "no_credentials": True,
        },
    }
    if timestamp_errors:
        record["timestamp_errors"] = timestamp_errors
    return record


def capture_open() -> None:
    yf = _import_yf("open")
    try:
        frame = yf.download(SYMBOL, period="1d", interval="1m", prepost=False, progress=False)
    except Exception as exc:
        _fail(f"1m download failed: {exc!r}", "open")
    captured_at = _now_utc()
    _require_authorized("open", captured_at)
    record = _build_open_record(frame, captured_at)
    _write(record, "open")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="CF-E2 provider-semantics diagnostic (read-only, non-production).",
    )
    parser.add_argument("--slot", choices=["premarket", "open", "auto"], default="auto")
    args = parser.parse_args(argv)

    now = _now_utc()
    slot, refusal = _authorized_slot(args.slot, now)
    if slot is None:
        _refuse(refusal or "capture is not authorized")

    if slot == "premarket":
        capture_premarket()
    else:
        capture_open()


if __name__ == "__main__":
    main()
