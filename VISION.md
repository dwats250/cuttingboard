# Vision

Cuttingboard is a personal pre-market decision-support tool for one
discretionary options trader. Each session it compresses top-down market
structure into one disciplined read - what the environment is, what matters
today, whether it is tradable, and what would invalidate the thesis - so the
day's trading decisions are structured and conditional rather than reactive. It
exists to repair the part that fails first: not the signal, but the discipline
around acting on it. Success is a read trustworthy enough to act on
consistently, with every gate traceable to one of those four questions. It is
explicitly not a trading bot: no execution automation, no backtesting, no ML, no
multi-agent orchestration, no HFT. A human stays at every seam.

## The four questions

Everything the system computes serves one of four questions, asked in order each
session:

1. **What environment are we in?** The market regime and its posture - whether
   conditions favor risk, demand caution, or are disordered enough to stand
   aside.
2. **What matters today?** The macro and event context that should frame the
   day - what is driving the tape and what is on the calendar.
3. **Is this actually tradable?** Whether a candidate clears the discipline
   gates and sizes to a real position, or whether the honest answer is no trade.
4. **What would invalidate this?** Where the thesis breaks - the invalidation
   level and the exit - and the conditions under which the environment itself
   voids any trade.

Under the fourth question, **extreme market stress is a hard invalidation.** A
volatility spike or an outsized index move means the environment, not the setup,
is the story, and the system treats it as a stop rather than a signal. The
concrete kill-switch thresholds and the terminal HALT they force are recorded in
`docs/system_logic_map.md`.

## What Cuttingboard is not, and will not become

- Not an automated execution engine
- Not a backtesting framework
- Not a machine-learning system
- Not a multi-agent orchestration platform
- Not a generalized financial operating system
- Not a high-frequency signal factory
- Not a regulated-infrastructure project requiring aircraft-grade process

The system is built by one person, for one person's trading, on a part-time
schedule. Scope decisions reflect that reality.

## Operating principles

- **Description, not prediction.** Features that explain or contextualize the
  present are welcome. Features that forecast are not.
- **Read-only sidecars by default.** New observational features extend through
  sidecars rather than mutating the decision contract.
- **Cuts before additions.** Before adding a feature, the system must justify
  the features it already has. Anything not earning its keep gets removed.
- **The system serves the trader.** If a feature exists but does not change a
  decision, it should not exist.
- **The system must match its documentation.** When code and documented intent
  diverge, the divergence is resolved explicitly - by changing one or the
  other - never left to drift. Silent drift is the failure mode that produced
  sprawl.
- **Acknowledged debt carries a re-evaluation date.** Open-ended deferral is
  drift dressed as discipline; `docs/PROJECT_STATE.md` names the date each known
  debt is re-examined.

## The trap to watch for

The strongest thing Cuttingboard has built is environmental awareness. The
weakest is the loop from awareness to changed behavior. The main failure mode
going forward is producing better and better explanations of markets without
producing fewer trading mistakes. Every proposed feature is measured against one
question: does this change what I will actually do, or does it just help me feel
more informed about what I might do? The second is intellectual comfort dressed
as progress.

---

The operating model - roles, review gates, scope discipline - lives in
`CLAUDE.md`. Current state, active work, the test baseline, and known debt live
in `docs/PROJECT_STATE.md`. Decisions and their rationale live in
`docs/DECISIONS.md`.
