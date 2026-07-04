# PRD Registry

All product requirement documents for the cuttingboard decision engine, in order.

---

| PRD | Commit(s) | Title | Status | File |
|-----|-----------|-------|--------|------|
| Init | d84cd027 | Bootstrap — initial PRD committed | COMPLETE | — |
| PRD-001 | d37e72f, 094b428 | 10-layer pipeline bootstrap — full system, 297 tests, GHA workflow | COMPLETE | [PRD-001](prd_history/PRD-001.md) |
| PRD-002 | 6bc67e6, 3d4a214 | Options chain validation + runtime orchestrator | COMPLETE | [PRD-002](prd_history/PRD-002.md) |
| PRD-003 | 809214bc | Enforce deterministic failure visibility in CI pipeline | COMPLETE | [PRD-003](prd_history/PRD-003.md) |
| PRD-003.2 | 7838f461 | Fix remaining workflow patch drift | PATCH | [PRD-003.2](prd_history/PRD-003.2.md) |
| PRD-003.3 | 6202bc9e | Fix CI failure-path guards | PATCH | [PRD-003.3](prd_history/PRD-003.3.md) |
| PRD-003.4 | c004db9c | Replace stale workflow lines exactly | PATCH | [PRD-003.4](prd_history/PRD-003.4.md) |
| PRD-004 | b5505613, 08117400 | Contract alignment — audit contract, stale data validation | COMPLETE | [PRD-004](prd_history/PRD-004.md) |
| PRD-005 | 61af9214 | Separate run alert routing from trade formatting; fix STAY_FLAT crash; enforce runtime failure artifacts | COMPLETE | [PRD-005](prd_history/PRD-005.md) |
| PRD-006 | d1984113, 1b11010 | Remove ntfy transport; enforce Telegram-only notification path | COMPLETE | [PRD-006](prd_history/PRD-006.md) |
| PRD-007 | ab3d20b8 | Imbalance pullback entry (FVG) — qualification and options layers | COMPLETE | [PRD-007](prd_history/PRD-007.md) |
| PRD-008 | 30b583a0 | Expansion regime detection + continuation entry mode | COMPLETE | [PRD-008](prd_history/PRD-008.md) |
| PRD-009 | f4ddb677 | Canonical timezone handling + time gate validation | COMPLETE | [PRD-009](prd_history/PRD-009.md) |
| PRD-010 | de6c0a6a | Continuation rejection audit + threshold calibration | COMPLETE | [PRD-010](prd_history/PRD-010.md) |
| PRD-011 | e6896f39 | Freeze canonical pipeline output contract | COMPLETE | [PRD-011](prd_history/PRD-011.md) |
| PRD-012 | b90c8938 | Deterministic payload delivery layer — adapter and transport | COMPLETE | [PRD-012](prd_history/PRD-012.md) |
| PRD-012 (cleanup) | b336b2f4 | Post-audit cleanup: remove dead code, fix symbols_scanned, enforce determinism | PATCH | [PRD-012-cleanup](prd_history/PRD-012-cleanup.md) |
| PRD-012A | 0d6b0215 | Guarantee hourly Telegram alerts via dedicated GitHub workflow | COMPLETE | [PRD-012A](prd_history/PRD-012A.md) |
| PRD-013 | b17be17f | Flow alignment soft gate in qualification pipeline | COMPLETE | [PRD-013](prd_history/PRD-013.md) |
| PRD-014 | 30ce0adc | Structural hardening, flow wiring, config-driven ingestion | COMPLETE | [PRD-014](prd_history/PRD-014.md) |
| PRD-015 / 015.1 | 30ce0adc | Flow wiring and ingestion config consolidation (bundled with PRD-014) | COMPLETE | [PRD-014](prd_history/PRD-014.md) |
| PRD-016 / 016.1 | 3d707356 | Pre-UI audit: legacy cleanup, interface lock, output contract verification | COMPLETE | [PRD-016](prd_history/PRD-016.md) |
| PRD-017 | fc7f5e9 | Notification delivery stabilization: rate limit, retry, aggregation, audit | COMPLETE | [PRD-017](prd_history/PRD-017.md) |
| PRD-018 | 0f7c341 | Notification signal hierarchy and suppression: state key, priority, dedup | COMPLETE | [PRD-018](prd_history/PRD-018.md) |
| PRD-019 | c7c64c9, 0aea646 | Notification Decision Audit / Delivery Safety Layer (Killed 2026-06-12 — never built; obsolete under the three-report cadence. Row title previously mislabeled with PRD-020's "Engine doctor" subject; corrected. See docs/DECISIONS.md and docs/audit/gate_recon_2026-06-12.md flags G1/D8) | DEPRECATED | [PRD-019](prd_history/PRD-019.md) |
| PRD-020 | 0472cfd | Engine doctor gate system (CI + runtime guardrails) | COMPLETE | [PRD-020](prd_history/PRD-020.md) |
| PRD-021 | e6b017c | Documentation canonicalization (README + docs system) | COMPLETE | [PRD-021](prd_history/PRD-021.md) |
| PRD-022 | 2b6009a | Sunday mode isolation — no live data, forced STAY_FLAT, non-live execution path | COMPLETE | [PRD-022](prd_history/PRD-022.md) |
| PRD-023 | 314ca46 | GLD–DXY correlation policy layer — advisory risk_modifier, no qualification mutation | COMPLETE | [PRD-023](prd_history/PRD-023.md) |
| PRD-024 | 6f97d12 | Contract UI consumer — static HTML read-only decision surface | COMPLETE | [PRD-024](prd_history/PRD-024.md) |
| PRD-025 | 3d532cd | Decision compression layer — primary signal and trade promotion | COMPLETE | [PRD-025](prd_history/PRD-025.md) |
| PRD-026 | 442b813 | Alert visibility upgrade — deterministic ASCII titles and structured body | COMPLETE | [PRD-026](prd_history/PRD-026.md) |
| PRD-027 | b8dc599 | Context report layer — deterministic premarket and postmarket reports | COMPLETE | [PRD-027](prd_history/PRD-027.md) |
| PRD-028 | 2796df4 | PRD system hardening — template, lifecycle states, file enforcement, scope lock | COMPLETE | [PRD-028](prd_history/PRD-028.md) |
| PRD-029 | 57c23f9 | Level awareness layer — derived price levels for premarket and postmarket reports | COMPLETE | [PRD-029](prd_history/PRD-029.md) |
| PRD-030 | 83bdd3b | Scenario engine hardening — regime + level driven scenario generation | COMPLETE | [PRD-030](prd_history/PRD-030.md) |
| PRD-031 | 0c61a87 | Claude Code hooks — commit gate, file guard, test gate, state snapshot | COMPLETE | [PRD-031](prd_history/PRD-031.md) |
| PRD-032 | — | Catastrophic output and validation contract repair | DEPRECATED | [PRD-032](prd_history/PRD-032.md) |
| PRD-033 | 7fe9eb7 | UI theme layer — sideloadable CSS theme system | COMPLETE | [PRD-033](prd_history/PRD-033.md) |
| PRD-034 | 54d490e | GitHub Pages deployment — remote read-only access | COMPLETE | [PRD-034](prd_history/PRD-034.md) |
| PRD-035 | feature/ui-decision-layer | Signal Forge dashboard — contract regime block + UI macro strip | COMPLETE | [PRD-035](prd_history/PRD-035.md) |
| PRD-036 | ccb53fb | Slim dashboard renderer — read-only HTML from payload + run artifacts | COMPLETE | [PRD-036](prd_history/PRD-036.md) |
| PRD-037 | 0a80981 | Dashboard publish artifact — static copy of generated HTML to docs/ | COMPLETE | [PRD-037](prd_history/PRD-037.md) |
| PRD-038 | d1a77e3 | Read-only macro tape consolidation block | COMPLETE | [PRD-038](prd_history/PRD-038.md) |
| PRD-039 | 3e7a4f2 | Dashboard link in all Telegram alerts | COMPLETE | [PRD-039](prd_history/PRD-039.md) |
| PRD-040 | 99c4d27 | Protect latest_* artifacts with timestamp guard | COMPLETE | [PRD-040](prd_history/PRD-040.md) |
| PRD-041 | d0f2ded | Run delta change detection block | COMPLETE | [PRD-041](prd_history/PRD-041.md) |
| PRD-042 | fd245a9 | Snapshot history — recent runs view | COMPLETE | [PRD-042](prd_history/PRD-042.md) |
| PRD-043 | 34becf7 | Decision summary block | COMPLETE | [PRD-043](prd_history/PRD-043.md) |
| PRD-044 | a5b1c85 | Macro driver payload surface with no-data mode support | COMPLETE | [PRD-044](prd_history/PRD-044.md) |
| PRD-045 | 64a78d5 | Trade decision materialization — explicit ALLOW/BLOCK per candidate | COMPLETE | [PRD-045](prd_history/PRD-045.md) |
| PRD-046 | 9fbd22b | Decision trace — first-failure explanation per candidate | COMPLETE | [PRD-046](prd_history/PRD-046.md) |
| PRD-047 | — | *(intentionally skipped — number not assigned)* | — | — |
| PRD-048 | 76f9786 | Trade decision visibility in payload and dashboard | COMPLETE | [PRD-048](prd_history/PRD-048.md) |
| PRD-049 | — | Development process hardening — CI tests, linting, commit gate, snapshot cleanup | COMPLETE | [PRD-049](prd_history/PRD-049.md) |
| PRD-050 | — | Alert runner fail-visible backstop | COMPLETE | — |
| PRD-051 | — | Execution policy materialization | COMPLETE | — |
| PRD-052 | — | Runtime artifact self-healing — legacy tolerance for missing timestamp keys | COMPLETE | [PRD-052](prd_history/PRD-052.md) |
| PRD-053 | 23db81e | Graded market map sidecar (landed alongside PRD-054 per 2026-05-22 reconciliation) | COMPLETE | [PRD-053](prd_history/PRD-053.md) |
| PRD-053 PATCH | 23db81e | Market map input plumbing + usefulness calibration (landed alongside PRD-054 per 2026-05-22 reconciliation) | COMPLETE | [PRD-053-PATCH](prd_history/PRD-053-PATCH.md) |
| PRD-054 | 23db81e | Add trade framing to market map sidecar (no PRD file; continuity note in PRD-055) | COMPLETE | — |
| PRD-055 | 395d07e, a360e23 | Signal Forge: Dashboard upgrade — macro tape, system state, candidate visibility board | COMPLETE | [PRD-055](prd_history/PRD-055.md) |
| PRD-056 | e7365c6 | Candidate lifecycle tracking — deterministic grade/setup_state transition metadata in market_map | COMPLETE | [PRD-056](prd_history/PRD-056.md) |
| PRD-057 | e7365c6 | Lifecycle visibility on Signal Forge dashboard — badge, detail row, removed symbols section | COMPLETE | [PRD-057](prd_history/PRD-057.md) |
| PRD-058 | 8f942c7 | Overnight Exit Guidance Layer | COMPLETE | [PRD-058](prd_history/PRD-058.md) |
| PRD-059 | 64d6aac | Macro Tape value row hardening | COMPLETE | [PRD-059](prd_history/PRD-059.md) |
| PRD-060 | 0ed003b | Deterministic macro pressure snapshot | COMPLETE | [PRD-060](prd_history/PRD-060.md) |
| PRD-061 | c7d5e23 | PRD Registry Numbering Guard | COMPLETE | [PRD-061](prd_history/PRD-061.md) |
| PRD-062 | 79c4185 | Macro Pressure Block in Signal Forge Dashboard | COMPLETE | [PRD-062](prd_history/PRD-062.md) |
| PRD-063 | d47ad79 | Macro Pressure Execution Policy Integration | COMPLETE | [PRD-063](prd_history/PRD-063.md) |
| PRD-064 | 663c652 | Trade Visibility Layer (Near-Miss Engine) | COMPLETE | [PRD-064](prd_history/PRD-064.md) |
| PRD-065 | 5a85df7 | Signal Forge Interactive Dashboard Controls | COMPLETE | [PRD-065](prd_history/PRD-065.md) |
| PRD-066 | b988f89 | Trade Drilldown Panel (Deterministic Explanation Layer) | COMPLETE | [PRD-066](prd_history/PRD-066.md) |
| PRD-067 | 88623b1 | Trade Thesis Gate | COMPLETE | [PRD-067](prd_history/PRD-067.md) |
| PRD-068 | 097c8e5 | Invalidation and Exit Guidance Layer | COMPLETE | [PRD-068](prd_history/PRD-068.md) |
| PRD-069 | d6a8660 | Entry Quality and Chase Filter | COMPLETE | [PRD-069](prd_history/PRD-069.md) |
| PRD-070 | 093d544 | Manual Trade Journal and Mistake Taxonomy | COMPLETE | [PRD-070](prd_history/PRD-070.md) |
| PRD-071 | cb48eba | Trading Process Review Scorecard | COMPLETE | [PRD-071](prd_history/PRD-071.md) |
| PRD-072 | 7e14a4e | Macro Drivers Snapshot Fallback | COMPLETE | [PRD-072](prd_history/PRD-072.md) |
| PRD-073 | dcc7446 | Human-Readable Dashboard Trader View | COMPLETE | [PRD-073](prd_history/PRD-073.md) |
| PRD-073-PATCH | dcc7446 | Renderer Boundary Test — explicit contract isolation requirement for R4 | COMPLETE | [PRD-073-PATCH](prd_history/PRD-073-PATCH.md) |
| PRD-074 | 6483a16 | Chart Context Layer (Level Diagram) | COMPLETE | [PRD-074](prd_history/PRD-074.md) |
| PRD-075 | 43a1052 | Signal Performance Engine | COMPLETE | [PRD-075](prd_history/PRD-075.md) |
| PRD-076 | 3c6bb76 | Dashboard Live Publishing and Layout Finalization | COMPLETE | [PRD-076](prd_history/PRD-076.md) |
| PRD-077 | 7d33a7a | Sunday Futures Pre-Report | COMPLETE | [PRD-077](prd_history/PRD-077.md) |
| PRD-078 | 7d33a7a | Dashboard Demo Candidate Fixture Mode | COMPLETE | [PRD-078](prd_history/PRD-078.md) |
| PRD-079 | 9e0aca7 | PRD Review Token Efficiency Guardrails | COMPLETE | [PRD-079](prd_history/PRD-079.md) |
| PRD-080 | 0cd7e45 | Sunday Report Expansion Layer | COMPLETE | [PRD-080](prd_history/PRD-080.md) |
| PRD-081 | c8462de | Dashboard Timestamp Display Hardening | COMPLETE | [PRD-081](prd_history/PRD-081.md) |
| PRD-082 | fbe5e11 | Remove Redundant Dashboard Permission Copy | COMPLETE | [PRD-082](prd_history/PRD-082.md) |
| PRD-083 | b67ac8a | Dashboard Data Freshness and Source Visibility | COMPLETE | [PRD-083](prd_history/PRD-083.md) |
| PRD-084 | b995d93 | Populate market_map current_price | COMPLETE | [PRD-084](prd_history/PRD-084.md) |
| PRD-085 | 9f4fe5f | Regression Coverage: current_price Survives Full Runtime Processing Chain | COMPLETE | [PRD-085](prd_history/PRD-085.md) |
| PRD-086 | 049e75f | Carry Forward current_price Through Sunday Market Map | COMPLETE | [PRD-086](prd_history/PRD-086.md) |
| PRD-087 | a976d01 | Pipeline Command Timeout Hardening | COMPLETE | [PRD-087](prd_history/PRD-087.md) |
| PRD-088 | 0be66f5 | Candidate Board Level Diagram Price Fallback | COMPLETE | [PRD-088](prd_history/PRD-088.md) |
| PRD-089 | fc3bf77 | Dashboard Artifact Coherence Guard | COMPLETE | [PRD-089](prd_history/PRD-089.md) |
| PRD-089-PATCH | 8980215 | Integrate run snapshot into system state | COMPLETE | [PRD-089-PATCH](prd_history/PRD-089-PATCH.md) |
| PRD-090 | 15ffa7f | Candidate Board Display Tiers | COMPLETE | [PRD-090](prd_history/PRD-090.md) |
| PRD-091 | c6e7249 | Candidate Validation Context | COMPLETE | [PRD-091](prd_history/PRD-091.md) |
| PRD-092 | e189a68 | Macro Conditions Consolidation | COMPLETE | [PRD-092](prd_history/PRD-092.md) |
| PRD-093 | 5513a8c | System State Information Economy | COMPLETE | [PRD-093](prd_history/PRD-093.md) |
| PRD-094 | 4aeef46 | Public Dashboard Artifact Contamination Guard | COMPLETE | [PRD-094](prd_history/PRD-094.md) |
| PRD-095 | 15ff9a5 | Scheduled Pipeline Morning Readiness Guard | COMPLETE | [PRD-095](prd_history/PRD-095.md) |
| PRD-096 | 04d66b2 | Runtime Artifact Git Hygiene and Pre-Push Safety | COMPLETE | — |
| PRD-097 | 03df0f4 | Dashboard Sidecar Freshness and Permission Clarity | COMPLETE | [PRD-097](prd_history/PRD-097.md) |
| PRD-098 | 729cde0 | Candidate Board Visibility and Validation Diagnostics | COMPLETE | [PRD-098](prd_history/PRD-098.md) |
| PRD-099 | 102063a | Dashboard Artifact Generation Contract | COMPLETE | [PRD-099](prd_history/PRD-099.md) |
| PRD-100 | e983bd0 | Standardize Artifact Push Rebase Contract | COMPLETE | [PRD-100](prd_history/PRD-100.md) |
| PRD-100-PATCH | 8d47ca3 | Artifact Push Helper Dirty Tree Rebase Safety | PATCH | — |
| PRD-100-PATCH-2 | 6100578 | Hourly Artifact Mutation Ordering | PATCH | — |
| PRD-101 | 97aa058 | Hourly Telegram Notification Truth Contract | COMPLETE | — |
| PRD-102 | accf10e | Align Alert and Dashboard Candidate Semantics | COMPLETE | [PRD-102](prd_history/PRD-102.md) |
| PRD-103 | c8ef8cf | Dashboard Data Contract Gap Patch | COMPLETE | [PRD-103](prd_history/PRD-103.md) |
| PRD-104 | 8d72f26 | Decision Logic and Artifact Flow Audit | COMPLETE | [PRD-104](prd_history/PRD-104.md) |
| PRD-105 | 740b48c | Decision Quality Evidence Map | COMPLETE | [PRD-105](prd_history/PRD-105.md) |
| PRD-106 | 8b5e672 | Cheap Lookup Dispatch Policy | COMPLETE | — |
| PRD-107 | d10e179 | Trend Structure Snapshot Sidecar | COMPLETE | [PRD-107](prd_history/PRD-107.md) |
| PRD-108 | 4cfdf5c | Registry Hook Hygiene | COMPLETE | [PRD-108](prd_history/PRD-108.md) |
| PRD-109 | 6f440e9 | Workflow Token Economy | COMPLETE | [PRD-109](prd_history/PRD-109.md) |
| PRD-110 | cea04ac | Narrow Trend Structure Snapshot Universe | COMPLETE | [PRD-110](prd_history/PRD-110.md) |
| PRD-111 | 93ed94d | Documentation & Knowledge-System Consolidation | COMPLETE | [PRD-111](prd_history/PRD-111.md) |
| PRD-112 | 339c3ea | Trend Structure Dashboard Panel | COMPLETE | [PRD-112](prd_history/PRD-112.md) |
| PRD-113 | 5d38186 | PRD Governance Hardening | COMPLETE | [PRD-113](prd_history/PRD-113.md) |
| PRD-114 | bab82cf | Watchlist Snapshot Sidecar | COMPLETE | [PRD-114](prd_history/PRD-114.md) |
| PRD-115 | e753ac0 | Dashboard Artifact Lineage Visibility | COMPLETE | [PRD-115](prd_history/PRD-115.md) |
| PRD-116 | d8df30c | Dashboard Mixed-Artifact Hierarchy Hardening | COMPLETE | [PRD-116](prd_history/PRD-116.md) |
| PRD-117 | ba10cfc | Session-Aware Inactive-State Labeling | COMPLETE | [PRD-117](prd_history/PRD-117.md) |
| PRD-118 | 136bbfe | Coherent Dashboard Publish Artifact Set | COMPLETE | [PRD-118](prd_history/PRD-118.md) |
| PRD-119 | ccdee4b | Dashboard Publish Freshness Gate | COMPLETE | [PRD-119](prd_history/PRD-119.md) |
| PRD-120 | d20d906 | Dashboard Source-Health Diagnostics and Permission Display Correction | COMPLETE | [PRD-120](prd_history/PRD-120.md) |
| PRD-121 | bd14b71 | PRD Workflow Lane Classification and Review Discipline | COMPLETE | [PRD-121](prd_history/PRD-121.md) |
| PRD-122 | 70a0e33 | Add WTI Crude Macro Visibility | COMPLETE | [PRD-122](prd_history/PRD-122.md) |
| PRD-122-PATCH | b0df0ad | Payload validator must permit optional oil driver | PATCH | [PRD-122-PATCH](prd_history/PRD-122-PATCH.md) |
| PRD-123 | 0b1ee7b | Trend Structure Refresh Decoupling and Truthful Source Status | COMPLETE | [PRD-123](prd_history/PRD-123.md) |
| PRD-124 | 5b0ae73 | Hourly Telegram Alert Header and Body Quality | COMPLETE | [PRD-124](prd_history/PRD-124.md) |
| PRD-125 | e727ae2 | OHLCV Cache Freshness Contract | COMPLETE | [PRD-125](prd_history/PRD-125.md) |
| PRD-126 | a4ce57c | Fixture Mode No-Live-OHLCV Boundary | COMPLETE | [PRD-126](prd_history/PRD-126.md) |
| PRD-127 | c814460 | Hourly Alert Action Language Alignment | COMPLETE | [PRD-127](prd_history/PRD-127.md) |
| PRD-128 | c959df5 | Hourly Readiness Ordering | COMPLETE | [PRD-128](prd_history/PRD-128.md) |
| PRD-129 | 1623687 | CI Artifact Hygiene and Push-Guard Stability | COMPLETE | [PRD-129](prd_history/PRD-129.md) |
| PRD-130 | d01327c | Trend Structure Unknown-State Normalization | COMPLETE | [PRD-130](prd_history/PRD-130.md) |
| PRD-131 | 82e1415 | Trend Structure Composite Display Layer | COMPLETE | [PRD-131](prd_history/PRD-131.md) |
| PRD-132 | e5e512c | Intraday VWAP × RVOL Context Display Layer | COMPLETE | [PRD-132](prd_history/PRD-132.md) |
| PRD-133 | 391f84c | Telegram Macro Pulse Alert Clarity | COMPLETE | [PRD-133](prd_history/PRD-133.md) |
| PRD-134 | c0c5ae5 | Daily Pipeline Market Map Coherence Repair | COMPLETE | [PRD-134](prd_history/PRD-134.md) |
| PRD-135 | 6fca328 | Engine Milestone Review and Consolidation Checkpoint | COMPLETE | [PRD-135](prd_history/PRD-135.md) |
| PRD-136 | b496b51 | Add Spot Metals Row to Macro Tape | COMPLETE | [PRD-136](prd_history/PRD-136.md) |
| PRD-137 | d88d8e0 | PATCH PRD-136 Payload Validator Accepts Optional Spot Metals | COMPLETE | [PRD-137](prd_history/PRD-137.md) |
| PRD-138 | b739bee | Shared Macro Tape Layout and Spot-Metals Color Parity | COMPLETE | [PRD-138](prd_history/PRD-138.md) |
| PRD-139 | 6ab8433 | Upstream Macro Collector Sidecar | COMPLETE | [PRD-139](prd_history/PRD-139.md) |
| PRD-140 | 1dbc886 | Document pre_push_check.sh in CLAUDE.md git hygiene | COMPLETE | [PRD-140](prd_history/PRD-140.md) |
| PRD-141 | 1ba6cc9 | Hourly Alert Canonical Slot + Cross-Run Idempotency | COMPLETE | [PRD-141](prd_history/PRD-141.md) |
| PRD-142 | — | PATCH PRD-141 Persist hourly slot state across CI runs (scheduled for kill per VISION.md 2026-05-22 — workflow change never landed) | DEPRECATED | [PRD-142](prd_history/PRD-142.md) |
| PRD-143 | 575b34f | Process hygiene sweep: hook exclusion, runtime.py debt note, Skill drift clause | COMPLETE | [PRD-143](prd_history/PRD-143.md) |
| PRD-144 | e3447d2 | Redundant cron entries for 6 AM PT hourly alert resilience | COMPLETE | [PRD-144](prd_history/PRD-144.md) |
| PRD-145 | 3230ceb | Sequencing-gate parser keys on row-owner cell only | COMPLETE | [PRD-145](prd_history/PRD-145.md) |
| PRD-146 | c0cfd53 | Reconcile prd_index.json with registry truth for 141/142/143 | COMPLETE | [PRD-146](prd_history/PRD-146.md) |
| PRD-147 | 320ab7f | prd_close.sh must not parse user input as re.sub template | COMPLETE | [PRD-147](prd_history/PRD-147.md) |
| PRD-148 | 08ea12e | Insert PRD-145 entry into prd_index.json | COMPLETE | [PRD-148](prd_history/PRD-148.md) |
| PRD-149 | c562259 | PT-Anchored Hourly Alert Window (6:00 AM – 1:00 PM PT) | COMPLETE | [PRD-149](prd_history/PRD-149.md) |
| PRD-150 | — | Five-Tier Symbol Classification System (Killed 2026-05-22 per vision review. Realizable behavior insufficient to justify surface area. See audits/recon-2026-05-22/prd-150-vision-review.md) | DEPRECATED | [PRD-150](prd_history/PRD-150.md) |
| PRD-151 | — | Gap-Down Permission Gating (retrospective documentation of feature built prior to VISION.md) | COMPLETE | [PRD-151](prd_history/PRD-151.md) |
| PRD-152 | c2adf7f | Batch B: Compatibility Shim Removal | COMPLETE | [PRD-152](prd_history/PRD-152.md) |
| PRD-153 | 5ec073e, a1993b9 | Moomoo Statement Consumer (Phase 2) — superseded by PRD-156 | DEPRECATED | [PRD-153](prd_history/PRD-153.md) |
| PRD-154 | 33844d7 | Scrub historical pytest contamination from logs/audit.jsonl | COMPLETE | [PRD-154](prd_history/PRD-154.md) |
| PRD-155 | cfae5d2 | Audit-write coverage doctrine | COMPLETE | [PRD-155](prd_history/PRD-155.md) |
| PRD-156 | 3c6fcb4 | Surgical removal of Moomoo Statement Consumer (PRD-153) | COMPLETE | [PRD-156](prd_history/PRD-156.md) |
| PRD-157 | 8417768 | Account-Equity-Driven Position Sizing | COMPLETE | [PRD-157](prd_history/PRD-157.md) |
| PRD-158 | c7a3863, ee2f055, d10b134, 85ee9a4, fd74b3f, 70d07d9, 599c17b | Dashboard Output Surface Realignment (Pass 1) | COMPLETE | [PRD-158](prd_history/PRD-158.md) |
| PRD-159 | 0481eb5 | scripts/prd_open.sh — Stage 0 PRD scaffolder | COMPLETE | [PRD-159](prd_history/PRD-159.md) |
| PRD-160 | 40353f6 | Fix macro_bias arrow-counting inversion | COMPLETE | [PRD-160](prd_history/PRD-160.md) |
| PRD-161 | 91d4afe | Add tradable qualified fixture for PRD-157 sizing gate | COMPLETE | [PRD-161](prd_history/PRD-161.md) |
| PRD-162 | 7aa4102 | outcome / regime / market_map reconciliation | COMPLETE | [PRD-162](prd_history/PRD-162.md) |
| PRD-163 | b57e1a4 | Fix regime permission wording for EXPANSION posture | COMPLETE | [PRD-163](prd_history/PRD-163.md) |
| PRD-164 | 2bc7e0a | Harden PRD lifecycle tooling (single-commit closeout, correct-table Stage-0, hash-drift detection) | COMPLETE | [PRD-164](prd_history/PRD-164.md) |
| PRD-165 | dac5712 | Candidate-card visual hierarchy and trend-structure dead-column pruning | COMPLETE | [PRD-165](prd_history/PRD-165.md) |
| PRD-166 | 5cac382 | Hourly market_map artifact isolation (PRD-118 R3 coherence) | COMPLETE | [PRD-166](prd_history/PRD-166.md) |
| PRD-167 | 3a4ee24 | RUN SNAPSHOT relative-freshness token | COMPLETE | [PRD-167](prd_history/PRD-167.md) |
| PRD-168 | 0442647 | Suppress idle screen-verdict above populated candidate cards | COMPLETE | [PRD-168](prd_history/PRD-168.md) |
| PRD-169 | 7b1d7ad | Persist continuation_audit to logs/audit.jsonl | COMPLETE | [PRD-169](prd_history/PRD-169.md) |
| PRD-170 | c4e9537 | runtime.py Monolith Split: Cut-Line Doctrine and Extraction Roadmap (Design-Only Scoping) | COMPLETE | [PRD-170](prd_history/PRD-170.md) |
| PRD-171 | d98ee31 | Sync PRD templates' status markers to the prd_close.sh flip convention | COMPLETE | [PRD-171](prd_history/PRD-171.md) |
| PRD-172 | 91b9dd2 | prd_close.sh baseline-bullet regex tolerates the N-xfailed suffix | COMPLETE | [PRD-172](prd_history/PRD-172.md) |
| PRD-173 | a5e47f2 | runtime/ package skeleton (Stage A of the runtime.py split) | COMPLETE | [PRD-173](prd_history/PRD-173.md) |
| PRD-174 | a62a218 | Populate trend-structure OHLCV on STAY_FLAT hourly runs | COMPLETE | [PRD-174](prd_history/PRD-174.md) |
| PRD-175 | 3de3809 | Historical regime scoreboard aggregation sidecar | COMPLETE | [PRD-175](prd_history/PRD-175.md) |
| PRD-176 | 1555bc8 | Red-folder economic calendar static schedule and loader | COMPLETE | [PRD-176](prd_history/PRD-176.md) |
| PRD-177 | 635680f | Dashboard realignment pass 2: cuts, four-questions reorder, macro evidence, new sidecar sections | COMPLETE | [PRD-177](prd_history/PRD-177.md) |
| PRD-178 | a3d34c5 | Dashboard fresh-data preview loop (CI preview workflow + local preview script) | COMPLETE | [PRD-178](prd_history/PRD-178.md) |
| PRD-179 | fce0ab2 | Preview fixture/all-section-state coverage (fast-follow to PRD-178) | COMPLETE | [PRD-179](prd_history/PRD-179.md) |
| PRD-180 | 6f74a76 | Kill switch forces real HALT (HaltCause primitive; cause-labeled HALT banner) | COMPLETE | [PRD-180](prd_history/PRD-180.md) |
| PRD-181 | b90aebf | Short-gate fail-closed during the open window (open-window fail-closed for SHORT when intraday state unavailable) | COMPLETE | [PRD-181](prd_history/PRD-181.md) |
| PRD-182 | 6733c61 | CI merge gate + pre-push full-suite + workflow env-default lint fix | COMPLETE | [PRD-182](prd_history/PRD-182.md) |
| PRD-183 | 84ca562 | Realign closeout tooling to the new PROJECT_STATE format | COMPLETE | [PRD-183](prd_history/PRD-183.md) |
| PRD-184 | 75a4121 | Auto-merge-via-PR landing flow (Claude push enablement) | COMPLETE | [PRD-184](prd_history/PRD-184.md) |
| PRD-185 | f77effe | Bump GitHub Actions to Node 24 majors (checkout v6, setup-python v6, upload-artifact v7) | COMPLETE | [PRD-185](prd_history/PRD-185.md) |
| PRD-186 | f775a48 | Drift-review gate: per-PRD drift check + post-merge audit teeth + governance auto-merge carve-out | COMPLETE | [PRD-186](prd_history/PRD-186.md) |
| PRD-187 | a7b0d58 | Macro-Awareness Producer + Materiality Eval | COMPLETE | [PRD-187](prd_history/PRD-187.md) |
| PRD-188 | — | Macro-Awareness SHOCK Banner + Scheduled Activation (GATED) | PROPOSED | [PRD-188](prd_history/PRD-188.md) |
| PRD-189 | b6e036e | Live-pipeline mode resolution + per-surface freshness observability | COMPLETE | [PRD-189](prd_history/PRD-189.md) |
| PRD-190 | 0573152 | OHLCV fetch window sized for SMA-200 | COMPLETE | [PRD-190](prd_history/PRD-190.md) |
| PRD-191 | 6f38429 | Direction-aware macro-evidence rationale | COMPLETE | [PRD-191](prd_history/PRD-191.md) |
| PRD-192 | a26a70c | Notify-mode tag on hourly notification audit + INTERFACE_LOCK reconciliation (folded from PRD-189 intraday-slot deferral) | COMPLETE | [PRD-192](prd_history/PRD-192.md) |
| PRD-193 | 3ce4179 | OHLCV cache trading-day freshness + publish-safe prefetch persistence | COMPLETE | [PRD-193](prd_history/PRD-193.md) |
| PRD-194 | 365f0fe | Production publish decoupling: dedicated unprotected publish branch (finishes PRD-178; unblocks the post-PRD-189 push rejection) | COMPLETE | [PRD-194](prd_history/PRD-194.md) |
| PRD-196 | 8a5fd6a | prd_close.sh baseline hygiene (robust bullet matching + CI-sourced baseline) | COMPLETE | [PRD-196](prd_history/PRD-196.md) |
| PRD-197 | 761eac4 | Codex cross-review via GitHub Actions (host-independent gate satisfier) | COMPLETE | [PRD-197](prd_history/PRD-197.md) |
| PRD-198 | ba8eb20 | Semantic-failure hardening doctrine | COMPLETE | [PRD-198](prd_history/PRD-198.md) |
| PRD-199 | fd27d79 | Macro-tape tradables daily %-change arrow | COMPLETE | [PRD-199](prd_history/PRD-199.md) |
| PRD-195 | 470aa2b | Publish-branch run_*.json storage cap/prune | COMPLETE | [PRD-195](prd_history/PRD-195.md) |
| PRD-200 | a794807 | Enforce registry/index/state consistency on the CI merge path | COMPLETE | [PRD-200](prd_history/PRD-200.md) |
| PRD-201 | b1f2598 | Canonical read-guard hook (warn on redundant re-read of injected docs) | COMPLETE | [PRD-201](prd_history/PRD-201.md) |
| PRD-202 | 7e5b52d | Agent-efficiency guidance: consult recon maps + delegate bookkeeping recon | COMPLETE | [PRD-202](prd_history/PRD-202.md) |
| PRD-203 | 35e0641 | prd_close.sh rebuilds the PROJECT_STATE baseline line (canonical, no stale provenance) | COMPLETE | [PRD-203](prd_history/PRD-203.md) |
| PRD-204 | 9c1fb37 | Non-destructive scoreboard aggregate (preserve-prior + staleness marker) | COMPLETE | [PRD-204](prd_history/PRD-204.md) |
| PRD-205 | — | (void — number skipped; 207/210 filed out of order) | DEPRECATED | — |
| PRD-206 | — | (void — number skipped; 207/210 filed out of order) | DEPRECATED | — |
| PRD-210 | 55b2f67 | Premarket trend-structure path coverage — apply the PRD-174 history fallback on _run_pipeline (F08 closes-None fix) | COMPLETE | [PRD-210](prd_history/PRD-210.md) |
| PRD-207 | 1968b50, 55f9cd2, 13c5d4a | codex-review.yml resolves the REQUESTED model, not the SERVED model (verified-real-Codex gate is hollow) | COMPLETE | [PRD-207](prd_history/PRD-207.md) |
| PRD-208 | 0f72e32 | Trend-structure SMA alignment presentation: compression + unavailable-token consistency | COMPLETE | [PRD-208](prd_history/PRD-208.md) |
| PRD-209 | — | OHLCV bar-count floor: reject/repair truncated daily frames served as fresh | PROPOSED | [PRD-209](prd_history/PRD-209.md) |
| PRD-211 | 57dfd12 | Macro-tape metals display correctness | COMPLETE | [PRD-211](prd_history/PRD-211.md) |
| PRD-212 | daedf10 | Pin the Codex cross-review identity (CLI version 0.142.1) — end the alias-drift gate outage. PREMISE SUPERSEDED (2026-07-01): the outage was a deprecated model (gpt-5-codex retired 2026-04-01), not CLI-alias drift; fixed by retargeting the model to gpt-5.5 (PR #76, validated run 28560459040). The 0.142.1 pin is retained. See DECISIONS 2026-07-01. | COMPLETE | [PRD-212](prd_history/PRD-212.md) |
| PRD-213 | 0cf7c25 | Mobile-responsive trend-structure table (stacked card reflow) | COMPLETE | [PRD-213](prd_history/PRD-213.md) |
| PRD-214 | 0cf7c25 | Macro-tape condensation (risk-vote tally supersedes per-driver evidence, PRD-177 R3/PRD-191) | COMPLETE | [PRD-214](prd_history/PRD-214.md) |
| PRD-215 | 0cf7c25 | Candidate-card condense + "actionable now" cyan accent | COMPLETE | [PRD-215](prd_history/PRD-215.md) |
| PRD-216 | 51fbb36 | Level-diagram dollar-value annotation | COMPLETE | [PRD-216](prd_history/PRD-216.md) |
| PRD-217 | f6113a9 | Macro-pressure: fold signals into the tally, remove the section | COMPLETE | [PRD-217](prd_history/PRD-217.md) |
| PRD-218 | 51fbb36 | Trend-structure density: compact mobile rows + alignment-colored price + SMA arrow spacing | COMPLETE | [PRD-218](prd_history/PRD-218.md) |
| PRD-219 | 02d2e8f | System-state distillation: verdict + one context line + single timestamp | COMPLETE | [PRD-219](prd_history/PRD-219.md) |
| PRD-220 | 2006db5 | Dashboard refinement round 2: system-state/market-map coherence + macro-tape & trend polish | COMPLETE | [PRD-220](prd_history/PRD-220.md) |
| PRD-221 | 6b3fef1 | Level diagram: NOW marker, % distance, entry-gap band | COMPLETE | [PRD-221](prd_history/PRD-221.md) |
| PRD-222 | b4a315c | Level diagram: label anchor NOW, drop redundant marker + empty band (PRD-221 patch) | COMPLETE | [PRD-222](prd_history/PRD-222.md) |
| PRD-223 | e654ca0 | Numeric entry→stop risk band on the level ladder (from contract trade_candidates) | COMPLETE | [PRD-223](prd_history/PRD-223.md) |
| PRD-224 | 204a5b8 | Macro-tape glyph alignment (GC/SI pad) + PRD-223 review fast-follows | COMPLETE | [PRD-224](prd_history/PRD-224.md) |
| PRD-225 | 9cc751c | Trend-structure mobile rows: uniform wrap (alignment-cell min-width + tighter gap) | COMPLETE | [PRD-225](prd_history/PRD-225.md) |
| PRD-226 | — | Level diagram NOW anchor = current price (contract entry is a separate ENTRY level, never NOW) | IN PROGRESS | [PRD-226](prd_history/PRD-226.md) |
| PRD-227 | — | Correct PRD-221 registry provenance (phantom 6b3fef1 → merged 8faa675) | IN PROGRESS | [PRD-227](prd_history/PRD-227.md) |
| PRD-228 | a11481b | Bot-review-thread disposition clause (governance guardrail) | COMPLETE | [PRD-228](prd_history/PRD-228.md) |
| PRD-229 | #99 | Ceremony tiering: cosmetic MICRO carve-out + same-PR closeout | COMPLETE | [PRD-229](prd_history/PRD-229.md) |
| PRD-230 | #99 | Process drop-list: Codex-authenticity teardown, cadence right-sizing, sediment stop, map de-line-numbering, process-doc dedup | COMPLETE | [PRD-230](prd_history/PRD-230.md) |
| PRD-231 | #99 | Doc-truth micro-fixes: qualification gate count (9→11), output.py dead runtime.py reference | COMPLETE | [PRD-231](prd_history/PRD-231.md) |
| PRD-232 | #99 | Guardrail tightening: skills learn PRD-229 rules, prd_open scaffold aligned to template, CLAUDE.md/CODEX.md dedup | COMPLETE | [PRD-232](prd_history/PRD-232.md) |
| PRD-233 | #100 | Wire assert_valid_contract into _run_pipeline + system_state key guard | COMPLETE | [PRD-233](prd_history/PRD-233.md) |
| PRD-234 | — | Kill the VALIDATED fail-open default: missing chain evidence renders MANUAL CHECK, never validated | IN PROGRESS | [PRD-234](prd_history/PRD-234.md) |

> **PRD-035 note:** Signal Forge dashboard strip is fully wired. Rendering requires HTTP serving, file picker, or valid raw JSON paste path. Direct filesystem access may block fetch().

---

## Audit Reports

| PRD | File |
|-----|------|
| PRD-016 | [docs/prd_history/AUDIT_PRD016.md](prd_history/AUDIT_PRD016.md) |
