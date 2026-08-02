# Domain D1 — Product surfaces, as-built

## Header
- Baseline SHA: `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`
- Accepted scaffold seam SHA: `e0d481f4e3daeae9d8cba4a7aee7670d27b5a2b5`
- Authorized Phase 1 execution-contract SHA: `41bfcd6888b7c28da9c0478c9534bdb66a9a2600`
- Assigned domain: D1
- Dispatch parameters (verbatim from `01_SOURCE_AUTHORITY_MANIFEST.md`):

- OWNED: `cuttingboard/delivery/dashboard_renderer.py`,
  `cuttingboard/market_map.py`, `cuttingboard/market_map_lifecycle.py`,
  `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md`,
  `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md`; the
  implementation seams stage0-01's own assertions depend on:
  `cuttingboard/watch.py`, `cuttingboard/ingestion.py`,
  `cuttingboard/intraday_state_engine.py`, `cuttingboard/runtime/__init__.py`,
  `cuttingboard/execution_policy.py`, `cuttingboard/contract.py`.
- CITED: `CLAUDE.md` (owned by A, cited by all); `docs/PRD_REGISTRY.md` +
  `docs/prd_index.json` (owned by B, cited by all — PRD-number lookups
  only); Program sec 2, 3, 4, 6, 7 (owned by B, cited by all — specifically
  the candidate card / Market Map source-map row within sec 3).
- EXCLUDED BY DEFAULT: broader `cuttingboard/` traversal beyond the 9 named
  files above — log as amendment if verifying "actual implementation
  seams" needs a file not on this list; this is not an open-ended
  `cuttingboard/` sweep.
- Methodology: fact-check against real code.


Files inspected:

- `audits/north-star-deep-audit-2026-08/00_AUDIT_CHARTER.md` — execution-governing. Pinned at authorized Phase 1 execution-contract SHA `41bfcd6888b7c28da9c0478c9534bdb66a9a2600`. Verified via commit ancestry that no commit or uncommitted change preceded this dispatch (the domain-evidence commit `a8bf688` and all later commits are descendants of `41bfcd6`, and the dispatch worktree carried no uncommitted diff against that SHA at dispatch time), so the content actually read is byte-equivalent to `git show 41bfcd6:audits/north-star-deep-audit-2026-08/00_AUDIT_CHARTER.md`. No re-collection was needed.
- `audits/north-star-deep-audit-2026-08/01_SOURCE_AUTHORITY_MANIFEST.md` — execution-governing. Pinned at `41bfcd6888b7c28da9c0478c9534bdb66a9a2600`, same reproducibility verification as above; governed D1's OWNED, CITED, and EXCLUDED dispatch parameters.
- `audits/north-star-deep-audit-2026-08/02_DOMAIN_COVERAGE_MATRIX.md` — status-tracking only, not execution-governing (corrected 2026-08-02 per adjudicated Stage 0 finding). This file is a mutable Phase 1 status tracker that legitimately evolved as sibling domains completed and D1 used its permitted retry; its content does not govern D1's OWNED, CITED, or EXCLUDED source contract, which is fixed by the Manifest above. No claim is made that the Coverage Matrix content read during D1's retry was byte-equivalent to `git show 41bfcd6:audits/north-star-deep-audit-2026-08/02_DOMAIN_COVERAGE_MATRIX.md` — it was not intermediate-committed at any point during Phase 1, so that claim is unverifiable from git history and was withdrawn as overclaiming.
- `CLAUDE.md` — pinned with `git show fdeef90b0a0e0747d1bbf92385d3750b4024f4ae:CLAUDE.md`.
- `docs/PRD_REGISTRY.md` — pinned with `git show fdeef90b0a0e0747d1bbf92385d3750b4024f4ae:docs/PRD_REGISTRY.md`.
- `docs/prd_index.json` — pinned with `git show fdeef90b0a0e0747d1bbf92385d3750b4024f4ae:docs/prd_index.json`.
- `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` — pinned with `git show fdeef90b0a0e0747d1bbf92385d3750b4024f4ae:docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`.
- `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md` — pinned.
- `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md` — pinned.
- All eleven owned implementation files listed above — each read with the required pinned `git show` command.

Files intentionally excluded:

- `cuttingboard/config.py` — referenced by assertions but excluded from the named implementation-seam scope.
- `cuttingboard/delivery/payload.py` — referenced by stage0-01 Q1 but not named in the dispatch.
- `cuttingboard/trade_visibility.py` — referenced by stage0-01 Q1 but not named in the dispatch.
- `cuttingboard/trend_structure.py` — referenced by stage0-01 Q2 but not named in the dispatch.
- `docs/artifact_flow_map.md` — referenced by stage0-01 Q2 but not named in the dispatch.
- `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` — NS-2 assertions are owned by D2 and were not re-derived.
- Broader `cuttingboard/` traversal — excluded by the manifest; no open-ended implementation sweep performed.
- PRD history files, including `docs/prd_history/PRD-271.md` — cited sources are limited to PRD-number lookups.

Completion status: COMPLETE — every OWNED source inspected, every CITED source consulted, every EXCLUDED-BY-DEFAULT item documented, evidence table fully populated for in-scope assertions with no blank rows; out-of-scope dependencies correctly routed to the unchanged PROPOSED AMENDMENT section, which does not block completion under this definition (Charter §11; retry 2 of 2 per Global Constraint #6, re-assessed against attempt 1's unchanged evidence — see Coverage Matrix).

Attempt count: 2

No-edits attestation: confirmed

## Evidence

| ID | North Star assertion | assertion_type | evidence (path:lines, pinned) | result | risk | confidence | assumptions | Dustin ruling required? |
|---|---|---|---|---|---|---|---|---|
| D1-01 | The stage0-01 decision-surface report is the evidence base for NS-2A/2B/2C/2E and supplies a producer/ownership map, positional-ORB reproduction, lifecycle schema, and Control Card row disposition. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:77` [pinned]; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:1-12,146-213` [pinned] | MATCH | Future product work may rely on evidence that has not yet become an implementation contract. | HIGH |  | no |
| D1-02 | The current Market Map decision surface is the candidate card; no declared Control Card contract exists. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:93` [pinned]; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:164-213` [pinned]; `cuttingboard/delivery/dashboard_renderer.py:1791-1910` [pinned] | MATCH | Future consumers could mistake candidate-card presentation fields for a durable control contract. | HIGH |  | yes |
| D1-03 | No production fixed-SPY observation artifact exists, and the current watch path has the reproduced positional ORB defect. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:94` [pinned]; `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:16-49,115-125` [pinned]; `cuttingboard/watch.py:156-166,356-371` [pinned] | MATCH | Incorrect ORB anchors can contaminate displayed context and downstream execution decisions. | HIGH |  | no |
| D1-04 | The universe substrate consists of two agreeing fixed six-symbol tuples: `config.TREND_STRUCTURE_SYMBOLS` and `market_map.PRIMARY_SYMBOLS`. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:95` [pinned]; `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:93-99` [pinned]; `cuttingboard/market_map.py:130-153` [pinned] | PARTIAL | A silent divergence between configuration and Market Map symbols could create inconsistent coverage. | MEDIUM | Agreement of the configuration tuple cannot be confirmed without reading excluded `cuttingboard/config.py`. | yes |
| D1-05 | PRD-271 is an IN PROGRESS Stage-0 scaffold owning the session-correct ORB defect, with Gate A pending. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:43,84` [pinned]; `docs/PRD_REGISTRY.md:288-294` [pinned]; `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:16-49,118-125` [pinned] | MATCH | Treating an unapproved scaffold as implemented could authorize an unruled ORB remedy. | HIGH |  | no |
| D1-06 | The dependency order is PRD-271 Gate A → session-correct ORB → fixed SPY observation/session VWAP → Market Control Card. | FUTURE-DESIGN-INTENT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:110-116` [pinned]; `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:297-307` [pinned]; `cuttingboard/watch.py:164-166` [pinned]; `cuttingboard/intraday_state_engine.py:124-142,400-438` [pinned] | MATCH | Building a downstream card before shared session truth is settled risks two conflicting ORB authorities. | HIGH |  | yes |
| D1-07 | The existing producer map contains separate market-map, intraday-state, execution-policy, and contract fields rather than one durable Control Card producer. | FACT | `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:58-80` [pinned]; `cuttingboard/market_map.py:159-244` [pinned]; `cuttingboard/execution_policy.py:157-199` [pinned]; `cuttingboard/contract.py:344-375` [pinned] | MATCH | Field ownership can drift if a future card treats presentation payloads as authoritative policy state. | HIGH |  | no |
| D1-08 | Market-map symbol records carry grade, bias, structure, setup state, watch zones, trade framing, and unavailable semantics. | FACT | `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:73-80` [pinned]; `cuttingboard/market_map.py:159-244` [pinned] | MATCH | Missing inputs may be represented as low-grade/data-unavailable context rather than a durable session-state fact. | HIGH |  | no |
| D1-09 | Market-map intraday zones include VWAP, ORB high/low, and prior-session levels when intraday metrics are present; derived EMA zones may remain independently available. | FACT | `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:155-162` [pinned]; `cuttingboard/market_map.py:310-340` [pinned] | MATCH | A consumer may interpret optional zones as complete session provenance when they are absent or filtered. | HIGH |  | no |
| D1-10 | Intraday ingestion filters regular-session bars to 09:30–15:30 ET, selects the latest session date, and returns at most 120 bars. | FACT | `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:93-99` [pinned]; `cuttingboard/ingestion.py:170-207` [pinned] | MATCH | The 120-bar retention window removes early-session bars needed by positional ORB logic. | HIGH |  | no |
| D1-11 | The watch path computes ORB from the first five retained bars, while the intraday-state engine selects bars by the 09:30–09:35 ET timestamp window. | FACT | `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:118-125` [pinned]; `cuttingboard/watch.py:156-166` [pinned]; `cuttingboard/intraday_state_engine.py:124-142` [pinned] | MATCH | Two ORB-selection rules can produce incompatible market-state and execution inputs. | HIGH |  | no |
| D1-12 | The intraday-state engine returns no state before 09:45 ET and raises insufficient-data errors when fewer than five ORB-window bars exist. | FACT | `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:118-125` [pinned]; `cuttingboard/intraday_state_engine.py:400-438` [pinned] | MATCH | Downstream surfaces may need to represent unavailable state explicitly rather than infer a state. | HIGH |  | no |
| D1-13 | The hourly runtime builds a separate hourly Market Map with an empty intraday-metrics mapping and writes it to the isolated hourly artifact path. | FACT | `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:155-162` [pinned]; `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:127-140` [pinned]; `cuttingboard/runtime/__init__.py:356-389,537-557` [pinned] | MATCH | Hourly output can omit VWAP/ORB zones; incorrectly assuming premarket reuse would create stale-context risk. | HIGH |  | no |
| D1-14 | Fixed-universe trend-structure production runs outside candidate decision guards and writes its own snapshot. | FACT | `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:101-109` [pinned]; `cuttingboard/runtime/__init__.py:537-562,2052-2089` [pinned] | PARTIAL | The production behavior is confirmed, but the symbol-source side of the fixed-universe claim remains unverified. | MEDIUM | The excluded configuration source is assumed to remain the tuple named by the stage0 assertion. | yes |
| D1-15 | Lifecycle injection transitions grade and setup state between Market Map artifacts and can backfill a missing current price from the prior artifact. | FACT | `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:149-154` [pinned]; `cuttingboard/market_map_lifecycle.py:39-85` [pinned] | MATCH | A carried-forward price can be mistaken for a fresh market anchor. | HIGH |  | no |
| D1-16 | The renderer displays candidate-card header identity, `IF NOW`, lifecycle transitions, `IN →`, `OUT →`, and supporting `REASON`/`PLAY`/`WATCH` detail. | FACT | `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:142-147` [pinned]; `cuttingboard/delivery/dashboard_renderer.py:1791-1910` [pinned] | MATCH | Presentation emphasis can be mistaken for execution permission or session-state authority. | HIGH |  | no |
| D1-17 | Market-state transitions and permission transitions are separate concepts; runtime removes short candidates when downside permission is false, and execution policy can block a decision. | FACT | `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:178-197` [pinned]; `cuttingboard/runtime/__init__.py:1319-1380` [pinned]; `cuttingboard/execution_policy.py:157-245` [pinned]; `cuttingboard/contract.py:344-375` [pinned] | MATCH | Conflating descriptive market state with permission state could expose blocked or unavailable candidates as tradable. | HIGH |  | no |
| D1-18 | The truthful v1 surface does not currently provide durable late-day ORB anchors, full-session VWAP after rolling-window loss, durable ORB lifecycle, exact source-failure reasons, or a fresh live-NOW price claim from final Market Map data. | FACT | `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:93-95` [pinned]; `audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:199-213` [pinned]; `cuttingboard/watch.py:156-166,356-371` [pinned]; `cuttingboard/market_map_lifecycle.py:82-85` [pinned] | MATCH | Consumers may display unavailable or stale values as authoritative session facts. | HIGH |  | yes |

## Non-match detail: D1-04

- Exact source path and lines: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:95`; `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:93-99`; `cuttingboard/market_map.py:130-153`.
- Governing authority: Source Authority Manifest dispatch boundary; `cuttingboard/config.py` is excluded by default.
- Observed discrepancy: `market_map.PRIMARY_SYMBOLS` is readable and is used to build the Market Map, but the asserted agreeing `config.TREND_STRUCTURE_SYMBOLS` tuple was not independently checked.
- Practical consequence: A tuple divergence could cause the Market Map and trend-structure snapshot to cover different symbols.
- False-authority risk: The North Star source map could present agreement as established when only one side was verified.
- Safety relevance: Incorrect universe coverage can omit or misrepresent market context.
- Current-vs-future-facing effect: Current-state verification is incomplete; the NS-4A future registry remains unbuilt.
- Proposed disposition: Amend the dispatch only if Dustin authorizes reading `cuttingboard/config.py`; otherwise retain as PARTIAL.
- Confidence: MEDIUM.
- Missing evidence: Pinned `cuttingboard/config.py` lines defining `TREND_STRUCTURE_SYMBOLS`.

## Non-match detail: D1-14

- Exact source path and lines: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:95`; `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:101-109`; `cuttingboard/runtime/__init__.py:537-562,2052-2089`.
- Governing authority: Source Authority Manifest exclusion of broader `cuttingboard/` traversal.
- Observed discrepancy: Runtime snapshot-writing and fixed-loop behavior were verified, but the configuration-defined fixed-universe source was not read.
- Practical consequence: The claim that the snapshot covers the intended fixed universe cannot be fully established.
- False-authority risk: A runtime loop may be treated as proof of correct symbol scope.
- Safety relevance: Incorrect or incomplete market coverage can affect decision context.
- Current-vs-future-facing effect: Current implementation evidence is partial; future universe-registry work remains separate.
- Proposed disposition: Amend the dispatch only if the excluded configuration file is explicitly added.
- Confidence: MEDIUM.
- Missing evidence: Pinned configuration definition and any authorized source-map for the trend-structure universe.

## Non-match detail: Stage0 Q1/Q2/Q3/Q4 excluded-source portions

- Exact source path and lines: `audits/stage0-recon-2026-07-20/verify-01-decision-surface.md:58-109`; corresponding excluded references include `cuttingboard/delivery/payload.py`, `cuttingboard/trade_visibility.py`, `cuttingboard/trend_structure.py`, `docs/artifact_flow_map.md`, and `cuttingboard/config.py`.
- Governing authority: Source Authority Manifest D1 dispatch; broader traversal is excluded by default.
- Observed discrepancy: The named D1 seams confirm the portions involving Market Map, runtime, execution policy, contract, ingestion, and intraday state, but the stage0 assertions also rely on unassigned files.
- Practical consequence: Full producer ownership, overlapping-producer, universe, and fixed-universe claims cannot be independently re-established within this dispatch.
- False-authority risk: A partial seam read could be reported as a complete implementation audit.
- Safety relevance: Ownership and unavailable-state errors can affect whether a displayed value is treated as a permission or safety control.
- Current-vs-future-facing effect: The limitation concerns current as-built verification; it does not authorize future implementation.
- Proposed disposition: Log a bounded amendment for the specifically named files; do not perform a broader sweep.
- Confidence: LOW.
- Missing evidence: Pinned reads of the five excluded paths listed above.

## PROPOSED AMENDMENT

- discovered by: D1 / D1-04 — description: verifying the asserted agreement between `config.TREND_STRUCTURE_SYMBOLS` and `market_map.PRIMARY_SYMBOLS` requires `cuttingboard/config.py` / proposed scope change: add that single pinned file to D1 implementation seams / blocking: yes, to fully resolving D1-04's confidence — D1-04 is recorded PARTIAL/MEDIUM with an explicit assumption note ("agreement... cannot be confirmed without reading excluded `cuttingboard/config.py`"), not a blank row. **Not** blocking to Domain D1's own COMPLETE status, independently satisfied per Charter §11.
- discovered by: D1 / Stage0 Q1 — description: full producer/consumer ownership verification requires `cuttingboard/delivery/payload.py` and `cuttingboard/trade_visibility.py` / proposed scope change: add only those two pinned files / blocking: yes, to fully resolving the affected rows' confidence, not to Domain D1's COMPLETE status (same basis as above).
- discovered by: D1 / Stage0 Q2 — description: overlapping producer and artifact-flow verification requires `cuttingboard/trend_structure.py` and `docs/artifact_flow_map.md` / proposed scope change: add only those named files / blocking: yes, to fully resolving the affected rows' confidence, not to Domain D1's COMPLETE status (same basis as above).
- discovered by: D1 / Stage0 Q4 — description: complete fixed-universe verification requires the excluded configuration source / proposed scope change: add `cuttingboard/config.py` if not covered by the first amendment / blocking: yes, to fully resolving the affected rows' confidence, not to Domain D1's COMPLETE status (same basis as above).
- discovered by: D1 — description: no broader `cuttingboard/` traversal was necessary or performed / proposed scope change: none; preserve the bounded dispatch / blocking: no.

No repository files were edited during this dispatch.
