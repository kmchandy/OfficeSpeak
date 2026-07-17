# investment_club / run_1 — Claude's actual graph

Prompt: offices/prompt.md (v1), 1-shot (support_desk example), registry named.
Source: fresh Claude chat, investment_club/spec.md pasted at the end.

```
Agents:
  yahoo_finance — source: financial data & analyst forecasts · sends -> fair_merge
  bloomberg     — source: financial data & analyst forecasts · sends -> fair_merge
  news_feeds    — source: breaking news, a few feeds · sends -> fair_merge
  Gus    — gate: let one piece of information in at a time · sends admitted item -> Warren, Bill, Don, Herb
  Warren — value analyst: argue buy/sell/hold from a value-investing view · state: (via record) his model portfolio · reads: current item, Rachel · sends: argument -> Meg ; argument + model-portfolio update -> Rachel
  Bill   — opportunities analyst: argue from a new-opportunities view · state: (via record) his model portfolio · reads: current item, Rachel · sends: argument -> Meg ; argument + model-portfolio update -> Rachel
  Meg    — merge_synch(inports: [warren, bill]): wait for both arguments for the same item, combine · sends the pair -> Don
  Herb   — tax-and-fees analyst: work out tax consequences & transaction fees of a proposed action · reads: current item, proposed action, Rachel (holdings) · sends: tax+fees report -> Don
  Don    — decision maker: propose an action, check it with Herb, finalize · state: select-loop for the Herb back-and-forth · reads: current item, both arguments, Herb's report, Rachel · sends: proposed action -> Herb ; final action -> decisions ; final action + real & model-portfolio update -> Rachel ; done -> Gus
  Rachel — record(holds: arguments, actions, real portfolio, model portfolios for Warren/Bill/Don)
  decisions — sink: the club's buy/sell/hold recommendations go out here (a display or JSONL file)
Wiring:
  yahoo_finance -> fair_merge
  bloomberg     -> fair_merge
  news_feeds    -> fair_merge
  fair_merge -> Gus
  Gus -> Warren          # broadcast the current item...
  Gus -> Bill
  Gus -> Don
  Gus -> Herb            # ...so all the information reaches every agent
  Warren -> Meg          # value argument
  Bill   -> Meg          # new-opportunities argument
  Meg -> Don             # both arguments, for the same item
  Don <-> Herb           # propose an action; get tax + fees back (ask-and-wait)
  Warren <-> Rachel      # log the argument; update Warren's model portfolio
  Bill   <-> Rachel      # log the argument; update Bill's model portfolio
  Herb   <-> Rachel      # read current holdings for the tax/fee math
  Don    <-> Rachel      # log the final action; update real & Don's model portfolio
  Don -> decisions       # the buy/sell/hold recommendation
  Don ..done..> Gus      # release the next item
Notes:
  One item at a time: Gus admits the next piece of information only after Don signals done — i.e. after Don has logged the action and updated the portfolios in Rachel — so the shared record stays consistent.
  Don needs both arguments for the same item, so Meg (merge_synch) waits for Warren and Bill before Don starts.
  Don proposes an action, sends it to Herb, and waits for the tax/fees reply before finalizing — a small ask-and-wait loop.
```

(Explain-back not captured in this paste — the other half of the round-trip.)
