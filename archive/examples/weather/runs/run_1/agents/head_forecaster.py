"""head-forecaster body — produced by the OfficeSpeak Project (held-out, gold standard).

Each day: blend the services' forecasts for tomorrow, giving more weight to whichever
service has been closer to the real highs lately.
"""


class HeadForecaster:
    def __init__(self, lookback_days=14, repo=None):
        self.lookback = lookback_days
        self.repo = repo                       # a handle to the Repository

    def run(self, msg):
        # msg has both services' forecasts for the same day, e.g.
        #   {"day": "2026-07-07", "forecasts": {"open_meteo": 30.5, "met_no": 29.0}}
        day, todays = msg["day"], msg["forecasts"]

        # 1. File today's service forecasts so they can be scored later.
        self.repo.file_forecasts(day, todays)

        # 2. Ask the Repository for recent history — and wait for the answer.
        #    history = {"open_meteo": [(forecast, actual), ...],   # actual may be None
        #               "met_no":     [(forecast, actual), ...]}
        history = self.repo.recent(self.lookback)

        # 3. Trust each service by how close it has been lately.
        weights = {}
        for service in todays:
            scored = [(f, a) for f, a in history.get(service, []) if a is not None]
            if scored:
                avg_error = sum(abs(f - a) for f, a in scored) / len(scored)
                weights[service] = 1.0 / (avg_error + 1.0)   # smaller error -> more trust
            else:
                weights[service] = 1.0                        # no track record yet: even share
        total = sum(weights.values()) or 1.0
        weights = {s: w / total for s, w in weights.items()}

        # 4. Blend today's forecasts by those trust levels.
        forecast = round(sum(todays[s] * weights[s] for s in todays), 1)

        result = {"day": day, "forecast": forecast,
                  "weights": {s: round(w, 3) for s, w in weights.items()}}

        # 5. Record the office's own forecast + weights, then hand it out.
        self.repo.file_office_forecast(result)
        return result        # -> FORECAST, and opens the door for the next day
