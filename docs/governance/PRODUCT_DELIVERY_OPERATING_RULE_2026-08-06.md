# CuttingBoard Product-Delivery Operating Rule

Status: RATIFIED UPON DUSTIN'S MERGE OF PR #220

This document records the operating rule Dustin authored for the session of
2026-08-06. It is an owner-authored mandate, recorded verbatim; the persisting
agent is the scribe, not the author. Dustin's merge of PR #220 is the ratifying
action. Before that merge this document is a held draft and is
not binding; no agent may treat this status line as advance ratification.

It complements the operating model in `CLAUDE.md` and the material-review order
in `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md`. Where this rule
names an owner hold or an escalation trigger, it restates a frame those
documents already assume. Where it names the active-lane order (Product-priority
rule), it is an **owner directive that sets lane priority**, not a restatement:
it re-sequences GEX ahead of the North Star LATER ranking (GEX #6, behind
NS-4A/B and the Opportunity Set Engine, in
`docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` and
`docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`), codifying Dustin's
2026-08-05 BALANCED-route ruling. That precedence, and exactly what it
supersedes, is recorded in `docs/DECISIONS.md` (2026-08-06). Setting lane
priority does not lift a lifecycle gate: GEX stays subject to Dustin's "GEX
go/stop after evidence" hold and its `EVIDENCE BLOCKED` status until that
evidence exists. This document introduces no new gate, schema, or consumer.

CuttingBoard governance exists to protect truthful product delivery, not to
displace it.

## Default behavior

1. Verify every prerequisite against current repository and GitHub state.
2. Stop immediately when a required prerequisite is false.
3. Do not manufacture completion, authorization, review, evidence, or
   chronology.
4. Once prerequisites are satisfied, move directly to the next authorized
   product step.
5. Keep unrelated governance debt, documentation drift, and adjacent findings
   out of the active lane unless they create:
   - false evidence;
   - unsafe execution;
   - data corruption;
   - irreversible repository damage;
   - or a genuine block to the current product slice.

## Escalation rule

Opus 4.8 is the default orchestrator.

Invoke Fable only when one of these occurs:

- repository authorities materially contradict each other;
- a design choice changes product semantics;
- a MATERIAL boundary or FILES ceiling must be reset;
- a review reveals an omitted consumer class;
- an unresolved owner decision blocks forward motion;
- repeated friction indicates the current workflow or architecture is wrong;
- the team is beginning to repeat archaeology or lose the product objective.

Do not invoke Fable for routine execution, deterministic bookkeeping, ordinary
corrections, CI follow-up, or straightforward reviews.

## Anti-stall rule

No agent may remain in an open-ended investigation once the decision-relevant
evidence is sufficient.

When friction appears, the agent must choose one:

- resolve it within the existing authority;
- isolate it as named non-blocking debt;
- present Dustin with a bounded decision;
- or escalate the exact ambiguity to Fable.

"Continue investigating" is not a default state.

## Product-priority rule

After TRUTH-SYNC closes, the active lanes are:

1. NS-2E Market Control Card
2. GEX evidence → producer → display
3. Context registry → news and heatmap

Governance work may not replace these lanes unless a concrete blocking defect
meets the stop conditions above.

> **Owner clarification (2026-08-06, recorded at ratification):** TRUTH-SYNC
> completes when PR #219 is merged into `main`. The subsequent closure of PR
> #184 as superseded is post-merge seam closeout and does not block activation
> of the product lanes above. Until PR #219 merges, the lane order above is
> dormant.

## Owner holds

Dustin retains:

- Gate A;
- semantic rulings;
- registry ratification;
- GEX go/stop after evidence;
- NEWS-2 KEEP/REVISE/RETIRE;
- every merge.

Agents prepare evidence and recommendations. They do not infer owner approval.

## Success criterion

The process is working when:

- repository truth stays reliable;
- false prerequisites are caught early;
- decisions arrive with bounded options;
- product slices reach Dustin quickly;
- and Fable is used as high-leverage consultation rather than a permanent
  dependency.
