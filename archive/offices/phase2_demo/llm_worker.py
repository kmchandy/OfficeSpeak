"""Phase 2 — the LLM worker host (the REAL model, not a stub).

Turns a language model into a worker that meets the SAME uniform contract as
a Python worker:

    step(message, state) -> [(outbox, message), ...]

A worker built here is a pure function of (message, state): it

  1. renders the incoming message into a prompt   (input adapter),
  2. asks the model to pick ONE outbox + produce the outgoing text,
  3. parses and VALIDATES the reply into {send_to, text}  (output adapter),

and returns [(send_to, text)]. It never calls send()/recv() and never
blocks — the runtime does the I/O, exactly as for a Python worker. Because
an LLM worker meets the identical contract and wiring, it is swappable with
a Python worker: the office does not change when the body's implementation
does.

The model is reached through DisSysLab's Backend interface
(``backend.complete(system=..., user=...)``), so any registered backend —
Claude, Qwen, GPT, Gemini, or a local SLM — drops in unchanged. This is the
real thing: triage_swap.py used a keyless canned stub to prove the contract;
here get_backend() returns a live provider (Claude by default).
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, List, Optional, Sequence, Tuple

from dissyslab.backends import Backend, get_backend


# A generic router system prompt. An office can pass its own `system` to
# make the worker do something more specific than pure routing.
DEFAULT_SYSTEM = (
    "You are a router inside a message-passing office. You are given one "
    "message and a fixed list of outboxes. Choose EXACTLY ONE outbox that "
    "the message should be sent to. Reply with NOTHING but a single JSON "
    'object of the form {"send_to": "<one of the outboxes>", "text": <the '
    "outgoing message>}. No explanation, no markdown fences."
)


def _default_render(msg: Any, outboxes: Sequence[str]) -> str:
    """Turn (message, outboxes) into the user prompt."""
    shown = msg if isinstance(msg, str) else json.dumps(msg)
    return f"Outboxes: {list(outboxes)}\nMessage: {shown}"


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_send(raw: str) -> dict:
    """Extract the {send_to, text} object from the model's reply.

    Tolerates the two things real models do that a stub never would:
    wrapping the JSON in ```markdown fences``` and adding stray prose
    around it. Raises ValueError if no JSON object can be found.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = re.sub(r"^\s*json\s*", "", text, flags=re.IGNORECASE)
    match = _JSON_RE.search(text)
    if not match:
        raise ValueError(f"LLM reply contained no JSON object: {raw!r}")
    return json.loads(match.group(0))


def make_llm_step(
    *,
    outboxes: Sequence[str],
    system: str = DEFAULT_SYSTEM,
    render: Callable[[Any, Sequence[str]], str] = _default_render,
    backend: Optional[Backend] = None,
    backend_name: Optional[str] = None,
    model: Optional[str] = None,
    max_tokens: int = 256,
) -> Callable[[Any, dict], List[Tuple[str, Any]]]:
    """Build an LLM worker body meeting the uniform worker contract.

    Args:
        outboxes:     the worker's outbox names; the model must choose one.
        system:       system prompt (persona + output-format instructions).
        render:       (msg, outboxes) -> user prompt string.
        backend:      an explicit Backend instance (mainly for tests). If
                      None, resolved lazily from `backend_name` / DSL_BACKEND
                      / the "anthropic" default on the first call — so a
                      missing API key surfaces when the office runs, not when
                      it is built.
        backend_name: name passed to get_backend() (e.g. "claude_precise").
        model:        optional model id override for this worker.
        max_tokens:   response cap.

    Returns:
        step(message, state) -> [(send_to, text)]
    """
    outbox_list = list(outboxes)
    resolved: Optional[Backend] = backend

    def step(msg: Any, state: dict) -> List[Tuple[str, Any]]:
        nonlocal resolved
        if resolved is None:
            resolved = get_backend(backend_name)
        user = render(msg, outbox_list)
        raw = resolved.complete(
            system=system, user=user, max_tokens=max_tokens, model=model
        )
        obj = _parse_send(raw)
        send_to, text = obj.get("send_to"), obj.get("text")
        if send_to not in outbox_list:
            raise ValueError(
                f"LLM chose invalid outbox {send_to!r}; allowed {outbox_list}"
            )
        return [(send_to, text)]

    return step
