# Office description format (for all paper examples) — proposal v1

The single flexible structure every example office in the paper is written in. It
is **plain English, not a form**: each part is prose, parts that don't apply are
omitted, and the section names are guides, not required keywords. It is the shape a
good description takes — and the shape onboarding (steps 0-6) produces.

## The parts

1. **Purpose** — one or two sentences: what the office watches, and what it decides
   or produces.
2. **Inputs** — what comes in, from where, and how often.
3. **Outputs** — what the office produces, and where it goes.
4. **Workers** — the team. For each worker, in a sentence or two: its **name**, its
   **job**, **what it needs to know**, **whom it sends its results to**, and **what
   it remembers** over time (only when there is state). Say it however is natural —
   behavior and who-it-talks-to belong in the same breath ("the accountant works out
   the fees and sends them to the manager"). *This is the heart of the description;
   "what it needs to know" is the part people most often leave something out of.*
5. **Shared records** *(optional)* — anything the whole team reads or writes
   together (a portfolio, a history, a log), and who updates it.
6. **Flow** *(optional)* — the story of what happens when one item comes in, start
   to finish. Its job is mainly the **order and timing** — who waits for whom, what
   happens before what, one-at-a-time — since who-sends-to-whom is already in the
   worker sentences. A useful coherence check, not a second place to re-list
   recipients.
7. **Rules** *(optional)* — anything about order, timing, or care: handled one at a
   time? does anyone wait for someone else? should the office learn over time?
8. **Open questions** *(optional)* — anything Pat is unsure about.

## Flexibility rules

- Prose within each part; no fixed syntax.
- Omit any optional part that doesn't apply (5, 7, 8), and any per-worker detail
  ("remembers") that isn't relevant.
- A worker can be one sentence; only spell out "needs" and "remembers" when they
  matter.
- Pat never writes "agent", "message", "port", or "graph".
- **Pat may fuse what a worker does with whom and when it communicates in one
  sentence — that is expected, not a mistake.** The clean separation of behavior,
  wiring, and timing is Claude's to recover, not Pat's to provide. (Pat's
  description is natural, coupled, and fused; the graph is clean, decoupled, and
  separated; Claude is the translator between them.)

## What each part gives the builder (for us, not shown to Pat)

Purpose -> intent · Inputs -> sources · Outputs -> sinks ·
Workers.needs -> each agent's read-set (and data dependencies) ·
Workers.remembers -> state · Shared records -> a record/keeper (a gate if updated) ·
Flow -> wiring order, joins, ask-and-wait · Rules -> coordination (gate, select,
feedback). The per-worker "needs" line is the seam that makes a spec-vs-wiring check
possible ("you said ACNT needs the plan, but taxes need holdings — nothing feeds it
that").

## Sources and sinks: how they bind to DSL (paper assumption)

Pat names inputs and outputs in her own words; she is **not** restricted to a
registry vocabulary. Binding is Claude's job, and works like the coordination
primitives:

- Sources and sinks are a **named registry** given to Claude in the build prompt
  (name + one-line description of what flows through). Claude maps Pat's Inputs and
  Outputs to registered entries **by meaning**; an unmatched one becomes a
  **declared-but-unbound port** — a flagged gap.
- **Paper assumption:** the registry the examples need is assumed already
  registered; where a live connector is impractical (real market/news APIs) the
  source is backed by **replayed / mock data** so the office runs end-to-end. We
  pick examples whose sources resolve.
- **Future work (not this paper):** a conversation in which Claude helps Pat create
  and register a brand-new source or sink.

Consequence for the thesis: the office is assembled from trusted, registered parts
at its **edges** (sources/sinks) and in its **coordination** (primitives); only the
**worker bodies** are generated.

## The investment club, in this format

**Purpose.** Recommend buy / sell / hold actions each period for a club holding
mutual funds and cash.

**Inputs.** Once per period: a batched feed of financial data, analyst forecasts,
and breaking news; and the club's own buy/sell/hold decisions from the previous
period.

**Outputs.** A recommended action plan for the next period, written to a file,
RECOMMEND. (Club members read it and decide for themselves; that deliberation is
outside the office.)

**Workers.**
- **VAL** — a value-investing analyst; recommends an action plan. *Needs:* the
  period's inputs and the club's current portfolio and history. *Remembers:* what it
  has learned over time.
- **OPPO** — an analyst focused on emerging opportunities; recommends an action
  plan. *Needs* and *remembers:* as VAL.
- **MGR** — the manager; collects both analysts' recommendations, proposes a plan,
  checks its cost, and writes the final plan. *Needs:* both recommendations and the
  cost estimate. *Remembers:* her own experience.
- **ACNT** — the accountant; given a proposed plan, replies with its fees (taxes and
  transaction costs). *Needs:* the proposed plan.

**Shared records.** The club's current portfolio and its investment history, read by
the analysts; updated each period from the club's previous decisions.

**Flow.** Each period, VAL and OPPO read the inputs and the portfolio and each send
a recommendation to MGR. MGR waits for both, proposes a plan, and asks ACNT for its
fees; ACNT replies; MGR then finalizes and writes the plan to RECOMMEND.

**Rules.** One period is handled at a time. MGR waits for both analysts before
proposing, and for ACNT's fees before finalizing.

*(Note: ACNT's "needs" lists only the proposed plan — not the portfolio — which is
the gap the explain-back surfaces and Pat corrects in the worked example. Left as-is
here on purpose: this is Pat's initial description.)*
