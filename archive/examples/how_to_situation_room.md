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

## A description of a sense-and-respond app

> *"I want a daily intelligence digest. Pull articles from three
> world-news RSS feeds (BBC, NPR, Al Jazeera). For each article, I
> want named entities extracted, the severity classified, the
> topic tagged, and the geographic location identified. Then
> combine all of that into a short written briefing for each
> article. Show me the briefings in my terminal and also save
> them as JSONL so I can analyse them later."*
>

----

## How to build an app from its description

Step 1: Identify sources Sources are ways in which
the app gets information. Sinks are where the app's outputs go.
Step 1.1. In this app the sources are the three RSS feeds from BBC, NPR, Al Jazeera.
Let's create source agents s0, s1, s2 that emit from the feeds BBC, NPR and Al
Jazeera, respectly. These agents use the standard RSS feed structure. List of
sources is:

```yaml
sources:
  - id: s0
    name: bbc_world
  - id: s1
    name: npr_news
  - id: s2
    name: al_jazeera
```
Step 2. Identify sinks. In this app the sinks are the briefing at the terminal and a JSONL file.
So we create sinks k0 and k1 that accept messages for briefing at terminal and
JSONL file, respectly. We aren't told what format the briefing and file should be
so we will use anything we want. List of sinks is:

```yaml
sinks:
  - id: k0
    name: intelligence_display
    purpose: "Render the briefings to the terminal as the office runs."
  - id: k1
    name: jsonl_recorder_briefing
    params: { path: "briefings.jsonl" } # arbitrary name of the file
    purpose: "Persist each briefing as one line of JSON for later analysis."
```

Step 3: Identify well-defined small steps in processing information.
In this example, the steps are [extract entities, classify severity, 
tag topic, identify geographic location]. Each small step will be an agent.
We create agents v0, v1, v2, v3 that execute steps extract entities, classify severity, 
tag topic, identify geographic location, respectly. We will use the following agents
each executing a step.

```yaml
vertices:
  - id: v0
    role: entity_extractor
    purpose: "Extract named entities (people, organisations, places) from the article body."

  - id: v1
    role: severity_classifier
    purpose: "Rate the article's severity on a fixed scale (LOW/MEDIUM/HIGH/CRITICAL)."

  - id: v2
    role: topic_tagger
    purpose: "Assign one or more topic tags (politics, economics, climate, conflict, ...)."

  - id: v3
    role: geolocator
    purpose: "Identify the geographic focus of the article — country and city if possible."

```

Step 4: Guess the pattern in which messages flow among sources, agents
and sinks. 
Observation 1: Messages from all the sources are processed in the same way. 
Messages from BBC, NPR, Al Jazeera are processed using the same steps.
This suggests that outputs from s0, s1, s2 should go to the same vertex.
Observation 2: Observe that the steps [extract entitites, ..., identify location] are carried
out independently of each other; one step does not depend on the output of
another. This suggests a broadcast-merge-enrichment message flow pattern which has a gate
agent g and a merge agent m, with edges from  g to the parallel steps and 
edges from each parallel step to m.


```yaml
- id: g
    role: gate
    purpose: "Gateway to the broadcast-merge structure."

  - id: m
    role: synchronizer
    purpose: "Merge inputs."

```


The messages output by the merge agent m are sent to the sinks. Use the
standard pattern of a writer agent that structures messages for sinks.

```yaml
- id: sink_writer
    role: writer
    purpose: "Write messages in a nice format."

```

Putting these ideas together, the initial design of the network is as follows.



---

## Network specification

```yaml
sources:
  - id: s0
    name: bbc_world
  - id: s1
    name: npr_news
  - id: s2
    name: al_jazeera

processing agents:
  - id: g
    role: gate
    purpose: "Gateway to the broadcast-merge structure."

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

  - id: m
    role: synchronizer
    purpose: "Wait for one message on each inport (each is one enrichment of the same article); emit a single merged message carrying all enrichment fields plus the original article fields."

  - id: sink_writer
    role: writer
    purpose: "Write messages in a nice format."

sinks:
  - id: k0
    name: intelligence_display
    purpose: "Render the briefings to the terminal as the office runs."
  - id: k1
    name: jsonl_recorder_briefing
    params: { path: "briefings.jsonl" }
    purpose: "Persist each briefing as one line of JSON for later analysis."

edges:
  # Sources feed the merge.
  - { from: [s0, out], to: [m, in_] }
  - { from: [s1, out], to: [m, in_] }
  - { from: [s2, out], to: [m, in_] }

  # Deduplicator fans out to four enrichers — they each see the
  # same deduplicated article.
  - { from: [m, out], to: [v1, in_] }
  - { from: [m, out], to: [v2, in_] }
  - { from: [m, out], to: [v3, in_] }
  - { from: [m, out], to: [v4, in_] }

  # Enrichers fan into the synchronizer, each on a named inport.
  - { from: [v1, out], to: [m, in_0] }
  - { from: [v2, out], to: [m, in_1] }
  - { from: [v3, out], to: [m, in_2] }
  - { from: [v4, out], to: [m, in_3] }

  # Synchronizer emits one merged message per article to the writer.
  - { from: [m, out], to: [sink_writer, in_] }

  # Writer fan-outs to both sinks (both consume the briefing).
  - { from: [sink_writer, out], to: [k0, in_] }
  - { from: [sink_writer, out], to: [k1, in_] }
```

---


### Argument for a new node: a deduplicator at the front

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
