"""PRD-333: GEX synthetic reference carrier (display-only, educational).

A frozen synthetic SPX example rendered through the existing ``gex_card`` geometry
as one labeled disclosure at the WATCHING -> DETAILS boundary. Its ONLY input is
one bundled resource beside this module (no caller path, clock, network, or
snapshot input), so it can never show current-market data by construction, not
merely by label. The envelope carries NONE of the production identity fields:
current admission rejects it and it rejects any production snapshot. Imports only
``gex_card``, never the current artifact. (R3/R4/R5/R7/R11)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from cuttingboard.delivery import gex_card

# The one bundled resource. Module-relative and hardcoded (no caller path).
_RESOURCE = Path(__file__).parent / "data" / "gex_reference_v1.json"

_REF_SCHEMA_VERSION = 1
_KIND = "synthetic_reference"
_SCENARIO_ID = "spx-structure-v1"
_INSTRUMENT = "SPX"
# Production identity fields that must NEVER appear in a reference envelope (R3/R4).
_FORBIDDEN_PRODUCTION_FIELDS = ("schema_version", "source", "data_delay", "fetched_at_utc")

# Reference ladder labeling: synthetic identity into the accessible name + a caption.
_REF_LADDER = gex_card.LadderLabel(
    aria_prefix="Reference synthetic SPX example, not live market data. ",
    caption="REFERENCE &middot; SYNTHETIC SPX EXAMPLE",
)

# Scoped presentation, emitted inside the fragment only (global _CSS unchanged);
# summary >= 44px touch target, kv-grid wrap fix, wide table scrolls in place.
_STYLE = (
    "  <style>#gex-reference{border-top:1px solid #222;margin:0 0 1rem;padding:12px 0}"
    "#gex-reference>summary{cursor:pointer;list-style:none;color:#aaa;font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;min-height:44px;display:flex;align-items:center;flex-wrap:wrap;gap:.15rem .5rem}"
    "#gex-reference>summary .label{text-transform:none;letter-spacing:0}"
    "#gex-reference h2{font-size:0.8rem;color:#9aa4b2;text-transform:uppercase;letter-spacing:.05em;margin:2px 0 6px}"
    "#gex-reference .gex-bins{display:block;overflow-x:auto;max-width:100%}"
    "#gex-reference .kv-grid{grid-template-columns:minmax(0,1fr) auto;column-gap:0.6rem}"
    "#gex-reference .kv-grid .label{white-space:normal;overflow-wrap:anywhere}#gex-reference .kv-grid .value{text-align:right;white-space:nowrap}"
    "#gex-reference .gex-reference-guide{color:#8a93a0;text-transform:none;letter-spacing:0;font-size:0.72rem;line-height:1.35;margin-top:8px}</style>"
)

# ~90-word reading guide; avoids directional/predictive vocabulary (R5).
_GUIDE = (
    "Read the example's spot against the distribution of modeled call and put magnitudes across strikes. "
    "The NET* tick is call minus put under the configured convention; it is a modeled-magnitude difference only. "
    "In TAPE, separately note volatility, rates, DXY and regime; use NEXT EVENT for timing and SPY SESSION for its own price context. "
    "Those live observations do not update this frozen example. Watch how the cockpit changes over successive sessions, "
    "without treating this fixed structure as an explanation of any single day's move. SPX strikes are not SPY price levels."
)

_FOOTNOTE = (
    "NET* = CALL MODELED MAGNITUDE - PUT MODELED MAGNITUDE under a configured "
    "call-plus / put-minus convention; a modeled magnitude difference only. "
    "CALL+PUT MODELED MAGNITUDE = CALL MODELED MAGNITUDE + PUT MODELED MAGNITUDE, "
    "no sign assignment."
)


@dataclass(frozen=True)
class GexReference:
    """Immutable synthetic reference; carries NO timestamp/as-of (not an observation)."""

    scenario_id: str
    instrument: str
    synthetic_source: str
    authoring_basis_sha: str
    authoring_helper_path: str
    net_usd: float
    dominant: tuple[float, float]
    call_wall: tuple[float, float] | None
    put_wall: tuple[float, float] | None
    zero_dte_share: float | None
    profile: gex_card.GexProfile


def _load_bundled() -> dict | None:
    """Read the one bundled resource; never raises. None on missing/malformed/
    non-dict (fail-loud -> unavailable disclosure)."""
    try:
        data = json.loads(_RESOURCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return data if isinstance(data, dict) else None


def build_reference(envelope) -> GexReference | None:
    """Strictly validate a reference envelope and build the immutable model, or
    return None (fail-loud, no fallback). Rejects any production snapshot and any
    laundered / renamed / provenance-stripped input."""
    if not isinstance(envelope, dict):
        return None
    if any(k in envelope for k in _FORBIDDEN_PRODUCTION_FIELDS):
        return None                                     # production identity present -> reject
    if (envelope.get("reference_schema_version") != _REF_SCHEMA_VERSION
            or envelope.get("kind") != _KIND
            or envelope.get("scenario_id") != _SCENARIO_ID
            or envelope.get("instrument") != _INSTRUMENT
            or envelope.get("observation_date") is not None):
        return None
    src = envelope.get("synthetic_source")
    sha = envelope.get("authoring_basis_sha")
    helper = envelope.get("authoring_helper_path")
    if not (isinstance(src, str) and src
            and isinstance(sha, str) and sha
            and isinstance(helper, str) and helper):
        return None                                     # missing provenance -> reject
    spot = gex_card._real(envelope.get("spot"))
    if spot is None or spot <= 0:
        return None
    net = gex_card._real(envelope.get("gex_total_1pct_usd"))
    if net is None:
        return None
    validated = gex_card._validate_carrier(envelope.get("by_strike") or {})
    if validated is None:
        return None
    kf, mills, call, put = validated
    if not gex_card._reconciles(kf, call, put, envelope):
        return None                                     # aggregate/anchor contradiction
    profile = gex_card._compute_profile(
        kf, mills, call, put, gex_card._anchor_bins(envelope), spot)
    if len(profile.window_bins) != 31:                  # defensive: window is always 31
        return None

    def _wall(key: str) -> tuple[float, float] | None:
        obj = envelope.get(key)
        if not isinstance(obj, dict):
            return None
        s = gex_card._real(obj.get("strike"))
        if s is None or s <= 0:
            return None
        return (s, (s / spot - 1.0) * 100.0)

    dom = _wall("dominant_net_gamma")
    if dom is None:                                     # dominant anchor is required
        return None
    zd = envelope.get("zero_dte")
    raw = zd.get("share") if isinstance(zd, dict) else None   # None = row omitted
    zshare = gex_card._real(raw)
    if raw is not None and (zshare is None or not (0.0 <= zshare <= 1.0)):
        return None                                         # present-but-degenerate -> reject (R8)
    return GexReference(
        scenario_id=_SCENARIO_ID, instrument=_INSTRUMENT, synthetic_source=src,
        authoring_basis_sha=sha, authoring_helper_path=helper,
        net_usd=net, dominant=dom,
        call_wall=_wall("call_wall"), put_wall=_wall("put_wall"),
        zero_dte_share=zshare, profile=profile,
    )


def _details_open(inner: list[str]) -> str:
    """Wrap inner lines in the labeled collapsed disclosure: always exactly one
    #gex-reference, always data-gex-kind="reference", never a current wrapper."""
    head = [
        '<details class="gex-reference" id="gex-reference" data-gex-kind="reference">',
        _STYLE,
        '  <summary>GEX REFERENCE &middot; SYNTHETIC EXAMPLE'
        '<span class="label">Learning context only &middot; current availability is '
        'shown in TAPE</span></summary>',
        '  <div class="gex-reference-body">',
    ]
    return "\n".join([*head, *inner, "  </div>", "</details>"])


def _unavailable() -> str:
    """R8: labeled disclosure, no numbers, no ladder, no fallback."""
    return _details_open(['    <div class="label">Reference example unavailable.</div>'])


def _render(ref: GexReference) -> str:
    rows = gex_card._core_rows(
        ref.net_usd, ref.dominant, ref.call_wall, ref.put_wall,
        ref.zero_dte_share, ref.profile)
    inner = [
        "    <h2>REFERENCE - SYNTHETIC SPX EXAMPLE</h2>",
        f'    <div class="label">Scenario: {ref.scenario_id} &middot; Instrument: '
        f'{ref.instrument} &middot; Observation date: none (synthetic)</div>',
        f'    <div class="label">Source: {ref.synthetic_source}</div>',
        '    <div class="kv-grid">',
        *rows,
        "    </div>",
        *gex_card._profile_block(ref.profile, _REF_LADDER),
        f'    <div class="gex-reference-guide">{_GUIDE}</div>',
        f'    <div class="label">{_FOOTNOTE}</div>',
    ]
    return _details_open(inner)


def render_reference_fragment() -> str:
    """The renderer's single entry point. Loads the one bundled resource and always
    returns exactly one labeled <details id="gex-reference">. No inputs: same bytes
    for every render (clock/current-market independent). Invalid/missing -> the
    labeled unavailable disclosure (R8)."""
    ref = build_reference(_load_bundled())
    return _unavailable() if ref is None else _render(ref)
