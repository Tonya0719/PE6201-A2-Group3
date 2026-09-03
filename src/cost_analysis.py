"""D6 cost-to-serve analysis using measured evaluation results.

Purpose
-------
Turn measured model performance and token usage into business-level unit economics.
This module consumes result files; it should not run the Agent itself.

Expected inputs
---------------
- D4/D5 measured success rate and token counts.
- Model input/output prices.
- Problem A volume: 8,000 claims/month.
- Problem A human failure/fallback cost: US$7.60 per failed task.
- Assumptions for fixed monthly storage / infrastructure / monitoring / maintenance.
- D2 measurements for tool block size, turn count, and observation size.

Expected outputs
----------------
- Layer 1 per-task variable cost.
- Layer 2 expected human fallback cost.
- Layer 3 fixed monthly cost.
- Cost per successful task and monthly cost.
- Sensitivity analysis at success rate ±10 percentage points.
- Break-even success rate for cheap vs expensive model choices.
- Four-lever cost ledger: tool block B, turns T, observation size D, success rate P.

A2 mapping: D6; uses evidence from D2, D4, D5 and D7.
"""
