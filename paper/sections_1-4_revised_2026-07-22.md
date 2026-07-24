# Sections 1–4, revised — addresses two gaps found 2026-07-22

Not a replacement for `draft_v2.md` yet — a standalone revision of its
Abstract through Section 4, for review before merging. Sections 2 and 3
(the Kahn-network formalism and the office mental model) are carried over
essentially unchanged; they weren't part of either gap. What changed is
the Abstract, the tail of Section 4, and the Contributions list, to fix:

1. **Gap 1 — the "Things I assumed" correction loop was missing from the
   contribution statement**, despite being the one claim that survived
   every reframing in `reframing_log.md` (v1 through v10) and the
   best-evidenced one (the cold-test protocol exists specifically to
   validate it).
2. **Gap 2 — the novelty claim was asserted, not grounded.** Below is a
   real related-work pass (searched 2026-07-22, not from memory), used to
   turn "no prior system combines all three" from an assertion into a
   claim positioned against specific, named, current systems.

---

## What the search found (for Section 7's eventual use, and to ground the
## claim below)

- **LangGraph** does checkpoint — but its checkpointer saves a single
  graph/thread's state at each super-step; it has no automatic failure
  detection ("no supervisor, no watchdog, no heartbeat") and, if two
  processes try to resume the same thread concurrently, "no built-in
  coordination to prevent both from executing." One industry analysis
  states this plainly: LangGraph's (and CrewAI's, and Google ADK's)
  checkpoints are fault *recovery*, not a consistent distributed
  snapshot, and fall short of durable execution for production agent
  workflows.
- **CrewAI** has no built-in checkpointing for long-running workflows at
  all; its hierarchical delegation is reported fragile enough in
  production that teams fall back to sequential mode after repeated
  failures.
- **AutoGen** bounds runaway agent loops with a hard cap
  (`max_consecutive_auto_reply`) — a crude circuit breaker, not a
  termination-detection algorithm that reasons about whether the network
  has actually gone quiescent.
- **Temporal** genuinely offers durable execution (state persisted,
  resumable after a crash) — but workflows are written in real
  programming languages (Go, Java, TypeScript, Python, .NET, PHP), with
  no natural-language or no-code interface. It solves durability for
  programmers, not accessibility for non-programmers.
- **End-user natural-language programming research** (e.g., the CHI 2025
  paper on how people communicate programming tasks in natural language)
  is an active area, and separately, HCI work on mixed-initiative systems
  establishes that proposing a correction the user can accept or reject
  is a known interaction pattern. But nothing found combines that
  correction pattern with actual distributed-systems guarantees — the
  work in this space targets NL-to-code translation generally, not
  persistent multi-agent systems with checkpoint/termination properties.

Net: the honest claim is not "first system to do X" in isolation — each
piece (checkpointing, termination bounds, NL correction loops) exists
somewhere. The claim that survives scrutiny is that no system found
combines *natural-language specification with an explicit,
assumption-disclosing correction loop* **and** *distributed-systems
correctness guarantees that are actually verified to hold* (a
consistent global snapshot across concurrently running agents,
not a single-thread state dump; termination detection under cycles, not
a call-count cap) — in one conversational system built for
non-programmers. That's a narrower, defensible claim, not a sweeping one.

---

## Abstract (revised)

Distributed systems — programs that run continuously, keep state, react
to asynchronous inputs, and coordinate several agents — have been used by
corporations for decades. Individuals, such as small business owners,
with limited programming skills, can benefit from them too. A challenge
for non-programmers is not only to build distributed systems, but also to
debug and maintain them. Large language models can generate code, but
generating stateful, concurrent systems is more difficult than generating
sequential programs, and existing multi-agent LLM frameworks that do
target this space either lack consistent state-recovery guarantees under
concurrency or require writing real code.

This paper presents **OfficeSpeak**, a system that converses in English
with non-programmers to build, understand, debug, and maintain
distributed systems. The user describes an *office* — a team of workers,
each with a role stated in English. OfficeSpeak assembles a network of
message-passing agents and explains the network back in English,
including an explicit list of what it assumed and could not determine
from the description alone; the user corrects it in English, and the
system rebuilds — the same loop then extends to debugging and
maintenance, where the user asks for an explanation of a saved checkpoint
or a run's recorded history and gets one in English. OfficeSpeak generates
code for agents but not for their coordination; it manages concurrency
with a small set of trusted coordination primitives, so the systems it
generates gain distributed termination detection and consistent
global-snapshot checkpointing that the user never specifies and never
sees the machinery for. The paper gives examples of OfficeSpeak building,
correcting, debugging, and running distributed systems, and positions
these guarantees against current multi-agent and workflow frameworks that
either do not provide them under concurrency or provide them only to
programmers.

## 1. Introduction

*(unchanged from draft_v2 — the investment-club / facilities-manager
motivation and the three framing questions still hold and weren't part of
either gap)*

## 2. A Distributed System

*(unchanged — the Kahn-network / agent / channel formalism)*

## 3. How Non-Programmers Specify Distributed Systems

*(unchanged — the office mental model, org chart as 4-tuples)*

## 4. Mapping English Specifications to Systems (revised from "OfficeSpeak turns..." onward)

English is ambiguous. We cannot prove that the network that is generated
is what the user had in mind. We do, however, use concurrency constructs
to increase the likelihood that the generated network matches the user's
expectations, and — critically — OfficeSpeak does not try to hide its own
uncertainty. The process for converting an English description of an
office to a network of agents takes multiple steps and produces, at the
end, not just a graph but a **disclosure**: a short, explicit list of the
choices the description left open.

OfficeSpeak turns a description into a network of message-passing agents,
explains the network back to the user — who communicates with whom — and
states, as a numbered "Things I assumed" list, exactly what it filled in
without being told. This is not a decoration on the explanation; it is
the mechanism that makes the loop work. The user reads the list and
corrects any wrong assumption in plain English — "the accountant has to
see our current holdings" — or asks for clarification, and OfficeSpeak
rebuilds. The conversation continues until the user thinks the office
represents what she had in mind. This "build → disclose assumptions →
correct" loop is the one claim that has held up, unchanged, across every
revision of this project's own contribution statement, and it is
independently evidenced: a pre-registered, held-out test protocol (nine
cases, uncontaminated fresh instances, expected outcomes fixed before
running) exists specifically to check that the disclosure surfaces real
gaps rather than staying silent or crying wolf.

She isn't done once the office is built and corrected, though — she can
also ask OfficeSpeak to explain what's happening *inside* a running or
previously-run office, in the same English register:

- Debugging by looking at each agent's own input and output, isolated
  from the rest of the office — driving one worker at a time on
  hand-picked examples.
- Debugging by asking for the recorded history of a run: every message
  every agent sent and received, ordered by a physical-time-grounded
  logical clock (in the tradition of Lamport's happened-before relation
  and hybrid logical clocks such as Kulkarni et al.'s), merged into one
  causally-consistent story and narrated in English, one action at a
  time.
- Asking OfficeSpeak to explain a saved checkpoint: what each worker's
  own memory held, and what messages were still in flight, at the moment
  the snapshot was taken — the same global-snapshot consistent-cut
  algorithm the recovery machinery itself depends on, made legible rather
  than left as an implementation detail.

Larger offices are built by wiring smaller ones together — connecting one
office's outputs into another's inputs, or nesting an office as a single
worker inside a larger one. *(Note for Mani: per your 2026-07-22
correction, systematic compositionality — validated standalone offices
recomposed into new ones — is not yet built; this sentence should either
be cut or explicitly marked as a demonstrated-only-informally capability
until task #34 lands. Left in as a placeholder for that decision, not a
claim to submit as-is.)*

OfficeSpeak is based on two ideas: first, limit the LLM's role; second,
serve as a translator of system issues into English. The system consists
of (1) agents specified in English by the user and (2) agents that manage
message flow between user agents or carry out operating-system functions
such as checkpointing. We call the former user agents and the latter
substrate agents. LLMs generate user agents but never substrate agents;
OfficeSpeak has a small, fixed set of substrate-agent types, and the
LLM's task is to choose which to use, not to implement them.

The user's description of an office, OfficeSpeak's explanation (including
its disclosed assumptions), the user's corrections, and its explanations
of checkpoints and recorded execution history are all in English. In HCI
terms, this bridges Norman's *gulf of execution* ("how do I say what I
want?") and *gulf of evaluation* ("did it do what I meant — and what is
it actually doing, right now, underneath?").

**Contributions.**

1. The **office** interaction: a non-programmer builds, understands,
   corrects, debugs, and maintains a persistent, stateful, concurrent
   distributed system through an ongoing English conversation, in which
   the system explicitly discloses what it assumed and revises on
   correction — evidenced by a pre-registered held-out test protocol, not
   just demonstrated once.
2. A small library of **trusted coordination primitives** that the model
   assembles the system from, rather than generating coordination. An
   entire class of concurrency bug — races, lost updates, a deadlocking
   hand-written gate or queue — cannot arise, because that machinery is
   library code, not model-written. The assembled office also gains
   distributed termination detection (correct even with feedback loops,
   unlike a fixed reply-count cap) and consistent global-snapshot
   checkpointing (a genuine global-snapshot consistent cut across
   concurrently running agents, including in-flight messages — not a
   single-thread state dump with no cross-process recovery coordination)
   — properties the user never specifies and current multi-agent LLM
   frameworks either do not provide under concurrency or provide only to
   programmers writing real code.
3. **Debugging and understanding by conversation**: explain any agent's
   isolated behavior, a recorded run's message history (ordered by a
   physical-time-grounded logical clock), or a saved checkpoint's
   contents, in plain English, so a non-expert can localize a bug or
   simply understand what the system did — without re-executing anything
   and without requiring the user to read a formalism. *(Deliberately not
   claimed: bit-for-bit deterministic replay of a prior run. That is a
   harder, separate problem — capturing every source of nondeterminism, a
   worker's LLM calls included — that remains future work.)*
4. A clean **separation of concerns** — a wiring layer (checkable from
   per-agent contracts) versus an agent-specification layer (the user
   confirms), with the contract as the seam.
5. An **evaluation**: held-out build → disclose → correct → debug on
   offices of several shapes, showing the generated systems run,
   terminate, checkpoint, and let a non-expert catch genuine coordination
   defects through the disclosure mechanism.
