# investment_club / run_2 — Claude's actual graph (local-state substrate)

Prompt: offices/prompt_local_state.md (no shared memory; local state + messages).
Source: fresh Claude chat, investment_club/spec.md pasted at the end.

```
Agents:
  Nora   — log keeper: keeps the shared record of every argument and every final action, and hands it out on request · state: the running log · reads: "write this argument/action" requests; look-up requests · sends: an ack, or the requested log, back to the asker
  Gus    — gate: lets one triggering item in at a time · gate
  Warren — value analyst: argues buy/sell/hold from a value point of view; logs his argument; updates his own model portfolio · state: Warren's private model portfolio + his own copy of the latest data · reads: incoming data · sends: argument -> merge_synch:warren; argument -> Nora
  Bill   — opportunity analyst: argues from a new-opportunities point of view; logs his argument; updates his own model portfolio · state: Bill's private model portfolio + own copy of latest data · reads: incoming data · sends: argument -> merge_synch:bill; argument -> Nora
  Don    — decision maker: weighs both arguments, checks tax/fees with Herb, finalizes; logs it; updates his own model portfolio; hands the action to Bruno · state: Don's private model portfolio + own copy of data · reads: the two combined arguments (from merge_synch); Herb's reply; incoming data · sends: proposed action -> Herb (and waits); final action -> Nora; final action -> Bruno
  Herb   — tax-and-fees analyst: given a proposed action, works out tax consequences and transaction fees and reports back · state: tax basis + fee schedule + own copy of the data · reads: Don's proposed action; incoming data · sends: tax+fees -> Don
  Bruno  — custodian: keeps the club's real portfolio, executes Don's final decision, then releases the gate · state: the real portfolio (holdings + cash) · reads: Don's final action · sends: action + resulting holdings -> decisions; ..done..> Gus
Wiring:
  yahoo, bloomberg, news_feeds -> fair_merge -> Gus -> Warren, Bill, Don, Herb   # one item in, then broadcast; each keeps its own copy
  Warren -> merge_synch:warren
  Bill   -> merge_synch:bill
  merge_synch(inports:[warren, bill]) -> Don
  Warren -> Nora            # log the argument
  Bill   -> Nora            # log the argument
  Don   <-> Herb            # send the proposed action, wait for tax+fees
  Don    -> Nora            # log the final action
  Don    -> Bruno           # execute the final action
  Bruno  -> decisions       # record/display the action and new holdings
  Bruno ..done..> Gus       # release the gate for the next item
  (any agent) <-> Nora      # read the shared log on request
Notes:
  One triggering item at a time: Gus admits one and Bruno releases it only after the real portfolio is updated, so the real portfolio and all three model portfolios advance in step and stay comparable. Nobody shares memory: Nora alone keeps the shared log; Bruno alone keeps the real portfolio; Warren, Bill, Don each keep their own private model portfolio. merge_synch gives Don both analysts' arguments for the same item. Don <-> Herb is ask-and-wait (select underneath). The merged feed is broadcast to Warren, Bill, Don, Herb — each keeps its own copy.
```
