# OfficeSpeak — a tester's guide (start with the tutor)

Hi Sachin,

Thanks for agreeing to kick the tires on this. You mentioned wanting a software
tutor for your daughter, and it turns out the running example we built is exactly
a tutor — so that is where this guide starts. You will have it running in a couple
of minutes, and by the end you will know enough to change how it teaches, or to
build a different office of your own.

You are the tester we most want to hear from because you will actually read and
run the code. So this guide is written peer-to-peer: it does not explain Python,
it explains *our* pieces and the few ideas that make them fit together.

---

## What this is, in three sentences

An **office** is a small network of **agents** (we call them *workers*) that pass
messages to each other — like a team where each person has an in-tray, does one
small job, and hands results to colleagues. You describe an office by naming its
workers and drawing the connections between them; the tricky coordination
(joining two streams, one-at-a-time access to a shared file, ask-and-wait) is
handled by a few **trusted, predefined primitives**, not by code you have to get
right. Every worker — whether it is plain Python or a language model — is just a
**pure function** of one message and its own state, so the runtime does all the
concurrency and you never touch a thread, a queue, or a lock.

The long-term goal is that a non-programmer describes an office in English and an
LLM assembles it from these primitives. You are seeing the runtime substrate that
makes that safe.

---

## Setup (about 2 minutes)

You need Python 3.10+ and the two repos.

```bash
# 1. the runtime
git clone https://github.com/kmchandy/DisSysLab.git
cd DisSysLab
pip install -e .            # installs the `dissyslab` package
cd ..

# 2. the offices + this guide
git clone https://github.com/kmchandy/OfficeSpeak.git
cd OfficeSpeak/offices/phase2_demo
```

That is enough to run everything Python-only. To use **language-model workers**
(optional, see below), put an Anthropic key where the runtime can find it:

```bash
# in the DisSysLab folder
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
```

Nothing else needs configuring — Claude is the default backend.

---

## Run the tutor now

From `offices/phase2_demo`:

```bash
python tutor.py
```

You will see a short fractions session and a parent report:

```
[SHOW]    1/2 + 1/2 = ?
[FEEDBACK] correct!
[SHOW]    1/4 + 1/4 = ?
[FEEDBACK] not quite — try the worked solution
[SHOW]    2/3 of 9 = ?
[FEEDBACK] correct!
[SHOW]    3/4 - 1/4 = ?
[FEEDBACK] correct!
[SUMMARY] Session done — you got 3/4. Nice work!

=== parent report file ===
  {'kind': 'report', 'mastery': 3, 'questions_seen': 4, 'score': '3/4'}
```

The program starts the office, runs it to completion, and stops on its own. No
event loop, no shutdown code — the runtime detects when the whole office is
quiescent and halts it.

---

## How the tutor office is wired

Open `tutor.py` alongside this. The office is:

```
  SESSION ─start──▶ PLANNER ─show──────────────▶ SCREEN
  ANSWERS ─answer─▶ CHECKER                       ▲   ▲
                       │  ▲                        │   │
             key/answer│  │outcome     feedback────┘   │
                       ▼  │                            │
   PLANNER ◀──reply── BANK (question bank, a record)   │
   PLANNER ──update/read──▶ PROGRESS (a record)        │
   PLANNER ─final──▶ REPORTER ─summary─────────────────┘
                        └─────report──▶ PARENT_REPORT (file)
```

- **SESSION / ANSWERS** are *sources* — they feed the session start and the kid's
  answers in.
- **PLANNER** is the brain: it asks BANK for the next question, shows it, tells
  CHECKER the grading key, records the outcome in PROGRESS, and at the end asks
  REPORTER to write the parent report. It has five outboxes.
- **CHECKER** grades: it receives the *key* (from PLANNER) and the *answer* (from
  the kid) on the same inbox — a fan-in — and buffers whichever arrives first.
- **BANK** and **PROGRESS** are *records* — shared files with a keeper. Because
  only PLANNER touches each of them, a single in-tray already serializes access,
  so **no gate is needed**. (If two workers shared a record, you would wrap it in
  the `gate` primitive; the tutor does not need to.)
- **REPORTER** writes a summary to the screen and a report to a file.

Every one of those workers is the same shape:

```python
def step(message, state) -> list[(outbox, message)]:
    ...        # look at the message, maybe update state, return what to send
```

It never calls `send` or `recv`, never blocks, returns `[]` to send nothing. That
uniform contract is the whole trick — read `planner_step`, `checker_step`,
`bank_step` in `tutor.py` and you have read the entire behaviour of the office.

---

## Two ways to write a worker — and why it matters for your daughter's tutor

The tutor above is all Python rules, so it only grades exact-match answers. The
interesting part is that a worker's body can equally be a **language model**, and
it meets the *identical* contract, so you can swap one for the other without
changing the office at all.

See it directly:

```bash
python triage_swap.py     # same office, body built once as Python, once as a stubbed LLM
python triage_llm.py      # same office again, body is a LIVE Claude call (needs the key)
```

`llm_worker.py` is the adapter: it renders the incoming message into a prompt,
calls the model, and forces the reply into `{send_to, text}`, validating that the
model chose a real outbox. That is all an "LLM worker" is — an input adapter, a
model call, an output adapter — wrapped so it looks like every other worker.

**This is the hook for a real tutor.** To move from exact-match to something that
can read a free-form answer, give a hint, or generate the next question at the
right difficulty, you replace `checker_step` (or add a "coach" worker) with an
LLM body built by `make_llm_step` — same inboxes, same outboxes, same wiring. The
office diagram does not change; only that one worker gets smarter. That swap is
the thing we would most love your read on.

---

## Build your own office (the harness)

You do not wire offices by hand. `harness.py` takes a plain description — workers
with a *kind*, and connections as 4-tuples `(from, outbox, to, inbox)` — and gives
you a runnable network. Ports are inferred from the connections; a bad description
fails with a plain-English error instead of hanging.

```python
from harness import build_office

def triage(msg, state):
    box = "urgent" if "urgent" in msg["text"].lower() else "normal"
    return [(box, msg["text"])]

urgent, normal = [], []
office = {
    "name": "triage",
    "agents": [
        {"name": "ITEMS",  "kind": "source",    "body": my_feed},        # fn() -> item | None
        {"name": "TRIAGE", "kind": "transform", "body": triage},         # step(msg, state)
        {"name": "URGENT", "kind": "sink",      "body": urgent.append},
        {"name": "NORMAL", "kind": "sink",      "body": normal.append},
    ],
    "connections": [
        ("ITEMS",  "out_",   "TRIAGE", "in_"),
        ("TRIAGE", "urgent", "URGENT", "in_"),
        ("TRIAGE", "normal", "NORMAL", "in_"),
    ],
}
build_office(office).run_network()
```

`kind` is one of `source`, `sink`, `transform`, `record` (a single-keeper file),
or `coordinator` (one of the trusted primitives `merge_synch` / `gate` / `select`).
`harness_demo.py` builds three offices this way — including a coordinator — and
runs them; it is a good next thing to read after the tutor.

---

## The one piece of hard distributed-systems work you get for free

Offices can have joins, gates, and feedback loops, so "is the whole thing done?"
is not obvious — a coordinator can be legitimately blocked waiting on one inbox
while another inbox holds a message it will never read. The runtime detects true
quiescence correctly in those cases and halts (this was the last correctness fix
we made; see `tests/integration/test_coordinator_termination.py` in DisSysLab for
the two shapes that used to hang and now don't). You should never see an office
hang. If you do, that is a bug we want to hear about immediately.

---

## What we would love your feedback on

1. Reading `tutor.py` cold — is the uniform `step(message, state)` contract clear,
   or did any worker make you stop and puzzle?
2. The record-with-a-keeper idea (shared file = a worker, one in-tray serializes
   access): did that land, or feel like ceremony?
3. Swapping a Python worker for an LLM worker — did `llm_worker.py` +
   `triage_llm.py` convince you they are really the same contract?
4. Building your own small office with `build_office` — where did you get stuck,
   and were the error messages actually helpful?
5. Anything you tried that hung, crashed, or surprised you.

Rough notes are perfect — a paragraph per point, or inline comments in a copy of
the files. There is no wrong feedback.

---

## File map

| file | what it is |
|------|------------|
| `tutor.py` | the running example — start here |
| `worker.py` | the `Worker` block: hosts a `step(message, state)` body |
| `llm_worker.py` | build a worker whose body is a language model |
| `triage_swap.py` | one office, Python body vs. stubbed-LLM body, identical routing |
| `triage_llm.py` | same office with a live Claude worker (needs the key) |
| `room_monitor.py` | a stateful transform (rolling baseline of sensor readings) |
| `harness.py` | `build_office(spec)` — description → runnable network |
| `harness_demo.py` | three offices built and run purely from specs |
| `test_harness.py`, `test_llm_worker.py` | keyless self-tests you can run |

Questions or anything unclear — just reply to Mani. Thanks again for testing this.
