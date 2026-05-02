# Review Scorecard Schema

Output path: `logs/review_scorecard_YYYY-MM-DD.json`

Existing files for the same date are overwritten.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| trade_date | string | ISO-8601 date (YYYY-MM-DD) |
| total_records | int | All journal records for the date |
| entered_count | int | Records with action == ENTERED |
| skipped_count | int | Records with action == SKIPPED |
| missed_count | int | Records with action == MISSED |
| exited_count | int | Records with action == EXITED |
| planned_trade_count | int | Records with intent == PLANNED_TRADE |
| impulse_trade_count | int | Records with intent == IMPULSE_TRADE |
| thesis_followed_count | int | Records with thesis_adherence == FOLLOWED_THESIS |
| thesis_violated_count | int | Records with thesis_adherence == VIOLATED_THESIS |
| no_thesis_count | int | Records with thesis_adherence == NO_THESIS |
| mistake_counts | dict[str, int] | Label → count, NONE excluded |
| process_flags | list[str] | See flags below |
| overall_process_grade | string | A / B / C / D / F / INSUFFICIENT_DATA |

## Grade Rules (priority order)

1. `INSUFFICIENT_DATA` — no records for date or journal missing
2. `F` — any REVENGE_TRADE or BROKE_RULES label
3. `D` — any ENTERED record has NO_THESIS or VIOLATED_THESIS thesis_adherence
4. `C` — any record has intent == IMPULSE_TRADE
5. `B` — all ENTERED records have FOLLOWED_THESIS, but non-NONE mistakes exist
6. `A` — all ENTERED records have FOLLOWED_THESIS and no non-NONE mistakes; OR entered_count == 0 and all mistake_labels == ["NONE"]

## Process Flags

| Flag | Condition |
|------|-----------|
| NO_TRADES_RECORDED | total_records == 0 |
| IMPULSE_TRADE_PRESENT | impulse_trade_count > 0 |
| THESIS_VIOLATION_PRESENT | any ENTERED record has thesis_adherence == VIOLATED_THESIS |
| NO_THESIS_ENTRY_PRESENT | any ENTERED record has thesis_adherence == NO_THESIS |
| REVENGE_TRADE_PRESENT | any record has REVENGE_TRADE in mistake_labels |
| OVERTRADING_PRESENT | OVERTRADED in mistake_counts |
| CLEAN_PROCESS_DAY | overall_process_grade == A (exclusive) |
| INSUFFICIENT_DATA | overall_process_grade == INSUFFICIENT_DATA (exclusive) |
