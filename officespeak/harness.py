"""
claudette/harness.py — Stage A measurement harness.

For each test case (spec.md + expected.pseudo), the harness:
  1. Reads spec.md (Pat's English description).
  2. Reads prompts/meta_prompt_v1.md (the system prompt).
  3. Sends them to Claude (or uses a mock fallback) -> Claudette's output.
  4. Saves the output as <case>.actual.pseudo.
  5. Parses both expected and actual through claudette/parser.py.
  6. Compares the resulting graphs by structural equivalence.
  7. Reports per-case: OK | STRUCTURAL DIFF | PARSE ERROR | LLM ERROR.

Structural equivalence ignores positional IDs (s0/v0/k0) and edge
declaration order: two graphs are equivalent iff there's a bijection
between their nodes that preserves names/params/role/reads/enriches/
outports AND preserves the edge structure.

Mock fallback: when no ANTHROPIC_API_KEY is set in the environment,
the harness uses the existing `<case>.expected.pseudo` as a stand-in
for Claudette's output. This exercises the parsing + comparison
chain so the harness itself can be verified, but does not measure
Claudette.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR.parent))

from officespeak.parser import parse, ParseError  # noqa: E402


# --------------------------------------------------------------------------- #
# Structural equivalence                                                      #
# --------------------------------------------------------------------------- #


def _source_key(source: dict):
    """Source identity for execution-equivalence: registry name only.

    Source params (e.g., max_articles, poll_interval) are config — they
    affect volume and timing but not what gets executed. Two designs
    that pull from `bbc_world` are execution-equivalent regardless of
    how many articles each fetches.
    """
    return source["name"]


def _sink_key(sink: dict):
    """Sink identity for execution-equivalence: registry name only.

    Sink params (e.g., path) are config — they affect WHERE output goes
    but not WHAT type of output is produced. Two designs that route to
    `jsonl_recorder_archive` are execution-equivalent regardless of the
    specific filename.
    """
    return sink["name"]


def _vertex_key(vertex: dict) -> tuple:
    """Vertex identity for execution-equivalence: (enriches, outports).

    Role name (derived from verb phrase) and reads list (which fields
    the agent inspects) are implementation choices — they don't change
    what the vertex contributes to the message or how routing works.

    Two vertices are execution-equivalent iff:
      - They add the same field to the message (`enriches`), AND
      - They have the same routing structure (outports).
    """
    return (
        vertex["enriches"],
        tuple(sorted(vertex.get("outports") or [])),
    )


def _build_key_map(graph: dict) -> dict:
    """Return id -> display-key for every node in the graph."""
    out = {}
    for s in graph.get("sources", []):
        out[s["id"]] = ("source", _source_key(s))
    for v in graph.get("vertices", []):
        out[v["id"]] = ("vertex", _vertex_key(v))
    for k in graph.get("sinks", []):
        out[k["id"]] = ("sink", _sink_key(k))
    return out


@dataclass
class StructuralDiff:
    """Container for a single comparison's result."""
    equivalent: bool
    differences: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.equivalent


def structural_equivalence(graph_a: dict, graph_b: dict) -> StructuralDiff:
    """Compare two graphs for structural equivalence.

    Returns a StructuralDiff. `bool(result)` is True iff equivalent.
    `result.differences` lists human-readable reasons when not equivalent.
    """
    diffs: list[str] = []

    # 1. Node sets must match (by structural key).
    for kind, fld in (("source", "sources"), ("sink", "sinks"), ("vertex", "vertices")):
        keys_a = {(_source_key(x) if kind == "source"
                   else _sink_key(x) if kind == "sink"
                   else _vertex_key(x))
                  for x in graph_a.get(fld, [])}
        keys_b = {(_source_key(x) if kind == "source"
                   else _sink_key(x) if kind == "sink"
                   else _vertex_key(x))
                  for x in graph_b.get(fld, [])}
        only_a = keys_a - keys_b
        only_b = keys_b - keys_a
        for k in sorted(only_a, key=str):
            diffs.append(f"{kind} only in expected: {k}")
        for k in sorted(only_b, key=str):
            diffs.append(f"{kind} only in actual:   {k}")

    # 2. Edge structure must match (after re-keying by display key).
    keymap_a = _build_key_map(graph_a)
    keymap_b = _build_key_map(graph_b)

    def edge_keys(graph, keymap) -> set:
        out = set()
        for e in graph.get("edges", []):
            from_id, from_port = e["from"]
            to_id, to_port = e["to"]
            from_key = keymap.get(from_id, ("?", from_id))
            to_key = keymap.get(to_id, ("?", to_id))
            out.add((from_key, from_port, to_key, to_port))
        return out

    edges_a = edge_keys(graph_a, keymap_a)
    edges_b = edge_keys(graph_b, keymap_b)
    only_a = edges_a - edges_b
    only_b = edges_b - edges_a
    for e in sorted(only_a, key=str):
        diffs.append(f"edge only in expected: {_fmt_edge(e)}")
    for e in sorted(only_b, key=str):
        diffs.append(f"edge only in actual:   {_fmt_edge(e)}")

    return StructuralDiff(equivalent=not diffs, differences=diffs)


def _fmt_edge(edge_tuple: tuple) -> str:
    """Render a re-keyed edge tuple for human display."""
    (from_kind, from_key), from_port, (to_kind, to_key), to_port = edge_tuple

    def fmt_node(kind: str, key) -> str:
        if kind == "vertex":
            # key is (enriches, outports_tuple)
            enriches, _outports = key
            return f"<vertex enriches={enriches}>"
        if kind == "source":
            # key is just the source name
            return f"<source {key}>"
        if kind == "sink":
            return f"<sink {key}>"
        return str(key)

    return (
        f"{fmt_node(from_kind, from_key)}.{from_port}"
        f" -> {fmt_node(to_kind, to_key)}.{to_port}"
    )


# --------------------------------------------------------------------------- #
# LLM call (Claudette as Stage A)                                              #
# --------------------------------------------------------------------------- #


def _call_claudette(meta_prompt: str, pat_spec: str) -> str:
    """Send (meta_prompt, pat_spec) to Claude. Returns raw response text."""
    try:
        from dissyslab.backends.anthropic_backend import AnthropicBackend
    except ImportError as exc:
        raise RuntimeError(
            "dissyslab not installed; cannot call Claudette. "
            "Install from local checkout: cd ~/Documents/DisSysLab && pip install -e ."
        ) from exc
    backend = AnthropicBackend()
    return backend.complete(system=meta_prompt, user=pat_spec, temperature=0.2)


_FENCE_RE = re.compile(r"```(?:[a-zA-Z0-9_-]*)?\n?(.*?)```", re.DOTALL)


def _extract_pseudocode(raw: str) -> str:
    """Pull the fenced pseudocode block from Claude's response.

    Per meta-prompt §2, Claudette's output is one fenced block. We
    extract the contents of the first fence. If there's no fence at
    all, return the raw text — better to let the parser surface the
    issue than to silently mishandle.
    """
    m = _FENCE_RE.search(raw)
    if m:
        return m.group(1).strip() + "\n"
    return raw.strip() + "\n"


# --------------------------------------------------------------------------- #
# Per-case runner                                                              #
# --------------------------------------------------------------------------- #


@dataclass
class CaseResult:
    case: str
    status: str             # "OK" | "DIFF" | "PARSE_ERROR" | "LLM_ERROR" | "MOCK"
    detail: str = ""
    actual_path: Optional[Path] = None


def run_case(
    case_prefix: str,
    cases_dir: Path,
    meta_prompt_path: Path,
    *,
    use_llm: Optional[bool] = None,
) -> CaseResult:
    """Run one case end-to-end. Persists <case_prefix>.actual.pseudo."""
    spec_path = cases_dir / f"{case_prefix}.spec.md"
    expected_path = cases_dir / f"{case_prefix}.expected.pseudo"
    actual_path = cases_dir / f"{case_prefix}.actual.pseudo"

    if not spec_path.exists():
        return CaseResult(case_prefix, "LLM_ERROR", f"missing {spec_path}")
    if not expected_path.exists():
        return CaseResult(case_prefix, "LLM_ERROR", f"missing {expected_path}")

    if use_llm is None:
        use_llm = bool(os.environ.get("ANTHROPIC_API_KEY"))

    # Stage A — get Claudette's output
    if use_llm:
        meta_prompt = meta_prompt_path.read_text()
        spec_text = spec_path.read_text()
        try:
            raw = _call_claudette(meta_prompt, spec_text)
        except Exception as e:
            return CaseResult(case_prefix, "LLM_ERROR", f"{type(e).__name__}: {e}")
        actual_text = _extract_pseudocode(raw)
        actual_path.write_text(actual_text)
    else:
        # Mock mode: use the expected as a stand-in. The comparison will
        # then trivially pass for unchanged cases; the harness's own
        # correctness has to be verified via unit tests.
        actual_text = expected_path.read_text()
        actual_path.write_text(actual_text)

    # Both ERROR outputs is a pass; mismatched ERROR is a diff.
    expected_text = expected_path.read_text()
    actual_is_error = actual_text.strip().startswith("# ERROR")
    expected_is_error = expected_text.strip().startswith("# ERROR")

    if expected_is_error and actual_is_error:
        status = "MOCK" if not use_llm else "OK"
        return CaseResult(
            case_prefix, status, "both expected and actual are ERROR (pass)",
            actual_path=actual_path,
        )
    if actual_is_error and not expected_is_error:
        return CaseResult(
            case_prefix, "DIFF",
            f"actual emitted ERROR but expected was parseable pseudocode: "
            f"{actual_text.strip()}",
            actual_path=actual_path,
        )
    if expected_is_error and not actual_is_error:
        return CaseResult(
            case_prefix, "DIFF",
            "expected ERROR output but actual produced parseable pseudocode",
            actual_path=actual_path,
        )

    # Both parseable — Stage B
    try:
        graph_actual, _ = parse(actual_text)
    except ParseError as e:
        return CaseResult(
            case_prefix, "PARSE_ERROR", str(e), actual_path=actual_path
        )
    try:
        graph_expected, _ = parse(expected_text)
    except ParseError as e:
        return CaseResult(
            case_prefix,
            "LLM_ERROR",
            f"expected.pseudo failed to parse: {e}",
            actual_path=actual_path,
        )

    # Structural comparison
    diff = structural_equivalence(graph_expected, graph_actual)
    if diff.equivalent:
        status = "MOCK" if not use_llm else "OK"
        return CaseResult(case_prefix, status, actual_path=actual_path)
    return CaseResult(
        case_prefix,
        "DIFF",
        "\n".join(f"    {d}" for d in diff.differences),
        actual_path=actual_path,
    )


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #


def _discover_cases(cases_dir: Path) -> list[str]:
    """Find every <prefix>.spec.md and return the prefixes (sorted)."""
    out = []
    for f in cases_dir.glob("*.spec.md"):
        out.append(f.stem.removesuffix(".spec"))
    return sorted(out)


def _main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Run the Claudette Stage-A harness on a directory of cases."
    )
    p.add_argument(
        "cases_dir",
        nargs="?",
        default="examples/sanity_checks",
        help="Directory of <case>.spec.md + <case>.expected.pseudo files",
    )
    p.add_argument(
        "--meta-prompt",
        default="prompts/meta_prompt_v1.md",
        help="Path to the meta-prompt",
    )
    p.add_argument(
        "--llm", action="store_true",
        help="Force LLM mode (otherwise auto: LLM iff ANTHROPIC_API_KEY)",
    )
    p.add_argument(
        "--no-llm", action="store_true",
        help="Force mock mode (use expected.pseudo as actual.pseudo)",
    )
    args = p.parse_args(argv)

    cases_dir = Path(args.cases_dir)
    if not cases_dir.is_dir():
        print(f"No such directory: {cases_dir}", file=sys.stderr)
        return 1
    meta_prompt_path = Path(args.meta_prompt)
    if not meta_prompt_path.is_file():
        print(f"No such file: {meta_prompt_path}", file=sys.stderr)
        return 1

    use_llm: Optional[bool] = None
    if args.llm:
        use_llm = True
    if args.no_llm:
        use_llm = False

    cases = _discover_cases(cases_dir)
    if not cases:
        print(f"No cases found in {cases_dir}", file=sys.stderr)
        return 1

    results: list[CaseResult] = []
    for case in cases:
        print(f"--- {case} ---")
        r = run_case(case, cases_dir, meta_prompt_path, use_llm=use_llm)
        results.append(r)
        if r.status in ("OK", "MOCK"):
            print(f"  [{r.status}]")
        else:
            print(f"  [{r.status}]")
            if r.detail:
                for line in r.detail.splitlines():
                    print(f"    {line}")
        if r.actual_path:
            print(f"    wrote {r.actual_path}")

    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    for status, n in sorted(counts.items()):
        print(f"  {status}: {n}")
    print(f"  total: {len(results)}")

    # Exit code: 0 only if all OK/MOCK
    bad = [r for r in results if r.status not in ("OK", "MOCK")]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(_main())
