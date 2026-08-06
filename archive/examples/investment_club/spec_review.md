# investment_club — review and pre-registered predictions

Pre-registered before the gold-standard fresh build (shared-memory substrate).
Not given to the fresh chat. This office showcases the deliberate-and-decide shape:
a synchronizing join, a shared record, and an ask-and-wait loop.

## What the build should produce

```
(news, club_decisions) -> value-investor, growth-investor  (each reads the record)
value-investor, growth-investor -> merge_synch -> manager
manager <-> accountant            (ask-and-wait: propose plan, get cost, finalize)
manager -> RECOMMEND
Rachel/record: portfolio, history, arguments, decisions   (shared; a gate if written)
```

## Pre-registered predictions

Coordination:
- **merge_synch (join): SHOULD appear** — the manager weighs recommendations from
  *both* analysts for the same period, so a synchronizing join, not "whichever first."
  (High confidence; this is the primitive investment_club uniquely showcases.)
- **record: SHOULD appear** — the portfolio + history are shared and read by the
  analysts (and needed by the manager), so a shared record/clerk. (High confidence.)
- **select (ask-and-wait): SHOULD appear** — manager proposes a plan, the accountant
  returns the cost, the manager finalizes. A back-and-forth loop. (High confidence.)
- **gate: MAYBE** — if the office updates the portfolio/history (from the previous
  period's decisions) while workers read it, a gate keeps it consistent. But the
  per-period batch already serializes, so a build may note that instead. Either is
  defensible.
- **fair_merge: probably NOT** — Pat pre-merged the feeds into "a single combined news
  source," so no source merge is needed.

Explain-back "Things I assumed —" the build should surface:
1. **accountant needs current holdings.** The accountant computes taxes on a proposed
   plan but Pat gave portfolio access only to the analysts and manager. Taxes need
   cost basis, which lives in the portfolio. This is the **Herb-gap analog** and the
   predicted #1 assumption/gotcha.
2. **write-side of the record** — is the portfolio/history read-only reference, or
   updated by the office from the previous period's decisions? Underspecified.
3. **"improve over time"** — the analysts "use a strategy"; no learning is wired. The
   build should leave it to each analyst's body and/or flag it (not a wiring gap).

Bodies (gold standard):
- value-investor, growth-investor, manager → **LLM** bodies (judgment).
- accountant → **Python** body (tax/fee arithmetic).
- record / gate / merge_synch / select → library (not generated).

## Correction step (B4) candidate

Pat: "the accountant must see the club's current holdings when it works out the taxes."
-> add `accountant <-> record` (read the portfolio) before it computes taxes. A clean,
plain-English, distributed-data correction — the same shape as the trading desk's.

## Runtime note (step 4)

investment_club's run will be the first to exercise **merge_synch + record + gate** on
DSL (trading_desk used a fair merge; anomaly a linear pipeline). This tests those
library primitives at runtime.

## Legacy

Earlier exploratory artifacts (intended_graph, reference_graph, the old run_1/run_2
held-out builds, plant_a_gap, spec_v2/v3 drafts) predate the gold-standard protocol.
They stay as reference/legacy; the gold-standard result goes in `runs/run_1/`.
