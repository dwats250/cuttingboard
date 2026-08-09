# Dev-bootstrap MATERIAL packet (QW-5) — 2026-08-09

Upstream GOV-2 MATERIAL packet for QW-5 (idempotent developer bootstrap: an
explicit `scripts/dev_bootstrap.sh` + a thin `.claude/settings.json`
SessionStart hook). RESEARCH/DESIGN ONLY — this branch mutates no PRD, no
production/config/script/test. Its job is to durably establish the
already-discovered boundary so the downstream Stage-0 PRD + Gate A can bind it.

Provenance: consolidates the boundary discovered by the Sol@xhigh fresh-context
review of the PRD-293 draft (reviewed head `27c35288`, verdict ACCEPT WITH
REQUIRED CHANGES) and the read-only recon of `origin/main` `a87d203f`. That Sol
review predates this packet and is retained as evidence/input, not as the GOV-2
packet review.

## 1. PURPOSE / USER FRICTION
Remote/mobile sessions (e.g. an Asher checkout) routinely start with the
`cuttingboard` package not installed into a usable environment. The exact
failure removed: the first agent tool call that runs `pytest`, `ruff`, or
`import cuttingboard` errors, because no editable install / usable `.venv`
exists (reconciliation debt **F-5**, "remote-session env unbootstrapped — a
known trap"). QW-5 makes a session self-heal by owning a repo-local `.venv` and
publishing it to the session, invoked idempotently at session start.

## 2. AUTHORITY / MATERIALITY
- **MATERIAL / INFRA.** The material surface is NEW automated SessionStart
  execution wired into `.claude/settings.json` (a change to how every session
  initializes) — not the small LOC. GOV-2 §1 applies (a change to the agent's
  own execution configuration; automated code runs each session).
- **GOV-2 applicability:** MATERIAL intake → this upstream packet → independent
  Codex packet review → one consolidated correction → independent
  exact-corrected-head confirmation → Dustin design-direction ruling → Stage-0
  PRD reviewed against packet + ruling → Dustin Gate A → implementation.
- **No permission widening.** `permissions.allow` / `permissions.deny` are
  byte-unchanged; only a `SessionStart` hook is added. This is not a governance
  guardrail change to the review gates, and it forces no HIGH-RISK payload
  (`.claude/settings.json` is not a GOVERNANCE_PAYLOAD_FILE); LANE STANDARD.

## 3. CURRENT REPO STATE (origin/main a87d203f)
- `.venv` is already git-ignored (`.gitignore`); the venv convention is a
  repo-local `.venv` (settings.json allow lists `.venv/bin/pytest`).
- `pyproject.toml`: package `cuttingboard`, `requires-python = ">=3.11"`;
  runtime deps in `[project.dependencies]`; dev extras
  `[project.optional-dependencies].dev` = `pytest>=7.0.0`, `ruff==0.15.22`
  (PRD-273 exact pin — the lint contract must not move), `PyYAML>=6.0`.
- CI (`.github/workflows/ci.yml`): `pip install -e ".[dev]"` → `ruff check
  cuttingboard/ tests/` → `pytest tests/ -q`.
- Existing hooks in `.claude/settings.json`: PreToolUse (`protect_files.sh`,
  `canonical_read_guard.sh`), UserPromptSubmit (`prd_eval.sh`), each shaped
  `cd "${CLAUDE_PROJECT_DIR:-.}" && bash .claude/hooks/<x>.sh`. There is NO
  existing `SessionStart` hook. `scripts/install_hooks.sh` exists (git hooks).

## 4. DESIGN DIRECTION (proposed)
- **Repo-local `.venv` ownership.** The script owns ONLY `<repo>/.venv`; it
  ignores any activated/system environment.
- **Physical root** resolved from the script's own location, never caller cwd /
  `PYTHONPATH`.
- **Base Python creates the venv only:** first usable of `python3` then `python`
  (>=3.11 with `venv`) runs `<base> -m venv .venv`; the base interpreter NEVER
  runs pip.
- **Every pip via `.venv/bin/python -m pip install -e ".[dev]"`** from the repo
  root (so PEP 668 / externally-managed Python is irrelevant).
- **Isolated version-true readiness** (`.venv/bin/python -I`): owned interpreter
  >=3.11; `cuttingboard` imports from THIS checkout with EDITABLE metadata whose
  `direct_url.json` resolves to the current physical root; all runtime + dev
  requirements satisfied incl. PyYAML; ruff metadata AND `.venv/bin/ruff
  --version` == `0.15.22`; pytest module AND `.venv/bin/pytest` resolve.
- **`CLAUDE_ENV_FILE` binding after success only:** idempotently append
  safely-quoted `VIRTUAL_ENV=<repo>/.venv` + `.venv/bin`-first `PATH`; never on
  failure; never duplicated. Standalone human runs print the `.venv/bin` paths /
  activation instead.
- **SessionStart** bound to `startup|resume|clear`; `compact` EXCLUDED (a
  no-network failure would recur automatically); explicit timeout.
- **Failure = exit 2** (Claude surfaces a non-blocking hook error; session
  continues, stays usable); no `continue:false`; at most one venv-create + one
  pip per event; no internal retry.

## 5. AUTHORITY SURFACE / NON-GOALS (hard)
`permissions.allow` unchanged; `permissions.deny` unchanged; existing PreToolUse
+ UserPromptSubmit hooks unchanged; no CI publish-state helpers
(`ci_restore_publish_state.sh`, `ci_push_artifacts.sh`) / no CI workflow change;
no global/system installs; no Cloudflare / Options coupling; no
developer-environment-manager redesign; no settings.json refactor.

## 6. COMPLETE IMPLEMENTATION SURFACE
PAYLOAD (the only mutated code/config at implementation):
- `scripts/dev_bootstrap.sh`
- `.claude/settings.json` (minimal SessionStart hook only)
- `tests/test_dev_bootstrap.py`
Lifecycle (downstream PRD bookkeeping, NOT packet payload): the Stage-0 PRD doc,
its review artifact, `docs/PRD_REGISTRY.md`, `docs/prd_index.json`,
`docs/PROJECT_STATE.md`.

## 7. REVIEWED DESIGN CEILING (proposed)
- Exactly **3 payload files** (script, settings.json, one test file).
- **<= 90 net-production LOC** across the script + the settings-config addition
  (counting venv-ownership / probe / fail-loud / session-binding logic
  first-class, PRD-290).
- Test file uncapped, first-class validation.
- STOP-AND-RENEW (GOV-2 §5) on: a helper / 4th payload file / 2nd test file /
  any `permissions.allow`/`deny` change / any existing-hook change / >90
  net-production LOC.

## 8. FROZEN INVARIANTS (design-proposal evidence — NOT Gate-A-bound yet)
Imported from the corrected PRD-293 draft as proposal input; they become binding
only at Gate A on the reviewed Stage-0 PRD:
1. Physical root from script location, never accidental cwd.
2. `.venv` repo-local, non-symlinked, isolated from system site-packages,
   Python >=3.11.
3. Base interpreter order `python3`→`python`; base MAY create the venv, NEVER
   runs pip.
4. All pip via `.venv/bin/python` only.
5. Probe isolated from cwd/`PYTHONPATH`/user-site/activated env.
6. Editable provenance names the current physical checkout.
7. All declared runtime + dev requirements satisfy versions (incl. PyYAML).
8. Ruff executable AND metadata both == 0.15.22.
9. Pytest module AND `.venv/bin/pytest` both resolve.
10. Ready => zero pip.
11. Not-ready => at most one install + identical post-probe.
12. Wrong-version / incomplete-extra / absent-editable / moved-repo /
    wrong-checkout are NOT ready.
13. Broken/unsafe `.venv` fails without deletion/recreation/external fallback.
14. Session PATH/VIRTUAL_ENV binding only after readiness, idempotent.
15. Failure => stderr + exit 2; success => one concise line + exit 0.
16. SessionStart excludes `compact`; exact cwd-safe delegation
    (`cd "${CLAUDE_PROJECT_DIR:-.}" && bash scripts/dev_bootstrap.sh`).
17. `permissions.allow`/`deny`, PreToolUse, UserPromptSubmit unchanged.
18. No CI workflow/helper, Cloudflare, Options, global install, or unrelated
    file change.
19. Tests prove call counts + targets in temporary fixtures (fake executables /
    logging, no network) + mutation-discriminating failures for readiness,
    confinement, fail-loud.
20. Payload expansion or >90 net-production LOC => stop-and-renew.

## 9. FAILURE / STATE MATRIX
- **ready:** session-env binding + one status line; ZERO pip.
- **missing venv:** create, install once, post-probe.
- **incomplete deps:** install once, post-probe.
- **wrong ruff (not 0.15.22):** NOT ready → install once, post-probe.
- **moved checkout / venv reused from another checkout:** editable provenance
  fails → install retargets it, provided the venv is itself valid.
- **broken / symlinked / non-isolated / unsupported `.venv`:** fail visibly, NO
  deletion / recreation / system fallback.
- **pip failure:** exit 2, no success message, no env binding.
- **post-probe failure (install did not satisfy readiness):** exit 2, no
  success message, no env binding.

## 10. TEST / FALSIFICATION PLAN
Isolated temp-repo fixtures; fake `python`/`pip`/`ruff`/`pytest` executables with
call logging; NO network. Prove: second invocation on ready == no-op (zero pip);
existing-ready not reinstalled; missing prereqs fail (exit 2 + message);
wrong-ruff-version reads NOT ready; broken/symlinked `.venv` fails without
deletion; hook delegates (no embedded logic); `.claude/settings.json` valid JSON
and `permissions.allow`/`deny` byte-equal to main (assert); no unrelated file
mutation; `CLAUDE_ENV_FILE` binding idempotent + absent on failure; `compact`
excluded; script mode `100755`. Mutation-discriminating tests for readiness,
confinement, and fail-loud.

## 11. OPEN QUESTIONS (genuine, unresolved by the Sol review)
1. **`CLAUDE_ENV_FILE` line format:** confirm the exact expected syntax
   (`KEY=VALUE` lines appended, PATH prepend semantics) against the installed
   Claude Code version before the implementation relies on it; if the format is
   unavailable/unstable, the session-binding step degrades to a printed
   instruction (readiness/confinement unaffected).
2. **Runtime-dep version strictness:** the probe checks dev deps by exact
   contract (ruff pin); should `[project.dependencies]` runtime deps be checked
   by installed-and-satisfies-specifier (proposed) vs importability only?
   Proposed: satisfies-specifier, since the editable install drives them.
3. **Timeout value:** 300s proposed (matches a cold `pip install -e`); confirm
   headroom on the slowest supported remote/mobile target.

## 12. RECOMMENDED DESIGN-DIRECTION RULING (for Dustin)
Approve the boundary as stated: QW-5 = an idempotent repo-local-`.venv`-owning
`scripts/dev_bootstrap.sh` + a thin `startup|resume|clear` SessionStart hook
that delegates to it; version-true isolated readiness (incl. PyYAML + ruff
0.15.22 executable/version + editable provenance); `CLAUDE_ENV_FILE` binding on
success only; exit-2 fail-loud with `compact` excluded and no retry; 3 payload
files, <=90 net-production LOC, stop-and-renew on any expansion; zero permission/
existing-hook change. Then authorize a Stage-0 PRD carrying the 20 invariants as
Gate-A-binding, its fresh-context PRD review, and Gate A.
