# The framework-builds-framework pattern: an abstract recipe

Working notes for the CHI 2027 submission. This document generalizes what
`mac_speed_suite` and `adaptive_tutor` actually have in common into a
recipe other offices (a daily-brief cockpit, a sensor dashboard) can
follow, and is honest about the one step in that recipe that cannot be
made mechanical.

## The shape, stated abstractly

Both existing examples decompose into three regions:

```
SHARED, UNCHANGING          ONE SMALL TYPED FUNCTION          SHARED, UNCHANGING
upstream machinery    -->   (the only thing that varies    -->   downstream machinery
                              between instances)
```

Concretely:

| | mac_speed_suite | adaptive_tutor |
|---|---|---|
| Shared upstream | `csv_stock_history` (one data source, unchanged per strategy) | `session_starter` (one per subject, but generic/parameterless) |
| **The one varying function** | `compute_variant_signal(bars, params) -> signal` | `generate_problem(rng, params) -> problem` |
| Config table | `VARIANTS` = speed name -> window lengths | `VARIANTS` = difficulty name -> session length, ranges |
| Shared wrapper/factory | `make_signal_computer(strategy_name, variants, compute_fn)` | `make_subject_bank(subject_name, variants, generate_fn)` |
| Shared downstream machinery | `BACKTESTER` -> `EVALUATOR` (identical role code, one instance per variant) | `PLANNER` -> `CHECKER` -> `STUDENT` (identical role code, one instance per subject) |
| Mechanical correctness check | no-lookahead: recomputing on a truncated history must not change day *t*'s signal | self-consistency + determinism + distractor-validity (`check_problem_ground_truth.py`) |
| Packaged as | `backtest-strategy-builder` skill | `tutor-subject-builder` skill |

Adding a new instance (a strategy, a subject) never touches the shared
regions. It always produces: one new file implementing the one varying
function against the documented signature, plus new agent instances in
`office.md` — some running genuinely new code, most running the exact same
unmodified shared role files, just instantiated again and wired the same
way the existing instances are. Recompiling (`dsl build`) is what turns
that into an actually larger running distributed system.

## The five ingredients, in general form

1. **A minimal, typed function signature** capturing exactly what differs
   between one instance of the class and another, and nothing else. Its
   inputs and outputs must be a fixed, documented shape — not "whatever
   the LLM decides to return this time."
2. **A `VARIANTS`-style config table**: named instance -> a params dict.
   This is what lets a domain author add difficulty tiers, speed windows,
   or similar variation *without touching code*.
3. **A shared wrapper/factory** that takes (name, variants, the one
   function) and produces whatever role-registration boilerplate the
   framework needs. This is what hides the framework from the domain
   author — they write one function and a dict, never a `Role(...)` or an
   `AgentRoleEntry(...)`.
4. **Shared, unmodified downstream (or upstream) machinery** that consumes
   (or produces for) every instance through the same generic contract,
   never needing to know which instance it's talking to.
5. **A mechanical, domain-specific correctness check** — no LLM judgment
   involved in the check itself. This is never free and never generic:
   no-lookahead only makes sense because a trading signal has a causality
   invariant; ground-truth/determinism only makes sense because a tutoring
   problem's own generator can be asked to reproduce itself. Every new
   domain needs its own invariant, hand-designed, from the shape of *that*
   domain's correctness story. There is no universal checker.

Steps 1-5 are what a Skill packages into a natural-language procedure:
elicit intent -> write the one function -> run the check -> wire new
instances into `office.md` the same way the existing ones are wired ->
rebuild -> verify end to end -> confirm the diff stayed contained to the
new piece plus `office.md`.

## The one step that is *not* mechanical

Before any of the five ingredients can be designed, someone has to answer
a question that has no algorithm: **where, in this particular office, does
the axis of anticipated future variation actually sit, relative to
machinery that's already shared?**

In both existing examples the answer happened to be the same shape: a
single shared *source* feeds a family of interchangeable *downstream*
computations. That is not guaranteed to be the shape for every office. The
axis of variation could just as easily sit *upstream* of a shared
consumer — many different sources, all feeding one shared aggregator. The
recipe is symmetric (the wrapper/factory idea and the mechanical-check
idea both still apply), but which side the new typed function sits on
changes what its signature has to look like, and this has to be worked
out by hand for each candidate office, not derived from a template.

## Applying it to a cockpit (daily brief / Salton Sea sensor dashboard)

`salton_sea_dashboard` as currently built does *not* fit this pattern yet
— it has two hand-written sources (`salton_wind`, `synthetic_salton_h2s`)
merged by a `synchronizer` and formatted into one report, not a family of
interchangeable variants of one thing. Turning it (or a daily-brief
cockpit generally) into a real instance of this pattern means working
through the same five ingredients honestly, and the axis of variation
turns out to sit on the *opposite* side from the two existing examples:

- **Axis of variation**: not "a different way to interpret the same
  data" (that's mac_speed_suite/adaptive_tutor's shape) but "a different
  data feed entirely" — a new sensor, a new news source, a new calendar
  integration. The new thing is naturally a new *source*, upstream of a
  shared aggregator/formatter.
- **The one varying function**, restated for this shape: not a pure
  compute function over already-fetched data, but an *adapter* —
  `fetch_and_normalize(raw_feed_response, params) -> section` — where
  `section` is a fixed, generic shape (e.g. `{"title": str, "lines":
  [str, ...], "timestamp": ..., "quality_note": str}`) that a shared
  `REPORT_FORMATTER` already knows how to render, the same way `BACKTESTER`
  already knows how to consume any `signal` and `PLANNER` already knows
  how to consume any `problem`.
- **Config table**: less "difficulty tiers," more "which named feed and
  its access parameters" (a URL, a poll interval, a unit system) — still
  a `VARIANTS`-shaped dict.
- **Shared wrapper**: `make_cockpit_source(feed_name, variants,
  fetch_and_normalize)`, structurally identical in spirit to
  `make_signal_computer` / `make_subject_bank`.
- **Shared downstream machinery**: one `REPORT_FORMATTER`/`AGGREGATOR`
  that never changes as feeds are added, consuming every feed's `section`
  dict through the same generic shape.
- **Mechanical correctness check**: the honest limitation is that a live
  network fetch can't be replayed deterministically the way a signal or a
  problem generator can. The checkable invariant has to live one level
  down from "is the live data right" — e.g., given a *recorded* or
  synthetic sample response, does the adapter always produce a `section`
  with all required keys, no empty title, a timestamp that parses, and
  values inside a declared sane range; and is it deterministic given the
  same input. This is the cockpit's analog of no-lookahead/ground-truth:
  checkable without redoing the domain's own judgment, but it verifies the
  *adapter*, not the live feed itself — a distinction worth stating
  plainly rather than overclaiming.

**The honest caveat this example surfaces, worth stating in the paper
directly**: for mac_speed_suite and adaptive_tutor, the genuinely new,
irreducible work per addition is small (one pure function). For a
cockpit, the genuinely new, irreducible work per addition is bigger —
every new feed needs real integration code (a new API, new auth, a new
`SOURCE_REGISTRY` entry) that this pattern does not, and should not try
to, generalize away. What the pattern *does* still buy a cockpit is real:
the formatting/aggregation half of adding a feed (turning whatever that
feed returns into something the shared report already knows how to
render, verified mechanically before it's wired in) can be handed to the
same kind of Skill-packaged, natural-language process as the other two
domains. The data-access half remains bespoke engineering, same as
`csv_stock_history` and `session_starter` already are today for the two
existing examples — this pattern was never claiming to generalize *that*
part, and it would be a weaker, less credible paper if it implied
otherwise.

## When this doesn't fit at all

Generalizing both apps' own "when this doesn't fit" sections: this pattern
needs (a) a genuine family of instances that are structurally
interchangeable from the shared machinery's point of view, not a fixed
small set of qualitatively different things; (b) a correctness story
that's checkable from an instance's own declared outputs, without
re-deriving whether those outputs are *actually* right; and (c) a shared
consumer (or producer) that can be written once and truly never needs to
know which instance it's talking to. Multi-step problems with intermediate
checkpoints, anything that compares across instances (a leaderboard across
students, a cross-strategy correlation report), and open-ended judgment
with no fixed contract at all are the three concrete failure modes
identified so far, and likely generalize to: whenever the "shared
downstream machinery" would actually need instance-specific knowledge to
do its job, the pattern has broken down and you have a bespoke office, not
an extensible framework.
