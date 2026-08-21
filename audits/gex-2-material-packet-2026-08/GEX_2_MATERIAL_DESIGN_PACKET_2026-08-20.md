# GEX-2 - Published-Board GEX Context Slice: MATERIAL design packet (REBUILD r2)

```
STATUS: PROVISIONAL MATERIAL PACKET - REBUILD r2 - 2026-08-20 - DESIGN ONLY
AUTHORIZES NO IMPLEMENTATION, NO PRD NUMBER (PRD-308 UNALLOCATED), NO GATE A,
  NO MERGE, NO CODEX COMMISSION BY THE AUTHOR.
DERIVED AT main SHA: e89eebb64997e8857827a9f294d228538b30bdce
PRIOR REVISION: packet head a7810d200de9af9575f05ae6de78e9f2c18e55cd (PR #261)
  received a completed independent Codex EVENT-1 verdict: DESIGN INCOMPLETE,
  NEW MATERIAL BOUNDARY FOUND, 9 required findings. This r2 is a GOV-2 sec6/sec7
  BOUNDARY RESET, not a local correction.
GOV-2 PACKET-REVIEW CYCLE: r2 awaits a NEW fresh independent Codex EVENT-1
  falsification of this exact rebuilt head. The packet is NOT review-clean and
  carries NO downstream authority until that review + its exact-corrected-head
  confirmation pass and Dustin issues a design-direction ruling.
OWNER RULING IN FORCE: "GEX-2 MATERIAL BOUNDARY REBUILD" (owner charge,
  2026-08-20). This is NOT the GOV-2 design-direction ruling.
```

> This is the upstream MATERIAL design packet GOV-2 requires before any GEX
> display PRD, decision entry establishing design direction, or implementation
> authority. r2 reconstitutes the boundary after EVENT-1 proved the reviewed
> design never reached the published dashboard in automated execution. Nothing
> here is buildable authority. Sequence position:
> **this rebuilt packet (now)** -> fresh Codex EVENT-1 falsification ->
> one consolidated correction -> Codex exact-corrected-head confirmation
> (GOV-2 sec7) -> Dustin design-direction ruling -> Stage-0 PRD drafting ->
> fresh-context PRD review -> Gate A.

---

## 0. Executive design decision

**What EVENT-1 broke.** The reviewed r1 packet assumed `logs/gex_snapshot.json`
would simply exist for the renderer to read. It does not: `logs/` is gitignored
(`.gitignore:49`), GEX-1 is manual/local, no workflow invokes the producer, and
no restore step reintroduces the artifact. In clean CI the renderer reaches the
published board with **no GEX artifact ever**. r1 therefore designed a card that
renders locally and is permanently invisible on Dustin's real board. That is the
`NO AUTOMATED ARTIFACT CARRIER` blocker (CB-GEX2-E1-001), and it drags in the
wrong-freshness-clock (E1-002) and producer-truth (E1-003) findings.

**The owner ruling.** GEX-2 is for the REAL published Cuttingboard, context-only
("GEX informs the board, never authorizes the trade"), fail-soft (if GEX is
unavailable the card disappears and the board is behaviorally unchanged),
smallest honest end-to-end carrier.

**The rebuilt slice, end to end.** A same-run producer invocation inside the
intraday publish workflow writes a fresh `logs/gex_snapshot.json`; a validated,
freshness-and-session-gated loader in `main()` resolves it to a display object
(or `None`); the renderer paints a compact, fully-removable GEX context card;
publication is unchanged when GEX is absent. Every load-bearing guard ships a
mutation-red test, including workflow-carrier behavior.

**The headline governance decision (D-0, see sec6).** Tracing the real carrier
proves the delivered product spans THREE canonical surfaces - CONSUMER (renderer
card), INFRA (workflow carrier), and a SIDECAR producer truth/cadence edit.
Binding doctrine (`decision-support-expansion-doctrine-v0.1.md` G3/G4/G8 and the
explicit GEX-2 -> GEX-3 gate) forbids compressing consumer construction and
cadence into one PRD, and PRD_PROCESS has NO mixed-class rule. So the honest,
falsification-surviving structure is **two tightly sequenced MATERIAL slices**:

- **GEX-2 (display consumer)** - renderer card + validated loader + the
  "machine consumers: none" truth corrections + consumer tests + docs. Mergeable
  independently; baseline-neutral; in production it renders a card only once the
  carrier exists, and is provably invisible-and-harmless until then.
- **GEX-3 (automated carrier / cadence)** - the workflow producer invocation
  (fail-soft, delete-before-fetch, staged, published) + the "no cadence, no
  workflow" truth corrections + carrier tests + docs. Gated behind demonstrated
  GEX-2 usefulness exactly as doctrine sec4.4 requires.

This split still delivers the owner's product goal - GEX on the real board - as
two sequenced merges, which is the doctrine's own intended path, NOT a local-only
demonstration. **RECOMMENDATION: adopt the split.** The single end-to-end slice
remains available only if Dustin issues an explicit written override of doctrine
G3/G4/G8 and the GEX-2/GEX-3 gate (sec6, Option 2). This packet designs the full
end-to-end product and lays every file into whichever structure Dustin picks;
the engineering is identical either way, only the PRD/Gate-A partition differs.

**No new material boundary beyond the owner charge was silently incorporated.**
The one governance conflict the recon surfaced (doctrine split vs single slice)
is escalated as D-0, per charge sec9 ("identify the conflict for Dustin rather
than papering over it"), not resolved by the author.

---

## 1. Exact repo / base / head / PR evidence

- Repository: `dwats250/cuttingboard`.
- `main` at rebuild time: `e89eebb64997e8857827a9f294d228538b30bdce`
  (local `HEAD` == `origin/main`; verified, no drift since the charge snapshot).
- MATERIAL packet PR: **#261** (OPEN, DRAFT), base `main`, head branch
  `worktree-gex-2-material-packet`, prior head
  `a7810d200de9af9575f05ae6de78e9f2c18e55cd` (the EVENT-1-reviewed revision).
- Packet file (revised in place, preserving the r1 revision in git history):
  `audits/gex-2-material-packet-2026-08/GEX_2_MATERIAL_DESIGN_PACKET_2026-08-20.md`.
- Working tree: only pre-existing generated artifacts dirty (`logs/*`,
  `ui/dashboard.html`); untouched by this packet and never committed.
- Unrelated NS-2E packet PRs #222/#225/#226 are NOT touched by this charge.

---

## 2. Prior EVENT-1 disposition and how r2 absorbs all nine findings

EVENT-1 verdict on `a7810d2`: **DESIGN INCOMPLETE**, NEW MATERIAL BOUNDARY: YES,
9 required findings. Each is absorbed below (full designs in the named sections):

| Finding | Absorbed by |
|---|---|
| E1-001 NO AUTOMATED CARRIER (blocker) | sec8 same-run carrier in the hourly publish job; assigned to the GEX-3 slice (sec6) |
| E1-002 WRONG FRESHNESS CLOCK (blocker) | sec9/sec10: freshness bound on `fetched_at_utc` (our own fetch instant) + session eligibility, NOT on `feed_timestamp_utc`; no arbitrary feed-age threshold |
| E1-003 PRODUCER TRUTH BECOMES FALSE (blocker) | sec22 doc cone: "machine consumers: none" -> GEX-2; "no cadence/no workflow" -> GEX-3; producer MATH/schema frozen (sec7) |
| E1-004 ARTIFACT SEMANTIC IDENTITY | sec11 identity contract; discriminator mutations in sec24 |
| E1-005 FIELD DOMAINS + TYPED UNAVAILABLE | sec12 domains, sec13 typed-unavailable unions/reasons |
| E1-006 RENDERER PURITY + EXCEPTION ISOLATION | sec16 GEX-branch purity (scoped narrowly; renderer HAS legacy I/O), new red isolation test |
| E1-007 TEST/MUTATION MATRIX | sec24 full matrix incl. golden-baseline byte-identity, readiness independence, carrier behavior |
| E1-008 CALL_SITE_MAP REQUIRED | sec22 doc cone includes `docs/CALL_SITE_MAP.md` (no longer discretionary) |
| E1-009 LOC ESTIMATE NOT CREDIBLE | sec23 honest per-category ranges per slice; old <=120 LOC ceiling discarded |

Findings are not relitigated. Where fresh repo evidence sharpens a premise
(E1-002: the untrustworthy clock is the self-reported feed `timestamp`, and the
TRUSTWORTHY recency clock `fetched_at_utc` already exists and r1 ignored it),
the sharpening is stated with citations, not used to dismiss the finding.

---

## 3. Owner rulings absorbed (charge 2026-08-20)

- **A. Published-board target.** The slice must place valid GEX context on the
  real published dashboard (sec8 carrier). A local-only card is rejected.
- **B. Context only.** GEX must not alter TRADE/NO TRADE/HALT, candidate
  qualification, readiness, execution eligibility, regime, notification
  ownership, payload/coherence requirements, or make ordinary publication fail
  when GEX is unavailable (sec19 proof; sec16 fail-soft).
- **C. D-1 APPROVED - presentation-only distance math.**
  `distance_pct = ((strike / spot) - 1) * 100`, display math only; never a
  threshold/state/regime/qualification/inference/support-resistance/magnet/
  predictive signal. The producer stays authoritative for which strikes are
  call wall / put wall / dominant (sec15).
- **D. D-2 REJECTED as written.** The `feed_timestamp_utc` 0..120-minute rule is
  rejected and 120 is NOT retained provisionally. `feed_timestamp_utc` is the
  feed's self-reported publish time, not a market-observation clock. r2 replaces
  it with a recency bound on `fetched_at_utc` + session eligibility (sec9/sec10).
- **E. Preferred architecture** - same-run ephemeral producer -> local artifact
  -> validated loader -> renderer -> publish; avoid a new long-lived persistence
  system. Adopted (sec8), subject to D-0.
- **F. Freshness promise** - never imply stronger freshness than can be
  evidenced; distinguish fetch recency from market-session eligibility from
  observation age (sec9). The card claims "fresh request, ~15m delayed" as a
  SOURCE DISCLOSURE, never an exact observation age.

---

## 4. Frozen GEX-1 producer contract (reverified at e89eebb; MATH untouched)

Source of truth: `tools/gex_snapshot.py` (428 lines), `_build_artifact`
(`:294-360`), serialized `json.dumps(..., indent=2, sort_keys=True,
allow_nan=False)`. Endpoint `https://cdn.cboe.com/api/global/delayed_quotes/
options/_SPX.json` (`:42`); SPX+SPXW roots; stdlib-only; isolated (imports
nothing from `cuttingboard/`, and no `cuttingboard` module imports it - PRD-306
R11, docstring `:8-13`). Core emitted keys (`_build_artifact` `:339-360`):

| Key | Type | Producer line | Card use |
|---|---|---|---|
| `schema_version` | str constant | `:340` | identity gate (sec11) |
| `source` | `"cboe_delayed_quotes"` | `:341` | identity gate |
| `underlying` | `"_SPX"` | `:343` | identity gate |
| `fetched_at_utc` | ISO-8601 UTC (aware) | `:345` | **recency clock (sec10)** |
| `feed_timestamp_utc` | ISO-8601 UTC | `:346` | display "as of" label ONLY |
| `data_delay` | descriptive constant str | `:347` | "~15m delayed" disclosure |
| `spot.value` / `spot.basis` | float>0 / str | `:348` | distance denominator; identity |
| `sign_convention` | str constant | `:350` | assumption-honesty token |
| `units` | str constant | `:351` | identity gate |
| `gex_total_1pct_usd` | float (signed) | `:353` | Net GEX (billions) |
| `call_wall{strike,gex_1pct_usd,reason}` | strike float or null | `:354` | Call row |
| `put_wall{...}` | strike float or null | `:355` | Put row |
| `dominant_net_gamma{...}` | strike float or null | `:356` | Dominant row (load-bearing) |
| `zero_dte.share` | float FRACTION 0..1 or null | `:279-287` | 0DTE row (share*100) |
| `zero_dte.observation_trading_date` | ET date str | `:283` | **session cross-check (sec10)** |

Load-bearing producer facts:

1. **`fetched_at_utc` is the producer's own fetch instant** - `_require_aware(now)`
   (`:345`), `now` defaulted to `datetime.now(timezone.utc)` at run entry
   (`:393`), fail-loud if naive (`:156-159`). This is the honest recency clock:
   in a same-run carrier it proves "we pulled this artifact this run."
2. **`feed_timestamp_utc` is the Cboe JSON body's self-reported top-level
   `timestamp`** (`_parse_feed_timestamp` `:144-153`, from `payload.get("timestamp")`
   `:179`), interpreted UTC by producer ASSUMPTION (comment `:61`), NOT an HTTP
   header (the fetcher reads no response headers, `_http_get` `:99-109`), NOT a
   Cboe-documented observation clock. It MUST NOT gate freshness (E1-002).
3. **`data_delay`** is a frozen descriptive constant (`:47`), never a measured
   lag - disclosure only.
4. **`zero_dte.observation_trading_date` is emitted UNCONDITIONALLY** (`:283` is
   in the returned dict even when `share` is null on `zero_abs_gex_denominator`,
   `:275-276`). So a session gate may read it without coupling the whole card to
   0DTE availability, and without a producer schema change.
5. **Each structural sub-object can be individually unavailable while the
   artifact is otherwise valid** (`_unavailable(reason)` -> `{"strike": null,
   "gex_1pct_usd": null, "reason": <str>}`; keys always present, values null).
6. **No committed sample**; `logs/` gitignored; tests use synthetic artifacts,
   injecting `now`/`fetch_fn`/`artifact_path` into `run()`.

**Frozen (do NOT reopen):** GEX math, wall/dominant selection, 0DTE definition,
SPX-only slice, formula, contract sign convention, provider choice, R11
isolation. If the design is found to require a producer MATH or SCHEMA change,
that is a boundary expansion -> STOP (sec27).

---

## 5. Complete current producer-to-published-board flow (traced cold at e89eebb)

```
tools/gex_snapshot.py   (SIDECAR producer, manual/local; invoked by NOTHING in CI)
        | one keyless GET -> Cboe _SPX
        v  atomic write (gitignored)
logs/gex_snapshot.json  (present ONLY on a machine that ran it by hand)
        X  no restore step names it; not cached; not staged unless present
        X  no cuttingboard module reads it (rg gex cuttingboard/ -> none)
        X  no workflow references gex (rg -i gex .github/ -> none)
```

The public board is rendered+published by two jobs (pages.yml deploys the
`publish` branch that GitHub Pages serves):

- **`cuttingboard.yml`** (morning pipeline): cron `5 13 * * 1-5` (~09:05 ET,
  pre-open) publishes; renders `python3 -m cuttingboard.delivery.dashboard_renderer
  --output ui/dashboard.html` (`:530`), then `cp ui/dashboard.html ui/index.html`
  (`:531`); stages with blanket `git add -f logs/` (`:528`); steps run
  `set -eo pipefail` (`:382`).
- **`hourly_alert.yml`** (intraday): ~7-8 RTH slots/weekday (`:11-18`), renders
  with explicit `--payload/--run/--market-map-path` (`:148-152`); stages an
  EXPLICIT file list (`:179-186`) that does NOT include `gex_snapshot.json`;
  `set -euo pipefail`.
- **`pages.yml`**: checks out `ref: publish` (`:31-33`), deploys `ui/` via
  `workflow_run` after either producer completes (`:10-16`).
- Publish helper `tools/ci_push_artifacts.sh` overlays the artifact-commit diff
  onto `publish` (`:54`), so a file reaches Pages only if the job stages it.

**Consequences that drive the carrier design:** network egress already exists in
both jobs (they fetch Polygon); the pipeline's blanket `git add -f logs/` would
auto-publish a present `gex_snapshot.json`, but the hourly's explicit list must
be amended; and a naive `set -e` producer call would abort the whole publish job
on a Cboe outage.

---

## 6. THE GOVERNANCE-STRUCTURE DECISION (D-0) + reclassification

### 6.1 The conflict (binding doctrine vs a single end-to-end slice)

- CLASS taxonomy is a closed six-set (`docs/PRD_PROCESS.md:412-421`): GOVERNANCE,
  SIDECAR, CONSUMER, EXECUTION, CONTRACT, INFRA. The renderer is a **CONSUMER**
  HIGH-RISK FILE (`:460`); `.github/workflows/**` is an **INFRA** HIGH-RISK FILE
  (`:463`); `tools/gex_snapshot.py` is the **SIDECAR** producer (named in no
  HIGH-RISK list).
- **No mixed-class rule exists** for one PRD spanning CONSUMER + INFRA + SIDECAR.
  The only "strictest wins" text is Cross-PRD Lane Mixing (`:560-567`), which
  governs SEPARATE PRDs sharing a PR, not one multi-surface PRD.
- Binding doctrine is explicit and verbatim:
  - **G3** - "A dashboard, notification, or scheduled cadence may not be bundled
    into the producer PRD."
  - **G4** - cadence "forbidden until ... a separately scoped consumer exists;
    and the consumer defines stale, missing, and invalid behavior."
  - **G8** - "Provider research, producer construction, consumer construction,
    cadence, and decision coupling are different questions. They may not be
    compressed into one PRD."
  - **sec4.4** - "GEX-2: display-only consumer ... GEX-3: optional cadence only
    after consumer usefulness is demonstrated ... Each gate requires a separate
    approval and separate PRD where implementation is involved."

The owner charge ("GEX-2 must reach the real published board") requires the
carrier, which the doctrine names GEX-3 and forbids compressing into the
consumer PRD. This is a genuine, cited conflict. Per charge sec9 it is escalated,
not resolved by the author.

### 6.2 The two options

**Option 1 - DOCTRINE-COMPLIANT SPLIT (RECOMMENDED).** Two sequenced MATERIAL
slices, each single-class, each its own PRD + fresh-context review + Gate A:

- **GEX-2 = CONSUMER (LANE HIGH-RISK).** Renderer card + validated loader +
  "machine consumers: none" truth corrections + consumer tests + docs. Falsifies
  only `artifact_flow_map:169` and the producer's "no machine consumer" clause.
  Mergeable now; baseline-neutral; renders a card in production only once GEX-3
  exists; provably invisible-and-harmless until then. Doctrine G4 preconditions
  are already met (GEX-1 realizable; Dustin inspected outputs) except "a
  separately scoped consumer exists" - which GEX-2 satisfies by existing.
- **GEX-3 = INFRA (LANE HIGH-RISK).** Workflow producer invocation (fail-soft,
  delete-before-fetch, staged, published) + "no cadence, no workflow" truth
  corrections + carrier tests + docs. Falsifies `artifact_flow_map:174` and the
  producer's "no cadence/no workflow" clause. Sequenced immediately after GEX-2
  usefulness is demonstrated (sec4.4).

Result: the published-board product is delivered end to end, in two governed
steps, with NO mixed-class problem and NO doctrine violation. This is the
structure that survives an independent doctrine-aware falsification.

**Option 2 - SINGLE END-TO-END SLICE (requires explicit owner override).** One
MATERIAL PRD spanning CONSUMER + INFRA + SIDECAR, delivering the board in one
merge. It requires Dustin to record an explicit written override of doctrine
G3/G4/G8 and the GEX-2/GEX-3 gate (a `docs/DECISIONS.md` entry or charge
amendment), because absent that override the slice violates binding canon and
will be re-flagged DESIGN INCOMPLETE. Its PRD would declare a primary CLASS
(CONSUMER or INFRA); LANE is HIGH-RISK either way (below).

### 6.3 Classification that holds under EITHER option

- **LANE: HIGH-RISK**, forced independently and redundantly - the renderer is a
  CONSUMER HIGH-RISK FILE (`:460`) and `.github/workflows/**` is an INFRA
  HIGH-RISK FILE (`:463`); each as payload triggers the Lane Downgrade
  Prohibition (`:501-504`). The payload/pointer carve-out cannot rescue a
  downgrade - it covers only `PROJECT_STATE.md`/`PRD_REGISTRY.md` (`:515-517`).
  Diff size is irrelevant (`:504-505`). Cosmetic Carve-Out does not apply
  (`:601-629`).
- **MATERIAL: YES**, re-confirmed on the expanded boundary. GOV-2 sec1 triggers
  that fire (`:18-29`): **T2** shared carrier across pipeline layers (`:21`);
  **T3** changes a production FILES/LOC ceiling (`:22`) - the reset itself;
  **T7** crosses delivery + dashboard + persistence (`:27-28`); **T1** if the
  PRD claims a complete consumer/renderer inventory (`:20`). T4 (`:23-24`) fires
  ONLY if a producer schema field is added - r2 adds none, so T4 does not fire.
  MICRO is barred (`GOV-2:51-63`); MATERIAL does not itself force HIGH-RISK
  (that comes from R11 above).
- **CLASS:** GEX-2 = CONSUMER; GEX-3 = INFRA (Option 1). Single primary CLASS
  under Option 2 with the mixed-surface caveat above.
- **Second-model disposition (both slices, HIGH-RISK >= 242):** each COMPLETE
  PRD carries a committed second-model artifact OR the exact line
  `SECOND-MODEL: instrument not commissioned, merging on Claude-review + human judgment.`
  (`docs/PRD_PROCESS.md:285-286`); CI fails a HIGH-RISK close carrying neither.
- **No network/CI-specific trigger exists** in PRD_PROCESS/GOV-2; the network
  dimension reaches MATERIAL only through T2/T7. The Cboe fetch adds no runtime
  dependency (producer is stdlib-only urllib).

---

## 7. Proposed automated carrier (GEX-3 half; documented here in full)

**Preferred (charge E): same-run ephemeral producer -> local artifact ->
renderer, no new persistence.** Concrete design:

1. **Where.** Wire the producer into the **hourly workflow only** for v1 - the
   intraday RTH render path where the card is eligible. The morning pipeline
   renders ~09:05 ET (pre-open), where the session gate (sec10) suppresses the
   card anyway, so wiring it is unnecessary for an intraday-only card (sec21
   Option A). Wiring the pipeline is deferred and tied to the session-scope
   decision (D-3).
2. **A dedicated step, immediately before render**, run as `continue-on-error:
   true` (records failure on that step only; never masks neighboring failures -
   the anti-pattern of `python ... || true` inside a shared `set -e` block is
   explicitly avoided). Shape:
   ```
   - name: Acquire GEX snapshot (fail-soft, non-blocking)
     continue-on-error: true
     run: |
       rm -f logs/gex_snapshot.json          # delete-before-fetch (sec18/D-0)
       python tools/gex_snapshot.py           # exits nonzero if Cboe is down
   ```
3. **Stage.** Add `logs/gex_snapshot.json` to the hourly explicit staging list
   (`hourly_alert.yml:179-186`) so a freshly produced artifact reaches `publish`.
4. **Render** consumes the just-written local artifact via the GEX-2 loader.
5. **Cadence** piggybacks the existing hourly cadence (~7-8 RTH slots/weekday);
   NO new scheduler/cron is added. Cboe is keyless delayed_quotes; one GET per
   render slot is well within reasonable polling.

**Producer-failure containment.** Cboe down/producer nonzero -> the GEX step
fails soft, no artifact is written, `rm -f` guarantees no stale leftover, the
loader sees no file -> card absent -> the dashboard still renders and publishes.
Unrelated failures still abort the job (the GEX step is the only one made
non-fatal). This behavior gets mutation coverage (sec24 tests A, K).

---

## 8. Freshness / session evidence table

The honest question: which fields prove the GEX structure belongs to the
CURRENT eligible market session? (`Y`=yes, `P`=partial/qualified, `N`=no.)

| Field | Source | Meaning | Fetch recency | Session eligibility | Observation age | Prior-session rejection |
|---|---|---|---|---|---|---|
| `fetched_at_utc` | producer clock `:345/:393` | when THIS run fetched | Y | N | N | N (needs a data clock) |
| `feed_timestamp_utc` | Cboe body `timestamp` `:346` | feed self-report (UTC by assumption) | P | P (self-certifying) | P (delayed, provider-trusted) | P (only vs an independent now) |
| `data_delay` | constant `:47` | static "~15m delayed" label | N | N | N | N |
| `observation_trading_date` | ET date of feed ts `:283` | feed's claimed session date | N | P (circular alone) | N | N alone (value to be CHECKED) |
| HTTP `Last-Modified` | NOT read (`:99-109`) | CDN mtime | (unavailable) | N | weak | N |
| per-contract `last_trade_time` | present, NOT emitted | last trade per strike | N | N | P (sparse) | weak |
| system `now` | render/load clock | wall clock at eval | Y (anchor) | N alone | N alone | N alone (required anchor) |

**Repo session capability (no calendar exists):** `cuttingboard/time_utils.py`
gives clock-hours + weekday helpers, explicitly holiday-UNAWARE
(`is_market_open` `:32-34`; `most_recent_completed_session_date` `:37-55`).
`cuttingboard/spy_observation.py` is the in-repo intended-vs-observed two-clock
precedent (`:43-114`). No `pandas_market_calendars`/`exchange_calendars`/
`holidays` dependency (`pyproject.toml`). The producer is stdlib-only and cannot
import `cuttingboard` (R11), so session logic must live on the READER side (the
loader, which already may use `time_utils`).

**Two distinct concepts, never conflated (charge sec7):**
1. ARTIFACT RECENCY - "we produced this JSON this run" - provable from
   `fetched_at_utc` (trustworthy in a same-run carrier).
2. MARKET-SESSION ELIGIBILITY - "the structure belongs to the current eligible
   session" - provable only by pairing an independent `now`-anchored session
   determination against the feed's claimed date; needs weekend AND holiday
   awareness, which the repo lacks. v1 uses the narrowest honest rule (sec10).

---

## 9. Freshness / session state machine (GEX-2 loader; deterministic, injectable now)

`_load_gex_context(path, *, now) -> dict | None`, private in
`dashboard_renderer.py`, `now` tz-aware UTC (default `datetime.now(timezone.utc)`
in `main()`, injected in tests). ALL gates below are computed here (main-side),
never in the render body. ANY failure returns `None` (card absent).

```
1. STRUCTURE:  file exists; parseable JSON; dict.            (else None)
2. IDENTITY:   schema_version/source/underlying/units/spot.basis/
               sign_convention/data_delay match the exact
               supported producer semantics (sec11).          (else None)
3. DOMAINS:    load-bearing numerics finite, non-bool, in-range (sec12).
4. PRESENCE:   spot.value>0; gex_total finite; dominant strike
               non-null finite + its gex finite.               (else None)
5. RECENCY:    0 <= (now - fetched_at_utc) <= FETCH_RECENCY_MAX (else None)
               -- bound on OUR fetch clock, NOT the feed clock.
               Defeats the stale last-good artifact (sec18/D-0).
6. SESSION:    is_market_open(convert_utc_to_et(now)) is True  (else None)
               AND zero_dte.observation_trading_date == et_date(now).
               Intraday-only (Option A); holiday-safe via the
               feed-date cross-check (below).
-> return the normalized display object (sec12), else None.
```

**Why this is honest and answers E1-002/D-2:**

- RECENCY is bound on `fetched_at_utc` (we fetched this run), never on the
  self-reported `feed_timestamp_utc`. No arbitrary feed-age threshold survives.
- SESSION reuses the canonical `time_utils.is_market_open` (weekday + RTH hours)
  - no second market-calendar is reimplemented. Overnight/weekend -> not open ->
  suppress. During RTH the ET and UTC calendar dates coincide, so the
  `observation_trading_date == et_date(now)` cross-check is unambiguous.
- The HOLIDAY gap (is_market_open is holiday-unaware) is closed WITHOUT a
  calendar by the cross-check: on a holiday the market is closed, so Cboe's
  latest delayed_quotes reflects a PRIOR session, its
  `observation_trading_date` != today -> suppress. This treats the feed date as
  a CORROBORATOR checked against an independent now-anchor, never as the
  self-certifying authority (the circularity trap of using it alone).
- `FETCH_RECENCY_MAX` is a single named constant on a TRUSTWORTHY clock; its
  exact value is a minor tunable knob (D-2'), semantically unlike the rejected
  feed-clock threshold. Recommended ~20 minutes (tolerates same-run + a slot gap
  + clock skew; rejects a prior slot's leftover as defense-in-depth behind the
  workflow `rm -f`). A future timestamp (`age < 0`) suppresses.

**Residual honesty limit (surfaced, not hidden):** the holiday cross-check
assumes Cboe reports a prior-session date on a closed day. If Cboe advances the
top-level `timestamp` to a holiday date with stale structure, the cross-check
would pass; this is a bounded provider-behavior assumption, flagged as part of
D-3 (session scope). Even then, the card is context-only and cannot affect any
decision (sec19).

---

## 10. Artifact semantic-identity contract (E1-004)

The loader must not accept numerically compatible JSON while hardcoding
disclosures. Every meaning-bearing field is validated against the exact producer
constant it stands for; a mismatch SUPPRESSES (never renders a false disclosure):

| Field | Required | If mismatch |
|---|---|---|
| `schema_version` | == the supported constant | suppress |
| `source` | == `"cboe_delayed_quotes"` | suppress |
| `underlying` | == `"_SPX"` | suppress |
| `units` | == the producer units constant | suppress |
| `spot.basis` | == the producer SPX-cash basis constant | suppress |
| `sign_convention` | == the producer constant (drives the `*` footnote) | suppress |
| `data_delay` | == the producer delay constant (drives "~15m delayed") | suppress |

The hardcoded card copy ("~15m delayed"; the sign-assumption footnote) is
LICENSED only by these equality checks - if the artifact's `data_delay` or
`sign_convention` differs from what the copy asserts, the card suppresses rather
than lie. Each identity field gets a discriminator mutation test (sec24 C).

---

## 11. Loader normalization contract + exact field domains (E1-005)

Numbers: native int/float only; **reject bool**; reject numeric strings; finite
only (`math.isfinite`). Then:

| Datum | Domain | Unavailable form |
|---|---|---|
| `spot.value` | finite float > 0 | (load-bearing; absence/invalid -> card absent) |
| `gex_total_1pct_usd` | finite float (sign kept) | (load-bearing) |
| `dominant_net_gamma.strike` | finite float > 0, non-null | null + reason `all_net_gamma_zero` -> **card absent** |
| `dominant_net_gamma.gex_1pct_usd` | finite float | (load-bearing) |
| `call_wall.strike` | finite float > 0 | null + reason in {`no_eligible_calls`,`no_nonzero_call_gex`} -> omit Call row |
| `put_wall.strike` | finite float > 0 | null + reason in {`no_eligible_puts`,`no_nonzero_put_gex`} -> omit Put row |
| `zero_dte.share` | finite float in [0,1] | null + reason `zero_abs_gex_denominator` -> omit 0DTE row |
| `fetched_at_utc` | ISO-8601, tz-aware, parseable | invalid -> card absent (recency gate) |
| `zero_dte.observation_trading_date` | ISO date, parseable | invalid -> card absent (session gate) |
| `feed_timestamp_utc` | ISO-8601 parseable (display only) | invalid -> card absent |

Timestamps are parsed with explicit UTC/ET semantics; naive/ambiguous ->
suppress. A malformed pseudo-unavailable state (e.g. `strike` non-null but
`reason` also non-null, or `reason` an unrecognized string, or `share` null with
no recognized reason) is treated as INVALID -> the relevant gate suppresses; it
is never accepted as honest unavailability.

---

## 12. Typed-unavailable unions and recognized reasons (E1-005)

Available sub-object: `strike` finite>0, `gex_1pct_usd` finite, `reason is None`.
Unavailable sub-object: `strike is None`, `gex_1pct_usd is None`, `reason` in the
exact recognized set for that role. 0DTE available: `share` in [0,1],
`reason is None`; unavailable: `share is None`, `reason == "zero_abs_gex_denominator"`.

Recognized producer reasons (verified `tests/test_gex_snapshot.py`):
`dominant`: `all_net_gamma_zero`; `call`: `no_eligible_calls`,
`no_nonzero_call_gex`; `put`: `no_eligible_puts`, `no_nonzero_put_gex`;
`0DTE`: `zero_abs_gex_denominator`.

Product disposition: dominant unavailable -> **suppress whole card** (dominant is
the central "strike vs spot" reading); call unavailable -> omit Call row only;
put unavailable -> omit Put row only; 0DTE unavailable -> omit 0DTE row only. An
unknown reason, or a contradictory null/value/reason combination, is INVALID
(sec11), not honest unavailability.

---

## 13. Renderer purity and exception isolation (E1-006)

**Honest scope.** `render_dashboard_html` (`:2049-3194`) already performs LEGACY
conditional file I/O at `:2080` (`_resolve_market_map`) and `:2158`
(`_load_macro_snapshot`). A blanket "the renderer does zero I/O" claim is FALSE.
The GEX purity claim is scoped narrowly and provably: **the GEX render branch
performs no file I/O, no clock read, no timezone conversion, no env, no network,
no artifact-loader call** - the GEX object is fully pre-resolved in `main()` and
passed as one kwarg, exactly like the `alert-watchlist` precedent
(`if alert_candidates:` at `:2593-2594`, no else; loader `_load_contract_entry_context`
`:3262` called in `main()` `:3385`).

**Seam.**
- Loader `_load_gex_context` (sec9) in `main()`; freshness/session/identity/
  domain all resolved here (main-side), plus ET display strings pre-formatted
  here (there is NO ET helper in the renderer - only PT at `:328/:348`; do not
  read the clock or convert tz in render).
- Do NOT reuse `_load_json_optional` (`:935-941`) - it RAISES `RuntimeError` on
  malformed JSON, which would fail the dashboard. Model on
  `_load_trend_structure_snapshot` (`:953-965`, never raises), EXTENDED with the
  identity/domain/finite/recency/session checks (no existing helper does all).
- One keyword-only `gex_context: dict | None = None` threaded through
  `write_dashboard` (`:3197-3218`, forwarded `:3236-3257`) and
  `render_dashboard_html` (`:2052-2070`). All existing call sites pass keywords /
  default `None`, so the kwarg is source-compatible.
- Render branch: `if gex_context: <paint> ` with NO else (no placeholder shell).

**Exception isolation.** The entire loader body is guarded so every failure path
(absent, permission, race-disappear, UnicodeDecodeError, JSONDecodeError, wrong
type, missing field, non-finite, tz-db error, any unexpected exception) returns
`None`. An invalid GEX artifact must NEVER escape as an exception that fails the
dashboard job or trips generic failure notification. The broad-except boundary is
confined to the loader; unrelated programmer errors outside it still surface. A
NEW red isolation test is required - the existing boundary test
(`tests/test_dash_boundary.py:34-46`) fences only `"contract"`-named reads and
will not catch a GEX in-render read (sec24 F).

---

## 14. Product card contract (compact; deterministic; mutation-testable)

```
GEX
Net       -$56.3B*
Dominant   7640   -0.02%
Call       8000   +4.70%
Put        8000   +4.70%
0DTE       7.6%
19:47 ET . ~15m delayed

* signed under configured positioning assumption; positioning is not measured
```

Formatting: Net = `gex_total/1e9`, one decimal, explicit sign, `$`..`B`, trailing
`*`. Strike rendered without trailing `.0` when integer-valued, then signed
2-decimal `distance_pct = ((strike/spot)-1)*100` (D-1; `+0.00%` for zero). 0DTE =
`share*100`, one decimal, `%`. Time = `feed_timestamp_utc` -> ET `HH:MM ET`
(pre-formatted in the loader) as an "as of" label - NOT an age claim - beside the
static `~15m delayed` disclosure. Sign-assumption footnote always present on a
rendered card. Display clock choice (feed-ts vs fetched-at) is a minor residual
(D-4); recommend feed-ts as the data's "as of".

**CUT from v1 (asserted absent by tests):** gross call/put-wall dollars; raw
dominant GEX magnitude; full-precision net USD; top-strike table; expiration
diagnostics; coverage/exclusion/provenance dumps; zero-OI/zero-gamma counts;
source URL; what-changed; persistence/history; gamma flip; max pain; vanna;
charm; live flow/CVD; and ALL interpretive labels - `AT SPOT`, `MAGNET`, `PIN`,
`SUPPORT`, `RESISTANCE`, `SHORT-GAMMA`/`LONG-GAMMA REGIME`, "tracks spot",
"dealers are short gamma", regime badges, threshold-derived state, predictive
language. Unknown/unavailable disappears honestly; never invented interpretation.

---

## 15. Failure matrix (fail soft without lying)

| Layer | Condition | Behavior |
|---|---|---|
| Producer/carrier | HTTP/network error, timeout, malformed top-level, write fail, nonzero exit, Cboe unavailable | GEX step fails soft (`continue-on-error`); no artifact; `rm -f` leaves none; publish proceeds; no GEX-specific failure notification |
| Loader | file absent / permission / race-disappear / UnicodeDecodeError / malformed JSON / wrong shape | `None` -> card absent |
| Loader | wrong schema/source/underlying/units/spot.basis/sign_convention/data_delay | `None` -> card absent (identity, sec10) |
| Loader | bool / numeric-string / NaN / +-Inf / spot<=0 / strike<=0 / share<0 / share>1 | `None` -> card absent (domains, sec11) |
| Loader | stale (recency fail) / ineligible session / future ts / clock skew | `None` -> card absent (sec9) |
| Loader | contradictory or unknown-reason unavailable state | `None` -> card absent (sec12) |
| Loader | dominant unavailable | `None` -> card absent |
| Loader | call/put/0DTE individually unavailable (else valid) | that row omitted; card renders |
| Render | `gex_context is None` | no GEX output; baseline byte-identical (sec17) |
| Publish | GEX acquisition fails | dashboard renders + publishes; readiness/decision unchanged |
| Publish | unrelated render error | still fails loudly (GEX isolation does not mask it) |

---

## 16. Behavioral non-coupling proof (traced cold at e89eebb)

GEX couples into NONE of the following; each with the current-code reason:

- **`assert_valid_payload` (`payload.py:217-289`)** checks only for MISSING
  required keys (`_require_keys`), does not reject extras; GEX-2 never touches
  payload (it reads the artifact directly), so the validator is untouched.
- **`validate_coherent_publish` (`dashboard_renderer.py:563-627`)** compares a
  hardcoded `generation_id` triple (payload/run/market_map); GEX has no
  generation_id and is not one of the three.
- **Readiness (`scripts/check_readiness.py`)** asserts a fixed 3-marker allowlist
  `REQUIRED_HTML_MARKERS` (`:39-43`) as a required-presence SUBSET and a fixed
  JSON-required set (`:27-33`); no card enumeration. The coupling to AVOID is
  adding a GEX marker to `REQUIRED_HTML_MARKERS` - GEX must not.
- **Notification formatters** dispatch on `AlertEvent` types, never dashboard
  cards. **Audit writers** never enumerate cards. **No decision module reads the
  artifact** (rg gex cuttingboard/ -> none), so presence/absence/staleness/
  failure changes no TRADE/NO TRADE/HALT, candidate permission, qualification,
  grading, ranking, sizing, regime, kill switch, or execution.
- **No generic all-cards loop** exists in the renderer; every card is explicit
  `w(...)`, so a new card cannot be pulled into a required-sections iterator.

Binding: GEX must not become a required payload section, contract field,
coherent-publish requirement, readiness marker, notification field, or audit
requirement. If implementation is found to require any of these -> STOP (sec27).

---

## 17. Baseline neutrality (E1-007) and persistence disposition

**Baseline neutrality.** With `gex_context is None` the rendered dashboard must be
byte-identical to the pre-GEX baseline. There is NO golden-HTML oracle in the
repo today (existing tests use render-twice `==` and section substrings). The
design therefore introduces a **committed pre-GEX golden characterization** (a
frozen full-HTML fixture, or an equivalent deterministic hash captured on the
pre-GEX renderer) and asserts `render_dashboard_html(..., gex_context=None) ==
golden` (sec24 G). Comparing only "None vs default None" is insufficient (both
could share the same accidental CSS/whitespace) - the oracle is an independent
pre-feature baseline. If unrelated nondeterministic fields make exact byte
equality impossible, the smallest deterministic characterization is used and the
weakening is stated, never silent.

**Persistence: none new (GEX-2).** The consumer writes no file and adds no
persisted schema surface; card state is in-memory per render. GEX-3 adds no
long-lived persistence either - the same-run artifact is ephemeral on the runner;
the only published copy is the existing `logs/`-in-`publish` overlay, and the
loader's recency gate + workflow `rm -f` prevent a stale copy from rendering.
No GitHub artifact upload/download/cache is introduced (G5 additive-only honored;
one writer, `tools/gex_snapshot.py`).

---

## 18. Preview / developer workflow

- **Deterministic tests only** use synthetic GEX fixtures (no network), built like
  `tests/test_gex_snapshot.py` (`gx.run(now=, fetch_fn=, artifact_path=)`), with
  an injected `now` into the loader.
- **`dashboard_preview.yml` stays GEX-absent** (deterministic pre-merge preview);
  it renders live payload but must NOT perform a live Cboe fetch.
  `scripts/preview_fixtures.py` remains baseline/no-GEX by construction (its
  `render_kwargs` default is empty and no case passes GEX).
- **Local live preview for Dustin** reuses the existing manual path: run
  `tools/gex_snapshot.py` by hand, then render via `scripts/preview_dashboard.sh`
  to a `reports/output/...` scratch path - NO new production path, NEVER
  overwriting committed `ui/dashboard.html`.
- An opt-in synthetic GEX fixture MAY be added to `preview_fixtures.py` (author
  discretion, GEX-2 test cone) so Dustin can eyeball the card layout
  deterministically.

---

## 19. Exhaustive consumer / call-site inventory (personally re-verified)

- Machine consumers of `logs/gex_snapshot.json` today: **NONE**
  (`rg -i "gex_snapshot|gex_total|dominant_net_gamma|call_wall" cuttingboard/`
  -> rc=1; `rg -i gex .github/` -> rc=1; `rg -i gex dashboard_renderer.py`
  -> rc=1). GEX-2 is provably the first machine reader; GEX-3 the first workflow
  reference.
- Renderer production call sites: `render_dashboard_html` at
  `dashboard_renderer.py:3236` (in `write_dashboard`) and
  `scripts/preview_fixtures.py:53`; `write_dashboard` at `:3415` (in `main`).
  ~400 test call sites, all keyword / `None`-default compatible.
- Family-B full-suppress precedent: `alert-watchlist` (loader `:3262`, main
  `:3385`, kwarg threaded `:3208/:3246/:3421`, render `:2593-2594`).

---

## 20. FILES cone (rebuilt from zero; dispositioned per file)

Legend: `[P]` payload, `[T]` test, `[D]` doc, `[L]` lifecycle, `[X]` not touched.

### Option 1 - GEX-2 (CONSUMER, display consumer)
```
[P] cuttingboard/delivery/dashboard_renderer.py   loader + kwarg + GEX render branch
[T] tests/test_dash_gex.py                         new focused consumer/mutation suite
[T] tests/test_check_readiness.py                  ADD independent literal marker-set test (E1-007)
[D] docs/artifact_flow_map.md                      "machine consumers: none" -> the renderer
[D] docs/CALL_SITE_MAP.md                          new loader read-site (E1-008; no longer discretionary)
[D] docs/plans/decision-support-workplan-v0.1.md   GEX-2 row status
[D] docs/PROJECT_STATE.md                          "no consumer" -> one display consumer
[D] tools/gex_snapshot.py                          docstring: "no machine consumer" -> corrected (comment-only)
[L] docs/prd_history/PRD-3NN.md, PRD_REGISTRY.md, prd_index.json   Stage-0 lifecycle
```

### Option 1 - GEX-3 (INFRA, automated carrier)
```
[P] .github/workflows/hourly_alert.yml             GEX acquire step (fail-soft, rm -f) + stage-list add
[T] tests/test_ci_artifact_hygiene.py              carrier structure/order/stage-list text-slice tests
[T] tests/test_dash_gex_carrier.py (or extend)     python fail-soft behavior test
[D] docs/artifact_flow_map.md                      "no cadence, cron" -> the hourly carrier
[D] docs/plans/decision-support-workplan-v0.1.md   GEX-3 row status
[D] docs/PROJECT_STATE.md                          cadence line
[D] tools/gex_snapshot.py                           docstring: "no cadence, no workflow" -> corrected (comment-only)
[L] docs/prd_history/PRD-3NN.md, PRD_REGISTRY.md, prd_index.json   Stage-0 lifecycle
```

Under **Option 2** the two payload sets merge into one PRD's FILES (with the
explicit doctrine override recorded). `.github/workflows/cuttingboard.yml` is
**DEFERRED** (pre-open render; card suppresses) unless D-3 selects an after-close
card. `docs/SCHEMA_MAP.md` is **NOT required** (no schema field added; T4 does
not fire). **NOT TOUCHED (`[X]`; touching any is a boundary expansion -> STOP):**
producer MATH/schema, `tests/test_gex_snapshot.py`, `payload.py`,
`check_readiness.py`'s marker constant (add none), `runtime/`, `qualification/`,
`regime/`, `execution/`, `notifications/`, `pages.yml`, `dashboard_preview.yml`
(kept GEX-absent), `ui/*` as committed source, `logs/gex_snapshot.json` as
committed content.

---

## 21. LOC / dependency estimate (honest; old <=120 discarded)

Per GOV-2 sec5, the RANGE is stated now; the binding GATE A CEILING is Dustin's,
proposed at top-of-range plus margin. Validation/identity/freshness/typed-
unavailable code counts as first-class surface (`PRD_PROCESS.md:672-687`); test
LOC is outside the net-production metric.

- **GEX-2 production** (`dashboard_renderer.py`): loader (structure+identity+
  domains+recency+session+ET pre-format) ~70-110; kwarg threading ~6; render
  branch ~35-60; producer docstring comment ~2. Expected **~110-180 net**;
  proposed **Gate A ceiling 210**.
- **GEX-3 production** (`hourly_alert.yml` + producer docstring): workflow step +
  stage-list ~12-25; producer docstring comment ~2. Expected **~15-30**; proposed
  **Gate A ceiling 45**.
- **Under Option 2** combined production expected **~125-210**; proposed ceiling
  **255**.
- **Tests**: GEX-2 ~250-400 LOC; GEX-3 ~60-120 LOC (outside the net metric).
- **0 new dependencies.** Stdlib `datetime`/`zoneinfo` + existing
  `cuttingboard.time_utils`; producer stays stdlib-only urllib. Any tz-db failure
  is caught by the loader (card absent), never a dashboard crash. No market-
  calendar library is added (the intraday-only + feed-date cross-check avoids it).

---

## 22. Documentation / lifecycle consequences (exact lines)

- `docs/artifact_flow_map.md:169` "machine consumers: none" -> the dashboard
  display renderer (GEX-2). `:174-175` "no cadence, cron, or scheduled publish"
  -> the hourly carrier (GEX-3). `:168-169`'s "no decision module reads it ...
  changes no TRADE/HALT" survives (display-only).
- `tools/gex_snapshot.py:6-8` "No cadence, no workflow, no machine consumer" ->
  "no machine consumer" corrected by GEX-2, "no cadence, no workflow" by GEX-3;
  "no decision authority" survives. R11 import-isolation (`:8`) is UNAFFECTED -
  the renderer reads the JSON artifact, it does not import the module.
- `docs/PROJECT_STATE.md:32` "no cadence, no consumer" -> updated per slice.
- `docs/CALL_SITE_MAP.md` - ADD the GEX loader read-site (convention `:3`;
  E1-008). `docs/SCHEMA_MAP.md` - no entry required (no new field).
- `docs/plans/decision-support-workplan-v0.1.md:52` GEX-2 row `EVIDENCE BLOCKED`
  -> implemented display consumer; add a GEX-3 cadence row.
- Do NOT clean unrelated North Star / Polygon doc debt in this work.

---

## 23. Test / mutation matrix (each guard: setup -> mutation -> which test turns red)

Synthetic artifacts only; no network; injected `now`. "Bad impl that survives
without the test" stated for each.

| # | Test | Setup -> mutation -> expected | Bad impl caught |
|---|---|---|---|
| A | carrier fail-soft | producer step fails -> dashboard still publishes, no card, no GEX notification | a `set -e` naive call that aborts publish |
| B | valid current-session artifact | fresh same-run artifact, `now` in RTH, obs_date==today -> card renders | render path dropped |
| C | identity discriminator | mutate each of schema_version/source/underlying/units/spot.basis/sign_convention/data_delay -> card suppressed | loader hardcodes disclosures, accepts foreign JSON |
| D | domain guards | bool / numeric-string / NaN / +-Inf / spot<=0 / strike<=0 / share<0 / share>1 -> suppressed (each) | `float()` coercion accepting bool/str; missing isfinite |
| E | typed unavailable | each recognized reason (call/put/0DTE) -> that row omitted, card renders | over-broad suppression or accepting unknown reason |
| F | dominant unavailable | `all_net_gamma_zero` -> WHOLE card absent | treating dominant like an optional row |
| G | GEX-branch purity | monkeypatch `open` + `_utcnow`; render with a valid `gex_context` -> neither called during GEX paint | in-render file read / clock read |
| H | recency (E1-002) | old `fetched_at_utc`, injected `now` -> suppressed; fresh -> renders | freshness bound on feed clock, or none |
| I | session eligibility | `now` outside RTH / weekend -> suppressed; obs_date != et_date(now) (holiday) -> suppressed | no session gate; feed-date used self-certifyingly |
| J | baseline neutrality | `gex_context=None` render == committed pre-GEX golden (byte/hash) | stray CSS/whitespace/empty shell in the None path |
| K | stale last-good leak | old artifact present + injected `now` beyond recency -> suppressed; AND carrier text-slice asserts `rm -f` precedes the producer | a leftover/ restored file rendering as current |
| L | readiness independence | literal `assert REQUIRED_HTML_MARKERS == (...3 markers...)` | a mutation ADDING a GEX marker (uncatchable by the existing parametrize, which derives from the mutable constant) |
| M | forbidden vocabulary | assert none of MAGNET/PIN/SUPPORT/RESISTANCE/SHORT-GAMMA/LONG-GAMMA/"tracks spot"/"dealers are short gamma" in the GEX section | interpretive copy leaking in |
| N | CUT magnitudes | assert raw call/put/dominant GEX dollars, coverage/provenance dumps absent from the card | leaking raw diagnostics |
| O | non-coupling | with and without the card, `assert_valid_payload`/`validate_coherent_publish`/readiness pass identically | GEX becoming a required data dependency |
| P | carrier structure | text-slice: hourly workflow contains the GEX acquire step ordered before render, `continue-on-error: true`, and `logs/gex_snapshot.json` in the stage list | carrier that never stages/publishes the artifact |

Determinism: identical inputs -> identical output; no wall clock in the render
body; `now` injected into the loader; producer `now`/`fetch_fn` injected.

---

## 24. CUT / forbidden interpretations (binding)

Deferred, NOT in v1: GEX history; what-changed; persistence DB; gamma flip;
vanna; charm; max pain; estimated intraday OI; live flow; CVD; OPRA; heatmap; SPY
duplicate; second provider; any DECISION coupling; thresholds; parameter tuning;
ML; morning-pipeline wiring (deferred, D-3); a producer schema/freshness field;
after-close/prior-session card (D-3). Forbidden vocabulary is enumerated in sec14
and test-bound in sec23 M/N. GEX remains ONE removable context card that informs
the board and never authorizes the trade.

---

## 25. Residual owner decisions (isolated; each with a recommendation)

- **D-0 (HEADLINE) - Governance structure: split vs single slice.**
  RECOMMEND **Option 1 (doctrine-compliant split: GEX-2 consumer, then GEX-3
  carrier)** - it delivers the published-board product in two governed steps,
  has no mixed-class problem, and survives doctrine-aware falsification. Option 2
  (single end-to-end slice) is available only with Dustin's explicit written
  override of doctrine G3/G4/G8 + the GEX-2/GEX-3 gate. Everything downstream
  (FILES partition, CLASS, number of Gate As) depends on this.
- **D-1 - Distance/percent presentation.** Owner-APPROVED; recorded. The
  workplan "no renderer computation" (`:406`) bars re-deriving GEX STRUCTURAL
  values in the display layer; loader-side freshness suppression and trivial
  presentation math (billions, percent, distance) are the established consumer
  pattern, not that. RECOMMEND PERMITTED (as ruled).
- **D-2' - `FETCH_RECENCY_MAX`.** RECOMMEND ~20 minutes on `fetched_at_utc` (a
  trustworthy clock), a single named tunable constant; the rejected D-2 was a
  threshold on the untrustworthy feed clock - this is categorically different.
- **D-3 - Session scope.** RECOMMEND **Option A: intraday-only** (card eligible
  only during an RTH session; overnight/weekend/holiday suppress). Option B
  (same-session after-close, explicitly labeled) and Option C (broader prior-
  session context) both require wiring the morning pipeline and a more complex
  freshness label, and risk implying overnight structure is live. A informs the
  board most honestly at least cost; recommend A for v1.
- **D-4 - Display clock.** RECOMMEND showing `feed_timestamp_utc` ET as the "as
  of" label beside "~15m delayed"; alternative is `fetched_at_utc`. Minor.

---

## 26. Explicit implementation stop conditions

STOP and return to HELM/Dustin (do not route around) if, at implementation time:
1. the card requires ANY producer MATH or SCHEMA change (new emitted field,
   producer-computed distance) - boundary expansion;
2. implementation requires touching payload schema, `assert_valid_payload`,
   `validate_coherent_publish`, or adding a `REQUIRED_HTML_MARKERS` entry;
3. a production file beyond those in the chosen FILES cone (sec20) is required -
   amend the PRD + this packet, obtain fresh-context review of the exact amended
   revision, and receive Dustin's amended Gate A (GOV-2 sec5);
4. the carrier cannot be made fail-soft without masking unrelated failures;
5. scope expands to add a second reader, decision coupling, morning-pipeline
   wiring, or a new schedule - re-run GOV-2 sec1 classification;
6. D-0 is unresolved - the FILES partition and Gate-A count are undefined until
   Dustin rules split vs single slice.

---

## 27. Fresh Codex EVENT-1 review handoff block

- **Subject:** THIS rebuilt packet at its exact committed head (reported by the
  author on push), read against the repository surfaces it cites - NOT a review
  of the r1 review's prose (GOV-1 reviews target the change).
- **Falsification targets (highest leverage first):**
  1. Does the carrier (sec7) actually place a fresh `gex_snapshot.json` on the
     published board in clean CI, and is it genuinely fail-soft without masking
     unrelated failures? (E1-001)
  2. Is the freshness/session contract (sec9) honest - recency on `fetched_at_utc`,
     session on `is_market_open` + the `observation_trading_date` cross-check -
     and does the holiday assumption hold or need narrowing? (E1-002)
  3. Is the D-0 split the correct reading of doctrine G3/G4/G8 + the GEX-2/GEX-3
     gate, or is there a canonical path that houses one slice? (governance)
  4. Are the identity/domain/typed-unavailable contracts (sec10-12) complete, and
     the GEX-branch purity claim (sec13) correctly scoped given the renderer's
     legacy I/O?
  5. Does the test matrix (sec23) give each load-bearing guard an isolating
     mutation, including baseline byte-identity and readiness independence?
- **Author has NOT commissioned Codex.** HELM commissions the fresh review.

---

## 28. Author self-verification results (r2)

- Repo/branch/SHA, PR #261 shape, prior head, dirty state: verified (sec1).
- Decisive sweeps RE-RUN by the main agent (Author discipline 4): GEX absent from
  the renderer, the `cuttingboard/` package, and `.github/` (all rc=1). PASS.
- Producer contract read first-hand (`_build_artifact` `:294-360`, `_zero_dte`
  `:262-287`, clocks `:345/:346`, docstring `:6-13`); `observation_trading_date`
  unconditional emission confirmed. PASS.
- Renderer seam, purity truth (legacy I/O `:2080/:2158`), alert-watchlist
  precedent (`:2593`), no ET helper: verified via recon + `:2593` re-read. PASS.
- Freshness clocks + no-calendar + `time_utils`/`spy_observation` precedent:
  verified. PASS.
- Classification (`PRD_PROCESS.md:412-421/:456-463/:499-517`), GOV-2 triggers
  (`:18-29/:51-63/:213-238`), doctrine G3/G4/G8 + sec4.4 read verbatim: PASS.
- Test seams (readiness marker mutability, no golden oracle, YAML text-slice
  pattern, producer fixture injection): verified. PASS.
- No production/test/workflow code changed by this packet; only the packet doc
  under `audits/gex-2-material-packet-2026-08/`. `git diff --check` clean
  (reported on push).

Pre-existing repo debt observed, NOT absorbed (out of scope for this design-only
charge): the registry-gap hook flags three `PRD-301.*.confirmation.*.md` files
lacking `PRD_REGISTRY.md` rows - unrelated to GEX; surfaced for Dustin.

---

## 29. Downstream sequence (informative; no authority created here)

Rebuilt packet (this) -> fresh Codex EVENT-1 falsification (read-only) -> one
consolidated correction -> Codex exact-corrected-head confirmation (GOV-2 sec7)
-> Dustin design-direction ruling + D-0 (split vs single) -> Stage-0 PRD(s) ->
fresh-context PRD review -> Gate A -> implementation -> implementation review +
PRD-242 second-model disposition -> Dustin merge.

**This packet authorizes none of the above. It is design only.**
