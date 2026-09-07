"""D2(c) entry point: sequential vs batched tool-call comparison.

Default run is scripted, uses no API key/network, prints a report table, and saves:
- results/d2c_comparison.json
- results/d2c_report.md
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
DEFAULT_JSON_PATH = RESULTS_DIR / "d2c_comparison.json"
DEFAULT_REPORT_PATH = RESULTS_DIR / "d2c_report.md"


def main():
    parser = argparse.ArgumentParser(description="Run D2(c) sequential-vs-batched comparison.")
    parser.add_argument("--backend", choices=["scripted", "live"], default="scripted")
    parser.add_argument("--case", action="append", dest="case_ids", help="Limit to one claim ID. Repeat for multiple IDs.")
    parser.add_argument("--tool-spec", choices=["v1", "v2"], default=config.TOOL_SPEC_VERSION)
    parser.add_argument("--model", help="Live model override.")
    parser.add_argument("--negative-trials", type=int, default=3)
    parser.add_argument("--ordinary-trials", type=int, default=1)
    parser.add_argument("--approve-write", action="store_true", default=True, help="Approve the local gated write. Default: true.")
    parser.add_argument("--hold-write", action="store_true", help="Run with the autonomy gate holding the write.")
    parser.add_argument("--no-progress", action="store_true")
    parser.add_argument("--json-path", default=str(DEFAULT_JSON_PATH))
    parser.add_argument("--report-path", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args()

    if args.model:
        config.MODEL = args.model

    comparison = run_d2c_comparison(
        case_ids=args.case_ids,
        backend=args.backend,
        approved_for_write=args.approve_write and not args.hold_write,
        tool_spec_version=args.tool_spec,
        negative_trials=args.negative_trials,
        ordinary_trials=args.ordinary_trials,
        progress=not args.no_progress,
    )

    print_d2c_report(comparison)
    json_path = save_d2c_comparison(comparison, args.json_path)
    report_path = write_d2c_report(comparison, args.report_path)
    print(f"\nSaved JSON evidence to {json_path}")
    print(f"Saved report summary to {report_path}")


if __name__ == "__main__":
    main()
