# weather — Pat's office description (held-out demo — NOT in the gallery)

Predict-and-learn shape. Pat pastes the section below into a fresh chat in the
OfficeSpeak project. Our pre-registered predictions are in `spec_review.md`.

---

## Overview

I want an office that forecasts tomorrow's high temperature for our city each day, and
gets better over time by checking how its past forecasts turned out — trusting the
weather services that have been more accurate.

## Inputs

1. Forecasts of tomorrow's high from a couple of weather services — for example
   Open-Meteo and Met.no. Each service sends its forecast on its own schedule, at
   unpredictable times during the day.
2. Once a day, the **actual** high temperature that was recorded — the real outcome for
   a day we had forecast.

## Outputs

Each day the office writes its own forecast of tomorrow's high to a file, FORECAST,
together with how much it weighted each service.

## Workers

- **repository** — keeps the office's full history: each service's past forecasts, the
  actual highs, the office's own past forecasts, and the weights it used each day.
- **head-forecaster** — produces the office's forecast by combining the services,
  weighting each by how accurate it has been recently.

## What each worker does

- **repository.** Keeps the running history above and answers requests for the recent
  history. Incoming service forecasts and the daily actual high are filed here — each
  actual against the day it belongs to, so a forecast and its later outcome sit
  together.
- **head-forecaster.** Each day: takes the services' forecasts for tomorrow; asks the
  repository for the last couple of weeks of forecasts, actual highs, and weights;
  works out weights for the services so that the weighted combination would have been
  most accurate over that period; combines today's service forecasts using those
  weights into the office's forecast; and writes the forecast and the weights to the
  repository and to FORECAST.

## Rules

- Handle one day at a time. Because the services send forecasts at unpredictable times
  and everything is filed in the shared repository, finish one day's forecast and record
  it before starting the next, so the history stays consistent.
- The head-forecaster waits until it has the recent history from the repository before
  it forecasts.
