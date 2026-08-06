# Office: weather_alert

Sources: weather(poll_interval=600)
Sinks: intelligence_display,
       discard

Agents:
V0 is a severity_classifier.

Connections:
weather's destination is V0.

V0's severe is intelligence_display.
V0's else is discard.
