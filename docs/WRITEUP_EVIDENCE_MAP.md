# A2 Write-up / Evidence Map

Use this as the operational checklist for every number or claim that may appear in the report, self-appraisal, or demo.

| Requirement / analysis | What it establishes | Run this | Official output to inspect | Where it feeds the write-up | Current state |
|---|---|---|---|---|---|
| D0(a) Why Agent / Rung 7 | Variable steps, fast ground truth, governance cliff | No run; review design | `docs/D0_why_agent.md` | Section 1 | Draft exists; align wording to final code |
| D0(b) compounding reliability | `s = P^(1/T)` diagnostic | After final model results, calculate from chosen model's pass rate P and median T | `results/live/<model>.json` | Section 1 | Historical values recovered; recalc after final battery |
| D0(c) What Good Looks Like | Exactly five pre-build criteria | No run | `docs/D0_why_agent.md` + Git history | Section 1 | Verify final text has exactly five |
| D2(a) shortest tool set | Why five agent tools; why helpers are not tools | No model run | `src/tools.py`, `docs/design_notes.md` | Section 2 | Code supports this; final 3-question table still needs prose polish |
| D2(b) V1→V2 controlled rewrite | One tool interface rewrite only | `python run_d2b_comparison.py --dry-run` first; after eval freeze run `python run_d2b_comparison.py` | `results/experiments/d2b_v1_vs_v2.json` and `.md` | Section 2 + D6 observation-size lever | **Code complete**; paid final run pending |
| D2(b) target tool | `get_preauthorisation` only; all other descriptors fixed | inspect code | `src/tools.py`: `_PREAUTH_V1`, `_PREAUTH_V2`, `_execute_one_tool` | Section 2 | Complete |
| D2(b) return tokens/call | Whether V2 observation is smaller | generated automatically by D2(b) runner | `v1/v2.tool_return_stats` in D2(b) JSON | Section 2 / D6 | Dry-run currently shows V1 ~44.7 vs V2 ~27.5 estimated tokens/call on provisional eval |
| D2(b) safety regression | Guardrail cases passed under each label | D2(b) runner reruns `run_guardrails.py` | D2(b) JSON `guardrails`; `results/guardrails/checklist.json` | Section 2 | 11/11 current deterministic checklist |
| D2(c) sequential vs batched | Turn reduction without correctness loss | scripted plumbing: `python run_d2c.py --backend scripted --no-progress`; final measured tokens/cost: `python run_d2c.py --backend live --model <chosen-model> --no-progress` | `results/d2c_comparison.json`, `results/d2c_report.md` | Section 2 + D6 turn lever | Code complete; final live comparison should be after eval freeze |
| D2(c) dependency rule | Which calls may batch | no extra run | D2(c) report + `src/harness.py` | Section 2 | Encoded in runner/report |
| D3(a) hard controls | step cap, budget, dedupe, autonomy gate (+ extra poka-yokes) | `python run_guardrails.py` | `results/guardrails/checklist.json` | Section 2 / safety | 11/11 current |
| D3(b) hostile cases | ≥3 hostile/free-text guardrail tests | `python run_guardrails.py` | same checklist JSON | Section 3 / evidence | 3 hostile cases present |
| D4 fixture integrity | JSON joins are valid | `python make_fixtures_A.py` then `python check_my_data.py` | terminal; generated `data_A/*.json` | Methods / appendix | 40-case provisional set hangs together |
| D4 deterministic evaluation | decision/trigger/missing/gated-action checks | `python run_eval.py` | `results/results.json` | Section 3 | Provisional set is 65/66 because CLM-9025 answer key conflicts with routing rule |
| D4 judgement check | reason/evidence quality; no unsupported facts | **Still needs final implementation/execution** (human review or different-family model judge) | create `results/judgement/` evidence | Section 3 | **Pending** |
| D5(a) reproducibility | no key/network scripted end-to-end | fresh clone → `python run_eval.py` | `results/results.json` | Section 3 / README | Infrastructure complete; rerun after final eval freeze |
| D5(b) live model battery | same eval/prompt/tools; model only changes | `python run_live_battery.py --dry-run`; final: `python run_live_battery.py` | `results/live/*.json`, `_all_models_summary.json` | Section 3 + Section 4 | Runner merged; historical six-model results preserved separately; final rerun depends on whether eval changes |
| Model trace inspection | Why a model failed | `python inspect_case.py --model <model> --case <case>` | terminal + saved live JSON | Section 3 / failure analysis | Utility merged |
| Failure clustering | List failing cases quickly | `python check_failures.py` | terminal | Section 3 | Utility merged |
| Reasoning-token diagnostic | Detect suspicious output-token inflation | `python analyze_reasoning.py` | terminal from final live files | Section 4 | Utility merged |
| D6 cost-to-serve | Layer 1 API + Layer 2 fallback + Layer 3 fixed; sensitivity + break-even | after final D5(b): `python run_cost_model.py` | `results/cost/d6_cost_model_results.json` | Section 4 | Runner merged; historical result preserved separately |
| D6 four levers | B, T, D, P before/after | after final D2(b), D2(c), D6: `python run_four_levers_summary.py` | `results/cost/four_levers_summary.json` | Section 4 | Runner repaired for current tool-spec implementation |
| D7 Failure 1 | working agent minus loop control → failure → restore | Current final runner still needs to be ported/frozen | target `results/failures/d7_failure1_loop_control.json` | Section 5 | Historical evidence recovered; current runner pending decision |
| D7 Failure 2 | different-layer real failure + before/after | Current final runner still needs to be ported to generalized intake guard | target `results/failures/d7_failure2_*.json` | Section 5 | Historical evidence recovered; code-port conflict pending decision |
| Submission hygiene | no secrets/conflicts/cache; default scripted | search before freeze | repo root / `.gitignore` | Submission quality | Freeze baseline retained |
| Contributions | truthful person→work mapping | manual | `CONTRIBUTIONS.md` + Git history | submission artifact | Still needs team completion |

## Recommended final execution order

After the eval set is truly frozen:

```bash
python make_fixtures_A.py
python check_my_data.py
python run_eval.py
python run_guardrails.py
python run_d2b_comparison.py --dry-run
python run_d2b_comparison.py              # paid, one fixed cheap model
python run_d2c_live.py --backend scripted --no-progress
python run_d2c_live.py --backend live --model <chosen-model> --no-progress
python run_live_battery.py --dry-run
python run_live_battery.py                # paid final model battery
python run_cost_model.py
python run_four_levers_summary.py
python analyze_reasoning.py
```

Then perform the D4 judgement check and the two final D7 reproductions, followed by a fresh-clone D5(a) run.
