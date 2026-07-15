# Debugging walkthrough — finding a bug by testing one worker

A worked example of how OfficeSpeak helps Pat debug a **computational** worker (a
worker whose job is a piece of Python, not an LLM). It shows the whole move: Pat
sees a wrong result, OfficeSpeak tests each worker by itself, the bug is localized
to one worker, and OfficeSpeak explains it in plain English and fixes it.

The office is `office.py` in this folder; the isolated tests are
`per_agent_tests.py`. Everything is ordinary Python and the office is
determinate, so every run is exactly reproducible.

## The office

**temp_watch** watches a stream of hourly temperatures and should raise an alert
only on a *spike* — a reading that jumps well above the recent normal.

    readings ──▶ Baseline ──▶ Alerter ──▶ ALERTS

- **Baseline** keeps a rolling average of the last five readings (it has memory).
- **Alerter** should alert when a reading is more than 5° above that baseline.
- **ALERTS** records the alerts.

## 1. Pat sees something wrong

Pat runs the office on a quiet day with one real spike (to 31°) and gets:

```
=== temp_watch (BUGGY) ===
readings: [20, 21, 20, 22, 19, 20, 31, 20, 21, 20]
alerts raised: 10
  reading= 20  baseline= 20.0  -> ALERT
  reading= 21  baseline= 20.5  -> ALERT
  ...
  reading= 31  baseline= 22.4  -> ALERT
  ...
```

Pat's complaint, in her own words: **"It's alerting on almost everything — it
should only flag the one real spike."**

## 2. OfficeSpeak tests each worker by itself

There are two workers that compute something — Baseline and Alerter — so
OfficeSpeak checks each one on its own, on inputs it chooses. This takes the whole
office and its timing out of the picture: each worker is judged only on what it
does with a given input.

**Baseline** — fed the readings one at a time:

```
  reading= 20  ->  baseline=20.0
  reading= 21  ->  baseline=20.5
  reading= 22  ->  baseline=20.8
  reading= 31  ->  baseline=22.4
```

This is right — the baseline tracks the recent temperatures, and the single spike
to 31 barely moves it (it's one of five). Baseline is not the problem.

**Alerter** — fed hand-picked cases where the raw reading is high but the *rise*
above the baseline is small or large (these are the cases that tell a correct
spike-detector apart from a broken one):

```
  reading= 22 baseline= 20 (rise= 2)  ->  ALERT     expected: no alert   <-- WRONG
  reading= 24 baseline= 20 (rise= 4)  ->  ALERT     expected: no alert   <-- WRONG
  reading= 31 baseline= 20 (rise=11)  ->  ALERT     expected: ALERT
  reading= 20 baseline= 20 (rise= 0)  ->  ALERT     expected: no alert   <-- WRONG
```

## 3. OfficeSpeak explains it, in Pat's terms

> Alerter is firing whenever the temperature is above 5°, instead of when it has
> *risen* more than 5° above the baseline. It's looking at the raw temperature, not
> at how far the temperature jumped. Since a normal reading (around 20°) is already
> well above 5°, it alerts nearly every hour. Baseline is fine — the mistake is only
> in Alerter, and only in what it compares.

The fix is one line — compare the *rise* (`reading − baseline`) to the threshold
instead of the raw reading. With that change the office does what Pat wanted:

```
=== temp_watch (FIXED) ===
readings: [20, 21, 20, 22, 19, 20, 31, 20, 21, 20]
alerts raised: 1
  reading= 31  baseline= 22.4  -> ALERT
```

## Why this works, and where it stops

Testing a worker by itself catches **body** bugs — a worker computing the wrong
thing — which are the most common kind and, because the worker is ordinary Python,
are deterministic: the same input always gives the same output, so a test is
trustworthy and repeatable. It localizes the problem to one worker (here, Alerter
not Baseline), and OfficeSpeak chooses the *discriminating* inputs — the ones that
separate a correct worker from a broken one — which Pat might not think to try.

It does **not** judge the *wiring* (whether a worker is even given the right
inputs — that's the channel-counts aid), and it does **not** apply to **LLM
workers**.

## LLM workers: prompt-only, no evaluation

For a worker whose job is done by a language model, OfficeSpeak does **not** try to
test, evaluate, or debug its judgment — that judgment isn't a fixed function and
can't be checked the way a Python body can. Instead OfficeSpeak simply **shows Pat
the worker's prompt** and asks *"Is this what you mean?"*, and can show a few
example inputs and the outputs the model gave — for Pat to read, not for the system
to grade. Getting the prompt right is Pat's call; correctness of an LLM worker is a
question of whether the prompt says what Pat intends, not something OfficeSpeak
scores.

## Run it yourself

```bash
python office.py               # the buggy office: 10 alerts
DEBUG_FIX=1 python office.py    # the fixed office: 1 alert
python per_agent_tests.py       # the isolated worker tests
```
