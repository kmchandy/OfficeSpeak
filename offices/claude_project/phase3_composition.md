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
from scratch. It does walk through one realistic case start to finish,
with real commands and real output, the same way `phase3_al_howto.md`
does for a single office.*

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

## Why bother — the payoff in one sentence

Build and test a piece of logic exactly once; reuse it, unmodified, in as
many offices as need it. The walkthrough below builds one signal-checking
department and plugs it, unmodified, into two different monitoring
offices — that's the whole point, made concrete.

## Walkthrough: one signal check, reused across two monitoring offices

The scenario: Al is helping build monitoring offices for a couple of
different instruments. Each one watches a price feed and a moving-average
feed, and needs to decide `"buy"`, `"sell"`, or `"hold"` by comparing the
two — price more than 2% above the average is a buy signal, more than 2%
below is a sell signal, otherwise hold. That comparison logic is exactly
the same no matter which instrument it's watching. Rather than write and
test it twice, Al builds it once as a department and plugs it into both.

### Step 1 — build the signal check as its own closed office, and test it

Before it's reusable, it has to exist and be provably correct on its own.
Al writes it as an ordinary, closed office first — a stand-in source
feeding it a fixed sequence of test prices and averages (exactly the
`starter`-fed-transform technique `phase3_al_howto.md` already teaches),
and a `console_printer` sink so the output is easy to check by eye:

```python
# signal_closed.officespeak.py
OFFICE_NAME = "signal_closed"

def _make_price_feed_fn():
    _VALUES = [105.0, 95.0, 100.0]
    def price_feed_fn(msg):
        return [({"price": v}, "out") for v in _VALUES]
    return price_feed_fn

def _make_average_feed_fn():
    _VALUES = [100.0, 100.0, 100.0]
    def average_feed_fn(msg):
        return [({"average": v}, "out") for v in _VALUES]
    return average_feed_fn

def _make_signal_fn():
    def signal_fn(msg):
        price = msg["price"]
        average = msg["average"]
        if price > average * 1.02:
            signal = "buy"
        elif price < average * 0.98:
            signal = "sell"
        else:
            signal = "hold"
        return [({"price": price, "average": average, "signal": signal}, "out")]
    return signal_fn

AGENTS = [
    dict(name="STARTER", kind="source", in_ports=[], out_ports=["out"],
         registered_as="starter", registered_args={}),
    dict(name="PRICE_FEED", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Stand-in test stream of prices.",
         body_kind="python", body_fn=_make_price_feed_fn, body_prompt=None, approved=True),
    dict(name="AVERAGE_FEED", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Stand-in test stream of recent moving averages.",
         body_kind="python", body_fn=_make_average_feed_fn, body_prompt=None, approved=True),
    dict(name="JOIN", kind="coordinator", in_ports=["price", "average"], out_ports=["out"],
         registered_as="merge_synch", registered_args={}),
    dict(name="SIGNAL", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Compare price to average; emit buy/sell/hold.",
         body_kind="python", body_fn=_make_signal_fn, body_prompt=None, approved=True),
    dict(name="PRINTER", kind="sink", in_ports=["in"], out_ports=[],
         description="Print the signal.",
         registered_as="console_printer", registered_args={}),
]

CONNECTIONS = [
    ("STARTER", "out", "PRICE_FEED", "in"),
    ("STARTER", "out", "AVERAGE_FEED", "in"),
    ("PRICE_FEED", "out", "JOIN", "price"),
    ("AVERAGE_FEED", "out", "JOIN", "average"),
    ("JOIN", "out", "SIGNAL", "in"),
    ("SIGNAL", "out", "PRINTER", "in"),
]
```

Note the field names into `JOIN`: `"price"`/`"average"`, not both `"value"`
— the same merge_synch discipline `phase3_al_howto.md` covers, so the two
readings combine into one message instead of colliding.

Assemble, build, run:

```bash
python -m dissyslab.office.assemble signal_closed.officespeak.py signal_closed/
cd signal_closed
dsl build .
dsl run .
```

Real output, this exact case:

```
[1] {'price': 105.0, 'average': 100.0, 'signal': 'buy'}
[2] {'price': 95.0, 'average': 100.0, 'signal': 'sell'}
[3] {'price': 100.0, 'average': 100.0, 'signal': 'hold'}
```

All three branches of the logic exercised, all three correct. This is the
*only* testing this logic will ever get — once it's a department, there's
no separate re-verification step. Trust it now, or don't turn it into a
department yet.

### Step 2 — open it up

The stand-in pieces (`STARTER`, `PRICE_FEED`, `AVERAGE_FEED`) and the sink
(`PRINTER`) are deleted — those are exactly what a *parent* office will
supply instead. `JOIN` and `SIGNAL`, the logic that was just tested, are
untouched. Two new top-level lists declare the boundary, and the affected
`CONNECTIONS` entries switch to the reserved name `"external"`:

```python
# signal_department.officespeak.py
OFFICE_NAME = "signal_department"

INPUTS = ["price_in", "average_in"]
OUTPUTS = ["signal_out"]

def _make_signal_fn():
    def signal_fn(msg):
        price = msg["price"]
        average = msg["average"]
        if price > average * 1.02:
            signal = "buy"
        elif price < average * 0.98:
            signal = "sell"
        else:
            signal = "hold"
        return [({"price": price, "average": average, "signal": signal}, "out")]
    return signal_fn

AGENTS = [
    dict(name="JOIN", kind="coordinator", in_ports=["price", "average"], out_ports=["out"],
         registered_as="merge_synch", registered_args={}),
    dict(name="SIGNAL", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Compare price to average; emit buy/sell/hold.",
         body_kind="python", body_fn=_make_signal_fn, body_prompt=None, approved=True),
]

CONNECTIONS = [
    ("external", "price_in", "JOIN", "price"),
    ("external", "average_in", "JOIN", "average"),
    ("JOIN", "out", "SIGNAL", "in"),
    ("SIGNAL", "out", "external", "signal_out"),
]
```

`python -m dissyslab.office.assemble signal_department.officespeak.py
signal_department/` — real, generated `office.md`:

```
# Office: signal_department

Inputs: price_in, average_in
Outputs: signal_out

Agents:
JOIN is a synchronizer(inports=['price', 'average']).
SIGNAL is a signal.

Connections:
price_in's destination is JOIN's price.
average_in's destination is JOIN's average.
JOIN's out is SIGNAL.
SIGNAL's out is signal_out.
```

`Inputs:`/`Outputs:` instead of `Sources:`/`Sinks:` is DisSysLab's own way
of saying "this office is open." There's nothing to run standalone here —
an open office has no source or sink of its own to drive it — it's ready
to be referenced from a parent.

### Step 3 — plug it into two different parent offices, unmodified

First parent — a monitoring office for one instrument, its own stand-in
price/average feeds, `signal_department` reused as a single worker:

```python
# aapl_monitor.officespeak.py
OFFICE_NAME = "aapl_monitor"

def _make_price_fn():
    _VALUES = [231.0, 228.0]
    def price_fn(msg):
        return [({"price": v}, "out") for v in _VALUES]
    return price_fn

def _make_average_fn():
    _VALUES = [225.0, 225.0]
    def average_fn(msg):
        return [({"average": v}, "out") for v in _VALUES]
    return average_fn

AGENTS = [
    dict(name="STARTER", kind="source", in_ports=[], out_ports=["out"],
         registered_as="starter", registered_args={}),
    dict(name="AAPL_PRICE", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Stand-in AAPL price feed.",
         body_kind="python", body_fn=_make_price_fn, body_prompt=None, approved=True),
    dict(name="AAPL_AVERAGE", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Stand-in AAPL moving-average feed.",
         body_kind="python", body_fn=_make_average_fn, body_prompt=None, approved=True),
    dict(name="AAPL_SIGNAL_DEPT", kind="department",
         in_ports=["price_in", "average_in"], out_ports=["signal_out"],
         office_path="../signal_department"),
    dict(name="PRINTER", kind="sink", in_ports=["in"], out_ports=[],
         description="Print AAPL's signal.",
         registered_as="console_printer", registered_args={}),
]

CONNECTIONS = [
    ("STARTER", "out", "AAPL_PRICE", "in"),
    ("STARTER", "out", "AAPL_AVERAGE", "in"),
    ("AAPL_PRICE", "out", "AAPL_SIGNAL_DEPT", "price_in"),
    ("AAPL_AVERAGE", "out", "AAPL_SIGNAL_DEPT", "average_in"),
    ("AAPL_SIGNAL_DEPT", "signal_out", "PRINTER", "in"),
]
```

Second parent — a different instrument, different feed values, same
department, byte-for-byte unmodified (only `office_path` needs to point at
it, the same `"../signal_department"` for both since they're siblings):

```python
# tsla_monitor.officespeak.py
OFFICE_NAME = "tsla_monitor"

def _make_price_fn():
    _VALUES = [240.0, 265.0]
    def price_fn(msg):
        return [({"price": v}, "out") for v in _VALUES]
    return price_fn

def _make_average_fn():
    _VALUES = [250.0, 250.0]
    def average_fn(msg):
        return [({"average": v}, "out") for v in _VALUES]
    return average_fn

AGENTS = [
    dict(name="STARTER", kind="source", in_ports=[], out_ports=["out"],
         registered_as="starter", registered_args={}),
    dict(name="TSLA_PRICE", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Stand-in TSLA price feed.",
         body_kind="python", body_fn=_make_price_fn, body_prompt=None, approved=True),
    dict(name="TSLA_AVERAGE", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Stand-in TSLA moving-average feed.",
         body_kind="python", body_fn=_make_average_fn, body_prompt=None, approved=True),
    dict(name="TSLA_SIGNAL_DEPT", kind="department",
         in_ports=["price_in", "average_in"], out_ports=["signal_out"],
         office_path="../signal_department"),
    dict(name="PRINTER", kind="sink", in_ports=["in"], out_ports=[],
         description="Print TSLA's signal.",
         registered_as="console_printer", registered_args={}),
]

CONNECTIONS = [
    ("STARTER", "out", "TSLA_PRICE", "in"),
    ("STARTER", "out", "TSLA_AVERAGE", "in"),
    ("TSLA_PRICE", "out", "TSLA_SIGNAL_DEPT", "price_in"),
    ("TSLA_AVERAGE", "out", "TSLA_SIGNAL_DEPT", "average_in"),
    ("TSLA_SIGNAL_DEPT", "signal_out", "PRINTER", "in"),
]
```

Assemble, build, and run each — same three commands as any other office,
`signal_department` itself never touched again:

```bash
python -m dissyslab.office.assemble aapl_monitor.officespeak.py aapl_monitor/
cd aapl_monitor && dsl build . && dsl run .
```

```
[1] {'price': 231.0, 'average': 225.0, 'signal': 'buy'}
[2] {'price': 228.0, 'average': 225.0, 'signal': 'hold'}
```

```bash
python -m dissyslab.office.assemble tsla_monitor.officespeak.py tsla_monitor/
cd tsla_monitor && dsl build . && dsl run .
```

```
[1] {'price': 240.0, 'average': 250.0, 'signal': 'sell'}
[2] {'price': 265.0, 'average': 250.0, 'signal': 'buy'}
```

Both correct — AAPL's price sitting above its average by more than 2%
correctly reads `buy`, TSLA's first reading well below average reads
`sell`, its second reading well above reads `buy`. The comparison logic
that produced all four of these signals is the exact same tested code from
step 1, never re-examined, never re-approved, plugged into two offices
that otherwise have nothing to do with each other. That's the payoff:
decompose real work into small, individually tested, individually approved
pieces, and each piece pays for its own testing cost only once.

## The recipe, in general

The walkthrough above is one instance of a fixed three-step pattern:

1. **Build and test it closed**, exactly like any other office
   (`phase3_al_howto.md`) — real (or stand-in) sources and sinks, real
   input, output checked by eye. This is the only testing a department
   ever gets; there's no re-verification once it's opened up, the same
   one-time-approval discipline `phase3_approval.md` already uses
   per-worker, just applied to a whole office.
2. **Open it up** — for each source/sink becoming a boundary: delete its
   `AGENTS` entry (and its stand-in factory function, if it had one), add
   it to a new `INPUTS = [...]` or `OUTPUTS = [...]` list, and rewrite the
   `CONNECTIONS` tuples that mentioned it to use the reserved name
   `"external"` instead. This only ever touches source/sink agents — never
   a transform or coordinator's logic, which stays exactly as tested.
   `assemble.py` checks every `"external"` port was actually declared, and
   raises immediately, naming the missing one, if not.
3. **Plug it in** — in the new parent's `AGENTS` list, add
   `kind="department"`, `in_ports`/`out_ports` matching exactly what the
   department declared as `INPUTS`/`OUTPUTS`, and `office_path` pointing at
   where it lives (relative to where the parent's own `assemble.py` output
   will end up — the same relative-path convention any `office at <path>`
   reference in `office.md` already uses). Wire `CONNECTIONS` to it like
   any other multi-port agent. `assemble.py` requires `office_path` to be
   set — raises immediately, naming the agent, if it's still blank.

## Smallest possible case, for quick reference

If the signal-check walkthrough above is more than you need to see the
mechanics, here's the same three steps at their most minimal — a
single-port department that just adds 1, and its two-input counterpart.

Closed and tested standalone (input `[1, 2, 3, 4]` → printed
`[2, 3, 4, 5]`):

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

Opened up (`STARTER`/`NUMS`/`PRINTER` deleted, `INCREMENTER` wired to the
boundary):

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

Plugged into a parent alongside its own source and sink; real output, the
parent's own stream of `[10, 20, 30]` run through the department:

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

```
[1] {'n': 11}
[2] {'n': 21}
[3] {'n': 31}
```

Multi-port departments work the same way as `signal_department` above —
also confirmed separately with a two-input department (`a_in`/`b_in`
merged by a `merge_synch` inside it, declared `Outputs: sum_out`), plugged
into a parent with two independent stand-in streams: the parent's
`[1,2,3]` and `[100,200,300]` streams matched up correctly through the
department's own internal join, printing `{'a': 1, 'b': 100}`,
`{'a': 2, 'b': 200}`, `{'a': 3, 'b': 300}`. A department's ports are
exactly as multi-valued as a coordinator's.

## What's not here

No parameterization (see above — reuse only, exactly as tested). No
catalog or matching step for finding a reusable office (look at the
gallery and whatever else you've built). No change to Pat's Stage 1
conversation at all — she describes a worker the same way regardless of
whether Al later implements it as Python, a prompt, or a department.
