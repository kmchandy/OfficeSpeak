# OfficeSpeak "start" module — cold-test record

A running record of cold tests of the **start** module (produce a first-draft
OfficeSpeak office from a plain-English description). Kept for the paper and the docs.
Full transcripts are in `transcripts/`.

## Why "cold"

The people who wrote the instructions and the gallery are contaminated evaluators — if
they build an office it flatters the artifacts. A **cold test** uses a fresh instance
whose entire input is exactly the production input and nothing else:
`start_instructions_v3.md` + the gallery examples (`start_gallery/`; the debate example
lives inside the instructions) + one plain-English Pat description. No design-chat
context, no hint of the expected answer. Here, each cold instance is a subagent
instructed to read only those files and act as the assistant.

## Protocol

1. **Pre-register** the expected office and the specific things the case tests, *before*
   running (so scoring isn't post-hoc).
2. **Run cold**: the subagent reads only the instructions + gallery + the one
   description, then produces Phase 1 (network) → explain-back with "Things I
   assumed —" → Phase 2. Corrections are run as a fresh cold instance given the built
   office + Pat's plain-English correction.
3. **Score** on: right coordination call (merge_synch vs fan-in vs gate vs select vs
   **none**); **state ownership** (private → stateful transform; shared across agents →
   record+gate or keeper); single-inbox rule; registered agents by name; **no
   over-engineering**; valid 4-tuples; Phase 1/2 separation; agent-vs-worker register;
   whether the explain-back surfaces the real ambiguities (esp. a missing "needs-to-see"
   connection); scope discipline (no code, no runtime placement, no jargon to Pat).
4. Every miss becomes a concrete instructions/gallery fix.

## Scorecard

| # | Case | Chiefly tests | Verdict |
|---|------|---------------|---------|
| 01 | Loan desk (stateful pipeline) | Restraint; **private state → stateful transform, NOT record+gate**; needs-to-see | **PASS** |
| 02 | Loan desk — correction (two writers, shared limit) | **Shared state → keeper/record+gate**; the inverse of 01 | **PASS** |
| 03 | Fractions tutor (adaptive, feedback) | Restraint; private mastery state; ask-and-wait loop through the outside world | **PASS** |
| 04 | Adaptive tutor (realistic; two records) | Records vs private state; **no gate on a single-writer record**; needs-to-see; the new three-part explain-back | **PASS** |
| 05 | Adaptive tutor, re-run (regression) | The two-pass port-message edit: Pass A itemizes every outbox, Pass B derives every inbox; Pat-facing explanation stays clean | **PASS** |
| 06 | Customer returns, many customers at once (new domain) | The new "many of the same kind at once" section: one team (no per-customer copies), every message tagged, a record generalized to one row per tag, restraint on tagging a second audience (manager) | **PASS** (with a gap noted in the test design itself — see case notes) |

**Running verdict: 6/6.** Most notable: the set handles **state ownership in every
form** — it refuses record+gate for a single-owner running total (01), correctly
introduces a shared keeper the moment two workers share that total (02), and refuses a
gate on a read-and-written *record* touched by a single worker (04). It reasons about
ownership (accessor count) rather than pattern-matching the examples. Case 04 also
confirms the **three-part explain-back** (meet the team / org chart / story) works on a
fresh instance the first time it's in the instructions. Case 06, in a domain unlike any
gallery example, confirms the new **"many of the same kind at once"** section transfers:
one team handles everyone, every message is tagged, a record's rows generalize to
one-per-tag, and — notably — restraint carries over to the new pattern too (it declined
to tag a second audience by "which one" until Pat implied there was more than one). It
did not, however, cleanly test whether a *private*, single-accessor, keyed-by-tag memory
stays private rather than getting promoted to a record — the domain chosen happened to
need a real shared record for an unrelated reason. That's flagged as a follow-up.

## Case summaries

**01 — Loan desk (build).** Pre-registered: `APPLICATIONS→SCORER→OFFERWRITER(stateful)→
OFFERS`, no coordinator/record/gate; the running risk total is the offer-writer's own
memory. The cold instance produced exactly this and stated the reasoning ("used and
updated by only one worker… so it is that worker's own memory — no record and no gate").
Surfaced score/pass threshold, limit definition, and proactively offered the
private-vs-shared choice back to Pat. Minor benign variance: folded pass/fail into the
scorer (fail-fast). Transcript: `transcripts/case_01_loan_desk_build.md`.

**02 — Loan desk (correction).** Correction: two offer-writers (consumer, business)
draw against one shared limit. Pre-registered: total can no longer be private; introduce
a shared keeper (trading_room pattern) or record+gate. The cold instance introduced
`RISKBOOK` (keeper), both writers ask-and-wait, fan-in of requests, single-inbox atomic
check-and-commit (no gate), split the scorer's output to route by loan type, and named
it a keeper "not the bare registered record." Textbook. Transcript:
`transcripts/case_02_loan_desk_correction.md`.

**03 — Fractions tutor (build).** Pre-registered: a stateful `TUTOR` transform + answer
source + screen sink, no coordinator/record/gate; ask-and-wait loop closes through the
external student. The cold instance produced this (adding a sensible `STOP` source),
kept mastery as the tutor's own memory, caught the needs-to-see (the tutor must remember
the question to grade), and noted the turn-taking makes ask-and-wait natural. Transcript:
`transcripts/case_03_fractions_tutor.md`.

**04 — Adaptive tutor (realistic app; build).** A richer tutor prepared for a tester:
adaptive difficulty, mastery/prerequisite advancement, spaced review, hints + worked
solution, a question bank, and cross-session progress with a parent report. Pre-registered:
records for the question bank (read-only) and the student profile (read+written, **single
accessor → no gate**), a tutor transform, no coordinator. The cold instance split the
brain into `PLANNER` + `QUIZMASTER` (acceptable variance; handled the resulting needs-to-see
by having each question carry its own answer), used `BANK` and `PROGRESS` records, and
**refused the gate on the single-writer PROGRESS record** with explicit accessor-count
reasoning. It produced the new three-part explain-back faithfully and surfaced an insightful
needs-to-see (the coach sees pass/fail, not the actual wrong answer). Transcript:
`transcripts/case_04_adaptive_tutor.md`.

**06 — Customer returns, many customers at once (new domain, off-distribution).**
Pre-registered: one CLERK/HISTORY/TREND team for every customer (no per-customer
copies), every message tagged by customer, and restraint about tagging the manager side
unless Pat implies more than one manager. The cold instance produced exactly this: a
single team, a `HISTORY` record explicitly generalized to "one entry per customer," and
it *declined* to tag the manager's screen by which manager since Pat only mentioned one
— stating plainly that several managers would each need their own filed view. It also
adapted sensibly rather than mechanically: no explicit "session start" message, because
a return is a one-shot request, not an ongoing session the way the tutor's is. One gap:
the domain happened to make HISTORY genuinely shared for an unrelated reason (CLERK
writes it, TREND reads it), so this case didn't isolate whether a truly *private*,
single-accessor, keyed-by-tag memory would wrongly get promoted to a record — that's
follow-up work. Transcript: `transcripts/case_06_customer_returns_many_customers.md`.

**Explain-back note.** The instructions' explain-back was tightened (this run onward) to a
three-part structure — **meet the team → the org chart → the story of one item** →
"Things I assumed —", re-told after each correction. This is a mental-model device
(Norman's gulfs of execution/evaluation): the same office/team metaphor Pat uses to
describe her system is used to explain it back so she can evaluate it. Case 04 confirms a
fresh instance follows it.

## Next cases (the paper wants more than three)

Run these cold, same protocol, to broaden the evidence:

- **Genuine join in a new domain** — an office where a decider truly needs *paired*
  inputs (merge_synch), e.g. matching each shipment's scan to its manifest before
  release. Tests that merge_synch is chosen (not fan-in).
- **Hidden data-dependency requiring a NEW connection** — a description where a
  computing worker silently lacks a fact it needs and the fix is an added edge (harder
  than the loan needs-to-see, closer to the accountant-holdings gap). Tests whether the
  explain-back surfaces it *and* whether a correction adds the right connection.
- **Off-distribution / deliberately odd** — something unlike any gallery example, to
  probe robustness and over-engineering under novelty.
- **A "should terminate?" office** — an office with an internal loop whose halting is
  not obvious (debate-like) in a fresh domain, to see if the loop is modeled cleanly.
- **Private, single-accessor, keyed-by-tag state, cleanly isolated** — a "many of the
  same kind at once" case, in a new domain, where the per-tag memory is touched by only
  one agent and nothing else ever reads it (the shape of the tutor's own PROGRESS).
  Tests whether the cold instance keeps it private and filed by tag rather than
  promoting it to a record+gate just because there are now many of something instead of
  one. Case 06 accidentally required a genuine shared record, so this is still open.

## Related: gallery README and the Gulf of Execution

The gallery also serves Pat directly (Norman's *gulf of execution*, "how do I say what
I want?"). `start_gallery/README.md` indexes the examples by *what kind of office they
are*, in plain language, so Pat (or a tester) can find one like the office she has in
mind and use it as a starting point to describe hers. Possible hook: the onboarding can
point a stuck Pat to that README.
