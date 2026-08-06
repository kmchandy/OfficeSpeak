# Office: inbox_triage

Sources: gmail(unread_only=True, max_emails=20)
Sinks: intelligence_display,
       jsonl_recorder_archive(path="email_archive.jsonl"),
       discard

Agents:
V0 is an urgency_classifier.

Connections:
gmail's destination is V0.

V0's urgent is intelligence_display.
V0's normal is jsonl_recorder_archive.
V0's else is discard.
