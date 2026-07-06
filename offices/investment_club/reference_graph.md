# investment_club — reference graph (corrected base)

One of **two useful bases**, not a replacement for run_1:
- `runs/run_1/actual_graph.md` — Claude's original graph. Kept as a live base
  because an analytical explain-back of it *found real latent issues* — that run
  is itself an experiment result (see `runs/run_1/explanation_analytical.md`).
- this file — the **corrected** graph, used as the clean control for plant-a-gap
  so a flagged defect in a mutant is the planted one.

Both are valuable: run_1 shows the explain-back surfacing coordination smells;
this graph gives mutants a clean baseline. This file incorporates three fixes
found by that analytical explain-back of run_1 ("three spots I had to paper over"):

1. **Explicit join at Don.** run_1 gave Don two inbound edges (item from Gus,
   argument-pair from Meg) correlated only because the gate keeps one item in
   flight — an implicit merge that silently breaks if the gate is relaxed. Fix:
   **Meg carries the item forward** with both arguments, so Don has ONE aligned
   inbound and no join is needed. The gate returns to its single job:
   serializing the shared-record read-modify-write.
2. **Herb off the fan-out.** run_1 broadcast the item to Herb, who did nothing
   with it until Don proposed. Fix: drop `Gus -> Herb`; Don hands Herb the item
   together with the proposed action (Herb is already ask-and-wait from Don).
   Result: Gus fans out to **only Warren and Bill** — the two who genuinely need
   the item at once.
3. **Model-portfolio semantics** (noted, not silently wired — see end).

Why keep run_1 as a base (not superseded): its graph + the analytical explain-back
that found these issues are themselves a result — evidence for E3 that the
explain-back surfaces latent coordination coupling in review mode. Both bases are
run.

```
Agents:
  yahoo_finance — source: financial data & analyst forecasts · sends -> fair_merge
  bloomberg     — source: financial data & analyst forecasts · sends -> fair_merge
  news_feeds    — source: breaking news, a few feeds · sends -> fair_merge
  Gus    — gate: let one piece of information in at a time · sends admitted item -> Warren, Bill
  Warren — value analyst · reads: item, Rachel · sends: (item, value-argument) -> Meg ; model-portfolio update -> Rachel
  Bill   — opportunities analyst · reads: item, Rachel · sends: (item, opp-argument) -> Meg ; model-portfolio update -> Rachel
  Meg    — merge_synch(inports: [warren, bill]): wait for both arguments for the same item, carry the item forward · sends (item, both arguments) -> Don
  Herb   — tax-and-fees analyst · reads: (proposed action, item) from Don, Rachel (holdings) · sends: tax+fees report -> Don
  Don    — decision maker · reads: (item, both arguments) from Meg, Herb's report, Rachel · sends: (proposed action, item) -> Herb ; final action -> decisions ; final action + real & Don's model-portfolio update -> Rachel ; done -> Gus
  Rachel — record(holds: arguments, actions, real portfolio, model portfolios for Warren/Bill/Don)
  decisions — sink
Wiring:
  yahoo_finance, bloomberg, news_feeds -> fair_merge -> Gus
  Gus -> Warren, Bill          # fan-out only to the two who act on the item at once
  Warren -> Meg                # each carries the item + its argument
  Bill   -> Meg
  Meg -> Don                   # single inbound to Don: the item + both arguments, already aligned
  Don <-> Herb                 # ask-and-wait; Don passes the item with the proposed action
  Warren <-> Rachel            # log the argument; update Warren's model portfolio
  Bill   <-> Rachel            # log the argument; update Bill's model portfolio
  Herb   <-> Rachel            # read current holdings for the tax/fee math
  Don    <-> Rachel            # log the final action; update real & Don's model portfolio
  Don -> decisions
  Don ..done..> Gus            # release the next item
Notes:
  Explicit join: Meg carries the item forward with both arguments, so Don has ONE
  aligned inbound and does not rely on the gate to line up two separate streams.
  Fan-out is minimal: only Warren and Bill, who both need the item at once. Herb
  is demand-driven (Don hands him the item with the proposed action); he is not on
  the fan-out. The gate's only remaining job is to serialize the shared-record
  read-modify-write, so one item is fully handled before the next.

Open (issue 3 — model-portfolio semantics, NOT silently wired):
  - Body (Stage B): how each analyst prices the hypothetical trade — mark each
    model portfolio to the same market data, at a defined price.
  - Wiring (a Pat-question): "whose advice is winning" needs a comparison of the
    three model portfolios against the real one. Options: (a) leave the raw
    practice portfolios in Rachel and let Pat eyeball them; (b) add a Scorer agent
    that periodically reads real + 3 models and reports a scoreboard to a sink.
    Ask Pat which she wants before wiring (b).
```
