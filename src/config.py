<<<<<<< HEAD
"""Shared configuration for controlled A2 experiments."""

BACKEND = "live"          # "scripted" or "live"
MODEL = "google/gemini-2.5-flash-lite"
BASE_URL = "https://openrouter.ai/api/v1"

STEP_CAP = 8
BUDGET_USD = 0.10
AUTONOMY = "confirm"          # "suggest" | "confirm" | "act"
PARALLEL_ENABLED = True
TOOL_SPEC_VERSION = "v2"      # "v1" | "v2"
USE_JSON_RESPONSE_FORMAT = True
LIVE_RETRIES = 3

# Update these to the actual list prices used for the model run.
PRICE_IN_PER_M = 0.10
PRICE_OUT_PER_M = 0.40
=======
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
>>>>>>> 5bd9f6e092f1512df28d8169c82e5b4e456af3a3
