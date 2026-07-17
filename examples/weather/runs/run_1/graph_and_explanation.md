# weather / run_1 — held-out build (OfficeSpeak Project, gold standard)

Fresh chat in the OfficeSpeak project; only `spec.md` pasted. The assistant produced the
graph, the explanation, the diagram, and the head-forecaster body (saved in `agents/`).

## The office

```
Agents:
  open_meteo, met_no — sources: each service's forecast of tomorrow's high (async)
  actuals            — source: recorded actual high, once a day, tagged with its day
  Repository — record(holds: each service's past forecasts by day · actual highs by day ·
                             the office's own past forecasts · the weights used each day)
  Gate       — gate (one day's forecast at a time)
  head-forecaster — Python: weight each service by recent accuracy, blend tomorrow's forecasts
  FORECAST   — sink
Wiring:
  open_meteo, met_no -> merge_synch -> Gate -> head-forecaster   # wait for both, one day at a time
  actuals -> Repository                                          # file the actual against its day
  head-forecaster <-> Repository                                 # file forecasts; ask history (wait); write forecast+weights
  head-forecaster -> FORECAST
  head-forecaster ..done..> Gate
Notes:
  merge_synch joins BOTH services' forecasts for the same day (head needs both to blend) and must
  sit BEFORE the Gate — gating the two services separately would jam the join. The Gate keeps one
  day's cycle whole because the head reads and writes the shared Repository. The actual high is
  filed as it arrives; nothing waits on it.
```

Diagram:
```
   open_meteo ┐
              ├─ merge_synch ─→ Gate ─→ head-forecaster ─→ FORECAST
   met_no ────┘                              ↕
                                         Repository ←─ actuals
```

## Explanation (abridged)

The two services send tomorrow's forecast at their own times; the office waits for both,
then lets one day through the door. The head-forecaster files the two forecasts, asks the
Repository for the last ~14 days of forecasts and how they turned out, waits, then trusts
each service by its recent accuracy, blends today's two forecasts by those trust levels,
writes the forecast + weights to the Repository and FORECAST, and opens the door for the
next day. Actual highs are filed against their day as they arrive, so each past forecast
sits next to what really happened.

## Things I assumed (from the build)

1. Both services report once a day and stay in step, so they can be paired. **If a service
   skips a day, the join would sit waiting for it** — offered to make it tolerate a missing
   service.
2. A day's forecast begins when both forecasts are in; the actual is filed whenever it
   arrives; nothing waits on it.
3. "Trust" = recent accuracy (smaller recent average error → bigger share) over ~14 days; a
   brand-new service starts with an even share. **Offered to swap in weights fitted to be
   literally most accurate over the window** (the regression the spec asked for).
4. The one-at-a-time door is there because the head reads and writes the shared Repository.
5. Every forecast carries its day, so a forecast and its later actual can be matched.
