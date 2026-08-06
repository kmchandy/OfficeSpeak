"""Phase 2 — the tutor office, run end to end. Exercises the hard runtime shapes:

  * records (BANK, PROGRESS) implemented as single-inbox keeper Workers. Each is
    touched by only ONE worker (PLANNER), so single-inbox serialization keeps them
    consistent — NO gate.
  * a multi-outbox worker (PLANNER: to_bank, to_checker, to_screen, to_progress,
    to_reporter) and a 2-outbox CHECKER / REPORTER.
  * fan-in inboxes (PLANNER.in gets start + bank replies + progress reply + outcomes;
    CHECKER.in gets keys + answers; SCREEN.in gets shows + feedback + summary).
  * ask-and-wait (PLANNER <-> BANK, PLANNER <-> PROGRESS) done with STATE, not blocking:
    every worker is still the pure contract  step(msg, state) -> [(outbox, message)].

There are no coordinators here (the tutor needs none), so this office is unaffected
by the coordinator-termination bug (#47).

Run:  python tutor.py
"""
from __future__ import annotations
from collections import deque

from dissyslab.network import Network
from dissyslab.blocks.source import Source
from dissyslab.blocks.sink import Sink

from worker import Worker


QUESTIONS = [
    {"id": 0, "text": "1/2 + 1/2 = ?",  "answer": "1"},
    {"id": 1, "text": "1/4 + 1/4 = ?",  "answer": "1/2"},
    {"id": 2, "text": "2/3 of 9 = ?",   "answer": "6"},
    {"id": 3, "text": "3/4 - 1/4 = ?",  "answer": "1/2"},
]
KID_ANSWERS = ["1", "wrong", "6", "1/2"]         # correct, wrong, correct, correct


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
        return []                                # a write — no reply
    # kind == "read"
    return [("reply", {"kind": "progress", "mastery": state["mastery"],
                       "seen": state["seen"]})]


# ── CHECKER: fan-in of grading keys (from PLANNER) and answers (from the kid). ─
def checker_step(msg, state):
    if msg["kind"] == "key":
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
    correct = (given == state["key"])
    state["key"] = None
    fb = "correct!" if correct else "not quite — try the worked solution"
    return [("screen", {"kind": "feedback", "text": fb}),
            ("out",    {"kind": "outcome", "correct": correct})]


# ── PLANNER: the multi-outbox brain. Ask-and-wait via state, never blocking. ──
def planner_step(msg, state):
    k = msg["kind"]
    if k == "start":
        return [("to_bank", {"n": 0})]                       # ask BANK for Q0
    if k == "question":
        state["current"] = msg
        return [("to_screen", {"kind": "show", "text": msg["text"]}),
                ("to_checker", {"kind": "key", "answer": msg["answer"]})]
    if k == "outcome":
        state["results"].append(msg["correct"])
        sends = [("to_progress", {"kind": "update", "correct": msg["correct"]})]
        state["n"] += 1
        if state["n"] < len(QUESTIONS):
            sends.append(("to_bank", {"n": state["n"]}))     # ask for next Q
        else:
            sends.append(("to_progress", {"kind": "read"}))  # session over: read progress
        return sends
    if k == "progress":                                       # the final read reply
        return [("to_reporter", {"kind": "final", "mastery": msg["mastery"],
                                 "seen": msg["seen"], "results": list(state["results"])})]
    return []


# ── REPORTER: 2 outboxes — summary to the screen, report to the file. ────────
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
        name="tutor",
        blocks={
            "SESSION":  Source(fn=Feed([{"kind": "start"}]).run, name="SESSION", interval=0.02),
            "ANSWERS":  Source(fn=Feed([{"kind": "answer", "value": a} for a in KID_ANSWERS]).run,
                               name="ANSWERS", interval=0.02),
            "BANK":     Worker(step=bank_step, outports=["reply"], name="BANK",
                               state={"questions": QUESTIONS}),
            "PROGRESS": Worker(step=progress_step, outports=["reply"], name="PROGRESS",
                               state={"mastery": 0, "seen": 0}),
            "CHECKER":  Worker(step=checker_step, outports=["out", "screen"], name="CHECKER",
                               state={"key": None, "pending": deque()}),
            "PLANNER":  Worker(step=planner_step,
                               outports=["to_bank", "to_checker", "to_screen",
                                         "to_progress", "to_reporter"],
                               name="PLANNER", state={"n": 0, "current": None, "results": []}),
            "REPORTER": Worker(step=reporter_step, outports=["screen", "file"], name="REPORTER"),
            "SCREEN":   Sink(fn=screen.append, name="SCREEN"),
            "PARENT_REPORT": Sink(fn=report.append, name="PARENT_REPORT"),
        },
        connections=[
            ("SESSION",  "out_",       "PLANNER",  "in_"),
            ("ANSWERS",  "out_",       "CHECKER",  "in_"),
            ("PLANNER",  "to_bank",    "BANK",     "in_"),
            ("BANK",     "reply",      "PLANNER",  "in_"),
            ("PLANNER",  "to_progress","PROGRESS", "in_"),
            ("PROGRESS", "reply",      "PLANNER",  "in_"),
            ("PLANNER",  "to_checker", "CHECKER",  "in_"),
            ("CHECKER",  "out",        "PLANNER",  "in_"),
            ("CHECKER",  "screen",     "SCREEN",   "in_"),
            ("PLANNER",  "to_screen",  "SCREEN",   "in_"),
            ("PLANNER",  "to_reporter","REPORTER", "in_"),
            ("REPORTER", "screen",     "SCREEN",   "in_"),
            ("REPORTER", "file",       "PARENT_REPORT", "in_"),
        ],
    )
    net._screen = screen; net._report = report
    return net


if __name__ == "__main__":
    net = build()
    net.run_network()
    print("\n=== tutor (phase 2) — what the kid saw on SCREEN ===")
    for m in net._screen:
        tag = m["kind"].upper()
        print(f"  [{tag}] {m['text']}")
    print("\n=== parent report file ===")
    for r in net._report:
        print("  ", r)
