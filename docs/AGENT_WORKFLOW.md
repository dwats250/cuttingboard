# AGENT_WORKFLOW.md - Auto-Approval Policy

The operating model for Cuttingboard lives in `CLAUDE.md`. This file exists for
one purpose: it defines the **protected-file set** that the PRD skills
(`scope-lock-precommit`, `prd-authoring-verified`) read to decide which files
require a `LANE: HIGH-RISK` PRD. Keep the `## Auto-Approval Policy` heading and
the "Never auto-approve" table stable - the skills parse them verbatim.

## Auto-Approval Policy

Read-only inspection and in-scope mechanical edits proceed without a stop;
anything that mutates protected surface, or repo state outside the active PRD's
`FILES` set, stops for explicit approval. The live enforcement is the harness
permission model in `.claude/settings.json`; the tables below are the policy the
PRD skills consume.

### Auto-approved (low-cost)

| Action | Notes |
|---|---|
| `grep` / `find` / `ls`, `git status` / `diff` / `log` | Read-only inspection |
| Read targeted file snippets | Files in PRD scope; use `offset+limit` |
| Targeted or full `pytest`, `ruff` / format checks | Validation |
| Create or update documentation | `docs/`, `*.md` - no logic files |
| Mechanical edits to in-scope files | Files listed in the active PRD `FILES` |

### Never auto-approve (protected pipeline set)

| Category | Files / patterns |
|---|---|
| Runtime core | `runtime/` |
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

A file in this set may be edited only under a `LANE: HIGH-RISK` PRD that lists it
in `FILES`; otherwise stop and escalate the lane or split the PRD.
