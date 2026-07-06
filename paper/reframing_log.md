# Reframing log

Tracks how the contribution claim has evolved as we've stress-tested it.
Each entry is a self-criticism that survived and changed the claim, or
a defence that didn't survive and was dropped.

---

## v0 — initial framing (when we wrote draft_v0)

**Claim:** Claude + a meta-prompt builds distributed sense-and-respond
systems from English specifications. The pseudocode language is the
mechanism that makes this reliable.

**Audience:** Python-literate users without distributed-systems
expertise.

**Empirical evaluation:** Convergence speed, library reuse,
modification patterns.

---

## v1 — after Q1 (LLMs can do this directly)

**Self-criticism:** Claude can already produce working S&R systems in
asyncio Python from English specs without our pseudocode language or
meta-prompt. The decomposition reasoning is baseline LLM capability.

**Survived claims:**
- *Two-layer specification model*: English (office.md + role.md) is
  the durable design layer; the implementation is ephemeral and
  maintained by the LLM.
- *Iteration at the English level*: Pat modifies English; Claude
  regenerates implementation.
- *Substrate provides distributed-systems machinery* (DSL).

**Dropped claims:**
- "We extend LLM capability." (We don't.)
- "Our pseudocode language is necessary." (It isn't — we use what
  Claude naturally produces.)
- "Claudette is a special agent." (It's just Claude.)

---

## v2 — after Q2 (Claudette is just Claude)

**Self-criticism:** We were building a custom "Claudette" persona with
600+ lines of meta-prompt. With the reframing in v1, Claudette is just
Claude with ~50 lines of contextual prompt. There is no distinct agent.

**Survived claims:** Same as v1.

**Dropped claims:**
- "Claudette is a distinct agent we built." (No, it's Claude with
  context.)

---

## v3 — after Q3 (iteration not first-try)

**Self-criticism:** Measuring "first-try accuracy" is the wrong success
metric. Software development is iterative even for programmers; non-
programmers will use the methodology iteratively too.

**Survived claims:**
- Iterative development model.
- English as the durable artifact across iterations.

**New claims:**
- Convergence over rounds is the right success criterion.

---

## v4 — after office metaphor surfaces (Mani's point 2 on draft_v0
feedback)

**Self-criticism:** The pedagogical contribution — the office / job
description / org chart vocabulary — was not articulated in v3. Pat
knows offices; she does not know co-routines. Choosing the
vocabulary IS a contribution.

**Survived claims:** All from v3.

**New claims:**
- The office mental model (organising the system as an office with
  role-as-job-description employees) is a pedagogical contribution
  in its own right.

**Dropped claims:**
- "Convergence speed is measured." (Mani: no, demonstrated qualitatively.)
- "Library reuse is a primary claim." (Mani: not central; new specs
  are easy to write.)
- "Python-literate users." (Mani: just non-programmers.)

---

## v5 — after Sketch reframing (use what Claude already produces)

**Self-criticism:** Even after dropping the pseudocode language, we
were over-engineering. Claude produces good Python directly — including
the class definitions, the instantiations, AND the prompts for LLM
agents. There is no need for a separate per-vertex orchestrator stage
to write prompts; Claude writes them inline.

**Survived claims:** All from v4.

**Architectural simplification:**
- The Sketch (Python AST format) is Claude's only output.
- Stage C per-vertex orchestrator becomes unnecessary; the Sketch
  contains the agent classes with full implementations including
  LLM prompts.
- The framework extracts a graph from the Sketch's AST and emits
  office.md.

---

## v6 — after asyncio-vs-DSL self-criticism (current)

**Self-criticism:** If Pat just iterates in English and Claude maintains
the Python, why does she need DSL at all? She could iterate in English
to produce asyncio Python and skip DSL entirely. Our "distributed
substrate" claim was unjustified for users who don't need the
distributed-systems properties.

**Mani's response:** Two-tier framing.
1. Pat iterates in English to produce asyncio programs (default).
2. If she wants distributed-systems properties (per-agent LLMs, process
   isolation, snapshot/resume, fault tolerance, termination detection
   on cycles), the same English design compiles to DSL.

**Survived claims:**
- Office mental model.
- English as durable design layer.
- Iterative development discipline.

**New / sharpened claims:**
- **Substrate-agnostic design.** The same English specification (and
  the same Sketch produced from it) targets both asyncio and DSL.
- **Two-tier deployment story.** Pat chooses a runtime substrate
  based on her needs; the design layer is shared.

**Dropped framing:**
- "DSL is essential." It is not. DSL is one of two demonstrated
  substrates, the one that adds production-grade properties.

---

## Current contribution claim (post-v6)

> We describe an iterative English-driven development model for
> sense-and-respond systems. Users specify and modify the system as
> an English *office* — an org chart populated by *role-as-job-
> description* agents — and an LLM (Claude) maintains the
> underlying Python implementation. The English design is the
> durable artifact. We demonstrate two runtime substrates with
> which the same English design can be deployed: (a) Python asyncio
> for development and small-scale use; (b) DisSysLab (DSL), a
> message-passing substrate providing per-agent LLM selection,
> process isolation, snapshot/resume, and termination detection.
> The English design is substrate-agnostic; Pat's iterative
> workflow does not change between substrates.

---

## v10 — compositionality is the missing pillar (Mani's framing, post Run 1 vs Run 2)

**The observation.** DSL has message-passing semantics with no shared
state. Two offices can be plugged together by wiring one office's
output messages into another office's input messages. The composition
is itself a valid office. Pat already knows this pattern — companies
merge, departments hand off work, contractors integrate — even though
she does not know the actor-model machinery underneath.

**Why this matters.** Compositionality is what makes professional
software development scalable: build small validated pieces; compose
them into larger systems; do not rewrite from scratch. Non-programmers
cannot do this today at the message-passing-system level. Spreadsheets
compose at the cell level; Zapier-like tools compose at the service
level. *Office-level composition for non-programmers is the gap
OfficeSpeak can fill.*

**Concrete demonstration plan.** Three small validated standalone
offices:

- `stock_watcher` — emits `{symbol, price, pct_change}` messages.
- `alert_filter` — passes messages whose `pct_change` exceeds a
  threshold.
- `slack_notifier` — formats messages and posts to a Slack webhook.

Plug them together: `stock_watcher → alert_filter → slack_notifier`
becomes a `slack_stock_alerts` office. Pat then builds a
`crypto_watcher` and plugs it the same way — new app in minutes.

**Why this changes the contribution.** Before compositionality, the
contribution was: a vocabulary for design choice with two
demonstrated substrates. Modest. Workshop-level.

With compositionality, the contribution is: **a methodology that
gives non-programmers access to the build-and-compose pattern at the
message-passing distributed-system level.** Useful in its own right,
independent of paper acceptance.

**The shift in the "is it worth the effort" answer.** The work is
useful if Pat can:
1. Build a small office in English (with Claude's help).
2. Validate it standalone.
3. Plug it into another office to form a larger one.
4. Reuse without rewriting.

The composition story is what makes the methodology stop being a
toy and start being scalable infrastructure for non-programmers.

**Final contribution claim (post-v10).**

> Non-programmer users can compose distributed sense-and-respond
> systems by writing English descriptions of how validated
> office building-blocks plug together. Each office is a small
> message-passing program with English-described agents (the
> office mental model); compositions are described as connections
> between offices. We provide a substrate (DisSysLab) supporting
> the composition semantics, an LLM-mediated workflow (Claude
> writes the implementations), and a Pat-facing vocabulary
> (OfficeSpeak) for expressing both individual offices and their
> composition. We demonstrate the build-and-compose workflow with
> [N] standalone offices recomposed into [M] derived applications.

---

## v9 — both offices are correct; OfficeSpeak is vocabulary for design choice (Mani's reframing after Run 1 vs Run 2)

**The observation.** Run 1 (bare prompt, fresh Claude) produced a
monolithic single-agent program. Run 2 (small style sheet) produced a
decomposed three-agent + one stateful-Python-agent program. Both code
outputs are correct in the sense that both satisfy Pat's specification.
Both can be mapped to offices. The Run 1 office has one heavy agent;
the Run 2 office has multiple lighter agents.

**Mani's reframing.** This is *not* a comparison of "right vs wrong."
It is a comparison of two architectural styles, both valid. Which is
better depends on context:

- **Cost:** Run 1 has 1 LLM call per article; Run 2 has 3.
- **Latency:** comparable (Run 2 uses `gather` for parallelism).
- **Modifiability:** Run 2 wins; you can edit one agent in isolation.
- **Token cost:** Run 1 wins; one prompt vs three for similar work.
- **Inspectability:** Run 2 wins; three transparent agents vs one
  black box.
- **Extensibility:** Run 2 wins; add a fourth agent without touching
  the others vs rewrite the combined prompt.

For a Pat running this once daily on a small feed, Run 1 is fine. For
a Pat planning to evolve the app over months, Run 2 is the better
choice. Both are legitimate.

**Consequence for the contribution claim.** The methodology's value is
NOT "OfficeSpeak produces decomposed code that Claude can't produce
alone." Claude can produce either form. OfficeSpeak's value is **a
vocabulary for choosing between architectural styles**.

- Pat doesn't include the style sheet → Claude defaults to the
  monolithic style. Simpler, cheaper, suitable for one-off uses.
- Pat includes the style sheet → Claude produces the decomposed
  style. Modular, inspectable, supports per-agent modification.

OfficeSpeak shifts the architectural decomposition decision from
"engineering skill" to "design preference Pat can articulate."
Junior engineers often write monolithic code; senior engineers
refactor it into pieces when complexity warrants. OfficeSpeak lets
Pat exercise this judgement without being an engineer.

**Final contribution claim (post-v9).**

> Non-programmer users can choose between architectural styles for
> sense-and-respond systems without writing code, by including a
> small structural style sheet (~10 lines) in their description.
> Without the style sheet, Claude defaults to a compact monolithic
> form. With it, Claude produces a decomposed form expressed as
> "agents with English contracts" that maps to a portable office
> representation. The decomposed representation supports per-agent
> modification, inspection, and deployment across multiple runtime
> substrates (asyncio + DisSysLab). We do not claim Claude cannot
> produce the same code unprompted; we claim that the methodology
> makes the architectural choice expressible by users who do not
> know what "decomposition" means.

**Five empirical demonstrations (illustrative, not measurement):**

1. An office.md + role files Pat can read.
2. Pat writes a spec in plain English; the methodology produces a
   decomposed office.
3. Pat asks for a modification in plain English; one role file
   changes and the system still runs.
4. The same office description compiles to asyncio.
5. The same office description compiles to DSL.

Two additional comparisons that strengthen the claim:

6. Bare-prompt output vs style-sheet output, side by side.
7. Cost / latency / modifiability trade-offs noted (descriptive).

---

## v8 — name change to OfficeSpeak; Claude is supportive, not constitutive

**Name change.** Project renamed from "Network of Thought" to
**OfficeSpeak**. The old name carried a CoT/ToT/GoT lineage that
no longer matches the contribution. OfficeSpeak captures the
notation-centric claim: it is an English notation for specifying
and implementing concurrent programs.

**Mani's refinement of the contribution.** OfficeSpeak is a
*notation*, not just a Claude-mediated workflow. The notation is
accessible enough that Pat can read and write it directly. Claude
is one (very helpful) way to produce OfficeSpeak; Pat can also
write it herself; a programmer could; another LLM could. The
notation is the durable thing.

**Consequence for the empirical demonstrations.** What we need to
show shifts slightly:

1. Pat can read an OfficeSpeak office and understand it.
2. Pat can write OfficeSpeak (with or without Claude's help).
3. OfficeSpeak compiles to two substrates (asyncio + DSL).
4. Pat can modify OfficeSpeak (with or without Claude's help).

Claude's role is supportive, not constitutive. The methodology
does not *depend* on the LLM; the LLM makes it easier.

---

## v7 — three open tensions resolved (Mani's response after v6)

**Tension 1 (one or two substrates).** Resolved: two substrates,
both demonstrated. asyncio for local use; DSL for distributed-
systems properties. Substrate-agnostic English design is a real
claim. Future substrates (e.g., Rust) are conceivable but not
required for the paper.

**Tension 2 (office metaphor — central or supporting).** Resolved:
central. The office is how Pat uses English. Mani's parenthetical
clarifies the broader principle: "the office model *(or some
other Pat-understandable model)*." The general claim is "use a
mental model the target user already understands"; the office is
our worked example.

**Tension 3 (iteration — required or not).** Resolved: not as a
measurement. The required claim is that Pat *can* iterate, which
follows from the English-and-office model being understandable
enough to receive modification requests in English. We are not
doing a software-engineering study of *how* Pat iterates.

---

## Final distilled contribution (post-v7)

Three claims, hierarchically:

1. **English-only interaction.** Pat never reads or writes code.
   Every interaction — specification, comprehension, modification —
   is in English.

2. **Pat-understandable mental model.** We give Pat a familiar
   mental structure (the office: an org chart of role-as-job-
   description agents) so the English is meaningful to her. The
   broader principle is "use a model the target user already knows";
   the office is our worked example.

3. **Substrate-agnostic English design.** The same English design
   maps to multiple runtime substrates. We demonstrate two:
   asyncio for local and DSL for distributed (per-agent LLMs,
   process isolation, snapshot/resume, termination detection).

**One-paragraph statement (for the paper introduction):**

> Pat's entire interaction with the system — initial specification,
> comprehension, modification — is in English. We give Pat a
> familiar mental model (the office: an org chart of role-as-job-
> description agents) so the English is understandable to her. An
> LLM (Claude) translates the English to runtime code; the same
> English design maps to multiple runtime substrates (asyncio for
> local use, DSL for distributed properties).

**Empirical demonstrations needed (illustrative, not measurement):**

- An office.md + role files that Pat can read.
- A spec in plain English that produces a valid office.
- A modification in plain English that produces a correct change.
- The same office running under asyncio.
- The same office running under DSL.

Five demonstrations. No user study, no metrics, no benchmarks.
