#!/usr/bin/env python3
"""Daily intelligence digest from world-news RSS feeds."""
import json
import os
import re
import sys
from datetime import datetime, timezone
import feedparser
from anthropic import Anthropic
FEEDS = {
    "BBC": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "NPR": "https://feeds.npr.org/1004/rss.xml",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
}
MODEL = "claude-sonnet-4-6"
OUTPUT_FILE = "digest.jsonl"
MAX_PER_FEED = 10
client = Anthropic()  # reads ANTHROPIC_API_KEY from environment
def ask(prompt, max_tokens=400):
    resp = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in resp.content if b.type == "text").strip()
def extract_json(text):
    """Pull the first JSON object out of a model response."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return json.loads(match.group(0)) if match else {}
def analyze(title, summary):
    prompt = f"""You are an intelligence analyst. Analyze this news item.
Title: {title}
Summary: {summary}
Return JSON only, no explanation, no nested JSON:
{{"severity": "low|medium|high|critical", "location": "place name or Global", "briefing": "2-3 sentence briefing"}}"""
    return extract_json(ask(prompt))
def fetch_articles():
    articles = []
    for source, url in FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries[:MAX_PER_FEED]:
            articles.append({
                "source": source,
                "title": entry.get("title", "").strip(),
                "summary": re.sub(r"<[^>]+>", "", entry.get("summary", "")).strip(),
                "link": entry.get("link", ""),
            })
    return articles
def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY in your environment first.")
    articles = fetch_articles()
    print(f"Fetched {len(articles)} articles. Analyzing...\n")
    results = []
    for art in articles:
        try:
            analysis = analyze(art["title"], art["summary"])
        except Exception as e:
            print(f"  skipped '{art['title'][:50]}': {e}", file=sys.stderr)
            continue
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": art["source"],
            "title": art["title"],
            "link": art["link"],
            "severity": analysis.get("severity", "unknown"),
            "location": analysis.get("location", "unknown"),
            "briefing": analysis.get("briefing", ""),
        }
        results.append(record)
    with open(OUTPUT_FILE, "w") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    critical = [r for r in results if r["severity"] == "critical"]
    print("=" * 60)
    print(f"CRITICAL BRIEFINGS ({len(critical)})")
    print("=" * 60)
    for r in critical:
        print(f"\n[{r['source']}] {r['location']}")
        print(f"  {r['title']}")
        print(f"  {r['briefing']}")
        print(f"  {r['link']}")
    if not critical:
        print("\nNo critical-severity items today.")
    print(f"\nAll {len(results)} briefings saved to {OUTPUT_FILE}")
if __name__ == "__main__":
    main()
