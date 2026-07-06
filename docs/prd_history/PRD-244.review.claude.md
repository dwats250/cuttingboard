# CLAUDE.md governance refactor — fresh-context Claude review

Review leg required by PRD-186 (governance change, manual-merge-only) and
PRD-242 (HIGH-RISK gate). Reviewer did not author the change and re-derived
the load-bearing rule set independently; the author's survival table was not
taken as evidence.

- **Change under review:** commit `724991e` on branch
  `claude/claude-md-governance-refactor-ga5kr0` (exactly one commit ahead of
  `main` @ `9720843`; touches `CLAUDE.md` +
  `audits/claude-md-refactor-2026-07-06/PROPOSAL.md` only).
- **SHA-pinned:** this review covers `724991e` and no later commit.
- **Artifact slot:** written to the charge-specified
  `audits/claude-md-refactor-2026-07-06/review.claude.md` because no PRD
  number exists yet (see REQUIRED EDIT 2). Relocate to
  `docs/prd_history/PRD-NNN.review.claude.md` once the PRD is filed.

VERDICT
ACCEPT WITH CHANGES  (charge scale: **PASS-WITH-FIXES**)

SUMMARY
The rewritten CLAUDE.md is a faithful compression: my independent enumeration
found **67 load-bearing rules** in the pre-refactor file (author's table: 63 —
the delta is granularity only, e.g. I count VISION's three restated principles
separately; there is no mapping disagreement), and **all 67 survive** in the
new file with operative force intact; nothing is weakened or absent. All three
repo verifications the author's reasoning rests on hold, and the critical
`SECOND-MODEL:` string survives byte-exact. Two fix-class defects remain, both
outside the survival table's scope: the section renames dangle four **live**
inbound citations in canonical docs/skills (a token-sweep miss of exactly the
kind the file's own pre-implementation-grep rule targets), and the change is
not yet filed to the repo's own Stage-0 / PRD standard.

## Independent invariant survival (check A)

Method: re-derived from the pre-refactor `CLAUDE.md` on `main` @ `9720843` —
a line counted as load-bearing if violating it causes real damage or re-opens
a named incident; narration explaining why a rule exists did not count.

Count: **67 load-bearing rules enumerated; 67 map to a surviving location in
the new file; 0 weakened, 0 absent.** Sections traced: Roles (4), Canonical
sources (3), Review and commit discipline (19), Operational rules (8),
Semantic-failure hardening (6), Workflow patterns (13), Alignment check (4),
PRD-author disciplines (4), Anti-patterns (6).

Deltas vs the author's 63-row table:
- Granularity only. I split the three VISION principles the old file restated
  (their row 6) and count the scope-lock rule at both of its old homes (their
  rows 27/32 fold these). No rule in my enumeration lacks a home in the new
  file, and no row in their table maps to a location I dispute.
- Characterization note on their row 6: the three principles
  (description-not-prediction, read-only-sidecars, cuts-before-additions) are
  the one place rule *text* leaves CLAUDE.md for a named reference (the VISION
  bullet: "bind every change; apply them from VISION directly"). `VISION.md`
  § Operating principles verifiably holds them verbatim, the names are
  self-describing, and the binding statement is explicit — survival by
  reference, accepted. See RECOMMENDED EDIT 1 for a completeness nit on that
  bullet's enumeration.
- Spot-checked compressions that stay operative: the `-s workspace-write`
  ban keeps its trust_level mechanism (drops only the consequence clause);
  invariant 4 keeps the full banned-pattern list; the recon-artifact clause,
  bot-thread disposition, and dashboard-regeneration rule survive nearly
  word-for-word; "Strict scope locking" keeps its exact name, which
  `scope-lock-precommit/SKILL.md:209` cites.

## Repo verifications (check B) — stated results

**B.1 — `docs/AGENT_WORKFLOW.md` (new outbound pointer): PASS.** The file
exists on `main` and holds exactly the claimed content: the protected-file
set ("Never auto-approve" table) that `scope-lock-precommit` and
`prd-authoring-verified` parse to decide HIGH-RISK lane
(`docs/AGENT_WORKFLOW.md:1-13,33-51`). The new Canonical-sources line
("protected-file set consumed by the PRD skills") describes it accurately.
The line stands.

**B.2 — Pointer integrity: PASS (2 mandatory + 3 sampled rows verified).**
- (a) `docs/prd_history/PRD-198.md` Part A (lines 57–113) contains all six
  hardening invariants **with every *Why:*/*Incident:* pair verbatim**; the
  doc's closeout header records Part A as adopted 2026-06-18. The cut
  de-duplicated; it did not delete.
- (b) `docs/DECISIONS.md` 2026-07-05 ("PRD-242: second-model review becomes a
  commissioned instrument (closes the 197→230 Codex arc)") holds the full
  arc history including the PRD-240 gate-skip and waiver semantics. The
  PRD-240 incident is additionally verbatim in `docs/PRD_PROCESS.md:163-164`.
- Sampled: DECISIONS 2026-06-10 ("Codex exec sandbox verified") holds the
  `workspace-write`/`trust_level` verification (move-list #23) — holds.
  `docs/PRD_PROCESS.md` holds Same-PR Closeout, Cosmetic Carve-Out, Review
  Dispatch, Second-Model Disposition, and the LANE matrix (#5, #7, #9, #14) —
  holds. Move-list #24 ("five runs, zero drift" → DECISIONS 2026-07-04):
  the 2026-07-04 Block-1 entry records the cadence retirement, and the five
  PASS/no-drift runs are individually recorded (2026-05-22, 05-29, 06-19,
  06-20, 06-30 entries) — the rationale is reconstructible from canonical
  entries rather than sitting in the one cited entry; acceptable, noted.
- The proposal's "deliberate exception" is honored: the four artifact
  properties stay in CLAUDE.md, which keeps `docs/PRD_PROCESS.md:155`'s
  inbound pointer ("the four artifact properties in the CLAUDE.md gate
  text") from dangling.

**B.3 — Cut #11 staleness claim: PASS, cut is sound.** DECISIONS 2026-06-14
("PRD-186: governance carve-out enforcement … corrected: label-gated check,
not CODEOWNERS") records the corrected mechanism — a required-check guardrail
workflow gated on a human approval label, with CODEOWNERS explicitly
withdrawn (admin-override bypasses the `test` gate) — and itself flags the
CLAUDE.md CODEOWNERS sentence as "superseded by this entry, fix on a
follow-up". The deletion executes a correction DECISIONS already ordered; no
live recommendation was lost. See RECOMMENDED EDIT 2 for an optional
discoverability pointer.

## Mechanical / critical-string check (C) — PASS

- Byte-exact grep of the new file:
  `SECOND-MODEL: instrument not commissioned, merging on Claude-review + human judgment.`
  present verbatim (new CLAUDE.md line 72).
- `tools/validate_prd_registry.py` matches on the constant
  `SECOND_MODEL_SENTENCE = "instrument not commissioned, merging on
  Claude-review + human judgment"` (lines 22–24) — a substring of the
  surviving line, checked against PRD docs, not CLAUDE.md; the CLAUDE.md line
  is the template mergers copy from, and it survives copyable-correct.
- Validator run locally: the second-model disposition check emitted **zero
  errors**. The run exits 1 only on "Unresolvable commit" noise — an artifact
  of this sandbox's shallow clone (60 commits; `git rev-parse` confirms), not
  of the branch; CI runs `--skip-commit-resolvability` (PROJECT_STATE,
  PRD-200/243) and is where this check is determined (invariant 5).

## DRIFT CHECK (D)

- VISION: **none.** No new prediction logic, sidecar, or module; the
  compression itself enacts "cuts before additions" and
  "docs must match code". No non-goal or principle conflicted.
- PROJECT_STATE: **none.** Every PROJECT_STATE claim about CLAUDE.md content
  (PRD-228 bot-thread clause "in CLAUDE.md"; PRD-202 recon guidance; the
  phase-boundary diff-read "per CLAUDE.md") remains true against the new
  file. No claim goes stale.

## Process conformance (E) — FAIL AS FILED (author-acknowledged)

The change edits `CLAUDE.md`, which sits in the GOVERNANCE class HIGH-RISK
FILES row of the CLASS matrix (`docs/PRD_PROCESS.md:239`): this is a
GOVERNANCE, LANE HIGH-RISK, manual-merge-only change requiring its own PRD.
On the branch: **no PRD scaffold, no registry row, no `prd_index.json` entry**
(`next_prd` still 244) — the implementation commit exists with no Stage-0
commit, contrary to the Stage-0 rule in both old and new CLAUDE.md. The
commit message acknowledges this ("requires a dedicated PRD, fresh-context
review, and Dustin's manual merge"), so it is filed as a proposal branch, not
to standard. PRD-number gap: **PRD-244** (next per `prd_index.json`) is the
natural slot. See REQUIRED EDIT 2.

## REQUIRED EDITS

1. **Reconcile four live inbound citations broken by the section renames.**
   The refactor renames "Operational rules" (→ Scope and approvals / PRD
   rules), "Review and commit discipline" (→ How work lands / Review gates),
   and "Workflow patterns" (→ Working practices). Live references that now
   dangle:
   - `CODEX.md:11` — "Owned by `CLAUDE.md` (§ Roles, § Canonical sources,
     § Operational rules)"
   - `docs/PRD_PROCESS.md:140` — "see CLAUDE.md \"Workflow patterns\""
   - `docs/architecture.md:287` — "see CLAUDE.md Workflow patterns"
   - `.claude/skills/prd-review-claude/SKILL.md:157-158` — "Per `CLAUDE.md
     § Review and commit discipline`…" (line-wrapped; single-line greps miss
     it — likely why the author's sweep did). This citation is valid today
     and this change breaks it.
   Fix in the same PRD (amend FILES to authorize these four files — note the
   skill edit is itself governance-gated, already satisfied by this PR being
   manual-merge-only) or retain the old section names. Historical narration
   in `docs/DECISIONS.md` / `docs/audit/` / `docs/prd_history/` is dated
   record, not live pointers — leave it.
   FAIL: after merge, any of the four files above cites a CLAUDE.md section
   name that does not exist in CLAUDE.md.

2. **File the governance PRD before merge (Stage-0).** Add the PRD-244
   scaffold + IN PROGRESS registry row + `prd_index.json` entry as the
   branch's next commit (CLASS GOVERNANCE, LANE HIGH-RISK,
   MANUAL-MERGE-ONLY). At close the PRD doc must carry the second-model
   disposition (the verbatim `SECOND-MODEL:` sentence unless Dustin
   commissions an artifact), and this review relocates to
   `docs/prd_history/PRD-244.review.claude.md` as the fresh-context Claude
   leg — re-pin if any commit beyond `724991e` changes `CLAUDE.md` content.
   FAIL: the PR merges with no COMPLETE PRD row covering the CLAUDE.md
   change, or a HIGH-RISK close carrying neither artifact nor sentence
   (which `tools/validate_prd_registry.py` will fail at CI).

## RECOMMENDED EDITS

1. The new VISION bullet enumerates five of VISION.md's six operating
   principles (omits "acknowledged debt carries a re-evaluation date"). Add
   it or mark the parenthetical non-exhaustive, so the list can't read as
   the complete set.
2. Optional, per B.3: a one-line enforcement-status pointer on the
   governance carve-out ("mechanical hardening tracked in DECISIONS
   2026-06-14: label-gated required check") would keep the deferred
   hardening discoverable from the file that declares the policy.
3. Fold the pre-existing stale citations into the follow-up MICRO the
   proposal already suggests, and add one the proposal missed:
   `.claude/hooks/prd_eval.sh:53` (comment citing `CLAUDE.md § Review
   artifact discipline` — already stale pre-refactor, comment-only).

## RATIONALE

- REQUIRED 1 is the repo's own standard applied to this change: a rename of
  a referenced surface without sweeping inbound references is the
  silent-drift class CLAUDE.md's pre-implementation-grep rule exists to
  close (and VISION's "system must match its documentation" principle names
  as the failure mode that produced sprawl). None of the four is a
  mechanical consumer — `canonical_read_guard.sh` and `protect_files.sh`
  match paths only, confirming the proposal's claim on that narrower point —
  but three sit in canonical docs and one in the review-gate skill itself.
- REQUIRED 2 is Stage-0 + the PRD-242 gate applied to a GOVERNANCE
  HIGH-RISK-FILES change; the author's own commit message concedes it.
- The verdict is ACCEPT WITH CHANGES, not REJECT: the substance under review
  — zero load-bearing rule loss — independently verifies clean, and both
  required edits are additive filing/reconciliation work, not rewrites.

## Verification Report

- V1 line citations: all cited lines re-checked against `main` @ `9720843`
  and branch @ `724991e` this session (CODEX.md:11; PRD_PROCESS.md:140,155,
  163-164,239; architecture.md:287; prd-review-claude/SKILL.md:157-158,209
  [209 = scope-lock-precommit]; prd_eval.sh:53; validator lines 22-24;
  AGENT_WORKFLOW.md:1-13,33-51; PRD-198.md:57-113; new CLAUDE.md:72) — all
  resolve.
- V2 symbols/paths verified: `docs/AGENT_WORKFLOW.md`,
  `tools/validate_prd_registry.py::SECOND_MODEL_SENTENCE`,
  `scripts/prd_open.sh`, all DECISIONS entries cited (2026-07-05, 2026-07-04,
  2026-06-30/20/19, 2026-06-14 ×2, 2026-06-10, 2026-05-22/29) — UNVERIFIED:
  none.
- V3 VERDICT: ACCEPT WITH CHANGES.
- V4 FAIL-line lint: pass (both REQUIRED edits carry binary FAIL lines).
- V5 Codex REQUIRED coverage: n/a (independent mode; no second-model review
  exists for this change).
- V6/V7 target path: charge-specified audits slot; not a Codex slot; did not
  previously exist. Relocation to the Claude PRD slot on numbering noted.
- V8 placeholder tokens: none.
- V9 focus: this review targets the proposed CLAUDE.md text + filing state;
  no test-suite claims asserted (local validator run reported with its
  sandbox caveat, per invariant 5).
- V10 drift check: VISION: none; PROJECT_STATE: none.
- Mode: WRITE_MODE. File written:
  `audits/claude-md-refactor-2026-07-06/review.claude.md`.
