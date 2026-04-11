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

from cuttingboard import config
from cuttingboard.audit import write_audit_record
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
) -> str:
    """Render the full report as a string (terminal and markdown use same text)."""
    lines: list[str] = []

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
    lines.append(_BORDER)
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
        # TRADE — qualified setups
        qual = qualification_summary
        assert qual is not None

        lines.append(f"  TRADES  ({qual.symbols_qualified})")
        lines.append("  " + "─" * 50)
        for setup in option_setups:
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
) -> bool:
    """Send ntfy notification. Returns True on success, False otherwise.

    Silently skips (returns False) when ntfy is not configured.
    Logs warnings on delivery failure — never raises.
    """
    topic = config.NTFY_TOPIC
    ntfy_url = config.NTFY_URL

    if not topic or not ntfy_url:
        logger.debug("ntfy not configured — notification skipped")
        return False

    title_map = {
        OUTCOME_TRADE:    f"Cuttingboard {date_str} — TRADE",
        OUTCOME_NO_TRADE: f"Cuttingboard {date_str} — NO TRADE",
        OUTCOME_HALT:     f"Cuttingboard {date_str} — ⚠ HALT",
    }
    title = title_map.get(outcome, f"Cuttingboard {date_str}")
    message = f"{title}\n\n{report}"

    try:
        resp = requests.post(
            f"{ntfy_url.rstrip('/')}/{topic}",
            data=message.encode(),
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

    # ----- Determine outcome -----
    if qual.symbols_qualified > 0 and setups:
        outcome = OUTCOME_TRADE
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
