PRD-012 Cleanup — Post-Audit Dead Code Removal and Determinism Enforcement

STATUS
PATCH
Commit: b336b2f4

ROOT CAUSE
missing fail condition — PRD-012 did not include a FAIL condition for dead code paths or the symbols_scanned watchlist omission, allowing both to survive review.

GOAL
Remove dead code identified in post-merge audit, fix symbols_scanned to include watchlist count, and enforce deterministic timestamp handling in output.py.

FILES
M cuttingboard/delivery/payload.py
M cuttingboard/output.py
M tests/test_delivery.py

REQUIREMENTS

R1 — Dead Code Removal
_NULLABLE_FIELDS constant in payload.py MUST be removed.
fake_contract in output.render_report_from_payload MUST be removed.

FAIL: Either dead symbol remains after merge.

R2 — symbols_scanned Completeness
symbols_scanned MUST equal qualified + rejected + watchlist count.

FAIL: symbols_scanned excludes watchlist candidates.

R3 — Deterministic Timestamp
output.py MUST raise ValueError on unparseable timestamp.
datetime.now() fallback MUST NOT exist in output.py.

FAIL: output.py falls back to datetime.now() on timestamp parse failure.

DATA FLOW
payload.py symbols_scanned → qualified + rejected + watchlist
output.py timestamp → parse → ValueError on failure (no fallback)

FAIL CONDITIONS
- Dead constants or functions remain
- symbols_scanned undercounts
- datetime.now() fallback present

VALIDATION
Run: pytest tests/test_delivery.py -q
Confirm: symbols_scanned watchlist cases pass, timestamp failure raises ValueError.
