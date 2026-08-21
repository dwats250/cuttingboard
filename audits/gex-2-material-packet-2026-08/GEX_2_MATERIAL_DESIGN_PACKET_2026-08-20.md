# GEX-2 - Baseline-Neutral GEX Context Card: MATERIAL design packet

```
STATUS: PROVISIONAL MATERIAL PACKET - 2026-08-20 - DESIGN ONLY
AUTHORIZES NO IMPLEMENTATION, NO PRD NUMBER (PRD-308 UNALLOCATED), NO GATE A
DERIVED AT main SHA: e89eebb64997e8857827a9f294d228538b30bdce
GOV-2 PACKET-REVIEW CYCLE: NOT YET STARTED (awaiting Codex Event-1 packet
  review; the packet is NOT review-clean and carries NO downstream authority
  until Event-1 review + Event-2 exact-corrected-head confirmation pass)
PRODUCT RULING IN FORCE: "GEX-2 PRODUCT DIRECTION: GO TO MATERIAL DESIGN"
  (owner usefulness ruling, 2026-08-20). This is NOT the GOV-2 design-direction
  ruling, which occurs only after this packet is review-clean.
```

> This is the upstream MATERIAL design packet GOV-2 requires before any GEX-2
> PRD, decision entry establishing design direction, or implementation
> authority. It defines the smallest baseline-neutral GEX context card so
> Dustin can issue a design-direction ruling from a review-clean packet.
> Nothing here is buildable authority. Sequence position:
> **this provisional packet (now)** -> Event-1 Codex packet review ->
> one consolidated correction -> Event-2 exact-corrected-head confirmation
> (GOV-2 SS7) -> Dustin's design-direction ruling -> Stage-0 PRD-308 ->
> fresh-context PRD review -> Gate A.

---

## SS0 - Intake classification (GOV-2 SS1)

**CLASS: CONSUMER. LANE: HIGH-RISK. MATERIAL: YES.**

### Why CONSUMER

Read-only consumer of a finalized artifact rendered to the dashboard
(`docs/PRD_PROCESS.md:418` - "CONSUMER | Read-only consumers of finalized
artifacts (dashboard, notifications)"). GEX-2 reads `logs/gex_snapshot.json`
and renders a display card. It writes no new persisted surface and computes no
GEX structural value.

### Why HIGH-RISK (locked; no downgrade available)

For CLASS CONSUMER, `docs/PRD_PROCESS.md:460` lists
`cuttingboard/delivery/dashboard_renderer.py` as a HIGH-RISK FILE. GEX-2
necessarily changes that renderer **as payload** (the PRD exists to add the
card to it). Under the Lane Downgrade Prohibition (`docs/PRD_PROCESS.md:499-506`
and the payload-vs-pointer rule at `:508-513`), a PRD whose `FILES` names a
HIGH-RISK FILES entry for its CLASS as payload MUST declare `LANE: HIGH-RISK`,
regardless of diff size or read-only intent. The pointer carve-out applies only
to `docs/PROJECT_STATE.md` and `docs/PRD_REGISTRY.md` (`:515-517`) -
`dashboard_renderer.py` has no bookkeeping form. **Verified against current
canonical governance: HIGH-RISK is mandatory and cannot be downgraded to
STANDARD or MICRO.** The Cosmetic Carve-Out (`docs/PRD_PROCESS.md` ~:617) does
not apply: GEX-2 adds a functional data-reading card, not a copy/CSS/layout or
docstring-only edit.

### Why MATERIAL - the single operative trigger

**GOV-2 SS1 trigger 2** (`docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:22`):
"it selects an implementation seam or carrier shared across pipeline layers."

GEX-2 establishes the **first machine reader** of `logs/gex_snapshot.json`,
turning a human-inspection-only artifact into a carrier shared across two
pipeline layers:

```
tools/gex_snapshot.py        (producer layer - tools/, PRD-306, untouched)
        v  writes
logs/gex_snapshot.json       (shared carrier - now cross-layer)
        v  read by
cuttingboard/delivery/dashboard_renderer.py   (delivery/dashboard layer, NEW reader)
```

This shared cross-layer carrier is sufficient for MATERIAL on its own. Per the
session charter, no additional trigger is manufactured. (Trigger 4 - "persisted
schema surface that has more than one reader" - is corroborative but not relied
upon; trigger 2 is the operative classification.)

**Reclassification watch (GOV-2 SS1, `:36-43`):** if downstream scope expands to
add cadence, a scheduled publish of the producer, a second reader, a payload
section, or any decision-path coupling, stop and re-run classification before
resuming.

### Lane consequence

MICRO ineligible (MATERIAL bar, GOV-2 SS1 `:51-63`, independently of the
HIGH-RISK trigger). Expected downstream PRD header: `CLASS: CONSUMER` (default
Tier T2), `LANE: HIGH-RISK`. As a HIGH-RISK CONSUMER PRD it carries the PRD-242
second-model disposition obligation (a committed second-model artifact OR the
exact `SECOND-MODEL:` waiver line).

---

## SS1 - Product ruling and binding principle

### Product finding (owner, 2026-08-20)

Two successful Cboe observations, each admitting 30,282 / 30,282 contracts with
zero exclusions:

| | Obs 1 (19:21:37Z) | Obs 2 (23:47:48Z) |
|---|---|---|
| spot | 7653.76 | 7641.16 |
| net GEX | -40.071B | -56.3B |
| dominant strike | 7650 (~-0.05%) | 7640 (~-0.02%) |
| call wall | 8000 (+29.526B gross) | 8000 (+27.9B gross) |
| put wall | 8000 (-25.663B gross) | 8000 (-24.1B gross) |
| 0DTE share | 6.36% | 7.64% |

The dominant net-gamma strike stayed extremely close to spot and moved
7650 -> 7640 while spot moved 7653.76 -> 7641.16 over ~4.5 hours. **This
justifies a cheap, fully-removable context card.**

### Claims explicitly FORBIDDEN from GEX-2 v1

Not licensed by two observations, and barred from the card and its copy:
dominant gamma "tracks" spot statistically; gamma magnetism; price pinning;
deterministic dealer hedging; predictive support/resistance; an "AT SPOT"
threshold or regime. The numbers are displayed; no interpretation is asserted.

### Binding product principle

**GEX informs the board. GEX never authorizes the trade.** GEX-2 MUST NOT
affect any of: TRADE / NO TRADE / HALT, candidate permission, qualification,
grading, ranking, sizing, regime, kill switch, execution, alert permission,
payload coherence, readiness, or run success/failure. It is removable display
context. (Proof: SS8.)

---

## SS2 - Producer / artifact contract (reverified at e89eebb; producer UNTOUCHED)

Source of truth: `tools/gex_snapshot.py` `_build_artifact` return
(`tools/gex_snapshot.py:339-360`), serialized `json.dumps(..., indent=2,
sort_keys=True, allow_nan=False)` (`:369`). The producer is **not modified by
GEX-2**. Confirmed relevant top-level keys and shapes:

| Artifact key | Type | Producer line | Card use |
|---|---|---|---|
| `feed_timestamp_utc` | ISO-8601 str (UTC) | `:346` | freshness clock + ET display |
| `data_delay` | str (descriptive, non-numeric) | `:347` | delayed-posture disclosure |
| `spot` -> `value` | float (>0, finite) | `:348` | distance denominator |
| `sign_convention` | str constant | `:350` | honesty-token source |
| `gex_total_1pct_usd` | float (signed) | `:353` | Net GEX (billions) |
| `call_wall` -> {`strike`,`gex_1pct_usd`,`reason`} | strike float\|null | `:354` | Call row (strike + distance) |
| `put_wall` -> {`strike`,`gex_1pct_usd`,`reason`} | strike float\|null | `:355` | Put row (strike + distance) |
| `dominant_net_gamma` -> {`strike`,`gex_1pct_usd`,`reason`} | strike float\|null | `:356` | Dominant row (strike + distance) |
| `zero_dte` -> `share` | float **fraction** 0..1 \| null | `:279-287` | 0DTE row (share*100) |

Load-bearing facts for the reader design:

1. **`zero_dte.share` is a FRACTION**, not a percent (producer computes
   `numerator / denominator`, `:278`; test asserts `0.625`,
   `tests/test_gex_snapshot.py:144`). The card multiplies by 100.
2. **Each structural sub-object can be individually unavailable while the
   artifact is otherwise valid**: `_unavailable(reason)` emits
   `{"strike": null, "gex_1pct_usd": null, "reason": <str>}`
   (`tools/gex_snapshot.py:222-223`). Reasons: `no_eligible_calls`,
   `no_nonzero_call_gex`, `no_eligible_puts`, `no_nonzero_put_gex`,
   `all_net_gamma_zero`; `zero_dte.share` null with `zero_abs_gex_denominator`.
   The KEYS are always present; only the values go null.
3. **`feed_timestamp_utc` is the correct freshness basis** (the observed feed
   time; malformed/missing FAILS LOUD in the producer, never a producer-clock
   fallback, `:144-153`). `data_delay` is a descriptive constant string
   ("~15 min delayed (REPORTED; ...)", `:47`), not a machine-parseable delay -
   confirming it is disclosure, not the stale clock.
4. **No committed sample.** `logs/` is gitignored (`.gitignore:49`);
   `logs/gex_snapshot.json` is not tracked and does not exist in-tree. Tests use
   synthetic artifacts only.
5. **PRD-306 R11 isolation invariant** (`tools/gex_snapshot.py:10-13`;
   `docs/artifact_flow_map.md:160-161`): "no `cuttingboard` module imports it."
   The renderer IS a `cuttingboard` module, so **the reader MUST NOT import
   `tools/gex_snapshot.py`.** It consumes the JSON purely and defines its own
   minimal read-side display contract. This keeps the producer genuinely
   untouched and preserves the isolation invariant.

**Boundary rule:** if the card is found to require ANY producer modification
(a new emitted field, a distance value the producer does not currently emit,
a schema change), that is a boundary expansion -> STOP and report (SS14).

---

## SS3 - Consumer inventory and reader seam (exhaustive, traced cold at e89eebb)

### Current machine consumers of `logs/gex_snapshot.json`: NONE

Verified by the main agent re-running the decisive sweep:
`rg "gex_snapshot|gex_total|dominant_net_gamma|call_wall" cuttingboard/`
-> zero hits (exit 1). Every repo reference is the producer, its tests, or
prose (docs/audits). **GEX-2 is provably the first machine reader** - which is
the MATERIAL trigger itself.

### Renderer call-site inventory (the seam a new kwarg touches)

`render_dashboard_html` is defined at
`cuttingboard/delivery/dashboard_renderer.py:2049-2071` (keyword-only optional
kwargs). `write_dashboard` at `:3197-3259`. `main()` at ~`:3353-3433`.

Production call sites of `render_dashboard_html`:
- `dashboard_renderer.py:3236` (inside `write_dashboard`, forwards all kwargs)
- `scripts/preview_fixtures.py:53` (passes `**case.render_kwargs`; needs no
  change unless a fixture case exercises GEX)

Production call site of `write_dashboard`:
- `dashboard_renderer.py:3415` (inside `main()`)

Test call sites: ~400 across `tests/test_dash*.py`,
`tests/test_dashboard_renderer.py`, and others - **all use keyword args**, so a
new `gex_context: dict | None = None` kwarg defaulting to `None` is
source-compatible with every existing call. Only tests that intend to exercise
the GEX card change.

### Established optional-card precedent (Family B - the pattern to match)

The newer optional cards load in `main()` and pass a pre-resolved object as a
kwarg into a renderer that only formats-or-suppresses:

| Card | Loader (in `main()`) | kwarg |
|---|---|---|
| Trend Structure (PRD-112) | `_load_trend_structure_snapshot` (`:953-965`) | `trend_structure_snapshot=` (`:3391-3393`) |
| Scoreboard / regime history | `_load_regime_history` (`:3308-3329`) | `regime_history=` (`:3396`) |
| Red Folder | `_resolve_red_folder_view` (`:3332-3350`) | `red_folder=` (`:3397`) |
| Pipeline run / LIVE STATE | `_load_json_optional` (`:935-941`) | `pipeline_run=` (`:3374`) |

The older cards (market_map, macro) read the file **inside** the renderer;
`tests/test_dash_boundary.py:33-46` now actively fences off new renderer file
reads. GEX-2 must follow Family B, not the older pattern.

### DECISION: reader seam (recommended)

1. **Loader** `_load_gex_context(path, *, now) -> dict | None`, a private
   function in `dashboard_renderer.py`, modeled on `_load_trend_structure_snapshot`
   (`:953-965`) - the fullest suppressor (absent / malformed JSON / IO error /
   wrong type / missing load-bearing field / non-finite value / **stale** all
   collapse to `None`). **Do NOT reuse `_load_json_optional`** - it raises
   `RuntimeError` on malformed JSON (`:935-941`), which would violate
   baseline-neutrality (malformed must yield card-absent, never a crash).
2. **Freshness lives in the loader**, with an injectable timezone-aware `now`
   (default `datetime.now(timezone.utc)` in `main()`, injected in tests). This
   keeps the renderer deterministic - the determinism tests
   (`tests/test_dash_run_history.py:89,116`) compare two renders for equality,
   so no wall-clock logic may live in the renderer.
3. **`main()`** loads the artifact from `logs_dir` and passes the resolved
   object (or `None`) into `write_dashboard`, mirroring `:3391-3397`.
4. **Kwarg threading**: a new `gex_context: dict | None = None` keyword-only
   kwarg on `write_dashboard` (`:3197-3218`, forwarded at `:3236-3257`) and on
   `render_dashboard_html` (`:2049-2071`).
5. **Renderer** paints a "GEX context" block using the Scoreboard/Red-Folder
   suppression idiom - `if gex_context: <render> ` with **no else branch that
   emits any GEX placeholder** (SS6). The renderer formats a clean object; it
   never reads disk, never checks the clock, never derives a GEX structural
   value.

All production edits land in **one file**: `dashboard_renderer.py`.

---

## SS4 - Exact data-field contract (fields the reader consumes)

The loader validates and returns ONLY the display fields below; the card
renders ONLY these. Everything else in the artifact is ignored.

**LOAD-BEARING (any absent / non-finite / null -> whole card suppressed):**
- `feed_timestamp_utc`: present, ISO-8601 parseable, and fresh (SS7).
- `spot.value`: finite float, > 0.
- `gex_total_1pct_usd`: finite float (sign preserved).
- `dominant_net_gamma.strike`: non-null finite float; and
  `dominant_net_gamma.gex_1pct_usd`: finite float. (Dominant is the product's
  central reading - "dominant strike vs spot" - so its unavailability suppresses
  the entire card; see SS6, D-resolution.)

**OPTIONAL (individually unavailable -> that row omitted, card still renders):**
- `call_wall.strike` / `.gex_1pct_usd` (omit Call row if null).
- `put_wall.strike` / `.gex_1pct_usd` (omit Put row if null).
- `zero_dte.share` (omit 0DTE row if null).

**DISCLOSURE (rendered unconditionally whenever the card renders):**
- Delayed-posture token ("~15m delayed").
- Sign-assumption honesty token (asterisk + footnote), sourced from the fact of
  `sign_convention` being a configured/inferred constant (never measured).

---

## SS5 - Display contract and vocabulary

Owner target card:

```
GEX
Net       -$56.3B*
Dominant   7640   -0.02%
Call       8000   +4.70%
Put        8000   +4.70%
0DTE       7.6%
19:47 ET . ~15m delayed

* signed under configured positioning assumption;
  positioning is not measured
```

### Exact formatting rules (deterministic, mutation-testable)

1. **Net GEX**: `gex_total_1pct_usd / 1e9`, one decimal, explicit sign, `$`
   prefix, `B` suffix, trailing `*`. Positive shows `+$29.5B*`, negative shows
   `-$56.3B*`. (Sign is meaningful; always shown.)
2. **Dominant / Call / Put strike**: strike rendered without trailing `.0` when
   integer-valued (e.g. `7640`), else as the artifact float; followed by signed
   distance percentage (rule 9).
3. **0DTE**: `zero_dte.share * 100`, one decimal, `%` suffix (`7.6%`).
4. **Feed timestamp**: `feed_timestamp_utc` converted to ET
   (`ZoneInfo("America/New_York")`), 24-hour `HH:MM ET` (`19:47 ET`).
5. **Delayed posture**: static `~15m delayed`, always present on a rendered card.
6. **Sign-assumption honesty**: `*` on Net GEX plus the footnote
   `* signed under configured positioning assumption; positioning is not measured`,
   always present on a rendered card (SS8 copy).

### Distance math (rule 9 - presentation-only)

```
distance_pct = ((strike / spot) - 1) * 100
```
- Signed, two decimals, explicit `+`/`-` sign; `+0.00%` for zero.
- `spot` = `spot.value` (guaranteed finite, > 0 by the load-bearing gate);
  `strike` = the sub-object's finite strike.
- **Arithmetic verification against the owner observations** (reproduces the
  card exactly): 7640/7641.16 -> -0.02%; 8000/7641.16 -> +4.70%;
  7650/7653.76 -> -0.05%. Formula and precision confirmed.
- No threshold, no category, no state inference. This is presentation math on
  artifact-provided values, in the same class as converting the 0DTE fraction
  to a percent or Net GEX to billions. (See D-1 for the workplan "no renderer
  computation" reconciliation.)

### CUT from the card (never rendered; asserted absent by tests)

Raw gross call/put-wall magnitudes; dominant raw GEX magnitude; full-precision
net USD; coverage/exclusion diagnostics; expiration range; provenance taxonomy;
zero-OI / zero-gamma counts; source URL; what-changed; persistence/history;
gamma flip; and every interpretive label - `AT SPOT`, `MAGNET`, `PIN`,
`SHORT-GAMMA REGIME`, `LONG-GAMMA REGIME`, `SUPPORT`, `RESISTANCE`,
"dealers are short gamma", "negative gamma will amplify moves".

---

## SS6 - Suppression and baseline-neutrality contract

### Whole-card suppression (card absent; dashboard otherwise byte-identical)

The loader returns `None` (card fully absent) on ANY of:

| Condition | Result |
|---|---|
| Artifact ABSENT | card absent |
| MALFORMED JSON | card absent (loader swallows `JSONDecodeError`) |
| WRONG SHAPE / not a dict | card absent |
| MISSING load-bearing field | card absent |
| NON-FINITE load-bearing value | card absent |
| `dominant_net_gamma` unavailable (strike null) | card absent |
| STALE (SS7) | card absent |
| Any unexpected exception (incl. tz-db error) | card absent |

**Never rendered:** `GEX UNKNOWN`, `GEX 0`, a neutral placeholder, a stale
warning card, or an error card. **The safest failure is absence.** The reader
must never make dashboard rendering fail (the whole loader body is guarded so
every failure path returns `None`).

### Row-level omission (VALID artifact with honestly unavailable OPTIONAL field)

When the artifact is otherwise valid and load-bearing but an OPTIONAL
sub-object is honestly unavailable (`call_wall`, `put_wall`, or `zero_dte.share`
null with a producer reason), the card renders and **only that row is omitted**.
A valid producer "unavailable" reason is never converted into an error.

**Resolution of "ARTIFACT INVALID vs VALID-WITH-UNAVAILABLE-OPTIONAL":**
Dominant is LOAD-BEARING (its unavailability suppresses the whole card); walls
and 0DTE are OPTIONAL (individual unavailability omits only that row). This
resolves the owner's "dominant availability may be more load-bearing than wall
availability" firmly, deterministically.

### Baseline-neutrality invariant

With no usable GEX (`gex_context is None`), the rendered dashboard is
byte-identical to the pre-GEX-2 baseline for the GEX region: the renderer emits
nothing for GEX. Test T9 asserts this (SS11). This matches the workplan's GEX-2
requirement "missing/stale/invalid yields baseline-identical output"
(`docs/plans/decision-support-workplan-v0.1.md:407`).

---

## SS7 - Freshness contract

**Primary age source:** `feed_timestamp_utc` (the observed feed time). NOT
`fetched_at_utc` (producer clock) and NOT `data_delay` (a descriptive string,
which remains a disclosure, not the stale basis).

**Selected rule (single knob, deterministic, stdlib-only):**

```
age = now_utc - parse(feed_timestamp_utc)          # now_utc injectable, tz-aware
render iff 0 <= age <= MAX_FEED_AGE_MINUTES
MAX_FEED_AGE_MINUTES = 120   (provisional product-safety bound; see D-2)
```

A feed timestamp that is absent, unparseable, non-finite, or in the future
(`age < 0`) is treated as stale -> card absent (fail toward suppression).

**Why 120 minutes:** the two observed samples changed materially over ~4.5h
(net GEX -40.1B -> -56.3B; dominant 7650 -> 7640), so an 18-24h window would let
hours-old or prior-session structure masquerade as current - which the owner
explicitly rejects. A 2-hour ceiling keeps a rendered card genuinely current,
rejects any prior-session snapshot (an overnight gap far exceeds 2h, so no
exchange calendar is needed), and tolerates a normal manual run-then-view
workflow. It is a single named constant, trivially tuned. No scheduler,
exchange calendar, cron, or holiday database is added. (See D-2.)

The ET-date-match alternative was rejected as insufficient: a 09:31 ET snapshot
would still render at 15:59 ET (same ET date, ~6.5h old), which is exactly the
hours-old masquerade the owner bars. The max-age rule already implies
same-session for any realistic case, so no second knob is added.

---

## SS8 - No-decision-authority and no payload/publish coupling (proof)

Traced cold at e89eebb. GEX-2 couples into NONE of the following, with the
current-code reason each does not require the card:

- **`assert_valid_payload` (`cuttingboard/delivery/payload.py:217-279`)**:
  validates a fixed, closed set of nine `sections` keys via subset-membership
  (`_require_keys`, `:286-289`) - it does not iterate cards and does not reject
  extras. **GEX-2 does not touch payload at all** (the card reads the artifact
  directly, not via a payload section), so the payload writer/validator is
  untouched.
- **`validate_coherent_publish`
  (`cuttingboard/delivery/dashboard_renderer.py:563-627`)**: coherence is a
  hardcoded triple of `generation_id`s from payload / run / market_map
  (`:556-560,624-627`). A card is not one of those artifacts; it is neither read
  nor compared here.
- **Readiness (`scripts/check_readiness.py`)**: HTML gate asserts a fixed
  3-marker allowlist `REQUIRED_HTML_MARKERS` (`:39-43`); payload JSON requires
  only `("meta","run_status","schema_version","sections")` (`:28`). No card
  enumeration. **The coupling to AVOID is adding the card's marker to
  `REQUIRED_HTML_MARKERS`** - GEX-2 must not.
- **Notification formatters (`cuttingboard/notifications/formatter.py`)**:
  dispatch on `AlertEvent` types (`:122-306`), never on dashboard cards.
- **Audit writers**: none enumerate dashboard cards (audit lives in the contract
  `audit_summary`).
- **No decision module reads the artifact** (SS3 sweep), so
  presence/absence/staleness/failure changes no TRADE/NO TRADE/HALT, candidate
  permission, qualification, grading, ranking, sizing, regime, kill switch, or
  execution behavior. The card is a pure display leaf.

**Binding direction:** GEX-2 must NOT become a required payload section, a
contract field, a coherent-publish requirement, a readiness marker, a
notification field, or an audit requirement. If implementation is found to
require touching payload schema or any publish/readiness gate -> STOP (SS14).

---

## SS9 - Persistence classification and artifact-flow consequences

**Persistence: none new.** GEX-2 writes no new file and adds no new persisted
schema surface. It reads the existing `logs/gex_snapshot.json` (produced by
PRD-306) and renders into the existing `ui/dashboard.html` output, published via
the existing `publish`-branch path (PRD-194). The card state is in-memory,
derived per render.

**Artifact-flow-map consequence (the doc line GEX-2 falsifies):**
`docs/artifact_flow_map.md:169` currently states the GEX snapshot has
"machine consumers: **none**". Once the renderer reads it, that becomes FALSE
and must be updated to name the dashboard display renderer as a machine
consumer. **Surgical update:** only "machine consumers: none" changes; the rest
of the Consumers block stays true, because a *display* reader is not a *decision*
module - the "no `cuttingboard` decision module reads it; presence/absence/
staleness/failure changes no TRADE/HALT/..." clause (`:169-172`) remains
accurate, as does "Category: ... never read for decision logic" (`:173`).

Other canonical lines to reconcile when GEX-2 lands (enumerated so none is left
silently stale; NOT a North Star truth-sync campaign):
- `docs/PROJECT_STATE.md:32` - "no consumer" becomes stale; update to reflect
  the one display consumer.
- `docs/plans/decision-support-workplan-v0.1.md:52` - GEX-2 row status
  `EVIDENCE BLOCKED` -> implemented; and `:398` (GEX-1 "no consumer") is
  superseded by the sanctioned GEX-2 display step (`:400-407`), a scope
  transition, not a flat error.
- `docs/SCHEMA_MAP.md` / `docs/CALL_SITE_MAP.md` - currently no GEX entry
  (grep: no matches); no false line to fix. Adding a CALL_SITE_MAP reader entry
  is appropriate but author-discretion (SS10 cone note).

---

## SS10 - Likely FILES cone (smallest honest cone from current repo truth)

**PRODUCTION PAYLOAD (forces HIGH-RISK):**
```
M cuttingboard/delivery/dashboard_renderer.py
```
The only production file: the `_load_gex_context` loader, the `gex_context`
kwarg on `write_dashboard` + `render_dashboard_html`, the `main()` load+pass,
and the GEX render block all live here (all bespoke optional-card loaders
already live in this file - SS3).

**TEST:**
```
A tests/test_dash_gex.py   (recommended - new focused file)
```
Matches the existing split-test architecture (`tests/test_dash_macro.py`,
`tests/test_dash_candidates.py`, `tests/test_dash_core.py`, ...). Author
discretion; the alternative (extend `tests/test_dashboard_renderer.py`) is
acceptable but bloats a 169-call file.

**DOC / PRODUCT TRUTH:**
```
M docs/artifact_flow_map.md                        (Consumers line, SS9)
M docs/plans/decision-support-workplan-v0.1.md     (GEX-2 row status; SS9)
```

**LIFECYCLE BOOKKEEPING (ordinary; every PRD):**
```
A docs/prd_history/PRD-308.md
M docs/PRD_REGISTRY.md        (PRD-308 row)
M docs/prd_index.json         (next_prd bump; not a HIGH-RISK FILE, stays implicit)
M docs/PROJECT_STATE.md       (active-PRD pointer + consumer-status line, SS9)
```

**AUTHOR-DISCRETION (list in the PRD if taken):**
```
M docs/CALL_SITE_MAP.md       (ADD a gex_snapshot reader call-site entry)
```

**STRONGLY EXPECTED NOT TO TOUCH** (touching any of these is a boundary
expansion -> STOP, SS14): `tools/gex_snapshot.py`, `tests/test_gex_snapshot.py`,
`cuttingboard/delivery/payload.py`, `scripts/check_readiness.py` (no new
marker), `scripts/preview_fixtures.py`, `runtime/`, `qualification/`, `regime/`,
`execution/`, `cuttingboard/notifications/`, any workflow YAML, `ui/dashboard.html`
as committed source, and `logs/gex_snapshot.json` as committed content.

If repo truth at implementation time proves another production file is required,
it MUST be called out (not hidden to keep the cone small); adding it after
Gate A requires the GOV-2 SS5 amended-PRD review and a fresh Gate A.

---

## SS11 - Proposed LOC / dependency ceiling and test/mutation plan

### LOC / dependency ceiling (proposed; the BINDING ceiling is Gate A)

- Production: **<= 120 LOC** in `dashboard_renderer.py` (loader ~15-25;
  kwarg threading ~6; render block ~40-70). Estimate ~60-100; the ceiling is
  the not-to-exceed.
- **0 new dependencies.** Stdlib `datetime` + `zoneinfo` only (already relied on
  in-tree); any tz-db failure is caught by the loader and yields card-absent,
  never a dashboard crash.

### Test / mutation plan (synthetic artifacts only; no network; every
load-bearing guard ships a mutation-red test - PRD-198 invariant 4)

| # | Test | Load-bearing guard / mutation that must turn it red |
|---|---|---|
| T1 | valid artifact renders card | render path present; mutate to drop card -> red |
| T2 | no artifact -> card absent | `path.exists()` gate |
| T3 | malformed JSON -> card absent, dashboard still renders | `except JSONDecodeError -> None` (NOT `_load_json_optional`) |
| T4 | wrong shape / non-dict -> card absent | `isinstance(data, dict)` gate |
| T5 | missing load-bearing field -> card absent | field-presence gate |
| T6 | non-finite load-bearing numeric -> card absent | `math.isfinite` gate |
| T7 | stale artifact -> card absent | `age <= MAX_FEED_AGE_MINUTES` gate (injected `now`) |
| T8 | current valid artifact -> card present | fresh path |
| T9 | baseline-neutrality: `gex_context=None` render == pre-GEX baseline | no-GEX byte-identity |
| T10 | Net GEX billions formatting (`-$56.3B*`) | `/1e9`, 1-dp, sign, `*` |
| T11 | signed distance formatting (`-0.02%`,`+4.70%`) | `((strike/spot)-1)*100`, 2-dp, sign |
| T12 | 0DTE formatting (fraction -> `7.6%`) | `share*100`, 1-dp |
| T13 | delayed label always present on rendered card | unconditional disclosure |
| T14 | assumption-honesty token always present on rendered card | unconditional disclosure |
| T15 | gross wall dollar magnitudes never rendered | absence assertion |
| T16 | forbidden vocabulary never rendered (magnet/pin/support/resistance/dealer short gamma/dealer long gamma) | absence assertion |
| T17 | optional wall unavailable -> that row omitted, card present; dominant unavailable -> whole card absent | row-vs-card suppression rule (SS6) |
| T18 | GEX never enters payload validation / coherence / readiness as required data | assert `assert_valid_payload` / `validate_coherent_publish` / readiness pass unchanged with and without the card |

Determinism: identical inputs -> identical output (no wall clock in the
renderer; `now` injected into the loader in tests).

---

## SS12 - Manual UI validation plan (ceremony for the later implementation)

CONSUMER validation depth is "Manual UI/notification render; targeted tests on
consumer path" (`docs/PRD_PROCESS.md:460`). Render to a SCRATCH path
(`reports/output/...` or tmp), **never** hand-overwrite committed
`ui/dashboard.html` (CLAUDE.md working practices); the sanctioned pre-merge
preview is `.github/workflows/dashboard_preview.yml` (ephemeral, never
committed/deployed).

1. Render with a current valid synthetic GEX artifact.
2. Visually inspect the actual card.
3. Confirm five-second readability.
4. Confirm assumption + delay disclosures visible.
5. Confirm no raw diagnostic clutter (SS5 CUT list).
6. Remove/rename the artifact; rerender.
7. Prove the GEX card disappears.
8. Confirm the baseline dashboard is otherwise unchanged.
9. Stale the synthetic artifact (feed_timestamp_utc beyond MAX_FEED_AGE).
10. Confirm the whole card suppresses.
11. Make one optional wall unavailable (strike null) on an otherwise-valid
    artifact; confirm only that row is omitted and the card still renders.

No screenshot-generation requirement beyond existing repo practice.

---

## SS13 - Explicit cuts (deferred; NOT in GEX-2 v1)

GEX history; what-changed; persistence database; gamma flip; vanna; charm;
max pain; estimated intraday OI; live flow; CVD; OPRA; heatmap; SPY duplicate;
second provider; cadence; scheduler; cron; automatic producer invocation;
notifications; trade coupling; thresholds; parameter tuning; ML. **GEX-2 is ONE
removable card.**

---

## SS14 - Stop conditions

STOP and return to HELM/Dustin (do not route around) if, at implementation time:
1. the card requires ANY producer modification (new field, producer-emitted
   distance, schema change) - boundary expansion;
2. implementation requires touching payload schema, `assert_valid_payload`,
   `validate_coherent_publish`, or adding a `REQUIRED_HTML_MARKERS` entry;
3. a second production file beyond `dashboard_renderer.py` is required (amend
   PRD + GOV-2 SS5 amended review + fresh Gate A);
4. D-1 is ruled against the card (distance/percent presentation deemed forbidden
   "renderer computation") - the card's core reading depends on distance;
5. scope expands to add cadence, a scheduled producer run, a second reader, or
   any decision-path coupling - re-run GOV-2 SS1 classification.

---

## SS15 - Unresolved owner decisions

Not buried in prose; each labeled with a recommendation.

**D-1 - Distance/percent presentation vs the workplan's "no renderer
computation."** `docs/plans/decision-support-workplan-v0.1.md:404` specifies
GEX-2 has "no renderer computation." The owner's target card shows distance
percentages that the artifact does not emit, so distance must be derived
renderer-side (`((strike/spot)-1)*100`) - the producer is out of scope.
**Recommendation: PERMITTED.** "No renderer computation" bars re-deriving GEX
*structural* values (walls, net, dominant) in the renderer; it does not bar
trivial presentation arithmetic on already-selected, artifact-provided values,
which is the same class as converting the 0DTE fraction to a percent or net USD
to billions. Every existing card does presentation formatting.
**If ruled against:** the card omits distance percentages and shows bare strikes
- which guts the product finding (dominant strike ~0.02-0.05% FROM SPOT is the
whole point). Strongly recommend PERMITTED.

**D-2 - Exact `MAX_FEED_AGE_MINUTES`.** **Recommendation: 120 minutes**, a
single named constant, labeled provisional product-safety bound, trivially
tuned at or after Gate A. Rationale in SS7. Owner may set a different value; the
rule shape (max-age on `feed_timestamp_utc`) is the recommendation, the exact
number is the open knob.

(Author-discretion, not owner decisions, resolved with recommendations in the
cone: new `tests/test_dash_gex.py` file (SS10); optional `CALL_SITE_MAP.md`
reader entry (SS9/SS10).)

---

## SS16 - Author self-verification results

- **Cited files/functions verified against e89eebb:** producer schema read
  first-hand (`tools/gex_snapshot.py:339-360`); renderer signatures and call
  sites (`dashboard_renderer.py:2049,3197,3236,3415`); precedent loaders
  (`:953-965,3308-3350,3374,3391-3397`). PASS.
- **Renderer call sites enumerated mechanically:** 2 production
  (`dashboard_renderer.py:3236`, `scripts/preview_fixtures.py:53`) + ~400 tests,
  all keyword-arg / `None`-default compatible. PASS.
- **All current machine consumers of `logs/gex_snapshot.json`:** NONE - main
  agent re-ran `rg` over `cuttingboard/` -> zero hits. PASS.
- **No existing GEX display reader:** confirmed none. PASS.
- **Payload/coherence/readiness non-coupling:** verified in code
  (`payload.py:217-289`, `dashboard_renderer.py:556-627`,
  `scripts/check_readiness.py:28,39-43`). PASS.
- **HIGH-RISK classification vs current PRD_PROCESS:** confirmed
  (`docs/PRD_PROCESS.md:460,482,499-517`). PASS.
- **MATERIAL classification vs current GOV-2:** confirmed trigger 2
  (`GOV-2 ...:22`). PASS.
- **FILES cone completeness:** production = 1 file; no hidden second production
  file identified; boundary-expansion stop condition stated. PASS.
- **`git diff --check`:** clean (no whitespace errors) - see final report.
- **No production code changed:** this packet adds only
  `audits/gex-2-material-packet-2026-08/` docs. PASS.

Pre-existing repo debt observed, NOT absorbed (product delivery first;
Phase 17 flagged separately): (a) the registry-gap hook flags three
`PRD-301.*.confirmation.*.md` files lacking registry rows - unrelated to GEX-2;
(b) older North Star docs may carry stale Polygon/GEX-held wording - none is
build-authoritative for GEX-2.

---

## SS17 - Downstream sequence (informative; no authority created here)

Provisional packet (this) -> Codex Event-1 packet review (read-only) -> one
consolidated correction -> Codex Event-2 exact-corrected-head confirmation
(GOV-2 SS7) -> Dustin design-direction ruling -> Stage-0 PRD-308 scaffold
(`CLASS: CONSUMER`, `LANE: HIGH-RISK`) -> fresh-context PRD review -> Gate A ->
implementation -> implementation review + PRD-242 second-model disposition ->
Dustin merge.

**This packet authorizes none of the above. It is design only.**
