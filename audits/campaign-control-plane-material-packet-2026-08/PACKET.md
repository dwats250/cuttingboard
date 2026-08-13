# PRD-302 Campaign Control Plane (Slice A bootstrap) -- GOV-2 MATERIAL packet

Upstream MATERIAL design packet for the PRD-302 Slice-A bootstrap of a
campaign control plane. Authored per the GOV-2 material-review order
(`docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md`). This packet is
provisional until the independent Codex review completes, one consolidated
correction is applied, and the exact corrected head is independently confirmed
(GOV-2 sections 2, 7). It authorizes nothing downstream.

> **REVISION:** This is the one-consolidated-correction revision. The INITIAL
> PACKET REVIEW returned `DESIGN INCOMPLETE` with 9 findings (1 CRITICAL, 6
> MAJOR, 2 MINOR); all were dispositioned in the `## CORRECTION CYCLE` section
> at the end, and the affected sections below are rewritten. The review record
> is `PACKET.review.sol.md` in this directory.
>
> **OUTCOME AT EXACT-CORRECTED-HEAD CONFIRMATION (`8c7669ed`): DESIGN
> INCOMPLETE.** The independent confirmation (`PACKET.review.sol.md` section 3)
> confirmed findings 1-4 and 6-8 ADDRESSED, but found finding 5 NOT-ADDRESSED
> and a NEW material boundary omission, plus finding 9 NOT-ADDRESSED. Per GOV-2
> sections 6-7 the packet is NOT review-clean; the single consolidated
> correction cycle is spent; HELM does not run a second cycle. **Held for the
> owner to choose: rebuild the read-surface boundary from a corrected frame,
> narrow the claim, or park.** See section 0.1.

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

### 0.1 DESIGN INCOMPLETE at exact-corrected-head confirmation

The exact-corrected-head confirmation (`8c7669ed`) returned **DESIGN
INCOMPLETE**. Two prior findings were not fully addressed and one NEW material
boundary omission was introduced by the correction. Per GOV-2 sections 6-7 this
is a hard stop: no second correction cycle runs autonomously, and the owner
chooses whether to **rebuild** the affected boundary from a corrected frame,
**narrow** the packet's claim, or **park** it.

**Unresolved item A -- runner-wide model read surface (NEW omission; the stop
driver).** The correction's finding-5 fix asserted a bounded model-readable
surface (sparse checkout + isolated working directory = only prompt, schema,
tool, event). That claim is false at pinned Codex `0.147.0`: built-in
`:read-only` grants `:root = read` (whole-filesystem read), and
`working-directory` only sets `codex exec --cd`. So the model can read the
checkout's `.git` object database (the full repository, not just the sparse
working tree) and any same-user-readable runner, action, temporary, and
Codex-home path. The model-input/trust surface -- and the secret-isolation and
PRD-230 analyses that leaned on a bounded surface -- must be redone on the true
runner-wide read boundary. Sections 3.5, 5.2, and 5.6 are affected.

**Unresolved item B -- CONTRACT ceremony not actually bound (finding 9
NOT-ADDRESSED).** Section 1.2 states the schema-diff review and full-consumer
audit are "carried into section 7," but section 7 contains no such binding
requirement (requirement 12 is only a validator/schema equivalence test). The
claim and the requirements set are inconsistent.

**HELM realizability note (attributed to HELM, not the confirmer).** Unresolved
item A is a correct property of the Codex read-only sandbox, but its *actual
Slice-A exploitability* is bounded and worth stating for the owner ruling:

- The repository is **public**, so the readable `.git` contents and reviewed
  tree are not themselves secret; reading them leaks nothing not already public.
- `OPENAI_API_KEY` is **proxy-held** by `openai/codex-action` and is never
  written to disk as a file the model could read; requirement 9's
  `persist-credentials: false` removes the `GITHUB_TOKEN` from the on-disk
  checkout. So no *repository* secret is on-disk-readable by the model in the
  corrected Slice-A design.
- The residual real risk is the *general* runner surface (other actions' temp
  files, environment, Codex home) that a filesystem-root-read model can reach --
  a property shared by any `openai/codex-action` read-only run, including the
  live precedent's SDK-in-`run:` job, which is *less* contained. The concrete
  defect here is therefore primarily that the **packet over-claimed a bounded
  read surface**, not that Slice-A is demonstrably exploitable.
- This does not, on its own, collapse the two-slice design or the PRD-230
  distinction (which rests on no-gate / no-authenticity-upkeep /
  non-authoritative output, not on the read-surface leg). It does mean the
  security analysis must be honestly rebuilt on the true read boundary before
  the packet can be review-clean.

This note is realizability context for the owner; it is **not** a HELM
resolution of the finding and **not** a second correction cycle. The lawful
next step is Dustin's (rebuild / narrow / park), per GOV-2 section 6.

---

## 1. Materiality classification and lane

### 1.1 MATERIAL: YES

Matched GOV-2 section 1 triggers (any one suffices; the first two independently
carry the conclusion, confirmed by the initial review):

- **Establishes a production FILES ceiling and a LOC ceiling** -- the packet
  proposes a five-file Slice-A payload FILES set and a net-added-line ceiling
  (section 8).
- **Selects an implementation seam / carrier shared across layers** -- a new
  CI workflow that invokes an external model, threads a repository secret, and
  defines the JSON event/charge carriers a future Slice B will consume.
- **Adds a coordination/artifact schema surface with more than one reader**
  -- the charge output schema is read by the model (as constraint), the
  secret-free validator, and (in Slice B) the publisher and owner.
- **Security-sensitive secret handling** -- introduces `OPENAI_API_KEY` into a
  new workflow; the trust and containment boundary is the core design object.

### 1.2 CLASS: INFRA (dominant purpose), with an acknowledged subordinate contract surface

INFRA is a canonical class in the `docs/PRD_PROCESS.md` CLASS table ("CI,
hooks, artifact-push plumbing, scripts, settings"). The deliverable's dominant
purpose is CI/workflow plumbing plus its checked-in tool, prompt, and schema.

**Subordinate contract surface, acknowledged (not dismissed).** The canonical
CONTRACT definition in `docs/PRD_PROCESS.md` is broader than the trading
payload: "payload schema, artifact contracts, cross-module shape definitions."
The charge/event JSON schemas ARE genuine internal artifact / job-boundary
contracts and are a real, subordinate CONTRACT-shaped surface. The class is
nonetheless **INFRA on dominant-purpose grounds**: the deliverable exists to
install CI/workflow plumbing that happens to define internal coordination
schemas; it does not modify or redefine Cuttingboard's runtime/payload contract
(`cuttingboard/output.py`, `ui/contract.json`, the `TradeDecision` shape), and
the schemas have no consumer in the trading pipeline. It is **not EXECUTION**
(no trading-decision, regime, qualification, or sizing logic). This does not
narrow the canonical CONTRACT definition to trading-only; it applies the
dominant-purpose test to a mixed-surface change (the same treatment PRD-230
gave a mixed workflow+process change). The CONTRACT-class ceremony that matters
here -- schema-diff review and full consumer audit of the internal schemas --
is carried into the design requirements (section 7) regardless of the class
label.

INFRA default tier is T1 ("T0 if hooks/CI gate runtime"). This workflow does
not gate the runtime pipeline, so its default tier is T1. The lane is forced
above the tier by R11 (below), not by the tier.

### 1.3 LANE: HIGH-RISK (forced)

Two independent forcings (both confirmed by the initial review):

- **R11 Lane Downgrade Prohibition** -- `FILES` names
  `.github/workflows/campaign_control.yml` as this PRD's **payload**, and
  `.github/workflows/**` is the INFRA HIGH-RISK FILES entry
  (`docs/PRD_PROCESS.md`). R11 forces `LANE: HIGH-RISK` regardless of diff
  size.
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
   secret in a read-only sandbox, over a minimal, isolated checkout (section
   3.5, 3.6);
3. returns schema-constrained JSON as a job output;
4. transports that job output as inert data (never spliced into shell) into a
   separate, secret-free job that validates and renders it inside a fixed
   non-authority wrapper (section 3.6);
5. uploads the rendered proposal as a one-day artifact.

It has **no** issue trigger, **no** issue permission, **no** comment API, and
**no** publication path. Its first behavioral proof is physically post-merge
(section 3.9 and the owner question in section 9).

---

## 3. Full trust, effect, and boundary enumeration (Slice A)

### 3.1 Payload FILES (five)

| Path | Bootstrap responsibility |
|---|---|
| `tools/campaign_control.py` | Synthetic-event generation, normalized-event loading, **handwritten stdlib charge validation** (section 3.11), inert rendering, CLI. No network calls. |
| `tests/test_campaign_control.py` | Unit tests, the schema-vs-validator drift-guard test (3.11), the model-output injection-inertness test (3.6), and workflow-structure (TRIPWIRE) tests. |
| `.github/workflows/campaign_control.yml` | `workflow_dispatch` only; secret-bearing Codex job + secret-free validation/artifact job. |
| `.github/campaign/charge_prompt.md` | Read-only, non-authoritative synthesizer prompt. |
| `.github/campaign/charge.schema.json` | Strict JSON schema (`additionalProperties: false`), kept in lockstep with the handwritten validator by the 3.11 drift-guard test. |

**Lifecycle / authority files (NOT payload; enumerated for honesty, per the
initial review Finding 6).** The implementation PR and its closeout will also
touch: `docs/prd_history/PRD-302.md` (the Stage-0 PRD doc);
`docs/prd_history/PRD-302.review.claude.md` and
`docs/prd_history/PRD-302.review.<model>.md` (routine + commissioned reviews);
`docs/PROJECT_STATE.md` (active-PRD **pointer** touch -- annotated per the
payload-vs-pointer rule, obliging a fresh-context review; NOT implicit); and
this packet plus its review records (design documentation). Registry
(`docs/PRD_REGISTRY.md`) and index (`docs/prd_index.json`) bookkeeping is
implicit per `docs/PRD_PROCESS.md` Scope Lock and is not enumerated in FILES.
No new dependency file (`pyproject.toml`) is touched because validation is
handwritten stdlib (3.11).

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
  action proxy; cannot write anything. Checkout uses
  `persist-credentials: false` and a minimal sparse checkout (3.5).
- **Validator/artifact job** (secret-free): `contents: read` only. Receives
  the model JSON as a job output, transports it as inert data (3.6), validates
  it, renders it, uploads a one-day artifact.

Slice A grants **no** `issues`, `pull-requests`, `checks`, `actions`, or
`contents: write` scope in any job.

### 3.4 Secret path and its enforceable boundary (revised per Finding 2)

`OPENAI_API_KEY` appears **exactly once**, only as the `openai-api-key` input
of the `openai/codex-action` step, which is the **literal final step** of the
Codex job. It is never a job-level or step-level `env:`, never referenced in a
`run:` step, never echoed, never written to the artifact, and never present in
the validator job. No repository code or artifact-upload step runs after the
key reaches the action proxy.

Those properties are **necessary but not a complete boundary** (initial review
Finding 2). Binding additions:

- **Bind the secret-bearing run to reviewed `main`.** `workflow_dispatch`
  offers a branch selector, so "the workflow exists on the default branch" does
  not by itself prove the run uses reviewed `main` code (the live
  `macro_awareness.yml:28-35` acknowledges exactly this). Slice A binds
  `ref: main` on the Codex-job checkout and a `github.ref == 'refs/heads/main'`
  guard; but see the next point for why that alone is insufficient.
- **Prefer a protected Environment deployment-branch policy for the secret.**
  A predicate inside a workflow file that a dispatcher could run from a
  modified branch is not equivalent to environment-level secret restriction.
  The design REQUIRES one of: (a) move `OPENAI_API_KEY` into a GitHub
  Environment whose deployment-branch rule restricts it to `main` (recommended;
  GitHub enforces this regardless of which workflow-file revision runs); or (b)
  the owner **explicitly accepts the sole-writer threat model** and it is
  documented. Under current live state only `dwats250` has write access (so no
  presently-known second dispatcher), which bounds the residual, but this must
  be an explicit owner acceptance, not a silent assumption. This is part of the
  owner design-direction ruling (section 9).
- **`allow-users` is additive, not a deny-by-default allowlist** (Finding 2).
  `openai/codex-action`'s `allow-users` permits the listed users **in addition
  to** actors with repository write access; it is not owner-only. The real
  actor control is that `workflow_dispatch` requires write access, combined with
  the Environment/branch policy above. The packet records `allow-users:
  dwats250` as defense-in-depth, not as the primary actor gate.
- **`persist-credentials: false`** on every checkout in the Codex job, so the
  `GITHUB_TOKEN` is not left on disk under `$RUNNER_TEMP` where the
  filesystem-read-capable model could read it (Finding 2).

### 3.5 Minimal, isolated checkout and the model's readable surface (revised per Finding 5)

The earlier claim that "the model receives only event JSON" was over-claimed:
`actions/checkout` makes the whole reviewed tree readable and
`openai/codex-action` defaults its working directory to the repository root.
The truthful boundary and its binding controls:

- The model does **not** check out the referenced PR head (true, and the real
  distinction from the deleted gate -- section 5).
- The Codex job uses a **minimal sparse checkout** limited to
  `.github/campaign/charge_prompt.md`, `.github/campaign/charge.schema.json`,
  and `tools/campaign_control.py`, and runs the action in an **isolated
  working directory** whose readable contents are exactly the prompt, the
  schema, the synthetic event file, and that tool. A TRIPWIRE test asserts the
  sparse-checkout paths and working-directory isolation.
- The model's readable input surface is therefore **enumerated**: the synthetic
  event JSON (untrusted-shaped but fixed), plus the prompt, schema, and tool
  above -- and, if any project-instruction file (e.g. `AGENTS.md`) would fall
  inside the isolated directory, it is enumerated too. The prompt-injection,
  consumer, secret, and PRD-230 analyses are done against this truthful,
  bounded surface, not against a false "event JSON only" claim.

### 3.6 Model output transport (new, per Finding 3)

Model-controlled `charge_json` is untrusted data and must never enter shell or
workflow-command syntax before validation. Binding transport:

- The Codex job output is consumed only via a step `env:` variable (or a
  command file) and passed as **quoted input** to the checked-in Python tool
  and to pinned `actions/github-script`; it is **never** interpolated into a
  `run:` body, a filename, an artifact name, a workflow command
  (`::set-output::` / `::notice::` etc.), or any shell syntax. Direct
  `${{ needs.codex.outputs.charge_json }}` splicing into `run:` is prohibited
  (it would be pre-validation expression/shell injection).
- A mutation/red test feeds `charge_json` values containing `"`, `'`, newlines,
  `$()`, backticks, `${{ }}`, and `::workflow-command::` strings and proves
  they remain inert data through transport, validation, and rendering.

### 3.7 Model input and output (semantics)

The model receives the **normalized synthetic event JSON** as untrusted-shaped
input (plus the enumerated trusted files of 3.5). It does **not** receive a raw
comment stream (there is none in Slice A) and does **not** check out the
referenced PR head. It returns schema-constrained JSON whose `final-message`
becomes the Codex job output `charge_json`.

### 3.8 Producer-to-final-consumer surface inventory (rewritten per Finding 1)

The earlier "one-day artifact is the only surface" claim was wrong. GOV-2
section 6 producer-to-final-consumer inventory for Slice A:

| Surface | Persistence | What reaches it | Trust note |
|---|---|---|---|
| Codex action step **stdout** | in the Actions **job log** | the raw model final message (PRD-207 confirms Codex output reaches the completed job log) | The **secret never reaches it** (proxy-held, not echoed). The raw proposal text DOES appear here. |
| Actions **job log** | **~90 days**, and this repository is **public** so the log is **publicly readable**; `retention-days: 1` on the artifact does NOT shorten the job log | the raw proposal text + workflow diagnostics | In Slice A the proposal is derived from the FIXED SYNTHETIC event -- no untrusted third-party content -- so public 90-day log persistence is benign. See the Slice-B constraint below. |
| check/run UI | run lifetime | job status, step names | no untrusted content |
| Codex job **output** (`charge_json`) | run lifetime | model JSON | transported as inert data (3.6) |
| uploaded **artifact** | **1 day** | the rendered, wrapped, neutralized proposal | HTML-escaped, `@`-neutralized, `<pre>`-confined, fixed NOT-AUTHORITY wrapper |
| artifact **downloader** (a maintainer) | -- | the rendered proposal | the only intended human surface |
| human **owner** | -- | the rendered proposal | evaluates on merits |

Consequences recorded honestly:

- The neutralization/wrapper hardening governs **only the uploaded artifact**,
  not the raw job log. The job log carries the raw model text for ~90 days,
  publicly.
- **Slice A is safe** because its model input is synthetic, so nothing
  untrusted or third-party reaches the public log, and the secret is excluded
  from all logs.
- **Named Slice-B design constraint (not authorized here):** in Slice B the
  model input includes **untrusted issue-comment text**, so that text and the
  model's output would persist in the **public** Actions job log for ~90 days,
  and log content **cannot be neutralized** the way the artifact is. Slice B's
  MATERIAL packet must design for public raw-log persistence of untrusted text
  (e.g. minimize what the model echoes, accept the exposure explicitly, or
  change the carrier). This is surfaced now so the boundary is not rediscovered
  late.

### 3.9 Default-branch bootstrap limitation (load-bearing)

GitHub only accepts a `workflow_dispatch` (and, in Slice B, `issue_comment`)
trigger when the workflow file exists on the **default branch**
(https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).
Therefore the workflow **cannot be dispatched before it is merged to `main`**.
The first behavioral proof of the harness is physically post-merge. This is the
crux of the owner design question in section 9; it is a fact about GitHub, not
a design choice, and it invalidates any one-PR plan that promises a pre-merge
Actions run. (Confirmed by the initial review.)

### 3.10 Denied effects and failure paths

Slice A performs none of: issue write, comment API call, PR/branch/check/action
write, `git push`, `gh` invocation, any command after the Codex action step,
any secret in logs, any network call from the checked-in Python tool. Every
failure is generic and fail-closed: the tool emits only
`campaign-control: FAIL [stable-code] safe-message` and exits 2; failure output
excludes event text, model output, API responses, and secrets. There is no
silent-fallback path (PRD-198 invariant 1).

### 3.11 Validator mechanism (new, per Finding 6)

Validation is **handwritten stdlib** inside `tools/campaign_control.py`
(consistent with the tool's stdlib-only constraint): strict exact-key parsing
enforcing the same closed vocabulary, patterns, and limits as
`.github/campaign/charge.schema.json`. To keep the Python contract and the JSON
schema from drifting while still truthfully "validating against the schema," a
**drift-guard test** asserts that the handwritten validator and the schema
accept/reject the same closed vocabulary (required keys, enums, patterns,
limits, `additionalProperties: false`). This adds **no** third-party dependency
(no `jsonschema`), so `pyproject.toml` is not in FILES. The counterfactual --
using a `jsonschema` dependency -- would add a dependency + config surface to
FILES and is deliberately not chosen.

---

## 4. Structural workflow tests are TRIPWIRES, not behavioral proof

Every YAML/shape test in `tests/test_campaign_control.py` -- trigger set,
permission scopes, single secret placement, `persist-credentials: false`,
sparse-checkout paths, `ref: main` binding, action pins, Codex-action-final,
inert-transport, validation-before-upload, prohibited-command absence --
asserts that the workflow **file says the right thing**. Each such test's
name/docstring is labeled `TRIPWIRE -- NOT BEHAVIORAL PROOF`, and a meta-test
asserts that marker remains machine-visible.

Under PRD-198 invariant 4 ("every guard ships a red test"), these tripwires
satisfy the red-test requirement for the **structural contract** only: they
fail if a future edit adds a banned trigger, moves the secret, unpins an
action, drops `persist-credentials: false`, or grants a write scope. They do
**not** prove the harness behaves -- that Codex authenticates, that the sandbox
holds, that the schema constrains real output, that no write occurs at runtime.
Behavioral truth is determined only where GitHub, the proxy, the action, and
the served model run (PRD-198 invariant 5), i.e. the post-merge `main` dispatch
(section 9). The PRD, closeout, and merge-return language must never describe
merge-time green as behavioral proof. (Confirmed by the initial review.)

The runtime-data guards that CAN be tested behaviorally in CI -- the schema/
validator drift guard (3.11) and the model-output injection-inertness test
(3.6) -- are genuine behavioral tests and are not tripwires; they run against
the checked-in Python, not the live workflow.

---

## 5. Cuts-before-additions reconciliation (VISION; PRD-230)

VISION's `cuts-before-additions` requires an addition to justify itself against
removal, and PRD-230 already **removed** a Codex-in-CI apparatus. The design
proceeds only if this is a distinct product capability, not that deleted
apparatus returning under a new name. If the distinction fails, the correct
result is **NO-GO**. (The initial review CONFIRMED the distinction is genuine
and "not automatically NO-GO"; the corrections below tighten the two axes it
flagged -- repository-input and the no-gate coupling -- and preserve the
owner's marginal-return ruling as the real seam.)

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
| Model input | The PR's **repository code** at a SHA (the review's whole subject) | A normalized **event JSON** + an enumerated, minimal trusted checkout (3.5); never the PR head; the repo tree is not the review subject |
| Authority granted | Contributed to a merge decision | Zero; cannot approve, resume, dispatch, rerun CI, resolve reviews, or merge |
| Authenticity upkeep | Allowlist-as-gate + resolved-model provenance + laundering detection + 16 artifacts | **None** -- because the proposal gates nothing, no served-model authenticity machinery is needed or built |
| Problem solved | Host-independent review gate (PRD-197) | Owner-decision coordination / anti-stall (section 5.3) |

The load-bearing line: the expensive part of the deleted apparatus (the PRD-207
resolved-model authenticity machinery) existed **only because its output
counted toward a gate**. PRD-302's output counts toward nothing, so it
deliberately does not build, and does not need, that machinery. The teardown's
cost driver is absent by construction. (Finding 5 correctly tightened the
"model input" row: the distinction is "never the PR head + minimal enumerated
checkout," not the over-claimed "event JSON only.")

### 5.3 The product need is an owner hypothesis, not a repository-established fact (revised per Finding 8)

The owner-authored `PRODUCT_DELIVERY_OPERATING_RULE_2026-08-06.md` requires an
agent that hits friction to "present Dustin with a bounded decision" and states
the Success criterion that "decisions arrive with bounded options" and "product
slices reach Dustin quickly." That establishes that bounded owner decisions are
valued and should reach Dustin quickly. It does **not** establish, as
repository fact, that the current terminal carrier is inadequate, that
off-terminal stalls have actually occurred at a material frequency, or that an
LLM-in-CI proposal is the necessary remedy. Those are a **product hypothesis**:
that a GitHub-mediated, off-terminal owner-decision checkpoint with a
bounded-options proposal has positive marginal return over the status quo. The
KEEP / NO-GO ruling on that hypothesis is Dustin's, and it is the actual
cuts-before-additions seam (section 9).

### 5.4 openai/codex-action vs the live SDK-in-run precedent

The live `macro_awareness.yml` (PRD-187) runs an LLM SDK in a `run:` step:
`ANTHROPIC_API_KEY` sits in **job-level `env:`** (lines 22-23), so **every step
in that job** -- including `pip install anthropic feedparser requests` and
`python3 tools/macro_awareness_collector.py` -- executes with the secret
present, and there is no sandbox around the model call. This proves LLM-in-CI is
not categorically banned in this repo; the question is only the containment.

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

### 5.5 The sharpest falsification target (for the owner)

PRD-302 reuses the **same secure workflow mechanism** the deleted
`codex-review.yml` used: `openai/codex-action`, read-only sandbox, key-isolated
job split. The strongest objection is: "this is codex-review.yml with the
output relabeled from review to proposal." The rebuttal is section 5.2
(purpose, output role, coupling, and the absent authenticity upkeep all
differ), reinforced by the fact that PRD-230 killed the old apparatus for
**marginal-return**, not security -- so reusing its proven-secure mechanism for
a genuinely different, gate-free product purpose is not revival. The initial
review CONFIRMED this. But whether the coordination capability carries
**positive** marginal return in a solo repo is a genuine **owner product
judgment**, the same judgment PRD-230 exercised in the other direction.

### 5.6 Verdict

**DISTINCT PRODUCT CAPABILITY -- not a revival of the deleted review gate**
(confirmed by the initial review). The design survives cuts-before-additions on
purpose, output role, coupling, and the deliberate absence of the deleted
authenticity upkeep. It is **not** NO-GO on the design merits. The one gating
judgment left open is the owner's marginal-return product ruling on the
section-5.3 hypothesis (section 9); if Dustin judges the coordination value
insufficient, NO-GO remains the correct and lawful outcome and no design
element here resists it.

---

## 6. Pin and identity verification table (PRD-198 invariant 6)

Verified 2026-08-13 against live official sources via `gh api
repos/<owner>/<repo>/tags` (tag -> commit SHA) and the local `codex --version`.
Labels: **VERIFIED** (resolved to a real official release/binary),
**INFERRED** (established by repository practice / owner ruling, not
independently confirmable against an external catalog here), **UNRESOLVED**.

Per Finding 7 the action pins are **reconciled now** to a single, consistent,
current-major, SHA-pinned set; `download-artifact` is **removed** (no Slice-A
data-flow responsibility -- Finding 6). Behavioral-compatibility of the current
majors is an implementation check.

| Action / identity | Reconciled pin (current major) | Resolves to | Status | Note |
|---|---|---|---|---|
| `actions/checkout` | `3d3c42e5aac5ba805825da76410c181273ba90b1` | **v7.0.1** (= `v7`) | VERIFIED | Was proposed at v6.1.0 (behind current major v7); reconciled up to v7. |
| `actions/upload-artifact` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` | **v7.0.1** (= `v7`) | VERIFIED | Was proposed at v4.6.2 (diverged from repo's live `@v7`); reconciled to v7 (matches repo). |
| `actions/github-script` | `3a2844b7e9c422d3c10d287c895573f7108da1b3` | **v9.0.0** (= `v9`) | VERIFIED | Was proposed at v7.1.0 (behind v9); reconciled up to v9. Responsibility: inert-data transport + secret-free write (3.6). |
| `openai/codex-action` | `52fe01ec70a42f454c9d2ebd47598f9fd6893d56` | **v1.11** (= `v1`) | VERIFIED | Current; unchanged. |
| `actions/download-artifact` | **REMOVED from Slice A** | -- | n/a | No Slice-A data flow; unearned supply-chain surface under cuts-before-additions (Finding 6). |
| Codex CLI | `codex-version: 0.147.0` | local `codex-cli 0.147.0` | VERIFIED | Matches the running CLI in this environment. |
| Model (requested) | `model: gpt-5.6-sol` | -- | **REQUESTED ONLY** | See 6.1. Served identity is **not positively observable** on this toolchain (PRD-207); recorded as requested, never as resolved/served. |

### 6.1 Requested model is not resolved model (PRD-207 lesson, binding; Finding 7)

The `model:` input is the **requested** identity only. The earlier table's
"live probe served gpt-5.6-sol" was an internal contradiction and is removed: a
`codex exec` run banner echoes the **requested/configured** model, which is
exactly the proxy the PRD-207 incident showed can diverge from the served model
(`codex-review.yml` requested `gpt-5-codex`, a fallback served the run, and the
gate laundered the request into a false "resolved" claim). On this toolchain
(PRD-207 finding) the Codex `--json` stream carries **no** structured
served-model field. Therefore:

- The packet and PRD record `gpt-5.6-sol` as **requested**; the served identity
  is **unresolved / not positively observable** and is never asserted as
  resolved.
- If the rendered artifact is retained without an honor gate, its fixed wrapper
  must disclose "requested model; served identity unverified."
- Because PRD-302's output is explicitly non-authoritative, served-model
  authenticity is low-stakes (a mis-served proposal is one Dustin evaluates on
  its merits and can reject) -- which is precisely why PRD-302 does **not** need
  or build the PRD-207 resolved-model authenticity machinery (consistent with
  section 5.2: no gate, no authenticity upkeep).

### 6.2 Pinning is more rigorous than current repo practice

The repo's live workflows pin actions by floating major tags (`@v6`, `@v7`),
not SHAs. The reconciled SHA pins above are therefore **more** rigorous than
current practice (aligned with PRD-198 invariant 6, "action -> commit SHA") and
are now consistent (all current majors) rather than a mix of old and new.

---

## 7. Binding design requirements for the downstream PRD

These are the reconciled design corrections (Fable F1-F8, strengthened, plus
the initial-review corrections). They become **binding packet requirements**
the downstream PRD must honor. Each is tagged **[A]** (Slice-A binding) or
**[B]** (future Slice-B constraint -- recorded for continuity, not authorized
by PRD-302).

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
   idempotency. Invariant: **at most one checkpoint per event ID**. (Fable F1.)
6. **[A] Additions-column LOC measurement; deletions never offset additions.**
   Both ceilings sum the additions column of `git diff --numstat`. (Fable F8.)
7. **[A] No issue trigger and no issue write in Slice A.** Dispatch-only with
   `contents: read` throughout.
8. **[A] The Codex action is the literal final secret-bearing job step.** No
   repository code or artifact step runs after the key reaches the proxy.
9. **[A] Secret-run controls (Finding 2):** `persist-credentials: false` on
   every Codex-job checkout; bind `ref: main` + a `github.ref` guard; AND
   either a protected Environment restricting `OPENAI_API_KEY` to `main` or an
   explicit owner acceptance of the sole-writer threat model. `allow-users` is
   documented as additive defense-in-depth, not the primary actor gate.
10. **[A] Minimal, isolated model checkout (Finding 5):** sparse checkout of
    only the prompt, schema, and tool; isolated working directory; the model's
    readable surface enumerated and TRIPWIRE-asserted.
11. **[A] Inert model-output transport (Finding 3):** job output -> `env:` /
    command file -> quoted input via pinned `github-script`; never spliced into
    `run:`, filenames, artifact names, or workflow commands; injection-inertness
    mutation test.
12. **[A] Handwritten stdlib validator + schema drift-guard test (Finding 6):**
    no new dependency; a test asserts the Python validator and the JSON schema
    accept/reject the same closed vocabulary.
13. **[A] Model identity recorded as requested only (Finding 7);** served
    identity never asserted; artifact wrapper discloses "requested model;
    served identity unverified" if retained without an honor gate.
14. **[A] Reconciled current-major SHA-pinned actions (Finding 7);**
    `download-artifact` removed unless a data-flow responsibility is added.

---

## 8. Provisional ceilings (GOV-2 section 5)

**STATUS: ESTIMATED SURFACE -- NOT YET APPROVED.** These are estimates, not
constraints; the first binding number is the GATE A CEILING Dustin approves on
the reviewed PRD.

- **Slice-A estimated surface:** ~600-720 added physical lines across the four
  **non-test** payload files (`tools/campaign_control.py`,
  `.github/workflows/campaign_control.yml`, `.github/campaign/charge_prompt.md`,
  `.github/campaign/charge.schema.json`), measured by summing the additions
  column of `git diff --numstat <slice-base> -- <four paths>`; deletions never
  offset additions. The range rose from the initial ~550-650 because the
  validator is now **handwritten stdlib** (Finding 6) rather than a
  dependency-backed one, adding validation surface to `campaign_control.py`.
  Test LOC (`tests/test_campaign_control.py`) is tracked separately and
  excluded from the net-production metric.
- **First-class validation surface (PRD-288/289 lesson; method CONFIRMED by the
  initial review).** The estimate counts as first-class -- not incidental
  plumbing -- the strict exact-key parsing, the schema/validator drift guard,
  the fail-loud guards, the `neutralize()` and fixed-wrapper rendering, the
  atomic write, the stable failure codes, the inert-transport handling, and the
  schema's closed vocabulary and limits. These are the bulk of the surface and
  are ratified-mandatory by the semantic-failure invariants.
- **Recommendation for Gate A (not decided here):** set the GATE A CEILING at
  the top of the estimate plus margin, stated as the single binding number on
  the reviewed PRD. A post-Gate-A breach is a stop-and-renew event (GOV-2
  section 5). The number remains provisional until implementation resolves the
  now-specified surface (validator, transport, checkout isolation).

---

## 9. The genuine owner design decision (surfaced, not decided)

### 9.1 The question

May PRD-302 close **COMPLETE** for the bounded deliverable **"structurally
installed bootstrap, behavioral validation pending,"** even though GitHub makes
the first behavioral proof physically post-merge (section 3.9)?

### 9.2 Current law, corrected (per Finding 4)

The precedent must be stated accurately. PRD-197, PRD-207, and PRD-212 did
**not** close COMPLETE-at-install. Each **merged with the PRD `IN PROGRESS`**
and closed COMPLETE only **later**, after post-merge validation/closeout
(PRD-197 merge `cc3ecb4`/`761eac4` carried `STATUS: IN PROGRESS` and no
`PRD-197.review.codex.md` exists; PRD-207 merge `55f9cd2` was `IN PROGRESS`,
closed at `847db58`; PRD-212 impl `daedf10` was `IN PROGRESS`, closed at
`bb05721`, and its validation premise was later falsified). So they are
precedent for "merge IN PROGRESS, prove post-merge, close later" -- which is
exactly the pattern **current GOV-2 section 9 now restricts** for HIGH-RISK:
moving HIGH-RISK closeout after merge weakens the second-model enforcement
(enforced by the validator only on a COMPLETE row) and requires a separate
code-touching PRD that first adds equivalent pre-merge enforcement for IN
PROGRESS implementation PRDs. Until that lands, same-PR closeout (PRD-229) is
mandatory.

Two corrections to the earlier draft, both material:

- The earlier "lawful NO alternative = merge IN PROGRESS, bookkeeping PR later"
  is **not presently lawful** for HIGH-RISK without the GOV-2 section 9
  enforcement PRD first.
- The earlier claim that a landed `IN PROGRESS` PRD-302 "blocks the closeout of
  any later-numbered PRD" is **false**: the PRD-255 rule blocks on an allocated
  number whose **document has not landed on `main`**; once the doc is on
  `main`, any status (including IN PROGRESS) suffices. That claim is withdrawn.
- Retained and accurate: an IN PROGRESS merge would **defer the HIGH-RISK
  second-model check** past merge (GOV-2 section 9) -- an argument **for**
  same-PR closeout, i.e. for the YES framing below.

### 9.3 Options and recommendation

**Recommended ruling: YES**, framed lawfully under current closeout law -- the
bounded **COMPLETE deliverable is the structural installation**, closed via
**same-PR closeout at merge** (which keeps the HIGH-RISK second-model
enforcement at merge), with **post-merge behavioral validation as a named,
non-closeout follow-up**. Conditions:

- (a) the post-merge behavioral-validation limitation is **prominent** in the
  PRD, the closeout, and the merge-return language, and merge-time green is
  never described as behavioral proof (section 4);
- (b) the **first `main`-branch dispatch is recorded as named PRD-302
  behavioral evidence** (run ID, workflow SHA, action pins, artifact identity,
  validator result) -- recorded as follow-up evidence, not as a closeout
  condition;
- (c) **Slice B remains parked** until that recorded dispatch is green; and
- (d) a **failure requires a governed correction** before any use -- it never
  justifies weakening the sandbox or schema.
- Plus: **flag the bootstrap-close pattern for the next alignment audit**
  (PRD-212 established that repeated bootstrap waivers get audited).

**Lawful alternatives (the real fork):**

- **YES (recommended):** structural-install-as-COMPLETE, same-PR closeout,
  named post-merge validation follow-up (above).
- **NO / defer:** either (i) require the GOV-2 section 9 pre-merge-enforcement
  PRD to land first if Dustin wants behavioral proof to be part of acceptance
  before a COMPLETE flip is permitted; or (ii) narrow or park the capability
  (the cuts-before-additions NO-GO of section 5.3/5.6). Consequence of (i): a
  new dependency PRD before PRD-302 can proceed. Consequence of (ii): the
  coordination capability is not built this way.

### 9.4 Second-model disposition

**Recommendation: commission** the HIGH-RISK second-model artifact for the
implementation PR; do **not** take the `SECOND-MODEL:` waiver. Rationale: this
is a security-sensitive INFRA change introducing a new secret-bearing workflow
with a subordinate internal contract surface; it is exactly the
contract/decision-surface + CI-semantics profile the PRD-242 advisory triggers
name. (Fable owner-decision 2.)

---

## 10. RED seams and stop conditions

Stop and return to Dustin (do not improvise around) if any of these arise
during downstream work:

- The cuts-before-additions distinction (section 5) does not survive owner
  product judgment -> **NO-GO**.
- A secure implementation needs PR-head repository code to execute **after** the
  key is introduced.
- `OPENAI_API_KEY` must become job-level or cross-job state.
- The model's readable surface cannot be bounded to the enumerated minimal
  checkout (Finding 5).
- Model output cannot be transported as inert data without shell/command
  exposure (Finding 3).
- Codex cannot run with `:read-only`, `drop-sudo`, the pinned action, and the
  action as the final step.
- Codex requires any GitHub write permission.
- A trigger beyond `workflow_dispatch` (Slice A) is required.
- FILES or an approved ceiling must expand (GOV-2 section 5 stop-and-renew).
- A schema consumer, notification audience, durable datastore, or HELM
  endpoint is added.
- Failure can look successful or expose secret content; or the **public** raw
  job log would carry untrusted third-party content (a Slice-B boundary --
  section 3.8).
- The post-merge operational dispatch is misrepresented as pre-merge evidence.
- A review finds a new material authority boundary (GOV-2 sections 6, 7 ->
  packet returns to DESIGN INCOMPLETE).

---

## 11. GOV-2 sequence status

This packet completed the bounded GOV-2 packet cycle: INITIAL PACKET REVIEW
(DESIGN INCOMPLETE, 9 findings) -> one consolidated correction (all nine
addressed) -> EXACT-CORRECTED-HEAD CONFIRMATION at `8c7669ed`. Both
auto-commissioned Codex packet-cycle events and the single correction are
recorded in `PACKET.review.sol.md`. No PRD is allocated, no Stage 0 is opened,
and no Gate A is issued or inferred by this document.

The confirmation returned **DESIGN INCOMPLETE (new material boundary
omission)**. The single consolidated correction cycle is spent; HELM does not
run a second cycle (GOV-2 sections 6-7). The packet is therefore **not
review-clean**.

**The campaign stops at:**
`PRD-302 MATERIAL PACKET -- DESIGN INCOMPLETE AT EXACT-HEAD CONFIRMATION --
HELD FOR OWNER (REBUILD / NARROW / PARK). NO STAGE 0. NO IMPLEMENTATION.`

---

## CORRECTION CYCLE (one consolidated cycle, GOV-2 sections 2, 7)

Initial review: `PACKET.review.sol.md` section 1 (reviewed head
`3de08a35118764fe0df5847d6ad8216659c45142`, `gpt-5.6-sol`, read-only, xhigh).
Verdict `DESIGN INCOMPLETE`, 9 findings. All dispositioned here; this is the one
consolidated correction GOV-1/GOV-2 authorize. No second cycle is improvised;
if the exact-corrected-head confirmation finds a NEW material boundary omission,
the packet returns to `DESIGN INCOMPLETE` for the owner (GOV-2 sections 6, 7).

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | CRITICAL | Raw model output has an omitted ~90-day public job-log presentation path | **ACTIONED.** Section 3.8 rewritten as a full producer-to-final-consumer inventory (GOV-2 section 6 first-class refresh): job log = ~90-day, public, carries raw proposal; secret proxy-excluded; Slice A synthetic = benign; Slice B untrusted-text-to-public-log named as a Slice-B design constraint. "Only surface" claim removed. |
| 2 | MAJOR | Secret boundary does not bind the ref or remove checkout credentials; `allow-users` mischaracterized | **ACTIONED.** Section 3.4 + req 9: `persist-credentials: false`; bind `ref: main` + `github.ref` guard; protected Environment secret restriction OR explicit owner sole-writer acceptance; `allow-users` recorded as additive defense-in-depth, not the primary gate. |
| 3 | MAJOR | Model-output-to-validator transport unspecified (shell injection) | **ACTIONED.** New section 3.6 + req 11: job output -> `env:`/command file -> quoted input via pinned github-script; never spliced into `run:`/filenames/commands; injection-inertness mutation test. |
| 4 | MAJOR | Bootstrap precedent and "lawful NO" path misstated | **ACTIONED.** Section 9.2 rewritten to current law: PRD-197/207/212 merged IN PROGRESS and closed later (not COMPLETE-at-install); the "merge IN PROGRESS then bookkeeping PR" NO path is not presently lawful for HIGH-RISK (GOV-2 section 9); the false later-numbered-closeout-blocking claim withdrawn; YES reframed as structural-install-as-COMPLETE via same-PR closeout with named post-merge follow-up; the deferred-second-model-check point retained. |
| 5 | MAJOR | "Model receives only event JSON / never checks out repo code" over-claimed | **ACTIONED.** Section 3.5 + req 10: minimal sparse checkout (prompt/schema/tool), isolated working directory, enumerated readable surface, TRIPWIRE-asserted; section 5.2 "model input" row corrected to "never the PR head + minimal enumerated checkout." |
| 6 | MAJOR | Five-file FILES set + ceiling not yet reviewable as complete | **ACTIONED.** Section 3.11: handwritten stdlib validator + schema drift-guard test (no new dep, no pyproject.toml in FILES). Section 6: `download-artifact` removed (unearned); github-script given the explicit transport responsibility. Section 3.1: lifecycle/authority files (PRD doc, review artifacts, PROJECT_STATE pointer) enumerated separately from payload; registry/index noted implicit. Section 8: estimate revised to ~600-720 for the handwritten validator. |
| 7 | MAJOR | Model-identity row records an unsupported resolved identity; pin currency inconsistent | **ACTIONED.** Section 6.1: `gpt-5.6-sol` recorded as requested only; served identity not positively observable (PRD-207); "live probe served" removed; wrapper-disclosure requirement added. Section 6: action pins reconciled now to a consistent current-major SHA set (checkout v7.0.1, upload-artifact v7.0.1, github-script v9.0.0, codex-action v1.11), download-artifact removed. |
| 8 | MINOR | Anti-stall doc does not establish the off-terminal need as fact | **ACTIONED.** Section 5.3 relabels off-terminal value as an owner product hypothesis, not repository-established fact; the KEEP/NO-GO ruling is the cuts-before-additions seam. |
| 9 | MINOR | INFRA "not CONTRACT" rationale narrows the canonical definition | **ACTIONED.** Section 1.2 keeps INFRA on dominant-purpose grounds, explicitly acknowledges the subordinate internal-contract surface, carries the schema-diff/consumer-audit ceremony into section 7, and does not redefine CONTRACT as trading-only. |

Confirmations recorded by the initial review (no change required): materiality;
CLASS INFRA (dominant) / LANE HIGH-RISK forcing; the default-branch bootstrap
fact; the good secret-hygiene elements (as necessary-not-sufficient); the
structural-test tripwire honesty; PRD-230 non-revival as genuine; and the
ceiling estimation method (number pending Finding 6, now resolved).

---
---

# REBUILD (owner-authorized 2026-08-13; GOV-2 section 6 ruling: REBUILD)

**This REBUILD block is the CURRENT AUTHORITATIVE packet content.** After the
first-cycle exact-corrected-head confirmation returned DESIGN INCOMPLETE
(section 0.1), Dustin ruled REBUILD (not narrow, not park). Everything above
(sections 0-11 and the first-cycle CORRECTION CYCLE) is preserved **verbatim as
historical first-cycle lineage** per the rebuild charge; where it conflicts with
this REBUILD block, this block **supersedes** it (GOV-2 section 10 -- exactly
one current ruling is plainly identified). The rebuild is documentation-only and
grants nothing downstream: no PRD, Stage 0, Gate A, implementation, or merge.
The bootstrap-COMPLETE exception (R.10), the marginal-return KEEP/NO-GO ruling
(R.9), Stage 0, Gate A, and merge all remain ungranted and return to Dustin only
after this rebuilt packet is review-clean.

## R.1 The true boundary: runner-wide readability (withdrawal + enumeration)

**Withdrawn.** Every first-cycle statement that a sparse checkout, a
`working-directory` selection, or an isolated directory is a *confidentiality*
boundary is **withdrawn**. Those are scope-minimization and navigation controls
only; they do not limit what the model can READ. Specifically superseded:
first-cycle sections 3.5 ("minimal, isolated checkout ... the model's readable
input surface is therefore enumerated" as if bounded), the section 5.2 "model
input" row's reliance on checkout isolation, and requirement 10's framing of
sparse checkout as a read-surface bound.

**Conservative model (primary evidence R.3).** The Codex process must be modeled
as able to read **every path the pinned sandbox permits**. At Codex `0.147.0`
the `:read-only` profile grants `:root = read` -- **whole-filesystem read**,
zero write, and network **Restricted** (no outbound). So the model can read any
path the runner OS lets its uid read, subject only to OS privilege (procfs of
other-privilege processes needs escalation).

Readable-surface enumeration (charge frame item 2):

| Surface | Model-readable? | Basis / label |
|---|---|---|
| Sparse working tree + **full `.git` object DB** | YES | VERIFIED -- whole-fs read; `.git` holds the entire repo regardless of sparse working tree. Content is the **public** repo. |
| Action code under the runner action cache | YES | VERIFIED -- whole-fs read. Public action code (non-secret). |
| Runner temp dirs + workflow command files (`GITHUB_ENV`, `GITHUB_OUTPUT`, `GITHUB_PATH`, `GITHUB_STEP_SUMMARY`) | YES, same-uid, **no sudo needed** | VERIFIED -- same-uid files + whole-fs read. Content is whatever steps write; **Slice A writes no secret here** (binding R.7.4). |
| `HOME`, `CODEX_HOME`, tool caches, action state, generated config | YES | VERIFIED readable. Whether any on-disk proxy/CODEX_HOME config contains the raw API key: **INFERRED NOT PRESENT** (the action captures the key via stdin, not a file -- R.3), residual **UNRESOLVED** pending direct inspection of the proxy config-writing step. |
| `/proc` -- same-uid, non-privileged entries | YES | VERIFIED -- same-uid procfs (e.g. own environ) readable without sudo. |
| `/proc` -- other-privilege process memory/environ (the proxy, the runner agent) | Only with escalation | VERIFIED (vendor, R.3): extractable "with appropriate privileges" i.e. **sudo**; closed by `safety-strategy: drop-sudo`. The exact same-uid `ptrace_scope` nuance on hosted runners is **UNRESOLVED** and is a named review/implementation item (R.4). |
| Checkout credential / `GITHUB_TOKEN` on disk (`.git/config`) | Only if `persist-credentials: true` | VERIFIED (actions/checkout): removed by **`persist-credentials: false`** (binding R.7). |
| `GITHUB_TOKEN` / Actions runtime, cache, artifact tokens in the runner process env | Only via privileged procfs | VERIFIED reachable only via sudo/escalation -> `drop-sudo`; also **not in the codex step env** (Slice A passes no token to the codex-action step). Scope is `contents: read` regardless (R.6). |
| Proxy token / `PROXY_API_KEY` | In-memory in the proxy process | VERIFIED not in codex env (`env -u`, R.3); on-disk **INFERRED NOT PRESENT**; in-memory reachable only via escalation -> `drop-sudo` (+ UNRESOLVED ptrace nuance). |
| stdout/stderr + **public Actions job log** (~90 days) | YES (public repo) | VERIFIED (first-cycle F1). Raw model output lands here; the **secret does not** (proxy). |
| OIDC token material | **NOT PRESENT** | VERIFIED -- Slice A declares no `id-token: write`, so no OIDC token is minted (binding R.7.5). |

The rule the first cycle violated and this block obeys: **do not infer
"not readable" from "not intentionally passed to the model."**

## R.2 Secret-and-capability inventory (charge frame item 4)

producer -> storage/representation -> reader -> model-command reachability ->
lifetime -> consumer -> write/network effect -> enforcing control:

- **OPENAI_API_KEY** -- owner repo Actions secret -> captured by the proxy via
  **stdin**, codex child launched with `env -u PROXY_API_KEY` (not on disk, not
  in codex env; R.3) -> read by the proxy process (in memory) -> model
  reachability: not via env, not via disk, in-memory only via privileged procfs
  (blocked by `drop-sudo`; same-uid ptrace residual UNRESOLVED) -> lifetime: the
  run -> consumer: the proxy forwards to the OpenAI Responses API -> effect:
  **OpenAI API spend only, no GitHub effect** -> control: proxy + `drop-sudo` +
  command-network Restricted; worst-case exfil path is the trusted model
  emitting it into its own output (see R.5).
- **GITHUB_TOKEN** -- Actions per-job token -> `.git/config` only if
  `persist-credentials: true`; runner env otherwise -> reader: referencing
  steps -> model reachability: removed from disk by `persist-credentials:
  false`; env reachable only via privileged procfs (`drop-sudo`) -> lifetime:
  job end -> **scope `contents: read`** so even if read it grants no write ->
  control: `persist-credentials: false` + least-privilege `permissions` +
  `drop-sudo`.
- **Actions runtime / cache / artifact tokens** (`ACTIONS_RUNTIME_TOKEN` etc.)
  -> runner process env/runtime -> model reachability only via privileged
  procfs (`drop-sudo`); not in the codex step env -> effect: artifact/cache
  manipulation *within the run* if read -> control: `drop-sudo` + the secret-
  bearing codex job is separate from the artifact-uploading validator job.
- **Proxy config / PROXY_API_KEY** -- as OPENAI_API_KEY above.
- **OIDC token** -- **NOT PRESENT** (no `id-token` permission).
- **Checkout auth** -- covered by GITHUB_TOKEN + `persist-credentials: false`.
- **Workflow command files** -- runner temp files, same-uid readable **without
  sudo** -> content is step-written; **binding: Slice A writes no secret to any
  command file** (R.7.4), so they hold no credential.

## R.3 Primary evidence (re-derived from source, charge frame item 3)

- **Codex `0.147.0` sandbox** -- `codex-rs/protocol/src/permissions.rs` at
  `rust-v0.147.0`: `read_only_file_system_entries()` returns
  `FileSystemPath::Special{Root}` with `FileSystemAccessMode::Read`;
  `read_only()` builds a policy with `:root = read` and
  `network_access: false`; `NetworkSandboxPolicy` defaults `Restricted` (no
  network), `Enabled` otherwise; `has_full_disk_read_access()` is true for a
  restricted-with-root-read policy. -> whole-fs read, zero write, no command
  network. VERIFIED.
- **openai/codex-action** action.yml at `52fe01ec...`: inputs include
  `openai-api-key`, `prompt-file`, `output-file`, `output-schema-file`, `model`,
  `effort`, `permission-profile`, `safety-strategy`
  (`drop-sudo`|`unprivileged-user`|`read-only`|`unsafe`), `codex-version`,
  `codex-args`, `allow-users`. The key is **proxied**: a "Start Responses API
  proxy" step captures it via stdin and the codex child is launched
  `printenv PROXY_API_KEY | env -u PROXY_API_KEY "${args[@]}"` (key unset in the
  codex env). The action runs a fixed sequence ending in the `codex exec`
  invocation. VERIFIED.
- **openai/codex-action** docs/security.md at `52fe01ec...`: the key is **not**
  kept secret by the proxy alone -- "Linux's procfs makes a considerable amount
  of information available via file-read operations to a user with appropriate
  privileges ... **Be sure to use either `drop-sudo` or `unprivileged-user` to
  ensure it stays secret!**" Permission profiles "constrain commands that Codex
  runs; they do not replace the action's `safety-strategy`, which controls the
  privileges of the Codex process itself." Untrusted values must be passed via
  `env:` and quoted, not spliced. VERIFIED.
- **GitHub-hosted runners** (docs.github.com/en/actions/reference/runners/
  github-hosted-runners; .../concepts/runners/github-hosted-runners): a **new
  VM per job**, "automatically provisions a new VM ... automatically
  decommissioned"; "each job runs in a fresh instance"; "The Linux and macOS
  virtual machines both run using **passwordless sudo**." -> the procfs+sudo key
  threat is real, so `drop-sudo` is load-bearing. VERIFIED.
- **GITHUB_TOKEN** (docs.github.com/.../automatic-token-authentication):
  accessible via `github.token` even if not passed; the workflow `permissions:`
  block sets its scope; least-access advised. VERIFIED. (Lifetime = job end:
  INFERRED, standard behavior, not quoted here.)

Requested model identity (`gpt-5.6-sol`) is recorded as **requested only**;
served identity is not positively observable (PRD-207); it is never recorded as
resolved (retained from first cycle, section 6.1).

## R.4 Slice-A reassessment on the truthful boundary (charge frame item 5)

- Repository + synthetic event content are **public/non-secret**, so broad read
  access to them is acceptable -- but it is **not** called isolation.
- `persist-credentials: false` **does** remove the GitHub token from the on-disk
  checkout (a real control given whole-fs read); it does **not** confer
  filesystem confidentiality.
- `safety-strategy: drop-sudo` is **load-bearing** (not defense-in-depth) for
  API-key and runner-credential confidentiality: the vendor names it as the
  control that closes the procfs escalation path that passwordless sudo would
  otherwise open. Residual: the exact same-uid `ptrace_scope` behavior on hosted
  runners is **UNRESOLVED**; recorded as a review/implementation item, not
  papered over.
- `permission-profile: ":read-only"` (whole-fs read, zero write, **no command
  network**) and `contents: read` + no write scopes together mean **no
  model-readable credential enables a write or GitHub effect** (R.6).
- "Proxy-held API key" is established from pinned implementation (stdin capture +
  `env -u`), and does **not** imply every runtime credential is unreadable --
  the runner/proxy in-memory credentials rest on `drop-sudo`.
- The pinned action, `drop-sudo`, main-only trusted ref, no untrusted ingress,
  and action-final placement each protect a specific thing and are proven, not
  assumed.

## R.5 Smallest lawful security claim (charge frame item 6)

> Slice A intentionally processes only **public, fixed, non-sensitive inputs**
> on an ephemeral GitHub-hosted runner. It **does not claim filesystem
> confidentiality from the model** (Codex `:read-only` grants whole-filesystem
> read). Its safety rests on: (a) the **absence of sensitive model-readable
> inputs** -- the repo is public, the event is a fixed synthetic public value,
> `persist-credentials: false` removes the GitHub token from disk, and no secret
> is written to any same-uid-readable command file; (b) **proxy separation of
> the owner API key combined with `drop-sudo`**, the vendor-named control pair,
> as defense-in-depth for the one sensitive value present; (c) **least-privilege
> GitHub permissions** (`contents: read`; no issues/PR/checks/actions write; no
> `id-token`) so no model-readable credential grants a write or GitHub effect;
> (d) Codex `:read-only` **denies command network egress and all writes**, so
> the model cannot exfiltrate off-runner via commands or mutate anything; (e)
> **no untrusted ingress** (fixed synthetic event -- no adversary can instruct
> the model to read and emit a credential); (f) **no publication path**; and (g)
> **zero authoritative effect** (a NOT-AUTHORITY proposal). The single residual
> exposure -- the trusted model emitting the API key into its own output, which
> lands in the public job log -- requires the model to misbehave on a fixed
> owner prompt with no untrusted ingress, and is bounded (key spend, no GitHub
> effect); it is stated, not hidden.

## R.6 Denied-effect analysis (charge frame item 5)

Does any model-readable credential enable a network or GitHub effect despite
`contents: read`? **No, for Slice A:**

- Command network egress is **denied** (`:read-only` -> `NetworkSandboxPolicy::
  Restricted`), so the model cannot open sockets to exfiltrate or call GitHub
  APIs from a tool/command.
- Even a read `GITHUB_TOKEN` is scoped `contents: read` (workflow `permissions`)
  -- no write, no issue/PR/checks/actions mutation.
- No `id-token` -> no OIDC federation to cloud.
- The only off-runner channel the model can reach is its own model output ->
  public log/artifact (an information-disclosure channel, not a mutation
  channel), which R.5(e) bounds via no-untrusted-ingress.

## R.7 Normative CONTRACT ceremony (BINDING requirements; charge frame item 7)

These are **normative requirements** for the downstream PRD, not descriptive
prose (this is the fix for first-cycle finding 9 NOT-ADDRESSED). CLASS stays
**INFRA on dominant-purpose grounds** while the subordinate CONTRACT ceremony is
carried explicitly:

1. **Schema-diff review (binding).** The reviewer performs a field-by-field
   schema-diff over `.github/campaign/charge.schema.json` and the synthetic
   event shape covering **every field, type, enum, pattern, length, required
   key, and `additionalProperties` rule**; the review artifact records it.
2. **Full producer/consumer audit (binding).** Enumerate and disposition every
   producer and consumer of the event and charge schemas: the model (as
   constraint), the handwritten validator, the renderer, the one-day artifact,
   the public job log, the owner, and **every future Slice-B dependency
   disclosed by Slice A** (issue ingress, publisher, checkpoint carrier).
3. **Drift-guard test (binding).** A test proves the handwritten stdlib
   validator and the JSON schema accept/reject the identical closed vocabulary
   (required keys, enums, patterns, limits, `additionalProperties: false`).
4. **No secret to any same-uid-readable sink (binding).** Slice A writes no
   credential to `GITHUB_ENV`/`GITHUB_OUTPUT`/`GITHUB_STEP_SUMMARY`, any command
   file, any artifact, or any log; model output transport is via step `env:` +
   quoted input through pinned `github-script` only (retained requirement 11).
5. **No `id-token` and no write scopes (binding).** Permissions are
   `contents: read` throughout; no `issues`, `pull-requests`, `checks`,
   `actions`, `contents: write`, or `id-token`. TRIPWIRE-asserted.
6. **`safety-strategy: drop-sudo` present (binding, load-bearing).** A TRIPWIRE
   asserts `drop-sudo`; removing it is a security regression, not a style
   change.
7. **Reviewer disposition obligation (binding).** Any consumer or schema drift
   is dispositioned **before Gate A and again at implementation review**;
   sparse-checkout/working-directory are never cited as confidentiality.

## R.8 Retained from the first cycle (unchanged unless contradicted above)

LANE HIGH-RISK / CLASS INFRA / MATERIAL (section 1); current official action
pins and the removal of unearned `download-artifact` (section 6); requested-only
model identity (section 6.1); inert model-output transport (section 3.6 /
requirement 11); the public Actions-log presentation path (section 3.8); no
model-authored verification field (requirement 1); no issue trigger/write in
Slice A (requirement 7); the Codex Action as the literal final secret-bearing
job step (requirement 8); structural tests labeled `TRIPWIRE -- NOT BEHAVIORAL
PROOF` (section 4); the default-branch bootstrap fact (section 3.9); and the
PRD-230 distinct-product-capability analysis (section 5) -- which remains
subject to the owner KEEP/NO-GO ruling. The Slice-A ceiling remains ESTIMATED
(section 8), unchanged by the rebuild (the rebuild adds requirements and honesty,
not new payload LOC beyond the already-counted validation surface).

## R.9 NO-GO assessment

**Not NO-GO.** On the truthful runner-wide boundary, Slice A's confidentiality
and denied-effect claims **are** supportable on a standard GitHub-hosted runner
via the R.5 claim: safety rests on absence-of-sensitive-inputs + least privilege
+ no untrusted ingress + command-network denial, with key confidentiality as
evidence-backed defense-in-depth (proxy + `drop-sudo`) and one honestly-flagged
UNRESOLVED ptrace residual. The architecture is not unsafe or unprovable; it
required an honest security claim, which R.5 supplies. The PRD-230
distinct-capability finding stands, and the marginal-return KEEP/NO-GO remains
the owner's product ruling.

## R.10 Owner decisions unchanged by the rebuild (return after review-clean)

The bootstrap-COMPLETE exception (first-cycle section 9.3, recommended YES via
same-PR closeout with named post-merge validation follow-up), the second-model
recommendation (commission, do not waive), and the marginal-return KEEP/NO-GO
ruling remain **ungranted** and return to Dustin only after this rebuilt packet
is review-clean.

## R.11 REBUILD CORRECTION CYCLE (one consolidated cycle)

The rebuilt INITIAL PACKET REVIEW (Sol, read-only, xhigh, pinned `ab958645`)
returned **DESIGN INCOMPLETE** with 6 findings (1 CRITICAL, 5 MAJOR) and
material confirmations. Full record: `PACKET.review.sol.md` section 4. This is
the single consolidated rebuild correction (GOV-2 sections 2, 7); it supersedes
the conflicting R.1-R.9 text above per GOV-2 section 10.

**Correction summary (the security model, corrected):** The API key is
**well protected** (Finding 3 strengthened the claim). The genuine residual is
the **runner's own credentials**, which are **same-uid readable** by the Codex
process and are **not** protected by `drop-sudo`. The correct control is
`unprivileged-user`, proven at the already-required post-merge dry-run.

### F1 (CRITICAL) -- runner-root credential surface; drop-sudo is insufficient. ACTIONED.

- **Corrected fact.** A GitHub-hosted runner stores a job-scoped Actions-service
  OAuth token in `<runner-root>/.credentials` (mode-600, owned by the `runner`
  user). The Codex process runs as `runner` (same uid) under `:read-only`
  whole-filesystem read, so it can read `.credentials` **without sudo**.
  `safety-strategy: drop-sudo` removes an escalation path; it does **not** change
  the Codex uid or block ordinary same-uid file reads. The first-cycle/rebuild
  labels calling runner/runtime tokens "reachable only via privileged procfs"
  are **withdrawn**; they are **same-uid readable** and UNRESOLVED for effect.
- **Readable-surface additions (supersedes R.1 table).** Add: runner-root
  `.credentials` (Actions-service token), `.runner`, `.credentials_migrated`,
  credential/diagnostic stores; `$HOME` (may hold credentials per GitHub's
  hosted-runner filesystem docs); and `GITHUB_EVENT_PATH`. All same-uid
  readable; none isolated by `drop-sudo`.
- **Corrected control (BINDING).** Runner-owned-credential confidentiality
  requires **`safety-strategy: unprivileged-user`** -- run Codex as a distinct,
  unprivileged uid so runner-owned mode-600 files are not same-uid readable --
  with the staged public inputs (prompt, schema, tool, synthetic event) made
  readable to that uid. `drop-sudo` alone is insufficient and is downgraded from
  "load-bearing" to "necessary-but-insufficient." Closure of the runner-credential
  surface under `unprivileged-user` is **INFERRED** at documentation stage and
  **must be VERIFIED at the post-merge bootstrap dry-run** (R.11.F6), which is a
  live hosted-runner probe the bootstrap already requires. If closure cannot be
  achieved on a standard hosted runner, it is a named RED stop (owner isolation
  choice, R.11 owner note).

### F2 (MAJOR) -- the Responses API channel and provider are omitted sinks/consumers. ACTIONED.

- **Corrected fact.** Command-network restriction (`:read-only` ->
  `NetworkSandboxPolicy::Restricted`) governs sandboxed **commands**, not the
  parent Codex process's intentionally-permitted **Responses API** traffic. A
  shell command's output (e.g. reading a file) is serialized into the next
  Responses request and POSTed upstream to the OpenAI provider **before** any
  final-message/log decision. So the Responses channel is an off-runner path for
  anything the model reads -- the public log is **not** the only egress.
- **Inventory additions (supersedes R.2/R.6).** Add as consumers/sinks: the
  Codex runtime, the local Responses proxy, the Responses request body, the
  OpenAI/model provider (and its retention/handling boundary), the runner log
  service, the command-file processor, and the artifact service.
- **Corrected control (BINDING).** The model's readable surface must contain no
  runner-owned credential (achieved by `unprivileged-user`, F1); credential
  **unreachability**, not command-network restriction, is the control that keeps
  a credential out of a tool result and thus out of a Responses request. Bind:
  no sensitive runner surface may enter a tool result or Responses request;
  verified at the post-merge dry-run.

### F3 (MAJOR) -- proxy analysis corrected; the API-key claim is STRENGTHENED. ACTIONED.

- **Corrected fact (stronger).** The Responses-API proxy runs as the same
  `runner` uid but is **non-dumpable**: it calls process hardening before
  `main` setting Linux `PR_SET_DUMPABLE=0` (fail-closed) plus `mlock`, so
  `/proc/<proxy>/mem` and same-uid ptrace do **not** yield the key without an
  overriding capability (which `drop-sudo` removes). `/proc/<proxy>/environ`
  lacks the key (`env -u PROXY_API_KEY`). The proxy config writer emits only the
  provider and loopback port, **not** the raw key. Therefore
  **`OPENAI_API_KEY` confidentiality from the model is VERIFIED** (non-dumpable
  proxy + `env -u` + key-free config), not merely `drop-sudo`-dependent
  defense-in-depth. Runner-wide absence from disk/swap/diagnostics remains
  UNRESOLVED but is not the primary custody path.
- **Separation.** The proxy's hardened key custody is distinct from the runner
  worker / composite-action orchestration, which also receives the secret input
  and job credentials and is **not** shown to use the proxy's hardening. That
  runner-worker exposure is the general "compromised runner can harvest secrets"
  baseline GitHub documents for **all** actions; it is not specific to this
  design and is recorded as an accepted platform baseline, not a packet defect.

### F4 (MAJOR) -- no-secret-to-sink rule reframed; "no publication path" narrowed. ACTIONED.

- **Corrected fact.** The pinned action **always** writes the final message to a
  temporary `output.md` and to `GITHUB_OUTPUT` via `setOutput`. So a normative
  "Slice A writes no credential to `GITHUB_OUTPUT`/command files" is **not**
  enforceable by design discipline: if the model emitted a secret in its final
  message it is already in `output.md` + `GITHUB_OUTPUT` before any `env:` /
  `github-script` transport, and GitHub masking is expressly **not** a security
  boundary (output can be encoded/split).
- **Corrected control (supersedes R.7.4).** The real prerequisite is
  **credential unreachability** (F1 `unprivileged-user`): if the model cannot
  read a credential, it cannot emit it into `output.md`/`GITHUB_OUTPUT`/log. The
  sink rule is reframed as: credential unreachability is the control; the inert
  `env:`/`github-script` transport (requirement 11) prevents **injection**, not
  secret-emission.
- **"No publication path" narrowed (supersedes R.5(f)).** Slice A deliberately
  has a public job log and a one-day artifact -- those **are** publication
  surfaces. The supportable claim is **"no repository-authoritative / issue /
  PR / comment publication path,"** not "no publication path."

### F5 (MAJOR) -- CONTRACT ceremony canonically incomplete; classification is an owner adjudication. ACTIONED.

- **Corrected fact.** The canonical closed CLASS set assigns "payload schema,
  artifact contracts, cross-module shape definitions" to **CONTRACT**, and there
  is **no** general "dominant-purpose" rule in canon (PRD-230 is precedent
  commentary, not a class-definition override). This payload deliberately
  introduces a JSON schema and a job-boundary artifact contract -- literal
  CONTRACT purposes.
- **Corrected disposition (supersedes R.7 CLASS framing).** The INFRA-vs-CONTRACT
  classification is routed to the **owner as an explicit adjudication**: either
  (a) reclassify `CLASS: CONTRACT`, or (b) an authoritative adjudication that
  expressly permits `CLASS: INFRA` for this mixed surface. **Regardless of the
  label, the full CONTRACT ceremony is now BOUND:** the full test suite, the
  field-by-field schema-diff review (R.7.1), the full producer/consumer audit
  including the F1/F2 consumers (R.7.2), and -- because CONTRACT mandates it on
  **any** reviewer disagreement, and this review is a disagreement -- a
  **mandatory adjudication artifact** (`PRD-302.adjudication.md`) if CONTRACT
  applies. The reviewer-disposition obligation (R.7.7) does not substitute for
  the adjudication artifact.

### F6 (MAJOR) -- FILES/ceiling refresh; NO-GO disposition. ACTIONED.

- **FILES/ceiling (supersedes R.8 "unchanged" claim).** The `unprivileged-user`
  isolation, the staged-input readability setup, and the extended dry-run
  acceptance add workflow/validation surface that the estimation rule
  (PRD-288/289) requires the estimate to count. The Slice-A ceiling is re-marked
  **ESTIMATED -- PENDING ISOLATION IMPLEMENTATION**; a binding number is not
  offered until the isolation approach is implemented and its surface measured.
  The five payload files stand; the workflow carries the `unprivileged-user`
  configuration (no new file).
- **NO-GO disposition (supersedes R.9).** **Not an architectural NO-GO.** The
  pinned action supports `unprivileged-user`, and a distinct-uid design plus the
  post-merge dry-run proof is a viable path to close the runner-credential
  surface. The truthful state is a design whose runner-credential isolation is
  **INFERRED at documentation stage and VERIFIED at the post-merge dry-run** --
  consistent with the bootstrap lifecycle -- with a named RED stop if the
  hosted-boundary probe cannot demonstrate closure.

### R.5 smallest lawful security claim -- corrected

> Slice A processes only **public, fixed, non-sensitive inputs** on an ephemeral
> hosted runner and **does not claim filesystem or runner-credential
> confidentiality via `drop-sudo`**. Its safety rests on: (a) **no adversarial
> ingress** -- an owner-only `workflow_dispatch` trigger with a fixed synthetic
> event and the owner's own trusted prompt, so no third party can instruct the
> model to read and exfiltrate a credential; (b) **`unprivileged-user`
> credential isolation** (Codex runs as a distinct uid; runner-owned
> credentials not same-uid readable), whose closure is VERIFIED at the
> post-merge dry-run; (c) **VERIFIED `OPENAI_API_KEY` protection** (non-dumpable
> proxy + `env -u` + key-free config, F3); (d) **least-privilege GitHub
> permissions** (`contents: read`; no issues/PR/checks/actions write; no
> `id-token`); (e) Codex `:read-only` **denies all writes and command network**;
> (f) **no repository-authoritative / issue / PR / comment publication path**
> (a public log and one-day artifact do exist and are acknowledged); and (g)
> **zero authoritative effect**. Runner-credential isolation is load-bearing for
> the future Slice B (untrusted ingress) and is a **blocking prerequisite**
> there; its hosted-boundary provability also bears on the owner KEEP/NO-GO
> ruling.

### Owner note surfaced by the rebuild correction (not decided here)

The runner-credential isolation question is **low-risk for Slice A** (no
adversarial ingress) but **load-bearing and harder for Slice B** (untrusted
issue text could instruct the model to read `.credentials` and exfiltrate it via
the Responses channel). Whether `unprivileged-user`-class isolation can be
demonstrated to close that surface on a standard hosted runner is provable only
at a live run and directly informs the marginal-return **KEEP / NO-GO** ruling:
if runner-credential isolation cannot be achieved for untrusted ingress, Slice B
-- and thus the control plane's product purpose -- may be unviable on a standard
hosted runner. This is surfaced for the owner design-direction ruling; it is not
decided here.
