# trading_desk — run mechanics (termination, one checkpoint, trace)

From reading DisSysLab (`os_agent.py`, `snapshot.py`, `docs/algorithms/
CHECKPOINT_RESUME.md`, `components/sources/csv_points_source.py`, `cli.py`).

## Termination detection
- `OsAgent` declares termination when: every agent heard from, AND for every edge
  sent-count == received-count. Each source sends one termination message when its
  `run()` returns.
- => Use **bounded sources**: emit M prices and N headlines, then return.
- Loops are fine: TD is per-edge count-matching, so the head-trader <-> risk-manager
  cycle does not block termination. (This is the "works even with loops" claim.)
- Demo sizes: M ~= 120 price ticks (enough for several MA crossings), N ~= 12
  headlines.

## Exactly one checkpoint
- Checkpoints are **time-based**: OS agent snapshots every `snapshot_interval`
  seconds (`--snapshot-interval SECONDS` / env `DSL_SNAPSHOT_INTERVAL`) until
  termination.
- Sources have an `interval` (inter-emission sleep) so a snapshot has something to
  capture. Run length R ~= (messages) x (source interval).
- For exactly one checkpoint want **R/2 < T < R**: one marker fires mid-run, the
  next would fire after termination.
- Starting point: prices interval ~0.02 s, news interval ~0.2 s => R ~= 2.5-3 s;
  set `--snapshot-interval 1.5`. Do one dry run to measure R, then set T ~= 0.6 R.
- Sources must be **checkpoint-aware** (poll the OS, like `csv_points_source`) to be
  captured in the snapshot.

## FINDING: no merge-order logging (checked in code)

Confirmed by reading `blocks/fanin.py` (MergeAsynch) and `core.py` (recv /
recording / recovery buffer):
- MergeAsynch runs one worker thread per inport, each `recv(port)` then
  `send(msg, "out_")`. The order messages reach `out_` is thread-scheduler
  dependent and is **not recorded anywhere**.
- The checkpoint records channel state **per inport** (`self._recording[
  "channels"][inport].append(msg)`) and replays the recovery buffer **per inport
  FIFO** (`self._recovery_buffer[inport].pop(0)`). The cross-inport interleaving
  (the office's only nondeterminism) is discarded.

Consequences, by property:
- Chandy-Lamport consistent cut: correct (unaffected by merge order).
- Crash-recovery world-correctness (no gap/dup): correct **by design** — the
  boundary protocol skips by count, and `CHECKPOINT_RESUME.md` explicitly says
  "Determinism is not required." So this is NOT a recovery bug.
- Deterministic replay for debugging: **not supported as-is** — resume can forward
  the merge's inputs in a different order, so "rerun from checkpoint is
  deterministic" does not hold. This is the gap relative to the paper's
  deterministic-replay claim.

Fix (sufficient, since the merge is the only nondeterminism): have MergeAsynch log
its forwarding choices — the sequence of source inports for each `out_` message —
as an ongoing log tied to the checkpoint, and on replay follow that recorded
sequence instead of racing threads. Record-and-replay of the single nondeterministic
choice point.

## Deterministic trace from the most recent checkpoint
- A checkpoint stores the consistent cut (per-agent `save_state()` + per-channel
  in-flight messages + manifest) — enough to RESTART, but **not** an action trace.
- NOT FOUND in code read: a per-agent action-trace facility, or a recorded
  fair-merge ingestion order in the recovery path. `CHECKPOINT_RESUME.md` states
  replay may diverge for nondeterministic agents (recovery is by count, not
  content). => deterministic replay needs the merge order logged; confirm whether
  that exists elsewhere or is the piece to add.
- For THIS demo the workers are deterministic (chart-analyst = Python; news =
  keyword stub, no LLM), so a reproducible trace needs only:
  1. resume from latest checkpoint;
  2. lightweight per-agent logging: append each `run()` input -> output to a trace
     file;
  3. record the head-trader's fair-merge ingestion order (the office's one fair
     merge) so the forward run reproduces the same interleaving.
- Explaining the trace to Pat: deferred (per Mani).

## Build order for the running demo
1. Bounded, checkpoint-aware price + news sources (mock/replay).
2. Wire the office: prices -> chart-analyst; news -> news-analyst(stub); both signal
   streams -> fair_merge -> head-trader; head-trader <-> risk-manager (gate + book);
   head-trader -> TRADES sink; prices also -> head-trader (for the stale-price gotcha).
3. Run with `--snapshot-interval` tuned for one checkpoint; confirm TD fires and one
   checkpoint dir appears under snapshots/checkpoints/000000/.
