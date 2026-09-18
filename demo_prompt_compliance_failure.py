"""
D7 · Failure 2 — prompt-compliance / business-state enforcement failure

REAL BACKGROUND
During earlier live testing, google/gemini-2.5-flash-lite ignored the prompt-level
instruction to stop retrieving after get_claim had already revealed an exact duplicate.
The model continued with lookup_policy / check_coverage before eventually escalating.
This script deterministically replays that recorded behaviour so the failure can be
reproduced without an API key.

The final code uses the generalized runtime guard
check_no_retrieval_after_decisive_intake(), which covers both exact duplicates and
hostile member instructions. This is a superset of the earlier duplicate-only guard.

RUN 1 (before): same recorded trace with the current decisive-intake guard disabled.
RUN 2 (after):  same recorded trace with the current decisive-intake guard enabled.
RUN 3 (scripted engine baseline): pure deterministic scripted logic runs the
                                  same claim independently of the recorded trace.

Usage:
    python demo_prompt_compliance_failure.py
"""
from __future__ import annotations

import json
from pathlib import Path

from src import agent_core, backends, config
from src.tools import reset_outbox

CASE_ID = "CLM-8933"

# Team's recorded non-compliant live-model trace, represented in the exact schema
# parse_model_response() expects. It is replayed deterministically here.
RECORDED_NAIVE_TRACE = [
    {"text": json.dumps({"type": "action", "tool_calls": [
        {"name": "get_claim", "arguments": {"claim_id": CASE_ID}}
    ]})},
    {"text": json.dumps({"type": "action", "tool_calls": [
        {"name": "lookup_policy", "arguments": {"member_id": "M-2214"}}
    ]})},
    {"text": json.dumps({"type": "action", "tool_calls": [
        {"name": "check_coverage", "arguments": {"policy_id": "POL-3310", "procedure_code": "47120"}}
    ]})},
    {"text": json.dumps({"type": "action", "tool_calls": [
        {"name": "issue_decision_letter", "arguments": {
            "case_id": CASE_ID,
            "decision": "escalate",
            "trigger": "duplicate_claim",
            "reason": "The claim is an exact duplicate of a previously submitted claim.",
            "evidence": [{"source": "get_claim", "fact": "duplicate_of: CLM-8710"}],
            "missing_item": None,
        }}
    ]})},
    {"text": json.dumps({
        "type": "final",
        "decision": "escalate",
        "trigger": "duplicate_claim",
        "missing_item": None,
        "reason": "The claim is an exact duplicate of a previously submitted claim.",
        "evidence": [{"source": "get_claim", "fact": "duplicate_of: CLM-8710"}],
    })},
]

# When the guard blocks the wasteful lookup, an adaptive model sees the
# observation and proceeds to the correct decision. This recovery queue keeps
# the original faulty request but does not blindly replay later pre-fix calls.
RECORDED_RECOVERY_TRACE = [
    RECORDED_NAIVE_TRACE[0],
    RECORDED_NAIVE_TRACE[1],
    RECORDED_NAIVE_TRACE[3],
    RECORDED_NAIVE_TRACE[4],
]


def run_replay(guard_enabled: bool) -> dict:
    """Replay the same recorded model responses with one runtime guard toggled."""
    config.BACKEND = "scripted"
    reset_outbox()
    real_call_model = backends.call_model
    real_guard = agent_core.check_no_retrieval_after_decisive_intake
    call_count = {"n": 0}
    trace = RECORDED_RECOVERY_TRACE if guard_enabled else RECORDED_NAIVE_TRACE

    def replay(messages):
        i = min(call_count["n"], len(trace) - 1)
        call_count["n"] += 1
        return trace[i]

    backends.call_model = replay
    if not guard_enabled:
        # Current guard signature: (tool_calls, claim) -> (allowed, blocked, reason)
        agent_core.check_no_retrieval_after_decisive_intake = (
            lambda calls, claim: (calls, [], None)
        )

    try:
        result = agent_core.run_agent(CASE_ID, approved_for_write=True)
    finally:
        backends.call_model = real_call_model
        agent_core.check_no_retrieval_after_decisive_intake = real_guard

    return result


def run_scripted_baseline() -> dict:
    """Run the normal loop and scripted backend with no monkey-patches."""
    config.BACKEND = "scripted"
    reset_outbox()
    return agent_core.run_agent(CASE_ID, approved_for_write=True)


def main():
    print(f"Demonstrating D7 Failure 2 on {CASE_ID} (deterministic replay, no API key needed)\n")

    before = run_replay(guard_enabled=False)
    after = run_replay(guard_enabled=True)
    scripted_baseline = run_scripted_baseline()

    blocked_events = [
        e for e in after.get("guardrail_events", [])
        if e.get("event") == "READ_AFTER_DECISIVE_INTAKE_BLOCKED"
    ]
    blocked_duplicate = any(e.get("decisive_reason") == "duplicate_claim" for e in blocked_events)
    before_tools = [
        call.get("name")
        for step in before.get("tool_history", [])
        for call in step.get("tool_calls", [])
    ]
    after_tools = [
        call.get("name")
        for step in after.get("tool_history", [])
        for call in step.get("tool_calls", [])
    ]

    print("=" * 78)
    print("D7 FAILURE 2 — PROMPT-COMPLIANCE / BUSINESS-STATE ENFORCEMENT")
    print("=" * 78)
    print("\nRUN 1 (before) - current guard DISABLED")
    print(
        f"  turns={before.get('turns')} tool_turns={before.get('tool_turns')} "
        f"decision={before.get('decision')} status={before.get('status')}"
    )
    print("\nRUN 2 (after) - current generalized decisive-intake guard ENABLED")
    print(
        f"  turns={after.get('turns')} tool_turns={after.get('tool_turns')} "
        f"decision={after.get('decision')} status={after.get('status')}"
    )
    print(f"  duplicate read blocked before execution: {blocked_duplicate}")
    print(f"  executed tools before: {' -> '.join(before_tools)}")
    print(f"  executed tools after : {' -> '.join(after_tools)}")

    print("\nRUN 3 (scripted engine baseline) - pure deterministic logic")
    print(
        f"  turns={scripted_baseline.get('turns')} "
        f"tool_turns={scripted_baseline.get('tool_turns')} "
        f"decision={scripted_baseline.get('decision')} "
        f"status={scripted_baseline.get('status')}"
    )

    print("\nGUARD EVENT EVIDENCE JSON (RUN 2 - GUARDED)")
    print(json.dumps(blocked_events, indent=2, ensure_ascii=False))

    print("\nWhy this is D7-worthy:")
    print("  - Prompt text and the early-exit nudge are advisory; the live model ignored them.")
    print("  - Removing one runtime control reproduces the wasteful retrieval behaviour.")
    print("  - Restoring that control blocks lookup_policy/check_coverage/preauth after decisive intake.")
    print("  - The final guard is deliberately generalized to both duplicate and hostile-intake cases.")

    result = {
        "case_id": CASE_ID,
        "failure_type": "prompt_compliance_business_state_enforcement",
        "recorded_source": "google/gemini-2.5-flash-lite live observation from earlier build",
        "control_removed": "check_no_retrieval_after_decisive_intake",
        "before": before,
        "after": after,
        "scripted_baseline": scripted_baseline,
        "blocked_duplicate_read": blocked_duplicate,
        "before_executed_tools": before_tools,
        "after_executed_tools": after_tools,
    }

    out_dir = Path(__file__).resolve().parent / "results" / "failures"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "d7_failure2_prompt_compliance.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nSaved to {out_path}")

    if not {"lookup_policy", "check_coverage"}.issubset(before_tools):
        raise SystemExit("D7 Failure 2 did not reproduce the original wasteful retrieval path.")
    if not blocked_duplicate:
        raise SystemExit("D7 Failure 2 demo did not observe the expected current guard event.")
    if "lookup_policy" in after_tools or "check_coverage" in after_tools:
        raise SystemExit("D7 Failure 2 guard did not prevent the wasteful retrieval path.")
    if after.get("status") != "completed" or after.get("decision") != "escalate":
        raise SystemExit("D7 Failure 2 guarded replay did not recover the correct decision.")
    if (
        scripted_baseline.get("status") != "completed"
        or scripted_baseline.get("decision") != "escalate"
    ):
        raise SystemExit("D7 Failure 2 scripted baseline did not recover the correct decision.")


if __name__ == "__main__":
    main()
