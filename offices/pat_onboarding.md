# Helping Pat get started — HCI design for the first office

The scaffold (`pat_scaffold.md`) says *what* to collect. This says *how* to collect
it from a non-programmer facing a blank page. The goal is not a perfect first
draft — it is a first draft good enough to produce an office Pat can react to,
because for non-programmers **reacting is far easier than creating**.

## The problem, framed with Norman's two gulfs

- **Gulf of execution** (Pat -> office): "I know what I want; how do I say it?"
- **Gulf of evaluation** (office -> Pat): "Did it do what I meant?"

Our two-part design maps cleanly onto the two gulfs: the scaffold + this
onboarding bridge *execution*; the explain-back + diagram bridge *evaluation*.
(Issue (2) — giving Claude the whole conversation when it explains — deepens the
evaluation bridge; postponed.) This document is the execution side, for the
**first** office.

### Why the execution gulf is wide for non-programmers
1. **Blank-page paralysis.** "Build an office of agents" offers no entry point.
2. **Missing target abstraction.** Pat has no mental model of agents / messages /
   state — so she can't organize her thoughts around them. But she *does* know her
   domain, and she *does* know how a human workplace works.
3. **Tacit-knowledge omission (expert blind spot).** Pat knows her domain so well
   she leaves out the obvious — e.g., that the accountant needs cost basis. This is
   the class that produced the Herb/accountant gap.
4. **Fear of getting it wrong.** A form reads like a test; novices freeze.
5. **Not knowing what's possible.** Pat can't imagine features she's never seen, so
   she can't scope the office.

## Design principles (each with the HCI basis it rests on)

1. **Recognition over recall** (Nielsen). Start from examples Pat edits, not a
   blank she fills. Editing an office beats inventing one.
2. **Concrete before abstract** (worked-examples effect; scenario-based design,
   Carroll). Get to a concrete strawman fast; let Pat critique it.
3. **Lean on the office/team metaphor** (interface metaphor; conceptual models,
   Norman). Pat describes *people with jobs*, never "agents." Every adult can
   staff a small team.
4. **Progressive disclosure / one question at a time** (Nielsen, Tidwell). An
   interview, not a nine-field form. Claude asks the next question, so Pat never
   faces the whole thing at once.
5. **Story-first elicitation** (use cases; contextual inquiry). Ask Pat to walk one
   item from arrival to output. Narrative is how humans think, it forces the flow
   without the word "edge," and a story that can't continue reveals a gap.
6. **Situated probes for tacit needs** (the "newcomer/Martian" elicitation trick).
   Concrete, first-day questions surface what Pat takes for granted.
7. **Safe to be wrong.** State up front that the first sketch is a
   conversation-starter and the office will be shown back and fixed together. Lowers
   the stakes that cause freezing.
8. **Propose, then let Pat dispose.** The strongest move: after minimal input,
   Claude offers a strawman office and asks "what's wrong with it?" — converting
   Pat's job from generation to recognition.

## The onboarding flow (recommended interaction)

Delivered as a guided conversation. Claude drives; Pat answers in plain words.

- **0. Frame + reassure.** "Let's set up a small team of helpers to do this for
  you. Start simple — we can grow it later, and I'll show you what I build so we
  can fix it together." (metaphor + safe-to-be-wrong + composition-later)
- **1. Show, to calibrate.** Offer 2-3 tiny complete example offices in plain words
  (a support desk; an investment club; a flu watch). "Pick the closest to remix, or
  start fresh." (recognition; scope calibration)
- **2. Goal in one breath.** "What should this team keep an eye on, and what should
  it decide or produce?"
- **3. Roster.** "Who's on the team, and what's each person's one-line job?" Offer a
  small **role palette** to recognize from: someone who *watches* inputs, an
  *analyst* who forms a view, a *decider*, a *checker*, a *record-keeper*.
- **4. Story walkthrough.** "Walk me through what happens when one piece of
  information comes in — who does what, and who hands what to whom?" (flow, in
  narrative)
- **5. Needs probe (the omission-catcher).** For each helper: "What does this person
  need in front of them to do the job?" For anyone who *computes or decides*, run
  the **newcomer test**: "Imagine a brand-new accountant on day one who knows
  nothing about your club — what would they need shown to them to work out the tax
  on a trade?" (surfaces cost basis and its kin)
- **6. Files & rules.** "What does the team keep on file?" and "Anything that must
  be handled one at a time, or where someone waits for someone else, or where the
  team should learn from what actually happened?"
- **7. Strawman + explain-back + iterate.** Claude builds a first office, shows it
  as a plain-English team description **and a simple diagram**, and asks "what's
  wrong with this?" Then loop.

**Shortcut:** Claude may jump to step 7 as soon as it has a goal and a rough roster
— a deliberately rough strawman gets Pat reacting sooner, which is the fastest path
for a non-programmer. Steps 4-6 can then be recovered *through* Pat's reactions.

## Tacit-knowledge probes (keep these in Claude's back pocket)

- **Newcomer/first-day test** — defamiliarize a role to expose assumed knowledge.
- **"What would they look at?"** — for any role that computes or decides.
- **"Where does that come from?"** — trace each computed output back to a source;
  a dead end is a missing input (this is the accountant-cost-basis catcher).

## Three entry modes (match Pat's readiness — let her self-select at step 1)

- **Remix an example** — total novice; edit the closest gallery office.
- **Guided interview** — has a goal, no structure; Claude runs steps 2-7.
- **Free write, Claude structures** — confident Pat writes a paragraph; Claude maps
  it to the scaffold and asks only about gaps (this is how v2/v3 were produced).

## Relation to the scaffold

Onboarding is the **delivery layer**; the scaffold fields are the interview's
backbone. Same information, but Pat never sees a form — and the questions teach the
office model implicitly. v3 is evidence this works: an engaged Pat already produced
the batched single source, the periodic rounds, feedback-as-input, and a clean
office boundary without being taught any systems vocabulary.

## Open questions for us

- The example gallery: which few domains, and how small should each example be?
- How rough should the first strawman be, and how early to offer it? (lean: as soon
  as goal + roster exist.)
- Role palette: a fixed small vocabulary Pat recognizes, vs fully freeform names?
  (lean: offer the palette as suggestions, accept any names.)
- Voice/tone for a nervous first-timer vs an impatient confident one.
