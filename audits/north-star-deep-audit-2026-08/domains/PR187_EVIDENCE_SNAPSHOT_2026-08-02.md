# PR #187 Review-Thread Evidence Snapshot (Domain A)
**Capture timestamp:** 2026-08-02T04:12:33Z
**Capture reference:** `gh api repos/dwats250/cuttingboard/pulls/187/comments --paginate` (inline review comments) and `gh api repos/dwats250/cuttingboard/issues/187/comments` (issue-level comments), run against PR #187 in state `closed`/`merged` (merge commit `fdeef90b0a0e0747d1bbf92385d3750b4024f4ae`).
**Count:** 29 inline review comments, 0 issue-level comments, 0 with `in_reply_to_id` set (no threaded replies exist as of this capture).
**Correction (time-bound, not a mechanical-defect claim):** Phase 0 recorded
28 comments at its capture point, shortly after PR #187's merge
(`2026-08-02T00:07:32Z`). A subsequent connector comment (id `3696977973`)
was posted at `2026-08-02T00:08:09Z`, 37 seconds after that merge and after
Phase 0's capture, so this timestamped Phase 1 snapshot contains 29. The
unqualified "28" stated elsewhere in the scaffold is therefore stale for
Phase 1, but Phase 0's earlier enumeration is not treated as mechanically
defective — it was accurate when captured. This snapshot is the
authoritative evidence Domain A's dispatch actually used. Flagged to
Dustin, not silently corrected in the scaffold's Phase 0 prose.
**Since this data is GitHub-hosted PR metadata, not a repository path, it is not `git show`-pinned (Charter Sec2). If a new reply or changed thread state appears on PR #187 after this timestamp, that is new material routed to the Amendments Log per Charter Sec2 -- never silently substituted.**

---
## PRD-228 disposition reminder (Charter Sec5)
Resolved/unresolved and outdated/current fields (captured in the Phase 0 charter attestation as: all threads unresolved, some outdated) are GitHub workflow metadata only. They establish none of ACTIONED / DISMISSED / BLOCKED-PARKED by themselves. Domain A determines actual disposition from the comment bodies below: an in-thread fixing SHA/PRD reference indicates ACTIONED; an explicit dismissal reason indicates DISMISSED; a stated valid-but-uncorrected dependency/GOV-2 hold/owner ruling indicates BLOCKED/PARKED. No disposition is pre-assigned in this snapshot.

---
## Full comment record

### Comment 1 of 29 -- id `3696498125`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T19:53:20Z
- In reply to: none (top-level)
- Body:

```
Keep L0 open until its required rulings land**

This marks L0's exit condition as met while the same row admits that PRD-268's disposition is still open, and PRD-271's Gate A is also listed as pending. The authoritative workplan requires both rulings in its L0 sequence (`docs/plans/decision-support-workplan-v0.1.md:128-138`) before L0 exits, so treating the row as completed can let later work bypass unresolved lifecycle gates. Keep L0 in progress, or explicitly state that only the narrower numbering freeze has ended.

Useful? React with 👍 / 👎.
```

### Comment 2 of 29 -- id `3696498129`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T19:53:20Z
- In reply to: none (top-level)
- Body:

```
Assign NS-4A/4B one portfolio state**

This promotes NS-4A/4B to `NEXT`, but the same program says NS-4A “stays LATER” at line 93 and the companion ledger marks both NS-4A and NS-4B as `LATER` at lines 139-140. Because `NEXT` means an approved follow-on while `LATER` is explicitly unauthorized, agents cannot determine whether this work may enter intake. Reconcile these entries to one state before making this the authoritative portfolio.

Useful? React with 👍 / 👎.
```

### Comment 3 of 29 -- id `3696498132`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T19:53:20Z
- In reply to: none (top-level)
- Body:

```
Keep unverified findings out of non-blocking debt**

These eighteen findings are placed under the “Open, non-blocking” heading even though their current truth was never investigated; the source matrix explicitly says CB-35 and CB-38 retain plausible Critical/High consequences (`audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md:419-442`). Classifying them as non-blocking without verification can suppress a safety-relevant stop condition and also makes the claim that NS-0C completed debt classification unsupported. Preserve them as `UNKNOWN` outside the non-blocking bucket until the commissioned sweep determines their disposition.

Useful? React with 👍 / 👎.
```

### Comment 4 of 29 -- id `3696498135`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T19:53:20Z
- In reply to: none (top-level)
- Body:

```
Define NS-0B's post-merge state**

When Dustin performs the stated exit action and merges this commit, the version on `main` will still label NS-0B as `NOW`, identify an ephemeral feature branch as current, and say ratification remains pending. With the ledger's one-`NOW` invariant, that immediately stale state can block or conflict with promotion of the actual next packet. Encode the merge-contingent transition to `COMPLETE`, or provide a closeout mechanism that updates the authoritative portfolio as part of ratification.

Useful? React with 👍 / 👎.
```

### Comment 5 of 29 -- id `3696498138`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`, line 402
- Created: 2026-08-01T19:53:20Z
- In reply to: none (top-level)
- Body:

```
Link the authoritative ledger from a canonical entry point**

A repository-wide search finds these new North Star documents referenced only by each other; neither `CLAUDE.md`, `docs/PROJECT_STATE.md`, `VISION.md`, nor `README.md` points to them. Fresh agents are instructed to begin with those canonical sources and will therefore continue using the older workplan without discovering this purported authoritative portfolio, defeating the stated protection against lost or competing plans. Add a pointer from the canonical-source/current-state surface before declaring this ledger authoritative.

Useful? React with 👍 / 👎.
```

### Comment 6 of 29 -- id `3696498140`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`, line 181
- Created: 2026-08-01T19:53:20Z
- In reply to: none (top-level)
- Body:

```
Preserve the separate CB-12b debt row**

This ledger carries CB-12 but omits CB-12b entirely from both new documents, even though the authoritative finding matrix tracks CB-12b as a separate `PARTIAL` Medium finding with different missing technical backstops (`audits/current-state-reconciliation-2026-07-30/FINDING_STATUS_MATRIX.md:256-279`). Collapsing it into CB-12 loses its distinct status, evidence, and next authority while the program claims to map every existing finding. Add CB-12b explicitly to the debt ledger rather than allowing it to disappear.

Useful? React with 👍 / 👎.
```

### Comment 7 of 29 -- id `3696498141`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T19:53:20Z
- In reply to: none (top-level)
- Body:

```
Keep the critical kill-switch bypass ahead of new product work**

CB-01 is a confirmed Critical defect that bypasses the hourly channel's live kill switch and falsely reports it clear, yet this program places it in the non-blocking bucket and Option B promotes the new NS-2 product slice directly while leaving CB-01 merely awaiting later numbering. That contradicts the ledger's own stop exception for unsafe execution and permits trader-facing expansion while an active safety surface is bypassed. If CB-02 is parked, require an explicit Dustin ruling to defer CB-01 rather than silently skipping it on the runway.

Useful? React with 👍 / 👎.
```

### Comment 8 of 29 -- id `3696498144`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T19:53:20Z
- In reply to: none (top-level)
- Body:

```
Stop claiming CI validates the portfolio's semantic truth**

Neither new product document is consumed by the registry validator or by any test, so a green CI run only establishes that existing code and registry checks still pass; it cannot prove that these statuses, dependencies, or repository-truth claims preserve the baseline. This is especially misleading for a document presented as repository-verified. Reword the note to state that CI does not validate the portfolio semantics, or add a check that actually verifies the asserted mappings before claiming proof.

Useful? React with 👍 / 👎.
```

### Comment 9 of 29 -- id `3696639311`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T21:06:48Z
- In reply to: none (top-level)
- Body:

```
Assign NS-1D a consistent portfolio state**

After ratification, this row makes NS-1D an approved `NEXT` follow-on, but the companion program's authoritative `NEXT` portfolio lists only NS-2A/B/C and NS-2E (`NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:263-276`), and the recommended runway omits NS-1D as well. Because `NEXT` explicitly means approved for follow-on intake, agents cannot determine whether the prospective baseline freeze is eligible for promotion or merely preserved future work; place it consistently in the program's sequence or change this state.

Useful? React with 👍 / 👎.
```

### Comment 10 of 29 -- id `3696639315`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T21:06:48Z
- In reply to: none (top-level)
- Body:

```
Keep the GEX follow-ons evidence-blocked**

These rows relabel GEX-1 and GEX-2 as `LATER`, although the still-authoritative workplan assigns both `EVIDENCE BLOCKED` (`docs/plans/decision-support-workplan-v0.1.md:50-52`) and the governing doctrine requires every planned item to carry exactly one state with that workplan as the sole planning ledger (`decision-support-expansion-doctrine-v0.1.md:367-386`). Because `LATER` is eligible for Dustin promotion while `EVIDENCE BLOCKED` preserves the prerequisite evidence gate, the competing state can allow producer or consumer intake before GEX-0 succeeds; retain the governed state or explicitly separate portfolio rank from lifecycle state.

Useful? React with 👍 / 👎.
```

### Comment 11 of 29 -- id `3696639317`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T21:06:48Z
- In reply to: none (top-level)
- Body:

```
Include PR #187 in the open-PR baseline**

In this revision PR #187 is repeatedly identified as the current draft awaiting Dustin's merge and has already received the review corrections incorporated here, so the same session cannot truthfully report exactly two open PRs, #184 and #185, without qualifying this as a snapshot taken before #187 was opened. This leaves the NS-0A truth-reset exit claiming that the open-PR inventory agrees while omitting its own active packet; record #187 or state the precise pre-opening cutoff.

Useful? React with 👍 / 👎.
```

### Comment 12 of 29 -- id `3696639320`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T21:06:48Z
- In reply to: none (top-level)
- Body:

```
Move CB-07 out of the non-blocking bucket**

When the NS-2A/B/C slice is selected, this row is not non-blocking: the same program makes PRD-271's Gate A ruling an explicit entry condition for that slice (`NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:266-275`) and calls CB-07 its runway dependency here. Leaving it under the delivered “Open, non-blocking” classification lets intake treat the ORB defect as skippable even though the portfolio forbids implementation until its ruling lands; classify it as blocking NS-2 or make the conditional scope explicit.

Useful? React with 👍 / 👎.
```

### Comment 13 of 29 -- id `3696686944`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`, line 91
- Created: 2026-08-01T21:25:30Z
- In reply to: none (top-level)
- Body:

```
Keep L0 as the sole current packet until its rulings land**

After the correction that leaves L0 `IN PROGRESS`, this row simultaneously makes NS-0B the `NOW` and “current active” packet. `docs/PROJECT_STATE.md:17-20` still identifies L0 as the current packet, and the governing workplan requires `PROJECT_STATE.md` to name exactly one current packet (`docs/plans/decision-support-workplan-v0.1.md:88-92`); until the PRD-268 disposition and PRD-271 Gate A ruling land, agents therefore receive two competing active packets. Keep NS-0B outside `NOW` while L0 remains current, or explicitly revise the governing workplan's single-current-packet contract.

Useful? React with 👍 / 👎.
```

### Comment 14 of 29 -- id `3696686946`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T21:25:30Z
- In reply to: none (top-level)
- Body:

```
Keep PRD-268 IN PROGRESS until Dustin dispositions it**

This changes PRD-268's working state to `PARKED` even though the same row admits that its canonical state is still `IN PROGRESS`, as recorded in both `docs/prd_history/PRD-268.md:1-4` and `docs/PRD_REGISTRY.md:288`; the companion program also promises that it changes no lifecycle status. Because this document still leaves the actual approve / return-to-PROPOSED / deprecate choice for a later Dustin ruling, ratifying it supplies no stated authority for the fourth `PARKED` disposition and can cause agents to omit PRD-268 from the active L0 reconciliation. Retain `IN PROGRESS / DECISION REQUIRED` until one of the named dispositions is explicitly chosen.

Useful? React with 👍 / 👎.
```

### Comment 15 of 29 -- id `3696686950`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`, line 10
- Created: 2026-08-01T21:25:30Z
- In reply to: none (top-level)
- Body:

```
Map the three fixed reconciliation findings**

A repository-wide search of both new product documents finds no entries for CB-13, CB-14, or CB-15, despite this promise to map every existing finding and the source-map claim that §5 covers CB-01 through CB-47. The authoritative matrix tracks these as three separate `FIXED` findings with distinct evidence and residual boundaries (`FINDING_STATUS_MATRIX.md:278-335`), including CB-13's explicit separation from still-open CB-08; omitting them makes NS-0C's supposedly complete classification indistinguishable from silently losing resolved findings. Add explicit `FIXED`/`COMPLETE` dispositions for all three.

Useful? React with 👍 / 👎.
```

### Comment 16 of 29 -- id `3696731017`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T21:50:05Z
- In reply to: none (top-level)
- Body:

```
Keep PRD-268 in CB-02's prerequisite chain**

When Dustin selects Option A, this declaration allows CB-02 implementation while PRD-268 remains unruled. In the checked `docs/plans/decision-support-workplan-v0.1.md`, lifecycle reconciliation precedes existing truth/safety fixes and a later wave may not bypass an earlier gate (lines 18-29); PRD-268's disposition is a required L0 step (lines 128-149), while OPT-1 is Wave 2. Even though §3 now correctly keeps L0 `IN PROGRESS`, calling PRD-268 a different-surface non-blocker still bypasses that authoritative sequencing gate; require its disposition before CB-02 implementation or explicitly revise the governing workplan.

Useful? React with 👍 / 👎.
```

### Comment 17 of 29 -- id `3696731019`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T21:50:05Z
- In reply to: none (top-level)
- Body:

```
Make the document status merge-contingent**

After Dustin merges PR #187, `docs/PROJECT_STATE.md` says this document becomes the authoritative portfolio, but this unconditional header will still identify it as a draft awaiting ratification (and line 428 repeats that it awaits ratification). The fresh inconsistency after the row-level transition fix is that only NS-0B's row is merge-contingent; readers who use the file-level status still receive the opposite authority signal. Encode the merge-contingent ratified state in the document status as well.

Useful? React with 👍 / 👎.
```

### Comment 18 of 29 -- id `3696731022`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`, line 303
- Created: 2026-08-01T21:50:05Z
- In reply to: none (top-level)
- Body:

```
Review the NS-2 material packet before PRD-271 Gate A**

When the NS-2 slice is promoted, these entry conditions put PRD-271 Gate A before the new MATERIAL packet that will define the shared ORB observation/execution boundary. In the checked `docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md`, the required order is material-packet review and exact-head confirmation, Dustin's design-direction ruling, PRD drafting/review, and only then Gate A (lines 65-84); because NS-2B must ride PRD-271 and this slice adds a persisted schema with multiple readers, issuing Gate A first leaves it based on an unreviewed boundary and may immediately require an amended gate. Make the NS-2 packet and its review prerequisites to PRD-271's Gate A rather than beginning that packet afterward.

Useful? React with 👍 / 👎.
```

### Comment 19 of 29 -- id `3696731024`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T21:50:05Z
- In reply to: none (top-level)
- Body:

```
Keep NS-0A open while the PRD inventories disagree**

This exit claims that PRDs and packets agree, but the companion program explicitly retains CB-28 because `docs/PROJECT_STATE.md` says `Active PRD: none` while the registry has four `IN PROGRESS` rows (`NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:192-194`), and the checked state file still contains that assertion at line 28. That self-admitted canonical disagreement means the repository-truth-reset acceptance condition is not met; either reconcile the active-PRD wording or qualify NS-0A's exit rather than marking it complete.

Useful? React with 👍 / 👎.
```

### Comment 20 of 29 -- id `3696764892`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T22:07:04Z
- In reply to: none (top-level)
- Body:

```
Keep OPT-0 evidence-blocked until Dustin approves it**

The authoritative workplan still assigns OPT-0 `EVIDENCE BLOCKED` and defines its exit as Dustin approving the carrier, reason semantics, and implementation seam (`docs/plans/decision-support-workplan-v0.1.md:41,195`), while this program acknowledges that exact-head independent confirmation remains outstanding. Declaring that lifecycle row stale before those gates are satisfied contradicts this document's promise not to change lifecycle status and can cause a resumed CB-02 sequence to treat the required OPT-0 approval as already complete.

Useful? React with 👍 / 👎.
```

### Comment 21 of 29 -- id `3696764895`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`, line 81
- Created: 2026-08-01T22:07:04Z
- In reply to: none (top-level)
- Body:

```
Preserve the queued second-model commission work**

This maps the stage0-05 governance-debt artifact into the debt ledger, but neither that ledger nor the not-lost appendix carries its Q24 `prd-second-model-commission` item. The source artifact says its queue dependency is cleared and activation awaits an operator commission (`audits/stage0-recon-2026-07-20/stage0-05-governance-debt-v0.1.md:78-96`), and `docs/PROJECT_STATE.md:195` still explicitly queues it after PRD-268. Once this program becomes authoritative, that open work therefore disappears despite the stated goal of mapping every existing plan and debt; give it an explicit parked/queued disposition.

Useful? React with 👍 / 👎.
```

### Comment 22 of 29 -- id `3696877555`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T23:05:36Z
- In reply to: none (top-level)
- Body:

```
Preserve OPT-1's evidence-blocked lifecycle**

The checked lifecycle ledger still assigns OPT-1 `EVIDENCE BLOCKED` until OPT-0 exits (`docs/plans/decision-support-workplan-v0.1.md:41-42,195`), but this row replaces that governed condition with `DRAFTED / BLOCKED`. Because the new ledger says the workplan remains authoritative and the companion program promises not to change lifecycle states, readers cannot tell whether OPT-0's evidence approval is still a prerequisite; retain `EVIDENCE BLOCKED` explicitly and record drafting progress on a separate axis.

Useful? React with 👍 / 👎.
```

### Comment 23 of 29 -- id `3696877557`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`, line 198
- Created: 2026-08-01T23:05:36Z
- In reply to: none (top-level)
- Body:

```
Carry the remaining queued debt into the ledger**

This supposedly complete debt classification omits several explicitly open items from the canonical state: `docs/PROJECT_STATE.md:160-164` parks three PRD-255 follow-ons, and line 196 separately retains the unscaffolded live-dropout instrument plus two queued adjacent follow-ups. A repository-wide search finds none of those concerns in either new North Star document, so making this program authoritative loses their dispositions despite the claim that every known debt was mapped; add explicit parked or decision-required entries.

Useful? React with 👍 / 👎.
```

### Comment 24 of 29 -- id `3696877558`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`, line 53
- Created: 2026-08-01T23:05:37Z
- In reply to: none (top-level)
- Body:

```
Run this governance change through GOV-2's MATERIAL sequence**

When PR #187 merges, these single-packet, promotion-authority, acceptance, and review rules become durable governance guardrails. GOV-2's intake test explicitly classifies any governance-guardrail change as MATERIAL (`docs/governance/GOV-2_MATERIAL_REVIEW_ORDER_2026-07-31.md:18-34`), and its required evidence includes a provisional packet, independent review, corrected-head confirmation, and committed packet-local records (`:67-110`); a repository-wide search finds no North Star MATERIAL packet or review record, and GOV-2 says connector comments cannot substitute for one. Complete that sequence before merge-contingent ratification rather than making this authoritative outside the process it invokes.

Useful? React with 👍 / 👎.
```

### Comment 25 of 29 -- id `3696877559`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`, line 132
- Created: 2026-08-01T23:05:37Z
- In reply to: none (top-level)
- Body:

```
Target the existing candidate-card surface for NS-2E**

The retained Stage-0 evidence identifies `_render_candidate_card` as the current relevant surface and explicitly says no Control Card contract exists (`audits/stage0-recon-2026-07-20/stage0-01-decision-surface-v0.1.md:166-176`); the companion source map repeats that conclusion at line 93. Calling NS-2E a replacement/refactor of the generic Market Map points its future MATERIAL packet at a different surface and can leave the existing candidate-card rows duplicated or undispositioned. Name the candidate card as the current surface, or explicitly specify how both surfaces are reconciled.

Useful? React with 👍 / 👎.
```

### Comment 26 of 29 -- id `3696877561`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md`, line 124
- Created: 2026-08-01T23:05:37Z
- In reply to: none (top-level)
- Body:

```
Promote the shared freshness contract before its consumers**

This graph names the NS-9C freshness vocabulary as shared substrate, but the portfolio leaves all of NS-9 until the final LATER item (`NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md:309-314,339`) while the NEXT NS-2 slice already requires visible freshness and explicit stale behavior, and the earlier NS-4B heatmap likewise requires visible freshness (`CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:128-130,154`). Those packets therefore either cannot satisfy their acceptance language or must invent local freshness contracts that NS-9 later replaces. Split or promote the bounded NS-9C contract as a prerequisite for the first freshness-consuming packet.

Useful? React with 👍 / 👎.
```

### Comment 27 of 29 -- id `3696950346`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T23:49:52Z
- In reply to: none (top-level)
- Body:

```
Insert the outstanding OPT-0 approval into the sequence**

When CB-02 is resumed, this “exact remaining sequence” jumps from PR #184 confirmation directly to PR #185 consistency and PRD review, omitting OPT-0's required Dustin approval of the carrier, reason semantics, and implementation seam. The corrected companion-ledger row now explicitly confirms that approval remains outstanding (`CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md:261`), and the governing workplan makes it OPT-0's exit (`decision-support-workplan-v0.1.md:195`); without a distinct approval step, the sequence permits OPT-1 to advance while its stated lifecycle prerequisite remains evidence-blocked.

Useful? React with 👍 / 👎.
```

### Comment 28 of 29 -- id `3696950347`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/NORTH_STAR_IMPLEMENTATION_PROGRAM_v0.1.md` (file-level, no line anchor)
- Created: 2026-08-01T23:49:52Z
- In reply to: none (top-level)
- Body:

```
Include PRD-268 in the precise blocker list**

When Dustin resumes CB-02, this claims that steps 1–4 are precisely all blockers and immediately classifies PRD-268 as non-blocking, but the fresh correction at lines 353–355 now explicitly prohibits final Gate A until PRD-268 is dispositioned and the L0 gate closes. These mutually exclusive instructions can cause an agent following the summarized blocker list to seek Gate A prematurely; list PRD-268 as an actual sequencing blocker rather than a stale/apparent one.

Useful? React with 👍 / 👎.
```

### Comment 29 of 29 -- id `3696977973`
- Author: `chatgpt-codex-connector[bot]`
- Path: `docs/product/CUTTINGBOARD_NORTH_STAR_MASTER_LEDGER_v0.1.md`, line 263
- Created: 2026-08-02T00:08:09Z
- In reply to: none (top-level)
- Body:

```
Preserve PRD-271's IN PROGRESS lifecycle**

When this ledger becomes authoritative after merge, this row assigns PRD-271 the unqualified state `BLOCKED`, although both `docs/PRD_REGISTRY.md:291` and `docs/prd_history/PRD-271.md:3` still record its canonical lifecycle as `IN PROGRESS`, and the companion program promises not to change lifecycle statuses. Since the ledger's vocabulary treats `BLOCKED` as a lifecycle condition, readers can incorrectly drop PRD-271 from the active reconciliation; retain `IN PROGRESS` and express the pending Gate A separately, such as `IN PROGRESS / BLOCKED`.

Useful? React with 👍 / 👎.
```
