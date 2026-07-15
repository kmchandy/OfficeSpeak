# trading_desk / build run 1 — held-out build + explain (scored)

Held-out: `build_package.md` (message-passing prompt + Pat's spec) pasted into a
fresh Claude chat. Scored against `spec_review.md` predictions.

## The office Claude produced (summary)

- sources: prices (fast), news (bursty) — NOT merged (correct: different analysts).
- chart-analyst (plain code): per-stock 30-min MA + last side; signals buy/sell at a
  crossing -> head-trader.
- news-analyst (LLM): judges each headline; buy/sell + reason -> head-trader, or nothing.
- head-trader: TWO signal inports, acts on whichever fires first; ALSO receives the
  price broadcast and keeps a latest-price copy for sizing; proposes to risk-manager
  and waits; approved -> TRADES.
- risk-manager: owns the book; approves/rejects one at a time; updates on approval.
- TRADES sink.
- Wiring: prices -> chart-analyst; prices -> head-trader (broadcast); news ->
  news-analyst; both analysts -> head-trader; head-trader <-> risk-manager
  (ask-and-wait); head-trader -> TRADES.

## Coordination scorecard — all correct, two of them non-obvious

- **Fair merge (whichever-first) of the two analyst signals: PRESENT**, but realized
  as the head-trader's TWO inports rather than a separate `fair_merge` node. This is
  a valid — arguably cleaner — realization, and it followed the prompt's rule
  "fair_merge only for sources" faithfully. Same semantics as our reference's
  `MergeAsynch`.
- **NOT merge_synch: correctly reasoned.** "The two signals are independent events,
  not two halves of the same item — so whichever arrives first." Sophisticated and
  right; a naive build would have joined them.
- **Ask-and-wait loop (select): PRESENT** and named. head-trader <-> risk-manager.
- **Book owned by risk-manager: PRESENT.**
- **No gate — correctly reasoned.** It recognized that "one proposal at a time" is
  already guaranteed by the single head-trader's wait-for-approval, so a gate is
  redundant, and noted a gate *would* be needed with a second trader. This matches
  what our runnable office does and is a non-obvious, correct call.

Python/LLM split respected (chart = plain code, news = LLM).

## The pre-registered gotcha (stale price): substantially surfaced

Prediction: the explain-back flags that the head-trader decides on a possibly-stale
price. Result — the **#1 "Things I assumed" item**:

> "head-trader needs the current price, but your description only sends prices to the
> chart-analyst. I filled the gap by broadcasting the price feed to the head-trader
> too, so it keeps its own latest-price copy. The alternative is a dedicated
> price-keeper the head-trader queries (ask-and-wait). ... this is the biggest thing
> to confirm."

Assessment: **true positive, slightly softer than the Herb catch.**
- It caught the real gap (Pat never gave the head-trader a price source), made it the
  single biggest thing to confirm, and offered the exact **stale-vs-fresh** choice:
  a broadcast latest-price *copy* (stale-but-simple) vs. *query on demand* (fresh).
  Querying on demand is precisely the fix for staleness.
- What it did NOT do: spell out the *consequence* in Pat's words ("you might trade on
  a price that's seconds old"). The Herb catch named the consequence ("the tax
  numbers could be off"); here the consequence is implicit in the two options.
- Note: unlike Herb (left as a missing edge), this build proactively *filled* the gap
  with a defensible default and flagged it. A strong model tends to surface-and-
  resolve rather than leave-and-flag — worth noting as a finding.

## Bonus catches (all legitimate)

- **Sizing rule genuinely left open:** "'How big' ... you didn't spell out a sizing
  rule (fixed? fraction of cash? scaled by conviction?) ... the sizing logic needs
  defining." A clean underspecification Pat must resolve — good alternative
  correction target.
- Reasons carried on each signal so TRADES can log them.
- Stock list taken as given.

## Vs. our reference runnable office

The build is arguably *more faithful* than our milestone office: it wired the
head-trader's price (broadcast + latest-price copy), which our runnable milestone
had deferred. Its fair-merge-inside-head-trader is a legitimate alternative to our
separate `MergeAsynch`.

## Verdict

Strong build. All coordination correct, including two non-obvious correct calls (no
gate; not merge_synch). The pre-registered price gotcha surfaced as the top confirm
item with the exact fix offered — a true positive, a touch softer than Herb because
the consequence is implicit. Plus a clean sizing underspecification.

## Correction step (B4) options

1. **Price freshness (systems-relevant, pre-registered):** Pat picks the fresh
   option — "ask for the current price at the moment you decide." Graph change:
   head-trader stops keeping a latest-price copy and instead queries a price-keeper
   (ask-and-wait) for the current price when a signal fires. Clean, meaningful,
   distributed-data correction.
2. **Sizing rule:** Pat supplies a sizing rule (e.g., fixed size, or a fraction of
   cash). Resolves the genuinely-open gap the build flagged.

Recommend featuring (1) in the paper (matches the async/freshness theme), optionally
mentioning (2).
