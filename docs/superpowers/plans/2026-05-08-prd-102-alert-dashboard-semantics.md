# PRD-102: Alert and Dashboard Candidate Semantics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate user-facing contradictions between Telegram alerts, System State, and the dashboard Candidate Board by making each surface consume and label the correct semantic layer.

**Architecture:** Load full `trade_candidates` from `latest_hourly_contract.json` into the dashboard renderer (currently only entry prices are loaded). Derive an `alert_candidates` list (non-ALLOW_TRADE candidates) and pass it to `render_dashboard_html`. Use it to (1) fix the System State reason, (2) add an Alert Watchlist section, and (3) rename the Candidate Board to "Market Map / Developing Setups".

**Tech Stack:** Python, pytest, `cuttingboard/delivery/dashboard_renderer.py`, `tests/test_dashboard_renderer.py`, `tests/test_dash_system_state.py`, `tests/test_dash_candidates.py`

---

## File Map

| File | Change |
|------|--------|
| `cuttingboard/delivery/dashboard_renderer.py` | Load full contract candidates; add `alert_candidates` param; fix System State reason; add Alert Watchlist section; rename Candidate Board |
| `tests/test_dashboard_renderer.py` | Update `test_permission_none_shows_reason_line` — old assertion "No candidate passed qualification" is replaced |
| `tests/test_dash_system_state.py` | Add two new reason tests: "candidates gated" and "no qualified candidates" |
| `tests/test_dash_candidates.py` | Add Alert Watchlist section tests + Candidate Board rename tests |
| `tests/dash_helpers.py` | No changes needed — `_trade_decision()` helper already exists |
| `docs/prd_history/PRD-102.md` | Create from template |
| `docs/PRD_REGISTRY.md` | Add PRD-102 row as IN PROGRESS |

---

## Task 1: Create PRD-102 file and register it

**Files:**
- Create: `docs/prd_history/PRD-102.md`
- Modify: `docs/PRD_REGISTRY.md`

- [ ] **Step 1: Create PRD-102.md**

```markdown
# PRD-102 — Align Alert, System State, and Candidate Board Semantics

**Status:** IN PROGRESS
**Date:** 2026-05-08

## GOAL
Eliminate user-facing contradictions between Telegram alerts, System State, and the dashboard Candidate Board by making each surface consume and label the correct semantic layer.

## SCOPE
- dashboard_renderer.py: load full contract candidates, add alert_candidates param
- System State reason distinguishes gated vs. no candidates
- Alert Watchlist section shows non-ALLOW_TRADE candidates (same as Telegram WATCHLIST)
- Candidate Board renamed to Market Map / Developing Setups
- Tests for all new behaviors

## OUT OF SCOPE
- No changes to regime scoring
- No changes to trade qualification
- No changes to market map grading
- No new symbols
- No Telegram transport changes
- No artifact push changes
- No dashboard redesign beyond labels/section consistency

## FILES
- cuttingboard/delivery/dashboard_renderer.py
- tests/test_dashboard_renderer.py
- tests/test_dash_system_state.py
- tests/test_dash_candidates.py

## REQUIREMENTS

R1. System State reason when permission=None and stay_flat_reason=None:
    - alert_candidates non-empty → "candidates gated"
    - alert_candidates empty → "no qualified candidates"
    FAIL: either message absent from rendered HTML in matching scenario.

R2. Alert Watchlist section (id="alert-watchlist") present when alert_candidates non-empty.
    FAIL: section absent when alert_candidates passed with at least one entry.

R3. Alert Watchlist section absent when alert_candidates is None or empty.
    FAIL: section present when no alert_candidates provided.

R4. Alert Watchlist shows each candidate's SYMBOL DIRECTION.
    FAIL: symbol or direction text absent from alert-watchlist block.

R5. Candidate Board heading is "Market Map / Developing Setups" (not "Candidate Board").
    FAIL: old heading text "Candidate Board" (without "DEMO MODE") present in rendered HTML.

R6. Existing tests pass without regressions.
    FAIL: any previously-passing test fails.

## DATA FLOW
contract["trade_candidates"] → filter decision_status != ALLOW_TRADE → alert_candidates
alert_candidates → render_dashboard_html(alert_candidates=...) → Alert Watchlist section

## FAIL CONDITIONS
- "No candidate passed qualification." appears in dashboard
- alert_candidates candidates not shown in dashboard when Telegram would show WATCHLIST

## VALIDATION
python3 -m pytest tests -q
grep -R "Candidate Board\|Alert Watchlist\|Market Map\|Developing Setups" cuttingboard tests ui
grep -R "No candidate passed qualification\|candidates gated\|no qualified candidates" cuttingboard tests
```

- [ ] **Step 2: Add PRD-102 row to PRD_REGISTRY.md**

Open `docs/PRD_REGISTRY.md` and add this row in the table (after PRD-101):
```
| PRD-102 | — | Align Alert and Dashboard Candidate Semantics | IN PROGRESS | [PRD-102](prd_history/PRD-102.md) |
```

- [ ] **Step 3: Commit PRD scaffolding**

```bash
git add docs/prd_history/PRD-102.md docs/PRD_REGISTRY.md
git commit -m "Register PRD-102 in registry and state"
```

---

## Task 2: Add failing tests for System State reason

These tests must fail before implementation — that's the point.

**Files:**
- Modify: `tests/test_dash_system_state.py`
- Modify: `tests/test_dashboard_renderer.py`

- [ ] **Step 1: Update the existing test that asserts old "No candidate passed qualification" text**

In `tests/test_dashboard_renderer.py`, find `test_permission_none_shows_reason_line` (around line 809) and change the assertion from:

```python
assert "No candidate passed qualification" in state
```

to:

```python
assert "no qualified candidates" in state
```

- [ ] **Step 2: Add two new tests to test_dash_system_state.py**

Append these two tests at the end of `tests/test_dash_system_state.py`:

```python
def test_system_state_reason_no_candidates() -> None:
    """When permission=None, stay_flat=None, no alert_candidates: reason is 'no qualified candidates'."""
    html = render_dashboard_html(_payload(validation_halt_detail=None), _run(permission=None), alert_candidates=[])
    state = html.split('id="system-state"', 1)[1].split('id="alert-watchlist"', 1)[0] if 'id="alert-watchlist"' in html else html.split('id="system-state"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "Reason" in state
    assert "no qualified candidates" in state
    assert "candidates gated" not in state


def test_system_state_reason_candidates_gated() -> None:
    """When permission=None, stay_flat=None, and alert_candidates non-empty: reason is 'candidates gated'."""
    from tests.dash_helpers import _trade_decision
    gated = [_trade_decision("META", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION")]
    html = render_dashboard_html(_payload(validation_halt_detail=None), _run(permission=None), alert_candidates=gated)
    state = html.split('id="system-state"', 1)[1].split('id="alert-watchlist"', 1)[0]
    assert "Reason" in state
    assert "candidates gated" in state
    assert "no qualified candidates" not in state
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
python3 -m pytest tests/test_dash_system_state.py::test_system_state_reason_no_candidates tests/test_dash_system_state.py::test_system_state_reason_candidates_gated tests/test_dashboard_renderer.py::test_permission_none_shows_reason_line -v
```

Expected: all 3 FAIL (either TypeError: unexpected keyword `alert_candidates`, or assertion error)

---

## Task 3: Add failing tests for Alert Watchlist section

**Files:**
- Modify: `tests/test_dash_candidates.py`

- [ ] **Step 1: Add Alert Watchlist tests**

Append these tests to `tests/test_dash_candidates.py`:

```python
# ---------------------------------------------------------------------------
# R2 / R3 / R4 — Alert Watchlist Section
# ---------------------------------------------------------------------------

def test_alert_watchlist_absent_when_no_candidates() -> None:
    """No alert-watchlist section when alert_candidates is not provided."""
    html = render_dashboard_html(_payload(), _run())
    assert 'id="alert-watchlist"' not in html


def test_alert_watchlist_absent_when_empty_candidates() -> None:
    """No alert-watchlist section when alert_candidates is an empty list."""
    html = render_dashboard_html(_payload(), _run(), alert_candidates=[])
    assert 'id="alert-watchlist"' not in html


def test_alert_watchlist_present_when_candidates() -> None:
    """Alert Watchlist section present when alert_candidates provided."""
    from tests.dash_helpers import _trade_decision
    gated = [_trade_decision("META", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION")]
    html = render_dashboard_html(_payload(), _run(), alert_candidates=gated)
    assert 'id="alert-watchlist"' in html


def test_alert_watchlist_shows_symbol_and_direction() -> None:
    """Alert Watchlist section shows symbol and direction for each candidate."""
    from tests.dash_helpers import _trade_decision
    gated = [
        _trade_decision("META", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION"),
        _trade_decision("XLE", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION"),
    ]
    html = render_dashboard_html(_payload(), _run(), alert_candidates=gated)
    block = html.split('id="alert-watchlist"', 1)[1].split('id="candidate-board"', 1)[0]
    assert "META" in block
    assert "LONG" in block
    assert "XLE" in block


def test_alert_watchlist_positioned_before_candidate_board() -> None:
    """alert-watchlist section appears before candidate-board in DOM."""
    from tests.dash_helpers import _trade_decision
    gated = [_trade_decision("NVDA", "LONG", decision_status="BLOCK_TRADE", block_reason="LATE_SESSION")]
    html = render_dashboard_html(_payload(), _run(), alert_candidates=gated)
    assert html.index('id="alert-watchlist"') < html.index('id="candidate-board"')


# ---------------------------------------------------------------------------
# R5 — Candidate Board Rename
# ---------------------------------------------------------------------------

def test_candidate_board_renamed_to_market_map() -> None:
    """Candidate Board heading is renamed to Market Map / Developing Setups."""
    html = render_dashboard_html(_payload(), _run())
    assert "Market Map / Developing Setups" in html
    # Old label must not appear (except in fixture mode which has its own label)
    board = html.split('id="candidate-board"', 1)[1].split('</div>', 1)[0]
    assert "Candidate Board" not in board
```

- [ ] **Step 2: Run new candidate tests to confirm they fail**

```bash
python3 -m pytest tests/test_dash_candidates.py::test_alert_watchlist_absent_when_no_candidates tests/test_dash_candidates.py::test_alert_watchlist_present_when_candidates tests/test_dash_candidates.py::test_alert_watchlist_shows_symbol_and_direction tests/test_dash_candidates.py::test_candidate_board_renamed_to_market_map -v
```

Expected: FAIL (render_dashboard_html does not accept `alert_candidates` yet)

---

## Task 4: Implement — add `alert_candidates` parameter and load it in `main()`

**Files:**
- Modify: `cuttingboard/delivery/dashboard_renderer.py`

This task adds the plumbing only. No rendering changes yet.

- [ ] **Step 1: Add import for ALLOW_TRADE in dashboard_renderer.py**

At the top of `cuttingboard/delivery/dashboard_renderer.py`, after the existing import:
```python
from cuttingboard.macro_pressure import build_macro_pressure
```

Add:
```python
from cuttingboard.trade_decision import ALLOW_TRADE
```

- [ ] **Step 2: Replace `_load_contract_entry_context` to also return alert_candidates**

Find the function `_load_contract_entry_context` (around line 1356) and replace it with:

```python
def _load_contract_entry_context(logs_dir: Path) -> tuple[dict[str, float], list[dict], object | None, Path]:
    """Load latest_hourly_contract entry prices, alert_candidates, and generated_at timestamp."""
    path = logs_dir / _HOURLY_CONTRACT_PATH.name
    contract = _load_json_optional(path)
    if not contract:
        return {}, [], None, path
    entry_map: dict[str, float] = {}
    alert_candidates: list[dict] = []
    for cand in (contract.get("trade_candidates") or []):
        sym = cand.get("symbol")
        val = cand.get("entry")
        if sym and val is not None:
            try:
                entry_map[sym] = float(val)
            except (TypeError, ValueError):
                pass
        if cand.get("decision_status") != ALLOW_TRADE:
            alert_candidates.append(cand)
    return entry_map, alert_candidates, contract.get("generated_at"), path
```

- [ ] **Step 3: Update `main()` to unpack the new return value**

Find the line in `main()` (around line 1397):
```python
contract_entry_map_raw, contract_generated_at, contract_source = _load_contract_entry_context(logs_dir)
```

Replace with:
```python
contract_entry_map_raw, alert_candidates_raw, contract_generated_at, contract_source = _load_contract_entry_context(logs_dir)
```

Then update the `write_dashboard` call to pass `alert_candidates`:
```python
write_dashboard(
    payload, run, previous_run, history_runs, output_path=output_path,
    market_map_path=market_map_path,
    macro_snapshot_path=macro_snapshot_path,
    contract_entry_map=contract_entry_map,
    alert_candidates=alert_candidates_raw or None,
    contract_generated_at=contract_generated_at,
    payload_source=payload_path,
    run_source=run_path,
    market_map_source=market_map_path,
    contract_source=contract_source,
    fixture_mode=_fixture_mode,
)
```

- [ ] **Step 4: Add `alert_candidates` parameter to `render_dashboard_html` signature**

Find the `render_dashboard_html` signature (around line 829). After `contract_entry_map`:
```python
    contract_entry_map: dict | None = None,
```
add:
```python
    alert_candidates: list[dict] | None = None,
```

- [ ] **Step 5: Add `alert_candidates` parameter to `write_dashboard` signature**

Same change — add after `contract_entry_map`:
```python
    alert_candidates: list[dict] | None = None,
```

And pass it through to `render_dashboard_html`:
```python
        alert_candidates=alert_candidates,
```

- [ ] **Step 6: Run tests — confirm plumbing doesn't break existing tests**

```bash
python3 -m pytest tests/test_dashboard_renderer.py tests/test_dash_system_state.py tests/test_dash_candidates.py -q
```

Expected: existing tests still pass; new tests still fail (no rendering logic yet)

---

## Task 5: Implement — fix System State reason

**Files:**
- Modify: `cuttingboard/delivery/dashboard_renderer.py`

- [ ] **Step 1: Update the System State reason logic**

Find lines around 1051-1054:
```python
    elif not bool(system_halted) and stay_flat_reason is None and run.get("permission") is None:
        _perm_reason = first_error or "No candidate passed qualification."
        w(f'  <div class="field"><div class="label">Reason</div>'
          f'<div class="value">{_esc(_perm_reason)}</div></div>')
```

Replace with:
```python
    elif not bool(system_halted) and stay_flat_reason is None and run.get("permission") is None:
        if first_error:
            _perm_reason = first_error
        elif alert_candidates:
            _perm_reason = "candidates gated"
        else:
            _perm_reason = "no qualified candidates"
        w(f'  <div class="field"><div class="label">Reason</div>'
          f'<div class="value">{_esc(_perm_reason)}</div></div>')
```

- [ ] **Step 2: Run System State tests**

```bash
python3 -m pytest tests/test_dash_system_state.py tests/test_dashboard_renderer.py::test_permission_none_shows_reason_line -v
```

Expected: `test_system_state_reason_no_candidates`, `test_system_state_reason_candidates_gated`, and `test_permission_none_shows_reason_line` all PASS

---

## Task 6: Implement — add Alert Watchlist section

**Files:**
- Modify: `cuttingboard/delivery/dashboard_renderer.py`

- [ ] **Step 1: Add Alert Watchlist section after the system-state block**

Find the comment `# --- sunday-macro-context` (around line 1061). Insert the new section directly before it:

```python
    # --- alert-watchlist ---
    if alert_candidates:
        w('<div class="block" id="alert-watchlist">')
        w('  <h2>Alert Watchlist</h2>')
        w('  <div class="label">Candidates gated by execution policy — same as Telegram WATCHLIST</div>')
        for cand in alert_candidates:
            sym = _esc(str(cand.get("symbol") or "").upper())
            direction = _esc(str(cand.get("direction") or "").upper())
            block_reason = _esc(str(cand.get("block_reason") or "").upper())
            w(f'  <div class="candidate-state">{sym} {direction}'
              + (f' — {block_reason}' if block_reason else '')
              + '</div>')
        w("</div>")
```

- [ ] **Step 2: Run Alert Watchlist tests**

```bash
python3 -m pytest tests/test_dash_candidates.py::test_alert_watchlist_absent_when_no_candidates tests/test_dash_candidates.py::test_alert_watchlist_absent_when_empty_candidates tests/test_dash_candidates.py::test_alert_watchlist_present_when_candidates tests/test_dash_candidates.py::test_alert_watchlist_shows_symbol_and_direction tests/test_dash_candidates.py::test_alert_watchlist_positioned_before_candidate_board -v
```

Expected: all 5 PASS

---

## Task 7: Implement — rename Candidate Board

**Files:**
- Modify: `cuttingboard/delivery/dashboard_renderer.py`

- [ ] **Step 1: Update the Candidate Board heading**

Find (around line 1148):
```python
    if fixture_mode:
        w('  <h2>Candidate Board &#8212; <span style="color:#ff9800">DEMO MODE &#8212; FIXTURE DATA</span></h2>')
    else:
        w("  <h2>Candidate Board</h2>")
```

Replace with:
```python
    if fixture_mode:
        w('  <h2>Market Map / Developing Setups &#8212; <span style="color:#ff9800">DEMO MODE &#8212; FIXTURE DATA</span></h2>')
    else:
        w("  <h2>Market Map / Developing Setups</h2>")
```

- [ ] **Step 2: Run rename test**

```bash
python3 -m pytest tests/test_dash_candidates.py::test_candidate_board_renamed_to_market_map -v
```

Expected: PASS

---

## Task 8: Full test suite and commit

**Files:** None changed — just verification

- [ ] **Step 1: Run full test suite**

```bash
python3 -m pytest tests -q
```

Expected: 2073+ passing, 2 pre-existing failures (test_dash_run_history::test_run_health_present, test_dash_system_state::test_system_state_permission_shows_dash_when_none), 0 new failures

- [ ] **Step 2: Grep validation**

```bash
grep -R "Candidate Board" cuttingboard tests ui 2>/dev/null | grep -v "DEMO MODE\|__pycache__\|\.pyc"
```

Expected: no matches (old label gone, except fixture demo line)

```bash
grep -R "No candidate passed qualification" cuttingboard tests ui 2>/dev/null | grep -v "__pycache__\|\.pyc"
```

Expected: no matches

```bash
grep -R "Alert Watchlist\|alert-watchlist\|Market Map / Developing Setups" cuttingboard tests 2>/dev/null | grep -v "__pycache__\|\.pyc"
```

Expected: matches in dashboard_renderer.py and test_dash_candidates.py

- [ ] **Step 3: Commit**

```bash
git add cuttingboard/delivery/dashboard_renderer.py tests/test_dashboard_renderer.py tests/test_dash_system_state.py tests/test_dash_candidates.py docs/prd_history/PRD-102.md docs/PRD_REGISTRY.md
git commit -m "PRD-102: align alert and dashboard candidate semantics"
```

---

## Task 9: Close PRD-102

**Files:**
- Modify: `docs/PRD_REGISTRY.md`
- Modify: `docs/PROJECT_STATE.md`

- [ ] **Step 1: Get commit hash**

```bash
git log --oneline -1
```

- [ ] **Step 2: Update PRD_REGISTRY.md status to COMPLETE with commit hash**

Change the PRD-102 row from:
```
| PRD-102 | — | Align Alert and Dashboard Candidate Semantics | IN PROGRESS | [PRD-102](prd_history/PRD-102.md) |
```
to (replace HASH with actual short hash):
```
| PRD-102 | HASH | Align Alert and Dashboard Candidate Semantics | COMPLETE | [PRD-102](prd_history/PRD-102.md) |
```

- [ ] **Step 3: Update PROJECT_STATE.md**

Update:
- `Last updated:` → `2026-05-08`
- `Last completed PRD:` → `PRD-102 - Align Alert and Dashboard Candidate Semantics (commit HASH)`
- `Active PRD:` → `none`
- `Test Baseline:` → update count from pytest output

- [ ] **Step 4: Commit closure**

```bash
git add docs/PRD_REGISTRY.md docs/PROJECT_STATE.md
git commit -m "Register PRD-102 complete in registry and state"
```

---

## Self-Review

### Spec coverage check

| Requirement | Task |
|-------------|------|
| Telegram WATCHLIST symbols in dashboard Alert Watchlist | Task 6 |
| Market-map symbols labeled Market Map / Developing Setups | Task 7 |
| System State shows NO TRADE when no executable trade | Not changed — System State already shows NO TRADE outcome from `run.json` |
| If candidates gated after 3:30 PM, reason says "candidates gated" | Task 5 — reason uses `alert_candidates` non-empty → "candidates gated" |
| NO TRADE with no candidates → "no qualified candidates" reason | Task 5 |
| Tests: alert watchlist candidates render in alert section | Task 3 + Task 6 |
| Tests: market_map candidates render in market map section | Task 3 (rename test, existing market_map tests already cover card rendering) |
| Tests: NO TRADE + gated candidates → gated-candidates reason | Task 2 + Task 5 |
| Tests: NO TRADE + no candidates → no-candidates reason | Task 2 + Task 5 |
| Existing tests pass | Task 4 Step 6 + Task 8 |

### Placeholder scan

No TBD, TODO, or incomplete steps found.

### Type consistency

- `alert_candidates: list[dict] | None` — consistent across `render_dashboard_html`, `write_dashboard`, `_load_contract_entry_context`
- `_load_contract_entry_context` now returns 4-tuple — updated in `main()` unpacking
- `ALLOW_TRADE` imported from `cuttingboard.trade_decision` — same source used in `execution_policy.py` and `contract.py`
