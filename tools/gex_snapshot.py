#!/usr/bin/env python3
"""PRD-306 - Manual cached _SPX GEX snapshot producer (isolated, observe-only).

One keyless GET against the Cboe delayed_quotes _SPX endpoint, computes settled
P0 gamma-exposure structural outputs for the SPX+SPXW option universe, and
atomically writes one honest, self-describing sidecar artifact
(logs/gex_snapshot.json) for manual inspection and the hourly best-effort CI
refresh (PRD-310; run-local in CI, never restored/staged/published); one
observe-only renderer consumer (PRD-309), still no decision authority.

Isolation invariant (PRD-306 R11): this module imports NOTHING from
cuttingboard/ and no cuttingboard module imports it. Stdlib only (R11 dependency
honesty; zoneinfo included - a missing OS IANA tz database FAILS LOUD, never a
tzdata pip dependency).

The source of build truth is docs/prd_history/PRD-306.md (BUILD-BINDING
CONTRACTS 1-8, REQUIREMENTS R1-R37), patched by docs/prd_history/PRD-307.md
(R38-R43: open_interest admissibility is semantic integer-valued, not Python
`int` representation -- Cboe emits whole-number OI as float). This module
implements them without redesign.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import namedtuple
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Callable, Optional
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Frozen contract constants (BUILD-BINDING CONTRACTS 1-3, 6)
# ---------------------------------------------------------------------------

SCHEMA_VERSION = 1
SOURCE = "cboe_delayed_quotes"
ENDPOINT = "https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json"
UNDERLYING = "_SPX"
ROOTS = ("SPX", "SPXW")  # admissibility allowlist
CONTRACT_MULTIPLIER = 100
UNITS = "USD gamma notional per 1% underlying move"
DATA_DELAY = "~15 min delayed (REPORTED; Cboe delayed_quotes posture)"
SPOT_BASIS = "SPX cash index level (data.current_price)"
MODEL_LABEL = "greeks Cboe-model-computed; GEX derived-of-model"
SIGN_CONVENTION = (
    "calls:+1 / puts:-1 -- assumed dealer-long-call/short-put positioning; "
    "descriptive assumption, not measured"
)
ZERO_DTE_CAVEAT = (
    "AM-settled SPX vs PM-settled SPXW actual settlement timing is NOT modeled "
    "in v1; per_root splits by root only."
)
ARTIFACT_PATH = Path("logs/gex_snapshot.json")
EASTERN = "America/New_York"

# Provider top-level timestamp: naive text "YYYY-MM-DD HH:MM:SS" interpreted UTC.
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
# OCC symbol: root letters, yymmdd, C/P flag, strike*1000 (8 digits).
_OCC_RE = re.compile(r"^([A-Z]+)(\d{6})([CP])(\d{8})$")

EXCLUSION_KEYS = (
    "missing_fields", "invalid_gamma", "invalid_open_interest",
    "unparseable_symbol", "invalid_expiry", "unexpected_root",
)

# Provenance classification, exhaustive over every emitted top-level field
# (BUILD-BINDING CONTRACTS 6; "provenance" classifies itself as CONFIGURED).
_PROVENANCE = {
    "configured": ["schema_version", "source", "endpoint", "underlying", "roots",
                   "units", "contract_multiplier", "provenance"],
    "observed": ["spot", "feed_timestamp_utc", "fetched_at_utc"],
    "reported": ["data_delay"],
    "derived": ["gex_total_1pct_usd", "call_wall", "put_wall",
                "dominant_net_gamma", "zero_dte", "coverage", "by_strike"],
    "inferred": ["sign_convention", "model_label"],
}

Contract = namedtuple("Contract", "root cp strike expiry gamma oi")


class FailLoud(Exception):
    """A top-level admissibility / provider / IO failure. Exit non-zero, write
    nothing, preserve the last good artifact (BUILD-BINDING CONTRACTS 4, 8)."""


def _log(reason: str) -> None:
    print(json.dumps({"gex_snapshot": reason}), file=sys.stderr)


# ---------------------------------------------------------------------------
# Fetch (one GET, stdlib urllib; injectable for tests) - R5/R6
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: float = 15.0) -> tuple[int, bytes]:
    """Return (status_code, body_bytes) for one keyless GET. No retry storm."""
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": "cuttingboard-gex/1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:  # non-200 surfaced as its status
        return exc.code, b""


# ---------------------------------------------------------------------------
# Small validators / parsers
# ---------------------------------------------------------------------------

def _finite_number(value: object) -> bool:
    """Numeric, non-boolean (bool subclasses int - checked FIRST), finite."""
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def _valid_gamma(value: object) -> bool:
    return _finite_number(value) and value >= 0


def _valid_oi(value: object) -> bool:
    # Integer-VALUED, not int-REPRESENTED (PRD-307): Cboe emits whole-number OI
    # as JSON floats (e.g. 2960.0). Admissible iff numeric, non-boolean, finite,
    # >= 0, and mathematically integer-valued; accepted OI is normalized to
    # int() at the call site (2.5 / negatives / bool / NaN / Inf rejected).
    return _finite_number(value) and value >= 0 and float(value).is_integer()


def _parse_expiry(yymmdd: str) -> Optional[date]:
    try:
        return date(2000 + int(yymmdd[0:2]), int(yymmdd[2:4]), int(yymmdd[4:6]))
    except ValueError:
        return None


def _parse_feed_timestamp(value: object) -> datetime:
    """Strict "YYYY-MM-DD HH:MM:SS" interpreted UTC. Anything else FAILS LOUD -
    never a fallback to the producer clock (BUILD-BINDING CONTRACTS 3, R34)."""
    if not isinstance(value, str) or not _TIMESTAMP_RE.match(value):
        raise FailLoud(f"malformed provider timestamp: {value!r}")
    try:
        naive = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise FailLoud(f"unparseable provider timestamp: {value!r}") from exc
    return naive.replace(tzinfo=timezone.utc)


def _require_aware(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise FailLoud("fetched_at_utc would be naive (construction error)")
    return dt.astimezone(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Top-level admissibility (R7/R28/R29/R33/R34/R35)
# ---------------------------------------------------------------------------

def _validate_top_level(payload: object) -> tuple[list, float, datetime]:
    if not isinstance(payload, dict):
        raise FailLoud("payload is not a JSON object")
    data = payload.get("data")
    if not isinstance(data, dict):
        raise FailLoud("missing top-level data object")
    options = data.get("options")
    if not isinstance(options, list):
        raise FailLoud("missing options list")
    spot = data.get("current_price")
    if isinstance(spot, bool) or not isinstance(spot, (int, float)) \
            or not math.isfinite(spot) or spot <= 0:
        raise FailLoud(f"invalid current_price: {spot!r}")
    feed_dt = _parse_feed_timestamp(payload.get("timestamp"))
    return options, float(spot), feed_dt


# ---------------------------------------------------------------------------
# Per-contract admissibility + first-failure exclusion accounting (R4/R30-R32/R36)
# ---------------------------------------------------------------------------

def _classify_row(row: object) -> tuple[Optional[Contract], Optional[str]]:
    """Return (contract, None) if eligible, else (None, exclusion_key). The
    fixed first-failure order is: missing-fields -> symbol parse -> root ->
    expiry -> gamma -> open_interest."""
    if not isinstance(row, dict) or not {"option", "gamma", "open_interest"} <= row.keys():
        return None, "missing_fields"
    symbol = row["option"]
    match = _OCC_RE.match(symbol) if isinstance(symbol, str) else None
    if match is None:
        return None, "unparseable_symbol"
    root, yymmdd, cp, digits = match.group(1), match.group(2), match.group(3), match.group(4)
    if root not in ROOTS:
        return None, "unexpected_root"
    expiry = _parse_expiry(yymmdd)
    if expiry is None:
        return None, "invalid_expiry"
    if not _valid_gamma(row["gamma"]):
        return None, "invalid_gamma"
    if not _valid_oi(row["open_interest"]):
        return None, "invalid_open_interest"
    # Normalize admitted OI to int (2960.0 -> 2960) so arithmetic, zero_oi_rows,
    # and determinism are byte-identical to a Python-int feed (PRD-307).
    return Contract(root, cp, int(digits) / 1000, expiry, float(row["gamma"]),
                    int(row["open_interest"])), None


# ---------------------------------------------------------------------------
# GEX + per-strike aggregation + structural selection (R2/R3/R14-R18/R24-R27)
# ---------------------------------------------------------------------------

def _gex(contract: Contract, spot: float) -> float:
    sign = 1.0 if contract.cp == "C" else -1.0
    return sign * contract.gamma * contract.oi * CONTRACT_MULTIPLIER * spot * spot * 0.01


def _unavailable(reason: str) -> dict:
    return {"strike": None, "gex_1pct_usd": None, "reason": reason}


def _lowest_strike(strikes) -> float:
    return min(strikes)


def _select_call_wall(call_by_strike: dict) -> dict:
    if not call_by_strike:
        return _unavailable("no_eligible_calls")
    best = max(call_by_strike.values())
    if best == 0.0:
        return _unavailable("no_nonzero_call_gex")
    strike = _lowest_strike([k for k, v in call_by_strike.items() if v == best])
    return {"strike": strike, "gex_1pct_usd": best, "reason": None}


def _select_put_wall(put_by_strike: dict) -> dict:
    if not put_by_strike:
        return _unavailable("no_eligible_puts")
    best_abs = max(abs(v) for v in put_by_strike.values())
    if best_abs == 0.0:
        return _unavailable("no_nonzero_put_gex")
    strike = _lowest_strike([k for k, v in put_by_strike.items() if abs(v) == best_abs])
    return {"strike": strike, "gex_1pct_usd": put_by_strike[strike], "reason": None}


def _select_dominant(net_by_strike: dict) -> dict:
    best_abs = max(abs(v) for v in net_by_strike.values())
    if best_abs == 0.0:
        return _unavailable("all_net_gamma_zero")
    strike = _lowest_strike([k for k, v in net_by_strike.items() if abs(v) == best_abs])
    return {"strike": strike, "gex_1pct_usd": net_by_strike[strike], "reason": None}


# ---------------------------------------------------------------------------
# Per-strike modeled-magnitude carrier + profile-only settlement gate (GEX-4)
# ---------------------------------------------------------------------------

def _profile_reason(included: list, feed_dt: datetime) -> Optional[str]:
    """Profile-only settlement validity gate (GEX-4 section 8), evaluated per
    observation, in this order. This governs ONLY whether the per-strike carrier
    is emitted with arrays; it never changes gex_total, the anchors, or 0DTE.
    Fail-closed by construction: root, expiry and the ET observation time are
    already required for admissibility, so the condition is always evaluable.
    """
    obs_et = feed_dt.astimezone(ZoneInfo(EASTERN))
    obs_date = obs_et.date()
    # 1. Any admitted SPX-root row expiring on the observation date -> unavailable
    #    (AM settlement timing is not modeled, so same-day AM-settled rows cannot
    #    be established as unsettled at any time of day).
    if any(c.root == "SPX" and c.expiry == obs_date for c in included):
        return "same_day_spx_rows_present"
    # 2. At or after 16:00 ET with any admitted same-day SPXW row -> unavailable.
    if obs_et.time() >= time(16, 0, 0) and any(
        c.root == "SPXW" and c.expiry == obs_date for c in included
    ):
        return "post_close_same_day_spxw_rows_present"
    # 3. Otherwise the profile carrier is emitted with arrays.
    return None


def _by_strike(call_by_strike: dict, put_by_strike: dict,
               strikes: list, reason: Optional[str]) -> dict:
    """Serialize the canonical per-strike carrier (GEX-4 section 9): typed-
    unavailable (reason only) when the settlement gate fires, else the ascending
    columnar arrays. ``strikes`` is the ascending union; put magnitudes are the
    absolute value of the producer's signed put contribution (>= 0). Columnar by
    design (no list-of-objects, no raw-chain keys), so PRD-306 R12 stays green."""
    if reason is not None:
        return {"reason": reason}
    return {
        "reason": None,
        "strike": list(strikes),
        "call_modeled_magnitude_1pct_usd": [call_by_strike.get(k, 0.0) for k in strikes],
        "put_modeled_magnitude_1pct_usd": [abs(put_by_strike.get(k, 0.0)) for k in strikes],
    }


# ---------------------------------------------------------------------------
# 0DTE (ET observation date, absolute-GEX numerator, all-expiry denominator) - R19-R23
# ---------------------------------------------------------------------------

def _zero_dte(included: list, spot: float, feed_dt: datetime) -> dict:
    obs_date = feed_dt.astimezone(ZoneInfo(EASTERN)).date()
    per_root = {r: {"abs_gex_0dte_1pct_usd": 0.0, "contracts": 0} for r in ROOTS}
    numerator = 0.0
    denominator = 0.0
    for contract in included:
        mag = abs(_gex(contract, spot))
        denominator += mag
        if contract.expiry == obs_date:
            numerator += mag
            bucket = per_root[contract.root]
            bucket["abs_gex_0dte_1pct_usd"] += mag
            bucket["contracts"] += 1
    if denominator == 0.0:
        share, reason = None, "zero_abs_gex_denominator"
    else:
        share, reason = numerator / denominator, None
    return {
        "share": share,
        "abs_gex_0dte_1pct_usd": numerator,
        "abs_gex_total_1pct_usd": denominator,
        "observation_trading_date": obs_date.isoformat(),
        "per_root": per_root,
        "caveat": ZERO_DTE_CAVEAT,
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# Artifact assembly (R1/R5-R10/R36/R37)
# ---------------------------------------------------------------------------

def _build_artifact(payload: object, now: datetime, url: str) -> dict:
    options, spot, feed_dt = _validate_top_level(payload)

    excluded = {key: 0 for key in EXCLUSION_KEYS}
    included: list = []
    zero_gamma_rows = 0
    zero_oi_rows = 0
    for row in options:
        contract, reason = _classify_row(row)
        if reason is not None:
            excluded[reason] += 1
            continue
        included.append(contract)
        if contract.gamma == 0.0:
            zero_gamma_rows += 1
        if contract.oi == 0:
            zero_oi_rows += 1
    if not included:
        raise FailLoud("zero eligible contracts after admissibility (included == 0)")

    call_by_strike: dict = {}
    put_by_strike: dict = {}
    for contract in included:
        value = _gex(contract, spot)
        target = call_by_strike if contract.cp == "C" else put_by_strike
        target[contract.strike] = target.get(contract.strike, 0.0) + value
    strikes = sorted(set(call_by_strike) | set(put_by_strike))
    net_by_strike = {k: call_by_strike.get(k, 0.0) + put_by_strike.get(k, 0.0) for k in strikes}
    # Core total reconciled with the carrier: ONE pinned flattened math.fsum over
    # the ascending union, operand order c(K1), -p(K1), c(K2), -p(K2), ... . The
    # consumer and the round-trip validation replay this exact expression, so the
    # reconciliation is exact equality (replaces the old dict-order sum()).
    call_mag = [call_by_strike.get(k, 0.0) for k in strikes]
    put_mag = [abs(put_by_strike.get(k, 0.0)) for k in strikes]
    gex_total = math.fsum(v for c, p in zip(call_mag, put_mag) for v in (c, -p))
    by_strike = _by_strike(call_by_strike, put_by_strike, strikes,
                           _profile_reason(included, feed_dt))

    expiries = sorted({contract.expiry for contract in included})
    coverage = {
        "contracts_total": len(options),
        "included": len(included),
        "excluded": excluded,
        "zero_gamma_rows": zero_gamma_rows,
        "zero_oi_rows": zero_oi_rows,
        "per_root": {r: sum(1 for c in included if c.root == r) for r in ROOTS},
        "expirations": {
            "count": len(expiries),
            "min": expiries[0].isoformat(),
            "max": expiries[-1].isoformat(),
        },
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
        "endpoint": url,
        "underlying": UNDERLYING,
        "roots": list(ROOTS),
        "fetched_at_utc": _require_aware(now),
        "feed_timestamp_utc": feed_dt.isoformat(),
        "data_delay": DATA_DELAY,
        "spot": {"value": spot, "basis": SPOT_BASIS},
        "model_label": MODEL_LABEL,
        "sign_convention": SIGN_CONVENTION,
        "units": UNITS,
        "contract_multiplier": CONTRACT_MULTIPLIER,
        "gex_total_1pct_usd": gex_total,
        "call_wall": _select_call_wall(call_by_strike),
        "put_wall": _select_put_wall(put_by_strike),
        "dominant_net_gamma": _select_dominant(net_by_strike),
        "zero_dte": _zero_dte(included, spot, feed_dt),
        "by_strike": by_strike,
        "provenance": {cls: list(fields) for cls, fields in _PROVENANCE.items()},
        "coverage": coverage,
    }


# ---------------------------------------------------------------------------
# Atomic write (tmp + os.replace; last-good preservation) - R10/R13
# ---------------------------------------------------------------------------

def _atomic_write(artifact: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(artifact, indent=2, sort_keys=True, allow_nan=False) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    try:
        os.replace(tmp, path)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run(
    *,
    now: Optional[datetime] = None,
    fetch_fn: Optional[Callable[[str], tuple[int, bytes]]] = None,
    artifact_path: Path = ARTIFACT_PATH,
    url: str = ENDPOINT,
) -> int:
    """Produce one snapshot. Returns 0 on a successful generation, 1 on any
    fail-loud condition (prior artifact left byte-identical). A naive `now`
    raises ValueError - a construction error, never a silent fallback (R9)."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware (fetched_at_utc is locally observed)")
    fetch_fn = fetch_fn or _http_get

    try:
        status, body = fetch_fn(url)
        if status != 200:
            raise FailLoud(f"provider returned non-200 status: {status}")
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise FailLoud("provider body is not valid JSON") from exc
        artifact = _build_artifact(payload, now, url)
        _atomic_write(artifact, Path(artifact_path))
    except FailLoud as exc:
        _log(f"fail-loud -> prior artifact preserved: {exc}")
        return 1
    except Exception as exc:  # zoneinfo/tz-db absence, non-standard JSON, IO
        _log(f"producer failure ({type(exc).__name__}) -> prior artifact preserved: {exc}")
        return 1
    _log(f"wrote {artifact_path}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Cached _SPX GEX snapshot producer (PRD-306; manual + hourly best-effort CI, PRD-310)")
    parser.add_argument("--artifact-path", default=str(ARTIFACT_PATH))
    parser.add_argument("--url", default=ENDPOINT)
    args = parser.parse_args(argv)
    return run(artifact_path=Path(args.artifact_path), url=args.url)


if __name__ == "__main__":
    raise SystemExit(main())
