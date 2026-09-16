"""Problem A tool layer.

Agent-visible tools (5):
    get_claim
    lookup_policy
    check_coverage
    get_preauthorisation
    issue_decision_letter

Deterministic runtime helpers (4):
    check_duplicate
    check_hospital_panel
    check_missing_documents
    already_decided

Design principles
-----------------
1. Tools expose authoritative facts, not final ACT / ASK / ESCALATE answers.
2. Deterministic arithmetic and validation belong in code.
3. Only issue_decision_letter is irreversible.
4. D2(b) changes ONLY the get_preauthorisation interface between v1 and v2.
5. No production/runtime code reads evaluation ground truth.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data_A"

OUTBOX: list[dict[str, Any]] = []


# =====================================================================
# Data helpers
# =====================================================================

def _load(name: str):
    with open(DATA_DIR / name, "r", encoding="utf-8") as f:
        return json.load(f)


def _same_lines(a, b):
    def norm(lines):
        return sorted(
            (str(x["code"]), float(x["amount"]))
            for x in lines
        )

    return norm(a) == norm(b)


# =====================================================================
# Deterministic helpers — NOT agent-visible
# =====================================================================

def check_duplicate(claim: dict) -> str | None:
    """Exact duplicate = member + hospital + service date + full line set."""
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
    """Record-only helper. Panel status does not route ACT/ASK/ESCALATE."""
    row = next(
        (
            x for x in _load("hospitals.json")
            if x["hospital_id"] == hospital_id
        ),
        None,
    )

    if row is None:
        raise ValueError(f"Unknown hospital_id: {hospital_id}")

    return bool(row["panel"])


def check_missing_documents(
    lines: list[dict],
    attached_documents: list[str],
):
    """Return required documents absent from this claim."""
    requirements = _load("required_documents.json")
    attached = set(attached_documents)

    missing = []

    for line in lines:
        for requirement in requirements:
            if (
                requirement["procedure_code"] == line["code"]
                and requirement["document"] not in attached
            ):
                missing.append(
                    {
                        "procedure_code": line["code"],
                        "document": requirement["document"],
                    }
                )

    return missing


def already_decided(case_id: str) -> bool:
    """Second-layer write dedupe for the gated action."""
    return any(
        row.get("case_id") == case_id
        for row in OUTBOX
    )


def format_missing_preauth(
    procedure_code: str,
    date_of_service: str,
) -> str:
    """Canonical ASK wording; formatting only, not routing."""
    return (
        f"current pre-authorisation for line "
        f"{procedure_code}, valid on {date_of_service}"
    )


def format_missing_document(
    document: str,
    procedure_code: str,
) -> str:
    """Canonical document ASK wording; formatting only, not routing."""
    return f"{document} for line {procedure_code}"


# =====================================================================
# Agent-visible tools
# =====================================================================

def get_claim(claim_id: str):
    """Get one queued claim plus deterministic intake facts."""
    claim = next(
        (
            x for x in _load("claims.json")
            if x["claim_id"] == claim_id
        ),
        None,
    )

    if claim is None:
        raise ValueError(f"Unknown claim_id: {claim_id}")

    result = dict(claim)

    # Poka-yoke 1:
    # duplicate matching is deterministic and remains outside model reasoning.
    result["duplicate_of"] = check_duplicate(claim)

    # Deterministic arithmetic only.
    # This does NOT tell the Agent whether the annual limit is exceeded.
    result["claim_total"] = sum(
        float(line["amount"])
        for line in claim["lines"]
    )

    return result


def lookup_policy(member_id: str):
    """Get policy gates and the policy_id required for line checks."""
    member = next(
        (
            x for x in _load("members.json")
            if x["member_id"] == member_id
        ),
        None,
    )

    if member is None:
        raise ValueError(f"Unknown member_id: {member_id}")

    policy = next(
        (
            x for x in _load("policies.json")
            if x["policy_id"] == member["policy_id"]
        ),
        None,
    )

    if policy is None:
        raise ValueError(
            f"No policy for member_id: {member_id}"
        )

    return {
        "policy_id": policy["policy_id"],
        "status": policy["status"],
        "start_date": policy["start_date"],
        "end_date": policy["end_date"],
        "annual_limit": policy["annual_limit"],
        "used_to_date": policy["used_to_date"],

        # Deterministic arithmetic only.
        "remaining_annual_limit":
            policy["annual_limit"] - policy["used_to_date"],

        "exclusions": policy.get("exclusions", []),
    }


def check_coverage(
    policy_id: str,
    procedure_code: str,
):
    """Resolve one line's coverage and preauthorisation requirement."""
    policy = next(
        (
            x for x in _load("policies.json")
            if x["policy_id"] == policy_id
        ),
        None,
    )

    procedure = next(
        (
            x for x in _load("procedures.json")
            if x["code"] == procedure_code
        ),
        None,
    )

    if policy is None:
        raise ValueError(
            f"Unknown policy_id: {policy_id}"
        )

    if procedure is None:
        raise ValueError(
            f"Unknown procedure_code: {procedure_code}"
        )

    exclusion = next(
        (
            x for x in policy.get("exclusions", [])
            if x["code"] == procedure_code
        ),
        None,
    )

    return {
        "procedure_code": procedure_code,
        "coverage_status":
            "excluded" if exclusion else "covered",
        "exclusion_code":
            exclusion["rule"] if exclusion else None,
        "requires_preauth":
            bool(procedure["requires_preauth"]),
    }


def get_preauthorisation(
    member_id: str,
    procedure_code: str,
    date_of_service: str | None = None,
):
    """Perform the common underlying PA lookup.

    The lookup itself is identical for D2(b) v1 and v2.
    Version-specific shaping happens in _execute_one_tool().
    """
    rows = [
        x
        for x in _load("preauthorisations.json")
        if (
            x["member_id"] == member_id
            and x["procedure_code"] == procedure_code
        )
    ]

    return {
        "member_id": member_id,
        "procedure_code": procedure_code,
        "date_of_service": date_of_service,
        "records": [
            {
                "preauthorisation_id": row["preauth_id"],
                "valid_from": row["valid_from"],
                "valid_to": row["valid_to"],
            }
            for row in rows[:3]
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
    """The one irreversible, runtime-gated local write."""
    allowed = {
        "approve_in_principle",
        "request_document",
        "escalate",
    }

    if decision not in allowed:
        raise ValueError(
            f"Invalid decision: {decision}"
        )

    if decision == "request_document":
        if not missing_item:
            raise ValueError(
                "request_document requires missing_item"
            )
        if trigger is not None:
            raise ValueError(
                "request_document requires trigger=null"
            )

    if decision == "escalate":
        if not trigger:
            raise ValueError(
                "escalate requires exactly one trigger"
            )
        if missing_item is not None:
            raise ValueError(
                "escalate requires missing_item=null"
            )

    if decision == "approve_in_principle":
        if trigger is not None:
            raise ValueError(
                "approve_in_principle requires trigger=null"
            )
        if missing_item is not None:
            raise ValueError(
                "approve_in_principle requires missing_item=null"
            )

    if already_decided(case_id):
        raise ValueError(
            "Decision action already executed for this case"
        )

    record = {
        "case_id": case_id,
        "decision": decision,
        "trigger": trigger,
        "missing_item": missing_item,
        "reason": reason,
        "evidence": evidence,
    }

    OUTBOX.append(record)

    return {
        "recorded": True,
        "case_id": case_id,
        "decision": decision,
    }


# =====================================================================
# Runtime / evaluation helpers
# =====================================================================

def reset_outbox():
    OUTBOX.clear()


def get_outbox_record(case_id: str):
    """Return the latest gated decision record."""
    for row in reversed(OUTBOX):
        if row.get("case_id") == case_id:
            return dict(row)

    return None


# =====================================================================
# Tool registry
# =====================================================================

TOOL_REGISTRY = {
    "get_claim": get_claim,
    "lookup_policy": lookup_policy,
    "check_coverage": check_coverage,
    "get_preauthorisation": get_preauthorisation,
    "issue_decision_letter": issue_decision_letter,
}


IRREVERSIBLE_TOOLS = {
    "issue_decision_letter",
}


def is_irreversible_tool(name: str):
    return name in IRREVERSIBLE_TOOLS


# =====================================================================
# Execution
# =====================================================================

def _execute_one_tool(
    call: dict,
    tool_spec_version: str = "v2",
):
    name = call.get("name")
    args = call.get("arguments", {})

    if name not in TOOL_REGISTRY:
        return {
            "tool": name,
            "ok": False,
            "error": "UNKNOWN_TOOL",
        }

    try:
        raw = TOOL_REGISTRY[name](**args)

        # =============================================================
        # D2(b) CONTROLLED VARIABLE
        #
        # Only get_preauthorisation changes between v1 and v2.
        # The underlying lookup above is identical.
        # =============================================================
        if name == "get_preauthorisation":

            # ---------------------------------------------------------
            # V1:
            # verbose raw records, repeated identifiers, no date-aware
            # poka-yoke.
            # ---------------------------------------------------------
            if tool_spec_version == "v1":
                result = {
                    "member_id":
                        raw["member_id"],
                    "procedure_code":
                        raw["procedure_code"],
                    "matching_records": [
                        {
                            "preauthorisation_id":
                                row["preauthorisation_id"],
                            "member_id":
                                raw["member_id"],
                            "procedure_code":
                                raw["procedure_code"],
                            "valid_from":
                                row["valid_from"],
                            "valid_to":
                                row["valid_to"],
                        }
                        for row in raw["records"]
                    ],
                }

            # ---------------------------------------------------------
            # V2:
            # date-aware poka-yoke. Code performs only the deterministic
            # validity comparison; Agent still decides what that means.
            # ---------------------------------------------------------
            elif tool_spec_version == "v2":
                date_of_service = raw.get(
                    "date_of_service"
                )

                if not date_of_service:
                    raise ValueError(
                        "V2 get_preauthorisation requires "
                        "date_of_service"
                    )

                valid_records = [
                    row
                    for row in raw["records"]
                    if (
                        row["valid_from"]
                        <= date_of_service
                        <= row["valid_to"]
                    )
                ]

                result = {
                    "procedure_code":raw["procedure_code"],
                    "date_of_service":date_of_service,
                    "records_found": len(raw["records"]),
                    "valid_records":valid_records,
                }

            else:
                raise ValueError(
                    f"Unknown tool_spec_version: "
                    f"{tool_spec_version}"
                )

        else:
            result = raw

        return {
            "tool": name,
            "ok": True,
            "result": result,
        }

    except Exception as exc:
        return {
            "tool": name,
            "ok": False,
            "error": str(exc),
        }


def execute_tool_calls(
    tool_calls: list[dict],
    parallel: bool = True,
    tool_spec_version: str = "v2",
):
    """Execute independent reads in parallel; writes remain sequential."""
    if not tool_calls:
        return []

    if (
        len(tool_calls) == 1
        or not parallel
    ):
        return [
            _execute_one_tool(
                call,
                tool_spec_version=tool_spec_version,
            )
            for call in tool_calls
        ]

    # Irreversible action is never batched with other calls.
    if any(
        is_irreversible_tool(
            call.get("name", "")
        )
        for call in tool_calls
    ):
        return [
            _execute_one_tool(
                call,
                tool_spec_version=tool_spec_version,
            )
            for call in tool_calls
        ]

    with ThreadPoolExecutor(
        max_workers=min(
            8,
            len(tool_calls),
        )
    ) as executor:
        return list(
            executor.map(
                lambda call:
                    _execute_one_tool(
                        call,
                        tool_spec_version=tool_spec_version,
                    ),
                tool_calls,
            )
        )


# =====================================================================
# D2(b) six-field tool descriptors
#
# Required fields:
# 1. NAME + SIGNATURE
# 2. WHAT
# 3. INPUT
# 4. RETURNS
# 5. FAILS
# 6. IRREVERSIBLE
#
# Only get_preauthorisation differs between v1 and v2.
# =====================================================================

_COMMON_PREFIX = """
TOOLS

1. get_claim(claim_id: str)
WHAT: Get the queued claim plus deterministic intake facts.
INPUT: valid queued claim_id.
RETURNS: {claim_id, member_id, hospital_id, date_of_service, narrative, documents, lines, claim_total, duplicate_of}.
FAILS: unknown claim_id.
IRREVERSIBLE: no.

2. lookup_policy(member_id: str)
WHAT: Get policy gates and policy_id.
INPUT: member_id from get_claim.
RETURNS: {policy_id, status, start_date, end_date, annual_limit, used_to_date, remaining_annual_limit, exclusions}.
FAILS: unknown member or linked policy.
IRREVERSIBLE: no.

3. check_coverage(policy_id: str, procedure_code: str)
WHAT: Resolve one line's coverage and PA requirement.
INPUT: policy_id from lookup_policy; procedure_code from claim.
RETURNS: {procedure_code, coverage_status, exclusion_code, requires_preauth}.
FAILS: unknown policy_id or procedure_code.
IRREVERSIBLE: no.
"""


_PREAUTH_V1 = """
4. get_preauthorisation(member_id: str, procedure_code: str)
WHAT: Search PA records for this member and procedure.
INPUT: member_id and procedure_code.
RETURNS: {member_id, procedure_code, matching_records:[{preauthorisation_id, member_id, procedure_code, valid_from, valid_to}]}.
FAILS: empty matching_records means no matching record.
IRREVERSIBLE: no.
"""


_PREAUTH_V2 = """
4. get_preauthorisation(member_id: str, procedure_code: str, date_of_service: str)
WHAT: Get PA records valid on the claim's service date.
INPUT: member_id and date_of_service from claim; procedure_code whose coverage returned requires_preauth=true.
RETURNS: {procedure_code, date_of_service, records_found, valid_records:[{preauthorisation_id, valid_from, valid_to}]}.
FAILS: records_found=0 means no matching PA exists; records_found>0 with empty valid_records means matching PA exists but none is valid on that date.
IRREVERSIBLE: no.
"""


_COMMON_SUFFIX = """
5. issue_decision_letter(case_id, decision, trigger, reason, evidence, missing_item=None)
WHAT: Record the final first-response decision.
INPUT: active case_id; decision; one trigger for ESCALATE; exact missing_item for ASK; evidence.
RETURNS: {recorded, case_id, decision}.
FAILS: invalid fields, wrong case, blocked gate, or duplicate write.
IRREVERSIBLE: yes; runtime-gated.
"""


TOOL_SPECS_V1 = (
    _COMMON_PREFIX
    + _PREAUTH_V1
    + _COMMON_SUFFIX
).strip()


TOOL_SPECS_V2 = (
    _COMMON_PREFIX
    + _PREAUTH_V2
    + _COMMON_SUFFIX
).strip()


def get_tool_specs(
    version: str = "v2",
):
    if version == "v1":
        return TOOL_SPECS_V1

    if version == "v2":
        return TOOL_SPECS_V2

    raise ValueError(
        f"Unknown tool spec version: {version}"
    )


def get_preauth_tool_spec(
    version: str = "v2",
):
    if version == "v1":
        return _PREAUTH_V1.strip()

    if version == "v2":
        return _PREAUTH_V2.strip()

    raise ValueError(
        f"Unknown tool spec version: {version}"
    )