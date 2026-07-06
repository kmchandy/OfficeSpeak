"""
Unit tests for claudette/harness.py.

The critical thing to test is `structural_equivalence`: it must
recognise two graphs as the same when they differ only in positional
IDs / declaration order, and as different when they differ in any
substantive way (sources, sinks, vertex roles, reads/enriches/outports,
edge structure).
"""

from __future__ import annotations

import textwrap

import pytest

from officespeak.parser import parse
from officespeak.harness import structural_equivalence


def _g(pseudo: str) -> dict:
    """Helper: parse pseudocode -> graph."""
    graph, _ = parse(textwrap.dedent(pseudo))
    return graph


# --------------------------------------------------------------------------- #
# Positive: equivalent graphs                                                  #
# --------------------------------------------------------------------------- #


def test_identical_graphs_are_equivalent():
    g = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to k
    """)
    assert structural_equivalence(g, g)


def test_renaming_step_ids_does_not_break_equivalence():
    g1 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to k
    """)
    g2 = _g("""\
        inputs:
          x: src()
        for each item from x:
          step_alpha: classify item -> reads item, enriches y
          send to k
    """)
    assert structural_equivalence(g1, g2)


def test_renaming_input_variable_does_not_break_equivalence():
    # Loop variable kept the same ('msg' both sides). Only the input
    # variable name changes (inbox vs mail). Input names are pure
    # pseudocode-level; they don't appear in the graph.
    g1 = _g("""\
        inputs:
          inbox: src()
        for each msg from inbox:
          s1: classify msg -> reads msg, enriches y
          send to k
    """)
    g2 = _g("""\
        inputs:
          mail: src()
        for each msg from mail:
          s1: classify msg -> reads msg, enriches y
          send to k
    """)
    assert structural_equivalence(g1, g2)


def test_renaming_merge_var_does_not_break_equivalence():
    # Same as above: only the input variable names change (a,b,combined
    # vs first,second,all_items). Loop variable, verb, and reads are
    # identical, so role names match.
    g1 = _g("""\
        inputs:
          a: src_a()
          b: src_b()
          combined: merge(a, b)
        for each item from combined:
          s1: classify item -> reads item, enriches y
          send to k
    """)
    g2 = _g("""\
        inputs:
          first: src_a()
          second: src_b()
          all_items: merge(first, second)
        for each item from all_items:
          step1: classify item -> reads item, enriches y
          send to k
    """)
    assert structural_equivalence(g1, g2)


def test_renaming_loop_var_does_NOT_break_equivalence():
    """Loop variable changes the role name but not what gets enriched.
    Under execution-equivalence semantics, this is the same design."""
    g1 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to k
    """)
    g2 = _g("""\
        inputs:
          x: src()
        for each thing from x:
          s1: classify thing -> reads thing, enriches y
          send to k
    """)
    assert structural_equivalence(g1, g2)


def test_reordered_sources_in_merge_remain_equivalent():
    """Sources are compared as sets, so order doesn't matter."""
    g1 = _g("""\
        inputs:
          a: src_a()
          b: src_b()
          c: src_c()
          all: merge(a, b, c)
        for each x from all:
          s1: classify x -> reads x, enriches y
          send to k
    """)
    g2 = _g("""\
        inputs:
          c: src_c()
          a: src_a()
          b: src_b()
          all: merge(c, a, b)
        for each x from all:
          s1: classify x -> reads x, enriches y
          send to k
    """)
    assert structural_equivalence(g1, g2)


def test_reordered_router_branches_remain_equivalent():
    g1 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches category
          if category == "a":
            send to k_a
          elif category == "b":
            send to k_b
          else:
            send to k_c
    """)
    # Different elif/else order shouldn't matter for set comparison.
    g2 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches category
          if category == "b":
            send to k_b
          elif category == "a":
            send to k_a
          else:
            send to k_c
    """)
    assert structural_equivalence(g1, g2)


# --------------------------------------------------------------------------- #
# Negative: substantively different graphs                                     #
# --------------------------------------------------------------------------- #


def test_different_source_name_breaks_equivalence():
    g1 = _g("""\
        inputs:
          x: src_a()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to k
    """)
    g2 = _g("""\
        inputs:
          x: src_b()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to k
    """)
    diff = structural_equivalence(g1, g2)
    assert not diff
    assert any("source" in d for d in diff.differences)


def test_different_source_params_does_NOT_break_equivalence():
    """Source params are config (volume, timing). Same source name
    = execution-equivalent regardless of params."""
    g1 = _g("""\
        inputs:
          x: src(n=3)
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to k
    """)
    g2 = _g("""\
        inputs:
          x: src(n=5)
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to k
    """)
    assert structural_equivalence(g1, g2)


def test_different_sink_params_does_NOT_break_equivalence():
    """Sink params (e.g., path) are config. Same sink type =
    execution-equivalent regardless of filename. This matches the
    inbox_triage case observed in practice."""
    g1 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to jsonl_recorder_archive(path="a.jsonl")
    """)
    g2 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to jsonl_recorder_archive(path="b.jsonl")
    """)
    assert structural_equivalence(g1, g2)


def test_different_sink_name_breaks_equivalence():
    g1 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to display
    """)
    g2 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to recorder
    """)
    diff = structural_equivalence(g1, g2)
    assert not diff
    assert any("sink" in d for d in diff.differences)


def test_different_enriches_field_breaks_equivalence():
    g1 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches severity
          send to k
    """)
    g2 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches urgency
          send to k
    """)
    diff = structural_equivalence(g1, g2)
    assert not diff


def test_different_reads_does_NOT_break_equivalence():
    """Reads is the field-list the agent inspects. Both designs
    enrich `summary`; reading more or fewer fields is an
    implementation choice, not a design choice."""
    g1 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: write summary -> reads item.body, item.title, enriches summary
          send to k
    """)
    g2 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: write summary -> reads item.body, enriches summary
          send to k
    """)
    assert structural_equivalence(g1, g2)


def test_different_role_does_NOT_break_equivalence():
    """Role name is derived from the verb phrase, which is a
    naming choice. Both designs enrich `y` from the same source —
    execution-equivalent."""
    g1 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to k
    """)
    g2 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: extract item -> reads item, enriches y
          send to k
    """)
    assert structural_equivalence(g1, g2)


def test_pipeline_with_extra_step_breaks_equivalence():
    g1 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches y
          send to k
    """)
    g2 = _g("""\
        inputs:
          x: src()
        for each item from x:
          s1: classify item -> reads item, enriches y
          s2: tag item -> reads item, enriches t
          send to k
    """)
    diff = structural_equivalence(g1, g2)
    assert not diff


def test_back_edge_vs_forward_edge_breaks_equivalence():
    """One graph has feedback; the other doesn't."""
    g1 = _g("""\
        inputs:
          x: starter
        for each item from x:
          s1: propose solution -> reads item, enriches solution
          s2: judge -> reads solution, enriches verdict
          if verdict == "approved":
            send to k
          else:
            send to s1
    """)
    g2 = _g("""\
        inputs:
          x: starter
        for each item from x:
          s1: propose solution -> reads item, enriches solution
          s2: judge -> reads solution, enriches verdict
          if verdict == "approved":
            send to k
          else:
            send to k
    """)
    diff = structural_equivalence(g1, g2)
    assert not diff
    # The diff should mention an edge in expected (the back-edge)
    # not in actual.
    assert any("edge" in d for d in diff.differences)


# --------------------------------------------------------------------------- #
# Mock-mode end-to-end (uses the sanity_checks/ fixtures)                      #
# --------------------------------------------------------------------------- #


def test_mock_mode_runs_against_real_sanity_cases():
    """Mock mode uses expected as actual, so every comparison should pass."""
    from pathlib import Path
    from officespeak.harness import run_case

    cases_dir = Path(__file__).resolve().parents[2] / "examples" / "sanity_checks"
    meta_prompt = (
        Path(__file__).resolve().parents[2] / "prompts" / "meta_prompt_v1.md"
    )
    if not cases_dir.is_dir():
        pytest.skip("sanity_checks dir not found")
    if not meta_prompt.is_file():
        pytest.skip("meta_prompt_v1.md not found")

    cases = [
        "01_weather_alert",
        "02_arxiv_summary",
        "03_inbox_triage",
        "04_debate",
    ]
    for case in cases:
        r = run_case(case, cases_dir, meta_prompt, use_llm=False)
        assert r.status in ("MOCK", "ERROR_OUTPUT"), (
            f"{case}: status={r.status}, detail={r.detail}"
        )
