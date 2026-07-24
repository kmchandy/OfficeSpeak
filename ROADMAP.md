# Roadmap — prioritized gaps (decided 2026-07-23)

One job: the single, priority-ordered to-do list for OfficeSpeak/DisSysLab.
`FEATURES.md` still holds the full built/scoped/designed
inventory (what exists); this file says what order to tackle what doesn't,
and records what we deliberately decided *not* to build and why, so that
question doesn't get re-opened by accident in a future session.

Update this file, not a fresh one, when priorities change — see `INDEX.md`'s
"keeping this current" note.

## Priority order

1. **Make already-built work visible.** We have a lot of examples and a lot
   of features that aren't visible to Pat, to Al, or to someone just
   browsing the website — and a visitor needs to see immediately that
   substantial, real work already exists here, not have to dig for it.
   Concretely: the front door (README, the GitHub Pages site, the two
   microcourses) needs to surface the breadth of what's built — the
   gallery of apps, the registered sources/sinks, the debugging/checkpoint
   story — much more prominently than it does today. This is a
   documentation/discoverability problem, not a code problem, and it's the
   top priority because every other item on this list is invisible until
   this is fixed.
   **Status (2026-07-23): mostly drafted, not fully finished.** Done:
   a new `index.html` landing page, a "What's already built" section in
   README, the Stage 1/2 microcourses fixed and restructured per tester
   feedback (Joe Kiniry), stale copies re-synced. **Not done yet:** (a)
   nothing has actually been pushed to GitHub, so none of this is live at
   kmchandy.github.io yet; (b) the microcourses themselves still don't
   have a "here's everything else that's built" slide — they now explain
   Stage 1/2 clearly, but don't showcase the gallery/sources-sinks breadth
   the way the new landing page does. Old related task (S10 slide wording)
   is resolved and folded into this item.

2. **Al-facing documentation: OpenRouter/multi-LLM, sources/sinks,
   deployment.** DisSysLab can already run different agents on different
   LLM backends via OpenRouter — but this is for **Al** (a Python- and
   OpenRouter-comfortable person), not Pat, who has no way to ask for this
   in English and isn't expected to. What's missing is documentation: a
   real how-to for Al covering backend/model selection, alongside the
   existing source/sink-matching docs and however Al is expected to deploy
   a finished office. Moved up in priority because these three (backends,
   sources/sinks, deployment) are the likely real friction points for the
   two testers arriving next week (a hedge fund and an environmental-sensor
   office both plausibly want a specific model or a specific connector),
   and because good docs here are cheap relative to their payoff.
   **Status (2026-07-23): done.** New doc
   `offices/claude_project/phase3_backends_and_deployment.md`, cross-linked
   from README (new step 2d) and INDEX.md — covers backend/model choice
   (thin layer on top of DisSysLab's already-thorough
   `LANGUAGE_MODELS.md`) and, the real gap, deployment: keeping an office
   running past a terminal session (nohup/tmux, a process supervisor),
   and how that interacts with checkpoint/resume on a crash.

3. **Reduce friction in Stage 2 for the Python-comfortable person.** There
   is no way to remove Al from the loop entirely — Stage 2 (turning a
   built office into a running one) needs someone who can follow
   `phase3_source_sink_matching.md` / `phase3_approval.md` by hand. That's
   accepted, not a gap to close. What *is* a real to-do: lowering the cost
   of being Al — tightening those two docs, cutting steps, clearer error
   messages — short of the "one command" goal that isn't realistic yet.
   **Status (2026-07-24): short-term fix done.** The two documented
   silent-failure footguns around single-outport transforms and `merge_synch`
   are closed: `dissyslab/blocks/role.py`'s new `status_aliases` lets an
   approved transform's code return either Track A's original port name
   (e.g. `"alert"`) or `"out"` — both route correctly, so the code no
   longer has to say `"out"` literally; and `synchronizer_role` (in
   `dissyslab/office/library.py`) now raises immediately, naming the inport
   and field, when two branches supply a colliding key, instead of silently
   letting one value overwrite the other. `phase3_al_howto.md` updated to
   match. **Postponed (2026-07-24): removing the single-in/out-port naming
   convention itself** (`"in_"`/`"out"`, also touching `office.md`'s
   compiler/parser convention and `core.py`/`builder.py`'s
   `default_inport`/`default_outport` — estimated 3-5 days). Postponed, not
   rejected, because it doesn't affect Pat at all — it's purely an Al-facing
   ergonomic choice, and the two footguns it would have prevented are
   already closed a different way (above). Revisit if it turns out to
   matter for a real reason later. **Also done (2026-07-24): the general
   friction-reduction pass.** Clearer, actionable error messages fixed
   across the pipeline Al actually hits: `compiler.py` (parameterized-role
   bad-argument errors now get "Did you mean?" + valid-argument lists, and
   the internal library-shape error points at `docs/EXTENDING.md`);
   `parser.py` (a missing `office.md`/`network.md` now says to run
   `assemble.py` first, instead of a bare "not found"); `builder.py` (the
   three "no default port" errors now list the agent's actual ports and
   the dot-notation fix); `cli.py`'s `dsl build`/`dsl run` failure-mapper
   (added a case for "office.md not generated yet" so it stops giving the
   wrong "check build/run.py" advice for that failure). Both docs
   (`phase3_source_sink_matching.md`, `phase3_approval.md`) tightened —
   redundant explanatory passages cut, nothing procedural removed.

4. **Guided onboarding / description elicitation for Pat.** A real gap.
   Today OfficeSpeak assumes Pat already knows roughly the shape of a good
   description (purpose, inputs/outputs, workers, what each needs to know).
   A guided conversation that gets a first-time Pat to a description likely
   to produce a correct office — while still keeping her in plain English,
   never a form — is designed in spirit (`paper/office_description_format.md`)
   but not built or evaluated as an actual onboarding flow.
   **Status (2026-07-24): built and cold-tested, 5/5.** New "Phase 0 — when
   Pat doesn't know where to start" section added to `start_instructions.md`,
   triggered only when Pat's opening is thin (skipped entirely if she already
   gives enough, e.g. the existing debate example). Combines four ingredients
   already sketched in `paper/draft_v2.md`'s limitations section: an anchor to
   the example gallery (`start_gallery/README.md`) for a genuinely stuck Pat,
   the team-metaphor question ("who would you hire?"), the story-of-one-item
   walkthrough, and — the highest-value one — a direct "what else does this
   worker need to see" probe, which is what actually catches the missing-
   connection gap the rest of Phase 1 relies on "Things I assumed —" to fix.
   Cold-tested five times total: one informal run (email-monitoring office)
   plus four pre-registered, scored cases now recorded in `cold_tests/README.md`
   under "Phase 0 (onboarding) cases" — a rich opening correctly skipping Phase
   0 entirely, a brief-but-not-stuck opening correctly skipping the gallery
   anchor, a stuck opening in a domain unlike any gallery example correctly
   avoiding a force-fit coordinator, and a case built so that only the
   needs-to-see probe (not the team question or the story walkthrough) could
   catch a real gap — which it did. Two wording refinements applied from these
   runs: the "stuck vs. merely brief" fork is now stated up front rather than
   buried in a qualifying sentence, and the needs-to-see question now suggests
   naming a concrete category (who/what, history, status) instead of staying
   fully open-ended. **Not yet done:** a case testing whether Phase 0 avoids
   re-asking something an earlier answer already implicitly covered, and a
   case with a misleading initial team description that the story-of-one-item
   step should catch — flagged as open in `cold_tests/README.md`, not blocking.

5. **Compositionality.** Plugging validated, standalone offices together
   into larger ones (or nesting one office as a worker inside another) is
   demonstrated only informally today, not as a systematic, first-class
   capability. (Task #34.)

6. **Per-agent process-vs-thread execution.** Al can already choose
   processes or threads for a whole office, but not mix the two within one
   office (one CPU-heavy worker as a process, the rest as threads).
   Al-facing, not Pat-facing. (Task #36.)

7. **Theory: from CS-theorist-facing UNITY specs to a Pat-facing
   certificate.** Split into two parts, 2026-07-23, because their
   priority diverged:

   **7a. UNITY specification of the substrate — elevated priority.**
   Prompted by Joe Kiniry/Sigil's interest in "more rigorous and
   trustworthy" agents. Write the actual UNITY-logic specification —
   safety/progress properties — for each coordination primitive
   (`merge_synch`, `gate`, `select`, `fair_merge`) and the logical
   structure of transforms/sources/sinks, as a document aimed at Joe and
   other CS theorists, not at Pat. This is the theoretical grounding for
   the trusted-primitives claim, made precise and formal, independent of
   whether or how it's ever translated into English for a non-programmer.
   **Open question:** who writes this — Mani directly (UNITY is his own
   formalism), or a first drafted skeleton for Mani to correct? Not yet
   decided.

   **7b. Surfacing a certificate to Pat, in English — still long-horizon,
   unchanged.** Deliberately *not* "show Pat a proof" (the proofs are
   about the primitives, not her specific office) but something like a
   per-office *certificate* — "this office is guaranteed to terminate
   because it only uses coordinators proven not to starve" — in the same
   honest, disclosed register as "Things I assumed." Explicitly postponed:
   turning 7a's formal logic into good English for a non-programmer is
   real, separate work (figuring out with Claude how best to make that
   translation), and doesn't need to happen before 7a does. Still Mani's
   own project, still expected around the January course.

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
