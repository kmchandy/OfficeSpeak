# Prompt v2 backlog

Findings to fold into the office prompts (`prompt.md`, `prompt_local_state.md`,
`prompt_explain.md`) **after** the rough-understanding experiments finish. The
v1 prompts stay frozen while runs are in progress, so results across offices stay
comparable. Add items freely; Mani will add more.

Each item notes which run exposed it and whether it is graph-level (in scope for
the prompts) or agent-internal (out of scope — belongs to an agent's own
prompt/code, not the wiring).

---

## The graph / agent-code boundary (scope note — read first)

Claude produces a **graph** (agents + wiring). What each agent does *internally*
(its LLM prompt or Python) is a separate layer and is **not** part of our
experiment. This boundary decides what the explain prompt should and shouldn't
flag:

- **Graph-level (surface it):** who exists, who sends to whom, who keeps which
  state, who waits for whom, fan-in / fan-out, one-at-a-time, ask-and-wait.
- **Agent-internal (out of scope):** how an agent reasons, whether it "learns,"
  how it weighs its inputs. The graph only needs to provide the *hooks* (state +
  incoming edges); the behavior itself is the agent's prompt.

Corollary used below: "try to do better over time" is agent-internal. The graph
is complete for it once each analyst has his own model-portfolio state and the
data feed. So an explanation is right to surface "each keeps a separate practice
portfolio" (a state-ownership choice) and right to stay silent on "does he
actually improve" (behavior).

---

## Items

### 1. Add a plain-word gloss for fan-out / broadcast  (explain prompt)
Source: investment_club run_1 + run_2 explanations.
`prompt_explain.md` glosses `fair_merge` (fan-in) but has no entry for fan-out —
one item going to several agents, each keeping its own copy. The explainer had to
improvise ("reaches everyone at once"). Read fine, but leaves consistency to
chance. Fan-out is deterministic (no choice), so it needs NO new registry entry
in the build prompts — only a plain-word line in the explain glossary, e.g.:
"one item going to several workers at once (each keeps its own copy)."
Graph-level. Low risk.

### 2. Add "per-agent copy of something that sounds shared" to the Baked-in checklist  (explain prompt)
Source: investment_club run_1 (needed calling out twice to land).
Instruction 4 lists categories to surface (one-at-a-time, who-keeps/reads shared
info, who-waits, back-and-forth) but not this one: when several agents each keep
their *own* copy of a thing a reader would assume is shared (three separate
practice portfolios vs one club book). It is a genuine state-ownership choice and
non-obvious, so it belongs on the checklist rather than left to judgment.
Graph-level.

### 3. Keep behavior OFF the Baked-in checklist — do NOT add "asked-to-improve-but-not-wired"
Source: run_1 vs run_2 asymmetry, resolved.
Earlier I considered adding "asked to improve but not acted on" as a checklist
category. Dropping it: adaptation is agent-internal (see boundary note), so it is
not a wiring choice and a graph explanation shouldn't be required to flag it.
run_1 staying silent on "try to do better" was correct; run_2 flagging it reached
slightly into agent internals. What the checklist SHOULD carry is item 2 (the
state-ownership hook), not the behavior. Recorded so we don't re-add it by
mistake.

### 5. Make joins at multi-input consumers explicit — never rely on the gate  (build prompt + static check)
Source: analytical explain-back of investment_club run_1 (the "three spots" note).
run_1 gave Don two inbound edges (item from Gus, argument-pair from Meg) that lined
up ONLY because the gate kept one item in flight — an implicit merge that silently
breaks if the gate is relaxed or under composition. This is the exact failure mode
the project exists to prevent (implicit vs explicit coordination). Two fixes:
- **Build prompt:** add a rule — "if a worker has two or more inbound streams that
  must correspond, either join them explicitly (merge_synch) or have an upstream
  agent carry them together; do not rely on the gate to align them." The clean fix
  for investment_club was to have Meg carry the item forward so Don has ONE inbound.
- **Static check:** "any agent with >=2 inbound data edges and no explicit
  merge_synch/select -> flag." This is statically detectable and is the FOURTH job
  for the unified structural checker (with liveness M6, unreachable-write M5,
  contract-conformance E1b). See EXPERIMENTS_PLAN E3b / DIRECTIONS #2.

### 6. Two explain artifacts, not one: Pat-explanation vs coordination-review
Source: same run. The Pat-facing explanation (confirm/correct) missed the implicit
join at Don; a developer-facing "where did rendering force me to paper over
something" pass found it. These are different jobs. Consider a separate
**coordination-review** prompt (developer-facing, NL) that audits for implicit
joins, dead fan-out edges, and unused inputs — overlapping the static checker but
in prose. Keep it OUT of the Pat explanation, which must stay jargon-free.

### 7. Fan-out should be minimal and justified  (build prompt)
Source: same run (Herb's premature fan-out). run_1 broadcast the item to Herb, who
did nothing until Don proposed. Rule for the build prompt: "fan out an item only
to agents that act on it immediately; an agent that acts later should be handed the
item at that point (demand-driven), not put on the broadcast." After applying this
plus item 5, investment_club's fan-out shrank to exactly {Warren, Bill} — the two
who need the item at once. Strengthens item 1's fan-out gloss with a build-side
rule.

### 8. Deliver a diagram to Pat, not just prose  (build + explain prompts)
Source: Mani. Pat should see a **graph** alongside the explanation — a picture of
who talks to whom helps her confirm/correct structure faster than prose alone. We
already have `officespeak/graph_viz.py` (to_mermaid/to_html). Requirement: the
build and explain outputs should include (or be accompanied by) a rendered graph.
Example produced by hand: `investment_club/reference_graph.mermaid`. Open task:
render from the office text/graph.yaml automatically so every run ships a diagram.

### 4. Meta-lesson: one worked example under-tests the prompt
Source: both runs.
support_desk (the single worked example in all three prompts) contains a linear
pipeline + one shared record + a gate. It does NOT contain fan-out or
per-agent-vs-shared state — exactly the two spots (items 1, 2) where v1
underspecified. Lesson for the write-up and for prompt design: coverage of the
worked example(s) predicts where explanations get shaky. Consider a second worked
example that exercises fan-out and per-agent state, or note the gap explicitly.
