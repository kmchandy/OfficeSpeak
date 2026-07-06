# Experiments plan (for the paper)

The paper's claim is stacked:
- **HCI layer** — a non-programmer (Pat) commands a stateful distributed system
  through a **build -> explain -> correct** loop.
- **Systems layer** — LLM-generated stateful offices are made correct and
  reproducible by **coordination** (gate, merge_synch, select, record/keeper,
  fair_merge, router), not by restricting the language.

Experiments map onto that claim.

## Corpus and controls

- The corpus must span a **space of office shapes**, not just add examples (see
  DIRECTIONS.md #1). Axis: deliberate / detect-anomaly / predict-and-learn /
  enrich.
  - deliberative: **support_desk** (the "shot"), **investment_club**, **tutor**,
    **debate**.
  - predict-and-learn: **oil_price**, **flu_watch** (draft specs in DIRECTIONS.md)
    — essential feedback loop; new coordination (temporal join, delayed match).
  - detect-anomaly: **anomaly_monitor**, and the anomaly half of flu_watch —
    per-key windowed state.
- Two substrates: **shared-memory** (`prompt.md`) and **message-passing**
  (`prompt_local_state.md`).
- Discipline: every build and every explanation is produced in a **fresh chat**
  that does not know what is being measured. Rotate which office is the shot so no
  test office appears in its own prompt.
- Paper framing: report **coverage of shapes**, not count of examples. Prediction
  offices specifically retire the "informal specs are trivial functional
  programming" objection, because their state is essential.

## E1 — Build validity

Question: can Claude turn an informal English office into a valid office graph?
Per office x substrate x N fresh runs, diagnose each graph on four properties:
1. valid office (well-formed, runnable topology);
2. implements the spec's required behavior;
3. uses coordination where needed (gate for shared read-modify-write; merge_synch
   for joins; select for ask-and-wait);
4. no missing or invented jobs.
Report per-property pass rates + a failure-mode catalog. (investment_club run_1
and run_2 are the first two data points; both passed strongly.)

E1 as stated tests **Stage A** (topology + coordination). A complete app also
needs **Stage B — agent bodies** (each worker's LLM prompt or Python). Split the
build claim accordingly (see DIRECTIONS.md #2):
- **E1a (Stage A)** — topology + coordination, as above.
- **E1b (Stage B)** — generate worker bodies and check **contract conformance**:
  does each body honor exactly the `state / reads / sends` the graph declared?
  Key point that bounds the risk: coordination agents (gate, merge_synch, select,
  record, router) are trusted **library** code, never generated; only worker
  bodies are generated, so a generation error is a **content** error (testable,
  Pat-catchable), never a coordination error. E1b is testable *because* of E4's
  determinism.

## E2 — Substrate portability

Question: does the same English office yield faithful graphs on both substrates
with coordination preserved? Compare shared-memory vs message-passing per office;
show the coordination structure is invariant and only the state-sharing mechanism
changes (record <-> keeper-agent / broadcast). investment_club already shows this;
extend to the other three.

## E3 — The explain-back loop (HCI core)

- **E3a fidelity** — does the explanation accurately describe the graph? Judge
  reads graph + explanation, rates accuracy.
- **E3b discrimination (plant-a-gap)** — inject single known defects; measure
  detection rate and false-positive rate. First pilot:
  `offices/investment_club/plant_a_gap/` (6 mutants, pre-registered). Extend to
  tutor/debate and both substrates before quoting a rate.
- **E3c Pat-in-the-loop** — give explanations of correct AND defective graphs to
  non-expert humans; measure whether they catch the planted defect from plain
  English alone. This is the claim that actually matters; needs human subjects.

## E4 — Determinism (systems core)

- Show generated graphs contain no fair merge except at the source merge, and that
  shared read-modify-write is serialized by a gate.
- **Ablation**: run an office with vs without its gate; show reproducible output
  vs corrupted/nondeterministic output. This is what makes E1-E3's empirical
  testing meaningful (determinism enables repeatable tests).
- Ties to the theory split: determinism = testable; UNITY-style properties =
  provable without determinism.

## E5 — Iteration (optional; strengthens toward a stronger venue)

Show the full loop closes: explain-back surfaces a gap, "Pat" corrects it in
English, the next build fixes it. Demonstrate end-to-end on a couple of cases
(e.g., the run_2 Herb gap: Pat says "Herb should ask the custodian for holdings"
-> rebuild -> the edge appears).

## E6 — Composition (answers the "only works for small offices" criticism)

Question: can Pat build small offices and combine them into a bigger one, with the
methodology still working? (See DIRECTIONS.md #3.)
- Build two small offices independently (e.g., support_desk + a small-business
  accounts office), then compose — wire one's outputs to the other's inputs, or
  nest one as a single agent ("department") in a larger chart.
- Test: (a) the composed office is a **valid** office; (b) the explain-back works
  **per level** — Pat understands and can correct the composition without having
  to comprehend the whole thing at once; (c) **determinism is preserved** — if
  each sub-office is determinate and the gluing wiring adds no uncontrolled merge,
  the composition is determinate (Kahn compositionality).
- New coordination questions to probe: a record shared across two offices may need
  a **gate spanning both**; an office-as-agent should expose a clean **contract**
  that hides its internal coordination (encapsulation).
- Payoff: converts the scalability objection into a compositionality result — a
  second contribution, not just a rebuttal.

## First-paper core vs. reach

- Core (self-contained): E1 + E2 + E3(a,b) + E4-ablation.
- Reach (stronger venue): add E3c (human study) and E5.

## Threats to validity (name them in the paper)

- **Model as its own judge** — E3b scoring and E1 diagnosis are currently done by
  the same model family. Use pre-registration (done for plant-a-gap), independent
  runs, and human scoring for the headline numbers.
- **Contamination** — offices may resemble training data. Use novel offices,
  rotate the shot, and report whether results degrade on the most novel office.
- **"Valid" is a judgment** — define a rubric and, where possible, a runnable
  check (does the compiled office run and produce output?).
- **Pilot vs rate** — one office's mutants are a pilot, not a measured rate.

## Known coverage limit to feature honestly

Plant-a-gap pre-registration predicts the explain-back catches defects that change
an item's journey or that the checklist probes (serialization, joins, ask-and-
wait, missing input to a consumer) and MISSES silent omissions (unlogged write)
and liveness bugs (deadlock from a missing done-signal). If confirmed, this maps
the explain-back's envelope and motivates a complementary **static structural
check** as the systems-layer partner to the HCI explain-back -- a strength of the
two-layer framing, not a weakness.
