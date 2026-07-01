# RECON — PRD-212 review stand-in (audit finding 1) — two load-bearing facts

**Type:** READ-ONLY recon. Establishes facts; resolves nothing. Every fix waits on Dustin's call.
**Date:** 2026-07-01. **Branch:** `claude/prd-212-audit-recon-ywlso0`.
**Scope of evidence:** in-tree docs @ `c38edf7`, git history, and the live GitHub Actions
run records for `codex-review.yml` (artifacts win over framing).

Audit finding 1 asks whether the two legs DECISIONS.md:108-109 credits as standing in for
PRD-212's waived HIGH-RISK Codex cross-review actually exist:
> "the Codex leg is waived under the PRD-207 bootstrap precedent (Claude review
> + the recorded Phase-4 live validation stand in)."

---

## FACT 1 — Did a PRD-212 Claude review actually happen? → **(b) No evidence anywhere.**

A negative can't be fully proven, but the absence is total across every surface a review
would leave a mark on:

- **No filed artifact.** `docs/prd_history/` has **no `PRD-212.review.claude.md`**
  (`ls docs/prd_history/ | grep 212` → only `PRD-212.md`). The `prd-review-claude` skill
  writes exactly that path; it is absent.
- **No review commit.** The full PRD-212 commit set is: `0e1c6e9` (Stage-0 scaffold),
  `daedf10` (implementation), `39811bf` (merge), `bb05721`/`c38edf7` (bookkeeping). None
  adds a review artifact or a review body.
- **No implementation PR to carry a review.** `search_pull_requests PRD-212` returns
  **one** PR — **#74**, the *bookkeeping/closeout* PR ("Close PRD-210/211/212 …"), merged
  2026-07-01 20:35. The **implementation** landed via a direct manual merge
  (`39811bf` "Merge remote-tracking branch 'origin/claude/prd-212-pin-codex-identity'"),
  so there is no implementation-PR review thread either.
- **The only trace of a "Claude review" is self-referential prose.** The claim lives in
  `docs/prd_history/PRD-212.md:99-100` and `docs/DECISIONS.md:108-109` — and
  `git blame` shows DECISIONS:106-113 was authored **in the implementation commit itself**
  (`daedf108`, "Claude", 2026-06-30 22:11:27). The assertion and the code it "reviews" are
  the same commit, by the same author. That is not an independent review; it is the
  author asserting one occurred.

**Verdict:** No durable, independent PRD-212 Claude-review artifact exists — not filed, not
committed, not in a PR. The "Claude review" leg rests entirely on prose written into the
implementation commit. (If it refers to in-chat project-lead review, that is by CLAUDE.md a
different actor than Claude Code and left no artifact — it does not satisfy a HIGH-RISK
independent review gate, which requires a durable in-tree artifact.)

---

## FACT 2 — What did Phase-4 show, and is the gate serving a real model NOW?

### The pivotal divergence: Phase-4 RAN and FAILED — the repo never recorded it.

Every in-tree doc frames Phase-4 as a *deferred, not-yet-run* greenlight
(`PRD-212.md:75-78,93`; `DECISIONS.md:99-100,112-113`; `PROJECT_STATE.md:24-25`). A repo-only
sweep concludes "Phase-4 has not run." **The live GitHub Actions record contradicts this.**

Phase-4 requires the pinned workflow on the default branch, then a `workflow_dispatch`.
After the merge, `codex-review.yml` shows **four dispatches on 2026-07-01, all on `main`
@ `39811bf`, all `completed failure`:**

| Run ID | Time (UTC) | review job | resolve job | Meaning |
|---|---|---|---|---|
| 28493181615 | 04:18 | **fail @ checkout** | skipped | infra (SHA checkout), no gate signal |
| 28493756030 | 04:34 | (fail) | — | infra-class |
| 28495500328 | 05:22 | success | **FAIL-CLOSED(4)** | codex ran; honor gate rejected fallback |
| 28495627204 | 05:25 | success | **FAIL-CLOSED(4)** | codex ran; honor gate rejected fallback |

The two runs where Codex actually executed (05:22, 05:25) both fail-closed with the
**identical** message the pin was meant to eliminate. Resolve job `84461372664` (run
28495627204), env `ALLOWED_CODEX_MODELS=gpt-5-codex`, `MODEL=gpt-5-codex`:

```
FAIL-CLOSED(4): codex model-metadata fallback: requested 'gpt-5-codex' not served:
Model metadata for `gpt-5-codex` not found. Defaulting to fallback metadata;
this can degrade performance and cause issues.
```

`land` skipped; **no artifact landed** (no new `codex-review/PRD-212-*` or post-pin
`codex-review/PRD-208-*` branch exists on the remote).

### (a) What Phase-4 demonstrated → it **FALSIFIED** PRD-212's premise.

PRD-212's premise (`PRD-212.md:40-47`, FAIL line `:80-85`): pinning `codex-version: 0.142.1`
freezes the alias so `gpt-5-codex` resolves to real metadata and the honor gate certifies
"honored." Phase-4 shows the opposite: **under the pinned 0.142.1 on `main`, `gpt-5-codex`
STILL falls back** — exit 4, no artifact. The CLI pin does not (cannot) freeze *server-side*
alias resolution; the "After" state the PRD promised never materialized. The user's read is
correct.

### (b) Is DECISIONS:108-109's crediting of "Phase-4 live validation" coherent? → **NO — incoherent on two counts.**

1. **Temporally impossible as written.** DECISIONS:109 ("the recorded Phase-4 live
   validation stand in") was authored `daedf108` @ 2026-06-30 22:11 — on the feature branch,
   *before* the pin was on `main` and *before* any Phase-4 dispatch existed (the real ones
   are 2026-07-01). At write-time there was **no recorded Phase-4 validation** to stand in.
2. **The result, once it ran, refutes the claim.** When Phase-4 did run it fail-closed —
   so the entry credits as *positive stand-in assurance* the very run that *falsified* the
   premise. It is also internally self-contradictory: the same DECISIONS entry, lines
   112-113, states "Live confirmation is Phase 4, a separate greenlight; PRD-208 stays
   parked until then" — i.e. admits Phase-4 had **not** confirmed, two lines below crediting
   it as a stand-in.

**Verdict:** DECISIONS:108-109 cites a validation that (at authorship) did not exist and (once
executed) returned the failing result. It is not coherent positive assurance.

### (c) DOWNSTREAM — is a HIGH-RISK Codex leg satisfiable RIGHT NOW? → **NO. Still fails closed.**

As of the latest evidence (run 28495627204, 2026-07-01 05:27), the account is served a
**fallback model, not an allowlisted `gpt-5-codex`.** PRD-207's honor gate correctly rejects
it (exit 4, no artifact). Therefore **no HIGH-RISK Codex cross-review can be produced today**
— the gate outage PRD-212 set out to end is **still open**. PRD-212's fix is necessary-but-
insufficient: it pinned the CLI, but the fallback is decided server-side, downstream of the
pin.

> Divergence to flag: `PROJECT_STATE.md:25` says PRD-208 is "now potentially unblockable
> since PRD-212 repaired the gate." The 2026-07-01 Phase-4 failures falsify "repaired" — the
> gate is not repaired for the purpose of serving `gpt-5-codex`.

---

## PRD-208 determination → **STILL BLOCKED / parked. PRD-212 did NOT unblock it.**

PRD-208's HIGH-RISK Codex leg remains UNSATISFIED. It can only be satisfied by an allowlisted
`gpt-5-codex` review artifact; the gate cannot currently produce one (fallback → fail-closed).
Reviving PRD-208 remains blocked on a *working* Codex identity, which PRD-212's CLI pin did
not deliver. PRD-208 stays parked — not for lack of a dispatch, but because the dispatch path
still fails closed.

---

## The decisions this leaves Dustin (recon resolves none of them)

1. **Finding 1 stands.** No independent PRD-212 Claude-review artifact exists, and the
   Phase-4 leg it was paired with failed. The HIGH-RISK waiver for PRD-212 rests on two legs,
   **both** of which are now shown empty/failing. Decision: how to remediate the waiver
   (file a retroactive review? corrective PRD? accept-and-annotate?).
2. **DECISIONS:108-113 is factually stale/incoherent** and records a falsified premise as
   assurance. Decision: correct the record (and PROJECT_STATE:24-25's "repaired"/"unblockable"
   claims) — a bookkeeping/DECISIONS edit, human-held.
3. **The Codex gate outage is NOT resolved.** `gpt-5-codex` still falls back under 0.142.1.
   Decision: whether PRD-212 should be reopened / superseded (the fix targeted the wrong
   layer — CLI pin vs. server-side alias), and what the real fix is (a served-model the
   provider still honors, or a different allowlisted identity).
4. **PRD-208 revive stays parked** until (3) is genuinely fixed and a Phase-4 dispatch
   certifies honored. It is not unblockable today.

*No source, contract, `main`, DECISIONS, registry, or PRD file was mutated by this recon.*
