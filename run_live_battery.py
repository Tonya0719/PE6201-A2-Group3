"""D5(b) live model battery.

Runs the SAME frozen evaluation set with the FINAL v2 tool interface while
changing only MODEL (and the corresponding price constants). D2(b) is kept in
run_d2b_comparison.py so the controlled interface experiment is not mixed with
the model-battery experiment.

Usage:
  python run_live_battery.py --dry-run
  python run_live_battery.py
  python run_live_battery.py --models openai/gpt-4o-mini

IMPORTANT: re-check provider prices immediately before the final live run and
record the verification date/source in the report. Prices below are recovered
from the later team snapshot and are therefore provisional until re-verified.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src import config
from src.harness import run_evaluation, summarize_results

ROOT = Path(__file__).resolve().parent
LIVE_DIR = ROOT / "results" / "live"  #change it

# Final seven-family battery. Use --models to run only one member's model.
MODELS = [
    ("openai/gpt-4o-mini", "cheap", "OpenAI"), #FANG XINYI
    ("amazon/nova-2-lite-v1", "mid", "Amazon"), #YANG YISHENG
    ("google/gemini-2.5-flash", "mid", "Google"), #PURI
    ("deepseek/deepseek-chat-v3.1", "cheap", "DeepSeek"), #ZHOU YIHAN
    ("meta-llama/llama-3.3-70b-instruct", "cheap", "Meta"),#JIAO YUXI
    ("mistralai/mistral-small-2603", "cheap", "Mistral"),#MA JIAN
    ("qwen/qwen3-30b-a3b-instruct-2507", "cheap", "Qwen"),  # WU YUSHAN
]

# Provisional recovered prices: (input USD/M tokens, output USD/M tokens).
MODEL_PRICES = {
    "openai/gpt-4o-mini": (0.15, 0.60),#FANG XINYI
    "amazon/nova-2-lite-v1": (0.30, 2.50),#YANG YISHENG
    "google/gemini-2.5-flash": (0.30, 2.50),#PURI
    "deepseek/deepseek-chat-v3.1": (0.25, 0.95),#ZHOU YIHAN
    "meta-llama/llama-3.3-70b-instruct": (0.10, 0.32),#JIAO YUXI
    "mistralai/mistral-small-2603": (0.15, 0.60),#MA JIAN
    "qwen/qwen3-30b-a3b-instruct-2507": (0.048, 0.19),  # WU YUSHAN
}

PER_MODEL_BUDGET_WARNING_USD = 3.00


def safe_name(model: str) -> str:
    return model.replace("/", "__").replace(".", "_")


def run_one_model(model: str, tool_spec_version: str = "v2", dry_run: bool = False):
    config.BACKEND = "scripted" if dry_run else "live"
    config.MODEL = model
    if model in MODEL_PRICES:
        config.PRICE_IN_PER_M, config.PRICE_OUT_PER_M = MODEL_PRICES[model]
    elif not dry_run:
        print(f"WARNING: no verified price entry for {model}; update MODEL_PRICES before using cost outputs.")

    def progress(p):
        print(
            f"\r  [{model} | {tool_spec_version}] {p['run_index']}/{p['total_runs']} "
            f"({p['case_id']} trial {p['trial']}/{p['trials_for_case']})",
            end="", flush=True,
        )

    records = run_evaluation(
        approved_for_write=True,
        parallel_enabled=config.PARALLEL_ENABLED,
        max_tool_calls_per_turn=config.MAX_TOOL_CALLS_PER_TURN,
        tool_spec_version=tool_spec_version,
        progress_callback=progress,
        progress_label=model,
    )
    print()
    return records, summarize_results(records)


def save(path: Path, payload: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_saved_live_summaries() -> dict:
    """Build the aggregate from all saved per-model live result files."""
    summaries = {}
    for path in sorted(LIVE_DIR.glob("*.json")):
        if path.name == "_all_models_summary.json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            model = payload["model"]
            summary = payload["summary"]
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            print(f"WARNING: skipping invalid live result {path.name}: {exc}")
            continue
        summaries[model] = {
            "tier": payload.get("tier"),
            "family": payload.get("family"),
            **summary,
        }
    return summaries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="Scripted backend; no key/network/cost.")
    ap.add_argument("--models", help="Comma-separated subset of MODELS.")
    args = ap.parse_args()

    models = MODELS
    if args.models:
        wanted = {m.strip() for m in args.models.split(",")}
        models = [m for m in MODELS if m[0] in wanted]
        if not models:
            print(f"No match for --models {args.models!r}")
            sys.exit(1)

    all_summaries = {}
    running_total_cost = 0.0
    for model, tier, family in models:
        print(f"\n--- {model} ({tier}, {family}) ---")
        try:
            records, summary = run_one_model(model, tool_spec_version="v2", dry_run=args.dry_run)
        except Exception as exc:
            print(f"FAILED: {type(exc).__name__}: {exc}")
            all_summaries[model] = {"tier": tier, "family": family, "error": str(exc)}
            continue

        save(LIVE_DIR / f"{safe_name(model)}.json", {
            "model": model,
            "tier": tier,
            "family": family,
            "tool_spec_version": "v2",
            "price_in_per_m": config.PRICE_IN_PER_M,
            "price_out_per_m": config.PRICE_OUT_PER_M,
            "summary": summary,
            "records": records,
        })
        all_summaries[model] = {"tier": tier, "family": family, **summary}
        running_total_cost += summary.get("api_cost", 0.0)
        print(
            f"pass={summary['pass_rate']:.3f} neg={summary.get('negative_pass_rate')} "
            f"cost=${summary.get('api_cost', 0.0):.4f} running=${running_total_cost:.4f}"
        )
        if not args.dry_run and summary.get("api_cost", 0.0) > PER_MODEL_BUDGET_WARNING_USD:
            print("WARNING: per-model spend exceeded the configured warning threshold.")

    # Preserve earlier completed models when one member runs only a subset.
    aggregate = all_summaries if args.dry_run else load_saved_live_summaries()
    aggregate_total_cost = sum(
        row.get("api_cost", 0.0)
        for row in aggregate.values()
        if "error" not in row
    )
    save(LIVE_DIR / "_all_models_summary.json", {
        "models": aggregate,
        "total_cost_usd": aggregate_total_cost,
        "backend_used": "scripted" if args.dry_run else "live",
        "tool_spec_version": "v2",
        "price_note": "Re-verify MODEL_PRICES before final submission.",
    })
    print(f"\nSaved D5(b) results to {LIVE_DIR}")


if __name__ == "__main__":
    main()
