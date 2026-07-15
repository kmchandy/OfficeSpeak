"""Phase 2 — prove Python <-> LLM worker swap under ONE contract.

Office:  ITEMS (source) --item--> TRIAGE (Worker) --> URGENT (sink)
                                              \\----> NORMAL (sink)

TRIAGE classifies each item and routes it to the `urgent` or `normal` outbox.
It is built TWO ways, with the identical `Worker` contract
`step(message, state) -> [(outbox, message)]` and the identical wiring:

  * `python_triage_step` — a Python rule.
  * an LLM worker — render the message into a prompt, call the model, force the
    answer into {send_to, text}, validate it, return [(send_to, text)].

The LLM here is a keyless STUB (canned, deterministic) that sees only the prompt
string, exactly like a real model would. Both builds produce identical routing —
that is the swap: the office doesn't change when the body's implementation does.

Run:  python triage_swap.py
"""
from __future__ import annotations
import json

from dissyslab.network import Network
from dissyslab.blocks.source import Source
from dissyslab.blocks.sink import Sink

from worker import Worker


ITEMS = [
    {"text": "Server is down, urgent!"},
    {"text": "weekly newsletter draft"},
    {"text": "URGENT: payment failed for a customer"},
    {"text": "lunch menu for Friday"},
]
OUTBOXES = ["urgent", "normal"]


# ── Body A: a Python worker (a rule) ─────────────────────────────────────────
def python_triage_step(msg, state):
    text = msg["text"]
    box = "urgent" if "urgent" in text.lower() else "normal"
    return [(box, text)]


# ── Body B: an LLM worker, same contract, via input/output adapters ──────────
def _render(msg, outboxes):
    return (f"Classify the message and choose exactly one of {outboxes}. "
            f'Reply ONLY as JSON {{"send_to": <one of them>, "text": <the message>}}.\n'
            f"Message: {msg['text']}")

def _stub_model(prompt):
    """Keyless stand-in for an LLM. Sees only the prompt string, returns a JSON
    string — like a real model would. (Same judgment as the rule, so the two
    builds route identically; a real model would go here unchanged.)"""
    message = prompt.split("Message: ", 1)[1]
    send_to = "urgent" if "urgent" in message.lower() else "normal"
    return json.dumps({"send_to": send_to, "text": message})

def make_llm_step(outboxes, model, render):
    def step(msg, state):
        raw = model(render(msg, outboxes))          # call the "LLM"
        try:
            obj = json.loads(raw)                    # output adapter: parse
        except Exception:
            raise ValueError(f"LLM did not return JSON: {raw!r}")
        send_to, text = obj.get("send_to"), obj.get("text")
        if send_to not in outboxes:                  # ...and validate the label
            raise ValueError(f"LLM chose invalid outbox {send_to!r}; allowed {outboxes}")
        return [(send_to, text)]
    return step


class Feed:
    def __init__(self, data): self.data = data; self.i = 0
    def run(self):
        if self.i >= len(self.data): return None
        v = self.data[self.i]; self.i += 1
        return v


def run_office(triage_step, label):
    urgent, normal = [], []
    net = Network(
        name=f"triage_{label}",
        blocks={
            "ITEMS": Source(fn=Feed(list(ITEMS)).run, name="ITEMS", interval=0.02),
            "TRIAGE": Worker(step=triage_step, outports=OUTBOXES, name="TRIAGE"),
            "URGENT": Sink(fn=urgent.append, name="URGENT"),
            "NORMAL": Sink(fn=normal.append, name="NORMAL"),
        },
        connections=[
            ("ITEMS", "out_", "TRIAGE", "in_"),
            ("TRIAGE", "urgent", "URGENT", "in_"),
            ("TRIAGE", "normal", "NORMAL", "in_"),
        ],
    )
    net.run_network()
    return {"urgent": urgent, "normal": normal}


if __name__ == "__main__":
    py = run_office(python_triage_step, "python")
    llm = run_office(make_llm_step(OUTBOXES, _stub_model, _render), "llm")

    print("\n=== triage: Python worker ===")
    print("  urgent:", py["urgent"])
    print("  normal:", py["normal"])
    print("\n=== triage: LLM worker (stub, same contract & wiring) ===")
    print("  urgent:", llm["urgent"])
    print("  normal:", llm["normal"])
    same = py == llm
    print(f"\nidentical routing (Python == LLM): {same}")
