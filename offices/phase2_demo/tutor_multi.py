"""Phase 2 — the SAME tutor office, handling several students concurrently.

This is tutor_interactive.py generalized from "one student, one run" to "many
students, one office." The office shape doesn't change — same PLANNER, CHECKER,
BANK, PROGRESS, PARENT_REPORT — and none of them are replicated per student.
What changes is one convention, applied everywhere:

    EVERY message carries a student_id. Any worker that needs to remember
    something about a particular student across more than one message keeps
    it in a dict keyed by that student_id, instead of a single value.

That's it. `state["n"]` becomes `state["n"][student_id]`; `state["results"]`
becomes `state["results"][student_id]`; and so on. Nothing about what a
worker remembers or when changes — only the shape of the dict gains one
layer, because now more than one student's "current question number" has to
live somewhere at once.

SESSION is a small roster source standing in for "students signing in": it
mints one `start` message per student (a real one at the keyboard, and a
couple of simulated ones answering on their own), spaced out so their
sessions overlap in flight — proving PLANNER/CHECKER/BANK/PROGRESS are safe to
share, not proving anything about a real always-on listener (that's a
separate, later problem: this office still runs once and terminates).

    SESSION ─start(id)─▶ PLANNER ──ask/say(id)──▶ TERMINAL ──answer(id)──▶ CHECKER(★LLM)
                edu          ▲  │                     or                        │
                          progress  ├─key(id)──────▶ SIM_ANSWERER ────────────┘ (grades)
                             │  ├─to_bank/to_progress(id)──▶ BANK / PROGRESS (records, keyed by id)
                             │  └─report(id)──▶ PARENT_REPORT (keyed by id)
                             └───────────────── graded(id) ◀── CHECKER

Only one student_id ("live") is ever routed to the real TERMINAL — a
deliberate choice, to keep the demo to one real keyboard. The others ("amy", "ben") are
routed to SIM_ANSWERER, a worker that answers on their behalf from a small
canned script, standing in for other students' own devices. PLANNER decides
which channel a student's messages go to by remembering, per student_id,
which channel they signed in on — itself just one more id-keyed fact.

RUN IT IN A REAL TERMINAL (so the "live" student can type):

    cd DisSysLab && pip install -e .          # once
    cd ../OfficeSpeak/offices/phase2_demo
    python tutor_multi.py

Needs ANTHROPIC_API_KEY in the environment. Running without a terminal
(piped/no stdin) still works — the live student's unanswered prompts are
treated as blank answers — so it never hangs.
"""
from __future__ import annotations

import json
import time
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

# Who signs in, in what order, and on which channel. "live" is the one real
# keyboard; the rest are simulated students answering on their own.
ROSTER = [
    ("live", "terminal"),
    ("amy",  "sim"),
    ("ben",  "sim"),
]

# Canned answers for the simulated students — deliberately in words / wrong
# forms, same spirit as tutor_llm.py's KID_ANSWERS, but one per student so
# their sessions are distinguishable in the transcript.
SIM_ANSWERS = {
    "amy": ["one", "1", "six", "two quarters"],   # correct, WRONG, correct, correct
    "ben": ["1/2", "one half", "5", "1/2"],        # correct, correct, WRONG, correct
}

REPORT_FILE = Path(__file__).with_name("parent_reports_multi.json")


# ── BANK: a record (keeper). Shared, read-only content -> just echo the id. ───
def bank_step(msg, state):
    n = msg["n"]
    q = state["questions"][n] if n < len(state["questions"]) else {"id": None}
    return [("reply", {"kind": "question", "student_id": msg["student_id"], **q})]


# ── PROGRESS: a record, now keyed by student_id (one row per student). ────────
def progress_step(msg, state):
    sid = msg["student_id"]
    mastery = state.setdefault("mastery", {})
    seen = state.setdefault("seen", {})
    if msg["kind"] == "update":
        seen[sid] = seen.get(sid, 0) + 1
        if msg["correct"]:
            mastery[sid] = mastery.get(sid, 0) + 1
        return []
    return [("reply", {"kind": "progress", "student_id": sid,
                       "mastery": mastery.get(sid, 0), "seen": seen.get(sid, 0)})]


# ── CHECKER: the LLM worker, now keyed by student_id instead of one slot. ─────
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
    sid = msg["student_id"]
    key = state.setdefault("key", {})
    question = state.setdefault("question", {})
    pending = state.setdefault("pending", {})

    if msg["kind"] == "key":
        question[sid] = msg["question"]
        key[sid] = msg["answer"]
        buf = pending.get(sid)
        if buf:
            return _grade(state, sid, buf.popleft())
        return []
    # kind == "answer"
    if key.get(sid) is not None:
        return _grade(state, sid, msg["value"])
    pending.setdefault(sid, deque()).append(msg["value"])
    return []


def _grade(state, sid, given):
    question = state["question"][sid]
    correct_answer = state["key"][sid]
    user = (f"Question: {question}\n"
            f"Correct answer: {correct_answer}\n"
            f"Child typed: {given!r}")
    raw = _backend().complete(system=GRADER_SYSTEM, user=user, max_tokens=120)
    obj = _parse_send(raw)
    correct = bool(obj.get("correct"))
    fb = obj.get("feedback") or ("Correct!" if correct else "Not quite — try again.")
    state["question"][sid] = None
    state["key"][sid] = None
    return [("graded", {"kind": "graded", "student_id": sid,
                        "correct": correct, "feedback": fb})]


# ── TERMINAL: the ONE real console. Always the "live" student — no id logic. ──
def terminal_step(msg, state):
    if msg["kind"] == "ask":
        print(f"\n  [live] {msg['text']}")
        try:
            value = input("  your answer: ")
        except EOFError:                     # no terminal (piped/empty stdin)
            value = ""
        return [("answer", {"kind": "answer", "value": value, "student_id": "live"})]
    print(f"  [live] {msg['text']}")
    return []


# ── SIM_ANSWERER: stands in for every OTHER student's own device. ─────────────
def sim_answerer_step(msg, state):
    sid = msg["student_id"]
    if msg["kind"] != "ask":
        return []                             # ignore "say" — no screen to show
    idx = state.setdefault("idx", {})
    i = idx.get(sid, 0)
    answers = SIM_ANSWERS.get(sid, [])
    value = answers[i] if i < len(answers) else ""
    idx[sid] = i + 1
    time.sleep(0.05)                          # a beat, so timelines visibly overlap
    print(f"  [{sid}] {msg['text']}\n  [{sid}] answers: {value!r}")
    return [("answer", {"kind": "answer", "value": value, "student_id": sid})]


# ── PLANNER: the coach, now tracking n/results/channel PER student_id. ────────
def planner_step(msg, state):
    n = state.setdefault("n", {})
    results = state.setdefault("results", {})
    channel = state.setdefault("channel", {})
    k = msg["kind"]

    if k == "start":
        sid = msg["student_id"]
        channel[sid] = msg.get("channel", "terminal")
        n[sid] = 0
        results[sid] = []
        return [("to_bank", {"n": 0, "student_id": sid})]

    if k == "question":
        sid = msg["student_id"]
        ask_out = "to_terminal" if channel.get(sid) == "terminal" else "to_sim"
        return [("to_checker", {"kind": "key", "question": msg["text"],
                                "answer": msg["answer"], "student_id": sid}),
                (ask_out, {"kind": "ask", "text": msg["text"], "student_id": sid})]

    if k == "graded":
        sid = msg["student_id"]
        say_out = "to_terminal" if channel.get(sid) == "terminal" else "to_sim"
        results[sid].append(msg["correct"])
        sends = [(say_out, {"kind": "say", "text": msg["feedback"], "student_id": sid}),
                 ("to_progress", {"kind": "update", "correct": msg["correct"], "student_id": sid})]
        n[sid] += 1
        if n[sid] < len(QUESTIONS):
            sends.append(("to_bank", {"n": n[sid], "student_id": sid}))
        else:
            sends.append(("to_progress", {"kind": "read", "student_id": sid}))
        return sends

    if k == "progress":
        sid = msg["student_id"]
        say_out = "to_terminal" if channel.get(sid) == "terminal" else "to_sim"
        score = f"{sum(results[sid])}/{len(results[sid])}"
        report = {"kind": "report", "student_id": sid, "mastery": msg["mastery"],
                  "questions_seen": msg["seen"], "score": score}
        return [(say_out, {"kind": "say",
                           "text": f"\n[{sid}] Session done — you got {score}. Nice work!",
                           "student_id": sid}),
                ("to_report", report)]
    return []


# ── SESSION: the roster "listener" — mints one start(id) per student. ─────────
def session_feed(state):
    if not state["roster"]:
        return None
    student_id, channel = state["roster"].popleft()
    return {"kind": "start", "student_id": student_id, "channel": channel}


def build():
    saved = []
    net = Network(
        name="tutor_multi",
        blocks={
            "SESSION":  Source(fn=session_feed, name="SESSION", interval=0.3,
                               state={"roster": deque(ROSTER)}),
            "BANK":     Worker(step=bank_step, outports=["reply"], name="BANK",
                               state={"questions": QUESTIONS}),
            "PROGRESS": Worker(step=progress_step, outports=["reply"], name="PROGRESS"),
            "CHECKER":  Worker(step=checker_step, outports=["graded"], name="CHECKER"),
            "TERMINAL": Worker(step=terminal_step, outports=["answer"], name="TERMINAL"),
            "SIM_ANSWERER": Worker(step=sim_answerer_step, outports=["answer"],
                                   name="SIM_ANSWERER"),
            "PLANNER":  Worker(step=planner_step,
                               outports=["to_bank", "to_checker", "to_terminal",
                                         "to_sim", "to_progress", "to_report"],
                               name="PLANNER"),
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
            ("SIM_ANSWERER", "answer",  "CHECKER",  "in_"),
            ("CHECKER",  "graded",      "PLANNER",  "in_"),
            ("PLANNER",  "to_terminal", "TERMINAL", "in_"),
            ("PLANNER",  "to_sim",      "SIM_ANSWERER", "in_"),
            ("PLANNER",  "to_report",   "PARENT_REPORT", "in_"),
        ],
    )
    net._saved = saved
    return net


if __name__ == "__main__":
    print("=" * 64)
    print("  Fractions practice — several students, one office.")
    print("  You are 'live'. 'amy' and 'ben' answer on their own.")
    print("=" * 64)
    net = build()
    net.run_network()
    if net._saved:
        by_student = {r["student_id"]: r for r in net._saved}
        REPORT_FILE.write_text(json.dumps(by_student, indent=2))
        print(f"\n  (parent reports saved to {REPORT_FILE.name})")
        for sid, r in by_student.items():
            print(f"    {sid}: {r['score']}")
