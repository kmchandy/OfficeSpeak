# Full-chain case 01 — shipment release

First run of the *entire* chain: cold Phase 1/2 conversation -> approve
office-specific workers (`phase3_approval.md`) -> generate
(`from_officespeak.py`) -> run the office and check the output by hand.
Pre-registration: `full_chain_case_01_pre_registration.md`. Everything
through "Round 1" and "Round 2" below is a cold subagent, given only the
five standard files and told to read nothing else. Everything after
"Transcription and generation" is me, not cold, as the pre-registration
said it would be.

## Round 1 — first draft (a real miss)

Pat's request, given verbatim: "I want an office that releases a shipment
only after both its warehouse scan and its manifest paperwork have come
in. Match them up by shipment ID, then send the release notice to the
loading dock."

The cold instance produced:

- `SCAN` (source) and `MANIFEST` (source), each naming a shipment ID.
- `MATCH` — declared as a **merge_synch** coordinator, inboxes `scan` /
  `manifest`, outbox `out`.
- `DOCK` (sink).

Its own explain-back described `MATCH` as holding onto whichever of the
two arrives first "for a given shipment" and combining them once both
arrive "for that shipment," and its "Things I assumed" section stated:
"many shipments move through at once, and each message... names which
shipment it's about, so the waiting worker can track several shipments'
partial information at the same time without mixing them up."

This is exactly the pre-registered risk. `merge_synch` (see
`dissyslab/blocks/merge_synch.py`) fills one slot per inport *per round*
and emits once both slots are full — it has no concept of a shipment ID
at all. It pairs the *n*-th scan with the *n*-th manifest, full stop. The
cold instance's own English description of what it wanted ("track several
shipments... without mixing them up") is not what the primitive it chose
actually does. This was scored a miss, not a defensible alternative
reading — confirmed concretely below.

## Round 2 — correction (fixed)

Following the same correction protocol used for `investment_club`'s Case
2, a fresh cold instance was given round 1's build plus this correction,
in Pat's voice: "Shipments don't move through in lockstep. Sometimes a
later shipment's scan comes in before an earlier shipment's manifest
paperwork, or the other way around. It has to match by the actual
shipment ID printed on the paperwork, not by which one happens to show up
first for each kind of check-in."

The corrected design: `MATCH` becomes a plain **transform** with a
memory, keyed by shipment ID — the same shape as `trading_room`'s
`LEDGER` — not a registered coordinator. Its own words: "it keeps a
little note of whichever piece has shown up so far... it always checks
the ID," and "MATCH keeps a separate note for each shipment ID rather
than one shared note." This is the right shape, and its explanation this
time is actually consistent with what it built.

## Concrete confirmation that round 1 was a real bug, not a nitpick

Fed the same interleaved event order used below (scans in order S101,
S103, S102; manifests in order S102, S101, S103 — deliberately
non-matching order across shipments) directly into a real
`dissyslab.blocks.merge_synch.MergeSynch`:

```
round: scan=S101 manifest=S102 -> MISMATCH
round: scan=S103 manifest=S101 -> MISMATCH
round: scan=S102 manifest=S103 -> MISMATCH
```

Every single round pairs the wrong shipment's scan with the wrong
shipment's manifest. Round 1's design, run for real, would release every
shipment against the wrong paperwork.

## Transcription and generation (not cold)

The corrected Phase 1 design was transcribed into an `OfficeSpeakSpec`:
`SCAN`, `MANIFEST`, `MATCH` as approved Python transforms (each a
zero-arg factory per `phase3_approval.md`), `STARTER` (source, registered
as `starter`), `DOCK` (sink, `jsonl_recorder`) and a `CONSOLE` sink
(`console_printer`) for visibility. `MATCH`'s body: a `pending` dict keyed
by shipment ID; on each message it checks whether the *other* kind is
already waiting for that ID — if so, releases and clears the entry; if
not, stores its own kind and waits.

`build_office_from_officespeak` generated `office.md` plus three role
files with no errors. Output `office.md`:

```
Sources: starter
Sinks: jsonl_recorder(path='releases.jsonl'), console_printer

Agents:
SCAN is a scan.
MANIFEST is a manifest.
MATCH is a match.

Connections:
starter's destination are SCAN and MANIFEST.
SCAN's out is MATCH.
MANIFEST's out is MATCH.
MATCH's out are jsonl_recorder and console_printer.
```

## Run

`dsl run` on the generated office, with `SCAN` emitting shipment IDs in
order S101, S103, S102 and `MANIFEST` emitting S102, S101, S103 (the same
deliberately-interleaved-across-shipments order used in the confirmation
above, so the same office that would break `merge_synch` is the one this
generated office actually has to handle correctly). Console output:

```
[Match] shipment S101: got scan, waiting on manifest
[Match] shipment S103: got scan, waiting on manifest
[Match] shipment S102: got scan, waiting on manifest
[Match] shipment S102: both scan and manifest in -- releasing
[Match] shipment S101: both scan and manifest in -- releasing
[Match] shipment S103: both scan and manifest in -- releasing
```

`releases.jsonl`:

```json
{"shipment_id": "S102", "release": true}
{"shipment_id": "S101", "release": true}
{"shipment_id": "S103", "release": true}
```

All three shipments released, each against its own correct paperwork,
regardless of arrival order — the exact case that would have silently
mismatched under round 1's design.

## Verdict

PASS overall, but only after one correction round. This is the first
validation of the whole chain end to end (cold Phase 1/2 -> approval ->
generation -> a real run), and it did its job: caught a real design
error before it reached generated code, not after. Task #19 ("build
reference implementations + cold-test the full chain") is satisfied by
this case. Task #34 (source/sink matching) remains open and required
before an external tester — this case still had me doing that matching
by hand (`STARTER` -> `starter`, `DOCK` -> `jsonl_recorder`), same as
`trading_room`/`investment_club`.
