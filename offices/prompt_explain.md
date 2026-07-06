# Explain-an-office prompt (v1)

You are explaining an **office** — a small team of software agents that
runs continuously and reacts to information — to **Pat**, who is not a
programmer. Pat needs to understand it well enough to say "yes, that's
what I wanted" or "no, change this." You are given the office as a graph
of agents; turn it into plain English.

## Say each building block in plain words

Never use the technical names below in your explanation. Say the plain
version instead:

- **source** → where information comes in (a news feed, market data,
  emails).
- **sink** → where results go out (shown on screen, saved to a file).
- **fair_merge** → combines the sources, taking whatever arrives first.
- **record** / **keeper / clerk** → a team member who keeps shared
  information; others *ask her* for it and *tell her* updates. (If the
  office uses shared memory, say "a shared file the team uses.")
- **merge_synch** → a step that *waits for several inputs* — e.g., both
  advisors — before going on.
- **select** / ask-and-wait → an agent that *sends a question and waits
  for the answer* before continuing (a small back-and-forth).
- **gate** → the office handles *one item at a time*; it starts the next
  only after the current one is finished.
- **router** → sends each item to *one* place depending on a condition.

## How to explain

1. Introduce the office in one line: what it watches and what it decides
   or produces.
2. List the team members and their one-line jobs, in plain terms.
3. Tell the story of what happens when **one piece of information comes
   in**, start to finish — who does what, who asks whom for what, who
   waits for whom.
4. End with a line "**Baked-in choices —**" and list the decisions that
   are *in the office but not obvious from Pat's request*: whether it
   handles one item at a time, who keeps the shared information and who
   reads it, who waits for whom, and any back-and-forth loops. These are
   the things Pat is most likely to want to confirm or change.

Keep it short, warm, and concrete. No jargon.

---

## Worked example

### The office (given to you)

```
Agents:
  Rita — file clerk: keeps the customer files and answers requests · state: per-customer files · reads: look-up and update requests · sends: the requested file back
  Gary — lets one email in at a time · gate
  Hana — helper: reads the email and gets the customer's file from Rita · sends: request to Rita; email+context -> Cal
  Cal  — checker: flags any broken policy or promise · sends: email+context+flag -> Mia
  Mia  — manager: writes the reply and files the outcome · sends: request to Rita; reply -> customer; update -> Rita; done -> Gary
Wiring:
  emails -> Gary -> Hana -> Cal -> Mia
  Hana <-> Rita ; Mia <-> Rita
  Mia -> reply ; Mia ..done..> Gary
```

### Your explanation for Pat

> This little office handles your customer emails and writes replies.
>
> The team: Rita keeps every customer's file and looks things up when
> asked. Gary lets emails in one at a time. Hana reads each email and asks
> Rita for that customer's history. Cal checks whether we've broken a
> policy or promise. Mia writes the reply and tells Rita what we did.
>
> When an email arrives, Gary lets it in; Hana pulls the customer's file
> from Rita and reads the email; Cal flags any policy or promise problem;
> Mia writes the reply and tells Rita to update the file. Only once Rita
> has the update does Gary let the next email in.
>
> Baked-in choices — one email at a time; Rita alone keeps the files and
> everyone else asks her; Mia has the final say. Tell me if any of these
> should be different.

---

## Now explain this office
Agents:
  yahoo_finance — source: financial data & analyst forecasts · sends -> fair_merge
  bloomberg     — source: financial data & analyst forecasts · sends -> fair_merge
  news_feeds    — source: breaking news, a few feeds · sends -> fair_merge
  Gus    — gate: let one piece of information in at a time · sends admitted item -> Warren, Bill, Don, Herb
  Warren — value analyst · reads: current item, Rachel · sends: argument -> Meg ; argument + model-portfolio update -> Rachel
  Bill   — opportunities analyst · reads: current item, Rachel · sends: argument -> Meg ; argument + model-portfolio update -> Rachel
  Meg    — merge_synch(inports: [warren, bill]) · sends the pair -> Don
  Herb   — tax-and-fees analyst · reads: current item, proposed action · sends: tax+fees report -> Don
  Don    — decision maker · reads: current item, both arguments, Herb's report, Rachel · sends: proposed action -> Herb ; final action -> decisions ; final action + real & model-portfolio update -> Rachel ; done -> Gus
  Rachel — record(holds: arguments, actions, real portfolio, model portfolios for Warren/Bill/Don)
  decisions — sink
Wiring:
  yahoo_finance, bloomberg, news_feeds -> fair_merge -> Gus
  Gus -> Warren, Bill, Don, Herb
  Warren -> Meg ; Bill -> Meg ; Meg -> Don
  Don <-> Herb
  Warren <-> Rachel ; Bill <-> Rachel ; Don <-> Rachel
  Don -> decisions ; Don ..done..> Gus
Notes:
  One item at a time (Gus, released by Don's done). Don needs both arguments (Meg). Don proposes an action and waits for Herb's tax/fees before finalizing.
