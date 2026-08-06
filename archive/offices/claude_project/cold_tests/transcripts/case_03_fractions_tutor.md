# Cold test 03 — Fractions tutor (build)

**Setup.** Fresh subagent reads only `start_instructions.md` + the three gallery
files, then acts as the assistant.

**Pat's description.**
> "I want a tutoring helper for my kid who is learning fractions. It asks a question and
> waits for my kid to answer, checks whether the answer is right, and keeps track of how
> my kid is doing. Based on that it picks the next question — easier if they're
> struggling, harder if they're getting them right — and moves on to a new topic once
> they've got the current one down. When we stop it gives a short summary of how the
> session went. The questions and feedback show on a screen; my kid types the answers."

**Pre-registration (expected correct office).** A stateful `TUTOR` transform (holds
mastery/topic/difficulty and the current question) + an answers source + a screen sink
(+ a start trigger). No coordinator, no record, no gate; mastery is the tutor's private
memory; the ask-and-wait loop closes **through the external student** (screen → kid →
answers). Tests: restraint on an adaptive office; private state (not a record); the
ask-and-wait-through-the-world modeling; needs-to-see (a grader needs the question — best
kept inside one agent). Acceptable variance: a grader + planner split *if* the question
is routed to the grader.

**Verdict: PASS.** Single stateful `TUTOR` transform; no coordinator/record/gate;
mastery kept as the tutor's own memory; needs-to-see caught (tutor remembers the
question to grade); added a sensible `STOP` source and noted a stop can interrupt a
pending wait. Improved on the pre-registration.

---

## Full transcript

## Phase 1 — the network

**Agents**

- **START** — *source*. Outbox `out`. Sends a single "begin" signal when the session starts (the app opening, or a start button), to kick off the first question.
- **ANSWERS** — *source*. Outbox `out`. Streams the answers the kid types in — one per question.
- **STOP** — *source*. Outbox `out`. Sends a "stop" signal when you end the session.
- **TUTOR** — *transform*. Inbox `in`. Outbox `out`. Reads one message at a time — a begin, an answer, or a stop. Keeps its own memory of the current topic, the current question and its correct answer, and how the kid has been doing. On *begin* it sends the first question; on an *answer* it checks it, updates its sense of progress, and sends feedback plus the next question; on *stop* it sends a short session summary. Everything it sends goes to the screen.
- **SCREEN** — *sink*. Inbox `in`. Shows each question, each piece of feedback, and the final summary.

**Connections**

- (START, out, TUTOR, in)
- (ANSWERS, out, TUTOR, in)
- (STOP, out, TUTOR, in)
- (TUTOR, out, SCREEN, in)

What the shape shows: three inputs — begin, answers, and stop — **fan in** to `TUTOR`'s single inbox; the tutor reacts to whichever arrives, so a stop can reach it even while it's waiting for an answer. There is **no coordinator**: the kid types one answer per question, so asking-and-waiting happens naturally by turn-taking, and the tutor stays consistent because it takes one message at a time from its one inbox and processes each fully before the next. The tutor's progress memory is **its own** — nothing is shared or jointly written — so there is **no gate and no record**. One place shows everything, so a single outbox to a single sink. This is a short line of workers, which is the right amount of machinery here.

## Explain it back to Pat (plain English)

> Here's the office I've sketched, and it's just a first draft we'll fix together.
>
> One worker — the tutor — runs the whole session. When the session begins, it puts a first fraction question on the screen and then waits. Your kid reads it and types an answer, which goes straight to the tutor. The tutor checks whether the answer is right, keeps a running sense in its own memory of how your kid is doing, and puts a short bit of feedback on the screen — then it picks the next question: an easier one if your kid is struggling, a harder one if they're getting them right, and it moves on to a new topic once your kid has the current one down. It shows that next question and waits again. This back-and-forth just keeps going, one question at a time. Whenever you stop, the tutor puts a short summary of how the session went on the screen. The questions, the feedback, and the summary all appear on the one screen, and your kid's typed answers are the only thing coming back in.
>
> **Things I assumed —**
> - The session needs *something* to kick it off (so the first question appears): I assumed a simple "start" — the app opening or a start button. Tell me if you'd rather it work differently.
> - Your kid types one answer per question, so the tutor naturally asks, waits, checks, then asks again — no risk of answers piling up.
> - A "stop" can come at any time, even while the tutor is waiting for an answer, and it ends the session with a summary. I assumed "stop" is a deliberate signal from you (a button, or closing the app), not the kid typing the word "stop."
> - The tutor remembers the question it just asked and the right answer, so it can check what your kid types — it needs to hold onto that to grade fairly.
> - The tutor alone decides everything: whether an answer is right, how your kid is doing, when to make things easier or harder, and when to switch topics.
> - The feedback and the final summary appear on the same screen as the questions. Tell me if you'd also like the session saved to a file somewhere, rather than only shown on screen.

## Phase 2 — the agent descriptions

- **START** *(source)* — a single "begin" signal that starts a session — for example, the app opening or your kid pressing a start button. It fires once to prompt the first question.
- **ANSWERS** *(source)* — the keyboard input: whatever your kid types as an answer, sent as one message per question.
- **STOP** *(source)* — a "stop" signal you give when the session is over (a stop button or closing the app). It fires once to end the session.
- **TUTOR** *(transform)* — the tutor keeps in its own memory: the current topic, the current question and its correct answer, and a running picture of how the kid is doing (recent right/wrong, and progress within each topic).
  - On a **begin** message: choose a first question at an easy level in the first topic, remember it and its answer, and send it to the screen.
  - On an **answer** message: compare it with the remembered correct answer; update the progress memory; send short feedback (right or wrong, with a brief hint or explanation) to the screen; then pick the next question — easier if the kid has been struggling, harder if they've been getting them right, and switch to a new topic once the current one looks mastered — remember the new question and its answer, and send it to the screen.
  - On a **stop** message: write a short summary of how the session went (topics covered and how the kid did) and send it to the screen.
  (Whether the checking and question-picking are later done by simple rules or by a small language model is decided in a later step, not here.)
- **SCREEN** *(sink)* — the screen your kid looks at; it displays each question, each piece of feedback, and the closing summary.
