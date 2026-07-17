# trading_desk / build run 1 — B4 correction (the round-trip closes)

Following the explain-back (`build_run_1.md`), whose #1 assumption was the
price-handling choice, Pat gives a one-line, plain-English correction.

## Pat

> "The head-trader should get the most recent price when it proposes a trade."

## Claude's revised office (the diff)

Pat picked the *fresh* option the explanation had offered (query on demand) over the
*stale* default (a broadcast latest-price copy). The change:

- **Add a worker — `price-keeper`** — owns the latest price per stock; the price
  feed updates it; it answers "what's the current price?" on request.
- **Remove** the `prices -> head-trader` broadcast and the head-trader's own
  latest-price copy.
- **head-trader**, when a signal fires, now **asks the price-keeper for the current
  price (ask-and-wait)** before proposing — so it sizes on a fresh price, not a copy
  that may be seconds old.

```
Agents (changed / added):
  price-keeper — keeps the current price per stock; answers price requests
               · state: latest price per stock · reads: price ticks; price requests
               · sends: current price back to the asker
  head-trader  — ... on a signal, asks price-keeper for the current price, then
                 proposes to risk-manager ... (no longer keeps its own price copy)
Wiring (changed):
  prices -> price-keeper                 # keeper stays current
  head-trader <-> price-keeper           # ask current price, wait for it  (NEW ask-and-wait)
  head-trader <-> risk-manager           # propose, wait for approval      (unchanged)
  (prices -> head-trader broadcast: REMOVED)
```

## Why this is the loop working

- The explain-back surfaced a real distributed-data concern (deciding on a possibly
  stale price) as the top thing to confirm, in plain English.
- Pat corrected it in one plain-English sentence — no mention of agents, ports, or
  freshness semantics.
- Claude turned that into a precise structural change: a keeper agent plus a second
  ask-and-wait, replacing the stale copy with a fresh on-demand read.

Net for the paper: build -> explain (flags the price handling) -> correct ("get the
most recent price") -> revised office. A non-programmer moved a stateful, concurrent
office from a stale-read design to a fresh-read design without ever seeing the
machinery. The head-trader now has two ask-and-wait loops (price-keeper, risk-
manager); the office still has no shared database — the price-keeper owns the price,
the risk-manager owns the book.

## Note

For the running demo, our reference office (`build/run_trading_desk.py`) sizes
trades without a live price and did not implement the stale copy, so no runtime
change is required to tell the paper's story; the correction is a design-level
round-trip shown on the graph. Optionally, the price-keeper + ask-and-wait can be
added to the runnable office later (a keeper agent much like the risk-manager).
