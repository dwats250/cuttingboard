# PRD-301 amended lock — portability evidence (owner ruling item C)

Packet-required pre-Gate-A portability validation of the amended primitives: the exact-pathname
`link` utility behavior and `ls -A` behavior, on the platforms R6 claims (Linux and macOS/BSD).
Recorded durably here (a review artifact; NOT added to the packet, whose change from e537b61 must
stay whitespace-only per owner item B).

## Linux — COMPLETE (executed 2026-08-12)

Platform: `Linux 6.12.74+deb13+1-amd64 x86_64` (Debian trixie). `link` = `/usr/bin/link` (GNU
coreutils 9.7); `ls` = GNU coreutils 9.7. Executed against real files in a scratch dir.

| Check | Command | Result | Expected | Pass |
|---|---|---|---|---|
| link into a directory | `link src d` (d is a dir) | `link: cannot create link 'd' to 'src': File exists`; rc=1; entries inside `d`: **none** | fail EEXIST, create no child | YES |
| link to a new name | `link src newfile` | rc=0; `newfile` exists; `src -ef newfile` = yes | succeed, same inode | YES |
| link onto existing | `link src existing` | `... File exists`; rc=1 | fail EEXIST | YES |
| ls -A empty dir | `ls -A empty` | `` (empty) | empty | YES |
| ls -A one-pid dir | `ls -A onlypid` | `pid` | `pid` | YES |
| ls -A stray dir | `ls -A stray` | `child pid` | both entries | YES |
| snapshot equality (clean) | `[ "$(ls -A onlypid)" = pid ]` | TRUE | TRUE (proceed) | YES |
| snapshot equality (stray) | `[ "$(ls -A stray)" = pid ]` | false | false (-> rc-3 path) | YES |

Conclusion (Linux): `link` provides exact-pathname EEXIST semantics on both file and directory
targets and never links inside a directory; `ls -A` gives the clean-vs-stray discrimination the
legacy-dir snapshot relies on. The mechanism's Linux assumptions are empirically confirmed.
Reproduce: `/home/dustin/.claude/jobs/fd88871b/tmp/portability_linux.sh` (harness; ephemeral).

## macOS/BSD — NOT OBTAINABLE INSIDE EXISTING AUTHORITY (owner item-C RED)

The packet makes a macOS-runner check a REQUIRED pre-Gate-A validation (not documentation-based
acceptance). It cannot be satisfied inside the current ratified authority:

- No macOS runner exists anywhere in the repo. All 8 GitHub Actions workflows run
  `runs-on: ubuntu-latest` (`.github/workflows/*.yml`); the project has never executed on macOS.
- The HELM environment is Linux (Debian); there is no local macOS to execute `link`/`ls -A` on.
- The only ways to obtain a macOS-runner check are OUTSIDE authority: (a) adding a
  `.github/workflows/*.yml` macOS job — a new file outside the ratified FILES
  (`scripts/dev_bootstrap.sh` + `tests/test_dev_bootstrap.py` + lifecycle/packet/review
  artifacts), and "no additional payload file"; or (b) a Mac the owner runs it on; or (c) the
  owner ruling macOS a non-target.
- Per owner item C, HELM STOPS at RED rather than weakening or inferring macOS behavior from
  man pages (which Finding 4 explicitly rejected as documentation-based acceptance).

This is the owner-anticipated RED. It blocks completing item C and therefore the fresh PRD review
(item D), whose package requires the portability evidence. Returned to the owner with options:

- Option A — owner supplies macOS evidence: run the same eight checks above on a Mac
  (`command -v link`; `link src dir` fails, no child; `link src newfile` ok; `link src existing`
  EEXIST; `ls -A` on empty/one-pid/stray) and provide the output; HELM records it here.
- Option B — owner authorizes a temporary macOS CI job as an explicit FILES addition (amended
  FILES): HELM adds a minimal `.github/workflows` macos-latest job asserting the checks, captures
  the run, and (optionally) removes it. This adds a file beyond the ratified FILES and needs the
  owner's explicit authorization.
- Option C (HELM recommendation if macOS is not a real dev/CI target) — owner rules macOS a
  NON-target for dev_bootstrap and narrows R6 to Linux-only. The whole system runs on the owner's
  Debian box + ubuntu CI; dropping an unvalidatable macOS claim is a doc correction (not a
  weakening: it removes the requirement rather than inferring the behavior), aligned with VISION
  cuts-before-additions. This eliminates the macOS-evidence obligation.

HELM has NOT chosen among these — it is an owner design/scope decision. No macOS behavior is
inferred or asserted here. 07dce51 stays RED-held; no production/test implementation; the 250
ceiling stays binding; no review (item D) proceeds until the owner resolves macOS.
