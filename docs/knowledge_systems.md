# Knowledge Systems — cuttingboard

This document defines the role boundaries between the two persistent
knowledge systems that surround the cuttingboard repository: GitNexus and
Obsidian. Neither system is part of the runtime pipeline. Both exist to
support strategic and architectural cognition without becoming a backdoor
into decision logic.

---

## Epistemic hierarchy

Obsidian is the human strategic cognition layer.
GitNexus is the machine architectural memory layer.
Neither system is authoritative over runtime behavior;
the repository, canonical docs, and PRD registry remain
the source of truth.

---

## GitNexus — machine architectural memory

GitNexus indexes the cuttingboard repository as a queryable knowledge
graph. Its role is mechanical, structural, and code-grounded.

- **Architectural retrieval:** locating modules, symbols, and execution
  flows without grepping the tree by hand.
- **PRD lineage tracing:** following how a requirement propagated from a
  PRD into specific files, functions, and tests.
- **Semantic codebase memory:** answering "where is X used?" and
  "what does X depend on?" against the current indexed state of the repo.
- **Implementation provenance:** mapping observed behavior back to the
  commits, modules, and PRDs that introduced it.
- **Dependency / context recall:** producing impact analyses, caller and
  callee maps, and process flow listings for safe edits.

GitNexus is not authoritative. When the index is stale, the repository is
correct and GitNexus is wrong; reindex before trusting query results that
disagree with the source.

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

## Boundaries between the two systems

GitNexus and Obsidian are **complementary and non-overlapping**:

- GitNexus answers questions about what the code *is*; Obsidian answers
  questions about what the system *should become*.
- GitNexus is queried by agents performing implementation work; Obsidian
  is authored by the human performing strategic work.
- Neither system writes into the other. Promotion from Obsidian to the
  repository happens only through PRDs.
- Neither system is a substitute for reading the repository or the PRD
  registry when correctness is at stake.

When the two systems disagree, the repository wins. When the repository
and a PRD disagree, the PRD registry and the merged code together define
the truth — and the discrepancy is itself a signal to open a corrective
PRD.
