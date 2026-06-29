"""
Wrapper: Claude-generated prompt → DSL role file.

Separation of concerns:

  Claude generates: the substantive prompt body — what the agent should
                    do, what input it expects, what output it produces.

  This wrapper generates: all DSL-specific boilerplate — YAML
                    frontmatter, the contract declaration, JSON output
                    discipline, "Always send to out", role-file naming.

  Composed result: a DSL-runnable role.md.

Why the separation: Claude is reliably good at writing English prompts
that describe tasks; Claude is less reliable at memorising and applying
framework-specific syntactic conventions. Putting conventions in
deterministic Python eliminates an entire class of failure mode and
makes the framework conventions trivially updatable.

Public API:
    create_agent_from_prompt(name, purpose, prompt_body, ...) -> Path
        Write a DSL role.md file from a Claude-generated prompt.

    render_role_file(name, purpose, prompt_body, ...) -> str
        Same, but return the file contents as a string (useful for tests
        and for callers that want to handle file IO themselves).
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import Mapping, Sequence


# ── Defaults ──────────────────────────────────────────────────────────

DEFAULT_INPORTS: tuple[str, ...] = ("in_",)
DEFAULT_OUTPORTS: tuple[str, ...] = ("out",)
DEFAULT_CONTRACT = "structured"


# ── Helpers ───────────────────────────────────────────────────────────


def _render_frontmatter(contract: str) -> str:
    """Render the YAML front-matter block.

    DSL's role-file parser reads only a small set of keys today
    (contract, AI). The frontmatter is deliberately minimal — Claudette
    additions (purpose, when_to_use, etc.) live alongside the role file
    in a separate ``meta.yaml``, not in the role's own frontmatter.
    """
    return f"---\ncontract: {contract}\n---"


def _format_schema_lines(output_schema: Mapping[str, str]) -> str:
    """Render an output schema as a bulleted list for inclusion in the
    output-discipline block.

    The schema is a dict from field name to short English description
    of the field's type and meaning. Claudette will have produced this
    schema; the wrapper just renders it.
    """
    if not output_schema:
        return "(no fields specified)"
    return "\n".join(
        f"- `{field}`: {description}"
        for field, description in output_schema.items()
    )


def _render_output_discipline(
    output_schema: Mapping[str, str],
    outports: Sequence[str],
) -> str:
    """Render the boilerplate that enforces JSON output discipline.

    This is the part that ensures Claude's prompt produces parseable
    output regardless of how vague the substantive prompt happens to
    be. The discipline block is deliberately stiff: caps, imperative
    phrasing, explicit first-char/last-char rules, no markdown fences.

    Implementation note: avoid ``textwrap.dedent`` here. dedent over a
    triple-quoted f-string with multi-line interpolations breaks
    because dedent only considers the common leading whitespace of the
    literal text, not of the interpolated content. Building the string
    line-by-line is uglier but produces correctly-formatted output.
    """
    schema_block = _format_schema_lines(output_schema)
    if len(outports) == 1:
        send_line = f"Always send to {outports[0]}."
    else:
        port_list = ", ".join(f"`{p}`" for p in outports)
        send_line = (
            f"Set the `send_to` field to one of: {port_list}. "
            "Choose based on the routing logic above."
        )
    lines = [
        "## CRITICAL: Output Format",
        "",
        "Respond with a single JSON object and nothing else.",
        "Your first character must be `{`.",
        "Your last character must be `}`.",
        "Do not wrap the JSON in markdown code fences.",
        "Do not output any commentary, preamble, or explanation outside",
        "the JSON object.",
        "",
        "The JSON object must have exactly these fields:",
        "",
        schema_block,
        "",
        send_line,
    ]
    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────


def render_role_file(
    name: str,
    purpose: str,
    prompt_body: str,
    output_schema: Mapping[str, str],
    *,
    inports: Sequence[str] = DEFAULT_INPORTS,
    outports: Sequence[str] = DEFAULT_OUTPORTS,
    contract: str = DEFAULT_CONTRACT,
) -> str:
    """Render a DSL role.md file as a string.

    Parameters
    ----------
    name : str
        The role's identifier (e.g., ``"credibility_scorer"``). Becomes
        ``# Role: <name>``.
    purpose : str
        One-sentence description of what the role does. Used as the
        first body line for human readers.
    prompt_body : str
        The substantive prompt body — Claude-generated. Should describe
        the task, the input shape, and how to reason about it. Should
        NOT include output-format discipline (the wrapper appends that).
    output_schema : Mapping[str, str]
        Dict from output field name to short English description of the
        field's type and meaning. Example::

            {"score": "float in [0, 1]",
             "reasoning": "one or two sentences explaining the score"}
    inports : sequence of str, optional
        Inport names. Defaults to ``("in_",)``.
    outports : sequence of str, optional
        Outport names. Defaults to ``("out",)``.
    contract : str, optional
        DSL contract type. Defaults to ``"structured"``.

    Returns
    -------
    str
        The complete role.md file contents, ready to write to disk.
    """
    # Gallery convention: frontmatter ends with `---` directly
    # adjacent to the `# Role:` H1 (no blank line). All other blocks
    # get a blank line between them for readability.
    body_parts = [
        f"# Role: {name}",
        f"_{purpose}_",
        prompt_body.strip(),
        _render_output_discipline(output_schema, outports),
    ]
    body = "\n\n".join(body_parts)
    return f"{_render_frontmatter(contract)}\n{body}\n"


def create_agent_from_prompt(
    name: str,
    purpose: str,
    prompt_body: str,
    output_schema: Mapping[str, str],
    target_dir: Path,
    *,
    inports: Sequence[str] = DEFAULT_INPORTS,
    outports: Sequence[str] = DEFAULT_OUTPORTS,
    contract: str = DEFAULT_CONTRACT,
    overwrite: bool = False,
) -> Path:
    """Write a Claude-generated prompt to disk as a DSL role.md file.

    Parameters
    ----------
    name, purpose, prompt_body, output_schema, inports, outports,
    contract :
        See ``render_role_file``.
    target_dir : Path
        Directory to write the role.md into. Typically the ``roles/``
        directory of a gallery app. Must exist.
    overwrite : bool, optional
        If False (default), raises ``FileExistsError`` if the target
        file already exists. If True, overwrites silently.

    Returns
    -------
    Path
        The path to the written role.md file.

    Raises
    ------
    FileNotFoundError
        If ``target_dir`` does not exist.
    FileExistsError
        If the target file exists and ``overwrite`` is False.
    """
    target_dir = Path(target_dir)
    if not target_dir.is_dir():
        raise FileNotFoundError(
            f"target_dir does not exist: {target_dir}. "
            "Create it before calling create_agent_from_prompt."
        )
    role_path = target_dir / f"{name}.md"
    if role_path.exists() and not overwrite:
        raise FileExistsError(
            f"{role_path} already exists. Pass overwrite=True to replace."
        )
    contents = render_role_file(
        name=name,
        purpose=purpose,
        prompt_body=prompt_body,
        output_schema=output_schema,
        inports=inports,
        outports=outports,
        contract=contract,
    )
    role_path.write_text(contents)
    return role_path


# ── Notes on what's not yet handled ───────────────────────────────────
#
# 1. Multi-outport routing. The "Always send to <out>" convention is
#    correct for single-outport agents. Multi-outport agents (router
#    pattern, classifier with discard branch) need a `send_to` field
#    convention — DSL has one but the prompt language has to be
#    different. Handled when Claudette first generates a multi-outport
#    agent.
#
# 2. `{{include: file.md}}` interpolation. Some role files (e.g.,
#    job_hunter/matcher.md) interpolate a resume.md into the prompt.
#    Not in scope for the wrapper; Claude's prompt can include the
#    interpolation syntax verbatim and DSL will resolve it.
#
# 3. Per-instance AI overrides. office.md can say "X's AI is
#    claude_precise"; the role file itself doesn't need to know.
#    Wrapper doesn't touch this.
#
# 4. Python agents. This wrapper is for LLM agents (role.md). A
#    separate wrapper for Python agents (create_python_agent_from_spec)
#    will follow once we've validated this one on LLM agents.
