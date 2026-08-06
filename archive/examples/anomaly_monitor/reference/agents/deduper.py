"""deduper worker body (Python, deterministic) — suppress repeat alerts.

Keeps, per service, how long ago it last let an alert through; if the same service
alerts again within `cooldown`, the repeat is suppressed. General DSL form: run(msg)
-> the alert, or None if suppressed.
"""


class Deduper:
    def __init__(self, cooldown=3):
        self.cooldown = cooldown
        self.last = {}
        self.n = 0

    def run(self, msg):
        self.n += 1
        svc = msg["service"]
        if svc in self.last and self.n - self.last[svc] <= self.cooldown:
            self.last[svc] = self.n
            return None                              # suppressed repeat
        self.last[svc] = self.n
        return msg


if __name__ == "__main__":
    d = Deduper(cooldown=1)
    seq = [{"service": "web"}, {"service": "web"}, {"service": "db"}, {"service": "web"}]
    outs = [d.run(m) for m in seq]
    print(outs)
    assert outs[0] and outs[1] is None and outs[2] and outs[3], outs
    print("OK: deduper suppresses a quick repeat, passes the rest")
