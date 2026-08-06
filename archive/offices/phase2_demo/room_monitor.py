"""Phase 2 — room_monitor, run end to end with the UNIFORM worker contract.

Every office-specific worker is a pure step function:

    step(message, state) -> [(outbox, message), ...]     # [] = send nothing

hosted on the `Worker` block (worker.py), which does the recv/send. A Python
worker and an LLM worker would present this SAME contract, so they are swappable.
This file uses the Python form; a later file adds an LLM worker of the same shape.

Office (from the start module's gallery `room_monitor`):

    MIC (source) --readings--> MONITOR (Worker) --alerts--> CONSOLE (sink)

Run:  python room_monitor.py
"""
from __future__ import annotations
from collections import deque

from dissyslab.network import Network
from dissyslab.blocks.source import Source
from dissyslab.blocks.sink import Sink

from worker import Worker


# ── mock input: loudness readings (normal chatter ~30; one loud spike; a silence) ──
READINGS = [30, 32, 28, 31, 90, 29, 30, 2, 2, 2, 31, 33]


# ── MONITOR's body: the uniform contract  step(message, state) -> sends ──────
def monitor_step(reading, state):
    w = state.setdefault("window", deque(maxlen=5))
    w.append(reading)
    baseline = sum(w) / len(w)
    if reading - baseline > 25:
        return [("out_", {"kind": "loud noise", "reading": reading,
                          "baseline": round(baseline, 1)})]
    if reading < 5:
        return [("out_", {"kind": "unusual silence", "reading": reading,
                          "baseline": round(baseline, 1)})]
    return []                                    # normal — send nothing


class Feed:
    """A mock source: emits one reading at a time, then None (end)."""
    def __init__(self, data): self.data = data; self.i = 0
    def run(self):
        if self.i >= len(self.data):
            return None
        v = self.data[self.i]; self.i += 1
        return v


def build():
    alerts = []
    def collect(alert): alerts.append(alert)

    net = Network(
        name="room_monitor",
        blocks={
            "MIC": Source(fn=Feed(READINGS).run, name="MIC", interval=0.02),
            "MONITOR": Worker(step=monitor_step, outports=["out_"], name="MONITOR",
                              state={}),
            "CONSOLE": Sink(fn=collect, name="CONSOLE"),
        },
        connections=[
            ("MIC", "out_", "MONITOR", "in_"),
            ("MONITOR", "out_", "CONSOLE", "in_"),
        ],
    )
    net._alerts = alerts
    return net


if __name__ == "__main__":
    net = build()
    net.run_network()
    print("\n=== room_monitor (phase 2, uniform worker contract) ===")
    print(f"readings: {READINGS}")
    print(f"alerts raised: {len(net._alerts)}")
    for a in net._alerts:
        print(f"  {a['kind']:<16} reading={a['reading']:>3}  baseline={a['baseline']}")
