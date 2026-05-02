# PROJECT_STATE.md

Project: Cutting Board

Latest completed PRD: PRD-068
Current active PRD: none

Status:
- PRD-068 COMPLETE (Invalidation and Exit Guidance Layer)
- PRD-067 COMPLETE (Trade Thesis Gate)
- PRD-075 COMPLETE (Signal Performance Engine)
- PRD-072 COMPLETE (Macro Drivers Snapshot Fallback)
- PRD-066 COMPLETE (Trade Drilldown Panel — Deterministic Explanation Layer)
- PRD-065 COMPLETE (Signal Forge Interactive Dashboard Controls)
- PRD-064 COMPLETE (Trade Visibility Layer — Near-Miss Engine)
- PRD-063 COMPLETE (Macro Pressure Execution Policy Integration)
- PRD-062 COMPLETE (Macro Pressure Block in Signal Forge Dashboard)
- PRD-061 COMPLETE (PRD Registry Numbering Guard)
- PRD-060 COMPLETE (Deterministic macro pressure snapshot)
- PRD-032 DEPRECATED (R2–R6 implemented across subsequent PRDs; R1 superseded by design)

Test baseline:
- 1806 passing

Architecture:
- audit.jsonl → trade decisions (exists: logs/audit.jsonl)
- evaluation.jsonl → trade outcomes (planned, not yet built)

Constraints:
- evaluation is downstream-only
- no mutation of decision logic
- same-session evaluation only
- no backtesting
