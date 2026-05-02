# Manual Trade Journal Schema

**File:** `logs/manual_trades.jsonl`
**Format:** Newline-delimited JSON (JSONL), append-only

---

## Record Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `recorded_at_utc` | ISO-8601 UTC string | auto | Set at write time; never supplied by caller |
| `trade_date` | YYYY-MM-DD string | yes | Trading session date |
| `symbol` | string | yes | Ticker symbol |
| `action` | enum | yes | See below |
| `direction` | enum | yes | See below |
| `instrument_type` | enum | yes | See below |
| `thesis_adherence` | enum | yes | See below |
| `intent` | enum | yes | See below |
| `mistake_labels` | list[enum] | yes | Must not be empty; use `["NONE"]` if no mistake |
| `system_candidate_id` | string or null | no | Links to a system-generated candidate if applicable |
| `notes` | string or null | no | Free-text annotation |

---

## Allowed Values

### action
`CONSIDERED`, `ENTERED`, `EXITED`, `SKIPPED`, `MISSED`, `CANCELLED`

### direction
`LONG`, `SHORT`, `NEUTRAL`, `UNKNOWN`

### instrument_type
`STOCK`, `ETF`, `OPTION`, `OPTION_SPREAD`, `CASH`, `UNKNOWN`

### thesis_adherence
`FOLLOWED_THESIS`, `VIOLATED_THESIS`, `NO_THESIS`, `THESIS_UNKNOWN`

### intent
`PLANNED_TRADE`, `IMPULSE_TRADE`, `HEDGE`, `TEST_SIZE`, `EXIT_MANAGEMENT`, `REVIEW_ONLY`, `UNKNOWN`

### mistake_labels
`CHASED_ENTRY`, `OVERSIZED`, `ENTERED_WITHOUT_THESIS`, `IGNORED_INVALIDATION`, `IGNORED_MACRO_CONFLICT`, `ENTERED_LATE`, `EXITED_EARLY`, `HELD_TOO_LONG`, `TOOK_LOW_QUALITY_SETUP`, `REVENGE_TRADE`, `OVERTRADED`, `BROKE_RULES`, `NONE`

**Rules:**
- Must contain at least one element.
- `NONE` must be the only element when present.
- Mixing `NONE` with any other label raises `ValueError`.

---

## Example Record

```json
{
  "recorded_at_utc": "2026-05-01T14:32:00.123456+00:00",
  "trade_date": "2026-05-01",
  "symbol": "SPY",
  "action": "ENTERED",
  "direction": "LONG",
  "instrument_type": "OPTION",
  "thesis_adherence": "FOLLOWED_THESIS",
  "intent": "PLANNED_TRADE",
  "mistake_labels": ["NONE"],
  "system_candidate_id": "SPY-LONG-20260501",
  "notes": null
}
```

---

## Constraints

- Records are append-only. Never modify or delete existing records.
- `manual_journal.py` must not be imported by `runtime.py`, `contract.py`, or any delivery module.
- This schema is consumed by PRD-071 (Trading Process Review Scorecard).
