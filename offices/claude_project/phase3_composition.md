# OfficeSpeak "Phase 3" — composing offices (departments)

*Sibling to `phase3_al_howto.md`, `phase3_approval.md`, and
`phase3_source_sink_matching.md`. Those cover building one office from a
Stage 1 hand-off file. This one is about reusing a whole other office,
already built and tested, as a single worker inside a new one. Pat never
sees any of this — composition is entirely Al's decision, made while
turning a Phase 2 description into a running office, not something Track A
ever asks about or names.*

*Assumes Al is a real programmer, comfortable with Python and the command
line — unlike `phase3_al_howto.md`, this doesn't walk through every step
from scratch.*

## The concept: a department is a worker whose insides are another office

DisSysLab already supports nesting one office inside another — arbitrary
port counts, arbitrary nesting depth, the same office reused twice in one
parent, all already built and working (`docs/recipes/chain-offices.md` if
you want the DisSysLab-side story). What was missing was a way for
OfficeSpeak's Stage 1 → Stage 2 hand-off file to express it. That's what
`kind="department"` is.

A department shares its *shape* with a coordinator — a name, a list of
named in/out ports, no body — because both are multi-port workers whose
own internal logic isn't written here. But they're a different *kind* on
purpose: a coordinator (`merge_synch`/`select`/`gate`/`record`) is one of
DisSysLab's small set of trusted, registered primitives with fixed,
eventually-formally-specified behavior. A department is just whatever
office is at the path you point it at — arbitrary content someone (maybe
you) wrote and tested, not a proven primitive. Nothing in the framework
vouches for what a department actually does; that's on whoever tested it
before turning it into one.

Reuse only, for now: there's no way to pass a parameter into a department
(no "same office, different threshold") — if the existing office doesn't
do quite the right thing, the options are use it as-is or build a fresh
one, not tweak it. And there's no registry or matching step for finding a
reusable office — you find one the same way you'd find anything else
you've built: look at the gallery, or at whatever else you've made.

## Step 1 — build and test the office closed, like any other office

Nothing changes here. Build the office the normal way
(`phase3_al_howto.md`), with real (or stand-in) sources and sinks, and test
it end to end — feed it realistic input, check what it actually writes
out. This is the *only* testing a department gets. Once you open a port up
in step 2, there's no separate re-verification step and no test harness for
the opened version — the trust comes entirely from having tested it while
it was still closed, the same one-time-approval discipline
`phase3_approval.md` already uses per-worker, just applied to the whole
office.

If a source doesn't have a real feed yet (or won't, because it's about to
become someone else's input), stand in for it exactly the way
`phase3_al_howto.md` already teaches: reclassify it as a `transform` fed by
the registered `starter` source, with a small fixed sequence of realistic
values. Test against that. When you open the port up in step 2, that
stand-in transform is exactly what gets deleted — so make sure the test
data it produces is realistic enough that passing the test actually means
something.

## Step 2 — open it up

Take the tested, closed hand-off file and, for each source or sink you
want to turn into a boundary:

1. Delete that agent's dict from `AGENTS` entirely (and, if it was a
   stand-in transform per step 1, delete its factory function too).
2. Add a new top-level list — `INPUTS = [...]` for a source becoming a
   boundary input, `OUTPUTS = [...]` for a sink becoming a boundary
   output — naming it whatever you want the outside world to call it.
3. Rewrite every `CONNECTIONS` tuple that mentioned the deleted agent to
   use the reserved name `"external"` instead, with the port set to the
   name you just declared in `INPUTS`/`OUTPUTS`.

This only ever touches source and sink agents — never a transform or
coordinator's own logic, which stays exactly as tested. `assemble.py`
checks that every `"external"` port used in `CONNECTIONS` was actually
declared in `INPUTS`/`OUTPUTS`, and raises immediately, naming the missing
one, if not.

Run `python -m dissyslab.office.assemble` on it as usual. The generated
`office.md` will have `Inputs:`/`Outputs:` lines instead of the deleted
`Sources:`/`Sinks:` entries — that's the DisSysLab-native way of saying
"this office is open." There's nothing to run standalone at this point (an
open office has no source or sink of its own to drive it) — it's ready to
be referenced from a parent.

## Step 3 — plug it into a new office as a department

In the *new* hand-off file's `AGENTS` list, add an entry with
`kind="department"`, the department's `in_ports`/`out_ports` set to
exactly the names its `INPUTS`/`OUTPUTS` declared, and `office_path`
pointing at where it lives, relative to wherever this new office's own
`assemble.py` output will end up (the same relative-path convention any
`office at <path>` reference in `office.md` already uses).

```python
dict(name="ADDER_DEPT", kind="department",
     in_ports=["a_in", "b_in"], out_ports=["sum_out"],
     office_path="../adder_department"),
```

Wire `CONNECTIONS` to it exactly like any other multi-port agent — a
department's ports are real, named ports, not the forced `in_`/`out` a
single-port transform gets. `assemble.py` requires `office_path` to be
set (raises immediately, naming the agent, if it's still blank) and
otherwise leaves a department's ports untouched.

## Worked example, real and tested

A closed office, tested standalone first:

```python
# increment_closed.officespeak.py
AGENTS = [
    dict(name="STARTER", kind="source", in_ports=[], out_ports=["out"],
         registered_as="starter", registered_args={}),
    dict(name="NUMS", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Stand-in test stream of numbers.",
         body_kind="python", body_fn=_make_nums_fn, body_prompt=None, approved=True),
    dict(name="INCREMENTER", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Add 1 to the incoming number.",
         body_kind="python", body_fn=_make_incrementer_fn, body_prompt=None, approved=True),
    dict(name="PRINTER", kind="sink", in_ports=["in"], out_ports=[],
         registered_as="console_printer", registered_args={}),
]
CONNECTIONS = [
    ("STARTER", "out", "NUMS", "in"),
    ("NUMS", "out", "INCREMENTER", "in"),
    ("INCREMENTER", "out", "PRINTER", "in"),
]
```

Built and run standalone: input `[1, 2, 3, 4]` → printed `[2, 3, 4, 5]`.
Confirmed correct before touching anything.

Opened up — `STARTER` and `NUMS` (the test-stand-in pair) and `PRINTER`
deleted, `INCREMENTER` now wired straight to the boundary:

```python
# increment_department.officespeak.py
INPUTS = ["number_in"]
OUTPUTS = ["incremented_out"]
AGENTS = [
    dict(name="INCREMENTER", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Add 1 to the incoming number.",
         body_kind="python", body_fn=_make_incrementer_fn, body_prompt=None, approved=True),
]
CONNECTIONS = [
    ("external", "number_in", "INCREMENTER", "in"),
    ("INCREMENTER", "out", "external", "incremented_out"),
]
```

Generated `office.md`:

```
# Office: increment_department

Inputs: number_in
Outputs: incremented_out

Agents:
INCREMENTER is an incrementer.

Connections:
number_in's destination is INCREMENTER.
INCREMENTER's out is incremented_out.
```

A new parent office, plugging it in as a department alongside its own
source and sink:

```python
# parent_office.officespeak.py
AGENTS = [
    dict(name="STARTER", kind="source", in_ports=[], out_ports=["out"],
         registered_as="starter", registered_args={}),
    dict(name="NUMS", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Stand-in test stream of numbers.",
         body_kind="python", body_fn=_make_nums_fn, body_prompt=None, approved=True),
    dict(name="INCREMENTER_DEPT", kind="department",
         in_ports=["number_in"], out_ports=["incremented_out"],
         office_path="../increment_department"),
    dict(name="PRINTER", kind="sink", in_ports=["in"], out_ports=[],
         registered_as="console_printer", registered_args={}),
]
CONNECTIONS = [
    ("STARTER", "out", "NUMS", "in"),
    ("NUMS", "out", "INCREMENTER_DEPT", "number_in"),
    ("INCREMENTER_DEPT", "incremented_out", "PRINTER", "in"),
]
```

`python -m dissyslab.office.assemble parent_office.officespeak.py
parent_office/`, then `dsl build .` and `dsl run .` from inside it — real
output, the parent's own stream of `[10, 20, 30]` run through the
department:

```
[1] {'n': 11}
[2] {'n': 21}
[3] {'n': 31}
```

Multi-port departments work the same way — tested separately with a
two-input department (`a_in`/`b_in` merged by a `merge_synch` inside it,
declared `Outputs: sum_out`), plugged into a parent with two independent
stand-in streams: the parent's `[1,2,3]` and `[100,200,300]` streams
matched up correctly through the department's own internal join, printing
`{'a': 1, 'b': 100}`, `{'a': 2, 'b': 200}`, `{'a': 3, 'b': 300}`. A
department's ports are exactly as multi-valued as a coordinator's.

## What's not here

No parameterization (see above — reuse only, exactly as tested). No
catalog or matching step for finding a reusable office (look at the
gallery and whatever else you've built). No change to Pat's Stage 1
conversation at all — she describes a worker the same way regardless of
whether Al later implements it as Python, a prompt, or a department.
