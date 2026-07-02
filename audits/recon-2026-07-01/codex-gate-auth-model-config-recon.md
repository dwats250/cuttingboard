# RECON — Codex cross-review gate: auth method + model config + honor-gate logic

**Type:** READ-ONLY recon. Establishes config facts; resolves nothing, proposes no fix.
**Date:** 2026-07-01. **Branch:** `claude/prd-212-audit-recon-ywlso0`.
**Evidence:** in-tree files @ current branch tip; grep receipts below. Artifacts win over framing.

Given context (treated as premise, not verified here): `gpt-5-codex` deprecated 2026-04-01;
PRD-207's gate is working correctly; `ALLOWED_CODEX_MODELS` targets a dead model.

---

## 1. AUTH METHOD → **API key (`OPENAI_API_KEY` secret), NOT ChatGPT sign-in.**

`.github/workflows/codex-review.yml`:
- `:99` — `openai-api-key: ${{ secrets.OPENAI_API_KEY }}` — the review step's only credential,
  passed as the `openai-api-key` **input** of `openai/codex-action@e0fdf012…` (v1.8, SHA-pinned, `:98`).
- `:14-17` (header) — "OPENAI_API_KEY is consumed ONLY as the `openai-api-key` input of the
  official openai/codex-action, which proxies it. It is NEVER a job/step `env:` and is NEVER echoed."

**No ChatGPT-auth path exists anywhere in the repo:**
- No `codex login`, no session token, no `auth.json`, no `preferred_auth`, no `chatgpt` reference
  in any `.yml/.yaml/.toml/.sh/.py` (grep clean; the single `CODEX_HOME` hit is
  `tests/test_codex_review.py:176`, a *negative* assertion that the artifact must NOT leak a
  `CODEX_HOME`/rollout path — not an auth config).
- Root `/config.toml` is the Cuttingboard app config (`[flow]`, `[engine_doctor]`) — no codex,
  model, openai, or auth keys. There is no `.codex/` config or codex `config.toml` in the tree.

> **DIVERGENCE FLAG (artifacts vs. framing).** The context states the fail-close is "the
> documented **ChatGPT-auth** behavior for requesting a deprecated model." The gate does **not**
> use ChatGPT auth — it authenticates with an **API key** via `openai/codex-action`. The
> observed "Model metadata for `gpt-5-codex` not found. Defaulting to fallback metadata" is
> emitted under **API-key** auth. Whether the deprecation/fallback narrative holds identically
> under API-key auth is yours to reconcile; the auth receipt itself is unambiguous.

---

## 2. MODEL CONFIG — every place a Codex model string is named

### LIVE config (actually drives a run) — three locations, all name `gpt-5-codex`:
1. **Requested model (default):** `.github/workflows/codex-review.yml:55` —
   `default: gpt-5-codex` on the `model` workflow input. Wired to the action at
   `:101` `model: ${{ inputs.model }}`, and re-read by the resolve job env
   `MODEL: ${{ inputs.model }}`. **This is the string that triggers the fallback** (see §3).
2. **Allowlist:** `.github/workflows/codex-review.yml` env `ALLOWED_CODEX_MODELS: ${{ vars.ALLOWED_CODEX_MODELS }}`
   — sourced from the **repository variable** (not in-tree; Dustin-set). Observed live value in the
   2026-07-01 Phase-4 run env = `gpt-5-codex` (prior recon). Comment example `:69`
   `"gpt-5-codex gpt-5-codex-*"`.
3. **Test fixture allowlist:** `tests/test_codex_review.py:253` — `_ALLOW = "gpt-5-codex gpt-5-codex-*"`
   (drives the resolver unit tests only; not production config).

There is **no** `config.toml model=` and **no** standalone `--model` flag; the model is set solely
via the `model` input → `openai/codex-action`.

### Whole-repo grep of the requested strings (file:line):
- **`gpt-5-codex`** — LIVE config: `codex-review.yml:55,69`. Test: `test_codex_review.py:231,253,275,282,284,294,299,307,316,322,323,340,344`.
  Docs/history/audit (documentary only): `CLAUDE.md:150,177`; `docs/DECISIONS.md:75,84,85,88,91,92,98,99,179,182`;
  `docs/PROJECT_STATE.md:21` (+omitted long lines 15-24); `docs/prd_history/PRD-212.md:19,20,32,33,37,45,48,57,60,66,74,76,83,84,100`;
  `PRD-207.md:51,52,61,63,70,178,212,213`; `PRD-198.md:29,30,79,106`; `PRD-197.md:102,104`; `PRD-197.review.claude.md:10,11`;
  `PRD-129.review.codex.md:5`; `PRD-195/199/210.review.codex.md:5` (provenance lines); `audits/recon-2026-06-22/SESSION_RESUME.md:43`;
  `audits/recon-2026-07-01/prd-212-review-standin-recon.md` (this session's prior artifact).
- **`gpt-5.5`** — SERVED-model prose self-reports in past artifacts (documentary): `PRD-135.review.codex.md:3`;
  `PRD-200.review.codex.md:37,50,84`; `PRD-192.review.codex.md:4,40`; `PRD-190.review.codex.md:5,62,68`;
  `PRD-191.review.codex.md:4,50`; `PRD-130.review.codex(.v2/.v3).md:5,806,1074`; `PRD-193.md:149`; `PRD-193.review.codex.md:8`;
  `PRD-195.review.codex.md:10`; `PRD-210.review.codex.md:10`. (These are what the fallback actually served, historically.)
- **`gpt-5.4`** — `PRD-199.review.codex.md:10` (served self-report); `audits/recon-2026-06-17/SESSION_RESUME.md:49` (a recommendation).
- **`gpt-5.3-codex`** — `audits/recon-2026-06-17/SESSION_RESUME.md:49` only (a recommendation, not config).
- **`gpt-5.1-codex`** — **no hits.**
- **`gpt-5.2-codex`** — **no hits.**
- **`codex-mini`** — **no hits.**

> Note: no in-tree config names any *successor* model. The only successor names present are a
> 2026-06-17 SESSION_RESUME recommendation (`gpt-5.4` / `gpt-5.3-codex`) and the historical
> served self-reports (`gpt-5.5`, `gpt-5.4`) inside past review artifacts.

---

## 3. HONOR-GATE LOGIC — how "served == requested" is decided

The resolver is embedded in `.github/workflows/codex-review.yml` (`# === RESOLVER BEGIN … END ===`,
resolve job) and unit-tested via extraction (`tests/test_codex_review.py:217-222`). Its `classify()`:

1. Parse `--json` JSONL events; **no recognized codex events → exit 2** (fail-closed).
2. **No `turn.completed` event → exit 3.**
3. For any `item.completed` with `item.type == "error"`:
   - message matches `FALLBACK_RE` (`/model metadata for .* not found/i`) → **exit 4**;
   - any other error → **exit 5**. (ANY structured `item.error` fails closed, reword-proof.)
4. `resolved = requested` — **the gate does NOT read a served-model id.** PRD-207 established the
   toolchain surfaces no structured served-model field, so honor is inferred **negatively**: a
   clean stream (no fallback error + a completed turn) is *treated* as "requested was honored,"
   and `resolved` is set to the **requested** string.
5. Allowlist check: `any(fnmatch.fnmatch(resolved, p) for p in allowlist.split())` — `resolved`
   must match ≥1 **space-separated glob pattern** from `ALLOWED_CODEX_MODELS`; else **exit 6**.
6. Otherwise **exit 0**, print `resolved`.

**So the comparison is:** NOT a two-name "served vs requested" string equality (no served name
exists to compare). It is (a) a **negative fallback check** at the requested-model layer, then
(b) an allowlist match against a **set of glob patterns** (not a single fixed name).

**Mechanical consequence (reported, not a fix):** because the deprecated `gpt-5-codex` (the
`model` input, `:55`) emits the fallback `item.error` on every run, the gate **exits 4 at step 3
— before the allowlist (step 5) is ever consulted.** Editing `ALLOWED_CODEX_MODELS` alone cannot
change the outcome while the requested `model` remains the deprecated string; the string that
must change to clear the fallback is the **`model` input at `:55`** (whichever successor OpenAI
serves), and the allowlist is a downstream glob-set that must then admit whatever `resolved`
(= requested) becomes. Whether that is one edit or two, and to what value, is your call — this
recon only reports the current mechanic.

---

*No source, contract, workflow, `main`, DECISIONS, registry, or PRD file was mutated. No gate run
was dispatched.*
