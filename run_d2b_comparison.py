"""D2(b) controlled one-tool descriptor + return-shape rewrite.

CONTROLLED VARIABLE
-------------------
Only get_preauthorisation changes between v1 and v2.

The other four tool descriptors and implementations are identical between
versions. The underlying preauthorisation data lookup is also identical.

V1 is deliberately verbose/redundant:
- generic descriptor;
- repeats member_id and procedure_code inside every matching record.

V2 is compact and dependency-aware:
- descriptor states that it is called only after check_coverage returns
  requires_preauth=true;
- returns only procedure_code plus the preauthorisation id and validity windows.

The script reports, for BOTH versions:
- evaluation pass rate on the same frozen eval set;
- negative pass rate;
- live model input/output tokens and API cost;
- total tool-spec size;
- target get_preauthorisation descriptor size;
- get_preauthorisation return size per call;
- D3 deterministic guardrail cases passed.

Tool-return and descriptor token counts are transparent model-agnostic estimates:
    ceil(character count / 4)

Provider-reported input/output tokens remain the authoritative API usage numbers.

Usage:
    python run_d2b_comparison.py --dry-run
    python run_d2b_comparison.py
    python run_d2b_comparison.py --model meta-llama/llama-3.3-70b-instruct
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

from run_live_battery import MODEL_PRICES, run_one_model
from src.tools import (
    TOOL_SPECS_V1,
    TOOL_SPECS_V2,
    get_preauth_tool_spec,
)


ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "results" / "experiments"

DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"
TARGET_TOOL = "get_preauthorisation"

UNCHANGED_TOOLS = [
    "get_claim",
    "lookup_policy",
    "check_coverage",
    "issue_decision_letter",
]


# =====================================================================
# Guardrail regression check
# =====================================================================

def _guardrail_summary() -> dict:
    """Run the deterministic D3(b) suite and return its saved summary."""

    subprocess.run(
        [
            sys.executable,
            str(ROOT / "run_guardrails.py"),
        ],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )

    path = ROOT / "results" / "guardrails" / "checklist.json"

    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    return {
        "cases": payload.get("cases"),
        "passed": payload.get("passed"),
        "all_passed": payload.get("all_passed"),
        "note": (
            "The D3 code guardrail suite is unchanged between v1 and v2; "
            "it is rerun as a regression check."
        ),
    }


# =====================================================================
# Tool-return measurement
# =====================================================================

def _tool_return_stats(
    records: list[dict],
    tool_name: str = TARGET_TOOL,
) -> dict:
    """Measure successful observations returned by the target tool."""

    sizes = []
    calls = 0

    for record in records:
        for step in record.get("tool_history", []):
            for obs in step.get("observations", []):

                if (
                    obs.get("tool") != tool_name
                    or not obs.get("ok")
                ):
                    continue

                calls += 1

                compact = json.dumps(
                    obs.get("result"),
                    ensure_ascii=False,
                    separators=(",", ":"),
                )

                chars = len(compact)

                sizes.append(
                    {
                        "chars": chars,
                        "estimated_tokens": math.ceil(chars / 4),
                    }
                )

    if not sizes:
        return {
            "calls": 0,
            "avg_chars_per_call": None,
            "median_chars_per_call": None,
            "avg_estimated_tokens_per_call": None,
            "median_estimated_tokens_per_call": None,
            "measurement_method": (
                "ceil(compact JSON character count / 4); "
                "transparent model-agnostic estimate"
            ),
        }

    return {
        "calls": calls,
        "avg_chars_per_call":
            sum(x["chars"] for x in sizes) / calls,
        "median_chars_per_call":
            statistics.median(
                x["chars"] for x in sizes
            ),
        "avg_estimated_tokens_per_call":
            sum(
                x["estimated_tokens"]
                for x in sizes
            ) / calls,
        "median_estimated_tokens_per_call":
            statistics.median(
                x["estimated_tokens"]
                for x in sizes
            ),
        "measurement_method": (
            "ceil(compact JSON character count / 4); "
            "transparent model-agnostic estimate"
        ),
    }


# =====================================================================
# Descriptor measurement
# =====================================================================

def _descriptor_stats(text: str) -> dict:
    """Return transparent size statistics for one descriptor text."""

    chars = len(text)

    return {
        "chars": chars,
        "estimated_tokens": math.ceil(chars / 4),
        "measurement_method": (
            "ceil(descriptor character count / 4); "
            "transparent model-agnostic estimate"
        ),
    }


def _descriptor_delta(
    v1_stats: dict,
    v2_stats: dict,
) -> dict:
    """Describe the V2-minus-V1 descriptor size change."""

    v1_chars = v1_stats["chars"]
    v2_chars = v2_stats["chars"]

    v1_tokens = v1_stats["estimated_tokens"]
    v2_tokens = v2_stats["estimated_tokens"]

    char_delta = v2_chars - v1_chars
    token_delta = v2_tokens - v1_tokens

    if v1_chars:
        char_percent = (
            char_delta / v1_chars
        ) * 100
    else:
        char_percent = None

    if v1_tokens:
        token_percent = (
            token_delta / v1_tokens
        ) * 100
    else:
        token_percent = None

    return {
        "chars_v2_minus_v1": char_delta,
        "estimated_tokens_v2_minus_v1": token_delta,
        "chars_percent_change": char_percent,
        "estimated_tokens_percent_change": token_percent,
    }


# =====================================================================
# Markdown report
# =====================================================================

def _write_report(
    payload: dict,
    path: Path,
):
    v1 = payload["v1"]
    v2 = payload["v2"]

    target_delta = payload["target_descriptor_delta"]

    lines = [
        "# D2(b) One-tool V1→V2 Controlled Rewrite",
        "",
        f"- Model held fixed: `{payload['model']}`",
        f"- Target tool: `{TARGET_TOOL}`",
        "- All other tool descriptors/implementations: unchanged",
        f"- Backend: `{payload['backend']}`",
        "",
        "## Main results",
        "",
        "| Metric | V1 | V2 |",
        "|---|---:|---:|",
        (
            f"| Eval pass rate | "
            f"{v1['summary'].get('pass_rate')} | "
            f"{v2['summary'].get('pass_rate')} |"
        ),
        (
            f"| Negative pass rate | "
            f"{v1['summary'].get('negative_pass_rate')} | "
            f"{v2['summary'].get('negative_pass_rate')} |"
        ),
        (
            f"| Model input tokens | "
            f"{v1['summary'].get('input_tokens')} | "
            f"{v2['summary'].get('input_tokens')} |"
        ),
        (
            f"| Model output tokens | "
            f"{v1['summary'].get('output_tokens')} | "
            f"{v2['summary'].get('output_tokens')} |"
        ),
        (
            f"| API cost | "
            f"{v1['summary'].get('api_cost')} | "
            f"{v2['summary'].get('api_cost')} |"
        ),
        (
            f"| Full tool-spec chars | "
            f"{v1['descriptor_stats']['chars']} | "
            f"{v2['descriptor_stats']['chars']} |"
        ),
        (
            f"| Full tool-spec est. tokens | "
            f"{v1['descriptor_stats']['estimated_tokens']} | "
            f"{v2['descriptor_stats']['estimated_tokens']} |"
        ),
        (
            f"| Target descriptor chars | "
            f"{v1['target_descriptor_stats']['chars']} | "
            f"{v2['target_descriptor_stats']['chars']} |"
        ),
        (
            f"| Target descriptor est. tokens | "
            f"{v1['target_descriptor_stats']['estimated_tokens']} | "
            f"{v2['target_descriptor_stats']['estimated_tokens']} |"
        ),
        (
            f"| Preauth calls observed | "
            f"{v1['tool_return_stats'].get('calls')} | "
            f"{v2['tool_return_stats'].get('calls')} |"
        ),
        (
            f"| Avg return chars/call | "
            f"{v1['tool_return_stats'].get('avg_chars_per_call')} | "
            f"{v2['tool_return_stats'].get('avg_chars_per_call')} |"
        ),
        (
            f"| Avg estimated return tokens/call | "
            f"{v1['tool_return_stats'].get('avg_estimated_tokens_per_call')} | "
            f"{v2['tool_return_stats'].get('avg_estimated_tokens_per_call')} |"
        ),
        (
            f"| Guardrail cases passed | "
            f"{v1['guardrails'].get('passed')}/{v1['guardrails'].get('cases')} | "
            f"{v2['guardrails'].get('passed')}/{v2['guardrails'].get('cases')} |"
        ),
        "",
        "## Controlled descriptor change",
        "",
        (
            f"- Target descriptor character change, V2−V1: "
            f"`{target_delta['chars_v2_minus_v1']}`"
        ),
        (
            f"- Target descriptor estimated-token change, V2−V1: "
            f"`{target_delta['estimated_tokens_v2_minus_v1']}`"
        ),
        (
            f"- Target descriptor character percentage change: "
            f"`{target_delta['chars_percent_change']}`"
        ),
        (
            f"- Target descriptor estimated-token percentage change: "
            f"`{target_delta['estimated_tokens_percent_change']}`"
        ),
        "",
        "## Measurement notes",
        "",
        (
            "Tool-return and descriptor token counts are approximations "
            "using `ceil(chars / 4)`."
        ),
        (
            "Provider-reported model input/output token counts are stored "
            "separately and should be treated as the authoritative API usage."
        ),
        (
            "Differences in total model tokens or API cost can also reflect "
            "different agent trajectories, even when the controlled interface "
            "change itself is smaller."
        ),
    ]

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


# =====================================================================
# Main
# =====================================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Hold this one model fixed for both versions.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Use scripted backend to validate plumbing "
            "before spending API credit."
        ),
    )

    args = parser.parse_args()

    if (
        args.model not in MODEL_PRICES
        and not args.dry_run
    ):
        raise SystemExit(
            f"No price configured for {args.model}; "
            "verify and add it to run_live_battery.py first."
        )

    print(
        f"D2(b) controlled comparison on {args.model}"
    )

    print(
        f"Only {TARGET_TOOL} changes; "
        "all other descriptors stay fixed.\n"
    )

    # -----------------------------------------------------------------
    # Descriptor measurement before the runs
    # -----------------------------------------------------------------

    target_v1_text = get_preauth_tool_spec("v1")
    target_v2_text = get_preauth_tool_spec("v2")

    full_v1_stats = _descriptor_stats(
        TOOL_SPECS_V1
    )

    full_v2_stats = _descriptor_stats(
        TOOL_SPECS_V2
    )

    target_v1_stats = _descriptor_stats(
        target_v1_text
    )

    target_v2_stats = _descriptor_stats(
        target_v2_text
    )

    target_delta = _descriptor_delta(
        target_v1_stats,
        target_v2_stats,
    )

    print("Descriptor audit:")
    print(
        "  Full tool specs:"
        f" V1={full_v1_stats['estimated_tokens']} est. tokens,"
        f" V2={full_v2_stats['estimated_tokens']} est. tokens"
    )
    print(
        f"  {TARGET_TOOL}:"
        f" V1={target_v1_stats['estimated_tokens']} est. tokens,"
        f" V2={target_v2_stats['estimated_tokens']} est. tokens"
    )
    print()

    # -----------------------------------------------------------------
    # Controlled live/scripted comparison
    # -----------------------------------------------------------------

    print("Running V1...")

    v1_records, v1_summary = run_one_model(
        args.model,
        tool_spec_version="v1",
        dry_run=args.dry_run,
    )

    print("Running V2...")

    v2_records, v2_summary = run_one_model(
        args.model,
        tool_spec_version="v2",
        dry_run=args.dry_run,
    )

    # -----------------------------------------------------------------
    # Same deterministic guardrail suite for both labels
    # -----------------------------------------------------------------

    g1 = _guardrail_summary()
    g2 = _guardrail_summary()

    # -----------------------------------------------------------------
    # Assemble experiment record
    # -----------------------------------------------------------------

    payload = {
        "experiment":
            "D2(b) one-tool descriptor and return-shape rewrite",

        "model":
            args.model,

        "backend":
            "scripted" if args.dry_run else "live",

        "controlled_variable":
            TARGET_TOOL,

        "unchanged_tools":
            UNCHANGED_TOOLS,

        "v1": {
            # Entire tool prompt block
            "descriptor_stats":
                full_v1_stats,

            # Only the controlled tool descriptor
            "target_descriptor_stats":
                target_v1_stats,

            "summary":
                v1_summary,

            "tool_return_stats":
                _tool_return_stats(v1_records),

            "guardrails":
                g1,

            "records":
                v1_records,
        },

        "v2": {
            "descriptor_stats":
                full_v2_stats,

            "target_descriptor_stats":
                target_v2_stats,

            "summary":
                v2_summary,

            "tool_return_stats":
                _tool_return_stats(v2_records),

            "guardrails":
                g2,

            "records":
                v2_records,
        },

        "target_descriptor_delta":
            target_delta,

        "interpretation_rule": (
            "Attribute differences only to the single "
            "get_preauthorisation interface rewrite; "
            "model, frozen eval set, loop, prompt outside "
            "tool descriptors, and guardrails are held fixed."
        ),
    }

    # -----------------------------------------------------------------
    # Save
    # -----------------------------------------------------------------

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = (
        OUT_DIR
        / "d2b_v1_vs_v2.json"
    )

    md_path = (
        OUT_DIR
        / "d2b_v1_vs_v2.md"
    )

    json_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    _write_report(
        payload,
        md_path,
    )

    # -----------------------------------------------------------------
    # Console summary
    # -----------------------------------------------------------------

    print()
    print(
        "Metric                              V1              V2"
    )

    print(
        f"pass_rate                           "
        f"{v1_summary.get('pass_rate')}   "
        f"{v2_summary.get('pass_rate')}"
    )

    print(
        f"negative_pass_rate                  "
        f"{v1_summary.get('negative_pass_rate')}   "
        f"{v2_summary.get('negative_pass_rate')}"
    )

    print(
        f"input_tokens                        "
        f"{v1_summary.get('input_tokens')}   "
        f"{v2_summary.get('input_tokens')}"
    )

    print(
        f"output_tokens                       "
        f"{v1_summary.get('output_tokens')}   "
        f"{v2_summary.get('output_tokens')}"
    )

    print(
        f"api_cost                            "
        f"{v1_summary.get('api_cost')}   "
        f"{v2_summary.get('api_cost')}"
    )

    print(
        f"full tool-spec tokens (est.)        "
        f"{full_v1_stats['estimated_tokens']}   "
        f"{full_v2_stats['estimated_tokens']}"
    )

    print(
        f"target descriptor tokens (est.)     "
        f"{target_v1_stats['estimated_tokens']}   "
        f"{target_v2_stats['estimated_tokens']}"
    )

    print(
        f"preauth calls                       "
        f"{payload['v1']['tool_return_stats']['calls']}   "
        f"{payload['v2']['tool_return_stats']['calls']}"
    )

    print(
        f"avg return tokens/call (est.)       "
        f"{payload['v1']['tool_return_stats']['avg_estimated_tokens_per_call']}   "
        f"{payload['v2']['tool_return_stats']['avg_estimated_tokens_per_call']}"
    )

    print(
        f"guardrails                          "
        f"{g1['passed']}/{g1['cases']}   "
        f"{g2['passed']}/{g2['cases']}"
    )

    print()
    print(
        "Target descriptor delta V2−V1:"
    )

    print(
        f"  chars: "
        f"{target_delta['chars_v2_minus_v1']}"
    )

    print(
        f"  estimated tokens: "
        f"{target_delta['estimated_tokens_v2_minus_v1']}"
    )

    print()
    print(
        f"Saved {json_path}"
    )

    print(
        f"Saved {md_path}"
    )


if __name__ == "__main__":
    main()