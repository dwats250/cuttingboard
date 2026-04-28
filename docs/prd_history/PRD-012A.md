PRD-012A — Guarantee Hourly Telegram Alerts via Dedicated GitHub Workflow

STATUS
COMPLETE
Commit: 0d6b0215

GOAL
Add a dedicated hourly alert workflow and NOTIFY_HOURLY runtime mode so Telegram alerts fire on a fixed schedule independent of the premarket run.

SCOPE
- Add .github/workflows/hourly_alert.yml: dedicated workflow with weekday schedule and isolated concurrency group
- Add NOTIFY_HOURLY mode to runtime.py: layers 1–7 always, layer 8 only if posture != STAY_FLAT
- Add _build_hourly_candidate_lines(), format_hourly_notification(), _format_hourly() to notifications/
- Write traceback.txt on exception before notification attempt
- Add 21 tests

OUT OF SCOPE
- No changes to premarket workflow
- No changes to contract schema

FILES
A .github/workflows/hourly_alert.yml
M cuttingboard/notifications/__init__.py
M cuttingboard/notifications/formatter.py
M cuttingboard/runtime.py

REQUIREMENTS

R1 — Dedicated Workflow
hourly_alert.yml MUST have a concurrency group separate from the main workflow.
MUST run on weekday schedule.

FAIL: hourly_alert.yml shares concurrency group with cuttingboard.yml.

R2 — NOTIFY_HOURLY Mode
NOTIFY_HOURLY MUST run layers 1–7 unconditionally.
Layer 8 (chain validation) MUST run only if posture != STAY_FLAT.
Layers 9–10 MUST NOT run in NOTIFY_HOURLY mode.

FAIL: NOTIFY_HOURLY runs chain validation when posture == STAY_FLAT.

R3 — Hourly Format Paths
format_hourly_notification MUST produce exactly one of: SETUP READY / NO SETUP / STAY FLAT.

FAIL: Output contains a status string outside those three values.

R4 — Candidate Filtering
_build_hourly_candidate_lines MUST exclude: ^VIX, ^TNX, DX-Y.NYB, BTC-USD.

FAIL: Hourly notification includes any of the four excluded symbols as a trade candidate.

R5 — Exception Traceability
On any exception before notification, runtime MUST write traceback.txt before attempting notification.

FAIL: Exception occurs and traceback.txt is not written.

DATA FLOW
hourly_alert.yml → runtime NOTIFY_HOURLY → layers 1–7 → format_hourly_notification → send_telegram

FAIL CONDITIONS
- Chain validation runs on STAY_FLAT in hourly mode
- Excluded symbols appear as candidates
- Traceback not written on exception

VALIDATION
Run: pytest -q (21 new tests)
Manual: trigger hourly workflow, confirm Telegram message received in correct format.
