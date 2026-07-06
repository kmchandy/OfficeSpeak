# Feedback on draft_v0 — recorded 2026-06-30

Six points from Mani, with the resulting changes to the framing and the
plan.

---

## (1) The audience is non-programmers, not Python-literate non-distributed-systems users

The draft over-narrowed the audience by requiring Python literacy. Mani
observes that Pat does not need Python for any gallery app — even
loudness_monitor, backyard_birds, wildlife_watcher, the Python-agent
apps. Pat reads English role descriptions; the Python is generated
and maintained by the LLM and the substrate.

**Change to the framing:** the audience is **non-programmers**. Drop
"Python-literate" from the abstract, the contribution claim, and the
substrate-accessibility claim.

The substrate-accessibility claim becomes: *"DSL minimizes the gap from
'I have a domain rule I can describe in English' to 'I have a running
distributed agent.'"* The "Python-literate" qualifier was hiding the
sharper claim.

## (2) The office / org-chart / role-as-job-description mental model is a contribution in its own right

This is new and was missing from the draft. The architecture does
not just expose English contracts — it organises them through a
metaphor from everyday life:

- The system is an **office** (not a network of co-routines).
- Each agent is an **employee with a job description** (the role.md).
- The office.md is the **org chart** showing who reports to whom and
  who passes work to whom.
- Messages are **memos** going from one employee to another.
- Sources are **mailrooms / front desks** bringing work into the office.
- Sinks are **outbound services** taking finished work out.

Pat knows offices. She does not know co-routines, channels, actors,
or message-passing protocols. The mental model uses a vocabulary she
already has.

This is a *pedagogical and cognitive contribution* — choosing a
domain-of-discourse that maps a non-trivial technical structure
(message-passing distributed system) onto a familiar everyday
structure (the workplace).

**Change to the framing:** add a fifth claim — *the office mental
model* — as a contribution co-equal with the two-layer specification
and the substrate. The architecture is more than English-as-source-of-
truth; it is English-organised-as-a-workplace.

## (3) Drop convergence measurement

The draft proposed convergence speed (rounds-to-user-accepted-result)
as an empirical axis. Mani's view: this is a measurement we can't
honestly conduct without user studies we are not going to run. We
will *illustrate* iterative development qualitatively — show what an
iteration session looks like, what the artifacts look like at each
step, what Claude does in response to Pat's edits — but we will not
quantify rounds-to-convergence.

**Change to the framing:** drop "convergence speed" from the empirical
axes. Replace with "iteration patterns we observe" — qualitative,
descriptive.

## (4) Library reuse is not central

The draft claimed library reuse as a contribution. Mani's view: if
Pat can write English specs easily and Claude can read them and
produce working code, writing a new spec from scratch is fine. The
"corpus of validated compositions" framing was overstated.

**Change to the framing:** drop library reuse as a primary claim.
The library is still useful as a set of examples and as a vocabulary
for Pat (so she sees what an English spec looks like), but it is not
a community-composition claim.

## (5) Audience is people who don't know Python or don't want to deal with it

The audience is sharpened to: **people who do not know Python (or who
do but prefer not to engage with it directly) and who are comfortable
talking with an LLM in English**.

This is a broader audience than "Python-literate non-distributed-
systems users" — it includes domain experts, non-programmers,
hobbyists, students before they learn to code, and programmers who
want a higher abstraction level.

Mani is not worried by the "why this draft may still be wrong"
section. That set of concerns assumed an audience that wanted
to read Python or wanted measurable convergence. Both fall away in
the new framing.

## (6) Hold off on writing more paper; plan the empirical work

The short material we have (the four claims, the concessions, and
the new mental-model claim) gives enough focus. The next step is to
plan the empirical work, do it, and then return to expanding the
paper.

The empirical work should be illustrative — case studies of
iterative development, the office mental model documented through
examples, the substrate documented as the mechanism. Not user
studies, not measurements, not benchmarks.

---

## What the contribution looks like, post-feedback

The contribution now stands on five claims, three concessions:

### Claims (revised)

1. **Two-layer specification with an LLM maintainer is a viable
   development model.** English office and role descriptions are the
   durable design; Python is ephemeral, generated and maintained by
   the LLM.
2. **The office mental model is a useful organising metaphor.** Users
   work with offices, role-as-job-description, memos, mailrooms, and
   org charts — vocabulary from everyday life. They do not work with
   co-routines or channels.
3. **Iterative development happens at the English level.** Pat edits
   the English specs (or asks Claude to); the LLM maintains
   correspondence with the Python. We illustrate this with case studies.
4. **A small accessible distributed substrate suffices.** DSL provides
   the message-passing, state management, and snapshot/resume
   machinery so the user is never exposed to distributed systems
   directly.
5. **The methodology is for non-programmers.** Including people who do
   not know Python and people who prefer not to engage with it.

### Concessions (unchanged from v0)

- LLMs can produce equivalent S&R systems directly from English. We
  do not extend that capability.
- We do not claim novelty in decomposition or in any individual
  agent's prompt.
- We do not claim performance benefits over direct LLM-Python.

### Out (from v0)

- Library reuse as a primary claim.
- Convergence measurement.
- "Python-literate" qualifier on the audience.

---

## What I would say the unifying thread is

Mani's framing across the six points pushes the paper toward a single
sentence:

> *We describe an architecture for non-programmer development of
> distributed sense-and-respond systems, in which the system is
> organised as an English-described office with role-as-job-description
> agents; an LLM maintains the Python implementation; and the user
> iterates with the LLM in everyday workplace vocabulary throughout.*

That is sharper than v0's abstract and replaces the central role of
"Python-literate users" and "library reuse" with "office mental
model" and "everyday vocabulary."
