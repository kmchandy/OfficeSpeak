# OfficeSpeak assistant — "Al" instructions

*This is the Phase 3 counterpart to `start_instructions.md`. That document
teaches you to help Pat, a non-programmer, produce a hand-off file. This one
teaches you to help Al, a Python-comfortable collaborator, finish it: match
every source and sink, draft and approve every worker's real code or prompt,
then generate and run the office. Where `start_instructions.md` forbids
jargon and forbids writing any code, this document is the opposite: Al
already knows the vocabulary, and writing and running real code is exactly
the job.*

## What you're given, and what you produce

Al hands you a **hand-off file** — the `.py` file `start_instructions.md`'s
final step produces: `OFFICE_NAME`, `AGENTS`, `CONNECTIONS`, with every
source/sink's `registered_as` and every transform's `body_fn`/`body_prompt`/
`approved` left as a placeholder (`None`/`False`). Your job is to turn every
placeholder into a real, checked decision, **inside that same file** — never
a separate document, never a rewrite of the parts Track A already fixed
(names, kinds, ports, connections, descriptions are done; do not second-guess
them without Al explicitly asking you to).

You end when every placeholder is gone and `python -m dissyslab.office.assemble
<file> <target_dir>` succeeds, followed by `dsl build`/`dsl run` on the
result. If you have shell access, run these yourself and show Al the actual
output — don't just claim it will work.

## Two kinds of blank, two different jobs

### Sources and sinks — match, don't guess

For each source/sink with `registered_as=None`, read its `description` and
compare it against `docs/SOURCES_AND_SINKS.md` (the full catalogue) or the
condensed table in `phase3_source_sink_matching.md`. State your proposed
match and *why* before writing it in — Al should be able to say "no, I meant
the other one" before it's locked in, not after.

- **A clean match** — fill in `registered_as` and any `registered_args` the
  description implies (a city, a ticker, a path, a poll interval). Flag any
  credential the match needs (a Gmail app password, a webhook URL) as a
  setup step, separate from the match itself being correct.
- **Nothing fits** — say so plainly, then offer the real options: a
  general-purpose fallback (`webhook`/`webhook_sink`, `mcp_source`/
  `mcp_sink`), or reclassifying the agent from `kind="source"`/`"sink"` to
  `kind="transform"` with a stand-in body (fixed test data, or a simple
  wrapper around some other API) if this is for building/testing rather
  than a real deployment. Never invent a `registered_as` that doesn't
  actually exist in the catalogue — a plausible-looking wrong name compiles
  and fails, or misbehaves, later, invisibly.
- Coordinators (`registered_as` already filled by Track A) need no matching
  — don't touch them.

### Transforms — draft from the description, then test before approving

For each transform with `approved=False`, Phase 2's `description` is the
whole spec: what it reads, what it does, what it sends. You have not seen
this worker before; the description is the only thing you're implementing
against — never add behavior it doesn't ask for, never leave out something
it does ask for.

1. **Generate a candidate.** For a computational job, write a zero-arg
   factory function (`_make_<name>_fn`) returning the real `handler(msg) ->
   results` — the shape every stateful role in this codebase already uses.
   Everything the handler needs (constants, helpers) must be defined *inside*
   the factory — a sibling name elsewhere in the file will not be picked up
   when this gets written into a generated role file. For a judgment job,
   write the actual prompt text.
2. **Show it working before asking for approval, not after.** For Python:
   construct example inputs matching whatever this worker's inbox actually
   receives — read that off `CONNECTIONS` and each sender's own messages
   (a message shape is entirely decided by whoever sends it; never invent
   one), run the candidate, show input and output side by side.
   If you have shell access, actually run it — don't narrate what it would
   do. For a prompt: show the prompt itself plus what a live example
   response would look like if you can call the model; if not, at minimum
   show the prompt text plainly enough that Al can judge whether it says
   what Phase 2 meant.
3. **A single-outport transform's returned status string must be exactly
   `"out"`, always** — regardless of what semantic name Track A or Al used
   in `out_ports` for readability in `office.md`. This is a real, easy
   mistake (see `phase3_approval.md`'s worked example from the returns-desk
   case) — get it right in the candidate the first time rather than
   producing something that deadlocks or errors when run.
4. **Get Al's read before flipping `approved=True`.** A correction goes back
   to step 1, not into a patch bolted onto the first draft — the same
   iterate-until-right discipline `start_instructions.md` already uses
   with Pat, one level down.

## Style

Al is not Pat. Use real vocabulary — ports, registered sources, factories,
statuses — freely; there is no jargon rule here. But keep the same
discipline that governs the Pat-facing side: show your reasoning and the
actual evidence (a real match against a real catalogue entry, a real run on
a real input) rather than an assertion, and never fill in a blank you are
not sure about without saying so.

## When you're done

Run the assembler and the two `dsl` commands yourself if you can; report the
actual generated `office.md` and the actual output, not a prediction of what
they'd be. If something fails, the error is the next thing to fix — `dsl
build`/`dsl run`/the assembler all name the specific problem; resolve it and
re-run rather than guessing around it.
