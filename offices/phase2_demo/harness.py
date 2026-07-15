"""Phase 2 — the general harness: an office description → a runnable Network.

This is the bridge from an OfficeSpeak *office* (what the start module and
phase-1 conversation produce — agents with a kind, and connections written as
4-tuples) to a live DisSysLab ``Network`` you can run. You describe the office
declaratively; the harness picks the right runtime block for each agent's
kind, infers every port from the connections, wires the 4-tuples, and hands
back a Network. No hand-wiring per office.

The office spec
===============

    office = {
        "name": "triage",
        "agents": [
            {"name": "ITEMS",  "kind": "source",    "body": items_feed},
            {"name": "TRIAGE", "kind": "transform", "body": triage_step},
            {"name": "URGENT", "kind": "sink",      "body": urgent.append},
            {"name": "NORMAL", "kind": "sink",      "body": normal.append},
        ],
        "connections": [
            ("ITEMS",  "out_",   "TRIAGE", "in_"),
            ("TRIAGE", "urgent", "URGENT", "in_"),
            ("TRIAGE", "normal", "NORMAL", "in_"),
        ],
    }
    net = build_office(office)
    net.run_network()

One agent dict per agent. ``kind`` is one of:

    source      → Source   — a body ``fn() -> item | None`` (or generator).
    sink        → Sink     — a body ``fn(msg)`` that consumes.
    transform   → Worker   — a body ``step(msg, state) -> [(outbox, msg)]``.
    record      → Worker   — same as transform: a single-inbox keeper. (A
                             record read+written by ONE agent needs no gate;
                             that single inbox serialises access.)
    coordinator → a registered primitive (``merge_synch`` / ``gate`` /
                  ``select``), named by ``"primitive"``. Coordinators are
                  predefined; only ``select`` takes a ``body`` (its
                  next-inbox step). ``merge_synch`` and ``gate`` take none.

Ports are inferred from the connections (an agent's outboxes are the
``from_port``s of edges leaving it, its inboxes the ``to_port``s of edges
entering it), in first-seen order — so ``merge_synch``'s ``in_0`` before
``in_1`` is preserved. Anything the harness cannot infer (a custom join
``combine``, a source ``interval``, a worker's initial ``state``) is passed
as an extra key on the agent dict.

The harness validates the spec and raises a plain-English error if an edge
names an unknown agent, a worker has no body, a coordinator names an unknown
primitive, and so on — so a mistake in a generated office fails loudly at
build time rather than hanging at run time.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from dissyslab.network import Network
from dissyslab.blocks.source import Source
from dissyslab.blocks.sink import Sink
from dissyslab.blocks.merge_synch import MergeSynch
from dissyslab.blocks.gate import Gate
from dissyslab.blocks.select import Select

from worker import Worker


Connection = Tuple[str, str, str, str]

# Coordinator primitives the harness knows → whether each needs a
# Pat/Claude-provided body (a step function). merge_synch and gate are fully
# predefined; select is parameterised by the office's next-inbox logic.
_COORDINATORS = {"merge_synch": False, "gate": False, "select": True}


def _ordered_unique(items: List[str]) -> List[str]:
    seen: Dict[str, None] = {}
    for it in items:
        seen.setdefault(it, None)
    return list(seen)


def _infer_ports(
    connections: List[Connection],
) -> Tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Return (outboxes, inboxes) per agent, in first-seen order."""
    outboxes: Dict[str, List[str]] = {}
    inboxes: Dict[str, List[str]] = {}
    for (fa, fp, ta, tp) in connections:
        outboxes.setdefault(fa, []).append(fp)
        inboxes.setdefault(ta, []).append(tp)
    return (
        {a: _ordered_unique(ps) for a, ps in outboxes.items()},
        {a: _ordered_unique(ps) for a, ps in inboxes.items()},
    )


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(f"build_office: {msg}")


def build_office(office: Dict[str, Any]) -> Network:
    """Assemble a runnable ``Network`` from an office description.

    See the module docstring for the spec. Raises ``ValueError`` with a
    plain-English message if the spec is inconsistent.
    """
    name = office.get("name", "office")
    agents = office.get("agents")
    connections = [tuple(c) for c in office.get("connections", [])]
    _require(isinstance(agents, list) and agents, "office needs a non-empty 'agents' list")
    for c in connections:
        _require(len(c) == 4, f"each connection must be a 4-tuple (from, out, to, in); got {c!r}")

    by_name = {}
    for a in agents:
        _require("name" in a and "kind" in a, f"each agent needs 'name' and 'kind'; got {a!r}")
        _require(a["name"] not in by_name, f"duplicate agent name {a['name']!r}")
        by_name[a["name"]] = a

    # Every connection must reference declared agents.
    for (fa, fp, ta, tp) in connections:
        _require(fa in by_name, f"connection names unknown sender {fa!r}")
        _require(ta in by_name, f"connection names unknown receiver {ta!r}")

    outboxes, inboxes = _infer_ports(connections)

    blocks: Dict[str, Any] = {}
    for a in agents:
        nm, kind = a["name"], a["kind"]
        outs = outboxes.get(nm, [])
        ins = inboxes.get(nm, [])

        if kind == "source":
            _require("body" in a, f"source {nm!r} needs a 'body' fn")
            blocks[nm] = Source(fn=a["body"], name=nm,
                                interval=a.get("interval", 0.0),
                                state=a.get("state"))

        elif kind == "sink":
            _require("body" in a, f"sink {nm!r} needs a 'body' fn")
            blocks[nm] = Sink(fn=a["body"], name=nm, state=a.get("state"))

        elif kind in ("transform", "record"):
            _require("body" in a, f"{kind} {nm!r} needs a 'body' step(msg, state)")
            _require(len(ins) <= 1,
                     f"{kind} {nm!r} has {len(ins)} inboxes {ins}; a "
                     f"{kind} has exactly one (fan-in is many senders into "
                     f"the SAME inbox, still one inbox)")
            inport = ins[0] if ins else "in_"
            blocks[nm] = Worker(step=a["body"], outports=outs, name=nm,
                                state=a.get("state"), inport=inport)

        elif kind == "coordinator":
            prim = a.get("primitive")
            _require(prim in _COORDINATORS,
                     f"coordinator {nm!r} needs 'primitive' in "
                     f"{sorted(_COORDINATORS)}; got {prim!r}")
            in_order = a.get("inboxes", ins)
            if prim == "merge_synch":
                blocks[nm] = MergeSynch(inports=in_order,
                                        combine=a.get("combine"), name=nm)
            elif prim == "gate":
                blocks[nm] = Gate(name=nm,
                                  in_port=a.get("data_port", "in_"),
                                  done_port=a.get("done_port", "done"),
                                  out_port=a.get("out_port", "out_"))
            elif prim == "select":
                _require("body" in a, f"select {nm!r} needs a 'body' step(msg, state, inport)")
                blocks[nm] = Select(inports=in_order, outports=outs or None,
                                    fn=a["body"], name=nm,
                                    state=a.get("state"), start=a.get("start"))
        else:
            _require(False, f"agent {nm!r} has unknown kind {kind!r} "
                            f"(source|sink|transform|record|coordinator)")

    return Network(name=name, blocks=blocks, connections=connections)
