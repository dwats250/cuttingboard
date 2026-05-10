# CLAUDE.md — cuttingboard

## purpose

Build and refine a constraint-driven options trading decision engine.

- Improve trade decisions
- Enforce clarity and discipline
- Prevent system drift

**System type:** Decision engine with a fixed pipeline. Not a research library. Not a feature-rich platform.

**Output contract:** Every run produces exactly one of: `TRADES | NO TRADE | HALT`

---

## system state

See `docs/PROJECT_STATE.md` for current test baseline, active PRD, and pipeline status. Pipeline architecture is indexed by GitNexus — use `gitnexus_query` or `gitnexus_context` to navigate modules rather than reading this file.

---

## session mode

Operate REPO-FIRST. Memory hierarchy (strict):

1. Active PRD (`docs/prd_history/PRD-NNN.md`)
2. `docs/PROJECT_STATE.md`
3. This file (CLAUDE.md)
4. Repo source code via GitNexus
5. Chat context — last resort only

**Startup sequence every session:**
1. Read `docs/PROJECT_STATE.md` — identifies active PRD and test baseline
2. Read the active PRD — defines exact scope, files, and requirements
3. Use GitNexus to locate affected modules and consumers before touching any code

Full bootstrap checklist: `docs/AGENT_SESSION_BOOTSTRAP.md`

**Auto-approval policy:**
LOW_COST read-only actions (grep, find, git status/diff/log, targeted reads, pytest, lint) execute without approval prompts. All mutations outside PRD-scoped files, and all changes to runtime/contract/execution_policy/payload/notification/dashboard/trading logic, must stop for explicit approval. Full policy and protected file list: `docs/AGENT_WORKFLOW.md § Auto-Approval Policy`.

**Constraints:**
- Do not rely on chat history for system understanding
- Do not ask for project summaries — query the repo
- Read only the minimum files needed
- No scope drift, no inferred features, no modifications outside PRD FILES section
- Raise errors instead of silently handling invalid states
- All changes must preserve contract integrity, notification behavior, and decision logic

**Spot-Read First Policy:**
Before reading any file, identify the exact function or symbol to verify. Use `offset+limit` reads or grep to go directly to it. Do not read a full file unless the function location is unknown, symbol lookup fails, or a broad consumer audit is required. Check `docs/CALL_SITE_MAP.md` for known function line numbers before scanning.

**Cheap-Lookup Dispatch Policy:**
Read-only lookup work must be delegated to an `Explore` subagent with `model: "haiku"` whenever the exact target file is not already known. The main thread is reserved for PRD reasoning, edits, impact analysis, architecture decisions, and mutation planning.

Always dispatch to Explore+haiku:
- Any grep/find/search where the exact target file is not already known
- "Where is X defined / declared / used?"
- "Which files reference Y?"
- Locating a symbol, function, class, enum, fixture, artifact writer, or consumer by name
- Multi-file consumer audits
- Broad codebase exploration when no precise entry point is known
- File-discovery work before drafting or editing a PRD

Stay in the main thread:
- Reading a known file path with `Read`
- Single targeted grep against one known file
- GitNexus queries (`gitnexus_query`, `gitnexus_context`, `gitnexus_impact`)
- Reading PRDs, `PROJECT_STATE.md`, `PRD_REGISTRY.md`, or known docs files
- Any edit, write, patch, commit, test run, or mutation

Dispatch shape: `Agent(subagent_type: "Explore", model: "haiku", prompt: "<exact lookup question>")`. Require the Explore result to be under 150 words and include only file paths, line numbers, and short relevance notes. No long excerpts unless explicitly requested.

Rationale: Mechanical lookup work does not require main-thread reasoning. Running broad greps and file discovery in the main context wastes premium tokens, pollutes the session window, and increases drift risk during PRD work.

**[UNVERIFIED] annotation:**
If a field path, function signature, or module behavior in a PRD cannot be immediately confirmed from `docs/SCHEMA_MAP.md` or `docs/CALL_SITE_MAP.md`, mark it `[UNVERIFIED]` in the PRD. Do not guess. Verify the specific symbol before implementing — not the whole file.

---

## instrument universe

**Macro drivers (HALT_SYMBOLS — pipeline stops if any fail):**
`^VIX`, `DX-Y.NYB`, `^TNX`, `SPY`, `QQQ`

**Required symbols:** `^VIX`, `DX-Y.NYB`, `^TNX`, `BTC-USD`, `SPY`, `QQQ`

**Indices:** `SPY`, `QQQ`, `IWM`

**Commodities:** `GLD`, `SLV`, `GDX`, `PAAS`, `USO`, `XLE`

**High beta:** `NVDA`, `TSLA`, `AAPL`, `META`, `AMZN`, `COIN`, `MSTR`

**Source rules:** `^VIX`, `DX-Y.NYB`, `^TNX` — yfinance only. All others: yfinance primary, Polygon fallback.

**Constraints:** Liquid options chains only. Prefer tight bid/ask. No arbitrary expansion. 5–8 tickers per session.

---

## regime engine

8-input vote model. Each input casts: `RISK_ON | RISK_OFF | NEUTRAL`

| Input | RISK_ON | RISK_OFF |
|---|---|---|
| SPY pct | > 0.3% | < -0.3% |
| QQQ pct | > 0.3% | < -0.3% |
| IWM pct | > 0.4% | < -0.4% |
| VIX level | < 18 | > 25 |
| VIX pct | < -3% | > +5% |
| DXY pct | < -0.2% | > +0.3% |
| TNX pct | < -0.5% | > +0.8% |
| BTC pct | > 1.5% | < -2.0% |

**CHAOTIC override:** VIX single-interval spike > 15% → CHAOTIC regardless of votes.

**Classification:** `net = risk_on − risk_off`. RISK_ON if net ≥ 4 and conf ≥ 0.60, or net ≥ 2. RISK_OFF if net ≤ -4 and conf ≥ 0.60, or net ≤ -2. Else NEUTRAL.

**Postures:** CHAOTIC or conf < 0.50 → STAY_FLAT. RISK_ON + conf ≥ 0.75 → AGGRESSIVE_LONG. RISK_ON + conf ≥ 0.55 → CONTROLLED_LONG. RISK_OFF + conf ≥ 0.55 → DEFENSIVE_SHORT. NEUTRAL + VIX 18–25 → NEUTRAL_PREMIUM. All other NEUTRAL → STAY_FLAT.

---

## qualification gates

Hard gates (1–4): immediate REJECT, no watchlist.
Soft gates (5–9+): one miss → WATCHLIST. Two+ misses → REJECT.

1. **(HARD) REGIME** — posture not STAY_FLAT
2. **(HARD) CONFIDENCE** — regime.confidence ≥ 0.50
3. **(HARD) DIRECTION** — candidate direction matches regime (RISK_ON=LONG, RISK_OFF=SHORT)
4. **(HARD) STRUCTURE** — not CHOP
5. **(SOFT) STOP_DEFINED** — stop_price > 0, distance > 0
6. **(SOFT) STOP_DISTANCE** — stop ≥ 1% of entry AND ≥ 0.5× ATR14
7. **(SOFT) RR_RATIO** — R:R ≥ 2.0 (NEUTRAL: ≥ 3.0)
8. **(SOFT) MAX_RISK** — 1 contract fits within TARGET_DOLLAR_RISK × regime_multiplier
9. **(SOFT) EARNINGS** — no earnings within 5 days (None = unknown → pass)
10. **(SOFT) EXTENSION** — |entry − ema21| / atr14 ≤ 1.5
11. **(SOFT) TIME** — no entries at or after 3:30 PM ET

STAY_FLAT short-circuits all per-symbol work — no gates run.

---

## key constants

```
MIN_RR_RATIO            = 2.0
NEUTRAL_RR_RATIO        = 3.0
MIN_REGIME_CONFIDENCE   = 0.50
TARGET_DOLLAR_RISK      = $150
MAX_DOLLAR_RISK         = $200
FRESHNESS_SECONDS       = 300   (5 min max quote age)
EXTENSION_ATR_MULTIPLIER= 1.5
VIX_CHAOTIC_SPIKE       = 0.15
EMA periods             = 9 / 21 / 50
ATR period              = 14 (Wilder RMA)
LATE_SESSION_CUTOFF     = 15:30 ET
REGIME_RISK_MULTIPLIER  = RISK_ON:1.0 / RISK_OFF:1.0 / NEUTRAL:0.6 / CHAOTIC:0.0
```

---

## core rules

1. **Execution only.** Every output must affect entry, exit, sizing, or avoidance. Otherwise reject.
2. **No bloat.** No speculative logic, no unused abstractions, no adjacent features.
3. **Constraints first.** Strict rules over flexible logic. Limit conditions and inputs.
4. **Single responsibility.** One module = one purpose. No overlapping logic.
5. **PRD required.** Define OBJECTIVE, SCOPE, REQUIREMENTS, DATA FLOW, FAIL CONDITIONS before coding. No exceptions.

---

## technical rules

1. Build in strict phase order. Do not begin Phase N+1 without passing tests and manual spot-check.
2. Never hardcode secrets. All secrets come from .env via config.py.
3. Never silently catch exceptions that hide data failures. Log explicitly.
4. No derived metric is computed on unvalidated input. Ever.
5. All dataclasses are frozen=True unless documented otherwise.
6. All timestamps are UTC datetime with tzinfo. Never naive datetimes.
7. The validation layer is the most critical layer. Do not weaken it.
8. If a symbol fails validation, exclude it and log why. Never substitute.
9. PRICE_BOUNDS in config.py must be updated periodically to reflect current market levels.
10. No HTML output, no web server, no backtest engine, no ML models.

---

## package

```python
# Package name: cuttingboard
from cuttingboard.xxx import yyy
```

---

## output style

- Concise, structured, direct.
- Do not repeat the prompt.
- Do not over-explain.
- No filler.

**Research format:**
```
INSIGHT: [one sentence, measurable conditions only]
TRADE IMPACT: [entry / exit / sizing / avoidance — one playbook only]
```

---

## failure conditions

Reject or flag output that:
- Adds complexity beyond the request
- Expands scope based on assumptions
- Lacks execution impact
- Introduces vague logic
- Weakens validation

---

## priority order

1. correctness
2. scope control
3. simplicity
4. execution relevance
5. maintainability
6. validation honesty
7. speed
8. convenience

---

## PRD documentation rule

Canonical process: `docs/PRD_PROCESS.md`. Summary below.

### Lifecycle states

| State | Meaning |
|-------|---------|
| PROPOSED | Drafted. Not approved for implementation. |
| IN PROGRESS | File exists in prd_history/. Implementation has begun. |
| COMPLETE | Implementation merged. Commit hash recorded in registry. |
| PATCH | Corrective PRD targeting a specific defect in a prior PRD. |
| DEPRECATED | Requirement superseded or withdrawn before completion. |

No other status values are permitted in `PRD_REGISTRY.md`.

### Starting a PRD

1. Copy `docs/PRD_TEMPLATE.md` to `docs/prd_history/PRD-NNN.md` before writing any code.
2. Section order is fixed: `GOAL → SCOPE → OUT OF SCOPE → FILES → REQUIREMENTS → DATA FLOW → FAIL CONDITIONS → VALIDATION`
3. Add registry row with `IN PROGRESS` and file link immediately.
4. Every requirement (R1, R2, …) must have an inline `FAIL:` line — observable, binary, non-subjective.

### Scope lock

The `FILES` section defines a hard boundary. Any file modified during implementation that is not listed in `FILES` is a scope violation. Resolve by amending the PRD before touching the file, or write a separate PRD.

### Closing a PRD

After merge: set registry status to `COMPLETE`, record commit hash, and ensure the `File` column links to the prd_history file.

### Patch PRDs

A PATCH PRD corrects a defect in a prior implementation. Must include a `ROOT CAUSE` section identifying exactly one of: `missing fail condition`, `ambiguous requirement`, or `hidden dependency`.

A PRD is not complete until the registry reflects it.

### Cross-review gate

Do not invoke Codex automatically after every PRD revision. Codex is invoked only when the gate below is triggered.

**Claude-only is sufficient when all of the following are true:**
- The change is documentation-only
- The change mechanically incorporates prior review findings already accepted
- No source code changes are made
- No tests are changed
- No runtime behavior changes are made
- No artifact contract, payload schema, or artifact path/writer/reader semantics change
- No dashboard behavior changes are made
- No notification behavior changes are made
- No new sidecar behavior is introduced
- No new architecture claims are added beyond already-reviewed findings
- No unresolved disagreement remains between Claude and Codex on this PRD

**Invoke Codex when any of the following is true:**
- Source code changes are proposed or made
- Tests are changed in a way that affects runtime or artifact behavior
- Runtime, contract, payload, notification, dashboard, audit, or sidecar behavior changes
- Artifact paths, artifact contracts, schemas, or writer/reader semantics change
- Acceptance criteria are materially redesigned rather than mechanically tightened
- Claude identifies new risks not covered by the prior review
- Claude disagrees with Codex, or Codex previously disagreed with Claude on the same unresolved issue
- The review becomes messy, ambiguous, or multi-directional
- The PRD introduces a new feature, sidecar, schedule, data source, dashboard section, or decision-affecting behavior

**Token discipline for review tasks:**
- Do not call Codex unless the review gate is triggered.
- Do not run broad searches unless a new ambiguity is exposed.
- Do not re-review the entire repository unless the revision introduces something not previously examined.
- Prefer targeted file reads and targeted grep checks over full file reads.
- Prefer mechanical edits over repeated full reviews when incorporating already-accepted findings.
- Stop after completing the requested revision or review; do not continue into implementation unless explicitly instructed.
- Summarize what changed; do not dump large file contents.
- When invoking Codex, pass a narrow prompt with exact files and exact questions — do not ask Codex to re-read the whole repo.
- If Codex is invoked, write one review artifact and stop. No automatic Claude → Codex → Claude → Codex loops.

### Review artifact discipline

PRD review files are not PRDs. Do not add them to `PRD_REGISTRY.md`.

- Review artifacts live in `docs/prd_history/` as:
  - `PRD-NNN.review.claude.md` — Claude's independent review
  - `PRD-NNN.review.codex.md` — Codex review-of-review
  - `PRD-NNN.adjudication.md` — optional; only if actual unresolved disagreement requires adjudication
- Do not create an adjudication file for simple mechanical review incorporation.
- Registry rows are added only when a PRD moves to `IN PROGRESS` (implementation begins) or `COMPLETE`. A PROPOSED draft with no registry row is correct.
- The `Starting a PRD` rule "Add registry row immediately" applies at the point implementation starts, not when the draft is first written.

### Micro-PRD eligibility

A change qualifies for the micro-PRD template (`docs/PRD_MICRO_TEMPLATE.md`) if and only if ALL of the following hold:

- The change is docs-only, hook-only, test-helper-only, or process-only.
- No production runtime module behavior changes.
- No file imported (directly or transitively) by `cuttingboard/runtime.py` is modified.
- No contract, payload, dashboard, notification, market_map, qualification, or decision behavior changes.
- No artifact schema or generated output shape changes.
- No data-fetch behavior (ingestion, normalization, OHLCV) changes.
- Diff is ≤ 20 production-code lines, excluding tests, docs, and registry/state files.
- At least one deterministic FAIL condition is present.
- Targeted tests are added when executable code is changed.
- When in doubt, use the full PRD template (`docs/PRD_TEMPLATE.md`).

If ANY criterion fails, the full PRD template is required. The micro template has six sections (`GOAL → SCOPE → FILES → REQUIREMENTS → VALIDATION → COMMIT PLAN`); the OUT OF SCOPE and DATA FLOW sections from the full template are omitted because no runtime impact = no data flow to specify, and no scope expansion possible = no out-of-scope to enumerate.

### Test-suite discipline

During iteration on a PRD:

- Run targeted tests only (e.g. `python3 -m pytest tests/test_<module>.py -q`).
- Run the full suite (`python3 -m pytest tests -q`) once before pre-commit review, UNLESS one of the following justifies an additional full-suite run:
  - **(a)** A prior full-suite run failed and the fix is non-trivial.
  - **(b)** The branch was rebased onto new main work.
  - **(c)** A shared helper, fixture, or `conftest.py` was modified.
  - **(d)** An infrastructure-level change was made (config, dependency, pytest plugin, CI script).

Re-running the full suite outside these exceptions wastes time and test-output context tokens without verification value.

### Task tracking discipline

For linear single-PRD work, do not create task/checklist artifacts solely because a reminder or tool nudge appears. Use task tracking only when the work is genuinely multi-step, multi-file, concurrent, or benefits from explicit checklist state. The trigger is actual task complexity, not reminder presence.

---

## git hygiene and artifact discipline

### Before starting work

- Check current branch: `git branch --show-current`
- Check status: `git status --short`
- Do not start with unresolved conflicts.
- Default to `main` unless the user explicitly names another branch.

### Generated artifacts

- Do not commit `logs/*` or `reports/*` unless the user explicitly requests it.
- Never use `git add .` during PRD work — stage explicit files only.
- If in doubt, run `scripts/clean_generated_artifacts.sh` to restore tracked log files to HEAD.

### Before committing

- Show staged files: `git diff --cached --name-only`
- Warn if `logs/*` or `reports/*` appear in staged set.
- Confirm recent commits: `git log --oneline -5`
- Run `scripts/pre_commit_sanity.sh` for a compact checklist.

### Workflow reruns

Do not rerun all workflows blindly. Match issue to workflow:

| Issue | Workflow |
|-------|----------|
| Source / test failures | Cuttingboard Pipeline |
| Dashboard publish | Deploy to GitHub Pages |
| Notification | Hourly Alert |

Always use `--ref main` unless another branch is explicitly required.

---

## final rule

When uncertain: simplify → reduce → constrain.

# GitNexus — Code Intelligence

This project is indexed by GitNexus as **cuttingboard**. Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Impact Analysis — Tiered Policy

**Skip `gitnexus_impact` for low-risk edits:**
- Constants, config thresholds, or numeric values (e.g. in `config.py`)
- String literals, log messages, or error text
- Comments or docstrings
- PRD bookkeeping files (`PRD_REGISTRY.md`, `PROJECT_STATE.md`, `prd_history/`)
- Test assertions or test data fixtures

**Always run `gitnexus_impact({target, direction: "upstream"})` before editing:**
- Any function or method signature or return type
- Any validation, qualification, regime, or derived metric logic
- Any module in the execution pipeline (layers 1–11 in CODEX.md)
- Any symbol flagged HIGH or CRITICAL in a prior impact report
- Any rename or structural refactor

**Always run `gitnexus_detect_changes()` before every commit** — no exceptions. Report blast radius and affected flows to the user.

**MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding.

## Exploration

- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/cuttingboard/context` | Codebase overview, check index freshness |
| `gitnexus://repo/cuttingboard/clusters` | All functional areas |
| `gitnexus://repo/cuttingboard/processes` | All execution flows |
| `gitnexus://repo/cuttingboard/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |
