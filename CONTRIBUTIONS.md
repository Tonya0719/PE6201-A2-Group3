# Contributions

## Team information

- **Team:** A-3, Section A
- **Problem:** A — Claims first-response agent
- **Repository:** https://github.com/Tonya0719/PE6201-A2-Group3
- **Allocation basis:** Team Declaration dated 4 September 2026

## Member contributions

| Member | Owned | Also contributed to |
|---|---|---|
| Dechasiripong Puri | Agent loop and tools; D1, D2(a), D2(c) | Evaluation cases; Gemini live battery; D7 failures; report/demo assembly |
| Fang Xinyi | Agent loop and tools; D1, D2(a), D2(c) | Evaluation cases; GPT-4o-mini live battery; Meta-Llama v1 pass; report/demo assembly |
| Zhou Yihan | Descriptors and guardrail layer; D2(b), D3 | Evaluation cases; DeepSeek live battery; report/demo assembly |
| Wu Yushan | Descriptors and guardrail layer; D2(b), D3 | Evaluation cases; Qwen live battery |
| Ma Jian | Evaluation harness and scripted run; D4, D5(a) | Evaluation cases; Mistral live battery |
| Jiao Yuxi | Evaluation harness and answer key; D4, D5(a) | Evaluation cases; Meta-Llama v2 live battery |
| Yang Yisheng | Cost model, sensitivity and ledger; D6 | Evaluation cases; Amazon Nova live battery |

## Shared work and evidence

Every member contributed labelled evaluation cases. The individual live-model runs, Meta-Llama v1 comparison, D7 failure work, and report/demo assembly responsibilities are recorded in the table above. The team jointly reviewed the final submission package and the eleven deterministic guardrail cases.

Key shared evidence is located at:

- `expected_outcomes_A.json` and `data_A/` — frozen labelled evaluation set and fixtures;
- `results_organized/D3_guardrails/` — eleven deterministic guardrail cases;
- `results_organized/D4_evaluation/` — deterministic and human judgement evidence;
- `results_organized/D5_model_battery/` — scripted baseline and seven-model live battery;
- `results_organized/D6_cost_model/` — cost model, four levers, sensitivity and break-even results;
- `results_organized/D7_failures/` — three-run reproductions of both documented failures.

## Repository-history note

The final repository was consolidated from several team working copies. Consequently, a single integration commit does not preserve the complete sequence of the work performed in those copies. This file records substantive ownership and points to the resulting repository artefacts; the team should retain its declaration, meeting records, earlier repository snapshots and experiment outputs as supporting evidence. This note does not replace or recreate Git history.
