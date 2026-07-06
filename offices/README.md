# offices — building offices from English

An *office* is a persistent network of stateful agents — workers with
jobs, plus shared records they **read and write** — that senses,
deliberates, decides, and acts. This folder holds the experiments behind
the contribution:

> Can Claude turn a trained end user's ("Pat's") plain-English
> description of an office into the right graph, and explain that graph
> back to Pat well enough that she can confirm or correct it?

Pat here is not arbitrary: she has read a few case studies and knows the
idiom (name your workers, say what records they keep).

## Two roles an office can play
- **Case study** — a fully worked office (spec + intended graph +
  explanation). Used to *train Pat* and to *seed Claude's prompt* as a
  few-shot example.
- **Test** — a held-out office (NOT in the prompt) whose graph Claude
  must produce from the spec alone, scored against the intended graph.

Rotate roles across runs so a test is never in its own prompt (the
contamination trap).

## Per-office layout
```
offices/
  README.md
  prompt.md               # office-generation prompt (model + chosen case studies)
  <office>/
    spec.md               # Pat's English description
    intended_graph.md     # our hand-built ground truth (roster + diagram)
    explanation.md        # intended plain-English explain-back for Pat
    runs/run_N/
      prompt.txt          # exact prompt used (reproducibility)
      actual_graph.md     # Claude's produced graph
      explanation.md      # Claude's explain-back
      notes.md            # diff vs intended (the result) + observations
    iterations/round_N.md # optional: Pat's edit + the revised graph
```

## The round-trip under test
spec (Pat) → graph (Claude) → explanation (Claude) → Pat confirms/corrects
→ revised graph. Success = Claude recovers a correct office **and**
explains it so Pat can validate, and the loop converges.

## Offices
- `support_desk` — case study; the simplest (a shared record + one-at-a-time).
- `investment_club` — first held-out **test** (advisors + a judge + a tax
  feedback loop + a shared ledger). Its `actual_graph` comes from Claude.
