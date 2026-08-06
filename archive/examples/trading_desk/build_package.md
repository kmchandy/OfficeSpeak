# Phase B — build package (paste into a fresh Cowork/Claude chat)

Held-out: paste everything below into a clean chat. It is the message-passing
office-builder prompt followed by Pat's trading-desk description. Do NOT paste our
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

- **source(name, …)** — brings information in (a news feed, market data).
- **fair_merge** — combines several sources into one stream, taking
  whichever message arrives first. Use *only* to merge sources.
- **merge_synch(inports: […])** — waits for one message on each named
  inport, combines them, and emits one message. Use when a worker needs
  several inputs *for the same item*.
- **select** — a worker that reads whichever input its current state
  points to, updating that state as messages arrive. Use for ask-and-wait
  (send a request, wait for the reply).
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
- No shared memory: if several agents need the same information, give one
  agent the job of keeping it and answering requests, or broadcast it.
- If a worker needs several inputs for the same item, use **merge_synch**.
- If a worker must send a request and wait for an answer, use **select**.
- If an agent that *owns* shared information is updated while handling
  each item, put a **gate** so its memory stays consistent.
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

I want a desk that watches the market in real time and *suggests* trades — buy or
sell — for a handful of stocks we follow, with a short reason for each suggestion.
People on the desk read the suggestions and decide for themselves; the office only
proposes.

## Inputs

1. A live stream of **price updates** for the stocks we follow. These arrive
   continuously and quickly.
2. **News from two independent feeds**, arriving asynchronously and in bursts:
   posts from **X** (social media) and **Bloomberg's** newswire. Both carry
   market-moving headlines — Fed announcements, analyst reports, breaking stories.

The price feed and the two news feeds arrive independently and at different rates.

## Outputs

A running log of suggested trades — each with the stock, buy or sell, and a short
reason — written to a file, TRADES.

## Workers

- **chart-analyst** — a technical analyst who watches prices and signals a trade
  when a stock breaks out of its recent moving average.
- **news-analyst** — an analyst who reads the news and signals a trade when a story
  looks likely to move a stock.
- **head-trader** — decides whether to actually suggest a trade, and how big.
- **risk-manager** — keeps the desk's book (current positions, cash, and risk
  limits) and approves or rejects a proposed trade.

## What each worker does

- **chart-analyst.** Watches the price stream. For each stock it keeps a
  **30-minute moving average** of the price. When the price crosses from below to
  above that average it signals **buy** to the head-trader; when it crosses from
  above to below, it signals **sell**. It signals only at the moment of the
  crossing, not on every tick. This is a computational job — plain arithmetic on
  the price stream.
- **news-analyst.** Reads each news headline as it arrives. Given the headline and
  the list of stocks we follow, it decides whether the news is likely to push one of
  those stocks up or down soon. If so, it signals **buy** (likely up) or **sell**
  (likely down) for that stock to the head-trader, with a one-sentence reason; if the
  headline isn't clearly relevant, it does nothing. This is a judgment job — reading
  and interpreting text — so it is handled by an LLM.
- **head-trader.** Receives signals from the chart-analyst and the news-analyst as
  they come in — whichever fires first — and, using the current price, decides
  whether to propose a trade and how big. Sends the proposed trade to the
  risk-manager and waits for approval; if approved, writes the suggestion to TRADES.
- **risk-manager.** Keeps the desk's book — current positions, cash, and risk
  limits. When the head-trader proposes a trade, checks it against the book and the
  limits, approves or rejects it, and if approved updates the book. Handles one
  proposal at a time so the book stays consistent.
