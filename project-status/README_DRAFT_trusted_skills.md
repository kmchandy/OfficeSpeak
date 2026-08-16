<!-- DRAFT — the working front door for the single repo. This file supersedes
     the earlier README_trusted_skills.md, which was deleted on 2026-08-16;
     there is no other copy. Not yet installed as the repo's public README.md.

     Revision 2026-08-16b. Two changes from the previous draft:
     (1) "trusted skill" is no longer used as a defined term in body text.
         "Trusted Skills" remains the project banner; the things in it are
         skills, in the standard Agent Skills sense, and the section
         "What makes these skills different" states the distinguishing
         properties as facts a reader can check rather than as a virtue.
     (2) An oversell pass. Every change is listed in the handback notes;
         the recurring fixes were: virtue words with nothing behind them
         ("dependable", "safe"), universal claims ("any", "never", "will"),
         guarantees about agent behavior that are really instructions to the
         agent, and — the important one — "verifying", which claimed more
         than testing delivers.

     Still to confirm: the Get started commands (does `dsl list` show skills
     or only offices?), and whether the harness contract check in
     "How flexible is it" covers the case described. Both are marked [CHECK]. -->

# Trusted Skills

> **Build persistent, concurrent applications in a conversation with an AI agent coupled with tested libraries.**
> *(paper-only where money is involved — simulated, never a real order.)*

This repository holds Agent Skills in the ordinary sense: folders with a
`SKILL.md` and bundled resources, loadable by Claude, Codex, Gemini CLI, and
other agents that read the format. What is unusual about them is stated below,
in terms you can check.

## What it is — the middle way

Three ways to get software, and where these skills sit between them:

- **A standard app** has every feature wired in. You pick among the options its builders imagined; there is no conversation. Fast, but you live inside someone else's decisions.
- **A general agent alone** has nothing wired in. Everything is an English conversation, built from scratch each time. Endlessly flexible, but you carry all the work — and the risk of getting the hard parts wrong.
- **A skill is the middle way.** The hard, common machinery comes already built and tested, so you save that work — and you keep the freedom to modify, extend, and check the system by talking. Its designer has drawn a deliberate line: enough wired in to spare you the work, enough left open to make the app yours.

You already have a capable AI agent — Cowork (Anthropic), say — that can read files, run code, and hold a conversation. This repository adds what such an agent should not improvise: tested libraries for the machinery supporting an application — concurrency primitives, and domain-specific components (a ledger for a stock-trading app, a screening pipeline for a drug-discovery app). You describe an application in English, and the agent assembles it from those libraries instead of generating the concurrent machinery from scratch each time.

That matters because concurrent systems are hard in ways a general agent can get subtly wrong: they are nondeterministic — the same program can behave differently from run to run — and their state spans many processes and message queues, so even operations that are trivial for a sequential program, like checkpointing and termination detection, are subtle for a concurrent one. Two things follow from reusing a library rather than regenerating the machinery. The code you run has a version history and a test suite, so fixes accumulate in it instead of being rediscovered per app. And you inherit services rather than build them: an app built on these skills knows when it has finished (termination detection), and can checkpoint and resume after a crash wherever its stateful components opt in.

## What makes these skills different

Two properties, both checkable. Neither is "we tested it" — every competent
author tests their own code, so that distinguishes nothing.

1. **The agent composes machinery it does not write.** The concurrency substrate is an installed, versioned package (`dissyslab`) with its own test suite, not instructions the model reproduces afresh each session. What makes the behavior reliable is the part that is off-limits to generation. The check: is the machinery a dependency you can pin and audit, or text that is regenerated per run?

2. **The checks run on code the skill's author never saw.** An ordinary skill's tests are the author's tests of the author's code, run in CI before release. These skills carry checks that run at build time against a component *you* just described — code that did not exist when the skill was written. For a trading rule, one such check looks for the classic look-ahead error: using a day's future prices to make that day's decision. The check: does the skill test artifacts it did not ship?

Closing those two gaps — building and checking — is what these skills do. Checking is not verification: the checks catch the mistakes a domain knows it makes, and prove nothing about the mistakes it does not.

## What a skill gives you

You use a skill to build and extend applications by talking with the agent. Three things, shown through one running example, a stock-trading skill. One app lets you describe and test a trading strategy, and a sister app runs your strategy on live prices (on paper, no real money).

**Provision — you build by describing.** The skill ships a set of well-known trading rules; use one as-is, or describe your own in conversation. For example say, "buy when the price has climbed steadily and sell when it stalls." The skill instructs the agent to implement the rule and to name what it assumed where your description was incomplete, and the conversation continues until you are satisfied it is the rule you meant. Then it helps you test what it built.

**Checks — the skill tests what you build.** A skill carries its own checks, and the agent runs them on anything new you create. For a trading rule, one looks for the classic look-ahead error — the mistake that flatters a rule on history and fails it in practice. Each problem domain has its own domain-specific checks.

**Sense and respond.** The sister app monitors live price feeds and executes the strategy you specified, continuously. At any point it can tell you what you now hold, what changed, and why — you can have a conversation with it to understand its actions and your portfolio. You can also extend the app to watch news and social feeds and use them to shape trading decisions.

## What it's most useful for

Trading is one instance, not the point. The same three-part shape — you build by describing, the skill checks what you build, and the result is a system that runs and responds — fits problems that are *concurrent* and where being *subtly wrong is costly*. That pairing is where a skill earns its keep; for a simple, one-off task, the agent alone is enough.

- **Trading** *(available today).* The running example above: describe a strategy, test it against history, run it forward on live prices.
- **Drug discovery** *(planned).* Screen a large library of molecules, dock the survivors against a target, and spend expensive simulation only on the few that earn it. The hard part the substrate guards is the *gate* — not running the costly step on the wrong candidates — and the pipeline is composed by describing it, office feeding office, rather than by writing distributed code.
- **Monitoring and alerting** *(planned).* A family of persistent sense-and-respond apps — a morning brief, a price or news watcher, an inbox triager — built from one skill. Here the stakes are low, so the checks matter less and the value is simply a system that *runs and reacts* reliably. This is also the shape students start from when they build their own.

The claim is that the pattern transfers across domains — not a trading tool, but a way to build concurrent systems by talking, wherever they are worth building. One domain is built. That is one instance, not evidence that the pattern generalizes; the other two are listed as planned because they would be the test of it.

## How flexible is it? Changing the structure

A skill's structure is a plain-English office spec plus small module files, so changing it is a conversation, not a refactor. Add a module — a new signal, a new analyzer — by describing it; the agent writes it, wires it in, and runs the checks on it. Remove one by saying so; it's unwired. Reorder or replace pieces by describing the new flow. What stays fixed is the tested substrate underneath — the engine and the coordination — so you are changing the *composition*, not re-deriving the hard parts. That is what keeps reshaping cheap: you are recomposing parts that already have tests, and those checks re-run against the new arrangement. The honest limit is that a genuinely new *kind* of module that does not fit the harness's contract — say, a strategy that compares many stocks at once — is reported as a mismatch rather than silently reshaped, for the contracts the harness actually checks. [CHECK: confirm the cross-sectional-strategy case is one of them.]

## How it's built — layers of expertise

A skill here is not written all at once by one person; it is built in layers, each resting on the tested layer beneath it, and often by different people:

- **The systems foundation.** A distributed-systems specialist builds and tests the hard, domain-independent machinery once — message-passing offices, termination detection, checkpointing and recovery. Every skill here stands on it, so no one above has to re-derive it. *(This is the `dissyslab` library.)*
- **The domain skill.** A domain expert — a trader, a chemist, a teacher — builds an application on top of the foundation: the domain's components and its own checks, like the trading skill's look-ahead check. They contribute what they know about their field and inherit the systems machinery.
- **Skills on skills.** Further specialists can build on a domain skill — refining a corner of it — each new layer standing on the tested one below.

That layering is the point: expertise is contributed once, at the right level, and reused by everyone above — you don't need to be a systems expert to build a trading app, or a trader to run one. It is also the argument for why the lower layers should hold up better than freshly generated code: each was built and tested by someone who understood it, on a layer that had already been tested. It is an argument, not a guarantee — a library can be wrong in ways its own tests do not reach. *(In the repo, `skills/` mirrors this: a foundation skill that the domain skills build on.)*

## Get started — you already have an AI agent

The fastest path is to let your agent do the setup. In Cowork (or a similar agent), point it at the repository and say what you want:

> *"Clone github.com/kmchandy/DisSysLab, install it, and run the trading backtester on a few chip stocks."*

It clones the code, installs the `dissyslab` library, opens the trading skill, and runs it — and from there you drive everything by conversation: *"try a momentum rule," "use a tighter stop," "what did that strategy do in 2020?"*

Prefer to set it up yourself? Install the library with `pip install dissyslab` (Python 3.10+), then follow the trading skill's own short setup notes to run it. `dsl list` shows the example offices that ship with the package. [CHECK: does `dsl list` also list skills, or only offices?]

Nothing here places a real trade — trading skills are paper-only: simulated, never a real order.

## Workshop — for students and builders

Beneath the finished skills is the workbench they are built on, and it is open. To build your own office from scratch — a monitor, a pipeline, something no existing skill covers — you describe it and your agent assembles it from the same tested foundation; the gallery of example offices is there to learn from and adapt.

It is also a course. Because the foundation is transparent as well as tested, you can lift the floorboards and study how it works — how an office detects that it has finished, how it takes a consistent snapshot of a running system in order to checkpoint it. Students build something they care about, then study the distributed-systems ideas underneath it. The algorithm under study is the one running in the thing they built, which is the motivation an exercise set does not supply.

## Honest limitations

Named plainly, so no one infers promises the system does not keep:

- **Single machine, for now.** An office runs in one process, each agent in its own thread. Per-agent process parallelism does not work yet; the intended unit of process parallelism is a whole office, and multi-machine distribution is on the roadmap.
- **Checkpoint-recovery is real but opt-in.** The framework implements consistent distributed snapshots (Chandy–Lamport). An app gets it where the author of a stateful component has added `save_state` / `load_state` to it — not automatically everywhere.
- **The checks are domain checks, not proofs.** They catch mistakes the domain knows it makes. They do not establish that what the agent built is what you meant; the conversation does that, and you stay in the loop.
- **No first-party web UI.** Skills are driven by conversation and produce files — reports, briefs, action lists; web front-ends are a demonstrated pattern, not a built-in.
- **Two of the three demos are planned.** Trading is available today; drug discovery and the monitoring family, described above, are *planned* and not yet built.
- **The structure described here is partly a target.** The `skills/` and `workshop/` layout above is where the repository is going; today the trading apps and the gallery still live under their original paths.
- **Platforms.** Linux and macOS are supported and tested; Windows runs, but its CI job is not green — the checkpoint/resume tests fail there because Windows will not delete a file another handle still has open.

## Install and license

The library is on PyPI — `pip install dissyslab` (Python 3.10+). The one-line installer, full source, and test suite are in the repository at github.com/kmchandy/DisSysLab. Licensed under MIT.
