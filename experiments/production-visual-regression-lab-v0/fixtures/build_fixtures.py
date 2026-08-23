"""Build deterministic production dashboard specimens for the visual lab.

This module deliberately owns no production logic.  It supplies in-memory
carriers to the current renderer and writes only the generated HTML and truth
catalog beneath this experiment.  The values are fixed so that a second build
is byte-for-byte identical to the first one.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make direct ``python path/to/build_fixtures.py`` invocation independent of
# the caller's working directory while keeping the renderer import explicit.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.dont_write_bytecode = True

from cuttingboard import config
from cuttingboard.delivery.dashboard_renderer import render_dashboard_html


LAB_DIR = Path(__file__).resolve().parent.parent
GENERATED_DIR = LAB_DIR / "fixtures" / "generated"
CATALOG_PATH = LAB_DIR / "fixtures" / "catalog.json"
FIXED_NOW = datetime(2026, 8, 23, 20, 0, tzinfo=timezone.utc)
FIXED_TS = "2026-08-23T20:00:00Z"
BASELINE_SHA = "044602770f745e322dc47a88e9bd342dc0955ce7"
GENERATION_ID = "fixture-prd314-23-13"

VIEWPORTS = [[360, 800], [390, 844], [430, 932], [431, 932], [768, 1024], [960, 900], [1280, 800], [1440, 900]]
SCALES = [100, 125, 150, 200]

CURRENT_PADDING = "#market-state,#system-state,#opportunity-survival{padding:10px;margin-bottom:10px}"
HISTORICAL_PADDING = "#market-state,#system-state,#opportunity-survival{padding:12px;margin-bottom:10px}"
CURRENT_GRID = "#opportunity-survival .kv-grid{grid-template-columns:max-content minmax(2.5ch,1fr) max-content minmax(2.5ch,1fr)}"
HISTORICAL_GRID = "#opportunity-survival .kv-grid{grid-template-columns:max-content minmax(0,1fr) max-content minmax(0,1fr)}"

CORE_IDS = (
    "normal", "halt", "operator-lock", "state-unavailable",
    "candidate-carrier-unavailable", "gex-unavailable", "movement-unavailable",
    "red-folder-event", "healthy-empty-red-folder", "no-candidate",
    "multiple-candidates", "opportunity-suppressed", "qualified-zero-b-candidate",
    "stale-board", "inactive-session",
)


def _macro_drivers() -> dict:
    return {
        "volatility": {"symbol": "^VIX", "level": 18.0, "change_pct": 0.05},
        "dollar": {"symbol": "DX-Y.NYB", "level": 104.0, "change_pct": -0.01},
        "rates": {"symbol": "^TNX", "level": 4.5, "change_pct": 0.02, "change_bps": 2.0},
        "bitcoin": {"symbol": "BTC-USD", "level": 65000.0, "change_pct": 0.03},
    }


def _candidate(symbol: str = "SPY", grade: str = "B", *, long_text: bool = False,
               missing_optional: bool = False, setup_state: str = "DEVELOPING") -> dict:
    if missing_optional:
        return {
            "symbol": symbol, "grade": grade, "bias": "BULL", "structure": "UPTREND",
            "setup_state": setup_state, "confidence": "MEDIUM", "current_price": 100.0,
            "watch_zones": [], "fib_levels": None, "what_to_look_for": [],
            "invalidation": [], "preferred_trade_structure": None,
            "reason_for_grade": None, "trade_framing": {}, "asset_group": "EQUITY",
        }
    suffix = (
        " with sustained breadth, clean reclaim, and confirmation across the monitored "
        "session structure; continue observing the hourly close before escalation."
        if long_text else " with constructive follow-through"
    )
    return {
        "symbol": symbol, "grade": grade, "bias": "BULL", "structure": "UPTREND",
        "setup_state": setup_state, "confidence": "MEDIUM", "current_price": 100.0,
        "watch_zones": [{"type": "SUPPORT", "level": 99.0}, {"type": "RESISTANCE", "level": 101.0}],
        "fib_levels": None, "what_to_look_for": ["watch volume confirmation" + suffix],
        "invalidation": ["loses reference and fails to recover" + suffix,
                         "momentum fades below trend support"],
        "preferred_trade_structure": "defined-risk debit spread",
        "reason_for_grade": "B DEVELOPING candidate: " + (
            ("extended evidence remains under observation across the scheduled review window " * 5).strip()
            if long_text else "constructive trend"
        ),
        "trade_framing": {
            "direction": "LONG",
            "entry": "hold above reference with constructive follow-through",
            "if_now": "WAIT",
            "downgrade": "close below reference invalidates the setup",
        },
        "asset_group": "EQUITY",
    }


def _market_map(symbols: dict[str, dict] | None = None, *, generation: str = GENERATION_ID,
                generated_at: str = FIXED_TS) -> dict:
    entries = symbols if symbols is not None else {"SPY": _candidate()}
    return {
        "schema_version": "market_map.v1", "generation_id": generation,
        "generated_at": generated_at, "primary_symbols": list(entries), "symbols": entries,
    }


def _rejections(count: int, *, long_reason: bool = False) -> list[dict]:
    reason = "execution evidence unavailable: " + (
        ("operator review remains required before qualification can resume " * 5).strip()
        if long_reason else "review later"
    )
    return [{"symbol": f"R{index:02d}", "stage": "QUALIFICATION", "reason": reason if index == 0 else "ONE_SOFT_MISS"}
            for index in range(count)]


def _watchlist(count: int, *, long_watch: bool = False) -> list[dict]:
    text = (
        ("watch for confirmation at the next scheduled review before changing state " * 5).strip()
        if long_watch else "monitor during next review"
    )
    return [{"symbol": f"W{index:02d}", "stage": "WATCHLIST", "reason": text} for index in range(count)]


def _payload(*, generation: str = GENERATION_ID, timestamp: str = FIXED_TS,
             scanned: int = 23, watchlist_count: int = 13, rejected_count: int = 7,
             session_type: str | None = None, long_reason: bool = False,
             long_watch: bool = False) -> dict:
    meta = {"timestamp": timestamp, "symbols_scanned": scanned, "generation_id": generation}
    if session_type is not None:
        meta["session_type"] = session_type
    return {
        "schema_version": "1.0", "run_status": "OK", "meta": meta,
        "macro_drivers": _macro_drivers(),
        "summary": {"market_regime": "RISK_ON", "tradable": True, "router_mode": "MIXED"},
        "sections": {
            "top_trades": [], "watchlist": _watchlist(watchlist_count, long_watch=long_watch),
            "rejected": _rejections(rejected_count, long_reason=long_reason),
            "option_setups_detail": [], "chain_results_detail": [],
            "continuation_audit": None, "watch_summary_detail": None,
            "validation_halt_detail": None, "trade_decision_detail": [],
        },
    }


def _run(*, generation: str = GENERATION_ID, timestamp: str = FIXED_TS,
         status: str = "SUCCESS", system_halted: bool = False,
         errors: list[str] | None = None, outcome: str = "NO_TRADE",
         permission: str | None = "Long bias — trend continuation allowed.",
         session_type: str | None = None) -> dict:
    run = {
        "run_id": "fixture-20260823T200000Z", "generation_id": generation,
        "status": status, "regime": "RISK_ON", "posture": "CONTROLLED_LONG",
        "confidence": 0.75, "system_halted": system_halted, "kill_switch": False,
        "errors": errors or [], "data_status": "ok", "outcome": outcome,
        "permission": permission, "mode": "LIVE", "timestamp": timestamp, "warnings": [],
    }
    if session_type is not None:
        run["session_type"] = session_type
    return run


def _gex() -> dict:
    return {
        "schema_version": 1, "source": "cboe_delayed_quotes",
        "data_delay": "~15 min delayed (REPORTED; Cboe delayed_quotes posture)",
        "gex_total_1pct_usd": -58358882895.27673,
        "spot": {"value": 7641.1602, "basis": "SPX cash index level"},
        "fetched_at_utc": "2026-08-23T19:42:00+00:00",
        "call_wall": {"strike": 8000.0, "gex_1pct_usd": 1.0, "reason": None},
        "put_wall": {"strike": 7400.0, "gex_1pct_usd": -1.0, "reason": None},
        "dominant_net_gamma": {"strike": 7640.0, "gex_1pct_usd": -1.0, "reason": None},
        "zero_dte": {"share": 0.07635226668688595, "reason": None},
    }


def _movement() -> dict:
    rows = (
        ("SPY", "INDEX", 0), ("QQQ", "INDEX", 1), ("GDX", "METALS", 2),
        ("GLD", "METALS", 3), ("SLV", "METALS", 4), ("XLE", "ENERGY", 5),
        ("UCO", "ENERGY", 6), ("NVDA", "TECH", 7), ("META", "TECH", 9),
        ("AMZN", "TECH", 10), ("GOOG", "TECH", 11), ("TSLA", "HIGH_BETA", 8),
    )
    return {
        "schema_version": 2, "source": "watchlist", "generated_at": "2026-08-23T19:45:00+00:00",
        "symbols": {
            sym: {"symbol": sym, "sector_theme": "Index", "watch_reason": "fixture watch",
                  "current_price": 100.0 + idx, "daily_change_pct": float((idx - 5) / 10),
                  "primary_group": group, "registry_index": idx}
            for sym, group, idx in rows
        },
    }


def _event(name: str = "CPI (July)", text: str | None = None) -> dict:
    return {"date": "2026-08-24", "time_et": "08:30", "name": text or name, "type": "INFLATION"}


def _base_inputs() -> dict:
    return {"payload": _payload(), "run": _run(), "market_map": _market_map(),
            "gex_snapshot": _gex(), "movement_snapshot": _movement(),
            "red_folder": {"ok": True, "expiring": False, "events": []}}


def _render(inputs: dict) -> str:
    return render_dashboard_html(
        inputs["payload"], inputs["run"], market_map=inputs.get("market_map"),
        gex_snapshot=inputs.get("gex_snapshot"), movement_snapshot=inputs.get("movement_snapshot"),
        red_folder=inputs.get("red_folder"), fixture_mode=False, now=FIXED_NOW,
    )


def _core_inputs() -> dict[str, dict]:
    cases = {name: _base_inputs() for name in CORE_IDS}
    cases["halt"]["payload"] = _payload()
    cases["halt"]["payload"]["sections"]["validation_halt_detail"] = {
        "reason": "HALT: carrier validation failed after " + (
            "an extended operator-visible diagnostic review remained unresolved " * 4
        ).strip()
    }
    cases["halt"]["run"] = _run(status="HALT", system_halted=True,
                                  errors=["HALT: execution carrier unavailable — review pipeline evidence before retry"])
    cases["operator-lock"]["run"] = _run(permission=config.OPERATOR_LOCK_PERMISSION)
    cases["state-unavailable"]["payload"] = _payload(generation=GENERATION_ID + "-payload")
    cases["state-unavailable"]["run"] = _run(generation=GENERATION_ID + "-run")
    cases["state-unavailable"]["market_map"] = _market_map(generation=GENERATION_ID + "-market")
    cases["candidate-carrier-unavailable"]["market_map"] = None
    cases["gex-unavailable"]["gex_snapshot"] = None
    cases["movement-unavailable"]["movement_snapshot"] = None
    cases["red-folder-event"]["red_folder"] = {"ok": True, "expiring": False, "events": [_event()]}
    cases["healthy-empty-red-folder"]["red_folder"] = {"ok": True, "expiring": False, "events": []}
    cases["no-candidate"]["market_map"] = _market_map({})
    cases["multiple-candidates"]["market_map"] = _market_map({
        "SPY": _candidate("SPY", "A+", setup_state="TRIGGERED"),
        "QQQ": _candidate("QQQ", "A", setup_state="DEVELOPING"),
        "GDX": _candidate("GDX", "B", setup_state="EARLY"),
    })
    cases["opportunity-suppressed"]["payload"] = _payload(scanned=0, watchlist_count=0, rejected_count=0)
    cases["qualified-zero-b-candidate"]["payload"] = _payload(scanned=13, watchlist_count=13, rejected_count=0)
    stale_ts = "2026-08-23T18:00:00Z"
    cases["stale-board"]["payload"] = _payload(timestamp=stale_ts)
    cases["stale-board"]["run"] = _run(timestamp=stale_ts)
    cases["stale-board"]["market_map"] = _market_map(generated_at=stale_ts)
    cases["inactive-session"]["payload"] = _payload(session_type="SUNDAY_PREMARKET")
    cases["inactive-session"]["run"] = _run(session_type="SUNDAY_PREMARKET")
    return cases


def _content_inputs() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for value in (0, 1, 9, 10, 13, 23, 99, 100, 999):
        inputs = _base_inputs()
        watch = min(value, 13)
        rejects = max(0, value - watch)
        inputs["payload"] = _payload(scanned=value, watchlist_count=watch, rejected_count=rejects)
        out[f"content-opportunity-{value}"] = inputs
    inputs = _base_inputs()
    inputs["market_map"] = _market_map({"UCO": _candidate("UCO", "B"), "NVDA": _candidate("NVDA", "B")})
    out["content-symbol-extremes"] = inputs
    inputs = _base_inputs()
    inputs["market_map"] = _market_map({
        "SPY": _candidate("SPY", "A+", setup_state="TRIGGERED"),
        "QQQ": _candidate("QQQ", "A"), "GDX": _candidate("GDX", "B"),
        "GLD": _candidate("GLD", "C", missing_optional=True),
    })
    out["content-multiple-cards"] = inputs
    inputs = _base_inputs()
    inputs["payload"] = _payload(long_reason=True, long_watch=True)
    inputs["market_map"] = _market_map({"SPY": _candidate("SPY", "B", long_text=True)})
    out["content-long-text"] = inputs
    inputs = _base_inputs()
    inputs["market_map"] = _market_map({"GLD": _candidate("GLD", "C", missing_optional=True)})
    out["content-missing-optionals"] = inputs
    inputs = _base_inputs()
    inputs["run"] = _run(permission="WAIT")
    out["content-permission-short"] = inputs
    inputs = _base_inputs()
    inputs["run"] = _run(permission="No new trades permitted — operator cannot continuously monitor the full execution surface during this extended review window.")
    out["content-permission-long"] = inputs
    for length, label in ((1, "short"), (2, "medium"), (4, "long")):
        inputs = _base_inputs()
        inputs["red_folder"] = {"ok": True, "expiring": False,
                                 "events": [_event(text=(
                                     "Employment and inflation release with revised outlook " * length
                                 ).strip())]}
        out[f"content-event-{label}"] = inputs
    return out


def _contract(fixture_id: str, filename: str, *, source_mode: str = "production-renderer",
              synthetic: bool = False, groups: list[str] | None = None,
              covers: list[str] | None = None, matrix: str = "representative",
              expected_verdict: str = "PASS", required: list[str] | None = None,
              forbidden: list[str] | None = None, candidate: dict | None = None,
              opportunity: int | None = 23, labels: dict | None = None,
              run_plan: list[dict] | None = None,
              expected_verdicts: list[dict] | None = None) -> dict:
    candidate_spec = candidate or {
        "minimumCards": 1, "symbols": ["SPY"], "grade": "B",
        "setupState": "DEVELOPING",
    }
    candidate_present = int(candidate_spec.get("minimumCards", 0)) > 0
    low_grade_only = fixture_id == "content-missing-optionals"
    candidate_truth = {
        "identity": candidate_present,
        "level": candidate_present and not low_grade_only,
        "invalidation": candidate_present and not low_grade_only,
        "minimumCards": int(candidate_spec.get("minimumCards", 0)),
    }
    if not candidate_present:
        candidate_truth["maximumCards"] = 0
    unhealthy_without_opportunity = {
        "candidate-carrier-unavailable", "state-unavailable"
    }
    opportunity_present = (
        opportunity not in (None, 0)
        and fixture_id not in unhealthy_without_opportunity
    )
    gex_present = fixture_id != "gex-unavailable"
    movement_present = fixture_id != "movement-unavailable"
    red_folder_present = (
        fixture_id == "red-folder-event"
        or fixture_id.startswith("content-event-")
    )
    staleness_visible = fixture_id in {"stale-board", "inactive-session"}

    presence = {
        "marketState": "present",
        "systemState": "present",
        "opportunity": "present" if opportunity_present else "absent",
        "gex": "present" if gex_present else "absent",
        "movement": "present" if movement_present else "absent",
        "redFolder": "present" if red_folder_present else "absent",
        "candidate": "present",
        "provenance": "present",
        "qualifier": "present" if gex_present else "absent",
    }
    if staleness_visible:
        presence["staleness"] = "present"

    expected_labels: dict[str, object]
    if not opportunity_present:
        expected_labels = {}
    elif labels is not None:
        expected_labels = labels
    elif fixture_id.startswith("content-opportunity-"):
        value = int(fixture_id.rsplit("-", 1)[1])
        watch = min(value, 13)
        rejected = max(0, value - watch)
        expected_labels = {
            "SURFACED": value,
            "QUALIFIED": 0,
            "WATCHLIST": watch,
            "REJECTED": rejected,
        }
    elif fixture_id == "qualified-zero-b-candidate":
        expected_labels = {
            "SURFACED": 13, "QUALIFIED": 0,
            "WATCHLIST": 13, "REJECTED": 0,
        }
    else:
        qualified_label = "SETUPS FOUND" if fixture_id == "operator-lock" else "QUALIFIED"
        expected_labels = {
            "SURFACED": 23, qualified_label: 3,
            "WATCHLIST": 13, "REJECTED": 7,
        }

    required_text: list[object] = [
        item for item in sorted(required or [])
        if not item.startswith("card-") and item != "B DEVELOPING"
    ]
    for symbol in candidate_spec.get("symbols", []):
        required_text.append({"key": "candidate", "includes": [symbol]})
    candidate_grade = candidate_spec.get("grade")
    candidate_state = candidate_spec.get("setupState")
    if candidate_grade:
        required_text.append({"key": "candidate", "includes": [candidate_grade]})
    if candidate_state:
        required_text.append({"key": "candidate", "includes": [candidate_state]})
    if fixture_id == "halt":
        required_text.append({"key": "systemState", "includes": ["HALT", "SYSTEM HALT"]})
    if fixture_id == "operator-lock":
        required_text.append({"key": "systemState", "includes": ["OBSERVE ONLY", "OPERATOR LOCK"]})
    if fixture_id == "state-unavailable":
        required_text.append({"key": "systemState", "includes": ["STATE UNAVAILABLE"]})
    if fixture_id == "candidate-carrier-unavailable":
        required_text.append({"key": "candidate", "includes": ["SOURCE_MISSING"]})
    if fixture_id == "gex-unavailable":
        required_text.append({"key": "marketState", "includes": ["POSITIONING", "unavailable"]})
    if fixture_id == "movement-unavailable":
        required_text.append({"key": "marketState", "includes": ["PARTICIPATION", "unavailable"]})
    if fixture_id == "healthy-empty-red-folder":
        required_text.append({"key": "marketState", "includes": ["no events in 48h"]})
    if fixture_id == "stale-board":
        required_text.append({"key": "staleness", "includes": ["BOARD 2h OLD"]})
    if fixture_id == "inactive-session":
        required_text.append({"key": "staleness", "includes": ["MARKET CLOSED"]})
        required_text.append({"key": "candidate", "includes": ["SESSION INACTIVE"]})

    critical_keys = ["marketState", "systemState", "candidate"]
    if opportunity_present:
        critical_keys.append("opportunity")
    if gex_present:
        critical_keys.extend(["gex", "provenance", "qualifier"])
    if movement_present:
        critical_keys.append("movement")
    if red_folder_present:
        critical_keys.append("redFolder")
    if staleness_visible:
        critical_keys.append("staleness")

    warn_on_wrap: list[str] = []
    if fixture_id == "content-long-text":
        warn_on_wrap.append("candidateInvalidation")
    if fixture_id == "content-permission-long":
        warn_on_wrap.append("marketState")
    if fixture_id == "content-event-long":
        warn_on_wrap.append("redFolder")

    contract = {
        "id": fixture_id,
        "label": fixture_id.replace("-", " ").title(),
        "file": f"generated/{filename}",
        "sourceMode": source_mode,
        "synthetic": synthetic,
        "groups": sorted(groups or []),
        "covers": sorted(covers or []),
        "matrix": matrix,
        "expectedVerdict": expected_verdict,
        "expected": {
            "presence": presence,
            "candidate": candidate_truth,
            "criticalKeys": sorted(set(critical_keys)),
            "requiredText": required_text,
            "forbiddenText": sorted(forbidden or []),
            "opportunityValues": expected_labels,
            "warnOnWrap": warn_on_wrap,
            "information": [
                "Opportunity-to-Candidate adjacency and Candidate-before-Context are measurements only."
            ],
        },
        "comparison": {
            "visibleTextKeys": [
                "marketState", "systemState", "opportunity", "candidateIdentity"
            ],
            "requireTextEquality": ["marketState", "systemState", "opportunity"],
        },
    }
    open_details: list[str] = []
    if fixture_id == "content-long-text":
        contract["synthetic"] = True
        contract["sourceMode"] = "production-renderer+open-disclosure-stress"
        open_details.append("#candidate-board details.card-detail")
    if fixture_id in {"content-missing-optionals", "content-multiple-cards"}:
        open_details.append("#candidate-board details.tier-group")
    if open_details:
        contract["setup"] = {"openDetails": open_details}
    if run_plan is not None:
        contract["runPlan"] = run_plan
    if expected_verdicts is not None:
        contract["expectedVerdicts"] = expected_verdicts
    return contract


def _catalog() -> tuple[list[dict], dict[str, str]]:
    core = _core_inputs()
    extras = _content_inputs()
    all_inputs = {**core, **extras}
    entries: list[dict] = []
    for fixture_id in sorted(all_inputs):
        filename = f"{fixture_id}.html"
        groups = ["core"] if fixture_id in CORE_IDS else ["content-torture"]
        covers: list[str] = []
        required: list[str] = []
        forbidden: list[str] = []
        candidate: dict = {"minimumCards": 1, "symbols": ["SPY"], "grade": "B", "setupState": "DEVELOPING"}
        matrix = "all" if fixture_id in ("normal", "prd314-current-23-13") else ("pressure" if fixture_id.startswith("content-") else "representative")
        opportunity: int | None = 23
        if fixture_id == "halt":
            covers += ["halt", "long-halt-reason", "long-unavailable-reason"]
            required += ["SYSTEM HALT", "HALT: execution carrier unavailable"]
        elif fixture_id == "operator-lock":
            covers += ["operator-lock", "short-permission"]; required += ["OPERATOR LOCK", "OBSERVE ONLY"]; forbidden += ["TRADE PERMITTED", "IF NOW"]
        elif fixture_id == "state-unavailable":
            covers += ["mixed-generation", "state-unavailable"]
            required += ["MIXED_ARTIFACTS", "STATE UNAVAILABLE"]
            candidate = {"minimumCards": 0, "symbols": []}
        elif fixture_id == "candidate-carrier-unavailable":
            covers += ["candidate-carrier-unavailable"]; required += ["SOURCE_MISSING"]
            candidate = {"minimumCards": 0, "symbols": []}
        elif fixture_id == "gex-unavailable":
            covers += ["gex-unavailable"]; required += ["POSITIONING", "unavailable"]
        elif fixture_id == "movement-unavailable":
            covers += ["movement-unavailable"]; required += ["PARTICIPATION", "unavailable"]
        elif fixture_id == "red-folder-event":
            covers += ["red-folder-event"]
            required += ["CPI (July)", "1 events in 48h"]
        elif fixture_id == "healthy-empty-red-folder":
            covers += ["healthy-empty-red-folder"]; required += ["no events in 48h"]
        elif fixture_id == "no-candidate":
            covers += ["no-candidate"]; required += ["NO_CANDIDATES"]; candidate = {"minimumCards": 0, "symbols": []}
        elif fixture_id == "multiple-candidates":
            covers += ["multiple-cards"]; required += ["card-SPY", "card-QQQ", "card-GDX"]; candidate = {"minimumCards": 3, "symbols": ["SPY", "QQQ", "GDX"]}
        elif fixture_id == "opportunity-suppressed":
            covers += ["opportunity-suppressed"]; opportunity = 0; candidate = {"minimumCards": 1, "symbols": ["SPY"]}
        elif fixture_id == "qualified-zero-b-candidate":
            covers += ["qualified-zero", "b-developing"]; required += ["SURFACED", "WATCHLIST", "card-SPY"]; opportunity = 13
        elif fixture_id == "stale-board":
            covers += ["stale-board"]
        elif fixture_id == "inactive-session":
            covers += ["inactive-session"]
            required += ["SESSION INACTIVE"]
            candidate = {"minimumCards": 0, "symbols": []}
        elif fixture_id == "normal":
            covers += [
                "normal", "b-developing", "symbol-short", "surface-23",
                "watchlist-13", "full-positioning-provenance", "full-qualifier",
            ]
            required += [
                "SURFACED", "WATCHLIST", "B DEVELOPING",
                "Cboe ~15m delayed", "positioning is not measured",
            ]
        elif fixture_id.startswith("content-opportunity-"):
            value = int(fixture_id.rsplit("-", 1)[1]); opportunity = value; covers += [f"opportunity-{value}"]; required += (["SURFACED"] if value else [])
        elif fixture_id == "content-symbol-extremes":
            covers += ["registry-shortest-symbol", "registry-longest-symbol"]
            required += ["UCO", "NVDA"]
            candidate = {"minimumCards": 2, "symbols": ["UCO", "NVDA"]}
        elif fixture_id == "content-multiple-cards":
            covers += ["multiple-cards", "missing-optional-fields"]; required += ["card-SPY", "card-GLD"]; candidate = {"minimumCards": 4, "symbols": ["SPY", "QQQ", "GDX", "GLD"]}
        elif fixture_id == "content-long-text":
            covers += ["long-reason", "long-watch", "long-invalidation"]
            required += ["extended evidence remains under observation"]
        elif fixture_id == "content-missing-optionals":
            covers += ["missing-optional-fields"]; required += ["card-GLD"]; candidate = {"minimumCards": 1, "symbols": ["GLD"]}
        elif fixture_id == "content-permission-short":
            covers += ["short-permission"]; required += ["WAIT"]
        elif fixture_id == "content-permission-long":
            covers += ["long-permission"]
            required += ["continuously monitor"]
        elif fixture_id.startswith("content-event-"):
            length_name = fixture_id.rsplit("-", 1)[1]
            covers += [f"event-text-{length_name}"]
            required += ["E"]
        entries.append(_contract(fixture_id, filename, groups=groups, covers=covers, matrix=matrix,
                                 required=required, forbidden=forbidden, candidate=candidate, opportunity=opportunity))
    return entries, all_inputs


def _write_if_changed(path: Path, content: str) -> None:
    encoded = content.encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded)


def build() -> dict:
    entries, inputs = _catalog()
    html_by_id: dict[str, str] = {}
    for fixture_id in sorted(inputs):
        html = _render(inputs[fixture_id])
        html_by_id[fixture_id] = html
        _write_if_changed(GENERATED_DIR / f"{fixture_id}.html", html)

    # The baseline pair is rendered from the same current carrier.  The mutant
    # is closed-fail: each historical declaration must occur exactly once.
    current_html = html_by_id["normal"]
    _write_if_changed(GENERATED_DIR / "prd314-current-23-13.html", current_html)
    if current_html.count(CURRENT_PADDING) != 1 or current_html.count(CURRENT_GRID) != 1:
        raise RuntimeError("PRD-314 mutation refused: current CSS declarations drifted")
    mutant_html = current_html.replace(CURRENT_PADDING, HISTORICAL_PADDING, 1).replace(CURRENT_GRID, HISTORICAL_GRID, 1)
    if CURRENT_PADDING in mutant_html or CURRENT_GRID in mutant_html:
        raise RuntimeError("PRD-314 mutation refused: current declaration survived")
    _write_if_changed(GENERATED_DIR / "prd314-prefixt-23-13.html", mutant_html)

    entries.append(_contract(
        "prd314-current-23-13", "prd314-current-23-13.html", source_mode="production-current",
        groups=["prd314", "calibration"],
        covers=["prd314", "surface-23", "watchlist-13"], matrix="calibration",
        required=["SURFACED", "WATCHLIST", "B DEVELOPING"], candidate={"minimumCards": 1, "symbols": ["SPY"], "grade": "B", "setupState": "DEVELOPING"},
        labels={"SURFACED": 23, "QUALIFIED": 3, "WATCHLIST": 13, "REJECTED": 7},
        run_plan=[
            {"width": 360, "height": 800, "scales": [100, 125]},
            {"width": 431, "height": 932, "scales": [100]},
        ],
    ))
    entries.append(_contract(
        "prd314-prefixt-23-13", "prd314-prefixt-23-13.html", source_mode="synthetic-calibration",
        synthetic=True, groups=["prd314", "calibration"], covers=["prd314", "historical-defect", "surface-23", "watchlist-13"],
        matrix="calibration", expected_verdict="PASS", required=["SURFACED", "WATCHLIST", "B DEVELOPING"],
        candidate={"minimumCards": 1, "symbols": ["SPY"], "grade": "B", "setupState": "DEVELOPING"},
        labels={"SURFACED": 23, "QUALIFIED": 3, "WATCHLIST": 13, "REJECTED": 7},
        run_plan=[
            {"width": 360, "height": 800, "scales": [100, 125]},
            {"width": 431, "height": 932, "scales": [100]},
        ],
        expected_verdicts=[{"width": 360, "height": 800, "scale": 125, "verdict": "FAIL"}],
    ))
    entries.sort(key=lambda item: item["id"])
    viewports = [{"width": width, "height": height} for width, height in VIEWPORTS]
    selectors = {
        "root": ".wrap",
        "marketState": "#market-state",
        "systemState": "#system-state",
        "opportunity": "#opportunity-survival",
        "gex": "#gex-context",
        "movement": "#market-movement",
        "macro": "#macro-tape",
        "redFolder": "#red-folder",
        "trend": "#trend-structure",
        "candidate": "#candidate-board",
        "candidateIdentity": (
            "#candidate-board .candidate-card .card-header,"
            "#candidate-board .candidate-card .failed-card-fields .value"
        ),
        "runDelta": "#run-delta",
        "scoreboard": "#scoreboard",
        "provenance": "#market-state .market-state-provenance",
        "qualifier": "#market-state .market-state-qualifier",
        "staleness": "#staleness-banner",
    }
    required_coverage = [
        "normal", "halt", "operator-lock", "state-unavailable",
        "candidate-carrier-unavailable", "gex-unavailable", "movement-unavailable",
        "red-folder-event", "healthy-empty-red-folder", "no-candidate",
        "multiple-cards", "opportunity-suppressed", "qualified-zero",
        "b-developing", "stale-board", "inactive-session",
        "opportunity-0", "opportunity-1", "opportunity-9", "opportunity-10",
        "opportunity-13", "opportunity-23", "opportunity-99",
        "opportunity-100", "opportunity-999", "symbol-short",
        "registry-shortest-symbol", "registry-longest-symbol", "long-reason",
        "long-watch", "long-invalidation", "missing-optional-fields",
        "short-permission", "long-permission", "long-unavailable-reason",
        "full-positioning-provenance", "full-qualifier", "event-text-short",
        "event-text-medium", "event-text-long", "surface-23", "watchlist-13",
        "historical-defect",
    ]
    catalog = {
        "schemaVersion": 1,
        "baseline": BASELINE_SHA,
        "baselineSha": BASELINE_SHA,
        "sourceIdentifier": f"cuttingboard@{BASELINE_SHA}",
        "fixedNow": FIXED_TS,
        "viewports": viewports,
        "scales": SCALES,
        "expectedCaseCount": 438,
        "requiredCoverage": required_coverage,
        "defaults": {
            "selectors": selectors,
            "criticalKeys": ["marketState", "systemState", "candidate"],
            "contextKeys": ["gex", "movement", "macro", "redFolder", "trend"],
            "surfaceKeys": [
                "marketState", "systemState", "opportunity", "gex", "movement",
                "macro", "redFolder", "trend", "candidate", "runDelta", "scoreboard",
            ],
            "order": [
                "marketState", "systemState", "opportunity", "gex", "movement",
                "macro", "redFolder", "trend", "candidate", "runDelta", "scoreboard",
            ],
            "candidateLevelLabels": ["IN →", "LEVEL"],
            "candidateInvalidationLabels": ["OUT →", "INVALIDATION"],
        },
        "matrix": {"viewports": VIEWPORTS, "scales": SCALES,
                   "defaults": {"matrix": "representative", "scale": 100}},
        "matrixDefaults": {"viewports": VIEWPORTS, "scales": SCALES,
                            "scaleMethod": "root-font-size-percent", "phoneBreakpointMaxWidth": 430},
        "fixtures": entries,
    }
    catalog_text = json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _write_if_changed(CATALOG_PATH, catalog_text)
    return {"fixture_count": len(entries), "files": sorted([p.name for p in GENERATED_DIR.glob("*.html")]),
            "catalog_sha256": hashlib.sha256(catalog_text.encode("utf-8")).hexdigest()}


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, sort_keys=True))
