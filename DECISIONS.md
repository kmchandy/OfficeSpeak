# Decisions Log — Adaptive DSL Paper 1

Distilled from a multi-hour brainstorm on 2026-06-25.
For full reasoning behind each decision, see BRAINSTORM.md.
For the work that follows from these decisions, see PLAN.md.

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

## 17. Four patterns total in the translation table

Replaces the older "5 libraries" / "pattern catalog" framing.
The catalog is now a **translation table** with four
pseudocode-construct → graph-construct entries, plus refinement
patterns. Single document, always loaded into Claudette's
context.

| Pseudocode construct | Graph construct | Pattern name |
|---|---|---|
| `for each ... step 1 → step 2 → step 3` | Sequential edges through vertices | **pipeline** |
| `if X then send to A elif Y then send to B` | Vertex with named outports, one edge per branch | **router** |
| `while not done: ... send back to upstream` | Back-edge from later vertex to earlier vertex | **feedback** |
| Multiple `flow <name>:` blocks → same sink | Multiple chains converging at one sink | **multi-flow** |

Plus refinement patterns:
- `dedup-at-front` — add deduplicator before expensive processing
- `threshold-alert` — numeric threshold with binary downstream
- (others as they prove needed)

This replaces what we had been calling the "pattern catalog."
The new framing is honest: these aren't abstract patterns
Claudette must recognise; they're literal translation
correspondences between pseudocode and graph.

## 18. Pseudocode language grammar

The pseudocode Claudette produces uses a small fixed grammar:

```
inputs:
  - <var>: <source_registry_name>(<optional_args>)
  ...

[FLOW BLOCK — one or more]:

for each <item> from <var>:
  <step_id>: <verb> <object> → [reads <field>,] produces <field>
  ...
  [send to <sink_registry_name>(<optional_args>)]
  ...

# Variations:
# - if/elif/else after a classifier step (router)
# - while not <condition>: ... break/continue (feedback)
# - multiple `flow <name>:` blocks (multi-flow)
```

The `→ reads X, produces Y` annotations are required. They
flow to the per-vertex prompt-generation step (the agent's
prompt is told *"you'll receive a message with field X; produce
a message with field Y added"*).

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
| **debate** | Feedback (required deviation: pipeline cannot do cycles) | Demonstrates the while-loop → back-edge translation; only case where DSL's distributed-systems algorithms matter |
| **periodic_brief_pro** | Multi-flow (required deviation: pipeline cannot do independent flows sharing sink) | Demonstrates `flow X / flow Y / flow Z` → shared sink translation |

Five examples, each demonstrating one of the four patterns
(pipeline appears twice, in different agent-type contexts).
Job_hunter is dropped from the demo lineup as redundant with
loudness_monitor for pipeline coverage.

---

## Status

Decisions 1–14 are committed (from earlier sessions).
Decisions 15–23 are committed (from 2026-06-28 brainstorm) and
supersede where they overlap with 1–14.

Open questions and ideas explored but not committed live in
BRAINSTORM.md. Implementation plan is in PLAN.md.
