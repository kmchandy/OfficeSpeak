# Directions — four load-bearing points (captured so we don't lose them)

Raised by Mani while running the plant-a-gap mutants. Each turns an apparent
limitation into structure. Cross-references: `EXPERIMENTS_PLAN.md`,
`prompt_v2_backlog.md`.

---

## 1. Diversify the corpus — span a space of office *shapes*

Problem: the four offices (support_desk, investment_club, tutor, debate) are all
one shape — a **deliberative panel**: several agents produce views, a decider
combines, a record logs. E1 (build validity) over four near-identical offices
tests one thing four times.

Fix: choose offices to span an axis of computational shapes.

| Shape | What it does | Essential state | New coordination it stresses |
|---|---|---|---|
| deliberate | agents argue, a decider combines | the record, turn-taking | joins (merge_synch), gate |
| detect-anomaly | learn "normal", flag deviations | per-entity baseline (windowed) | per-key state; thresholding; alert routing |
| predict-and-learn | forecast, observe outcome, update | model + pending forecasts | temporal join; delayed match of actual->prediction |
| enrich | stateless stream transform | none (the trivial end) | none — the baseline case |

Why prediction is the *right* kind of hard: it has an **essential feedback
loop** — forecast now, ground truth arrives later, predictor updates. Its state
(the learned model + forecasts pending their outcomes) is unavoidable. This is the
cleanest answer to the earlier worry that informal specs collapse to "trivial
functional programming": you literally cannot do prediction without state.

New coordination these shapes introduce (absent from the deliberative four):
- **temporal join** — align a numeric stream with a news stream for the *same
  day/window* (merge_synch on a key, not just "wait for both inputs").
- **delayed match** — when a real outcome arrives a week later, match it back to
  the earlier prediction it grades (a keeper holding pending forecasts, matched by
  id). A merge separated in time.
- **per-key state** — a baseline/model *per region / per entity*, not one global
  record.

Paper framing: report **coverage of shapes**, not count of examples.

Candidate new offices (Pat-style draft specs below): `oil_price`,
`flu_watch`, and an ops/`anomaly_monitor`. See draft specs at the end of this
file.

---

## 2. A complete app = graph + agent bodies (and the split is the correctness argument)

A running app is not just the wiring; each agent needs a **body** — an LLM prompt
or a Python function. Build therefore has two stages:

- **Stage A — topology + coordination** (what plant-a-gap / explain-back test).
- **Stage B — agent bodies** (generate each worker's prompt or Python).

The load-bearing observation: **coordination agents are library code, worker
bodies are generated.**

- gate, merge_synch, select, record, router, fair_merge = hand-written library,
  **correct by construction**. Never LLM-generated.
- worker bodies (Warren's value analysis, Herb's tax math) = LLM-generated.

Consequences:
1. An LLM mistake in a body is a **content** error (the worker reasons badly) —
   testable and Pat-catchable — and can **never** be a coordination error, because
   the nondeterminism-controlling machinery is never generated. This is *why* an
   office can be correct despite generated bodies.
2. The explain-correct loop extends **downward**: worker bodies are prompts Pat
   can read, so she reviews what each worker is told to do, not only the org chart.
3. New check — **contract conformance**: the graph declares each agent's
   `state / reads / sends`; the generated body must honor exactly that interface.
   Checkable, and testable *because* of determinism (E4).

(The repo already has orchestration that generates role files —
`prompt_orchestrator.orchestrate(...)`, Stage C in the older pipeline. Stage B
here is the office-era version of that.)

---

## 3. Composition answers "only works for small offices"

Criticism: this methodology only helps Pat with *small* offices.

Answer: Pat **composes** offices. She builds a support_desk office and a
small-business-accounts office separately, then combines them — either by wiring
one office's outputs to another's inputs, or by nesting a whole office as a single
agent (a "department") in a larger org chart.

This is not a dodge; it is dataflow / Kahn compositionality, and it buys three
things:

- **HCI (comprehension stays small).** Pat never understands the big office all at
  once. She builds and understands each sub-office, then treats each as one box in
  a bigger chart. The explain-back runs **per level**, and every level is small.
  So "small" is exactly where human comprehension lives; composition lets the
  system grow while Pat keeps reasoning small. That *is* the rebuttal.
- **Systems (determinism preserved under composition).** If each sub-office is
  determinate (no fair merge except at its own sources), the composition is
  determinate as long as the gluing wiring adds no uncontrolled merge. So the
  property that makes empirical testing valid (E4) survives scaling.
- **New research questions (a genuine second contribution).**
  - a **record shared across two offices** may need a gate spanning both offices
    (cross-office consistency).
  - an **office-as-agent** should present a clean contract (its input/output
    ports) that hides its internal coordination — encapsulation / assume-
    guarantee reasoning for offices.

Turns the scaling weakness into structure. Deserves its own experiment (see
EXPERIMENTS_PLAN E6): build two small offices, compose them, test that the
composition is a valid office and that the per-level explain-back still lets Pat
understand and correct it.

---

## 4. Cross-cutting: what each point does for the paper's claim

- (1) makes E1 a test across a *space*, and kills the "trivial functional
  programming" objection via prediction's essential state.
- (2) upgrades the claim from "Claude designs a valid office" to "Claude builds a
  *running* office," and isolates where LLM errors can and cannot land.
- (3) converts the scalability objection into a compositionality result and a
  second set of research questions.

---

## Draft Pat-style specs for the new offices (seeds — refine before use)

### oil_price (predict-and-learn; numeric+news temporal join; delayed feedback)

> I want an office that predicts where the price of crude oil is headed over the
> next week. Watch the daily price and inventory numbers, and also watch the
> news — OPEC announcements, conflicts, that sort of thing. I want two
> forecasters: one who goes mostly on the numbers and fundamentals, and one who
> goes on what the news is saying. Each makes a call — up, down, or flat, with a
> rough size — for the same day's information. A head forecaster combines the two
> into one prediction and writes it down. Then, when the real price a week later
> comes in, compare it to what we predicted and tell each forecaster how they did,
> so they can adjust and do better next time. Keep a running record of every
> prediction and how it turned out.

Coordination this forces: align numbers+news for the same day (temporal join);
match a week-later actual back to its prediction (delayed match / keeper of
pending forecasts); combine two forecasters (merge_synch); a record.

### flu_watch (anomaly + prediction; per-region state)

> I want an early warning office for flu. Watch the weekly CDC surveillance
> numbers and hospital reports for each region, and watch the news for outbreak
> stories. For each region, learn what a normal week looks like and flag when
> cases or deaths jump above what's expected. On top of the alerts, predict next
> week's flu-related deaths per region, and when the real numbers come in, check
> how close we were and adjust. Keep a log of alerts and predictions.

Coordination this forces: per-region baseline (per-key state — a record keyed by
region, or a keeper per region); threshold vs learned normal (anomaly);
prediction + delayed feedback (as in oil_price).

### anomaly_monitor (pure detect-anomaly; sense-and-respond)

> Watch the health metrics coming off our services — response times, error rates,
> that kind of thing. For each service, learn what normal looks like over a
> rolling window and raise an alert when something drifts out of range. If several
> alerts are really the same underlying problem, group them so I get one message,
> not twenty, and route it to whoever owns that service.

Coordination this forces: per-service windowed baseline (per-key state);
dedup/group (a stateful aggregator); route (router).
