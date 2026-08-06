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
`OfficeSpeak/archive/offices/debug_demo/`) to computational workers only — an LLM
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

### Full engineering design — 2026-07-21

Grounded in the real `core.py`/`snapshot.py` code (not just the algorithm
sketch above) and written up in full at
`DisSysLab/docs/algorithms/TRACE_AND_LOGICAL_CLOCK.md`. Summary for the
paper:

- **This is a separate feature from the existing (unbuilt) "debug-mode
  replay"** described in `DisSysLab/docs/internals/replay_debug_mode_decision.md`.
  That one is an exact-reproduction tool for engineers — it has to capture
  every source of nondeterminism (fair_merge order, LLM responses, RNG/
  clock/external calls) so a run can be replayed bit-for-bit. This feature
  is a **read-only narration** of one real run that already finished — it
  never re-executes anything, so it doesn't need to solve that harder
  problem. Worth stating this distinction explicitly in the paper so a
  reviewer familiar with replay-debugging doesn't conflate the two.
- **Recording**: each agent's `send()`/`recv()` already has a natural
  interception point (the same place `_Checkpoint`/`_GiveMeCounts` OS
  messages are intercepted today). A lightweight internal wrapper carries
  each message's Lamport timestamp across the wire, invisible to worker
  code; unwrapped and logged the instant it's dequeued, before the
  existing checkpoint channel-state recording ever sees it — so the two
  features don't interact. Logged to one append-only JSONL file per agent.
  Opt-in via a `--trace` flag (off by default, zero overhead when off,
  same principle as `--snapshot-interval`).
- **Decided for v1: logical time does not need to survive a
  checkpoint/resume.** Scoping the activity log to a single uninterrupted
  run keeps it fully decoupled from the snapshot machinery that was only
  stabilized six days ago — an honest, statable v1 limitation rather than
  a risk taken on for the paper.
- **Playback**: a standalone, read-only tool — no dependency on the live
  runtime — that merges every agent's JSONL log, sorts by
  `(timestamp, agent_name)`, and narrates one action at a time in English.
  Same worked example as the checkpoint explainer (recovery_demo, the
  five-agent Monte Carlo π office) for a single consistent illustration
  running through both features.
- **Bonus for "bridges" framing, now literally true rather than aspirational:**
  the same theoretical lineage (Lamport 1978 happened-before → Chandy-Lamport
  1985 snapshots) now grounds two built features, not one plus a footnote.
- **Resolved 2026-07-21 (Mani):** logical time scoped to a single
  uninterrupted run, does not survive checkpoint/resume (confirms the v1
  recommendation above); large messages truncated at a fixed character
  cutoff; LLM prompts are not logged or narrated (already visible in
  `roles/` — the log covers input/output messages only, uniformly for
  computational and LLM workers); tracing is opt-in and stopped manually
  from the terminal (Ctrl-C or natural termination), with no automatic
  stop condition — considered and rejected as unneeded complexity; no
  trace-file retention policy needed (unlike periodic checkpoints, trace
  files don't accumulate the same way). Full decision log in
  `DisSysLab/docs/algorithms/TRACE_AND_LOGICAL_CLOCK.md`.

---

## 5. A second pillar: the framework builds frameworks (Vikram / mac_speed_suite) — added 2026-08-02

### What this is, and how it surfaced

Separately from the checkpoint/trace work above, a second demo was built this
session end-to-end: `DisSysLab/dissyslab/gallery/apps/mac_speed_suite`, a
trend-following backtesting office built for a finance tester ("Vikram," see
`OfficeSpeak/paper/transcript_sp100_trend_following.md`) who asked for several
traditional trend-following rules (Man/AQR/Mulvaney-style moving-average
crossover, the Turtle system, Donchian channels) backtested and ranked across
SP100 stocks.

While building it, a reuse pattern emerged and was made explicit before being
implemented: every strategy family shares the same backtesting and evaluation
machinery (a BACKTESTER that turns a day-by-day position-size signal into
realized P&L, an EVALUATOR that turns P&L into the six standard stats and an
inverse-volatility-weighted portfolio ranking) — the only strategy-specific
piece is a small `compute_variant_signal(bars, params) -> signal` function.
This was formalized as a 3-part contract (VARIANTS table, compute function,
shared wrapper) with a `make_signal_computer(strategy_name, variants,
compute_variant_signal)` factory, implemented in
`roles/_signal_common.py`. Adding Donchian and Turtle as new strategy
families required writing only their compute functions — BACKTESTER and
EVALUATOR needed zero changes, confirming the contract holds in practice, not
just on paper.

### The claim, and why it's different from "we built N offices"

The existing gallery (33 offices) demonstrates breadth: many different,
finished, unrelated pipelines — the "what can you build" argument. This is a
different kind of demonstration: not one more office, but an office that is
itself an extensible *framework* — a documented contract a further plain-English
conversation can safely extend with a new strategy without touching the shared
machinery. Concretely: Mani plans to hand Vikram the existing contract and ask
him, unaided, to add a new strategy via a Claude conversation of his own — if
that works, it's evidence that OfficeSpeak's plain-English building process
can be turned on *extending* an existing system, not only on building one from
scratch. No low-code/no-code tool known to us claims this — most produce one
fixed pipeline per conversation, not a reusable extension point.

### Honest structural note: this is a second, parallel pillar, not a third instance of the Lamport lineage

Sections 2–4 above share one theoretical throughline: Lamport's 1978
happened-before relation and the 1985 Chandy-Lamport snapshot algorithm,
translated into English by the checkpoint explainer and the activity-log/trace
feature. The Vikram/mac_speed_suite pillar rests on a different kind of
formalism — a software-architecture discipline (separation of concerns, a
typed extension contract), not a named distributed-systems result. It
shouldn't be forced into the same lineage. It reads better as a second,
parallel pillar under the same higher-level umbrella from Section 1 ("a
formal structure translated into plain English, in both directions"): pillar
one bridges HCI to distributed-systems *theory* (checkpoints, causal
ordering); pillar two bridges HCI to software-architecture *practice* (a
non-programmer's conversation safely extending a running system).

### What's still needed before this pillar is submission-ready

- **A second strategy family actually built**, not just designed — done as of
  this session: Donchian channel breakout and a simplified Turtle system
  (ATR-based breakout entry/exit with pyramiding) now exist alongside MAC, so
  the "extend to a new strategy" claim is demonstrated on real code, not only
  argued for.
- **External validation.** Every example so far — recovery_demo,
  mac_speed_suite, the gallery — was built with Mani or Claude driving.
  Plan (Mani, 2026-08-02): ask Vikram to add a new strategy himself, via his
  own Claude conversation grounded in the existing contract, unaided. If it
  works, this is the evaluation evidence the pillar currently lacks — a real
  outside domain expert extending a running distributed system through plain
  English, not a fourth internally-built case study.
- **Real (non-synthetic) data.** The office now runs on 5 real SP100 tickers
  (AMD, NFLX, NVDA, PLTR, TSLA; local CSV files, `DisSysLab/sp100_data`) in
  addition to synthetic data — Stooq's own historical endpoint is still
  returning 404s and remains undiagnosed (unrelated open item).
- **External validation -- now in motion, 2026-08-04.** Packaged the
  contract into a shareable Cowork skill, `backtest-strategy-builder`
  (`SKILL.md` + a bundled no-lookahead checker script, tested internally
  first via two dry-run cases -- a momentum strategy and an RSI
  mean-reversion strategy -- comparing skill-guided vs. unaided attempts
  before sending it to anyone). Being sent to Vikram and a second fintech
  contact, each independently, with instructions limited to setup only
  (install the skill, connect the public DisSysLab repo) -- deliberately
  not walked through how to add a strategy, since that's the actual thing
  being tested. Their transcripts/diffs, if shared, would be the first
  real instance of an outside domain expert extending this system
  unaided, rather than a fifth internally-built case study.
- **All three external testers confirmed asked, as of 2026-08-05
  (Mani).** Vikram and Sebu for `backtest-strategy-builder`; Sachin
  (a parent who separately wanted a tutor for his daughter -- see
  `OfficeSpeak/archive/offices/phase2_demo/README.md`) for the new
  `tutor-subject-builder` skill below. None of the three has returned
  feedback yet as of this writing -- their transcripts/diffs, when they
  land, are the actual evidence this pillar has been missing.
- **A real bug the internal dry run caught, worth noting for the paper's
  own credibility.** Both dry-run conditions (skill-guided and unaided)
  independently hit the same genuine, pre-existing bug in the shipped
  office: the CLI's generated runner changes directory before executing,
  which broke a relative data path and silently zeroed out every
  strategy's results, not just the new one. Fixed directly in the repo and
  re-verified via the actual CLI (not just the Python API used in earlier
  testing). One honest, mildly self-critical finding from the same dry
  run: the two unaided attempts fixed this bug for real, while the two
  skill-guided attempts only worked around it locally -- the skill's own
  verification step had offered two "equally valid" ways to check the
  work, and that framing let it take the easier path instead of fixing
  the root cause. Tightened before packaging. Worth a sentence in the
  paper either way: the dry-run process caught a real defect neither the
  original build-and-run pass nor its own earlier verification had, which
  is itself evidence for why external, adversarial-ish testing (even
  internal dry runs) matters before claiming a contract "just works."
- **Persistence and checkpointing, if this pillar is to touch pillar one.**
  Vikram's actual next request: run these strategies as a continuous
  distributed system, reading stock prices daily, not a one-shot batch
  backtest. That reframes mac_speed_suite from a batch job into a long-running
  office — which is exactly where pillar one's checkpoint/snapshot and
  activity-log machinery becomes directly relevant, not just analogous. Not
  yet designed or built as of this note; the signal computers currently
  recompute from a full bulk history each run rather than maintaining
  incremental state (a running EWMA, a rolling breakout window, Turtle's open
  position/stop state) across daily updates — that statefulness, plus
  checkpointing it, is the next design problem, and it would make pillar one
  and pillar two the same running system rather than two separate examples.

---

## 6. Pillar two, second domain: adaptive_tutor (education) -- added 2026-08-05

The generality gap flagged above (pillar two rested on one full example --
mac_speed_suite -- plus one partial analogy, `situation_room_pro`'s single
role-file swap) is now partly closed. `dissyslab/gallery/apps/adaptive_tutor/`
ports an older tutoring demo (`OfficeSpeak/archive/offices/phase2_demo/tutor_multi.py`,
built on a pre-v1.6 API) onto the current office.md/roles framework, and --
unlike that version -- formalizes what varies between practice subjects into
the same kind of documented, typed contract mac_speed_suite has: a
`generate_problem(rng, params) -> problem` function per subject, wrapped by a
shared `make_subject_bank` factory, feeding one shared PLANNER/CHECKER/STUDENT.
Two seed subjects (fractions, multiplication_facts) plus a third
(telling_time) added unaided by a fresh Claude subagent given only the
packaged skill (`tutor-subject-builder`) and the repo -- no shared file
touched, verified independently afterward, not just by trusting the
subagent's own report.

**Why this is a genuinely different domain, not a relabeled finance example.**
Backtesting's automatic correctness check (no-lookahead) has a clean
mechanical shape because its invariant is about *time*. Tutoring problems
aren't sequential that way, so the analogous check had to be *rediscovered*,
not reused: `check_problem_ground_truth.py` verifies self-consistency
(a generator's own `correct_answer` is always in its own `accepted_forms`)
and determinism (same seed -> byte-identical problems), catching a different
class of bug (answer/accepted-forms drift, a forgotten `rng` argument) than
no-lookahead catches. Worth stating explicitly in the paper: the *contract
pattern* (VARIANTS + a small typed compute function + a shared wrapper)
generalizes across domains; *what counts as an automatic correctness check*
does not come for free and has to be designed fresh per domain. That is a
more honest, more interesting claim than "one universal checker," and is the
kind of nuance a reviewer is more likely to trust.

**A real bug this build caught, same spirit as the chdir bug in Section 5.**
`tutor_planner.py` initially returned `(status, message)` tuples instead of
the framework's `(message, status)` convention (`dissyslab/blocks/role.py`'s
`Role.run()`, line ~121) -- every session hung silently, no crash, no error
printed, until killed by a timeout. Found only by actually running the
pipeline end to end (via a monkeypatched LLM backend, since this sandbox has
no live Anthropic API access) rather than trusting that the code "looked
right." Fixed; the fresh-subagent test afterward confirmed the fix held and
found one more small, real thing: `_subject_common.py` eagerly imports the
Anthropic SDK at module load time even for pure-logic testing that never
calls it -- a minor design smell, not a blocker, worth a fix but not a
crisis.

**Sachin** (a parent who wanted a tutor for his daughter -- the same person
`phase2_demo/README.md` was originally written for) is the third external
tester, alongside Vikram and Sebu, given the packaged `tutor-subject-builder`
skill + a cover note mirroring the one sent for backtesting. As with the
other two, no feedback yet as of this writing.

---

## 7. CHI 2027 outline + what would convince reviewers -- discussion 2026-08-05

Draft v3 (`OfficeSpeak/paper/draft_v3.md`, dated 2026-07-22) predates all of
Sections 5-6 above -- its five contributions cover only pillar one
(the office interaction, trusted coordination primitives, English
debugging/checkpoint explainers, separation of concerns, preliminary
evidence). Pillar two (framework builds frameworks) is not in it at all yet.
Integrating rather than replacing is the right move -- v3's related-work and
evaluation sections are already well-built and honest; they need extending,
not redoing.

**Concrete edits to draft_v3.md:**
- Add a sixth contribution for pillar two, likely folded near contribution 4
  (separation of concerns) or as its own numbered item: a documented,
  domain-specific extension contract (VARIANTS + typed compute function +
  shared wrapper) that a further plain-English conversation -- Claude's own,
  or an outside domain expert's -- can safely extend without touching shared
  machinery, demonstrated in two unrelated domains (finance, education) with
  automatic, mechanically-checked correctness per domain and (pending) real
  external testers extending each one unaided.
- Related work needs a new subsection specifically for pillar two -- v3's
  current section 7 covers multi-agent frameworks and durable execution
  (AutoGen, LangGraph, CrewAI, Temporal) for pillar one, but says nothing
  about low-code/no-code extension mechanisms. Must engage directly with:
  LangFlow/AutoGen Studio/Zapier/n8n/Sim/Open Agent Platform (all extend via
  a visual canvas, not natural language, and none pair a typed contract with
  an automatic domain-correctness check); Claude Skills' own "verification
  loops" framing (genuinely close -- packaged natural-language instructions
  for safely extending existing code -- the real distinction is that
  OfficeSpeak's target system was *also* built through the same
  conversational process, and the correctness check is a designed part of
  the contract, not a generic "run tests"); SUGILITE/PUMICE (Li et al.,
  end-user natural-language task automation) -- adjacent tradition, not
  about extending a previously-built system via a reuse contract. A plain
  web search (2026-08-05) found nothing combining all of: natural-language
  build, natural-language extend, typed contract, automatic per-domain
  check -- but this was one afternoon's search, not a real ACM DL/Scholar
  pass; state the novelty claim at that precision, not more broadly.
- Evaluation section gains: the internal skill-eval benchmark for
  `backtest-strategy-builder` (2 evals x with/without skill, the honest
  mixed finding that with-skill runs *worked around* the chdir bug rather
  than fixing it -- a negative-ish finding worth reporting plainly, not
  hiding); the fresh-subagent `telling_time` test for
  `tutor-subject-builder`; and, in the "proposed, not yet run" bucket
  alongside the hedge-fund-manager/environmental-sensor-network conversations
  already listed there, the three pending tester results (Vikram, Sebu,
  Sachin). Note for Mani: Vikram's *original* strategy request (the thing
  that became mac_speed_suite) may already double as evidence for
  contribution 1 (a real domain expert describing an office he wanted) --
  worth checking whether that transcript still exists and fits v3's existing
  worked-example framing, before writing a new example from scratch.
- Limitations section should add the point made above about
  ground-truth/no-lookahead-style checks not being domain-free -- each new
  domain needs its own correctness invariant designed by hand; the pattern
  generalizes, the specific check does not.

**What would most convince a CHI reviewer, in rough priority order:**
1. Real tester transcripts landing before the Sept 10 deadline -- even
   informal, even critical. A reviewer's first objection to a "framework
   builds frameworks" claim will be "did anyone who didn't build this try
   it," and right now the honest answer is still no.
2. A precise, narrow novelty claim that visibly engages the closest prior
   work (Claude Skills, SUGILITE/PUMICE, LangFlow/AutoGen/Zapier) rather than
   a sweeping claim that ignores it -- reviewers who know any of these will
   flag the omission immediately.
3. Reporting negative/mixed findings plainly (the with-skill workaround
   finding; the silent-hang bug; the eager-import smell) -- v3 already does
   this well for pillar one (a real termination-detection bug found and
   fixed, stated outright); pillar two should match that standard rather
   than reading as a success story with no friction.
4. Genuine generality across unrelated domains, honestly scoped -- two
   full-fit examples (finance, education) is real progress over one; naming
   the boundary (salton_sea_dashboard, the environmental-monitoring app, does
   *not* yet fit this same contract shape -- it has two sources, not a
   family of interchangeable variants) is a better, more credible statement
   than implying the pattern fits everything.
5. Matching CHI 2027's own "bridges" theme directly and without forcing it --
   the paper already has this almost for free: pillar one bridges HCI to
   distributed-systems theory, pillar two bridges HCI to software-
   architecture practice, both under one higher-level claim (Section 1: a
   formal structure translated into English, in both directions).
6. A public, runnable artifact (the DisSysLab repo itself) a reviewer or PC
   member could actually clone and exercise -- already true today, worth
   stating plainly in the paper rather than assuming reviewers will find it.

---

## 8. Naming pillar two: "higher-order office" -- decided 2026-08-05

Settled name for what Section 5-7 above call "the framework builds
frameworks" / "framework -> framework": **higher-order office** (or
higher-order framework, for the more general noun). Rationale, for
whichever section first introduces it: it's a direct, precise analogy to
a higher-order function (one that takes or returns functions) -- an
office, once built, exposes a formal contract that lets a further
natural-language conversation produce a new instance of one of its own
components, mechanically verified before it's wired in. Stays inside the
paper's existing "office" vocabulary rather than introducing an unrelated
noun, and gives pillar two the same move pillar one already has with
Lamport/Chandy-Lamport: a real bridge from a named CS concept to an HCI
claim, matching CHI 2027's "bridges" theme the same way. Considered and
rejected: "self-extending framework" (plainer, no jargon, but less
distinctive) and "bootstrapped office" (nice echo of a self-compiling
compiler, but "bootstrap" is overloaded in ML/stats and risks confusing a
skimming reviewer).

**Also strengthened since Section 7 was written, worth folding into the
eventual draft_v3.md edit:** `backtest-strategy-builder`'s per-strategy
checker grew from one check (no-lookahead) to a small tiered menu --
determinism, finite-values, a declared directional/sizing range actually
enforced (previously just eyeballed), a declared warm-up period, and two
alternative ways to catch a "confidently wrong" formula: a hand-computed
golden example (most rigorous) or a zero-effort synthetic monotonic-
trend sanity check (weaker, automatic). The tester now picks which of
the latter two they want rather than the skill silently forcing the more
expensive one on everyone -- itself a small, honest data point for
contribution 6: the *menu* of what's mechanically checkable generalizes
per domain (tiered by cost/rigor), even though the specific checks don't.
Separately, `_backtester_core.py`/`evaluator.py` (shared machinery every
strategy relies on unchanged) gained their own permanent unit tests
(`tests/unit/test_mac_speed_suite_backtester_core.py`,
`test_mac_speed_suite_evaluator.py`) -- previously untested -- locking in
the P&L realization-lag invariant and the documented stat formulas so a
future edit to shared code can't silently break every strategy's numbers
without a test catching it.

---

## 9. Go/no-go decision point for CHI 2027 -- set 2026-08-06

Mani's decision, stated plainly: wait for real tester feedback -- Sebu and
Vikram on `backtest-strategy-builder`, Sachin on `tutor-subject-builder`,
and possibly Professor Sinclair on the Salton Sea dashboard (pending the
Aeroqual Cloud API integration). **If feedback lands by August 25**, submit
to CHI 2027 (Sept 10 deadline -- 16 days to write up whatever the feedback
says, honestly, per Section 7's priority list). **If it doesn't**, the plan
is not to force a submission on a still-unvalidated pillar-two claim, but
to look for another way to get people to actually try the framework and
give feedback -- the paper was never the actual goal, real usage and
feedback is, and the paper is only worth writing once that evidence exists.
Worth remembering if this note is revisited later: this is the honest
reason a submission may not happen this cycle, not a loss of momentum.

---

## 10. Applied to draft_v3.md: the three-condition framework value-add argument -- 2026-08-06

Added directly to Section 1 (Introduction), between the closing sentence
of the current framing paragraph and "This paper makes the following
contributions" -- a general argument for why build a reusable framework
at all rather than asking an LLM to generate each application from
scratch. Three necessary conditions: (1) reuse count (many people, or
many variations from one person) has to be large enough to amortize the
framework's own construction cost; (2) what's encapsulated has to be
expensive/risky to regenerate correctly on demand, not just voluminous;
(3) a new use has to be checkable against the framework's own contract
by something other than trusting whichever model session built it, or
conditions 1-2 can hold and the value still partially evaporates.
Condition 3 is flagged as the sharpest and most concretely evidenced by
this project specifically (no-lookahead / ground-truth checking).

Deliberately scoped as a general framing paragraph, not the paper's
central claim -- discussed and agreed with Mani that this inequality on
its own is a software-economics argument, not a human-centered one, and
would be a better fit as the paper's *motivation* than as its
contribution list. The actual contributions (the office interaction,
trusted primitives, English debugging, separation of concerns, and the
still-unwritten higher-order-office contribution 6) remain the
human-centered, evidenced claims; this paragraph explains why they're
worth having.
