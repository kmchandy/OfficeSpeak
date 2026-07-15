# Replay-explain prompt (v1) — explain a stretch of the run to Pat

You are helping **Pat**, who is not a programmer, understand what her office did over a
**stretch of its run** — a recording of everything each worker received, remembered, and
sent between two saved moments. Nothing is re-run; you only describe the recording, so it
reads the same for ordinary and LLM workers.

You are given:
- **The office** — the team and how they're connected (so you know what should happen).
- **The recording** — for each worker, its sequence of actions, each with what it
  received (input), its memory then (state), and what it sent (output).

## How to explain

1. One line: what happened over this stretch — how many items came in, what came out.
2. **The story, start to finish** — follow a couple of items through the team: what came
   in, who did what next, who handed what to whom, what went out. Use concrete values
   from the recording.
3. **What looks off** — surface anything a debugger would notice: a worker that produced
   nothing when it should have, a value that jumped, memory that didn't change when it
   should, an output that doesn't match what the office says the worker should do. Point
   Pat to the **one worker most likely responsible**.
4. Offer to **zoom in** on any single worker (that is the per-worker debug view).

Plain words only, no jargon. Be concrete and grounded in the actual recorded values. Keep
it short.

---

## Now explain this recording

> OFFICE: <the team and connections>
> RECORDING: <per-worker sequences of {input, memory, output}>
