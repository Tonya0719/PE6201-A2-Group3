"""D2(c) controlled sequential-versus-batched comparison.

The formal experiment holds the model, evaluation set, V2 tool interface,
prompt, guardrails and write approval fixed. Only the maximum number of tool
calls allowed per model turn changes.
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

ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"


def main():
    parser = argparse.ArgumentParser(
        description="Run the controlled D2(c) sequential-versus-batched experiment."
    )
    parser.add_argument(
        "--backend",
        choices=["scripted", "live"],
        default="scripted",
        help="Scripted is the safe default; select live explicitly for formal token/cost evidence.",
    )
    parser.add_argument("--model", default=config.MODEL, help="One model held fixed in both conditions.")
    parser.add_argument("--case", action="append", dest="case_ids", help="Optional claim ID; repeat to select several.")
    parser.add_argument("--ordinary-trials", type=int, default=1)
    parser.add_argument("--negative-trials", type=int, default=3)
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--json-path", default=str(RESULTS_DIR / "d2c_comparison.json"))
    parser.add_argument("--report-path", default=str(RESULTS_DIR / "d2c_report.md"))
    args = parser.parse_args()

    if args.ordinary_trials < 1 or args.negative_trials < 1:
        raise SystemExit("Trial counts must be at least 1.")

    config.MODEL = args.model
    comparison = run_d2c_comparison(
        case_ids=args.case_ids,
        backend=args.backend,
        approved_for_write=True,
        tool_spec_version="v2",
        negative_trials=args.negative_trials,
        ordinary_trials=args.ordinary_trials,
        progress=not args.no_progress,
    )
    comparison["controlled_variable"] = (
        "MAX_TOOL_CALLS_PER_TURN only: sequential=1, batched=None"
    )
    comparison["formal_live_run"] = args.backend == "live"
    comparison["configuration"] = {
        "backend": args.backend,
        "model": args.model,
        "tool_spec_version": "v2",
        "ordinary_trials": args.ordinary_trials,
        "negative_trials": args.negative_trials,
        "case_ids": args.case_ids,
    }

    print_d2c_report(comparison)
    json_path = save_d2c_comparison(comparison, args.json_path)
    report_path = write_d2c_report(comparison, args.report_path)
    print(f"\nSaved JSON evidence to {json_path}")
    print(f"Saved report summary to {report_path}")
    if args.backend == "scripted":
        print("Scripted verification complete; live evidence requires --backend live.")


if __name__ == "__main__":
    main()
