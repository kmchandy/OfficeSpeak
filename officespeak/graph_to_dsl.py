"""
officespeak/graph_to_dsl.py — build a DSL runtime Network directly from a
materialized graph.yaml. No office.md parse in the loop.

Position in the chain:

    English  →  asyncio Python  →  graph.yaml (canonical)
                                        ├── materialize → roles/*.py + _impl.py
                                        └── graph_to_dsl → OfficeSpec → Network

The DSL's runtime consumer is the pair::

    spec    : dissyslab.office.OfficeSpec
    library : dissyslab.office.library.Library    (dict[role_name, RoleEntry])

Both are handed to :func:`dissyslab.office.compiler._emit_network` which
walks the spec and produces a live ``dissyslab.network.Network``. The
existing ``compile_office(dir)`` path reaches the same call by first
running ``parse_office_dir(dir)`` to build ``spec`` from ``office.md``.
Here we replace that parse with a direct graph → OfficeSpec mapping.

The mapping is mechanical:

* ``graph.sources[i]``   → ``SourceSpec(name, args)``
* ``graph.sinks[j]``     → ``SinkSpec(name, args)``
* ``graph.vertices[k]``  → ``RoleRef(agent_name, role_name, args)``
    where ``agent_name`` is the vertex's uppercase id (``v0`` → ``V0``)
    and ``role_name`` is the vertex's ``role`` field. Vertex params
    become ``args``.
* ``graph.edges`` → grouped by ``(from_id, from_port)`` into one
    ``ConnectionStmt`` per group. Source-side ports are canonicalised to
    ``"destination"`` when the sender is a ``sources[]`` entry, matching
    what DSL's office.md parser produces.

Known caveats
-------------

* DSL's built-in ``synchronizer`` role has a single ``out`` outport.
  If a graph has a structural synchronizer with multiple outports (a
  common ``asyncio_to_graph`` v1 output when Claude's ``process_one``
  contained a post-merge ``if`` that fanned to different sinks), we
  raise a clear error rather than build a wrong network. The fix
  belongs upstream in ``asyncio_to_graph``: split ``synchronizer`` +
  ``router`` so each vertex has one responsibility.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Optional, Tuple

# DSL imports — these are runtime dependencies of graph_to_dsl.
from dissyslab.office.office_spec import (
    ConnectionStmt,
    Endpoint,
    OfficeSpec,
    RoleRef,
    SinkSpec,
    SourceSpec,
)


# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #


def _args_from_params(params: Optional[dict]) -> Tuple[Tuple[str, Any], ...]:
    """Turn a graph ``params`` dict into a DSL args tuple (key-order-preserving)."""
    if not params:
        return ()
    return tuple((k, v) for k, v in params.items())


def _agent_name_for_vertex(v: dict) -> str:
    """Vertex id → agent name shown in ConnectionStmts.

    ``v0`` becomes ``V0`` (matching the convention office_writer already
    produces, so hand-editors see the same names in either view).
    """
    vid = v["id"]
    if vid.startswith("v") and vid[1:].isdigit():
        return f"V{vid[1:]}"
    return vid.upper()


def _check_synchronizer_outports(v: dict) -> None:
    """Raise if a structural synchronizer has more than one outport.

    DSL's built-in ``synchronizer`` role has a single ``out`` outport.
    Multi-outport synchronizers must be split into a synchronizer +
    downstream router by ``asyncio_to_graph``.
    """
    if v.get("kind") != "structural":
        return
    if v.get("role") != "synchronizer":
        return
    outports = v.get("outports") or ["out"]
    extra = [p for p in outports if p != "out"]
    if extra:
        raise ValueError(
            f"vertex {v.get('id')!r} is a synchronizer with extra outports "
            f"{extra!r}. DSL's built-in synchronizer supports only 'out'. "
            f"Split it into synchronizer + router in asyncio_to_graph."
        )


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def graph_to_office_spec(graph: dict, name: str) -> OfficeSpec:
    """Convert a graph dict into a DSL ``OfficeSpec``.

    Parameters
    ----------
    graph
        A materialized graph (produced by ``officespeak.materialize`` or
        equivalent). Inline vertex bodies are not required at this stage;
        only structure (sources, sinks, vertices with ``role``, edges) is
        consulted. Vertex ``params`` become the ``args`` on the resulting
        ``RoleRef``.
    name
        The office name (used as ``OfficeSpec.name``).

    Returns
    -------
    OfficeSpec
        The DSL-native spec object, ready to hand to ``_emit_network``.
    """
    # --- sources / sinks ---------------------------------------------------
    sources = tuple(
        SourceSpec(name=s["name"], args=_args_from_params(s.get("params")))
        for s in graph.get("sources", [])
    )
    sinks = tuple(
        SinkSpec(name=k["name"], args=_args_from_params(k.get("params")))
        for k in graph.get("sinks", [])
    )

    # --- vertices → RoleRefs and id → display-name map ---------------------
    id_to_name: dict[str, str] = {}
    for s in graph.get("sources", []):
        id_to_name[s["id"]] = s["name"]
    for k in graph.get("sinks", []):
        id_to_name[k["id"]] = k["name"]

    agents_list = []
    for v in graph.get("vertices", []):
        _check_synchronizer_outports(v)
        agent_name = _agent_name_for_vertex(v)
        id_to_name[v["id"]] = agent_name
        agents_list.append(
            RoleRef(
                agent_name=agent_name,
                role_name=v["role"],
                args=_args_from_params(v.get("params")),
            )
        )
    agents = tuple(agents_list)

    # --- edges → ConnectionStmts (grouped by source endpoint) --------------
    # We keep insertion order so the resulting spec's connection order
    # matches the graph's edge order, which matches what a hand-written
    # office.md would produce for the same shape.
    groups: "OrderedDict[Tuple[str, str], Tuple[Endpoint, list[Endpoint]]]"
    groups = OrderedDict()
    source_ids = {s["id"] for s in graph.get("sources", [])}

    for e in graph.get("edges", []):
        from_id, from_port = e["from"]
        to_id, to_port = e["to"]

        # Source-side port canonicalisation: sources emit under the
        # user-facing name "destination" in DSL's office.md convention.
        # Vertices keep whatever outport name the graph declared.
        if from_id in source_ids:
            src_port = "destination"
        else:
            src_port = from_port

        src_endpoint = Endpoint(
            name=id_to_name.get(from_id, from_id),
            port=src_port,
        )
        dst_endpoint = Endpoint(
            name=id_to_name.get(to_id, to_id),
            port=to_port,
        )
        key = (src_endpoint.name, src_endpoint.port)
        if key not in groups:
            groups[key] = (src_endpoint, [])
        groups[key][1].append(dst_endpoint)

    connections = tuple(
        ConnectionStmt(source=src_ep, destinations=tuple(dests))
        for _key, (src_ep, dests) in groups.items()
    )

    return OfficeSpec(
        name=name,
        sources=sources,
        sinks=sinks,
        agents=agents,
        connections=connections,
    )


def compile_graph(
    app_dir: Path,
    library=None,
    name: Optional[str] = None,
) -> Tuple[Any, list]:
    """Load ``app_dir/graph.yaml`` (+ ``roles/``) and compile to a DSL Network.

    Mirror of DSL's ``compile_office(office_dir)`` but uses the graph as
    the source of truth. The ``roles/`` directory is still needed — it's
    where the DSL library loader finds each role's ``AgentRoleEntry``.

    Parameters
    ----------
    app_dir
        Directory containing ``graph.yaml`` (or ``graph.json``) and a
        ``roles/`` subdirectory.
    library
        Optional pre-built ``Library`` mapping role names to entries. If
        ``None``, ``_load_office_library(app_dir)`` is used (built-ins
        plus ``app_dir/roles/``).
    name
        Office name to use in the ``OfficeSpec``. Defaults to
        ``app_dir.name``.

    Returns
    -------
    (Network, list[CompileWarning])
        Same shape as DSL's ``compile_office``.
    """
    from dissyslab.office._internals import _load_office_library
    from dissyslab.office.compiler import _emit_network

    app_dir = Path(app_dir).resolve()

    graph_path = app_dir / "graph.yaml"
    if not graph_path.exists():
        graph_path = app_dir / "graph.json"
    if not graph_path.exists():
        raise FileNotFoundError(
            f"no graph.yaml or graph.json found in {app_dir}"
        )
    graph_text = graph_path.read_text()
    try:
        import yaml
        graph = yaml.safe_load(graph_text)
    except ImportError:
        graph = json.loads(graph_text)

    if name is None:
        name = app_dir.name

    spec = graph_to_office_spec(graph, name)

    if library is None:
        library = _load_office_library(app_dir)

    warnings: list = []
    network = _emit_network(spec, library, app_dir, warnings)
    return network, warnings


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Compile a materialized officespeak app (graph.yaml + roles/) "
            "into a DSL Network. Runs the network unless --dry-run is given."
        )
    )
    p.add_argument("app_dir", help="Directory with graph.yaml and roles/")
    p.add_argument("--name", help="Office name (default: app dir name)")
    p.add_argument(
        "--dry-run", action="store_true",
        help="Build the Network but don't call run_network()."
    )
    args = p.parse_args(argv)

    net, warnings = compile_graph(Path(args.app_dir), name=args.name)
    for w in warnings:
        print(f"  warning: {w}")
    print(
        f"Built network from {args.app_dir}: "
        f"{len(net.agents)} agents, {len(net.connections) if hasattr(net, 'connections') else '?'} connections"
    )
    if args.dry_run:
        return 0
    net.run_network()
    return 0


if __name__ == "__main__":
    sys.exit(_main())
