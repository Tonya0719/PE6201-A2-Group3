<<<<<<< HEAD
# Design Notes — Problem A

## D1 / D2(c) expected trajectory

The system uses one generic ReAct loop, but the measured/expected efficient paths are:

- **Turn 1 — Intake:** `get_claim(claim_id)`. It returns the raw claim plus `duplicate_of`, computed by the internal `check_duplicate` helper. If duplicate or hostile narrative is decisive, the next model turn should be Final.
- **Turn 2 — Policy gate:** `lookup_policy(member_id)` runs alone. It supplies `policy_id` and can terminate the path for lapsed policy, outside policy dates, or annual-limit exceeded.
- **Turn 3 — Batched line verification:** `check_coverage × N` + `get_preauthorisation × M` in the same model turn. `M` is known from the static preauth-required procedure-code list derived from `procedures.json`. `check_hospital_panel` and `check_missing_documents` run automatically here as internal helpers.
- **Turn 4 — Judgment + gated write:** the model returns Final; the runtime applies autonomy/write-dedup checks and then calls `issue_decision_letter` in the same model turn. No extra model call is needed for the local write.

Therefore the same loop can produce 2-, 3-, or 4-turn paths depending on evidence and early exit.

## D2(a) tool boundary

### Agent-visible tools retained
1. `get_claim` — every path needs claim facts.
2. `lookup_policy` — gates policy-level escalations and provides `policy_id`.
3. `check_coverage` — authoritative line exclusion/coverage source.
4. `get_preauthorisation` — supplies authorisation records for procedures known to require it.
5. `issue_decision_letter` — one gated local write.

### Helpers, not tools
- `check_duplicate`: deterministic exact 4-field match; folded into the `get_claim` observation.
- `check_hospital_panel`: record-only; panel status changes what the record says, not ACT/ASK/ESCALATE.
- `check_missing_documents`: deterministic join against `required_documents.json`; deferred until higher-priority escalation gates pass.
- `already_decided`: write-specific second-layer dedupe inside the gated action.

This follows the rule: **model judgment/choice → agent tool; deterministic lookup/compare → ordinary helper**.

## Coverage + preauth batching trade-off

The optimized design intentionally differs from a strict `coverage → next-turn preauth` sequence. `procedures.json` is static supplied ground truth, so the procedure codes requiring preauthorisation are extracted into a static prompt dependency list. The model can therefore request line coverage and relevant preauthorisation records in the same turn. The preauth tool returns only raw dates; the model still has to judge whether the authorisation applies to the claim's service date.

This should be treated as a **measured D2(c) optimization**, not an assumption. Compare sequential vs batched execution on the same eval set and report turns, tokens, cost and correctness.

## Live-model prompt failure and fix

Observed failure: a live model returned multiple JSON objects in one call and fabricated its own `lookup_policy`, `check_coverage` and `get_preauthorisation` observations (including invented IDs). This breaks the central ground-truth rule.

Mitigation implemented:
- one turn must return exactly one JSON object;
- Action must stop immediately;
- observations may only come from runtime tools/helpers;
- unknown facts remain unknown;
- multi-call batching occurs only inside one `tool_calls` list;
- structured JSON mode is requested from the API;
- parser rejects multi-object/invalid JSON rather than extracting the first object and hiding the violation.

Live testing also showed that duplicate/injection early exit was not always followed by prompt instruction alone. The loop therefore injects a narrow follow-up nudge after a decisive Turn-1 observation. The model still produces the decision, trigger, reason and evidence; the runtime does not hard-code the Final output.

## Governance cliff

Retrieval and helper calculations are read-only. The governance cliff is the local simulated `issue_decision_letter` write. `AUTONOMY` is system configuration, never a model-supplied argument.
=======
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
>>>>>>> 5bd9f6e092f1512df28d8169c82e5b4e456af3a3
