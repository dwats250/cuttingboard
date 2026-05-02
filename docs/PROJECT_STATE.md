# PROJECT_STATE.md

Project: Cutting Board

Latest completed PRD: PRD-064
Current active PRD: none

Status:
- PRD-064 COMPLETE (Trade Visibility Layer — Near-Miss Engine)
- PRD-063 COMPLETE (Macro Pressure Execution Policy Integration)
- PRD-062 COMPLETE (Macro Pressure Block in Signal Forge Dashboard)
- PRD-061 COMPLETE (PRD Registry Numbering Guard)
- PRD-060 COMPLETE (Deterministic macro pressure snapshot)
- PRD-032 DEPRECATED (R2–R6 implemented across subsequent PRDs; R1 superseded by design)

Test baseline:
- 1710 passing

Architecture:
- audit.jsonl → trade decisions (exists: logs/audit.jsonl)
- evaluation.jsonl → trade outcomes (planned, not yet built)

Constraints:
- evaluation is downstream-only
- no mutation of decision logic
- same-session evaluation only
- no backtesting
