"""Evaluation harness for Problem A."""
from __future__ import annotations

import statistics

from src.agent_core import run_agent
from src.evaluation import (
    is_negative_case,
    iter_expected_outcomes,
    load_expected_outcomes,
    validate_expected_outcome_entry,
)
from src.tools import reset_outbox


def grade_run(run_result: dict, expected: dict):
    checks = {}
    checks["decision"] = run_result.get("decision") == expected.get("expected_decision")
    if expected.get("expected_decision") == "escalate":
        checks["trigger"] = run_result.get("trigger") == expected.get("trigger")
    if expected.get("expected_decision") == "request_document":
        checks["missing_item"] = (run_result.get("missing_item") or "").strip().lower() == (expected.get("missing") or "").strip().lower()
    gated_attempts = sum(
        1
        for h in run_result.get("tool_history", [])
        for c in h.get("tool_calls", [])
        if c.get("name") == "issue_decision_letter"
    )
    checks["gated_action_attempted_once"] = gated_attempts == 1
    if run_result.get("write_status") == "held":
        checks["gated_action_held_not_written"] = run_result.get("gated_action_count", 0) == 0
    else:
        checks["gated_action_recorded_once"] = run_result.get("gated_action_count", 0) == 1
    return {"passed": all(checks.values()), "checks": checks}


def _build_run_record(*, expected: dict, trial: int, negative: bool, result: dict, grade: dict):
    return {
        "case_id": expected["case_id"],
        "trial": trial,
        "negative": negative,
        "expected_decision": expected["expected_decision"],
        "passed": grade["passed"],
        "checks": grade["checks"],
        **result,
    }


def run_evaluation(
    case_ids: list[str] | None = None,
    *,
    negative_trials: int = 3,
    ordinary_trials: int = 1,
    approved_for_write: bool = True,
    parallel_enabled: bool | None = None,
    tool_spec_version: str | None = None,
):
    expected_rows = load_expected_outcomes()
    validate_expected_outcome_entry(expected_rows)
    selected_rows = list(iter_expected_outcomes(expected_rows, case_ids=case_ids))
    records = []
    for expected in selected_rows:
        negative = is_negative_case(expected)
        trials = negative_trials if negative else ordinary_trials
        for trial in range(1, trials + 1):
            reset_outbox()
            result = run_agent(
                expected["case_id"],
                approved_for_write=approved_for_write,
                parallel_enabled=parallel_enabled,
                tool_spec_version=tool_spec_version,
            )
            grade = grade_run(result, expected)
            records.append(_build_run_record(expected=expected, trial=trial, negative=negative, result=result, grade=grade))
    return records


def summarize_results(records: list[dict]):
    if not records:
        return {}
    neg = [r for r in records if r.get("negative")]
    turns = [r.get("tool_turns", r.get("turns", 0)) for r in records]
    return {
        "trials": len(records),
        "pass_rate": sum(bool(r.get("passed")) for r in records) / len(records),
        "negative_trials": len(neg),
        "negative_pass_rate": (sum(bool(r.get("passed")) for r in neg) / len(neg)) if neg else None,
        "median_turns": statistics.median(turns),
        "worst_turns": max(turns),
        "cap_hits": sum(r.get("failure_reason") == "NO_FINAL_BEFORE_CAP" for r in records),
        "input_tokens": sum(r.get("input_tokens", 0) for r in records),
        "output_tokens": sum(r.get("output_tokens", 0) for r in records),
        "api_cost": sum(r.get("cost", 0.0) for r in records),
    }
