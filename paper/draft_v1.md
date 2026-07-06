# Offices: Letting Non-Programmers Command Stateful, Persistent Multi-Agent Systems in Plain English

*Draft v1 — approach (b): the paper begins from a structured-but-plain English
office description (the document a successful onboarding conversation would
produce) and centers on the build → explain → correct loop. The onboarding
conversation itself is described as context and future work.*

Status of evidence: the worked example and the portability result are real; the
explain-back discrimination result is one true-positive plus one clean negative
control, with a pre-registered plant-a-gap protocol whose full run is pending.
Marked [PENDING] where numbers are not yet in.

---

## Abstract

Large language models can generate code, but the systems ordinary people most
need — persistent, stateful services that watch for information and react to it —
are concurrent and history-dependent, exactly where naive generation is unreliable
and unrepeatable. We present **offices**: a way for a non-programmer to command a
running multi-agent system by describing it in structured-but-plain English. The
user describes a small *team of workers with jobs*; a language model turns the
description into an executable graph of message-passing agents and *explains the
graph back* in plain English; the user confirms or corrects; they iterate. The
generated office runs on a small library of *trusted coordination primitives*
(a gate, a synchronizer, an ask-and-wait selector, a shared record/clerk, a source
merge, a router) that make coordination correct by construction and make the office
deterministic wherever determinism is wanted — without restricting what the user
can express. Because coordination lives in the library and only worker *bodies* are
generated, a model error is a *content* error the user can catch, never a
coordination error. We show the loop on a worked example (an investment-club
office), give a preliminary evaluation of substrate portability and of whether the
explain-back lets a non-programmer catch real defects, and argue that the approach
separates cleanly into a wiring layer (checkable) and an agent-specification layer
(the user's to confirm).

## 1. Introduction

Most people who could benefit from software automation cannot build it, and the
software they would benefit from most is rarely a one-shot script. It is a
*persistent service*: watch my club's market data and news and recommend what to
do; watch our customer emails and draft replies from each customer's history; watch
our services and flag unusual behavior. These systems are **stateful** (they
remember), **concurrent** (many things happen at once), and **history-dependent**
(what they do depends on what came before). This is precisely the regime in which
directly generating code from a prompt is fragile: the correctness bugs are
race conditions, lost updates, and mis-synchronized joins, and they are neither
visible in a single output nor reliably reproducible across runs.

We take a different route. Instead of asking a language model to emit correct
concurrent code, we ask it to *assemble a system out of trusted parts* and to
*explain the result back* to the person in their own terms. Concretely:

- The person — a non-programmer we call **Pat** — describes what she wants as a
  small **office**: a team of workers, each with a job, that runs on its own. She
  writes in structured-but-plain English (what the office is for, who the workers
  are, what each does and needs), not in any formal language.
- A language model turns that description into an executable **graph** of
  message-passing agents, drawing coordination from a fixed **library** of
  primitives.
- The model **explains the graph back** to Pat in plain English — who does what,
  who waits for whom, what is assumed — and Pat confirms or corrects it. They
  iterate until it matches her intent.

Two design commitments make this work. First, **coordination is not generated**:
the primitives that control concurrency (serialize, synchronize, ask-and-wait,
share state) are hand-written and trusted, so the model's job is to *choose and
connect* them, not to implement them. Second, **the explanation is a first-class
artifact**: it is how a person with no systems vocabulary evaluates whether the
system is right, and — as we show — it is good enough to let her catch genuine
distributed-data defects.

Framed in classic HCI terms, the two halves bridge Norman's two gulfs. The
structured-plain description bridges the *gulf of execution* ("how do I say what I
want?"); the explain-back bridges the *gulf of evaluation* ("did it do what I
meant?").

**Contributions.**
1. The **office** interaction: a non-programmer commands a persistent, stateful,
   concurrent system through a build → explain → correct loop over a
   structured-but-plain English description.
2. A small library of **trusted coordination primitives** that make an
   LLM-assembled office's coordination correct by construction and deterministic
   where wanted, *without restricting the description language*.
3. A clean **separation of concerns** — a wiring layer (checkable from
   per-agent contracts) versus an agent-specification layer (the user confirms) —
   with the per-agent contract as the seam.
4. A **preliminary evaluation**: substrate portability of one office across
   shared-memory and message-passing realizations, and an assessment of whether the
   explain-back lets a non-programmer catch planted and naturally-occurring defects.

## 2. The office abstraction

An **office** is a network of **agents**. Each agent has one job, its own private
memory (**state**), input ports it reads, and output ports it sends on. Information
enters through **sources** and leaves through **sinks**. The office runs
continuously; it is not a function that is called but a service that reacts.

Most agents are **workers** whose job is described in English and realized by an
LLM prompt or a small piece of code (an analyst who forms a view, a manager who
decides). A few agents are **coordination primitives** drawn from a fixed library:

- **source / sink** — information in / results out.
- **fair_merge** — combine several sources into one stream (used only to merge
  sources).
- **merge_synch** — wait for one message on each named input and emit the combined
  result (a join; e.g., a decider that needs every advisor's argument).
- **select** — read whichever input the agent's state points to; used for
  ask-and-wait (send a request, wait for the reply) and for taking inputs in a set
  order.
- **record (a clerk)** — a shared file that other agents read and update by asking
  a keeper agent; the message-passing realization uses a keeper agent instead of
  shared memory.
- **gate** — admit one item at a time, releasing the next only after a "done"
  signal; used when an agent that owns shared state is updated while handling each
  item.
- **router** — send each item to exactly one place by a condition.

**Determinism via coordination, not restriction.** In a network of
message-passing agents, the only source of nondeterminism is a **merge** — a point
where messages from several streams interleave. If merges are controlled
(merge_synch, select), the office is determinate in Kahn's sense; an *uncontrolled*
merge (fair_merge) is the sole nondeterministic primitive, confined to combining
sources. So determinism, where the user wants it, is achieved by *how the office is
coordinated*, not by limiting what the user may describe. Determinism matters
because it makes the office **testable**: the same inputs produce the same outputs,
so empirical testing is meaningful.

**Coordination is trusted; bodies are generated.** The coordination primitives are
library code, correct by construction and never generated. Only worker bodies are
produced by the model. The consequence is a sharp bound on where model error can
land: a wrong body is a *content* error (the analyst reasons poorly) — testable and
catchable by the user — and can never be a *coordination* error, because the
machinery that controls concurrency is not model-written.

The substrate also endows every office, for free, with distributed-systems
machinery the user never asked for and never sees: **termination detection** that
works even when the agent network has loops, and consistent **checkpoints** for
saving and restoring state. Checkpoints do double duty: the runtime records the
order in which messages are ingested at each fair merge — the office's only source
of nondeterminism — so a rerun from the last checkpoint replays the *exact same*
execution. This gives the user **deterministic replay for debugging**, something
even expert-built distributed systems rarely offer, delivered to someone who never
confronts concurrency. And because each worker body is independent, different
workers may be powered by **different LLMs** — a heterogeneous office — at no extra
cost in the model. These are exactly the properties that ad-hoc generated code does
not reliably have, and they are supplied by the library, not by the model.

The same holds at the office's **boundary**. Sources and sinks are a named registry
presented to the model; the model maps the user's plain-English inputs and outputs
to registered entries by meaning, and an unmatched one is a flagged, unbound port
rather than a silent failure. So the office is assembled from trusted, registered
parts at its edges (sources/sinks) and in its coordination (primitives); only the
interior worker bodies are generated. In this paper we assume the sources and sinks
the examples require are registered — backed by replayed or mock data where a live
connector is impractical — and treat helping the user register brand-new sources
and sinks as future work.

**Roles and agents (kept under the hood).** DSL separates a **role** — a reusable
job template with named inputs and outputs — from an **agent**, an instance of a
role wired into a particular office, exactly as a class relates to an object. Two
analysts, VAL and OPPO, *may* be two agents of one analyst role differing only in
per-instance parameters (a value strategy vs an opportunities strategy), or they may
be two separate roles; both are correct. Role reuse is a capability DSL offers, not
something the model is required to find — we do not ask Claude to recognize shared
roles across a description, since separate roles yield the same office behavior.
This gives reuse where it is used, but the formalism (ports, wiring, the words
"role" and "agent") is never shown to the user. It has a natural everyday analog — a job description versus the
people who hold it — and it surfaces, if at all, only in those terms ("VAL and OPPO
are both analysts"). A role's port signature is precisely the contract below, so
the user specifies ports implicitly, in plain words, by saying what each worker
needs and sends.

Ports are where this indirection is most tempting to leak, and we keep it hidden.
The user describes routing **agent-to-agent**, naming recipients ("if it fits, send
it to the writer; otherwise to the reject log"), which is how people naturally
think. The model factors that single statement into what DSL needs — a role with
outputs, plus wiring that binds those outputs to the named recipients — and may (but
need not) reuse a role when the same branching recurs. The coupled,
recipient-naming form is the user's; the decoupled, reusable port-and-wiring form is
the model's; converting between them is a central part of the model's job, not
incidental parsing.

**Two layers, one seam.** Every agent has a **contract**: what it reads, what it
sends, what state it owns. Above the contract is the **body** (how it turns reads
into sends); around it is the **wiring** (edges between contracts). This gives two
kinds of problem and one seam between them:

- A **wiring problem** is a graph that is inconsistent with the contracts: a
  declared input nothing feeds, a multi-input consumer with no explicit join, a
  shared record read-and-written with no gate, an uncontrolled merge. These are
  checkable **from the contracts alone**, without reading any body.
- An **agent-specification problem** is a body that does not do what its contract
  or the user intends. These require reading the job descriptions.

The contract is the seam, and it is *derived from* the specification and *consumed
by* the wiring (spec → contract → wiring). Making the contract explicit is what lets
the two reviews proceed independently.

## 3. Commanding an office in plain English

Pat never writes agents, ports, or edges. She writes a **structured-but-plain**
description — flexible prose organized around a few questions: what is the office
for, what comes in and goes out, who are the workers, what does each do and *need
to know*, and what rules must hold (one-at-a-time, who waits, learning over time).
The structure is not a formal language; it is the shape a good description takes,
and it doubles as scaffolding so a first-time Pat knows where to begin. (Producing
this description through a guided conversation is the subject of ongoing work,
Section 8; here we take the description as given.)

A single principle runs through the description. Pat's natural unit fuses *what* a
worker does with *whom* and *when* it communicates — "the accountant works out the
fees and sends them to the manager" — and names recipients inline rather than
through ports. Her description is natural, coupled, and fused; the graph the system
needs is clean, decoupled, and separated (bodies, ports, wiring, coordination). The
model is the translator that pulls apart what Pat runs together. This is the case
for a model in the loop rather than a form or a parser: a form would force Pat to
pre-separate behavior from communication, which is not how she thinks; the model
lets her fuse and does the separation itself.

**Realization: the loop runs inside a general agent host.** We do not build a
bespoke interface. DSL is packaged as a plugin for a general agent platform (here,
Claude's Cowork), bundling the pip-installable library — with its trusted
primitives, termination detection, and checkpoints — and three skills that shape the
host's own conversation: onboard, build, and explain. The host supplies everything
else it already does well: it holds the plain-English conversation, writes the
office (graph plus generated worker bodies) into the user's folder, renders the
office as a diagram, edits it on a correction, runs it in a sandbox, presents the
output, and can schedule the periodic office as a running service. The contribution
is the substrate, the abstraction, and the method; the host is interchangeable and
improves independently, so advances in general agents make the office *easier* to
build, not redundant.

From the description the model **builds** a graph and **explains it back**: a plain
account of the team, a walk through what happens to one item start to finish, and a
short list of the choices the description did not pin down ("things I assumed").
Pat reads the explanation — optionally alongside a simple diagram — and **corrects**
it. The correction is itself plain English ("the accountant must see what we
currently hold"), and the model rebuilds. The loop is the product; a first draft
need not be right, because it is cheaper for a person to *react* to a concrete
office than to *specify* one from nothing.

## 4. Worked example: the investment-club office

**Pat's description (abbreviated).** Recommend buy/sell/hold for a club holding
mutual funds and cash. Once per period the office receives a batched feed
(financial data, forecasts, breaking news) and the club's decisions from the
previous period. Two analysts — **VAL** (value investing) and **OPPO** (emerging
opportunities) — each read the feed and have access to the club's current portfolio
and history, and each recommends an action plan. A manager, **MGR**, collects both
analysts' recommendations, proposes a plan, checks the fees with an accountant,
**ACNT** (taxes and transaction costs), then writes a final plan to a file,
**RECOMMEND**.

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

The model chose the right coordination without being told the words: a **join**
(merge_synch) so MGR waits for both analysts on the same period; an
**ask-and-wait** (select) for the MGR↔ACNT back-and-forth; a **record** (Ledger)
for the shared portfolio and history; and it kept the per-item fan-out minimal —
the feed reaches the two analysts, and ACNT is demand-driven, handed the plan by
MGR rather than put on the feed. The per-period batching gives natural
one-at-a-time processing.

**The explanation Pat reads (abbreviated).**
> Each period, the team gets the day's information and last period's club
> decisions, bundled together. VAL and OPPO each read it, check the club's current
> holdings and history, and each writes a recommendation. MGR waits for both, puts
> together a proposed plan, and asks ACNT what it would cost in taxes and fees. ACNT
> works that out and reports back; MGR then finalizes and writes the plan to
> RECOMMEND.
>
> Things I assumed — the two analysts are treated equally; MGR has the final say;
> **ACNT works out the taxes from the proposed plan alone — it does not look at what
> the club currently holds.** Tell me if any of these should be different.

**Pat's correction.** The last assumption is wrong, and Pat can see it in plain
English without any systems knowledge: taxes depend on cost basis, which lives in
the portfolio.
> "The accountant has to see what we currently hold — otherwise the tax numbers are
> guesses."

**The revised graph** adds one edge, `ACNT <-> Ledger`, so the accountant reads the
portfolio and history before pricing. Nothing else changes.

This is the loop in miniature, and it makes the central claim concrete: a
non-programmer caught a genuine distributed-data defect — a computation reading a
value it was never given access to — through a plain-English explanation, and fixed
it with a plain-English instruction.

## 5. Why an office can be correct and testable

Three things do the work.

**Trusted coordination.** Because the gate, join, selector, record, merge, and
router are library code, the office's coordination is correct whatever the model
does. The model's freedom is confined to choosing and wiring them and to writing
worker bodies.

**Determinism where wanted.** With merges controlled, the office is determinate, so
the same inputs reproduce the same outputs and testing is meaningful. Uncontrolled
merge is available (for source combination) but is the only nondeterministic
primitive and is used deliberately.

**Checks on the seam.** Wiring problems are contract-vs-graph mismatches and are
statically checkable independent of bodies. A single structural checker covers
several: an input nothing feeds (a missing dependency, e.g., ACNT before the fix);
a multi-input consumer with no explicit join (an implicit merge that would break if
the office were parallelized); a gate with no matching release (a stall); a body
that references inputs its contract does not declare (a contract violation). This
static checker is the systems-side complement to the explain-back: it catches the
structural faults a plain-English description cannot be expected to surface, while
the explain-back catches the intent mismatches a static check cannot judge.

## 6. Preliminary evaluation

**Substrate portability.** The same investment-club office was realized on two
substrates — shared-memory (a shared record) and message-passing (keeper agents and
broadcast) — driven only by a change of prompt. The coordination structure was
preserved across both (the gate, the join, the ask-and-wait all survived), and the
message-passing realization independently produced a *better* decomposition (a
custodian agent that owns the real portfolio, separate from the decider). This
supports the claim that an office is a substrate-independent description whose
coordination is intrinsic, not an artifact of one realization.

**Does the explain-back let a non-programmer catch defects?** We assess this in the
regime that matters: whether a plain-English explanation surfaces a real defect as
something the user can act on.
- *Naturally-occurring (true positive).* In a message-passing realization, a
  tax-and-fees agent kept its own copy of holdings and was not wired to the
  portfolio owner. The explain-back flagged exactly this, phrased as a question the
  user could answer ("tell me if it should ask for the current holdings"). The
  worked example in Section 4 is the same defect class in the shared-memory office.
- *Negative control.* On a realization where the tax agent *was* correctly wired to
  the record, the explain-back stayed silent about it — it responds to the wiring,
  not to the agent's name, so the positive was signal rather than boilerplate.
- *Planted defects (protocol).* We pre-registered a plant-a-gap protocol: six
  single-edge mutations of a verified office, each with one known defect, run
  held-out through the explainer, scored for detection and false positives. The
  pre-registration predicts that defects which change an item's journey or that the
  explanation's checklist probes (missing input to a consumer, absent
  serialization, a broken join, a missing wait) are caught, while silent omissions
  and liveness stalls are missed — mapping the explain-back's coverage envelope and
  motivating the static checker for the rest. Full results are [PENDING].

**Why not just a general coding agent? (the ablation that carries the claim.)** A
capable general agent can already hold a plain-English conversation, generate code,
and iterate — so the *interaction* is not our contribution and we do not claim it.
The contribution is that the assembled system is a *correct, reproducible*
distributed application, which a general agent's free-form code is not. We make this
concrete with an ablation: the *same* English office is built two ways — (a) through
the trusted substrate, and (b) by a general agent asked to write the office directly
in Python. We then check for the two distributed-systems properties the substrate implements
today: **termination detection** — the office correctly detects when it has finished
the current work, *including when the agent network contains loops* (the hard case,
here the manager-accountant back-and-forth) — and **checkpoints** — the office's
state is saved consistently and can be restored. The prediction is that (a) has these
by construction while (b), free-form generated code, lacks them or implements them
incorrectly — the substrate supplies distributed-systems machinery the user never
sees and the model never has to generate correctly. (Monitoring, message-rate, and
performance instrumentation exist as future substrate features and are not claimed
here.) This comparison is the direct answer to
"isn't this just a general agent?": the value is the substrate and method, for which
the conversational host is interchangeable, not the plain-English loop itself.
[PENDING run.]

**Does structure reduce iteration?** Across successive plain-English descriptions of
the same office, adding light structure (organized around what each worker *needs to
know*) removed the ambiguities that previously required back-and-forth (the flow,
the join, the ask-and-wait became stated rather than inferred) and pushed the
residual gaps to genuine user-decisions (whether the accountant sees holdings;
whether shared records are updated), which is what the explain-back is meant to
confirm. This is qualitative; a controlled study is future work.

## 7. Related work

**Decomposition of LLM reasoning.** Chain-, Tree-, and Graph-of-Thought decompose a
*problem* into steps, a tree, or a graph of reasoning. We decompose a *system
design* into a network of persistent, message-passing agents; the artifact is not a
reasoning trace but a running service.

**Models of concurrency.** Offices are Kahn process networks with controlled
merges; the determinism argument and the role of merges as the locus of
nondeterminism follow the dataflow tradition (Kahn; the merge anomaly; Boolean
dataflow) and the tagged-signal framing. Coordination requirements echo workflow
patterns. Reasoning about correctness without determinism draws on UNITY-style
program logic; determinism is what our testing side relies on.

**End-user and naturalistic programming; LLM agent frameworks.** [TODO: position
against end-user programming, PBD, and current LLM multi-agent frameworks, which
generate orchestration code directly rather than assembling from trusted
coordination parts with an explanation loop.]

## 8. Limitations and future work

- **The description is assumed, not elicited.** Producing the structured-plain
  description through a guided onboarding conversation — so a Pat off the street
  knows where to begin — is designed (a team metaphor, an example gallery, a story
  walkthrough, a "newcomer" probe for hidden data needs) but not yet evaluated.
- **Scale via composition.** The approach targets small, comprehensible offices.
  Larger systems are built by *composing* offices — wiring one office's outputs into
  another's inputs, or nesting an office as a single worker. Stream composition
  preserves determinism; shared state across offices is the hard case and open.
- **Corpus breadth.** The evidence centers on one office family (a deliberative
  panel). Prediction and anomaly-detection offices exercise different coordination
  (temporal joins, delayed matching of outcomes to forecasts, per-key state) and are
  the natural next targets.
- **Evaluation rigor.** Explain-back scoring is currently by the authors;
  the claim that ultimately matters — non-expert humans catching defects from the
  explanation — needs a human study. Model-as-judge is mitigated by
  pre-registration but not removed.

## 9. Conclusion

Offices let a non-programmer command a persistent, stateful, concurrent system by
describing a team of workers in plain English, having the system explain the result
back, and correcting it in plain English. Coordination is trusted rather than
generated, so the system can be correct and — where wanted — deterministic without
restricting what the user may say, and the explanation is good enough to let a
person with no systems vocabulary catch real defects. The worked example shows the
whole loop, including a user catching and fixing a genuine distributed-data bug.
