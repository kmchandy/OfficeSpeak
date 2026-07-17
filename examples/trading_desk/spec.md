# trading_desk — Pat's office description

Five-section plain-English form (Overview / Inputs / Outputs / Workers / What each
worker does). Clean input — this is the document handed to Cowork. Our review and
predictions are in `spec_review.md`; do not include those when building.

---

## Overview

I want a desk that watches the market in real time and *suggests* trades — buy or
sell — for a handful of stocks we follow, with a short reason for each suggestion.
People on the desk read the suggestions and decide for themselves; the office only
proposes.

## Inputs

1. A live stream of **price updates** for the stocks we follow. These arrive
   continuously and quickly.
2. **News from two independent feeds**, arriving asynchronously and in bursts:
   posts from **X** (social media) and **Bloomberg's** newswire. Both carry
   market-moving headlines — Fed announcements, analyst reports, breaking stories.

The price feed and the two news feeds arrive independently and at different rates.

## Outputs

A running log of suggested trades — each with the stock, buy or sell, and a short
reason — written to a file, TRADES.

## Workers

- **chart-analyst** — a technical analyst who watches prices and signals a trade
  when a stock breaks out of its recent moving average.
- **news-analyst** — an analyst who reads the news and signals a trade when a story
  looks likely to move a stock.
- **head-trader** — decides whether to actually suggest a trade, and how big.
- **risk-manager** — keeps the desk's book (current positions, cash, and risk
  limits) and approves or rejects a proposed trade.

## What each worker does

- **chart-analyst.** Watches the price stream. For each stock it keeps a
  **30-minute moving average** of the price. When the price crosses from below to
  above that average it signals **buy** to the head-trader; when it crosses from
  above to below, it signals **sell**. It signals only at the moment of the
  crossing, not on every tick. This is a computational job — plain arithmetic on
  the price stream.
- **news-analyst.** Reads each news headline as it arrives. Given the headline and
  the list of stocks we follow, it decides whether the news is likely to push one of
  those stocks up or down soon. If so, it signals **buy** (likely up) or **sell**
  (likely down) for that stock to the head-trader, with a one-sentence reason; if the
  headline isn't clearly relevant, it does nothing. This is a judgment job — reading
  and interpreting text — so it is handled by an LLM.
- **head-trader.** Receives signals from the chart-analyst and the news-analyst as
  they come in — whichever fires first — and, using the current price, decides
  whether to propose a trade and how big. Sends the proposed trade to the
  risk-manager and waits for approval; if approved, writes the suggestion to TRADES.
- **risk-manager.** Keeps the desk's book — current positions, cash, and risk
  limits. When the head-trader proposes a trade, checks it against the book and the
  limits, approves or rejects it, and if approved updates the book. Handles one
  proposal at a time so the book stays consistent.
