"""Phase 2 — the LLM tutor a real student can USE, live, at the terminal.

tutor_llm.py replays a canned session (the answers are baked in). This version
lets a child sit down and actually type answers: it shows a question, waits for
them to type, an LLM grades what they wrote (accepting "one", "1/2", "two
quarters", …), gives a kind line of feedback, and moves on. At the end it prints
an encouraging summary and saves a parent report.

It is the SAME office as tutor_llm.py, with the two I/O ends swapped:

  * the canned ANSWERS source and the print-only SCREEN sink are replaced by ONE
    interactive TERMINAL worker that both shows text and reads the student's
    typed answer;
  * every line shown to the student is routed through PLANNER, so the question /
    feedback / next-question order is deterministic (no screen races).

    SESSION ─start─▶ PLANNER ──ask/say──▶ TERMINAL ──answer──▶ CHECKER(★LLM)
                       ▲  │                                   │
                       │  ├─key──────────────────────────────┘ (grades)
                       │  ├─to_bank/to_progress──▶ BANK / PROGRESS (records)
                       │  └─report──▶ PARENT_REPORT (file)
                       └───────────── graded ◀── CHECKER

RUN IT IN A REAL TERMINAL (so the child can type):

    python tutor_interactive.py

Needs an Anthropic API key in the environment (ANTHROPIC_API_KEY). Running it
without a terminal (piped/no stdin) still works — each unanswered prompt is
treated as a blank answer — so it never hangs.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

from dissyslab.network import Network
from dissyslab.blocks.source import Source
from dissyslab.blocks.sink import Sink
from dissyslab.backends import get_backend

from worker import Worker
from llm_worker import _parse_send        # tolerant JSON extractor (fences/prose)


QUESTIONS = [
    {"id": 0, "text": "1/2 + 1/2 = ?", "answer": "1"},
    {"id": 1, "text": "1/4 + 1/4 = ?", "answer": "1/2"},
    {"id": 2, "text": "2/3 of 9 = ?",  "answer": "6"},
    {"id": 3, "text": "3/4 - 1/4 = ?", "answer": "1/2"},
]
REPORT_FILE = Path(__file__).with_name("parent_report.json")


# ── BANK: a record (keeper). Holds the questions; PLANNER reads it. ───────────
def bank_step(msg, state):
    n = msg["n"]
    q = state["questions"][n] if n < len(state["questions"]) else {"id": None}
    return [("reply", {"kind": "question", **q})]


# ── PROGRESS: a record (keeper). Read AND written by PLANNER only -> no gate. ──
def progress_step(msg, state):
    if msg["kind"] == "update":
        state["seen"] += 1
        if msg["correct"]:
            state["mastery"] += 1
        return []
    return [("reply", {"kind": "progress", "mastery": state["mastery"],
                       "seen": state["seen"]})]


# ── CHECKER: the LLM worker. Grades the typed answer, writes the feedback. ────
GRADER_SYSTEM = (
    "You are a warm, encouraging tutor for a young child learning fractions. "
    "You are given a question, the correct answer, and what the child typed. "
    "Accept ANY mathematically equivalent form as correct — for the answer "
    "'1/2', the child writing 'one half', '0.5', '2/4', or 'two quarters' are "
    "all correct. Decide if the child is right, and write ONE short, kind "
    "sentence of feedback for them (a gentle hint if they are wrong; do NOT give "
    'away the answer on the first miss). Reply with ONLY a JSON object: '
    '{"correct": true or false, "feedback": "<one short sentence>"}.'
)


def _backend():
    return get_backend("claude_precise")     # steady, low-temperature grading


def checker_step(msg, state):
    if msg["kind"] == "key":
        state["question"] = msg["question"]
        state["key"] = msg["answer"]
        if state["pending"]:
            return _grade(state, state["pending"].popleft())
        return []
    # kind == "answer"
    if state["key"] is not None:
        return _grade(state, msg["value"])
    state["pending"].append(msg["value"])
    return []


def _grade(state, given):
    user = (f"Question: {state['question']}\n"
            f"Correct answer: {state['key']}\n"
            f"Child typed: {given!r}")
    raw = _backend().complete(system=GRADER_SYSTEM, user=user, max_tokens=120)
    obj = _parse_send(raw)
    correct = bool(obj.get("correct"))
    fb = obj.get("feedback") or ("Correct!" if correct else "Not quite — try again.")
    state["question"] = None
    state["key"] = None
    return [("graded", {"kind": "graded", "correct": correct, "feedback": fb})]


# ── TERMINAL: the interactive console (shows text, reads the typed answer). ───
def terminal_step(msg, state):
    if msg["kind"] == "ask":
        print(f"\n  {msg['text']}")
        try:
            value = input("  your answer: ")
        except EOFError:                     # no terminal (piped/empty stdin)
            value = ""
        return [("answer", {"kind": "answer", "value": value})]
    # kind == "say" — feedback or summary; show it, read nothing.
    print(f"  {msg['text']}")
    return []


# ── PLANNER: the coach AND the single driver of the screen (keeps it ordered). ─
def planner_step(msg, state):
    k = msg["kind"]
    if k == "start":
        return [("to_bank", {"n": 0})]
    if k == "question":
        return [("to_checker", {"kind": "key", "question": msg["text"], "answer": msg["answer"]}),
                ("to_terminal", {"kind": "ask", "text": msg["text"]})]
    if k == "graded":
        state["results"].append(msg["correct"])
        sends = [("to_terminal", {"kind": "say", "text": msg["feedback"]}),
                 ("to_progress", {"kind": "update", "correct": msg["correct"]})]
        state["n"] += 1
        if state["n"] < len(QUESTIONS):
            sends.append(("to_bank", {"n": state["n"]}))
        else:
            sends.append(("to_progress", {"kind": "read"}))
        return sends
    if k == "progress":
        score = f"{sum(state['results'])}/{len(state['results'])}"
        report = {"kind": "report", "mastery": msg["mastery"],
                  "questions_seen": msg["seen"], "score": score}
        return [("to_terminal", {"kind": "say", "text": f"\nSession done — you got {score}. Nice work!"}),
                ("to_report", report)]
    return []


def _one_start():
    """Source body: emit a single 'start', then stop."""
    if _one_start.done:
        return None
    _one_start.done = True
    return {"kind": "start"}
_one_start.done = False


def build():
    saved = []
    net = Network(
        name="tutor_interactive",
        blocks={
            "SESSION":  Source(fn=_one_start, name="SESSION", interval=0.02),
            "BANK":     Worker(step=bank_step, outports=["reply"], name="BANK",
                               state={"questions": QUESTIONS}),
            "PROGRESS": Worker(step=progress_step, outports=["reply"], name="PROGRESS",
                               state={"mastery": 0, "seen": 0}),
            "CHECKER":  Worker(step=checker_step, outports=["graded"], name="CHECKER",
                               state={"key": None, "question": None, "pending": deque()}),
            "TERMINAL": Worker(step=terminal_step, outports=["answer"], name="TERMINAL"),
            "PLANNER":  Worker(step=planner_step,
                               outports=["to_bank", "to_checker", "to_terminal",
                                         "to_progress", "to_report"],
                               name="PLANNER", state={"n": 0, "results": []}),
            "PARENT_REPORT": Sink(fn=saved.append, name="PARENT_REPORT"),
        },
        connections=[
            ("SESSION",  "out_",        "PLANNER",  "in_"),
            ("PLANNER",  "to_bank",     "BANK",     "in_"),
            ("BANK",     "reply",       "PLANNER",  "in_"),
            ("PLANNER",  "to_progress", "PROGRESS", "in_"),
            ("PROGRESS", "reply",       "PLANNER",  "in_"),
            ("PLANNER",  "to_checker",  "CHECKER",  "in_"),
            ("TERMINAL", "answer",      "CHECKER",  "in_"),
            ("CHECKER",  "graded",      "PLANNER",  "in_"),
            ("PLANNER",  "to_terminal", "TERMINAL", "in_"),
            ("PLANNER",  "to_report",   "PARENT_REPORT", "in_"),
        ],
    )
    net._saved = saved
    return net


if __name__ == "__main__":
    _one_start.done = False
    print("=" * 56)
    print("  Fractions practice — type your answer and press Enter.")
    print("=" * 56)
    net = build()
    net.run_network()
    if net._saved:
        REPORT_FILE.write_text(json.dumps(net._saved[-1], indent=2))
        print(f"\n  (parent report saved to {REPORT_FILE.name})")
