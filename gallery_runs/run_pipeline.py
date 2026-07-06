#!/usr/bin/env python3
"""
gallery_runs/run_pipeline.py — drive one gallery app through the pipeline
and log every stage, so a whole app's journey is inspectable:

    spec.md  →  pseudocode.txt (Claudette)  →  graph.yaml  →  diagram  →  run

The source language is the NoT **pseudocode**, not asyncio. Claude reads
spec.md under the meta-prompt and returns pseudocode; the rest is
mechanical (``officespeak.parser`` turns pseudocode into a graph, which
compiles to a runnable DSL network). We do NOT save office.md —
graph.yaml is canonical.

Three modes.

Scaffold a new app::

    python gallery_runs/run_pipeline.py --new <app>

    Creates gallery_runs/<app>/ with a spec.md template, a pseudocode.txt
    placeholder, and notes.md.

Build the paste-ready prompt (meta-prompt + this app's spec)::

    python gallery_runs/run_pipeline.py --prompt <app>

    Writes gallery_runs/<app>/prompt.txt — paste this into a fresh Claude
    chat; paste Claude's reply into pseudocode.txt.

Log every stage from a filled-in pseudocode.txt::

    python gallery_runs/run_pipeline.py <app> [--execute]

    Writes, next to pseudocode.txt:
        warnings.txt    parser warnings (empty == clean)
        graph.yaml      the graph the parser produced
        diagram.html    self-contained Mermaid diagram (open in a browser)
        diagram.mermaid Git-friendly diagram source
        app/graph.yaml  copy compiled against the DSL role library
        compile.txt     compile result (blocks + connections, or the error)
        run.log         execution output (only with --execute)
"""

from __future__ import annotations

import argparse
import io
import sys
import traceback
from contextlib import redirect_stdout
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_META_PROMPT = _ROOT / "prompts" / "meta_prompt_v1.md"


# --------------------------------------------------------------------------- #
# Scaffolding templates                                                       #
# --------------------------------------------------------------------------- #

_SPEC_TEMPLATE = """\
# {app} — Pat's spec

Pat's English description: a non-coder saying what they want — sources,
processing, output — with no topology, agent count, or framework details.

---

<Write the one-paragraph Pat-style description here.>
"""

_PSEUDO_PLACEHOLDER = """\
# PLACEHOLDER — paste Claudette's pseudocode here.
#
# 1. python gallery_runs/run_pipeline.py --prompt {app}
# 2. paste gallery_runs/{app}/prompt.txt into a fresh Claude chat
# 3. replace this file's contents with the fenced pseudocode Claude returns
# 4. python gallery_runs/run_pipeline.py {app}
"""

_NOTES_TEMPLATE = """\
# notes — {app}

Fill in after pasting Claudette's pseudocode and running the pipeline.

## Metadata

- Claude model used:
- Date / time of session:
- Surface (claude.ai web, API, etc.):

## Pseudocode result

- In-grammar (parses with 0 warnings)? If not, what did the parser reject?
- Decomposition correct (matches the intended shape:
  pipeline / router / feedback)?
- Did Claude use only registered sources/sinks, or invent names?
- If the spec was inexpressible, did Claude emit a clean `# ERROR:` line?

## Graph + run

- graph.yaml shape (sources / vertices / sinks / edges):
- Compiled against the role library? Ran? Output sane?

## Variance (if sampled more than once)

- Stable across runs, or did the decomposition change?
"""


def _load_spec_body(app_dir: Path) -> str:
    """Return the spec text below the `---` marker (Pat's description)."""
    spec = (app_dir / "spec.md").read_text()
    if "\n---\n" in spec:
        return spec.split("\n---\n", 1)[1].strip()
    return spec.strip()


def scaffold(app: str) -> int:
    app_dir = _ROOT / "gallery_runs" / app
    if app_dir.exists():
        print(f"{app_dir} already exists; not overwriting.", file=sys.stderr)
        return 1
    app_dir.mkdir(parents=True)
    (app_dir / "spec.md").write_text(_SPEC_TEMPLATE.format(app=app))
    (app_dir / "pseudocode.txt").write_text(_PSEUDO_PLACEHOLDER.format(app=app))
    (app_dir / "notes.md").write_text(_NOTES_TEMPLATE.format(app=app))
    print(f"Scaffolded {app_dir}. Write spec.md, then --prompt {app}.")
    return 0


def build_prompt(app: str) -> int:
    app_dir = _ROOT / "gallery_runs" / app
    if not (app_dir / "spec.md").exists():
        print(f"no spec.md in {app_dir}", file=sys.stderr)
        return 1
    meta = _META_PROMPT.read_text()
    spec_body = _load_spec_body(app_dir)
    prompt = (
        meta.rstrip()
        + "\n\n---\n\n## Pat's task\n\n"
        + spec_body
        + "\n"
    )
    (app_dir / "prompt.txt").write_text(prompt)
    print(f"Wrote {app_dir/'prompt.txt'} (meta-prompt + spec).")
    return 0


# --------------------------------------------------------------------------- #
# Stage runner                                                                #
# --------------------------------------------------------------------------- #


def _dump_yaml(obj) -> str:
    try:
        import yaml
        return yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)
    except ImportError:
        import json
        return json.dumps(obj, indent=2, default=str)


def run_stage(app: str, execute: bool) -> int:
    from officespeak.parser import parse, ParseError
    from officespeak.graph_viz import render

    app_dir = _ROOT / "gallery_runs" / app
    pseudo = app_dir / "pseudocode.txt"
    if not pseudo.exists():
        print(f"no pseudocode.txt at {pseudo}", file=sys.stderr)
        return 1
    text = pseudo.read_text()
    if "PLACEHOLDER" in text:
        print(f"{pseudo} is still the placeholder — paste pseudocode first.",
              file=sys.stderr)
        return 1

    stages: list[tuple[str, str]] = []

    # 1. Parse pseudocode -> graph.
    try:
        graph, warnings = parse(text)
    except ParseError as exc:
        (app_dir / "warnings.txt").write_text(f"ParseError: {exc}\n")
        stages.append(("parse", f"FAILED: {exc}"))
        _print_summary(app, stages)
        return 1
    (app_dir / "warnings.txt").write_text(
        "\n".join(warnings) + ("\n" if warnings else "")
    )
    (app_dir / "graph.yaml").write_text(_dump_yaml(graph))
    stages.append((
        "parse",
        "ok (0 warnings)" if not warnings else f"ok ({len(warnings)} warnings)",
    ))

    # 2. Diagram.
    (app_dir / "diagram.mermaid").write_text(render(graph, "mermaid"))
    (app_dir / "diagram.html").write_text(
        render(graph, "html", title=app)
    )
    stages.append(("diagram", "ok (diagram.html, diagram.mermaid)"))

    # 3. Generate one role prompt per vertex (Stage C). Template mode is
    #    deterministic and offline; the graph names roles by verb phrase
    #    (e.g. "write briefing" -> briefing_writer), which won't all exist
    #    in the built-in library, so we materialize them here.
    app_out = app_dir / "app"
    app_out.mkdir(exist_ok=True)
    (app_out / "graph.yaml").write_text(_dump_yaml(graph))
    try:
        from officespeak.prompt_orchestrator import orchestrate
        role_files = orchestrate(
            graph, app_out, use_llm=False, overwrite=True, verbose=False
        )
        stages.append(("roles", f"ok ({len(role_files)} role files, template)"))
    except Exception as exc:  # noqa: BLE001
        stages.append(("roles", f"FAILED: {exc}"))

    # 4. Compile graph -> DSL network.
    try:
        from officespeak.graph_to_dsl import compile_graph
        net, warns = compile_graph(app_out, name=app)
        chk = getattr(net, "check", None)
        if callable(chk):
            chk()
        n_conn = len(getattr(net, "connections", []) or [])
        (app_dir / "compile.txt").write_text(
            f"OK\nblocks: {sorted(getattr(net, 'blocks', {}).keys())}\n"
            f"connections: {n_conn}\nwarnings: {warns}\n"
        )
        stages.append(("compile", f"ok ({n_conn} connections)"))
    except ImportError as exc:
        (app_dir / "compile.txt").write_text(
            f"SKIPPED (dissyslab not importable): {exc}\n"
        )
        stages.append(("compile", f"skipped (no dissyslab)"))
    except Exception as exc:  # noqa: BLE001 - a failed compile is a result
        (app_dir / "compile.txt").write_text(
            f"FAILED: {exc}\n\n{traceback.format_exc()}"
        )
        stages.append(("compile", f"FAILED: {exc}"))
        _print_summary(app, stages)
        return 0  # translation still succeeded; compile failure is logged

    # 4. Execute (optional).
    if execute:
        try:
            from officespeak.graph_to_dsl import compile_graph
            net, _ = compile_graph(app_out, name=app)
            buf = io.StringIO()
            with redirect_stdout(buf):
                net.run_network()
            (app_dir / "run.log").write_text(buf.getvalue())
            stages.append(("execute", "ok (run.log)"))
        except Exception as exc:  # noqa: BLE001
            (app_dir / "run.log").write_text(
                f"FAILED: {exc}\n\n{traceback.format_exc()}"
            )
            stages.append(("execute", f"FAILED: {exc}"))

    _print_summary(app, stages)
    return 0


def _print_summary(app: str, stages: list) -> None:
    print(f"\n{app}")
    for name, status in stages:
        mark = "✓" if not status.startswith("FAILED") else "✗"
        print(f"  {mark} {name:<10} {status}")


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Drive a gallery app: pseudocode -> graph -> diagram -> run."
    )
    p.add_argument("app", nargs="?", help="App name under gallery_runs/")
    p.add_argument("--new", metavar="APP", help="Scaffold a new app and exit")
    p.add_argument("--prompt", metavar="APP",
                   help="Build prompt.txt (meta-prompt + spec) and exit")
    p.add_argument("--execute", action="store_true",
                   help="Also run the network, logging to run.log")
    args = p.parse_args(argv)

    if args.new:
        return scaffold(args.new)
    if args.prompt:
        return build_prompt(args.prompt)
    if not args.app:
        p.error("give <app>, or --new <app>, or --prompt <app>")
    return run_stage(args.app, args.execute)


if __name__ == "__main__":
    sys.exit(_main())
