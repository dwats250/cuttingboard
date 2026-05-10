# Sidecar Doctrine — cuttingboard

This document defines the architectural rules for sidecar modules and
artifacts in cuttingboard. A sidecar is any module, job, or artifact that
runs alongside the main decision pipeline without participating in the
TRADE / NO_TRADE / HALT outcome. The doctrine below is binding — sidecars
are the primary mechanism for adding observability, research surfaces, and
visibility layers without weakening the deterministic decision engine.

---

## Observe-only philosophy

Sidecars exist to **observe**, not to decide. They read existing artifacts
and emit new artifacts that describe, summarize, or contextualize what the
pipeline already produced. A sidecar that influences whether a trade is
taken, blocked, or sized differently is not a sidecar — it is a pipeline
component and must be implemented under the pipeline's full PRD discipline.

A sidecar may:

- Read pipeline artifacts (contract, payload, market_map, audit, evaluation).
- Read raw data sources (OHLCV, calendars, news) for descriptive context.
- Write its own artifact at a non-overlapping path.
- Render supplementary output for human review.

A sidecar may not:

- Mutate any pipeline-owned artifact.
- Inject derived fields into the contract or payload.
- Change a candidate's qualification, decision, or sizing.
- Trigger or suppress notifications.

---

## Producer / consumer separation

Every sidecar has exactly one **producer** (the writer) and a defined set
of **consumers** (the readers). Producers do not consume their own outputs
on the same run, and consumers do not write back to producer paths.

- The producer owns the artifact path, schema, and write contract.
- Consumers must treat the artifact as read-only and version-tolerant.
- No "shared scratchpad" artifacts exist; each path has one writer.

Documentation of producer/consumer relationships for every artifact lives
in `docs/artifact_flow_map.md`. Adding a sidecar means adding a row there
in the same PRD that introduces the sidecar.

---

## No mutation paths into TradeDecision

The `TradeDecision` object and the contract fields that surround it
(`hard_gate_result`, `soft_gate_results`, `decision`, `outcome`,
`trade_candidates`, `system_halted`) are sealed against sidecar influence.

- No sidecar reads back into `qualification.py`, `trade_decision.py`,
  `trade_policy.py`, or `execution_policy.py`.
- No sidecar modifies `contract.build_pipeline_output_contract` outputs.
- No sidecar adds fields that downstream qualification logic could read.

If a future requirement needs a sidecar's data to reach the decision layer,
that is a pipeline change, not a sidecar change, and requires a PRD that
explicitly promotes the field into the contract under decision-affecting
discipline.

---

## Contract isolation

The pipeline output contract is the deterministic boundary between
decision logic and downstream systems. Sidecars, dashboards, notifiers,
and evaluators all sit downstream of the contract.

- The contract schema is owned by `contract.py` and frozen per PRD.
- Sidecar artifacts have their own schemas and do not extend the contract.
- Renderers and notifiers consume the contract as-is; they do not merge
  sidecar data into it before displaying or sending.

When a sidecar produces fields that a renderer wants to display, the
renderer reads the sidecar artifact directly. The contract is not the
transport layer for sidecar data.

---

## Dashboard as consumer (not computation engine)

The dashboard renderer (`delivery/dashboard_renderer.py`) is a **consumer**
of pipeline and sidecar artifacts. It does not compute new analytics, does
not derive new qualification logic, and does not invent fields absent from
its inputs.

- The renderer reads payload, run, contract, market_map, and macro snapshot.
- The renderer reads sidecar artifacts (e.g. trend structure snapshot)
  directly from their canonical paths.
- The renderer must degrade gracefully when an input is missing — never
  by fabricating values.

A change that requires the dashboard to compute a new metric is a pipeline
or sidecar change, not a renderer change.

---

## No-hidden-coupling doctrine

Coupling between modules must be **declared**: imports, documented reads,
artifact paths in `docs/artifact_flow_map.md`. Hidden coupling is forbidden.

Examples of hidden coupling that violate this doctrine:

- A renderer that silently re-runs qualification math to fill a gap.
- A sidecar that reads a pipeline-internal in-memory cache.
- A notifier that re-derives candidate ranking from raw quotes.
- A dashboard component that mutates a sidecar artifact and writes it back.

Every cross-module data flow in cuttingboard must be traceable from the
artifact map and the import graph. If a behavior cannot be explained by
those two surfaces alone, it is a doctrine violation that must be unwound
or promoted into an explicit, PRD-defined interface.
