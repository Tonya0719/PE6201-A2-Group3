# PE6201 A2 — Group 3 · Problem A

Single-agent hand-written ReAct system for health-insurance claim first response.

## Marker reproduction

```bash
pip install -r requirements.txt
python check_my_data.py
python run_eval.py
python run_guardrails.py
python demo_loop_failure_d7.py
python demo_prompt_compliance_failure.py
```

`run_eval.py` forces the deterministic scripted backend and needs no key or network. The submitted default in `src/config.py` is also `BACKEND = "scripted"`.

## Architecture

- One agent, one hand-written loop; no agent framework.
- Agent-visible tools: `get_claim`, `lookup_policy`, `check_coverage`, `get_preauthorisation`, `issue_decision_letter`.
- Deterministic helpers: exact duplicate check, hospital-panel lookup, required-document join, write de-duplication.
- `get_claim` runs first. Duplicate / hostile intake evidence is decisive and a runtime guard blocks further reads.
- `lookup_policy` then runs alone because later coverage checks need `policy_id`.
- Independent `check_coverage` calls may batch in one turn.
- `get_preauthorisation` is called only after a coverage observation says `requires_preauth=true`.
- `issue_decision_letter` is the only irreversible simulated write. The model must select it as an Action; the runtime applies the autonomy gate immediately before execution.
- `Final` is bookkeeping only after the gated action observation.

## Controlled experiments

- D2(b): `TOOL_SPEC_VERSION=v1|v2` changes only the `get_preauthorisation` descriptor and return shape; all other tool interfaces remain fixed.
- D2(c): `MAX_TOOL_CALLS_PER_TURN=1` is the sequential baseline; `None` allows independent multi-call turns.
- D3(b): `python run_guardrails.py` reproduces the eleven-case deterministic checklist.
- D5(a): `python run_eval.py` reproduces the scripted evaluation.
- D7: the two `demo_*failure*.py` runners reproduce the before/after failures without a key or network.

## Repository map

```text
run_eval.py              marker-facing scripted evaluation
run_guardrails.py        D3(b) deterministic checklist
run_d2c.py               D2(c) sequential vs batched runner
A2_Agent_System.py       developer/demo CLI
src/agent_core.py        hand-written ReAct loop
src/backends.py          scripted backend + the only vendor-aware live call
src/tools.py             tools, helpers, D2(b) descriptors
src/guardrails.py        hard runtime controls
src/harness.py           evaluation + D2(c) harness
src/evaluation.py        answer-key helpers
src/cost_analysis.py     D6 calculations
data_A/                   local fixture systems of record
expected_outcomes_A.json evaluation answer key
evals/                    guardrail/judgement materials
results/                  machine-generated evidence
docs/                     D0 and design notes
```

## Safety / secrets

Never commit `.env` or an API key. Live mode reads a key from environment/Colab secret and is only used for the measured D2(b)/D5(b) runs.

For a local live run only, create an untracked `.env` file in the repository root:

```dotenv
OPENROUTER_API_KEY=your_key_here
```

Do not commit `.env`, share it with teammates, or include it in the NTULearn submission ZIP. The marker-facing scripted commands above do not require `.env`, an API key, or network access.

## Evidence scope

The current frozen set contains 40 cases, including 10 negative cases, for 60 trials per model. `results/live/` contains evidence produced against that shape. Historical paid runs retained under `results/recovered_later_snapshot/` used a different negative-case shape and are archival only; do not combine them with the final-shape battery as though they were one controlled experiment.
