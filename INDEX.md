# Index — where everything lives

A map of every doc across both repos, so you can find things without holding
paths in your head. This is a **navigation** doc — for *what's actually
built*, see `project-status/FEATURES.md`; for *paper-specific* working notes,
see `paper/PAPER_NOTES.md`; for *picking up a stalled session cold*, see
`project-status/HANDOFF.md`. Those three don't duplicate each other or this
file — each has one job.

**Reorganized 2026-08-06:** top-level files grouped into `guides/`
(tester-facing onboarding/walkthroughs), `project-status/` (Claude/Mani-facing
snapshots of where things stand), and `paper/` (everything CHI-submission
related). `offices/` and `examples/` — pre-current-framework prototypes and
design-exploration drafts, superseded by DisSysLab's real gallery apps and by
working directly in Cowork instead of a claude.ai Project — moved to
`archive/`, with `archive/README.md` explaining what superseded each piece.
Nothing was deleted; everything is still findable via this index or git
history.

**Also worth flagging plainly, not just in `project-status/`:**
`project-status/FEATURES.md`, `ROADMAP.md`, `HANDOFF.md`, and
`guides/gallery_overview.md` all predate the biggest recent stretch of work —
`mac_speed_suite`'s multi-strategy rebuild, `adaptive_tutor`,
`salton_sea_dashboard`, and both Cowork skills (`backtest-strategy-builder`,
`tutor-subject-builder`) don't appear in any of them. Treat those four files
as historical snapshots of an earlier state, not current status, until
they're refreshed.

**Keeping this current:** when you (or a session with me) add a new doc
anywhere in either repo, add one line for it here. That's the whole
maintenance cost — a habit, not a project.

---

## Start here

- **`README.md`** — the front door. Stage 1 (describe it, no install) / Stage 2
  (run it for real) walkthrough, investment-club example throughout. **Note:**
  its Stage 1/2 instructions still point at `offices/claude_project/...`
  paths, which are now under `archive/offices/claude_project/` — this file
  hasn't been updated since the reorg. Likely to be superseded outright once
  the planned new user manual (backtesting as the running example) exists,
  rather than patched in place — flagged, not fixed, pending that decision.
- **`project-status/FEATURES.md`** — what's actually built vs. scoped vs.
  designed, across both repos, verified against real code as of 2026-07-21.
  **Stale** — see note above.
- **`project-status/ROADMAP.md`** — the single, priority-ordered to-do list
  (added 2026-07-23). **Stale** — see note above.
- **`project-status/HANDOFF.md`** — written for a fresh Claude session with no
  memory of prior work, to pick a stalled thread back up cold. Dated
  2026-07-16 — was already flagged stale as of the last INDEX revision, and is
  now three weeks further out of date.

### The Trusted Skills restructure (2026-08-15/16) — current, not stale

These are the newest docs in either repo and the right place for a fresh
session to start. Read them in this order:

- **`project-status/RESTRUCTURE_PLAN.md`** — the decisions locked 2026-08-15:
  project story/name (**Trusted Skills**), the target tree (`dissyslab/` library
  at root, `skills/` for the foundation + domain skills, `workshop/` for the
  student tier), and a four-phase reversible-first migration sequence. **We are
  in Phase 0 — framing only; no files have been moved.** Also records what must
  *not* happen yet: no Phase 2 migration during the active tester round, and
  the PyPI package name never changes.
- **`project-status/README_DRAFT_trusted_skills.md`** — the drafted public front
  door for the single repo, all sections written. Supersedes an earlier
  `README_trusted_skills.md`, since deleted. Decision recorded in its header:
  "trusted skill" is no longer used as a defined term in body text — the
  artifacts are *skills* in the standard Agent Skills sense (now a cross-vendor
  open format, not Anthropic-specific), and a section states the two properties
  that actually distinguish these ones: the agent composes machinery it does
  not write, and the checks run on code the skill's author never saw. Two
  `[CHECK]` markers flag claims not yet verified against the code.
- **`project-status/ASPIRATIONAL_README.md`** — **private, not for the public
  repo.** The picture rather than the plan: what becomes reachable when a
  capable agent stands on a floor it can trust — the fourth beat (growth) after
  provision/trust/habit, and a gallery of futures that do not exist yet. Read
  it alongside the draft README; it carries the *why* the public page
  deliberately leaves out.

---

## Strategic / paper

- **`paper/PAPER_NOTES.md`** — working notes for the CHI 2027 submission
  (deadline **September 10, 2026**, gated on real tester feedback landing by
  **August 25** — see PAPER_NOTES §9 for the go/no-go decision). Checkpoint-
  explainer design, the logical-clock trace design, the "framework builds
  frameworks" / **higher-order office** pillar (mac_speed_suite,
  adaptive_tutor), the three-condition framework-value-add argument now in
  `draft_v3.md`'s introduction, and open novelty-claim verification needed
  before submission.
- **`paper/FRAMEWORK_EXTENSION_PATTERN.md`** — the abstract recipe behind the
  higher-order-office pattern (five ingredients, worked through for
  mac_speed_suite, adaptive_tutor, and a hypothetical cockpit/dashboard case),
  generalized from `paper/PAPER_NOTES.md`'s per-domain sections.
- **`paper/draft_v3.md`** — the paper draft itself.
- **`DisSysLab/docs/internals/URGENT_termination_detection_coordinator_bug.md`**
  — explicitly says it "underpins the paper's termination-detection claim."
  Resolved 2026-07-15, but re-verify before leaning on it in the writeup,
  since the fix is recent.
- **`archive/offices/claude_project/cold_tests/README.md`** +
  `cold_tests/transcripts/` (9 cases) — a real, rigorous evaluation protocol
  (pre-registered outcomes, uncontaminated fresh subagents). This is validity
  evidence for the paper, easy to forget it already exists now that it's
  under `archive/`.

## Tester-facing / onboarding (all under `guides/` as of the 2026-08-06 reorg)

- **`README.md`** — see above (top level, not moved).
- **`guides/GETTING_THE_FILES.md`** — how a first-time tester with no repo
  gets the files (ZIP download or clone), including the GitHub-bootstrap
  problem.
- **`guides/STAGE2_WALKTHROUGH.md`** — a second full Stage 2 example
  (fractions tutor), the Cowork-based route rather than a plain terminal.
- **`guides/INVESTMENT_CLUB_WALKTHROUGH.md`** — the investment-club story
  alone, start to finish, no setup/troubleshooting text in between.
- **`guides/DEBUG_TRACE_AND_CHECKPOINT_WALKTHROUGH.md`** — extreme-step-by-step
  teaching doc for `dsl run --trace`, `dsl explain-trace`, `dsl run
  --snapshot-interval`, and `dsl show-checkpoint`, using `recovery_demo`
  (the π example).
- **`stage1_microcourse.html`** / **`stage2_microcourse.html`** (top level,
  not moved — see "known loose ends") — the 2-minute visual versions of
  Stage 1 / Stage 2. Live at `kmchandy.github.io/OfficeSpeak/`.
- **`gallery_microcourse.html`** (top level, not moved) — a third
  microcourse, browsing the full breadth of what's built as of 2026-07-26 —
  all 33 DisSysLab offices grouped by shape/cost tier at that time, plus
  real, unedited excerpts from 3 of the 9 `cold_tests/transcripts/` cases.
  Predates everything built since (see staleness note above).
- **`guides/gallery_overview.md`** — the reading version of the same gallery.
  **Stale** — see note above; doesn't mention mac_speed_suite's multi-strategy
  form, adaptive_tutor, or salton_sea_dashboard.
- **`project-status/DEMO_RECORDING_SCRIPT.md`** — shot list for a recruitment
  video (not yet recorded; recruiting by phone call instead, and by direct
  outreach to testers, for now). Moved to `project-status/` rather than
  `guides/` since it's planning material, not tester-facing content.
- **`guides/TESTER_MANUAL.md`** — a short stub pointing back to `README.md`
  (its content was merged into README during the Stage 1/2 restructure).

## OfficeSpeak's own operating instructions (Claude-facing, not tester-facing) — ARCHIVED

Everything below moved to `archive/offices/claude_project/` on 2026-08-06:
superseded by working directly in Cowork sessions, which is how every
current gallery app (`mac_speed_suite`, `adaptive_tutor`,
`salton_sea_dashboard`) was actually built. See `archive/README.md` for the
full explanation. Kept for provenance and because `cold_tests/transcripts/`
(above) still has paper-evidentiary value.

- `start_instructions.md`, `project_instructions.md`, `OfficeSpeak_gallery.md`
  / `start_gallery/`, `phase3_*.md`, `SETUP.md`,
  `backlog_generated_coordinators.md`, `investment_club_handoff.py`.

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
  the logical-clock trace (designed).
- `replay_debug_mode_decision.md` — the *harder*, different feature (exact
  bit-for-bit replay from a checkpoint for engineers); scoped, not built.
- `URGENT_termination_detection_coordinator_bug.md` — resolved 2026-07-15.

**User-facing guides** (`docs/` top level): `GETTING_STARTED.md` (10-minute
install + first office), `API_KEY_SETUP.md`, `BUILD_APPS.md` (how to design
an office), `EXTENDING.md` (local-to-your-office vs. up-into-the-framework),
`LANGUAGE_MODELS.md` (LLM-backed roles), `PATTERN_sense_think_respond.md`,
`SOURCES_AND_SINKS.md` (the full registered catalogue), `TROUBLESHOOTING.md`.

## Gallery apps & examples (DisSysLab)

The real, current gallery lives entirely in DisSysLab, not here:
`dissyslab/gallery/apps/` (full offices, including `mac_speed_suite`,
`adaptive_tutor`, and `salton_sea_dashboard`, none of which are reflected in
`project-status/FEATURES.md`'s count yet) and each app's `skill_for_testers/`
for the two packaged Cowork skills. `guides/gallery_overview.md` is the
readable index, but see the staleness note above before trusting its count.

`examples/` in *this* repo (the older, pre-current-framework design drafts)
moved to `archive/examples/` — see `archive/README.md`.

---

## Known loose ends (things flagged but not resolved)

- `README.md` still documents the archived `claude_project/` Stage 1/2 flow —
  flagged above, not yet fixed; likely superseded by the planned new manual
  rather than patched.
- `backlog_generated_coordinators.md` (now `archive/offices/claude_project/`)
  — undecided design question, unresolved before the archive.
- `project-status/HANDOFF.md`, `FEATURES.md`, `ROADMAP.md`,
  `guides/gallery_overview.md` — all stale, need a refresh (see top of this
  file).
- Debugging aid (b) and debug-mode exact replay — decided not to pursue
  (`project-status/ROADMAP.md` has the reasoning); aid (c) is built.
- **`index.html`, `stage1_microcourse.html`, `stage2_microcourse.html` exist as
  copies in two repos** — this `OfficeSpeak` repo (where they're edited) and
  `kmchandy.github.io/OfficeSpeak/` (what's actually served). Nothing keeps
  them in sync automatically; they've already drifted once before. Whoever
  edits one of these three files needs to copy the change to the other repo
  too, and both repos need to be committed and pushed before anything is
  actually live.
