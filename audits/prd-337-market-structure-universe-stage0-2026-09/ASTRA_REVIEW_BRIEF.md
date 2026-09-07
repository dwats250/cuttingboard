# Market Structure Universe v1 — Astra review brief and implementation plan

Status: PROVISIONAL MATERIAL PACKET — READY FOR FABLE REVIEW, not implementation authority.
Date: 2026-09-06 PT. Authoring context: Codex/Astra session with same-session
read-only recon helpers; no independent review is claimed.

**Goal:** Separate personal attention from market measurement while preserving the
existing observation-only boundary, before NS-4C Leadership.
**Architecture:** One human-authored registry, explicit roles and benchmark
relationships, separate deterministic projections, one evolved observation carrier.
**Tech stack:** Existing Python frozen dataclasses, JSON, yfinance and pure HTML delivery.
**Handoff:** Fable 5.1 reviews this packet in a fresh session. Opus implements only
the accepted, authorized design in a second session on this persistent lineage.
No execution of this plan is commissioned in the Astra session.

## 1. Basis, identity and authority

- Inspected branch: `claude/prd-337-ns4c-leadership-v0`.
- Inspected local and origin head: `5612c3690109dbd6bbee72b4497d5a3ce105879a`.
- Fetched main: `f87bda756314f47ea9de341ebe26b6512e8cb4c2`.
- Persistent worktree: `/home/dustin/Projects/cuttingboard/.claude/worktrees/prd-337-ns4c-leadership-v0`.
- Draft PR #325 initially contains only the original owner-ratification sheet;
  there is no `docs/prd_history/PRD-337.md` at the inspected head.
- Dustin's current charge supersedes that sheet's 12-row proposal, categorical
  thresholds, and suggestion that benchmark-table approval alone starts work.
  The direction is approved; the exact proposals below are not ratified membership.
- MATERIAL under GOV-2 §1: runtime/delivery/persistence seam and schema evolution.
  This packet enters upstream review; it grants no Gate A. The requested
  Fable review is not represented as completion of GOV-2's Codex review and
  exact-corrected-head confirmation events. Record independent review evidence,
  substantive dispositions and exact SHA; reconcile reviewer-seat requirements
  with Helm before any downstream implementation authorization.
- Sequence: **NS-4A v2 / Market Structure Universe → NS-4C Leadership → NS-4D Breadth**.
  Existing PRD-308/311 ceilings do not authorize this expansion. Retain their
  historical records; state intentional successor changes in the eventual PRD.

## 2. Current architecture and load-bearing evidence

All source locations below refer to the inspected head, not proposed code.

| Disposition | Evidence and reachability | Failure behavior / falsifier |
|---|---|---|
| CONFIRMED | `universe_registry.py:40–74`: frozen six-field records, 12 enabled rows; `watchlist_sidecar.py:26,41–66` is its sole production importer and projects every enabled row | Changing enabled/rationale changes projection; `tests/test_universe_registry.py:117` guards importer boundary |
| CONFIRMED | `watchlist_sidecar.py:69–104`: emits schema 2, source `watchlist`, every expected row, one-decimal daily percentage and capture clock | Missing quote produces null, not zero; naive clock raises; does not establish quote observation freshness |
| CONFIRMED | `movement_card.py:25–38,113–160`: expected identity already derives from producer; schema/source, exact set, group and index checks; fixed five-group vocabulary | Missing/extra row, bad group/index or invalid numeric type suppress whole card. Missing daily-change key currently becomes null via `.get`; tighten in v3 |
| CONFIRMED | `runtime/__init__.py:805–815,2797–2830`: hourly non-HALT branch, separate best-effort fetch, new mapping passed only to writer | Observe fetch failure yields null cell; HALT skips observation fetch/write; atomic replacement on success. A spy seeing observation extras in validation falsifies isolation |
| CONFIRMED | `config.py:269–288`, `ingestion.py:77–85`: ALL_SYMBOLS independently authored; observation tuple is UCO/GOOG | Registry roles must never populate ALL/REQUIRED/HALT or other decision universes |
| CONFIRMED | `dashboard_renderer.py:3589–3610,4310`: loads carrier, resolves card, displays coverage and movement in MARKET STRUCTURE | Invalid/absent carrier hides card but retains `PARTICIPATION: not captured`; coverage is availability, not breadth |
| CONFIRMED | `delivery/market_state_panel.py:82–102`: another presentation helper consumes resolved MovementCard, not JSON | Dynamic usable/total count and capture clock; keep group/chip interface compatible |
| CONFIRMED | `tests/test_ci_artifact_hygiene.py:867–876`, hourly workflow: watchlist carrier is run-local, neither restored nor staged | Existing hygiene test fails if restore/stage is introduced; do not mistake local JSON for a published independent artifact |
| NARROWED | Existing `tests/test_observe_only_isolation.py:91–122` exercises runtime validator/writer seam | Empty main quotes and mocked downstream work are not exhaustive decision-output proof; require paired executable runs below |

Author baseline: 80 tests passed (registry, sidecar, movement, observation isolation,
market-state panel), 3.50s, using the shared venv with package resolution confirmed
inside this worktree. No live quote-provider timing or rate-limit experiment was run.
This baseline verifies existing behavior only; it does not validate this design.
Documentation checks: `git diff --check` passed; PRD registry validator exited 0
with historical unresolvable-commit notices for PRD-139/158/161/167/168/169/208/
213–220/222. Validator and registry inputs are unchanged from the inspected head;
no historical cleanup was attempted. Full suite and live provider trial were not run.

## 3. Problem and smallest model

The legacy registry conflates attention, measurement and display grouping. It
omits ten sectors, labels META/AMZN/GOOG TECH, excludes AAPL because of an older
personal selection, and retains TSLA by history. Merely enlarging WATCHLIST_SYMBOLS
would preserve the semantic error. Movement admission is already exact-projection
based; replace the projection contract, not strict acceptance with arbitrary sets.

Retain `UniverseInstrument` and its six fields; add exactly:

```python
roles: tuple[str, ...]       # immutable, unique, closed vocabulary
benchmark_symbol: str | None  # literal owner-authored relationship; no inference
```

Five proposed roles: `PERSONAL`, `MARKET_STRUCTURE`, `CROSS_ASSET`,
`SECTOR_BENCHMARK`, `LEADERSHIP_CONSTITUENT`. PERSONAL means attention only.
Do not add a TRADE role: `trade_eligible` already exists and remains inert registry
metadata, independent of attention and measurement. Do not add unused MACRO or
MEGA_CAP roles; describe selected mega-cap constituents honestly in rationales.
Neither roles nor benchmark fields may be read by a decision module.

Retain `functions` and its UCO `crude_proxy` meaning. Re-scope `primary_group`
explicitly to display: `MARKET`, `SECTORS`, `REAL_ASSETS`, `LEADERS`, `PERSONAL`.
No sector classification field is needed for this card: the reviewed membership
table and human-authored rationales carry constituent sector descriptions.
`enabled` is observation activation only, never trading activation.

Preserve all existing rows' `trade_eligible` values, including disabled TSLA.
Propose False for new registry rows (including AAPL), meaning no new eligibility
grant; AAPL's already-existing config membership remains untouched. This mismatch
is deliberate evidence that the registry is not the trading authority.

## 4. Proposed bounded membership and explicit benchmark map

Exactly **22 measurement symbols**, in display order. `MS` below means
MARKET_STRUCTURE. Relationships are proposals for explicit ratification, never
inferred by a category rule at runtime.

| Symbol(s), exact order | Group | Roles beyond MS | Benchmark, explicitly for each listed symbol | Measurement job |
|---|---|---|---|---|
| SPY | MARKET | none | null | broad equity anchor; no meaningless self-zero |
| QQQ | MARKET | none | SPY | Nasdaq-heavy growth relative to broad equity |
| XLK, XLF, XLE, XLI, XLY, XLP, XLV, XLU, XLB, XLRE, XLC | SECTORS | SECTOR_BENCHMARK | SPY for each of these 11 entries | full sector ETF foundation, not constituent breadth |
| GLD | REAL_ASSETS | CROSS_ASSET | null | gold anchor; no unsupported gold-vs-equity product question |
| SLV | REAL_ASSETS | CROSS_ASSET | GLD | silver relative to gold |
| GDX | REAL_ASSETS | CROSS_ASSET | GLD | gold-mining equities relative to gold exposure |
| AAPL, MSFT, NVDA, META, AMZN, GOOG | LEADERS | LEADERSHIP_CONSTITUENT | QQQ for each of these six entries | selected large-growth constituents, not a sector sample or breadth proxy |

Constituent jobs: AAPL consumer-device ecosystem; MSFT enterprise software/cloud;
NVDA semiconductors/AI infrastructure; META social advertising; AMZN commerce/cloud;
GOOG search/advertising/cloud. AAPL/MSFT/NVDA are Technology; META/GOOG Communication
Services; AMZN Consumer Discretionary. QQQ is a common growth-relative question,
not a claim of sector-relative performance. Explicit sector benchmarks could
replace individual rows only through owner-authored changes.

The issuer's [full sector suite](https://www.ssga.com/us/en/intermediary/capabilities/equities/sector-investing/select-sector-etfs)
confirms all 11 labels: Technology, Financials, Energy, Industrials, Consumer
Discretionary, Consumer Staples, Health Care, Utilities, Materials, Real Estate,
Communication Services (XLC). Source checked during this session; no holdings
weights or quote freshness are inferred from it. Constituent classification also
follows the binding owner direction in the charge.

Proposed PERSONAL projection: legacy attention membership minus TSLA =
`SPY QQQ GDX GLD SLV XLE UCO NVDA META AMZN GOOG` (11).
This is an explicit continuity proposal, not evidence that Dustin currently
actively trades all 11. AAPL/MSFT are measurement-only. UCO retains PERSONAL and
`crude_proxy`, group PERSONAL, null benchmark: leveraged crude exposure earns no
additional measurement slot beside the existing macro oil context and XLE.
TSLA remains as a disabled historical registry record with empty roles, null
benchmark and group PERSONAL; its unrelated existing runtime membership is preserved.
Thus 24 total registry rows, 23 enabled observation rows, 22 movement rows, 11
personal rows. Do not add IWM, USO, PAAS or other legacy runtime symbols by inference.

## 5. Projections and observation wiring

Keep the registry's sole direct production importer as `watchlist_sidecar.py`.
It becomes the observation-projection adapter despite its legacy module name:

```text
WATCHLIST_SYMBOLS       = enabled rows with PERSONAL
MARKET_STRUCTURE_SYMBOLS = enabled rows with MARKET_STRUCTURE
OBSERVATION_SYMBOLS     = ordered union of those projections, deduplicated
```

Define projections as immutable symbol tuples; snapshot metadata is projected by
the same adapter. Do not preserve the misleading legacy five-tuple public shape
under the same meaning. Update its named local consumers/tests atomically.
Registry insertion order is serialization only, never rank. Measurement rows
follow table order; UCO follows as personal-only. Disabled TSLA is not serialized.

Move observation fetch membership out of config's hardcoded tuple. Runtime imports
the observation projection from the existing sidecar adapter and derives a local
ordered tuple at the fetch seam:

```python
observe_only = tuple(s for s in OBSERVATION_SYMBOLS if s not in config.ALL_SYMBOLS)
```

No config → sidecar import (normalization already imports config); avoid that
cycle. Remove only `config.OBSERVE_ONLY_SYMBOLS` and its stale comment; do not
change ALL_SYMBOLS, REQUIRED_SYMBOLS, HALT_SYMBOLS, NON_TRADABLE_SYMBOLS, source
priorities, price bounds, trend universe or any unrelated config list.
Validate the projection is disjoint from decision/protected sets at the seam;
fail within the best-effort observation boundary if that invariant is violated.
Admit returned quotes only for requested keys with matching quote.symbol. Filter
the fetched mapping to observe_only before merge so a malformed injected result
cannot overwrite SPY or another existing quote. Keep `normalized_quotes` unchanged.
Never retry a missing ALL_SYMBOLS quote through the observation path: null is honest.

At this base, extra fetches are exactly
`XLK XLF XLI XLY XLP XLV XLU XLB XLRE XLC MSFT GOOG UCO` (13).
AAPL is already in ALL_SYMBOLS; it adds no fetch or decision membership.
Preserve hourly/non-HALT gating, daily/Sunday behavior and run-local atomic write.
No new persistence, scheduler, provider, credential or publication channel.

## 6. Carrier evolution and fail-closed admission

Keep `logs/watchlist_snapshot.json`, writer/loader names and path for minimal
transport churn. Document it as the **observation universe snapshot**, not a
personal-only watchlist. Use schema **3** (one justified bump for changed membership,
roles and row semantics), source `observation_universe`.

```text
top-level exact keys: schema_version, source, generated_at, symbols
row exact keys: symbol, roles, benchmark_symbol, primary_group, registry_index,
                rationale, current_price, daily_change_pct
```

Replace obsolete `sector_theme`/`watch_reason` with honest rationale; serialize
roles as an ordered JSON list. `registry_index` means contiguous position in the
enabled observation union, not original registry position or ranking.
Every expected row exists even when quote unavailable. Preserve current one-decimal
daily change, null and zero semantics; no relative calculation. Benchmark is
persisted as authored metadata to make future snapshot context explicit.

Consumer requires exact v3/source identity, exact expected observation key set,
exact row key sets and exact identity metadata against the current projection
(roles, benchmark, group, rationale, index). Reject bool-as-int, duplicate indices,
unknown role/group, missing required fields and unapproved injected rows. Validate
price as finite positive float-or-null and daily change as finite float-or-null;
missing keys are invalid, explicit null is available-state metadata. Require
valid aware capture timestamp. Do not claim capture time is observation time.
Validate human-authored registry duplicates, closed vocabularies, role combinations
and benchmark closure before projecting: each non-null benchmark must be an enabled
measurement member; forbid self-comparisons and cycles. Anchors are explicit null.
SECTOR_BENCHMARK/CROSS_ASSET/LEADERSHIP_CONSTITUENT require MARKET_STRUCTURE.

After full carrier validation, render only MARKET_STRUCTURE rows. A valid
personal-only row cannot enter card groups or coverage denominator. Bad envelope
or metadata suppresses whole card; an explicit unavailable quote renders `n/a`.
Keep MovementCard.groups/captured_et interface and chip suffix ` n/a` stable.
Coverage must become 22/22, 21/22, etc., never 23/23 or a breadth statistic.

Compatibility is coordinated writer/consumer cutover: v3 reader rejects v1/v2;
v2 reader rejects v3; no reinterpretation or fallback. Stale membership under the
same version fails exact projection identity. Existing run-local transport makes
an extra artifact or dual writer unnecessary. An unavailable producer suppresses
the card; retain the visible `not captured` coverage notice. Existing same-process
old-file behavior on writer failure is a known risk, not solved by a schema bump;
do not add restore or claim new freshness guarantees.

## 7. Dashboard consequences

Keep MARKET MOVEMENT within existing MARKET STRUCTURE context. Four ordered rows:
MARKET, SECTORS, REAL ASSETS / METALS, LEADERS (display label `SELECTED LEADERS`).
LEADERS is a static basket label, not a computed leading verdict. No PERSONAL
dashboard card is proposed. Keep compact monospace chips, signed absolute daily
percentages, honest n/a and existing capture clock. No sorting by returns.

Eleven sector chips must wrap at ordinary chip boundaries at 360×780 and 390×844;
also inspect desktop 1440×900, full/partial/all-null/rejected snapshots and coverage.
Any CSS change stays inside movement rendering or the renderer's existing CSS.
No layout reskin, new ranking, badges, score, notification change or sideways overflow.

Future NS-4C is numeric only: `relative_daily_move = symbol.daily_change_pct -
benchmark.daily_change_pct`, in percentage points. Future output must name the
benchmark (`NVDA +1.4 vs QQQ`, `XLK +0.8 vs SPY`, `GDX +1.2 vs GLD`) and suppress
anchor/self comparisons. Arithmetic, rounding policy for relative values, pair
observation-time admission and that renderer belong to NS-4C, not this precursor.

## 8. Provider cost, risks and unresolved questions

`ingestion.py:333–382` uses sequential per-symbol yfinance attempts;
`config.py:248–250` sets three attempts, 2s backoff, 10s timeout. `fast_info`
properties (`ingestion.py:390–409`) may entail multiple internal HTTP requests;
symbol count is not HTTP request count. Thirteen extra-path symbols versus two is
6.5× the existing loop: nominal timeout-heavy budget 13×(3×10+2×2)=442s versus
68s, before overhead. This is **not a hard upper bound**: `_run_with_timeout`
(`ingestion.py:616–623`) exits a ThreadPoolExecutor context that waits for a running
worker. Actual elapsed time can exceed the configured timeout substantially.

The naive expanded loop is fragile under provider slowness/rate limiting. Preserve
the existing path for this design; do not imply operational readiness. Opus must
record controlled failure/slow-worker timing and a bounded live observation trial
before rollout. If acceptable elapsed-time behavior cannot be demonstrated, STOP
for a separately scoped acquisition correction or owner narrowing of membership.
No timeout fix or concurrency redesign is smuggled into this file fence.

Other open items for review/owner ratification: six versus fewer selected leaders;
continuity PERSONAL set; common QQQ benchmarks versus explicit sector benchmarks;
acceptance of schema-3 transition and strict whole-union admission; registry's inert
trade_eligible terminology; capture-time-only carrier versus future NS-4C pair
freshness requirements. These do not prevent Fable review. They prevent treating
this provisional table as an approved implementation contract.

## 9. Proposed file fence and executable proof plan

**ESTIMATED SURFACE — NOT YET APPROVED.** Six production files, no new module:

1. `cuttingboard/universe_registry.py`: roles, benchmarks, authored rows/groups.
2. `cuttingboard/watchlist_sidecar.py`: validated projections and v3 producer.
3. `cuttingboard/config.py`: remove obsolete observation tuple only.
4. `cuttingboard/runtime/__init__.py`: derive/filter extra fetches at existing seam.
5. `cuttingboard/delivery/movement_card.py`: v3 admission, measurement-only groups.
6. `cuttingboard/delivery/dashboard_renderer.py`: bounded label/wrapping integration;
   retain coverage semantics and location, reduce fence if no change is needed.

Six test files to modify:
`tests/test_universe_registry.py`, `tests/test_watchlist_sidecar.py`,
`tests/test_movement_card.py`, `tests/test_observe_only_isolation.py`,
`tests/test_dashboard_renderer.py`, `tests/test_market_state_panel.py`.
No new test file is necessary. Update only relevant sections of
`docs/universe_taxonomy.md`, `docs/artifact_flow_map.md`, `docs/SCHEMA_MAP.md`,
`docs/CALL_SITE_MAP.md`. Eventual PRD and its required registry/index/review records
are a separate governed authorization step, not permission for project-state cleanup.
Estimate 200–350 net production LOC and 250–450 net test LOC; review these estimates
before setting Gate A limits. No ingestion.py, workflow, decision-contract or
notification edits are authorized by this proposed fence.

Required tests (assert the approved literal set as well as derivation, so shared
producer/consumer mistakes cannot silently redefine expected truth):

| File | Discriminating assertions |
|---|---|
| test_universe_registry.py | Exact 24/23/22/11 populations; all 11 sectors including XLC; TSLA disabled; AAPL measurement not personal; UCO personal not measurement; all benchmark literals; preserve legacy trade flags; new rows False; duplicate/unknown/disabled benchmark/cycle rejected; sole importer remains sidecar |
| test_watchlist_sidecar.py | Role mutation changes only correct projection; deterministic order/serialization; overlapping roles yield one row; metadata and exact v3 keys; null missing quote, genuine zero, no unrequested quote row; legacy theme absent |
| test_movement_card.py | v1/v2 and wrong source rejected; missing/extra/injected personal-to-market row rejected; missing daily key distinct from null; bad bool/index/NaN/Inf/metadata rejected; 22 chips, 4 groups, no UCO/TSLA, stable order; all-null accepted honestly |
| test_observe_only_isolation.py | Exact derived 13-fetch set and no ALL_SYMBOLS retry; mismatched quote identity and injected SPY discarded; success, partial failure, all failure and thrown fetches; no mutation of original quote mapping; HALT/daily/Sunday absence |
| test_dashboard_renderer.py | Valid v3 makes 22/22 coverage, one unavailable makes 21/22, all-null 0/22; bad/missing snapshot preserves not-captured notice; no personal denominator; baseline-neutral outside observation region; rendered mobile/desktop checks |
| test_market_state_panel.py | Resolved 22-row model yields correct dynamic total/partial/unavailable coverage; no new raw JSON reader, clock or breadth |

Isolation must be executable, beyond source order: paired runs with identical
non-empty decision fixtures and fixed clock, observation fetch absent versus
extreme-valued successful extras. Spy/capture inputs at validate_quotes, valid
quote construction, derived/structure, regime, candidates and qualification;
compare final contract permission, ranked candidates, execution-related fields,
notification content/counts and RunResult. All must be identical, with none of the
new-only symbols present. Repeat with partial/all failures and thrown exceptions.
Do not remove real downstream stages from the paired end-to-end comparison.
Assert ALL/REQUIRED/HALT/NON_TRADABLE/TREND lists equal frozen pre-change values.
The falsifier is any extra key or changed decision result attributable to observation.
Perform a controlled red mutation routing extras into normalized_quotes; the
isolation test must fail. Also mutate an omitted XLC and a permissive acceptance
guard; their targeted tests must fail. Restore mutations before final validation.

Run targeted tests above plus `tests/test_runtime_decision.py`,
`tests/test_ci_artifact_hygiene.py`, `tests/test_config.py`, `tests/test_phase1.py`,
`tests/test_intraday_bars_sidecar.py`, `tests/test_hourly_alert.py` as unchanged
regressions. Existing artifact-hygiene assertions must pass without weakening.
Then run `ruff check .`, `python tools/validate_prd_registry.py`, and `pytest -q`
using the repository venv. Confirm package resolves to the persistent worktree.
Any unexplained failure or needed file outside the approved fence is STOP/renewal.
Record exact head and CI separately; docs-only CI does not validate proposed logic.

## 10. Proposed implementation sequence (Opus, after authority)

- [ ] Complete Fable adversarial review; disposition findings in one correction,
  pin the corrected head, obtain applicable independent confirmation and owner
  membership/benchmark direction, reviewed successor PRD and explicit Gate A.
- [ ] Freeze decision baselines and add failing literal-membership/projection and
  runtime isolation tests. Prove they discriminate before production edits.
- [ ] Extend registry and sidecar together; validate roles/benchmark graph, derive
  projections and emit the exact v3 envelope. Pass producer/registry tests.
- [ ] Replace config's observation tuple with runtime-side derivation and guarded
  fetch-result filtering; keep copy-only merge and non-HALT hourly seam. Pass
  failure-path and paired decision-invariance tests.
- [ ] Cut movement admission to v3 and measurement-only rendering; update dashboard
  and resolved-card tests together. Check rejection paths and null coverage.
- [ ] Capture full/weak-state desktop and mobile browser evidence in this persistent
  worktree; verify wraps, no overflow, no personal rows or implied breadth.
- [ ] Update only four named maps/taxonomy sections. Run targeted → ruff → registry
  validator → full suite, required red mutations and provider timing assessment.
- [ ] Commit/push on this lineage or an explicitly chosen successor, obtain fresh
  adversarial exact-implementation-head review, return to Dustin. Never merge.

## 11. OUT OF SCOPE

NS-4C arithmetic/rendering or categorical LEADING/INLINE/LAGGING thresholds;
NS-4D breadth; persistence/rotation/history scores; predictions/recommendations;
composites/ranking; trade eligibility changes; decision/regime/qualification/
permission/execution behavior; provider/channel changes; ingestion redesign;
new snapshots; workflow restore/staging; personal dashboard expansion; broad
documentation cleanup; generated production dashboards; merge or auto-merge.

## 12. Fable review questions

1. Is the five-role model minimal, or is CROSS_ASSET redundant with display grouping?
2. Does any field accidentally gain decision semantics, particularly trade_eligible?
3. Is the personal/measurement split structurally clear, including carrier union?
4. Is 22 a defensible bounded universe; do all six constituents earn a slot?
5. Is the full 11-sector set correct, including XLC and XLRE?
6. Are selected constituent labels honest about their actual sectors and limitations?
7. Are explicit QQQ/SPY/GLD relationships defensible, and are null anchors preferable?
8. Does the observe-only projection remain isolated through runtime and final outputs?
9. Is schema 3 deterministic and fail-closed without unnecessary persistence?
10. Can exact projection validation replace legacy assumptions without becoming permissive?
11. Is there any hidden path into decision authority, including imports and quote collisions?
12. Is any NS-4C or NS-4D calculation or interpretation leaking into this precursor?
13. Is the provisional implementation fence small enough and complete for real consumers?
14. Which adversarial tests above are insufficient; what exact additional falsifiers
    must Opus pass, particularly non-empty end-to-end decision fixtures?
15. Is the 13-symbol sequential fetch exposure acceptable for a rollout trial, or
    must a separately authorized timing correction precede it?
16. Does whole-union rejection impose needless personal-data coupling on measurement,
    or is exact single-carrier admission the smallest coherent initial contract?

Requested review output: SHA-pinned findings with severity/taxonomy, file/section
evidence and concrete falsifiers; fresh-context independence statement; no review
of another review's prose and no production edits. READY FOR FABLE REVIEW means
the provisional packet is ready to challenge, not review-clean or merge-ready.
