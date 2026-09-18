"""
Measure B and per-turn token growth for PE6201 D2(c).

This script does NOT modify production runtime behaviour.
It temporarily wraps backends.call_model so every live model call's
provider-reported token usage is recorded while run_agent() executes.

Output:
- B: first-turn provider input tokens
- T: number of model calls
- per-turn input/output tokens
- delta input tokens between adjacent turns
- average D
- actual total input/output tokens
- theoretical input using B*T + D*T*(T-1)/2
- approximation error

Results are saved automatically to:
results/experiments/measure_B_D_<case>_<model>.json
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from src import backends, config
from src.agent_core import run_agent
from src.tools import reset_outbox


# ============================================================
# CONFIG
# ============================================================

CLAIM_ID = "CLM-8842"

MODEL = "google/gemini-2.5-flash-lite"

TOOL_SPEC_VERSION = "v2"

APPROVED_FOR_WRITE = True

PARALLEL_ENABLED = True

MAX_TOOL_CALLS_PER_TURN = None


# ============================================================
# OUTPUT PATH
# ============================================================

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results" / "experiments"


def safe_name(text: str) -> str:
    return (
        text
        .replace("/", "__")
        .replace(".", "_")
        .replace(":", "_")
    )


OUTPUT_PATH = (
    RESULTS_DIR
    / f"measure_B_D_{CLAIM_ID}_{safe_name(MODEL)}.json"
)


# ============================================================
# SET LIVE CONFIG
# ============================================================

config.BACKEND = "live"
config.MODEL = MODEL

reset_outbox()


# ============================================================
# TEMPORARILY WRAP call_model()
# ============================================================

original_call_model = backends.call_model

usage_log = []


def measured_call_model(messages):
    result = original_call_model(messages)

    usage = result.get("usage", {})

    usage_log.append(
        {
            "turn": len(usage_log) + 1,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "message_count": len(messages),
        }
    )

    return result


backends.call_model = measured_call_model


# ============================================================
# RUN ONE REAL AGENT TRAJECTORY
# ============================================================

try:
    result = run_agent(
        CLAIM_ID,
        approved_for_write=APPROVED_FOR_WRITE,
        parallel_enabled=PARALLEL_ENABLED,
        max_tool_calls_per_turn=MAX_TOOL_CALLS_PER_TURN,
        tool_spec_version=TOOL_SPEC_VERSION,
    )

finally:
    # Always restore original function.
    backends.call_model = original_call_model


# ============================================================
# CALCULATE B, D, ACTUAL, THEORY
# ============================================================

if not usage_log:
    raise RuntimeError(
        "No live model usage was recorded."
    )


B = usage_log[0]["input_tokens"]

T = len(usage_log)

input_tokens_per_turn = [
    row["input_tokens"]
    for row in usage_log
]

output_tokens_per_turn = [
    row["output_tokens"]
    for row in usage_log
]

deltas = [
    input_tokens_per_turn[i]
    - input_tokens_per_turn[i - 1]
    for i in range(
        1,
        len(input_tokens_per_turn),
    )
]

D = mean(deltas) if deltas else 0.0

actual_total_input = sum(
    input_tokens_per_turn
)

actual_total_output = sum(
    output_tokens_per_turn
)

theoretical_total_input = (
    B * T
    + D * T * (T - 1) / 2
)

if actual_total_input:
    approximation_error_pct = (
        (
            theoretical_total_input
            - actual_total_input
        )
        / actual_total_input
        * 100
    )
else:
    approximation_error_pct = None


# Add delta to each turn record for easier inspection.
for i, row in enumerate(usage_log):
    if i == 0:
        row["delta_input_tokens"] = None
    else:
        row["delta_input_tokens"] = (
            row["input_tokens"]
            - usage_log[i - 1]["input_tokens"]
        )


# ============================================================
# BUILD SAVED RESULT
# ============================================================

saved_result = {
    "experiment": "D2(c) B and D measurement",

    "configuration": {
        "claim_id": CLAIM_ID,
        "model": MODEL,
        "tool_spec_version": TOOL_SPEC_VERSION,
        "backend": "live",
        "approved_for_write": APPROVED_FOR_WRITE,
        "parallel_enabled": PARALLEL_ENABLED,
        "max_tool_calls_per_turn":
            MAX_TOOL_CALLS_PER_TURN,
    },

    "agent_result": {
        "decision": result.get("decision"),
        "trigger": result.get("trigger"),
        "missing_item": result.get("missing_item"),
        "status": result.get("status"),
        "failure_reason":
            result.get("failure_reason"),
        "tool_turns":
            result.get("tool_turns"),
        "model_calls":
            result.get("model_calls"),
    },

    "derived_metrics": {
        "B_first_turn_input_tokens": B,
        "T_model_calls": T,
        "D_mean_input_growth_per_turn": D,

        "actual_total_input_tokens":
            actual_total_input,

        "actual_total_output_tokens":
            actual_total_output,

        "theoretical_total_input_tokens":
            theoretical_total_input,

        "approximation_error_pct":
            approximation_error_pct,
    },

    "input_deltas": deltas,

    "per_turn_usage": usage_log,

    "formula": (
        "B*T + D*T*(T-1)/2"
    ),

    "measurement_note": (
        "B is provider-reported input tokens on the first model call. "
        "D is the mean increase in provider-reported input tokens between "
        "consecutive model calls. Actual D2(c) token/cost comparisons should "
        "use provider-reported aggregate usage rather than this approximation."
    ),
}


# ============================================================
# SAVE JSON
# ============================================================

RESULTS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT_PATH.write_text(
    json.dumps(
        saved_result,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ============================================================
# PRINT REPORT
# ============================================================

print()
print("=" * 72)
print("PE6201 D2(c) B / D Measurement")
print("=" * 72)

print(f"Claim ID:           {CLAIM_ID}")
print(f"Model:              {MODEL}")
print(f"Tool spec:          {TOOL_SPEC_VERSION}")
print(f"Parallel enabled:   {PARALLEL_ENABLED}")
print(
    f"Max calls / turn:   "
    f"{MAX_TOOL_CALLS_PER_TURN}"
)

print()
print("Agent result")
print("-" * 72)

print(
    f"Decision:           "
    f"{result.get('decision')}"
)

print(
    f"Status:             "
    f"{result.get('status')}"
)

print(
    f"Model calls T:      {T}"
)

print(
    f"Tool turns:         "
    f"{result.get('tool_turns')}"
)

print()
print("Per-turn provider token usage")
print("-" * 72)

print(
    f"{'Turn':<8}"
    f"{'Input':>12}"
    f"{'Output':>12}"
    f"{'Δ Input':>14}"
    f"{'Messages':>12}"
)

for row in usage_log:
    delta = (
        "-"
        if row["delta_input_tokens"] is None
        else str(
            row["delta_input_tokens"]
        )
    )

    print(
        f"{row['turn']:<8}"
        f"{row['input_tokens']:>12}"
        f"{row['output_tokens']:>12}"
        f"{delta:>14}"
        f"{row['message_count']:>12}"
    )

print()
print("Derived values")
print("-" * 72)

print(
    f"B (first-turn input):        "
    f"{B:.2f} tokens"
)

print(
    f"T (model calls):             "
    f"{T}"
)

print(
    f"Average D (input growth):     "
    f"{D:.2f} tokens/turn"
)

print(
    f"Actual total input:           "
    f"{actual_total_input:.2f}"
)

print(
    f"Actual total output:          "
    f"{actual_total_output:.2f}"
)

print(
    "Theory B*T + D*T(T-1)/2:   "
    f"{theoretical_total_input:.2f}"
)

if approximation_error_pct is not None:
    print(
        "Theory vs actual error:       "
        f"{approximation_error_pct:+.2f}%"
    )

print()
print(
    f"Saved result to:\n{OUTPUT_PATH}"
)

print("=" * 72)