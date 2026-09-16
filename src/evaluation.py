"""Problem A evaluation data helpers."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_OUTCOMES_PATH = ROOT / "expected_outcomes_A.json"
DATA_DIR = ROOT / "data_A"
EVAL_DIR = ROOT / "evals"
GUARDRAIL_CASES_PATH = EVAL_DIR / "guardrail_cases.json"
JUDGEMENT_PROMPT_PATH = EVAL_DIR / "judgement_prompt.txt"


def load_expected_outcomes(path: Path | None = None):
    with open(path or EXPECTED_OUTCOMES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_expected_outcome_entry(entries: list[dict]):
    required = {"case_id", "expected_decision"}
    for entry in entries:
        missing = required - set(entry)
        if missing:
            raise ValueError(f"Expected outcome entry missing fields: {sorted(missing)} for case_id={entry.get('case_id')}")
        decision = entry["expected_decision"]
        if decision not in {"approve_in_principle", "request_document", "escalate"}:
            raise ValueError(f"Invalid expected_decision for case_id={entry['case_id']}: {decision}")
        if decision == "escalate" and not entry.get("trigger"):
            raise ValueError(f"Escalate case missing trigger: {entry['case_id']}")
        if decision == "request_document" and not entry.get("missing"):
            raise ValueError(f"Request-document case missing missing key: {entry['case_id']}")
    return True


def is_negative_case(entry: dict) -> bool:
    return entry.get("expected_decision") != "approve_in_principle"


def get_negative_case_ids(entries: list[dict] | None = None):
    source = entries if entries is not None else load_expected_outcomes()
    return [entry["case_id"] for entry in source if is_negative_case(entry)]


def iter_expected_outcomes(entries: list[dict] | None = None, *, case_ids: list[str] | None = None):
    source = entries if entries is not None else load_expected_outcomes()
    wanted = set(case_ids) if case_ids is not None else None
    for entry in source:
        if wanted is not None and entry["case_id"] not in wanted:
            continue
        yield entry


def build_judgement_items(records: list[dict]):
    return [
        {
            "case_id": record.get("case_id"),
            "trial": record.get("trial"),
            "expected_decision": record.get("expected_decision"),
            "passed": record.get("passed"),
            "decision": record.get("decision"),
            "trigger": record.get("trigger"),
            "missing_item": record.get("missing_item"),
        }
        for record in records
    ]
