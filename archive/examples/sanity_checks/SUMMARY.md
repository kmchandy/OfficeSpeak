# Sanity-check test cases — Phase 1 Step 4b

Five Pat-style English descriptions, each with an expected pseudocode
that the meta-prompt (`prompts/meta_prompt_v1.md`) is intended to
elicit from Claudette.

| # | Spec | Pattern | Status |
|---|---|---|---|
| 01 | weather_alert | Pipeline + binary router with else | ✅ end-to-end OK |
| 02 | arxiv_summary | Multi-source merge + minimal pipeline | ✅ end-to-end OK |
| 03 | inbox_triage | Three-way equality router | ✅ end-to-end OK |
| 04 | debate | Feedback loop with explicit iter counter | ✅ end-to-end OK |
| 05 | ambiguous | Should produce `# ERROR:` line | (no pipeline run; expected behavior is to error) |

"End-to-end OK" means:
1. The expected pseudocode parses cleanly through `claudette/parser.py`.
2. The resulting graph renders to office.md through `claudette/office_writer.py`.
3. The office.md is accepted by DSL's real `parse_office_dir` parser.

## How to use these once an API key is available

When you run Claudette with `prompts/meta_prompt_v1.md`:

1. Feed the meta-prompt as system message.
2. Feed the contents of `NN_<name>.spec.md` (the Pat-style English) as user message.
3. Take Claudette's output (which should be a fenced pseudocode block).
4. Compare it to `NN_<name>.expected.pseudo`.

The comparison can be exact-match (strict) or by structural
equivalence (run both through the parser and compare graph dicts).
Structural is more forgiving and probably what you want — Claudette
may pick different but equivalent variable names, role descriptions,
or whitespace.

## Run the sanity check yourself

From the repo root:

```bash
python3 examples/sanity_checks/run_sanity.py
```

This re-parses each `expected.pseudo`, regenerates `graph.yaml` and
`office.md`, and verifies DSL acceptance. Should print
`4/4 cases passed`.

## What was discovered while building these cases

Two real issues surfaced and were fixed:

1. **Parser bug:** the parser rejected bare-identifier sources like
   `problems: starter` (no parens). DSL allows the bare form for
   no-arg sources. Fix: parser now accepts both `starter` and
   `starter()` in input bindings.

2. **DSL constraint:** sink registry names must be unique within an
   office. Two `jsonl_recorder` sinks with different paths is not
   legal in DSL. The gallery convention uses suffixed names
   (`jsonl_recorder_archive`, `jsonl_recorder_discard`, etc.) for
   different purposes. Fix: added an explicit guard in the
   meta-prompt's failure-modes section warning Claudette not to
   reuse a sink registry name.

Both fixes are committed in the parser and meta-prompt as of this
session.

## Open observation for the next iteration

These five cases all use **flat** structures (one for-each, optional
single if/elif/else, no nested anything). The current grammar can
also describe more complex things (e.g., a fan-out where the unconditional
send-to goes to two different sinks). It might be worth adding one or
two more cases that exercise:

- Sources with no params at all (`console_input` only).
- Sinks that need no arguments stacked alongside ones with arguments.
- A pipeline of 5+ enrichers (test that role-name derivation holds
  up across a longer chain).

But the four passing cases give us reasonable initial coverage of the
three primitives (sequence, branch, send-to), and they exercise
real-world DSL sources and sinks.
