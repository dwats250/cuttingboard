"""PRD-250: guardrails for the client-side staleness banner.

The banner surfaces the published board's page-age at VIEW time. Two failure
surfaces are pinned here:

1. The SERVER contract — what the renderer must emit for the browser to compute a
   correct verdict: a machine-readable UTC timestamp on ``#cb-updated``, the
   threshold and the server-supplied "was a refresh due" flag on
   ``#staleness-banner``, the banner as a preceding sibling ABOVE ``#system-state``,
   and — load-bearing — NO verdict baked server-side (the div ships empty/hidden).

2. The CLIENT behaviour — the fresh/old/closed boundary, which lives in JS because
   the verdict must be viewer-clock-relative. It is exercised by executing the exact
   emitted script in Node against a stubbed DOM (no JS-in-tree runtime dep beyond
   the `node` binary, which CI's ubuntu image ships; the test FAILS loudly, never
   skips, if node is absent — per the hardening invariants).

Fixtures are owned here. Distinct vocabulary from the input-source ``STALE`` tags
(``_compute_timestamp_freshness``) is enforced so the two never collide.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone

import pytest

from cuttingboard.delivery.dashboard_renderer import (
    BOARD_STALE_AFTER_SECONDS,
    _STALENESS_BANNER_JS,
    render_dashboard_html,
)
from tests.dash_helpers import _macro_drivers, _market_map, _mm_symbol, _payload, _run

_RUN_TS = "2026-04-28T12:00:00Z"  # Tuesday (non-Sunday) — matches dash_helpers fixtures
_RUN_TS_MS = int(datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc).timestamp() * 1000)


def _render(*, session_type: str | None = None) -> str:
    payload = _payload(macro_drivers=_macro_drivers())
    if session_type is not None:
        payload["meta"]["session_type"] = session_type
    market_map = _market_map({"SPY": _mm_symbol()})
    return render_dashboard_html(payload, _run(), market_map=market_map)


def _banner_open_tag(html: str) -> str:
    m = re.search(r'<div class="block" id="staleness-banner"[^>]*>', html)
    assert m, "staleness-banner element not emitted"
    return m.group(0)


def _banner_inner(html: str) -> str:
    """Text between the banner element's open and close tags."""
    after_open = html.split('id="staleness-banner"', 1)[1].split(">", 1)[1]
    return after_open.split("</div>", 1)[0]


# ---------------------------------------------------------------------------
# Server contract
# ---------------------------------------------------------------------------

def test_updated_timestamp_emitted_machine_readable() -> None:
    """#cb-updated carries a parseable ISO-8601 UTC value == the run timestamp."""
    html = _render()
    m = re.search(r'id="cb-updated" data-updated-utc="([^"]*)"', html)
    assert m, "machine-readable data-updated-utc not emitted on #cb-updated"
    iso = m.group(1)
    assert iso, "data-updated-utc is empty for a run that has a timestamp"
    parsed = datetime.fromisoformat(iso)
    assert parsed.tzinfo is not None, f"emitted timestamp is not tz-aware: {iso!r}"
    assert int(parsed.timestamp() * 1000) == _RUN_TS_MS


def test_banner_verdict_not_baked_server_side() -> None:
    """Load-bearing: the server ships an EMPTY, hidden banner — no verdict baked.

    If a future change rendered the age/verdict at publish time, a frozen board
    would freeze its own 'fresh' label. This test fails the moment any verdict
    text leaks into the server-emitted element.
    """
    html = _render()
    assert "hidden" in _banner_open_tag(html), "banner must ship hidden"
    assert _banner_inner(html) == "", (
        f"banner must ship EMPTY (verdict is client-side); got {_banner_inner(html)!r}"
    )


def test_banner_is_preceding_sibling_above_system_state() -> None:
    html = _render()
    assert html.index('id="staleness-banner"') < html.index('id="system-state"')
    # Not woven INTO the decision-shaped #system-state block: the banner closes
    # before that block opens.
    banner_region = html.split('id="staleness-banner"', 1)[1]
    assert banner_region.index("</div>") < banner_region.index('id="system-state"')


def test_threshold_attribute_matches_constant() -> None:
    html = _render()
    m = re.search(r'data-board-stale-after-s="(\d+)"', _banner_open_tag(html))
    assert m, "threshold attribute not emitted"
    assert int(m.group(1)) == BOARD_STALE_AFTER_SECONDS == 90 * 60


def test_valid_until_baked_from_admitted_ep_only() -> None:
    """PRD-342 / Sol N1+N2: `data-valid-until` carries the ADMITTED valid_until (via
    admit_ep, called WITHOUT `now`) — an expired-but-canonical envelope keeps it,
    while a malformed/prior-session/absent envelope fail-closes to "" and never leaks
    the raw envelope's timestamp."""
    from cuttingboard import effective_permission as _ep
    sess = "2026-04-28"
    env = _ep.resolve_effective_permission(
        mode="live", outcome_is_trade=False, system_halted=False, operator_locked=False,
        session_date=sess, run_uid="a" * 32,
        posture_permission_line="No new trades permitted.",
        operator_lock_line="No new trades permitted — operator cannot monitor.").to_envelope()

    def _vu(run: dict) -> str:
        html = render_dashboard_html(_payload(macro_drivers=_macro_drivers()), run,
                                     market_map=_market_map({"SPY": _mm_symbol()}))
        m = re.search(r'data-valid-until="([^"]*)"', _banner_open_tag(html))
        assert m, "data-valid-until attribute not emitted"
        return m.group(1)

    # admitted (canonical, current session) -> the envelope's valid_until
    assert _vu({**_run(), "session_date": sess, "effective_permission": env}) == env["valid_until"]
    # expired-but-canonical survives admission (admit_ep called without `now`) — Sol N2
    past = {**env, "valid_until": "2020-01-01T00:00:00+00:00"}
    assert _vu({**_run(), "session_date": sess, "effective_permission": past}) == "2020-01-01T00:00:00+00:00"
    # malformed with a PARSEABLE valid_until -> rejected -> "" (no raw leak) — Sol N1
    bad = {**env, "unexpected_extra_key": 1}
    assert _vu({**_run(), "session_date": sess, "effective_permission": bad}) == ""
    # prior-session canonical envelope -> rejected -> "" (session mismatch)
    prior = {**_run(), "session_date": "2026-04-29", "effective_permission": env}
    assert _vu(prior) == ""
    # absent EP -> "" (fail-closed, neutral banner)
    assert _vu({k: v for k, v in _run().items() if k != "effective_permission"}) == ""


@pytest.mark.parametrize(
    "session_type, expected",
    [(None, "false"), ("SUNDAY_PREMARKET", "true")],
)
def test_session_flag_reflects_refresh_due(session_type: str | None, expected: str) -> None:
    """`data-session-inactive` is the server-supplied 'was a refresh due' signal:
    false in an active session (refresh due), true when inactive (none due)."""
    html = _render(session_type=session_type)
    m = re.search(r'data-session-inactive="(true|false)"', _banner_open_tag(html))
    assert m and m.group(1) == expected, (
        f"session flag for session_type={session_type!r} should be {expected!r}"
    )


def test_banner_vocabulary_informs_never_instructs() -> None:
    """The banner states an age/condition and never directs an action, and its
    wording stays distinct from the input-source STALE tags (carry-ins A + C)."""
    js = _STALENESS_BANNER_JS
    # Informs: page-age framing is present.
    assert "OLD" in js and "LAST UPDATE" in js
    # Distinct from _compute_timestamp_freshness input tags: no bare "STALE".
    assert "STALE" not in js, "banner must not reuse the input-source 'STALE' label"
    # Never instructs: no imperative action verb in the script (word-boundary so
    # identifiers like 'inactive' are not false hits).
    banned = r"\b(trade|buy|sell|hold|wait|avoid|should|exit|enter|don't|do not)\b"
    hit = re.search(banned, js, re.IGNORECASE)
    assert hit is None, f"banner drifts toward instruction: {hit and hit.group(0)!r}"


# ---------------------------------------------------------------------------
# Client behaviour — the fresh/old/closed boundary, executed in Node
# ---------------------------------------------------------------------------

_HARNESS = """
globalThis.__NOW__ = __NOW_MS__;
Date.now = function () { return globalThis.__NOW__; };
var banner = {
  hidden: true, textContent: "", style: {},
  _a: { "data-session-inactive": "__INACTIVE__", "data-board-stale-after-s": "__THRESH__",
        "data-valid-until": "__VALID_UNTIL__" },
  getAttribute: function (k) { return this._a[k]; }
};
var updatedEl = {
  _a: { "data-updated-utc": "__ISO__" },
  getAttribute: function (k) { return this._a[k]; }
};
globalThis.document = {
  readyState: "complete",
  getElementById: function (id) {
    return id === "staleness-banner" ? banner : (id === "cb-updated" ? updatedEl : null);
  },
  addEventListener: function () {}
};
__BANNER_JS__
console.log(JSON.stringify({ hidden: banner.hidden, text: banner.textContent }));
// PRD-334 R1: the banner JS now schedules a setInterval to re-evaluate page age
// on the viewer's clock. In this one-shot node harness the interval would keep the
// process alive forever; exit as soon as the single verdict has been read.
process.exit(0);
"""


def _run_client(*, age_seconds: float, inactive: bool, iso: str = _RUN_TS,
                valid_until: str = "") -> dict:
    node = shutil.which("node")
    # Fail loudly rather than skip: the client verdict is the whole point of the
    # feature, and CI's ubuntu image ships node.
    assert node is not None, "node is required to exercise the client-side banner verdict"
    now_ms = _RUN_TS_MS + int(age_seconds * 1000)
    script = (
        _HARNESS
        .replace("__NOW_MS__", str(now_ms))
        .replace("__INACTIVE__", "true" if inactive else "false")
        .replace("__THRESH__", str(BOARD_STALE_AFTER_SECONDS))
        .replace("__ISO__", iso)
        .replace("__VALID_UNTIL__", valid_until)
        .replace("__BANNER_JS__", _STALENESS_BANNER_JS)
    )
    proc = subprocess.run(
        [node, "-"],
        input=script, capture_output=True, text=True, timeout=30,
    )
    assert proc.returncode == 0, f"node harness failed: {proc.stderr}"
    return json.loads(proc.stdout.strip())


def test_client_fresh_board_stays_hidden() -> None:
    out = _run_client(age_seconds=BOARD_STALE_AFTER_SECONDS - 10, inactive=False)
    assert out["hidden"] is True, f"fresh board should show no banner: {out}"


_FUTURE_VU = "2026-04-29T08:00:00Z"   # after any aged `now` in these fixtures -> not expired
_PAST_VU = "2026-04-28T12:00:00Z"     # == run ts, before an aged `now` -> expired


def test_client_aged_valid_decision_is_neutral() -> None:
    """PRD-342: an aged board whose admitted decision is still within valid_until
    reads as a neutral DECISION age, never the OLD/STALE warning."""
    out = _run_client(age_seconds=BOARD_STALE_AFTER_SECONDS + 10, inactive=False,
                      valid_until=_FUTURE_VU)
    assert out["hidden"] is False
    assert "DECISION" in out["text"]
    assert "OLD" not in out["text"] and "STALE" not in out["text"]


def test_client_expired_decision_flags_board_old() -> None:
    """PRD-342: viewer clock past the ADMITTED valid_until -> genuine expiry keeps
    the existing OLD warning."""
    out = _run_client(age_seconds=BOARD_STALE_AFTER_SECONDS + 10, inactive=False,
                      valid_until=_PAST_VU)
    assert out["hidden"] is False
    assert "OLD" in out["text"] and "BOARD" in out["text"]
    # informs the age, never instructs
    assert "trade" not in out["text"].lower()


def test_client_aged_absent_valid_until_never_warns() -> None:
    """PRD-342 (owner ruling 1 / Sol N1): with no admitted valid_until (fail-closed
    authority), the banner shows the neutral DECISION age and NEVER fabricates an
    expiry warning (no secondary validity clock)."""
    out = _run_client(age_seconds=BOARD_STALE_AFTER_SECONDS + 10, inactive=False,
                      valid_until="")
    assert out["hidden"] is False
    assert "DECISION" in out["text"]
    assert "OLD" not in out["text"]


def test_client_inactive_session_is_neutral_not_old() -> None:
    """Off-hours (no refresh due): a neutral last-update notice, never an OLD alarm."""
    out = _run_client(age_seconds=100_000, inactive=True)
    assert out["hidden"] is False
    assert "LAST UPDATE" in out["text"] and "AGO" in out["text"]
    assert "OLD" not in out["text"], "inactive session must not raise the OLD alarm"


def test_client_unparseable_timestamp_shows_unavailable() -> None:
    out = _run_client(age_seconds=0, inactive=False, iso="not-a-timestamp")
    assert out["hidden"] is False
    assert "UNAVAILABLE" in out["text"]
