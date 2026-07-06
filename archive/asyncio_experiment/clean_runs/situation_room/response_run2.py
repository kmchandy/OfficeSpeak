"""
Daily intelligence digest.
Pulls articles from three world-news RSS feeds (BBC, NPR, Al Jazeera). For each
article it uses the Anthropic API to (1) classify severity, (2) identify the
geographic location, and (3) write a short briefing. Critical-severity briefings
are printed to the terminal; every briefing is appended to a JSONL file.
Run it:
    pip install feedparser anthropic
    export ANTHROPIC_API_KEY=sk-ant-...      # Windows: set ANTHROPIC_API_KEY=...
    python digest.py
Structure (so a parsing tool can read it):
  - SOURCES                 : RSS feeds declared at module top.
  - async def <agent>(msg)  : each LLM-driven agent. dict in -> dict out.
  - class SeverityTally      : a Python-driven stateful agent (__init__ + process).
  - def process_one(msg)    : the per-item pipeline that wires the agents together.
  - def send_to(msg, sink)  : dispatches a finished message to a named sink.
"""
import asyncio
import html
import json
import os
import re
import sys
from datetime import datetime, timezone
try:
    import feedparser
    from anthropic import AsyncAnthropic
except ImportError:
    sys.exit("Missing dependencies. Run:  pip install feedparser anthropic")
# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
# World-news RSS feeds. Add or swap feeds here.
SOURCES = {
    "bbc":    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "npr":    "https://feeds.npr.org/1004/rss.xml",
    "al_jaz": "https://www.aljazeera.com/xml/rss/all.xml",
}
# Where every briefing is saved (one JSON object per line, appended each run).
OUTPUT_PATH = "digest.jsonl"
# How many of the newest articles to take from each feed. Each article costs
# 3 API calls (severity + location + briefing), so raise this with cost in mind.
MAX_ARTICLES_PER_SOURCE = 5
# Anthropic model. Haiku is fast and cheap for triage + short briefings; switch
# to "claude-sonnet-4-6" if you want richer briefings.
MODEL = "claude-haiku-4-5-20251001"
# One shared async client. It reads ANTHROPIC_API_KEY from the environment.
client = AsyncAnthropic()
# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #
def _clean(text):
    """Strip HTML tags, decode entities, and collapse whitespace from a summary."""
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()
def _extract_json(text):
    """Pull the first JSON object out of an LLM response, tolerating stray prose."""
    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}
async def _ask_json(prompt):
    """Send a prompt to the Anthropic API and return the JSON object it produces.
    Failures (network, rate limits, bad output) return an empty dict so that one
    bad article never crashes the whole run.
    """
    try:
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_json(resp.content[0].text)
    except Exception as exc:
        print(f"[warn] API call failed: {exc}", file=sys.stderr)
        return {}
async def fetch_source(source_key):
    """Fetch and normalize the newest articles from one feed in SOURCES."""
    url = SOURCES[source_key]
    # feedparser.parse blocks on the network, so run it in a worker thread.
    feed = await asyncio.to_thread(feedparser.parse, url)
    articles = []
    for entry in feed.entries[:MAX_ARTICLES_PER_SOURCE]:
        summary = entry.get("summary") or entry.get("description") or ""
        articles.append({
            "source": source_key,
            "title": entry.get("title", ""),
            "summary": _clean(summary),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
        })
    return articles
# --------------------------------------------------------------------------- #
# LLM-driven agents: each takes a dict and returns a dict.
# --------------------------------------------------------------------------- #
async def classify_severity(message):
    """Classify how serious a news article is: low, medium, high, or critical."""
    prompt = (
        "You are a news triage assistant. Rate the severity of the article below.\n\n"
        "Severity scale:\n"
        "- low: routine or minor news with little wider impact\n"
        "- medium: notable regional news, no immediate widespread danger\n"
        "- high: serious events causing significant harm or large-scale disruption\n"
        "- critical: mass casualties, war escalation, major disasters, or events of "
        "urgent global significance\n\n"
        f"Title: {message['title']}\n"
        f"Summary: {message['summary']}\n\n"
        'Return JSON only, no explanation, no nested JSON: '
        '{"severity": "low|medium|high|critical", "reason": "one short sentence"}'
    )
    data = await _ask_json(prompt)
    return {
        "severity": str(data.get("severity", "unknown")).lower(),
        "severity_reason": data.get("reason", ""),
    }
async def identify_location(message):
    """Identify the single main geographic location an article is about."""
    prompt = (
        "Identify the single main geographic location of the news article below.\n"
        'If no specific place applies, use "global".\n\n'
        f"Title: {message['title']}\n"
        f"Summary: {message['summary']}\n\n"
        'Return JSON only, no explanation, no nested JSON: '
        '{"location": "city or region", "country": "country or global"}'
    )
    data = await _ask_json(prompt)
    return {
        "location": data.get("location", "unspecified"),
        "country": data.get("country", "unspecified"),
    }
async def write_briefing(message):
    """Write a short, neutral 2-3 sentence intelligence briefing for an article."""
    prompt = (
        "Write a concise, neutral intelligence briefing (2-3 sentences) capturing "
        "the key facts of the news article below. Plain English, no speculation.\n\n"
        f"Title: {message['title']}\n"
        f"Summary: {message['summary']}\n\n"
        'Return JSON only, no explanation, no nested JSON: '
        '{"briefing": "your 2-3 sentence briefing"}'
    )
    data = await _ask_json(prompt)
    return {"briefing": data.get("briefing", "")}
# --------------------------------------------------------------------------- #
# Python-driven stateful agent: a class with __init__ and one process method.
# --------------------------------------------------------------------------- #
class SeverityTally:
    """Counts how many briefings fall into each severity bucket across a run."""
    def __init__(self):
        self.counts = {"low": 0, "medium": 0, "high": 0, "critical": 0, "unknown": 0}
    def process(self, message):
        """Record one enriched article's severity, then pass the message through."""
        sev = message.get("severity", "unknown")
        if sev not in self.counts:
            sev = "unknown"
        self.counts[sev] += 1
        return message
# --------------------------------------------------------------------------- #
# Sinks
# --------------------------------------------------------------------------- #
def send_to(message, sink_name, **kwargs):
    """Dispatch a finished briefing to a named sink ("terminal" or "jsonl")."""
    if sink_name == "terminal":
        block = (
            "\n" + "=" * 70 + "\n"
            f"  CRITICAL  |  {message.get('location', '?')}, "
            f"{message.get('country', '?')}  |  source: {message.get('source', '?')}\n"
            + "-" * 70 + "\n"
            f"  {message.get('title', '')}\n\n"
            f"  {message.get('briefing', '')}\n\n"
            f"  why critical: {message.get('severity_reason', '')}\n"
            f"  link: {message.get('link', '')}\n"
            + "=" * 70
        )
        print(block)
    elif sink_name == "jsonl":
        path = kwargs.get("path", OUTPUT_PATH)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(message, ensure_ascii=False) + "\n")
    else:
        raise ValueError(f"Unknown sink: {sink_name}")
# --------------------------------------------------------------------------- #
# Per-item pipeline
# --------------------------------------------------------------------------- #
async def process_one(message):
    """Per-item pipeline body: enrich one article and route it to sinks.
    The three LLM agents are independent (each only needs the raw article), so
    they run concurrently with asyncio.gather.
    """
    severity, location, briefing = await asyncio.gather(
        classify_severity(message),
        identify_location(message),
        write_briefing(message),
    )
    enriched = {
        **message,
        **severity,
        **location,
        **briefing,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }
    # Save every briefing.
    send_to(enriched, "jsonl", path=OUTPUT_PATH)
    # Show only the critical ones in the terminal.
    if enriched.get("severity") == "critical":
        send_to(enriched, "terminal")
    return enriched
# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
async def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY before running (export ANTHROPIC_API_KEY=...).")
    print(f"Fetching world news from: {', '.join(SOURCES)}")
    batches = await asyncio.gather(*(fetch_source(k) for k in SOURCES))
    articles = [a for batch in batches for a in batch]
    print(f"Fetched {len(articles)} articles. Briefing them with the Anthropic API...")
    # Process every article concurrently.
    enriched = await asyncio.gather(*(process_one(a) for a in articles))
    # Run the results through the stateful tally agent for an end-of-run summary.
    tally = SeverityTally()
    for item in enriched:
        tally.process(item)
    print("\n=== Digest complete ===")
    print(f"Saved {len(enriched)} briefings to {OUTPUT_PATH}")
    print("Severity breakdown: "
          + ", ".join(f"{k}={v}" for k, v in tally.counts.items() if v))
    if tally.counts["critical"] == 0:
        print("No critical-severity articles in this batch.")
if __name__ == "__main__":
    asyncio.run(main())
