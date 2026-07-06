# Clean Claude experiments

Experiments where Claude is given a Pat-style spec in a **fresh session**
with **no prior context** about NoT / OfficeSpeak / pseudocode / our
methodology. Goal: see what Claude actually produces for typical
Pat-style users.

## Directory structure

```
clean_runs/
  <app_name>/
    spec.md            Pat's English specification (paste this content)
    prompt_run1.txt    The exact prompt to paste into a fresh Claude window
    prompt_run2.txt    (optional) Prompt with small style sheet
    response_run1.py   Claude's actual response, pasted from the new window
    response_run2.py   ...
    notes.md           Observations after reading the responses
```

## Workflow

1. Open a fresh Claude session (claude.ai or API) — no system prompt,
   no project context, no prior conversation. Start from blank.
2. Paste the contents of `prompt_runN.txt`.
3. Claude responds with code (and possibly some prose around it).
4. Copy the code portion into `response_runN.py`.
5. Save any extra notes (which model used, when, anything unusual)
   in `notes.md`.

## Apps to test (in priority order)

| App | Why this app | Status |
|---|---|---|
| `situation_room` | Multi-source, LLM-only enrichers, conditional output. Canonical. | TODO |
| `loudness_monitor` | Stateful Python agents, sensor-style source. Tests classes-emerge-naturally. | TODO |
| `inbox_triage` | Three-way router with distinct sinks. Tests routing structure. | TODO |
| `outlier_detector` | Sliding-window stateful Python agent. Tests state pattern. | TODO |
| `debate` | Feedback loop with bounded iterations. Tests cycle expression. | TODO |
