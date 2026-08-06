# CuttingBoard Owner-Merge / Agent-Managed-Closeout Convention

Status: RATIFIED UPON DUSTIN'S MERGE OF PR #221

This document records an operating convention Dustin authored. It is an
owner-authored mandate, recorded faithfully; the persisting agent is the
scribe, not the author. Dustin's merge of PR #221 is the ratifying action.
Before that merge this document is a held draft and is not binding; no agent
may treat this status line as advance ratification.

It complements `CLAUDE.md` (GOV-1 — Dustin merges every PR; PRD-186 governance
draft-hold) and
`docs/governance/PRODUCT_DELIVERY_OPERATING_RULE_2026-08-06.md` (owner holds,
anti-stall). It changes no merge authority — every merge remains Dustin's — and
adds no gate, schema, or consumer. What it settles is the division of labor
*around* the merge: Dustin keeps the judgment calls; agents own the
deterministic completion work that precedes and follows the merge, verifying
rather than re-asking.

## 1. Owner holds — exclusive to Dustin

Dustin exclusively retains:

- semantic and product rulings;
- Gate A;
- explicit ratification decisions;
- every merge.

## 2. Agent-managed deterministic closeout — no additional owner prompt

Once a PR's final head is SHA-pinned, independently reviewed,
correction-complete, validator/CI-green, and held for Dustin, an agent may —
without another owner prompt —

- remove generated-by or agent-attribution boilerplate from PR metadata;
- mark a draft ready when the documented governance/review hold has been fully
  satisfied;
- update the PR body to report the actual final head, review outcome,
  corrections, residuals, and CI state;
- after Dustin merges, verify that `main` contains the expected reviewed tree;
- close explicitly superseded PRs with a provenance comment;
- reconcile local and remote branch state;
- delete a merged or explicitly superseded branch only after proving it
  contains no unique commits or unpreserved artifacts;
- report the completed seam and any remaining product gate.

## 3. Mandatory stop conditions

The agent stops and returns the decision to Dustin — it does not proceed
autonomously — when any of these is true:

- the expected merge is not present;
- the merged tree differs materially from the reviewed head;
- CI or a required validator is not green;
- the branch or superseded PR contains unique unpreserved work;
- the requested action changes product semantics, governance policy, or
  production behavior rather than reconciling recorded state;
- repository authorities conflict.

## 4. Attribution hygiene

Generated-by, Claude Code, or equivalent agent-promotion footers are not part
of repository truth and are removed automatically from PR bodies and authored
artifacts unless Dustin explicitly requests them.

## 5. Principle

Governance should require Dustin's judgment where judgment is necessary, while
agents own deterministic completion work. Verification replaces repeated
permission-seeking; exact SHA pinning and stop conditions prevent autonomous
closeout from outrunning repository truth.
