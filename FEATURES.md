# Feature inventory — what's actually built, as of 2026-07-21

A reference snapshot after 18 months of work on DisSysLab and OfficeSpeak, so
you don't have to hold all of it in your head. Everything below was confirmed
by actually reading the code/docs/tests in both repos on this date — nothing
here is from memory or guesswork. Each item is marked:

- **Built & verified** — real code, actually run/tested, not just designed.
- **Built** — real code exists and works, but hasn't been exercised as
  thoroughly as "verified" items.
- **Scoped, not built** — a real design decision is recorded, no code yet.
- **Designed, not built** — a fuller design doc exists, no code yet.

---

## 1. Core runtime primitives (DisSysLab `dissyslab/blocks/`)

| Primitive | What it is | Status |
|---|---|---|
| `Source` | Feeds messages into the office from the world | Built & verified |
| `Transform` | One inbox, one outbox, stateless or stateful computation | Built & verified |
| `Sink` | Consumes messages, no outbox | Built & verified |
| `Coordinator` (base class) | Several inboxes/outboxes, behavior controlled by its own state — the base for every *deterministic* coordination primitive | Built & verified |
| `merge_synch` | Join over `in_0..in_{n-1}`, emits combined message when all slots fill (dict-merge by default) | Built & verified |
| `gate` | Admits from `in_` while free, switches to reading `done` while busy | Built & verified |
| `select` | Ask-and-wait: reads whichever inport its own state points to | Built & verified |
| `fair_merge` (`MergeAsynch`) | The **one nondeterministic primitive** — reads whichever inbox is ready first | Built |
| `fanout` / `fanin` / `split` | Structural helpers (broadcast, multi-source merge, routing) — compiler auto-inserts these when an office's wiring needs them | Built & verified |
| `record` | A shared, stateful "keeper" role (e.g. a ledger, a portfolio) | Built & verified |

`router`/`Split`-as-coordination-primitive was considered and explicitly
**rejected** — routing to one of several places is plain computation, so an
ordinary `Transform` covers it; not worth a dedicated primitive.

---

## 2. Registered sources & sinks (`docs/SOURCES_AND_SINKS.md`)

**11 source types**, no code required to use, declared directly in
`office.md`: 10 named RSS feeds sharing one implementation (Hacker News, Al
Jazeera, BBC World, BBC Tech, NPR, TechCrunch, + 4 more), `console_input`,
`weather`, `stocks`, `bluesky`, `web` (MCP shortcut), `search` (Brave, MCP
shortcut), `gmail` (credentialed), `calendar` (any public ICS, credentialed),
`webhook` (inbound HTTP POSTs), `mcp_source` (any MCP server tool, advanced).

**9 sink types**: `discard`, `console_printer`, `intelligence_display`
(color-coded briefing display), `jsonl_recorder` (+ `jsonl_recorder_*` for
multiple files in one office), `gmail_sink`, `slack_sink`, `webhook_sink`,
`mcp_sink`.

This catalogue is a **fixed, finite list** — a real, known limitation
(already documented in OfficeSpeak's README): if an office needs something not
on this list, the honest answer is "not supported yet" or reclassify as a
stand-in for testing, not a silent guess.

**Before saying "not supported":** check `mcp_source`/`mcp_sink` against the
[MCP Registry](https://modelcontextprotocol.info/tools/registry/) (500+
community servers as of 2026) — many asks are already reachable without new
code. And check `DisSysLab/docs/SOURCES_AND_SINKS.md`'s "Adding more" section
(added 2026-07-22) for a surveyed list of easy-to-add candidates (Discord,
Telegram, USGS earthquakes, crypto prices, CSV/SQLite, more RSS feeds) —
not built, but each mirrors an existing entry closely enough that testers
asking for one of these by name is a good signal for what to build next.

---

## 3. Distributed-systems features

| Feature | Status | Notes |
|---|---|---|
| **Checkpoint/resume** (global distributed snapshot) | **Built & verified** | Real adaptation of the 1985 algorithm, with a four-way recovery handshake and a source/sink boundary protocol so a crash-and-resume produces no duplicate/missing messages. Spec: `docs/algorithms/CHECKPOINT_RESUME.md`. Demoed end-to-end in `recovery_demo` (5-agent Monte Carlo π). |
| **Termination detection** | **Built & verified**, recently fixed | Coordinator-aware quiescence predicate — a coordinator blocked on one inbox doesn't falsely count a nonempty-but-unreachable channel as live work. A real correctness bug here (hangs on coordinator-heavy offices) was found and fixed **2026-07-15** — six days before this inventory. Full suite passing (446 tests) at time of fix. |
| **Debugging aid (a): isolated worker testing** | **Built & verified** | Test one computational worker alone on hand-picked inputs; localizes body bugs. Worked example: `OfficeSpeak/offices/debug_demo/` (planted bug: 10 false alerts → 1 correct alert after fix). Computational workers only — LLM workers are shown their prompt, not graded. |
| **Debugging aid (b): channel-count liveness check** | **Scoped, not built** | Catches a stuck coordinator via sent/received imbalance. Design recorded in `docs/internals/debugging_aids_decision.md`. |
| **Debugging aid (c): per-agent activity log (logical-clock trace)** | **Built & verified** (2026-07-22) | Each agent logs what it received/sent, tagged with a physical-time-grounded hybrid logical clock (`x := max(t, x+1)` on every receive — see `docs/algorithms/TRACE_AND_LOGICAL_CLOCK.md`). `dsl run --trace` records it; `dsl explain-trace <office_dir>/trace/` merges every agent's log into one causally-ordered JSONL sequence; Claude narrates that record in English by reading it fresh, not via a template. Verified end-to-end against a real `recovery_demo` run: per-agent clocks strictly increasing, correct causal ordering, a real send/receive tie-break bug found and fixed during verification. Works uniformly on computational **and** LLM workers, unlike aid (a). Full pytest suite (446 tests) passing after the change. |
| **Checkpoint explainer** (`dsl show-checkpoint`) | **Built & verified** (2026-07-22) | The Pat-facing counterpart to the trace explainer, for a snapshot instead of a run: merges one checkpoint's `manifest.json`, per-agent saved state, and any in-flight channel messages into one human-readable JSON document (`dsl show-checkpoint <office_dir> <N\|latest>`). Closes the "explain a checkpoint to Pat" gap that PAPER_NOTES.md had flagged as design-only. Same division of labor as the trace tools — DisSysLab merges, Claude narrates. Verified against `recovery_demo`'s own real checkpoints, including one caught with a real in-flight message. Spec: `docs/algorithms/CHECKPOINT_RESUME.md`. |
| **Debug-mode exact replay** | **Scoped, not built** | A *different, harder* feature for engineers: replay a run bit-for-bit from a checkpoint by logging every source of nondeterminism (fair_merge order, LLM responses, RNG/clock/external calls). Design: `docs/internals/replay_debug_mode_decision.md`. Known open gap: bodies that grab nondeterminism the substrate can't see (raw `time.time()`/`random` calls). |

---

## 4. Gallery apps & examples (DisSysLab)

**24 apps** in `dissyslab/gallery/apps/`, **9** in `dissyslab/gallery/examples/`.
Grouped by what they're actually for:

**News / social / market monitoring** (the largest cluster — sense-and-respond
offices watching a live feed and reacting): `arxiv_radar`, `competitor_watch`,
`inbox_triage`, `kalshi_market_watch`, `new_grad_jobs`, `periodic_brief` /
`periodic_brief_pro`, `situation_room` / `situation_room_pro` /
`situation_room_requests`, `stocks_monitor`, `weather_monitor`, `web_monitor`
(examples/), `gmail_monitor` (examples/), `org_news_editorial` /
`org_news_filter` / `org_intelligence_briefing` / `org_situation_room` /
`org_two_office_news` (examples/).

**Personal / productivity**: `wardrobe_assistant` (calendar + weather +
inventory), `job_hunter` (5-agent RSS filter + 4 parallel LLM analysts),
`lead_qualifier` (webhook → CRM), `ticket_router` (webhook → Slack),
`shipment_release`.

**Perception / non-text input**: `backyard_birds` (audio → BirdNET species
ID), `wildlife_watcher` (camera-trap images), `loudness_monitor` (audio
stream, the simplest sense→detect→respond example).

**Multi-agent structure demos**: `debate` (3-agent panel, iterative
consensus), `trading_room` and `investment_club` — **these two are
validation fixtures**, not demo apps: they confirm the generic `select` /
`record` / `gate` primitives match OfficeSpeak's own worked examples in
`start_gallery/` exactly (closing specific tracked tasks, e.g. task #31/#32).
`org_two_office_news` demonstrates an office containing other offices.

**Direct `office.md` examples** (added this session, for people using
DisSysLab without OfficeSpeak's conversation layer): `app_test`,
`returns_desk`, `room_climate_monitor`.

**Starter**: `my_first_office` (Hacker News, single agent, the onboarding
example for someone learning DisSysLab directly).

---

## 5. OfficeSpeak Stage 1 / Stage 2 pipeline

| Piece | Status |
|---|---|
| Stage 1 (describe → build → explain → correct, on claude.ai, no install) | **Built & verified** — this is the mature, complete part of the pipeline. |
| "Things I assumed —" self-disclosure + correction loop | **Built & verified** |
| Source/sink matching (`phase3_source_sink_matching.md`) | **Built**, currently a human-followed doc, not automated |
| Worker approval (`phase3_approval.md`) | **Built**, same caveat |
| `python -m dissyslab.office.assemble` (hand-off file → office.md + roles/) | **Built & verified** — real generator, validated on real cases (investment_club, room_climate_monitor) |
| One-command Stage 2 (no human following two docs by hand) | **Not built** — already an explicitly documented known limitation in `README.md`, not new information, just confirming it's still true |
| **Cold-test evaluation protocol** | **Built & verified** — a real, rigorous methodology: fresh, uncontaminated subagent instances, pre-registered expected outcomes before running, 9 recorded cases (`offices/claude_project/cold_tests/transcripts/`: 7 "start module" cases + 2 "full chain" cases). This is real evidence for the paper's validity section, not just an internal sanity check. |

---

## 6. Tester-facing materials (built this session, for the record)

`README.md` (Stage 1/2 front door), `GETTING_THE_FILES.md`, `stage1_microcourse.html`
+ `stage2_microcourse.html` (now live via GitHub Pages on `kmchandy.github.io`),
`STAGE2_WALKTHROUGH.md`, `INVESTMENT_CLUB_WALKTHROUGH.md`,
`DEMO_RECORDING_SCRIPT.md`, `PAPER_NOTES.md`.

---

## Quick answer to "what's NOT built yet"

See `ROADMAP.md` for the priority-ordered version of this list, plus what
we decided to actively *not* pursue (and why) as of 2026-07-23:

- Debugging aid (b) (channel-count liveness check) and debug-mode exact
  replay are both **decided not to pursue** — see `ROADMAP.md`'s "Decided
  not to pursue" section for the reasoning.
- Stage 2 as a single command (currently needs a Python-comfortable person
  following two docs by hand) — accepted as permanent, but reducing the
  friction is on the roadmap.
- Adding a new registered source/sink outside the fixed catalogue —
  mitigated by the MCP Registry and webhook fallbacks (see
  `DisSysLab/docs/SOURCES_AND_SINKS.md`'s "Adding more"), not eliminated.
- OpenRouter/multi-LLM backend selection and per-agent process/thread
  control exist in DisSysLab but aren't documented for Al yet, and Pat has
  no way to ask for either in English (nor is she expected to).
- Guided onboarding/description elicitation for Pat, compositionality, and
  surfacing theory/proofs to Pat are all real, larger gaps — see
  `ROADMAP.md` for what order to tackle them in.

(Debugging aid (c) — the logical-clock activity-log trace and its
playback — and the checkpoint explainer were both built and verified
2026-07-22; see §3 above. Both were "designed, not built" as of this
document's original write-up on 2026-07-21.)
