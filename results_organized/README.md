# Final Results Evidence Index

This directory contains the final evidence set, organised by the assignment's D-sections. JSON files are the primary machine-readable evidence. Markdown files explain the corresponding controlled experiment or review. The original pre-cleanup directory is preserved at `../results_organized_legacy_before_cleanup_20260919/`.

## D2 - Tool layer

| Requirement | Primary evidence | What it shows |
|---|---|---|
| D2(a), shortest defensible tool set | `D6_cost_model/D6_four_levers_summary.json` | Five visible tools versus the documented seven-tool candidate; repeated tool-block size estimate. |
| D2(b), descriptor/interface rewrite | `D2_tool_layer/D2b_descriptor_rewrite_live_results.json` | Controlled v1 versus v2 live comparison on the same model and cases. |
| D2(c), live parallel calling | `D2_tool_layer/D2c_parallel_calls_live_results.json` | Sequential versus batched tool calls, turns, tokens, pass rates and cost. |
| D2(c), deterministic correctness | `D2_tool_layer/D2c_parallel_calls_scripted_validation.json` | Both modes pass the same 60 scripted trials. |
| D2(c), output-token anomaly | `D2_tool_layer/D2c_output_token_outlier_analysis.md` | Separates the raw result from the outlier-exclusion sensitivity analysis. |

## D3 - Guardrails

`D3_guardrails/D3_guardrail_checklist_11_cases.json` contains the machine-readable results for eleven deterministic cases, including step cap, budget cap, action/write de-duplication, autonomy, evidence readiness, case binding, duplicate-intake blocking and three hostile-text cases. `D3_guardrails/D3_guardrail_checklist_summary.md` presents the same results as a readable table.

## D4 - Evaluation

The deterministic code checks are the same 60-trial records reproduced by D5(a), stored at `D5_model_battery/D5a_scripted_baseline_60_trials.json`. The judgement-check evidence is:

- `D4_evaluation/D4_human_judgement_results_12_cases.json`
- `D4_evaluation/D4_human_judgement_summary.md`
- `D4_evaluation/D4_judgement_prompt.txt`
- `D4_evaluation/D4_judgement_rubric.txt`

## D5 - Model battery

- `D5_model_battery/D5a_scripted_baseline_60_trials.json` - reproducible no-key baseline.
- `D5_model_battery/D5b_live_battery_7_models_summary.json` - comparison table for all seven live models.
- `D5_model_battery/D5b_model_*.json` - complete per-model trial records.

## D6 - Cost model

- `D6_cost_model/D6_three_layer_cost_model_7_models.json` - variable API cost, expected human fallback cost, monthly cost, sensitivity and break-even.
- `D6_cost_model/D6_four_levers_summary.json` - tool block, turn count, observation size and success-rate levers.
- `D6_cost_model/D6_four_levers_conclusions.md` - report-ready interpretation and limitations.

## D7 - Reproduced failures

- `D7_failures/D7_failure1_loop_control_three_runs.json` - working baseline, de-duplication removed, guard restored.
- `D7_failures/D7_failure2_prompt_compliance_three_runs.json` - guard disabled replay, guarded recovery, independent scripted-engine baseline.

## Figures

The `figures/` directory contains optional presentation figures. Figures are secondary; use the JSON files for quoted numbers.
