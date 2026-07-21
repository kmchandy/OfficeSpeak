# Full-chain case 02 — returns desk (select, "ask-and-wait, frozen")

Second full-chain case (see case 01, shipment release, for the protocol). This
one targets `select` rather than a keyed keeper — the "freeze while waiting for
a reply" pattern `trading_room`'s Case 2 already teaches, tested here in a new
domain to see whether a cold Phase 1/2 conversation reaches for it correctly on
its own, and whether the rest of the chain (approval, generation, run) handles
a coordinator with a `command` port correctly.

## Pat's description (given verbatim)

> "I run a small returns desk. Tickets come in asking for refunds. For every
> ticket, check if the refund is under $50 — if so, approve it immediately. If
> it's $50 or more, ask a manager to approve it, and don't look at any other
> ticket while waiting for that answer. Once the manager replies, resume with
> the next ticket and send the outcome to the customer log."

## Cold Phase 1/2 result — correct on the first try

A fresh cold instance (only `start_instructions.md` + the four
`start_gallery/*.md` files) produced exactly the right shape without a
correction round: `SELECT` (coordinator, `select`, inboxes `ticket` /
`manager_reply` / `command`), `CLERK` (a transform that auto-approves under
$50, or escalates to `MANAGER` and commands `SELECT` to bring the manager's
reply next — "nothing else reaches CLERK until that answer comes"), `MANAGER`,
`LOG`. Its own explain-back named this "the frozen ask-and-wait pattern" and
was consistent with what it built — no gap between stated intent and
structural choice this time, unlike case 01's `merge_synch` miss. It correctly
declined a gate or record ("no shared ledger here... CLERK's own memory of
'who I'm waiting on' is enough").

## Transcription, approval, and a real bug caught by testing (not cold)

Transcribed into an `OfficeSpeakSpec` — `STARTER`→`TICKETS` (a fixed sequence
of four tickets: $20, $120, $35, $80) → `SELECT` → `CLERK` → `MANAGER` /
`LOG` — and generated with `from_officespeak.py`, no errors.

First run stalled after ticket 1: only T1's outcome was ever written, then the
office quiesced (correctly detected as genuine deadlock, not a termination-
detector bug — checked directly against `os_agent.py`'s logic, which is
sound). Cause: `select_role`'s actual contract is stricter than my first draft
assumed — after forwarding *any* data message, it unconditionally waits on
`command` next, regardless of what that message was. My `CLERK` factory sent a
command only on the escalation branch (matching the docstring's own wording,
correctly, on reflection: "forwards it... and select then waits for the next
command" — a command is required after *every* message, not just an
escalation). The auto-approve branch sent none, so `SELECT` waited forever on
a `command` that was never coming — real deadlock, correctly reported as such.

This is exactly the class of bug `phase3_approval.md`'s fidelity check exists
to catch — running a worker on example inputs and checking the outputs, before
trusting it in a live office. Fixed by having the auto-approve branch also
send `{"next": "ticket"}`; re-ran clean.

## Run (after the fix)

```
[Clerk] ticket T1 ($20) -- approved on the spot
[Clerk] ticket T2 ($120) -- escalating to manager, freezing
[Manager] reviewing ticket T2 ($120) -- approving
[Clerk] manager decided ticket T2: approved=True
[Clerk] ticket T3 ($35) -- approved on the spot
[Clerk] ticket T4 ($80) -- escalating to manager, freezing
[Manager] reviewing ticket T4 ($80) -- approving
[Clerk] manager decided ticket T4: approved=True
```

`outcomes.jsonl`, in order: T1 (clerk, approved), T2 (manager, approved), T3
(clerk, approved), T4 (manager, approved) — strictly in ticket order, T3 only
processed *after* T2's manager reply came back, confirming the freeze actually
held (T3 could have arrived and been read out of order if `SELECT` had not
genuinely withheld it while waiting on `command`/`manager_reply`).

## Verdict

PASS. Phase 1/2 needed no correction this time — a genuine, useful data point
alongside case 01's miss: the process doesn't manufacture problems where there
aren't any. The real finding here is downstream: `select`'s "always read
`command` next, no exceptions" contract is easy to get wrong when hand-writing
a worker against it, and a mistake there produces a silent deadlock, not a
compile error — reinforcing that the approval step's "run it and check the
output" discipline is required, not a formality. New gallery fixture:
`dissyslab/gallery/apps/returns_desk/` (`office.md` + `roles/tickets.py`,
`roles/clerk.py`, `roles/manager.py`, run artifact `outcomes.jsonl`).
