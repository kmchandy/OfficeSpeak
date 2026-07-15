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
