"""
situation_room_runnable.py

Same structure as situation_room_natural.py, but with the Anthropic API
and feedparser RSS fetch replaced by mocks so the code can execute in
a sandbox without network or API credentials.

The point of this file is to confirm that the structure Claude produced
is internally consistent and runs end-to-end, not to produce real
classifications.
"""

from __future__ import annotations

import asyncio
import json
import random
from pathlib import Path


MODEL = "claude-sonnet-4-6-mock"
OUTPUT_PATH = Path(__file__).parent / "briefings.jsonl"


# --------------------------------------------------------------------------- #
# MOCK: feedparser                                                            #
# --------------------------------------------------------------------------- #


class _FakeEntry:
    def __init__(self, title, summary, link):
        self.title, self.summary, self.link = title, summary, link


class _FakeFeed:
    def __init__(self, entries):
        self.entries = entries


def _fake_feedparser_parse(url):
    """Return a tiny fixture feed for each source URL."""
    if "bbc" in url:
        return _FakeFeed([
            _FakeEntry(
                "BBC: Major earthquake strikes Indonesia",
                "A 7.3 magnitude earthquake hit Sulawesi this morning, killing at least 14 people.",
                "https://example.com/bbc/1",
            ),
            _FakeEntry(
                "BBC: EU agrees on emissions target",
                "European member states reached a compromise on the 2035 emissions trading scheme.",
                "https://example.com/bbc/2",
            ),
            _FakeEntry(
                "BBC: Champions League final preview",
                "The final between Madrid and Munich begins Saturday at the Berlin Olympiastadion.",
                "https://example.com/bbc/3",
            ),
        ])
    if "npr" in url:
        return _FakeFeed([
            _FakeEntry(
                "NPR: US Fed holds rates steady",
                "The Federal Reserve announced no change to the benchmark rate at its latest meeting.",
                "https://example.com/npr/1",
            ),
            _FakeEntry(
                "NPR: Wildfire spreads in northern California",
                "A wildfire near Lake Shasta has forced evacuations of three towns.",
                "https://example.com/npr/2",
            ),
            _FakeEntry(
                "NPR: Researcher wins Nobel for protein folding",
                "A Stanford researcher's work on protein folding has won the chemistry Nobel.",
                "https://example.com/npr/3",
            ),
        ])
    if "aljazeera" in url:
        return _FakeFeed([
            _FakeEntry(
                "Al Jazeera: Talks resume on Sudan ceasefire",
                "Diplomatic delegations from the African Union met in Geneva to discuss the conflict.",
                "https://example.com/aj/1",
            ),
            _FakeEntry(
                "Al Jazeera: Floods displace thousands in Bangladesh",
                "Monsoon flooding in the south has displaced over 200,000 people; relief is slow.",
                "https://example.com/aj/2",
            ),
            _FakeEntry(
                "Al Jazeera: New art biennale opens in Marrakech",
                "The third Marrakech Biennale opened with installations by 40 international artists.",
                "https://example.com/aj/3",
            ),
        ])
    return _FakeFeed([])


# Drop the import; install the mock as `feedparser`.
class _FeedparserModule:
    parse = staticmethod(_fake_feedparser_parse)


feedparser = _FeedparserModule()


# --------------------------------------------------------------------------- #
# MOCK: AsyncAnthropic                                                        #
# --------------------------------------------------------------------------- #


class _MockResponse:
    def __init__(self, text):
        class _C:
            def __init__(self, t):
                self.text = t
        self.content = [_C(text)]


class AsyncAnthropic:
    """Mock that pattern-matches on the system prompt to decide what to return."""

    async def messages_create_classify(self, user):
        # Very rough heuristic so the output looks plausible.
        keywords_critical = ["earthquake", "wildfire", "ceasefire", "floods displace"]
        keywords_high     = ["evacuat", "killing", "conflict"]
        keywords_low      = ["preview", "biennale", "Nobel"]
        text = user.lower()
        if any(k in text for k in keywords_critical):
            return "CRITICAL"
        if any(k in text for k in keywords_high):
            return "HIGH"
        if any(k in text for k in keywords_low):
            return "LOW"
        return "MEDIUM"

    async def messages_create_location(self, user):
        # Pull a noun-like word that looks like a location.
        for hint in ("Indonesia", "California", "Sudan", "Bangladesh",
                     "Marrakech", "Berlin", "EU", "Geneva", "Stanford"):
            if hint.lower() in user.lower():
                return hint
        return "Global"

    async def messages_create_briefing(self, user):
        # Just summarise back a couple of sentences.
        for line in user.splitlines():
            if line.lower().startswith("title:"):
                title = line[len("Title:"):].strip()
                break
        else:
            title = "an unspecified situation"
        return (
            f"Briefing: {title}. The situation continues to develop and is being "
            "monitored closely by regional and international observers."
        )

    class messages:
        @staticmethod
        async def create(model, max_tokens, system, messages):
            """Dispatch based on system prompt content. Order matters —
            the briefing prompt mentions 'severity' and 'location' as
            things to mention, so we check 'briefing' FIRST."""
            outer = AsyncAnthropic._instance
            user_content = messages[0]["content"]
            sys_lower = system.lower()
            if "write" in sys_lower and "briefing" in sys_lower:
                text = await outer.messages_create_briefing(user_content)
            elif "classify" in sys_lower:
                text = await outer.messages_create_classify(user_content)
            elif "identify the primary geographic" in sys_lower:
                text = await outer.messages_create_location(user_content)
            else:
                text = "OK"
            # Cheap simulated latency
            await asyncio.sleep(0.01)
            return _MockResponse(text)


# Make the inner classmethod able to find the outer instance.
AsyncAnthropic._instance = AsyncAnthropic()


# --------------------------------------------------------------------------- #
# All the rest is identical to situation_room_natural.py                      #
# --------------------------------------------------------------------------- #


FEEDS = {
    "bbc":        "http://feeds.bbci.co.uk/news/world/rss.xml",
    "npr":        "https://feeds.npr.org/1004/rss.xml",
    "al_jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
}


async def fetch_articles(name, url, max_articles=3):
    loop = asyncio.get_event_loop()
    parsed = await loop.run_in_executor(None, feedparser.parse, url)
    return [
        {
            "source": name,
            "title": entry.title,
            "body": getattr(entry, "summary", entry.title),
            "url": entry.link,
        }
        for entry in parsed.entries[:max_articles]
    ]


async def classify_severity(client, article):
    response = await client.messages.create(
        model=MODEL,
        max_tokens=20,
        system=(
            "You classify news article severity. "
            "Respond with exactly one of: LOW, MEDIUM, HIGH, CRITICAL. "
            "Nothing else."
        ),
        messages=[{"role": "user", "content": f"{article['title']}\n\n{article['body']}"}],
    )
    return response.content[0].text.strip().upper()


async def identify_location(client, article):
    response = await client.messages.create(
        model=MODEL,
        max_tokens=60,
        system=(
            "You identify the primary geographic location of a news article. "
            "Respond with 'Country, City' if both are clear, just 'Country' if "
            "only that is clear, or 'Global' if no specific location applies."
        ),
        messages=[{"role": "user", "content": f"{article['title']}\n\n{article['body']}"}],
    )
    return response.content[0].text.strip()


async def write_briefing(client, article):
    response = await client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=(
            "You write short, factual news briefings. "
            "Write 2-3 sentences summarising the situation. "
            "Mention the location and reflect the assigned severity."
        ),
        messages=[{"role": "user", "content": (
            f"Title: {article['title']}\n"
            f"Body: {article['body']}\n"
            f"Severity: {article['severity']}\n"
            f"Location: {article['location']}\n"
        )}],
    )
    return response.content[0].text.strip()


async def enrich_article(client, article):
    severity, location = await asyncio.gather(
        classify_severity(client, article),
        identify_location(client, article),
    )
    article["severity"] = severity
    article["location"] = location
    article["briefing"] = await write_briefing(client, article)
    return article


def emit_outputs(articles):
    with OUTPUT_PATH.open("w") as f:
        for article in articles:
            if article["severity"] == "CRITICAL":
                print("=" * 60)
                print(f"[CRITICAL] {article['location']}")
                print(article["briefing"])
                print(f"  source: {article['source']}  url: {article['url']}")
                print("=" * 60)
            f.write(json.dumps(article) + "\n")
    print(f"\nWrote {len(articles)} briefings to {OUTPUT_PATH}")


async def main():
    client = AsyncAnthropic()
    article_lists = await asyncio.gather(
        *(fetch_articles(name, url) for name, url in FEEDS.items())
    )
    articles = [a for lst in article_lists for a in lst]
    print(f"Fetched {len(articles)} articles total.")
    enriched = await asyncio.gather(*(enrich_article(client, a) for a in articles))
    emit_outputs(enriched)


if __name__ == "__main__":
    asyncio.run(main())
