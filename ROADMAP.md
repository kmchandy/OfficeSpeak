# Roadmap — prioritized gaps (decided 2026-07-23)

One job: the single, priority-ordered to-do list for OfficeSpeak/DisSysLab.
`FEATURES.md` still holds the full built/scoped/designed
inventory (what exists); this file says what order to tackle what doesn't,
and records what we deliberately decided *not* to build and why, so that
question doesn't get re-opened by accident in a future session.

Update this file, not a fresh one, when priorities change — see `INDEX.md`'s
"keeping this current" note.

## Priority order

1. **Compositionality.** Plugging validated, standalone offices together
   into larger ones (or nesting one office as a worker inside another) is
   demonstrated only informally today, not as a systematic, first-class
   capability. (Task #34.)

2. **Per-agent process-vs-thread execution.** Al can already choose
   processes or threads for a whole office, but not mix the two within one
   office (one CPU-heavy worker as a process, the rest as threads).
   Al-facing, not Pat-facing. (Task #36.)

3. **Theory: from CS-theorist-facing UNITY specs to a Pat-facing
   certificate.** Split into two parts, 2026-07-23, because their
   priority diverged:

   **3a. UNITY specification of the substrate — elevated priority.**
   Prompted by Joe Kiniry/Sigil's interest in "more rigorous and
   trustworthy" agents. Write the actual UNITY-logic specification —
   safety/progress properties — for each coordination primitive
   (`merge_synch`, `gate`, `select`, `fair_merge`) and the logical
   structure of transforms/sources/sinks, as a document aimed at Joe and
   other CS theorists, not at Pat. This is the theoretical grounding for
   the trusted-primitives claim, made precise and formal, independent of
   whether or how it's ever translated into English for a non-programmer.
   Mani is writing this himself (task #54); no draft exists yet as of
   2026-07-24 — Claude's role is converting the finished English-plus-
   notation draft into typeset LaTeX and compiling it to PDF.

   **3b. Surfacing a certificate to Pat, in English — still long-horizon,
   unchanged.** Deliberately *not* "show Pat a proof" (the proofs are
   about the primitives, not her specific office) but something like a
   per-office *certificate* — "this office is guaranteed to terminate
   because it only uses coordinators proven not to starve" — in the same
   honest, disclosed register as "Things I assumed." Explicitly postponed:
   turning 3a's formal logic into good English for a non-programmer is
   real, separate work (figuring out with Claude how best to make that
   translation), and doesn't need to happen before 3a does. Still Mani's
   own project, still expected around the January course.

## Completed

1. **Make already-built work visible.** Landing page (`index.html`), a
   "What's already built" section in README, both microcourses fixed and
   restructured per tester feedback (Joe Kiniry), and `stage1_microcourse
   .html`'s S2b/S2c slides now showcase the gallery/sources-sinks breadth
   directly in the microcourse. Done 2026-07-24, pending only your own
   push to GitHub — nothing is live at kmchandy.github.io until then.
2. **Al-facing documentation: backends, sources/sinks, deployment.**
   `offices/claude_project/phase3_backends_and_deployment.md`, cross-linked
   from README and INDEX.md. Done 2026-07-23.
3. **Reduce friction in Stage 2 for Al.** Closed the two documented
   silent-failure footguns — `dissyslab/blocks/role.py`'s `status_aliases`
   (a transform's code can return Track A's original port name instead of
   the forced `"out"`) and `synchronizer_role`'s loud collision check
   (`dissyslab/office/library.py`) — plus a general error-message and
   doc-tightening pass across `compiler.py`/`parser.py`/`builder.py`/
   `cli.py`/`phase3_source_sink_matching.md`/`phase3_approval.md`.
   Removing the `"in_"`/`"out"` single-port naming convention itself was
   considered and **postponed, not rejected** — it's purely Al-facing,
   doesn't touch Pat at all, and the footguns it would have prevented are
   already closed a different way; ~3-5 days of work if it's ever worth
   revisiting (also touches `office.md`'s compiler/parser convention and
   `core.py`/`builder.py`'s `default_inport`/`default_outport`). Done
   2026-07-24.
4. **Guided onboarding / description elicitation for Pat.** New "Phase 0
   — when Pat doesn't know where to start" section in `start_instructions
   .md` — an anchor to the example gallery for a genuinely stuck Pat, the
   team-metaphor question, a story-of-one-item walkthrough, and a direct
   "what else does this worker need to see" probe. Cold-tested 5/5 (one
   informal run plus four pre-registered, scored cases — see `cold_tests/
   README.md`'s "Phase 0 (onboarding) cases"). A lightweight written
   template (instead of the live conversation) was considered and set
   aside for now: the needs-to-see probe's value depends on adaptive,
   worker-specific follow-up a static template can't reproduce. Two open,
   non-blocking follow-up cases noted in `cold_tests/README.md`. Done
   2026-07-24.

## Decided not to pursue (with rationale, so it isn't silently re-opened)

- **Live "why is nothing moving" diagnostic** (debugging aid (b),
  channel-count liveness). "Nothing moving" on a channel isn't a reliable
  bug signal by itself — a Coordinator legitimately blocked on one inbox by
  design looks identical to one that's stuck, from counts alone. Living
  with the gap: after-the-fact explanation via `dsl explain-trace` /
  `dsl show-checkpoint` is the debugging story for a hung office; there's
  no live detector. See `DisSysLab/docs/internals/debugging_aids_decision.md`.
- **Debug-mode exact bit-for-bit replay.** What a user actually wants while
  debugging is closer to step-control — "next, make agent X receive a
  message" — which needs the substrate to run its own scheduler instead of
  handing agents to Python's thread scheduler. That's a different runtime
  architecture, not an incremental feature, and isn't worth the cost here.
  What stays: read-only narration of a run or checkpoint that already
  happened, which needs no custom scheduler because it re-executes nothing.
  See `DisSysLab/docs/internals/replay_debug_mode_decision.md`.
- **Maintenance as live extension of a running office.** Not a supported
  capability, and not on the roadmap to become one. The only supported path
  to change a running office is: stop it, edit the description/office, and
  restart. No in-place upgrade of a live office.

## Tracked, but not a build item

- **Evidence from real, independent non-programmers.** Every worked
  example so far (investment club, room-climate monitor) was author-written.
  The two tester conversations scheduled next week, and a larger cohort of
  50+ first-time users this term, are the actual fix — not a system gap,
  but a real one, and the reason nothing in `paper/draft_v3.md`'s
  evaluation section overclaims. See `paper/draft_v3.md` §8.
