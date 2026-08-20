"""PRD-306 — tests for the manual cached _SPX GEX snapshot producer.

Frozen acceptance matrix R1..R37 (families A-H) from
docs/prd_history/PRD-306.md. Every test is network-free: the HTTP fetch is
injected via `fetch_fn(url) -> (status, body)` and the producer clock via
`now`. Each test is a PRD-198 invariant-4 red test — it fails if the guard it
covers is removed or inverted (MUTATION OBLIGATIONS).

The producer lives at tools/gex_snapshot.py (outside the cuttingboard package),
so it is imported by plain name after bootstrapping tools/ onto sys.path — the
same idiom tests/test_macro_awareness_collector.py uses.
"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import gex_snapshot as gx  # noqa: E402 (must follow the sys.path bootstrap)

# --------------------------------------------------------------------------
# Fixture builders (synthetic only; no committed Cboe chain, no network)
# --------------------------------------------------------------------------

_NOW = datetime(2026, 8, 17, 18, 45, 0, tzinfo=timezone.utc)   # producer clock
_FEED_TS = "2026-08-17 18:42:35"                               # provider UTC text
_F = 25_000_000.0  # 100 * 5000**2 * 0.01, the per (gamma*OI) factor at spot 5000


def _contract(option, gamma, oi, **extra):
    """One raw provider row. `extra` lets a test seed raw-chain keys (bid/iv/...)
    to prove they never survive into the emitted artifact (R12)."""
    row = {"option": option, "gamma": gamma, "open_interest": oi}
    row.update(extra)
    return row


def _feed(options, *, current_price=5000.0, timestamp=_FEED_TS, drop=None):
    data = {"current_price": current_price, "options": options}
    top = {"timestamp": timestamp, "data": data}
    if drop == "options":
        del data["options"]
    elif drop == "current_price":
        del data["current_price"]
    elif drop == "timestamp":
        del top["timestamp"]
    return top


def _body(feed):
    # allow_nan=True so NaN/inf fixtures can be injected as provider input.
    return json.dumps(feed).encode("utf-8")


def _fetch(feed, *, status=200):
    return lambda url: (status, _body(feed))


def _run(tmp_path, feed_or_fetch, *, now=_NOW, name="gex_snapshot.json"):
    path = tmp_path / name
    fetch_fn = feed_or_fetch if callable(feed_or_fetch) else _fetch(feed_or_fetch)
    code = gx.run(now=now, fetch_fn=fetch_fn, artifact_path=path)
    return code, path


def _run_ok(tmp_path, feed, *, now=_NOW):
    code, path = _run(tmp_path, feed, now=now)
    assert code == 0, "expected a successful (exit 0) generation"
    return json.loads(path.read_text(encoding="utf-8"))


def _happy_options():
    return [
        _contract("SPX260817C05000000", 0.0002, 100, bid=1.2, ask=1.3, iv=0.15),
        _contract("SPX260817P04900000", 0.0003, 100),
        _contract("SPXW260817C05100000", 0.0001, 100),
        _contract("SPX260919C05200000", 0.0002, 100),
        _contract("SPX260919P05000000", 0.00016, 100),
    ]


def _keys_recursive(obj, out):
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.add(k)
            _keys_recursive(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _keys_recursive(item, out)


def _has_list_of_objects(obj):
    if isinstance(obj, list):
        if any(isinstance(x, dict) for x in obj):
            return True
        return any(_has_list_of_objects(x) for x in obj)
    if isinstance(obj, dict):
        return any(_has_list_of_objects(v) for v in obj.values())
    return False


# ==========================================================================
# A. Happy-path / schema / determinism
# ==========================================================================

class TestASchema:
    def test_r1_happy_path_full_schema_types(self, tmp_path):
        art = _run_ok(tmp_path, _feed(_happy_options()))

        assert art["schema_version"] == 1
        assert art["source"] == "cboe_delayed_quotes"
        assert art["endpoint"] == gx.ENDPOINT
        assert art["underlying"] == "_SPX"
        assert art["roots"] == ["SPX", "SPXW"]
        assert art["fetched_at_utc"] == "2026-08-17T18:45:00+00:00"
        assert art["feed_timestamp_utc"] == "2026-08-17T18:42:35+00:00"
        assert art["data_delay"] == "~15 min delayed (REPORTED; Cboe delayed_quotes posture)"
        assert art["spot"] == {"value": 5000.0,
                               "basis": "SPX cash index level (data.current_price)"}
        assert art["model_label"] == "greeks Cboe-model-computed; GEX derived-of-model"
        assert art["sign_convention"] == (
            "calls:+1 / puts:-1 -- assumed dealer-long-call/short-put "
            "positioning; descriptive assumption, not measured")
        assert art["units"] == "USD gamma notional per 1% underlying move"
        assert art["contract_multiplier"] == 100

        assert art["gex_total_1pct_usd"] == 100000.0
        assert art["call_wall"] == {"strike": 5000.0, "gex_1pct_usd": 500000.0, "reason": None}
        assert art["put_wall"] == {"strike": 4900.0, "gex_1pct_usd": -750000.0, "reason": None}
        assert art["dominant_net_gamma"] == {"strike": 4900.0, "gex_1pct_usd": -750000.0,
                                             "reason": None}

        zd = art["zero_dte"]
        assert zd["share"] == 0.625
        assert zd["abs_gex_0dte_1pct_usd"] == 1_500_000.0
        assert zd["abs_gex_total_1pct_usd"] == 2_400_000.0
        assert zd["observation_trading_date"] == "2026-08-17"
        assert zd["per_root"]["SPX"] == {"abs_gex_0dte_1pct_usd": 1_250_000.0, "contracts": 2}
        assert zd["per_root"]["SPXW"] == {"abs_gex_0dte_1pct_usd": 250_000.0, "contracts": 1}
        assert isinstance(zd["caveat"], str) and zd["caveat"]
        assert zd["reason"] is None

        assert set(art["provenance"].keys()) == {
            "configured", "observed", "reported", "derived", "inferred"}
        cov = art["coverage"]
        assert cov["contracts_total"] == 5
        assert cov["included"] == 5
        assert set(cov["excluded"].keys()) == {
            "missing_fields", "invalid_gamma", "invalid_open_interest",
            "unparseable_symbol", "invalid_expiry", "unexpected_root"}
        assert cov["per_root"] == {"SPX": 4, "SPXW": 1}
        assert cov["expirations"] == {"count": 2, "min": "2026-08-17", "max": "2026-09-19"}
        assert cov["zero_gamma_rows"] == 0
        assert cov["zero_oi_rows"] == 0

    def test_r13_determinism_byte_identical(self, tmp_path):
        code1, p1 = _run(tmp_path, _feed(_happy_options()), name="a.json")
        code2, p2 = _run(tmp_path, _feed(_happy_options()), name="b.json")
        assert code1 == 0 and code2 == 0
        assert p1.read_bytes() == p2.read_bytes()


# ==========================================================================
# B. Arithmetic
# ==========================================================================

class TestBArithmetic:
    def test_r2_gex_total_hand_computed(self, tmp_path):
        opts = [
            _contract("SPX260919C05000000", 0.0002, 100),   # +0.0002*100*F = +500000
            _contract("SPX260919P05000000", 0.0001, 100),   # -0.0001*100*F = -250000
            _contract("SPX260919C05100000", 0.0001, 50),    # +0.0001*50*F  = +125000
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["gex_total_1pct_usd"] == 375000.0   # 500000 - 250000 + 125000

    def test_r3_put_sign_negated_pair_nets_zero(self, tmp_path):
        opts = [
            _contract("SPX260919C05000000", 0.0001, 100),   # +250000
            _contract("SPX260919P05000000", 0.0001, 100),   # -250000
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["gex_total_1pct_usd"] == 0.0


# ==========================================================================
# C. Walls / dominant
# ==========================================================================

class TestCWalls:
    def test_r14_call_wall_distinct_from_oi_and_net_max(self, tmp_path):
        opts = [
            _contract("SPX260919C05000000", 0.0003, 10),    # call_gex +75000 (max call)
            _contract("SPX260919C05100000", 0.000002, 1000),  # call_gex +50000 (max OI, not max gex)
            _contract("SPX260919C04900000", 0.0001, 10),    # call_gex +25000
            _contract("SPX260919P04900000", 0.0005, 100),   # put -1,250,000 -> net-max @4900
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["call_wall"]["strike"] == 5000.0
        assert art["call_wall"]["gex_1pct_usd"] == 75000.0
        assert art["dominant_net_gamma"]["strike"] == 4900.0

    def test_r15_put_wall_absolute_selection_negative_value(self, tmp_path):
        opts = [
            _contract("SPX260919P05200000", 0.0004, 100),   # -1,000,000 (max abs)
            _contract("SPX260919P04900000", 0.00025, 100),  # -625000
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["put_wall"]["strike"] == 5200.0
        assert art["put_wall"]["gex_1pct_usd"] == -1_000_000.0

    def test_r16_cancellation_strike_not_dominant_still_wall(self, tmp_path):
        opts = [
            _contract("SPX260919C05000000", 0.0002, 100),   # +500000
            _contract("SPX260919P05000000", 0.0002, 100),   # -500000 -> net@5000 = 0
            _contract("SPX260919C05100000", 0.0001, 100),   # +250000 -> net@5100 dominant
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["call_wall"]["strike"] == 5000.0
        assert art["put_wall"]["strike"] == 5000.0
        assert art["dominant_net_gamma"]["strike"] == 5100.0

    def test_r17_dominant_negative_beats_positive(self, tmp_path):
        opts = [
            _contract("SPX260919C05000000", 0.00012, 100),  # net@5000 = +300000
            _contract("SPX260919P04900000", 0.0002, 100),   # net@4900 = -500000
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["dominant_net_gamma"]["strike"] == 4900.0
        assert art["dominant_net_gamma"]["gex_1pct_usd"] == -500000.0
        assert art["call_wall"]["strike"] == 5000.0

    def test_r18_tie_break_lowest_strike(self, tmp_path):
        opts = [
            _contract("SPX260919C05100000", 0.0001, 100),   # +250000
            _contract("SPX260919C05000000", 0.0001, 100),   # +250000 (tie -> lowest)
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["call_wall"]["strike"] == 5000.0

    def test_r24_call_wall_unavailable_tokens(self, tmp_path):
        puts_only = [_contract("SPX260919P05000000", 0.0001, 100)]
        art = _run_ok(tmp_path, _feed(puts_only))
        assert art["call_wall"]["strike"] is None
        assert art["call_wall"]["gex_1pct_usd"] is None
        assert art["call_wall"]["reason"] == "no_eligible_calls"

        zero_calls = [
            _contract("SPX260919C05000000", 0.0, 100),      # degenerate call (0 gex)
            _contract("SPX260919P05000000", 0.0001, 100),   # keeps included > 0
        ]
        art2 = _run_ok(tmp_path, _feed(zero_calls))
        assert art2["call_wall"]["reason"] == "no_nonzero_call_gex"

    def test_r25_put_wall_unavailable_tokens(self, tmp_path):
        calls_only = [_contract("SPX260919C05000000", 0.0001, 100)]
        art = _run_ok(tmp_path, _feed(calls_only))
        assert art["put_wall"]["reason"] == "no_eligible_puts"

        zero_puts = [
            _contract("SPX260919P05000000", 0.0001, 0),     # degenerate put (0 OI)
            _contract("SPX260919C05000000", 0.0001, 100),
        ]
        art2 = _run_ok(tmp_path, _feed(zero_puts))
        assert art2["put_wall"]["reason"] == "no_nonzero_put_gex"

    def test_r26_dominant_unavailable_full_cancellation(self, tmp_path):
        opts = [
            _contract("SPX260919C05000000", 0.0001, 100),   # +250000
            _contract("SPX260919P05000000", 0.0001, 100),   # -250000 -> net 0 everywhere
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["dominant_net_gamma"]["strike"] is None
        assert art["dominant_net_gamma"]["reason"] == "all_net_gamma_zero"

    def test_r27_uniform_unavailable_object_shape(self, tmp_path):
        # only degenerate rows -> all three structural objects unavailable but full-shaped
        opts = [
            _contract("SPX260919C05000000", 0.0, 100),
            _contract("SPX260919P05000000", 0.0, 100),
        ]
        art = _run_ok(tmp_path, _feed(opts))
        for key in ("call_wall", "put_wall", "dominant_net_gamma"):
            obj = art[key]
            assert set(obj.keys()) == {"strike", "gex_1pct_usd", "reason"}
            assert obj["strike"] is None
            assert obj["reason"] is not None


# ==========================================================================
# D. 0DTE
# ==========================================================================

class TestDZeroDte:
    def test_r19_numerator_absolute_and_date_scoped(self, tmp_path):
        opts = [
            _contract("SPX260817C05000000", 0.0002, 100),   # 0DTE +500000 abs 500000
            _contract("SPX260817P05000000", 0.0001, 100),   # 0DTE -250000 abs 250000
            _contract("SPX260919C05000000", 0.0001, 100),   # non-0DTE +250000
        ]
        art = _run_ok(tmp_path, _feed(opts))
        # abs numerator = 500000 + 250000 = 750000 (signed would be 250000)
        assert art["zero_dte"]["abs_gex_0dte_1pct_usd"] == 750000.0

    def test_r20_denominator_all_expirations(self, tmp_path):
        opts = [
            _contract("SPX260817C05000000", 0.0002, 100),   # 0DTE 500000
            _contract("SPX260919C05000000", 0.0001, 100),   # non-0DTE 250000
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["zero_dte"]["abs_gex_total_1pct_usd"] == 750000.0

    def test_r21_per_root_split(self, tmp_path):
        opts = [
            _contract("SPX260817C05000000", 0.0002, 100),   # SPX 0DTE 500000
            _contract("SPX260817P04900000", 0.0001, 100),   # SPX 0DTE 250000
            _contract("SPXW260817C05100000", 0.0001, 100),  # SPXW 0DTE 250000
        ]
        art = _run_ok(tmp_path, _feed(opts))
        pr = art["zero_dte"]["per_root"]
        assert pr["SPX"] == {"abs_gex_0dte_1pct_usd": 750000.0, "contracts": 2}
        assert pr["SPXW"] == {"abs_gex_0dte_1pct_usd": 250000.0, "contracts": 1}

    def test_r22_zero_denominator_share_null(self, tmp_path):
        opts = [
            _contract("SPX260817C05000000", 0.0, 100),      # degenerate, included, 0 gex
            _contract("SPX260919P05000000", 0.0, 100),
        ]
        art = _run_ok(tmp_path, _feed(opts))
        zd = art["zero_dte"]
        assert zd["share"] is None
        assert zd["reason"] == "zero_abs_gex_denominator"
        assert zd["abs_gex_0dte_1pct_usd"] == 0
        assert zd["abs_gex_total_1pct_usd"] == 0

    def test_r23_observation_date_uses_eastern_not_utc(self, tmp_path):
        # 2026-08-18 01:00:00 UTC -> 2026-08-17 21:00 America/New_York
        feed = _feed([_contract("SPX260817C05000000", 0.0002, 100)],
                     timestamp="2026-08-18 01:00:00")
        art = _run_ok(tmp_path, feed)
        assert art["zero_dte"]["observation_trading_date"] == "2026-08-17"
        # the 260817 contract is therefore 0DTE on the ET date
        assert art["zero_dte"]["abs_gex_0dte_1pct_usd"] == 500000.0


# ==========================================================================
# E. Validation / admissibility
# ==========================================================================

class TestEValidation:
    def test_r4_occ_parse_strict_and_scaled(self, tmp_path):
        opts = [
            _contract("SPX260919C05000000", 0.0001, 100),   # valid, strike 5000
            _contract("NOT_AN_OCC_SYMBOL", 0.0001, 100),    # malformed
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["coverage"]["excluded"]["unparseable_symbol"] == 1
        assert art["call_wall"]["strike"] == 5000.0        # digits/1000 scaling

    def test_r7_missing_top_level_surfaces_fail_loud(self, tmp_path):
        base = _happy_options()
        for missing in ("options", "current_price", "timestamp"):
            code, path = _run(tmp_path, _feed(base, drop=missing), name=f"{missing}.json")
            assert code != 0, f"missing {missing} must exit non-zero"
            assert not path.exists()

    def test_r8_zero_included_fail_loud(self, tmp_path):
        opts = [_contract("GARBAGE", 0.0001, 100)]  # everything excluded -> included 0
        code, path = _run(tmp_path, _feed(opts))
        assert code != 0
        assert not path.exists()

    def test_r28_booleans_never_pass_numeric(self, tmp_path):
        opts = [
            _contract("SPX260919C05000000", True, 100),     # bool gamma
            _contract("SPX260919C05100000", 0.0001, True),  # bool OI
            _contract("SPX260919C05200000", 0.0001, 100),   # keep one included
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["coverage"]["excluded"]["invalid_gamma"] == 1
        assert art["coverage"]["excluded"]["invalid_open_interest"] == 1

        code, path = _run(tmp_path, _feed(_happy_options(), current_price=True),
                          name="boolspot.json")
        assert code != 0

    def test_r29_non_finite_rejected(self, tmp_path):
        opts = [
            _contract("SPX260919C05000000", float("nan"), 100),
            _contract("SPX260919C05100000", float("inf"), 100),
            _contract("SPX260919C05200000", 0.0001, 100),
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["coverage"]["excluded"]["invalid_gamma"] == 2

        code, _ = _run(tmp_path, _feed(_happy_options(), current_price=float("nan")),
                       name="nanspot.json")
        assert code != 0

    def test_r30_domain_violations_rejected(self, tmp_path):
        opts = [
            _contract("SPX260919C05000000", -0.5, 100),     # negative gamma
            _contract("SPX260919C05100000", 0.0001, -3),    # negative OI
            _contract("SPX260919C05200000", 0.0001, 2.5),   # non-integer OI
            _contract("SPX260919C05300000", 0.0001, 100),   # keep one included
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["coverage"]["excluded"]["invalid_gamma"] == 1
        assert art["coverage"]["excluded"]["invalid_open_interest"] == 2

    def test_r31_expiry_must_be_valid_calendar_date(self, tmp_path):
        opts = [
            _contract("SPX261301C05000000", 0.0001, 100),   # month 13
            _contract("SPX260230C05100000", 0.0001, 100),   # Feb 30
            _contract("SPX260919C05200000", 0.0001, 100),   # valid
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["coverage"]["excluded"]["invalid_expiry"] == 2

    def test_r32_root_allowlist(self, tmp_path):
        opts = [
            _contract("XSP260919C05000000", 0.0001, 100),   # non-allowlisted root
            _contract("SPX260919C05100000", 0.0001, 100),
        ]
        art = _run_ok(tmp_path, _feed(opts))
        assert art["coverage"]["excluded"]["unexpected_root"] == 1

    def test_r33_invalid_present_spot_fail_loud(self, tmp_path):
        for bad in (0.0, -5.0, "abc"):
            code, path = _run(tmp_path, _feed(_happy_options(), current_price=bad),
                              name=f"spot_{bad}.json")
            assert code != 0, f"current_price {bad!r} must fail loud"
            assert not path.exists()

    def test_r34_malformed_timestamp_fail_loud(self, tmp_path):
        code, path = _run(tmp_path,
                          _feed(_happy_options(), timestamp="2026-08-17T18:42:35"))
        assert code != 0
        assert not path.exists()

    def test_r35_feed_timestamp_normalized_tz_aware(self, tmp_path):
        art = _run_ok(tmp_path, _feed(_happy_options()))
        assert art["feed_timestamp_utc"] == "2026-08-17T18:42:35+00:00"

    def test_r36_coverage_reconciles(self, tmp_path):
        opts = [
            _contract("SPX260817C05000000", 0.0001, 100),                 # included
            {"option": "SPX260817C05000000", "open_interest": 100},        # missing gamma
            _contract("GARBAGE", 0.0001, 100),                            # unparseable
            _contract("XSP260817C05000000", 0.0001, 100),                 # unexpected_root
            _contract("SPX261301C05000000", 0.0001, 100),                 # invalid_expiry
            _contract("SPX260817C05000000", -0.5, 100),                   # invalid_gamma
            _contract("SPX260817C05000000", 0.0001, -3),                  # invalid_open_interest
        ]
        art = _run_ok(tmp_path, _feed(opts))
        cov = art["coverage"]
        for key in ("missing_fields", "invalid_gamma", "invalid_open_interest",
                    "unparseable_symbol", "invalid_expiry", "unexpected_root"):
            assert cov["excluded"][key] == 1, f"{key} should count exactly 1"
        assert cov["included"] + sum(cov["excluded"].values()) == cov["contracts_total"]
        assert cov["contracts_total"] == 7

    def test_r9_timestamps_honest(self, tmp_path):
        art = _run_ok(tmp_path, _feed(_happy_options()))
        assert art["fetched_at_utc"].endswith("+00:00")
        assert art["data_delay"] == "~15 min delayed (REPORTED; Cboe delayed_quotes posture)"

    def test_r9_naive_now_raises(self, tmp_path):
        naive = datetime(2026, 8, 17, 18, 45, 0)  # no tzinfo
        with pytest.raises(ValueError):
            gx.run(now=naive, fetch_fn=_fetch(_feed(_happy_options())),
                   artifact_path=tmp_path / "n.json")

    def test_r37_provenance_exhaustive_five_classes(self, tmp_path):
        art = _run_ok(tmp_path, _feed(_happy_options()))
        prov = art["provenance"]
        top_level = set(art.keys())
        classified = []
        for cls in ("configured", "observed", "reported", "derived", "inferred"):
            classified.extend(prov[cls])
        # exhaustive and disjoint over every emitted top-level field
        assert sorted(classified) == sorted(top_level)
        assert len(classified) == len(set(classified))
        assert "coverage" in prov["derived"]
        assert "coverage" not in prov["observed"]
        assert "fetched_at_utc" in prov["observed"]


# ==========================================================================
# F. Failure / IO
# ==========================================================================

class TestFFailureIO:
    def test_r5_non_200_fail_loud_preserves_prior(self, tmp_path):
        path = tmp_path / "gex_snapshot.json"
        prior = b'{"prior": true}\n'
        path.write_bytes(prior)
        code = gx.run(now=_NOW, fetch_fn=_fetch(_feed(_happy_options()), status=503),
                      artifact_path=path)
        assert code != 0
        assert path.read_bytes() == prior

    def test_r6_non_json_fail_loud(self, tmp_path):
        path = tmp_path / "gex_snapshot.json"
        code = gx.run(now=_NOW, fetch_fn=lambda url: (200, b"<html>not json</html>"),
                      artifact_path=path)
        assert code != 0
        assert not path.exists()

    def test_r10_atomic_write_preserves_prior_on_midwrite_failure(self, tmp_path, monkeypatch):
        path = tmp_path / "gex_snapshot.json"
        prior = b'{"prior": true}\n'
        path.write_bytes(prior)

        def boom(src, dst):
            raise OSError("simulated mid-write failure")

        monkeypatch.setattr(gx.os, "replace", boom)
        code = gx.run(now=_NOW, fetch_fn=_fetch(_feed(_happy_options())),
                      artifact_path=path)
        assert code != 0
        assert path.read_bytes() == prior
        assert not (tmp_path / "gex_snapshot.json.tmp").exists()


# ==========================================================================
# G. Isolation / non-redistribution
# ==========================================================================

class TestGIsolation:
    def test_r11_no_cuttingboard_import_in_producer(self):
        src = (_TOOLS_DIR / "gex_snapshot.py").read_text(encoding="utf-8")
        assert "import cuttingboard" not in src
        assert "from cuttingboard" not in src

    def test_r11_no_reverse_import_from_cuttingboard(self):
        pkg = _REPO_ROOT / "cuttingboard"
        hits = []
        for py in pkg.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            if "import gex_snapshot" in text or "from gex_snapshot" in text:
                hits.append(str(py))
        assert hits == [], f"cuttingboard must not import the producer: {hits}"

    def test_r12_non_redistribution_shape(self, tmp_path):
        art = _run_ok(tmp_path, _feed(_happy_options()))
        forbidden = {
            "bid", "ask", "bid_size", "ask_size", "iv", "theo", "delta", "gamma",
            "theta", "vega", "rho", "volume", "last_trade_price", "last_trade_time",
            "open", "high", "low", "close", "prev_day_close", "change",
            "percent_change", "tick", "option", "open_interest",
        }
        keys = set()
        _keys_recursive(art, keys)
        leaked = forbidden & keys
        assert leaked == set(), f"forbidden raw-chain keys leaked: {leaked}"
        assert not _has_list_of_objects(art), "no per-contract row-list may be emitted"


# ==========================================================================
# Guard: JSON must never carry NaN/Inf tokens
# ==========================================================================

class TestStandardJson:
    def test_standard_json_only(self, tmp_path):
        _, path = _run(tmp_path, _feed(_happy_options()))
        raw = path.read_text(encoding="utf-8")
        for token in ("NaN", "Infinity", "-Infinity"):
            assert token not in raw
        # round-trips through a strict parser (rejects non-standard constants)
        json.loads(raw, parse_constant=_reject_constant)


def _reject_constant(value):  # pragma: no cover - only fires on non-standard JSON
    raise AssertionError(f"non-standard JSON constant emitted: {value}")


def test_module_uses_stdlib_only():
    src = (_TOOLS_DIR / "gex_snapshot.py").read_text(encoding="utf-8")
    third_party = {"requests", "yfinance", "pandas", "numpy", "anthropic",
                   "feedparser", "dotenv", "pyarrow"}
    for line in src.splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ")):
            mod = stripped.split()[1].split(".")[0]
            assert mod not in third_party, f"non-stdlib import: {mod}"
    assert not math.isnan(float("0"))  # keep math import meaningful/used
