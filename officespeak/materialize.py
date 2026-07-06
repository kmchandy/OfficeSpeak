"""
officespeak/materialize.py — split a graph's inline vertex bodies into a
DSL-loadable ``roles/`` directory.

The pipeline is:

    English spec
        ↓  (Claude)
    asyncio Python
        ↓  (officespeak.asyncio_to_graph)
    graph.yaml with inline ``source_code`` / ``role_prompt`` on each vertex
        ↓  (this module)
    <app_dir>/graph.yaml   ← same structure, but each non-structural
                              vertex carries ``role_file: "roles/<name>.py"``
                              instead of the inline body
    <app_dir>/roles/_impl.py         ← Claude's original module verbatim,
                                       minus the OfficeSpeak-owned bits
                                       (``main``, ``process_one``, ``send_to``,
                                       and the ``__main__`` guard).
    <app_dir>/roles/<name>.py        ← a thin ``AgentRoleEntry`` wrapper per
                                       LLM or python_stateful vertex.

Design (2026-06-30, "Option A"):

* Every non-structural vertex becomes a **Python role**. LLM vertices
  are Python roles that just happen to call an LLM inside their ``run()``
  loop, using Claude's original fstring prompt verbatim. This avoids the
  impedance mismatch between DSL's ``nl_role`` prompt-contract envelope
  and asyncio's raw fstring prompts.
* Structural vertices (currently only ``synchronizer``) are provided by
  DSL's built-in library. They get no local file.
* graph.yaml stays canonical; ``roles/`` is derived. Re-running
  ``materialize()`` should overwrite the ``roles/`` tree without loss.

Public API
----------

``materialize(graph, python_source, out_dir)``
    Given the graph dict (with inline bodies) plus the original asyncio
    Python source, write ``<out_dir>/graph.yaml`` and
    ``<out_dir>/roles/*.py`` and return the updated graph dict.

CLI usage
---------

    python -m officespeak.materialize digest.py graph.yaml out/
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Optional

# Function / block names at the top of Claude's asyncio module that
# OfficeSpeak owns rather than translates. These are dropped from
# ``roles/_impl.py`` so Claude's Python is decoupled from OfficeSpeak's
# runtime concerns.
_OFFICESPEAK_OWNED_TOP_LEVEL_NAMES = {
    "main",         # process-driver — OfficeSpeak provides one
    "process_one",  # per-item pipeline — encoded as the graph itself
    "send_to",      # sink dispatch — DSL sinks handle this
}


# --------------------------------------------------------------------------- #
# Role-name / class-name helpers                                              #
# --------------------------------------------------------------------------- #


def _pascal(role: str) -> str:
    """Convert ``severity_classifier`` → ``SeverityClassifier``."""
    return "".join(p.capitalize() for p in re.split(r"[_\W]+", role) if p)


# --------------------------------------------------------------------------- #
# _impl.py — Claude's original module minus OfficeSpeak-owned bits            #
# --------------------------------------------------------------------------- #


def _strip_officespeak_owned(python_source: str) -> str:
    """Remove ``main``, ``process_one``, ``send_to``, and the ``__main__``
    guard from Claude's asyncio module. Everything else — imports, module
    docstring, module constants like ``SOURCES``, private helpers like
    ``_ask_json``, ``_clean``, ``_extract_json``, plus the vertex
    functions and classes — is kept verbatim.

    Preserves the surrounding text (comments, blank lines, formatting)
    by slicing the source string on line boundaries.
    """
    tree = ast.parse(python_source)
    lines = python_source.splitlines(keepends=True)
    # Build a set of line ranges to drop.
    drop_ranges: list[tuple[int, int]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                node.name in _OFFICESPEAK_OWNED_TOP_LEVEL_NAMES:
            drop_ranges.append((node.lineno, node.end_lineno))
        elif isinstance(node, ast.If) and _is_main_guard(node):
            drop_ranges.append((node.lineno, node.end_lineno))
        elif isinstance(node, ast.Assign) and _is_sources_assign(node):
            # SOURCES is an OfficeSpeak source declaration, not runtime
            # Python — its entries (e.g. ``audio_clip(...)``) are not real
            # symbols. It is encoded into the graph's ``sources`` list, so
            # drop it from _impl.py to avoid a NameError at import.
            drop_ranges.append((node.lineno, node.end_lineno))
    # Also drop the immediately-preceding ``# ---`` banner comment if
    # present, so the output doesn't have orphan headers. The banners
    # in Claude's Run 2 output look like:
    #     # --------------------------- #
    #     # Driver
    #     # --------------------------- #
    # A banner is a run of 1–3 consecutive comment-only lines directly
    # above the dropped block, separated only by blank lines.
    expanded: list[tuple[int, int]] = []
    for start, end in drop_ranges:
        s = start
        # Walk back over blank + comment lines to swallow a banner header.
        i = s - 2  # -1 for zero-based, another -1 to look above
        while i >= 0:
            stripped = lines[i].strip()
            if stripped == "" or stripped.startswith("#"):
                s = i + 1
                i -= 1
            else:
                break
        expanded.append((s, end))
    # Sort and merge.
    expanded.sort()
    kept: list[str] = []
    cursor = 1
    for start, end in expanded:
        if start > cursor:
            kept.extend(lines[cursor - 1 : start - 1])
        cursor = end + 1
    if cursor <= len(lines):
        kept.extend(lines[cursor - 1 :])
    text = "".join(kept)
    # Trim redundant blank runs left behind by the excisions.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.rstrip() + "\n"


def _is_sources_assign(node: ast.Assign) -> bool:
    """Detect a module-level ``SOURCES = {...}`` assignment."""
    return (len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "SOURCES")


def _hoist_future_imports(text: str) -> str:
    """Move any ``from __future__`` imports to the top of ``text``.

    A future statement must appear before any other code. When Claude's
    module carries ``from __future__ import annotations`` (common), the
    ``_impl.py`` header docstring pushes it down and Python rejects it.
    We pull every module-level future import out and re-emit them right
    after the (single) leading docstring, before anything else.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text
    lines = text.splitlines(keepends=True)
    future_line_ranges: list[tuple[int, int]] = []
    future_stmts: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            future_line_ranges.append((node.lineno, node.end_lineno))
            future_stmts.append(ast.unparse(node))
    if not future_stmts:
        return text

    # Drop the future imports from their original positions.
    drop: set[int] = set()
    for start, end in future_line_ranges:
        drop.update(range(start, end + 1))
    body = "".join(
        ln for i, ln in enumerate(lines, start=1) if i not in drop
    )

    # Re-emit them after a leading module docstring, if present.
    body_tree = ast.parse(body)
    insert_at = 0
    if (body_tree.body
            and isinstance(body_tree.body[0], ast.Expr)
            and isinstance(body_tree.body[0].value, ast.Constant)
            and isinstance(body_tree.body[0].value.value, str)):
        insert_at = body_tree.body[0].end_lineno

    body_lines = body.splitlines(keepends=True)
    head = "".join(body_lines[:insert_at])
    tail = "".join(body_lines[insert_at:])
    future_block = "\n".join(future_stmts) + "\n"
    joined = head
    if head and not head.endswith("\n"):
        joined += "\n"
    joined += future_block + "\n" + tail.lstrip("\n")
    return re.sub(r"\n{3,}", "\n\n", joined)


def _is_main_guard(node: ast.If) -> bool:
    """Detect ``if __name__ == "__main__":`` blocks."""
    t = node.test
    if not isinstance(t, ast.Compare) or len(t.ops) != 1:
        return False
    if not isinstance(t.ops[0], ast.Eq):
        return False
    left = t.left
    right = t.comparators[0]
    return (
        (isinstance(left, ast.Name) and left.id == "__name__"
         and isinstance(right, ast.Constant) and right.value == "__main__")
        or
        (isinstance(right, ast.Name) and right.id == "__name__"
         and isinstance(left, ast.Constant) and left.value == "__main__")
    )


# --------------------------------------------------------------------------- #
# Wrapper templates                                                           #
# --------------------------------------------------------------------------- #


_IMPL_HEADER = '''\
"""
_impl.py — Claude's original asyncio module, kept verbatim minus the
OfficeSpeak-owned top-level bits (``main``, ``process_one``, ``send_to``,
and the ``__main__`` guard). Auto-generated by officespeak.materialize.

Underscore-prefixed files are ignored by DSL's ``load_roles_dir``, so this
module is available for the sibling ``roles/<name>.py`` wrappers to import
without being registered as a role itself.
"""

'''


_ROLE_HEADER = '''\
"""
{role} — auto-generated by officespeak.materialize.

Wraps ``_impl.{impl_symbol}`` ({kind}) as a DSL Agent so it can be
loaded by ``load_roles_dir`` and wired into a runtime Network.
"""

from __future__ import annotations

import sys
from pathlib import Path

# The wrapper needs to import ``_impl`` from the same ``roles/`` dir.
# ``load_roles_dir`` imports each role by file path without adding its
# parent to sys.path, so we do it ourselves before the import.
_ROLES_DIR = Path(__file__).parent
if str(_ROLES_DIR) not in sys.path:
    sys.path.insert(0, str(_ROLES_DIR))

import _impl  # noqa: E402

from dissyslab.core import Agent  # noqa: E402
from dissyslab.office.library import AgentRoleEntry  # noqa: E402

'''


_LLM_BODY = '''\

import asyncio


class _{PascalRole}Agent(Agent):
    """DSL agent wrapping the async LLM function ``_impl.{func_name}``."""

    def __init__(self, name: str | None = None, **kwargs):
        # kwargs from office.md / graph.yaml are accepted but ignored;
        # LLM roles don't currently take runtime configuration.
        super().__init__(name=name, inports=["in_"], outports=["out_"])

    def run(self) -> None:
        while True:
            msg = self.recv("in_")
            try:
                result = asyncio.run(_impl.{func_name}(msg))
            except Exception as exc:
                print(
                    f"[{{self.name}}] {func_name} failed: {{exc}}",
                    file=sys.stderr,
                )
                continue
            if result is None:
                continue
            if isinstance(msg, dict) and isinstance(result, dict):
                out = {{**msg, **result}}
            else:
                out = result
            self.send(out, "out_")


role = AgentRoleEntry(
    name="{role}",
    in_ports=("in_",),
    out_ports=("out",),
    factory=_{PascalRole}Agent,
)
'''


_PY_STATEFUL_BODY = '''\


class _{PascalRole}Agent(Agent):
    """DSL agent wrapping the stateful Python class ``_impl.{class_name}``."""

    def __init__(self, name: str | None = None, **kwargs):
        super().__init__(name=name, inports=["in_"], outports=["out_"])
        self._impl = _impl.{class_name}(**kwargs)

    def run(self) -> None:
        while True:
            msg = self.recv("in_")
            try:
                result = self._impl.process(msg)
            except Exception as exc:
                print(
                    f"[{{self.name}}] {class_name}.process failed: {{exc}}",
                    file=sys.stderr,
                )
                continue
            if result is None:
                continue
            self.send(result, "out_")


role = AgentRoleEntry(
    name="{role}",
    in_ports=("in_",),
    out_ports=("out",),
    factory=_{PascalRole}Agent,
)
'''


_SOURCE_RSS_BODY = '''\
"""
{name} — app-local RSS source, auto-generated by officespeak.materialize.

The graph references this feed by the unique block name ``{name}``.
Emitting one module per feed (rather than DSL's single generic ``rss``
component) lets an app read several distinct RSS feeds without their
block names colliding — the same idea as the framework's built-in
``bbc_world`` / ``npr_news`` factories, but for an arbitrary URL.

Discovered by DSL's app-local source loader, exactly like ``roles/``
files. The loader calls ``build_source()`` and wraps the returned
object in a runtime ``Source`` named after this file.
"""

from __future__ import annotations

from dissyslab.components.sources.rss_normalizer import RSSNormalizer

URL = {url!r}


def build_source() -> RSSNormalizer:
    """Return the feed reader for ``{name}``. DSL wraps it in a Source."""
    return RSSNormalizer(url=URL, name={name!r})
'''


def _render_rss_source(name: str, url: str) -> str:
    return _SOURCE_RSS_BODY.format(name=name, url=url)


def _render_llm_role(role: str, func_name: str) -> str:
    header = _ROLE_HEADER.format(
        role=role,
        impl_symbol=func_name,
        kind="an async LLM function",
    )
    body = _LLM_BODY.format(
        PascalRole=_pascal(role),
        func_name=func_name,
        role=role,
    )
    return header + body


def _render_py_stateful_role(role: str, class_name: str) -> str:
    header = _ROLE_HEADER.format(
        role=role,
        impl_symbol=class_name,
        kind="a Python stateful class",
    )
    body = _PY_STATEFUL_BODY.format(
        PascalRole=_pascal(role),
        class_name=class_name,
        role=role,
    )
    return header + body


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def materialize(
    graph: dict,
    python_source: str,
    out_dir: Path,
) -> dict:
    """Write ``<out_dir>/graph.yaml`` and ``<out_dir>/roles/*.py`` from a
    graph with inline vertex bodies.

    Parameters
    ----------
    graph
        The graph dict produced by ``officespeak.asyncio_to_graph.parse``.
        Vertices carry inline ``role_prompt`` / ``source_code`` /
        ``class_name`` on entry; they are replaced with ``role_file``
        pointers on exit.
    python_source
        Claude's original asyncio Python source. Everything above the
        vertex definitions (imports, module constants, private helpers,
        docstring) plus the vertex definitions themselves are written
        verbatim to ``roles/_impl.py``. Only OfficeSpeak-owned top-level
        bits (``main``, ``process_one``, ``send_to``, and the
        ``if __name__ == "__main__"`` guard) are excised.
    out_dir
        Target directory. Created if needed.

    Returns
    -------
    dict
        The updated graph, with ``role_file`` pointers on non-structural
        vertices and inline body fields removed.
    """
    out_dir = Path(out_dir)
    roles_dir = out_dir / "roles"
    roles_dir.mkdir(parents=True, exist_ok=True)

    # 1. Emit roles/_impl.py — Claude's module minus OfficeSpeak-owned bits.
    #    Hoist any `from __future__` imports above the injected header so
    #    they remain the first statements Python sees.
    impl_text = _hoist_future_imports(
        _IMPL_HEADER + _strip_officespeak_owned(python_source)
    )
    (roles_dir / "_impl.py").write_text(impl_text)

    # 2. Emit one roles/<name>.py per non-structural vertex, and rewrite
    #    each vertex in the returned graph to reference its role file.
    new_vertices: list[dict] = []
    for v in graph.get("vertices", []):
        role = v["role"]
        kind = v.get("kind", "")
        if kind == "llm":
            (roles_dir / f"{role}.py").write_text(
                _render_llm_role(role, func_name=role)
            )
            new_v = {k: val for k, val in v.items()
                     if k not in ("role_prompt", "source_code")}
            new_v["role_file"] = f"roles/{role}.py"
            new_vertices.append(new_v)
        elif kind == "python_stateful":
            class_name = v.get("class_name") or _pascal(role)
            (roles_dir / f"{role}.py").write_text(
                _render_py_stateful_role(role, class_name=class_name)
            )
            new_v = {k: val for k, val in v.items()
                     if k not in ("role_prompt", "source_code")}
            new_v["role_file"] = f"roles/{role}.py"
            new_vertices.append(new_v)
        elif kind == "structural":
            # DSL's built-in library provides these (e.g. ``synchronizer``).
            # No local file; the role_name in the graph is enough for
            # graph_to_dsl to resolve it.
            new_v = {k: val for k, val in v.items()
                     if k not in ("role_prompt", "source_code")}
            new_vertices.append(new_v)
        else:
            raise ValueError(
                f"materialize: unknown vertex kind {kind!r} on vertex "
                f"{v.get('id')!r}"
            )

    new_graph = dict(graph)
    new_graph["vertices"] = new_vertices

    # 2b. Emit one sources/<name>.py per generic-URL feed. A source that
    #     carries a ``url`` param came from a bare URL string in Claude's
    #     ``SOURCES`` dict (e.g. ``"bbc": "https://..."``). DSL's registry
    #     has no entry for such a name, and its single generic ``rss``
    #     component can't host several feeds without a block-name clash.
    #     So we give each feed its own app-local module, discovered the
    #     same way ``roles/`` are. Sources that reference a framework
    #     factory by name (no ``url`` param) are left untouched.
    sources_dir = out_dir / "sources"
    for s in graph.get("sources", []):
        params = s.get("params") or {}
        url = params.get("url")
        if not url:
            continue
        sources_dir.mkdir(parents=True, exist_ok=True)
        (sources_dir / f"{s['name']}.py").write_text(
            _render_rss_source(s["name"], url)
        )

    # 3. Write graph.yaml (YAML if pyyaml is available, else JSON).
    try:
        import yaml
        (out_dir / "graph.yaml").write_text(
            yaml.safe_dump(new_graph, sort_keys=False, allow_unicode=True)
        )
    except ImportError:
        (out_dir / "graph.json").write_text(
            json.dumps(new_graph, indent=2)
        )

    return new_graph


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Materialize a graph.yaml with inline bodies into a DSL-loadable "
            "app dir (graph.yaml + roles/_impl.py + roles/<name>.py)."
        )
    )
    p.add_argument("python_source", help="Claude's asyncio Python file")
    p.add_argument(
        "--from-source", action="store_true",
        help=(
            "Skip an explicit graph.yaml and run asyncio_to_graph on the "
            "Python file first (equivalent to the common one-shot case)."
        ),
    )
    p.add_argument(
        "--graph", help="Path to graph.yaml (required unless --from-source)"
    )
    p.add_argument(
        "--out", "-o", required=True, help="Target app directory"
    )
    args = p.parse_args(argv)

    python_source = Path(args.python_source).read_text()

    if args.from_source:
        from officespeak.asyncio_to_graph import parse
        graph, _warnings = parse(python_source)
    else:
        if not args.graph:
            p.error("--graph is required unless --from-source is given")
        graph_text = Path(args.graph).read_text()
        try:
            import yaml
            graph = yaml.safe_load(graph_text)
        except ImportError:
            graph = json.loads(graph_text)

    new_graph = materialize(graph, python_source, Path(args.out))
    print(
        f"Wrote {args.out}/graph.yaml and "
        f"{len(new_graph.get('vertices', []))} role files under "
        f"{args.out}/roles/"
    )
    return 0


if __name__ == "__main__":
    sys.exit(_main())
