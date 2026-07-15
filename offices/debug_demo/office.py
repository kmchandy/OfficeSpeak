"""temp_watch — a tiny, fully-deterministic office with a planted bug.

A worked example for debugging *computational* workers (Pat's Python bodies).

The office:

    readings ──▶ Baseline ──▶ Alerter ──▶ ALERTS

- readings : a stream of hourly temperatures (synthetic, fixed).
- Baseline : keeps a rolling average of the last K readings (has memory).
- Alerter  : raises an alert when a reading is a *spike* — more than THRESHOLD
             degrees above the current baseline.
- ALERTS   : records the alerts.

Everything here is ordinary Python and the pipeline is determinate (no
fair_merge, no LLM), so a run is exactly reproducible and each worker can be
tested by itself.

There is a planted bug in Alerter (see the comment). Run with the default to see
the buggy behaviour; run with DEBUG_FIX=1 to see the corrected office.

    python office.py            # buggy   -> alerts on almost everything
    DEBUG_FIX=1 python office.py # fixed   -> one alert, on the real spike
"""
from __future__ import annotations
import os
from collections import deque

from dissyslab.network import Network
from dissyslab.blocks.source import Source
from dissyslab.blocks.transform import Transform
from dissyslab.blocks.sink import Sink

# Hourly readings: mostly ~20 °C, with one real spike to 31.
READINGS = [20, 21, 20, 22, 19, 20, 31, 20, 21, 20]
K = 5            # rolling-average window
THRESHOLD = 5    # a "spike" is more than this many degrees above baseline


# ── the two computational workers, as plain functions we can also test alone ──

def baseline_fn(reading, state):
    """Rolling average of the last K readings (including the current one)."""
    state["window"].append(reading)
    if len(state["window"]) > K:
        state["window"].popleft()
    avg = sum(state["window"]) / len(state["window"])
    return {"reading": reading, "baseline": round(avg, 1)}


def alerter_fn(msg):
    """Alert when the reading is a spike above the baseline.

    A spike means (reading - baseline) > THRESHOLD.
    """
    reading = msg["reading"]
    baseline = msg["baseline"]
    # ---- PLANTED BUG ----------------------------------------------------
    # Meant to compare the *rise above baseline* to the threshold, but this
    # compares the raw reading. With THRESHOLD=5 and readings around 20, the
    # test `reading > THRESHOLD` is true for almost every reading, so the
    # office floods with alerts.
    if reading > THRESHOLD:                       # BUG: should be reading - baseline
        return {"reading": reading, "baseline": baseline, "alert": True}
    return None
    # ---- CORRECT VERSION (used when DEBUG_FIX=1) ------------------------
    #   if reading - baseline > THRESHOLD:
    #       return {"reading": reading, "baseline": baseline, "alert": True}
    #   return None


def alerter_fn_fixed(msg):
    reading = msg["reading"]
    baseline = msg["baseline"]
    if reading - baseline > THRESHOLD:
        return {"reading": reading, "baseline": baseline, "alert": True}
    return None


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


def build(fixed=False):
    alerts = []

    def collect(msg):
        alerts.append(msg)

    net = Network(
        name="temp_watch",
        blocks={
            "readings": Source(fn=Feed(READINGS).run, name="readings", interval=0.02),
            "Baseline": Transform(fn=baseline_fn, state={"window": deque()}, name="Baseline"),
            "Alerter": Transform(fn=(alerter_fn_fixed if fixed else alerter_fn), name="Alerter"),
            "ALERTS": Sink(fn=collect, name="ALERTS"),
        },
        connections=[
            ("readings", "out_", "Baseline", "in_"),
            ("Baseline", "out_", "Alerter", "in_"),
            ("Alerter", "out_", "ALERTS", "in_"),
        ],
    )
    net._alerts = alerts
    return net


if __name__ == "__main__":
    fixed = bool(os.environ.get("DEBUG_FIX"))
    net = build(fixed=fixed)
    net.run_network()
    alerts = net._alerts
    print(f"\n=== temp_watch ({'FIXED' if fixed else 'BUGGY'}) ===")
    print(f"readings: {READINGS}")
    print(f"alerts raised: {len(alerts)}")
    for a in alerts:
        print(f"  reading={a['reading']:>3}  baseline={a['baseline']:>5}  -> ALERT")
