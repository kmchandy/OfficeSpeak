# Phase B — build package (paste into a fresh Cowork/Claude chat)

Held-out: paste everything below into a clean chat. It is the shared-memory
office-builder prompt (with a *neutral* worked example, so the investment-club answer
is not leaked) followed by Pat's description. Do NOT paste our review or predictions.
Save the graph, the explanation, and the agent bodies Claude produces, and hand them
back for scoring.

---

You help someone who is not a programmer — call her **Pat** — build an
**office**: a small team of software agents that runs continuously,
watches for information, and reacts to it.

## What an office is

An office is a set of **agents** (workers), each with one clear job.
Agents pass messages to one another. Some agents keep **state** (memory).
Some jobs need a **shared record** that several agents read and write —
like a filing cabinet the whole team uses. Information comes in through
**sources** and results go out through **sinks**. The office runs on its
own; it does not wait to be prompted.

Your job has two parts: (a) turn Pat's description into an office — a
graph of agents — and (b) explain that office back to Pat in plain
English so she can confirm it or ask for changes.

## Building blocks you can use by name

Name a worker for each job Pat describes, and give it a one-line job
description. For structure, memory, and coordination, use these ready-made
agents by name:

- **source(name, …)** — brings information in.
- **fair_merge** — combines several sources into one stream, taking
  whichever message arrives first. Use *only* to merge sources.
- **record(holds: …)** — a shared file/ledger kept by a clerk. Other
  agents send it read requests (and get a reply) and write updates. Use
  whenever several agents share memory that some of them read.
- **merge_synch(inports: […])** — waits for one message on each named
  inport, combines them, and emits one message. Use when a worker needs
  several inputs *for the same item* (e.g., a decider that needs each
  advisor's argument).
- **select** — a worker that reads whichever input its current state
  points to. Use for ask-and-wait (send a request, wait for the reply).
- **gate** — admits one item at a time and waits for a "done" signal
  before admitting the next. Use when workers read and write a shared
  **record** and it must stay consistent.
- **router** — sends each message to exactly one place based on a
  condition (if / elif / else).
- **sink(name, …)** — sends results out (a display, a JSONL file).

## How to write the office

```
Agents:
  <Name> — <one-line job> · state: <what it remembers> · reads: <inputs> · sends: <outputs>
  <Clerk> — record(holds: <the shared files>)
  <Gate>  — gate
  ...
Wiring:
  <sources> -> fair_merge -> <gate or first worker>
  <A> -> <B>                 # a message
  <A> <-> <Clerk>            # a read request / reply, or a write
  <A> ..done..> <Gate>       # a control signal
Notes:
  <what runs one item at a time and why; any waits or joins>
```

Rules of thumb:
- One worker per job Pat names.
- If several workers share memory that some of them read, add a **record**.
- If a worker needs several inputs for the same item, use **merge_synch**.
- If a worker must send a request and wait for an answer, use **select**.
- If workers read *and* write a shared record, add a **gate** so the office
  handles one item at a time and the record stays consistent.
- Use only the sources and sinks Pat's description implies. Do not invent
  extra jobs Pat did not ask for.

## Then explain it to Pat

After the office, write a short plain-English explanation of it as a team —
who does what, and what happens when a piece of information comes in. End with
"**Things I assumed —**" listing the choices Pat did not spell out, so Pat
can confirm or correct them.

## Then write each worker's body

For every worker you named (not the ready-made coordination agents), write its
**body** — the code that turns each incoming message into an outgoing one:

- For a **computational** worker (arithmetic, taxes/fees, bookkeeping): plain
  **Python**, a small class with a `run(msg)` method returning the output message
  (or `None` to send nothing); keep memory as instance state.
- For a **judgment** worker (forming a recommendation from news and data): an
  **LLM prompt** — the system prompt plus the shape of its input and output messages.

Give each body its own labeled code block, using the exact worker names.

---

# Pat's office description

## Overview

I want an office that recommends buy, sell, and hold actions each period for my
investment club.

## Inputs

1. Each period (say, once a day) the office receives a batch of information —
   financial data, analyst forecasts, and breaking news — from sources such as
   Yahoo Finance, Bloomberg, the New York Times, and the Wall Street Journal. Treat
   it as a single combined news source; the office doesn't have to deal with each
   source separately.
2. Each period the office also receives the buy/sell/hold decisions the club
   actually made in the previous period.

## Outputs

Each period the office writes a recommended action plan — what to buy, sell, or hold
next period — to a file called RECOMMEND. Club members read RECOMMEND each period and
make their own decisions; that deliberation is not part of the office.

## Workers

- **value-investor** — a market analyst who recommends an action plan using a
  value-investing strategy.
- **growth-investor** — a market analyst who recommends an action plan using a
  growth strategy.
- **manager** — makes the office's final recommendation.
- **accountant** — works out the taxes and fees of a proposed plan.

## What each worker does

- **value-investor.** Each period, receives all the office's inputs (the news and
  the club's previous decisions) and can see the club's current portfolio and
  history. Using a value-investing strategy, it decides the best action plan (what
  to buy, sell, hold) and sends its recommendation to the manager.
- **growth-investor.** The same as the value-investor, but uses a growth strategy.
- **manager.** Receives all the office's inputs, as well as the action-plan
  recommendations from the value-investor and the growth-investor. She weighs their
  recommendations, uses her own knowledge, and puts together a proposed action plan,
  which she sends to the accountant. When the accountant returns the plan's costs,
  she adjusts the plan into a final recommendation and writes it to RECOMMEND.
- **accountant.** Receives a proposed action plan from the manager, computes the
  taxes and transaction fees if the plan were executed, and sends the cost back to
  the manager.
