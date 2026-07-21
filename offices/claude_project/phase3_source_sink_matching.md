# OfficeSpeak "Phase 3" — matching sources and sinks (task #34)

*Sibling to `phase3_approval.md`. That document is about approving
office-specific workers (transforms). This one is about the other half of
turning a Phase 1/2 conversation into a generator-ready `OfficeSpeakSpec`:
resolving every `source`/`sink` agent's plain-English description into
one of DisSysLab's actual registered names and arguments — the
`registered_as` / `registered_args` fields on `AgentSpec`
(`dissyslab/office/officespeak_spec.py`).*

*This is required before an external tester can run the full chain
unassisted. Today it's a step a Python-familiar person does by hand;
this doc is what they follow while doing it.*

## Why this is its own step, not automated

Phase 1 already decided *that* an agent is a source or sink and what its
one port carries (Pass A/B's message-shape rule). It never decided, and
was never supposed to decide, which literal registered implementation
that agent runs as — Pat says "the BBC news feed" or "send me a text,"
not `bbc_world(max_articles=20)` or a Slack webhook URL. Matching those
two vocabularies is a lookup problem today (a fixed catalogue,
`docs/SOURCES_AND_SINKS.md`), but it is not a *safe-to-guess* problem: a
wrong match either silently produces the wrong data (guessing
`hacker_news` for "tech news" when Pat meant `techcrunch`) or, worse,
compiles clean and fails at runtime for a reason invisible from
`office.md` alone (a credentialed sink with no credentials set). Both
failure modes are exactly what `from_officespeak.py`'s own
`GeneratorError` philosophy exists to avoid elsewhere in the pipeline —
"never a silent guess" — so this step holds itself to the same standard.

## The procedure

For every `AgentSpec` with `kind="source"` or `kind="sink"`:

1. **Reread Phase 2's own description of this agent** — not just its
   name. Phase 1 names the agent (`NEWSWIRE`, `ALERT_EMAIL`); Phase 2 (or
   Phase 1's own agent-kind notes) is where Pat's actual words about it
   live ("watches the BBC," "emails me when...").
2. **Find the entry in `docs/SOURCES_AND_SINKS.md`** whose description
   matches. The table below is a shortcut for the common cases; the doc
   itself is the source of truth and has the full argument list for each.
3. **Fill in `registered_args` from whatever specifics Pat gave** — a
   city, a ticker, a URL, a channel, a recipient, a poll interval. If Pat
   didn't give one, use the registered default (already documented per
   entry) rather than inventing a value.
4. **Check credentials, not just the name.** Several entries need
   something set up before they'll run at all (`gmail`/`gmail_sink` need
   an app password; `slack_sink` needs a webhook URL; `search`/`web`
   need an MCP server installed). A correct name match with a missing
   credential is still a blocker — note it as a setup step for whoever
   runs the office, don't treat the match as done until it's flagged.
5. **If nothing fits, do not force a match** — see "When nothing fits"
   below.
6. **Record the result** in a form that plugs directly into `AgentSpec`:
   `registered_as="<name>"`, `registered_args={...}`. That's literally
   the two fields the generator reads.

## Quick lookup: common Pat phrasings → registered name

This is a shortcut, not a replacement for reading `docs/SOURCES_AND_SINKS.md` —
several entries below have arguments and setup notes that matter and
aren't repeated here.

| Pat says something like...                          | registered name                              |
|-------------------------------------------------------|-----------------------------------------------|
| "the BBC" / "world news" / "tech news" / "Al Jazeera" / "NPR" / "Hacker News" / "TechCrunch" / "NASA news" | one of the 10 named RSS feeds — pick the specific one named, e.g. `bbc_world`, `al_jazeera`, `npr_news`, `hacker_news`, `techcrunch`, `nasa_news` |
| "the weather" / "today's forecast for \<city\>"      | `weather(city="...")`                        |
| "a stock's price" / "\<ticker\>'s price"             | `stocks(ticker="...")`                       |
| "posts on BlueSky about..."                          | `bluesky(filter_keywords=[...])`             |
| "my email" / "my inbox"                              | `gmail` — needs a Gmail app password         |
| "my calendar"                                        | `calendar` — needs a public `.ics` URL       |
| "a web page that changes" / "check this URL"         | `web(url="...")`                             |
| "search the web for..."                              | `search(query="...")` — needs an MCP server  |
| "when \<some other system\> notifies us" / "an inbound webhook" | `webhook` — push-style, needs a public tunnel for real third parties |
| something typed in at the start / "you tell it..."   | `console_input`                              |
| "print it" / "show it on screen" / "the console"     | `console_printer`                            |
| "a colorful/live dashboard"                           | `intelligence_display`                       |
| "save it" / "log it" / "an archive" / "a file"       | `jsonl_recorder(path="...")`                 |
| "email me" / "send an alert to my inbox"             | `gmail_sink(to="...")` — same credential as `gmail` |
| "post to Slack" / "a Slack channel"                  | `slack_sink` — needs an Incoming Webhook URL |
| "send it to \<some other system\>" / a generic outbound webhook | `webhook_sink(url="...")`         |
| "drop it" / "ignore it" / "don't keep it"            | `discard`                                     |

## When nothing fits

Not everything Pat might ask for has a registered match today — the most
common real gap is **texting/SMS** (no `sms_sink` ships yet) and anything
requiring an MCP server that isn't already set up (`search`, `web`,
`mcp_source`/`mcp_sink` all need one installed first). When nothing in
`docs/SOURCES_AND_SINKS.md` genuinely fits:

1. **Check the general-purpose escape valves first** — `webhook`/
   `webhook_sink` (arbitrary inbound/outbound HTTP) and `mcp_source`/
   `mcp_sink` (any MCP server tool) cover a lot of ground a named entry
   doesn't. A "text me" request, for instance, is realistically a
   `webhook_sink` pointed at a third-party SMS gateway (e.g. a Twilio
   webhook URL), not a built-in DisSysLab primitive — worth naming this
   explicitly to whoever's approving, since it shifts a setup cost onto
   them (an account with that gateway), not just a config line.
2. **If even that doesn't cover it, stop and flag it** — same discipline
   as every other "never guess" rule in this pipeline. Tell Pat (or the
   tester) plainly: "there's no registered way to do this yet; here's
   the closest thing, or here's what building a new one would take." Do
   **not** generate an office with a guessed or silently-approximated
   source/sink.
3. **Writing a genuinely new source or sink is out of scope for this
   step.** It's real work — a Python class with a `run()` method,
   registered in `dissyslab/office/utils.py`'s `SOURCE_REGISTRY`/
   `SINK_REGISTRY` (see `docs/SOURCES_AND_SINKS.md`'s own "Adding more"
   section) — but it's a one-time framework addition a developer does
   once, not a per-office judgment call, so it belongs to a different
   step than this matching pass.

## Worked example

Case 07's news-subscription office (`cold_tests/transcripts/
case_07_news_subscriptions.md`) named its sources as "the BBC," "Al
Jazeera," and "NPR," and (in a variant of the case) "notify a friend by
text." The first three are exact catalogue hits: `bbc_world`,
`al_jazeera`, `npr_news`. "Notify a friend by text" is exactly the "when
nothing fits" case above — there is no SMS sink; the honest answer is
either `webhook_sink` against a real SMS gateway Pat would need to set
up, or telling Pat this isn't supported yet and asking whether email
(`gmail_sink`) is an acceptable substitute. Flagging that choice back to
Pat, rather than silently picking one, is the point of this whole step.

## Feeding the generator

Once matched, this is all `from_officespeak.py` needs — literally the
`registered_as`/`registered_args` on each source/sink `AgentSpec`. It
does no matching of its own (by design; see its module docstring), so a
skipped or wrong match here is not something `dsl build` will always
catch — a credentialed sink with a plausible-looking but wrong name
compiles fine and only fails (or silently misbehaves) at run time. This
step is the only check standing between a Phase 2 description and that
failure mode; treat it as required, not optional, before generating.
