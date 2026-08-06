# Gallery example — anomaly_monitor (detect-anomaly)

A worked example: per-key windowed state, a router, and the *restraint* of using no
fair_merge and no gate because the office does not need them.

## Pat's description

Watch our services' health and alert me when something looks abnormal. For each
service (web, db, cache) a reading arrives regularly. A **monitor** learns each
service's normal range and flags a reading far outside it; a **deduper** groups
repeated alerts for the same service; a **router** sends each alert to whoever owns
that service. Alerts go to a file, ALERTS.

## The office

```
Agents:
  metrics — source: health readings {service, value}
  monitor — per-service rolling average/spread; flags a reading > 3 std out · state: per-service window
  deduper — suppresses a repeat alert for the same service in quick succession · state: per-service last-alert
  router  — sends each alert to the owner of its service (if/elif/else)
  ALERTS  — sink
Wiring:
  metrics -> monitor -> deduper -> router -> ALERTS
Notes:
  A single readings stream, so NO fair_merge. No shared writable state (each worker's
  memory is its own, keyed by service), so NO gate. The router is the only branching.
```

## Explanation for Pat

Each reading goes to the monitor, which keeps a separate recent average and spread for
every service and flags a value more than a few standard deviations out (it needs a few
readings first to learn "normal"). The deduper drops a repeat alert for a service that
just alerted, so you get one message, not twenty. The router looks up who owns the
service and sends the alert there. Nothing is shared or written jointly, so the office
handles readings as fast as they come — no one-at-a-time needed.

## Worker bodies

**monitor (Python — computational):**
```python
from collections import defaultdict, deque
import math
class Monitor:
    def __init__(self, window=20, z=3.0):
        self.w = defaultdict(lambda: deque(maxlen=window)); self.z = z
    def run(self, msg):
        s, v = msg["service"], float(msg["value"]); w = self.w[s]; w.append(v)
        n = len(w)
        if n >= 5:
            mean = sum(w)/n; std = math.sqrt(max(sum((x-mean)**2 for x in w)/n, 0.0))
            if std > 0 and abs((v-mean)/std) >= self.z:
                return {"service": s, "value": v, "z": round((v-mean)/std, 2)}
        return None
```

**deduper (Python — computational):**
```python
class Deduper:
    def __init__(self, cooldown=3):
        self.cooldown = cooldown; self.last = {}; self.n = 0
    def run(self, msg):
        self.n += 1; s = msg["service"]
        if s in self.last and self.n - self.last[s] <= self.cooldown:
            self.last[s] = self.n; return None
        self.last[s] = self.n; return msg
```
