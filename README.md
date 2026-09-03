# PE6201 A2 — Applied AI System · Problem A

This repository is the team workspace for **PE6201 Assignment 2, Problem A: health-insurance claim first response**.

## Repository purpose

The project will implement and evaluate a **single-agent ReAct system** that reads a claim, queries local systems of record through tools, and produces one of three outcomes:

- `approve_in_principle`
- `request_document`
- `escalate`

The gated action is represented only as a **local structured record**. No real decision letter, email, database server, or external system integration is required.

## Design principles

- One Agent, one control loop.
- The Agent decides the next step from tool observations; business paths are not hard-coded as a fixed workflow.
- Scripted and live backends use the same Agent loop.
- Live model comparison changes the `MODEL` setting only; the eval set, prompt, tools, and loop remain fixed.
- Tools return facts from systems of record; the Agent reasons over those facts.
- Code guardrails protect the irreversible write: step cap, budget ceiling, action de-duplication, and an autonomy gate.
- Evaluation grades outcomes against the answer key and keeps each case isolated.
- Results used in the report should come from reproducible runs, not hand-entered numbers.

## Main files

- `A2_Agent_System.ipynb` — Colab-friendly runner and demonstration notebook.
- `src/` — shared implementation modules.
- `data_A/` — teacher-provided Problem A systems-of-record data.
- `make_fixtures_A.py`, `check_my_data.py`, `expected_outcomes_A.json`, `data_dictionary.json` — teacher-provided fixture package kept at repo root so its original relative paths continue to work.
- `fixtures/` — reference documentation supplied by the teacher.
- `evals/` — guardrail checklist and optional judgement-grader prompt.
- `docs/` — D0 reasoning and team design log.
- `results/` — generated evidence for D2–D7.

## Current status

The repository is intentionally scaffolded before implementation. Files under `src/` currently contain interface notes only. Teacher-provided data and fixture files are preserved unchanged.

## Important data rule

Do not edit or delete shipped records. Add new cases through the `EXTRA_*` sections in `make_fixtures_A.py`, regenerate the JSON, extend `expected_outcomes_A.json` by hand, and run `check_my_data.py` after every data change.

## Suggested team split

For a **6-person team**, a practical ownership model is:

| People | Primary responsibility | Main files |
|---|---|---|
| A + B | Agent loop / parallel tools | `src/agent_core.py` |
| C | Tools / descriptors | `src/tools.py` |
| D | Guardrails | `src/guardrails.py` + `evals/guardrail_cases.json` |
| E + F | Evaluation / scripted harness | `src/evaluation.py` |
| One person also owns | Cost model | `src/cost_analysis.py` |
| Everyone | Evaluation cases | `make_fixtures_A.py` + `expected_outcomes_A.json` |
| Everyone | Live battery | Do **not** change core code; only change `MODEL` / run the notebook |
| D7 collaboration | Loop owner + Tool/Guardrail owner | Reproduce failures from the working agent; do **not** create a separate `bad_agent` |

If there are **7 team members**, D6 / the cost model can be owned by one person independently.

The main collaboration principle is that **ownership boundaries should follow code boundaries**. Team members should avoid editing another workstream's core file unless the change is agreed first. Shared experiments should reuse the same Agent loop and evaluation harness so that model, descriptor, parallelisation, and failure comparisons change only the intended variable.
