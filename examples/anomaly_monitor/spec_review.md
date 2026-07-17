# anomaly_monitor — review and pre-registered predictions

Our notes on the held-out spec (`spec.md`). Not given to Cowork. This office is the
**detect-anomaly** shape; its interesting tests differ from the trading desk's.

## What the build should produce

A mostly-linear pipeline:

```
metrics -> monitor (per-service baseline + threshold) -> deduper -> router -> {owner sinks}
```

## Pre-registered predictions

Coordination:
- **router: SHOULD be used** — Pat asks to "send each alert to whoever owns that
  service," which is exactly the exclusive if/elif/else the router is for. This is
  the primitive this office showcases. (High confidence.)
- **NO fair_merge** — there is a single readings stream, so no source merge is
  needed. A build that adds fair_merge would be over-reaching (unless it chooses to
  model per-service streams merged, which Pat did not ask for). (Check.)
- **NO gate** — no shared writable state; each worker's memory is its own
  (per-service baselines in the monitor, per-service last-alert in the deduper). A
  build that adds a gate is over-reaching. Good test of "use only the coordination
  you need."
- **Per-key (per-service) state** — the build should recognize that the monitor and
  deduper keep state **keyed by service**, not one global value.

Explain-back "Things I assumed —" the build should surface:
1. **Threshold + window unspecified.** Pat said "a few standard deviations" and "a
   recent window" without numbers. The build should pick defaults and flag them — the
   analog of the trading desk's undefined sizing rule. (Predicted #1 assumption.)
2. **Dedup window unspecified** — "right away" is not a duration. Should be flagged.
3. **Cold start** — a service with no baseline yet can't be judged; the monitor needs
   some readings before it can flag. A thoughtful build may note it waits for a
   baseline. (Bonus if surfaced.)
4. **Source granularity** — one stream tagged by service vs. one stream per service.
   The build likely assumes a single tagged stream (matches Pat).

## What this office tests that the trading desk didn't

- The **router** primitive (trading desk had none).
- **Per-key windowed state** as the central pattern (vs. the trading desk's single
  book + analyst signals).
- The **restraint** test: correctly using *no* fair_merge and *no* gate — "an office
  uses only the coordination it needs."

Unlike the trading desk, there is no obvious latent distributed-data bug here (it's a
clean pipeline), so the explain-back's job is mainly to surface the unspecified
numbers (threshold/window/cooldown), not to catch a wiring gap.

## Correction step (B4) candidate

Pat supplies the missing numbers: "flag a reading more than 3 standard deviations out,
over the last 20 readings, and don't repeat an alert for the same service within a
minute." A clean, plain-English tightening of the thresholds the build flagged.

## Reference runnable office

`build/run_anomaly.py` (+ `agents/monitor.py`, `agents/deduper.py`) — our hand-built
version: verified to run, terminate, write one checkpoint, catch one spike per service
(z ~ 4.2), tag owners (router-as-tag), and dedupe a deliberate repeat.
