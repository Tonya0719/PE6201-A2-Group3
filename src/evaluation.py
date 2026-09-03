"""Evaluation harness, graders, and run-level metrics.

Purpose
-------
Run the same isolated evaluation set against scripted or live backends and compare
Agent outputs with the committed Problem A answer key.

Expected inputs
---------------
- Cases from data_A / the extended fixture set.
- Ground truth from expected_outcomes_A.json.
- Agent runner from agent_core.
- Trial rules: ordinary case = 1 trial/model; negative case = 3 trials/model.
- Optional judgement prompt / judge for fields that cannot be exact-matched.

Expected outputs
----------------
Per-trial and aggregate results including:
- pass / fail
- overall pass rate
- negative-only pass rate
- check type (code or judgement)
- turns, token counts, cost
- median / worst turns and cap-hit information where needed
- machine-readable result files written under results/

Grading principles
------------------
- Clean state for every case/trial.
- Grade the outcome, not a required tool path.
- Correct outcome with the wrong single trigger is a failure.
- Use code checks for fixed-value fields; use judgement checks only where needed.

A2 mapping: D4, D5(a), D5(b); provides measured P and run data for D0(b), D6, D7.
"""
