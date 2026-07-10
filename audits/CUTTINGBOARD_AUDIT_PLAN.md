# CuttingBoard — Fable Audit Plan

*Brainstorm-phase audit plan. Output is a findings ledger (ranked observations,
written artifacts) — NOT a PRD backlog. Descriptive, not predictive. Human makes
the calls; the audit only surfaces and ranks.*

**Spine:** evidence → questions → state → attention → terminal decision →
explanation → governance.

---

## Phase 1 — Architecture foundations

1. **Mantra sanity check (light).** Quick, up-front: is the spine — "Symbols are
   evidence → Questions create state → State governs attention → Attention
   precedes execution" — actually the right frame, or is something else driving
   the system? A gut-check before auditing *along* the spine bakes it in.

2. **Dependency audit.** Map state flow, gate order, and mutation sequence; spot
   cycles and feedback loops. The bedrock — nothing downstream can be trusted
   until this is known.

3. **Run-trace / replayability audit.** For any TRADE / NO TRADE / HALT, can the
   run be reconstructed end-to-end: inputs → evidence accepted/rejected/stale →
   questions → resolved state → gates passed/failed → blockers → terminal
   decision → displayed reasoning. Load-bearing for catching silent degradation.

## Phase 2 — State and integrity

4. **State formation & integrity audit (merged).** How state is built and
   mutated across the pipeline in a single pass with two lenses: formation (what
   creates state, from what evidence) and integrity (hidden mutations, staleness,
   duplicate/conflicting truth, silent fallbacks, fields read before resolution
   or written after decision authority closes).

## Phase 3 — Governance

5. **Governance invariant enforcement.** Where do the six semantic-failure
   bindings have loopholes or silent violations in actual code.

6. **Governance alignment pass.** Lanes, gates, review cadence, and merge
   discipline vs. Claude Code agent skills and the binding rules file. Does the
   process actually enforce the architecture — could Claude Code merge a
   violation without being stopped?

## Phase 4 — Logic, scope, and red-team

7. **Complexity audit (cross-cutting).** Parasitic features, scope creep, cuts
   vs. additions. Per component: why does it exist, what breaks without it, who
   consumes it, is it decision-critical / explanatory / observational / dead
   weight, is there a simpler version.

8. **Four-question anchor audit.** Every gate, sidecar, output, and state field
   must serve one of: (1) what environment are we in, (2) what matters today,
   (3) is it tradable, (4) what invalidates it. Flag anything serving none as
   parasitic unless there's a clear governance/traceability reason.

9. **Sidecar doctrine enforcement.** Sidecars must be read-only with a named
   downstream consumer. Hunt orphaned / dead-code sidecars and any sidecar
   quietly influencing TRADE / NO TRADE / HALT.

10. **Mantra adversarial red-team.** Now attack the spine: does the pipeline
    actually follow the order, is attention ever created before state, do
    questions create state or merely decorate outputs — and "if this doctrine is
    wrong or incomplete, where does the system fail first?"

---

## Cross-cutting lenses (apply across all phases, not as a step)

- **Complexity:** essential vs. accidental, at every layer.
- **Semantic-failure invariants:** fail-loud, assert resolved state, read from
  authoritative source, red test per guard, CI parity, pinned identities — used
  as *diagnostic criteria* while auditing state (Phases 1–2), not siloed in
  governance.

## Fable time-box triage (~5-hour window)

If Fable runs out of context, the two that MUST land are the **dependency audit
(#2)** and the **run-trace audit (#3)** — heavy reasoning, highest-value finds.
The four-question anchor (#8), complexity sweep (#7), and mantra red-team (#10)
are lighter and can go to GPT-5.6 or a later window.

## Output contract

Ranked findings, persisted as written artifacts. Each finding: what, where,
severity, and which spine stage it breaks. This feeds the GPT-5.6 adversarial
review pass. No building this window.
