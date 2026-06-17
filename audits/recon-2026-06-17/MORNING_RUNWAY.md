# Morning Runway — PRD backlog (overnight charge, 2026-06-17)

Single index for the morning: approve the pre-surfaced decisions, then execute. Everything here is
grounded in the repo as of branch `claude/overnight-recon-scoping-dxia5x` (base `33ac1f7`). No substantive
implementation was done; no auto-merge was performed; `main` is untouched.

---

## 0. Read these first — three headline flags

1. **⚠️ PRD-190 drift (corrective action needed).** PROJECT_STATE:14 claims the OHLCV window bump +
   shape-aware cache "landed with unit tests (commit `7a53fc4`)". **Verified false:** commit `7a53fc4`
   does not exist, `OHLCV_FETCH_MONTHS` is still `6` (config.py:97), and no shape-aware cache logic exists.
   Only the PRD *document* changed (`47d5f94`, docs-only). PRD-190 has **zero implementation**. → decision
   SEAM 190-A. (Not corrected tonight — PROJECT_STATE is machine-parsed governance bookkeeping, off the
   auto-merge whitelist.)
2. **⚠️ Codex is unavailable in this environment** (no PATH binary, no npm egress). Every HIGH-RISK /
   publish-touching PRD requires a Codex cross-review that **could not run tonight**. Each affected PRD's
   review is a fresh-context Claude review (satisfies the HIGH-RISK *Claude*-review independence
   requirement) with the **Codex cross-review flagged OUTSTANDING**. Do not merge any HIGH-RISK PRD until
   Codex (or an approved second model) reviews it.
3. **Charge backlog list was stale — corrected here.** PRD-187 is **COMPLETE** (not "scope first");
   PRD-190/191 are already IN PROGRESS; PRD-188's gate is the eval corpus + threshold T + go, not 187.

Also: **no yfinance egress** → PRD-190's R4 live diff cannot run here (recon-only, as the charge expected);
**no npm egress** → gitnexus could not run, so all blast-radius recon was manual import/call-site tracing.

## 1. Backlog state (corrected against the registry)

| PRD | Status | Lane | Class | Tonight | Ready to build? |
|-----|--------|------|-------|---------|-----------------|
| 187 | COMPLETE | STANDARD | SIDECAR | — | done (producer live, dispatch-only) |
| 179 | PROPOSED | STANDARD | INFRA | full scope+review | **YES — lowest risk, no deps, no Codex** |
| 191 | IN PROGRESS | HIGH-RISK | CONSUMER | full scope+review | yes, but **Codex outstanding** |
| 190 | IN PROGRESS | STANDARD(prov) | SIDECAR | recon-only | no — drift + needs network for R4 |
| 193 | PROPOSED | STANDARD(prov) | EXEC/INFRA | full scope+review | after 190; Option B keeps it STANDARD |
| 192 | PROPOSED | HIGH-RISK | EXEC/INFRA | full scope+review | no — needs routing decision + Codex |
| 195 | not opened | HIGH-RISK | INFRA | new scope+review | no — publish machinery + Codex |
| 188 | PROPOSED (GATED) | HIGH-RISK | CONSUMER | scope+review | no — eval gate (corpus+T+go) |

## 2. Dependency / risk map

**Dependency edges (what waits on what):**
- `193 → 190` — PRD-193's cache-version token should track PRD-190's window/shape contract (SEAM 193-C).
- `195 → 194` — PRD-195 amends PRD-194's ownership/lifecycle note (194 is COMPLETE; just an amendment;
  NOT a governance carve-out — it edits a PRD reference doc, not CLAUDE.md).
- `188 → eval gate → 187` — 187 done; 188 waits on labeled corpus + threshold T + eval pass + Dustin go.
- `192` — no PRD dependency, but blocked on the SEAM 192-A routing decision (human/architectural).
- `191`, `179` — no dependencies.

**Risk tiers (change risk, distinct from lane ceremony):**
- **LOW:** 179 (additive harness/fixtures; no render-logic change; no Codex).
- **MEDIUM:** 191 (tight, well-understood renderer edit; lane is HIGH-RISK so Codex still required).
  190 (medium change + the drift + network-gated R4).
- **HIGH:** 192 (protected `runtime/`, execution path), 193-if-OptionA (publish scripts), 195 (publish
  machinery delete path), 188 (gated; eval discipline).

**Systemic blocker:** Codex unavailability gates the merge of 191, 192, 195, 188 (and 193 if Option A).

## 3. Recommended implementation sequence (dependency-ordered, risk-ascending)

1. **PRD-179** — lowest risk, no deps, no Codex. Warm-up; land first. ∥ parallelizable with 191.
2. **PRD-191** — ready and tight; implement, but **hold merge for Codex**. Decision needed: SEAM 191-A copy.
   ∥ parallelizable with 179 (179 is additive harness; 191 edits the macro-evidence lookup — low conflict).
3. **PRD-190** — first resolve the drift (SEAM 190-A: correct PROJECT_STATE, then implement the bump +
   shape-aware cache), then run the R4 diff **in a network-enabled environment**; lane outcome is
   data-driven (null diff → STANDARD; any flip → HIGH-RISK + Codex).
4. **PRD-193** — after 190's cache contract; take Option B (actions/cache) to stay STANDARD and keep all
   PRD-194 invariants intact; suppress prefetch render (delete the PUBLISH_READY=true line).
5. **PRD-192** — needs the SEAM 192-A routing decision up front + Codex; protected runtime.
6. **PRD-195** — publish-machinery delete path; needs Codex + the PRD-194 ownership amendment.
7. **PRD-188** — only when the eval gate clears (corpus labeled + T set + eval ≤ T + Dustin go).

Parallelizable: {179, 191} now; 190 independent; 192 independent of the renderer work. 193 and 195 both
touch publish — do not run them concurrently with each other or with a live publish window.

## 4. Per-PRD index (runway + review + verdict + the one decision that unblocks it)

| PRD | Runway doc | Review | Verdict | The decision that unblocks the build |
|-----|------------|--------|---------|--------------------------------------|
| 191 | PRD-191.runway.md | PRD-191.review.claude.md | APPROVE-WITH-EDITS | SEAM 191-A: approve the direction-keyed copy table |
| 192 | PRD-192.runway.md | PRD-192.review.claude.md | APPROVE-WITH-EDITS | SEAM 192-A: fold into hourly_alert.yml (recommended) vs resurrect in cuttingboard.yml |
| 193 | PRD-193.runway.md | PRD-193.review.claude.md | APPROVE-WITH-EDITS | SEAM 193-A: actions/cache (recommended) vs commit data/cache |
| 188 | PRD-188.runway.md | (existing PRD draft) | GATED | SEAM 188-A/B/C: label corpus, set T, eval+go |
| 195 | PRD-195.runway.md | PRD-195.review.claude.md | APPROVE-WITH-EDITS | SEAM 195-A: retention N (recommended N=20) |
| 179 | PRD-179.runway.md | (low-risk; review at open) | scoped | SEAM 179-A: reuse test builders (recommended) |
| 190 | PRD-190.runway.md | (recon-only) | DRIFT | SEAM 190-A: correct PROJECT_STATE, then implement |

## 5. Consolidated decision seams (the morning approve-list)

Each has a recommended default; approving the defaults unblocks the recommended sequence.
- **190-A (drift, top priority):** correct PROJECT_STATE to "PRD doc re-centered; implementation NOT
  landed; window still 6", then implement. *Default: correct + implement.*
- **191-A (content):** adopt the direction-keyed copy table (PRD-191.runway §5). *Default: adopt as-is.*
- **192-A (architectural):** intraday slot home → fold into `hourly_alert.yml`. *Default: fold (Option 1).*
- **193-A (architectural, publish-adjacent):** cache persistence → `actions/cache`. *Default: Option B.*
- **193-B:** prefetch publish-safety → suppress render (delete the PUBLISH_READY=true line). *Default: suppress.*
- **195-A:** prune retention → count-based N=20 (≥ HISTORY_LIMIT). *Default: N=20.*
- **188-A/B/C (gated, Dustin-owned):** label the eval corpus; set threshold T (default posture: strict,
  T≤0.05); run eval + explicit go. *No defaults for A/C — ground truth + go are human-only.*
- **179-A:** reuse existing test builders for fixtures. *Default: reuse/extend.*

Escalated (touch non-goals or publish machinery — decide explicitly, do not auto-default): 192-A, 193-A,
195 (and its PRD-194 amendment), 188 gate.

## 6. Git status, auto-merge decision, and what landed

- **Branch:** all artifacts are on `claude/overnight-recon-scoping-dxia5x` (the designated dev branch).
  The per-PRD *implementation* branches happen in the morning when each PRD is actually built; tonight's
  output is one cohesive analysis deliverable, so it lives on one branch.
- **Auto-merge: NONE performed.** The auto-merge whitelist (pure-prose docs) was available, but the
  scoping output IS the substantive prep the human must review, and the charge says hold substantive prep.
  Per "unsure → it does NOT qualify → hold it", nothing was auto-merged. No incidental pure-prose fixes
  were made (notably, the PRD-190 PROJECT_STATE drift was deliberately NOT auto-corrected — it is
  machine-parsed governance bookkeeping and decision SEAM 190-A).
- **`main` is untouched.** No force-push. No registry/index/PROJECT_STATE edits.
- **Held PR:** the branch is pushed and a single PR is opened and HELD (no `gh pr merge --auto`) for the
  morning read. This PR contains only `audits/recon-2026-06-17/` analysis docs — no code, config, workflow,
  or bookkeeping change, so CI `test` is unaffected.

## 7. Verification

- Environment probed: Codex absent; npm egress absent (gitnexus unrunnable); yfinance egress absent
  (PRD-190 R4 confirmed un-runnable here). All recorded above.
- Every sub-agent recon sweep that fed a FILES boundary or a "nothing else reads this" claim was
  re-verified by the main agent on the decisive command (e.g., the PRD-190 drift: `git cat-file`,
  `grep OHLCV_FETCH_MONTHS`, `git show --stat 47d5f94`).
- No tests were run because no behavior changed (docs-only). The held PR's CI `test` reflects the base.
- Deliverables on disk under `audits/recon-2026-06-17/`: seven `PRD-NNN.runway.md` (191/192/193/188/195/
  179/190), four `PRD-NNN.review.claude.md` (191/192/193/195), and this index.

## 8. Index of files

- `MORNING_RUNWAY.md` (this doc)
- `PRD-191.runway.md` + `PRD-191.review.claude.md`
- `PRD-192.runway.md` + `PRD-192.review.claude.md`
- `PRD-193.runway.md` + `PRD-193.review.claude.md`
- `PRD-195.runway.md` + `PRD-195.review.claude.md`
- `PRD-188.runway.md` (gated; reviewed against the existing PRD draft)
- `PRD-179.runway.md` (low-risk; full review at open)
- `PRD-190.runway.md` (recon-only; drift recorded)
