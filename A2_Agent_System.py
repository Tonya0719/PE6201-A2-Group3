"""Local CLI runner for PE6201 A2 Group 3. Core logic stays in src/."""
from __future__ import annotations
import argparse, json
from src import config
from src.agent_core import run_agent
from src.evaluation import run_evaluation, summarize_results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--claim", default="CLM-8842")
    p.add_argument("--backend", choices=["scripted", "live"])
    p.add_argument("--model")
    p.add_argument("--tool-spec", choices=["v1", "v2"])
    p.add_argument("--sequential", action="store_true")
    p.add_argument("--approve-write", action="store_true")
    p.add_argument("--eval", action="store_true")
    p.add_argument("--debug-raw", action="store_true")
    args = p.parse_args()
    if args.backend: config.BACKEND = args.backend
    if args.model: config.MODEL = args.model
    if args.tool_spec: config.TOOL_SPEC_VERSION = args.tool_spec
    if args.sequential: config.PARALLEL_ENABLED = False

    print("\nPE6201 A2 — Problem A Agent")
    print(f"BACKEND            : {config.BACKEND}")
    print(f"MODEL              : {config.MODEL}")
    print(f"TOOL_SPEC_VERSION  : {config.TOOL_SPEC_VERSION}")
    print(f"PARALLEL_ENABLED   : {config.PARALLEL_ENABLED}")
    print(f"STEP_CAP           : {config.STEP_CAP}")
    print(f"BUDGET_USD         : {config.BUDGET_USD}")
    print(f"AUTONOMY           : {config.AUTONOMY}")
    print("=" * 60)

    if args.eval:
        records = run_evaluation(approved_for_write=args.approve_write, parallel_enabled=config.PARALLEL_ENABLED, tool_spec_version=config.TOOL_SPEC_VERSION)
        print(json.dumps(summarize_results(records), indent=2, ensure_ascii=False))
    else:
        result = run_agent(args.claim, approved_for_write=args.approve_write, debug_raw=args.debug_raw)
        print("\nRUN RESULT")
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
