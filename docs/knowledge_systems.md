# Knowledge Systems — cuttingboard

This document defines the role of the persistent knowledge system that
surrounds the cuttingboard repository: Obsidian. It is not part of the
runtime pipeline; it exists to support strategic and architectural
cognition without becoming a backdoor into decision logic.

---

## Epistemic hierarchy

Obsidian is the human strategic cognition layer.
It is not authoritative over runtime behavior;
the repository, canonical docs, and PRD registry remain
the source of truth.

---

## GitNexus — RETIRED (PRD-243, 2026-07-05)

A "machine architectural memory" layer (repo knowledge-graph indexer)
formerly described here. The lifecycle audit found the entire surface dead:
its 12 skill files were generated once (2026-06-26 / 2026-04-28) and never
regenerated, their symbol indexes had drifted measurably stale, the CLI/MCP
was not installed in any operating environment, and four of its skills
trigger-matched ordinary requests toward the absent tool. Deleted: the
`generated/*` and `gitnexus/*` skill packs, `scripts/gitnexus-analyze.sh`,
and the `pre_commit_sanity.sh` detect-changes step. The architectural-recon
role it claimed is served by `docs/SCHEMA_MAP.md`, `docs/CALL_SITE_MAP.md`,
`grep`-at-use, and `Explore` subagents (CLAUDE.md workflow patterns).
History: DECISIONS 2026-05-22 (AGENTS.md auto-generation), PRD-243.

---

## Obsidian — human strategic cognition

Obsidian is the human-side workspace for thinking, research, and planning
that sits *outside* the repository. Its role is interpretive and strategic.

- **Macro research:** notes, charts, and references that inform regime
  expectations and instrument selection.
- **Strategic planning:** roadmap framing, prioritization, and long-arc
  decisions about where the engine is headed.
- **PRD ideation:** drafting and refining PRD candidates before they are
  formalized into `docs/prd_history/`.
- **Discretionary trading journal:** human trade reviews, lessons,
  mistakes taxonomy, and process reflection.
- **Architecture thinking:** sketches, diagrams, and reasoning about
  structural choices that have not yet hardened into the codebase.
- **Roadmap cognition:** synthesizing observations into directional
  decisions before they become PRDs.

Obsidian is not authoritative. A note in Obsidian does not change runtime
behavior; only a merged PRD plus committed code does that.

---

## Boundary

- Obsidian answers questions about what the system *should become*; the
  repository answers what the code *is* (via SCHEMA_MAP / CALL_SITE_MAP /
  grep, not a parallel index).
- Obsidian never writes into the repository. Promotion happens only
  through PRDs.
- Obsidian is not a substitute for reading the repository or the PRD
  registry when correctness is at stake.

When Obsidian and the repository disagree, the repository wins. When the
repository and a PRD disagree, the PRD registry and the merged code
together define the truth — and the discrepancy is itself a signal to open
a corrective PRD.
