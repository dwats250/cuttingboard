# GEX-1 / GEX-2 Planning Reconnaissance — 2026-08-20

```
STATUS: PLANNING RECON — NON-BINDING
AUTHORIZES NO IMPLEMENTATION, NO PRD, NO PROVIDER ADOPTION
DELIVERABLE OF: session "GEX-1/GEX-2 planning and reconnaissance" (2026-08-20)
```

> This artifact is read-only reconnaissance and sequencing input for the GEX
> lane. It builds nothing, allocates no PRD number (doctrine G9), lifts no
> gate, and decides nothing that is Dustin's to decide. Every GEX-1/GEX-2
> promotion step remains gated exactly as the doctrine, workplan, GOV-2, and
> the owner holds specify.

**Charge provenance (honesty note).** The commissioning session's original
prompt text was lost to a container restart before any work landed; the charge
here is reconstructed from the session title ("GEX-1/GEX-2 planning and
reconnaissance"), the session's configured outcome branch
(`claude/gex-planning-reconnaissance-upntlo`), and the standing lane order
(operating rule 2026-08-06: NS-2E → GEX → context registry; NS-2E is COMPLETE
via PRD-289). Per the CLAUDE.md recon-artifact clause, silence defaults to
committable-to-branch; the configured outcome branch corroborates that
intent. If the lost charge carried narrower bounds, this artifact overclaims
nothing — it is recon prose only — but Dustin should say so and it will be
revised or retired.

**Base commit:** `e3f0b597cf2312513252dea9dafd27e87e412b11` (== `origin/main`
at session start; verified clean checkout).
**Branch:** `claude/gex-planning-reconnaissance-upntlo` (this artifact is the
only payload).
**Merge permission:** NONE — held for Dustin's GOV-1 merge like every PR.

---

## §1 — Current lane state (verified 2026-08-20)

| Item | State | Where verified |
|---|---|---|
| GEX-0 (Cboe) | `PROVIDER VIABLE` (scoped: personal / non-redistributed / context-only, ~15-min delayed; SPY + SPX/SPXW only) | Packet `audits/gex-0-cboe-evidence-2026-08/GEX_0_CBOE_PROVIDER_EVIDENCE_PACKET_2026-08-17.md` on branch `worktree-claude+gex0-cboe-pass-0817`, head `b55b0de` |
| GEX-0 PR | **PR #256 OPEN, ready (not draft), reviewed ACCEPT-WITH-NITS (no required edits) — Held for your merge** | GitHub, 2026-08-20 |
| GEX-0 on `main` | Still `EVIDENCE INCOMPLETE` — the `PROVIDER VIABLE` workplan row flip rides PR #256 and is NOT yet merged | `docs/plans/decision-support-workplan-v0.1.md:50` at `e3f0b59` |
| GEX-0 (Polygon) | `EVIDENCE INCOMPLETE` for Polygon, unchanged (free tier gates the options snapshot; 2026-08-06 pass) | `audits/gex-0-polygon-provider-evidence-2026-08/` |
| GEX-1 | `EVIDENCE BLOCKED` — future SIDECAR PRD, "honest artifact" | workplan row 51 |
| GEX-2 | `EVIDENCE BLOCKED` — future CONSUMER PRD, "baseline-neutral display" | workplan row 52 |
| GEX-3 | Not planned; cadence is not presumed (doctrine §4.4) | doctrine |
| GEX code on `main` | **None.** `grep -rniE "gex|gamma" cuttingboard/` exits 1 at `e3f0b59` (re-run by this session, not delegated) | this pass |
| Lane order | NS-2E (done, PRD-289 COMPLETE @ #231) → **GEX** → context registry | operating rule 2026-08-06 |
| Owner holds in force | "GEX go/stop after evidence"; every merge | operating rule; GOV-1 |

**Post-#256-merge staleness sweep (flagged, not fixed here — scope lock).**
When PR #256 merges, three surfaces on `main` go stale and belong to the
post-merge drift sweep (PRD-186 posture), none of which PR #256 or this recon
may touch:

1. `docs/PROJECT_STATE.md` (~lines 24, 209): still narrates GEX-0 as
   `EVIDENCE INCOMPLETE` / needs-Polygon-credential (already flagged as
   deferred nit #2 in the #256 review artifact).
2. `docs/plans/decision-support-expansion-doctrine-v0.1.md` §3.1: its
   "Current status (updated 2026-08-09)" block and
   `State: EVIDENCE INCOMPLETE` line predate the Cboe pass; §3.1's closing
   sentence ("No GEX implementation PRD may be drafted until the bounded
   provider evidence gate in section 4 passes") becomes satisfied-in-fact.
3. The `EVIDENCE BLOCKED` states on GEX-1/GEX-2 workplan rows become
   ripe for `PROPOSED` / `HELD FOR DUSTIN DECISION` re-statement (doctrine §7
   vocabulary) once the go/stop ruling exists — a one-row edit each, owned by
   whoever lands the ruling's decision entry.

---

## §2 — Gate sequence to a running GEX-1 (critical path)

Nothing below is novel; this is the existing rule set laid end-to-end so the
lane's real length is visible. Steps marked **[DUSTIN]** are owner acts.

1. **[DUSTIN] Merge PR #256** (Held for your merge). Until then the
   `PROVIDER VIABLE` verdict is not repository truth and no downstream step
   may cite it.
2. **[DUSTIN] "GEX go/stop after evidence" ruling** (Held for your decision;
   operating rule owner-hold + doctrine §4.4 "Only after a pass and Dustin's
   explicit go"). A dated `docs/DECISIONS.md` entry is the natural carrier.
   §5 below lists the scope decisions worth folding into the same ruling so
   the lane doesn't stall on them later.
3. **GOV-2 §1 intake classification of the GEX-1 slice.** This recon's
   recommendation (argued in §3): **MATERIAL** — which chains steps 4–7.
   Classification is decided at intake by whoever opens the work, and
   Dustin may classify or decline-to-classify regardless.
4. **Upstream MATERIAL packet** (design/seam-trace: artifact schema,
   producer placement, staleness/unavailable semantics, FILES cone) —
   authored under a charge-template envelope
   (`docs/plans/agent-work-charge-template-v0.1.md`, mandatory for packets
   governed by the expansion plans).
5. **Codex packet review → one consolidated correction → Codex SHA-pinned
   exact-corrected-head confirmation** (the two GOV-2 auto-commissioned
   Codex events; no others are authorized by MATERIAL classification).
6. **[DUSTIN] Design-direction ruling** from the review-clean packet.
7. **Stage-0 PRD** (scaffold + IN PROGRESS registry row + `prd_index.json`
   entry, via `scripts/prd_open.sh`), drafted from the ruling.
   Expected header: `CLASS: SIDECAR` (T1), `LANE: STANDARD` — MATERIAL bars
   MICRO (GOV-2 §1); no HIGH-RISK FILES entry is needed as payload
   (`any new cuttingboard/<name>_sidecar.py` is the SIDECAR class's allowed
   column in the PRD_PROCESS CLASS matrix, and CLASS is neither EXECUTION
   nor CONTRACT, so R11 does not force HIGH-RISK).
8. **Fresh-context independent PRD review** (capability role; not the
   author or same-session implementer; committed verdict pinned to the
   reviewed revision).
9. **[DUSTIN] Gate A** — explicit implementation authorization.
10. **Implementation** within the locked FILES set, with the PRD-198
    invariants (§4 below) and pre-implementation grep sweep (PRD-158)
    honored; fresh-context implementation review (GOV-1 routine gate);
    at most one correction cycle.
11. **[DUSTIN] Merge** of the implementation PR (Same-PR closeout rides it,
    via the `prd-closeout-verified` skill only).

**GEX-2 sequence (after GEX-1 exists):** [DUSTIN] inspects real GEX-1
artifacts and rules them useful (doctrine §4.4; a `HELD FOR DUSTIN DECISION`
state until then) → its own GOV-2 intake test → separate CONSUMER PRD
(`CLASS: CONSUMER`, T2; `LANE: STANDARD` expected — dashboard renderer and
`ui/` files are the CONSUMER class's allowed column) → same review/Gate A/
merge ceremony. GEX-1 and GEX-2 are separate work units by doctrine G3 and
may not be bundled into one PRD.

**Anti-stall note.** The only two steps that can start before Dustin acts
are none. Step 3's classification and step 4's packet CAN be drafted
immediately after the go ruling in the same session that receives it; the
workplan's parallelism table already blesses "charge preparation without
conducting the pass" as safe concurrent work, and preparing the GEX-1 packet
charge text ahead of the go ruling is the analogous safe prep this recon
partially performs (§4).

---

## §3 — GOV-2 materiality recommendation for GEX-1 (argued, not decided)

**Recommendation: classify the GEX-1 slice MATERIAL at intake.**

- **Layer crossing (decisive leg).** GOV-2 §1: MATERIAL when the work
  "crosses two or more of runtime, contract, audit, reporting, notification,
  delivery, dashboard, or persistence." A GEX-1 producer performs a live
  network fetch + in-repo computation (runtime) and writes a versioned,
  durable, schema-bearing sidecar artifact (persistence). Two layers.
- **New persisted schema surface (weaker leg, stated honestly).** GOV-2 §1
  also matches a new "persisted schema surface that has more than one reader
  or presentation path." At GEX-1 time the artifact has, by construction,
  zero programmatic readers (no consumer, no imports) — so this leg arguably
  does NOT fire yet. But the schema is being designed precisely so GEX-2 can
  read it later; choosing it IS choosing the seam GEX-2 inherits.
- **Precedent.** NS-2E Market Control Card — the nearest prior work of this
  shape (new observational surface + later display card) — ran the full
  MATERIAL packet workflow before PRD-289.
- **Counter-reading, for completeness.** One could read GEX-1 as a "narrow
  single-surface patch" (one new module + one artifact). This recon does not
  find that persuasive against the layer-crossing leg, and the cost asymmetry
  favors MATERIAL: a wrongly-skipped packet forces a mid-implementation stop
  under GOV-2's reclassification rule; a wrongly-run packet costs one bounded
  review cycle.

Consequences if MATERIAL: MICRO ineligible (already irrelevant — GEX-1 is not
MICRO-shaped); STANDARD minimum lane; exactly two auto-commissioned Codex
events; the fresh-context PRD reviewer role is commissioned per the MATERIAL
workflow (Codex in that seat would need a separate PRD-242 commission).

**GEX-2** gets its own intake test when its time comes; a display-only card
that touches the dashboard renderer + reads a persisted artifact will very
likely also cross two layers (dashboard + persistence). Plan for MATERIAL
there too rather than being surprised.

---

## §4 — GEX-1 design constraints already fixed by evidence + doctrine

These are not proposals; they are the constraints the packet author inherits.
Source: Cboe packet §§6–13, doctrine §4, VISION principles, PRD-198.

1. **Provider and endpoint (single).** Cboe delayed_quotes public JSON,
   one GET per underlying: `cdn.cboe.com/api/global/delayed_quotes/options/
   {SYMBOL}.json` (`_SPX` for the cash index). Keyless; no credential
   anywhere. No second provider, abstraction, comparison, or fallback chain
   (doctrine §4.2) — a Cboe outage means an honest `unavailable` state, not
   a fallback.
2. **Underlying scope is a Dustin decision (§5 Q3), bounded by evidence.**
   The verdict covers SPY and SPX/SPXW only. SPX is the correct gamma
   underlying (both AM-settled SPX and PM-settled SPXW roots arrive in one
   `_SPX` response); SPY is the repo's flagship symbol (config INDICES,
   spy_observation/spy_state, market control card). "Primary universe only"
   (doctrine §4.4) needs an explicit reading here — one underlying is the
   cuts-before-additions default.
3. **Computation is in-repo and must be labeled derived-of-model.** The feed
   ships per-strike `open_interest` + Cboe-model `gamma` (+ delta/theta/
   vega/rho, `iv`, `theo`, quotes, spot) and NO vendor flip/put-wall/
   call-wall levels. GEX = Σ over strikes of gamma · OI · multiplier ·
   dealer-sign-convention · spot factor. The dealer-sign convention is an
   assumption, not data — the artifact must label it, and label the whole
   figure model-derived-of-model (G1: description, not prediction).
4. **Timestamps are mixed-zone; localize explicitly.** Top-level `timestamp`
   is UTC; per-contract `last_trade_time` is naive US/Eastern; HTTP
   `Last-Modified` is edge-regeneration cadence, distinct from the ~15-min
   market-data delay. The artifact must carry an explicit fetched-at (UTC),
   the feed's own timestamp, and a delay label — never present delayed data
   as real-time.
5. **Staleness is per-signal, not per-response.** Untraded contracts carry
   stale `last_trade_time` (observed: 6 days) alongside populated model
   fields, and deep-ITM rows show degenerate `gamma`/`iv` = 0.0. Coverage
   accounting (contracts included/excluded and why) is a first-class
   artifact field, not a footnote (G6: honest absence).
6. **Unavailable = fail-loud, baseline-neutral.** Unknown symbol → HTTP 403
   with S3-style XML, not 200 JSON. Producer keys `unavailable` off
   non-200 / non-JSON / missing load-bearing fields and exits non-zero or
   writes an explicit unavailable-state artifact — never
   substitute-and-continue (PRD-198 invariant 1). Every such guard ships a
   mutation-verified red test (invariant 4).
7. **Manual / lazy / cached; no cadence.** No cron, no scheduler hook, no
   notification, no pipeline import, no consumer (G3, G4). Invocation is a
   human act. Cache honestly: the artifact records when it was fetched, and
   a re-render without re-fetch shows the old fetched-at, not a fresh one.
8. **Versioned additive artifact.** Schema carries an explicit version
   field from v1; changes are additive (G5). Source, model label, fetched-at,
   delay, coverage, and the sign-convention assumption are embedded in the
   artifact itself (workplan GEX-1 row), so the artifact is honest standing
   alone with no code context.
9. **Non-redistribution posture.** Personal / non-redistributed /
   context-only (owner-ruled terms leg). The artifact stores derived
   per-strike/aggregate GEX figures and provenance — never the bulk raw
   chain. Posture shift toward any display-to-others requires a fresh Cboe
   terms review and re-commission (packet §12 stop condition carries
   forward).
10. **Producer placement respects the banned-import guards.** Pure modules
    are guarded against `requests`/`urllib`/`polygon`/`yfinance`
    (`tests/test_scenario_engine.py`, `tests/test_levels.py`); the producer
    lives outside them (see §6 seam notes for where network I/O
    conventionally sits in this repo).
11. **Rate posture.** No rate-limit ceiling was established at high volume —
    and none is needed: manual/cached/low-volume by design. The producer
    must not add retry storms; one fetch, fail loud.
12. **Endpoint fragility is a named risk.** An undocumented public CDN path
    can change or vanish without notice (packet §8). The producer's
    unavailable path IS the mitigation; no defensive multi-endpoint logic.

---

## §5 — Decisions this lane needs from Dustin (consolidated)

Phrased per the blocker-phrasing rule. Q1 is a merge; Q2–Q5 are rulings that
can all ride one DECISIONS.md entry with the go ruling.

1. **Held for your merge:** PR #256 (GEX-0 Cboe evidence, reviewed, no
   required edits). Everything else waits on this.
2. **Held for your decision:** the "GEX go/stop after evidence" ruling
   itself — go, stop, or park-with-conditions.
3. **Held for your decision (fold into Q2):** GEX-1 underlying scope —
   `_SPX` only (correct gamma underlying, both roots), `SPY` only (flagship
   symbol consistency), or both. Recon default per cuts-before-additions:
   **one underlying, `_SPX`**, with SPY deferred until usefulness is shown.
4. **Held for your decision (fold into Q2):** concurrence with the MATERIAL
   classification recommendation (§3), or an owner classification either way
   — GOV-2 gives Dustin that authority explicitly.
5. **Held for your decision (fold into Q2):** whether the GEX-1 MATERIAL
   packet charge is commissioned immediately on go (the anti-stall default)
   or held for a later session.
6. **Housekeeping observation (no action urged):** NS-2E MATERIAL packet PRs
   #222 and #225 (v0.1, v0.2) remain open alongside the v0.3 packet PR #226
   while PRD-289 already landed via #231. If the v0.1/v0.2 packets are
   superseded history, closing them is a one-click tidy — flagged only
   because this recon touched the PR list; entirely Dustin's call.

---

## §6 — Repo seams a GEX-1 producer / GEX-2 consumer would touch

Surveyed via a delegated read-only sweep of `main` at `e3f0b59`; the decisive
zero-consumer / isolation / requirement greps were re-run first-hand by this
session (§9). This section informs the future MATERIAL packet and PRD FILES
sets; it declares none.

### 6.1 GEX-1 is an observation sidecar under `docs/sidecar_doctrine.md`

- The PRD must declare the **observation** category in its header (human
  reader is the valid consumer — exactly GEX-1's shape).
- Observe-only: own artifact at a non-overlapping path; never mutates
  pipeline artifacts, injects contract/payload fields, or triggers
  notifications. One producer per path.
- **Adding a sidecar means adding a row to `docs/artifact_flow_map.md` in
  the same PRD** (`docs/sidecar_doctrine.md:78`) — a mandatory FILES entry
  the packet must not forget.
- Contract isolation: the sidecar schema never extends the contract; a
  future consumer (GEX-2) reads the artifact **directly from its canonical
  path** in the renderer — never via a payload section.

### 6.2 Producer placement: two live conventions, one recommendation

| Convention | Precedent | Shape |
|---|---|---|
| `cuttingboard/<name>_sidecar.py` | `cuttingboard/watchlist_sidecar.py` — pure builder (purity enforced by source-fence tests: no I/O imports, no wall-clock), with `runtime/__init__.py` doing the write | Assumes a pipeline write hook — which GEX-1 is FORBIDDEN to have (no pipeline import) |
| Standalone `tools/` CLI | `tools/macro_awareness_collector.py` — argparse CLI, imports no `cuttingboard` module (re-verified: zero `from/import cuttingboard` lines), `validate_snapshot()` self-check, explicit fail-closed state, atomic tmp-then-replace write, `workflow_dispatch`-only workflow (`.github/workflows/macro_awareness.yml`) | The only existing **manual/lazy** producer; isolation is mechanically provable |

**Recon recommendation: the `tools/` CLI shape** — it is the only precedent
matching GEX-1's manual/no-pipeline-import contract, and its isolation
(no `cuttingboard` imports either direction) makes the no-decision-imports
guarantee a grep, not an argument. Note the PRD_PROCESS CLASS matrix's
SIDECAR row names `any new cuttingboard/<name>_sidecar.py` as the allowed
column; a `tools/`-resident producer should be declared explicitly in the
PRD so CLASS mapping is unambiguous. Packet decision, flagged here.

Network I/O placement: the banned-import guards
(`tests/test_scenario_engine.py`, `tests/test_levels.py`) fence pure
modules; `tools/` is outside the fence, consistent with the macro collector.

### 6.3 Artifact path and publication mechanics

- Path convention: `logs/gex_*.json`. **Everything under `logs/` is
  gitignored** (plus a blanket `*.json`); committed generated artifacts
  exist only via explicit per-workflow `git add -f` allowlists (PRD-194
  per-file ownership; `.github/workflows/macro_awareness.yml:73` is the
  exact pattern a manual GEX workflow would copy, and
  `tests/test_ci_artifact_hygiene.py` pins those allowlists).
- **Open design item for the packet:** where the human reads the artifact.
  A locally-run producer leaves a gitignored file in the working tree
  (fine for personal inspection; simplest); a `workflow_dispatch` producer
  must force-add/commit its artifact to be visible at all. Cuts-before-
  additions favors local-first, workflow later if ever.
- Inherited drift warning (do not copy it): `scripts/
  clean_generated_artifacts.sh`'s `GENERATED` array is already missing half
  the files the pipeline dirties (PROJECT_STATE known debt, unfiled MICRO).
  Whether a GEX artifact joins that array is a deliberate decision for the
  packet, not an accident.

### 6.4 GEX-1 test template

`tests/test_watchlist_sidecar.py` is the closest model: top-level schema
keys, exact per-record key count, byte-identical determinism, naive-datetime
rejection, plus source-scanning purity fences. A GEX equivalent adds: the
unavailable-state artifact shape, the coverage-accounting fields, the
non-200/non-JSON fail-loud path, and the sign-convention label presence —
each guard with a mutation-verified red test (PRD-198 invariant 4).
`tests/test_trend_structure.py` holds the unavailable-token vocabulary
precedent (PRD-130) worth reusing rather than inventing new literals.

### 6.5 GEX-2 consumption seam (for its later PRD; recorded now while fresh)

- **Read path:** direct sidecar-artifact read in
  `cuttingboard/delivery/dashboard_renderer.py` (the trend-structure
  pattern): a module-level `_GEX_PATH` constant beside the existing path
  constants (~line 60), a never-raising loader (returns `None` on
  missing/malformed — the `_load_trend_structure_snapshot` pattern,
  ~line 953), a source-health classifier (the nine-state
  `_trend_structure_source_health` machine, ~line 1031, is the repo's most
  mature honest-absence implementation), projection-only display helpers,
  and one more kwarg threaded through `render_dashboard_html` (already ~20
  params; `docs/renderer_decomposition_map.md` records that strain —
  design-only, no refactor license).
- **NOT the payload path:** PRD-289's market-control card rides
  `payload["sections"]` because it is a transient in-run object. Routing a
  sidecar through the contract/payload is exactly what the sidecar
  doctrine's contract-isolation rule forbids for GEX-2.
- **Baseline-identical mechanics:** the MCC block's all-or-nothing
  suppression is the right model — absent input emits no block at all,
  asserted by `tests/test_dashboard_renderer.py:4178`
  (`test_m23_no_market_control_card_when_section_absent`, re-verified).
  That is literally the "missing/stale/invalid yields baseline-identical
  output" acceptance test shape.
- **Publish gate isolation:** `validate_coherent_publish`
  (`dashboard_renderer.py:~563`) must never gain a GEX input — a
  display-only consumer can never block a publish.
- **Fixture corpus:** `tests/preview_fixtures.py` `SECTION_STATE_CASES`
  feeds both tests and the sanctioned `dashboard_preview.yml` path; a GEX
  card adds coherent + missing/stale cases there or the preview corpus
  silently under-covers it.
- **PRD-289's FILES section** (`docs/prd_history/PRD-289.md`) is a directly
  reusable FILES template for a card PRD, including its explicit
  read-only-imports exclusion list.

### 6.6 Overlap inventory (informational only — reuse forbidden)

- `cuttingboard/options.py`: representation/sizing over relative strike
  labels; never fetches a chain, holds no greeks. No overlap.
- `cuttingboard/chain_validation.py`: the repo's only live chain fetcher
  (yfinance primary + yahooquery fallback; reads OI, never gamma/IV).
  Overlaps GEX-1's data-acquisition needs on paper — **and must not be
  imported or extended**: it is a two-provider fallback chain, the exact
  §4.2 anti-pattern, built on providers the GEX-0 evidence does not cover.
  Precedent for structure, not a dependency.
- Recon-cache maps: `docs/SCHEMA_MAP.md` has no sidecar-artifact section
  (sidecar schemas conventionally live in the producer module +
  `docs/artifact_flow_map.md`); `docs/CALL_SITE_MAP.md` is
  file+function-granularity by design. Both current but thin; each gets a
  row from the eventual PRDs, not from this recon.
- Universe declaration precedent: `cuttingboard/config.py`
  `TREND_STRUCTURE_SYMBOLS` (curated tuple, strict subset) is the
  established way a sidecar declares a bounded universe — GEX-1's
  equivalent is a single-underlying constant per the §5 Q3 ruling.

---

## §7 — Out of scope for this recon (explicit)

- No GEX-3 / cadence planning: doctrine says cadence is not presumed, so it
  is not pre-planned either.
- No second-provider contingency planning (doctrine §4.2 forbids the
  comparison program this would become).
- No draft artifact schema: the schema is the MATERIAL packet's job, after
  the go ruling, under its own charge — drafting it here would be placeholder
  authority (G9).
- No PRD numbers reserved, no FILES ceilings set, no LOC ceilings proposed.

## §8 — Stop conditions honored this pass

- Read-only everywhere except this artifact's own directory: no source,
  contract, workplan, doctrine, or lifecycle file touched.
- No PR opened; branch push only; merge stays with Dustin (GOV-1).
- No Codex invocation (none commissioned; GEX-1 is not yet at its GOV-2
  events).

## §9 — Provenance

- Session: "GEX-1/GEX-2 planning and reconnaissance", 2026-08-20, outcome
  branch `claude/gex-planning-reconnaissance-upntlo`.
- Base: `e3f0b597cf2312513252dea9dafd27e87e412b11` == `origin/main` at pass
  start; `git status` clean.
- Evidence branch inspected: `worktree-claude+gex0-cboe-pass-0817` @
  `b55b0de34af3f2417f1632cc98c69a36db1d7400` (PR #256 head, verified against
  GitHub 2026-08-20).
- §6 surveyed via one delegated read-only Explore sweep of `main`; per the
  sub-agent re-verification discipline, the decisive greps were re-run
  first-hand by this session: `grep -rniE "gex|gamma" cuttingboard/` →
  exit 1 (no GEX code) at `e3f0b59`; `rg -l "watchlist_snapshot" --type py`
  → producer, runtime writer/constants, and its own test only (zero
  consumers); `rg "^from cuttingboard|^import cuttingboard"
  tools/macro_awareness_collector.py` → exit 1 (isolated);
  `docs/sidecar_doctrine.md:78` (artifact-flow-map row requirement) and
  `tests/test_dashboard_renderer.py:4178` (`test_m23_...section_absent`)
  confirmed at those locations.

```
PLANNING RECON — NON-BINDING — NO GEX-1 AUTHORITY CREATED OR IMPLIED.
```
