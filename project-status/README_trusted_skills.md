<!-- DRAFT — the new front door for the single repo.
     Opening reworked around the questions a newcomer actually asks
     (Vikram, 2026-08): how is it different from the agent alone? what's it for?
     can I change the structure? §1–§5 finalized 2026-08-16.
     §6–§10 drafted 2026-08-16; one bracket remains, the Get started install path.
     Note: this page describes the target skills/ + workshop/ structure from the
     restructure plan. Phase 0 is framing only — no files have been moved yet, so
     the paths named in italics are targets, not current locations. -->

# Trusted Skills

> **Build persistent, concurrent applications in a conversation with an AI agent coupled with tested libraries.**

A standard app, such as Gmail, has its features wired in: it has been carefully designed and extensively tested, with documentation and videos showing how to use it. You tailor the app to your needs by picking among the options its designers chose. By contrast, when you ask a general AI agent such as Claude to generate an app, you have total flexibility. But you are responsible for testing the result and making sure that the generated app is the one you actually wanted. 

A **trusted skill**, shortened to **skill** is a middle way. A trusted skill is an AI agent working with a tested library of functions and instructions for the agent. A trusted skill for an application space is designed to offer the flexibility that users want in that space. And it is designed to offer a safe, well-tested framework for that space. 

For example, a skill for building distributed systems has a library of concurrency primitives. A skill for building a distributed stock-trading application has, in addition, a library with primitives such as a transaction ledger. You describe an application in English, and the AI agent assembles your application with the aid of those libraries instead of the AI agent generating the entire app from scratch each time.

Skills are especially helpful when you are building concurrent apps. Concurrent systems are nondeterministic — the same program can behave differently from run to run — and their state spans many processes and message queues. Operations that are trivial for sequential programs, such as checkpointing and termination detection, are tricky for concurrent systems. So libraries for concurrency skills include code that implements these operations. 

Skills are designed to give users in an application space the flexibility they want in that space. Each user of a stock trading app is unlikely to want to implement her own checkpointing algorithm; however, she is likely to want the flexibility of creating her own stock-trading strategy.

The library also ships system-wide tests grounded in the system's structure and the application domain. When a user has the agent generate a new component, those tests run to confirm the system's properties still hold — for example, a newly generated trading strategy that makes each day's decision using future prices is a look-ahead error the domain tests catch before it is ever traded.

Closing those two gaps — building and verifying — is what a trusted skill does.

## What a trusted skill gives you

You use a trusted skill to build and extend applications by talking with the agent. What it gives you are the three things in the tagline, shown through one running example, a stock-trading skill. One app lets you describe and test a trading strategy, and a sister app runs your strategy on live prices (on paper, no real money).

**Provision — you build by describing.** The skill ships a set of well-known trading rules; use one as-is, or describe your own in conversation. For example say, "buy when the price has climbed steadily and sell when it stalls." The agent implements the rule, tells you what it assumed where your description was incomplete, and your conversation keeps refining until it's exactly the rule you meant. Then it helps you test what it built.

**Tests — the skill runs tests on what you build.** A trusted skill carries its own tests, and the agent runs them on anything new you create. For a trading rule, one test confirms it never used future prices to decide a past buy or sell — the classic mistake that flatters a rule on history and fails it in practice. Each problem domain has its own domain-specific tests.

**Sense and respond.** The sister app monitors live price feeds and executes the strategy you specified, continuously. At any point it can tell you what you now hold, what changed, and why — you can have a conversation with it to understand its actions and your portfolio. You can also extend the app to watch news and social feeds and use them to shape trading decisions.

## What it's most useful for

Trading is one instance, not the point. The same three-part shape — you build by describing, the skill tests what you build, and the result is a system that runs and responds — fits any problem that is *concurrent* and where being *subtly wrong is costly*. That pairing is where a trusted skill earns its keep; for a simple, one-off task, the agent alone is enough.

- **Trading** *(available today).* The running example above: describe a strategy, test it against history, run it forward on live prices.
- **Drug discovery** *(planned).* Screen a large library of molecules, dock the survivors against a target, and spend expensive simulation only on the few that earn it. The hard part the substrate guards is the *gate* — never running the costly step on the wrong candidates — and the pipeline is composed by describing it, office feeding office, rather than by writing distributed code.
- **Monitoring and alerting** *(planned).* A family of persistent sense-and-respond apps — a morning brief, a price or news watcher, an inbox triager — built from one skill. Here the stakes are low, so the tests matter less and the value is simply a system that *runs and reacts* reliably. This is also the shape students start from when they build their own.

Each is the same skill pattern in a different domain — which is the real claim: not a trading tool, but a way to build dependable concurrent systems by talking, wherever they're worth building.

## How flexible is it? Changing the structure

A trusted skill's structure is a plain-English office spec plus small module files, so changing it is a conversation, not a refactor. Add a module — a new signal, a new analyzer — by describing it; the agent writes it, wires it in, and runs the tests on it. Remove one by saying so; it's unwired. Reorder or replace pieces by describing the new flow. What stays fixed is the tested substrate underneath — the engine and the coordination — so you are changing the *composition*, not re-deriving the hard parts. That is what makes reshaping both easy and safe: the tests re-run to confirm the new structure still holds its properties. The one honest limit is that a genuinely new *kind* of module that doesn't fit the harness's contract — say, a strategy that compares many stocks at once — is flagged as not fitting, rather than bent in silently.

## How it's built — layers of expertise

No one person writes a trusted skill. It is built in layers, each resting on the tested layer beneath it, and usually by different people contributing different expertise.

- **The systems foundation.** A distributed-systems specialist builds the hard, domain-independent machinery once and tests it hard: message-passing offices, termination detection, checkpointing and recovery. This is the layer where being wrong is subtle and expensive, and where almost nobody wants to become an expert. Every trusted skill stands on it, so no one above it has to get it right again. *(Here that is the `dissyslab` library and the foundation skill that fronts it.)*
- **The domain skill.** A domain expert — a trader, a chemist, a teacher — builds on the foundation: the components their field needs, and the tests that catch their field's characteristic mistakes, like the look-ahead check in trading. They contribute what they know and inherit the systems machinery for free. You do not have to understand consistent snapshots to be protected by one.
- **Skills on skills.** Nothing stops a further specialist from building on a domain skill — narrowing it to options rather than equities, or to one lab's assay — each new layer trusting the tested layer below and adding tests of its own.

That layering is the mechanism behind the word *trusted*. Trust here is not an assurance in a README; it is the accumulated result of each layer having been built and tested by someone who understood it, standing on ground that was already tested. It also settles who a skill is for: you don't need to be a systems expert to build a trading app, or a trader to run one.

## Get started

You already have the agent. What a trusted skill adds is the tested floor underneath it — so getting started means pointing your agent at a skill and then talking to it. There is nothing to learn first: describe what you want, and the agent builds it, tells you what it assumed, and runs the tests on the result.

[REVERSIBLE — exact wording TBD once the setup path is confirmed. Intended shape: ask your agent to install Trusted Skills and run a skill — e.g. *"install Trusted Skills and run the trading backtester on the chip stocks"* — and it clones, installs, and runs, with the conversation continuing from there. Confirm the one-line install and the `dsl` entry point before this section goes public.]

## Workshop — for students and builders

The workshop is the tier below the skills. A skill hands you a domain someone has already made trustworthy; the workshop is for people who want to build an office themselves — a new sense-and-respond system for a hobby, a club, a lab, a small business. It holds the build-your-own path (agent-assisted, starting from an English office spec), a gallery of roughly thirty working example offices to read and copy, and a course with short interactive micro-courses.

It is also a real distributed-systems course, and for the same reason the skills are dependable. Students, including first-years, build an app for something they actually care about — then lift the floorboards and study the algorithms holding it up: how a system knows it is done, how it takes a consistent snapshot of a moving target, how independent agents agree. The motivation is that the algorithm under study is the one running in the thing they built. For the formal treatment of concurrent algorithms behind the course, see *Parallel Program Design: A Foundation*, K. Mani Chandy and Jayadev Misra (Addison-Wesley, 1988).

## Honest limitations

Named here so no one infers a promise the software does not keep.

- **Single machine; each agent is a thread.** An office runs in one process with each agent in its own thread. Per-agent process parallelism (`dsl run --processes`) does not work on any platform — agents hold un-picklable queues and closures. The intended unit of process parallelism is a whole office, not a single agent. Multi-machine distribution is roadmap, not release.
- **Checkpoint-recovery is implemented but opt-in.** The framework implements the Chandy-Lamport distributed snapshot algorithm, and one gallery office demonstrates the protocol end to end. Other offices get it as their authors add `save_state` / `load_state` to their stateful agents.
- **One domain skill exists.** Trading is live and tested — backtester, paper trader, and the look-ahead check. Drug discovery and the monitoring family are marked *planned* above because they have not been built, and the foundation (distributed) skill is still being written.
- **Trading is on paper.** The apps place no real orders and connect to no broker. Nothing here is investment advice, and a strategy that passes every test can still lose money.
- **No first-party web UI.** The framework stays Python-only. Wrapping an office in a React/FastAPI frontend is the recommended pattern for authors who want one, and several offices have been shipped that way.
- **The tests are domain checks, not proofs.** They catch the mistakes a domain knows it makes. They do not certify that what the agent built is what you meant — the conversation does that, and you stay in the loop.

## Install and license

`pip install dissyslab` installs the library. Python 3.10 or newer; Linux and macOS are the supported platforms and both run in CI. Windows runs the framework, but its CI job is not green: the checkpoint/resume tests fail there because Windows will not delete a file another handle still has open.

MIT license. [Badges, CI status, repo links, and the one-line installer to be carried over once the entry path above is confirmed.]
