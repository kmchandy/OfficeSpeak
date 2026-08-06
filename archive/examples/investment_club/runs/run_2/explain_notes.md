# investment_club / run_2 — explain-back diagnostic

Question this run was designed to answer: **does the explain-back surface the
one real gap we found by hand in run_2 — that Herb keeps his own tax basis and
is never wired to Bruno (who owns the real portfolio), so his tax/fee numbers
can be computed on holdings that have drifted from the truth?**

Held-out discipline: the explainer got only `prompt_explain.md` + the run_2
graph. It did not get the spec, the intended graph, or the run_2 build notes
where we first flagged the Herb gap. So a mention of the gap is the explainer
finding it, not repeating it.

## Result: caught, and framed for Pat

The "Baked-in choices —" list names the Herb gap explicitly:

> Herb figures taxes and fees from his own records of the club's cost basis,
> not from Bruno's live holdings. ... Right now nothing connects Herb to Bruno.
> Tell me if Herb should ask Bruno for the current holdings before working out
> the taxes.

This is exactly the item we identified by careful reading. Crucially it is
phrased as a *question for Pat* ("Tell me if Herb should ask Bruno..."), not as
a technical note — which is the whole point of the explain-back: Pat, a
non-programmer, can answer "yes, he should" and the office gets fixed. Pat never
has to know the words "replica," "stale read," or "consistency."

## Why it caught it (mechanism, worth keeping)

The explain prompt's instruction 4 asks the explainer to list "who keeps the
shared information and who reads it." Walking the graph to answer that question
mechanically exposes the gap: Nora is written but not read; Bruno owns the real
holdings; Herb needs holdings to compute tax but has no edge to Bruno and instead
carries his own copy. The gap is visible precisely because the explain step
forces an ownership/who-reads-whom audit. This is evidence that the "Baked-in
choices" section is doing real work, not decoration.

## Two other honest catches (bonus)

The explainer also surfaced, unprompted:
- **Nora is write-only** — arguments are filed but never read back before a
  decision. That is arguably a second under-wiring (the spec said everything is
  "written down where all the agents can see it," implying it should be
  readable). Good catch.
- **"Try to do better over time" is not wired in** — the same
  adaptation/reweighting gap we flagged as under-specified in both build runs.
  The explainer correctly declined to invent it and instead flagged it as an
  assumption for Pat.

## What this establishes

- The round-trip works on a *real* defect, not a toy one. Build introduced a
  genuine distributed-state gap (local copy vs authoritative owner); explain-back
  surfaced it in plain English as a yes/no question for Pat. That is the
  end-user-correctness loop working end to end on one concrete case.
- It is a single data point. It shows the loop *can* catch this class of gap; it
  does not show it reliably catches all such gaps. To make the claim, we need
  more offices and, ideally, some planted gaps where we know the answer.

## Suggested follow-ups (not started)

1. Run the same explainer on the run_1 (shared-memory) graph. In run_1 Herb
   *did* read Rachel for holdings, so the Herb line should come back clean —
   a useful negative control (explainer doesn't cry wolf when the wiring is fine).
2. Plant-a-gap test: take a known-good graph, delete one edge (e.g., Herb->owner),
   run the explainer, check it flags exactly that. Repeat for a few edges. This
   turns "it caught one" into a measured hit rate for the explain-back.
3. Feed this explanation to a fresh "Pat" persona (no systems knowledge) and see
   which baked-in choices she reacts to — tests readability, not just coverage.
