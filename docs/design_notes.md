# Design Notes / Decision Log

Use this file to record **why** the team made important design choices. Keep entries short and evidence-based. This is not a second report.

## Confirmed constraints from the A2 brief / FAQ

- Build a **single-agent ReAct** system; no multi-agent architecture.
- Use one control loop for scripted and live backends.
- The three Problem A outcomes are `approve_in_principle`, `request_document`, and `escalate`.
- The gated action is only a local structured write, not a real letter or external transaction.
- Tool interfaces may be renamed, merged, split, or re-argued, but the routing logic / expected outcomes are fixed by the problem statement.
- Code guardrails must include step cap, budget ceiling, action de-duplication, and an explicit autonomy setting.
- D3 guardrail checklist, D5(a) scripted run, and D7 failure reproductions should run on the scripted backend.
- D4 grades outcomes, not a fixed trajectory. Fixed-value fields should use code checks; prose/evidence quality may use judgement checks.
- Ordinary cases run once per model; negative cases run three times per model.
- Live model comparison must keep the eval set and v2 prompt fixed. Model swapping should require changing the `MODEL` variable only.
- D2(b) v1→v2 should hold the model and eval set fixed and change only the selected descriptor / return shape.
- D2(c) parallelisation is allowed only when neither tool depends on the other's output.
- Both D7 failures must be created as **working agent minus X**, and restored by putting X back.

## Decision log template

### Decision: [short title]
- **Date:**
- **Owner:**
- **Related section:** D2 / D3 / D6 / D7
- **Choice made:**
- **Alternative considered:**
- **Evidence:**
- **Why this choice:**
- **Measurement / result:**

## Decisions that should eventually be recorded

- Final tool list and any tool removed / not added — D2(a)
- Two poka-yoke interface changes — D2(b)
- Which tool is used for the v1→v2 rewrite — D2(b)
- Dependency rule and parallelisation boundary — D2(c)
- Chosen autonomy level and why — D3(a)
- Step cap and budget ceiling, based on observed runs — D3 / D7
- Dominant cost lever — D6
- Failure 1 root cause and correct fix layer — D7
- Failure 2 root cause and correct fix layer — D7
