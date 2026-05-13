# AGENT_WORKFLOW.md — Token & Compute Discipline

Governs how the agent reasons, reads, and responds inside this repo.
These rules reduce unnecessary compute while preserving correctness.

---

## Task Cost Tiers

### LOW_COST — execute without extended reasoning

- `grep` / `find` / symbol existence checks
- `git status`, `git diff`, `git log`
- File discovery and path resolution
- Enum / constant / status validation
- Targeted `pytest -k <pattern>` runs
- Full `pytest` suite run
- Lint / format checks
- Mechanical edits with exact instructions (rename, move, delete line)
- PRD registry and state file reads
- Read targeted snippets of files already in scope
- Create or update documentation files

**Rule:** Collect evidence first. Do not reason before running these.

---

### LEAF_FILE — skip gitnexus_impact, edit directly

A file is a leaf if it contains **no `from cuttingboard.` or `import cuttingboard` statements**. These files have no downstream consumers in the Python call graph.

Qualifying leaf files:
- Pure CSS files (`ui/styles.css`, `ui/themes/*.css`)
- Pure documentation (`docs/**/*.md`, `CLAUDE.md`, `*.md`)
- Pure data / config files with no internal imports (`pyproject.toml`, `.github/workflows/*.yml` — but see Never Auto-Approve list)
- Static UI assets (`ui/index.html`, `ui/app.js`, `ui/dashboard.html`) — only when the edit does not touch rendering logic already covered by HIGH_REASONING

**Rule:** Run a quick `grep -n "from cuttingboard\|import cuttingboard"` on the file before skipping. If any line matches, treat the file as HIGH_REASONING, not LEAF_FILE.

**Exception:** Even if a file is a leaf, it remains in the Never Auto-Approve list if it matches a protected pattern (dashboard logic, CI workflows, etc.).

---

### HIGH_REASONING — stop, collect full context, then reason

- Architecture or data-flow changes
- PRD authoring or critique
- Contract / schema changes (dataclasses, output format, payload shape)
- Execution policy changes (gate logic, regime thresholds, posture rules)
- Notification / dashboard / audit log changes
- Any change to trade-decision logic
- Ambiguous CI failures (not a trivial import error)
- Any edit where impact analysis returns HIGH or CRITICAL

**Rule:** Run `gitnexus_impact` before touching any symbol in this tier.
Report blast radius to the user before writing a single line.

---

## Auto-Approval Policy

LOW_COST actions execute without prompting the user for approval. All other actions stop for explicit approval before proceeding.

### Auto-approved (LOW_COST only)

| Action | Notes |
|---|---|
| `grep` / `find` / `ls` | Any read-only search or listing |
| `git status`, `git diff`, `git log` | Read-only git inspection |
| Read targeted file snippets | Files already in PRD scope; must use `offset+limit` |
| Inspect exact symbols | Via `gitnexus_context`, `gitnexus_query`, `grep` |
| Run targeted `pytest -k <pattern>` | Named test scope only |
| Run full `pytest` suite | Pre-commit validation only |
| Run lint / format checks | `ruff`, `black --check`, `mypy` |
| Create or update documentation files | `docs/`, `CLAUDE.md`, `*.md` — no logic files |
| Mechanical edits to in-scope files | Files listed in active PRD `FILES` section |

### Never auto-approve

| Category | Files / patterns |
|---|---|
| Runtime core | `runtime.py` |
| Output contract | `contract.py` |
| Execution policy | `execution_policy.py` |
| Payload / notification | `*payload*.py`, `*notification*.py`, `*notify*.py` |
| Dashboard / UI | `*dashboard*.py`, `*panel*.py`, `*ui*.py` |
| Trading logic | `*regime*.py`, `*gate*.py`, `*qualify*.py`, `*signal*.py` |
| Environment / secrets | `.env`, `config.py`, `secrets.*` |
| CI workflows | `.github/`, `*.yml` CI files |
| Dependency files | `pyproject.toml`, `requirements*.txt`, `setup.cfg` |
| Destructive commands | `rm`, `git reset --hard`, `git clean`, file deletion |
| Git push | Any `git push` in any form |
| Test expectation changes | Modifying expected counts, thresholds, or assertion values |

### Auto-approval rules

1. Auto-approved actions must still appear in the final build report under `AUTO_APPROVED_ACTIONS`.
2. Any action outside the LOW_COST list must stop and request approval.
3. Any command that mutates repo state outside explicitly PRD-scoped files must stop for approval.
4. A failed command must stop, report the failure summary, and not continue until the agent receives direction.
5. Auto-approval does not override PRD `FILES` scope — a LOW_COST action on an out-of-scope file still requires approval.

### Auto-approval failure conditions

| ID | FAIL when |
|---|---|
| F9 | Agent requests approval for a LOW_COST read-only command |
| F10 | Agent auto-approves a mutation outside explicitly scoped files |
| F11 | Agent auto-approves changes to trading / runtime / contract / payload / notification / dashboard logic |
| F12 | Agent pushes commits without explicit user approval |

---

## Safe Command Auto-Approval Policy

During PRD implementation, review, closeout, and CI investigation, the agent may run the following command classes without repeatedly asking for approval, provided they do not modify files:

### 1. Git read-only inspection

- `git status -sb`
- `git status --short`
- `git log --oneline -N`
- `git show --stat <commit>`
- `git show --name-only --oneline <commit>`
- `git show <ref>` / `git show <ref>:<path>`
- `git diff --stat`
- `git diff --name-only`
- `git diff -- <scoped files>`
- `git diff --cached --name-only`
- `git diff <ref>` / `git diff <refA>..<refB>` (read-only ref comparison)
- `git fetch` (no `--prune` of local branches; remote-tracking refs only)
- `git blame <path>`
- `git ls-files` / `git ls-files <pattern>`
- `git stash list`
- `git stash show` (read-only; `git stash show -p` allowed; `pop`/`apply` not auto-approved)
- `git rev-parse <ref>` / `git rev-parse --show-toplevel`
- `git branch --show-current`

### 2. GitHub CLI read-only inspection

- `gh run list`
- `gh run view`
- `gh run view --json ...`
- `gh run view --log` / `gh run view --log-failed`
- `gh run watch <run_id>` (read-only stream; ends when run completes)
- `gh workflow view`
- `gh workflow list`
- `gh pr list`
- `gh pr view <num>` / `gh pr view --json ...`
- `gh pr diff <num>`
- `gh pr checks <num>`
- `gh release list`
- `gh release view <tag>`
- `gh api` GET / read-only calls used only for inspection

### 3. File / text read-only inspection

- `grep` / `rg` searches
- `sed -n` reads
- `cat` reads
- `head` / `tail` reads
- `find` reads
- `ls` / `tree` reads
- `wc` / `stat` reads
- `diff <a> <b>` / `diff -u <a> <b>` (file comparison, no `-i` interactive)
- `comm` (set comparisons over sorted files)
- `sort -u` / `sort | uniq` (read-only stream transforms)
- `jq` over local files or piped input (no `--in-place` / `-i`)
- `python3 -m json.tool <path>` (JSON pretty-print / validate)
- `python3 -c "<expr>"` one-liners that ONLY read or print — no file writes, no network mutations, no subprocess side effects

### 4. Validation commands

- `python3 -m pytest <specific test file> -q`
- `python3 -m pytest tests/ -q`
- `python3 -m pytest --collect-only` (test discovery, no execution)
- `python3 scripts/check_readiness.py`
- `ruff check` / `ruff check <path>`
- `ruff format --check` (verify-only; `ruff format` without `--check` mutates and is NOT auto-approved)
- `mypy` / `mypy <path>`
- Project validation scripts that are read-only and do not mutate artifacts
- PRD functional validation snippets copied exactly from the PRD when they are read-only

### 5. Workflow / status investigation

- `gh run list --workflow <workflow> --limit N`
- `gh run view <run_id> --json jobs,url,status,conclusion`
- `gh run view <run_id> --log-failed`
- `gh run watch <run_id>` — preferred over polling loops; see Background Workflow Watching

### Batching rule

The agent should batch safe read-only checks into one shell block where practical instead of asking one command at a time.

Example:

```bash
git status -sb && \
git status --short && \
git log --oneline -8 && \
gh run list --workflow hourly_alert.yml --limit 5
```

### Still require explicit approval before

- `git push`
- `git pull`
- `git rebase`
- `git merge`
- `git reset`
- `git restore`
- `git checkout`
- `git stash`
- `git commit`
- `rm` / delete operations
- `chmod` or permission changes
- package installs
- networked commands that mutate state
- `gh workflow run`
- `gh run rerun`
- `gh api` POST / PATCH / DELETE
- modifying generated UI / log artifacts
- modifying files outside the PRD `FILES` scope
- rewriting commit history
- applying patches or editing files

### Read-only vs mutating gh commands

Read-only `gh` commands are safe inspection. Mutating `gh` commands are not. The agent must distinguish:

- **Allowed without repeated prompts:** `gh run list`, `gh run view`, `gh workflow view`, `gh workflow list`
- **Ask first:** `gh workflow run`, `gh run rerun`, `gh api` POST / PATCH / DELETE

### Stop conditions

The agent must stop and ask before continuing if:

- working tree is dirty before implementation
- branch is behind / ahead unexpectedly
- remote diverged
- unexpected files changed
- generated artifacts changed unexpectedly
- validation fails
- a command would mutate repo, remote, workflow state, files, or history
- the requested change requires files outside PRD `FILES`

### Relationship to the broader Auto-Approval Policy

This section enumerates concrete commands for the existing LOW_COST tier. It does NOT broaden the LOW_COST tier and does NOT override the Never-Auto-Approve list, the PRD `FILES` scope lock, or the F9–F12 failure conditions above. When a command in this section would touch a protected path or a file outside `FILES`, the Never-Auto-Approve and scope-lock rules win.

---

## Sub-Agent Dispatch Standard

Sub-agent dispatch is not optional decoration — it is the mechanism that
keeps the main thread reserved for PRD reasoning, edits, impact analysis,
and mutation planning. The default lookup agent is
`Agent(subagent_type: "Explore", model: "haiku")` with a result budget of
≤ 150 words: file paths, line numbers, short relevance notes only.

### MUST dispatch to Explore+haiku

The following situations require a sub-agent. Doing the work on the main
thread is a workflow violation.

- **PRD FILES existence verification** before promoting a PRD to
  `IN PROGRESS`. Every path in the `FILES` section must be confirmed to
  exist (or be explicitly marked as a new file) via Explore lookup.
- **Visible-string / test-reference hunts** spanning ≥ 3 files or > 5
  literal strings (per CLAUDE.md Visible-String Pre-Edit Audit). The
  audit's grep step is a dispatch trigger, not a main-thread task.
- **Regression hunts** involving lineage / coherence / renderer
  diagnostics — anything that requires walking multiple renderers,
  fixtures, or golden files to identify the divergence point.
- **Broad grep / sweep operations** across `renderer/`, `tests/`, or
  `docs/` trees when the target file is not already known.
- **Consumer audits** when changing a symbol's signature, return type,
  or semantics and the full caller set is not already in hand from
  `gitnexus_impact`.

### MUST stay on main thread

- Reading a known file path with `Read` (`offset+limit` preferred).
- Single targeted grep against one known file.
- `gitnexus_query`, `gitnexus_context`, `gitnexus_impact`.
- Reading PRDs, `PROJECT_STATE.md`, `PRD_REGISTRY.md`, `CALL_SITE_MAP.md`,
  `SCHEMA_MAP.md`, or other known docs files.
- Any edit, write, patch, commit, test run, or mutation.

### Wasteful-cycle thresholds

The main thread must leave for a sub-agent when ANY of the following
occurs in a single task:

| Threshold | Trigger |
|---|---|
| T1 | A second broad `grep`/`rg` sweep is about to run because the first did not narrow the target. |
| T2 | Three or more `Read` calls have occurred on files not yet confirmed to be in PRD scope. |
| T3 | The same symbol has been searched in two or more directory roots without a hit. |
| T4 | A literal-string audit spans ≥ 3 files OR > 5 strings (hard rule, not a heuristic). |
| T5 | The next planned action is "skim a few files to orient" rather than verify one named symbol. |

If a threshold trips, stop the current main-thread exploration and dispatch
Explore+haiku with the precise remaining question. Continuing to grep/read
past these thresholds is the failure mode this section exists to prevent.

### Lightweight Explore preference

Prefer one well-scoped Explore dispatch over a sequence of main-thread
grep + read cycles when the answer is "where is X / which files reference Y
/ does Z exist." A single sub-agent call with a 150-word budget costs less
total context than 4–6 main-thread tool calls and prevents drift into
adjacent files.

---

## Session Bootstrap and Workflow Efficiency

### Standard session bootstrap command block

Run this block at the start of every PRD-implementation session. It
batches the read-only checks required by CLAUDE.md's startup sequence
into a single shell invocation.

```bash
git branch --show-current && \
git status -sb && \
git log --oneline -8 && \
git diff --stat && \
git diff --cached --name-only
```

Follow with the documentation reads required by CLAUDE.md:

1. `docs/PROJECT_STATE.md` — identify active PRD and test baseline.
2. The active PRD file in `docs/prd_history/`.
3. `docs/PRD_REGISTRY.md` row for the active PRD.

Bootstrap reads are LOW_COST and auto-approved. Do not split this block
into one-command-at-a-time prompts.

### IGNORED_DIRTY_PATHS

Some paths are intentionally dirty between sessions (review scratch files,
in-progress notes, locally regenerated artifacts that are not committed by
policy). The agent must not treat their dirtiness as a stop condition for
the standard "working tree is dirty before implementation" rule, provided
the dirty file matches an entry in this list AND is not in the active
PRD's `FILES` scope.

Current `IGNORED_DIRTY_PATHS`:

- `docs/prd_history/PRD-*.review.codex.md` — Codex review scratch
- `docs/prd_history/PRD-*.review.claude.md` — Claude review scratch
- `docs/prd_history/PRD-*.adjudication.md` — adjudication scratch
- `logs/**` — generated logs (per CLAUDE.md git hygiene)
- `reports/**` — generated reports (per CLAUDE.md git hygiene)

Rules:

1. A path matching `IGNORED_DIRTY_PATHS` does NOT relax scope lock — it
   only relaxes the pre-implementation dirty-tree stop condition.
2. If an ignored-dirty path appears in `git diff --cached`, that is still
   a stop condition. Ignoring applies to unstaged dirtiness only.
3. Adding new entries to this list is a process change and requires
   explicit user approval.

### Background workflow watching

When monitoring a GitHub Actions run, a long-running test, or any external
state the harness cannot notify on:

- **Preferred:** `gh run watch <run_id>` (streams to completion; one
  command, no polling loop).
- **Acceptable:** a single `gh run view <run_id> --json status,conclusion`
  check after an expected ETA.
- **Avoid:** repeated `gh run list` / `gh run view` calls every few
  seconds. This is the polling antipattern and burns context for no
  signal.

If a watch command is impractical (e.g., the run id is not yet known),
batch the discovery and the watch into one shell block rather than two
separate approval cycles:

```bash
RUN_ID=$(gh run list --workflow hourly_alert.yml --limit 1 --json databaseId --jq '.[0].databaseId') && \
gh run watch "$RUN_ID"
```

### Batched inspection over fragmented calls

Read-only inspections must be batched into a single shell block whenever
the commands are independent and the agent already knows it will run all
of them. Fragmented single-command shells trigger approval friction and
inflate the transcript without adding signal.

Batch when:

- Two or more read-only commands from the Safe Command Auto-Approval list
  will run back-to-back with no decision between them.
- A bootstrap, status check, or post-commit verification spans multiple
  commands that do not depend on each other's output.

Do not batch when:

- A later command depends on parsing an earlier command's output (run
  them sequentially so the agent can react).
- One of the commands is mutating or outside the auto-approval list.

---

## Spot-Read First Policy

Before reading any file, identify the exact function or symbol to verify.

1. Check `docs/CALL_SITE_MAP.md` — if the function is listed, use its line
   number with `offset+limit` to read directly.
2. Check `docs/SCHEMA_MAP.md` — if the field is listed, no read needed.
3. If not found in either map, use `grep` to locate the symbol.
4. Only after location is known: read the targeted lines.
5. Full-file reads are only permitted when:
   - function location is unknown after grep
   - module structure is unknown
   - multiple consumers require broad audit

**FAILURE (F2 applies):** Full-file read performed before function target was
identified via grep, CALL_SITE_MAP.md, or snippet.

---

## [UNVERIFIED] Annotation Standard

When a PRD or review proposes a field path, function name, or module behavior
that cannot be confirmed from `docs/SCHEMA_MAP.md` or `docs/CALL_SITE_MAP.md`:

- Mark it `[UNVERIFIED]` in the PRD.
- Do not guess or invent. Do not proceed to implementation on an unverified
  field.
- During review: verify the specific symbol only — not the whole file.
- After verification: update `docs/SCHEMA_MAP.md` or `docs/CALL_SITE_MAP.md`
  with the confirmed path.

**FAILURE:** PRD accepted for implementation with an `[UNVERIFIED]` field that
was never resolved.

---

## PRD Review Read Budget

Before beginning any PRD review or implementation:

1. State the target functions and fields to verify.
2. State the file and line for each (from CALL_SITE_MAP.md if available).
3. State why each read is needed.
4. If a full-file read is required, explain why targeted reads were insufficient.

Review output must contain only: Strengths, Blockers, Exact fixes, Registry
readiness verdict. No broad summaries of unrelated modules.

---

## Retrieval Planning Rule

Before executing shell operations on any task that meets ANY of the
following triggers, the agent MUST state a short retrieval/verification
plan first:

- The change spans more than 3 files.
- The work will require more than 3 distinct repository inspections
  (grep, find, read, gitnexus call).
- The work involves broad renderer / tests / docs sweeps.
- Initial scoping risks repeated grep or read cycles to converge on
  the right symbol set.

The plan must enumerate:

1. The exact targets to locate (symbol, field, string, file).
2. The single retrieval method per target (grep pattern, gitnexus
   query, CALL_SITE_MAP / SCHEMA_MAP lookup, or Explore+haiku
   dispatch).
3. Which targets are main-thread reads vs. delegated lookups.

Goal: collapse fragmented inspections into one ordered pass. No
exploratory greps before the plan exists. No "let me just check one
thing" cartography loops.

**FAILURE:** Agent runs three or more retrieval commands on a task
matching the triggers above without having first stated the
retrieval plan.

---

## Main Thread Responsibility

The main thread is a scarce reasoning context. It is reserved for
work that requires synthesis across evidence already in hand.

Main thread SHOULD prioritize:

- Synthesis of retrieved evidence into a decision.
- Architectural reasoning and cross-module impact judgment.
- PRD interpretation, scope enforcement, FILES boundary checks.
- Conflict resolution between competing signals (test failures,
  reviewer disagreements, ambiguous requirements).
- Final validation and acceptance / rejection decisions.
- Authoring edits, patches, and commits.

Main thread SHOULD avoid:

- Broad search sweeps where the target file is not already known.
- Repetitive grep loops to triangulate a symbol.
- Repository cartography ("what's in this folder?", "how is this
  area organized?").
- Low-value repeated inspections of files already read this session.
- Retrieval work that fits the Cheap-Lookup Dispatch Policy — those
  go to `Agent(subagent_type: "Explore", model: "haiku")`.

If the next action is mechanical retrieval, the main thread should
either delegate it or batch it inside a stated retrieval plan, not
absorb it into freeform reasoning.

---

## CI / Failure Triage Discipline

When a test, workflow, or pipeline fails, the agent MUST follow this
sequence before modifying any code:

1. **Inspect failing logs / stage first.** Read the actual failure
   output. Identify the failing stage, command, and error line.
2. **Localize the failing invariant.** Name the specific assertion,
   exception, exit code, or contract violation that fired.
3. **Reproduce minimally.** Run the narrowest command that
   reproduces the failure (`pytest -k <name>`, single workflow step,
   single payload). Do not rerun the full suite or full workflow as
   a diagnostic step.
4. **Verify failure scope.** Confirm whether the failure is isolated
   to one test / one path, or whether it indicates broader breakage.
   Establish what is NOT broken before proposing a fix.
5. **Only then modify code.** The fix MUST target the localized
   invariant from step 2. Speculative edits "to see if it helps"
   are prohibited.

Goal: prevent speculative editing, chaotic debugging, and
shotgun-pattern fixes that mutate unrelated code while chasing a
single failure.

**FAILURE:** Agent edits code before stating the failing invariant
from step 2, or reruns the full suite as a diagnostic before
reproducing minimally.

---

## Command-First Workflow

Execute in this order. Do not skip ahead.

```
1. git status --short            # What is dirty?
2. grep -n "SymbolName" ...      # Does the target exist?
3. Read snippet (offset + limit) # Only the relevant lines
4. gitnexus_impact               # Who does this affect?
5. Read full file                # Only if snippet is insufficient
6. Write / Edit                  # Only after evidence is in hand
7. pytest -k <specific_test>     # Targeted, not full suite
8. Full pytest                   # Only before commit approval
```

Never read a full file when a 20-line snippet answers the question.
Never run the full test suite when a targeted `pytest -k` suffices.

---

## File Access Discipline

- MUST read minimum lines needed (use `offset` + `limit` on Read).
- MUST NOT re-read a file that has not changed in the same session.
- MUST NOT open a file to "orient" — use `gitnexus_context` instead.
- MUST NOT read unchanged dependency files when editing one module.
- Cache resolved paths and symbol locations within the session.

---

## Output Format (all non-trivial responses)

```
SUMMARY:    One sentence. What happened or what was decided.
EVIDENCE:   Grep result / snippet / test output that supports it.
RISKS:      What could break. Empty if none.
ACTION:     Exact next step. File, line, command, or "none needed".
VALIDATION: How to confirm the action worked.
```

Skip sections that are empty. Never pad with filler.

---

## MUST / MUST NOT Rules (paste into CLAUDE.md if enforcing globally)

```
MUST run gitnexus_impact before editing any function, class, or method.
MUST collect grep/git evidence before reasoning about a change.
MUST use offset+limit when reading files — no full reads for orientation.
MUST use targeted pytest -k before running the full suite.
MUST use the 5-field output format (SUMMARY/EVIDENCE/RISKS/ACTION/VALIDATION).
MUST NOT re-read a file that has not changed in the current session.
MUST NOT open a file to "get context" — use gitnexus_context instead.
MUST NOT reason about architecture before running impact analysis.
MUST NOT run full pytest mid-session except immediately before commit approval.
MUST NOT produce filler prose — every sentence must carry an action or finding.
```

---

## Enforcement Checkpoints

| Checkpoint | Trigger | Required action |
|---|---|---|
| Before any Edit/Write | Always | `gitnexus_impact` if HIGH_REASONING tier; skip if LEAF_FILE (grep confirms no internal imports) |
| Before commit | Always | Full `pytest`, clean git status, PRD scope check |
| Before full file read | Always | Attempt grep + snippet first |
| Before architecture response | Always | Collect evidence; output SUMMARY/EVIDENCE/RISKS/ACTION |

---

## Failure Enforcement (MANDATORY)

These rules convert workflow guidance into enforceable behavior.
Any violation is a FAILURE — stop, revert, rerun from the correct step.

| ID | Condition | FAILURE when |
|---|---|---|
| F1 | Premature Reasoning | Reasoning occurs before grep, file evidence, or command output |
| F2 | Full File Overread | File read in full before target symbol was located via grep |
| F3 | Redundant File Reads | Same file read again without new search criteria or new scope |
| F4 | Unbounded Output | Response exceeds structured format, repeats context, or adds unnecessary explanation |
| F5 | Task Misclassification | LOW_COST task triggers architecture discussion or speculative reasoning |
| F6 | Evidence-Free Claims | Any statement not backed by a file path, symbol, or command output |
| F7 | Scope Violation | Agent proposes changes outside explicitly requested scope or PRD FILES |
| F8 | PRD Shortcutting | PRD critique begins before FILES validation, symbol validation, and enum validation |
| F9 | Approval Nag | Agent requests approval for a LOW_COST read-only command |
| F10 | Unauthorized Mutation | Agent auto-approves a mutation outside explicitly scoped files |
| F11 | Protected File Bypass | Agent auto-approves changes to trading/runtime/contract/payload/notification/dashboard logic |
| F12 | Unauthorized Push | Agent pushes commits without explicit user approval |

### Recovery Protocol

```
STOP.
State which failure rule was triggered.
Rerun from the last valid step in Command-First Workflow.
Do not proceed until evidence is collected.
```

---

## Milestone Snapshot (2026-05-02)

| Item | State |
|---|---|
| Latest completed PRD | PRD-070 (Manual Trade Journal and Mistake Taxonomy) |
| Active PRD | none |
| Test baseline | 1834 passing |
| Next PRD slot | PRD-071 |
| Evaluation layer | planned, not built |
| Hooks | git_gate, protect_files, test_gate, stop_snapshot — all active |
| Auto-approval policy | active — LOW_COST actions exempt from approval prompts |
