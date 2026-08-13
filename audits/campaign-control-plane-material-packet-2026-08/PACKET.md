# PRD-302 Campaign Control Plane (Slice A bootstrap) -- GOV-2 MATERIAL packet

Upstream MATERIAL design packet for the PRD-302 Slice-A bootstrap of a
campaign control plane. Authored per the GOV-2 material-review order
(`docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md`). This packet is
provisional until an independent Codex review completes, one consolidated
correction is applied, and the exact corrected head is independently confirmed
(GOV-2 sections 2, 7). It authorizes nothing downstream.

- **Base:** `origin/main` @ `ff320357e35dc4d16c80787dff9197f90c6ab0a2`
  (PR #248 merged; unchanged from the planning base, so next-free-PRD,
  workflow, secret-name, branch-protection, and precedent claims below hold
  against this exact SHA).
- **Branch:** `worktree-prd-302-material-packet` (documentation-only; GOV-2
  section 4 -- existence creates no implementation authority).
- **Date:** 2026-08-13.
- **HELM / author:** Opus 4.8 (sole driver; no Claude subagents; read-only
  Codex/Sol for the two GOV-2 review events).
- **Deliverable scope:** PRD-302 = **Slice A (bootstrap) only**. Slice B
  (issue-comment activation) is a separate future PRD with its own MATERIAL
  packet; it is described here only where Slice A's boundaries depend on it.
- **Planning inputs:** the reconciled two-slice implementation plan and the
  Fable review-reconciliation (Task-0 advisory Navigator evidence, ACCEPT
  WITH REQUIRED EDITS). Fable's review is advisory; it is neither GOV-2 Codex
  packet-review event.

---

## 0. Provisional status and authority boundary

**STATUS: ESTIMATED SURFACE -- NOT YET APPROVED** (GOV-2 section 5).

This packet grants no downstream authority. Under GOV-2 section 4, no Stage-0
PRD, registry/index/PROJECT_STATE edit, PRD allocation, Gate A, payload file,
test, workflow, schema, prompt, or implementation change is authorized by this
document or by the existence of its branch. The required order is:

```
this MATERIAL packet
-> INITIAL PACKET REVIEW (independent Codex/Sol, read-only, SHA-pinned)
-> one consolidated author correction
-> EXACT-CORRECTED-HEAD CONFIRMATION (independent Codex/Sol, read-only)
-> Dustin design-direction ruling            <-- campaign STOPS here
-> [Stage 0 PRD -> fresh-context PRD review -> Gate A -> implementation]
```

The bracketed steps are out of scope for this campaign.

**Docs-only CI claim boundary (GOV-2 section 8).** CI on this documentation
branch confirms only that the branch preserves the current green baseline. It
does not execute or validate the proposed runtime design, the secret-isolation
guarantees, the consumer inventory, or the regression plan. A docs-only
full-suite count is not evidence that any proposed implementation is complete.

---

## 1. Materiality classification and lane

### 1.1 MATERIAL: YES

Matched GOV-2 section 1 triggers (any one suffices; several apply):

- **Establishes a production FILES ceiling and a LOC ceiling** -- the packet
  proposes a five-file Slice-A FILES set and a net-added-line ceiling
  (section 8).
- **Selects an implementation seam / carrier shared across layers** -- a new
  CI workflow that invokes an external model, threads a repository secret, and
  defines the JSON event/charge carriers a future Slice B will consume.
- **Adds a persisted/coordination schema surface with more than one reader**
  -- the charge output schema is read by the model (as constraint), the
  secret-free validator, and (in Slice B) the publisher and owner.
- **Security-sensitive secret handling** -- introduces `OPENAI_API_KEY` into a
  new workflow; the trust and containment boundary is the core design object.
- **Owner discretion** -- GOV-2 section 1 lets Dustin classify any change
  MATERIAL; the intake recommendation and the Fable reconciliation both land
  on MATERIAL.

### 1.2 CLASS: INFRA

INFRA is a canonical class in the `docs/PRD_PROCESS.md` CLASS table ("CI,
hooks, artifact-push plumbing, scripts, settings"). The deliverable is a CI
workflow plus its checked-in tool, prompt, and schema -- CI/plumbing surface.

It is **not CONTRACT**: the coordination JSON schemas are internal to this
control plane and do not redefine Cuttingboard's runtime/payload contract
(`cuttingboard/output.py`, `ui/contract.json`, the `TradeDecision` shape). It
is **not EXECUTION**: it contains no trading-decision, regime, qualification,
or sizing logic. Relabeling it CONTRACT or EXECUTION merely because it invokes
a model and owns internal schemas would be a mis-classification (this is
Fable finding F5, REJECTED-after-canon-check, confirmed here against the live
CLASS table).

INFRA default tier is T1 ("T0 if hooks/CI gate runtime"). This workflow does
not gate the runtime pipeline, so its default tier is T1. The lane is forced
above the tier by R11 (below), not by the tier.

### 1.3 LANE: HIGH-RISK (forced)

Two independent forcings:

- **R11 Lane Downgrade Prohibition** -- `FILES` names
  `.github/workflows/campaign_control.yml` as this PRD's **payload**, and
  `.github/workflows/**` is the INFRA HIGH-RISK FILES entry. R11 forces
  `LANE: HIGH-RISK` regardless of diff size.
- **GOV-2 section 1 MICRO-ineligibility** -- a MATERIAL slice cannot be
  `LANE: MICRO`; with MICRO removed it takes STANDARD at minimum, and R11
  lifts it to HIGH-RISK.

**Consequences of HIGH-RISK/INFRA at closeout (recorded, not yet due):** the
COMPLETE PRD must carry either a commissioned second-model artifact
`docs/prd_history/PRD-302.review.<model>.md` (four properties: in-tree +
durable, SHA-pinned, read-only, fresh-context) or the verbatim
`SECOND-MODEL:` waiver line; `tools/validate_prd_registry.py` fails the CI
`test` check on a HIGH-RISK COMPLETE row carrying neither. A `CHANGE SURFACE`
section is mandatory (T0/T1 or HIGH-RISK FILES intersection). This packet
recommends **commissioning** the second-model artifact, not waiving it
(section 9.3).

---

## 2. What the Slice-A deliverable is

A `workflow_dispatch`-only harness that **structurally installs** the secure
shape of a Codex-invoking control plane, with no untrusted ingress and no
publication path. It:

1. constructs one fixed synthetic normalized event
   (`source_comment_id: 0`, `pr_number: 1`, `head_sha` = the trusted workflow
   ref SHA);
2. invokes pinned `openai/codex-action` with the existing `OPENAI_API_KEY`
   secret in a read-only sandbox;
3. returns schema-constrained JSON as a job output;
4. validates and renders it inside a fixed non-authority wrapper in a
   separate, secret-free job; and
5. uploads the rendered proposal as a one-day artifact.

It has **no** issue trigger, **no** issue permission, **no** comment API, and
**no** publication path. Its first behavioral proof is physically post-merge
(section 3.9 and the owner question in section 9).

---

## 3. Full trust, effect, and boundary enumeration (Slice A)

### 3.1 FILES (five, all Slice-A payload)

| Path | Bootstrap responsibility |
|---|---|
| `tools/campaign_control.py` | Synthetic-event generation, normalized-event loading, charge validation, inert rendering, CLI. No network calls. |
| `tests/test_campaign_control.py` | Unit + workflow-structure (TRIPWIRE) tests. |
| `.github/workflows/campaign_control.yml` | `workflow_dispatch` only; secret-bearing Codex job + secret-free validation/artifact job. |
| `.github/campaign/charge_prompt.md` | Read-only, non-authoritative synthesizer prompt. |
| `.github/campaign/charge.schema.json` | Strict JSON output schema (`additionalProperties: false`). |

No other repository file is touched by Slice A payload. (Registry/index
bookkeeping is implicit per `docs/PRD_PROCESS.md` Scope Lock and is not a
payload FILES entry.)

### 3.2 Trigger

`on: workflow_dispatch` **only**. Slice A structurally bans every other event:
`issue_comment`, `pull_request`, `pull_request_target`, `repository_dispatch`,
`workflow_run`, `push`, `schedule`. The ban is asserted by TRIPWIRE tests
(section 4). PyYAML's YAML-1.1 `on`/`True` key coercion is normalized
explicitly in the tests so the trigger key is read correctly.

Rationale (inherited from the PRD-197 secure pattern): a `pull_request` or
`pull_request_target` trigger from a fork would expose `OPENAI_API_KEY` to
untrusted code; dispatch-only keeps the secret on trusted, owner-initiated
runs.

### 3.3 Jobs and permissions

- Top-level `permissions: contents: read`.
- **Codex job** (secret-bearing): `contents: read` only. Holds the key via the
  action proxy; cannot write anything.
- **Validator/artifact job** (secret-free): `contents: read` only. Receives
  the model JSON as a job output, validates it, renders it, uploads a one-day
  artifact.

Slice A grants **no** `issues`, `pull-requests`, `checks`, `actions`, or
`contents: write` scope in any job.

### 3.4 Secret path (the core containment object)

`OPENAI_API_KEY` appears **exactly once**, only as the `openai-api-key` input
of the `openai/codex-action` step, which is the **literal final step** of the
Codex job. It is never a job-level or step-level `env:`, never referenced in a
`run:` step, never echoed, never written to the artifact, and never present in
the validator job. No repository code or artifact-upload step runs after the
key reaches the action proxy.

### 3.5 External actions and model identity

The five pinned actions and the codex-action inputs are enumerated with
verification status in section 6. Model-facing inputs (proposed): requested
model `gpt-5.6-sol`, `effort: xhigh`, `permission-profile: ":read-only"`,
`safety-strategy: drop-sudo`, `codex-version: 0.147.0`,
`allow-users: dwats250`, `codex-args: ["--ephemeral", "--ignore-user-config"]`.

### 3.6 Model input and output

The model receives the **normalized synthetic event JSON** as untrusted-shaped
input. It does **not** receive the raw comment stream (there is none in Slice
A) and does **not** check out the referenced PR head. It returns
schema-constrained JSON whose `final-message` becomes the Codex job output
`charge_json`.

### 3.7 Output, artifact, and consumers

The validator job validates `charge_json` against the schema, renders it inside
a fixed `PROPOSED OWNER CHARGE -- NOT AUTHORITY` wrapper with all model text
HTML-escaped, `@`-neutralized, and confined to `<pre>` blocks, and uploads the
rendered file as a **one-day retention** artifact. In Slice A the **only**
consumer is that ephemeral artifact. There is no dashboard cell, no
notification, no comment, no persisted state, no scoreboard row, no published
contract field. (Downstream-consumer audit, Author-discipline 2: the Slice-A
emission reaches no human-facing surface other than the one-day artifact a
maintainer downloads.)

### 3.8 Denied effects (negative boundary)

Slice A performs none of: issue write, comment API call, PR/branch/check/action
write, `git push`, `gh` invocation, any command after the Codex action step,
any secret in logs, any network call from the checked-in Python tool. A failure
never publishes and never echoes untrusted content.

### 3.9 Default-branch bootstrap limitation (load-bearing)

GitHub only accepts a `workflow_dispatch` (and, in Slice B, `issue_comment`)
trigger when the workflow file exists on the **default branch**
(https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).
Therefore the workflow **cannot be dispatched before it is merged to `main`**.
The first behavioral proof of the harness is physically post-merge. This is the
crux of the owner design question in section 9; it is a fact about GitHub, not
a design choice, and it invalidates any one-PR plan that promises a pre-merge
Actions run.

### 3.10 Failure paths

Every failure is generic and fail-closed: the tool emits only
`campaign-control: FAIL [stable-code] safe-message` and exits 2. Failure output
excludes event text, model output, API responses, and secrets. There is no
silent-fallback path: a malformed input, an unresolvable identity, or an
unreadable stream fails loudly (PRD-198 invariant 1).

---

## 4. Structural workflow tests are TRIPWIRES, not behavioral proof

Every YAML/shape test in `tests/test_campaign_control.py` -- trigger set,
permission scopes, single secret placement, action pins, Codex-action-final,
validation-before-upload, prohibited-command absence -- asserts that the
workflow **file says the right thing**. Each such test's name/docstring is
labeled `TRIPWIRE -- NOT BEHAVIORAL PROOF`, and a meta-test asserts that marker
remains machine-visible.

Under PRD-198 invariant 4 ("every guard ships a red test"), these tripwires
satisfy the red-test requirement for the **structural contract** only: they
fail if a future edit adds a banned trigger, moves the secret, unpins an
action, or grants a write scope. They do **not** prove the harness behaves --
that Codex authenticates, that the sandbox holds, that the schema constrains
real output, that no write occurs at runtime. Behavioral truth is determined
only where GitHub, the proxy, the action, and the served model run (PRD-198
invariant 5), i.e. the post-merge `main` dispatch (section 9). The PRD,
closeout, and merge-return language must never describe merge-time green as
behavioral proof.

---

## 5. Cuts-before-additions reconciliation (VISION; PRD-230)

This is the decisive section. VISION's `cuts-before-additions` requires an
addition to justify itself against removal, and PRD-230 already **removed** a
Codex-in-CI apparatus. The design proceeds only if this is a distinct product
capability, not that deleted apparatus returning under a new name. If the
distinction fails, the correct result is **NO-GO**.

### 5.1 What PRD-230 deleted, and why

PRD-230 deleted `.github/workflows/codex-review.yml` and
`tests/test_codex_review.py` (the PRD-197/207/212 arc). Its WHY NOW, verbatim:

> The apparatus being torn down caught one real issue (model laundering,
> PRD-207) and its marginal return is now negative: 5 PRDs, a 344-line
> workflow, and 16 review artifacts to make tamper-evident a reviewer whose
> every merge Dustin performs himself.

The deleted thing was a **review-authenticity / merge-gate satisfier**:
`codex-review.yml` produced a `docs/prd_history/PRD-NNN.review.codex.md`
artifact that **counted toward the HIGH-RISK merge gate**. To make that gate
trustworthy it needed a fail-closed model allowlist, resolved-model provenance,
and model-laundering detection (PRD-207). PRD-230's judgment was that this
authenticity upkeep had **negative marginal return in a solo repo where Dustin
performs every merge himself** -- the tamper-evidence was redundant against the
human merge seam.

### 5.2 Why PRD-302 is not that apparatus returning

| Axis | Deleted `codex-review.yml` | Proposed campaign control plane |
|---|---|---|
| Purpose | Authenticate that a genuine second-model **review** happened, to satisfy a merge gate | Surface an **owner-decision checkpoint** off-terminal and produce one copy-ready **proposal** |
| Output role | Review-of-record; **counted toward** the HIGH-RISK gate | Explicitly `NOT AUTHORITY`; gates nothing; Dustin accepts/edits/rejects |
| Model input | The PR's **repository code** at a SHA | A normalized **event JSON**; never checks out PR code |
| Authority granted | Contributed to a merge decision | Zero; cannot approve, resume, dispatch, rerun CI, resolve reviews, or merge |
| Authenticity upkeep | Allowlist-as-gate + resolved-model provenance + laundering detection + 16 artifacts | **None** -- because the proposal gates nothing, no served-model authenticity machinery is needed or built |
| Problem solved | Host-independent review gate (PRD-197) | Owner-decision coordination / anti-stall (below) |

The single most important line: the expensive part of the deleted apparatus
(the PRD-207 resolved-model authenticity machinery) existed **only because its
output counted toward a gate**. PRD-302's output counts toward nothing, so it
deliberately does not build, and does not need, that machinery. The teardown's
cost driver is absent by construction.

### 5.3 The live product need (why the addition earns its place)

The owner-authored `PRODUCT_DELIVERY_OPERATING_RULE_2026-08-06.md` names the
need directly: the Anti-stall rule requires an agent that hits friction to
"present Dustin with a bounded decision," and the Success criterion is that
"decisions arrive with bounded options" and "product slices reach Dustin
quickly." Today a local HELM campaign that reaches a genuine owner-decision
checkpoint stalls at the terminal until Dustin is present. The control plane
gives that checkpoint a GitHub-mediated carrier: a native notification plus a
bounded-options proposal Dustin can act on off-terminal. That is a
coordination/delivery capability, not a review-authenticity apparatus.

### 5.4 openai/codex-action vs the live SDK-in-run precedent

The live `macro_awareness.yml` (PRD-187) runs an LLM SDK in a `run:` step:
`ANTHROPIC_API_KEY` sits in **job-level `env:`** (line 22-23), so **every step
in that job** -- including `pip install anthropic feedparser requests` of
arbitrary network clients and `python3 tools/macro_awareness_collector.py` --
executes with the secret present, and there is no sandbox around the model
call. This proves LLM-in-CI is not categorically banned in this repo; the
question is only the containment.

The proposed `openai/codex-action` is materially tighter, and the addition is
justified **only** through the containment actually needed here:

- **Proxy-held key + final-step isolation.** The key reaches only the final
  action step via the action proxy; no repository code or artifact step runs
  after the key is introduced. Contrast the SDK pattern, where the key is live
  for the whole job.
- **Read-only sandbox + drop-sudo.** The model runs `permission-profile:
  ":read-only"` with `safety-strategy: drop-sudo`. The SDK pattern has no
  sandbox around the model's execution context.
- **Structured/schema-constrained output.** `output-schema-file` constrains the
  model to schema-valid JSON; the SDK pattern returns free text a collector
  must parse.
- **Untrusted-input trajectory.** Slice B will feed **untrusted issue-comment
  text** to this model. The containment is installed and proven in the
  bootstrap so the secure shape exists before untrusted ingress is activated.

**Honest caveat (do not overclaim).** Slice A's event is a *fixed synthetic*
input, not untrusted, so Slice A **alone** does not strictly require the
read-only sandbox for input-trust reasons. The containment is installed in the
bootstrap deliberately -- to establish and prove the secure shape before Slice
B turns on untrusted ingress -- and the final-step secret isolation plus schema
output remain worth having even for the synthetic run. This is the weakest
point of the marginal-return argument and is named as such.

### 5.5 The sharpest falsification target (for the Codex review and the owner)

PRD-302 reuses the **same secure workflow mechanism** the deleted
`codex-review.yml` used: `openai/codex-action`, read-only sandbox, key-isolated
job split. A skeptic's strongest objection is: "this is codex-review.yml with
the output relabeled from review to proposal." The rebuttal is section 5.2
(purpose, output role, coupling, and the absent authenticity upkeep all
differ), reinforced by the fact that PRD-230 killed the old apparatus for
**marginal-return**, not security -- so reusing its proven-secure mechanism for
a genuinely different, gate-free product purpose is not revival. But whether
the coordination capability carries **positive** marginal return in a solo repo
is a genuine **owner product judgment**, the same judgment PRD-230 exercised in
the other direction. The Codex review must attempt to falsify the distinction;
the owner must rule on the product value.

### 5.6 Verdict

**DISTINCT PRODUCT CAPABILITY -- not a revival of the deleted review gate.**
The design survives cuts-before-additions on purpose, output role, coupling,
and the deliberate absence of the deleted authenticity upkeep. It is **not**
NO-GO on the design merits. The one gating judgment left open is the owner's
marginal-return product ruling (section 9); if Dustin judges the coordination
value insufficient, NO-GO remains the correct and lawful outcome and no design
element here resists it.

---

## 6. Pin and identity verification table (PRD-198 invariant 6)

Verified 2026-08-13 against live official sources via `gh api
repos/<owner>/<repo>/tags` (tag -> commit SHA) and the local `codex --version`.
Labels: **VERIFIED** (resolved to a real official release/binary),
**INFERRED** (established by repository practice / owner ruling, not
independently confirmable against an external catalog here), **UNRESOLVED**.

| Identity | Proposed pin | Resolves to | Status | Disposition |
|---|---|---|---|---|
| `actions/checkout` | `d23441a48e516b6c34aea4fa41551a30e30af803` | **v6.1.0** (= current `v6`) | VERIFIED | Current; consistent with repo (`@v6`). |
| `openai/codex-action` | `52fe01ec70a42f454c9d2ebd47598f9fd6893d56` | **v1.11** (= current `v1`) | VERIFIED | Current major/minor. |
| `actions/github-script` | `f28e40c7f34bde8b3046d885e986cb6290c5673b` | **v7.1.0** | VERIFIED | Real release, but behind current `v9`. Reconcile or justify at implementation. |
| `actions/upload-artifact` | `ea165f8d65b6e75b540449e92b4886f43607fa02` | **v4.6.2** | VERIFIED | Real release, but behind current `v7`, and the repo's live workflows use `@v7`. **Version drift finding** -- reconcile to `v7` or justify `v4.6.2` before Gate A. |
| `actions/download-artifact` | `634f93cb2916e3fdff6788551b99b062d0335ce0` | **v5.0.0** | VERIFIED | Real release, but behind current `v8`. Reconcile or justify. (Slice A may not need download-artifact if the model JSON is passed as a job output rather than an uploaded artifact; confirm necessity at implementation.) |
| Codex CLI | `codex-version: 0.147.0` | local `codex-cli 0.147.0` | VERIFIED | Matches the running CLI in this environment. |
| Model (requested) | `model: gpt-5.6-sol` | live probe served `gpt-5.6-sol` | INFERRED | Established reviewer/model identity by owner ruling 2026-08-08 and landed artifacts (`gh-pr-ready .../PACKET.review.sol.md`, `PRD-293.review.sol.md`); a live read-only probe on 2026-08-13 was served `gpt-5.6-sol`. See 6.1. |

### 6.1 Requested model is not resolved model (PRD-207 lesson, binding)

The `model:` input is the **requested** identity only. The PRD-207 incident is
the cautionary case: `codex-review.yml` requested `gpt-5-codex`, a fallback
model served the run, and the gate laundered the request into a false
"resolved" claim. On this toolchain (PRD-207 finding) the Codex `--json` stream
carries **no** structured served-model field; the only served-model signal is a
structured `item.error` fallback event (request-not-honored) or the banned
prose self-report. Therefore:

- The packet and PRD must record `gpt-5.6-sol` as **requested**, never assert
  it as the **served/resolved** model.
- Because PRD-302's output is explicitly non-authoritative, served-model
  authenticity is low-stakes (a mis-served proposal is one Dustin evaluates on
  its merits and can reject) -- which is precisely why PRD-302 does **not** need
  or build the PRD-207 resolved-model authenticity machinery. This is
  consistent with section 5.2: no gate, no authenticity upkeep.

### 6.2 Pinning is more rigorous than current repo practice

The repo's live workflows pin actions by floating major tags (`@v6`, `@v7`),
not SHAs. The proposed SHA pins are therefore **more** rigorous than current
practice (aligned with PRD-198 invariant 6, "action -> commit SHA"), but the
SHAs cannot be cross-checked against in-repo usage; the external verification
above is the check. The version-currency drift (three actions behind latest;
upload-artifact diverging from the repo's live `@v7`) is a real disposition
item for the implementation slice, not a packet blocker.

---

## 7. Binding design requirements for the downstream PRD

These are the reconciled design corrections (Fable F1-F8, strengthened). They
become **binding packet requirements** the downstream PRD must honor. Each is
tagged **[A]** (Slice-A binding) or **[B]** (future Slice-B constraint --
recorded here for continuity, not authorized by PRD-302).

1. **[A] No model-authored verification field.** The charge schema has no
   field by which the model attests a live check occurred; only the (Slice-B)
   publisher appends fixed facts it actually verified. (Fable F2.)
2. **[B] Publish-time re-fetch of the OPEN PR exact head.** Immediately before
   publication the secret-free publisher re-fetches the referenced PR and
   requires it still OPEN at the event's exact head SHA; head drift fails
   closed. (Fable F2.)
3. **[B] Bot / non-owner / non-matching comments are silent successful
   no-ops.** They never enter a failure reporter, preventing an
   `issue_comment` feedback loop. (Fable F3.)
4. **[B] Failure reporter only after an owner route passes.** A generic failure
   comment is eligible only after a Dustin/OWNER event-marker or command-prefix
   route passes and a later genuine step fails. (Fable F3.)
5. **[B] Slice-B checkpoint concurrency keyed by parsed event ID, plus a final
   marker scan.** Event-ID job concurrency supplies mutual exclusion; a final
   existing-marker scan immediately before posting supplies durable
   idempotency. The invariant is **at most one checkpoint per event ID** (a
   first valid event may create a checkpoint before a later duplicate is
   rejected). (Fable F1, strengthened -- a rescan alone is TOCTOU.)
6. **[A] Additions-column LOC measurement; deletions never offset additions.**
   Both ceilings sum the additions column of `git diff --numstat`; a deletion
   never buys back an addition. (Fable F8.)
7. **[A] No issue trigger and no issue write in Slice A.** Slice A is
   dispatch-only with `contents: read` throughout.
8. **[A] The Codex action is the literal final secret-bearing job step.** No
   repository code or artifact step runs after the key reaches the proxy.

---

## 8. Provisional ceilings (GOV-2 section 5)

**STATUS: ESTIMATED SURFACE -- NOT YET APPROVED.** These are estimates, not
constraints; the first binding number is the GATE A CEILING Dustin approves on
the reviewed PRD.

- **Slice-A estimated surface:** ~550-650 added physical lines across the four
  **non-test** payload files (`tools/campaign_control.py`,
  `.github/workflows/campaign_control.yml`, `.github/campaign/charge_prompt.md`,
  `.github/campaign/charge.schema.json`), measured by summing the additions
  column of `git diff --numstat <slice-base> -- <four paths>`; deletions never
  offset additions. Test LOC (`tests/test_campaign_control.py`) is tracked
  separately and excluded from the net-production metric.
- **First-class validation surface (PRD-288/289 lesson).** The estimate counts
  as first-class -- not incidental plumbing -- the strict exact-key parsing,
  the fail-loud guards, the `neutralize()` and fixed-wrapper rendering, the
  atomic write, the stable failure codes, and the schema's closed vocabulary
  and limits. These are the bulk of the surface and are ratified-mandatory by
  the semantic-failure invariants, so they are not discounted.
- **Recommendation for Gate A (not decided here):** set the GATE A CEILING at
  the top of the estimate plus margin (the plan's proposed 650), stated as the
  single binding number on the reviewed PRD. A post-Gate-A breach is a
  stop-and-renew event (GOV-2 section 5).

---

## 9. The genuine owner design decision (surfaced, not decided)

### 9.1 The question

May PRD-302 close **COMPLETE** for the bounded deliverable **"structurally
installed bootstrap, behavioral validation pending,"** even though GitHub makes
the first behavioral proof physically post-merge (section 3.9)?

### 9.2 Precedent, options, recommendation

**Precedent (directly on point):** PRD-197 merged under a one-time explicit
bootstrapping waiver whose close condition was the first post-merge
`workflow_dispatch` run; PRD-207 deferred its first trustworthy Codex run to a
post-merge validation; PRD-212 was the second such waiver and was **flagged for
the next alignment audit** to confirm the pattern was not masking drift. The
"install now, prove on first main dispatch" shape is established, and it
carries a standing caution: repeated bootstrap waivers get audited.

**Recommended ruling: YES**, as a one-time explicit bootstrap exception, only
if all of:

- (a) the post-merge behavioral-validation limitation is **prominent** in the
  PRD, the closeout, and the merge-return language (never described as
  operationally proven at merge -- section 4);
- (b) the **first `main`-branch dispatch is recorded as named PRD-302
  behavioral evidence** (run ID, workflow SHA, action pins, artifact identity,
  validator result), mirroring the PRD-207 bootstrap-note pattern;
- (c) **Slice B remains parked** until that recorded dispatch is green; and
- (d) a **failure requires a governed correction** before any use -- it never
  justifies weakening the sandbox or schema.
- Plus (from PRD-212): **flag the repeated-bootstrap-waiver pattern for the
  next alignment audit.**

**Lawful NO alternative and its consequence.** Dustin may rule NO: PRD-302 may
not close COMPLETE at merge. Then the workflow merges with the PRD **IN
PROGRESS**, and PRD-302 closes only via a later bookkeeping PR after the
post-merge `main` dispatch is green. Consequences to weigh:

- An IN-PROGRESS PRD-302 **blocks the closeout of any later-numbered PRD**
  until it closes (PRD-255 allocated-but-unlanded rule).
- HIGH-RISK second-model disposition is CI-enforced by
  `tools/validate_prd_registry.py` **only on a COMPLETE row** (GOV-2 section
  9). Merging IN PROGRESS therefore defers that enforcement past the merge --
  i.e. the NO path **weakens the pre-merge second-model gate**, the same
  weakening GOV-2 section 9 warns about for post-merge closeout. This is a real
  argument in favor of the YES path, not against it.

### 9.3 Second-model disposition

**Recommendation: commission** the HIGH-RISK second-model artifact for the
implementation PR; do **not** take the `SECOND-MODEL:` waiver. Rationale: this
is a security-sensitive INFRA change introducing a new secret-bearing workflow;
it is exactly the contract/decision-surface + CI-semantics profile the PRD-242
advisory triggers name. (Fable owner-decision 2.)

---

## 10. RED seams and stop conditions

Stop and return to Dustin (do not improvise around) if any of these arise
during downstream work:

- The cuts-before-additions distinction (section 5) does not survive review or
  owner product judgment -> **NO-GO**.
- A secure implementation needs PR-head repository code to execute **after** the
  key is introduced.
- `OPENAI_API_KEY` must become job-level or cross-job state.
- Codex cannot run with `:read-only`, `drop-sudo`, the pinned action, and the
  action as the final step.
- Codex requires any GitHub write permission.
- A trigger beyond `workflow_dispatch` (Slice A) is required.
- FILES or an approved ceiling must expand (GOV-2 section 5 stop-and-renew).
- A schema consumer, notification audience, durable datastore, or HELM
  endpoint is added.
- Failure can look successful or expose untrusted/secret content.
- The post-merge operational dispatch is misrepresented as pre-merge evidence.
- A review finds a new material authority boundary (GOV-2 sections 6, 7 ->
  packet returns to DESIGN INCOMPLETE).

---

## 11. GOV-2 sequence status

This packet is the provisional MATERIAL packet (step 2 of the GOV-2 required
order). The two auto-commissioned Codex packet-cycle events (INITIAL PACKET
REVIEW; EXACT-CORRECTED-HEAD CONFIRMATION) and the one consolidated correction
are recorded in `PACKET.review.sol.md` in this directory. No PRD is allocated,
no Stage 0 is opened, and no Gate A is issued or inferred by this document.

**On completion of the review cycle the campaign stops at:**
`MATERIAL PACKET REVIEW-CLEAN -- HELD FOR OWNER DESIGN-DIRECTION RULING. NO
STAGE 0. NO IMPLEMENTATION.`
