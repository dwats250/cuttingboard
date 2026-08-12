# DEV_BOOTSTRAP LOCK AMENDMENT — MATERIAL PACKET (2026-08-12)

Amends the PRD-293 dev-bootstrap MATERIAL packet lineage
(`DEV_BOOTSTRAP_MATERIAL_PACKET_2026-08-09.md`, PRD-293.md:20). Upstream authority for the
corrective realization PRD-301 Amendment 1, classified MATERIAL by the owner 2026-08-12
(owner event #3) because it changes the binding production LOC ceiling (250 -> 260 provisional),
a GOV-2 §1 trigger. Prepared for independent packet review; NO production implementation exists
for the amended mechanism (RED-held at 07dce51). The pre-amendment implementation at 07dce51
already closes the original mkdir->pid publication race deterministically and preserves every
safety invariant; this packet governs only the correction of the two safety residuals (Sol #1,
#2) and the caught-signal cleanup (#5) the owner ruled must be fixed.

## 0. Intake classification (GOV-2 §1)
MATERIAL. Trigger: changes a production LOC ceiling (250 -> 260). Not triggered: no new
external consumer/renderer/schema; no new dependency (the `link` utility is coreutils/BSD, as
available as `ln`); crosses no additional domain (bootstrap infra only); enumeration of callers
is unchanged (sole runtime caller = the SessionStart hook, `.claude/settings.json`). Lane after
MICRO-ineligibility: STANDARD (no HIGH-RISK payload file). FILES limited to
`scripts/dev_bootstrap.sh` + `tests/test_dev_bootstrap.py` plus lifecycle/review artifacts.

## 1. The two-reclaimer failure interleaving (Sol #1 — pre-amendment defect at 07dce51)
Reclaim at 07dce51 is `_reclaim_lock`: `link/ln`-capture the lock inode into a pid-tagged grave,
judge liveness on the captured inode, then `[ "$LOCKFILE" -ef "$grave" ] && rm -f "$LOCKFILE"`.
The `-ef` test and the `rm` are two syscalls (stat, then unlink) — non-atomic. Interleaving:
- t0: dead canonical lock D present. Reclaimers A and B each capture D's inode into their own
  graves; both judge D dead; both pass `[ -ef ]` while D is still at `$LOCKFILE`.
- t1: A executes `rm -f "$LOCKFILE"` (unlinks D). `$LOCKFILE` name is now free.
- t2: a fresh contender C acquires: its `link` creates `$LOCKFILE` = inode Y (C live).
- t3: B — already past its `[ -ef ]` at t0 — executes `rm -f "$LOCKFILE"`, unlinking Y (C's
  live lock).
Because 07dce51 does NOT recheck ownership before venv creation / pip install, C can be inside
protected work when its lock is unlinked, and a later acquirer can enter protected work
concurrently -> mutual-exclusion / venv-integrity violation (owner ruling: a safety defect, not
a harmless exit-2). Requires a pre-existing dead lock (crash/SIGKILL-while-holding) plus >=2
concurrent contenders with the fresh acquire landing in B's stat->unlink gap.

## 2. The old/new-version directory-target failure interleaving (Sol #2 — pre-amendment defect)
07dce51 detects a legacy directory with `[ -d "$LOCKFILE" ]` before acquiring with the `ln`
utility. `ln src dir` (no `-T`, banned as GNU-only) LINKS INSIDE the directory and returns exit
0. Interleaving during an old/new-version transition:
- A (new version) evaluates `[ -d "$LOCKFILE" ]` = false.
- B (old version, mkdir-based lock) executes `mkdir "$LOCKFILE"` and is paused before writing
  its pid.
- A executes acquisition; `ln "$tmp" "$LOCKFILE"` succeeds by creating
  `$LOCKFILE/$(basename "$tmp")` INSIDE B's directory and returns 0; A breaks and treats itself
  as owner though it never acquired the canonical lock, and later performs protected work.
Requires concurrent old+new-version execution against the same REPO_ROOT (a one-time upgrade
transient; impossible post-merge, REPO_ROOT is script-relative). Owner ruling: a safety defect.

## 3. Why exact-pathname `link` acquisition closes #2
The amendment replaces the `ln` builtin/utility acquisition with the POSIX **`link` UTILITY**
(`link "$src" "$dst"`), which calls `link(2)` on the exact destination pathname. `link(2)`
fails EEXIST when the destination exists — whether a file OR a directory — and NEVER creates an
entry inside a directory. So even if a directory appears between `[ -d ]` and acquisition, `link`
FAILS; A does not falsely acquire and drops no child link; the loop re-routes to legacy handling
next iteration. The `[ -d ]` branch is retained for ROUTING to legacy migration (a `link`
failure is EEXIST for both file and dir; `link dir grave` also fails), not for acquisition
safety. Empirical evidence in §9.

## 4. RECLAIM_LOCK state machine (amended mechanism)
`RECLAIM_LOCK="$LOCKFILE.reclaim"`, a FIXED-NAME mutex acquired with the same atomic `link`
primitive; `_have_reclaim_lock` is a per-process held-flag.
- ACQUIRE-RECLAIM: `link "$_lock_tmp" "$RECLAIM_LOCK"` — atomic; only one reclaimer wins; on
  EEXIST (another reclaimer holds it, or a SIGKILLed reclaimer left it) `_reclaim_lock` returns
  1 and the outer bounded loop waits.
- CRITICAL SECTION (single-threaded): read `$LOCKFILE`'s pid; if live -> keep; else (dead /
  malformed / absent) -> `rm -f "$LOCKFILE"`. Safe: no other reclaimer runs concurrently (they
  are blocked on RECLAIM_LOCK), and no new owner can acquire `$LOCKFILE` while the dead lock is
  present, so the check->rm gap cannot race a fresh owner.
- NORMAL RELEASE: `rm -f "$RECLAIM_LOCK"; _have_reclaim_lock=0`.
- CAUGHT-SIGNAL CLEANUP: `trap 'exit 2' HUP INT TERM` -> EXIT -> `_on_exit` removes
  `$RECLAIM_LOCK` iff `_have_reclaim_lock=1` (ownership-guarded, so it never unlinks another
  process's live reclaim lock), alongside the acquisition temp.
- SIGKILL RESIDUE: an orphaned RECLAIM_LOCK cannot be caught-cleaned; it is NEVER auto-stolen
  (see §5). It makes subsequent `link` acquisitions fail, so the outer loop waits.
- TIMEOUT (bounded wait exhausted with RECLAIM_LOCK still present): FAIL LOUD with a specific
  instruction to remove the stale reclaim lock manually with `rm -f "$RECLAIM_LOCK"` after
  confirming no bootstrap is running — the identical bounded-wait-then-fail-loud pattern
  ratified for the pid-less legacy directory.
- MANUAL RECOVERY: operator `rm -f "$RECLAIM_LOCK"`; the next run proceeds.

## 5. Proof that manual recovery is NOT automatic stale-lock stealing
Automatic stealing of a fixed-name mutex is inherently a compare-then-unlink TOCTOU: "read the
stored pid, `kill -0`, and unlink if dead" is stat-then-unlink; two contenders can both observe
a stale RECLAIM_LOCK, both unlink it, and one land its `link` on the other's fresh relink,
producing two concurrent reclaimers — reintroducing #1 (the amended-PRD review caught exactly
this in the first-draft self-heal). The amendment performs NO such read-then-unlink on
RECLAIM_LOCK: a present RECLAIM_LOCK only ever causes `link` to fail (a pure atomic test) and
the run to WAIT, then FAIL LOUD. Removal of a stale RECLAIM_LOCK happens only by an out-of-band
human `rm` after the fail-loud instruction, never by a concurrent bootstrap process. Therefore
no interleaving of bootstrap processes can both "decide stale" and race to remove/reacquire it;
the recovery is single-actor (the operator) and cannot be represented as automatic stealing.

## 6. Complete artifact lifecycle
- Canonical lock `$LOCKFILE` (regular file, owner pid): created atomically by `link` (pid
  present the instant it exists); removed by the owner (`_unlock`, ownership-guarded) or
  reclaimed when dead under RECLAIM_LOCK. Untracked (already not gitignored; only `.venv/` is).
- Acquisition temp `$LOCKFILE.new.PID.XXXXXX` (mktemp sibling, holds owner pid): removed on
  every `_lock` return + EXIT trap; a dead-owner leftover is removed by the next run's
  `_sweep_stale` (pid parsed from the literal `$LOCKFILE.new.` prefix — Sol #4 fix).
- Legacy reclaim grave `$LOCKFILE.stale.PID` (dir renamed aside during legacy dead/malformed
  reclaim): removed in-function; a dead-owner leftover swept next run (literal `.stale.` prefix).
- Legacy directory `$LOCKFILE` (pre-upgrade carrier): live pid -> never reclaimed; dead/malformed
  -> reclaimed via atomic `mv`; pid-less -> never auto-reclaimed, bounded-wait-then-`rmdir`
  fail-loud (ratified).
- RECLAIM_LOCK `$LOCKFILE.reclaim` (fixed-name): §4 state machine; NOT pid-tagged so the sweep
  glob does not match it; recovered by caught-signal cleanup or bounded-wait-then-fail-loud
  manual `rm`. No permanent unowned artifact survives a later bootstrap for the pid-tagged
  classes; RECLAIM_LOCK's only non-swept residue path is the SIGKILL-then-manual-`rm` case,
  which is loud, bounded, and single-actor.

## 7. First-class LOC budget
Durable model of the review-corrected amended mechanism: **253 net-production** lines
(non-blank, non-comment, by the `test_script_stays_within_frozen_production_ceiling` metric;
`bash -n` clean). Auditable derivation from the current 07dce51 script (249):
- `RECLAIM_LOCK` constant: +1.
- `_have_reclaim_lock` init: +0 (replaces the retired grave-tracking var of the first draft).
- acquisition `ln` -> `link`: +0 (token swap).
- `_reclaim_lock` rewritten (drop `-ef`-capture; serialize via RECLAIM_LOCK; no self-heal): the
  new 6-line body vs the old 7-line body: -1.
- EXIT-trap ownership-guarded RECLAIM_LOCK cleanup: +0 (replaces the grave-cleanup line).
- timeout stale-RECLAIM_LOCK fail-loud branch: +1.
Net +2 vs 249 -> ~251; the model measures 253 (the honest count of the drafted implementation,
which the derivation approximates; the draft, not the derivation, is authoritative). The
`link`-utility swap and serialized reclaim are the substance; nothing is packed.

## 8. Proposed ceiling and margin
Provisional Gate-A ceiling: **260 net-production**, = 253 model + 7-line margin for
implementation-phase correctness tweaks (e.g., a test-visible seam) — NOT for packing or
readability loss. 250 remains the currently binding pre-amendment ceiling. If the durable model
or packet review shows 260 insufficient, HELM returns with an honest revised estimate before
design-direction ratification (owner directive §3).

## 9. Cross-platform `link` evidence
- Linux: EMPIRICALLY VERIFIED this session. `/usr/bin/link` (GNU coreutils). `link src dir`
  fails `EEXIST` ("cannot create link 'dir' to 'src': File exists") and creates nothing inside
  the directory; `ln src dir` DID link inside (reproducing #2). `link src newpath` succeeds;
  `link src existingpath` fails EEXIST. `link dir grave` fails EPERM.
- macOS/BSD: `link(1)` is a documented BSD utility present on macOS (`/bin/link` / coreutils via
  the base system), a thin wrapper over `link(2)` with the same exact-pathname EEXIST semantics
  and no directory-destination reinterpretation. NOT independently run on macOS in this
  environment. RECOMMENDED owner/CI check: run the same three assertions on a macOS runner
  before amended Gate A, or accept the documented-behavior basis. No GNU-only flag is used.

## 10. Deterministic tests + independent mutation kills (required at implementation, post amended Gate A)
Guards and their killing tests (each mutation independently reddens a NAMED test; verbatim
production script under real processes):
- reclaim serialization: two real reclaimers with a barrier immediately before the canonical
  removal; assert the eventual live owner's lock survives. Mutation: remove the RECLAIM_LOCK
  serialization -> RED.
- never-auto-steal: SIGKILL a reclaimer holding RECLAIM_LOCK; two contenders then attempt
  recovery; assert no fresh live owner's lock is ever unlinked and the run fails loud with the
  manual `rm` recovery on timeout. Mutation: reintroduce a read-pid-then-rm self-heal -> RED.
- exact-pathname acquisition: a legacy directory appears after `[ -d ]`; assert no child link is
  created and no ownership is claimed. Mutation: revert `link` -> `ln` -> RED.
- caught-signal cleanup: TERM a process holding RECLAIM_LOCK / mid reclaim; assert ownership-
  guarded cleanup and that a non-owner's lock is never removed. Mutation: drop the
  `_have_reclaim_lock` guard -> RED.
Plus retention of the existing deterministic tests and Sol #3 (pid-0) / #4 (literal-prefix
sweep) tests already green at 07dce51.

## 11. FILES confirmation
Payload strictly `scripts/dev_bootstrap.sh` + `tests/test_dev_bootstrap.py`. No `.gitignore`,
`.claude/settings.json`, new dependency, or other payload file. Lifecycle/review artifacts:
`docs/prd_history/PRD-301*.md` (PRD, reviews, confirmations) + this packet + its review/
confirmation. Any `.gitignore` need is a Section-8 RED stop.

## Required packet cycle (GOV-2)
1. Independent packet review.
2. One consolidated correction cycle.
3. Independent exact-corrected-head confirmation.
Then return for the owner design-direction ruling. Only after a review-clean packet + that
ruling may HELM update PRD-301 against the ruling, obtain fresh-context review of the exact
amended PRD revision, and return for explicit amended Gate A. Production implementation remains
prohibited until amended Gate A.

## CORRECTION CYCLE (GOV-2 independent packet review 2026-08-12 — one consolidated cycle)
The independent packet review returned REQUIRED-CHANGES (5 findings + 1 recommended). All are
resolved below; this is the single GOV-2 correction cycle.

FINDING 1 (RESOLVED) — the `_have_reclaim_lock` boolean was not an ownership PROOF across
release + caught-signal cleanup (A release -> B acquire -> TERM-A -> A's trap unlinks B's live
reclaim lock; and a signal after acquire but before flag-set wedges). CORRECTION: the boolean
flag is REMOVED; the EXIT trap removes RECLAIM_LOCK ONLY when it still holds THIS process's pid
(`IFS= read -r _p <"$RECLAIM_LOCK" && [ "$_p" = "$$" ] && rm -f "$RECLAIM_LOCK"`). This is a
pid-IDENTITY ownership proof: RECLAIM_LOCK cannot change hands while it holds our pid (any other
process's `link` fails EEXIST while it exists), so the read-then-rm is not a TOCTOU, and if B
holds it (B's pid) our trap reads B's pid != $$ and leaves it. The normal-release `rm -f
"$RECLAIM_LOCK"` is safe (we own it); a signal in the acquire->critical->release window leaves
RECLAIM_LOCK holding our pid, which the trap then cleans, or (SIGKILL) which the bounded-wait-
then-fail-loud path recovers. No boolean-flag window remains. Tests: A-release -> B-acquire ->
TERM-A asserts B's lock survives; TERM immediately after a successful acquire asserts the trap
cleans our own reclaim lock (no wedge).

FINDING 2 (RESOLVED) — `.stale.PID` exists in TWO forms (the pre-amendment regular-file hardlink
grave AND the legacy-directory grave); and the pre-amendment `ln`-into-dir defect can leave a
stray child inside a legacy directory, so a later dead/malformed reclaim's `rmdir` fails on the
non-empty grave and it persists. CORRECTION: the amended `_reclaim_lock` no longer creates a
`.stale.PID` file grave at all (it serializes via RECLAIM_LOCK); only `_reclaim_legacy_dir`
creates a `.stale.PID` (a moved-aside legacy directory). A dead/malformed legacy directory is
reclaimed ONLY when it is clean (`[ "$(ls -A "$LOCKFILE")" = pid ]`); a directory holding any
stray child (the former false-acquisition artifact) is NOT auto-removed -> `_reclaim_legacy_dir`
returns 3 and `_lock` FAILS LOUD ("legacy lock directory with stray content ... remove it
manually") — fail-closed, never a silent persist or auto-`rm -rf`. Test: seed a legacy dir with
a dead pid + a stray child, assert fail-loud rc 2 and no auto-removal.

FINDING 3 (RESOLVED) — the LOC derivation is now pinned to an AUDITABLE line-level diff from the
exact 07dce51 script (below). Durable model measured with the ceiling metric: 252 net-production
(bash -n clean) — within the 260 provisional ceiling (8-line margin). The prior narrative
`+0`-accounting referenced a superseded intermediate draft and is withdrawn; the diff is
authoritative.

FINDING 4 (RESOLVED) — wording corrected: POSIX standardizes the `link()` FUNCTION (atomic,
exact-pathname, EEXIST on existing target); `link(1)` is a coreutils/BSD COMMAND present on both
target platforms, not "the POSIX utility." A macOS-runner check (`command -v link`; `link src
dir` fails with no child; `link src newfile` succeeds; `link src existing` fails EEXIST) is a
REQUIRED pre-Gate-A portability validation, not optional documentation-based acceptance.

FINDING 5 (RESOLVED) — the mutation plan is tightened to controlled event orders: (serialization)
a 3-process order A-captures-and-removes-dead-D -> C-acquires-canonical (live) -> delayed-B-
unlinks, asserting C survives; (never-auto-steal) the two Finding-1 signal windows; (exact-
pathname) `[ -d ]` evaluated false, THEN the directory appears, THEN acquire, asserting no child
link + no false ownership; (fail-closed legacy) the Finding-2 seeded non-empty-legacy-dir. Each
guard has a NAMED real-process test whose corresponding mutant it independently reddens.

RECOMMENDED 1 (APPLIED) — §1's minimum pre-amendment race is THREE bootstrap processes: two
reclaimers A/B plus a distinct fresh acquirer C (with only A/B, neither performs the fresh
acquisition landing in the other's stat->unlink gap).

### AUDITABLE MODEL DIFF (verbatim unified diff; apply against `scripts/dev_bootstrap.sh` @ 07dce51 -> corrected amended model; 252 net-production, `bash -n` clean)
The hunks below are the exact line-level delta from the RED-held 07dce51 script to the
correction-cycle model. This is the pinned auditable model for Finding #3; the durable-model LOC
(252) is derived from applying it to 07dce51. Production implementation of it remains prohibited
until amended Gate A.
```diff
@@ -7,6 +7,7 @@
 VENV="$REPO_ROOT/.venv"
 VPY="$VENV/bin/python"
 LOCKFILE="$REPO_ROOT/.dev_bootstrap.lock"
+RECLAIM_LOCK="$LOCKFILE.reclaim"
 LOCK_TRIES="${DEV_BOOTSTRAP_LOCK_TRIES:-120}"
 LOCK_SLEEP="${DEV_BOOTSTRAP_LOCK_SLEEP:-0.5}"
 BEGIN="# >>> dev_bootstrap (PRD-293) >>>"
@@ -45,8 +46,9 @@
 }
 
 _on_exit() {
-  local rc=$?
+  local rc=$? _p
   [ -n "$_lock_tmp" ] && rm -f "$_lock_tmp"
+  IFS= read -r _p <"$RECLAIM_LOCK" 2>/dev/null && [ "$_p" = "$$" ] && rm -f "$RECLAIM_LOCK"
   _unlock || rc=2
   trap - EXIT
   exit "$rc"
@@ -69,11 +71,10 @@
 # hardlink grave, judge liveness on that immutable inode, and remove the lock only
 # if it is STILL that captured dead inode (a live/new owner is never touched).
 _reclaim_lock() {
-  local grave="$LOCKFILE.stale.$$" pid
-  ln "$LOCKFILE" "$grave" 2>/dev/null || return 1
-  IFS= read -r pid <"$grave" 2>/dev/null && _pid_live "$pid" && { rm -f "$grave"; return 1; }
-  [ "$LOCKFILE" -ef "$grave" ] && rm -f "$LOCKFILE"
-  rm -f "$grave"
+  local pid
+  link "$_lock_tmp" "$RECLAIM_LOCK" 2>/dev/null || return 1
+  { IFS= read -r pid <"$LOCKFILE" 2>/dev/null && _pid_live "$pid"; } || rm -f "$LOCKFILE"
+  rm -f "$RECLAIM_LOCK"
 }
 
 # Legacy (pre-PRD-301) DIRECTORY carrier, detected by [ -d ] (NOT by ln failing:
@@ -83,6 +84,7 @@
   local pid grave="$LOCKFILE.stale.$$"
   [ -s "$LOCKFILE/pid" ] && IFS= read -r pid <"$LOCKFILE/pid" 2>/dev/null && [ -n "$pid" ] || return 1
   _pid_live "$pid" && return 1
+  [ "$(ls -A "$LOCKFILE" 2>/dev/null)" = pid ] || return 3
   mv "$LOCKFILE" "$grave" 2>/dev/null || return 1
   rm -f "$grave/pid" 2>/dev/null; rmdir "$grave" 2>/dev/null || true
 }
@@ -97,8 +99,8 @@
   printf '%s\n' "$$" >"$_lock_tmp" || { rm -f "$_lock_tmp"; _lock_tmp=""; return 1; }
   while :; do
     if [ -d "$LOCKFILE" ]; then
-      _reclaim_legacy_dir || true
-    elif ln "$_lock_tmp" "$LOCKFILE" 2>/dev/null; then
+      _reclaim_legacy_dir; [ $? -eq 3 ] && { echo "dev_bootstrap: FAIL [legacy lock directory with stray content] $LOCKFILE -- inspect and, if no dev_bootstrap is running, remove it manually" >&2; return 2; }
+    elif link "$_lock_tmp" "$LOCKFILE" 2>/dev/null; then
       break
     else
       _reclaim_lock || true
@@ -107,6 +109,7 @@
     if [ "$i" -gt "$LOCK_TRIES" ]; then
       rm -f "$_lock_tmp"; _lock_tmp=""
       [ -d "$LOCKFILE" ] && [ ! -s "$LOCKFILE/pid" ] && { echo "dev_bootstrap: FAIL [legacy lock directory without pid] $LOCKFILE -- ensure no dev_bootstrap process is running, then remove it with: rmdir \"$LOCKFILE\"" >&2; return 2; }
+      [ -e "$RECLAIM_LOCK" ] && { echo "dev_bootstrap: FAIL [stale reclaim lock] $RECLAIM_LOCK -- ensure no dev_bootstrap process is running, then remove it with: rm -f \"$RECLAIM_LOCK\"" >&2; return 2; }
       return 1
     fi
     sleep "$LOCK_SLEEP"
```

POST-CORRECTION STATUS: the corrected packet supersedes §4-§10's pre-correction wording where it
conflicts with this cycle. Honest re-modeled ceiling remains 260 (model 252). Ready for the
independent exact-corrected-head confirmation, then the owner design-direction ruling. No
production implementation before amended Gate A.
