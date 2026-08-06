# Debugging by explanation — Claude explains an agent's tape to Pat

The office was run with `DSL_DEBUG=1`, which records, for every agent, a tape of
**(input, state, output)** per action — `debug_dict.json`. "Replay" here is just
*display* of these tapes; nothing is re-executed, so it works the same for
deterministic and LLM agents (for an LLM agent we simply show its recorded in/out).

Pat does not read the raw dict. She asks Claude, in plain English, about one agent.

---

## Example 1 — Pat: "What did the risk-manager actually do? Is it tracking our positions right?"

**Claude (from the risk-manager's tape):**
> Your risk-manager handled 23 proposals from the head-trader this run. For each
> one it did three things: read the proposed trade, checked it against the desk's
> book (the running count of how much we hold in each stock, capped at ±5), and
> replied approve or reject — updating the book when it approved.
>
> Walking the first few: it approved a **buy AAPL** (book: AAPL 1), another **buy
> AAPL** (AAPL 2), a **buy TSLA** (TSLA 1), then a **sell TSLA** that took TSLA
> back to 0, and so on. Over the whole run AAPL moved between 0 and 3 and TSLA
> between -1 and 1.
>
> Two things worth noting for you. First, it **approved all 23** — the ±5 limit
> never actually bit, because your positions never got past 3. So the guard is
> wired correctly but was never tested in this run; if you expected it to hold you
> back, either the limit is looser than you need or this particular run just didn't
> push hard enough. Second, it updates the book **only on approval**, which is what
> you'd want — a rejected trade doesn't change your holdings.

Pat can confirm ("yes, that's right") or correct ("±5 is too loose, make it ±2") —
in plain English, without ever seeing the dict.

---

## Example 2 — Pat: "How does the chart-analyst decide? It saw 120 prices but only acted a few times."

**Claude (from the chart-analyst's tape):**
> Right — it looked at all 120 price ticks but only sends a signal at a **crossing**.
> Its state is just which side of the 30-tick average each stock is on. As long as a
> stock stays on the same side, it says nothing. The moment the price crosses the
> average it fires once: for example, AAPL at 101.64 crossed *above* its average of
> 100.82, so it flipped to the "above" side and signalled **buy**. It stays quiet
> again until the next crossing. So the sparse output is correct behaviour, not a
> missed input.

---

## Why this is enough (and cheap)

- The tape is the debug artifact; **Claude's explanation is the contribution** — a
  non-programmer inspects one worker at a time in plain English.
- Because it is display-only, there is **no re-execution**, so LLM nondeterminism
  and fair-merge ordering are irrelevant to debugging.
- State comes for free by reusing each agent's `save_state()`-style snapshot.
- Retention back to the last checkpoint or two bounds the log size.

## Raw excerpt (for the paper figure)

```
risk-manager, action 1:
  in:    {symbol: AAPL, action: buy, why: "Fed cuts rates by 50 bps"}
  state: {AAPL: 1}
  out:   {approved: true, symbol: AAPL, position: 1}
risk-manager, action 5:
  in:    {symbol: TSLA, action: sell, why: "moving-average crossing"}
  state: {AAPL: 2, TSLA: -1}
  out:   {approved: true, symbol: TSLA, position: -1}
```
