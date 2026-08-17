"""GEX-0 CBOE evidence-integrity guards (doctrine-scoped; not production code).

These guards run against the COMMITTED evidence artifacts only. They are
deliberately network-free so they are deterministic and reproducible. They live
inside the GEX-0 evidence directory (not tests/) because GEX-0 authorizes no
production files; CI's `pytest tests/ -q` therefore does not select them. Run
them directly:

    python -m pytest audits/gex-0-cboe-evidence-2026-08/test_gex0_cboe_evidence.py -q

Three guards, each with a mutation obligation (doctrine hardening invariant 4 —
every guard ships a red test):

  1. fetch-shape guard   : a response row missing any load-bearing field is
                           FLAGGED, not silently accepted.  Neutering the guard
                           to always-pass turns test_fetch_shape_* red.
  2. excerpt guard       : committed evidence contains NO full contract array
                           (no list longer than EXCERPT_CAP).  Dumping the chain
                           or raising the cap in the data turns
                           test_excerpt_has_no_full_chain red.
  3. claim/evidence guard: every field the packet CLAIMS observed is present in
                           the committed excerpt.  Claiming an unobserved field
                           turns test_packet_claims_match_evidence red.
"""

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVIDENCE_DIR = HERE / "evidence"
PACKET = HERE / "GEX_0_CBOE_PROVIDER_EVIDENCE_PACKET_2026-08-17.md"
# Evidence is committed as markdown-wrapped json (the repo-wide *.json gitignore
# would otherwise drop raw .json). Each file holds one fenced ```json block.
SAMPLE_FILES = ["spy_sample.md", "spx_sample.md"]


def _load_sample(name):
    text = (EVIDENCE_DIR / name).read_text()
    m = re.search(r"```json\s*(\{.*\})\s*```", text, re.DOTALL)
    assert m, f"{name} is missing its fenced json evidence block"
    return json.loads(m.group(1))

# Small cap: 1-2 partial rows are permitted; a real chain (14k/30k rows) is not.
EXCERPT_CAP = 5

# §4.3 load-bearing per-contract fields the fetch-shape guard requires.
REQUIRED_CONTRACT_FIELDS = [
    "open_interest", "gamma", "delta", "theta", "vega", "rho",
    "iv", "bid", "ask", "volume", "last_trade_time", "prev_day_close", "theo",
]


# --------------------------------------------------------------------------- #
# Guard 1: fetch-shape                                                         #
# --------------------------------------------------------------------------- #
def missing_load_bearing_fields(row):
    """Return the list of REQUIRED_CONTRACT_FIELDS absent/None in a contract row.

    Fail-loud posture: an empty list means the row is complete; a non-empty
    list is the flag. This is the single function the fetch-shape guard is built
    on — neutering it to always return [] turns the negative test red.
    """
    return [f for f in REQUIRED_CONTRACT_FIELDS
            if f not in row or row[f] is None]


def test_fetch_shape_flags_missing_field():
    """A row missing a load-bearing field MUST be flagged (no silent accept)."""
    complete = {f: 1 for f in REQUIRED_CONTRACT_FIELDS}
    assert missing_load_bearing_fields(complete) == []
    broken = dict(complete)
    del broken["gamma"]
    flagged = missing_load_bearing_fields(broken)
    assert "gamma" in flagged, "guard failed to flag a missing load-bearing field"


def test_fetch_shape_committed_rows_are_complete():
    """The committed excerpt rows themselves carry every load-bearing field."""
    for name in SAMPLE_FILES:
        data = _load_sample(name)
        rows = data["sample_contracts"]
        assert rows, f"{name} has no sample_contracts"
        for i, row in enumerate(rows):
            missing = missing_load_bearing_fields(row)
            assert missing == [], f"{name} row {i} missing {missing}"


# --------------------------------------------------------------------------- #
# Guard 2: excerpt cap (no full chain committed)                              #
# --------------------------------------------------------------------------- #
def _long_lists(obj, path="$"):
    """Yield (path, length) for every list longer than EXCERPT_CAP, recursively."""
    if isinstance(obj, list):
        if len(obj) > EXCERPT_CAP:
            yield (path, len(obj))
        for i, v in enumerate(obj):
            yield from _long_lists(v, f"{path}[{i}]")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from _long_lists(v, f"{path}.{k}")


def test_excerpt_has_no_full_chain():
    """No committed evidence JSON may contain a list longer than EXCERPT_CAP."""
    for name in SAMPLE_FILES:
        data = _load_sample(name)
        offenders = list(_long_lists(data))
        assert offenders == [], f"{name} commits a full array: {offenders}"
        # sample_contracts is explicitly capped
        assert len(data["sample_contracts"]) <= EXCERPT_CAP


# --------------------------------------------------------------------------- #
# Guard 3: packet claims match committed evidence                             #
# --------------------------------------------------------------------------- #
CLAIM_MARKER = "CLAIMED-OBSERVED-FIELDS"


def _load_packet_claims():
    text = PACKET.read_text()
    idx = text.find(CLAIM_MARKER)
    assert idx != -1, f"packet is missing the {CLAIM_MARKER} marker block"
    block = re.search(r"```json\s*(\{.*?\})\s*```", text[idx:], re.DOTALL)
    assert block, "no ```json claim block after the marker"
    return json.loads(block.group(1))


def test_packet_claims_match_evidence():
    """Every field the packet claims observed must exist in the committed excerpt."""
    claims = _load_packet_claims()
    # union of fields present across both underlyings' excerpts
    contract_keys, underlying_keys = set(), set()
    for name in SAMPLE_FILES:
        data = _load_sample(name)
        for row in data["sample_contracts"]:
            contract_keys |= set(row.keys())
        underlying_keys |= set((data.get("underlying") or {}).keys())
    for f in claims.get("contract_fields", []):
        assert f in contract_keys, f"packet claims contract field '{f}' not in excerpt"
    for f in claims.get("underlying_fields", []):
        assert f in underlying_keys, f"packet claims underlying field '{f}' not in excerpt"
