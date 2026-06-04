# PRD-157 Fixture-Verification Gate — Report

**Date:** 2026-06-04
**Objective:** Clear (or block) the binding post-B4 pause before B1/B2/W4.
**Source gate:** `docs/prd_history/PRD-157.md` IMPLEMENTATION WATCHOUTS ("After B4 lands: PAUSE before B1/B2") and `audits/recon-2026-05-24/next-batch-staging.md` (B4 → fixture verification [GATING] → B1/B2).
**No production logic was modified; working tree was restored to clean after the run.**

---

## 1. Commands run

```bash
# Inspected gate spec
#   docs/PROJECT_STATE.md (PRD-157 entry + IMPLEMENTATION WATCHOUTS)
#   docs/prd_history/PRD-157.md (R6 sizing-field contract)
#   audits/recon-2026-05-24/next-batch-staging.md (B4/W4 gate definition)

# Backed up artifacts -> /tmp/cb_gate_backup/ (logs/ is git-tracked)

# Fixture pipeline run (no live network)
FIXTURE_MODE=1 python3 -m cuttingboard --mode fixture --fixture-file tests/fixtures/2026-04-12.json
#   -> exit 0, mode=FIXTURE, chain_validation = "fixture mode skips live chain validation"

# Inspected logs/latest_payload.json (.sections.top_trades) and logs/run_2026-04-12_130000.json
# Confirmed ^VIX in config.NON_TRADABLE_SYMBOLS
# Restored tree: git checkout -- logs/{audit.jsonl,latest_payload,latest_run,macro_drivers_snapshot,market_map}.json
# git status -> clean
```

## 2. Fixture artifacts inspected

- `logs/latest_payload.json` — `meta.generation_id = fixture-fixture-2026-04-12`, `meta.fixture_mode = true`. **The three PRD-157 sizing fields land here**, at `.sections.top_trades[0]` — *not* in `latest_contract.json` (which the fixture run does not rewrite; it still held a stale `live-20260513` artifact with 0 candidates).
- `logs/run_2026-04-12_130000.json` — run summary: `regime=EXPANSION`, `outcome=NO_TRADE`, `candidates_generated=8`, `candidates_qualified=0`, `candidates_watchlist=5`.

**Only one fixture date exists in the repo (`tests/fixtures/2026-04-12.json`).** "A few days of fixture output" is not literally achievable — fixture output is deterministic, so this is a single snapshot.

## 3. Field-by-field sanity

Single sized candidate (`sections.top_trades[0]`):

| Field | Value | Sane? | Reasoning |
|---|---|---|---|
| `position_size` | `2` | math ✅ / context ⚠️ | Positive integer. But `size_multiplier=0.0` and `decision_status=BLOCK_TRADE` on the same record — see D2. |
| `dollar_risk` | `150.0` | ✅ | Exactly the 1% cap: `ACCOUNT_EQUITY(15000) × MAX_RISK_PCT(0.01) × EXPANSION_mult(1.0)`. At cap, not over. |
| `estimated_debit` | `75.0` | ✅ | `spread_width(0.75) × 100`, per R6. Positive, plausible per-contract debit. |
| **Coherence** | `2 × 75 = 150` | ✅ | `position_size × estimated_debit == dollar_risk` holds exactly. |

**The sizing arithmetic is correct and coherent**, and matches the PRD-157 regression pins (`position_size=2, dollar_risk=150.0, estimated_debit=75.0`). B4's emission contract is intact.

## 4. Contradictions / missing fields

- **D1 — Non-tradable instrument sized as a trade.** The only sized candidate is **`^VIX`**, confirmed in `config.NON_TRADABLE_SYMBOLS`. A bull-call-spread on the VIX index is not something you "type into Moomoo" (the W4 anchor). A non-tradable macro driver should not surface in `top_trades` with a position size.
- **D2 — `position_size` ignores `size_multiplier=0.0`.** The record is `decision_status=BLOCK_TRADE`, `policy_allowed=false`, `size_multiplier=0.0`, yet `position_size=2`. A W4 report reading `position_size` verbatim would print "2 contracts" for a zero-sized, blocked trade.
- **D3 — `outcome=NO_TRADE` + populated `top_trades`.** `candidates_qualified=0` but `top_trades` has an entry. The exact PRD-162-candidate (now **PRD-163**) contradiction, observed live.
- **Not missing:** all three R6 sizing fields are present and typed correctly.

The `block_reason` here ("fixture mode skips live chain validation") is expected fixture behavior, not a defect — but it means the sized candidate is a **blocked watchlist item, not a recommendation.**

## 5. Realizability finding (why a synthetic fixture cannot reach ALLOW_TRADE)

Traced during this gate:

- `cuttingboard/trade_decision.py:101` — `status = ALLOW_TRADE if chain.classification == VALIDATED else BLOCK_TRADE`.
- `cuttingboard/runtime.py:1558-1564` (`_fixture_chain_results`) — fixture mode **unconditionally** stamps every setup `classification=MANUAL_CHECK`.

Therefore **every fixture-mode candidate is forced to `BLOCK_TRADE` / `policy_allowed=false` / `size_multiplier=0.0`** at the chain stage, before execution policy runs. No fixture input produces `ALLOW_TRADE` without changing `_fixture_chain_results` (production logic). The sizing fields, however, are populated regardless of block status — so a deterministic fixture **can** verify the raw sizing math against a realistic tradable instrument, just not the multiplier-adjusted, policy-cleared values the live W4 path will consume.

## 6. Verdict

> ## 🔴 GATE BLOCKED

**Not because the sizing math is wrong** — it is arithmetically correct, coherent, and at the expected cap. The gate is blocked because its success condition — *"confirm the values match what would actually be traded"* — cannot be met on the available fixture: the only sized candidate is **non-tradable (`^VIX`), `BLOCK_TRADE`, `size_multiplier=0.0`** under `outcome=NO_TRADE`. There is no realistically-tradable candidate to gut-check against, and the fields ride on a record a W4 report would misrepresent (D1/D2). Layering B1/B2/W4 on this surface now risks building the pre-market report against sizing never validated against a real, tradable setup.

## 7. Smallest follow-up to clear the gate

**PRD-161 (MICRO / FIXTURE) — "Add tradable qualified fixture for PRD-157 sizing gate."** Add fixture coverage that produces at least one **qualified, tradable** candidate (symbol ∉ `NON_TRADABLE_SYMBOLS`) that surfaces in `top_trades` with present, positive, coherent (`position_size × estimated_debit ≤ dollar_risk`) sizing, deterministically — with **no production logic change**.

Per the realizability finding (§5), the criteria are scoped to a `MANUAL_CHECK` candidate: `decision_status=ALLOW_TRADE`, `policy_allowed=true`, and `size_multiplier>0` are **dropped as unrealizable in fixture mode** and documented as such in the PRD. This still verifies the gate's real intent (B4 sizing against a realistic tradable instrument), matching PRD-157's original watchout ("inspect the sizing values").

## 8. Separately filed (not part of clearing this gate)

- **D1/D2/D3** should sharpen **PRD-163** (candidate; outcome / `market_map` reconciliation — renumbered from PRD-162). Specifically: gate `top_trades` against `NON_TRADABLE_SYMBOLS` (D1), reconcile `position_size` with `size_multiplier`/`decision_status` (D2), and reconcile `outcome` with populated `top_trades` (D3). **Not fixed in PRD-161.**

---

**State left behind:** working tree restored to HEAD before scaffolding (backup at `/tmp/cb_gate_backup/`); B1/B2/W4 untouched and un-opened.
