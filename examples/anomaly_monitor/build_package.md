# Phase B — build package (paste into a fresh Cowork/Claude chat)

Held-out: paste everything below into a clean chat. It is the message-passing
office-builder prompt followed by Pat's anomaly-monitor description. Do NOT paste our
review or predictions. Save what Claude produces (the office graph + the
explanation) and hand it back for scoring.

---

You help someone who is not a programmer — call her **Pat** — build an
**office**: a small team of software agents that runs continuously,
watches for information, and reacts to it.

## What an office is

An office is a set of **agents** (workers), each with one clear job.
Every agent keeps its **own private memory** — no agent can reach inside
another's memory, and there is no shared database. Agents share
information **only by sending messages**. Information comes in through
**sources** and results go out through **sinks**. The office runs on its
own; it does not wait to be prompted.

Your job has two parts: (a) turn Pat's description into an office — a
graph of agents — and (b) explain that office back to Pat in plain
English so she can confirm it or ask for changes.

## Sharing information without shared memory

If several agents need the same information, you have two choices:
- **Give one agent the job of keeping it and answering requests.** Others
  send that agent a request and get a reply (ask-and-wait).
- **Broadcast it**, so each agent keeps its own private copy up to date.

Pick whichever is simpler for the job. Either way it is just messages.

## Building blocks you can use by name

Name a worker for each job Pat describes, with a one-line job description
(most workers are driven by an LLM prompt; a few are simple code). For
coordination, use these ready-made agents by name:

- **source(name, …)** — brings information in.
- **fair_merge** — combines several sources into one stream, taking
  whichever message arrives first. Use *only* to merge sources.
- **merge_synch(inports: […])** — waits for one message on each named
  inport, combines them, and emits one message. Use when a worker needs
  several inputs *for the same item*.
- **select** — a worker that reads whichever input its current state
  points to. Use for ask-and-wait (send a request, wait for the reply).
- **gate** — admits one item at a time and waits for a "done" signal
  before admitting the next.
- **router** — sends each message to exactly one place based on a
  condition (if / elif / else).
- **sink(name, …)** — sends results out (a display, a JSONL file).

## How to write the office

```
Agents:
  <Name> — <one-line job> · state: <its own private memory> · reads: <messages it receives> · sends: <messages it sends>
  ...
Wiring:
  <sources> -> fair_merge -> <first worker>
  <A> -> <B>                 # a message
  <A> <-> <Keeper>           # a request and its reply
Notes:
  <what runs one item at a time and why; any waits or joins; who owns which shared information>
```

Rules of thumb:
- One worker per job Pat names.
- If a worker needs several inputs for the same item, use **merge_synch**.
- If a worker must send a request and wait for an answer, use **select**.
- If an agent that *owns* shared information is updated while handling
  each item, put a **gate** so its memory stays consistent.
- Use only the coordination the description needs — not every building block.
- Use only the sources and sinks Pat's description implies. Do not invent
  extra jobs Pat did not ask for.

## Then explain it to Pat

After the office, write a short plain-English explanation of it as a team —
who does what, and what happens when information comes in. End with
"**Things I assumed —**" listing the choices Pat did not spell out, so Pat
can confirm or correct them.

## Then write each worker's body

For every worker you named (not the ready-made coordination agents), write its
**body** — the code that turns each incoming message into an outgoing one:

- For a **computational** worker (arithmetic, thresholds, bookkeeping): plain
  **Python**, as a small class with a `run(msg)` method that returns the output
  message, or `None` to send nothing. Keep any memory as instance state.
- For a **judgment** worker (reading/interpreting text): an **LLM prompt** — the
  system prompt the worker would use, plus the shape of its input and output
  messages.

Give each body its own labeled code block so it can be dropped straight into a file.
Use the exact worker names and the reads/sends you declared in the office.

---

# Pat's office description

## Overview

I want an office that watches our services' health and alerts me when something looks
abnormal.

## Inputs

A continuous stream of **health readings** — for each of our services (web, db,
cache), a number arrives regularly (say, a response time).

## Outputs

**Alerts** written to a file, ALERTS — each naming the service, the abnormal reading,
and how far out of the normal range it was.

## Workers

- **monitor** — for each service, learns what "normal" looks like over a recent
  window and flags a reading that is far outside it.
- **deduper** — groups repeated alerts for the same service so I get one message, not
  twenty in a row.
- **router** — sends each alert to whoever owns that service.

## What each worker does

- **monitor.** For each service separately, keeps a recent window of readings and its
  average and spread. When a new reading is more than a few standard deviations from
  that service's recent average, it raises an alert (service, value, how far out) to
  the deduper. Otherwise it stays quiet. Plain arithmetic per service.
- **deduper.** Keeps track of when it last alerted for each service; if the same
  service alerts again right away, it suppresses the repeat and passes only the first.
- **router.** Looks up who owns the service and sends the alert to that owner.
