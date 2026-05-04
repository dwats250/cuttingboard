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
