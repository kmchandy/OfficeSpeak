# Exactly what Cowork needs to help Pat build a DSL app

Cowork is the host. The only addition is the **DSL plugin**. Everything else is
Cowork's native power.

## Cowork provides natively (build nothing)

- Plain-English conversation.
- Read / write / edit files in Pat's folder.
- A sandbox to `pip install` and run Python.
- Mermaid diagram rendering.
- Scheduled tasks (for the periodic office).
- File presentation / live artifacts.

## The DSL plugin = six items

| # | Item | What it is | Status |
|---|------|------------|--------|
| 1 | **DSL library** (pip) | trusted coordination primitives, runtime, termination detection (works with loops), checkpoints, LLM-agent wrapper | exists |
| 2 | **onboard skill** | prompt: Pat's request -> five-section spec | exists (`prompt_onboard.md`) |
| 3 | **build skill** | (a) spec -> graph (existing graph-producer); (b) graph -> DSL code (trivial existing mapping); (c) generate each worker's LLM-prompt body from its job description | exists / thin glue |
| 4 | **explain skill** | prompt: graph -> plain English + Mermaid diagram | exists (`prompt_explain.md` + `graph_viz`) |
| 5 | **source/sink registry** | named sources/sinks with **mock/replay** backends for the examples (batched market feed, club-decisions input, RECOMMEND file) | small gap (demo mocks) |
| 6 | **runtime model access** | the running office is a separate process; its LLM workers each call a model per period, so that process needs a model credential | config (the one real operational requirement) |

## Net new work

Only three things are not already done:
- **Package** items 1-4 as a Cowork plugin (skills + library dependency).
- **Add demo mock sources/sinks** (item 5) so the example inputs/outputs resolve
  and the office runs end-to-end.
- **Wire runtime model access** for the office process (item 6), distinct from
  Cowork's own model access.

## Notes / scope

- The office's workers may use **different LLMs** (heterogeneous office) — a small
  step, since each body is an independent model call.
- For the paper/demo, the office runs in Cowork's sandbox on mock/replay inputs; a
  persistent long-running deployment (on Pat's machine or a server) is a separate,
  later concern.
- spec->graph is an LLM step Claude does in conversation; graph->code is
  deterministic; worker bodies are LLM steps. Cowork does the LLM steps as part of
  its conversation and runs the deterministic codegen as a script.
