# investment_club / run_1 — analytical explain-back (captured experiment result)

Input: `runs/run_1/actual_graph.md`. Prompt: `offices/prompt_explain.md`, run in a
mode that also surfaced developer-facing coordination issues. This is the artifact
point (1) asks us to keep: the graph (run_1) plus **an explanation that points out
errors**. It found three latent issues our earlier Pat-facing explanation missed.

---

## Pat-facing explanation

This office watches the markets and the news and decides what the club should do
with its money — buy, sell, or hold — and records every decision.

The team: Yahoo, Bloomberg, and a few news feeds are where information comes in —
prices, forecasts, and breaking news. Gus lets one piece of news in at a time.
Warren is your value analyst and Bill your opportunities analyst; each reads the
news and makes a case for what to do. Meg waits until both of them have weighed in
before passing their two arguments along together. Herb is your tax-and-fees
analyst; he prices out what a proposed move would cost. Don is the decision-maker
who weighs the arguments and makes the final call. Rachel keeps all the shared
records — the club's real holdings, every argument and decision, and a separate
practice portfolio for each analyst that tracks how that person's advice would
have done on its own. Decisions get written out where you can see them.

When a piece of information arrives, whichever feed got there first, Gus lets it
in — just one at a time — and hands it to Warren, Bill, Herb, and Don all at once.
Warren and Bill each read it, check their own records with Rachel, and write up
their argument; each sends his argument to Meg and tells Rachel to update his
practice portfolio. Meg waits until she has both arguments, then passes the pair
to Don. Don reads the item and both arguments, sketches a proposed move, and asks
Herb what it would cost in taxes and fees. Herb reports back, and only then does
Don make the final call: he writes the decision out, tells Rachel to update both
the club's real holdings and his own practice portfolio, and signals Gus he's
done. Only then does Gus let the next piece of information in.

Baked-in choices — one piece of information at a time, with nothing new admitted
until Don finishes the current one; Don has the final say and the two analysts
only advise; Don won't finalize until Herb has priced the taxes and fees, a small
back-and-forth between them; Meg makes Don wait for both analysts, so he never
decides on a single voice; and Rachel alone keeps the records — on top of the real
holdings, she keeps a separate practice portfolio for each analyst, so you can see
whose advice is actually paying off. Tell me if any of these should be different.

## Developer-facing: three spots where rendering the graph forced a paper-over

1. **Don's two inbound streams don't have an explicit join.** Don gets the raw
   item from Gus and the argument pair from Meg, but there is no `merge_synch` at
   Don over `[Gus-item, Meg-pair]`. The explanation only works because the gate
   guarantees one item in flight, so the two always line up. Relax the gate and
   this silently breaks. Either add the join at Don, or have Meg carry the item
   forward so Don has a single inbound. **[WIRING problem.]**

2. **Herb gets the item from Gus but does nothing with it until Don proposes.**
   Pat would reasonably ask why Herb receives the news up front if he just waits.
   Cleaner to drop Herb from Gus's fan-out and let Don pass the item alongside the
   proposed action. The broadcast/fan-out primitive showing its seams.
   **[WIRING problem.]**

3. **Model-portfolio timing is underspecified.** Warren and Bill update their
   practice portfolios at proposal time, as if their own recommendation executes,
   independent of what Don decides. The graph doesn't say how they price the
   hypothetical trade, and the analyst models never reconcile against Don's actual
   decision. For "whose advice would have won" to mean anything, each analyst's
   model probably also needs to record what Don actually did. **[AGENT-SPEC
   problem — read from the description of what Warren/Bill do, not from the
   wiring.]**

## Classification (for the wiring-vs-spec discussion)

- Issues 1 and 2 are **wiring** problems — found by reading the topology.
- Issue 3 is an **agent-specification** problem — found by reading the job
  descriptions, correct and helpful, but about *behavior*, not connections.
- (Separately, mutant M6 — a missing gate-release — is also an agent-coding
  problem, not wiring: the "done" signal is a protocol obligation a correct body
  emits, not an independent edge Pat would choose. See mutants.md M6 note.)

The corrected topology (issues 1-2 fixed) is `../../reference_graph.md`; the
diagram Pat would see is `../../reference_graph.mermaid`. Issue 3 is recorded as an
open Pat-question there.
