# investment_club / run_1 — explain-back diagnostic (negative control)

Question this run answers: **when the Herb-to-holdings link IS present (run_1
wires Herb to read Rachel), does the explainer stay quiet about it — i.e., does
it avoid a false-positive Herb flag?**

Held-out discipline: explainer got only `prompt_explain.md` + the run_1 graph.
No spec, no intended graph, no notes.

## Result: passes. No Herb flag; the wiring is acknowledged as correct.

In the story of one item the explainer wrote:

> Don proposes an action and asks Herb what it would cost in taxes and fees;
> Herb looks up the club's current holdings from Rachel and sends the numbers
> back.

And "Baked-in choices —" contains NO Herb-drift warning. Compare run_2, same
explainer and prompt, where Herb had no edge to the portfolio owner and the
explainer wrote: "nothing connects Herb to Bruno ... the tax and fee numbers
could be off."

So the explainer responds to the actual wiring, not to Herb's name:
- Herb wired to the record (run_1)  -> clean, "looks up ... from Rachel."
- Herb NOT wired to the owner (run_2) -> flagged, "nothing connects Herb to Bruno."

This is the pair that makes the run_2 catch credible: it was signal, not a
boilerplate suspicion the explainer prints for every Herb.

## What the run_1 explanation did surface (all correct)

- One item at a time; nothing starts until Don finishes and records are updated.
- Rachel alone holds every record; everyone goes through her.
- Don waits for both Warren and Bill (the join).
- Don <-> Herb back-and-forth before finalizing.
- Each analyst keeps his own practice portfolio alongside the real one.
- Don has the final say.

All six are real baked-in choices in the graph, phrased for Pat as confirm/change
items. No hallucinated coordination, no invented jobs.

## One apparent asymmetry vs run_2 — resolved (it is not a defect)

run_2's explanation flagged "try to do better over time" as not-wired-in; run_1's
did not. On first read this looked like an inconsistency to fix. It is not, once
the graph / agent-code boundary is applied:

- "Try to do better over time" is **agent-internal** — it is how Warren reasons
  about his own practice portfolio, i.e. his prompt/code, NOT a wire. The graph
  is already complete for it: Warren has his own model-portfolio state and the
  data feed, so he can compute how he did and adapt with no extra edge.
- Therefore a *graph* explanation has no obligation to flag it. run_1 staying
  silent was correct; run_2 flagging it reached slightly into agent internals.

The legitimate, graph-level item here is the **state-ownership choice** —
"each analyst keeps his OWN separate practice portfolio" vs one shared book —
which both explanations DID surface. That belongs on the Baked-in checklist (see
prompt_v2_backlog item 2). The behavior "does he actually improve" does not (item
3). So there is no run_1 defect to fix.

## Status of the explain-back claim after run_1 + run_2

- run_2: catches a real, hand-verified gap (true positive).
- run_1: stays quiet when the same concern is correctly wired (true negative).
- Together: one clean positive and one clean negative on the same concern across
  two substrates. Enough to say the explain-back *can* discriminate; not yet a
  measured hit rate.

## Suggested follow-ups (not started)

1. Plant-a-gap test: delete one known edge from a good graph, run the explainer,
   confirm it flags exactly that edge; repeat for several edges -> a hit rate.
2. (resolved — see the asymmetry section above and prompt_v2_backlog item 3) Do
   NOT add an "asked to improve but not wired" checklist line; adaptation is
   agent-internal. The graph-level item to add instead is per-agent-vs-shared
   state (backlog item 2).
3. Fresh-"Pat" readability pass: give the explanation to a non-systems reader and
   see which baked-in choices she actually reacts to.
