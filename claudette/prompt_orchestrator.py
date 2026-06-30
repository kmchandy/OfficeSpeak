"""
claudette/prompt_orchestrator.py — Stage C of NoT.

Given a graph dict, generate one role.md file per vertex.

For each vertex the orchestrator:
  1. Builds a per-vertex prompt body (either by calling Claude or via
     a deterministic template).
  2. Calls `create_agent_from_prompt` (from wrapper.py) to write
     `<app_dir>/roles/<role_name>.md`.

Two modes:
  - LLM mode (`use_llm=True`): one Claude call per vertex.
  - Template mode (`use_llm=False`): purely deterministic.

Default behaviour: LLM mode iff ANTHROPIC_API_KEY is set in the
environment, otherwise template mode. Template mode lets the end-to-end
pipeline run in sandboxed / offline environments — the resulting agents
have less-tuned prompts but the office still compiles and runs.

The role-file naming convention matches DSL's:
  <app_dir>/roles/<role_name>.md
where <role_name> is the vertex's role (e.g., severity_classifier),
not the agent name (V0). DSL looks up role files by role name.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from textwrap import dedent
from typing import Optional

# Make the parent directory importable when invoked as `python claudette/prompt_orchestrator.py`
_THIS_DIR = Path(__file__).resolve().parent
if str(_THIS_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR.parent))

from claudette.wrapper import create_agent_from_prompt


# --------------------------------------------------------------------------- #
# Per-vertex meta-prompt (used in LLM mode)                                   #
# --------------------------------------------------------------------------- #


PER_VERTEX_META_PROMPT = dedent("""\
    You are designing one agent in a multi-agent sense-and-respond
    system built on DisSysLab (DSL). Each agent reads one JSON message
    at a time, computes one field, and forwards the full message
    (with that field added or updated) downstream.

    You will be given the agent's role and contract. Produce a JSON
    object with EXACTLY these fields:

      - "name":          short identifier (lowercase, underscores).
                         For your output, this MUST equal the role name
                         you are given below — do not invent a new name.
      - "purpose":       one-sentence summary (you may use the purpose
                         line you are given, or rephrase).
      - "prompt_body":   substantive English describing the task, what
                         to read from the message, and how to reason
                         about it. DO NOT include JSON output
                         instructions or routing instructions; the
                         wrapper adds those.
      - "output_schema": a JSON object with ONE key — the `enriches`
                         field — whose value is a short English
                         description of the field's type and meaning.

    If the vertex is marked CYCLIC, include a sentence in prompt_body
    noting that the message may already contain the `enriches` field
    from a previous iteration, and that the agent should treat any
    previously-set value as feedback and produce a refined value.

    Output discipline: respond with the JSON object and nothing else.
    First character must be `{`. Last character must be `}`. No
    markdown code fences. No commentary.
""")


def _vertex_brief(vertex: dict) -> str:
    """Format the per-vertex inputs into a user message for Claude."""
    cyclic_note = (
        "CYCLIC: yes (this vertex sits on a feedback loop; messages may "
        "arrive multiple times)\n"
        if vertex.get("cyclic")
        else ""
    )
    reads_str = (
        ", ".join(f"`{r}`" for r in vertex["reads"])
        if vertex["reads"]
        else "(the agent may inspect the whole message)"
    )
    return dedent(f"""\
        Role name (use this as the JSON 'name'): {vertex['role']}
        Verb phrase: {vertex.get('verb_phrase', vertex['role'])}
        Purpose line: {vertex['purpose']}
        Reads (input fields): {reads_str}
        Enriches (output field): `{vertex['enriches']}`
        {cyclic_note}
        Produce the JSON spec for this agent.
    """)


# --------------------------------------------------------------------------- #
# Template fallback (used when no API key)                                    #
# --------------------------------------------------------------------------- #


def _template_spec(vertex: dict) -> dict:
    """Build a deterministic agent spec without calling an LLM.

    Produces a workable but generic prompt body. Good enough for the
    end-to-end pipeline to run; not as tuned as a Claude-generated body.
    """
    role = vertex["role"]
    enriches = vertex["enriches"]
    reads = vertex["reads"]
    verb_phrase = vertex.get("verb_phrase", role)
    cyclic = vertex.get("cyclic", False)
    outports = vertex.get("outports") or []

    if reads:
        read_lines = "\n".join(f"- `{r}` — the field named in the message" for r in reads)
        read_intro = (
            f"You receive a JSON message that contains the following "
            f"field(s):\n\n{read_lines}\n"
        )
    else:
        read_intro = "You receive a JSON message. Inspect whatever fields are present.\n"

    body_parts = [
        read_intro,
        f"Your task: {verb_phrase}. Specifically, compute a value for "
        f"the field named `{enriches}` and add it to the message. "
        "Forward the full message (with all other fields preserved).",
    ]
    if cyclic:
        body_parts.append(
            f"Note: this agent sits on a feedback loop. On a re-entry "
            f"the message may already contain `{enriches}` from a "
            f"previous iteration. Treat any previously-set value as "
            f"feedback and produce a refined value."
        )

    if len(outports) > 1:
        # Router vertex — describe the routing decision.
        # The condition text isn't carried through the graph, so the
        # template falls back to a generic instruction. (LLM mode will
        # do better because the per-vertex prompt explicitly mentions
        # the conditions.)
        port_list = ", ".join(f"`{p}`" for p in outports)
        body_parts.append(
            f"This vertex is a router with multiple outports ({port_list}). "
            f"In addition to setting `{enriches}`, you must decide which "
            f"outport this message should leave on. Inspect the message "
            f"fields (especially any classification-style fields set by "
            f"earlier agents) and set the `send_to` field of your output "
            f"to one of the outport names listed."
        )

    return {
        "name": role,
        "purpose": vertex["purpose"],
        "prompt_body": "\n\n".join(body_parts),
        "output_schema": {
            enriches: f"value of `{enriches}` — see prompt above for semantics"
        },
    }


# --------------------------------------------------------------------------- #
# LLM call (uses dissyslab's AnthropicBackend; matches smoke_test.py)         #
# --------------------------------------------------------------------------- #


def _call_claude(system: str, user: str) -> str:
    """Call Claude via dissyslab's AnthropicBackend."""
    try:
        from dissyslab.backends.anthropic_backend import AnthropicBackend
    except ImportError as exc:
        raise RuntimeError(
            "dissyslab not installed; cannot use LLM mode. "
            "Install from local checkout: cd ~/Documents/DisSysLab && pip install -e ."
        ) from exc
    backend = AnthropicBackend()
    return backend.complete(system=system, user=user, temperature=0.2)


def _parse_llm_response(raw: str, expected_role: str) -> dict:
    """Extract and validate the JSON spec from Claude's response."""
    start = raw.find("{")
    if start == -1:
        raise ValueError(f"No JSON object in response: {raw[:200]!r}...")
    depth = 0
    end = -1
    for i in range(start, len(raw)):
        c = raw[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        raise ValueError(f"Unbalanced braces in response: {raw[:200]!r}...")
    obj = json.loads(raw[start:end])

    for field in ("name", "purpose", "prompt_body", "output_schema"):
        if field not in obj:
            raise ValueError(f"Missing field {field!r} in response: {list(obj.keys())}")
    if not isinstance(obj["output_schema"], dict):
        raise ValueError(f"output_schema must be a dict, got {type(obj['output_schema'])}")
    # Enforce the role-name == name invariant so role files match office.md
    if obj["name"] != expected_role:
        # Claude sometimes invents a different name; coerce it
        obj["name"] = expected_role
    return obj


def _llm_spec(vertex: dict) -> dict:
    raw = _call_claude(PER_VERTEX_META_PROMPT, _vertex_brief(vertex))
    return _parse_llm_response(raw, expected_role=vertex["role"])


# --------------------------------------------------------------------------- #
# Public API                                                                  #
# --------------------------------------------------------------------------- #


def orchestrate(
    graph: dict,
    target_dir: Path,
    *,
    use_llm: Optional[bool] = None,
    overwrite: bool = False,
    verbose: bool = True,
) -> list[Path]:
    """Generate role.md files for every vertex in the graph.

    Parameters
    ----------
    graph : dict
        Graph produced by claudette/parser.py.
    target_dir : Path
        App directory. Role files are written to <target_dir>/roles/.
    use_llm : bool or None
        True: call Claude per vertex.
        False: use deterministic templates.
        None (default): auto-detect — LLM iff ANTHROPIC_API_KEY is set.
    overwrite : bool
        If True, overwrite existing role files. If False, raise on conflict.
    verbose : bool
        If True, print progress to stderr.

    Returns
    -------
    list[Path]
        Paths to the generated role.md files.
    """
    target_dir = Path(target_dir)
    roles_dir = target_dir / "roles"
    roles_dir.mkdir(parents=True, exist_ok=True)

    if use_llm is None:
        use_llm = bool(os.environ.get("ANTHROPIC_API_KEY"))

    mode = "LLM (Claude)" if use_llm else "template (no LLM)"
    if verbose:
        print(
            f"[orchestrator] {len(graph['vertices'])} vertices, mode: {mode}",
            file=sys.stderr,
        )

    written: list[Path] = []
    for v in graph["vertices"]:
        if use_llm:
            spec = _llm_spec(v)
        else:
            spec = _template_spec(v)

        # If the vertex has named outports (router), declare them in
        # the role file too so DSL's office<->role check passes.
        outports = v.get("outports") or ["out"]
        path = create_agent_from_prompt(
            name=spec["name"],
            purpose=spec["purpose"],
            prompt_body=spec["prompt_body"],
            output_schema=spec["output_schema"],
            target_dir=roles_dir,
            outports=outports,
            overwrite=overwrite,
        )
        written.append(path)
        if verbose:
            print(
                f"[orchestrator] wrote {path.name} (vertex {v['id']}, role {v['role']})",
                file=sys.stderr,
            )

    return written


# --------------------------------------------------------------------------- #
# CLI                                                                         #
# --------------------------------------------------------------------------- #


def _main(argv: Optional[list[str]] = None) -> int:
    import argparse
    import yaml

    p = argparse.ArgumentParser(
        description="Generate role.md files from a graph YAML."
    )
    p.add_argument("graph", help="Path to graph YAML")
    p.add_argument("target_dir", help="App directory (role files go to <dir>/roles/)")
    p.add_argument("--llm", action="store_true", help="Force LLM mode")
    p.add_argument("--no-llm", action="store_true", help="Force template mode")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing role files")
    args = p.parse_args(argv)

    graph = yaml.safe_load(Path(args.graph).read_text())

    use_llm = None
    if args.llm:
        use_llm = True
    if args.no_llm:
        use_llm = False

    paths = orchestrate(
        graph,
        Path(args.target_dir),
        use_llm=use_llm,
        overwrite=args.overwrite,
    )
    for p in paths:
        print(p)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
