"""Consolidate final D2(a/b/c), D5(b), and D6 evidence into one audited JSON."""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

from src import config
from src.tools import TOOL_SPECS_V2

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required evidence file is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def pct_change(before, after):
    if before in (None, 0) or after is None:
        return None
    return (after - before) / before * 100.0


def pct_reduction(before, after):
    change = pct_change(before, after)
    return None if change is None else -change


def lever1_tool_block_size():
    extra = """
6. check_hospital_panel(hospital_id: str)
WHAT: Report whether a hospital is on the panel network.
INPUT: hospital_id from get_claim.
RETURNS: {hospital_id, is_panel: bool}.
FAILS WHEN: hospital_id does not exist.
IRREVERSIBLE? No.

7. check_missing_documents(lines: list, attached_documents: list)
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
        "actual_agent_visible_tools": 5,
        "hypothetical_agent_visible_tools": 7,
        "actual_5_tool_spec_tokens_est": current,
        "hypothetical_7_tool_spec_tokens_est": hypothetical,
        "increase_tokens_per_turn_est": increase,
        "increase_pct": round(increase / current * 100, 1),
        "measurement_note": "model-agnostic ceil(characters/4) estimate",
    }


def lever2_turn_count(d: dict):
    seq = d["sequential"]["summary"]
    bat = d["batched"]["summary"]
    neg_delta = None
    if seq.get("negative_pass_rate") is not None and bat.get("negative_pass_rate") is not None:
        neg_delta = (bat["negative_pass_rate"] - seq["negative_pass_rate"]) * 100
    fields = (
        "trials", "pass_rate", "negative_pass_rate", "model_calls", "tool_turns",
        "input_tokens", "output_tokens", "api_cost", "cap_hits"
    )
    bat_fields = fields + ("batched_turns", "max_tool_calls_in_one_turn")
    bat_records = d["batched"].get("records", [])
    bat_output_values = [r.get("output_tokens", 0) for r in bat_records]
    bat_output_median = statistics.median(bat_output_values) if bat_output_values else 0
    outlier_threshold = max(2000, bat_output_median * 10)
    output_outliers = [
        {
            "case_id": r.get("case_id"),
            "trial": r.get("trial"),
            "negative": r.get("negative"),
            "status": r.get("status"),
            "failure_reason": r.get("failure_reason"),
            "output_tokens": r.get("output_tokens", 0),
            "visible_response_characters": len(r.get("raw_model_response") or ""),
        }
        for r in bat_records
        if r.get("output_tokens", 0) > outlier_threshold
    ]
    excluded_output_tokens = sum(r["output_tokens"] for r in output_outliers)
    sensitivity_output_tokens = bat.get("output_tokens", 0) - excluded_output_tokens
    sensitivity_api_cost = (
        bat.get("api_cost", 0)
        - excluded_output_tokens * config.PRICE_OUT_PER_M / 1_000_000
    )
    return {
        "attacks": "Turn count / trajectory growth",
        "built_in": "D2(c) sequential vs batched",
        "evidence_file": "results/d2c_comparison.json",
        "backend": d.get("backend"),
        "model": d.get("model"),
        "tool_spec_version": d.get("tool_spec_version"),
        "formal_live_run": d.get("formal_live_run"),
        "sequential": {k: seq.get(k) for k in fields},
        "batched": {k: bat.get(k) for k in bat_fields},
        "deltas": {
            "pass_rate_percentage_points": (bat.get("pass_rate", 0) - seq.get("pass_rate", 0)) * 100,
            "negative_pass_rate_percentage_points": neg_delta,
            "model_calls_reduction": seq.get("model_calls", 0) - bat.get("model_calls", 0),
            "model_calls_reduction_pct": pct_reduction(seq.get("model_calls"), bat.get("model_calls")),
            "tool_turns_reduction": seq.get("tool_turns", 0) - bat.get("tool_turns", 0),
            "tool_turns_reduction_pct": pct_reduction(seq.get("tool_turns"), bat.get("tool_turns")),
            "input_token_reduction_pct": pct_reduction(seq.get("input_tokens"), bat.get("input_tokens")),
            "output_token_change_pct": pct_change(seq.get("output_tokens"), bat.get("output_tokens")),
            "api_cost_change_pct": pct_change(seq.get("api_cost"), bat.get("api_cost")),
        },
        "output_token_outlier_analysis": {
            "method": "Flag a batched record when output_tokens exceeds both 2,000 and 10 times the batched median.",
            "batched_median_output_tokens_per_record": bat_output_median,
            "flagged_records": output_outliers,
            "flagged_output_tokens": excluded_output_tokens,
            "flagged_share_of_batched_output_pct": (
                excluded_output_tokens / bat.get("output_tokens", 1) * 100
            ),
            "raw_measured_result": {
                "batched_output_tokens": bat.get("output_tokens"),
                "output_token_change_pct": pct_change(seq.get("output_tokens"), bat.get("output_tokens")),
                "batched_api_cost": bat.get("api_cost"),
                "api_cost_change_pct": pct_change(seq.get("api_cost"), bat.get("api_cost")),
            },
            "outlier_exclusion_sensitivity": {
                "batched_output_tokens": sensitivity_output_tokens,
                "output_token_change_pct": pct_change(seq.get("output_tokens"), sensitivity_output_tokens),
                "batched_api_cost": sensitivity_api_cost,
                "api_cost_change_pct": pct_change(seq.get("api_cost"), sensitivity_api_cost),
                "note": (
                    "Sensitivity only: subtracts the provider-reported output tokens of flagged records. "
                    "It does not replace the primary measured result."
                ),
            },
        },
        "interpretation": (
            "The primary run shows fewer model calls, tool turns, and input tokens. Its raw output-token and cost "
            "totals are dominated by one malformed JSON response with anomalous provider-reported completion usage. "
            "Report the raw result and the outlier-exclusion sensitivity separately: the robust conclusion is a "
            "turn/input-context reduction, while total-cost direction is not stable enough for a causal saving claim."
        ),
    }


def lever3_observation_size(d: dict):
    v1, v2 = d["v1"], d["v2"]
    s1, s2 = v1["summary"], v2["summary"]
    t1 = v1["tool_return_stats"].get("avg_estimated_tokens_per_call")
    t2 = v2["tool_return_stats"].get("avg_estimated_tokens_per_call")
    return {
        "attacks": "Observation size compounds because observations are re-sent on later turns",
        "built_in": "D2(b) get_preauthorisation interface rewrite",
        "evidence_file": "results/experiments/d2b_v1_vs_v2.json",
        "backend": d.get("backend"),
        "model": d.get("model"),
        "controlled_variable": d.get("controlled_variable"),
        "v1": {
            "trials": s1.get("trials"), "pass_rate": s1.get("pass_rate"),
            "negative_pass_rate": s1.get("negative_pass_rate"),
            "input_tokens": s1.get("input_tokens"), "output_tokens": s1.get("output_tokens"),
            "api_cost": s1.get("api_cost"), "avg_estimated_return_tokens_per_call": t1,
            "guardrails_passed": v1["guardrails"].get("passed"),
        },
        "v2": {
            "trials": s2.get("trials"), "pass_rate": s2.get("pass_rate"),
            "negative_pass_rate": s2.get("negative_pass_rate"),
            "input_tokens": s2.get("input_tokens"), "output_tokens": s2.get("output_tokens"),
            "api_cost": s2.get("api_cost"), "avg_estimated_return_tokens_per_call": t2,
            "guardrails_passed": v2["guardrails"].get("passed"),
        },
        "deltas": {
            "return_tokens_per_call_reduction_pct": pct_reduction(t1, t2),
            "pass_rate_percentage_points": (s2.get("pass_rate", 0) - s1.get("pass_rate", 0)) * 100,
            "negative_pass_rate_percentage_points": (s2.get("negative_pass_rate", 0) - s1.get("negative_pass_rate", 0)) * 100,
            "input_token_change_pct": pct_change(s1.get("input_tokens"), s2.get("input_tokens")),
            "output_token_change_pct": pct_change(s1.get("output_tokens"), s2.get("output_tokens")),
            "api_cost_change_pct": pct_change(s1.get("api_cost"), s2.get("api_cost")),
        },
        "measurement_note": v1["tool_return_stats"].get("measurement_method"),
        "interpretation": (
            "V2 reduced the target tool's return size and improved pass rate, while total run tokens and cost rose. "
            "Do not describe it as a total-cost saving."
        ),
    }


def lever4_success_rate(cost: dict, battery: dict):
    models = cost.get("per_model", [])
    if not models:
        raise ValueError("D6 cost output contains no models")
    best = min(models, key=lambda m: m["cost_per_successful_task"])
    reliable = max(models, key=lambda m: m["pass_rate"])
    battery_models = battery.get("models", {})
    return {
        "attacks": "Layer-2 expected human fallback cost",
        "built_in": "D4/D5(b) measured success rate",
        "evidence_files": ["results/live/_all_models_summary.json", "results/cost/d6_cost_model_results.json"],
        "model_count": len(battery_models),
        "families": sorted({m.get("family") for m in battery_models.values()}),
        "price_tiers": sorted({m.get("tier") for m in battery_models.values()}),
        "trials_per_model": sorted({m.get("trials") for m in battery_models.values()}),
        "best_cost_model": best["model"],
        "best_cost_model_pass_rate": best["pass_rate"],
        "best_cost_model_variable_cost_per_run": best["variable_cost_per_run"],
        "best_cost_model_expected_failure_cost": best["layer2_expected_failure_cost"],
        "best_cost_per_task": best["cost_per_successful_task"],
        "best_cost_model_monthly_cost": best["monthly_cost"],
        "most_reliable_model": reliable["model"],
        "most_reliable_pass_rate": reliable["pass_rate"],
        "assumptions": cost.get("assumptions"),
        "sensitivity_model": cost.get("sensitivity_model"),
        "sensitivity": cost.get("sensitivity"),
        "break_even": cost.get("break_even"),
        "per_model": models,
        "interpretation": "Expected human fallback cost dominates API cost; success rate is the largest lever.",
    }


def readiness(d2c: dict, d2b: dict, battery: dict, cost: dict) -> dict:
    bmodels = battery.get("models", {})
    checks = {
        "d2c_is_live": d2c.get("backend") == "live",
        "d2c_formal_flag": d2c.get("formal_live_run") is True,
        "d2c_equal_trial_counts": d2c["sequential"]["summary"].get("trials") == d2c["batched"]["summary"].get("trials"),
        "d2c_real_batching_observed": d2c["batched"]["summary"].get("batched_turns", 0) > 0,
        "d2b_is_live": d2b.get("backend") == "live",
        "d2b_equal_trial_counts": d2b["v1"]["summary"].get("trials") == d2b["v2"]["summary"].get("trials"),
        "d2b_guardrails_pass": bool(d2b["v1"]["guardrails"].get("all_passed") and d2b["v2"]["guardrails"].get("all_passed")),
        "battery_has_at_least_3_models": len(bmodels) >= 3,
        "battery_spans_at_least_2_tiers": len({m.get("tier") for m in bmodels.values()}) >= 2,
        "battery_uses_distinct_families": len({m.get("family") for m in bmodels.values()}) == len(bmodels),
        "battery_trials_are_consistent": len({m.get("trials") for m in bmodels.values()}) == 1,
        "cost_model_covers_battery": len(cost.get("per_model", [])) == len(bmodels),
        "model_prices_recorded": all(
            m.get("price_used") and all(v is not None for v in m["price_used"].values())
            for m in cost.get("per_model", [])
        ),
    }
    warnings = []
    bat_records = d2c["batched"].get("records", [])
    bat_outputs = [r.get("output_tokens", 0) for r in bat_records]
    bat_median = statistics.median(bat_outputs) if bat_outputs else 0
    d2c_outliers = [r for r in bat_records if r.get("output_tokens", 0) > max(2000, bat_median * 10)]
    if d2c_outliers:
        warnings.append(
            "D2(c): raw output-token and API-cost totals are dominated by a flagged malformed-response outlier; "
            "report raw and sensitivity results separately and do not claim a stable total-cost saving or penalty."
        )
    elif d2c["batched"]["summary"].get("api_cost", 0) > d2c["sequential"]["summary"].get("api_cost", 0):
        warnings.append("D2(c): batching reduced turns but increased measured API cost; do not claim a cost saving.")
    if d2b["v2"]["summary"].get("api_cost", 0) > d2b["v1"]["summary"].get("api_cost", 0):
        warnings.append("D2(b): V2 reduced target return size but increased total measured API cost.")
    if "re-verify" in (battery.get("price_note") or "").lower():
        warnings.append("Model prices are recorded but still marked provisional; add verification source and date to the report.")
    failed = [name for name, passed in checks.items() if not passed]
    submission_inputs_missing = []
    monthly_limit = getattr(config, "MONTHLY_LIMIT_PER_USER", None)
    if monthly_limit is None:
        submission_inputs_missing.append("monthly_limit_per_user")
    return {
        "all_required_evidence_ready": not failed,
        "submission_inputs_complete": not submission_inputs_missing,
        "checks": checks,
        "failed_checks": failed,
        "submission_inputs_missing": submission_inputs_missing,
        "operational_caps": {
            "step_cap": config.STEP_CAP,
            "per_run_budget_usd": config.BUDGET_USD,
            "monthly_limit_per_user": monthly_limit,
        },
        "warnings": warnings,
    }


def main():
    d2c = load_json(RESULTS / "d2c_comparison.json")
    d2b = load_json(RESULTS / "experiments" / "d2b_v1_vs_v2.json")
    battery = load_json(RESULTS / "live" / "_all_models_summary.json")
    cost = load_json(RESULTS / "cost" / "d6_cost_model_results.json")
    summary = {
        "evidence_readiness": readiness(d2c, d2b, battery, cost),
        "lever_1_tool_block_size": lever1_tool_block_size(),
        "lever_2_turn_count": lever2_turn_count(d2c),
        "lever_3_observation_size": lever3_observation_size(d2b),
        "lever_4_success_rate": lever4_success_rate(cost, battery),
    }
    for name, data in summary.items():
        print(f"\n=== {name} ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    out = RESULTS / "cost" / "four_levers_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved {out}")
    if not summary["evidence_readiness"]["all_required_evidence_ready"]:
        raise SystemExit("Summary generated, but required evidence checks failed.")


if __name__ == "__main__":
    main()
