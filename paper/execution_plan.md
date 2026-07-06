# Execution plan — from here to a submitted paper

Ordered sequence. De-risk first: prove the office runs with termination detection
and one checkpoint before writing around it. "Show" = demonstrated/running; the rest
is described from the design notes we already have.

Division of labor: **[sandbox]** = Claude does it here (build/run DSL). **[Cowork]** =
Mani runs a fresh Cowork/Claude chat held-out and pastes back (as with the
investment club). **[write]** = Claude drafts, Mani reviews.

## Phase A — Systems demo (the running example) [do first; riskiest]

A1. [sandbox] Install DSL; build a runnable trading-desk office directly on DSL's
    Agent/Network API: bounded, checkpoint-aware price + news sources (emit M~120
    prices, N~12 headlines then stop), the tested `chart_analyst` + `news_analyst_stub`
    bodies, a fair merge into head-trader, head-trader <-> risk-manager (gate + book),
    TRADES sink; prices also feed head-trader (so the stale-price gotcha is real).
A2. [sandbox] Run it; confirm **termination detection** fires on the bounded inputs
    (survives the head-trader<->risk-manager loop).
A3. [sandbox] Tune source `interval` + `--snapshot-interval` for **exactly one
    checkpoint**; confirm one checkpoint dir on disk. (Dry-run to measure R, set
    T ~= 0.6R.)
A4. [sandbox] Add per-agent I/O logging during the run -> produce the **debug dict**
    (agent -> sequence of in/out).
A5. [sandbox] Expose the two cheap commands to the OS agent: **take checkpoint** (the
    existing manual-snapshot trigger) and **stop**.
A6. [sandbox, optional] **Replay self-check**: replay from checkpoint N reproduces
    snapshot N+k on the deterministic office. Do if ~an hour; else describe.

## Phase B — Interaction evidence (the build -> explain -> correct loop) [held-out]

B1. [sandbox] Assemble the held-out **build package** (general build prompt +
    `trading_desk/spec.md`).
B2. [Cowork] Run the build held-out; paste back the graph + agent bodies. [sandbox]
    Score against `spec_review.md` predictions.
B3. [Cowork] Run the **explain** held-out on that graph; paste back. [sandbox] Verify
    the **stale-price gotcha** surfaces (pre-registered), like the Herb catch.
B4. [Cowork] Apply Pat's correction ("fetch the current price at decision time");
    rebuild; confirm the fix. Capture the one-iteration loop.
B5. [sandbox] From the A4 debug dict, capture **one transcript** of Claude explaining
    a chosen agent's in/out to Pat in plain English.

## Phase C — Write the paper [after A and B produce real results]

C1. [write] Rewrite **abstract + intro** around the sharpened thesis (guarantees
    foregrounded; the plain-English loop is how you drive it, not the novelty).
C2. [write] Make the **trading desk the worked example**: Pat's spec -> the built
    graph + bodies (B2) -> explain-back with the gotcha (B3) -> correction (B4);
    include the run showing TD + one checkpoint (A2-A3).
C3. [write] Add the **deterministic-replay-for-debugging** section from
    `deterministic_replay_design.md` (described): NOW = a snapshot, two-cut episode,
    minimal merge-order logging, per-agent tapes, self-check; include the debug dict
    + the B5 transcript as the figure. Mention (don't build) concurrent live replay.
C4. [write] **Evaluation**: the running demo (TD + checkpoint), the held-out
    explain-back catch (stale price), and the general-agent **ablation** (described,
    or partial if cheap).
C5. [write] Related work; **limitations/future work** (concurrent replay,
    LLM-nondeterminism logging, corpus breadth, the onboarding study).
C6. [verify] Reproduce the run 2-3x (TD + one checkpoint stable); fact-check every
    substrate claim against the code; critical read pass (optionally a subagent).
C7. [write] Post the **arXiv preprint** (establishes priority) and package the DSL
    plugin in parallel; submit to a venue.

## Done = submittable when

- The trading-desk office runs, terminates, and writes one checkpoint (A2-A3).
- The explain-back catches the stale-price gotcha held-out and Pat's fix lands (B3-B4).
- The debug dict + one English explanation transcript exist (A4, B5).
- The paper foregrounds the guarantees, uses the trading desk as the worked example,
  and scopes replay/debugging as designed-and-described with one concrete figure.

## Explicitly deferred (future work, not blocking)

Concurrent-with-live replay; a full interactive debugger; content-logging for LLM
nondeterminism; corpus breadth beyond the two offices; the onboarding user study;
the plant-a-gap full run (nice-to-have, not required for this paper).
