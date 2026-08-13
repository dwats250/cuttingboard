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

## macOS — COMPLETE (owner event #6, Option B; executed on GitHub-hosted macOS runners)

Obtained via the owner-authorized temporary evidence-only workflow
`.github/workflows/prd301_macos_portability_evidence.yml` (permissions `{}`, no secrets, no
checkout, no third-party Actions, no writes, 5-minute timeout, matrix fail-fast off), triggered by
draft PR #248.

- Evidence commit SHA: **8452e144360cb327792bfcbb195883d3688881fd**
- Run: https://github.com/dwats250/cuttingboard/actions/runs/31647596061 (conclusion: success)
- Jobs (both success):
  - `link_ls_evidence (macos-15)` — https://github.com/dwats250/cuttingboard/actions/runs/31647596061/job/94284651440
  - `link_ls_evidence (macos-15-intel)` — https://github.com/dwats250/cuttingboard/actions/runs/31647596061/job/94284651283
- Hermetic posture confirmed in the run log: GITHUB_TOKEN Permissions = `Metadata: read` only (the
  irremovable minimum under `permissions: {}`); no other scope; no secret consumed; no checkout.

| Runner | Kernel / arch | macOS | Runner image | `link` | `ls` | Result |
|---|---|---|---|---|---|---|
| `macos-15` (Apple Silicon) | Darwin 24.6.0 arm64 | 15.7.7 (24G720) | macos-15 20260727.0377.1 | /bin/link | /bin/ls | PORTABILITY-OK |
| `macos-15-intel` (Intel) | Darwin 24.6.0 x86_64 | 15.7.7 (24G720) | macos-15 20260727.0377.1 | /bin/link | /bin/ls | PORTABILITY-OK |

Both runners passed ALL EIGHT assertion-hard checks (correctness from return codes + filesystem
state): `link` present at `/bin/link`; `link src dir` fails and creates NO child inside the
directory; `link src newfile` succeeds (same inode); `link src existing` fails EEXIST; `ls -A`
gives empty / `pid` / `child pid` for empty / one-pid / stray dirs; `[ "$(ls -A onlypid)" = pid ]`
holds and `[ "$(ls -A stray)" = pid ]` does not. macOS `link` is the BSD `link(1)` utility at
`/bin/link`, present on both architectures, with the same exact-pathname EEXIST semantics as
Linux — no macOS behavior was inferred; it was executed.

Conclusion (macOS): the amended mechanism's `link` exact-path and `ls -A` assumptions are
empirically confirmed on macOS 15 (both Apple Silicon and Intel). Portability item C is COMPLETE
on Linux + macOS.

## Item C disposition: COMPLETE

Linux and macOS (both arches) empirically confirm the amended primitives. Per the owner protocol
(event #6), the temporary evidence-only workflow is REMOVED in a separate commit after this record
lands, and its absence from the final diff (plus no change to any existing workflow) is proven
below/in the PR. 07dce51 stays RED-held; no production/test implementation; the 250 ceiling stays
binding; 260 remains only proposed. The fresh-context PRD review (item D) may now proceed.
