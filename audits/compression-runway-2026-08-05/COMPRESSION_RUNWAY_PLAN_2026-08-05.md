# CuttingBoard Remaining-Work Compression & Product Runway Plan

Date: 2026-08-05
Status: PLANNING PACKET — authorizes no implementation, allocates no PRD number,
changes no lifecycle state. Ratified route: BALANCED (Dustin, 2026-08-05).
Baseline reviewed: `origin/main` @ `a419b80` (PRD-288 closeout, PR #218).
Revision: 2 — incorporates Dustin's 2026-08-05 corrections and rulings.

---

## Context

Commissioned planning pass (read-only) to compress the remaining CuttingBoard
work into the shortest safe route to GEX context, relationship-aware news,
universe/heatmap views, and richer trader-facing market context — deep enough
that subsequent sessions execute from this roadmap instead of reconstructing
repository state.

Dustin approved the BALANCED route and issued the rulings recorded below. This
revision incorporates his three corrections:

1. PR #184 is superseded through one TRUTH-SYNC PR (which imports its two
   evidence artifacts under an explicit historical/out-of-order banner), not
   merged separately. One docs PR, one review, one Dustin merge.
2. PRD-283 evidence reconciliation is an honest-chronology validation of the
   landed implementation — never described as retroactive authorization.
3. GEX-0's verdict set is `PROVIDER VIABLE` / `PROVIDER NOT VIABLE` /
   `EVIDENCE INCOMPLETE` — a one-provider bounded pass cannot conclude
   "no viable provider exists."

**Verified baseline** (re-verified this session, not taken from the handoff):

- `origin/main` @ `a419b80`. Test baseline 3245 passed / 1 xfailed (CI truth
  for `68cca76`). `next_prd: 289`, `latest_complete: 288`.
- One open PR: **#184** (DRAFT, OPT-0 seam-trace packet + Late Connector
  Addendum, branch `worktree-opt-0-seam-trace`, untouched since 2026-08-01).
- **The handoff claim "PRD-283 … is not yet authorized for implementation" is
  stale.** PRD-283's production code is merged and live on `main`
  (`f806f5b2a0f6bccd7db67424ab4c2d5117454bb0`, 2026-08-03, "PRD-283: refuse
  when smallest options contract exceeds risk budget", 8 production + 10 test
  files — exactly its FILES ceiling; connector thread on PR #204 dispositioned
  ACTIONED with mutation-verified tests). What never landed is the surrounding
  evidence chain: registry/index/PRD-doc still IN PROGRESS, no
  `PRD-283.review.*.md` artifact, no Gate A entry in DECISIONS.md, the
  upstream OPT-0 packet exists only on unmerged draft PR #184, and the CB-02
  row in FINDING_STATUS_MATRIX still reads OPEN/Critical. The 2026-08-05
  bookkeeping recovery sweep (`6f8d902`, PR #211) covered
  PRD-284/285/286/287/271 and skipped 283.
- **Chronology to preserve, verbatim, in every reconciliation artifact: the
  implementation landed before the complete governed evidence chain was
  durably recorded. The later review and closeout reconcile truth; they do
  not rewrite authorization history.**

---

## Dustin rulings (2026-08-05) — recorded

1. **Route: BALANCED.** This ruling doubles as the runway reassessment DR-001
   required after CB-02 landed; TRUTH-SYNC records it as a dated DECISIONS
   entry.
2. **PRD-283:** commission one independent fresh-context review of the exact
   merged implementation commit
   `f806f5b2a0f6bccd7db67424ab4c2d5117454bb0`; record that review as
   **validation of the landed implementation**; then incorporate and
   disposition it in TRUTH-SYNC. Honest evidence closeout — chronology
   preserved, no retroactive authorization claimed.
3. **PR #184: supersede through TRUTH-SYNC; do not merge separately.**
   TRUTH-SYNC imports its two evidence artifacts with an explicit
   historical/out-of-order banner; #184 is then closed as superseded.
4. **PRD-268: PARK** with a demonstrated-need reopen condition. This closes
   L0's remaining tail.
5. **GEX-0: commission immediately and run in parallel.**
6. **Registry: agent drafts from existing repository seeds; Dustin ratifies.**
7. **PRD-275: return to PROPOSED; non-blocking.**
8. **MACRO-0: KEEP DORMANT.**
9. **PRD-274: retain as non-blocking MICRO debt.**

Remaining open owner gates (future, in sequence): registry ratification after
the draft; GEX-0 go/stop after its verdict; NEWS-2 KEEP/REVISE/RETIRE; every
Gate A; every merge (GOV-1).

---

## A. Executive summary

**What happens next.** Two agents dispatch immediately: the PRD-283
exact-merged-head reviewer (Prompt J0) and the GEX-0 provider-evidence agent
(Prompt J3, commissioned per ruling 5). TRUTH-SYNC (Prompt J1) dispatches once
J0's artifact exists, consuming it plus rulings 1–4 and 7–9 — one docs PR, one
fresh-context review, one Dustin merge. The registry-packet agent (Prompt J4)
drafts from repository seeds for Dustin's ratification (ruling 6). The NS-2E
Market Control Card packet (Prompt J2) runs in parallel throughout.

**Path to GEX** (owner gates only — engineering is parallel):

1. TRUTH-SYNC merges (closes L0, which the workplan sets ahead of GEX-0's
   start; GEX-0 preparation already runs in parallel per workplan §10).
2. GEX-0 verdict → Dustin's go on `PROVIDER VIABLE`.
3. GEX-1 manual cached producer (MATERIAL packet + PRD,
   red-folder/macro-awareness patterns) → Dustin inspects real artifacts →
   GEX-2 display-only daily card (PRD-288 card recipe). No cadence, no
   decision effect.

**Path to news** (the long pole is registry ratification, not engineering):

1. TRUTH-SYNC closes L0 (workplan gate for NEWS-0).
2. Combined **context-registry packet** (NS-4A universe registry + NEWS-0
   relationship registry — substantially the same object). Agent drafts from
   seeds; Dustin ratifies content plus the two missing doctrine anchors
   (heatmap vocabulary G-002; relationship path G-006 as presentation
   ordering).
3. Registry artifact PRD → NEWS-1 manual producer PRD (2–3 items, cap 5, no
   sentiment) → NEWS-2 KEEP → NEWS-3 display card. The same registry unlocks
   NS-4B heatmap in parallel.

**PRD-283's place:** as engineering it is done (merged 2026-08-03). Its
evidence closeout precedes the product lanes because the workplan freezes
NEWS-0/GEX-0 behind L0, DR-001 requires the reassessment ruling on the
record, and a merged EXECUTION-class change must not remain labeled IN
PROGRESS with no review artifact. Cost: one commissioned review + one docs PR.

**Sequencing principle:** *one truth-sync, then three parallel lanes* —
product-NEXT (NS-2E), GEX (evidence → producer → display),
registry/news/heatmap — converging only at Dustin's gates. Every new surface
reuses the PRD-288 recipe (carrier or versioned sidecar artifact → optional
payload section → guarded daily card, freshness states + reason tokens,
absent-by-default, mutation plan) so no feature invents architecture.

---

## B. Verified current roster

Every row re-verified against the working tree at `a419b80` and GitHub state;
none trusts a status label. Dispositions marked *(ruled)* are Dustin's
2026-08-05 rulings.

| Item | Label says | Verified remaining work | Blocker type | Blocks GEX? | Blocks news? | Disposition | Evidence |
|---|---|---|---|---|---|---|---|
| **PRD-283** smallest-contract refusal (CB-02) | IN PROGRESS | **None in code** — merged `f806f5b` 2026-08-03, 8 prod files live, tests in. Remaining: independent review of the exact merged head, then closeout flip (registry row 303, index, doc STATUS), chronology DECISIONS entry, FINDING_STATUS_MATRIX row | Evidence work | Governance-yes (via L0/DR-001), engineering-no | same | **Exact-merged-head review (J0), then honest evidence closeout in TRUTH-SYNC** *(ruled)* | `git merge-base --is-ancestor f806f5b origin/main`; `PRD-283.md:350-366`; recovery sweep `6f8d902` skipped 283 |
| **PR #184** OPT-0 seam-trace packet | Open DRAFT | Disposition only — PRD-283 names it "the preserved upstream MATERIAL packet"; its two artifacts exist nowhere on `main` | Sequenced work | No | No | **Supersede through TRUTH-SYNC** *(ruled)*: import both artifacts with a historical/out-of-order banner; close #184 as superseded after merge | PR #184 body/files; `PRD-283.md:26-39`; GOV-2 §12 |
| **L0** lifecycle reconciliation | IN PROGRESS | PRD-268 disposition (now ruled: PARK) + bookkeeping; 267/271/272/273 already reconciled | Bookkeeping | **Yes** — workplan: "GEX-0 … after L0" | **Yes** — "NEWS-0 begins only after L0" | **Complete in TRUTH-SYNC** | workplan §2 rows; Program:83,96,468 |
| **PRD-268** hourly coverage-reason | IN PROGRESS | Empty Stage-0 scaffold, design fork unruled | — | Via L0 | Via L0 | **PARK with demonstrated-need reopen condition** *(ruled)* | `PRD-268.md:13-52` (all TODO) |
| **PRD-275** review-artifact append-only enforcement | IN PROGRESS | Empty scaffold, "BLOCKED — DO NOT IMPLEMENT AS SKETCHED", six undismissed constraints | Design constraints | No | No | **Return to PROPOSED; non-blocking** *(ruled)* | `PRD-275.md:20-44`; DECISIONS 2026-07-26 ("None is dismissed") |
| **PRD-274** ruff lint baseline | IN PROGRESS | Empty MICRO scaffold with binding scope note | — | No | No | **Retain as non-blocking MICRO debt** *(ruled)* | `PRD-274.md:16-45` |
| **DR-001 runway reassessment** | Required, unrecorded | A dated ruling — NS-2A/B/C + Product Rescue (PRD-279–282) ran after CB-02 landed with no recorded reassessment | — | Formally yes | Formally yes | **Ruling 1 (BALANCED) is the reassessment**; TRUTH-SYNC records it | `95_POST_RATIFICATION_RULINGS.md:28-60`; no matching DECISIONS entry |
| **PROJECT_STATE / workplan / ledger drift** | — | ~8 stale claims: "Active PRD: none" vs 4 IN PROGRESS rows; GOV-0/GOV-1/#187 described as unmerged (all merged); D-RULE/OPT-0/OPT-1 rows stale; NS-2A/B/C still `NEXT`; PRD-283 absent from Recent-ships | Doc correction | Indirect | Indirect | **Fold into TRUTH-SYNC** | PROJECT_STATE:12-28,199,216; Ledger:132-134; workplan §2 |
| **DOC-0** stale proposal headers | PROPOSED | Two header corrections (PRD-251/PRD-259 proposals) | — | No | No | **Fold into TRUTH-SYNC** (activates doctrine G10's header guarantee) | workplan §2 |
| **MACRO-0** PRD-187/188 fate | HELD FOR DUSTIN DECISION | One three-way choice; packet never run | — | No | No — doctrine firewalls macro-awareness from news | **KEEP DORMANT** *(ruled)*; skip the packet | doctrine §3.4; workplan §6 |
| **PRD-188** SHOCK banner / **PRD-209** bar-count floor | PROPOSED / SHELVED | Parked by design | Parked | No | No | **No action** | PRD-188 GATE comment; PRD-209 header |
| **NS-2E** Market Control Card | NEXT, not started | Full chain: MATERIAL packet → D-ruling → PRD → Gate A → build | Sequenced work | No | No | **Start packet in parallel lane** (Prompt J2) | Ledger:136; Program:104,318 |
| **NS-4A/4B** universe registry + heatmap | LATER | Full chain; heatmap vocabulary lacks a doctrine anchor (G-002 PARTIAL) | Owner ratification + sequenced work | No | **NS-4A gates news** (registry = NEWS-0 substrate) | **Combined registry packet with NEWS-0; agent drafts, Dustin ratifies** *(ruled)* (Prompts J4/J5) | Program:129-132,320-322; audit G-002/G-006 |
| **GEX-0** provider evidence | LATER / EVIDENCE BLOCKED | Never attempted — sole artifact re-dispositioned "NOT ATTEMPTED — EXTERNAL REACH DISABLED"; zero vendors ever named in-repo | External evidence | **Yes** — hard gate for any GEX code | No | **Commissioned immediately; runs in parallel** *(ruled)* (Prompt J3) | `stage0-04-gex-v0.1.md:35-62`; doctrine §4 |
| **PRES-0** (PRD-259 E/F/G), **runtime/ split** (re-eval 2026-08-15), **hourly SPY card + halt-time SPY** follow-ups, two MICRO script fixes | Deferred / debt | Various small | — | No | No | **Keep as dated non-blocking debt**; script fixes ride the next weekly polish PRD | PROJECT_STATE:199,312-350; PRD-288.md:118-125,346 |

Categorized: **must-complete before GEX/news** = J0 review + TRUTH-SYNC
(PRD-283 evidence closeout + L0 + DR-001 entry + drift sweep). **Evidence
work** = GEX-0; registry draft + ratification. **Implementation work** =
NS-2E, registry artifact, GEX-1/2, NEWS-1/3, NS-4B. **Governance debt
(non-blocking)** = PRD-275, PRD-274, PRES-0. **Parked by Dustin** = PRD-268,
PRD-188, PRD-209, NS-1C/1D. **Obsolete/satisfied** = OPT-1/PRD-278 line
(superseded by PRD-283), stage0-04's original GEX verdict (superseded),
D-RULE row (complete), "held PR" language for GOV-0/GOV-1/#187 (all merged).

---

## C. Dependency graph

```
main @ a419b80
│
├─ [J0] PRD-283 exact-merged-head review (independent, fresh-context,
│       review-only; sole write authority = its one review artifact on a
│       dedicated branch; pinned to f806f5b…) — dispatches immediately
│
├─ [T] TRUTH-SYNC PR  (docs-only; consumes J0's artifact + rulings 1–4,7–9)
│      imports PR #184's two artifacts w/ historical banner · PRD-283
│      honest closeout · L0 exit (PRD-268 PARK) · DR-001/BALANCED entry ·
│      drift sweep · DOC-0 · PRD-275→PROPOSED · MACRO-0 KEEP DORMANT ·
│      GEX-0 verdict-vocabulary amendment entry
│      → after Dustin's merge: PR #184 closed as superseded
│      ────► unlocks workplan gates "after L0" for GEX-0 & NEWS-0
│
│  ════ three parallel lanes (◆ = owner gate) ═══════════════════════
│
├─ LANE 1 (product NEXT)
│      packet(NS-2E) → ◆D-ruling → PRD → ◆Gate A → build → ◆merge
│      = MARKET CONTROL CARD          (no dep on GEX/news/registry)
│
├─ LANE 2 (GEX — commissioned, running in parallel from day one)
│      GEX-0 evidence pass → verdict {PROVIDER VIABLE | PROVIDER NOT
│      VIABLE | EVIDENCE INCOMPLETE} → ◆go/stop
│         → packet+PRD(GEX-1 producer) → ◆Gate A → build → ◆merge
│         → ◆Dustin inspects artifacts → PRD(GEX-2 display) → ◆Gate A → build
│      = GEX v1 (display-only daily card)
│
└─ LANE 3 (registry / news / heatmap)
       agent drafts registry from seeds → combined packet(NS-4A+NEWS-0)
          → ◆ratification (content + G-002 heatmap vocab + G-006
            relationship path as presentation ordering)
          → PRD(registry artifact) → ◆Gate A → build → ◆merge
             ├─► PRD(NS-4B heatmap) → ◆Gate A → build   = HEATMAP v1
             └─► PRD(NEWS-1 producer) → ◆Gate A → build
                    → ◆NEWS-2 (KEEP) → PRD(NEWS-3 display)
                    = NEWS v1 (briefing card)
```

- **Hard dependencies:** L0 → {GEX-0 execution, NEWS-0} (workplan law; GEX-0
  *preparation* is already safe-concurrent per workplan §10); GEX-0 viable +
  go → GEX-1 → GEX-2 (doctrine §4.4); registry → {NEWS-1, NS-4B}; NEWS-1 →
  NEWS-2 → NEWS-3 (doctrine §5.4); every MATERIAL packet → its PRD (GOV-2 §2).
- **Soft dependencies:** NS-2E after NS-2A/B/C (satisfied); heatmap benefits
  from Control Card conventions but does not require them.
- **Parallelizable:** the three lanes are file-disjoint; safe under workplan
  §10 provided registry/index/PROJECT_STATE edits serialize through one owner
  at a time.
- **Reusable shared foundations:** PRD-288 recipe (carrier → optional section
  → guarded card), freshness states + reason tokens, `red_folder.py`
  manual-cache loader shape, `macro_awareness.yml` workflow_dispatch producer
  pattern, `artifact_flow_map.md` registration, kv-grid/.block presentation
  primitives, MUTATION PLAN convention.

---

## D. Route

**BALANCED — approved (ruling 1).** [J0 + T] truth-sync first (one
commissioned review + one docs PR), then all three lanes in parallel per
Section C. Truth debt that matters (PRD-283 evidence, L0, DR-001, drift)
closes up front; product momentum continues through NS-2E while GEX/news
clear evidence gates that are owner/externally bound anyway. Every deferral
is explicit and dated.

Alternatives considered and set aside: *Fastest* (defer NS-2E behind
LATER-ranked work — inverts the ratified rank order for negligible wall-clock
gain, since the GEX/news critical paths are gated on decisions and external
evidence, not NS-2E engineering); *Maximum-conservatism* (full serial ledger
order with a retro GOV-2 §12 sequence — ~10+ owner gates before the first GEX
pixel, defensible only if the merged PRD-283 implementation itself were in
doubt; nothing found this pass supports that doubt).

---

## E. Proposed work packets (no PRD numbers allocated)

**E1. TRUTH-SYNC — one repository-truth reconciliation PR.** Purpose: single
docs-only PR, one fresh-context review, one Dustin merge, that (a) imports
PR #184's two evidence artifacts
(`OPT_0_SMALLEST_CONTRACT_REFUSAL_SEAM_TRACE_2026-07-31.md`,
`OPT_0_LATE_CONNECTOR_ADDENDUM_2026-07-31.md`) into
`audits/current-state-reconciliation-2026-07-30/` unmodified except a
prepended historical/out-of-order banner stating the actual chronology; (b)
incorporates and dispositions the independently produced J0 review artifact
as validation of the landed implementation; (c) closes out PRD-283 honestly
(doc STATUS, registry row 303, index; commit cell `f806f5b`; DECISIONS entry
preserving chronology — implementation landed before the governed evidence
chain was durably recorded; the closeout reconciles truth, it does not
rewrite authorization history; note the 8-vs-9 production-file ceiling
discrepancy between PRD and packet); (d) exits L0 (PRD-268 → PARK with
demonstrated-need reopen condition); (e) records rulings 1–9 as dated
DECISIONS entries including the BALANCED/DR-001 reassessment and the GEX-0
verdict-vocabulary amendment (doctrine §4.3's stop-verdict wording amended
per the doctrine's own four-step amendment rule: Dustin ruling + DECISIONS
entry + doctrine edit + manual merge — all riding this PR); (f) sweeps the
documented drift (PROJECT_STATE:12-28/199/216, workplan D-RULE/OPT-0/OPT-1
rows, Ledger NS-2A/B/C, FINDING_STATUS_MATRIX CB-02 row, DOC-0 headers); (g)
PRD-275 → PROPOSED; MACRO-0 → KEEP DORMANT recorded. After Dustin's merge,
PR #184 is closed as superseded (a comment citing the importing commit;
closing, not merging). Class/lane: GOVERNANCE, HIGH-RISK by matrix
(PROJECT_STATE/PRD_REGISTRY payload) — docs-only. Tests:
`tools/validate_prd_registry.py` green. Gate A: n/a (no production code).
Stop: J0 artifact missing → hold; J0 verdict adverse → stop and report to
Dustin before closeout.

**E2. GEX-0 — provider evidence pass.** Purpose: one provider vs the doctrine
§4.3 13-point honesty contract. Read-only research charge, network-enabled,
**zero repo code**; commissioned (ruling 5). **Verdicts (ruled): `PROVIDER
VIABLE`, `PROVIDER NOT VIABLE`, or `EVIDENCE INCOMPLETE`** — a verdict speaks
only to the one provider examined in this bounded pass; no verdict claims "no
viable provider exists." NOT VIABLE or INCOMPLETE ends the pass; any further
pass is a fresh Dustin commission. Evidence needed: access terms/cost, rate
limits, coverage, model label, field/flip/wall definitions, expiry scope,
cadence, source timestamps, spot basis, sample response, staleness + failure
behavior. Non-goals: no second provider, no abstraction, no schema, no PRD.
Stop: any load-bearing meaning unknowable → EVIDENCE INCOMPLETE with the
specific unknowns enumerated.

**E3. CONTEXT-REGISTRY — combined NS-4A + NEWS-0 MATERIAL packet.** Purpose:
one Dustin-ratified registry (symbols, aliases, themes, roles, horizons,
benchmarks, approved sources, enabled/disabled + reason) + proposed
news-artifact schema + the two doctrine-anchor questions (G-002 heatmap
vocabulary; G-006 relationship path as presentation ordering, not causality).
Agent drafts from repository seeds (`config.TREND_STRUCTURE_SYMBOLS`,
`market_map.PRIMARY_SYMBOLS`, Ledger suggested groups), flagging every
element beyond the seeds for ratification (ruling 6). MATERIAL → full GOV-2
§2 sequence. Downstream registry PRD ≈ 1–2 production files (loader +
validation, `red_folder.py` shape) + data file + tests. Non-goals: no
producer, no consumer, no network. Stop: content not ratified → packet holds
at DESIGN.

**E4. NS-2E — Market Control Card packet → PRD.** Compact orientation card
(state, location, event, transition, invalidation, permission, candidate
implication) replacing/refactoring the generic Market Map surface. MATERIAL
(crosses contract/renderer; no Control Card contract exists — Program:104).
Est. 3–5 production files, PRD-288-scale LOC; tests in the `test_dash_*`
family. Gate A: yes. Non-goals: no new data sources; no prediction; no
decision-bearing renderer derivation. Stop: Market Map retirement needs
dead-branch enumeration beyond ceiling → split.

**E5. GEX-1 — manual cached GEX producer.** Versioned snapshot artifact
(provider + model identity, symbol scope = primary universe only, gamma
flip, call wall, put wall, expiry scope, source/as-of + retrieved-at
timestamps, spot basis, freshness state + reason token, schema_version).
Manual `workflow_dispatch` refresh per `macro_awareness.yml`; provenance as
hard validation gate per `macro_awareness_collector.py`. Class SIDECAR
(observation), MATERIAL → packet + PRD + Gate A. Dependencies: GEX-0
`PROVIDER VIABLE` + Dustin go. Non-goals: **no consumer, no cron, no
pipeline imports, no decision effect** (doctrine G3/G4). Stop: provider
response diverges from GEX-0 evidence → halt, report.

**E6. GEX-2 — display-only daily card.** One guarded daily dashboard card via
the PRD-288 recipe; absent/stale/invalid ⇒ baseline byte-identical output.
Class CONSUMER; renderer is HIGH-RISK FILES → LANE HIGH-RISK. ~60–120 LOC
(`payload.py` + `dashboard_renderer.py`) + present/absent test pair.
Dependencies: GEX-1 landed + Dustin has inspected real artifacts. Non-goals:
no renderer-computed labels (threshold→label synthesis forbidden — relations
like spot-vs-flip are producer fields, mirroring `price_vs_vwap`); no
confidence, no cadence.

**E7. NEWS-1 — manual relationship-aware producer.** Deterministic artifact,
2–3 items normally, hard cap 5; fields per doctrine §5.2 + retrieved_at,
schema_version, dedup identity (macro-awareness precedent). Class SIDECAR,
MATERIAL → packet may be an annex to E3's ruling if the schema was ratified
there. Dependencies: registry landed. Non-goals: no sentiment/severity/
scores, no social ingestion, no dashboard panel, no cron (doctrine §5.3).
Stop: source outside approved allowlist → refuse item.

**E8. NEWS-3 — briefing display card** (after Dustin's NEWS-2 KEEP). Same
shape/ceremony as E6; groups items by the ratified relationship path as
*presentation ordering only*.

**E9. NS-4B — movement heatmap.** Grouped raw movement with visible freshness
("observe wide, trade narrow"), reading the registry + existing quote/trend
surfaces. Class CONSUMER (HIGH-RISK lane via renderer). Dependencies:
registry landed; G-002 ruling. Parallel with news lane. Non-goals: no
leadership/participation modes (NS-4C/D stay LATER), no new fetch paths.

---

## F. GEX v1 shape — confirmed with corrections

1. **Provider evidence is unskippable and truly greenfield.** Zero GEX vendors
   have ever been evaluated or named in-repo; the one prior negative verdict
   is formally superseded ("NOT ATTEMPTED — EXTERNAL REACH DISABLED",
   stage0-04:35-56). Existing providers (yfinance, Polygon free tier) carry
   no options-chain or GEX data (`data_sources.md`;
   `options_framework.md:5`). GEX requires a genuinely new source; hence
   GEX-0 first, exactly one provider, no fallback chain. **Verdict set per
   ruling: PROVIDER VIABLE / PROVIDER NOT VIABLE / EVIDENCE INCOMPLETE.**
2. **Snapshot fields** (doctrine-required): provider + provider-defined model
   label; expiry scope; source/as-of AND retrieved-at timestamps; spot basis;
   gamma flip; call wall; put wall; symbol scope = primary universe only;
   freshness state + reason token reusing PRD-288 vocabulary;
   `schema_version`; one writer, own versioned path, registered in
   `artifact_flow_map.md`.
3. **"Concise interpretation boundaries" — narrow it.** The renderer may not
   synthesize labels from thresholds. Any interpretive relation (spot
   ABOVE/BELOW flip) is computed in the producer as a descriptive field,
   mirroring `price_vs_vwap`. No regime language, no "supportive/hostile"
   glosses — description, not prediction (G1).
4. **Manual refresh, honest absence, no effects:** `workflow_dispatch`-only
   producer (macro-awareness workflow is the worked example, including
   re-validate-before-stage and publish-branch mechanics), card
   absent-by-default via section presence, stale/missing ⇒ baseline
   byte-identical, zero execution/confidence/cadence effect. Cadence is a
   separate later ruling (GEX-3), not presumed.

---

## G. News v1 shape — confirmed with corrections

1. **The registry is the foundation and is Dustin's.** NEWS-0's relationship
   registry and NS-4A's universe registry are substantially the same object —
   one registry, drafted by an agent from repository seeds, ratified once by
   Dustin (ruling 6). Agents flag everything beyond the seeds. Seeds:
   `config.TREND_STRUCTURE_SYMBOLS` / `market_map.PRIMARY_SYMBOLS` + Ledger
   suggested groups.
2. **Producer bounds are already law:** 2–3 items normally, hard max 5;
   fields per doctrine §5.2; deterministic relevance/dedup/freshness rules;
   manual-first, artifact-first; no sentiment scores, no invented causality,
   no social media, no LLM bullish/bearish labels (§5.3).
3. **The relationship path needs one ruling before display.** `GLOBAL STATE →
   THEME HEALTH → LEADERS → WATCHLIST → SETUPS` exists only as vision text
   with no doctrine anchor (audit G-006). Ratify it as *presentation
   ordering* in the E3 packet ruling.
4. **Display only after usefulness.** Doctrine G3/G8 forbid bundling producer
   + consumer: v1's briefing is first an artifact Dustin reads raw (NEWS-1),
   then a card only after NEWS-2 KEEP. The macro-awareness collector may not
   be renamed or widened into this track (doctrine firewall, §3.2).

---

## H. Reusable external-context substrate

**Share at the planning-contract level only; no shared code module now.**

- **Share now (as written convention in the E3 packet, referenced by every
  external-context schema):** the provenance/freshness vocabulary — source
  name, source url (where applicable), `as_of`/`published_at`,
  `retrieved_at`, freshness state set + snake_case reason tokens,
  `schema_version`, one-writer versioned path, dashboard
  omission-when-absent, diagnostic "unavailable" rendering. All already
  proven per-feature (RawQuote provenance, macro-awareness validation gate,
  red-folder expiry signal, PRD-288 freshness machine, `_timestamp_label`
  family).
- **Do not build:** a shared loader/framework/base-class. GEX and news differ
  in every hard part; doctrine G5/G8 want separate artifacts and separate
  bounded questions. Extract shared code only when a third external-context
  producer makes duplication real — cuts-before-additions applies to
  abstractions too.

---

## I. Owner decision state

Rulings 1–9 above are recorded; no open decision blocks dispatch of
J0/J1/J2/J3/J4. Remaining owner gates arrive in sequence with full context
attached: registry ratification (after J4's draft); GEX-0 go/stop (after its
verdict); NEWS-2 KEEP/REVISE/RETIRE (after NEWS-1 artifacts exist); each
Gate A on a reviewed PRD; each merge (GOV-1).

---

## J. Ready-to-dispatch prompts

Each prompt is self-contained and repository-verifying. Every dispatched
agent follows `docs/plans/agent-work-charge-template-v0.1.md` where its work
is governed by the expansion plans, reports blockers with exactly `Held for
your merge` or `Held for your decision`, never merges, and never appends
generated-by attribution to any repo content.

### J0 — PRD-283 exact-merged-head review (dispatch first)

```
You are a fresh-context independent reviewer for dwats250/cuttingboard. You
did not author or implement PRD-283 and share no session context with anyone
who did.

CHARGE: review the exact merged implementation commit
f806f5b2a0f6bccd7db67424ab4c2d5117454bb0 ("PRD-283: refuse when smallest
options contract exceeds risk budget", merged to main 2026-08-03) against
docs/prd_history/PRD-283.md, and record the review as VALIDATION OF THE
LANDED IMPLEMENTATION. Chronology (state it verbatim in the artifact): the
implementation landed before the complete governed evidence chain was
durably recorded; this review reconciles truth and does not rewrite
authorization history. Do not use authorization language (no "Gate A",
"approve for implementation", or equivalents).

WRITE AUTHORITY — exactly one file: you are review-only, but you are
authorized to create and commit exactly one durable artifact,
docs/prd_history/PRD-283.review.claude.md, on a dedicated review branch you
create from origin/main. You may not modify production code, tests,
PRD-283.md, docs/DECISIONS.md, docs/PRD_REGISTRY.md, docs/prd_index.json,
docs/PROJECT_STATE.md, upstream evidence files, or any other file. You must
not merge, must not open a PR, and must not change any lifecycle state.

PREFLIGHT (report all values; STOP on any mismatch):
- git fetch origin main; confirm f806f5b2a0f6bccd7db67424ab4c2d5117454bb0
  exists and `git merge-base --is-ancestor f806f5b2a0f6bccd7db67424ab4c2d5117454bb0 origin/main`
  succeeds.
- Create branch claude/prd-283-merged-head-review from origin/main; confirm
  `git status --short` empty.
- Read: docs/prd_history/PRD-283.md (in full), CLAUDE.md (Review gates,
  Semantic-failure hardening), docs/PRD_PROCESS.md (Review Dispatch, Review
  Failure Taxonomy), VISION.md.

REVIEW SCOPE:
- `git show f806f5b2a0f6bccd7db67424ab4c2d5117454bb0` — the full diff vs its
  parent. Verify: FILES boundary respected (8 production + 10 test files per
  PRD-283 FILES; note the packet's nine-file ceiling discrepancy as a
  finding, not a fix); each R1–R8 FAIL line is satisfied by observable
  behavior at the authoritative seam; OUT OF SCOPE retained-with-reason
  dispositions hold; mutation-plan claims correspond to real discriminating
  tests (spot-check at least three by reading the test bodies).
- Run the targeted tests the PRD names (record exact commands, exit codes,
  counts). Full suite only if targeted results are ambiguous.
- DRIFT CHECK (PRD-186): does the change conflict with any VISION.md
  non-goal/principle; does it leave any PROJECT_STATE.md claim stale (note:
  PRD-283's absence from PROJECT_STATE is known and being reconciled
  separately — record it, do not fix it).

ARTIFACT (docs/prd_history/PRD-283.review.claude.md): SHA-pinned header
naming f806f5b2a0f6bccd7db67424ab4c2d5117454bb0; the chronology statement;
VERDICT (VALIDATED / VALIDATED WITH FINDINGS / NOT VALIDATED); FINDINGS
tagged per the Review Failure Taxonomy; DRIFT CHECK; the memory-provenance
fresh-context confirmation. Commit only this file to your review branch,
push the branch, and end with: branch name, commit SHA, verdict, and
"Held for your decision."

STOP CONDITIONS: commit not found or not an ancestor of origin/main; any
edit outside the one authorized file would be required; verdict would be
NOT VALIDATED (still write and commit the artifact, then stop and report).
```

### J1 — TRUTH-SYNC reconciliation PR (dispatch after J0's artifact exists)

```
You are the TRUTH-SYNC reconciliation agent for dwats250/cuttingboard. This
is a docs-only charge: one PR, one fresh-context review, one Dustin merge.
You CONSUME the independently produced PRD-283 review artifact — you do not
produce, commission, or review it, and you never review your own
reconciliation (your PR receives its own fresh-context review per GOV-1).

INPUTS (verify each exists before starting; STOP if any is missing):
- The J0 review artifact docs/prd_history/PRD-283.review.claude.md on its
  review branch (branch name supplied at dispatch). If its verdict is NOT
  VALIDATED, STOP: "Held for your decision."
- Dustin's 2026-08-05 rulings (embedded below).
- The planning packet
  audits/compression-runway-2026-08-05/COMPRESSION_RUNWAY_PLAN_2026-08-05.md
  (branch claude/cuttingboard-compression-runway-rcff3m) — Sections
  "Dustin rulings" and E1 govern this charge.

RULINGS TO RECORD (dated 2026-08-05, ruled: Dustin): 1 route BALANCED (also
the DR-001-required runway reassessment); 2 PRD-283 exact-merged-head review
then honest evidence closeout; 3 PR #184 superseded through this PR;
4 PRD-268 PARK with demonstrated-need reopen condition; 5 GEX-0 commissioned
immediately, parallel; 6 registry drafted from repository seeds, Dustin
ratifies; 7 PRD-275 returns to PROPOSED, non-blocking; 8 MACRO-0 KEEP
DORMANT; 9 PRD-274 retained as non-blocking MICRO debt.

PREFLIGHT: branch from current origin/main; report both SHAs; clean tree;
read CLAUDE.md, docs/PRD_PROCESS.md, docs/DECISIONS.md (last 10 entries),
docs/PROJECT_STATE.md, docs/plans/decision-support-workplan-v0.1.md,
docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md.

WORK (docs-only; no production code, no tests, no new PRD numbers):
a) Import PR #184's two artifacts. `git fetch origin worktree-opt-0-seam-trace`
   (fall back to refs/pull/184/head). Copy
   OPT_0_SMALLEST_CONTRACT_REFUSAL_SEAM_TRACE_2026-07-31.md and
   OPT_0_LATE_CONNECTOR_ADDENDUM_2026-07-31.md into
   audits/current-state-reconciliation-2026-07-30/ byte-identical except one
   prepended banner block on each: "HISTORICAL EVIDENCE — IMPORTED OUT OF
   ORDER (2026-08-05): this packet's implementation (PRD-283, commit
   f806f5b2a0f6bccd7db67424ab4c2d5117454bb0, merged 2026-08-03) landed
   before the complete governed evidence chain was durably recorded. This
   import preserves the evidence; it does not rewrite authorization
   history. Source: PR #184 (closed as superseded by this import)."
b) Incorporate the J0 artifact: bring
   docs/prd_history/PRD-283.review.claude.md into this branch exactly as
   produced (cherry-pick its commit or copy byte-identical, citing the
   producing branch commit SHA in your PR body), and disposition its
   findings in the DECISIONS entry (ACTIONED here / recorded as debt / no
   action with reason).
c) PRD-283 closeout — through the prd-closeout-verified skill in hex-hash
   (post-merge) mode, never hand-rolled: PRD doc Status/STATUS → COMPLETE;
   registry row 303 → COMPLETE with commit cell f806f5b; prd_index.json;
   PROJECT_STATE Recent-ships row. DECISIONS entry states the chronology
   sentence verbatim and notes the 8-vs-9 production-file ceiling
   discrepancy between PRD-283 FILES and the packet's corrected ceiling.
d) L0 exit: PRD-268 doc header → "PROPOSED — PARKED (reopen only on
   demonstrated need: a concrete observed incident where the missing hourly
   coverage reason misled a session)"; registry/index status PROPOSED
   (registry permits no PARKED literal). Update the workplan L0 row exit
   state.
e) PRD-275 doc header + registry/index → PROPOSED with its BLOCKED design
   note retained; PRD-274 unchanged except confirming its row reflects
   MICRO debt.
f) DECISIONS entries for rulings 1–9 (one dated entry may carry them as a
   numbered list) including the GEX-0 verdict-vocabulary amendment, and the
   matching edit to decision-support-expansion-doctrine-v0.1.md §4.3:
   verdicts become PROVIDER VIABLE / PROVIDER NOT VIABLE / EVIDENCE
   INCOMPLETE, each speaking only to the one provider examined; the
   track-ending consequence and fresh-commission requirement are unchanged.
   Update the workplan GEX-0 row wording to match. Record MACRO-0 → KEEP
   DORMANT and update its workplan/ledger rows.
g) Drift sweep — correct only these known-stale claims, changing no policy:
   PROJECT_STATE lines 12-28 (GOV-1/GOV-0/#187 merged; Active-PRD line
   reflects post-sync truth), line 199 (PR #174 merged; stale queue text),
   line 216 (stale PRD-278 parenthetical); workplan rows D-RULE (COMPLETE),
   OPT-0/OPT-1 (superseded by PRD-283, pointer to the DECISIONS entry);
   Ledger/Program NS-2A/2B/2C → shipped (PRD-288/PRD-271) and NS-1E →
   resolved-by-PRD-283 pointers; FINDING_STATUS_MATRIX CB-02 row → RESOLVED
   with commit + review pointers; DOC-0's two proposal headers
   (PRD-251/PRD-259 proposals) corrected to current truth; mark DOC-0
   complete in the workplan.
VALIDATION: git diff --check; python tools/validate_prd_registry.py
--skip-commit-resolvability; confirm zero production/test files in
`git diff --name-only` vs main.
LANDING: one DRAFT PR whose body names itself GOVERNANCE (PRD-186) and
lists every ruling applied; dispatch one fresh-context review of the PR
diff (not of this charge's prose); at most one correction cycle; end with
"Held for your merge." After Dustin merges, comment on PR #184 citing the
importing commit and close it as superseded — close, never merge.

STOP CONDITIONS: J0 artifact missing or NOT VALIDATED; validator red after
correction; any needed edit outside the files enumerated above; any
instruction here conflicting with a canonical doc — report the conflict,
do not choose.
```

### J2 — NS-2E Market Control Card MATERIAL packet author

```
You are the MATERIAL-packet author for NS-2E (Market Control Card) in
dwats250/cuttingboard. Planning only: no production code, no PRD number, no
lifecycle changes. GOV-2 §2 governs — you produce the provisional packet
(steps 1–2); the Codex packet review and exact-head confirmation are the two
auto-commissioned events that follow; Dustin's design-direction ruling comes
after review-clean.

PREFLIGHT: branch from origin/main; report SHAs; clean tree. Read: VISION.md;
CLAUDE.md; docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md;
docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md (NS-2);
docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md (NS-2E, line ~104,
~318); the worked example
audits/ns2a-ns2c-spy-observation-material-packet-2026-08/NS2A-NS2C_SPY_OBSERVATION_MATERIAL_PACKET_v0.1.md;
cuttingboard/market_map.py; cuttingboard/delivery/dashboard_renderer.py
(market-map/system-state sections); cuttingboard/delivery/payload.py;
docs/SCHEMA_MAP.md and docs/CALL_SITE_MAP.md before any grep.

PACKET CONTENT (audits/ns2e-market-control-card-packet-2026-08/, one file,
modeled on the worked example):
- Reviewed-state header pinned to the exact main SHA you read.
- The card's seven answers (state, location, event, transition,
  invalidation, permission, candidate implication): for each, the existing
  upstream producer field that supplies it — the card is a projection of
  existing truth, not a new computation; any answer with no existing
  producer is declared DEFERRED, not invented.
- Dead-branch enumeration of the Market Map surface being
  replaced/refactored: every reader of the retired/changed sections
  (renderer sections, tests, docs), each removed-in-slice or
  retained-with-reason.
- Carrier/seam proposal (follow the PRD-288 transient-carrier vs
  payload-section decision pattern), provisional FILES set and net-LOC
  ceiling (GOV-2 §5 labels), regression matrix sketch, mutation-red design
  sketch.
- Explicit non-goals: no new data sources, no prediction, no
  decision-bearing renderer derivation, no NS-2F ranked ladder.
- The Dustin questions the design-direction ruling must answer, each with
  two or three concrete options.
LANDING: commit the packet to its own branch, push, no PR unless instructed
at dispatch. End with "Held for your decision."
STOP: if the design cannot avoid touching decision logic
(runtime/qualification/regime), stop and report rather than expanding.
```

### J3 — GEX-0 provider evidence pass (commissioned, ruling 5)

```
You are the GEX-0 evidence agent for dwats250/cuttingboard — a
network-enabled, research-only charge commissioned by Dustin (2026-08-05).
ZERO repository code changes. Your only repo write is the evidence artifact
itself, committed to its own branch (recon-artifact clause).

AUTHORITY: docs/plans/decision-support-expansion-doctrine-v0.1.md §4
(read it in full first) as amended by Dustin's 2026-08-05 ruling: the
verdict set is PROVIDER VIABLE / PROVIDER NOT VIABLE / EVIDENCE INCOMPLETE.
A verdict speaks ONLY to the one provider examined in this bounded pass —
never conclude that no viable provider exists. Also read
docs/plans/decision-support-workplan-v0.1.md §8 (Wave 5, GEX-0) and
audits/stage0-recon-2026-07-20/stage0-04-gex-v0.1.md (the prior
NOT-ATTEMPTED disposition).

SCOPE: exactly ONE provider. Select the single most promising economically
acceptable candidate from current public documentation and state the
selection reasoning in the artifact (free tier or trial strongly preferred;
you may not purchase anything — if establishing a load-bearing meaning
requires payment, that is EVIDENCE INCOMPLETE with the cost named). No
provider abstraction, comparison program, consensus, or fallback chain. No
schema design, no PRD, no code.

EVIDENCE — the pass must directly establish all 13 points from doctrine
§4.3, each with a citation to current provider documentation or a real
captured response (marketing copy and memory do not count):
1 access terms and cost; 2 rate limits; 3 symbol coverage (SPY at minimum;
primary universe noted); 4 provider and model label; 5 field definitions;
6 expiration scope; 7 update cadence; 8 source timestamps; 9 spot-price
basis; 10 exact meaning of any gamma-flip / put-wall / call-wall level;
11 a sample response (captured verbatim, secrets redacted); 12 staleness
behavior; 13 unavailable/failure behavior.

ARTIFACT: audits/gex0-provider-evidence-2026-08/GEX_0_PROVIDER_EVIDENCE_<provider>_<date>.md
containing: charge header + this verdict-set amendment reference; provider
selection reasoning; the 13 points each with evidence and a disposition
(ESTABLISHED / UNKNOWABLE-WITHOUT-<what>); the captured sample; exactly one
verdict: PROVIDER VIABLE (all 13 established and economics acceptable),
PROVIDER NOT VIABLE (a load-bearing meaning is established to be absent or
unacceptable for THIS provider), or EVIDENCE INCOMPLETE (enumerate the
specific unknowns and what would resolve each). Commit only this artifact
to its own branch, push, no PR. End with the verdict line and "Held for
your decision."

STOP: any temptation to examine a second provider, write schema/code, or
infer an unverified meaning → stop at EVIDENCE INCOMPLETE instead.
```

### J4 — CONTEXT-REGISTRY packet author (combined NS-4A + NEWS-0)

```
You are the context-registry packet author for dwats250/cuttingboard.
Planning only: no production code, no network collection, no PRD number, no
lifecycle changes. Ruling 6 (2026-08-05) governs: the agent DRAFTS from
existing repository seeds; Dustin RATIFIES. You may not invent symbols,
themes, or sources as settled content — every element beyond the seeds is
flagged `[BEYOND-SEED — RATIFY]`.

PREFLIGHT: branch from origin/main; report SHAs; clean tree. Read:
docs/plans/decision-support-expansion-doctrine-v0.1.md (§5 news, G1–G10);
docs/plans/decision-support-workplan-v0.1.md (§7 Wave 4, NEWS-0 required
registry categories); docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md
(NS-4, NS-6 incl. the suggested groups line and relationship path);
audits/north-star-deep-audit-2026-08/domains/G_EXPANSION_VOCABULARY_RECONCILIATION.md
(G-002, G-006); seeds: config.TREND_STRUCTURE_SYMBOLS and
market_map.PRIMARY_SYMBOLS (read the actual code);
docs/plans/agent-work-charge-template-v0.1.md (your envelope).

PACKET (audits/context-registry-packet-2026-08/, one file):
1. Registry schema: symbols, aliases, themes, roles, horizons, benchmarks,
   approved sources, enabled/disabled + human-editable reason — versioned,
   one writer, human-authored data file; loader/validation design follows
   cuttingboard/red_folder.py (curated JSON, provenance fields, expiry/
   staleness signal, fail-loud validation).
2. Draft content: seed symbols verbatim; the Ledger's suggested groups as
   draft themes; every addition flagged [BEYOND-SEED — RATIFY].
3. Proposed news artifact schema (NEWS-0 exit): doctrine §5.2 fields —
   title, source, publication time, URL, matched symbols/themes,
   source-grounded excerpt — plus retrieved_at, schema_version, dedup
   identity (macro_awareness_state precedent); item cap 5; example valid /
   empty / stale artifacts.
4. Shared external-context provenance/freshness vocabulary (the substrate
   contract other packets reference; convention only, no shared code).
5. Two doctrine-anchor questions for Dustin, each with 2–3 concrete
   options + consequences: (a) G-002 — ratify the NS-4 heatmap/registry
   vocabulary as doctrine-anchored, or amend the doctrine first; (b) G-006 —
   ratify GLOBAL STATE → THEME HEALTH → LEADERS → WATCHLIST → SETUPS as
   presentation ordering only (never causal/decision pipeline), or defer
   the path entirely.
6. Materiality statement (GOV-2 §1 match: new persisted schema, multiple
   readers) and the required §2 sequence ahead.
LANDING: commit the packet to its own branch, push, no PR unless instructed.
End with "Held for your decision" (ratification).
STOP: any pressure to finalize content without ratification, add a network
producer, or widen into consumer design → stop and report.
```

### J5 — NS-4B heatmap Stage-0 prep (optional; dispatch only after the registry lands)

```
You are the NS-4B movement-heatmap design-prep agent for
dwats250/cuttingboard. Planning only: no production code, no PRD number
allocation, no lifecycle changes. Precondition (verify, else STOP): the
ratified context registry artifact is merged on main.

PREFLIGHT: branch from origin/main; report SHAs; clean tree. Read:
docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md (NS-4B, "Observe
wide. Trade narrow."); the ratified registry file and its packet; the G-002
ruling recorded in docs/DECISIONS.md; cuttingboard/watchlist_sidecar.py,
cuttingboard/trend_structure.py, cuttingboard/ingestion.py (existing quote
surfaces); cuttingboard/delivery/dashboard_renderer.py (card recipe:
PRD-288's #spy-observation block); docs/prd_history/PRD-288.md (FILES/
mutation-plan shape).

DELIVERABLE: a Stage-0-ready design note (own branch, audits/ or the
location instructed at dispatch) covering: data source = EXISTING ingestion/
quote surfaces only (no new fetch paths); grouping = registry themes/roles;
freshness visibly rendered per-cell (reuse the freshness tokenizer family,
no new vocabulary); consumer-only rendering (CONSUMER class; renderer is a
HIGH-RISK file → the eventual PRD rides LANE HIGH-RISK); absent registry or
stale quotes ⇒ honest degradation, never fabrication; proposed FILES set +
LOC ceiling; present/absent + staleness test plan with mutation-red
sketches. Explicit non-goals: no leadership mode (NS-4C), no participation
mode (NS-4D), no external watchlist mirror (NS-4E), no decision effect.
End with "Held for your decision."
```

---

## Landing record

This packet is the read-only planning deliverable, committed alone to
`claude/cuttingboard-compression-runway-rcff3m` per the recon-artifact
clause. No PR is opened; no lifecycle state changes; the branch is held for
Dustin.
