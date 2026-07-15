# Gallery example — investment_club (a shared record + gate, a join, and the "needs-to-see" correction)

Teaches: the registered **record** (shared state read *and* written by more than one
worker) paired with a **gate** (one item at a time so the shared state stays
consistent); a **merge_synch** join; and the canonical correction — a *computing*
worker that was never given a fact it needs (the missing connection). Shown as a full
build → explain → correct loop.

---

## Pat's description

> "Once each period my club gets a batch of market data, forecasts, and news, plus our
> decisions from last period. Two analysts each read it and recommend a plan — one
> value-investing, one chasing emerging opportunities. A manager weighs both, proposes
> a plan, checks the taxes and fees with an accountant, then writes the final plan to a
> file. Keep our portfolio and history in one place, and handle one period at a time so
> the books stay consistent."

---

## Phase 1 — the network (first build)

**Agents**

- **FEED** — *source*. Outbox `out`. Once per period, a batch of market data, forecasts,
  news, and last period's decisions.
- **GATE** — *coordinator* (gate). Inboxes `data`, `control`. Outbox `out`. Lets one
  period in at a time; admits the next only after the manager finishes the current one.
- **VAL** — *transform*. Inbox `in`. Outbox `out`. Reads the period's batch; sends a
  value-investing recommendation.
- **OPPO** — *transform*. Inbox `in`. Outbox `out`. Reads the batch; sends an
  emerging-opportunities recommendation.
- **JOIN** — *coordinator* (merge_synch). Inboxes `val`, `oppo`. Outbox `out`. Waits for
  both analysts' recommendations for the period, then sends the pair.
- **MANAGER** — *transform*. Inbox `in`. Outboxes `to_accountant`, `to_ledger`, `out`,
  `done`. Reads the pair; proposes a plan; asks the accountant for the costs and waits;
  finalizes; writes the final plan and updated holdings to the ledger; sends the plan to
  RECOMMEND; tells the gate the period is done.
- **ACCOUNTANT** — *transform*. Inbox `in`. Outbox `reply`. Reads a proposed plan; works
  out the taxes and fees; replies to the manager.
- **LEDGER** — registered **record** (holds: portfolio, history). Inbox `req`. Outbox
  `reply`. Written by the manager.
- **RECOMMEND** — *sink*. Inbox `in`. The final-plan file.

**Connections**

- (FEED, out, GATE, data)
- (GATE, out, VAL, in)
- (GATE, out, OPPO, in)
- (VAL, out, JOIN, val)
- (OPPO, out, JOIN, oppo)
- (JOIN, out, MANAGER, in)
- (MANAGER, to_accountant, ACCOUNTANT, in)
- (ACCOUNTANT, reply, MANAGER, in)
- (MANAGER, to_ledger, LEDGER, req)
- (MANAGER, out, RECOMMEND, in)
- (MANAGER, done, GATE, control)

What the shape shows: `JOIN` is a **merge_synch** — the manager waits for *both*
analysts on the same period (a join, not "whichever first"). The `MANAGER ↔ ACCOUNTANT`
pair is an **ask-and-wait** (as in trading_room): the manager sends a request and reads
the reply on its inbox. `LEDGER` is the registered **record** holding the shared
portfolio; the `GATE` handles **one period at a time**, and the manager releases it
(`done`) only after it has written the ledger — so a period's writes finish before the
next period begins.

**Explain it back to Pat** (plain English, "workers"):

> Each period the office lets one batch in. Both analysts read it and each writes a
> recommendation; a worker whose only job is to wait for both hands the pair to the
> manager. The manager puts together a proposed plan and asks the accountant what it
> would cost in taxes and fees; the accountant works that out and reports back; the
> manager finalizes the plan, writes it and the updated holdings to the shared
> portfolio, saves the plan to the file, and lets the next period in.
>
> **Things I assumed —** the two analysts are treated equally and the manager has the
> final say; the office handles one period fully before starting the next so the shared
> portfolio stays consistent; and **the accountant works out the taxes from the proposed
> plan alone — it does not look at what the club currently holds.** Tell me if any of
> these should be different.

## Phase 2 — the agent descriptions (first build)

(GATE, JOIN, and LEDGER are registered, so they are not described. LEDGER holds the
portfolio and history.)

- **FEED** *(source)* — once per period, a batch: market data, forecasts, news, and the
  club's decisions from the previous period.
- **VAL** *(transform)* — read the period's batch; produce a value-investing
  recommendation (which funds to buy/sell/hold, and why).
- **OPPO** *(transform)* — the same, from an emerging-opportunities view.
- **MANAGER** *(transform)* — read both recommendations for the period; propose a plan;
  ask the accountant what it would cost in taxes and fees and wait for the answer;
  finalize the plan; write the final plan and the updated holdings to the ledger; send
  the plan to RECOMMEND; tell the gate the period is done.
- **ACCOUNTANT** *(transform)* — read a proposed plan; work out the taxes and fees of the
  trades in it; reply to the manager.
- **RECOMMEND** *(sink)* — the file where each period's final plan is written.

---

## Pat's correction

> "The accountant has to see what we currently hold — otherwise the tax numbers are
> guesses. Taxes depend on what we paid for what we own."

Pat caught a real gap in plain English: the accountant *computes* something (taxes) but
was never given a fact it needs (the current holdings and their cost basis). The fix is
one new reading — the accountant asks the ledger for the current holdings before
pricing.

## The rebuild — Phase 1 (Case 2)

**Agent changed**

- **ACCOUNTANT** — gains an outbox `to_ledger`. Its inbox `in` now also receives the
  ledger's reply (an ask-and-wait, as elsewhere).

**Connections added** (everything else is unchanged):

- (ACCOUNTANT, to_ledger, LEDGER, req)
- (LEDGER, reply, ACCOUNTANT, in)

Now **two** workers touch the shared ledger — the manager writes it and the accountant
reads it — within the same period. This is exactly why the **gate** is there: it keeps
periods from overlapping, so the accountant always reads holdings the current period has
finished updating and never a half-written portfolio.

**Show Pat what changed:**

> One new link: before it prices anything, the accountant now looks up what the club
> currently holds and what we paid for it, and uses that for the tax math. Nothing else
> about the office changes.

## The rebuild — Phase 2 (Case 2)

- **ACCOUNTANT** *(transform)* — read a proposed plan; **ask the ledger for the current
  holdings and wait for them**; work out the taxes and fees **using the cost basis in
  those holdings**; reply to the manager.

(All other descriptions are unchanged.)

---

## What this example teaches

- **A shared record + a gate go together.** When more than one worker reads *and* writes
  shared state (`MANAGER` writes, `ACCOUNTANT` reads the `LEDGER`), a **gate** handles
  one item at a time so the shared state stays consistent across the whole multi-step
  period — the record's per-request serialization isn't enough on its own.
- **merge_synch is a join.** `JOIN` waits for *both* analysts on the same period — pair,
  not whichever-first (contrast the fan-in in trading_room).
- **The famous correction: a computing worker needs the facts it computes on.** The
  accountant priced taxes without the holdings — a missing connection, visible to Pat in
  plain English, fixed by one new reading. This is the "*what each computing or deciding
  worker needs to see*" check the explain-back exists to surface.
- **Ask-and-wait recurs** (MANAGER ↔ ACCOUNTANT, ACCOUNTANT → LEDGER) — the same pattern
  as trading_room, reused without new machinery.
