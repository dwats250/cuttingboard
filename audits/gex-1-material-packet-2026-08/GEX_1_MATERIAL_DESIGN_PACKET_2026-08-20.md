# GEX-1 — Manual cached `_SPX` GEX producer: MATERIAL design packet

```
STATUS: PROVISIONAL MATERIAL PACKET — 2026-08-20 — DESIGN ONLY
AUTHORIZES NO IMPLEMENTATION, NO PRD NUMBER, NO CONSUMER, NO CADENCE
GOV-2 PACKET-REVIEW CYCLE: EVENT 1 COMPLETE (verdict DESIGN INCOMPLETE at
  70475f2; single consolidated correction APPLIED — see ## CORRECTION CYCLE)
AWAITING: EVENT 2 EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 §7) — the packet
  is NOT review-clean and carries NO downstream authority until it passes
```

> This is the upstream MATERIAL design packet GOV-2 requires before any GEX-1
> PRD, decision entry establishing design direction, or implementation
> authority. It defines the smallest doctrine-compliant GEX-1 producer so
> Dustin can issue a design-direction ruling from a review-clean packet.
> Nothing here is buildable authority. Sequence position: Event-1 packet
> review COMPLETE (DESIGN INCOMPLETE) → the ONE consolidated correction
> APPLIED (this revision) → **Event-2 exact-corrected-head confirmation
> (next)** → Dustin's design-direction ruling → Stage-0 PRD → fresh-context
> PRD review → Gate A.

---

## §0 — Intake classification (GOV-2 §1)

**MATERIAL — owner-accepted.** Dustin accepted MATERIAL treatment for GEX-1
on 2026-08-20 (`docs/DECISIONS.md` 2026-08-20 entry, this PR). Independently
of the acceptance, three §1 legs fire on the merits:

- **Layer crossing:** the producer performs a live network fetch plus in-repo
  computation (runtime) and writes a durable, versioned, schema-bearing
  artifact (persistence). Two of the enumerated layers.
- **Ceiling establishment:** §8 of this packet proposes the production FILES
  and LOC ceiling for the implementation — itself a §1 trigger.
- **Consumer enumeration (corrected per Event-1 F1):** §5 claims to
  enumerate ALL consumers of the new artifact — it declares the complete
  reader set, enumerates non-consumers, and states a falsifier. GOV-2 §1
  fires on the enumeration claim itself, including when the machine-reader
  set enumerated is empty. The enumeration is: the initial consumer is
  **HUMAN — Dustin, via manual local inspection** of
  `logs/gex_snapshot.json` (`docs/sidecar_doctrine.md` names the human
  reader as a valid observation-sidecar consumer); **machine readers:
  none** (`rg -ni 'gex|gamma' cuttingboard/` → exit 1; no reader of
  `logs/gex_snapshot.json`; no `cuttingboard` module imports `tools/`).
  The prior draft's claim that this leg does not fire was wrong and is
  withdrawn.

Legs that do NOT fire, stated for completeness: no contract/audit/report/
payload surface touched; no governance guardrail changed; no Critical/High
finding resolved.

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
  **Dependency, now satisfied in-tree (Event-1 F2 closed structurally):**
  PR #256 has landed on `main` (merge commit `ed87913`), and during the
  Event-1 correction cycle `origin/main` — containing `ed87913` and the
  GEX-0 evidence packet — was merged into this packet branch. The governing
  Cboe evidence is therefore **an ancestor of, and present in-tree at, this
  corrected head**: the `PROVIDER VIABLE` verdict and the observed feed
  facts this design rests on are repository truth at the reviewed commit,
  not an external reference. The remaining sequence gate is unchanged — the
  Stage-0 PRD still opens only after the Event-2 exact-corrected-head
  confirmation and Dustin's design-direction ruling.
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
8. PR state at original authoring: none yet for this branch (draft PR opened
   with the packet commit). *Corrected in the Event-1 cycle:* related PR #256
   (head `b55b0de`) is **MERGED to `main`** — merge commit `ed87913`,
   2026-08-20 — and `origin/main` has been merged into this branch, so the
   GEX-0 evidence is in-tree at this corrected head (§1)
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
  (net signed GEX, call wall, put wall, dominant net gamma, 0DTE share) are
  defined deterministically in **D4a** below — and they are the **entire v1
  aggregation surface**. No `top_strikes`, no per-strike table, no strike
  profile in v1 (Event-1 HELM cut: the earlier generic `top_strikes` output
  is removed): a broader strike profile / top-N / heatmap is additive
  FUTURE work under G5 only if the first slice proves useful. Compact,
  derived, nowhere near raw-chain redistribution.
- Greeks are Cboe-model-computed; the artifact's `model_label` states the
  figure is derived-of-model (evidence §6 row 4).

### D4a. P0 structural outputs — deterministic definitions

All five are **DERIVED** (deterministic in-repo calculations over the
observed chain); none is provider-supplied — the Cboe feed ships no
vendor wall/flip levels (evidence §2). "Eligible contract" = a row admitted
by **D6's frozen admissibility rules** (strictly parseable OCC symbol with
allowlisted root SPX/SPXW and C/P type flag, valid calendar expiry date,
admissible `gamma` — numeric, non-boolean, finite, ≥ 0 — and admissible
`open_interest` — non-boolean integer, ≥ 0; degenerate `gamma == 0` /
`open_interest == 0` rows are admissible and simply contribute 0).
Per-strike aggregation groups eligible
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

2. **Call wall** — `call_wall = {strike, gex_1pct_usd, reason}` where
   `strike` = argmax over strikes `k` of `strike_call_gex(k)`, and
   `gex_1pct_usd` = that maximum (a positive call-side aggregate; the metric
   field name is the unified `gex_1pct_usd` across all three wall/dominant
   objects). Selection uses **call-side aggregated GEX, never call OI
   alone**. Tie-break: on equal `strike_call_gex`, the **lowest** strike
   wins (deterministic; the same lowest-strike rule is used for every
   structural output so ordering never depends on dict/iteration order).
   Available: `reason: null`. Unavailable: the **object is still present**
   with `strike: null, gex_1pct_usd: null` and a stable explicit reason
   token — `"no_eligible_calls"` (no eligible call rows) or
   `"no_nonzero_call_gex"` (maximum `strike_call_gex` is `0`: no non-zero
   call gamma notional anywhere). Never a fabricated strike, never a bare
   `null` in place of the object.

3. **Put wall** — `put_wall = {strike, gex_1pct_usd, reason}` where
   `strike` = argmax over strikes `k` of `|strike_put_gex(k)|`, and
   `gex_1pct_usd` = `strike_put_gex(strike)` reported with its **native
   negative sign** (selection is by absolute magnitude; the reported value
   keeps the `−` so the sign convention stays visible and consistent with
   net signed GEX; the field name is the unified `gex_1pct_usd`). Selection
   uses **put-side aggregated signed GEX, never put OI alone**. Tie-break:
   lowest strike. Available: `reason: null`. Unavailable: object still
   present with `strike: null, gex_1pct_usd: null` and reason token
   `"no_eligible_puts"` (no eligible put rows) or `"no_nonzero_put_gex"`
   (maximum `|strike_put_gex|` is `0`).

4. **Dominant net gamma** — `dominant_net_gamma = {strike, gex_1pct_usd,
   reason}` where `strike` = argmax over strikes `k` of
   `|strike_net_gex(k)|`, and `gex_1pct_usd` = `strike_net_gex(strike)`
   (signed; the field name is the unified `gex_1pct_usd`). This is the
   **maximum absolute net per-strike signed GEX**, and it is deliberately
   distinct from the two walls: the walls read one side of the book
   (call-only / put-only) per strike, whereas dominant net gamma reads the
   **net of both sides at the same strike**, so a strike where large call
   and put GEX cancel ranks high on the walls but low here, and a strike
   dominated by one side ranks high here. It is the single strike carrying
   the most concentrated net dealer gamma under the sign convention — not a
   vague "largest gamma node." The persisted field name
   `dominant_net_gamma` keeps the NET semantic explicit (Event-1
   Recommended 4; the earlier `dominant_gamma` name is renamed everywhere).
   (Alternatives considered and rejected for
   v1: max Σ`gamma·OI` ignoring sign — that is a raw-gamma node, not a
   signed-GEX node, and double-counts cancelling strikes; max single-contract
   |contribution| — that is a contract, not a strike.) Tie-break: lowest
   strike. Available: `reason: null`. Unavailable: all `strike_net_gex` are
   `0` → object still present with `strike: null, gex_1pct_usd: null,
   reason: "all_net_gamma_zero"`.

5. **0DTE GEX share** — `zero_dte = {share, abs_gex_0dte_1pct_usd,
   abs_gex_total_1pct_usd, observation_trading_date, per_root:
   {SPX, SPXW}, caveat, reason}`. The object is always present;
   `reason: null` when `share` is available.
   - **Observation trading date** — the calendar date of the feed
     `timestamp` (authoritative feed clock; provider shape and UTC
     interpretation frozen in D6 top-level admissibility, per evidence §6
     row 8) converted to US Eastern via the
     stdlib `zoneinfo` zone `America/New_York`, `.date()`. Eastern is used
     because OCC expiry dates are Eastern trading dates; `zoneinfo` handles
     DST and the UTC/ET date-boundary correctly (a provider stamp of
     `"2026-08-18 01:00:00"` — naive text, interpreted UTC — resolves to
     trading date `2026-08-17`, not `2026-08-18`). Stdlib-only; see the tz
     caveat in §9 Q8.
   - **Numerator** `abs_gex_0dte_1pct_usd` = Σ `|gex_contract|` over
     eligible contracts whose OCC-parsed expiry date **equals** the
     observation trading date. Always emitted as a number.
   - **Denominator** `abs_gex_total_1pct_usd` = Σ `|gex_contract|`
     over **all** eligible included contracts (all included expirations —
     the share of the full observed structure; a bounded near-dated horizon
     is a modeling choice deferred to §9 Q7). Always emitted as a number.
   - **`share`** = numerator ÷ denominator, in `[0, 1]`, or `null` with a
     reason token when unavailable (below). Absolute (not
     signed) GEX is used so cancellation cannot push the share negative or
     above 1.
   - **`per_root`** = the explicit descriptive SPX/SPXW split of the 0DTE
     numerator: `{SPX: {abs_gex_0dte_1pct_usd, contracts}, SPXW:
     {abs_gex_0dte_1pct_usd, contracts}}`. This is the honest handling of the
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
     with `included > 0`), `share = null` with reason token
     `"zero_abs_gex_denominator"` (numerator and denominator still emitted
     as `0` numbers; the object stays fully present); never `0/0`.
     Outside market hours or on a non-trading observation date, the numerator
     is legitimately `0` (no contracts expire that date) → `share = 0.0`
     with `reason: null`, which is honest, not an error.

### D5. Schema v1 (versioned, additive from birth — G5)

Top-level keys, all always present on a written artifact:

| Field | Content |
|---|---|
| `schema_version` | `1` |
| `source` | `"cboe_delayed_quotes"` |
| `endpoint` | the exact `_SPX` URL fetched |
| `underlying` | `"_SPX"` (CONFIGURED endpoint scope) |
| `roots` | `["SPX","SPXW"]` — the CONFIGURED admissibility allowlist (D6); own row per Event-1 Recommended 2 |
| `fetched_at_utc` | tz-aware ISO-8601, **producer clock — locally observed, not a provider fact**; naive datetime is a construction error (watchlist-sidecar precedent) |
| `feed_timestamp_utc` | the response's top-level `timestamp` — observed provider shape is **naive text `YYYY-MM-DD HH:MM:SS` interpreted as UTC** (evidence §6 row 8, header-corroborated); strictly parsed against that exact contract and re-emitted as a timezone-aware ISO-8601 UTC value (e.g. `2026-08-18T01:00:00+00:00`); malformed provider timestamp → fail loud, nothing written (D6) |
| `data_delay` | `"~15 min delayed (REPORTED; Cboe delayed_quotes posture)"` — never presented as real-time |
| `spot` | `{value, basis: "SPX cash index level (data.current_price)"}` |
| `model_label` | `"greeks Cboe-model-computed; GEX derived-of-model"` |
| `sign_convention` | `"calls:+1 / puts:-1 — assumed dealer-long-call/short-put positioning; descriptive assumption, not measured"` |
| `units` | `"USD gamma notional per 1% underlying move"`; `contract_multiplier`: `100` — the units of every GEX figure below |
| `gex_total_1pct_usd` | net signed GEX total (P0 #1; D4a) |
| `call_wall` | P0 #2 — `{strike: number\|null, gex_1pct_usd: number\|null, reason: string\|null}` — **always present**; `reason: null` when available, reason token + null metrics when unavailable (D4a) |
| `put_wall` | P0 #3 — `{strike: number\|null, gex_1pct_usd: number\|null, reason: string\|null}` (available value keeps its native negative sign, ≤ 0) — always present (D4a) |
| `dominant_net_gamma` | P0 #4 — `{strike: number\|null, gex_1pct_usd: number\|null, reason: string\|null}` (available value signed) — always present (D4a) |
| `zero_dte` | P0 #5 — `{share: number\|null, abs_gex_0dte_1pct_usd: number, abs_gex_total_1pct_usd: number, observation_trading_date, per_root: {SPX: {abs_gex_0dte_1pct_usd, contracts}, SPXW: {abs_gex_0dte_1pct_usd, contracts}}, caveat, reason: string\|null}` — always present; `share: null` + reason token only on the zero-denominator case (D4a) |
| `provenance` | exhaustive classification of **every emitted top-level field**, five classes: `{configured: [...], observed: [...], reported: [...], derived: [...], inferred: [...]}` (see below) |
| `coverage` | `{contracts_total, included, excluded: {missing_fields, invalid_gamma, invalid_open_interest, unparseable_symbol, invalid_expiry, unexpected_root}, zero_gamma_rows, zero_oi_rows, per_root: {SPX, SPXW}, expirations: {count, min, max}}` — one exact reason key per exclusion class (D6); `included` + Σ `excluded` = `contracts_total` |

**Provenance classification** (Event-1 F6: the `provenance` field is
**exhaustive** — every emitted top-level field appears in exactly one of
five explicit classes, so no modeled or transformed figure is ever read as
provider-observed truth):

- **CONFIGURED** (producer constants, chosen in-repo — NOT provider
  observations): `schema_version`, `source`, `endpoint`, `underlying`,
  `roots` (the admissibility allowlist), `units` (+ `contract_multiplier`).
- **OBSERVED** (provider feed facts read from the response): `spot`
  (`data.current_price`, value + basis), `feed_timestamp_utc` (parsed from
  the provider's top-level `timestamp`), and the per-contract
  `gamma`/`open_interest` the calculations consume (inputs, never emitted
  as rows). `fetched_at_utc` is **locally OBSERVED** — the producer's own
  clock at fetch time, explicitly identified as a local observation, not a
  provider fact.
- **REPORTED** (provider posture taken on report, not independently
  re-derived): `data_delay` (the ~15-minute Cboe delayed_quotes posture;
  evidence §6 row 7).
- **DERIVED** (deterministic producer transformations — explicitly NOT raw
  provider observations): `gex_total_1pct_usd`, `call_wall`, `put_wall`,
  `dominant_net_gamma`, `zero_dte` (share, numerator, denominator,
  `observation_trading_date`, `per_root`), every `coverage` count and
  summary (included/excluded/per_root/zero-value/expiration summaries are
  producer transformations of the chain, not provider facts — the prior
  draft's OBSERVED classification of coverage was wrong and is corrected),
  and the unavailable `reason` tokens.
- **INFERRED** (assumption-dependent interpretive layer): the
  dealer-positioning reading carried by `sign_convention` (calls +1 /
  puts −1 is an assumption, not measured), and `model_label` (the Cboe
  greeks are model-computed — a labeled inference per evidence §6 row 4 —
  so every GEX figure is derived-of-model). The DERIVED outputs are
  arithmetically exact but inherit this INFERRED interpretive layer — the
  sign of a wall or of net GEX is a positioning *interpretation*, not an
  observed dealer book.

The artifact is honest standing alone: source, model, timestamps, delay,
coverage, the sign assumption, and the CONFIGURED/OBSERVED/REPORTED/
DERIVED/INFERRED provenance of every emitted field are all embedded
(workplan GEX-1 row: "source/model/timestamp/coverage embedded").

### D6. Admissibility domain — frozen (G6; Event-1 F3/F4)

The eligible-input domain is frozen exactly; nothing outside it is
admitted, defaulted, or repaired.

**Top-level admissibility** — ALL of the following must hold, or the run
**fails loud: exit non-zero, write nothing, last good artifact preserved**
(D7):

1. The `options` collection exists and is a valid list of contract rows.
2. `current_price` is numeric, **non-boolean** (`isinstance(x, bool)` is
   tested FIRST — Python `bool` subclasses `int`, so a bare numeric check
   would silently admit `True`), **finite** (NaN/±inf rejected), and
   **> 0**.
3. The top-level `timestamp` matches the observed provider contract
   **exactly**: naive text `YYYY-MM-DD HH:MM:SS`, strictly parsed and
   interpreted as **UTC** (evidence §6 row 8: naive text such as
   `"2026-08-17 18:42:35"`, UTC-interpreted by comparison against the HTTP
   `Date` header). A malformed or missing provider timestamp is a fail-loud
   condition — never a fallback to the producer clock.

**Per-contract admissibility** — a row is eligible only if ALL of the
following hold; any failure **excludes the row and increments exactly one
`coverage.excluded` reason key**:

- `gamma`: numeric, non-boolean, finite, **≥ 0** → else `invalid_gamma`
  (a missing `gamma` or `open_interest` key → `missing_fields`).
- `open_interest`: **non-boolean integer, ≥ 0** → else
  `invalid_open_interest`.
- OCC `option` symbol: strict pattern parse (root, yymmdd expiry, type
  flag, strike ×1000) → else `unparseable_symbol`. An option type other
  than `C`/`P` fails the strict pattern and lands here — C/P only.
- Expiry: positionally parseable AND a **valid calendar date** (e.g.
  month 13 or Feb 30 rejected) → else `invalid_expiry`.
- Root: allowlist `SPX` / `SPXW` **only** → else `unexpected_root`.

Reason keys, at minimum: `missing_fields`, `invalid_gamma`,
`invalid_open_interest`, `unparseable_symbol`, `invalid_expiry`,
`unexpected_root`. Checks run in that fixed order per row —
missing-fields, then symbol parse, then root, then expiry, then gamma,
then open interest — and the FIRST failure counts, so exclusion counting
is deterministic (R13). `included` + Σ `excluded` = `contracts_total`.

Boolean note (applies everywhere a numeric is validated, top-level and
per-row): a boolean must never pass numeric validation merely because
Python `bool` subclasses `int` — `isinstance(x, bool)` is always checked
first and rejects.

Degenerate rows with numeric `gamma == 0.0` or `open_interest == 0`
(deep-ITM etc., observed in evidence §6 row 12) are **admissible**: they
are included (they contribute 0) and counted (`zero_gamma_rows` /
`zero_oi_rows`), so the human sees how much of the chain is inert. If
`included == 0` → fail loud, exit non-zero, write nothing. No proportion
thresholds, no silent repair: the human reads `coverage`.

### D7. Unavailable / failure — fail loud, never overwrite good data

Non-200 status (the observed unknown-symbol behavior is HTTP 403 with an
S3-style XML body — evidence §6 row 13), non-JSON content, or any missing
or **invalid** top-level surface per D6 (including a malformed provider
`timestamp`): print the reason to stderr, **exit non-zero, write
nothing** — the previous good artifact (if any) is untouched, and its own
embedded `fetched_at_utc` carries staleness honestly (PRD-198 invariant 1;
G6). No retry storm: one fetch per invocation. The rejected alternative —
writing a `status: UNAVAILABLE` artifact — destroys the last good
observation and is recorded as considered-and-rejected (§9 Q3).

### D8. Non-redistribution guard — machine-enforced

The artifact contains **no** per-contract rows, quotes, or raw chain data —
only the five P0 derived outputs (a scalar net total; three single-strike
objects; the 0DTE share object), `coverage` counts, and provenance. With
`top_strikes` removed (Event-1 HELM cut) the guard rests on the five scalar
outputs plus an **exhaustive forbidden-key check**: the artifact-shape
guard recursively scans the emitted artifact and fails if ANY forbidden
per-contract chain key appears anywhere, at any depth. The frozen forbidden
set enumerates every observed per-contract field from evidence §6 row 5:
`bid`, `ask`, `bid_size`, `ask_size`, `iv`, `theo`, `delta`, `gamma`,
`theta`, `vega`, `rho`, `volume`, `last_trade_price`, `last_trade_time`,
`open`, `high`, `low`, `close`, `prev_day_close`, `change`,
`percent_change`, `tick`, `option`, `open_interest` (raw `gamma` /
`open_interest` are computation INPUTS and never appear as artifact keys) —
plus any list-of-objects container that could carry per-contract rows: the
only list the schema permits anywhere is the flat string list `roots` and
the provenance class name lists. Each P0 output is a single strike + scalar
+ reason (or nulls), so it adds no redistribution surface. Test fixtures
are **synthetic** chain JSON, never captured Cboe data, so the repo never
commits provider rows at all (stricter than the evidence packet's excerpt
cap). Posture unchanged: personal / non-redistributed / context-only; any
shift toward display-to-others stops for a fresh terms review (evidence §12
stop conditions carry forward).

## §5 — Seam trace (complete artifact lifecycle)

**Writer:** `tools/gex_snapshot.py` (manual CLI; the only writer).
**Path:** `logs/gex_snapshot.json` — non-overlapping, one-producer-per-path
(sidecar doctrine).
**Consumers (complete enumeration — this IS the GOV-2 §1
consumer-enumeration claim, recorded as firing in §0):**
- **Initial HUMAN consumer: Dustin — manual local inspection** of
  `logs/gex_snapshot.json`. The human reader is a valid observation-sidecar
  consumer per `docs/sidecar_doctrine.md`; "human inspection only" is a
  consumer, not an empty consumer set.
- **Machine readers today: none** (proven for the current tree below).
  GEX-2 (display-only machine consumer) is a separate, later,
  separately-gated work unit (G3).

**`docs/artifact_flow_map.md`:** gains a row in the implementation PRD (the
sidecar doctrine makes this mandatory in the same PRD), following the
existing `logs/watchlist_snapshot.json` entry format: Writer / Constant /
Universe / Consumers `Dustin — human, manual local inspection (observe-only);
machine consumers: none` / Category / Test isolation
(monkeypatch the path constant to `tmp_path`). The row must name the human
observation consumer truthfully — never `Consumers: (none)` (Event-1 F1).

Enumerated NON-consumers — surfaces that do **not** change and must not be
touched by the implementation (each verified against the current tree by
the planning recon's first-hand greps at `e3f0b59`; dispositions per the
evidence standard):

| Surface | Why untouched | Disposition |
|---|---|---|
| `cuttingboard/` package (all modules) | Producer imports nothing from it; nothing in it imports the producer. No GEX/gamma code exists (`rg -ni 'gex|gamma' cuttingboard/` → exit 1 — the exact command the Event-1 reviewer re-ran) | CONFIRMED |
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
| R7 | Missing top-level surface → fail loud (each of the three) | Missing `options` → exit ≠ 0; missing `current_price` → exit ≠ 0; missing `timestamp` → exit ≠ 0 — each names the field | `test_missing_options_exits_nonzero`, `test_missing_spot_exits_nonzero`, `test_missing_timestamp_exits_nonzero` | Default any one of the three missing fields |
| R8 | Zero usable rows → fail loud | `included == 0` → exit ≠ 0 | `test_all_rows_excluded_exits_nonzero` | Write an empty-coverage artifact |
| R9 | Timestamps honest | `fetched_at_utc` tz-aware; naive → raise; `data_delay` label present verbatim | `test_naive_datetime_rejected`, `test_delay_label_present` | Accept naive; drop the label |
| R10 | Atomic write | Injected failure mid-write leaves the previous artifact intact | `test_write_failure_preserves_previous` | Replace tmp-then-replace with direct write |
| R11 | Isolation | No top-level `cuttingboard` import in the producer; no `cuttingboard` module imports it | `test_no_cuttingboard_import`, `test_no_reverse_import` | Add either import edge |
| R12 | Non-redistribution shape — exhaustive forbidden-key guard | Recursive scan of the emitted artifact finds NONE of the D8 forbidden per-contract keys (`bid`, `ask`, `bid_size`, `ask_size`, `iv`, `theo`, `delta`, `gamma`, `theta`, `vega`, `rho`, `volume`, `last_trade_price`, `last_trade_time`, `open`, `high`, `low`, `close`, `prev_day_close`, `change`, `percent_change`, `tick`, `option`, `open_interest`) and no list-of-objects row container anywhere | `test_artifact_has_no_chain_rows` | Emit any one forbidden key (e.g. `bid`), or emit a per-contract row container |
| R13 | Determinism | Byte-identical output for fixed fixture + fixed clock | `test_deterministic_output` | Introduce dict-order or float-format drift |
| R14 | Call wall = max call-side GEX | Fixture built so the call-GEX winner is distinct from BOTH the call-OI winner AND the net-GEX winner (a heavy-put strike shifts the net winner elsewhere) → `call_wall.strike` is the call-GEX winner | `test_call_wall_uses_call_side_gex_not_oi_not_net` | Select by `call_oi` (red), or by net (call+put) GEX (also red — three distinct winners by construction) |
| R15 | Put wall = max \|put-side GEX\|, sign retained | Fixture where max-`put_oi` strike differs from max-put-GEX strike → correct strike; `put_wall.gex_1pct_usd` is negative (native sign kept) | `test_put_wall_uses_put_side_gex_not_oi`, `test_put_wall_value_is_negative` | Select by `put_oi`; report abs value / drop sign |
| R16 | Call/put cancellation is handled correctly | Strike A has large call & put GEX that net ≈ 0; strike B is one-sided smaller → `dominant_net_gamma` = B, but A still appears as both a wall candidate | `test_dominant_net_gamma_ignores_cancelled_strike` | Compute dominant from Σ\|contribution\| (sign-blind) → wrongly picks A |
| R17 | Dominant net gamma = max \|net per-strike signed GEX\| | Fixture where the winner is a NEGATIVE-net strike whose \|value\| exceeds the largest positive-net strike AND is distinct from the call-wall strike → `dominant_net_gamma.strike` is the negative-net winner; `gex_1pct_usd` keeps its negative sign | `test_dominant_net_gamma_max_abs_net` | Use max signed (not abs) → picks the positive strike, red; use call-side only → picks the call wall, red |
| R18 | Deterministic tie-break (lowest strike) | Two strikes with exactly equal selection metric → the lower strike is chosen for every structural output | `test_wall_tie_break_lowest_strike`, `test_dominant_tie_break_lowest_strike` | Rely on dict/iteration order; pick higher strike |
| R19 | 0DTE numerator = expiry == observation trading date, absolute GEX | Fixture with MIXED calls and puts expiring today (so the signed sum ≠ the absolute sum) plus later expiries → numerator sums only today's \|GEX\|, and equals the hand-computed absolute value, not the signed one | `test_zero_dte_numerator_today_only_absolute` | Include next-day expiries (red); use signed GEX (red — mixed C/P makes signed ≠ absolute by construction) |
| R20 | 0DTE denominator = all eligible expirations | Same fixture → denominator = Σ\|GEX\| over all included, not a window | `test_zero_dte_denominator_all_expirations` | Restrict denominator to a near-dated window |
| R21 | 0DTE per-root split (AM-SPX vs PM-SPXW) | Fixture with both roots expiring today → `per_root.SPX` and `per_root.SPXW` carry the correct split | `test_zero_dte_per_root_split` | Collapse roots; drop SPXW |
| R22 | Zero denominator → `share = null` + reason token, object intact | Fixture `included > 0` but every eligible row inert (gamma 0 / OI 0) → `zero_dte` object fully present, `share` is `null`, `reason` = `"zero_abs_gex_denominator"`, numerator/denominator emitted as `0`, no crash | `test_zero_dte_zero_denominator_null` | Emit `0.0`; raise `ZeroDivisionError`; drop the object or the reason token |
| R23 | Observation date via ET, not UTC — actual provider timestamp shape | Fixture feed `timestamp` = `"2026-08-18 01:00:00"` (the observed naive `YYYY-MM-DD HH:MM:SS` shape, interpreted UTC) → ET calendar date `2026-08-17` ≠ UTC calendar date `2026-08-18`; with contracts expiring 2026-08-17, `observation_trading_date` = `2026-08-17` and they count as 0DTE | `test_observation_trading_date_eastern_boundary` | Use the UTC calendar date → wrong date (`2026-08-18`), 0DTE miss |
| R24 | Call wall unavailable → always-present object + reason token | Fixture with eligible calls all `gamma·OI == 0` → `call_wall = {strike: null, gex_1pct_usd: null, reason: "no_nonzero_call_gex"}`; puts-only fixture → `reason: "no_eligible_calls"` | `test_call_wall_unavailable_reason_tokens` | Emit bare `null` for `call_wall`; fabricate a strike; drop the reason token |
| R25 | Put wall unavailable → always-present object + reason token | Fixture with no non-zero put GEX → `put_wall = {strike: null, gex_1pct_usd: null, reason: "no_nonzero_put_gex"}`; calls-only fixture → `reason: "no_eligible_puts"` | `test_put_wall_unavailable_reason_tokens` | Emit bare `null`; fabricate a strike; drop the token |
| R26 | Dominant net gamma unavailable on full cancellation | Fixture where every strike's call and put GEX cancel exactly (all `strike_net_gex == 0`) → `dominant_net_gamma = {strike: null, gex_1pct_usd: null, reason: "all_net_gamma_zero"}`; walls still resolve normally | `test_dominant_net_gamma_all_cancelled_unavailable` | Pick an arbitrary strike among the zeros; emit bare `null` |
| R27 | Uniform unavailable-object construction | On BOTH an all-available and an all-unavailable fixture, `call_wall` / `put_wall` / `dominant_net_gamma` / `zero_dte` are each present with their full key set; available objects carry `reason: null`; the metric key is `gex_1pct_usd` in all three wall/dominant objects | `test_unavailable_objects_always_present_uniform` | Omit an object when unavailable; omit `reason` when available; use a per-object metric name |
| R28 | Booleans never pass numeric validation | Row with `gamma: true` → excluded, `invalid_gamma`; row with `open_interest: true` → excluded, `invalid_open_interest`; top-level `current_price: true` → exit ≠ 0 | `test_boolean_rejected_per_row`, `test_boolean_spot_exits_nonzero` | Validate with `isinstance(x, (int, float))` without the `isinstance(x, bool)`-first check |
| R29 | Non-finite values rejected | Row with `gamma: NaN` (or `inf`) → excluded, `invalid_gamma`; top-level `current_price: NaN`/`inf` → exit ≠ 0 | `test_nonfinite_gamma_excluded`, `test_nonfinite_spot_exits_nonzero` | Drop the `math.isfinite` check |
| R30 | Negative / non-integer domain violations rejected | Row with `gamma: -0.5` → excluded, `invalid_gamma`; row with `open_interest: -3` or `open_interest: 2.5` → excluded, `invalid_open_interest` | `test_negative_gamma_excluded`, `test_invalid_open_interest_excluded` | Accept negatives; accept fractional OI |
| R31 | Expiry must be a valid calendar date | Row whose OCC symbol parses positionally but encodes an impossible date (e.g. month 13 / Feb 30) → excluded, `invalid_expiry` | `test_invalid_calendar_expiry_excluded` | Parse positionally without calendar validation |
| R32 | Root allowlist SPX/SPXW only | Row with root `XSP` (parseable, wrong root) → excluded, `unexpected_root` | `test_unexpected_root_excluded` | Accept any parseable root |
| R33 | Invalid top-level `current_price` → fail loud | `current_price` ≤ 0 or non-numeric (present but invalid — distinct from R7's missing case) → exit ≠ 0, artifact preserved | `test_invalid_spot_exits_nonzero` | Coerce/default an invalid spot and continue |
| R34 | Malformed provider timestamp → fail loud | Top-level `timestamp` not matching `YYYY-MM-DD HH:MM:SS` (e.g. ISO `T` form, or garbage) → exit ≠ 0, nothing written | `test_malformed_feed_timestamp_exits_nonzero` | Fall back to the producer clock; parse leniently |
| R35 | `feed_timestamp_utc` normalized tz-aware | Provider naive `"2026-08-17 18:42:35"` → artifact `feed_timestamp_utc` = `"2026-08-17T18:42:35+00:00"` (unambiguous tz-aware ISO-8601 UTC) | `test_feed_timestamp_normalized_utc` | Emit the naive provider text verbatim; interpret it as local time |
| R36 | Coverage reason keys exhaustive and reconciling | Fixture with exactly one row per exclusion class → each of the six keys (`missing_fields`, `invalid_gamma`, `invalid_open_interest`, `unparseable_symbol`, `invalid_expiry`, `unexpected_root`) counts exactly 1, and `included` + Σ `excluded` = `contracts_total` | `test_coverage_reason_keys_exhaustive` | Collapse reasons into one bucket; drop a key; double-count a row |
| R37 | Provenance exhaustive, five classes, correctly assigned | Every emitted top-level field appears in exactly one of `configured` / `observed` / `reported` / `derived` / `inferred`; `coverage` is listed under `derived` (never `observed`); `fetched_at_utc` carries the locally-observed identification | `test_provenance_exhaustive_five_classes` | Omit a field from the classification; move `coverage` to `observed`; drop a class |

Every guard above is a PRD-198 invariant-4 red test: each merges only with
its demonstrated failing mutation. Tests never touch the network (fetcher
injected / URL overridden; synthetic fixtures only). R14–R27 discriminate the
P0 structural outputs and their unavailable shapes; the walls/dominant/0DTE
fixtures are hand-built so the OI winner, the call-GEX winner, and the
net-GEX winner are pairwise *different* strikes (R14/R15), the negative-net
dominant winner beats the largest positive and differs from the call wall
(R17), the cancelling strike is *not* the dominant one (R16), mixed calls
and puts make the signed and absolute 0DTE numerators differ (R19), and the
ET/UTC date boundary actually flips the 0DTE membership on the real provider
timestamp shape (R23) — proxy tests where the discriminating values coincide
would pass under the wrong implementation and are banned. R28–R37 give every
frozen admissibility, timestamp, schema-shape, and provenance rule from the
Event-1 correction (D5/D6/D8) its own named red test with the mutation that
turns it red.

## §7 — FILES cone (provisional — the PRD copies or amends it, Gate A locks it)

| File | Change |
|---|---|
| `tools/gex_snapshot.py` | A — producer CLI |
| `tests/test_gex_snapshot.py` | A — R1–R37 suite |
| `docs/artifact_flow_map.md` | M — one writer row (mandatory same-PRD, sidecar doctrine) |
| `docs/plans/decision-support-workplan-v0.1.md` | M — GEX-1 row state flip at closeout |
| Lifecycle (implicit per PRD_PROCESS): `docs/PRD_REGISTRY.md`, `docs/prd_index.json`, `docs/PROJECT_STATE.md` | M — bookkeeping only |

Pre-implementation grep sweep (PRD-158) applies at PRD time; no rendered
field / contract key / enum is deleted or renamed, so no test-file additions
to FILES are expected from the sweep — the sweep still runs and binds.

## §8 — Change-surface ceiling (provisional, GOV-2 §5)

- Production files: **1** (`tools/gex_snapshot.py`)
- Test files: **1**
- Net production LOC: **≤ 400** — re-estimated bottom-up in the Event-1
  correction cycle, *within the same single production file* (the FILES
  cone does not widen). Two opposing movements against the prior ≤ 420:
  removing `top_strikes` REMOVES the top-N selection, row formatting, and
  per-strike OI accumulation (~−20; note the per-strike call/put/net GEX
  aggregation itself SURVIVES because the walls and dominant net gamma need
  it), while the frozen D6 admissibility domain, strict timestamp contract,
  uniform unavailable-object construction, and five-class provenance ADD
  validation code. Fresh bottom-up arithmetic: fetch (status/content-type)
  ~30; top-level admissibility incl. bool-first/finite/positive spot checks
  and strict `YYYY-MM-DD HH:MM:SS`-UTC timestamp parse + ISO re-emit ~35;
  OCC parse with root allowlist, C/P flag, strike ×1000, calendar-valid
  expiry ~45; per-row admissibility + six-reason deterministic exclusion
  counting ~35; per-contract GEX computation ~15; per-strike call/put/net
  aggregation ~20; wall/dominant selection with tie-break + uniform
  `{strike, gex_1pct_usd, reason}` builder + reason tokens ~35; 0DTE
  (ET-date via `zoneinfo`, expiry-date match, numerator/denominator,
  per-root split, zero-denominator) ~35; provenance constant block ~15;
  artifact build/serialize ~35; atomic write ~15; CLI main + fail-loud
  error paths ~25; constants/docstrings ~40. **Σ ≈ 380**, + ~20 margin
  (same margin policy as the prior estimate) = **ceiling 400** — the net of
  the cut and the added validation is LOWER than the prior 420, so the
  ceiling is honestly lowered, not held. This is a **pre-review-cycle
  provisional** ceiling (the packet is not yet Gate-A-locked; GOV-2 §5's
  amended-authority path governs a *post-Gate-A* increase, not this
  pre-ruling estimate refinement).
  Exceeding 400, a second production file, a new dependency, a workflow, or
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
(net signed GEX, call wall, put wall, dominant net gamma, 0DTE share) are
now design-frozen in D4a/D5**, not open questions — the ruling may still
override a definition, but the packet no longer presents them as optional.

| # | Question | Recommendation | Named alternative |
|---|---|---|---|
| Q1 | Extra aggregation shape beyond the P0 outputs | **OUT for v1** — the five P0 outputs are the whole v1 aggregation surface (Event-1 HELM cut: the earlier `top_strikes` proposal is removed) | A strike profile / top-N / heatmap is additive FUTURE work under G5, only if the first slice proves useful |
| Q2 | Units | USD per 1% move, spot² · 0.01 (all P0 GEX figures) | Per-1-point move (spot¹) |
| Q3 | Unavailable behavior | Exit non-zero, write nothing, preserve last good artifact | Write `status: UNAVAILABLE` artifact (rejected: destroys last observation) |
| Q4 | Delivery | Local-first, artifact gitignored, no workflow | `workflow_dispatch` workflow + force-add commit (named later slice, not GEX-1) |
| Q5 | Expiry treatment (per-contract inclusion) | All expirations included, no windowing | Near-dated window or per-bucket breakdown (additive later if ruled useful) |
| Q6 | AM-settled SPX vs PM-settled SPXW in the 0DTE bucket | Match by expiry **date only**; surface the per-root split; do **not** model settlement timing (needs a market calendar + settlement clock, outside stdlib + single-snapshot scope) | Drop/zero already-settled AM-SPX 0DTE contracts (requires settlement-time modeling — deferred; would also risk silently reweighting observed data) |
| Q7 | 0DTE denominator scope | All eligible included expirations (share of the full observed structure) | Bounded near-dated horizon denominator (a modeling choice; additive later) |
| Q8 | Observation-date derivation / tz reliance | Feed `timestamp` → `America/New_York` via stdlib `zoneinfo`, `.date()`; fail loud if the OS tz database is absent (no `tzdata` pip dep) | Add the `tzdata` wheel as an explicit dependency (breaks the 0-dependency ceiling); or use UTC date (rejected — wrong ET trading date near the day boundary, R23) |
| Q9 | Gamma flip / zero-gamma level | **Deferred from P0** — the first slice is useful with net GEX + both walls + dominant net gamma + 0DTE share; gamma flip needs hypothetical-spot repricing assumptions and is a separately-dispositioned modeling question. It must **not** delay GEX-1 | Include a flip estimate in v1 (rejected for P0: introduces a repricing model — a prediction-adjacent assumption layer — into a descriptive first slice) |

## §10 — Review (GOV-2 packet cycle; charge-template mirror)

- **Event 1 — independent packet review: COMPLETE (2026-08-20).** Fresh
  context, read-only Codex review, not the author. Reviewed commit:
  `70475f2bdd0bd7dd51525ba08a304b0f5add87a5`. Verdict: **DESIGN
  INCOMPLETE** — 7 REQUIRED findings + 4 RECOMMENDED, all accepted in
  full. Durable SHA-pinned record:
  `audits/gex-1-material-packet-2026-08/GEX_1_EVENT_1_CODEX_REVIEW_2026-08-20.md`.
  Charge used: `CODEX_REVIEW_PROMPT_2026-08-20.md` (this directory).
- **Correction: APPLIED (this revision).** The ONE consolidated cycle
  GOV-1 allows, recorded in the `## CORRECTION CYCLE` section appended to
  this packet (dev-bootstrap precedent). There is NO second author
  correction cycle: a new material boundary omission returns the packet to
  DESIGN INCOMPLETE instead of opening another cycle.
- **Event 2 — exact-corrected-head confirmation: PENDING (next gate).**
  SHA-pinned confirmation against the Event-1 findings list — a
  confirmation, not a fresh-scope review (GOV-2 §7). Ready-to-run charge:
  `CODEX_EVENT_2_CONFIRMATION_CHARGE_2026-08-20.md` (this directory):
  `codex exec -s read-only - <
  audits/gex-1-material-packet-2026-08/CODEX_EVENT_2_CONFIRMATION_CHARGE_2026-08-20.md`
  from an equipped checkout, stdout captured into
  `GEX_1_EVENT_2_CONFIRMATION_2026-08-20.md` with a header pinning the
  confirmed SHA. Only after a clean Event-2 confirmation is the packet
  review-clean; Dustin's design-direction ruling follows, then Stage-0 PRD
  → fresh-context PRD review → Gate A. Still NO implementation authority.

## §11 — Validation, landing, stop conditions

Validation for this docs-only packet: `git diff --check` clean;
`python3 tools/validate_prd_registry.py --skip-commit-resolvability` exit 0
(registry untouched but must stay green); `git status --short` clean after
commit; diff contains only the files §3 permits.

Landing: this branch (`claude/gex-planning-reconnaissance-upntlo`), one
packet commit, **DRAFT PR** naming the GOV-0 expansion-plan hold; auto-merge
forbidden; merge is Dustin's, always.

Stop conditions (all live until Gate A): authority conflict; preflight
drift; any FILES/ceiling expansion; any move toward a consumer, cadence,
notification, second provider, SPY, or pipeline import; the merged GEX-0
evidence basis (`ed87913`, in-tree at this head) materially amended or
reverted on `main` (the evidence basis changes → packet returns to Dustin);
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
- **2026-08-20 — post-Event-1 addendum (pointer, not a revision).** The
  entry above is a historical record of the pre-review draft; the Event-1
  correction cycle (see `## CORRECTION CYCLE` below) subsequently
  **removed `top_strikes` from v1 entirely**, **renamed `dominant_gamma` →
  `dominant_net_gamma`**, renamed its "dominant gamma" prose accordingly,
  and **re-estimated the LOC ceiling ≤ 420 → ≤ 400**. References to
  `top_strikes`, `dominant_gamma`, or the 420 ceiling in the entry above
  are superseded design, retained only as history.

## CORRECTION CYCLE (GOV-2 Event-1 — single consolidated author correction, 2026-08-20)

**This is the ONE consolidated correction cycle GOV-1 allows. There is NO
second author correction cycle: a new material boundary omission at Event-2
returns the packet to DESIGN INCOMPLETE rather than opening another
cycle.** Event-1: independent Codex packet review, reviewed SHA
`70475f2bdd0bd7dd51525ba08a304b0f5add87a5`, verdict DESIGN INCOMPLETE, 7
REQUIRED findings + 4 RECOMMENDED — all accepted in full by HELM. Durable
record: `GEX_1_EVENT_1_CODEX_REVIEW_2026-08-20.md` (this directory,
already committed). Disposition of every finding:

### F1 — Consumer-enumeration MATERIAL leg misstated; human consumer omitted (§0, §5)

- **ACCEPTED.**
- **Exact correction:** §0 now records the consumer-enumeration leg as
  FIRING (three legs, not two) and withdraws the prior claim that it does
  not; §5 replaces "Readers today: none" with the complete enumeration —
  initial HUMAN consumer Dustin (manual local inspection, a valid
  observation-sidecar consumer per `docs/sidecar_doctrine.md`) plus
  "machine readers today: none" as a separate, evidence-backed statement;
  the planned `docs/artifact_flow_map.md` row is respecified as
  `Consumers: Dustin — human, manual local inspection (observe-only);
  machine consumers: none`, never `Consumers: (none)`.
- **Test/requirement consequence:** none (classification/enumeration
  correction; the R11 isolation tests already pin the machine-reader
  negative).
- **HELM cut applied:** none under this item.

### F2 — Reviewed commit did not contain the governing Cboe evidence (§1, §3)

- **ACCEPTED.** Closed structurally by the orchestrator before this
  correction: `origin/main` (containing merge commit `ed87913` and the
  GEX-0 evidence packet) was merged into this branch, so the corrected
  head contains the evidence in-tree.
- **Exact correction:** §1's "Related evidence" bullet now states the
  evidence is an ancestor of and present in-tree at this corrected head;
  §3 preflight item 8's stale "PR #256 open/ready, head `b55b0de`, held
  for Dustin" is corrected to record the merge (`ed87913`, 2026-08-20)
  and the branch reconciliation; §11's stop condition now keys off the
  merged evidence basis being amended/reverted on `main`, not off a
  no-longer-open PR.
- **Test/requirement consequence:** none (repository-truth
  reconciliation).
- **HELM cut applied:** none under this item.

### F3 — Eligible-input domain materially incomplete (§4 D4/D6)

- **ACCEPTED.**
- **Exact correction:** D6 rewritten as "Admissibility domain — frozen":
  top-level rules (valid `options` list; `current_price` numeric,
  non-boolean via `isinstance(x, bool)`-first, finite, > 0; `timestamp`
  matching the provider contract exactly; any violation → fail loud, exit
  non-zero, write nothing, last good artifact preserved) and per-contract
  rules (gamma numeric/non-boolean/finite/≥ 0; open_interest non-boolean
  integer ≥ 0; strict OCC parse with C/P-only type flag; expiry parseable
  AND calendar-valid; root allowlist SPX/SPXW only) with the six frozen
  exclusion reason keys (`missing_fields`, `invalid_gamma`,
  `invalid_open_interest`, `unparseable_symbol`, `invalid_expiry`,
  `unexpected_root`), a deterministic per-row check order, and the
  reconciliation identity `included + Σ excluded = contracts_total`. The
  NaN/inf and bool-subclasses-int hazards are named explicitly. D4a's
  "eligible contract" definition and D5's `coverage` schema row updated to
  match; D7 extended to cover invalid (not just missing) top-level
  surfaces.
- **Test/requirement consequence:** R28 (booleans), R29 (non-finite), R30
  (negative gamma / invalid OI), R31 (calendar expiry), R32 (root
  allowlist), R33 (invalid spot), R36 (reason-key exhaustiveness +
  reconciliation) added; R7 strengthened to all three top-level surfaces
  (also under F7); R8 (`included == 0` fail-loud) unchanged and still
  binding.
- **HELM cut applied:** none under this item.

### F4 — Timestamp contract must match the observed provider shape (§4 D4a/D5, R23)

- **ACCEPTED.**
- **Exact correction:** the provider `timestamp` contract is frozen to the
  GEX-0-observed shape — naive text `YYYY-MM-DD HH:MM:SS` interpreted
  explicitly as UTC (evidence §6 row 8, e.g. `"2026-08-17 18:42:35"`
  UTC-interpreted by `Date`-header comparison) — in D6 top-level
  admissibility; emitted `feed_timestamp_utc` is normalized to
  timezone-aware ISO-8601 UTC (D5 row rewritten, e.g.
  `2026-08-18T01:00:00+00:00`); malformed provider timestamps fail loud.
  The old invented `"2026-08-18T01:00Z"` form is removed from D4a
  (observation-trading-date example now `"2026-08-18 01:00:00"`), from the
  D5 `feed_timestamp_utc` row, and from R23.
- **Test/requirement consequence:** R23 rewritten on the actual provider
  shape, proving ET date `2026-08-17` ≠ UTC date `2026-08-18`; R34
  (malformed timestamp → fail loud) and R35 (tz-aware ISO-8601
  normalization) added.
- **HELM cut applied:** none under this item.

### F5 — Unavailable output shapes must be representable and always-present (§4 D4a/D5)

- **ACCEPTED.** HELM-recommended schema frozen verbatim.
- **Exact correction:** D4a #2–#5 and the D5 rows now define `call_wall`,
  `put_wall`, and `dominant_net_gamma` as always-present
  `{strike: number|null, gex_1pct_usd: number|null, reason: string|null}`
  objects — `reason: null` when available; stable explicit reason tokens
  when unavailable (`no_eligible_calls` / `no_nonzero_call_gex`,
  `no_eligible_puts` / `no_nonzero_put_gex`, `all_net_gamma_zero`) with
  null metrics; never a bare `null`, never a fabricated strike. The metric
  field name is unified to `gex_1pct_usd` (replacing `call_gex_1pct_usd` /
  `put_gex_1pct_usd` / `net_gex_1pct_usd`); the available put-wall value
  keeps its native negative sign. `zero_dte` is frozen as
  `{share: number|null, abs_gex_0dte_1pct_usd: number,
  abs_gex_total_1pct_usd: number, observation_trading_date, per_root:
  {SPX: {abs_gex_0dte_1pct_usd, contracts}, SPXW: {…}}, caveat,
  reason: string|null}` (renaming the old `abs_gex_1pct_usd` /
  `denominator_abs_gex_1pct_usd`), with reason token
  `"zero_abs_gex_denominator"` on the zero-denominator case.
- **Test/requirement consequence:** R24 (no non-zero calls), R25 (no
  non-zero puts), R26 (fully cancelling net strikes), R27 (uniform
  always-present construction + unified field name) added; R22
  strengthened to assert the intact object + reason token.
- **HELM cut applied:** none under this item.

### F6 — Provenance must be exhaustive with five explicit classes (§4 D5)

- **ACCEPTED.**
- **Exact correction:** the D5 provenance block and `provenance` schema
  row rewritten to the five classes CONFIGURED / OBSERVED / REPORTED /
  DERIVED / INFERRED, exhaustive over every emitted top-level field:
  endpoint/source/schema_version/units/contract_multiplier/underlying/
  roots → CONFIGURED; provider feed facts (per-contract gamma and
  open_interest as inputs, spot, feed_timestamp_utc) → OBSERVED with
  `fetched_at_utc` explicitly identified as locally observed (producer
  clock, not a provider fact); the ~15-minute delay posture (`data_delay`)
  → REPORTED; all coverage counts/summaries, net GEX, walls,
  dominant_net_gamma, 0DTE share, and unavailable reason tokens → DERIVED
  (the prior draft's classification of coverage counts as OBSERVED is
  named and corrected); `sign_convention` (and the model_label
  interpretive layer) → INFERRED.
- **Test/requirement consequence:** R37 (provenance exhaustive, five
  classes, coverage under DERIVED, fetched_at_utc locally-observed) added.
- **HELM cut applied:** none under this item.

### F7 — Proxy tests; every named mutation must be killed by construction (§6)

- **ACCEPTED.**
- **Exact correction:** R7 split into three named tests (missing
  `options` / `current_price` / `timestamp`); R14's fixture now makes the
  call-GEX winner distinct from BOTH the call-OI winner AND the net-GEX
  winner (test renamed `test_call_wall_uses_call_side_gex_not_oi_not_net`);
  R17's fixture includes a negative-net winner larger in absolute value
  than the largest positive and distinct from the call wall; R19's fixture
  mixes calls and puts so the signed and absolute 0DTE numerators differ
  (test renamed `test_zero_dte_numerator_today_only_absolute`); R23 uses
  the actual Cboe timestamp shape across the UTC/ET boundary (F4); R12
  frozen as the exhaustive forbidden raw-chain key/container guard (D8's
  enumerated set — bid, ask, bid_size, ask_size, iv, theo, delta, gamma,
  theta, vega, rho, volume, last_trade_price, last_trade_time, open, high,
  low, close, prev_day_close, change, percent_change, tick, option,
  open_interest — plus any per-contract row container), no longer a
  `top_strikes`-cap check; and every F3–F6 validation rule received its
  own named red test with the mutation that turns it red (R24–R37). The
  R-table is extended coherently R1–R37, every row in PRD-198 invariant-4
  form; §7's test-file row updated to "R1–R37 suite".
- **Test/requirement consequence:** this item IS the test consequence —
  rows R24–R37 added; rows R7, R12, R14, R16, R17, R19, R22, R23
  strengthened or rewritten.
- **HELM cut applied:** R12's former `top_strikes ≤ 10` clause dropped as
  part of the top_strikes removal — the guard is now purely the
  forbidden-key/container check.

### Recommended 1 — Broken decisive-negative command in the Event-1 charge

- **ACCEPTED.**
- **Exact correction:** `CODEX_REVIEW_PROMPT_2026-08-20.md` line
  `rg -niE "gex|gamma" cuttingboard/` replaced with
  `rg -ni 'gex|gamma' cuttingboard/`; the packet's §5 seam-trace table now
  cites the corrected `rg -ni 'gex|gamma' cuttingboard/` (exit 1) — the
  exact command the Event-1 reviewer actually ran — instead of the old
  `grep -rniE "gex\|gamma"` form. §0's new consumer-enumeration leg cites
  the same corrected command.
- **Test/requirement consequence:** none (charge/citation hygiene).
- **HELM cut applied:** none under this item.

### Recommended 2 — `roots` gets its own schema row

- **ACCEPTED.**
- **Exact correction:** D5's `underlying` row split: `underlying` =
  `"_SPX"` (CONFIGURED endpoint scope) and a new dedicated `roots` row =
  `["SPX","SPXW"]`, identified as the CONFIGURED admissibility allowlist
  that D6 enforces.
- **Test/requirement consequence:** covered by R1 (schema completeness)
  and R32 (allowlist enforcement).
- **HELM cut applied:** none under this item.

### Recommended 3 — `python3` consistently

- **ACCEPTED.**
- **Exact correction:** §11's validation line now reads
  `python3 tools/validate_prd_registry.py --skip-commit-resolvability`
  (the packet's only bare-`python` occurrence).
- **Test/requirement consequence:** none.
- **HELM cut applied:** none under this item.

### Recommended 4 — Rename `dominant_gamma` → `dominant_net_gamma` everywhere

- **ACCEPTED.**
- **Exact correction:** renamed in D4 (aggregation bullet prose), D4a #4
  (definition heading, object name, and unavailable form), D5 (schema
  row), the D5 provenance DERIVED list, §6 R16/R17 (rows and test names
  `test_dominant_net_gamma_ignores_cancelled_strike` /
  `test_dominant_net_gamma_max_abs_net`) plus new rows R26/R27, §9 (intro
  and Q9), and the §10/§12 status prose; §12's historical mention is
  marked superseded by the addendum rather than rewritten. The persisted
  field name keeps the NET semantic explicit.
- **Test/requirement consequence:** R16/R17 test names updated; R26 named
  on the new field.
- **HELM cut applied (recorded here for locality):** independent of the
  Codex findings, HELM cut generic `top_strikes` from GEX-1 v1 entirely —
  removed from D4 (definition), D5 (schema row), the provenance DERIVED
  list, D8 (guard rephrased onto the five scalar outputs + exhaustive
  forbidden-key check), §6 R12 (cap clause dropped), and §9 Q1 (extra
  aggregation shape ruled OUT for v1; strike profile / top-N / heatmap is
  additive future work only if the first slice proves useful). The five
  P0 structural outputs are the whole v1 aggregation surface. The LOC
  ceiling was re-estimated bottom-up in §8 (≤ 420 → ≤ 400, arithmetic
  shown): the cut removes more than the frozen F3–F6 validation adds.

```
PROVISIONAL MATERIAL PACKET — DESIGN ONLY — EVENT-1 COMPLETE, CORRECTION APPLIED — AWAITING EVENT-2 EXACT-CORRECTED-HEAD CONFIRMATION — NO IMPLEMENTATION AUTHORITY.
```
