# trading_desk — review and pre-registered predictions

Our notes on the held-out spec (`spec.md`). Not given to Cowork.

## How it hits the rubric (why this example, in one table)

| Requirement | Where it lives in the office |
|---|---|
| async multi-input -> **fair merge** (the only nondeterminism) | head-trader merges the chart-analyst and news-analyst signal streams "whichever fires first" |
| **Python + LLM** workers | chart-analyst = deterministic Python (moving-average / breakout, our `sliding_window_stats` agent); news-analyst = LLM judgment |
| shared state + **gate** | risk-manager owns the book (positions, cash, limits), read-and-written, "one proposal at a time" |
| **ask-and-wait loop** (a real graph cycle) | head-trader proposes -> risk-manager approves -> back to head-trader; the loop exists because the risk-manager has private information (the book/limits) the head-trader lacks |
| **termination detection with loops** | end-of-session quiescence must be detected with the head-trader<->risk-manager request-reply possibly in flight |
| **deterministic replay** payoff | the fair merge at the head-trader is the only nondeterminism; logging its ingestion order makes replay-from-checkpoint reproduce the exact run |

Four workers, two async sources, one sink — minimal, but it exercises every claimed
feature. It is deliberately not a real trading desk; it shows what *can* be done.

## Predicted graph shape

```
prices  ─▶ chart-analyst ─┐
                          ├─(fair merge)─▶ head-trader ⇄ risk-manager ─▶ TRADES
news    ─▶ news-analyst  ─┘                    ▲ (uses current price)      │
prices  ───────────────────────────────────────┘        risk-manager owns the book (gate)
```

## Pre-registered explain-back gotcha (the caught bug)

The spec says the head-trader decides "using the current price." With asynchronous
streams, "current" will almost certainly be implemented as *the last price message
the head-trader happened to receive* — which can be seconds stale when a news signal
fires. Prediction: the explain-back surfaces this as a plain-English "things I
assumed" item ("when a news signal triggers a trade, the desk uses the last price it
received, which may be out of date"), and Pat corrects it ("it must fetch the current
price at that moment"). This bug exists **only because the inputs are asynchronous** —
it is the reason the async example is worth its added complexity, and it is the arc
that mirrors the investment club's accountant-holdings catch.

## Notes

- Framed as *suggestions* a human acts on (like the investment club), not autonomous
  execution — keeps it sober for referees.
- Parallels the investment club deliberately: chart-analyst/news-analyst ~ the two
  analysts, head-trader ~ manager, risk-manager ~ accountant — same pattern, now
  asynchronous, so a referee sees the generalization at a glance.
