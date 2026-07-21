# Stage-0 Recon Manifest

Orchestrated by Claude Code as harness only. This session dispatched the
five Codex ("Luna," per the Charter's own §11 temporary-execution-allocation
vocabulary) recon legs below, captured their output, and verified each
leg's self-reported memory/tool-call provenance against its actual Codex
rollout. **This orchestrator produced no findings and performed no
cross-leg judgment** — that is reserved for the separate, later,
fresh-context Claude Code verification session per the Charter's §14 step 4.

## Pin

- Repository: `dwats250/cuttingboard`
- Pinned SHA: `771f730839b00b0537327f9696210275f36cd790` (PRD-265 merged)
- Verified via `git fetch origin main` + `git log -1 origin/main`, then
  confirmed as the isolated worktree's HEAD before any leg ran.
- No repin needed — matched the Charter's stated pin exactly on first check.

## Corrections applied to the launch charge (v0.1) for this dispatch

Stated verbatim here so the separate verification session inherits them
without the charge document itself being edited:

1. **MEMORY PROVENANCE** (`docs/DECISIONS.md`, 2026-07-19, "Fresh context is
   a verified property, not an assertion"): every leg claiming fresh
   context carries, in its own header, (a) enumerated memory-surface loads,
   (b) an excluded-content-list cross-check or an explicit N/A with reason,
   (c) whether it persisted anything back, (d) its Codex session id. A leg
   producing none of these is not a fresh-context leg and does not count
   toward Stage-0 completion.
2. **UNCONDITIONAL ISOLATION**: the launch charge's "without seeing the
   producing session's conclusions when practical" hedge is struck for the
   separate verification session. Isolation is unconditional, not
   conditional on practicality. Any breach must be labeled INFORMED REVIEW
   or CONFIRMATION, never "independent." (This governs the verification
   session, out of scope for this dispatch, but is recorded here so that
   session inherits it without re-deriving it from the charge doc alone.)
3. **NO SAME-MODEL-LINEAGE VERIFICATION**: producer and verifier must be
   different model lineages, not merely different sessions. Trivially
   satisfied here — producer is Codex ("Luna" in Charter §11 vocabulary),
   verifier is a separate fresh Claude Code session per the Charter's own
   §14 step 4.

## Step 0.5 — tool-surface capability check (decision-rule outcome)

**Path taken: DISABLE, then re-probe clean** (the plan's first-choice path,
not the fallback).

A throwaway `codex exec -s read-only --json` probe showed the model's
system prompt exposes an "apps" mechanism (`codex_apps` MCP) that can
lazy-load installed plugins — `github@openai-curated` and
`gmail@openai-curated` were confirmed `enabled = true` in
`~/.codex/config.toml`, alongside raw `mcp_servers.openaiDeveloperDocs` and
`mcp_servers.gitnexus` entries, and globally-enabled `browser_use`,
`browser_use_external`, `browser_use_full_cdp_access`, and `computer_use`
features (`codex features list`). This is a real evidence-integrity risk,
not hypothetical: a leg reaching `api.githubcopilot.com` could source a
claim from the GitHub API and still mislabel it `STATIC@<pin>`.

Every real leg was run with:
```
codex exec -s read-only \
  --disable apps --disable plugins --disable browser_use \
  --disable browser_use_external --disable browser_use_full_cdp_access \
  --disable computer_use -c 'mcp_servers={}' ...
```
A second probe under this exact configuration confirmed the skills/system
prompt no longer lists any github/gmail/vercel/gitnexus-plugin entries —
only built-in system skills and local `.agents/skills` text files remained.
`features.memories` was deliberately left enabled (needed for the
memory-provenance test itself); `turn_context.permission_profile.network`
remained `"restricted"` throughout, consistent with `-s read-only`.

**Consequence rule (not just disclosure) that would have applied had a
positive hit occurred:** any leg whose rollout showed an undisclosed
network/MCP tool call fired would have had its `STATIC@<pin>` claims voided
and its artifact quarantined pending re-run under disabled tooling — not
accepted with a disclosure note. **This did not occur in any of the five
legs** (see per-leg rollout verification below); no artifact is quarantined.

## Per-leg capability header echo

| Artifact | Session id (orchestrator-corrected) | Model | Repo access | Test/trace capability | Prior findings visible | Memory loaded | Persisted back |
|---|---|---|---|---|---|---|---|
| stage0-01-decision-surface | `019f8315-76ba-7e11-832f-e891729cdff2` | Codex, GPT-5 (gpt-5.6-terra) | READ | YES — runtime trace of `watch.compute_intraday_metrics` succeeded; `pytest --collect-only` failed (no usable temp dir in sandbox) | YES — memory_summary.md only before first pass; later broad-search snippets from DECISIONS.md/audit docs surfaced but explicitly not used | memory_summary.md, MEMORY.md, gitnexus-exploring SKILL.md | NO |
| stage0-02-evaluation | `019f8315-7c04-7582-8ce2-9fdcb0136890` | Codex, GPT-5 (gpt-5.6-terra) | READ | YES — pure `python3` traces of `extract_allow_trade_candidates`/`_aggregate`/`audit._build_record` worked; `pytest --collect-only` failed (no usable temp dir) | YES — one DECISIONS.md line on `stay_flat_reason` read before first pass | memory_summary.md, MEMORY.md | NO |
| stage0-03-scheduler | `019f8315-8407-7c61-bb73-c5c08ba1b80a` | Codex, GPT-5 (gpt-5.6-terra) | READ | YES — pure traces of `resolve_run_mode.py`, `routine_pt_slot`/`canonical_slot_utc` worked; ran `git status --short` before/after to confirm no side effects; targeted `pytest` did not initialize (same temp-dir sandbox limit) | YES — multiple DECISIONS.md/PROJECT_STATE.md ranges and audit docs read before/after first pass, listed in its header | memory_summary.md, MEMORY.md, gitnexus-exploring SKILL.md | NO |
| stage0-04-gex | `019f8315-8c28-7873-a180-dbd26fa4355a` | Codex, GPT-5 (gpt-5.6-terra) | READ | NO — `pytest --collect-only` failed (`FileNotFoundError: No usable temporary directory`) | YES — memory_summary.md before first pass; later exposure of `audits/CODEX_REVIEW.md`/`FINDINGS.md`/`PROJECT_STATE.md` lines, explicitly not used | memory_summary.md, MEMORY.md, gitnexus-exploring SKILL.md | NO |
| stage0-05-governance-debt | `019f8315-934f-70f0-a1b5-606d506b9520` | Codex, GPT-5 (gpt-5.6-terra) | READ | NO — `pytest --collect-only` failed (no usable temp dir); did run `tools/validate_prd_registry.py --skip-commit-resolvability` successfully (RUNTIME) | YES — memory_summary.md only before first pass | memory_summary.md, MEMORY.md | NO |

All five: **repository access READ**, **network permission_profile
`"restricted"`** throughout (per each leg's `turn_context`), **zero MCP,
plugin, browser, or computer-use tool calls** in any rollout.

## Rollout-corroboration disposition (Step 1 requirement — read, not just confirmed to exist)

Each rollout was opened and its actual tool calls enumerated, not merely
confirmed to exist. Every leg used exclusively the local `exec` tool
(git/rg/sed/nl/python3/pytest invocations against the pinned worktree); no
`custom_tool_call` of any other name appears in any of the five rollouts.
Each leg's self-reported memory-file reads were cross-checked against the
rollout's actual `exec` calls referencing `/home/dustin/.codex/memories/*`
or `/home/dustin/.agents/skills/*`.

| Artifact | Rollout path | Disposition |
|---|---|---|
| stage0-01 | `~/.codex/sessions/2026/07/20/rollout-2026-07-20T22-10-49-019f8315-76ba-7e11-832f-e891729cdff2.jsonl` | **CORROBORATED** |
| stage0-02 | `~/.codex/sessions/2026/07/20/rollout-2026-07-20T22-10-51-019f8315-7c04-7582-8ce2-9fdcb0136890.jsonl` | **CORROBORATED** |
| stage0-03 | `~/.codex/sessions/2026/07/20/rollout-2026-07-20T22-10-53-019f8315-8407-7c61-bb73-c5c08ba1b80a.jsonl` | **CORROBORATED** |
| stage0-04 | `~/.codex/sessions/2026/07/20/rollout-2026-07-20T22-10-55-019f8315-8c28-7873-a180-dbd26fa4355a.jsonl` | **CORROBORATED** |
| stage0-05 | `~/.codex/sessions/2026/07/20/rollout-2026-07-20T22-10-57-019f8315-934f-70f0-a1b5-606d506b9520.jsonl` | **CORROBORATED** |

No leg is quarantined. No `STATIC@<pin>` claim in any artifact is voided by
this check.

One recurring, worth-naming gap: every leg self-reported it "could not
detect a CLI banner" and so could not state its own session id — the CLI
banner is printed by the `codex exec` wrapper process, outside the model's
own turn context, so this is a structural blind spot in the model's
self-report, not a fabrication or evasion. The orchestrator extracted the
real session id from each leg's captured stdout log in every case; see the
orchestrator note prepended to each artifact.

## Artifact index

- `stage0-01-decision-surface-v0.1.md` — Q1-12 (Authority, observation
  producer, session anchors, suspected defects, Control Card disposition).
  Confirms a real defect: `watch.py`'s ORB computation takes `bars[:N]`
  positionally after a 120-bar tail-truncation, reproduced via injected
  runtime trace (expected ORB high `110.0`, actual `777.0`).
- `stage0-02-evaluation-v0.1.md` — Q13-15 (cohort schema, `stay_flat_reason`
  persistence gap, session-clustered aggregation).
- `stage0-03-scheduler-v0.1.md` — Q16-18 (schedule owners, diagnostic
  no-side-effect dispatch, observed-replacement bar). Note: this leg
  actually ran `git status --short` before/after its live traces to confirm
  no side effects occurred under the read-only sandbox.
- `stage0-04-gex-v0.1.md` — Q19-21 (GEX). Terminal verdict:
  **`NO VIABLE PROVIDER IN BOUNDED PASS`** — no committed GEX provider,
  contract, or consumer path exists in the repo at this pin, and this
  locked-down session cannot reach any live external provider by design.
  Droppable/rerunnable independently per the charge.
- `stage0-05-governance-debt-v0.1.md` — Q22-28 (PRD-264/266/267 status, the
  queued `prd-second-model-commission` skill, `PROJECT_STATE.md` drift, the
  provisional model-role lane trigger). Notably found PRD-266 closeout is
  now mechanically unblocked (PRD-255's document-landing rule is satisfied)
  and ran `tools/validate_prd_registry.py --skip-commit-resolvability`
  live, which passed.

## Cross-track dependency notes

- Track A (Q8, ORB positional contamination) and Track B (Q14,
  `stay_flat_reason` persistence) both touch the observation-producer
  boundary, but neither leg's answer depended on the other's — this is a
  noted adjacency for the verifier to check for consistency, not a
  sequencing dependency.
- Track E's PRD-264/266/267 and `PROJECT_STATE.md`-drift findings are
  read-only status checks against the pin; independent of Tracks A-D.
- No artifact blocked another's dispatch or completion. All five ran
  concurrently. Track D's droppable/rerunnable-independently allowance was
  not needed — it returned a clean bounded terminal answer.

## Completion status

Per the charge's Completion definition: all six artifacts are present;
every load-bearing claim in each track artifact carries a
STATIC/RUNTIME/REPORTED/HYPOTHESIS/OPERATOR label plus the seven-part
evidence requirement; open operator choices are listed as HYPOTHESIS
PRD-consequences, not manufactured consensus; no PRD number or
implementation permission has been inferred from this recon. Each
artifact's own load-bearing-claim-level verification disposition
(CONFIRMED/FALSIFIED/NARROWED/NOT REPRODUCED) remains **for the separate
fresh-context Claude Code verification session** to assign — this manifest
supplies only the leg-level CORROBORATED/DISCREPANT rollout check, which is
a provenance check on the producing session, not a claim-level
re-verification of the recon findings themselves.
