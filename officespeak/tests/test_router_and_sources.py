"""
Regression tests for the synchronizer/router split (#189) and the
app-local source emission for generic-URL feeds (#190).

#189 — a post-merge conditional (`if enriched[...] == "...": send_to(...)`)
must NOT add an extra outport to the fan-in synchronizer (DSL's
synchronizer has a single `out`). It must instead route through a
dedicated `router` vertex.

#190 — a source declared as a bare URL string in `SOURCES` (e.g.
`"bbc": "https://..."`) must materialize an app-local `sources/<name>.py`
module so several distinct feeds don't collide on DSL's single generic
`rss` component.
"""

from __future__ import annotations

from pathlib import Path

from officespeak.asyncio_to_graph import parse
from officespeak.materialize import materialize


# --------------------------------------------------------------------------- #
# Shared fixture: a minimal situation-room-shaped OfficeSpeak module           #
# --------------------------------------------------------------------------- #

_SRC = '''
import asyncio

SOURCES = {
    "bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "npr": "https://feeds.npr.org/1004/rss.xml",
}


async def classify_severity(message):
    """Rate severity."""
    return {"severity": "low"}


async def write_briefing(message):
    """Write a briefing."""
    return {"briefing": "..."}


async def process_one(message):
    """Enrich then route."""
    severity, briefing = await asyncio.gather(
        classify_severity(message),
        write_briefing(message),
    )
    enriched = {**message, **severity, **briefing}
    send_to(enriched, "jsonl", path="digest.jsonl")
    if enriched.get("severity") == "critical":
        send_to(enriched, "terminal")
    return enriched


async def main():
    pass
'''


def _vertex_by_role(graph, role):
    return [v for v in graph["vertices"] if v["role"] == role]


# --------------------------------------------------------------------------- #
# #189 — synchronizer/router split                                            #
# --------------------------------------------------------------------------- #


def test_synchronizer_has_single_out_port():
    graph, _ = parse(_SRC)
    syncs = _vertex_by_role(graph, "synchronizer")
    assert len(syncs) == 1
    sync = syncs[0]
    # No extra outports were grafted onto the synchronizer.
    extra = [p for p in (sync.get("outports") or ["out"]) if p != "out"]
    assert extra == [], f"synchronizer gained extra outports: {extra}"


def test_conditional_send_creates_router_vertex():
    graph, _ = parse(_SRC)
    routers = _vertex_by_role(graph, "router")
    assert len(routers) == 1
    router = routers[0]
    assert router["kind"] == "structural"
    routes = router["params"]["routes"]
    assert routes == [
        {"outport": "critical", "field": "severity", "equals": "critical"}
    ]


def test_router_is_wired_between_synchronizer_and_sink():
    graph, _ = parse(_SRC)
    sync = _vertex_by_role(graph, "synchronizer")[0]["id"]
    router = _vertex_by_role(graph, "router")[0]["id"]

    def has_edge(frm, to):
        return any(e["from"] == frm and e["to"] == to for e in graph["edges"])

    # synchronizer feeds the router on its single out port
    assert has_edge([sync, "out"], [router, "in_"])
    # the conditional branch leaves the router (not the synchronizer)
    critical_edges = [
        e for e in graph["edges"] if e["from"] == [router, "critical"]
    ]
    assert len(critical_edges) == 1
    # the unconditional send still leaves the synchronizer directly
    assert any(
        e["from"] == [sync, "out"] and e["to"][0] != router
        for e in graph["edges"]
    )


def test_no_unrecognised_statement_warnings():
    _, warnings = parse(_SRC)
    assert warnings == []


# --------------------------------------------------------------------------- #
# #190 — app-local source emission                                            #
# --------------------------------------------------------------------------- #


def test_materialize_emits_app_local_sources(tmp_path: Path):
    graph, _ = parse(_SRC)
    materialize(graph, _SRC, tmp_path)

    sources_dir = tmp_path / "sources"
    assert sources_dir.is_dir()
    assert (sources_dir / "bbc.py").is_file()
    assert (sources_dir / "npr.py").is_file()

    bbc = (sources_dir / "bbc.py").read_text()
    # Baked-in URL and a discoverable build_source() entry point.
    assert "https://feeds.bbci.co.uk/news/world/rss.xml" in bbc
    assert "def build_source()" in bbc
    assert 'name=\'bbc\'' in bbc or 'name="bbc"' in bbc


# --------------------------------------------------------------------------- #
# #191 — faithful dataflow translation (sequential pipeline)                  #
# --------------------------------------------------------------------------- #

_SEQ = '''
import asyncio

SOURCES = {"mic": audio_clip(path="x.wav", chunk_ms=200)}


class RMSMeter:
    """Compute RMS."""
    def __init__(self):
        self.w = []
    def process(self, message):
        return message


class ThresholdDetector:
    """Edge detect."""
    def __init__(self):
        self.armed = True
    def process(self, message):
        return message


meter = RMSMeter()
detector = ThresholdDetector()


async def process_one(sample):
    rms = meter.process(sample)
    event = detector.process(rms)
    send_to(event, "terminal")
    return event


async def main():
    pass
'''


def test_sequential_pipeline_produces_edges_not_warnings():
    graph, warnings = parse(_SEQ)
    # Previously a sequential `.process()` chain produced zero edges and
    # two "unrecognised statement" warnings. It must now wire fully.
    assert warnings == []
    roles = {v["role"]: v["id"] for v in graph["vertices"]}
    assert set(roles) == {"rmsmeter", "thresholddetector"}
    # No synchronizer or router for a straight-line pipeline.
    assert not any(v["role"] in ("synchronizer", "router")
                   for v in graph["vertices"])

    meter_id = roles["rmsmeter"]
    det_id = roles["thresholddetector"]
    src_id = graph["sources"][0]["id"]
    sink_id = graph["sinks"][0]["id"]
    edges = {(tuple(e["from"]), tuple(e["to"])) for e in graph["edges"]}
    assert ((src_id, "out"), (meter_id, "in_")) in edges
    assert ((meter_id, "out"), (det_id, "in_")) in edges
    assert ((det_id, "out"), (sink_id, "in_")) in edges


def test_stateful_constructor_kwargs_captured_into_vertex_params():
    src = '''
import asyncio

SOURCES = {"mic": audio_clip(path="x.wav")}


class ThresholdDetector:
    """Edge detect."""
    def __init__(self, db_threshold=-30.0, debounce_ms=400.0):
        self.db_threshold = db_threshold
    def process(self, message):
        return message


detector = ThresholdDetector(db_threshold=-15.0, debounce_ms=250.0)


async def process_one(sample):
    event = detector.process(sample)
    send_to(event, "terminal")
    return event


async def main():
    pass
'''
    graph, _ = parse(src)
    det = [v for v in graph["vertices"] if v["role"] == "thresholddetector"][0]
    assert det["params"] == {"db_threshold": -15.0, "debounce_ms": 250.0}


def test_gather_introduces_no_extra_node():
    # gather is just concurrent calls — the only synthesized node comes
    # from the {**...} merge (a synchronizer), never from gather itself.
    graph, _ = parse(_SRC)
    roles = [v["role"] for v in graph["vertices"]]
    assert roles.count("synchronizer") == 1
    assert roles.count("router") == 1


def test_named_factory_source_gets_no_local_file(tmp_path: Path):
    # A source that references a registered factory by name (no url
    # param) must NOT get an app-local module.
    src = _SRC.replace(
        '    "npr": "https://feeds.npr.org/1004/rss.xml",\n', ""
    ).replace(
        '"bbc": "https://feeds.bbci.co.uk/news/world/rss.xml",',
        '"world": bbc_world(max_articles=5),',
    )
    graph, _ = parse(src)
    materialize(graph, src, tmp_path)
    # bbc_world is a registered factory → no sources/ file for it.
    assert not (tmp_path / "sources" / "bbc_world.py").exists()
    assert not (tmp_path / "sources" / "world.py").exists()


# --------------------------------------------------------------------------- #
# materialize robustness: _impl.py must import cleanly                         #
# --------------------------------------------------------------------------- #

_FUTURE_SRC = '''\
"""Module docstring."""
from __future__ import annotations

import asyncio

SOURCES = {"mic": audio_clip(path="x.wav")}


class RMSMeter:
    """Compute RMS."""
    def __init__(self):
        self.w = []
    def process(self, message):
        return message


meter = RMSMeter()


async def process_one(sample):
    rms = meter.process(sample)
    send_to(rms, "terminal")
    return rms


async def main():
    pass
'''


def test_impl_module_hoists_future_and_strips_sources(tmp_path: Path):
    import ast as _ast

    graph, _ = parse(_FUTURE_SRC)
    materialize(graph, _FUTURE_SRC, tmp_path)
    impl = (tmp_path / "roles" / "_impl.py").read_text()

    # _impl.py must be syntactically valid (future import not buried, and
    # the OfficeSpeak-only SOURCES declaration removed so `audio_clip`
    # doesn't NameError at import).
    tree = _ast.parse(impl)
    assert "from __future__ import annotations" in impl
    assert "SOURCES" not in impl

    # The future import must precede every non-docstring statement.
    first_future = next(
        i for i, n in enumerate(tree.body)
        if isinstance(n, _ast.ImportFrom) and n.module == "__future__"
    )
    for n in tree.body[:first_future]:
        assert isinstance(n, _ast.Expr) and isinstance(
            n.value, _ast.Constant
        ), "only docstrings may precede the future import"
