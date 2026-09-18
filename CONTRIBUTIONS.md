# Contributions

This allocation follows the team declaration dated 4 September 2026. The final consolidated repository was assembled from several team working copies, so its single import commit does not preserve the original per-member commit sequence. Contemporaneous meeting records, earlier repository snapshots and saved experiment files should be retained with the submission evidence.

| Member | Matriculation number | Primary ownership | D-sections | Live model / v1 pass | Concrete repository evidence |
|---|---|---|---|---|---|
| Dechasiripong Puri | G2609142E | Agent loop and tools | D1, D2(a), D2(c) | google/gemini-2.5-flash | `src/agent_core.py`, `src/tools.py`, `results/recovered_later_snapshot/live/google__gemini-2_5-flash.json` |
| Fang Xinyi | G2603842A | Agent loop and tools | D1, D2(a), D2(c) | openai/gpt-4o-mini | `src/agent_core.py`, `run_d2c_live.py`, `results/live/openai__gpt-4o-mini.json` |
| Ma Jian | G2606495E | Evaluation harness and scripted run | D4, D5(a) | mistralai/mistral-small-2603 | `src/harness.py`, `run_eval.py`, `results/recovered_later_snapshot/live/mistralai__mistral-small-2603.json` |
| Wu Yushan | G2604092L | Descriptors and guardrail layer | D2(b), D3 | v1 pass on meta-llama/llama-3.3-70b-instruct | `run_d2b_comparison.py`, `results/experiments/d2b_v1_vs_v2.json`, `run_guardrails.py` |
| Zhou Yihan | G2606574C | Descriptors and guardrail layer | D2(b), D3 | deepseek/deepseek-chat-v3.1 | `src/guardrails.py`, `results/recovered_later_snapshot/live/deepseek__deepseek-chat-v3_1.json` |
| Yang Yisheng | G2604043G | Cost model, ledger, sensitivity, report and demo assembly | D6, report sections 4 and 5 | amazon/nova-2-lite-v1 | `src/cost_analysis.py`, `run_cost_model.py`, `results/recovered_later_snapshot/live/amazon__nova-2-lite-v1.json` |
| Jiao Yuxi | G2606617H | Evaluation harness and scripted run | D4, D5(a) | meta-llama/llama-3.3-70b-instruct | `src/evaluation.py`, `expected_outcomes_A.json`, `results/recovered_later_snapshot/live/meta-llama__llama-3_3-70b-instruct.json` |

Every member contributed evaluation cases. The individual case-ID allocation was not preserved in the consolidated copy and must be supported by the team's original meeting notes or earlier working repositories if requested.
