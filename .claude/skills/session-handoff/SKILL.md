---
name: session-handoff
description: Use when ending a session to leave ONE committed resume note so a fresh session (new container, no memory) stands up fast without losing contract context. Authors a dated, scannable resume note at the repo's resume-note location (existing convention if present, else docs/session_resume/<date>.md) covering what landed, each live branch's exact next gate, durable non-PRD findings, queued/future scope, and DECISIONS.md candidates — then commits it. A handoff LOADS context, it does not ADVANCE work: it never opens PRs for, merges, or implements the work being handed off; resting branches stay resting. Triggers on "close out", "session handoff", "hand off", "wrap up the session".
---

# Session Handoff

End a session with one committed resume note. The reader is a **fresh session
with no memory** — likely a new container. The note must let them stand up fast
without re-deriving contract context that lives in no structured field.

## Hard constraint — load context, never advance work

A handoff **summarizes gates; it never trips them.** As part of a handoff you do
NOT:

- open or merge PRs for the work being handed off,
- push, rebase, or implement on any resting branch,
- run a review, close out a PRD, or take any step that moves work forward.

Resting branches stay resting. The ONLY thing this skill creates and commits is
the resume note itself (plus, when warranted, a DECISIONS.md entry — see §5).
Committing the note is delivery of the note, not advancement of the work it
describes. If landing the note on a protected `main` requires its own dedicated
doc PR, that is allowed; opening a PR for anything else is not.

## Step 0 — Locate the resume-note path (check first, don't assume)

Find the repo's existing convention before writing anywhere new:

```
git ls-files | grep -i "SESSION_RESUME\|session_resume\|handoff"
```

- If an existing resume-note location/convention exists, **use it** (this repo
  has used `audits/recon-<date>/SESSION_RESUME.md`).
- Otherwise create `docs/session_resume/<date>.md`.

Use the current date for `<date>`. One note per session.

## Step 1 — Author the note (all five sections required; prompt for each)

Scannable, not narrative. Bullets and SHAs, not prose. Prompt the user for each
section — do not silently leave one empty.

### 1. LANDED THIS SESSION
PRDs / PRs that reached `main` this session, **each with its commit SHA**. One
line each: what it changed, in one clause.

### 2. LIVE BRANCHES — the load-bearing section
For **each unmerged branch** (`git branch -a --no-merged main` to enumerate):
- branch name,
- status / stage,
- the **EXACT next gate** — the specific blocking step, never "finish it".
  Name it: *host implementation*, *a named review* (which review, what it must
  check), *a decision* (what decision, by whom). If a branch is
  governance/manual-merge, say so. This is what a fresh session cannot
  reconstruct — get it precise.

### 3. DURABLE FINDINGS NOT IN ANY PRD — highest value, easiest to lose
Judgment and lessons that emerged this session and live in **no** structured
field (no PRD, no registry, no code comment). Prompt explicitly:

> "What did we learn this session that isn't captured in a PRD?"

Do NOT skip this because it looks empty — push for it. Environment quirks,
tooling gotchas, "X looks done but rests on unverified Y", open debt that
gates trust. Mark open debt as such (e.g. **OPEN HIGH DEBT:**).

### 4. QUEUED / FUTURE SCOPE
Seeded-but-not-started work — ideas parked in a PRD's OUT OF SCOPE, follow-ups,
lower-priority leads. Enough that a fresh session can find the thread.

### 5. DECISIONS.md CANDIDATES
For **each** durable finding in §3 ask: *does this belong in `docs/DECISIONS.md`
as a permanent rule, not just a dated note?*

- Resume note = **"where I am now."**
- `docs/DECISIONS.md` = **"rules that always hold."**

For each finding that is a permanent rule, add it to `docs/DECISIONS.md` too
(date-ordered, newest first, matching the file's entry format) and
cross-reference it from the note. A dated "what I observed" can stay note-only;
a "from now on, always/never" belongs in DECISIONS.md.

## Step 2 — Commit (authoring + commit only)

- Stage the note (and the DECISIONS.md entry if §5 produced one) and commit with
  a clear doc-only message.
- If doc edits go directly to `main` per repo convention, commit there.
- If `main` is protected, land the note via **its own dedicated doc branch + PR**
  (and auto-merge only if that is the repo's convention for non-governance docs).
  This PR carries the note alone — never bundle resting-branch work into it.

Then stop. The skill's entire job is: one resume note, authored and committed.
Nothing else moves.

## Anti-patterns

- Narrating the session instead of stating gates and SHAs.
- A §2 entry that says "continue the work" instead of the precise next gate.
- Skipping §3 because nothing "structured" is left — that is exactly the
  irreplaceable part.
- Advancing any handed-off work "while I'm here" — opening a PR, kicking CI,
  rebasing a resting branch. A handoff never does this.
