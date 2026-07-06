"""
Unit tests for officespeak/graph_viz.py — rendering a graph.yaml as a
diagram (mermaid / dot / text).
"""

from __future__ import annotations

import pytest

from officespeak.graph_viz import render, to_dot, to_html, to_mermaid, to_text


_GRAPH = {
    "sources": [
        {"id": "s0", "name": "bbc", "params": {"url": "http://x"}},
        {"id": "s1", "name": "npr", "params": {"url": "http://y"}},
    ],
    "vertices": [
        {"id": "v0", "role": "classify_severity", "kind": "llm"},
        {"id": "v1", "role": "synchronizer", "kind": "structural",
         "params": {"inports": ["severity"]}},
        {"id": "v2", "role": "router", "kind": "structural",
         "params": {"routes": [{"outport": "critical"}]}},
    ],
    "sinks": [
        {"id": "k0", "name": "jsonl_recorder", "params": {}},
        {"id": "k1", "name": "intelligence_display", "params": {}},
    ],
    "edges": [
        {"from": ["s0", "out"], "to": ["v0", "in_"]},
        {"from": ["s1", "out"], "to": ["v0", "in_"]},
        {"from": ["v0", "out"], "to": ["v1", "severity"]},
        {"from": ["v1", "out"], "to": ["v2", "in_"]},
        {"from": ["v1", "out"], "to": ["k0", "in_"]},
        {"from": ["v2", "critical"], "to": ["k1", "in_"]},
    ],
}


def test_mermaid_has_all_nodes_and_edges():
    out = to_mermaid(_GRAPH)
    assert out.startswith("flowchart TD")
    for node_id in ("s0", "s1", "v0", "v1", "v2", "k0", "k1"):
        assert node_id in out
    # One arrow per edge.
    assert out.count("-->") == len(_GRAPH["edges"])


def test_mermaid_labels_nondefault_ports_only():
    out = to_mermaid(_GRAPH)
    # Synchronizer inport and router outport are labelled...
    assert "|severity|" in out
    assert "|critical|" in out
    # ...but plain out->in_ edges carry no label.
    assert "|out|" not in out
    assert "|in_|" not in out


def test_mermaid_shapes_distinguish_kinds():
    out = to_mermaid(_GRAPH)
    assert 's0(["bbc"]):::source' in out
    assert 'v1{{"v1: synchronizer"}}:::sync' in out
    assert 'v2{"v2: router"}:::router' in out
    assert 'k0[("jsonl_recorder")]:::sink' in out
    assert 'v0["v0: classify_severity"]:::agent' in out


def test_dot_is_digraph_with_edges():
    out = to_dot(_GRAPH)
    assert out.startswith("digraph office {")
    assert out.count("->") == len(_GRAPH["edges"])
    assert '"s0" [label="bbc"' in out


def test_text_lists_sections_and_edges():
    out = to_text(_GRAPH)
    assert "Sources:" in out and "Agents:" in out and "Sinks:" in out
    assert "synchronizer (synchronizer)" in out
    assert "router (router)" in out
    # Edge with a labelled port.
    assert "--critical-->" in out


def test_html_is_self_contained_and_embeds_mermaid():
    out = to_html(_GRAPH, title="demo")
    assert out.startswith("<!DOCTYPE html>")
    assert "<title>demo</title>" in out
    assert "mermaid.min.js" in out          # loads the renderer
    assert 'class="mermaid"' in out
    assert "flowchart TD" in out            # embeds the diagram source


def test_render_dispatch_and_bad_format():
    assert render(_GRAPH, "mermaid").startswith("flowchart")
    assert render(_GRAPH, "html").startswith("<!DOCTYPE html>")
    assert render(_GRAPH, "dot").startswith("digraph")
    assert render(_GRAPH, "text").startswith("Sources:")
    with pytest.raises(ValueError):
        render(_GRAPH, "svg")
