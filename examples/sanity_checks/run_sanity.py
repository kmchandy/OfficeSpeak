"""
Sanity-check driver for the four non-ERROR test cases.

For each NN_<name>.expected.pseudo, this script:
  1. Runs claudette/parser.py    -> NN_<name>.graph.yaml
  2. Runs claudette/office_writer -> NN_<name>.office.md
  3. Runs DSL's parse_office_dir  -> verifies acceptance
  4. Prints a one-line summary per case.

Run from the repo root:
    python3 examples/sanity_checks/run_sanity.py
"""

from __future__ import annotations

import sys
import json
from pathlib import Path

# Make `claudette` importable when run from repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from claudette.parser import parse, ParseError  # noqa: E402
from claudette.office_writer import write_office_md  # noqa: E402

import yaml  # noqa: E402


SANITY_DIR = Path(__file__).parent

# The four cases that go end-to-end (case 05 is an ERROR case).
CASES = [
    ("01_weather_alert", "weather_alert"),
    ("02_arxiv_summary", "arxiv_summary"),
    ("03_inbox_triage", "inbox_triage"),
    ("04_debate", "debate"),
]


def _try_dsl_parse(office_text: str, tmp_dir: Path) -> tuple[bool, str]:
    """Try parsing office.md with DSL. Return (ok, message)."""
    try:
        from dissyslab.office.parser import parse_office_dir
    except ImportError:
        return False, "dissyslab not installed"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    (tmp_dir / "office.md").write_text(office_text)
    try:
        spec = parse_office_dir(tmp_dir)
        return True, (
            f"DSL OK: {len(spec.sources)} sources, {len(spec.sinks)} sinks, "
            f"{len(spec.agents)} agents, {len(spec.connections)} connections"
        )
    except Exception as e:
        return False, f"DSL parse error: {type(e).__name__}: {e}"


def main():
    print(f"Running sanity checks in {SANITY_DIR}\n")
    summary_lines = []
    failures = 0

    for case_prefix, office_name in CASES:
        pseudo_path = SANITY_DIR / f"{case_prefix}.expected.pseudo"
        graph_path = SANITY_DIR / f"{case_prefix}.graph.yaml"
        office_path = SANITY_DIR / f"{case_prefix}.office.md"

        print(f"--- {case_prefix} ---")

        # 1. parse
        try:
            pseudo_text = pseudo_path.read_text()
            graph, warnings = parse(pseudo_text)
            graph_path.write_text(
                yaml.safe_dump(graph, sort_keys=False, allow_unicode=True)
            )
            print(f"  [✓] parser -> {graph_path.name} "
                  f"({len(graph['sources'])} sources, "
                  f"{len(graph['vertices'])} vertices, "
                  f"{len(graph['sinks'])} sinks, "
                  f"{len(graph['edges'])} edges)")
            for w in warnings:
                print(f"      warning: {w}")
        except ParseError as e:
            print(f"  [✗] parser FAILED: {e}")
            summary_lines.append(f"{case_prefix:30}  PARSER FAILED")
            failures += 1
            print()
            continue

        # 2. office_writer
        try:
            office_text = write_office_md(graph, office_name)
            office_path.write_text(office_text)
            print(f"  [✓] office_writer -> {office_path.name}")
        except Exception as e:
            print(f"  [✗] office_writer FAILED: {e}")
            summary_lines.append(f"{case_prefix:30}  WRITER FAILED")
            failures += 1
            print()
            continue

        # 3. DSL acceptance
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ok, msg = _try_dsl_parse(office_text, Path(td))
            print(f"  [{'✓' if ok else '✗'}] {msg}")
        if not ok and "not installed" not in msg:
            summary_lines.append(f"{case_prefix:30}  DSL REJECTED")
            failures += 1
            print()
            continue

        summary_lines.append(f"{case_prefix:30}  OK")
        print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for line in summary_lines:
        print(line)
    print()
    print(f"{len(CASES) - failures}/{len(CASES)} cases passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
