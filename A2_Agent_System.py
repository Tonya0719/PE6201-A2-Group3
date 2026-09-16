"""Local CLI runner for PE6201 A2 Group 3. Core logic stays in src/."""
from __future__ import annotations

import argparse
import json

from src import config
from src.agent_core import run_agent
from src.backends import get_openrouter_credit_balance
from src.harness import print_d2c_report, run_d2c_comparison, run_evaluation, summarize_results


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--claim", default="CLM-8842")
    p.add_argument("--backend", choices=["scripted", "live"])
    p.add_argument("--model")
    p.add_argument("--tool-spec", choices=["v1", "v2"])
    p.add_argument("--sequential", action="store_true", help="D2(c): execute at most one tool call per model turn.")
    p.add_argument("--d2c", action="store_true", help="Run D2(c) sequential-vs-batched comparison.")
    p.add_argument("--d2c-case", action="append", help="Limit D2(c) comparison to one claim ID. Repeat for multiple claims.")
    p.add_argument("--credits", action="store_true", help="Show OpenRouter account credits and remaining balance.")
    p.add_argument("--approve-write", action="store_true")
    p.add_argument("--eval", action="store_true")
    p.add_argument("--debug-raw", action="store_true")
    args = p.parse_args()

    if args.backend:
        config.BACKEND = args.backend
    if args.model:
        config.MODEL = args.model
    if args.tool_spec:
        config.TOOL_SPEC_VERSION = args.tool_spec
    if args.sequential:
        config.MAX_TOOL_CALLS_PER_TURN = 1

    print("\nPE6201 A2 - Problem A Agent")
    print(f"BACKEND                 : {config.BACKEND}")
    print(f"MODEL                   : {config.MODEL}")
    print(f"TOOL_SPEC_VERSION       : {config.TOOL_SPEC_VERSION}")
    print(f"PARALLEL_ENABLED        : {config.PARALLEL_ENABLED}")
    print(f"MAX_TOOL_CALLS_PER_TURN : {config.MAX_TOOL_CALLS_PER_TURN}")
    print(f"STEP_CAP                : {config.STEP_CAP}")
    print(f"BUDGET_USD              : {config.BUDGET_USD}")
    print(f"AUTONOMY                : {config.AUTONOMY}")
    print("=" * 60)

    if args.credits:
        balance = get_openrouter_credit_balance()
        print("\nOPENROUTER CREDITS")
        print(json.dumps(balance, indent=2, ensure_ascii=False))
    elif args.d2c:
        comparison = run_d2c_comparison(
            case_ids=args.d2c_case,
            backend=config.BACKEND,
            approved_for_write=args.approve_write,
            tool_spec_version=config.TOOL_SPEC_VERSION,
            progress=True,
        )
        print_d2c_report(comparison)
    elif args.eval:
        records = run_evaluation(
            approved_for_write=args.approve_write,
            parallel_enabled=config.PARALLEL_ENABLED,
            max_tool_calls_per_turn=config.MAX_TOOL_CALLS_PER_TURN,
            tool_spec_version=config.TOOL_SPEC_VERSION,
        )
        print(json.dumps(summarize_results(records), indent=2, ensure_ascii=False))
    else:
        result = run_agent(
            args.claim,
            approved_for_write=args.approve_write,
            max_tool_calls_per_turn=config.MAX_TOOL_CALLS_PER_TURN,
            debug_raw=args.debug_raw,
        )
        print("\nRUN RESULT")
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
