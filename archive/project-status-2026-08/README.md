# Archived plans — retired 2026-08-17

Superseded by **`project-status/PLAN_2026-08.md`**, which is the plan of
record. Nothing here is direction any more. Kept because the diagnoses and
design decisions inside them are still true and were expensive to reach.

The occasion for retiring all four at once: the CHI paper was dropped, and the
project narrowed to a single goal — a first-year builds an app they care about,
then studies the algorithms underneath it. Each of these documents was shaped
by a goal that no longer applies.

| File | What it was | Why it is retired | What is still worth reading in it |
|---|---|---|---|
| `RESTRUCTURE_PLAN.md` | The four-phase, reversible-first migration to `skills/` + `workshop/`, decisions locked 2026-08-15 | Its phasing was timed around the paper's tester round and its three-demo structure | The target tree is still the right shape, and is restated in the new plan. Its two hard constraints also still hold: never rename the PyPI package `dissyslab`, and do not move `mac_speed_suite` or `paper_trader` while testers hold links to them |
| `ROADMAP.md` | The single priority-ordered to-do list, 2026-07-23 | Already flagged stale in `INDEX.md` before this; the new plan replaces it outright | — |
| `HANDOFF.md` | Written for a fresh Claude session to pick a stalled thread up cold, 2026-07-16 | Superseded as a handoff by `PLAN_2026-08.md` + `INDEX.md`. Was over a month out of date | Detailed implementation history — the `gate` naming decision, the `GeneratorError` design, generator/translator mismatch handling. Useful as a record of *why* things are as they are |
| `DEMO_RECORDING_SCRIPT.md` | Shot list for a recruitment demo video | Recruitment was for the paper's tester cohort | — |

Not archived, and not plans either — nobody should read them as direction:

- `project-status/ASPIRATIONAL_README.md` — a picture, explicitly not a
  roadmap. Only its teaching thread is being pursued.
- `project-status/FEATURES.md` — a status snapshot, stale since 2026-07-21.
- `paper/` — kept as a record. The submission is not happening.
