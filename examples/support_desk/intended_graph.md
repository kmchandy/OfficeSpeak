# support_desk — intended graph (ground truth)

Roster — each agent: role · state · reads · emits

- **Rita — record-keeper (the shared files).** State: one file per
  customer (orders, complaints, promises). Reads: look-up requests.
  Emits: the requested file; applies updates.
- **Gary — gate.** State: idle/busy. Admits one email at a time; releases
  when Mia has filed the outcome.
- **Hana — helper.** Reads: the email; the customer's file (from Rita).
  Emits: email + context → Cal.
- **Cal — checker.** Reads: email + context. Emits: email + context + a
  policy/promise flag → Mia.
- **Mia — manager.** Reads: email + context + flag; the customer's file.
  Emits: a reply → the customer; files the outcome → Rita; signals Gary.

```mermaid
flowchart TD
  E[customer emails]:::src --> G[Gary — gate<br/>one at a time]:::coord
  G --> H[Hana — helper]:::agent
  H --> C[Cal — checker]:::agent
  C --> Mi[Mia — manager]:::agent
  H <-->|look up file| R[(Rita — customer files)]:::store
  Mi <-->|read / file outcome| R
  Mi --> Rep[reply to customer]:::sink
  Mi -.done.-> G
  classDef src fill:#dbeafe,stroke:#1d4ed8
  classDef sink fill:#fef3c7,stroke:#92400e
  classDef store fill:#ede9fe,stroke:#6d28d9
  classDef coord fill:#fee2e2,stroke:#b91c1c
  classDef agent fill:#dcfce7,stroke:#15803d
```

Coordination: one email at a time (Gary), released by Mia's "done", so
reads/writes of the shared files are ordered → deterministic given the
email order.
