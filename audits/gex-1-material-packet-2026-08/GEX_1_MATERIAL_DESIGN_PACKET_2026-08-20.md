# GEX-1 — Manual cached `_SPX` GEX producer: MATERIAL design packet

```
STATUS: PROVISIONAL MATERIAL PACKET — 2026-08-20 — DESIGN ONLY
AUTHORIZES NO IMPLEMENTATION, NO PRD NUMBER, NO CONSUMER, NO CADENCE
GOV-2 PACKET-REVIEW CYCLE: PENDING (provisional until review-clean, GOV-2 §2)
```

> This is the upstream MATERIAL design packet GOV-2 requires before any GEX-1
> PRD, decision entry establishing design direction, or implementation
> authority. It defines the smallest doctrine-compliant GEX-1 producer so
> Dustin can issue a design-direction ruling from a review-clean packet.
> Nothing here is buildable authority: the sequence ahead is packet review →
> one consolidated correction → exact-corrected-head confirmation → Dustin's
> design-direction ruling → Stage-0 PRD → fresh-context PRD review → Gate A.

---

## §0 — Intake classification (GOV-2 §1)

**MATERIAL — owner-accepted.** Dustin accepted MATERIAL treatment for GEX-1
on 2026-08-20 (`docs/DECISIONS.md` 2026-08-20 entry, this PR). Independently
of the acceptance, two §1 legs fire on the merits:

- **Layer crossing:** the producer performs a live network fetch plus in-repo
  computation (runtime) and writes a durable, versioned, schema-bearing
  artifact (persistence). Two of the enumerated layers.
- **Ceiling establishment:** §8 of this packet proposes the production FILES
  and LOC ceiling for the implementation — itself a §1 trigger.

Legs that do NOT fire, stated for completeness: no claim to enumerate all
consumers (GEX-1 has none by construction — §5 proves the negative for
today's tree, not for all time); no contract/audit/report/payload surface
touched; no governance guardrail changed; no Critical/High finding resolved.

**Lane consequence:** MICRO ineligible (MATERIAL bar). Expected downstream
PRD header: `CLASS: SIDECAR` (T1), `LANE: STANDARD` — no HIGH-RISK FILES
entry appears as payload for the SIDECAR class in §7's cone, CLASS is
neither EXECUTION nor CONTRACT, and default Tier is not T0, so PRD-121 R11
does not force HIGH-RISK.

## §1 — Authority (charge-template mirror)

- **Operator ruling:** `docs/DECISIONS.md` 2026-08-20 — "GEX GO: Cboe `_SPX`
  single-underlying first slice, MATERIAL under GOV-2, GEX-1 design packet
  commissioned (ruled: Dustin)". Five points: GO; `_SPX` single underlying
  (scope minimization — SPY deferred pending usefulness evidence, not
  invalidated); MATERIAL accepted; packet commissioned immediately; GEX
  remains context-only and creates no decision authority.
- **Governing plan:** `docs/plans/decision-support-expansion-doctrine-v0.1.md`
  §4 (GEX contract; §4.4 gate `GEX-1`), global invariants G1–G10.
- **Workplan packet:** `docs/plans/decision-support-workplan-v0.1.md` §8
  Wave 5, GEX-1 row.
- **Governing PRD:** NONE — this is the pre-PRD design packet; the Stage-0
  PRD opens only after the design-direction ruling.
- **Related evidence:**
  `audits/gex-0-cboe-evidence-2026-08/GEX_0_CBOE_PROVIDER_EVIDENCE_PACKET_2026-08-17.md`
  (verdict `PROVIDER VIABLE`, scoped; head `b55b0de`, **PR #256 — MERGED to
  `main` 2026-08-20, merge commit `ed87913`**) and
  `audits/gex-planning-recon-2026-08/GEX_1_2_PLANNING_RECON_2026-08-20.md`
  (planning recon, same branch as this packet).
  **Dependency, now satisfied:** PR #256 has landed on `main`, so the
  `PROVIDER VIABLE` verdict and the observed feed facts this design rests on
  are repository truth. The remaining sequence gate is unchanged — the
  Stage-0 PRD still opens only after Event-1 review, one consolidated
  correction, exact-corrected-head confirmation, and Dustin's
  design-direction ruling.
- **Precedence on conflict:** `VISION.md` → `CLAUDE.md` /
  `docs/PRD_PROCESS.md` → expansion doctrine → dated operator decision →
  active PRD → this packet. Conflicts stop the work; they are not resolved
  by interpretation here.

## §2 — Objective

Define the smallest honest, doctrine-compliant manual cached GEX producer
for the Cboe `_SPX` delayed_quotes feed — schema, computation, failure
semantics, seam trace, FILES cone, and ceilings — precisely enough that
Dustin can rule on design direction and a Stage-0 PRD can be drafted from
the ruling without re-deriving anything.

## §3 — Work type and preflight (charge-template mirror)

| Field | Value |
|---|---|
| Mode | DOCS-ONLY (design packet; no production code, no network fetch this pass) |
| Lane/class | N/A for the packet itself; downstream PRD expectation recorded in §0 |
| Mutation permission | This packet directory; the GEX-1 workplan row; the 2026-08-20 DECISIONS entry — nothing else |
| Merge permission | **NONE** — draft PR, held for Dustin (GOV-0 visible hold; GOV-1) |

Preflight (reported at authoring time):

1. Repository: `dwats250/cuttingboard`
2. Expected branch: `claude/gex-planning-reconnaissance-upntlo`
3. Actual branch: `claude/gex-planning-reconnaissance-upntlo`
4. Expected starting SHA: `38780ea362dc1a7c452c565cde6fe6cea0696c87` (branch
   head after the planning-recon commit; base `main` = `e3f0b59`)
5. Actual HEAD: `38780ea362dc1a7c452c565cde6fe6cea0696c87`
6. Remote counterpart: `origin/claude/gex-planning-reconnaissance-upntlo` =
   `38780ea` (fetched and compared this session)
7. Working tree: clean at start of authoring
8. PR state: none yet for this branch (draft PR opens with this commit);
   related PR #256 open/ready, head `b55b0de`, held for Dustin
9. Authority files read: doctrine §§3.1, 4, 7, 8; workplan §8 + ledger rows;
   GOV-2 §§1–2; `CLAUDE.md`; charge template v0.1; sidecar doctrine; Cboe
   evidence packet + its review; PRD_PROCESS CLASS/LANE matrices

## §4 — Design: the producer

### D1. Placement — standalone `tools/` CLI

`tools/gex_snapshot.py`: an argparse CLI in the `tools/macro_awareness_collector.py`
mold — the repo's only existing manual/lazy producer. It imports **no**
`cuttingboard` module and no `cuttingboard` module imports it; isolation is
grep-provable (the `TestR1Isolation` pattern from
`tests/test_macro_awareness_collector.py` carries over directly). This keeps
the no-pipeline-import guarantee mechanical, and stays outside the
banned-import purity fences that guard pure modules. The PRD_PROCESS SIDECAR
row names `cuttingboard/<name>_sidecar.py` as the class-typical file; that
shape assumes a runtime write hook, which GEX-1 is forbidden to have, so the
PRD will declare the `tools/` placement explicitly under `CLASS: SIDECAR`
with this packet as the recorded reason.

### D2. Invocation and artifact — manual, local-first

`python3 tools/gex_snapshot.py` fetches
`https://cdn.cboe.com/api/global/delayed_quotes/options/_SPX.json` once
(single GET, no retry loop, stdlib `urllib.request` only — no new
dependency), computes, and writes `logs/gex_snapshot.json` atomically
(tmp-then-`os.replace`, the established idiom). `logs/` is gitignored: the
first slice ships **no workflow, no commit of the artifact, no publish** —
Dustin runs it locally and reads the file. A `workflow_dispatch` workflow
mirroring `macro_awareness.yml` is a named later slice IF usefulness shows;
it is not part of GEX-1 (cuts-before-additions; G4 forbids cadence before a
useful consumer anyway).

### D3. Universe — `_SPX`, both roots

Single underlying `_SPX` per the operator ruling. The one response carries
both roots of the SPX complex — SPX (AM-settled) and SPXW (PM-settled) —
and both are included, with per-root contract counts in coverage. All
expirations in the response are included; no expiry windowing in v1 (a
window is a modeling choice; description-not-prediction says report what is,
and the per-expiry structure is an additive later extension if ruled
useful). SPY: out of scope, deferred, not invalidated.

### D4. Computation — descriptive GEX, labeled assumptions

Per contract row: parse the OCC-style `option` symbol (root, yymmdd expiry,
C/P flag, strike ×1000 — strict parse; unparseable rows are excluded and
counted). Contribution:

```
gex_contract = sign · gamma · open_interest · 100 · spot² · 0.01
  sign = +1 for calls, −1 for puts
  spot = data.current_price (SPX cash index level, per evidence §6 row 9)
```

- Convention: the standard published descriptive convention
  (dealers-long-calls / short-puts). It is an **assumption about
  positioning, not measured data**, and the artifact says so in a
  load-bearing `sign_convention` field (G1).
- Units: USD gamma notional per 1% underlying move (`units` field). Every
  GEX figure in the artifact — net signed total, both walls, dominant
  gamma, and the 0DTE numerator/denominator — is in these same units.
- Aggregation: `gex_total_1pct_usd` = Σ over all included contracts (the
  **net signed** aggregate, preserved). The five P0 structural outputs
  (net signed GEX, call wall, put wall, dominant gamma, 0DTE share) are
  defined deterministically in **D4a** below. `top_strikes` = the 10
  strikes with largest |Σ per-strike net GEX|, each
  `{strike, gex_1pct_usd, call_oi, put_oi}` — retained because it is cheap
  and useful, but it does **not** substitute for the four named structural
  outputs. No full per-strike table in v1 — compact, derived, and nowhere
  near raw-chain redistribution.
- Greeks are Cboe-model-computed; the artifact's `model_label` states the
  figure is derived-of-model (evidence §6 row 4).

### D4a. P0 structural outputs — deterministic definitions

All five are **DERIVED** (deterministic in-repo calculations over the
observed chain); none is provider-supplied — the Cboe feed ships no
vendor wall/flip levels (evidence §2). "Eligible contract" = an included
row per D6 (parseable OCC symbol, present numeric `gamma` and
`open_interest`; degenerate `gamma == 0` / `open_interest == 0` rows are
included and simply contribute 0). Per-strike aggregation groups eligible
contracts by parsed strike **across both roots (SPX + SPXW) and all
included expirations**. Let `strike_call_gex(k)` = Σ of `gex_contract` over
eligible **call** rows at strike `k` (each ≥ 0 by the sign convention);
`strike_put_gex(k)` = Σ of `gex_contract` over eligible **put** rows at
strike `k` (each ≤ 0); `strike_net_gex(k)` = `strike_call_gex(k) +
strike_put_gex(k)` (signed).

1. **Net signed GEX** — `gex_total_1pct_usd` = Σ `gex_contract` over all
   eligible contracts (calls positive, puts negative). Preserved
   unchanged. Provenance DERIVED; rests on the INFERRED dealer-positioning
   sign convention.

2. **Call wall** — `call_wall = {strike, call_gex_1pct_usd}` where `strike`
   = argmax over strikes `k` of `strike_call_gex(k)`, and
   `call_gex_1pct_usd` = that maximum (a positive call-side aggregate).
   Selection uses **call-side aggregated GEX, never call OI alone**.
   Tie-break: on equal `strike_call_gex`, the **lowest** strike wins
   (deterministic; the same lowest-strike rule is used for every structural
   output so ordering never depends on dict/iteration order). Unavailable:
   if there are no eligible call rows, **or** the maximum `strike_call_gex`
   is `0` (no non-zero call gamma notional anywhere), `call_wall = null`
   with a `reason` string — never a fabricated strike.

3. **Put wall** — `put_wall = {strike, put_gex_1pct_usd}` where `strike`
   = argmax over strikes `k` of `|strike_put_gex(k)|`, and
   `put_gex_1pct_usd` = `strike_put_gex(strike)` reported with its **native
   negative sign** (selection is by absolute magnitude; the reported value
   keeps the `−` so the sign convention stays visible and consistent with
   net signed GEX). Selection uses **put-side aggregated signed GEX, never
   put OI alone**. Tie-break: lowest strike. Unavailable: no eligible put
   rows, or maximum `|strike_put_gex|` is `0` → `put_wall = null` with a
   `reason`.

4. **Dominant gamma** — `dominant_gamma = {strike, net_gex_1pct_usd}` where
   `strike` = argmax over strikes `k` of `|strike_net_gex(k)|`, and
   `net_gex_1pct_usd` = `strike_net_gex(strike)` (signed). This is the
   **maximum absolute net per-strike signed GEX**, and it is deliberately
   distinct from the two walls: the walls read one side of the book
   (call-only / put-only) per strike, whereas dominant gamma reads the
   **net of both sides at the same strike**, so a strike where large call
   and put GEX cancel ranks high on the walls but low here, and a strike
   dominated by one side ranks high here. It is the single strike carrying
   the most concentrated net dealer gamma under the sign convention — not a
   vague "largest gamma node." (Alternatives considered and rejected for
   v1: max Σ`gamma·OI` ignoring sign — that is a raw-gamma node, not a
   signed-GEX node, and double-counts cancelling strikes; max single-contract
   |contribution| — that is a contract, not a strike.) Tie-break: lowest
   strike. Unavailable: all `strike_net_gex` are `0` → `dominant_gamma =
   null` with a `reason`.

5. **0DTE GEX share** — `zero_dte = {share, abs_gex_1pct_usd,
   denominator_abs_gex_1pct_usd, observation_trading_date, per_root:
   {SPX, SPXW}, caveat}`.
   - **Observation trading date** — the calendar date of the feed
     `timestamp` (authoritative feed clock) converted to US Eastern via the
     stdlib `zoneinfo` zone `America/New_York`, `.date()`. Eastern is used
     because OCC expiry dates are Eastern trading dates; `zoneinfo` handles
     DST and the UTC/ET date-boundary correctly (a feed stamp of
     `2026-08-18T01:00Z` resolves to trading date `2026-08-17`, not
     `2026-08-18`). Stdlib-only; see the tz caveat in §9 Q8.
   - **Numerator** `abs_gex_1pct_usd` = Σ `|gex_contract|` over eligible
     contracts whose OCC-parsed expiry date **equals** the observation
     trading date.
   - **Denominator** `denominator_abs_gex_1pct_usd` = Σ `|gex_contract|`
     over **all** eligible included contracts (all included expirations —
     the share of the full observed structure; a bounded near-dated horizon
     is a modeling choice deferred to §9 Q7).
   - **`share`** = numerator ÷ denominator, in `[0, 1]`. Absolute (not
     signed) GEX is used so cancellation cannot push the share negative or
     above 1.
   - **`per_root`** = the 0DTE numerator split into SPX vs SPXW contribution
     (and contract counts). This is the honest handling of the
     **AM-settled SPX vs PM-settled SPXW** distinction: v1 matches by
     expiry **date only** and does **not** model whether an AM-settled SPX
     contract has already settled at the open (that needs settlement-time
     knowledge and a market calendar — outside stdlib + single-snapshot
     scope, §9 Q6). Surfacing the per-root split lets the human see how much
     "0DTE" gamma is AM-settled SPX (which on its expiry morning may already
     be settled and typically carries ~0 gamma in the feed) versus
     PM-settled SPXW (true intraday 0DTE). v1 reports what the feed carries;
     it never drops or reweights already-settled contracts silently.
   - **`caveat`** — a fixed string stating the expiry-date-only method and
     the AM/PM-settlement non-modeling, so the artifact is honest standing
     alone.
   - **Zero denominator** — if the denominator is `0` (every eligible row
     inert: all `gamma == 0` or `open_interest == 0`, which is possible even
     with `included > 0`), `share = null` with a `reason`; never `0/0`.
     Outside market hours or on a non-trading observation date, the numerator
     is legitimately `0` (no contracts expire that date) → `share = 0.0`,
     which is honest, not an error.

### D5. Schema v1 (versioned, additive from birth — G5)

Top-level keys, all always present on a written artifact:

| Field | Content |
|---|---|
| `schema_version` | `1` |
| `source` | `"cboe_delayed_quotes"` |
| `endpoint` | the exact `_SPX` URL fetched |
| `underlying` | `"_SPX"`; `roots`: `["SPX","SPXW"]` |
| `fetched_at_utc` | tz-aware ISO-8601, producer clock; naive datetime is a construction error (watchlist-sidecar precedent) |
| `feed_timestamp_utc` | the response's top-level `timestamp` (UTC per evidence §6 row 8) |
| `data_delay` | `"~15 min delayed (REPORTED; Cboe delayed_quotes posture)"` — never presented as real-time |
| `spot` | `{value, basis: "SPX cash index level (data.current_price)"}` |
| `model_label` | `"greeks Cboe-model-computed; GEX derived-of-model"` |
| `sign_convention` | `"calls:+1 / puts:-1 — assumed dealer-long-call/short-put positioning; descriptive assumption, not measured"` |
| `units` | `"USD gamma notional per 1% underlying move"`; `contract_multiplier`: `100` — the units of every GEX figure below |
| `gex_total_1pct_usd` | net signed GEX total (P0 #1; D4a) |
| `call_wall` | P0 #2 — `{strike, call_gex_1pct_usd}` or `null` + `reason` (D4a) |
| `put_wall` | P0 #3 — `{strike, put_gex_1pct_usd}` (value signed ≤ 0) or `null` + `reason` (D4a) |
| `dominant_gamma` | P0 #4 — `{strike, net_gex_1pct_usd}` (value signed) or `null` + `reason` (D4a) |
| `zero_dte` | P0 #5 — `{share, abs_gex_1pct_usd, denominator_abs_gex_1pct_usd, observation_trading_date, per_root: {SPX, SPXW}, caveat}`; `share` may be `null` + `reason` (D4a) |
| `top_strikes` | ≤10 rows `{strike, gex_1pct_usd, call_oi, put_oi}` — retained, not a substitute for the four named outputs |
| `provenance` | classification of every output: `{observed: [...], derived: [...], inferred: [...]}` (D4a; see below) |
| `coverage` | `{contracts_total, included, excluded: {missing_fields, unparseable_symbol}, zero_gamma_rows, zero_oi_rows, per_root: {SPX, SPXW}, expirations: {count, min, max}}` |

**Provenance classification** (the `provenance` field names each output by
class, so no modeled figure is ever read as provider-observed truth):

- **OBSERVED** (Cboe/source facts): `source`, `endpoint`, `underlying`/
  `roots`, `feed_timestamp_utc`, `spot` (value + basis), and the per-contract
  `gamma`/`open_interest` the calculations consume, plus the `coverage`
  counts.
- **DERIVED** (deterministic Cuttingboard calculations): `gex_total_1pct_usd`,
  `call_wall`, `put_wall`, `dominant_gamma`, `zero_dte` (share + numerator +
  denominator + `observation_trading_date`), `top_strikes`.
- **INFERRED / MODEL-DERIVED** (assumption-dependent): the dealer-positioning
  reading carried by `sign_convention` (calls +1 / puts −1 is an assumption,
  not measured), and `model_label` (the Cboe greeks are model-computed, so
  every GEX figure is derived-of-model). The DERIVED outputs are arithmetically
  exact but inherit this INFERRED interpretive layer — the sign of a wall or
  of net GEX is a positioning *interpretation*, not an observed dealer book.

The artifact is honest standing alone: source, model, timestamps, delay,
coverage, the sign assumption, and the OBSERVED/DERIVED/INFERRED provenance
of every output are all embedded (workplan GEX-1 row:
"source/model/timestamp/coverage embedded").

### D6. Coverage and degenerate rows — count, don't hide (G6)

Load-bearing **top-level** surfaces missing (options list, `current_price`,
`timestamp`) → exit non-zero, no artifact written. **Per-row** missing
`gamma`/`open_interest` keys or unparseable OCC symbols → row excluded and
counted by reason. Rows with numeric `gamma == 0.0` or `open_interest == 0`
(degenerate deep-ITM etc., observed in evidence §6 row 12) are **included**
(they contribute 0) and counted, so the human sees how much of the chain is
inert. If `included == 0` → exit non-zero. No proportion thresholds, no
silent repair: the human reads `coverage`.

### D7. Unavailable / failure — fail loud, never overwrite good data

Non-200 status (the observed unknown-symbol behavior is HTTP 403 with an
S3-style XML body — evidence §6 row 13), non-JSON content, or missing
top-level surfaces: print the reason to stderr, **exit non-zero, write
nothing** — the previous good artifact (if any) is untouched, and its own
embedded `fetched_at_utc` carries staleness honestly (PRD-198 invariant 1;
G6). No retry storm: one fetch per invocation. The rejected alternative —
writing a `status: UNAVAILABLE` artifact — destroys the last good
observation and is recorded as considered-and-rejected (§9 Q3).

### D8. Non-redistribution guard — machine-enforced

The artifact contains **no** per-contract rows, quotes, or raw chain data —
only derived aggregates (net total, the two walls, dominant gamma, the 0DTE
share, and ≤10 strike rows) and provenance. The four restored P0 outputs are
each a single strike + scalar (or a null), so they add no redistribution
surface. The test suite enforces it: an artifact-shape guard fails if
`top_strikes` exceeds its cap or any per-contract field (bid/ask/iv/etc.)
appears. Test fixtures
are **synthetic** chain JSON, never captured Cboe data, so the repo never
commits provider rows at all (stricter than the evidence packet's excerpt
cap). Posture unchanged: personal / non-redistributed / context-only; any
shift toward display-to-others stops for a fresh terms review (evidence §12
stop conditions carry forward).

## §5 — Seam trace (complete artifact lifecycle)

**Writer:** `tools/gex_snapshot.py` (manual CLI; the only writer).
**Path:** `logs/gex_snapshot.json` — non-overlapping, one-producer-per-path
(sidecar doctrine).
**Readers today: none.** Human inspection only; GEX-2 (display-only
consumer) is a separate, later, separately-gated work unit (G3).
**`docs/artifact_flow_map.md`:** gains a row in the implementation PRD (the
sidecar doctrine makes this mandatory in the same PRD), following the
existing `logs/watchlist_snapshot.json` entry format: Writer / Constant /
Universe / Consumers `(none) — observe-only` / Category / Test isolation
(monkeypatch the path constant to `tmp_path`).

Enumerated NON-consumers — surfaces that do **not** change and must not be
touched by the implementation (each verified against the current tree by
the planning recon's first-hand greps at `e3f0b59`; dispositions per the
evidence standard):

| Surface | Why untouched | Disposition |
|---|---|---|
| `cuttingboard/` package (all modules) | Producer imports nothing from it; nothing in it imports the producer. No GEX/gamma code exists (`grep -rniE "gex\|gamma" cuttingboard/` → exit 1) | CONFIRMED |
| `cuttingboard/delivery/dashboard_renderer.py`, `ui/*` | No consumer in GEX-1; baseline output byte-identical because the renderer never learns the artifact exists | CONFIRMED (by construction) |
| Contract/payload (`output.py`, `delivery/payload.py`, `ui/contract.json`) | Sidecar contract-isolation rule; no payload section, no contract field | CONFIRMED (by construction) |
| Notifications, hourly/daily workflows, publish gate (`validate_coherent_publish`) | No cadence, no notification, no publish; artifact is gitignored and uncommitted in slice 1 | CONFIRMED (by construction) |
| `scripts/clean_generated_artifacts.sh`, `tests/test_ci_artifact_hygiene.py` allowlists | Artifact never committed in slice 1, so it joins no force-add allowlist; the script's known GENERATED-array drift (PROJECT_STATE debt) is explicitly not inherited or fixed here | CONFIRMED |
| `cuttingboard/chain_validation.py` | Overlaps on paper (chain fetch, OI) but is a two-provider fallback chain — the doctrine §4.2 anti-pattern — on providers the GEX-0 evidence does not cover. Precedent, never a dependency; the implementation must not import or extend it | CONFIRMED |
| `docs/SCHEMA_MAP.md` | Sidecar artifact schemas conventionally live in the producer module + `artifact_flow_map.md`, not SCHEMA_MAP (no sidecar section exists there today) | CONFIRMED |

Falsifier for the negative claims: any new import edge or reader appearing
between this packet and Gate A — the PRD's pre-implementation grep sweep
(PRD-158) re-runs the decisive greps at implementation time.

## §6 — Requirements and discriminating tests (design-stage; binds the PRD draft, not the tree)

| # | Requirement | Observable behavior | Test (planned, `tests/test_gex_snapshot.py`) | Mutation that must turn it red |
|---|---|---|---|---|
| R1 | Happy path writes schema-v1 artifact | All §4-D5 keys present, correct types, on a synthetic fixture | `test_happy_path_writes_full_schema` | Drop any top-level key from the writer |
| R2 | GEX arithmetic is correct | Hand-computed expected total on a ≤6-contract fixture matches exactly | `test_gex_total_matches_hand_computation` | Alter multiplier, spot power, or the 0.01 factor |
| R3 | Put gamma is negated | Fixture with one call + one put of equal gamma·OI nets to 0 | `test_sign_convention_put_negative` | Flip or drop the sign |
| R4 | OCC symbol parse is strict and correct | Strike = digits/1000; root/expiry/flag extracted; malformed symbol → excluded + counted | `test_occ_parse_strike_scaling`, `test_unparseable_symbol_excluded_and_counted` | Drop the /1000; silently skip without counting |
| R5 | Non-200 → fail loud, nothing written | Exit ≠ 0; pre-existing artifact byte-identical | `test_non_200_exits_nonzero_preserves_artifact` | Swallow the status and write |
| R6 | Non-JSON body → fail loud | Same as R5 for XML/garbage body | `test_non_json_exits_nonzero` | try/except-continue around parse |
| R7 | Missing top-level surface → fail loud | Missing `current_price` (or options/timestamp) → exit ≠ 0, names the field | `test_missing_spot_exits_nonzero` | Default the missing field |
| R8 | Zero usable rows → fail loud | `included == 0` → exit ≠ 0 | `test_all_rows_excluded_exits_nonzero` | Write an empty-coverage artifact |
| R9 | Timestamps honest | `fetched_at_utc` tz-aware; naive → raise; `data_delay` label present verbatim | `test_naive_datetime_rejected`, `test_delay_label_present` | Accept naive; drop the label |
| R10 | Atomic write | Injected failure mid-write leaves the previous artifact intact | `test_write_failure_preserves_previous` | Replace tmp-then-replace with direct write |
| R11 | Isolation | No top-level `cuttingboard` import in the producer; no `cuttingboard` module imports it | `test_no_cuttingboard_import`, `test_no_reverse_import` | Add either import edge |
| R12 | Non-redistribution shape | `top_strikes` ≤ 10; no per-contract field names anywhere in the artifact | `test_artifact_has_no_chain_rows` | Raise the cap; emit bid/ask |
| R13 | Determinism | Byte-identical output for fixed fixture + fixed clock | `test_deterministic_output` | Introduce dict-order or float-format drift |
| R14 | Call wall = max call-side GEX | Fixture where the max-`call_oi` strike differs from the max-call-GEX strike → `call_wall.strike` is the call-GEX winner | `test_call_wall_uses_call_side_gex_not_oi` | Select by `call_oi`, or by net (call+put) GEX |
| R15 | Put wall = max \|put-side GEX\|, sign retained | Fixture where max-`put_oi` strike differs from max-put-GEX strike → correct strike; `put_gex_1pct_usd` is negative | `test_put_wall_uses_put_side_gex_not_oi`, `test_put_wall_value_is_negative` | Select by `put_oi`; report abs value / drop sign |
| R16 | Call/put cancellation is handled correctly | Strike A has large call & put GEX that net ≈ 0; strike B is one-sided smaller → `dominant_gamma` = B, but A still appears as both a wall candidate | `test_dominant_gamma_ignores_cancelled_strike` | Compute dominant from Σ\|contribution\| (sign-blind) → wrongly picks A |
| R17 | Dominant gamma = max \|net per-strike signed GEX\| | Fixture with a known signed-net peak → `dominant_gamma.strike` matches; value signed | `test_dominant_gamma_max_abs_net` | Use max signed (not abs); use call-side only |
| R18 | Deterministic tie-break (lowest strike) | Two strikes with exactly equal selection metric → the lower strike is chosen for every structural output | `test_wall_tie_break_lowest_strike`, `test_dominant_tie_break_lowest_strike` | Rely on dict/iteration order; pick higher strike |
| R19 | 0DTE numerator = expiry == observation trading date | Fixture with contracts expiring today + later → numerator sums only today's \|GEX\| | `test_zero_dte_numerator_today_only` | Include next-day expiries; use signed GEX |
| R20 | 0DTE denominator = all eligible expirations | Same fixture → denominator = Σ\|GEX\| over all included, not a window | `test_zero_dte_denominator_all_expirations` | Restrict denominator to a near-dated window |
| R21 | 0DTE per-root split (AM-SPX vs PM-SPXW) | Fixture with both roots expiring today → `per_root.SPX` and `per_root.SPXW` carry the correct split | `test_zero_dte_per_root_split` | Collapse roots; drop SPXW |
| R22 | Zero denominator → `share = null` | Fixture `included > 0` but every eligible row inert (gamma 0 / OI 0) → `zero_dte.share` is `null` + `reason`, no crash | `test_zero_dte_zero_denominator_null` | Emit `0.0`; raise `ZeroDivisionError` |
| R23 | Observation date via ET, not UTC | Fixture feed `timestamp` at `2026-08-18T01:00Z` (= ET 2026-08-17) with today-expiring contracts → `observation_trading_date` = `2026-08-17` and they count as 0DTE | `test_observation_trading_date_eastern_boundary` | Use the UTC calendar date → wrong date, 0DTE miss |

Every guard above is a PRD-198 invariant-4 red test: each merges only with
its demonstrated failing mutation. Tests never touch the network (fetcher
injected / URL overridden; synthetic fixtures only). R14–R23 discriminate the
restored P0 structural outputs; the walls/dominant/0DTE fixtures are
hand-built so the OI-based winner and the GEX-based winner are *different*
strikes (R14/R15), the cancelling strike is *not* the dominant one (R16), and
the ET/UTC date boundary actually flips the 0DTE membership (R23) — proxy
tests where the two coincide would pass under the wrong implementation and are
banned.

## §7 — FILES cone (provisional — the PRD copies or amends it, Gate A locks it)

| File | Change |
|---|---|
| `tools/gex_snapshot.py` | A — producer CLI |
| `tests/test_gex_snapshot.py` | A — R1–R23 suite |
| `docs/artifact_flow_map.md` | M — one writer row (mandatory same-PRD, sidecar doctrine) |
| `docs/plans/decision-support-workplan-v0.1.md` | M — GEX-1 row state flip at closeout |
| Lifecycle (implicit per PRD_PROCESS): `docs/PRD_REGISTRY.md`, `docs/prd_index.json`, `docs/PROJECT_STATE.md` | M — bookkeeping only |

Pre-implementation grep sweep (PRD-158) applies at PRD time; no rendered
field / contract key / enum is deleted or renamed, so no test-file additions
to FILES are expected from the sweep — the sweep still runs and binds.

## §8 — Change-surface ceiling (provisional, GOV-2 §5)

- Production files: **1** (`tools/gex_snapshot.py`)
- Test files: **1**
- Net production LOC: **≤ 420** — raised honestly from the pre-correction
  ≤ 340 to carry the four restored P0 structural outputs *within the same
  single production file* (the FILES cone does not widen). Margin math:
  fetch ~30, OCC parse ~40, top-level/per-row validation ~50, per-contract
  computation ~40, artifact build ~50, atomic write ~20, CLI main ~30,
  constants/docstrings ~40 ≈ 300 (the prior estimate); **+ per-strike
  aggregation ~25, call/put-wall + dominant selection with tie-break and
  null-on-unavailable ~30, 0DTE (ET-date via `zoneinfo`, expiry-date match,
  numerator/denominator, per-root split, zero-denominator) ~35, provenance
  block ~10 ≈ +100**; ≈ 400, + ~20 margin so an honest guard never fights
  the ceiling. This is a **pre-review provisional** ceiling adjustment (the
  packet is not yet Gate-A-locked; GOV-2 §5's amended-authority path governs
  a *post-Gate-A* increase, not this pre-ruling estimate refinement).
  Exceeding 420, a second production file, a new dependency, a workflow, or
  any consumer surface is a STOP → GOV-2 §5 amended-authority path, never
  silent expansion.
- New dependencies: **0** (stdlib only — `zoneinfo` is stdlib since Python
  3.9; it reads the OS IANA tz database, present on Linux/macOS and
  GitHub-hosted runners. If that database is absent, `ZoneInfo` raises and
  the producer fails loud — never a silent wrong date, and no `tzdata` pip
  dependency is added. See §9 Q8.)

## §9 — Open design questions for the design-direction ruling

Each has a recommended default; the ruling can adopt or override them all
in one act. None blocks packet review. The **five P0 structural outputs
(net signed GEX, call wall, put wall, dominant gamma, 0DTE share) are now
design-frozen in D4a/D5**, not open questions — the ruling may still
override a definition, but the packet no longer presents them as optional.

| # | Question | Recommendation | Named alternative |
|---|---|---|---|
| Q1 | Extra aggregation shape beyond the P0 outputs | Keep `top_strikes` (top-10 by \|net GEX\|) alongside the five frozen P0 outputs | Full per-strike profile (larger artifact, closer to raw data; additive later under G5) |
| Q2 | Units | USD per 1% move, spot² · 0.01 (all P0 GEX figures) | Per-1-point move (spot¹) |
| Q3 | Unavailable behavior | Exit non-zero, write nothing, preserve last good artifact | Write `status: UNAVAILABLE` artifact (rejected: destroys last observation) |
| Q4 | Delivery | Local-first, artifact gitignored, no workflow | `workflow_dispatch` workflow + force-add commit (named later slice, not GEX-1) |
| Q5 | Expiry treatment (per-contract inclusion) | All expirations included, no windowing | Near-dated window or per-bucket breakdown (additive later if ruled useful) |
| Q6 | AM-settled SPX vs PM-settled SPXW in the 0DTE bucket | Match by expiry **date only**; surface the per-root split; do **not** model settlement timing (needs a market calendar + settlement clock, outside stdlib + single-snapshot scope) | Drop/zero already-settled AM-SPX 0DTE contracts (requires settlement-time modeling — deferred; would also risk silently reweighting observed data) |
| Q7 | 0DTE denominator scope | All eligible included expirations (share of the full observed structure) | Bounded near-dated horizon denominator (a modeling choice; additive later) |
| Q8 | Observation-date derivation / tz reliance | Feed `timestamp` → `America/New_York` via stdlib `zoneinfo`, `.date()`; fail loud if the OS tz database is absent (no `tzdata` pip dep) | Add the `tzdata` wheel as an explicit dependency (breaks the 0-dependency ceiling); or use UTC date (rejected — wrong ET trading date near the day boundary, R23) |
| Q9 | Gamma flip / zero-gamma level | **Deferred from P0** — the first slice is useful with net GEX + both walls + dominant gamma + 0DTE share; gamma flip needs hypothetical-spot repricing assumptions and is a separately-dispositioned modeling question. It must **not** delay GEX-1 | Include a flip estimate in v1 (rejected for P0: introduces a repricing model — a prediction-adjacent assumption layer — into a descriptive first slice) |

## §10 — Review (GOV-2 packet cycle; charge-template mirror)

- **Event 1 — independent packet review:** fresh context, read-only, not the
  author. Review question: *is this the smallest honest GEX-1 design that
  satisfies doctrine §4.4, the sidecar doctrine, and the operator ruling —
  and is any material boundary omitted?* Artifact slot:
  `audits/gex-1-material-packet-2026-08/GEX_1_MATERIAL_DESIGN_PACKET_2026-08-20.review.<model>.md`,
  SHA-pinned to the reviewed head.
- **Correction:** ONE consolidated cycle, recorded in a `## CORRECTION
  CYCLE` section appended to this packet (dev-bootstrap precedent). A new
  material boundary omission returns the packet to DESIGN INCOMPLETE
  instead of a second cycle.
- **Event 2 — exact-corrected-head confirmation:** SHA-pinned confirmation
  artifact `PACKET_EXACT_CORRECTED_HEAD_CONFIRMATION_<date>.md`; a
  confirmation, not a fresh-scope review.
- **Operational blocker, stated:** the authoring container has no `codex`
  CLI, so neither event could run in the commissioning session.
  `CODEX_REVIEW_PROMPT_2026-08-20.md` (this directory) is the ready-to-run
  Event-1 charge: `codex exec -s read-only - <
  audits/gex-1-material-packet-2026-08/CODEX_REVIEW_PROMPT_2026-08-20.md`
  from an equipped checkout, stdout captured into the review slot above.
  **Held for your decision:** run it locally, or commission it from an
  equipped session.

## §11 — Validation, landing, stop conditions

Validation for this docs-only packet: `git diff --check` clean;
`python tools/validate_prd_registry.py --skip-commit-resolvability` exit 0
(registry untouched but must stay green); `git status --short` clean after
commit; diff contains only the files §3 permits.

Landing: this branch (`claude/gex-planning-reconnaissance-upntlo`), one
packet commit, **DRAFT PR** naming the GOV-0 expansion-plan hold; auto-merge
forbidden; merge is Dustin's, always.

Stop conditions (all live until Gate A): authority conflict; preflight
drift; any FILES/ceiling expansion; any move toward a consumer, cadence,
notification, second provider, SPY, or pipeline import; PR #256 rejected or
materially amended (the evidence basis changes → packet returns to Dustin);
any posture shift toward redistribution; the task creating prediction,
execution automation, or decision coupling (forbidden by doctrine — and by
the operator ruling's own final clause).

## §12 — Pre-review revision log

This section records author revisions made **before** the GOV-2 Event-1
review runs; it is not the `## CORRECTION CYCLE` (that slot stays reserved
for the single consolidated post-review cycle GOV-1 allows).

- **2026-08-20 — bounded P0 correction (this revision).** Restored four
  explicit P0 structural outputs that the prior draft had collapsed into
  net-total + generic `top_strikes`: **call wall**, **put wall**, **dominant
  gamma (max |net per-strike signed GEX|)**, and **0DTE GEX share** — each
  now a first-class schema field with a deterministic definition,
  tie-break, and unavailable behavior (D4a, D5). Net signed GEX preserved;
  `top_strikes` retained as cheap-and-useful but explicitly not a
  substitute. Added `provenance` (OBSERVED / DERIVED / INFERRED)
  classification so no modeled figure reads as provider-observed. Added
  discriminating tests R14–R23 (wall selection by GEX not OI, call/put
  cancellation, dominant selection, deterministic tie-break, 0DTE
  numerator/denominator, per-root AM/PM split, zero-denominator,
  ET/UTC date boundary). Raised the provisional LOC ceiling ≤ 340 → ≤ 420
  within the same single-file cone (no FILES widening); dependencies still
  0 (stdlib `zoneinfo`). Deferred gamma flip from P0 (§9 Q9). Truth-synced
  §1: PR #256 merged to `main` (`ed87913`). Gamma flip and settlement-time
  modeling remain out of scope.

```
PROVISIONAL MATERIAL PACKET — DESIGN ONLY — REVIEW CYCLE PENDING — NO IMPLEMENTATION AUTHORITY.
```
