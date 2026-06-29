# Example: situation_room

A training example for Claudette. Pat-style task description in
English, the resulting network expressed as a flat graph, and
rationale prose explaining why the network has the shape it
does — with structural rules embedded in context where they
apply.

The network specification format is graph-oriented: a flat list
of vertices (with role and purpose), sources, sinks, and edges
that connect them. No human-friendly names (Sasha, Eve, …); just
`v0, v1, …, s0, s1, …, k0, k1, …`. Pat reads office.md; Claudette
reads and produces this.

---

## Task description (Pat-style)

> *"I want a daily intelligence digest. Pull articles from three
> world-news RSS feeds (BBC, NPR, Al Jazeera). For each article, I
> want named entities extracted, the severity classified, the
> topic tagged, and the geographic location identified. Then
> combine all of that into a short written briefing for each
> article. Show me the briefings in my terminal and also save
> them as JSONL so I can analyse them later."*

This is the kind of paragraph a non-coder would write when
asking for a sense-and-respond app. It names the sources, the
processing wanted, the output. It does not specify topology,
agent count, or framework details.

---

## Network specification

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
    role: deduplicator
    params: { by: url }
    purpose: "Drop articles whose URL has already been seen this run."

  - id: v1
    role: entity_extractor
    purpose: "Extract named entities (people, organisations, places) from the article body."

  - id: v2
    role: severity_classifier
    purpose: "Rate the article's severity on a fixed scale (LOW/MEDIUM/HIGH/CRITICAL)."

  - id: v3
    role: topic_tagger
    purpose: "Assign one or more topic tags (politics, economics, climate, conflict, ...)."

  - id: v4
    role: geolocator
    purpose: "Identify the geographic focus of the article — country and city if possible."

  - id: v5
    role: synchronizer
    params: { inports: [entities, severity, topic, location] }
    purpose: "Wait for one message on each inport (each is one enrichment of the same article); emit a single merged message carrying all four enrichment fields plus the original article fields."

  - id: v6
    role: writer
    purpose: "Compose a short briefing from the merged article + four enrichment fields. Output readable prose, preserve the original url and source."

sinks:
  - id: k0
    name: intelligence_display
    purpose: "Render the briefings to the terminal as the office runs."
  - id: k1
    name: jsonl_recorder_briefing
    params: { path: "briefings.jsonl" }
    purpose: "Persist each briefing as one line of JSON for later analysis."

edges:
  # Sources feed the deduplicator.
  - { from: [s0, out], to: [v0, in_] }
  - { from: [s1, out], to: [v0, in_] }
  - { from: [s2, out], to: [v0, in_] }

  # Deduplicator fans out to four enrichers — they each see the
  # same deduplicated article.
  - { from: [v0, out], to: [v1, in_] }
  - { from: [v0, out], to: [v2, in_] }
  - { from: [v0, out], to: [v3, in_] }
  - { from: [v0, out], to: [v4, in_] }

  # Enrichers fan into the synchronizer, each on a named inport.
  - { from: [v1, out], to: [v5, entities] }
  - { from: [v2, out], to: [v5, severity] }
  - { from: [v3, out], to: [v5, topic] }
  - { from: [v4, out], to: [v5, location] }

  # Synchronizer emits one merged message per article to the writer.
  - { from: [v5, out], to: [v6, in_] }

  # Writer fan-outs to both sinks (both consume the briefing).
  - { from: [v6, out], to: [k0, in_] }
  - { from: [v6, out], to: [k1, in_] }
```

---

## Rationale

The rationale explains *why* the network has this shape. Each
sub-section addresses one design choice. Structural rules
(*"when N parallel paths converge, use a synchronizer"*) are
introduced in context as they become relevant, not as standalone
instructions.

### Why one round of processing, not several

The task describes one operation per article: *enrich, then
combine, then write*. There is no second-pass refinement; the
writer's output is the final artifact, not input for further
processing. So the network's depth is determined by the data
flow described: roughly **source → process → write → out**.
Adding extra depth without a reason in the task description is
over-engineering.

If Pat had said *"...then rank the briefings by severity and
show me the top three,"* a downstream ranking vertex would be
needed. She didn't, so it isn't.

### Why four parallel enrichers, not one combined agent

The four enrichments — entities, severity, topic, location —
are **independent of each other**. The topic tag does not
depend on the severity rating; the entity list does not depend
on the geolocation. None of them needs the output of any other
as input.

When transformations are mutually independent, two options
exist:

- **Sequential pipeline:** entity_extractor → severity_classifier → topic_tagger → geolocator → writer. Each agent reads everything that came before and adds its field.
- **Parallel diamond:** all four enrichers receive the same input from the deduplicator; their outputs converge later.

The parallel design is strictly better when the enrichments
don't depend on each other. Reasons:

- **Four LLM calls in parallel < four LLM calls in sequence** for wall-clock latency.
- **Each enricher's prompt is simpler** — it only has to think about its one job, not also pass through all the other fields. (In a pipeline each agent has to be careful to preserve all upstream fields; in a diamond each agent emits only its own field and the synchronizer does the merging.)
- **Replacing one enricher is local** — change v2's prompt and the others are untouched.

A single combined agent ("one giant prompt that produces all four fields") would also work, but loses these properties: it's one big prompt to maintain, hard to inspect per-field, can't be parallelised, and any change requires re-engineering the whole prompt. **The "many small focused agents" pattern is the design principle here.**

### Why the synchronizer (v5)

After the four parallel enrichers, we have four separate
messages per article — one from each enricher, each carrying
just that enricher's output field. The writer needs all four
together to produce one briefing.

**Structural rule (in context):** *when N parallel paths
converge at one downstream agent, a synchronizer is needed
between them. The synchronizer waits for one message on each of
N named inports and emits a single merged message. Without it,
the writer would receive four separate messages per article
with no way to know they belong together.*

The synchronizer's inports are named to match the
enrichments — `entities`, `severity`, `topic`, `location` —
so the merged message has those fields readable. The
enricher-to-synchronizer edges target those named inports
specifically (see `{from: [v1, out], to: [v5, entities]}`,
etc.).

### Why the deduplicator (v0) is at the front

Three RSS sources sometimes carry the same story (e.g., a major
event covered by all of BBC, NPR, and Al Jazeera). Without
deduplication, the story would be enriched separately for each
source — four enrichments × three sources = twelve LLM calls
on the same article, three nearly-identical briefings.

The deduplicator sits *before* the enrichers because
deduplication is per-article and doesn't need enrichment
information. Putting it first saves the expensive enrichment
work on duplicates.

**Structural pattern (in context):** *vertices that filter or
transform per-item without needing downstream information go
near the front. They reduce the workload of more expensive
downstream vertices.*

### Why a separate writer (v6) after the synchronizer

The synchronizer is a structural agent — it waits for inputs
and merges them mechanically. It does not generate prose. The
writer takes the merged dict and produces a coherent briefing.

These are different jobs:

- **Synchronizer** — structural, deterministic, language-agnostic. DSL's built-in synchronizer handles this; no prompt needed.
- **Writer** — semantic, generative. Requires an LLM with a prompt that knows how to compose a briefing.

Combining them would mean asking the synchronizer to also do
natural-language composition, which muddles its role. The
cleaner factoring keeps structural agents structural and gives
the LLM job to a dedicated vertex.

### Why two sinks (k0, k1), not one

The user wants both terminal output (`intelligence_display`)
and persistent storage (`jsonl_recorder_briefing`). These are
different output formats with different consumers:

- Terminal output is for human-now (the user reading as the office runs).
- JSONL is for machine-later (the user analysing patterns over time).

Both can consume the same briefing — no need to choose. The
writer fan-outs its single output to both sinks via two edges
from `v6's out`. **This is fan-out without synchronisation: the
sinks consume the briefing independently and don't need to be
combined downstream.**

---

## Alternatives considered and rejected

**Pipeline instead of diamond (sequential enrichment).**
Could the four enrichments run sequentially? Yes, but it
would be slower (four sequential LLM calls per article instead
of four parallel) and forces each agent to pass through all
earlier fields. Rejected because the enrichments are
independent — there's no reason to serialise them.

**A single all-in-one enricher.** Could one large prompt
produce all four enrichment fields at once? Yes, and it would
save LLM calls. But it sacrifices modularity: changing the
severity scale requires rewriting the combined prompt;
adding a fifth enrichment means restructuring everything. Four
focused agents are easier to maintain, easier to inspect, and
easier for Claudette to generate (each has a narrow purpose).

**Skipping the deduplicator.** Could the diamond just process
duplicates as if they were distinct? Yes, the JSONL would just
have repeats. But the user gets a cleaner experience without
duplicates, and the enrichment cost is non-trivial. The
deduplicator is a small structural agent with no LLM call;
cheap to include.

**Putting the writer inside the synchronizer.** Could the
synchronizer produce the briefing directly? Yes, but DSL's
synchronizer is structural and prompt-less. Forcing prose
generation into it would require either a custom synchronizer
or a hybrid agent. Cleaner to keep `v5` structural and add
`v6` for the writing.

---

## What this design does not handle

- **Cross-article reasoning.** Each article is processed
  independently. The writer can't say *"This is the third
  article today mentioning OPEC, suggesting a pattern."* That
  would require a second processing stage with cross-article
  state.

- **Article ranking.** Briefings come out in the order articles
  were processed, not ranked by severity or relevance. If the
  user wanted *"show me the most important story first,"* this
  design would need a downstream ranking vertex.

- **Source-quality weighting.** All three sources are treated
  identically. If the user wanted BBC's coverage of European
  events weighted higher than NPR's, the office would need
  per-source metadata and a credibility-aware enricher.

These are real limitations. They're correctly excluded because
the task description doesn't ask for them. If Pat's next
request was *"now also rank by severity,"* the change would be
adding a ranking vertex after `v6` — not restructuring the
existing graph.
