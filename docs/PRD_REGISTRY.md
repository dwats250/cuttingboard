# PRD Registry

All product requirement documents for the cuttingboard decision engine, in order.

---

| PRD | Commit(s) | Title | Status |
|-----|-----------|-------|--------|
| Init | d84cd027 | Bootstrap — initial PRD committed | COMPLETE |
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

---

## Audit Reports

| PRD | File |
|-----|------|
| PRD-016 | [docs/AUDIT_PRD016.md](AUDIT_PRD016.md) |

---

## How to use this file

- Add a row when a new PRD is defined (before coding begins).
- Link to an audit report doc when a formal pre/post audit is performed.
- Status: `IN PROGRESS` while active, `COMPLETE` when merged to main.
