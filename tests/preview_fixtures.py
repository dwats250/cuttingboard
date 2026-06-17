"""PRD-179 — section-state fixture catalog for the dashboard preview harness.

Each case deterministically triggers one conditional section state of the
dashboard renderer, reusing the ``tests/dash_helpers.py`` builders (SEAM 179-A:
reuse/extend, no parallel corpus). Both ``tests/test_preview_fixtures.py`` and
``scripts/preview_fixtures.py`` consume :data:`SECTION_STATE_CASES`, so the test
corpus and the preview harness can never drift apart.

R2 guarantee: every case carries a ``generation_id`` containing ``"fixture"``,
so ``validate_coherent_publish`` fails closed on the fixture-substring check for
any ``ui/`` output path — independent of fixture_mode or lineage. The substring
does not affect section rendering (lineage keys off generation_id *equality*,
not content), so coherent cases share one id and the MIXED case uses three
distinct fixture ids.

Coverage and the pre-empted (dead-by-routing) states are enumerated in
``docs/prd_history/PRD-179.md`` under REALIZABILITY.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from tests.dash_helpers import _macro_drivers, _market_map, _mm_symbol, _payload, _run

# A path that does not exist, so the macro-snapshot fallback yields {} and the
# macro tape renders "NO LIVE MACRO DATA" instead of loading the real snapshot.
_MISSING_SNAPSHOT = Path("/nonexistent/cuttingboard/preview_macro_snapshot.json")

_SUNDAY_PT_TS = "2026-04-12T17:00:00Z"  # Sunday in America/Los_Angeles
_WEEKDAY_TS = "2026-04-28T12:00:00Z"    # Tuesday — the dash_helpers default


@dataclass(frozen=True)
class SectionStateCase:
    """One renderable dashboard section state.

    name           short identifier (also the output filename stem)
    marker         substring that MUST appear in the rendered HTML
    payload/run    contract artifacts (built from dash_helpers)
    market_map     optional market_map artifact (None exercises MISSING lineage)
    render_kwargs  extra keyword args forwarded to render_dashboard_html
    fixture_mode   whether the render runs in demo/fixture mode
    extra_markers  additional substrings that MUST also appear — used when the
                   primary marker alone does not prove the case's intended branch
                   (e.g. a populated list whose heading renders even when empty)
    """

    name: str
    marker: str
    payload: dict
    run: dict
    market_map: dict | None = None
    render_kwargs: dict = field(default_factory=dict)
    fixture_mode: bool = False
    extra_markers: tuple[str, ...] = ()


def _stamp(*, payload: dict, run: dict, market_map: dict | None, gid: str, ts: str) -> None:
    """Align generation_ids and timestamps so lineage is COHERENT and non-stale.

    Used for every coherent case; the MIXED case stamps the three ids by hand.
    """
    payload["meta"]["generation_id"] = gid
    payload["meta"]["timestamp"] = ts
    run["generation_id"] = gid
    run["timestamp"] = ts
    if market_map is not None:
        market_map["generation_id"] = gid
        market_map["generated_at"] = ts


def _coherent(name: str, marker: str, *, ts: str = _WEEKDAY_TS, **kw) -> SectionStateCase:
    """Build a COHERENT-lineage case with one shared fixture generation_id."""
    payload = kw.pop("payload", None) or _payload(macro_drivers=_macro_drivers())
    run = kw.pop("run", None) or _run()
    market_map = kw.pop("market_map", None)
    if market_map is None and not kw.pop("_no_mm", False):
        market_map = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    _stamp(payload=payload, run=run, market_map=market_map, gid=f"fixture-{name}", ts=ts)
    return SectionStateCase(
        name=name,
        marker=marker,
        payload=payload,
        run=run,
        market_map=market_map,
        render_kwargs=kw.pop("render_kwargs", {}),
        fixture_mode=kw.pop("fixture_mode", False),
        extra_markers=kw.pop("extra_markers", ()),
    )


def section_state_cases() -> list[SectionStateCase]:
    cases: list[SectionStateCase] = []

    # 1. Coherence warning — three differing generation_ids → MIXED lineage.
    p = _payload(macro_drivers=_macro_drivers())
    r = _run()
    mm = _market_map({"SPY": _mm_symbol("SPY", grade="A")})
    p["meta"]["generation_id"] = "fixture-mixed-payload"
    r["generation_id"] = "fixture-mixed-run"
    mm["generation_id"] = "fixture-mixed-mm"
    cases.append(
        SectionStateCase(
            "coherence_mixed",
            "MIXED_ARTIFACTS",
            p,
            r,
            mm,
            # MIXED_ARTIFACTS is also the System State title under mixed artifacts,
            # so it alone would still pass if the coherence-warning banner stopped
            # rendering. Pin the warning block by its id (PR #20 review).
            extra_markers=('id="artifact-coherence"',),
        )
    )

    # 2. Sunday pre-market banner — coherent + SUNDAY_PREMARKET + Sunday-PT timestamp.
    sun = _payload(macro_drivers=_macro_drivers())
    sun["meta"]["session_type"] = "SUNDAY_PREMARKET"
    cases.append(
        _coherent(
            "sunday_premarket",
            "SUNDAY PRE-MARKET CONTEXT",
            ts=_SUNDAY_PT_TS,
            payload=sun,
        )
    )

    # 3. Session inactive — coherent + SUNDAY_PREMARKET + non-Sunday-PT timestamp
    #    (sunday_coherent false, inactive_session true).
    ina = _payload(macro_drivers=_macro_drivers())
    ina["meta"]["session_type"] = "SUNDAY_PREMARKET"
    cases.append(
        _coherent(
            "session_inactive",
            "SESSION INACTIVE",
            payload=ina,
            # SESSION INACTIVE renders in BOTH the trend-structure and candidate-
            # board branches, so the bare label could be satisfied by one section
            # if the other regressed. Pin each branch's inactive render with its
            # section-specific wrapper class (PR #20 review).
            extra_markers=('tape-no-data">SESSION INACTIVE', 'unavailable">SESSION INACTIVE'),
        )
    )

    # 4. Macro tape no live data — empty macro_drivers + missing snapshot fallback.
    cases.append(
        _coherent(
            "macro_tape_no_data",
            "NO LIVE MACRO DATA",
            payload=_payload(macro_drivers={}),
            render_kwargs={"macro_snapshot_path": _MISSING_SNAPSHOT},
        )
    )

    # 5/6/7. Red folder error / empty / expiring.
    cases.append(
        _coherent(
            "red_folder_error",
            "RED FOLDER UNAVAILABLE",
            render_kwargs={"red_folder": {"ok": False, "error": "schedule unavailable"}},
        )
    )
    cases.append(
        _coherent(
            "red_folder_empty",
            "No red-folder events in the next 48 hours.",
            render_kwargs={"red_folder": {"ok": True, "events": []}},
        )
    )
    cases.append(
        _coherent(
            "red_folder_expiring",
            "Red-folder schedule nearing expiry",
            # extra_markers pin the *populated* branch: the expiry banner renders
            # off the `expiring` flag alone, so without these the case would still
            # pass if the supplied CPI event stopped rendering (PR #20 review).
            extra_markers=("red-folder-event", "CPI"),
            render_kwargs={
                "red_folder": {
                    "ok": True,
                    "expiring": True,
                    "events": [
                        {"date": "2026-04-29", "time_et": "08:30", "name": "CPI", "type": "INFLATION"}
                    ],
                }
            },
        )
    )

    # 8. Trend structure awaiting/closed — coherent, zero usable rows. The
    #    snapshot carries NO generated_at on purpose: _trend_structure_source_health
    #    runs its 300s freshness gate only when generated_at is a non-empty string,
    #    so omitting it skips straight to the usable_count==0 -> AWAITING_DATA
    #    branch. This makes the case time-independent (no render-vs-import clock
    #    dependency); a stamped "now" would flip to STALE in a long-lived process.
    cases.append(
        _coherent(
            "trend_awaiting_data",
            "MARKET CLOSED &#8212; AWAITING INTRADAY DATA",
            render_kwargs={"trend_structure_snapshot": {"symbols": {}}},
        )
    )

    # 9. Trend structure no-data — coherent active session, no snapshot supplied.
    cases.append(
        _coherent("trend_no_data", "no trend structure data")
    )

    # 10. Lineage missing — market_map absent → MISSING lineage; drives the
    #     trend-structure and candidate-board UNAVAILABLE branches.
    miss_p = _payload(macro_drivers=_macro_drivers())
    miss_r = _run()
    miss_p["meta"]["generation_id"] = "fixture-missing"
    miss_r["generation_id"] = "fixture-missing"
    cases.append(
        SectionStateCase(
            "lineage_missing",
            "artifact_lineage_state=MISSING",
            miss_p,
            miss_r,
            market_map=None,
            # The lineage marker is emitted by the trend-structure block, so it
            # alone would still pass if the candidate-board missing-lineage render
            # broke. SOURCE_MISSING is the candidate-board-specific output, pinning
            # that this case actually covers the candidate board (PR #20 review).
            extra_markers=("SOURCE_MISSING",),
        )
    )

    # 11. Candidate board no candidates — coherent, empty symbols dict.
    cases.append(
        _coherent(
            "candidate_no_candidates",
            "NO_CANDIDATES",
            market_map=_market_map({}),
        )
    )

    # 12. Healthy baseline (positive control) — coherent high-grade card, no DEMO MODE.
    #     Marker is the card-specific element id, not the board heading: the heading
    #     renders for every board state (cards / no-candidates / unavailable), so it
    #     would not catch the A+ card being filtered out or ceasing to render. The
    #     card-SPY id is present iff the card actually rendered (absent in the
    #     no-candidates case), giving the positive control real teeth (PR #20 review).
    cases.append(
        _coherent(
            "healthy_baseline",
            "card-SPY",
            market_map=_market_map({"SPY": _mm_symbol("SPY", grade="A+")}),
        )
    )

    return cases


SECTION_STATE_CASES: list[SectionStateCase] = section_state_cases()
