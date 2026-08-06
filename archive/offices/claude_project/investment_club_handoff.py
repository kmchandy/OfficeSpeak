OFFICE_NAME = "investment_club_manual"

# Reference hand-off file for TESTER_MANUAL.md's running example.
#
# This is what Track A hands Al at the end of a conversation like the one
# TESTER_MANUAL.md walks through: every agent, port, and connection already
# fixed, with each source/sink matched (`registered_as`) and each
# office-specific worker's real code approved (`body_fn`, `approved=True`).
# TESTER_MANUAL.md's Track B section only shows the ACCOUNTANT snippet
# inline -- this file is the whole thing, for anyone who wants to run it
# themselves or see how every worker fits together.
#
# Reproduces OfficeSpeak's own worked example
# (offices/claude_project/start_gallery/investment_club.md), Case 2 --
# the "famous correction" where the accountant must read current holdings
# before pricing a trade, not just the proposed move. Matches the
# already-validated DisSysLab fixture at
# dissyslab/gallery/apps/investment_club/ in behavior (Feed/Gate/Val/Oppo/
# Join/Manager/Accountant/Ledger); this file is written in the newer
# hand-off-draft shape (`AGENTS`/`CONNECTIONS` dicts, zero-arg factories)
# that `python -m dissyslab.office.assemble` consumes directly.
#
# Verified end-to-end (2026-07-20): assembled with
#   python -m dissyslab.office.assemble investment_club_handoff.py <target_dir>
# then `dsl build <target_dir>` and `dsl run <target_dir>`, producing the
# exact three-period output quoted in TESTER_MANUAL.md's Track B, step 3.


def _make_feed_fn():
    _NUM_PERIODS = 3

    def feed_fn(msg):
        return [({"period": p}, "out") for p in range(1, _NUM_PERIODS + 1)]
    return feed_fn


def _make_val_fn():
    def val_fn(msg):
        period = msg["period"]
        return [({"period": period, "val_shares": period * 5}, "out")]
    return val_fn


def _make_oppo_fn():
    def oppo_fn(msg):
        period = msg["period"]
        return [({"period": period, "oppo_shares": period * 3}, "out")]
    return oppo_fn


def _make_manager_fn():
    _PRICE_PER_SHARE = 100.0
    pending = {}

    def manager_fn(msg):
        if "val_shares" in msg:
            period = msg["period"]
            proposed = msg["val_shares"] + msg["oppo_shares"]
            pending["period"] = period
            pending["proposed_shares"] = proposed
            return [({"period": period, "proposed_shares": proposed}, "to_accountant")]

        period = pending["period"]
        proposed = pending["proposed_shares"]
        cost = proposed * _PRICE_PER_SHARE
        new_shares = msg["current_shares"] + proposed
        new_cash = msg["current_cash"] - cost - msg["fee"]
        return [
            ({"action": "write", "data": {"aapl_shares": new_shares, "cash": new_cash}}, "to_ledger"),
            ({"period": period, "bought": proposed, "fee": msg["fee"],
              "resulting_shares": new_shares, "resulting_cash": new_cash}, "out"),
            ({}, "done"),
        ]
    return manager_fn


def _make_accountant_fn():
    _PRICE_PER_SHARE = 100.0
    pending = {}

    def accountant_fn(msg):
        if "proposed_shares" in msg:
            pending["period"] = msg["period"]
            pending["proposed_shares"] = msg["proposed_shares"]
            return [({"action": "read"}, "to_ledger")]

        current_shares = msg["aapl_shares"]
        current_cash = msg["cash"]
        proposed = pending["proposed_shares"]
        fee = 1.0 * proposed + 0.001 * current_shares * _PRICE_PER_SHARE
        return [({"fee": fee, "current_shares": current_shares, "current_cash": current_cash}, "to_manager")]
    return accountant_fn


AGENTS = [
    dict(name="STARTER", kind="source", in_ports=[], out_ports=["out"],
         registered_as="starter", registered_args={}),

    dict(name="FEED", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Once per period, a batch signaling the start of that period (market data, forecasts, news, prior decisions, standing in as just a period number here).",
         body_kind="python", body_fn=_make_feed_fn, body_prompt=None, approved=True),

    dict(name="GATE", kind="coordinator", in_ports=["data", "control"], out_ports=["out"],
         registered_as="gate", registered_args={}),

    dict(name="VAL", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Read the period's batch; produce a value-investing recommendation (which funds to buy/sell/hold, and why).",
         body_kind="python", body_fn=_make_val_fn, body_prompt=None, approved=True),

    dict(name="OPPO", kind="transform", in_ports=["in"], out_ports=["out"],
         description="Read the period's batch; produce an emerging-opportunities recommendation.",
         body_kind="python", body_fn=_make_oppo_fn, body_prompt=None, approved=True),

    dict(name="JOIN", kind="coordinator", in_ports=["val", "oppo"], out_ports=["out"],
         registered_as="merge_synch", registered_args={}),

    dict(name="MANAGER", kind="transform", in_ports=["in"], out_ports=["to_accountant", "to_ledger", "out", "done"],
         description="Read both recommendations for the period; propose a plan; ask the accountant what it would cost in taxes and fees and wait for the answer; finalize the plan; write the final plan and updated holdings to the ledger; send the plan to RECOMMEND; tell the gate the period is done.",
         body_kind="python", body_fn=_make_manager_fn, body_prompt=None, approved=True),

    dict(name="ACCOUNTANT", kind="transform", in_ports=["in"], out_ports=["to_ledger", "to_manager"],
         description="Read a proposed plan; ask the ledger for the current holdings and wait for them (Pat's correction: taxes depend on what the club currently holds, not just the proposed move); work out the taxes and fees using the cost basis in those holdings; reply to the manager.",
         body_kind="python", body_fn=_make_accountant_fn, body_prompt=None, approved=True),

    dict(name="LEDGER", kind="coordinator", in_ports=["in_"], out_ports=["out"],
         registered_as="record", registered_args={"initial": {"aapl_shares": 0, "cash": 10000.0}}),

    dict(name="RECOMMEND", kind="sink", in_ports=["in"], out_ports=[],
         description="The file where each period's final plan is written.",
         registered_as="jsonl_recorder", registered_args={"path": "recommendations.jsonl"}),
]

CONNECTIONS = [
    ("STARTER", "out", "FEED", "in"),
    ("FEED", "out", "GATE", "data"),
    ("GATE", "out", "VAL", "in"),
    ("GATE", "out", "OPPO", "in"),
    ("VAL", "out", "JOIN", "val"),
    ("OPPO", "out", "JOIN", "oppo"),
    ("JOIN", "out", "MANAGER", "in"),
    ("MANAGER", "to_accountant", "ACCOUNTANT", "in"),
    ("ACCOUNTANT", "to_manager", "MANAGER", "in"),
    ("MANAGER", "to_ledger", "LEDGER", "in_"),
    ("ACCOUNTANT", "to_ledger", "LEDGER", "in_"),
    ("LEDGER", "out", "ACCOUNTANT", "in"),
    ("MANAGER", "out", "RECOMMEND", "in"),
    ("MANAGER", "done", "GATE", "control"),
]
