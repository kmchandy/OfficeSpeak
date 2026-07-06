# Decisions Log — Adaptive DSL Paper 1

Distilled from a multi-hour brainstorm on 2026-06-25.
For full reasoning behind each decision, see BRAINSTORM.md.
For the work that follows from these decisions, see PLAN.md.

## Goal (2026-07-02)

Empower an end user — *Pat*, a student or small-business owner, not a
programmer — to **develop and execute distributed systems** by
conversing with Claude in plain English.

Pat describes, in ordinary language, an *office*: a persistent network
of stateful agents that sense, deliberate, decide, and act. Claude
turns that description into a runnable office (a graph of message-passing
agents), and explains the office back to Pat in plain English; Pat
confirms or corrects; they iterate until the office is what Pat wants.
The office runs with the distributed-systems machinery Pat should never
have to think about — termination detection, checkpointing, and
deterministic coordination of shared state — so the system Pat gets is
not only runnable but reproducible and trustworthy.

The end-user contribution (a non-expert commanding a distributed system
in English, through a build → explain-back → correct loop) rests on a
systems contribution (making an LLM-generated stateful office correct
and reproducible). The second is what makes the first real.

## Status update (2026-07-01)

Three refinements, all consistent with the pseudocode-first workflow
(§15) below:

- **Canonical form is `graph.yaml`.** office.md is a derived, Pat-facing
  view, no longer generated on the execution path; the graph compiles
  directly to a DSL network (`officespeak/graph_to_dsl.py`).
- **The asyncio front-end was explored and dropped.** We briefly tried
  having Claude write an asyncio program and translating *that* to the
  graph. Recovering a dataflow graph from an imperative program is a
  compilation problem — precisely what the pseudocode Stage A exists to
  avoid, because asyncio hides the dataflow inside control flow. Stage A
  produces pseudocode; asyncio is not part of the pipeline.
- **No diamond.** Independent enrichers sequentialize into a pipeline
  (§16), so `situation_room` is a pipeline, not a broadcast-and-combine
  diamond. True parallelism is deferred to a later phase.
- **Explicit `send to` after every step.** A step `enriches` (adds
  fields) but does not forward on its own; each step routes its output
  with an explicit `send to`. This makes feedback and branching uniform
  (a back-edge is just another `send to`) and removes implicit
  fall-through.
- **Enrich-only, correctness-first; efficiency deferred.** Agents only
  add key–value pairs — messages grow monotonically and are never
  pruned mid-pipeline (only sinks project). Consequences are accepted:
  fat messages at the ends of long pipelines, and work done on items
  that are later discarded (an agent cannot be applied conditionally).
  These are bandwidth/compute costs, never correctness costs, because
  sinks read only the fields they need. Efficiency mechanisms
  (projection, conditional application) are a later phase.
- **Custom output sinks are hand-authored, outside spec→graph.** The
  generator maps English to a topology over a *fixed* sink vocabulary
  (terminal display + a generic `jsonl_recorder(path=…)`). Novel output
  targets Pat wants — databases, bespoke formats — are ordinary sink
  components she writes with Claude's help (message in → I/O) and plugs
  in at the editable graph. Topology generation (the research claim)
  stays automated; custom I/O adapters are conventional software and are
  explicitly out of scope for the automated pipeline. This is the same
  "fixed vocabulary + on-demand local components" pattern already used
  for roles (Stage C generation) and sources (app-local).

---

## 1. Research direction

Pivot from forced-advocacy MCQ research (killed by stage1_sanity)
to a demonstration of **Claude as architect of sense-and-respond
systems specified in English.**

## 2. Paper scope

**Phase A only.** Claude builds offices from English task specs.
Phase B (exogenous-event-aware control — Claude reads news/policy
to trigger structural restructuring) is deferred to a future
paper.

Paper message: *"Did you know an LLM can build sense-and-respond
apps from English specifications?"*

Target venue: AI workshop. Demonstration-paper genre — existence
proof, not characterisation.

## 3. Paper protagonist

**Claude** (the LLM), not DSL (the framework). The paper is a
demonstration of LLM capability when given the right substrate.
Title and abstract name a specific LLM version.

## 4. Success criterion

**"Imperfect but helpful."** A build that produces a working but
imperfect office that a human reviewer can inspect, understand,
and adjust is a useful artifact. Not *"Claude produces optimal
offices"* but *"Claude produces reviewable starting points."*

## 5. The five demonstration apps

| App | Type | Notes |
|---|---|---|
| Situation Room | Rebuild | Existing gallery app — low-risk validation |
| Job Hunter | Rebuild | One of Nyasha's apps — personal-data structure |
| Personal news brief | New | Daily-cadence text aggregation |
| Box office predictor | New | Prediction; keeps Phase B open |
| CDC FluView predictor | New | Prediction; public-interest framing |

Two rebuilds + three new builds. Two Phase B candidates without
committing to Phase B.

## 6. Architectural template

All five apps use one restricted template:

```
sources → text-enrichment diamond → numerical pipeline → sink
```

- Diamond: **single-pass** (not debate-style with internal
  feedback). Sync→gate loop is for dispatch only.
- Pipeline: optional feature extraction + optional output
  computation. Variable length.
- Same template across all five apps; only slot contents vary.

## 7. Two-layer split of adaptation labor

- **Numerical agents** handle their own parameter adaptation
  internally (classical algorithms: gradient descent, Bayesian
  optimisation, online learning). Lives inside each agent.
- **Claudette** handles structural changes (architectural
  restructuring).
- The paper does **not** claim Claudette is good at numerical
  parameter tuning.

### Implication for Phase A on prediction apps

For prediction apps (Box Office, FluView), Claudette builds
the *entire* office during Phase A — sources, text-enrichment
diamond, numerical feature-extraction pipeline, prediction
model, sink. The office produces predictions when run.

Claudette is *not* in the per-prediction control loop. Once the
office is built, the numerical components handle their own
internal adaptation as new data arrives. Claudette does not
return until Phase B (future paper), at which point she handles
exogenous-event-triggered structural changes.

So Phase A is the *whole distributed system*, including
numerics — Claudette as architect. All five demonstration apps
(text-output and prediction-output alike) are built the same
way: a single Phase A build, then the office runs unattended.

## 7a. The five libraries Claudette consults

Claudette draws on five distinct retrieval contexts during a
build. They are different in shape and serve different stages:

| # | Library | Contents | When Claudette uses it |
|---|---|---|---|
| 1 | **Component library** | Sources, LLM/Python transformers, sinks, combiners — each with YAML frontmatter + body | Stage 4 (component selection) |
| 2 | **Template library** | Topology shapes with named slots (diamond, pipeline, fan-in, router, …) | Stage 6 (topology assembly) |
| 3 | **Example library** | Worked offices with rationale + failures + samples | Stage 2 (precedent search) |
| 4 | **Design patterns document** | Principles, anti-patterns, heuristics | Stage 0 (pre-load, baked into meta-prompt) |
| 5 | **Task spec format reference** | Spec schema + well-written examples | Stage 1 (task analysis) |

Libraries (1)–(3) are collections of structured artifacts.
Documents (4) and (5) are single files. The component library
(1) may live in the DSL repo proper rather than in
adaptive_dsl/, since it overlaps with DSL's existing
component library and will be reused outside the research.

## 8. Component library schema

Every agent — LLM or Python — has YAML frontmatter:

| Field | Purpose |
|---|---|
| `purpose` | One-sentence what-it-does |
| `inputs` / `outputs` | Schema with English descriptions |
| `when_to_use` / `when_not_to_use` | Suitability characterisation |
| `usage_examples` | Past offices that used this agent |
| `modification_patterns` | How the agent can be customised |
| `internal_adaptation` | (Numerical agents only) What the agent auto-tunes |
| `computational_cost` | Tokens or compute per call |

Plus the prompt body (LLM agents) or code body (Python agents).

Seed library size: **~15 components** (4 sources, 5 LLM enrichers,
4 numerical transformers, 4 prediction models, 2 combiners).
Library grows as Claude invents and validates new agents.

## 9. Task specification format

Structured YAML header + free-form English description.

The header includes: prediction target, cadence, available
sources, success metric, reference accuracy. The free-form
description gives context, preferences, and qualitative guidance.

**The spec tells Claude *what* to build, not *how*.**
Decomposition into enrichers/features/models is Claude's job.

## 10. The 12-stage builder pipeline

1. Task analysis (Claude)
2. Precedent search (Claude)
3. Decomposition (Claude)
4. Component selection (Claude)
5. New agent design (Claude, per gap)
6. Topology assembly (Claude)
7. Self-critique (Claude)
8. Refinement (Claude)
9. Static validation (Python)
10. Smoke test (Python)
11. Fix loop (Claude, if needed)
12. Documentation (Claude)

Stages 1–8, 11, 12 are Claude calls; stages 9, 10 are Python.

## 10. Example library lives with the gallery, not duplicated

For each gallery app in Claudette's example library, the five
metadata files (`task.md`, `meta.yaml`, `rationale.md`,
`failures.md`, `samples/`) live alongside the app itself in
`dissyslab/gallery/apps/<app_name>/`. Not duplicated under
`NetworkOfThought/examples/` (the legacy adaptive_dsl path is superseded).

The `examples/` directory contains only:
- `INDEX.yaml` — registry of apps Claudette uses + paths
- `README.md` — explanation of the index pattern
- `external/` — metadata for non-gallery apps (e.g., Nyasha's)

Reasons: single source of truth for `office.md`; no drift; the
rationale + failures + samples documentation benefits any human
reader of the gallery, not just Claudette.

## 10a. The builder is named Claudette

The Claude agent that builds (and, in future Phase B, adapts)
sense-and-respond systems is named **Claudette**. The name
fits DSL's first-name convention for agents (Sasha, Eve, Sam,
Riley, Casey, Morgan, Alex, Jordan, …) and disambiguates the
agent (Claudette) from the underlying LLM (Claude).

The paper and code use "Claudette" for the builder role.

## 11. Controller (Claudette) configuration

- Identity: a specific frontier Claude version, named in the
  paper
- Meta-prompt: **fixed within a run**; varied across
  experiments (the prompt is itself an experimental artifact)
- State carried across stages: the accumulating build trace
  (Stage N's input is Stages 1..N-1's outputs)
- State carried across builds: component library + example
  library + design patterns doc (all persist on disk)

## 12. What the paper does NOT claim

- That the approach generalises to LLMs other than the one named
- That Claude produces optimal offices
- That Claude can characterise where the paradigm fails
- A contribution to feedback control theory
- A contribution to machine-learning training methodology
- That Phase B (exogenous-event-aware control) works yet

## 13. Adjacent prior work to cite

- **Khan et al. (2024)** "Debating with More Persuasive LLMs" —
  LLMs in feedback loops, but for judgment, not structural
  control
- **Kenton et al. (NeurIPS 2024)** "On scalable oversight" —
  adjacent control patterns
- **Voyager (Wang et al. 2023)** — continual capability
  extension; closest in spirit
- **AutoML / Neural Architecture Search** — adjacent paradigm,
  different substrate
- **MemGPT / Letta / Mem0** — agent memory for individual agents
- **LangGraph / AutoGen** — multi-agent frameworks where
  topology is Python-defined, not adapted

The contribution sits in the intersection: LLM as structural
author + natural-language specs + small message-passing agents +
inspectable English artifacts.

## 14. Intellectual lineage to acknowledge

The architectural substrate has a four-decade pedigree:
dataflow models (Arvind, Dennis, 1970s) → CSP (Hoare, 1978) →
distributed dataflow / termination (Chandy-Misra, 1985) →
actors (Hewitt, Agha, 1990s) → microservices (2000s) →
reactive streams (2010s) → this work (2020s).

The paper positions itself as adding *LLM-driven structural
control* on top of an established architectural pattern, not
as inventing the substrate.

---

# Decisions from 2026-06-28 brainstorm

The following decisions supersede or refine earlier ones. They
emerged from a multi-hour brainstorm focused on what Claudette
should actually do (vs what we'd been imagining she'd do).

## 15. Pseudocode-first workflow (supersedes the 12-stage pipeline)

Claudette's design process has three cognitive stages, not twelve:

| Stage | Activity | Mechanism |
|---|---|---|
| **A** | Read Pat's English description; write pseudocode in the DSL pseudo-language | Claudette (hard cognitive step) |
| **B** | Translate pseudocode to graph (sources / vertices / sinks / edges) | Wrapper (deterministic Python) |
| **C** | Apply refinements from the refinement catalog | Claudette (per-refinement) |

Plus per-vertex prompt generation (the existing smoke-test-1
capability, applied per vertex in the graph), file-writing
(`create_agent_from_prompt`), `dsl build`, `dsl run`, and a fix
loop on errors.

The full path:

```
Pat's English description
    ↓ Claudette (Stage A)
Pseudocode in DSL pseudo-language
    ↓ Wrapper (mechanical, Stage B)
Graph (sources / vertices / sinks / edges)
    ↓ Claudette per-vertex (Stage B for agents)
Agent prompts
    ↓ create_agent_from_prompt wrapper
Role files in target office
    ↓ dsl build
Compiled run.py
    ↓ dsl run
Running persistent S&R system
    ↓ on error: feed back to Claudette → fix
Working system
```

The cognitive load concentrates in Stage A. Everything else is
either mechanical translation or per-vertex work we've already
validated.

## 16. Pipeline-of-enrichers is the default; ignore efficiency

For most apps, the appropriate topology is a pipeline of small
enricher agents. Each agent reads a JSON message, adds new
field(s), passes the message downstream. Sequential by default.

We ignore latency and parallelism concerns. The "diamond"
pattern (broadcast to N enrichers + synchroniser) is dropped
from the catalog except as it appears inside feedback patterns
(debate-style). This simplifies Claudette's choices: pipeline
is the baseline; deviations from pipeline happen only when
*structurally* required (router, feedback, multi-flow).

The honest cost: when an app needs low latency, the produced
system runs slower than necessary. Acceptable for research
demonstration.

The honest gain: massively simpler decision-making; pipelines
are the natural shape of pseudocode; success rate increases.

## 17. Three primitives; patterns are emergent

The pseudocode language has **three primitives**, not four named
patterns:

| Primitive | Pseudocode form | Role |
|---|---|---|
| **Sequence** | The `for each` body — one step line per row | Order-dependent processing chain |
| **Branch** | `if/elif/else` after a classifier step | Conditional routing |
| **Send-to** | `send to <target>` | Edge to a sink (registered name) or to a vertex (declared step ID) |

From these three primitives, common graph shapes *emerge* — they
are not separately identified by Claudette:

| Emergent shape | How it appears in the pseudocode |
|---|---|
| **Pipeline** | A `for each` body with sequential steps and no branching |
| **Router** | A `for each` body where an `if/elif/else` directs messages to different sinks |
| **Feedback** | A `for each` body where an `if/elif/else` sends a message back to an earlier vertex |
| **Multi-flow** (Phase 2) | Multiple top-level `flow <name>:` blocks |

Earlier framings of this work treated pattern recognition (*"this
is a diamond"*, *"this is a feedback loop"*) as a separate
cognitive step that Claudette had to perform before writing the
graph. That framing is superseded. There is no
pattern-identification step. Claudette writes pseudocode using the
three primitives; the graph's shape is whatever the pseudocode
produces.

Specifically, the "diamond" (broadcast to N enrichers + a
synchronizer) is **not expressible** in this grammar at all. Per
§16, independent enrichments are sequentialized into a pipeline.
If true parallel processing is ever needed, it will be a Phase 2
extension (multi-flow with explicit synchronization), not a Phase
1 construct.

Refinement patterns (`dedup-at-front`, `threshold-alert`, etc.)
remain useful labels for human discussion but are not separate
constructs in the grammar. They are post-hoc names for
combinations of the three primitives.

## 18. Pseudocode language grammar

The pseudocode Claudette produces uses a small fixed grammar:

```
inputs:
  <var>: <source_registry_name>(<arg>=<value>, ...)     # primitive input
  <var>: merge(<var>[, <var>]*)                         # derived input (1+ args)
  ...

for each <item> from <var>:
  <step_id>: <verb> <object> → [reads <field>,] enriches <field>
  ...
  [if <condition>:
     <body>
   [elif <condition>:
     <body>]*
   [else:
     <body>]]
  send to <target>(<arg>=<value>, ...)
  ...
```

Where:

- `<var>` is a pseudocode-level identifier (local to the pseudocode;
  does not appear in the graph).
- `<source_registry_name>` and `<target>` (when targeting a sink)
  are names in DSL's source/sink registries.
- `<target>` may also be a vertex step ID declared earlier in the
  loop body — in which case the resulting edge is a back-edge
  (feedback). See §24.
- `<step_id>` is a local identifier for a step line; renamed to a
  positional vertex ID (`v0, v1, ...`) by the wrapper.
- `<verb> <object>` is a noun-phrasable pair like `extract entities`
  that becomes a role name (`entity_extractor`).
- `enriches <field>` is the only step verb. It writes one field to
  the message (overwriting on re-entry — see §24).

The grammar deliberately does **not** include:

- `while not <condition>:` — feedback is expressed via `if + send
  to <vertex_id>`, not a separate looping construct.
- `produces <field>` — earlier proposals had a second verb meaning
  "replace the message with a fresh dict." Dropped to keep the
  grammar minimal. The corresponding architectural rule is below.
- `flow <name>:` blocks — multi-flow is Phase 2.

**Agent and sink contracts (the rule that makes `produces`
unnecessary):**

- **Every processing vertex enriches.** A vertex receives a JSON
  message, sets one field on it (per its `enriches X` clause), and
  forwards the **full enriched message** to its outport(s). No
  vertex ever drops fields. Pass-through is automatic and total.
- **Sinks project.** A sink receives the full message and reads
  whichever fields it needs — typically just the latest
  enrichment (`briefing`, `verdict`, etc.) plus identifying
  metadata (`url`, `source`). The other fields are ignored.
- **Consequence.** Pat does not need to think about "which fields
  flow forward." All of them do. Pat only thinks about which
  field each vertex adds and which fields each sink consumes. This
  is what removes the `produces` distinction.

The `→ reads X, enriches Y` annotation is required on every step
line. It flows to the per-vertex prompt-generation step (the
agent's prompt is told *"you receive a message with field X; set
field Y on the message"*).

Why pseudocode is the right intermediate:

- LLMs generate it fluently (training data is full of
  algorithm pseudocode)
- It externalises the design reasoning (CoT applied to system
  design)
- The translation to graph is mechanical
- It is human-inspectable at every level

## 19. Graph schema (Claudette's output of Stage B)

Flat graph: four lists, no human-friendly names.

```yaml
sources:
  - id: s0
    name: <registered_source_name>
    params: {...}

vertices:
  - id: v0
    role: <role_name>
    params: {...}
    purpose: <one-line English description>

sinks:
  - id: k0
    name: <registered_sink_name>
    params: {...}

edges:
  - { from: [<node_id>, <port>], to: [<node_id>, <port>] }
  ...
```

IDs are positional (`s0/s1/.../v0/v1/.../k0/k1/...`), not human
names. The prefix tells the kind (source, vertex, sink). The
graph is the artifact that compiles to a Network object via
the runtime.

## 20. Contribution claim — sharpened

> *We demonstrate that an LLM (Claude) can produce executable
> persistent multi-agent sense-and-respond systems from
> Pat-style English descriptions, by externalising its
> decomposition reasoning as pseudocode in a small structured
> language and then mechanically translating that pseudocode to
> a runnable agent network. The pseudocode is human-readable;
> the translation is deterministic; the resulting system runs
> continuously and its design is inspectable at every level —
> English description, pseudocode, graph, agent prompts,
> output. We apply this methodology to a set of gallery apps
> and characterise where it succeeds, where the LLM needs
> adjustment, and where the methodology runs out. The substrate
> (DSL) provides the small message-passing agents with English
> contracts that make this possible, plus the distributed-systems
> algorithms (Chandy–Misra termination, Chandy–Lamport snapshots)
> needed for the cases where the pseudocode includes feedback
> loops.*

Five distinct properties of the contribution:

1. **Pseudocode as cognitive pivot** — externalising
   decomposition in a form LLMs generate fluently
2. **Mechanical translation eliminates syntax-compliance risk**
3. **Multi-level inspectability** — every artifact is readable
4. **Application to persistent S&R systems** — substrate class
   understudied in LLM-agents literature
5. **Honest scope** — pipelines as default; non-pipeline
   patterns when structurally required

## 21. No baseline comparison

The contribution is an *existence proof*: Claude can build
persistent S&R systems from English descriptions, via the
methodology described. The contribution is not "this method
beats some other method."

We therefore do not need baseline comparisons (no-pseudocode,
direct-English-to-graph, human-designed, etc.). The paper
demonstrates the methodology works; characterisation of *when*
it works is the empirical contribution.

This makes the experiment simpler: run the methodology on N
gallery apps; report success, partial success, failure for
each; characterise the failure modes.

## 22. Honest framing: CoT applied to system design

The contribution is NOT "NoT beats CoT." It is:

> *We apply CoT-style decomposition thinking to a new domain:
> the design of persistent multi-agent sense-and-respond
> systems. The decomposition methodology transfers; the
> artifact it produces is different — a persistent network of
> agents rather than an ephemeral chain of reasoning steps.*

Most apps are structurally pipeline-equivalent to CoT.
Persistence, inspectability, and the substrate's support for
non-DAG cases (feedback) are the distinguishing properties,
not the topology shape per se.

## 23. The five demonstration apps

Updated lineup (replaces earlier mix):

| App | Pattern shown | Why included |
|---|---|---|
| **situation_room** | Pipeline (default; was diamond, now sequential per #16) | Canonical text-enrichment baseline |
| **loudness_monitor** | Pipeline with numeric agents + threshold-alert refinement | Canonical Python-agent example; tests pseudocode language on non-LLM agents |
| **inbox_triage** | Router (required deviation: pipeline cannot do routing) | Demonstrates the if/elif/else → named-outports translation |
| **debate** | Feedback (required deviation: pipeline cannot do cycles) | Demonstrates `if + send to <earlier_vertex>` → back-edge translation (see §24); only case where DSL's distributed-systems algorithms matter |
| **periodic_brief_pro** | Multi-flow (required deviation: pipeline cannot do independent flows sharing sink) | Demonstrates `flow X / flow Y / flow Z` → shared sink translation |

Five examples, each demonstrating one of the four patterns
(pipeline appears twice, in different agent-type contexts).
Job_hunter is dropped from the demo lineup as redundant with
loudness_monitor for pipeline coverage.

---

## 24. Feedback by back-edge with overwrite semantics

When the pseudocode contains `if ... send to <vertex_id>` where
the vertex was declared earlier in the loop body, the wrapper
emits a back-edge in the graph. The result is a cyclic graph —
messages circulate from later vertices back to earlier ones.

The semantics on re-entry are:

- **Message shape is unchanged.** A message is still a
  scalar-valued JSON dict (same as DAG apps). No lists, no
  versioned keys, no embedded history.
- **`enriches X` overwrites X.** On every write — first pass or
  re-entry — the value of field X is replaced by the agent's
  output. The previous value is lost.
- **Termination is the pseudocode author's responsibility.** The
  grammar does not enforce termination. Pat expresses it via
  convergence conditions (`if verdict == "approved": send to k0
  else: send to v0`) or an explicit iteration counter (a counter
  step plus `if iter >= 3: send to k0 else: send to v0`).
- **Debug tracing is a future runtime feature.** Full per-message
  history is not part of the message shape. It will be captured
  by an opt-in runtime trace layer (enable with `DSL_TRACE=1`),
  separate from message semantics. Until that is built, only the
  latest state of each field is visible at runtime.

This design choice prioritises pedagogical simplicity (one verb,
scalar fields, no list-vs-dict cases) and uniformity (DAG and
feedback apps look identical from an agent's perspective). The
cost is loss of intermediate history at runtime — recoverable
later via the trace layer when it ships.

The per-vertex prompt generator (Phase 1 Step 5) detects cyclic
vertices via SCC analysis on the graph and includes a clause in
those vertices' prompts noting that fields may be present from a
previous iteration. Non-cyclic (DAG) vertices have unchanged
prompts.

Of the 11 gallery apps in the demonstration lineup, 10 are DAGs
and only debate has a cycle. The overwrite semantics is sufficient
for all 11. (This was the empirical check that motivated choosing
this design over the append-only-list alternative discussed in
BRAINSTORM.md.)

This decision supersedes the `while not <condition>:` construct
proposed in earlier drafts of §18.

## 25. The persistent artifact chain

The "multi-level inspectability" claim in §20 is not a slogan; it
is realised by **a chain of durable files on disk** that Claudette
produces and any reader can open.

After Claudette finishes building an app, the app directory
contains:

| File | Stage | What it is |
|---|---|---|
| `spec.md` (or `spec.txt`) | Input | Pat's English description (the prompt Claudette was given) |
| `spec.pseudo` | Stage A | The pseudocode Claudette wrote — her externalised decomposition reasoning |
| `graph.yaml` | Stage B | The mechanical reduction of the pseudocode to a flat graph (sources / vertices / sinks / edges) |
| `office.md` | Stage B' | DSL's office file, generated from the graph; what `dsl build` reads |
| `<role>.md` (one per vertex) | Stage C | The per-vertex agent prompts (or, for Python vertices, the role wrapper) |

Each file is human-inspectable. Each file explains the file
immediately below it:

- `spec.md` → why the pseudocode looks the way it does.
- `spec.pseudo` → why the graph has the vertices and edges it has.
- `graph.yaml` → what office.md must contain.
- `office.md` → what roles must exist and how they connect.
- `<role>.md` → what each agent does, in English (the contract for
  the LLM).

This is the operational meaning of "Claude explains what she does."
A reader can pick any level of the chain and audit it. A reader
who disagrees with a design choice can point at the specific file
where the choice was made.

**Contrast with CoT.** Chain-of-Thought reasoning is visible during
a single inference but does not survive it. The reasoning trace is
not part of the system being built; if you delete it, the system
still runs (and was never described). In NoT, the artifacts *are*
the system: deleting `spec.pseudo` deletes the design rationale;
deleting `graph.yaml` deletes the structural specification;
deleting `office.md` deletes the executable instructions. None of
these files is optional.

**Implementation commitment.** All five files are persisted to disk
by default. None is hidden behind a debug flag. The end-to-end
driver (Phase 1 Step 6) writes the full chain on every successful
build. Removing any one of them from default output would weaken
the inspectability claim and is not allowed without an explicit
decision to do so.

This decision means we keep `graph.yaml` as a persisted artifact
(not just an in-memory data structure between parser and office
writer). It is part of the contribution, not just an internal
implementation detail.

---

## Status

Decisions 1–14 are committed (from earlier sessions).
Decisions 15–25 are committed (from 2026-06-28 / 2026-06-29
brainstorms) and supersede where they overlap with 1–14.

Open questions and ideas explored but not committed live in
BRAINSTORM.md. Implementation plan is in PLAN.md.
