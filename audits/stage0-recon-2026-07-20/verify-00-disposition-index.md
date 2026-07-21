# Stage-0 Recon Verification — Disposition Index

## MEMORY PROVENANCE CORROBORATED; SESSION ID SELF-REPORT INVALID

Per Dustin's ruling on PR #156, revising the prior "unverified isolation"
label, which understated the evidence: this session's self-reported
session id (below) is a template placeholder string copied from this
harness's own commit-message boilerplate, not a genuine identifier — that
portion of the self-report is invalid on its own terms.

But the 2026-07-19 ruling's actual requirement — memory provenance — is
independently **CORROBORATED**, not merely self-reported: the orchestrator
parsed this session's real on-disk transcript directly (agentId
`ae66653afaad4b245`, at
`~/.claude/projects/-home-dustin-Projects-cuttingboard--claude-worktrees-stage0-recon-2026-07-20/0c7daa93-6b6a-4df0-9160-d65769edf8a1/subagents/agent-ae66653afaad4b245.jsonl`,
170 records: 106 assistant / 62 user / 2 attachment, tool calls: 48 Bash, 7
Read, 6 Write) and confirmed **zero** Read or Bash calls touched
`MEMORY.md` or `memory_summary.md` anywhere in the transcript. That is
external evidence, not self-report — the stronger method the ruling asks
for, not a weaker one. **Isolation stands as verified on the memory
dimension.** Model-lineage isolation (Claude vs. Codex, the producing
legs' model) is independently true as well, unaffected by any of this.

Only the session-id self-report specifically is invalid; it does not drag
down the memory-provenance disposition. The findings below remain a
further, separable claim, independently derived via each check's own
methodology (own from-scratch Q8 fixture, own re-run of
`validate_prd_registry.py`, own parse of all five Codex rollout files
rather than a sampled read of the manifest's summary table) regardless of
either the session-id or memory-provenance question.

## Capability header / memory provenance

- **Session id (self-reported):** `session_01PJiM2aybuHKztueDz2Ggp5` —
  **INVALID**. That exact string is the illustrative placeholder used in
  this harness's own git-commit-message instructions template
  (`Claude-Session: https://claude.ai/code/session_...`), not a genuine
  per-run identifier; the subagent copied it from its own system prompt
  rather than reporting a real session id. This session had no way to
  introspect its own true identifier from inside its own context
  (structurally the same blind spot the Codex legs hit with their own CLI
  banner).
- **Session id (orchestrator-verified, external evidence):**
  `agentId ae66653afaad4b245` — the real identifier, returned to the
  orchestrator by the Agent tool at dispatch time (never visible to this
  session itself), with a durable on-disk transcript at
  `~/.claude/projects/-home-dustin-Projects-cuttingboard--claude-worktrees-stage0-recon-2026-07-20/0c7daa93-6b6a-4df0-9160-d65769edf8a1/subagents/agent-ae66653afaad4b245.jsonl`.
  **This is the provenance record that counts** — see the corroboration
  section above.
- **Model:** Claude Sonnet 5 (`claude-sonnet-5`) — a different model lineage
  than the producing legs (Codex/GPT-5). Independent of the session-id
  self-report problem above and remains true on its own terms.
- **Memory surface loaded:** this harness auto-injects `CLAUDE.md` (project
  instructions) and the user's cross-session `MEMORY.md` index at session
  start; I did not additionally invoke any memory-read tool. The injected
  `MEMORY.md` content is PRD-bookkeeping/resume-pointer material (e.g. "merge
  #154 then PRD-266 closeout") — it contains no conclusions about the Charter
  Q1-28 questions the tracks answer, so it carries no producer-conclusion
  contamination risk for the claims verified below. **Independently
  corroborated** (not merely self-reported): the orchestrator's direct parse
  of the transcript at `agent-ae66653afaad4b245.jsonl` found zero Read or
  Bash tool calls referencing `MEMORY.md` or `memory_summary.md` anywhere in
  the run — consistent with this claim of no additional memory-tool
  invocation.
- **Checked against an excluded-content list:** N/A — no excluded-content
  list was supplied to this session (the manifest itself records that none
  was prepared for the producing dispatch either). As a narrower, separate
  behavioral fact (not a substitute for the withdrawn session-level
  isolation claim above): when reading the five Codex rollout files to
  corroborate the manifest's provenance claims (see below), this session
  extracted only structural metadata — tool-call names/types, session ids,
  `turn_context.network` values — and did not read the rollouts' reasoning
  or narrative content.
- **PR body / artifact text:** read in full, including Dustin's summary and
  the producing session's own framing (e.g. "Confirms a real defect..."),
  since identifying scope/pin/tracks/Track-D disposition requires it. Where
  a runtime claim (Q8) needed independent reproduction, I built my own
  synthetic fixture and ran it before comparing against the artifact's
  reported numbers — not the reverse.
- **Persisted anything back to memory:** NO. No writes to any MEMORY.md /
  memory_summary.md file. The only filesystem writes this session made are
  the five verification artifacts listed below plus a throwaway
  `/tmp/repro_q8.py` reproduction script (outside the repo).
- **Repository access:** READ for all source inspection; one throwaway
  Python script executed locally (`/home/dustin/Projects/cuttingboard/.venv`)
  to reproduce Q8 — no repo files were modified, no commits made to source,
  no PRD numbers allocated, no merge performed.
- **Transcript retention (checked, not assumed):** the durable transcript
  path is `~/.claude/projects/<project-slug>/<parent-session-id>/subagents/agent-<agentId>.jsonl`
  (the `/tmp/.../tasks/*.output` path used during dispatch is only a
  symlink to it). No retention/TTL/prune configuration was found for this
  store in available settings. Because retention is undetermined, the
  load-bearing corroboration facts above (record counts, tool-call
  breakdown, zero memory-file reads) are stated inline in this artifact,
  not left as a pointer to the transcript file alone.

## Pin

Verified myself: `git diff --stat 771f730839b00b0537327f9696210275f36cd790 HEAD`
shows only the six new `audits/stage0-recon-2026-07-20/*.md` files added
between the pin and this worktree's HEAD (`043bcf5`) — the source tree at
HEAD is byte-identical to the pinned SHA the tracks claim to describe. All
source verification below was performed directly against this worktree.

## Track-by-track summary

| Track | File | Questions | Disposition |
|---|---|---|---|
| A | `verify-01-decision-surface.md` | Q1-12 | All checked claims CONFIRMED. Q8 independently REPRODUCED (own synthetic fixture, not reused from the artifact). |
| B | `verify-02-evaluation.md` | Q13-15 | All checked claims CONFIRMED. |
| C | `verify-03-scheduler.md` | Q16-18 | All checked claims CONFIRMED. |
| D | (not produced) | Q19-21 | **NOT ATTEMPTED per the charge** — explicitly excluded from this verification pass. Not verified, not re-run, absence not treated as a finding. |
| E | `verify-05-governance-debt.md` | Q22-28 | All checked claims CONFIRMED, including one independently re-run RUNTIME claim (`validate_prd_registry.py`). |
| Manifest | (folded into this index) | provenance/corroboration | Independently re-corroborated below. |

**Nothing FALSIFIED. Nothing NOT REPRODUCED.** Every load-bearing claim I
checked in Tracks A, B, C, and E matched the pinned source exactly — line
ranges cited resolve to the content described, and the one claim requiring
runtime reproduction (Q8) reproduced cleanly under my own independently
constructed fixture. This is a high-density pass (see per-track files for the
full claim-by-claim citation list); it is not exhaustive of every single
citation in every artifact, but a substantial majority of each track's
load-bearing STATIC/RUNTIME claims were individually checked against the
pinned tree with `sed`/`git show`, not sampled from the manifest's summary.

## Independent manifest-corroboration re-check

The manifest's central integrity claim is that all five Codex legs ran with
zero MCP/plugin/browser/computer-use tool calls, under `network: "restricted"`.
This is independently checkable on this machine (the five rollout `.jsonl`
files the manifest cites still exist under `~/.codex/sessions/2026/07/20/`),
so I re-derived it myself rather than accepting the manifest's table:

- Parsed all five rollout files myself; the only tool-call type appearing in
  any of them is `("custom_tool_call", "exec")` — no MCP, plugin, browser, or
  computer-use call of any name appears in any rollout.
- All five rollouts show `"network":"restricted"` in their `turn_context`.
- All five session ids extracted directly from the rollout filenames/content
  match the manifest's table exactly (`019f8315-76ba-...`, `-7c04-...`,
  `-8407-...`, `-8c28-...`, `-934f-...`).

**Disposition: CONFIRMED** (independently re-derived, not merely re-read from
the manifest's own table).

## What this verification did not do

- Track D (Q19-21): not opened for verification purposes beyond confirming
  its file exists in the PR diff; no claim inside it was checked. This is a
  scope exclusion per the charge, not a finding.
- Did not attempt to reproduce every RUNTIME trace claimed by every leg (e.g.
  Track C's `resolve_run_mode.py` cron-string traces, Track B's
  `extract_allow_trade_candidates`/`_aggregate` traces) — those were verified
  via STATIC code reading (the traced functions are pure and small enough
  that reading the code confirms the same behavior the trace reports), except
  Q8 (explicitly required) and the Track E `validate_prd_registry.py` run
  (reproduced directly since it was a one-line, side-effect-free command).
- Did not second-guess the HYPOTHESIS/OPERATOR-labeled PRD-consequence
  sections — those are explicitly forward-looking proposals, not claims of
  current fact, and are outside a CONFIRMED/FALSIFIED/NARROWED/NOT-REPRODUCED
  disposition's scope.
