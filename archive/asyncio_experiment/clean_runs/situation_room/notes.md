# notes — clean run on situation_room

Fill these in after pasting Claude's response.

## Metadata

- Claude model used:
- Date / time of session:
- Surface (claude.ai web, API, etc.):

## Observations on Claude's response

- Did Claude use asyncio (concurrent) or sync (serial)?
- Was each agent a function, a class, or something else?
- Where did the routing decision live (per-article function, output stage, inline in main, somewhere else)?
- Where were sources declared?
- Did Claude factor a per-item function (like `process_one` or
  `enrich_article`) or keep everything in main?
- Did Claude use any of the NoT-specific words we have been using
  with the contaminated session (enrich, role, office, agent)?
- Was the code runnable as-is (modulo the API key)?

## Comparison with the contaminated Run 1

(Compare `response_run1.py` saved here against
`experiments/run1/situation_room_natural.py`.)

- Structural differences:
- Vocabulary differences:
- Surprises:

## Implications for the AST walker

- Patterns we can rely on across both:
- Patterns specific to one or the other:
