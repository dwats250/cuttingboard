# PRD-337 precursor — adversarial exact-head implementation review

## 1. EXACT HEAD REVIEWED

`0b5bd551bedcf88dde8097cf78ba38cebffbdd55`

Base: `faa5d7fdeec08f4f17ab81a48a2447ffa9766c35`.
Branch: `claude/prd-337-ns4c-leadership-v0`. PR: #325, OPEN and DRAFT.
Review date: 2026-09-06 America/Vancouver (CI timestamps are September 7 UTC).
Reviewer: commissioned Astra counter-model review, Codex harness.

Fresh-context independence: this session did not author the implementation or
design. One implementation findings pass, against the named diff and the
owner-designated `FABLE_REVIEW.md` contract. Fable's record was read as the
commissioned design authority, not as an implementation verdict to endorse.
No production or test source was modified. Checks used the persistent worktree
only; no clone, scratch repository, or temporary worktree was created. Local
discriminating probes modified Python objects in memory, intercepted writes and
notification delivery, and made no provider requests. This report is the only
new repository artifact authorized for packaging by the root orchestrator.

## 2. VERDICT

**REQUIRED CHANGES**

The 22-symbol measurement model and current-run quote-data isolation are
technically sound at this head. The required whole-helper failure experiment
is not equivalent to the supplied per-symbol failure tests: it exposes a path
that sends a second notification and replaces successful hourly artifacts with
failure/HALT. The deadline boundary and the authority-regression proof also
need correction. Governance remains independently held by Helm.

## 3. FINDINGS

### R1 — REQUIRED — Observation helper exception reaches the run failure handler

Taxonomy: **hidden coupling**.
Seam: `cuttingboard/runtime/__init__.py:815-818`, outer exception handler
`:876-930`; `tests/test_observe_only_isolation.py:339` paired-run test.

The helper call is evaluated before `_write_watchlist_snapshot` is entered.
The writer's exception handler therefore cannot contain a helper exception.
Per-symbol fetch/normalization exceptions are caught at `:2860-2864`, but that
does not establish the unconditional "NEVER raises" contract for the complete
observation boundary. Fable section 3.10 explicitly specifies a helper that
raises `RuntimeError` as case C.
The call-site/outer-handler exposure is inherited, not a newly introduced
exception mechanism; it remains unclosed despite the new explicit C contract.

Discriminating evidence: an in-memory invocation of `_execute_notify_run` used
the existing six-quote `_real_stage_fixture`, real validation, regime, derived,
router, and decision stages; provider/bar inputs and external writes were
intercepted. `_write_hourly_artifacts` recorded attempted status/outcome writes;
`send_notification` recorded calls. Only the observation helper's response
changed:

| Observation response | Returned status | Notification calls | Hourly status/outcome write sequence |
|---|---|---|---|
| `{}` | SUCCESS | 1 | SUCCESS / NO_TRADE |
| All 12 extreme quotes | SUCCESS | 1 | SUCCESS / NO_TRADE |
| 11 quotes, XLK absent | SUCCESS | 1 | SUCCESS / NO_TRADE |
| `raise RuntimeError("review C sentinel")` | FAIL | 2 | SUCCESS / NO_TRADE, then FAIL / HALT |

These are intercepted calls, not real messages or disk overwrites. This probe
establishes the exception propagation; it is not a substitute for persisted
byte-comparison tests. Ordinary partial provider failures are already contained.

Human surface: **DEGRADED** — failure notification at `runtime:886` and replacement
hourly artifacts at `:929`; the original successful decision is misrepresented
after an auxiliary failure. No observation symbol leakage into the decision
quote mappings was found.

Smallest correction: put helper evaluation inside a local best-effort exception
boundary at the existing hourly watchlist seam, log the failure, and continue
with no extras. Preserve the primary mapping and earlier artifacts. Add C to
the existing real-stage paired regression, asserting identical notification,
all four decision files, returned result, and unchanged validation keys. The
writer must still receive the primary quotes when extras are unavailable.

### R2 — REQUIRED — Exact-deadline start and ambiguous timing guarantee

Taxonomy: **hidden coupling / factual drift**.
Seam: `runtime/__init__.py:2808-2827,2849-2859`;
`tests/test_observe_only_isolation.py:160-184`;
`docs/universe_taxonomy.md:120-123`.

The check is `elapsed > 60.0`. A patched monotonic clock advanced by 30 seconds
per fetch produced request starts `[0.0, 30.0, 60.0]` and retained XLK, XLF, XLI.
Thus a request starts when the 60-second allocation is exactly exhausted. The
existing test explicitly blesses that boundary.

Authority distinction: this matches Fable's literal three-call test D and its
"exceeded" wording. It does not meet this review charge's stricter "no new
observation fetch starts once budget is exhausted" requirement. This is an
identified contract discrepancy, not an assertion that the builder silently
departed from Fable's test. The smallest correction under the current charge is
`>=`, with two starts at 0 and 30, retaining both results; test exact deadline
and just-over-deadline without sleeping.

The code calls this an "elapsed ceiling" and says the budget "bounds the seam".
It qualifies that it is not a hard per-symbol timeout, but should explicitly
state that total seam duration and next-slot delay remain unbounded when a call
hangs. The unchanged executor cleanup in `ingestion.py:616-623` can wait for the
worker indefinitely. No finite worst-case single-call duration has been proven.

Human surface: **DEGRADED** under a hang — delayed dashboard/A1-P completion and
potentially the next hourly alert through workflow concurrency. The current
run's already-written decisions remain intact while the call is stalled.

Smallest correction: fix the comparison and its test; describe this as a
subsequent-call start budget, explicitly retaining the in-flight-call/next-slot
limitation. Do not introduce executors, provider changes, or workflow changes.
Any demand for a genuine total wall-clock guarantee requires Helm's separate
scope decision; this review does not authorize it.

### R3 — REQUIRED — The no-reader regression can miss an authority reader

Taxonomy: **factual drift**.
Seam: `tests/test_universe_registry.py:182-194,208-219`.

The test scans all production Python files, not just a fixed list, but checks
only the literal text `.trade_eligible` and entirely skips every file with the
basename `universe_registry.py`. `permission = getattr(inst, "trade_eligible")`
does not contain that text and remains GREEN. An attribute reader added inside
the skipped registry also remains GREEN. The import guard is line-based and
is not an alias-aware structural proof.

Inspection of this exact head found no actual production reader: the registry
defines the field, only the sidecar imports the registry, and runtime/card
consume observation projections. **INERT** at the current human-facing surface;
this finding concerns the promised regression guard, not existing trading
authority leakage.

Smallest correction: use a small AST-based scan across production modules,
including the registry. Reject executable attribute loads and literal
`getattr`/mapping access to this field; inspect imports structurally, allowing
only the sidecar registry dependency. Permit the dataclass declaration and
documentary text. Add synthetic source cases proving that direct, aliased-object,
helper/getattr, and registry-local readers turn RED. No general taint-analysis
framework or production refactor is requested.

### R4 — REQUIRED — F7 product question and self-weight caveat are absent from implementation docs

Taxonomy: **factual drift**.
Seam: `cuttingboard/universe_registry.py:42-45` and
`docs/universe_taxonomy.md:98-137`; Fable F7 / section 3.4.

The authored benchmark values are correct and inert, but the implementation
documentation only calls them future relationships. It does not carry F7's
explicit question (mega-cap movement with/against the growth complex it
dominates) or the warning that small spreads against QQQ partly compare the
constituents with themselves. Those explanations remain only in the design
review. **INERT** today, because nothing computes or renders comparisons.

Smallest correction: add a short paragraph or explicit canonical F7 reference
with the product question and self-weight limitation in the already-fenced
taxonomy documentation. Do not implement relative movement.

### N1 — NON-BLOCKING — Validation and handoff evidence require truthful reconciliation

Taxonomy: **factual drift**.
Exact-head CI is green, but the full local commands are not both green:
repository-wide Ruff has three pre-existing E741 errors; strict registry
validation exits 1 with 22 unresolvable historical commit notices. Their files
are unchanged from the review base. These do not identify a precursor code
regression and do not authorize unrelated fixes.

The live PR body still describes a design-only packet, says "No production logic
changed", and reports the old 80-test evidence. Browser-matrix and live-fetch
timing records were not present in the packet directory or PR body inspected.
They are unverified, not failed. Before a readiness handoff, the orchestrator
should reconcile the PR description and link existing exact-head evidence or
obtain the required bounded evidence. This review did not edit the PR body or
send a comment. The draft state must remain.

## 4. FABLE CONTRACT CHECKLIST

PASS/FAIL refers to each required correction F1–F9, with the above distinctions
between literal implementation conformance and complete acceptance.

| Correction | Result | Evidence / qualification |
|---|---|---|
| F1 monotonic observation budget | **FAIL** | Literal Fable stop-after-exceeded mechanism implemented; total-seam/next-slot assurance is not established, and current charge requires stopping at equality. R2. |
| F2 two booleans, no role ontology | **PASS** | Nine explicit dataclass fields; personal and market_structure only; closed display groups. |
| F3 minimal v3 carrier | **PASS** | Exactly five produced row fields; metadata excluded; schema 3 / source watchlist. |
| F4 exclude personal-only UCO from fetch/carrier | **PASS** | 22 measurement rows, 11 personal identities, 12 derived extras; UCO absent from all measurement consumers. |
| F5 five-file fence and chip-local nbsp | **PASS** | Renderer unchanged; plain-space model retained; only HTML inserts nbsp within chips. Browser matrix not independently verified. |
| F6 MEGACAPS semantics | **PASS** | MARKET/SECTORS/METALS/MEGACAPS; actual sector rationales, no ranking. |
| F7 benchmark map plus question/caveat | **FAIL** | Exact map PASS; implementation documentation incomplete. R4. |
| F8 pure import-time validator | **PASS** | Direct registry checks run before projections; duplicates, invalid groups/targets, self-reference/cycles rejected. Literal identity tests separately pin UCO/TSLA/populations. |
| F9 inert trade_eligible plus no-reader guard | **FAIL** | Values/docs/current no-reader inspection PASS; regression guard has concrete bypasses. R3. |

## 5. DECISION-ISOLATION RULING

**PASS for quote-data/decision-authority isolation at this exact head. FAIL for
whole-observation-boundary failure isolation (R1).** No BLOCKER symbol leakage
was found.

Actual flow: `fetch_all -> normalize_all -> validate_quotes` at `runtime:554-557`;
regime reads `validation_summary.valid_quotes` at `:574`; derived/router at
`:591-598`; structure/candidates/qualification at `:603-666`. All precede
notification `:703`, hourly contract/summary `:746`, and market-map write
`:774`. The only extra-quote call is `:816`, under non-HALT hourly gating.
It builds a NEW dictionary for the watchlist writer. Neither the primary
dictionary nor its normalized quote objects are mutated by this path. The
sidecar reads prices/changes without mutation. Later A1-P work reads the
already-built market map/history, not the merged watchlist mapping.

All five frozen decision lists retain their literal baseline values; TSLA
remains in HIGH_BETA/ALL_SYMBOLS despite its observation tombstone. Existing
primary symbols are not refetched. Only watchlist_sidecar imports the registry;
runtime imports its measurement symbols/builder and movement_card imports its
rows. Personal and benchmark projections have no downstream production reader;
trade_eligible has none at all. No new ranking, permission, execution,
notification count, NS-4C computation, NS-4D breadth semantics, persistence,
provider, or workflow behavior was added. Existing PARTICIPATION is capture
availability, not newly implemented breadth.

## 6. 60-SECOND BUDGET RULING

**Achieves A with an equality defect under this charge; does not achieve B.**

- Clock: `time.monotonic`, beginning immediately before the fetch loop after
  static disjointness validation. No wall clock/deadline mixing.
- Each iteration checks elapsed time before starting the synchronous fetch.
  At this head it stops only when elapsed is strictly greater than 60.
- Completed observations are retained; fetch/normalization failures are
  best-effort; expiry logs once and breaks without raising.
- No new executor lifecycle exists. The old fetch can block in executor
  shutdown. The next check cannot execute until that call returns.
- Therefore no total 60-second guarantee, no proven finite "60 seconds plus
  one call" numerical maximum, and no guaranteed removal of next-slot coupling.
  Conditional on a finite call duration L, exposure is approximately budget+L;
  L is not bounded by this code. Tests advance a fake clock, never sleep 60s.

Fable's concrete allowed implementation is this kind of start budget. Its
stronger timing assurance is not a consequence of that mechanism. This report
records the discrepancy for Helm rather than redesigning ingestion or treating
an estimated six-minute case as a hard upper bound. R2 is an in-fence correction
to the exact-deadline behavior and truth of the documentation.

## 7. DEVIATION RULING

**A/B versus C:** accept unit coverage for ordinary partial provider failure:
one symbol raises, later symbols remain, and the pure sidecar converts absent
quotes to null. The review's partial-map run also succeeds. However, Fable's
explicit whole-helper-raises C is different and fails as shown in R1. The
deviation does not close that requirement. Add that single discriminating
run-level case, with result comparison; do not require a redundant partial-map
ceremony. The existing A/B test compares four nonmissing durable files and
notifications and records real validation keys, but does not compare the full
return dictionaries and does not include Fable's helper-raises case. Its second
MonkeyPatch scope nests over the first spy; use separate contexts for the
expanded regression so captures remain independently attributable.

**M2:** ACCEPT existing guard. In-memory mutation of movement_card._EXPECTED to
include enabled personal-only UCO caused
`test_valid_artifact_renders_all_22_in_four_groups_in_order` to raise
AssertionError: the producer's 22-row snapshot is rejected. Separate literal
22-row producer tests prevent shared producer/consumer co-drift. No duplicate
test is required.

**M6:** ACCEPT existing guard for the stated mutation. Merging extras into
normalized_quotes before validate_quotes makes the real validation spy record
extra keys, violating the explicit disjointness assertion at the bottom of the
paired test. The faster merge-seam test also records validation input and
asserts disjointness. The six-quote fixture is nonempty and validation is real;
this is not merely a comparison of mocked decisions. This ruling does not claim
that these tests cover all later-stage mutations or the separate exception seam.

## 8. EXACT DERIVED OBSERVATION FETCH SET

```python
('XLK', 'XLF', 'XLI', 'XLY', 'XLP', 'XLV',
 'XLU', 'XLB', 'XLRE', 'XLC', 'MSFT', 'GOOG')
```

Derived at runtime import as the ordered MARKET_STRUCTURE_SYMBOLS projection
minus config.ALL_SYMBOLS. Deterministic; no mutation and no second authored
runtime symbol list. UCO/TSLA excluded. The ten already available measurement
symbols are SPY, QQQ, XLE, GLD, SLV, GDX, AAPL, NVDA, META, AMZN.

## 9. TEST / VALIDATION EVIDENCE

Local package resolution was printed by pytest and points to this persistent
worktree's `cuttingboard/__init__.py`, using the shared project venv.

| Check | Exact observed result |
|---|---|
| Focused local registry/sidecar/card/observation checks | **90 passed, 4 deselected in 0.95s** |
| Full exact-head CI | **4628 passed, 1 xfailed in 155.52s** |
| Local Ruff cuttingboard/ tests/ | **Exit 0**, All checks passed |
| Local Ruff entire worktree | **Exit 1**, three E741 errors at unchanged `audits/operator-setup-chart-material-packet-2026-08/EVIDENCE_PROTOTYPE_GENERATOR_2026-08-28.py:121,197,199` |
| Local strict PRD registry validator | **Exit 1**, 22 historical unresolvable-commit notices, no other diagnostics |
| Local validator --skip-commit-resolvability | **Exit 0**, PRD registry validation passed |
| Exact-head CI lint / validator | PASS for `ruff check cuttingboard/ tests/` and validator with `--skip-commit-resolvability` |
| Exact diff whitespace | `git diff --check BASE HEAD`: exit 0 |
| Production fence | Exactly the five authorized production files; net +209 lines; no renderer/ingestion/workflow edit |
| Local implementation head / live origin head | Both `0b5bd551bedcf88dde8097cf78ba38cebffbdd55` before report commit |
| PR state | Live GitHub response: OPEN, isDraft=true, same head |
| Working tree | NOT CLEAN on arrival: three pre-existing modified logs; no staged changes |

CI provenance: run **34079402498**, job **101611690048**, headSha explicitly
verified as the reviewed SHA. Full-suite logs and successful step conclusions
were inspected at
https://github.com/dwats250/cuttingboard/actions/runs/34079402498/job/101611690048 .
The full suite was not needlessly repeated locally.

Focused command: `PYTHONDONTWRITEBYTECODE=1 /home/dustin/Projects/cuttingboard/.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_universe_registry.py tests/test_watchlist_sidecar.py tests/test_movement_card.py tests/test_observe_only_isolation.py -k 'not runtime_write_helper_writes_atomically and not load_rejects_malformed_and_nondict_json and not runtime_observe_only_reaches_watchlist_not_decisions and not decision_invariance_real_stages_paired_run'`.
Those four disk-writing tests were deselected locally to preserve the existing
dirty state; the full exact-head CI includes them. The independent in-memory C,
deadline, and M2 probes are reported above. No mutation was written to source.

Registry validation reads authored rows directly, then follows the constructed
symbol map for bounded benchmark closure; it does not validate a projection
using that same projection. UCO/TSLA membership is pinned independently by
literal tests, not encoded as magic symbol names in the generic validator.
Some distinct invalid fixtures (disabled measurement, nonmeasurement benchmark
target) are not separately named in the new red tests; inspection confirms the
corresponding rejection branches, so no production defect is inferred.

Carrier/consumer agreement: schema 3, watchlist source, 22 exact identities,
five output fields, null for missing observations, no fabricated zero, capture
timestamp preserved. A null generated_at is allowed by the producer and
deliberately suppresses the card. Builder insertion order is registry order;
the unchanged disk writer uses sort_keys=True, so physical JSON key order is
alphabetical. Registry indices preserve canonical display order across that
round trip; do not claim disk insertion order is registry order.

Movement admission at `movement_card.py:102-153` checks the whole exact key set,
every row identity/group/index, both required numeric keys/types/finite values,
source, version, and aware timestamp before returning any model. Missing,
extra, UCO, TSLA, unknown, duplicate row identity/index, bad group, malformed
percentage and timestamp all suppress the whole model; explicit null remains
n/a. Group ordering uses index, not performance. This is a dict-level contract;
no special duplicate-JSON-object-key detector was introduced beyond json.loads.
The model retains plain chip spaces for `market_state_panel.py:90-97`; HTML
adds nbsp only within a chip (`movement_card.py:157-170`). Dashboard consumption
remains at `dashboard_renderer.py:3599-3605`; capture coverage derives from the
model, including 22/22, 21/22, 0/22. No CSS change or new label semantics.

Generated files preserved outside staging:
`logs/latest_hourly_market_map.json`, `logs/price_bars_snapshot.json`,
`logs/trend_structure_snapshot.json`. A report-only commit must not be described
as a clean working tree. No cleanup of these files is authorized here.

## 10. GOVERNANCE STATUS / DRIFT CHECK

**Held for your decision — owner: Dustin/Helm.** No successor PRD-337 registry
entry or Gate A was found in the reviewed registry/index. Fable's implementation
contract conditions IMPLEMENT on successor PRD/Gate A and leaves GOV-2 seat
reconciliation to Helm under F15. This technical review grants neither missing
authorization nor retrospective ratification. Code could in principle be
technically clean while governance remains held; this head also has technical
required changes, so CLEAN WITH GOVERNANCE HOLD is not its verdict.

VISION drift: no new prediction, recommendations, execution authority, or
decision-contract mutation found; observation-sidecar architecture preserved.
The timing/failure claims need the explicit correction above to honor documented
truth. PROJECT_STATE names PRD-336 as active and does not record this implemented
precursor; reconcile that status through the owner-governed PRD lifecycle, not
through an unauthorized review edit. PR #325's design-only body is also stale.

## 11. NEXT ACTION — smallest proposed fix charge

Helm must commission the fixes; this review does not grant implementation or
expand the five-file production fence.

Basis: this exact-head report plus the Fable design and Helm's governance ruling.
Objective: close R1–R4 without NS-4C/NS-4D or provider/workflow changes.
Smallest FILES: `cuttingboard/runtime/__init__.py`,
`tests/test_observe_only_isolation.py`, `tests/test_universe_registry.py`,
`docs/universe_taxonomy.md`.

1. Contain complete observation-helper failure locally at the watchlist seam;
   retain primary quotes, prior successful outputs, and one notification.
2. Stop at elapsed >=60; pin exact-deadline retention and clarify remaining
   in-flight/next-slot exposure in comments/documentation.
3. Extend the existing A/B regression with Fable's raised-helper C and complete
   result equality; use independent patch scopes. Keep existing M2/M6 guards.
4. Replace the fragile authority-reader guard with the bounded structural guard
   and discriminating synthetic snippets; carry F7's question/caveat in docs.
5. Run targeted tests, production/test Ruff, registry validation and full gate;
   distinguish the known broad-lint and historical-resolvability limitations.
   Reconcile/link browser and bounded timing evidence and the PR description.
6. Commit/push only the newly authorized fixes on this lineage; return for
   exact-corrected-head confirmation against these findings, then the Helm-owned
   Gate A/ratification/merge process as applicable. PR remains draft; never merge.

Production changes are required, confined to the runtime observation seam.

**FIXES REQUIRED**
