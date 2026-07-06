"""
claudette/office_writer.py — Stage B' of NoT.

Graph dict -> office.md text (DSL's format).

Pure function: `write_office_md(graph: dict, office_name: str) -> str`.
No file I/O in write_office_md(); the optional CLI wrapper handles files.

See:
  - catalog/translation_table.md for the graph schema.
  - dissyslab/gallery/apps/*/office.md for examples of the target format.

The office.md format (informal grammar):

    # Office: <name>

    Sources: <name>(<args>), <name>(<args>), ...
    Sinks: <name>(<args>), <name>(<args>), ...

    Agents:
    <AgentName> is a <role>(<args>).
    ...

    Connections:
    <source_name>'s destination is <agent>, ...
    <agent>'s <outport> is <agent_or_sink>, ...
    ...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def write_office_md(graph: dict, office_name: str) -> str:
    """Convert a graph dict to office.md text."""
    parts: list[str] = []
    parts.append(f"# Office: {office_name}")
    parts.append("")
    parts.append(_render_sources(graph.get("sources", [])))
    parts.append(_render_sinks(graph.get("sinks", [])))
    parts.append("")
    parts.append("Agents:")
    parts.extend(_render_agents(graph.get("vertices", [])))
    parts.append("")
    parts.append("Connections:")
    parts.extend(_render_connections(graph))
    return "\n".join(parts) + "\n"


# --------------------------------------------------------------------------- #
# Rendering helpers                                                           #
# --------------------------------------------------------------------------- #


def _render_value(v) -> str:
    """Render a single argument value in office.md style."""
    if isinstance(v, str):
        escaped = v.replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, list):
        # Matches DSL's synchronizer(inports=[...]) style — double-quoted items.
        return "[" + ", ".join(_render_value(x) for x in v) + "]"
    return str(v)


def _render_kwargs(params: dict) -> str:
    """Render `k=v, k=v` with strings quoted."""
    if not params:
        return ""
    return ", ".join(f"{k}={_render_value(v)}" for k, v in params.items())


def _render_call(name: str, params: dict) -> str:
    """Render `name` or `name(args)`."""
    if not params:
        return name
    return f"{name}({_render_kwargs(params)})"


def _render_comma_list(label: str, items: list[str]) -> str:
    """Render `<label>: a, b, c` with hanging indent if multi-line."""
    if not items:
        return f"{label}:"
    if len(items) == 1:
        return f"{label}: {items[0]}"
    indent = " " * (len(label) + 2)  # length of "Label: "
    lines = [f"{label}: {items[0]},"]
    for i, item in enumerate(items[1:]):
        sep = "," if i < len(items) - 2 else ""
        lines.append(f"{indent}{item}{sep}")
    return "\n".join(lines)


def _render_sources(sources: list[dict]) -> str:
    calls = [_render_call(s["name"], s.get("params") or {}) for s in sources]
    return _render_comma_list("Sources", calls)


def _render_sinks(sinks: list[dict]) -> str:
    calls = [_render_call(s["name"], s.get("params") or {}) for s in sinks]
    return _render_comma_list("Sinks", calls)


def _agent_name_for(vertex: dict) -> str:
    """Agent name in office.md. Uses the positional ID capitalized.

    Convention: v0 -> V0, v1 -> V1, ..., so the agent name directly
    matches the graph's vertex ID (with a capital). Keeps office.md
    aligned with the canonical graph.yaml.
    """
    vid = vertex["id"]
    if vid.startswith("v"):
        return "V" + vid[1:]
    return vid.upper()


def _is_vowel_start(s: str) -> bool:
    return bool(s) and s[0].lower() in "aeiou"


def _render_agents(vertices: list[dict]) -> list[str]:
    lines: list[str] = []
    for v in vertices:
        name = _agent_name_for(v)
        role = v["role"]
        params = v.get("params") or {}
        article = "an" if _is_vowel_start(role) else "a"
        if params:
            lines.append(f"{name} is {article} {role}({_render_kwargs(params)}).")
        else:
            lines.append(f"{name} is {article} {role}.")
    return lines


def _render_connections(graph: dict) -> list[str]:
    """Render the Connections: section.

    Output order:
      1. Source connections: `<source_name>'s destination is <dest>, ...`
      2. For each vertex in declaration order: one line per outgoing outport,
         `<AgentName>'s <outport> is <dest>, ...`. Multiple targets on the
         same (vertex, outport) merge into one comma-separated line.
    """
    sources = graph.get("sources", [])
    vertices = graph.get("vertices", [])
    sinks = graph.get("sinks", [])
    edges = graph.get("edges", [])

    # Build lookup: any id -> display name used in connections
    display: dict[str, str] = {}
    for s in sources:
        display[s["id"]] = s["name"]
    for v in vertices:
        display[v["id"]] = _agent_name_for(v)
    for k in sinks:
        display[k["id"]] = k["name"]

    # Group edges by (from_id, from_port) → ordered list of destination names
    # Preserve insertion order; dedupe while preserving order.
    from typing import OrderedDict
    from collections import OrderedDict as _OD
    groups: "_OD[tuple[str, str], list[str]]" = _OD()
    for e in edges:
        key = (e["from"][0], e["from"][1])
        dest_name = display.get(e["to"][0], e["to"][0])
        dest_port = e["to"][1]
        # When the destination has a *named* inport (anything other than the
        # default "in_"), render it as `<name>'s <port>` so the DSL parser can
        # route to that inport (e.g. a synchronizer's per-source ports).
        if dest_port and dest_port != "in_":
            dest = f"{dest_name}'s {dest_port}"
        else:
            dest = dest_name
        bucket = groups.setdefault(key, [])
        if dest not in bucket:
            bucket.append(dest)

    out_lines: list[str] = []

    # 1. Source connections
    for s in sources:
        key = (s["id"], "out")
        if key in groups:
            dests = ", ".join(groups[key])
            out_lines.append(f"{s['name']}'s destination is {dests}.")
            del groups[key]

    if any(True for _ in out_lines):
        # blank line between sources and vertices
        out_lines.append("")

    # 2. Vertex connections, in vertex declaration order
    for v in vertices:
        v_lines: list[str] = []
        # Outports for this vertex, in graph-edge declaration order
        for (from_id, from_port), dests in list(groups.items()):
            if from_id == v["id"]:
                vname = display[v["id"]]
                dest_str = ", ".join(dests)
                v_lines.append(f"{vname}'s {from_port} is {dest_str}.")
                del groups[(from_id, from_port)]
        out_lines.extend(v_lines)

    # Strip trailing blank lines
    while out_lines and out_lines[-1] == "":
        out_lines.pop()

    return out_lines


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Convert a graph YAML to a DSL office.md file."
    )
    p.add_argument("input", help="Path to graph YAML (or JSON)")
    p.add_argument("--name", "-n", required=True, help="Office name")
    p.add_argument(
        "--output", "-o",
        help="Path to write office.md (default: stdout)",
    )
    args = p.parse_args(argv)

    text = Path(args.input).read_text()
    try:
        import yaml
        graph = yaml.safe_load(text)
    except ImportError:
        graph = json.loads(text)

    out = write_office_md(graph, args.name)

    if args.output:
        Path(args.output).write_text(out)
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
