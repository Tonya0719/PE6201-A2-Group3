"""Problem A tool layer aligned to the D1/D2 team outline.

Agent-visible tools (5):
    get_claim, lookup_policy, check_coverage,
    get_preauthorisation, issue_decision_letter

Internal deterministic helpers (4):
    check_duplicate, check_hospital_panel,
    check_missing_documents, already_decided

Only agent-visible tools appear in TOOL_REGISTRY / tool descriptors. Helpers are
ordinary Python and never generate their own Action/Observation pair.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data_A"
OUTBOX: list[dict[str, Any]] = []


def _load(name: str):
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def _same_lines(a, b):
    def norm(lines):
        return sorted((str(x["code"]), float(x["amount"])) for x in lines)
    return norm(a) == norm(b)


# ---------- Internal helpers (NOT agent-visible) ----------

def check_duplicate(claim: dict) -> str | None:
    """Exact 4-field match: member + hospital + service date + full line set."""
    for old in _load("decided_claims.json"):
        if (
            old["member_id"] == claim["member_id"]
            and old["hospital_id"] == claim["hospital_id"]
            and old["date_of_service"] == claim["date_of_service"]
            and _same_lines(old["lines"], claim["lines"])
        ):
            return old["claim_id"]
    return None


def check_hospital_panel(hospital_id: str) -> bool:
    """Deferred record-only helper; panel status does not route ACT/ASK/ESCALATE."""
    row = next((x for x in _load("hospitals.json") if x["hospital_id"] == hospital_id), None)
    if row is None:
        raise ValueError(f"Unknown hospital_id: {hospital_id}")
    return bool(row["panel"])


def check_missing_documents(lines: list[dict], attached_documents: list[str]):
    """Deferred deterministic join: procedure -> required document -> attached docs."""
    reqs = _load("required_documents.json")
    attached = set(attached_documents)
    missing = []
    for line in lines:
        for req in reqs:
            if req["procedure_code"] == line["code"] and req["document"] not in attached:
                missing.append({"procedure_code": line["code"], "document": req["document"]})
    return missing


def already_decided(case_id: str) -> bool:
    """Tool-specific second-layer write dedupe used inside the gated action."""
    return any(x.get("case_id") == case_id for x in OUTBOX)


# Static dependency map derived from the supplied procedure fixture.
# This is prompt/runtime configuration, not an agent-visible helper/tool.
PREAUTH_REQUIRED_CODES = tuple(
    x["code"] for x in _load("procedures.json") if bool(x.get("requires_preauth"))
)


# ---------- Agent-visible tools ----------

def get_claim(claim_id: str):
    """Turn 1: raw claim + duplicate_of only. Hospital/doc checks are deferred."""
    claim = next((x for x in _load("claims.json") if x["claim_id"] == claim_id), None)
    if claim is None:
        raise ValueError(f"Unknown claim_id: {claim_id}")
    result = dict(claim)
    result["duplicate_of"] = check_duplicate(claim)
    return result


def lookup_policy(member_id: str):
    """Turn 2: authoritative policy gate + policy_id required by coverage."""
    member = next((x for x in _load("members.json") if x["member_id"] == member_id), None)
    if member is None:
        raise ValueError(f"Unknown member_id: {member_id}")
    policy = next((x for x in _load("policies.json") if x["policy_id"] == member["policy_id"]), None)
    if policy is None:
        raise ValueError(f"No policy for member_id: {member_id}")
    return {
        "policy_id": policy["policy_id"],
        "status": policy["status"],
        "start_date": policy["start_date"],
        "end_date": policy["end_date"],
        "annual_limit": policy["annual_limit"],
        "used_to_date": policy["used_to_date"],
        "remaining_annual_limit": policy["annual_limit"] - policy["used_to_date"],
        "exclusions": policy.get("exclusions", []),
    }


def check_coverage(policy_id: str, procedure_code: str):
    """Turn 3: one line's exclusion/coverage result + preauth requirement."""
    policy = next((x for x in _load("policies.json") if x["policy_id"] == policy_id), None)
    proc = next((x for x in _load("procedures.json") if x["code"] == procedure_code), None)
    if policy is None:
        raise ValueError(f"Unknown policy_id: {policy_id}")
    if proc is None:
        raise ValueError(f"Unknown procedure_code: {procedure_code}")
    exclusion = next((x for x in policy.get("exclusions", []) if x["code"] == procedure_code), None)
    return {
        "procedure_code": procedure_code,
        "coverage_status": "excluded" if exclusion else "covered",
        "exclusion_code": exclusion["rule"] if exclusion else None,
        "requires_preauth": bool(proc["requires_preauth"]),
    }


def get_preauthorisation(member_id: str, procedure_code: str):
    """Turn 3: return raw matching authorisation dates; model judges applicability."""
    rows = [
        x for x in _load("preauthorisations.json")
        if x["member_id"] == member_id and x["procedure_code"] == procedure_code
    ]
    return {
        "procedure_code": procedure_code,
        "records": [
            {
                "preauthorisation_id": x["preauth_id"],
                "valid_from": x["valid_from"],
                "valid_to": x["valid_to"],
            }
            for x in rows[:3]
        ],
    }


def issue_decision_letter(
    case_id: str,
    decision: str,
    trigger: str | None,
    reason: str,
    evidence: list,
    missing_item: str | None = None,
):
    """The one gated write. A2 only appends a local structured record."""
    allowed = {"approve_in_principle", "request_document", "escalate"}
    if decision not in allowed:
        raise ValueError(f"Invalid decision: {decision}")
    if decision == "request_document" and not missing_item:
        raise ValueError("request_document requires missing_item")
    if decision == "escalate" and not trigger:
        raise ValueError("escalate requires exactly one trigger")
    if already_decided(case_id):
        raise ValueError("Decision action already executed for this case")
    record = {
        "case_id": case_id,
        "decision": decision,
        "trigger": trigger,
        "missing_item": missing_item,
        "reason": reason,
        "evidence": evidence,
    }
    OUTBOX.append(record)
    return {"recorded": True, "case_id": case_id, "decision": decision}


def reset_outbox():
    OUTBOX.clear()


TOOL_REGISTRY = {
    "get_claim": get_claim,
    "lookup_policy": lookup_policy,
    "check_coverage": check_coverage,
    "get_preauthorisation": get_preauthorisation,
    "issue_decision_letter": issue_decision_letter,
}
IRREVERSIBLE_TOOLS = {"issue_decision_letter"}


def is_irreversible_tool(name: str):
    return name in IRREVERSIBLE_TOOLS


def _execute_one_tool(call: dict):
    name = call.get("name")
    args = call.get("arguments", {})
    if name not in TOOL_REGISTRY:
        return {"tool": name, "ok": False, "error": "UNKNOWN_TOOL"}
    try:
        return {"tool": name, "ok": True, "result": TOOL_REGISTRY[name](**args)}
    except Exception as e:
        return {"tool": name, "ok": False, "error": str(e)}


def execute_tool_calls(tool_calls: list[dict], parallel: bool = True):
    """One turn may execute multiple independent calls and return all observations together."""
    if not tool_calls:
        return []
    if len(tool_calls) == 1 or not parallel:
        return [_execute_one_tool(c) for c in tool_calls]
    if any(is_irreversible_tool(c.get("name", "")) for c in tool_calls):
        return [_execute_one_tool(c) for c in tool_calls]
    with ThreadPoolExecutor(max_workers=min(8, len(tool_calls))) as ex:
        return list(ex.map(_execute_one_tool, tool_calls))


# ---------- D2(b): same tool set, different ACI descriptions ----------

TOOL_SPECS_V1 = """
You can use these tools:

1. get_claim(claim_id)
Gets claim information, including member, hospital, service date, documents, narrative, lines and duplicate information.

2. lookup_policy(member_id)
Gets the member's policy information such as status, dates, limits, usage and exclusions.

3. check_coverage(policy_id, procedure_code)
Checks whether a procedure is covered and may return exclusions and preauthorisation information.

4. get_preauthorisation(member_id, procedure_code)
Gets matching preauthorisation information and validity dates.

5. issue_decision_letter(case_id, decision, trigger, reason, evidence, missing_item=None)
Records the final claim first-response decision. This is a gated write.
"""

TOOL_SPECS_V2 = """
Available tools — use only facts returned by these tools.

1. NAME + SIGNATURE
get_claim(claim_id: str)
WHAT: Retrieve exactly one queued claim and exact duplicate-history evidence.
INPUT: one valid claim ID.
RETURNS: {claim_id, member_id, hospital_id, date_of_service, narrative, documents, lines, duplicate_of}.
SIZE BOUND: one claim and at most one exact duplicate ID.
FAILS WHEN: claim_id does not exist.
IRREVERSIBLE? No.

2. NAME + SIGNATURE
lookup_policy(member_id: str)
WHAT: Retrieve the authoritative policy facts that gate claim processing and supply policy_id for line checks.
INPUT: member_id returned by get_claim.
RETURNS: {policy_id, status, start_date, end_date, annual_limit, used_to_date, remaining_annual_limit, exclusions}.
SIZE BOUND: one policy record.
FAILS WHEN: member_id or its linked policy does not exist.
IRREVERSIBLE? No.

3. NAME + SIGNATURE
check_coverage(policy_id: str, procedure_code: str)
WHAT: Resolve one claim line for exclusion/coverage and report whether the procedure requires preauthorisation.
INPUT: policy_id from lookup_policy; one procedure code from get_claim.
RETURNS: {procedure_code, coverage_status: "covered"|"excluded", exclusion_code|null, requires_preauth: bool}.
SIZE BOUND: one line result only.
FAILS WHEN: policy_id or procedure_code does not exist.
IRREVERSIBLE? No.

4. NAME + SIGNATURE
get_preauthorisation(member_id: str, procedure_code: str)
WHAT: Retrieve raw matching preauthorisation dates. You must compare them with the claim date_of_service yourself.
INPUT: member_id and a procedure code known from the static preauth-required list in the system prompt.
RETURNS: {procedure_code, records:[{preauthorisation_id, valid_from, valid_to}]}; records may be empty.
SIZE BOUND: at most 3 matching records.
FAILS WHEN: malformed IDs; an empty records list means no matching preauthorisation exists.
IRREVERSIBLE? No.

5. NAME + SIGNATURE
issue_decision_letter(case_id: str, decision: "approve_in_principle"|"request_document"|"escalate", trigger: str|null, reason: str, evidence: list, missing_item: str|null=None)
WHAT: Record the final first-response decision only after all facts required for that path are known.
INPUT: fixed decision vocabulary; exactly one trigger for ESCALATE; named missing_item for ASK; structured evidence.
RETURNS: {recorded:true, case_id, decision}.
SIZE BOUND: confirmation only.
FAILS WHEN: invalid decision, ASK lacks missing_item, ESCALATE lacks trigger, autonomy gate has not passed, or this case was already written.
IRREVERSIBLE? Yes — gated by system autonomy and write de-duplication. The model cannot set autonomy.
"""


def get_tool_specs(version: str = "v2"):
    return TOOL_SPECS_V1 if version == "v1" else TOOL_SPECS_V2
