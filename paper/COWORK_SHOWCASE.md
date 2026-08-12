# Showcasing Claude Cowork in the Backtester — material for the paper

This note enumerates concrete ways the backtester app demonstrates what Claude
Cowork adds *on top of* the DisSysLab framework. The framing question for the
paper: **a first-year student, or a non-programmer domain expert, sits down with a
running distributed office and speaks to it in English. What can they now do that
they could not do with the code alone?**

The examples below are grouped into six modes. Modes A–C are the three the user
asked about directly (interrogating results, generating/modifying offices,
debugging). Modes D–F are additional showcase angles. Each item is written so it
can be lifted more or less directly into the paper, and each is grounded in what
this specific app already produces (walk-forward, Monte Carlo, transaction costs,
strategy correlation, per-stock detail).

A useful organizing claim for the paper: **the office is the artifact of record;
Cowork is the interface to it.** DisSysLab gives you a running distributed system
of agents (sources, signal computers, backtesters, a gate, a comparator, sinks);
Cowork lets a non-programmer read that system, reshape it, and repair it —
entirely in conversation — without ever seeing the wiring. The three modes below
map to the three things you do with any instrument: *read it, retune it, fix it.*

---

## A. Interrogating the results in English

The report (`report.html`) is already rich, but a static report answers only the
questions its author anticipated. The showcase is that a tester can ask questions
the report's author never hard-coded, and get an answer computed or explained from
*their own run's data*. Three sub-categories:

**A1. Explaining what a number means (pedagogy).** The audience knows markets, or
knows Python, but not necessarily both — and knows nothing about distributed
systems. Cowork closes that gap on demand:

- "What is a Sharpe ratio, and why is the walk-forward one lower than the
  full-window one for this strategy?"
- "You keep saying 'out-of-sample.' Explain it using my results."
- "What does the correlation table tell me that the returns table doesn't?"
- (DisSysLab-facing) "What is a checkpoint here, and what got checkpointed during
  this run?" / "This ran as several agents passing messages — draw me the pipeline
  that produced this report."

The paper point: *the same substrate teaches the framework and the domain.* A
first-year student asking "what's a checkpoint?" and a trader asking "what's
out-of-sample?" are served by one system.

**A2. Re-analyzing the run without re-running it.** The run already emitted rich
per-ticker data (returns, dates, days-in-market, turnover, per-variant stats,
a correlation matrix). Cowork can slice it in ways the report didn't lay out:

- "Rank the strategies by return *after* transaction costs, not before."
- "Which single stock contributed most of the winning strategy's return? Is the
  edge broad or is it one lucky name?"
- "Show me only the strategies whose out-of-sample Sharpe stayed positive in every
  fold."
- "How much of the time was the best strategy actually holding anything? What did
  it earn per day *in* the market?"
- "Turn the Monte Carlo section into one sentence I could say to a skeptic."

The paper point: *a conversational layer over a structured message turns one
report into an open-ended analytics session.* No new office is needed — the data
is already in hand; Cowork is doing the last-mile analysis a human analyst would.

**A3. Stress-testing trust (the honest-advisor angle).** This is the most
distinctive and worth foregrounding in the paper:

- "Is this result too good to be true? What would make you doubt it?"
- "If I were going to fool myself with this backtest, how would I do it — and did
  we?"
- "Will this strategy make money next year?" — a *good* answer declines to promise.
- "What's the single biggest weakness of the best-looking strategy here?"

The paper point: Cowork can be prompted to argue *against* the result, which is
exactly the discipline backtesting demands and exactly what a naive user lacks.
The tool doesn't just compute; it can supply the skepticism.

---

## B. Building and modifying offices in English

DisSysLab offices are defined in an `office.md` file (English-like declarations of
sources, agents, and wiring) plus small Python role files under `roles/`. The
showcase is that a non-programmer can commission changes to that office
conversationally, and Cowork edits the office files. Ordered from lightest to
heaviest:

**B1. Retune an existing office (parameter changes).**

- "Change the basket to the FAANG stocks instead of the current five."
- "Use a 50-day and a 200-day moving average instead of the current speeds."
- "Set transaction costs to 10 basis points and re-run — how much does that change
  the ranking?"
- "Give me more Monte Carlo samples for a tighter robustness band" / "skip the
  Monte Carlo this time — just run the fast walk-forward." *(The default
  `validation_gate` runs BOTH validations in one pass, so this is not a swap but a
  single-kwarg dial on one line of `office.md` — `validation_gate(n_samples=500)`
  or `validation_gate(monte_carlo=False)`. A plain-English request maps to a bounded,
  safe edit while the rest of the office is untouched; one sentence, one kwarg, a
  visibly different robustness band.)*

**B2. Add a new strategy to the office (new role, existing pipeline).** The app was
deliberately built with a reuse contract: every strategy is one
`compute_variant_signal(bars, params[, context])` function; everything downstream
(backtester, join, evaluator, comparator, sinks) is shared. So:

- "Add a Bollinger-band strategy: buy when price closes below the lower band,
  sell above the upper."
- "Add a strategy that only holds a stock while it's above *both* its 50- and
  200-day averages."
- "Add a relative-strength strategy that also requires the whole market to be
  trending up." *(The market-context agent already exists and publishes a
  cross-sectional benchmark and momentum rank; a new role just consumes it.)*

The paper point: *because the office has a clean seam, the natural-language request
maps to a bounded, safe edit* — Cowork writes one role file and adds a couple of
lines to `office.md`; it does not have to touch the trust machinery. This is a
strong argument that good framework design and conversational authoring reinforce
each other: **the cleaner the seam in the office, the smaller and safer the edit
Cowork has to make.**

**B3. Generate an adjacent office from scratch.** The same building blocks
(a source, signal computers, a gate, a comparator, sinks) recompose into new apps.
Prompts that would showcase this:

- "Build me a *screening* office: instead of backtesting, just rank today's basket
  by momentum and print the top three."
- "Build a *regime* office that reports, for each year, which strategy would have
  won — so I can see if the best approach changes over time."
- "Make a version that emails me the report instead of writing an HTML file."
  *(A new sink; the pipeline is untouched.)*

The paper point: the unit of reuse is the *role/agent*, and Cowork is fluent in
recombining roles. A student who has one working office effectively has a kit.

---

## C. Debugging and repair in English

Real runs fail — a data file is missing, a stock has a shorter history than the
others, a package isn't installed. In the traditional workflow, a stack trace ends
the session for a non-programmer. The showcase is that the error becomes the start
of a conversation:

- "I got `EVAL: list index out of range` — what does that mean and can you fix
  it?" *(This is a real bug we hit: Palantir's shorter history broke a
  position-indexed portfolio calculation. The fix — aligning by date — is exactly
  the kind of thing a non-programmer cannot do but can *ask for*.)*
- "The report says 'no trades' for one strategy — is that a bug or did the rule
  just never fire?"
- "It says it can't find the data files. What do I do?"
- "Something looks off in the Tesla numbers — can you check whether the data for
  that stock is clean?"

The paper point: **the framework's failure modes are converted from dead-ends into
dialogue.** For the teaching audience this is decisive — a first-year's error is no
longer a wall. It also demonstrates that Cowork can operate on the *code and data
of the running system*, not just chat about it.

---

## D. Beyond a single run — operating the office over time

Modes A–C are all one-session. Cowork's reach also extends to *operating* the app
as an ongoing thing, which is worth a short paper section because it's the part
that most exceeds a static tool:

- **Scheduling.** "Re-run this every Monday morning with fresh data and send me the
  report." A recurring scheduled task turns a one-off backtest into a standing
  monitor — no code, no cron literacy.
- **Comparison over time.** "Compare this week's walk-forward ranking to last
  week's — did the best strategy change?" (Cowork keeps and diffs artifacts.)
- **Narrated deliverables.** "Write a one-page memo for a non-technical partner
  explaining what we found and what we're *not* claiming." The office produces
  numbers; Cowork produces the human-readable, appropriately-hedged write-up.
- **Data hygiene.** "Before the next run, check each CSV for gaps or obviously bad
  prices and tell me what you'd throw out." The domain expert supervises data
  quality in English.

The paper point: Cowork spans the whole lifecycle — author, run, schedule,
compare, report — that normally requires several tools and a programmer to stitch
together.

---

## E. The disclosure-and-correction loop as a trust mechanism

Worth its own paragraph in the paper because it's a *design pattern*, not just a
feature. The app is built so that when a user describes a strategy, Cowork replies
with an explicit **"here's what I assumed you meant"** list before running —
naming every choice it filled in (which average, how fast, what "strongest"
means). The user corrects it in words; the correction takes effect on the next run.

Why this matters for the paper's thesis: the central risk in letting a
non-programmer drive a quantitative tool is the **silent mismatch** — the tool does
something subtly different from what the user intended, and the user never knows.
The disclosure loop attacks exactly that. It makes the tool's interpretation
*legible and contestable* before any result is trusted. This is a generalizable
claim: **conversational scientific tools should surface their assumptions as a
first-class step, not bury them in defaults.** The backtester is a clean case study
because a wrong assumption produces a plausible-looking wrong number — the most
dangerous kind.

---

## F. Generated artifacts as evidence

For the paper's figures and appendix, the tangible outputs a tester produces are
themselves the argument. Candidates to include:

- The `report.html` from a tester-authored strategy (shows the domain expert
  reached a real result).
- A **transcript** of the English session that produced it (shows the *path* — the
  vague first ask, the assumption disclosure, the correction, the run). This is the
  single most persuasive artifact: it makes the "no code was written by the user"
  claim visible.
- A **git diff** of the office files Cowork changed in response to an English
  request (shows the mapping from sentence → bounded, safe code edit).
- A before/after of the Monte Carlo robustness bands when Vikram asks for more
  samples (or of the report with one half turned off) — one kwarg changed in
  `office.md`, a visibly different result.

The paper point: every claim about accessibility is backed by an artifact a
skeptical reviewer can inspect — the report, the transcript, the diff.

---

## Suggested framing sentence for the paper

> DisSysLab lets a student *build* a distributed office; Cowork lets a
> non-programmer *read it, retune it, repair it, and operate it* — in English,
> without seeing the wiring — while a disclosure-and-correction loop keeps the
> system's interpretation of their intent legible and contestable at every step.
