# OfficeSpeak — Tester's Manual

Thanks for testing OfficeSpeak. This round is about **building an office in plain
English, understanding it, and correcting it** — plus a first taste of
**debugging**. Long-term maintenance comes later.

You do **not** need any background in distributed systems or multi-agent
frameworks. There are two ways to help, and you can stop after the first:

- **Track A — Build in plain English (no installation).** Everything happens in a
  conversation with an assistant on claude.ai. No Python, no terminal. This is the
  most important part to test, and anyone can do it.
- **Track B — Run an office (needs Python).** Install a small package and run a
  ready-made office to watch one work end to end. For testers comfortable running
  a script.

If setting up Python isn't for you, **just do Track A** — that's the heart of it.

---

## What OfficeSpeak is

OfficeSpeak lets you build a small, always-on software system by **describing a
team of workers in plain English** — an *office*. You say what the office should
watch and decide; an assistant (Claude, set up with OfficeSpeak's instructions)
turns that into a team of **workers** that pass messages to each other, explains
the team back to you, and lets you correct it in plain English. Information comes
in through **sources** and results go out through **sinks**.

The point of the test is to find out whether *you* can go from an English
description to an office you understand and trust — and to tell us every place it's
confusing. Rough edges are exactly what we're looking for; if something is unclear,
that's a bug in our design, not yours.

---

# Track A — Build in plain English (no installation)

## A1. One-time setup (~10 min, no Python)

1. On claude.ai, create a new **Project** named **OfficeSpeak**.
2. Open `OfficeSpeak/offices/claude_project/project_instructions.md`, copy its
   whole contents, and paste them into the Project's **custom instructions**.
3. Upload `OfficeSpeak/offices/claude_project/OfficeSpeak_gallery.md` as Project
   **knowledge** (the worked examples that make the assistant good at this).

That Project *is* the OfficeSpeak assistant. Start every office in a new chat
inside it. (Your contact can share these two files directly if you'd rather not
open the folder.)

## A2. Describe an office

Open a **new chat inside the OfficeSpeak Project** and describe the office you
want, in plain prose. Write freely, or answer these prompts — skip any that don't
apply:

1. **The goal** — what should the office watch, and what should it decide or
   produce?
2. **What comes in** — where does information arrive from?
3. **What goes out** — what does it produce, and where does it go?
4. **The helpers** — who does the work; give each a name and a one-line job.
5. **What each helper needs to know** — *the most important one.* For any helper
   that computes or decides, what current facts must it see? (A helper working out
   taxes needs to know what you currently hold, not just the proposed move.)
6. **What each helper remembers** — does anyone track something over time?
7. **Shared information** — anything the whole team reads or writes together?
8. **Rules** — order, waiting, one-at-a-time, learning over time?

Don't try to get it perfect. A rough first description is the point.

## A3. Build

Send your description. The assistant replies with the **team** of workers and how
information flows between them, a short **explanation** of what happens to one item
start to finish, a list titled **"Things I assumed —"** (choices you didn't spell
out), and each worker's **body** (a small piece of Python for computational jobs,
or an instruction prompt for judgment jobs).

## A4. Read and correct

Read the explanation, and **especially the "Things I assumed —" list** — that's
where mistakes hide. If something's wrong, say so in plain English (e.g., *"The
accountant has to see what we currently hold, otherwise the tax numbers are
guesses"*). The assistant revises and shows you what changed. Repeat until it
matches what you meant.

> This is the whole idea: you shouldn't have to specify a correct office up front.
> It's easier to *react* to a concrete team than to describe one perfectly from
> nothing.

## A5. Understanding a worker

You can ask the assistant to look closely at any single worker. How it helps
depends on the kind of worker:

- **A computational worker** (its job is a piece of Python — averaging numbers,
  computing a fee) can be **tested on example inputs**: the assistant walks through
  what it does with specific inputs so you can see whether it's right. Actually
  *running* those tests is in Track B (see the debugging example), but even in
  conversation the assistant can talk you through it.
- **A judgment worker** (its job is done by a language model — weighing an
  argument, writing a summary) is **not** tested or graded. There's no fixed right
  answer to check against. Instead the assistant simply **shows you its prompt** and
  asks *"Is this what you mean?"*, and can show a few example inputs and what the
  model produced — for you to read and judge, not for the system to score. Getting
  an LLM worker right is a matter of whether its prompt says what you intend.

## A6. What to send back (the most valuable part)

1. **Your description** — what you pasted in.
2. **Did the team make sense?** Could you follow the explanation? Where did it lose
   you?
3. **The "Things I assumed —" list** — anything wrong or missing? Did you catch it?
4. **Your correction(s)** — what you said, and whether the revision fixed it.
5. **Jargon slips** — the assistant is supposed to avoid words like "port", "queue",
   "state". Tell us if it slips.
6. **Would you use this?** For what?

Short notes are fine. Confusion and dead-ends are the signal.

---

# Track B — Run an office (needs Python)

For testers comfortable running a script. This lets you watch an office work end to
end and see the debugging aid in action.

## B1. Install the runtime

```bash
cd path/to/DisSysLab
pip install -e .
python -c "import dissyslab; print('DisSysLab OK')"
```

## B2. Watch an office run

The **weather** office (pure Python, no API key) predicts a temperature by blending
two forecast services and learns which one to trust:

```bash
cd path/to/OfficeSpeak/examples/weather/reference/build
DSL_DEBUG=1 python run_weather.py
```

You should see it finish on its own with 14 forecasts, one saved snapshot, and the
office's trust shifting from a 50/50 split toward the more accurate service — it
**learns**, **stops by itself** (even though it has a loop), and **saves a
consistent snapshot**, none of which you had to ask for.

## B3. See a bug found by testing one worker

The **debug_demo** office is a tiny weather-alert office with a *planted* bug, to
show how OfficeSpeak debugs a computational worker:

```bash
cd path/to/OfficeSpeak/offices/debug_demo
python office.py             # buggy: alerts on almost every reading (10)
DEBUG_FIX=1 python office.py  # fixed: one alert, on the real spike
python per_agent_tests.py     # tests each worker alone; localizes the bug
```

Then read `debugging_walkthrough.md` in that folder — it's the Pat-facing story of
the same bug: the office over-alerts, the assistant tests each worker by itself,
finds that one worker compares the wrong value, explains it in plain English, and
fixes it with one line. (Note: this works because the workers are ordinary Python.
Judgment/LLM workers are not tested this way — see Track A, step A5.)

## B4. What to send back

Everything from A6, plus: did the examples run for you? Any errors? Did the
debugging walkthrough make the bug clear? How hard did the run step feel?

---

## Known limitations (so they don't surprise you)

- **Running your *own* office isn't one command yet.** Building, explaining, and
  correcting is smooth in Track A; wiring a freshly built office to *run* still
  takes some Python. The ready-made examples in Track B run as-is.
- **Debugging is early.** It covers **computational** workers (testing them in
  isolation). Judgment/LLM workers are shown to you as a prompt to confirm, not
  debugged. Checking whether messages are getting stuck between workers, and
  explaining a saved snapshot, are coming next.
- **Maintenance isn't in this round.**
- **Sources and sinks are limited** to built-in or stand-in data, not arbitrary
  live connectors.
- **It's research software.** Expect rough edges — that's what you're here to find.

## Troubleshooting (Track B)

- **`pip install -e .` fails** — check Python 3.10+ (`python --version`) and that
  you're inside the `DisSysLab` folder; try `python -m pip install -e .`.
- **`import dissyslab` fails** — you likely installed into a different Python than
  the one you're running.
- **An example prints nothing / doesn't stop** — re-run exactly as shown, from the
  folder given; each finishes within a few seconds.

## Getting help

Send your notes (Track A step A6, and B4 if you ran anything) to your OfficeSpeak
contact. Thanks again — your confusion is our roadmap.
