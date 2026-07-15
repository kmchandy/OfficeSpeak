"""monitor worker body (Python, deterministic) — per-service anomaly detector.

For each service, keeps a rolling window of readings (reusing SlidingWindowStats)
and flags a reading whose z-score exceeds a threshold. Needs a few readings first to
have a baseline (realistic: it can't judge "abnormal" until it has learned "normal").

General DSL form: an object with run(msg). msg = {"service": str, "value": float};
run returns an alert dict or None.
"""
import os
import sys
from collections import defaultdict

_d = os.path.dirname(os.path.abspath(__file__))        # find agents_demo, wherever we sit
for _ in range(6):
    _cand = os.path.join(_d, "agents_demo")
    if os.path.isdir(_cand):
        sys.path.insert(0, _cand)
        break
    _d = os.path.dirname(_d)
from sliding_window_stats import SlidingWindowStats   # noqa: E402  (reuse)


class Monitor:
    def __init__(self, window=20, z=3.0):
        self.stats = defaultdict(lambda: SlidingWindowStats(window))
        self.z = z

    def run(self, msg):
        svc, val = msg["service"], float(msg["value"])
        s = self.stats[svc].run(val)                 # {n, mean, std}
        if s["n"] >= 5 and s["std"] > 0:
            zscore = (val - s["mean"]) / s["std"]
            if abs(zscore) >= self.z:
                return {"service": svc, "value": val,
                        "z": round(zscore, 2), "mean": round(s["mean"], 2)}
        return None


if __name__ == "__main__":
    m = Monitor(window=20, z=3.0)
    normals = [100, 101, 99, 100, 102, 98, 101, 100, 99, 101,
               100, 102, 98, 100, 101, 99, 100, 101, 99, 100]
    for v in normals:                                    # learn "normal" first
        assert m.run({"service": "web", "value": v}) is None      # no false alarms
    alert = m.run({"service": "web", "value": 500})      # then a spike
    print(alert)
    assert alert and alert["service"] == "web", alert
    print("OK: no false alarms on normal readings; flags the 500 spike")
