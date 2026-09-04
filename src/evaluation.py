
"""D4/D5 evaluation harness. Outcome-graded, clean state per case."""
from __future__ import annotations
import json, statistics
from pathlib import Path
from src.agent_core import run_agent
from src.tools import reset_outbox

ROOT=Path(__file__).resolve().parents[1]


def load_expected_outcomes():
    with open(ROOT/"expected_outcomes_A.json", "r", encoding="utf-8") as f:
        return json.load(f)


def grade_run(run_result: dict, expected: dict):
    checks={}
    checks["decision"] = run_result.get("decision") == expected.get("expected_decision")
    if expected.get("expected_decision") == "escalate":
        checks["trigger"] = run_result.get("trigger") == expected.get("trigger")
    if expected.get("expected_decision") == "request_document":
        checks["missing_item"] = (run_result.get("missing_item") or "").strip().lower() == (expected.get("missing") or "").strip().lower()
    checks["gated_action_once"] = run_result.get("gated_action_count", 0) == 1
    return {"passed": all(checks.values()), "checks": checks}


def run_evaluation(case_ids: list[str] | None = None, *, negative_trials: int = 3, ordinary_trials: int = 1, approved_for_write: bool = True, parallel_enabled: bool | None = None, tool_spec_version: str | None = None):
    expected=load_expected_outcomes()
    if case_ids is not None:
        wanted=set(case_ids); expected=[x for x in expected if x["case_id"] in wanted]
    records=[]
    for exp in expected:
        negative=exp["expected_decision"] != "approve_in_principle"
        trials=negative_trials if negative else ordinary_trials
        for trial in range(1, trials+1):
            reset_outbox()
            result=run_agent(exp["case_id"], approved_for_write=approved_for_write, parallel_enabled=parallel_enabled, tool_spec_version=tool_spec_version)
            grade=grade_run(result, exp)
            records.append({"case_id":exp["case_id"],"trial":trial,"negative":negative,"expected_decision":exp["expected_decision"],"passed":grade["passed"],"checks":grade["checks"],**result})
    return records


def summarize_results(records: list[dict]):
    if not records:
        return {}
    neg=[r for r in records if r.get("negative")]
    turns=[r.get("turns",0) for r in records]
    return {
        "trials": len(records),
        "pass_rate": sum(bool(r.get("passed")) for r in records)/len(records),
        "negative_trials": len(neg),
        "negative_pass_rate": (sum(bool(r.get("passed")) for r in neg)/len(neg)) if neg else None,
        "median_turns": statistics.median(turns),
        "worst_turns": max(turns),
        "cap_hits": sum(r.get("failure_reason")=="NO_FINAL_BEFORE_CAP" for r in records),
        "input_tokens": sum(r.get("input_tokens",0) for r in records),
        "output_tokens": sum(r.get("output_tokens",0) for r in records),
        "api_cost": sum(r.get("cost",0.0) for r in records),
    }

"""Evaluation harness, graders, and run-level metrics.

Purpose
-------
Run the same isolated evaluation set against scripted or live backends and compare
Agent outputs with the committed Problem A answer key.

Expected inputs
---------------
- Cases from data_A / the extended fixture set.
- Ground truth from expected_outcomes_A.json.
- Agent runner from agent_core.
- Trial rules: ordinary case = 1 trial/model; negative case = 3 trials/model.
- Optional judgement prompt / judge for fields that cannot be exact-matched.

Expected outputs
----------------
Per-trial and aggregate results including:
- pass / fail
- overall pass rate
- negative-only pass rate
- check type (code or judgement)
- turns, token counts, cost
- median / worst turns and cap-hit information where needed
- machine-readable result files written under results/

Grading principles
------------------
- Clean state for every case/trial.
- Grade the outcome, not a required tool path.
- Correct outcome with the wrong single trigger is a failure.
- Use code checks for fixed-value fields; use judgement checks only where needed.

A2 mapping: D4, D5(a), D5(b); provides measured P and run data for D0(b), D6, D7.
"""

