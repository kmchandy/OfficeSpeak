# Pat's office scaffold (first draft)

A guided way for a non-programmer (Pat) to describe the office she wants. It
trades a little more thinking up front for fewer build->explain->correct rounds,
and — just as important — it tells a Pat-off-the-street **where to begin** instead
of facing a blank "build an office of agents."

Design rules:
- Structure the **what** (Pat's world), never the **how** (no "agent", "message",
  "port", "graph"). Pat stays in her own domain.
- Every field is answered in **plain prose**, with a one-line prompt and a tiny
  example. Skippable if it doesn't apply.
- The fields quietly teach the office mental model by asking Pat to fill them —
  she learns by doing, not by studying distributed systems.
- It is a **starting draft, not a contract**. Claude will show an office back and
  Pat can fix it; the iteration loop is still the safety net, so no field is
  high-stakes.

## Delivery: prefer a guided interview over a blank form

The same fields can be shipped two ways:
- **Form** — Pat fills all fields at once. Faster for a confident Pat.
- **Interview (recommended)** — Claude asks the questions one at a time, in order,
  and Pat answers in prose. Gentlest for a first-timer ("she wouldn't know where
  to begin" -> Claude begins). Claude can also fill obvious fields from earlier
  answers and just ask Pat to confirm.

Open question for us: default to interview, offer form as a shortcut? (my lean:
yes.)

## The fields

1. **The goal.** In a sentence or two: what should this office watch, and what
   should it decide or produce?
   > e.g. "Watch market news and prices and recommend whether my club should buy,
   > sell, or hold — and keep a record."

2. **What comes in.** Where does information arrive from? List each source.
   > e.g. "Prices and forecasts from Yahoo and Bloomberg; breaking news from a few
   > news feeds."

3. **What goes out.** What should the office produce, and where does it go?
   > e.g. "A buy/sell/hold recommendation, shown on screen and saved to a file."

4. **The helpers.** Who does the work, and what is each one's job? Give each a
   name (a made-up role name is fine) and a one-line job.
   > e.g. "Warren — argues from a value view. Bill — argues from an opportunities
   > view. Herb — works out taxes and fees. Don — makes the final call."
   *(You don't have to get the list perfect — Claude may split or combine helpers,
   and will show you what it chose.)*

5. **What each helper needs to know.** For each helper, what information do they
   need to do the job well? *(This is the most important question — it's the one
   people most often leave something out of.)* **Watch the helpers who *compute*
   or *decide* something: what current facts or figures must they see?** (A helper
   who works out taxes needs to know what you currently hold, not just the
   proposed move.)
   > e.g. "Warren and Bill need the incoming news. Herb needs the proposed move
   > **and what we currently hold**. Don needs both arguments and Herb's estimate."

6. **What each helper remembers.** Does anyone keep track of something over time?
   > e.g. "Each analyst keeps a practice portfolio of how their own advice would
   > have done. The club's real holdings are kept too."

7. **Shared information.** Is there anything the whole team looks at or writes down
   together?
   > e.g. "Every argument and decision is written down where everyone can see it."

8. **Rules that must hold.** Anything about order, timing, or care?
   - **Does the office *update* any shared information** (not just read it)? If so,
     should it finish one item completely before starting the next, so the shared
     information stays consistent? *(If nothing shared is updated, it can handle
     many at once — no need to slow it down.)*
   - Does anyone have to **wait** for someone else before acting?
   - Should the office **learn** from what actually happened over time?
   > e.g. "Handle one piece of news at a time so the records stay consistent. Don
   > waits for Herb before deciding. Each analyst tries to improve over time."

9. **Anything else.** Special cases, exceptions, or things you're unsure about.

## Worked example — investment_club filled in

1. Goal: recommend buy/sell/hold for my club (tech stocks + cash) from market data
   and news, and record every decision.
2. Comes in: Yahoo + Bloomberg (prices, forecasts); a few news feeds (breaking
   news).
3. Goes out: a buy/sell/hold recommendation, on screen and saved to a file.
4. Helpers: Warren (value view), Bill (opportunities view), Herb (taxes & fees),
   Don (final call).
5. Needs to know: Warren, Bill need the incoming info; Herb needs the proposed
   move **and current holdings**; Don needs both arguments and Herb's estimate.
6. Remembers: a practice portfolio per analyst; the club's real holdings.
7. Shared: every argument and decision written where all can see.
8. Rules: one piece of news at a time (keep records consistent); Don waits for
   Herb; each analyst tries to improve over time.
9. Else: —

## Does it capture what caused our iterations?

Every requirement we discovered *late* has an up-front home:

| Late-discovered requirement | Scaffold field |
|---|---|
| Herb needs current holdings (the gap) | **5 — needs to know** |
| One item at a time / consistency | 8 — rules |
| Per-analyst model portfolios | 6 — remembers |
| Everything written down / shared record | 7 — shared |
| "Try to do better over time" (feedback) | 8 — rules |

So the field that earns its keep most is **#5** — it's where the Herb gap would
have surfaced before any graph was drawn.

## Field -> contract mapping (for us, not shown to Pat)

- 2 -> sources · 3 -> sinks · 4 -> workers + bodies (Stage B) ·
  **5 -> each agent's read-set (wiring inputs + data dependencies)** ·
  6 -> state · 7 -> shared record (record/keeper; implies a gate if written) ·
  8 -> coordination requirements (gate, ask-and-wait/select, feedback loop) ·
  9 -> escape hatch / expressiveness relief.

Pat fills domain intent; we recover the contract skeleton from (4) almost 1:1.
Field 5 is the read-set, so a spec-vs-wiring check falls out: "you said Herb needs
holdings, but nothing feeds him that."

## Where this sits on the burden line, and the risks

- Fields 1-4 are near-zero burden for anyone — pure scaffold value.
- Field 5 is the highest value **and** the highest burden, but it's phrased in
  domain terms ("what do they need to know"), not systems terms. Worth it.
- Field 8 risks nudging Pat toward mechanism ("wait", "one at a time"). Kept
  because these are still real-world concerns (order, consistency) she recognizes;
  Claude can infer/confirm the mechanism.
- Field 4 asks Pat to name helpers — a *seed* decomposition, not binding. Our runs
  showed Claude refines it well (it split Bruno-the-custodian from Don). State
  clearly to Pat that the list is a starting point.

## Open questions for us
- Interview vs form as default (my lean: interview, form as shortcut).
- Are 5 and 7 distinct enough for Pat, or do they blur? (keep separate for now.)
- Should the build prompt (`prompt.md`) take the filled scaffold in place of
  free-text "PASTE PAT'S DESCRIPTION HERE"? (downstream change; not yet.)
- Minimum required fields vs optional, to tune burden per Pat.
