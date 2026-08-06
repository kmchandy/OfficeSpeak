"""Phase 2 — drive real offices through the general harness.

Each office below is written as a plain declarative spec (agents + kinds +
4-tuple connections) and assembled by harness.build_office — no hand-wiring.
We rebuild offices we already trust from bespoke scripts and check the
harness-built versions produce the same results and terminate:

  * triage      — source → transform → two sinks (routing).
  * room_monitor — source → stateful transform (keeps a baseline) → sink.
  * uneven_join — two sources → merge_synch coordinator → sink, with an
                  unpaired leftover (exercises the coordinator path AND the
                  #47 termination fix through the harness).

Run:  python harness_demo.py
"""
from __future__ import annotations

from collections import deque

from harness import build_office


class Feed:
    """Exhaustible source body: emit each item, then None."""
    def __init__(self, data):
        self.data = list(data)
        self.i = 0

    def run(self):
        if self.i >= len(self.data):
            return None
        v = self.data[self.i]
        self.i += 1
        return v


# ── Office 1: triage ─────────────────────────────────────────────────────
def triage_step(msg, state):
    box = "urgent" if "urgent" in msg["text"].lower() else "normal"
    return [(box, msg["text"])]


def run_triage():
    urgent, normal = [], []
    office = {
        "name": "triage",
        "agents": [
            {"name": "ITEMS", "kind": "source",
             "body": Feed([{"text": "Server down, urgent!"},
                           {"text": "weekly newsletter"},
                           {"text": "URGENT: payment failed"},
                           {"text": "lunch menu"}]).run, "interval": 0.01},
            {"name": "TRIAGE", "kind": "transform", "body": triage_step},
            {"name": "URGENT", "kind": "sink", "body": urgent.append},
            {"name": "NORMAL", "kind": "sink", "body": normal.append},
        ],
        "connections": [
            ("ITEMS", "out_", "TRIAGE", "in_"),
            ("TRIAGE", "urgent", "URGENT", "in_"),
            ("TRIAGE", "normal", "NORMAL", "in_"),
        ],
    }
    build_office(office).run_network()
    return urgent, normal


# ── Office 2: room_monitor (stateful transform) ──────────────────────────
def monitor_step(reading, state):
    # Same rule as the trusted room_monitor.py: a rolling baseline; loud if
    # well above it, silence if near zero.
    w = state.setdefault("window", deque(maxlen=5))
    w.append(reading)
    baseline = sum(w) / len(w)
    if reading - baseline > 25:
        return [("out_", {"kind": "loud noise", "reading": reading})]
    if reading < 5:
        return [("out_", {"kind": "unusual silence", "reading": reading})]
    return []


def run_monitor():
    alerts = []
    office = {
        "name": "room_monitor",
        "agents": [
            {"name": "MIC", "kind": "source",
             "body": Feed([30, 32, 28, 31, 90, 29, 30, 2, 2, 2, 31, 33]).run,
             "interval": 0.01},
            {"name": "MONITOR", "kind": "transform", "body": monitor_step},
            {"name": "CONSOLE", "kind": "sink", "body": alerts.append},
        ],
        "connections": [
            ("MIC", "out_", "MONITOR", "in_"),
            ("MONITOR", "out_", "CONSOLE", "in_"),
        ],
    }
    build_office(office).run_network()
    return alerts


# ── Office 3: uneven_join (coordinator + #47) ────────────────────────────
def run_join():
    joined = []
    office = {
        "name": "uneven_join",
        "agents": [
            {"name": "SRC0", "kind": "source",
             "body": Feed(["a0", "a1"]).run, "interval": 0.01},
            {"name": "SRC1", "kind": "source",
             "body": Feed(["b0", "b1", "b2"]).run, "interval": 0.01},
            {"name": "JOIN", "kind": "coordinator", "primitive": "merge_synch"},
            {"name": "OUT", "kind": "sink", "body": joined.append},
        ],
        "connections": [
            ("SRC0", "out_", "JOIN", "in_0"),
            ("SRC1", "out_", "JOIN", "in_1"),
            ("JOIN", "out_", "OUT", "in_"),
        ],
    }
    build_office(office).run_network()
    return joined


if __name__ == "__main__":
    urgent, normal = run_triage()
    print("triage:")
    print("  urgent:", urgent)
    print("  normal:", normal)
    t_ok = urgent == ["Server down, urgent!", "URGENT: payment failed"] and \
        normal == ["weekly newsletter", "lunch menu"]

    alerts = run_monitor()
    print("room_monitor:")
    for a in alerts:
        print("  ", a["kind"], "reading=", a["reading"])
    m_ok = len(alerts) == 4 and alerts[0]["kind"] == "loud noise"

    joined = run_join()
    print("uneven_join:")
    print("  joined:", joined)
    j_ok = joined == [["a0", "b0"], ["a1", "b1"]]   # b2 stranded, still terminates

    print("\nall harness offices correct & terminated:", t_ok and m_ok and j_ok)
