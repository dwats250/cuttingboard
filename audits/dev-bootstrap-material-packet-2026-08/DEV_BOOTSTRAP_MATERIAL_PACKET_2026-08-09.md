# Dev-bootstrap MATERIAL packet (QW-5) — 2026-08-09

Upstream GOV-2 MATERIAL packet for QW-5 (idempotent developer bootstrap: an
explicit `scripts/dev_bootstrap.sh` + a thin `.claude/settings.json`
SessionStart hook). RESEARCH/DESIGN ONLY — this branch mutates no PRD, no
production/config/script/test. Its job is to durably establish the boundary so
the downstream Stage-0 PRD + Gate A can bind it.

Provenance: consolidates the boundary discovered by the Sol@xhigh review of the
PRD-293 draft (reviewed `27c35288`) and by the GOV-2 packet review of this
packet's first revision (`88fe58d`, ACCEPT-WITH-REQUIRED-CORRECTIONS); this
revision applies that packet review's 10 required corrections (the single GOV-1
consolidated cycle). Prior review prose is retained as evidence, not as this
packet's content.

## 1. PURPOSE / USER FRICTION
Remote/mobile sessions (e.g. an Asher checkout) routinely start with
`cuttingboard` not installed into a usable environment; the first agent tool
call running `pytest`, `ruff`, or `import cuttingboard` errors (reconciliation
debt **F-5**). QW-5 makes a session self-heal by owning a repo-local `.venv` and
publishing it to the session, idempotently at session start.

## 2. AUTHORITY / MATERIALITY
- **MATERIAL / INFRA.** The material surface is NEW automated SessionStart
  execution wired into `.claude/settings.json`; GOV-2 §1 applies.
- **GOV-2 order:** MATERIAL intake → this upstream packet → independent Codex
  packet review → one consolidated correction → independent exact-corrected-head
  confirmation → Dustin design-direction ruling → Stage-0 PRD reviewed against
  packet + ruling → Dustin Gate A → implementation.
- **No permission widening.** `permissions.allow`/`deny` byte-unchanged; only a
  `SessionStart` hook is added. LANE STANDARD (`.claude/settings.json` is not a
  GOVERNANCE_PAYLOAD_FILE).

## 3. CURRENT REPO STATE (origin/main a87d203f)
- `.venv` git-ignored; repo-local `.venv` convention (`.venv/bin/pytest` in the
  settings allow). NOTE (packet-review finding 3): the current checkout's ignored
  `.venv` has current-root editable provenance BUT stale installed metadata
  declaring `ruff>=0.4.0`, while `pyproject.toml` pins `ruff==0.15.22` — a live
  example of why readiness must key off current `pyproject.toml`, not installed
  metadata.
- `pyproject.toml`: `cuttingboard`, `requires-python = ">=3.11"`; runtime deps
  `[project.dependencies]`; dev extras `pytest>=7.0.0`, `ruff==0.15.22` (PRD-273
  pin), `PyYAML>=6.0`.
- CI: `pip install -e ".[dev]"` → `ruff check` → `pytest`.
- Existing hooks: PreToolUse (`protect_files.sh`, `canonical_read_guard.sh`),
  UserPromptSubmit (`prd_eval.sh`), each `cd "${CLAUDE_PROJECT_DIR:-.}" && bash
  .claude/hooks/<x>.sh`. NO existing `SessionStart` hook.
- **Claude Code 2.1.226** SessionStart sources: `startup`, `resume`, `clear`,
  `compact`, `fork`. `CLAUDE_ENV_FILE` is a per-session/per-hook SHELL SCRIPT
  (`sessionstart-hook-<index>.sh`) executed before Bash tool commands — NOT a
  dotenv file.

## 4. DESIGN DIRECTION (proposed, post-correction)
- **Own only `<repo>/.venv`.** Physical root resolved from the script's own
  location, never caller cwd/`PYTHONPATH`.
- **Interprocess serialization (NEW):** acquire a repo-scoped lock
  (`.venv`-adjacent, e.g. `flock` on a lockfile) around validate/create/install;
  RE-PROBE readiness after acquiring the lock (a concurrent starter may have just
  finished); bounded lock-wait, then fail-loud on contention timeout. No two
  processes create/install concurrently.
- **Base Python creates the venv only:** first usable of `python3` then `python`
  (>=3.11, `venv` present), invoked with `-I`; runs `<base> -I -m venv .venv`;
  the base NEVER runs pip.
- **Isolate every invocation:** `-I` (ignore env + user-site) for base
  validation, venv creation, the probe, and pip; pip in isolated/config-sanitized
  mode (`--isolated --no-input`, retries/connect bounded), and neutralize
  `PYTHONPATH`/`PYTHONHOME`/`PIP_*`/`PIP_TARGET`/pip config/cache overrides so no
  write escapes the owned venv.
- **Existing-`.venv` validation by RUNTIME IDENTITY** (not directory/exe
  existence): `.venv/bin/python -I` reports physical `sys.prefix ==
  <root>/.venv`, `sys.base_prefix != sys.prefix`, system-site disabled, no
  outside site-package path. A valid venv whose `.venv/bin/python` symlinks to a
  base interpreter is FINE; the failure case is the `.venv` DIRECTORY being a
  symlink or non-isolated. Broken/non-isolated/symlinked venv → fail-loud, NO
  deletion/recreation.
- **Version-true readiness** (isolated `.venv/bin/python -I`), source of truth =
  current `pyproject.toml` (NOT installed dist metadata): `cuttingboard` imports
  and `__file__` resolves under the current checkout; distribution is EDITABLE
  with `direct_url.json` `file:` URL canonically decoded and physically equal to
  the current root; PEP-440 specifier evaluation of EVERY current
  `[project.dependencies]` + `[project.optional-dependencies].dev` requirement
  (incl. PyYAML); ruff distribution metadata AND `.venv/bin/ruff --version` both
  exactly `0.15.22`; `.venv/bin/pytest --version` and `.venv/bin/python -I -m
  pytest --version` both EXECUTE (existence alone misses a stale shebang);
  structural isolation proved separately (no `.pth`/`sitecustomize` escape — `-I`
  alone does not cover this).
- **Session binding = shell exports (NEW, corrected):** because `CLAUDE_ENV_FILE`
  is an executed shell script, after readiness emit exactly ONE normalized block
  of safely-quoted `export VIRTUAL_ENV=<root>/.venv` and `export
  PATH=<root>/.venv/bin:$PATH`, written TRANSACTIONALLY — clear/replace this
  hook's owned content (no append accumulation, no duplicates). Never written on
  failure; if a stale success-binding may persist in the owned file, the invariant
  is: on any run that reaches the binding step, the owned block is fully rewritten
  or removed, so a later failure cannot leave a stale success-binding loaded (if
  the file is unwritable, the "no binding on failure" guarantee is narrowed
  explicitly and reported).
- **SessionStart** bound to `startup|resume|clear|fork` (INCLUDE `fork` per the
  2.1.226 source list); `compact` EXCLUDED (a no-network failure would recur
  automatically); explicit seconds timeout.
- **Failure = exit 2** (for SessionStart the client displays stderr and continues
  initialization; the session stays usable — this is the operational effect;
  "non-blocking hook error" was inaccurate terminology). No `continue:false`; at
  most one venv-create + one pip per event; NO retry (and pip's own
  download/connect retries disabled so one pip process cannot retry internally).

## 5. AUTHORITY SURFACE / NON-GOALS (hard)
`permissions.allow`/`deny` unchanged; existing PreToolUse + UserPromptSubmit
hooks unchanged; no CI publish-state helpers / no CI workflow change; no
global/system installs; no Cloudflare/Options coupling; no
developer-environment-manager redesign; no settings.json refactor.

## 6. COMPLETE IMPLEMENTATION SURFACE
PAYLOAD (exactly 3 files — no fourth is required; the probe is an INLINE
`python -I` block in the script, not a separate module):
- `scripts/dev_bootstrap.sh`
- `.claude/settings.json` (minimal SessionStart hook only)
- `tests/test_dev_bootstrap.py`
LIFECYCLE / AUTHORITY (downstream PRD bookkeeping, NOT packet payload): the
Stage-0 PRD doc, its review artifact, `docs/PRD_REGISTRY.md`,
`docs/prd_index.json`, `docs/PROJECT_STATE.md`, and **`docs/DECISIONS.md`** (the
canonical location for Dustin's design-direction + Gate-A rulings, CLAUDE.md
§ Canonical sources). This packet's review records are likewise lifecycle
evidence.

## 7. REVIEWED DESIGN CEILING (RANGE, per docs/PRD_PROCESS.md:666-682)
The exact-`90` point ceiling is withdrawn (it conflicts with the MATERIAL
estimation rule and the added locking/isolation/env-file/probe surface). Counting
validation / fail-loud / provenance / isolation / locking / proof-support logic
first-class (PRD-290), the design-estimate RANGE (non-authoritative, no spike
committed on this design-only branch) is:
- `scripts/dev_bootstrap.sh` (bash orchestration + inline `python -I` probe +
  locking + transactional binding + fail-loud): **~130-210 LOC**
- `.claude/settings.json` SessionStart addition: ~10-14 LOC
=> production RANGE **~140-224 LOC** across the two payload files. **Proposed
Gate-A ceiling: top-of-range + margin (order ~250 LOC), to be BOUND as an integer
only at Gate A** on the reviewed Stage-0 PRD. Test file uncapped, first-class.
STOP-AND-RENEW on: a 4th payload file / 2nd test file / any permission-array or
existing-hook change / production LOC above the Gate-A-bound ceiling. If the safe
contract cannot fit a ceiling Dustin will accept, the design-direction ruling may
narrow specific requirements (see §12) rather than widen during build.

## 8. FROZEN INVARIANTS (design-proposal evidence — NOT Gate-A-bound yet)
1. Physical root from script location, never accidental cwd.
2. `.venv` repo-local; validated by RUNTIME IDENTITY (`sys.prefix==<root>/.venv`,
   `sys.base_prefix!=sys.prefix`, system-site disabled, no outside site path);
   the `.venv` directory is not a symlink; Python >=3.11. (A base-interpreter
   symlink under `.venv/bin` is valid.)
3. Base order `python3`→`python`, invoked `-I`; base MAY create the venv, NEVER
   runs pip.
4. All pip via `.venv/bin/python -I -m pip --isolated --no-input` (retries/connect
   bounded); `PYTHONPATH`/`PYTHONHOME`/`PIP_*`/pip-config/cache neutralized.
5. Probe isolated (`-I`) AND structurally isolated (no `.pth`/`sitecustomize`
   escape), from cwd/`PYTHONPATH`/user-site/activated env.
6. Editable provenance: `direct_url.json` `file:` canonically decoded == current
   physical root, and `cuttingboard.__file__` under the checkout.
7. PEP-440 evaluation of EVERY current pyproject runtime + dev requirement (incl.
   PyYAML), source of truth = current `pyproject.toml`, not installed metadata.
8. Ruff metadata AND `.venv/bin/ruff --version` both == 0.15.22.
9. `.venv/bin/pytest --version` AND `.venv/bin/python -I -m pytest --version`
   both EXECUTE.
10. Ready => zero pip.
11. Not-ready => at most one install + identical post-probe (under the lock).
12. Wrong-version / incomplete-extra / absent-editable / moved-repo /
    wrong-checkout / stale-installed-metadata are NOT ready.
13. Broken/non-isolated/symlinked-dir `.venv` fails without deletion/recreation/
    external fallback.
14. Repo-scoped interprocess lock around validate/create/install, with an
    after-lock re-probe and bounded lock-wait failure.
15. Session binding: after readiness only, ONE transactional normalized
    `export`-block in the `CLAUDE_ENV_FILE` shell script; no append accumulation/
    duplicates; never on failure; stale-success cannot survive a later failure
    (or the narrowing is stated when the file is unwritable).
16. SessionStart set = `startup|resume|clear|fork`; `compact` excluded; exact
    cwd-safe delegation (`cd "${CLAUDE_PROJECT_DIR:-.}" && bash
    scripts/dev_bootstrap.sh`); explicit timeout.
17. Failure => stderr diagnostic + exit 2; success => one concise line + exit 0.
18. `permissions.allow`/`deny`, PreToolUse, UserPromptSubmit unchanged (proved by
    baseline-minus-SessionStart equality + textual-diff inspection against a
    durable pinned snapshot/hash, not `origin/main` in shallow CI).
19. No CI workflow/helper, Cloudflare, Options, global install, or unrelated
    file change.
20. Tests prove call counts + targets in temp fixtures (fake executables /
    logging, no network) + mutation-discriminating failures for readiness,
    confinement, locking, fail-loud, and success→failure env-file reuse.
21. Payload expansion or production LOC above the Gate-A-bound ceiling =>
    stop-and-renew.

## 9. FAILURE / STATE MATRIX
ready (zero pip; one binding + status line) · missing `.venv` (lock → create →
install once → post-probe) · incomplete deps / wrong ruff / absent editable /
stale-installed-metadata (NOT ready → install once → post-probe) · moved checkout
/ `.venv` reused from another checkout (provenance fails → install retargets,
if venv valid) · broken/symlinked-dir/non-isolated `.venv` (fail-loud, no
deletion) · **concurrent SessionStart / lock contention** (serialize; after-lock
re-probe; bounded-wait then fail-loud) · **read-only repo/`.venv`, disk
exhaustion, interrupted/timed-out create or install, partial venv** (fail-loud
exit 2; a partial venv is treated as not-ready under the lock and re-installed,
or fails if it cannot be made isolated) · **polluted `PYTHONPATH`/`PYTHONHOME`/
`PIP_TARGET`/pip-config** (neutralized; must not affect outcome) · **unwritable /
pre-populated `CLAUDE_ENV_FILE`** (rewrite owned block transactionally; if
unwritable, no-binding-on-failure narrowed + reported) · pip failure / post-probe
failure (exit 2, no success message, no binding).

## 10. TEST / FALSIFICATION PLAN
Isolated temp-repo fixtures; fake `python`/`pip`/`ruff`/`pytest` with call
logging; NO network. Prove: ready => no-op (zero pip); existing-ready not
reinstalled; missing prereqs fail (exit 2 + message); wrong-ruff-version reads
NOT ready; stale-installed-metadata (ruff>=0.4.0 vs pin) reads NOT ready;
broken/symlinked-dir `.venv` fails without deletion; **concurrent starts
serialize (lock) with a single install and an after-lock no-op**; hook delegates
(no embedded logic); `.claude/settings.json` valid JSON; **the whole settings
tree minus the new `hooks.SessionStart` member equals a durable pinned
snapshot/hash AND a textual diff shows no reformat/refactor of PreToolUse /
UserPromptSubmit / permissions**; no unrelated file mutation; `CLAUDE_ENV_FILE`
binding is a single transactional `export` block, deduped, absent on failure,
and **success-followed-by-failure reuse of the same file leaves no stale
binding**; bounded no-network failure across `startup|resume|clear|fork`;
`compact` excluded; script mode `100755`. Mutation-discriminating tests for
readiness, confinement, locking, and fail-loud.

## 11. OPEN QUESTIONS (genuine, unresolved)
1. **`fork` binding inheritance:** confirm whether a `fork` SessionStart inherits
   a valid parent env binding (allowing a cheap no-op) or must fully re-probe;
   default to re-probe under the lock.
2. **Lock primitive:** `flock(1)` availability across supported remote/mobile
   targets vs a portable `mkdir`-based lock; the packet requires serialization,
   the implementation picks the portable primitive at the spike.
3. **Timeout headroom:** the SessionStart `timeout` must exceed a cold isolated
   `pip install -e` on the slowest supported target; confirm at the spike.

## 12. RECOMMENDED DESIGN-DIRECTION RULING (for Dustin)
Approve the corrected boundary: a repo-local-`.venv`-owning, lock-serialized,
`-I`-isolated `scripts/dev_bootstrap.sh` with runtime-identity venv validation,
current-`pyproject` version-true readiness (incl. PyYAML + ruff 0.15.22
metadata/executable + editable provenance + structural isolation), a
transactional `CLAUDE_ENV_FILE` shell-export binding (success-only), an exit-2
fail-loud contract with `startup|resume|clear|fork` (compact excluded) and no
retry; exactly 3 payload files; production RANGE ~140-224 LOC with the Gate-A
ceiling bound at top-of-range + margin only at Gate A; zero permission/
existing-hook change; `docs/DECISIONS.md` added as a lifecycle/authority surface.
If that LOC/complexity is more than Dustin wants for a quick win, the ruling may
NARROW scope — e.g. drop the `CLAUDE_ENV_FILE` session-binding (leaving human
activation + a printed instruction) and/or reduce the readiness rigor — which
materially lowers the range. Then authorize a Stage-0 PRD carrying the (possibly
narrowed) invariants as Gate-A-binding, its fresh-context PRD review, and Gate A.
