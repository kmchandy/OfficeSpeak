# Cold test 04 — Adaptive fractions tutor (build; realistic app)

**Setup.** Fresh subagent reads only `start_instructions_v3.md` (with the new
three-part explain-back) + the three gallery files, then acts as the assistant. This is
the realistic-tutor description prepared for a tester interested in tutoring.

**Pat's description.**
> "I want an adaptive practice tutor for a kid learning fractions. It works from a bank
> of practice questions, each tagged with which skill it drills and how hard it is. When
> a session starts it picks up where the kid left off. It asks one question at a time on
> the screen and waits for an answer; if the answer is wrong it gives a gentle hint and
> lets them try again, and after a couple of tries it shows the worked solution. It keeps
> track of how well the kid knows each skill, and chooses the next question adaptively —
> easier if they're struggling, harder as they improve — and it also mixes in review of
> skills they learned a while ago or got wrong before so they don't forget them. It only
> moves on to a new skill once the kid has mastered the current one and its prerequisites.
> When the session ends it shows the kid a short encouraging summary and saves a progress
> report the parent can read later."

**Pre-registration.** Sources `START`/`ANSWERS`/`STOP`; sinks `SCREEN`, `REPORT`;
records `ITEMS` (question bank, read-only) and `PROFILE` (mastery + schedule, read+written
by the tutor, single accessor); a `TUTOR` transform. **No coordinator.** Subtle call:
`PROFILE` is read-and-written but by a *single* worker → **no gate** (the trap is a gate
on PROFILE). Also tests: records vs private state, needs-to-see, and the **new three-part
explain-back**. Acceptable variance: grader + planner split *if* the item flows to the
grader.

**Verdict: PASS — strongest run.** Split into `PLANNER` + `QUIZMASTER` (the acceptable
variance) with `BANK` + `PROGRESS` records; avoided the gate-on-single-writer trap with
explicit accessor-count reasoning; used records appropriately; produced the three-part
explain-back faithfully; and surfaced a genuinely insightful needs-to-see (coach sees
pass/fail, not the actual wrong answer). No coordinator.

---

## Full transcript

# Phase 1 — the network

## Agents

- **SESSION** — *source*. Outbox `out`. Emits a "start" signal when the kid begins and an "end" signal when the kid finishes.
- **KID** — *source*. Outbox `out`. Streams the kid's typed answers as they come in from the screen.
- **BANK** — registered **record** (holds: the practice-question bank, each question tagged with its skill and difficulty and carrying its correct answer, a hint, and a worked solution). Inbox `req`, outbox `reply`. Returns a question matching the skill and difficulty asked for.
- **PROGRESS** — registered **record** (holds: how well the kid knows each skill, and where the kid left off). Inbox `req`, outbox `reply`. Read and updated by the planner.
- **PLANNER** — *transform*. Inbox `in`. Outboxes `to_bank`, `to_progress`, `question`, `screen`, `report`. The adaptive brain: reads the start/end signals, the question outcomes, and the record replies; tracks each skill's mastery; chooses the next skill and difficulty (easier when struggling, harder as the kid improves, mixing in review of old or previously-wrong skills, and only advancing to a new skill once the current one and its prerequisites are mastered); asks the bank for a matching question; and at session end writes the encouraging summary to the screen and the parent report to the report file.
- **QUIZMASTER** — *transform*. Inbox `in`. Outboxes `screen`, `result`. Runs one question at a time: puts the question on the screen and waits; checks each answer; on a wrong answer gives a gentle hint and lets the kid try again; after a couple of tries shows the worked solution; then reports the outcome (which skill, right or wrong, how many tries) to the planner.
- **SCREEN** — *sink*. Inbox `in`. Shows the kid each question, hint, worked solution, and the closing summary.
- **REPORT** — *sink*. Inbox `in`. Saves the progress report the parent can read later.

## Connections

- (SESSION, out, PLANNER, in)
- (KID, out, QUIZMASTER, in)
- (PLANNER, to_bank, BANK, req)
- (BANK, reply, PLANNER, in)
- (PLANNER, to_progress, PROGRESS, req)
- (PROGRESS, reply, PLANNER, in)
- (PLANNER, question, QUIZMASTER, in)
- (QUIZMASTER, screen, SCREEN, in)
- (QUIZMASTER, result, PLANNER, in)
- (PLANNER, screen, SCREEN, in)
- (PLANNER, report, REPORT, in)

What the shape shows: there is **one kid** and **one decider**, so there is **no coordinator**. The planner's single inbox is a **fan-in** — the start/end signals, the bank's question, the progress record's reply, and each question's outcome all arrive there, and the planner tells them apart by what it is currently doing. The quizmaster's single inbox is likewise a fan-in of the next question and the kid's answers. Both records are asked-and-waited-on the ordinary way (send a request, read the reply on the inbox), the same pattern the gallery reuses without new machinery. **PROGRESS** is touched by only the planner, so its own single inbox keeps it consistent — **no gate**. Both `SCREEN` writers (quizmaster and planner) **fan in** to the one screen.

---

# Explaining it back to you, Pat

Here's the tutor as a small team of workers. Remember this first version is just a starting point — we'll fix whatever doesn't match what you had in mind.

**Meet the team**

- A **sign-in worker** notices when your kid sits down to practice and when they're done.
- A **coach worker** is the brain. It remembers how well your kid knows each skill, decides what to practice next — easier when they're struggling, harder as they improve, and slipping in a bit of review of older or shaky skills so they don't fade — and only moves on to a new skill once the current one and the skills it builds on are solid.
- A **quizmaster worker** runs the actual practice: it shows one question, waits, checks the answer, offers a gentle hint and another try if it's wrong, and shows the full worked solution after a couple of misses.
- A **question shelf** holds all the practice questions, each labeled with its skill, its difficulty, and its own answer, hint, and worked solution.
- A **progress keeper** remembers, between visits, how your kid is doing and where they left off.
- A **screen** shows your kid everything — questions, hints, solutions, and the cheerful wrap-up.
- A **report file** quietly saves a progress note for you to read later.

**The org chart**

- The sign-in worker tells the coach when practice starts and ends.
- The coach looks up where your kid left off from the progress keeper, picks a skill and difficulty, and pulls a matching question off the question shelf.
- The coach hands that question to the quizmaster.
- The quizmaster shows it on the screen, reads your kid's typed answers, and handles hints, retries, and the worked solution.
- When a question is finished, the quizmaster tells the coach how it went; the coach updates the progress keeper and picks the next question.
- When practice ends, the coach puts an encouraging summary on the screen for your kid and saves a report for you.

**The story of one question**

Your kid sits down and the sign-in worker says "start." The coach looks up where they left off, sees they've been shaky on comparing fractions, and decides to try an easier one there. It asks the question shelf for an easy "comparing fractions" question and hands it to the quizmaster. The quizmaster puts it on the screen and waits. Your kid types an answer; it's wrong, so the quizmaster shows a gentle hint and lets them try again. Still not quite — so after that second try the quizmaster shows the worked solution, then tells the coach "comparing fractions, missed, two tries." The coach nudges that skill's mastery down a little, saves it to the progress keeper, and — since they're struggling — picks another gentle question on the same skill, and around it goes. Later, your kid clicks done; the sign-in worker says "end," and the coach shows a warm "nice work today" summary on the screen and saves your progress report.

**Things I assumed —**

- **The quizmaster genuinely waits** for this kid's answer before doing anything else (one kid, one question at a time). Tell me if you'd rather it behave differently.
- **Each question on the shelf carries its own correct answer, a hint, and a worked solution**, plus its skill and difficulty labels — so the quizmaster has everything it needs to check answers, hint, and show the solution.
- **"A couple of tries"** means the kid gets a hint-and-retry, and the worked solution appears after the second miss. Say the word if it should be more or fewer tries.
- **The coach only needs the outcome** of each question — which skill, right or wrong, and how many tries — to track mastery; it does **not** see the exact wrong answers. If you'd like the coach to look at *what* the kid actually typed (say, to spot a specific misconception), that's one more thing to hand it — tell me and I'll add it.
- **The list of which skills are prerequisites for which** is known and lives with the question shelf/skill map, so the coach can decide when to advance.
- **Where the kid left off and their per-skill mastery are saved in one place** and survive between visits, which is how a new session picks up where the last one ended.
- **The coach decides the skill and difficulty; the shelf just supplies a matching question.**
- **The kid sees only the encouraging summary on the screen; the fuller progress report is saved to a file for you** — the two are separate on purpose.
- **One kid at a time.**

---

# Phase 2 — the agent descriptions

*(BANK and PROGRESS are registered records, so they aren't described — BANK holds the tagged question bank, PROGRESS holds per-skill mastery and where the kid left off.)*

- **SESSION** *(source)* — the app's start/stop signal: emits "start" when the kid opens the tutor and "end" when the kid finishes (for example, closes it or presses a "done" button).
- **KID** *(source)* — the kid's typed answers as they are entered on the screen during practice.
- **PLANNER** *(transform)* — reads four kinds of message on its one inbox and keeps its own working picture of the session:
  - On **"start"**: ask the progress keeper for this kid's saved mastery and where they left off; using that, choose the next skill and difficulty; ask the bank for a matching question; hand it to the quizmaster.
  - On a **question outcome** from the quizmaster (which skill, right/wrong, number of tries): update that skill's mastery; save the update to the progress keeper; then choose the next question adaptively — lower the difficulty when the kid is struggling and raise it as they improve; periodically mix in a review question on a skill learned a while ago or previously missed so it isn't forgotten; and advance to a new skill only once the current skill and its prerequisites are mastered. Ask the bank for the chosen question and hand it to the quizmaster.
  - On a **bank reply** (a question) or a **progress reply**: use it to continue whichever of the above it was waiting for.
  - On **"end"**: compose a short, encouraging summary of the session and send it to the screen for the kid, and write a fuller progress report to the report file for the parent.
- **QUIZMASTER** *(transform)* — reads two kinds of message on its one inbox and keeps track of the current question and how many tries have been used:
  - On a **question** from the planner: show it on the screen and wait for the kid's answer.
  - On the **kid's answer**: check it against the question's correct answer. If right, tell the planner the outcome (skill, correct, tries used). If wrong and tries remain, show the question's gentle hint on the screen and wait for another answer. If wrong and the tries are used up, show the question's worked solution on the screen, then tell the planner the outcome (skill, missed, tries used).
- **SCREEN** *(sink)* — the kid's screen; displays each question, hint, worked solution, and the closing summary.
- **REPORT** *(sink)* — the file where the parent-facing progress report is saved at the end of each session.
