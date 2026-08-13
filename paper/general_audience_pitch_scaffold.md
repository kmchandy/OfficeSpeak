# [Working title — pick one before sending]

- *Give Claude a Toolbox, Not Just a Task*
- *Systems That Keep Running: OfficeSpeak + Cowork*
- *Claude Already Knows Distributed Systems. Now It Has a Toolbox For Them.*

*Scaffold only — status notes and TODOs are in brackets, delete before this
goes to any tester. Purpose of this document: a short, general-audience read
that a potential tester skims in a few minutes. If their application space
is in here, or close to it, they ask you for the detailed walkthrough. This
is a hook, not a manual — every section should be short enough that someone
who isn't interested can bail after one paragraph, and someone who is
interested can't stop reading.*

---

## 1. Opening — a few people, a few problems

*[Draft: 3-4 one- or two-sentence vignettes, each ending on the same shape
of want: "something that keeps running and reacting, not a one-time
answer." Pull from real examples already built, plus the new one:]*

- A member of an investment club wants something that watches the market
  and tells him when a strategy stops working — not once, every day.
- A facilities manager wants something that fuses HVAC and utility sensor
  readings into a heads-up before something breaks.
- A parent wants something that quizzes their kid on fractions today and
  multiplication next week, without hiring a tutor.
- A biologist wants something that keeps screening new compounds against
  the same criteria as the last thousand, without re-explaining the
  criteria every time. *[new — from today's conversation, confirm framing
  with her before publishing]*

*[Close section 1 with one line: what all four have in common — a system
that has to keep state, run continuously, and be trusted, not a script
that runs once.]*

## 2. The problem, plainly

*[Draft the core tension in plain language, no jargon:]*

Claude can write code. Ask it to build you a one-off script and it's
usually fine. Ask it to build something that runs continuously, keeps
track of what happened before, and coordinates several moving parts at
once — and the code is much easier to get subtly wrong, in ways that
don't show up until the system's been running for a while. This isn't a
knock on Claude — it's a hard problem that took the field decades to get
right even for people who do it for a living. Most people asking Claude
for this kind of system don't have that expertise, and neither, usually,
does the person prompting it — even a PhD in an unrelated field, even
someone who codes.

## 3. The idea — one mechanism, two starting points

*[This is the unified-pillars section — the main story. Draft:]*

OfficeSpeak is a small library — Python functions plus natural-language
instructions to the LLM, nothing more exotic than that — that gives
Claude a pre-built, pre-checked way to assemble these systems instead of
inventing the tricky parts from scratch each time. Paired with Cowork, using
it is just a conversation: you describe what you want, Claude builds it
using the library's pieces, explains back what it built and what it
guessed, and you correct it in English.

The same mechanism supports two things that used to feel like separate
efforts:

- **Building something new.** Describe an office — a team of Claude-run
  workers — and Claude assembles it from the library's coordination
  pieces (the parts that keep the system correct, not the parts that make
  it specific to you).
- **Extending something that already exists.** Someone already built and
  verified an office for your application space — backtesting, tutoring,
  monitoring. You don't rebuild it; you describe the one new piece that's
  actually different for you (a new trading rule, a new practice subject,
  a new sensor), and Cowork walks Claude through fitting it into what's
  already there, checking your addition against the same rules the
  original office had to satisfy.

These aren't two products. They're the same conversation, starting from
different points — day one versus day two thousand of an application
space's life.

## 4. Why this beats asking Claude cold, every time

*[Plain-language version of the reuse argument — no inequality, no
formalism. Draft:]*

Building a reusable library only pays off if three things are true, and
it's worth saying them plainly instead of assuming them: it has to get
reused a lot, not built for one person's one app; what it encapsulates has
to be the kind of logic that's genuinely risky to get right from
scratch every time, not just a lot of typing; and — the part people
skip — a new addition has to be checkable against the library's own rules,
not just "looks right to the model that wrote it." OfficeSpeak's checks
(same-inputs-same-outputs, no peeking at the future, does the number stay
in the range it's supposed to, does a hand-worked example come out right)
exist because of that third point, not the first two.

## 5. What this looks like today

*[Two working examples and one that isn't working yet — keep each to a
short paragraph. Ground every claim in what's actually built; don't
oversell any of these. The third entry is included because environmental
monitoring is an application space a reader may recognise as theirs, not
because it runs today; if that trade doesn't seem worth it, cut it.]*

**Backtesting trading strategies** *(mac_speed_suite)*. A working office
that pulls real stock price history, runs several strategies (moving
averages, breakout rules, and more) against it, and ranks them. Adding a
new strategy — someone's own idea for when to buy and sell — is a
Cowork-guided conversation: describe the rule, Claude writes the one
function that's actually new, and a checker verifies it doesn't peek at
future prices, gives finite numbers, stays in range, and matches a
hand-worked example (or a cheaper sanity check, tester's choice) before
it's wired in. Two outside testers with real trading/quant backgrounds
are trying this now.

**Environmental monitoring** *(the Salton Sea dashboard)* — **in progress;
not a working office yet.** The data side is real: a source that scrapes
NASA/JPL's two moored buoys on the sea for live wind speed and direction,
confirmed working and covered by an offline parser check, plus a synthetic
stand-in for hydrogen sulfide while the CARB site-id mapping is unresolved.
Sample dashboard output exists. What does not work is the office itself —
the wind source isn't registered with the framework, so `office.md` doesn't
compile, and the dashboards produced so far came from a standalone script
rather than from a running office. *[Include this only if you're willing to
say the above plainly. A reader who tries the example and finds it doesn't
run costs more than the section gains. There's also no packaged
"add-a-sensor" skill for it, which is the natural next step once the office
compiles.]*

**Practice tutoring** *(adaptive_tutor)*. A working office that quizzes a
student, adapts to what they get wrong, and now covers fractions,
multiplication facts, and telling time. Adding a subject — spelling,
vocabulary, another arithmetic skill — works the same way: describe how a
problem in that subject is generated and checked, and the same
Cowork-guided process verifies the new subject's ground truth before
wiring it in. One outside tester is trying this now.

## 6. Where this could go — drug discovery

*[New, unbuilt, exploratory — flagged clearly as such. Draft placeholder,
fill in after the follow-up conversation with the biologist:]*

A biologist raised a fourth application space today: screening candidate
compounds against a consistent set of criteria, over and over, as new
candidates and new evidence come in. *[Don't invent the specifics of what
a "new instance" would mean here — a new scoring rule for a target? a new
assay result feed? — until she's weighed in. Once that's clearer, this
section should follow the same shape as Section 5: what the shared office
does, what the one new piece per addition looks like, what a mechanical
check on that piece could be (the backtester's golden-example idea has an
analog here somewhere — a known binder/non-binder pair, maybe).]*

## 7. What you get, and how to go further

*[Closing section — the actual call to action. Draft:]*

If any of this is close to something you'd want — a system that keeps
running in your domain, or a new piece added to one that already exists —
say so, and the next step is a walkthrough specific to your case: what
the office would look like, what the one new piece would be, and what
"correct" means for it. That's a different, longer document from this
one, and it only gets written for domains where someone's actually asked.

---

## [Notes to self — resolve before sending to anyone]

- Title: pick one of the three above, or something else entirely.
- Decide whether to name real testers (the tester, the trader, Sachin) by name/role
  or keep them anonymous ("two testers with trading backgrounds," etc.) —
  hasn't been asked of them for this specific use.
- Target length once drafted: this reads fast only if each section stays
  to what's above — resist the urge to add the Lamport-clock/checkpoint
  material from draft_v3; that's tutorial-depth content, not hook-depth.
  Section 4 is the only place any "why" argument belongs at all.
- Section 6 needs the follow-up conversation before it's more than a
  placeholder — don't guess at her domain's specifics.
- Decide where this document should live once finished: `paper/` (grouped
  with draft_v3 as "paper-adjacent") or `guides/` (grouped with
  tester-facing material, which is arguably what this actually is). Filed
  under `paper/` for now since it's a sibling effort to the CHI draft, but
  flag if you want it moved.
