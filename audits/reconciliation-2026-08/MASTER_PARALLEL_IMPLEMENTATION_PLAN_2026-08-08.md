# CUTTINGBOARD -- MASTER PARALLEL IMPLEMENTATION PLAN (2026-08-08)

ORCHESTRATION / PLANNING ONLY. No implementation, no Gate A, no production
code, no implementation PRs, no merges. This document converts the eight
planning artifacts in `audits/reconciliation-2026-08/` (read from remote
branch `claude/cuttingboard-reconciliation-notes-op3p8w`, tip `a853e8c`)
into one execution-orchestration plan. Repo state verified at `main` =
`7d0805e` (PRD-289 merge; HEAD == origin/main). Design authority is the
packet set; nothing here re-decides a packet ruling or reconstructs one
from canonical docs.

Model-role legend used throughout:
- OPUS 4.8 = HELM / campaign driver (distinct model from the banned Opus 5)
- FABLE = Navigator / escalation / semantic + governance review
- CODEX = autonomous engineering crew (read-only review OR sandboxed build)
- LIGHT = lightweight recon agents (Explore / general-purpose, low effort)
- OWNER = Dustin (rulings, ratification, Gate A, every merge)

===================================================================
1. EXECUTIVE CAMPAIGN VERDICT
===================================================================

READY WITH BOUNDED PRECONDITIONS.

The planning set is mature, internally consistent, normalized to one
structure, and readiness-labeled without promotion. The Holistic Review
returned CLEAN, the Normalization pass returned NORMALIZATION COMPLETE, and
the Engineering Health verdict is HEALTHY WITH BOUNDED DEBT / P0: none.
Nothing in the set blocks entry into an execution campaign.

What is NOT ready is any single lane's implementation authority -- by
design. The bounded preconditions that genuinely precede EXECUTION (not
planning) are exactly these, and only these:

  P-1 (Cloudflare). Owner issues the CF ruling bundle (CF-D1a, CF-D2, CF-D3,
      CF-D4, CF-D5, CF-D6) and commissions CF-E1 + CF-E2. CF-D5
      (infrastructure ownership) is the hard gate: no agent-held-secret
      alternative exists, so a decline stops the lane. Implementation
      cannot begin until CF-E1/CF-E2 evidence lands and the MATERIAL packet
      clears its GOV-2 sequence.

  P-2 (Registry). Owner authorizes commissioning the MATERIAL packet draft
      (ideally pre-ruling REG-D2 theme-axis to save a ratification round).
      No evidence phase; every input is in-tree. Implementation waits on
      the packet -> Codex cycle -> REG-D1..D7 rulings -> Stage-0 PRD ->
      Gate A.

  P-3 (GEX). Owner issues the GEX-D1..D4 bundle (egress grant, fresh
      commission with 13e framing, sole-provider confirmation, tier
      posture). The lane is BLOCKED on owner action; nothing moves on agent
      effort alone.

  P-4 (Estimation debt, cross-cutting). The F-1 estimation-rule graduation
      should land BEFORE the next MATERIAL packet sets a Gate-A ceiling, or
      GOV-2 5 stop-and-renew fires a third time on the same root cause.
      This is a tiny docs/governance change, not a blocker on planning --
      but it is a genuine precondition on setting a defensible CF ceiling.

None of P-1..P-4 require implementation to satisfy; they are owner acts and
one docs graduation. That is why the verdict is READY WITH BOUNDED
PRECONDITIONS, not NOT READY.

===================================================================
2. MASTER EXECUTION DAG
===================================================================

Node legend: [OWNER] owner act; [GOV] governance/packet step; [IMPL]
implementation; [REV] review; [MERGE] owner merge.

--- A. CLOUDFLARE CLOCK + MORNING BRIEF (lane 1, implementation-first) ---

  A0  [OWNER] CF ruling bundle (CF-D1a/D2/D3/D4/D5/D6) + commission CF-E1/E2
        prereq: none (issuable now)
        unlocks: A1, A2
  A1  [GOV/evidence] CF-E1 trigger-path capture (needs CF-D5: owner PAT +
        Worker deploy)          prereq: A0(CF-D5)      unlocks: A3
  A2  [GOV/evidence] CF-E2 premarket-quote + first-bar latency capture
        prereq: A0             unlocks: A2b, A3
  A2b [OWNER] CF-D1b premarket-displacement banner ruling
        prereq: A2 (hard: CF-E2 -> CF-D1b)             unlocks: A3
  A3  [GOV] MATERIAL packet draft (design-class; compiles out all semantics)
        prereq: A1 + A2 + A2b + all CF-D rulings       unlocks: A4
  A4  [GOV] Codex packet review + exact-head confirmation (GOV-2 2/7)
        prereq: A3             unlocks: A5
  A5  [OWNER] design-direction ruling
        prereq: A4             unlocks: A6
  A6  [GOV] Stage-0 PRD (PRD-290 scaffold + registry row + prd_index)
        prereq: A5             unlocks: A7
  A7  [REV] fresh-context independent PRD review
        prereq: A6            unlocks: A8
  A8  [OWNER] Gate A (implementation authority)
        prereq: A7            unlocks: A9
  A9  [IMPL] build (composer, runtime wiring, payload projection, renderer
        block, clock files, tests)   prereq: A8       unlocks: A10
  A10 [REV] implementation review + one correction cycle
        prereq: A9           unlocks: A11
  A11 [MERGE] OWNER merge of the CF PR
        prereq: A10          unlocks: downstream rebases (see 7)

--- B. CONTEXT REGISTRY / NEWS-0 (lane 2) ---

  B0  [OWNER] authorize MATERIAL packet draft (+ optional pre-rule REG-D2)
        prereq: none (issuable now)     unlocks: B1
  B1  [GOV] MATERIAL packet draft (schema + seeded-unratified content +
        news-schema proposal)   prereq: B0    unlocks: B2
  B2  [GOV] Codex packet review + exact-head confirmation
        prereq: B1           unlocks: B3
  B3  [OWNER] REG-D1..D7 rulings + design direction + content ratification
        prereq: B2           unlocks: B4
  B4  [GOV] Stage-0 PRD (R1 only: loader + validator + ci.yml line + tests)
        prereq: B3           unlocks: B5
  B5  [REV] fresh-context independent PRD review
        prereq: B4           unlocks: B6
  B6  [OWNER] Gate A
        prereq: B5           unlocks: B7
  B7  [IMPL] build R1 (Ultracode sprint; mechanical once schema frozen)
        prereq: B6           unlocks: B8
  B8  [REV]+[MERGE] impl review + OWNER merge   prereq: B7   unlocks: R2 (deferred)

--- C. GEX VIABILITY CLOSURE (lane 3) ---

  C0  [OWNER] GEX-D1..D4 bundle (egress grant, fresh commission + 13e
        framing, sole-provider confirm, tier posture)
        prereq: none (issuable now)     unlocks: C1
  C1  [IMPL/evidence] GEX-0 continuation pass (network read-only, docs-only,
        addendum in existing audit folder; 0 production LOC)
        prereq: C0           unlocks: C2
  C2  [GOV] terminal verdict: VIABLE / NOT VIABLE / (2nd) INCOMPLETE
        prereq: C1           unlocks: C3 or lane stop
  C3  [OWNER] go/stop ruling (only if VIABLE)
        prereq: C2==VIABLE   unlocks: D

--- D. CONDITIONAL GEX-1 PRODUCER (lane 3 continuation) ---

  D0  [GOV] GOV-2 1 MATERIAL intake (classify only when VIABLE + go exist)
        prereq: C3           unlocks: D1
  D1..D7  MATERIAL packet -> Codex review + exact-head -> ruling -> Stage-0
        PRD -> review -> Gate A -> build (producer + provenance carrier +
        in-repo GEX compute + artifact writer + dispatch workflow + tests)
        -> impl review -> OWNER merge
        NOTE: renderer untouched (GEX-2 is a separate, later, gated step).

--- E. ENGINEERING HEALTH WAVE A (bounded, runs around the lanes) ---

  E1  [IMPL] QW-4 GEX docs-drift batch (docs-only; independent)  no prereq
  E2  [IMPL] QW-1 resolve_run_mode stale PRD-192 comment (cosmetic)  no prereq
  E3  [OWNER] Alignment check (due; phase boundary passed at PRD-289) + stale
        pointer edit rides it   no prereq
  E4  [IMPL] QW-3 pip cache -- SEQUENCED: land BEFORE or FOLD INTO A9's
        cuttingboard.yml edit (shared file)   soft-prereq: coordinate with A
  E5  [IMPL] QW-5 idempotent dev bootstrap (.claude hook + script)  no prereq
  E6  [IMPL] QW-2 macro-driver dedup (~15 LOC, mutation-verified test)
        no file prereq; independent tiny code PR
  E7  [OWNER] TD-4 SMCI ruling -> then trivial 1-line fix   no prereq

--- F. ENGINEERING HEALTH WAVE B (friction reducers) ---

  F1  [GOV] estimation-rule graduation (PRD_PROCESS line; Fable review;
        draft, owner-held)   PRECEDES A3's ceiling ideally
  F2  [IMPL] mutation-runner utility (small tools/ PRD; earned by 3rd use)
  F3  [OWNER+IMPL] PROJECT_STATE archival convention (owner rules format,
        then mechanical)   prereq: owner ruling (TD-14)
  F4  [GOV] process-lesson graduation (agent-workflow conventions; Fable
        review; draft, owner-held)

--- G. ENGINEERING HEALTH WAVE C (deferred; do NOT start without justification) ---

  G1  runtime/ split continuation -- GATED on the 2026-08-15 re-ruling (TD-12)
  G2  renderer decomposition (PRD-238) -- only if post-CF pressure appears
      (registry R2/R3 is feature-lane work, not cleanup)

--- SEQUENTIAL / PARALLEL / BLOCKED / DEFERRED classification ---

MUST BE SEQUENTIAL (hard order, do not collapse):
  - A: A0(CF-D5)->A1; A2->A2b; (A1+A2+rulings)->A3->A4->A5->A6->A7->A8->A9->A10->A11
  - B: B0->B1->B2->B3->B4->B5->B6->B7->B8  (REG-D2 ideally before B1)
  - C: C0->C1->C2->C3   (2nd INCOMPLETE ends the track, no retry authority)
  - D: strictly after C3==VIABLE+go (doctrine G3/G8 non-collapsible)
  - E4 (pip cache) before/with A9 (shared cuttingboard.yml)
  - F1 (estimation rule) before A3 sets the CF Gate-A ceiling (soft-hard)

MAY RUN IN PARALLEL (no shared files, no cross-lane dependency):
  - A, B, C top-level all run concurrently once their owner acts land
  - E1, E2, E3, E5, E6, E7 concurrent with everything
  - B (entire R1 chain) parallel with A through A11 -- disjoint files
  - C1 continuation pass parallel with everything (touches only audit folder)
  - Card real-use observation parallel with all (A AMPLIFIES it)

BLOCKED (on owner action only, zero agent effort available):
  - C entire lane until C0
  - A1 until CF-D5; A2b until CF-E2; A3 until all CF evidence+rulings
  - D entire lane until C3==VIABLE + go
  - E7 fix until TD-4 ruling; F3 until TD-14 format ruling

DEFERRED (explicitly out; reopen only on the stated trigger):
  - Registry R2 (consumer migration), R3 (deletions) -- after B8, separate PRDs
  - GEX-2 display card -- after inspected GEX-1 artifacts
  - GH-cron retirement -- observed-replacement-gated, after CF observation
  - Market Map narrowing -- strictly after CF card observation window
  - Wave C entirely
  - Holiday calendar, premarket bar ingestion, pairwise relationships,
    roles/horizons/questions, generalized scheduler

DEPENDENCIES THE PACKETS EXPLICITLY REJECTED (do NOT create):
  - Morning Brief -> Registry (Brief is SPY-only; PASS on registry-as-dep)
  - GEX -> Cloudflare clock (GEX-1 is manual workflow_dispatch; scope wall)
  - GEX -> Registry (GEX-1 SPY-primary; no file/schema overlap)
  - Any lane -> Market Control Card coupling (all three carry the wall)
  - Shared provenance/freshness infrastructure before a 3rd real instance

===================================================================
3. FIRST 72-HOUR / USAGE-BURN CAMPAIGN
===================================================================

Objective: maximum useful throughput with minimal rework. Cloudflare keeps
the implementation seat; everything else fills otherwise-idle capacity
without touching CF's production surfaces. Assume substantial Codex
capacity.

TRACK A -- Cloudflare authority + evidence (the seat).
  - Owner: OPUS 4.8 drives; OWNER issues the ruling bundle; CODEX/LIGHT run
    the evidence captures once CF-D5 lands.
  - Branch: `worktree-cf-morning-brief-evidence` (docs/evidence only in
    this window -- NO production code yet).
  - Authority level: PLANNING-READY -> evidence -> MATERIAL-packet. NO
    Gate A in 72h; that is by design (CF-E1/E2 + packet + Codex cycle +
    ruling + PRD + review all precede it).
  - Exact stopping point for the window: MATERIAL packet DRAFTED and
    submitted for the Codex packet review (A3 done, A4 in flight). Do NOT
    cross into A6 (Stage-0 PRD) inside 72h unless owner accelerates.
  - Merge priority: 1 (feature seat) -- but nothing from Track A merges in
    72h except possibly the folded pip-cache line (E4) if CF's workflow
    edit is reached, which it will not be this window.
  - If blocked: CF-D5 declined -> lane STOPS (Section 14); reallocate the
    freed capacity to Track B depth and Track D. CF-E1 unworkable under
    least-privilege auth -> STOP, escalate to FABLE for auth-model
    reframing before any fallback.

TRACK B -- Registry MATERIAL packet drafting (parallel, no seat contention).
  - Owner: OPUS 4.8 commissions a design-class drafter (FABLE-reviewed
    where semantics bind); LIGHT already did the 2 duplication inventory.
  - Branch: `worktree-registry-material-packet` (docs only: schema spec +
    seeded-unratified content + news-schema proposal).
  - Authority level: MATERIAL-PACKET-READY. Draft only; NO ratification,
    NO Stage-0 PRD, NO implementation in 72h.
  - Exact stopping point: packet draft complete and presenting REG-D1..D7
    as bounded owner choices; REG-D2 asked first. Held for Codex packet
    review + owner rulings.
  - Merge priority: 3 (after CF, after Wave A truth batches).
  - If blocked: owner defers REG-D2 -> draft can still present it as a
    bounded choice; proceed. Owner declines all ratification -> park the
    lane (do not build a consumer-less registry).

TRACK C -- GEX owner ruling + evidence continuation (parallel, tiny).
  - Owner: OWNER issues GEX-D1..D4; CODEX/LIGHT run the read-only network
    evidence pass once egress is granted.
  - Branch: `worktree-gex-0-continuation` (addendum in the existing
    `audits/gex-0-polygon-provider-evidence-2026-08/` folder; 0 production
    LOC).
  - Authority level: BLOCKED until GEX-D1+D2. After grant, immediately
    runnable, no further planning.
  - Exact stopping point: terminal verdict artifact (VIABLE / NOT VIABLE /
    2nd INCOMPLETE). Do NOT begin GEX-1 in 72h even if VIABLE -- GEX-1 is
    its own MATERIAL intake behind an explicit owner go.
  - Merge priority: 4 (GEX evidence docs/addendum), independent.
  - If blocked: egress not granted -> lane idle, zero cost, no reallocation
    needed. 2nd INCOMPLETE -> track ends pending fresh owner ruling; do not
    retry.

TRACK D -- isolated engineering-health quick wins (parallel, mechanical).
  - Owner: CODEX autonomous (lightweight cleanup) under the Section 6
    contract; OPUS 4.8 reviews; OWNER runs the Alignment check + rulings.
  - Branches (each its own tiny PR, per Wave A seam-not-omnibus rule):
      `chore-gex-docs-drift` (QW-4, docs-only)
      `chore-resolve-run-mode-comment` (QW-1, cosmetic carve-out)
      `chore-macro-drivers-dedup` (QW-2, ~15 LOC + mutation test)
      `chore-dev-bootstrap` (QW-5, .claude hook + script)
  - Authority level: quick wins need no Gate A (bug/cleanup within
    established patterns); QW-2 rides a mutation-verified red test.
  - Exact stopping point per item: branch review-ready, targeted tests
    green, held for OWNER merge.
  - Merge priority: 2 (a tiny truth/docs cleanup may merge before CF, per
    Section 17, if it does not delay CF).
  - If blocked: QW-3 pip cache must NOT land as a standalone if it would
    race CF's cuttingboard.yml edit -- hold it to fold into A9, or land it
    first and rebase A onto it. TD-4 SMCI fix waits on the owner ruling.

Realistic 72h end-state: CF MATERIAL packet drafted + in Codex review;
Registry MATERIAL packet drafted + held for owner rulings; GEX terminal
verdict reached (if egress granted); 2-4 Wave A quick-win PRs review-ready
and held for owner merge; Alignment check run and recorded. Zero feature
implementation merged; zero Gate A issued. That is the intended aggressive-
but-clean shape.

===================================================================
4. WORKTREE / BRANCH OWNERSHIP PLAN
===================================================================

Design rule: one active branch owns a high-contention file at a time. The
Holistic Review's single-owner rule for payload.py / dashboard_renderer.py
is preserved absolutely -- Cloudflare holds both during its implementation;
no other active branch touches them.

NOTE (env constraint): `git worktree add/remove`, `checkout`, `reset`,
`rebase` are hard-denied to agents in this repo. Worktree creation and any
rebase in this plan are OWNER actions (or done via fresh branch + PR). The
"worktree" names below are logical ownership units; realize them as
branches Dustin creates or as PR branches.

  Stream: CF evidence + packet (Track A, pre-impl)
    Purpose: CF-E1/E2 captures + MATERIAL packet draft
    Owns: audits/ evidence files, cloudflare/ (docs-only worker stub for
          docs-match-code), the packet doc
    Forbidden: ALL cuttingboard/ production, payload.py, renderer, workflows
    Collision points: none in this phase
    Merge order: not merged in campaign window (packet -> PRD path)

  Stream: CF implementation (Track A, post-Gate-A -- LATER)
    Purpose: build the Morning Brief slice
    Owns (SINGLE-OWNER during its life): delivery/payload.py,
          delivery/dashboard_renderer.py, runtime/__init__.py,
          runtime/_constants.py, cloudflare/worker.js + wrangler.toml,
          cuttingboard.yml, scripts/resolve_run_mode.py, new
          test_morning_brief*.py, new brief composer module
    Forbidden: data/, tools/ registry files; GEX files; regime.py; the
          three read-only producers (spy_observation, intraday_state_engine,
          red_folder); PAYLOAD_SCHEMA_VERSION; decision contract
    Collision points: cuttingboard.yml (with QW-3 pip cache -> fold in);
          resolve_run_mode.py (with QW-1 comment fix -> land QW-1 first or
          fold in)
    Merge order: 1 (feature seat)

  Stream: Registry R1 (Track B)
    Purpose: registry file + loader + validator + tests
    Owns: data/context_registry.json (new), cuttingboard/context_registry.py
          (new), tools/validate_context_registry.py (new),
          tests/test_context_registry.py (new), one line in
          .github/workflows/ci.yml
    Forbidden: payload.py, renderer, runtime, regime, config.py lists,
          market_map.py, watchlist_sidecar.py (all stay authoritative until
          R2); any decision-config absorption
    Collision points: ci.yml single validator line (with nothing else this
          window; Morning Brief does NOT touch ci.yml -- it touches
          cuttingboard.yml). Trivial; owner serialized merge absorbs it.
    Merge order: 3

  Stream: GEX-0 continuation (Track C)
    Purpose: evidence addendum
    Owns: audits/gex-0-polygon-provider-evidence-2026-08/ only
    Forbidden: all production, all workflows
    Collision points: none
    Merge order: 4

  Streams: Wave A quick wins (Track D) -- one branch each
    chore-gex-docs-drift: owns docs/PROJECT_STATE.md,
      docs/plans/decision-support-workplan-v0.1.md, NS ledger,
      docs/system_logic_map.md (docs-only). Collision: PROJECT_STATE.md is
      also edited at every PRD closeout -- land QW-4 early, before CF/Registry
      PRDs add PROJECT_STATE rows, to avoid a closeout-vs-cleanup race.
    chore-resolve-run-mode-comment: owns scripts/resolve_run_mode.py
      (comment-only). Collision: CF impl also edits this file -> land QW-1
      BEFORE CF impl, or fold into it.
    chore-macro-drivers-dedup: owns the narrowest shared location for
      _OPTIONAL_MACRO_DRIVERS (import-graph decides at impl time) +
      contract.py:64 / payload.py:318-336. Collision: payload.py is a
      CF single-owner file -> QW-2 must land BEFORE CF takes the seat, or
      wait until after CF merges. RECOMMEND: land QW-2 first (it is tiny and
      independent), then CF rebases onto it.
    chore-dev-bootstrap: owns .claude/ hook config + a new script.
      Collision: none.

HIGH-CONTENTION FILE ARBITRATION (explicit):
  - payload.py:  CF owns during impl. QW-2 touches it -> land QW-2 first.
      Registry never touches it. GEX-1 never touches it (GEX-2 far later).
  - dashboard_renderer.py:  CF owns during impl (adds block #3). Nobody
      else active touches it. Registry R1 stays out. GEX reaches it only at
      GEX-2.
  - GitHub workflow files:  cuttingboard.yml -> CF (+ QW-3 folded).
      ci.yml -> Registry (one line) + QW-3 (pip cache line, different line).
      hourly_alert.yml etc -> QW-3 pip cache only. macro_awareness.yml ->
      TD-16 owner ruling only, untouched otherwise.
  - CI configuration:  QW-3 (cache) is the only structural change; do not
      change --skip-commit-resolvability (WONTFIX-HISTORICAL) or the
      full-suite-before-run policy (owner-only).
  - docs/governance surfaces:  F1/F4 graduations (drafts, owner-held,
      Fable-reviewed); the two 2026-08-06 owner-authored docs are NOT edited
      by agents.
  - data/:  Registry R1 exclusively (context_registry.json).
  - tools/:  Registry validator (new file) + mutation-runner (F2, new file)
      -- different files, no collision.
  - tests/:  each lane adds its own new test_*.py; QW-2 adds one test;
      pre-implementation grep sweep (PRD-158) required before any FILES
      declaration that renames/removes a rendered field or contract key.

===================================================================
5. MODEL ASSIGNMENT MATRIX
===================================================================

Rule: no heavyweight reasoning on mechanical work; no autonomous execution
where product semantics remain open.

  Step / work item                         Best executor        Why
  ---------------------------------------  -------------------  --------------------------------
  CF ruling bundle (CF-D*)                 OWNER-only           product/security/infra choices
  CF-E1 trigger-path capture               CODEX (autonomous)   mechanical once PAT deployed;
                                                                exact success criterion
  CF-E2 quote/bar-latency capture          CODEX or LIGHT       read-only diagnostic capture
  CF MATERIAL packet draft                 FABLE-review /       vocabulary + failure-semantics +
                                           design-class draft   boundary design (product reasoning)
  CF packet Codex review + exact-head      CODEX (read-only)    GOV-2 2/7 auto-commissioned events
  CF design-direction ruling               OWNER-only           semantic authority
  CF Stage-0 PRD authoring                 OPUS 4.8             interprets approved packet
  CF PRD independent review                fresh-context (may   GOV-1 routine gate; NOT the
                                           be FABLE or 2nd model) packet author/implementer
  CF implementation                        OPUS 4.8 + CODEX     Opus interprets; Codex builds
                                           (autonomous build)   bounded slices with full proof
  Registry duplication inventory           LIGHT (done)         mechanical grep/consumer trace
  Registry axis-conflation / authority     FABLE / design-class product boundary (what a theme
    boundary / NEWS-0 split                                     axis means; context-vs-decision)
  Registry MATERIAL packet draft           design-class draft   schema is a shared seam; misdesign
                                                                propagates to 3 lanes
  Registry packet Codex review             CODEX (read-only)    packet-cycle event
  REG-D1..D7 rulings + ratification        OWNER-only           registry CONTENT is product authority
  Registry R1 implementation               CODEX (HIGH AUTONOMY) mechanical once schema frozen --
                                                                "genuine Ultracode sprint"
  GEX-D1..D4 bundle                        OWNER-only           egress/licensing/provider posture
  GEX-0 continuation pass                  CODEX (autonomous,   read-only network evidence against
                                           network read-only)   a fixed 16-row checklist
  GEX terminal verdict authorship          FABLE / design-class provider-viability judgment
  GEX-1 (if reached)                       OPUS 4.8 + CODEX     Opus-led feature lane
  QW-1 comment truth fix                   CODEX (light cleanup) cosmetic, total independence
  QW-2 macro-driver dedup                  CODEX (light cleanup) exact files, 1 mutation test
  QW-3 pip cache                           CODEX (light cleanup) 5 known lines; sequenced w/ CF
  QW-4 GEX docs-drift batch                CODEX (light cleanup) 4 known docs edits
  QW-5 dev bootstrap                       CODEX (light cleanup) small script + hook
  TD-4 SMCI fix                            OWNER ruling ->       1 line after the intent ruling
                                           CODEX (light)
  Alignment check                          OWNER (+ LIGHT for   phase-boundary diff-read is an
                                           the diff enumeration) owner audit act
  Mutation-runner utility (F2)             CODEX (standard) +   small spec first; Fable-lite spec
                                           FABLE spec review    review
  Estimation-rule graduation (F1)          FABLE review first   governance-adjacent wording
  Process-lesson graduation (F4)           FABLE review first   governance-adjacent wording
  PROJECT_STATE archival (F3)              OWNER format ruling  convention is owner's; exec is
                                           -> CODEX (light)     mechanical
  Cross-lane conflict / circling / drift   FABLE (escalation)   Navigator role (Section 10)

CODEX HIGH-AUTONOMY GREEN LIGHT (finish-line-defined, no open semantics):
  - Registry R1 build once the MATERIAL packet freezes the schema (exact
    files, exact validator invariants with mutation targets, exact tests,
    zero-consumer definition-of-done -- textbook autonomous).
  - GEX-0 continuation pass (exact 16-row checklist, exact host allowlist,
    exact terminal-verdict discipline, docs-only output).
  - QW-1, QW-2, QW-3, QW-4, QW-5 (each has exact files, exact size, exact
    proof).
  - CF implementation slices AFTER Gate A, packet-frozen (the PRD-289
    "transcription with proof obligations" pattern).

NOT SUITABLE FOR AUTONOMOUS EXECUTION (flag -- semantics open):
  - Any CF work before CF-E2 resolves premarket quote semantics (CF-D1b
    open).
  - Registry content drafting before REG-D2 (axis semantics unresolved --
    autonomy here risks a wasted ratification round).
  - GEX terminal verdict (a judgment, not a transcription).
  - TD-4 SMCI fix before the owner rules which intent is true.
  - Anything that would expand FILES, bump a schema version, add a
    dependency, or touch a decision contract -- STOP conditions, Section 6.

===================================================================
6. CODEX GOAL CONTRACT TEMPLATE (reusable, for autonomous / long-running tasks)
===================================================================

Paste-and-fill. One contract per autonomous Codex goal. "Best effort" is
banned: the task continues until the finish line OR hits a stop-and-escalate
trigger.

-------------------------------------------------------------------
CODEX AUTONOMOUS GOAL CONTRACT
  Goal id:            <lane-item, e.g. QW-2 / REG-R1-BUILD>
  Objective (1 line): <exact deliverable>
  Branch/worktree:    <isolated branch; never main>
  Model/effort:       <sandbox read-only for review; build sandbox for impl>
                      reasoning effort <= high (default medium)

  AUTHORIZED FILES (hard boundary -- the FILES ceiling):
    <exact paths; nothing outside without STOP>

  INVARIANTS TO HOLD:
    - additive only; PAYLOAD_SCHEMA_VERSION unchanged; decision contract
      byte-identical with feature absent/present
    - fail-loud, never substitute-and-continue (PRD-198 #1)
    - every guard ships a mutation-verified red test (PRD-198 #4)
    - value-XOR-typed-unavailable cells; UPPER_SNAKE states, lower_snake
      reasons
    - run_at_utc determinism: no wall-clock in composers
    - no secret in URL/log/artifact/repo (header auth only)

  EXACT TESTS THAT MUST GO GREEN:
    <named test files/cases; the M-mutation targets that must turn red when
     the guard is removed>

  DEFINITION OF DONE (continue until ALL true):
    [ ] implementation complete against the objective
    [ ] targeted tests green
    [ ] full required validation green (ruff + the lane's required suite)
    [ ] mutation demonstrations complete where required (apply -> red ->
        revert -> green, table emitted)
    [ ] lint/format checks green
    [ ] diff stays within AUTHORIZED FILES (verify with
        `git diff --name-only`)
    [ ] docs/bookkeeping the slice requires are updated (registry row,
        prd_index, SCHEMA_MAP/CALL_SITE_MAP if a symbol moved)
    [ ] branch is review-ready (commit per validation step, not one batch)

  STOP AND ESCALATE TO OPUS/FABLE IMMEDIATELY IF:
    - architecture ambiguity (two defensible structures, spec silent)
    - a needed file is outside AUTHORIZED FILES (FILES expansion)
    - LOC trending past the Gate-A ceiling (GOV-2 5 threat)
    - any schema/version expansion appears necessary
    - a new dependency is needed (declared AND locked, or STOP)
    - a new external service / network host is needed
    - any credential/security decision arises
    - an owner-only semantic choice surfaces
    - the decision contract would change
    - a test fails in a way that implies the DESIGN is wrong, not the code
    - provider substitution / comparison is implied (GEX)

  ON STOP: do not work around. Emit current diff + the exact trigger + the
  decision needed. Escalation goes to OPUS (routine) or FABLE (semantic/
  governance). Never merge; never queue auto-merge; never push to main.
-------------------------------------------------------------------

===================================================================
7. MERGE TRAIN
===================================================================

Per-lane pipeline (every lane, no exceptions):
  BUILD -> SELF-VALIDATE (ruff + targeted + required suite) -> REQUIRED
  REVIEW (one fresh-context implementation review) -> CORRECTION (single
  GOV-1 cycle) -> EXACT-HEAD CONFIRMATION (GOV-2 lanes only) -> CLOSEOUT
  (same-PR, prd-closeout-verified skill) -> OWNER MERGE -> DOWNSTREAM
  REBASE/RECONCILE -> REVALIDATE.

Recommended global merge sequence (collision-aware):
  1. Wave A truth/docs quick wins that are TOTALLY independent and do not
     delay CF: QW-4 (GEX docs-drift), QW-1 (comment), QW-5 (bootstrap).
     These may merge before CF -- Section 17. QW-2 (payload.py dedup) merges
     here too, BEFORE CF takes the payload.py seat.
  2. QW-3 pip cache -- either merged just before CF's workflow edit or folded
     into the CF PR. Never a standalone that races cuttingboard.yml with CF
     mid-flight.
  3. Cloudflare / Morning Brief PR (the feature seat).
  4. Registry / NEWS-0 R1 PR.
  5. GEX evidence addendum (docs; can actually merge any time -- placed here
     only because it is lowest-contention, not because it is blocked by 3/4).
  6. Conditional GEX-1 (only if VIABLE + go; its own full chain).
  7. Wave B friction reducers (mutation-runner, PROJECT_STATE archival,
     graduations) -- interleave as they become ready; F1 ideally lands
     before CF's MATERIAL ceiling is set.

DOWNSTREAM RECONCILIATION (who rebases after each merge):
  - After ANY merge to main: every long-lived branch (CF impl, Registry R1,
    GEX continuation, open Wave A/B branches) does `git pull --ff-only`
    reconcile at its next active step. Rebases are OWNER acts (deny list);
    agents request them.
  - After QW-2 merges: CF impl branch rebases (payload.py changed).
  - After QW-1 merges: CF impl branch rebases (resolve_run_mode.py changed).
  - After QW-4 merges: Registry + CF branches rebase if they have added
    PROJECT_STATE rows (closeout-vs-cleanup contention).
  - After CF merges: Registry branch rebases (no file overlap, but keep it
    current); any Wave B branch touching PROJECT_STATE rebases.
  - After Registry merges: no forced rebase (disjoint files), but ff-only
    pull at next step.

ANTI-DRIFT RULE (explicit): no long-lived implementation branch may go more
than one merged-PR-to-main behind without an ff-only reconcile. If a branch
cannot ff-only (history diverged), STOP and escalate to OWNER for a rebase
rather than accumulating silent drift. This is the mechanism that prevents
"several long-lived branches silently drift from main."

REGISTRY-BEFORE-CLOUDFLARE-MERGE question: Registry PACKET/PRD work proceeds
in parallel now (Track B), but Registry IMPLEMENTATION (B7) need not wait for
CF to merge -- its files are disjoint. RECOMMENDATION: let Registry R1 build
and merge on its own clock whenever its owner rulings land; it does not
compete for CF's seat and carries no CF dependency. Do NOT, however, start
Registry R2 (consumer migration) until after CF merges, because R2 begins
touching consumer files and the collision surface widens.

GEX-1-BEFORE-CLOUDFLARE-MERGE question: GEX-1 cannot begin until a terminal
VIABLE verdict + owner go, which realistically post-dates CF's merge. Even if
it did not, GEX-1's producer files are disjoint from CF. RECOMMENDATION:
GEX-1 implementation waits on its own authority chain regardless of CF; only
its evidence continuation (docs) proceeds in parallel now.

===================================================================
8. HUMAN ATTENTION QUEUE (optimize Dustin's attention)
===================================================================

Group owner acts so the campaign does not fire five simultaneous semantic
asks. Ranked by leverage x blocking-power.

NOW (issuable in one sitting, mutually independent, unblock the most):
  1. CF ruling bundle: CF-D1a, CF-D2, CF-D3, CF-D4, CF-D5, CF-D6 +
     commission CF-E1/CF-E2. (Unblocks the entire feature seat. CF-D5 is the
     hard one -- infrastructure ownership.)
  2. GEX-D1..D4 bundle (egress grant, fresh commission + 13e framing,
     sole-provider confirm, tier posture). (Unblocks an otherwise-idle
     lane at near-zero cost.)
  3. Authorize the Registry MATERIAL packet draft + optionally pre-rule
     REG-D2 (theme-axis) to save a ratification round.
  4. Run the DUE Alignment check (phase boundary passed at PRD-289) +
     approve the stale-pointer edit riding it.

AFTER EVIDENCE (do not ask until the evidence lands):
  5. CF-D1b premarket-displacement banner ruling (strictly after CF-E2).
  6. GEX go/stop ruling (strictly after the terminal verdict; only if
     VIABLE).
  7. REG-D1, REG-D3..D7 formal ratification (after the packet draft presents
     them as bounded choices; REG-D2 if not pre-ruled).

BEFORE IMPLEMENTATION (Gate A gates -- one per lane, never bundled):
  8. CF design-direction ruling (after packet Codex cycle) -> then CF Gate A.
  9. Registry design direction + Gate A (after packet + rulings).
  10. GEX-1 Gate A (only if the lane reaches it).

BEFORE MERGE (the human gate, every PR):
  11. Every merge is Dustin's act (GOV-1) -- CF, Registry, each Wave A/B
      quick win, GEX evidence addendum.

DEFERRED (do not force into the first window; rank by leverage when they
come up):
  - TD-4 SMCI intent ruling (P1, but conservative-direction -- safe to
    hold briefly).
  - TD-12 runtime/-split re-ruling (calendar-due 2026-08-15 -- will arrive
    mid-CF-arc; put it on the calendar, not the critical path).
  - TD-14 PROJECT_STATE archival format ruling (P2).
  - TD-10 action-SHA-pinning ruling (accept float vs pin).
  - TD-16 macro_awareness.yml force-push-to-main exception (bless or
    migrate).
  - PRD-283-F1 qualified_count semantics (already queued).
  - TD-17 settings.local text verify (low stakes).
  - TD-18 / 2026-06-10 parked dashboard-item cut ruling.
  - Estimation-rule + process-lesson graduation approval (F1/F4 drafts,
    owner-held).

The design goal: items 1-4 are ONE sitting. 5-7 arrive only when their
evidence is in hand. 8-10 are spaced by lane. Everything else is a queue
Dustin pulls from, not a set of interrupts pushed at him.

===================================================================
9. ENGINEERING-HEALTH STRIKE PLAN
===================================================================

P0: none (confirmed -- no correctness/safety blocker; TD-4 is
conservative-direction and one line once ruled). Cleanup never takes the
implementation seat; Cloudflare-first stands.

WAVE A -- bounded by seam, NOT one omnibus branch:

  QW-1 (stale PRD-192 comment in resolve_run_mode):
    Run: immediately. Own tiny cosmetic-carve-out PR.
    Collision: CF impl edits this file -> land BEFORE CF impl or fold in.
    Verdict: RUN NOW as its own PR (land before CF takes the seat).

  QW-4 (GEX docs-drift truth batch: PROJECT_STATE + workplan + NS ledger +
        system_logic_map:21):
    Run: immediately. Docs-only, total independence.
    Sequence: land EARLY, before the next GEX commission and before CF/
    Registry PRDs add PROJECT_STATE rows.
    Verdict: RUN NOW, own PR, merge first.

  Alignment check (TD-2, DUE):
    Run: immediately (owner act + LIGHT for the diff enumeration). The stale
    next-check pointer edit rides it. No PR ceremony for the pointer.
    Verdict: RUN NOW (owner).

  QW-3 (pip cache, 5 setup-python steps incl. cuttingboard.yml):
    Run: SEQUENCED. Shares cuttingboard.yml with CF.
    Decision: FOLD INTO the CF workflow edit (cleanest -- one owner of
    cuttingboard.yml), OR land as its own PR strictly BEFORE CF touches the
    workflow, then CF rebases. RECOMMEND fold-in to avoid a rebase.
    Verdict: FOLD INTO CF (or land-first-then-CF-rebases).

  QW-5 (idempotent dev bootstrap: .claude hook + script):
    Run: immediately. No collision. Prefer explicit bootstrap script + thin
    SessionStart hook over unconditional install.
    Verdict: RUN NOW, own PR.

  QW-2 (macro-driver dedup, ~15 LOC + mutation-verified test):
    Run: immediately, BUT touches payload.py (a CF single-owner file).
    Decision: land QW-2 BEFORE CF takes the payload.py seat; CF rebases onto
    it. Do NOT single-source in a way that introduces a new payload->contract
    dependency (packet: narrowest already-valid shared location only).
    Verdict: RUN NOW as its own tiny tested PR, land before CF impl.

  Which can run immediately: QW-1, QW-4, QW-5, QW-2, Alignment check.
  Which folds into another lane: QW-3 (into CF).
  Which deserves its own tiny PR: QW-1, QW-2, QW-4, QW-5 (Wave A seam rule).
  Which waits to avoid collision: QW-3 (CF workflow), and QW-2/QW-1 must
  precede CF's grab of payload.py / resolve_run_mode.py.

WAVE B -- high-leverage friction reducers (alongside CF evidence/MATERIAL
and, once authorized, CF implementation):

  Estimation-rule graduation (F1): one PRD_PROCESS line -- highest
    leverage-to-cost in the audit. Fable review (governance wording), draft,
    owner-held. LAND BEFORE the CF MATERIAL packet sets its Gate-A ceiling.
  Mutation-runner utility (F2): small tools/ PRD with tests; earned by 3rd
    HIGH-RISK use (CF is that use). Standard Codex impl, Fable-lite spec
    review.
  PROJECT_STATE archival convention (F3): after owner rules the format
    (TD-14); then mechanical narratives -> prd_history pointers.
  Process-lesson graduation (F4): agent-workflow conventions (probe-before-
    fan-out, light-models-for-recon, commit -F, transcript salvage); Fable
    review, draft, owner-held.

WAVE C -- do NOT begin without explicit justification:
  runtime/ split continuation -- ONLY per the 2026-08-15 re-ruling.
  renderer decomposition (PRD-238) -- ONLY if post-CF renderer pressure
    appears. Registry R2/R3 is feature-lane work, not cleanup.

===================================================================
10. FRICTION-REMOVAL ESCALATION RULE
===================================================================

Rule (the "twice" trigger): if the same implementation or process friction
appears TWICE during the campaign, OPUS 4.8 stops working around it and
escalates to FABLE for root-cause classification. A single occurrence is
absorbed; the second is a signal, not noise.

FABLE classifies the response into exactly one of:
  - LOCAL FIX NOW: a bounded code/config change removes it (e.g. add a
    missing pip cache line). Do it, tiny PR, move on.
  - PROCESS FIX NOW: a one-line canonical-doc change removes the recurring
    trigger (e.g. F-1 estimation rule -> PRD_PROCESS). Draft, owner-held.
  - NAMED DEBT: real but not now; record in PROJECT_STATE known-debt with a
    re-eval trigger. Do not fix in-lane silently.
  - OWNER RULING: the friction encodes an unresolved owner choice (e.g. TD-4
    intent, full-suite-per-run policy). Queue it (Section 8), do not guess.
  - LEAVE ALONE: the friction is the cost of a deliberate posture (e.g.
    full-pytest-before-scheduled-runs is verify-where-truth-is-determined).
    Document why, stop re-raising it.

Already-known recurring frictions and their pre-classified responses (so the
first occurrence this campaign is already triaged):
  - LOC estimation miss (F-1, fired 2x on PRD-288/289): PROCESS FIX NOW.
  - Manual mutation ceremony (F-2): LOCAL FIX (mutation-runner), earned now.
  - Harness/orchestration fragility (F-3): PROCESS FIX (graduate the proven
    conventions); LEAVE ALONE the underlying harness.
  - Cold install + full suite (F-4): LOCAL FIX pip cache (TD-9) + OWNER
    RULING on suite policy.
  - Remote-session env unbootstrapped (F-5): LOCAL FIX (QW-5).
  - PROJECT_STATE reading cost (F-6): OWNER RULING on format (TD-14) then
    mechanical.

The goal is aggressive elimination of recurring drag -- not tolerance of
repeated workarounds, and not a standing invitation to widen scope.

===================================================================
11. CROSS-LANE CONSISTENCY GUARDS (carried from the Holistic Review 7)
===================================================================

Binding on all three lanes for the whole campaign:

  1. Deterministic observation only -- describe, never predict.
  2. Compute explicitly, display selectively; every cell is
     value-XOR-typed-unavailable; UPPER_SNAKE states, lower_snake reasons.
  3. Fail loud, never substitute-and-continue; every guard ships a
     mutation-verified red test (PRD-198).
  4. run_at_utc determinism is inviolable: no wall-clock in composers;
     observations keyed to data windows, never execution time.
  5. Additive integration only: additive payload sections, presence-gated
     renderer blocks, no schema-version bumps, decision contract
     byte-identical with the feature absent.
  6. No hidden cross-lane coupling and no premature shared infrastructure:
     the clock stays single-consumer; provenance stays per-domain until a
     third real instance exists.
  7. Secrets: header auth only, owner-held, never in query strings, the
     repo, or artifacts.
  8. Owner authority is explicit: content ratification, ceilings, Gate A,
     and every merge are Dustin's acts; agents deliver bounded choices,
     never inferred approval.
  9. One lane owns a shared seam at a time: payload.py / dashboard_renderer.py
     are single-owner (Cloudflare holds them during its implementation).

No additional guards are added -- these are necessary and sufficient for the
three lanes as scoped. (Adding more would be the premature-infrastructure
anti-pattern the set warns against.)

===================================================================
12. ABSTRACTION WATCHLIST (do NOT generalize prematurely)
===================================================================

  Pattern                              Status        Revisit trigger
  -----------------------------------  ------------  ------------------------------
  Additive payload/renderer section    NOT YET       The Morning Brief is copy #3
    wiring (optional field -> keyword                (after spy_observation,
    payload param -> additive sections               market_control_card). Copy #3
    key -> presence-gated block)                     makes generalizing ELIGIBLE,
                                                     not mandatory. Doing it inside
                                                     the CF slice widens scope ->
                                                     land the brief as copy #3.
                                                     REVISIT if/when GEX-2 would be
                                                     copy #4 -- and only if the
                                                     cost/benefit clearly justifies
                                                     it then.
  Provenance / freshness carriers      NOT YET       Morning Brief and GEX-1 each
    (value-XOR-typed-unavailable)                    build a domain carrier in the
                                                     SAME convention. Duplication is
                                                     not real-and-immediate (GEX-1
                                                     is 2 gates away). REVISIT AFTER
                                                     a 2nd real carrier ships and
                                                     the two visibly duplicate.
  Scheduler / trigger infrastructure   NOT YET       The Worker is scope-walled to
    (Cloudflare clock)                               one workflow + three slots.
                                                     REVISIT only when a 2nd
                                                     scheduled consumer has its own
                                                     owner ruling -- never by the
                                                     clock acquiring one silently.
  Registry consumers                   NOT YET       R1 ships zero consumers by
                                                     definition. REVISIT at R2, and
                                                     migrate per-consumer, bounded.
  Mutation tooling (F-2)               EARNED NOW    3rd HIGH-RISK use (CF) is the
                                                     earn point; build the small
                                                     tools/ utility, do not
                                                     over-generalize it into a
                                                     framework.

The single most important line here: the Morning Brief becoming copy #3 does
NOT by itself justify extracting a shared wiring primitive. The rule is
"eligible at 3, decide on cost/benefit," and doing the extraction inside the
CF slice is out of scope regardless. If GEX-2 later becomes copy #4, that is
the re-evaluation moment -- weighed on its merits, not automatic.

===================================================================
13. DAILY STATE JOURNAL -- OPTIONAL WILD-CARD EVALUATION (evaluate, do NOT authorize)
===================================================================

Idea: a deterministic daily state journal preserving key CuttingBoard
snapshots (PRE-MARKET, OPEN, OPEN+1, possibly CLOSE later) as a retrospective
benchmark -- to later ask whether Market Control / Morning Brief / future
context actually helped, WITHOUT optimization contamination.

Does Cloudflare create a natural seam for this? YES, partially, and this is
the important finding. The Morning Brief slice ALREADY introduces exactly the
primitive a journal would need:
  - The packet mandates an "observation-slot lineage" field (PREMARKET /
    OPEN / OPEN_PLUS_1) recorded on each immutable `logs/run_<ts>.json`
    (packet 4.1). Those immutable per-run artifacts already persist and
    already accumulate -- a journal is, at its smallest, a read-over of
    files the Brief will already be writing.
  - So the Brief does NOT need a journal, but it lays the seam: after it
    ships, each key moment's snapshot exists on disk, slot-labeled, keyed to
    run_at_utc. That is the raw material a journal would index.

Is there a tiny additive archival version worth planning soon? There is a
DEFENSIBLE tiny version -- a read-only index/pointer over the already-written
immutable run files, adding no new capture and no new decision surface. But
note the packet EXPLICITLY walls this out of the CF slice ("Explicitly NOT a
new historical subsystem"; "any new historical/query subsystem" is a scope
wall and a STOP condition). So even the tiny version is a SEPARATE lane, not
a CF rider.

Recommendation: DEFER until the Morning Brief proves itself. Three reasons.
(1) The seam is a free byproduct of CF -- waiting costs nothing, because the
immutable slot-labeled artifacts will already exist to index later. (2) The
"does the card change behavior" trap question (VISION's named risk) is
answered first by real-use OBSERVATION of the shipped card, which is already
the #1-ranked zero-cost arc -- a journal is only worth building once there is
something proven worth benchmarking. (3) Building it now risks exactly the
contamination the idea is meant to avoid: a benchmark built before the thing
it benchmarks exists tends to encode assumptions about what "helped" looks
like. Let the Brief ship, observe it in anger, and only then decide whether a
read-only journal-index earns a lane.

NOT in the active execution DAG. No compelling reason to pull it forward.
Recorded here as a post-CF candidate with a named, cheap seam.

===================================================================
14. FAILURE / STOP MATRIX (hard stops per active lane)
===================================================================

CLOUDFLARE / MORNING BRIEF:
  Lane stops entirely if:
    - CF-E1 shows the Cloudflare -> GitHub dispatch path cannot work under
      least-privilege auth (no fallback authorized without fresh recon +
      owner ruling).
    - Dustin declines CF-D5 (infrastructure ownership) -- no agent-held-
      secret alternative exists by design.
    - CF-E2 shows premarket quote semantics unusable AND first-bar latency
      incompatible with OPEN/OPEN+1 (premarket-half-only failure merely
      narrows the slice via CF-D1b/CF-D2 -- it does NOT stop the lane).
  Boundary reset (stop, re-run GOV-2 classification / amend upstream):
    - any 7th-production-file class of growth; any PAYLOAD_SCHEMA_VERSION
      bump or required-key change; any touch of the three read-only
      producers; any notification-reach expansion; any 2nd scheduled
      consumer proposed for the Worker; premarket bar ingestion (prepost)
      creeping in; LOC past the Gate-A ceiling (GOV-2 5).
    - external auth/trigger model cannot meet the security boundary.
    - DST / market-day semantics unresolved.
    - scope expands into a generic scheduler platform.
    - material-gap definition lacks an owner ruling.
    - payload/render ownership collision (two active branches editing).

REGISTRY / NEWS-0:
  Lane stops entirely if:
    - Dustin declines to ratify any universe/theme content (a registry with
      only unratified content has no consumers-to-be -- park, don't build).
    - GOV-2 intake + owner ruling redirect the deliverable so materially
      that the context-only doctrine boundary breaks -- that contradiction
      goes back to Dustin, not into the packet.
  Boundary reset:
    - owner semantics unresolved (drafting past REG-D2 blind).
    - registry starts absorbing decision config (HALT_SYMBOLS, PRICE_BOUNDS,
      SYMBOL_UNITS, SYMBOL_SOURCE_PRIORITY, EXPANSION_LEADERSHIP_SYMBOLS,
      the correlation pair).
    - consumer migration (R2) creeping into R1.
    - any renderer/payload/runtime file entering FILES.
    - any numeric/scoring field proposed for the schema.
    - ontology expanding beyond the approved axes (pairwise relationships
      arriving before their evidence trigger).
    - LOC past the eventual Gate-A ceiling.

GEX:
  Terminal lane stops:
    - licensing/redistribution prohibits caching OR public-dashboard
      display (row 11 alone -> NOT VIABLE).
    - required fields/coverage unavailable (no per-contract OI or greeks/IV
      path; no usable spot basis).
    - field semantics unestablishable for honest labeling (row 3
      unresolvable).
    - provenance inadequate (no trustworthy as-of/observation times).
    - auth contract unacceptable (query-string-only credentials).
    - egress unavailable after GEX-D1 (2nd INCOMPLETE ends the track pending
      fresh owner ruling -- NOT a retry authorization).
    - rate limits make even manual snapshots impractical.
  Boundary resets (stop and re-classify/escalate):
    - provider substitution or comparison attempted without authority.
    - GEX beginning to influence decision contract / permissions / sizing.
    - required freshness that cannot be truthfully represented (would force
      fabricated freshness -- G6 violation).
    - any proposal to couple GEX to the clock, Brief, registry, or card.

HEALTH CLEANUP (all waves):
  - cleanup touches feature semantics -> STOP, it is not cleanup.
  - a "small" utility becomes platform work -> STOP (mutation-runner must
    stay a utility, not a framework).
  - an omnibus cleanup branch appears -> STOP; Wave A is seam-bounded,
    one PR per seam, never a batch.

===================================================================
15. REVIEW STRATEGY
===================================================================

Per-lane review, minimized to what governance requires -- no redundant
review, no review-of-review (GOV-1: disagreement is Dustin's to adjudicate).

  - OPUS self-review: on every branch before requesting the required review
    (author disciplines: dead-branch enumeration, downstream-consumer audit,
    realizability, sub-agent sweep re-verification).
  - FABLE review ONLY where a semantic/design choice remains: CF and Registry
    MATERIAL packet drafts (vocabulary/boundary/failure semantics); the
    estimation-rule and process-lesson graduations (governance wording); the
    GEX terminal-verdict framing. NOT on mechanical quick wins.
  - CODEX external read-only review: the two GOV-2 auto-commissioned events
    per MATERIAL lane -- upstream packet review AND exact-corrected-head
    confirmation (`codex exec -s read-only`, effort <= high, verdict from
    stdout, artifact written by Claude Code). Nowhere else at agent
    discretion.
  - Fresh-context independent PRD review: required for every MATERIAL PRD
    (CF, Registry, GEX-1) -- from fresh context, NOT the packet author or
    same-session implementer, recorded against the exact reviewed SHA. A
    qualified fresh-context second model may fill this seat; selecting Codex
    for it needs a separate PRD-242 commission.
  - Routine implementation review: exactly one fresh-context review per PR
    plus the connector bot's advisory triage (never gate-satisfying).

SEPARATION-OF-DUTIES (explicit, the "same model must not author AND
independently review the same semantic decision"):
  - Whoever DRAFTS the CF MATERIAL packet does NOT perform its fresh-context
    PRD review.
  - Whoever DRAFTS the Registry schema does NOT review the Registry PRD.
  - OPUS as HELM interprets/implements; it does NOT provide the fresh-context
    independent review of its own implementation -- that is a different
    fresh context (Fable or a commissioned second model).
  - The Codex exact-head confirmation reads the corrected head SHA + the
    prior findings list; it is a confirmation, NOT a fresh-scope review, and
    NOT a review of another review.

===================================================================
16. CI / TEST STRATEGY
===================================================================

Phases (fastest feedback first, full proof preserved):
  1. TARGETED test phase (iteration): run only the lane's affected test
     modules locally on every change. Cheap, tight loop.
  2. MUTATION phase: for each guard, apply the mutation -> confirm the
     targeted test goes RED -> revert -> confirm GREEN. Emit the table. The
     F-2 mutation-runner utility (once built) automates the apply/revert so
     this stops being hand-attested.
  3. FULL-SUITE phase: run the entire pytest suite once before requesting
     pre-commit review -- backgrounded when long enough to work in parallel.
     Do NOT weaken the full-suite-before-scheduled-run policy; that is an
     owner-only trade (verify-where-truth-is-determined).
  4. CI phase: the gate. Environment parity with CI is authoritative;
     local/sandbox green is unverified until reproduced where the decision
     is made (PRD-198 #5). Remote/mobile sessions MUST bootstrap (QW-5)
     before trusting local pytest -- 85 misleading collection errors on an
     unbootstrapped env is a known trap.
  5. EXACT-HEAD CONFIRMATION: GOV-2 lanes only, on the corrected head SHA.

Safe speedups (no proof weakening):
  - QW-3 pip cache: removes cold-install latency from every scheduled run --
    the single biggest safe CI speedup, and it serves the exact schedule the
    Morning Brief exists to feed.
  - Light models + targeted greps for recon (not CI): keeps the token cost
    of fact-gathering low.
  - Background the full suite while doing other work; poll with an
    until-loop, not a fixed sleep. (Note: `gh pr checks` has no --json and
    exits instantly -- do not build a naive poll loop on it.)

Do NOT: change --skip-commit-resolvability (WONTFIX-HISTORICAL); drop the
full suite before scheduled runs; treat a green sandbox as a green gate.

===================================================================
17. MASTER MERGE ORDER (collision-accounted)
===================================================================

Cloudflare-first refers to the FEATURE IMPLEMENTATION seat. A tiny
independent truth/docs cleanup MAY merge before it if it does not delay CF.

  1. QW-4 (GEX docs-drift, docs-only)          -- independent, merge first
  2. QW-1 (resolve_run_mode comment)           -- before CF touches the file
  3. QW-5 (dev bootstrap)                       -- independent
  4. QW-2 (macro-driver dedup, payload.py)      -- BEFORE CF grabs payload.py
  5. QW-3 (pip cache)                           -- FOLD INTO CF, or land here
                                                   then CF rebases
  6. CLOUDFLARE / MORNING BRIEF                 -- the feature seat
  7. REGISTRY / NEWS-0 R1                        -- disjoint files; own clock
  8. GEX evidence addendum (docs)               -- any time; low-contention
  9. Conditional GEX-1                          -- only if VIABLE + go
  10. Wave B friction reducers (F1 estimation ideally before CF's ceiling;
      F2 mutation-runner; F3 PROJECT_STATE archival; F4 process graduation)

Collision rationale: items 1-5 are ordered so that every file CF will own
(payload.py via QW-2, resolve_run_mode.py via QW-1, cuttingboard.yml via
QW-3) is settled BEFORE CF takes its single-owner seat -- so CF rebases once,
cleanly, onto a stable base, and no quick win races CF mid-flight. Registry
(7) and GEX (8) are disjoint from CF and from each other; their order is by
contention, not dependency.

===================================================================
18. CAMPAIGN BOARD (working control board for the next session)
===================================================================

WORK ITEM        READINESS        MODEL     START  BLOCKER            WORKTREE/BRANCH              MERGE  STOP CONDITION
                                  OWNER     NOW?
---------------  ---------------  --------  -----  -----------------  --------------------------   -----  ------------------------------
CF ruling bundle PLANNING-READY   OWNER     YES    none               (owner act)                  n/a    CF-D5 declined -> lane stops
CF-E1 trigger    PLANNING-READY   CODEX     after  CF-D5 (PAT+deploy) cf-morning-brief-evidence    n/a    auth unworkable -> escalate
CF-E2 quote/bar  PLANNING-READY   CODEX/LT  after  CF-D* issued       cf-morning-brief-evidence    n/a    both semantics+latency fail
CF MATERIAL pkt  PLANNING-READY   FABLE/dsn after  CF-E1+E2+rulings   cf-morning-brief-packet      n/a    7th-file / schema bump
CF impl          NOT READY        OPUS+CDX  no     Gate A (far)       cf-morning-brief-impl        1      Section 14 CF resets
Registry pkt     MATERIAL-PKT-RDY OPUS/dsn  YES    owner authorize    registry-material-packet     n/a    owner won't ratify -> park
Registry R1 impl NOT READY        CODEX(hi) no     REG rulings+GateA  registry-r1                  7      decision-config absorption
GEX-D1..D4       BLOCKED          OWNER     YES    none               (owner act)                  n/a    -
GEX-0 continu.   BLOCKED          CODEX     after  GEX-D1+D2          gex-0-continuation           8      2nd INCOMPLETE ends track
GEX-1 producer   NOT READY        OPUS+CDX  no     VIABLE+go (cond.)  gex-1 (later)                9      NOT VIABLE / licensing
QW-1 comment     READY            CODEX-lt  YES    none (pre-CF)      chore-resolve-run-mode       2      touches CF file -> pre-CF
QW-2 macro dedup READY            CODEX-lt  YES    none (pre-CF)       chore-macro-drivers-dedup    4      new payload->contract dep
QW-3 pip cache   READY            CODEX-lt  seq    CF workflow edit   fold into CF                 5      races cuttingboard.yml
QW-4 GEX docs    READY            CODEX-lt  YES    none               chore-gex-docs-drift         1      -
QW-5 bootstrap   READY            CODEX-lt  YES    none               chore-dev-bootstrap          3      unconditional-install smell
Alignment check  DUE              OWNER     YES    none               (owner act + LIGHT diff)     n/a    -
TD-4 SMCI fix    OWNER-RULING     OWNER->lt YES*   intent ruling      chore-smci (after ruling)    A      -
F1 estimation    candidate        FABLE     YES    owner-held draft   gov-estimation-rule          10     -
F2 mutation-run  earned-now       CODEX+FBL after  small spec         tools-mutation-runner        10     becomes a framework
F3 proj-state    OWNER-RULING     OWNER->lt no     TD-14 format rule  chore-project-state-archive  10     -
F4 process grad  candidate        FABLE     YES    owner-held draft   gov-process-lessons          10     -

(*TD-4 "YES" = the ruling can be asked now; the fix waits on it.)

===================================================================
19. EXACT FIRST ACTIONS (operational, for Opus at execution start)
===================================================================

  1. Synchronize main: `git pull --ff-only origin main`; confirm HEAD ==
     origin/main; report both SHAs. (Currently 7d0805e -- reconfirm at start,
     other work may have landed.)

  2. Preserve the planning artifacts if the owner chooses: the reconciliation
     branch `claude/cuttingboard-reconciliation-notes-op3p8w` (tip a853e8c)
     is DOCS-ONLY (8 files under audits/reconciliation-2026-08/, zero
     production files). Offer Dustin a clean docs-only PR to land them on main
     as durable planning record, OR leave on the branch per the PRD-230
     session-scratch lifecycle (delete once absorbed). Owner's call -- do not
     merge unbidden. If landed, add this master plan alongside as the 9th
     artifact.

  3. Issue the bounded owner-ruling bundle (Section 8 NOW group, one sitting):
     CF-D1a/D2/D3/D4/D5/D6 + commission CF-E1/E2; GEX-D1..D4; authorize the
     Registry MATERIAL packet draft (+ optional REG-D2); run the due
     Alignment check. Present as bounded choices, not open questions.

  4. Launch the independent Wave A cleanup branches (Track D), each its own
     tiny PR, held for owner merge: QW-4 (docs), QW-1 (comment), QW-5
     (bootstrap), QW-2 (payload dedup -- land before CF). Use the Section 6
     Codex contract for each. Do NOT batch them.

  5. Commission CF evidence (Track A) once CF-D5 lands: CF-E1 (needs owner
     PAT + Worker deploy), CF-E2 (one ~6:00 PT and one ~6:32 PT market-day
     capture). Read-only in product terms; branch cf-morning-brief-evidence.

  6. Commission the Registry MATERIAL packet draft (Track B) in parallel:
     design-class drafter, schema + seeded-unratified content + news-schema
     proposal, built to present REG-D1..D7 as bounded choices; ask REG-D2
     first. Branch registry-material-packet. Held for Codex packet review +
     owner rulings.

  7. Commission the GEX-0 continuation (Track C) once egress is granted:
     read-only network pass against api.polygon.io only, existing 16-row
     checklist verbatim, terminal-verdict discipline, docs-only addendum in
     the existing GEX audit folder. Branch gex-0-continuation.

  8. Land F1 (estimation-rule graduation) as a Fable-reviewed, owner-held
     governance draft BEFORE the CF MATERIAL packet sets its Gate-A ceiling
     -- so the third GOV-2 5 stop-and-renew does not fire on the same
     arithmetic.

  9. When CF evidence + rulings are in hand: draft the CF MATERIAL packet
     (Section 6 discipline), submit for the Codex packet review + exact-head
     confirmation, then present Dustin the design-direction ruling. Only THEN
     open the Stage-0 PRD (PRD-290), get the fresh-context review, and request
     CF Gate A. Implementation is downstream of all of that -- not in the
     first window.

  10. Maintain the anti-drift discipline throughout: every long-lived branch
      does an ff-only reconcile at its next active step after any merge to
      main; request an owner rebase (deny list) rather than accumulate silent
      drift. Keep the Section 18 board current as the session's control
      surface.

===================================================================
20. FINAL VERDICT
===================================================================

CLOUDFLARE-FIRST:
  CONFIRMED. Survived the explicit challenge test in all three lane packets
  and the Holistic Review. The only argument against it -- Registry's greater
  procedural readiness -- is a process fact, not a product one, and it
  dissolves under parallelism (Registry packet drafts concurrently while CF
  holds the seat). Nothing is time-sensitive, no dependency crosses lanes,
  and CF-first front-loads the plan's only external unknowns (CF-E1/CF-E2).
  No correctness/safety blocker was found that would invalidate the lane
  (P0: none; TD-4 is conservative-direction and one line once ruled).

PARALLEL EXECUTION:
  SAFE WITH SERIALIZED SEAMS. The three lanes plus Wave A/B run concurrently;
  the ONE standing serialization is single-ownership of delivery/payload.py
  and delivery/dashboard_renderer.py (Cloudflare holds both during
  implementation), plus the pre-CF ordering of the three quick wins that
  touch CF's future files (QW-1, QW-2, QW-3). Every other surface is disjoint
  by construction.

CODEX AUTONOMY:
  HIGH -- for packet-frozen, semantics-closed work: Registry R1 build, the
  GEX-0 continuation pass, all five quick wins, and post-Gate-A CF
  implementation slices. MODERATE-to-LOW elsewhere: any step with an open
  owner semantic (CF pre-CF-E2, Registry pre-REG-D2, the GEX terminal
  verdict, TD-4) is NOT autonomous -- it escalates. The Section 6 contract's
  stop-and-escalate triggers are the guardrail that makes HIGH autonomy safe:
  autonomy is high where the finish line is exact, and the moment an exact
  finish line dissolves (FILES expansion, schema bump, new dependency, owner
  semantic), Codex stops rather than best-efforts.

FABLE ESCALATION -- exact trigger conditions:
  - Any friction that recurs a SECOND time in the campaign (Section 10).
  - Any architecture ambiguity a packet did not compile out.
  - Any cross-lane conflict or a lane reaching for another lane's seam.
  - Any governance/materiality question (GOV-2 classification edge, ceiling
    increase, new material boundary).
  - Opus circling / losing context / repeating a workaround.
  - Any semantic choice left open in a spec Codex is executing.
  - Owner-decision shaping (turning a raw ask into a bounded choice set).

HANDOFF:
  READY FOR EXECUTION -- ONE BOUNDED ISSUE REMAINS: the owner-ruling bundle
  (Section 8 NOW group) must be issued before any lane leaves the starting
  line. That is an owner act, not an engineering gap. With it issued, all
  four tracks move in parallel under the ownership, merge-train, and
  stop-condition discipline above. Nothing here implements, authorizes Gate
  A, opens an implementation PR, or merges feature work.
