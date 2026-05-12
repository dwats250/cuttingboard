"""PRD-012A acceptance tests: hourly alert filtering, R:R format, and alert contract."""

import inspect
import json
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from cuttingboard.notifications import NOTIFY_HOURLY, format_hourly_notification
from cuttingboard.notifications.formatter import (
    ALERT_CONTEXT_NOTIFY,
    AlertEvent,
    OUTCOME_TRADE,
    format_ntfy_alert,
)
from cuttingboard.qualification import QualificationResult, QualificationSummary, TradeCandidate
from cuttingboard.regime import RegimeState
from cuttingboard.runtime import (
    MODE_LIVE,
    SUMMARY_STATUS_FAIL,
    SUMMARY_STATUS_SUCCESS,
    _build_hourly_candidate_lines,
    _execute_notify_run,
    _hourly_rr,
)
from cuttingboard.sector_router import SectorRouterState
from cuttingboard.validation import ValidationSummary


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _regime(**kwargs) -> RegimeState:
    defaults = dict(
        regime="RISK_OFF",
        posture="DEFENSIVE_SHORT",
        confidence=0.62,
        net_score=-5,
        risk_on_votes=0,
        risk_off_votes=5,
        neutral_votes=3,
        total_votes=8,
        vote_breakdown={},
        vix_level=22.0,
        vix_pct_change=0.02,
        computed_at_utc=datetime(2026, 4, 23, 14, 30, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return RegimeState(**defaults)


def _validation(*, halted: bool = False) -> ValidationSummary:
    vs = MagicMock(spec=ValidationSummary)
    vs.system_halted = halted
    vs.halt_reason = "test halt" if halted else None
    vs.valid_quotes = {}
    vs.symbols_validated = 0
    vs.symbols_attempted = 0
    return vs


def _qual(symbols: list[str], direction: str = "SHORT") -> QualificationSummary:
    trades = [
        QualificationResult(
            symbol=s,
            qualified=True,
            watchlist=False,
            direction=direction,
            gates_passed=[],
            gates_failed=[],
            hard_failure=None,
            watchlist_reason=None,
            max_contracts=2,
            dollar_risk=150.0,
        )
        for s in symbols
    ]
    return QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=trades,
        watchlist=[],
        excluded={},
        symbols_evaluated=len(symbols),
        symbols_qualified=len(symbols),
        symbols_watchlist=0,
        symbols_excluded=0,
    )


def _candidate(symbol: str, entry: float = 100.0, stop: float = 97.0, target: float = 106.0) -> TradeCandidate:
    return TradeCandidate(
        symbol=symbol,
        direction="SHORT",
        entry_price=entry,
        stop_price=stop,
        target_price=target,
        spread_width=1.0,
    )


def _structure(structure: str = "PULLBACK") -> MagicMock:
    sr = MagicMock()
    sr.structure = structure
    return sr


def _router_state() -> SectorRouterState:
    return SectorRouterState(
        mode="MIXED",
        energy_score=0.0,
        index_score=0.0,
        computed_at_utc=datetime(2026, 4, 23, 14, 30, tzinfo=timezone.utc),
        session_date="2026-04-23",
    )


def _hourly_event(regime=None, qual=None, candidate_lines=(), halted=False) -> AlertEvent:
    val = _validation(halted=halted)
    return AlertEvent(
        alert_context=ALERT_CONTEXT_NOTIFY,
        notify_mode=NOTIFY_HOURLY,
        outcome="NO_TRADE",
        asof_utc=datetime(2026, 4, 23, 14, 30, tzinfo=timezone.utc),
        regime=regime or _regime(),
        validation_summary=val,
        qualification_summary=qual,
        candidate_lines=candidate_lines,
    )


# ---------------------------------------------------------------------------
# R:R computation
# ---------------------------------------------------------------------------

def test_hourly_rr_basic():
    c = _candidate("NVDA", entry=100.0, stop=97.0, target=106.0)
    assert abs(_hourly_rr(c) - 2.0) < 0.01


def test_hourly_rr_zero_risk_returns_zero():
    c = _candidate("NVDA", entry=100.0, stop=100.0, target=106.0)
    assert _hourly_rr(c) == 0.0


def test_hourly_rr_three_to_one():
    # risk=4, reward=12 => 3.0
    c = _candidate("META", entry=200.0, stop=196.0, target=212.0)
    assert abs(_hourly_rr(c) - 3.0) < 0.01


# ---------------------------------------------------------------------------
# Tradable symbol filtering
# ---------------------------------------------------------------------------

def test_candidate_lines_excludes_vix():
    qual = _qual(["^VIX", "NVDA", "META"])
    structure = {s: _structure() for s in ["^VIX", "NVDA", "META"]}
    candidates = {s: _candidate(s) for s in ["^VIX", "NVDA", "META"]}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates)
    symbols = [line.split(" | ")[0] for line in lines]

    assert "^VIX" not in symbols
    assert "NVDA" in symbols
    assert "META" in symbols


def test_candidate_lines_excludes_all_macro_drivers():
    macro = ["^VIX", "^TNX", "DX-Y.NYB", "BTC-USD"]
    tradable = ["NVDA", "META"]
    all_symbols = macro + tradable
    qual = _qual(all_symbols)
    structure = {s: _structure() for s in all_symbols}
    candidates = {s: _candidate(s) for s in all_symbols}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates, limit=len(all_symbols))
    symbols = [line.split(" | ")[0] for line in lines]

    for m in macro:
        assert m not in symbols, f"{m} must be excluded"
    for t in tradable:
        assert t in symbols, f"{t} must be included"


def test_candidate_lines_excludes_caret_symbols():
    qual = _qual(["^TNX", "SPY"])
    structure = {s: _structure() for s in ["^TNX", "SPY"]}
    candidates = {s: _candidate(s) for s in ["^TNX", "SPY"]}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates)
    symbols = [line.split(" | ")[0] for line in lines]

    assert "^TNX" not in symbols
    assert "SPY" in symbols


# ---------------------------------------------------------------------------
# R:R in candidate line format
# ---------------------------------------------------------------------------

def test_candidate_lines_format_has_four_parts():
    qual = _qual(["NVDA"])
    structure = {"NVDA": _structure("TREND")}
    candidates = {"NVDA": _candidate("NVDA")}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates)
    assert len(lines) == 1
    parts = lines[0].split(" | ")
    assert len(parts) == 4, f"Expected SYMBOL | direction | structure | R:R, got: {lines[0]!r}"


def test_candidate_lines_rr_format():
    qual = _qual(["NVDA"])
    structure = {"NVDA": _structure("TREND")}
    # entry=200, stop=196 (risk=4), target=208 (reward=8) => 2.0:1
    candidates = {"NVDA": _candidate("NVDA", entry=200.0, stop=196.0, target=208.0)}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates)
    assert "2.0:1" in lines[0]


def test_candidate_lines_includes_structure():
    qual = _qual(["META"])
    structure = {"META": _structure("BREAKOUT")}
    candidates = {"META": _candidate("META")}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates)
    assert "BREAKOUT" in lines[0]


def test_candidate_lines_respects_limit():
    symbols = ["NVDA", "META", "AAPL", "AMZN", "SPY", "TSLA"]
    qual = _qual(symbols)
    structure = {s: _structure() for s in symbols}
    candidates = {s: _candidate(s) for s in symbols}

    lines = _build_hourly_candidate_lines(qual.qualified_trades, structure, candidates, limit=3)
    assert len(lines) == 3


# ---------------------------------------------------------------------------
# Formatter output
# ---------------------------------------------------------------------------

def test_format_hourly_stay_flat_title_and_body():
    event = _hourly_event(regime=_regime(posture="STAY_FLAT", regime="NEUTRAL"))
    title, body = format_ntfy_alert(event)
    assert title == "STAY FLAT"
    assert "STAY_FLAT — no entries" in body


def test_format_hourly_no_setup_title_and_body():
    event = _hourly_event(qual=_qual([]))
    title, body = format_ntfy_alert(event)
    assert title == "NO SETUP"
    assert "No A+ setups" in body


def test_format_hourly_setup_ready_title():
    event = _hourly_event(
        qual=_qual(["META"]),
        candidate_lines=("META | SHORT | PULLBACK | 2.5:1",),
    )
    title, body = format_ntfy_alert(event)
    assert title == "META SHORT READY"
    assert "META | SHORT | PULLBACK | 2.5:1" in body


def test_format_hourly_required_fields_present():
    event = _hourly_event()
    _, body = format_ntfy_alert(event)
    assert "ET" in body
    assert "Regime:" in body
    assert "Posture:" in body
    assert "Confidence:" in body
    assert "Tradable:" in body
    assert "Setups:" in body


def test_format_hourly_system_halt_routes_to_halt_format():
    event = AlertEvent(
        alert_context=ALERT_CONTEXT_NOTIFY,
        notify_mode=NOTIFY_HOURLY,
        outcome="NO_TRADE",
        asof_utc=datetime(2026, 4, 23, 14, 30, tzinfo=timezone.utc),
        regime=None,
        validation_summary=_validation(halted=True),
        halt_reason="^VIX fetch failed",
    )
    title, body = format_ntfy_alert(event)
    assert title == "SYSTEM HALT"


def test_format_hourly_notification_wrapper_uses_new_section_shape():
    """PRD-133: hourly body renders Regime/Confidence/Reason then Macro Tape, no Action/Blockers/Generated."""
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 4, 23, 14, 0, tzinfo=timezone.utc),
        regime=_regime(regime="EXPANSION", posture="RISK_ON", confidence=0.72),
        validation_summary=_validation(),
        qualification_summary=_qual([]),
    )

    # 14:00 UTC = 07:00 PT (DST), 10:00 ET
    assert title == "MONITOR 7:00 AM"
    lines = body.split("\n")
    assert lines[0] == "Regime: EXPANSION"
    assert lines[1] == "Confidence: 0.72"
    assert lines[2] == "Reason: no setups"
    assert "" in lines
    assert not any(line.startswith("Action:") for line in lines)
    assert not any(line.startswith("State:") for line in lines)
    assert not any(line.startswith("Blockers:") for line in lines)
    assert not any(line.startswith("Generated:") for line in lines)
    assert not any(line.startswith("Macro:") for line in lines)
    assert "Focus: no active setup" in lines
    assert "TRIGGERS:" not in body


def test_format_hourly_notification_wrapper_filters_macro_candidates():
    # PRD-127: under default canonical_outcome=None the body renders
    # MONITOR SETUP rather than TRADE even when qualified symbols exist.
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 4, 23, 14, 0, tzinfo=timezone.utc),
        regime=_regime(regime="EXPANSION", posture="RISK_ON", confidence=0.81),
        validation_summary=_validation(),
        qualification_summary=_qual(["^VIX", "NVDA"], direction="LONG"),
        candidate_lines=("^VIX | LONG | TREND | 9.0:1", "NVDA | LONG | TREND | 2.4:1"),
    )

    assert title == "MONITOR SETUP 7:00 AM"
    assert "^VIX" not in body
    assert "Focus: NVDA LONG" in body
    assert not any(line.startswith("Action:") for line in body.split("\n"))
    assert not title.startswith("LONG ")


def test_format_hourly_notification_wrapper_watchlist_focus_section():
    qual = QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[],
        watchlist=[
            QualificationResult(
                symbol="AAPL",
                qualified=False,
                watchlist=True,
                direction="LONG",
                gates_passed=[],
                gates_failed=["STOP_DISTANCE", "RR_RATIO"],
                hard_failure=None,
                watchlist_reason="developing above trigger",
                max_contracts=None,
                dollar_risk=None,
            )
        ],
        excluded={},
        symbols_evaluated=1,
        symbols_qualified=0,
        symbols_watchlist=1,
        symbols_excluded=0,
    )
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 4, 23, 14, 0, tzinfo=timezone.utc),
        regime=_regime(regime="EXPANSION", posture="RISK_ON", confidence=0.81),
        validation_summary=_validation(),
        qualification_summary=qual,
    )

    assert title == "MONITOR 7:00 AM"
    assert not any(line.startswith("Action:") for line in body.split("\n"))
    assert "Focus: AAPL LONG" in body
    assert "Blockers: STOP_DISTANCE, RR_RATIO" in body


# ---------------------------------------------------------------------------
# PRD-124: header, body sections, action enum, banned-phrase audit
# ---------------------------------------------------------------------------

_PRD124_BANNED_PHRASES = (
    "TRIGGERS:",
    "breakdown below support",
    "failed reclaim at breakdown level",
    "breakout above resistance",
    "continuation hold above trigger",
    "range break",
    "expansion confirmation",
    "confirmed direction",
)


def _prd124_event_args(**overrides):
    base = dict(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(regime="RISK_OFF", posture="DEFENSIVE_SHORT", confidence=0.62),
        validation_summary=_validation(),
        qualification_summary=_qual([]),
    )
    base.update(overrides)
    return base


def test_prd124_r1_title_uses_pt_clock_not_et():
    """R1: 16:20Z → 9:20 AM PT in the title; no ET in the title."""
    title, _ = format_hourly_notification(**_prd124_event_args())
    assert "9:20 AM" in title
    assert " ET" not in title
    assert "12:20" not in title
    assert "16:20" not in title


class _Q:
    def __init__(self, price, pct):
        self.price = price
        self.pct_change_decimal = pct


def _full_quotes():
    return {
        "^VIX": _Q(18.1, -0.015),
        "DX-Y.NYB": _Q(98.5, -0.002),
        "^TNX": _Q(4.42, -0.007),
        "BTC-USD": _Q(81300.0, 0.011),
        "SPY": _Q(724.59, 0.0),
        "QQQ": _Q(682.62, 0.0),
        "GLD": _Q(418.94, 0.0),
        "SLV": _Q(66.28, 0.0),
        "XLE": _Q(59.71, 0.0),
        "GDX": _Q(86.22, 0.0),
    }


def test_prd133_macro_tape_block_renders_when_quotes_available():
    _, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 12, 19, 4, tzinfo=timezone.utc),
        regime=_regime(posture="STAY_FLAT", regime="RISK_OFF", confidence=0.50,
                       vix_level=18.1, vix_pct_change=-0.015),
        validation_summary=_validation(),
        qualification_summary=None,
        normalized_quotes=_full_quotes(),
    )
    assert "Macro Tape:" in body
    # ASCII-only, one ticker per line, signed pct (PRD-133-PATCH)
    assert "VIX  18.1   -1.5%" in body
    assert "DXY  98.5   -0.2%" in body
    assert "10Y  4.42   -0.7%" in body
    assert "BTC  81.3K  +1.1%" in body
    assert body.isascii() or "—" in body  # only non-ASCII allowed is the title em-dash


def test_prd133_tradables_block_full_universe():
    _, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 12, 19, 4, tzinfo=timezone.utc),
        regime=_regime(posture="STAY_FLAT", regime="RISK_OFF"),
        validation_summary=_validation(),
        qualification_summary=None,
        normalized_quotes=_full_quotes(),
    )
    assert "Tradables:" in body
    # One ticker per line, fixed order (PRD-133-PATCH)
    lines = body.split("\n")
    tradables_idx = lines.index("Tradables:")
    assert lines[tradables_idx + 1] == "SPY  724.59"
    assert lines[tradables_idx + 2] == "QQQ  682.62"
    assert lines[tradables_idx + 3] == "GLD  418.94"
    assert lines[tradables_idx + 4] == "SLV  66.28"
    assert lines[tradables_idx + 5] == "XLE  59.71"
    assert lines[tradables_idx + 6] == "GDX  86.22"


def test_prd133_tradables_block_skips_missing_symbols_preserves_order():
    quotes = {
        "SPY": _Q(700.00, 0.0),
        # QQQ missing
        "GLD": _Q(400.00, 0.0),
        # SLV missing
        "XLE": _Q(60.00, 0.0),
        "GDX": _Q(85.00, 0.0),
    }
    _, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 12, 19, 4, tzinfo=timezone.utc),
        regime=_regime(posture="STAY_FLAT", regime="RISK_OFF"),
        validation_summary=_validation(),
        qualification_summary=None,
        normalized_quotes=quotes,
    )
    assert "Tradables:" in body
    # Available symbols rendered one per line in fixed order (PRD-133-PATCH):
    # SPY, GLD, XLE, GDX (QQQ and SLV skipped)
    lines = body.split("\n")
    tradables_idx = lines.index("Tradables:")
    assert lines[tradables_idx + 1] == "SPY  700.00"
    assert lines[tradables_idx + 2] == "GLD  400.00"
    assert lines[tradables_idx + 3] == "XLE  60.00"
    assert lines[tradables_idx + 4] == "GDX  85.00"
    # Next non-tradable line is the focus block
    assert lines[tradables_idx + 5] == ""
    assert "QQQ" not in body
    assert "SLV" not in body


def test_prd133_tradables_block_omitted_when_zero_symbols():
    quotes = {
        "^VIX": _Q(18.1, -0.015),  # macro only
    }
    _, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 12, 19, 4, tzinfo=timezone.utc),
        regime=_regime(posture="STAY_FLAT", regime="RISK_OFF"),
        validation_summary=_validation(),
        qualification_summary=None,
        normalized_quotes=quotes,
    )
    assert "Tradables:" not in body


def test_prd133_macro_tape_partial_skips_missing_symbols():
    """PRD-133-PATCH: missing macro symbols are skipped, not rendered as n/a rows."""
    quotes = {
        "^VIX": _Q(20.0, 0.005),
        # DXY, 10Y, BTC missing
    }
    _, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 12, 19, 4, tzinfo=timezone.utc),
        regime=_regime(posture="STAY_FLAT", regime="RISK_OFF"),
        validation_summary=_validation(),
        qualification_summary=None,
        normalized_quotes=quotes,
    )
    assert "Macro Tape:" in body
    assert "VIX  20.0   +0.5%" in body
    assert "DXY" not in body
    assert "10Y" not in body
    assert "BTC" not in body
    assert "n/a" not in body


def test_prd133_no_generated_trailer_in_body():
    """PRD-133: hourly body has no Generated: line; STAY-FLAT title has ` — ` and ` PT`."""
    title, body = format_hourly_notification(**_prd124_event_args())
    assert not any(line.startswith("Generated:") for line in body.split("\n"))
    assert " ET" not in title

    # STAY-FLAT title format check (separate input)
    sf_title, _ = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(posture="STAY_FLAT", regime="NEUTRAL", confidence=0.4),
        validation_summary=_validation(),
        qualification_summary=None,
    )
    assert sf_title.startswith("STAY FLAT — ")
    assert sf_title.endswith(" PT")


def test_prd133_body_required_section_labels_in_order():
    """PRD-133: Regime / Confidence / Reason / (Macro Tape) / Focus, in that order."""
    _, body = format_hourly_notification(**_prd124_event_args())
    required = ["Regime:", "Confidence:", "Reason:", "Focus:"]
    positions = []
    body_lines = body.split("\n")
    for label in required:
        match_idx = next(
            (i for i, line in enumerate(body_lines) if line.startswith(label)),
            -1,
        )
        assert match_idx >= 0, f"missing required section: {label}"
        positions.append(match_idx)
    assert positions == sorted(positions), f"sections out of order: {positions}"


def test_prd133_action_label_branches_via_title():
    """PRD-133: action label drives the title; body no longer carries Action: line."""
    # STAY FLAT — regime posture is STAY_FLAT → title gets ` — ` and ` PT`
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(posture="STAY_FLAT", regime="NEUTRAL", confidence=0.4),
        validation_summary=_validation(),
        qualification_summary=None,
    )
    assert title.startswith("STAY FLAT — ")
    assert title.endswith(" PT")
    assert not any(line.startswith("Action:") for line in body.split("\n"))

    # HALT — system halted overrides everything
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(),
        validation_summary=_validation(halted=True),
        qualification_summary=_qual(["NVDA"]),
    )
    assert title.startswith("HALT ")
    assert not any(line.startswith("Action:") for line in body.split("\n"))

    # MONITOR SETUP — qualified candidates + tradable posture
    title, _ = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.7),
        validation_summary=_validation(),
        qualification_summary=_qual(["NVDA"], direction="LONG"),
    )
    assert title.startswith("MONITOR SETUP ")

    # MONITOR — tradable posture, no qualified
    title, _ = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.7),
        validation_summary=_validation(),
        qualification_summary=_qual([]),
    )
    assert title.startswith("MONITOR ")
    assert not title.startswith("MONITOR SETUP ")


def test_prd124_r5_no_generic_trigger_phrases_without_attached_symbol():
    """R5: no banned trigger phrase appears on any line without a focus ticker."""
    _, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(posture="STAY_FLAT", regime="NEUTRAL", confidence=0.4),
        validation_summary=_validation(),
        qualification_summary=None,
    )
    assert "TRIGGERS:" not in body
    for phrase in _PRD124_BANNED_PHRASES:
        assert phrase not in body, f"banned phrase {phrase!r} leaked into STAY FLAT body"


def test_prd133_missing_data_renders_explicit_fallback_tokens():
    """PRD-133: regime=None and no quotes produces explicit Regime/Confidence/Focus fallbacks."""
    _, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=None,
        validation_summary=_validation(),
        qualification_summary=None,
    )
    assert "Regime: unknown" in body
    assert "Confidence: unknown" in body
    assert "Focus: no active setup" in body
    # No banned legacy labels
    assert "State:" not in body
    assert "Action:" not in body
    assert "Blockers:" not in body
    assert "Generated:" not in body
    # Empty normalized_quotes → no Macro Tape and no Tradables block
    assert "Macro Tape:" not in body
    assert "Tradables:" not in body
    assert "UNKNOWN | UNKNOWN | 0.00" not in body


def test_prd124_r7_notifier_formatter_module_unchanged_by_format_call():
    """R7 surrogate: formatter.py source bytes are stable across a hourly format call."""
    import hashlib
    from cuttingboard.notifications import formatter as fmt_mod
    src_before = hashlib.sha256(open(fmt_mod.__file__, "rb").read()).hexdigest()
    format_hourly_notification(**_prd124_event_args())
    src_after = hashlib.sha256(open(fmt_mod.__file__, "rb").read()).hexdigest()
    assert src_before == src_after


def test_prd124_r9_no_new_ranking_or_scoring_constructs_in_notifier():
    """R9: static-grep prohibition on new sort/key/max/min in __init__.py."""
    import cuttingboard.notifications as notif_pkg
    src = open(notif_pkg.__file__, "r", encoding="utf-8").read()
    # Pre-existing sorted(...) in _watch_lines_from_qualification was deleted
    # with the function. Post-PRD the file must have zero sort/key/max/min
    # constructs operating on artifact collections.
    forbidden_tokens = ("sorted(", ".sort(", "key=", "max(", "min(")
    for token in forbidden_tokens:
        assert token not in src, (
            f"forbidden token {token!r} found in notifications/__init__.py "
            f"— R9 prohibits new ranking/scoring constructs in the notifier."
        )


def test_prd124_r5_banned_phrases_absent_from_module_source():
    """R5 source-level: banned trigger boilerplate must not appear in the file."""
    import cuttingboard.notifications as notif_pkg
    src = open(notif_pkg.__file__, "r", encoding="utf-8").read()
    for phrase in _PRD124_BANNED_PHRASES:
        assert phrase not in src, (
            f"banned phrase {phrase!r} still present in notifications/__init__.py"
        )


# ---------------------------------------------------------------------------
# PRD-127: hourly action language alignment with canonical outcome
# Direct inspection of _execute_notify_run shows hourly runtime hardcodes
# OUTCOME_NO_TRADE at cuttingboard/runtime.py:560 and :600, and
# _build_hourly_contract sets contract["outcome"] = OUTCOME_NO_TRADE at
# :1752 — there is no hourly TRADES path today. The reachability test
# exercises the formatter directly with the new canonical_outcome kwarg.
# ---------------------------------------------------------------------------


def test_prd127_qualified_default_outcome_renders_monitor_setup_not_trade():
    """R1+R2: qualified symbols + tradable regime + default canonical_outcome
    must NOT emit Action: TRADE; must emit Action: MONITOR SETUP."""
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.7),
        validation_summary=_validation(),
        qualification_summary=_qual(["NVDA"], direction="LONG"),
        candidate_lines=("NVDA | LONG | TREND | 2.4:1",),
    )
    assert title.startswith("MONITOR SETUP ")
    assert not any(line.startswith("Action:") for line in body.split("\n"))
    assert not title.startswith("TRADE ")
    assert not title.startswith("LONG ")
    assert not title.startswith("SHORT ")


def test_prd127_canonical_trade_outcome_reaches_trade_label():
    """R3 reachability: passing canonical_outcome=OUTCOME_TRADE with the
    same qualified inputs MUST render Action: TRADE, proving the future
    canonical-TRADES path is reachable through the new kwarg."""
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.7),
        validation_summary=_validation(),
        qualification_summary=_qual(["NVDA"], direction="LONG"),
        candidate_lines=("NVDA | LONG | TREND | 2.4:1",),
        canonical_outcome=OUTCOME_TRADE,
    )
    assert title.startswith("LONG NVDA ")
    assert not any(line.startswith("Action:") for line in body.split("\n"))


def test_prd127_monitor_setup_body_does_not_leak_directional_prefixes():
    """PRD-133: MONITOR SETUP body has no Action line; Regime line carries the regime label."""
    _, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.7),
        validation_summary=_validation(),
        qualification_summary=_qual(["NVDA"], direction="LONG"),
        candidate_lines=("NVDA | LONG | TREND | 2.4:1",),
    )
    assert not any(line.startswith("Action:") for line in body.split("\n"))
    regime_lines = [line for line in body.split("\n") if line.startswith("Regime:")]
    assert len(regime_lines) == 1
    assert regime_lines[0] == "Regime: RISK ON"


def test_prd127_watchlist_only_branch_preserves_monitor_label():
    """R2: pre-existing MONITOR label for watchlist-only path MUST remain."""
    qual = QualificationSummary(
        regime_passed=True,
        regime_short_circuited=False,
        regime_failure_reason=None,
        qualified_trades=[],
        watchlist=[
            QualificationResult(
                symbol="AAPL",
                qualified=False,
                watchlist=True,
                direction="LONG",
                gates_passed=[],
                gates_failed=["STOP_DISTANCE"],
                hard_failure=None,
                watchlist_reason="developing",
                max_contracts=None,
                dollar_risk=None,
            )
        ],
        excluded={},
        symbols_evaluated=1,
        symbols_qualified=0,
        symbols_watchlist=1,
        symbols_excluded=0,
    )
    title, body = format_hourly_notification(
        asof_utc=datetime(2026, 5, 11, 16, 20, tzinfo=timezone.utc),
        regime=_regime(regime="RISK_ON", posture="CONTROLLED_LONG", confidence=0.7),
        validation_summary=_validation(),
        qualification_summary=qual,
    )
    assert title.startswith("MONITOR ")
    assert not title.startswith("MONITOR SETUP ")
    assert not any(line.startswith("Action:") for line in body.split("\n"))


def test_prd127_action_label_trade_branch_is_gated_by_canonical_outcome():
    """R8: every `return "TRADE"` line in notifications/__init__.py must
    sit inside a branch that tests canonical_outcome."""
    import cuttingboard.notifications as notif_pkg
    text = open(notif_pkg.__file__, "r", encoding="utf-8").read()
    lines = text.splitlines()
    trade_lines = [i for i, line in enumerate(lines, 1) if 'return "TRADE"' in line]
    assert trade_lines, 'no `return "TRADE"` branch found in notifier'
    for line_no in trade_lines:
        window = "\n".join(lines[max(0, line_no - 8):line_no])
        assert "canonical_outcome" in window, (
            f'return "TRADE" at line {line_no} is not gated by canonical_outcome'
        )


def test_prd127_format_hourly_notification_declares_canonical_outcome_kwarg():
    """R3: format_hourly_notification's signature must expose canonical_outcome
    with default None."""
    import inspect as _inspect
    sig = _inspect.signature(format_hourly_notification)
    assert "canonical_outcome" in sig.parameters
    param = sig.parameters["canonical_outcome"]
    assert param.default is None
    assert param.kind == _inspect.Parameter.KEYWORD_ONLY


def test_prd124_r1_no_duplicate_local_tz_declarations():
    """R1 source-level: exactly one ZoneInfo('America/Vancouver') declaration."""
    import cuttingboard.notifications as pkg_init
    from cuttingboard.notifications import formatter as fmt_mod
    init_src = open(pkg_init.__file__, "r", encoding="utf-8").read()
    fmt_src = open(fmt_mod.__file__, "r", encoding="utf-8").read()
    init_count = init_src.count('ZoneInfo("America/Vancouver")')
    fmt_count = fmt_src.count('ZoneInfo("America/Vancouver")')
    assert init_count == 0, "notifier __init__.py must not redeclare LOCAL_TZ"
    assert fmt_count == 1, "formatter.py must hold the single LOCAL_TZ declaration"


# ---------------------------------------------------------------------------
# Alert contract: no file writes on normal execution
# ---------------------------------------------------------------------------

def test_execute_notify_run_does_not_write_markdown():
    src = inspect.getsource(_execute_notify_run)
    assert "_write_markdown_report" not in src


def test_execute_notify_run_does_not_write_latest_run():
    src = inspect.getsource(_execute_notify_run)
    assert "_write_summary_files" not in src
    assert "LATEST_RUN_PATH" not in src


def test_hourly_run_writes_hourly_specific_artifacts(tmp_path, monkeypatch):
    import cuttingboard.runtime as runtime

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_RUN_PATH", tmp_path / "logs" / "latest_hourly_run.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_CONTRACT_PATH", tmp_path / "logs" / "latest_hourly_contract.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_PAYLOAD_PATH", tmp_path / "logs" / "latest_hourly_payload.json")
    monkeypatch.setattr(runtime, "HOURLY_REPORT_PATH", tmp_path / "reports" / "output" / "hourly_report.html")
    monkeypatch.setattr(runtime, "MARKET_MAP_PATH", tmp_path / "logs" / "market_map.json")

    patches = _patch_pipeline_stay_flat()
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
        result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    assert result["status"] == SUMMARY_STATUS_SUCCESS
    assert (tmp_path / "logs" / "latest_hourly_run.json").exists()
    assert (tmp_path / "logs" / "latest_hourly_contract.json").exists()
    assert (tmp_path / "logs" / "latest_hourly_payload.json").exists()
    assert (tmp_path / "logs" / "market_map.json").exists()
    assert (tmp_path / "reports" / "output" / "hourly_report.html").exists()
    assert not (tmp_path / "logs" / "latest_run.json").exists()

    hourly_run = json.loads((tmp_path / "logs" / "latest_hourly_run.json").read_text(encoding="utf-8"))
    hourly_contract = json.loads((tmp_path / "logs" / "latest_hourly_contract.json").read_text(encoding="utf-8"))
    hourly_payload = json.loads((tmp_path / "logs" / "latest_hourly_payload.json").read_text(encoding="utf-8"))
    market_map = json.loads((tmp_path / "logs" / "market_map.json").read_text(encoding="utf-8"))

    assert hourly_run["notify_mode"] == NOTIFY_HOURLY
    assert hourly_run["status"] == SUMMARY_STATUS_SUCCESS
    assert hourly_run["notification_sent"] is True
    assert hourly_contract["artifacts"]["log_path"].endswith("latest_hourly_run.json")
    assert hourly_contract["outcome"] == "NO_TRADE"
    assert hourly_payload["meta"]["timestamp"] == hourly_contract["generated_at"]
    assert hourly_run["generation_id"] == hourly_contract["generation_id"]
    assert hourly_payload["meta"]["generation_id"] == hourly_run["generation_id"]
    assert market_map["generation_id"] == hourly_run["generation_id"]


def test_hourly_run_failure_writes_hourly_failure_artifacts(tmp_path, monkeypatch):
    import cuttingboard.runtime as runtime

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_RUN_PATH", tmp_path / "logs" / "latest_hourly_run.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_CONTRACT_PATH", tmp_path / "logs" / "latest_hourly_contract.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_PAYLOAD_PATH", tmp_path / "logs" / "latest_hourly_payload.json")
    monkeypatch.setattr(runtime, "HOURLY_REPORT_PATH", tmp_path / "reports" / "output" / "hourly_report.html")
    monkeypatch.setattr(runtime, "MARKET_MAP_PATH", tmp_path / "logs" / "market_map.json")

    with (
        patch("cuttingboard.runtime.fetch_all", side_effect=RuntimeError("data fetch failed")),
        patch("cuttingboard.runtime.send_notification", return_value=True),
    ):
        result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    assert result["status"] == SUMMARY_STATUS_FAIL
    assert (tmp_path / "logs" / "latest_hourly_run.json").exists()
    assert (tmp_path / "logs" / "latest_hourly_contract.json").exists()
    assert (tmp_path / "logs" / "latest_hourly_payload.json").exists()

    hourly_run = json.loads((tmp_path / "logs" / "latest_hourly_run.json").read_text(encoding="utf-8"))
    hourly_contract = json.loads((tmp_path / "logs" / "latest_hourly_contract.json").read_text(encoding="utf-8"))
    hourly_payload = json.loads((tmp_path / "logs" / "latest_hourly_payload.json").read_text(encoding="utf-8"))

    assert hourly_run["status"] == SUMMARY_STATUS_FAIL
    assert hourly_run["notification_sent"] is True
    assert hourly_run["errors"] == ["data fetch failed"]
    assert hourly_contract["status"] == "ERROR"
    assert hourly_contract["outcome"] == "HALT"
    assert hourly_run["generation_id"] == hourly_contract["generation_id"]
    assert hourly_payload["meta"]["generation_id"] == hourly_run["generation_id"]


# ---------------------------------------------------------------------------
# Alert contract: exactly one send_notification per trigger
# ---------------------------------------------------------------------------

def _patch_pipeline_stay_flat():
    return [
        patch("cuttingboard.runtime.fetch_all", return_value={}),
        patch("cuttingboard.runtime.normalize_all", return_value={}),
        patch("cuttingboard.runtime.extract_fetch_failures", return_value={}),
        patch("cuttingboard.runtime.validate_quotes", return_value=_validation()),
        patch("cuttingboard.runtime.compute_regime", return_value=_regime(posture="STAY_FLAT", regime="NEUTRAL")),
        patch("cuttingboard.runtime.compute_all_derived", return_value={}),
        patch("cuttingboard.runtime.resolve_sector_router", return_value=_router_state()),
        patch("cuttingboard.runtime.send_notification", return_value=True),
    ]


def test_hourly_sends_exactly_once_stay_flat(tmp_path, monkeypatch):
    _setup_tmp_artifacts(monkeypatch, tmp_path)
    patches = _patch_pipeline_stay_flat()
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7] as mock_send:
        result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)
    mock_send.assert_called_once()
    assert result["status"] == SUMMARY_STATUS_SUCCESS


def test_hourly_sends_exactly_once_system_halted(tmp_path, monkeypatch):
    _setup_tmp_artifacts(monkeypatch, tmp_path)
    with (
        patch("cuttingboard.runtime.fetch_all", return_value={}),
        patch("cuttingboard.runtime.normalize_all", return_value={}),
        patch("cuttingboard.runtime.extract_fetch_failures", return_value={}),
        patch("cuttingboard.runtime.validate_quotes", return_value=_validation(halted=True)),
        patch("cuttingboard.runtime.send_notification", return_value=True) as mock_send,
    ):
        result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    mock_send.assert_called_once()
    assert result["status"] == SUMMARY_STATUS_SUCCESS


def test_hourly_sends_exactly_once_on_exception(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with (
        patch("cuttingboard.runtime.fetch_all", side_effect=RuntimeError("data fetch failed")),
        patch("cuttingboard.runtime.send_notification", return_value=True) as mock_send,
    ):
        result = _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    mock_send.assert_called_once()
    assert result["status"] == SUMMARY_STATUS_FAIL


def test_hourly_writes_traceback_on_exception(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with (
        patch("cuttingboard.runtime.fetch_all", side_effect=RuntimeError("data fetch failed")),
        patch("cuttingboard.runtime.send_notification", return_value=True),
    ):
        _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    assert (tmp_path / "traceback.txt").exists()
    content = (tmp_path / "traceback.txt").read_text()
    assert "RuntimeError" in content
    assert "data fetch failed" in content


# ---------------------------------------------------------------------------
# PRD-101: Notification truth contract fields in latest_hourly_run.json
# ---------------------------------------------------------------------------

_NOTIFICATION_FIELDS = (
    "notification_status",
    "notification_reason",
    "notification_attempted",
    "notification_transport",
    "notification_http_status",
    "notification_retry_count",
)


def _read_hourly_run(tmp_path) -> dict:
    return json.loads((tmp_path / "logs" / "latest_hourly_run.json").read_text(encoding="utf-8"))


def _setup_tmp_artifacts(monkeypatch, tmp_path):
    import cuttingboard.runtime as runtime
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(runtime, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(runtime, "REPORTS_DIR", tmp_path / "reports")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_RUN_PATH", tmp_path / "logs" / "latest_hourly_run.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_CONTRACT_PATH", tmp_path / "logs" / "latest_hourly_contract.json")
    monkeypatch.setattr(runtime, "LATEST_HOURLY_PAYLOAD_PATH", tmp_path / "logs" / "latest_hourly_payload.json")
    monkeypatch.setattr(runtime, "HOURLY_REPORT_PATH", tmp_path / "reports" / "output" / "hourly_report.html")
    monkeypatch.setattr(runtime, "MARKET_MAP_PATH", tmp_path / "logs" / "market_map.json")


def test_hourly_run_has_all_notification_fields(tmp_path, monkeypatch):
    _setup_tmp_artifacts(monkeypatch, tmp_path)
    patches = _patch_pipeline_stay_flat()
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7]:
        _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    hourly_run = _read_hourly_run(tmp_path)
    for field in _NOTIFICATION_FIELDS:
        assert field in hourly_run, f"missing field: {field}"
    assert hourly_run["notification_transport"] == "telegram"


def test_notification_sent_derived_strictly_from_status():
    """notification_sent is strictly derived from notification_status == SENT.

    Tests _build_hourly_run_summary directly for all five status values, verifying
    the derivation without going through the full pipeline.
    """
    from cuttingboard.output import NotificationResult
    from cuttingboard.runtime import (
        _build_hourly_run_summary,
        SUMMARY_STATUS_SUCCESS,
        OUTCOME_NO_TRADE,
    )

    run_at = datetime(2026, 4, 23, 14, 30, tzinfo=timezone.utc)
    base = dict(
        mode=MODE_LIVE,
        run_at_utc=run_at,
        run_date=date(2026, 4, 23),
        notify_mode=NOTIFY_HOURLY,
        validation_summary=None,
        regime=None,
        router_state=None,
        qualification_summary=None,
        candidate_lines=(),
        alert_title="TEST",
        alert_body="body",
        alert_sent=False,
        errors=[],
        status=SUMMARY_STATUS_SUCCESS,
        outcome=OUTCOME_NO_TRADE,
        raw_quotes={},
        normalized_quotes={},
    )

    cases = [
        ("SENT",              True),
        ("SKIPPED_NO_CONFIG", False),
        ("FAILED_TRANSPORT",  False),
        ("SUPPRESSED",        False),
        ("NOT_REQUESTED",     False),
    ]

    for n_status, expected_sent in cases:
        nr = NotificationResult(
            notification_status=n_status,
            notification_reason=None,
            notification_attempted=(n_status == "SENT"),
            notification_transport="telegram",
            notification_http_status=200 if n_status == "SENT" else None,
            notification_retry_count=0,
        )
        summary = _build_hourly_run_summary(**{**base, "notification_result": nr})
        assert summary["notification_status"] == n_status, (
            f"notification_status mismatch for {n_status}"
        )
        assert summary["notification_sent"] is expected_sent, (
            f"notification_sent={summary['notification_sent']} for status={n_status!r}; "
            f"expected {expected_sent}"
        )


def test_skipped_no_config_when_telegram_not_configured(tmp_path, monkeypatch):
    """Missing Telegram config produces SKIPPED_NO_CONFIG."""
    from cuttingboard import config as cfg
    _setup_tmp_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(cfg, "TELEGRAM_BOT_TOKEN", None)
    monkeypatch.setattr(cfg, "TELEGRAM_CHAT_ID", None)
    patches = _patch_pipeline_stay_flat()
    # Remove the send_notification mock so the real code runs
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    hourly_run = _read_hourly_run(tmp_path)
    assert hourly_run["notification_status"] == "SKIPPED_NO_CONFIG"
    assert hourly_run["notification_attempted"] is False
    assert hourly_run["notification_reason"] == "not_configured"
    assert hourly_run["notification_transport"] == "telegram"
    assert hourly_run["notification_sent"] is False


def test_sent_when_telegram_succeeds(tmp_path, monkeypatch):
    """Successful mocked send produces SENT."""
    from cuttingboard import config as cfg
    _setup_tmp_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(cfg, "TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setattr(cfg, "TELEGRAM_CHAT_ID", "test_chat")

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    patches = _patch_pipeline_stay_flat()
    # Remove the send_notification mock; mock requests.post instead
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        with patch("requests.post", return_value=mock_resp):
            _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    hourly_run = _read_hourly_run(tmp_path)
    assert hourly_run["notification_status"] == "SENT"
    assert hourly_run["notification_attempted"] is True
    assert hourly_run["notification_transport"] == "telegram"
    assert hourly_run["notification_http_status"] == 200
    assert hourly_run["notification_sent"] is True


def test_failed_transport_when_telegram_fails(tmp_path, monkeypatch):
    """Failed mocked send produces FAILED_TRANSPORT."""
    from cuttingboard import config as cfg
    _setup_tmp_artifacts(monkeypatch, tmp_path)
    monkeypatch.setattr(cfg, "TELEGRAM_BOT_TOKEN", "test_token")
    monkeypatch.setattr(cfg, "TELEGRAM_CHAT_ID", "test_chat")

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    patches = _patch_pipeline_stay_flat()
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        with patch("requests.post", return_value=mock_resp):
            _execute_notify_run(mode=MODE_LIVE, run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    hourly_run = _read_hourly_run(tmp_path)
    assert hourly_run["notification_status"] == "FAILED_TRANSPORT"
    assert hourly_run["notification_attempted"] is True
    assert hourly_run["notification_transport"] == "telegram"
    assert hourly_run["notification_sent"] is False


def test_not_requested_when_mode_is_not_live(tmp_path, monkeypatch):
    """No notification call requested when mode != MODE_LIVE."""
    _setup_tmp_artifacts(monkeypatch, tmp_path)
    patches = _patch_pipeline_stay_flat()
    # mode=MODE_FIXTURE skips the send_notification call
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        _execute_notify_run(mode="fixture", run_date=date(2026, 4, 23), notify_mode=NOTIFY_HOURLY)

    hourly_run = _read_hourly_run(tmp_path)
    assert hourly_run["notification_status"] == "NOT_REQUESTED"
    assert hourly_run["notification_attempted"] is False
    assert hourly_run["notification_sent"] is False
