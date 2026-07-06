"""
Unit tests for claudette/parser.py.

Each construct from catalog/translation_table.md is covered by at least one test.
The worked examples in the translation table appear as end-to-end tests.
"""

from __future__ import annotations

import pytest

from officespeak.parser import parse, ParseError


# --------------------------------------------------------------------------- #
# §2.1 — inputs block                                                          #
# --------------------------------------------------------------------------- #


def test_single_primitive_input():
    """§2.1.3 — single primitive input + minimal pipeline."""
    pseudo = """
inputs:
  emails: imap_inbox(folder="INBOX", poll_seconds=60)

for each email from emails:
  s1: classify spam -> reads email.body, enriches spam_score
  send to spam_report
"""
    graph, warnings = parse(pseudo)
    assert len(graph["sources"]) == 1
    s = graph["sources"][0]
    assert s["id"] == "s0"
    assert s["name"] == "imap_inbox"
    assert s["params"] == {"folder": "INBOX", "poll_seconds": 60}


def test_three_primitives_plus_merge():
    """§2.1.4 — three primitives + a derived merge."""
    pseudo = """
inputs:
  bbc:      bbc_world(max_articles=3)
  npr:      npr_news(max_articles=3)
  al_jaz:   al_jazeera(max_articles=3)
  articles: merge(bbc, npr, al_jaz)

for each article from articles:
  s1: classify severity -> reads article.body, enriches severity
  send to display
"""
    graph, warnings = parse(pseudo)
    assert len(graph["sources"]) == 3
    assert [s["id"] for s in graph["sources"]] == ["s0", "s1", "s2"]
    assert [s["name"] for s in graph["sources"]] == ["bbc_world", "npr_news", "al_jazeera"]
    # All three sources feed v0 (merge is implicit in the edges)
    incoming_v0 = [e for e in graph["edges"] if e["to"][0] == "v0"]
    src_ids = {e["from"][0] for e in incoming_v0}
    assert src_ids == {"s0", "s1", "s2"}


def test_merge_with_single_argument_is_legal():
    pseudo = """
inputs:
  bbc:      bbc_world()
  articles: merge(bbc)

for each article from articles:
  s1: classify severity -> reads article.body, enriches severity
  send to display
"""
    graph, _ = parse(pseudo)
    assert len(graph["sources"]) == 1
    # The merge of one variable is equivalent to that variable
    incoming_v0 = [e for e in graph["edges"] if e["to"][0] == "v0"]
    assert len(incoming_v0) == 1
    assert incoming_v0[0]["from"][0] == "s0"


def test_merge_undefined_variable_is_parse_error():
    pseudo = """
inputs:
  articles: merge(bbc, npr)

for each article from articles:
  s1: classify severity -> reads article.body, enriches severity
  send to display
"""
    with pytest.raises(ParseError, match="undefined variable"):
        parse(pseudo)


def test_duplicate_input_var_is_parse_error():
    pseudo = """
inputs:
  bbc: bbc_world()
  bbc: npr_news()

for each x from bbc:
  s1: classify x -> reads x, enriches y
  send to k
"""
    with pytest.raises(ParseError, match="duplicate input"):
        parse(pseudo)


# --------------------------------------------------------------------------- #
# §2.2 — for each (pipeline body)                                              #
# --------------------------------------------------------------------------- #


def test_pipeline_two_steps_implicit_edges():
    """§2.2 worked example — pipeline with 2 steps."""
    pseudo = """
inputs:
  articles: bbc_world(max_articles=3)

for each article from articles:
  s1: extract entities -> reads article.body, enriches entities
  s2: classify severity -> reads article.body, enriches severity
  send to intelligence_display
"""
    graph, _ = parse(pseudo)
    assert len(graph["vertices"]) == 2
    assert graph["vertices"][0]["id"] == "v0"
    assert graph["vertices"][1]["id"] == "v1"
    # Implicit edges
    edges = graph["edges"]
    expected = [
        {"from": ["s0", "out"], "to": ["v0", "in_"]},
        {"from": ["v0", "out"], "to": ["v1", "in_"]},
        {"from": ["v1", "out"], "to": ["k0", "in_"]},
    ]
    for e in expected:
        assert e in edges, f"missing edge {e}"


def test_for_each_unknown_input_var_is_parse_error():
    pseudo = """
inputs:
  bbc: bbc_world()

for each x from articles:
  s1: classify x -> reads x, enriches y
  send to k
"""
    with pytest.raises(ParseError, match="unknown input variable"):
        parse(pseudo)


def test_for_each_empty_body_is_parse_error():
    pseudo = """
inputs:
  bbc: bbc_world()

for each x from bbc:
"""
    with pytest.raises(ParseError, match="for-each body"):
        parse(pseudo)


def test_no_send_to_is_parse_error():
    pseudo = """
inputs:
  bbc: bbc_world()

for each x from bbc:
  s1: classify x -> reads x, enriches y
"""
    with pytest.raises(ParseError, match="no 'send to'"):
        parse(pseudo)


# --------------------------------------------------------------------------- #
# §2.3 — step lines: enriches                                                  #
# --------------------------------------------------------------------------- #


def test_step_line_with_reads_clause():
    pseudo = """
inputs:
  articles: bbc()

for each article from articles:
  s1: write briefing -> reads article.body, severity, location, enriches briefing
  send to display
"""
    graph, _ = parse(pseudo)
    v = graph["vertices"][0]
    assert v["reads"] == ["article.body", "severity", "location"]
    assert v["enriches"] == "briefing"
    assert v["role"] == "briefing_writer"


def test_step_line_without_reads_clause():
    pseudo = """
inputs:
  articles: bbc()

for each article from articles:
  s1: classify severity -> enriches severity
  send to display
"""
    graph, _ = parse(pseudo)
    v = graph["vertices"][0]
    assert v["reads"] == []
    assert v["enriches"] == "severity"


def test_step_line_missing_enriches_is_parse_error():
    pseudo = """
inputs:
  articles: bbc()

for each article from articles:
  s1: classify severity -> reads article.body
  send to display
"""
    with pytest.raises(ParseError, match=r"missing 'enriches"):
        parse(pseudo)


def test_role_derivation_table():
    """The role-name derivation should match translation table §2.3 examples."""
    from officespeak.parser import _derive_role
    assert _derive_role("extract entities") == "entity_extractor"
    assert _derive_role("classify severity") == "severity_classifier"
    assert _derive_role("tag topic") == "topic_tagger"
    assert _derive_role("identify location") == "geolocator"
    assert _derive_role("write briefing") == "briefing_writer"
    assert _derive_role("score sentiment") == "sentiment_scorer"


def test_arrow_unicode_and_ascii_both_accepted():
    """Both → and -> should work as step-line arrows."""
    for arrow in ("->", "→"):
        pseudo = f"""
inputs:
  x: src()

for each item from x:
  s1: classify item {arrow} reads item, enriches y
  send to k
"""
        graph, _ = parse(pseudo)
        assert graph["vertices"][0]["enriches"] == "y"


# --------------------------------------------------------------------------- #
# §2.4 — if/elif/else (router)                                                 #
# --------------------------------------------------------------------------- #


def test_three_way_router():
    """§2.4 — three-way router."""
    pseudo = """
inputs:
  tickets: support_inbox()

for each ticket from tickets:
  s1: classify ticket -> reads ticket.body, enriches category
  if category == "billing":
    send to billing_queue
  elif category == "technical":
    send to tech_queue
  else:
    send to general_queue
"""
    graph, _ = parse(pseudo)
    v = graph["vertices"][0]
    assert v["outports"] == ["billing", "technical", "else"]
    assert {s["name"] for s in graph["sinks"]} == {
        "billing_queue", "tech_queue", "general_queue"
    }
    # Edges from named outports
    outport_targets = {
        e["from"][1]: graph["sinks"][int(e["to"][0][1:])]["name"]
        for e in graph["edges"] if e["from"][0] == "v0"
    }
    assert outport_targets == {
        "billing": "billing_queue",
        "technical": "tech_queue",
        "else": "general_queue",
    }


def test_binary_predicate_router():
    """§2.4 binary filter — predicate produces true/false outports."""
    pseudo = """
inputs:
  txns: txn_stream()

for each tx from txns:
  s1: score fraud_risk -> reads tx, enriches fraud_score
  if fraud_score > 0.8:
    send to fraud_review_queue
  else:
    send to normal_processing
"""
    graph, _ = parse(pseudo)
    v = graph["vertices"][0]
    assert v["outports"] == ["true", "false"]


def test_implicit_else_outport_for_unconditional_send():
    """§3 — `if X:` without explicit else still creates an else outport
    so that unconditional send-tos can route from it."""
    pseudo = """
inputs:
  articles: bbc()

for each article from articles:
  s1: classify severity -> reads article.body, enriches severity
  if severity == "critical":
    send to intelligence_display
  send to jsonl_recorder(path="briefings.jsonl")
"""
    graph, _ = parse(pseudo)
    v = graph["vertices"][0]
    assert "critical" in v["outports"]
    assert "else" in v["outports"]
    # critical -> intelligence_display, critical -> jsonl_recorder, else -> jsonl_recorder
    by_outport = {(e["from"][1], graph["sinks"][int(e["to"][0][1:])]["name"])
                  for e in graph["edges"] if e["from"][0] == "v0"}
    assert ("critical", "intelligence_display") in by_outport
    assert ("critical", "jsonl_recorder") in by_outport
    assert ("else", "jsonl_recorder") in by_outport


def test_step_in_if_body_is_parse_error():
    """If-body cannot contain step lines (grammar restriction in §2.4)."""
    pseudo = """
inputs:
  tickets: src()

for each t from tickets:
  s1: classify t -> reads t, enriches category
  if category == "urgent":
    s2: extract entities -> reads t.body, enriches entities
    send to urgent_queue
  else:
    send to default_queue
"""
    with pytest.raises(ParseError, match="if-body must contain only 'send to'"):
        parse(pseudo)


def test_unsupported_condition_form():
    pseudo = """
inputs:
  x: src()

for each item from x:
  s1: classify item -> reads item, enriches v
  if v + 1 == 5:
    send to k
"""
    with pytest.raises(ParseError, match="unsupported condition"):
        parse(pseudo)


# --------------------------------------------------------------------------- #
# §2.5 — send to <target>                                                      #
# --------------------------------------------------------------------------- #


def test_fan_out_two_sinks_from_one_vertex():
    """§2.5 fan-out — two sinks share v0's out port."""
    pseudo = """
inputs:
  articles: bbc()

for each article from articles:
  s1: write briefing -> reads article.body, enriches briefing
  send to intelligence_display
  send to jsonl_recorder(path="briefings.jsonl")
"""
    graph, _ = parse(pseudo)
    assert len(graph["sinks"]) == 2
    out_edges = [e for e in graph["edges"] if e["from"][0] == "v0"]
    assert len(out_edges) == 2
    assert all(e["from"][1] == "out" for e in out_edges)


def test_sink_dedup_same_name_same_args():
    """Two `send to X` lines with identical args share the same sink id."""
    pseudo = """
inputs:
  articles: bbc()

for each article from articles:
  s1: classify severity -> reads article.body, enriches severity
  if severity == "critical":
    send to display
  send to display
"""
    graph, _ = parse(pseudo)
    assert len(graph["sinks"]) == 1


def test_sink_no_dedup_different_args():
    """Sinks with different args are distinct."""
    pseudo = """
inputs:
  articles: bbc()

for each article from articles:
  s1: write briefing -> reads article.body, enriches briefing
  send to jsonl_recorder(path="a.jsonl")
  send to jsonl_recorder(path="b.jsonl")
"""
    graph, _ = parse(pseudo)
    assert len(graph["sinks"]) == 2


def test_back_edge_via_send_to_earlier_step():
    """§2.5 back-edge — `send to s1` creates a cycle."""
    pseudo = """
inputs:
  problems: problem_stream()

for each problem from problems:
  s1: propose solution -> reads problem, enriches solution
  s2: critique solution -> reads solution, enriches critique
  s3: judge -> reads critique, enriches verdict
  if verdict == "approved":
    send to k_answers
  else:
    send to s1
"""
    graph, warnings = parse(pseudo)
    # Look for the back-edge in edges
    back_edges = [
        e for e in graph["edges"]
        if e["from"][0] == "v2" and e["to"][0] == "v0"
    ]
    assert len(back_edges) == 1
    assert back_edges[0]["from"][1] == "else"
    # Cyclic vertices marked
    cyclic_vertices = [v for v in graph["vertices"] if v["cyclic"]]
    assert len(cyclic_vertices) == 3  # v0, v1, v2 all in the cycle
    # Termination warning emitted (no counter field)
    assert any("convergence-only termination" in w for w in warnings)


def test_back_edge_with_counter_no_warning():
    """When a counter field is present, the termination warning is suppressed."""
    pseudo = """
inputs:
  problems: problem_stream()

for each problem from problems:
  s0: count iter -> enriches iter
  s1: propose solution -> reads problem, enriches solution
  s2: judge -> reads solution, enriches verdict
  if verdict == "approved":
    send to k
  else:
    send to s0
"""
    graph, warnings = parse(pseudo)
    assert not any("convergence-only termination" in w for w in warnings)


def test_back_edge_target_with_args_is_parse_error():
    pseudo = """
inputs:
  problems: src()

for each p from problems:
  s1: propose solution -> reads p, enriches solution
  s2: judge -> reads solution, enriches verdict
  if verdict == "approved":
    send to k
  else:
    send to s1(extra=1)
"""
    with pytest.raises(ParseError, match="back-edge target"):
        parse(pseudo)


# --------------------------------------------------------------------------- #
# §3 — end-to-end worked example                                               #
# --------------------------------------------------------------------------- #


def test_end_to_end_worked_example_from_section_3():
    """Reproduces the §3 end-to-end example from the translation table."""
    pseudo = """
inputs:
  bbc:      bbc_world(max_articles=3)
  npr:      npr_news(max_articles=3)
  al_jaz:   al_jazeera(max_articles=3)
  articles: merge(bbc, npr, al_jaz)

for each article from articles:
  s1: classify severity -> reads article.body, enriches severity
  s2: identify location -> reads article.body, enriches location
  s3: write briefing -> reads article.body, severity, location, enriches briefing
  if severity == "critical":
    send to intelligence_display
  send to jsonl_recorder_briefing(path="briefings.jsonl")
"""
    graph, warnings = parse(pseudo)

    # Sources
    assert [s["id"] for s in graph["sources"]] == ["s0", "s1", "s2"]
    assert [s["name"] for s in graph["sources"]] == [
        "bbc_world", "npr_news", "al_jazeera"
    ]
    # Vertices
    assert len(graph["vertices"]) == 3
    assert graph["vertices"][0]["role"] == "severity_classifier"
    assert graph["vertices"][1]["role"] == "geolocator"
    assert graph["vertices"][2]["role"] == "briefing_writer"
    # Router vertex has outports
    assert graph["vertices"][2]["outports"] == ["critical", "else"]
    # Sinks
    assert {s["name"] for s in graph["sinks"]} == {
        "intelligence_display", "jsonl_recorder_briefing"
    }
    # Specific edges
    expected = [
        {"from": ["s0", "out"], "to": ["v0", "in_"]},
        {"from": ["s1", "out"], "to": ["v0", "in_"]},
        {"from": ["s2", "out"], "to": ["v0", "in_"]},
        {"from": ["v0", "out"], "to": ["v1", "in_"]},
        {"from": ["v1", "out"], "to": ["v2", "in_"]},
    ]
    for e in expected:
        assert e in graph["edges"], f"missing edge {e}"
    # No cyclic vertices in this graph
    assert not any(v["cyclic"] for v in graph["vertices"])


# --------------------------------------------------------------------------- #
# Misc: comments, blank lines, errors                                          #
# --------------------------------------------------------------------------- #


def test_comments_and_blank_lines_ignored():
    pseudo = """
# This is a comment
inputs:
  # nested comment
  articles: bbc()

  # blank line above this

for each article from articles:  # inline comment
  s1: classify severity -> reads article.body, enriches severity   # comment
  send to display
"""
    graph, _ = parse(pseudo)
    assert len(graph["sources"]) == 1
    assert len(graph["vertices"]) == 1
    assert len(graph["sinks"]) == 1


def test_empty_pseudocode_is_parse_error():
    with pytest.raises(ParseError, match="empty"):
        parse("")


def test_missing_inputs_block():
    pseudo = """
for each x from y:
  s1: classify x -> reads x, enriches y
  send to k
"""
    with pytest.raises(ParseError, match="expected 'inputs:'"):
        parse(pseudo)


def test_quoted_string_arg_with_special_chars():
    pseudo = """
inputs:
  files: file_watcher(path="/tmp/foo bar.jsonl")

for each f from files:
  s1: classify f -> reads f, enriches kind
  send to display
"""
    graph, _ = parse(pseudo)
    assert graph["sources"][0]["params"]["path"] == "/tmp/foo bar.jsonl"


def test_purpose_strings_match_template():
    """All vertex purpose strings follow 'Read X; set Y.' template."""
    pseudo = """
inputs:
  x: src()

for each item from x:
  s1: classify item -> reads item.body, enriches category
  s2: write summary -> reads item.body, category, enriches summary
  send to display
"""
    graph, _ = parse(pseudo)
    for v in graph["vertices"]:
        assert v["purpose"].startswith("Read "), v["purpose"]
        assert "; set `" in v["purpose"], v["purpose"]
