"""Render the 15 binding production/state specimens from EXACT current main.

The reusable ``validate`` catalog renders from the working tree, which on this
experiment branch is forked at ``044602770f745e322dc47a88e9bd342dc0955ce7``
(pre PRD-315).  PRD-315 relocated the ``candidate-board`` block above
``alert-watchlist``; it is a pure vertical DOM move and touches no Opportunity
markup, no Opportunity CSS, and no horizontal geometry.  For the Opportunity
125% prototype the binding fixtures must nonetheless originate from EXACT
current main (``origin/main``), so this builder loads the current-main renderer
directly out of git -- without mutating the working tree -- and re-expresses the
lab's authority-order contract in its now-canonical PRD-315 form.

Only ``cuttingboard/delivery/dashboard_renderer.py`` differs between the forked
base and current main, so the current-main renderer loaded here executes against
the byte-identical remainder of the working-tree ``cuttingboard`` package and
reproduces exact current-main output.  The builder writes only beneath this
experiment.  The historical 0446027 catalog and the PRD-315 before/after report
are left untouched.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import types
from pathlib import Path

LAB_DIR = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent
REPO_ROOT = LAB_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(FIXTURES_DIR) not in sys.path:
    sys.path.insert(0, str(FIXTURES_DIR))
sys.dont_write_bytecode = True

import build_fixtures as base  # noqa: E402  (path set above)

CURRENTMAIN_DIR = FIXTURES_DIR / "currentmain"
CURRENTMAIN_CATALOG = FIXTURES_DIR / "currentmain-catalog.json"
RENDERER_REL = "cuttingboard/delivery/dashboard_renderer.py"

# Current main's tracked top-level authority order.  PRD-315 moved candidate
# from "after trend" to "immediately after opportunity" (rendered just before
# alert-watchlist, which precedes gex/movement/macro/redFolder/trend).
CURRENTMAIN_ORDER = [
    "marketState", "systemState", "opportunity", "candidate", "gex",
    "movement", "macro", "redFolder", "trend", "runDelta", "scoreboard",
]

# The 15 binding production/state fixtures (the core states; content-pressure
# and PRD-314 calibration specimens are out of scope for this prototype).
BINDING_IDS = tuple(base.CORE_IDS)


def _resolve_sha() -> str:
    sha = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "origin/main"],
        text=True,
    ).strip()
    if len(sha) != 40:
        raise RuntimeError(f"unexpected origin/main sha: {sha!r}")
    return sha


def _load_currentmain_renderer(sha: str):
    """Load the current-main renderer straight from git as an isolated module.

    Absolute imports (``from cuttingboard... import ...``) resolve against the
    working-tree package, which is byte-identical to current main for every file
    except the renderer itself -- so this is exact current-main behavior.
    """
    src = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "show", f"{sha}:{RENDERER_REL}"]
    )
    module = types.ModuleType("cuttingboard.delivery.dashboard_renderer_currentmain")
    module.__file__ = f"<git:{sha}:{RENDERER_REL}>"
    module.__package__ = "cuttingboard.delivery"
    code = compile(src, f"currentmain::{RENDERER_REL}", "exec")
    exec(code, module.__dict__)
    render = module.render_dashboard_html
    if not callable(render):
        raise RuntimeError("current-main render_dashboard_html not callable")
    return render


def _assert_prd315_order(html: str, fixture_id: str) -> None:
    """Fail loud (PRD-198 §1) unless this really is PRD-315 content."""
    cand = html.find('id="candidate-board"')
    alert = html.find('id="alert-watchlist"')
    opp = html.find('id="opportunity-survival"')
    if cand == -1:
        raise RuntimeError(f"{fixture_id}: candidate-board absent from render")
    if opp != -1 and not (opp < cand):
        raise RuntimeError(
            f"{fixture_id}: candidate-board must follow opportunity-survival"
        )
    # candidate-board must precede alert-watchlist when the latter is present.
    if alert != -1 and not (cand < alert):
        raise RuntimeError(
            f"{fixture_id}: PRD-315 order violated -- candidate-board must "
            f"precede alert-watchlist (candidate={cand}, alert={alert})"
        )


def _write_if_changed(path: Path, data: bytes) -> None:
    if path.exists() and path.read_bytes() == data:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def build() -> dict:
    sha = _resolve_sha()
    currentmain_render = _load_currentmain_renderer(sha)
    # Swap the renderer the shared builder calls; reuse its carriers + contracts.
    base.render_dashboard_html = currentmain_render  # type: ignore[attr-defined]

    inputs = base._core_inputs()
    manifest: dict[str, dict] = {}
    fixtures: list[dict] = []
    for fixture_id in sorted(BINDING_IDS):
        html = base._render(inputs[fixture_id])
        _assert_prd315_order(html, fixture_id)
        encoded = html.encode("utf-8")
        _write_if_changed(CURRENTMAIN_DIR / f"{fixture_id}.html", encoded)
        manifest[fixture_id] = {
            "bytes": len(encoded),
            "sha256": hashlib.sha256(encoded).hexdigest(),
        }
        # Reuse the shared per-fixture contract, then repoint its file and adopt
        # the current-main authority order.  This keeps required/forbidden text,
        # presence, opportunity values, candidate truth, and critical keys in
        # exact lock-step with the reusable validate catalog.
        contract = base._contract(
            fixture_id,
            f"{fixture_id}.html",
            groups=(["core"]),
            covers=[fixture_id],
            matrix="representative",
            required=_required_for(fixture_id),
            forbidden=_forbidden_for(fixture_id),
            candidate=_candidate_for(fixture_id),
            opportunity=_opportunity_for(fixture_id),
        )
        contract["file"] = f"currentmain/{fixture_id}.html"
        contract["sourceMode"] = "currentmain-renderer-fixtures"
        contract["expected"]["order"] = list(CURRENTMAIN_ORDER)
        fixtures.append(contract)

    fixtures.sort(key=lambda item: item["id"])
    catalog = {
        "schemaVersion": 1,
        "baseline": sha,
        "baselineSha": sha,
        "sourceIdentifier": f"cuttingboard@{sha}",
        "sourceMode": "currentmain-renderer-fixtures",
        "fixedNow": base.FIXED_TS,
        "provenance": {
            "forkedBase": base.BASELINE_SHA,
            "currentMain": sha,
            "prd315": "candidate-board relocated above alert-watchlist (move-only)",
            "note": (
                "Rendered from origin/main via git show + importlib; working "
                "tree not modified. Only dashboard_renderer.py differs between "
                "forkedBase and currentMain."
            ),
        },
        "viewports": [{"width": w, "height": h} for w, h in base.VIEWPORTS],
        "scales": base.SCALES,
        "fixtureManifest": manifest,
        "defaults": {
            "selectors": _selectors(),
            "criticalKeys": ["marketState", "systemState", "candidate"],
            "contextKeys": ["gex", "movement", "macro", "redFolder", "trend"],
            "surfaceKeys": [
                "marketState", "systemState", "opportunity", "candidate", "gex",
                "movement", "macro", "redFolder", "trend", "runDelta", "scoreboard",
            ],
            "order": list(CURRENTMAIN_ORDER),
            "candidateLevelLabels": ["IN →", "LEVEL"],
            "candidateInvalidationLabels": ["OUT →", "INVALIDATION"],
        },
        "fixtures": fixtures,
    }
    catalog_text = json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _write_if_changed(CURRENTMAIN_CATALOG, catalog_text.encode("utf-8"))
    return {
        "currentMainSha": sha,
        "fixtureCount": len(fixtures),
        "catalogSha256": hashlib.sha256(catalog_text.encode("utf-8")).hexdigest(),
        "files": sorted(p.name for p in CURRENTMAIN_DIR.glob("*.html")),
    }


# --- per-fixture inputs to base._contract, mirroring build_fixtures._catalog ---

def _candidate_for(fixture_id: str) -> dict:
    if fixture_id in {"state-unavailable", "candidate-carrier-unavailable",
                      "no-candidate", "inactive-session"}:
        return {"minimumCards": 0, "symbols": []}
    if fixture_id == "multiple-candidates":
        return {"minimumCards": 3, "symbols": ["SPY", "QQQ", "GDX"]}
    if fixture_id == "opportunity-suppressed":
        return {"minimumCards": 1, "symbols": ["SPY"]}
    return {"minimumCards": 1, "symbols": ["SPY"], "grade": "B", "setupState": "DEVELOPING"}


def _opportunity_for(fixture_id: str):
    if fixture_id == "opportunity-suppressed":
        return 0
    if fixture_id == "qualified-zero-b-candidate":
        return 13
    return 23


def _required_for(fixture_id: str) -> list[str]:
    table = {
        "halt": ["SYSTEM HALT", "HALT: execution carrier unavailable"],
        "operator-lock": ["OPERATOR LOCK", "OBSERVE ONLY"],
        "state-unavailable": ["MIXED_ARTIFACTS", "STATE UNAVAILABLE"],
        "candidate-carrier-unavailable": ["SOURCE_MISSING"],
        "gex-unavailable": ["POSITIONING", "unavailable"],
        "movement-unavailable": ["PARTICIPATION", "unavailable"],
        "red-folder-event": ["CPI (July)", "1 events in 48h"],
        "healthy-empty-red-folder": ["no events in 48h"],
        "no-candidate": ["NO_CANDIDATES"],
        "multiple-candidates": ["card-SPY", "card-QQQ", "card-GDX"],
        "qualified-zero-b-candidate": ["SURFACED", "WATCHLIST", "card-SPY"],
        "inactive-session": ["SESSION INACTIVE"],
        "normal": ["SURFACED", "WATCHLIST", "B DEVELOPING",
                   "Cboe ~15m delayed", "positioning is not measured"],
    }
    return table.get(fixture_id, [])


def _forbidden_for(fixture_id: str) -> list[str]:
    if fixture_id == "operator-lock":
        return ["TRADE PERMITTED", "IF NOW"]
    return []


def _selectors() -> dict:
    return {
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


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
