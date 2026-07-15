"""Keyless tests for the LLM worker's output adapter (no API key needed).

Uses a fake Backend that returns canned strings, so we can check the parse +
validate logic against the messy things real models actually emit — bare
JSON, ```json fenced``` JSON, and JSON buried in prose — plus the guard that
rejects an outbox the office never declared.

Run:  python test_llm_worker.py      (prints PASS/FAIL, exits nonzero on fail)
"""
from __future__ import annotations

import json

from llm_worker import make_llm_step


class FakeBackend:
    """A Backend that ignores the prompt and returns a preset reply."""
    def __init__(self, reply):
        self.reply = reply
        self.calls = 0

    def complete(self, *, system, user, max_tokens=256, temperature=1.0, model=None):
        self.calls += 1
        return self.reply


def _run(reply, outboxes=("urgent", "normal")):
    step = make_llm_step(outboxes=outboxes, backend=FakeBackend(reply))
    return step({"text": "hi"}, {})


def main():
    checks = []

    # 1. Bare JSON.
    out = _run('{"send_to": "urgent", "text": "hi"}')
    checks.append(("bare json", out == [("urgent", "hi")]))

    # 2. Markdown-fenced JSON with a language tag.
    out = _run('```json\n{"send_to": "normal", "text": "hi"}\n```')
    checks.append(("fenced json", out == [("normal", "hi")]))

    # 3. JSON embedded in prose.
    out = _run('Sure! Here you go: {"send_to": "urgent", "text": "hi"} — done.')
    checks.append(("prose + json", out == [("urgent", "hi")]))

    # 4. Invalid outbox must raise (protects the office from a bad label).
    try:
        _run('{"send_to": "archive", "text": "hi"}')
        checks.append(("reject bad outbox", False))
    except ValueError:
        checks.append(("reject bad outbox", True))

    # 5. No JSON at all must raise.
    try:
        _run("I could not decide.")
        checks.append(("reject non-json", False))
    except ValueError:
        checks.append(("reject non-json", True))

    ok = all(passed for _, passed in checks)
    for name, passed in checks:
        print(f"  [{'PASS' if passed else 'FAIL'}] {name}")
    print("all passed:", ok)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
