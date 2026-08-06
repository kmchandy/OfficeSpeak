# OfficeSpeak "Phase 3" — choosing a backend and deploying (task #35)

*Sibling to `phase3_source_sink_matching.md` and `phase3_approval.md`. Those
two cover the required gates (matching, approval) before generation. This
one covers two things every Al eventually needs but neither Stage 1 nor the
other two docs mention: which LLM backend an office's judgment workers
actually run on, and what it takes to keep a generated office running past
the terminal session that started it. Neither is a required gate — an
office with no judgment workers, run once for a demo, needs neither — but
real, ongoing use almost always needs both.*

## Part A — Choosing a backend

**This section is a thin, OfficeSpeak-specific layer on top of
`DisSysLab/docs/LANGUAGE_MODELS.md`, which is the real reference — read
that for the full mechanics (the Backend Protocol, writing your own
backend, named temperature variants, per-role and per-agent overrides).
This section only answers the question LANGUAGE_MODELS.md doesn't:
*which one should this office use, and when does it matter enough to
choose deliberately.*

### Does this office even need one?

Only offices with **judgment workers** — a role Phase 2 described as
requiring understanding, weighing, or writing, rather than a fixed
computation — call an LLM at all. A worker Phase 2 described as "add up
the fees" or "check if the count exceeds the threshold" is a computational
transform; it never touches a backend. Check Phase 2's own notes on each
worker before assuming a backend choice matters here — for a
computation-only office (like the investment-club walkthrough's current
gallery form), this whole section is a no-op.

### The three real choices, in the order most people should consider them

1. **OpenRouter** (`DSL_BACKEND=openrouter`, `OPENROUTER_API_KEY=...`) —
   the recommended default for anyone past a single local demo. Cheap,
   fast, cloud-hosted, and lets you point different agents at different
   open-weight models without juggling several providers' API keys. This
   is also where this project's own empirical evaluation runs, so it's
   the best-exercised path. **This is the right default for a real
   organizational deployment** — e.g. an office that needs to run
   continuously and reliably for a team, not just a one-off test.
2. **Ollama, local** (`DSL_BACKEND=ollama`) — free, private, runs on your
   own machine, no data leaves it. Right choice when cost must be exactly
   $0 or data can't leave the building, at the cost of slower responses
   and more variable JSON reliability on smaller models.
3. **A commercial API directly** (Claude / OpenAI / Gemini) — highest
   quality and reliability, real per-token cost. Right choice when a
   judgment worker's output quality matters more than running cost, e.g.
   a small number of high-stakes calls per day rather than a
   high-volume feed.

Mixing is normal, not exotic: a cheap, high-volume filtering worker on
Ollama or a small OpenRouter model, and a small number of
higher-stakes judgment workers (final recommendation, customer-facing
text) on Claude or GPT — see LANGUAGE_MODELS.md §4, "Per-role model
choice," and the `office.md` sentence form:

```
Agents:
Filter's AI is qwen.
Recommender's AI is claude.
```

### Cost, roughly

From LANGUAGE_MODELS.md's own numbers: a pipeline running 100 items/day
through 5 judgment workers is ~500 LLM calls/day. On Claude Sonnet
pricing that's roughly $0.45/day (~$14/month) per office; the same
office on Ollama or a cheap OpenRouter model is close to $0. Scale this
by however many workers in *your* office are judgment workers, not the
office's total worker count.

### What to actually do, as Al

1. Reread Phase 2's per-worker notes; list which workers are judgment
   workers (need a backend) vs. computational (don't).
2. Pick one of the three choices above as the office's default
   (`DSL_BACKEND`), based on: does this need to run unattended for an
   organization (→ OpenRouter), does data-privacy or cost-zero matter
   more than speed (→ Ollama), or does a small number of high-stakes
   calls justify paid quality (→ Claude/OpenAI/Gemini)?
3. If any individual worker's quality bar or cost profile differs from
   the rest, override it per-agent in `office.md` (the `Agents:` sentence
   form above) rather than changing the whole office's default.
4. Set the matching environment variable(s) before `dsl run` (see
   LANGUAGE_MODELS.md §1–2 for exact commands per backend), and confirm
   with `dsl doctor`.

## Part B — Deploying: keeping an office running past this terminal

**This is a real, previously undocumented gap** — every worked example
so far (`dsl run <office>`) assumes someone is watching a terminal. Real
use — the kind Joe Kiniry described, business agents that run like
cron jobs — needs the office to keep running after that terminal closes,
survive a crash, and put its output somewhere retrievable.

### The lightweight option — good enough for one person, one machine

Run the office detached from the terminal session, so closing your laptop
lid or logging out doesn't kill it:

```bash
nohup dsl run my_office > my_office.log 2>&1 &
disown
```

- `nohup ... &` — runs in the background, immune to the terminal closing.
- `> my_office.log 2>&1` — sends both normal output and errors to a file
  you can `tail -f my_office.log` later.
- `disown` — detaches it from this shell fully.

Alternative, if you prefer to reattach and watch it live: run inside
`tmux` or `screen` instead of `nohup` — `tmux new -s myoffice`, then
`dsl run my_office`, then detach with `Ctrl-b d` and reattach anytime with
`tmux attach -t myoffice`.

**This does not survive a machine restart or crash on its own.** If the
process dies (crash, reboot, `kill`), nothing restarts it automatically —
see the next option if that's not acceptable.

### The sturdier option — restart on crash, survive a reboot

Use a real process supervisor. On macOS, a `launchd` agent; on Linux, a
`systemd` user service or a tool like `supervisord`. All of these do the
same job: start the office on boot/login, and restart it automatically if
it exits unexpectedly. Writing the actual unit file is environment-specific
enough that it's out of scope for this doc — the key thing an Al setting
this up needs to know is what happens *when it restarts*, below.

### Why this connects to checkpointing — and what "restart" actually means here

An office that crashes and gets restarted by a supervisor does **not**
resume from where it left off unless you tell it to. Two real options:

- **Cold restart** (`dsl run my_office` again, no flags) — starts fresh,
  as if for the first time. Fine for offices with no meaningful
  cross-run state (e.g. a pure news filter with no memory).
- **Resume from checkpoint** (`dsl run my_office --resume` from the
  latest snapshot, if the office was started with
  `--snapshot-interval N`) — picks up mid-execution with no lost or
  duplicated messages, using the same global-snapshot machinery covered
  in `DisSysLab/docs/algorithms/CHECKPOINT_RESUME.md`. This is the right
  choice for any office with real accumulated state (a ledger, a running
  count, anything Pat would be upset to lose).

**Practical rule of thumb:** if the office was described with any
"remembers" or "shared record" language in Phase 1/2 (a portfolio, a
history, a running total), run it with `--snapshot-interval` from the
start and configure the supervisor to restart with `--resume`, not a cold
`dsl run`. If it's purely reactive with no memory, a cold restart is
simpler and just as correct.

### Where output actually goes

Whatever sink(s) the office was built with — `jsonl_recorder`,
`gmail_sink`, `slack_sink`, and so on — keep writing wherever they always
write; deployment doesn't change this. The `nohup`/`tmux` log file above
is a *separate* thing: it's the office's own diagnostic stdout/stderr
(errors, restarts, `--trace` output if enabled), not its actual business
output. Don't confuse the two when troubleshooting.

## See also

- `DisSysLab/docs/LANGUAGE_MODELS.md` — full backend mechanics.
- `DisSysLab/docs/algorithms/CHECKPOINT_RESUME.md` — the snapshot/resume
  algorithm referenced above.
- `phase3_source_sink_matching.md`, `phase3_approval.md` — the two
  required gates this doc doesn't replace or duplicate.
