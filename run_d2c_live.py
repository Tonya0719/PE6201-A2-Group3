"""D2(c) controlled sequential-vs-batched comparison.

FORMAL EXPERIMENT
-----------------
Hold fixed:
- model
- frozen eval set
- V2 tool interface
- prompt/runtime/guardrails
- write approval

Change only:
- Sequential: max 1 tool call per model turn
- Batched: multiple independent tool calls per model turn

Formal run uses the live backend.
Use --dry-run for scripted plumbing checks.

Outputs:
- results/d2c_comparison.json
- results/d2c_report.md

Usage:
    python run_d2c_live.py --dry-run
    python run_d2c_live.py
    python run_d2c_live.py --model meta-llama/llama-3.3-70b-instruct
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src import config
from src.harness import (
    print_d2c_report,
    run_d2c_comparison,
    save_d2c_comparison,
    write_d2c_report,
)


# =====================================================================
# Experiment configuration
# =====================================================================

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"

DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct"

TOOL_SPEC_VERSION = "v2"
APPROVED_FOR_WRITE = True

ORDINARY_TRIALS = 1
NEGATIVE_TRIALS = 3

JSON_PATH = RESULTS_DIR / "d2c_comparison.json"
REPORT_PATH = RESULTS_DIR / "d2c_report.md"


# =====================================================================
# Main
# =====================================================================

def main():

    parser = argparse.ArgumentParser(
        description="Run D2(c) sequential-vs-batched comparison."
    )

    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Hold this one live model fixed for both conditions.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use scripted backend for plumbing checks; no API/network.",
    )

    parser.add_argument(
        "--case",
        action="append",
        dest="case_ids",
        help="Run selected claim only. Repeat for multiple claim IDs.",
    )

    parser.add_argument(
        "--ordinary-trials",
        type=int,
        default=ORDINARY_TRIALS,
    )

    parser.add_argument(
        "--negative-trials",
        type=int,
        default=NEGATIVE_TRIALS,
    )

    parser.add_argument(
        "--no-progress",
        action="store_true",
    )

    args = parser.parse_args()

    if args.ordinary_trials < 1:
        raise SystemExit("--ordinary-trials must be >= 1.")

    if args.negative_trials < 1:
        raise SystemExit("--negative-trials must be >= 1.")

    # -----------------------------------------------------------------
    # Resolve fixed experiment configuration
    # -----------------------------------------------------------------

    backend = "scripted" if args.dry_run else "live"

    config.BACKEND = backend
    config.MODEL = args.model
    config.TOOL_SPEC_VERSION = TOOL_SPEC_VERSION

    print("D2(c) sequential vs batched comparison")
    print(f"BACKEND     {backend}")
    print(f"MODEL       {args.model}")
    print(f"TOOL_SPEC   {TOOL_SPEC_VERSION}")
    print(f"PARALLEL    sequential vs batched")
    print(f"WRITE       approved")
    print(
        f"TRIALS      ordinary={args.ordinary_trials}, "
        f"negative={args.negative_trials}"
    )

    if args.case_ids:
        print(f"CASES       {', '.join(args.case_ids)}")
    else:
        print("CASES       full frozen eval set")

    print()

    # -----------------------------------------------------------------
    # Controlled D2(c) experiment
    # -----------------------------------------------------------------

    comparison = run_d2c_comparison(
        case_ids=args.case_ids,
        backend=backend,
        approved_for_write=APPROVED_FOR_WRITE,
        tool_spec_version=TOOL_SPEC_VERSION,
        negative_trials=args.negative_trials,
        ordinary_trials=args.ordinary_trials,
        progress=not args.no_progress,
    )

    # -----------------------------------------------------------------
    # Save experiment metadata
    # -----------------------------------------------------------------

    if isinstance(comparison, dict):
        comparison["experiment"] = (
            "D2(c) sequential vs batched tool-call comparison"
        )

        comparison["configuration"] = {
            "backend": backend,
            "model": args.model,
            "tool_spec_version": TOOL_SPEC_VERSION,
            "approved_for_write": APPROVED_FOR_WRITE,
            "ordinary_trials": args.ordinary_trials,
            "negative_trials": args.negative_trials,
            "case_ids": args.case_ids,
        }

        comparison["controlled_variable"] = (
            "tool-call strategy only: sequential vs batched"
        )

        comparison["formal_live_run"] = not args.dry_run

    # -----------------------------------------------------------------
    # Report
    # -----------------------------------------------------------------

    print_d2c_report(comparison)

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    json_path = save_d2c_comparison(
        comparison,
        JSON_PATH,
    )

    report_path = write_d2c_report(
        comparison,
        REPORT_PATH,
    )

    print()
    print(f"Saved {json_path}")
    print(f"Saved {report_path}")

    if args.dry_run:
        print(
            "\nDry-run only: use a live run for the formal "
            "D2(c) turns/tokens/cost/correctness evidence."
        )


if __name__ == "__main__":
    main()