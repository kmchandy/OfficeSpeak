# Paper notes — checkpoint explainer and per-agent activity log

Working notes for the CHI 2027 submission (deadline September 10, 2026). This
file is raw material for the paper, not tester-facing documentation — nothing
here should be assumed to already be built unless a section says so
explicitly. Add to this file as the two features below are designed and
built, and as new paper-relevant decisions get made.

---

## 1. The general capability these two features are instances of

OfficeSpeak already translates two things into plain English for a
non-programmer: the office's structure (the workers and how they connect),
and its own uncertainty (the "Things I assumed —" list, and the correction
loop). The checkpoint explainer and the per-agent activity log are a third
and fourth instance of the *same* underlying capability: taking a formal,
provably-correct distributed-systems object and rendering it as English a
non-programmer can read and reason about, without ever seeing the
formalism.

That's the framing worth stating explicitly in the paper: OfficeSpeak's
contribution isn't "one feature that builds a team from English," it's a
general translation layer that works in both directions — English → formal
system, and formal system → English — and that this second direction is
what's being extended here to cover a system's internal recorded state
(snapshot) and its internal history (activity log), not just its structure.

---

## 2. Checkpoint / snapshot explainer

### What a snapshot actually contains (real, implemented, v1.6)

From `dissyslab/snapshot.py`, for a given office and snapshot number N:

- `manifest.json` — office name, N, timestamp, agent list, edges.
- `agents/<agent_name>.pkl` — one pickle per agent, the object returned by
  that agent's `save_state()`.
- `channels/<dst_agent>__<dst_port>.pkl` — one pickle per edge, the list of
  messages that were in flight on that edge at the moment of the cut.

This is captured via a Chandy-Lamport distributed snapshot (Chandy & Lamport,
*Distributed Snapshots: Determining Global States of Distributed Systems*,
ACM TOCS, 1985), adapted with a four-way recovery handshake and a
source/sink boundary protocol so a crash-and-resume produces no duplicate or
missing messages at the office's boundary with the world. Full spec:
`docs/algorithms/CHECKPOINT_RESUME.md`. Implementation: `core.py`,
`os_agent.py`, `snapshot.py` (~500 lines).

The explainer's job: read a snapshot's three pieces (manifest + per-agent
state + per-edge channel state) and produce English sentences of exactly
the two forms Mani specified: "the messages between this outbox and that
inbox were ..." and "the state of worker X was Y." No new data needs to be
captured — this is a translation layer over data that already exists.

### Worked example to use in the paper: recovery_demo (Monte Carlo π)

Chosen because it's small, already built, already documented, and easy to
describe in one sentence: it estimates π by classifying random points as
inside or outside a circle.

```
csv_points_source → Alex (inside_classifier)  → Pi (pi_combiner) → display
                  ↘ Bob   (outside_classifier) ↗
```

Five agents; three are stateful (their saved state, from the real gallery
README table):

| Agent | State saved |
|---|---|
| `csv_points_source` | `{"cursor": int}` — how many points read so far |
| Alex (`inside_classifier`) | `{"count": int}` |
| Bob (`outside_classifier`) | `{"count": int}` |
| Pi (`pi_combiner`) | `{"inside": int, "outside": int}` |

Illustrative English translation (for a figure or quote box in the paper —
exact numbers to be replaced with a real run's output once the explainer
exists):

> "At this snapshot, Alex had counted 412 points inside the circle and Bob
> had counted 138 outside. Pi's running estimate was based on 550 total
> points. Three points were still in transit — one between the source and
> Alex, two between the source and Bob — and will be replayed if the office
> needs to recover from here."

### Novelty framing for the paper (tie to the "bridges" theme)

Candidate claim: OfficeSpeak lets a non-programmer both build a distributed
system in plain English and have that system's own internal, formally
correct machinery (a Chandy-Lamport snapshot) explained back in plain
English — not just the system's surface-level structure. This is a concrete
instance of a "bridge" between HCI (end-user program construction and
comprehension) and distributed-systems theory (global-state consistency).

**Not yet verified: the word "first."** Before this goes in the paper as
written, it needs an actual related-work check (workflow/durable-execution
engines like Temporal or AWS Step Functions; LLM-based no-code agent
builders like AutoGen Studio or LangFlow) to confirm no prior system already
does this combination. Treat any novelty claim here as a placeholder until
that search is done.

**Resolved:** reading (a) — use recovery_demo as-is, no new example app.
Confirmed by Mani.

---

## 3. Per-agent activity log ("debug trace")

### Scope, as discussed

Not a single globally-ordered trace across the whole office — a local,
per-agent log. Each agent records, in order, the messages it received and
the messages it sent. The English explanation shows what one worker did:
"here is the message it received, here is what it sent."

### Why this is more tractable than a full cross-agent trace

A full cross-agent ordered trace ("who sent to whom, in a single global
order") requires solving distributed event ordering (Lamport clocks / a
happened-before relation) — real, nontrivial work, and it would mean adding
new logic to the same OS-layer control path (`core.py`, `os_agent.py`) that
carried the termination-detection bug fixed just six days ago (July 15).

A **per-agent** log avoids that entirely: it's purely observational — each
agent appends to its own list on every receive and every send, as a side
effect, without changing what any agent decides to do or when. It doesn't
need cross-agent ordering, doesn't touch the termination/checkpoint control
logic, and is low-risk to add this close to the deadline.

### A nice property worth stating in the paper: it works for LLM workers too

The existing debugging design (`docs/internals/debugging_aids_decision.md`)
deliberately scopes worker-isolation testing (aid (a), already built as
`OfficeSpeak/offices/debug_demo/`) to computational workers only — an LLM
worker's judgment isn't a fixed function, so it can't be graded the way a
Python body can. The per-agent activity log doesn't evaluate a worker's
judgment at all; it just shows what happened. So it applies uniformly to
both computational and LLM workers, unlike aid (a). Example English
translation: "The accountant received the manager's proposed plan and the
club's current holdings, and sent back a tax estimate of $340." That's true
and useful whether the accountant is a Python function or an LLM prompt —
worth flagging as a point of contrast in the paper.

### How this relates to the two debugging aids already scoped

From `debugging_aids_decision.md`:
- **Aid (a)**, built: test one worker in isolation on hand-picked inputs —
  catches wrong-body bugs, computational workers only.
- **Aid (b)**, scoped but not built: per-channel sent/received counts —
  catches a stuck coordinator (liveness), doesn't explain content.
- **This (new)**: a per-agent log of real messages from an actual run,
  explained in English — shows real execution, not synthetic test cases;
  works for both worker types; doesn't require solving liveness or
  cross-agent ordering.

### Theoretical bridge bonus for the paper

If this is ever extended from a per-agent log into a true cross-agent
causally-ordered trace, that's precisely Lamport's happened-before relation
(Lamport, *Time, Clocks, and the Ordering of Events in a Distributed
System*, CACM, 1978) — the same Lamport already in the paper via
Chandy-Lamport snapshots. Worth one sentence in a future-work paragraph even
if not built now: it gives the paper a single unified theoretical lineage
(Lamport 1978 → Chandy-Lamport 1985) running under both the checkpoint
explainer and a possible future trace explainer.

### Assessment

Good idea, and more tractable than the version discussed last turn (this
one is local per-agent, not a global ordered trace). Recommend building it
as a pure append-only observability layer — don't touch the OS-layer
control logic that was just fixed. Complements, rather than duplicates, the
two aids already scoped.

---

## 4. Cross-agent trace via logical time (Lamport clocks) — decided 2026-07-21

Mani's proposed rule, verbatim: sources timestamp messages starting at 0,
increasing with each message a source emits. Each agent keeps its own
timestamp. On receiving a message with timestamp t, an agent sets its own
timestamp to the larger of t+1 and its current timestamp. An agent
timestamps its outgoing messages with its own current timestamp. Collect
every agent's log and play it back action by action.

**This is Lamport's logical clock algorithm** (Lamport, *Time, Clocks, and
the Ordering of Events in a Distributed System*, CACM, 1978) — the same
Lamport as in Chandy-Lamport snapshots, already in the paper via the
checkpoint explainer. Deciding to actually build this (not just gesture at
it as future work) upgrades that connection from a one-line aside to a real
second contribution resting on the same theoretical lineage. Good move for
a "bridges" pitch: one paper, one 1978→1985 throughline, two plain-English
explainer features hanging off it.

### A correctness refinement worth making before building it

As stated, the update rule is `new_clock = max(t+1, current_clock)`. This
differs from the textbook rule in one way that matters here: the textbook
rule increments the local clock on **every** event at a process (send,
receive, or internal), not only when an incoming timestamp forces it
higher. Concretely: if an agent's current clock is already ≥ t+1 when it
receives a message timestamped t, the clock as specified **does not
change** on that receive. If the agent then sends output in response, and
later receives a second, "stale-relative" message and sends again, both
outputs can end up tagged with the *same* timestamp. For a "playback,
action by action" view, two different actions by the same agent landing on
an identical timestamp is a real problem — there's no way to say which
happened first from the timestamp alone.

Standard fix: increment the local clock by 1 on **every** send or internal
step, not only on receive-with-a-larger-t. I.e.: on receive, `clock =
max(clock, t) + 1` (always increments); on any other event that produces
an outgoing message, `clock = clock + 1` first, then tag the outgoing
message. This guarantees every action at a given agent gets a strictly
higher timestamp than the last, so a single agent's own actions are always
totally ordered by timestamp alone.

### Two more things worth deciding before building

- **Coordinators with multiple inbound messages.** `merge_synch` (and
  similar) can combine messages from more than one inport into a single
  combined receive (see `synchronizer_role`'s dict-merge behavior). The
  rule generalizes naturally: take the max over *all* contributing
  incoming timestamps, i.e. `clock = max(clock, t_1, t_2, ...) + 1` for a
  combined receive, not just one `t`.
- **Total order for the playback needs a tie-break.** Lamport timestamps
  give a partial order consistent with causality (happened-before ⇒
  smaller timestamp), not a full total order — two actions at *different*
  agents can legitimately land on the same timestamp if neither caused the
  other. To render one linear "playback," sort by `(timestamp, agent_name)`
  or similar. Worth stating precisely in the paper: the playback shown to
  Pat is **a valid causally-consistent linearization** of what happened,
  not *the* one true real-time order — real-time order isn't even a
  well-defined concept for an asynchronous distributed system without
  synchronized clocks. This is a genuinely nice, technically correct thing
  to explain to a non-programmer, and worth a sentence in the paper: the
  system is honest with Pat about what kind of ordering guarantee she's
  looking at.

### Implementation placement

Follow the same pattern already used for checkpoint markers: the timestamp
should be OS-layer metadata attached to each message send/receive, invisible
to the worker's own code — not something the client layer computes or sees.
This mirrors `docs/algorithms/CHECKPOINT_RESUME.md`'s existing client/OS
layering (the client layer never knows about `checkpoint(N)` messages; the
OS layer intercepts and forwards them). Keeping the Lamport timestamp
entirely in the OS layer means no worker's code (Python or LLM prompt) ever
needs to know this exists — consistent with the project's whole design
philosophy of keeping the formalism invisible to the person and the worker
author alike.
