# PRD Registry

All product requirement documents for the cuttingboard decision engine, in order.

---

| PRD | Commit(s) | Title | Status |
|-----|-----------|-------|--------|
| Init | d84cd027 | Bootstrap — initial PRD committed | COMPLETE |
| PRD-001 | d37e72f, 094b428 | 10-layer pipeline bootstrap — full system, 297 tests, GHA workflow | COMPLETE |
| PRD-002 | 6bc67e6, 3d4a214 | Options chain validation + runtime orchestrator | COMPLETE |
| PRD-003 | 809214bc | Enforce deterministic failure visibility in CI pipeline | COMPLETE |
| PRD-003.2 | 7838f461 | Fix remaining workflow patch drift | COMPLETE |
| PRD-003.3 | 6202bc9e | Fix CI failure-path guards | COMPLETE |
| PRD-003.4 | c004db9c | Replace stale workflow lines exactly | COMPLETE |
| PRD-004 | b5505613, 08117400 | Contract alignment — audit contract, stale data validation | COMPLETE |
| PRD-005 | 61af9214 | Separate run alert routing from trade formatting; fix STAY_FLAT crash; enforce runtime failure artifacts | COMPLETE |
| PRD-006 | d1984113, 1b11010 | Remove ntfy transport; enforce Telegram-only notification path | COMPLETE |
| PRD-007 | ab3d20b8 | Imbalance pullback entry (FVG) — qualification and options layers | COMPLETE |
| PRD-008 | 30b583a0 | Expansion regime detection + continuation entry mode | COMPLETE |
| PRD-009 | f4ddb677 | Canonical timezone handling + time gate validation | COMPLETE |
| PRD-010 | de6c0a6a | Continuation rejection audit + threshold calibration | COMPLETE |
| PRD-011 | e6896f39 | Freeze canonical pipeline output contract | COMPLETE |
| PRD-012 | b90c8938 | Deterministic payload delivery layer — adapter and transport | COMPLETE |
| PRD-012 (cleanup) | b336b2f4 | Post-audit cleanup: remove dead code, fix symbols_scanned, enforce determinism | COMPLETE |
| PRD-012A | 0d6b0215 | Guarantee hourly Telegram alerts via dedicated GitHub workflow | COMPLETE |
| PRD-013 | b17be17f | Flow alignment soft gate in qualification pipeline | COMPLETE |
| PRD-014 | 30ce0adc | Structural hardening, flow wiring, config-driven ingestion | COMPLETE |
| PRD-015 / 015.1 | 30ce0adc | Flow wiring and ingestion config consolidation (bundled with PRD-014) | COMPLETE |
| PRD-016 / 016.1 | 3d707356 | Pre-UI audit: legacy cleanup, interface lock, output contract verification | COMPLETE |
| PRD-017 | fc7f5e9 | Notification delivery stabilization: rate limit, retry, aggregation, audit | COMPLETE |
| PRD-018 | 0f7c341 | Notification signal hierarchy and suppression: state key, priority, dedup | COMPLETE |
| PRD-019 | c7c64c9, 0aea646 | Engine doctor — canonical pipeline health authority | COMPLETE |
| PRD-020 | 0472cfd | Engine doctor gate system (CI + runtime guardrails) | COMPLETE |
| PRD-021 | e6b017c | Documentation canonicalization (README + docs system) | COMPLETE |
| PRD-022 | 2b6009a | Sunday mode isolation — no live data, forced STAY_FLAT, non-live execution path | COMPLETE |
| PRD-023 | 314ca46 | GLD–DXY correlation policy layer — advisory risk_modifier, no qualification mutation | COMPLETE |
| PRD-024 | 6f97d12 | Contract UI consumer — static HTML read-only decision surface | COMPLETE |
| PRD-025 | 3d532cd | Decision compression layer — primary signal and trade promotion | COMPLETE |
| PRD-026 | 442b813 | Alert visibility upgrade — deterministic ASCII titles and structured body | COMPLETE |

---

## Audit Reports

| PRD | File |
|-----|------|
| PRD-016 | [docs/prd_history/AUDIT_PRD016.md](prd_history/AUDIT_PRD016.md) |
