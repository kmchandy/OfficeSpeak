# Gallery example — trading_desk (async sense-and-respond)

A worked example: async multi-source input (fair_merge), an ask-and-wait loop, and a
mix of a Python worker and an LLM worker.

## Pat's description

A desk that watches the market and *suggests* trades — buy or sell — for a few
stocks, with a short reason. Prices stream in fast and continuously. News arrives in
bursts from two feeds — X (social) and Bloomberg. Two analysts: a **chart-analyst**
(signals buy/sell when a price crosses its 30-minute moving average) and a
**news-analyst** (an LLM that flags a headline likely to move a stock). A
**head-trader** decides whether to suggest a trade and how big, checking a
**risk-manager** (who keeps the book and limits) before writing to a file, TRADES.

## The office

```
Agents:
  prices        — source: price ticks
  news_x, news_bb — sources: two async news feeds
  chart-analyst — signals buy/sell at a moving-average crossing · state: per-stock MA + side
  news-analyst  — LLM: flags a market-moving headline · state: the stock list
  head-trader   — proposes a trade, asks the risk-manager, writes approved ones
  risk-manager  — keeps the book; approves/rejects one proposal at a time
  TRADES        — sink
Wiring:
  news_x, news_bb -> fair_merge -> news-analyst
  prices -> chart-analyst
  chart-analyst -> head-trader ; news-analyst -> head-trader   # whichever fires first
  head-trader <-> risk-manager                                 # ask-and-wait (the loop)
  head-trader -> TRADES
Notes:
  The two news feeds are merged (fair_merge). The head-trader acts on whichever analyst
  signal arrives first (not a join). One proposal at a time is guaranteed by the single
  head-trader waiting for the risk-manager's reply, so NO gate is needed.
```

## Explanation for Pat

Prices go to the chart-analyst, who watches each stock's 30-minute average and calls
out buy or sell the moment the price crosses it. The two news feeds are combined and
read by the news-analyst, who flags market-moving stories. The head-trader listens to
both and acts on whichever speaks first; before suggesting a trade it asks the
risk-manager — who alone keeps the book of positions and limits — and only writes an
approved suggestion to TRADES. Nothing is executed; the desk only proposes.

## Worker bodies

**chart-analyst (Python — computational):**
```python
from collections import deque, defaultdict
class ChartAnalyst:
    def __init__(self, window_ticks=30):
        self.w = defaultdict(lambda: deque(maxlen=window_ticks)); self.side = {}
    def run(self, msg):
        s, p = msg["symbol"], float(msg["price"])
        w = self.w[s]; w.append(p); ma = sum(w)/len(w)
        side = 1 if p > ma else -1; prev = self.side.get(s); self.side[s] = side
        if prev is not None and side != prev:
            return {"symbol": s, "signal": "buy" if side == 1 else "sell", "price": p}
        return None
```

**news-analyst (LLM — judgment). System prompt:**
> You are a market news analyst for a desk that follows {symbols}. Given one headline,
> decide if it is likely to move a followed stock soon. Reply exactly one line:
> `BUY <symbol> — <reason>`, `SELL <symbol> — <reason>`, or `NONE`.
> input: `{"headline": "...", "about": "..."}` · output: `{"symbol","signal","reason"}` or nothing.
