# Extending the Claude-Pat conversation (directions)

The paper's loop is build -> explain -> correct at the **wiring** level. These
directions extend the same conversation *downward* (to agent bodies) and *outward*
(to testing and to global state). Each is a natural extension of a capability we
already have, and each is demonstrable.

## 1. Claude explains a snapshot (global state) to Pat

A checkpoint is a **consistent global cut** — every agent's state plus the messages
in flight at that instant. Today Claude explains per-agent *tapes* (debug dict).
The snapshot is the *global* companion: "here is what the whole office looked like at
the moment things went wrong." Claude reads the snapshot (agent states + in-flight
channels) and narrates it in plain English. Useful when a bug is about *timing / what
was in flight*, not one agent's logic. Cheap: the snapshot files already exist.

## 2. Claude helps Pat improve each agent's body (prompt or Python)

The explain/correct loop currently stops at the wiring. Extend it to **bodies**:
- For an **LLM worker** (news-analyst): Claude and Pat iterate on the worker's
  prompt — Pat says "it's too trigger-happy on rumors," Claude tightens the prompt.
- For a **Python worker** (chart-analyst): Claude and Pat refine the rule — "use a
  20-minute average, and require a 0.5% breakout," Claude edits the code.
This is the highest-impact extension, because *content* bugs (a worker reasoning
badly) live in the body, and the body is where Pat's domain expertise actually
applies. It closes the loop at the layer the wiring loop can't reach.

## 3. Claude runs per-agent tests

Because each agent has a **contract** (declared reads/sends) and the office is
deterministic-by-display, a single agent can be tested in isolation. Claude can:
- feed an agent its **recorded inputs** (from the debug tape) and show outputs, or
- **generate test cases** for the agent from its job description and run them,
and explain pass/fail to Pat. Turns "debug a distributed office" into "unit-test one
worker," matching Pat's one-worker-at-a-time mental model. We already showed a Python
agent runs standalone (`chart_analyst.py`, `sliding_window_stats.py`), so this is a
short step.

## The theme (one sentence for the paper)

The same plain-English conversation that builds and explains the *wiring* extends to
refining agent *bodies*, testing *individual agents*, and explaining *global
snapshots* — so a non-programmer maintains a running distributed system end to end,
never leaving plain English.

## For this paper vs later

- This paper: keep 1-3 as **future work** (the build->explain->correct wiring loop is
  already a complete story). Optionally demonstrate **#3** with one example (cheap,
  and it reinforces the testability-from-determinism claim) if we want one more
  result.
- Later papers: #2 (body-refinement loop) is a paper on its own — the content-bug
  half of end-user maintenance.
