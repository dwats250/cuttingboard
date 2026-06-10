"""Module-level constants for the runtime package (PRD-173, L0 leaf).

Extracted verbatim from the former ``cuttingboard/runtime.py`` and
re-exported by ``cuttingboard.runtime`` (``__init__``) so every
``cuttingboard.runtime.<CONST>`` path — including the module path
constants that tests patch via ``setattr`` — is preserved unchanged.

This module is an L0 leaf in the PRD-170 sublayer model: it imports only
stdlib and non-runtime ``cuttingboard.*`` names, never
``cuttingboard.runtime``.
"""

from __future__ import annotations

from pathlib import Path

from cuttingboard.notifications import (
    NOTIFY_HOURLY,
    NOTIFY_MARKET_CLOSE,
    NOTIFY_MIDMORNING,
    NOTIFY_ORB_TRAJECTORY,
    NOTIFY_POST_ORB,
    NOTIFY_POWER_HOUR,
)

MODE_LIVE = "live"
MODE_FIXTURE = "fixture"
MODE_SUNDAY = "sunday"
MODE_VERIFY = "verify"
MODE_PREFETCH = "prefetch"

# Notify modes that skip the full pipeline (not premarket)
_REGIME_ONLY_MODES = frozenset({NOTIFY_ORB_TRAJECTORY, NOTIFY_MIDMORNING})
_QUALIFY_ONLY_MODES = frozenset({NOTIFY_POST_ORB, NOTIFY_POWER_HOUR, NOTIFY_MARKET_CLOSE})
_HOURLY_MODES = frozenset({NOTIFY_HOURLY})

SUMMARY_MODE_LIVE = "LIVE"
SUMMARY_MODE_FIXTURE = "FIXTURE"
SUMMARY_MODE_SUNDAY = "SUNDAY"

SUMMARY_STATUS_SUCCESS = "SUCCESS"
SUMMARY_STATUS_FAIL = "FAIL"

REPORTS_DIR = Path("reports")
LOGS_DIR = Path("logs")
LATEST_RUN_PATH = LOGS_DIR / "latest_run.json"
LATEST_HOURLY_RUN_PATH = LOGS_DIR / "latest_hourly_run.json"
LATEST_HOURLY_CONTRACT_PATH = LOGS_DIR / "latest_hourly_contract.json"
LATEST_HOURLY_PAYLOAD_PATH = LOGS_DIR / "latest_hourly_payload.json"
HOURLY_REPORT_PATH = REPORTS_DIR / "output" / "hourly_report.html"
MARKET_MAP_PATH = LOGS_DIR / "market_map.json"
# PRD-166 D1/D2: hourly pipeline writes/reads an isolated market_map artifact so
# the shared MARKET_MAP_PATH can never be the source of an hourly render's
# PRD-118 R3 lineage mismatch. Default/fixture writes stay on MARKET_MAP_PATH.
LATEST_HOURLY_MARKET_MAP_PATH = LOGS_DIR / "latest_hourly_market_map.json"
TREND_STRUCTURE_PATH = LOGS_DIR / "trend_structure_snapshot.json"
WATCHLIST_PATH = LOGS_DIR / "watchlist_snapshot.json"
DEFAULT_FIXTURE_DIR = Path("tests/fixtures")

VALID_REGIMES = {"RISK_ON", "RISK_OFF", "NEUTRAL", "CHAOTIC", "EXPANSION"}
VALID_POSTURES = {
    "AGGRESSIVE_LONG",
    "CONTROLLED_LONG",
    "DEFENSIVE_SHORT",
    "NEUTRAL_PREMIUM",
    "STAY_FLAT",
    "EXPANSION_LONG",
}

_FIXTURE_QUOTE_FIELDS = {
    "symbol",
    "price",
    "pct_change_decimal",
    "volume",
    "fetched_at_utc",
    "source",
    "units",
    "age_seconds",
}

_PERMISSION_LINES: dict[str, str] = {
    "AGGRESSIVE_LONG": "Long bias — trend continuation allowed.",
    "CONTROLLED_LONG": "Long bias — defined risk preferred.",
    "DEFENSIVE_SHORT": "Short bias — breakdown trades allowed.",
    "NEUTRAL_PREMIUM": "Selective only — defined risk, R:R >= 3:1.",
    "STAY_FLAT":       "No new trades permitted.",
    "EXPANSION_LONG":  "EXPANSION — momentum allowed. Continuation entries. R:R >= 1.5.",
}

__all__ = [
    "MODE_LIVE",
    "MODE_FIXTURE",
    "MODE_SUNDAY",
    "MODE_VERIFY",
    "MODE_PREFETCH",
    "_REGIME_ONLY_MODES",
    "_QUALIFY_ONLY_MODES",
    "_HOURLY_MODES",
    "SUMMARY_MODE_LIVE",
    "SUMMARY_MODE_FIXTURE",
    "SUMMARY_MODE_SUNDAY",
    "SUMMARY_STATUS_SUCCESS",
    "SUMMARY_STATUS_FAIL",
    "REPORTS_DIR",
    "LOGS_DIR",
    "LATEST_RUN_PATH",
    "LATEST_HOURLY_RUN_PATH",
    "LATEST_HOURLY_CONTRACT_PATH",
    "LATEST_HOURLY_PAYLOAD_PATH",
    "HOURLY_REPORT_PATH",
    "MARKET_MAP_PATH",
    "LATEST_HOURLY_MARKET_MAP_PATH",
    "TREND_STRUCTURE_PATH",
    "WATCHLIST_PATH",
    "DEFAULT_FIXTURE_DIR",
    "VALID_REGIMES",
    "VALID_POSTURES",
    "_FIXTURE_QUOTE_FIELDS",
    "_PERMISSION_LINES",
]
