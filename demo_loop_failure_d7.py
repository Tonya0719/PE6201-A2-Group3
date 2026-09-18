"""
D7 · Failure 1 — loop-control failure

Built as "the working agent, minus X" via a TEMPORARY runtime monkey-patch,
not a permanent edit to any real file. X here is action de-duplication
(check_duplicate_actions). Everything else — agent_core.py, guardrails.py,
backends.py on disk — is completely untouched. The patch is applied, the
demo runs, and the ORIGINAL functions are restored in a finally block
before this script exits, whether it succeeds or crashes.

WHAT THIS SHOWS
    RUN 1 (before)  - working agent, guard in place, normal claim, normal
                      turn count, correct decision.
    RUN 2 (after)   - same agent, dedup guard DISABLED, and the model is
                      forced (by injecting a repeated response) to keep
                      re-asking for the same claim data forever. No
                      exception is raised. It just burns the entire step
                      cap and returns with NO final decision.
    RUN 3 (restored)- the monkey-patch has been removed and the working
                      agent is run again on the same claim. It must return
                      to the same correct outcome and normal turn range.

Runs entirely on the scripted backend. No API key needed. Reproduces
identically every time.

USAGE
    python3 demo_loop_failure.py
    python3 demo_loop_failure.py --case CLM-8850
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src import agent_core, backends, config
from src.tools import reset_outbox


def run_normal(claim_id: str) -> dict:
    config.BACKEND = "scripted"
    # Every condition must start from the same clean simulated write state.
    # Otherwise RUN 1 leaves a decision in memory and later conditions are
    # measuring write de-duplication rather than the loop-control variable.
    reset_outbox()
    return agent_core.run_agent(claim_id, approved_for_write=True)


def capture_natural_sequence(claim_id: str) -> list[dict]:
    """Run once, recording every raw response backends.call_model returned,
    in order. This is what a correctly-behaving model said at each turn for
    THIS specific claim - we reuse it to build the forced-repeat scenario."""
    captured = []
    real_call_model = backends.call_model

    def recorder(messages):
        r = real_call_model(messages)
        captured.append(r)
        return r

    backends.call_model = recorder
    try:
        run_normal(claim_id)
    finally:
        backends.call_model = real_call_model
    return captured


def run_forced_loop(claim_id: str, captured: list[dict], disable_dedup: bool) -> dict:
    """Replays captured[0] (the first turn's response) over and over,
    simulating a model that keeps re-asking for data it already has.
    If disable_dedup is True, ALSO removes the guard that would normally
    catch this. Both patches are restored in finally, regardless of outcome."""
    real_call_model = backends.call_model
    real_dedup = agent_core.check_duplicate_actions

    # Repeat the first response far more times than the step cap allows,
    # so if nothing stops it, it genuinely never reaches a final answer -
    # matching the brief's own "8 turns, no answer" illustration.
    forced_queue = [captured[0]] * (config.STEP_CAP + 5) + captured[1:]
    call_count = {"n": 0}

    def looping_call_model(messages):
        i = min(call_count["n"], len(forced_queue) - 1)
        call_count["n"] += 1
        return forced_queue[i]

    backends.call_model = looping_call_model
    if disable_dedup:
        agent_core.check_duplicate_actions = lambda tool_calls, seen: (tool_calls, [])

    try:
        result = run_normal(claim_id)
    finally:
        backends.call_model = real_call_model
        agent_core.check_duplicate_actions = real_dedup

    return result


def report(before: dict, after: dict, restored: dict) -> dict:
    lines = []
    def p(s=""):
        print(s)
        lines.append(s)

    p("\n" + "=" * 78)
    p("D7 FAILURE 1 — LOOP-CONTROL FAILURE (action de-duplication)")
    p("=" * 78)

    p(f"\nRUN 1 (before) - working agent, guard in place, normal claim")
    p(f"  turns={before['turns']} tokens_in={before.get('input_tokens')} "
      f"tokens_out={before.get('output_tokens')} cost=${before.get('cost', 0):.4f} "
      f"decision={before.get('decision')} status={before.get('status')}")

    p(f"\nRUN 2 (after) - SAME agent, dedup guard REMOVED, model forced to repeat")
    p(f"  turns={after['turns']} tokens_in={after.get('input_tokens')} "
      f"tokens_out={after.get('output_tokens')} cost=${after.get('cost', 0):.4f} "
      f"decision={after.get('decision')} status={after.get('status')} "
      f"failure_reason={after.get('failure_reason')}")

    p(f"\nRUN 3 (restored) - guard restored, same claim rerun normally")
    p(f"  turns={restored['turns']} tokens_in={restored.get('input_tokens')} "
      f"tokens_out={restored.get('output_tokens')} cost=${restored.get('cost', 0):.4f} "
      f"decision={restored.get('decision')} status={restored.get('status')}")

    p("\n" + "-" * 78)
    p("1. THE INSTRUMENTATION THAT FOUND IT")
    p(f"   Turns and cost logged per run. RUN 2 raised no exception - it just")
    p(f"   burned {after['turns']} turns (vs {before['turns']} normally) and")
    p(f"   returned with failure_reason={after.get('failure_reason')!r} instead")
    p(f"   of a decision. A pass-rate table alone would show this as a failed")
    p(f"   run, but nothing would tell you WHY without turn/cost instrumentation.")

    p("\n2. THE TURN DISTRIBUTION")
    p(f"   before: {before['turns']} turns | after (no guard): {after['turns']} turns "
      f"| step cap: {config.STEP_CAP}")
    p(f"   RUN 2 hit the step cap: {after.get('failure_reason') == 'NO_FINAL_BEFORE_CAP'}")

    p("\n3. THE FIX, AND WHY THE OTHER LAYERS WERE WRONG")
    p(f"   Action de-duplication (check_duplicate_actions) is what normally")
    p(f"   catches this - it fires BEFORE the repeated call is even executed.")
    p(f"   The step cap did eventually stop RUN 2, but only after burning the")
    p(f"   full budget with nothing to show for it - a cap BOUNDS the damage,")
    p(f"   it does not DETECT the fault. A prompt-level fix cannot be relied")
    p(f"   on either: the injected 'model' here is exactly the thing that")
    p(f"   forgot. Only the code layer (guardrails.py) reliably remembers.")

    p("\n4. BEFORE / AFTER, AND PROOF THE RESTORE WORKS")
    p(f"   The monkey-patch in this script is undone in a finally block the")
    p(f"   instant this demo ends - agent_core.py, guardrails.py, backends.py")
    p(f"   are never edited on disk. RUN 3 executes after the finally block")
    p(f"   restored the original guard. It returns decision={restored.get('decision')!r}")
    p(f"   in {restored.get('turns')} turns, matching the working baseline.")
    p(f"   The full run_eval.py regression separately checks that restoration")
    p(f"   does not reduce correctness anywhere in the frozen evaluation set.")
    p("=" * 78 + "\n")

    return {
        "before": before,
        "after": after,
        "restored": restored,
        "step_cap": config.STEP_CAP,
        "report_text": "\n".join(lines),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="CLM-8842", help="Claim ID to demonstrate on")
    args = ap.parse_args()

    print(f"Demonstrating on {args.case} (scripted backend, no API key needed)")

    before = run_normal(args.case)
    captured = capture_natural_sequence(args.case)

    after = run_forced_loop(args.case, captured, disable_dedup=True)
    restored = run_normal(args.case)

    if restored.get("decision") != before.get("decision") or restored.get("status") != before.get("status"):
        raise SystemExit("Restored guard did not recover the working baseline.")

    result = report(before, after, restored)

    out_dir = Path(__file__).resolve().parent / "results" / "failures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "d7_failure1_loop_control.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
