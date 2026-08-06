# Office: debate

Sources: problem_stream
Sinks: answers,
       gave_up

Agents:
V0 is an iter_counter.
V1 is a solution_proposer.
V2 is a solution_critic.
V3 is a judge.

Connections:
problem_stream's destination is V0.

V0's out is V1.
V1's out is V2.
V2's out is V3.
V3's approved is answers.
V3's true is gave_up.
V3's else is V0.
