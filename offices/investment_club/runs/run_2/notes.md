# investment_club / run_2 — diagnostic (local-state substrate)

Question: same office, message-passing substrate — does the mapping stay
faithful and does the coordination survive without a shared record?

## Substrate respected — fully
- No shared memory. Claude used all three sharing patterns correctly:
  - **keeper agents**: Nora owns the log (others write to her, ask her);
    Bruno owns the real portfolio.
  - **broadcast + local copy**: the merged feed goes to every agent, each
    keeping its own copy ("all information reaches every agent").
  - **fully local**: Warren, Bill, Don each hold their *own* model
    portfolio in private state — no central store.

## Coordination survived the substrate swap
- **gate** (Gus) — kept; release moved to **Bruno** (the real-portfolio
  owner), fired after the portfolio updates. Correct.
- **merge_synch** — kept for Don's join (both arguments, same item).
- **select** — kept for the Don<->Herb ask-and-wait.

## Refinements over run_1 and our intended graph (substrate drove them)
- **Bruno (custodian) split from Don (decider):** the real portfolio got
  its own owner, separate from the decision-maker — like a real fund
  (decision vs custody). Cleaner, and forced by "someone must own the
  portfolio."
- **Nora (archivist) split from Bruno (custodian):** two keepers for two
  distinct pieces of shared state (the log vs the real portfolio).
- Sophisticated serialization reasoning: one-at-a-time keeps the real and
  three model portfolios "advancing in step and comparable."

## One real gap (Pat-catchable)
- **Herb's cost basis.** Herb keeps his *own* "tax basis" and is not wired
  to ask Bruno (who owns the real portfolio) for current holdings. Tax
  depends on actual holdings/cost basis, so Herb could compute on a stale
  or disconnected copy. In run_1 (shared memory) Herb read Rachel for
  holdings — correct. Here that link is missing. A cleaner design: Herb
  asks Bruno (or Nora) for current holdings before the tax math. This is
  exactly the kind of thing the explain-back should surface and Pat would
  catch ("does Herb know what we actually hold?").

## Same under-specified area (not a miss)
- "Try to do better": each agent keeps its own model portfolio (raw
  material); whether/how Don reweights advisors by track record is left
  open, consistent with the spec.

## Verdict
Portability holds: one English office, two substrates, two faithful and
arguably-better graphs, with only the prompt changed — and all three
coordination primitives survived the swap. One subtle correctness gap
(Herb's holdings source). Strong second data point.
