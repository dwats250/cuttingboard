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
- Lint / format checks
- Mechanical edits with exact instructions (rename, move, delete line)
- PRD registry and state file reads

**Rule:** Collect evidence first. Do not reason before running these.

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
| Before any Edit/Write | Always | `gitnexus_impact` if symbol is HIGH_REASONING tier |
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
| Latest completed PRD | PRD-068 (Invalidation & Exit Guidance) |
| Active PRD | none |
| Test baseline | 1806 passing |
| Next PRD slot | PRD-069 |
| Evaluation layer | planned, not built |
| Hooks | git_gate, protect_files, test_gate, stop_snapshot — all active |
