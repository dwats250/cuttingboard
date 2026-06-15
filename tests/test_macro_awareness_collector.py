"""PRD-187 -- Macro-Awareness Producer test suite.

Tests cover R1-R7 requirements without any real network I/O and without
requiring anthropic, feedparser, or requests to be installed.

Import strategy: the tool is import-isolated (R1) so we add the repo's
tools/ directory to sys.path and import via plain name.
"""

from __future__ import annotations

import ast
import hashlib
import html
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import pytest

# ---------------------------------------------------------------------------
# sys.path bootstrap (R1 isolation: no cuttingboard import in this file)
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TOOLS_DIR = _REPO_ROOT / "tools"

if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import macro_awareness_collector as mac  # noqa: E402 (must follow sys.path setup)

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 6, 14, 12, 0, 0, tzinfo=timezone.utc)
_BOJ_DOMAIN = "boj.or.jp"
_BOJ_LINK = "https://www.boj.or.jp/en/x"
_BOJ_NAME = "Bank of Japan"


def _boj_entry(
    *,
    title: str = "BoJ exits YCC policy",
    summary: str = "The Bank of Japan announced an unscheduled shift.",
    link: str = _BOJ_LINK,
    published_at: Optional[str] = None,
) -> mac.Entry:
    return mac.Entry(
        source_name=_BOJ_NAME,
        entity="BoJ",
        domain=_BOJ_DOMAIN,
        title=title,
        summary=summary,
        link=link,
        published_at=published_at or mac._iso(_NOW - timedelta(hours=1)),
    )


def _shock_classification(idx: int = 0, event_type: str = "POLICY_REGIME_SHIFT") -> dict:
    return {"shock_present": True, "selected_index": idx, "event_type": event_type}


def _quiet_classification() -> dict:
    return {"shock_present": False, "selected_index": None, "event_type": None}


def _valid_shock_snapshot(now: Optional[datetime] = None) -> dict:
    now = now or _NOW
    entries = [_boj_entry()]
    classification = _shock_classification()
    snap = mac.build_snapshot(entries, classification, now)
    assert snap["status"] == "SHOCK", "fixture build failed"
    return snap


def _valid_quiet_snapshot(now: Optional[datetime] = None) -> dict:
    now = now or _NOW
    return mac.build_snapshot([], _quiet_classification(), now)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# R1 -- Isolation: AST import check
# ---------------------------------------------------------------------------


class TestR1Isolation:
    def test_no_top_level_cuttingboard_import(self) -> None:
        """AST check: no top-level import references cuttingboard."""
        source = (_REPO_ROOT / "tools" / "macro_awareness_collector.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                # Only flag top-level nodes (col_offset == 0 or depth 1)
                # ast.walk visits all nodes; we check the parent body
                pass

        # Collect all top-level import statements (body of Module)
        top_level_imports: list[ast.stmt] = [
            n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
        ]
        for node in top_level_imports:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "cuttingboard" not in alias.name, (
                        f"top-level 'import {alias.name}' references cuttingboard (R1)"
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert "cuttingboard" not in module, (
                    f"top-level 'from {module} import ...' references cuttingboard (R1)"
                )
                assert "anthropic" not in module, (
                    f"top-level 'from {module} import ...' is anthropic -- must be lazy (R1)"
                )
                assert "feedparser" not in module, (
                    f"top-level 'from {module} import ...' is feedparser -- must be lazy (R1)"
                )
                assert "requests" not in module, (
                    f"top-level 'from {module} import ...' is requests -- must be lazy (R1)"
                )

    def test_no_top_level_anthropic_import(self) -> None:
        """anthropic must be a lazy import (inside a function)."""
        source = (_REPO_ROOT / "tools" / "macro_awareness_collector.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        top_level_imports = [
            n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
        ]
        for node in top_level_imports:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "anthropic" not in alias.name, (
                        f"top-level 'import {alias.name}' -- anthropic must be lazy (R1)"
                    )

    def test_no_top_level_feedparser_or_requests_import(self) -> None:
        """feedparser and requests must be lazy imports (inside functions)."""
        source = (_REPO_ROOT / "tools" / "macro_awareness_collector.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        top_level_imports = [
            n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))
        ]
        for node in top_level_imports:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "feedparser" not in alias.name, (
                        f"feedparser must be lazy, found top-level: {alias.name}"
                    )
                    assert "requests" not in alias.name, (
                        f"requests must be lazy, found top-level: {alias.name}"
                    )

    def test_no_cuttingboard_module_imports_collector(self) -> None:
        """No file under cuttingboard/ imports macro_awareness_collector."""
        result = subprocess.run(
            ["rg", "--fixed-strings", "macro_awareness_collector",
             str(_REPO_ROOT / "cuttingboard")],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0 or result.stdout.strip() == "", (
            f"cuttingboard/ imports macro_awareness_collector:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# R2 -- Artifact-path isolation
# ---------------------------------------------------------------------------


class TestR2ArtifactPathIsolation:
    def test_snapshot_path_not_in_cuttingboard(self) -> None:
        """logs/macro_awareness_snapshot.json must not appear in cuttingboard/."""
        result = subprocess.run(
            ["rg", "--fixed-strings", "macro_awareness_snapshot",
             str(_REPO_ROOT / "cuttingboard")],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0 or result.stdout.strip() == "", (
            f"macro_awareness_snapshot found in cuttingboard/:\n{result.stdout}"
        )

    def test_state_path_not_in_cuttingboard(self) -> None:
        """logs/macro_awareness_state.json must not appear in cuttingboard/."""
        result = subprocess.run(
            ["rg", "--fixed-strings", "macro_awareness_state",
             str(_REPO_ROOT / "cuttingboard")],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0 or result.stdout.strip() == "", (
            f"macro_awareness_state found in cuttingboard/:\n{result.stdout}"
        )


# ---------------------------------------------------------------------------
# R3 -- Controlled schema (validate_snapshot)
# ---------------------------------------------------------------------------


class TestR3Schema:
    # -- Happy paths ---------------------------------------------------------

    def test_valid_quiet_snapshot_returns_no_errors(self) -> None:
        snap = _valid_quiet_snapshot()
        assert mac.validate_snapshot(snap) == []

    def test_valid_shock_snapshot_returns_no_errors(self) -> None:
        snap = _valid_shock_snapshot()
        assert mac.validate_snapshot(snap) == []

    # -- Rejection cases -----------------------------------------------------

    def test_shock_with_null_shock_rejected(self) -> None:
        snap = _valid_shock_snapshot()
        snap = dict(snap)
        snap["shock"] = None
        errors = mac.validate_snapshot(snap)
        assert errors, "SHOCK with shock=null must be rejected"

    def test_quiet_with_populated_shock_rejected(self) -> None:
        shock_snap = _valid_shock_snapshot()
        snap = dict(_valid_quiet_snapshot())
        snap["shock"] = shock_snap["shock"]
        errors = mac.validate_snapshot(snap)
        assert errors, "QUIET with non-null shock must be rejected"

    def test_extra_key_inside_shock_rejected(self) -> None:
        snap = _valid_shock_snapshot()
        shock = dict(snap["shock"])
        shock["extra_key"] = "unexpected"
        snap = dict(snap)
        snap["shock"] = shock
        errors = mac.validate_snapshot(snap)
        assert errors, "extra key inside shock must be rejected"

    def test_forbidden_key_confidence_score_at_top_level_rejected(self) -> None:
        snap = dict(_valid_quiet_snapshot())
        snap["confidence_score"] = 0.9
        errors = mac.validate_snapshot(snap)
        assert errors, "forbidden key 'confidence_score' at top level must be rejected"

    def test_forbidden_key_macro_bias_at_top_level_rejected(self) -> None:
        snap = dict(_valid_quiet_snapshot())
        snap["macro_bias"] = "bullish"
        errors = mac.validate_snapshot(snap)
        assert errors, "forbidden key 'macro_bias' at top level must be rejected"

    def test_forbidden_key_inside_shock_rejected(self) -> None:
        snap = _valid_shock_snapshot()
        shock = dict(snap["shock"])
        shock["confidence_score"] = 0.9
        snap = dict(snap)
        snap["shock"] = shock
        errors = mac.validate_snapshot(snap)
        assert errors, "forbidden key inside shock must be rejected"

    def test_invalid_event_type_rejected(self) -> None:
        snap = _valid_shock_snapshot()
        shock = dict(snap["shock"])
        shock["event_type"] = "MADE_UP_TYPE"
        snap = dict(snap)
        snap["shock"] = shock
        errors = mac.validate_snapshot(snap)
        assert errors, "event_type not in enum must be rejected"

    def test_non_allowlist_source_url_rejected(self) -> None:
        snap = _valid_shock_snapshot()
        shock = dict(snap["shock"])
        shock["source_url"] = "https://evil.com/news"
        snap = dict(snap)
        snap["shock"] = shock
        errors = mac.validate_snapshot(snap)
        assert errors, "non-allowlist source_url must be rejected"

    def test_naive_generated_at_rejected(self) -> None:
        snap = dict(_valid_quiet_snapshot())
        snap["generated_at"] = "2026-06-14T12:00:00"  # no tz
        errors = mac.validate_snapshot(snap)
        assert errors, "naive generated_at must be rejected"

    def test_excerpt_too_long_rejected(self) -> None:
        snap = _valid_shock_snapshot()
        shock = dict(snap["shock"])
        shock["source_excerpt"] = "x" * (mac.EXCERPT_MAX + 1)
        snap = dict(snap)
        snap["shock"] = shock
        errors = mac.validate_snapshot(snap)
        assert errors, "source_excerpt exceeding length cap must be rejected"

    def test_unescaped_html_in_excerpt_rejected(self) -> None:
        snap = _valid_shock_snapshot()
        shock = dict(snap["shock"])
        shock["source_excerpt"] = "This has <script> tag"  # raw unescaped <
        snap = dict(snap)
        snap["shock"] = shock
        errors = mac.validate_snapshot(snap)
        assert errors, "source_excerpt with raw '<' must be rejected"

    # -- build_snapshot behavior ---------------------------------------------

    def test_build_snapshot_escapes_html_in_excerpt(self) -> None:
        entry = _boj_entry(title="<script>alert(1)</script>", summary="xss attempt")
        classification = _shock_classification()
        snap = mac.build_snapshot([entry], classification, _NOW)
        assert snap["status"] == "SHOCK"
        assert "<" not in snap["shock"]["source_excerpt"], (
            "build_snapshot must HTML-escape '<' in source_excerpt"
        )

    def test_build_snapshot_caps_excerpt_length(self) -> None:
        long_summary = "word " * 200  # much longer than EXCERPT_MAX
        entry = _boj_entry(title="Title", summary=long_summary)
        classification = _shock_classification()
        snap = mac.build_snapshot([entry], classification, _NOW)
        assert snap["status"] == "SHOCK"
        assert len(snap["shock"]["source_excerpt"]) <= mac.EXCERPT_MAX

    def test_build_snapshot_shock_is_schema_valid(self) -> None:
        snap = _valid_shock_snapshot()
        assert mac.validate_snapshot(snap) == []

    def test_build_snapshot_quiet_when_shock_present_false(self) -> None:
        entries = [_boj_entry()]
        snap = mac.build_snapshot(entries, _quiet_classification(), _NOW)
        assert snap["status"] == "QUIET"
        assert snap["shock"] is None

    def test_build_snapshot_quiet_when_selected_index_out_of_range(self) -> None:
        entries = [_boj_entry()]
        classification = {"shock_present": True, "selected_index": 99, "event_type": "POLICY_REGIME_SHIFT"}
        snap = mac.build_snapshot(entries, classification, _NOW)
        assert snap["status"] == "QUIET"

    def test_build_snapshot_quiet_when_selected_index_none(self) -> None:
        entries = [_boj_entry()]
        classification = {"shock_present": True, "selected_index": None, "event_type": "POLICY_REGIME_SHIFT"}
        snap = mac.build_snapshot(entries, classification, _NOW)
        assert snap["status"] == "QUIET"

    def test_build_snapshot_quiet_when_event_type_not_in_enum(self) -> None:
        entries = [_boj_entry()]
        classification = {"shock_present": True, "selected_index": 0, "event_type": "BOGUS_TYPE"}
        snap = mac.build_snapshot(entries, classification, _NOW)
        assert snap["status"] == "QUIET"

    def test_build_snapshot_quiet_when_link_domain_not_in_allowlist(self) -> None:
        entry = _boj_entry(link="https://evil.com/news")
        classification = _shock_classification()
        snap = mac.build_snapshot([entry], classification, _NOW)
        assert snap["status"] == "QUIET"


# ---------------------------------------------------------------------------
# R4 -- Fail-closed and coherent generation
# ---------------------------------------------------------------------------


class TestR4FailClosed:
    def test_missing_api_key_returns_1_and_preserves_snapshot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """run() returns 1 and leaves snapshot byte-identical when API key missing."""
        snapshot_path = tmp_path / "snapshot.json"
        state_path = tmp_path / "state.json"
        sentinel = {"sentinel": "do not overwrite"}
        snapshot_path.write_text(json.dumps(sentinel), encoding="utf-8")
        before_sha = _sha256(snapshot_path)

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        result = mac.run(
            snapshot_path=snapshot_path,
            state_path=state_path,
            fetch_fn=lambda n: [],
            classify_fn=lambda e: _quiet_classification(),
        )

        assert result == 1
        assert _sha256(snapshot_path) == before_sha, (
            "run() must leave snapshot byte-identical when ANTHROPIC_API_KEY is unset"
        )

    def test_fetch_raises_returns_1_and_preserves_snapshot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """run() returns 1 and preserves prior snapshot when fetch_fn raises."""
        snapshot_path = tmp_path / "snapshot.json"
        state_path = tmp_path / "state.json"
        sentinel = {"sentinel": "preserved"}
        snapshot_path.write_text(json.dumps(sentinel), encoding="utf-8")
        before_sha = _sha256(snapshot_path)

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        def bad_fetch(n: datetime) -> list:
            raise RuntimeError("network error")

        result = mac.run(
            snapshot_path=snapshot_path,
            state_path=state_path,
            fetch_fn=bad_fetch,
            classify_fn=lambda e: _quiet_classification(),
        )

        assert result == 1
        assert _sha256(snapshot_path) == before_sha

    def test_classify_raises_returns_1_and_preserves_snapshot(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """run() returns 1 and preserves prior snapshot when classify_fn raises."""
        snapshot_path = tmp_path / "snapshot.json"
        state_path = tmp_path / "state.json"
        sentinel = {"sentinel": "preserved"}
        snapshot_path.write_text(json.dumps(sentinel), encoding="utf-8")
        before_sha = _sha256(snapshot_path)

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        def bad_classify(entries: list) -> dict:
            raise ValueError("model failure")

        result = mac.run(
            snapshot_path=snapshot_path,
            state_path=state_path,
            fetch_fn=lambda n: [_boj_entry()],
            classify_fn=bad_classify,
        )

        assert result == 1
        assert _sha256(snapshot_path) == before_sha

    def test_classify_malformed_output_returns_1(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """run() returns 1 when classify_fn returns output that fails self-validation."""
        snapshot_path = tmp_path / "snapshot.json"
        state_path = tmp_path / "state.json"
        sentinel = {"sentinel": "preserved"}
        snapshot_path.write_text(json.dumps(sentinel), encoding="utf-8")
        before_sha = _sha256(snapshot_path)

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        # Return a classification that passes through build_snapshot but causes
        # the produced snapshot to fail validate_snapshot via forbidden key injection
        # We simulate this by patching build_snapshot to inject a forbidden key.
        # Instead: provide a classify_fn that returns shock_present=True with a
        # bad event_type so build_snapshot -> QUIET -> valid, that's fine.
        # Better approach: monkeypatch validate_snapshot to reject for this test.
        # Actually, build_snapshot degrades to QUIET on bad event_type, so it
        # produces a valid QUIET snapshot. To test self-validation failure, we
        # patch build_snapshot directly to inject a forbidden key.
        original_build = mac.build_snapshot

        def bad_build(entries, classification, now):
            snap = original_build(entries, classification, now)
            snap["macro_bias"] = "INJECTED"  # forbidden key
            return snap

        import unittest.mock as mock
        with mock.patch.object(mac, "build_snapshot", bad_build):
            result = mac.run(
                snapshot_path=snapshot_path,
                state_path=state_path,
                fetch_fn=lambda n: [_boj_entry()],
                classify_fn=lambda e: _shock_classification(),
            )

        assert result == 1
        assert _sha256(snapshot_path) == before_sha

    def test_ambiguity_to_quiet_returns_0_and_writes_quiet(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """run() returns 0 and writes QUIET when classify_fn returns ambiguous result."""
        snapshot_path = tmp_path / "snapshot.json"
        state_path = tmp_path / "state.json"

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        result = mac.run(
            snapshot_path=snapshot_path,
            state_path=state_path,
            fetch_fn=lambda n: [_boj_entry()],
            classify_fn=lambda e: _quiet_classification(),
        )

        assert result == 0
        snap = json.loads(snapshot_path.read_text(encoding="utf-8"))
        assert snap["status"] == "QUIET"
        assert mac.validate_snapshot(snap) == []

    def test_successful_shock_run_writes_both_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """On a successful SHOCK run, both snapshot and state files exist and are valid."""
        snapshot_path = tmp_path / "snapshot.json"
        state_path = tmp_path / "state.json"

        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        result = mac.run(
            now=_NOW,
            snapshot_path=snapshot_path,
            state_path=state_path,
            fetch_fn=lambda n: [_boj_entry()],
            classify_fn=lambda e: _shock_classification(),
        )

        assert result == 0
        assert snapshot_path.exists(), "snapshot file must exist after successful SHOCK run"
        assert state_path.exists(), "state file must exist after successful SHOCK run"

        snap = json.loads(snapshot_path.read_text(encoding="utf-8"))
        assert mac.validate_snapshot(snap) == []
        assert snap["status"] == "SHOCK"

        state = json.loads(state_path.read_text(encoding="utf-8"))
        assert "seen" in state


# ---------------------------------------------------------------------------
# R5 -- Deterministic novelty
# ---------------------------------------------------------------------------


class TestR5Novelty:
    def _shock_snap(self, now: datetime) -> dict:
        return _valid_shock_snapshot(now=now)

    def test_first_occurrence_allowed(self) -> None:
        """First SHOCK occurrence is allowed; state records the identity."""
        snap = self._shock_snap(_NOW)
        state: dict = {"version": 1, "seen": []}
        out_snap, new_state = mac.apply_novelty(snap, state, _NOW)
        assert out_snap["status"] == "SHOCK"
        assert len(new_state["seen"]) == 1

    def test_second_occurrence_within_ttl_suppressed(self) -> None:
        """Same identity within the TTL is suppressed to QUIET."""
        snap = self._shock_snap(_NOW)
        state: dict = {"version": 1, "seen": []}

        # First occurrence
        _, state = mac.apply_novelty(snap, state, _NOW)

        # Second occurrence: same entries, same time -> suppressed
        snap2 = self._shock_snap(_NOW + timedelta(hours=12))
        out_snap, new_state = mac.apply_novelty(snap2, state, _NOW + timedelta(hours=12))
        assert out_snap["status"] == "QUIET", (
            "second occurrence of same identity within TTL must be suppressed"
        )

    def test_changed_event_type_for_same_entity_date_allowed(self) -> None:
        """Changed event_type for the same entity+date is a material update; allowed."""
        snap1 = self._shock_snap(_NOW)
        state: dict = {"version": 1, "seen": []}
        _, state = mac.apply_novelty(snap1, state, _NOW)

        # Now same entry but different event_type
        entry = _boj_entry()
        classification2 = _shock_classification(event_type="GEOPOLITICAL_CROSS_ASSET_SHOCK")
        snap2 = mac.build_snapshot([entry], classification2, _NOW + timedelta(hours=1))

        out_snap, new_state = mac.apply_novelty(snap2, state, _NOW + timedelta(hours=1))
        assert out_snap["status"] == "SHOCK", (
            "material update (changed event_type) must not be suppressed"
        )

    def test_occurrence_after_ttl_allowed(self) -> None:
        """After the TTL window expires, the same identity is allowed again."""
        snap = self._shock_snap(_NOW)
        state: dict = {"version": 1, "seen": []}
        _, state = mac.apply_novelty(snap, state, _NOW)

        # Advance past the TTL
        after_ttl = mac.add_trading_days(_NOW, mac.NOVELTY_TTL_TRADING_DAYS) + timedelta(hours=1)
        snap2 = self._shock_snap(after_ttl)
        out_snap, new_state = mac.apply_novelty(snap2, state, after_ttl)
        assert out_snap["status"] == "SHOCK", (
            "occurrence after TTL window must be allowed"
        )

    def test_state_round_trips_through_json(self) -> None:
        """State can be serialized/deserialized through JSON and still work."""
        snap = self._shock_snap(_NOW)
        state: dict = {"version": 1, "seen": []}
        _, state = mac.apply_novelty(snap, state, _NOW)

        # Round-trip through JSON
        state_json = json.dumps(state)
        state_loaded = json.loads(state_json)

        snap2 = self._shock_snap(_NOW + timedelta(hours=1))
        out_snap, _ = mac.apply_novelty(snap2, state_loaded, _NOW + timedelta(hours=1))
        assert out_snap["status"] == "QUIET", (
            "state must round-trip through JSON and suppress correctly"
        )

    def test_add_trading_days_skips_weekend(self) -> None:
        """Friday + 1 trading day must land on Monday."""
        # 2026-06-12 is a Friday
        friday = datetime(2026, 6, 12, 12, 0, 0, tzinfo=timezone.utc)
        assert friday.weekday() == 4, "fixture date must be a Friday"

        result = mac.add_trading_days(friday, 1)
        assert result.weekday() == 0, (
            f"Friday + 1 trading day must land on Monday, got weekday={result.weekday()}"
        )
        expected = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert result == expected

    def test_add_trading_days_multiple_over_weekend(self) -> None:
        """Thursday + 3 trading days = Tuesday (skips Sat/Sun)."""
        # 2026-06-11 is a Thursday
        thursday = datetime(2026, 6, 11, 12, 0, 0, tzinfo=timezone.utc)
        assert thursday.weekday() == 3, "fixture date must be a Thursday"

        result = mac.add_trading_days(thursday, 3)
        # Fri(+1), Mon(+2), Tue(+3)
        expected = datetime(2026, 6, 16, 12, 0, 0, tzinfo=timezone.utc)
        assert result == expected


# ---------------------------------------------------------------------------
# R6 -- Source authority: _domain_in_allowlist
# ---------------------------------------------------------------------------


class TestR6SourceAuthority:
    @pytest.mark.parametrize("domain_source", [
        ("federalreserve.gov", "https://www.federalreserve.gov/news/pressreleases"),
        ("ecb.europa.eu", "https://www.ecb.europa.eu/press/pr/date/2026/html/ecb.mp260612~x.en.html"),
        ("boj.or.jp", "https://www.boj.or.jp/en/x"),
        ("bankofengland.co.uk", "https://www.bankofengland.co.uk/news/2026"),
        ("pbc.gov.cn", "http://www.pbc.gov.cn/en/3688110/article.html"),
    ])
    def test_allowlist_domains_accepted(self, domain_source: tuple[str, str]) -> None:
        _, url = domain_source
        assert mac._domain_in_allowlist(url), f"{url} should be in allowlist"

    def test_subdomain_accepted(self) -> None:
        """A subdomain of an allowlist domain is accepted."""
        assert mac._domain_in_allowlist("https://sub.boj.or.jp/x"), (
            "subdomain of allowlist domain must be accepted"
        )
        assert mac._domain_in_allowlist("https://www.boj.or.jp/x"), (
            "www. subdomain of allowlist domain must be accepted"
        )

    def test_non_allowlist_domain_rejected(self) -> None:
        assert not mac._domain_in_allowlist("https://evil.com/x"), (
            "evil.com must not be in allowlist"
        )

    def test_non_allowlist_domain_with_allowlist_in_path_rejected(self) -> None:
        """Domain not in allowlist even if allowlist name appears in path."""
        assert not mac._domain_in_allowlist("https://evil.com/boj.or.jp/x")


# ---------------------------------------------------------------------------
# R7a -- Workflow contract (macro_awareness.yml)
# ---------------------------------------------------------------------------


class TestR7WorkflowContract:
    _WORKFLOW_PATH = _REPO_ROOT / ".github" / "workflows" / "macro_awareness.yml"

    @classmethod
    def _text(cls) -> str:
        return cls._WORKFLOW_PATH.read_text(encoding="utf-8")

    def test_no_schedule_trigger(self) -> None:
        # The comment in the YAML mentions `schedule:` to explain why it is absent.
        # We want to assert that the `on:` trigger block itself has no schedule entry.
        # Parse the on: block by finding it and checking its immediate contents.
        text = self._text()
        # Strip comment lines before checking for the trigger keyword
        non_comment_lines = [
            line for line in text.splitlines()
            if not line.lstrip().startswith("#")
        ]
        non_comment_text = "\n".join(non_comment_lines)
        assert "schedule:" not in non_comment_text, (
            "macro_awareness.yml must NOT have a schedule: trigger (PRD-187; "
            "cron activation belongs to PRD-188)"
        )

    def test_workflow_dispatch_present(self) -> None:
        assert "workflow_dispatch:" in self._text(), (
            "macro_awareness.yml must have a workflow_dispatch: trigger"
        )

    def test_concurrency_group_named(self) -> None:
        text = self._text()
        assert "concurrency:" in text, "macro_awareness.yml must have a concurrency block"
        assert "group: macro-awareness" in text, (
            "concurrency group must be named 'macro-awareness'"
        )

    def test_concurrency_cancel_in_progress_false(self) -> None:
        assert "cancel-in-progress: false" in self._text(), (
            "concurrency must set cancel-in-progress: false (R7)"
        )

    def test_validate_step_before_commit_step(self) -> None:
        text = self._text()
        validate_idx = text.index("--validate-only")
        commit_idx = text.index("git add -f")
        assert validate_idx < commit_idx, (
            "--validate-only step must appear BEFORE the git add/commit step (R7)"
        )

    def test_git_add_stages_only_two_artifacts(self) -> None:
        text = self._text()
        # Find the git add -f line
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("git add -f"):
                # Must contain exactly the two artifact paths, nothing else
                assert "logs/macro_awareness_snapshot.json" in stripped, (
                    "git add -f must stage logs/macro_awareness_snapshot.json"
                )
                assert "logs/macro_awareness_state.json" in stripped, (
                    "git add -f must stage logs/macro_awareness_state.json"
                )
                # Check that the line contains ONLY these two paths (no others)
                # Strip the command prefix and check remaining tokens are the two paths
                remainder = stripped[len("git add -f"):].strip()
                tokens = remainder.split()
                assert set(tokens) == {
                    "logs/macro_awareness_snapshot.json",
                    "logs/macro_awareness_state.json",
                }, (
                    f"git add -f must stage ONLY the two artifacts, found: {tokens}"
                )
                break
        else:
            pytest.fail("No 'git add -f' line found in macro_awareness.yml")

    def test_ci_push_artifacts_sh_invoked(self) -> None:
        assert "tools/ci_push_artifacts.sh" in self._text(), (
            "macro_awareness.yml must invoke tools/ci_push_artifacts.sh"
        )


# ---------------------------------------------------------------------------
# R7b -- ci_push_artifacts.sh behavior via temp git fixture
# ---------------------------------------------------------------------------

_SCRIPT = _REPO_ROOT / "tools" / "ci_push_artifacts.sh"


def _git(args: list[str], cwd: Path, extra_env: Optional[dict] = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _git_check(args: list[str], cwd: Path, extra_env: Optional[dict] = None) -> subprocess.CompletedProcess:
    result = _git(args, cwd, extra_env)
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {cwd}:\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def _setup_bare_repo_and_clone(tmp_path: Path) -> tuple[Path, Path]:
    """Create a bare 'origin' repo and a work-dir clone with an initial commit on main.
    Returns (bare_path, work_dir_path).
    """
    bare = tmp_path / "origin.git"
    bare.mkdir()
    _git_check(["init", "--bare", str(bare)], tmp_path)

    work = tmp_path / "work"
    _git_check(["clone", str(bare), str(work)], tmp_path)

    # Configure git identity in work dir
    _git_check(["config", "user.email", "test@test.com"], work)
    _git_check(["config", "user.name", "Test"], work)

    # Create initial commit on main
    initial = work / "README.md"
    initial.write_text("initial\n")
    _git_check(["checkout", "-b", "main"], work)
    _git_check(["add", "README.md"], work)
    _git_check(["commit", "-m", "initial commit"], work)
    _git_check(["push", "origin", "main"], work)

    return bare, work


class TestR7CiPushArtifacts:
    def _run_script(
        self,
        cwd: Path,
        pre_sha: Optional[str] = None,
        post_sha: Optional[str] = None,
    ) -> subprocess.CompletedProcess:
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        if pre_sha is not None:
            env["PRE_SHA"] = pre_sha
        else:
            env.pop("PRE_SHA", None)
        if post_sha is not None:
            env["POST_SHA"] = post_sha
        else:
            env.pop("POST_SHA", None)
        return subprocess.run(
            ["bash", str(_SCRIPT)],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def test_no_sha_env_exits_0_prints_skip(self, tmp_path: Path) -> None:
        """Missing PRE_SHA/POST_SHA -> exit 0, prints skip."""
        result = self._run_script(tmp_path)
        assert result.returncode == 0, f"expected exit 0, got {result.returncode}"
        assert "skip" in result.stdout.lower(), (
            f"expected 'skip' in stdout, got: {result.stdout!r}"
        )

    def test_pre_sha_equals_post_sha_exits_0_prints_skip(self, tmp_path: Path) -> None:
        """PRE_SHA == POST_SHA -> exit 0, prints skip."""
        result = self._run_script(tmp_path, pre_sha="abc123", post_sha="abc123")
        assert result.returncode == 0, f"expected exit 0, got {result.returncode}"
        assert "skip" in result.stdout.lower()

    def test_dirty_tree_with_different_shas_exits_1(self, tmp_path: Path) -> None:
        """Dirty tree with PRE_SHA != POST_SHA -> exit 1."""
        bare, work = _setup_bare_repo_and_clone(tmp_path)

        # Add a pre_sha (the current HEAD on origin) and a different post_sha
        pre_sha = _git_check(["rev-parse", "HEAD"], work).stdout.strip()
        post_sha = "0" * 40  # fake different SHA

        # Leave a dirty/unstaged file in the work dir
        dirty_file = work / "dirty.txt"
        dirty_file.write_text("uncommitted change\n")

        result = self._run_script(work, pre_sha=pre_sha, post_sha=post_sha)
        assert result.returncode == 1, (
            f"expected exit 1 for dirty tree, got {result.returncode}; "
            f"stdout={result.stdout!r}"
        )

    def test_happy_rebase_and_push(self, tmp_path: Path) -> None:
        """Happy path: local commit, upstream advance on unrelated file -> rebase + push succeeds."""
        bare, work = _setup_bare_repo_and_clone(tmp_path)

        # Record origin HEAD before any local work
        pre_sha = _git_check(["rev-parse", "HEAD"], work).stdout.strip()

        # Make a local commit in work dir
        artifact = work / "logs"
        artifact.mkdir(exist_ok=True)
        snap_file = artifact / "macro_awareness_snapshot.json"
        snap_file.write_text('{"status":"QUIET"}\n')
        _git_check(["add", str(snap_file)], work)
        _git_check(["commit", "-m", "macro-awareness: 2026-06-14T12:00Z"], work)
        post_sha = _git_check(["rev-parse", "HEAD"], work).stdout.strip()

        # Advance origin/main with an UNRELATED file from a second clone
        work2 = tmp_path / "work2"
        _git_check(["clone", str(bare), str(work2)], tmp_path)
        _git_check(["config", "user.email", "test2@test.com"], work2)
        _git_check(["config", "user.name", "Test2"], work2)
        # The clone already has main tracked from origin; no need to create it
        _git_check(["checkout", "main"], work2)
        unrelated = work2 / "unrelated.txt"
        unrelated.write_text("upstream advance\n")
        _git_check(["add", "unrelated.txt"], work2)
        _git_check(["commit", "-m", "upstream unrelated commit"], work2)
        _git_check(["push", "origin", "main"], work2)

        result = self._run_script(work, pre_sha=pre_sha, post_sha=post_sha)
        assert result.returncode == 0, (
            f"expected exit 0 for happy rebase, got {result.returncode};\n"
            f"stdout={result.stdout}\nstderr={result.stderr}"
        )

        # origin/main must contain both the upstream commit and our local commit
        _git_check(["fetch", "origin", "main"], work)
        log = _git_check(["log", "--oneline", "origin/main"], work).stdout
        assert "upstream unrelated commit" in log, (
            "origin/main must contain the upstream commit after rebase+push"
        )
        assert "macro-awareness" in log, (
            "origin/main must contain the local commit after rebase+push"
        )

    def test_conflict_leaves_origin_unchanged(self, tmp_path: Path) -> None:
        """Conflicting upstream commit -> exit non-zero; origin/main HEAD unchanged."""
        bare, work = _setup_bare_repo_and_clone(tmp_path)

        pre_sha = _git_check(["rev-parse", "HEAD"], work).stdout.strip()

        # Local commit touching README.md
        readme = work / "README.md"
        readme.write_text("local change\n")
        _git_check(["add", "README.md"], work)
        _git_check(["commit", "-m", "local readme change"], work)
        post_sha = _git_check(["rev-parse", "HEAD"], work).stdout.strip()

        # Upstream conflict: also change README.md
        work2 = tmp_path / "work2"
        _git_check(["clone", str(bare), str(work2)], tmp_path)
        _git_check(["config", "user.email", "test2@test.com"], work2)
        _git_check(["config", "user.name", "Test2"], work2)
        _git_check(["checkout", "main"], work2)
        readme2 = work2 / "README.md"
        readme2.write_text("upstream conflicting change\n")
        _git_check(["add", "README.md"], work2)
        _git_check(["commit", "-m", "upstream conflict commit"], work2)
        _git_check(["push", "origin", "main"], work2)
        upstream_sha = _git_check(["rev-parse", "HEAD"], work2).stdout.strip()

        result = self._run_script(work, pre_sha=pre_sha, post_sha=post_sha)
        assert result.returncode != 0, (
            f"expected non-zero exit for conflict, got {result.returncode}"
        )

        # origin/main must still be the upstream commit, not our local commit
        _git_check(["fetch", "origin", "main"], work2)
        origin_head = _git_check(["rev-parse", "origin/main"], work2).stdout.strip()
        assert origin_head == upstream_sha, (
            "origin/main must be unchanged after a conflicting push attempt"
        )


# ---------------------------------------------------------------------------
# R7 -- _validate_only / main(["--validate-only", ...]) entrypoint
# ---------------------------------------------------------------------------


class TestR7ValidateOnly:
    def test_valid_quiet_snapshot_exits_0(self, tmp_path: Path) -> None:
        snap = _valid_quiet_snapshot()
        path = tmp_path / "snapshot.json"
        path.write_text(json.dumps(snap), encoding="utf-8")
        result = mac._validate_only(str(path))
        assert result == 0

    def test_valid_shock_snapshot_exits_0(self, tmp_path: Path) -> None:
        snap = _valid_shock_snapshot()
        path = tmp_path / "snapshot.json"
        path.write_text(json.dumps(snap), encoding="utf-8")
        result = mac._validate_only(str(path))
        assert result == 0

    def test_invalid_snapshot_exits_1(self, tmp_path: Path) -> None:
        snap = {"schema_version": 1}  # missing required keys
        path = tmp_path / "snapshot.json"
        path.write_text(json.dumps(snap), encoding="utf-8")
        result = mac._validate_only(str(path))
        assert result == 1

    def test_missing_file_exits_1(self, tmp_path: Path) -> None:
        result = mac._validate_only(str(tmp_path / "nonexistent.json"))
        assert result == 1

    def test_main_validate_only_flag_dispatches_correctly(self, tmp_path: Path) -> None:
        snap = _valid_quiet_snapshot()
        path = tmp_path / "snapshot.json"
        path.write_text(json.dumps(snap), encoding="utf-8")
        result = mac.main(["--validate-only", str(path)])
        assert result == 0


class TestTransactionalWrite:
    """R4: snapshot + state publish as one coherent generation (both-or-neither).

    Codex push-path review: a failure between the two os.replace calls must not
    leave snapshot new while state stays old."""

    def test_state_replace_failure_rolls_back_snapshot(self, tmp_path: Path) -> None:
        snapshot_path = tmp_path / "snap.json"
        prior = b'{"prior": true}\n'
        snapshot_path.write_bytes(prior)
        # Make the state target a directory so state_tmp.replace(state_path) fails.
        state_path = tmp_path / "state.json"
        state_path.mkdir()
        with pytest.raises(Exception):
            mac._write_atomic(
                _valid_quiet_snapshot(), {"version": 1, "seen": []},
                snapshot_path, state_path,
            )
        # both-or-neither: snapshot is rolled back to its prior generation
        assert snapshot_path.read_bytes() == prior
        assert not (tmp_path / "snap.json.tmp").exists()

    def test_run_returns_1_on_write_failure_preserving_prior(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
        snapshot_path = tmp_path / "snap.json"
        prior = b'{"prior": true}\n'
        snapshot_path.write_bytes(prior)
        state_path = tmp_path / "state.json"
        state_path.mkdir()  # force the state replace to fail
        rc = mac.run(
            now=_NOW,
            snapshot_path=snapshot_path,
            state_path=state_path,
            fetch_fn=lambda n: [],
            classify_fn=lambda e: {
                "shock_present": False, "selected_index": None, "event_type": None,
            },
        )
        assert rc == 1
        assert snapshot_path.read_bytes() == prior


class TestSourceFailureContract:
    """R4 all-or-preserve: any required feed unreachable -> preserve prior, no
    write; distinct from genuine QUIET (all feeds read, nothing material)."""

    @staticmethod
    def _fed_fails(url: str, timeout: float) -> Optional[bytes]:
        # One required feed (Fed, first in FEED_SOURCES) unreachable.
        return None if "federalreserve.gov" in url else b"<rss></rss>"

    def test_required_feed_unreachable_raises(self) -> None:
        with pytest.raises(RuntimeError):
            mac.fetch_entries(_NOW, retries=1, _get=self._fed_fails)

    def test_source_failure_preserves_prior_no_write(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
        snap = tmp_path / "s.json"
        st = tmp_path / "st.json"
        snap.write_bytes(b'{"prior": 1}\n')
        st.write_bytes(b'{"prior_state": 1}\n')
        rc = mac.run(
            now=_NOW, snapshot_path=snap, state_path=st,
            fetch_fn=lambda n: mac.fetch_entries(n, retries=1, _get=self._fed_fails),
            classify_fn=lambda e: _quiet_classification(),
        )
        assert rc == 1
        # nothing overwritten: both prior generations are byte-identical
        assert snap.read_bytes() == b'{"prior": 1}\n'
        assert st.read_bytes() == b'{"prior_state": 1}\n'

    def test_genuine_quiet_writes_when_all_feeds_read(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
        snap = tmp_path / "s.json"
        st = tmp_path / "st.json"
        rc = mac.run(
            now=_NOW, snapshot_path=snap, state_path=st,
            fetch_fn=lambda n: [],  # all feeds reachable, nothing recent in window
            classify_fn=lambda e: _quiet_classification(),
        )
        assert rc == 0
        assert json.loads(snap.read_text())["status"] == "QUIET"


class TestExcerptCap:
    """R3: excerpt capped to EXCERPT_MAX AND fully HTML-escaped (no severed entity)."""

    def test_cap_does_not_sever_entity(self) -> None:
        raw = "A" * 278 + "<>"  # escaped exceeds the cap; a naive cut severs "&lt;"
        out = mac._capped_excerpt(raw)
        assert len(out) <= mac.EXCERPT_MAX
        assert html.escape(html.unescape(out)) == out  # fully escaped, no dangling entity
        assert "<" not in out and ">" not in out

    def test_build_snapshot_special_chars_near_cap_validates(self) -> None:
        entry = _boj_entry(title="<script>&\"'" + "Q" * 400, summary="R" * 400)
        snap = mac.build_snapshot([entry], _shock_classification(0), _NOW)
        assert snap["status"] == "SHOCK"
        assert mac.validate_snapshot(snap) == []
        ex = snap["shock"]["source_excerpt"]
        assert len(ex) <= mac.EXCERPT_MAX
        assert "<script>" not in ex
