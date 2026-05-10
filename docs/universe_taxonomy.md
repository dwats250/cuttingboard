# Universe Taxonomy — cuttingboard

This document is the canonical reference for the symbol universes used by the
cuttingboard pipeline. Every universe has a single source of truth in
`cuttingboard/config.py`; downstream modules must consume those constants
directly and must not redefine, alias, or shadow them.

The pipeline is deterministic and macro-aware: changes to any universe ripple
into ingestion, validation, regime, qualification, sidecars, and dashboard
display. Mutation boundaries below are governance rules, not advisory notes.

---

## ALL_SYMBOLS

- **Purpose:** Master tradable + macro fetch list; the union the pipeline
  ingests every run.
- **Ownership:** `cuttingboard/config.py:ALL_SYMBOLS`
  (= `MACRO_DRIVERS + INDICES + COMMODITIES + HIGH_BETA`).
- **Consumers:** `runtime._tradable_symbols`, ingestion layer, validation
  layer, derived metrics, regime inputs, qualification fan-out.
- **Mutation boundaries:** Modify only via a PRD that explicitly scopes
  universe expansion or contraction. Adding a symbol implies updating
  source priority, validation bounds, and any sidecar that enumerates the
  list. No silent additions, no temporary entries, no conditional members.

---

## tradable universe

- **Purpose:** Symbols eligible for trade qualification; macro drivers are
  excluded because they are decision context, not trade candidates.
- **Ownership:** Derived only — no constant. Computed as
  `ALL_SYMBOLS \ NON_TRADABLE_SYMBOLS` by
  `cuttingboard/runtime.py:_tradable_symbols`.
- **Consumers:** Qualification fan-out, options layer, contract assembly.
- **Mutation boundaries:** Never define a `TRADABLE_SYMBOLS` constant. The
  derivation must remain a pure set difference computed at runtime so that
  `ALL_SYMBOLS` and `NON_TRADABLE_SYMBOLS` are the only knobs.

---

## MACRO_DRIVERS

- **Purpose:** Macro context inputs to the regime engine and macro display.
- **Ownership:** `cuttingboard/config.py:MACRO_DRIVERS`
  (`^VIX`, `DX-Y.NYB`, `^TNX`, `BTC-USD`).
- **Consumers:** `regime.py` (8-input vote model), macro snapshot writer,
  dashboard renderer macro panel, validation (HALT_SYMBOLS overlap).
- **Mutation boundaries:** Tightly bound by the regime model. Adding or
  removing a driver changes vote counts, thresholds, and confidence math;
  requires a regime-scoped PRD with explicit threshold rewiring.

---

## HALT_SYMBOLS

- **Purpose:** Pipeline halt set — failure of any HALT_SYMBOL in validation
  stops the entire run.
- **Ownership:** `cuttingboard/config.py:HALT_SYMBOLS`
  (`^VIX`, `DX-Y.NYB`, `^TNX`, `SPY`, `QQQ`).
- **Consumers:** `validation.py` hard gate, runtime kill-switch logic,
  audit records.
- **Mutation boundaries:** This set defines the system's data integrity
  contract. Any change is a runtime-critical PRD; it cannot be edited as a
  side effect of universe changes elsewhere.

---

## TREND_STRUCTURE_SYMBOLS

- **Purpose:** Curated 6-symbol universe for the trend structure sidecar
  snapshot (`logs/trend_structure_snapshot.json`).
- **Ownership:** `cuttingboard/config.py:TREND_STRUCTURE_SYMBOLS`
  (`SPY`, `QQQ`, `GDX`, `GLD`, `SLV`, `XLE`).
- **Consumers:** `cuttingboard/trend_structure.py:build_trend_structure_snapshot`
  invoked by `runtime._write_trend_structure_snapshot`.
- **Mutation boundaries:** Must remain a strict subset of `ALL_SYMBOLS` and
  disjoint from `NON_TRADABLE_SYMBOLS`. The snapshot is observe-only — it
  must not feed back into qualification, regime, or contract assembly.
  Universe edits require a sidecar-scoped PRD.

---

## NON_TRADABLE_SYMBOLS

- **Purpose:** Symbols excluded from trade qualification (macro context only).
- **Ownership:** `cuttingboard/config.py:NON_TRADABLE_SYMBOLS`
  (`frozenset(MACRO_DRIVERS)`).
- **Consumers:** `runtime._tradable_symbols`, any module that must distinguish
  context inputs from trade candidates.
- **Mutation boundaries:** Definitionally tied to `MACRO_DRIVERS`. Do not
  diverge — if the two ever need to differ, that divergence requires a PRD
  that explicitly redefines what "non-tradable" means.

---

## Canonical separation rules

1. **One source of truth per universe.** No module redefines a universe
   list locally; consumers import from `config.py`.
2. **Derived universes stay derived.** The tradable universe is a runtime
   computation, never a constant.
3. **Sidecar universes are subsets.** Any new sidecar universe must be a
   strict subset of `ALL_SYMBOLS` and cannot introduce new fetch targets.
4. **Universe changes are PRD-gated.** Adding, removing, or reordering
   members of any universe above requires an explicit PRD documenting the
   blast radius across ingestion, regime, qualification, and sidecars.
