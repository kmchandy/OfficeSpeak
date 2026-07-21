# Cold test 02 — Loan desk (correction loop)

**Setup.** Fresh subagent reads only `start_instructions.md` + the three gallery
files, is given the office built in case 01, plus Pat's plain-English correction, and
does the correction step.

**Pat's correction.**
> "I actually have two offer-writers — one for consumer loans, one for business loans —
> but they both draw against the same total-risk limit for the whole desk. Make sure we
> never go over that shared limit."

**Pre-registration (expected correct revision).** The risk total is now **shared by two
writers**, so it can no longer be one writer's private memory. Introduce shared-state
coordination: a keeper (`RISK_LEDGER` both writers ask-and-wait against — the
trading_room pattern) or a registered `record` + `gate`. Tests: recognizing the private→
shared flip (the **inverse** of case 01) and adding the right machinery; avoiding the
failure of keeping it private or duplicating it per writer.

**Verdict: PASS (textbook).** Recognized the flip and stated why; introduced `RISKBOOK`
keeper with fan-in of the two writers' requests; single-inbox **atomic check-and-commit**
(no gate needed); routed consumer/business via scorer outboxes ("ordinary sorting");
named it a keeper, not the registered record. Also flagged the near-simultaneous
double-approval hazard and how the atomic step prevents it.

---

## Full transcript

## What you changed, and why it matters

Right now there's one offer-writing worker, and it keeps the desk's running risk total in **its own memory**. That was fine when it was the only one making offers — it always knew the true total because it was the only one adding to it.

Now you have **two** offer-writers, consumer and business, and they share **one** limit for the whole desk. If each kept its own private total, neither would ever see the other's committed loans. Two offers could each look fine on its own and still push the desk over the shared limit together. So the running total can't live inside the offer-writers anymore.

The fix is the same shape as a trading desk's ledger: move the shared total out into **one worker that both offer-writers check with**. Before either one makes an offer, it asks this shared risk-keeper "can I commit this much?" The risk-keeper holds the single desk-wide total, and it answers **one request at a time**. It looks at the request, and if the current total plus this loan still fits under the limit, it adds the loan to the total and says "approved"; otherwise it says "rejected." Because it handles the requests one at a time, two offers can never both slip under the limit and then jointly blow past it — the shared limit is always respected.

Only on an "approved" does the offer-writer actually write the offer (rate and amount) and save it. On a "rejected," it writes nothing.

I also split the scoring worker's output: after it scores an application and decides it passes, it now hands it to the **consumer** offer-writer or the **business** offer-writer depending on the kind of loan. That's just ordinary sorting — no special machinery.

## Revised agents

- **APPLICATIONS** — *source*. Outbox `out`. Loan applications, one at a time. *(unchanged)*
- **SCORER** — *transform*. Inbox `in`. Outboxes `to_consumer`, `to_business`. Scores an application for risk and decides pass/fail; for a passing application, sends `{application, risk}` to the consumer or the business offer-writer depending on the loan type; otherwise sends nothing. *(now routes to one of two)*
- **OFFERWRITER_CONSUMER** — *transform*. Inbox `in`. Outboxes `request`, `offer`. For a passing consumer application, asks the risk-keeper to reserve this loan's risk; on "approved" writes an offer (rate + amount) and sends it; on "rejected" sends nothing. *(no longer keeps its own total)*
- **OFFERWRITER_BUSINESS** — *transform*. Inbox `in`. Outboxes `request`, `offer`. Same, for business loans. *(new — the second offer-writer)*
- **RISKBOOK** — *transform (a keeper)*. Inbox `in`. Outboxes `reply_consumer`, `reply_business`. Keeps the desk's **single** running total of committed risk. For each reservation request, if the total plus this loan's risk stays within the shared limit, adds it to the total and replies "approved," otherwise replies "rejected." Handles one request at a time. *(new — holds what used to live inside the lone offer-writer)*
- **OFFERS** — *sink*. Inbox `in`. Writes each offer to a file. *(unchanged)*

*(RISKBOOK applies the limit rule and answers each offer-writer, so it does more than store — it's a keeper transform, like the trading desk's ledger, not the bare registered `record`.)*

## Revised connections

- (APPLICATIONS, out, SCORER, in)
- (SCORER, to_consumer, OFFERWRITER_CONSUMER, in)
- (SCORER, to_business, OFFERWRITER_BUSINESS, in)
- (OFFERWRITER_CONSUMER, request, RISKBOOK, in)
- (OFFERWRITER_BUSINESS, request, RISKBOOK, in)
- (RISKBOOK, reply_consumer, OFFERWRITER_CONSUMER, in)
- (RISKBOOK, reply_business, OFFERWRITER_BUSINESS, in)
- (OFFERWRITER_CONSUMER, offer, OFFERS, in)
- (OFFERWRITER_BUSINESS, offer, OFFERS, in)

The two offer-writers' requests **fan in** to RISKBOOK's one inbox, and each offer-writer's inbox receives both its scored applications and the risk-keeper's reply back to it. There's **no coordinator and no gate** — RISKBOOK stays consistent simply because it takes one request at a time from its single inbox and adds to the total as one atomic step. Both offer-writers still save to the one OFFERS file.

**Things I assumed —** the shared limit lives entirely in the risk-keeper now, so it's the single source of truth for how much risk the whole desk has taken on; the risk-keeper both checks *and* commits in one step (an offer-writer never gets an "approved" without the total already being updated, so two near-simultaneous offers can't both be told yes when only one fits); and while an offer-writer is waiting for the risk-keeper's answer it doesn't send a second request. Tell me if you'd rather an offer-writer completely stop and wait for the answer before even looking at its next application — that's a small change if you want it.
