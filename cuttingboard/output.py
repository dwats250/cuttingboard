"""
Layer 9 — Output Engine.

Three write destinations per run:
  1. Terminal  — printed immediately after all layers complete
  2. Markdown  — reports/YYYY-MM-DD.md (written even on NO TRADE days)
  3. ntfy      — alert sent when NTFY settings are in .env

Report is written and committed on every run, including NO TRADE days.

Outcomes
--------
  TRADE       — one or more qualified trades
  NO_TRADE    — regime short-circuit or zero qualified (non-halt)
  HALT        — a HALT_SYMBOL failed validation

Full pipeline entry point: run_pipeline()
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

import requests

from datetime import date as _date

from cuttingboard import config
from cuttingboard.audit import write_audit_record
from cuttingboard.chain_validation import (
    ChainValidationResult,
    validate_option_chains,
    VALIDATED, OPTIONS_WEAK, CHAIN_FAILED, OPTIONS_INVALID, MANUAL_CHECK,
)
from cuttingboard.derived import compute_all_derived
from cuttingboard.ingestion import fetch_all
from cuttingboard.normalization import normalize_all
from cuttingboard.options import OptionSetup, build_option_setups, generate_candidates
from cuttingboard.qualification import QualificationSummary, qualify_all
from cuttingboard.regime import RegimeState, compute_regime
from cuttingboard.structure import classify_all_structure
from cuttingboard.validation import ValidationSummary, validate_quotes

logger = logging.getLogger(__name__)

_BORDER = "═" * 54
_DIVIDER = "─" * 54
_REPORT_DIR = "reports"

_PERMISSION_LINES: dict[str, str] = {
    "AGGRESSIVE_LONG": "Long bias — trend continuation allowed. Kill: VIX spikes >15%.",
    "CONTROLLED_LONG": "Long bias — defined risk preferred. Kill: VIX crosses 25.",
    "DEFENSIVE_SHORT": "Short bias — no longs without VIX declining + support. Kill: VIX <20.",
    "NEUTRAL_PREMIUM": "Selective only — defined risk, R:R ≥ 3:1. Kill: VIX spikes >15%.",
    "STAY_FLAT":       "FLAT — no new positions. Await regime clarity.",
}

_PERMISSION_MATRIX = """\
  REGIME PERMISSIONS
  ─────────────────────────────────────────────────────
  RISK_ON   │ Trend continuation / BULL spreads
  RISK_OFF  │ Breakdown shorts / BEAR spreads
  NEUTRAL   │ Defined risk only / R:R ≥ 3:1
  CHAOTIC   │ FLAT — no new positions
  ─────────────────────────────────────────────────────
  Kill switch: VIX > 35 OR SPY gaps >3% → halt all new positions"""


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
) -> str:
    """Render the full report as a string (terminal and markdown use same text)."""
    lines: list[str] = []
    cr = chain_results or {}

    # ---- Header ----
    lines.append(_BORDER)
    lines.append(f"  CUTTINGBOARD  ·  {date_str}")

    if outcome == OUTCOME_HALT:
        lines.append("  ⚠  SYSTEM HALT")
    elif regime is not None:
        sign = "+" if regime.net_score >= 0 else ""
        lines.append(
            f"  {regime.regime} / {regime.posture}"
            f"  |  conf={regime.confidence:.2f}"
            f"  |  net={sign}{regime.net_score}"
        )
        lines.append(f"  {_permission_line(regime)}")

    lines.append(_BORDER)
    lines.append("")

    # ---- Sunday weekly context block ----
    if _is_sunday(date_str) and regime is not None and outcome != OUTCOME_HALT:
        lines.append(_PERMISSION_MATRIX)
        lines.append("")

    # ---- Body ----
    if outcome == OUTCOME_HALT:
        lines.append("  HALT — MACRO DATA INVALID")
        lines.append(f"  {halt_reason or 'unknown halt reason'}")

    elif outcome == OUTCOME_NO_TRADE:
        lines.append("  NO TRADE")
        if qualification_summary is not None and qualification_summary.regime_short_circuited:
            lines.append(f"  Reason: {qualification_summary.regime_failure_reason}")
        elif regime is not None:
            lines.append(
                f"  Reason: {regime.posture} posture — no qualifying setups"
            )

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

        lines.append(f"  TRADES  ({len(trade_setups)})")
        lines.append("  " + "─" * 50)
        for setup in trade_setups:
            lines.append(
                f"  {setup.symbol:<8}  {setup.strategy:<18}  "
                f"{setup.structure} / {setup.iv_environment}"
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

    # Watchlist and excluded appear for both TRADE and NO_TRADE outcomes
    # (not for HALT — there is no qualification data)
    if outcome != OUTCOME_HALT and qualification_summary is not None:
        qual = qualification_summary

        if qual.symbols_watchlist > 0:
            lines.append(f"  WATCHLIST  ({qual.symbols_watchlist})")
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
    lines.append(f"  Run       : {run_at_utc.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append(_BORDER)

    return "\n".join(lines)


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


def send_ntfy(
    report: str,
    date_str: str,
    outcome: str,
    title: Optional[str] = None,
) -> bool:
    """Send ntfy notification. Returns True on success, False otherwise.

    When title is provided it is sent as the ntfy Title header (displays as
    push notification headline on mobile). The report is sent as the body.

    When title is None the legacy behaviour applies: a title is constructed
    from outcome and prepended to the body.

    Silently skips (returns False) when ntfy is not configured.
    Logs warnings on delivery failure — never raises.
    """
    topic = config.NTFY_TOPIC
    ntfy_url = config.NTFY_URL

    if not topic or not ntfy_url:
        logger.debug("ntfy not configured — notification skipped")
        return False

    if title is not None:
        headers = {"Title": title}
        body = report
    else:
        title_map = {
            OUTCOME_TRADE:    f"Cuttingboard {date_str} — TRADE",
            OUTCOME_NO_TRADE: f"Cuttingboard {date_str} — NO TRADE",
            OUTCOME_HALT:     f"Cuttingboard {date_str} — ⚠ HALT",
        }
        headers = {"Title": title_map.get(outcome, f"Cuttingboard {date_str}")}
        body = report

    try:
        resp = requests.post(
            f"{ntfy_url.rstrip('/')}/{topic}",
            headers=headers,
            data=body.encode(),
            timeout=10,
        )
        if resp.status_code == 200:
            logger.info("ntfy notification delivered")
            return True
        logger.warning(
            f"ntfy delivery failed: HTTP {resp.status_code} — {resp.text[:200]}"
        )
    except Exception as exc:
        logger.warning(f"ntfy delivery error: {exc}")

    return False


# ---------------------------------------------------------------------------
# Full pipeline runner
# ---------------------------------------------------------------------------

def run_pipeline() -> int:
    """Execute all 9 layers and write all three output destinations.

    Layer execution order:
        1  fetch_all            — ingest raw quotes
        2  normalize_all        — unit normalization
        3  validate_quotes      — hard validation gate
        4  compute_regime       — 8-input vote model
        5  compute_all_derived  — EMA / ATR / momentum
        6  classify_all_structure
        7  generate_candidates  — options-aware TradeCandidate objects
        8  qualify_all          — 9-gate qualification
        9  build_option_setups  — strategy expression

    Returns 0 on success, 1 on HALT.
    """
    run_at = datetime.now(timezone.utc)
    date_str = run_at.strftime("%Y-%m-%d")

    # ----- Layers 1–3: Data spine -----
    logger.info("Pipeline start")
    raw    = fetch_all()
    normed = normalize_all(raw)
    val    = validate_quotes(normed)

    if val.system_halted:
        report = render_report(
            date_str=date_str,
            run_at_utc=run_at,
            regime=None,
            validation_summary=val,
            qualification_summary=None,
            option_setups=[],
            outcome=OUTCOME_HALT,
            halt_reason=val.halt_reason,
        )
        write_terminal(report)
        report_path = write_markdown(report, date_str)
        ntfy_sent = send_ntfy(report, date_str, OUTCOME_HALT)

        write_audit_record(
            run_at_utc=run_at,
            date_str=date_str,
            outcome=OUTCOME_HALT,
            regime=None,
            validation_summary=val,
            qualification_summary=None,
            option_setups=[],
            halt_reason=val.halt_reason,
            ntfy_sent=ntfy_sent,
            report_path=report_path,
        )
        return 1

    # ----- Layers 4–6: Analysis -----
    regime    = compute_regime(val.valid_quotes)
    dm        = compute_all_derived(val.valid_quotes)
    structure = classify_all_structure(val.valid_quotes, dm, regime.vix_level)

    # ----- Layers 7–8: Qualification -----
    candidates = generate_candidates(structure, dm, val.valid_quotes, regime)
    qual       = qualify_all(regime, structure, candidates or None, dm)

    # ----- Layer 9: Options expression -----
    setups: list[OptionSetup] = []
    if qual.qualified_trades:
        setups = build_option_setups(qual.qualified_trades, structure, dm)

    # ----- Layer 10: Chain validation -----
    chain_results: dict[str, ChainValidationResult] = {}
    if setups:
        chain_results = validate_option_chains(setups, val.valid_quotes)

    # ----- Determine outcome -----
    # Only VALIDATED setups count as actionable trades
    validated_count = sum(
        1 for s in setups
        if chain_results.get(s.symbol, ChainValidationResult(
            symbol=s.symbol, classification=VALIDATED, reason=None,
            spread_pct=None, open_interest=None, volume=None,
            expiry_used=None, data_source=None,
        )).classification == VALIDATED
    )
    if validated_count > 0:
        outcome = OUTCOME_TRADE
    elif qual.symbols_qualified > 0 and setups:
        # Setups existed but all failed chain validation
        outcome = OUTCOME_NO_TRADE
    else:
        outcome = OUTCOME_NO_TRADE

    # ----- Render and write -----
    report = render_report(
        date_str=date_str,
        run_at_utc=run_at,
        regime=regime,
        validation_summary=val,
        qualification_summary=qual,
        option_setups=setups,
        outcome=outcome,
        chain_results=chain_results,
    )

    write_terminal(report)
    report_path = write_markdown(report, date_str)
    ntfy_sent = send_ntfy(report, date_str, outcome)

    write_audit_record(
        run_at_utc=run_at,
        date_str=date_str,
        outcome=outcome,
        regime=regime,
        validation_summary=val,
        qualification_summary=qual,
        option_setups=setups,
        halt_reason=None,
        ntfy_sent=ntfy_sent,
        report_path=report_path,
    )

    logger.info(
        f"Pipeline complete: {outcome}  "
        f"qualified={qual.symbols_qualified}  "
        f"watchlist={qual.symbols_watchlist}"
    )
    return 0
