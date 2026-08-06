# weather — review and pre-registered predictions (held-out demo)

Pre-registered before the fresh Project build. Not given to the assistant. This is the
**predict-and-learn** shape — a *new shape not in the gallery* — so it tests whether the
assistant generalizes beyond the offices it has seen.

## What the build should produce

```
open_meteo, met_no (async) -> fair_merge -> repository (record)
actuals -> repository
head-forecaster <-> repository            (ask-and-wait: get recent history)
head-forecaster -> repository (write forecast + weights) ; head-forecaster -> FORECAST
gate: one day at a time (async writes to the shared repository)
```

## Pre-registered predictions

Coordination:
- **fair_merge: SHOULD appear** — two (or more) forecast services arrive asynchronously
  at unpredictable times, so a source merge. (High confidence.)
- **record: SHOULD appear** — the repository is a shared history read and written by
  several workers → a record/keeper. (High confidence; Pat names it.)
- **gate: SHOULD appear** — async writes to the shared repository, "one day at a time,"
  is exactly the gate's case. (High confidence; Pat gives the reason.)
- **select (ask-and-wait): SHOULD appear** — the head-forecaster asks the repository for
  recent history and waits before forecasting → a cycle (head-forecaster ↔ repository).
  (High confidence.)
- **merge_synch: probably NOT** — the head combines whatever the repository holds; it
  doesn't wait for both services *for the same item*. (Check.)

The key generalization test — **delayed match**:
- A forecast is graded against an actual that arrives *later*. Prediction: the assistant
  handles this **through the repository** (the actual is filed against its day, so the
  head reads aligned forecast/actual pairs) and does **not** invent a new "matcher"
  primitive. If it reaches for a matcher, that tells us the library needs one; if the
  record suffices, that's the cleaner result. Either outcome is informative.

Bodies (gold standard):
- **head-forecaster → Python** — a small regression / least-squares fit of weights over
  the recent window (this office's learning is statistical, not an LLM).
- Services and actuals → sources; repository → record (library). **Likely no LLM worker
  at all** — a fully computational predict-and-learn office (good for coverage). A build
  that invents an LLM "conditions interpreter" is over-reaching (Pat didn't ask).

Explain-back "Things I assumed —" the build should surface:
1. **Window length unspecified** — "the last couple of weeks" is vague. The assistant
   picks a default (e.g., 14 days) and flags it. (Predicted #1 assumption.)
2. **Cold start** — with fewer than a window of days, the regression can't fit; the head
   should note it uses equal weights until it has history.
3. **Fresh vs stale weights** — the head should use the *current* weights (the
   ask-and-wait gives freshness); a correction candidate if it keeps a stale copy.

## Correction step (B4) candidate

Pat: "use the last **14** days, and until we have 14 days, weight the services equally."
A clean plain-English tightening of the window + cold-start rule.

## This office is the all-five-capabilities demo

One coherent Project session showcases every capability:
1. **Specify** — paste this spec; assistant builds graph + explanation + bodies.
2. **Correct** — the window/cold-start correction above.
3. **Checkpoint** — after a run, "what did the office look like when it saved?" → the
   repository's history, forecasts in flight, current weights.
4. **Replay** — "walk me through the last two weeks" → forecasts, actuals arriving,
   weights being refit (the office visibly learning).
5. **Build/debug an agent** — "the head-forecaster's weights look wrong" → explain its
   tape and refine the regression body.

## Runtime note (step 4)

The run exercises **fair_merge + record + gate + select** together — the richest
coordination of any office so far — and the debug dict will show the **weights evolving**
period by period (the office learning), which is the figure for capabilities 4 and 5.
