# GEX-3 MATERIAL packet -- GOV-2 Event-2 durable record, ATTEMPT 2 (CONFIRMING)

EVENT TYPE: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 sec2 step 5), attempt 2
REVIEWER: Codex (second model), capability role: independent exact-head confirmer
CONFIRMED SHA: 965529c52b5b38c8cf78a844d4ae0211c51d061d (packet revision 3 on claude/gex-3-material-packet; base main ed53df3)
REVIEW DATE: 2026-08-22
VERDICT: CONFIRMED -- F1-F5 all RESOLVED at the exact confirmed head; NO new material boundary. The packet at 965529c is the REVIEW-CLEAN revision.
PRIOR EVENTS: Event-1 INITIAL PACKET REVIEW, DESIGN INCOMPLETE @ a718cf2 (F1-F5); Event-2 attempt 1, NOT CONFIRMED @ 11d9643 (F2/F3 residuals).
FINDINGS ENUMERATION CONFIRMED: F1 (cross-workflow/final-consumer inventory) RESOLVED; F2 (hard wall-clock bound with encoded --kill-after escalation) RESOLVED; F3 (dirty-tree predicate + global workflow scans) RESOLVED; F4 (truth-only FILES additions) RESOLVED; F5 (precision) RESOLVED.
SANDBOX: codex exec -s read-only; prompt via stdin; output captured verbatim below.
NOTE: this record is committed AFTER the confirmed head by design -- the confirmed packet revision is identified by SHA and is not edited post-confirmation; the packet status line's 'awaiting Event-2' is superseded by THIS record.

----------------------------------------------------------------------

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION (ATTEMPT 2)
CONFIRMED SHA: 965529c52b5b38c8cf78a844d4ae0211c51d061d
PRIOR EVENTS: Event-1 DESIGN INCOMPLETE @ a718cf2 (F1-F5); Event-2 attempt 1 NOT CONFIRMED @ 11d9643 (F2, F3)
PER-FINDING:
F1: RESOLVED
Evidence: Unchanged since attempt 1. Sec5 Parts A-B retain the complete hourly, pipeline, macro, preview, publish/Pages, failure-path, and last-writer inventory; sec9 Q3 retains explicit owner acceptance of the persistence semantics.
F2: RESOLVED
Evidence: Sec4 now encodes `timeout --kill-after=10 120`; TERM expiry escalates to SIGKILL and the resulting nonzero exit reaches the same `|| rm` cleanup. A focused TERM-ignoring-process check returned exit 137.
F3: RESOLVED
Evidence: DR4(h) now requires both artifact paths to be physically present, ignored, and absent from `git status --porcelain`; DR6 is explicitly global over `.github/workflows/*.yml` and scans restore, staging, publish/deploy, and failure-upload path lists.
F4: RESOLVED
Evidence: Unchanged since attempt 1. Sec7 retains the required truth-only updates to `tools/gex_snapshot.py` and `docs/artifact_flow_map.md`; sec8 retains the non-behavioral documentation ceiling.
F5: RESOLVED
Evidence: Unchanged since attempt 1. E8 retains the narrowed failure claim; sec5 retains Aggregate before Refresh and requires a present, fresh, valid, in-domain artifact for rendering.
NEW MATERIAL BOUNDARY INTRODUCED: no
The attempt-2 delta completes the existing F2/F3 requirements without adding a consumer class, carrier, schema surface, renderer, workflow, or end-to-end seam.
VERDICT: CONFIRMED
FRESH CONTEXT: Fresh independent Codex context, separate from the authoring session, using only the required prior-event records and focused repository evidence. Inspection ran in a read-only sandbox. Final isolation evidence: HEAD remained 965529c52b5b38c8cf78a844d4ae0211c51d061d; `git status --porcelain=v1` was empty; unstaged and staged diff checks both returned exit 0. GitNexus comparison mapping was attempted but its service reported no indexed repositories; write-producing reindexing was not run.
