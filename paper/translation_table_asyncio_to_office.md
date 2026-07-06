# Translation table: asyncio Python → office.md

**Status:** first draft. Table of patterns we recognise; gaps will surface the library agents we still need.

**Scope.** Maps OfficeSpeak-style asyncio Python (Run 2 style) to office.md
elements plus a library of standard concurrency agents. The translator is a
pattern-matching walk over the AST guided by this table; anything not covered
is a gap.

**Theoretical grounding.** Composition of the resulting office is supported
by the compositional proof theory of communicating processes (Misra &
Chandy, "Proofs of Networks of Processes," *IEEE Software Engineering*,
July 1981). Not user-facing; establishes correctness of composition.

---

## Section 1 — Structural patterns (module-level declarations)

### 1.1 Sources dictionary

**Python idiom.**

```python
SOURCES = {
    "bbc":    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "npr":    "https://feeds.npr.org/1004/rss.xml",
    "al_jaz": "https://www.aljazeera.com/xml/rss/all.xml",
}
```

Or with function-call syntax:
```python
SOURCES = {
    "temperature": clock_source(interval_seconds=30),
    "twitter":     bluesky_stream(query="python"),
}
```

**Graph fragment.** One source node per dict entry. Name from the dict key
(optional; can also come from the source-registry name). Params from the
call args or the URL string.

**Library agent.** None — sources are handled by the substrate.

**Notes.** The RHS may be a string (URL), a function call (with args), or a
factory expression. The translator inspects the AST of the RHS to pick a
registered source kind (rss, clock, mic, gmail, webhook, etc.). If the RHS
does not match a registered source kind → gap.

### 1.2 Top-level LLM-driven agent

**Python idiom.**

```python
async def classify_severity(message):
    """Classify how serious a news article is: low, medium, high, or critical."""
    ...
    return {"severity": ..., "severity_reason": ...}
```

**Graph fragment.**

```
vertex:
  id: v_<name>
  role: <function name>
  kind: llm
  role_prompt: <docstring>
  enriches: <keys of returned dict>
```

**Library agent.** None — this is a user-defined agent. Its prompt is the
docstring; its wrapper is the DSL LLM agent wrapper.

**Notes.** The function must (a) be `async`, (b) take exactly one parameter
`message`, (c) return a dict. Anything else → gap.

### 1.3 Top-level stateful Python agent (class form)

**Python idiom.**

```python
class SeverityTally:
    """Counts how many briefings fall into each severity bucket across a run."""
    def __init__(self):
        self.counts = {"low": 0, "medium": 0, "high": 0, "critical": 0, "unknown": 0}
    def process(self, message):
        sev = message.get("severity", "unknown")
        if sev not in self.counts:
            sev = "unknown"
        self.counts[sev] += 1
        return message
```

**Graph fragment.**

```
vertex:
  id: v_<lowered class name>
  role: <lowered class name>
  kind: python_stateful
  class_source: <the class body verbatim>
  role_prompt: <docstring>
```

**Library agent.** None — this is a user-defined stateful agent. DSL wraps
it via the class contract (`__init__` for state, `process(msg)` for the
per-message transform).

**Notes.** Class must have (a) `__init__` that takes no non-default args,
(b) `process(self, message)` that takes exactly one message and returns
one message. If the process is not defined or requires more args → gap.

---

## Section 2 — Data-flow patterns (inside `process_one` or `main`)

### 2.1 Sequential enrichment

**Python idiom.**

```python
async def process_one(message):
    message["severity"] = await classify_severity(message)
    message["location"] = await identify_location(message)
    ...
```

**Graph fragment.** Linear chain: previous vertex → next vertex.

```
v_classify_severity.out → v_identify_location.in
```

**Library agent.** None.

### 2.2 Parallel enrichment with convergence (asyncio.gather)

**Python idiom.**

```python
severity, location, briefing = await asyncio.gather(
    classify_severity(message),
    identify_location(message),
    write_briefing(message),
)
enriched = {**message, **severity, **location, **briefing}
```

**Graph fragment.** Broadcast from upstream to each function; each function's
output goes to a named inport of a synthesized `merge_sync`; `merge_sync`
emits one merged message.

```
upstream.out → v_classify_severity.in
upstream.out → v_identify_location.in
upstream.out → v_write_briefing.in

v_classify_severity.out → merge_sync.severity
v_identify_location.out → merge_sync.location
v_write_briefing.out    → merge_sync.briefing

merge_sync.out → downstream
```

**Library agent.** ✅ **`merge_sync`** (called `synchronizer` in DSL).
Waits for one message on each of N named inports; emits one merged output.
Inport names taken from the tuple assignment left-hand side or the returned
dict field names.

**Notes.** The three functions must be top-level agents; the same `message`
must be passed to each; the results must be merged into a single dict. If
the results are used separately without merging → gap (this is
fan-out-to-different-sinks, not converge).

### 2.3 Broadcast without convergence (fan-out to distinct sinks)

**Python idiom.**

```python
async def process_one(message):
    scored = await score_relevance(message)
    send_to(scored, "slack")
    send_to(scored, "jsonl")
```

Two unconditional `send_to` calls after the same intermediate value.

**Graph fragment.** The vertex has one `out` port; multiple edges leave it
to different sinks.

```
v_score_relevance.out → slack_sink
v_score_relevance.out → jsonl_sink
```

**Library agent.** None. DSL supports fan-out from one outport to multiple
downstream nodes natively.

### 2.4 Filter (predicate-gated pass-through)

**Python idiom.**

```python
scored = await score_relevance(message)
if scored["score"] < 0.5:
    return    # drop
send_to(scored, "downstream")
```

**Graph fragment.** A `filter` agent with two outports (`pass`, `drop`); the
`drop` outport goes to the discard sink or to a leaf.

```
v_score_relevance.out → filter.in
filter.pass → downstream
filter.drop → discard
```

**Library agent.** ✅ **`filter`** — takes a predicate; passes messages that
satisfy it, drops others. Predicate expressed as a field comparison.

**Notes.** For Phase 1, predicates limited to `<field> <op> <value>` forms
(`==`, `!=`, `<`, `>`, `<=`, `>=`) and simple boolean combinations of them.
More complex predicates → gap.

### 2.5 Conditional-routing (if/elif/else)

**Python idiom.**

```python
send_to(enriched, "jsonl")     # unconditional
if enriched["severity"] == "critical":
    send_to(enriched, "terminal")
```

Or a proper if/elif/else chain:

```python
if severity == "critical":
    send_to(msg, "slack_alerts")
elif severity == "high":
    send_to(msg, "slack_briefings")
else:
    send_to(msg, "jsonl_low")
```

**Graph fragment.** A `router` vertex with:
- one unconditional outport (`out`) for the always-fires case, wired to
  every sink that is a bare `send_to`.
- one conditional outport per branch (`critical`, `high`, `else`, etc.),
  wired to that branch's `send_to` target.

```
upstream.out → router.in
router.out       → jsonl_sink            (unconditional)
router.critical  → terminal_sink         (conditional on severity)
```

**Library agent.** ✅ **`router`** — has one unconditional outport plus
zero-or-more named conditional outports; routing decision based on a
single field's value or a boolean predicate.

**Notes.** Nested conditionals → gap. `and`/`or` in the predicate → gap for
Phase 1.

### 2.6 Fair-merge convergence (multiple sources, one downstream)

**Python idiom.** Two sources both feed into the same processing function
without an explicit merge step.

```python
for msg in interleave(source_a, source_b):
    result = await process(msg)
    send_to(result, "sink")
```

**Graph fragment.** Multiple edges into one vertex's inport; DSL's default
fair-merge semantics interleaves the streams.

**Library agent.** None — DSL's default when a vertex has multiple incoming
edges to the same inport is fair-merge.

### 2.7 Stateful Python vertex called on stream

**Python idiom.**

```python
tally = SeverityTally()
for msg in enriched:
    tally.process(msg)
```

**Graph fragment.** The instance becomes a vertex. Every message from the
upstream flows into it. It may or may not have outgoing edges (leaf if not).

**Library agent.** None (user-defined class).

**Notes.** The instance's state is inspectable at end of run. Leaves are legal.

---

## Section 3 — Control-flow patterns (feedback, iteration)

### 3.1 Bounded feedback loop

**Python idiom.**

```python
async def process_one(problem):
    for iteration in range(3):
        solution = await propose(problem)
        critique = await critique_solution(solution)
        verdict = await judge(critique)
        if verdict == "approved":
            send_to(solution, "approved")
            return
    send_to(problem, "gave_up")
```

**Graph fragment.** Three vertices in a chain plus a back-edge to the first
vertex from the else branch of a router; a counter in the message tracks
iterations.

**Library agent.** Uses `router` and the base substrate's back-edge support.
An `iter_counter` library agent may simplify: increments a message field
each pass; router checks `iter >= bound`.

**Notes.** Bounded via explicit iteration count OR via convergence
condition. Unbounded loops → gap (require explicit reasoning by user).

### 3.2 Windowing / batching

**Python idiom.**

```python
class Batcher:
    def __init__(self, size=10):
        self.buffer = []
        self.size = size
    def process(self, msg):
        self.buffer.append(msg)
        if len(self.buffer) >= self.size:
            out = self.buffer
            self.buffer = []
            return {"batch": out}
        return None
```

**Graph fragment.** A stateful vertex; emits only when internal condition met.

**Library agent.** ✅ **`batch`** — collects messages until a size, time, or
condition threshold is met.

**Notes.** Emitting `None` should be recognised as "skip this message" (no
downstream forward). Or DSL agents can express this via not calling
`send`.

### 3.3 Deduplication (drop repeats)

**Python idiom.**

```python
class Dedup:
    def __init__(self):
        self.seen = set()
    def process(self, msg):
        key = msg["id"]
        if key in self.seen:
            return None
        self.seen.add(key)
        return msg
```

**Graph fragment.** A stateful vertex that drops repeats.

**Library agent.** ✅ **`deduplicator`** — takes a key field; passes only
novel messages.

---

## Section 4 — Timing patterns

### 4.1 Throttle (rate limit)

**Python idiom.**

```python
class Throttle:
    def __init__(self, rate_per_sec=1.0):
        self.last = 0
        self.interval = 1.0 / rate_per_sec
    def process(self, msg):
        now = time.time()
        if now - self.last < self.interval:
            return None
        self.last = now
        return msg
```

**Library agent.** ✅ **`throttle`** — passes at most N messages per unit time.

### 4.2 Delay

**Python idiom.**

```python
await asyncio.sleep(delay); send_to(msg, ...)
```

**Library agent.** ✅ **`delay`** — holds each message for a fixed time.

---

## Section 5 — Runtime and driver patterns

### 5.1 `main()` driver

**Python idiom.**

```python
async def main():
    batches = await asyncio.gather(*(fetch_source(k) for k in SOURCES))
    articles = [a for batch in batches for a in batch]
    enriched = await asyncio.gather(*(process_one(a) for a in articles))
    ...
```

**Graph fragment.** `main` is not represented in the graph directly; it's
the driver that connects sources to the pipeline body. The presence of
`process_one` and `SOURCES` is sufficient; `main` is inferred as the
default orchestration.

**Library agent.** None. This is substrate-level.

---

## Summary — what's structurally necessary vs. what's convention

**Revised after review:** most of the "library agents" listed in an earlier
draft turn out to be just Python patterns that Claude's asyncio expresses
naturally — an agent whose `process(msg)` decides whether/what/when to
emit. They do not need to be framework primitives.

### Structurally necessary (only 1 non-native primitive)

| Agent | Why it must be a library primitive |
|---|---|
| `merge_sync` (aka `synchronizer`) | Pure message-passing interleaves independent streams (fair merge). It does not synchronize them. To recover asyncio's `gather` semantics (wait for all N, produce ONE merged message), the substrate must provide an explicit synchronizer. DSL has this. |

### Native to DSL — no primitive needed

| Behaviour | How it works |
|---|---|
| Broadcast (fan-out) | An agent outport can be connected to multiple downstream nodes. |
| Fair merge (fan-in without synchronization) | Multiple upstream edges to the same inport interleave. |

### Not primitives — expressed as normal agents

The following patterns are just "an agent whose `process(msg)` implements
this behaviour." They do not need library primitives.

| Pattern | Realised as |
|---|---|
| Filter (pass/drop by predicate) | An agent whose `process` returns `None` (does not emit) when the predicate fails. |
| Router (multi-way branching) | An agent with multiple outports whose `process` chooses which to emit on. |
| Deduplicator | A stateful agent with a `seen` set; drops repeats. |
| Throttle | A stateful agent with a `last_emit` timestamp; drops or delays. |
| Batch | A stateful agent with a buffer; emits when full or on timer. |
| Delay | A stateful agent that holds each message for a fixed time. |
| Iteration counter | A stateful agent that increments a message field. |

Each of these can be a Python class Claude writes, or a pre-written role
file Pat picks from a shared library. Either way, they are **agents, not
framework primitives**. The library is an optional convenience, not a
translation target.

### Reference role library (optional)

A shared roles directory can offer pre-written implementations of the
common patterns above. Pat says "add a deduplicator" and Claude drops in
the shared role file. But the translator does not need this library; it
treats every one of these as a normal stateful agent.

---

## Gaps flagged for later

- **Complex predicates in filter/router** (`and`, `or`, function calls) — currently limited to simple field comparisons.
- **Nested conditionals** — currently only one level of if/elif/else per step.
- **Multiple gather calls in one process_one** — one is understood, multiple in sequence is a chain of merge_syncs; supported but should be verified.
- **Unbounded loops** — require reasoning by the user; not translated automatically.
- **Sources whose factories are compound expressions** — RHS of SOURCES currently limited to URL strings and simple function calls.

---

## Worked example — situation_room Run 2

Applying the table to `experiments/clean_runs/situation_room/response_run2.py`:

- §1.1 SOURCES dict with three RSS URLs → three sources (s0 bbc_world, s1 npr_news, s2 al_jazeera).
- §1.2 three top-level `async def` (`classify_severity`, `identify_location`, `write_briefing`) → three LLM vertices (v0, v1, v2). Docstrings become role prompts. Each returns a dict; the dict keys are the enriched fields.
- §1.3 `class SeverityTally` → one stateful Python vertex (v_tally). Leaf.
- §2.2 `asyncio.gather(classify_severity(m), identify_location(m), write_briefing(m))` in `process_one` → broadcast from source to v0/v1/v2, converge at synthesized `merge_sync` with inports [severity, location, briefing].
- §2.5 Unconditional `send_to(enriched, "jsonl")` + conditional `if severity == "critical": send_to(enriched, "terminal")` → router with unconditional outport to jsonl_recorder and conditional outport `critical` to intelligence_display.
- §2.7 `tally.process(item)` for every enriched message → edge from merge_sync (or router.out) to v_tally.

Resulting graph identical to the one derived by hand:

- Sources: 3
- Vertices: 6 (3 LLM enrichers + merge_sync + router + tally)
- Sinks: 2 (jsonl_recorder, intelligence_display)
- Edges: 16 (9 broadcast + 3 to sync + 1 sync→router + 3 router outputs)

The correspondence is one-to-one from the AST to the graph.
