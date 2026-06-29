# Migration note (2026-06-28)

This repository was migrated out of
`DisSysLab-Debate/experiments/adaptive_dsl/` on 2026-06-28.

## Why we moved

The work outgrew its old home:

1. **The debate research direction was abandoned.** Forced
   advocacy (debate) lost to self-consistency at matched compute
   in the stage-1 sanity check. We're not pursuing it further.
2. **The remaining work is about something different.** Building
   Claudette (an LLM agent that constructs DSL sense-and-respond
   systems from English descriptions) deserves its own repo and
   its own framing.
3. **The old name was wrong.** "adaptive_dsl" was a temporary
   working title for the debate-era experiments. The current
   research is **Network of Thought (NoT)** — a CoT-style
   decomposition methodology for system design.

## What moved

Everything under
`DisSysLab-Debate/experiments/adaptive_dsl/` was reorganised
into a flatter layout:

| Old | New |
|---|---|
| `experiments/adaptive_dsl/BRAINSTORM.md` | `BRAINSTORM.md` |
| `experiments/adaptive_dsl/DECISIONS.md` | `DECISIONS.md` |
| `experiments/adaptive_dsl/PLAN.md` | `PLAN.md` |
| `experiments/adaptive_dsl/claudette/` | `claudette/` |
| `experiments/adaptive_dsl/examples_for_claudette/` | `examples/` |
| `experiments/adaptive_dsl/example_library/INDEX.yaml` | `archive/old_example_library_INDEX.yaml` |
| `experiments/adaptive_dsl/example_library/README.md` | `archive/old_example_library_README.md` |

The catalog/, prompts/, and outputs/ directories were created
fresh (empty) for the Phase 1 work described in PLAN.md.

## What stayed behind

The debate-era work — the panellist roles, the moderator, the
gate, the debate display sink — stays in `DisSysLab-Debate/`
as a historical record. It is not part of NetworkOfThought.

## Path references

Doc references inside the moved files have been updated:
- `experiments/adaptive_dsl/catalog/...` → `catalog/...`
- `experiments/adaptive_dsl/claudette/...` → `claudette/...`
- `experiments/adaptive_dsl/examples/...` → `NetworkOfThought/examples/...`

If you find a stale reference, please update it.
