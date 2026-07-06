"""
officespeak/graph_viz.py — draw a graph.yaml so a human can see it.

A materialized ``graph.yaml`` lists sources, vertices, sinks, and edges,
but reading the edge list by hand is hard. This module renders the same
graph as a picture: nodes for each source / agent / synchronizer /
router / sink, and arrows for each edge, labelled with any non-default
port names (a synchronizer inport like ``severity``, a router outport
like ``critical``).

Three output formats, same graph:

* ``mermaid`` (default) — a Mermaid ``flowchart`` string. Save it as a
  ``.mermaid`` file to see it rendered, or paste it into any Mermaid
  viewer. Best for a quick visual.
* ``dot`` — Graphviz DOT, for ``dot -Tpng graph.dot -o graph.png``.
* ``text`` — a plain-text node list + arrow list, no tools required.

Public API
----------

``render(graph, fmt="mermaid") -> str``
    Render a graph dict (as produced by ``asyncio_to_graph`` /
    ``materialize``) to the chosen format.

``render_file(path, fmt="mermaid") -> str``
    Load ``path`` (graph.yaml or graph.json) and render it.

CLI
---

    python -m officespeak.graph_viz app/graph.yaml
    python -m officespeak.graph_viz app/graph.yaml --format dot -o graph.dot
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Port names that carry no information (the framework defaults). Edges
# whose ports are all defaults are drawn without a label.
_DEFAULT_OUT_PORTS = {"out", "out_", "destination", ""}
_DEFAULT_IN_PORTS = {"in_", "in", ""}


# --------------------------------------------------------------------------- #
# Graph indexing                                                              #
# --------------------------------------------------------------------------- #


def _index(graph: dict) -> dict:
    """Map every node id to ``(category, node_dict)``.

    ``category`` is one of ``"source"``, ``"vertex"``, ``"sink"``.
    """
    idx: dict = {}
    for s in graph.get("sources", []):
        idx[s["id"]] = ("source", s)
    for v in graph.get("vertices", []):
        idx[v["id"]] = ("vertex", v)
    for k in graph.get("sinks", []):
        idx[k["id"]] = ("sink", k)
    return idx


def _node_label(node_id: str, idx: dict) -> str:
    """Human-readable label for a node id."""
    entry = idx.get(node_id)
    if entry is None:
        return node_id
    category, node = entry
    if category == "source":
        return str(node.get("name", node_id))
    if category == "sink":
        return str(node.get("name", node_id))
    # vertex
    return f"{node_id}: {node.get('role', '?')}"


def _node_kind(node_id: str, idx: dict) -> str:
    """A drawing category: source, sink, sync, router, or agent."""
    entry = idx.get(node_id)
    if entry is None:
        return "agent"
    category, node = entry
    if category == "source":
        return "source"
    if category == "sink":
        return "sink"
    role = node.get("role")
    if role == "synchronizer":
        return "sync"
    if role == "router":
        return "router"
    return "agent"


def _edge_label(from_port: str, to_port: str) -> str:
    """Label an edge with whatever ports are non-default."""
    parts = []
    if from_port not in _DEFAULT_OUT_PORTS:
        parts.append(str(from_port))
    if to_port not in _DEFAULT_IN_PORTS:
        parts.append(str(to_port))
    return " ▸ ".join(parts)


def _iter_edges(graph: dict):
    """Yield ``(from_id, from_port, to_id, to_port)`` for each edge."""
    for e in graph.get("edges", []):
        frm = e.get("from", [None, ""])
        to = e.get("to", [None, ""])
        yield frm[0], (frm[1] if len(frm) > 1 else ""), to[0], (
            to[1] if len(to) > 1 else ""
        )


# --------------------------------------------------------------------------- #
# Mermaid                                                                     #
# --------------------------------------------------------------------------- #

# Node shapes per kind, as (prefix, suffix) around the quoted label.
_MERMAID_SHAPES = {
    "source": ("([", "])"),   # stadium
    "sink":   ("[(", ")]"),   # cylinder
    "sync":   ("{{", "}}"),   # hexagon
    "router": ("{", "}"),     # rhombus / decision
    "agent":  ("[", "]"),     # rectangle
}

_MERMAID_CLASSDEFS = [
    "classDef source fill:#e3f2fd,stroke:#1565c0,color:#0d47a1;",
    "classDef sink fill:#ede7f6,stroke:#5e35b1,color:#311b92;",
    "classDef sync fill:#fff3e0,stroke:#ef6c00,color:#e65100;",
    "classDef router fill:#fce4ec,stroke:#c2185b,color:#880e4f;",
    "classDef agent fill:#e8f5e9,stroke:#2e7d32,color:#1b5e20;",
]


def to_mermaid(graph: dict) -> str:
    """Render ``graph`` as a Mermaid ``flowchart TD`` string."""
    idx = _index(graph)
    lines = ["flowchart TD"]

    # Declare every node once, in a stable order (sources, vertices, sinks).
    for node_id in idx:
        kind = _node_kind(node_id, idx)
        pre, suf = _MERMAID_SHAPES.get(kind, ("[", "]"))
        label = _node_label(node_id, idx).replace('"', "'")
        lines.append(f'    {node_id}{pre}"{label}"{suf}:::{kind}')

    lines.append("")
    for from_id, from_port, to_id, to_port in _iter_edges(graph):
        label = _edge_label(from_port, to_port)
        if label:
            lines.append(f"    {from_id} -->|{label}| {to_id}")
        else:
            lines.append(f"    {from_id} --> {to_id}")

    lines.append("")
    lines.extend("    " + cd for cd in _MERMAID_CLASSDEFS)
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Self-contained HTML                                                         #
# --------------------------------------------------------------------------- #


_HTML_TEMPLATE = '''\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font-family: -apple-system, Helvetica, Arial, sans-serif;
         margin: 2rem; color: #1b1b1b; }}
  h1 {{ font-size: 1.1rem; font-weight: 600; color: #444; }}
  .diagram {{ display: flex; justify-content: center; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="diagram">
<pre class="mermaid">
{mermaid}
</pre>
</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{ startOnLoad: true, securityLevel: "loose" }});</script>
</body>
</html>
'''


def to_html(graph: dict, title: str = "graph") -> str:
    """Render ``graph`` as a self-contained HTML page.

    The page embeds the Mermaid source and loads Mermaid from a CDN, so
    it renders as a picture in any browser with nothing to install —
    just open the file. Keep the ``.mermaid`` output for version
    control; use this to look at the graph.
    """
    return _HTML_TEMPLATE.format(title=title, mermaid=to_mermaid(graph))


# --------------------------------------------------------------------------- #
# Graphviz DOT                                                                #
# --------------------------------------------------------------------------- #

_DOT_SHAPES = {
    "source": ("stadium", "#e3f2fd"),
    "sink":   ("cylinder", "#ede7f6"),
    "sync":   ("hexagon", "#fff3e0"),
    "router": ("diamond", "#fce4ec"),
    "agent":  ("box", "#e8f5e9"),
}


def to_dot(graph: dict) -> str:
    """Render ``graph`` as Graphviz DOT."""
    idx = _index(graph)
    lines = ["digraph office {", "    rankdir=TB;",
             '    node [style="filled,rounded", fontname="Helvetica"];']
    for node_id in idx:
        kind = _node_kind(node_id, idx)
        shape, fill = _DOT_SHAPES.get(kind, ("box", "#ffffff"))
        label = _node_label(node_id, idx).replace('"', r"\"")
        lines.append(
            f'    "{node_id}" [label="{label}", shape={shape}, '
            f'fillcolor="{fill}"];'
        )
    for from_id, from_port, to_id, to_port in _iter_edges(graph):
        label = _edge_label(from_port, to_port).replace("▸", "->")
        attr = f' [label="{label}"]' if label else ""
        lines.append(f'    "{from_id}" -> "{to_id}"{attr};')
    lines.append("}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- #
# Plain text                                                                  #
# --------------------------------------------------------------------------- #


def to_text(graph: dict) -> str:
    """Render ``graph`` as a plain-text node list and arrow list."""
    idx = _index(graph)
    out = []

    out.append("Sources:")
    for s in graph.get("sources", []):
        out.append(f"  {s['id']:<4} {s.get('name', '?')}")
    out.append("")

    out.append("Agents:")
    for v in graph.get("vertices", []):
        kind = _node_kind(v["id"], idx)
        tag = {"sync": " (synchronizer)", "router": " (router)"}.get(kind, "")
        out.append(f"  {v['id']:<4} {v.get('role', '?')}{tag}")
    out.append("")

    out.append("Sinks:")
    for k in graph.get("sinks", []):
        out.append(f"  {k['id']:<4} {k.get('name', '?')}")
    out.append("")

    out.append("Edges:")
    for from_id, from_port, to_id, to_port in _iter_edges(graph):
        label = _edge_label(from_port, to_port)
        arrow = f" --{label}-->" if label else " -->"
        out.append(
            f"  {_node_label(from_id, idx)}{arrow} {_node_label(to_id, idx)}"
        )
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# Dispatch + file loading                                                     #
# --------------------------------------------------------------------------- #

_FORMATS = ("mermaid", "html", "dot", "text")


def render(graph: dict, fmt: str = "mermaid", *, title: str = "graph") -> str:
    """Render a graph dict to ``fmt``.

    ``fmt`` is one of ``mermaid``, ``html``, ``dot``, ``text``. ``title``
    is used only by the ``html`` page header.
    """
    if fmt == "mermaid":
        return to_mermaid(graph)
    if fmt == "html":
        return to_html(graph, title=title)
    if fmt == "dot":
        return to_dot(graph)
    if fmt == "text":
        return to_text(graph)
    raise ValueError(f"unknown format {fmt!r}; choose from {list(_FORMATS)}")


def _load_graph(path: Path) -> dict:
    text = path.read_text()
    try:
        import yaml
        return yaml.safe_load(text)
    except ImportError:
        return json.loads(text)


def render_file(path, fmt: str = "mermaid") -> str:
    """Load a graph.yaml / graph.json file and render it to ``fmt``.

    The HTML page title defaults to the graph's app-directory name.
    """
    path = Path(path)
    title = path.parent.name or path.stem
    return render(_load_graph(path), fmt, title=title)


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _main(argv: Optional[list] = None) -> int:
    p = argparse.ArgumentParser(
        description="Draw a graph.yaml as a diagram (mermaid / dot / text).",
    )
    p.add_argument("graph", help="Path to graph.yaml or graph.json")
    p.add_argument(
        "--format", "-f", default="mermaid",
        choices=list(_FORMATS),
        help="Output format (default: mermaid)",
    )
    p.add_argument(
        "--output", "-o",
        help="Write to this file instead of stdout",
    )
    args = p.parse_args(argv)

    rendered = render_file(args.graph, args.format)
    if args.output:
        Path(args.output).write_text(rendered)
        print(f"Wrote {args.format} diagram to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
