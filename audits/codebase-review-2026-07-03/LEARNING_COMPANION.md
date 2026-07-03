# Learning Companion — from operator to engineer

Companion to `MASTER_PLAN.md` (the rails) and `mentor-review.md` (the reference).
This file is about YOU, not the repo. It codifies the concepts the review said
you're shaky on, using your own codebase as the textbook.

---

## Who this is written for (your actual starting point)

You didn't start from zero. Fifteen years of Linux command-line use is a real
foundation, and it explains the exact shape of your skills:

**What you already have (and it shows in the repo):**
- **Ops instinct.** `set -euo pipefail` in every script, fail-loud HALT
  notifications, freshness gates before publishing — that's an operator's
  nervous system, and most career programmers never develop it.
- **Pipeline thinking.** You've piped commands for 15 years. Your system is
  literally a pipeline (ingestion → normalization → … → output). That mental
  model transferred perfectly.
- **Tool skepticism.** "Assert the resolved, not the requested" (PRD-198) is
  the instinct of someone who's been burned by a command that exited 0 and
  did nothing. That's earned knowledge.

**What 15 years of shell does NOT teach (and it also shows):**
- Shell scripts grow *linearly* — add a line, it runs after the last one.
  Software systems grow *combinatorially* — add a field, and every reader of
  that field is now a place it can break. This is THE conceptual jump, and
  it's why the review's findings cluster at the untyped contract boundary:
  that's the part of your system that still behaves like a shell pipeline
  (loose text/dicts flowing between stages) instead of a program (typed
  values with checked shapes).
- In shell, "it printed the right thing" is verification. In systems, the
  question is "what *guarantees* it stays right when I change something a
  year from now?" — types, tests, and single-source-of-truth are the answers,
  and all three are the concepts below.

So the arc of this document: **convert operator instincts into engineering
judgment.** You're not learning to code. You're learning to see structure.

---

## How to use this file

- Each concept below is one sitting (15–25 min). One concept per sitting, max.
- Every concept has the same four parts:
  **THE IDEA** (plain words) → **IN YOUR REPO** (real file, real line) →
  **DO THIS** (a concrete exercise) → **YOU'VE GOT IT WHEN** (observable).
- The concepts are ordered to pair with the MASTER_PLAN weekly module reads.
  When the plan says "read `contract.py`," do Concept 1 the same week.
- Log one sentence per concept in the log at the bottom, dated. Same rule as
  the module-read log: bad sentences count, absent ones don't.

---

## Concept 1 — Types are contracts, and your repo has both halves

**THE IDEA.** A type says "this value has exactly this shape, checked by the
machine." A dict says "trust me." Both work on day 1. They differ on day 300,
when you've forgotten the shape and the machine either reminds you (typed) or
lets you ship a typo (dict).

**IN YOUR REPO.** You have a perfect A/B experiment running:
- Typed half: `cuttingboard/regime.py` — `RegimeState` is a frozen dataclass.
  Misspell a field and Python raises immediately, at the line you typed it.
- Untyped half: `cuttingboard/contract.py:62` builds `dict[str, Any]`.
  Misspell a key and you get `None`, silently, somewhere downstream, later.
- The tell: you had to write `docs/SCHEMA_MAP.md` — a hand-maintained list of
  the dict's keys. **That document is a type definition you're maintaining by
  hand, without machine checking.** Typed code doesn't need it.

**DO THIS.** In a scratch Python session:
```python
from cuttingboard.regime import RegimeState
RegimeState(regime="EXPANSION", postur="RISK_ON")   # typo on purpose
```
Watch it fail instantly and loudly. Then look at `payload.py` and find three
`.get("...")` calls; ask yourself what happens if that key were misspelled at
the *write* site. (Answer: nothing — until the dashboard renders wrong.)

**YOU'VE GOT IT WHEN** you can say in your own words why SCHEMA_MAP.md exists,
and why Wave 3's PRD-J makes most of it unnecessary.

---

## Concept 2 — Immutability: why your upstream is frozen

**THE IDEA.** `frozen=True` means a value cannot be changed after creation —
only *replaced* with a modified copy. Why care? Because the alternative is
that anyone holding a reference can change it, and then "who set this field?"
becomes an archaeology project. Immutable values make data flow *traceable*:
if you have the object, you know it looks exactly like it did when it was
built.

**IN YOUR REPO.**
- The pattern done right: `flow.py:138` — the flow downgrade doesn't edit the
  qualification result; it calls `replace()` to make a new one. One line, and
  the original is still intact for anyone else who saw it.
- The pattern done wrong: `runtime/__init__.py:902-952` — the contract dict
  gets edited in place, after construction, from scattered lines
  (`contract["outcome"] = ...`, `contract["system_state"]["permission"] = ...`).
  To know what a "contract" contains, you have to read every line that ever
  touched it.

**DO THIS.** Grep it yourself: `rg 'contract\[' cuttingboard/runtime/__init__.py`.
Count the mutation sites. That count is the number of places you'd have to
check to answer "what's in the contract?" — versus ONE place if it were built
complete and frozen.

**YOU'VE GOT IT WHEN** the phrase "mutated in place across a boundary" makes
you slightly uncomfortable, the way an unquoted shell variable does.

---

## Concept 3 — Fail-open vs fail-closed (the safety-tool question)

**THE IDEA.** When data is *missing*, every check has to pick a default: pass
(fail-open) or block (fail-closed). Neither is always right — but for a
*discipline* tool, a gate that silently passes on missing data is a gate that
disappears exactly when the data source has a bad morning.

**IN YOUR REPO.**
- Fail-closed, done right: `qualification._is_late_session` (`:854`) — can't
  determine the time? Block the entry. The comment even says so.
- Fail-open, dangerous: `output.py:305-312` — a symbol missing from
  chain_results renders as VALIDATED. Gates 9/10 (`qualification.py:427,444`)
  pass on missing data. A yfinance outage makes your system *more* permissive.
- Your ops layer already knows this: `hourly_alert.yml:106-125` refuses to
  publish without a freshness proof. The instinct exists — it just wasn't
  applied inside the qualification path.

**DO THIS.** MASTER_PLAN PRDs B and C fix these. Before the agent implements,
predict on paper what each fix's red test will assert. Compare after.

**YOU'VE GOT IT WHEN** every time you see a `.get(key, default)` you reflexively
ask: "and is *default* the safe direction here?"

---

## Concept 4 — The seam: bugs live where the types stop

**THE IDEA.** Every codebase has a line where discipline hands off to
convention — typed→untyped, validated→trusted, tested→assumed. Defects
cluster there, because that's where the machine stops checking and humans
(or agents) start remembering. Skilled readers find that seam FIRST.

**IN YOUR REPO.** The seam is precisely `PipelineResult` (frozen, typed,
`runtime/_types.py:54`) → `build_pipeline_output_contract` (dict,
`contract.py:62`). Nearly every bug in the review's list sits at or after
that line: the unclosed validator, the injected keys, the fail-open renders,
the duplicated schema in payload.

**DO THIS.** Pick any repo you're curious about on GitHub. Spend 10 minutes
finding ONLY its seam — where do the types/checks stop? Don't read anything
else. This is the highest-leverage code-reading skill there is, and it's
trainable.

**YOU'VE GOT IT WHEN** "where does the checking stop?" is the first question
you ask of any system — including ones an agent just built for you.

---

## Concept 5 — Function size: the accretion trap

**THE IDEA.** No one writes a 451-line function. They write a 40-line function
that 30 people (or 30 agent sessions) each add 15 reasonable lines to. Size
is not a style problem — it's a *review* problem: a function nobody can hold
in their head is a function nobody actually reviews, only appends to.

**IN YOUR REPO.** `_run_pipeline` (`runtime/__init__.py:611-1061`) and
`render_dashboard_html` (`dashboard_renderer.py:1785-2625`, 22 keyword
arguments). Both grew one PRD at a time, each addition locally sensible.
Nothing ever said stop — so the MASTER_PLAN adds a tripwire (function >80
lines → automatic debt entry).

**DO THIS.** Open `_run_pipeline`. Don't read it line by line — instead, write
down just the *stage names* in order as section headers (fetch, validate,
regime, …). You just produced the decomposition PRD-I will implement. That's
the whole skill: seeing the sections inside the monolith.

**YOU'VE GOT IT WHEN** a long function reads to you as a list of trapped
smaller functions, the way a long shell script reads as functions-waiting-
to-happen.

---

## Concept 6 — Duplication is future divergence

**THE IDEA.** Two copies of a value or rule are fine today — they agree. The
problem is the future edit that changes one and not the other. Nothing warns
you; the system just quietly starts disagreeing with itself. "Single source
of truth" isn't tidiness — it's making disagreement *impossible*.

**IN YOUR REPO.** `EXTENSION_ATR_MULTIPLIER = 1.5` in both `config.py:110`
and `market_map.py:112`. Today they agree. The first tuning session that
finds one of them breaks the agreement between your map's "extended" grade
and your qualification gate — silently. Same disease, milder: the macro-driver
schema written three times, `_iso()` twice, float-coercion four times.

**DO THIS.** You already know this concept from Linux — it's why config
belongs in ONE file, not exported in three dotfiles. The exercise is PRD-D's
personal check: after the fix, run
`rg "EXTENSION_ATR_MULTIPLIER\s*=" cuttingboard/` yourself and see exactly one
line. One command, total certainty — that's what single-sourcing buys.

**YOU'VE GOT IT WHEN** copy-pasting a constant or a validation block makes
your hands itch.

---

## Concept 7 — Tests are specifications you can execute

**THE IDEA.** A test's real job isn't catching today's bug — it's *pinning a
decision* so no future change (by you, or an agent) can silently unmake it.
Red-test-first isn't ritual: watching the test fail is the only proof the
test can detect the thing it claims to guard. A test you never saw fail is a
green light wired to nothing.

**IN YOUR REPO.** You largely have this one — your suite has zero can't-fail
tests, and `tests/test_gap_down_permission_integration.py:361` is a
masterclass: a `strict=True` xfail that documents a missing guard and will
*force* an update the day the guard lands. But see the gap: `confirmation.py`
has zero tests, which means every one of its decisions is currently unpinned —
an agent could invert `_crosses_level` tomorrow and nothing would object.

**DO THIS.** With PRD-F: before the agent writes `test_confirmation.py`, you
write (in English, in the PRD) the five behaviors that must be pinned. The
agent turns them into code. Specifying tests is the highest-leverage way you
personally steer agent work.

**YOU'VE GOT IT WHEN** "is there a test that would fail?" is your version of
"did you actually run it?"

---

## Concept 8 — Dependency injection vs monkey-patching

**THE IDEA.** When code needs a replaceable piece (a data source, a clock),
there are two moves: *pass the piece in* (injection — the seam is visible in
the function signature) or *reach into the module and swap it behind its
back* (patching — invisible, and it breaks when imports move). Patching is a
test-only emergency tool. In production code it's a booby trap.

**IN YOUR REPO.** `runtime/__init__.py:1538` — production fixture mode does
`unittest.mock.patch("cuttingboard.derived.fetch_ohlcv", ...)`. It works, but
notice what it depends on: the *string name of an import site*. Move that
import during any refactor and fixture mode silently breaks. Compare
`apply_execution_policy_to_decisions(..., overall_pressure=...)` — pressure
is *passed in*, so the dependency is visible in the signature and survives
any refactor.

**DO THIS.** Look at `_fixture_cache_only_ohlcv` (`runtime:1526`) and answer:
if someone renamed `derived.fetch_ohlcv`, which test would catch the
breakage? (Trick question — that's PRD-K's red test, which doesn't exist yet.)

**YOU'VE GOT IT WHEN** you can explain why "pass it in" beats "patch it" using
only the phrase "visible in the signature."

---

## Concept 9 — State: know where it lives and who can touch it

**THE IDEA.** Every bug is easier to find when you can answer, for each piece
of data: where is it born, who can change it, how long does it live? Local
variable < function argument < object field < module global < file on disk —
each step up that ladder means more possible writers and harder debugging.
Module globals are the shell equivalent of environment variables mutated by
sourced scripts: convenient, then haunted.

**IN YOUR REPO.**
- Ladder done right: cross-run state is *explicit files* with load/save pairs
  (`notifications/state.py`, execution-policy session state) — you can `cat`
  them. Very Linux, very good.
- Ladder violated: `output.py`'s notification dedup — `sent_message_hashes`,
  `_LAST_SEND_TS` are module globals, and the scope key mixes in
  `PYTEST_CURRENT_TEST` from the environment (`output.py:91-93`). Production
  send behavior now depends on whether a test framework is loaded. That's the
  haunted-env-var pattern.

**DO THIS.** `rg "^_[A-Z_]+ =|^[a-z_]+ = \{|^[a-z_]+ = \[" cuttingboard/output.py`
— list the module-level mutable names. For each, ask: who writes this, and
from how many places? PRD-L exists because of your answers.

**YOU'VE GOT IT WHEN** you instinctively flinch at a bare module-level `= {}`.

---

## Concept 10 — How to read a module (the method)

**THE IDEA.** Nobody reads code top-to-bottom like prose. The method:
1. Docstring + imports (what does it claim, what does it lean on?)
2. The data shapes — dataclasses/constants first. Data before logic, always.
3. The public entry points (what does the rest of the system call?)
4. ONE main path, end to end, ignoring branches.
5. Only then the edge branches — and now they'll make sense.
Time-boxed: 25 minutes gets you 80% of any module this size.

**IN YOUR REPO.** This is the weekly module-read habit from the MASTER_PLAN.
Use this exact sequence each time. For `contract.py`: docstring → the key
constants and `_OPTIONAL_MACRO_DRIVERS` → `build_pipeline_output_contract` →
follow one candidate through `_build_trade_candidates` → then the validator.

**DO THIS.** It's already scheduled — module-read list, MASTER_PLAN. This
concept just gives you the method so the reads have rails too.

**YOU'VE GOT IT WHEN** 25 minutes in an unfamiliar module leaves you able to
say what it does, what's ugliest, and what you'd change — the three-sentence
log, which is exactly why the log asks for those three.

---

## Concept 11 — Proportionality: ceremony budgets are engineering too

**THE IDEA.** Process is a tool with a cost, and sizing the ceremony to the
risk of the change is itself a core engineering skill — same muscle as sizing
a test suite or a type system. All-or-nothing process is how you end up with
115-line specs for CSS padding while a duplicated risk constant ships unread.

**IN YOUR REPO.** PRDs 213–225 vs the findings list in the review. The
ceremony went where the *volume* was (cosmetics), not where the *risk* was
(contract boundary). PRD-H in the plan is the fix; this concept is why it
matters beyond saved time.

**DO THIS.** For your next five changes, before opening anything, write one
line: "worst realistic outcome if this is wrong: ___" — and pick the lane
from that line alone. That sentence is the entire skill.

**YOU'VE GOT IT WHEN** "how wrong can this go?" — not "how big is the diff?" —
picks your lane.

---

## Concept 12 — What your Linux years gave you (use it on purpose)

Not a lesson — a map of transfers, so you lean on real strengths knowingly:

| Linux instinct | Engineering twin | Where it already shows |
|---|---|---|
| `set -euo pipefail` | Fail-loud doctrine | alert_runner HALT path |
| Pipes | Staged pipeline w/ typed hand-offs | the 10-layer design |
| "exit 0 lies" | Assert the resolved, not the requested | PRD-198 invariant 2 |
| One config file, not three | Single source of truth | Concept 6 (PRD-D) |
| `cron` + logs | Scheduled workflows + audit.jsonl | hourly_alert, audit.py |
| Quoting variables | Escaping output | `_esc()` in the renderer |
| Reading man pages | Reading source (Concept 10) | the weekly habit |

And the two places shell instinct actively misleads:
1. **"Text between stages is fine."** In shell, yes. In a system, untyped
   text/dicts between stages is the seam where bugs live (Concept 4).
2. **"It ran clean, ship it."** Shell scripts are done when they run. Systems
   are done when a *check that can fail* says so, forever (Concept 7).

---

## Milestones — how you'll know you're leveling up

- **M1:** You catch something in an agent's diff that its own summary didn't
  mention. (First time this happens, note the date below. It's a big day.)
- **M2:** During a module read you find a defect the 2026-07-03 review missed.
  It exists — reviews always miss things.
- **M3:** You correctly predict a fresh review's top finding before reading it.
- **M4:** You write a PRD's red-test spec and the agent's implementation
  passes it unchanged on the first try — meaning your specification, not the
  agent's judgment, carried the correctness.
- **M5:** You downsize a ceremony on purpose, in writing, and it was right.

## Concept log
(One dated sentence per concept, your own words. Milestones too.)

-
