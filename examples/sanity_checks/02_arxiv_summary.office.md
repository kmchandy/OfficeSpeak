# Office: arxiv_summary

Sources: arxiv_cs_ai(max_articles=5),
         arxiv_cs_cl(max_articles=5)
Sinks: jsonl_recorder(path="papers.jsonl")

Agents:
V0 is a paper_summarizer.

Connections:
arxiv_cs_ai's destination is V0.
arxiv_cs_cl's destination is V0.

V0's out is jsonl_recorder.
