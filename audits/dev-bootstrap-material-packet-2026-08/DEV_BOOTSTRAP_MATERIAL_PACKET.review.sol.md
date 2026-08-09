# Dev-bootstrap MATERIAL packet — GOV-2 packet review + exact-corrected-head confirmation (Sol)

Independent GOV-2 upstream MATERIAL-packet review and exact-corrected-head
confirmation for QW-5 (idempotent dev bootstrap), branch
`dev-bootstrap-material-packet`.

Reviewer: GPT-5.6 **Sol** (`gpt-5.6-sol`), `codex exec -s read-only -m
gpt-5.6-sol -c model_reasoning_effort=xhigh` (sandboxed read-only; prompt via
stdin; verdict from stdout). Capability role: fresh-context independent
second-model reviewer, standing default for MATERIAL packet reviews (owner
model-utilization ruling 2026-08-08). Not the packet author. Artifact written by
Claude Code from captured stdout; Sol wrote nothing into the repo (self-reported
read-only, based on `a87d203f`, added only the packet).

## 1. INITIAL PACKET REVIEW — reviewed head `88fe58d346062075f0a1649363675b59a2282e42`
**VERDICT: ACCEPT-WITH-REQUIRED-CORRECTIONS.** Fresh-context: reviewed the packet
+ repository surfaces before any PRD existed; consulted no prior review prose.

Findings (1-9) and the 10 REQUIRED CORRECTIONS, all applied in the single GOV-1
consolidated cycle at the corrected head:
1. **Env/state matrix incomplete** → §9/§10 expanded (concurrent starts, lock
   contention, read-only/disk/interrupted, `PYTHONPATH`/`PYTHONHOME`/`PIP_TARGET`
   pollution, reused env-file, partial venv).
2. **Confinement not airtight** → `-I` on base/create/probe/pip + pip
   `--isolated`; env/pip-config/cache neutralized; existing-`.venv` validated by
   RUNTIME IDENTITY (`sys.prefix`/`base_prefix`/system-site), distinguishing a
   valid base-interpreter symlink from a symlinked `.venv` dir (invariants 2,4,5).
3. **READY underspecified** → source of truth = current `pyproject.toml`; PEP-440
   for all reqs; canonical `file:` decode + physical compare; `__file__` under
   checkout; ruff metadata+executable == 0.15.22; pytest executes; structural
   isolation proved separately (invariants 6-9,12). Recorded the live
   stale-metadata example (installed `ruff>=0.4.0` vs pin).
4. **SessionStart incomplete** → added `fork` to the source set; corrected exit-2
   terminology (client displays stderr + continues); pip-internal retries
   disabled (invariants 16,17,4).
5. **Permission/non-change proof** → invariant 18 now proves the whole settings
   tree minus the new `SessionStart` member equals a durable pinned snapshot/hash
   + textual-diff of PreToolUse/UserPromptSubmit/permissions (not `origin/main` in
   shallow CI).
6. **Lifecycle inventory** → `docs/DECISIONS.md` added to lifecycle/authority
   surfaces (§6); 3-file implementation payload retained.
7. **90-LOC point ceiling** → withdrawn; replaced with a RANGE per
   `docs/PRD_PROCESS.md:666-682` (§7: ~140-224 production; Gate-A ceiling bound at
   top+margin only at Gate A).
8. **Failure loops** → §9 states the cross-event recurrence truthfully; pip
   retry/connect bounded; concurrent runs serialized; recovery instruction
   defined.
9. **`CLAUDE_ENV_FILE` semantics** → corrected to the installed shell-script
   contract: one transactional safely-quoted `export` block, deduped, never on
   failure, success→failure reuse tested (invariant 15).

## 2. EXACT-CORRECTED-HEAD CONFIRMATION — corrected head (this commit)
PENDING — the independent Sol exact-corrected-head confirmation runs against the
corrected head that carries this record; its verdict + the confirmed SHA are
appended in the immediately following commit before the packet returns
review-clean.

## Disposition
GOV-2 upstream packet cycle: independent Sol packet review + one consolidated
correction + independent exact-corrected-head confirmation. Per GOV-2 the packet
then returns for Dustin's design-direction ruling. This artifact authorizes
nothing downstream: no PRD allocated, no Gate A, PR #238 untouched, no
implementation.
