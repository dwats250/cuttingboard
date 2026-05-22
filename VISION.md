# VISION.md

## What Cuttingboard is

Cuttingboard is a Python-based market observation and decision-support system. It ingests market data, computes contextual interpretations across a 10-layer pipeline, and renders artifacts that help answer four questions: *what environment are we in, what matters today, is this actually tradable, and what conditions invalidate this.*

Its core value is **cognitive compression** — reducing noise, organizing context, and forcing explicit reasoning under uncertainty. It is not a prediction engine. It does not generate alpha. It supports a discretionary trader operating in a domain where the cost of being wrong is high and the cost of being unprepared is higher.

## What Cuttingboard is not, and will not become

- Not an automated execution engine
- Not a backtesting framework
- Not a machine learning system
- Not a multi-agent orchestration platform
- Not a generalized financial operating system
- Not a high-frequency signal factory
- Not a regulated infrastructure project requiring aircraft-grade process

The system is built by one person, for one person's trading, on a part-time schedule. Scope decisions reflect that reality.

## Current state, honestly

**Built and in use:** the 10-layer pipeline (Ingestion through Audit), 297 tests, CLI entrypoint, GitHub Actions CI committing daily markdown reports, the artifact lineage and coherence enforcement work (PRDs 115-120), the sidecar architectural pattern, Gap-Down Permission Gating (built prior to VISION.md being written; retroactively documented as PRD-151 during the 2026-05-22 realignment).

**In flight:** none. Intraday state classification engine PRD (PRD-150) was killed 2026-05-22 per vision review.

**Dead code to remove:** Polygon integration (never used in production), ntfy alerts (topic `cuttingboard86`, no longer relied on), any references in config, env, requirements, and docs.

**Stalled and to be closed:** PRD 142 is blocked on data that isn't being collected. Either the data collection gap gets explicitly scoped or the PRD gets killed. No middle state.

**Suspected debt, unverified:** duplicated logic across sidecars, stale PRD references, renderer assumptions that no longer match actual use, "temporary" patches that became permanent. To be surfaced during the inventory audit.

## Phases ahead

**Phase 1 — Inventory, cleanup, implement, align.**

1. **Inventory audit.** Codex maps the full repo: modules, dependencies, dead code, orphans, drift from PRDs. Known cleanup targets (Polygon, ntfy, PRD 142) are flagged for deletion in the inventory rather than deeply analyzed.
2. **Consolidated cleanup.** All dead code removed in one informed pass — known targets plus anything inventory surfaced. Single coherent cleanup commit set.
3. **Gap-Down Permission Gating implementation.** Already complete — the 2026-05-22 realignment discovered the feature was implemented in `cuttingboard/intraday_state_engine.py` + `cuttingboard/runtime.py` (with dedicated integration tests) prior to VISION.md being written. Retrospectively documented as PRD-151.
4. **Architectural alignment audit.** Codex (directed by Claude) evaluates whether the resulting system matches this document. Sidecars are still read-only? No prediction logic crept in? Every module earns its keep? Dustin reviews the report and makes explicit decisions on every flagged item.

**Exit criteria:** repo contains only code that's used, every PRD is either active, completed, or formally killed, and the architecture demonstrably reflects what this document declares the system to be. Until alignment audit passes, no Phase 2 work begins.

**Phase 2 — Trade evaluation sidecar.** PRD, then build. Read-only consumer of the existing L10 audit output, joined to imported Moomoo trade statements. Produces post-hoc evaluation of trades against the market state Cuttingboard observed at the time. Descriptive, not predictive. Closes the loop between the system's market observations and Dustin's actual trading behavior — the loop whose absence is the project's central weakness. Exit criteria: every trade Dustin takes can be evaluated against the market state at entry, exit, and key intermediate points.

**Phase 3 — Presentation pass.** README, repo hygiene, documentation that reflects the actual system rather than aspirational framing. The goal is a repo that a thoughtful outsider can read and understand in 15 minutes without being misled about what it does. No marketing language. Constraints stated plainly.

The ordering reflects a judgment: cleanup and audit first because debt compounds and silent drift is the failure mode that produced sprawl; sidecar second because it's the keystone for closing the explanation-to-behavior loop; presentation last because it should describe what exists rather than what's planned.

## Operating principles

- **PRD before build for anything non-trivial.** "Non-trivial" means: new module, new external dependency, new architectural pattern, or change that touches more than one layer of the pipeline. Bug fixes, small refactors, and additions within established patterns don't need PRDs. This is graduated formality, not abolition.
- **Read-only sidecars by default.** New observational features extend through sidecars rather than mutating core contracts.
- **Description, not prediction.** Features that explain or contextualize are welcome. Features that forecast are not.
- **Cuts before additions.** Before adding a feature, the system should justify the features it already has. Anything not earning its keep gets removed.
- **The system serves the trader, not the other way around.** If a feature exists but Dustin doesn't actually use it to make decisions, it shouldn't exist.
- **The system must match its documentation.** When code and documented intent diverge, one of them is wrong and the divergence gets resolved explicitly — by changing the code, changing the documentation, or formally acknowledging the gap. Silent drift is the failure mode that allowed sprawl, and the audit gate exists to catch it before it compounds.

## How we work

Dustin makes final decisions. AI handles logic and code. Implementations get reviewed before merge.

Claude (project lead) drafts PRDs, reviews code against architectural principles, flags drift from stated vision, asks the procedural questions the market won't ask. Authorized to push back on scope additions that violate non-goals; Dustin can override.

Codex (implementation) executes against specs. Doesn't make architectural calls. Output gets reviewed against the PRD.

Decisions that meaningfully change direction get recorded with date and rationale — short notes, not ceremony. Next session, we read what we decided last time so neither of us drifts silently.

## The trap to watch for

The strongest pattern-recognition Cuttingboard has built is environmental awareness. The weakest is the loop from awareness to behavioral change. The project's main failure mode going forward is producing better and better explanations of markets without producing fewer behavioral mistakes. Every proposed feature should be evaluated against: *does this change what I'll actually do, or does it just help me feel more informed about what I might do?* The latter is intellectual comfort dressed as progress.
