# Debt-sweep recon — 2026-06-25

Read-only reconnaissance for human triage. Three carry-over debts from this
week's loop runs. **Recommendations only — no fixes, no branch, no PRD.** All
file:line citations re-verified by the main agent against the working tree
(per CLAUDE.md sub-agent sweep re-verification discipline).

Contract baseline confirmed before judging:
- PRD status enum = `{PROPOSED, IN PROGRESS, COMPLETE, PATCH, DEPRECATED}`;
  "No other status values are permitted" — `docs/PRD_PROCESS.md:9-17`.
- HIGH-RISK lane defined at `docs/PRD_PROCESS.md:212` (FILES ∩ HIGH-RISK FILES,
  or CLASS ∈ {EXECUTION, CONTRACT}, or default Tier T0).
- PRD-198 invariants #2 (assert resolved, not requested) and #6 (pin identities)
  are the doctrine Debt B is measured against — `CLAUDE.md` § Semantic-failure
  hardening.

---

## DEBT A — "PRD … MODE" injection-hook origin  [tag: improvement / governance]

**Status: ROOT CAUSE LOCATED. Not a stray injection — intentional scaffolding
that over-fires.**

### Evidence (every emitter traced)
The strings are emitted by exactly one source, the `UserPromptSubmit` hook:

- `.claude/hooks/prd_eval.sh:212` — `"""SYSTEM INSTRUCTION — PRD REVIEW MODE
  ACTIVE …"""` appended when `is_prd_body` is true (PRD-NNN identifier + ≥4
  section keywords; detection at lines 27-36).
- `.claude/hooks/prd_eval.sh:239` — `"""SYSTEM INSTRUCTION — PRD IMPLEMENTATION
  REQUEST DETECTED …"""` appended when `is_impl_request` is true (impl verb +
  PRD-NNN, no full body; detection at lines 41-48).
- Both are joined (`prd_eval.sh:246`) and emitted as
  `hookSpecificOutput.additionalContext` JSON (lines 247-252), which the harness
  injects into the agent's context.
- Wiring: `.claude/settings.json` `UserPromptSubmit` → `bash
  .claude/hooks/prd_eval.sh` — fires on **every** prompt submission.

Only one non-emitting reference exists (documentation, not a source):
- `docs/PRD_REVIEW_TEMPLATE.md:15-16` — cites the `SYSTEM INSTRUCTION — PRD
  REVIEW MODE ACTIVE` hook by name to explain the filename convention. Static
  text, does not emit.

`tests/test_prd_eval_hook.py` exercises the hook's detection/JSON logic but does
not hardcode the instruction literals.

### Root-cause hypothesis
The strings are legitimate hook scaffolding, not an attack or stray injection.
They surfaced "4+ times and were correctly ignored" this week because the hook
fires on **any** prompt that merely *mentions* a PRD-NNN token plus enough
keywords — including recon/loop/bookkeeping prompts that are not PRD authoring
or implementation. This very recon charge (references PRD-209, PRD-198, etc.)
is exactly the shape that trips the `HAS_PRD_NUM` branch. The hook has no
"authoring intent" signal: presence of the token is treated as intent to
author/implement.

Note the literal differs from the reported names: the actual emitted strings are
`PRD REVIEW MODE ACTIVE` and `PRD IMPLEMENTATION REQUEST DETECTED` (not "PRD
IMPLEMENTATION MODE"). Same source; the report's paraphrase is close enough that
this is the same debt.

### Blast-radius hint
Contained: one shell file, one settings wiring. No production code path. The
cost is **context pollution in unattended loop runs** — every loop prompt that
names a PRD gets a multi-paragraph "REVIEW MODE" or "IMPLEMENTATION REQUEST"
instruction block prepended, which the agent must recognize and discard. Risk is
not corruption but (a) wasted context budget and (b) the small chance an
unattended agent *acts* on the injected "perform a complete evaluation /
confirm next sequential PRD" instruction when it shouldn't (this is what
"blocks unattended runs" refers to).

### Fix-shape sketch (recommend — do not implement)
Tighten the trigger so injection requires authoring/implementation *intent*, not
mere mention:
- Gate `is_prd_body` / `is_impl_request` on the prompt not being a read-only
  charge — e.g. suppress when the prompt contains recon/audit/"read-only"
  markers, mirroring the existing `skip_phrases` mechanism (lines 157-164) that
  already suppresses the sequencing gate.
- Or require the PRD body detection to see the prompt *is* the PRD (section
  headers at line starts, not just substring hits), so a charge that quotes PRD
  numbers in prose doesn't qualify.
- Cheapest: add a single opt-out token the loop harness can include.

Tag: **improvement** (hook precision) with a **governance** edge (it injects
behavior-directing SYSTEM INSTRUCTION text into every session).

---

## DEBT B — Codex model-provenance mismatch  [tag: bug / governance]

**Status: ROOT CAUSE LOCATED. Two emission paths; the CI path writes two
disagreeing model identities into the same artifact.**

### Evidence
Codex review artifacts carry the model identity in two places that disagree:

CI-emitted artifacts (via `.github/workflows/codex-review.yml`) — both values
present, disagreeing:
- `docs/prd_history/PRD-199.review.codex.md:5` — `resolved-model=\`gpt-5-codex\``
- `docs/prd_history/PRD-199.review.codex.md:10` — `Model: gpt-5.4`
- `docs/prd_history/PRD-195.review.codex.md:5` — `resolved-model=\`gpt-5-codex\``
- `docs/prd_history/PRD-195.review.codex.md:10` — `Model: gpt-5.5`

Locally-emitted artifacts (hand-written from `codex exec -s read-only` stdout) —
**no** provenance line at all, only the prose self-report:
- `PRD-191/192/200.review.codex.md:4`, `PRD-193:8`, `PRD-190:5` — all
  `gpt-5.5` only.

### Where each value is written
- **Body label** (`Model: gpt-5.x`): comes verbatim from Codex's own prose. The
  workflow *asks* for it at `codex-review.yml:112` ("State explicitly which
  Codex model you are running as") and concatenates the raw prose unchanged at
  `codex-review.yml:170` (`cat codex-final-message.md`).
- **Provenance label** (`resolved-model=…`): extracted from the JSONL response
  metadata `"model"` field at `codex-review.yml:133-139` (`extract_model`),
  allowlist-checked (lines 145-154), written at `codex-review.yml:165`.
- The two are assembled independently in the same block,
  `codex-review.yml:160-171`, with **no reconciliation step between them.**

### Root-cause hypothesis (and a caveat on "ground truth")
The artifact has two model fields produced by two unsynchronized sources, so they
can — and do — disagree. PRD-198 #2/#3 say to trust the resolved value from
response metadata over the model's prose self-report, which argues the prose
`Model: gpt-5.x` body label is the stale/untrusted one.

**But the resolved value is weaker than it looks** (worth a human eye): on every
CI artifact `requested == resolved == gpt-5-codex`. That equality strongly
suggests the JSONL `"model"` field is **echoing the requested alias**, not a
resolved dated snapshot — i.e. it satisfies PRD-198 #2 only superficially and
still trips #6 (`gpt-5-codex` is an alias, not a pinned snapshot). The prose
`gpt-5.5`/`gpt-5.4` is the only place the served *family version* appears. So
the two values are at different granularities (alias vs. family), and "which is
ground truth" is a genuine decision, not a lookup:
- If the goal is provenance of *what was served*, the prose family is more
  informative but is an untrusted channel (#3).
- If the goal is auditable pinning, neither is a snapshot — both fail #6.

### Blast-radius hint
- Affects every CI-emitted `*.review.codex.md` (2 confirmed: 195, 199) plus all
  future ones — these are **binding HIGH-RISK review-gate artifacts**, so a
  wrong/ambiguous model identity weakens the gate's "verified-real Codex"
  property (CLAUDE.md review-gate clause #3).
- Locally-emitted artifacts have a *different* shape (no provenance line),
  so any normalization must cover both paths or the inconsistency persists.
- No runtime/trading impact — this is governance/audit-trail only.

### Fix-shape sketch (recommend — do not implement)
Single normalization point: the artifact-assembly block,
`codex-review.yml:160-171`. Make the body's model identity *derive from* the
verified `${resolved}` rather than be catted verbatim — e.g. rewrite/append the
prose `Model:` line from `${resolved}`, or strip the prose self-report and let
the provenance line be the sole model identity. **Before coding:** resolve the
ground-truth question above (alias vs. family vs. true snapshot) at the decide
seam — the fix differs depending on whether the answer is "trust resolved" or
"capture a real snapshot from metadata." Also decide whether the local
`codex exec` path is being retired in favor of CI (PRD-197); if not, it needs
the same normalization.

Tag: **bug** (two fields disagree in a binding artifact) with a **governance**
dimension (it is a review-gate integrity property).

---

## DEBT C — PRD status enum has no HELD state  [tag: improvement / governance]

**Status: ENUM + CONSUMERS MAPPED. Adding HELD is low-mechanical / one
behavioral hinge.**

### Enum definition locations
- `docs/PRD_PROCESS.md:9-17` — canonical table; "No other status values are
  permitted."
- `tools/validate_prd_registry.py:16` — `ALLOWED_STATUSES = {"PROPOSED", "IN
  PROGRESS", "COMPLETE", "PATCH", "DEPRECATED"}` (the **enforced** copy; CI gate).
- Template examples (non-enforcing): `docs/PRD_TEMPLATE.md:3`,
  `docs/PRD_MICRO_TEMPLATE.md:7`.

### PRD-209 clarification
PRD-209 **does not exist** in the repo: no `prd_history/PRD-209.md`, no registry
row, no index entry (`prd_index.json` `next_prd: 205`). It is a forward-looking
example in the charge. The real, *historical* instance of this gap is **PRD-189**:
its closeout was "held pending PRD-194's publish decoupling" while it was tracked
as `IN PROGRESS` — `docs/PROJECT_STATE.md:14` uses the word "held" in prose
precisely because the enum has no value for it. The debt is real; the cited PRD
number is illustrative.

### Full consumer / validator list (every switch on status)
| Location | What it does with status | HELD impact |
|----------|--------------------------|-------------|
| `docs/PRD_PROCESS.md:9-17` | Canonical enum table | **Add HELD row** |
| `tools/validate_prd_registry.py:16` | `ALLOWED_STATUSES` set; rejects others (CI-blocking via `.github/workflows/ci.yml`) | **Add "HELD"** or CI rejects every HELD row |
| `tools/validate_prd_registry.py:87-88,192` | Validates registry rows + index entries against the set | Works once set updated |
| `tools/validate_prd_registry.py:109,140,287,309` | `status == "COMPLETE"` gates (counter, commit-hash, resolvability, doc-agreement) | No change — HELD ≠ COMPLETE |
| `.claude/hooks/prd_eval.sh:132` | Sequencing gate: `"IN PROGRESS" not in line: continue` — **substring** match | **HINGE — see below** |
| `.claude/hooks/prd_eval.sh:166-186` | Builds "NON-SEQUENTIAL" gate message from IN PROGRESS blockers | Message wording if HELD blocks |
| `scripts/prd_open.sh:~93,158` | Hardcodes new rows to "IN PROGRESS" (registry + index) | No change (HELD set by a different action) |
| `scripts/prd_close.sh:~176,302` | Flips IN PROGRESS → "COMPLETE @ hash"; resets Active-PRD pointer | No change (no HELD↔COMPLETE path needed) |
| `docs/prd_index.json` | Per-entry `status` field, kept 4-way consistent with registry | New value flows through once validator allows it |
| `tests/test_prd_eval_hook.py`, `tests/test_prd_registry.py` | Assert current statuses/detection | **Add red test** for HELD (PRD-198 #4: every guard ships a failing test) |

### The one behavioral hinge
`.claude/hooks/prd_eval.sh:132` decides sequencing by substring-matching
`"IN PROGRESS"`. A HELD PRD will **not** be seen as a blocker. Whether that is
correct *depends on HELD's intended semantics* — and the charge's stated
convention answers it: **HELD = parked**, i.e. NOT actively building, so it
should **not** block higher-numbered PRDs. Under that convention the current
substring behavior is already correct for HELD and line 132 needs **no change** —
HELD naturally falls through as non-blocking, same as PROPOSED.
(If a future decision wanted HELD to block, line 132 would need to match HELD
too — flag, but not the proposed convention.)

### Blast-radius assessment
Small and mostly mechanical:
- **Must change:** `PRD_PROCESS.md:9-17` (enum doc), `validate_prd_registry.py:16`
  (allowed set), and a red test (PRD-198 #4).
- **Should add:** a way to *set* HELD — `prd_open.sh`/`prd_close.sh` only know
  IN PROGRESS↔COMPLETE; parking a PRD is currently a manual registry+index edit.
  Decide whether HELD is set manually or via a small `prd_hold.sh`.
- **No change under the parked-semantics convention:** the sequencing hook,
  the COMPLETE-gated validator logic, and the closeout pointer reset.
- **CLASS:** GOVERNANCE; HIGH-RISK FILES for GOVERNANCE include
  `docs/PRD_PROCESS.md` and `docs/PROJECT_STATE.md` (matrix at
  `PRD_PROCESS.md:188`), so a HELD PRD would land **LANE: HIGH-RISK** and is
  **governance-change / manual-merge-only** per CLAUDE.md (changes the status
  contract). It also needs the four PROPOSED-vs-IN-PROGRESS convention lines
  ("PROPOSED until decide-seam, IN PROGRESS only during build, HELD for parked")
  written into the enum doc so the new state has an unambiguous meaning.

Tag: **improvement** (new lifecycle state) that is **governance**-class and
manual-merge-only.

---

## Triage summary

| Debt | Root cause | Severity | Tag | Fix locus |
|------|-----------|----------|-----|-----------|
| A | `prd_eval.sh` over-fires on any PRD-NNN mention (no authoring-intent gate) | Priority (loop noise / unattended-action risk) | improvement / governance | `.claude/hooks/prd_eval.sh:212,239` + trigger at 27-48 |
| B | Two unsynchronized model-identity fields in CI artifact; resolved may only echo the alias | Medium (binding review-gate integrity) | bug / governance | `.github/workflows/codex-review.yml:160-171` |
| C | Enum has no parked state; "held" work mislabeled IN PROGRESS | Low/medium (lifecycle truthfulness) | improvement / governance | `PRD_PROCESS.md:9-17` + `validate_prd_registry.py:16` |

Two decide-seam questions for the human before any build:
1. **Debt B:** is the ground-truth model identity the JSONL `resolved` alias, the
   prose family version, or a true snapshot that must be captured from metadata?
2. **Debt C:** is HELD set manually or via tooling, and does it confirm the
   parked = non-blocking convention (which leaves the sequencing hook untouched)?
