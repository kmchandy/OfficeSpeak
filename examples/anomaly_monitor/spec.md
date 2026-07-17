# anomaly_monitor — Pat's office description

A second office shape: **detect-anomaly** (per-key windowed state), to contrast the
trading desk's deliberate-and-decide shape. All computational — no LLM worker.

## Overview

I want an office that watches our services' health and alerts me when something looks
abnormal.

## Inputs

A continuous stream of **health readings** — for each of our services (web, db,
cache), a number arrives regularly (say, a response time).

## Outputs

**Alerts** written to a file, ALERTS — each naming the service, the abnormal reading,
and how far out of the normal range it was.

## Workers

- **monitor** — for each service, learns what "normal" looks like over a recent
  window and flags a reading that is far outside it.
- **deduper** — groups repeated alerts for the same service so I get one message, not
  twenty in a row.
- **router** — sends each alert to whoever owns that service.

## What each worker does

- **monitor.** For each service separately, keeps a recent window of readings and its
  average and spread. When a new reading is more than a few standard deviations from
  that service's recent average, it raises an alert (service, value, how far out) to
  the deduper. Otherwise it stays quiet. Plain arithmetic per service.
- **deduper.** Keeps track of when it last alerted for each service; if the same
  service alerts again right away, it suppresses the repeat and passes only the first.
- **router.** Looks up who owns the service and sends the alert to that owner. (In the
  minimal runnable version this is a single ALERTS file with the owner tagged; a
  router splitting to per-owner sinks is the full version.)
