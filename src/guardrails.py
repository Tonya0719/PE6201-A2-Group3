"""Deterministic code guardrails for PE6201 A2 Problem A."""
from __future__ import annotations

import json


READ_TOOLS_AFTER_INTAKE = {"lookup_policy", "check_coverage", "get_preauthorisation"}


def check_step_cap(turns_completed: int, step_cap: int):
    ok = turns_completed < step_cap
    return ok, None if ok else "STEP_CAP_REACHED"


def check_budget(cost_so_far: float, budget_usd: float):
    """Allow work only while cumulative spend has not reached the ceiling."""
    ok = cost_so_far < budget_usd
    return ok, None if ok else "BUDGET_CAP_REACHED"


def action_signature(call: dict):
    return json.dumps({"name": call.get("name"), "arguments": call.get("arguments", {})}, sort_keys=True)


def check_duplicate_actions(tool_calls: list[dict], seen_actions: set[str]):
    allowed, blocked = [], []
    for call in tool_calls:
        (blocked if action_signature(call) in seen_actions else allowed).append(call)
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



def check_evidence_complete(tool_call: dict, history: list[dict]):
    """Block the irreversible decision write if the agent gathered no claim evidence.

    This is a readiness check, distinct from the autonomy permission gate.
    Requiring get_claim (and only get_claim) preserves legitimate early exits such
    as exact duplicates and hostile member instructions, which should not be forced
    through policy/coverage retrieval.
    """
    if tool_call.get("name") != "issue_decision_letter":
        return True, None
    saw_claim = any(
        obs.get("tool") == "get_claim" and obs.get("ok")
        for step in history
        for obs in step.get("observations", [])
    )
    return (True, None) if saw_claim else (False, "PREMATURE_GATED_ACTION_BLOCKED")

def check_case_id_match(tool_call: dict, active_claim_id: str):
    """Poka-yoke: a gated write may only target the claim currently being processed."""
    if tool_call.get("name") != "issue_decision_letter":
        return True, None
    requested = (tool_call.get("arguments") or {}).get("case_id")
    ok = requested == active_claim_id
    return ok, None if ok else "CASE_ID_MISMATCH"


def _hostile_narrative(narrative: str) -> bool:
    text = (narrative or "").lower()
    return (
        "system note:" in text
        or "system audit override" in text
        or ("returned:" in text and "[" in text)
        or "ignore prior instructions" in text
        or "ignore previous instructions" in text
    )


def decisive_intake_reason(claim: dict | None):
    if not claim:
        return None
    if claim.get("duplicate_of"):
        return "duplicate_claim"
    if _hostile_narrative(claim.get("narrative", "")):
        return "instruction_in_member_narrative"
    return None


def check_no_retrieval_after_decisive_intake(tool_calls: list[dict], claim: dict | None):
    """Hard-stop read tools after duplicate / hostile intake evidence is already decisive.

    This converts a prompt-only instruction into a runtime control. The model may recover
    on the next turn by selecting the gated decision action.
    """
    reason = decisive_intake_reason(claim)
    if reason is None:
        return tool_calls, [], None
    allowed, blocked = [], []
    for call in tool_calls:
        (blocked if call.get("name") in READ_TOOLS_AFTER_INTAKE else allowed).append(call)
    return allowed, blocked, reason
