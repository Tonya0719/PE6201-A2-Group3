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
