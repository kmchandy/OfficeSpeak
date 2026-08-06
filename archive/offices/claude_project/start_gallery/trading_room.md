# Gallery example — trading_room (async merge · keeper · ask-and-wait · the correction loop)

Teaches: **fan-in / async merge** (not merge_synch), a **keeper** transform made
consistent by its single inbox plus atomic processing, the **two ask-and-wait
semantics**, and how a correction can *add a coordinator*. Shown as a full
build → explain → correct loop, because the correction here resolves a genuine
semantic choice only Pat can make — both offices are valid.

---

## Pat's description

> "I want an office for a small trading desk. Two traders watch different
> information — one watches a news feed, the other watches market-data numbers — and
> each proposes trades. Before any proposed trade is actually made it has to be
> approved by the ledger, which keeps our positions and cash and rejects anything
> that would break our limits. Every approved trade is written to a trades file."

---

## Phase 1 — the network (first build)

**Agents**

- **NEWS** — *source*. Outbox `out`. Streams news items.
- **MARKET** — *source*. Outbox `out`. Streams market-data numbers.
- **TRADER_NEWS** — *transform*. Inbox `in`. Outboxes `request`, `trade`. Reads a
  news item or a ledger reply; may propose a trade and, on approval, write the trade.
- **TRADER_QUANT** — *transform*. Inbox `in`. Outboxes `request`, `trade`. Same, from
  market-data numbers.
- **LEDGER** — *transform* (a keeper). Inbox `in`. Outboxes `reply_news`,
  `reply_quant`. Keeps positions and cash; approves or rejects one proposed trade at a
  time and replies to the trader that sent it.
- **TRADES** — *sink*. Inbox `in`. Records approved trades.

*(LEDGER applies the limit rules and answers each trader, so it does more than store —
it is a keeper transform, not the bare registered `record`. If it only stored and
returned data, you'd use the registered `record`.)*

**Connections**

- (NEWS, out, TRADER_NEWS, in)
- (MARKET, out, TRADER_QUANT, in)
- (TRADER_NEWS, request, LEDGER, in)
- (TRADER_QUANT, request, LEDGER, in)
- (LEDGER, reply_news, TRADER_NEWS, in)
- (LEDGER, reply_quant, TRADER_QUANT, in)
- (TRADER_NEWS, trade, TRADES, in)
- (TRADER_QUANT, trade, TRADES, in)

What the shape shows: the two traders' proposals **fan in** to `LEDGER`'s one inbox,
and each trader's one inbox is a **fan-in** of its information source and its own
ledger reply. There is **no coordinator**: `LEDGER` stays consistent because it takes
one proposal at a time from its single inbox and processes each atomically — the
single-inbox keeper *is* the serialization. This is a fan-in / async merge, **not** a
merge_synch: the two traders' proposals are independent, not paired.

**Explain it back to Pat** (plain English, "workers"):

> One worker -- a trader -- watches the news and proposes trades based on the worker's state and the news it read. Another worker is identical except that it watches quantitative data streams. Each of these two workers sends proposed trades to the ledger worker, which alone keeps the trading desk's positions and cash. The ledger worker looks at one proposed trade at a time, either approves or rejects the proposed trade based on the ledger's books, and updates the ledger's books. If a trader hears "approved," from the ledger worker, the trader converts the proposed trade to an actual trade by writing it to the trades file.
>
> **Things I assumed —** a trader keeps accepting and processing information from news or quantitative data sources while the trader is waiting to get a reply from the ledger worker about a proposed trade. While the trader is waiting for a reply it does not send another proposal. Tell me if instead a trader should **stop and wait** —
> and stop accepting data from news or quantitative streams — until the ledger replies. Also: the ledger checks one proposed trade at a time, so the books do not become inconsistent due to interference between concurrent trades.

## Phase 2 — the agent descriptions (first build)

- **NEWS** *(source)* — the desk's news feed.
- **MARKET** *(source)* — the desk's market-data numbers feed.
- **TRADER_NEWS** *(transform)* — reads either a news item or a reply from the ledger.
  On a news item: if it is **not** currently waiting for a reply and the news warrants
  a trade, propose a trade (send it to the ledger) and remember it is now waiting; if
  it **is** waiting, update its view of the news but propose nothing. On a ledger
  reply: if approved, write the trade to the trades file; either way, stop waiting.
- **TRADER_QUANT** *(transform)* — the same, driven by market-data numbers.
- **LEDGER** *(transform / keeper)* — keeps the desk's positions and cash. On a
  proposed trade: check it against the limits; if it fits, approve and update positions
  and cash, otherwise reject; reply approve/reject to the trader that sent it. Because
  it handles one proposal at a time on its single inbox, the two traders can never
  corrupt the books.
- **TRADES** *(sink)* — the approved-trades file.

---

## Pat's correction

> "No — while a trader is waiting for the ledger's answer it should stop looking at
> new information entirely and just wait for the reply."

This picks the *other* ask-and-wait semantics. It needs each trader to be fed one
message at a time in an order the trader controls, so a **select** coordinator goes in
front of each trader.

## The rebuild — Phase 1 (Case 2)

**Agents added**

- **SELECT_NEWS** — *coordinator* (select). Inboxes `info`, `reply`, `command`. Outbox
  `out`. Delivers a message from the inbox its state points to; the trader's `command`
  says which inbox to read next.
- **SELECT_QUANT** — *coordinator* (select). Inboxes `info`, `reply`, `command`. Outbox
  `out`.

**Connections changed** (LEDGER, TRADES, and the request/trade edges are unchanged):

- (NEWS, out, SELECT_NEWS, info)
- (LEDGER, reply_news, SELECT_NEWS, reply)
- (SELECT_NEWS, out, TRADER_NEWS, in)
- (TRADER_NEWS, command, SELECT_NEWS, command)
- (MARKET, out, SELECT_QUANT, info)
- (LEDGER, reply_quant, SELECT_QUANT, reply)
- (SELECT_QUANT, out, TRADER_QUANT, in)
- (TRADER_QUANT, command, SELECT_QUANT, command)
- unchanged: (TRADER_NEWS, request, LEDGER, in), (TRADER_QUANT, request, LEDGER, in),
  (TRADER_NEWS, trade, TRADES, in), (TRADER_QUANT, trade, TRADES, in)

**Show Pat what changed:**

> The change adds a worker in front of each trader. This worker hands the trader one
> thing at a time — either the next piece of incoming information or the ledger's
> answer — and the trader tells it which to bring next. After the trader proposes a
> trade it says "bring me the ledger's answer next," so no new information reaches the
> trader until the answer comes; if the trader decides not to propose, it says "bring
> me the next piece of information." That is the only change to the trader — it no
> longer has to remember that it is waiting; the new worker does the waiting.

## The rebuild — Phase 2 (Case 2)

`SELECT_NEWS` and `SELECT_QUANT` are registered coordinators, so they are **not**
described. Only the two traders' descriptions change; NEWS, MARKET, LEDGER, TRADES are
unchanged.

- **TRADER_NEWS** *(transform)* — reads one message at a time from its coordinator. On
  a news item: if it warrants a trade, propose it (send to the ledger) and command the
  coordinator to read the ledger reply next; otherwise command it to read news next. On
  a ledger reply: if approved, write the trade; then command the coordinator to read
  news next. (No "waiting" state is needed — the coordinator guarantees the trader sees
  the reply before any further news.)
- **TRADER_QUANT** *(transform)* — the same, driven by market-data numbers.

---

## What this example teaches

- **Fan-in / async merge is not merge_synch.** The traders' proposals are independent,
  so they merge into one inbox (whichever arrives), never paired. Reaching for
  merge_synch here would be the classic error.
- **A single-inbox keeper serializes shared state.** `LEDGER` needs no gate and no
  shared memory; one inbox + atomic processing keeps the books consistent under two
  senders.
- **"Ask-and-wait" is two different behaviors,** and the choice is Pat's: keep reacting
  and just suppress new requests (Case 1, no coordinator), or freeze and wait (Case 2,
  a commanded select). The explain-back surfaces the choice; the correction resolves it.
- **A coordinator is introduced only when the correction needs it** — the first build
  used none.
- **Keeper vs registered record:** a keeper that applies rules and routes replies is a
  transform; the bare registered `record` is for pure store-and-return.
