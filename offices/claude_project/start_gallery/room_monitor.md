# Gallery example — room_monitor (restraint: a single-stream pipeline, no coordinator)

Teaches: **when to use nothing.** One source, a short line of transforms, one sink —
**no coordinator, no keeper, no record.** This is the counterweight to the
coordination-heavy examples (debate, trading_room): the most common way a generated
office goes wrong is adding machinery the description doesn't need.

---

## Pat's description

> "I have a microphone in a room. Watch the sound and alert me on the console when
> something unusual happens — a loud noise, an unusual silence, or someone talking."

---

## Phase 1 — the network

**Agents**

- **MIC** — *source*. Outbox `out`. Streams sound readings from the microphone.
- **MONITOR** — *transform*. Inbox `in`. Outbox `out`. Keeps a short memory of the
  room's normal sound; for each reading decides whether it is normal, a loud noise, an
  unusual silence, or someone talking; sends an alert when something is unusual and
  nothing otherwise.
- **CONSOLE** — *sink*. Inbox `in`. Shows each alert.

**Connections**

- (MIC, out, MONITOR, in)
- (MONITOR, out, CONSOLE, in)

What the shape shows: there is **one** source stream, so there is nothing to
fair-merge and **no coordinator**. MONITOR's memory is **its own** — nothing is shared
or written jointly — so there is **no gate and no record**. Results go to one place,
so a single outbox to a single sink. The whole office is a short line of workers, and
that is exactly the right amount of machinery.

**Explain it back to Pat** (plain English, "workers"):

> A single worker listens to the microphone. It keeps a short sense of what the room
> normally sounds like, and whenever something stands out — a loud noise, an unusual
> stretch of silence, or someone talking — it puts a short alert on the console. The
> rest of the time it stays quiet.
>
> **Things I assumed —** "unusual" means a loud noise, a long silence, or speech; the
> worker learns what's "normal" from the recent past (for the first little while it
> just listens to calibrate); and every alert goes to the one console. Tell me if you
> meant something different by "unusual," or if you also want the alerts kept
> somewhere.

## Phase 2 — the agent descriptions

- **MIC** *(source)* — the room's microphone; streams a sound reading many times a
  second (for example, a loudness sample).
- **MONITOR** *(transform)* — keeps a short rolling memory of recent sound to learn the
  room's normal level. For each reading: if it is much louder than normal, alert "loud
  noise"; if the room stays near silence longer than usual, alert "unusual silence"; if
  the sound has the on-and-off pattern of speech, alert "someone talking"; otherwise
  send nothing. (Whether "someone talking" is later a simple rule or a small audio
  model is decided in a later step, not here.)
- **CONSOLE** *(sink)* — the screen where alerts are shown.

---

## Pat's correction (small)

> "Also keep a log of the alerts in a file, not just on the console."

The same alerts now go to two places. MONITOR's one outbox feeds **both** sinks — a
**fan-out** — and a second sink is added. Nothing else changes; still no coordinator.

**Agents added**

- **ALERT_LOG** — *sink*. Inbox `in`. Records each alert.

**Connections**

- (MONITOR, out, CONSOLE, in)  *(unchanged)*
- (MONITOR, out, ALERT_LOG, in)  *(new)*

**Show Pat what changed:**

> The same alerts now go two places at once — the console and a log file. Nothing else
> about the office changes.

---

## What this example teaches

- **One source stream → no fair-merge, no coordinator.** A single incoming stream needs
  no merging.
- **A worker's memory is its own → no gate, no record.** Nothing here is shared or
  jointly written, so there is no shared state to protect.
- **The simplest good office is a short line of workers.** Don't add machinery Pat
  didn't ask for — this is the restraint the coordination-heavy examples don't show.
- **Sending the same result to two places is a fan-out** (one outbox → two sinks), not
  a coordinator.
- A transform's English description can imply either a simple rule or a model
  ("someone talking"); that implementation choice is downstream, not part of this step.
