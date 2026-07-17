# investment_club / run_1 — explain-back (shared-memory graph → Pat English)

Prompt: offices/prompt_explain.md
Input: offices/investment_club/runs/run_1/actual_graph.md (the shared-memory / record graph).
Held-out: the explainer was given only the explain prompt + the graph, not the
spec, the intended graph, or any run notes.

Role in the experiment: **negative control** for the run_2 Herb catch. In this
graph Herb reads the club's holdings from Rachel (the shared record), so the
Herb-to-holdings link is present and correct. A trustworthy explainer should
therefore NOT flag a Herb gap here.

---

This office watches the markets and the news, and for each new development it
decides whether the club should buy, sell, or hold — then writes that
recommendation down.

The team: three feeds bring information in — two carry market data and analyst
forecasts, one carries breaking news. Gus lets information in one piece at a
time. Warren argues each item the way a value investor would — buy, sell, or hold
on the merits. Bill argues the same item from a spot-an-opportunity angle. Meg
waits until both Warren and Bill have made their cases, then hands the pair over
together. Herb works out the taxes and transaction fees for any action being
considered. Don is the decision-maker: he weighs both arguments, proposes an
action, checks the cost with Herb, and makes the final call. Rachel keeps all the
shared records — every argument, every action, the club's real portfolio, and a
separate practice portfolio for each of Warren, Bill, and Don; everyone asks her
when they need something and tells her when something changes. The finished
recommendations go out to a running list, on screen or saved to a file.

When a new piece of information arrives — a market update or a news item,
whichever feed speaks first — it goes into one line and Gus lets it in. The same
item reaches Warren, Bill, Herb, and Don all at once, so everyone works from the
same facts. Warren builds his buy/sell/hold case from a value view, logs it with
Rachel, and updates his own practice portfolio; Bill does the same from an
opportunities view. Meg waits for both, then passes the two arguments to Don
together. Don proposes an action and asks Herb what it would cost in taxes and
fees; Herb looks up the club's current holdings from Rachel and sends the numbers
back. Don waits for that, then finalizes: he sends the recommendation out, tells
Rachel to log the action and update both the real portfolio and his own practice
portfolio, and signals he's done. Only then does Gus let the next item in.

Baked-in choices — one item at a time, and nothing new starts until Don has
finished and the records are updated; Rachel alone holds every record and
everyone goes through her; Don must wait for both Warren and Bill before he can
decide; Don checks every proposed action with Herb before finalizing — a small
back-and-forth; each analyst keeps his own separate practice portfolio alongside
the club's real one; and Don has the final say. Tell me if any of these should be
different.
