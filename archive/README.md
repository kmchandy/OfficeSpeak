# Archive

Historical material, kept for provenance and paper citations, not
current documentation. Nothing here reflects the framework as it exists
today — see the top-level `README.md`, `guides/`, and DisSysLab's own
`dissyslab/gallery/apps/` for what's actually current.

## offices/claude_project/

The claude.ai Project-based operating model (custom instructions,
Stage 1/2 matching-and-approval process, `cold_tests/` evaluation
transcripts). Superseded by working directly in Cowork sessions, which
is how every current gallery app (`mac_speed_suite`, `adaptive_tutor`,
`salton_sea_dashboard`) was actually built. `cold_tests/transcripts/`
still has value as evaluation evidence if the paper cites it — check
`paper/PAPER_NOTES.md` before assuming it's purely historical.

## offices/phase2_demo/

Pre-v1.6-API prototypes, predating the current `office.md`/`roles/`
framework. `tutor_multi.py` and its siblings (`tutor.py`, `tutor_llm.py`,
`tutor_interactive.py`) are superseded by
`DisSysLab/dissyslab/gallery/apps/adaptive_tutor/`, which ports the same
idea onto the current framework and formalizes the subject-extension
contract that this version never had. `room_monitor.py`, `triage_llm.py`,
`triage_swap.py`, `worker.py`, `harness*.py`, `llm_worker.py` are earlier,
more general prototyping of the same message-passing idea, superseded by
the current framework's own `dissyslab.blocks.role` machinery.

## offices/agents_demo/

Early single-file worker prototype (`sliding_window_stats.py`), predating
the current framework's role/office structure.

## offices/debug_demo/

Design exploration for isolated-worker debugging. Superseded by the real,
built version of that idea, documented in
`DisSysLab/docs/internals/debugging_aids_decision.md`.

## offices/deterministic_replay_design.md, prompt_*_explain.md

Pre-implementation design notes and prompt drafts for the
checkpoint/trace/debug-explain features. Superseded by the actual built
algorithms and docs in `DisSysLab/docs/algorithms/` (`CHECKPOINT_RESUME.md`,
`TRACE_AND_LOGICAL_CLOCK.md`) and the real `dsl explain-trace` /
`dsl show-checkpoint` CLI commands.

## examples/

Design-exploration and spec-review artifacts (`investment_club`,
`trading_desk`, `anomaly_monitor`, `support_desk`, `weather`,
`sanity_checks`, `debate.*`, `situation_room.*`) from before DisSysLab's
current gallery existed in its present form. Superseded by the real,
built, run-and-checked gallery apps in `DisSysLab/dissyslab/gallery/apps/`
(33 offices as of the last `FEATURES.md` snapshot) — see
`guides/gallery_overview.md` for a browsable index of those. `example_prompts/`
is example-prompt output history (moved here from a since-removed
`officespeak/smoke_test_outputs/` per an earlier decision), not a design
draft, but grouped here for the same reason: not current documentation.
