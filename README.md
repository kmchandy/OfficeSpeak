# OfficeSpeak

Build a small, always-on team of software workers — an **office** — by
**describing what you want in plain English**. No programming needed to try
it. An assistant (Claude, set up with OfficeSpeak's instructions) turns your
description into a team of workers that pass messages to each other, explains
the team back to you, and lets you correct it in plain English. Information
comes in through **sources** and results go out through **sinks**. OfficeSpeak
runs on the [DisSysLab](https://github.com/kmchandy/DisSysLab) runtime.

**New here?** See [the OfficeSpeak site](https://kmchandy.github.io/OfficeSpeak/)
for an overview of what's already built, or jump straight to the two-minute
visual walkthroughs:
[`stage1_microcourse.html`](https://kmchandy.github.io/OfficeSpeak/stage1_microcourse.html)
(Stage 1) and
[`stage2_microcourse.html`](https://kmchandy.github.io/OfficeSpeak/stage2_microcourse.html)
(Stage 2) — click any of these, no install and nothing to download, they open
straight in your browser.

This page assumes **no computer background at all** — if you've never opened
a "terminal" or typed a "command" before, every one of those words gets
explained the first time it shows up.

There are two stages, and it's normal to stop after the first:

- **Stage 1 — Describe it (no installation).** Everything happens in a
  conversation with an assistant on claude.ai. No Python, no terminal. This is
  the most important part to try, and anyone can do it.
- **Stage 2 — Run it for real (needs a computer with Python).** Turning your
  description into an actually-running system. This is usually a second step,
  sometimes done by the same person after learning a little Python, sometimes
  by asking someone else. **Right now, that "someone else" can just be us** —
  send us what Stage 1 produces and we'll run it for you. You don't need to
  learn anything technical to get to see your office actually work.

If setting up Python isn't for you, **just do Stage 1** — that's the heart of
it, and it's the same experience whether or not anyone ever runs what you
build.

The point of trying this is to find out whether *you* can go from an English
description to an office you understand and trust — and to tell us every place
it's confusing. Rough edges are exactly what we're looking for; if something
is unclear, that's a bug in our design, not yours.

## What's already built (so you know before you start)

This page walks through one story so you can see the whole path clearly, but
it's not the only thing here — there's real, substantial groundwork behind it
already:

- **33 example offices run end to end today** (24 apps + 9 examples in
  DisSysLab's gallery) — news and market monitoring, a wardrobe assistant
  that checks your calendar and the weather, birdsong and camera-trap
  perception, a multi-agent debate panel, and more.
- **20 registered sources and sinks**, no code required — RSS feeds, weather,
  stocks, Bluesky, Gmail, calendar, webhooks, web search — and beyond that
  fixed list, `mcp_source`/`mcp_sink` can reach any of the 500+ community
  servers in the public MCP Registry. See `DisSysLab/docs/SOURCES_AND_SINKS.md`.
- **Crash recovery that actually works.** Every office can checkpoint and
  resume without losing or duplicating a message — a real adaptation of the
  global distributed-snapshot algorithm, not a toy version.
- **Debugging and checkpoints, explained in English.** Ask OfficeSpeak to
  narrate a saved checkpoint or a run's full recorded history — grounded in
  real distributed-systems theory (logical clocks, consistent snapshots), not
  hidden as implementation detail. See
  `DEBUG_TRACE_AND_CHECKPOINT_WALKTHROUGH.md` for a full worked example.

`FEATURES.md` has the complete, verified inventory across both repos; `ROADMAP.md` says what's next.

## The example this page follows

Rather than show fragments from several different offices, this whole page
follows **one story start to finish** — Stage 1, the correction, and then
Stage 2 actually running it — so you can see the entire path an office takes,
end to end. The story:

> Once each period my club gets a batch of market data, forecasts, and news,
> plus our decisions from last period. Two analysts each read it and recommend
> a plan — one value-investing, one chasing emerging opportunities. A manager
> weighs both, proposes a plan, checks the taxes and fees with an accountant,
> then writes the final plan to a file. Keep our portfolio and history in one
> place, and handle one period at a time so the books stay consistent.

(You'll paste this exact wording in yourself in Stage 1, step 2 — this is just
a preview of where the story is headed.)

By the end of Stage 1 you'll have watched this exact office get built,
explained back, and corrected. By the end of Stage 2 you'll have watched it
actually run and produce real numbers. Then, at the very end, you'll do the
whole thing again with an idea of your own.

---

# Stage 1 — Describe it (no installation)

## Step 1 — one-time setup (~10 min, no Python)

Don't already have an `OfficeSpeak` folder on your computer? See
**[GETTING_THE_FILES.md](GETTING_THE_FILES.md)** first — a short,
no-experience-needed guide to downloading it from GitHub (including a link to
GitHub's own cloning tutorial, if you'd rather do that than download a ZIP).
(Whoever pointed you here can also just hand you the two things below
directly, if that's easier.)

1. On claude.ai, create a new **Project** named **OfficeSpeak**. (A "Project" on
   claude.ai is just a named folder for conversations that all share the same
   background instructions and reference material — nothing to install.)
2. Open `OfficeSpeak/offices/claude_project/start_instructions.md`, copy its
   whole contents, and paste them into the Project's **custom instructions**.
3. Upload every file in `OfficeSpeak/offices/claude_project/start_gallery/` as
   Project **knowledge** (the worked examples that make the assistant good at
   this).

That Project *is* the OfficeSpeak assistant. Start every office in a new chat
inside it.

## Step 2 — describe an office

Open a **new chat inside the OfficeSpeak Project**. For this walkthrough, paste
in exactly this description (word for word is fine — it's the one this whole
page follows):

> Once each period my club gets a batch of market data, forecasts, and news,
> plus our decisions from last period. Two analysts each read it and recommend
> a plan — one value-investing, one chasing emerging opportunities. A manager
> weighs both, proposes a plan, checks the taxes and fees with an accountant,
> then writes the final plan to a file. Keep our portfolio and history in one
> place, and handle one period at a time so the books stay consistent.

(When you get to the end of this page and try your own idea, here's what
that description was answering, in case it helps you write yours: what should
the office watch and decide; what comes in and from where; what goes out and
to where; who does the work, with a name and a one-line job for each; what each
helper needs to know to do its job — the most important one; what anyone
remembers over time; anything the whole team shares; and any rules about
order or one-at-a-time handling. Don't try to get it perfect — a rough first
description is the point.)

## Step 3 — build

Send the description. The assistant replies with the **team** of workers and
how information flows between them, a short **explanation** of what happens to
one item start to finish, and a list titled **"Things I assumed —"** (choices
you didn't spell out). For our example, the assistant's explanation reads
something like this:

> Each period the office lets one batch in. Both analysts read it and each
> writes a recommendation; a worker whose only job is to wait for both hands
> the pair to the manager. The manager puts together a proposed plan and asks
> the accountant what it would cost in taxes and fees; the accountant works
> that out and reports back; the manager finalizes the plan, writes it and the
> updated holdings to the shared portfolio, saves the plan to the file, and
> lets the next period in.
>
> **Things I assumed —** the two analysts are treated equally and the manager
> has the final say; the office handles one period fully before starting the
> next so the shared portfolio stays consistent; and **the accountant works out
> the taxes from the proposed plan alone — it does not look at what the club
> currently holds.** Tell me if any of these should be different.

It also gives a plain-English description of what each worker does — but not
its actual code or prompt yet; deciding whether a worker ends up as Python or a
language-model prompt, and writing that, is a later step (Stage 2), not part
of this conversation.

## Step 4 — read and correct

Read the explanation, and **especially the "Things I assumed —" list** —
that's where mistakes hide. Look at the third assumption above: the accountant
prices taxes from the proposed plan alone, never checking what the club
currently owns. That's wrong — taxes and fees depend on what you already hold,
not just the proposed move. Send the correction in plain English:

> "The accountant has to see what we currently hold — otherwise the tax
> numbers are guesses. Taxes depend on what we paid for what we own."

The assistant revises and shows you what changed:

> One new link: before it prices anything, the accountant now looks up what
> the club currently holds and what we paid for it, and uses that for the tax
> math. Nothing else about the office changes.

Repeat this read-and-correct loop until an explanation matches what you meant.

> This is the whole idea: you shouldn't have to specify a correct office up
> front. It's easier to *react* to a concrete team than to describe one
> perfectly from nothing. Catching exactly this kind of gap — a worker that
> computes something but was never given a fact it needs — is what the
> "Things I assumed —" list is for.

## Step 5 — understanding a worker

You can ask the assistant to look closely at any single worker. How it helps
depends on the kind of worker:

- **A computational worker** (its job is a well-defined computation — working
  out a fee, averaging numbers) can be **walked through on example inputs**:
  the assistant reasons through what its description implies for a specific
  input so you can see whether it's right. Try asking about the accountant,
  after the correction: "Walk me through what the accountant does for period
  1, if we start with no shares and $10,000 cash and the analysts propose
  buying 8 shares." This is still in English at this stage — actually writing
  code, and actually running it on real numbers, comes in Stage 2.
- **A judgment worker** (its job is done by a language model — weighing an
  argument, writing a summary) is **not** tested or graded. There's no fixed
  right answer to check against. Instead the assistant simply **shows you its
  prompt** and asks *"Is this what you mean?"*, and can show a few example
  inputs and what the model produced — for you to read and judge, not for the
  system to score. Getting an LLM worker right is a matter of whether its
  prompt says what you intend.

## Step 6 — what to send back (the most valuable part)

1. **Your description** — what you pasted in (or your own idea, if you tried
   one after the example).
2. **Did the team make sense?** Could you follow the explanation? Where did it
   lose you?
3. **The "Things I assumed —" list** — anything wrong or missing? Did you catch
   it before being told (as with the accountant above)?
4. **Your correction(s)** — what you said, and whether the revision fixed it.
5. **Jargon slips** — the assistant is supposed to avoid words like "port",
   "queue", "state". Tell us if it slips.
6. **Would you use this?** For what?

Short notes are fine. Confusion and dead-ends are the signal.

---

# Stage 2 — Run it for real (needs a computer with Python)

This is where a description becomes an actually-running system. **You don't
have to do this part yourself** — send us what Stage 1 produced (the
assistant's hand-off file) and we'll run it and send back what happened. If
you (or someone helping you) do want to do it directly, here's the whole
path, continuing the same investment-club example, now with the accountant's
correction already built in, so you can see the exact numbers it produces.

**A few words, explained, before we start:** a **terminal** (also called a
"command line" or "shell") is a plain, text-only window where you type
instructions to your computer one line at a time, instead of clicking icons —
on a Mac it's an app called **Terminal**, already installed, in
Applications → Utilities. A **command** is one line you type into it, then
press Return/Enter to run. A **folder** (technically a "directory") is the
same thing as the folders you already see in Finder — a terminal just lets you
move between them by typing their name instead of double-clicking. Every
command below is something you can copy and paste in exactly as written (just
change the parts that are clearly your own file paths).

## Step 1 — install the runtime

Open Terminal, then type each of these lines, pressing Return after each one:

```bash
cd path/to/DisSysLab
pip install -e .
python -c "import dissyslab; print('DisSysLab OK')"
```

(`cd` means "change directory" — move into that folder. `pip install -e .`
means "install the package that lives in this folder." The last line just
checks it worked; if you see `DisSysLab OK` printed back, you're set.)

You'll also need an LLM backend for any judgment (LLM) workers an office uses
— our investment-club example happens to need none (every worker in it is
plain, deterministic Python), so you can skip this for this walkthrough.
`install.sh` sets a backend up for you (Ollama for free/local, or an
OpenRouter/Claude API key) when a later office needs one; doing it by hand,
export whichever the office's workers expect, e.g.:

```bash
export OPENROUTER_API_KEY='...'
```

(Choosing *which* backend, and mixing backends across an office's workers,
is covered properly in step 2d below — this is just enough to get set up.)

## Step 2 — turn the description into a runnable office

This is the real point of Stage 2. Starting from Stage 1's output — the
network, the "Things I assumed —" list, and each worker's approved body —
Stage 1 ends by producing a single **hand-off file**: an ordinary `.py` file
listing every worker and connection, with two kinds of blanks still open —
`registered_as=None` for anything that needs to be matched to a real
data source or destination, and `approved=False` for anything that needs its
actual code or prompt written and checked. Whoever does Stage 2 does three
things, in order:

### 2a. Match sources and sinks

The description names things like "a batch each period" and "a file"; DisSysLab
has a fixed catalogue of registered ones (`DisSysLab/docs/SOURCES_AND_SINKS.md`).
Follow `OfficeSpeak/offices/claude_project/phase3_source_sink_matching.md` to
match each one, or find out there's no match yet and flag it rather
than guessing. In our example one matches cleanly and one doesn't — both are
worth seeing, since "nothing fits" is a real, common outcome, not a failure:

| Worker | The description's words | What happens |
|---|---|---|
| the final-plan file | "writes the final plan to a file" | **Clean match:** `jsonl_recorder(path="recommendations.jsonl")` — appends one line of JSON per period. No credentials needed. |
| FEED (the per-period batch) | "once each period my club gets a batch of market data, forecasts, and news..." | **Nothing fits.** No registered source polls Yahoo/Bloomberg/news feeds and bundles them into one per-period batch. Following `phase3_source_sink_matching.md`'s "when nothing fits" path, FEED is reclassified from `kind="source"` to `kind="transform"` with a stand-in body (a fixed sequence of 3 period numbers) for building/testing — flagged, not silently guessed. It needs one upstream kick to start, which *is* a clean, tiny match: the registered `starter` (fires a single one-time signal, nothing else). |

Only `jsonl_recorder` is a real "asked for X, X exists" match. `starter` isn't
answering anything in the description — it's plumbing added only because FEED
became a transform and every transform needs something upstream to trigger it.

### 2b. Approve each office-specific worker

Follow `OfficeSpeak/offices/claude_project/phase3_approval.md` — for a
computational worker, run it on example inputs and check the outputs; for a
judgment worker, read the prompt and a few example outputs and judge whether it
says what was meant. This is the one required human-review gate before
anything runs unattended.

Here's the accountant — the worker the correction changed — approved as
real code. Notice it does exactly what was asked: it asks the ledger for
current holdings *before* it prices anything, not after.

```python
def _make_accountant_fn():
    _PRICE_PER_SHARE = 100.0
    pending = {}

    def accountant_fn(msg):
        if "proposed_shares" in msg:
            # A proposal from the manager -- ask the ledger what we hold
            # *before* pricing anything (this is the correction).
            pending["period"] = msg["period"]
            pending["proposed_shares"] = msg["proposed_shares"]
            return [({"action": "read"}, "to_ledger")]

        # The ledger's reply.
        current_shares = msg["aapl_shares"]
        current_cash = msg["cash"]
        proposed = pending["proposed_shares"]
        fee = 1.0 * proposed + 0.001 * current_shares * _PRICE_PER_SHARE
        return [({"fee": fee, "current_shares": current_shares,
                   "current_cash": current_cash}, "to_manager")]
    return accountant_fn
```

Tested on period 1's actual numbers, before approving it:

```
IN  (manager's proposal):  {"period": 1, "proposed_shares": 8}
OUT (accountant's first reply): asks the ledger, {"action": "read"}

IN  (ledger's reply):      {"aapl_shares": 0, "cash": 10000.0}
OUT (accountant's answer to the manager):
    {"fee": 8.0, "current_shares": 0, "current_cash": 10000.0}
```

(The two value/opportunity analysts in this example are deliberately simple,
fixed stand-ins — "recommend buying a small, growing number of shares each
period" — so the walkthrough has real, changing numbers to follow without
needing real market data. A real office would replace them with a genuine
computation or an LLM judgment worker, approved the same way.)

The whole hand-off file — every worker, not just the accountant snippet above
— is at `OfficeSpeak/offices/claude_project/investment_club_handoff.py` if
you want to see how it all fits together or run it yourself.

### 2c. Generate and run

Once every source/sink is matched and every worker is approved, one command
turns the finished hand-off file into a real, runnable office:

```bash
python -m dissyslab.office.assemble investment_club_handoff.py investment_club_office
```

This writes `investment_club_office/office.md` (the office description) and
`investment_club_office/roles/` (one file per worker) — you should never need
to hand-write either. Then:

```bash
dsl build investment_club_office     # just checks it compiles
dsl run investment_club_office       # actually runs it
```

Running it end to end for real produces exactly three periods (this office is
set up to run three, then stop on its own):

```
[Manager] period 1: proposing 8 shares (val=5, oppo=3); asking accountant
[Accountant] period 1: asking ledger for current holdings before pricing
[Accountant] period 1: current holdings shares=0, cash=10000.00 -> fee=8.00
[Manager] period 1: fee=8.00, holdings before this trade: shares=0, cash=10000.00 -> after: shares=8, cash=9192.00

[Manager] period 2: proposing 16 shares (val=10, oppo=6); asking accountant
[Accountant] period 2: current holdings shares=8, cash=9192.00 -> fee=16.80
[Manager] period 2: -> after: shares=24, cash=7575.20

[Manager] period 3: proposing 24 shares (val=15, oppo=9); asking accountant
[Accountant] period 3: current holdings shares=24, cash=7575.20 -> fee=26.40
[Manager] period 3: -> after: shares=48, cash=5148.80
```

and `recommendations.jsonl` ends up holding:

```json
{"period": 1, "bought": 8, "fee": 8.0, "resulting_shares": 8, "resulting_cash": 9192.0}
{"period": 2, "bought": 16, "fee": 16.8, "resulting_shares": 24, "resulting_cash": 7575.2}
{"period": 3, "bought": 24, "fee": 26.4, "resulting_shares": 48, "resulting_cash": 5148.8}
```

Each period's fee is computed from the *previous* period's ending holdings —
exactly the thing the correction asked for, now visibly true in real numbers
(period 2's fee of 16.80 = $1/share × 16 shares + 0.1% × 8 shares the club
already held × $100 — the 8 shares are period 1's result, not period 2's
proposal).

### 2d. Choose a backend; deploy it

If any worker is a judgment (LLM) worker, pick which backend it runs on —
and if the office needs to keep running past this terminal session (the
usual case for anything meant to run 24 × 7, not just a one-off demo),
set that up too. Follow
`OfficeSpeak/offices/claude_project/phase3_backends_and_deployment.md`
for both.

This step currently takes a Python-comfortable person following the two
`phase3_*.md` docs by hand — it is not yet one command you could run
yourself with no help. See "Known limitations" below.

## Step 3 — see this exact office, already built

If you'd rather run something that's already known to work before assembling
your own hand-off file, this exact office (post-correction) already lives in
DisSysLab as a validated example:

```bash
cd path/to/DisSysLab
dsl run dissyslab/gallery/apps/investment_club
```

You should see the identical three-period output shown above.

## Step 4 — see a bug found by testing one worker

The **debug_demo** office is a tiny weather-alert office with a *planted* bug,
to show how OfficeSpeak debugs a computational worker:

```bash
cd path/to/OfficeSpeak/offices/debug_demo
python office.py             # buggy: alerts on almost every reading (10)
DEBUG_FIX=1 python office.py  # fixed: one alert, on the real spike
python per_agent_tests.py     # tests each worker alone; localizes the bug
```

Then read `debugging_walkthrough.md` in that folder — it's the plain-English
story of the same bug: the office over-alerts, the assistant tests each worker
by itself, finds that one worker compares the wrong value, explains it in
plain English, and fixes it with one line. (Note: this works because the
workers are ordinary Python. Judgment/LLM workers are not tested this way —
see Stage 1, step 5.)

## Step 5 — what to send back

Everything from Stage 1's step 6, plus: did step 2 actually produce a running
office with the numbers shown above? Where did the source/sink matching or the
worker approval step get confusing or stuck? Did steps 3/4 run for you? Did
the debugging walkthrough make the bug clear? How hard did the whole run step
feel, start to finish?

## Want to see another example run, a different way?

`STAGE2_WALKTHROUGH.md` walks a completely different office (a fractions
tutor for a student, with a real language-model grader) through Stage 2 a
different way: live, inside the Claude desktop app's Cowork mode, rather than
a plain terminal. Good if you want to see an LLM judgment worker actually
running, or the Cowork-based workflow specifically.

---

## Now try your own idea

Once you've followed the investment-club example through both stages, describe
an office of your own the same way (Stage 1, step 2's questions are there to
help). If someone else is doing Stage 2 for you, hand off the same way —
matching, approving, generating, running — and compare how much friction you
hit against how smooth this worked example felt.

---

## Known limitations (so they don't surprise you)

- **Running your *own* office isn't one command yet.** Building, explaining,
  and correcting is smooth and complete in Stage 1. Turning that into a running
  office (Stage 2, step 2) is now possible end to end — a real generator
  exists and has been validated on real cases, including the investment-club
  example above — but it currently takes a Python-comfortable person
  working through two short docs by hand (matching sources/sinks; approving
  each worker), not a single command you could run entirely on your own yet.
- **Source/sink matching can hit a real gap — but this is likely to cause
  little or no friction in practice.** DisSysLab's registered sources and
  sinks are a fixed catalogue (`docs/SOURCES_AND_SINKS.md`), not arbitrary
  live connectors, so if your office needs something not on that list, the
  honest first answer used to be "not supported yet." In practice there are
  three fallbacks, checked in this order, before that's the real answer:
  (1) `mcp_source`/`mcp_sink` can already reach any server in the [MCP
  Registry](https://modelcontextprotocol.info/tools/registry/) — 500+
  community servers as of 2026 (Google Drive, Notion, Postgres, Discord,
  and hundreds more) — so a surprising number of "not built-in" requests
  are actually already reachable; (2) a generic outbound/inbound webhook
  covers most everything else (e.g. "text me" → a webhook to a third-party
  SMS gateway you set up); (3) a handful of specific gaps (Discord,
  Telegram, USGS earthquakes, crypto prices, CSV/SQLite, more RSS feeds)
  are easy, near-term additions — see `docs/SOURCES_AND_SINKS.md`'s "Adding
  more" section — so naming what you actually want, even if it's not on the
  list today, is useful signal. Only if none of the three apply is the
  honest answer "not supported yet" — see `phase3_source_sink_matching.md`.
- **Debugging is early.** It covers **computational** workers (testing them in
  isolation). Judgment/LLM workers are shown to you as a prompt to confirm, not
  debugged. Checking whether messages are getting stuck between workers, and
  explaining a saved snapshot, are coming next.
- **Maintenance isn't in this round.**
- **It's research software.** Expect rough edges — that's what we're hoping
  you'll help us find.

## Troubleshooting (Stage 2)

- **`pip install -e .` fails** — check Python 3.10+ (`python --version`) and
  that you're inside the `DisSysLab` folder; try `python -m pip install -e .`.
- **`import dissyslab` fails** — you likely installed into a different Python
  than the one you're running.
- **An example prints nothing / doesn't stop** — re-run exactly as shown, from
  the folder given; each finishes within a few seconds.
- **Generation raises an `AssemblyError` or `GeneratorError` (step 2)** — it
  always names the exact problem (a still-blank `registered_as`, an unapproved
  worker, a port declared under the wrong name). It's telling you something in
  the hand-off file doesn't match what Stage 1 or the source/sink matching
  step decided — fix that, don't work around the error.

## Getting help

Send your notes (Stage 1, step 6, and Stage 2, step 5 if you ran anything) to
your OfficeSpeak contact — and if you want Stage 2 done for you rather than
doing it yourself, send your hand-off file too. Thanks for trying this —
your confusion is our roadmap.

## Read the whole story in one place

Everything above is interleaved with setup steps, troubleshooting, and
side notes. If you'd rather reread the investment-club example straight
through — the description, the build, the mistake it caught, the
correction, and the real numbers it produced — with none of that in
between, see
[`INVESTMENT_CLUB_WALKTHROUGH.md`](INVESTMENT_CLUB_WALKTHROUGH.md).

## License

[MIT](LICENSE).
