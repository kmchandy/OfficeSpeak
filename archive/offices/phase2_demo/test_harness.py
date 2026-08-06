"""Keyless tests for the general harness: the happy path plus the friendly
errors a generated office might trip. Run:  python test_harness.py"""
from __future__ import annotations

from harness import build_office


class Feed:
    def __init__(self, d): self.d = list(d); self.i = 0
    def run(self):
        if self.i >= len(self.d): return None
        v = self.d[self.i]; self.i += 1; return v


def _expect_error(office, needle):
    try:
        build_office(office)
    except ValueError as e:
        return needle in str(e)
    return False


def main():
    checks = []

    # Happy path: a source → transform → sink office builds and runs.
    out = []
    office = {
        "name": "t",
        "agents": [
            {"name": "S", "kind": "source", "body": Feed([1, 2, 3]).run, "interval": 0.01},
            {"name": "D", "kind": "transform", "body": lambda m, s: [("out_", m * 10)]},
            {"name": "K", "kind": "sink", "body": out.append},
        ],
        "connections": [("S", "out_", "D", "in_"), ("D", "out_", "K", "in_")],
    }
    build_office(office).run_network()
    checks.append(("happy path runs", out == [10, 20, 30]))

    # Connection naming an unknown agent.
    checks.append(("unknown receiver", _expect_error({
        "agents": [{"name": "S", "kind": "source", "body": Feed([]).run}],
        "connections": [("S", "out_", "GHOST", "in_")],
    }, "GHOST")))

    # Transform with no body.
    checks.append(("missing body", _expect_error({
        "agents": [{"name": "D", "kind": "transform"},
                   {"name": "K", "kind": "sink", "body": lambda m: None}],
        "connections": [("D", "out_", "K", "in_")],
    }, "needs a 'body'")))

    # Coordinator with an unknown primitive.
    checks.append(("bad primitive", _expect_error({
        "agents": [{"name": "C", "kind": "coordinator", "primitive": "magic"},
                   {"name": "K", "kind": "sink", "body": lambda m: None}],
        "connections": [("C", "out_", "K", "in_")],
    }, "primitive")))

    # Transform handed two distinct inboxes (should be exactly one).
    checks.append(("two inboxes on transform", _expect_error({
        "agents": [
            {"name": "A", "kind": "source", "body": Feed([]).run},
            {"name": "B", "kind": "source", "body": Feed([]).run},
            {"name": "D", "kind": "transform", "body": lambda m, s: []},
        ],
        "connections": [("A", "out_", "D", "in_0"), ("B", "out_", "D", "in_1")],
    }, "exactly one")))

    ok = all(p for _, p in checks)
    for name, p in checks:
        print(f"  [{'PASS' if p else 'FAIL'}] {name}")
    print("all passed:", ok)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
