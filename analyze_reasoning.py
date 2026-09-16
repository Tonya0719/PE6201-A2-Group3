"""
D6 diagnostic: detect reasoning-mode cost inflation.

METHOD (straight from the brief): a model doing hidden "thinking" before
answering bills those tokens as ordinary output tokens. The signal is
output_tokens PER MODEL CALL — a plain JSON action/final object should cost
roughly the same handful of tokens regardless of which model produced it.
If one model's output-per-call is 5-10x another's, that gap is thinking
tokens, not verbosity.

Reads every results/live/<model>.json saved by run_live_battery.py.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE_DIR = ROOT / "results" / "live"

# Flag a model as "likely reasoning mode" if its avg output tokens/call
# exceeds this multiple of the cheapest model's avg. Not a hard science —
# a diagnostic threshold, adjust after looking at your real numbers.
OUTLIER_MULTIPLE = 3.0


def analyze():
    files = [f for f in sorted(glob.glob(str(LIVE_DIR / "*.json")))
             if not f.endswith("_all_models_summary.json")]
    if not files:
        print(f"No results found in {LIVE_DIR}. Run run_live_battery.py first.")
        return

    rows = []
    for f in files:
        data = json.loads(Path(f).read_text(encoding="utf-8"))
        model = data["model"]
        records = data["records"]
        total_output = sum(r.get("output_tokens", 0) for r in records)
        total_calls = sum(r.get("model_calls", 0) for r in records)
        total_input = sum(r.get("input_tokens", 0) for r in records)
        total_cost = sum(r.get("cost", 0.0) for r in records)
        if total_calls == 0:
            continue
        rows.append({
            "model": model,
            "avg_output_per_call": total_output / total_calls,
            "avg_input_per_call": total_input / total_calls,
            "total_calls": total_calls,
            "total_output_tokens": total_output,
            "total_cost": total_cost,
            "pass_rate": data["summary"]["pass_rate"],
        })

    if not rows:
        print("No records with token data found — did you run against scripted (dry-run)? "
              "Token counts are only real under --live.")
        return

    # Exclude near-zero entries from baseline/ratio math — these are almost
    # always leftover scripted (dry-run) files or a model that failed every
    # call, not a genuine cheap/efficient model. Report them separately.
    MIN_MEANINGFUL_TOKENS = 1.0
    meaningful = [r for r in rows if r["avg_output_per_call"] >= MIN_MEANINGFUL_TOKENS]
    zero_or_broken = [r for r in rows if r["avg_output_per_call"] < MIN_MEANINGFUL_TOKENS]

    if zero_or_broken:
        print("Excluded from comparison (near-zero output tokens — likely scripted/dry-run "
              "leftovers or failed calls, not real live data):")
        for r in zero_or_broken:
            print(f"  - {r['model']}: avg_output_per_call={r['avg_output_per_call']:.2f}")
        print()

    if not meaningful:
        print("No models with meaningful token data to compare. Run the live battery for real first.")
        return

    rows = meaningful
    rows.sort(key=lambda r: r["avg_output_per_call"])
    baseline = rows[0]["avg_output_per_call"]

    print(f"\n{'MODEL':30} {'AVG_OUT/CALL':>13} {'AVG_IN/CALL':>13} {'x_BASELINE':>11} {'PASS_RATE':>10} {'TOTAL_COST':>11}")
    print("-" * 95)
    for r in rows:
        ratio = r["avg_output_per_call"] / baseline
        flag = "  <-- LIKELY REASONING MODE" if ratio >= OUTLIER_MULTIPLE else ""
        print(f"{r['model']:30} {r['avg_output_per_call']:13.1f} {r['avg_input_per_call']:13.1f} "
              f"{ratio:10.2f}x {r['pass_rate']:10.3f} ${r['total_cost']:10.4f}{flag}")

    print(f"\nBaseline (lowest avg output/call): {rows[0]['model']} at {baseline:.1f} tokens/call")
    print(f"Flagging threshold: {OUTLIER_MULTIPLE}x baseline")

    flagged = [r for r in rows if r["avg_output_per_call"] / baseline >= OUTLIER_MULTIPLE]
    if flagged:
        print(f"\n{len(flagged)} model(s) show output-token inflation consistent with hidden reasoning:")
        for r in flagged:
            print(f"  - {r['model']}: {r['avg_output_per_call']:.1f} tokens/call "
                  f"({r['avg_output_per_call']/baseline:.1f}x baseline)")
        print("\nImplication for D6: these models' cost-per-successful-task is inflated by")
        print("tokens the user never sees. Report the baseline (visible-output) comparison")
        print("separately from these, per the brief's guidance on reasoning models.")
    else:
        print("\nNo models show output-token inflation beyond the threshold — "
              "cost differences across your battery are driven by price-per-token, not reasoning mode.")


if __name__ == "__main__":
    analyze()