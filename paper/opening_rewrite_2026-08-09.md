# draft_v3 — proposed rewrite of the abstract and opening

*Prepared 2026-08-09. Nothing in `draft_v3.md` has been changed. Each block
below is independent: accept, reject, or edit them one at a time. Rationale
for each is in italics underneath. Section C at the end lists the knock-on
edits these changes create in text that follows.*

---

##  Abstract

Distributed systems that coordinate multiple agents and runs continuously have been used by large organizations for decades.
An investment club, a field scientist, or a parent benefift from such systems too; however,
building and maintaining one requires distributed-systems expertise that
most people don't have. A large language
model can generate code for a distributed system, but may get the coordination subtly
wrong in ways that surface only after the system has been running for a
while. We present OfficeSpeak, which lets someone without that expertise
build, correct, and maintain such a system through an English conversation.
The user describes an **office**: a team of workers, each with a job
description, with information arriving and results leaving. A language model
assembles the office from a small library of trusted coordination primitives
rather than deriving concurrency logic afresh each time, and then explains back in English what it built and the assumptions it made. The user corrects wrong assumptions made by the LLM which then iterates by building a new office.The
English conversation continues through debugging: OfficeSpeak explains what happened during a recorded run instead of giving the user a log file.
A user can ask for a description of a checkpoint - a global snapshot of the system.
reading a concurrency trace.  We report a worked example end to end,
checkpoint and execution-trace explainers verified against a live office.


---

## Block 2 — §1 ¶1 (replaces the current first paragraph)

A member of an investment club wants something that watches market data,
economic news, and social feeds, weighs several strategies against one
another, and tells him when one of them stops working — not once, but every
day. An environmental scientist wants something that reads a set of sensors
continuously and warns her when pollution crosses a threshold that endangers
health. A parent wants something that tutors her children, adapting to what
each child got wrong last week. None of them wants an answer. Each wants a
system: something that keeps running, keeps track of what has happened,
coordinates several moving parts, and can be trusted to do all three
unattended.

*Rationale: the three vignettes are kept nearly verbatim — they are the
strongest writing in the opening — but the topic sentence that framed them
as things LLMs already handle is gone, and the paragraph now closes by
naming what they share. The reader arrives at ¶2 wanting to know why this is
hard, rather than believing it is solved.*

---

## Block 3 — §1 ¶2 (new; this is the turn the draft is missing)

A large language model will write code for any of these, and for a one-off
script the result is usually fine. Software that runs continuously, holds
state, and coordinates concurrent parts is different in kind. Its failures
are not syntax errors that appear on the first run; they are races, lost
updates, and deadlocks that appear only under one particular interleaving,
often long after the system was declared working. This is not a shortcoming
peculiar to language models. Getting concurrency right took the field
decades and took specialists: the constructs, the algorithms, and the
theories of correctness that make these systems dependable were worked out
over forty years by computer scientists, for computer scientists. Neither
the club member nor the scientist nor the parent has that background — and
neither, usually, does the programmer they would ask for help.

*Rationale: this is the plain-language turn already drafted in
`general_audience_pitch_scaffold.md` §2, adapted to the paper's register.
It supplies the "but" the current opening leaves implicit, and it does the
work without any distributed-systems vocabulary, which buys room for ¶5 to
use some.*

---

## Block 4 — §1 ¶3 (new; the thesis, promoted out of its buried position)

Our claim is that the fix is not a better prompt but a smaller job. A model
asked to derive coordination logic from scratch for each new system is being
asked to redo, correctly and silently, work the field found hard. A model
asked instead to *assemble* a system from a fixed set of coordination pieces
that are already written, already tested, and always the same is doing
something far more reliable: choosing and connecting rather than deriving.
OfficeSpeak is that fixed set — a small library of Python coordination
functions, together with natural-language instructions telling a model how
to use them. An entire class of concurrency bug cannot arise in an office
OfficeSpeak assembles, because the machinery that controls concurrency is
library code and is never model-written. What the model does generate is the
content of each worker: the analyst's reasoning, the accountant's
arithmetic. A mistake there is a wrong answer the user can see and judge —
not a race she cannot.

*Rationale: in the current draft this argument is the second-to-last
sentence of ¶2, where it reads as a supporting remark. It is the load-bearing
claim of the paper and needs its own paragraph and its own position.*

---

## Block 5 — §1 ¶4 (new; what the user actually sees)

What the user works with is an **office**. She describes a team: who the
workers are, what each does, what each needs to know, what comes in and what
goes out. She does not write agents, ports, or edges, and never sees them.
The model builds the office and explains it back in the same plain English —
a walk through what happens to one item from arrival to result, and a short
numbered list headed "Things I assumed," enumerating the choices her
description did not settle. That list is the mechanism, not a courtesy: she
can correct only what she can see was assumed. She replies in English, the
model rebuilds, and the loop continues. A first draft need not be right,
because reacting to a concrete office is far easier than specifying one from
nothing.

*Rationale: the current opening goes from "a parent wants a tutor" to
"termination detection, checkpointing, and rollback-recovery" with nothing
in between. This is the missing beat — the reader gets a picture of the
interaction before being shown the machinery underneath it. Much of this
text exists in §3; having it here in compressed form is worth the
duplication, and §3 can be trimmed accordingly (see Section C).*

---

## Block 6 — §1 ¶5 (the machinery, now motivated)

Because the office is assembled from known pieces rather than improvised, it
also arrives with distributed-systems machinery the user never asked for and
never sees. It detects its own termination even when the network of workers
contains feedback loops. It can take a checkpoint that is a consistent
global snapshot across every concurrently running worker, including messages
caught in flight, so that resuming from it neither drops nor duplicates
work. And because these are the classical mechanisms rather than
approximations of them, the same English conversation extends past building
into living with the system: the user can ask what a saved checkpoint held,
or what happened during a recorded run, and get an answer in English rather
than a concurrency trace she would have to interpret herself.

*Rationale: this is the surviving content of the current ¶2, but arriving
fifth, after the reader knows what an office is and why coordination is the
risky part. The same five terms now land on a prepared reader.*

---

## Block 7 — §1 ¶6 (new; libraries can be layered — the trading-firm example)

A library of this kind does not have to stop at general-purpose
coordination. Consider a small stock-trading firm building a system that
lets each of its traders specify a stock-selection strategy, back-test it
against historical data, and receive trade recommendations as new data
arrives. Every trader gets the same distributed structure — the same
historical-data source, the same back-tester, the same evaluation and
reporting downstream — and what differs from one trader to the next is only
the strategy itself, which each trader describes in English. The firm builds
this by adding trading-specific functions to the OfficeSpeak library: a
documented signature for what a strategy function receives and must return,
a table of the parameters it may vary, and a wrapper that turns any strategy
meeting that signature into a worker wired into the standard office. The
trader never sees the office.

*Rationale: this is the idea from the current draft's third paragraph
("later sections show a further natural-language conversation extending an
already-built office with a new instance"), which was stated abstractly and
in passing. The trading firm makes it concrete before the abstraction
arrives, matching the pattern used for the rest of the rewritten opening.*

---

## Block 8 — §1 ¶7 (new; what the layering buys, and who controls what)

The enhanced library then divides authority in a way neither party could get
from a general coding assistant. The firm controls the structure of every
computation its traders run — what data feeds a strategy, what order things
happen in, what counts as a completed back-test — because that structure is
library code the firm wrote once. Each trader controls the part that is
actually his, and uses a language model to write it, without being able to
disturb anything else. And because the varying piece has a declared shape,
the firm can check each new strategy mechanically instead of trusting the
model that produced it: a trading signal must not depend on data from after
the day it is computed for, an invariant testable by recomputing the signal
on a truncated history and confirming it does not change. The same layering
applies to other subdomains with their own invariants — in an adaptive
tutoring office, the varying piece is a problem generator and the check is
that the generator reproduces its own stated answer. Each layer narrows what
a model is allowed to invent, and each supplies its own check on what it
left open: OfficeSpeak fixes the coordination, a subdomain library above it
fixes the application structure, and what remains for the model is one
function with a known signature and a known correctness test.

*Rationale: the "who controls what" point is the part of your framing that
does not appear anywhere in draft_v3 and is the strongest argument for
layering — it is an organizational claim, not just an engineering one, and a
CHI audience will find it more interesting than the reuse argument. The
no-lookahead and problem-generator checks are drawn from
`FRAMEWORK_EXTENSION_PATTERN.md`, which is where the mechanical-check
requirement is worked out properly.*

---

## Block 9 — optional abstract insertion

*You said the abstract is fine, so this is offered separately rather than
folded into Block 1. If you want the layering idea signalled up front, this
sentence goes after "…rather than deriving concurrency logic afresh each
time":*

> The library is itself extensible: a small firm can add functions for its
> own application area on top, fixing the structure every user's system
> shares while leaving each user an English description of the one part that
> is theirs.

*Rationale: costs 38 words. Worth it only if you expect reviewers to read
the abstract as "one general-purpose library, one class of user." Skip it if
the abstract is already at your length limit.*

---

## Section C — knock-on edits these blocks create

1. **The "why build a framework at all" paragraph (current lines 39–66) is
   now largely absorbed by Blocks 4, 7, and 8, and should probably go.** Its
   second condition — that what the framework encapsulates be "expensive or
   risky to regenerate correctly on demand" — is Block 4's argument stated
   abstractly. Its third condition — that a new use be checkable against the
   framework's contract by means other than trusting the model — is Block 8's
   no-lookahead example stated abstractly. Only the first condition
   (amortization across many uses) survives unillustrated, and it is the
   least interesting of the three. Recommended: cut the paragraph, and if you
   want the three conditions stated as conditions, add two sentences to the
   end of Block 8 naming them as what the trading example just demonstrated.
   Failing that, move the passage down to open §2 as scoping.

   *Note that this reverses my earlier suggestion to trim it lightly — Blocks
   7 and 8 cover substantially more of it than Block 4 did alone.*

2. **Contribution 2's opening clause becomes redundant.** "A small library of
   trusted coordination primitives the model assembles the system from,
   rather than generating coordination code" now restates Block 4 nearly
   word for word. The contribution list can lead with the *consequence*
   ("An entire class of concurrency bug cannot arise…") and drop the setup.

3. **§3's build → explain → correct passage (current lines 260–270) overlaps
   Block 5.** Recommend keeping §3's version — it is more detailed and
   properly placed — but cutting its restatement of *why* disclosure matters,
   since Block 5 has now made that point.

4. **Terminology.** Blocks 1–6 consistently say "workers" for the people-facing
   noun and reserve "agent" for the technical term introduced in §2. The
   title still says "Multi-Agent Systems" and the abstract now says neither
   — worth deciding whether the title should change to match (e.g. "Build and
   Maintain Systems That Keep Running, in English"), or whether the abstract
   should gloss the two vocabularies once.

5. **Section numbering, unrelated but adjacent.** The contributions list cites
   "(Section 8)" for coordination primitives and "(Section 7)" for the
   evidence, but §7 is Related Work and §8 is Preliminary Evaluation. The
   primitives are in §2 and §5. Worth fixing in the same pass.
