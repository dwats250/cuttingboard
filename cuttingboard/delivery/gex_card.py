"""GEX-2 free board card (PRD-309): baseline-neutral, display-only GEX context card.

Pure, stdlib-only consumer of ``logs/gex_snapshot.json`` (the GEX-1 sidecar) with
NO decision authority. Renders only a fresh, in-domain artifact; on any absence,
staleness, or domain violation it suppresses to nothing so the dashboard stays
byte-identical to the pre-GEX baseline (R1/R6/D6). All GEX validation and math
live here; the renderer only loads and emits. Imports no ``cuttingboard`` module;
imported only by the renderer (isolation R17).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

# Identity guards -- must match tools/gex_snapshot.py exactly (D5a / Event-2 F4).
_SOURCE = "cboe_delayed_quotes"
_DATA_DELAY = "~15 min delayed (REPORTED; Cboe delayed_quotes posture)"
_SCHEMA_VERSION = 1
_STALE_MAX = timedelta(hours=24)  # Q4 single freshness knob
_FUTURE_SKEW = timedelta(minutes=5)
_ET = ZoneInfo("America/New_York")

# The producer's exact recognized "unavailable" reason tokens (D5a coherence).
_REASONS = {
    "dominant_net_gamma": {"all_net_gamma_zero"},
    "call_wall": {"no_eligible_calls", "no_nonzero_call_gex"},
    "put_wall": {"no_eligible_puts", "no_nonzero_put_gex"},
}
_ZERO_DTE_REASON = "zero_abs_gex_denominator"
_INVALID = object()  # sentinel: reason/value incoherence -> suppress the whole card

# GEX-4 structural profile (per-strike carrier -> bounded strike ladder around spot).
_BIN_MILLS = 25_000           # 25-point bins, in integer strike-mills (OCC digits)
_HALF_BIN_MILLS = 12_500      # half-open interval half-width [b-12.5, b+12.5)
_WINDOW_HALF = 15             # 15 bins each side of the spot bin -> 31 contiguous bins
_OUTSIDE_THRESHOLD = 0.02     # a bin outside the window qualifies at >= 2% of chain call+put
_OUTSIDE_CAP = 6              # at most 6 outside rows on the compact line (table is uncapped)
_SCALE_UNITS = 112.0          # SVG units per max window extent (carried for the ladder slice)


def load_gex_snapshot(path: Path) -> dict | None:
    """Soft loader for the GEX sidecar: never raises; returns a dict on success,
    None on missing / malformed / non-dict, so a bad artifact never breaks publish."""
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _real(x) -> float | None:
    """Finite, non-boolean int/float -> float; else None (G6: invalid, not coerced)."""
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        return None
    return float(x)


def _wall_strike(obj, reasons):
    """Coherence for call/put/dominant (D5a/R15): a valid strike float; None (typed-
    unavailable via a recognized reason); or _INVALID (contradictory -> suppress)."""
    if not isinstance(obj, dict):
        return _INVALID
    strike, reason = obj.get("strike"), obj.get("reason")
    if strike is None:
        return None if reason in reasons else _INVALID
    s = _real(strike)
    if s is None or s <= 0 or reason is not None:
        return _INVALID
    return s


def _zero_dte_share(obj):
    """0DTE coherence + honest zero (D5a/R11/R15): a share float in [0,1] (incl. 0.0);
    None (typed-unavailable); or _INVALID (contradictory -> suppress)."""
    if not isinstance(obj, dict):
        return _INVALID
    share, reason = obj.get("share"), obj.get("reason")
    if share is None:
        return None if reason == _ZERO_DTE_REASON else _INVALID
    v = _real(share)
    if v is None or not (0.0 <= v <= 1.0) or reason is not None:
        return _INVALID
    return v


def _parse_aware(value) -> datetime | None:
    """ISO-8601 -> tz-aware datetime; None if not a string / naive / malformed."""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt if dt.tzinfo is not None else None


@dataclass(frozen=True)
class GexBin:
    """One 25-point window bin, exact half-open interval [center-12.5, center+12.5)."""

    center: float                           # bin center strike (= bin_mills / 1000)
    interval: tuple[float, float]           # [low, high); high belongs to the next bin
    call: float                             # CALL MODELED MAGNITUDE summed in the bin (>= 0)
    put: float                              # PUT MODELED MAGNITUDE summed in the bin (>= 0)
    call_plus_put: float                    # CALL+PUT MODELED MAGNITUDE (no sign assignment)
    model_net: float                        # MODEL NET* = call - put (configured convention)
    markers: tuple[str, ...]                # subset of ("C","P","D") raw-strike anchors here
    in_window: bool


@dataclass(frozen=True)
class OutsideBin:
    """A bin outside the window carrying >= 2% of chain CALL+PUT MODELED MAGNITUDE."""

    center: float
    distance_pct: float
    call: float
    put: float
    call_plus_put: float
    model_net: float


@dataclass(frozen=True)
class GexProfile:
    """The bounded structural profile derived from a domain-valid, reconciled
    per-strike carrier. All arithmetic is here; the presentation layer only
    formats. Model net is derived, never stored per strike upstream."""

    spot: float
    spot_bin_center: float
    window_bins: tuple[GexBin, ...]         # exactly 31, ascending by center
    chain_call_plus_put: float
    window_call_plus_put: float
    in_window_pct: float                    # window / chain * 100; out = 100 - in
    outside_bins: tuple[OutsideBin, ...]    # ALL qualifying, ascending (line caps at 6)
    outside_cap: int
    scale_denominator: float                # max over window bins of max(call, put)


@dataclass(frozen=True)
class GexCard:
    """Immutable, display-ready presentation model (no raw producer internals)."""

    net_usd: float
    dominant: tuple[float, float]           # (strike, distance_pct)
    call_wall: tuple[float, float] | None
    put_wall: tuple[float, float] | None
    zero_dte_share: float | None
    as_of_et: str
    profile: GexProfile | None = None       # GEX-4 structural profile, or None when absent


def _bin_mills(strike_mills: int) -> int:
    """Half-open bin: [b-12.5, b+12.5). Exact upper boundary goes to the higher
    bin. Integer arithmetic only (no float binning)."""
    return ((strike_mills + _HALF_BIN_MILLS) // _BIN_MILLS) * _BIN_MILLS


def _validate_carrier(by_strike):
    """Domain-validate the columnar carrier. Returns (kf, mills, call, put) on a
    well-formed carrier, or None when malformed (types, lengths, ordering, sign,
    or a strike that does not round-trip through integer mills). A malformed
    carrier suppresses the profile only; it never suppresses the core card."""
    strike = by_strike.get("strike")
    call = by_strike.get("call_modeled_magnitude_1pct_usd")
    put = by_strike.get("put_modeled_magnitude_1pct_usd")
    if not (isinstance(strike, list) and isinstance(call, list) and isinstance(put, list)):
        return None
    n = len(strike)
    if n < 1 or len(call) != n or len(put) != n:
        return None
    kf, mills, cout, pout = [], [], [], []
    prev = None
    for k, c, p in zip(strike, call, put):
        ks, cs, ps = _real(k), _real(c), _real(p)
        if ks is None or cs is None or ps is None:
            return None
        if ks <= 0 or cs < 0 or ps < 0:                 # strikes > 0; magnitudes >= 0
            return None
        m = int(round(ks * 1000))
        if m / 1000 != ks:                              # strike_mills round-trip exact
            return None
        if prev is not None and m <= prev:              # strictly ascending
            return None
        prev = m
        kf.append(ks)
        mills.append(m)
        cout.append(cs)
        pout.append(ps)
    return kf, mills, cout, pout


def _argmax_low(values: list) -> int:
    """Index of the maximum; on a tie the lowest strike wins. The carrier is
    ascending, so the FIRST index carrying the max is the lowest strike."""
    best = max(values)
    for i, v in enumerate(values):
        if v == best:
            return i
    return 0  # pragma: no cover - values is non-empty


def _anchor_ok(kf: list, magnitude: list, values: list, wall) -> bool:
    """Reconcile one raw-strike anchor against the carrier. ``magnitude`` selects
    the argmax (call, put, or |net|); ``values`` is the signed quantity the wall
    stores (call, -put, or net). Unavailable wall (strike None) is coherent only
    when the carrier carries no nonzero magnitude on that side."""
    if not isinstance(wall, dict):
        return False
    ws, wr, wg = wall.get("strike"), wall.get("reason"), wall.get("gex_1pct_usd")
    if ws is None:
        return wr is not None and max(magnitude) == 0.0
    if wr is not None:
        return False
    i = _argmax_low(magnitude)
    return kf[i] == ws and values[i] == wg


def _reconciles(kf: list, call: list, put: list, snapshot) -> bool:
    """A domain-valid carrier must agree with the core total and all three raw
    anchors, else the artifact is internally incoherent (whole card suppressed)."""
    total = _real(snapshot.get("gex_total_1pct_usd"))
    if total is None:
        return False
    if math.fsum(v for c, p in zip(call, put) for v in (c, -p)) != total:
        return False
    net = [c - p for c, p in zip(call, put)]
    return (
        _anchor_ok(kf, call, call, snapshot.get("call_wall"))
        and _anchor_ok(kf, put, [-p for p in put], snapshot.get("put_wall"))
        and _anchor_ok(kf, [abs(x) for x in net], net, snapshot.get("dominant_net_gamma"))
    )


def _anchor_bins(snapshot) -> dict:
    """Map each available core anchor strike to its containing bin (C/P/D)."""
    out = {}
    for mark, key in (("C", "call_wall"), ("P", "put_wall"), ("D", "dominant_net_gamma")):
        obj = snapshot.get(key)
        if isinstance(obj, dict) and obj.get("strike") is not None:
            s = _real(obj.get("strike"))
            if s is not None:
                out[mark] = _bin_mills(int(round(s * 1000)))
    return out


def _build_profile(by_strike, snapshot, spot_val: float):
    """Return a GexProfile, or None (profile absent: carrier absent, typed-
    unavailable, or malformed -> core card unchanged), or _INVALID (a domain-valid
    carrier that contradicts the core -> suppress the whole card)."""
    if not isinstance(by_strike, dict):
        return None                                     # absent / non-dict -> profile absent
    if by_strike.get("reason") is not None:
        return None                                     # typed-unavailable (settlement/other)
    validated = _validate_carrier(by_strike)
    if validated is None:
        return None                                     # malformed columnar carrier
    kf, mills, call, put = validated
    if not _reconciles(kf, call, put, snapshot):
        return _INVALID                                 # contradicts core -> suppress card
    return _compute_profile(kf, mills, call, put, snapshot, spot_val)


def _compute_profile(kf, mills, call, put, snapshot, spot_val: float) -> GexProfile:
    """All GEX-4 binning/window/outside arithmetic. Pure; deterministic order."""
    bin_call: dict = {}
    bin_put: dict = {}
    for m, c, p in zip(mills, call, put):
        b = _bin_mills(m)
        bin_call.setdefault(b, []).append(c)
        bin_put.setdefault(b, []).append(p)

    def bcall(b: int) -> float:
        return math.fsum(bin_call.get(b, ()))

    def bput(b: int) -> float:
        return math.fsum(bin_put.get(b, ()))

    chain_cpp = math.fsum([*call, *put])
    center = _bin_mills(round(spot_val * 1000))
    window = [center + (i - _WINDOW_HALF) * _BIN_MILLS for i in range(2 * _WINDOW_HALF + 1)]
    window_set = set(window)
    anchors = _anchor_bins(snapshot)

    window_bins = []
    scale_denom = 0.0
    win_parts = []
    for b in window:
        cc, pp = bcall(b), bput(b)
        win_parts.append(cc)
        win_parts.append(pp)
        scale_denom = max(scale_denom, cc, pp)
        window_bins.append(GexBin(
            center=b / 1000,
            interval=((b - _HALF_BIN_MILLS) / 1000, (b + _HALF_BIN_MILLS) / 1000),
            call=cc, put=pp, call_plus_put=cc + pp, model_net=cc - pp,
            markers=tuple(m for m in ("C", "P", "D") if anchors.get(m) == b),
            in_window=True,
        ))
    window_cpp = math.fsum(win_parts)

    outside = []
    if chain_cpp > 0.0:                                 # zero-denominator guard (0 >= 0 excluded)
        threshold = _OUTSIDE_THRESHOLD * chain_cpp
        for b in sorted(set(bin_call) | set(bin_put)):
            if b in window_set:
                continue
            cc, pp = bcall(b), bput(b)
            if cc + pp >= threshold:
                outside.append(OutsideBin(
                    center=b / 1000, distance_pct=(b / 1000 / spot_val - 1.0) * 100.0,
                    call=cc, put=pp, call_plus_put=cc + pp, model_net=cc - pp,
                ))

    in_pct = (window_cpp / chain_cpp * 100.0) if chain_cpp > 0.0 else 0.0
    return GexProfile(
        spot=spot_val, spot_bin_center=center / 1000,
        window_bins=tuple(window_bins), chain_call_plus_put=chain_cpp,
        window_call_plus_put=window_cpp, in_window_pct=in_pct,
        outside_bins=tuple(outside), outside_cap=_OUTSIDE_CAP, scale_denominator=scale_denom,
    )


def build_gex_card(snapshot, *, now: datetime) -> GexCard | None:
    """Validate against the frozen admissibility domain (D5a) and build the model,
    or return None to suppress. ``now`` is injected so staleness is deterministic."""
    if not isinstance(snapshot, dict):
        return None
    sv = snapshot.get("schema_version")
    if not (isinstance(sv, int) and not isinstance(sv, bool) and sv == _SCHEMA_VERSION):
        return None
    if snapshot.get("source") != _SOURCE or snapshot.get("data_delay") != _DATA_DELAY:
        return None
    spot = snapshot.get("spot")
    spot_val = _real(spot.get("value")) if isinstance(spot, dict) else None
    if spot_val is None or spot_val <= 0:
        return None
    net = _real(snapshot.get("gex_total_1pct_usd"))
    if net is None:
        return None
    fetched = _parse_aware(snapshot.get("fetched_at_utc"))
    if fetched is None or (fetched - now) > _FUTURE_SKEW or (now - fetched) > _STALE_MAX:
        return None
    # Dominant anchor is required (Q6): unavailable OR invalid -> suppress the card.
    dom = _wall_strike(snapshot.get("dominant_net_gamma"), _REASONS["dominant_net_gamma"])
    if dom is _INVALID or dom is None:
        return None
    # Optional rows: invalid suppresses the card; typed-unavailable omits the row.
    call = _wall_strike(snapshot.get("call_wall"), _REASONS["call_wall"])
    put = _wall_strike(snapshot.get("put_wall"), _REASONS["put_wall"])
    zero = _zero_dte_share(snapshot.get("zero_dte"))
    if call is _INVALID or put is _INVALID or zero is _INVALID:
        return None

    def dist(strike: float) -> float:
        return (strike / spot_val - 1.0) * 100.0

    # GEX-4: derive the structural profile. A domain-valid carrier that
    # contradicts the core total/anchors makes the artifact internally incoherent
    # -> suppress the whole card. Absent/unavailable/malformed -> profile absent.
    profile = _build_profile(snapshot.get("by_strike"), snapshot, spot_val)
    if profile is _INVALID:
        return None

    return GexCard(
        net_usd=net,
        dominant=(dom, dist(dom)),
        call_wall=(call, dist(call)) if call is not None else None,
        put_wall=(put, dist(put)) if put is not None else None,
        zero_dte_share=zero,
        as_of_et=fetched.astimezone(_ET).strftime("%H:%M"),
        profile=profile,
    )


def _fmt_strike(strike: float) -> str:
    return f"{int(strike)}" if float(strike).is_integer() else f"{strike:g}"


def _fmt_net(net_usd: float) -> str:
    b = net_usd / 1e9
    return f"{'-' if b < 0 else '+'}${abs(b):.1f}B"


def _fmt_b(usd: float) -> str:
    """Unsigned modeled magnitude in $B, one decimal (e.g. 71.0B)."""
    return f"{usd / 1e9:.1f}B"


def _fmt_net_b(usd: float) -> str:
    """Signed MODEL NET* in $B with an explicit sign (e.g. +5.1B / -0.9B)."""
    b = usd / 1e9
    return f"{'-' if b < 0 else '+'}{abs(b):.1f}B"


def _kv(label: str, value: str) -> str:
    return f'    <div class="label">{label}</div><div class="value">{value}</div>'


def _row(label: str, pair: tuple[float, float]) -> str:
    strike, dist_pct = pair
    return _kv(label, f"{_fmt_strike(strike)} &nbsp; {dist_pct:+.2f}%")


def _outside_line(p: GexProfile) -> str:
    """The compact outside-bins line (capped at 6; the accessible table is full)."""
    total = len(p.outside_bins)
    if total == 0:
        return "OUTSIDE BINS >= 2% OF CHAIN CALL+PUT MODELED MAGNITUDE: NONE"
    body = "; ".join(
        f"{_fmt_strike(b.center)} ({b.distance_pct:+.2f}%) CALL+PUT MODELED "
        f"MAGNITUDE {_fmt_b(b.call_plus_put)} MODEL NET* {_fmt_net_b(b.model_net)}"
        for b in p.outside_bins[:p.outside_cap]
    )
    if total > p.outside_cap:
        return (f"{p.outside_cap} OF {total} OUTSIDE BINS >= 2% OF CHAIN CALL+PUT "
                f"MODELED MAGNITUDE SHOWN &middot; {total - p.outside_cap} MORE: {body}")
    return f"OUTSIDE BINS >= 2% OF CHAIN CALL+PUT MODELED MAGNITUDE: {body}"


def _accessible_table(p: GexProfile) -> list[str]:
    """The phone-inspectable full table: all 31 window bins + all outside bins.
    Plain HTML, no hover/JS reliance, exact per-bin vocabulary."""
    lines = [
        '  <details><summary class="label">ALL 31 BINS + OUTSIDE BINS</summary>',
        '    <table class="gex-bins"><thead><tr><th>BIN</th><th>INTERVAL</th>'
        '<th>CALL MODELED MAGNITUDE</th><th>PUT MODELED MAGNITUDE</th>'
        '<th>MODEL NET*</th></tr></thead><tbody>',
    ]
    for b in p.window_bins:
        lo, hi = b.interval
        mark = "".join(b.markers)
        label = f"{_fmt_strike(b.center)}{(' ' + mark) if mark else ''}"
        lines.append(
            f'    <tr><td>{label}</td><td>[{_fmt_strike(lo)}, {_fmt_strike(hi)})</td>'
            f'<td>{_fmt_b(b.call)}</td><td>{_fmt_b(b.put)}</td>'
            f'<td>{_fmt_net_b(b.model_net)}</td></tr>'
        )
    for b in p.outside_bins:
        lo = b.center - _HALF_BIN_MILLS / 1000
        hi = b.center + _HALF_BIN_MILLS / 1000
        lines.append(
            f'    <tr><td>{_fmt_strike(b.center)} (outside {b.distance_pct:+.2f}%)</td>'
            f'<td>[{_fmt_strike(lo)}, {_fmt_strike(hi)})</td>'
            f'<td>{_fmt_b(b.call)}</td><td>{_fmt_b(b.put)}</td>'
            f'<td>{_fmt_net_b(b.model_net)}</td></tr>'
        )
    lines.append("    </tbody></table></details>")
    return lines


def _profile_block(p: GexProfile) -> list[str]:
    """The GEX-4 text + accessible profile seam (no SVG ladder geometry yet):
    coverage line (both directions, summing to 100), spot label, outside-bins
    line, the full accessible table, and the anchor/bin/expiry disclosures."""
    in_i, out_i = round(p.in_window_pct), round(100.0 - p.in_window_pct)
    if in_i + out_i == 100:
        cov_in, cov_out = str(in_i), str(out_i)
    else:                                               # rounding broke the sum -> one decimal
        cov_in, cov_out = f"{p.in_window_pct:.1f}", f"{100.0 - p.in_window_pct:.1f}"
    lines = [
        f'  <div class="label">WINDOW SHOWS {cov_in}% OF CHAIN CALL+PUT MODELED '
        f'MAGNITUDE &middot; {cov_out}% OUTSIDE</div>',
        f'  <div class="label">SPX CASH SPOT {_fmt_strike(p.spot)}</div>',
        f'  <div class="label">{_outside_line(p)}</div>',
    ]
    lines.extend(_accessible_table(p))
    lines.extend([
        '  <div class="label">C / P / D = RAW-STRIKE ANCHORS (LARGEST CALL-CONTRACT '
        'MAGNITUDE STRIKE, LARGEST PUT-CONTRACT MAGNITUDE STRIKE, LARGEST RAW-STRIKE '
        '|MODEL NET|) SHOWN IN THEIR 25-PT BIN; NOT THE BIN MAXIMUM.</div>',
        '  <div class="label">31 x 25-PT BINS [B-12.5, B+12.5) AROUND THE SPX CASH '
        'SPOT BIN; RECENTERS IN 25-PT STEPS. BIN MODEL NET CAN NEAR-BALANCE ACROSS '
        'DIFFERENT STRIKES.</div>',
        '  <div class="label">All expirations combined; expiry mix hidden. SPX and '
        'SPXW combined; AM/PM settlement timing not modeled.</div>',
    ])
    return lines


def render_gex_card_html(card: GexCard | None) -> str:
    """Format the model to a compact HTML fragment; empty string when suppressed.
    Reuses existing dashboard CSS classes and adds no styles (D7/R1). Core rows
    carry the GEX-4 vocabulary; the profile block (text + accessible table) is
    emitted only when a reconciled per-strike carrier is present."""
    if card is None:
        return ""
    rows = [
        _kv("MODEL NET*", _fmt_net(card.net_usd)),
        _row("LARGEST RAW-STRIKE |MODEL NET|", card.dominant),
    ]
    if card.call_wall is not None:
        rows.append(_row("LARGEST CALL-CONTRACT MAGNITUDE STRIKE", card.call_wall))
    if card.put_wall is not None:
        rows.append(_row("LARGEST PUT-CONTRACT MAGNITUDE STRIKE", card.put_wall))
    if card.zero_dte_share is not None:
        rows.append(_kv("0DTE", f"{card.zero_dte_share * 100:.1f}%"))
    if card.profile is not None:
        rows.append(_kv("CALL+PUT MODELED MAGNITUDE", _fmt_b(card.profile.chain_call_plus_put)))

    lines = [
        '<div class="block" id="gex-context">',
        '  <h2>GEX <span class="label">(context only)</span></h2>',
        '  <div class="kv-grid">',
        *rows,
        "  </div>",
    ]
    if card.profile is not None:
        lines.extend(_profile_block(card.profile))

    footnote = ("* MODEL NET = CALL MODELED MAGNITUDE - PUT MODELED MAGNITUDE. "
                "Configured call-plus / put-minus convention; participant and "
                "dealer positioning are not measured.")
    if card.profile is not None:
        footnote += (" CALL+PUT MODELED MAGNITUDE = CALL MODELED MAGNITUDE + "
                     "PUT MODELED MAGNITUDE, no sign assignment.")
    lines.extend([
        f'  <div class="label">as of {card.as_of_et} ET &middot; Cboe ~15m delayed source</div>',
        f'  <div class="label">{footnote}</div>',
        "</div>",
    ])
    return "\n".join(lines)


def render_fragment(snapshot, *, now: datetime) -> str:
    """Compose loader-validated model -> HTML. Empty string suppresses the card."""
    return render_gex_card_html(build_gex_card(snapshot, now=now))
