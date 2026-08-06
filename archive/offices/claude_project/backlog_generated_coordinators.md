# For later — allow generated (determinate) coordinators

**Update (2026-07-24):** the taxonomy question this doc was wrestling with — is a
generated multi-inbox agent a coordinator or something else — has an answer now,
worked out while designing office composition (ROADMAP item 1, `phase3_composition.md`):
it's a **department**, not a new flavor of coordinator. The distinction that matters
for `kind` was never really the port shape (a coordinator and a department are both
"an arbitrary number of named ports, no body written here") — it's whether the logic
behind those ports is one of DisSysLab's small, trusted, formally-specified primitives
(`kind="coordinator"`) or not (`kind="department"`), regardless of whether that logic
came from reusing an already-built office or from Claude generating something fresh for
this one case. So "flagged as generated, extra scrutiny" below is just what a
department already is: something with a department's shape whose logic Al (or Claude)
wrote and tested, not something the framework itself vouches for. This doc's "safe
condition" section is still the right technical content for *what makes a generated
multi-inbox agent safe to trust at all* — that hasn't changed, and still matters before
anything gets treated as a department. What's changed is just where the result of that
scrutiny lives in the schema.

Decision direction (not yet in start_instructions): weaken "all coordinators are
registered/predefined" to allow Claude to generate a custom multi-inbox agent when
no registered coordinator fits Pat's need.

## The safe condition (refined)

"Single-threaded + no randomness" is necessary but NOT sufficient. A generated
coordinator is safe (determinate) iff it **conforms to the coordinator execution
model**:

- waits for a message on **exactly one inbox chosen by its state** — a *blocking*
  read;
- **never** reads "whichever inbox is ready" (a non-blocking poll across inboxes) —
  that is nondeterministic regardless of threading (it's the fair-merge behavior we
  keep out);
- processes each message **atomically**;
- **single-threaded**, **no randomness**, **no wall-clock branching**, **no shared
  memory**.

Under this, races and lost updates are excluded by construction; only ordinary
logic/liveness bugs remain (same class as transform bugs — testable, caught by the
channel-count/liveness aid). It stays testable and replayable because it's
deterministic. Async fan-in is still expressed as connections into a single-inbox
agent, not as a generated multi-inbox coordinator.

## Policy (two-tier)

1. **Default:** registered coordinators (merge_synch, select, gate) — verified, trusted.
2. **Escape hatch:** a generated conformant coordinator, only when no registered one
   fits, and **flagged as generated** so it gets extra scrutiny/testing.

## Paper implication

Claim shifts from "coordination is never generated" to "coordination is assembled
from trusted primitives where they fit, and any generated coordinator is confined to
a determinate model that excludes races and lost updates by construction." Weaker but
honest and more flexible.
