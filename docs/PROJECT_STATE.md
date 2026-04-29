# PROJECT_STATE.md

Project: Cutting Board

Latest completed PRD: PRD-047
Current active PRD: PRD-048

Status:
- PRD-047 COMPLETE (Post-Trade Evaluation Layer)
- PRD-048 IN PROGRESS (Trade Decision Visibility)

Test baseline:
- 1407 passing

Architecture:
- audit.jsonl → trade decisions
- evaluation.jsonl → trade outcomes

Constraints:
- evaluation is downstream-only
- no mutation of decision logic
- same-session evaluation only
- no backtesting
