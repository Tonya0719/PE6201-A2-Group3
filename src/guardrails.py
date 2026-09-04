
"""D3 hard guardrails. These are code controls, not prompt advice."""
import json


def check_step_cap(turns_completed: int, step_cap: int):
    return (turns_completed < step_cap, None if turns_completed < step_cap else "STEP_CAP_REACHED")


def check_budget(cost_so_far: float, budget_usd: float):
    return (cost_so_far < budget_usd, None if cost_so_far < budget_usd else "BUDGET_CAP_REACHED")


def action_signature(call: dict):
    return json.dumps({"name": call.get("name"), "arguments": call.get("arguments", {})}, sort_keys=True)


def check_duplicate_actions(tool_calls: list[dict], seen_actions: set[str]):
    allowed, blocked = [], []
    for c in tool_calls:
        (blocked if action_signature(c) in seen_actions else allowed).append(c)
    return allowed, blocked


def check_autonomy(tool_call: dict, autonomy: str, approved: bool = False):
    if tool_call.get("name") != "issue_decision_letter":
        return True, None
    if autonomy == "act":
        return True, None
    if autonomy == "confirm" and approved:
        return True, None
    if autonomy == "suggest":
        return False, "AUTONOMY_SUGGEST_ONLY"
    return False, "HUMAN_CONFIRMATION_REQUIRED"

"""Deterministic code guardrails for the Agent.

Purpose
-------
Provide hard controls that remain effective regardless of model behaviour.

Expected inputs
---------------
Current run state such as turn number, cumulative cost/token use, action signature,
requested gated action, configured autonomy setting, and (for confirm mode) human approval.

Expected outputs
----------------
Allow / block / halt decisions plus a clear reason that can be logged in the trace.

Required controls
-----------------
- Step cap
- Budget ceiling
- Action de-duplication
- Autonomy gate: suggest / confirm / act

The gate belongs directly in front of the irreversible local write, not in front
of ordinary read-only retrieval.

A2 mapping: D3(a); tested by D3(b); one control may be removed for D7 Failure 1.
"""

