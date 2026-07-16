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
  live)**, `room_monitor.py`, `triage_swap.py`, `triage_llm.py`.
- Note on interaction: a Cowork run is non-interactive (no live keyboard), so the
  in-chat demo uses `tutor_llm.py` (fixed answers); a real student types into
  `tutor_interactive.py` in a normal terminal.

Phase 1 (start module) and cold tests live under
`offices/claude_project/` (`start_instructions_v3.md`, `start_gallery/`,
`cold_tests/` 5/5).

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

## Immediate next steps (where we were headed)

1. **Pat role-play (next session):** Mani plays a brand-new Pat using the
   `README.md` walkthrough — paste the description, see the explain-back +
   diagram, run `tutor_llm.py`, then change it in English. Smooth out any friction
   found.
2. **The parent-alert watcher (point 4):** add a small *Python* worker that counts
   wrong answers and alerts a parent after N misses — the deliberate "add exact,
   auditable code back" example. Add it to the tutor diagram.
3. **Later:** multi-student tutor; other testers (a journalist with a Claude key; a
   hedge-fund non-programmer); debug-mode + checkpoint replay explained in English
   (phase 3, not needed for pilot); paper (`paper/draft_v2.md`).

## Session checkpoint — 2026-07-16 (this Cowork session)

Picked up from this file in a fresh Cowork session. Status to resume from:

- Both `OfficeSpeak` and `DisSysLab` folders are connected in this session, with
  confirmed read/write access (verified with a write+delete test, cleaned up
  after).
- OfficeSpeak had 1 local commit ahead of `origin/main`
  (`9c59892 Update HANDOFF.md: interactive tutor, README is the onboarding doc,
  repos public`). **`git push` failed from the sandbox** — proxy returned
  `403` trying to reach GitHub. This still needs to be pushed from Mani's own
  machine. DisSysLab was already up to date with origin.
- Asked Mani which "immediate next step" from this file to tackle (Pat
  role-play, parent-alert watcher, or a later-stage item). Answer: no
  preference given yet.
- Given no preference, leaning toward **the parent-alert watcher** (item 2
  below) since it's a self-contained coding task; a task list for it was
  created (5 subtasks) but **no exploration or code changes have been made
  yet** — work stops right after confirming folder access, before reading
  `offices/phase2_demo/worker.py`, `harness.py`, `tutor_llm.py`.
- Next action on resume: either (a) confirm doing the parent-alert watcher and
  start by reading those three files to learn the Worker contract and
  `build_office` spec format, or (b) switch to whichever item Mani actually
  wants.

## Note on account switch

Conversations don't transfer between personal Claude accounts and can't be
imported. But the work is all in these two repos (+ GitHub), so nothing is lost —
only the chat context, which is what this file preserves. In the new account:
connect both folders, open this file, and continue.
