# Build and Maintain Persistent Multi-Agent Systems in English

*Draft v3 — 2026-07-22. The goal of this document is to get OfficeSpeak's
approach and results written up and out, not to optimize for any one
venue. It is written in a form suitable for submission to CHI 2027
(deadline September 10, 2026) should that be the right vehicle, but it is
not final: several evaluation claims below are illustrative/preliminary
and explicitly marked as such, pending real, independent testers
(including two tester conversations already scheduled) and a larger
cohort of 50+ first-time users this term. Sections that are genuinely
evidenced today are marked accordingly; nothing is claimed as built or
measured unless it is.*

## Abstract

Distributed systems — programs that run continuously, keep state, react to
asynchronous inputs, and coordinate several agents — have been used by
corporations for decades. Individuals, such as small business owners, with
limited programming skills, can benefit from them too. A challenge for
non-programmers is not only to build distributed systems, but also to
debug and maintain them. Large language models can generate code, but
generating stateful, concurrent systems is more difficult than generating
sequential programs, and existing multi-agent LLM frameworks that target
this space either lack consistent state-recovery guarantees under
concurrency or require writing real code.

This paper presents **OfficeSpeak**, a system that converses in English
with non-programmers to build, understand, debug, and maintain
distributed systems. The user describes an *office* — a team of workers,
each with a role stated in English. OfficeSpeak assembles a network of
message-passing agents and explains it back in English, including an
explicit, numbered list of what it assumed and could not determine from
the description alone; the user corrects it in English and the system
rebuilds. The same conversational register extends to debugging and
maintenance: the user can ask OfficeSpeak to explain a saved checkpoint or
a run's recorded execution history, and get an answer grounded in the
same distributed-systems theory (Lamport clocks, global snapshots)
that makes the underlying guarantees correct — surfaced as English, not
hidden as implementation detail. OfficeSpeak generates code for agents but
not for their coordination; a small library of trusted coordination
primitives gives every generated system distributed termination detection
and consistent global-snapshot checkpointing that the user never
specifies. We position these properties against current multi-agent and
workflow frameworks that either do not provide them under concurrency or
provide them only to programmers, and report preliminary evidence — a
worked example, a pre-registered held-out test protocol, and verified
technical demonstrations — toward a fuller evaluation with real
non-programmer users.

## 1. Introduction

Organizations, such as banks, have long used distributed systems for
applications such as credit-card processing. Individuals can benefit from
them too. A member of a local investment club wants a system that watches
market data, economic news, and social feeds, weighs different investment
strategies, and makes recommendations. A facilities manager wants one
that fuses HVAC readings, utility sensors, and email into plan updates.
These apps are smaller and simpler than an organization's, but they are
persistent, multi-agent, and stateful — a service that keeps running and
keeps state, not a script that runs once and exits.

How can a non-programmer build, debug, and maintain a distributed system
for herself? One answer is to have a large language model generate
systems from English descriptions; however, code that creates and
coordinates multiple concurrent agents is tricky, and existing multi-agent
LLM tooling was built for programmers, not for the person who has to live
with the running system afterward. The hard problems of distributed
systems — concurrency constructs, distributed algorithms, theories of
correctness — were solved over decades, by computer scientists, for
computer scientists. OfficeSpeak is an attempt to make those results
usable by everyone, without ever showing the person the formalism that
makes them work.

**This paper makes the following contributions:**

1. The **office** interaction: a non-programmer builds, understands,
   corrects, debugs, and maintains a persistent, stateful, concurrent
   distributed system through an ongoing English conversation, in which
   the system explicitly discloses what it assumed and revises on
   correction. This is the one claim that has survived every revision of
   this project's own framing, and it is the one with the most direct
   evidence behind it (Section 7).
2. A small library of **trusted coordination primitives** the model
   assembles the system from, rather than generating coordination code.
   An entire class of concurrency bug — races, lost updates, a
   deadlocking hand-written gate or queue — cannot arise, because that
   machinery is library code, never model-written. The assembled office
   also gains distributed termination detection (correct even with
   feedback loops) and consistent global-snapshot checkpointing (a
   genuine global-snapshot consistent cut across concurrently running
   agents, including messages caught in flight) — properties current
   multi-agent LLM frameworks either do not provide under concurrency or
   provide only to people writing real code (Section 8).
3. **Debugging and understanding by conversation**: the same English
   channel that builds the office also explains it while it runs and
   after it stops — an isolated worker's behavior, a recorded run's full
   message history ordered by a physical-time-grounded logical clock, or
   a saved checkpoint's contents — grounded in Lamport's happened-before
   relation and global snapshots, made legible rather than hidden
   (Section 6).
4. A clean **separation of concerns** — a wiring layer checkable from
   per-agent contracts, versus an agent-specification layer the user
   confirms — with the contract as the seam (Section 2).
5. **Preliminary evidence** toward evaluating all of the above: a worked
   example where a non-expert caught a genuine distributed-data defect
   through the disclosure mechanism, a pre-registered held-out test
   protocol, and verified technical demonstrations of the checkpoint and
   trace explainers against a real running system (Sections 4, 6, 7).

Next we discuss the structure of the systems OfficeSpeak generates, the
mental model non-programmers use to describe them, and how computer
science theory gets surfaced to a non-programmer rather than hidden from
her.

## 2. The office abstraction

An **office** is a network of **agents**. Each agent has one job, its own
private memory (**state**), input ports it reads, and output ports it
sends on. Information enters through **sources** and leaves through
**sinks**. The office runs continuously; it is not a function that is
called but a service that reacts. Formally, this is a network of
processes in the sense of Kahn, Misra, and Hoare [1–3]: a process (here,
**agent**) is either a sequential program or itself a network of
processes; an edge from an outbox to an inbox is a queue (a **channel**);
the network's behavior is the set of actions "move the message at the
head of a nonempty outbox to every channel it feeds" and "move the
message at the head of a nonempty channel to the inbox it feeds." We
elide the full formalism here in favor of the office vocabulary
non-programmers actually use, below.

Most agents are **workers** whose job is described in English and
realized by an LLM prompt or a small piece of code (an analyst who forms
a view, a manager who decides). A few agents are **coordination
primitives** drawn from a fixed library:

- **source / sink** — information in / results out.
- **fair_merge** — combine several sources into one stream (used only to
  merge sources).
- **merge_synch** — wait for one message on each named input and emit the
  combined result (a join; e.g., a decider that needs every advisor's
  argument).
- **select** — read whichever input the agent's state points to; used
  for ask-and-wait (send a request, wait for the reply) and for taking
  inputs in a set order.
- **record (a clerk)** — a shared file that other agents read and update
  by asking a keeper agent; the message-passing realization uses a
  keeper agent instead of shared memory.
- **gate** — admit one item at a time, releasing the next only after a
  "done" signal; used when an agent that owns shared state is updated
  while handling each item.

(Sending an item to one of several places by a condition is
*computation*, not coordination — an ordinary worker does it — so it is
not a primitive.)

**Determinism via coordination, not restriction.** In a network of
message-passing agents, the only source of nondeterminism is a **merge**
— a point where messages from several streams interleave. If merges are
controlled (merge_synch, select), the office is determinate in Kahn's
sense; an *uncontrolled* merge (fair_merge) is the sole nondeterministic
primitive, confined to combining sources. So determinism, where the user
wants it, is achieved by *how the office is coordinated*, not by limiting
what the user may describe. Determinism matters because it makes the
office **testable**: the same inputs produce the same outputs, so
empirical testing is meaningful.

**Coordination is trusted; bodies are generated.** The coordination
primitives are library code — trusted mechanisms, never generated. Only
worker bodies are produced by the model. The consequence is a sharp bound
on where model error can land: a wrong body is a *content* error (the
analyst reasons poorly) — testable and catchable by the user — and can
never be a *coordination* error, because the machinery that controls
concurrency is not model-written.

The substrate also endows every office, for free, with distributed-systems
machinery the user never asked for and never sees: **termination
detection** that works even when the agent network has loops, and
consistent **checkpoints** for saving and restoring state. A checkpoint is
a genuine global-snapshot [5] consistent cut across every concurrently running
agent, including whatever messages were caught in flight at the moment of
the cut — not a single process's serialized state — so resuming from it
continues the office correctly rather than dropping or duplicating work at
the boundary. This checkpoint is also, separately, something the user can
ask to have explained: what each worker's memory held, and what was still
in transit, narrated in English (Section 6). We stop short of a stronger,
harder claim some readers might expect here: the substrate does not
currently capture every source of run-to-run nondeterminism (fair-merge
order, an LLM's sampled response, a worker calling the clock or a random
number generator directly), so it does not offer bit-for-bit deterministic
replay of a prior execution. That is real, identified future work (Section
9), not a claimed capability. What is built and verified is read-only:
narrating what a checkpoint holds, and narrating a recorded run's message
history, without re-executing anything.

The same holds at the office's **boundary**. Sources and sinks are a named
registry presented to the model; the model maps the user's plain-English
inputs and outputs to registered entries by meaning, and an unmatched one
is a flagged, unbound port rather than a silent failure. So the office is
assembled from trusted, registered parts at its edges (sources/sinks) and
in its coordination (primitives); only the interior worker bodies are
generated. In this paper we assume the sources and sinks the examples
require are registered — backed by replayed or mock data where a live
connector is impractical — and treat helping the user register brand-new
sources and sinks as future work.

**Roles and agents (kept under the hood).** DSL separates a **role** — a
reusable job template with named inputs and outputs — from an **agent**,
an instance of a role wired into a particular office, exactly as a class
relates to an object. Two analysts, VAL and OPPO, *may* be two agents of
one analyst role differing only in per-instance parameters (a value
strategy vs an opportunities strategy), or they may be two separate
roles; both are correct. Role reuse is a capability DSL offers, not
something the model is required to find. This gives reuse where it is
used, but the formalism (ports, wiring, the words "role" and "agent") is
never shown to the user — it has a natural everyday analog, a job
description versus the people who hold it.

Ports are where this indirection is most tempting to leak, and we keep it
hidden. The user describes routing **agent-to-agent**, naming recipients
("if it fits, send it to the writer; otherwise to the reject log"), which
is how people naturally think. The model factors that single statement
into what DSL needs — a role with outputs, plus wiring that binds those
outputs to the named recipients — and may (but need not) reuse a role
when the same branching recurs.

**Two layers, one seam.** Every agent has a **contract**: what it reads,
what it sends, what state it owns. Above the contract is the **body**
(how it turns reads into sends); around it is the **wiring** (edges
between contracts). A **wiring problem** is a graph inconsistent with the
contracts — checkable from the contracts alone, without reading any body.
An **agent-specification problem** is a body that does not do what its
contract or the user intends, and requires reading the job descriptions.
The contract is the seam, derived from the specification and consumed by
the wiring, and it is what lets the two kinds of review proceed
independently.

## 3. Commanding an office in plain English

Pat never writes agents, ports, or edges. She writes a
**structured-but-plain** description — flexible prose organized around a
few questions: what is the office for, what comes in and goes out, who
are the workers, what does each do and *need to know*, and what rules
must hold (one-at-a-time, who waits, learning over time). The structure
is not a formal language; it is the shape a good description takes.

A single principle runs through the description. Pat's natural unit fuses
*what* a worker does with *whom* and *when* it communicates — "the
accountant works out the fees and sends them to the manager" — and names
recipients inline rather than through ports. Her description is natural,
coupled, and fused; the graph the system needs is clean, decoupled, and
separated. The model is the translator that pulls apart what Pat runs
together.

**Realization: the loop runs inside a general agent host.** We do not
build a bespoke interface. DSL is packaged as a plugin for a general
agent platform (here, Claude's Cowork), bundling the pip-installable
library — with its trusted primitives, termination detection, and
checkpoints — and skills that shape the host's own conversation: onboard,
build, explain, debug. The host supplies everything else it already does
well: it holds the plain-English conversation, writes the office into the
user's folder, renders it as a diagram, edits it on a correction, runs it
in a sandbox, presents the output, and can schedule it as a running
service. The contribution is the substrate, the abstraction, and the
method; the host is interchangeable and improves independently.

From the description the model **builds** a graph and **explains it
back**: a plain account of the team, a walk through what happens to one
item start to finish, and a short, numbered list of the choices the
description did not pin down — **"Things I assumed."** This disclosure is
not a courtesy footnote; it is the mechanism that makes the whole loop
work, because Pat can only correct what she can see was assumed. Pat
reads the explanation and **corrects** it in plain English ("the
accountant must see what we currently hold"), and the model rebuilds. The
loop is the product; a first draft need not be right, because it is
cheaper for a person to *react* to a concrete office than to *specify*
one from nothing.

Pat's description, OfficeSpeak's explanation (including its disclosed
assumptions), her corrections, and — as Section 6 describes — its later
explanations of checkpoints and recorded execution history are all in the
same English register. In HCI terms, this bridges Norman's [9] *gulf of
execution* — "how do I say what I want the system to do?" — and *gulf of
evaluation* — "did it do what I meant, and what is it actually doing,
right now, underneath?" Both gulfs are usually crossed by learning an
interface's own vocabulary (a form, a diagram notation, a query
language); here both are crossed in the same plain English Pat already
used to describe the office in the first place, before, during, and after
it runs.

## 4. Worked example: the investment-club office

**Pat's description (abbreviated).** Recommend buy/sell/hold for a club
holding mutual funds and cash. Once per period the office receives a
batched feed (financial data, forecasts, breaking news) and the club's
decisions from the previous period. Two analysts — **VAL** (value
investing) and **OPPO** (emerging opportunities) — each read the feed and
have access to the club's current portfolio and history, and each
recommends an action plan. A manager, **MGR**, collects both analysts'
recommendations, proposes a plan, checks the fees with an accountant,
**ACNT** (taxes and transaction costs), then writes a final plan to a
file, **RECOMMEND**.

**The graph the model builds.**

```
Sources: feed (batched, per period), club_decisions (previous period)
Ledger — record(holds: portfolio, history); updated from club_decisions
Batcher — assemble one period packet from feed + club_decisions, release per period
VAL  — value analyst · reads: period packet, Ledger · sends: rec -> MGR
OPPO — opportunities analyst · reads: period packet, Ledger · sends: rec -> MGR
MGR  — manager · merge_synch[VAL, OPPO] -> propose plan; <-> ACNT; final -> RECOMMEND
ACNT — accountant · reads: proposed plan · sends: fees -> MGR
RECOMMEND — sink (file)
Wiring:
  feed, club_decisions -> Batcher -> VAL, OPPO
  club_decisions -> Ledger
  VAL -> MGR ; OPPO -> MGR          (merge_synch join)
  MGR <-> ACNT                      (ask-and-wait / select)
  VAL <-> Ledger ; OPPO <-> Ledger  (read portfolio + history)
  MGR -> RECOMMEND
```

The model chose the right coordination without being told the words: a
**join** (merge_synch) so MGR waits for both analysts on the same period;
an **ask-and-wait** (select) for the MGR↔ACNT back-and-forth; a
**record** (Ledger) for the shared portfolio and history.

**The explanation Pat reads (abbreviated).**
> Each period, the team gets the day's information and last period's club
> decisions, bundled together. VAL and OPPO each read it, check the
> club's current holdings and history, and each writes a recommendation.
> MGR waits for both, puts together a proposed plan, and asks ACNT what it
> would cost in taxes and fees. ACNT works that out and reports back; MGR
> then finalizes and writes the plan to RECOMMEND.
>
> Things I assumed — the two analysts are treated equally; MGR has the
> final say; **ACNT works out the taxes from the proposed plan alone — it
> does not look at what the club currently holds.** Tell me if any of
> these should be different.

**Pat's correction.** The last assumption is wrong, and Pat can see it in
plain English without any systems knowledge: taxes depend on cost basis,
which lives in the portfolio.
> "The accountant has to see what we currently hold — otherwise the tax
> numbers are guesses."

**The revised graph** adds one edge, `ACNT <-> Ledger`. Nothing else
changes. **What actually happened when the corrected office ran** (three
periods, real numbers, then it stops on its own): period 1 — propose 8
shares, fee $8.00 (0 shares held); period 2 — propose 16 shares, fee
$16.80 (8 shares held from period 1); period 3 — propose 24 shares, fee
$26.40 (24 shares held from period 2). Each period's fee is computed from
the *previous* period's ending holdings — exactly what the correction
asked for, now visibly true in real output, not just in the corrected
graph.

This is the loop in miniature, and it makes the central claim concrete: a
non-programmer caught a genuine distributed-data defect — a computation
reading a value it was never given access to — through a plain-English
explanation, and fixed it with a plain-English instruction, and the fix
is verifiable in the numbers the corrected system actually produces.

## 5. Why an office can be correct and testable

Three things do the work.

**Trusted coordination.** The gate, join, selector, record, and merge are
library code — trusted mechanisms, so the office never contains a
hand-generated gate or queue that races, loses updates, or deadlocks. The
model's remaining freedom — which primitive, how they are wired, and the
worker bodies — is exactly what the static checks and the explain-back
are there to cover.

**Determinism where wanted.** With merges controlled, the office is
determinate, so the same inputs reproduce the same outputs and testing is
meaningful. Uncontrolled merge is available (for source combination) but
is the only nondeterministic primitive and is used deliberately.

**Checks on the seam.** Wiring problems are contract-vs-graph mismatches,
statically checkable independent of bodies: an input nothing feeds, a
multi-input consumer with no explicit join, a gate with no matching
release, a body referencing an undeclared input. This static checker is
the systems-side complement to the explain-back: it catches the
structural faults a plain-English description cannot be expected to
surface, while the explain-back catches the intent mismatches a static
check cannot judge.

## 6. Debugging and maintaining an office in English

Building and correcting is not the end of the relationship between Pat
and her office — it keeps running, and eventually something needs
explaining: why did it do that, what did it know at the time, is it
stuck. OfficeSpeak answers all three in the same conversational register
used to build the office, and — the point worth dwelling on for a
"bridges" venue — the answers are grounded in real distributed-systems
theory rather than approximating it away.

**Isolated worker testing.** The simplest aid: run one worker alone on
hand-picked inputs, outside the running office, to localize a body bug
without any of the concurrency around it. Built and verified: a planted
bug in a computational worker (comparing a raw reading instead of its
rise above baseline) produced 10 false alerts; isolating and fixing the
worker brought it to 1 correct alert. This aid is computational-workers
only — an LLM worker's judgment is not a fixed function to grade this
way.

**Explaining a recorded run.** Each agent can log every message it sent
and received, tagged with a clock value, and a merge tool produces one
time-ordered account of the whole office's history for OfficeSpeak to
narrate. The clock is a **hybrid logical clock** in the tradition of
Lamport's happened-before relation [4] and, in spirit, Kulkarni et
al.'s physical-time-grounded logical clocks [6]: each agent's clock is
the current physical time, corrected on every receive by `x := max(t,
x+1)` where `t` is the incoming message's timestamp — guaranteeing each
agent's own actions strictly increase in timestamp order while staying
close to true wall-clock time. Verified against a real five-agent office
(a Monte Carlo estimator of π: a source of random points, two workers
classifying each point inside or outside a circle, a combiner tracking
the running estimate, a display): every agent's clock was confirmed
strictly monotonically increasing across a real run, and the merged,
sorted record was confirmed causally correct — sent actions before their
matching received actions — after one real ordering subtlety was found
and fixed during verification (a send and its matching receive can land
on the identical timestamp when the receiver's clock is behind the
sender's; the merge tool now breaks such ties send-before-receive). A
narrated excerpt of a real run: "The source sent point (0.639, 0.025)
into the office. The classifier received it and, having decided the
point falls inside the circle, sent a running inside-count of 1 onward.
The combiner received that count and updated its estimate: π ≈ 4.0000 —
just the first point, so still noisy." This is deliberately *not*
deterministic replay: it narrates a run that already happened, once; it
never re-executes anything, and so it does not need to solve the harder
problem of capturing every source of nondeterminism (Section 2).

**Explaining a checkpoint.** The same office's checkpoints — the
global-snapshot [5] consistent cut described in Section 2 — are
explainable the same way. A real checkpoint, narrated: "At this
checkpoint, the combiner had folded in 3339 inside-counts and 916
outside-counts, giving a running estimate of about π ≈ 3.14 at that
instant. One classifier had actually already classified one more point as
inside — that message was still on its way to the combining step when
this checkpoint was taken, so it hadn't been folded in yet." This is the
consistent cut from Section 2, made legible: what each
worker's own memory held, and what was still in flight, at one instant.

**Why this is a real, not cosmetic, extension.** Both explainers work
uniformly on computational and LLM workers alike, unlike isolated worker
testing — narrating what a worker did or what it held requires no
judgment about whether an LLM's output was *right*, only a faithful
record of what happened. And both rest on the same theoretical lineage
already grounding the checkpoint guarantee in Section 2 (Lamport [4] →
global snapshots [5] → a physical-time-grounded clock in Kulkarni et al.'s
tradition [6]), so a non-programmer's debugging conversation and the
system's underlying correctness proof are, for once, talking about the
same object.

## 7. Related work

**Multi-agent LLM frameworks.** AutoGen, LangGraph, and CrewAI let a
developer assemble multiple LLM-driven agents into a workflow, but none
gives the guarantees OfficeSpeak's substrate does under concurrency.
AutoGen bounds runaway agent loops with a fixed reply-count cap
(`max_consecutive_auto_reply` [11]), not a termination-detection
algorithm that reasons about whether the network has actually gone
quiescent. CrewAI has no built-in checkpointing for long-running
workflows, and its hierarchical Manager-Worker delegation has been
reported to not function as documented in production — tasks executed
out of order, outputs overwritten, no explicit stop condition — fragile
enough that teams fall back to simpler sequential execution after
repeated failures [13]. LangGraph does checkpoint — its checkpointer
saves a `StateSnapshot` at every super-step, keyed by `thread_id` [16] —
but it has no automatic failure detection and no coordination preventing
two processes from resuming the same `thread_id` concurrently [12];
independent analysis characterizes this explicitly as fault *recovery*
for a single process, not a consistent distributed snapshot, and reports
the same gap in CrewAI and Google ADK [12]. DisSysLab's checkpoint, by
contrast, is a global-snapshot [5] consistent cut across every
concurrently running agent, including messages caught in flight — the
same guarantee class, at the same rigor, as classical
distributed-snapshot algorithms, not a serialized state blob. None of the
three exposes any of this to a non-programmer in natural language; all
three are developer tools.

**Durable execution.** Temporal offers genuine durable execution —
workflow state persisted and resumable after a crash [14] — and is
explicit that workflows are written in real programming languages (Go,
Java, TypeScript, Python, .NET, PHP, Ruby) with full IDE support and
version control [15]. It solves durability for programmers; it does not
attempt an English interface for non-programmers, and does not attempt
termination detection for open-ended, cyclic multi-agent coordination in
OfficeSpeak's sense.

**End-user and natural-language programming.** There is active HCI
research on how people communicate programming tasks in natural language
and what that implies for end-user programming with LLMs — a recent CHI
study found programming experience gave only a modest edge in
communicating tasks successfully, and that requesting clarification did
not reliably correlate with a better outcome [10]. Separately,
mixed-initiative systems research establishes proposing a correction the
user can accept or reject as a known, effective interaction pattern [18].
We build on both traditions but combine them with a target neither
centers: a *persistent, stateful, concurrent* system, not a one-shot
script or a single-turn task, and a correction loop that explicitly
discloses the system's own uncertainty ("Things I assumed") rather than
only responding to a user-initiated error report.

**Models of concurrency.** Offices are Kahn process networks with
controlled merges [1,2]; the determinism argument and the role of merges
as the locus of nondeterminism follow the dataflow tradition and the
merge anomaly [17], and the tagged-signal framing [8]. Reasoning about
correctness without determinism draws on UNITY-style program logic [7].

**The claim, stated precisely.** No single piece here is new in
isolation — checkpointing, termination bounds, and natural-language
correction loops each exist somewhere. What we have not found combined
elsewhere is natural-language specification with an explicit,
assumption-disclosing correction loop, *together with* distributed-systems
correctness guarantees actually verified to hold under concurrency (a
consistent multi-agent snapshot, not a single-thread state dump;
termination detection under cycles, not a call-count cap) — in one
conversational system built for people who have never written concurrent
code.

## 8. Preliminary evaluation

We report what is genuinely built, verified, or pre-registered today, and
say plainly what is not yet run.

**Evidenced now.**
- *The investment-club worked example* (Section 4) is real, run
  end-to-end, with real output numbers, not a hypothetical.
- *A pre-registered held-out test protocol*: nine cases (seven
  single-module, two full-chain), run on fresh, uncontaminated model
  instances, with expected outcomes fixed before running — designed
  specifically to check whether the "Things I assumed" disclosure
  surfaces real gaps rather than staying silent or crying wolf on offices
  the system had not seen being built.
- *The trace and checkpoint explainers* (Section 6) are built and were
  verified against a real running system on 2026-07-22: correct clock
  monotonicity, correct causal ordering after one real bug was found and
  fixed during verification, and correct checkpoint content including a
  message genuinely caught in flight. This is a real system being
  exercised, not a description of an intended one.
- *Termination detection* under a coordinator-heavy office with feedback
  loops: a real correctness bug here was found and fixed shortly before
  this writing, with a full regression suite (446 tests) passing at the
  time of the fix — evidence the property is taken as seriously as a
  claim, not asserted and left unchecked.

**Proposed, not yet run — and why that's stated here rather than
elsewhere.** Two different kinds of evidence are still missing, and they
address two different weaknesses, worth distinguishing explicitly. The
first is a **planted-defect protocol**: starting from a verified,
already-correct office, introduce one known synthetic defect at a time
(a single mutated edge, a swapped port) and score whether the
explain-back disclosure surfaces it, and how often it cries wolf on
non-defects. This is designed and pre-registered but not yet run; it is
a controlled sensitivity/specificity check on the disclosure mechanism
itself, closer to mutation testing than to a user study, and does not by
itself need independent human testers to execute (though independent
non-expert judges would strengthen the scoring).

The second, more important gap is different in kind: every worked example
in this paper so far — the investment club, the room-climate monitor —
was authored by the same people who built the system being evaluated.
That is a real limitation independent of the planted-defect protocol: an
author-written example risks being shaped, consciously or not, to make
the disclosure loop look good. The genuine fix is examples authored by
people with no stake in the system working, describing an office they
actually want. We have two such conversations scheduled in the immediate
term — a hedge fund manager and a manager of environmental sensor
networks, each describing a real system they'd want built, independently
of any example in this paper — and a larger cohort of 50+ first-time,
non-programmer users is expected to use OfficeSpeak this term. Neither
has happened yet as of this writing, so no results are claimed here; a
revision of this paper, or a follow-on report, is where they will land.
An ablation against a general coding agent asked to write the same office
directly, and a controlled study of whether structured description
reduces iteration, remain designed-but-unrun and undesigned,
respectively.

## 9. Limitations and future work

- **The description is assumed, not elicited.** Producing the
  structured-plain description through a guided onboarding conversation —
  so a Pat off the street knows where to begin — is designed but not yet
  evaluated.
- **Compositionality is not yet built.** Wiring validated, standalone
  offices together into larger ones (or nesting one office as a single
  worker) is demonstrated only informally today, not as a first-class,
  systematic capability. This is likely the largest single piece of
  near-term future work, and would be needed before any claim about
  building larger systems by composition, not just describing one large
  system directly.
- **Per-agent LLM choice exists in the substrate but is not yet surfaced
  conversationally.** DisSysLab can already run different agents on
  different LLM backends (including via OpenRouter), so a heterogeneous
  office — one worker on one model, another on a cheaper or more capable
  one — is technically possible today. Pat cannot currently ask for this
  in English; exposing it through the conversation is a small, concrete
  piece of near-term work.
- **Process-vs-thread execution is office-wide, not per-agent.** A
  technical user (not Pat) can currently choose whether an entire office
  runs as OS processes (true parallelism) or threads, but not mix the
  two within one office — e.g., one CPU-heavy worker as a process while
  the rest stay as threads. Useful future work for offices with an
  uneven workload across workers.
- **No deterministic exact replay.** As stated in Section 2, the
  substrate does not capture every source of run-to-run nondeterminism
  (fair-merge order, an LLM's sampled response, direct clock/RNG calls in
  a worker body), so it cannot currently reproduce a prior execution
  bit-for-bit. The read-only explainers in Section 6 are a different,
  easier problem, solved; exact replay remains future work with a known
  open sub-problem (routing a worker's own nondeterministic calls through
  a logged channel).
- **Corpus breadth.** The evidence centers on one office family so far.
  Prediction and anomaly-detection offices exercise different
  coordination (temporal joins, delayed matching of outcomes to
  forecasts, per-key state) and are natural next targets.
- **Evaluation rigor.** Explain-back scoring for the planted-defect
  protocol, when run, will initially be by the authors; the claim that
  ultimately matters — non-expert humans catching defects from the
  explanation, in practice — needs real non-programmer usage. The
  upcoming class is the intended source of that evidence.

## 10. Conclusion

Offices let a non-programmer command a persistent, stateful, concurrent
system by describing a team of workers in plain English, having the
system explain the result back — including what it assumed and could not
determine — and correcting it in plain English. The same conversational
register extends past building into debugging and maintenance: explaining
a saved checkpoint or a recorded run's history in terms grounded in real
distributed-systems theory, not an approximation of it. Coordination is
trusted rather than generated, so the system is correct and, where
wanted, deterministic without restricting what the user may say. The
worked example shows the whole loop, including a user catching and fixing
a genuine distributed-data bug; the trace and checkpoint explainers show
the same conversational register working for the system's internal,
formally correct state. What is not yet shown is that this holds up with
real non-programmers at scale — that evidence is the explicit next step,
not a gap papered over.

## Suggested figures (described, not yet drawn)

Six figures would make this paper substantially more readable. None are
produced yet — each is described here as a spec for later production, with
a suggested placement.

1. **The build → explain → correct loop (Section 3).** The figure the
   paper most needs. Three or four panels in sequence: (a) Pat typing a
   plain-English description into a chat window; (b) OfficeSpeak's reply
   — a rendered office graph plus a numbered "Things I assumed" list,
   shown side by side with the graph; (c) Pat typing a one-line
   correction ("the accountant has to see what we currently hold"); (d)
   the graph updating — one new edge appears, highlighted — with a
   shortened re-explanation. Caption: "Pat builds and corrects an office
   entirely in English; the graph and its self-disclosed assumptions are
   the only technical artifacts she ever sees, and both change together
   in response to her plain-language correction."
2. **The office abstraction (Section 2).** A static architecture diagram
   of one small office (the investment-club example is the natural
   choice, since it's already worked through in the text) — boxes for
   VAL, OPPO, MGR, ACNT, arrows for message flow, a distinguished shape
   or color for the coordination primitives (the `merge_synch` join at
   MGR, the `select` ask-and-wait with ACNT) versus ordinary worker
   boxes, and the Ledger drawn as a shared record with its own inbox.
   Caption: "An office is a network of workers (generated) wired together
   by a small set of trusted coordination primitives (library code, never
   generated)."
3. **Two layers, one seam (Section 2/5).** A simple layered diagram: a
   "wiring" layer (the graph, checkable from contracts alone) and a
   "specification" layer (worker bodies, judged by the user), meeting at
   a horizontal line labeled "contract" — with a small callout showing
   the one concrete example from the text (ACNT's contract listing only
   "proposed plan" as an input, which is exactly what the explain-back
   catches and Pat corrects).
4. **A recorded run, explained (Section 6).** A short horizontal timeline
   with a handful of real events from the recovery_demo run already
   quoted in the text (source sends a point, a classifier receives and
   sends a count, the combiner receives and updates its estimate),
   each event tagged with its logical-clock value, with arrows showing
   the happened-before/causal ordering between sender and receiver — and
   the actual narrated English sentence for one event shown as a callout
   next to it.
5. **A checkpoint, explained (Section 6).** A single "consistent cut"
   diagram: several parallel timelines (one per agent), a jagged vertical
   line sweeping through them at different local points (the
   global-snapshot cut), boxes on the cut line showing each agent's saved
   state at that instant, and — the detail worth actually drawing — one
   message shown mid-flight, crossing the cut line, labeled with the real
   in-flight example from the text ("still on its way to the combining
   step when this checkpoint was taken").
6. **Stage 1 / Stage 2 pipeline overview (Section 1 or an appendix).** A
   simple left-to-right pipeline: "English conversation (Stage 1)" →
   "hand-off file" → "source/sink matching + worker approval (Stage 2)" →
   "generated, running office," with a small annotation marking which
   stages are fully automated today versus which still need a
   Python-comfortable person. Useful mainly for readers unfamiliar with
   the two-stage split; skippable if space is tight.

## References

[1] Gilles Kahn. 1974. The semantics of a simple language for parallel
programming. In *Information Processing 74: Proceedings of IFIP Congress
1974*. North-Holland, 471–475.

[2] Gilles Kahn and David B. MacQueen. 1977. Coroutines and networks of
parallel processes. In *Information Processing 77: Proceedings of IFIP
Congress 1977*. North-Holland, 993–998.

[3] C. A. R. Hoare. 1978. Communicating sequential processes.
*Communications of the ACM* 21, 8 (1978), 666–677.
https://doi.org/10.1145/359576.359585

[4] Leslie Lamport. 1978. Time, clocks, and the ordering of events in a
distributed system. *Communications of the ACM* 21, 7 (1978), 558–565.
https://doi.org/10.1145/359545.359563

[5] K. Mani Chandy and Leslie Lamport. 1985. Distributed snapshots:
Determining global states of distributed systems. *ACM Transactions on
Computer Systems* 3, 1 (1985), 63–75. https://doi.org/10.1145/214451.214456

[6] Sandeep S. Kulkarni, Murat Demirbas, Deepak Madappa, Bharadwaj Avva,
and Marcelo Leone. 2014. Logical physical clocks. In *Proceedings of the
17th International Conference on Principles of Distributed Systems
(OPODIS 2014)*, LNCS 8878. Springer, 17–32.
https://doi.org/10.1007/978-3-319-14472-6_2

[7] K. Mani Chandy and Jayadev Misra. 1988. *Parallel Program Design: A
Foundation*. Addison-Wesley.

[8] Edward A. Lee and Alberto Sangiovanni-Vincentelli. 1998. A framework
for comparing models of computation. *IEEE Transactions on
Computer-Aided Design of Integrated Circuits and Systems* 17, 12 (1998),
1217–1229. https://doi.org/10.1109/43.736561

[9] Donald A. Norman. 1986. Cognitive engineering. In *User Centered
System Design: New Perspectives on Human-Computer Interaction*, Donald A.
Norman and Stephen W. Draper (Eds.). Lawrence Erlbaum Associates, 31–61.

[10] Madison Pickering, Francisco Piedrahita Velez, Michael L. Littman,
and Blase Ur. 2025. How humans communicate programming tasks in natural
language and implications for end-user programming with LLMs. In
*Proceedings of the 2025 CHI Conference on Human Factors in Computing
Systems (CHI '25)*. ACM. https://doi.org/10.1145/3706598.3713271

[11] Microsoft. AutoGen 0.2 Documentation. Terminating conversations
between agents. https://microsoft.github.io/autogen/0.2/docs/tutorial/chat-termination/
(accessed 2026-07-22).

[12] Diagrid. Why checkpoints aren't durable execution: LangGraph,
CrewAI, Google ADK, and others fall short for production agent workflows.
Diagrid Blog. https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows
(accessed 2026-07-22).

[13] Why CrewAI's manager-worker architecture fails — and how to fix it.
*Towards Data Science*.
https://towardsdatascience.com/why-crewais-manager-worker-architecture-fails-and-how-to-fix-it/
(accessed 2026-07-22).

[14] Temporal Technologies. Temporal Workflow Execution overview. Temporal
Platform Documentation. https://docs.temporal.io/workflow-execution
(accessed 2026-07-22).

[15] Temporal Technologies. About Temporal SDKs. Temporal Platform
Documentation. https://docs.temporal.io/encyclopedia/temporal-sdks
(accessed 2026-07-22).

[16] LangChain. Persistence. LangGraph documentation.
https://docs.langchain.com/oss/python/langgraph/persistence (accessed
2026-07-22).

[17] J. D. Brock and W. B. Ackerman. 1981. Scenarios: A model of
non-determinate computation. In *Formalization of Programming Concepts*,
LNCS 107. Springer, 252–259. https://doi.org/10.1007/3-540-10699-5_102

[18] Eric Horvitz. 1999. Principles of mixed-initiative user interfaces.
In *Proceedings of the SIGCHI Conference on Human Factors in Computing
Systems (CHI '99)*. ACM, 159–166. https://doi.org/10.1145/302979.303030

*Note on citation quality: [1]–[9], [17], [18] are well-established
citations from long-settled literature, cited from knowledge and not
independently re-verified page-by-page this session. [10]–[16] were
looked up fresh on 2026-07-22 specifically for this draft; the systems
references ([11]–[16]) are vendor documentation and third-party blog
analysis, not peer-reviewed sources — accurate as descriptions of current
behavior, but worth flagging to a reviewer as such, and worth re-checking
before final submission since vendor docs and blog posts can change.*
