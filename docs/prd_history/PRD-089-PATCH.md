# PRD-089-PATCH — Integrate Run Snapshot into System State

**Status:** COMPLETE
**Commit:** 8980215
**Patches:** PRD-089 (Dashboard Artifact Coherence Guard)
**ROOT CAUSE:** missing requirement — PRD-089 added coherence guards but did not specify where the run timestamp and freshness label should render, leaving Run Snapshot outside the System State block.

---

## GOAL

Move the Run Snapshot (freshness label + Pacific timestamp) into the System State block.
Add conditional Permission rendering: `HALTED` when `system_halted=True`, raw halt reason
as a separate `Reason` field rather than as the Permission value.

---

## SCOPE

Renderer and tests only.

---

## FILES

```
cuttingboard/delivery/dashboard_renderer.py
tests/test_dashboard_renderer.py
```

---

## REQUIREMENTS

- R1: System State block renders `RUN SNAPSHOT - STALE` or `RUN SNAPSHOT - CURRENT` label.
- R2: Pacific timestamp renders inside System State when available.
- R3: When `system_halted=True`, Permission field displays `HALTED`.
- R4: When `system_halted=True` and halt reason is present, reason appears as a separate `Reason` field below the Permission row.
- R5: Raw halt reason does not appear as the Permission value.

---

## FAIL CONDITIONS

- `"RUN SNAPSHOT"` absent from system-state block → FAIL
- Permission shows raw reason string instead of `HALTED` when halted → FAIL
- Halt reason absent from `Reason` field when halted with reason → FAIL
- Halt reason leaks into Permission value → FAIL
