"""Phase 2 — run the triage office with a REAL LLM worker.

Same office and wiring as triage_swap.py:

    ITEMS (source) --item--> TRIAGE (Worker) --urgent--> URGENT (sink)
                                          \\----normal--> NORMAL (sink)

triage_swap.py proved the uniform contract with a keyless *stub* model. This
runs the identical office with the body built by llm_worker.make_llm_step —
a live provider through DisSysLab's Backend interface (Claude by default).
The office code is unchanged; only the worker's implementation differs. That
is the swap, now demonstrated end to end against a real model.

Run (needs a key):  ANTHROPIC_API_KEY=... python triage_llm.py
"""
from __future__ import annotations

from dissyslab.network import Network
from dissyslab.blocks.source import Source
from dissyslab.blocks.sink import Sink

from worker import Worker
from llm_worker import make_llm_step


ITEMS = [
    {"text": "Server is down, urgent!"},
    {"text": "weekly newsletter draft"},
    {"text": "URGENT: payment failed for a customer"},
    {"text": "lunch menu for Friday"},
]
OUTBOXES = ["urgent", "normal"]

SYSTEM = (
    "You triage incoming office messages. Decide whether each message needs "
    "urgent attention or is routine. Send urgent items to the 'urgent' "
    "outbox and routine items to the 'normal' outbox. Reply with NOTHING "
    'but a single JSON object {"send_to": "urgent" | "normal", "text": <the '
    "original message text>}. No markdown, no explanation."
)


def render(msg, outboxes):
    return f"Message: {msg['text']}"


class Feed:
    def __init__(self, data):
        self.data = data
        self.i = 0

    def run(self):
        if self.i >= len(self.data):
            return None
        v = self.data[self.i]
        self.i += 1
        return v


def build(triage_step):
    urgent, normal = [], []
    net = Network(
        name="triage_llm",
        blocks={
            "ITEMS":  Source(fn=Feed(list(ITEMS)).run, name="ITEMS", interval=0.02),
            "TRIAGE": Worker(step=triage_step, outports=OUTBOXES, name="TRIAGE"),
            "URGENT": Sink(fn=urgent.append, name="URGENT"),
            "NORMAL": Sink(fn=normal.append, name="NORMAL"),
        },
        connections=[
            ("ITEMS",  "out_",   "TRIAGE", "in_"),
            ("TRIAGE", "urgent", "URGENT", "in_"),
            ("TRIAGE", "normal", "NORMAL", "in_"),
        ],
    )
    net._urgent, net._normal = urgent, normal
    return net


if __name__ == "__main__":
    # Deterministic routing → use the low-temperature ("precise") Claude.
    step = make_llm_step(outboxes=OUTBOXES, system=SYSTEM,
                         render=render, backend_name="claude_precise")
    net = build(step)
    net.run_network()

    print("\n=== triage: REAL LLM worker (Claude, via Backend interface) ===")
    print("  urgent:", [m for m in net._urgent])
    print("  normal:", [m for m in net._normal])

    # Sanity check: the two clearly-urgent items must land in urgent, the
    # two routine ones in normal. (Text may be lightly reworded by the model,
    # so match on a keyword rather than exact string.)
    urgent_blob = " ".join(net._urgent).lower()
    normal_blob = " ".join(net._normal).lower()
    ok = (
        len(net._urgent) == 2 and len(net._normal) == 2
        and "server" in urgent_blob and "payment" in urgent_blob
        and "newsletter" in normal_blob and "lunch" in normal_blob
    )
    print(f"\nreal-LLM routing correct: {ok}")
