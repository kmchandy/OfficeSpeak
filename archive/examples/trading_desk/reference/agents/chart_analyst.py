"""chart-analyst worker body (Python, deterministic) — built from Pat's description.

Rule: for each stock, keep a moving average of the price over a recent window
(~30 one-minute ticks = a 30-minute moving average) and signal at the moment the
price CROSSES the average — buy when it crosses from below to above, sell when it
crosses from above to below. Signal only on the crossing, not on every tick.

General DSL form: an object with run(msg). msg = {"symbol": str, "price": float};
run returns a signal dict or None. In a DSL office the body would self.send(...).
"""
from collections import deque, defaultdict


class ChartAnalyst:
    def __init__(self, window_ticks=30):
        self.window_ticks = window_ticks
        self._prices = defaultdict(lambda: deque(maxlen=window_ticks))
        self._side = {}   # symbol -> +1 (above MA) or -1 (at/below MA)

    def run(self, msg):
        sym = msg["symbol"]
        price = float(msg["price"])
        w = self._prices[sym]
        w.append(price)
        ma = sum(w) / len(w)
        side = 1 if price > ma else -1
        prev = self._side.get(sym)
        self._side[sym] = side
        if prev is not None and side != prev:
            return {"symbol": sym,
                    "signal": "buy" if side == 1 else "sell",
                    "price": price, "ma": round(ma, 4)}
        return None


if __name__ == "__main__":
    a = ChartAnalyst(window_ticks=3)
    series = [100, 100, 100, 101, 102, 103, 100, 98, 97]
    fired = [s for s in (a.run({"symbol": "AAPL", "price": p}) for p in series) if s]
    for s in fired:
        print(s)
    assert [s["signal"] for s in fired] == ["buy", "sell"], fired
    print("OK: buy on the up-cross, sell on the down-cross")
