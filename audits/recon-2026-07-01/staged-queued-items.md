# Recon & staging — three queued/parked items (2026-07-01)

**Pass type:** RECON-AND-STAGE. No mutation of `main`, no PR close, no DECISIONS
entry, no registry/index flip, no merge. Every actionable is staged behind
Dustin's explicit approval. Artifacts win over framing; divergences flagged inline.

**Base:** `main` @ `f0e365c` (PR #74 merged). Branch: `claude/unfinished-work-review-jgaqyw`.

**Out of scope:** the PRD-208 revive (separate staged work) — not touched.

---

## Item 1 — PR #51 (PRD-205 codex-review-router scaffold)

### What PR #51 actually is
- Open since **2026-06-22**, **untouched since** (`updated_at` unchanged → no comments/reviews/pushes since creation). Head `claude/codex-review-router-prd205` @ `33096b8`; base `main` @ `35e0641` (now far behind `f0e365c`). `mergeable_state: unknown`.
- **Doc-only Stage-0 scaffold**: 5 files, +320/−2 — `PRD-205.md`, `PRD-205.review.claude.md`, and registry/index/state rows. **No `scripts/codex_review.sh`, no tests.** The PR body says so explicitly ("the `codex-review` wrapper itself is **not built** here … ships no executable behavior change") and marks itself "hold for human merge — not auto-merged."
- What it *proposed*: a `codex-review <target>` command that capability-routes a read-only Codex review — host `codex exec -s read-only` with egress fallback, else PRD-197 GitHub Actions dispatch + poll — to retire the host-dependence hazard (in-container `codex exec` → `host_not_allowed`).

### Divergence (artifacts win) — the PRD-205 number is VOID
- **Registry** (`docs/PRD_REGISTRY.md:225`): `PRD-205 | — | (void — number skipped; 207/210 filed out of order) | DEPRECATED | —`.
- **Index** (`docs/prd_index.json`): `205 → status DEPRECATED, commit null`.
- **DECISIONS.md 2026-06-29** ("Numbering-gap convention", line 103): *"PRD-205/206 were never authored; 207 and 210 were filed out-of-order into the gap … Recorded as DEPRECATED void placeholders."*
- Timeline: PR #51 opened 2026-06-22 → the void-fill decision landed 2026-06-29 (at PRD-207 closeout), **reclaiming 205 as an official void placeholder a week after #51 was opened.** PR #51's `PRD-205` identity is therefore **orphaned**: it cannot land as "PRD-205" (the number is void), and its branch is based on pre-void `main`, so a merge today would collide with the void row.

### What the router work *became* (traced, not assumed)
- **It was never built.** No `codex_review.sh` / router command exists on `main` (`scripts/` has no such entry; no non-doc match for a routing wrapper).
- The Codex-review **capability** is delivered by a different line of work: `.github/workflows/codex-review.yml` (**PRD-197**, dispatch → review → resolve → land-to-`codex-review/*` branch), hardened by **PRD-207** (served-model honor gate, fail-closed) and **PRD-212** (codex-cli `0.142.1` pin). Route **selection** between host and CI is still **human-chosen per CLAUDE.md doctrine** (`codex exec -s read-only - < prompt` on host; the CI workflow otherwise).
- So the router's *concept* — auto-select the route in tooling — is **UNBUILT and UNCLAIMED**. Nothing supersedes the capability; only the *number* was superseded.

### Verdict
**Two-part, and they differ** (per instruction: "if NOT cleanly superseded, tell me what's still live"):
1. The PR's **deliverable** (a PRD-205 scaffold) is **cleanly orphaned** by the number-voiding — safe to close.
2. The router **capability** it proposed is **still live/unbuilt** — closing #51 abandons the idea unless it is refiled under a live number (`next_prd` = **213**).

### STAGED — draft close comment (NOT posted; do not close)
> Closing as orphaned. The `PRD-205` number this PR claims was **void-filled** at the
> PRD-207 closeout (DECISIONS.md 2026-06-29 "Numbering-gap convention"; `PRD_REGISTRY.md:225`
> and `prd_index.json` both record `PRD-205 → DEPRECATED, "void — number skipped"`). This PR
> is a doc-only Stage-0 scaffold (no `codex_review.sh`, no tests) on a pre-void `main` base,
> so it cannot land under this number.
>
> Note the router **capability** was never built and nothing replaced it: the Codex-review
> path today is `codex-review.yml` (PRD-197 / -207 / -212), with host-vs-CI route selection
> still chosen by CLAUDE.md doctrine rather than a tool. If the auto-routing wrapper is still
> wanted, it should be refiled as a fresh PRD under a live number (next_prd 213).

### Decision needed from Dustin (item 1)
- **(A)** Close #51 as orphaned **and drop** the router idea; or
- **(B)** Close #51 **and refile** the router as a fresh PRD under a live number (213); or
- **(C)** Keep #51 open.
- _Recon recommendation:_ **(A) or (B)** — the scaffold is unmergeable as-is either way. Pick (B) only if the in-container `host_not_allowed` hazard still bites in practice.

---

## Item 2 — PRD-187 materiality eval / PRD-188 go-no-go (2026-07-15)

### Answer: the eval is NOT wired to fire. The date is a bare note.
- `.github/workflows/macro_awareness.yml` is **`workflow_dispatch:` ONLY** — and *deliberately* so: its own header comment reads *"PRD-187: workflow_dispatch ONLY. The live cron (scheduled activation) belongs to PRD-188 … do not add a `schedule:` here."* No cron, no scheduled eval run, anywhere.
- The **2026-07-15 go/no-go is a calendar NOTE** in `PROJECT_STATE.md` only. Its origin (DECISIONS.md 2026-06-19, alignment cadence #3, finding 2) was itself a *borderline-drift remediation*: "the materiality eval had no re-evaluation date … Remediated: go/no-go date 2026-07-15 recorded in PROJECT_STATE." There is **no tracked task, no cron, no DECISIONS entry with an owner+trigger** behind it.

### Worse: the gate preconditions are essentially unstarted
PRD-188's GATE ("does not build until ALL of") stands at:
1. **Labeled corpus** — `data/macro_awareness_eval_corpus.json` has **2 cases, 0 labeled** (a scaffold; `label` empty on both). The harness `tools/macro_awareness_eval.py` *refuses to run until every case carries a ground-truth label.* ❌
2. **Threshold T** — `[T = TBD — Dustin to set; err strict.]` in PRD-188. ❌
3. **Eval result artifact** under `audits/` (FP-rate ≤ T, pinned `claude-opus-4-8`) — **none exists**. ❌
4. **Dustin's explicit go** — not given. ❌

The *tooling* exists (`macro_awareness_collector.py` + `macro_awareness_eval.py` + a 2-case corpus scaffold), but it has never been run to a recorded result, and it *can't pass* today (unlabeled 2-case corpus, no T).

### Decision needed from Dustin (item 2)
Nothing to build here without a call. To make 2026-07-15 a *real* go/no-go, someone must (manually, unscheduled): **expand + label the corpus → set threshold T → run the eval to an `audits/` artifact → decide.** So:
- **(A)** Wire it: commit to doing the corpus+T+eval work before the window (optionally track/schedule it); or
- **(B)** Treat 2026-07-15 as soft/advisory — leave PRD-188 parked, no work now; or
- **(C)** Drop the date entirely (removes the calendar note).
- _Recon recommendation:_ decide **(A) vs (B)** consciously — right now the date will silently lapse because nothing fires it, which is the worst of both (looks scheduled, isn't).

---

## Item 3 — PRD-209 (OHLCV bar-count floor), PROPOSED but HELD

### The HELD reason (from the PRD, verbatim intent)
- PRD-209 was originally the fix for recon **F08** (QQQ trend "DATA UNAVAILABLE") on a **truncated-cache premise**. That premise is **REFUTED**: F08's real cause was a *path divergence* (premarket `_run_pipeline` bypassed the PRD-174 history fallback) — **fixed by PRD-210**, not by a bar-count floor.
- The two count-blind ingestion gates PRD-209 targets **are a verified latent fail-silent hole** (PRD-198 #1), but **no real "truncation-served-as-fresh" event has ever been observed.** The PRD self-downgrades: *"the 'why now' is downgraded to 'why ever' … speculative hardening to weigh against VISION 'cuts before additions'."*
- **Trigger to build (per PRD):** a real short-frame-served-as-fresh incident is observed, **OR** a human elects to enforce PRD-198 #1 (fail-loud) proactively.

### What the floor would harden (the real latent hole)
- `cuttingboard/ingestion.py:_is_fresh_ohlcv_cache` (:147-167) validates **only the last bar's date**, no count → a short-but-recent cache is served as "fresh," not refetched within a trading day.
- `_fetch_ohlcv_from_yfinance` (:325-361) accept gate is **empty-only** (`if df.empty: raise`) → a short-but-nonempty provider response is accepted and cached.
- Floor = `OHLCV_FULL_MIN_BARS = 200` (the `sma_200` consumer need), shared by both gates; heal-on-refetch primary, loud-raise fallback.

### Cost / risk
- **HIGH-RISK** (ingestion is the decision-bearing OHLCV path). ~2 files (`ingestion.py`, `config.py`) + a **new `tests/test_ingestion.py`** (none exists today).
- A real **EDGE**: a genuinely short-history symbol (newly listed, provider ceiling < 200) must degrade to honest INSUFFICIENT_HISTORY and **not refetch-storm every slot** — needs a "short-by-nature" marker.
- An **OPEN DIAGNOSTIC QUESTION** the PRD says must be resolved *before* building (confirm QQQ's failing-slot frame was short vs closes-None), else the floor may masquerade as a fix for an incident it doesn't cover.
- Full HIGH-RISK gate (Claude + real Codex under the 0.142.1 pin) applies.

### VISION stance
- **"Cuts before additions"** (`VISION.md:55`) — before adding a feature, justify the ones already present. This is the principle in direct tension: PRD-209 is an *addition* with no observed incident justifying it.
- **"Description, not prediction"** (`VISION.md:51`) — **no conflict**; a data-integrity floor is neither a forecast nor a sidecar-with-no-consumer. So PRD-209 violates no non-goal; it is purely a *cuts-discipline* weigh.

### STAGED — both paths drafted (NEITHER recorded)

**(a) BUILD — single-concern scope** (already the PRD's shape; refined to one concern):
> **Concern:** a daily OHLCV frame with fewer closes than the largest consumer needs
> (`sma_200` ⇒ 200) is never served as fresh nor cached as complete.
> **Change:** add `config.OHLCV_FULL_MIN_BARS = 200`; both `_is_fresh_ohlcv_cache`
> (count + date, short-by-nature exception) and `_fetch_ohlcv_from_yfinance`
> (reject sub-floor download, never cache it, fail loud after retries) reference it.
> **Precondition:** resolve the OPEN DIAGNOSTIC QUESTION first (confirm-check on a failing
> slot). **Trigger justification:** electing to enforce PRD-198 #1 proactively.
> **FILES:** `M ingestion.py`, `M config.py`, `A tests/test_ingestion.py`. HIGH-RISK gate.

**(b) SHELVE — recorded reason** (draft for a DECISIONS entry, if Dustin picks shelve):
> **PRD-209 shelved (not built).** The F08 incident that motivated it was root-caused
> to a path divergence and fixed by PRD-210; the count-blind ingestion gates remain a
> *verified latent* fail-silent hole (PRD-198 #1) but **no real short-frame-served-as-fresh
> event has been observed.** Per VISION "cuts before additions," the guard is **documented,
> not built** — PRD-209 is retained as a reopen-on-incident spec. **Reopen trigger:** a real
> short-frame-served-as-fresh occurrence, or a deliberate election to enforce PRD-198 #1
> proactively. Registry row: PROPOSED → (a shelve/parked status of Dustin's choosing).

### Decision needed from Dustin (item 3)
- **(a)** Build now (proactive PRD-198 #1 enforcement) — resolve the diagnostic question, then run the HIGH-RISK lane; or
- **(b)** Shelve with the recorded reason above.
- _Recon recommendation:_ **(b) shelve** unless proactive hardening is explicitly wanted — consistent with the PRD's own "why ever" downgrade and VISION cuts-before-additions. Neither is recorded; the decision is yours.

---

## Divergences flagged (artifacts vs. state) — for Dustin's seam, not fixed here
1. **`docs/prd_history/PRD-209.md:266`** ends with a stale `STATUS: IN PROGRESS` line that contradicts the header `Status: PROPOSED — HELD`. Cosmetic-but-misleading; fix at the human seam (not touched — recon only).
2. **PR #51** is based on pre-void `main` (`35e0641`); merging it would collide with the current `PRD-205` void row. Reinforces the orphaned finding.

## Exact decisions owed (summary)
- **Item 1:** close #51 → (A) drop router idea, (B) refile under #213, or (C) keep open.
- **Item 2:** 2026-07-15 go/no-go → (A) wire+do the corpus/T/eval work, (B) soft/advisory-park, or (C) drop the date.
- **Item 3:** PRD-209 → (a) build the floor now, or (b) shelve with the recorded reason.

_No mutating action taken. Awaiting explicit go per item._
