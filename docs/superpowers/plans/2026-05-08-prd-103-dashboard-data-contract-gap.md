# PRD-103 Dashboard Data Contract Gap Patch — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Patch contract, runtime, payload, and renderer so outcome/permission/confidence/reason are truthfully non-null in the dashboard.

**Architecture:** Five targeted fixes, each preceded by a failing test. All changes are additive (no contract key removals). The renderer falls back to payload when run field is None. The run-delta label changes from SOURCE_MISSING to NO_PREVIOUS_RUN when previous_run is absent.

**Tech Stack:** Python 3.13, pytest, existing contract/payload/renderer modules in cuttingboard/.

---

## File Map

| File | Change |
|------|--------|
| `cuttingboard/contract.py` | Add `confidence` to `_build_system_state()` return dict (line ~225) |
| `cuttingboard/runtime.py` | (a) Inject `outcome`/`permission`/`reason` into `contract["system_state"]` after line 942; (b) Fix `"permission": None` → derived in `_build_hourly_run_summary()` around line 1790 |
| `cuttingboard/delivery/payload.py` | Add `outcome`, `confidence`, `permission` to `summary` dict in `build_report_payload()` (line ~113) |
| `cuttingboard/delivery/dashboard_renderer.py` | (a) Fallback `permission` from `payload["summary"]` when `run.get("permission")` is None; (b) Render `NO_PREVIOUS_RUN` when `previous_run is None` (line ~1238) |
| `tests/test_contract.py` | Add `TestSystemStateDashboardFields` class |
| `tests/test_payload.py` | Add tests for new summary fields |
| `tests/test_dash_system_state.py` | Add test: Permission shows payload value when run.permission is None |
| `tests/test_dash_run_history.py` | Add test: NO_PREVIOUS_RUN not SOURCE_MISSING |

---

## Task 1 — Add `confidence` to contract system_state

**Files:**
- Modify: `cuttingboard/contract.py:225-231` (`_build_system_state` return dict)
- Test: `tests/test_contract.py`

- [ ] **Step 1.1: Write the failing test**

Add to `tests/test_contract.py` (inside or after `TestSuccessfulRun`):

```python
class TestSystemStateDashboardFields:
    def setup_method(self):
        pr = _FakePipelineResult(regime=_regime(confidence=0.75))
        self.contract = _build(pr)

    def test_system_state_confidence_float_when_regime_present(self):
        assert isinstance(self.contract["system_state"].get("confidence"), float)
        assert self.contract["system_state"]["confidence"] == 0.75

    def test_system_state_confidence_none_when_no_regime(self):
        pr = _FakePipelineResult(regime=None)
        contract = _build(pr)
        assert contract["system_state"].get("confidence") is None
```

- [ ] **Step 1.2: Run test to verify it fails**

```bash
python3 -m pytest tests/test_contract.py::TestSystemStateDashboardFields -v
```

Expected: FAIL — `test_system_state_confidence_float_when_regime_present` fails because `"confidence"` key is absent from system_state.

- [ ] **Step 1.3: Implement the fix**

In `cuttingboard/contract.py`, `_build_system_state()` return dict (around line 225), add the `confidence` entry:

```python
    return {
        "router_mode": router_mode,
        "market_regime": _safe_str(regime.regime) if regime else None,
        "intraday_state": intraday_state,
        "time_gate_open": time_gate_open,
        "tradable": bool(tradable),
        "stay_flat_reason": stay_flat_reason,
        "confidence": float(regime.confidence) if regime is not None else None,
    }
```

- [ ] **Step 1.4: Run tests**

```bash
python3 -m pytest tests/test_contract.py::TestSystemStateDashboardFields tests/test_contract.py -q
```

Expected: All pass including the new class and all existing contract tests.

- [ ] **Step 1.5: Compile check**

```bash
python3 -m py_compile cuttingboard/contract.py
```

Expected: no output (clean).

- [ ] **Step 1.6: Commit**

```bash
git add cuttingboard/contract.py tests/test_contract.py
git commit -m "PRD-103: add confidence to system_state in contract builder"
```

---

## Task 2 — Inject outcome/permission/reason into system_state in runtime

**Files:**
- Modify: `cuttingboard/runtime.py` (around line 942 — after `contract["outcome"] = outcome`)
- Test: `tests/test_contract.py` (add to `TestSystemStateDashboardFields`)

Note: This requires understanding how runtime injections work. The contract dict is mutable after `build_pipeline_output_contract()`. The production path already does `contract["system_state"]["stay_flat_reason"] = ...` at line 950. We follow the same pattern.

`_PERMISSION_LINES` and `_summary_regime_fields` are already defined in runtime.py.

- [ ] **Step 2.1: Find the injection point and helpers**

```bash
grep -n "_PERMISSION_LINES\|_summary_regime_fields" cuttingboard/runtime.py | head -10
```

Note the line numbers of `_PERMISSION_LINES` dict definition and `_summary_regime_fields` function.

- [ ] **Step 2.2: Write the failing test**

These tests cannot use `_build()` from test_contract.py because that bypasses runtime injection. The system_state fields injected by runtime.py are tested by inspecting a mock of the runtime path OR by verifying the contract dict shape after the injection block runs.

For contract-level testing without running the full pipeline, add a standalone test in `tests/test_contract.py`:

```python
def test_system_state_outcome_permission_reason_injectable():
    """Verify system_state dict accepts outcome/permission/reason without assert_valid_contract raising."""
    pr = _FakePipelineResult(regime=_regime())
    contract = _build(pr)
    # Simulate runtime.py injection
    contract["system_state"]["outcome"] = "NO_TRADE"
    contract["system_state"]["permission"] = "No new trades permitted."
    contract["system_state"]["reason"] = None
    assert_valid_contract(contract)  # must not raise
    assert contract["system_state"]["outcome"] == "NO_TRADE"
    assert contract["system_state"]["permission"] == "No new trades permitted."
    assert contract["system_state"]["reason"] is None
```

- [ ] **Step 2.3: Run to verify it passes (verifies assert_valid_contract tolerates new keys)**

```bash
python3 -m pytest tests/test_contract.py::test_system_state_outcome_permission_reason_injectable -v
```

Expected: PASS — confirms the contract validator does not reject extra keys in system_state.

- [ ] **Step 2.4: Add the runtime injection**

In `cuttingboard/runtime.py`, after line `contract["outcome"] = outcome` (line ~942) and before the `apply_overnight_policy` call, add:

```python
    contract["outcome"] = outcome
    # Inject dashboard-readable fields into system_state
    _ss_regime_label, _ss_posture_label, _ss_conf, _ = _summary_regime_fields(regime)
    _ss_perm = _PERMISSION_LINES.get(_ss_posture_label, "No new trades permitted.")
    if validation_summary.system_halted:
        _ss_perm = "No trades permitted. System halted."
    contract["system_state"]["outcome"] = outcome
    contract["system_state"]["permission"] = _ss_perm
    contract["system_state"]["reason"] = contract["system_state"].get("stay_flat_reason")
```

- [ ] **Step 2.5: Compile check**

```bash
python3 -m py_compile cuttingboard/runtime.py
```

Expected: no output.

- [ ] **Step 2.6: Run full test suite**

```bash
python3 -m pytest tests -q 2>&1 | tail -5
```

Expected: same pass count as baseline (2081) or higher; 0 new failures.

- [ ] **Step 2.7: Commit**

```bash
git add cuttingboard/runtime.py tests/test_contract.py
git commit -m "PRD-103: inject outcome/permission/reason into system_state after contract build"
```

---

## Task 3 — Fix permission=None in hourly run summary

**Files:**
- Modify: `cuttingboard/runtime.py` (`_build_hourly_run_summary()` around line 1790)
- Test: `tests/test_dash_system_state.py`

- [ ] **Step 3.1: Confirm the hardcoded None**

```bash
grep -n '"permission": None' cuttingboard/runtime.py
```

Expected: shows one hit in `_build_hourly_run_summary()`.

- [ ] **Step 3.2: Write the failing test**

The hourly run summary is built in runtime.py's `_build_hourly_run_summary()`. The dashboard reads `run.get("permission")`. Add to `tests/test_dash_system_state.py`:

```python
def test_system_state_permission_shows_from_run_when_non_null() -> None:
    """Permission shows the run value when run.permission is a non-null string."""
    r = _run(permission="No new trades permitted.")
    html = render_dashboard_html(_payload(), r)
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Permission" in state
    assert "No new trades permitted." in state
    assert "&#8212;" not in state
```

- [ ] **Step 3.3: Run test to verify it passes (it should already pass because render uses run["permission"] when non-None)**

```bash
python3 -m pytest tests/test_dash_system_state.py::test_system_state_permission_shows_from_run_when_non_null -v
```

Expected: PASS — confirms the renderer correctly shows non-None permission from run.

- [ ] **Step 3.4: Implement the fix in _build_hourly_run_summary()**

In `cuttingboard/runtime.py`, in `_build_hourly_run_summary()`, locate the `"permission": None` line (around line 1790). Replace it with:

```python
        # Derive permission from regime posture (matches _build_run_summary_dict logic)
        _hrly_regime_label, _hrly_posture_label, _, _ = _summary_regime_fields(regime)
        _hrly_perm = _PERMISSION_LINES.get(_hrly_posture_label, "No new trades permitted.")
        if validation_summary is not None and validation_summary.system_halted:
            _hrly_perm = "No trades permitted. System halted."
```

And change the dict entry from:
```python
        "permission": None,
```
to:
```python
        "permission": _hrly_perm,
```

- [ ] **Step 3.5: Compile check**

```bash
python3 -m py_compile cuttingboard/runtime.py
```

- [ ] **Step 3.6: Run test suite**

```bash
python3 -m pytest tests -q 2>&1 | tail -5
```

Expected: all existing tests pass. The old `test_system_state_permission_shows_dash_when_none` may now need update if it creates run with `permission=None` and expects a dash — check that test still passes.

- [ ] **Step 3.7: Commit**

```bash
git add cuttingboard/runtime.py tests/test_dash_system_state.py
git commit -m "PRD-103: derive permission from posture in hourly run summary"
```

---

## Task 4 — Payload adapter: surface outcome/confidence/permission in summary

**Files:**
- Modify: `cuttingboard/delivery/payload.py` (`build_report_payload()` around line 113)
- Test: `tests/test_payload.py`

- [ ] **Step 4.1: Write the failing tests**

Add to `tests/test_payload.py` (in a new class or after existing tests):

```python
def test_summary_outcome_field_present():
    """payload["summary"]["outcome"] is populated from system_state."""
    from tests.test_payload import _build_contract  # use existing contract builder helper
    # Build a minimal contract with system_state containing outcome
    # Use the existing contract fixture from test_payload.py
    p = build_report_payload(_contract_with_system_state(outcome="NO_TRADE", confidence=0.75, permission="No new trades permitted."))
    assert p["summary"].get("outcome") == "NO_TRADE"

def test_summary_confidence_field_present():
    p = build_report_payload(_contract_with_system_state(outcome="NO_TRADE", confidence=0.75, permission="No new trades permitted."))
    assert p["summary"].get("confidence") == 0.75

def test_summary_permission_field_present():
    p = build_report_payload(_contract_with_system_state(outcome="NO_TRADE", confidence=0.75, permission="No new trades permitted."))
    assert p["summary"].get("permission") == "No new trades permitted."

def test_assert_valid_payload_passes_with_new_summary_fields():
    p = build_report_payload(_contract_with_system_state(outcome="NO_TRADE", confidence=0.75, permission="No new trades permitted."))
    assert_valid_payload(p)  # must not raise
```

You will need a helper `_contract_with_system_state`. Look at the existing `_minimal_contract()` helper in `tests/test_payload.py` and extend it:

```python
def _contract_with_system_state(outcome: str, confidence: float, permission: str) -> dict:
    c = _minimal_contract()  # existing helper
    c["system_state"]["outcome"] = outcome
    c["system_state"]["confidence"] = confidence
    c["system_state"]["permission"] = permission
    return c
```

Find `_minimal_contract()` definition in `tests/test_payload.py` first:
```bash
grep -n "_minimal_contract\|def _minimal" tests/test_payload.py | head -5
```

- [ ] **Step 4.2: Run failing tests**

```bash
python3 -m pytest tests/test_payload.py -k "summary_outcome or summary_confidence or summary_permission or new_summary_fields" -v
```

Expected: FAIL — keys absent from summary.

- [ ] **Step 4.3: Implement the fix**

In `cuttingboard/delivery/payload.py`, in `build_report_payload()`, after the existing `ss.get()` calls, add:

```python
    outcome_val = ss.get("outcome")
    confidence_val = ss.get("confidence")
    permission_val = ss.get("permission")
```

Then update the `"summary"` dict (around line 113):

```python
    return {
        ...
        "summary": {
            "market_regime": market_regime,
            "tradable": tradable,
            "router_mode": router_mode,
            "outcome": outcome_val,
            "confidence": confidence_val,
            "permission": permission_val,
        },
        ...
    }
```

- [ ] **Step 4.4: Compile check**

```bash
python3 -m py_compile cuttingboard/delivery/payload.py
```

- [ ] **Step 4.5: Run payload tests**

```bash
python3 -m pytest tests/test_payload.py -q
```

Expected: all pass.

- [ ] **Step 4.6: Run full suite**

```bash
python3 -m pytest tests -q 2>&1 | tail -5
```

Expected: baseline or better.

- [ ] **Step 4.7: Commit**

```bash
git add cuttingboard/delivery/payload.py tests/test_payload.py
git commit -m "PRD-103: surface outcome/confidence/permission in payload summary"
```

---

## Task 5 — Dashboard renderer: permission fallback and NO_PREVIOUS_RUN label

**Files:**
- Modify: `cuttingboard/delivery/dashboard_renderer.py`
  - (a) Permission fallback: around line 931 where `permission = run.get("permission")`
  - (b) SOURCE_MISSING → NO_PREVIOUS_RUN: around line 1238
- Test: `tests/test_dash_system_state.py`, `tests/test_dash_run_history.py`

- [ ] **Step 5.1: Write failing test for NO_PREVIOUS_RUN**

Add to `tests/test_dash_run_history.py`:

```python
def test_run_delta_no_previous_run_shows_no_previous_run() -> None:
    """When previous_run is None, Changes Since Last Run shows NO_PREVIOUS_RUN not SOURCE_MISSING."""
    html = render_dashboard_html(_payload(), _run(), previous_run=None)
    delta = html.split('id="run-delta"', 1)[1].split('id="run-history"', 1)[0]
    assert "NO_PREVIOUS_RUN" in delta
    assert "SOURCE_MISSING" not in delta
```

- [ ] **Step 5.2: Run test to verify it fails**

```bash
python3 -m pytest tests/test_dash_run_history.py::test_run_delta_no_previous_run_shows_no_previous_run -v
```

Expected: FAIL — finds SOURCE_MISSING, not NO_PREVIOUS_RUN.

- [ ] **Step 5.3: Write failing test for permission fallback**

Add to `tests/test_dash_system_state.py`:

```python
def test_system_state_permission_falls_back_to_payload_when_run_none() -> None:
    """When run.permission is None, Permission shows payload["summary"]["permission"] value."""
    payload_with_perm = _payload()
    payload_with_perm["summary"]["permission"] = "No new trades permitted."
    r = _run(permission=None)
    html = render_dashboard_html(payload_with_perm, r)
    state = html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Permission" in state
    assert "No new trades permitted." in state
```

- [ ] **Step 5.4: Run test to verify it fails**

```bash
python3 -m pytest tests/test_dash_system_state.py::test_system_state_permission_falls_back_to_payload_when_run_none -v
```

Expected: FAIL — currently shows &#8212; (dash) when run.permission is None.

- [ ] **Step 5.5: Implement fix (a) — NO_PREVIOUS_RUN label**

In `cuttingboard/delivery/dashboard_renderer.py`, in the `# --- run-delta ---` section (around line 1238), change:

```python
    if previous_run is None:
        w('  <div class="value">SOURCE_MISSING</div>')
```

to:

```python
    if previous_run is None:
        w('  <div class="value">NO_PREVIOUS_RUN</div>')
```

- [ ] **Step 5.6: Implement fix (b) — permission fallback from payload**

In `cuttingboard/delivery/dashboard_renderer.py`, after `permission = run.get("permission")` (around line 932), add a fallback:

```python
    outcome    = run.get("outcome")
    permission = run.get("permission")
    if permission is None:
        permission = payload.get("summary", {}).get("permission")
```

Note: this fallback must be added BEFORE the `action_text` and the system-state rendering that reads `permission`. The `permission` variable is used in the action_text block (line ~938) and in the Permission field rendering (line ~1034).

- [ ] **Step 5.7: Compile check**

```bash
python3 -m py_compile cuttingboard/delivery/dashboard_renderer.py
```

- [ ] **Step 5.8: Run dashboard tests**

```bash
python3 -m pytest tests/test_dash_system_state.py tests/test_dash_run_history.py -q
```

Expected: all pass including new tests.

- [ ] **Step 5.9: Run full suite**

```bash
python3 -m pytest tests -q 2>&1 | tail -5
```

Expected: baseline or better (2081+).

- [ ] **Step 5.10: Commit**

```bash
git add cuttingboard/delivery/dashboard_renderer.py tests/test_dash_system_state.py tests/test_dash_run_history.py
git commit -m "PRD-103: NO_PREVIOUS_RUN label and permission payload fallback in renderer"
```

---

## Task 6 — Final compile, full test run, artifact regeneration

**Files:**
- `ui/dashboard.html`, `ui/index.html`

- [ ] **Step 6.1: Final compile check on all touched files**

```bash
python3 -m py_compile \
  cuttingboard/runtime.py \
  cuttingboard/contract.py \
  cuttingboard/delivery/payload.py \
  cuttingboard/delivery/dashboard_renderer.py
```

Expected: no output.

- [ ] **Step 6.2: Full test suite**

```bash
python3 -m pytest tests -q 2>&1 | tail -10
```

Expected: 2081+ passing, 0 failures.

- [ ] **Step 6.3: Regenerate dashboard artifacts**

```bash
python3 -m cuttingboard.delivery.dashboard_renderer --output ui/dashboard.html
cp ui/dashboard.html ui/index.html
```

- [ ] **Step 6.4: Verify dashboard content**

```bash
grep -n "SOURCE_MISSING\|Permission\|Artifact diagnostics\|History\|NO_DATA\|UNAVAILABLE\|NO_PREVIOUS_RUN" ui/dashboard.html | head -40
```

Expected:
- No line contains `SOURCE_MISSING` (in run-delta)
- `Permission` label appears with a non-dash value
- `History` summary element present
- `Artifact diagnostics` summary present

- [ ] **Step 6.5: Verify diff stat**

```bash
git diff --stat
```

Expected: shows changes to `ui/dashboard.html` and `ui/index.html`.

- [ ] **Step 6.6: Commit artifacts**

```bash
git add ui/dashboard.html ui/index.html
git commit -m "PRD-103: regenerate dashboard artifacts with permission/NO_PREVIOUS_RUN fixes"
```

---

## Task 7 — Close PRD

- [ ] **Step 7.1: Update PROJECT_STATE.md**

In `docs/PROJECT_STATE.md`, update:
- `Last updated:` → 2026-05-08
- `Last completed PRD:` → PRD-103 - Dashboard Data Contract Gap Patch (commit hash TBD)
- `Active PRD:` → none

- [ ] **Step 7.2: Update PRD_REGISTRY.md**

Set PRD-103 row to `COMPLETE` and record commit hash.

- [ ] **Step 7.3: Update PRD-103.md**

Change `STATUS` from `IN PROGRESS` to `COMPLETE`.

- [ ] **Step 7.4: Commit bookkeeping**

```bash
git add docs/PROJECT_STATE.md docs/PRD_REGISTRY.md docs/prd_history/PRD-103.md
git commit -m "PRD-103: mark complete in registry and state"
```

---

## Self-Review

**Spec coverage check:**
- R1 (confidence in system_state) → Task 1 ✓
- R2 (outcome/permission/reason injected) → Task 2 ✓
- R3 (hourly run permission non-null) → Task 3 ✓
- R4 (payload summary carries fields) → Task 4 ✓
- R5 (dashboard Permission shows payload value) → Task 5 fix (b) ✓
- R6 (NO_PREVIOUS_RUN not SOURCE_MISSING) → Task 5 fix (a) ✓
- R7 (history/diagnostics explicit messages) → existing code already handles NO_HISTORY; no empty div possible ✓

**No placeholders:** all code blocks are complete.

**Type consistency:**
- `confidence` is `float | None` throughout (contract → ss.get → payload → renderer read)
- `permission` is `str | None` throughout
- `outcome` is `str | None` throughout
