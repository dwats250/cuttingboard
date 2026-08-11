# Agent seating — current operational defaults (informative)

This file RECORDS the current operational defaults for the harness seats defined
in `CLAUDE.md`. It owns no authority and holds no governance facts: it is a
point-in-time record of current state, not a source of any permission, lifecycle
gate, or reviewer/event selection. Binding governance owns all authority; this
record never does. It cannot select or waive a required gated reviewer or event.
On any conflict with a governance source, this record is wrong and is corrected;
governance is never reinterpreted to match it.

## Current seating (routing defaults, not capability guarantees)

| Seat | Current default |
|---|---|
| HELM / orchestrator | Opus 4.8, High |
| HELM — major planning / architecture | Opus 4.8, Extra High |
| Builder | Opus 4.8, High |
| Navigator | Fable, High |
| Navigator — sticky / contradictory / high-blast-radius | Fable, Extra High |
| Mechanical / preflight / recon subagent | Opus 5 or Sonnet 5, lowest adequate reasoning |
| Adversary / independent review | Codex/Sol, selectively, within existing gated-event rules |

Adversary (Codex/Sol) reasoning effort: economical default for ordinary bounded
review; selective escalation to higher or max reasoning for unusually
consequential, sticky, or explicitly experimental deep-review work; no permanent
ceiling. Multi-agent or Ultra-style Codex runs are deliberate experiments, not
routine defaults.

Concurrent-agent cap: 5 total, including the HELM.

## Gated-event carve-out

This record controls no gated event. It cannot select or waive: GOV-2's two
Codex events (upstream material-packet review, exact-corrected-head
confirmation), PRD-242 second-model commissioning, the CI literals in
`tools/validate_prd_registry.py`, or the CLASS/LANE matrix. Changing which model
fills a seat never changes that seat's authority.

## Precedence

Authority flows only from `CLAUDE.md` and the canonical docs it references. This
file describes, never authorizes; on any conflict it is the record that is wrong
and is corrected.
