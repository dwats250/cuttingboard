# PRD-302 Campaign Control Plane MATERIAL packet -- independent review + exact-head confirmation (Sol)

GOV-2 packet-cycle durable evidence for the PRD-302 Slice-A campaign control
plane MATERIAL packet (`PACKET.md` in this directory). Records the two
auto-commissioned Codex packet-cycle events (INITIAL PACKET REVIEW;
EXACT-CORRECTED-HEAD CONFIRMATION) and the one consolidated correction between
them (GOV-2 sections 2, 7).

**Reviewer:** GPT-5.6 **Sol** (`gpt-5.6-sol`), invoked
`codex exec -s read-only -m gpt-5.6-sol -c model_reasoning_effort=xhigh`
(sandboxed read-only, prompt via stdin, verdict from stdout). Sol is the
standing default independent second-model reviewer for MATERIAL packet reviews
(owner model-utilization ruling 2026-08-08). Fresh context; not the packet
author. Artifacts written by Claude Code (HELM, Opus 4.8) from captured stdout;
Sol wrote nothing into the repository tree (self-reported memory-provenance /
isolation line, quoted per event).

---

## 1. INITIAL PACKET REVIEW

- **Event type:** `INITIAL PACKET REVIEW` (GOV-2 section 2, step 3).
- **Reviewer / role:** `gpt-5.6-sol`, fresh-context independent reviewer.
- **Reviewed commit SHA:** `3de08a35118764fe0df5847d6ad8216659c45142`.
- **Review date:** 2026-08-13.
- **Run session id:** `019ff9d9-85f4-7d42-b866-4d3ba2d99842`, sandbox
  `read-only`, reasoning effort `xhigh`.
- **VERDICT: DESIGN INCOMPLETE** (1 CRITICAL, 6 MAJOR, 2 MINOR; 7 confirmations).

### Findings and dispositions (one consolidated correction cycle)

Full disposition detail is in `PACKET.md` section `## CORRECTION CYCLE`; each
finding was addressed in the single GOV-1/GOV-2 correction cycle.

| # | Sev | Finding (Sol) | Disposition |
|---|---|---|---|
| 1 | CRITICAL | Raw model output has an omitted ~90-day public Actions job-log presentation path; the one-day artifact is not the only surface, and neutralization governs only the artifact, not the job log. | **ACTIONED** -- `PACKET.md` 3.8 rewritten as a full producer-to-final-consumer inventory; secret proxy-excluded from logs; Slice A synthetic = benign; Slice B untrusted-text-to-public-log named as a Slice-B constraint. |
| 2 | MAJOR | Secret boundary does not bind the workflow ref, does not set `persist-credentials: false`, and mischaracterizes `allow-users` as a deny-by-default allowlist. | **ACTIONED** -- 3.4 + req 9: `persist-credentials: false`, `ref: main` + `github.ref` guard, protected Environment secret policy OR explicit owner sole-writer acceptance, `allow-users` recorded as additive. |
| 3 | MAJOR | Model-output-to-validator transport unspecified; direct `${{ ... }}` splicing into `run:` would be pre-validation injection. | **ACTIONED** -- new 3.6 + req 11: env/command-file transport, quoted input via pinned github-script, injection-inertness mutation test. |
| 4 | MAJOR | Bootstrap precedent and "lawful NO" path misstated; PRD-197/207/212 merged IN PROGRESS and closed later (not COMPLETE-at-install); the later-numbered-closeout-blocking claim is false. | **ACTIONED** -- 9.2 rewritten to current law; false blocking claim withdrawn; YES reframed as structural-install-as-COMPLETE via same-PR closeout with named post-merge follow-up; deferred-second-model-check point retained. |
| 5 | MAJOR | "Model receives only event JSON / never checks out repo code" over-claimed; `actions/checkout` makes the reviewed tree readable. | **ACTIONED** -- 3.5 + req 10: minimal sparse checkout, isolated working dir, enumerated readable surface, TRIPWIRE-asserted; 5.2 row corrected. |
| 6 | MAJOR | Five-file FILES set + ceiling not yet reviewable: validator mechanism unchosen; `github-script`/`download-artifact` unearned; lifecycle files not enumerated. | **ACTIONED** -- 3.11 handwritten stdlib validator + schema drift-guard test (no new dep); download-artifact removed; github-script given transport role; lifecycle/authority files enumerated; estimate revised. |
| 7 | MAJOR | Model-identity row records an unsupported "served" identity; action pin currency inconsistent. | **ACTIONED** -- 6.1: `gpt-5.6-sol` recorded as requested only, served not positively observable (PRD-207), "live probe served" removed, wrapper disclosure added; section 6 pins reconciled to a consistent current-major SHA set, download-artifact removed. |
| 8 | MINOR | Anti-stall doc does not establish the off-terminal need as repository fact. | **ACTIONED** -- 5.3 relabels off-terminal value as an owner product hypothesis; KEEP/NO-GO is the cuts-before-additions seam. |
| 9 | MINOR | INFRA "not CONTRACT" rationale narrows the canonical CONTRACT definition. | **ACTIONED** -- 1.2 keeps INFRA on dominant-purpose grounds, acknowledges the subordinate internal-contract surface, carries schema-diff/consumer-audit ceremony into section 7. |

### Confirmations (Sol; no change required)

Materiality (GOV-2 section 1); CLASS INFRA (dominant) and LANE HIGH-RISK forcing
(R11 + MICRO-ineligibility); the default-branch bootstrap fact; the good
secret-hygiene elements (necessary but not a complete boundary); the
structural-test tripwire honesty; PRD-230 non-revival as genuine ("not
automatically NO-GO"); the ceiling estimation method (number pending Finding 6,
now resolved).

### Isolation (Sol, verbatim)

> Operated in fresh review context independent of the authoring session; prior
> memory was used only as a narrow navigation index and no packet claim was
> accepted from it. All findings were re-derived from HEAD
> `3de08a35118764fe0df5847d6ad8216659c45142`, live repository/GitHub state, and
> governing sources. Read-only throughout; no repository writes, files, staging
> changes, or git changes.

---

## 2. CONSOLIDATED CORRECTION

One GOV-1/GOV-2 correction cycle applied to `PACKET.md`, addressing all nine
findings above (see the `## CORRECTION CYCLE` table in `PACKET.md`). Changes are
confined to `PACKET.md` and this review record; no PRD, Stage-0, registry,
index, PROJECT_STATE, payload, test, workflow, schema, or prompt file was
created or modified. The corrected head is the commit that applies this
correction on branch `worktree-prd-302-material-packet` (recorded in section 3
below once confirmed).

---

## 3. EXACT-CORRECTED-HEAD CONFIRMATION

- **Event type:** `EXACT-CORRECTED-HEAD CONFIRMATION` (GOV-2 section 2, step 5;
  scope per sections 5, 7 -- confirmation that each prior finding is resolved at
  the exact head, not a new broad review).
- **Reviewer / role:** `gpt-5.6-sol`, fresh-context independent reviewer,
  distinct session from the INITIAL review.
- **Confirmed head SHA:** `8c7669ed36d36fd9d9c47aa3fee82c4479746e60`
  (the consolidated-correction commit).
- **Confirmation date:** 2026-08-13.
- **Run:** `codex exec -s read-only -m gpt-5.6-sol -c
  model_reasoning_effort=xhigh`, sandbox `read-only`.
- **VERDICT: DESIGN INCOMPLETE (new material boundary omission).**

### Per-finding confirmation (prior findings 1-9)

| # | Prior finding | Confirmation |
|---|---|---|
| 1 | 90-day public job-log surface | **ADDRESSED** -- 3.8 inventory is honest; secret proxy-excluded; Slice-B public-log constraint named. |
| 2 | Secret boundary / ref / persist-credentials / allow-users | **ADDRESSED** -- 3.4 + req 9 bind the controls; `allow-users` correctly additive. |
| 3 | Model-output transport (injection) | **ADDRESSED** -- 3.6 + req 11 bind inert transport + injection-inertness test. |
| 4 | Bootstrap precedent / lawful NO path | **ADDRESSED** -- 9.2 accurate vs PRD-197/207/212 histories and GOV-2 section 9; false PRD-255 blocking claim withdrawn. |
| 5 | "Model receives only event JSON" over-claim | **NOT-ADDRESSED** -- see new omission below. The replacement claim (readable surface = exactly prompt/schema/tool/event) is false: `working-directory` only sets `codex exec --cd`; Codex 0.147.0 `:read-only` = `:root = read`. |
| 6 | FILES/ceiling completeness | **ADDRESSED** -- validator selected; download-artifact removed; lifecycle files enumerated; estimate revised. |
| 7 | Model identity / pin currency | **ADDRESSED** -- requested-only; served unobservable; pins reconciled to a consistent current-major SHA set. |
| 8 | Anti-stall need as fact | **ADDRESSED** -- relabeled owner product hypothesis; KEEP/NO-GO is the seam. |
| 9 | INFRA "not CONTRACT" ceremony | **NOT-ADDRESSED** -- 1.2 acknowledges the subordinate CONTRACT surface and 1.2 says the schema-diff review + full-consumer-audit ceremony is "carried into section 7," but section 7 contains no such binding requirement; req 12 is only a validator/schema equivalence test. |

### NEW MATERIAL BOUNDARY OMISSION (the DESIGN INCOMPLETE driver)

> The correction newly asserts an enumerated model-readable surface without
> covering the actual runner-wide filesystem-read transition. At pinned Codex
> 0.147.0, built-in `:read-only` grants `:root = read`; an isolated current
> directory and sparse checkout therefore do not prevent the model from reading
> the checkout's `.git` object database or other same-user-readable runner,
> action, temporary, and Codex-home paths. The model-input/trust surface -- and
> the security analysis based on it -- is materially incomplete.

Per GOV-2 sections 6 and 7 this returns the packet to `DESIGN INCOMPLETE`. The
one consolidated correction cycle GOV-1/GOV-2 authorize is spent; HELM does not
run a second cycle autonomously. See the HELM realizability note in `PACKET.md`
section 0 and the owner options recorded there.

### Isolation (Sol, verbatim)

> Fresh context, independent of the authoring session; exact head
> `8c7669ed36d36fd9d9c47aa3fee82c4479746e60` reviewed read-only, with no
> repository writes, files created, staging changes, or git changes;
> pre-existing untracked `.confirm_prompt.txt` remained untouched.

---
---

# REBUILD CYCLE (owner-ruled REBUILD, 2026-08-13)

Sections 1-3 above are the first-cycle lineage (preserved verbatim). The
following records the owner-authorized REBUILD cycle's two Codex packet-cycle
events and its one consolidated correction.

## 4. REBUILD INITIAL PACKET REVIEW

- **Event type:** `INITIAL PACKET REVIEW` (rebuild cycle).
- **Reviewer / role:** `gpt-5.6-sol`, fresh-context independent reviewer.
- **Reviewed commit SHA:** `ab958645e58e05832f44bec7a5672afa43c46880` (rebuilt
  packet with the REBUILD block).
- **Review date:** 2026-08-13. Run: `codex exec -s read-only -m gpt-5.6-sol -c
  model_reasoning_effort=xhigh`, read-only, xhigh.
- **VERDICT: DESIGN INCOMPLETE** (1 CRITICAL, 5 MAJOR; substantial
  confirmations). The review used primary sources (Codex 0.147.0 permissions.rs;
  codex-action action.yml / docs/security.md / src at `52fe01ec`; actions/runner
  `.credentials` design; GitHub runner + compromised-runner docs).

### Findings and dispositions (one consolidated rebuild correction)

Full disposition detail is in `PACKET.md` section `## R.11 REBUILD CORRECTION
CYCLE`.

| # | Sev | Finding (Sol) | Disposition |
|---|---|---|---|
| 1 | CRITICAL | Runner-root `<runner-root>/.credentials` (job-scoped Actions-service token, mode-600, owned by `runner`) is a same-uid-readable surface; `drop-sudo` does not close same-uid reads; the packet mislabeled runner/runtime tokens as sudo-only. | **ACTIONED** (R.11.F1) -- enumerate runner-root credential surfaces; withdraw the sudo-only labels; bind `safety-strategy: unprivileged-user` as the control (distinct uid), closure VERIFIED at the post-merge dry-run; `drop-sudo` downgraded to necessary-but-insufficient. |
| 2 | MAJOR | The Codex->Responses API channel and provider are omitted sinks; command-network restriction does not stop parent Responses traffic, so anything the model reads is sent upstream before any log decision. | **ACTIONED** (R.11.F2) -- add Responses runtime/proxy/request-body/provider/log/command-file/artifact consumers; bind credential unreachability (not network restriction) as the control; public log is not the only egress. |
| 3 | MAJOR | Proxy procfs analysis conflated same-uid with privilege; the API-key conclusion was only partly correct. | **ACTIONED and STRENGTHENED** (R.11.F3) -- proxy is same-uid but non-dumpable (`PR_SET_DUMPABLE=0`, fail-closed, `mlock`) with a key-free config, so `OPENAI_API_KEY` confidentiality is VERIFIED; runner-worker credential custody separated as the general platform baseline. |
| 4 | MAJOR | The no-secret-to-sink requirement contradicts the pinned action (it always writes final-message to `output.md` + `GITHUB_OUTPUT`); "no publication path" is overbroad. | **ACTIONED** (R.11.F4) -- reframe the sink rule around credential unreachability (masking is not a boundary); narrow to "no repository-authoritative / issue / PR / comment publication path." |
| 5 | MAJOR | CONTRACT ceremony textually binding but canonically incomplete; canon has no dominant-purpose rule; CONTRACT mandates full suite + adjudication on any disagreement. | **ACTIONED** (R.11.F5) -- route INFRA-vs-CONTRACT to owner adjudication; bind the full suite, schema-diff, full consumer audit, and a mandatory `PRD-302.adjudication.md` (this review is a disagreement) regardless of the label. |
| 6 | MAJOR | FILES/ceiling and "not NO-GO" cannot stay unchanged after the boundary failure. | **ACTIONED** (R.11.F6) -- ceiling re-marked ESTIMATED-PENDING-ISOLATION-IMPLEMENTATION; NO-GO disposition = not architectural NO-GO, isolation VERIFIED at the post-merge dry-run, with a named RED stop if the hosted probe cannot show closure. |

### Confirmations recorded by the rebuilt review (Sol)

Withdrawal of sparse-checkout/working-directory as confidentiality (correct);
Codex `:read-only` = root read + no write + network Restricted; public
checkout/action-cache/command-file readability; `OPENAI_API_KEY` proxy custody
(stdin, `env -u`, non-dumpable, key-free config); `persist-credentials: false`
prevents checkout-token persistence (checkout v7 default true); no `id-token` =>
no OIDC; distinctness of filesystem-read vs privilege vs credential-scope vs
command-network; `contents: read` denies mutation; MATERIAL + HIGH-RISK correct;
action pins resolve to v7.0.1 / v7.0.1 / v9.0.0 / (codex-action) with
download-artifact removed; requested-only model identity; TRIPWIRE labeling;
default-branch bootstrap; PRD-230 distinct-capability comparison. R.7 obligations
are genuinely normative (fixes first-cycle finding 9's prose defect) though not
yet canonically complete (F5).

### Isolation (Sol, verbatim)

> Fresh context, independent of the authoring session; repository and primary
> sources reviewed read-only; no repository files, index entries, commits, or
> git refs were written or changed. Reviewed exact HEAD
> `ab958645e58e05832f44bec7a5672afa43c46880`.

## 5. REBUILD CONSOLIDATED CORRECTION

One GOV-1/GOV-2 correction cycle applied to `PACKET.md` (appended as section
`## R.11`, plus the corrected R.5 smallest-claim), addressing all six rebuilt-
review findings. The security model is corrected to: API key VERIFIED protected
(non-dumpable proxy); runner-owned credentials are the genuine residual, closed
by `unprivileged-user` (proven at the post-merge dry-run); Responses channel
added as a sink; sink rule reframed around credential unreachability;
publication claim narrowed; full CONTRACT ceremony + adjudication bound and the
classification routed to owner adjudication; ceiling re-marked pending isolation
implementation. Changes are confined to `PACKET.md` and this review record. The
corrected head is recorded in section 6 once confirmed.

## 6. REBUILD EXACT-CORRECTED-HEAD CONFIRMATION

PENDING -- to be filled from the independent Codex/Sol confirmation of the
rebuilt corrected head. Confirmation scope per GOV-2 sections 5, 7: each rebuilt
finding resolved at the exact head, plus a scan for any NEW material boundary
omission introduced by the correction; the only lawful non-ACCEPT outcome is a
new omission (DESIGN INCOMPLETE) or an unprovable-on-standard-runner boundary
(the owner isolation choice / NO-GO per the rebuild charge).
