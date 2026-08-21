# GEX Published-Board Context Slice: MATERIAL design packet (REBUILD r3)

```
STATUS: PROVISIONAL MATERIAL PACKET - REBUILD r3 - 2026-08-20 - DESIGN ONLY
AUTHORIZES NO IMPLEMENTATION, NO PRD NUMBER, NO GATE A, NO MERGE,
  NO CODEX COMMISSION BY THE AUTHOR.
DERIVED AT main SHA: e89eebb64997e8857827a9f294d228538b30bdce
REVISION HISTORY (preserved in git):
  r1 a7810d2 -> Codex EVENT-1: DESIGN INCOMPLETE, 9 findings (boundary reset).
  r2 7e3e710 -> HELM review: D-0 approved (doctrine split, no override) +
     two pre-Codex findings H-1 (circular session gate) and H-2 (artifact
     should stay ephemeral). This r3 addresses both before fresh Codex EVENT-1.
GOV-2 CYCLE: r3 awaits a NEW fresh independent Codex EVENT-1 falsification of
  this exact head; NOT review-clean; NO downstream authority until that review
  + exact-corrected-head confirmation pass and Dustin issues a design-direction
  ruling.
OWNER DECISIONS FROZEN (HELM, 2026-08-20): D-0 doctrine-compliant split APPROVED
  (no override); D-1 presentation distance math APPROVED; D-2 feed_timestamp
  freshness REJECTED; D-3 intraday-only preferred but must rest on truthful
  INDEPENDENT session evidence (the r2 gate is NOT holiday-safe); D-4 display
  clock minor / may stay open.
```

> Upstream MATERIAL design packet GOV-2 requires before any GEX display PRD or
> implementation authority. r3 reconstitutes the freshness contract on
> independent market-observation evidence and makes the raw artifact genuinely
> ephemeral. Nothing here is buildable authority. Sequence:
> **this rebuilt packet (now)** -> fresh Codex EVENT-1 -> one correction ->
> Codex exact-corrected-head confirmation (GOV-2 sec7) -> Dustin design-direction
> ruling -> Stage-0 PRD(s) -> fresh-context PRD review -> Gate A.

---

## 0. Executive design decision

**The product (unchanged from the owner charge).** A compact, fully-removable
GEX context card on the REAL published Cuttingboard board; context only ("GEX
informs the board, never authorizes the trade"); fail-soft (unavailable/invalid/
stale -> the card disappears and the board is behaviorally unchanged).

**The doctrine-compliant structure (D-0 APPROVED; no override).** The delivered
product spans three canonical surfaces, so it lands as THREE tightly sequenced
slices, each single-class, each its own PRD + fresh-context review + Gate A:

```
GEX-1b  SIDECAR  producer freshness-evidence field  (prerequisite; sec6.3, sec8-9)
  -> GEX-2  CONSUMER  validated loader + display card  (sec9-16)
      -> GEX-3  INFRA  ephemeral same-run carrier       (sec7, sec17)
```

**What r3 changed (the two HELM findings).**

- **H-1 (circular session gate) - FIXED.** r2 gated current-session eligibility
  on `time_utils.is_market_open` (a clock-only check, no weekday/holiday) plus
  `observation_trading_date == today` - but that date derives from the feed's
  edge-regeneration `timestamp`, the very clock EVENT-1 rejected. Two clocks that
  both track "now" cannot prove market observation; a weekday holiday or a
  weekend manual run during 09:30-16:00 ET satisfies both while carrying prior-
  session structure. r3 REPLACES that gate with **independent market-observation
  recency**: the producer emits the underlying delayed last-trade timestamp
  (`data.last_trade_time`), which the captured evidence proves sits ~15 minutes
  behind the edge-regeneration clock (i.e. it is the delayed market clock, not
  the regeneration heartbeat) and freezes overnight/weekend/holiday. The loader
  suppresses unless that timestamp is recent relative to `now`. No weekday logic,
  no holiday table, no reliance on the feed `timestamp`. This requires a
  narrowly-necessary PRODUCER SCHEMA EXTENSION, surfaced as GEX-1b (sec6.3).
- **H-2 (artifact should be ephemeral) - FIXED.** r2 contradicted itself by
  calling the design "ephemeral" while proposing to `git add logs/gex_snapshot.json`.
  The hourly renderer consumes the artifact BEFORE the artifact commit, so the
  raw JSON never needs committing - the published product is `ui/*.html`. r3
  keeps the artifact runner-local and UNCOMMITTED (no stage/restore/cache/upload),
  with delete-before-fetch so an old local file cannot substitute for a failed
  acquisition (sec7, sec17).

**No new material boundary was silently incorporated.** The producer schema
extension is the owner-anticipated freshness consequence (charge H-1) and is
surfaced as its own slice, not hidden in GEX-2.

---

## 1. Exact repo / base / head / PR evidence

- Repo `dwats250/cuttingboard`; `main` = `origin/main` =
  `e89eebb64997e8857827a9f294d228538b30bdce` (no drift).
- MATERIAL packet PR **#261** (OPEN, DRAFT), base `main`, head branch
  `worktree-gex-2-material-packet`; r2 head `7e3e710`; this r3 head reported on
  push (sec28). r1 `a7810d2` and r2 `7e3e710` preserved in git history.
- Packet file (revised in place):
  `audits/gex-2-material-packet-2026-08/GEX_2_MATERIAL_DESIGN_PACKET_2026-08-20.md`.
- Unrelated NS-2E PRs #222/#225/#226 untouched.

---

## 2. Prior EVENT-1 disposition and absorption (all nine findings)

| Finding | Absorbed by (r3) |
|---|---|
| E1-001 NO AUTOMATED CARRIER | sec7 ephemeral same-run carrier in the hourly job (GEX-3) |
| E1-002 WRONG FRESHNESS CLOCK | sec8/9 independent market-observation recency on the producer's underlying-last-trade field; feed `timestamp` never gates |
| E1-003 PRODUCER TRUTH BECOMES FALSE | sec22 per-slice truth-sync: "machine consumers: none" -> GEX-2; "no cadence/no workflow" -> GEX-3; the new field itself is GEX-1b |
| E1-004 SEMANTIC IDENTITY | sec10 identity contract + discriminator mutations (sec23 C) |
| E1-005 FIELD DOMAINS + TYPED UNAVAILABLE | sec11/12 |
| E1-006 RENDERER PURITY + ISOLATION | sec13 GEX-branch-scoped purity + new red isolation test |
| E1-007 TEST/MUTATION MATRIX | sec23 (golden byte-identity, readiness independence, carrier behavior, ephemerality) |
| E1-008 CALL_SITE_MAP | sec22 doc cone |
| E1-009 LOC ESTIMATE | sec21 per-slice honest ranges |

---

## 3. Owner rulings absorbed (frozen this cycle)

- **D-0 - doctrine-compliant split APPROVED; no override.** Canonical ladder
  kept: GEX-2 = display CONSUMER; GEX-3 = cadence/carrier INFRA; plus the
  GEX-1b SIDECAR producer prerequisite that H-1 forces.
- **D-1 - presentation distance math APPROVED** (`((strike/spot)-1)*100`, display
  only; never a threshold/state/regime/inference/support-resistance/magnet/signal).
- **D-2 - feed_timestamp freshness REJECTED** (and not retained provisionally).
- **D-3 - intraday-only preferred, but MUST rest on truthful independent session
  evidence.** r3 supplies it (sec8/9); the r2 gate is explicitly NOT called
  holiday-safe.
- **D-4 - display clock minor**, may stay open (sec14/sec25).
- Context-only invariant and fail-soft (charge B) proven in sec16/sec19.

---

## 4. Frozen GEX-1 producer contract (reverified at e89eebb)

`tools/gex_snapshot.py` (428 lines); endpoint `.../delayed_quotes/options/_SPX.json`
(`:42`); SPX+SPXW; stdlib-only; isolated (R11, docstring `:8-13`).
`_build_artifact` (`:294-360`) emits, among others: `schema_version`, `source`
(`"cboe_delayed_quotes"`), `underlying` (`"_SPX"`), `fetched_at_utc` (`:345`,
producer fetch instant), `feed_timestamp_utc` (`:346`, the untrustworthy feed
clock), `data_delay` (`:47/:347`), `spot{value,basis}`, `sign_convention`,
`units`, `gex_total_1pct_usd`, `call_wall`/`put_wall`/`dominant_net_gamma`
(`{strike,gex_1pct_usd,reason}`), `zero_dte{share,...,observation_trading_date}`.

**Frozen (do NOT reopen in any slice):** GEX math, wall/dominant selection, 0DTE
definition, SPX-only slice, formula, sign convention, provider choice, R11
isolation, the per-contract admissibility path `_classify_row` (`:191`, reads
only `{option,gamma,open_interest}`). GEX-1b (sec6.3) adds ONE freshness field
read from the response's underlying block; it changes no GEX math and does not
touch `_classify_row`.

Load-bearing facts: `fetched_at_utc` is our own fetch clock (trustworthy for
run-recency); `feed_timestamp_utc`/`observation_trading_date` derive from the
feed's edge-regeneration `timestamp` (NOT market observation - E1-002/H-1);
`data_delay` is a descriptive constant; each structural sub-object may be
individually unavailable while the artifact is otherwise valid.

---

## 5. Complete current producer-to-published-board flow (traced cold at e89eebb)

```
tools/gex_snapshot.py  (SIDECAR, manual; invoked by NOTHING in CI)
  -> logs/gex_snapshot.json  (gitignored; present only on a machine that ran it)
     X no restore names it; not cached; no cuttingboard reader; no workflow ref
```
Public board rendered+published by two jobs (Pages deploys the `publish` branch):
`cuttingboard.yml` (morning, ~09:05 ET pre-open, blanket `git add -f logs/`
`:528`, render `:530-531`, `set -eo pipefail` `:382`); `hourly_alert.yml`
(~7-8 RTH slots `:11-18`, render `:148-152`, EXPLICIT stage list `:179-186` that
does NOT include `gex_snapshot.json`); `pages.yml` deploys `ui/` from `publish`
via `workflow_run` (`:10-16`). Network egress already exists in both jobs.

---

## 6. Governance: doctrine split (frozen) + reclassification

### 6.1 D-0 frozen
Doctrine-compliant split APPROVED; no override. Rationale (binding, verbatim):
doctrine **G3** ("a scheduled cadence may not be bundled into the producer PRD"),
**G4** (cadence "forbidden until ... a separately scoped consumer exists"),
**G8** ("provider research, producer construction, consumer construction,
cadence ... may not be compressed into one PRD"), and sec4.4 ("GEX-2 display-only
consumer ... GEX-3 optional cadence ... Each gate requires a separate approval
and separate PRD"). PRD_PROCESS has no mixed-class rule for a single multi-surface
PRD. So the product lands as sequenced single-class slices.

### 6.2 Classification (holds across the slices)
- **LANE: HIGH-RISK** for GEX-2 and GEX-3 (independently): renderer is a CONSUMER
  HIGH-RISK FILE (`PRD_PROCESS.md:460`); `.github/workflows/**` is an INFRA
  HIGH-RISK FILE (`:463`); each as payload triggers the Lane Downgrade
  Prohibition (`:501-504`); the payload/pointer carve-out covers only
  `PROJECT_STATE`/`PRD_REGISTRY` (`:515-517`). GEX-1b (producer) touches no
  HIGH-RISK FILE, so it is not forced HIGH-RISK by R11 (below).
- **MATERIAL: YES.** GOV-2 sec1 triggers that fire (`:18-29`): **T2** shared
  carrier (`:21`, GEX-3); **T4** adds a persisted schema surface with a
  presentation path (`:23-24`) - now FIRES because GEX-1b adds the freshness
  field that GEX-2 renders (r2 said T4 did not fire; r3 flips this); **T7**
  crosses delivery + dashboard (`:27-28`); **T3** the reset changes the FILES/LOC
  ceiling (`:22`). MICRO barred (`GOV-2:51-63`).

### 6.3 GEX-1b - the producer schema extension H-1 forces (SURFACED, not hidden)
- **Why a producer change is unavoidable (proven).** No existing emitted field
  gives independent session evidence: `fetched_at_utc` is our fetch clock;
  `feed_timestamp_utc`/`observation_trading_date` are the rejected edge-regen
  clock; `data_delay` is a constant. The only independent market-observation
  evidence in the Cboe response is the delayed last-trade time, which the
  producer currently DISCARDS (it reads only `{option,gamma,open_interest}`). The
  consumer cannot derive it without the producer emitting it, and raw-chain
  persistence is barred (doctrine G5). Therefore a producer schema extension is
  required - stated explicitly per the owner charge.
- **Minimal new field (recommended).** `underlying_last_trade_utc` = the Cboe
  response `data.last_trade_time` (a top-level sibling of `data.current_price`),
  parsed as ET-naive `"YYYY-MM-DDTHH:MM:SS"`, localized `America/New_York` ->
  UTC. Provenance: OBSERVED (provider-reported underlying last-trade/observation
  time). Typed-unavailable form if absent/unparseable: `underlying_last_trade_utc:
  null` with an explicit reason (fail-closed). This adds ONE top-level read; it
  does NOT touch `_classify_row`, GEX math, walls, dominant, or 0DTE.
- **Evidence (captured `_SPX` sample, 2026-08-17).** `data.last_trade_time`
  `"2026-08-17T14:27:32"` ET = `18:27:32Z`, versus edge-regen `timestamp`
  `18:42:35Z` and `Last-Modified` `18:42:38Z` - the last-trade clock sits ~15 min
  BEHIND the regeneration clock, proving it is the delayed MARKET-observation
  time, not the regeneration heartbeat. It is fresh during RTH and freezes
  overnight/weekend/holiday.
- **Alternative the owner named:** `MAX` over included contracts of per-contract
  `last_trade_time`. Semantics are VERIFIED (the contract's actual trade), but
  the captured `_SPX` option rows are stale (6-day and 4-month-old deep-OTM
  strikes), so a contract-MAX risks over-suppression unless liquid strikes are
  confirmed fresh. `data.last_trade_time` is the smaller, single-field,
  verified-fresh choice and is RECOMMENDED; the contract-MAX is the fallback.
- **Realizability item for GEX-1b (flagged, not papered over).** Confirm against
  a fresh live active-RTH `_SPX` capture that the chosen field advances during
  RTH and freezes outside it (the single 2026-08-17 sample shows it fresh once;
  GEX-1b implementation validates the RTH-advance property before Gate A). If it
  proves unreliable, fall back to contract-MAX or widen the bound.
- **Class/lane/material of GEX-1b.** SIDECAR (producer). LANE STANDARD (no
  HIGH-RISK file; MATERIAL bars MICRO but does not force HIGH-RISK). MATERIAL
  plausibly YES via T4 (a new schema surface with a planned presentation path);
  whether it runs a full GOV-2 packet cycle or rides as a PRD-306 patch under the
  MATERIAL sequence is a classification question for the review/Dustin to
  confirm. It is a PREREQUISITE to GEX-2 and is not folded into it.

---

## 7. Ephemeral same-run carrier (GEX-3; H-2 resolution)

**The artifact stays runner-local and UNCOMMITTED.** The hourly renderer consumes
`logs/gex_snapshot.json` in-run, before the artifact commit; the published
product is `ui/dashboard.html`/`ui/index.html`. So:

```
- name: Acquire GEX snapshot (fail-soft, non-blocking, ephemeral)
  continue-on-error: true
  run: |
    rm -f logs/gex_snapshot.json        # delete-before-fetch: no leftover can pass as current
    python tools/gex_snapshot.py         # exits nonzero if Cboe is down
# ... existing render step consumes the local artifact ...
# gex_snapshot.json is NOT added to the hourly explicit stage list (:179-186)
# -> never committed, never published; runner disappears, raw GEX disappears
```

- **No commit/stage/restore/cache/upload/download for GEX.** The hourly's staging
  list is EXPLICIT, so simply not listing `gex_snapshot.json` keeps it out of the
  artifact commit (unlike the morning pipeline's blanket `git add -f logs/`, which
  is another reason GEX is wired into the HOURLY only; the pipeline is DEFERRED,
  and is pre-open anyway - the card would suppress there).
- **Fail-soft without masking.** The GEX acquire is its own `continue-on-error`
  step; a Cboe outage fails that step only, the publish job proceeds, no GEX
  failure notification. Unrelated failures still abort the job.
- **Stale-leftover defense (two layers).** Workflow `rm -f` (a failed producer
  leaves no file); plus the loader run-recency gate on `fetched_at_utc` (sec9)
  makes "producer failed this run" != "some older file exists" - deterministic
  and unit-testable (sec23 K).
- **If anyone later argues the raw JSON must be committed:** the exact consumer/
  product requirement must be named; "so it reaches publish" is insufficient
  because the renderer consumes it before publish.

---

## 8. Freshness / session evidence table (r3)

| Field | Source | Independent of edge-regen? | Proves current-session market observation? |
|---|---|---|---|
| `fetched_at_utc` | producer clock `:345` | yes (our clock) | no - proves only WHEN WE FETCHED (run-recency) |
| `feed_timestamp_utc` | Cboe body `timestamp` | NO (it IS the edge-regen clock) | no - REJECTED (D-2) |
| `observation_trading_date` | ET date of feed ts `:283` | NO (derived from feed ts) | no - circular (H-1) |
| `data_delay` | constant `:47` | n/a | no (descriptive) |
| **`data.last_trade_time` (underlying)** | Cboe response, delayed | **YES - ~15 min behind edge-regen in the captured sample** | **yes - delayed market-observation time; freezes off-session** (NEW field, GEX-1b) |
| per-contract `last_trade_time` | Cboe rows (discarded) | yes | partial - actual trades, but sparse/stale for illiquid strikes |
| system `now` | load clock | yes (anchor) | no alone - the required anchor for both recency gates |

Two concepts kept distinct (charge sec7): ARTIFACT RECENCY (`fetched_at_utc`) and
MARKET-OBSERVATION RECENCY (`underlying_last_trade_utc`). The card claims "fresh
request, ~15m delayed" as a SOURCE DISCLOSURE, never an exact observation age.

---

## 9. Freshness / session state machine (GEX-2 loader; deterministic; injectable now)

`_load_gex_context(path, *, now) -> dict | None` in `dashboard_renderer.py`,
`now` tz-aware UTC (injected in tests). ANY failure -> `None` (card absent):

```
1. STRUCTURE     file exists; parseable JSON; dict.
2. IDENTITY      schema_version/source/underlying/units/spot.basis/
                 sign_convention/data_delay match the producer semantics (sec10).
3. DOMAINS       load-bearing numerics finite, non-bool, in-range (sec11).
4. PRESENCE      spot.value>0; gex_total finite; dominant strike non-null finite
                 + its gex finite.
5. RUN-RECENCY   0 <= (now - fetched_at_utc) <= FETCH_RECENCY_MAX
                 -- our fetch clock; defeats the stale last-good artifact.
6. SESSION       underlying_last_trade_utc present, parseable, AND
                 0 <= (now - underlying_last_trade_utc) <= SESSION_ACTIVITY_MAX
                 -- INDEPENDENT delayed market-observation recency (GEX-1b field);
                 absent/ambiguous/future -> FAIL CLOSED (suppress).
-> normalized display object, else None.
```

**Why this is honest and answers H-1:**
- Gate 6 rests on the delayed MARKET-observation clock (proven ~15 min behind the
  edge-regen clock, sec6.3), NOT on `feed_timestamp_utc` or `is_market_open` or
  `observation_trading_date` - all three are gone.
- Holiday/weekend/overnight are safe BY CONSTRUCTION: no market observation ->
  the last-trade time is hours/days old -> Gate 6 suppresses. No weekday logic,
  no holiday table.
- Early-session suppression is acceptable (owner): right at 09:30 ET the freshest
  delayed observation may still be ~15 min old; the card simply appears a little
  after open.
- Gates 5 and 6 are complementary: 5 proves the ARTIFACT is from this run; 6
  proves the MARKET DATA is current-session. Both fail closed.

**Tunable knobs (sec25):** `FETCH_RECENCY_MAX` ~20 min on `fetched_at_utc`
(D-2'); `SESSION_ACTIVITY_MAX` ~30 min on `underlying_last_trade_utc` (D-5) -
covers the ~15 min delay plus margin; both single named constants on TRUSTWORTHY
clocks, categorically unlike the rejected feed-clock threshold.

---

## 10. Artifact semantic-identity contract (E1-004)

The loader validates each meaning-bearing field against the exact producer
constant it stands for; a mismatch SUPPRESSES (never renders a false disclosure):
`schema_version`, `source` (`cboe_delayed_quotes`), `underlying` (`_SPX`),
`units`, `spot.basis` (SPX cash), `sign_convention` (drives the `*` footnote),
`data_delay` (drives "~15m delayed"). The hardcoded copy is LICENSED only by
these equality checks; if the artifact disagrees, the card suppresses. Each field
gets a discriminator mutation test (sec23 C). The GEX-1b `schema_version` bump (a
new field is a schema change) is part of the identity set - an older artifact
without `underlying_last_trade_utc` fails Gate 6 (fail-closed) and suppresses.

---

## 11. Loader normalization + exact field domains (E1-005)

Numbers: native int/float only; reject bool; reject numeric strings; finite only.

| Datum | Domain | Unavailable |
|---|---|---|
| `spot.value` | finite float > 0 | load-bearing -> card absent |
| `gex_total_1pct_usd` | finite float (sign kept) | load-bearing |
| `dominant_net_gamma.strike` / `.gex_1pct_usd` | finite > 0 / finite | null+`all_net_gamma_zero` -> card absent |
| `call_wall.strike` | finite > 0 | null+{`no_eligible_calls`,`no_nonzero_call_gex`} -> omit Call row |
| `put_wall.strike` | finite > 0 | null+{`no_eligible_puts`,`no_nonzero_put_gex`} -> omit Put row |
| `zero_dte.share` | finite in [0,1] | null+`zero_abs_gex_denominator` -> omit 0DTE row |
| `fetched_at_utc` | ISO-8601 tz-aware parseable | invalid -> card absent (Gate 5) |
| `underlying_last_trade_utc` | ISO-8601 parseable (GEX-1b) | null/invalid -> card absent (Gate 6, fail-closed) |
| `feed_timestamp_utc` | display-only; parseable | invalid -> card absent |

A malformed pseudo-unavailable state (strike non-null with a non-null reason;
unrecognized reason; `share` null with no recognized reason) is INVALID ->
suppress; never accepted as honest unavailability.

---

## 12. Typed-unavailable unions and reasons (E1-005)

Available sub-object: `strike` finite>0, `gex_1pct_usd` finite, `reason is None`.
Unavailable: `strike is None`, `gex_1pct_usd is None`, `reason` in the exact set.
Recognized reasons (verified `tests/test_gex_snapshot.py`): `all_net_gamma_zero`
(dominant); `no_eligible_calls`,`no_nonzero_call_gex` (call);
`no_eligible_puts`,`no_nonzero_put_gex` (put); `zero_abs_gex_denominator` (0DTE).
Disposition: dominant unavailable -> whole card absent; call/put/0DTE unavailable
-> that row omitted only. Unknown reason or contradictory combo -> INVALID.

---

## 13. Renderer purity + exception isolation (E1-006)

**Honest scope.** `render_dashboard_html` (`:2049-3194`) already performs legacy
conditional file I/O (`:2080` `_resolve_market_map`, `:2158` `_load_macro_snapshot`),
so "the renderer does zero I/O" is FALSE. The GEX claim is scoped narrowly: the
GEX render branch performs no I/O, no clock read, no tz conversion, no env, no
network, no loader call - the object is pre-resolved in `main()` and passed as one
kwarg, exactly like `alert-watchlist` (`if alert_candidates:` `:2593-2594`, no
else; loader `_load_contract_entry_context` `:3262`, main `:3385`).

Seam: loader `_load_gex_context` in `main()` (freshness/session/identity/domain +
ET display strings pre-formatted here - there is NO ET helper in the renderer,
only PT at `:328/:348`). Do NOT reuse `_load_json_optional` (`:935-941`, RAISES on
malformed); model on `_load_trend_structure_snapshot` (`:953-965`, never raises),
extended with identity/domain/finite/recency/session checks. One keyword-only
`gex_context: dict | None = None` threaded through `write_dashboard` and
`render_dashboard_html`; render is `if gex_context:` with no else.

Exception isolation: the whole loader body is guarded (absent/permission/race/
UnicodeDecodeError/JSONDecodeError/wrong-type/missing/non-finite/tz-db/any) ->
`None`. An invalid artifact must never escape as an exception that fails the
dashboard job. A NEW red isolation test is required - the existing boundary test
(`tests/test_dash_boundary.py:34-46`) fences only `"contract"`-named reads.

---

## 14. Product card contract

```
GEX
Net       -$56.3B*
Dominant   7640   -0.02%
Call       8000   +4.70%
Put        8000   +4.70%
0DTE       7.6%
14:27 ET . ~15m delayed

* signed under configured positioning assumption; positioning is not measured
```

Net = `gex_total/1e9`, 1-dp, explicit sign, `$`..`B`, trailing `*`. Strike without
trailing `.0` when integer-valued, then signed 2-dp `((strike/spot)-1)*100` (D-1;
`+0.00%` for zero). 0DTE = `share*100`, 1-dp, `%`. The ET time label is the "as
of" market-observation time (`underlying_last_trade_utc` -> ET, pre-formatted in
the loader) beside the static `~15m delayed` disclosure - an "as of" label, never
an age claim. Sign-assumption footnote always present. Display-clock choice
(observation vs feed vs fetch) is D-4, minor. **CUT (asserted absent by tests):**
gross wall dollars; raw dominant magnitude; full-precision net; top-strike table;
expiration/coverage/provenance dumps; source URL; history; gamma flip; max pain;
vanna; charm; flow/CVD; and ALL interpretive labels (AT SPOT, MAGNET, PIN,
SUPPORT, RESISTANCE, SHORT/LONG-GAMMA REGIME, "tracks spot", "dealers are short
gamma", regime badges, predictive language).

---

## 15. Failure matrix

| Layer | Condition | Behavior |
|---|---|---|
| Producer/carrier | Cboe down / nonzero / malformed / write fail | GEX step fails soft; no artifact; `rm -f` leaves none; publish proceeds; no GEX notification |
| Loader | absent/permission/race/UnicodeDecode/malformed/wrong-shape | None -> card absent |
| Loader | wrong identity (sec10) | None -> card absent |
| Loader | bad domain (bool/str/NaN/Inf/spot<=0/strike<=0/share out of [0,1]) | None -> card absent |
| Loader | run-recency fail (stale artifact) | None -> card absent (Gate 5) |
| Loader | session fail: `underlying_last_trade_utc` absent/stale/future | None -> card absent (Gate 6, fail-closed) |
| Loader | dominant unavailable | None -> card absent |
| Loader | call/put/0DTE individually unavailable (else valid) | that row omitted; card renders |
| Render | `gex_context is None` | no GEX output; baseline byte-identical (sec17) |
| Publish | GEX acquisition fails | dashboard renders + publishes; readiness/decisions unchanged |
| Publish | unrelated render error | still fails loudly (GEX isolation does not mask it) |

---

## 16. Behavioral non-coupling proof (traced cold at e89eebb)

- `assert_valid_payload` (`payload.py:217-289`) checks only MISSING required keys,
  does not reject extras; GEX never touches payload.
- `validate_coherent_publish` (`dashboard_renderer.py:563-627`) compares a
  hardcoded generation_id triple; GEX is not one.
- Readiness (`check_readiness.py`) asserts a fixed 3-marker allowlist (`:39-43`)
  as a required-presence subset; the coupling to AVOID is adding a GEX marker -
  GEX must not.
- Notification formatters dispatch on `AlertEvent` types; audit writers never
  enumerate cards; no decision module reads the artifact (rg gex cuttingboard/
  -> none); no generic all-cards loop exists.

Binding: GEX must not become a required payload section, contract field,
coherent-publish requirement, readiness marker, notification field, or audit
requirement. Any such need -> STOP (sec26).

---

## 17. Baseline neutrality (E1-007) and persistence (H-2)

**Baseline neutrality.** With `gex_context is None` the dashboard must be
byte-identical to the pre-GEX baseline. No golden-HTML oracle exists in-repo
today, so GEX-2 introduces a committed pre-GEX golden characterization (full-HTML
fixture or deterministic hash) and asserts `render_dashboard_html(..., gex_context=
None) == golden` (sec23 J). Comparing only "None vs default None" is insufficient
(shared accidental CSS/whitespace); the oracle is an independent pre-feature
baseline. Any unavoidable weakening is stated, never silent.

**Persistence: NONE (r3).** The raw artifact is runner-local and UNCOMMITTED (H-2)
- not staged, restored, cached, uploaded, or published. No GitHub artifact
persistence. The only durable output is the rendered HTML card. GEX-1b adds one
field to the artifact SCHEMA but the artifact itself is still not persisted to
`publish`. Doctrine G5 (one writer; additive path) honored.

---

## 18. Preview / developer workflow

Deterministic tests use synthetic fixtures only (`gx.run(now=,fetch_fn=,
artifact_path=)`), injected `now` into the loader. `dashboard_preview.yml` stays
GEX-absent (no live Cboe fetch); `scripts/preview_fixtures.py` remains baseline/
no-GEX by construction. Local live preview reuses the manual path (run the
producer by hand, render via `scripts/preview_dashboard.sh` to a `reports/output/`
scratch path; never overwrite committed `ui/`). An opt-in synthetic GEX fixture
MAY be added for deterministic layout review (author discretion, GEX-2 test cone).

---

## 19. Exhaustive consumer / call-site inventory (personally re-verified)

Machine consumers of `logs/gex_snapshot.json` today: NONE (`rg -i "gex_snapshot|
gex_total|dominant_net_gamma|call_wall" cuttingboard/` rc=1; `rg -i gex .github/`
rc=1; `rg -i gex dashboard_renderer.py` rc=1). Renderer production call sites:
`render_dashboard_html` at `:3236` + `scripts/preview_fixtures.py:53`;
`write_dashboard` at `:3415`. Family-B full-suppress precedent: `alert-watchlist`
(`:2593`). Producer per-contract read set is `{option,gamma,open_interest}` only
(`:191`) - GEX-1b adds an underlying-block read, not a per-contract one.

---

## 20. FILES cone (rebuilt; three slices)

Legend: `[P]` payload, `[T]` test, `[D]` doc, `[L]` lifecycle.

### GEX-1b (SIDECAR, producer freshness field) - PREREQUISITE
```
[P] tools/gex_snapshot.py            emit underlying_last_trade_utc + provenance + typed-unavailable
[T] tests/test_gex_snapshot.py       parse/localize/aggregate + fail-closed mutations
[D] docs/SCHEMA_MAP.md               new canonical field (now REQUIRED - a schema surface is added)
[D] docs/artifact_flow_map.md        add the new field to the artifact description
[L] docs/prd_history/PRD-*.md, PRD_REGISTRY.md, prd_index.json, PROJECT_STATE.md
```

### GEX-2 (CONSUMER, display card)
```
[P] cuttingboard/delivery/dashboard_renderer.py   loader (identity/domain/recency/session) + kwarg + GEX render branch
[T] tests/test_dash_gex.py                         consumer/mutation suite + golden baseline
[T] tests/test_check_readiness.py                  independent literal marker-set test (E1-007)
[D] docs/artifact_flow_map.md                      "machine consumers: none" -> the renderer
[D] docs/CALL_SITE_MAP.md                          new loader read-site (E1-008)
[D] docs/plans/decision-support-workplan-v0.1.md   GEX-2 row
[D] docs/PROJECT_STATE.md                          consumer line
[D] tools/gex_snapshot.py                          docstring: "no machine consumer" comment corrected
[L] docs/prd_history/PRD-*.md, PRD_REGISTRY.md, prd_index.json
```

### GEX-3 (INFRA, ephemeral carrier)
```
[P] .github/workflows/hourly_alert.yml             GEX acquire step (continue-on-error, rm -f); NO stage-list edit (H-2)
[T] tests/test_ci_artifact_hygiene.py              carrier text-slice: step present, ordered before render, fail-soft, AND gex_snapshot.json NOT staged
[T] tests/test_dash_gex_carrier.py (or extend)     python fail-soft behavior test
[D] docs/artifact_flow_map.md                      "no cadence, cron" -> the hourly carrier
[D] docs/plans/decision-support-workplan-v0.1.md   GEX-3 row
[D] docs/PROJECT_STATE.md                          cadence line
[D] tools/gex_snapshot.py                          docstring: "no cadence, no workflow" comment corrected
[L] docs/prd_history/PRD-*.md, PRD_REGISTRY.md, prd_index.json
```

`cuttingboard.yml` DEFERRED (pre-open; blanket `git add -f logs/` would also
commit the artifact, contradicting H-2 - a reason to keep GEX out of the pipeline
for v1). NOT TOUCHED (boundary expansion -> STOP): producer GEX math / `_classify_row`,
`payload.py`, `check_readiness.py` marker constant, `runtime/`, `qualification/`,
`regime/`, `execution/`, `notifications/`, `pages.yml`, `dashboard_preview.yml`,
`ui/*` as committed source, `logs/gex_snapshot.json` as committed content.

---

## 21. LOC / dependency estimate (honest; per slice)

Range now; binding GATE A CEILING is Dustin's, at top-of-range plus margin
(`PRD_PROCESS.md:684-687`); validation/identity/freshness/typed-unavailable count
as first-class surface (`:672-680`); test LOC excluded from the net metric.

- **GEX-1b production** (`gex_snapshot.py`): parse `data.last_trade_time` +
  localize + typed-unavailable + provenance ~15-30 net; ceiling **45**.
- **GEX-2 production** (`dashboard_renderer.py`): loader (structure+identity+
  domains+2 recency gates+ET pre-format) ~80-120; kwarg ~6; render branch ~35-60;
  docstring comment ~2. Expected **~120-190**; ceiling **220**.
- **GEX-3 production** (`hourly_alert.yml` + docstring): acquire step ~8-15;
  docstring comment ~2. Expected **~10-18**; ceiling **30**.
- **Tests**: GEX-1b ~60-120; GEX-2 ~280-420; GEX-3 ~50-90 (all outside the net).
- **0 new dependencies.** Stdlib `datetime`/`zoneinfo` + existing
  `cuttingboard.time_utils` for tz helpers on the reader side; producer stays
  stdlib-only. No market-calendar library (the independent last-trade recency
  avoids it entirely).

---

## 22. Documentation / lifecycle consequences (exact lines; per slice)

- GEX-1b: add `underlying_last_trade_utc` to `docs/SCHEMA_MAP.md` (convention
  `:3-4`, now REQUIRED - a schema surface is introduced) and to the
  `docs/artifact_flow_map.md` GEX artifact description.
- GEX-2: `artifact_flow_map.md:169` "machine consumers: none" -> the renderer;
  ADD the loader read-site to `docs/CALL_SITE_MAP.md` (E1-008); producer docstring
  `:6-8` "no machine consumer" corrected; `PROJECT_STATE.md:32`/workplan GEX-2 row.
- GEX-3: `artifact_flow_map.md:174-175` "no cadence, cron, or scheduled publish"
  -> the hourly carrier; producer docstring "no cadence, no workflow" corrected;
  workplan GEX-3 cadence row. R11 import-isolation (`:8`) UNAFFECTED (the renderer
  reads the JSON, does not import the module). Do NOT clean unrelated North Star /
  Polygon doc debt in this work.

---

## 23. Test / mutation matrix (setup -> mutation -> which test turns red)

Synthetic artifacts only; no network; injected `now`.

| # | Test | Setup -> mutation -> expected | Bad impl caught |
|---|---|---|---|
| A | carrier fail-soft | producer step fails -> dashboard still publishes, no card, no GEX notification | a `set -e` naive call that aborts publish |
| B | valid current-observation | fresh artifact, recent `fetched_at_utc` + `underlying_last_trade_utc` -> card renders | render path dropped |
| C | identity discriminator | mutate each identity field -> suppressed | hardcoded disclosures accepting foreign JSON |
| D | domain guards | bool/str/NaN/Inf/spot<=0/strike<=0/share<0/share>1 -> suppressed (each) | `float()` coercion; missing isfinite |
| E | typed unavailable | each recognized reason (call/put/0DTE) -> that row omitted, card renders | over-broad suppression / unknown reason accepted |
| F | dominant unavailable | `all_net_gamma_zero` -> whole card absent | treating dominant as optional |
| G | GEX-branch purity | monkeypatch `open`+`_utcnow`; render valid `gex_context` -> neither called | in-render file/clock read |
| H | run-recency (Gate 5) | old `fetched_at_utc`, injected `now` -> suppressed | no run-recency gate |
| I | session recency (Gate 6, H-1) | `underlying_last_trade_utc` hours old (holiday/overnight) -> suppressed; absent -> suppressed; fresh -> renders | reliance on feed ts / is_market_open; not fail-closed |
| J | baseline neutrality | `gex_context=None` render == committed pre-GEX golden | stray CSS/whitespace/empty shell in None path |
| K | stale last-good leak (H-2) | old artifact + injected `now` beyond recency -> suppressed; AND carrier text-slice asserts `rm -f` precedes producer AND gex_snapshot.json NOT staged | a leftover/committed file rendering as current |
| L | readiness independence | literal `assert REQUIRED_HTML_MARKERS == (...3 markers...)` | a mutation ADDING a GEX marker |
| M | forbidden vocabulary | assert none of MAGNET/PIN/SUPPORT/RESISTANCE/SHORT-GAMMA/LONG-GAMMA/"tracks spot"/"dealers are short gamma" in the GEX section | interpretive copy leaking in |
| N | CUT magnitudes | raw wall/dominant dollars, coverage/provenance dumps absent | leaking diagnostics |
| O | non-coupling | payload/coherence/readiness pass identically with and without the card | GEX as a required dependency |
| P | GEX-1b producer | `data.last_trade_time` parsed/localized to `underlying_last_trade_utc`; absent -> typed-unavailable (fail-closed); math/walls/dominant/0DTE unchanged | reading the field wrong tz; or perturbing GEX math |

Determinism: identical inputs -> identical output; `now` injected into the loader;
producer `now`/`fetch_fn` injected.

---

## 24. CUT / forbidden interpretations (binding)

Deferred, NOT in v1: GEX history; what-changed; persistence DB; gamma flip; vanna;
charm; max pain; live flow; CVD; OPRA; heatmap; SPY duplicate; second provider;
decision coupling; thresholds; parameter tuning; ML; morning-pipeline wiring;
after-close/prior-session card; per-contract-MAX evidence (fallback only);
committing the raw artifact. Forbidden vocabulary is enumerated in sec14 and
test-bound (sec23 M/N). GEX remains ONE removable context card that informs the
board and never authorizes the trade.

---

## 25. Residual owner decisions (isolated; each with a recommendation)

- **D-0 - FROZEN:** doctrine-compliant split, no override. Sequence GEX-1b ->
  GEX-2 -> GEX-3.
- **D-1 - FROZEN:** presentation distance math permitted.
- **D-2 - FROZEN:** feed_timestamp freshness rejected.
- **D-3 - Session scope.** RECOMMEND intraday-only, now backed by INDEPENDENT
  market-observation recency (sec9), not the circular r2 gate. Options B
  (after-close labeled) / C (prior-session) remain deferred and would require
  pipeline wiring + a different label.
- **D-4 - Display clock.** RECOMMEND the "as of" market-observation time
  (`underlying_last_trade_utc` -> ET); may stay open (does not affect the gate).
- **D-5 - `SESSION_ACTIVITY_MAX`.** RECOMMEND ~30 min on `underlying_last_trade_utc`
  (covers the ~15 min delay + margin); single tunable constant. **D-2' -
  `FETCH_RECENCY_MAX`** ~20 min on `fetched_at_utc`.
- **GEX-1b evidence item (not an owner decision, a build gate):** confirm the
  underlying last-trade field advances during active RTH and freezes off-session
  against a fresh live capture before GEX-1b Gate A; contract-MAX is the fallback.

---

## 26. Explicit implementation stop conditions

STOP and return to HELM/Dustin if, at implementation time:
1. the card requires a producer GEX MATH change or a `_classify_row` change
   (the GEX-1b freshness field reads the underlying block ONLY; anything beyond
   that is a boundary expansion);
2. implementation requires touching payload schema, `assert_valid_payload`,
   `validate_coherent_publish`, or adding a `REQUIRED_HTML_MARKERS` entry;
3. a production file beyond the chosen slice's FILES cone is required (amend PRD +
   packet, fresh-context review of the exact amended revision, amended Gate A -
   GOV-2 sec5);
4. the carrier cannot be made fail-soft without masking unrelated failures, or the
   artifact cannot be kept ephemeral (H-2);
5. the GEX-1b realizability item fails (the underlying last-trade field is not a
   reliable current-session signal) - re-open the freshness evidence question;
6. scope expands to a second reader, decision coupling, pipeline wiring, or a new
   schedule - re-run GOV-2 sec1 classification.

---

## 27. Fresh Codex EVENT-1 review handoff block

- **Subject:** THIS r3 head (reported on push), read against the cited repository
  surfaces - NOT a review of prior review prose (GOV-1).
- **Falsification targets (highest leverage first):**
  1. Is the freshness gate (sec9) genuinely INDEPENDENT and holiday/weekend-safe -
     i.e. is `data.last_trade_time` provably the delayed market-observation clock
     (sec6.3 evidence) and does the fail-closed Gate 6 reject prior-session data?
  2. Is the GEX-1b producer schema extension the minimal necessary change, and is
     it correctly surfaced as a separate SIDECAR prerequisite (not hidden in
     GEX-2)? Is the RTH-advance realizability caveat handled honestly?
  3. Is the artifact genuinely ephemeral (H-2) - never staged/committed - and does
     the stale-leftover defense (rm -f + Gate 5) hold?
  4. Does the doctrine split (sec6.1) correctly partition CONSUMER/INFRA/SIDECAR,
     and are the identity/domain/typed-unavailable/purity contracts complete?
  5. Does the test matrix (sec23) give each load-bearing guard an isolating
     mutation, including Gate 6, baseline byte-identity, readiness independence,
     and the not-staged assertion?
- **Author has NOT commissioned Codex.** HELM commissions the fresh review.

---

## 28. Author self-verification (r3)

- Repo/branch/SHA, PR #261 shape, r1/r2 heads, dirty state: verified (sec1).
- Provider evidence read first-hand: `data.last_trade_time` `2026-08-17T14:27:32`
  ET vs edge-regen `18:42:35Z`/`Last-Modified 18:42:38Z` -> the last-trade clock
  is ~15 min behind regeneration (independent market clock). Per-contract rows in
  the `_SPX` sample are stale (deep-OTM). PASS.
- Producer: `_classify_row` reads only `{option,gamma,open_interest}` (`:191`);
  `data.current_price` read in `_validate_top_level` (a sibling of the target
  `data.last_trade_time`); GEX math untouched by the freshness field. PASS.
- Doctrine G3/G4/G8 + sec4.4 and classification citations: verified verbatim. PASS.
- Decisive GEX-absence sweeps re-run by the main agent (renderer / `cuttingboard/`
  / `.github/`, all rc=1). PASS.
- No production/test/workflow code changed by this packet; only the packet doc.
  `git diff --check` clean (reported on push). PASS.

Pre-existing repo debt observed, NOT absorbed (out of scope): three
`PRD-301.*.confirmation.*.md` files lack `PRD_REGISTRY.md` rows - unrelated to GEX.

---

## 29. Downstream sequence (informative; no authority created here)

Rebuilt packet (this) -> fresh Codex EVENT-1 -> one correction -> Codex
exact-corrected-head confirmation (GOV-2 sec7) -> Dustin design-direction ruling
-> Stage-0 GEX-1b (SIDECAR) -> review -> Gate A -> GEX-2 (CONSUMER) -> review ->
Gate A -> GEX-3 (INFRA) -> review -> Gate A. Each slice: implementation review +
PRD-242 second-model disposition -> Dustin merge.

**This packet authorizes none of the above. It is design only.**
