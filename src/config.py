"""Central configuration for A2.

Purpose
-------
Keep experiment-critical settings in one place so team members do not edit the
Agent implementation when changing a run condition.

Expected inputs / settings
--------------------------
- BACKEND: "scripted" or "live"
- MODEL: live model identifier. D5 model comparison should change this value only.
- BASE_URL / API-key environment-variable name for the live backend.
- STEP_CAP and BUDGET_USD for code guardrails.
- AUTONOMY: "suggest", "confirm", or "act".
- PARALLEL_ENABLED for the D2(c) controlled comparison.
- TOOL_SPEC_VERSION for the D2(b) v1→v2 controlled comparison.

Expected output
---------------
Configuration constants imported by the runner and shared modules. This module
should not run the Agent, call a model, or contain Problem A decision logic.

A2 mapping: D1, D2(b), D2(c), D3(a), D5(b).
"""
