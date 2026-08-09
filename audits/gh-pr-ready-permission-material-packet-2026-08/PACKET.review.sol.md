# gh-pr-ready permission MATERIAL packet -- independent review + exact-head confirmation (Sol)

Independent second-model MATERIAL-packet review and exact-corrected-head
confirmation for the agent PR-ready permission change (branch
`governance/allow-gh-pr-ready-draft-transition`, PR #234).

Reviewer: GPT-5.6 **Sol** (`gpt-5.6-sol`), invoked `codex exec -s read-only
-m gpt-5.6-sol -c model_reasoning_effort=xhigh` (sandboxed read-only, prompt via
stdin, verdict from stdout). Sol is the standing default independent second-model
reviewer for MATERIAL packet reviews (owner model-utilization ruling
2026-08-08). Fresh context; not the packet author. Artifact written by Claude
Code from captured stdout; Sol wrote nothing into the repo (self-reported
"read-only; no repository writes").

## 1. Packet review -- reviewed head `e6a767e`
**VERDICT: ACCEPT-WITH-REQUIRED-CORRECTIONS.**

REQUIRED CORRECTIONS (all three applied in the single consolidated cycle):
1. Negative-boundary overclaim. `Bash(gh pr *)` (settings.local.json) already
   permits `gh pr edit` (title/body/base) and `gh pr close`/`reopen` with no
   matching deny; the `gh api` denies do not gate those. The packet's
   "title/body owner/UI-only" framing was inaccurate. Corrected: title/body via
   `gh api` PATCH stays denied; `gh pr edit`/`close`/`reopen` are a pre-existing
   local authorization unchanged by this proposal (recorded, out of scope for
   this one-line packet).
2. Glob breadth + one-way vs bidirectional. `Bash(gh pr ready*)` is an
   arbitrary-suffix matcher; `gh pr ready` (gh 2.46.0) exposes only ready<->draft
   via `--undo` (no merge/close/base). Corrected: sections 4 and 6 now describe
   the bidirectional transition, include `--undo`, and dispose of the glob
   breadth.
3. Head reference. `66c2b27` is the settings-change commit/parent, not the
   packet head. Corrected: labeled as the change commit; no self-referential
   head claim.

VERIFIED by Sol (unchanged): current boundary (gh pr ready denied;
`Bash(gh pr *)` allowed; deny-over-allow precedence; merge + api denies
separate); the settings change is exactly 1 deletion / 0 insertions (deny 80 ->
79, valid JSON); the negative diff leaves merge, all gh-api mutation denies, and
the checkout/switch/restore/reset/rebase/worktree/force-push denies
byte-unchanged; `gh pr ready` performs only ready<->draft; MATERIAL + STANDARD
classification repository-consistent.

## 2. Consolidated correction -- corrected head `79315e8`
Single GOV-1 correction cycle: only `PACKET.md` changed (the three corrections
above); the settings.json change is untouched (still one deleted deny line).

## 3. Exact-corrected-head confirmation -- confirmed head `79315e8`
**VERDICT: CONFIRMED** -- corrected head addresses the required corrections;
GOV-2 review-clean for the owner design-direction ruling. Sol confirmed:
correction 1 (pre-existing gh pr edit/close/reopen recorded; denial limited to
gh api PATCH), correction 2 (bidirectional draft<->ready + `--undo` + glob
breadth), correction 3 (head reference corrected); no new material problem; the
correction changed only `PACKET.md`; settings remains exactly one deleted deny
line.

## Disposition
GOV-2 upstream sequence complete for this MATERIAL packet: independent Sol review
+ one consolidated correction + exact-corrected-head confirmation. Per the owner
ruling the change now returns for the **design-direction ruling**. This artifact
authorizes nothing downstream: no PRD allocated, no Gate A, PR #234 not merged.

Note surfaced by the review (out of scope here, for owner awareness): the
pre-existing `Bash(gh pr *)` local allow grants `gh pr edit`/`close`/`reopen`
with no matching deny -- a broader standing agent capability than the
merge-boundary discussion assumed. Tightening it is a separate decision, not
bundled into this one-line packet.
