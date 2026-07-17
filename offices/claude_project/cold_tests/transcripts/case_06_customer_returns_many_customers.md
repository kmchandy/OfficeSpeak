# Case 06 — Customer returns, many customers at once

**What's new in the instructions being tested:** the "Many of the same kind at once"
section (added after case 05), teaching: keep one set of agents; tag every message with
which person/thing it's about; any agent's memory becomes one slot per tag instead of
one shared slot; a new arrival is a source message, not a new agent; a trail to a
different audience (e.g. a parent, a manager) gets its own tag.

Domain is deliberately **not** tutoring, so this tests transfer of the pattern rather
than recognition of the worked example already in the instructions.

## Pre-registration (written before running)

Pat's description (single case, then "many at once" + a second audience):

> "I want an office that handles a customer's return request: the customer describes
> what's wrong with their order, a worker decides whether it qualifies for a refund or
> an exchange and takes that action, keeping track of how many issues this particular
> customer has had. Now I want it to handle many customers at once, each having their
> own conversation with us at the same time, and I'd like the store manager to be able
> to check in on how a particular customer's issues are trending."

Expected: one CLERK (or similarly named decider) handling every customer, no
per-customer replication; every message tagged by customer; a manager-facing trend
check-in modeled as its own trail. Chiefly testing whether the cold instance (a) avoids
building a separate office per customer, (b) tags messages correctly, (c) generalizes
whatever holds the issue count to "one entry per customer," and (d) shows restraint
about tagging the manager side (only one manager was mentioned — a manager-tag is
warranted only if Pat says there's more than one manager).

**Known weakness in this pre-registration, noted honestly:** because the manager needs
to see data the clerk produces, this domain accidentally created a genuine two-accessor
case (clerk writes, trend-checker reads) rather than a clean single-accessor-plus-many-
tags case. That means this case can't cleanly test "does the cold instance correctly
avoid over-promoting private per-tag state into a record" — it can only test "does it
correctly generalize a record's rows to one-per-tag," which is a real but narrower
question. A cleaner test of the pure private-per-tag case (nobody else ever reads it) is
still needed — see follow-up below.

## Protocol

A fresh subagent was given only: `start_instructions_v3.md`, `start_gallery/README.md`,
`start_gallery/investment_club.md`, `start_gallery/room_monitor.md`,
`start_gallery/trading_room.md` — explicitly instructed not to read anything else
(no HANDOFF.md, no phase2_demo code, no other cold-test transcripts). It confirmed at
the top of its reply which five files it read.

## Cold instance's full reply

I read exactly these five files:

1. `/Users/kmchandy/Documents/OfficeSpeak/offices/claude_project/start_instructions_v3.md`
2. `/Users/kmchandy/Documents/OfficeSpeak/offices/claude_project/start_gallery/README.md`
3. `/Users/kmchandy/Documents/OfficeSpeak/offices/claude_project/start_gallery/investment_club.md`
4. `/Users/kmchandy/Documents/OfficeSpeak/offices/claude_project/start_gallery/room_monitor.md`
5. `/Users/kmchandy/Documents/OfficeSpeak/offices/claude_project/start_gallery/trading_room.md`

No other file was read.

---

### Phase 1 — the network

**Agents**

- **CUSTOMER** — *source*. Outbox `out`. Whenever a customer files a return request, sends what's wrong with the order — tagged with that customer.
- **CLERK** — *transform*. Inbox `in`. Outboxes `to_history`, `decision`. For whichever customer a message names: decides whether the problem qualifies for a refund or an exchange, sends that decision as an action to take, and logs the issue to that customer's history.
- **HISTORY** — registered **record** (holds: each customer's issue history — a running count and the list of past issues). Inbox `req`. Outbox `reply`.
- **ACTION** — *sink*. Inbox `in`. Carries out the refund or exchange for a customer's order.
- **MANAGER_QUERY** — *source*. Outbox `out`. Whenever the store manager wants to check in on a particular customer, sends a request naming that customer.
- **TREND** — *transform*. Inbox `in`. Outboxes `to_history`, `out`. For whichever customer the manager named: asks HISTORY for that customer's issue record and writes a short summary of how the issues are trending.
- **MANAGER_VIEW** — *sink*. Inbox `in`. Shows the store manager the trend summary for whichever customer was looked up.

**Connections**

- (CUSTOMER, out, CLERK, in)
- (CLERK, to_history, HISTORY, req)
- (CLERK, decision, ACTION, in)
- (MANAGER_QUERY, out, TREND, in)
- (TREND, to_history, HISTORY, req)
- (HISTORY, reply, TREND, in)
- (TREND, out, MANAGER_VIEW, in)

**Pass A — every outbox**

- CUSTOMER.out — `{customer, order, description_of_problem}`.
- CLERK.to_history — `{customer, issue: {order, description, decision}}`.
- CLERK.decision — `{customer, order, decision: refund|exchange, details}`.
- MANAGER_QUERY.out — `{customer}`.
- TREND.to_history — `{customer}` (a lookup).
- HISTORY.reply — the data requested: for a lookup, `{customer, issue_count, list_of_past_issues}`.
- TREND.out — `{customer, issue_count, trend_description}`.

**Pass B — every inbox**

- CLERK.in — return requests, from CUSTOMER.out only.
- HISTORY.req — two kinds, interleaved: updates from CLERK.to_history, lookups from TREND.to_history.
- ACTION.in — action messages, from CLERK.decision only.
- TREND.in — two kinds, interleaved: check-in requests from MANAGER_QUERY.out, HISTORY's reply.
- MANAGER_VIEW.in — trend summaries, from TREND.out only.

Note (cold instance's own observation): HISTORY's reply to a CLERK *update* isn't wired anywhere — nobody needs to see it, the same way the ledger's reply to the manager's write in the investment-club example wasn't routed back. Only the reply to a *lookup* is connected.

**Meet the team / org chart / story of one item** — given in full in the reply; summarized: a customer's complaint goes to the clerk, who decides and hands off to fulfillment while logging the issue to the shared issues log; separately, the manager's lookup goes to a trend-checker who reads the same log and reports back.

**Things I assumed —**

- The clerk decides refund-or-exchange from *this* complaint alone, not from the customer's past-issue count — flagged as a connection worth double-checking with Pat.
- A return is a single exchange, not a back-and-forth conversation.
- "How many issues" is a simple count of returns filed.
- The manager looks a customer up on demand (pull), not an automatic alert.
- **There's one store manager, so the manager's screen isn't tagged by which manager — only by which customer is being checked; a case with several managers would need each manager's own filed view.**
- **Many customers are handled by the very same small team at once — nobody gets their own copy — with the issues log keeping one entry per customer, and the clerk's and trend-checker's work always naming which customer it concerns.**

### Phase 2 — the agent descriptions

(HISTORY is a registered record, not described.)

- **CUSTOMER** *(source)* — the store's return-request intake; emits a customer's problem description tagged with that customer.
- **CLERK** *(transform)* — weighs the complaint against return policy, decides refund vs exchange, sends the action, and logs the issue to that customer's entry in the shared log.
- **ACTION** *(sink)* — the refund/payment system or exchange-shipment process.
- **MANAGER_QUERY** *(source)* — the manager's dashboard search box.
- **TREND** *(transform)* — looks up a customer's record and writes a plain-language trend summary.
- **MANAGER_VIEW** *(sink)* — the manager's screen.

---

## Scoring

| Criterion | Result |
|---|---|
| One team, no per-customer replication | **PASS** — explicit in "Things I assumed," and the design has exactly one CLERK/HISTORY/TREND for everyone. |
| Every message tagged by the right id | **PASS** — every payload carries `customer`. |
| Record generalized to one row per tag | **PASS** — HISTORY explicitly described as "one entry per customer." |
| Restraint on the second-audience tag | **PASS, and notably good** — it did *not* invent a manager-tag since Pat only mentioned one manager, and it said so explicitly, naming exactly when a manager-tag *would* be needed (several managers). This is the over-engineering-avoidance criterion working correctly on the new pattern, not just the old one. |
| New-arrival-as-message vs. new-arrival-as-agent | **Partial / domain-adapted** — no explicit "session start" message, but this domain doesn't have a session (a return is one request-response, not an ongoing conversation like the tutor), so there was nothing for a start event to open. Reasonable adaptation, not a miss. |
| Private-vs-shared state on the new pattern specifically | **Not cleanly isolated by this test** — see the pre-registration caveat above; HISTORY is shared for the *original* reason (two agents touch it: CLERK writes, TREND reads), so this case doesn't test whether the cold instance would wrongly promote a truly single-accessor, keyed-by-tag memory into a record+gate. Needs a follow-up case. |
| No unwarranted gate | **PASS** — CLERK only writes, TREND only reads; no gate added, consistent with case 04's "no gate without a genuine read-and-write accessor." |
| Scope discipline (no code, Phase 1/2 separation, agent-vs-worker register in the explain-back) | **PASS**. |

**Verdict: PASS**, with one gap in the test design itself (noted above and carried
forward as a follow-up) rather than in the instructions or the cold instance's answer.

## Follow-up needed

Run one more cold case where the per-tag memory is touched by **only one** agent and
nobody else ever reads it (the tutor's own PROGRESS is exactly this shape: only PLANNER
touches it) — but in a new, non-tutor domain — to test whether "many of the same kind"
is correctly read as "still private, still no record/gate, just filed by tag" rather
than being over-promoted to a shared keeper just because there are now many customers/
students/callers instead of one.
