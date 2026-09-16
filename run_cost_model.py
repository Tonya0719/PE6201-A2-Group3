"""
D6 — cost-to-serve runner

Reads your ALREADY-SAVED results (results/live/*.json from the FINAL run_live_battery.py run) and produces the actual D6
deliverable: cost per successful task per model, a sensitivity table at
+/-10 percentage points, and a break-even success rate between your cheapest
and your most reliable model.

Does NOT call any model or re-run anything. Pure arithmetic on numbers you
already measured, using src/cost_analysis.py's formulas.

Problem A defaults (from the brief, Appendix A):
    volume = 8,000 claims/month
    failure_cost = US$7.60 (claims assessor, 12 min @ US$38/hr)

USAGE
    python3 run_cost_model.py
    python3 run_cost_model.py --volume 8000 --failure-cost 7.60
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

from src.cost_analysis import build_cost_summary, sensitivity, break_even_success_rate

ROOT = Path(__file__).resolve().parent
LIVE_DIR = ROOT / "results" / "live"
OUT_DIR = ROOT / "results" / "cost"


def load_models():
    files = [f for f in sorted(glob.glob(str(LIVE_DIR / "*.json")))
             if not f.endswith("_all_models_summary.json")]
    models = []
    for f in files:
        data = json.loads(Path(f).read_text(encoding="utf-8"))
        summary = data["summary"]
        trials = summary.get("trials", 0)
        if trials == 0:
            continue
        variable_cost_per_run = summary.get("api_cost", 0.0) / trials
        models.append({
            "model": data["model"],
            "tier": data.get("tier"),
            "family": data.get("family"),
            "pass_rate": summary["pass_rate"],
            "variable_cost_per_run": variable_cost_per_run,
            "trials": trials,
            "price_used": data.get("price_used"),
        })
    return models


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume", type=int, default=8000, help="Monthly claim volume (Problem A default: 8000)")
    ap.add_argument("--failure-cost", type=float, default=7.60, help="Cost of one human escalation (Problem A default: $7.60)")
    ap.add_argument("--monthly-fixed", type=float, default=0.0, help="Layer 3 fixed monthly cost (storage/infra/monitoring)")
    args = ap.parse_args()

    models = load_models()
    if not models:
        print(f"No usable results found in {LIVE_DIR}. Run run_live_battery.py first, "
              f"then recompute_costs.py to fix pricing, then re-run this.")
        return

    if len(models) < 6:
        print(f"WARNING: only {len(models)} of 6 models have saved results. "
              f"Proceeding with what's available — re-run this once the rest finish.\n")

    print(f"Problem A defaults: volume={args.volume}/month, failure_cost=${args.failure_cost:.2f}\n")

    # --- Per-model cost summary (Layer 1 + Layer 2, monthly at volume) ---
    # Column width fits the longest model name (meta-llama/llama-3.3-70b-instruct = 33 chars).
    print(f"{'MODEL':35} {'PASS':>6} {'VAR_COST/RUN':>13} {'COST/SUCCESS':>13} {'MONTHLY':>12}")
    print("-" * 90)
    full_summaries = {}
    for m in models:
        s = build_cost_summary(
            success_rate=m["pass_rate"],
            variable_cost_per_run=m["variable_cost_per_run"],
            monthly_fixed_cost=args.monthly_fixed,
            monthly_volume=args.volume,
            failure_cost=args.failure_cost,
        )
        full_summaries[m["model"]] = s

    # Sort by cost-per-successful-task, cheapest overall first - not alphabetical,
    # so the recommended model is the first row a marker reads, not buried mid-table.
    ranked = sorted(models, key=lambda m: full_summaries[m["model"]]["cost_per_successful_task"])
    for m in ranked:
        s = full_summaries[m["model"]]
        print(f"{m['model']:35} {m['pass_rate']:6.3f} ${m['variable_cost_per_run']:12.5f} "
              f"${s['cost_per_successful_task']:12.5f} ${s['monthly_cost']:11.2f}")

    # --- Sensitivity, on the model with the best cost-per-successful-task ---
    best_model = min(models, key=lambda m: full_summaries[m["model"]]["cost_per_successful_task"])
    print(f"\n>> Cheapest per successful task: {best_model['model']} "
          f"(${full_summaries[best_model['model']]['cost_per_successful_task']:.5f}/success)")
    print(f"\nSensitivity (+/-10pp success rate) on best model by cost-per-success: {best_model['model']}")
    sens = sensitivity(
        success_rate=best_model["pass_rate"],
        variable_cost_per_run=best_model["variable_cost_per_run"],
        monthly_fixed_cost=args.monthly_fixed,
        monthly_volume=args.volume,
        failure_cost=args.failure_cost,
    )
    for label, s in sens.items():
        print(f"  {label:12} success_rate={s['success_rate']:.3f}  "
              f"cost_per_success=${s['cost_per_successful_task']:.5f}  monthly=${s['monthly_cost']:.2f}")

    # --- Break-even: cheapest-per-run model vs the most reliable model ---
    cheapest = min(models, key=lambda m: m["variable_cost_per_run"])
    most_reliable = max(models, key=lambda m: m["pass_rate"])
    if cheapest["model"] != most_reliable["model"]:
        expensive_all_in = full_summaries[most_reliable["model"]]["cost_per_successful_task"]
        be = break_even_success_rate(
            cheap_variable_cost=cheapest["variable_cost_per_run"],
            expensive_all_in_success_cost=expensive_all_in,
            failure_cost=args.failure_cost,
        )
        print(f"\nBreak-even: {cheapest['model']} (cheapest, ${cheapest['variable_cost_per_run']:.5f}/run, "
              f"{cheapest['pass_rate']:.3f} pass) vs {most_reliable['model']} "
              f"(most reliable, {most_reliable['pass_rate']:.3f} pass, "
              f"${expensive_all_in:.5f} cost/success)")
        print(f"  {cheapest['model']} would need a success rate of {be:.3f} to match "
              f"{most_reliable['model']}'s all-in cost.")
        print(f"  {cheapest['model']}'s ACTUAL measured success rate is {cheapest['pass_rate']:.3f}.")
        clears = cheapest["pass_rate"] >= be
        print(f"  Does it clear the break-even? {clears}")
    else:
        print(f"\n{cheapest['model']} is both the cheapest AND the most reliable — "
              f"no break-even trade-off to compute, it's a clean win either way.")
        be = None
        clears = None

    # --- Save everything ---
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "assumptions": {"volume": args.volume, "failure_cost": args.failure_cost,
                         "monthly_fixed_cost": args.monthly_fixed},
        "per_model": [{**m, **full_summaries[m["model"]]} for m in models],
        "sensitivity_model": best_model["model"],
        "sensitivity": sens,
        "break_even": {
            "cheapest_model": cheapest["model"],
            "most_reliable_model": most_reliable["model"],
            "break_even_success_rate": be,
            "cheapest_clears_break_even": clears,
        } if cheapest["model"] != most_reliable["model"] else None,
    }
    out_path = OUT_DIR / "d6_cost_model_results.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()