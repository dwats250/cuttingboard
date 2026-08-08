# CuttingBoard — Planning Session Wins (2026-08-08)

STATUS: Temporary synthesis input for the reconciliation/handoff session. This is not canonical product or governance authority. It records process lessons worth carrying forward; any rule intended to become binding must graduate through the normal authority path.

## What proved unusually effective

1. **Use context-rich sessions for planning, not implementation.** Once a session has accumulated high-quality recon, design history, owner rulings, and cross-lane context, its highest-value use is to shape the next few slices coherently rather than immediately spend that context on one implementation.

2. **Plan multiple adjacent lanes before authorizing any of them.** The Morning Brief/Cloudflare, Context Registry/NEWS-0, and GEX lanes were planned together while remaining independent. This surfaced sequencing, parallelism, and collision risks before code existed.

3. **Normalize packets before execution.** A dedicated normalization pass caught silent proposal→decision drift, inconsistent readiness language, naming collisions in decision IDs, and estimation inconsistencies. Planning artifacts should use a common contract: purpose, current truth, unresolved loop, smallest next slice, owner decisions, dependencies, parallel-safe work, scope walls, surface estimate, falsification plan, governance path, stop conditions, readiness, next commission.

4. **Separate priority from readiness.** A lane can be procedurally more ready without deserving the implementation seat. Registry reached MATERIAL-packet-ready before Morning Brief, yet Cloudflare remains first because product leverage is higher and nothing blocks it.

5. **Use secondary review to challenge framing, not to seek agreement.** Fable's original recommendation to cut the scheduler/freshness arc was useful precisely because the owner disagreed. Reframing the arc from a staleness framework to the operating clock for a Morning Brief revealed substantially higher product value.

6. **Make cross-lane collisions explicit before implementation.** The holistic pass checked workflows, CI, time/freshness semantics, provenance, unavailable-state conventions, payload/renderer ownership, trigger infrastructure, registry dependencies, and decision-contract contamination. Most correct answers were "remain independent" or "defer abstraction".

7. **Do not create shared infrastructure from conceptual similarity alone.** Morning Brief timing, GEX provider freshness, and future news freshness share conventions, not yet a common implementation. Domain-specific carriers and triggers remain separate until real duplication justifies a primitive.

8. **Exploratory reasoning and implementation execution are different jobs.** PRD-289 reinforced the pattern: spend strong reasoning on architecture, semantics, invariants, tests, and stop conditions; once those degrees of freedom are compiled out, implementation-class Claude/Ultracode can move very quickly with little steering.

9. **Use lightweight recon aggressively when the question is mechanical.** Narrow readers/direct greps were sufficient for most planning verification. Stronger reasoning should be reserved for product boundaries, architecture, governance, provider viability, and owner-choice shaping.

10. **Recon fan-out needs a cheap environment probe first.** A failed broad agent fan-out previously burned substantial tokens on a harness failure. Probe the environment/tool path cheaply before parallel dispatch; prefer narrow, low-cost readers for repository fact gathering.

11. **Estimate validation surfaces honestly.** PRD-288 and PRD-289 both exceeded initial LOC ceilings because closed vocabularies, validation, fail-loud guards, and proof obligations were treated as incidental plumbing. Future planning should count validators, typed-unavailable handling, time/DST boundaries, auth/provenance logic, and mutation scaffolding explicitly and use ranges until the design is mature.

12. **A bounded disagreement can improve the roadmap.** Cloudflare-first survived an explicit challenge test. Owner priority should not be rubber-stamped, but it also should not be displaced by process readiness alone; only concrete correctness, dependency, timing, or rework evidence should force resequencing.

## Three-lane execution discipline to preserve

- Cloudflare Clock + Morning Brief remains the first implementation arc unless a compelling new blocker appears.
- Context Registry / NEWS-0 can advance in planning/governance in parallel but must not become a dependency of Morning Brief or GEX without a real need.
- GEX remains a separate viability/evidence lane; no producer work until a terminal provider verdict permits it.
- `payload.py` / `dashboard_renderer.py` should be treated as single-owner surfaces during overlapping implementation arcs.
- Additive integration first; no schema/version or decision-contract expansion merely to accommodate a new observational surface.
- Compute explicitly, display selectively.
- Deterministic observation only; no predictive promotion.
- Explicit unavailable states and exact provenance remain per-domain until duplication is concrete enough to justify abstraction.

## Planning-session stopping rule

When the lane packets are normalized, cross-lane review is clean, owner decisions are explicit, readiness is truthful, and the next commissions are known, stop planning. Do not convert a productive planning session into premature implementation. Preserve the handoff while the reasoning remains coherent, then execute each lane through its own authority chain.
