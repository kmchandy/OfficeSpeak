# investment_club — Pat's office description

Five-section plain-English form (Overview / Inputs / Outputs / Workers / What each
worker does). Clean input — hand this verbatim to a fresh build chat. Our review and
predictions are in `spec_v2_review.md`; do not paste those into the build chat.

---

## Overview

I want an office that recommends buy, sell, and hold actions each period for my
investment club.

## Inputs

1. Each period (say, once a day) the office receives a batch of information —
   financial data, analyst forecasts, and breaking news — from sources such as
   Yahoo Finance, Bloomberg, the New York Times, and the Wall Street Journal. Treat
   it as a single combined news source; the office doesn't have to deal with each
   source separately.
2. Each period the office also receives the buy/sell/hold decisions the club
   actually made in the previous period.

## Outputs

Each period the office writes a recommended action plan — what to buy, sell, or hold
next period — to a file called RECOMMEND. Club members read RECOMMEND each period and
make their own decisions; that deliberation is not part of the office.

## Workers

- **value-investor** — a market analyst who recommends an action plan using a
  value-investing strategy.
- **growth-investor** — a market analyst who recommends an action plan using a
  growth strategy.
- **manager** — makes the office's final recommendation.
- **accountant** — works out the taxes and fees of a proposed plan.

## What each worker does

- **value-investor.** Each period, receives all the office's inputs (the news and
  the club's previous decisions) and can see the club's current portfolio and
  history. Using a value-investing strategy, it decides the best action plan (what
  to buy, sell, hold) and sends its recommendation to the manager.
- **growth-investor.** The same as the value-investor, but uses a growth strategy.
- **manager.** Receives all the office's inputs, as well as the action-plan
  recommendations from the value-investor and the growth-investor. She weighs their
  recommendations, uses her own knowledge, and puts together a proposed action plan,
  which she sends to the accountant. When the accountant returns the plan's costs,
  she adjusts the plan into a final recommendation and writes it to RECOMMEND.
- **accountant.** Receives a proposed action plan from the manager, computes the
  taxes and transaction fees if the plan were executed, and sends the cost back to
  the manager.
