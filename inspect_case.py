"""
Browse the per-case results saved by run_live_battery.py.

MODES

1. List all cases for one model (pass/fail, decision, turns, cost):
   python3 inspect_case.py --model openai/gpt-4o-mini

2. Drill into ONE case for ONE model — full turn-by-turn trace:
   python3 inspect_case.py --model openai/gpt-4o-mini --case CLM-8894

3. Compare ONE case across every saved model:
   python3 inspect_case.py --case CLM-8894 --all-models

Reads from results/live/<model>.json, written by run_live_battery.py.
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LIVE_DIR = ROOT / "results" / "live"


def load_model_file(model: str) -> dict:
    safe = model.replace("/", "__").replace(".", "_")
    path = LIVE_DIR / f"{safe}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"No saved results for {model} at {path}. "
            f"Available: {[Path(p).stem for p in glob.glob(str(LIVE_DIR / '*.json'))]}"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def list_cases(model: str):
    data = load_model_file(model)
    records = data["records"]
    print(f"\n{model} — {data['summary']['trials']} trials, "
          f"pass_rate={data['summary']['pass_rate']:.3f}\n")
    print(f"{'CASE_ID':14} {'TRIAL':6} {'PASS':6} {'EXPECTED':22} {'GOT':22} {'TURNS':6} {'COST':>8}")
    print("-" * 90)
    for r in records:
        print(f"{r['case_id']:14} {r['trial']:<6} {'YES' if r['passed'] else 'NO':6} "
              f"{r['expected_decision']:22} {str(r.get('decision')):22} "
              f"{r.get('turns', '?'):<6} ${r.get('cost', 0.0):.4f}")


def show_case_detail(model: str, case_id: str, trial: int | None = None):
    data = load_model_file(model)
    matches = [r for r in data["records"] if r["case_id"] == case_id]
    if trial:
        matches = [r for r in matches if r["trial"] == trial]
    if not matches:
        print(f"No record found for {case_id} in {model} (trial={trial}).")
        return

    expected_rows = json.loads((ROOT / "expected_outcomes_A.json").read_text(encoding="utf-8"))
    expected = next((e for e in expected_rows if e["case_id"] == case_id), {})

    for r in matches:
        print(f"\n{'=' * 80}")
        print(f"{model} | {case_id} | trial {r['trial']}/{r.get('trials_for_case', '?')}")
        print(f"{'=' * 80}")
        print(f"Expected: {expected.get('expected_decision')}"
              + (f" (trigger={expected.get('trigger')})" if expected.get('expected_decision') == 'escalate' else "")
              + (f" (missing={expected.get('missing')})" if expected.get('expected_decision') == 'request_document' else ""))
        print(f"Got:      {r.get('decision')} "
              f"(trigger={r.get('trigger')}, missing_item={r.get('missing_item')})")
        print(f"PASSED:   {r['passed']}   | checks: {r.get('checks')}")
        print(f"Turns: {r.get('turns')} | tool_turns: {r.get('tool_turns')} | "
              f"model_calls: {r.get('model_calls')}")
        print(f"Tokens: in={r.get('input_tokens')} out={r.get('output_tokens')} "
              f"| cost=${r.get('cost', 0.0):.4f}")
        if r.get("guardrail_events"):
            print(f"Guardrail events: {r['guardrail_events']}")

        print("\n--- Turn-by-turn tool trace ---")
        for h in r.get("tool_history", []):
            calls = [c["name"] for c in h.get("tool_calls", [])]
            print(f"  Turn {h['turn']} (model_call {h.get('model_call')}): calls={calls}")
            for obs in h.get("observations", []):
                tool = obs.get("tool", obs.get("type", "?"))
                ok = obs.get("ok", "-")
                print(f"    -> {tool}: ok={ok}"
                      + (f" error={obs['error']}" if not ok and "error" in obs else ""))


def compare_across_models(case_id: str):
    files = sorted(glob.glob(str(LIVE_DIR / "*.json")))
    files = [f for f in files if not f.endswith("_all_models_summary.json")]
    print(f"\n{case_id} across all saved models:\n")
    print(f"{'MODEL':30} {'PASS':6} {'GOT':22} {'TURNS':6} {'COST':>8}")
    print("-" * 80)
    for f in files:
        data = json.loads(Path(f).read_text(encoding="utf-8"))
        model = data["model"]
        matches = [r for r in data["records"] if r["case_id"] == case_id and r["trial"] == 1]
        if not matches:
            print(f"{model:30} — no record for {case_id}")
            continue
        r = matches[0]
        print(f"{model:30} {'YES' if r['passed'] else 'NO':6} "
              f"{str(r.get('decision')):22} {r.get('turns', '?'):<6} ${r.get('cost', 0.0):.4f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="Model name, e.g. openai/gpt-4o-mini")
    ap.add_argument("--case", help="Case ID, e.g. CLM-8894")
    ap.add_argument("--trial", type=int, help="Specific trial number (for negative cases with 3 trials)")
    ap.add_argument("--all-models", action="store_true", help="Compare one case across every saved model")
    args = ap.parse_args()

    if args.all_models:
        if not args.case:
            print("--all-models requires --case CASE_ID")
            return
        compare_across_models(args.case)
    elif args.model and args.case:
        show_case_detail(args.model, args.case, args.trial)
    elif args.model:
        list_cases(args.model)
    else:
        print("Usage:\n"
              "  --model MODEL                      list all cases for a model\n"
              "  --model MODEL --case CASE_ID        full trace for one case\n"
              "  --case CASE_ID --all-models         compare one case across models")


if __name__ == "__main__":
    main()