"""news-analyst credential-free STAND-IN for the LLM body (news_analyst.md).

Same message shape as the real LLM agent, but decides by keyword so the office can
run end-to-end without a model credential. Swap for the LLM body when available.
"""

BULLISH = ("cuts rates", "rate cut", "upgrade", "beats", "raised guidance", "approval")
BEARISH = ("hikes rates", "rate hike", "downgrade", "misses", "probe", "lawsuit", "recall")


class NewsAnalystStub:
    def __init__(self, symbols):
        self.symbols = symbols

    def run(self, msg):
        text = msg["headline"].lower()
        hint = msg.get("about", "").lower()
        sym = next((s for s in self.symbols
                    if s.lower() in text or s.lower() in hint), None)
        if sym is None:
            return None
        if any(k in text for k in BULLISH):
            return {"symbol": sym, "signal": "buy", "reason": msg["headline"]}
        if any(k in text for k in BEARISH):
            return {"symbol": sym, "signal": "sell", "reason": msg["headline"]}
        return None


if __name__ == "__main__":
    n = NewsAnalystStub(symbols=["AAPL", "TSLA"])
    items = [
        {"headline": "Fed cuts rates by 50 bps", "about": "AAPL"},
        {"headline": "Analyst downgrade for TSLA on demand worries", "about": "TSLA"},
        {"headline": "Local weather remains mild", "about": ""},
    ]
    outs = [n.run(i) for i in items]
    for o in outs:
        print(o)
    assert outs[0]["signal"] == "buy" and outs[1]["signal"] == "sell" and outs[2] is None
    print("OK: headlines map to buy / sell / none")
