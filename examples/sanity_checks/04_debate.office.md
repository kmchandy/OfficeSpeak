# Office: debate

Sources: starter
Sinks: jsonl_recorder_archive(path="approved.jsonl"),
       jsonl_recorder_discard(path="gave_up.jsonl")

Agents:
V0 is an iter_counter.
V1 is a solution_proposer.
V2 is a solution_critic.
V3 is a judge.

Connections:
starter's destination is V0.

V0's out is V1.
V1's out is V2.
V2's out is V3.
V3's approved is jsonl_recorder_archive.
V3's true is jsonl_recorder_discard.
V3's else is V0.
