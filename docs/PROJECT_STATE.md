# PROJECT_STATE.md

Project: Cutting Board

Latest completed PRD: PRD-048
Current active PRD: PRD-032 (PATCH — catastrophic output and validation contract repair)

Status:
- PRD-048 COMPLETE (Trade Decision Visibility in Payload and Dashboard)
- PRD-032 OPEN PATCH (no commit — genuinely unresolved)

Test baseline:
- 1441 passing

Architecture:
- audit.jsonl → trade decisions
- evaluation.jsonl → trade outcomes

Constraints:
- evaluation is downstream-only
- no mutation of decision logic
- same-session evaluation only
- no backtesting
