# 07 — VISION.md Currency Flags (Bridge to Part B)

Tensions where VISION.md and the code shape are not perfectly aligned.
Audit posture: surface, don't propose. Recommendations are deferred to
Part B.

Per audit brief format: principle in tension / code evidence / why VISION
might need revision / why code might need revision / recommendation
deferred.

---

## Flag 1 — Sidecar-without-consumer (watchlist_snapshot)

**Principle in tension.** "*The system serves the trader, not the other
way around. If a feature exists but Dustin doesn't actually use it to
make decisions, it shouldn't exist.*"

**Code evidence.** `watchlist_sidecar.py` produces
`logs/watchlist_snapshot.json` but per PROJECT_STATE.md PRD-135 milestone
review there is **no v1 consumer**. The renderer doesn't read it.
Notifications don't read it. Decision modules don't read it. It is
write-only governance from the system's standpoint.

**Why VISION might need revision.** Observability-without-immediate-use
might be a deliberate doctrine: writing a sidecar first, building a
consumer second is healthy if Phase 2 is going to need this snapshot for
the trade-evaluation sidecar. In that case, the principle could be
refined to *"every sidecar earns its keep within ≤ N PRDs of being
written"* rather than blanket "must be used now."

**Why code might need revision.** Alternatively: PRD-114 might have been
optimistic about adoption, and the sidecar should be deleted under the
*cuts-before-additions* rule.

**Recommendation deferred to Part B.**

---

## Flag 2 — Compatibility shims with no clear retirement path

**Principle in tension.** "*Cuts before additions. Before adding a
feature, the system should justify the features it already has. Anything
not earning its keep gets removed.*"

**Code evidence.**
- `sector_router.py` — three stub functions returning MIXED and
  pass-through tuples
  ([sector_router.py:35-50](cuttingboard/sector_router.py#L35-L50)).
- `universe.filter_execution_dict` / `filter_execution_items` /
  `log_universe_configuration` — no-op pass-throughs
  ([universe.py:20-37](cuttingboard/universe.py#L20-L37)).

Both exist to preserve runtime import surface. They are dead behavior
behind live shapes — exactly the failure mode the cleanup pass was meant
to surface.

**Why VISION might need revision.** It may be worth declaring an explicit
exemption: *"interface-preserving shims are permitted when the
alternative is a multi-file rename PR"* — which is the de facto reason
these survive.

**Why code might need revision.** Alternatively: bite the rename, delete
the shims, and update the runtime imports in one PRD.

**Recommendation deferred to Part B.**

---

## Flag 3 — runtime.py size vs. cuts-before-additions

**Principle in tension.** Same as Flag 2 plus the operating principle
that the system "match its documentation" — the monolith is officially
acknowledged but never shrinks.

**Code evidence.** ~2100 LOC, every notify-mode PRD widens it.
PROJECT_STATE.md and `docs/milestones/ENGINE_MILESTONE_2026-05-12.md`
both flag this debt. The refactor is gated by a "forcing function" that
hasn't arrived in 6 months.

**Why VISION might need revision.** Add an explicit codeword in
operating principles: *"acknowledged debt is permissible if and only if
PROJECT_STATE.md names the forcing function and the date by which it
must be re-evaluated"*. Right now the deferral is open-ended.

**Why code might need revision.** Alternatively: schedule the refactor
PRD even without a forcing function. The PRD-135 milestone already
provides the scoping reference.

**Recommendation deferred to Part B.**

---

## Flag 4 — Phase 2 wording vs. evaluation.py reality

**Principle in tension.** Documentation currency.

**Code evidence.** VISION.md Phase 2 reads "*Trade evaluation sidecar.
PRD, then build. Read-only consumer of the existing L10 audit output,
joined to imported Moomoo trade statements.*" — but `evaluation.py` and
`performance_engine.py` already implement a same-session evaluation loop
against forward 1-minute bars
([evaluation.py:1-7](cuttingboard/evaluation.py#L1-L7),
[performance_engine.py:1-5](cuttingboard/performance_engine.py#L1-L5)).
The Moomoo-joined version doesn't exist yet, but a substantial chunk of
the Phase 2 scope is functionally already present.

**Why VISION might need revision.** Phase 2 should be re-scoped to
explicitly read *"Moomoo-integration extension of the existing
same-session evaluation loop"* — accurate framing of what's left.

**Why code might need revision.** Alternatively: `evaluation.py` could be
the wrong shape for Phase 2's intent, and we should plan to replace
rather than extend it. (No evidence this is the case, but the audit
brief asks for both sides.)

**Recommendation deferred to Part B.**

---

## Flag 5 — `market_map_lifecycle.py` cross-run carry not in doctrine

**Principle in tension.** *"The system must match its documentation."*

**Code evidence.** `market_map_lifecycle.inject_lifecycle` backfills
`current_price` from the previous market_map snapshot when current is
None ([market_map_lifecycle.py:82-85](cuttingboard/market_map_lifecycle.py#L82-L85)).
`docs/sidecar_doctrine.md` is not known to call this out (verified by
absence of `current_price` references during this audit; full review
deferred to Part B).

**Why VISION might need revision.** Probably not — this is a doctrine-doc
gap, not a vision-doc gap.

**Why code might need revision.** Either document the carry in
`sidecar_doctrine.md` or remove the backfill and let renderers handle
None explicitly.

**Recommendation deferred to Part B.**

---

## Flag 6 — No active "in flight" work

**Principle in tension.** None directly — this is a pacing observation
rather than a tension.

**Code evidence.** VISION.md `In flight: none.` PROJECT_STATE.md
`Active PRD: none. Deferred PRD: none.` This is healthy state, not drift.
Worth flagging only because the architectural-alignment audit (Phase 1
step 4) is itself the next step, and after it Phase 2 PRD authoring
begins — at which point Flag 4 becomes load-bearing.

**Recommendation deferred to Part B.**

---

## Headline

Six tensions surfaced. None are violations; all are recommendations to
either tighten VISION.md wording, retire shim code, document quiet
behavior, or rescope Phase 2 framing. Part B should review and decide
each.
