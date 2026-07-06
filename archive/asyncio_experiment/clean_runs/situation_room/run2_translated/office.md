# Office: situation_room

Sources: bbc(url="https://feeds.bbci.co.uk/news/world/rss.xml"),
         npr(url="https://feeds.npr.org/1004/rss.xml"),
         al_jaz(url="https://www.aljazeera.com/xml/rss/all.xml")
Sinks: jsonl_recorder(path="digest.jsonl"),
       intelligence_display

Agents:
V0 is a classify_severity.
V1 is an identify_location.
V2 is a write_briefing.
V3 is a severitytally.
V4 is a synchronizer(inports=["severity", "location", "briefing"]).

Connections:
bbc's destination is V0, V1, V2.
npr's destination is V0, V1, V2.
al_jaz's destination is V0, V1, V2.

V0's out is V4's severity.
V1's out is V4's location.
V2's out is V4's briefing.
V4's out is jsonl_recorder, V3.
V4's critical is intelligence_display.
