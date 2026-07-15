# Cold test 01 — Loan desk (build)

**Setup.** Fresh subagent reads only `start_instructions_v3.md` + the three gallery
files, then acts as the assistant.

**Pat's description.**
> "I run a small loan desk. Loan applications come in one at a time. I want something
> that scores each application for risk, and for the ones that pass, writes a loan offer
> with a rate and an amount. But before it makes an offer it should check the total risk
> we've already taken on from the loans we've already offered — if this new loan would
> push our total risk over our limit, don't make the offer. Save the offers to a file."

**Pre-registration (expected correct office).** `APPLICATIONS`(source) →
`RISK_SCORER`(transform) → `OFFER_WRITER`(**stateful** transform, keeps running risk
total in its own memory) → `OFFERS`(sink). No coordinator, no record, no gate. Tests:
restraint; **private state → stateful transform, not record+gate** (over-engineering
trap, given investment_club sits in the gallery); needs-to-see (score must flow to the
offer-writer); explain-back surfaces the limit/threshold assumptions.

**Verdict: PASS.** Exact structural match. Kept the running total as the offer-writer's
own memory with explicit reasoning; no record/gate. Score flows to the offer-writer.
Strong "Things I assumed" that even offered the private-vs-shared choice back to Pat.
Benign variance: pass/fail folded into the scorer (fail-fast) rather than the
offer-writer.

---

## Full transcript

## Phase 1 — the network

**Agents**

- **APPLICATIONS** — *source*. Outbox `out`. Brings in loan applications from outside the office, one at a time.
- **SCORER** — *transform*. Inbox `in`. Outbox `out`. Reads one application, works out a risk score for it, and decides whether it passes. If it passes, sends the application together with its risk score onward; if it fails, sends nothing.
- **OFFERWRITER** — *transform*. Inbox `in`. Outbox `out`. Keeps a running total of the risk already taken on from loans it has already offered. Reads a passing, scored application; checks whether adding this loan's risk would push the running total over the limit. If it stays within the limit, it writes a loan offer (a rate and an amount), sends the offer out, and adds this loan's risk to its running total; if it would go over the limit, it sends nothing and leaves the total unchanged.
- **OFFERS** — *sink*. Inbox `in`. Writes each loan offer to a file.

**Connections**

- (APPLICATIONS, out, SCORER, in)
- (SCORER, out, OFFERWRITER, in)
- (OFFERWRITER, out, OFFERS, in)

What the shape shows: there is **one** incoming stream — applications arrive one at a time — so there is nothing to fair-merge and **no coordinator**. The running total of risk is used and updated by only one worker, OFFERWRITER, so it is **that worker's own memory** — nothing is shared or written jointly, so there is **no record and no gate**. Because OFFERWRITER takes one application at a time from its single inbox and finishes each before the next (an atomic step), its running total can never be left half-updated. The office is a short line of workers: applications → score → offer-or-not → file.

**Explain it back to Pat** (plain English):

> Applications come in one at a time. The first worker reads each application and gives it a risk score, then decides whether it passes. If it doesn't pass, that's the end of it — nothing more happens. If it passes, the worker hands the application and its score to a second worker. That second worker remembers how much total risk the desk has already taken on from the loans it has already offered. It checks: would offering this loan push our total risk over our limit? If it stays within the limit, the worker writes an offer — a rate and an amount — saves it to the offers file, and adds this loan's risk to its running total. If it would go over the limit, the worker makes no offer and the total stays where it was.
>
> **Things I assumed —**
> - **What "score" and "pass" mean:** the first worker turns each application into a single risk number and passes it only if that number is good enough (a threshold). I don't yet know what goes into the score or where the pass line sits — tell me and I'll pin it down.
> - **What "total risk" and "limit" mean:** the running total is the sum of the risk contributions of the loans already offered, and the limit is a fixed ceiling on that total. I assumed the check is "current total + this loan's risk ≤ limit." Tell me if the total or the limit should be measured differently (for example, by dollar amount rather than by risk score).
> - **Who watches the running total:** only the offer-writing worker needs it, so I kept it as *that worker's own memory* rather than a separate shared ledger. This is safe because applications are handled one at a time in a single line. If you'd like other workers (or you) to see the running total, or want it kept in a shared book of its own, that's an easy change — just say so.
> - **What the offer-writing worker needs to see:** it needs both the application's risk (it gets that from the first worker) and the running total (it holds that itself) — so it has everything it needs to decide. This is the spot where a missing piece would usually hide, so flag it if you think it should also see something else (say, the applicant's requested amount, or past offers) before setting the rate and amount.
> - **A declined loan just produces nothing** — no offer is written and nothing is saved. Tell me if you'd instead like declined applications logged somewhere.
> - **How the rate and amount are chosen** comes from the application and its risk; I've left the exact formula open for now.

## Phase 2 — the agent descriptions

- **APPLICATIONS** *(source)* — the loan desk's stream of incoming loan applications; emit one application at a time, each carrying the applicant's details and requested loan (for example, requested amount, income, and whatever facts the desk uses to judge risk).
- **SCORER** *(transform)* — read one application. Work out a risk score for it from the applicant's details (the higher the score, the riskier the loan). Decide whether the application passes: if its risk is acceptable (within the desk's scoring threshold), send the application onward together with its risk score; if it is too risky, send nothing and drop it. (Whether the score is later a simple rule or a small model is decided in a later step, not here.)
- **OFFERWRITER** *(transform)* — keep a running total of the risk taken on from loans already offered (start at zero). For each passing application it receives, with its risk score: check whether adding this loan's risk to the running total would stay at or under the desk's risk limit. If it would go over the limit, make no offer and leave the total unchanged. If it stays within the limit, draft a loan offer — set a rate and an amount appropriate to the application and its risk — send the offer to the offers file, and add this loan's risk to the running total so later applications are judged against the updated figure.
- **OFFERS** *(sink)* — the file where each loan offer is written (each record including at least the application it answers, the rate, and the amount).
