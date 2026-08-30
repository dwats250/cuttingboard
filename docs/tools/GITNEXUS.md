# GitNexus - optional code-intelligence tooling

Opt-in reference. GitNexus is a code-intelligence index available through its
MCP tools when it helps understand code, assess blast radius, or navigate the
call graph. It is NOT standing Cuttingboard authority and issues no universal
mandate; nothing here overrides `CLAUDE.md`, `AGENTS.md`, or the mode contracts.
Relocated here from a former root-`AGENTS.md` block (2026-08-29) so it loads only
when an agent chooses to use it.

Caveat before relying on it: the registered index has pointed at temporary
worktrees rather than the working checkout, so treat its results as advisory and
confirm repo truth against the actual files (and `docs/SCHEMA_MAP.md` /
`docs/CALL_SITE_MAP.md`, the repo's own recon cache) before acting. If a tool
warns the index is stale, run `npx gitnexus analyze` first.

## When it is useful

- Impact / blast radius before a risky edit:
  `gitnexus_impact({target: "symbolName", direction: "upstream"})` reports
  direct callers, affected processes, and a risk level. Prefer it over a blind
  find-and-replace, and surface HIGH/CRITICAL risk to the user.
- Change scope check before committing: `gitnexus_detect_changes()` shows which
  symbols and flows a change actually touches.
- Exploring unfamiliar code: `gitnexus_query({query: "concept"})` returns
  process-grouped execution flows; `gitnexus_context({name: "symbolName"})`
  returns callers, callees, and participating flows for one symbol.
- Safe rename: `gitnexus_rename` understands the call graph.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/cuttingboard/context` | codebase overview, index freshness |
| `gitnexus://repo/cuttingboard/clusters` | functional areas |
| `gitnexus://repo/cuttingboard/processes` | execution flows |
| `gitnexus://repo/cuttingboard/process/{name}` | step-by-step execution trace |

These are conveniences. The maps in `docs/` and the source itself remain the
authoritative surfaces for any decision.
