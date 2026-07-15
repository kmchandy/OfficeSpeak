# Office experiment layout (the gold standard)

Every office folder (trading_desk, anomaly_monitor, ...) uses the same structure so a
reader can tell **inputs** from **held-out results** from **our reference code**.

```
<office>/
  spec.md              INPUT  — Pat's five-section description
  build_package.md     INPUT  — the office-builder prompt + spec, pasted into a FRESH chat
  spec_review.md       OURS   — pre-registered predictions + rubric (not shown to the fresh chat)

  runs/                HELD-OUT results — what a fresh Claude conversation produced
    run_1/
      graph_and_explanation.md   the office graph + explain-back the fresh chat produced
      correction.md              Pat's correction and the revised office
      agents/                    the agent bodies the fresh chat wrote  (gold standard)
      ...run outputs...          results of running those fresh bodies (TD, checkpoint, alerts)

  reference/           OURS   — implementation we authored during development to verify the
                               substrate runs (termination detection, checkpoint). NOT the
                               held-out build. A sanity check, not evidence of build-validity.
    build/  agents/  snapshots/  ...
```

## Two claims, two artifact sources (state this in the paper)

- **Build-validity** ("can Claude turn a plain-English spec into a correct office —
  graph *and* agent bodies?") is measured by the **held-out `runs/`**, produced by a
  fresh chat that saw only `build_package.md`.
- **Substrate guarantees** ("it terminates, checkpoints, replays for debugging") are
  shown by running code — ideally the fresh bodies in `runs/`, with `reference/` as a
  sanity check.

## Gold standard

The fresh chat produces the **graph, the explanation, AND the agent bodies**
(`build_package.md` now asks for all three). We then run *those* bodies — so even the
code is Claude's, not ours. `reference/` exists only to prove the shape runs; it is
never presented as the held-out result.

## Held-out purity

The fresh chat is a separate conversation that never reads these folders — it sees
only what is pasted (the prompt + spec). So `reference/` and `spec_review.md` cannot
leak into it; no need to delete anything before a fresh run.

## What "held-out" actually means (showcase the maximal expert)

We showcase the **full OfficeSpeak assistant** — the real product Pat uses — preloaded
with the coordination primitives, the build/explain/debug prompts, and a gallery of
worked examples of *other* offices. Those assets are the contribution, not
hand-holding, so using them is not inflating the result.

The only held-out discipline that matters: **the specific office being demonstrated
must be new to the assistant** — not in its example gallery, and its solution not fed
in context. (Our "fresh chat" runs exist to prevent exactly that leakage — e.g., from
a development conversation that already contained the intended graph and the
pre-identified gotcha.) Few-shot with *different* worked examples is standard and fine.

`build_package.md` is a self-contained stand-in for the assistant for reproducibility;
the demonstrated office simply must be one the assistant has not already seen solved.
An optional "works with less context too" run can be a robustness footnote — not the
headline.
