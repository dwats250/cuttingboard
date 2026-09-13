GOV-2 INITIAL PACKET REVIEW -- PRD-339 COMPLETENESS-BY-CONSTRUCTION packet (gpt-5.6-sol)

Independent Codex reviewer, fresh context, read-only, no edits, no implementation. GOV-2
principle: no agent certifies the completeness of the boundary it chose. Owner has RULED the
method: REBUILD -- COMPLETENESS BY CONSTRUCTION. So the review question has CHANGED.

## Base
- Repo at the exact committed packet SHA. Confirm HEAD (git rev-parse HEAD) and report it.
- Packet under review: audits/prd-339-effective-permission-material-packet-2026-09/
  PRD_339_STRUCTURAL_AUTHORITY_PACKET_2026-09-12.md (read in full). It supersedes the
  enumeration framing; the prior inventory is reused as the migration/sink list.
- You MAY and SHOULD read source to test claims, esp: tests/test_runtime_layering.py,
  tests/test_dash_boundary.py (the existing AST-guard idiom), .github/workflows/ci.yml +
  drift_full_suite.yml, pyproject.toml (ruff), trade_decision.py (is_actionable_trade),
  the bypass sites market_map.py:489-509, dashboard_renderer.py:1875, market_control_card.py:42-54.

## The review question is NO LONGER "did you enumerate every consumer"
Do NOT try to enumerate every sink. The owner ruled that enumeration is not the completeness
proof. Instead, ATTACK THE MECHANISM'S SOUNDNESS. The claim to falsify is:

  "With a frozen EffectivePermission carrier whose module is the ONLY definer of the
   authoritative-action vocabulary + approved interface, and an AST/import-boundary pytest
   guard that fails if any other module defines/imports the vocabulary or emits the
   authoritative literals, a sink CANNOT validly emit authoritative action state without
   consuming canonical EffectivePermission -- and this holds for NEW/undiscovered sinks."

Try to break it:
1. BYPASS THE GUARD: can a Python sink still emit authoritative action WITHOUT importing the
   carrier and WITHOUT tripping the AST guard? Consider: f-strings/format assembling the
   verdict from fragments; computing the action from a proxy (grade, posture, tradable,
   candidate presence) and emitting a NON-literal-but-authoritative result; re-exporting the
   vocabulary; dynamic getattr/enum; deriving "actionable" numerically then mapping to words
   downstream. Name any concrete evasion the proposed guard (as described in s5) would miss,
   and whether it is closable by an AST guard or needs the lexical defense-in-depth or a data
   constraint.
2. THE AST GUARD ITSELF: is s5's guard actually implementable as described given the repo's
   AST-test idiom? Would it produce false positives (legitimate non-authoritative uses of the
   words, e.g. tests, docstrings, comments, the demoted evidence producers) or false negatives?
   Is the "authoritative vocabulary" precisely definable, or is the boundary between
   authoritative and analytical vocabulary ambiguous (a real risk)?
3. NON-PYTHON GAP: the guard covers Python. Are the s4/s5/Q9 controls for ui/app.js and the
   workflow commit message (carrier-provides-only-authoritative-field + companion checks)
   sufficient, or is there a residual bypass there?
4. THE CARRIER / RESOLVER: is resolve_effective_permission at runtime:1051 the right single
   origin? Does demoting the parallel origins (market_map if_now, _regime_to_permission_verb,
   _action_label, watch execution_posture, tradable) to evidence actually remove their
   authority, or does any of them still reach a sink authoritatively?
5. MIGRATION COMPLETENESS-AS-CI: is it TRUE that "the guard passing == migration complete"?
   i.e., would the guard actually fail today for each un-migrated sink? If any authoritative
   sink could pass the guard while still bypassing the carrier, say so (that is the crux).
6. Owner vs factual: are Q1/Q3/Q4/Q6/Q7/Q9/Q11 genuine owner choices? Any factual defect
   miscast as a choice? Is the estimate (s8) plausibly complete + labeled?

If you find a class of bypass the mechanism cannot structurally close, that is a REQUIRED
CHANGE to the mechanism (not a boundary reset of an enumeration -- the frame is now
structural). Only mark DESIGN INCOMPLETE if the structural approach itself is unsound as
described.

## Constraints
No edits. Read-only. Cite file:line. Distinguish traced from hypothesis.

## Return (end with exactly this)
EVENT: INITIAL PACKET REVIEW (STRUCTURAL)
REVIEWER: gpt-5.6-sol (Codex), fresh-context independent, run-isolated (cbagent transient
  unit, read-only sandbox, exact-SHA verified)
EXACT REVIEWED SHA: <SHA>
DATE: 2026-09-12
VERDICT: CLEAN | CLEAN WITH NITS | REQUIRED CHANGES | DESIGN INCOMPLETE (mechanism unsound)
FINDINGS: numbered; each with the concrete evasion/issue (file:line where relevant), and
  whether it is a mechanism gap (closable how), a factual defect, or an owner choice. (empty
  only if truthfully none)
STRUCTURAL COMPLETENESS SOUND: YES/NO (can a sink emit authoritative action without consuming
  EffectivePermission after this design? if YES, name the path)
