# Case 07 — News subscriptions (dynamic subscribers, compute once)

**What's new in the instructions being tested:** nothing — this is a baseline test of
`start_instructions.md` and `start_gallery/` exactly as they stand, with no changes
made for this case. It probes a pattern none of the four gallery examples demonstrate:
an unbounded, dynamic set of external parties who each register interest in a different
slice of the same computed fact, where the fact must be computed once regardless of how
many parties want it, plus a request ("is the story positive") that doesn't correspond
to anything the office was described as already computing.

This case matters beyond the usual scorecard: it's evidence for whether Pat-speak alone
(no separate "Al" / structural-description mode) is sufficient for this class of
problem, or whether testers would need a different entry point to reach a correct
compute-once design.

## Pre-registration (written before running)

Pat's description (given verbatim to the cold instance):

> "I want to build an office that watches the news for me and my friends. It should
> follow BBC, Al Jazeera, and NPR, and work out useful things about every story — who's
> involved, how serious it is, what it's about, and where it happened.
>
> Any of my friends can tell the office what they want to hear -- eg. who is mentioned,
> is the story positive -- about a story. From then on they should get that information,
> for every new story, without me having to pay for the same story to be looked at again
> and again for each friend who's watching for something. A friend can also say to stop,
> and after that they shouldn't hear anything more, but nobody else should be affected.
>
> I'd also like to be able to see everything myself, regardless of who's asked for what
> — a running view of the whole thing, not just what any one friend sees.
>
> My friends aren't part of the office — they just send it requests, and it sends them
> what they asked for."

Expected: one shared analysis step per story (not one per friend); a single
subscriptions-holding worker with its own private, per-friend memory, needing neither a
gate nor a registered record since only that one worker ever touches it; friends modeled
as external source/sink, not as agents; Pat's own view as a separate, unconditional
sink. Whether the "who's involved / how serious / what it's about / where it happened"
step is built as one transform or as several joined by a merge_synch was **not**
pre-registered as right or wrong — Pat's words don't name separate workers for it the
way, say, investment_club names two analysts, so either shape is a legitimate reading.

**Known weakness in this pre-registration, noted honestly:** I don't know in advance
whether "is the story positive" will be handled by (a) proposing a new fact for the
analysis step to compute and flagging it under "Things I assumed," (b) asking Pat
directly instead of guessing, or (c) silently folding "positive" into an existing fact
like severity or topic. (a) and (b) are both fine outcomes under the instructions'
"make your best guess — she can correct it" rule; only (c) is a real miss, since it
changes the meaning of what gets delivered without telling Pat. I registered this as the
single most informative thing to watch for, alongside compute-once.

## Protocol

A fresh subagent was given only: `start_instructions.md`, `start_gallery/README.md`,
`start_gallery/investment_club.md`, `start_gallery/room_monitor.md`,
`start_gallery/trading_room.md` — explicitly instructed not to read anything else (no
HANDOFF.md, no other cold-test transcripts, no DSL/dissyslab files). It confirmed at the
top of its reply which five files it read.

## Cold instance's full reply

I read all five of the requested files:

1. `/Users/kmchandy/Documents/OfficeSpeak/offices/claude_project/start_instructions.md`
2. `/Users/kmchandy/Documents/OfficeSpeak/offices/claude_project/start_gallery/README.md`
3. `/Users/kmchandy/Documents/OfficeSpeak/offices/claude_project/start_gallery/investment_club.md`
4. `/Users/kmchandy/Documents/OfficeSpeak/offices/claude_project/start_gallery/room_monitor.md`
5. `/Users/kmchandy/Documents/OfficeSpeak/offices/claude_project/start_gallery/trading_room.md`

No other file was read.

---

### Phase 1 — the network

**Agents**

- **BBC / AL_JAZEERA / NPR** — *sources*. Outbox `out`. Stream raw stories from each feed.
- **ANALYZER** — *transform*. Inbox `in`. Outbox `out`. Reads one raw story at a time
  and works out, once: who's involved, how serious it is, what it's about, where it
  happened, and its tone (positive/negative). Sends the enriched story.
- **ROUTER** — *transform* (a keeper). Inbox `in`. Outbox `to_friend`. Keeps, per friend
  currently watching, what they asked to hear about. On a friend's request: update or
  erase that friend's entry. On an enriched story: check it against every watching
  friend's entry and send each match its requested piece.
- **FRIEND_REQUESTS** — *source*. Outbox `out`. A friend's subscribe/stop message,
  tagged with which friend.
- **FRIEND_OUTBOX** — *sink*. Inbox `in`. Delivers a matched piece to the friend it's for.
- **PAT_VIEW** — *sink*. Inbox `in`. Every enriched story, unfiltered.

**Connections**

- (BBC, out, ANALYZER, in)
- (AL_JAZEERA, out, ANALYZER, in)
- (NPR, out, ANALYZER, in)
- (ANALYZER, out, PAT_VIEW, in)
- (ANALYZER, out, ROUTER, in)
- (FRIEND_REQUESTS, out, ROUTER, in)
- (ROUTER, to_friend, FRIEND_OUTBOX, in)

**What the shape shows (cold instance's own words):** the three feeds fan in to
ANALYZER's one inbox, no coordinator needed since nothing needs pairing. ANALYZER's one
outbox fans out two ways — straight to Pat's view, and into ROUTER — so a story is
analyzed exactly once no matter how many friends are watching or what they each asked
for. ROUTER is a keeper, not a plain record, because it does real matching work each
time; no gate, because nobody reads *and* writes the same information as one multi-step
unit — a friend's request is a single, self-contained update.

**Meet the team / org chart / story of one item** — given in full; summarized: a story
lands on ANALYZER once, a copy goes straight to Pat's view, another goes to ROUTER,
which checks its notes on currently-watching friends and sends each a match only what
they asked for; a friend who said stop earlier gets nothing, and nobody else is affected.

**Things I assumed —**

- Added a **tone** (positive/negative) fact to ANALYZER's output, beyond the four Pat
  named, since "is the story positive" needs it.
- A friend can only ask about the kinds of facts ANALYZER actually produces.
- A friend identifies themselves in every request; how FRIEND_OUTBOX actually reaches
  them (text/email/chat) is left for a later step.
- A new request replaces a friend's old one; "stop" erases it with no memory kept.
- A newly-subscribing friend only gets stories going forward, not a backfill of past
  stories.
- Any number of friends watch independently; one stopping never affects another.
- Pat sees every story regardless of subscriptions and is not "one of the friends" in
  ROUTER's bookkeeping.

### Phase 2 — the agent descriptions

- **BBC / AL_JAZEERA / NPR** *(sources)* — each feed; one raw story at a time as published.
- **ANALYZER** *(transform)* — reads one raw story once; works out who's involved, how
  serious, what it's about, where it happened, and tone; sends the enriched story.
  Processed here exactly once regardless of how many friends turn out to be interested.
- **ROUTER** *(transform, a keeper)* — a per-friend note of what they currently want (or
  nothing). On a request: replace or erase that friend's note. On an enriched story: for
  every friend with a note, check the story's facts against it and send each match the
  specific piece asked for. A story matching nobody produces nothing.
- **FRIEND_REQUESTS** *(source)* — the front door for a friend's request or stop, tagged
  with who sent it.
- **FRIEND_OUTBOX** *(sink)* — delivers a matched piece to the friend it's addressed to.
- **PAT_VIEW** *(sink)* — Pat's running, unfiltered view of every enriched story.

---

## Scoring

| Criterion | Result |
|---|---|
| Compute-once, not recompute-per-friend | **PASS** — ANALYZER runs once per story and fans out to both PAT_VIEW and ROUTER; ROUTER matches any number of friends off that one enriched copy. Stated explicitly, twice, in the reply. |
| Handling of the unmapped request ("is the story positive") | **PASS, and notably good** — chose option (a) from the pre-registration: added a `tone` fact to ANALYZER and flagged it plainly under "Things I assumed," rather than silently folding it into severity/topic (the miss case) or stopping to ask. |
| Friends modeled as external, not as agents | **PASS** — FRIEND_REQUESTS/FRIEND_OUTBOX are ordinary source/sink; friends never appear as agents inside the office. |
| Pat's own view kept separate and unconditional | **PASS** — PAT_VIEW is a distinct sink fed directly from ANALYZER, and the reply says explicitly Pat "is not one of the friends" in ROUTER's bookkeeping. |
| No unwarranted gate or record on the subscription table | **PASS** — ROUTER is correctly identified as a single-inbox keeper (citing the same reasoning trading_room's LEDGER teaches); no gate, no registered record, matching the pre-registration's expectation that this pattern shouldn't apply since only one worker ever touches the table. |
| Analysis-step decomposition (one transform vs. several + merge_synch) | **Not scored** — pre-registered as either being a legitimate reading. Cold instance chose one transform (ANALYZER); reasonable, not a miss. |
| Scope discipline (Phase 1/2 separation, valid 4-tuples, agent-vs-worker register in the explain-back) | **PASS.** |

**Verdict: PASS, 5/5 on the criteria that were actually scored** (one criterion was
explicitly not scored per the pre-registration). No instructions or gallery fix is
indicated by this case.

## What this adds to the open question about Al vs. Pat-only

This is a second data point (after the reasoning that motivated task #30) that Pat-speak
alone, on the current unmodified instructions, converges correctly on a genuinely new
pattern class (dynamic multi-party subscription with compute-once sharing) without any
DSL-style structural description and without any gallery example that teaches this
pattern directly. It does not by itself settle whether Al-speak is still worth keeping
for other reasons (see HANDOFF.md's discussion of Al vs. Pat) — it only bears on the
narrower question of whether testers using Pat-speak alone would get a good result on
this specific class of problem. On this one case, they would have.

## Follow-up worth considering

Run a corresponding *correction* round: give the built office back to a fresh cold
instance along with a plausible Pat correction (e.g., "Actually, I'd like new friends to
get the last day's worth of stories when they first sign up, not just what comes in
after") to see whether backfill — one of the assumptions this case's cold instance
flagged rather than resolved — is handled well once Pat actually asks for it. This would
mirror the two-round build→correct structure used in cases 01/02 and in the
investment_club and trading_room gallery examples themselves.
