"""
Operational runtime layer for the public CLI.

This module wraps the existing engine layers without modifying their logic.
It adds:
  - public mode dispatch
  - fixture loading
  - Sunday-mode truncation
  - JSON run summaries
  - run verification
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional
from unittest.mock import patch

import pandas as pd

from cuttingboard import config, time_utils
from cuttingboard.audit import write_audit_record, write_notification_audit
from cuttingboard.contract import (
    LATEST_CONTRACT_PATH,
    build_error_contract,
    build_pipeline_output_contract,
    derive_run_status,
)
from cuttingboard.chain_validation import (
    ChainValidationResult,
    MANUAL_CHECK,
    VALIDATED,
    validate_option_chains,
)
from cuttingboard.derived import compute_all_derived
from cuttingboard.ingestion import fetch_ohlcv
from cuttingboard.ingestion import RawQuote, _ohlcv_cache_path, fetch_all, fetch_intraday_bars
from cuttingboard.intraday_state_engine import Bar as IntradayStateBar, compute_intraday_state
from cuttingboard.market_map import build_market_map
from cuttingboard.trend_structure import build_trend_structure_snapshot
from cuttingboard.watchlist_sidecar import build_watchlist_snapshot
from cuttingboard.trade_visibility import build_visibility_map
from cuttingboard.trade_explanation import build_explanation_map
from cuttingboard.market_map_lifecycle import inject_lifecycle
from cuttingboard.evaluation import run_post_trade_evaluation
from cuttingboard.performance_engine import run_performance_engine
from cuttingboard.contract import _build_macro_drivers
from cuttingboard.execution_policy import (
    ExecutionSessionState,
    OrbPolicyState,
    apply_execution_policy_to_decisions,
    load_execution_session_state,
)
from cuttingboard.macro_pressure import build_macro_pressure
from cuttingboard.normalization import NormalizedQuote, normalize_all
from cuttingboard.notifications import (
    NOTIFY_MODES,
    NOTIFY_ORB_TRAJECTORY,
    NOTIFY_POST_ORB,
    NOTIFY_MIDMORNING,
    NOTIFY_POWER_HOUR,
    NOTIFY_MARKET_CLOSE,
    NOTIFY_HOURLY,
    format_failure_notification,
    format_hourly_notification,
    format_notification,
)
from cuttingboard.notifications.state import (
    classify_notification_priority,
    load_last_state,
    notification_state_key,
    save_last_state,
    should_send,
    LAST_STATE_PATH,
)
from cuttingboard.flow import load_flow_snapshot
from cuttingboard.overnight_policy import apply_overnight_policy
from cuttingboard.correlation import CorrelationResult, compute_correlation
from cuttingboard.options import OptionSetup, build_option_setups, generate_candidates
from cuttingboard.trade_policy import PolicyContext, evaluate_policy
from cuttingboard.trade_decision import TradeDecision, create_trade_decision, ALLOW_TRADE
from cuttingboard.trade_thesis import apply_thesis_gate
from cuttingboard.invalidation import apply_invalidation_gate
from cuttingboard.entry_quality import apply_entry_quality_gate
from cuttingboard.output import (
    OUTCOME_HALT,
    OUTCOME_NO_TRADE,
    OUTCOME_TRADE,
    NotificationResult,
    build_notification_message,
    get_last_notification_result,
    render_report,
    send_notification,
)
from cuttingboard.qualification import ENTRY_MODE_CONTINUATION, QualificationSummary, qualify_all
from cuttingboard.reports.premarket import build_premarket_report
from cuttingboard.reports.postmarket import build_postmarket_report
from cuttingboard.regime import CHAOTIC, NEUTRAL, EXPANSION, RegimeState, compute_regime
from cuttingboard.sector_router import (
    SectorRouterState,
    SuppressedCandidate,
    apply_sector_router,
    resolve_sector_router,
)
from cuttingboard.structure import classify_all_structure
from cuttingboard.universe import filter_execution_dict, filter_execution_items, is_tradable_symbol, log_universe_configuration
from cuttingboard.validation import ValidationSummary, extract_fetch_failures, validate_quotes
from cuttingboard.watch import WatchSummary, classify_watchlist, compute_all_intraday_metrics

logger = logging.getLogger(__name__)


@dataclass
class _PartialPipelineResult:
    """Lightweight view passed to the contract builder before PipelineResult is frozen."""
    mode: str
    generation_id: str
    run_at_utc: datetime
    date_str: str
    raw_quotes: dict
    normalized_quotes: dict
    validation_summary: Any
    regime: Any
    router_mode: str
    qualification_summary: Any
    watch_summary: Any
    option_setups: list
    chain_results: dict
    alert_sent: bool
    report_path: str
    errors: list
    correlation: Optional[CorrelationResult] = None
    trade_decisions: list[TradeDecision] = field(default_factory=list)
    thesis_map: Optional[dict] = None
    invalidation_guidance_map: Optional[dict] = None
    entry_quality_map: Optional[dict] = None


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


@dataclass(frozen=True)
class PipelineResult:
    mode: str
    generation_id: str
    run_at_utc: datetime
    date_str: str
    raw_quotes: dict[str, RawQuote]
    normalized_quotes: dict[str, NormalizedQuote]
    validation_summary: ValidationSummary
    regime: Optional[RegimeState]
    router_mode: str
    energy_score: float
    index_score: float
    qualification_summary: Optional[QualificationSummary]
    watch_summary: Optional[WatchSummary]
    candidates_generated: int
    option_setups: list[OptionSetup]
    trade_decisions: list[TradeDecision]
    suppressed_candidates: list[SuppressedCandidate]
    chain_results: dict[str, ChainValidationResult]
    outcome: str
    alert_sent: bool
    report: str
    report_path: str
    audit_record: dict[str, Any]
    warnings: list[str]
    errors: list[str]
    summary: dict[str, Any]
    contract: dict[str, Any]
    correlation: Optional[CorrelationResult] = None
    premarket_report: dict[str, Any] = field(default_factory=dict)
    postmarket_report: dict[str, Any] = field(default_factory=dict)
    market_map: dict[str, Any] = field(default_factory=dict)
    visibility_map: dict[str, dict] = field(default_factory=dict)
    explanation_map: dict[str, dict] = field(default_factory=dict)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m cuttingboard")
    parser.add_argument(
        "--mode",
        choices=[MODE_LIVE, MODE_FIXTURE, MODE_SUNDAY, MODE_VERIFY, MODE_PREFETCH],
        default=MODE_LIVE,
    )
    parser.add_argument(
        "--notify-mode",
        choices=sorted(NOTIFY_MODES),
        default=None,
        dest="notify_mode",
    )
    parser.add_argument("--fixture-file")
    parser.add_argument("--file")
    parser.add_argument("--date")
    return parser


def cli_main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )

    if args.mode == MODE_VERIFY:
        result = verify_run_summary(args.file or str(LATEST_RUN_PATH))
        print("PASS" if result["pass"] else "FAIL")
        for line in result["errors"]:
            print(f"ERROR: {line}")
        for line in result["warnings"]:
            print(f"WARNING: {line}")
        return 0 if result["pass"] else 1

    if args.mode == MODE_PREFETCH:
        return execute_prefetch()

    _run_engine_health_gate()

    requested_mode = args.mode
    requested_run_date = _resolve_run_date(args.date)
    _now_et = time_utils.convert_utc_to_et(datetime.now(timezone.utc))
    effective_mode = _resolve_effective_mode(requested_mode, requested_run_date, _now_et)
    fixture_path = _resolve_cli_fixture_path(
        effective_mode=effective_mode,
        fixture_file=args.fixture_file,
        requested_run_date=requested_run_date,
    )
    run_date = _effective_run_date(effective_mode, requested_run_date, fixture_path, args.date is not None)

    result = execute_run(
        mode=effective_mode,
        run_date=run_date,
        fixture_file=fixture_path,
        notify_mode=args.notify_mode,
    )
    return 0 if result["status"] == SUMMARY_STATUS_SUCCESS else 1


def execute_prefetch() -> int:
    """L1-L4 warm-up: fetch, normalize, validate, derive. No notification, no report."""
    try:
        raw = fetch_all()
        normed = normalize_all(raw)
        val = validate_quotes(normed)
        if not val.system_halted:
            compute_all_derived(val.valid_quotes)
        logger.info("Prefetch complete")
        return 0
    except Exception as exc:
        logger.exception("Prefetch failed: %s", exc)
        return 1


def execute_run(
    mode: str,
    run_date: date,
    fixture_file: Optional[Path] = None,
    notify_mode: Optional[str] = None,
) -> dict[str, Any]:
    errors: list[str] = []
    report_path: Optional[Path] = None
    summary_path: Optional[Path] = None

    try:
        pipeline = _run_pipeline(mode=mode, run_date=run_date, fixture_file=fixture_file, notify_mode=notify_mode)
        report_path = Path(pipeline.report_path)
        summary_path, latest_path = _write_summary_files(
            pipeline.summary,
            pipeline.run_at_utc,
        )

        verification = verify_run_summary(str(latest_path))
        _write_markdown_report(
            pipeline.report,
            pipeline.date_str,
            "PASS" if verification["pass"] else "FAIL",
        )

        pipeline.summary["warnings"] = list(dict.fromkeys(pipeline.summary["warnings"] + verification["warnings"]))
        pipeline.summary["errors"] = list(dict.fromkeys(pipeline.summary["errors"] + verification["errors"]))
        pipeline.summary["status"] = (
            SUMMARY_STATUS_SUCCESS
            if verification["pass"] and pipeline.summary["status"] == SUMMARY_STATUS_SUCCESS
            else SUMMARY_STATUS_FAIL
        )
        _rewrite_summary_file(summary_path, pipeline.summary)
        _rewrite_summary_file(latest_path, pipeline.summary)
        _write_contract_file(pipeline.contract)
        _write_payload_artifacts(pipeline.contract)
        _previous_market_map = _load_previous_market_map()
        _enhanced_market_map = inject_lifecycle(pipeline.market_map, _previous_market_map)
        _write_market_map_file(_enhanced_market_map)
        _write_macro_snapshot(pipeline.contract)
        return pipeline.summary
    except Exception as exc:
        logger.exception("Run failed")
        errors.append(str(exc))
        failure_at = datetime.now(timezone.utc)
        generation_id = _generation_id(mode, failure_at, fixture_file)
        error_contract = build_error_contract(
            generated_at=failure_at,
            generation_id=generation_id,
            artifacts={"report_path": str(report_path) if report_path else None},
            error_detail=str(exc)[:200],
        )
        error_contract["outcome"] = OUTCOME_HALT
        _write_contract_file(error_contract)
        _write_payload_artifacts(error_contract)
        timestamped_path, latest_path = _write_summary_files(
            _failure_summary(
                mode=mode,
                run_date=run_date,
                errors=errors,
                report_path=report_path,
                generated_at=failure_at,
                generation_id=generation_id,
            ),
            failure_at,
        )
        _write_markdown_report(
            _failure_report(run_date, errors),
            run_date.isoformat(),
            "FAIL",
        )
        summary = json.loads(latest_path.read_text(encoding="utf-8"))
        summary["status"] = SUMMARY_STATUS_FAIL
        _rewrite_summary_file(timestamped_path, summary)
        _rewrite_summary_file(latest_path, summary)
        return summary


def _hourly_rr(candidate: Any) -> float:
    risk = abs(candidate.entry_price - candidate.stop_price)
    reward = abs(candidate.target_price - candidate.entry_price)
    return reward / risk if risk > 0 else 0.0


def _build_hourly_candidate_lines(
    qualified_trades: list[Any],
    execution_structure: dict[str, Any],
    candidates: dict[str, Any],
    limit: int = 5,
) -> tuple[str, ...]:
    lines = []
    for trade in qualified_trades[:limit]:
        symbol = trade.symbol
        if not is_tradable_symbol(symbol):
            continue
        if symbol not in execution_structure or symbol not in candidates:
            continue
        structure = execution_structure[symbol].structure
        rr = _hourly_rr(candidates[symbol])
        lines.append(f"{symbol} | {trade.direction} | {structure} | {rr:.1f}:1")
    return tuple(lines)


def _load_flow() -> Optional[dict]:
    """Single authoritative call site for flow snapshot loading.

    Reads flow_data_path from config.toml [flow] section via config.get_flow_data_path().
    Returns snapshot.symbols when path is set; None when path is absent/empty.
    Raises on any load or parse failure — never returns a partial result.
    """
    path = config.get_flow_data_path()
    if path is None:
        return None
    return load_flow_snapshot(path).symbols


def _execute_notify_run(mode: str, run_date: date, notify_mode: str) -> dict[str, Any]:
    """Lightweight path for non-premarket notify modes.

    Runs the appropriate pipeline depth, formats a mode-specific alert,
    and returns a minimal status dict. Does not write markdown or summary JSON.
    """
    date_str = run_date.isoformat()
    try:
        raw_quotes = fetch_all()
        normalized_quotes = normalize_all(raw_quotes)
        fetch_failures = extract_fetch_failures(raw_quotes)
        validation_summary = validate_quotes(normalized_quotes, fetch_failures)

        regime: Optional[RegimeState] = None
        router_state = SectorRouterState(
            mode="MIXED",
            energy_score=0.0,
            index_score=0.0,
            computed_at_utc=datetime.now(timezone.utc),
            session_date=run_date.isoformat(),
        )
        qualification_summary: Optional[QualificationSummary] = None
        candidate_lines: tuple[str, ...] = ()
        derived: dict[str, Any] = {}
        structure: dict[str, Any] = {}
        intraday_metrics: dict[str, Any] = {}
        ohlcv: dict[str, pd.DataFrame] = {}

        if not validation_summary.system_halted:
            regime = compute_regime(validation_summary.valid_quotes)
            derived = compute_all_derived(validation_summary.valid_quotes)
            router_state = resolve_sector_router(
                validation_summary.valid_quotes,
                derived,
                datetime.now(timezone.utc),
                state_path=_sector_router_state_path(mode),
            )

            flow_snapshot = _load_flow()

            if notify_mode in _QUALIFY_ONLY_MODES:
                log_universe_configuration(logger)
                structure = classify_all_structure(validation_summary.valid_quotes, derived, regime.vix_level)
                execution_quotes = filter_execution_dict(validation_summary.valid_quotes, log=logger)
                execution_derived = filter_execution_dict(derived, log=logger)
                execution_structure = filter_execution_dict(structure, log=logger)
                candidates = generate_candidates(execution_structure, execution_derived, execution_quotes, regime)
                candidates, _ = _apply_intraday_short_permission(candidates, execution_quotes)
                ohlcv = {
                    symbol: df
                    for symbol in candidates
                    if (df := fetch_ohlcv(symbol)) is not None
                }
                qualification_summary = qualify_all(
                    regime,
                    execution_structure,
                    candidates or None,
                    execution_derived,
                    ohlcv=ohlcv,
                    now_et=time_utils.convert_utc_to_et(datetime.now(timezone.utc)),
                    flow_snapshot=flow_snapshot,
                )
                qualification_summary, _ = apply_sector_router(
                    qualification_summary,
                    router_state,
                    datetime.now(timezone.utc),
                )
                _log_continuation_audit(regime, qualification_summary)

            elif notify_mode in _HOURLY_MODES and regime.posture != "STAY_FLAT":
                log_universe_configuration(logger)
                structure = classify_all_structure(validation_summary.valid_quotes, derived, regime.vix_level)
                execution_quotes = filter_execution_dict(validation_summary.valid_quotes, log=logger)
                execution_derived = filter_execution_dict(derived, log=logger)
                execution_structure = filter_execution_dict(structure, log=logger)
                candidates = generate_candidates(execution_structure, execution_derived, execution_quotes, regime)
                candidates, _ = _apply_intraday_short_permission(candidates, execution_quotes)
                ohlcv = {
                    symbol: df
                    for symbol in candidates
                    if (df := fetch_ohlcv(symbol)) is not None
                }
                qualification_summary = qualify_all(
                    regime,
                    execution_structure,
                    candidates or None,
                    execution_derived,
                    ohlcv=ohlcv,
                    now_et=time_utils.convert_utc_to_et(datetime.now(timezone.utc)),
                    flow_snapshot=flow_snapshot,
                )
                qualification_summary, _ = apply_sector_router(
                    qualification_summary,
                    router_state,
                    datetime.now(timezone.utc),
                )
                _log_continuation_audit(regime, qualification_summary)
                candidate_lines = _build_hourly_candidate_lines(
                    qualification_summary.qualified_trades,
                    execution_structure,
                    candidates,
                )

        if notify_mode in _HOURLY_MODES:
            alert_title, alert_body = format_hourly_notification(
                asof_utc=regime.computed_at_utc if regime is not None else datetime.now(timezone.utc),
                regime=regime,
                validation_summary=validation_summary,
                qualification_summary=qualification_summary,
                candidate_lines=candidate_lines,
                halt_reason=validation_summary.halt_reason if validation_summary.system_halted else None,
            )
        else:
            alert_title, alert_body = format_notification(
                notify_mode=notify_mode,
                date_str=date_str,
                regime=regime,
                router_mode=router_state.mode,
                energy_score=router_state.energy_score,
                index_score=router_state.index_score,
                validation_summary=validation_summary,
                qualification_summary=qualification_summary,
                normalized_quotes=normalized_quotes,
                outcome=OUTCOME_NO_TRADE,
            )

        alert_sent = False
        notification_result: Optional[NotificationResult] = None
        if mode == MODE_LIVE:
            alert_sent = send_notification(alert_title, alert_body)
            notification_result = get_last_notification_result()

        if notify_mode in _HOURLY_MODES:
            run_at_utc = regime.computed_at_utc if regime is not None else datetime.now(timezone.utc)
            contract = _build_hourly_contract(
                mode=mode,
                run_at_utc=run_at_utc,
                run_date=run_date,
                raw_quotes=raw_quotes,
                normalized_quotes=normalized_quotes,
                validation_summary=validation_summary,
                regime=regime,
                router_state=router_state,
                qualification_summary=qualification_summary,
                errors=[],
                alert_sent=alert_sent,
            )
            summary = _build_hourly_run_summary(
                mode=mode,
                run_at_utc=run_at_utc,
                run_date=run_date,
                notify_mode=notify_mode,
                validation_summary=validation_summary,
                regime=regime,
                router_state=router_state,
                qualification_summary=qualification_summary,
                candidate_lines=candidate_lines,
                alert_title=alert_title,
                alert_body=alert_body,
                alert_sent=alert_sent,
                notification_result=notification_result,
                errors=[],
                status=SUMMARY_STATUS_SUCCESS,
                outcome=OUTCOME_NO_TRADE,
                raw_quotes=raw_quotes,
                normalized_quotes=normalized_quotes,
            )
            _write_hourly_artifacts(summary, contract)
            hourly_market_map = build_market_map(
                generated_at=run_at_utc,
                session_date=run_date.isoformat(),
                mode=mode,
                run_at_utc=run_at_utc,
                normalized_quotes=normalized_quotes,
                derived_metrics=derived,
                structure_results=structure,
                intraday_metrics=intraday_metrics,
                regime=regime,
                watch_summary=None,
                bar_windows=_market_map_bar_windows(ohlcv),
            )
            hourly_market_map["generation_id"] = summary["generation_id"]
            previous_market_map = _load_previous_market_map()
            _write_market_map_file(inject_lifecycle(hourly_market_map, previous_market_map))
            _write_trend_structure_snapshot(
                normalized_quotes=normalized_quotes,
                history_by_symbol=ohlcv,
                generated_at=run_at_utc,
            )
            if not validation_summary.system_halted:
                _write_watchlist_snapshot(
                    normalized_quotes=normalized_quotes,
                    generated_at=run_at_utc,
                )

        return {"status": SUMMARY_STATUS_SUCCESS, "suppressed": False}

    except Exception as exc:
        import traceback as _tb
        logger.exception("notify-mode run failed: %s", exc)
        if notify_mode in _HOURLY_MODES:
            Path("traceback.txt").write_text(_tb.format_exc(), encoding="utf-8")
        alert_title, alert_body = format_failure_notification(notify_mode, date_str, str(exc)[:120])
        alert_sent = False
        failure_notification_result: Optional[NotificationResult] = None
        try:
            alert_sent = send_notification(alert_title, alert_body)
            failure_notification_result = get_last_notification_result()
        except Exception as _notify_exc:
            logger.warning("Failed to send failure notification: %s", _notify_exc)
        if notify_mode in _HOURLY_MODES:
            failure_at = datetime.now(timezone.utc)
            generation_id = _generation_id("hourly", failure_at, None)
            error_contract = build_error_contract(
                generated_at=failure_at,
                generation_id=generation_id,
                artifacts={
                    "report_path": str(HOURLY_REPORT_PATH),
                    "log_path": str(LATEST_HOURLY_RUN_PATH),
                    "notification_sent": alert_sent,
                },
                error_detail=str(exc)[:200],
            )
            error_contract["outcome"] = OUTCOME_HALT
            failure_summary = _build_hourly_run_summary(
                mode=mode,
                run_at_utc=failure_at,
                run_date=run_date,
                notify_mode=notify_mode,
                validation_summary=None,
                regime=None,
                router_state=None,
                qualification_summary=None,
                candidate_lines=(),
                alert_title=alert_title,
                alert_body=alert_body,
                alert_sent=alert_sent,
                notification_result=failure_notification_result,
                errors=[str(exc)],
                status=SUMMARY_STATUS_FAIL,
                outcome=OUTCOME_HALT,
                raw_quotes={},
                normalized_quotes={},
            )
            _write_hourly_artifacts(failure_summary, error_contract)
        return {"status": SUMMARY_STATUS_FAIL, "suppressed": False}


def _run_pipeline(
    mode: str,
    run_date: date,
    fixture_file: Optional[Path],
    notify_mode: Optional[str] = None,
) -> PipelineResult:
    fixture_backed = _is_fixture_backed(mode, fixture_file)
    run_at_utc = _deterministic_run_at(mode, fixture_file) if mode == MODE_FIXTURE else datetime.now(timezone.utc)
    generation_id = _generation_id(mode, run_at_utc, fixture_file)
    date_str = run_date.isoformat()
    warnings: list[str] = []
    errors: list[str] = []

    now_et = time_utils.convert_utc_to_et(run_at_utc)
    _log_time_diagnostics(run_at_utc, now_et)

    if mode == MODE_SUNDAY and not fixture_backed:
        # Sunday non-live path: no data fetch, forced STAY_FLAT.
        raw_quotes: dict[str, RawQuote] = {}
        normalized_quotes: dict[str, NormalizedQuote] = {}
        validation_summary = ValidationSummary(
            system_halted=False,
            halt_reason=None,
            failed_halt_symbols=[],
            results={},
            valid_quotes={},
            invalid_symbols={},
            symbols_attempted=0,
            symbols_validated=0,
            symbols_failed=0,
        )
    else:
        raw_quotes, normalized_quotes = _load_inputs(mode, fixture_file)
        fetch_failures = extract_fetch_failures(raw_quotes) if raw_quotes else None
        with _fixture_validation_clock(mode, fixture_file, normalized_quotes):
            validation_summary = validate_quotes(normalized_quotes, fetch_failures)

    regime: Optional[RegimeState] = None
    correlation_result: Optional[CorrelationResult] = None
    router_state = SectorRouterState(
        mode="MIXED",
        energy_score=0.0,
        index_score=0.0,
        computed_at_utc=run_at_utc,
        session_date=date_str,
    )
    qualification_summary: Optional[QualificationSummary] = None
    watch_summary: Optional[WatchSummary] = None
    candidates_generated = 0
    option_setups: list[OptionSetup] = []
    trade_decisions: list[TradeDecision] = []
    suppressed_candidates: list[SuppressedCandidate] = []
    intraday_state_context: dict[str, dict[str, Any]] = {}
    chain_results: dict[str, ChainValidationResult] = {}
    derived: dict[str, Any] = {}
    structure: dict[str, Any] = {}
    intraday_metrics: dict[str, Any] = {}
    ohlcv: dict[str, pd.DataFrame] = {}
    outcome = OUTCOME_NO_TRADE
    overall_pressure = "UNKNOWN"
    thesis_map: dict = {}
    invalidation_guidance_map: dict = {}
    entry_quality_map: dict = {}

    if validation_summary.system_halted:
        errors.append(validation_summary.halt_reason or "system halted")
        outcome = OUTCOME_HALT
    else:
        regime = compute_regime(validation_summary.valid_quotes)
        correlation_result = compute_correlation(validation_summary.valid_quotes)
        policy_context: PolicyContext = evaluate_policy(correlation_result)

        if mode != MODE_SUNDAY:
            with _fixture_cache_only_ohlcv(mode, fixture_file):
                derived = compute_all_derived(validation_summary.valid_quotes)
            router_state = resolve_sector_router(
                validation_summary.valid_quotes,
                derived,
                run_at_utc,
                state_path=_sector_router_state_path(mode),
            )
            structure = classify_all_structure(validation_summary.valid_quotes, derived, regime.vix_level)
            log_universe_configuration(logger)
            execution_quotes = filter_execution_dict(validation_summary.valid_quotes, log=logger)
            execution_derived = filter_execution_dict(derived, log=logger)
            execution_structure = filter_execution_dict(structure, log=logger)
            if mode == MODE_FIXTURE:
                intraday_metrics, ignored_watch_symbols = ({}, sorted(execution_quotes))
            else:
                intraday_metrics, ignored_watch_symbols = compute_all_intraday_metrics(list(execution_quotes))
            watch_summary = classify_watchlist(
                execution_structure,
                execution_derived,
                intraday_metrics,
                regime,
                asof=run_at_utc,
                ignored_symbols=ignored_watch_symbols,
            )
            watch_summary = WatchSummary(
                session=watch_summary.session,
                threshold=watch_summary.threshold,
                watchlist=filter_execution_items(watch_summary.watchlist, symbol_getter=lambda item: item.symbol, log=logger),
                ignored_symbols=watch_summary.ignored_symbols,
                execution_posture=watch_summary.execution_posture,
            )
            candidates = generate_candidates(execution_structure, execution_derived, execution_quotes, regime)
            if mode != MODE_FIXTURE:
                candidates, intraday_state_context = _apply_intraday_short_permission(candidates, execution_quotes)
            candidates_generated = len(candidates)
            ohlcv = {
                symbol: df
                for symbol in candidates
                if (df := fetch_ohlcv(symbol)) is not None
            }
            qualification_summary = qualify_all(
                regime,
                execution_structure,
                candidates or None,
                execution_derived,
                ohlcv=ohlcv,
                now_et=now_et,
                flow_snapshot=_load_flow(),
            )
            qualification_summary, suppressed_candidates = apply_sector_router(
                qualification_summary,
                router_state,
                run_at_utc,
            )
            _log_continuation_audit(regime, qualification_summary)

            if qualification_summary.qualified_trades:
                option_setups = build_option_setups(
                    qualification_summary.qualified_trades,
                    execution_structure,
                    execution_derived,
                    candidates,
                    risk_modifier=policy_context.risk_modifier,
                )

            if option_setups:
                if mode == MODE_FIXTURE:
                    chain_results = _fixture_chain_results(option_setups)
                    warnings.extend(_chain_warning_lines(chain_results))
                else:
                    chain_results = validate_option_chains(option_setups, validation_summary.valid_quotes)
                    warnings.extend(_chain_warning_lines(chain_results))

            if option_setups:
                setup_by_symbol = {setup.symbol: setup for setup in option_setups}
                qualified_by_symbol = {
                    result.symbol: result for result in qualification_summary.qualified_trades
                }
                trade_decisions = [
                    create_trade_decision(
                        candidates[symbol],
                        qualified_by_symbol[symbol],
                        setup,
                        chain_results.get(symbol, _validated_chain_result(symbol)),
                    )
                    for symbol, setup in setup_by_symbol.items()
                ]
                overall_pressure = _compute_overall_pressure(normalized_quotes)
                trade_decisions = apply_execution_policy_to_decisions(
                    trade_decisions,
                    market_regime=regime.regime if regime is not None else None,
                    posture=regime.posture if regime is not None else None,
                    confidence=regime.confidence if regime is not None else 0.0,
                    timestamp=run_at_utc,
                    session_state=_load_execution_policy_session_state(run_at_utc, date_str),
                    orb_states=_build_execution_policy_orb_states(
                        trade_decisions,
                        qualified_by_symbol,
                        intraday_metrics,
                    ),
                    overall_pressure=overall_pressure,
                )
                trade_decisions, thesis_map = apply_thesis_gate(
                    trade_decisions,
                    candidates,
                    qualified_by_symbol,
                    execution_structure,
                    overall_pressure,
                )
                trade_decisions, invalidation_guidance_map = apply_invalidation_gate(
                    trade_decisions,
                    thesis_map,
                    overall_pressure,
                )
                trade_decisions, entry_quality_map = apply_entry_quality_gate(
                    trade_decisions,
                    candidates,
                    qualified_by_symbol,
                    execution_structure,
                    thesis_map,
                )

            outcome = (
                OUTCOME_TRADE
                if any(decision.status == ALLOW_TRADE for decision in trade_decisions)
                else OUTCOME_NO_TRADE
            )

    market_map = build_market_map(
        generated_at=run_at_utc,
        session_date=date_str,
        mode=mode,
        run_at_utc=run_at_utc,
        normalized_quotes=normalized_quotes,
        derived_metrics=derived,
        structure_results=structure,
        intraday_metrics=intraday_metrics,
        regime=regime,
        watch_summary=watch_summary,
        bar_windows=_market_map_bar_windows(ohlcv),
    )
    market_map["generation_id"] = generation_id

    visibility_map = build_visibility_map(trade_decisions, market_map)
    explanation_map = build_explanation_map(trade_decisions, visibility_map, overall_pressure)

    report = render_report(
        date_str=date_str,
        run_at_utc=run_at_utc,
        regime=regime,
        router_mode=router_state.mode,
        energy_score=router_state.energy_score,
        index_score=router_state.index_score,
        validation_summary=validation_summary,
        qualification_summary=qualification_summary,
        watch_summary=watch_summary,
        option_setups=option_setups,
        outcome=outcome,
        halt_reason=validation_summary.halt_reason,
        chain_results=chain_results,
    )
    _write_markdown_report(report, date_str, "NOT RUN")
    report_path = str(REPORTS_DIR / f"{date_str}.md")

    # Build contract before sending notification so build_notification_message
    # can derive message content from the canonical contract.
    contract_status = derive_run_status(outcome, regime, validation_summary.system_halted)
    data_quality = _data_status(mode, raw_quotes, normalized_quotes, fixture_file)
    contract = build_pipeline_output_contract(
        _PartialPipelineResult(
            mode=mode,
            generation_id=generation_id,
            run_at_utc=run_at_utc,
            date_str=date_str,
            raw_quotes=raw_quotes,
            normalized_quotes=normalized_quotes,
            validation_summary=validation_summary,
            regime=regime,
            router_mode=router_state.mode,
            qualification_summary=qualification_summary,
            watch_summary=watch_summary,
            option_setups=option_setups,
            chain_results=chain_results,
            alert_sent=False,
            report_path=report_path,
            errors=errors,
            correlation=correlation_result,
            trade_decisions=trade_decisions,
            thesis_map=thesis_map,
            invalidation_guidance_map=invalidation_guidance_map,
            entry_quality_map=entry_quality_map,
        ),
        generated_at=run_at_utc,
        status=contract_status,
        artifacts={"report_path": report_path, "log_path": str(LATEST_RUN_PATH)},
        data_quality=data_quality,
    )
    contract["outcome"] = outcome
    # Inject dashboard-readable fields into system_state
    _ss_regime_label, _ss_posture_label, _ss_conf, _ = _summary_regime_fields(regime)
    _ss_perm = _PERMISSION_LINES.get(_ss_posture_label, "No new trades permitted.")
    if validation_summary.system_halted:
        _ss_perm = "No trades permitted. System halted."
    contract["system_state"]["outcome"] = outcome
    contract["system_state"]["permission"] = _ss_perm
    contract["system_state"]["reason"] = contract["system_state"].get("stay_flat_reason")
    contract = apply_overnight_policy(
        contract=contract,
        market_map=market_map,
        timestamp=run_at_utc,
    )

    if mode == MODE_SUNDAY:
        contract["system_state"]["stay_flat_reason"] = "PREMARKET_CONTEXT"
        contract["system_state"]["session_type"] = "SUNDAY_PREMARKET"

    # Exactly one notification send per run. PRD-018 suppression gate applied
    # before send; state persisted only on confirmed success (R7).
    alert_sent = False
    if mode in {MODE_LIVE, MODE_SUNDAY} and not fixture_backed:
        current_key = notification_state_key(contract)
        priority = classify_notification_priority(contract)
        last_key = load_last_state(LAST_STATE_PATH)

        if should_send(current_key, priority, last_key):
            title, body = build_notification_message(contract)
            alert_sent = send_notification(
                title,
                body,
                notification_priority=priority.value,
                notification_state_key=current_key,
            )
            if alert_sent:
                save_last_state(current_key, LAST_STATE_PATH)
        else:
            write_notification_audit(
                transport="telegram",
                alert_title="suppressed",
                attempted=False,
                success=False,
                reason="suppressed_unchanged_state",
                priority=priority.value,
                state_key=current_key,
            )

    contract["artifacts"]["notification_sent"] = alert_sent

    run_history = _load_run_history(LOGS_DIR / "audit.jsonl")
    premarket_report = build_premarket_report(contract)
    postmarket_report = build_postmarket_report(contract, run_history)

    audit_record = write_audit_record(
        run_at_utc=run_at_utc,
        date_str=date_str,
        outcome=outcome,
        regime=regime,
        router_mode=router_state.mode,
        energy_score=router_state.energy_score,
        index_score=router_state.index_score,
        validation_summary=validation_summary,
        qualification_summary=qualification_summary,
        watch_summary=watch_summary,
        option_setups=option_setups,
        trade_decisions=trade_decisions,
        suppressed_candidates=suppressed_candidates,
        halt_reason=validation_summary.halt_reason,
        alert_sent=alert_sent,
        report_path=report_path,
        intraday_state_context=intraday_state_context,
    )
    run_post_trade_evaluation(current_run_at_utc=run_at_utc)
    run_performance_engine(
        evaluation_log_path=LOGS_DIR / "evaluation.jsonl",
        output_path=LOGS_DIR / "performance_summary.json",
    )

    summary = _build_run_summary(
        mode=mode,
        generation_id=generation_id,
        run_at_utc=run_at_utc,
        raw_quotes=raw_quotes,
        normalized_quotes=normalized_quotes,
        validation_summary=validation_summary,
        regime=regime,
        router_mode=router_state.mode,
        energy_score=router_state.energy_score,
        index_score=router_state.index_score,
        qualification_summary=qualification_summary,
        watch_summary=watch_summary,
        candidates_generated=candidates_generated,
        option_setups=option_setups,
        trade_decisions=trade_decisions,
        chain_results=chain_results,
        warnings=warnings,
        errors=errors,
        fixture_file=fixture_file,
        outcome=outcome,
    )

    return PipelineResult(
        mode=mode,
        generation_id=generation_id,
        run_at_utc=run_at_utc,
        date_str=date_str,
        raw_quotes=raw_quotes,
        normalized_quotes=normalized_quotes,
        validation_summary=validation_summary,
        regime=regime,
        router_mode=router_state.mode,
        energy_score=router_state.energy_score,
        index_score=router_state.index_score,
        qualification_summary=qualification_summary,
        watch_summary=watch_summary,
        candidates_generated=candidates_generated,
        option_setups=option_setups,
        trade_decisions=trade_decisions,
        suppressed_candidates=suppressed_candidates,
        chain_results=chain_results,
        outcome=outcome,
        alert_sent=alert_sent,
        report=report,
        report_path=report_path,
        audit_record=audit_record,
        warnings=warnings,
        errors=errors,
        summary=summary,
        contract=contract,
        correlation=correlation_result,
        premarket_report=premarket_report,
        postmarket_report=postmarket_report,
        market_map=market_map,
        visibility_map=visibility_map,
        explanation_map=explanation_map,
    )


def _market_map_bar_windows(ohlcv: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Return primary-symbol OHLCV windows already available in this runtime pass."""
    primary_symbols = {"SPY", "QQQ", "GDX", "GLD", "SLV", "XLE"}
    return {symbol: frame for symbol, frame in ohlcv.items() if symbol in primary_symbols}


def _build_run_summary(
    mode: str,
    generation_id: str,
    run_at_utc: datetime,
    raw_quotes: dict[str, RawQuote],
    normalized_quotes: dict[str, NormalizedQuote],
    validation_summary: ValidationSummary,
    regime: Optional[RegimeState],
    router_mode: str,
    energy_score: float,
    index_score: float,
    qualification_summary: Optional[QualificationSummary],
    watch_summary: Optional[WatchSummary],
    candidates_generated: int,
    option_setups: list[OptionSetup],
    trade_decisions: list[TradeDecision],
    chain_results: dict[str, ChainValidationResult],
    warnings: list[str],
    errors: list[str],
    fixture_file: Optional[Path],
    outcome: str,
) -> dict[str, Any]:
    fallback_used = any(raw.source == "polygon" for raw in raw_quotes.values())
    data_status = _data_status(mode, raw_quotes, normalized_quotes, fixture_file)
    kill_switch = _kill_switch(regime, normalized_quotes)
    validated_count = sum(1 for decision in trade_decisions if decision.status == ALLOW_TRADE)
    if kill_switch:
        validated_count = 0

    summary_mode = {
        MODE_LIVE: SUMMARY_MODE_LIVE,
        MODE_FIXTURE: SUMMARY_MODE_FIXTURE,
        MODE_SUNDAY: SUMMARY_MODE_SUNDAY,
    }[mode]

    regime_label, posture_label, confidence, net_score = _summary_regime_fields(regime)
    permission = _PERMISSION_LINES.get(posture_label, "No new trades permitted.")
    if validation_summary.system_halted:
        permission = "No trades permitted. System halted."

    summary = {
        "run_id": _run_id(mode, run_at_utc, fixture_file),
        "generation_id": generation_id,
        "timestamp": _iso_z(run_at_utc),
        "run_at_utc": _iso_z(run_at_utc),
        "mode": summary_mode,
        "outcome": outcome,
        "status": SUMMARY_STATUS_FAIL if validation_summary.system_halted or errors else SUMMARY_STATUS_SUCCESS,
        "regime": regime_label,
        "posture": posture_label,
        "confidence": confidence,
        "net_score": net_score,
        "router_mode": router_mode,
        "energy_score": round(energy_score, 2),
        "index_score": round(index_score, 2),
        "permission": permission,
        "kill_switch": kill_switch,
        "min_rr_applied": _min_rr_for_regime(regime),
        "data_status": data_status,
        "fallback_used": fallback_used,
        "system_halted": validation_summary.system_halted,
        "halt_reason": validation_summary.halt_reason,
        "candidates_generated": 0 if mode == MODE_SUNDAY else candidates_generated,
        "candidates_qualified": 0 if mode == MODE_SUNDAY else validated_count,
        "candidates_watchlist": 0 if qualification_summary is None else qualification_summary.symbols_watchlist,
        "continuation_audit": None if qualification_summary is None else qualification_summary.continuation_audit,
        "watch_candidates": 0 if watch_summary is None else len(watch_summary.watchlist),
        "chain_validation": {
            symbol: {
                "classification": result.classification,
                "reason": result.reason,
            }
            for symbol, result in sorted(chain_results.items())
        },
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
    return summary


def _apply_intraday_short_permission(
    candidates: dict[str, Any],
    execution_quotes: dict[str, NormalizedQuote],
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    filtered = dict(candidates)
    context: dict[str, dict[str, Any]] = {}

    for symbol, candidate in candidates.items():
        if candidate.direction != "SHORT":
            continue

        intraday_df = fetch_intraday_bars(symbol)
        if intraday_df is None or intraday_df.empty:
            continue

        symbol_bars = _intraday_state_bars_from_df(intraday_df)
        if not symbol_bars:
            continue

        previous_close = _reconstruct_previous_close(execution_quotes.get(symbol))
        try:
            intra_state = compute_intraday_state(symbol, symbol_bars, previous_close=previous_close)
            intraday_state_available = intra_state is not None
        except Exception as exc:
            logger.info("Skipping intraday short gate for %s: %s", symbol, exc)
            intra_state = None
            intraday_state_available = False

        if not intraday_state_available:
            logger.debug("[INTRA] state unavailable — fail-open applied")
            context[symbol] = {"intraday_state_available": False}
            continue

        downside_permission = _downside_permission_from_state(intra_state)
        context[symbol] = {
            "downside_permission": downside_permission,
            "intraday_state": intra_state.state,
            "intraday_state_available": True,
        }
        if not downside_permission:
            filtered.pop(symbol, None)
            logger.info("SUPPRESSED %s: SHORT blocked pending downside permission", symbol)

    return filtered, context


def _compute_overall_pressure(normalized_quotes: dict) -> str:
    try:
        macro_drivers = _build_macro_drivers(normalized_quotes)
        snapshot = build_macro_pressure(macro_drivers)
        return snapshot["overall_pressure"]
    except Exception as exc:
        logger.warning("build_macro_pressure failed, defaulting to UNKNOWN: %s", exc)
        return "UNKNOWN"


def _load_execution_policy_session_state(run_at_utc: datetime, date_str: str) -> ExecutionSessionState:
    return load_execution_session_state(
        run_at_utc=run_at_utc,
        session_date=date_str,
        audit_log_path=LOGS_DIR / "audit.jsonl",
        evaluation_log_path=LOGS_DIR / "evaluation.jsonl",
    )


def _build_execution_policy_orb_states(
    trade_decisions: list[TradeDecision],
    qualified_by_symbol: dict[str, Any],
    intraday_metrics: dict[str, Any],
) -> dict[str, OrbPolicyState]:
    states: dict[str, OrbPolicyState] = {}
    for decision in trade_decisions:
        qualified = qualified_by_symbol.get(decision.ticker)
        continuation_breakout = getattr(qualified, "entry_mode", None) == ENTRY_MODE_CONTINUATION
        metrics = intraday_metrics.get(decision.ticker)
        if metrics is None:
            states[decision.ticker] = OrbPolicyState(
                price=decision.entry,
                continuation_breakout=continuation_breakout,
            )
            continue
        states[decision.ticker] = OrbPolicyState(
            price=decision.entry,
            orb_high=getattr(metrics, "orb_high", None),
            orb_low=getattr(metrics, "orb_low", None),
            continuation_breakout=continuation_breakout,
        )
    return states


def _log_continuation_audit(
    regime: Optional[RegimeState],
    qualification_summary: Optional[QualificationSummary],
) -> None:
    if regime is None or regime.regime != EXPANSION or qualification_summary is None:
        return

    audit = qualification_summary.continuation_audit
    if not audit:
        return

    logger.info("[CONTINUATION_AUDIT]")
    logger.info("total_candidates=%d", audit["total_candidates"])
    logger.info("accepted=%d", audit["accepted"])
    logger.info("")
    logger.info("rejections:")
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
        logger.info("%s=%d", reason, audit.get(reason, 0))


def _intraday_state_bars_from_df(df: pd.DataFrame) -> list[IntradayStateBar]:
    frame = df.copy()
    frame.index = pd.to_datetime(frame.index, utc=True)
    bars: list[IntradayStateBar] = []
    for ts, row in frame.iterrows():
        bars.append(
            IntradayStateBar(
                timestamp=ts.to_pydatetime(),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"]),
            )
        )
    return bars


def _reconstruct_previous_close(quote: Optional[NormalizedQuote]) -> Optional[float]:
    if quote is None:
        return None
    denominator = 1.0 + quote.pct_change_decimal
    if denominator <= 0:
        return None
    return quote.price / denominator


def _downside_permission_from_state(intra_state: Any) -> bool:
    if intra_state.gap_type != "DOWN":
        return True
    if intra_state.phase == "OPEN":
        return False
    if intra_state.orb_break_direction == "SHORT" and not (
        intra_state.failed_reclaim or intra_state.acceptance_below_level
    ):
        return False
    if intra_state.failed_reclaim or intra_state.acceptance_below_level:
        return True
    return False


def verify_run_summary(path: str) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    file_path = Path(path)

    if not file_path.exists():
        return {"pass": False, "warnings": [], "errors": [f"file not found: {path}"]}

    try:
        summary = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"pass": False, "warnings": [], "errors": [f"invalid JSON: {exc}"]}

    required_fields = {
        "run_id",
        "timestamp",
        "mode",
        "outcome",
        "status",
        "regime",
        "posture",
        "confidence",
        "net_score",
        "permission",
        "kill_switch",
        "min_rr_applied",
        "data_status",
        "fallback_used",
        "system_halted",
        "halt_reason",
        "candidates_generated",
        "candidates_qualified",
        "candidates_watchlist",
        "chain_validation",
        "warnings",
        "errors",
    }
    missing = sorted(required_fields - set(summary))
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    _nullable_summary_fields = frozenset({"halt_reason", "continuation_audit"})
    for key, value in summary.items():
        if value is None and key not in _nullable_summary_fields:
            errors.append(f"{key} must not be null")

    if summary.get("mode") not in {SUMMARY_MODE_LIVE, SUMMARY_MODE_FIXTURE, SUMMARY_MODE_SUNDAY}:
        errors.append(f"invalid mode: {summary.get('mode')}")
    if summary.get("outcome") not in {OUTCOME_TRADE, OUTCOME_NO_TRADE, OUTCOME_HALT}:
        errors.append(f"invalid outcome: {summary.get('outcome')}")
    if summary.get("status") not in {SUMMARY_STATUS_SUCCESS, SUMMARY_STATUS_FAIL}:
        errors.append(f"invalid status: {summary.get('status')}")
    if summary.get("regime") not in VALID_REGIMES:
        errors.append(f"invalid regime: {summary.get('regime')}")
    if summary.get("posture") not in VALID_POSTURES:
        errors.append(f"invalid posture: {summary.get('posture')}")
    confidence = summary.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0.0 <= confidence <= 1.0:
        errors.append(f"confidence out of range: {confidence}")

    net_score = summary.get("net_score")
    if not isinstance(net_score, int) or not -8 <= net_score <= 8:
        errors.append(f"net_score out of range: {net_score}")

    data_status = summary.get("data_status")
    if data_status not in {"ok", "fallback", "stale"}:
        errors.append(f"invalid data_status: {data_status}")

    try:
        raw_timestamp = summary.get("timestamp")
        if not isinstance(raw_timestamp, str) or "T" not in raw_timestamp:
            raise ValueError("timestamp must be an ISO-8601 datetime string")
        ts = datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        if summary.get("mode") in {SUMMARY_MODE_LIVE, SUMMARY_MODE_SUNDAY}:
            age = datetime.now(timezone.utc) - ts.astimezone(timezone.utc)
            if age.total_seconds() > 6 * 3600:
                errors.append(f"timestamp older than 6 hours: {summary.get('timestamp')}")
    except Exception:
        errors.append(f"invalid timestamp: {summary.get('timestamp')}")

    if summary.get("kill_switch") and summary.get("candidates_qualified") != 0:
        errors.append("kill_switch runs must not qualify trades")
    if summary.get("regime") == CHAOTIC and summary.get("candidates_qualified") != 0:
        errors.append("CHAOTIC runs must not qualify trades")
    if summary.get("posture") == "STAY_FLAT" and summary.get("candidates_qualified") != 0:
        errors.append("STAY_FLAT runs must not qualify trades")
    if summary.get("regime") == NEUTRAL and summary.get("min_rr_applied") != 3.0:
        errors.append("NEUTRAL runs must apply min_rr_applied == 3.0")
    if summary.get("system_halted") and summary.get("status") != SUMMARY_STATUS_FAIL:
        errors.append("system_halted runs must have status FAIL")
    if summary.get("system_halted") and summary.get("outcome") != OUTCOME_HALT:
        errors.append("system_halted runs must have outcome HALT")
    if summary.get("outcome") == OUTCOME_TRADE and summary.get("candidates_qualified", 0) < 1:
        errors.append("TRADE outcome requires qualified candidates")
    if summary.get("outcome") == OUTCOME_NO_TRADE and summary.get("candidates_qualified", 0) > 0:
        errors.append("NO_TRADE outcome cannot qualify trades")
    if summary.get("outcome") == OUTCOME_HALT and not summary.get("system_halted"):
        errors.append("HALT outcome requires system_halted true")

    chain_validation = summary.get("chain_validation")
    if not isinstance(chain_validation, dict):
        errors.append("chain_validation must be an object")
        chain_validation = {}

    invalid_count = 0
    for symbol, payload in chain_validation.items():
        if not isinstance(payload, dict):
            errors.append(f"chain_validation[{symbol}] must be an object")
            continue
        if "classification" not in payload or "reason" not in payload:
            errors.append(f"chain_validation[{symbol}] missing classification or reason")
            continue
        classification = payload["classification"]
        if classification == "DISQUALIFIED_OPTIONS_INVALID":
            warnings.append(f"{symbol}: options invalid")
            invalid_count += 1
        if classification == MANUAL_CHECK:
            warnings.append(f"{symbol}: needs manual chain check")

    if chain_validation and invalid_count == len(chain_validation):
        warnings.append("all candidates invalid at chain validation")

    return {
        "pass": not errors,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }


def _load_inputs(
    mode: str,
    fixture_file: Optional[Path],
) -> tuple[dict[str, RawQuote], dict[str, NormalizedQuote]]:
    if _is_fixture_backed(mode, fixture_file):
        normalized = _load_fixture_quotes(fixture_file)
        raw_quotes = {
            symbol: RawQuote(
                symbol=quote.symbol,
                price=quote.price,
                pct_change_raw=quote.pct_change_decimal,
                volume=quote.volume,
                fetched_at_utc=quote.fetched_at_utc,
                source=quote.source,
                fetch_succeeded=True,
                failure_reason=None,
            )
            for symbol, quote in normalized.items()
        }
        return raw_quotes, normalized

    raw_quotes = fetch_all()
    normalized = normalize_all(raw_quotes)
    return raw_quotes, normalized


def _load_fixture_quotes(path: Optional[Path]) -> dict[str, NormalizedQuote]:
    if path is None:
        raise ValueError("fixture mode requires a fixture file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"fixture file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid fixture JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("fixture file must be a JSON object keyed by symbol")

    quotes: dict[str, NormalizedQuote] = {}
    for symbol, item in payload.items():
        if not isinstance(item, dict):
            raise ValueError(f"fixture[{symbol}] must be an object")
        extra = set(item) - _FIXTURE_QUOTE_FIELDS
        missing = _FIXTURE_QUOTE_FIELDS - set(item)
        if extra or missing:
            raise ValueError(
                f"fixture[{symbol}] schema mismatch; missing={sorted(missing)} extra={sorted(extra)}"
            )
        if item["symbol"] != symbol:
            raise ValueError(f"fixture key mismatch for {symbol}")
        quotes[symbol] = NormalizedQuote(
            symbol=str(item["symbol"]),
            price=float(item["price"]),
            pct_change_decimal=float(item["pct_change_decimal"]),
            volume=None if item["volume"] is None else float(item["volume"]),
            fetched_at_utc=datetime.fromisoformat(str(item["fetched_at_utc"]).replace("Z", "+00:00")).astimezone(timezone.utc),
            source=str(item["source"]),
            units=str(item["units"]),
            age_seconds=float(item["age_seconds"]),
        )
    return quotes

@contextmanager
def _fixture_cache_only_ohlcv(mode: str, fixture_file: Optional[Path]):
    if not _is_fixture_backed(mode, fixture_file):
        yield
        return

    def _cache_only(symbol: str) -> Optional[pd.DataFrame]:
        cache_path = _ohlcv_cache_path(symbol)
        if not cache_path.exists():
            return None
        return pd.read_parquet(cache_path)

    with patch("cuttingboard.derived.fetch_ohlcv", side_effect=_cache_only):
        yield


def _fixture_chain_results(setups: list[OptionSetup]) -> dict[str, ChainValidationResult]:
    results: dict[str, ChainValidationResult] = {}
    for setup in setups:
        results[setup.symbol] = ChainValidationResult(
            symbol=setup.symbol,
            classification=MANUAL_CHECK,
            reason="fixture mode skips live chain validation",
            spread_pct=None,
            open_interest=None,
            volume=None,
            expiry_used=None,
            data_source=None,
        )
    return results


@contextmanager
def _fixture_validation_clock(
    mode: str,
    fixture_file: Optional[Path],
    normalized_quotes: dict[str, NormalizedQuote],
):
    if not _is_fixture_backed(mode, fixture_file) or not normalized_quotes:
        yield
        return

    frozen_now = max(quote.fetched_at_utc for quote in normalized_quotes.values())

    class _FixtureDateTime:
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return frozen_now.replace(tzinfo=None)
            return frozen_now.astimezone(tz)

    with patch("cuttingboard.validation.datetime", _FixtureDateTime):
        yield


def _write_markdown_report(report: str, date_str: str, verification: str) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{date_str}.md"
    body = f"Verification: {verification}\n\n```\n{report}\n```\n"
    path.write_text(body, encoding="utf-8")
    return path


def safe_write_latest(path: str | Path, new_data: dict[str, Any], ts_key: str) -> Path:
    target = Path(path)
    if ts_key not in new_data:
        raise RuntimeError(f"Missing required timestamp field in new data: {ts_key}")

    def _parse_timestamp(value: Any, *, source: str) -> datetime:
        if not isinstance(value, str):
            raise RuntimeError(f"Missing required timestamp field in {source}: {ts_key}")
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise RuntimeError(
                f"Invalid timestamp field in {source}: {ts_key}={value!r}"
            ) from exc

    new_ts = _parse_timestamp(new_data[ts_key], source="new data")
    payload = json.dumps(new_data, indent=2, sort_keys=True) + "\n"

    if not target.exists():
        target.write_text(payload, encoding="utf-8")
        return target

    try:
        existing = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in existing latest artifact: {target}") from exc

    if not isinstance(existing, dict) or ts_key not in existing:
        logger.info("LEGACY_ARTIFACT_OVERWRITE")
        target.write_text(payload, encoding="utf-8")
        return target

    old_ts = _parse_timestamp(existing[ts_key], source="existing data")
    if new_ts > old_ts:
        target.write_text(payload, encoding="utf-8")
    return target


def _write_summary_files(summary: dict[str, Any], run_at_utc: datetime) -> tuple[Path, Path]:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"run_{run_at_utc.strftime('%Y-%m-%d_%H%M%S')}.json"
    timestamped_path = LOGS_DIR / filename
    summary_to_write = dict(summary)
    text = json.dumps(summary_to_write, indent=2, sort_keys=True)
    timestamped_path.write_text(text + "\n", encoding="utf-8")
    safe_write_latest(LATEST_RUN_PATH, summary_to_write, "run_at_utc")
    return timestamped_path, LATEST_RUN_PATH


def _rewrite_summary_file(path: Path, summary: dict[str, Any]) -> None:
    path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_run_history(path: Path, limit: int = 5) -> list[dict]:
    """Return up to `limit` pipeline run records from audit.jsonl (most recent first).

    Filters out notification-event entries. Returns [] on missing file or parse error.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return []
    except Exception:
        logger.exception("Failed to read run history from %s", path)
        return []

    records: list[dict] = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "outcome" in record and "run_at_utc" in record:
            records.append(record)
            if len(records) >= limit:
                break
    return records


def _write_contract_file(contract: dict[str, Any]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    safe_write_latest(LATEST_CONTRACT_PATH, contract, "generated_at")


def _build_hourly_contract(
    *,
    mode: str,
    run_at_utc: datetime,
    run_date: date,
    raw_quotes: dict[str, RawQuote],
    normalized_quotes: dict[str, NormalizedQuote],
    validation_summary: Optional[ValidationSummary],
    regime: Optional[RegimeState],
    router_state: Optional[SectorRouterState],
    qualification_summary: Optional[QualificationSummary],
    errors: list[str],
    alert_sent: bool,
) -> dict[str, Any]:
    generation_id = _generation_id("hourly", run_at_utc, None)
    contract_status = derive_run_status(
        OUTCOME_NO_TRADE,
        regime,
        bool(validation_summary.system_halted) if validation_summary is not None else False,
    )
    data_quality = _data_status(mode, raw_quotes, normalized_quotes, fixture_file=None)
    contract = build_pipeline_output_contract(
        _PartialPipelineResult(
            mode=mode,
            generation_id=generation_id,
            run_at_utc=run_at_utc,
            date_str=run_date.isoformat(),
            raw_quotes=raw_quotes,
            normalized_quotes=normalized_quotes,
            validation_summary=validation_summary,
            regime=regime,
            router_mode=router_state.mode if router_state is not None else "MIXED",
            qualification_summary=qualification_summary,
            watch_summary=None,
            option_setups=[],
            chain_results={},
            alert_sent=alert_sent,
            report_path=str(HOURLY_REPORT_PATH),
            errors=errors,
            correlation=None,
            trade_decisions=[],
        ),
        generated_at=run_at_utc,
        status=contract_status,
        artifacts={
            "report_path": str(HOURLY_REPORT_PATH),
            "log_path": str(LATEST_HOURLY_RUN_PATH),
            "notification_sent": alert_sent,
        },
        data_quality=data_quality,
    )
    contract["outcome"] = OUTCOME_NO_TRADE
    contract["generation_id"] = generation_id
    return contract


def _build_hourly_run_summary(
    *,
    mode: str,
    run_at_utc: datetime,
    run_date: date,
    notify_mode: str,
    validation_summary: Optional[ValidationSummary],
    regime: Optional[RegimeState],
    router_state: Optional[SectorRouterState],
    qualification_summary: Optional[QualificationSummary],
    candidate_lines: tuple[str, ...],
    alert_title: str,
    alert_body: str,
    alert_sent: bool,
    notification_result: Optional[NotificationResult] = None,
    errors: list[str],
    status: str,
    outcome: str,
    raw_quotes: dict[str, RawQuote],
    normalized_quotes: dict[str, NormalizedQuote],
) -> dict[str, Any]:
    regime_name, posture, confidence, net_score = _summary_regime_fields(regime)
    generation_id = _generation_id("hourly", run_at_utc, None)

    # Derive notification fields: prefer rich result, fall back to alert_sent bool.
    # The fallback handles test scenarios where send_notification is mocked at the
    # runtime level (bypassing module state in output.py).
    if notification_result is not None and not (
        notification_result.notification_status == "NOT_REQUESTED" and alert_sent
    ):
        n_status = notification_result.notification_status
        n_reason = notification_result.notification_reason
        n_attempted = notification_result.notification_attempted
        n_http_status = notification_result.notification_http_status
        n_retry_count = notification_result.notification_retry_count
    elif alert_sent:
        n_status = "SENT"
        n_reason = None
        n_attempted = True
        n_http_status = None
        n_retry_count = 0
    else:
        n_status = notification_result.notification_status if notification_result is not None else "NOT_REQUESTED"
        n_reason = notification_result.notification_reason if notification_result is not None else None
        n_attempted = False
        n_http_status = None
        n_retry_count = 0

    return {
        "run_id": f"hourly-{run_at_utc.strftime('%Y%m%dT%H%M%SZ')}",
        "generation_id": generation_id,
        "timestamp": _iso_z(run_at_utc),
        "run_at_utc": _iso_z(run_at_utc),
        "generated_at": _iso_z(run_at_utc),
        "mode": {
            MODE_LIVE: SUMMARY_MODE_LIVE,
            MODE_FIXTURE: SUMMARY_MODE_FIXTURE,
            MODE_SUNDAY: SUMMARY_MODE_SUNDAY,
        }.get(mode, SUMMARY_MODE_LIVE),
        "session_date": run_date.isoformat(),
        "notify_mode": notify_mode,
        "outcome": outcome,
        "status": status,
        "regime": regime_name,
        "posture": posture,
        "confidence": confidence,
        "net_score": net_score,
        "router_mode": router_state.mode if router_state is not None else "MIXED",
        "energy_score": float(router_state.energy_score) if router_state is not None else 0.0,
        "index_score": float(router_state.index_score) if router_state is not None else 0.0,
        "kill_switch": False,
        "permission": (
            "No trades permitted. System halted."
            if validation_summary is not None and validation_summary.system_halted
            else _PERMISSION_LINES.get(posture, "No new trades permitted.")
        ),
        "data_status": _data_status(mode, raw_quotes, normalized_quotes, fixture_file=None),
        "system_halted": bool(validation_summary.system_halted) if validation_summary is not None else True,
        "halt_reason": getattr(validation_summary, "halt_reason", None) if validation_summary is not None else "; ".join(errors) if errors else None,
        "candidates_qualified": len(qualification_summary.qualified_trades) if qualification_summary is not None else 0,
        "candidates_watchlist": len(qualification_summary.watchlist) if qualification_summary is not None else 0,
        "candidate_lines": list(candidate_lines),
        "alert_title": alert_title,
        "alert_body": alert_body,
        "notification_sent": n_status == "SENT",
        "notification_status": n_status,
        "notification_reason": n_reason,
        "notification_attempted": n_attempted,
        "notification_transport": "telegram",
        "notification_http_status": n_http_status,
        "notification_retry_count": n_retry_count,
        "warnings": [],
        "errors": errors,
        "artifacts": {
            "contract_path": str(LATEST_HOURLY_CONTRACT_PATH),
            "payload_path": str(LATEST_HOURLY_PAYLOAD_PATH),
            "report_path": str(HOURLY_REPORT_PATH),
        },
    }


def _write_hourly_artifacts(summary: dict[str, Any], contract: dict[str, Any]) -> None:
    import os
    _fixture_mode = os.environ.get("FIXTURE_MODE", "0") == "1"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    safe_write_latest(LATEST_HOURLY_RUN_PATH, summary, "run_at_utc")
    safe_write_latest(LATEST_HOURLY_CONTRACT_PATH, contract, "generated_at")
    try:
        from cuttingboard.delivery.payload import build_report_payload, assert_valid_payload
        from cuttingboard.delivery.transport import deliver_html, deliver_json

        payload = build_report_payload(contract, fixture_mode=_fixture_mode)
        _attach_generation_id_to_payload(payload, contract)
        assert_valid_payload(payload)
        deliver_json(payload, output_path=str(LATEST_HOURLY_PAYLOAD_PATH))
        deliver_html(payload, output_path=str(HOURLY_REPORT_PATH))
    except Exception:
        logger.exception("Hourly payload artifact generation failed — summary/contract preserved")


def _load_previous_market_map() -> dict[str, Any] | None:
    if not MARKET_MAP_PATH.exists():
        return None
    text = MARKET_MAP_PATH.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Previous market_map.json is malformed: {MARKET_MAP_PATH}") from exc


def _write_market_map_file(market_map: dict[str, Any]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    MARKET_MAP_PATH.write_text(json.dumps(market_map, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _tradable_symbols() -> list[str]:
    return [s for s in config.ALL_SYMBOLS if s not in config.NON_TRADABLE_SYMBOLS]


def _write_trend_structure_snapshot(
    normalized_quotes: dict[str, NormalizedQuote],
    history_by_symbol: dict[str, pd.DataFrame],
    generated_at: datetime,
) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        snapshot = build_trend_structure_snapshot(
            normalized_quotes=normalized_quotes,
            history_by_symbol=history_by_symbol,
            symbols=list(config.TREND_STRUCTURE_SYMBOLS),
            generated_at=generated_at,
        )
        tmp = TREND_STRUCTURE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(TREND_STRUCTURE_PATH)
    except Exception:
        logger.exception("Failed to write trend_structure_snapshot")


def _write_watchlist_snapshot(
    normalized_quotes: dict[str, NormalizedQuote],
    generated_at: datetime,
) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        snapshot = build_watchlist_snapshot(
            normalized_quotes=normalized_quotes,
            generated_at=generated_at,
        )
        tmp = WATCHLIST_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(WATCHLIST_PATH)
    except Exception:
        logger.exception("Failed to write watchlist_snapshot")


def _write_macro_snapshot(contract: dict[str, Any]) -> None:
    macro_drivers = contract.get("macro_drivers")
    if not macro_drivers:
        return
    path = LOGS_DIR / "macro_drivers_snapshot.json"
    tmp = path.with_suffix(".tmp")
    try:
        import json as _json
        tmp.write_text(
            _json.dumps({
                "macro_drivers": macro_drivers,
                "generated_at": contract.get("generated_at", ""),
            }),
            encoding="utf-8",
        )
        tmp.replace(path)
    except Exception:
        logger.exception("Failed to write macro_drivers snapshot")


def _write_payload_artifacts(contract: dict[str, Any]) -> None:
    import os
    _fixture_mode = os.environ.get("FIXTURE_MODE", "0") == "1"
    try:
        from cuttingboard.delivery.payload import build_report_payload, assert_valid_payload
        from cuttingboard.delivery.transport import deliver_json, deliver_html

        payload = build_report_payload(contract, fixture_mode=_fixture_mode)
        _attach_generation_id_to_payload(payload, contract)
        assert_valid_payload(payload)
        deliver_json(payload)
        deliver_html(payload)
    except Exception:
        logger.exception("Payload artifact generation failed — contract artifacts unaffected")


def _data_status(
    mode: str,
    raw_quotes: dict[str, RawQuote],
    normalized_quotes: dict[str, NormalizedQuote],
    fixture_file: Optional[Path],
) -> str:
    if _is_fixture_backed(mode, fixture_file):
        return "ok"
    if mode == MODE_SUNDAY:
        return "stale"
    if mode == MODE_LIVE and not normalized_quotes:
        return "stale"
    if any(_quote_age_seconds(quote) > config.FRESHNESS_SECONDS for quote in normalized_quotes.values()):
        return "stale"
    if mode != MODE_FIXTURE and any(raw.source == "polygon" for raw in raw_quotes.values()):
        return "fallback"
    return "ok"


def _kill_switch(regime: Optional[RegimeState], normalized_quotes: dict[str, NormalizedQuote]) -> bool:
    spy = normalized_quotes.get("SPY")
    spy_pct_change = spy.pct_change_decimal if spy is not None else 0.0
    vix_level = regime.vix_level if regime is not None and regime.vix_level is not None else 0.0
    vix_pct_change = regime.vix_pct_change if regime is not None and regime.vix_pct_change is not None else 0.0
    return (
        vix_level > 35
        or vix_pct_change > 0.15
        or abs(spy_pct_change) > 0.03
    )


def _min_rr_for_regime(regime: Optional[RegimeState]) -> float:
    if regime is None:
        return config.NEUTRAL_RR_RATIO
    if regime.regime == NEUTRAL:
        return config.NEUTRAL_RR_RATIO
    if regime.regime == EXPANSION:
        return config.EXPANSION_RR_RATIO
    return config.MIN_RR_RATIO


def _summary_regime_fields(regime: Optional[RegimeState]) -> tuple[str, str, float, int]:
    if regime is None:
        return NEUTRAL, "STAY_FLAT", 0.0, 0
    return regime.regime, regime.posture, float(regime.confidence), int(regime.net_score)


def _chain_warning_lines(chain_results: dict[str, ChainValidationResult]) -> list[str]:
    warnings: list[str] = []
    invalid_count = 0
    for symbol, result in sorted(chain_results.items()):
        if result.classification == "DISQUALIFIED_OPTIONS_INVALID":
            warnings.append(f"{symbol}: options invalid")
            invalid_count += 1
        elif result.classification == MANUAL_CHECK:
            warnings.append(f"{symbol}: needs manual chain check")
    if chain_results and invalid_count == len(chain_results):
        warnings.append("all candidates invalid at chain validation")
    return warnings


def _validated_chain_result(symbol: str) -> ChainValidationResult:
    return ChainValidationResult(
        symbol=symbol,
        classification=VALIDATED,
        reason=None,
        spread_pct=None,
        open_interest=None,
        volume=None,
        expiry_used=None,
        data_source=None,
    )


def _resolve_run_date(date_arg: Optional[str]) -> date:
    return date.fromisoformat(date_arg) if date_arg else datetime.now(timezone.utc).date()


def _resolve_effective_mode(requested_mode: str, run_date: date, now_et: Optional[datetime] = None) -> str:
    if requested_mode == MODE_LIVE and run_date.weekday() == 6:
        if now_et is None or now_et.hour * 60 + now_et.minute >= 15 * 60 + 30:
            return MODE_SUNDAY
    return requested_mode


def _resolve_cli_fixture_path(
    effective_mode: str,
    fixture_file: Optional[str],
    requested_run_date: date,
) -> Optional[Path]:
    if effective_mode == MODE_FIXTURE:
        return _resolve_fixture_path(fixture_file, requested_run_date)
    if effective_mode == MODE_SUNDAY and fixture_file:
        return Path(fixture_file)
    return None


def _resolve_fixture_path(fixture_file: Optional[str], run_date: date) -> Path:
    if fixture_file:
        return Path(fixture_file)
    return DEFAULT_FIXTURE_DIR / f"{run_date.isoformat()}.json"


def _effective_run_date(
    mode: str,
    requested_run_date: date,
    fixture_file: Optional[Path],
    explicit_date: bool,
) -> date:
    if mode not in {MODE_FIXTURE, MODE_SUNDAY} or explicit_date or fixture_file is None:
        return requested_run_date

    try:
        return date.fromisoformat(fixture_file.stem)
    except ValueError:
        return requested_run_date


def _deterministic_run_at(mode: str, fixture_file: Optional[Path]) -> datetime:
    if not _is_fixture_backed(mode, fixture_file):
        return datetime.now(timezone.utc)
    quotes = _load_fixture_quotes(fixture_file)
    if not quotes:
        return datetime.now(timezone.utc)
    return max(quote.fetched_at_utc for quote in quotes.values())


def _quote_age_seconds(quote: NormalizedQuote) -> float:
    return (datetime.now(timezone.utc) - quote.fetched_at_utc).total_seconds()


def _run_id(mode: str, run_at_utc: datetime, fixture_file: Optional[Path]) -> str:
    if _is_fixture_backed(mode, fixture_file):
        return f"{mode}-fixture-{fixture_file.stem}"
    return f"{mode}-{run_at_utc.strftime('%Y%m%dT%H%M%SZ')}"


def _generation_id(mode: str, run_at_utc: datetime, fixture_file: Optional[Path]) -> str:
    return _run_id(mode, run_at_utc, fixture_file)


def _attach_generation_id_to_payload(payload: dict[str, Any], contract: dict[str, Any]) -> None:
    generation_id = contract.get("generation_id")
    if generation_id is None:
        return
    meta = payload.setdefault("meta", {})
    if isinstance(meta, dict):
        meta["generation_id"] = generation_id


def _is_fixture_backed(mode: str, fixture_file: Optional[Path]) -> bool:
    return fixture_file is not None and mode in {MODE_FIXTURE, MODE_SUNDAY}


def _sector_router_state_path(mode: str) -> Optional[str]:
    if mode == MODE_FIXTURE:
        return None
    return str(LOGS_DIR / "sector_router_state.json")


def _failure_summary(
    mode: str,
    run_date: date,
    errors: list[str],
    report_path: Optional[Path],
    generated_at: datetime | None = None,
    generation_id: str | None = None,
) -> dict[str, Any]:
    now_utc = generated_at or datetime.now(timezone.utc)
    resolved_generation_id = generation_id or _generation_id(mode, now_utc, None)
    summary_mode = {
        MODE_LIVE: SUMMARY_MODE_LIVE,
        MODE_FIXTURE: SUMMARY_MODE_FIXTURE,
        MODE_SUNDAY: SUMMARY_MODE_SUNDAY,
    }.get(mode, SUMMARY_MODE_LIVE)
    return {
        "run_id": f"failed-{summary_mode.lower()}-{run_date.isoformat()}",
        "generation_id": resolved_generation_id,
        "timestamp": _iso_z(now_utc),
        "run_at_utc": _iso_z(now_utc),
        "mode": summary_mode,
        "outcome": OUTCOME_HALT,
        "status": SUMMARY_STATUS_FAIL,
        "regime": NEUTRAL,
        "posture": "STAY_FLAT",
        "confidence": 0.0,
        "net_score": 0,
        "router_mode": "MIXED",
        "energy_score": 0.0,
        "index_score": 0.0,
        "permission": "No trades permitted. Run failed.",
        "kill_switch": False,
        "min_rr_applied": config.NEUTRAL_RR_RATIO,
        "data_status": "stale",
        "fallback_used": False,
        "system_halted": True,
        "halt_reason": "; ".join(errors) if errors else "run failed",
        "candidates_generated": 0,
        "candidates_qualified": 0,
        "candidates_watchlist": 0,
        "chain_validation": {},
        "warnings": [],
        "errors": errors,
    }


_ROOT = Path(__file__).resolve().parent.parent
_DOCTOR_PATH = _ROOT / "tools" / "engine_doctor.py"
_BASELINE_PATH = _ROOT / "tools" / "baseline.json"


def _run_engine_health_gate() -> None:
    """Abort execution if engine_doctor reports a failure (runtime_gate_enabled=true).

    No-op when runtime_gate_enabled is false (default). Runs without --tests for speed.
    Exit code from engine_doctor is propagated on failure.
    """
    if not config.get_engine_doctor_runtime_gate():
        return

    result = subprocess.run(
        [sys.executable, str(_DOCTOR_PATH), "--json", "--baseline", str(_BASELINE_PATH)],
        capture_output=True,
        text=True,
        cwd=str(_ROOT),
    )

    if result.returncode == 0:
        return

    try:
        report = json.loads(result.stdout)
        status = report.get("status", "FAIL")
    except (json.JSONDecodeError, ValueError):
        status = "FAIL"

    logger.error(
        "ENGINE HEALTH GATE FAILED — status=%s exit_code=%d",
        status,
        result.returncode,
    )
    if result.stderr:
        logger.error("engine_doctor stderr: %s", result.stderr[:500])

    raise SystemExit(result.returncode)


def _failure_report(run_date: date, errors: list[str]) -> str:
    lines = [
        "======================================================",
        f"  CUTTINGBOARD  -  {run_date.isoformat()}",
        "  RUN FAILED",
        "======================================================",
        "",
    ]
    for line in errors or ["Unknown failure"]:
        lines.append(f"  {line}")
    return "\n".join(lines)


def _iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _log_time_diagnostics(run_at_utc: datetime, now_et: datetime) -> None:
    market_open = time_utils.is_market_open(now_et)
    after_cutoff = time_utils.is_after_entry_cutoff(now_et, config.ENTRY_CUTOFF_ET)
    logger.info(
        "[TIME] now_utc=%s now_et=%s market_open=%s entry_cutoff_et=%s is_after_cutoff=%s",
        run_at_utc.replace(microsecond=0).isoformat(),
        now_et.replace(microsecond=0).isoformat(),
        market_open,
        config.ENTRY_CUTOFF_ET.strftime("%H:%M:%S"),
        after_cutoff,
    )
    if after_cutoff:
        logger.info(
            "[TIME_GATE] blocked=True reason=AFTER_CUTOFF now_et=%s cutoff_et=%s",
            now_et.replace(microsecond=0).isoformat(),
            config.ENTRY_CUTOFF_ET.strftime("%H:%M:%S"),
        )
    else:
        logger.info("[TIME_GATE] blocked=False")
