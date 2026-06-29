# NetworkOfThought (NoT)

A methodology and working system for using an LLM (Claude) to design and
build persistent multi-agent sense-and-respond applications from plain
English descriptions.

NetworkOfThought sits in the lineage of decomposition methodologies that
externalise LLM reasoning into structured intermediate forms:

- **Chain of Thought** (Wei et al., 2022) — decompose a problem into a
  sequence of reasoning steps in a single inference
- **Tree of Thoughts** (Yao et al., 2023) — decompose into a tree of
  alternative reasoning paths
- **Graph of Thoughts** (Besta et al., 2023) — decompose into a
  general graph of reasoning operations
- **Network of Thought** (this work, 2026) — decompose *system design*
  into a network of small, persistent, message-passing agents

The contribution: applying CoT-style decomposition reasoning to a new
domain — the design of running multi-agent systems rather than the
solution of single problems. The artifact Claude produces is not a
sequence of reasoning steps; it is an executable agent network that
runs continuously, ingests data, and emits outputs.

## What's in this repo

| Directory | What it contains |
|---|---|
| `BRAINSTORM.md` | Full reasoning trace of the design process (how we got here) |
| `DECISIONS.md` | Committed design decisions; ground truth for "what we're building" |
| `PLAN.md` | Phased work plan (Phase 1: LLM-only apps; Phase 2: Python-agent apps; Phase 3: gallery regeneration experiment) |
| `catalog/` | The translation table: pseudocode constructs → graph constructs |
| `examples/` | Walkthroughs showing how to decompose a task into pseudocode |
| `prompts/` | Versioned meta-prompts for Claudette |
| `claudette/` | The Python code: wrapper, parser, smoke tests, orchestrator |
| `outputs/` | Generated apps from experimental runs |
| `archive/` | Superseded artifacts from earlier iterations |

## Naming

- **NetworkOfThought (NoT)** is the methodology and the name of this
  repo.
- **Claudette** is the LLM agent that does the building — Claude with
  a fixed meta-prompt that specifies the design process.
- **DisSysLab (DSL)** is the underlying framework Claudette builds on:
  small message-passing agents with English contracts. DSL lives in a
  separate repo and is a dependency of this one.

## Status

This is research code, currently in Phase 1 (see PLAN.md). The full
pipeline (Pat's English description → Claudette → executable system)
is not yet end-to-end; we are building it piece by piece.

The end-state target: a single command takes a Pat-style English
description of a sense-and-respond app and produces a running
DisSysLab office. The methodology is what makes that possible; the
code in this repo is one instantiation.

## Setup

```bash
# Install DSL (the framework dependency) from local checkout
cd ~/Documents/DisSysLab && pip install -e .

# Install NetworkOfThought (this repo)
cd ~/Documents/NetworkOfThought && pip install -e .

# Sanity check: tests pass
python3 -m pytest claudette/tests/
```

## Reading order for new contributors

1. **README.md** (this file) — what NoT is
2. **DECISIONS.md** — what we've committed to
3. **PLAN.md** — what we're building, in what order
4. **examples/situation_room.md** — one complete walkthrough
5. **BRAINSTORM.md** — if you want to understand *why* we chose
   what we chose (long, but it shows the trajectory)

## Related repos

- **DisSysLab** (`~/Documents/DisSysLab/`) — the framework Claudette
  builds on. NetworkOfThought depends on it.
- **DisSysLab-Debate** (`~/Documents/DisSysLab-Debate/`) — historical
  artifact of an earlier (abandoned) research direction. Preserved
  for reference; not part of NetworkOfThought.

## License

(TBD — same as DSL)
