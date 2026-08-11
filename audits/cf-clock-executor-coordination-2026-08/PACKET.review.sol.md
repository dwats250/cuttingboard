# CF Clock/Executor Coordination packet — INITIAL PACKET REVIEW (GOV-2 §2/§7)

## GOV-2 durable record

- **Event type:** `INITIAL PACKET REVIEW` (GOV-2 §2 auto-commissioned MATERIAL
  packet-cycle event 1 of 2).
- **Reviewer identity / capability role:** GPT-5.6 **Sol** / independent
  fresh-context — the Adversary / independent-review seat
  (`docs/AGENT_SEATING.md`: "Codex/Sol"). Genuinely independent of the authoring
  Claude session: a different model family, fresh context, commissioned and run
  by Dustin — NOT the packet author and NOT a subagent spawned by the authoring
  session (so it satisfies GOV-2 §3, unlike the author-side evidence review in
  `PACKET.review.evidence.md`).
- **Exact reviewed SHA:** `12c77ca7782a21ccb6a9b841f6a0b49d6a41fb5d`
  (packet v0.3).
- **Review date:** 2026-08-11.
- **Verdict:** **REQUIRED CHANGES** (one finding, C5).
- **Fresh-context / independence evidence:** run as a separate GPT-5.6 Sol
  review seat outside the authoring session; the authoring HELM did not perform,
  prompt in-line, or spawn this review; recorded here as relayed by the owner.

## Verdict: REQUIRED CHANGES

### FINDING C5 — Dedicated OPEN group does not fully remove pending eviction

- **Severity:** REQUIRED / load-bearing availability defect.
- **Mechanism:** §7.4 / D2 dedicated OPEN concurrency group.
- **Failure:** The packet correctly identifies GitHub's default single-pending
  replacement behavior, but concludes that moving OPEN runs to a dedicated group
  closes the missing-board hazard. It only removes eviction by NON-OPEN runs. A
  third OPEN-class run can still replace the pending GitHub fallback:
  1. CF OPEN A is running.
  2. GH fallback B queues pending.
  3. `workflow_dispatch` C with `slot=OPEN` enters the same dedicated OPEN group.
  4. Default concurrency replaces pending B with C.
  5. A fails.
  6. C starts but fails closed on malformed OPEN/mode input.
  7. No fallback remains.
  8. Morning board is missed.
- **Violated invariant:** first-success / fallback availability.

**Minimum correction (per Sol):** Keep the owner-directed dedicated OPEN group,
but make its queuing semantics **non-evicting**. Preferred current GitHub
mechanism proposed by Sol:

```yaml
concurrency:
  group: <stable dedicated OPEN group>
  cancel-in-progress: false
  queue: max
```

Do not claim a trading-date-keyed concurrency group unless the workflow can
derive that key from allowed workflow-level contexts without introducing a new
date/input authority field. A fixed dedicated OPEN group is acceptable and
simpler if Stage-0 proves there is no legitimate cross-day overlap requirement.

Add falsification tests / structural assertions:
- **T25:** running CF OPEN + pending GH fallback + third valid OPEN → fallback is
  not canceled/replaced.
- **T26:** running CF OPEN + pending GH fallback + malformed `slot=OPEN` dispatch
  → malformed dispatch cannot remove the valid fallback.
- **T27:** multiple duplicate CF OPEN dispatches → they serialize without evicting
  the fallback; first completed successful OPEN still satisfies the slot.

**Ordering bind:** slot/mode validation MUST occur before the first-success
SATISFIED no-op decision can turn a malformed invocation into a successful no-op.

**Scope of verdict:** "No other packet authority/truth findings require
correction from this review."

## Next step (GOV-2 §7)

After one bounded C5 correction, the new exact full corrected SHA returns to THIS
independent Sol review seat for the **EXACT-CORRECTED-HEAD CONFIRMATION** (the
second GOV-2 packet-cycle event), which verifies every prior required finding is
correctly dispositioned and no new load-bearing defect was introduced. Only then
does the standing design-direction ruling become effective.

---

Author disposition of C5 is recorded in the packet (§7.4, §14-D2, §14 item 13,
§11 T25–T27, §22). This file is the durable INITIAL PACKET REVIEW record; the
EXACT-CORRECTED-HEAD CONFIRMATION record is appended below.

---

# EXACT-CORRECTED-HEAD CONFIRMATION (GOV-2 §7)

## GOV-2 durable record

- **Event type:** `EXACT-CORRECTED-HEAD CONFIRMATION` (GOV-2 §7 packet-cycle
  event 2 of 2).
- **Reviewer identity / capability role:** GPT-5.6 **Sol** / independent
  fresh-context — the SAME independent seat as the INITIAL PACKET REVIEW; not the
  author, not a subagent spawned by the authoring session.
- **Corrected exact SHA:** `46963f7f5de6e757c7ccbabc1ca7ff0d76c728d8` (v0.4).
- **Confirmation date:** 2026-08-11.
- **Prior finding confirmed:** C5 — **CONFIRMED CORRECTED.**
- **Verdict:** **ACCEPT** — "PACKET REVIEW CLEAN — PROCEED TO STAGE-0."

## Verified corrections (as recorded by Sol)

1. Non-evicting queuing is now a binding OPEN concurrency invariant — a later
   OPEN-class enqueue may not cancel/replace the pending fallback.
2. Dedicated OPEN concurrency uses a fixed group rather than a new
   trading-date/input authority field.
3. Slot/mode validation is ordered before the first-success no-op decision,
   preventing malformed OPEN input from becoming a successful satisfying no-op.
4. T25 / T26 / T27 explicitly falsify third-valid-OPEN, malformed-OPEN, and
   duplicate-CF-OPEN eviction.
5. Failure to find a full-non-eviction mechanism is an explicit RED/owner-return
   condition, not an accepted residual hazard.
6. **Native mechanism independently confirmed by Sol against current GitHub
   Actions documentation:**
   `concurrency: { group: <fixed dedicated OPEN group>, queue: max }`, with the
   documented restriction that `queue: max` must NOT be combined with
   `cancel-in-progress: true`. This resolves the packet's §7.4 Stage-0 mechanism
   pin to decision-tree **branch 1** (native support exists → use it); the
   validity-routed group expression is no longer needed as a fallback.

"No new load-bearing authority, truth, state, security, or scope defect was
introduced by the bounded C5 correction."

## Effect

The GOV-2 §2/§7 packet-review cycle is COMPLETE and the packet is REVIEW-CLEAN at
`46963f7`. Under the standing owner pre-authorizations (packet §16), the
design-direction ruling is automatically effective. **PROCEED TO STAGE-0.**
