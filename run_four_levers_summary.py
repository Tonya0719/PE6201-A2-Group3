"""D6: consolidate the four measured cost levers into one JSON summary.

Run AFTER final D2(b), D2(c), D5(b) and D6 cost-model outputs exist.
Writes: results/cost/four_levers_summary.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from src.tools import TOOL_SPECS_V2

ROOT = Path(__file__).resolve().parent


def lever1_tool_block_size():
    extra = """
6. NAME + SIGNATURE
check_hospital_panel(hospital_id: str)
WHAT: Report whether a hospital is on the panel network.
INPUT: hospital_id from get_claim.
RETURNS: {hospital_id, is_panel: bool}.
FAILS WHEN: hospital_id does not exist.
IRREVERSIBLE? No.

7. NAME + SIGNATURE
check_missing_documents(lines: list, attached_documents: list)
WHAT: Compare required documents against submitted documents.
INPUT: claim lines and attached_documents from get_claim.
RETURNS: {missing:[{procedure_code, document}]}.
FAILS WHEN: malformed line data.
IRREVERSIBLE? No.
"""
    current = math.ceil(len(TOOL_SPECS_V2) / 4)
    hypothetical = math.ceil((len(TOOL_SPECS_V2) + len(extra)) / 4)
    increase = hypothetical - current
    return {
        "attacks": "Linear base-prompt cost; descriptors are re-sent each model turn",
        "built_in": "D2(a) shortest defensible tool set",
        "actual_5_tool_spec_tokens_est": current,
        "hypothetical_7_tool_spec_tokens_est": hypothetical,
        "increase_tokens_per_turn_est": increase,
        "increase_pct": round(increase / current * 100, 1),
        "measurement_note": "model-agnostic chars/4 estimate, stated explicitly",
    }


def lever2_turn_count():
    d = json.loads((ROOT / "results" / "d2c_comparison.json").read_text(encoding="utf-8"))
    seq = d["sequential"]["summary"]
    batch = d["batched"]["summary"]
    return {
        "attacks": "Turn count / trajectory growth",
        "built_in": "D2(c) sequential vs batched",
        "sequential_model_calls": seq.get("model_calls"),
        "sequential_tool_turns": seq.get("tool_turns"),
        "sequential_input_tokens": seq.get("input_tokens"),
        "sequential_api_cost": seq.get("api_cost"),
        "batched_model_calls": batch.get("model_calls"),
        "batched_tool_turns": batch.get("tool_turns"),
        "batched_input_tokens": batch.get("input_tokens"),
        "batched_api_cost": batch.get("api_cost"),
        "pass_rate_unchanged": seq.get("pass_rate") == batch.get("pass_rate"),
    }


def lever3_observation_size():
    d = json.loads((ROOT / "results" / "experiments" / "d2b_v1_vs_v2.json").read_text(encoding="utf-8"))
    v1, v2 = d["v1"], d["v2"]
    return {
        "attacks": "Observation size compounds because observations are re-sent on later turns",
        "built_in": "D2(b) get_preauthorisation interface rewrite",
        "v1_avg_estimated_return_tokens_per_call": v1["tool_return_stats"].get("avg_estimated_tokens_per_call"),
        "v2_avg_estimated_return_tokens_per_call": v2["tool_return_stats"].get("avg_estimated_tokens_per_call"),
        "v1_pass_rate": v1["summary"].get("pass_rate"),
        "v2_pass_rate": v2["summary"].get("pass_rate"),
        "v1_guardrails_passed": v1["guardrails"].get("passed"),
        "v2_guardrails_passed": v2["guardrails"].get("passed"),
        "measurement_note": v1["tool_return_stats"].get("measurement_method"),
    }


def lever4_success_rate():
    d = json.loads((ROOT / "results" / "cost" / "d6_cost_model_results.json").read_text(encoding="utf-8"))
    best = min(d["per_model"], key=lambda m: m["cost_per_successful_task"])
    return {
        "attacks": "Layer-2 expected failure cost",
        "built_in": "D4/D5(b) measured success rate",
        "best_model": best["model"],
        "best_model_pass_rate": best["pass_rate"],
        "best_model_variable_cost_per_run": best["variable_cost_per_run"],
        "best_model_expected_failure_cost": best["layer2_expected_failure_cost"],
        "best_model_cost_per_successful_task": best["cost_per_successful_task"],
        "break_even": d.get("break_even"),
    }


def main():
    summary = {
        "lever_1_tool_block_size": lever1_tool_block_size(),
        "lever_2_turn_count": lever2_turn_count(),
        "lever_3_observation_size": lever3_observation_size(),
        "lever_4_success_rate": lever4_success_rate(),
    }
    for name, data in summary.items():
        print(f"\n=== {name} ===")
        for k, v in data.items():
            print(f"  {k}: {v}")
    out = ROOT / "results" / "cost" / "four_levers_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
