# Owner design-direction ruling - Morning Executor Truthfulness + Gate Swap

MATERIAL packet: Morning Executor Truthfulness + Gate Swap
Corrected packet head: 503f8dae694aa1ba2d0036bfffa7bb18212fe3ca
Sol exact-corrected-head confirmation: ACCEPT (PACKET.review.sol.confirmation.md)

These are OWNER DESIGN DIRECTIONS. They are NOT Gate A. They are NOT implementation authorization. PRD-295 / Slice 1 (fail-loud) may proceed through Stage-0 review toward its own Gate A. PRD 2 (gate swap) remains subject to its own Stage-0, review, Gate A, and required live evidence.

## Owner design-direction rulings D1-D6 (Dustin, 2026-08-10)

D1: PRD 2 MAY PROPOSE removing repository-wide pytest/ruff from the time-sensitive morning runtime path, contingent on current branch-protection premise verification before Gate A.

D2: PRD 2 MAY PROPOSE:
  contents: write
  actions: read
No checks:read unless later evidence proves it necessary.

D3: CI_PENDING policy direction = HYBRID. Initial maximum bounded wait = 120 seconds. SUCCESS proceeds. PENDING may wait within budget then named-fails. MISSING / FAILED / CI_PROOF_ERROR / REVISION_DRIFT fail named and closed. The 120-second value remains falsifiable by the required larger latency sample.

D4: YES to a separate non-blocking full-suite DRIFT observation. It does not gate slots, authorize observations, satisfy exact-SHA CI proof, or alter market artifacts.

D5: Use a dedicated scripts/check_runtime_readiness.py. It is limited to deterministic local/runtime prerequisites and must not become a partial pytest suite or market-semantic validator.

D6: Use explicit current-workflow failure context only. Never derive current failure cause/date from stale latest_run.json. Require executable handler red tests with stale observation state present and Telegram transport isolated.

## Status

- These rulings authorize downstream PRD DRAFTING and Stage-0 progression only.
- Gate A and implementation authorization remain reserved to Dustin, per PRD, after independent review.
- The morning-executor packet cycle (packet review REQUIRED CHANGES -> one bounded correction -> Sol exact-corrected-head confirmation ACCEPT) is recorded in PACKET.md, PACKET.review.sol.md, and PACKET.review.sol.confirmation.md on this branch.
