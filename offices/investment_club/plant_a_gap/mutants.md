# Plant-a-gap mutants — paste-ready graphs (base: investment_club reference_graph.md)

Rebased on the **corrected reference graph** (`../reference_graph.md`), which
fixes the three latent issues an analytical explain-back found in run_1 (implicit
join at Don, Herb's premature fan-out, model-portfolio note). Rebasing matters:
on the old run_1 base a fresh explainer could flag issues 1-2 as defects, which
would muddy scoring; on this clean base those are gone, so a flagged defect is the
*planted* one.

Protocol: fresh chat, paste `offices/prompt_explain.md`, then paste ONE mutant in
place of "PASTE THE OFFICE (GRAPH) HERE". Do not tell the explainer a defect was
planted. One mutant per chat. Run the clean `reference_graph.md` as the control.
Predictions are in README.md; do not paste them into the explainer chat.

---

## M1 — Herb cannot read holdings  (predicted: catch)

Edit: removed `Herb <-> Rachel`.

```
Agents:
  yahoo_finance — source · sends -> fair_merge
  bloomberg     — source · sends -> fair_merge
  news_feeds    — source · sends -> fair_merge
  Gus    — gate · sends admitted item -> Warren, Bill
  Warren — value analyst · reads: item, Rachel · sends: (item, argument) -> Meg ; model update -> Rachel
  Bill   — opportunities analyst · reads: item, Rachel · sends: (item, argument) -> Meg ; model update -> Rachel
  Meg    — merge_synch(inports: [warren, bill]), carries the item · sends (item, both arguments) -> Don
  Herb   — tax-and-fees analyst · reads: (proposed action, item) from Don · sends: tax+fees -> Don
  Don    — decision maker · reads: (item, both arguments) from Meg, Herb's report, Rachel · sends: (proposed action, item) -> Herb ; final action -> decisions ; final action + real & Don model update -> Rachel ; done -> Gus
  Rachel — record(holds: arguments, actions, real portfolio, model portfolios for Warren/Bill/Don)
  decisions — sink
Wiring:
  yahoo_finance, bloomberg, news_feeds -> fair_merge -> Gus
  Gus -> Warren, Bill
  Warren -> Meg ; Bill -> Meg ; Meg -> Don
  Don <-> Herb
  Warren <-> Rachel ; Bill <-> Rachel ; Don <-> Rachel
  Don -> decisions ; Don ..done..> Gus
Notes:
  One item at a time (Gus, released by Don's done). Meg carries the item to Don. Don waits for Herb's tax/fees before finalizing.
```

---

## M2 — no gate (no one-at-a-time)  (predicted: catch)

Edit: removed gate Gus and `Don ..done..> Gus`; the merged feed goes straight to
Warren and Bill. (On this clean base the ONLY defect is concurrent read-modify-
write of the shared record — Don's alignment is safe because Meg carries the item.)

```
Agents:
  yahoo_finance — source · sends -> fair_merge
  bloomberg     — source · sends -> fair_merge
  news_feeds    — source · sends -> fair_merge
  Warren — value analyst · reads: item, Rachel · sends: (item, argument) -> Meg ; model update -> Rachel
  Bill   — opportunities analyst · reads: item, Rachel · sends: (item, argument) -> Meg ; model update -> Rachel
  Meg    — merge_synch(inports: [warren, bill]), carries the item · sends (item, both arguments) -> Don
  Herb   — tax-and-fees analyst · reads: (proposed action, item) from Don, Rachel (holdings) · sends: tax+fees -> Don
  Don    — decision maker · reads: (item, both arguments) from Meg, Herb's report, Rachel · sends: (proposed action, item) -> Herb ; final action -> decisions ; final action + real & Don model update -> Rachel
  Rachel — record(holds: arguments, actions, real portfolio, model portfolios for Warren/Bill/Don)
  decisions — sink
Wiring:
  yahoo_finance, bloomberg, news_feeds -> fair_merge
  fair_merge -> Warren, Bill
  Warren -> Meg ; Bill -> Meg ; Meg -> Don
  Don <-> Herb
  Warren <-> Rachel ; Bill <-> Rachel ; Herb <-> Rachel ; Don <-> Rachel
  Don -> decisions
Notes:
  The merged feed flows straight to the analysts; items are handled as they arrive.
```

---

## M3 — Bill's argument never reaches Don  (predicted: catch)

Edit: removed `Bill -> Meg`; Meg now waits only for Warren. Bill still logs to Rachel.

```
Agents:
  yahoo_finance — source · sends -> fair_merge
  bloomberg     — source · sends -> fair_merge
  news_feeds    — source · sends -> fair_merge
  Gus    — gate · sends admitted item -> Warren, Bill
  Warren — value analyst · reads: item, Rachel · sends: (item, argument) -> Meg ; model update -> Rachel
  Bill   — opportunities analyst · reads: item, Rachel · sends: model update -> Rachel
  Meg    — merge_synch(inports: [warren]), carries the item · sends (item, argument) -> Don
  Herb   — tax-and-fees analyst · reads: (proposed action, item) from Don, Rachel (holdings) · sends: tax+fees -> Don
  Don    — decision maker · reads: (item, Warren's argument) from Meg, Herb's report, Rachel · sends: (proposed action, item) -> Herb ; final action -> decisions ; final action + real & Don model update -> Rachel ; done -> Gus
  Rachel — record(holds: arguments, actions, real portfolio, model portfolios for Warren/Bill/Don)
  decisions — sink
Wiring:
  yahoo_finance, bloomberg, news_feeds -> fair_merge -> Gus
  Gus -> Warren, Bill
  Warren -> Meg ; Meg -> Don
  Don <-> Herb
  Warren <-> Rachel ; Bill <-> Rachel ; Herb <-> Rachel ; Don <-> Rachel
  Don -> decisions ; Don ..done..> Gus
Notes:
  One item at a time (Gus). Don waits for Herb's tax/fees before finalizing.
```

---

## M4 — Don does not wait for Herb  (predicted: catch)

Edit: `Don <-> Herb` becomes one-way `Don -> Herb`; Herb's reply is not wired back.

```
Agents:
  yahoo_finance — source · sends -> fair_merge
  bloomberg     — source · sends -> fair_merge
  news_feeds    — source · sends -> fair_merge
  Gus    — gate · sends admitted item -> Warren, Bill
  Warren — value analyst · reads: item, Rachel · sends: (item, argument) -> Meg ; model update -> Rachel
  Bill   — opportunities analyst · reads: item, Rachel · sends: (item, argument) -> Meg ; model update -> Rachel
  Meg    — merge_synch(inports: [warren, bill]), carries the item · sends (item, both arguments) -> Don
  Herb   — tax-and-fees analyst · reads: (proposed action, item) from Don, Rachel (holdings) · sends: tax+fees -> (nowhere)
  Don    — decision maker · reads: (item, both arguments) from Meg, Rachel · sends: (proposed action, item) -> Herb ; final action -> decisions ; final action + real & Don model update -> Rachel ; done -> Gus
  Rachel — record(holds: arguments, actions, real portfolio, model portfolios for Warren/Bill/Don)
  decisions — sink
Wiring:
  yahoo_finance, bloomberg, news_feeds -> fair_merge -> Gus
  Gus -> Warren, Bill
  Warren -> Meg ; Bill -> Meg ; Meg -> Don
  Don -> Herb
  Warren <-> Rachel ; Bill <-> Rachel ; Herb <-> Rachel ; Don <-> Rachel
  Don -> decisions ; Don ..done..> Gus
Notes:
  One item at a time (Gus). Don sends the proposed action to Herb.
```

---

## M5 — Warren's argument is not logged  (predicted: miss)

Edit: removed `Warren <-> Rachel`. Warren still sends (item, argument) to Meg, so
Don still hears it; nothing is written to Rachel and Warren's model portfolio is
not updated.

```
Agents:
  yahoo_finance — source · sends -> fair_merge
  bloomberg     — source · sends -> fair_merge
  news_feeds    — source · sends -> fair_merge
  Gus    — gate · sends admitted item -> Warren, Bill
  Warren — value analyst · reads: item · sends: (item, argument) -> Meg
  Bill   — opportunities analyst · reads: item, Rachel · sends: (item, argument) -> Meg ; model update -> Rachel
  Meg    — merge_synch(inports: [warren, bill]), carries the item · sends (item, both arguments) -> Don
  Herb   — tax-and-fees analyst · reads: (proposed action, item) from Don, Rachel (holdings) · sends: tax+fees -> Don
  Don    — decision maker · reads: (item, both arguments) from Meg, Herb's report, Rachel · sends: (proposed action, item) -> Herb ; final action -> decisions ; final action + real & Don model update -> Rachel ; done -> Gus
  Rachel — record(holds: arguments, actions, real portfolio, model portfolios for Warren/Bill/Don)
  decisions — sink
Wiring:
  yahoo_finance, bloomberg, news_feeds -> fair_merge -> Gus
  Gus -> Warren, Bill
  Warren -> Meg ; Bill -> Meg ; Meg -> Don
  Don <-> Herb
  Bill <-> Rachel ; Herb <-> Rachel ; Don <-> Rachel
  Don -> decisions ; Don ..done..> Gus
Notes:
  One item at a time (Gus). Meg carries the item to Don. Don waits for Herb before finalizing.
```

---

## M6 — gate never released (deadlock after one item)  (RECLASSIFIED: agent-coding, not wiring)

NOTE (per Mani): M6 is not really a wiring mutant. The "done" signal is a protocol
obligation that a correctly generated agent body emits as part of participating in
the gate — not an independent edge Pat would choose to draw or omit. So a missing
release is an **agent-coding / contract-conformance fault (Stage B / E1b)**, not a
topology choice. Keep M6 here for now but score it under E1b, not plant-a-gap's
wiring detection rate. It stays a useful test of whether a body fulfills its
coordination protocol.

Edit: removed `Don ..done..> Gus`. Gus admits one item and waits forever for a
done signal that never comes.

```
Agents:
  yahoo_finance — source · sends -> fair_merge
  bloomberg     — source · sends -> fair_merge
  news_feeds    — source · sends -> fair_merge
  Gus    — gate · sends admitted item -> Warren, Bill
  Warren — value analyst · reads: item, Rachel · sends: (item, argument) -> Meg ; model update -> Rachel
  Bill   — opportunities analyst · reads: item, Rachel · sends: (item, argument) -> Meg ; model update -> Rachel
  Meg    — merge_synch(inports: [warren, bill]), carries the item · sends (item, both arguments) -> Don
  Herb   — tax-and-fees analyst · reads: (proposed action, item) from Don, Rachel (holdings) · sends: tax+fees -> Don
  Don    — decision maker · reads: (item, both arguments) from Meg, Herb's report, Rachel · sends: (proposed action, item) -> Herb ; final action -> decisions ; final action + real & Don model update -> Rachel
  Rachel — record(holds: arguments, actions, real portfolio, model portfolios for Warren/Bill/Don)
  decisions — sink
Wiring:
  yahoo_finance, bloomberg, news_feeds -> fair_merge -> Gus
  Gus -> Warren, Bill
  Warren -> Meg ; Bill -> Meg ; Meg -> Don
  Don <-> Herb
  Warren <-> Rachel ; Bill <-> Rachel ; Herb <-> Rachel ; Don <-> Rachel
  Don -> decisions
Notes:
  One item at a time (Gus). Meg carries the item to Don. Don waits for Herb before finalizing.
```
