"""Create and run the D4 prose judgement check.

The deterministic harness already grades fixed fields. This runner grades only
the natural-language reason and evidence fields against the recorded trace.
"""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from src import config
from src.backends import _get_openrouter_key


ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE = ROOT / "results" / "live" / "google__gemini-2_5-flash.json"
DEFAULT_OUTPUT_DIR = ROOT / "results" / "judgement"
RUBRIC_PATH = ROOT / "evals" / "judgement_prompt.txt"

# Fixed before review to cover different decisions and tool paths. Trial 1 is
# always used, so the sample does not depend on whether an individual run passed.
SAMPLE_CASE_IDS = [
    "CLM-3001", "CLM-8842", "CLM-8861", "CLM-9506",  # approve
    "CLM-8888", "CLM-8894", "CLM-8901", "CLM-9507",  # ask
    "CLM-8910", "CLM-8917", "CLM-8925", "CLM-8933",  # escalate
]

CHECK_NAMES = [
    "consistent_with_structured_outcome",
    "evidence_present_in_trace",
    "no_unsupported_facts",
    "specific_enough",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def select_records(source: dict) -> list[dict]:
    records = source.get("records")
    if records is None:
        # Model-battery files store the evaluation payload directly in some versions.
        records = source.get("results", [])
    by_key = {(r.get("case_id"), r.get("trial")): r for r in records}
    selected = []
    missing = []
    for case_id in SAMPLE_CASE_IDS:
        record = by_key.get((case_id, 1))
        if record is None:
            missing.append(case_id)
        else:
            selected.append(record)
    if missing:
        raise ValueError(f"Source result is missing fixed judgement cases: {missing}")
    return selected


def compact_trace(record: dict) -> list[dict]:
    trace = []
    for event in record.get("tool_history", []):
        calls = event.get("tool_calls", [])
        observations = event.get("observations", [])
        trace.append(
            {
                "turn": event.get("turn"),
                "tools": [call.get("name") for call in calls],
                "observations": observations,
            }
        )
    return trace


def review_item(record: dict) -> dict:
    return {
        "case_id": record.get("case_id"),
        "trial": record.get("trial"),
        "expected_decision": record.get("expected_decision"),
        "deterministic_pass": record.get("passed"),
        "decision": record.get("decision"),
        "trigger": record.get("trigger"),
        "missing_item": record.get("missing_item"),
        "reason": record.get("reason"),
        "evidence": record.get("evidence"),
        "trace": compact_trace(record),
    }


def base_payload(source_path: Path, source: dict, selected: list[dict]) -> dict:
    return {
        "source_model": source.get("model", "google/gemini-2.5-flash"),
        "source_file": str(source_path.resolve()),
        "source_trials": source.get("summary", {}).get("trials", len(source.get("records", []))),
        "selection_rule": (
            "Twelve case IDs fixed before prose review: four approve, four request-document, "
            "and four escalate cases; always trial 1. Cases cover different tool paths and "
            "are selected independently of judgement outcome."
        ),
        "selected_case_ids": SAMPLE_CASE_IDS,
        "rubric_file": str(RUBRIC_PATH.resolve()),
        "rubric_checks": CHECK_NAMES,
        "records": [review_item(r) for r in selected],
    }


def write_human_template(source_path: Path, output_dir: Path) -> Path:
    source = load_json(source_path)
    selected = select_records(source)
    payload = base_payload(source_path, source, selected)
    payload.update(
        {
            "method": "human_review",
            "reviewer": "FILL_REAL_TEAM_MEMBER_NAME",
            "review_date": "YYYY-MM-DD",
            "instructions": (
                "A team member must inspect each trace and fill all four checks, "
                "judgement_pass, and review_comment. Do not change source fields."
            ),
        }
    )
    for item in payload["records"]:
        item["checks"] = {name: None for name in CHECK_NAMES}
        item["judgement_pass"] = None
        item["review_comment"] = ""
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "judgement_rubric.txt").write_text(
        RUBRIC_PATH.read_text(encoding="utf-8"), encoding="utf-8"
    )
    out = output_dir / "judgement_human_template.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def validate_human(template_path: Path, output_dir: Path) -> tuple[Path, Path]:
    payload = load_json(template_path)
    if payload.get("reviewer") in (None, "", "FILL_REAL_TEAM_MEMBER_NAME"):
        raise ValueError("Fill the real human reviewer name before validation.")
    if payload.get("review_date") in (None, "", "YYYY-MM-DD"):
        raise ValueError("Fill the human review date before validation.")
    records = payload.get("records", [])
    if len(records) != len(SAMPLE_CASE_IDS):
        raise ValueError(f"Expected {len(SAMPLE_CASE_IDS)} reviewed records, found {len(records)}.")
    for item in records:
        checks = item.get("checks", {})
        if any(checks.get(name) not in (True, False) for name in CHECK_NAMES):
            raise ValueError(f"Incomplete checks for {item.get('case_id')}.")
        expected_pass = all(checks[name] for name in CHECK_NAMES)
        if item.get("judgement_pass") is not expected_pass:
            raise ValueError(
                f"judgement_pass for {item.get('case_id')} must equal the AND of all four checks."
            )
        if not str(item.get("review_comment", "")).strip():
            raise ValueError(f"Missing review_comment for {item.get('case_id')}.")
    passed = sum(bool(item["judgement_pass"]) for item in records)
    payload["summary"] = {
        "reviewed": len(records),
        "passed": passed,
        "failed": len(records) - passed,
        "pass_rate": passed / len(records),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / "judgement_results_human.json"
    result_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_path = output_dir / "judgement_summary_human.md"
    summary_path.write_text(summary_markdown(payload), encoding="utf-8")
    return result_path, summary_path


def model_family(model: str) -> str:
    return model.split("/", 1)[0].lower()


def judge_one(client, judge_model: str, rubric: str, item: dict) -> tuple[dict, dict]:
    request = {
        "case_id": item["case_id"],
        "expected_decision": item["expected_decision"],
        "decision": item["decision"],
        "trigger": item["trigger"],
        "missing_item": item["missing_item"],
        "reason": item["reason"],
        "evidence": item["evidence"],
        "trace": item["trace"],
    }
    response = client.chat.completions.create(
        model=judge_model,
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": rubric},
            {"role": "user", "content": json.dumps(request, ensure_ascii=False)},
        ],
    )
    text = response.choices[0].message.content
    verdict = json.loads(text)
    if verdict.get("pass") not in (True, False) or not str(verdict.get("reason", "")).strip():
        raise ValueError(f"Invalid judge response for {item['case_id']}: {text}")
    usage = getattr(response, "usage", None)
    usage_dict = {
        "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
    }
    return verdict, usage_dict


def run_llm_judge(source_path: Path, output_dir: Path, judge_model: str) -> tuple[Path, Path]:
    from openai import OpenAI

    source = load_json(source_path)
    selected = select_records(source)
    payload = base_payload(source_path, source, selected)
    source_model = payload["source_model"]
    if model_family(source_model) == model_family(judge_model):
        raise ValueError(
            f"Judge must use a different model family: source={source_model}, judge={judge_model}"
        )
    rubric = RUBRIC_PATH.read_text(encoding="utf-8")
    client = OpenAI(base_url=config.BASE_URL, api_key=_get_openrouter_key())
    reviewed = []
    total_in = total_out = 0
    for source_record in payload.pop("records"):
        verdict, usage = judge_one(client, judge_model, rubric, source_record)
        total_in += usage["input_tokens"]
        total_out += usage["output_tokens"]
        source_record["judgement_pass"] = verdict["pass"]
        source_record["review_comment"] = verdict["reason"]
        source_record["judge_usage"] = usage
        reviewed.append(source_record)
        print(f"{source_record['case_id']}: {'PASS' if verdict['pass'] else 'FAIL'} - {verdict['reason']}")
    passed = sum(bool(item["judgement_pass"]) for item in reviewed)
    payload.update(
        {
            "method": "llm_as_judge",
            "judge_model": judge_model,
            "review_date": date.today().isoformat(),
            "records": reviewed,
            "summary": {
                "reviewed": len(reviewed),
                "passed": passed,
                "failed": len(reviewed) - passed,
                "pass_rate": passed / len(reviewed),
                "judge_input_tokens": total_in,
                "judge_output_tokens": total_out,
            },
        }
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "judgement_rubric.txt").write_text(rubric, encoding="utf-8")
    result_path = output_dir / "judgement_results_llm.json"
    result_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_path = output_dir / "judgement_summary_llm.md"
    summary_path.write_text(summary_markdown(payload), encoding="utf-8")
    return result_path, summary_path


def summary_markdown(payload: dict) -> str:
    summary = payload["summary"]
    reviewer = payload.get("reviewer") or payload.get("judge_model")
    lines = [
        "# D4 judgement check summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Source model: `{payload['source_model']}`",
        f"- Reviewer/judge: `{reviewer}`",
        f"- Review date: `{payload['review_date']}`",
        f"- Records reviewed: {summary['reviewed']}",
        f"- Passed: {summary['passed']}",
        f"- Failed: {summary['failed']}",
        f"- Judgement pass rate: {summary['pass_rate']:.1%}",
        "",
        "The deterministic harness grades decision, trigger, missing item and gated-action count. "
        "This judgement check grades only the natural-language reason and evidence against the trace.",
        "",
        "| Case | Decision | Deterministic check | Prose judgement | Comment |",
        "|---|---|---:|---:|---|",
    ]
    for item in payload["records"]:
        comment = str(item.get("review_comment", "")).replace("|", "\\|")
        lines.append(
            f"| {item['case_id']} | {item.get('decision')} | "
            f"{'PASS' if item.get('deterministic_pass') else 'FAIL'} | "
            f"{'PASS' if item.get('judgement_pass') else 'FAIL'} | {comment} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare or run the D4 prose judgement check.")
    parser.add_argument(
        "--mode", required=True, choices=["human-template", "validate-human", "llm"]
    )
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--template", type=Path, help="Completed human template for validate-human mode.")
    parser.add_argument("--judge-model", default="openai/gpt-4o-mini")
    args = parser.parse_args()

    if args.mode == "human-template":
        print(f"Saved human review template to {write_human_template(args.source, args.output_dir)}")
    elif args.mode == "validate-human":
        if args.template is None:
            raise SystemExit("--template is required for validate-human mode")
        result, summary = validate_human(args.template, args.output_dir)
        print(f"Saved validated human results to {result}")
        print(f"Saved summary to {summary}")
    else:
        result, summary = run_llm_judge(args.source, args.output_dir, args.judge_model)
        print(f"Saved LLM judgement results to {result}")
        print(f"Saved summary to {summary}")


if __name__ == "__main__":
    main()
