#!/usr/bin/env python3
"""Cboe All Access API acquisition adapter for the GEX snapshot producer.

The retired/prohibited Cboe ``delayed_quotes`` webpage/CDN acquisition path is
replaced by the sanctioned **Cboe All Access API** (LiveVol Web API) delayed
``option-and-underlying-quotes`` endpoint. This module is a THIN seam: it does
OAuth2 client-credentials auth, issues one bounded SPX/SPXW pull, and normalizes
the response into the *exact* payload shape ``tools/gex_snapshot.py`` already
consumes -- so all existing by_strike / profile / wall / 0DTE logic and every
downstream identity guard stay byte-for-byte unchanged.

Seam contract: :func:`make_fetch_fn` returns a ``fetch_fn(url) -> (status,
bytes)`` callable of exactly the shape ``gex_snapshot.run(fetch_fn=..., url=...)``
expects. The producer file is not modified.

Normalization (documented semantic translation, adapter-only):
  * ``option``           <- composed 21-char OCC symbol from
                            (root, expiry, option_type, strike); the producer's
                            own ``_OCC_RE`` re-parses it, so the producer is
                            untouched.
  * ``gamma``            <- passed through verbatim (producer admissibility keeps
                            its own exclusion accounting for bad VALUES).
  * ``open_interest``    <- passed through verbatim.
  * ``data.current_price`` <- ``underlying_last_trade_price`` (SPX cash index
                            level basis; the one field whose cash-index semantics
                            must be confirmed against the first live sample).
  * ``timestamp``        <- authoritative reconstruction: query ``date`` (ET
                            trading date) + response ``timestamp`` (ET time of
                            day) -> UTC ``"YYYY-MM-DD HH:MM:SS"``. This is NOT a
                            producer-clock fallback; both halves are authoritative
                            (the date we requested, the time the provider stamped).

Provenance identity (item reviewed 2026-09-04): the producer's frozen constants
``source == "cboe_delayed_quotes"`` and ``data_delay`` (``~15 min delayed
(REPORTED; ...)``) are left UNCHANGED because they remain TRUTHFUL for this exact
dataset -- Cboe All Access serves the same Cboe *delayed* (15-minute) options-quote
class, acquired here over its ``/v1/delayed/`` tier -- not merely to preserve the
consumer identity guard. Editing those PRD-306/307 build-binding constants was
rejected as an out-of-scope frozen-contract change with no honesty gain. Proven by
``test_source_identity_truthful_cboe_delayed_tier`` and the end-to-end provenance
assertion.

Fail-closed: any transport non-200, missing token, malformed envelope, missing
per-record identity field, or unparseable timestamp raises :class:`AdapterError`.
The producer's ``run`` catches it, returns non-zero, and preserves the last-good
artifact. This adapter never contacts ``cdn.cboe.com`` / ``delayed_quotes``.

Stdlib-only (no new dependency), mirroring the producer's dependency honesty;
``python-dotenv`` is used only in :func:`main` for the env read (the established
``config.py`` secret pattern).
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Frozen adapter constants
# ---------------------------------------------------------------------------

# OAuth2 client-credentials token endpoint (official Cboe All Access / LiveVol).
TOKEN_URL = "https://id.livevol.com/connect/token"
# Delayed options snapshot endpoint (the /v1/delayed/ prefix selects the delayed
# tier; the same endpoint schema serves live/delayed/historical).
BASE_URL = (
    "https://api.livevol.com/v1/delayed/allaccess/market/"
    "option-and-underlying-quotes"
)
# Underlying index symbol pulled (SPX cash index). SPX and SPXW option roots both
# list under this underlying symbol; the ``root`` query param splits them.
SYMBOL = "SPX"
ROOTS = ("SPX", "SPXW")
OPTION_TYPES = ("C", "P")
# Deterministic, guaranteed-complete call plan: one bounded call per
# (root, option_type). Union is the full SPX+SPXW call/put universe. Delayed cost
# is 8 points per call (documented), i.e. 32 points per pull under this plan; if a
# live probe confirms ``root``/``option_type`` are optional filters the plan can
# be collapsed to a single 8-point call without touching normalization.
CALL_PLAN = tuple((root, ot) for root in ROOTS for ot in OPTION_TYPES)

MARKET_TZ = ZoneInfo("America/New_York")

# Credential env vars (existing config.py + os.getenv secret pattern).
ENV_CLIENT_ID = "CBOE_ALLACCESS_CLIENT_ID"
ENV_CLIENT_SECRET = "CBOE_ALLACCESS_CLIENT_SECRET"

# Per-option identity fields required to build the OCC symbol. Their ABSENCE is a
# structural provider-contract violation -> fail-closed. (Bad gamma/OI VALUES are
# NOT structural: they pass through for the producer's own exclusion accounting.)
_REQUIRED_OPTION_FIELDS = ("root", "expiry", "option_type", "strike")
# Top-level underlying price field mapped to the producer's ``current_price``.
_UNDERLYING_PRICE_FIELD = "underlying_last_trade_price"

# A transport is: (method, url, headers, body_bytes_or_None) -> (status, bytes).
Transport = Callable[[str, str, dict, Optional[bytes]], "tuple[int, bytes]"]


class AdapterError(Exception):
    """Any auth / transport / envelope / mapping failure. Fail-closed: the
    producer's ``run`` catches it, exits non-zero, preserves the last artifact."""


# ---------------------------------------------------------------------------
# Default transport (stdlib urllib; injectable for tests)
# ---------------------------------------------------------------------------

def _default_transport(
    method: str, url: str, headers: dict, body: Optional[bytes]
) -> "tuple[int, bytes]":
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15.0) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:  # non-200 surfaced as its status
        return exc.code, exc.read() if hasattr(exc, "read") else b""


# ---------------------------------------------------------------------------
# Auth (OAuth2 client-credentials)
# ---------------------------------------------------------------------------

def build_basic_auth_header(client_id: str, client_secret: str) -> str:
    """``Authorization: Basic base64(client_id:client_secret)`` header value."""
    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def fetch_token(
    client_id: str, client_secret: str, transport: Transport
) -> str:
    """Mint an access token via the client-credentials grant. Fail-closed on any
    non-200 or a response missing ``access_token``."""
    headers = {
        "Authorization": build_basic_auth_header(client_id, client_secret),
        "Content-Type": "application/x-www-form-urlencoded",
    }
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode(
        "utf-8"
    )
    status, raw = transport("POST", TOKEN_URL, headers, body)
    if status != 200:
        raise AdapterError(f"token endpoint returned non-200 status: {status}")
    try:
        doc = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AdapterError("token response is not valid JSON") from exc
    token = doc.get("access_token") if isinstance(doc, dict) else None
    if not isinstance(token, str) or not token:
        raise AdapterError("token response missing access_token")
    return token


# ---------------------------------------------------------------------------
# Request construction + one bounded chain pull
# ---------------------------------------------------------------------------

def build_chain_url(root: str, option_type: str, date_str: str) -> str:
    """Bounded delayed option-and-underlying-quotes URL for one (root,
    option_type) on ``date_str`` (yyyy-MM-dd)."""
    query = urllib.parse.urlencode(
        {
            "symbol": SYMBOL,
            "root": root,
            "option_type": option_type,
            "date": date_str,
        }
    )
    return f"{BASE_URL}?{query}"


def fetch_chain(
    access_token: str,
    root: str,
    option_type: str,
    date_str: str,
    transport: Transport,
) -> dict:
    """GET one bounded chain response as a dict. Fail-closed on non-200/non-JSON
    or a response that is not a JSON object."""
    headers = {"Authorization": f"Bearer {access_token}"}
    url = build_chain_url(root, option_type, date_str)
    status, raw = transport("GET", url, headers, None)
    if status != 200:
        raise AdapterError(
            f"chain endpoint returned non-200 status {status} "
            f"(root={root}, option_type={option_type})"
        )
    try:
        doc = json.loads(raw)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise AdapterError("chain response is not valid JSON") from exc
    if not isinstance(doc, dict):
        raise AdapterError("chain response is not a JSON object")
    return doc


# ---------------------------------------------------------------------------
# Normalization -> producer payload shape
# ---------------------------------------------------------------------------

def compose_occ_symbol(
    root: str, expiry: str, option_type: str, strike: object
) -> str:
    """Build the 21-char OCC ``option`` string the producer's ``_OCC_RE`` parses:
    ``ROOT + yymmdd + C/P + strike*1000 as 8 digits``. Fail-closed on any
    structurally invalid identity field."""
    if root not in ROOTS:
        raise AdapterError(f"unexpected option root: {root!r}")
    if option_type not in OPTION_TYPES:
        raise AdapterError(f"unexpected option_type: {option_type!r}")
    try:
        yymmdd = datetime.strptime(expiry, "%Y-%m-%d").strftime("%y%m%d")
    except (TypeError, ValueError) as exc:
        raise AdapterError(f"unparseable expiry: {expiry!r}") from exc
    if isinstance(strike, bool) or not isinstance(strike, (int, float)):
        raise AdapterError(f"non-numeric strike: {strike!r}")
    thousandths = int(round(float(strike) * 1000))
    if thousandths < 0 or thousandths > 99_999_999:
        raise AdapterError(f"strike out of OCC 8-digit range: {strike!r}")
    return f"{root}{yymmdd}{option_type}{thousandths:08d}"


def normalize_option(record: object) -> dict:
    """Map one All Access option record to the producer row shape
    ``{option, gamma, open_interest}``. Identity fields (root/expiry/option_type/
    strike) MUST be present -- their absence is a structural violation and is
    fail-closed. ``gamma`` and ``open_interest`` are passed through verbatim
    (including missing/None) so the producer's per-row admissibility does the
    documented exclusion accounting."""
    if not isinstance(record, dict):
        raise AdapterError("option record is not a JSON object")
    missing = [f for f in _REQUIRED_OPTION_FIELDS if f not in record]
    if missing:
        raise AdapterError(f"option record missing identity fields: {missing}")
    option = compose_occ_symbol(
        record["root"], record["expiry"], record["option_type"],
        record["strike"],
    )
    return {
        "option": option,
        "gamma": record.get("gamma"),
        "open_interest": record.get("open_interest"),
    }


def compose_feed_timestamp(date_str: str, time_of_day: object) -> str:
    """Authoritative UTC feed timestamp for the producer: query ``date_str``
    (ET trading date) + provider ``time_of_day`` (ET, ``HH:MM:SS[.mmm]``) ->
    ``"YYYY-MM-DD HH:MM:SS"`` in UTC. Fail-closed on any malformed part; never a
    producer-clock fallback."""
    if not isinstance(time_of_day, str):
        raise AdapterError(f"non-string provider timestamp: {time_of_day!r}")
    hms = time_of_day.split(".", 1)[0]  # drop optional milliseconds
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        t = datetime.strptime(hms, "%H:%M:%S").time()
    except (TypeError, ValueError) as exc:
        raise AdapterError(
            f"unparseable feed date/time: {date_str!r} {time_of_day!r}"
        ) from exc
    et = datetime.combine(d, t, tzinfo=MARKET_TZ)
    return et.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def normalize(responses: list, date_str: str) -> dict:
    """Merge the call-plan responses into the exact producer payload shape:
    ``{"timestamp": <utc str>, "data": {"current_price": float, "options": [...]}}``.

    Spot basis is ``underlying_last_trade_price`` (fail-closed if absent/invalid).
    The emitted feed timestamp is the OLDEST across responses (conservative
    freshness). Fail-closed if the plan produced no responses."""
    if not responses:
        raise AdapterError("no responses to normalize")

    spot: Optional[float] = None
    feed_ts: Optional[str] = None
    options: list = []
    for doc in responses:
        raw_options = doc.get("options")
        if not isinstance(raw_options, list):
            raise AdapterError("chain response missing options array")
        options.extend(normalize_option(rec) for rec in raw_options)

        if spot is None:
            candidate = doc.get(_UNDERLYING_PRICE_FIELD)
            if (
                not isinstance(candidate, bool)
                and isinstance(candidate, (int, float))
                and candidate > 0
            ):
                spot = float(candidate)

        ts = compose_feed_timestamp(date_str, doc.get("timestamp"))
        # Same-day UTC "YYYY-MM-DD HH:MM:SS" strings sort chronologically.
        feed_ts = ts if feed_ts is None or ts < feed_ts else feed_ts

    if spot is None:
        raise AdapterError(
            f"no valid {_UNDERLYING_PRICE_FIELD} in any response"
        )
    return {
        "timestamp": feed_ts,
        "data": {"current_price": spot, "options": options},
    }


# ---------------------------------------------------------------------------
# Seam: a producer-shaped fetch_fn
# ---------------------------------------------------------------------------

def pull_payload(
    client_id: str,
    client_secret: str,
    date_str: str,
    *,
    transport: Optional[Transport] = None,
    call_plan=CALL_PLAN,
) -> dict:
    """Authenticate, issue the bounded call plan, and return the normalized
    producer payload dict. Fail-closed throughout."""
    tx = transport or _default_transport
    token = fetch_token(client_id, client_secret, tx)
    responses = [
        fetch_chain(token, root, ot, date_str, tx) for root, ot in call_plan
    ]
    return normalize(responses, date_str)


def make_fetch_fn(
    client_id: str,
    client_secret: str,
    date_str: str,
    *,
    transport: Optional[Transport] = None,
    call_plan=CALL_PLAN,
) -> Callable[[str], "tuple[int, bytes]"]:
    """Return a ``fetch_fn(url) -> (status, bytes)`` for ``gex_snapshot.run``.
    The ``url`` argument (the producer's recorded endpoint) is accepted but the
    adapter always talks to the sanctioned All Access endpoints. Any
    :class:`AdapterError` propagates and the producer fail-closes."""

    def fetch_fn(url: str) -> "tuple[int, bytes]":
        payload = pull_payload(
            client_id, client_secret, date_str,
            transport=transport, call_plan=call_plan,
        )
        return 200, json.dumps(payload).encode("utf-8")

    return fetch_fn


# ---------------------------------------------------------------------------
# Manual invocation (reads credentials via the established dotenv/getenv pattern)
# ---------------------------------------------------------------------------

def _today_et() -> str:
    return datetime.now(MARKET_TZ).date().isoformat()


def main(argv: Optional[list] = None) -> int:
    import os

    parser = argparse.ArgumentParser(
        description="Cboe All Access GEX adapter -> gex_snapshot producer"
    )
    parser.add_argument(
        "--date", default=None, help="trading date yyyy-MM-dd (default: today ET)"
    )
    parser.add_argument("--artifact-path", default=None)
    args = parser.parse_args(argv)

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:  # dotenv optional at runtime; env may already be populated
        pass

    client_id = os.getenv(ENV_CLIENT_ID)
    client_secret = os.getenv(ENV_CLIENT_SECRET)
    if not client_id or not client_secret:
        print(
            json.dumps(
                {
                    "gex_allaccess_adapter": "missing credentials",
                    "need_env": [ENV_CLIENT_ID, ENV_CLIENT_SECRET],
                }
            ),
            file=sys.stderr,
        )
        return 1  # fail-closed: no silent fallback to any other acquisition path

    date_str = args.date or _today_et()

    # Import the unmodified producer as a tools/ sibling and drive it with the
    # adapter fetch_fn. url=BASE_URL so the artifact's endpoint field is honest.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import gex_snapshot  # noqa: E402

    fetch_fn = make_fetch_fn(client_id, client_secret, date_str)
    kwargs = {"fetch_fn": fetch_fn, "url": BASE_URL}
    if args.artifact_path:
        kwargs["artifact_path"] = Path(args.artifact_path)
    return gex_snapshot.run(**kwargs)


if __name__ == "__main__":
    raise SystemExit(main())
