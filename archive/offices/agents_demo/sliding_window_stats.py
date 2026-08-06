"""A stateful Python agent in the general DSL form: an object with run(msg).

SlidingWindowStats keeps the last `window` numeric values and, on each incoming
value, emits the running mean and population standard deviation over the current
window. State (the window and rolling sums) lives in the object; run(msg) ingests
one message and returns the output message. In a DSL office the same body would
call self.send(...) on an outport instead of returning.

This is the *computational* kind of worker body (plain, deterministic Python) —
as opposed to an LLM-prompt body. Claude generates both kinds; numeric work like
this stays out of the LLM, so it is exact, cheap, and testable.
"""

from collections import deque
import math


class SlidingWindowStats:
    def __init__(self, window=5):
        self.window = window
        self._values = deque(maxlen=window)
        self._sum = 0.0
        self._sumsq = 0.0

    def run(self, msg):
        x = float(msg)
        if len(self._values) == self.window:          # window full: evict oldest
            old = self._values[0]
            self._sum -= old
            self._sumsq -= old * old
        self._values.append(x)
        self._sum += x
        self._sumsq += x * x
        n = len(self._values)
        mean = self._sum / n
        var = max(self._sumsq / n - mean * mean, 0.0)  # clamp tiny fp negatives
        return {"n": n, "mean": mean, "std": math.sqrt(var)}


if __name__ == "__main__":
    import random
    from statistics import mean as ref_mean, pstdev as ref_std

    random.seed(0)
    data = [random.gauss(10, 3) for _ in range(20)]
    W = 5
    agent = SlidingWindowStats(window=W)

    last = None
    for i, x in enumerate(data):
        out = agent.run(x)
        window = data[max(0, i - W + 1): i + 1]        # trailing W values
        assert abs(out["mean"] - ref_mean(window)) < 1e-9, (out, window)
        assert abs(out["std"] - ref_std(window)) < 1e-9, (out, window)
        last = out

    print(f"OK: all {len(data)} steps match reference mean & population std")
    print(f"window size = {W}")
    print(f"last output = n={last['n']}, mean={last['mean']:.4f}, std={last['std']:.4f}")
