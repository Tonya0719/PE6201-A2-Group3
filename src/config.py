"""Central configuration for controlled PE6201 A2 experiments."""

# D5(a): submitted default must be scripted, deterministic, no network, no key.
BACKEND = "scripted"          # "scripted" | "live"
MODEL = "google/gemini-2.5-flash-lite"
BASE_URL = "https://openrouter.ai/api/v1"

# Hard code-layer controls (D3(a)).
STEP_CAP = 8
BUDGET_USD = 0.10
AUTONOMY = "confirm"          # "suggest" | "confirm" | "act"

# Controlled-experiment switches.
PARALLEL_ENABLED = True
MAX_TOOL_CALLS_PER_TURN = None  # None = batched; 1 = D2(c) sequential baseline
TOOL_SPEC_VERSION = "v2"       # "v1" | "v2"; D2(b) changes one tool interface only

USE_JSON_RESPONSE_FORMAT = True
LIVE_RETRIES = 3

# Replace only when running a live model whose list prices differ.
PRICE_IN_PER_M = 0.10
PRICE_OUT_PER_M = 0.40
