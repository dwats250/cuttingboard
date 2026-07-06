# CLAUDE.md governance refactor — proposal (2026-07-06)

Session artifact for the Fable charge "CLAUDE.md governance refactor".
Deliverable per the recon-artifact clause: committed to this branch
(`claude/claude-md-governance-refactor-ga5kr0`), merge human-held. Per the
`audits/` anti-pattern, delete this note once the refactor is adopted or
rejected; nothing here is canonical.

The proposed `CLAUDE.md` is the version committed alongside this note on this
branch. This document carries the other five required outputs: move-list, cut
rationale, invariant-survival table, relocate-vs-compress recommendation, and
word counts.

---

## 1. Recommendation: COMPRESS-IN-PLACE (with reference-out), not relocate

**Every candidate relocation turned out to be a no-op: the destination docs
already contain the content.** Verified by reading each destination before
deciding (charge constraint 3):

| Content in old CLAUDE.md | Already canonical at |
|---|---|
| Second-model disposition spec, enforcement, waiver semantics | `docs/PRD_PROCESS.md` § Second-Model Disposition (PRD-242) |
| Same-PR closeout mechanics | `docs/PRD_PROCESS.md` § Same-PR Closeout |
| Cosmetic carve-out definition + batching | `docs/PRD_PROCESS.md` § Cosmetic Carve-Out |
| Parallel review dispatch | `docs/PRD_PROCESS.md` § Review Dispatch |
| Six hardening invariants incl. every *Why:*/*Incident:* line, verbatim | `docs/prd_history/PRD-198.md` Part A |
| PRD-197→207→212→230→242 Codex-arc history | `docs/DECISIONS.md` 2026-07-05 ("PRD-242: second-model review becomes a commissioned instrument") |
| Codex read-only sandbox verification, `workspace-write`/`trust_level` behavior | `docs/DECISIONS.md` 2026-06-10 ("Codex exec sandbox verified") |
| Alignment-cadence retirement rationale ("five runs, zero drift") | `docs/DECISIONS.md` 2026-07-04 (Fable-window Block 1 / PRD-230) |
| PRD-184/186/194 landing-flow history | `docs/DECISIONS.md` 2026-06-14 / 2026-06-16 entries |
| PRD-150 review-arc provenance for the author disciplines | `docs/DECISIONS.md` 2026-05-22 entries |
| Hook mechanics (prd_eval scope, protected patterns) | `docs/CLAUDE_HOOKS.md` |

Relocating would therefore mean **writing duplicates into canonical docs** —
violating the repo's own "reference, don't duplicate" rule and DECISIONS.md's
no-retroactive-condensing norm — while widening this governance PR's FILES set
for zero gain. Compress-in-place keeps FILES = `CLAUDE.md` (+ this session
artifact), and every cut is justified as *redundant with existing canonical
text*, not as a move that could be botched.

**One deliberate exception to leanness:** the four second-model artifact
properties stay in CLAUDE.md nearly in full, because
`docs/PRD_PROCESS.md` § Second-Model Disposition points AT them ("meeting the
four artifact properties in the CLAUDE.md gate text"). Cutting them here would
dangle that canonical cross-reference; moving them into PRD_PROCESS would be a
canonical-doc edit this charge forbids without confirmation. They are the gate
text; they stay.

---

## 2. Move-list

No passage was relocated (see recommendation). Every removed passage is either
**deleted-redundant** (its content already lives at the named location) or
**consolidated** (merged into another surviving line). Format:
old passage → disposition.

1. Intro ("who does what, how work is reviewed…") → consolidated into new
   intro; adds the explicit "states rules and names owners; does not retell
   origin stories" reading contract.
2. "Decisions that meaningfully change direction are recorded in
   docs/DECISIONS.md with date and rationale" (standalone paragraph) →
   consolidated into the `docs/DECISIONS.md` bullet in Canonical sources.
3. Roles/Codex "cross-referencing, structured analysis, code review
   (PRD-242)" examples → consolidated into Working practices § Codex
   mechanics ("PRD cross-review, vision review, structured pre-merge code
   review").
4. HIGH-RISK gate sentence "A second-model review … is an INSTRUMENT … never
   a standing requirement owed by a lane" (appeared twice: gate bullet +
   second-model bullet) → consolidated to once (Roles bullet) + the
   disposition clause; rule intact.
5. "The lane is declared in the PRD header; STANDARD and MICRO lanes are
   lighter" → consolidated into "Lane declares ceremony" bullet; matrix owner
   `docs/PRD_PROCESS.md` (LANE Axis).
6. Second-model "(History: PRD-197/207/212 built and repaired a
   mandatory-Codex apparatus … PRD-242 made the instrument framing official
   … DECISIONS 2026-06-26..07-05.)" → deleted, redundant with
   `docs/DECISIONS.md` 2026-07-05 PRD-242 entry; one-line pointer retained.
7. "(this closes the gate-skip class: PRD-240 merged while its own review
   said the second leg was still owed)" → deleted, redundant with
   `docs/PRD_PROCESS.md` § Second-Model Disposition (retains the PRD-240
   incident verbatim) and DECISIONS 2026-07-05.
8. Auto-merge bullet "(verified during PRD-184 closeout)" → deleted,
   redundant with `docs/DECISIONS.md` 2026-06-14 PRD-184 entry.
9. "the separate closeout PR is retired" rationale → deleted, redundant with
   `docs/PRD_PROCESS.md` § Same-PR Closeout; operative residue kept
   ("Residual bookkeeping fixes auto-merge as their own PR").
10. Named publish workflows "(cuttingboard / hourly_alert / macro_awareness)"
    → deleted, reference detail (discoverable in `.github/workflows/`); the
    rule — scheduled workflows publish only to `publish` — retained in full.
    **Judgment call, flagged.**
11. Governance carve-out "Enforcement today is this policy (agent-honored);
    the recommended mechanical hardening is CODEOWNERS … (PRD-186 R4)" →
    deleted, redundant with `docs/DECISIONS.md` 2026-06-14 PRD-186
    carve-out-enforcement entry (which also corrects the CODEOWNERS claim to
    a label-gated check — the CLAUDE.md sentence was stale). **Flagged:**
    cutting also removes a stale-vs-DECISIONS discrepancy.
12. "Surgical edits, scope-locked" bullet (Review section) → consolidated
    with the Operational-rules "Strict scope locking" bullet (the two
    restated each other); survives as Scope and approvals § Strict scope
    locking, name preserved because `scope-lock-precommit/SKILL.md` cites it.
13. Operational rules "Read-only sidecars by default", "Description, not
    prediction", "Cuts before additions" → deleted, duplication with
    `VISION.md` § Operating principles (charge constraint 2); Canonical
    sources now states VISION's principles bind every change and names them.
14. Ceremony-tiering restatement → compressed to the cosmetic definition +
    owner pointer (`docs/PRD_PROCESS.md` § Cosmetic Carve-Out); the same-PR
    closeout half lives under How work lands.
15. "PRD-158 hit this loop three times before adopting the rule." → deleted,
    narration; provenance tag "(PRD-158)" retained on the rule.
16. Stage-0 "Authoring a PRD in chat and filing it only at closeout produces
    sequencing-gate noise and forces reconstruction from chat history." →
    deleted, narration.
17. Semantic-hardening preamble "Each names the incident it generalizes" and
    all six *Why:* + *Incident:* line pairs → deleted, redundant with
    `docs/prd_history/PRD-198.md` Part A (verbatim canonical); explicit
    pointer added. Rule names, operative statements, and invariant 4's banned
    list retained in full.
18. Explore bullet "Cost is small; the gain is preserved main-context window
    … PRD-158 had at least six missed opportunities of this shape." →
    deleted, narration.
19. Map-consult bullet "re-deriving a location they already record is wasted
    recon" → deleted, narration; instruction retained.
20. "Bookkeeping recon is recon" bullet → consolidated into the single
    "Recon goes to subagents" bullet (same instruction, one home), together
    with "Do not invoke Codex or subagents for simple greps…".
21. Task-list bullet "it keeps progress visible and turns each report into a
    delta rather than a full re-statement" → deleted, narration.
22. Registry-gap "(.claude/hooks/prd_eval.sh, registry-gap check only since
    PRD-243)" → compressed to `prd_eval.sh`; hook scope canonical in
    `docs/CLAUDE_HOOKS.md`. "— a 10-minute bookkeeping commit —" → deleted,
    narration.
23. Codex invocation "(Verified 2026-06-10; see docs/DECISIONS.md.)" →
    deleted, redundant with `docs/DECISIONS.md` 2026-06-10 entry (which also
    canonically holds the `workspace-write`/`trust_level` verification; the
    operative "never `-s workspace-write`" warning is retained in the
    artifact-properties list).
24. Alignment check "Five scheduled cadence runs found zero drift; the
    ceremony detected nothing, so the ceremony is retired and the read
    remains." → deleted, narration; redundant with `docs/DECISIONS.md`
    2026-07-04 Block-1/PRD-230 entry.
25. "Remediation unchanged:" framing word → consolidated ("Remediation:").
26. Author-disciplines preamble "The first three surfaced from the PRD-150
    review arc (2026-05-22); see docs/DECISIONS.md and
    audits/recon-2026-05-22/prd-150-vision-review.md … fourth surfaced from
    the sub-agent flow audit (2026-06-10)." → deleted, narration; redundant
    with `docs/DECISIONS.md` 2026-05-22 and 2026-06-10 entries.
27. Sweep-re-verification "One command; it closes the false-all-clear path
    where an incomplete delegated sweep manufactures a clean result." →
    compressed; the operative "main agent re-runs the single decisive `rg`
    itself" retained verbatim.

## 3. Cut rationale (classification per cut)

| # (above) | Class |
|---|---|
| 1, 4, 5, 12, 14, 20, 25 | consolidation |
| 2, 3 | consolidation |
| 6, 7, 8, 9, 11, 13, 17, 22, 23, 24, 26 | duplication (canonical home already exists — none relocated) |
| 10 | reference detail (rule retained; flagged) |
| 15, 16, 18, 19, 21, 27 | narration |

## 4. Invariant-survival table

Every load-bearing rule enumerated from the old file, mapped to its location
in the new file. "§" = section of the new CLAUDE.md.

| # | Load-bearing rule | New location |
|---|---|---|
| 1 | Dustin decides; human at every seam | § Roles |
| 2 | Claude-chat = lead; Claude Code = implementation within PRD scope | § Roles |
| 3 | Second model = commissioned instrument, never standing gate, never drives architecture | § Roles + § Review gates (disposition) |
| 4 | Reference canonical sources, never duplicate | § Canonical sources + § Anti-patterns |
| 5 | Direction-changing decisions → dated DECISIONS.md entry | § Canonical sources (DECISIONS bullet) |
| 6 | VISION principles (description-not-prediction, read-only sidecars, cuts-before-additions, …) bind all work | § Canonical sources (VISION bullet, per constraint 2) |
| 7 | Nothing lands without review against the PRD | § Review gates |
| 8 | Lane declared in PRD header; ceremony per PRD_PROCESS | § Review gates |
| 9 | HIGH-RISK gate: fresh-context Claude review artifact + Dustin's manual merge | § Review gates |
| 10 | HIGH-RISK ≥242: in-tree artifact OR the exact `SECOND-MODEL:` sentence; waiver is a positive act; `validate_prd_registry.py` fails CI otherwise | § Review gates (sentence verbatim) |
| 11 | Artifact property: in-tree + durable committed path | § Review gates, property 1 |
| 12 | Artifact property: SHA-pinned; superseded-commit review doesn't count | § Review gates, property 2 |
| 13 | Artifact property: read-only; `codex exec -s read-only`, never `-s workspace-write` (re-persists trust_level) | § Review gates, property 3 |
| 14 | Artifact property: fresh-context, not authoring conversation | § Review gates, property 4 |
| 15 | Connector-only ephemeral comment is NOT a second-model artifact | § Review gates (twice: disposition + bot threads) |
| 16 | Bot threads advisory, never gate-satisfying | § Review gates (bot threads) |
| 17 | Every substantive bot thread ACTIONED (fix + in-thread SHA/PRD cite) or DISMISSED (one-line reason); none dangling | § Review gates (bot threads) |
| 18 | Bot-caught real defect gets PRD-when-non-trivial + mutation-verified red test, never silent patch | § Review gates (bot threads) |
| 19 | Thread resolution never substitutes for Claude review or second-model disposition | § Review gates (bot threads) |
| 20 | Bot-thread clause changes are manual-merge-only | § Review gates (bot threads, last sentence) + § How work lands (governance carve-out) |
| 21 | Every review artifact records a DRIFT CHECK (VISION conflict + stale PROJECT_STATE) | § Review gates |
| 22 | Drift review is a post-merge audit under auto-merge, not pre-merge gate | § Review gates |
| 23 | All work lands via PR + `gh pr merge --auto`; branch protection holds until CI `test` green; no direct-to-main; force-push denied | § How work lands |
| 24 | Closeout bookkeeping folds into the implementation PR; residuals auto-merge as own PR | § How work lands |
| 25 | Scheduled publish workflows push only to unprotected `publish` branch; `main` only via CI-gated PRs | § How work lands |
| 26 | Governance changes manual-merge-only: never queue auto-merge on a PR touching `prd-review-claude` or any guardrail in this file | § How work lands |
| 27 | FILES is a hard boundary; stop and amend before touching outside; no silent expansion | § Scope and approvals (Strict scope locking) + § Anti-patterns |
| 28 | Pre-implementation grep sweep of `tests/` for delete/rename/translate of rendered field / contract key / enum; asserting test files into FILES up front | § Scope and approvals |
| 29 | Stage 0: scaffold + registry row + index entry are the first commit; `scripts/prd_open.sh` | § Scope and approvals |
| 30 | Read-only inspection approval-free; mutating commands need explicit approval | § Scope and approvals |
| 31 | Recon-artifact clause: read-only forbids mutating source/contracts/`main`; deliverable committable to its own non-`main` branch; merge human-held; silence = committable | § Scope and approvals |
| 32 | PRD before build for anything non-trivial; established-pattern fixes exempt | § PRD rules |
| 33 | Cosmetic-only → MICRO ≤10-line note, ≤1 weekly polish batch | § PRD rules (Ceremony tiering) |
| 34 | Dead-branch enumeration | § PRD rules, discipline 1 |
| 35 | Downstream-consumer audit | § PRD rules, discipline 2 |
| 36 | Realizability check (incl. declare defensive-against-future-routing) | § PRD rules, discipline 3 |
| 37 | Sub-agent sweep re-verification: main agent re-runs the decisive `rg` | § PRD rules, discipline 4 |
| 38 | Fail-loud, never silent-fallback | § Semantic-failure hardening 1 |
| 39 | Assert the resolved, not the requested | § Semantic-failure hardening 2 |
| 40 | Authoritative source, not proxy | § Semantic-failure hardening 3 |
| 41 | Every guard ships a red test; banned: `importorskip` on required dep, WARN-and-exit-0, tests that cannot fail | § Semantic-failure hardening 4 |
| 42 | Verify where truth is determined (CI parity; sandbox green unverified) | § Semantic-failure hardening 5 |
| 43 | Pin identities that matter (snapshot / SHA / declared-and-locked) | § Semantic-failure hardening 6 |
| 44 | Dashboard regeneration = dispatch `cuttingboard.yml` live; never hand-overwrite `main`'s `ui/*.html` from a sandbox render; local renderer DRY_RUN-only | § Working practices |
| 45 | Start PRD work by reading PRD + modules + DECISIONS | § Working practices |
| 46 | Pause and surface mid-task drift before proceeding | § Working practices |
| 47 | Dispatch Explore reflexively for code recon and bookkeeping recon | § Working practices |
| 48 | No Codex/subagents for simple greps, git ops, mechanical edits | § Working practices (same bullet) |
| 49 | Consult SCHEMA_MAP / CALL_SITE_MAP before location greps; fix stale maps in the change | § Working practices |
| 50 | Task list upfront for ≥3-stage work; keep statuses current | § Working practices |
| 51 | Registry-gap hook fire → add the row, don't work past | § Working practices |
| 52 | Codex only when commissioned; `codex exec -s read-only - < prompt`; artifact written by Claude Code from stdout; Codex never writes in-tree | § Working practices (Codex mechanics) |
| 53 | Independent reviews dispatch in parallel | § Working practices |
| 54 | Decision-driving artifact paths linked in DECISIONS entry | § Working practices |
| 55 | Targeted tests while iterating; full suite once before pre-commit review, backgrounded when long | § Working practices |
| 56 | Alignment check triggers at phase boundaries, not the calendar | § Alignment check |
| 57 | The 15-minute diff read + four questions (incl. folded PRD-186 post-merge audit) | § Alignment check |
| 58 | One DECISIONS.md line per run | § Alignment check |
| 59 | Remediation: substantive drift → corrective PRD; DRIFT-CHECK miss → append in place, no ceremony | § Alignment check |
| 60 | No PRDs violating VISION non-goals without Dustin's override | § Anti-patterns |
| 61 | No opportunistic `runtime/` refactors; own PRD required | § Anti-patterns |
| 62 | No committing generated artifacts outside the workflow force-add allowlist | § Anti-patterns |
| 63 | No session-note sediment in `audits/`; durable findings → DECISIONS or PRD | § Anti-patterns |

Gaps: none. Every rule maps to a surviving location.

## 5. Flagged judgment calls (surfaced, not silently resolved)

- **Cut #10 (workflow names):** the three publish-workflow names were dropped
  as reference detail; the publish-branch rule itself is intact. Restore the
  parenthetical if Dustin considers the enumeration load-bearing.
- **Cut #11 (PRD-186 R4 enforcement note):** the "recommended mechanical
  hardening is CODEOWNERS" sentence was stale — DECISIONS 2026-06-14 records
  the corrected mechanism (label-gated check, not CODEOWNERS). Cut rather
  than corrected, since correcting would have been new content.
- **Kept despite compression pressure:** the four artifact properties
  (PRD_PROCESS points at "the CLAUDE.md gate text"); the full recon-artifact
  clause; the full bot-thread disposition; the exact `SECOND-MODEL:` sentence;
  invariant 4's banned-pattern list. All are operative nearly word-for-word.
- **Pre-existing stale cross-references, not introduced here:**
  `prd-authoring-verified/SKILL.md` and `prd-review-claude/SKILL.md` cite
  `CLAUDE.md § Cross-review gate`, `§ Review artifact discipline`, and
  `§ Cheap-Lookup Dispatch Policy` — none of these section names exist in the
  *current* (pre-refactor) CLAUDE.md either. Out of this charge's scope
  (skill edits are themselves governance-gated); candidate for a follow-up
  MICRO. The one still-valid citation, `§ Strict scope locking`
  (scope-lock-precommit), keeps its exact bullet name in the new file.
- **No hook/tool parses CLAUDE.md content** (`canonical_read_guard.sh` and
  `protect_files.sh` match paths only), so the restructure breaks no
  mechanical consumer.

## 6. Word count

- Before: 2,968 words (475 lines)
- After: 2,112 words (266 lines) — −856 words (−29%)

The charge's diagnosis estimated ~40% operative text (~1,200 words). The
landing point is higher because several passages that read as spec-with-a-home
are pinned here by inbound canonical references (the four artifact
properties), and because the bias-toward-preserving-governance rule was
applied wherever operative content and explanation interleave (recon-artifact
clause, bot-thread disposition, dashboard-regeneration rule). Every remaining
line issues or scopes an instruction.
