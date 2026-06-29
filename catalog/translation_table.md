# Translation table — pseudocode → graph

**Status:** v1 (Phase 1: LLM-only apps).
**Owner:** Claudette (read-only) + humans (editing).
**Loaded into:** every Claudette prompt as part of the meta-prompt.

This document is the **single authoritative reference** for how each
construct in the DSL pseudo-language translates to a graph fragment.
The wrapper in `claudette/parser.py` implements exactly these rules
(deterministic Python — no LLM).

If Claudette can express Pat's task in this pseudo-language, the
wrapper produces a graph; the graph compiles to an office; the
office runs.

---

## 0. Scope and what's deferred

**In scope (Phase 1):**

| # | Construct | Role |
|---|---|---|
| 1 | `inputs:` block (with `merge(...)`) | sources |
| 2 | `for each <item> from <var>:` | pipeline body (the **sequence** primitive) |
| 3 | Step lines (`<id>: <verb> <object> → reads ..., enriches ...`) | vertex |
| 4 | `if/elif/else` after a classifier step | conditional routing (the **branch** primitive) |
| 5 | `send to <target>` | edge to a sink **or** to a vertex declared earlier (the **send-to** primitive) |

Per DECISIONS.md §17, common shapes — pipeline, router, feedback,
multi-flow — **emerge** from these constructs. They are not
separately identified by Claudette.

**Feedback is in scope.** When `send to <target>` targets a vertex
declared earlier in the loop body, the result is a back-edge in
the graph. Messages circulate; on re-entry, `enriches X` overwrites
the previous value of X. Termination is the pseudocode author's
responsibility. See DECISIONS.md §24 for the full semantics.

**Out of scope (Phase 2 / Phase 3):**

- Multiple top-level `flow <name>:` blocks — multi-flow patterns.
  Phase 2.
- Python-implemented vertices (`role: python <module>.<func>`).
  Phase 2.
- Runtime tracing (capturing the full message history across loop
  iterations). Phase 2; until then only the latest field values
  are visible.

If a task description seems to need one of those, Claudette should
say so explicitly rather than guess; the human will decide whether
to defer or extend.

---

## 1. Conventions

### 1.1 Identifiers

Identifiers in the graph are **positional**, not human-friendly.
They are assigned in the order constructs appear in the pseudocode.

| Prefix | What it tags | Example |
|---|---|---|
| `s0, s1, s2, ...` | Sources | `s0` is the first source declared in `inputs:` |
| `v0, v1, v2, ...` | Processing vertices | `v0` is the first step line in the `for each` body |
| `k0, k1, k2, ...` | Sinks | `k0` is the first `send to` |

The pseudocode's step IDs (`s1`, `s2`, … *inside* the `for each`)
are **not** the same as the graph's vertex IDs. The wrapper
renames step IDs to vertex IDs in declaration order. The
pseudocode is for human reading; the graph is for compilation.

### 1.2 Ports

Ports name where messages enter and leave a node.

| Convention | Meaning |
|---|---|
| `out` | The default output port of any node. Used unless overridden by a router (§5). |
| `in_` | The default input port of any vertex or sink. (Trailing underscore because `in` is a Python keyword.) |
| `<branch_value>` | Conditional output port name when an `if/elif/else` step exists. See §5. |
| `<inport_name>` | Named input port on a vertex with multiple inputs. Phase 2 (multi-input synchronizers); not used in pipeline-of-enrichers. |

### 1.3 Edges

Edge form:
```yaml
{ from: [<node_id>, <port>], to: [<node_id>, <port>] }
```

Pipeline rule: between consecutive step lines in a `for each`
body, the wrapper emits an edge `from [v_i, out] to [v_{i+1}, in_]`
automatically. The pseudocode does **not** need to spell these
edges out — they are implicit in the sequence.

### 1.4 Agent and sink contracts

This is the architectural rule that makes `produces` unnecessary.

- **Every processing vertex enriches.** A vertex receives a JSON
  message, sets one field on it (per its `enriches X` clause), and
  forwards the **full enriched message** to its outport(s). No
  vertex ever drops fields. Pass-through is automatic and total.

  On a DAG vertex: incoming message + one new field → outgoing message.

  On a cyclic vertex: same operation, repeated each iteration. The
  field set by `enriches X` is **overwritten** on re-entry (per
  DECISIONS §24); all other fields remain untouched.

- **Sinks project.** A sink receives the full message and reads
  whichever fields it needs — typically the most recent
  enrichment (e.g., `briefing`, `verdict`) plus identifying
  metadata (`url`, `source`). All other fields are ignored.

- **Consequence for Pat.** Pat does not need to think about *which*
  fields flow forward — all of them do. Pat only thinks about
  which field each vertex adds, and which fields each sink
  consumes. The intermediate enrichments (e.g., `severity`,
  `entities`) are present in the message at every downstream
  point; whether they are *used* is the sink's call.

This rule replaces the earlier `produces` verb. There is no need
for "replace the message with a fresh dict" semantics: the writer
just adds `briefing` to a message that already contains
`article.body, entities, severity, ...`; the JSONL sink projects
`briefing` plus `url`; the terminal display projects `briefing`.

---

## 2. The five constructs

### 2.1 Construct: `inputs:` block

#### 2.1.0 Sources vs. inputs — definitions

These two words appear at different levels of the system and are
worth pinning down before the rules.

| | Source (graph level) | Input (pseudocode level) |
|---|---|---|
| What it is | A node in the compiled graph that emits messages | A named handle for a stream of messages |
| Where it appears | `graph.sources` list, positional IDs `s0, s1, ...` | The `inputs:` block in pseudocode |
| Corresponds to | A real-world emitter (RSS feed, IMAP inbox, mic, file watcher) | A name Claudette uses to refer to a stream |
| Persists into the graph? | Yes | No (names are erased by the wrapper) |

The relationship:

- **Primitive input** — binding to a source call:
  `bbc: bbc_world(max_articles=3)` → one source emitted (`s0`).
- **Derived input** — binding to a `merge(...)` of existing input names:
  `articles: merge(bbc, npr, al_jaz)` → **zero** new sources. The
  name `articles` is just shorthand for "the union of streams
  named `bbc`, `npr`, and `al_jaz`."

Both kinds of binding live inside `inputs:`. The grammar of a
binding is uniform: `<var>: <expr>`.

#### 2.1.1 Pseudocode form

```
inputs:
  <var>: <source_name>(<arg>=<value>, ...)     # primitive input
  <var>: merge(<var>[, <var>]*)                # derived input (1+ args)
  ...
```

Constraints:

- Every line is a binding `<var>: <expr>`.
- `<expr>` is either a source-registry call or `merge(...)` over
  previously-bound input variables.
- A `merge(...)` may only reference variables already declared
  earlier in the block. One argument is legal but uncommon —
  `merge(x)` is equivalent to `x` and the parser does not flag it.
- Variable names are local to the pseudocode; the wrapper does
  not emit them into the graph.

#### 2.1.2 Translation rule

The wrapper walks the `inputs:` block in declaration order and
builds a symbol table of input names. For each line:

- **Primitive input** `<var>: <source_name>(args)` →
  emit one entry in `graph.sources` with a fresh positional ID
  (`s0, s1, ...`). Record `<var>` in the symbol table as pointing
  to that source ID.

- **Derived input** `<var>: merge(<v1>, <v2>, ...)` →
  emit no source. Record `<var>` in the symbol table as pointing
  to the union of the source IDs that the named variables resolve
  to (transitively, so a merge of merges flattens).

When the `for each` line below references an input variable, the
wrapper looks it up in the symbol table to get the set of source
IDs, then emits edges `[s_i, out] → [v0, in_]` for each.

#### 2.1.3 Worked example — single primitive input

Pseudocode:
```
inputs:
  emails: imap_inbox(folder="INBOX", poll_seconds=60)
```

Symbol table after parsing:
- `emails` → {s0}

Graph:
```yaml
sources:
  - id: s0
    name: imap_inbox
    params: { folder: INBOX, poll_seconds: 60 }
```

#### 2.1.4 Worked example — three primitives plus a derived merge

Pseudocode:
```
inputs:
  bbc:      bbc_world(max_articles=3)
  npr:      npr_news(max_articles=3)
  al_jaz:   al_jazeera(max_articles=3)
  articles: merge(bbc, npr, al_jaz)
```

Symbol table after parsing:
- `bbc` → {s0}, `npr` → {s1}, `al_jaz` → {s2}
- `articles` → {s0, s1, s2}  (derived; no new source)

Graph (sources block only):
```yaml
sources:
  - id: s0
    name: bbc_world
    params: { max_articles: 3 }
  - id: s1
    name: npr_news
    params: { max_articles: 3 }
  - id: s2
    name: al_jazeera
    params: { max_articles: 3 }
```

The merge is *implicit* in the graph. When a `for each article
from articles:` follows, the wrapper emits three edges into the
first pipeline vertex — one from each of s0, s1, s2 — and DSL's
runtime fairly interleaves the three streams at that input queue.
No explicit "merge vertex" is created.

Notice the asymmetry between the four input bindings (one of which
is derived) and the three graph sources: the `articles` line adds
a name to the symbol table but contributes nothing to
`graph.sources`. This is what "sources vs inputs" means in
practice.

---

### 2.2 Construct: `for each <item> from <var>:`

**Pseudocode form:**

```
for each <item> from <var>:
  <step_1>
  <step_2>
  ...
  <step_N>
  send to <sink>
  ...
```

**Translation rule:**

This is the **pipeline construct**. The body steps become a chain
of vertices `v0, v1, ..., v_{N-1}` in declaration order. The
wrapper emits:

- Edges from each declared source (the `<var>`'s backing sources)
  to `v0`'s `in_` port.
- Edges between consecutive vertices: `[v_i, out] → [v_{i+1}, in_]`.
- Edges from the last vertex (or from a router's outports) to
  sinks declared by `send to`.

`<item>` is the loop variable name — useful for the prompt-body
generator (it tells each agent's prompt *"you'll receive an
`<item>`"*) but not part of the graph itself.

**Default topology rule:** *pipeline is the default.* If the steps
inside the `for each` are sequential and not separated by
conditionals, the result is a straight chain. Diamond / fan-out
patterns are dropped in Phase 1 (see DECISIONS.md §16).

**Worked example:**

Pseudocode:
```
inputs:
  articles: bbc_world(max_articles=3)

for each article from articles:
  s1: extract entities → reads article.body, enriches entities
  s2: classify severity → reads article.body, enriches severity
  send to intelligence_display
```

Graph:
```yaml
sources:
  - id: s0
    name: bbc_world
    params: { max_articles: 3 }

vertices:
  - id: v0
    role: entity_extractor
    purpose: "Extract named entities from article.body and add to the message as `entities`."
  - id: v1
    role: severity_classifier
    purpose: "Read article.body; produce a severity rating and add to the message as `severity`."

sinks:
  - id: k0
    name: intelligence_display

edges:
  - { from: [s0, out], to: [v0, in_] }
  - { from: [v0, out], to: [v1, in_] }
  - { from: [v1, out], to: [k0, in_] }
```

---

### 2.3 Construct: step lines — `enriches`

**Pseudocode form:**

```
<step_id>: <verb> <object> → reads <field>[, <field>]*, enriches <field>
```

The `reads` clause is **optional** (omit for steps whose agents take
the whole message). The `enriches` clause is **required**.

`enriches` is the only step verb in the grammar. Earlier proposals
had a second verb (`produces`) meaning "replace the message with a
fresh dict"; it was dropped to keep the grammar minimal. Every
vertex writes one field to the message.

**Translation rule:**

Each step line becomes one vertex. The verb + object pair determines
the vertex's `role` name (the canonical snake_case form of the noun
phrase):

| Pseudocode | role |
|---|---|
| `extract entities` | `entity_extractor` |
| `classify severity` | `severity_classifier` |
| `tag topic` | `topic_tagger` |
| `identify location` | `geolocator` |
| `write briefing` | `briefing_writer` |
| `score sentiment` | `sentiment_scorer` |

The `reads`/`enriches` annotation does **not** appear in the graph
directly. It is used downstream by the per-vertex prompt generator
(Phase 1 Step 5) to write the agent's prompt body:

> *"You receive a JSON message. Read field `article.body`. Set
> field `entities` on the message. Forward the full message
> (with all other fields preserved) to your output."*

The "forward the full message" clause is generated for every
vertex. Pass-through is universal (see §1.4).

**Semantics of `enriches X`:**

`enriches X` sets `msg.X = <value>`. Other fields are preserved.

On a DAG vertex (no cycle through it), each message arrives at most
once, so "set the field" and "add the field" are the same operation.

On a vertex inside a cycle (reached by a back-edge from a later
step), a message arrives once per loop iteration. `enriches X`
**overwrites** the previous value of X with each new write. Earlier
iterations' values are lost. See DECISIONS.md §24.

**Cyclic-vertex prompt clause.** The per-vertex prompt generator
detects cyclic vertices via SCC analysis on the graph. For a cyclic
vertex, it adds a clause to the agent's prompt:

> *"On a re-entry, the message may already contain fields you
> normally produce, set by your previous pass. Treat them as
> feedback and produce a refined value."*

DAG vertices do not get this clause; their prompt is the
straightforward form above.

**Worked example — pipeline (DAG):**

Pseudocode:
```
for each article from articles:
  s1: extract entities → reads article.body, enriches entities
  s2: classify severity → reads article.body, enriches severity
  s3: tag topic → reads article.body, enriches topic
  s4: identify location → reads article.body, enriches location
  s5: write briefing → reads article.body, entities, severity, topic, location,
                       enriches briefing
  send to intelligence_display
```

Graph (vertices only — sources / sinks / edges as in §2.2):
```yaml
vertices:
  - id: v0
    role: entity_extractor
    purpose: "Read article.body; set `entities` (list of {name, type})."
  - id: v1
    role: severity_classifier
    purpose: "Read article.body; set `severity` (one of LOW/MEDIUM/HIGH/CRITICAL)."
  - id: v2
    role: topic_tagger
    purpose: "Read article.body; set `topic` (list of tags)."
  - id: v3
    role: geolocator
    purpose: "Read article.body; set `location` (country and city if possible)."
  - id: v4
    role: briefing_writer
    purpose: "Read article body + four enrichments; set `briefing` (short prose)."
```

Note: per §16, this is the **pipeline** version of situation_room.
The earlier diamond version (v0..v4 in parallel + synchronizer) is
not expressible in this grammar at all.

---

### 2.4 Construct: `if/elif/else` (router)

**Pseudocode form:**

```
<step_id>: <verb> <object> → reads <field>, enriches <field>
if <field> == "<value_1>":
  send to <sink_1>
elif <field> == "<value_2>":
  send to <sink_2>
else:
  send to <sink_default>
```

or with downstream steps before the sink:

```
<step_id>: classify <X> → reads <field>, enriches <X>
if <X> == "urgent":
  s_urgent_1: ...
  send to <urgent_sink>
else:
  send to <default_sink>
```

**Translation rule:**

The step that the `if` reads from becomes a **router vertex** with
**named outports** — one outport per branch value. The outport name
is the literal `<value>` from the comparison; the `else` branch's
outport is named `else` (or `default`, equivalently).

Each `send to` (or downstream sub-pipeline) attaches its edges to
the corresponding named outport, not to `out`.

**Default rule:** binary `if/else` produces outports `true` and
`false` if the condition is a predicate (e.g., `if is_urgent`); or
the literal values if the condition is `field == "value"`.

**Worked example — three-way router:**

Pseudocode:
```
inputs:
  tickets: support_inbox()

for each ticket from tickets:
  s1: classify ticket → reads ticket.body, enriches category
  if category == "billing":
    send to billing_queue
  elif category == "technical":
    send to tech_queue
  else:
    send to general_queue
```

Graph:
```yaml
sources:
  - id: s0
    name: support_inbox

vertices:
  - id: v0
    role: ticket_classifier
    purpose: "Read ticket.body; add `category` field (one of billing/technical/other)."
    outports: [billing, technical, else]

sinks:
  - id: k0
    name: billing_queue
  - id: k1
    name: tech_queue
  - id: k2
    name: general_queue

edges:
  - { from: [s0, out], to: [v0, in_] }
  - { from: [v0, billing], to: [k0, in_] }
  - { from: [v0, technical], to: [k1, in_] }
  - { from: [v0, else], to: [k2, in_] }
```

**Worked example — binary filter (router as drop-filter):**

Pseudocode:
```
for each transaction from txn_stream:
  s1: score fraud_risk → reads transaction, enriches fraud_score
  if fraud_score > 0.8:
    send to fraud_review_queue
  else:
    send to normal_processing
```

Graph (vertices + edges only):
```yaml
vertices:
  - id: v0
    role: fraud_risk_scorer
    purpose: "Read transaction; add `fraud_score` ∈ [0, 1]."
    outports: [true, false]   # binary predicate: fraud_score > 0.8

edges:
  - { from: [s0, out], to: [v0, in_] }
  - { from: [v0, true], to: [k0, in_] }   # fraud_review_queue
  - { from: [v0, false], to: [k1, in_] }  # normal_processing
```

---

### 2.5 Construct: `send to <target>`

**Pseudocode form:**

```
send to <target>(<arg>=<value>, ...)
```

Where `<target>` is either:

- a **sink name** registered in DSL's sink registry (e.g.,
  `intelligence_display`, `jsonl_recorder_briefing`), or
- a **vertex step ID** declared earlier in the same `for each`
  body (e.g., `v1`, or whichever local step ID Pat used).

The `(<args>)` are optional; omit for sinks that need no
configuration. Vertex targets never take arguments.

**Translation rule:**

The wrapper resolves the target by symbol-table lookup:

- If `<target>` matches a registered sink name → emit one entry in
  `graph.sinks` (deduplicated by name + params) with positional ID
  `k0, k1, ...` and an edge `[<from>, ...] → [<sink_id>, in_]`.
- If `<target>` matches a step ID declared earlier in the loop
  body → emit an edge `[<from>, ...] → [<earlier_vertex_id>, in_]`.
  No new graph node is created. This is a **back-edge** and makes
  the graph cyclic.

The `<from>` for the edge depends on what precedes the `send to`:

- If preceded by a router (`if/elif/else`), the edge leaves the
  router vertex's branch-named outport.
- Otherwise the edge leaves the immediately preceding vertex's
  `out` port.

The parser does **not** reject cycles. It emits an info-level note
in its output reporting the back-edge so a human can verify the
design intent. See §5 for the parser's handling.

**Fan-out — multiple sinks from one vertex:**

Pseudocode:
```
for each article from articles:
  s1: write briefing → reads article.body, severity, location, enriches briefing
  send to intelligence_display
  send to jsonl_recorder_briefing(path="briefings.jsonl")
```

Graph (sinks + edges):
```yaml
sinks:
  - id: k0
    name: intelligence_display
  - id: k1
    name: jsonl_recorder_briefing
    params: { path: "briefings.jsonl" }

edges:
  - { from: [v0, out], to: [k0, in_] }
  - { from: [v0, out], to: [k1, in_] }
```

Both edges leave `v0`'s `out`. DSL's runtime fans out: each message
emitted by `v0` is delivered to both sinks.

**Back-edge — sending to an earlier vertex (feedback):**

Pseudocode:
```
for each problem from problems:
  s1: propose solution → reads problem, enriches solution
  s2: critique         → reads solution, enriches critique
  s3: judge            → reads critique, enriches verdict
  if verdict == "approved":
    send to k_answers
  else:
    send to s1
```

Graph (relevant edges only):
```yaml
edges:
  - { from: [s0, out], to: [v0, in_] }
  - { from: [v0, out], to: [v1, in_] }
  - { from: [v1, out], to: [v2, in_] }
  # Conditional outports on v2 (the judge).
  - { from: [v2, approved], to: [k0, in_] }
  - { from: [v2, else],     to: [v0, in_] }   # ← back-edge
```

The last edge is the back-edge: messages with `verdict ≠ "approved"`
return to `v0` (the proposer) for another iteration. `v0`'s prompt
will get the cyclic-vertex clause (see §2.3) because v0 is in a
non-trivial SCC of the graph.

**Termination is Pat's responsibility.** The example above
terminates only if the judge eventually returns "approved." For
a hard bound, Pat can add an explicit counter step:

```
for each problem from problems:
  s0: count iter → enriches iter
  s1: propose solution → reads problem, iter, enriches solution
  ...
  if verdict == "approved" or iter >= 3:
    send to k_answers
  else:
    send to s0
```

---

### 2.6 Construct: `merge(...)`

Covered in §2.1 as a binding form inside the `inputs:` block —
`merge(...)` is only legal as the right-hand side of an input
binding. It combines previously-declared input variables into a
named derived stream. It is not a standalone statement.

Two consequences:

- **No new source.** A merge only renames; the graph's
  `sources` list is unchanged. The composition shows up later
  as multiple edges into one vertex (see §2.1.4).
- **No mid-pipeline merging in Phase 1.** All merges happen at
  the top of the pipeline. If a task description requires
  mid-pipeline merging (two parallel sub-pipelines converging),
  that is a multi-flow pattern — Phase 2.

---

## 3. End-to-end worked example

A small pipeline tying §2.1 – §2.5 together. This is the kind of
output Stage A should produce for a simple task.

### Task description (Pat-style)

> *"Pull RSS articles from BBC, NPR, and Al Jazeera. For each
> article, classify the severity (low / medium / high / critical),
> identify the geographic location, and write a short briefing.
> Show me critical-severity briefings in my terminal; save all of
> them to a JSONL file."*

### Pseudocode (Stage A output)

```
inputs:
  bbc:      bbc_world(max_articles=3)
  npr:      npr_news(max_articles=3)
  al_jaz:   al_jazeera(max_articles=3)
  articles: merge(bbc, npr, al_jaz)

for each article from articles:
  s1: classify severity → reads article.body, enriches severity
  s2: identify location → reads article.body, enriches location
  s3: write briefing → reads article.body, severity, location,
                       enriches briefing

  if severity == "critical":
    send to intelligence_display
  send to jsonl_recorder_briefing(path="briefings.jsonl")
```

### Graph (Stage B output — wrapper-produced)

```yaml
sources:
  - id: s0
    name: bbc_world
    params: { max_articles: 3 }
  - id: s1
    name: npr_news
    params: { max_articles: 3 }
  - id: s2
    name: al_jazeera
    params: { max_articles: 3 }

vertices:
  - id: v0
    role: severity_classifier
    purpose: "Read article.body; add `severity` ∈ {low, medium, high, critical}."
  - id: v1
    role: geolocator
    purpose: "Read article.body; add `location` (country and city if possible)."
  - id: v2
    role: briefing_writer
    purpose: "Read article.body, severity, location; set `briefing` (short prose)."
    outports: [critical, else]   # because of the if/else following s3

sinks:
  - id: k0
    name: intelligence_display
  - id: k1
    name: jsonl_recorder_briefing
    params: { path: "briefings.jsonl" }

edges:
  # Sources → first vertex (merge is implicit at v0's input queue).
  - { from: [s0, out], to: [v0, in_] }
  - { from: [s1, out], to: [v0, in_] }
  - { from: [s2, out], to: [v0, in_] }

  # Pipeline body.
  - { from: [v0, out], to: [v1, in_] }
  - { from: [v1, out], to: [v2, in_] }

  # Conditional fan-out: severity == "critical" goes to display;
  # everything (both branches) goes to JSONL.
  - { from: [v2, critical], to: [k0, in_] }
  - { from: [v2, critical], to: [k1, in_] }
  - { from: [v2, else], to: [k1, in_] }
```

Notice: the second `send to jsonl_recorder_briefing` line is
**outside** the `if`, so both branches forward to `k1`. The
wrapper emits two edges to `k1` — one from each outport — because
"send to k1" applies to every message regardless of branch.

---

## 4. Open issues / TODO

- **Refinement patterns:** `dedup-at-front` and `threshold-alert`
  are useful post-hoc names but are not primary constructs in the
  grammar. To be documented in `catalog/refinements.md` (Phase 1
  Step 1.5).
- **Role-name derivation rule:** §2.3 lists common verb→role
  mappings by example. A more formal rule (e.g., "drop articles,
  noun-form the verb, append `_<object>` if disambiguating") may
  be needed once we see more cases. For now: the per-vertex
  prompt generator can ask the LLM to pick a role name when the
  derivation is ambiguous.
- **Source/sink registry coverage:** this table assumes Claudette
  knows what's in DSL's source and sink registries. The meta-prompt
  needs to include or reference that list so Claudette doesn't
  invent source names that don't exist. Tracked separately.
- **Termination-guard heuristic:** when a cyclic vertex is reached
  by a back-edge and the `if/elif/else` immediately before the
  back-edge contains no obvious bound (no `iter >=` term, no
  counter step earlier in the loop), the parser may emit a warning.
  Heuristic only; not enforced.

---

## 5. How to use this table (for the parser)

The parser in `claudette/parser.py` (Phase 1 Step 2) implements
exactly the rules in §2.1 – §2.5. Each construct has a
deterministic mapping; there is no LLM call in Stage B.

The parser's job, in order:

1. Read the `inputs:` block → build the input symbol table and
   emit `graph.sources` with positional IDs. Primitive bindings
   add sources; derived (`merge(...)`) bindings only add names.
2. Read each step line in the `for each` body in order → emit one
   `graph.vertices` entry per step, with a local step-ID-to-vertex-ID
   map.
3. Track any `if/elif/else` immediately following a step → annotate
   that step's vertex with `outports: [<value_1>, <value_2>, ...]`.
4. Read each `send to <target>` → resolve `<target>`:
   - If it matches a registered sink name → emit a `graph.sinks`
     entry (deduplicated by name + params) and an edge.
   - If it matches a step ID declared earlier in the body → emit
     a back-edge (no new graph node). Log the back-edge.
5. Emit the implicit edges: sources → v0, v_i → v_{i+1}, last → sinks.
6. Run SCC analysis on the assembled graph. Annotate every vertex
   in a non-trivial SCC as `cyclic: true` in the graph dict.
7. Validate: every vertex has at least one incoming edge; every
   non-sink output is consumed somewhere; every `send to` target
   resolves either to a sink name or to an earlier step ID
   (otherwise: parse error).
8. Optional warning: cyclic vertex with no obvious termination
   guard (no `iter >=` term, no counter step earlier in the loop).

Anything the pseudocode contains that this table does not cover —
unknown verb, unrecognised target name, malformed step line — is a
parse error. The parser fails loudly rather than guessing.

**Cycles are not parse errors.** Back-edges are legal graph
structure. The parser emits an info-level log entry per back-edge
so a human can verify intent; it does not reject the program.
