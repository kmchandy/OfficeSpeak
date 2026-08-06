# Setting up the OfficeSpeak experiments with a Claude Project

Two one-time setup steps, then a repeatable per-demo loop.

## One-time: build the assistant (the "clone" Pat talks to)

1. On claude.ai, create a **Project** named **OfficeSpeak**.
2. Paste **`project_instructions.md`** into the Project's **custom instructions**.
   (These are the build + explain + write-bodies + debug instructions in one.)
3. Upload the **gallery** as Project **knowledge** — the worked examples that make the
   assistant expert. For each of these offices, upload its `spec.md`, its graph +
   explanation, and its agent bodies:
   - `investment_club` (deliberate: join + shared record + gate + ask-and-wait)
   - `trading_desk` (async: fair_merge + ask-and-wait loop)
   - `anomaly_monitor` (detect-anomaly: router + per-key state)
   - plus `START_HERE.md` and the primitives list (from the instructions).
4. **Do NOT upload any office you will use as a held-out demo** (e.g., `weather`). The
   gallery makes the assistant expert; the demos test that it generalizes to offices it
   has not seen.

That Project *is* the maximal expert. Pat opens a chat in it and starts building.

## Per held-out demo — the seven steps (see OFFICESPEAK_EXPERIMENTS.md)

0. **Pre-register** predictions in `<office>/spec_review.md` *before* running.
1. **Build:** new chat **inside the OfficeSpeak project**; Pat pastes only her
   `spec.md` (the builder instructions already live in the Project). The assistant
   returns the graph + explanation ("Things I assumed —") + agent bodies. Save to
   `runs/run_1/` (`graph_and_explanation.md`, `agents/`).
2. **Score** the explain-back vs predictions → `runs/run_1/notes.md`.
3. **Correct:** Pat gives one plain-English correction → revised office →
   `runs/run_1/correction.md`.
4. **Run:** wire the produced bodies into DSL, bounded input → termination detection +
   one checkpoint → `runs/run_1/run_output.txt`. (Done on the DSL side.)
5. **Debug:** produce the per-agent `debug_dict.json`; ask the assistant to explain one
   agent's tape → `runs/run_1/debug_explanation.md`.
6. **Record:** final scoring in `notes.md`.

## Keep it reproducible (for the paper)

- Record the **model** used and a snapshot of the Project's instructions + gallery, so
  runs are comparable.
- Same protocol and same artifact set for every demo (see `EXPERIMENT_LAYOUT.md`).
- Pre-registration + `runs/` recording is what makes the held-out results defensible.

## Note: `build_package.md` vs the Project

The per-office `build_package.md` files were a **stand-in** for the Project — they
front-load the builder prompt so a run can be reproduced in a bare chat with no Project.
With the real Project, Pat does **not** paste `build_package.md`; the instructions live
in the Project and she gives only her `spec.md`. Keep `build_package.md` for
reproducing a run without a Project, or for reviewers who want the exact self-contained
input.

## Immediate next steps

- Finalize the **weather** demo's `spec.md` + `spec_review.md` (async feeds → fair_merge
  → repository/record + gate; head-forecaster ask-and-wait regression; delayed match via
  the record). Keep it OUT of the gallery.
- Assemble the gallery files for the three offices (I can curate these into clean
  worked-example docs for upload).
