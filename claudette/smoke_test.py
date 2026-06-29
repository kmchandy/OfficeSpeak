"""
Claudette smoke test 1: end-to-end agent generation under option γ.

Tests the claim:
    Given a Pat-style English task description, Claudette (Claude with
    a structured-output meta-prompt) produces a JSON specification of
    an agent which the wrapper turns into a syntactically valid DSL
    role.md.

Steps:
    1. Send the meta-prompt + task description to Claude
    2. Parse Claude's JSON response into {name, purpose, prompt_body,
       output_schema}
    3. Pass to create_agent_from_prompt → writes role.md to a temp dir
    4. Print the resulting role file for human inspection
    5. Report pass/fail

What this test does NOT cover (intentionally):
    - Whether the generated agent runs correctly under DSL
    - Whether its output is substantively useful on real news data

Those are downstream tests (smoke tests 2 and 3). This one isolates
"does Claudette + wrapper produce a well-formed artifact?" so we
can debug the prompt-and-parse pipeline without confounding it with
DSL execution issues.

Requires: ANTHROPIC_API_KEY in the environment (uses dissyslab's
ClaudeBackend). Costs a few cents at most per run.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path
from textwrap import dedent

# Make the parent directory importable so `from claudette.wrapper`
# works regardless of whether this script is invoked as
# `python -m claudette.smoke_test` or `python claudette/smoke_test.py`.
_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR.parent))

# claudette package — wrapper we built and tested
from claudette.wrapper import create_agent_from_prompt


# ── Meta-prompt for Claudette ─────────────────────────────────────────
# This is the fixed prompt that establishes Claudette's role and the
# structured-output contract she emits under. Version 1 — will be
# iterated. The meta-prompt is itself the experimental artifact.

META_PROMPT = dedent("""\
    You are Claudette, an agent designer for a distributed
    sense-and-respond framework called DisSysLab (DSL). Your job is
    to design a new LLM-driven agent for a given task.

    DSL agents communicate via message passing. Each agent receives
    typed messages on input ports and emits typed messages on output
    ports. An agent's behaviour is defined by a natural-language
    prompt that processes one incoming message at a time.

    You will be given:
      - A task description in English (the kind of thing a non-coder
        user would write to describe what they want).

    You will produce:
      - A JSON object specifying the agent, with EXACTLY these
        fields:

        - "name":          short identifier (lowercase, underscores)
        - "purpose":       one-sentence summary of what the agent does
        - "prompt_body":   substantive English describing the task,
                           the input message shape, how to reason
                           about it, and what to produce. Write this
                           as if explaining the job to a thoughtful
                           collaborator.
        - "output_schema": a JSON object whose keys are output field
                           names and whose values are short English
                           descriptions of each field's type and
                           meaning. Example:
                             {"score": "float in [0, 1]; higher = more credible",
                              "reasoning": "one or two sentences explaining the score"}

    IMPORTANT — what NOT to include in prompt_body:
      - JSON output format rules ("respond with a single JSON object",
        "first character must be {", etc.)
      - "Always send to out" or routing instructions
      - YAML frontmatter
      - DSL-specific syntax

    All of that is added automatically by a deterministic wrapper. Your
    job is the *substantive* prompt — what the agent should do and how
    to reason about it. Trust the wrapper to handle framework
    conventions.

    Output discipline: respond with the JSON object and nothing else.
    First character must be {. Last character must be }. No markdown
    code fences. No commentary.
""")


# ── Example task — Pat-style description ──────────────────────────────

TASK_CREDIBILITY_SCORER = dedent("""\
    I want an agent that assesses the credibility of news articles.

    Given a news article — its title, its body text, and the name of
    the publication it appeared in — the agent should produce a
    numeric credibility score between 0 (clearly dubious) and 1
    (highly credible), along with a short reasoning explaining the
    score.

    The agent should consider:
      - The source's general reputation (established outlets vs
        unknown blogs).
      - The article's tone (measured and specific vs sensational and
        vague).
      - The presence of unverified or unsupported claims.

    I want the agent to be honest and calibrated. Most mainstream
    articles should fall in the 0.4-0.8 range. Scores above 0.9
    should be rare and justified; scores below 0.2 should be
    reserved for clear fabrication or extreme bias.
""")


# ── Call Claude ───────────────────────────────────────────────────────

# A pre-canned response simulating what Claude might produce. Used
# only when ANTHROPIC_API_KEY is missing — this lets the smoke test
# exercise the wrapper integration even without API access (useful
# in sandboxed dev environments and for CI). On any machine where
# the API key is set, the real Claude call runs instead.
MOCK_CLAUDE_RESPONSE = """\
{
  "name": "credibility_scorer",
  "purpose": "Score the credibility of a news article with reasoning.",
  "prompt_body": "You receive one news article at a time and assess its credibility.\\n\\nInput shape. Each article is a JSON object with these fields:\\n- \\"title\\"  — the headline (string)\\n- \\"body\\"   — the article text (string)\\n- \\"source\\" — the publication name (string)\\n\\nYour job. Produce a numeric credibility score in [0, 1] and a short reasoning string. Consider three signals when assigning the score:\\n\\n1. The source's general reputation. Established outlets with editorial oversight (major newspapers, public broadcasters) generally warrant higher scores than unknown blogs or partisan opinion sites. If the source is unfamiliar, weight your assessment toward the article's internal evidence instead.\\n\\n2. The article's tone and specificity. Measured prose with specific names, dates, and attributions warrants a higher score than sensational, vague, or emotionally charged language.\\n\\n3. The presence of unverified or unsupported claims. Articles that make strong claims without attribution to identifiable sources, or that repeat assertions without evidence, warrant lower scores.\\n\\nBe honest and calibrated. Most mainstream articles fall in the 0.4-0.8 range. Reserve scores above 0.9 for cases where you can specifically justify high confidence in every claim. Reserve scores below 0.2 for cases of clear fabrication, demonstrable falsehood, or extreme partisan distortion.",
  "output_schema": {
    "score": "float in [0, 1]; higher = more credible",
    "reasoning": "one or two sentences explaining the score, citing the specific signals (source, tone, claims) that drove it"
  }
}"""


def call_claude(system: str, user: str) -> str:
    """Use dissyslab's AnthropicBackend to get a completion.

    Falls back to a pre-canned mock response if ANTHROPIC_API_KEY is
    not set in the environment, so the smoke test can exercise the
    wrapper integration in sandboxed environments without API access.
    The mock is clearly labeled in the output.
    """
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  (No ANTHROPIC_API_KEY in env — using mock Claude response.)")
        print("  (Run on a machine with the key set to test against real Claude.)")
        return MOCK_CLAUDE_RESPONSE

    try:
        from dissyslab.backends.anthropic_backend import AnthropicBackend
    except ImportError as exc:
        raise SystemExit(
            "dissyslab not installed in this Python environment.\n"
            "Install it from your local checkout:\n"
            "    cd ~/Documents/DisSysLab && pip install -e .\n"
            "Then re-run this smoke test from any directory."
        ) from exc

    backend = AnthropicBackend()
    return backend.complete(system=system, user=user, temperature=0.2)


# ── Parse Claude's response ───────────────────────────────────────────

REQUIRED_FIELDS = ("name", "purpose", "prompt_body", "output_schema")


def parse_response(raw: str) -> dict:
    """Extract and validate the JSON object from Claude's response.

    Claude usually obeys the "first char {, last char }" discipline,
    but sometimes prepends prose. We extract the first balanced-
    braces region as a defence.
    """
    # Find first balanced JSON object.
    start = raw.find("{")
    if start == -1:
        raise ValueError(f"No JSON object found in response.\nFull response:\n{raw}")
    depth = 0
    end = -1
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end == -1:
        raise ValueError(f"Unbalanced braces in response.\nFull response:\n{raw}")
    blob = raw[start:end]
    try:
        obj = json.loads(blob)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"JSON parse failure: {exc}\nExtracted blob:\n{blob}"
        ) from exc

    # Validate required fields.
    missing = [f for f in REQUIRED_FIELDS if f not in obj]
    if missing:
        raise ValueError(
            f"Response missing required field(s): {missing}\n"
            f"Got fields: {list(obj.keys())}\nFull object:\n{obj}"
        )
    if not isinstance(obj["output_schema"], dict):
        raise ValueError(
            f"output_schema must be a dict, got {type(obj['output_schema'])}"
        )
    return obj


# ── Driver ────────────────────────────────────────────────────────────

def run_smoke_test(task: str) -> int:
    """Run the smoke test. Returns 0 on pass, 1 on fail."""
    print("=" * 70)
    print("CLAUDETTE SMOKE TEST 1 — agent generation under option γ")
    print("=" * 70)
    print()
    print("[1/5] Sending task to Claude via meta-prompt...")
    try:
        raw = call_claude(META_PROMPT, task)
    except SystemExit as exc:
        print(f"  FAIL: {exc}")
        return 1
    except Exception as exc:
        print(f"  FAIL: unexpected error from Claude call: {exc}")
        return 1
    print(f"  OK — received {len(raw)} chars of response")
    print()

    print("[2/5] Parsing Claude's structured response...")
    try:
        spec = parse_response(raw)
    except ValueError as exc:
        print(f"  FAIL: {exc}")
        return 1
    print(f"  OK — parsed spec with fields: {sorted(spec.keys())}")
    print(f"  name = {spec['name']!r}")
    print(f"  purpose = {spec['purpose']!r}")
    print(f"  output_schema keys = {sorted(spec['output_schema'].keys())}")
    print(f"  prompt_body length = {len(spec['prompt_body'])} chars")
    print()
    print("  --- Claudette's prompt_body (substantive content she wrote) ---")
    # Show the prompt_body indented so it's clearly distinguished from
    # the script's own output. This is the central artifact: the
    # substantive English prompt Claudette generated, before the
    # wrapper added any DSL boilerplate.
    for line in spec["prompt_body"].splitlines():
        print(f"  | {line}")
    print("  --- end Claudette's prompt_body ---")
    print()
    print("  --- Claudette's output_schema ---")
    for field, desc in spec["output_schema"].items():
        print(f"  | {field}: {desc}")
    print("  --- end Claudette's output_schema ---")
    print()

    # Persist the raw spec so Claudette's contribution is separately
    # inspectable later, not just embedded inside the wrapped role
    # file. The role.md is "spec + wrapper boilerplate"; the .spec.json
    # is "spec alone" — useful for comparing what Claudette produced
    # across runs or against alternative meta-prompts.
    persistent = Path(__file__).parent / "smoke_test_outputs"
    persistent.mkdir(exist_ok=True)
    spec_path = persistent / f"{spec['name']}.spec.json"
    spec_path.write_text(json.dumps(spec, indent=2))
    print(f"  raw spec saved to {spec_path}")
    print()

    print("[3/5] Wrapping into a DSL role file...")
    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = Path(tmpdir)
        try:
            role_path = create_agent_from_prompt(
                name=spec["name"],
                purpose=spec["purpose"],
                prompt_body=spec["prompt_body"],
                output_schema=spec["output_schema"],
                target_dir=target_dir,
            )
        except Exception as exc:
            print(f"  FAIL: wrapper raised: {exc}")
            return 1
        print(f"  OK — role file written to {role_path}")
        print()

        print("[4/5] Inspecting the resulting role file...")
        contents = role_path.read_text()
        print()
        print("-" * 70)
        print(contents)
        print("-" * 70)
        print()

        # Persist for later inspection (the tmpdir is about to vanish).
        persistent = Path(__file__).parent / "smoke_test_outputs"
        persistent.mkdir(exist_ok=True)
        out_path = persistent / f"{spec['name']}.md"
        out_path.write_text(contents)
        print(f"  Also saved to {out_path}")
        print()

    print("[5/5] Sanity checks on the generated file...")
    checks = [
        ("starts with frontmatter", contents.startswith("---\ncontract: structured\n---")),
        ("has role header", f"# Role: {spec['name']}" in contents),
        ("has purpose line", f"_{spec['purpose']}_" in contents),
        ("has output discipline block", "CRITICAL: Output Format" in contents),
        ("mentions schema fields", all(
            f"`{field}`" in contents for field in spec["output_schema"]
        )),
        ("has send-to line", "Always send to out" in contents or "send_to" in contents),
    ]
    all_passed = True
    for name, passed in checks:
        marker = "✓" if passed else "✗"
        print(f"  {marker} {name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("PASS — Claudette + wrapper produced a well-formed role file.")
        print()
        print("Next step (smoke test 2): drop this role file into a tiny test")
        print("office and verify it produces sensible output on a real article.")
        return 0
    else:
        print("FAIL — some sanity checks did not pass. Inspect the file above.")
        return 1


if __name__ == "__main__":
    sys.exit(run_smoke_test(TASK_CREDIBILITY_SCORER))
