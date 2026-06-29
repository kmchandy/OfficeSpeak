# Office: situation_room

Sources: bbc_world(max_articles=3),
         npr_news(max_articles=3),
         al_jazeera(max_articles=3)
Sinks: intelligence_display,
       jsonl_recorder_briefing(path="briefings.jsonl")

Agents:
V0 is a severity_classifier.
V1 is a geolocator.
V2 is a briefing_writer.

Connections:
bbc_world's destination is V0.
npr_news's destination is V0.
al_jazeera's destination is V0.

V0's out is V1.
V1's out is V2.
V2's critical is intelligence_display, jsonl_recorder_briefing.
V2's else is jsonl_recorder_briefing.
