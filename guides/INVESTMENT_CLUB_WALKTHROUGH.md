# The investment-club example, start to finish

This is the same worked example that runs through `README.md`, told straight
through with none of the setup instructions, troubleshooting, or "what to
send back" notes in between — just the story: the description, the build,
the mistake it caught, the correction, and the real numbers it produced.
If you want to actually *do* this yourself, `README.md` is where the
step-by-step instructions live; this page is for rereading the story on its
own.

## The description

> Once each period my club gets a batch of market data, forecasts, and news,
> plus our decisions from last period. Two analysts each read it and recommend
> a plan — one value-investing, one chasing emerging opportunities. A manager
> weighs both, proposes a plan, checks the taxes and fees with an accountant,
> then writes the final plan to a file. Keep our portfolio and history in one
> place, and handle one period at a time so the books stay consistent.

## What came back

> Each period the office lets one batch in. Both analysts read it and each
> writes a recommendation; a worker whose only job is to wait for both hands
> the pair to the manager. The manager puts together a proposed plan and asks
> the accountant what it would cost in taxes and fees; the accountant works
> that out and reports back; the manager finalizes the plan, writes it and the
> updated holdings to the shared portfolio, saves the plan to the file, and
> lets the next period in.
>
> **Things I assumed —** the two analysts are treated equally and the manager
> has the final say; the office handles one period fully before starting the
> next so the shared portfolio stays consistent; and **the accountant works out
> the taxes from the proposed plan alone — it does not look at what the club
> currently holds.** Tell me if any of these should be different.

## The catch, and the correction

The third assumption is wrong: taxes and fees depend on what the club
already holds, not just the proposed move. The correction, sent back in
plain English:

> "The accountant has to see what we currently hold — otherwise the tax
> numbers are guesses. Taxes depend on what we paid for what we own."

What changed:

> One new link: before it prices anything, the accountant now looks up what
> the club currently holds and what we paid for it, and uses that for the tax
> math. Nothing else about the office changes.

This is the whole idea: you shouldn't have to specify a correct office up
front. It's easier to react to a concrete team than to describe one
perfectly from nothing. Catching exactly this kind of gap — a worker that
computes something but was never given a fact it needs — is what the
"Things I assumed —" list is for.

## The accountant, built and approved

The worker the correction changed, approved as real code. It does exactly
what was asked: it asks the ledger for current holdings *before* it prices
anything, not after.

```python
def _make_accountant_fn():
    _PRICE_PER_SHARE = 100.0
    pending = {}

    def accountant_fn(msg):
        if "proposed_shares" in msg:
            # A proposal from the manager -- ask the ledger what we hold
            # *before* pricing anything (this is the correction).
            pending["period"] = msg["period"]
            pending["proposed_shares"] = msg["proposed_shares"]
            return [({"action": "read"}, "to_ledger")]

        # The ledger's reply.
        current_shares = msg["aapl_shares"]
        current_cash = msg["cash"]
        proposed = pending["proposed_shares"]
        fee = 1.0 * proposed + 0.001 * current_shares * _PRICE_PER_SHARE
        return [({"fee": fee, "current_shares": current_shares,
                   "current_cash": current_cash}, "to_manager")]
    return accountant_fn
```

Tested on period 1's actual numbers, before approving it:

```
IN  (manager's proposal):  {"period": 1, "proposed_shares": 8}
OUT (accountant's first reply): asks the ledger, {"action": "read"}

IN  (ledger's reply):      {"aapl_shares": 0, "cash": 10000.0}
OUT (accountant's answer to the manager):
    {"fee": 8.0, "current_shares": 0, "current_cash": 10000.0}
```

## What actually happened when it ran

Real output from a real run — three periods, then it stops on its own:

```
[Manager] period 1: proposing 8 shares (val=5, oppo=3); asking accountant
[Accountant] period 1: asking ledger for current holdings before pricing
[Accountant] period 1: current holdings shares=0, cash=10000.00 -> fee=8.00
[Manager] period 1: fee=8.00, holdings before this trade: shares=0, cash=10000.00 -> after: shares=8, cash=9192.00

[Manager] period 2: proposing 16 shares (val=10, oppo=6); asking accountant
[Accountant] period 2: current holdings shares=8, cash=9192.00 -> fee=16.80
[Manager] period 2: -> after: shares=24, cash=7575.20

[Manager] period 3: proposing 24 shares (val=15, oppo=9); asking accountant
[Accountant] period 3: current holdings shares=24, cash=7575.20 -> fee=26.40
[Manager] period 3: -> after: shares=48, cash=5148.80
```

and `recommendations.jsonl` ends up holding:

```json
{"period": 1, "bought": 8, "fee": 8.0, "resulting_shares": 8, "resulting_cash": 9192.0}
{"period": 2, "bought": 16, "fee": 16.8, "resulting_shares": 24, "resulting_cash": 7575.2}
{"period": 3, "bought": 24, "fee": 26.4, "resulting_shares": 48, "resulting_cash": 5148.8}
```

Each period's fee is computed from the *previous* period's ending
holdings — exactly the thing the correction asked for, now visibly true in
real numbers (period 2's fee of 16.80 = $1/share × 16 shares + 0.1% × 8
shares the club already held × $100 — the 8 shares are period 1's result,
not period 2's proposal).

The full hand-off file behind this run — every worker, not just the
accountant — is at
`offices/claude_project/investment_club_handoff.py`, and the exact steps to
reproduce it are in `README.md`'s Stage 1 and Stage 2 sections.
