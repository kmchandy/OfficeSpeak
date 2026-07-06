"""Unit tests for claudette.wrapper.

These tests do not invoke Claude. They verify the wrapper's
deterministic transformation: given (name, purpose, prompt_body,
output_schema), do we produce a syntactically-correct DSL role.md?
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from officespeak.wrapper import (
    create_agent_from_prompt,
    render_role_file,
)


# ── Fixtures ──────────────────────────────────────────────────────────


SIMPLE_PROMPT = """\
You receive one news article and produce a credibility score in [0, 1].

Input shape. Each article is a JSON object with these fields:
- "title"  — the headline
- "body"   — the article text
- "source" — the publication name

Your job. Consider the source's reputation, the article's tone and
specificity, and the presence of unverified or sensational claims.
Produce a numeric credibility score and a short reasoning string.
"""

SIMPLE_SCHEMA = {
    "score": "float in [0, 1]; higher = more credible",
    "reasoning": "one or two sentences explaining the score",
}


# ── render_role_file ──────────────────────────────────────────────────


class TestRenderRoleFile:
    """Tests for the pure-string rendering function."""

    def test_includes_frontmatter(self):
        out = render_role_file(
            name="credibility_scorer",
            purpose="Score article credibility.",
            prompt_body=SIMPLE_PROMPT,
            output_schema=SIMPLE_SCHEMA,
        )
        assert out.startswith("---\n")
        assert "contract: structured\n---" in out

    def test_includes_role_header(self):
        out = render_role_file(
            name="credibility_scorer",
            purpose="Score article credibility.",
            prompt_body=SIMPLE_PROMPT,
            output_schema=SIMPLE_SCHEMA,
        )
        assert "# Role: credibility_scorer" in out

    def test_includes_purpose_line(self):
        out = render_role_file(
            name="credibility_scorer",
            purpose="Score article credibility.",
            prompt_body=SIMPLE_PROMPT,
            output_schema=SIMPLE_SCHEMA,
        )
        assert "_Score article credibility._" in out

    def test_includes_prompt_body(self):
        out = render_role_file(
            name="credibility_scorer",
            purpose="Score article credibility.",
            prompt_body=SIMPLE_PROMPT,
            output_schema=SIMPLE_SCHEMA,
        )
        # A distinctive substring from SIMPLE_PROMPT should appear.
        assert "Consider the source's reputation" in out

    def test_includes_output_discipline_block(self):
        out = render_role_file(
            name="credibility_scorer",
            purpose="Score article credibility.",
            prompt_body=SIMPLE_PROMPT,
            output_schema=SIMPLE_SCHEMA,
        )
        assert "CRITICAL: Output Format" in out
        assert "single JSON object" in out
        assert "first character must be" in out
        assert "last character must be" in out

    def test_renders_schema_fields(self):
        out = render_role_file(
            name="credibility_scorer",
            purpose="Score article credibility.",
            prompt_body=SIMPLE_PROMPT,
            output_schema=SIMPLE_SCHEMA,
        )
        # Each schema field should appear as a bullet with its description.
        assert "`score`" in out
        assert "float in [0, 1]" in out
        assert "`reasoning`" in out
        assert "one or two sentences" in out

    def test_default_single_outport_emits_always_send_to(self):
        out = render_role_file(
            name="x",
            purpose="x",
            prompt_body="x",
            output_schema={"a": "b"},
        )
        assert "Always send to out." in out

    def test_custom_single_outport_uses_that_name(self):
        out = render_role_file(
            name="x",
            purpose="x",
            prompt_body="x",
            output_schema={"a": "b"},
            outports=("downstream",),
        )
        assert "Always send to downstream." in out

    def test_multi_outport_uses_send_to_field(self):
        out = render_role_file(
            name="router",
            purpose="route messages",
            prompt_body="...routing logic...",
            output_schema={"kind": "category label"},
            outports=("keep", "discard"),
        )
        assert "send_to" in out
        assert "`keep`" in out
        assert "`discard`" in out
        # Should NOT emit the single-outport "Always send to" line.
        assert "Always send to" not in out

    def test_ends_with_newline(self):
        out = render_role_file(
            name="x",
            purpose="x",
            prompt_body="x",
            output_schema={"a": "b"},
        )
        assert out.endswith("\n")

    def test_empty_schema_does_not_crash(self):
        out = render_role_file(
            name="x",
            purpose="x",
            prompt_body="x",
            output_schema={},
        )
        assert "(no fields specified)" in out

    def test_prompt_body_whitespace_is_normalised(self):
        # Leading/trailing whitespace in prompt body shouldn't bleed
        # into the output and create awkward double blank lines.
        out = render_role_file(
            name="x",
            purpose="x",
            prompt_body="\n\n  body  \n\n",
            output_schema={"a": "b"},
        )
        # No triple-newline sequences inside the body region.
        assert "\n\n\n" not in out

    def test_custom_contract_appears_in_frontmatter(self):
        out = render_role_file(
            name="x",
            purpose="x",
            prompt_body="x",
            output_schema={"a": "b"},
            contract="passthrough",
        )
        assert "contract: passthrough" in out


# ── create_agent_from_prompt ──────────────────────────────────────────


class TestCreateAgentFromPrompt:
    """Tests for the file-writing wrapper."""

    def test_writes_file_to_target_dir(self, tmp_path: Path):
        out_path = create_agent_from_prompt(
            name="credibility_scorer",
            purpose="Score article credibility.",
            prompt_body=SIMPLE_PROMPT,
            output_schema=SIMPLE_SCHEMA,
            target_dir=tmp_path,
        )
        assert out_path == tmp_path / "credibility_scorer.md"
        assert out_path.is_file()

    def test_file_contents_match_render(self, tmp_path: Path):
        out_path = create_agent_from_prompt(
            name="credibility_scorer",
            purpose="Score article credibility.",
            prompt_body=SIMPLE_PROMPT,
            output_schema=SIMPLE_SCHEMA,
            target_dir=tmp_path,
        )
        expected = render_role_file(
            name="credibility_scorer",
            purpose="Score article credibility.",
            prompt_body=SIMPLE_PROMPT,
            output_schema=SIMPLE_SCHEMA,
        )
        assert out_path.read_text() == expected

    def test_raises_on_missing_target_dir(self, tmp_path: Path):
        nonexistent = tmp_path / "does_not_exist"
        with pytest.raises(FileNotFoundError, match="target_dir"):
            create_agent_from_prompt(
                name="x",
                purpose="x",
                prompt_body="x",
                output_schema={"a": "b"},
                target_dir=nonexistent,
            )

    def test_raises_on_existing_file_without_overwrite(
        self, tmp_path: Path,
    ):
        create_agent_from_prompt(
            name="x",
            purpose="x",
            prompt_body="x",
            output_schema={"a": "b"},
            target_dir=tmp_path,
        )
        with pytest.raises(FileExistsError, match="overwrite=True"):
            create_agent_from_prompt(
                name="x",
                purpose="x",
                prompt_body="x",
                output_schema={"a": "b"},
                target_dir=tmp_path,
            )

    def test_overwrite_replaces_existing_file(self, tmp_path: Path):
        create_agent_from_prompt(
            name="x",
            purpose="first",
            prompt_body="x",
            output_schema={"a": "b"},
            target_dir=tmp_path,
        )
        create_agent_from_prompt(
            name="x",
            purpose="second",
            prompt_body="x",
            output_schema={"a": "b"},
            target_dir=tmp_path,
            overwrite=True,
        )
        contents = (tmp_path / "x.md").read_text()
        assert "_second_" in contents
        assert "_first_" not in contents


# ── DSL conformance ───────────────────────────────────────────────────


class TestDslConformance:
    """Tests that the produced files conform to DSL's role.md
    conventions (as observed from gallery examples).
    """

    def test_frontmatter_block_is_first(self):
        out = render_role_file(
            name="x",
            purpose="x",
            prompt_body="x",
            output_schema={"a": "b"},
        )
        # Frontmatter must be the first three lines.
        lines = out.splitlines()
        assert lines[0] == "---"
        assert lines[1] == "contract: structured"
        assert lines[2] == "---"

    def test_frontmatter_block_appears_exactly_once(self):
        out = render_role_file(
            name="x",
            purpose="x",
            prompt_body="x",
            output_schema={"a": "b"},
        )
        # Exactly two '---' delimiters (one opening, one closing).
        assert out.count("\n---") + (1 if out.startswith("---") else 0) == 2

    def test_role_header_uses_markdown_h1(self):
        out = render_role_file(
            name="credibility_scorer",
            purpose="x",
            prompt_body="x",
            output_schema={"a": "b"},
        )
        # Must have exactly one '# Role:' line, at column 0.
        h1_lines = [
            l for l in out.splitlines()
            if re.match(r"^# Role: ", l)
        ]
        assert len(h1_lines) == 1
        assert h1_lines[0] == "# Role: credibility_scorer"
