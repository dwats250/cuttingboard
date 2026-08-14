# Independent MATERIAL Packet Review — PRD-304 Manageability Lock

## Initial review

**Reviewed SHA:** `835503631d46dce087db6a4fb68c7574f27e50f0`

**Verdict:** DESIGN-INCOMPLETE

The reviewer confirmed the fail-closed default, exact-once carrier model,
invalid-value non-disclosure, halt precedence, and MATERIAL / EXECUTION /
HIGH-RISK classification. It found six boundary omissions:

1. **HIGH:** qualification-only formatters can emit candidate-independent
   directional/action language after candidate lists are emptied; the owning
   notification modules were outside FILES.
2. **HIGH:** analytical and actionable meanings of `qualified_count` differ
   across contract, daily run, hourly run, dashboard, and postmarket report and
   lacked an artifact-by-artifact contract.
3. **HIGH:** `system_state.tradable` is analytical today but notification state,
   CLI delivery, and reports interpret it as permission; locked semantics needed
   an owner choice and complete consumer disposition.
4. **MEDIUM:** `dashboard_preview.yml` runs the real hourly/render path but was
   omitted from the carrier/proof boundary.
5. **MEDIUM:** a code revert makes the environment lock inert, so operational
   safe hold and software rollback needed separate contracts.
6. **MEDIUM:** test paths were categorical and the eight-file estimate/380
   ceiling could not be reviewed against the incomplete consumer boundary.

**Initial FILES/ceiling verdict:** incomplete; estimate and ceiling not
ratifiable. **Ready for owner ruling:** no. **Implementation/Stage 0:**
unauthorized.

## Consolidated correction disposition

- F1 ACTIONED: dedicated locked notification projection with exact allowed and
  forbidden language; notification owners added.
- F2 ACTIONED: per-artifact analytical/actionable count truth table; postmarket
  language owner added.
- F3 ACTIONED: `tradable` remains analytical; locked permission takes precedence
  in notification state/dedup, CLI delivery, and reports; all owners added.
- F4 ACTIONED: dashboard preview receives the same repository-variable relay and
  is included in FILES/proof.
- F5 ACTIONED: operational safe hold separated from code rollback; revert
  requires availability restoration or owner-disabled schedules/delivery.
- F6 ACTIONED: exact test paths listed; complete fifteen-file production/
  workflow surface re-estimated at 410–540 with proposed 600 ceiling.

Fresh exact-corrected-head confirmation follows below.

## Exact-corrected-head confirmation

**Confirmed SHA:** `2ec8071703dccd45b8b71b44b3c3254e3361c103`

**Verdict:** CONFIRMATION ACCEPT

F1–F6 are ADDRESSED. The confirmer found no new material boundary omission.
The fifteen production/workflow files and eleven exact test files are complete;
the 410–540 estimate and proposed 600 additions ceiling are ratifiable as a
design boundary but are not yet authorized. The packet is ready for Dustin's
design-direction ruling. Stage 0, repository-variable activation,
implementation, Gate A, and merge remain unauthorized.
