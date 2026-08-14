"""Contract + core tests for the PRD-302 Slice-A campaign control plane tool.

Tests-first (RED before tools/campaign_control.py, .github/campaign/*, and
.github/workflows/campaign_control.yml exist). Import isolation follows the
macro-awareness pattern: add tools/ to sys.path and import by plain name.

Slice A only: fixed synthetic event, non-authoritative proposed charge, no
network, and no repository-authoritative/issue/PR/comment publication (the job
log and a one-day artifact remain observable). See docs/prd_history/PRD-302.md.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"
_CAMPAIGN_DIR = _REPO_ROOT / ".github" / "campaign"
_SCHEMA_PATH = _CAMPAIGN_DIR / "charge.schema.json"
_PROMPT_PATH = _CAMPAIGN_DIR / "charge_prompt.md"

if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import campaign_control as cc  # noqa: E402 (must follow sys.path setup)

_GOOD_SHA = "0123456789abcdef0123456789abcdef01234567"
_OTHER_SHA = "fedcba9876543210fedcba9876543210fedcba98"


# --------------------------------------------------------------------------
# builders
# --------------------------------------------------------------------------
def _event_dict(**over):
    d = {
        "schema": cc.SCHEMA_EVENT,
        "source_comment_id": 0,
        "campaign": "PRD-302",
        "event_id": "PRD-302-E01",
        "kind": "OWNER_DECISION",
        "pr_number": 1,
        "head_sha": _GOOD_SHA,
        "trigger": "OTHER_BOUNDARY",
        "authority_boundary": "EVIDENCE",
        "summary": "A bounded owner decision needs a proposal.",
        "options": [
            {"id": "A", "label": "Hold", "effect": "Keep the boundary."},
            {"id": "B", "label": "Amend", "effect": "Renew the boundary."},
        ],
        "recommended_option": "B",
    }
    d.update(over)
    return d


def _charge_dict(**over):
    d = {
        "schema": cc.SCHEMA_CHARGE,
        "event_id": "PRD-302-E01",
        "head_sha": _GOOD_SHA,
        "recommended_option": "B",
        "confidence": "HIGH",
        "rationale": "One concise paragraph.",
        "charge_markdown": "A copy-ready proposed instruction.",
    }
    d.update(over)
    return d


# --------------------------------------------------------------------------
# fixed synthetic event + SHA binding
# --------------------------------------------------------------------------
def test_make_dry_run_event_binds_trusted_sha():
    ev = cc.make_dry_run_event(_GOOD_SHA)
    assert ev.head_sha == _GOOD_SHA


def test_make_dry_run_event_has_fixed_synthetic_fields():
    ev = cc.make_dry_run_event(_GOOD_SHA)
    assert ev.source_comment_id == 0
    assert ev.pr_number == 1
    assert ev.campaign == "PRD-302"
    assert ev.event_id == "PRD-302-E01"
    assert ev.kind == "OWNER_DECISION"
    assert ev.recommended_option in {o.id for o in ev.options}


def test_make_dry_run_event_rejects_bad_sha():
    with pytest.raises(cc.CampaignError):
        cc.make_dry_run_event("not-a-sha")


# --------------------------------------------------------------------------
# strict event validation
# --------------------------------------------------------------------------
def test_normalized_event_accepts_valid():
    ev = cc.parse_event(_event_dict())
    assert ev.event_id == "PRD-302-E01"


def test_normalized_event_rejects_unknown_keys():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(extra="x"))


def test_normalized_event_rejects_missing_keys():
    d = _event_dict()
    del d["trigger"]
    with pytest.raises(cc.CampaignError):
        cc.parse_event(d)


def test_event_rejects_bad_schema():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(schema="wrong/v1"))


def test_event_rejects_bool_as_int_pr_number():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(pr_number=True))


def test_event_rejects_bool_as_source_comment_id():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(source_comment_id=False))


def test_event_rejects_bad_campaign_pattern():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(campaign="PRD-2"))


def test_event_rejects_bad_event_id_pattern():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(event_id="PRD-302-X1"))


def test_event_rejects_event_id_campaign_mismatch():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(event_id="PRD-303-E01"))


def test_event_rejects_bad_kind():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(kind="OTHER"))


def test_event_rejects_nonpositive_pr_number():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(pr_number=0))


def test_event_rejects_bad_head_sha():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(head_sha="ABC"))


def test_event_rejects_bad_trigger():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(trigger="NOPE"))


def test_event_accepts_every_trigger_literal():
    for t in cc.TRIGGERS:
        assert cc.parse_event(_event_dict(trigger=t)).trigger == t


def test_event_rejects_bad_authority_boundary():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(authority_boundary="NOPE"))


def test_event_accepts_every_boundary_literal():
    for b in cc.BOUNDARIES:
        assert cc.parse_event(_event_dict(authority_boundary=b)).authority_boundary == b


def test_event_rejects_empty_summary():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(summary=""))


def test_event_rejects_oversize_summary():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(summary="x" * 1201))


def test_event_rejects_control_char_in_summary():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(summary="bad\x07bell"))


def test_event_allows_newline_in_summary():
    assert cc.parse_event(_event_dict(summary="line1\nline2")).summary


def test_event_rejects_option_count_below_two():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(options=[{"id": "A", "label": "x", "effect": "y"}]))


def test_event_rejects_option_count_above_three():
    opts = [{"id": i, "label": "x", "effect": "y"} for i in ("A", "B", "C")]
    opts.append({"id": "A", "label": "x", "effect": "y"})
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(options=opts))


def test_event_rejects_duplicate_option_ids():
    opts = [{"id": "A", "label": "x", "effect": "y"},
            {"id": "A", "label": "z", "effect": "w"}]
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(options=opts))


def test_event_rejects_bad_option_id():
    opts = [{"id": "A", "label": "x", "effect": "y"},
            {"id": "D", "label": "z", "effect": "w"}]
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(options=opts))


def test_event_rejects_option_unknown_keys():
    opts = [{"id": "A", "label": "x", "effect": "y", "extra": 1},
            {"id": "B", "label": "z", "effect": "w"}]
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(options=opts))


def test_event_rejects_oversize_label():
    opts = [{"id": "A", "label": "x" * 81, "effect": "y"},
            {"id": "B", "label": "z", "effect": "w"}]
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(options=opts))


def test_event_rejects_oversize_effect():
    opts = [{"id": "A", "label": "x", "effect": "y" * 601},
            {"id": "B", "label": "z", "effect": "w"}]
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(options=opts))


def test_event_rejects_recommendation_not_in_options():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(recommended_option="C"))


def test_event_rejects_oversize_8192_bytes():
    big = "x" * 1200
    d = _event_dict(summary=big,
                    options=[{"id": "A", "label": "l", "effect": "e" * 600},
                             {"id": "B", "label": "l", "effect": "e" * 600},
                             {"id": "C", "label": "l", "effect": "e" * 600}])
    # inflate to exceed 8192 UTF-8 bytes via load path
    payload = json.dumps(d) + (" " * 9000)
    with pytest.raises(cc.CampaignError):
        cc.load_event_bytes(payload.encode("utf-8"))


def test_event_rejects_nul_byte():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(summary="a\x00b"))


# --------------------------------------------------------------------------
# strict charge validation + identity
# --------------------------------------------------------------------------
def test_valid_charge_matches_event_identity():
    ev = cc.parse_event(_event_dict())
    ch = cc.parse_charge(_charge_dict())
    # render enforces identity match; should not raise
    out = cc.render_charge(ev, ch)
    assert "PROPOSED OWNER CHARGE" in out


def test_charge_rejects_unknown_keys():
    with pytest.raises(cc.CampaignError):
        cc.parse_charge(_charge_dict(verification="i checked"))


def test_charge_rejects_missing_keys():
    d = _charge_dict()
    del d["confidence"]
    with pytest.raises(cc.CampaignError):
        cc.parse_charge(d)


def test_charge_rejects_bad_schema():
    with pytest.raises(cc.CampaignError):
        cc.parse_charge(_charge_dict(schema="x/v1"))


def test_charge_rejects_bad_confidence():
    with pytest.raises(cc.CampaignError):
        cc.parse_charge(_charge_dict(confidence="MAYBE"))


def test_charge_rejects_oversize_rationale():
    with pytest.raises(cc.CampaignError):
        cc.parse_charge(_charge_dict(rationale="x" * 2001))


def test_charge_rejects_oversize_markdown():
    with pytest.raises(cc.CampaignError):
        cc.parse_charge(_charge_dict(charge_markdown="x" * 6001))


def test_render_rejects_event_id_drift():
    ev = cc.parse_event(_event_dict())
    ch = cc.parse_charge(_charge_dict(event_id="PRD-302-E02"))
    with pytest.raises(cc.CampaignError):
        cc.render_charge(ev, ch)


def test_render_rejects_sha_drift():
    ev = cc.parse_event(_event_dict())
    ch = cc.parse_charge(_charge_dict(head_sha=_OTHER_SHA))
    with pytest.raises(cc.CampaignError):
        cc.render_charge(ev, ch)


def test_render_rejects_recommendation_drift():
    ev = cc.parse_event(_event_dict())
    ch = cc.parse_charge(_charge_dict(recommended_option="A"))
    # A is a valid option id but does not match the event recommendation (B)
    with pytest.raises(cc.CampaignError):
        cc.render_charge(ev, ch)


# --------------------------------------------------------------------------
# neutralization + wrapper + disclosure
# --------------------------------------------------------------------------
def test_neutralize_escapes_html_and_at():
    out = cc.neutralize('<b>@dwats250 & "x"</b>')
    assert "<b>" not in out
    assert "@dwats250" not in out
    assert "&#64;" in out
    assert "&lt;" in out


def test_rendered_charge_has_fixed_non_authority_wrapper():
    ev = cc.parse_event(_event_dict())
    ch = cc.parse_charge(_charge_dict())
    out = cc.render_charge(ev, ch)
    assert "PROPOSED OWNER CHARGE -- NOT AUTHORITY" in out
    assert "does not approve, resume, modify, dispatch, or merge" in out


def test_rendered_charge_has_requested_model_disclosure():
    ev = cc.parse_event(_event_dict())
    ch = cc.parse_charge(_charge_dict())
    out = cc.render_charge(ev, ch)
    assert "requested model; served identity unverified" in out


def test_untrusted_model_text_has_no_active_markup_or_mentions():
    ev = cc.parse_event(_event_dict())
    ch = cc.parse_charge(_charge_dict(
        charge_markdown='<script>x</script> @dwats250 [t](http://x)'))
    out = cc.render_charge(ev, ch)
    assert "<script>" not in out
    assert "@dwats250" not in out


def test_inert_content_is_rendered_as_data():
    ev = cc.parse_event(_event_dict())
    hostile = '<x>@dwats250 $(id) `x` ${{ secrets.X }} ::set-output name=y::z'
    ch = cc.parse_charge(_charge_dict(charge_markdown=hostile))
    out = cc.render_charge(ev, ch)
    # model content is confined to <pre> and HTML/mentions are neutralized;
    # shell/workflow tokens survive only as inert escaped display text (the
    # workflow-command-splice hazard is the workflow's concern, R10/structural).
    assert "<pre>" in out
    assert "<x>" not in out            # angle tag escaped, cannot open an element
    assert "&lt;x&gt;" in out          # ... it survives only as escaped text
    assert "@dwats250" not in out      # mention neutralized


# --------------------------------------------------------------------------
# atomic writes + safe stable errors
# --------------------------------------------------------------------------
def test_output_write_is_atomic(tmp_path):
    target = tmp_path / "out.md"
    cc.atomic_write(target, "hello")
    assert target.read_text() == "hello"
    # no sibling temp left behind
    assert list(tmp_path.iterdir()) == [target]


def test_failure_never_echoes_event_or_model_content():
    secret_marker = "SENSITIVE-MARKER-9c1"
    try:
        cc.parse_event(_event_dict(trigger=secret_marker))
    except cc.CampaignError as exc:
        assert secret_marker not in exc.message
        assert exc.code
    else:
        pytest.fail("expected CampaignError")


def test_error_has_stable_code():
    try:
        cc.parse_charge(_charge_dict(confidence="X"))
    except cc.CampaignError as exc:
        assert isinstance(exc.code, str) and exc.code
    else:
        pytest.fail("expected CampaignError")


# --------------------------------------------------------------------------
# loader robustness: event byte/control contract vs charge (no whole-charge cap)
# --------------------------------------------------------------------------
def test_charge_max_size_is_accepted_by_loader(tmp_path):
    # a schema-valid maximum charge serializes > 8192 bytes; the charge loader
    # must NOT impose the event's 8192-byte cap.
    big = _charge_dict(rationale="r" * 2000, charge_markdown="m" * 6000)
    p = tmp_path / "charge.json"
    p.write_text(json.dumps(big))
    assert len(p.read_bytes()) > cc.MAX_EVENT_BYTES
    ch = cc.load_charge_json(p)
    assert len(ch.charge_markdown) == 6000


def test_event_loader_rejects_tab_control_in_raw_bytes():
    # a TAB used as JSON whitespace is an ASCII control -> event allows only \n
    raw = ('{\n\t"schema": "%s"}' % cc.SCHEMA_EVENT).encode("utf-8")
    with pytest.raises(cc.CampaignError):
        cc.load_event_bytes(raw)


def test_event_loader_allows_newline_whitespace():
    ev = cc.load_event_bytes((json.dumps(_event_dict(), indent=2)).encode("utf-8"))
    assert ev.event_id == "PRD-302-E01"


def test_charge_rejects_unhashable_confidence_as_campaign_error():
    with pytest.raises(cc.CampaignError):
        cc.parse_charge(_charge_dict(confidence=[]))


def test_event_rejects_unhashable_trigger_as_campaign_error():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(trigger=[]))


def test_event_rejects_unhashable_recommended_option():
    with pytest.raises(cc.CampaignError):
        cc.parse_event(_event_dict(recommended_option=[]))


# --------------------------------------------------------------------------
# R7 SPLIT credential-isolation proof: fail-closed decision logic
# Amendment 2 replaces the single ancestor-o+x probe with a two-uid proof: a
# runner-side leg (runner uid) proving the canonical credential EXISTS and is
# runner-owned, and a codex-side leg (exact codex uid) proving /home/runner is
# non-traversable, every enumerated runner credential is unreadable, and only
# the isolated public inputs are readable / its output writable.
# --------------------------------------------------------------------------
def _runner_side(**kw):
    base = dict(runner_uid=1000, runner_root="/runner", runner_temp="/tmp",
                canonical_exists=True, canonical_owner_uid=1000)
    base.update(kw)
    return cc.evaluate_runner_side(**base)


def _codex_iso(**kw):
    base = dict(runner_uid=1000, codex_uid=2000, home_runner_traversable=False,
                credentials_readable=[("/runner/.credentials", False)],
                isolated_inputs_readable=[("/tmp/ws/campaign_control.py", True)],
                output_writable=True)
    base.update(kw)
    return cc.evaluate_codex_isolation(**base)


# --- runner-side leg (runner uid): canonical existence + ownership ----------
def test_runner_side_passes_when_canonical_present_and_owned():
    _runner_side()  # root+temp resolved, canonical exists and is runner-owned


def test_runner_side_fails_on_ambiguous_root():
    with pytest.raises(cc.CampaignError):
        _runner_side(runner_root="")


def test_runner_side_fails_on_missing_temp_source():
    with pytest.raises(cc.CampaignError):
        _runner_side(runner_temp="")


def test_runner_side_fails_when_canonical_absent():
    # absence fails closed: a missing credential must never read as "isolated"
    with pytest.raises(cc.CampaignError):
        _runner_side(canonical_exists=False, canonical_owner_uid=None)


def test_runner_side_fails_when_canonical_wrong_owner():
    with pytest.raises(cc.CampaignError):
        _runner_side(canonical_owner_uid=2000)


# --- codex-side leg (exact codex uid): isolation ---------------------------
def test_codex_iso_passes_when_isolated():
    _codex_iso()  # distinct uid, home non-traversable, creds unreadable, inputs ok


def test_codex_iso_fails_when_codex_uid_equals_runner_uid():
    with pytest.raises(cc.CampaignError):
        _codex_iso(codex_uid=1000)


def test_codex_iso_fails_when_home_runner_traversable():
    # the ancestor-o+x regression: ANY traversal into /home/runner fails closed
    with pytest.raises(cc.CampaignError):
        _codex_iso(home_runner_traversable=True)


def test_codex_iso_fails_when_no_credentials_enumerated():
    # an empty enumeration must not read as "nothing readable, therefore pass"
    with pytest.raises(cc.CampaignError):
        _codex_iso(credentials_readable=[])


def test_codex_iso_fails_when_a_credential_is_readable():
    # the exact failure of run 31763968329: a runner-owned credential readable
    with pytest.raises(cc.CampaignError):
        _codex_iso(credentials_readable=[("/runner/.credentials", True)])


def test_codex_iso_fails_when_any_enumerated_credential_readable():
    # every enumerated target must be unreadable, not only the first
    with pytest.raises(cc.CampaignError):
        _codex_iso(credentials_readable=[("/runner/.credentials", False),
                                         ("/runner/.runner", True)])


def test_codex_iso_fails_when_no_isolated_inputs():
    with pytest.raises(cc.CampaignError):
        _codex_iso(isolated_inputs_readable=[])


def test_codex_iso_fails_when_an_isolated_input_unreadable():
    with pytest.raises(cc.CampaignError):
        _codex_iso(isolated_inputs_readable=[("/tmp/ws/campaign_control.py", False)])


def test_codex_iso_fails_when_output_not_writable():
    with pytest.raises(cc.CampaignError):
        _codex_iso(output_writable=False)


# --- credential enumeration is paths-only (contents are never opened) -------
def test_enumerate_credentials_covers_basenames_and_temp_glob(tmp_path):
    root = tmp_path / "runner"
    temp = tmp_path / "temp"
    root.mkdir()
    temp.mkdir()
    (temp / "abc.credentials").write_text("x", encoding="utf-8")
    paths = cc.enumerate_credentials(str(root), str(temp))
    for b in cc.CREDENTIAL_BASENAMES:
        assert str(root / b) in paths
    assert str(temp / "abc.credentials") in paths


def test_enumerate_credentials_returns_paths_not_contents(tmp_path):
    # the enumeration yields path strings only; it never opens a credential
    root = tmp_path / "runner"
    root.mkdir()
    secret = root / ".credentials"
    secret.write_text("TOP-SECRET-TOKEN", encoding="utf-8")
    paths = cc.enumerate_credentials(str(root), "")
    assert str(secret) in paths
    assert all("TOP-SECRET-TOKEN" not in p for p in paths)


# --------------------------------------------------------------------------
# schema <-> validator drift guard + field-by-field diff (RED until schema lands)
# --------------------------------------------------------------------------
def _schema():
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


# Literal expected projection of charge.schema.json's properties. Exact-dict
# equality means ANY schema mutation (changed pattern/type/enum/length, added or
# removed key) fails the drift guard. Do NOT derive these from cc constants --
# the point is an independent lock.
_EXPECTED_CHARGE_PROPS = {
    "schema": {"type": "string", "const": "cuttingboard-owner-charge/v1"},
    "event_id": {"type": "string", "pattern": "^PRD-[0-9]{3}-E[0-9]{2}$"},
    "head_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
    "recommended_option": {"type": "string", "enum": ["A", "B", "C"]},
    "confidence": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
    "rationale": {"type": "string", "minLength": 1, "maxLength": 2000,
                  "pattern": "^(?:[^\\u0000-\\u001f\\u007f]|\\n)*$"},
    "charge_markdown": {"type": "string", "minLength": 1, "maxLength": 6000},
}
_EXPECTED_CHARGE_REQUIRED = ["schema", "event_id", "head_sha",
                             "recommended_option", "confidence", "rationale",
                             "charge_markdown"]
_EXPECTED_TRIGGERS = {"AUTHORITY_CONFLICT", "REVIEW_SPLIT", "FILES_LOC",
                      "MATERIALITY", "PORTABILITY", "NEW_CONSUMER",
                      "OTHER_BOUNDARY"}
_EXPECTED_BOUNDARIES = {"SEMANTICS", "GOVERNANCE", "FILES_LOC", "TRUST",
                        "PLATFORM", "CONSUMER", "EVIDENCE"}


def test_charge_schema_exact_projection():
    s = _schema()
    assert s["type"] == "object"
    assert s["additionalProperties"] is False
    assert set(s["required"]) == set(_EXPECTED_CHARGE_REQUIRED)
    assert set(s["properties"]) == set(_EXPECTED_CHARGE_PROPS)
    for key, spec in _EXPECTED_CHARGE_PROPS.items():
        assert s["properties"][key] == spec, key


def test_charge_schema_has_no_verification_field():
    s = _schema()
    assert all("verif" not in k and "attest" not in k for k in s["properties"])


def test_charge_schema_matches_validator_constants():
    # schema <-> handwritten validator equivalence (R12/R17)
    s = _schema()
    props = s["properties"]
    assert set(s["required"]) == cc.CHARGE_KEYS
    assert props["schema"]["const"] == cc.SCHEMA_CHARGE
    assert props["head_sha"]["pattern"] == cc.RE_SHA.pattern
    assert props["event_id"]["pattern"] == cc.RE_EVENT_ID.pattern
    assert set(props["recommended_option"]["enum"]) == set(cc.OPTION_IDS)
    assert set(props["confidence"]["enum"]) == set(cc.CONFIDENCE)
    assert props["rationale"]["maxLength"] == cc.MAX_RATIONALE_CHARS
    assert props["charge_markdown"]["maxLength"] == cc.MAX_CHARGE_CHARS


def test_event_vocabulary_is_locked_literally():
    # independent literal lock so a matching drift in impl + derived expectation
    # cannot evade the guard
    assert cc.TRIGGERS == _EXPECTED_TRIGGERS
    assert cc.BOUNDARIES == _EXPECTED_BOUNDARIES
    assert cc.KIND == "OWNER_DECISION"
    assert cc.OPTION_IDS == ("A", "B", "C")
    assert cc.MAX_EVENT_BYTES == 8192


def test_schema_and_validator_agree_on_a_sweep():
    for bad in (
        _charge_dict(schema="x/v1"),
        _charge_dict(confidence="X"),
        _charge_dict(recommended_option="Z"),
        _charge_dict(extra="k"),
    ):
        with pytest.raises(cc.CampaignError):
            cc.parse_charge(bad)


# --------------------------------------------------------------------------
# CLI surface (exact set)
# --------------------------------------------------------------------------
def _run_cli(*args):
    return subprocess.run(
        [sys.executable, str(_TOOLS_DIR / "campaign_control.py"), *args],
        capture_output=True, text=True)


def test_cli_make_dry_run_event(tmp_path):
    out = tmp_path / "event.json"
    r = _run_cli("make-dry-run-event", "--head-sha", _GOOD_SHA,
                 "--event-output", str(out))
    assert r.returncode == 0
    ev = json.loads(out.read_text())
    assert ev["head_sha"] == _GOOD_SHA
    assert ev["schema"] == cc.SCHEMA_EVENT


def test_cli_validate_charge(tmp_path):
    ev = tmp_path / "event.json"
    ch = tmp_path / "charge.json"
    out = tmp_path / "comment.md"
    _run_cli("make-dry-run-event", "--head-sha", _GOOD_SHA,
             "--event-output", str(ev))
    ch.write_text(json.dumps(_charge_dict(recommended_option="B")))
    r = _run_cli("validate-charge", "--event", str(ev), "--charge", str(ch),
                 "--comment-output", str(out))
    assert r.returncode == 0
    assert "NOT AUTHORITY" in out.read_text()


def test_cli_validate_charge_fails_closed_on_bad_charge(tmp_path):
    ev = tmp_path / "event.json"
    ch = tmp_path / "charge.json"
    out = tmp_path / "comment.md"
    _run_cli("make-dry-run-event", "--head-sha", _GOOD_SHA,
             "--event-output", str(ev))
    ch.write_text(json.dumps(_charge_dict(confidence="BOGUS")))
    r = _run_cli("validate-charge", "--event", str(ev), "--charge", str(ch),
                 "--comment-output", str(out))
    assert r.returncode == 2
    assert r.stdout == "" or "BOGUS" not in (r.stdout + r.stderr)
    assert "campaign-control: FAIL" in r.stderr


# --------------------------------------------------------------------------
# prompt invariants (RED until prompt lands)
# --------------------------------------------------------------------------
def test_prompt_declares_read_only_non_authority():
    low = _PROMPT_PATH.read_text(encoding="utf-8").lower()
    assert "read-only" in low
    assert "not authority" in low or "non-authoritative" in low
    # insufficient evidence -> LOW confidence + explicitly conditional charge
    assert "insufficient" in low and "conditional" in low


def test_prompt_forbids_authority_claims():
    low = _PROMPT_PATH.read_text(encoding="utf-8").lower()
    for token in ("gate a", "approv", "merge", "ratif"):
        assert token in low  # each named as something the model must NOT claim


def test_prompt_insufficient_evidence_is_conditional_not_hold_substitution():
    """PR #249 P1 mutation-kill: the insufficient-evidence path must NOT tell the
    model to recommend HOLD or substitute a different option -- that conflicts
    with the validator's enforced recommended_option == event.recommended_option
    rule (the only synthetic event sets HOLD=A but recommends B). It must instead
    preserve the event's recommendation and express insufficiency as LOW
    confidence + an explicitly conditional, evidence-gated charge."""
    norm = " ".join(_PROMPT_PATH.read_text(encoding="utf-8").lower().split()).replace("`", "")
    # the conflicting instruction cannot return
    assert "recommend the hold" not in norm
    assert "prefer hold" not in norm
    # the recommendation is always the event's
    assert "recommended_option must equal the event's recommended_option" in norm
    # insufficiency -> LOW confidence + explicitly conditional charge
    assert "insufficient" in norm
    assert "conditional" in norm
    assert "confidence to low" in norm


# ==========================================================================
# WORKFLOW STRUCTURAL TESTS -- every one is a TRIPWIRE - NOT BEHAVIORAL PROOF.
# They assert the workflow FILE says the right thing; they do NOT prove the
# workflow behaves. Behavioral + credential-isolation truth is the mandatory
# post-merge `main` dispatch (PRD-302 R7/R18). Do not read a green TRIPWIRE as
# behavioral proof.
# ==========================================================================
import yaml  # noqa: E402

_WF_PATH = _REPO_ROOT / ".github" / "workflows" / "campaign_control.yml"
_TRIPWIRE_MARKER = "TRIPWIRE - NOT BEHAVIORAL PROOF"

_PIN_CHECKOUT = "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1"
_PIN_UPLOAD = "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
_PIN_SCRIPT = "actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3"
_PIN_CODEX = "openai/codex-action@52fe01ec70a42f454c9d2ebd47598f9fd6893d56"


def _wf_text():
    return _WF_PATH.read_text(encoding="utf-8")


def _wf():
    return yaml.safe_load(_wf_text())


def _on_section(wf):
    # PyYAML (YAML 1.1) parses the `on:` key as the boolean True.
    return wf[True] if True in wf else wf["on"]


def _job(wf, name):
    return wf["jobs"][name]


def _steps(job):
    return job.get("steps", [])


def _codex_action_step(job):
    for s in _steps(job):
        if isinstance(s.get("uses"), str) and s["uses"].startswith("openai/codex-action@"):
            return s
    return None


def _run_code(wf):
    # concatenated run: bodies with shell comment-only lines removed, so an
    # assertion targets executable shell and not explanatory comment prose.
    lines = []
    for name in ("codex", "validate"):
        for s in _steps(_job(wf, name)):
            run = s.get("run")
            if isinstance(run, str):
                lines.extend(ln for ln in run.splitlines()
                             if not ln.lstrip().startswith("#"))
    return "\n".join(lines)


def _r7_step_run(job):
    # the single split-proof step contains both the runner-side and codex-side
    # legs (probe-runner-side + probe-codex-isolation).
    for s in _steps(job):
        run = s.get("run") or ""
        if "probe-codex-isolation" in run or "probe-runner-side" in run:
            return run
    return None


def test_tripwire_only_workflow_dispatch():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: only workflow_dispatch is declared."""
    on = _on_section(_wf())
    keys = set(on) if isinstance(on, dict) else {on}
    assert keys == {"workflow_dispatch"}
    for banned in ("issue_comment", "pull_request", "pull_request_target",
                   "repository_dispatch", "workflow_run", "push", "schedule"):
        assert banned not in keys


def test_tripwire_top_level_permissions_contents_read():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: top-level permissions are contents:read."""
    assert _wf()["permissions"] == {"contents": "read"}


def test_tripwire_both_jobs_contents_read_only():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: both jobs are contents:read only."""
    wf = _wf()
    for name in ("codex", "validate"):
        assert _job(wf, name)["permissions"] == {"contents": "read"}


def test_tripwire_no_write_scopes_or_id_token():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: no write scope and no id-token anywhere."""
    text = _wf_text()
    assert "id-token" not in text
    assert "issues:" not in text
    assert "pull-requests:" not in text
    assert "contents: write" not in text
    assert ": write" not in text


def test_tripwire_codex_job_actor_and_ref_guard():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: codex job binds owner actor + main ref."""
    cond = _job(_wf(), "codex")["if"]
    assert "github.actor == 'dwats250'" in cond
    assert "github.ref == 'refs/heads/main'" in cond


def test_tripwire_codex_checkout_ref_main_and_no_persisted_creds():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: codex checkout uses main + no persisted creds."""
    for s in _steps(_job(_wf(), "codex")):
        if isinstance(s.get("uses"), str) and s["uses"].startswith("actions/checkout@"):
            assert s["with"]["ref"] == "main"
            assert s["with"]["persist-credentials"] is False


def test_tripwire_all_checkouts_disable_persisted_creds():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: every checkout sets persist-credentials:false."""
    wf = _wf()
    for name in ("codex", "validate"):
        for s in _steps(_job(wf, name)):
            if isinstance(s.get("uses"), str) and s["uses"].startswith("actions/checkout@"):
                assert s["with"]["persist-credentials"] is False


def test_tripwire_secret_appears_once_as_action_input():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: OPENAI_API_KEY only as the codex-action input."""
    text = _wf_text()
    assert text.count("OPENAI_API_KEY") == 1
    assert "openai-api-key: ${{ secrets.OPENAI_API_KEY }}" in text
    # never in an env: block or a run: step
    for line in text.splitlines():
        if "OPENAI_API_KEY" in line:
            assert "openai-api-key:" in line


def test_tripwire_codex_action_is_literal_final_step():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: the Codex Action is the last step of its job."""
    steps = _steps(_job(_wf(), "codex"))
    last = steps[-1]
    assert isinstance(last.get("uses"), str)
    assert last["uses"].startswith("openai/codex-action@")


def test_tripwire_unprivileged_user_and_concrete_codex_user():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: unprivileged-user + concrete codex-user + read-only."""
    step = _codex_action_step(_job(_wf(), "codex"))
    assert step is not None
    with_ = step["with"]
    assert with_["safety-strategy"] == "unprivileged-user"
    assert with_["permission-profile"] == ":read-only"
    codex_user = with_["codex-user"]
    assert isinstance(codex_user, str) and codex_user.strip()
    # the user is provisioned by an earlier step
    assert codex_user in _wf_text()
    assert "useradd" in _wf_text()


def test_tripwire_exact_pins_and_codex_version():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: exact R21 action pins + codex 0.147.0."""
    text = _wf_text()
    for pin in (_PIN_CHECKOUT, _PIN_UPLOAD, _PIN_SCRIPT, _PIN_CODEX):
        assert pin in text
    assert "0.147.0" in text


def test_tripwire_no_download_artifact():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: download-artifact is not present (unearned)."""
    assert "actions/download-artifact" not in _wf_text()


def test_tripwire_artifact_fixed_name_one_day_retention():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: rendered artifact has a fixed name + 1-day retention."""
    step = None
    for s in _steps(_job(_wf(), "validate")):
        if isinstance(s.get("uses"), str) and s["uses"].startswith("actions/upload-artifact@"):
            step = s
    assert step is not None
    assert step["with"]["retention-days"] == 1
    assert step["with"]["name"]


def test_tripwire_model_output_transported_inertly():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: charge_json enters via env->github-script, not spliced."""
    text = _wf_text()
    # the model output is consumed only via env into pinned github-script
    assert "CHARGE_JSON: ${{ needs.codex.outputs.charge_json }}" in text
    # never spliced into a run: body or an artifact name
    assert "run: |" in text  # sanity: run steps exist
    assert "${{ needs.codex.outputs.charge_json }}" not in text.replace(
        "CHARGE_JSON: ${{ needs.codex.outputs.charge_json }}", "")


def test_tripwire_github_script_write_is_a_fixed_safe_write():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: the model-output materializer is a fixed non-evaluating write."""
    script = None
    for s in _steps(_job(_wf(), "validate")):
        if isinstance(s.get("uses"), str) and s["uses"].startswith("actions/github-script@"):
            script = s["with"]["script"]
    assert script is not None
    assert "fs.writeFileSync" in script
    assert "process.env.CHARGE_JSON" in script
    for danger in ("eval(", "Function(", "child_process", "execSync", "require('vm')"):
        assert danger not in script


def test_tripwire_no_explicit_action_output_file():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: no explicit codex output-file (unwritable by the codex uid)."""
    step = _codex_action_step(_job(_wf(), "codex"))
    assert step is not None
    assert "output-file" not in step["with"]


def test_tripwire_staged_inputs_world_readable():
    """TRIPWIRE - NOT BEHAVIORAL PROOF (Amendment 2): the isolated public copies
    are made readable to the distinct codex uid (a+rX on the /tmp workspace)."""
    text = _wf_text()
    assert "useradd" in text
    assert 'chmod -R a+rX "$WS/tools" "$WS/.github"' in text  # isolated copies readable
    assert "chmod -R u+rX" not in text  # user-only would starve the codex uid


def test_tripwire_no_ancestor_or_home_traversal_grant():
    """TRIPWIRE - NOT BEHAVIORAL PROOF (Amendment 2): NO o+x grant is placed on
    any runner-owned ancestor or /home/runner. Mutation-kill: reintroducing the
    ancestor-o+x traversal walk (the run-31763968329 failure class)."""
    text = _wf_text()
    code = _run_code(_wf())
    assert "chmod o+x" not in text            # no execute grant on any ancestor
    assert "o+x" not in code                  # no o+x anywhere in executable shell
    assert 'while [ "$d" != "/" ]' not in text  # the ancestor-walk loop is gone
    assert "/home/runner" not in code         # the runner home is never staged/granted


def test_tripwire_isolated_workspace_under_tmp_not_runner_paths():
    """TRIPWIRE - NOT BEHAVIORAL PROOF (Amendment 2): the codex workspace is a
    uniquely-named /tmp dir derived from the trusted run id -- never beneath
    /home/runner or $RUNNER_TEMP. Mutation-kill: re-basing the workspace under a
    runner-owned path or the runner temp."""
    text = _wf_text()
    code = _run_code(_wf())
    assert 'WS="/tmp/campaign-ws-${GITHUB_RUN_ID}"' in text
    assert "/home/runner" not in code
    # $RUNNER_TEMP is used ONLY as the credential-enumeration source, never a base
    assert "$RUNNER_TEMP/" not in code and "${RUNNER_TEMP}/" not in code
    # the approved public copies land under $WS only
    assert 'cp tools/campaign_control.py "$WS/tools/campaign_control.py"' in text
    assert 'mkdir -p "$WS/tools"' in text


def test_tripwire_codex_action_isolated_paths():
    """TRIPWIRE - NOT BEHAVIORAL PROOF (Amendment 2): the codex-action
    working-directory / prompt-file / output-schema-file are absolute isolated
    /tmp paths derived from the trusted run id. Mutation-kill: dropping or
    mis-pointing any of the three isolated-path inputs."""
    step = _codex_action_step(_job(_wf(), "codex"))
    assert step is not None
    base = "/tmp/campaign-ws-${{ github.run_id }}"
    with_ = step["with"]
    assert with_["working-directory"] == base
    assert with_["prompt-file"] == base + "/.github/campaign/charge_prompt.md"
    assert with_["output-schema-file"] == base + "/.github/campaign/charge.schema.json"


def test_tripwire_no_issue_or_comment_publication():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: no issue/PR/comment/authoritative publication."""
    text = _wf_text()
    assert "gh pr" not in text
    assert "gh issue" not in text
    assert "createComment" not in text
    assert "issues.create" not in text


def test_tripwire_r7_split_runner_leg_present():
    """TRIPWIRE - NOT BEHAVIORAL PROOF (Amendment 2): the runner-side leg proves
    the canonical credential exists + is runner-owned and runs AS the runner uid
    (never the codex uid), with the root derived from the LIVE Runner.Worker.
    Mutation-kill: removing the runner-side existence/ownership proof, or running
    it under the wrong uid."""
    run = _r7_step_run(_job(_wf(), "codex"))
    assert run is not None
    assert "python3 tools/campaign_control.py probe-runner-side" in run
    # the runner-side leg is NOT run via sudo -u codex (that would be wrong-uid)
    assert 'sudo -u "$CODEX_USER" python3 tools/campaign_control.py probe-runner-side' not in run
    assert "--runner-root" in run and "--runner-temp" in run
    # root derived from the LIVE runner process, not a guessed candidate path
    assert "Runner.Worker" in run and "/proc/" in run
    assert "/actions-runner" not in run            # no hardcoded candidate list


def test_tripwire_r7_codex_leg_runs_as_codex_uid():
    """TRIPWIRE - NOT BEHAVIORAL PROOF (Amendment 2): the credential-denial +
    isolation checks run AS the exact codex uid, via the COPY of the tool in the
    isolated workspace, enumerating the runner credentials and the isolated
    inputs/output. Mutation-kill: running the denial checks under the wrong uid,
    against the runner-side tool, or dropping the credential/input enumeration."""
    run = _r7_step_run(_job(_wf(), "codex"))
    assert run is not None
    # denial checks run as the distinct codex uid, against the isolated tool copy
    assert ('sudo -u "$CODEX_USER" python3 "$WS/tools/campaign_control.py" '
            "probe-codex-isolation") in run
    assert '--runner-uid "$RUNNER_UID"' in run   # tool fails closed on same-uid
    assert "--credential" in run                 # enumerated runner credentials
    assert "--input" in run                      # positive isolated-input checks
    assert "--output-dir" in run                 # positive output-writable check


def test_tripwire_r7_before_codex_action():
    """TRIPWIRE - NOT BEHAVIORAL PROOF (Amendment 2): the R7 split proof runs
    BEFORE the secret-bearing codex action. Mutation-kill: moving R7 after the
    Codex action."""
    steps = _steps(_job(_wf(), "codex"))
    r7_idx = next((i for i, s in enumerate(steps)
                   if "probe-codex-isolation" in (s.get("run") or "")), None)
    action_idx = next((i for i, s in enumerate(steps)
                       if isinstance(s.get("uses"), str)
                       and s["uses"].startswith("openai/codex-action@")), None)
    assert r7_idx is not None and action_idx is not None
    assert r7_idx < action_idx


def test_tripwire_r7_split_proof_is_fail_closed():
    """TRIPWIRE - NOT BEHAVIORAL PROOF (Amendment 2): the split proof is
    fail-closed -- `set -euo pipefail`, no status masking, terminating `exit 2`
    on shell failure branches, and the runner-side capture uses a plain
    assignment (propagates a FAIL under set -e) rather than a process-
    substitution pipe that would swallow the exit code. Mutation-kills: masking
    any failure (`|| true` / `|| :` / `|| exit 0`), or piping the runner-side
    proof through `mapfile < <(...)`."""
    run = _r7_step_run(_job(_wf(), "codex"))
    assert run is not None
    assert "set -euo pipefail" in run
    assert "|| :" not in run
    assert "|| exit 0" not in run
    # the runner-side proof is captured by a plain assignment, not a pipe that
    # would swallow its exit code
    assert "mapfile -t CRED_PATHS < <(python3" not in run
    assert 'CRED_PATHS_RAW="$(python3 tools/campaign_control.py probe-runner-side' in run
    # the codex-side denial call is not status-masked
    _after_codex = run.split("probe-codex-isolation", 1)[1]
    assert "|| true" not in _after_codex
    # the ONLY permitted `|| true` is the pgrep no-match guard (followed by a
    # count check + exit 2); any second one is status masking
    assert run.count("|| true") <= 1
    assert "pgrep -x Runner.Worker || true" in run
    # every shell-level FAIL message is paired with a terminating exit 2
    fail_msgs = run.count("campaign-control: FAIL [")
    assert fail_msgs >= 2  # probe-root, probe-temp
    assert run.count("exit 2") >= fail_msgs


def test_tripwire_marker_present_on_every_tripwire_test():
    """TRIPWIRE - NOT BEHAVIORAL PROOF: meta-test -- the marker stays machine-visible."""
    mod = sys.modules[__name__]
    tripwires = [obj for name, obj in vars(mod).items()
                 if name.startswith("test_tripwire_") and callable(obj)]
    assert len(tripwires) >= 15
    for fn in tripwires:
        assert (fn.__doc__ or "").find(_TRIPWIRE_MARKER) != -1, fn.__name__
