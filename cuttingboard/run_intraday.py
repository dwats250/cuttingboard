"""
Intraday monitor — Layers 1–5 regime watch.

Scheduled entry point: every 30 minutes, 14:00–21:00 UTC Monday–Friday.
  python -m cuttingboard.run_intraday

Runs L1–L5 (ingest → normalize → validate → derived → regime) and sends a
Telegram alert on any of three trigger conditions:

  1. Regime becomes CHAOTIC
  2. RISK_ON ↔ RISK_OFF crossover (directional regime flip)
  3. VIX single-interval spike > 20%

90-minute alert deduplication: if an alert was sent within the last 90 minutes
the current run logs the trigger but suppresses the notification. This prevents
alert storms during sustained volatile periods without missing the initial signal.

State is persisted in logs/intraday_state.json between GitHub Actions runs.
The CI commit step (`git add logs/`) ensures state survives across runs.
"""

import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

from cuttingboard.derived import compute_all_derived
from cuttingboard.ingestion import fetch_all
from cuttingboard.notifications import format_intraday_alert
from cuttingboard.output import send_notification
from cuttingboard.normalization import normalize_all
from cuttingboard.regime import (
    RegimeState,
    compute_regime,
    CHAOTIC, RISK_ON, RISK_OFF,
)
from cuttingboard.validation import validate_quotes

_UNICODE_REPLACEMENTS = [
    ("\u2014", "-"),  ("\u2013", "-"),  ("\u00B7", "-"),
    ("\u2022", "*"),  ("\u2192", "->"), ("\u2265", ">="),
    ("\u2264", "<="), ("\u2550", "="),  ("\u2500", "-"),
    ("\u2502", "|"),  ("\u2019", "'"),  ("\u2018", "'"),
    ("\u201C", '"'),  ("\u201D", '"'),  ("\u26A0", "!!"),
]


def _ascii_safe(text: str) -> str:
    for src, dst in _UNICODE_REPLACEMENTS:
        text = text.replace(src, dst)
    return text.encode("ascii", errors="replace").decode("ascii")

logger = logging.getLogger(__name__)

_STATE_PATH       = "logs/intraday_state.json"
_DEDUP_MINUTES    = 90
_VIX_SPIKE_LIMIT  = 0.20   # 20% single-interval move triggers alert

# Alert type labels (stored in state for auditability)
ALERT_CHAOTIC      = "CHAOTIC"
ALERT_REGIME_SHIFT = "REGIME_SHIFT"
ALERT_VIX_SPIKE    = "VIX_SPIKE"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    run_at = datetime.now(timezone.utc)

    # --- Layers 1–3: data spine ---
    raw    = fetch_all()
    normed = normalize_all(raw)
    val    = validate_quotes(normed)

    if val.system_halted:
        logger.warning(f"Intraday: system halted — {val.halt_reason}")
        _update_state(run_at, regime=None)
        sys.exit(0)   # Don't fail CI — data outage is not a pipeline error

    # --- Layers 4–5: derived + regime ---
    compute_all_derived(val.valid_quotes)
    regime = compute_regime(val.valid_quotes)

    logger.info(
        f"Intraday: {regime.regime} / {regime.posture}  "
        f"conf={regime.confidence:.2f}  VIX={regime.vix_level}"
    )

    state      = _load_state()
    alert_type = _detect_trigger(regime, state)

    if alert_type is not None:
        if _within_dedup_window(state, run_at):
            logger.info(
                f"Trigger {alert_type} detected but suppressed "
                f"(within {_DEDUP_MINUTES}-min dedup window)"
            )
            _update_state(run_at, regime)
        else:
            sent = _send_alert(regime, alert_type, run_at)
            _update_state(
                run_at, regime,
                last_alert_at=run_at if sent else None,
                last_alert_type=alert_type if sent else None,
            )
    else:
        _update_state(run_at, regime)

    sys.exit(0)


# ---------------------------------------------------------------------------
# Trigger detection
# ---------------------------------------------------------------------------

def _detect_trigger(regime: RegimeState, state: dict) -> Optional[str]:
    """Return alert type string if a trigger condition is active, else None.

    Checked in priority order: CHAOTIC > REGIME_SHIFT > VIX_SPIKE.
    """
    # Trigger 1: CHAOTIC — highest priority, always alert
    if regime.regime == CHAOTIC:
        return ALERT_CHAOTIC

    # Trigger 2: Directional regime flip (RISK_ON ↔ RISK_OFF)
    last_regime = state.get("last_regime")
    if (
        last_regime in (RISK_ON, RISK_OFF)
        and regime.regime in (RISK_ON, RISK_OFF)
        and regime.regime != last_regime
    ):
        return ALERT_REGIME_SHIFT

    # Trigger 3: VIX spike > 20% single interval
    if regime.vix_pct_change is not None and regime.vix_pct_change > _VIX_SPIKE_LIMIT:
        return ALERT_VIX_SPIKE

    return None


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _within_dedup_window(state: dict, now: datetime) -> bool:
    """Return True if the last alert was sent within the dedup window."""
    last_alert = state.get("last_alert_at_utc")
    if not last_alert:
        return False
    try:
        last_dt = datetime.fromisoformat(last_alert)
        return (now - last_dt) < timedelta(minutes=_DEDUP_MINUTES)
    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Telegram delivery
# ---------------------------------------------------------------------------

def _send_alert(regime: RegimeState, alert_type: str, run_at: datetime) -> bool:
    """Format and deliver a Telegram notification. Returns True on success."""
    title, message = format_intraday_alert(
        alert_type=alert_type,
        asof_utc=run_at,
        regime=regime,
    )
    sent = send_notification(title, message)
    if sent:
        logger.info(f"Intraday alert delivered: {alert_type} - {title!r}")
    return sent


# ---------------------------------------------------------------------------
# State persistence
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    """Load intraday state from disk. Returns empty dict if missing or corrupt."""
    if not os.path.exists(_STATE_PATH):
        return {}
    try:
        with open(_STATE_PATH, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        logger.warning(f"Could not read {_STATE_PATH} — starting with empty state")
        return {}


def _update_state(
    run_at: datetime,
    regime: Optional[RegimeState],
    last_alert_at: Optional[datetime] = None,
    last_alert_type: Optional[str] = None,
) -> None:
    """Write updated intraday state to disk.

    Only updates last_alert_at_utc when last_alert_at is explicitly provided
    (i.e., an alert was successfully sent this run). The existing value is
    preserved otherwise, maintaining the dedup window across runs.
    """
    os.makedirs(os.path.dirname(_STATE_PATH) or ".", exist_ok=True)

    state = _load_state()
    state["last_run_at_utc"] = run_at.isoformat()

    if regime is not None:
        state["last_regime"]     = regime.regime
        state["last_posture"]    = regime.posture
        state["last_confidence"] = round(regime.confidence, 4)
        state["last_vix_level"]  = regime.vix_level

    if last_alert_at is not None:
        state["last_alert_at_utc"] = last_alert_at.isoformat()
    if last_alert_type is not None:
        state["last_alert_type"] = last_alert_type

    with open(_STATE_PATH, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)

    logger.debug(f"Intraday state updated: {_STATE_PATH}")


if __name__ == "__main__":
    main()
