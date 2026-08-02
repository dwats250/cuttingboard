# North Star Deep Audit — Charter

**Baseline commit:** `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae` (merge commit
of PR #187, "NORTH STAR: preserve the product vision and map the delivery
program", merged 2026-08-02T00:07:32Z).

**Status:** Phase 0 scaffold. No findings yet — this document establishes
mission, roles, and the rules the rest of the audit must follow.

**Governing architecture:** reviewed 2026-08-01 (verdict: READY AFTER MINOR
ARCHITECTURE CORRECTIONS), corrections ratified by Dustin the same day, Final
Governance Tightening micro-charge applied the same day. See
`audit_execution_plan` (held outside this repo) for full dispatch mechanics;
this charter states the standing rules, not the task-by-task sequence.

---

## 1. Mission (verbatim from the ratified proposal)

1. Freeze one exact merged baseline.
2. Create a source-authority manifest, audit charter, and domain coverage map.
3. Dispatch Luna Extra High agents in parallel as bounded evidence collectors.
4. Require every Luna to write an individual domain audit file using one
   standardized evidence schema.
5. Have Fable: validate domain coverage; spot-check evidence; deduplicate
   findings; reconcile authority conflicts; build the North Star Truth
   Matrix; build an Authority and Dependency Map; isolate genuine
   Dustin-held rulings; create a closed correction plan.
6. Have Sol adversarially cross-review Fable's reasoning, matrix
   completeness, severity, scope, and correction ordering.
7. Present unresolved factual conflicts and genuine owner decisions to
   Dustin.
8. Freeze the accepted truth matrix and correction plan.
9. Execute corrections later in separate bounded PRs.
10. Permit no further open-ended finding discovery after the accepted audit
    contract closes, except for safety, authority, corruption, or material
    matrix-integrity defects.

Actual dispatch mechanics (reasoning-effort levels, exact `codex exec`
invocations) are governed by this repository's existing Codex conventions,
not by the "Extra High" label above — see the execution plan's Task 1.2.

## 2. Evidence and artifact pinning

**Repository source evidence** — every file/section named in
`01_SOURCE_AUTHORITY_MANIFEST.md` — is pinned to North Star baseline
`fdeef90b0a0e0747d1bbf92385d3750b4024f4ae` for the entire lifetime of this
audit. Every such read is `git show
fdeef90b0a0e0747d1bbf92385d3750b4024f4ae:<path>` — never the live working
tree. If `main` advances while the audit is in progress, this pin does not
move: no repository source evidence is refreshed, rebased, or re-read
against the new state. Any newer material discovered incidentally becomes
an entry in `03_AMENDMENTS_LOG.md` only — never a silent evidence update.
This pin is not weakened by anything below.

This baseline pin cannot apply to artifacts this audit itself generates —
Luna domain files, Fable synthesis artifacts, and Sol counter-review
artifacts did not exist at `fdeef90` and have no baseline commit to read
from. Those are pinned separately, by seam, each recorded before the phase
that depends on it begins:

- **Luna domain artifacts** are read by Fable only from the accepted
  evidence-seam commit — the head of PR seam 2 once accepted — recorded in
  `02_DOMAIN_COVERAGE_MATRIX.md` before Phase 2 starts.
- **Fable synthesis artifacts** are read by Sol only from the exact
  synthesis head supplied for that specific counter-review round —
  recorded before that round begins, never inferred from whatever the
  branch happens to hold at read time.
- No actor — Luna, Fable, or Sol — reads any generated audit artifact from
  a mutable live working tree, matching the source-evidence rule above.
- Once an evidence-seam SHA or a synthesis-round head SHA is accepted and
  recorded, `main` advancing afterward never changes that accepted pin. A
  later change becomes a new, separately recorded round, or an Amendments
  Log entry — never a silent substitution of what was already accepted.

## 3. Roles (verbatim from the ratified proposal)

**Luna:** evidence discovery; source tracing; bounded repository inspection;
individual domain files; no final adjudication; no shared synthesis-file
writes; no repository corrections.

**Fable:** synthesis; authority adjudication; deduplication; matrix
construction; dispute isolation; correction planning; no independent
open-ended second audit after Luna coverage closes.

**Sol:** adversarial counter-review of Fable's artifacts; challenge
authority selection, reasoning, matrix completeness, severity, ordering,
and scope discipline; may introduce a new finding only for: safety; false
implementation permission; authority conflict; missing audit-domain
coverage; or a contradiction that invalidates the plan.

**Dustin:** owner rulings; audit acceptance; promotion decisions; approval
of the final correction program.

## 4. PR #187 / PRD-187 disambiguation

PR #187 is the North Star ratification pull request under audit here —
merge commit `fdeef90`, title "NORTH STAR: preserve the product vision and
map the delivery program", exactly 3 files changed:
`docs/PROJECT_STATE.md`, `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`,
`docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`.

PRD-187 ("Macro-Awareness Producer + Materiality Eval", COMPLETE) is an
unrelated, separately-numbered PRD referenced *inside* those same
documents' macro-awareness discussion. No domain may conflate the two.

## 5. Mechanical PR #187 provenance attestation

Verified directly against the GitHub REST API this session (`gh api
repos/dwats250/cuttingboard/pulls/187` and `.../pulls/187/files` and
`.../pulls/187/comments`), not delegated to a sub-agent:

- **Merge commit:** `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae` — matches
  the audit baseline exactly.
- **State:** closed / merged, not draft, merged at `2026-08-02T00:07:32Z`.
- **Head:** branch `docs/north-star-master-ledger`, sha
  `a55450cb3063a1f0ab71640f063ea224fe5aebfa`.
- **Files changed:** exactly the 3 files named in §4 above — confirmed via
  the API file list, not assumed.
- **PR body's own scope claim (verbatim):** "Documentation only. No
  production code, tests, workflows, dependencies, registry, PRD-index,
  historical PRD, or governance-doctrine changes."
- **PR body's own validation claim (verbatim):** "exact branch head:
  `579d7f8` (F1–F8 review-finding correction commit on top of `df73154`) ·
  the two product documents plus one pointer bullet in
  `docs/PROJECT_STATE.md` changed · complete diff inspected · `git diff
  --check` clean · exactly one packet marked NOW · no Dustin decision
  represented as already made."
- **PR body's own held-authority claim (verbatim):** "This PR is draft and
  manual-merge-only. Dustin alone may ratify, promote work, mark ready, or
  merge."

**Connector thread enumeration (PRD-228):** 28 inline review comments on
this PR, all authored by `chatgpt-codex-connector[bot]`, zero issue-level
(non-inline) comments. Severity split: 1 tagged P1 ("Keep the critical
kill-switch bypass ahead of new product work", CB-01, on
`NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`), 27 tagged P2. All 28 target
the two North Star product docs; none target `docs/PROJECT_STATE.md`.
Representative topics observed (not adjudicated here — that is Phase 1
domain territory, principally Domain A): portfolio-state consistency
(NS-4A/4B, NS-1D, PRD-268), debt-row completeness (CB-12b, GEX-1/2, three
"fixed" reconciliation findings), CI-validates-semantic-truth overclaim,
self-reference to PR #187 in its own open-PR baseline, and a GOV-2
MATERIAL-sequence applicability question.

**Connector thread resolution state (AMENDMENT-001, closed non-blocking —
see `03_AMENDMENTS_LOG.md`):** GitHub-tracked review-thread metadata has
been independently obtained: all 28 threads are unresolved; some are
marked outdated (their diff context has been superseded by a later
revision) and some are not. Resolved/unresolved and outdated/current are
GitHub workflow metadata — they describe a thread's relationship to the
current diff, not whether the underlying comment was substantively
actioned or dismissed. GitHub's `isResolved` state cannot by itself
establish a PRD-228 disposition; nor can `isOutdated`.

The full governed taxonomy is exactly three values — CLAUDE.md's PRD-228
clause names `ACTIONED`/`DISMISSED`; `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md`
§7 extends it with the third for MATERIAL packets:

- `ACTIONED` — the correcting commit or governed follow-up lands and is
  cited in-thread by fixing commit SHA or PRD number.
- `DISMISSED` — false positive, out of scope, or already covered, with an
  explicit in-thread one-line reason.
- `BLOCKED/PARKED` — the finding is valid, the packet is not review-clean,
  no downstream authority may proceed, and the thread remains unresolved
  until Dustin resumes, narrows, or retires the packet (GOV-2 §7: "not a
  substitute for action on a packet presented as ready").

An unresolved GitHub thread is not automatically `BLOCKED/PARKED`, and a
resolved GitHub thread is not automatically `ACTIONED` or `DISMISSED` —
resolved/unresolved and outdated/current are workflow metadata and
establish none of the three by themselves. Inspecting replies, cited
fixes, and dismissal reasons for all 28 threads to determine their actual
disposition is Phase 1 work, not part of this Phase 0 attestation. No
comment in the enumeration above is treated as `ACTIONED`, `DISMISSED`,
`BLOCKED/PARKED`, correct, or incorrect in this charter. Substantive
adjudication of all 28 comments is routed to Phase 1 — principally Domain
A, which owns the PRD-228 bot-thread convention and the PR #187 provenance
evidence per the Source Authority Manifest — and to whichever other domain
owns a given comment's specific subject matter.

## 6. Global Constraints (non-negotiable, verbatim from Dustin's ruling)

1. Every evidence read is pinned to `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`
   — never the live working tree.
2. The Source Authority Manifest is built and committed before any Luna
   dispatch.
3. Every evidence row carries `assertion_type`.
4. Luna's allowed `result` values never include `DUPLICATE OF <ID>` — dedup
   is Fable-only.
5. Every shared master source has exactly one owning domain; all others
   cite, never re-derive.
6. Confidence is a defined 3-tier scale, not a free number; incomplete
   domains get exactly 1 retry before escalation.
7. Scaffold, evidence, and synthesis land in three separate PRs unless
   Dustin explicitly overrides.
8. Fable/Sol correction iteration is capped at 2 rounds before forced
   escalation to Dustin.
9. Any discovery that would expand scope is logged to the Amendments Log
   and left un-investigated — never silently folded into a finding.

## 7. Definition: CONFIDENCE, and the committed evidence schema

Referenced by Global Constraint #6. Every evidence row's `confidence` field
is exactly one of three values, no numbers or additional labels:

- **HIGH** = direct code-and-document cross-reference, or a single direct
  and unambiguous authoritative source.
- **MEDIUM** = document-only evidence where no code cross-reference is
  possible, or one authoritative source plus a minor interpretive step.
- **LOW** = ambiguous, incomplete, or conflicting evidence.

This is the committed definition every Luna dispatch incorporates — no
domain file may define or use a different scale.

**Domain file header.** Every domain file states these fields before any
evidence row:

- Baseline SHA: `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`.
- Accepted scaffold seam SHA (recorded in `02_DOMAIN_COVERAGE_MATRIX.md`;
  governs which version of this charter and the manifest the dispatch
  used).
- Assigned domain.
- Owned sources (from `01_SOURCE_AUTHORITY_MANIFEST.md`).
- Cited sources (from the manifest).
- Excluded by default (from the manifest).
- Files inspected — path list, each read via `git show
  fdeef90b0a0e0747d1bbf92385d3750b4024f4ae:<path>`.
- Files intentionally excluded — list plus one-line reason.
- Completion status: `NOT STARTED | IN PROGRESS | COMPLETE |
  BLOCKED-PENDING-AMENDMENT | INCOMPLETE-RETRY-EXHAUSTED`.
- Attempt count.
- No-edits attestation: confirmed.

**Evidence table** — one row per assertion checked:

`| ID | North Star assertion | assertion_type | evidence (path:lines, pinned) | result | risk | confidence | assumptions | Dustin ruling required? |`

- `assertion_type` is one of: `FACT`, `INTERPRETATION`,
  `FUTURE-DESIGN-INTENT`, `OWNER-DECISION`.
- `result` is one of: `MATCH`, `MISMATCH`, `PARTIAL`, `UNKNOWN`, `OUT OF
  SCOPE`. Never `DUPLICATE OF <ID>` (Global Constraint #4) — dedup is
  Fable-only.
- `risk` — a short free-text note on the practical consequence if this
  assertion is wrong. Not an enum; distinct from `confidence`, which is
  about evidentiary certainty, not consequence.
- `confidence` — `HIGH`/`MEDIUM`/`LOW` exactly as defined above.
- `assumptions` — optional, normally empty. Populate only when reaching
  this row's result required an interpretive assumption beyond what the
  cited evidence states outright, so Fable and Sol can distinguish
  observed evidence from inference at a glance.
- `Dustin ruling required?` — yes/no.

**Non-match detail** — one block per `MISMATCH` or `PARTIAL` row: exact
source path and lines; governing authority; observed discrepancy;
practical consequence; false-authority risk; safety relevance;
current-vs-future-facing effect; proposed disposition; confidence; missing
evidence.

## 8. Domains (full source assignment in `01_SOURCE_AUTHORITY_MANIFEST.md`)

| Domain | Scope (one line) |
|---|---|
| A | Governance, authority, materiality — broadest domain, no exclusions |
| B | Portfolio, lifecycle, PRD/current-state truth — excludes full PRD-history re-audit |
| C | Findings/debt/queues (CB-01–47) — excludes ungrounded "PRD-255 follow-ons" |
| D1 | Product surfaces, as-built (candidate card, Market Map) — fact-check against named code files |
| D2 | Product surfaces, proposed (Market Control Card) — plan-consistency check, not fact-check |
| E | ORB / candidate fidelity (PRD-271, CB-07) — excludes general VWAP semantics |
| F | Freshness/scheduling reconciliation — reconciles against `stage0-02`/`stage0-03`, not fresh derivation |
| G | Expansion vocabulary reconciliation — checks North-Star-only terms against binding doctrine, not a 5-track audit |

Domain H (PR #187 provenance) is not a peer domain — its mechanical check is
§5 above.

## 9. Amendments procedure

Any Luna, Fable, or Sol discovery that would expand scope (new domain, new
source, reversal of an excluded-by-default item, a capability gap
discovered mid-audit) is appended to `03_AMENDMENTS_LOG.md` and left
un-investigated until Dustin rules on it. Full format in that file.

## 10. Stopping rule (verbatim from the ratified proposal)

The audit closes when:

1. every manifest source is assigned;
2. every domain attests to completed coverage;
3. every material North Star assertion appears in the Truth Matrix;
4. every mismatch has one disposition;
5. every cross-domain conflict is resolved or entered in the Dispute Log;
6. every Dustin-held decision is separated from factual correction;
7. Sol has no unresolved safety, authority, or matrix-integrity objection;
8. Dustin ratifies the correction plan.

## 11. Definition: COMPLETE

A domain's completion status may read `COMPLETE` only when all of the
following hold simultaneously:

- every OWNED source has been inspected and appears in the domain file's
  "files inspected" list;
- every CITED source required to interpret an owned-source assertion has
  been consulted (not necessarily re-derived);
- every EXCLUDED-BY-DEFAULT item is documented with a one-line reason, not
  silently omitted;
- the evidence table is fully populated for every assertion the domain
  charter names — no blank rows;
- no unresolved TODO, placeholder, or "to be determined" text anywhere in
  the file;
- the completion-status field itself is explicitly set to `COMPLETE` (not
  left blank or implied).

A domain missing any of these is `IN PROGRESS`, `BLOCKED-PENDING-AMENDMENT`,
or `INCOMPLETE-RETRY-EXHAUSTED` — never a self-declared `COMPLETE` that
Fable has to take on faith.

## 12. Definition: WAIVER

A Dustin waiver of an incomplete domain is not equivalent to `COMPLETE`,
and does not silently satisfy Stopping Rule condition 2 ("every domain
attests to completed coverage"). A waiver is a formal amendment — logged
in `03_AMENDMENTS_LOG.md`, never a verbal or implicit approval — that must
explicitly state all four of:

1. the waived domain or source;
2. the accepted coverage gap (what remains unknown or unverified);
3. whether Phase 2 synthesis may proceed despite the gap;
4. the corresponding amendment to Stopping Rule condition 2, recording
   that this specific domain is accepted as a logged exception rather than
   completed.

Absent any one of these four elements, an incomplete domain blocks Phase 2
— full stop, no informal waiver substitutes for this.

## 13. Post-ratification freeze

The instant Dustin ratifies the correction plan: `90_NORTH_STAR_TRUTH_MATRIX.md`
becomes immutable — no further edits, not even typo fixes, without a new
dated amendment. `91_AUTHORITY_DEPENDENCY_MAP.md` and `92_DISPUTE_LOG.md`
become historical records of how the matrix was reached, not living
documents. Only future bounded PRDs may implement corrections against the
frozen matrix — the audit itself does not resume to apply them.

## 14. Post-closure reopening exceptions (verbatim from the ratified proposal)

After closure, later discovery does not reopen the audit unless it
demonstrates: a safety defect; false implementation authority; data
corruption; an authority conflict; or a materially false fact in the
accepted matrix.
