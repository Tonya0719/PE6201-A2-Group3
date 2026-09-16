# PE6201 A2 — Group 3 · Problem A

Single-agent hand-written ReAct system for health-insurance claim first response.

## Marker reproduction

```bash
pip install -r requirements.txt
python check_my_data.py
python run_eval.py
python run_guardrails.py
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
- D3(b): `python run_guardrails.py` reproduces the ten-case deterministic checklist.
- D5(a): `python run_eval.py` reproduces the scripted evaluation.

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

## Current working-state notes

This merged working tree restores the later snapshot's provisional 40-case eval set and experiment runners while retaining the stronger Freeze runtime controls. Before final submission, read:

- `docs/EVAL_SET_REVIEW.md` — where/how to edit and freeze the eval set;
- `docs/D2B_CONTROLLED_REWRITE.md` — the final one-tool D2(b) V1→V2 design;
- `docs/WRITEUP_EVIDENCE_MAP.md` — every experiment, command, and output path;
- `docs/MERGE_DECISIONS.md` — what was merged and which later-snapshot conflicts were deliberately not applied.

Recovered paid results from the later snapshot live under `results/recovered_later_snapshot/` and must not be confused with final evidence produced by the current merged commit.
