# PROJECT_STATE.md

Project: Cutting Board

Latest completed PRD: PRD-061
Current active PRD: none

Status:
- PRD-061 COMPLETE (PRD Registry Numbering Guard)
- PRD-060 COMPLETE (Deterministic macro pressure snapshot)
- PRD-059 COMPLETE (Macro Tape value row hardening)
- PRD-032 DEPRECATED (R2–R6 implemented across subsequent PRDs; R1 superseded by design)

Test baseline:
- 1661 passing

Architecture:
- audit.jsonl → trade decisions (exists: logs/audit.jsonl)
- evaluation.jsonl → trade outcomes (planned, not yet built)

Constraints:
- evaluation is downstream-only
- no mutation of decision logic
- same-session evaluation only
- no backtesting
