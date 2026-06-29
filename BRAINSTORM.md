# Adaptive DSL — brainstorm notes

Captured 2026-06-25 over a multi-hour brainstorm. The previous
research direction (forced advocacy on MCQ) was killed by the
stage1_sanity experiment; this is the replacement direction.
Not yet a design doc — those are deferred to a future session.
This document preserves the ideas, framings, and scoping decisions
while they are fresh.

This is a substantial revision of an earlier draft. Major changes:
the paper's protagonist is the LLM (Claude), not DSL; the framing
borrows from feedback control theory; the experimental scope is
narrowed to a demonstration paper rather than a characterization
study.

---

## Origin and pivot

Three prior research directions were ruled out during the
brainstorm:

- **Debate** (panellists deliberating to consensus). Ruled out
  because debate is intrinsically sequential and does not need a
  concurrent agent-network framework. DSL would be incidental
  rather than essential to the research.
- **Forced advocacy on MCQ.** Ruled out by the stage1_sanity
  experiment: CoT beat advocacy on the same model at the same
  compute, including the "high-precision" single-defender bucket
  (CoT 82% vs advocacy 52% on Qwen 2.5 7B on 50 MMLU problems).
- **Cascade (advocacy as router + CoT fallback).** Ruled out by
  the same data: cascade cost 4.58× CoT for worse accuracy
  because advocacy carried no signal CoT did not already have.

The replacement direction has two properties the prior directions
lacked: (a) concurrency is *essential* (continuous sense-and-
respond, not bounded computation), and (b) DSL's English-specified
topology is the contribution-bearing artifact, not an
implementation detail.

---

## The protagonist shift: Claude, not DSL

This is the single most important framing decision.

The HN/Reddit story for DSL was:
> *"Here is a framework for building distributed agentic
> applications in English. You — the developer — describe an
> office and the framework runs it."*
> Protagonist: **DSL**. Claude is one of many possible backends.

The paper's story is:
> *"Here is an LLM that builds and continuously restructures a
> working multi-agent sense-and-respond system. The system is
> specified in English so the LLM can read and modify it. The
> framework provides the substrate that makes this possible."*
> Protagonist: **Claude**. DSL is the substrate that enables
> Claude's contribution.

These are different products of the same technical work. The
audiences, the venues, the comparisons, and the reviewers are
all different. The paper is essentially a capabilities study of
an LLM: it shows what Claude can do when given the right
substrate.

---

## The core idea, in one paragraph

> We exhibit a paradigm in which an LLM acts as a structural
> controller in continuous feedback with a long-running
> multi-agent sense-and-respond computation. The framing borrows
> from feedback control — plant, sensor, controller, error — but
> differs from classical control in two ways. First, the
> controller does not adjust inputs to a fixed plant; **it edits
> the plant itself** — adding agents, modifying prompts,
> rewiring connections, inventing new components. Second, these
> modifications take place **while the plant continues to run**;
> there is no separate training phase. The plant and the
> controller share a common medium: natural language. The
> plant's topology and the input/output contracts of each
> component are specified in English; the controller reads this
> specification, observes the plant's outputs and recent errors,
> and writes English edits back into the specification, which
> take effect on the running plant. We do not claim a
> contribution to feedback control theory or to machine-learning
> training methodology. The contribution is the working
> demonstration of this paradigm and a qualitative
> characterization of the conditions under which it applies.
> Because plant specification, controller proposals, edit
> history, and rationales are all in English, a human reader can
> inspect at any moment what the system is, what it was, and why
> each change was made.

---

## The architectural substrate: small message-passing agents with English contracts

A third foundational claim, structurally prior to the other two:
**the paradigm only works because the underlying architecture is
small message-passing agents whose behaviour is specified in
English.** Each of the three adjectives — *small*,
*message-passing*, *in English* — is load-bearing.

### Why "small"

Three reasons, in increasing depth:

1. **Context budget.** Claude has bounded context. A library of
   N small agents (each described in ~100 tokens) fits
   comfortably; a library of N large agents (each ~5000 tokens)
   does not. The library size at which Claude can hold the full
   menu in working memory is roughly inverse to per-agent
   description size.

2. **Composability.** Small agents combine in more ways than
   large ones. An agent that "does everything for news
   processing" is hard to combine with others — its boundaries
   are unclear, its responsibilities overlap. Five small agents
   (fetch, deduplicate, classify, summarise, score) compose
   freely. This is the **Unix philosophy at the agent level**:
   do one thing well, compose via pipes (here: messages).

3. **Reasoning load on the controller.** Claude's reasoning task
   is "given this error, which combination of agents would
   help?" If each agent has a narrow well-defined purpose, the
   reasoning reduces to recognition + selection. If each agent
   has a vague broad purpose, the reasoning becomes "well, agent
   A could maybe handle part of this, plus..." — which is much
   harder and produces worse choices.

### Why message-passing, not general concurrency

Message-passing distributed systems have specifications you can
write in a paragraph; general concurrent systems do not. Consider
what a shared-memory agent's spec would need to include: memory
locations read and written, timing of operations, atomicity
guarantees, memory consistency model, lock acquisition order,
race-condition possibilities. These are nearly impossible to
write in concise English. They are nearly impossible for *humans*
to reason about, let alone an LLM controller.

A message-passing agent's spec needs only:
- What it receives (typed messages on named ports)
- What it sends (typed messages on named ports)
- The mapping from input messages to output messages

That is it. The composition story reduces to a single thing:
which output port feeds which input port. No locks, no order, no
memory.

This is why DSL was already the right substrate for this work
before we knew what work we would do with it. The framework's
architectural choice — message-passing agents with named ports —
is exactly the choice that makes English specifications
tractable, and therefore the choice that makes LLM control
possible.

### Why "in English" — and what exactly is in English

The agent contract covers two things, both in English:

1. **The message shapes** — what fields each input message has,
   what fields each output message has. This is the structural
   contract (close to a type signature). The runtime uses this
   for wiring without type errors.
2. **The behaviour** — what the agent does with input messages
   to produce output messages, including `when_to_use` and
   `when_not_to_use`. This is the semantic contract (close to a
   docstring). The controller uses this to reason about
   composition.

Both are needed. The structural contract supports the runtime;
the semantic contract supports the LLM controller. The
behavioural-English part is what distinguishes this from
ordinary typed-component libraries.

### Intellectual lineage

The architectural substrate has a four-decade pedigree in CS:

| Era | Idea | Reference |
|---|---|---|
| 1970s | Dataflow models for parallel computation | Arvind, Dennis |
| 1978 | Communicating Sequential Processes | Hoare |
| 1985 | Distributed dataflow / termination detection | Chandy–Misra |
| 1990s | Actor-model maturation | Hewitt, Agha |
| 2000s | Microservices architecture | (industry) |
| 2010s | Reactive streams, event-driven systems | Akka, Kafka |
| 2020s | LLM control over English-specified message-passing agents | *this work* |

The paper can honestly position the contribution as: *"We apply
LLM-driven structural control to the class of message-passing
dataflow systems that has been studied in distributed computing
for four decades. The architectural simplicity of message-passing
makes natural-language specification of agent behaviour
tractable, which in turn makes LLM-mediated composition
tractable. We do not invent the substrate; we exhibit the kind
of control that becomes possible when the substrate is already
English-specifiable."*

This positioning matters for three reasons:

1. It places the work in a tradition that takes architectural
   choices seriously. Reviewers from distributed systems will
   recognize the lineage and understand immediately why
   message-passing matters.
2. It distinguishes the work from the LangChain / AutoGen line.
   Those frameworks add abstractions on top of LLMs; this work
   adds LLM control on top of an established architectural
   pattern. The direction of abstraction is different.
3. It gives the work historical weight. The contribution is not
   "look, agents!" — it is "the right architectural substrate
   for LLM-controlled systems has been understood for forty
   years; here is what becomes possible when you combine that
   substrate with a capable LLM controller."

---

## The feedback-control framing — borrowed, not contributed to

We use the picture from feedback control theory as an organizing
mental model:

```
                    ┌────────────────────────────────┐
                    │           PLANT                │
   Sources ───────▶ │  Long-running, persistent      │ ─── outputs
                    │  multi-agent sense-and-respond │
                    │  computation specified in      │
                    │  English                       │
                    └────────────────────────────────┘
                              │ outputs
                              ▼
                    ┌────────────────────────────────┐
                    │           ERROR                │
                    │  Outputs − ground truth        │
                    └────────────────────────────────┘
                              │ error signal
                              ▼
                    ┌────────────────────────────────┐
                    │        CONTROLLER (LLM)        │
                    │  Reads plant spec, history,    │
                    │  errors. Writes structural     │
                    │  edits in English.             │
                    └────────────────────────────────┘
                              │ English edits
                              ▼
                    (back to PLANT — restructures it in place)
```

Two deliberate departures from classical control:

1. **The controller edits the plant.** Classical control adjusts
   inputs to a fixed plant. Here the controller restructures the
   plant itself — adds components, modifies their behavior,
   rewires connections.
2. **No separate training phase.** Classical control and ML
   training have offline phases where the controller is designed
   or trained. Here the controller is *fixed* (a particular LLM
   with a fixed prompt); only the plant's specification changes
   over time.

We do **not** claim a contribution to feedback control theory.
No stability proofs, no convergence rates, no Lyapunov analysis.
The vocabulary is borrowed because it crisply names what is
happening; the formal apparatus is not invoked.

---

## What the paradigm is — and what it is not

The paradigm is most cleanly characterized by negation:

| It is not | Because |
|---|---|
| A chatbot | Persistent operation across many cycles, not bounded request-response. |
| Reinforcement learning | The controller's weights are not updated by rewards; the locus of learning is in the *plant's specification*, not the controller. |
| Machine-learning training | Adaptation happens while the plant runs; there is no separate training phase. |
| Classical feedback control | The controller modifies the plant's structure, not inputs to a fixed plant. |
| AutoML | AutoML constructs numerical pipelines offline; this restructures multi-agent networks online, in English. |
| Memory-augmented LLM agents | The LLM is not gaining memory; the multi-agent plant is being restructured. |
| Self-modifying code | The modifications are made to a separate symbolic system (the plant) by an external controller (the LLM), not to the controller itself. |

What the paradigm *is*, positively: a continuous-time feedback
loop in which an LLM, with fixed weights, acts as the structural
author of a running multi-agent computation, with all artifacts
of authorship expressed in natural language.

---

## System architecture — two-layer hybrid pipeline

```
                       LAYER 1 — text enrichment (diamond)
                       ┌─────────────────────────────────┐
   Sources ──────────▶ │ Broadcast to N enricher agents  │
   (news, blogs,       │ (sentiment, NER, classification,│
    finance feeds,     │  topic, summarisation, ...)     │
    social, ...)       │            ▼                    │
                       │   Text moderator combines       │
                       │   → JSON dict + narrative +     │
                       │     normalised feature vector   │
                       └─────────────────────────────────┘
                                      │
                                      ▼
                       LAYER 2 — numerical processing (pipeline)
                       ┌─────────────────────────────────┐
                       │ Stage 1: feature extraction     │
                       │   (FFT, smoothing, normalisation)│
                       │            │                    │
                       │ Stage 2: feature transformation │
                       │   (lag construction, scaling)   │
                       │            │                    │
                       │ Stage N: prediction model       │
                       │   (ARIMA / Ridge / RF / LLM)    │
                       └─────────────────────────────────┘
                                      │
                                      ▼
                                  Prediction
```

Design decisions:

- **Layer 1 is a diamond** — broadcast to independent enrichers
  combined by a moderator. Mirrors the situation_room / debate
  patterns already in DSL's gallery. Restricts the search space
  enough to be tractable while remaining expressive.
- **Layer 1 moderator emits three interface formats**:
  structured JSON dict, English narrative, normalised feature
  vector. Downstream agents pick whichever interface fits.
- **Layer 2 is a pipeline** — sequential, because numerical
  processing often needs each stage's output as the next
  stage's input. Pipeline is structurally right for this layer
  even though Layer 1 is a diamond. Pipeline naturally subsumes
  any sequential decomposition (feature extraction → modeling →
  calibration); no need for an explicit two-diamond stack at
  this scope.
- **Library mixes LLM and Python agents.** Some tasks (FFT,
  sklearn regression, ARIMA) are not LLM tasks; Python is the
  right substrate. Some tasks (sentiment, summarisation, NER)
  are LLM tasks. The controller treats both uniformly through
  English contracts.

---

## The controller (Claude)

| Aspect | Decision |
|---|---|
| Identity | Claude (a specific version, named in the paper). |
| Prompt | **Fixed within a run, varied across experiments.** The prompt is itself an experimental artifact. |
| State carried across adaptations | Office trajectory + library + bounded scratch pad. |
| Action space | ADD, REMOVE, REWIRE, MODIFY_PROMPT, CREATE_AGENT. |
| Output per adaptation | Structured proposal: edit + reasoning + *predicted effect on next-period error* + confidence. |
| Cadence | Match prediction cadence; adapt every K predictions where K ≈ 5–20. |
| Stop condition | Controller may emit "no change" — this is a valid action. |

### Why fixed prompt

Reproducibility, clean ablations, no controller-level drift,
scientific honesty about what the system is. The scratch pad
gives content-level learning; a changing prompt would add
meta-level learning, which is a confounder for the first paper.

### The "predicted effect" field

Each controller proposal includes the controller's *prediction*
of how the edit will affect next-period error. This makes the
experiment measure controller **competence** (was the edit good)
and controller **calibration** (did it know what was good). The
calibration is a free second-order signal that can be tracked
over the course of a run.

### Bounded scratch pad

The scratch pad is the controller's persistent working memory:

- Hypotheses being tested
- Components ruled out and why
- Observed patterns in the prediction task
- Calibration notes ("I was wrong about my last 3 edits;
  weight my predictions accordingly")
- Pending experiments

Bounded in size (LRU or summarisation) so the token budget stays
stable. Without this bound, the "fixed prompt" claim leaks
because the effective input grows over time.

---

## The component library

Every agent — LLM or Python — has YAML frontmatter with a
unified schema:

```yaml
---
purpose: "..."
inputs: { name: "type — English description" }
outputs: { name: "type — English description" }
when_to_use: "..."
when_not_to_use: "..."
usage_examples:
  - "Used in box_office app to gauge audience buzz."
  - "Used in job_hunter app to gauge company sentiment in news."
modification_patterns:
  - "Add domain-specific lexicon (e.g., 'mention awards as positive')."
  - "Request entity-conditional sentiment."
  - "Constrain output to fixed label set."
internal_adaptation:    # for numerical agents only
  - "Retunes (p, d, q) on rolling 1-year window every 4 weeks."
  - "Signals 'structural break suspected' when fit quality
     drops > 30%."
computational_cost: "..."
---
```

The schema's load-bearing fields:

- `when_to_use` / `when_not_to_use` let the controller reason
  about agents it has never used.
- `usage_examples` give the controller a pattern-matching anchor:
  "this agent was used in office X for Y; my task resembles X,
  so this agent is plausible."
- `modification_patterns` give the controller a vocabulary for
  customisation: "I know this agent can be specialised in these
  ways." In Phase A this seeds initial customisation; in Phase
  B it bounds the action space.
- `internal_adaptation` (numerical agents only) tells the
  controller what the agent does *on its own*. The controller
  does not have to manage local parameter tuning. The controller reads
"ARIMA is bad for structural breaks" and matches against its
scratch-pad note "we've had three structural-break errors
recently" → swaps ARIMA out for a regime-aware model.

This is **a typed component library with self-describing English
semantics** — every component has not just an API but a
behavioural description the controller can read. The unified
schema across LLM and Python agents is itself a small
contribution: the controller does not care whether an agent is
LLM or Python; both are typed components with English semantics.

### Library growth

The library is *not static*. The controller can invent new
agents (with stiff JSON-format prompts, validated by trial run
before commit). Surviving inventions are added to the library.

This makes the library a form of **accumulated wisdom expressed
as English prompts**. After running for weeks on box office, the
library reflects what the controller has learned about that
domain.

### Verification of invented agents

Two safeguards:
- **Trial run.** New agent runs on 3–5 cached inputs; check
  output validity; reject and explain failure if malformed.
- **Robust downstream.** Moderator gracefully ignores enrichers
  whose output is malformed.

Stiff prompts (explicit JSON schema, mandatory output format)
are part of the invention discipline.

---

## The two-layer split of adaptation labor

A late refinement that materially changes the paper's claim.

Adaptation in this paradigm divides cleanly between two layers,
each with its own appropriate controller:

| Layer | Best controller | Why |
|---|---|---|
| **Fast / local / numerical** — hyperparameter tuning, ensemble weight adjustment, online learning of model parameters within a component | Classical adaptive algorithms (gradient descent, Bayesian optimisation, online learning) — lives *inside* each numerical agent | These problems are solved. An ARIMA agent can internally retune (p, d, q) on rolling windows; a Ridge agent can adjust α on recent residuals. LLMs will never beat 50 years of optimisation theory at this. |
| **Slow / global / structural** — which enrichers exist, which models are considered, when a regime has changed and the architecture needs restructuring | LLM (Claude) reading English specifications and exogenous context, proposing English edits | This is where qualitative reasoning over architecture and outside context matters. The LLM's strengths apply directly. |

This is the right division. It mirrors how brains and
organisations work: local synaptic plasticity is handled by
neurons themselves through local rules; structural plasticity
and cognitive flexibility are handled by higher-level signals.
The LLM sits in the higher layer; numerical adaptive algorithms
sit in the lower layer.

### Implication for the component library

Each numerical-agent library entry adds a new field:

```yaml
internal_adaptation:
  - "Retunes (p, d, q) on rolling 1-year window every 4 weeks."
  - "Detects fit-quality drop > 30% and signals 'structural
     break suspected' to controller."
```

This tells Claude what the agent does *on its own*. Claude does
not have to manage local parameter tuning. Claude is told what
the agent will handle without intervention, and what the agent
will signal up when it cannot.

### Implication for Phase B

Phase B is **not** parameter tuning. Phase B is structural
restructuring driven by qualitative context — including
**exogenous context that numerical controllers cannot see**.
The unique capability the LLM adds is reading news, policy
announcements, expert commentary, sentiment shifts — *qualitative
information that no numerical controller has access to* — and
deciding when this context implies the existing system's
assumptions are violated.

A classical adaptive controller can detect that residuals are
growing. Only an LLM can read a news article saying "the Federal
Reserve announces emergency rate cuts" and propagate the
implications to a prediction system. This is what the LLM
contributes that classical control fundamentally cannot.

The COVID box office example illustrates: in early 2020, news
is full of pandemic coverage. Claude reads it, infers that
theatrical box office is about to be catastrophically disrupted,
proposes restructuring (e.g., "the prediction model can no
longer assume normal theatrical operations; switch to a model
that treats this as a structural break"). Classical adaptive
control would have stayed in its model class while errors grew
unboundedly.

### Candidate naming for Phase B

"Phase B" is internal scaffolding language. For the eventual
paper, more precise names:

- **"Exogenous-event-aware control"** — captures the unique
  capability precisely.
- **"Context-driven restructuring"** — emphasises the LLM's role.
- **"Outer-loop control"** — places it correctly in a control
  hierarchy.

Working name: **exogenous-event-aware control**, because it
names the information source (exogenous events) that
distinguishes the LLM's contribution.

### Why Phase B should probably be a separate paper

The exogenous-event-aware claim is more ambitious than the
Phase A claim. It requires demonstrating not just that Claude
can edit a system, but that Claude correctly interprets news
and policy events for the system's domain. That is a much
stronger claim and needs more evidence.

For paper 1, Phase A is the work. Phase B is a future paper
informed by everything Phase A surfaces.

---

## Paper scope: Phase A only, with five apps

The first paper covers Phase A only — Claude as builder of S&R
systems from English specifications. Phase B (exogenous-event-
aware control) is future work, possibly a separate paper.

### The success criterion: "imperfect but helpful"

Claude's builds need not be perfect. A build that produces a
working but imperfect office that a human reviewer can inspect,
understand, and adjust is itself a useful artifact. The paper
measures not *"did Claude produce the optimal office"* but
*"did Claude produce an office that runs, makes coherent design
choices, and provides a reviewable starting point."*

This lowers the success bar in a principled way and aligns with
how LLMs are best used in practice: as first-draft generators
that humans then refine, not as oracles that produce final
artifacts.

It also defangs the "Claude's design is suboptimal" critique.
The paper does not claim optimality; it claims utility.

### The five demonstration apps

| App | Why included | Source of task spec |
|---|---|---|
| **Situation Room** | Rebuild of an existing gallery app — low-risk, demonstrates Claude can reproduce known-good designs | Existing gallery README |
| **Job Hunter** | Rebuild of one of Nyasha's apps — has personal-data structure, demonstrates Claude handles configurable office | Existing gallery / Nyasha's repo |
| **Personal news brief** | New design — daily-cadence text aggregation, demonstrates Claude builds from a fresh task description | Task spec drafted for the paper |
| **Box office predictor** | New prediction app — keeps Phase B open without committing to it | Task spec drafted for the paper |
| **CDC FluView predictor** | New prediction app — public-interest framing, different signal mix | Task spec drafted for the paper |

The mix is deliberate: two rebuilds (lower-risk validations),
two prediction apps (forward-leaning, Phase B candidates), one
new daily-cadence app (variety).

If we ever do Phase B, box office and FluView are already in
place as candidates. If we never do Phase B, the five-app demo
stands on its own.

---

## What Phase A actually demonstrates

The paper measures Claude as builder. For each of the five
apps, the experimental procedure is:

1. Write the structured task spec (header + free-form).
2. Run the 12-stage builder pipeline on the spec.
3. Inspect the resulting office, build trace, rationale, and
   any newly-invented agents.
4. Run the resulting office on cached or live sample inputs.
5. Document successes, failures, and human adjustments needed.

### What we measure

Qualitative more than quantitative:

- **Does the office run?** Static validation passes; smoke test
  produces sensible output.
- **Are the design choices coherent?** A reader of the build
  trace can follow why Claude made each decision.
- **What patterns emerge across apps?** Looking at the five
  offices side-by-side, what does Claude do consistently? What
  does it vary?
- **Where does Claude need help?** Document the human
  adjustments required after the build. This is itself a
  finding.
- **How does the library evolve?** Track new agents invented
  during the five builds and assess whether they are genuinely
  novel or near-duplicates of existing ones.

### What we deliberately do not measure

- Whether the offices produce optimal outputs.
- Whether Claude can adapt offices over time (this is Phase B,
  future work).
- Whether the paradigm generalises to LLMs other than Claude.
- The boundary between tasks Claude can build for and tasks it
  cannot.

These are deferred. The paper claims that Claude can produce
*useful starting points*, not optimal artifacts.

---

## Preconditions — when the paradigm applies (positive framing)

The paradigm demonstrated here requires:

1. **A system whose structure and components can be naturally
   expressed in concise English.** The plant specification is
   small enough that the LLM can read the whole thing in
   context. (This is why the paradigm does not apply to
   large-scale safety-critical systems such as missile defence,
   whose specifications run to thousands of pages.)

2. **A prediction task with ground truth that arrives at
   intervals comparable to the desired adaptation cadence.** The
   adaptive loop needs feedback events densely enough in time to
   drive adaptation. Tasks where ground truth arrives weekly or
   daily are well-suited; tasks where ground truth arrives once
   per decade (earthquake severity) are not.

3. **A domain that tolerates iterative experimentation and
   bounded error during adaptation.** While the controller is
   exploring edits, the plant may produce worse predictions for
   a period. This is acceptable in forecasting, analytics, and
   research; it is not acceptable in safety-critical control or
   medical decision support.

4. **An LLM controller with sufficient capability to read system
   specifications and propose meaningful edits.** The paper uses
   a specific frontier-class model; we do not claim the
   paradigm generalizes to less capable models.

5. **Acceptable cost of running the controller alongside the
   plant.** Each adaptation event costs LLM tokens. The paradigm
   is suitable for offline backtests and for online systems
   where controller cost is small relative to system value.

Outside these preconditions — real-time safety-critical systems,
rare-event prediction, ultra-large specifications, resource-
constrained edge deployment — the paradigm does not apply, and
we do not claim it does.

---

## Limitations explicitly acknowledged

Beyond the preconditions above, three substantive limitations
of the work itself:

- **Verification is limited.** The paradigm does not formally
  verify that LLM-edited offices are *correct* — only that they
  reduce measured error. Edits could introduce subtle bugs that
  the error metric does not catch (e.g., the controller learns
  to predict the right answer for the wrong reason, or removes
  a component whose value is not visible in short-term error).
  For some applications this is acceptable (forecasting); for
  others it is not (decision support, medical, financial).

- **Reproducibility across LLM versions.** The results are for a
  specific Claude version at a specific point in time. We claim
  the *paradigm* generalizes; we do not claim that re-running
  the experiment with a different LLM would produce the same
  offices or the same edit decisions.

- **Boundaries are not characterized.** We do not investigate
  for which classes of systems the paradigm works and for which
  it fails. The preconditions above are an a priori
  characterization, not an empirical one. Empirical boundary
  characterization is left for future work.

---

## The paper's positioning — what it claims and what it does not

Claims:
- The paradigm exists as a working demonstration.
- An LLM controller can build initial offices, adapt them in
  response to error, and produce inspectable English artifacts
  describing what it did and why.
- On the demonstration tasks shown, the adaptive arm exhibits
  measurable improvement over the static arm.

Does not claim:
- That the approach generalizes to all LLMs.
- That the approach generalizes to all sense-and-respond
  systems.
- A contribution to feedback control theory.
- A contribution to machine-learning training methodology.
- A characterization of where the approach fails.
- Better predictions than domain experts or commercial systems.

Target audience: AI workshop. The message is *"Did you know an
LLM can build and continuously adapt sense-and-respond apps?"*
The contribution is opening this question with conviction and
compelling examples, even if the contribution is limited in
scope.

This is the genre of the **first paper in a line**. The pattern
in AI is well-established: existence-proof first (Voyager, ReAct,
Toolformer, AutoGPT-style demonstrations), characterization
later. Subsequent papers — by us or by others — will study
where the paradigm works, where it fails, and how to harden it.

---

## Adjacent prior work

To be cited, distinguished, and respected:

- **Khan et al. (2024)** "Debating with More Persuasive LLMs
  Leads to More Truthful Answers" — LLMs in feedback loops, but
  for judgment, not structural control.
- **Kenton et al. (NeurIPS 2024)** "On scalable oversight with
  weak LLMs judging strong LLMs" — adjacent control patterns,
  binary debate setting.
- **Voyager** (Wang et al., 2023) — continual learning in
  Minecraft; an LLM that accumulates skills. Closest in spirit
  to what we're doing: an LLM extending its own capability
  library over time. Our work differs in that the artifact being
  restructured is a multi-agent network, not a skill set.
- **AutoML / Neural Architecture Search** — automated pipeline
  construction, but for numerical pipelines, offline, without
  natural-language reasoning.
- **MemGPT / Letta / Mem0** — persistent memory for individual
  agents; we restructure a network of agents.
- **LangGraph / AutoGen** — multi-agent frameworks where
  topology is Python-defined and not adapted at runtime.
- **RLHF / Constitutional AI** — feedback-driven adaptation,
  but centralised training rather than distributed,
  natural-language-mediated restructuring.

The combination of (a) LLM as structural controller, (b)
natural-language plant specification, (c) continuous restructuring
during operation, (d) English-mediated edits with rationales, is
the gap.

---

## Open questions to settle for the design doc (next session)

1. **Which 2–3 prediction tasks** for the demonstration?
   Candidates: box-office (weekly), CDC FluView (weekly), grid
   demand (daily/hourly), 6-month forward oil price (monthly).
   First choice probably box office — text-driven, no
   market-efficiency confound, clean public data.

2. **Initial library size and content.** Seed with ~10 generic
   agents (sentiment, NER, summarisation, FFT, ARIMA, Ridge,
   moving-average, etc.) or smaller? Generic or domain-
   specialised?

3. **Adaptation cadence.** Burn-in length per office version
   (K = 5? 10? 20?). Event-driven adaptation (on surprise) vs
   fixed-interval adaptation.

4. **Controller prompt v1.** Sketch the actual prompt. The
   prompt is the experimental artifact and will probably need
   2–3 iterations before the experiment runs.

5. **Reward shaping.** Plain MSE? MSE + parsimony penalty?
   Directional accuracy separately from magnitude?

6. **How to present LLM-built artifacts in the paper.** Offices
   as code listings? Trajectories as diff sequences? Library
   as a summary table? This is a presentation question but it
   matters — the paper's qualitative argument lives in how
   readable these artifacts are.

7. **Backtest mechanics.** How to "rewind" historical data
   without leakage. Source-by-source as-of timestamps; care
   with news archives that contain post-hoc analysis.

---

## Deferred ideas (thesis-scope, not paper-1 scope)

These are good ideas that came up during the brainstorm and
should not appear in paper 1:

- **Two controllers competing** with the losing prompt evolved
  toward the winner. Evolutionary controller selection.
- **Hierarchical controllers** — separate controllers for Layer 1
  and Layer 2, with a meta-controller above. Credit assignment
  across layers becomes a real problem to solve.
- **Brain-inspired multi-timescale adaptation** — fast (in-call),
  medium (prompt updates), slow (topology) with neuromodulator-
  style global signals coordinating across timescales.
- **Sleep cycles** — periodic offline consolidation passes that
  promote useful short-term patterns to long-term role
  descriptions.
- **Homeostatic plasticity** — agents that self-regulate firing
  rate (over-utilised summariser raises its threshold).
- **Transfer learning across tasks** — library learned on box
  office, evaluated on flu prediction.
- **Cross-network ensembles** — parallel pipelines (numerical
  layer) combined by a final moderator.
- **Surprise-driven adaptation** — controller fires only on
  large prediction errors (event-driven rather than fixed-
  interval).
- **Controller self-calibration** — controller's confidence in
  its proposals is itself learned and improves over time.
- **Comparison across LLM controllers** (Claude vs GPT-4o vs
  Llama 405B) — characterising the capability threshold for
  serving as structural controller.
- **Snapshot semantics for learned state** — Chandy-Lamport
  extension for plants whose specification updates continuously.
  (Mani's territory; arguably a paper of its own.)
- **Educational deployment** — undergraduates building personal
  adaptive S&R systems. A separate paper, SIGCSE venue.

These are all interesting. Any of them could be a thesis chapter
or a follow-on paper. None should be in paper 1.

---

## Status (as of 2026-06-25)

- **Brainstorm:** ongoing.
- **Design doc:** deferred.
- **Implementation:** not started.

---

# Session 2: 2026-06-28 — sharpening the Claudette design

Major shift in framing: away from "characterising adaptation"
toward a sharper existence proof, with a much simpler
methodology and a tightened contribution claim.

## The trajectory of thinking, in order

The brainstorm in this session followed roughly this arc, with
each step refining the previous:

1. **The "stage abstraction" was our scaffolding, not
   Claudette's natural representation.** We had been organising
   examples around gate / pipelines / synchroniser / moderator /
   feedback. This is useful for our reasoning but it's
   abstract-LLM-speak. Stages stay as a *thinking tool* in
   walkthrough prose; the artifact Claudette produces is
   simpler.

2. **Vertex IDs (`v0`, `v1`, ...) for Claudette's output, not
   human names (Sasha, Eve, Sam).** Names are a Pat-facing
   affordance with no semantic content for an LLM. Removing
   them eliminates a generation burden and prevents irrelevant
   associations.

3. **Graph as the output format.** Flat lists of sources,
   vertices, sinks, edges. Mechanically translatable to
   Network construction. Replaces the stage-organised YAML.

4. **The pattern catalog becomes a translation table.** Instead
   of teaching abstract patterns Claudette must "recognise,"
   we provide a one-document translation reference: *if your
   pseudocode looks like this, your graph looks like that.*
   Single document, always in context.

5. **Pipelines of enrichers as the default.** Ignoring
   efficiency, most apps are pipelines. Diamond and
   broadcast-merge become optional optimisations (we dropped
   them from the catalog except inside feedback patterns).
   Four baseline patterns: pipeline, router, feedback,
   multi-flow.

6. **Examples carry the patterns; rules embedded in context.**
   Don't write "always use a synchroniser when paths
   converge." Instead show, in the relevant walkthrough, *"we
   need a synchroniser here because..."*. The rule lives where
   it applies, not as standalone instruction.

7. **The "how to design X" walkthrough format** captures
   Mani's actual design process — step-by-step reasoning from
   spec to graph. This is process-trace data, which teaches
   reasoning better than result-justification.

8. **CoT analogy made explicit.** Claudette writes pseudocode
   first; the pseudocode is essentially CoT for system design.
   This is honest about what we're doing: applying CoT-style
   decomposition reasoning to a different domain (persistent
   S&R systems instead of single answers).

9. **Flowcharts → pseudocode → graph as a translation
   chain.** LLMs produce pseudocode fluently; the translation
   to graph is mechanical. The cognitive work concentrates in
   the English→pseudocode step.

10. **The pseudocode language has a small fixed grammar.** Six
    constructs: `inputs:`, `for each from`, sequential step
    lines, `if/elif/else`, `while/break`, `flow` blocks. Each
    construct maps deterministically to graph elements.

11. **Stage 3 (pattern identification) is redundant.** The
    pseudocode IS the pattern. Labels add no information.
    Process is two cognitive steps: English → pseudocode,
    pseudocode → graph (mechanical). The catalog is a
    reference for the second step.

12. **No baseline comparison needed.** Contribution is
    existence proof. We don't need to claim better-than-X; we
    need to claim Claude can do this.

13. **The five demos are pipeline (twice — text + numeric),
    router, feedback, multi-flow.** One pattern per demo,
    covering the catalog and the agent-type range
    (LLM-driven and Python-wrapped).

## What this simplifies

| Earlier framing | Sharpened framing |
|---|---|
| 5 libraries (component, template, example, patterns doc, spec format) | Translation table + agent catalog + example walkthroughs |
| 12-stage builder pipeline | 3 cognitive stages (pseudocode write, graph translate, refine) plus per-vertex prompt generation and the build/run/fix loop |
| Pattern catalog with 7+ patterns | Translation table with 4 baseline patterns + refinements |
| Stage-organised network YAML | Flat graph (sources/vertices/sinks/edges) |
| Human-named vertices (Sasha, Eve) | Positional IDs (v0, v1, s0, k0) |
| "NoT beats CoT" framing | "CoT applied to system design" framing |
| Baseline-comparison framing | Existence-proof framing |
| Variable-shape topology (diamond + pipeline + ...) | Pipeline default; non-pipeline only when structurally required |

Every change reduces variance, simplifies Claudette's task,
and produces a more honest research claim.

## What remains hard

Three real challenges that didn't dissolve:

1. **Iteration loop.** Claudette needs to receive runtime
   errors and produce corrected output. The infrastructure
   exists (wrapper + smoke test + dsl build/run); the loop
   itself needs implementation.

2. **Per-agent prompt generation.** The smoke-test-1 capability
   handles one agent at a time. For a graph with N vertices,
   we need to call it N times. Orchestration is small but
   needs to exist.

3. **The pseudocode language for Python-wrapped agents.**
   LLM-agent steps (`extract entities`) map cleanly to verb-noun
   roles. Python-wrapper agents (`apply FFT`, `compute moving
   average`, `classify with BirdNET`) need a similar
   pseudocode form. Loudness_monitor example will surface
   what's needed.

## Status

- **Brainstorm:** committed. Decisions captured in DECISIONS.md
  sections 15–23.
- **Implementation:** ready to begin. Next concrete step is
  building loudness_monitor as the second walkthrough using
  the pseudocode-first format (see PLAN.md).
- **Target audience:** still the Claude/AI community. Vehicle
  could be a workshop paper, a blog post, an open-source
  artifact, or all three. Vehicle choice deferred until after
  the experiment runs.
