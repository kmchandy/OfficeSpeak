# Cold test 05 — Adaptive tutor, re-run after the two-pass message-shape edit (regression)

**Purpose.** Regression check on the Phase-1 edit that added the two-pass port-message
procedure (Pass A: name every outbox's message; Pass B: derive every inbox from the
connected outboxes). Same Pat description as case 04. Question: does the module still
produce a clean, Pat-clear office, *and* does it now itemize per-outbox messages and
derive inboxes (the gap in case 04's PLANNER)?

**Verdict: PASS.** Pass A itemized every outbox with component parts; Pass B derived
every inbox and named the fan-in kinds with their sources; the Pat-facing explanation
stayed in plain worker language (three parts) without leaking the schemas. Still no
coordinator; no gate on the single-writer PROGRESS record. Cleaner decomposition than
case 04 (CHECKER / PLANNER / REPORTER). Confirms the edit works and does not clutter the
module — start module is ready for the pilot.

---

## Full transcript

# Phase 1 — the network

## Agents

- **SESSION** — *source*. Outbox `out`. Signals the start of a practice session and, later, its end.
- **ANSWERS** — *source*. Outbox `out`. Streams the kid's typed answers, one at a time.
- **CHECKER** — *transform*. Inbox `in`. Outboxes `feedback`, `result`. Holds the current question; grades each answer; gives a hint and lets the kid retry, and after a couple of tries shows the worked solution; when the question is resolved, reports the outcome.
- **PLANNER** — *transform*. Inbox `in`. Outboxes `to_screen`, `to_checker`, `to_bank`, `to_progress`, `to_reporter`. Picks up where the kid left off; updates how well the kid knows each skill; chooses the next question adaptively (easier when struggling, harder as they improve, with review mixed in) and respects prerequisites before advancing a skill; at session end, hands the final picture to the reporter.
- **REPORTER** — *transform*. Inbox `in`. Outboxes `to_screen`, `to_file`. Builds the short encouraging summary for the kid and the progress report for the parent.
- **BANK** — registered **record** (holds: the tagged question bank and the skill/prerequisite map). Inbox `req`. Outbox `reply`. Read by the planner.
- **PROGRESS** — registered **record** (holds: per-skill mastery, past errors, when each skill was last practiced, and where the kid left off). Inbox `req`. Outbox `reply`. Read and written by the planner only.
- **SCREEN** — *sink*. Inbox `in`. Shows questions, hints, worked solutions, "correct!" feedback, and the closing summary to the kid.
- **PARENT_REPORT** — *sink*. Inbox `in`. Saves the progress report for the parent to read later.

## Connections (4-tuples: sender, outbox, receiver, inbox)

- (SESSION, out, PLANNER, in)
- (ANSWERS, out, CHECKER, in)
- (PLANNER, to_checker, CHECKER, in)
- (CHECKER, feedback, SCREEN, in)
- (CHECKER, result, PLANNER, in)
- (PLANNER, to_screen, SCREEN, in)
- (PLANNER, to_bank, BANK, req)
- (BANK, reply, PLANNER, in)
- (PLANNER, to_progress, PROGRESS, req)
- (PROGRESS, reply, PLANNER, in)
- (PLANNER, to_reporter, REPORTER, in)
- (REPORTER, to_screen, SCREEN, in)
- (REPORTER, to_file, PARENT_REPORT, in)

## The message on every port

### Pass A — every outbox

- **SESSION.out** — a session signal: either "start" (begin the session for this kid) or "end" (the session is over).
- **ANSWERS.out** — the kid's typed answer to the question currently on screen (a number or expression).
- **CHECKER.feedback** — one of three: a gentle hint (answer wrong, tries remain), a worked solution (out of tries), or a short "correct!" congratulation.
- **CHECKER.result** — a resolved outcome for the current question: `{skill, question id, difficulty, outcome = correct or needed-solution, number of tries and hints used}`.
- **PLANNER.to_screen** — the next question to display (the question text the kid reads).
- **PLANNER.to_checker** — the current question's grading key: `{skill, question id, difficulty, correct answer, worked solution, how many tries before the solution is shown}`.
- **PLANNER.to_bank** — a request for a question: `{skill, difficulty, questions to avoid because recently seen}`.
- **PLANNER.to_progress** — either a read request ("give me this kid's mastery, error history, last-practiced times, and place") or an update ("record this outcome / new mastery level / new place").
- **PLANNER.to_reporter** — the end-of-session snapshot: mastery per skill, which skills were practiced, and progress made this session.
- **BANK.reply** *(registered record)* — a question matching the request: text, correct answer, worked solution, skill, difficulty (drawn from the bank; the skill/prerequisite map is also served on request).
- **PROGRESS.reply** *(registered record)* — the mastery/history/place data asked for (and an acknowledgement for an update).
- **REPORTER.to_screen** — the short encouraging summary shown to the kid at the end.
- **REPORTER.to_file** — the progress report written for the parent.

### Pass B — every inbox (read off the outboxes connected to it)

- **PLANNER.in** — a fan-in of four kinds, interleaved: "start"/"end" signals (from SESSION.out), resolved outcomes (from CHECKER.result), a chosen question (from BANK.reply), and mastery/history/place data or acks (from PROGRESS.reply). The planner tells them apart by kind and by which request it is awaiting.
- **CHECKER.in** — a fan-in of two kinds: the kid's answer (from ANSWERS.out) and the current question's grading key (from PLANNER.to_checker). The checker holds the latest grading key in memory and grades each incoming answer against it.
- **BANK.req** — question requests (from PLANNER.to_bank).
- **PROGRESS.req** — read requests and updates (from PLANNER.to_progress).
- **REPORTER.in** — the end-of-session snapshot (from PLANNER.to_reporter).
- **SCREEN.in** — a fan-in of three kinds: hints / worked solutions / "correct!" (from CHECKER.feedback), the next question (from PLANNER.to_screen), and the closing summary (from REPORTER.to_screen).
- **PARENT_REPORT.in** — the progress report (from REPORTER.to_file).

What the shape shows: there are **no coordinators**. The flow is a single sequential loop driven by one kid answering one question at a time, so nothing runs in parallel that would need synchronizing. The planner is the **only** worker that touches the progress record, so the record's own one-request-at-a-time handling keeps it consistent — no gate is needed. The planner asks the two records and waits for their replies on its own inbox (ask-and-wait), and because the kid cannot answer until a fresh question is on screen, no new answer arrives while the planner is mid-selection.

---

# Explaining it back to Pat

Here's the tutor as a small team of workers. Remember this is a first sketch — we'll fix whatever doesn't match what you pictured.

**Meet the team**

- A **session worker** that says when practice begins and when it's over.
- An **answer worker** that carries whatever the kid types.
- A **checker** that looks at each answer, decides if it's right, offers a gentle hint and a second try, and shows the full worked-out solution after a couple of misses.
- A **planner** — the heart of the tutor. It remembers how well the kid knows each skill, picks up where they left off, and chooses each next question: easier when they're struggling, harder as they get stronger, with older or previously-missed skills mixed back in so they aren't forgotten. It only lets the kid move on to a new skill once the current one and everything it builds on are solid.
- A **reporter** that, at the end, writes the kid a short cheerful summary and saves a report the parent can read later.
- A **question shelf** that holds all the practice questions, each labelled with its skill and difficulty, plus the map of which skills come before which.
- A **progress book** that holds, for this kid, how well they know each skill, what they've gotten wrong, when they last practiced each thing, and where they stopped.
- A **screen** where everything the kid sees appears, and a **report file** where the parent's report is saved.

**The org chart**

The session worker tells the planner "we're starting." The planner looks in the progress book to see where the kid left off, pulls a suitable question off the question shelf, shows it on the screen, and quietly tells the checker what the right answer and worked solution are. The kid's answers go to the checker. The checker either cheers, hints and waits for another try, or shows the solution — all on the screen — and, once a question is finished, tells the planner how it went. The planner updates the progress book and picks the next question. When the session worker says "we're done," the planner hands the final picture to the reporter, who puts a kind summary on the screen and saves the parent's report.

**The story of one question**

The planner chooses a fractions question at the right level and shows it on the screen; at the same time it privately tells the checker the correct answer and the worked solution. The kid types an answer, which reaches the checker. Say it's wrong — the checker puts a gentle hint on the screen and waits. The kid tries again and is still off, so after this second miss the checker shows the full worked solution on the screen and tells the planner "this one needed the solution." The planner marks that skill as needing more work in the progress book, decides the kid isn't ready to advance, and — mixing in a little review — picks a slightly easier question on a related skill, shows it, and the loop continues. When the kid stops for the day, the planner gathers the final results and hands them to the reporter, who tells the kid something encouraging on the screen and saves a report the parent can open later.

**Things I assumed —**

- The **planner** is the worker that needs to see the most, so I gave it three things: the kid's mastery and history (from the progress book), the actual questions (from the question shelf), and the **map of which skills are prerequisites for which** — I assumed that map lives with the questions. If that prerequisite map lives somewhere else, tell me and I'll connect it.
- The **checker** grades against the correct answer and worked solution I have the planner hand it — the checker itself never looks in the question shelf or the progress book.
- "**A couple of tries**" means a small fixed number of attempts (say two) before the worked solution appears; you can set the exact number.
- Only the planner reads and writes the progress book, and the whole tutor handles **one question at a time for one kid**, so the book never gets muddled and I did not add any extra "traffic cop" machinery. If you ever want several kids practicing at once through the same tutor, tell me — that would change this.
- The **end of a session** is a signal (the kid clicking "done," or time running out); I modelled it as coming from the session worker.
- The kid's **answers and the "start/finish" signals** are two separate incoming streams even though they both come from the kid at the keyboard.
- The parent's report is **saved to a file** for later, not emailed or shown live.

---

# Phase 2 — the agent descriptions

(Proceeding as if you approved the network. BANK and PROGRESS are registered record workers, so they aren't described — BANK holds the tagged question bank and the skill/prerequisite map; PROGRESS holds this kid's per-skill mastery, error history, last-practiced times, and place.)

- **SESSION** *(source)* — the session lifecycle for one kid: emits "start" when practice begins and "end" when it finishes (the kid clicks done, or a time/length limit is reached).
- **ANSWERS** *(source)* — the kid's input at the screen: emits each typed answer to the question currently displayed.
- **CHECKER** *(transform)* — reads either a grading key from the planner or an answer from the kid. On a grading key: store it as the current question (correct answer, worked solution, skill, difficulty, tries-allowed) and reset the try count. On an answer: compare it with the stored correct answer. If correct: put a short "correct!" on the screen and send the planner a result marked correct, with how many tries and hints were used. If wrong and tries remain: put a gentle, skill-appropriate hint on the screen, count the try, and wait for another answer (do not notify the planner — the kid retries the same question). If wrong and the tries-allowed is reached: put the worked solution on the screen and send the planner a result marked "needed solution," with the tries and hints used.
- **PLANNER** *(transform)* — reads one message at a time from its inbox and acts by kind. On "start": ask the progress book for this kid's mastery, error history, last-practiced times, and place; when it replies, choose the first question (resuming where the kid left off), ask the question shelf for a matching question, and when that arrives, show the question text on the screen and send the checker its grading key. On a result from the checker: update the progress book for that skill (raise or lower mastery, note an error, mark it just-practiced); then decide the next question (easier if struggling, harder as they improve, periodic review, advance a skill only once it and its prerequisites are mastered); ask the shelf, then show it and hand the checker its grading key. On "end": read the final mastery picture from the progress book and send the reporter a snapshot. (It keeps a small note of which request it is awaiting.)
- **REPORTER** *(transform)* — reads the end-of-session snapshot from the planner. Writes a short warm encouraging summary for the kid and shows it on the screen; writes a fuller progress report for the parent and saves it to the report file.
- **SCREEN** *(sink)* — the kid's screen; displays the current question, hints, worked solutions, "correct!" notes, and the closing summary.
- **PARENT_REPORT** *(sink)* — the file where each session's parent-facing progress report is saved for later reading.
