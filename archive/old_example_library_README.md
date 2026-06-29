# Claudette's example library

Claudette (the LLM that builds sense-and-respond systems from
English specs) consults a library of *example offices* during
precedent search (Stage 2 of the builder pipeline). The library
helps her transfer design reasoning from known-good apps to a
new task.

## Layout

This directory contains:

- `INDEX.yaml` — the registry of apps in Claudette's library,
  with paths to their metadata files
- `external/` — metadata files for apps that live outside the
  DSL gallery (e.g., Nyasha's apps)

The metadata files for **gallery apps** live alongside the apps
themselves, in `dissyslab/gallery/apps/<app_name>/`. This avoids
duplicating `office.md` and keeps the rationale and failure
documentation co-located with the code it describes.

## What metadata each app provides

Every entry in the library has six artifacts:

| File | What it is | Who reads it |
|---|---|---|
| `office.md` | The live office spec | Everyone |
| `README.md` | Human-facing introduction | Humans |
| `task.md` | Abstract spec — "what would a user have asked for to get this office?" | Claudette + humans |
| `meta.yaml` | Machine-readable metadata: tags, complexity, patterns, applies_when, does_not_apply_when | Claudette (and tooling) |
| `rationale.md` | Design decisions, alternatives considered, generalisable lessons | Claudette + humans |
| `failures.md` | Known failure modes + when this design breaks | Claudette + humans |
| `samples/` | Cached input/output examples | Claudette + humans |

For gallery apps, `office.md` and `README.md` already exist;
the other four files are added when the app joins Claudette's
example library.

## How Claudette uses the library

At Stage 2 (precedent search) of the build pipeline:

1. Read `INDEX.yaml`
2. For each entry, read `meta.yaml` (fast — small file)
3. Match the new task's characteristics against each `meta.yaml`'s
   `applies_when` / `does_not_apply_when` / patterns / etc.
4. For the top 2–3 matches, read the full `task.md`,
   `rationale.md`, and `failures.md`
5. Cite specific precedents and lessons in subsequent build
   stages

## Leave-one-out protocol

When Claudette is rebuilding an app that is itself in the
library (e.g., `situation_room` or `job_hunter`), the matching
entry is filtered out of the precedent set. This makes the
rebuild test honest: Claudette must reason from analogous
examples, not copy.

The filter rules live in `INDEX.yaml` under `leave_one_out`.

## Adding a new entry

1. Author the five metadata files in the app's folder
   (or in `external/<app_name>/` for non-gallery apps)
2. Add an entry to `INDEX.yaml` under `gallery_apps` or
   `external_apps`
3. If the app is also a rebuild target, add a `leave_one_out`
   rule

That's it. Claudette will see the new precedent on her next run.
