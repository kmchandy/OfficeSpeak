# Trusted Skills — restructure plan

**Status: PLAN ONLY. Nothing in the repo has been moved.** Per our method,
reversible framing (this plan + the new README) comes first; migrations that move
files come later, timed around the tester round.

## Decisions locked (2026-08-15)

- **Claim:** value added to Cowork with trusted skills — distributed
  infrastructure and app-domain infrastructure.
- **Story / project name:** **Trusted Skills.**
  Tagline (draft): *"Value added to Cowork: a tested distributed-systems
  substrate plus per-domain infrastructure, so you build real, persistent
  applications by talking."*
- **PyPI package `dissyslab`:** UNCHANGED (installs + external imports depend on
  it; a rename has no graceful redirect).
- **GitHub repo `kmchandy/DisSysLab`:** keep for now; can rename later (GitHub
  redirects the old URL).
- **Paper (`draft_v3.md` etc.):** stays private for now, public later after
  revision. Not part of this restructure.
- **Individuals' names never appear in the public repo.**

## The one story

Cowork (the user brings it) + **distributed infrastructure** (system-level
trusted floor) + **app-domain infrastructure** (domain-level trusted floor).
Experienced as three beats: **provision → trust → habit.** Demonstrated by three
apps. Taught to students, who study the three to see what they can build.

## Target structure

```
README.md              # the one story; tagline above
dissyslab/             # distributed-infrastructure LIBRARY (installable, name unchanged)
skills/
  distributed/         # FOUNDATION skill — build/run correct offices; backed by dissyslab
                       #   (= office-builder = third demo = student enabler); TO BUILD
  trading/             # domain skill, builds on distributed/        [LIVE]
    SKILL.md
    lib/               #   backtest math, ledger, look-ahead check (domain infra)
    apps/              #   backtester + paper_trader offices
    TUTORIAL.md
  drug_discovery/      # domain skill, builds on distributed/        TO BUILD
workshop/              # subordinated student tier: gallery, course, microcourses, build-your-own
docs/
```

### The key distinction (why `skills/` can "include the distributed infrastructure")

- **skill ≠ library.** `skills/` holds Cowork-facing *skills* (instructions +
  guardrails). The tested *distributed library* stays at the repo root as the
  installable `dissyslab` package.
- **Foundation skill** (`skills/distributed/`) = "build and run correct offices."
  Common to the whole class of applications; backed by `dissyslab`. It is also
  the **office-builder = the third demo = the student enabler** — one artifact,
  four roles, the root of the skills tree.
- **Domain skills** (`skills/trading/`, `skills/drug_discovery/`) **build on** the
  foundation skill; each ships its own domain library + demo app + tutorial +
  domain check (the look-ahead test for trading; the cost gate for drug
  discovery).

Dependency semantics: **domain skill —builds-on→ foundation skill —backed-by→
`dissyslab` library.**

## Built vs to build

- **Built & tested (LIVE):** the trading domain — backtester (`mac_speed_suite`),
  `paper_trader`, and the look-ahead self-check.
- **To build:** the foundation/distributed skill (office-builder / third demo /
  student enabler); the drug-discovery skill; the workshop consolidation.

## Migration sequence (reversible-first)

- **Phase 0 — Framing (reversible; no files moved).** Agree the target tree;
  finalize the README (skeleton → full) + tagline; this plan. ← *we are here.*
- **Phase 1 — Additive (low risk).** Scaffold `skills/`; author the foundation
  (distributed) skill = office-builder = third demo; build `drug_discovery`. All
  new files; nothing moved or broken.
- **Phase 2 — Migration (higher blast radius; AFTER the current tester round).**
  Move `mac_speed_suite` + `paper_trader` → `skills/trading/`; move the gallery →
  `workshop/`. Update, as a *move not an edit*: `office.md` relative paths (data
  dirs such as `sp100_data`), each skill's "Requires dissyslab/gallery/apps/…"
  line, the `.skill` bundles' internal references, `TUTORIAL` links, and any
  tester-facing links. Keep the two trading apps behavior-frozen — relocate only,
  don't change numbers — and verify `dsl run` still works after the move.
- **Phase 3 — Consolidate.** Fold OfficeSpeak's course + narrative into the single
  repo; retire the OfficeSpeak repo. Paper held back.
- **Phase 4 — Optional, later.** Rename the GitHub repo to match the story
  (redirects preserve links). **Never** rename the PyPI package.

## Sequencing constraints / risks

- **Do NOT run Phase 2 during the active tester round.** Vikram and Sebu hold
  links to `gallery/apps/mac_speed_suite` and `paper_trader`; moving them
  mid-test breaks their world. Migrate after their feedback lands.
- **Path breakage on move:** `office.md` relative paths, data directories,
  `dsl run` discovery, CI workflow paths, the committed `.skill` "Requires" lines,
  external links (the letter, Nyasha's repos, README badges).
- **Keep the honest-limitations ethos:** planned demos are marked *planned* in the
  README until they exist.

## Open items

- Final tagline wording.
- The example set the foundation skill's demo (gallery-family generation) draws
  from, and honest scope (dominant monitoring family, not literally all).
- Whether `skills/distributed/` bundles the office-builder scripts or references
  `dissyslab` only.
