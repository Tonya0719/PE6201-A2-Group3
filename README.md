<<<<<<< HEAD
# PE6201 A2 — Group 3 · Problem A

This repository implements a **single-agent ReAct system** for the Problem A health-insurance claim first response task.

## Current design

The implementation is aligned to the team's D1/D2(a)/D2(c) design outline:

- **5 agent-visible tools:** `get_claim`, `lookup_policy`, `check_coverage`, `get_preauthorisation`, `issue_decision_letter`
- **4 internal helpers:** `check_duplicate`, `check_hospital_panel`, `check_missing_documents`, `already_decided`
- **Expected efficient paths:** 2 turns for duplicate/injection early exit; 3 turns for policy-level escalation; 4 turns for the full ordinary/ASK path.
- `lookup_policy` runs in its own turn because `check_coverage` requires its `policy_id`.
- Turn 3 batches `check_coverage × N` with `get_preauthorisation × M`. The preauth-required procedure codes are a static dependency map derived from the supplied `procedures.json` and placed in the system prompt.
- Hospital panel and missing-document checks are deterministic helpers, deferred until the line-verification stage.
- `issue_decision_letter` is the only gated write and only appends a local structured record.

These turn counts are **expected trajectories, not a hard-coded workflow**. `src/agent_core.py` owns one generic loop: model → Action(s) → real tool observations → model → … → Final.

## Important prompt / live-model hardening

Live testing exposed a failure where a model returned several JSON objects in one model turn and **invented policy/preauthorisation observations** instead of waiting for the runtime. The current prompt and parser therefore enforce:

1. one model turn = exactly one JSON object;
2. Action → stop and wait for real tool observations;
3. the model must never generate/simulate an Observation;
4. any fact not already returned by the runtime is unknown;
5. multiple independent calls are allowed only inside one `tool_calls` list;
6. OpenRouter JSON response mode is requested when enabled;
7. the parser rejects invalid/multiple JSON instead of silently salvaging fabricated traces.

## Repository structure

```text
PE6201-A2-Group3/
├── A2_Agent_System.ipynb       # Colab/demo runner
├── A2_Agent_System.py          # local CLI runner
├── README.md
├── CONTRIBUTIONS.md
├── requirements.txt
├── make_fixtures_A.py          # teacher-provided; keep shipped rows unchanged
├── check_my_data.py            # teacher-provided data-integrity checker
├── expected_outcomes_A.json    # answer key; extend for your own added cases
├── data_dictionary.json
├── data_A/                     # supplied Problem A systems of record
├── docs/
│   ├── D0_why_agent.md
│   └── design_notes.md
├── src/
│   ├── config.py
│   ├── tools.py
│   ├── agent_core.py
│   ├── guardrails.py
│   ├── evaluation.py
│   └── cost_analysis.py
├── evals/
└── results/
```

## Run locally

```bash
pip install -r requirements.txt
python check_my_data.py
python A2_Agent_System.py --claim CLM-8842 --approve-write
```

Default `BACKEND="scripted"` requires no API key. For live runs, set `BACKEND="live"` and use an OpenRouter key via environment variable, `.env`, or Colab Secret.

## D0–D7 ownership map

| Workstream | Main files | D sections |
|---|---|---|
| Agent loop / parallelisation (2 people) | `src/agent_core.py` | D1, D2(c), D7 Failure 1 |
| Tools / descriptors (1) | `src/tools.py` | D2(a), D2(b), D7 Failure 2 |
| Guardrails (1) | `src/guardrails.py`, `evals/guardrail_cases.json` | D3, D7 Failure 1 |
| Evaluation / scripted / live (2) | `src/evaluation.py` | D4, D5, D7 measurement |
| Cost (1) | `src/cost_analysis.py` | D6 |
| Everyone | fixture additions + live battery | D4, D5 |

**Team rule:** do not push directly to `main`; work on a branch and merge via PR.
=======
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
| C(probably with another)| Tools / descriptors | `src/tools.py` |
| D + E | Guardrails | `src/guardrails.py` + `evals/guardrail_cases.json` |
| F + G | Evaluation / scripted harness | `src/evaluation.py` |
| One person also owns | Cost model | `src/cost_analysis.py` |
| Everyone | Evaluation cases | `make_fixtures_A.py` + `expected_outcomes_A.json` |
| Everyone | Live battery | Do **not** change core code; only change `MODEL` / run the notebook |
| D7 collaboration(one main onwer) | Loop owner + Tool/Guardrail owner | Reproduce failures from the working agent; do **not** create a separate `bad_agent` |
|2|Report and demo assembly rotates sections 4 and 5|README.md、CONTRIBUTIONS.md、docs/D0_why_agent.md|

If there are **7 team members**, D6 / the cost model can be owned by one person independently.

The main collaboration principle is that **ownership boundaries should follow code boundaries**. Team members should avoid editing another workstream's core file unless the change is agreed first. Shared experiments should reuse the same Agent loop and evaluation harness so that model, descriptor, parallelisation, and failure comparisons change only the intended variable.
>>>>>>> 5bd9f6e092f1512df28d8169c82e5b4e456af3a3
