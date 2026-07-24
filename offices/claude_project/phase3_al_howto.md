# A how-to for Al — from Pat's hand-off file to a running office

This walks the whole thing end to end on a real case, with real commands and
real output — not a hypothetical. If you're Al, this is the one document to
follow start to finish; it points at `phase3_source_sink_matching.md`,
`phase3_approval.md`, and `phase3_assistant_instructions.md` where you need
more depth on one step, but you shouldn't need to read those cold.

## 0. What you start with

Pat's Track A conversation ends with one file — call it
`<office>.officespeak.py`. Here it is for this walkthrough, a real hand-off
file from a real Track A conversation (room temperature/humidity
monitoring — alert facilities when a reading is both too hot and too humid):

```python
OFFICE_NAME = "room_climate_monitor"

AGENTS = [
    dict(name="TEMP_SENSOR", kind="source", in_ports=[], out_ports=["out"],
         description="The room's temperature sensor; emit one temperature reading (value and timestamp) every few minutes.",
         registered_as=None, registered_args={}),
    dict(name="HUMIDITY_SENSOR", kind="source", in_ports=[], out_ports=["out"],
         description="The room's humidity sensor; emit one humidity reading (value and timestamp) every few minutes, on the same cadence as the temperature sensor so readings can be paired.",
         registered_as=None, registered_args={}),
    dict(name="JOIN", kind="coordinator", in_ports=["temp", "humidity"], out_ports=["out"],
         registered_as="merge_synch", registered_args={}),
    dict(name="CHECKER", kind="transform", in_ports=["in"], out_ports=["alert"],
         description="Read a paired temperature-and-humidity reading for the same time. If the temperature is above the 'too hot' threshold and the humidity is above the 'too humid' threshold at the same time, write a short alert describing both readings and send it on alert. Otherwise send nothing.",
         body_kind=None, body_fn=None, body_prompt=None, approved=False),
    dict(name="FACILITIES", kind="sink", in_ports=["in"], out_ports=[],
         description="The concrete place the facilities team receives alerts (for example, an email inbox, a ticketing system, or a shared alerts channel); deliver each alert there.",
         registered_as=None, registered_args={}),
]

CONNECTIONS = [
    ("TEMP_SENSOR", "out", "JOIN", "temp"),
    ("HUMIDITY_SENSOR", "out", "JOIN", "humidity"),
    ("JOIN", "out", "CHECKER", "in"),
    ("CHECKER", "alert", "FACILITIES", "in"),
]
```

Everything above came from Track A. Nothing about names, ports, or
connections is yours to redecide — your job is only the blanks: three
`registered_as=None`, one `approved=False`.

## 1. Set up once

```bash
pip install dissyslab
python -c "import dissyslab; print('DisSysLab OK')"
```

Pick a backend for any judgment (LLM) workers this office turns out to need
— an API key, e.g. `export OPENROUTER_API_KEY=...`. This particular office
has none (both workers below turn out to be plain computation), so this step
is a no-op for this walkthrough, but don't skip checking.

## 2. Open a conversation and hand it the file

Start a chat with Claude — same as Pat's Project, but paste
`phase3_assistant_instructions.md` as its instructions instead of
`start_instructions.md`, and give it this hand-off file. Something like:
"Here's a hand-off file from a Track A conversation. Help me finish it." is
enough; the instructions tell it what to do from there.

## 3. Match the sources and sinks

`TEMP_SENSOR` / `HUMIDITY_SENSOR`: Claude checks `docs/SOURCES_AND_SINKS.md`
and reports back — correctly — that nothing registered matches a physical
room sensor (the catalogue has `weather`, RSS feeds, `gmail`, `calendar`,
`webhook`, and a couple of others; no room-sensor integration). The honest
move, since this is for building and testing rather than a real deployment:
reclassify both from `kind="source"` to `kind="transform"`, standing in with
a small fixed sequence of readings, fed by DisSysLab's `starter`. This is a
bigger edit than filling in a blank — a real reclassification — and it's
exactly the kind of call `phase3_source_sink_matching.md`'s "when nothing
fits" section exists for.

`FACILITIES`: "an email inbox, a ticketing system, or a shared alerts
channel" matches several registered sinks — `gmail_sink` (needs your Gmail
app password), `slack_sink` (needs a webhook URL), or `console_printer` (no
setup at all). For this walkthrough, pick `console_printer` — no
credentials needed, good enough to prove the office works before wiring up
a real notification channel later.

## 4. Draft and approve the workers

`TEMP_SENSOR` / `HUMIDITY_SENSOR` (now transforms): a fixed sequence of
readings standing in for the real sensor, deliberately including at least
one clearly-hot-and-humid pair and at least one that isn't, so the alert
logic actually gets exercised both ways once wired up:

```python
def _make_temp_fn():
    _READINGS = [70.0, 82.0, 79.0, 85.0]
    def temp_fn(msg):
        return [({"temp": v}, "out") for v in _READINGS]
    return temp_fn

def _make_humidity_fn():
    _READINGS = [45.0, 65.0, 55.0, 70.0]
    def humidity_fn(msg):
        return [({"humidity": v}, "out") for v in _READINGS]
    return humidity_fn
```

Note the field names: `"temp"`/`"humidity"`, not both called `"value"` —
`JOIN` (`merge_synch`) dict-merges the two readings into one message, so
colliding field names would silently overwrite each other. This is exactly
Phase 1's own Pass A/B message-shape discipline, applied here for the first
time to real code instead of English.

`CHECKER`, from its Phase 2 description:

```python
def _make_checker_fn():
    def checker_fn(combined):
        temp = combined["temp"]
        hum = combined["humidity"]
        if temp > 80.0 and hum > 60.0:
            return [({"temp": temp, "humidity": hum, "alert": True}, "out")]
        return None
    return checker_fn
```

Tested on the four paired readings before approving, exactly as
`phase3_approval.md` asks: `(70, 45)` → nothing, `(82, 65)` → alert,
`(79, 55)` → nothing, `(85, 70)` → alert. Matches the threshold rule Phase 2
described. Approved.

`CHECKER`'s code above returns status `"out"`, matching Track A's `out_ports`
after the assembler's single-outport normalization. It didn't have to: the
assembler also accepts Track A's original name (`"alert"`) here, and
translates it automatically — a single-outport transform's code can return
either the readable name Track A gave it or `"out"`, whichever reads better
to whoever drafts and approves it. This used to be a real footgun (getting
it wrong caused a silent deadlock, a documented real case); it no longer is,
as of the `status_aliases` fix in `dissyslab/blocks/role.py`.

## 5. Generate

The finished file (every blank resolved) at
`dissyslab/office/draft_template.py`'s sibling — or wherever you saved it —
gets turned into a real office with one command:

```bash
python -m dissyslab.office.assemble room_climate_monitor.officespeak.py room_climate_monitor/
```

```
  Wrote room_climate_monitor/office.md and room_climate_monitor/roles/
  Next: dsl build room_climate_monitor   (or dsl run room_climate_monitor)
```

If anything's still unresolved, this fails here, loudly, naming exactly
which agent and which field — never generates a partial office.

## 6. Build and run

```bash
cd room_climate_monitor
dsl build .
dsl run .
```

Real output from this exact case:

```
[1] {'temp': 82.0, 'humidity': 65.0, 'alert': True}
[2] {'temp': 85.0, 'humidity': 70.0, 'alert': True}
```

Two alerts, exactly the two paired readings that were actually both hot and
humid at once — the other two produced nothing, correctly.

## If something goes wrong

`assemble.py` and `dsl build`/`dsl run` all raise errors that name the exact
agent and field at fault — read the message before doing anything else. Two
formerly-silent mistakes are now caught loudly instead:

- **Colliding field names into a `merge_synch`.** If two paired messages use
  the same field name, the merge now raises immediately, naming the inport
  and the colliding field, instead of silently letting one value overwrite
  the other. Fixed by using distinct field names (step 4, above) — the
  error message tells you exactly which ones collided if you forget.
- **A single-outport transform's code returning a status string.** No
  longer a footgun: the generator accepts either Track A's original name
  (e.g. `"alert"`) or `"out"` — both route to the same outport. Older
  advice said the code had to say `"out"` literally; it no longer has to.

## What to send back

If you're testing this process itself (not just building a real office):
which blank was hardest to resolve confidently, whether the matching
catalogue actually had what you needed, whether the approval step's
"show it working before approving" habit actually caught anything, and
whether the generated `office.md` matched what you expected before you
even ran it.
