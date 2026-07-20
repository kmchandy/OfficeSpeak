# OfficeSpeak "Phase 3" — approving workers before generation

*This step comes after `start_instructions_v3.md`'s Phase 1 and Phase 2 end,
and before the generator (turns an approved spec into `office.md` + role
files, so DisSysLab's existing `compile_office` / `dsl build` can build it).
Phase 1 and Phase 2 are unchanged by this document — this only describes what
happens to their output before it becomes code.*

## Why this step exists

Phase 2 gives a plain-English description of what each office-specific
worker does. Before any of that becomes real code or a real prompt running
inside a trusted, unattended system, someone has to look at the actual
prompt or the actual generated function and say "yes, this is what I meant."
That review is this step. It is required, not optional — unlike Track A's
current step A5 ("the assistant can talk you through it"), which is a
conversational aside, this is a gate the office does not pass through
without.

## The one thing this step does *not* have to decide

Phase 1 already fixed the message shape on every port, before Phase 2 even
began — the "Pass A, every outbox; Pass B, every inbox; never invented"
rule. That means every worker approved here is implementing to a contract
that already exists. **Approval here is a fidelity check against that
contract, not a fresh design decision.** The question is never "what should
this worker's inputs and outputs look like" — Phase 1 already answered that
— the question is only "does this actual prompt or actual code honor what
Phase 1 already committed to for its ports, and does it do the job Phase 2
described." Keeping this distinction explicit is the point of writing it
down: it's what keeps this step fast and mechanical instead of turning into
a second design pass.

## Computational workers (Python)

For each office-specific agent Phase 2 describes as a computational job:

1. Generate a candidate implementation from the Phase 2 description.
2. Construct example inputs **that match the shape Phase 1 already fixed**
   for this worker's inbox(es) — not invented fresh, read off Phase 1's Pass
   A/B record for this port.
3. Run the candidate on those inputs. Show the inputs and the actual outputs
   side by side.
4. The check: do the outputs match Phase 1's fixed shape for this worker's
   outbox(es), and do they match what Phase 2 said this worker should do.
5. Approve or reject.

This is the same kind of check `debug_demo`'s `per_agent_tests.py` already
does for finding a planted bug — the difference is this step runs *before*
the office exists, on a worker that hasn't been trusted yet, not after
something goes wrong.

**A concrete constraint, found by actually building the generator, not
guessed in advance:** an approved computational worker's code must be a
**self-contained, zero-arg factory** — a function that, called once, returns
the real per-message handler (the same shape every stateful hand-written
role in DisSysLab already uses: a fresh closure per agent, so a running
count or a pending value stays private). Everything the handler needs —
constants, helper functions, its own state — must be defined *inside* that
factory, not as a sibling name elsewhere in whatever file it was drafted in.
The generator writes only the factory's own recovered source into the
office's role file; a reference to a name defined outside it will compile
fine and fail at runtime with a `NameError`. Whoever drafts or approves a
computational worker's code should know this going in, not discover it as a
generation-time surprise.

## Judgment workers (LLM)

For each office-specific agent Phase 2 describes as a judgment job:

1. Generate the actual prompt from the Phase 2 description.
2. Show the prompt itself, plus a small number of example inputs and what
   the model actually produced for them.
3. There is no scoring and no right answer to check against — same as Track
   A's step A5. The person approving reads the prompt and the examples and
   judges whether the prompt says what was intended.
4. Separately, still check the *shape* of what came back against Phase 1's
   fixed outbox contract for this worker (a judgment worker's output still
   has to match what downstream workers expect) — this part **is**
   mechanical, even though the content judgment isn't.
5. Approve or reject.

## Rejection — the iterate loop

A rejection at either step does not restart Phase 1 or Phase 2. It goes back
to a revised Phase 2 description (or, if the description was already right
and only the generated prompt/code was wrong, straight to a revised
prompt/code), then repeats: regenerate, retest or reshow, reapprove. This is
the same "iterate until Pat says it's right" discipline Phase 1 and Phase 2
already use — nothing new is introduced here, just applied one level down,
to the worker's actual implementation rather than its English description.

## Exit criteria — the handoff to generation

The generator can run once, for every office-specific agent named in Phase
1:

- either an **approved prompt** (a judgment worker), or
- **approved, tested code** (a computational worker),

and the Phase 1 network (agents, connections, port shapes) is untouched
from when Phase 1 ended. Registered agents (coordinators, `record`) need
none of this — their behavior is fixed, per `start_instructions_v3.md`:
"You need not describe a registered agent; its behaviour is fixed."

## Explicitly out of scope

Matching the current round's own scope: no checkpoint explanation, no
recording or replaying nondeterminism, no debugging of a *running* office.
This step produces enough per-worker confidence to generate and trust an
office once — not the fuller debugging capability that's deliberately
postponed for this round.
