"""Evaluation harness for Problem A."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from src import config
from src.agent_core import run_agent
from src.evaluation import (
    is_negative_case,
    iter_expected_outcomes,
    load_expected_outcomes,
    validate_expected_outcome_entry,
)
from src.tools import reset_outbox


D2C_REPORT_KEYS = [
    "trials",
    "pass_rate",
    "negative_pass_rate",
    "median_turns",
    "worst_turns",
    "tool_turns",
    "model_calls",
    "input_tokens",
    "output_tokens",
    "api_cost",
    "max_tool_calls_in_one_turn",
    "cap_hits",
]


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
    max_tool_calls_per_turn: int | None = None,
    tool_spec_version: str | None = None,
    progress_callback=None,
    progress_label: str | None = None,
):
    expected_rows = load_expected_outcomes()
    validate_expected_outcome_entry(expected_rows)
    selected_rows = list(iter_expected_outcomes(expected_rows, case_ids=case_ids))
    total_runs = sum(negative_trials if is_negative_case(row) else ordinary_trials for row in selected_rows)
    records = []
    run_index = 0
    for expected in selected_rows:
        negative = is_negative_case(expected)
        trials = negative_trials if negative else ordinary_trials
        for trial in range(1, trials + 1):
            run_index += 1
            if progress_callback:
                progress_callback({
                    "label": progress_label,
                    "run_index": run_index,
                    "total_runs": total_runs,
                    "case_id": expected["case_id"],
                    "trial": trial,
                    "trials_for_case": trials,
                    "mode_max_tool_calls_per_turn": max_tool_calls_per_turn,
                })
            reset_outbox()
            result = run_agent(
                expected["case_id"],
                approved_for_write=approved_for_write,
                parallel_enabled=parallel_enabled,
                max_tool_calls_per_turn=max_tool_calls_per_turn,
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


def summarize_d2c_records(records: list[dict]):
    summary = summarize_results(records)
    if not records:
        return summary
    tool_calls_per_turn = [
        len(step.get("tool_calls", []))
        for record in records
        for step in record.get("tool_history", [])
        if step.get("tool_calls")
    ]
    summary.update({
        "model_calls": sum(r.get("model_calls", 0) for r in records),
        "tool_turns": sum(r.get("tool_turns", r.get("turns", 0)) for r in records),
        "total_tool_calls": sum(
            len(step.get("tool_calls", []))
            for record in records
            for step in record.get("tool_history", [])
        ),
        "max_tool_calls_in_one_turn": max(tool_calls_per_turn) if tool_calls_per_turn else 0,
    })
    return summary


def run_d2c_comparison(
    case_ids: list[str] | None = None,
    *,
    backend: str = "scripted",
    approved_for_write: bool = True,
    tool_spec_version: str | None = None,
    negative_trials: int = 3,
    ordinary_trials: int = 1,
    progress: bool = False,
):
    def _progress(event: dict):
        label = event.get("label") or "run"
        print(
            f"[D2(c) {label}] {event['run_index']}/{event['total_runs']} "
            f"{event['case_id']} trial {event['trial']}/{event['trials_for_case']} "
            f"MAX_TOOL_CALLS_PER_TURN={event['mode_max_tool_calls_per_turn']}",
            flush=True,
        )

    original_backend = config.BACKEND
    original_parallel = config.PARALLEL_ENABLED
    original_max_calls = config.MAX_TOOL_CALLS_PER_TURN
    try:
        config.BACKEND = backend
        config.PARALLEL_ENABLED = True

        config.MAX_TOOL_CALLS_PER_TURN = 1
        sequential_records = run_evaluation(
            case_ids=case_ids,
            negative_trials=negative_trials,
            ordinary_trials=ordinary_trials,
            approved_for_write=approved_for_write,
            parallel_enabled=True,
            max_tool_calls_per_turn=1,
            tool_spec_version=tool_spec_version,
            progress_callback=_progress if progress else None,
            progress_label="sequential",
        )

        config.MAX_TOOL_CALLS_PER_TURN = None
        batched_records = run_evaluation(
            case_ids=case_ids,
            negative_trials=negative_trials,
            ordinary_trials=ordinary_trials,
            approved_for_write=approved_for_write,
            parallel_enabled=True,
            max_tool_calls_per_turn=None,
            tool_spec_version=tool_spec_version,
            progress_callback=_progress if progress else None,
            progress_label="batched",
        )
    finally:
        config.BACKEND = original_backend
        config.PARALLEL_ENABLED = original_parallel
        config.MAX_TOOL_CALLS_PER_TURN = original_max_calls

    return {
        "experiment": "D2(c) sequential vs batched tool calls",
        "backend": backend,
        "model": config.MODEL,
        "tool_spec_version": tool_spec_version or config.TOOL_SPEC_VERSION,
        "autonomy": config.AUTONOMY,
        "approved_for_write": approved_for_write,
        "modes": {
            "sequential": {
                "max_tool_calls_per_turn": 1,
                "parallel_enabled": True,
            },
            "batched": {
                "max_tool_calls_per_turn": None,
                "parallel_enabled": True,
            },
        },
        "dependency_rule": (
            "get_claim runs first; lookup_policy waits for get_claim and runs alone; "
            "check_coverage calls for claim lines may batch after policy gates pass; "
            "get_preauthorisation waits for coverage.requires_preauth; "
            "issue_decision_letter runs alone behind the autonomy gate."
        ),
        "sequential": {
            "mode": "MAX_TOOL_CALLS_PER_TURN=1",
            "summary": summarize_d2c_records(sequential_records),
            "records": sequential_records,
        },
        "batched": {
            "mode": "MAX_TOOL_CALLS_PER_TURN=None",
            "summary": summarize_d2c_records(batched_records),
            "records": batched_records,
        },
    }


def print_d2c_report(comparison: dict):
    sequential = comparison["sequential"]["summary"]
    batched = comparison["batched"]["summary"]
    print("D2(c) sequential vs batched tool-call comparison")
    print(f"Backend: {comparison.get('backend')}")
    print("Dependency rule:")
    print(comparison["dependency_rule"])
    print()
    print("Metric                         sequential        batched")
    for key in D2C_REPORT_KEYS:
        print(f"{key:<30} {str(sequential.get(key)):<17} {batched.get(key)}")


def save_d2c_comparison(comparison: dict, path: str | Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(comparison, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def build_d2c_report_markdown(comparison: dict):
    sequential = comparison["sequential"]["summary"]
    batched = comparison["batched"]["summary"]
    lines = [
        "# D2(c) Sequential vs Batched Tool Calls",
        "",
        f"- Backend: `{comparison.get('backend')}`",
        f"- Model: `{comparison.get('model')}`",
        f"- Tool spec version: `{comparison.get('tool_spec_version')}`",
        f"- Autonomy: `{comparison.get('autonomy')}`",
        f"- Approved for write: `{comparison.get('approved_for_write')}`",
        f"- Sequential mode: `{comparison['sequential'].get('mode')}`",
        f"- Batched mode: `{comparison['batched'].get('mode')}`",
        f"- Dependency rule: {comparison['dependency_rule']}",
        "",
        "| Metric | Sequential | Batched |",
        "|---|---:|---:|",
    ]
    for key in D2C_REPORT_KEYS:
        lines.append(f"| `{key}` | {sequential.get(key)} | {batched.get(key)} |")

    lines.extend([
        "",
        "## Interpretation",
        "",
        (
            "The D2(c) lever is `MAX_TOOL_CALLS_PER_TURN`: the sequential baseline "
            "uses `1`, while the batched version uses `None` and allows multiple "
            "independent tool calls to be executed in one model turn."
        ),
        "",
        (
            "Correctness is checked by comparing pass rate across the same evaluation "
            "cases. A lower `tool_turns` or `model_calls` count in the batched run is "
            "the measured turn-collapse effect."
        ),
    ])
    if comparison.get("backend") == "scripted":
        lines.extend([
            "",
            "Scripted backend note: token and API cost fields are zero because no live model API is called.",
        ])
    return "\n".join(lines) + "\n"


def write_d2c_report(comparison: dict, path: str | Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_d2c_report_markdown(comparison), encoding="utf-8")
    return path
