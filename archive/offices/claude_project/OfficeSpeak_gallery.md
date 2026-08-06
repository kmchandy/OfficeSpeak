# OfficeSpeak gallery — worked examples (upload as one Project knowledge file)

Three complete offices spanning the coordination library and both body styles, plus the getting-started guide. These make the assistant expert; held-out demo offices (e.g. weather) are NOT included here.

==============================================================

# Gallery example — investment_club (deliberate-and-decide)

A worked example: a synchronizing join (merge_synch), a shared record, a gate, and an
ask-and-wait loop. Shows the *corrected* office (the accountant reads current holdings).

## Pat's description

Each period, recommend buy/sell/hold for the club. Inputs: a batched news/data feed,
and the club's actual decisions from the previous period. A **value-investor** and a
**growth-investor** each read the inputs and the club's portfolio and recommend an
action plan. A **manager** weighs both recommendations, proposes a plan, checks the
cost with an **accountant** (taxes + fees), then writes a final plan to RECOMMEND.

## The office

```
Agents:
  feed, club_decisions — sources (batched per period)
  Ledger — record(holds: portfolio, history, arguments, decisions)
  Gate   — gate (one period at a time)
  value-investor  — LLM: value-strategy plan · reads: inputs, Ledger · sends: rec -> merge_synch
  growth-investor — LLM: growth-strategy plan · reads: inputs, Ledger · sends: rec -> merge_synch
  manager — LLM: weighs both, proposes, finalizes · <-> accountant · <-> Ledger
  accountant — Python: taxes + fees of a plan · reads: plan, Ledger (holdings)
  RECOMMEND — sink
Wiring:
  feed, club_decisions -> Gate -> value-investor, growth-investor
  value-investor -> merge_synch ; growth-investor -> merge_synch ; merge_synch -> manager
  value-investor <-> Ledger ; growth-investor <-> Ledger      # read portfolio/history
  manager <-> accountant                                       # ask-and-wait (the loop)
  accountant <-> Ledger                                        # read current holdings for taxes
  manager <-> Ledger                                           # write final plan; update portfolio
  manager -> RECOMMEND ; manager ..done..> Gate
Notes:
  merge_synch makes the manager wait for BOTH analysts (a join, not "whichever first").
  Ledger is the shared record. A gate keeps one period at a time because workers read
  and write the Ledger. The accountant reads the Ledger for current holdings — taxes
  need cost basis.
```

## Explanation for Pat

Each period the gate lets one batch in. Both analysts read it and the club's portfolio
and write a recommendation; the manager waits for both, proposes a plan, and asks the
accountant what it would cost — the accountant looks up current holdings to get the
taxes right — then finalizes, writes to RECOMMEND, updates the portfolio, and releases
the gate for the next period.

## Worker bodies (illustrative)

**accountant (Python — computational):**
```python
class Accountant:
    def __init__(self, tax_rate=0.15, fee_per_trade=5.0):
        self.tax_rate = tax_rate; self.fee = fee_per_trade
    def run(self, msg):
        plan, holdings = msg["plan"], msg.get("holdings", {})
        fees = self.fee * len(plan.get("trades", []))
        gains = sum(t["proceeds"] - holdings.get(t["symbol"], {}).get("cost_basis", 0)
                    for t in plan.get("trades", []) if t["action"] == "sell")
        return {"taxes": round(max(gains, 0) * self.tax_rate, 2), "fees": fees}
```

**value-investor / growth-investor / manager (LLM — judgment).** Each is an LLM prompt:
a system prompt describing the strategy (value / growth / weigh-and-decide), plus the
input it reads (the period's inputs, the portfolio) and the output it sends (an action
plan). The growth-investor is the value-investor's prompt with a growth strategy.

==============================================================

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

==============================================================

# Gallery example — anomaly_monitor (detect-anomaly)

A worked example: per-key windowed state, a router, and the *restraint* of using no
fair_merge and no gate because the office does not need them.

## Pat's description

Watch our services' health and alert me when something looks abnormal. For each
service (web, db, cache) a reading arrives regularly. A **monitor** learns each
service's normal range and flags a reading far outside it; a **deduper** groups
repeated alerts for the same service; a **router** sends each alert to whoever owns
that service. Alerts go to a file, ALERTS.

## The office

```
Agents:
  metrics — source: health readings {service, value}
  monitor — per-service rolling average/spread; flags a reading > 3 std out · state: per-service window
  deduper — suppresses a repeat alert for the same service in quick succession · state: per-service last-alert
  router  — sends each alert to the owner of its service (if/elif/else)
  ALERTS  — sink
Wiring:
  metrics -> monitor -> deduper -> router -> ALERTS
Notes:
  A single readings stream, so NO fair_merge. No shared writable state (each worker's
  memory is its own, keyed by service), so NO gate. The router is the only branching.
```

## Explanation for Pat

Each reading goes to the monitor, which keeps a separate recent average and spread for
every service and flags a value more than a few standard deviations out (it needs a few
readings first to learn "normal"). The deduper drops a repeat alert for a service that
just alerted, so you get one message, not twenty. The router looks up who owns the
service and sends the alert there. Nothing is shared or written jointly, so the office
handles readings as fast as they come — no one-at-a-time needed.

## Worker bodies

**monitor (Python — computational):**
```python
from collections import defaultdict, deque
import math
class Monitor:
    def __init__(self, window=20, z=3.0):
        self.w = defaultdict(lambda: deque(maxlen=window)); self.z = z
    def run(self, msg):
        s, v = msg["service"], float(msg["value"]); w = self.w[s]; w.append(v)
        n = len(w)
        if n >= 5:
            mean = sum(w)/n; std = math.sqrt(max(sum((x-mean)**2 for x in w)/n, 0.0))
            if std > 0 and abs((v-mean)/std) >= self.z:
                return {"service": s, "value": v, "z": round((v-mean)/std, 2)}
        return None
```

**deduper (Python — computational):**
```python
class Deduper:
    def __init__(self, cooldown=3):
        self.cooldown = cooldown; self.last = {}; self.n = 0
    def run(self, msg):
        self.n += 1; s = msg["service"]
        if s in self.last and self.n - self.last[s] <= self.cooldown:
            self.last[s] = self.n; return None
        self.last[s] = self.n; return msg
```

==============================================================

# Start here — build an office (no programming needed)

Welcome. You're going to build a small **office**: a team of software helpers that
watches for information and reacts to it, on its own. You will **not** write code.
You describe what you want in plain English; the assistant builds it, shows it back
to you as a simple picture and a plain description, and you fix anything that's
wrong. You go back and forth until it does what you want.

## What is an office?

Think of a small team. Each person has **one clear job**. Information comes in the
door — a news feed, live prices, emails, sensor readings. The workers react to it,
hand things to one another, and results go out — written to a file, or shown on a
screen. The office runs on its own; you don't press "go" each time.

You already understand this — it's how a real workplace runs. That's all an office
is.

## How to describe your office

Just answer a few plain questions, in your own words:

1. **What is it for?** One or two sentences.
2. **What comes in?** Where does information arrive from, and how often?
3. **What goes out?** What should it produce, and where does it go?
4. **Who's on the team?** Name each worker and its one-line job — and, importantly,
   **what each one needs to know** to do the job, and **who it hands things to**.
5. **Any rules?** For example: handle one thing at a time? Does anyone wait for
   someone else? Should the team learn over time?

Don't worry about getting it perfect or complete. The whole point is that you'll
**see it and fix it**.

## What happens next

1. You describe it in plain words.
2. The assistant builds the office and **explains it back** to you — who does what,
   who hands what to whom — with a simple diagram, and a short list of "things I
   assumed" (the choices you didn't spell out).
3. You **confirm or correct** in plain English — for example, "no, the accountant
   has to see what we currently hold."
4. It updates and shows you again. Repeat until it's right.

That back-and-forth is the whole method. A first rough description is enough to get
started.

## A tiny example

> "I want a desk that watches the market and suggests buy or sell for a few stocks.
> Prices come in continuously; news comes in from X and from Bloomberg. A
> chart-watcher signals when a price breaks its recent average; a news-reader signals
> when a story looks market-moving. A head-trader decides what to suggest and checks
> a risk-manager (who keeps our positions and limits) before writing the suggestion
> to a file."

From that, the assistant builds the office, notices things you left open (e.g., "how
should the head-trader get the current price?"), and asks you — and you answer in
plain English.

## What you get, without having to think about it

Under the hood, your office runs on grown-up machinery you never have to see:

- it **stops cleanly** when there's nothing left to do,
- it **saves its state** now and then (checkpoints), so it can recover, and
- you can **look inside** when something seems off.

You don't manage any of that. It's just there.

## You can also ask the assistant to…

- **Explain what any worker did** — it shows you that worker's inputs and outputs in
  plain English ("your risk-manager approved all 23 proposals; your positions never
  hit the limit").
- **Test one worker** on its own.
- **Improve a worker's instructions** — "the news-reader is too jumpy on rumors" —
  and it tightens them.

## Ready?

Describe your office in your own words. A good way to start is simply:

> "I want an office that …"
