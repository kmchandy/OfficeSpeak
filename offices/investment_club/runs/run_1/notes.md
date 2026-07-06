# investment_club / run_1 — diagnostic (reference, not a score)

Intended graph is a reference, not an answer key. Question: is Claude's
office valid for the spec (implements it + needed properties), and could
Pat understand/modify it? A different or better decomposition is success.

## Both hard inferences — got
- **Shared record is READ, not just written.** Warren, Bill, Herb, Don
  all `<-> Rachel`. (We predicted this would be missed. It wasn't.)
- **Serialization.** A gate (Gus), released by Don's `done`, orders the
  reads/writes of the shared record. (The other predicted-hard inference.)

## Coordination primitives — all correct
- **merge_synch** (Meg) for the join of Warren + Bill for the same item.
- **select** for the Don<->Herb tax ask-and-wait loop.
- **gate** (Gus) for one-at-a-time.
- Model/shadow portfolios stored in Rachel for Warren/Bill/Don.
- Sources -> fair_merge -> broadcast to every agent (incl. Herb).

## Differences from our intended graph (improvements / neutral)
- Claude **split the join into its own agent (Meg)**; we had folded it
  into Don. Claude's is cleaner — one worker per job. Different, arguably
  better → success.
- Names differ (Gus vs Gwen; Meg is new) — cosmetic.

## Under-specified (by the spec, not a Claude error)
- "Each can see how his approach is doing and try to do better": Claude
  stores each agent's model portfolio and lets each read Rachel, so each
  *can* see his own performance — faithful to the words. HOW each adapts,
  and whether Don reweights advisors by track record, the spec does not
  say and the graph does not wire. This is a legitimate iteration point,
  not a miss: it is under-specified consistently in spec and graph.

## Verdict
1-shot + the named registry was **sufficient** for a valid, arguably
better office that got both hard inferences and all four coordination
primitives on the first held-out test. Strong data point (n=1, graph
only). Next: capture Claude's explain-back (the arbiter for Pat) and run
an iteration round on the adaptation mechanism.
