# Course media strategy — teaching distributed systems in the age of AI

*How to deliver teaching material that reaches a large, attendance-optional class
(40–100) and anyone in the world interested in distributed systems. Working note;
opinions, not orders.*

## Don't pick one medium — pick a spine plus layers

The choice is mostly decided by four facts about this course, not by taste:

1. **Two audiences at once** — enrolled students *and* the open world. Favors
   web-native, linkable, no-login formats: one URL serves both.
2. **Attendance optional / asynchronous** — material must stand alone without a
   live lecturer. Self-paced.
3. **The subject is doing** — students build and run real distributed systems.
   Every concept should sit one click from *running something*, not from "install
   this first."
4. **The field moves monthly** ("in the age of AI") — favor media that are cheap
   to revise. Video is not; text and notebooks are.

Those four push toward: web-native and updatable, connected to hands-on doing,
and low-setup (setup friction is the biggest dropout cause in a large async class
— the single-tester friction, times a hundred).

## Verdict on each medium

- **Text** — the strongest *spine*. Searchable, linkable, accessible,
  translatable, outlives any platform, cheapest to keep current, and it already
  lives in the git repos so it can stay in lockstep with the code. A public course
  **website generated from Markdown in the repo** reaches the class and the world
  from the same URL.
- **Micro-courses (the HTML walkthroughs)** — keep them; a real asset. The *visual
  on-ramp* for intuition ("here's the shape of an office / a snapshot /
  termination"), browser-native, no install, self-narrating. Good for orientation,
  not for depth or for running code.
- **Google Colab notebooks** — the right *hands-on layer for framework mechanics*:
  notebooks without the local-setup tax, run in the browser, free, shareable by
  link. Where a student watches checkpoint-recovery happen, inspects a consistent
  snapshot, or runs the backtester — the deterministic, no-LLM parts, which are
  exactly the distributed-systems concepts. (Caveat: LLM-calling offices need an
  API key in Colab; Ollama isn't practical there. Colab shines for the no-model
  mechanics; the conversational parts happen in Cowork.)
- **Local Jupyter** — same pedagogy as Colab with the setup burden back on. For a
  large class, skip it in favor of Colab.
- **Video** — use *sparingly and surgically*: a few short screencasts where
  *seeing the interaction* is the point (an office built by talking to Cowork; a
  checkpoint restoring). Never the backbone — most expensive to produce, hardest
  to keep current, least skimmable, worst for code.
- **Plain slides** — weakest standalone (slides without a speaker lose their
  meaning). The micro-courses are already "slides done right." Don't invest here.
- **Claude education material / a Claude Project** — the *scaling move for
  support*, and dead-on-theme. A Claude Project preloaded with the course text and
  framework docs becomes an always-available TA that explains a checkpoint, helps
  debug an office, or answers "why did termination fire?" — scaling office hours to
  100 students without 100 hours. A supplement/tutor layer, not the primary
  content.

## The recommended stack

1. **Spine: a public, static course website generated from the repo** (text) — the
   canonical, updatable, searchable reference; same URL for the class and the
   world.
2. **On-ramp: the micro-courses** — for the intuition beats.
3. **Do-it layer, one click from each concept:** Colab notebooks for framework
   mechanics; Cowork prompts for the conversational build/tune/inspect parts.
4. **TA layer: a Claude Project** as the always-on tutor.
5. **Video: a handful of short "watch this" clips** — no more.

## Two principles that hold it together

**Single source of truth.** Keep the material in the repos and *generate* the
website and micro-courses from it, so the course, the docs, and the code cannot
drift — the same discipline that makes the software trustworthy.

**The course is also the attention strategy.** A polished, public, hands-on course
on building distributed systems in the age of AI is itself one of the most
persuasive artifacts the project can produce: it travels, it demonstrates the
thesis at the scale of a whole class, and it is exactly what an education
partnership is for. The teaching medium doubles as the way the work gets noticed.

## Next step (when ready): map assets to layers

Sketch which existing pieces become which layer, so the course has a skeleton to
pour lectures into:

- **Website chapters (text):** the concepts — message-passing offices, consistent
  snapshots and checkpoint/recovery, termination detection, exactly-once,
  no-look-ahead / as-of correctness, composition, the thread→process transition.
- **Micro-courses:** the orientation beats — what an office is, what a snapshot is,
  the gallery tour.
- **Colab notebooks:** run an office; watch recovery; inspect a checkpoint; run the
  backtester; (capstone) the paper-trading execution app and its supervisor.
- **Cowork:** talk to the backtester; build/tune a strategy in English; ask the
  Claude-Project TA to explain a run.
- **Video:** one clip of an office being built by talking; one of a checkpoint
  restoring.

The paper-trading execution app is the natural capstone — a real distributed
system where checkpointing, idempotency, and (eventually) the thread→process
migration are load-bearing rather than decorative.
