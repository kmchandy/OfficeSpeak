# OfficeSpeak experiments — protocol (consistent across all offices)

Purpose: **showcase Claude's maximal expertise** building distributed sense-&-respond
offices from plain English. These are OfficeSpeak experiments (the Claude–Pat
conversation), distinct from DisSysLab's internal tests. Each office is run in a
**fresh chat with the full OfficeSpeak assistant** (primitives + prompts + a gallery
of *other* worked offices). The only held-out discipline: **the specific office is new
to the assistant** — its solution is not in context (no answer leakage). See
`EXPERIMENT_LAYOUT.md`.

## The seven steps — identical for every office

0. **Inputs ready:** `spec.md` (five-section), `spec_review.md` (pre-registered
   predictions + rubric), `build_package.md` (assistant context + the spec; this
   office not in the gallery).
1. **Build (gold standard):** fresh chat produces the office **graph** + the
   **explanation** (ending "Things I assumed —") + the **agent bodies** (Python for
   computational, LLM prompt for judgment). → `runs/run_1/graph_and_explanation.md`,
   `runs/run_1/agents/`.
2. **Explain-back scoring:** does the explanation surface the pre-registered
   assumptions / gotcha? → `runs/run_1/notes.md`.
3. **Correct:** Pat gives one plain-English correction → the assistant revises. →
   `runs/run_1/correction.md`.
4. **Run (substrate guarantees on Claude's own code):** wire the produced bodies into
   DSL (mechanical), run a bounded input → **termination detection + one checkpoint**.
   → `runs/run_1/run_output.txt`.
5. **Debug showcase:** produce the per-agent **debug dict**, then a **debug-explain**
   of one agent's tape for Pat. → `runs/run_1/debug_dict.json`,
   `runs/run_1/debug_explanation.md`.
6. **Record:** score against predictions in `notes.md`.

## Consistent artifact set per office

```
<office>/
  spec.md  build_package.md  spec_review.md          (inputs + our predictions)
  runs/run_1/
    graph_and_explanation.md   agents/   correction.md
    run_output.txt   debug_dict.json   debug_explanation.md   notes.md
  reference/                                           (our dev code; sanity check)
```

## Division of labor

- **Mani (fresh chats):** steps 1, 3, and the debug-explain in step 5 — paste back.
- **Claude (here):** pre-register predictions (spec_review), score (2, 6), wire and run
  the produced bodies (4), produce the debug dict (5).

## Coverage matrix — what each office showcases (paper's headline table)

| office | shape | coordination it showcases | Python / LLM | pre-registered gotcha |
|---|---|---|---|---|
| **investment_club** | deliberate-and-decide | **merge_synch** (join), **record** (shared), **gate**, **select** (ask-and-wait) | LLM analysts + Python accountant | accountant needs current holdings; "improve over time" not wired |
| **trading_desk** | async sense-&-respond | **fair_merge** (async sources), **select** loop (head↔risk), **TD with a loop** | Python chart + LLM news | head-trader decides on a stale price |
| **anomaly_monitor** | detect-anomaly | **router**, **per-key windowed state**, restraint: *no* fair_merge, *no* gate | all Python | threshold / window / cooldown unspecified |

Together these span the coordination library and three computational shapes, with a
Python-only, an LLM+Python, and an LLM-heavy office — "coverage, not count."

## Substrate per office

- **investment_club:** shared-memory (`prompt.md`) — showcases **record** + **gate**
  (unique to it). Portability to message-passing is its bonus result (the old run_2).
- **trading_desk, anomaly_monitor:** message-passing (`prompt_local_state.md`).

## Order

investment_club → trading_desk → anomaly_monitor. (trading_desk and anomaly_monitor
already have reference implementations that run; investment_club's runtime will be the
first to exercise merge_synch + record + gate on DSL.)
