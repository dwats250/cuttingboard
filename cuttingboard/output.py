"""
Layer 9 — Output Engine.

Three write destinations per run:
  1. Terminal  — printed immediately after all layers complete
  2. Markdown  — reports/YYYY-MM-DD.md (written even on NO TRADE days)
  3. Telegram  — alert sent when TELEGRAM settings are in .env

Report is written and committed on every run, including NO TRADE days.

Outcomes
--------
  TRADE       — one or more qualified trades
  NO_TRADE    — regime short-circuit or zero qualified (non-halt)
  HALT        — a HALT_SYMBOL failed validation

Consumed by runtime.py — pure render and delivery layer, no pipeline logic.
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional

import requests

from datetime import date as _date

from cuttingboard import config, time_utils
from cuttingboard.audit import write_notification_audit
from cuttingboard.chain_validation import (
    ChainValidationResult,
    VALIDATED,
)
from cuttingboard.options import OptionSetup
from cuttingboard.qualification import QualificationSummary
from cuttingboard.regime import RegimeState, EXPANSION
from cuttingboard.validation import ValidationSummary
from cuttingboard.watch import (
    WatchSummary,
    get_session_phase,
    regime_bias,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

_LAST_SEND_TS: float = 0.0
_MIN_SEND_INTERVAL: float = 1.1  # seconds between Telegram sends


def _rate_limit_send() -> None:
    """Block until at least _MIN_SEND_INTERVAL has elapsed since last send."""
    global _LAST_SEND_TS
    elapsed = time.monotonic() - _LAST_SEND_TS
    if elapsed < _MIN_SEND_INTERVAL:
        time.sleep(_MIN_SEND_INTERVAL - elapsed)
    _LAST_SEND_TS = time.monotonic()


_BORDER = "=" * 54
_DIVIDER = "-" * 54
_REPORT_DIR = "reports"

# ---------------------------------------------------------------------------
# ASCII sanitisation
# ---------------------------------------------------------------------------

_UNICODE_REPLACEMENTS = [
    ("\u2014", "-"),    # em dash —
    ("\u2013", "-"),    # en dash –
    ("\u00B7", "-"),    # middle dot ·
    ("\u2022", "*"),    # bullet •
    ("\u2192", "->"),   # right arrow →
    ("\u2265", ">="),   # ≥
    ("\u2264", "<="),   # ≤
    ("\u2550", "="),    # ═  box double horizontal
    ("\u2500", "-"),    # ─  box light horizontal
    ("\u2502", "|"),    # │  box light vertical
    ("\u2019", "'"),    ("\u2018", "'"),
    ("\u201C", '"'),    ("\u201D", '"'),
    ("\u26A0", "!!"),   # ⚠
]


def _ascii_safe(text: str) -> str:
    """Replace common non-ASCII chars with ASCII equivalents, then strip the rest."""
    for src, dst in _UNICODE_REPLACEMENTS:
        text = text.replace(src, dst)
    return text.encode("ascii", errors="replace").decode("ascii")

_PERMISSION_LINES: dict[str, str] = {
    "AGGRESSIVE_LONG": "Long bias - trend continuation allowed. Kill: VIX spikes >15%.",
    "CONTROLLED_LONG": "Long bias - defined risk preferred. Kill: VIX crosses 25.",
    "DEFENSIVE_SHORT": "Short bias - no longs without VIX declining + support. Kill: VIX <20.",
    "NEUTRAL_PREMIUM": "Selective only - defined risk, R:R >= 3:1. Kill: VIX spikes >15%.",
    "STAY_FLAT":       "FLAT - no new positions. Await regime clarity.",
    "EXPANSION_LONG":  "EXPANSION - momentum allowed. Continuation entries. R:R >= 1.5.",
}

_PERMISSION_MATRIX = """\
  REGIME PERMISSIONS
  -----------------------------------------------------
  RISK_ON   | Trend continuation / BULL spreads
  RISK_OFF  | Breakdown shorts / BEAR spreads
  NEUTRAL   | Defined risk only / R:R >= 3:1
  CHAOTIC   | FLAT - no new positions
  -----------------------------------------------------
  Kill switch: VIX > 35 OR SPY gaps >3% -> halt all new positions"""


def _permission_line(regime: RegimeState) -> str:
    return _PERMISSION_LINES.get(regime.posture, "Awaiting regime clarity.")


def _is_sunday(date_str: str) -> bool:
    try:
        d = _date.fromisoformat(date_str)
        return d.weekday() == 6
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Outcome constants
# ---------------------------------------------------------------------------

OUTCOME_TRADE    = "TRADE"
OUTCOME_NO_TRADE = "NO_TRADE"
OUTCOME_HALT     = "HALT"


# ---------------------------------------------------------------------------
# Report renderer
# ---------------------------------------------------------------------------

def render_report(
    date_str: str,
    run_at_utc: datetime,
    regime: Optional[RegimeState],
    validation_summary: ValidationSummary,
    qualification_summary: Optional[QualificationSummary],
    option_setups: list[OptionSetup],
    outcome: str,
    halt_reason: Optional[str] = None,
    chain_results: Optional[dict[str, "ChainValidationResult"]] = None,
    watch_summary: Optional[WatchSummary] = None,
    **_: object,
) -> str:
    """Render the full report as a string (terminal and markdown use same text)."""
    lines: list[str] = []
    cr = chain_results or {}

    # ---- Header ----
    lines.append(_BORDER)
    lines.append(f"  CUTTINGBOARD  |  {date_str}")

    if outcome == OUTCOME_HALT:
        lines.append("  ⚠  SYSTEM HALT")
    elif regime is not None:
        session = watch_summary.session if watch_summary is not None else get_session_phase(run_at_utc)
        delta = "N/A" if regime.vix_pct_change is None else f"{regime.vix_pct_change:+.1%}"
        vix_text = "N/A" if regime.vix_level is None else f"{regime.vix_level:.1f}"
        now_et = time_utils.convert_utc_to_et(run_at_utc)
        lines.append(f"  Timestamp: {now_et.strftime('%Y-%m-%dT%H:%M:%S')} ET")
        lines.append(f"  Session: {session or 'OFF_SESSION'}")
        lines.append(f"  Regime: {regime.regime} / {regime.posture}")
        lines.append(f"  VIX: {vix_text}  |  delta: {delta}")
        lines.append(f"  Bias: {regime_bias(regime)}")

    lines.append(_BORDER)
    lines.append("")

    # ---- Sunday weekly context block ----
    if _is_sunday(date_str) and regime is not None and outcome != OUTCOME_HALT:
        lines.append(_PERMISSION_MATRIX)
        lines.append("")

    # ---- EXPANSION banner ----
    if regime is not None and regime.regime == EXPANSION and outcome != OUTCOME_HALT:
        lines.append("  EXPANSION MODE - Momentum allowed")
        lines.append("  Bias: LONG")
        lines.append("")

    # ---- Body ----
    if outcome == OUTCOME_HALT:
        lines.append("  HALT — MACRO DATA INVALID")
        lines.append(f"  {halt_reason or 'unknown halt reason'}")

    elif outcome == OUTCOME_NO_TRADE:
        if regime is not None and regime.regime == EXPANSION:
            lines.append("  EXPANSION MODE — No valid continuation entries yet")
        else:
            lines.append("  NO TRADE")
            if qualification_summary is not None and qualification_summary.regime_short_circuited:
                lines.append(f"  Reason: {qualification_summary.regime_failure_reason}")
            elif regime is not None:
                lines.append(
                    f"  Reason: {regime.posture} posture — no qualifying setups"
                )
        lines.append("")

    else:
        # TRADE — show only chain-validated setups
        trade_setups = [
            s for s in option_setups
            if not cr or cr.get(s.symbol, ChainValidationResult(
                symbol=s.symbol, classification=VALIDATED, reason=None,
                spread_pct=None, open_interest=None, volume=None,
                expiry_used=None, data_source=None,
            )).classification == VALIDATED
        ]

        entry_mode_for: dict[str, str] = {}
        if qualification_summary is not None:
            entry_mode_for = {
                r.symbol: r.entry_mode
                for r in qualification_summary.qualified_trades
            }

        lines.append(f"  A+ TRADES  ({len(trade_setups)})")
        lines.append("  " + "─" * 50)
        for setup in trade_setups:
            mode = entry_mode_for.get(setup.symbol, "")
            mode_tag = f"  [{mode}]" if mode and mode != "DIRECT" else ""
            lines.append(
                f"  {setup.symbol:<8}  {setup.strategy:<18}  "
                f"{setup.structure} / {setup.iv_environment}{mode_tag}"
            )
            lines.append(
                f"             {setup.long_strike} / {setup.short_strike}"
                f"  ·  ${setup.strike_distance:.2f} wide"
                f"  ·  {setup.dte} DTE"
            )
            contracts = setup.max_contracts
            risk = setup.dollar_risk
            lines.append(
                f"             {contracts} contract{'s' if contracts != 1 else ''}"
                f"  ·  max risk ${risk:.0f}"
            )
            if cr and setup.symbol in cr:
                cv = cr[setup.symbol]
                chain_line = f"             Chain: {cv.classification}"
                if cv.open_interest is not None:
                    chain_line += f"  OI={cv.open_interest}"
                if cv.spread_pct is not None:
                    chain_line += f"  spread={cv.spread_pct:.1%}"
                if cv.expiry_used:
                    chain_line += f"  exp={cv.expiry_used}"
                lines.append(chain_line)
            lines.append("             Exit: +50% profit or full debit loss")
            lines.append("")

    if (
        regime is not None
        and regime.regime == EXPANSION
        and qualification_summary is not None
        and qualification_summary.continuation_audit is not None
    ):
        audit = qualification_summary.continuation_audit
        lines.append("  [CONTINUATION_AUDIT]")
        lines.append(f"  total_candidates={audit['total_candidates']}")
        lines.append(f"  accepted={audit['accepted']}")
        lines.append("")
        lines.append("  rejections:")
        for reason in (
            "DATA_INCOMPLETE",
            "VIX_BLOCKED",
            "NO_BREAKOUT",
            "NO_HOLD_CONFIRMATION",
            "INSUFFICIENT_MOMENTUM",
            "EXTENDED_FROM_MEAN",
            "STOP_TOO_TIGHT",
            "RR_BELOW_THRESHOLD",
            "TIME_BLOCKED",
        ):
            lines.append(f"  {reason}={audit.get(reason, 0)}")
        lines.append("")

    # Watchlist and excluded appear for both TRADE and NO_TRADE outcomes
    # (not for HALT — there is no qualification data)
    if outcome != OUTCOME_HALT and watch_summary is not None and watch_summary.watchlist:
        lines.append(f"  WATCHLIST  ({len(watch_summary.watchlist)})")
        lines.append("  " + "─" * 50)
        for item in watch_summary.watchlist:
            lines.append(f"  {item.symbol:<8}  score {item.score:.1f}")
            lines.append(f"           {item.structure_note}")
            missing = ", ".join(item.missing_conditions) if item.missing_conditions else "none"
            lines.append(f"           Missing: {missing}")
        lines.append("")

    if outcome != OUTCOME_HALT and qualification_summary is not None:
        qual = qualification_summary

        if qual.symbols_watchlist > 0:
            lines.append(f"  NEAR_A_PLUS  ({qual.symbols_watchlist})")
            lines.append("  " + "─" * 50)
            for r in qual.watchlist:
                lines.append(f"  {r.symbol:<8}  {r.watchlist_reason}")
            lines.append("")

        if qual.symbols_excluded > 0:
            lines.append(f"  EXCLUDED  ({qual.symbols_excluded})")
            lines.append("  " + "─" * 50)
            for sym, reason in sorted(qual.excluded.items()):
                lines.append(f"  {sym:<8}  {reason}")
            lines.append("")

    # Chain issues section — setups that failed chain validation
    if cr:
        chain_issues = [
            (sym, cv) for sym, cv in cr.items()
            if cv.classification != VALIDATED
        ]
        if chain_issues:
            lines.append(f"  CHAIN ISSUES  ({len(chain_issues)})")
            lines.append("  " + "─" * 50)
            for sym, cv in sorted(chain_issues):
                note = cv.reason or cv.classification
                lines.append(f"  {sym:<8}  {cv.classification}")
                lines.append(f"           {note}")
            lines.append("")

    if outcome != OUTCOME_HALT and regime is not None:
        lines.append("  SUMMARY")
        lines.append("  " + "─" * 50)
        market_regime = regime.regime
        posture_label = regime.posture
        lines.append(f"  Market state: {market_regime} / {posture_label}")
        execution_posture = (
            watch_summary.execution_posture
            if watch_summary is not None
            else ("No Trade" if regime.posture == "STAY_FLAT" else "A+ Only")
        )
        lines.append(f"  Execution posture: {execution_posture}")
        lines.append("")

    # ---- Data status footer ----
    lines.append("")
    lines.append(_DIVIDER + " DATA STATUS " + "─" * max(0, 54 - len(_DIVIDER) - 13))
    vix_str = (
        f"{regime.vix_level:.1f}" if regime is not None and regime.vix_level is not None
        else "N/A"
    )
    lines.append(
        f"  Validated : {validation_summary.symbols_validated} / "
        f"{validation_summary.symbols_attempted}"
        f"    VIX : {vix_str}"
    )
    lines.append(f"  Run       : {time_utils.convert_utc_to_et(run_at_utc).strftime('%Y-%m-%dT%H:%M:%S')} ET")
    lines.append(_BORDER)

    return "\n".join(lines)


def render_report_from_payload(payload: dict) -> str:
    """Render a report string from a canonical ReportPayload dict.

    Minimal rendering path: produces a date header, outcome body (NO TRADE /
    HALT text), and DATA STATUS footer. The header timestamp/VIX/session block
    and the SUMMARY block (market_regime, tradable, posture_label) are NOT
    rendered because those sections in render_report() are gated on regime != None
    and this adapter does not reconstruct a full regime object.

    The payload dict is the authoritative input for UI layers; this adapter
    exists only for backward-compatible text output.
    """
    from cuttingboard.delivery.payload import assert_valid_payload
    from cuttingboard.validation import ValidationSummary

    assert_valid_payload(payload)

    meta = payload.get("meta", {})
    sections = payload.get("sections", {})
    run_status = payload.get("run_status", "ERROR")

    timestamp_str = meta.get("timestamp", "")
    try:
        from datetime import datetime
        run_at_utc = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise ValueError(
            f"render_report_from_payload: unparseable timestamp in payload: {timestamp_str!r}"
        )

    date_str = run_at_utc.strftime("%Y-%m-%d")

    if run_status == "ERROR":
        outcome = OUTCOME_HALT
    elif sections.get("top_trades"):
        outcome = OUTCOME_TRADE
    else:
        outcome = OUTCOME_NO_TRADE

    vhd = sections.get("validation_halt_detail")
    halt_reason: Optional[str] = vhd.get("reason") if vhd else None

    symbols_scanned = int(meta.get("symbols_scanned") or 0)
    stub_validation = ValidationSummary(
        system_halted=(run_status == "ERROR"),
        halt_reason=halt_reason,
        failed_halt_symbols=[],
        results={},
        valid_quotes={},
        invalid_symbols={},
        symbols_attempted=symbols_scanned,
        symbols_validated=symbols_scanned,
        symbols_failed=0,
    )

    return render_report(
        date_str=date_str,
        run_at_utc=run_at_utc,
        regime=None,
        validation_summary=stub_validation,
        qualification_summary=None,
        option_setups=[],
        outcome=outcome,
        halt_reason=halt_reason,
        chain_results=None,
        watch_summary=None,
    )


# ---------------------------------------------------------------------------
# Write destinations
# ---------------------------------------------------------------------------

def write_terminal(report: str) -> None:
    """Print report to stdout."""
    print(report)


def write_markdown(report: str, date_str: str) -> str:
    """Write report to reports/YYYY-MM-DD.md. Returns the file path."""
    os.makedirs(_REPORT_DIR, exist_ok=True)
    path = os.path.join(_REPORT_DIR, f"{date_str}.md")

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"```\n{report}\n```\n")

    logger.info(f"Report written to {path}")
    return path


def send_telegram(
    title: str,
    body: str = "",
    *,
    notification_priority: str = "",
    notification_state_key: str = "",
) -> bool:
    """Send Telegram notification. Returns True on success, False otherwise.

    Enforces a global minimum send interval (rate limit). Retries once on
    HTTP 429 (after 2s) or timeout/5xx (after 1s). Max 2 attempts total.

    Writes exactly one structured audit record to audit.jsonl per call:
    skip (not configured), success, HTTP failure, or exception.
    Never raises — notification failure must not crash the pipeline.

    notification_priority and notification_state_key are forwarded to the
    audit record when provided by the PRD-018 suppression layer.
    """
    token = config.TELEGRAM_BOT_TOKEN
    chat_id = config.TELEGRAM_CHAT_ID

    _priority = notification_priority or None
    _state_key = notification_state_key or None

    if not token or not chat_id:
        logger.debug("Telegram not configured — notification skipped")
        write_notification_audit(
            transport="telegram",
            alert_title=title,
            attempted=False,
            success=False,
            reason="not_configured",
            priority=_priority,
            state_key=_state_key,
            message_preview=body[:120] if body else None,
        )
        return False

    _rate_limit_send()

    text = f"{title}\n\n{body}" if body else title
    safe_text = _ascii_safe(text)
    preview = safe_text[:120]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": safe_text}

    success = False
    http_status: Optional[int] = None
    error_detail: Optional[str] = None
    attempts_made = 0

    for attempt in range(2):
        attempts_made = attempt + 1
        try:
            resp = requests.post(url, json=payload, timeout=10)
            http_status = resp.status_code
            if resp.status_code == 200:
                success = True
                break
            if attempt == 0:
                if resp.status_code == 429:
                    time.sleep(2)
                    continue
                if resp.status_code >= 500:
                    time.sleep(1)
                    continue
            error_detail = resp.text[:200]
            break
        except requests.exceptions.Timeout as exc:
            error_detail = str(exc)
            if attempt == 0:
                time.sleep(1)
                continue
            break
        except Exception as exc:
            error_detail = str(exc)
            break

    retry_count = attempts_made - 1

    if success:
        logger.info(f"Telegram delivered: {title!r} ({len(safe_text)} bytes)")
        write_notification_audit(
            transport="telegram",
            alert_title=title,
            attempted=True,
            success=True,
            http_status=200,
            retry_count=retry_count,
            priority=_priority,
            state_key=_state_key,
            message_preview=preview,
        )
        return True

    logger.warning(
        f"Telegram failed: HTTP {http_status} for {title!r}"
        + (f" - {error_detail}" if error_detail else "")
    )
    write_notification_audit(
        transport="telegram",
        alert_title=title,
        attempted=True,
        success=False,
        http_status=http_status,
        error=error_detail,
        retry_count=retry_count,
        reason="exception" if http_status is None else None,
        priority=_priority,
        state_key=_state_key,
        message_preview=preview,
    )
    return False


def send_notification(
    title: str,
    body: str = "",
    *,
    notification_priority: str = "",
    notification_state_key: str = "",
) -> bool:
    """Single notification dispatch point. Sends via Telegram."""
    return send_telegram(
        title,
        body,
        notification_priority=notification_priority,
        notification_state_key=notification_state_key,
    )


def build_notification_message(contract: dict) -> tuple[str, str]:
    """Return (title, body) for a Telegram alert derived from the canonical contract.

    Uses only: contract["status"], contract["generated_at"],
    contract["system_state"]["market_regime"], contract["system_state"]["tradable"],
    contract["trade_candidates"].
    """
    status = contract.get("status") or ""
    ss = contract.get("system_state") or {}
    market_regime = ss.get("market_regime") or "UNKNOWN"
    tradable = bool(ss.get("tradable", False))
    candidates = contract.get("trade_candidates") or []
    generated_at = (contract.get("generated_at") or "")[:16]

    if status in {"FAIL", "ERROR"}:
        title = "HALT - SYSTEM ERROR"
    elif tradable:
        title = "TRADE READY"
    elif candidates:
        title = "WATCHLIST - SETUPS FORMING"
    else:
        title = "NO TRADE - SYSTEM ACTIVE"

    lines = [
        f"Time: {generated_at}",
        f"Regime: {market_regime}",
        f"Tradable: {tradable}",
        f"Setups: {len(candidates)}",
        f"Status: {status}",
    ]

    if status in {"FAIL", "ERROR"}:
        lines.append("Reason: pipeline failure")
    elif not tradable and not candidates:
        lines.append("Reason: no qualifying setups")
    elif not tradable:
        lines.append("Reason: setups present but not tradable")

    return title, "\n".join(lines)
