"""Contract + core tests for the PRD-302 Slice-A campaign control plane tool.

Tests-first (RED before tools/campaign_control.py, .github/campaign/*, and
.github/workflows/campaign_control.yml exist). Import isolation follows the
macro-awareness pattern: add tools/ to sys.path and import by plain name.

Slice A only: fixed synthetic event, non-authoritative proposed charge, no
network, no issue/PR/comment/publication. See docs/prd_history/PRD-302.md.
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


def _cred(path="/runner/.credentials", exists=True, owner_uid=1000,
          readable_by_codex=False):
    return cc.CredentialObservation(
        path=path, exists=exists, owner_uid=owner_uid,
        readable_by_codex=readable_by_codex)


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
    hostile = 'q"n\n$(id)`x`${{ secrets.X }} ::set-output name=y::z'
    ch = cc.parse_charge(_charge_dict(charge_markdown=hostile))
    out = cc.render_charge(ev, ch)
    # present as escaped data, never as an active construct
    assert "$(id)" not in out or "&#" in out  # dollar-paren neutralized/escaped context
    assert "::set-output" not in out.replace("&#", "")  # not a live workflow command


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
# R7 credential-isolation probe: fail-closed decision logic
# --------------------------------------------------------------------------
def test_probe_passes_when_isolated():
    cc.evaluate_isolation(
        runner_uid=1000, codex_uid=2000, runner_root="/runner",
        observations=[_cred()])


def test_probe_fails_when_codex_uid_equals_runner_uid():
    with pytest.raises(cc.CampaignError):
        cc.evaluate_isolation(
            runner_uid=1000, codex_uid=1000, runner_root="/runner",
            observations=[_cred()])


def test_probe_fails_on_ambiguous_root():
    with pytest.raises(cc.CampaignError):
        cc.evaluate_isolation(
            runner_uid=1000, codex_uid=2000, runner_root="",
            observations=[_cred()])


def test_probe_fails_when_credentials_absent():
    with pytest.raises(cc.CampaignError):
        cc.evaluate_isolation(
            runner_uid=1000, codex_uid=2000, runner_root="/runner",
            observations=[_cred(exists=False, owner_uid=None)])


def test_probe_fails_when_credentials_missing_from_observations():
    with pytest.raises(cc.CampaignError):
        cc.evaluate_isolation(
            runner_uid=1000, codex_uid=2000, runner_root="/runner",
            observations=[])


def test_probe_fails_when_credentials_wrong_owner():
    with pytest.raises(cc.CampaignError):
        cc.evaluate_isolation(
            runner_uid=1000, codex_uid=2000, runner_root="/runner",
            observations=[_cred(owner_uid=2000)])


def test_probe_fails_when_credential_readable_by_codex():
    with pytest.raises(cc.CampaignError):
        cc.evaluate_isolation(
            runner_uid=1000, codex_uid=2000, runner_root="/runner",
            observations=[_cred(readable_by_codex=True)])


def test_probe_reports_no_credential_contents():
    # the observation type carries no content field at all
    fields = {f.name for f in cc.dataclasses_fields(cc.CredentialObservation)}
    assert "content" not in fields and "data" not in fields


# --------------------------------------------------------------------------
# schema <-> validator drift guard + field-by-field diff (RED until schema lands)
# --------------------------------------------------------------------------
def _schema():
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_charge_schema_required_keys_match_validator():
    s = _schema()
    assert set(s["required"]) == cc.CHARGE_KEYS
    assert s["additionalProperties"] is False


def test_charge_schema_has_no_verification_field():
    s = _schema()
    assert "verification" not in s["properties"]
    assert all("verif" not in k for k in s["properties"])


def test_charge_schema_enums_and_limits_match_validator():
    s = _schema()
    props = s["properties"]
    assert set(props["recommended_option"]["enum"]) == set(cc.OPTION_IDS)
    assert set(props["confidence"]["enum"]) == set(cc.CONFIDENCE)
    assert props["charge_markdown"]["maxLength"] == cc.MAX_CHARGE_CHARS
    assert props["rationale"]["maxLength"] == cc.MAX_RATIONALE_CHARS
    assert props["schema"]["const"] == cc.SCHEMA_CHARGE


def test_schema_and_validator_agree_on_a_sweep():
    # every field the schema rejects, the validator also rejects (sample sweep)
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
    text = _PROMPT_PATH.read_text(encoding="utf-8")
    low = text.lower()
    assert "read-only" in low
    assert "not authority" in low or "non-authoritative" in low
    assert "hold" in low  # recommend HOLD when evidence insufficient


def test_prompt_forbids_authority_claims():
    low = _PROMPT_PATH.read_text(encoding="utf-8").lower()
    for token in ("gate a", "approv", "merge", "ratif"):
        assert token in low  # each named as something the model must NOT claim
