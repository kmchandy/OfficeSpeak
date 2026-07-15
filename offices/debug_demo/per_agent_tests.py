"""Test each computational worker of temp_watch by itself.

This is aid (a): isolate a worker, feed it fixed inputs, look at what it
produces — no office running, no timing. It localizes a body bug to one worker.

We test Baseline and Alerter separately. Baseline turns out fine; Alerter is
where the office's flood of alerts comes from.
"""
from collections import deque

from office import baseline_fn, alerter_fn, THRESHOLD


def test_baseline():
    print("── Baseline (rolling average of the last 5) ──")
    state = {"window": deque()}
    for reading in [20, 21, 20, 22, 19, 20, 31]:
        out = baseline_fn(reading, state)
        print(f"  reading={reading:>3}  ->  baseline={out['baseline']}")
    print("  Looks right: the baseline tracks the recent readings and the")
    print("  spike to 31 barely moves it (it's one of five).\n")


def test_alerter():
    print("── Alerter (should alert only on a spike > 5 above baseline) ──")
    # Discriminating cases: raw reading high, but the *rise* is small or large.
    cases = [
        # (reading, baseline, what a spike-detector SHOULD do)
        (22, 20, "no alert  (rise = 2, not a spike)"),
        (24, 20, "no alert  (rise = 4, not a spike)"),
        (31, 20, "ALERT     (rise = 11, a real spike)"),
        (20, 20, "no alert  (rise = 0)"),
    ]
    for reading, baseline, expected in cases:
        out = alerter_fn({"reading": reading, "baseline": baseline})
        got = "ALERT" if out else "no alert"
        rise = reading - baseline
        flag = "  <-- WRONG" if (got == "ALERT") != ("ALERT" in expected) else ""
        print(f"  reading={reading:>3} baseline={baseline:>3} (rise={rise:>2})  "
              f"->  {got:<8}  expected: {expected}{flag}")
    print()
    print(f"  Diagnosis: Alerter fires whenever reading > {THRESHOLD}, not when the")
    print(f"  RISE above baseline > {THRESHOLD}. It's comparing the raw temperature")
    print("  instead of how far it rose. That's why the office alerts on almost")
    print("  every reading. Fix: compare (reading - baseline) to the threshold.\n")


if __name__ == "__main__":
    print("\nTesting each worker of temp_watch by itself:\n")
    test_baseline()
    test_alerter()
    print("Localized: Baseline is fine; the bug is in Alerter's body.")
