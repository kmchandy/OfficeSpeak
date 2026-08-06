"""Phase 2 — the uniform worker host.

Every office-specific worker (Python OR LLM) presents ONE contract:

    step(message, state) -> [(outbox, message), ...]      # [] = send nothing

The body is a pure function: it reads its one inbox's message plus its state,
mutates state in place, and RETURNS the messages to send (each labeled with its
outbox). It never calls send()/recv() and never blocks — this `Worker` agent
does the recv/send. Because the contract is identical for Python and LLM bodies,
the two are swappable without touching the rest of the office (an LLM body is
wrapped with input/output adapters so it also returns `[(outbox, message)]`).

This is `Transform` generalized to several outboxes and a list-of-labeled-messages
return. Registered coordinators (merge_synch/select/gate) and records are the
trusted, imperative message-passing agents; a `Worker` is generated content and
is deliberately a pure step function.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Tuple
import traceback

from dissyslab.core import Agent

Sends = Optional[List[Tuple[str, Any]]]


class Worker(Agent):
    """Single inbox; one or more outboxes; body `step(msg, state) -> sends`."""

    def __init__(
        self,
        *,
        step: Callable[[Any, Dict[str, Any]], Sends],
        outports: List[str],
        name: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
        inport: str = "in_",
    ):
        if not callable(step):
            raise TypeError(f"Worker step must be callable, got {type(step).__name__}")
        super().__init__(name=name, inports=[inport], outports=list(outports))
        self._step = step
        self._inport = inport
        self._state: Dict[str, Any] = deepcopy(state) if state is not None else {}

    @property
    def state(self) -> Dict[str, Any]:
        return self._state

    def save_state(self) -> Any:
        return {"state": self._state}

    def load_state(self, saved: Any) -> None:
        if isinstance(saved, dict) and "state" in saved:
            self._state = saved["state"]

    def run(self) -> None:
        while True:
            msg = self.recv(self._inport)              # blocks; raises on _Shutdown
            try:
                sends = self._step(msg, self._state)
            except Exception as e:                     # report and stop (flushed!)
                print(f"[Worker '{self.name}'] error in step: {e}", flush=True)
                print(traceback.format_exc(), flush=True)
                return
            for outbox, out_msg in (sends or []):
                self.send(out_msg, outbox)

    def __repr__(self) -> str:
        fn = getattr(self._step, "__name__", repr(self._step))
        return f"<Worker name={self.name} step={fn} outports={self.outports}>"
