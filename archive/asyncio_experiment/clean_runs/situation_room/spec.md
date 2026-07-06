# situation_room — Pat's spec

This is Pat's English description of the situation_room app. Treat it
as the canonical Pat-style description: a non-coder describing what
they want, with sources/processing/output mentioned but no topology,
agent count, or framework details specified.

---

I want a daily intelligence digest. Pull articles from three
world-news RSS feeds (BBC, NPR, Al Jazeera). For each article, classify
the severity (low / medium / high / critical), identify the geographic
location, and write a short briefing. Show me critical-severity
briefings in my terminal; save all of them to a JSONL file.
