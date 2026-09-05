"""Marker-facing entry point for D5(a).

Runs the full scripted evaluation set with no arguments, no key, and no network.
"""
from __future__ import annotations

import json
from pathlib import Path

from src import config
from src.harness import run_evaluation, summarize_results


ROOT = Path(__file__).resolve().parent
RESULTS_DIR = ROOT / "results"
RESULTS_PATH = RESULTS_DIR / "results.json"


def main():
    config.BACKEND = "scripted"

    records = run_evaluation(
        approved_for_write=True,
        parallel_enabled=config.PARALLEL_ENABLED,
        tool_spec_version=config.TOOL_SPEC_VERSION,
    )
    summary = summarize_results(records)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "backend": config.BACKEND,
        "parallel_enabled": config.PARALLEL_ENABLED,
        "tool_spec_version": config.TOOL_SPEC_VERSION,
        "summary": summary,
        "records": records,
    }
    RESULTS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nSaved results to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
