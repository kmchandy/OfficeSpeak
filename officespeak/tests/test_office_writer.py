"""
Unit tests for claudette/office_writer.py.

Covers:
- Header line
- Sources/Sinks rendering (single, multiple, with/without params)
- Agent rendering (a/an article, params)
- Connections rendering (source destinations, default 'out', named outports,
  fan-out, back-edges)
- End-to-end: situation_room and debate examples (parser + office_writer)
"""

from __future__ import annotations

import pytest

from officespeak.parser import parse
from officespeak.office_writer import write_office_md


# --------------------------------------------------------------------------- #
# Header                                                                       #
# --------------------------------------------------------------------------- #


def test_header_uses_office_name():
    graph = {
        "sources": [{"id": "s0", "name": "src", "params": {}}],
        "vertices": [{
            "id": "v0", "role": "classifier", "purpose": "p",
            "reads": [], "enriches": "x", "cyclic": False,
        }],
        "sinks": [{"id": "k0", "name": "display", "params": {}}],
        "edges": [
            {"from": ["s0", "out"], "to": ["v0", "in_"]},
            {"from": ["v0", "out"], "to": ["k0", "in_"]},
        ],
    }
    out = write_office_md(graph, "my_app")
    assert out.startswith("# Office: my_app\n")


# --------------------------------------------------------------------------- #
# Sources / Sinks                                                              #
# --------------------------------------------------------------------------- #


def test_sources_single_no_params():
    pseudo = """
inputs:
  x: source_a()
for each item from x:
  s1: classify item -> reads item, enriches y
  send to k
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    assert "Sources: source_a\n" in out


def test_sources_single_with_params():
    pseudo = """
inputs:
  x: source_a(n=3, name="foo")
for each item from x:
  s1: classify item -> reads item, enriches y
  send to k
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    assert 'Sources: source_a(n=3, name="foo")\n' in out


def test_sources_multiple_uses_hanging_indent():
    pseudo = """
inputs:
  a: src_a()
  b: src_b()
  c: src_c()
  x: merge(a, b, c)
for each item from x:
  s1: classify item -> reads item, enriches y
  send to k
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    lines = out.splitlines()
    # The Sources line is multi-line: first line ends in a comma; the rest
    # are indented to align with the first source name.
    src_lines = [l for l in lines if "src_" in l or l.startswith("Sources")]
    assert src_lines[0] == "Sources: src_a,"
    assert src_lines[1] == "         src_b,"  # 9-space indent ("Sources: ")
    assert src_lines[2] == "         src_c"


def test_sinks_with_quoted_string_arg():
    pseudo = """
inputs:
  x: src()
for each item from x:
  s1: classify item -> reads item, enriches y
  send to jsonl_recorder(path="out.jsonl")
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    assert 'jsonl_recorder(path="out.jsonl")' in out


def test_sinks_with_bool_arg():
    """The bool True should be rendered as Python `True`, not `true`."""
    pseudo = """
inputs:
  x: src()
for each item from x:
  s1: classify item -> reads item, enriches y
  send to gmail_sink(unread_only=true, n=5)
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    assert "gmail_sink(unread_only=True, n=5)" in out


# --------------------------------------------------------------------------- #
# Agents                                                                       #
# --------------------------------------------------------------------------- #


def test_agent_naming_uses_capital_v_prefix():
    pseudo = """
inputs:
  x: src()
for each thing from x:
  s1: classify thing -> reads thing, enriches y
  send to k
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    # thing_classifier starts with 't' (consonant) -> 'a'
    assert "V0 is a thing_classifier." in out


def test_article_a_or_an_by_vowel():
    pseudo = """
inputs:
  x: src()
for each thing from x:
  s1: extract entities -> reads thing, enriches entities
  s2: classify thing -> reads thing, enriches y
  send to k
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    # entity_extractor starts with 'e' (vowel) -> 'an'
    assert "V0 is an entity_extractor." in out
    # thing_classifier starts with 't' (consonant) -> 'a'
    assert "V1 is a thing_classifier." in out


# --------------------------------------------------------------------------- #
# Connections                                                                  #
# --------------------------------------------------------------------------- #


def test_connections_source_to_first_vertex():
    pseudo = """
inputs:
  x: src_a()
for each item from x:
  s1: classify item -> reads item, enriches y
  send to k
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    assert "src_a's destination is V0." in out


def test_connections_multiple_sources_to_same_vertex():
    pseudo = """
inputs:
  a: src_a()
  b: src_b()
  x: merge(a, b)
for each item from x:
  s1: classify item -> reads item, enriches y
  send to k
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    assert "src_a's destination is V0." in out
    assert "src_b's destination is V0." in out


def test_connections_pipeline_uses_out():
    pseudo = """
inputs:
  x: src()
for each item from x:
  s1: classify item -> reads item, enriches y
  s2: tag item -> reads item, enriches z
  send to k
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    assert "V0's out is V1." in out
    assert "V1's out is k." in out


def test_connections_router_uses_named_outports():
    """Router with named outports should emit one line per branch."""
    pseudo = """
inputs:
  x: src()
for each item from x:
  s1: classify item -> reads item, enriches category
  if category == "billing":
    send to billing_queue
  elif category == "technical":
    send to tech_queue
  else:
    send to general_queue
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    assert "V0's billing is billing_queue." in out
    assert "V0's technical is tech_queue." in out
    assert "V0's else is general_queue." in out


def test_connections_fan_out_uses_comma_list():
    """Two send-tos from one vertex's out port → one comma-separated line."""
    pseudo = """
inputs:
  x: src()
for each item from x:
  s1: classify item -> reads item, enriches y
  send to k_a
  send to k_b
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    assert "V0's out is k_a, k_b." in out


def test_connections_back_edge():
    pseudo = """
inputs:
  x: src()
for each item from x:
  s1: propose solution -> reads item, enriches solution
  s2: judge -> reads solution, enriches verdict
  if verdict == "approved":
    send to k
  else:
    send to s1
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "t")
    # Back-edge: V1's else routes to V0
    assert "V1's approved is k." in out
    assert "V1's else is V0." in out


# --------------------------------------------------------------------------- #
# End-to-end                                                                   #
# --------------------------------------------------------------------------- #


SITUATION_ROOM_PSEUDO = """
inputs:
  bbc:      bbc_world(max_articles=3)
  npr:      npr_news(max_articles=3)
  al_jaz:   al_jazeera(max_articles=3)
  articles: merge(bbc, npr, al_jaz)

for each article from articles:
  s1: classify severity -> reads article.body, enriches severity
  s2: identify location -> reads article.body, enriches location
  s3: write briefing    -> reads article.body, severity, location, enriches briefing

  if severity == "critical":
    send to intelligence_display
  send to jsonl_recorder_briefing(path="briefings.jsonl")
"""


def test_end_to_end_situation_room():
    """Full parser + office_writer pipeline on the §3 example."""
    graph, _ = parse(SITUATION_ROOM_PSEUDO)
    out = write_office_md(graph, "situation_room")

    # Header
    assert out.startswith("# Office: situation_room\n")

    # Sources (3, multi-line)
    assert "Sources: bbc_world(max_articles=3)," in out
    assert "npr_news(max_articles=3)" in out
    assert "al_jazeera(max_articles=3)" in out

    # Sinks
    assert "intelligence_display" in out
    assert 'jsonl_recorder_briefing(path="briefings.jsonl")' in out

    # Agents — three vertices with derived role names
    assert "V0 is a severity_classifier." in out
    assert "V1 is a geolocator." in out
    assert "V2 is a briefing_writer." in out

    # Connections
    assert "bbc_world's destination is V0." in out
    assert "npr_news's destination is V0." in out
    assert "al_jazeera's destination is V0." in out
    assert "V0's out is V1." in out
    assert "V1's out is V2." in out
    assert "V2's critical is intelligence_display, jsonl_recorder_briefing." in out
    assert "V2's else is jsonl_recorder_briefing." in out


DEBATE_PSEUDO = """
inputs:
  problems: problem_stream()

for each problem from problems:
  s0: count iter        -> enriches iter
  s1: propose solution  -> reads problem, iter, enriches solution
  s2: critique solution -> reads solution, enriches critique
  s3: judge             -> reads critique, enriches verdict

  if verdict == "approved":
    send to answers
  elif iter > 2:
    send to gave_up
  else:
    send to s0
"""


def test_end_to_end_debate_with_back_edge():
    graph, _ = parse(DEBATE_PSEUDO)
    out = write_office_md(graph, "debate")

    # Header + sources
    assert "# Office: debate" in out
    assert "Sources: problem_stream" in out

    # Sinks: answers, gave_up
    assert "Sinks:" in out
    assert "answers" in out
    assert "gave_up" in out

    # Agents
    assert "V0 is an iter_counter." in out
    assert "V1 is a solution_proposer." in out
    assert "V2 is a solution_critic." in out
    assert "V3 is a judge." in out

    # Back-edge connection
    assert "V3's else is V0." in out
    # Approved goes to answers
    assert "V3's approved is answers." in out


# --------------------------------------------------------------------------- #
# Round-trip with the parser                                                   #
# --------------------------------------------------------------------------- #


def test_office_text_is_complete_for_minimal_pipeline():
    """Sanity: every section header is present in any valid output."""
    pseudo = """
inputs:
  x: src()
for each item from x:
  s1: classify item -> reads item, enriches y
  send to k
"""
    graph, _ = parse(pseudo)
    out = write_office_md(graph, "tiny")
    assert "# Office: tiny" in out
    assert "Sources:" in out
    assert "Sinks:" in out
    assert "Agents:" in out
    assert "Connections:" in out
    # Ends with a single trailing newline
    assert out.endswith("\n")
    assert not out.endswith("\n\n")


# --------------------------------------------------------------------------- #
# Integration with DSL's real parser (skipped if dissyslab not installed)      #
# --------------------------------------------------------------------------- #


def _dsl_available():
    try:
        from dissyslab.office.parser import parse_office_dir  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _dsl_available(), reason="dissyslab not installed")
def test_dsl_accepts_situation_room_office(tmp_path):
    """DSL's real office parser must accept our generated office.md."""
    from dissyslab.office.parser import parse_office_dir

    graph, _ = parse(SITUATION_ROOM_PSEUDO)
    out = write_office_md(graph, "situation_room")
    (tmp_path / "office.md").write_text(out)

    spec = parse_office_dir(tmp_path)
    assert spec.name == "situation_room"
    assert len(spec.sources) == 3
    assert [s.name for s in spec.sources] == ["bbc_world", "npr_news", "al_jazeera"]
    assert len(spec.sinks) == 2
    assert len(spec.agents) == 3
    assert [a.role_name for a in spec.agents] == [
        "severity_classifier", "geolocator", "briefing_writer"
    ]
    # 7 connection lines: 3 source-destinations + 2 pipeline + 2 router-branch
    assert len(spec.connections) == 7


@pytest.mark.skipif(not _dsl_available(), reason="dissyslab not installed")
def test_dsl_accepts_debate_office_with_back_edge(tmp_path):
    """DSL's real parser must accept our office.md including the back-edge."""
    from dissyslab.office.parser import parse_office_dir

    graph, _ = parse(DEBATE_PSEUDO)
    out = write_office_md(graph, "debate")
    (tmp_path / "office.md").write_text(out)

    spec = parse_office_dir(tmp_path)
    assert spec.name == "debate"
    # Back-edge: V3.else routes to V0
    v3_else_destinations = []
    for c in spec.connections:
        if c.source.name == "V3" and c.source.port == "else":
            v3_else_destinations = [(d.name, d.port) for d in c.destinations]
    assert v3_else_destinations == [("V0", "in_")]
