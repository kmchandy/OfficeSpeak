# Start here — build an office (no programming needed)

Welcome. You're going to build a small **office**: a team of software helpers that
watches for information and reacts to it, on its own. You will **not** write code.
You describe what you want in plain English; the assistant builds it, shows it back
to you as a simple picture and a plain description, and you fix anything that's
wrong. You go back and forth until it does what you want.

## What is an office?

Think of a small team. Each person has **one clear job**. Information comes in the
door — a news feed, live prices, emails, sensor readings. The workers react to it,
hand things to one another, and results go out — written to a file, or shown on a
screen. The office runs on its own; you don't press "go" each time.

You already understand this — it's how a real workplace runs. That's all an office
is.

## How to describe your office

Just answer a few plain questions, in your own words:

1. **What is it for?** One or two sentences.
2. **What comes in?** Where does information arrive from, and how often?
3. **What goes out?** What should it produce, and where does it go?
4. **Who's on the team?** Name each worker and its one-line job — and, importantly,
   **what each one needs to know** to do the job, and **who it hands things to**.
5. **Any rules?** For example: handle one thing at a time? Does anyone wait for
   someone else? Should the team learn over time?

Don't worry about getting it perfect or complete. The whole point is that you'll
**see it and fix it**.

## What happens next

1. You describe it in plain words.
2. The assistant builds the office and **explains it back** to you — who does what,
   who hands what to whom — with a simple diagram, and a short list of "things I
   assumed" (the choices you didn't spell out).
3. You **confirm or correct** in plain English — for example, "no, the accountant
   has to see what we currently hold."
4. It updates and shows you again. Repeat until it's right.

That back-and-forth is the whole method. A first rough description is enough to get
started.

## A tiny example

> "I want a desk that watches the market and suggests buy or sell for a few stocks.
> Prices come in continuously; news comes in from X and from Bloomberg. A
> chart-watcher signals when a price breaks its recent average; a news-reader signals
> when a story looks market-moving. A head-trader decides what to suggest and checks
> a risk-manager (who keeps our positions and limits) before writing the suggestion
> to a file."

From that, the assistant builds the office, notices things you left open (e.g., "how
should the head-trader get the current price?"), and asks you — and you answer in
plain English.

## What you get, without having to think about it

Under the hood, your office runs on grown-up machinery you never have to see:

- it **stops cleanly** when there's nothing left to do,
- it **saves its state** now and then (checkpoints), so it can recover, and
- you can **look inside** when something seems off.

You don't manage any of that. It's just there.

## You can also ask the assistant to…

- **Explain what any worker did** — it shows you that worker's inputs and outputs in
  plain English ("your risk-manager approved all 23 proposals; your positions never
  hit the limit").
- **Test one worker** on its own.
- **Improve a worker's instructions** — "the news-reader is too jumpy on rumors" —
  and it tightens them.

## Ready?

Describe your office in your own words. A good way to start is simply:

> "I want an office that …"
