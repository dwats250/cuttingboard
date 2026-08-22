"""PRD-309 GEX-2 free board card — pure loader/model/fragment guards (R2-R16).

Each test is the red mutation for a named requirement: removing the guard it
exercises turns the test red (PRD-198 invariant 4). Integration guards R1, R7,
R17-R20 live in tests/test_dashboard_renderer.py.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cuttingboard.delivery import gex_card

# Fixed render clock ~1 minute after the sample capture time (fresh).
NOW = datetime(2026, 8, 20, 20, 43, 0, tzinfo=timezone.utc)

_DATA_DELAY = "~15 min delayed (REPORTED; Cboe delayed_quotes posture)"


def _base() -> dict:
    """A fresh, in-domain snapshot (mirrors the live logs/gex_snapshot.json sample)."""
    return {
        "schema_version": 1,
        "source": "cboe_delayed_quotes",
        "data_delay": _DATA_DELAY,
        "gex_total_1pct_usd": -58358882895.27673,
        "spot": {"value": 7641.1602, "basis": "SPX cash index level"},
        "fetched_at_utc": "2026-08-20T20:42:28.098947+00:00",
        "call_wall": {"strike": 8000.0, "gex_1pct_usd": 1.0, "reason": None},
        "put_wall": {"strike": 8000.0, "gex_1pct_usd": -1.0, "reason": None},
        "dominant_net_gamma": {"strike": 7640.0, "gex_1pct_usd": -1.0, "reason": None},
        "zero_dte": {"share": 0.07635226668688595, "reason": None},
    }


def _frag(snapshot, now=NOW) -> str:
    return gex_card.render_fragment(snapshot, now=now)


def test_valid_baseline_renders():
    assert _frag(_base()) != ""


# --- R2: malformed / non-dict -> suppressed; loader never raises ---
def test_gex_malformed_suppressed(tmp_path):
    # mutation: broaden loader to accept, or to raise.
    p = tmp_path / "gex_snapshot.json"
    p.write_text("{not valid json", encoding="utf-8")
    assert gex_card.load_gex_snapshot(p) is None  # never raises
    p.write_text("[1, 2, 3]", encoding="utf-8")  # valid JSON, not a dict
    assert gex_card.load_gex_snapshot(p) is None
    assert gex_card.load_gex_snapshot(tmp_path / "absent.json") is None
    assert _frag("not a dict") == ""
    assert _frag(None) == ""


def test_gex_loader_reads_valid(tmp_path):
    import json

    p = tmp_path / "gex_snapshot.json"
    p.write_text(json.dumps(_base()), encoding="utf-8")
    assert isinstance(gex_card.load_gex_snapshot(p), dict)


# --- R3: schema identity (bool-first == 1; exact source/data_delay) ---
def test_gex_schema_identity():
    # mutation: drop the bool-first check (True==1 leaks) / drop source identity.
    s = _base()
    s["schema_version"] = True  # bool must NOT satisfy == 1
    assert _frag(s) == ""
    s = _base()
    s["schema_version"] = 2
    assert _frag(s) == ""
    s = _base()
    s["source"] = "polygon"
    assert _frag(s) == ""
    s = _base()
    s["data_delay"] = "realtime"
    assert _frag(s) == ""


# --- R4: required key missing / wrong type -> suppressed ---
def test_gex_missing_key_suppressed():
    # mutation: skip a required-field validation.
    for key in ("gex_total_1pct_usd", "spot", "fetched_at_utc", "dominant_net_gamma"):
        s = _base()
        del s[key]
        assert _frag(s) == "", key
    s = _base()
    s["spot"] = "not a dict"
    assert _frag(s) == ""


# --- R5: numeric domain (finite, non-bool; spot>0; share in [0,1]) ---
def test_gex_numeric_domain():
    # mutation: remove the bool/finite/range guard.
    s = _base()
    s["gex_total_1pct_usd"] = True  # bool is not a real number
    assert _frag(s) == ""
    s = _base()
    s["gex_total_1pct_usd"] = float("nan")
    assert _frag(s) == ""
    s = _base()
    s["spot"] = {"value": 0.0}  # not > 0
    assert _frag(s) == ""
    s = _base()
    s["spot"] = {"value": -5.0}
    assert _frag(s) == ""
    s = _base()
    s["zero_dte"] = {"share": 1.5, "reason": None}  # out of [0,1]
    assert _frag(s) == ""


# --- R6: staleness vs injected now -> suppressed ---
def test_gex_stale_suppressed():
    # mutation: remove the staleness check.
    fresh = _frag(_base(), NOW)
    assert fresh != ""
    stale_now = NOW + timedelta(hours=25)  # > STALE_MAX (24h)
    assert _frag(_base(), stale_now) == ""
    edge = NOW + timedelta(hours=23)  # still within 24h
    assert _frag(_base(), edge) != ""


# --- R7: valid artifact -> exact values rendered ---
def test_gex_valid_render_values():
    # mutation: read a wrong key / wrong scale.
    out = _frag(_base())
    assert "-$58.4B" in out  # net /1e9, one decimal, signed
    assert "7640" in out and "8000" in out  # strikes
    assert "7.6%" in out  # 0DTE share*100
    assert "16:42 ET" in out  # absolute ET capture time


# --- R8: distance = (strike/spot - 1)*100, correct sign + magnitude ---
def test_gex_distance_math():
    # mutation: flip the sign / drop the -1.
    out = _frag(_base())
    assert "-0.02%" in out  # dominant 7640 below spot 7641.16
    assert "+4.70%" in out  # walls 8000 above spot


# --- R9: dominant anchor null -> WHOLE card suppressed (Q6) ---
def test_gex_dominant_null_suppressed():
    # mutation: render the card without the anchor.
    s = _base()
    s["dominant_net_gamma"] = {"strike": None, "gex_1pct_usd": None, "reason": "all_net_gamma_zero"}
    assert _frag(s) == ""


# --- R10: call/put/0DTE typed-unavailable -> that row omitted only ---
def test_gex_row_typed_unavailable():
    # mutation: render null as "None"/0/"-", or suppress whole card.
    s = _base()
    s["call_wall"] = {"strike": None, "gex_1pct_usd": None, "reason": "no_eligible_calls"}
    out = _frag(s)
    assert out != "" and "Call wall" not in out and "Dominant" in out
    assert "None" not in out
    s = _base()
    s["put_wall"] = {"strike": None, "gex_1pct_usd": None, "reason": "no_nonzero_put_gex"}
    out = _frag(s)
    assert out != "" and "Put wall" not in out
    s = _base()
    s["zero_dte"] = {"share": None, "reason": "zero_abs_gex_denominator"}
    out = _frag(s)
    assert out != "" and "0DTE" not in out


# --- R11: honest zero (share==0.0, reason None) -> 0.0% shown ---
def test_gex_zero_dte_honest_zero():
    # mutation: treat 0.0 as unavailable and omit.
    s = _base()
    s["zero_dte"] = {"share": 0.0, "reason": None}
    out = _frag(s)
    assert "0.0%" in out


# --- R12: freshness from fetched_at_utc; absolute ET; no relative age / session ---
def test_gex_freshness_source_and_wording():
    # mutation: bind on feed_timestamp_utc / add a session gate / print a relative age.
    s = _base()
    s["feed_timestamp_utc"] = "1999-01-01T00:00:00+00:00"  # would be ancient if used
    s["is_market_open"] = False
    out = _frag(s)  # freshness must ignore feed clock / session and use fetched_at_utc
    assert out != ""
    assert "16:42 ET" in out
    assert "ago" not in out.lower()
    # A stale fetched_at_utc DOES suppress (proves fetched clock is the source).
    s2 = _base()
    s2["fetched_at_utc"] = "2026-08-01T00:00:00+00:00"
    assert _frag(s2, NOW) == ""


# --- R13: no forbidden vocabulary ---
def test_gex_no_forbidden_vocabulary():
    # mutation: add any pin/magnet/support/regime/short-gamma label.
    out = _frag(_base()).lower()
    for token in ("pin", "magnet", "support", "resistance", "short gamma",
                  "long gamma", "regime", "tracks spot", "at spot", "max pain",
                  "dealers are short"):
        assert token not in out, token


# --- R14: sign-assumption footnote present; net not asserted "short gamma" ---
def test_gex_sign_footnote_present():
    # mutation: drop the footnote / assert "short gamma".
    out = _frag(_base())
    assert "not measured" in out
    assert "*" in out
    assert "short gamma" not in out.lower()


# --- R15: reason/value-pair coherence (unknown token / contradiction -> suppress) ---
def test_gex_reason_pair_coherence():
    # mutation: accept an unknown reason token / a contradictory pair.
    s = _base()
    s["call_wall"] = {"strike": None, "gex_1pct_usd": None, "reason": "made_up_token"}
    assert _frag(s) == ""  # unknown reason -> whole card invalid
    s = _base()
    s["dominant_net_gamma"] = {"strike": 7640.0, "gex_1pct_usd": -1.0, "reason": "all_net_gamma_zero"}
    assert _frag(s) == ""  # contradictory: strike AND reason both present
    s = _base()
    s["zero_dte"] = {"share": 0.5, "reason": "zero_abs_gex_denominator"}
    assert _frag(s) == ""  # contradictory 0DTE pair


# --- R16: timestamp domain (naive/malformed/future -> suppress) ---
def test_gex_timestamp_domain():
    # mutation: accept a naive or future timestamp.
    s = _base()
    s["fetched_at_utc"] = "2026-08-20T20:42:28.098947"  # naive
    assert _frag(s) == ""
    s = _base()
    s["fetched_at_utc"] = "not-a-timestamp"
    assert _frag(s) == ""
    s = _base()
    s["fetched_at_utc"] = "2026-08-20T21:00:00+00:00"  # ~17 min in the future vs NOW
    assert _frag(s) == ""
