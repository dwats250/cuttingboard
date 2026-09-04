"""Tests for the Cboe All Access GEX acquisition adapter.

Network-free: the HTTP transport is injected. Covers the charge's required
surface -- auth/header/request construction, SPX/SPXW admission, required-field
mapping, (non-)pagination, malformed/missing fail-closed, no contact with the
retired ``cdn.cboe.com`` delayed_quotes endpoint, and an end-to-end pass through
the *unmodified* producer ``tools/gex_snapshot.py``.

The adapter and producer live in tools/ (outside the cuttingboard package), so
they are imported by plain name after bootstrapping tools/ onto sys.path -- the
same idiom tests/test_gex_snapshot.py uses.
"""

from __future__ import annotations

import base64
import json
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import gex_allaccess_adapter as ad  # noqa: E402
import gex_snapshot as gx  # noqa: E402

# ---------------------------------------------------------------------------
# Synthetic fixtures (documented from the official response schema; no network)
# ---------------------------------------------------------------------------

_DATE = "2026-08-17"
_TOD = "09:30:00.001"  # ET time-of-day, as the delayed endpoint stamps it
_EXPIRY = "2026-09-18"  # future vs observation date (keeps the settlement gate open)


def _option(root, option_type, strike, gamma, oi, expiry=_EXPIRY, **extra):
    rec = {
        "root": root,
        "expiry": expiry,
        "option_type": option_type,
        "strike": strike,
        "gamma": gamma,
        "open_interest": oi,
    }
    rec.update(extra)
    return rec


def _chain_response(options, *, underlying=5000.0, timestamp=_TOD):
    return {
        "options": options,
        "underlying_last_trade_price": underlying,
        "underlying_mid": underlying,
        "timestamp": timestamp,
        "seq_no": 1,
    }


# A complete SPX+SPXW universe distributed into the four (root, option_type)
# call-plan buckets.
_UNIVERSE = {
    ("SPX", "C"): [_option("SPX", "C", 5000.0, 0.0002, 100, bid=1.2, iv=0.15),
                   _option("SPX", "C", 5200.0, 0.0002, 100)],
    ("SPX", "P"): [_option("SPX", "P", 4900.0, 0.0003, 100),
                   _option("SPX", "P", 5000.0, 0.00016, 100)],
    ("SPXW", "C"): [_option("SPXW", "C", 5100.0, 0.0001, 100)],
    ("SPXW", "P"): [_option("SPXW", "P", 4950.0, 0.0002, 100)],
}


class FakeTransport:
    """Records every call and returns programmed token + per-(root,option_type)
    chain responses. Routes chain calls by parsing the URL query."""

    def __init__(self, *, token_status=200, token_body=None,
                 chain_by_key=None, chain_status=200):
        self.calls = []  # (method, url, headers, body)
        self.token_status = token_status
        self.token_body = ({"access_token": "tok-123", "expires_in": 3600}
                           if token_body is None else token_body)
        self.chain_by_key = (chain_by_key if chain_by_key is not None
                             else {k: _chain_response(v)
                                   for k, v in _UNIVERSE.items()})
        self.chain_status = chain_status

    def __call__(self, method, url, headers, body):
        self.calls.append((method, url, dict(headers), body))
        if url.split("?", 1)[0] == ad.TOKEN_URL:
            return self.token_status, json.dumps(self.token_body).encode()
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        key = (q["root"][0], q["option_type"][0])
        return self.chain_status, json.dumps(self.chain_by_key[key]).encode()

    def urls(self):
        return [c[1] for c in self.calls]


# ---------------------------------------------------------------------------
# Auth / header / request construction
# ---------------------------------------------------------------------------

def test_basic_auth_header_is_base64_of_id_colon_secret():
    header = ad.build_basic_auth_header("cid", "csecret")
    assert header.startswith("Basic ")
    decoded = base64.b64decode(header.split(" ", 1)[1]).decode()
    assert decoded == "cid:csecret"


def test_fetch_token_posts_client_credentials_with_basic_header():
    tx = FakeTransport()
    token = ad.fetch_token("cid", "csecret", tx)
    assert token == "tok-123"
    method, url, headers, body = tx.calls[0]
    assert method == "POST" and url == ad.TOKEN_URL
    assert headers["Authorization"] == ad.build_basic_auth_header("cid", "csecret")
    assert b"grant_type=client_credentials" in body


def test_fetch_token_non_200_fails_closed():
    tx = FakeTransport(token_status=401)
    with pytest.raises(ad.AdapterError):
        ad.fetch_token("cid", "csecret", tx)


def test_fetch_token_missing_access_token_fails_closed():
    tx = FakeTransport(token_body={"expires_in": 3600})
    with pytest.raises(ad.AdapterError):
        ad.fetch_token("cid", "csecret", tx)


def test_build_chain_url_is_delayed_allaccess_with_filters():
    url = ad.build_chain_url("SPXW", "P", _DATE)
    assert url.startswith(
        "https://api.livevol.com/v1/delayed/allaccess/market/"
        "option-and-underlying-quotes?"
    )
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    assert q["symbol"] == ["SPX"]
    assert q["root"] == ["SPXW"]
    assert q["option_type"] == ["P"]
    assert q["date"] == [_DATE]


def test_fetch_chain_sends_bearer_token():
    tx = FakeTransport()
    ad.fetch_chain("tok-123", "SPX", "C", _DATE, tx)
    method, url, headers, body = tx.calls[0]
    assert method == "GET"
    assert headers["Authorization"] == "Bearer tok-123"


def test_fetch_chain_non_200_fails_closed():
    tx = FakeTransport(chain_status=503)
    with pytest.raises(ad.AdapterError):
        ad.fetch_chain("tok-123", "SPX", "C", _DATE, tx)


# ---------------------------------------------------------------------------
# OCC composition + SPX/SPXW admission (round-trips through the producer)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("root", ["SPX", "SPXW"])
def test_composed_occ_is_admitted_by_producer(root):
    occ = ad.compose_occ_symbol(root, "2026-09-18", "C", 5000.0)
    row = {"option": occ, "gamma": 0.0002, "open_interest": 100}
    contract, reason = gx._classify_row(row)
    assert reason is None
    assert contract is not None and contract.root == root
    assert contract.cp == "C" and contract.strike == 5000.0


def test_compose_occ_strike_padding_and_fraction():
    assert ad.compose_occ_symbol("SPX", "2026-09-18", "C", 5000.0) == \
        "SPX260918C05000000"
    # fractional-dollar strike (e.g. 5002.5) -> 5002500 thousandths
    assert ad.compose_occ_symbol("SPX", "2026-09-18", "P", 5002.5) == \
        "SPX260918P05002500"


@pytest.mark.parametrize("bad", [
    {"root": "AAPL", "expiry": "2026-09-18", "option_type": "C", "strike": 5000.0},
    {"root": "SPX", "expiry": "2026-09-18", "option_type": "X", "strike": 5000.0},
    {"root": "SPX", "expiry": "not-a-date", "option_type": "C", "strike": 5000.0},
    {"root": "SPX", "expiry": "2026-09-18", "option_type": "C", "strike": "5000"},
    {"root": "SPX", "expiry": "2026-09-18", "option_type": "C", "strike": True},
])
def test_compose_occ_rejects_bad_identity_fields(bad):
    with pytest.raises(ad.AdapterError):
        ad.compose_occ_symbol(bad["root"], bad["expiry"],
                              bad["option_type"], bad["strike"])


# ---------------------------------------------------------------------------
# Required-field mapping
# ---------------------------------------------------------------------------

def test_normalize_option_maps_required_fields_and_drops_extras():
    rec = _option("SPX", "C", 5000.0, 0.0002, 100, bid=1.2, ask=1.3, iv=0.15)
    out = ad.normalize_option(rec)
    assert out == {
        "option": "SPX260918C05000000",
        "gamma": 0.0002,
        "open_interest": 100,
    }
    assert "bid" not in out and "iv" not in out


def test_normalize_option_passes_bad_values_through_for_producer_accounting():
    # A negative gamma is NOT a structural fault; it must reach the producer,
    # which excludes it (invalid_gamma) rather than the adapter dropping it.
    rec = _option("SPX", "C", 5000.0, -1.0, 100)
    out = ad.normalize_option(rec)
    assert out["gamma"] == -1.0
    _, reason = gx._classify_row(out)
    assert reason == "invalid_gamma"


@pytest.mark.parametrize("drop", ["root", "expiry", "option_type", "strike"])
def test_normalize_option_missing_identity_field_fails_closed(drop):
    rec = _option("SPX", "C", 5000.0, 0.0002, 100)
    del rec[drop]
    with pytest.raises(ad.AdapterError):
        ad.normalize_option(rec)


# ---------------------------------------------------------------------------
# Timestamp reconstruction (ET time-of-day + query date -> UTC)
# ---------------------------------------------------------------------------

def test_compose_feed_timestamp_et_to_utc_and_round_trips_through_producer():
    # 09:30 ET on 2026-08-17 (EDT, UTC-4) -> 13:30 UTC.
    ts = ad.compose_feed_timestamp("2026-08-17", "09:30:00.001")
    assert ts == "2026-08-17 13:30:00"
    # DISCRIMINATOR: the ET text must NOT be handed to the producer as-is; the
    # producer interprets its string as UTC, so an un-converted ET string would be
    # silently wrong by the offset. This asserts the conversion actually happened.
    assert ts != "2026-08-17 09:30:00"
    # Producer parses it as UTC; its settlement gate converts back to ET 09:30.
    feed_dt = gx._parse_feed_timestamp(ts)
    et = feed_dt.astimezone(ZoneInfo("America/New_York"))
    assert (et.hour, et.minute) == (9, 30)
    assert et.date().isoformat() == "2026-08-17"


def test_compose_feed_timestamp_uses_real_tz_not_fixed_offset():
    # A winter date is EST (UTC-5): 09:30 EST -> 14:30 UTC. A summer date is EDT
    # (UTC-4): 09:30 EDT -> 13:30 UTC. The two differing offsets prove a real
    # America/New_York conversion, not a hardcoded shift or ET-read-as-UTC.
    assert ad.compose_feed_timestamp("2026-01-15", "09:30:00") == "2026-01-15 14:30:00"
    assert ad.compose_feed_timestamp("2026-07-15", "09:30:00") == "2026-07-15 13:30:00"


@pytest.mark.parametrize("bad", [None, "9:30", "25:00:00", 930])
def test_compose_feed_timestamp_malformed_fails_closed(bad):
    with pytest.raises(ad.AdapterError):
        ad.compose_feed_timestamp("2026-08-17", bad)


# ---------------------------------------------------------------------------
# Provenance: source/data_delay identity is TRUTHFUL for this dataset
# ---------------------------------------------------------------------------

def test_source_identity_truthful_cboe_delayed_tier():
    # Proves the frozen producer identity ``source == "cboe_delayed_quotes"`` is a
    # truthful data-class label for what THIS adapter acquires -- Cboe, delayed,
    # options quotes -- not merely a preserved consumer guard. Every endpoint the
    # adapter contacts is a Cboe/LiveVol host, and the data path is the /delayed/
    # tier.
    for url in (ad.TOKEN_URL, ad.build_chain_url("SPX", "C", _DATE)):
        host = urllib.parse.urlparse(url).netloc
        assert host in {"api.livevol.com", "id.livevol.com"}  # Cboe/LiveVol
    assert "/v1/delayed/" in ad.build_chain_url("SPX", "C", _DATE)
    # The producer's frozen identity strings are Cboe + delayed, matching the tier.
    assert gx.SOURCE == "cboe_delayed_quotes"
    assert "delayed" in gx.DATA_DELAY.lower()


# ---------------------------------------------------------------------------
# Merge / spot / envelope fail-closed
# ---------------------------------------------------------------------------

def test_normalize_merges_options_and_takes_spot_and_oldest_timestamp():
    responses = [
        _chain_response(_UNIVERSE[("SPX", "C")], underlying=5001.0,
                        timestamp="09:31:00.000"),
        _chain_response(_UNIVERSE[("SPX", "P")], underlying=5001.0,
                        timestamp="09:30:00.000"),
    ]
    payload = ad.normalize(responses, _DATE)
    assert payload["data"]["current_price"] == 5001.0
    assert len(payload["data"]["options"]) == 4  # 2 calls + 2 puts merged
    # oldest (09:30 ET -> 13:30 UTC) chosen over 09:31
    assert payload["timestamp"] == "2026-08-17 13:30:00"


def test_normalize_missing_underlying_price_fails_closed():
    resp = _chain_response(_UNIVERSE[("SPX", "C")])
    del resp["underlying_last_trade_price"]
    with pytest.raises(ad.AdapterError):
        ad.normalize([resp], _DATE)


def test_normalize_missing_options_array_fails_closed():
    resp = _chain_response(_UNIVERSE[("SPX", "C")])
    del resp["options"]
    with pytest.raises(ad.AdapterError):
        ad.normalize([resp], _DATE)


def test_normalize_consumes_full_options_array_no_pagination():
    # The bounded snapshot endpoint has no request-side cursor/limit; the entire
    # options array is consumed in one response.
    many = [_option("SPX", "C", 5000.0 + 5 * i, 0.0002, 100) for i in range(40)]
    payload = ad.normalize([_chain_response(many)], _DATE)
    assert len(payload["data"]["options"]) == 40


# ---------------------------------------------------------------------------
# Seam: fetch_fn + end-to-end through the unmodified producer
# ---------------------------------------------------------------------------

def test_fetch_fn_issues_token_then_full_call_plan():
    tx = FakeTransport()
    fetch_fn = ad.make_fetch_fn("cid", "csecret", _DATE, transport=tx)
    status, body = fetch_fn(ad.BASE_URL)
    assert status == 200
    posts = [c for c in tx.calls if c[0] == "POST"]
    gets = [c for c in tx.calls if c[0] == "GET"]
    assert len(posts) == 1  # one token mint
    assert len(gets) == len(ad.CALL_PLAN) == 4  # root x option_type


def test_fetch_fn_never_contacts_retired_cdn_endpoint():
    tx = FakeTransport()
    fetch_fn = ad.make_fetch_fn("cid", "csecret", _DATE, transport=tx)
    fetch_fn(ad.BASE_URL)
    for url in tx.urls():
        assert "cdn.cboe.com" not in url  # the retired delayed_quotes host
        host = urllib.parse.urlparse(url).netloc
        assert host in {"api.livevol.com", "id.livevol.com"}


def test_end_to_end_producer_writes_valid_artifact(tmp_path):
    tx = FakeTransport()
    fetch_fn = ad.make_fetch_fn("cid", "csecret", _DATE, transport=tx)
    now = datetime(2026, 8, 17, 18, 45, 0, tzinfo=timezone.utc)
    path = tmp_path / "gex_snapshot.json"
    code = gx.run(now=now, fetch_fn=fetch_fn, artifact_path=path,
                  url=ad.BASE_URL)
    assert code == 0
    art = json.loads(path.read_text())
    # Identity guard unchanged (consumer keys on this exact source string), and
    # the delayed-posture provenance is preserved and truthful for the tier.
    assert art["source"] == "cboe_delayed_quotes"
    assert art["data_delay"] == gx.DATA_DELAY
    assert "delayed" in art["data_delay"].lower()
    assert art["endpoint"] == ad.BASE_URL
    assert art["spot"]["value"] == 5000.0
    assert isinstance(art["gex_total_1pct_usd"], float)
    assert art["call_wall"]["strike"] is not None
    # by_strike profile emitted (future expiries -> settlement gate open)
    assert art["by_strike"]["reason"] is None
    assert set(art["coverage"]["per_root"]) == {"SPX", "SPXW"}
    assert art["coverage"]["included"] == 6


def test_fetch_fn_error_propagates_and_producer_fails_closed(tmp_path):
    tx = FakeTransport(token_status=500)
    fetch_fn = ad.make_fetch_fn("cid", "csecret", _DATE, transport=tx)
    # The AdapterError surfaces to the producer, which fail-closes (exit 1) and
    # writes no artifact.
    now = datetime(2026, 8, 17, 18, 45, 0, tzinfo=timezone.utc)
    path = tmp_path / "gex_snapshot.json"
    code = gx.run(now=now, fetch_fn=fetch_fn, artifact_path=path,
                  url=ad.BASE_URL)
    assert code == 1
    assert not path.exists()
