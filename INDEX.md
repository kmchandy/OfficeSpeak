# Index — where everything lives

A map of every doc across both repos, so you can find things without holding
paths in your head. This is a **navigation** doc — for *what's actually
built*, see `FEATURES.md`; for *paper-specific* working notes, see
`PAPER_NOTES.md`; for *picking up a stalled session cold*, see `HANDOFF.md`.
Those three don't duplicate each other or this file — each has one job.

**Keeping this current:** when you (or a session with me) add a new doc
anywhere in either repo, add one line for it here. That's the whole
maintenance cost — a habit, not a project.

---

## Start here

- **`README.md`** — the front door. Stage 1 (describe it, no install) / Stage 2
  (run it for real) walkthrough, investment-club example throughout.
- **`FEATURES.md`** — what's actually built vs. scoped vs. designed, across
  both repos, verified against real code as of 2026-07-21.
- **`ROADMAP.md`** — the single, priority-ordered to-do list (added
  2026-07-23): what to build next and in what order, plus what was
  deliberately decided *not* to pursue and why (so those questions don't
  get silently re-opened).
- **`HANDOFF.md`** — written for a fresh Claude session with no memory of prior
  work, to pick a stalled thread back up cold. **Dated 2026-07-16 — five days
  stale as of this index.** Worth refreshing given how much happened since
  (Stage 1/2 README rewrite, both microcourses, the checkpoint/trace design,
  the CHI 2027 paper notes, `kmchandy.github.io` cleanup). Ask me to update it
  next time we talk.

---

## Strategic / paper

- **`PAPER_NOTES.md`** — working notes for the CHI 2027 submission (deadline
  **September 10, 2026**). Checkpoint-explainer design, the logical-clock
  trace design and its confirmed decisions, the "bridges" theme fit, open
  novelty-claim verification needed before submission.
- **`DisSysLab/docs/internals/URGENT_termination_detection_coordinator_bug.md`**
  — explicitly says it "underpins the paper's termination-detection claim."
  Resolved 2026-07-15, but re-verify before leaning on it in the writeup,
  since the fix is recent.
- **`offices/claude_project/cold_tests/README.md`** + `cold_tests/transcripts/`
  (9 cases) — a real, rigorous evaluation protocol (pre-registered outcomes,
  uncontaminated fresh subagents). This is validity evidence for the paper,
  easy to forget it already exists.

## Tester-facing / onboarding

- **`README.md`** — see above.
- **`GETTING_THE_FILES.md`** — how a first-time tester with no repo gets the
  files (ZIP download or clone), including the GitHub-bootstrap problem.
- **`STAGE2_WALKTHROUGH.md`** — a second full Stage 2 example (fractions
  tutor), the Cowork-based route rather than a plain terminal.
- **`INVESTMENT_CLUB_WALKTHROUGH.md`** — the investment-club story alone,
  start to finish, no setup/troubleshooting text in between.
- **`DEBUG_TRACE_AND_CHECKPOINT_WALKTHROUGH.md`** — extreme-step-by-step
  teaching doc for `dsl run --trace`, `dsl explain-trace`, `dsl run
  --snapshot-interval`, and `dsl show-checkpoint`, using `recovery_demo`
  (the π example). Added 2026-07-22, same day the trace/checkpoint-explainer
  features it documents were built and verified.
- **`stage1_microcourse.html`** / **`stage2_microcourse.html`** — the 2-minute
  visual versions of Stage 1 / Stage 2. Live at
  `kmchandy.github.io/OfficeSpeak/` (also present in this repo).
- **`gallery_microcourse.html`** — added 2026-07-26: a third microcourse, same
  visual format, browsing the full breadth of what's built — all 33 DisSysLab
  offices grouped by shape/cost tier, plus real, unedited excerpts from 3 of
  the 9 `cold_tests/transcripts/` cases. Answers the gap that `README.md`
  linked `FEATURES.md` as plain text and never linked the cold-test
  transcripts at all. Live at `kmchandy.github.io/OfficeSpeak/` alongside the
  other two (also present in this repo).
- **`gallery_overview.md`** — added 2026-07-26: the reading version of the
  same gallery, linked right next to `gallery_microcourse.html` from
  `README.md`. A quick-index table plus narrative sections organized by the
  four "which shape is like yours" categories and by domain (news/markets,
  personal/productivity, perception, deliberating teams, small patterns,
  real transcripts) — meant to actually be searched, not just skimmed.
- **`DEMO_RECORDING_SCRIPT.md`** — shot list for a recruitment video (not yet
  recorded; recruiting by phone call instead for now).
- **`TESTER_MANUAL.md`** — now a short stub pointing back to `README.md`
  (its content was merged into README during the Stage 1/2 restructure).

## OfficeSpeak's own operating instructions (Claude-facing, not tester-facing)

- **`offices/claude_project/start_instructions.md`** — the actual custom
  instructions pasted into the claude.ai Project. (Renamed from
  `start_instructions_v3.md`; old v1/v2/CHECKPOINT versions deleted.)
- **`offices/claude_project/project_instructions.md`** — defines the
  Pat-facing assistant persona and job.
- **`offices/claude_project/OfficeSpeak_gallery.md`** /
  **`start_gallery/`** — the worked examples uploaded as Project knowledge.
- **`offices/claude_project/phase3_source_sink_matching.md`**,
  **`phase3_approval.md`**, **`phase3_al_howto.md`**,
  **`phase3_assistant_instructions.md`** — the Stage 2 (Al-facing) process:
  matching, approval, and a real end-to-end walkthrough with real commands.
- **`offices/claude_project/phase3_backends_and_deployment.md`** — added
  2026-07-23 (ROADMAP.md item 2): backend/model choice for judgment
  workers and deploying an office to keep running past the terminal
  session (nohup/tmux, a process supervisor, and how that interacts with
  checkpoint/resume). Not a required gate like matching/approval, but
  real ongoing use almost always needs it.
- **`offices/claude_project/phase3_composition.md`** — added 2026-07-24
  (ROADMAP.md item 1): reusing an already-built, already-tested office as
  a single worker (`kind="department"`) inside a new one. Al-only, tested
  end-to-end (single- and multi-port cases); Pat's Stage 1 conversation is
  unchanged. See also `backlog_generated_coordinators.md`, whose open
  taxonomy question this resolves.
- **`offices/claude_project/SETUP.md`** — one-time setup + repeatable
  per-demo loop (operational, for running demos yourself).
- **`offices/claude_project/backlog_generated_coordinators.md`** — an
  **open, undecided** backlog item: whether to let Claude generate a custom
  multi-inbox coordinator, vs. the current rule that all coordinators are
  registered/predefined. Not yet folded into `start_instructions.md`.
- **`offices/claude_project/investment_club_handoff.py`** — the verified
  reference hand-off file backing README's Stage 2 numbers.

## Technical design docs (DisSysLab)

**Algorithms** (`docs/algorithms/`):
- `CHECKPOINT_RESUME.md` — the global snapshot algorithm, built & verified.
- `TRACE_AND_LOGICAL_CLOCK.md` — the logical-clock activity-log trace design,
  fully designed with all open questions resolved, not yet built.

**Internals** (`docs/internals/`) — architecture/implementation references:
`architecture.md`, `core_overview.md` / `core_implementation.md`,
`network_overview.md` / `network_implementation.md`,
`builder_overview.md` / `builder_implementation.md`, `blocks_implementation.md`,
`making_a_component.md`, `common_gotchas.md` (real foot-guns from real use).

**Internals** — decision docs (dated, recorded, some resolved):
- `coordinator_design.md` — why `Coordinator` is the base for every
  *deterministic* coordination primitive; `fair_merge` is the one exception.
- `debugging_aids_decision.md` — the three debugging aids as one family: (a)
  isolated worker testing (built), (b) channel-count liveness (scoped), (c)
  the logical-clock trace (designed) — cross-referenced as of this session.
- `replay_debug_mode_decision.md` — the *harder*, different feature (exact
  bit-for-bit replay from a checkpoint for engineers); scoped, not built.
- `URGENT_termination_detection_coordinator_bug.md` — resolved 2026-07-15.

**User-facing guides** (`docs/` top level): `GETTING_STARTED.md` (10-minute
install + first office), `API_KEY_SETUP.md`, `BUILD_APPS.md` (how to design
an office), `EXTENDING.md` (local-to-your-office vs. up-into-the-framework),
`LANGUAGE_MODELS.md` (LLM-backed roles), `PATTERN_sense_think_respond.md`,
`SOURCES_AND_SINKS.md` (the full registered catalogue), `TROUBLESHOOTING.md`.

## Gallery apps & examples (DisSysLab)

Full list with one-line descriptions is in `FEATURES.md` §4 (33 total: 24
apps + 9 examples) — not repeated here to avoid the two files drifting out of
sync. Categories: news/market monitoring (largest cluster), personal/
productivity, perception (audio/image), multi-agent structure demos and
validation fixtures, direct-`office.md` examples, and the `my_first_office`
starter.

---

## Known loose ends (things flagged but not resolved)

- `backlog_generated_coordinators.md` — undecided design question, see above.
- `HANDOFF.md` — stale, needs a refresh.
- Debugging aid (b) and debug-mode exact replay — decided not to pursue
  (`ROADMAP.md` has the reasoning); aid (c) is built.
- **`index.html`, `stage1_microcourse.html`, `stage2_microcourse.html` exist as
  copies in two repos** — this `OfficeSpeak` repo (where they're edited) and
  `kmchandy.github.io/OfficeSpeak/` (what's actually served at
  kmchandy.github.io/OfficeSpeak/). Nothing keeps them in sync automatically;
  they've already drifted once (`stage2_microcourse.html`, caught and fixed
  2026-07-23). Whoever edits one of these three files needs to copy the
  change to the other repo too, and both repos need to be committed and
  pushed before anything is actually live — see `ROADMAP.md` item 1.
