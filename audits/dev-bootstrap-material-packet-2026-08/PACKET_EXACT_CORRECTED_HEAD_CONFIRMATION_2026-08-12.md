# PRD-301 MATERIAL packet — GOV-2 exact-corrected-head confirmation

- Confirmation subject: corrected packet head **5b94a18** (branch
  worktree-prd-301-bootstrap-lock), the one-consolidated-correction-cycle
  revision of `DEV_BOOTSTRAP_LOCK_AMENDMENT_MATERIAL_PACKET_2026-08-12.md`.
- Instrument: Codex `gpt-5.6-terra`, `-s read-only`, reasoning xhigh, fresh
  context. This is a GOV-2 confirmation (each prior finding addressed?), not a
  fresh-scope review; the only lawful non-ACCEPT outcome is a new material
  boundary omission returning the packet to DESIGN INCOMPLETE.
- Prior review: independent packet review (REQUIRED-CHANGES, 5 findings + 1
  recommended), addressed in the packet's `## CORRECTION CYCLE` section.

## Verdict (Codex, verbatim)

CONFIRMATION: DESIGN INCOMPLETE (new material boundary omission)

PER-FINDING:
1. ADDRESSED — PID-identity cleanup of `RECLAIM_LOCK` prevents TERM-A from
   unlinking B's lock after handoff and removes the acquired-before-flag window.
2. NOT-ADDRESSED — `[ "$(ls -A "$LOCKFILE")" = pid ]` is a snapshot before `mv`:
   an old-version process already past `[ -d ]` can create its false-acquisition
   child after that check, so the moved grave's `rmdir ... || true` again
   silently leaves a persistent non-empty `.stale.PID` directory.
3. ADDRESSED — The exact 07dce51 baseline measures 249 production lines; the
   embedded hunk is +11/-8 counted lines, yielding 252, within 260.
4. ADDRESSED — POSIX `link()`-function vs platform `link(1)` distinction stated;
   macOS runner assertions made a REQUIRED pre-Gate-A validation.
5. ADDRESSED — controlled real-process orders for three-process serialization,
   both signal windows, directory-after-check acquisition, and the seeded
   legacy-dir case, with independent mutant kills.
REC1. ADDRESSED — §1 now requires two reclaimers plus a distinct fresh acquirer.

NEW MATERIAL BOUNDARY OMISSION: The corrected legacy-directory reclamation has
an unprotected check-to-`mv` lifecycle boundary: a false-acquisition child can
arrive after the clean-directory check, be moved into `.stale.PID`, and survive
the ignored `rmdir` failure.

## HELM realizability note (attributed to HELM, not the confirmer)

The residual is a real code-level TOCTOU, but its realizability depends on which
old version can drop a NON-`pid` child into the legacy directory. Verified
read-only against the actual deployed surfaces:

- `origin/main`'s PRD-293 lock (the only pre-amendment lock ever deployed) is
  `mkdir "$LOCKDIR"` then `printf '%s\n' "$$" >"$LOCKDIR/pid"`. The ONLY child it
  ever creates is `pid` (verified: `git show origin/main:scripts/dev_bootstrap.sh`,
  lines 65-74). It never runs `ln tmp dir` and never creates a `.new.*` or any
  other-named child.
- The stray NON-`pid` child the finding requires is produced ONLY by the
  07dce51 `ln`-into-directory false-acquisition (the #2 defect the amendment
  replaces with `link`). 07dce51 is RED-held and NOT on main (verified:
  `git branch -a --contains 07dce51` shows no main).
- Two amended (Version-C) processes never link into a directory (`link` fails
  EEXIST on a dir, creating no child) and route a directory to
  `_reclaim_legacy_dir` instead. So neither the deployed old version nor the new
  version can produce the non-`pid` stray child in the real upgrade path.

Conclusion: the persistent non-empty `.stale.PID` grave is unrealizable under
the actual deployed old version (PRD-293 -> amended); it becomes realizable only
if the never-deployed 07dce51 (`ln`-into-dir) code ran concurrently, which the
RED-hold prevents.

A cheap owner-doctrine-compliant hardening exists if defense-in-depth is wanted:
replace `_reclaim_legacy_dir`'s trailing `rmdir "$grave" 2>/dev/null || true`
with a fail-loud on `rmdir` failure (a non-empty grave after removing `pid` is
unexpected content we refuse to silently orphan). This checks the ACTUAL
post-`mv` state (not a pre-`mv` snapshot), uses `rmdir`+fail-loud exactly as the
owner's pid-less-legacy recovery doctrine prescribes, adds ~1-2 net lines (well
within 260), and uses no `rm -rf`.

## Disposition

GOV-2 places a DESIGN INCOMPLETE confirmation with the owner. The one
consolidated correction cycle GOV-1/GOV-2 authorize is spent; HELM does not run
a second cycle autonomously. Head 07dce51 stays RED-held; production
implementation remains prohibited. Returned for the owner design-direction
ruling with two lawful paths:

- **Path A — dismiss Finding 2 as unrealizable-under-deployed-versions** and
  ratify the packet at 5b94a18 (or 5b94a18 + a one-line realizability note),
  proceeding to the design-direction ruling. Basis: the verified realizability
  note above (Author-discipline-3 realizability judgment; an owner call, not
  HELM's, because it turns on accepting the RED-hold as the boundary that makes
  Version-B non-concurrent).
- **Path B — authorize one further bounded correction** applying the fail-loud-
  on-`rmdir` hardening, then a re-confirmation of the new corrected head. This
  closes the residual regardless of realizability but is a second correction
  cycle only the owner may authorize.
