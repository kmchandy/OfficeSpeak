# Plan — Adaptive DSL Paper 1 (Phase A demonstration)

Implementation plan for the Phase A paper.
For the *decisions* this plan implements, see DECISIONS.md.
For the *reasoning* behind those decisions, see BRAINSTORM.md.

Estimated total time: ~10–12 weeks of focused work plus paper
writing. Aspirational — reality is often 1.5–2× plan estimates,
particularly the earlier phases.

---

## Phase 0 — Foundations (~2 weeks)

Build the infrastructure Claude will use. No experiments yet.
Four workstreams; A and B can run in parallel, C overlaps B,
D waits until B is mature.

### Workstream A — Example library from gallery apps + Nyasha (~1 week)

Backfill design rationales for ~10 gallery apps plus 2–3 of
Nyasha's apps so they become the seed example library Claude
searches at Phase A build time.

**Why gallery apps first, then Nyasha:** the DSL gallery
contains 20 apps that are already documented (READMEs), use
pure-DSL patterns (no app-engineering wrapping), and span more
variety than Nyasha's three. Most of the rationale work is
extracting and structuring existing README content into the
example-library format.

#### Pick from the gallery (~10 entries)

Chosen for *variety of topology, domain, source type, and
complexity*:

| Gallery app | Topology pattern | Why include |
|---|---|---|
| `situation_room` | Diamond (4-way enrichment) → writer | Canonical broadcast-and-combine; multi-RSS news |
| `periodic_brief` | Pipeline | Simpler daily aggregation pattern |
| `job_hunter` | Filter pipeline | Classification + matching with personal data |
| `inbox_triage` | Classifier + router | Queue processing pattern |
| `kalshi_market_watch` | Mixed text + numeric monitor | Spans both modalities |
| `stocks_monitor` | Pure numeric monitor + alert | Numeric-only baseline |
| `wardrobe_assistant` | Multi-source with calendar | Personal-data injection pattern |
| `arxiv_radar` | Specialised text monitor | Scientific domain |
| `weather_monitor` | Alerts | Pure alert pattern |
| `loudness_monitor` | Audio-input + threshold | Non-text source modality |

(Not all 20 gallery apps need entries — 10 well-chosen ones
give the variety the builder needs without redundancy from
near-duplicate text-aggregation apps.)

#### Then add Nyasha's apps (~2 entries)

Nyasha's apps are larger end-to-end systems with personal-data
integration. They demonstrate scaling the DSL patterns:

| Nyasha app | Why include |
|---|---|
| Calendar Manager | Unique to Nyasha (not in gallery); calendar + multi-source event matching |
| Wardrobe Assistant (Nyasha's version) | More elaborate than gallery version; demonstrates scale |

(Nyasha's Job Hunter is similar enough to the gallery version
to skip; cite the difference in the rationale of the gallery
version instead.)

#### Per-entry deliverables

For each app, produce:

- `task.md` — what the office is for (extracted from README)
- `office.md` — the actual specification (copy of the existing
  one)
- `rationale.md` — why these design choices (extracted from
  README + supplemented)
- `samples/` — cached input/output pairs
- `failures.md` — known limitations
- `meta.yaml` — tags, complexity, patterns used

Deliverable: ~12 example-library entries in `examples/`.

**This is the highest-leverage early work.** It forces
articulation of what good S&R designs look like, which directly
informs the seed library (Workstream B), the task specs
(Workstream D), and the builder meta-prompt (Workstream C).

### Workstream B — Seed component library (~1 week)

Write ~15 component entries with full YAML frontmatter and
prompt/code bodies.

| Category | Components |
|---|---|
| Sources (4) | `news_feed`, `price_history`, `weather_observations`, `calendar_events` |
| LLM enrichers (5) | `sentiment`, `ner`, `classifier`, `summariser`, `relevance_filter` |
| Numerical transformers (4) | `moving_average`, `lag_features`, `rolling_stats`, `standardise` |
| Prediction models (4) | `mean_baseline`, `linear_extrapolator`, `arima`, `ridge` |
| Combiners (2) | `text_moderator`, `weighted_average` |

Each entry: full frontmatter (purpose, inputs, outputs,
when_to_use, when_not_to_use, usage_examples,
modification_patterns, internal_adaptation if numerical, cost)
plus body.

Deliverable: `library/` directory with 15 entries.

### Workstream C — Builder pipeline + meta-prompt (~1 week)

Implement the 12-stage builder pipeline as Python code that
orchestrates Claude calls. Write the builder meta-prompt v1.

Components:
- `builder.py` — orchestrator
- `stages/` — one module per stage (1–12)
- `meta_prompt.md` — versioned controller prompt
- `validation.py` — static checks for `office.md`
- `smoke_test.py` — run an office on cached sample data
- `fix_loop.py` — feed Python errors back to Claude

Deliverable: working builder that takes a task spec and produces
an office. Initial offices may be broken — that's what Phase 1
is for.

### Workstream D — Task specs for the 5 demo apps (~3 days)

Draft structured task specs (YAML header + free-form description)
for each demo app:

- `specs/situation_room.md`
- `specs/job_hunter.md`
- `specs/news_brief.md`
- `specs/box_office.md`
- `specs/fluview.md`

Deliverable: 5 task specs in the agreed format.

---

## Phase 1 — First build (~1 week)

Run the builder on **Situation Room** as the proving ground.
This is the existing-gallery rebuild where we know what good
looks like, making it the lowest-risk first test of the
pipeline.

### Experimental-design wrinkle: hide the matching example

Because situation_room is *both* a rebuild target *and* an entry
in the seed example library (Workstream A), the builder might
just retrieve and copy the existing situation_room rather than
designing from scratch.

To make this a real test of reasoning rather than copying, the
builder must be configured so that **when rebuilding gallery app
X, the example library presented to the builder excludes X
itself.** The builder gets to reason from analogous examples
(other gallery apps, Nyasha's apps) but must produce
situation_room without seeing situation_room in its precedent
set.

Same discipline applies for job_hunter (also a rebuild target
and in the example library). For news_brief, box_office, and
FluView — none of which are in the example library — no
exclusion is needed.

This "leave-one-out" protocol is cheap to implement (just filter
the example library by name at Stage 2) and turns the rebuild
test into an honest evaluation: *can Claude reproduce a
known-good design by reasoning from other examples rather than
copying?*

Steps:
1. Feed `situation_room.spec.md` to the builder.
2. Capture the full build trace (Stages 1–12).
3. Run `dsl build` on the produced `office.md`.
4. Run `dsl run` on sample input data.
5. Compare side-by-side to the existing gallery situation_room.
6. Document gaps, failures, surprises.
7. Iterate the meta-prompt if the builder fails systematically.

Goal: builder produces a runnable office at least roughly
comparable to the gallery version. If it doesn't, debug and
iterate on the meta-prompt before scaling to the other apps.

Deliverable: first working build + lessons learned + revised
meta-prompt if needed.

This phase is a **gate**. Don't proceed to Phase 2 until the
builder reliably produces runnable offices for the easy case.

---

## Phase 2 — Build the remaining 4 apps (~2–3 weeks)

Run the builder on each of: Job Hunter, news brief, box office,
FluView. Order from easiest to hardest:

1. Job Hunter (rebuild — known target)
2. News brief (new but similar to periodic_brief in gallery)
3. Box office (new prediction task)
4. FluView (new prediction task)

Per app:
- Feed spec to builder
- Capture build trace
- Validate runnable (`dsl build`)
- Smoke test on cached sample data
- Document what worked, what needed human adjustment
- Update the example library with the new build as a positive
  example

Deliverable: 5 working offices, 5 build traces, 5 rationale
documents.

---

## Phase 3 — Cross-app analysis (~1 week)

The heart of the paper's qualitative analysis. Look at all five
builds side-by-side and identify:

- **Consistent patterns** Claude uses across all five apps
- **Variations** that are appropriately task-specific
- **Common failure modes** that surfaced
- **Quality of rationales** — coherent, useful, shallow,
  defensive?
- **Library growth** — what did Claude invent? Was it novel
  or near-duplicate of existing library agents?
- **Human adjustments** — what kind, how often, why?
- **The "imperfect but helpful" check** — for each app, can a
  human refine the office in a bounded amount of time?

Deliverable: `ANALYSIS.md` capturing patterns, failures, and
characteristic behaviours across the five builds.

---

## Phase 4 — Paper writing (~3–4 weeks)

Workshop paper. Estimated length: 6–10 pages.

### Section structure

1. **Introduction** — the question; why it matters
2. **Background** — adjacent work, distinguishing claims
3. **The paradigm** — architectural substrate, English
   specifications, two-layer split
4. **The builder pipeline** — 12 stages, meta-prompt design
5. **Apps and task specs** — the five apps, the task spec
   format
6. **Library and example memory** — the persistent components
7. **Results** — per-app outcomes, patterns, failures; build
   traces as appendices
8. **Discussion** — preconditions, limitations (including Phase
   B as future work)
9. **Conclusion** — what we showed, what's open

### Key figures

- The architectural template diagram (sources → diamond →
  pipeline → sink)
- The 12-stage builder pipeline diagram
- Five-up comparison of the offices Claude built
- Example build trace excerpt (one per app, abbreviated)
- Library growth across the five builds
- Cross-app pattern table

### Key appendices

- Full task specs for all 5 apps
- Full final `office.md` for all 5 apps
- Build trace excerpts (Stages 1, 3, 6, 7, 12) for one
  representative app
- Component library YAML for all 15 seed agents

Deliverable: paper draft ready for workshop submission.

---

## Phase 5 — Submission (timing varies by venue)

Target an AI workshop with a deadline in fall/winter 2026 or
early 2027. Probable candidates:

- NeurIPS workshops (typically Oct deadline for Dec workshop)
- ICLR workshops
- AAAI / AAMAS workshops

Choose venue after the paper draft is in hand. The paper's
target audience is AI researchers thinking about LLM
capabilities and multi-agent systems.

---

## Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Builder produces unrunnable offices consistently | Medium | Stages 7 (critique), 9 (validation), 10 (smoke test), 11 (fix loop) are designed to catch this. Iterate the meta-prompt in Phase 1. |
| Seed library too small / wrong components | Medium | Library grows during builds as Claude invents. Phase 1 surfaces gaps early. |
| Rationales too shallow to be useful for analysis | Medium | Iterate Stage 12 prompt to require depth (mention alternatives considered, failure modes anticipated). |
| Cross-app patterns are dull / unremarkable | Medium | The rebuild/new mix is designed to surface variation. If it doesn't, that itself is a finding worth reporting. |
| Phase A takes 1.5–2× the estimated time | High | Estimates are aspirational. Don't overcommit to deadlines. |
| Claude's builds need too much human adjustment to be "helpful" | Medium | The "imperfect but helpful" criterion explicitly accepts adjustment. Document what adjustments are needed; it's data. |
| Workshop reviewers say "this is just app generation" | Medium | The architectural-substrate argument (small message-passing agents with English contracts) plus the lineage citations differentiate from generic LLM-codes-an-app work. |

---

## Open questions to revisit during work

- Should Stage 11 (fix loop) cap at N iterations to prevent
  infinite cycles? Probable yes — N = 3.
- How long should the build trace be allowed to grow? (token
  budget vs completeness)
- Should we manually grade office quality, or rely on smoke
  tests + qualitative inspection?
- Should the seed library be the *same* across all 5 apps, or
  varied per app? (Per DECISIONS.md: same — but worth
  revisiting if it proves limiting.)
- Do we need a "verification harness" that runs each office on
  multiple cached inputs to check robustness?

---

## Plan (revised 2026-06-29) — Phase 1: LLM-only apps first, Python agents later

The work splits into two phases. **Phase 1** gets the full
Claudette pipeline working end-to-end for apps with only LLM
agents (situation_room, inbox_triage, debate, periodic_brief_pro).
**Phase 2** extends the pipeline to support apps that include
Python agents (loudness_monitor, backyard_birds, etc.).

This staging is deliberate:
- Most gallery apps are LLM-only — Phase 1 covers them
- Phase 1 validates the core pipeline (pseudocode → graph →
  role files → dsl build → dsl run)
- Phase 2 adds the Python-agent wrapper as a clean extension,
  not a rewrite
- An end-to-end working LLM-only pipeline is a smaller, more
  defensible milestone than trying to do everything at once

---

### Phase 1: LLM-only apps end-to-end (~7 days)

**Step 1 — Translation table (narrow scope).**

Document at `catalog/translation_table.md` (in the NetworkOfThought repo).
Covers the LLM-only-relevant pseudocode constructs:
- `for each <item> from <source>:` (pipeline)
- Step lines: `<step_id>: <verb> <object> -> reads <fields>, enriches <fields>`
- Conditional `if/elif/else` (router; binary case = filter)
- `send to <sink>`
- `merge(...)` if needed for multi-source input

Each entry: pseudocode construct → graph construct, with one
or two specific examples. Always loaded into Claudette's
context.

Estimate: ~1 day.

**Step 2 — Pseudocode → graph parser.**

Python module at `claudette/parser.py`.
Input: pseudocode in the strict grammar (DECISIONS.md §18).
Output: graph dict (DECISIONS.md §19 schema). Deterministic,
with unit tests covering each construct from the translation
table.

Public API:

```python
def parse(pseudocode: str) -> tuple[Graph, list[Warning]]:
    """Pure function: text → (graph dict, warnings). Raises ParseError on malformed input."""
```

Plus a CLI wrapper that reads a pseudocode file, calls `parse()`,
and writes `graph.yaml`. The persisted YAML file is part of the
inspectability chain (DECISIONS.md §25) — not just a debugging
artifact, but a durable record of Stage B's output.

Estimate: ~2 days.

**Step 3 — Graph → office.md generator.**

Python module at `claudette/office_writer.py`.
Input: graph dict. Output: DSL office.md file. Templates the
sources / sinks / agents / connections blocks from the graph's
lists. Smaller than it sounds.

Estimate: ~half a day.

**Step 4 — Meta-prompt v1.**

The prompt Claudette receives at run time. Explains the
three-stage process (English → pseudocode → graph), the
pseudocode grammar in brief, references the translation table,
includes one complete walkthrough (situation_room) as the
exemplar. Plus instructions like *"default to sequential
pipeline; include only what Pat asks for; refinements come in
a separate pass."*

Estimate: ~half a day.

**Step 5 — Per-vertex prompt orchestrator.**

Driver script that:
- Runs SCC analysis on the graph (one call to
  `networkx.strongly_connected_components`) to classify every
  vertex as DAG or cyclic.
- Iterates over the graph's LLM vertices.
- For each vertex, calls Claude with the vertex's role +
  purpose to generate the agent's prompt body. For cyclic
  vertices, the meta-prompt to Claude includes the extra clause
  from translation table §2.3 ("on a re-entry, the message may
  already contain fields you normally produce — treat them as
  feedback and produce a refined value").
- Calls `create_agent_from_prompt` (the wrapper from smoke
  test 1) to write the role.md file.

This uses infrastructure we already have; the new pieces are
the orchestration loop and the SCC-based DAG/cyclic
classification.

Estimate: ~1 day.

**Step 6 — End-to-end driver and first test on situation_room.**

Glue everything together: Pat's spec → pseudocode → graph →
office.md + role.md files → `dsl build` → `dsl run` → output.
Single command: `python3 claudette/build_app.py --spec
<spec_file> --output <target_dir>`.

First test target: situation_room. The Pat-style spec we
already have feeds the pipeline; the output should be a
running office that produces briefings comparable to the
gallery version.

Iterate on bugs and the meta-prompt until end-to-end works.

Estimate: ~2-3 days including bug-fixing.

---

### Phase 1 success criterion

A single command takes situation_room's Pat-style English
description and produces a running DSL office that emits
sensible intelligence briefings on cached news articles. Every
intermediate artifact (pseudocode, graph, role files, office.md)
is inspectable.

After this works, we extend coverage to inbox_triage (tests
the router pattern), debate (tests feedback), and
periodic_brief_pro (tests multi-flow). Each extension is mostly
adding translation-table entries; the pipeline doesn't change.

---

### Phase 2: extend to Python-agent apps (~5-7 days, after Phase 1)

Adds support for apps that include numerical or library-wrapped
agents (loudness_monitor, backyard_birds, wildlife_watcher,
kalshi_market_watch).

| # | What | Estimate |
|---|---|---|
| 7 | Extend translation table with refinement patterns (`threshold-alert`, others) | half day |
| 8 | Write loudness_monitor walkthrough (validates pseudocode for Python agents) | a few hours |
| 9 | Build `create_python_agent_from_spec` wrapper (parallel to `create_agent_from_prompt`; takes pure `f(message, state)` function from Claudette and wraps it as a DSL Agent class) | 1-2 days |
| 10 | Smoke test 5 — Claudette generates a Python agent for a pseudocode operation not in the seed library | half a day |
| 11 | Extend per-vertex orchestrator to dispatch to LLM vs Python wrapper based on vertex type | half a day |
| 12 | End-to-end test on loudness_monitor | 1 day |
| 13 | Extend to backyard_birds (ML-library wrap) and wildlife_watcher | 1-2 days |

---

### Phase 3: gallery regeneration experiment (~2 weeks, after Phases 1+2)

Run Claudette on the full set of demonstration apps from
DECISIONS.md §23. Document per app: did pseudocode generate
correctly? Did the graph compile? Did the agents produce
sensible output? Where did Claudette need adjustment?

This is the experiment that becomes the paper's results
section.

---

## Total estimate

| Phase | What | Time |
|---|---|---|
| 1 | LLM-only apps end-to-end | ~7 days |
| 2 | Python-agent extension | ~5-7 days |
| 3 | Gallery regeneration experiment | ~2 weeks |

End-to-end: roughly **4–5 weeks** of focused work to a complete
demonstration paper.

---

## Immediate next action

**Step 1 — write the translation table.** It's the smallest
foundational piece. Once it exists, the parser (Step 2)
becomes a small exercise in implementing the grammar it
documents. Without it, everything downstream is unanchored.

Estimated time: a few hours for v1.
