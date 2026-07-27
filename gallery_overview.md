# The gallery — find an office like yours

Everything here is real: built, run, and checked against real output — not
mockups or sketches. Skim this the way you'd browse a neighborhood before
choosing where to live: not to copy a house exactly, but to get a feel for
what's possible and find the one closest to what you already have in mind.
If you find one that's close, describe yours the same way, borrowing its
shape; if nothing here quite fits, describe yours anyway — the assistant
builds a first draft from nothing but your own words just as easily.

Prefer a two-minute visual version? See
[`gallery_microcourse.html`](https://kmchandy.github.io/OfficeSpeak/gallery_microcourse.html) —
same material, no reading required, plus three real quotes from offices
actually being built live. This page is the version with enough detail to
actually search through.

## Quick index

| Office | What it does | Shape | Setup |
|---|---|---|---|
| [room_monitor](#watching-and-listening-to-the-world) | Mic listens to a room, alerts on anything unusual | Watch & alert | none |
| [weather_monitor](#watching-the-news-and-markets) | Hourly plain-English weather briefing | Watch & alert | none |
| [stocks_monitor](#watching-the-news-and-markets) | One-line read of a stock's movement | Watch & alert | none |
| [periodic_brief](#watching-the-news-and-markets) | News + weather + stocks, one morning page | Watch & alert | none |
| [periodic_brief_pro](#watching-the-news-and-markets) | Same, plus tagged news, calendar, Gmail | Watch & alert | keys |
| [situation_room](#watching-the-news-and-markets) | Three feeds → four thinkers → one briefing | Several weigh in, one decides | keys |
| [situation_room_pro](#watching-the-news-and-markets) | Same, split across cheap + premium models | Several weigh in, one decides | keys |
| [arxiv_radar](#watching-the-news-and-markets) | Daily papers rated for relevance | Watch & alert | keys |
| [kalshi_market_watch](#watching-the-news-and-markets) | Prediction-market moves, explained | Watch & alert | keys |
| [competitor_watch](#watching-the-news-and-markets) | Competitor news, tagged and digested | Watch & alert | keys |
| [inbox_triage](#personal-and-productivity) | Gmail sorted by urgency into a Slack digest | Watch & alert | keys |
| [ticket_router](#personal-and-productivity) | Support tickets classified and routed | Watch & alert | keys |
| [lead_qualifier](#personal-and-productivity) | Form submissions summarized into your CRM | Watch & alert | keys |
| [new_grad_jobs](#personal-and-productivity) | Hiring-thread postings screened for fit | Watch & alert | keys |
| [job_hunter](#personal-and-productivity) | Job feed matched to your resume | Several weigh in, one decides | keys |
| [wardrobe_assistant](#personal-and-productivity) | Calendar + weather → outfit pick | Watch & alert | keys |
| [backyard_birds](#watching-and-listening-to-the-world) | Audio → bird species ID | Watch & alert | none |
| [wildlife_watcher](#watching-and-listening-to-the-world) | Camera-trap photos → species labels | Watch & alert | none |
| [loudness_monitor](#watching-and-listening-to-the-world) | Mic → threshold-crossing alert | Watch & alert | none |
| [debate](#teams-that-deliberate) | Panel debates a question in rounds | Take turns in rounds | keys |
| [investment_club](#teams-that-deliberate) | Two analysts, a manager, a shared ledger | Shared ledger, one at a time | none |
| [trading_room](#teams-that-deliberate) | Trades proposed, checked against limits | Propose, then get approval | none |
| [loan desk](#real-unedited-conversations) *(transcript)* | Risk-checked loan offers against a shared limit | Propose, then get approval | — |
| [adaptive tutor](#real-unedited-conversations) *(transcript)* | A coach, a quizmaster, a progress keeper | Several weigh in, one decides | — |
| [customer returns](#real-unedited-conversations) *(transcript)* | Many customers at once, one team, tagged | Shared ledger, one at a time | — |
| [shipment release](#real-unedited-conversations) *(transcript, built & run)* | Match a scan to its paperwork, then release | Watch & alert | — |

*("keys" means an LLM backend and/or a third-party credential — Gmail, Slack,
a calendar URL. "none" means it runs the moment you install it.)*

---

## Which shape is like yours?

Almost everything below is one of four shapes. Find the one that matches how
your workers actually relate to each other, and you've found your starting
point.

**Watch one thing, speak up when it matters.** One stream of information
comes in — a feed, a mailbox, a microphone, a camera — a worker or two watch
it, and something goes out only when it's worth noticing. This is the
biggest category by far: most of the news-and-markets apps, the
perception apps (birdsong, camera traps, loudness), and most of the
personal-productivity apps all have this shape underneath, even when the
"something worth noticing" is different every time.

**Take turns, in rounds, until it's settled.** Workers go back and forth —
each round, everyone weighs in — until one of them decides it's done and
writes the final answer. `debate` is the clean example.

**Share one ledger, and handle things one at a time.** Several workers read
and update one common record — a portfolio, a customer's history, a running
total — and things are handled one item at a time so the shared record never
gets out of sync. `investment_club` is the clean example; the loan-desk and
customer-returns transcripts below show the same shape in new domains.

**Propose something, then wait for approval.** A worker wants to do
something, but has to check it first — against a shared limit, a policy, a
manager — and waits for the answer before acting. `trading_room` is the
clean example; the loan-desk transcript is the same shape too.

A few offices don't fit neatly into one bucket — `situation_room` and
`job_hunter` both have several workers independently look at the same thing
from different angles before one worker combines their views, which is its
own small variation on "several weigh in, one decides." That's fine; these
four shapes are a starting point for finding something close, not a strict
taxonomy.

---

## Watching the news and markets

The largest cluster in the gallery — offices that watch a live feed and
react, the pattern most people mean when they say "I want something that
watches X for me."

**periodic_brief** — the simplest of these, and worth starting with: it
combines BBC and NPR headlines, Pasadena's weather, and a few stock tickers
into one clean morning page. No AI calls at all — pure orchestration of
public feeds into something readable. **periodic_brief_pro** is the richer
version of the same idea: it tags every article by entity, topic, and
urgency before writing per-article briefs, and folds in your Google
Calendar and Gmail too.

**weather_monitor** and **stocks_monitor** are the two smallest useful
examples — an hourly plain-English weather read, and a one-line read of a
ticker's movement. Good starting points if your whole office is "watch one
number or one feed and say something short about it."

**situation_room** is the framework's showcase for "several workers each
look at the same thing differently, then one worker combines their views":
three news feeds get deduplicated, then four parallel thinkers tag each
story by entity, severity, topic, and geography, and a writer turns all
four views into one briefing — archived to both the terminal and a JSONL
file. **situation_room_pro** is the same structure with a twist worth
knowing about: the four "thinker" workers run on a cheap, open-weight
model, while the writer that turns their work into prose runs on Claude —
a real demonstration of mixing cheap and expensive judgment inside one
office, using only the workers that actually need the better model.

**arxiv_radar** watches daily arXiv postings in topics you pick and rates
each one for relevance, so you get a digest of only the papers worth your
time. **kalshi_market_watch** does the analogous thing for prediction
markets — it doesn't just report a price move, it writes out the reasoning
an analyst would give for why the market moved. **competitor_watch** reads
three tech-news sources, tags every article with the entities, sentiment,
and topic involved, and writes a daily digest — the "watch our competitors"
office, if that's closer to what you have in mind than "watch the news."

## Personal and productivity

Smaller-scale offices built around one person's actual daily workload.

**inbox_triage** watches Gmail, rates each unread message for urgency and
sentiment, summarizes it, and drops only the keepers into a Slack channel —
a good starting point if your office's job is "help me not miss the
important email in a pile of unimportant ones." **ticket_router** and
**lead_qualifier** are the same shape applied to two different inboxes: a
support queue (classified by severity/urgency/category, routed to an
oncall Slack channel) and inbound leads (summarized and tagged, then
forwarded to a CRM).

**new_grad_jobs** watches Hacker News' "Who's Hiring" thread and screens
hundreds of postings down to the ones that actually fit an entry-level
search. **job_hunter** goes a step further — RSS job feeds get filtered for
relevance, then matched against your actual resume, and for each real match
it writes a tailored cover letter, a tailored resume, and a background brief
on the company. This one is a good example of "several weigh in, one
decides" showing up somewhere that doesn't look like a news office at all.

**wardrobe_assistant** checks your calendar and the day's weather and
recommends what to wear — small, but a clean example of combining two very
different kinds of information (a schedule, a forecast) into one simple
daily decision.

*(`job_hunter` and `wardrobe_assistant` were built by Caltech undergraduate
Nyasha Makaya; the copies here are reference versions of his own
deployments.)*

## Watching and listening to the world

Offices whose "source" isn't text at all.

**room_monitor** is the simplest possible version of this shape, and the
one to start with if you're not sure: a microphone listens to a room and
puts an alert on the screen when it hears something unusual — a loud noise,
an odd silence, someone talking. **loudness_monitor** is the same idea made
concrete and running: a sliding window over live mic or file audio, with a
threshold-crossing alert, pure signal processing, no AI model at all.

**backyard_birds** takes recorded or live audio clips and runs them through
a real bird-classification model (BirdNET) to identify species with
confidence scores — a nice example of a "worker" that's a local ML model
rather than an LLM or plain code. **wildlife_watcher** does the analogous
thing for camera-trap images, with a confidence filter that drops
low-confidence guesses before they ever reach you.

## Teams that deliberate

Offices built around several workers with real, structured relationships to
each other, not just a pipeline.

**debate** — three panelists on different backends argue a question in
rounds; a moderator reads every round and either calls for another one or,
once it's settled, writes the final answer. The clean example of "take
turns in rounds."

**investment_club** — each period, two analysts (one value-oriented, one
opportunity-seeking) recommend a plan; a manager weighs both, proposes,
checks the cost with an accountant, and writes the final plan — all against
one shared portfolio-and-history record that everyone reads and updates,
handled one period at a time so the books never go inconsistent. This is
the office `README.md`'s own full walkthrough uses, if you want to see it
built and run in complete detail, correction included.

**trading_room** — two traders each propose trades; before either one
executes, a ledger checks the proposal against the desk's positions, cash,
and limits and approves or refuses it. Each trader waits for the answer
before acting — the clean example of "propose, then get approval."

## Small patterns to learn from

If you'd rather see one moving part in isolation than a full office, these
are deliberately minimal — read the office description and you can see the
whole idea in seconds.

**my_first_office** — a single agent, watching Hacker News, the simplest
possible office. **org_news_editorial** — two agents, an analyst feeding an
editor, the smallest possible pipeline. **org_two_office_news** — an office
made of two other offices plugged together, if you're curious what
composition looks like. **org_intelligence_briefing** — a multi-source feed
with a significance filter before anything gets written up.
**org_news_filter** — a pipeline that simply drops anything that doesn't
match a criterion. **org_situation_room** — the older, simpler two-agent
ancestor of the full `situation_room` above, kept as the "just the basics"
reference. **webhook_listener**, **web_monitor**, and **gmail_monitor** each
show one specific way information can arrive from outside — an inbound
HTTP POST, a watched web page, or an unread Gmail inbox.

## Real, unedited conversations

Everything above is a finished office. These are the conversations that
built some of them — a fresh assistant, given nothing but the standard
instructions and gallery, handed one plain-English description and left to
work. No editing, no second takes.

**Loan desk** (propose, then get approval) — "score each application, check
it against a running risk limit, then offer or don't." Its follow-up
correction is the best illustration of a shape *change* in this whole
gallery: told that two desks now share one limit, the assistant correctly
recognized that a private running total had to become a shared ledger both
desks check before committing — the exact inverse of what it had just
built, reasoned out from one sentence of correction.

**Adaptive tutor** (several weigh in, one decides) — a coach that tracks a
kid's mastery of each skill and picks the next question, a quizmaster that
runs the actual back-and-forth, a shared question bank, and a progress
record — built from a single paragraph, with the tricky trap (don't
over-engineer a shared-record gate where only one worker ever writes)
avoided correctly.

**Customer returns, many at once** (shared ledger, one at a time) — the
same one-customer office generalized to handle every customer
simultaneously without duplicating the team — each message tagged by
customer, one shared record generalized to one row per customer, plus a
manager who can check in on any single one.

**Shipment release** (watch & alert) — the one case here that was carried
all the way through, not just designed: approved, generated, and actually
run. The first draft had a real, honest miss in its own explanation, caught
and fixed before anything ran — you can see its real output for yourself,
the same way you'd check any office in this gallery.

All nine cases, including the ones not spotlighted here, are in
`offices/claude_project/cold_tests/transcripts/` — every one pre-registered
before it ran and scored afterward, kept as a real record, not cleaned up
after the fact.

---

## Don't see yours?

That's normal — this gallery is a sample, not a catalogue. Describe your
office the same way you'd describe any of these: what comes in, what you
want to happen, who does what, and any rules like "one at a time" or "wait
for the answer." The assistant builds a first draft and explains it back to
you regardless of whether anything here was close. See `README.md`, Stage
1, step 2.
