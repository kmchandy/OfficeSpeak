# Getting a debug trace, and looking at a checkpoint — step by step

This is a teaching document for actually doing two things with a running
office: watching a **debug trace** (what each worker sent and received,
in order) and looking inside a **checkpoint** (a saved snapshot of every
worker's memory, taken while the office was running). Both are built and
tested (2026-07-22). The example throughout is `recovery_demo` — the same
five-worker "estimate π by throwing random points at a circle" office used
in the checkpoint design docs — because it ships with DisSysLab, needs no
setup of its own, and needs no LLM key (every worker in it is plain,
deterministic Python).

Every command below is something you can copy and paste in exactly as
written. Your own numbers and timestamps will come out different from the
ones shown here — that's expected, they depend on your machine's clock and
exactly when you press Ctrl-C — but the *shape* of what you see should
match.

---

## Step 0 — set up (once)

1. Get DisSysLab if you don't already have it:

   ```bash
   git clone https://github.com/kmchandy/DisSysLab.git
   cd DisSysLab
   ```

2. Install it:

   ```bash
   pip install -e .
   python -c "import dissyslab; print('DisSysLab OK')"
   ```

   (If you already did this for another walkthrough, skip it — it's a
   one-time step.) You do **not** need an LLM key for this walkthrough —
   `recovery_demo`'s workers are all plain Python, no judgment calls.

3. Check the office is there and runs:

   ```bash
   dsl run recovery_demo
   ```

   You'll see a stream of boxes scroll by, each one an updated estimate
   of π, something like:

   ```
   ╔══════════════════════════════════════════════════════════════════╗
   ║  π ≈ 3.1432
   ║  Inside: 4043 Outside: 1102 Total: 5145
   ╚══════════════════════════════════════════════════════════════════╝
   ```

   Let it run to completion (it stops on its own after about a minute —
   it's reading a fixed file of 10,000 points) or press **Ctrl-C** to stop
   it early. Either way is fine; this was just to confirm the office
   itself works before adding tracing or checkpoints on top of it.

---

## Step 1 — get a debug trace

A trace records, for every worker, every message it sent and every
message it received, each one tagged with a clock value so they can all
be lined up into one ordered story afterward.

### 1a. Turn tracing on and run

```bash
dsl run recovery_demo --trace
```

Watch a few boxes go by — you don't need to wait for the whole run — then
press **Ctrl-C**. Stopping is always manual; there's no setting for "stop
after N messages."

### 1b. Look at what got written

```bash
ls dissyslab/gallery/apps/recovery_demo/trace/
```

You'll see one file per worker:

```
broadcast_0.jsonl
merge_0.jsonl
recovery_demo__Alex.jsonl
recovery_demo__Bob.jsonl
recovery_demo__Pi.jsonl
recovery_demo__csv_points_source.jsonl
recovery_demo__intelligence_display.jsonl
```

(`broadcast_0` and `merge_0` are plumbing the compiler inserted for you —
one hands the source's point to both Alex and Bob, the other funnels
whichever of them finishes first onward to Pi. You never named these two;
Alex, Bob, and Pi are the workers you'd recognize from the office's
description.)

Each file is one line per action. Here's a real excerpt from
`recovery_demo__Alex.jsonl`:

```json
{"t": 1784738222245143000, "dir": "received", "port": "in_", "msg": "{'x': 0.639427, 'y': 0.025011}"}
{"t": 1784738222267379000, "dir": "sent", "port": "out_", "msg": "{'kind': 'inside', 'running_count': 1}"}
```

`t` is the clock value (bigger number = happened later), `dir` is whether
this was a send or a receive, `port` is which inbox/outbox, `msg` is a
short rendering of the message itself.

### 1c. Merge every worker's file into one ordered story

Each file above is just one worker's own diary — to see the whole office's
story in order, merge them:

```bash
dsl explain-trace dissyslab/gallery/apps/recovery_demo/trace/
```

This prints one merged, time-ordered sequence to your screen. A real
excerpt (the very start of a run):

```json
{"t": 1784738222187833000, "agent": "recovery_demo__csv_points_source", "dir": "sent", "port": "out_", "msg": "{'x': 0.639427, 'y': 0.025011}"}
{"t": 1784738222187833000, "agent": "broadcast_0", "dir": "received", "port": "in_", "msg": "{'x': 0.639427, 'y': 0.025011}"}
{"t": 1784738222245143000, "agent": "broadcast_0", "dir": "sent", "port": "out_0", "msg": "{'x': 0.639427, 'y': 0.025011}"}
{"t": 1784738222245143000, "agent": "recovery_demo__Alex", "dir": "received", "port": "in_", "msg": "{'x': 0.639427, 'y': 0.025011}"}
{"t": 1784738222267379000, "agent": "recovery_demo__Alex", "dir": "sent", "port": "out_", "msg": "{'kind': 'inside', 'running_count': 1}"}
{"t": 1784738222267379000, "agent": "merge_0", "dir": "received", "port": "in_0", "msg": "{'kind': 'inside', 'running_count': 1}"}
```

If you'd rather have this in a file than scroll through it on screen, add
`--output`:

```bash
dsl explain-trace dissyslab/gallery/apps/recovery_demo/trace/ --output merged.jsonl
```

### 1d. Get it explained in English

This merged file is still just data — numbers and short codes. Getting it
turned into a plain-English story is the last step, and it's a
conversation, not another command: open your OfficeSpeak chat and paste
in a chunk of the merged output (from Step 1c) along with `office.md`
(the office's description) if Claude doesn't already have it from having
built the office earlier in the same conversation. Ask something like:

> "Here's a debug trace from recovery_demo. Walk me through what
> happened."

Claude reads the raw entries and writes the story, something like:

> "The source sent point (0.639, 0.025) into the office. Alex received it
> and, having decided the point falls inside the circle, sent a running
> inside-count of 1 onward. Pi received that count and updated its
> estimate: π ≈ 4.0000 — that's just the very first point, so the
> estimate is still noisy."

You can ask follow-up questions ("why did the estimate jump around so
much at the start?", "show me just what Bob did") the same way you'd ask
about anything else Claude built for you.

---

## Step 2 — look inside a checkpoint

A checkpoint is a saved snapshot of what every worker's memory held, and
what messages were still in transit, at one instant while the office was
running.

### 2a. Turn checkpointing on and run

```bash
dsl run recovery_demo --snapshot-interval 2
```

`2` means "save a checkpoint every 2 seconds." Let it run for at least
5–10 seconds (long enough for two or three checkpoints to be written),
then press **Ctrl-C**.

### 2b. See what got saved

```bash
ls dissyslab/gallery/apps/recovery_demo/snapshots/checkpoints/
```

You'll see one folder per checkpoint, numbered from zero:

```
000000
000001
000002
```

### 2c. Show one checkpoint's contents

```bash
dsl show-checkpoint recovery_demo latest
```

(`latest` means the most recent one; you can also ask for a specific
number, e.g. `dsl show-checkpoint recovery_demo 1`.) This prints one
merged, human-readable JSON document — no need to open any files by hand.
Below is a real example, from an actual checkpoint of `recovery_demo` — a
later one (N=4, from a longer run) than the 2–3 checkpoints your own
quick 5–10 second test in Step 2a will produce, but the shape is
identical:

```json
{
  "office": "recovery_demo",
  "N": 4,
  "timestamp": "2026-06-15T18:13:34",
  "agents": {
    "recovery_demo::Alex": {
      "user": {"count": 3340},
      "sent": {"out_": 3340},
      "received": {"in_": 4256}
    },
    "recovery_demo::Bob": {
      "user": {"count": 916},
      "sent": {"out_": 916},
      "received": {"in_": 4256}
    },
    "recovery_demo::Pi": {
      "user": {"inside": 3339, "outside": 916},
      "sent": {"out_": 4255},
      "received": {"in_": 4255}
    },
    "recovery_demo::csv_points_source": {
      "user": {"owner_state": {"cursor": 4256}},
      "sent": {"out_": 4256},
      "received": {}
    }
  },
  "in_flight_messages": {
    "merge_0::in_0": [
      {"kind": "inside", "running_count": 3340}
    ]
  }
}
```

Each worker's `"user"` field is its own private memory — Alex remembers
it has classified 3340 points as inside the circle so far; Pi remembers
both counts and could recompute its π estimate from them at any time.
Notice Alex's own count (3340) is one ahead of what Pi has folded in so
far (3339) — that's exactly the in-flight message below, caught between
being sent and being received. `"sent"`/`"received"` are just message
counts, kept for bookkeeping. `"in_flight_messages"` lists anything that
was sent but not yet received at the exact instant this checkpoint was
taken — in the example above, one message (Alex's latest count, 3340)
was still on its way to the merge step when the snapshot was taken.

If you'd rather have this in a file:

```bash
dsl show-checkpoint recovery_demo latest --output checkpoint.json
```

### 2d. Get it explained in English

Same last step as the trace: paste the JSON from Step 2c into your
OfficeSpeak chat and ask Claude to explain it, e.g.:

> "Here's a checkpoint from recovery_demo. What was going on at this
> moment?"

Claude reads the structured JSON and narrates it, e.g.: "At this
checkpoint, Pi had folded in 3339 inside-counts and 916 outside-counts
from Alex and Bob, giving a running estimate of about π ≈ 3.14 at that
instant (4 × 3339 ÷ 4255). Alex had actually already classified one more
point as inside (3340, one ahead of what Pi has) — that message was still
on its way to the step that combines Alex and Bob's counts when this
checkpoint was taken, so it hadn't been folded into Pi's running total
yet."

---

## Step 3 — trace and checkpoints together

You can turn both on for the same run:

```bash
dsl run recovery_demo --trace --snapshot-interval 2
```

Run it, watch it for a bit, Ctrl-C, then use `dsl explain-trace` and
`dsl show-checkpoint` exactly as in Steps 1 and 2 — they don't interfere
with each other. This is the normal way to actually debug something: turn
both on, reproduce whatever seemed wrong, stop, and ask Claude to explain
what the trace and the nearest checkpoint show.

---

## The whole workflow, in one place

1. Turn on debug execution — `dsl run <office> --trace` (add
   `--snapshot-interval SECONDS` too if you also want checkpoints; add
   `--resume N` instead of starting fresh if you're continuing from an
   earlier checkpoint).
2. Stop it from the command line — Ctrl-C, or let it finish on its own.
   There's no automatic stop condition; you decide when you've seen
   enough.
3. Get Claude to explain it — `dsl explain-trace <trace-dir>` and/or
   `dsl show-checkpoint <office> <N|latest>`, then paste the output into
   your OfficeSpeak chat and ask.
4. Fix whatever the explanation surfaced.
5. Start a fresh run — traced or not, checkpointed or not — and repeat.

---

## Why this works (for the curious)

Every message in a trace is tagged with a clock value built from a simple
rule: each worker's clock only ever needs to know the highest value it's
seen so far and add to it — never anything about *why* two things happen
in a particular order, just enough bookkeeping to line up everyone's
diary into one consistent story afterward. The same underlying idea —
Lamport's 1978 "happened-before" relation — is also what the checkpoint
mechanism itself rests on (Chandy and Lamport's 1985 snapshot algorithm,
described in `docs/algorithms/CHECKPOINT_RESUME.md` in the DisSysLab
repo). Full details, including exactly which decisions were made and why,
are in `docs/algorithms/TRACE_AND_LOGICAL_CLOCK.md`.
