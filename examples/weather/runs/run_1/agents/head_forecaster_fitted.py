"""head-forecaster body — FITTED version (after Pat's correction).

Instead of scoring each service independently, choose the blend of the services'
forecasts that WOULD HAVE been most accurate over the last couple of weeks, then apply
that blend to tomorrow. Produced by the OfficeSpeak Project as capability-5 (refine an
agent's body). The office graph is unchanged; only this body changed, plus the SHAPE of
what the Repository hands back (now arranged by day, so whole blends can be graded).
"""


class HeadForecaster:
    def __init__(self, lookback_days=14, step=0.05, repo=None):
        self.lookback = lookback_days
        self.step = step            # how finely we try different splits of the trust
        self.repo = repo

    def run(self, msg):
        # msg: {"day": "2026-07-07", "forecasts": {"open_meteo": 30.5, "met_no": 29.0}}
        day, todays = msg["day"], msg["forecasts"]
        services = sorted(todays)

        self.repo.file_forecasts(day, todays)

        # recent history arranged BY DAY:
        #   history[day] = {"forecasts": {service: value, ...}, "actual": value or None}
        history = self.repo.recent(self.lookback)
        graded = [d for d in history.values()
                  if d["actual"] is not None
                  and all(s in d["forecasts"] for s in services)]

        if graded:
            best_w, best_err = None, None
            for w in self._splits(len(services), self.step):
                error = 0.0
                for d in graded:
                    blend = sum(w[i] * d["forecasts"][s] for i, s in enumerate(services))
                    error += abs(blend - d["actual"])
                error /= len(graded)
                if best_err is None or error < best_err:
                    best_err, best_w = error, w
            weights = {s: best_w[i] for i, s in enumerate(services)}
        else:
            even = 1.0 / len(services)
            weights = {s: even for s in services}

        forecast = round(sum(todays[s] * weights[s] for s in services), 1)
        result = {"day": day, "forecast": forecast,
                  "weights": {s: round(weights[s], 3) for s in services}}
        self.repo.file_office_forecast(result)
        return result

    @staticmethod
    def _splits(n, step):
        """Every way to split 100% of the trust among n services in `step` steps."""
        from itertools import product
        ticks = round(1 / step)
        for combo in product(range(ticks + 1), repeat=n):
            if sum(combo) == ticks:
                yield [c / ticks for c in combo]
