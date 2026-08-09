# Context Registry / NEWS-0 MATERIAL packet -- GOV-2 Codex review + exact-head confirmation

Independent GOV-2 upstream material-packet review and exact-corrected-head
confirmation. Reviewer: Codex (codex-cli 0.146.0), invoked
`codex exec -s read-only -c model_reasoning_effort=medium` (sandboxed
read-only, prompt via stdin, verdict from stdout). Fresh context: not the
packet author or its Fable pre-reviewer. Artifact written by Claude Code from
captured stdout; Codex wrote nothing into the repo tree. Subject of the review
is the PACKET and the repository surfaces -- not any other review's prose.

Target: `audits/context-registry-material-packet-2026-08/CONTEXT_REGISTRY_NEWS0_MATERIAL_PACKET_v0.1.md`

## 1. Packet review -- reviewed exact head `35c57ef29c35d91396587e438b0ca4d88c94216a`

**VERDICT: ACCEPT-WITH-REQUIRED-CORRECTIONS** (Codex confirmed the target blob
SHA-256 matched the working-tree artifact byte-for-byte).

**REQUIRED CORRECTION 1 (material accuracy).** Section 2 stated
`watchlist_sidecar.WATCHLIST_SYMBOLS` has "ZERO modules" / is human-reader-only;
however production runtime imports `build_watchlist_snapshot`
(`cuttingboard/runtime/__init__.py:58`) and invokes it (`:2279`) to write
`logs/watchlist_snapshot.json`. Amend section 2 to name runtime as the existing
producer surface while retaining the accurate R1 boundary (R1 changes neither
`watchlist_sidecar.py`, runtime, nor its artifact/consumer path). No FILES entry
is added -- R1 still performs zero consumer migration; the fix makes the
current-truth claim evidence-complete.

**RECOMMENDED 1.** Turn "canonically sorted" into explicit comparators for
`themes`, `sources`, aliases, and top-level ordering, so the Stage-0 validator
is deterministic rather than "canonical" by convention.

**Otherwise clean (Codex's acceptance summary).** The FILES ceiling is complete
for R1 (five new paths + CI workflow line + explicitly allowlisted lifecycle
touches; section 9). No existing production consumer is repointed; runtime,
payload, renderer, decision configuration, and classification/config parity are
all walled out (section 8). Schema internally coherent as a proposal --
conditional benchmark validation, strict-key intent, closed enums, no
numeric/scoring fields (sections 4.1, 10). REG-D2 quoted verbatim and confined
to its three settled propositions (section 5); candidate seeds, SMCI, and the
`_OPTIONAL_MACRO_DRIVERS` debt handled faithfully (sections 2, 5, 14).
MATERIAL / STANDARD / no-evidence-packet supported (section 11).

## 2. Consolidated correction applied -- corrected head `5ad4c66cb01a33cfb0f879d026c2918a798f0664`

GOV-2 single consolidated correction, authored on top of `35c57ef`:
- Section 2 watchlist row now names runtime as the producer surface (import
  `runtime/__init__.py:58`, call `:2279`, artifact `logs/watchlist_snapshot.json`),
  retains the "R1 touches none of it" boundary. (Verified firsthand by the
  campaign HELM before applying: import at :58, call at :2279 are real.)
- Section 10 now specifies explicit comparators: `symbols[]` byte-wise by
  `symbol`; `themes[]` by theme `id`; `sources[]` by `domain`; aliases byte-wise;
  fixed top-level order `meta`, `themes`, `symbols`, `sources`.
The `35c57ef..5ad4c66` diff is confined to those two locations.

## 3. Exact-corrected-head confirmation -- confirmed head `5ad4c66cb01a33cfb0f879d026c2918a798f0664`

Narrow GOV-2 confirmation (reads the corrected head + the prior findings list;
not a fresh-scope review).

**VERDICT: CONFIRMED -- corrected head addresses the findings; GOV-2
review-clean for the owner design-direction ruling.**

Codex's justification: section 2 now names runtime's import (`:58`), call
(`:2279`), and `logs/watchlist_snapshot.json`, explicitly retaining that R1
changes none of the sidecar/runtime/artifact path; both runtime sites are real;
section 10 specifies byte-wise symbol/alias ordering, theme-id ordering,
source-domain ordering, and fixed top-level order; the `35c57ef..5ad4c66` diff
changes only the section-2 row and the section-10 ordering line, retains the
FILES ceiling, and introduces no scope expansion.

## Disposition

GOV-2 upstream sequence complete for this MATERIAL packet: independent Codex
packet review + one consolidated correction + independent SHA-pinned
confirmation of the exact corrected head. Per GOV-2, the packet is now eligible
for Dustin's design-direction ruling (and the deferred REG-D1, REG-D3..D7
owner choices the packet presents). Nothing downstream (Stage-0 PRD drafting,
Gate A) is authorized by this artifact. Merge of the packet branch remains
Dustin's act.
