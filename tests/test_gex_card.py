"""PRD-309 GEX-2 free board card — pure loader/model/fragment guards (R2-R16).

Each test is the red mutation for a named requirement: removing the guard it
exercises turns the test red (PRD-198 invariant 4). Integration guards R1, R7,
R17-R20 live in tests/test_dashboard_renderer.py.
"""

from __future__ import annotations

import math
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


# --- GEX-4 helpers: build a core snapshot made coherent with a per-strike carrier
def _argmax_low(vals):
    best = max(vals)
    return next(i for i, v in enumerate(vals) if v == best)


def _coherent(strike, call, put, *, spot=7747.71, reason=None, **overrides):
    """A fresh, in-domain snapshot whose core total and anchors are derived from
    the given carrier arrays, so the carrier reconciles by construction. Pass
    ``reason`` for a typed-unavailable carrier; pass overrides to tamper."""
    net = [c - p for c, p in zip(call, put)]

    def wall(mag, val, token):
        if max(mag) == 0.0:
            return {"strike": None, "gex_1pct_usd": None, "reason": token}
        i = _argmax_low(mag)
        return {"strike": strike[i], "gex_1pct_usd": val[i], "reason": None}

    snap = {
        "schema_version": 1,
        "source": "cboe_delayed_quotes",
        "data_delay": _DATA_DELAY,
        "gex_total_1pct_usd": math.fsum(v for c, p in zip(call, put) for v in (c, -p)),
        "spot": {"value": spot, "basis": "SPX cash index level"},
        "fetched_at_utc": "2026-08-20T20:42:28.098947+00:00",
        "call_wall": wall(call, call, "no_nonzero_call_gex"),
        "put_wall": wall(put, [-p for p in put], "no_nonzero_put_gex"),
        "dominant_net_gamma": wall([abs(x) for x in net], net, "all_net_gamma_zero"),
        "zero_dte": {"share": 0.05, "reason": None},
    }
    snap["by_strike"] = (
        {"reason": reason} if reason is not None
        else {"reason": None, "strike": list(strike),
              "call_modeled_magnitude_1pct_usd": list(call),
              "put_modeled_magnitude_1pct_usd": list(put)}
    )
    snap.update(overrides)
    return snap


def _bin(profile, center):
    return next(b for b in profile.window_bins if b.center == center)


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
    assert out != "" and "LARGEST CALL-CONTRACT MAGNITUDE STRIKE" not in out
    assert "LARGEST RAW-STRIKE |MODEL NET|" in out  # required dominant row still present
    assert "None" not in out
    s = _base()
    s["put_wall"] = {"strike": None, "gex_1pct_usd": None, "reason": "no_nonzero_put_gex"}
    out = _frag(s)
    assert out != "" and "LARGEST PUT-CONTRACT MAGNITUDE STRIKE" not in out
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


# ==========================================================================
# GEX-4 structural profile: carrier -> bins/window/outside + compatibility
# ==========================================================================

def _card(snap, now=NOW):
    return gex_card.build_gex_card(snap, now=now)


# --- absent optional carrier: legacy card renders, no profile block ---
def test_profile_absent_carrier_compatible():
    # mutation: require by_strike / raise on its absence.
    s = _base()                                  # _base() has no by_strike key
    card = _card(s)
    assert card is not None and card.profile is None
    out = _frag(s)
    assert out != "" and "WINDOW SHOWS" not in out and "ALL 31 BINS" not in out


# --- settlement / typed-unavailable carrier: profile absent, card unchanged ---
def test_profile_settlement_unavailable():
    # mutation: emit a profile from a typed-unavailable carrier.
    for token in ("same_day_spx_rows_present", "post_close_same_day_spxw_rows_present"):
        s = _coherent([7750.0], [10.0], [4.0], reason=token)
        card = _card(s)
        assert card is not None and card.profile is None, token
        assert "WINDOW SHOWS" not in _frag(s)


# --- malformed carrier: profile suppressed only; core card still renders ---
def test_profile_malformed_suppresses_profile_only():
    # mutation: relax a domain check, or let a malformed carrier suppress the card.
    good = _coherent([7700.0, 7750.0], [10.0, 20.0], [4.0, 5.0])
    bad_carriers = [
        {"reason": None, "strike": [7700.0, 7750.0],                    # length mismatch
         "call_modeled_magnitude_1pct_usd": [10.0],
         "put_modeled_magnitude_1pct_usd": [4.0, 5.0]},
        {"reason": None, "strike": [7750.0, 7700.0],                    # not ascending
         "call_modeled_magnitude_1pct_usd": [20.0, 10.0],
         "put_modeled_magnitude_1pct_usd": [5.0, 4.0]},
        {"reason": None, "strike": [7700.0, 7750.0],                    # negative magnitude
         "call_modeled_magnitude_1pct_usd": [10.0, -20.0],
         "put_modeled_magnitude_1pct_usd": [4.0, 5.0]},
        {"reason": None, "strike": [7700.1234, 7750.0],                 # strike not mills-exact
         "call_modeled_magnitude_1pct_usd": [10.0, 20.0],
         "put_modeled_magnitude_1pct_usd": [4.0, 5.0]},
        {"reason": None, "strike": "nope",                             # wrong type
         "call_modeled_magnitude_1pct_usd": [10.0, 20.0],
         "put_modeled_magnitude_1pct_usd": [4.0, 5.0]},
    ]
    for bad in bad_carriers:
        s = dict(good)
        s["by_strike"] = bad
        card = _card(s)
        assert card is not None and card.profile is None, bad
        assert _frag(s) != "" and "WINDOW SHOWS" not in _frag(s)


# --- domain-valid carrier that contradicts the core: WHOLE card suppressed ---
def test_profile_contradiction_suppresses_whole_card():
    # mutation: skip reconciliation / suppress only the profile on contradiction.
    total_bad = _coherent([7700.0, 7750.0], [10.0, 20.0], [4.0, 5.0],
                          gex_total_1pct_usd=999.0)               # fsum != stored total
    assert _card(total_bad) is None and _frag(total_bad) == ""
    anchor_bad = _coherent([7700.0, 7750.0], [10.0, 20.0], [4.0, 5.0],
                           call_wall={"strike": 7700.0, "gex_1pct_usd": 10.0, "reason": None})
    assert _card(anchor_bad) is None                              # argmax(call) is 7750, not 7700


# --- anchor tie reconciliation: lowest-strike wins; a higher pick contradicts ---
def test_profile_anchor_tie_lowest_strike():
    # mutation: resolve the argmax tie to the highest strike.
    strike, call, put = [7700.0, 7750.0], [20.0, 20.0], [0.0, 0.0]   # call ties
    ok = _coherent(strike, call, put)                                # helper picks lowest (7700)
    assert ok["call_wall"]["strike"] == 7700.0
    card = _card(ok)
    assert card is not None and card.profile is not None            # reconciles
    higher = _coherent(strike, call, put,
                       call_wall={"strike": 7750.0, "gex_1pct_usd": 20.0, "reason": None})
    assert _card(higher) is None                                    # tie must resolve to 7700


# --- half-open bins incl. exact upper boundary + 3-decimal strikes ---
def test_profile_bin_half_open_and_three_decimal():
    # mutation: use <= upper / float binning / round strikes before binning.
    s = _coherent([7737.5, 7762.5], [10.0, 20.0], [0.0, 0.0])       # 3-decimal strikes
    p = _card(s).profile
    # 7737.5 is the lower boundary of bin 7750 -> included there
    assert _bin(p, 7750.0).call == 10.0
    # 7762.5 is the exact UPPER boundary of bin 7750 -> belongs to the higher bin 7775
    assert _bin(p, 7775.0).call == 20.0
    assert _bin(p, 7750.0).interval == (7737.5, 7762.5)


# --- window is exactly 31 contiguous ascending 25-point bins around spot ---
def test_profile_window_31_bins():
    # mutation: wrong bin count / non-contiguous window / wrong spot bin.
    p = _card(_coherent([7750.0], [10.0], [4.0])).profile
    assert len(p.window_bins) == 31
    centers = [b.center for b in p.window_bins]
    assert centers == sorted(centers)
    assert all(centers[i + 1] - centers[i] == 25.0 for i in range(30))
    assert p.spot_bin_center == 7750.0 and 7750.0 in centers


# --- coverage percentages are honest and sum to 100 ---
def test_profile_coverage_sums_to_100():
    # mutation: print only one direction / let rounding break the sum.
    # in-window 7750 plus a far outside cluster at 8500 (> spot+375)
    s = _coherent([7750.0, 8500.0], [30.0, 70.0], [0.0, 0.0])
    out = _frag(s)
    line = next(x for x in out.splitlines() if "WINDOW SHOWS" in x)
    import re
    pair = re.search(r"(\d+)% OF CHAIN CALL\+PUT MODELED MAGNITUDE &middot; (\d+)% OUTSIDE", line)
    assert pair is not None and int(pair.group(1)) + int(pair.group(2)) == 100


# --- outside accounting: >=2% qualifies; line caps at 6 with a count; table is full ---
def test_profile_outside_cap_and_count():
    # mutation: drop the cap / drop the count / cap the accessible table too.
    strike = [7750.0] + [8200.0 + 100.0 * i for i in range(8)]      # 8 far bins (> 8125)
    call = [5.0] + [100.0] * 8                                       # each far bin ~12% of chain
    put = [0.0] * 9
    p = _card(_coherent(strike, call, put)).profile
    assert len(p.outside_bins) == 8                                  # all qualify (>= 2%)
    assert [b.center for b in p.outside_bins] == sorted(b.center for b in p.outside_bins)
    out = _frag(_coherent(strike, call, put))
    assert "6 OF 8 OUTSIDE BINS" in out and "2 MORE" in out          # compact line caps at 6
    assert out.count("(outside ") == 8                               # accessible table lists all 8


# --- zero-denominator guard: chain CALL+PUT == 0 -> no bin qualifies (0 >= 0) ---
def test_profile_zero_denominator_guard():
    # mutation: use >= against a zero chain so an empty far bin qualifies.
    walls = {"call_wall": {"strike": None, "gex_1pct_usd": None, "reason": "no_nonzero_call_gex"},
             "put_wall": {"strike": None, "gex_1pct_usd": None, "reason": "no_nonzero_put_gex"},
             "dominant_net_gamma": {"strike": None, "gex_1pct_usd": None, "reason": "all_net_gamma_zero"}}
    p = gex_card._compute_profile([7750.0, 9000.0], [7750000, 9000000], [0.0, 0.0], [0.0, 0.0],
                                  walls, 7747.71)
    assert p.chain_call_plus_put == 0.0 and p.in_window_pct == 0.0 and p.outside_bins == ()


# --- per-bin MODEL NET* is exactly call - put ---
def test_profile_model_net_derivation():
    # mutation: store a signed producer net / flip the subtraction.
    p = _card(_coherent([7700.0, 7750.0], [30.0, 10.0], [5.0, 25.0])).profile
    assert _bin(p, 7700.0).model_net == 25.0                        # 30 - 5
    assert _bin(p, 7750.0).model_net == -15.0                       # 10 - 25
    assert _bin(p, 7750.0).call_plus_put == 35.0                    # 10 + 25


# --- anchor markers land in their containing bin ---
def test_profile_anchor_markers_placed():
    # mutation: place markers by bin maximum instead of the raw anchor strike.
    p = _card(_coherent([7700.0, 7750.0, 7800.0], [10.0, 40.0, 5.0], [8.0, 2.0, 30.0])).profile
    marks = {m: b.center for b in p.window_bins for m in b.markers}
    assert marks["C"] == 7750.0                                     # largest call magnitude
    assert marks["P"] == 7800.0                                     # largest put magnitude
    assert marks["D"] == 7750.0                                     # largest |model net|


# --- accessible per-bin table carries the exact vocabulary, no hover reliance ---
def test_profile_accessible_table_vocabulary():
    # mutation: drop the table / rename a column / omit a disclosure.
    out = _frag(_coherent([7750.0], [30.0], [10.0]))
    for token in ("ALL 31 BINS + OUTSIDE BINS", "CALL MODELED MAGNITUDE",
                  "PUT MODELED MAGNITUDE", "MODEL NET*", "CALL+PUT MODELED MAGNITUDE",
                  "LARGEST CALL-CONTRACT MAGNITUDE STRIKE",
                  "LARGEST PUT-CONTRACT MAGNITUDE STRIKE",
                  "LARGEST RAW-STRIKE |MODEL NET|",
                  "participant and dealer positioning are not measured",
                  "AM/PM settlement timing not modeled", "SPX CASH SPOT"):
        assert token in out, token
    assert out.count("<script") == 0                                # no JS added


# --- extended forbidden vocabulary absent from the rendered profile ---
def test_profile_no_forbidden_vocabulary():
    # mutation: reintroduce a wall/dominant label or a directional/positioning word.
    out = _frag(_coherent([7700.0, 7750.0, 8500.0], [10.0, 40.0, 70.0], [8.0, 2.0, 5.0])).lower()
    for token in ("gamma flip", "zero gamma", "long gamma", "short gamma", "dealer long",
                  "dealer short", "dealers are", "hedging pressure", "support", "resistance",
                  "magnet", "pinning", "expected move", "max pain", "regime", "wall", "gross",
                  "cancellation", "offset", "financing", "footprint", "paired", "two-sided",
                  "tracks spot", "at spot", "bullish", "bearish", "dominant"):
        assert token not in out, token


# --- an anchor whose bin is OUTSIDE the window: no ladder marker, still disclosed ---
def test_profile_anchor_outside_window_disclosed_in_core():
    # A far max-magnitude anchor sits outside the +/-375 window; the ladder marks
    # only in-window anchor bins, but the raw strike is always printed in the core
    # LARGEST-... row, so nothing is lost.
    s = _coherent([7750.0, 9000.0], [10.0, 90.0], [0.0, 0.0])        # 9000 >> spot+375
    card = _card(s)
    assert card is not None and card.profile is not None
    marks = {m for b in card.profile.window_bins for m in b.markers}
    assert marks == set()                                            # 9000 anchor bin is off-window
    out = _frag(s)
    assert "LARGEST CALL-CONTRACT MAGNITUDE STRIKE" in out and "9000" in out


# ===========================================================================
# GEX-4 SVG structural strike ladder (visual implementation). Geometry is pure
# in gex_card._ladder_rows / _spot_y; markup is _svg_ladder. Each test is the
# red mutation for a named ladder invariant (no CSS-declaration theater).
# ===========================================================================
def _rich() -> dict:
    """A carrier spanning the 31-bin window (call-heavy above spot, put-heavy
    below, a near-balanced straddle at spot) plus outside mass on both sides, so
    the ladder exercises strong/weak/balanced bins, +/- MODEL NET*, C/P/D markers
    and a spot that falls between strikes."""
    spot = 7747.71
    strike, call, put = [], [], []
    for k in range(7375, 8126, 25):
        d = k - spot
        c = max(0.0, d + 55.0) * math.exp(-abs(d) / 300.0) if d > -55 else 0.0
        p = max(0.0, -d + 55.0) * math.exp(-abs(d) / 300.0) if d < 55 else 0.0
        if k in (7825, 7850):
            c += 250.0
        if k in (7650, 7675):
            p += 235.0
        if k == 7750:
            c += 72.0
            p += 68.0
        strike.append(float(k))
        call.append(round(c, 3) * 1e9)
        put.append(round(p, 3) * 1e9)
    strike = [7000.0] + strike + [8300.0]               # outside-window mass both sides
    call = [18.0e9] + call + [300.0e9]
    put = [205.0e9] + put + [45.0e9]
    return _coherent(strike, call, put, spot=spot)


def _ladder(snapshot):
    card = _card(snapshot)
    assert card is not None and card.profile is not None
    return card.profile, "\n".join(gex_card._svg_ladder(card.profile))


def test_ladder_present_with_profile_absent_without():
    # mutation: emit the ladder unconditionally, or never.
    prof, svg = _ladder(_rich())
    assert len(gex_card._ladder_rows(prof)) == 31
    assert svg.count('class="gex-ladder"') == 1
    assert "gex-ladder" not in _frag(_base())           # valid card, no carrier -> no ladder


def test_ladder_higher_strikes_drawn_above():
    # mutation: reverse the row orientation.
    prof, _ = _ladder(_rich())
    rows = gex_card._ladder_rows(prof)
    centers = [r["center"] for r in rows]
    ys = [r["y_mid"] for r in rows]
    assert centers == sorted(centers)                   # index 0 is the lowest strike
    assert all(ys[i] > ys[i + 1] for i in range(len(ys) - 1))   # higher strike -> smaller y


def test_ladder_widths_never_exceed_bounds():
    # mutation: drop the /scale_denominator normalization (a bar overruns the zone).
    prof, _ = _ladder(_rich())
    rows = gex_card._ladder_rows(prof)
    for r in rows:
        assert 0.0 <= r["call_len"] <= gex_card._L_BAR_MAX + 1e-9
        assert 0.0 <= r["put_len"] <= gex_card._L_BAR_MAX + 1e-9
        assert gex_card._L_BAR_L - 1e-9 <= r["net_x"] <= gex_card._L_SPINE + gex_card._L_BAR_MAX + 1e-9
    # the largest window bin fills exactly the max extent (never-clipping denom)
    assert max(max(r["call_len"], r["put_len"]) for r in rows) == gex_card._L_BAR_MAX


def test_ladder_net_tick_direction_matches_sign():
    # mutation: flip the MODEL NET* sign convention (call-heavy tick would go right).
    prof, _ = _ladder(_rich())
    saw_call, saw_put = False, False
    for r in gex_card._ladder_rows(prof):
        if r["model_net"] > 0:
            assert r["net_x"] < gex_card._L_SPINE       # call-heavy -> left of spine
            saw_call = True
        elif r["model_net"] < 0:
            assert r["net_x"] > gex_card._L_SPINE        # put-heavy -> right of spine
            saw_put = True
        else:
            assert r["net_x"] == gex_card._L_SPINE
    assert saw_call and saw_put                          # the fixture exercises both


def test_ladder_spot_rail_uses_actual_spot_not_snapped():
    # mutation: snap the spot rail to the containing bin center.
    prof, svg = _ladder(_rich())
    assert f"SPOT {gex_card._fmt_strike(prof.spot)}" in svg  # 7747.71, the true spot
    assert "SPOT 7750" not in svg                            # not snapped to the bin center
    rows = gex_card._ladder_rows(prof)
    row_ys = {round(r["y_mid"], 6) for r in rows}
    spot_y = gex_card._spot_y(prof)
    assert round(spot_y, 6) not in row_ys                    # interpolated between rows
    y7750 = next(r["y_mid"] for r in rows if r["center"] == 7750.0)
    y7725 = next(r["y_mid"] for r in rows if r["center"] == 7725.0)
    assert y7750 < spot_y < y7725                            # 7747.71 sits just below 7750


def test_ladder_zero_window_magnitude_renders_safely():
    # mutation: divide by scale_denominator without the zero guard.
    s = _coherent([7000.0, 8300.0], [50.0, 60.0], [40.0, 30.0], spot=7747.71)
    card = _card(s)
    assert card is not None and card.profile is not None
    prof = card.profile
    assert prof.scale_denominator == 0.0                     # all mass is outside the window
    rows = gex_card._ladder_rows(prof)
    assert len(rows) == 31
    assert all(r["call_len"] == 0.0 and r["put_len"] == 0.0 for r in rows)
    assert all(r["net_x"] == gex_card._L_SPINE for r in rows)
    svg = "\n".join(gex_card._svg_ladder(prof))              # must not raise
    assert 'class="gex-ladder"' in svg
    assert "<rect" not in svg                                # no zero-width bars drawn


def test_ladder_markers_render_in_containing_bins():
    # mutation: place a marker on the bin maximum instead of the anchor's own bin.
    s = _coherent([7700.0, 7750.0, 7800.0], [10.0, 40.0, 5.0], [8.0, 2.0, 30.0], spot=7747.71)
    prof, svg = _ladder(s)
    marks = {m: b.center for b in prof.window_bins for m in b.markers}
    assert marks == {"C": 7750.0, "P": 7800.0, "D": 7750.0}
    assert ">CD<" in svg                                     # 7750 carries C and D
    assert ">P<" in svg                                      # 7800 carries P


def test_ladder_offwindow_anchor_no_geometry_corruption():
    # mutation: force an off-window anchor into the window / distort rows to include it.
    s = _coherent([7750.0, 9000.0], [10.0, 90.0], [0.0, 0.0], spot=7747.71)  # 9000 off-window
    prof, _ = _ladder(s)
    rows = gex_card._ladder_rows(prof)
    assert len(rows) == 31
    marks = {m for b in prof.window_bins for m in b.markers}
    assert "C" not in marks and "D" not in marks            # the 9000 anchor stays off-window
    assert all(0.0 <= r["call_len"] <= gex_card._L_BAR_MAX for r in rows)


def test_ladder_table_and_scoped_overflow_guard_present():
    # mutation: dump the table open by default, or drop the phone overflow guard.
    frag = _frag(_rich())
    assert 'class="gex-ladder"' in frag                      # SVG is the primary visual
    assert "ALL 31 BINS + OUTSIDE BINS" in frag              # full table retained
    assert "<details>" in frag                               # behind a disclosure, not open
    assert "grid-template-columns:minmax(0,1fr) auto" in frag  # card-scoped phone guard
    assert "#gex-context" in frag


def test_ladder_no_directional_color_or_vocabulary():
    # mutation: encode call/put with red/green or add positioning shorthand.
    _, svg = _ladder(_rich())
    low = svg.lower()
    for hue in ("red", "green", "#f00", "#0f0", "#ff0000", "#00ff00", "rgb(",
                "hsl(", "crimson", "lime", "orange", "gold"):
        assert hue not in low, hue
    for token in ("wall", "magnet", "pinning", "flip", "support", "resistance",
                  "bullish", "bearish", "long gamma", "short gamma", "dealer"):
        assert token not in low, token


def test_ladder_accessibility_scaffolding_present():
    # mutation: drop role="img" / aria-label / the per-mark <title>s -> screen-reader
    # and touch users silently lose the datum the table is supposed to back up.
    _, svg = _ladder(_rich())
    assert 'role="img"' in svg
    assert 'aria-label="Modeled GEX strike ladder' in svg
    assert "<title>" in svg                              # per-bar / net-tick titles exist
    assert "CALL MODELED MAGNITUDE" in svg               # carried inside a bar <title>
    assert "MODEL NET*" in svg                           # carried inside a net-tick <title>
