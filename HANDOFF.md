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

## Repo state at end of this session

OfficeSpeak has local commits **not yet pushed** — the sandbox's `git push` fails
(`403` from the proxy reaching GitHub) every session; this needs to happen from
Mani's own machine (`cd ~/Documents/OfficeSpeak && git push`). DisSysLab was
untouched this session (no code changes there).

## Note on account switch

Conversations don't transfer between personal Claude accounts and can't be
imported. But the work is all in these two repos (+ GitHub), so nothing is lost —
only the chat context, which is what this file preserves. In the new account:
connect both folders, open this file, and continue.
