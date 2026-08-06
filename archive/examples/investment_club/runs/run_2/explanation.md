# investment_club / run_2 — explain-back (local-state graph → Pat English)

Prompt: offices/prompt_explain.md
Input: offices/investment_club/runs/run_2/actual_graph.md (the local-state / message-passing graph).
Held-out: the explainer was given only the explain prompt + the graph, not the spec, the intended graph, or the run_2 diagnostic notes.

---

This little office watches the markets for your club and, whenever something
important happens, decides whether to buy, sell, or hold — and keeps score of
how each person's approach would have done.

The team: **Nora** keeps the written record of every argument and every
decision, and hands out pieces of it when someone asks. **Warren** argues from a
value point of view; **Bill** argues from a new-opportunities point of view.
**Don** makes the final call. **Herb** works out the taxes and fees on a
proposed action. **Bruno** holds the club's real portfolio and carries out Don's
decisions.

When a piece of market data or news comes in, the office takes one item at a
time. It goes to Warren, Bill, Don, and Herb all at once, and each keeps his own
copy. Warren and Bill each write up an argument, file a copy with Nora, and
update their own personal scorecard of what they'd be holding. Don waits until he
has *both* arguments in hand for that same item. He then works out a proposed
action and asks Herb what it would cost in taxes and fees; Herb works that out
and reports back, and Don waits for that answer before finalizing. Don files the
final decision with Nora, updates his own scorecard, and hands the action to
Bruno. Bruno updates the club's real holdings, records what was done, and only
*then* lets the next item in — so the real portfolio and everyone's scorecards
all move forward together, on the same item, and stay comparable.

**Baked-in choices —**
- **One item at a time.** The office fully finishes one piece of news before
  starting the next. This keeps the real portfolio and the three scorecards in
  step, but it means the office works through a backlog one at a time rather than
  all at once.
- **Nora alone keeps the shared record**, and others get to it only by asking
  her. Warren and Bill file their arguments with her, but I did not have anyone
  *read* the log back before deciding — the analysts argue from the incoming
  data, not from the history in Nora's book. If you wanted Don or the analysts to
  consult past arguments, I'd need to add that.
- **Herb figures taxes and fees from his own records** of the club's cost basis,
  not from Bruno's live holdings. Bruno is the one who actually keeps the real
  portfolio, so if Herb's copy of what we own ever drifts from Bruno's, the tax
  and fee numbers could be off. Right now nothing connects Herb to Bruno. Tell me
  if Herb should ask Bruno for the current holdings before working out the taxes.
- **Don has the final say**, and he only consults Herb — not the other way
  around; the analysts don't see Herb's tax numbers.
- **Each person keeps his own scorecard** privately; nobody compares them
  automatically. "Try to do better over time" isn't wired in yet — I assumed
  you'd review the scorecards yourself for now.
