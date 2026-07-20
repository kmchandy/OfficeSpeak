# Project handoff — resume OfficeSpeak in a new Cowork session

Written 2026-07-16 (updated same day) to continue this work on a different Claude
account. If you are a fresh Claude with no memory of the prior conversation: read
this file, then the linked docs, and you can pick up where we left off. If you are
Mani: connect the `DisSysLab` and `OfficeSpeak` folders in the new account's
Cowork and point Claude at this file.

**Both repos are now PUBLIC on GitHub** (`kmchandy/DisSysLab`,
`kmchandy/OfficeSpeak`). OfficeSpeak has an MIT `LICENSE`. Make sure local commits
are pushed (`git push`) so the public repos match what's on disk.

## What the project is

OfficeSpeak lets a non-programmer ("Pat") build, run, and maintain a distributed
system as an **office** of message-passing **workers**, by describing it in plain
English. An LLM assembles the office from trusted, predefined coordination
primitives and explains it back in English; Pat corrects it by conversation.
**DisSysLab** (`~/Documents/DisSysLab`) is the runtime; **OfficeSpeak**
(`~/Documents/OfficeSpeak`) is the assistant/notation layer, examples, and paper.

Both repos are on GitHub under `kmchandy/` and are **pushed and current** as of
this handoff.

## Core model (stable decisions)

- An **office** = agents ("workers") + connections. A connection is a 4-tuple
  `(sender, outbox, receiver, inbox)`. Fan-in (many outboxes → one inbox) and
  fan-out (one outbox → many inboxes) are allowed.
- Worker **kinds**: source (no inbox), sink (no outbox), transform (one inbox),
  record (a shared file with a keeper — single accessor needs no gate; shared by
  many needs the `gate` primitive), coordinator (2+ inboxes; predefined
  primitives only: `merge_synch`, `gate`, `select`).
- **Uniform worker contract:** every worker is a pure function
  `step(message, state) -> [(outbox, message), ...]`. It never calls send/recv,
  never blocks. Python workers and **LLM workers meet the identical contract**, so
  they are swappable. LLM as the base case; plain code is for plumbing and for
  deliberately exact/auditable rules.
- **Pure functions as data (2026-07-19).** A worker whose behavior is a *stateless*
  per-message judgment call (an LLM prompt applied to one item, no memory of any
  other item) doesn't need to be its own structurally distinct agent. It can be
  pulled out as data — e.g. one entry in a list of prompts — executed by one
  generic, already-trusted runner (looping over the list, or fanning out one call
  per entry; both are just execution strategies for the same computation). Adding
  a new capability of this kind becomes "add a prompt to the list," a data change
  through already-reviewed code, not new code entering a running system. This does
  **not** extend to stateful workers — the deduplicator, a registry/subscriber
  handler, `merge_synch`, `gate`, `select` — because what's trusted about those is
  the correctness of a *protocol* that persists across messages, not the content
  of one call; that can't be flattened into a list a generic runner iterates over.
  Also doesn't remove the need to review a prompt's *content* — it shrinks the
  review surface (one prompt) rather than eliminating review.

## What is done (phase 2 — build & run)

Runtime (DisSysLab):
- `dissyslab/blocks/coordinator.py` + `merge_synch`, `gate`, `select` subclasses.
- **#47 FIXED — coordinator-aware termination detection.** os_agent now uses a
  passivity gate (every non-source agent answered the current poll round ⇒ blocked
  in recv) + reachable-channels-empty (a coordinator only needs the channel into
  its `waiting_on` inbox empty). See
  `docs/internals/URGENT_termination_detection_coordinator_bug.md` (marked
  RESOLVED) and `tests/integration/test_coordinator_termination.py`. Full suite:
  446 passed.
- Backend registry already supports Claude/Qwen/GPT/Gemini/SLM via
  `dissyslab/backends` (`get_backend`, `Backend.complete(system=, user=)`).

OfficeSpeak `offices/phase2_demo/`:
- `worker.py` — the `Worker` block hosting a `step(msg, state)` body.
- `llm_worker.py` — `make_llm_step(...)`: any backend as a worker under the
  uniform contract (robust JSON/fence parsing + outbox validation). Verified live.
- `harness.py` — `build_office(spec)`: an office description → a runnable
  `Network` (infers ports, maps kinds to blocks, validates with plain-English
  errors). `harness_demo.py`, `test_harness.py`, `test_llm_worker.py` pass.
- Worked offices, all run & terminate: `tutor.py` (Python grader),
  **`tutor_llm.py` (LLM grader — the base case; accepts "one"/"two quarters",
  gives real hints, 3/4)**, **`tutor_interactive.py` (a LIVE terminal tutor a
  real student types answers into — same office as tutor_llm, but the canned
  answer source + print-only screen are replaced by one interactive TERMINAL
  worker; all display routed through PLANNER for deterministic ordering; verified
  live)**, **`tutor_multi.py` (several students through the SAME office at
  once — see "Multi-student design" below)**, `room_monitor.py`,
  `triage_swap.py`, `triage_llm.py`.
- Note on interaction: a Cowork run is non-interactive (no live keyboard), so the
  in-chat demo uses `tutor_llm.py` (fixed answers); a real student types into
  `tutor_interactive.py` in a normal terminal.

Phase 1 (start module) and cold tests live under
`offices/claude_project/` (`start_instructions_v3.md`, `start_gallery/`,
`cold_tests/` 6/6 — see "Multi-student design" below for case 06).

## Onboarding doc = the public README

The tutor walkthrough is now the repo **`README.md`** (it replaced the stale
NetworkOfThought README; the old `paper/sachin.md` was renamed into it). It is
generic (no personal references), diagram at the top, Steps 0–4: set up →
describe in English → run in Cowork (demo) → change in English → run
`tutor_interactive.py` live in a terminal. The README links to
`offices/phase2_demo/README.md` for the code details (worker contract, harness,
LLM worker).

## Tester

First tester is **Sachin Adlakha** (PhD, avid Claude user, has an API key,
interested in a tutor for his daughter). His onboarding is the repo `README.md`
(above).

## Multi-student design — the big addition this session (2026-07-16)

A long brainstorm (not skipped to code) worked out how to describe an office that
handles **many of the same kind of thing at once** (many students, not one) — this
generalizes past the tutor to any "one case, now many at once" problem.

**The design, settled:**

- Keep exactly the same agents. Do **not** replicate the office per student and do
  **not** spawn new workers when someone new arrives.
- **Every message carries a tag** — whichever thing repeats (student_id here).
- **Any worker's own memory becomes one slot per tag** instead of one shared slot —
  a mechanical extension of what it already remembered (`state["n"]` becomes
  `state["n"][student_id]`, etc.). This is the whole idea; nothing else changes.
  Records generalize the same way (one row per tag).
- A new arrival is a **message** (a "start" tagged with a fresh id from a listener/
  roster source), never a new agent.
- Handling one tagged item can start a **separate message trail under a different
  tag** toward a different audience (e.g. a parent) — same rule applies to that
  trail, filed by *its own* tag (parent_id, not student_id).
- Deliberately punted for now (Mani's call): race conditions at a shared repository,
  and performance/efficiency splits (e.g. one PLANNER per grade level) — "any office
  that works" first, refine later.
- Why this works safely even though many students are "concurrent": the runtime is
  message-at-a-time per worker already (that's the actor-model foundation
  room_monitor etc. already rely on) — there's no real race to design around, only
  the bookkeeping of keying state by tag.

**What got built from this:**

1. `offices/phase2_demo/tutor_multi.py` — a reference implementation: the SAME
   PLANNER/CHECKER/BANK/PROGRESS/PARENT_REPORT as `tutor_interactive.py`, generalized
   by keying every worker's state on `student_id`. One real `TERMINAL` (Mani's call,
   for the demo) plus a `SIM_ANSWERER` worker standing in for other students'
   own devices, so `python tutor_multi.py` proves several sessions run through the
   same shared workers with no state bleed. **Verified working** (see below).
2. `offices/claude_project/start_instructions_v3.md` — added a new section, "Many
   of the same kind at once," teaching this exact convention (tag every message;
   memory becomes one-per-tag; new arrival = message not agent; a trail to a new
   audience gets its own tag), with its own worked example (one tutor, many
   students) in the same style as the existing debate worked example. Added a
   matching bullet to "Rules of thumb."
3. `offices/claude_project/cold_tests/` — **case 06**, a fresh subagent given only
   the instructions + gallery (no memory of this conversation, no access to
   `tutor_multi.py`), tested on a **different domain** (customer returns, not
   tutoring) to check the new section transfers rather than just being recognized
   from its own worked example. **Verdict: PASS** — it kept one team for every
   customer, tagged every message, generalized a record to one row per tag, and
   (notably) showed restraint by *not* tagging the manager side since Pat only
   mentioned one manager. One real gap, in the test design rather than the
   instructions: this domain accidentally needed a genuinely shared record anyway
   (two different agents touch it), so it didn't isolate whether a truly *private*,
   single-accessor, keyed-by-tag memory would wrongly get promoted to a record. See
   `cold_tests/README.md`'s scorecard and "Next cases" for the follow-up case still
   needed (mirrors PROGRESS's shape — touched by only one worker — in a new domain).

**Verification done:** `tutor_multi.py` was run end-to-end in the sandbox with a
fake grading backend (no network/API key available there) and blank/piped input for
the "live" student; `live`/`amy`/`ben` each got independently correct scores and
per-student parent reports, confirming no cross-student state bleed. It has **not**
been run yet with the real Claude backend in a real terminal — worth Mani doing once
back at the keyboard (`cd DisSysLab && pip install -e .` once, then
`cd ../OfficeSpeak/offices/phase2_demo && python tutor_multi.py`).

## Immediate next steps (where we're headed)

1. **Run `tutor_multi.py` for real** (real terminal, real ANTHROPIC_API_KEY) — the
   sandbox verification used a fake backend since there's no network/API access
   there.
2. **The follow-up cold test** noted above: a new-domain case isolating a *private*,
   single-accessor, keyed-by-tag memory, to confirm the new instructions section
   doesn't over-promote it to a record.
3. **The parent-alert-after-N-misses feature** (originally its own task, now a
   small addition on top of the multi-student design rather than a separate one):
   PARENT_REPORT currently only fires at session end; add the exact, auditable rule
   "alert after N wrong answers," per student, using the same id-keyed PLANNER/
   PROGRESS state.
4. **Pat role-play:** Mani plays a brand-new Pat using the `README.md` walkthrough.
5. **Later:** other testers (a journalist with a Claude key; a hedge-fund
   non-programmer); debug-mode + checkpoint replay explained in English (phase 3,
   not needed for pilot); paper (`paper/draft_v2.md`) — the multi-student design is
   good material for it.

## README updated for the multi-student step

`README.md` (the public onboarding doc) now has **Step 5 — many students, one
office**, right after Step 4: a new Pat description ("now let it handle many
students at once... let a parent check in"), an org-chart diagram, explain-back,
and `python tutor_multi.py` run instructions with sample output. The old "Later
examples" placeholder for this was removed; the still-unbuilt "alert a human tutor
if a student gives random answers or stops answering" idea was kept there as
future work (not yet implemented — only the many-students generalization and
per-student parent reports are done).

## Repo cleanup — done (2026-07-17)

`OfficeSpeak/` was scattered across several earlier-phase locations (an
"Adaptive DSL Paper 1" planning cycle from late June, and an older
`officespeak/`-package pipeline before that). Cleaned up in two passes, using
git history as the safety net (default: delete rather than archive, since
nothing is really lost):

- **Kept, moved into one place:** `offices/{investment_club,weather,
  trading_desk,anomaly_monitor,support_desk}` → `examples/` (their old
  `spec.md`/`build_package.md`/`reference/`/`runs/` drafts, alongside the
  existing `examples/debate.*`, `examples/situation_room.*`,
  `examples/sanity_checks/`). `officespeak/smoke_test_outputs/` (two nice
  example prompts) → `examples/example_prompts/`. Everything example-like now
  lives under one `examples/` folder.
- **`situation_room` resolved:** it had four scattered copies. Kept
  `examples/situation_room.md` + `how_to_situation_room.md` (the full Pat
  spec + graph decomposition + rationale — also the one Mani wants to reuse
  for the multi-client idea, below). Deleted the other three: `gallery_runs/
  situation_room/` and `archive/asyncio_experiment/.../situation_room/` were
  both mostly-unfilled experiment-note templates; the asyncio version was the
  approach BRAINSTORM.md itself says was dropped.
- **Deleted entirely:** `BRAINSTORM.md`, `DECISIONS.md`, `PLAN.md`,
  `MIGRATION.md` (a superseded planning trail, fully replaced by this file);
  `archive/`, `catalog/`, `experiments/`, `gallery_runs/` (old pipeline
  runs/logs — `cold_tests/` is the current equivalent); the old `officespeak/`
  Python package; `network_of_thought.egg-info/` (build artifact);
  `pyproject.toml` (broken — referenced a nonexistent `claudette` package;
  OfficeSpeak's own code isn't pip-installed in the current workflow, only
  DisSysLab is); empty top-level `*.jsonl` files; `outputs/`; `prompts/`; 16
  loose early-phase planning docs under `offices/` (kept the 4 relating to
  debug/checkpoint-replay, plus `agents_demo/` and `debug_demo/`, both still
  useful examples).
- **One mistake made and fixed:** a `rm -rf officespeak` swept away
  `smoke_test_outputs/` before it was supposed to be — caught it, restored
  from git history, then moved it properly once confirmed.
- Fixed a real broken reference this surfaced: `TESTER_MANUAL.md`'s Track B
  pointed at `offices/weather/reference/build`, now `examples/weather/
  reference/build`. Note still open, not fixed (low stakes, Mani's own
  wording, didn't want to edit paper prose unprompted):
  `paper/empirical_plan.md` still references the now-deleted `DECISIONS.md`.
- `offices/` root is now just `phase2_demo/`, `claude_project/`,
  `agents_demo/`, `debug_demo/`, and the 4 kept planning docs — everything in
  it is current or explicitly wanted.

## Then: get set up for more testers

One idea Mani is considering: run `situation_room` for multiple clients
(multiple Pat-testers at once) — set up many news/social-media sources per
Pat, and deliver results by email, text, or social post. This is a new,
bigger design conversation for next session (not started): it touches real
external feeds, multiple simultaneous testers, and real contact info/delivery
channels, so it deserves its own careful design pass (and note: any real
tester contact info that enters the picture should be handled per the usual
PII-care norms — not stored or surfaced carelessly). `situation_room`'s spec
(now cleanly at `examples/situation_room.md`) is the natural starting point.

## situation_room_requests — dynamic subscriptions (2026-07-18)

New DisSysLab gallery app, built directly in `office.md` (not via an English
description — no OfficeSpeak instructions cover dynamic subscription
membership yet): `DisSysLab/dissyslab/gallery/apps/situation_room_requests/`.
Same fixed torrent + four parallel extractors + synchronizer as
`situation_room`, plus one new agent, `Registry` (custom Python role,
`roles/subscription_registry.py`), that lets stakeholders start/stop analysis
requests dynamically (each watching one field, e.g. `severity`) and serves
them from features computed **once per item** regardless of how many requests
are watching — no recomputation per subscriber. Confirmed design choices:
push (Registry notifies active subscribers itself, nothing polls it) and no
backfill (a new request only sees records from the moment it starts, not
history). Two demo destinations, both off-the-shelf sinks, no new sink code:
one console (`intelligence_display`), one email (`gmail_sink`). Verified with
`dsl build` in the sandbox (no API key needed — build never calls the LLM
backends; had to stub the `anthropic` package to get past the import, same
trick as `tutor_multi.py`'s `FakeBackend`) — compiles clean, `Registry`'s
three outports wire to archive/console/email as intended. Not yet run for
real (needs Anthropic/OpenRouter + Gmail credentials). Intended to eventually
replace `situation_room` in the DSL gallery, once it's been run for real and,
ideally, once an English-description-first version exists too.

Also decided in this session: the `office.md → run.py` compiler should stay a
deterministic, mechanical Python compiler, not something Claude regenerates
per run — that determinism is exactly what lets the termination/snapshot
guarantees hold. Where Claude's judgment belongs is one layer up: Pat's
English → `office.md` + role prompts (the existing OfficeSpeak premise, and
the still-missing Phase 3 step for this pattern specifically).

**Noted for the paper, not yet done:** `Registry`'s per-item fan-out loop
(`for request_id, sub in subscriptions.items(): ...`) is a candidate for a
later optimization — spawning one thread per subscription instead of looping
sequentially. Sequential is correct and is what we built; the threaded
version is worth a mention in the paper as a performance note, not a
correctness one.

## start_gallery / start_instructions for DSL (2026-07-19)

Mani is focusing on DSL for the next day or so. Decided this session, all in
DisSysLab (no OfficeSpeak changes): apply OfficeSpeak's own build-by-
conversation discipline (chat, explain back, iterate until Pat agrees) to
DSL's `dsl new`/`dsl edit`, which already have a multi-turn chat loop
(`dissyslab/cli_chat.py`) but currently just write files and exit — no
required explain-back, no forced iterate-until-correct loop, and the context
file the loader looks for (`CLAUDE_CONTEXT_OFFICE.md`) doesn't exist, so it's
silently falling back to two generic sentences.

Naming, settled: use `start_instructions` (not `CLAUDE_CONTEXT_OFFICE`) and
`start_gallery/` in DSL too — exact same names OfficeSpeak already uses for
the same two roles (rules file; folder of worked examples), different repo.
OfficeSpeak's own `start_instructions_v3.md` is untouched — too disruptive to
rename something testers already reference by name.

Examples folder decision: a *curated* `start_gallery/` folder, not references
into the real `dissyslab/gallery/` apps directly — real gallery apps mix
several patterns together and carry setup/cost prose that dilutes what a
generation model needs; a curated folder can isolate one pattern per example
and order simplest-first. Tradeoff acknowledged: curated copies can drift
from the real implementation, so every example names its source app.

Started (not finished): `DisSysLab/dissyslab/start_gallery/` now has a
`README.md` (purpose, duplication tradeoff, and — important — **two example
types**, not one: Type A is a pattern-reference example (final artifact
only), Type B shows an ambiguous/incomplete structural ask resolved through a
clarifying exchange into a correct office). Two example files exist:
`01_single_agent.md` (Type A, distilled from `my_first_office`) and
`02_dynamic_subscriptions_ambiguity.md` (Type B, distilled from the actual
conversation that built `situation_room_requests` this session — the
compute-once-vs-recompute-per-subscriber correction, the push/no-backfill
clarifications, and a coda distinguishing "resolved at the description
stage" from "correct once actually run," since a silently-unwired outport
and a missing `poll_interval` both surfaced only by running it, not by
conversation).

**Important correction, caught by Mani right after `02` was written:** its
first draft implied this was a Pat-and-cold-Claude conversation. It isn't —
it's a real transcript, but between Mani (the system's own designer, not a
non-technical Pat) and a Claude holding this entire session's accumulated
context (not one grounded only on `start_instructions.md` + `start_gallery`,
which don't fully exist yet). Both `01`'s Pat quote (invented for
illustration) and `02` (an expert session) fall short of the real target: an
actual cold test, fresh Claude + a genuinely non-technical Pat, the same
discipline OfficeSpeak already uses. `02` is now relabeled throughout ("the
architect's description/correction," not "Pat's") with a prominent caveat at
the top, and `README.md` has a new section naming this gap explicitly as the
top priority once `start_instructions.md` exists — ahead of writing more
Type A pattern examples. Don't reuse `02`'s register or pacing as evidence of
what a real Pat conversation looks like; its structural content (compute
once, push, no backfill, no new coordinator) is still sound and worth
keeping.

Key conceptual distinction surfaced this session, worth keeping straight
going forward: in DSL, Pat's own description is already loosely
office-shaped (she names sources/sinks/agents herself, possibly incompletely
or ambiguously) — DSL's job is disambiguation of Pat's own sketch. In
OfficeSpeak, Pat describes a goal, never that vocabulary — OfficeSpeak's job
is inventing the structure from scratch. Same explain-back-and-correct
discipline, different starting point. `start_instructions.md` for DSL will
need to teach *disambiguation of a structural sketch*, which is a different
skill than what `start_instructions_v3.md` teaches (inventing structure from
a goal) — not just a retitled copy of it.

Not yet done (tracked as tasks #25–27 in this session's tracker): write
`start_instructions.md` itself; keep growing `start_gallery/` (one Type-A
example per remaining coordinator — `merge_synch`, `gate`, `select`, a shared
`record`, per-role backend override — plus more Type-B examples as real ones
surface); update `cli_chat.py` to actually load `start_instructions.md` +
everything in `start_gallery/`, and to make explain-back/iterate the loop's
behavior instead of "write files and exit."

Also noted, not yet done: `situation_room_pro`'s only real insight is a
backend-cost lever (per-role override — pay for the one generative role,
run closed-list classification free/local), which doesn't have an obvious
analogue in `situation_room_requests` since that office has no LLM writer
step to begin with.

## Cold test case 07 — news subscriptions, run and PASSed (2026-07-19)

After the Al/Pat discussion and the "pure functions as data" rule (above), the
open question was whether Pat-speak alone — no DSL-style structural
description — would actually converge on the right office for a pattern class
none of `start_gallery`'s four examples teach: a dynamic, unbounded set of
external subscribers each wanting a different slice of the same computed
fact, computed once and shared, not recomputed per subscriber. Rather than
keep reasoning about this, ran a real cold test (task #30), following the
existing `cold_tests/` protocol exactly (pre-register → fresh subagent reads
only `start_instructions_v3.md` + the four `start_gallery/*.md` files + one
Pat description → score).

Pat's description (the news-subscription spec from this session, user's own
final revision, including "is the story positive" — deliberately left
unresolved earlier whether to keep this scope mismatch against the DSL `03`
example's four fields): watches BBC/Al Jazeera/NPR, works out who's involved /
severity / topic / location on every story, lets any friend ask for a slice
of that (e.g. who's mentioned, or something not yet computed like
positivity), delivers only what changed, compute-once regardless of how many
friends are watching, a friend can stop without affecting anyone else, and
Pat herself sees everything unconditionally. Friends are explicitly external,
not agents.

Result: **PASS, 5/5 scored criteria** (case 07 in `cold_tests/README.md`,
full transcript `cold_tests/transcripts/case_07_news_subscriptions.md`). The
cold instance built one shared `ANALYZER` feeding both Pat's own unconditional
view and a `ROUTER` keeper that matches any number of friends off that single
computation — no per-friend recomputation. It handled "is the story positive"
well: added a `tone` fact to `ANALYZER` and flagged it explicitly under
"Things I assumed," rather than silently misreading it onto severity or
topic. No gate or record was added to the subscription table — correctly
reasoned as a single-inbox keeper, the same pattern `trading_room`'s `LEDGER`
teaches. Friends stayed external (source/sink), never modeled as agents.

Significance: this is now real evidence, not just an argument, that Pat-speak
on the current unmodified instructions handles this pattern class without
needing an Al-style structural description first. It doesn't settle the
separate question of whether to keep Al for other reasons (still keeping
both, per Mani's decision above) — only that testers using Pat-speak alone
would, on this one case, get a good result. A natural follow-up (not yet
run): a correction round testing whether backfill — flagged as an assumption,
not resolved — is handled well once Pat actually asks for it.

## Phase 3 architecture — decided (2026-07-19)

Mani wants one complete, end-to-end path for Pat — OfficeSpeak spec all the way
to a runnable office — explicitly **excluding debug-run capability** for now,
after which he plans to stop extending this and pivot to using the same
approach to build a course. Motivation stated directly: "partly for my own
sanity... I'd like one complete end-to-end system." Decided to do this
carefully enough not to have to revisit it.

**The two-part split.** Making an office runnable has two independent pieces:
the network structure (wiring) and the agent implementations (worker bodies).
Checked directly: `dissyslab.builder.network(edges)` already builds a
`Network` straight from Python, no `office.md` needed — but it takes
*already-instantiated* `Agent` objects; it does no code/prompt generation. So
network wiring is solved; agent implementations are not. No converter from an
OfficeSpeak Phase 1/2 spec to either `office.md` or a live `Network` exists
anywhere in either repo (checked, including full git history) — this is real,
unstarted work, not something forgotten.

**The registered-agent gap.** `PARAMETERIZED_LIBRARY` (`dissyslab/office/library.py`)
currently has exactly two entries: `synchronizer` (OfficeSpeak's `merge_synch`,
already solved) and `router`. OfficeSpeak's other two registered coordinators —
`select` and `gate` — and the registered `record`, have **no generic DisSysLab
equivalent**. (`debate`'s own local `roles/gate.py` is an office-specific
custom role with different behavior, not a match — role-resolution precedence
means it won't collide with a new framework-level `gate`, so no naming risk.)

**Decided scope for the missing coordinators (build once, generically, same
pattern as `synchronizer`):**
- **select** — a generic engine driven by a state/transition table (which
  inbox to read next, whether to send, given current state). This is genuinely
  generic infrastructure, not per-office generated code.
- **gate** — implemented as *one fixed transition table over `select`*, not a
  separate implementation: two states (waiting-for-data, waiting-for-control);
  reading `data` sends and moves to waiting-for-control; reading `control`
  sends nothing and moves back. Matches OfficeSpeak's `gate` definition exactly.
- **record** — a plain store-and-reply keeper (request in, reply out, holds
  arbitrary data, parameterized by what it holds — same shape as
  `synchronizer` being parameterized by port names). **No internal locking.**

**Reader/writer (RW) lock — designed, then explicitly deferred.** Mani
proposed implementing `record` with its own internal reader/writer lock
(shared concurrent reads, exclusive writes) rather than relying on an external
`gate`. Worked through the design; the initial version had a real bug — no
release message and no logic to drain the pending queue, meaning the lock
could be granted at most once, ever. Corrected design would need: a **set**
(not a flag) of currently-granted readers, a release/done message type, and
per-requester tagging (like the tutor's id-keyed state) so grants and releases
match up to the right caller. Mani's own call once this complexity was surfaced:
**too complex for now — use plain `record` + `gate` and revisit RW only if a
real case needs the concurrency.** This required no change to
`start_instructions_v3.md`: "pair a record with a gate when it's both read and
written" is already the documented rule, so nothing Pat-facing changes: RW
would later be a swappable *implementation* detail behind the same registered
names, not a new taught concept. The RW design above is preserved here so it
isn't lost if the need arises later.

**Approval workflow (Phase 2 → generated code), and why it's simpler than it
sounds.** `start_instructions_v3.md`'s existing Phase 1 already fixes every
port's message shape via the "Pass A — every outbox, then Pass B — every
inbox, never invented" rule, before Phase 2 begins. So the new approval step
(Pat approves each LLM worker's prompt; each Python worker is tested on
example inputs) doesn't need to (re)decide message shapes — it only needs a
**fidelity check**: does this generated worker's actual code/prompt produce
and consume exactly what Phase 1 already committed to for its ports. That's
the check to build into the approval-protocol README, not a fresh design step.

**Compile target: `office.md`, not a direct `Network`.** Confirmed with Mani.
Full pipeline: **OfficeSpeak (Phase 1/2, already exists) → generate `office.md`
+ approved `roles/*.py` / `roles/*.md` (new work) → DisSysLab's existing
`compile_office`/`dsl build` (already exists, already tested) → runnable
code.** Only the first arrow is new. Reusing `office.md` means every generated
office lands on the same, already-tested, git-trackable, human-readable
artifact every hand-built gallery example and Track B example already uses —
deliberately not the `dissyslab.builder.network(edges)` path, which is
documented as a tools/tests convenience, not a production target.

**Source/sink matching — deferred to a human, not automated yet.** Matching a
Phase 2 source/sink description ("the BBC feed," "a console") against
DisSysLab's existing registered sources/sinks, with a fallback when nothing
fits, is being written up as a doc for a Python-familiar developer to execute
by hand, rather than automated in this pass.

**Concrete build list this unlocks (see tasks #16/#18 and new tasks):** build
`select`; build `gate` as a `select` instance; build `record` (plain, no
locking); validate `select`/`gate` against `start_gallery/trading_room.md`'s
correction case; validate `record`+`gate` against
`start_gallery/investment_club.md`; write the approval-protocol README (prompt
approval + Python testing + Pass A/B fidelity check); write the Phase 3
generator (approved spec → `office.md` + roles); write the source/sink-matching
doc for a developer. Debug-run capability (checkpoints, nondeterminism
recording) is explicitly out of scope for this push.

## select/gate built and validated (2026-07-19)

Built and validated the first piece of the Phase 3 plan above. Turned out
smaller than expected: `dissyslab/blocks/select.py` and
`dissyslab/blocks/gate.py` already existed as proper `Coordinator` subclasses
matching OfficeSpeak's semantics almost exactly — the missing piece was only
the office.md-facing registration layer (an `AgentRoleEntry` + a
`PARAMETERIZED_LIBRARY` entry, the same pattern `synchronizer`/`router`
already use), not the coordination engines themselves.

Added `select_role(inports, command)` and `gate_role(data, control)` to
`dissyslab/office/library.py`, registered both in `PARAMETERIZED_LIBRARY`,
exported from `dissyslab/office/__init__.py`. `select`'s design keeps it a
genuine *registered* primitive (no per-office judgment baked in, per
OfficeSpeak's own rule that a registered coordinator is never something you
implement yourself): one inport is reserved as `command`; a message there
(`{"next": "<inport>"}`) is the only thing that changes which inport select
reads next; every other inport's message is forwarded unchanged. This exactly
matches how `trading_room`'s traders actually use `select` — they, not
`select`, decide what "next" means.

One real subtlety surfaced and fixed: for any `AgentRoleEntry` with a single
declared outport, the compiler *always* maps it to the literal runtime port
`"out_"` regardless of what semantic name is declared (`office/_internals.py`,
`_runtime_outport`) — and for multiple outports, positionally to
`out_0`/`out_1`/… A first draft used a customizable `out_port=` kwarg that
would have silently mismatched this convention the moment anyone passed a
non-default value. Fixed by hardcoding the real agent's outport to the
literal runtime name and keeping the semantic name (`"out"`, matching
`synchronizer_role`) fixed and uncustomizable — the same lesson as inports,
which pass through *unchanged*, no positional translation, so `in_ports` must
literally equal the underlying agent's real inport names.

**Validated against a real office, not just inspection.** Built
`dissyslab/gallery/apps/trading_room/` — a small, deterministic, no-API-key
fixture implementing OfficeSpeak's `start_gallery/trading_room.md` Case 2
(one trader only; a second trader on market data would exercise the same
`select` mechanism again, not new coverage). `dsl build` succeeded and the
office ran and terminated cleanly. First run surfaced a real bug — not in
`select`, in the test fixture itself: the trader's own code distinguished "is
this a news item or a ledger reply" by checking for a `"headline"` key, but
both message kinds carry one, so every ledger reply was misread as a news
item and no trade was ever written despite the ledger approving two. Fixed by
checking for `"approved"` instead (present only on a reply). After the fix,
the run produced exactly the expected sequence — propose → reply → skip a
non-trade item → propose → reply → propose → rejected — with `trades.jsonl`
containing exactly the two approved trades in order. Confirms `select`
correctly withholds later news items while a trade proposal is outstanding,
the core behavior Case 2 exists to test.

`gate` is registered and smoke-tested at the construction level (right ports,
right factory) but not yet exercised inside a running office — that needs
`record` (task #32, `investment_club`'s record+gate case), which is
deferred, matching the RW-lock deferral above: plain `record` first, no
internal locking.

## record built and validated; select/gate/record now all done (2026-07-19)

Added `record_role(initial=...)` to `dissyslab/office/library.py`, registered
in `PARAMETERIZED_LIBRARY`. One real design fix needed before it worked:
`record` has exactly one outbox, so a "write" that produced a reply would
broadcast that reply to *everyone* connected to it, not just the agent that
wrote — there's no way to route a reply to "only the one that asked" through
a single outbox. Fixed by making writes silent (update state, no reply
message at all) and only reads reply. This isn't a workaround — it matches
what every existing OfficeSpeak example already assumes ("the ledger's reply
to the manager's write isn't wired anywhere; nobody needs to see it").

Validated against a real, running office (task #32): built
`dissyslab/gallery/apps/investment_club/`, implementing OfficeSpeak's
`start_gallery/investment_club.md` Case 2 — the "famous correction" where the
accountant must read current holdings from the ledger before pricing a trade,
not just the proposed move. Three periods, `Gate` admitting one at a time,
`Manager` writing updated holdings after each period, `Accountant` reading
them back before pricing the next. `dsl build` succeeded first try; the run
produced, and hand-verified by arithmetic: period 2's fee (16.80) and period
3's fee (26.40) exactly reflect the holdings *written* at the end of the
previous period (8 shares, then 24 shares) — proving the read-after-write
sequencing across the gate boundary is correct, not just that it runs
without crashing. Reran to confirm determinism: identical output both times.

Both validation fixtures (`trading_room`, `investment_club`) are small,
deterministic, and need no API key or network access — intentionally, so
they can be re-run as regression checks once the Phase 3 generator exists.

`gate` is still only exercised via `investment_club`'s pairing with `record`,
not on its own in an office where it isn't paired with anything — not
considered a gap, since OfficeSpeak's own rule is "record + gate," never
"gate" alone.

**Note for the paper.** In the actual code, `Select`, `Gate`, and `MergeSynch`
(`dissyslab/blocks/`) are three independent `Coordinator` subclasses, siblings
— none literally inherits from another. But the reduction still holds
conceptually: `MergeSynch`'s own `_get_inport`/`_step` (read whichever inport
this round hasn't filled; fill a slot; emit once all are full) is exactly a
state-driven policy of the kind `select`'s contract requires — the same
argument already made for `gate`. For the paper, it's fair to present
`select` as the general primitive and `merge_synch`/`gate`/`router` as
specific transition functions over that same shape, even though the shipped
code writes each one directly (clearer to read than an opaque transition
table) rather than building it literally on top of `Select`.

## Phase 3 generator built and validated end-to-end (2026-07-19)

Built the generator (task #18): `dissyslab/office/officespeak_spec.py` (the
input shape — `OfficeSpeakSpec`/`AgentSpec`/`ConnectionSpec`/`WorkerBody`,
OfficeSpeak's own vocabulary) and `dissyslab/office/from_officespeak.py`
(translates that into a `dissyslab.office.office_spec.OfficeSpec`, writes
role files for office-specific agents, calls the existing `make_office()`).
Confirmed the scope stayed as small as designed: no message-shape logic (already
fixed by Phase 1's Pass A/B), no source/sink matching (task #34's job, spec
already carries the resolved registered name).

Validated by actually building and running a generated office, not just
inspecting the code — reused `investment_club`'s already-hand-verified
numbers as the expected answer. Wrote a spec equivalent to that fixture,
generated an office from it, ran `dsl build` and the office itself, and got
byte-for-byte identical output (period 1/2/3 fees and holdings all match).

Three real bugs surfaced by that process, none of them things a design
review would have caught:

1. **`make_office`'s `_format_agent_line` dropped `RoleRef.args` entirely** —
   a real, previously-unnoticed bug in already-shipped code, not new code.
   Any parameterized role (`synchronizer`, `select`, `gate`, `record`,
   `deduplicator(by=...)`) silently lost its arguments when written back to
   `office.md` text. `_format_source_or_sink` already rendered args
   correctly; `_format_agent_line` just never got the same treatment. Fixed
   to match, and confirmed by a manual round-trip test (`make_office` →
   `parse_office_dir` → equal `RoleRef`, args included) since pytest isn't
   available in this sandbox to run the existing suite — read
   `tests/unit/office_v2/test_make_office.py` by hand to confirm no existing
   test exercises the args path, so no regression risk.
2. **My own `_translate_record` reused a check built for select/gate/
   synchronizer** (`out_ports == ("out",)`), but `record`'s single outport
   is semantically `"reply"`, not `"out"`. Caught immediately by `dsl
   build`'s own error message naming the mismatch.
3. **Approved Python bodies must be fully self-contained factories** — a
   first draft of the test spec had a helper constant defined as a sibling
   in the same file, not inside the factory; `inspect.getsource` only
   recovers the factory's own text, so the generated role file referenced a
   name that didn't exist, a silent `NameError` waiting to happen at
   runtime rather than a `dsl build` error. Fixed the test spec and added
   this as an explicit constraint to `phase3_approval.md` so it's not
   rediscovered per office.

`select`'s "detect a port named `command`" default and `record`'s "starts
empty if Phase 2 didn't say otherwise" default (both agreed with Mani) are
implemented as validated lookups in `from_officespeak.py`'s coordinator
translators — any mismatch raises a clear `GeneratorError` naming the
problem, never a silent guess.

Not yet done: task #34 (source/sink matching doc) and the still-open
`start_instructions_v3.md` gap this design pass surfaced — Phase 1 doesn't
yet teach "one of select's inports is the command port, name it `command`,"
so a cold Phase 1 conversation could still produce a select the generator
would correctly refuse rather than silently mishandle.

**Follow-up, same day:** renamed `record`'s outport from `"reply"` to
`"out"`, matching `select`/`gate`/`synchronizer`. Bug #2 above happened
specifically because `record` was the one coordinator with a different
outport name, needing its own separate check in `_translate_record` instead
of reusing `_require_single_out` — the docstring's "reply outbox" wording
was descriptive, not a naming rule the way `gate`'s `data`/`control` are, so
there was no real reason to keep the exception. Updated `record_role`
(`library.py`), `from_officespeak.py` (the special case is gone;
`_translate_record` now just calls `_require_single_out` like the other
three), and `investment_club`'s hand-built `office.md`
(`Ledger's reply is Accountant.` → `Ledger's out is Accountant.`). Reran
both the hand-built fixture and the generator's test spec afterward —
identical output to before, confirming the rename didn't change behavior,
only removed the special-cased code path that had caused the bug.

## Task #34 is a gate for external testers, not just a nice-to-have

Explicit decision (2026-07-19): the source/sink-matching doc (task #34) is
currently informally satisfied by Claude doing the matching by hand during
internal validation (`trading_room`, `investment_club`). That's fine for
building and testing the generator, but it does **not** scale to an external
tester — there's no one standing by to do that matching for them. Before
letting any external tester run the full OfficeSpeak → office.md chain
end to end, task #34 needs to actually be written and, ideally, wired into
the generator's own flow (even if the first version is just a lookup table a
developer maintains by hand, not automated matching). Recorded here so this
isn't quietly skipped once the cold end-to-end test (next section) passes
and it *looks* done.

## First full-chain cold test — PASS after one correction (2026-07-19)

Ran the first end-to-end validation of the whole chain (task #19): a cold
Phase 1/2 conversation, carried all the way through transcription,
approval, generation (`from_officespeak.py`), and a real run — not just
Phase 1/2 in isolation, which is all `cold_tests/` 01-07 ever exercised.
Case: shipment release, matching a warehouse scan to its manifest
paperwork by shipment ID before releasing to the loading dock. Full
writeup: `offices/claude_project/cold_tests/transcripts/
full_chain_case_01_shipment_release.md`; pre-registration in this
session's scratch output.

**Round 1 was a real, confirmed miss.** The cold instance chose
`merge_synch` for the matching step, even though its own explain-back
described keyed-by-shipment-ID behavior — something `merge_synch`
structurally cannot do (it pairs the *n*-th message per inbox by arrival
order, no key concept at all). Not a matter of interpretation: fed the
same deliberately-interleaved-across-shipments event order directly into
a real `MergeSynch`, and all three rounds paired the wrong scan with the
wrong manifest. This is exactly the risk pre-registered before the test
ran.

**Round 2 (a fresh cold instance, given the round-1 build plus a Pat-style
correction) fixed it correctly**: replaced the `merge_synch` coordinator
with a plain stateful transform keyed by shipment ID (the `trading_room`
`LEDGER` shape), and its explain-back was, this time, actually consistent
with what it built.

**Generation and run, done by me (not cold), completed the chain for the
first time end to end.** Transcribed the corrected design into an
`OfficeSpeakSpec`, wrote three approved Python worker factories (`SCAN`,
`MANIFEST`, `MATCH`), ran `build_office_from_officespeak` with no errors,
then `dsl run` on the result. Fed scans and manifests in deliberately
different orders across three shipments (the same interleaving that broke
`MergeSynch` above) — the generated office released all three, each
against its own correct paperwork. New gallery fixture:
`dissyslab/gallery/apps/shipment_release/` (`office.md` + `roles/scan.py`,
`roles/manifest.py`, `roles/match.py`, run artifacts `releases.jsonl`).

This closes task #19 and the "genuine join in a new domain" item on
`cold_tests/README.md`'s wishlist. It's also the first real, concrete
evidence for something argued only in the abstract before now: the
full-chain process (cold build → correction round → approval → generation
→ run) catches a genuine structural bug before it reaches generated code,
using the exact same discipline already validated for Phase 1/2 alone.
Task #34 remains open and required before any external tester — this case
still had me matching sources/sinks (`STARTER`→`starter`,
`DOCK`→`jsonl_recorder`) by hand.

**Sandbox note:** running DisSysLab in this sandbox requires stubbing the
`anthropic` package (no network access to pip-install it, and the repo's
own `.venv` is a macOS-native venv with broken symlinks + a
platform-specific `pydantic_core` build here) — same workaround
`situation_room_requests` and `tutor_multi.py` needed earlier. A minimal
`class Anthropic: ...` stub on `PYTHONPATH` is enough since building/
running an office never actually calls the LLM backend unless a worker is
a genuine judgment (prompt) worker, and this case has none.

## Repo state at end of this session

OfficeSpeak has local commits **not yet pushed** — the sandbox's `git push` fails
(`403` from the proxy reaching GitHub) every session; this needs to happen from
Mani's own machine (`cd ~/Documents/OfficeSpeak && git push`).

DisSysLab: the `situation_room_requests` commit (`6ae6010`, adds
`poll_interval` to the RSS sources) is committed but **not yet pushed** —
push from Mani's own machine. On top of that, as of this session's end there
are further **uncommitted** changes: `situation_room_requests/NOTES.md`
(two-terminal run instructions, replace-situation_room plan), the new
`dissyslab/start_gallery/` folder (untracked — `README.md`,
`01_single_agent.md`, `02_dynamic_subscriptions_ambiguity.md`,
`03_al_subscriber_handler.md`), the `select`/`gate`/`record` additions to
`dissyslab/office/library.py` and `dissyslab/office/__init__.py`, two new
validation fixtures: `dissyslab/gallery/apps/trading_room/` (`office.md` +
`roles/news_feed.py`, `roles/trader_news.py`, `roles/ledger.py`) and
`dissyslab/gallery/apps/investment_club/` (`office.md` +
`roles/period_feed.py`, `roles/val_analyst.py`, `roles/oppo_analyst.py`,
`roles/manager.py`, `roles/accountant.py`), the new Phase 3 generator
(`dissyslab/office/officespeak_spec.py`, `dissyslab/office/from_officespeak.py`),
the bug fix to `dissyslab/office/make_office.py` (`_format_agent_line` now
renders `RoleRef.args`), and each fixture's generated `build/` and output
jsonl from the validation runs (`trades.jsonl`, `periods.jsonl` — run
artifacts, fine to `.gitignore` rather than commit if that's not already the
convention here). Also new and uncommitted: the third validation/full-chain
fixture, `dissyslab/gallery/apps/shipment_release/` (`office.md` +
`roles/scan.py`, `roles/manifest.py`, `roles/match.py`, generated by
`from_officespeak.py`, plus its run artifact `releases.jsonl`). OfficeSpeak
also has uncommitted new/changed files: `offices/claude_project/
phase3_approval.md`, `offices/claude_project/cold_tests/transcripts/
full_chain_case_01_shipment_release.md`, and edits to
`offices/claude_project/cold_tests/README.md` (new "Full-chain cases"
section) reflecting the first full-chain test above. Not committed yet
since Mani didn't ask for a commit this round; review and commit next
session (`cd ~/Documents/DisSysLab && git add -A && git commit && git push`;
same for OfficeSpeak).

## Note on account switch

Conversations don't transfer between personal Claude accounts and can't be
imported. But the work is all in these two repos (+ GitHub), so nothing is lost —
only the chat context, which is what this file preserves. In the new account:
connect both folders, open this file, and continue.
