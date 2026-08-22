# GEX-3 MATERIAL packet -- GOV-2 Event-2 durable record, ATTEMPT 1

EVENT TYPE: EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 sec2 step 5), attempt 1
REVIEWER: Codex (second model), capability role: independent exact-head confirmer
CONFIRMED-TARGET SHA: 11d964329ad9c3e4def6f181b6bbfb44c1b1e87e
REVIEW DATE: 2026-08-22
VERDICT: NOT CONFIRMED (F2, F3 incompletely resolved; F1/F4/F5 RESOLVED; NO new material boundary)
SANDBOX: codex exec -s read-only; prompt via stdin; output captured verbatim below.
DISPOSITION: the two residuals are completion-of-resolution edits to the SAME Event-1 findings (encode --kill-after escalation in sec4; add the dirty-tree predicate to DR4(h) and global publish/failure-upload scans to DR6). Applied at the next commit; Event-2 ATTEMPT 2 targets that head. GEX-2 precedent: confirmation attempts repeat within the single bounded cycle until CONFIRMED or a new boundary appears.

----------------------------------------------------------------------

EVENT: EXACT-CORRECTED-HEAD CONFIRMATION
CONFIRMED SHA: 11d964329ad9c3e4def6f181b6bbfb44c1b1e87e
PRIOR EVENT: INITIAL PACKET REVIEW, DESIGN INCOMPLETE @ a718cf20d039706185ccf392d327a2d6e069173b, findings F1-F5

PER-FINDING:
F1: RESOLVED
Packet sec5 Parts A-B inventories hourly, pipeline render replacement and broad logs staging, macro preservation, dashboard preview, Pages deploy-on-any-completion, failure paths, publish retry/bootstrap, and last-writer persistence. Sec6 DR6 and existing publish/Pages guards cover the corresponding cross-workflow invariants; sec9 Q3 presents the persistence consequence to the owner.

F2: NOT RESOLVED
Packet sec4 uses "timeout 120" but omits "--kill-after"; coreutils timeout therefore sends catchable TERM only. The packet's claimed SIGKILL escalation is not encoded, and a TERM-ignoring hang can prevent timeout from returning and bypass ordinary nonzero cleanup, so the exact shell design does not provide the required hard wall-clock bound.

F3: NOT RESOLVED
Sec6 DR5 supplies the five-outcome shell harness, including hang, and DR4(h) checks both final and .tmp ignore coverage. However, DR4(h) omits the required observable clean dirty-tree predicate, while DR6 omits the required global publishing and failure-upload scans; it covers invocation, restore/stage, and the existing Pages guard only.

F4: RESOLVED
Packet sec7 adds truth-only edits for tools/gex_snapshot.py module/CLI text and docs/artifact_flow_map.md. Sec8 raises the test ceiling and adds a <= 10-line non-behavioral documentation ceiling while retaining zero behavioral Python changes.

F5: RESOLVED
Packet E8 limits return-1 claims to operational/provider/validation/ordinary-Exception failures and identifies naive-clock ValueError as a pre-catch programming error. Sec5 orders Aggregate before Refresh and requires a present, fresh, valid, in-domain artifact for card rendering.

NEW MATERIAL BOUNDARY INTRODUCED: no
The correction introduces no new consumer class, renderer, audit carrier, schema surface, or end-to-end seam; the failures above are incomplete resolutions of prior F2 and F3.

VERDICT: NOT CONFIRMED (F2, F3)

FRESH CONTEXT: Fresh independent Codex run, separate from the authoring session; no task-specific GEX-3 authoring memory was used. Inspection ran in a read-only sandbox. Final run-isolation evidence: HEAD remained 11d964329ad9c3e4def6f181b6bbfb44c1b1e87e, git status --porcelain was empty, and both unstaged and staged diffs were empty. GitNexus was attempted but reported zero indexed repositories; write-producing reindexing was not run.
