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
| PRD-019 | c7c64c9, 0aea646 | Engine doctor — canonical pipeline health authority | COMPLETE | [PRD-019](prd_history/PRD-019.md) |
| PRD-020 | 0472cfd | Engine doctor gate system (CI + runtime guardrails) | COMPLETE | [PRD-020](prd_history/PRD-020.md) |
| PRD-021 | e6b017c | Documentation canonicalization (README + docs system) | COMPLETE | [PRD-021](prd_history/PRD-021.md) |
| PRD-022 | 2b6009a | Sunday mode isolation — no live data, forced STAY_FLAT, non-live execution path | COMPLETE | [PRD-022](prd_history/PRD-022.md) |
| PRD-023 | 314ca46 | GLD–DXY correlation policy layer — advisory risk_modifier, no qualification mutation | COMPLETE | [PRD-023](prd_history/PRD-023.md) |
| PRD-024 | 6f97d12 | Contract UI consumer — static HTML read-only decision surface | COMPLETE | [PRD-024](prd_history/PRD-024.md) |
| PRD-025 | 3d532cd | Decision compression layer — primary signal and trade promotion | COMPLETE | [PRD-025](prd_history/PRD-025.md) |
| PRD-026 | 442b813 | Alert visibility upgrade — deterministic ASCII titles and structured body | COMPLETE | [PRD-026](prd_history/PRD-026.md) |
| PRD-027 | b8dc599 | Context report layer — deterministic premarket and postmarket reports | COMPLETE | [PRD-027](prd_history/PRD-027.md) |
| PRD-028 | — | PRD system hardening — template, lifecycle states, file enforcement, scope lock | IN PROGRESS | [PRD-028](prd_history/PRD-028.md) |
| PRD-029 | — | Level awareness layer — derived price levels for premarket and postmarket reports | PROPOSED | [PRD-029](prd_history/PRD-029.md) |

---

## Audit Reports

| PRD | File |
|-----|------|
| PRD-016 | [docs/prd_history/AUDIT_PRD016.md](prd_history/AUDIT_PRD016.md) |
