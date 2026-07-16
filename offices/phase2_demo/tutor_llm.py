"""Phase 2 — the tutor, with the grader as a LANGUAGE-MODEL worker (base case).

Same office as tutor.py, but the CHECKER's judgement — "is this answer right,
and what should we say to the kid?" — is done by an LLM instead of an exact
string match. Everything else is unchanged: the sources, the sinks, the BANK
and PROGRESS records, and PLANNER's sequencing are ordinary provided code that
nobody writes by hand. Only the thinking part is a model, given a job
description (the system prompt).

Because the LLM worker meets the identical contract
``step(message, state) -> [(outbox, message), ...]``, the wiring and the
diagram are exactly the same as tutor.py. The visible difference: the kid can
now write "one", "six", or "two quarters" and be graded correctly — an
exact-match grader would mark all three wrong — and the feedback is written
fresh for each answer.

Needs an Anthropic API key (ANTHROPIC_API_KEY). Run:  python tutor_llm.py
"""
from __future__ import annotations
from collections import deque

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
# How the kid types their answers — deliberately in words / decimals / equivalent
# forms an exact-match grader would reject. Q1 is a genuine mistake.
KID_ANSWERS = ["one", "1", "six", "two quarters"]   # -> correct, WRONG, correct, correct


# ── BANK: a record (keeper). Holds the question bank; PLANNER reads it. ───────
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


# ── CHECKER: the LLM worker. Grades the answer and writes the feedback. ───────
GRADER_SYSTEM = (
    "You are a warm, encouraging tutor for a young child learning fractions. "
    "You are given the correct answer to a question and what the child wrote. "
    "Accept ANY mathematically equivalent form as correct — for the answer "
    "'1/2', the child writing 'one half', '0.5', '2/4', or 'two quarters' are "
    "all correct. Decide if the child is right, and write ONE short, kind "
    "sentence of feedback for them (a gentle hint if they are wrong). Reply "
    'with ONLY a JSON object: {"correct": true or false, "feedback": "<one '
    'short sentence>"}.'
)


def _backend():
    # Low temperature: grading should be steady, not creative.
    return get_backend("claude_precise")


def checker_step(msg, state):
    """Fan-in of grading keys (from PLANNER) and answers (from the kid).

    Same buffering as the Python tutor — pair each answer with its question —
    but the grade itself is an LLM call.
    """
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
            f"Child wrote: {given}")
    raw = _backend().complete(system=GRADER_SYSTEM, user=user, max_tokens=120)
    obj = _parse_send(raw)
    correct = bool(obj.get("correct"))
    fb = obj.get("feedback") or ("Correct!" if correct else "Not quite — try again.")
    state["question"] = None
    state["key"] = None
    return [("screen", {"kind": "feedback", "text": fb}),
            ("out",    {"kind": "outcome", "correct": correct})]


# ── PLANNER: the coach. Ask-and-wait via state, never blocking. ──────────────
def planner_step(msg, state):
    k = msg["kind"]
    if k == "start":
        return [("to_bank", {"n": 0})]
    if k == "question":
        state["current"] = msg
        return [("to_screen", {"kind": "show", "text": msg["text"]}),
                ("to_checker", {"kind": "key", "question": msg["text"],
                                "answer": msg["answer"]})]
    if k == "outcome":
        state["results"].append(msg["correct"])
        sends = [("to_progress", {"kind": "update", "correct": msg["correct"]})]
        state["n"] += 1
        if state["n"] < len(QUESTIONS):
            sends.append(("to_bank", {"n": state["n"]}))
        else:
            sends.append(("to_progress", {"kind": "read"}))
        return sends
    if k == "progress":
        return [("to_reporter", {"kind": "final", "mastery": msg["mastery"],
                                 "seen": msg["seen"], "results": list(state["results"])})]
    return []


# ── REPORTER: summary to the screen, report to the file. ─────────────────────
def reporter_step(msg, state):
    results = msg["results"]
    score = f"{sum(results)}/{len(results)}"
    return [("screen", {"kind": "summary", "text": f"Session done — you got {score}. Nice work!"}),
            ("file",   {"kind": "report", "mastery": msg["mastery"],
                        "questions_seen": msg["seen"], "score": score})]


class Feed:
    def __init__(self, data): self.data = data; self.i = 0
    def run(self):
        if self.i >= len(self.data): return None
        v = self.data[self.i]; self.i += 1
        return v


def build():
    screen, report = [], []
    net = Network(
        name="tutor_llm",
        blocks={
            "SESSION":  Source(fn=Feed([{"kind": "start"}]).run, name="SESSION", interval=0.02),
            "ANSWERS":  Source(fn=Feed([{"kind": "answer", "value": a} for a in KID_ANSWERS]).run,
                               name="ANSWERS", interval=0.02),
            "BANK":     Worker(step=bank_step, outports=["reply"], name="BANK",
                               state={"questions": QUESTIONS}),
            "PROGRESS": Worker(step=progress_step, outports=["reply"], name="PROGRESS",
                               state={"mastery": 0, "seen": 0}),
            "CHECKER":  Worker(step=checker_step, outports=["out", "screen"], name="CHECKER",
                               state={"key": None, "question": None, "pending": deque()}),
            "PLANNER":  Worker(step=planner_step,
                               outports=["to_bank", "to_checker", "to_screen",
                                         "to_progress", "to_reporter"],
                               name="PLANNER", state={"n": 0, "current": None, "results": []}),
            "REPORTER": Worker(step=reporter_step, outports=["screen", "file"], name="REPORTER"),
            "SCREEN":   Sink(fn=screen.append, name="SCREEN"),
            "PARENT_REPORT": Sink(fn=report.append, name="PARENT_REPORT"),
        },
        connections=[
            ("SESSION",  "out_",        "PLANNER",  "in_"),
            ("ANSWERS",  "out_",        "CHECKER",  "in_"),
            ("PLANNER",  "to_bank",     "BANK",     "in_"),
            ("BANK",     "reply",       "PLANNER",  "in_"),
            ("PLANNER",  "to_progress", "PROGRESS", "in_"),
            ("PROGRESS", "reply",       "PLANNER",  "in_"),
            ("PLANNER",  "to_checker",  "CHECKER",  "in_"),
            ("CHECKER",  "out",         "PLANNER",  "in_"),
            ("CHECKER",  "screen",      "SCREEN",   "in_"),
            ("PLANNER",  "to_screen",   "SCREEN",   "in_"),
            ("PLANNER",  "to_reporter", "REPORTER", "in_"),
            ("REPORTER", "screen",      "SCREEN",   "in_"),
            ("REPORTER", "file",        "PARENT_REPORT", "in_"),
        ],
    )
    net._screen = screen; net._report = report
    return net


if __name__ == "__main__":
    net = build()
    net.run_network()
    print("\n=== tutor (LLM grader) — what the kid saw on SCREEN ===")
    for m in net._screen:
        print(f"  [{m['kind'].upper()}] {m['text']}")
    print("\n=== parent report file ===")
    for r in net._report:
        print("  ", r)
