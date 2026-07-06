# Paper draft v0 — abstract and one-page contribution

> **STATUS:** Superseded multiple times. See `reframing_log.md` for
> the trajectory of the contribution claim. The most recent
> (post-v6) framing is "substrate-agnostic English design with
> two demonstrated runtime substrates (asyncio + DSL)."
>
> This file is kept as a reference point only.

**Working title (placeholder):** *English as the Durable Layer: An Architecture for Iterative Non-Programmer Development of Distributed Sense-and-Respond Systems with an LLM Partner*

**Purpose of this document:** to test, by writing it, whether the contribution we have built is actually a contribution. If we read this and are not convinced, the work needs more thought before more time is invested. If we are convinced, this becomes the skeleton for the full paper.

---

## Abstract

Large language models can produce working distributed sense-and-respond (S&R) systems directly from English specifications. We do not extend this capability. We describe instead an architecture and methodology targeting a distinct goal: enabling Python-literate users without distributed-systems expertise to iteratively develop, modify, and share such systems with an LLM as their development partner.

The architecture has two layers. A durable specification layer — an English *office* description plus an English *role* description per agent — is what the user reads and edits. An ephemeral implementation layer of Python agents is generated and maintained by an LLM (Claude). A message-passing substrate, DisSysLab, supplies the distributed-systems machinery (agents, message routing, state management, snapshot and resume) so the user need not learn concurrency primitives. Modifications happen at the specification layer; the implementation regenerates as needed.

We evaluate the architecture on a library of validated S&R applications and on case studies of iterative refinement sessions in which a target user converges with the LLM on a desired system over a small number of rounds. We measure convergence speed (rounds to a user-accepted result), library reuse (fraction of agents drawn from existing roles), and modification patterns (what kinds of changes the methodology supports cleanly).

We argue that this packaging of LLM capability is useful for a specific set of conditions — multi-iteration development, non-programmer modification, and cross-user composition — and explicitly note that simpler approaches (direct LLM-generated Python) suffice when these conditions do not hold. The contribution is the packaging, the iteration discipline, and the empirical characterization of where the packaging earns its keep; not the underlying LLM capability.

---

## Contribution (one page)

We make four specific claims and we concede three things our work could be mistaken for. Both sets are deliberately small and concrete.

### Four claims

**1. Two-layer specification with an LLM maintainer is a viable development model.**

The architecture separates a durable English design layer (office.md and per-agent role.md files) from an ephemeral Python implementation layer maintained by an LLM. Users read and modify only the English layer. The LLM regenerates the Python when the English changes and produces English explanations of the Python when asked. The English IS the source of truth; the Python is bookkeeping. We demonstrate this model works in practice: every gallery application in our library has a Python implementation generated and maintainable in this manner.

**2. Iteration converges to user intent at the English level over a small number of rounds.**

The user iterates with the LLM by editing the English layer or by asking the LLM to edit it. Each iteration is a small, design-scoped change ("change the display sink," "have the classifier also read the headline," "add a Slack alert for critical items"). Across a small number of rounds — empirically reported in our case studies — the resulting office converges to a user-accepted result. The measurement we report is *convergence speed*: the number of rounds, not first-try accuracy. This reframes the success criterion in line with how iterative software development actually works.

**3. A small, accessible distributed substrate suffices for the target class of applications.**

DisSysLab (DSL) — a Python library providing message-passing agents, message routing, state management, and snapshot/resume — is sufficient to host every S&R application in our gallery. The substrate is the only piece of distributed systems the user is exposed to, and only indirectly through its agent and message abstractions. A user who can write a Python function can have a distributed agent by writing the role's English contract and letting the LLM and substrate handle the rest.

**4. A library of validated compositions supports cross-user reuse.**

Agent roles, office structures, and source/sink connectors form a library that one user can build on from another user's work. The seed library demonstrates the pattern with [N] applications and [M] distinct roles. We document the library and describe the reuse patterns it supports, including modification of an existing role for a new context and composition of an existing office with new sinks.

### Three concessions

- **We do not claim that an LLM cannot produce equivalent S&R systems directly from English without this scaffold.** It can. Sequential or concurrent Python, in a single program, runnable, behaviorally equivalent. The contribution is what the scaffold adds beyond the working program: inspectability, modifiability, and iteration accessible to non-programmers.

- **We do not claim novelty in decomposition or in any individual agent prompt.** Both follow from baseline LLM capability. A "severity classifier" prompt is something anyone can write in a few minutes. Our contribution is the scaffolding around the prompts, not the prompts themselves.

- **We do not claim performance benefits.** The methodology accepts inefficiencies in exchange for inspectability — pipeline serialization where parallelism would work, LLM-generated code overhead where hand-tuned code would be tighter. These are tradeoffs, not innovations.

### Why this packaging matters

The Python-literate user who does not know distributed systems can use the architecture to build, modify, and share S&R applications without learning concurrency primitives, without reading Python implementations, and without committing to a particular software engineering toolchain. The user remains in domain language throughout the development cycle. The LLM does the implementation work and is the partner across iterations. The library provides the reuse path.

We do not argue this is the only way to support this user. We argue it is a particular way that works, characterized empirically, with explicit limits and explicit concessions.

### Empirical contribution

The empirical work is descriptive, not comparative. We evaluate the architecture along three axes:

| Axis | Measure | What it shows |
|---|---|---|
| Convergence | Number of iteration rounds to reach user-accepted office, across case studies | Whether the iteration model is practical for real changes |
| Library reuse | Fraction of agents in each office drawn from the seed library | Whether composition pays off as the library grows |
| Modification patterns | Categorization of the English-layer changes users actually request | What kinds of changes the methodology supports cleanly |

The case studies illustrate; they do not benchmark against alternatives.

### Position in existing work (sketch)

The architecture is closest in spirit to two bodies of work:

- *LLM-assisted programming tools* (e.g., GitHub Copilot, Cursor) iterate code at the source-code layer. We push the durable layer up to natural-language design specifications and use the LLM to maintain the source.
- *Agent-composition frameworks* (e.g., LangChain, AutoGen) provide programmable primitives for LLM-agent systems but assume programming-level engagement. Our substrate provides similar agent primitives, but factors out the implementation through the English design layer so non-programmers can engage.

Our contribution is the combination — durable English design, ephemeral LLM-maintained implementation, accessible distributed substrate, and iteration discipline — characterized as a methodology rather than a feature of any one component.

---

## Self-criticism (to be addressed by the empirical work and revision)

Three claims a skeptical reader is most likely to push back on:

**"This is just code generation with extra steps."**

Partial truth. The extra step is durable English as the design layer that non-programmers can read and modify. Without this, code generation is opaque to anyone but the developer. With this, the artifact is auditable in domain language. The "extra step" *is* the contribution.

**"What stops the Python and the English from drifting out of sync?"**

The LLM. The Python is regenerated from the English on demand. There is no separate maintained copy of the Python; it is always derived. Drift is impossible because there is nothing to drift from.

**"How is convergence measured? When does an iteration session end?"**

A session ends when the user states the office matches their intent. We report rounds per session and a brief qualitative description of what each round addressed. This is descriptive empirical work; we are not setting a benchmark.

---

## Why this draft might still be wrong

This draft assumes the empirical results will support the four claims. The most likely failure modes are:

- **Convergence is slow.** If users need 20+ rounds for typical changes, the iteration model is not the productivity claim it sounds like. We would need to investigate whether the friction is in the LLM, the substrate, or our methodology.

- **Reuse doesn't materialize.** If each new office requires writing new role files from scratch, the library claim collapses. We would need to investigate whether roles are too app-specific to compose or whether our role granularity is wrong.

- **Pat-like users don't actually use the English layer.** If users find it easier to read the Python and ignore the English contracts, the two-layer design is solving a problem they don't have. We would need to investigate who the audience actually is.

If any of these turns up in the case studies, the paper needs revision before the empirical work justifies the framing.

---

## Reading test

If we read this draft and ask "is this a useful contribution?" — what's the answer?

I think it's a contribution worth investing the remaining empirical work into. It is modest, falsifiable, and honest about what it does not claim. It targets a specific user class and a specific evaluation regime. It does not depend on the LLM doing something the LLM can't already do; it depends on the *packaging* being useful for the user class, which is the empirical question.

The risks are concrete and listed. The path from here to a finished paper is small case studies and library curation — both within the scope of what the substrate already supports.

If we (you) read this and feel we are pretending to a contribution that isn't there, the draft has done its job: it surfaced the gap before the empirical work locked it in.

Mani, when you read this, please write your reactions back as you go — what you find honest, what you find inflated, what you would cut. That will tell us whether the draft is right and what to revise.
