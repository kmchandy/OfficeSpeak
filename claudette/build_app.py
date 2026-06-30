"""
claudette/build_app.py — Stage 6, end-to-end driver.

Single command from Pat's input to a buildable DSL app directory:

    python3 -m claudette.build_app --pseudo path/to/spec.pseudo \\
                                   --name my_app \\
                                   --output ./apps/

Pipeline:
    spec.pseudo  --[parser]--> graph.yaml
    graph.yaml   --[office_writer]--> office.md
    graph.yaml   --[orchestrator]--> roles/<role>.md  (one per vertex)

Output layout (under <output>/<name>/):
    spec.pseudo        copy of input
    graph.yaml         Stage B output
    office.md          Stage B' output
    roles/             role files
        <role>.md
        ...

After building, the app is ready for `dsl build` and `dsl run` (those
steps are NOT invoked by this driver; see --build / --run options).

Future work (Stage A — not in v1):
    --spec path/to/spec.md     run Claudette on Pat's English spec
                                first to produce spec.pseudo.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# Make the parent dir importable when invoked as a script
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR.parent))

from claudette.parser import parse, ParseError  # noqa: E402
from claudette.office_writer import write_office_md  # noqa: E402
from claudette.prompt_orchestrator import orchestrate  # noqa: E402

import yaml  # noqa: E402


def build_app(
    pseudo_path: Path,
    app_name: str,
    output_dir: Path,
    *,
    use_llm: bool | None = None,
    overwrite: bool = False,
    verbose: bool = True,
) -> Path:
    """Run the full chain. Returns the app directory.

    Stages:
      1. Read spec.pseudo and copy to <app_dir>/spec.pseudo.
      2. Parse → graph; write <app_dir>/graph.yaml.
      3. Render → office.md; write <app_dir>/office.md.
      4. Orchestrate per-vertex prompts → <app_dir>/roles/<role>.md.
    """
    pseudo_path = Path(pseudo_path)
    output_dir = Path(output_dir)
    app_dir = output_dir / app_name

    if app_dir.exists():
        if not overwrite:
            raise FileExistsError(
                f"{app_dir} already exists. Pass --overwrite to replace."
            )
        shutil.rmtree(app_dir)
    app_dir.mkdir(parents=True)

    def log(msg: str):
        if verbose:
            print(f"[build_app] {msg}", file=sys.stderr)

    # 1. Copy spec.pseudo into the app dir
    spec_dest = app_dir / "spec.pseudo"
    shutil.copy2(pseudo_path, spec_dest)
    log(f"copied {pseudo_path} -> {spec_dest}")

    # 2. Parse pseudocode -> graph
    pseudo_text = pseudo_path.read_text()
    try:
        graph, warnings = parse(pseudo_text)
    except ParseError as e:
        raise SystemExit(f"parser error: {e}")
    for w in warnings:
        log(f"warning: {w}")
    graph_path = app_dir / "graph.yaml"
    graph_path.write_text(yaml.safe_dump(graph, sort_keys=False, allow_unicode=True))
    log(
        f"wrote graph.yaml: {len(graph['sources'])} sources, "
        f"{len(graph['vertices'])} vertices, "
        f"{len(graph['sinks'])} sinks, "
        f"{len(graph['edges'])} edges"
    )

    # 3. Render graph -> office.md
    office_text = write_office_md(graph, app_name)
    office_path = app_dir / "office.md"
    office_path.write_text(office_text)
    log(f"wrote office.md")

    # 4. Orchestrate per-vertex prompts -> roles/*.md
    role_paths = orchestrate(
        graph, app_dir, use_llm=use_llm, overwrite=True, verbose=verbose
    )
    log(f"wrote {len(role_paths)} role files in {app_dir}/roles/")

    return app_dir


def _run_dsl_command(cmd: list[str], app_dir: Path) -> int:
    """Run a `dsl` subcommand inside app_dir. Returns the exit code."""
    print(f"[build_app] running: {' '.join(cmd)} (cwd={app_dir})", file=sys.stderr)
    try:
        proc = subprocess.run(cmd, cwd=app_dir)
        return proc.returncode
    except FileNotFoundError:
        print(
            "[build_app] `dsl` not on PATH. Install DSL or run "
            "`pip install -e ~/Documents/DisSysLab`.",
            file=sys.stderr,
        )
        return 127


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="End-to-end driver: pseudocode -> graph -> office -> roles."
    )
    p.add_argument("--pseudo", required=True, help="Path to spec.pseudo")
    p.add_argument("--name", required=True, help="App name (becomes directory name)")
    p.add_argument(
        "--output", default="./apps",
        help="Directory where the app folder will be created (default: ./apps)",
    )
    p.add_argument(
        "--llm", action="store_true",
        help="Force LLM (Claude) mode for per-vertex prompts",
    )
    p.add_argument(
        "--no-llm", action="store_true",
        help="Force template mode for per-vertex prompts (no LLM calls)",
    )
    p.add_argument(
        "--overwrite", action="store_true",
        help="Replace the app directory if it already exists",
    )
    p.add_argument(
        "--build", action="store_true",
        help="After building artifacts, run `dsl build` in the app directory",
    )
    p.add_argument(
        "--run", action="store_true",
        help="After building (and `dsl build`), run `dsl run`",
    )
    args = p.parse_args(argv)

    use_llm = None
    if args.llm:
        use_llm = True
    if args.no_llm:
        use_llm = False

    app_dir = build_app(
        Path(args.pseudo),
        args.name,
        Path(args.output),
        use_llm=use_llm,
        overwrite=args.overwrite,
    )

    print(f"\n[build_app] app built at: {app_dir}")
    print(f"[build_app] artifacts:")
    for p in sorted(app_dir.rglob("*")):
        if p.is_file():
            print(f"  {p.relative_to(app_dir)}")

    if args.build or args.run:
        rc = _run_dsl_command(["dsl", "build", "."], app_dir)
        if rc != 0:
            return rc
    if args.run:
        rc = _run_dsl_command(["dsl", "run", "."], app_dir)
        if rc != 0:
            return rc

    return 0


if __name__ == "__main__":
    sys.exit(_main())
