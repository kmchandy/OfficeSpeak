# investment_club — Pat's office description (scaffolded, held-out test)

Written in the scaffold structure (Sources / Agents+jobs / Information flow).
Clean input — hand this verbatim to a fresh build chat. Our review and
predictions are in `spec_v2_review.md`; do not paste those into the build chat.

---

## Sources of data
I want to build an office that recommends buy, sell, and hold actions for
my investment club, which holds mutual funds and cash. It should watch
financial data and analyst forecasts from Yahoo Finance and Bloomberg,
and breaking news from a few news feeds, New York Times and Wall Street
Journal.

## Agents in the office and job descriptions
The office has analysts, managers and tax specialists. An analyst gets
financial data and news. An analyst also has access to my clubs current
investment portfolio and investment history. An analyst makes recommendations
for actions such as buy, sell, hold stocks in a list of mutual funds.
An analyst's actions are based on the analyst's training and what it has
learned. My office has an analyst, VAL, who makes recommendations based
on a value-investment strategy, and different analyst, OPPO, who makes
recommendations based on a strategy that emphasizes stocks of companies
that use innovation and new technologies.

My office has a manager who gets recommendations from analysts and makes
a recommendation for the office as a whole. The manager makes a tentative
decision and sends it to an accountant who receives proposed actions and
determines taxes and transaction fees for the actions.

## Information flow

Messages from all the data sources are sent to all the analysts in the
office.

Analyst recommendations are sent to the manager. The manager waits to
receive recommendations from all analysts, weighs their arguments, and
makes a tentative decision which is sent to the accountant who computes
the taxes and transaction fees of the tentative decision and sends the
results back to the manager. Then the manager makes a final recommendation
based on all the information the manager received. The final recommendation
is sent to a file.
