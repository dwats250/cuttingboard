"""PRD-340 Slice 2 -- F3/F4: the BROWSER authority channel (ui/app.js), exercised
behaviorally in Node against a stubbed DOM (the `node` idiom of
tests/test_staleness_banner.py; FAILS loudly, never skips, if node is absent).

F3 (authority leak, fail-closed): admitAuthority() completes envelope freshness +
shape admission -- it parses valid_until, compares it to the viewer clock, and
rejects an expired / malformed / prior-session / absent envelope to the no-authority
state; and renderPrimaryTrade() shows the grant surface ONLY on an admitted PERMITTED
(TRADE_READY) posture, never on candidate presence alone.

F4 (functional/inert): renderNoTrade / renderWatchlist take the contract (the
derivePosture signature is derivePosture(contract)); NO_TRADE shows its no-trade
block, and the retired WATCHLIST posture maps onto STAY_FLAT-with-candidates.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
from datetime import datetime


from cuttingboard import config
from cuttingboard import effective_permission as ep_authority

REPO = pathlib.Path(__file__).resolve().parents[1]
_APP_JS = (REPO / "ui" / "app.js").read_text(encoding="utf-8")
_SESSION = "2026-06-12"


def _envelope(*, trade: bool, session: str = _SESSION) -> dict:
    ep = ep_authority.resolve_effective_permission(
        mode="live", outcome_is_trade=trade, system_halted=False, operator_locked=False,
        session_date=session, run_uid="b" * 32,
        posture_permission_line="Longs allowed." if trade else "No new trades permitted.",
        operator_lock_line=config.OPERATOR_LOCK_PERMISSION)
    return ep.to_envelope()


def _valid_until_ms(env: dict) -> int:
    return int(datetime.fromisoformat(env["valid_until"]).timestamp() * 1000)


_HARNESS = r"""
globalThis.__NOW__ = __NOW_MS__;
Date.now = function () { return globalThis.__NOW__; };
function _elem() {
  return { style: {}, textContent: '', innerHTML: '', className: '', dataset: {},
           addEventListener: function () {}, appendChild: function () {},
           closest: function () { return null; } };
}
var _els = {};
globalThis.document = {
  readyState: 'complete',
  getElementById: function (id) { if (!_els[id]) { _els[id] = _elem(); } return _els[id]; },
  createElement: function () { return _elem(); },
  addEventListener: function () {}
};
globalThis.localStorage = {
  _d: {}, getItem: function (k) { return this._d[k] || null; },
  setItem: function (k, v) { this._d[k] = v; }
};
globalThis.window = globalThis;
__APP_JS__
var contract = __CONTRACT__;
renderPrimaryTrade(contract);
renderNoTrade(contract);
renderWatchlist(contract);
console.log(JSON.stringify({
  posture: derivePosture(contract),
  primary: document.getElementById('primary-trade-block').style.display,
  no_trade: document.getElementById('no-trade-block').style.display,
  watchlist: document.getElementById('watchlist-block').style.display
}));
process.exit(0);
"""


def _run(contract: dict, now_ms: int) -> dict:
    node = shutil.which("node")
    # Fail loudly, never skip: the browser channel's fail-closed verdict is the
    # whole point of F3/F4, and CI's ubuntu image ships node.
    assert node is not None, "node is required to exercise the browser authority channel"
    script = (_HARNESS
              .replace("__NOW_MS__", str(int(now_ms)))
              .replace("__APP_JS__", _APP_JS)
              .replace("__CONTRACT__", json.dumps(contract)))
    proc = subprocess.run([node, "-"], input=script, capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, f"node harness failed: {proc.stderr}"
    return json.loads(proc.stdout.strip())


_CANDS = [{"symbol": "SPY", "direction": "LONG", "entry_mode": "DIRECT",
           "strategy_tag": "BULL_CALL_SPREAD", "risk_reward": 2.0}]


# --------------------------------------------------------------------- F3 freshness

def test_fresh_permitted_shows_primary_trade() -> None:
    env = _envelope(trade=True)
    contract = {"session_date": _SESSION, "effective_permission": env, "trade_candidates": _CANDS}
    out = _run(contract, _valid_until_ms(env) - 3_600_000)  # 1h BEFORE expiry
    assert out["posture"] == "TRADE_READY"
    assert out["primary"] == ""          # grant surface shown
    assert out["no_trade"] == "none" and out["watchlist"] == "none"


def test_expired_permitted_fails_closed_and_hides_primary_trade() -> None:
    env = _envelope(trade=True)
    contract = {"session_date": _SESSION, "effective_permission": env, "trade_candidates": _CANDS}
    out = _run(contract, _valid_until_ms(env) + 3_600_000)  # 1h AFTER expiry
    # F3: stale authority fails closed; the grant surface is hidden DESPITE candidates.
    assert out["posture"] == "UNAVAILABLE"
    assert out["primary"] == "none"


def test_malformed_valid_until_fails_closed() -> None:
    env = _envelope(trade=True)
    env["valid_until"] = "not-a-timestamp"
    contract = {"session_date": _SESSION, "effective_permission": env, "trade_candidates": _CANDS}
    out = _run(contract, _valid_until_ms(_envelope(trade=True)) - 3_600_000)
    assert out["posture"] == "UNAVAILABLE"
    assert out["primary"] == "none"


def test_prior_session_fails_closed() -> None:
    env = _envelope(trade=True, session=_SESSION)
    contract = {"session_date": "2026-06-13", "effective_permission": env, "trade_candidates": _CANDS}
    out = _run(contract, _valid_until_ms(env) - 3_600_000)
    assert out["posture"] == "UNAVAILABLE"
    assert out["primary"] == "none"


def test_absent_authority_fails_closed() -> None:
    contract = {"session_date": _SESSION, "trade_candidates": _CANDS}
    out = _run(contract, _valid_until_ms(_envelope(trade=True)) - 3_600_000)
    assert out["posture"] == "UNAVAILABLE"
    assert out["primary"] == "none"


# ------------------------------------------------- F2 forged/partial-schema envelopes

def test_partial_envelope_missing_canonical_fields_fails_closed() -> None:
    # A forged/partial envelope carrying only verdict + IDs + session + valid_until
    # (MISSING restriction_rank, authority_version, recovery_basis, permission_line,
    # decision_seq) must NOT admit as TRADE_READY -- the browser mirrors the canonical
    # closed-schema admission (effective_permission._valid_canonical).
    env = _envelope(trade=True)
    forged = {"verdict": "PERMITTED", "session_date": _SESSION,
              "decision_uid": env["decision_uid"], "run_uid": env["run_uid"],
              "valid_until": env["valid_until"]}
    contract = {"session_date": _SESSION, "effective_permission": forged, "trade_candidates": _CANDS}
    out = _run(contract, _valid_until_ms(env) - 3_600_000)
    assert out["posture"] == "UNAVAILABLE"
    assert out["primary"] == "none"


def test_cross_field_mismatch_envelope_fails_closed() -> None:
    # A full-key envelope whose cross-fields are inconsistent (authority_version does
    # not equal [session_date, decision_seq, restriction_rank]) fails closed.
    env = _envelope(trade=True)
    env["authority_version"] = [_SESSION, 9, 9]  # != [session, seq=1, rank=0]
    contract = {"session_date": _SESSION, "effective_permission": env, "trade_candidates": _CANDS}
    out = _run(contract, _valid_until_ms(_envelope(trade=True)) - 3_600_000)
    assert out["posture"] == "UNAVAILABLE"
    assert out["primary"] == "none"


def test_extra_key_envelope_fails_closed() -> None:
    # A NON-closed envelope with an extra key is rejected (exact canonical key set).
    env = _envelope(trade=True)
    env["injected"] = "surprise"
    contract = {"session_date": _SESSION, "effective_permission": env, "trade_candidates": _CANDS}
    out = _run(contract, _valid_until_ms(_envelope(trade=True)) - 3_600_000)
    assert out["posture"] == "UNAVAILABLE"
    assert out["primary"] == "none"


# ------------------------------------------------------- F4 posture-mapped blocks

def test_no_trade_posture_shows_no_trade_block() -> None:
    env = _envelope(trade=False)
    contract = {"session_date": _SESSION, "effective_permission": env, "trade_candidates": []}
    out = _run(contract, _valid_until_ms(env) - 3_600_000)
    assert out["posture"] == "STAY_FLAT"
    assert out["no_trade"] == "" and out["primary"] == "none" and out["watchlist"] == "none"


def test_stay_flat_with_candidates_shows_watchlist_not_grant() -> None:
    env = _envelope(trade=False)
    contract = {"session_date": _SESSION, "effective_permission": env, "trade_candidates": _CANDS}
    out = _run(contract, _valid_until_ms(env) - 3_600_000)
    # STAY_FLAT posture + candidates => watchlist evidence, never a primary-trade grant.
    assert out["posture"] == "STAY_FLAT"
    assert out["watchlist"] == "" and out["primary"] == "none" and out["no_trade"] == "none"
