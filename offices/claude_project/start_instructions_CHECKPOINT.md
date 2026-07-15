# Checkpoint — OfficeSpeak "start" module + gallery (2026-07-13)

Current state so work can resume after a break.

## Where things stand

**`start_instructions_v3.md` — essentially done.** Two-phase structure (Phase 1
network, Phase 2 English descriptions), four agent kinds (source / sink / transform /
coordinator) with `agent` as the umbrella and `worker` as the Pat-facing word, the
registered-library section, fan-out + fan-in in Connections, the atomicity rule, and
the **debate** worked example. Focused purely on producing an OfficeSpeak description
(no running, no code, no runtime placement).

**Gallery (new format) — in progress (`start_gallery/`).**
- `trading_room.md` — DONE. Full build→explain→correct loop: Case 1 (fan-in / async
  merge, keeper serialized by single inbox + atomicity, no coordinator) → Pat's
  correction → Case 2 (adds a commanded `select` per trader). Mani revised the prose
  (reads well); fixed one orphaned `> to it.` fragment. Teaches: fan-in ≠ merge_synch,
  keeper serialization, the two ask-and-wait semantics, coordinator-added-on-correction,
  keeper vs registered record.

## Coverage so far (across debate + trading_room)

source, sink, transform, all three coordinators (merge_synch + gate in debate; select
in trading), fan-out, fan-in, keeper, feedback loop, non-obvious termination, a
transform choosing among outboxes. **Not yet shown:** an office that needs *no*
coordinator (restraint), and the registered `record` + `gate` pattern.

## Next gallery examples (recommended, in order)

1. **Restraint / per-key monitor** (anomaly-watch) — the counterweight to two
   coordination-heavy examples; teaches when to use *nothing*. Sketch: METRICS(source)
   → MONITOR(per-service stats) → DEDUPER(per-service) → DISPATCH(transform, several
   outboxes, routes by owner) → owner sinks + ALERTS file. No coordinator, no keeper,
   no record; per-key state inside transforms; routing = transform choosing an outbox.
   **Draft this first next session.**
2. **investment_club** — the one library pattern none of the examples exercises: a
   shared `record` read *and written* by several agents, protected by a `gate`. Pairs
   with (1) to complete "when do I need shared state, and when don't I."

Then: reconcile **debate** into the same new gallery format, and split old
`OfficeSpeak_gallery.md` (start-module gallery vs a separate code-gen gallery holding
the Python bodies/prompts). (Task #45.)

## Decisions parked for later

- **Generated determinate coordinators (escape hatch)** — `backlog_generated_coordinators.md`.
  Agreed in principle. Safe condition = conforms to the coordinator execution model
  (blocking read on a state-chosen inbox; never "whichever inbox is ready"; atomic;
  single-threaded; no randomness/clock/shared-memory). **Strongest footing:** if the
  runtime only ever exposes "wait on one named inbox" (no select/poll/timeout), a
  single-threaded generated agent *cannot* express fair-merge — determinism enforced by
  the receive API, not by trusting Claude. (Confirmed: with block-forever-on-one-queue
  as the only primitive, a single thread cannot wait for whichever-arrives-first; that's
  why MergeAsynch uses one thread per inbox.) Not yet folded into start_instructions.
- Pat-facing "what changed" in trading_room uses notation words (inbox/command);
  optional softening flagged, left as-is.

## Open tasks

- #44 Cold-test the start instructions (run a Pat description through v3 with a fresh
  instance; check clean Phase 1, a correction, clean Phase 2; test a judgment-worker
  office too).
- #45 Split & reformat the gallery to the new notation (restraint + investment_club +
  reconcile debate; separate code-gen gallery).

## Broader state (unchanged)

Tester kit built: `TESTER_MANUAL.md` (two tracks), `offices/debug_demo/` (computational
debugging worked example, verified). DisSysLab: Coordinator base + MergeSynch/Gate/Select
done; decision notes in `DisSysLab/docs/internals/`. Paper `draft_v2.md`:
"correct by construction" removed; replay-claim fix still pending (reframe as debug-mode
capability).
