# CuttingBoard Decision-Support Expansion Doctrine v0.1

Status: APPROVED FOR MANUAL MERGE — EFFECTIVE WHEN MERGED

Owner and final authority: Dustin

Applies to: GEX, personalized news, options-data expansion, and the
presentation work attached to those tracks.

This is a planning authority, not an implementation PRD. It assigns no PRD
number, authorizes no production edit, creates no live cadence, and does not
override `VISION.md`, `CLAUDE.md`, `docs/PRD_PROCESS.md`, or
`docs/sidecar_doctrine.md`.

Once ratified and merged, this document is the authoritative boundary for
these tracks. Earlier chats, external drafts, recon notes, and proposal files
remain evidence, not implementation authority. Any change to a constraint
below requires:

1. an explicit ruling from Dustin;
2. a dated `docs/DECISIONS.md` entry;
3. an amendment to this document; and
4. a manual merge of the governance change.

Silence, an agent inference, a proposal, or an old audit does not amend this
doctrine.

## 1. Shared purpose

CuttingBoard remains a personal, deterministic, pre-market
decision-support tool for one discretionary trader.

Every addition must serve at least one of the four questions in `VISION.md`:

1. What environment are we in?
2. What matters today?
3. Is this actually tradable?
4. What would invalidate this?

The expansion tracks are intended to reduce reconstruction effort and expose
relevant context. They are not permission to create predictions, automate
execution, backtest strategies, add ML, or turn CuttingBoard into a general
financial platform.

## 2. Global invariants

These apply to every track and every future PRD.

### G1 — Description, not prediction

Allowed outputs describe observed source data, its provenance, and its
freshness. They may not forecast price, score directional conviction, infer
sentiment, recommend a trade, or create synthetic confidence.

### G2 — Human-readable observation is not pipeline permission

GEX and news are observation-sidecar candidates. They may inform Dustin, but
they may not mutate:

- regime;
- qualification;
- TRADE / NO_TRADE / HALT;
- setup grade;
- position size or risk budget;
- contract selection;
- notification eligibility; or
- an existing pipeline-owned artifact.

If a future proposal wants any of those effects, it is a separate
decision-pipeline proposal requiring an explicit doctrine amendment before a
PRD may be drafted.

### G3 — Producer and consumer are separate work units

The producer ships before its consumer. The producer must first demonstrate a
valid, useful artifact under manual execution. A dashboard, notification, or
scheduled cadence may not be bundled into the producer PRD.

### G4 — No live cadence before a useful consumer

New producers begin manual-only. Cron, notifications, and other automatic
delivery are forbidden until:

- the producer artifact is proven realizable;
- Dustin has inspected representative outputs;
- a separately scoped consumer exists; and
- the consumer defines stale, missing, and invalid behavior.

### G5 — Additive artifacts only

Every producer owns a new, versioned artifact path with one writer. It may not
extend the pipeline output contract as a transport shortcut. Every reader and
writer must be recorded in `docs/artifact_flow_map.md`.

### G6 — Honest absence

Missing, stale, malformed, partially fetched, or semantically unknown data
must be visibly unavailable or omitted according to a written contract. No
zero, neutral value, prior value, or generic label may be substituted unless
the track's approved schema explicitly defines that behavior.

### G7 — Cuts before additions

Before a new sidecar or consumer enters implementation, the workplan must
confirm that adjacent constructed work is either:

- retained with a named purpose;
- completed;
- superseded with a durable pointer; or
- retired.

An unresolved adjacent feature may not be ignored merely because the new
feature is exciting.

### G8 — One bounded question per PRD

Provider research, producer construction, consumer construction, cadence,
and decision coupling are different questions. They may not be compressed
into one PRD.

### G9 — No placeholder authority

Proposal labels, tentative PRD numbers, fabricated review identifiers,
unmerged-branch decisions, and mutable model names are not canonical facts.
Agents must resolve real repository state and exact identities before
editing.

### G10 — Current truth is discoverable without deep recon

Immediately when this plan lands:

- `CLAUDE.md` must link to this doctrine and the companion workplan;
- `docs/PROJECT_STATE.md` must link to the current workplan phase;
- meaningful direction changes must be recorded in `docs/DECISIONS.md`; and
- this workplan is the authority wherever a known proposal header still
  carries stale status.

The stronger proposal-header guarantee becomes binding at `DOC-0` exit:
every superseded or partially dispositioned proposal must state its complete
disposition at the top. Until DOC-0 completes, the two headers named there are
explicit tracked reconciliation debt, not hidden competing authority.

An agent should not need two model passes or an archaeology sweep to learn
whether a track exists, is blocked, or is authorized.

## 3. Current baseline

Baseline inspected: `main` at `724d84af58bd0a021bb989cd2637832e2639e8a3`
on 2026-07-25.

### 3.1 GEX

- No committed GEX provider, schema, producer, consumer, or tests exist.
- The Stage-0 GEX leg did not perform provider research because external
  reach was disabled.
- Its valid repository-only conclusion is that GEX is absent.
- All provider, model, expiration, cadence, spot-basis, and unavailability
  semantics remain unverified.

Current status (updated 2026-08-09): the 2026-08-05 GEX-0 egress pass
reached Polygon and received a real HTTP 401 (authentication required), so
external reach is available -- the Stage-0 "external reach was disabled"
bullet above is historical, not current. A 401 proves reachability and that
authentication is required only; it does not establish usable chain
evidence, provider viability, or evidence sufficiency, and no key is
available. GEX-0 is `EVIDENCE INCOMPLETE`; the next step needs a real
free-tier Polygon credential. Downstream GEX-1..3 holds remain in force.

State: `EVIDENCE INCOMPLETE` (GEX-0; GEX-1..3 remain gated `EVIDENCE BLOCKED`).

No GEX implementation PRD may be drafted until the bounded provider evidence
gate in section 4 passes.

### 3.2 Personalized news

- No personalized news track currently exists.
- Historical RSS/macro work does not constitute this feature.
- PRD-187's macro-awareness collector is a distinct structural-shock
  experiment. It excludes ordinary news, sentiment, predictions, and
  recommendations.
- PRD-188 is a gated proposed consumer for PRD-187, not a news-feed plan.

State: `PROPOSED`.

The macro-awareness collector may not be renamed, widened, or repurposed into
personalized news.

### 3.3 Options

- The core options-expression and sizing machinery already exists.
- PRD-251/252/253/256/157 work is constructed and must be preserved.
- The PRD-251 continuation proposal is stale at its header: PRD-256 R3
  fulfilled the functional question.
- PRD-259 Findings E, F, and G remain open, non-blocking presentation debt.
- Finding D has an explicit operator ruling in open PR #167: refuse a setup
  when its smallest expressible contract exceeds the adjusted risk budget.
  That ruling is not canonical on `main` until PR #167 merges.

State: `CONSTRUCTED / RECONCILIATION REQUIRED`.

Finding D requires a bounded seam trace and a HIGH-RISK implementation PRD
after its ruling is canonical. The seam trace determines placement, affected
consumers, and the refusal reason; it does not reopen the refuse-versus-round
up decision.

### 3.4 Macro-awareness collector

PRD-187 is COMPLETE as a manual/evaluation-only structural-shock producer.
PRD-188 remains PROPOSED and blocked on:

- a fully labeled evaluation corpus;
- a numeric false-positive threshold set by Dustin;
- a passing pinned-model evaluation; and
- Dustin's explicit go.

State: `CONSTRUCTED / EVALUATION GATED`.

Before more work, Dustin must choose `KEEP DORMANT`, `PROMOTE THE PRD-188
CONSUMER AFTER SPLITTING OUT CADENCE`, or `RETIRE`. PRD-188 may not be
promoted unchanged because its current proposal combines consumer
construction and scheduled activation, which G8 forbids. No fourth implicit
state is allowed.

## 4. GEX contract and promotion gates

### 4.1 Intended use

GEX may provide cheap, bounded, source-labeled market-structure context for
human display and audit. It cannot create trade permission.

### 4.2 Provider constraints

- Start with exactly one economically acceptable provider.
- Do not create a provider abstraction, provider comparison program,
  consensus, averaging, or fallback chain.
- The first pass is research only and may make no repository code changes.
- Evidence must come from current provider documentation and a real response,
  not marketing copy or memory.

### 4.3 Minimum honesty contract

The provider pass must directly establish:

- access terms and cost;
- rate limits;
- symbol coverage;
- provider and model label;
- field definitions;
- expiration scope;
- update cadence;
- source timestamps;
- spot-price basis;
- exact meaning of any flip, put-wall, or call-wall level;
- sample response;
- staleness behavior; and
- unavailable/failure behavior.

**Verdict vocabulary (amended 2026-08-05, ruled: Dustin; `docs/DECISIONS.md`
2026-08-05 TRUTH-SYNC entry, ruling 5).** The pass ends in exactly one of:

- `PROVIDER VIABLE`;
- `PROVIDER NOT VIABLE`; or
- `EVIDENCE INCOMPLETE`.

Every verdict speaks only to the one provider examined in that bounded pass. No
verdict may claim that no viable provider exists — a one-provider pass cannot
establish that, and the retired wording `NO VIABLE PROVIDER IN BOUNDED PASS`
invited exactly that overclaim.

If any load-bearing meaning above is unknowable, the result is
`EVIDENCE INCOMPLETE`, with the specific unknowns enumerated.

The track-ending consequence is unchanged: `PROVIDER NOT VIABLE` or
`EVIDENCE INCOMPLETE` ends the track until Dustin explicitly commissions a fresh
pass. Neither authorizes a second provider automatically.

### 4.4 Construction gates

`GEX-0`: bounded live-provider evidence, no code.

`GEX-1`: manual, cached producer sidecar with a versioned schema. Primary
universe only. No consumer, cron, notifications, or pipeline imports.

`GEX-2`: display-only consumer after Dustin inspects useful GEX-1 artifacts.
Missing/stale/invalid data renders no GEX context and leaves baseline output
byte-identical.

`GEX-3`: optional cadence only after consumer usefulness is demonstrated.
Cadence is not presumed.

Each gate requires a separate approval and separate PRD where implementation
is involved.

## 5. Personalized-news contract and promotion gates

### 5.1 User question

The feed answers:

> What new information could cause Dustin to reconsider a premise or pay
> closer attention to a symbol in his defined universe today?

This describes relevance for a human. It does not change system permission.

### 5.2 Scope

- Personal universe, context symbols, and named themes only.
- Two to three surfaced items normally; hard maximum five.
- Deterministic source, symbol, theme, freshness, and deduplication rules.
- Source title, source, publication time, URL, matched symbols/themes, and a
  short source-grounded excerpt or deterministic summary.
- Manual-first and artifact-first.

### 5.3 Forbidden expansion

- No general-market firehose.
- No social-media ingestion in the initial track.
- No LLM sentiment, bullish/bearish label, confidence, severity, velocity,
  catalyst score, or trade recommendation.
- No mutation of existing logic, artifacts, decisions, sizing, or
  notifications.
- No dashboard panel, cron, or push alert in the producer PRD.
- No provider or source abstraction beyond what the bounded registry needs.

### 5.4 Construction gates

`NEWS-0`: static universe/source/theme registry and schema proposal, no
network producer.

`NEWS-1`: manual producer sidecar writing one new versioned artifact. It
enforces the item cap and explicit source/freshness/dedup rules.

`NEWS-2`: usefulness evaluation on representative outputs. Dustin chooses
`KEEP`, `REVISE`, or `RETIRE`.

`NEWS-3`: display consumer only after `KEEP`. Absence is baseline-neutral.

`NEWS-4`: optional cadence or notification as a separately ruled proposal.
Neither is presumed.

## 6. Options construction contract

### 6.1 Existing behavior first

Before adding live chain economics, absolute strikes, expiry selection, or new
presentation, complete the reconciliation work named in the companion
workplan.

### 6.2 Finding D invariant

After PR #167's ruling lands:

> An adjusted risk budget is a hard ceiling. If the smallest expressible
> contract exceeds it, CuttingBoard refuses the setup. It never rounds up to a
> budget-violating actionable contract.

The implementation PRD must still decide:

- where refusal occurs;
- which existing non-actionable carrier receives it;
- the exact stable reason token;
- how every downstream consumer behaves; and
- which positive-sizing paths must remain unchanged.

### 6.3 Future options-data work

Separate:

- data-independent representation, such as a deterministic calendar expiry
  field; from
- provider-dependent economics, such as exact strikes, bid/ask legs, net
  debit/credit, and live max loss.

Provider-dependent work requires a data-contract evidence pass before a
feature PRD. The existing estimated economics remain explicitly estimated
until live inputs are verified.

### 6.4 Forbidden expansion

- No broker or order-routing integration.
- No execution automation.
- No automatic contract recommendation from unverified live data.
- No silent fallback from live pricing to an unlabeled estimate.
- No bundling provider research, chain resolution, sizing correction, and UI.
- No reuse of an existing reason token unless its semantics are proven to
  match.

## 7. Promotion states

Every planned work item must carry exactly one state:

- `EVIDENCE BLOCKED`
- `PROPOSED`
- `HELD FOR DUSTIN DECISION`
- `HELD FOR DUSTIN MERGE`
- `DEFERRED`
- `READY FOR PRD`
- `IN PROGRESS`
- `CONSTRUCTED / EVALUATION GATED`
- `CONSTRUCTED / RECONCILIATION REQUIRED`
- `COMPLETE`
- `SUPERSEDED`
- `RETIRED`

The companion workplan is the only planning ledger for these tracks. Proposal
documents may contain evidence, but their header must point to the workplan
state and may not silently establish another queue.

## 8. Agent non-deviation rules

Every charge must use
`docs/plans/agent-work-charge-template-v0.1.md`.

Agents must:

- inspect current `main`, exact branch, exact SHA, and clean status;
- read this doctrine, the workplan, `VISION.md`, and the active PRD;
- stop when authority conflicts rather than choosing an interpretation;
- use real IDs and current repository paths;
- keep recon read-only except for its commissioned findings artifact;
- derive and lock `FILES` before implementation;
- map every requirement to a discriminating test;
- run one independent review against one pinned SHA;
- permit at most one bounded correction pass before escalating;
- leave every PR governed by this plan draft and manual-held; and
- never merge.

Repeated review-of-review loops, opportunistic cleanup, inferred scope,
unrequested abstractions, and “keep going until done” behavior are prohibited.

## 9. Ratification and repository landing

This doctrine becomes durable only when a manual-merge governance PR:

- adds this file;
- adds the companion workplan and charge template;
- links all three from `CLAUDE.md`;
- adds a `CLAUDE.md` landing-policy carve-out making every PR governed by
  these plans manual-merge-only;
- points `docs/PROJECT_STATE.md` to the current workplan phase; and
- records Dustin's ratification in `docs/DECISIONS.md`.

Until that merge, this document is a reviewable proposal and must not be
represented as repository authority.
