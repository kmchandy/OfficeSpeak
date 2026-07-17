# weather / run_1 — scoring vs pre-registered predictions

Held-out generalization test: a **new shape (predict-and-learn) not in the gallery**.
Verdict: **strong pass — the strongest held-out result so far**, notable because the
build *corrected two of my pre-registered predictions with sound reasoning*.

## Coordination scorecard

| primitive | predicted | build | verdict |
|---|---|---|---|
| record (Repository) | yes | yes | ✓ |
| gate (one day) | yes | yes, **placed after the join** | ✓ + insight |
| select (ask-and-wait) | yes | yes (head ↔ Repository) | ✓ |
| merge_synch (join) | *probably NOT* | **yes** | **my prediction wrong; build right** |
| fair_merge | *yes* | **not used** | **my prediction wrong; build right** |

The two "misses" are the headline. I predicted `fair_merge` (async sources → merge) and
"probably not merge_synch." The build did the opposite and is **more correct**: the
head-forecaster *blends both services' forecasts for the same day*, which needs them
**paired** — a synchronizing **join** (merge_synch), not "whichever arrives first"
(fair_merge). It reasoned this explicitly ("the head needs both to blend them"). On a
shape it had never seen, it made the join-vs-fair-merge distinction correctly and against
my expectation — reasoning, not pattern-matching.

**Gate-placement insight (unprompted):** it put merge_synch **before** the gate and
explained why — "gating the two services separately would jam the join." Gating each
source before the join would deadlock (the gate admits one, the join needs both). That is
a genuine liveness-correctness insight it volunteered.

## Delayed match — the key generalization question

Predicted: handled *through the record*, no new primitive. **Confirmed.** Actuals are
filed against their day; every forecast carries its day; the head reads aligned
forecast/actual pairs from the Repository. So **the coordination library does NOT need a
`matcher` primitive** — the shared record subsumes the delayed match. Clean result.

## Bodies

- head-forecaster → **Python, no LLM**, as predicted. A fully computational predict-and-
  learn office (good for coverage).
- Method: it used **inverse-recent-error weighting** (`1/(avg_error+1)`), a simpler
  heuristic than the least-squares fit the spec's wording implies ("weights so the blend
  would have been most accurate"). It **flagged this itself** and offered to swap in the
  fitted version. So: minor under-delivery on the stated objective, self-surfaced with a
  fix offered — exactly what the explain-back is for.

## Things I assumed — scoring

- Window unspecified → picked **14 days**, stated it. ✓ (predicted #1)
- Cold start → new service gets an even share. ✓ (predicted)
- **UNPREDICTED, excellent:** the **skipped-service liveness gotcha** — "if a service skips
  a day, the join would sit waiting for it," with a fix offered. A real deadlock risk of
  the merge_synch join, surfaced proactively. This is the trading-desk-caliber catch,
  unprompted.

## Correction step (B4) candidate

My pre-registered correction (window + cold-start) was **pre-empted** — the build already
did both. The natural correction now upgrades the body and doubles as the **capability-5
demo**: Pat says "fit the weights so the blend would have been most accurate over the 14
days," and the assistant swaps the heuristic for a least-squares fit (a `agent_build`
refinement). Alternatively, "make it tolerate a missing service" (the liveness fix).

## Runtime (step 4) — ran Claude's office + fitted body on DSL

Wired the graph (SyncJoin = merge_synch; Repository keeper = record; head ⇄ Repository =
select/ask-and-wait; actuals merged in) and ran a 14-day replay where open_meteo is
accurate (+0.3) and met_no is biased (+3.0). Results (`run_output.txt`):

- **Termination detection fired with the ask-and-wait loop** (head ⇄ Repository) — the
  hard case — clean exit.
- **Exactly one checkpoint** (a consistent Chandy-Lamport cut). Note: at the cut the
  Repository's *applied* memory was empty with writes *in transit* — a genuine
  consistency artifact (the Repository sits one hop from the `actuals` source, so the
  marker reaches it before the head's writes). Honest, and itself a nice "explain a
  checkpoint" point (memory + in-flight messages); a checkpoint showing rich accumulated
  history is a pacing/topology tuning detail, not needed for the claim.
- **The office visibly learns** — the debug dict shows the weights move from even
  (`0.5/0.5`, cold start, no graded days) to fully trusting the accurate service
  (`open_meteo 1.0 / met_no 0.0`) once actuals accumulate, and the forecast error drops
  from ~1.6°C to ~0.3°C. That trajectory is the single figure carrying capabilities
  3–5 (checkpoint, replay, learning).

So the *whole* five-capability office runs on the substrate: Claude's graph + Claude's
fitted body, with join + record + keeper + ask-and-wait, terminating with a checkpoint and
demonstrably learning.

## Bottom line

On an unseen shape, the assistant produced a correct, well-reasoned office with the full
record + gate + select + join coordination, got the join-vs-fair-merge call right *against
my prediction*, volunteered a gate-placement correctness argument and a join-deadlock
assumption, handled the delayed match via the record (no new primitive), and wrote a clean
Python learner that **runs on DSL and visibly learns**. This is transfer, not memorization
— the strongest evidence for the generalization claim.
