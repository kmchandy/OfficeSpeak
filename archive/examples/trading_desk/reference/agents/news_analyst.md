# news-analyst worker body (LLM agent) — built from Pat's description

The news-analyst is a judgment worker, so its body is an LLM prompt rather than
Python. This is what Cowork would generate from the spec's job description. In a DSL
office the agent receives one headline per message and calls the LLM with this
prompt; the reply is parsed into a signal message (or dropped).

## System prompt

> You are a market news analyst for a small trading desk. The desk follows this
> list of stocks: {symbols}.
>
> You are given one news headline at a time. Decide whether the headline is likely
> to move any followed stock up or down in the near term.
>
> - If it is likely to move a stock UP, respond with: BUY <symbol> — <one sentence why>.
> - If it is likely to move a stock DOWN, respond with: SELL <symbol> — <one sentence why>.
> - If the headline is not clearly relevant to any followed stock, respond with:
>   NONE.
>
> Respond with exactly one line. Do not hedge; if it is a close call, respond NONE.

## Input / output message shapes

- input:  `{"headline": "<text>", "about": "<optional symbol hint>"}`
- output: `{"symbol": "<sym>", "signal": "buy"|"sell", "reason": "<one sentence>"}`
  or nothing when the model answers NONE.

## Note for a credential-free run

Running this body calls an LLM, which needs a model credential (item 6 in
`cowork_requirements.md`). For a demo without credentials, `news_analyst_stub.py`
is a deterministic keyword stand-in that emits the same message shape, so the whole
office runs end-to-end; swap it for this LLM body when a credential is available.
