# For later — allow generated (determinate) coordinators

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
