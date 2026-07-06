# Review of the scaffolded investment_club spec (spec_v2_scaffolded.md)

A spec-side review: what the structure bought, what gaps remain, and what that
teaches about the scaffold. Done before the held-out build so we can pre-register
predictions.

## What the structure bought us (vs the earlier free-text spec)

The structured description removed most of the *inference* Claude had to do before:

- **Information flow is explicit — and already minimal-fan-out.** "Messages from
  all the data sources are sent to all the analysts" — sources fan out to VAL and
  OPPO *only*; the manager and accountant are demand-driven. That is exactly the
  corrected pattern we had to fix by hand in run_1 (Herb off the fan-out), and Pat
  produced it for free just by describing the flow.
- **The join is stated.** "The manager waits to receive recommendations from all
  analysts" -> merge_synch, no inference.
- **The ask-and-wait is stated.** manager -> accountant -> back -> final ->
  select, no inference.
- **One earlier gap is closed up front.** Analysts are explicitly given "access to
  my club's current investment portfolio and investment history" — the analog of
  the Herb-holdings dependency, stated by Pat this time.

So the structure did its job: the parts that previously caused iterations
(topology, join, back-and-forth, one data dependency) are now given, not guessed.

## Residual gaps (mapped to scaffold fields)

The remaining gaps are genuine Pat-decisions, not topology Claude must guess —
which is the right kind of residue.

1. **[Field 5 — needs to know] The accountant's information needs.** The accountant
   "determines taxes and transaction fees" on proposed actions but is **not** given
   access to the portfolio / cost basis. Transaction fees may be computable from
   the action alone; **taxes need cost basis**, which lives in the portfolio and
   history. This is the Herb-holdings gap **moved one seat over** — from the
   tax analyst to the accountant. Field 5 is exactly where it should have been
   caught; Pat answered it for the analysts but not for the accountant.

2. **[Fields 6/7 — remembers / shared] Who writes the portfolio and history?**
   Analysts *read* the portfolio and history; nobody is said to *write* them, and
   the only output is "final recommendation -> file." So either:
   - the portfolio/history is **read-only reference** (updated outside the office)
     -> then there is **no shared read-modify-write, no gate needed** — a simpler
     office; or
   - the office should **update** the portfolio/history after a final decision ->
     then it needs a write path and consistency.
   Currently ambiguous. This is the single most consequential unstated choice.

3. **[Field 8 — rules] One-at-a-time is omitted, and its necessity is contingent
   on (2).** Pat did not ask for serialization. A gate is needed **only if** the
   office writes shared state (case 2b). So the right move is not to assume a gate
   — it is to resolve (2) first.

4. **[Field 6 — remembers / Stage B] Learning is stated but not operationalized.**
   "based on the analyst's training and what it has learned" — a learning/feedback
   behavior with no mechanism, and (unlike v1) no per-analyst model portfolio. This
   is an agent-body concern (Stage B), fine to leave to the analyst's prompt, but
   worth confirming Pat isn't expecting the office to wire a feedback loop.

## Lessons for the scaffold (feed back into pat_scaffold.md)

- **Strengthen field 5.** For any helper who *computes or decides* something,
  prompt specifically: "what current facts / state do they need to see?" That
  phrasing would have caught the accountant (it computes taxes -> needs cost
  basis).
- **Strengthen field 8.** Ask explicitly: "Does the office **update** any shared
  information? If so, should it finish one item before starting the next?" This
  ties the gate to the write-side and, importantly, *avoids adding a gate when it
  isn't needed* (case 2a).
- **Confirm the payoff.** Structure removed the inference gaps (fan-out, join,
  ask-wait) and closed one data dependency; the residue is exactly the set of
  Pat-decisions the explain-back is meant to confirm. That is the scaffold working
  as intended, not failing.

## Pre-registered predictions for a fresh build (score after the run)

1. High confidence: the build fans sources to VAL/OPPO only; a merge_synch join at
   the manager; a manager<->accountant ask-and-wait; final -> file sink.
2. The accountant will most likely **not** be wired to the portfolio/holdings
   (Pat didn't say) -> the explain-back should flag "the accountant works out
   taxes without seeing what the club currently holds."
3. The build will most likely treat the portfolio/history as **read-only
   reference (no gate)**, because Pat never mentions updating it -> the explain-back
   should ask "the office reads your portfolio but doesn't update it — is that
   right, or should final decisions update it?"
4. "What it has learned" -> left as analyst body behavior; no explicit learning
   wiring.

If (2) and (3) come back as explain-back questions rather than silent choices,
that is the loop doing exactly what the scaffold leaves for it.
