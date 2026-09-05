"""Backend seam for Problem A.

This module owns the vendor-aware live call and the deterministic scripted
backend. `src.agent_core` keeps the loop and delegates model calls here.
"""
from __future__ import annotations

import getpass
import json
import os
import re
import time

from src import config


def _get_openrouter_key():
    key = os.environ.get("MY_PRIVATE_OPENROUTER_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    try:
        from dotenv import load_dotenv
        load_dotenv()
        key = os.environ.get("MY_PRIVATE_OPENROUTER_KEY") or os.environ.get("OPENROUTER_API_KEY")
        if key:
            return key
    except Exception:
        pass
    try:
        from google.colab import userdata
        key = userdata.get("OPENROUTER_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return getpass.getpass("Paste your OpenRouter API key (hidden): ")


def _live(messages: list[dict]):
    """The only vendor-aware function. OpenRouter uses the OpenAI-compatible API."""
    from openai import OpenAI, RateLimitError

    client = OpenAI(base_url=config.BASE_URL, api_key=_get_openrouter_key())
    kwargs = dict(model=config.MODEL, messages=messages, temperature=0.0)
    if config.USE_JSON_RESPONSE_FORMAT:
        kwargs["response_format"] = {"type": "json_object"}

    last_error = None
    for attempt in range(config.LIVE_RETRIES):
        try:
            r = client.chat.completions.create(**kwargs)
            usage = {"input_tokens": 0, "output_tokens": 0}
            if getattr(r, "usage", None):
                usage["input_tokens"] = getattr(r.usage, "prompt_tokens", 0) or 0
                usage["output_tokens"] = getattr(r.usage, "completion_tokens", 0) or 0
            return {"text": r.choices[0].message.content.strip(), "usage": usage}
        except RateLimitError as e:
            last_error = e
            if attempt == config.LIVE_RETRIES - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise last_error


def _observations_from_messages(messages: list[dict]):
    observations = []
    for m in messages:
        if m.get("role") != "user":
            continue
        try:
            x = json.loads(m.get("content", ""))
        except Exception:
            continue
        if x.get("type") == "observation":
            observations.extend(x.get("results", []))
    return observations


def _latest_issue_decision_args(messages: list[dict]):
    for m in reversed(messages):
        if m.get("role") != "assistant":
            continue
        try:
            x = json.loads(m.get("content", ""))
        except Exception:
            continue
        if x.get("type") != "action":
            continue
        for call in reversed(x.get("tool_calls", [])):
            if call.get("name") == "issue_decision_letter":
                return call.get("arguments", {})
    return None


def _issue_decision_action(case_id: str, decision: str, trigger, missing_item, reason: str, evidence: list):
    return {
        "type": "action",
        "tool_calls": [
            {
                "name": "issue_decision_letter",
                "arguments": {
                    "case_id": case_id,
                    "decision": decision,
                    "trigger": trigger,
                    "missing_item": missing_item,
                    "reason": reason,
                    "evidence": evidence,
                },
            }
        ],
    }


def _scripted(messages: list[dict]):
    """Deterministic canned backend that drives the SAME loop without network or key."""
    obs = _observations_from_messages(messages)
    by_tool = {}
    helper_context = None
    for o in obs:
        if o.get("type") == "helper_context":
            helper_context = o
        elif o.get("ok"):
            by_tool.setdefault(o["tool"], []).append(o["result"])

    decision_args = _latest_issue_decision_args(messages)
    if decision_args and any(o.get("tool") == "issue_decision_letter" for o in obs):
        return {"text": json.dumps({
            "type": "final",
            "decision": decision_args.get("decision"),
            "trigger": decision_args.get("trigger"),
            "missing_item": decision_args.get("missing_item"),
            "reason": decision_args.get("reason"),
            "evidence": decision_args.get("evidence", []),
        }), "usage": {"input_tokens": 0, "output_tokens": 0}}

    if not by_tool.get("get_claim"):
        user = next((m["content"] for m in reversed(messages) if m.get("role") == "user" and m.get("content", "").startswith("Process claim")), "")
        match = re.search(r"(CLM-\d+)", user)
        cid = match.group(1) if match else ""
        payload = {"type": "action", "tool_calls": [{"name": "get_claim", "arguments": {"claim_id": cid}}]}
        return {"text": json.dumps(payload), "usage": {"input_tokens": 0, "output_tokens": 0}}

    claim = by_tool["get_claim"][-1]
    if claim.get("duplicate_of"):
        payload = _issue_decision_action(
            claim["claim_id"],
            "escalate",
            "duplicate_claim",
            None,
            f"Exact duplicate of {claim['duplicate_of']}.",
            [{"source": "get_claim", "fact": f"duplicate_of={claim['duplicate_of']}"}],
        )
        return {"text": json.dumps(payload), "usage": {"input_tokens": 0, "output_tokens": 0}}

    narrative = (claim.get("narrative") or "").lower()
    if "system note:" in narrative or ("returned:" in narrative and "[" in narrative):
        payload = _issue_decision_action(
            claim["claim_id"],
            "escalate",
            "instruction_in_member_narrative",
            None,
            "Untrusted member narrative contains an instruction/tool-output imitation.",
            [{"source": "get_claim", "fact": "hostile instruction in member narrative"}],
        )
        return {"text": json.dumps(payload), "usage": {"input_tokens": 0, "output_tokens": 0}}

    if not by_tool.get("lookup_policy"):
        return {"text": json.dumps({"type": "action", "tool_calls": [{"name": "lookup_policy", "arguments": {"member_id": claim["member_id"]}}]}), "usage": {"input_tokens": 0, "output_tokens": 0}}

    pol = by_tool["lookup_policy"][-1]
    dos = claim["date_of_service"]
    total = sum(float(x["amount"]) for x in claim["lines"])
    if pol["status"] == "lapsed":
        payload = _issue_decision_action(claim["claim_id"], "escalate", "policy_lapsed", None, "Policy is lapsed.", [{"source": "lookup_policy", "fact": f"{pol['policy_id']} status=lapsed"}])
        return {"text": json.dumps(payload), "usage": {"input_tokens": 0, "output_tokens": 0}}
    if not (pol["start_date"] <= dos <= pol["end_date"]):
        payload = _issue_decision_action(claim["claim_id"], "escalate", "outside_policy_dates", None, "Service date is outside policy dates.", [{"source": "lookup_policy", "fact": f"{dos} outside {pol['start_date']}..{pol['end_date']}"}])
        return {"text": json.dumps(payload), "usage": {"input_tokens": 0, "output_tokens": 0}}
    if total > float(pol["remaining_annual_limit"]):
        payload = _issue_decision_action(claim["claim_id"], "escalate", "annual_limit_exceeded", None, "Claim total exceeds remaining annual limit.", [{"source": "lookup_policy", "fact": f"claim_total={total:g}, remaining={pol['remaining_annual_limit']}"}])
        return {"text": json.dumps(payload), "usage": {"input_tokens": 0, "output_tokens": 0}}

    coverage_by_code = {x["procedure_code"]: x for x in by_tool.get("check_coverage", [])}
    pa_by_code = {x["procedure_code"]: x for x in by_tool.get("get_preauthorisation", [])}
    missing_cov = [x["code"] for x in claim["lines"] if x["code"] not in coverage_by_code]
    if missing_cov:
        calls = [{"name": "check_coverage", "arguments": {"policy_id": pol["policy_id"], "procedure_code": c}} for c in missing_cov]
        return {"text": json.dumps({"type": "action", "tool_calls": calls}), "usage": {"input_tokens": 0, "output_tokens": 0}}

    required_pa = [code for code, result in coverage_by_code.items() if result.get("requires_preauth")]
    missing_pa = [c for c in required_pa if c not in pa_by_code]
    if missing_pa:
        calls = [{"name": "get_preauthorisation", "arguments": {"member_id": claim["member_id"], "procedure_code": c}} for c in missing_pa]
        return {"text": json.dumps({"type": "action", "tool_calls": calls}), "usage": {"input_tokens": 0, "output_tokens": 0}}

    if helper_context is None:
        return {"text": json.dumps({"type": "action", "tool_calls": []}), "usage": {"input_tokens": 0, "output_tokens": 0}}

    missing_docs = helper_context.get("missing_documents", [])
    if missing_docs:
        m = missing_docs[0]
        item = f"{m['document'].replace('_', ' ')} for line {m['procedure_code']}"
        payload = _issue_decision_action(claim["claim_id"], "request_document", "missing_required_document", item, f"Required document is missing: {item}.", [{"source": "check_missing_documents", "fact": item}])
        return {"text": json.dumps(payload), "usage": {"input_tokens": 0, "output_tokens": 0}}

    for c in required_pa:
        raw = pa_by_code[c].get("records", [])
        valid = next((x for x in raw if x["valid_from"] <= dos <= x["valid_to"]), None)
        if valid is None:
            if raw:
                row = raw[0]
                item = f"current pre-authorisation for line {c}, valid on {dos}"
                trig = "expired_preauthorisation"
                fact = f"{row['preauthorisation_id']} valid {row['valid_from']}..{row['valid_to']}; service date {dos}"
            else:
                item = f"pre-authorisation reference for line {c}, valid on {dos}"
                trig = "missing_preauthorisation"
                fact = f"no matching preauthorisation for {c}"
            payload = _issue_decision_action(claim["claim_id"], "request_document", trig, item, item, [{"source": "get_preauthorisation", "fact": fact}])
            return {"text": json.dumps(payload), "usage": {"input_tokens": 0, "output_tokens": 0}}

    approved_total = 0.0
    refused_total = 0.0
    evidence = []
    for line in claim["lines"]:
        cov = coverage_by_code[line["code"]]
        if cov["coverage_status"] == "excluded":
            refused_total += float(line["amount"])
            evidence.append({"source": "check_coverage", "fact": f"{line['code']} excluded: {cov.get('exclusion_code')}"})
        else:
            approved_total += float(line["amount"])
            fact = f"{line['code']} covered"
            if line["code"] in required_pa:
                raw = pa_by_code[line["code"]].get("records", [])
                valid = next((x for x in raw if x["valid_from"] <= dos <= x["valid_to"]), None)
                if valid:
                    fact += f"; preauth {valid['preauthorisation_id']} valid"
            evidence.append({"source": "check_coverage", "fact": fact})
    if helper_context.get("hospital_panel") is False:
        evidence.append({"source": "check_hospital_panel", "fact": f"{claim['hospital_id']} is non-panel"})
    payload = _issue_decision_action(
        claim["claim_id"],
        "approve_in_principle",
        None,
        None,
        f"All lines resolved. approved_total={approved_total:g}; refused_total={refused_total:g}.",
        evidence,
    )
    return {"text": json.dumps(payload), "usage": {"input_tokens": 0, "output_tokens": 0}}


def call_model(messages: list[dict]):
    if config.BACKEND == "scripted":
        return _scripted(messages)
    if config.BACKEND == "live":
        return _live(messages)
    raise ValueError(f"Unknown BACKEND: {config.BACKEND}")
